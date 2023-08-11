import operator
import os
from abc import abstractmethod
from functools import reduce
from typing import Any, Dict, List, Tuple, Union

from pynamodb.indexes import GlobalSecondaryIndex, LocalSecondaryIndex
from pynamodb.models import Model

from pynamodb_utils.conditions import Condition, FilterError, create_model_condition

from .exceptions import SerializerError
from .parsers import parse_value
from .utils import create_index_map, pick_index_keys

MAX_QUERY_DEPTH = int(os.environ.get("PYNAMODB_UTILS_MAX_QUERY_DEPTH", 10))


class Serializer:
    def __init__(self, model: Model) -> None:
        self.model: Model = model
        super().__init__()

    @abstractmethod
    def load(data: dict) -> Any:
        pass


class ConditionsSerializer(Serializer):
    STATEMENT_OPERATOR_MAP = {"AND": operator.and_, "OR": operator.or_}

    def __init__(self, model: Model, unavailable_attributes: List[str] = []) -> None:
        self.unavailable_attributes: List[str] = unavailable_attributes
        super().__init__(model)

    def _get_conditions(
        self,
        data: dict,
        raise_exception: bool = False,
        depth: int = 0,
        _operator=operator.and_,
    ):
        if depth > MAX_QUERY_DEPTH:
            raise SerializerError(message={"Query": ["Maximal query depth has been reached."]})

        conditions = []
        for k, __operator in self.STATEMENT_OPERATOR_MAP.items():
            statement = data.pop(k, None)
            if statement:
                conditions.append(
                    self._get_conditions(
                        data=statement,
                        raise_exception=raise_exception,
                        _operator=__operator,
                        depth=depth + 1,
                    )
                )
        if data:
            conditions.append(
                create_model_condition(
                    self.model,
                    args=data,
                    _operator=_operator,
                    raise_exception=raise_exception,
                    unavailable_attributes=self.unavailable_attributes
                )
            )
        return reduce(operator.and_, conditions) if conditions else None

    def load(self, data: dict, raise_exception: bool = False) -> Condition:
        try:
            return self._get_conditions(data, raise_exception)
        except ValueError as e:
            raise SerializerError(message={"Query": str(e)})
        except FilterError as e:
            raise SerializerError(message={"Query": e.message}) from e


class QuerySerializer(Serializer):
    def __init__(self, model: Model, unavailable_attributes: List[str] = []) -> None:
        self.unavailable_attributes: List[str] = unavailable_attributes
        super().__init__(model)

    def _create_query(self, data: dict, raise_exception: bool = False):
        idx_map = create_index_map(self.model)
        _equals = {}
        _rest = {}
        for k in data:
            if k not in ("AND", "OR"):
                _name, *_operator = k.rsplit("__", 1)
                if _operator in (["equals"], []):
                    _equals[_name] = data[k]
                else:
                    _rest[_name] = data[k]

        preferred_index_key = pick_index_keys(idx_map, _equals, _rest)

        if preferred_index_key is None:
            raise SerializerError(message={"Query": ["Could not find index for query"]})

        range_key_query = {}
        range_keys = [_k for _k in data if _k.rsplit("__", 1)[0].startswith(preferred_index_key[1])]
        hash_keys = [_k for _k in data if _k.rsplit("__", 1)[0].startswith(preferred_index_key[0])]
        for _k in range_keys:
            range_key_query[_k] = data[_k]
            del data[_k]

        for _k in hash_keys:
            del data[_k]
        conditions_serializer = ConditionsSerializer(self.model, self.unavailable_attributes)
        range_key_condition = conditions_serializer.load(
            range_key_query, raise_exception
        )
        condition = conditions_serializer.load(data, raise_exception)
        hash_key = parse_value(self.model, preferred_index_key[0], _equals[preferred_index_key[0]])
        result = idx_map[preferred_index_key], {
            "hash_key": hash_key,
            "range_key_condition": range_key_condition,
            "filter_condition": condition,
        }
        return result

    def load(
        self,
        data: dict,
        raise_exception: bool = False
    ) -> Tuple[Union[Model, GlobalSecondaryIndex, LocalSecondaryIndex], Dict[str, Any]]:
        try:
            return self._create_query(data, raise_exception)
        except ValueError as e:
            raise SerializerError(message={"Query": str(e)})
        except FilterError as e:
            raise SerializerError(message={"Query": e.message})

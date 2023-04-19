import operator
import os
from abc import abstractmethod
from functools import reduce
from typing import Any, Dict

from pynamodb_utils.conditions import FilterError, create_model_condition

from .exceptions import SerializerError
from .parsers import parse_value
from .utils import create_index_map

MAX_QUERY_DEPTH = os.environ.get("PYNAMODB_UTILS_MAX_QUERY_DEPTH", 10)


class Serializer:
    def __init__(self, model) -> None:
        self.model = model
        super().__init__()

    @abstractmethod
    def load(data: dict) -> Any:
        pass


class ConditionsSerializer(Serializer):
    STATEMENT_OPERATOR_MAP = {"AND": operator.and_, "OR": operator.or_}

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
        for k, _operator in self.STATEMENT_OPERATOR_MAP.items():
            statement = data.pop(k, None)
            if statement:
                conditions.append(
                    self._get_conditions(
                        data=statement,
                        raise_exception=raise_exception,
                        _operator=_operator,
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
                )
            )
        return reduce(operator.and_, conditions)

    def load(self, data: dict, raise_exception: bool = False):
        try:
            return self._get_conditions(data, raise_exception)
        except ValueError as e:
            raise SerializerError(message={"Query": str(e)})
        except FilterError as e:
            raise SerializerError(message={"Query": e.message}) from e


class QuerySerializer(Serializer):
    def _create_query(self, data: dict, raise_exception: bool = False):
        prefered_index = None

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
        # if possible pick the index that have at least one in equals and one in rest
        for k in idx_map:
            if set(_equals.keys()) & set(k) and set(_rest.keys()) & set(k):
                prefered_index = idx_map[k]
                break
            if set(_equals.keys()) & set(k):
                prefered_index = idx_map[k]

        if prefered_index is None:
            raise SerializerError(message={"Query": ["Could not find index for query"]})

        range_key_query = {}
        _keys = [_k for _k in data if _k.rsplit("__", 1)[0].startswith(k[1])]

        for _k in _keys:
            range_key_query[_k] = data[_k]
            del data[_k]

        condtions_serializer = ConditionsSerializer(self.model)
        range_key_condition = condtions_serializer.load(
            range_key_query, raise_exception
        )
        condition = condtions_serializer.load(data, raise_exception)
        return prefered_index, {
            "hash_key": parse_value(self.model, k[0], _equals[k[0]]),
            "range_key_condition": range_key_condition,
            "filter_condition": condition,
        }

    def load(self, data: dict, raise_exception: bool = False) -> Dict[str, Any]:
        try:
            return self._create_query(data, raise_exception)
        except ValueError as e:
            raise SerializerError(message={"Query": str(e)})
        except FilterError as e:
            raise SerializerError(message={"Query": e.message})

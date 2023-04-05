import operator
import typing
from functools import reduce

from marshmallow import INCLUDE, Schema, fields, post_load, types
from marshmallow.exceptions import ValidationError

from pynamodb_utils.filters import FilterError, create_model_filter

from .parsers import parse_value
from .utils import create_index_map


class ConditionsSerializer(Schema):
    Or = fields.List(fields.Dict, required=False, allow_none=True)
    And = fields.List(fields.Dict, required=False, allow_none=True)

    class Meta:
        unknown = INCLUDE

    def __init__(
            self,
            *,
            only: types.StrSequenceOrSet = None,
            exclude: types.StrSequenceOrSet = (),
            many: bool = False,
            context: typing.Dict = None,
            load_only: types.StrSequenceOrSet = (),
            dump_only: types.StrSequenceOrSet = (),
            partial: typing.Union[bool, types.StrSequenceOrSet] = False,
            unknown: str = None,
            model=None,
            raise_exception=True
    ):
        super().__init__(only=only, exclude=exclude, many=many, context=context, load_only=load_only,
                         dump_only=dump_only, partial=partial, unknown=unknown)
        self.model = model
        self.raise_exception = raise_exception

    def load(
            self,
            data: typing.Mapping,
            *,
            many: bool = None,
            partial: typing.Union[bool, types.StrSequenceOrSet] = None,
            unknown: str = None,
            model=None,
            raise_exception=True
    ):
        if model is not None:
            self.model = model
            self.raise_exception = raise_exception
        return super().load(data=data, many=many, partial=partial, unknown=unknown)

    @staticmethod
    def parse_conditions_dict(model, data: dict, raise_exception=False):
        try:
            conditions = []
            or_conditions = data.pop('Or', [])
            and_conditions = data.pop('And', [])

            query = create_model_filter(model=model, args=data, raise_exception=raise_exception)
            or_conditions = [create_model_filter(model=model, args=item, raise_exception=raise_exception) for
                             item in or_conditions]
            and_conditions = [create_model_filter(model=model, args=item, raise_exception=raise_exception) for
                              item in and_conditions]

            if or_conditions:
                conditions.append(reduce(operator.or_, or_conditions))
            if and_conditions:
                conditions.append(reduce(operator.and_, and_conditions))

            if query is not None:
                conditions.append(query)

            return reduce(operator.and_, conditions) if conditions else None
        except ValueError as e:
            raise ValidationError(message=str(e))
        except FilterError as e:
            raise ValidationError(
                message={
                    "Query": e.message
                }
            )

    @post_load(pass_original=True)
    def create_conditions(self, data, original_data, **kwargs):
        return self.parse_conditions_dict(self.model, original_data, self.raise_exception)


class QuerySerializer(Schema):
    Or = fields.List(fields.Dict, required=False, allow_none=True)
    And = fields.List(fields.Dict, required=False, allow_none=True)

    class Meta:
        unknown = INCLUDE

    def __init__(
            self,
            *,
            only: types.StrSequenceOrSet = None,
            exclude: types.StrSequenceOrSet = (),
            many: bool = False,
            context: typing.Dict = None,
            load_only: types.StrSequenceOrSet = (),
            dump_only: types.StrSequenceOrSet = (),
            partial: typing.Union[bool, types.StrSequenceOrSet] = False,
            unknown: str = None,
            model=None,
            raise_exception=True
    ):
        super().__init__(only=only, exclude=exclude, many=many, context=context, load_only=load_only,
                         dump_only=dump_only, partial=partial, unknown=unknown)
        self.model = model
        self.raise_exception = raise_exception

    def load(
            self,
            data: typing.Mapping,
            *,
            many: bool = None,
            partial: typing.Union[bool, types.StrSequenceOrSet] = None,
            unknown: str = None,
            model=None,
            raise_exception=True
    ):
        if model is not None:
            self.model = model
            self.raise_exception = raise_exception
        return super().load(data=data, many=many, partial=partial, unknown=unknown)

    @post_load(pass_original=True)
    def create_query(self, data, original_data, **kwargs):
        prefered_index = None

        idx_map = create_index_map(self.model)
        _equals = {}
        _rest = {}
        for k in data:
            if k not in ("And", "Or"):
                _name, *_operator = k.rsplit("__", 1)
                if _operator in (['equals'], []):
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
            raise ValidationError(
                message={
                    "Query": ["Could not find index for query"]
                }
            )

        range_key_query = {}
        _keys = [_k for _k in original_data if _k.rsplit("__", 1)[0].startswith(k[1])]

        for _k in _keys:
            range_key_query[_k] = original_data[_k]
            del original_data[_k]

        range_key_condition = ConditionsSerializer.parse_conditions_dict(
            self.model,
            range_key_query,
            self.raise_exception
        )
        condition = ConditionsSerializer.parse_conditions_dict(
            self.model,
            original_data,
            self.raise_exception
        )
        return prefered_index, {
            "hash_key": parse_value(self.model, k[0], _equals[k[0]]),
            "range_key_condition": range_key_condition,
            "filter_condition": condition
        }

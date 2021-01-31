import operator
import typing
from functools import reduce

from marshmallow import INCLUDE, Schema, fields, post_load, types
from marshmallow.exceptions import ValidationError

from pynamodb_utils.filters import FilterError, create_model_filter


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
        try:
            conditions = []
            or_conditions = original_data.pop('Or', [])
            and_conditions = original_data.pop('And', [])

            query = create_model_filter(model=self.model, args=original_data, raise_exception=self.raise_exception)
            or_conditions = [create_model_filter(model=self.model, args=item, raise_exception=self.raise_exception) for
                             item in or_conditions]
            and_conditions = [create_model_filter(model=self.model, args=item, raise_exception=self.raise_exception) for
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

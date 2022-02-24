from marshmallow.exceptions import ValidationError
from pynamodb.attributes import UTCDateTimeAttribute
from pynamodb.models import Model

from pynamodb_utils.exceptions import FilterError
from pynamodb_utils.query_serializer import QuerySerializer
from pynamodb_utils.utils import get_timestamp, parse_attrs_to_dict


class JSONQueryModel(Model):

    class Meta:
        abstract = True

    @classmethod
    def get_conditions_from_json(cls, query: dict):
        try:
            return QuerySerializer().load(model=cls, data=query)
        except ValidationError as e:
            raise FilterError(message=e.messages, status_code=400)


class AsDictModel(Model):

    class Meta:
        abstract = True

    def as_dict(self):
        return parse_attrs_to_dict(self)


class TimestampedModel(Model):
    created_at = UTCDateTimeAttribute(default=get_timestamp)
    updated_at = UTCDateTimeAttribute(default=get_timestamp)
    deleted_at = UTCDateTimeAttribute(null=True)

    class Meta:
        abstract = True

    def save(self, condition=None):
        tz_info = getattr(self.Meta, "TZINFO", None)
        self.updated_at = get_timestamp(tzinfo=tz_info)
        super().save(condition=condition)

    def save_without_timestamp_update(self, condition=None):
        super().save(condition=condition)

    def soft_delete(self, condition=None):
        tz_info = getattr(self.Meta, "TZINFO", None)
        self.deleted_at = get_timestamp(tz_info)
        super().save(condition=condition)

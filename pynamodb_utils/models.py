from copy import deepcopy

from pynamodb.attributes import JSONAttribute, UnicodeAttribute, UTCDateTimeAttribute
from pynamodb.models import Model

from pynamodb_utils.query_serializer import QuerySerializer

from .utils import get_timestamp, parse_attrs_to_dict


class JSONQueryModel(Model):
    
    @classmethod
    def get_conditions_from_json(cls, query:dict):
        return QuerySerializer.load(model=cls, data=query)


class AsDicteModel(Model):

    def as_dict(self):
        return parse_attrs_to_dict(self)


class TimestampedModel(Model):
    CreatedAt = UTCDateTimeAttribute(default=get_timestamp)
    UpdatedAt = UTCDateTimeAttribute(default=get_timestamp)
    DeletedAt = UTCDateTimeAttribute(null=True)

    def save(self, condition=None):
        tz_info = getattr(self.Meta, "TZINFO", None)
        self.UpdatedAt = get_timestamp(tzinfo=tz_info)
        super().save(condition=condition)

    def save_without_timestamp_update(self, condition=None):
        super().save(condition=condition)

    def soft_delete(self, condition=None):
        tz_info = getattr(self.Meta, "TZINFO", None)
        self.DeletedAt = get_timestamp(tz_info)
        super().save(condition=condition)

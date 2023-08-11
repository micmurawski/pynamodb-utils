from datetime import timezone
from typing import Any, List

from pynamodb.attributes import UTCDateTimeAttribute
from pynamodb.expressions.condition import Condition
from pynamodb.models import Model, ResultIterator

from pynamodb_utils.serializers import ConditionsSerializer, QuerySerializer
from pynamodb_utils.utils import get_timestamp, parse_attrs_to_dict


class JSONQueryModel(Model):
    class Meta:
        abstract = True

    @classmethod
    def get_conditions_from_json(cls, query: dict, raise_exception: bool = True) -> Condition:
        """
            Class method parses query dictionary and returns computed pynamodb condition.

            Parameters:
                    query (dict): A decimal integer

            Returns:
                    condition (Condition): computed pynamodb condition
        """
        query_unavailable_attributes: List[str] = getattr(cls.Meta, "query_unavailable_attributes", [])
        return ConditionsSerializer(cls, query_unavailable_attributes).load(data=query, raise_exception=raise_exception)

    @classmethod
    def make_index_query(cls, query: dict, raise_exception: bool = True, **kwargs) -> ResultIterator[Model]:
        """
            Class method parses query dictionary and executes query on index most suitable index

            Parameters:
                    query (dict): A decimal integer

            Returns:
                    result_iterator (result_iterator): result iterator for optimized query
        """
        query_unavailable_attributes: List[str] = getattr(cls.Meta, "query_unavailable_attributes", [])
        idx, query = QuerySerializer(cls, query_unavailable_attributes).load(
            data=query, raise_exception=raise_exception)
        return idx.query(**query, **kwargs)


class AsDictModel(Model):
    class Meta:
        abstract = True

    def as_dict(self) -> dict:
        """ Parses pynamodb model instance to python dict"""
        invisible_attributes: List[str] = getattr(self.Meta, "invisible_attributes", [])
        result: dict = parse_attrs_to_dict(self)
        attr: str
        for attr in invisible_attributes:
            self._pop_path(result, attr)
        return result

    @staticmethod
    def _pop_path(obj: dict, path: str) -> Any:
        attrs = path.split(".")[::-1]
        _len = len(attrs)
        for i in range(len(attrs)):
            key = attrs[i]
            if key in obj:
                if i == _len - 1:
                    return obj.pop(key)
                obj = obj[key]


class TimestampedModel(Model):
    created_at = UTCDateTimeAttribute(default=get_timestamp)
    updated_at = UTCDateTimeAttribute(default=get_timestamp)
    deleted_at = UTCDateTimeAttribute(null=True)

    class Meta:
        abstract = True

    def save(self, condition=None):
        tz_info = getattr(self.Meta, "TZINFO", None)
        self.created_at = self.created_at.astimezone(tz=tz_info or timezone.utc)
        self.updated_at = get_timestamp(tzinfo=tz_info)
        super().save(condition=condition)

    def save_without_timestamp_update(self, condition=None):
        super().save(condition=condition)

    def soft_delete(self, condition=None):
        """ Puts delete_at timestamp """
        tz_info = getattr(self.Meta, "TZINFO", None)
        self.deleted_at = get_timestamp(tz_info)
        super().save(condition=condition)

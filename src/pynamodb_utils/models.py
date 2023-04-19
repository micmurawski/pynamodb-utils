from datetime import timezone

from pynamodb.attributes import UTCDateTimeAttribute
from pynamodb.expressions.condition import Condition
from pynamodb.models import Model, ResultIterator

from pynamodb_utils.serializers import ConditionsSerializer, QuerySerializer
from pynamodb_utils.utils import get_timestamp, parse_attrs_to_dict


class JSONQueryModel(Model):
    class Meta:
        abstract = True

    @classmethod
    def get_conditions_from_json(cls, query: dict) -> Condition:
        """
            Class method parses query dictionary and returns computed pynamodb condition.

            Parameters:
                    query (dict): A decimal integer

            Returns:
                    condtion (Condition): computed pynamodb condition
        """
        return ConditionsSerializer(cls).load(data=query)

    @classmethod
    def make_index_query(cls, query: dict, **kwargs) -> ResultIterator[Model]:
        """
            Class method parses query dictionary and executes query on index most suitable index

            Parameters:
                    query (dict): A decimal integer

            Returns:
                    result_iterator (result_iterator): result iterator for optimized query
        """
        idx, query = QuerySerializer(cls).load(data=query)
        return idx.query(**query, **kwargs)


class AsDictModel(Model):
    class Meta:
        abstract = True

    def as_dict(self) -> dict:
        """ Parses pynamodb model instance to python dict"""
        return parse_attrs_to_dict(self)


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

from enum import Enum

import pytest
from moto import mock_dynamodb2

from pynamodb_utils.attributes import DynamicMapAttribute, EnumAttribute, UnicodeAttribute


class ExampleEnum(Enum):
    A = 'A'
    B = 'B'
    C = 'C'


@pytest.fixture
def dynamodb():
    with mock_dynamodb2():
        yield


@pytest.fixture
def resource_model(dynamodb):
    from pynamodb_utils.models import AsDictModel, JSONQueryModel, TimestampedModel

    class ResourceModel(JSONQueryModel, AsDictModel, TimestampedModel):
        ID = UnicodeAttribute(hash_key=True)
        map = DynamicMapAttribute()
        enum = EnumAttribute(enum=ExampleEnum)

        class Meta:
            table_name = 'resource_model_table_name'

    ResourceModel.create_table(read_capacity_units=10, write_capacity_units=10)
    return ResourceModel

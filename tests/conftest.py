import enum
from datetime import timezone

import pytest
from moto import mock_dynamodb2
from pynamodb.attributes import UnicodeAttribute

from pynamodb_utils import AsDictModel, DynamicMapAttribute, EnumAttribute, JSONQueryModel, TimestampedModel


@pytest.fixture
def dynamodb():
    with mock_dynamodb2():
        yield


@pytest.fixture
def post_table(dynamodb):

    class CategoryEnum(enum.Enum):
        finance = enum.auto()
        politics = enum.auto()

    class Post(AsDictModel, JSONQueryModel, TimestampedModel):
        name = UnicodeAttribute(hash_key=True)
        category = EnumAttribute(enum=CategoryEnum, default=CategoryEnum.finance)
        content = UnicodeAttribute()
        sub_name = UnicodeAttribute(null=True)
        tags = DynamicMapAttribute(default={})

        class Meta:
            table_name = 'example-table-name'
            TZINFO = timezone.utc

    Post.create_table(read_capacity_units=10, write_capacity_units=10)

    yield Post

    Post.delete_table()

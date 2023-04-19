import enum
from datetime import timezone

import pytest
from moto import mock_dynamodb
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute
from pynamodb.indexes import AllProjection, GlobalSecondaryIndex

from pynamodb_utils import AsDictModel, DynamicMapAttribute, EnumAttribute, JSONQueryModel, TimestampedModel


@pytest.fixture
def dynamodb():
    with mock_dynamodb():
        yield


@pytest.fixture
def post_table(dynamodb):
    class CategoryEnum(enum.Enum):
        finance = enum.auto()
        politics = enum.auto()

    class PostCategoryCreatedAtGSI(GlobalSecondaryIndex):
        category = EnumAttribute(hash_key=True, enum=CategoryEnum)
        created_at = UTCDateTimeAttribute(range_key=True)

        class Meta:
            index_name = "example-index-name"
            projection = AllProjection

    class Post(AsDictModel, JSONQueryModel, TimestampedModel):
        name = UnicodeAttribute(hash_key=True)
        sub_name = UnicodeAttribute(range_key=True)
        category = EnumAttribute(enum=CategoryEnum, default=CategoryEnum.finance)
        content = UnicodeAttribute()
        tags = DynamicMapAttribute(default={})
        category_created_at_gsi = PostCategoryCreatedAtGSI()

        class Meta:
            table_name = "example-table-name"
            TZINFO = timezone.utc

    Post.create_table(read_capacity_units=10, write_capacity_units=10)

    yield Post

    Post.delete_table()

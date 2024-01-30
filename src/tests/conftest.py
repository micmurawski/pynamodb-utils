import enum
import os
from datetime import timezone

import pytest
from moto import mock_aws
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute
from pynamodb.indexes import AllProjection, GlobalSecondaryIndex

from pynamodb_utils import AsDictModel, DynamicMapAttribute, EnumAttribute, JSONQueryModel, TimestampedModel


@pytest.fixture
def aws_environ():
    env_vars = {
        "AWS_DEFAULT_REGION": "us-east-1"
    }
    with mock_aws():
        for k, v in env_vars.items():
            os.environ[k] = v

        yield

        for k in env_vars:
            del os.environ[k]


@pytest.fixture
def post_table(aws_environ):
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
        tags = DynamicMapAttribute(default=None)
        category_created_at_gsi = PostCategoryCreatedAtGSI()
        secret_parameter = UnicodeAttribute(default="secret")

        class Meta:
            table_name = "example-table-name"
            TZINFO = timezone.utc
            query_unavailable_attributes = ["secret_parameter"]
            invisible_attributes = ["secret_parameter"]

    Post.create_table(read_capacity_units=10, write_capacity_units=10)

    yield Post

    Post.delete_table()

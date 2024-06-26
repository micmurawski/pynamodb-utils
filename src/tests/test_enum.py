from datetime import datetime

import pytest
from freezegun import freeze_time

from pynamodb_utils.serializers import SerializerError


@freeze_time("2019-01-01 00:00:00+00:00")
def test_enum_query_not_member_of(post_table):
    post = post_table
    category_enum = post.category.enum

    post = post(
        name="A weekly news.",
        sub_name="Shocking revelations",
        content="Last week took place...",
        category=category_enum.finance,
        tags={"type": "news", "topics": ["stock exchange", "NYSE"]},
    )
    post.save()

    with pytest.raises(SerializerError) as e:
        post.get_conditions_from_json(
            query={
                "created_at__lte": str(datetime.now()),
                "sub_name__exists": None,
                "category__equals": 1,
                "tags.type__equals": "news",
                "tags.topics__contains": ["NYSE"],
            }
        )
    assert e.value.message == {
        "Query": {"category": ["1 is not member of finance, politics."]}
    }


@freeze_time("2019-01-01 00:00:00+00:00")
def test_enum_create_not_member_of(post_table):
    post = post_table

    with pytest.raises(AttributeError):
        post = post(
            name="A weekly news.",
            sub_name="subname",
            content="Last week took place...",
            category="ABC",
            tags={"type": "news", "topics": ["stock exchange", "NYSE"]},
        )
        post.save()

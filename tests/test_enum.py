from datetime import datetime

import pytest
from freezegun import freeze_time

from pynamodb_utils.filters import FilterError


@freeze_time("2019-01-01 00:00:00+00:00")
def test_enum_query_not_member_of(post_table):
    Post = post_table
    CategoryEnum = Post.category.enum

    post = Post(
        name='A weekly news.',
        sub_name='Shocking revelations',
        content='Last week took place...',
        category=CategoryEnum.finance,
        tags={
            "type": "news",
            "topics": ["stock exchange", "NYSE"]
        }
    )
    post.save()

    with pytest.raises(FilterError) as e:
        Post.get_conditions_from_json(query={
            "created_at__lte": str(datetime.now()),
            "sub_name__exists": None,
            "category__equals": 1,
            "tags.type__equals": "news",
            "tags.topics__contains": ["NYSE"]
        })
        assert e.value.message == {'Query': {'category': ['1 is not member of finance, politics.']}}


@freeze_time("2019-01-01 00:00:00+00:00")
def test_enum_create_not_member_of(post_table):
    Post = post_table

    with pytest.raises(ValueError) as e:
        post = Post(
            name='A weekly news.',
            content='Last week took place...',
            category=1,
            tags={
                "type": "news",
                "topics": ["stock exchange", "NYSE"]
            }
        )
        post.save()
        assert str(e.value) == "Value Error: 1 must be in finance, politics"

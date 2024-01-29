from datetime import datetime

import pytest
from freezegun import freeze_time

from pynamodb_utils.exceptions import SerializerError


@freeze_time("2019-01-01 00:00:00+00:00")
def test_general(post_table):
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
    query = {
        "created_at__lte": str(datetime.now()),
        "sub_name__exists": None,
        "category__equals": "finance",
        "OR": {"tags.type__equals": "news", "tags.topics__contains": ["NYSE"]},
    }

    results = post.make_index_query(query)

    expected = {
        "content": "Last week took place...",
        "created_at": "2019-01-01T00:00:00+00:00",
        "deleted_at": None,
        "name": "A weekly news.",
        "category": "finance",
        "sub_name": "Shocking revelations",
        "tags": {"type": "news", "topics": ["stock exchange", "NYSE"]},
        "updated_at": "2019-01-01T00:00:00+00:00",
    }

    assert next(results).as_dict() == expected


def test_bad_field(post_table):
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

    with pytest.raises(SerializerError) as exc_info:
        post.get_conditions_from_json(query={"tag.type__equals": "news"})
    assert exc_info.value.message == {
            "Query": {
                "tag.type": [
                    "Parameter tag.type does not exist. Choose some of "
                    "available: category, content, created_at, deleted_at, "
                    "name, sub_name, tags, tags.*, updated_at"
                ]
            }
        }

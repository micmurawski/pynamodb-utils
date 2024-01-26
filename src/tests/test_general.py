from datetime import datetime

import pytest
from freezegun import freeze_time

from pynamodb_utils.exceptions import SerializerError


@freeze_time("2019-01-01 00:00:00+00:00")
def test_general(post_table):
    Post = post_table
    CategoryEnum = Post.category.enum

    post_1 = Post(
        name="A weekly news.",
        sub_name="Shocking revelations",
        content="Last week took place...",
        category=CategoryEnum.finance,
        tags={"type": "news", "topics": ["stock exchange", "NYSE"]},
    )
    post_1.save()
    post_2 = Post(
        name="A boring news.",
        sub_name="Nothing interesting...",
        content="...",
        category=CategoryEnum.finance,
        tags={"type": "not-news", "topics": ["stock exchange", "LSE"]},
    )
    post_2.save()
    query = {
        "created_at__lte": str(datetime.now()),
        "sub_name__exists": None,
        "category__equals": "finance",
        "OR": {"tags.type__equals": "news", "tags.topics__contains": ["NYSE"]},
    }

    results = list(Post.make_index_query(query))

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

    assert len(results) == 1
    assert results[0].as_dict() == expected


def test_bad_field(post_table):
    Post = post_table
    CategoryEnum = Post.category.enum

    post = Post(
        name="A weekly news.",
        sub_name="Shocking revelations",
        content="Last week took place...",
        category=CategoryEnum.finance,
        tags={"type": "news", "topics": ["stock exchange", "NYSE"]},
    )
    post.save()

    with pytest.raises(SerializerError) as e:
        Post.get_conditions_from_json(query={"tag.type__equals": "news"})
        assert e.message == {
            "Query": {
                "tag.type": [
                    "Parameter tag does not exist. Choose some of "
                    "available: category, content, created_at, deleted_at, "
                    "name, sub_name, tags, updated_at"
                ]
            }
        }

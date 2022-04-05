from datetime import datetime

from freezegun import freeze_time

from pynamodb_utils.filters import FilterError


@freeze_time("2019-01-01 00:00:00+00:00")
def test_general(post_table):
    Post = post_table
    CategoryEnum = Post.category.enum

    post = Post(
        name='A weekly news.',
        content='Last week took place...',
        category=CategoryEnum.finance,
        tags={
            "type": "news",
            "topics": ["stock exchange", "NYSE"]
        }
    )
    post.save()

    condition = Post.get_conditions_from_json(query={
        "created_at__lte": str(datetime.now()),
        "sub_name": None,
        "category__equals": "finance",
        "tags.type__equals": "news",
        "tags.topics__contains": ["NYSE"]
    })
    results = Post.scan(filter_condition=condition)

    expected = {
        'content': 'Last week took place...',
        'created_at': '2019-01-01 00:00:00+00:00',
        'deleted_at': None,
        'name': 'A weekly news.',
        'category': 'finance',
        "sub_name": None,
        'tags': {
            'type': 'news',
            'topics': ['stock exchange', 'NYSE']
        },
        'updated_at': '2019-01-01 00:00:00+00:00'
    }

    assert next(results).as_dict() == expected


def test_bad_field(post_table):
    Post = post_table
    CategoryEnum = Post.category.enum

    post = Post(
        name='A weekly news.',
        content='Last week took place...',
        category=CategoryEnum.finance,
        tags={
            "type": "news",
            "topics": ["stock exchange", "NYSE"]
        }
    )
    post.save()

    try:
        Post.get_conditions_from_json(query={
            "tag.type__equals": "news"
        })
    except FilterError as e:
        assert e.message == {
            'Query': {
                'tag.type': [
                    'Parameter tag does not exist. Choose some of '
                    'available: category, content, created_at, deleted_at, '
                    'name, sub_name, tags, updated_at'
                ]
            }
        }

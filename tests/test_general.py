from freezegun import freeze_time


@freeze_time("2019-01-01 00:00:00+00:00")
def test_general(dynamodb):
    from datetime import timezone, datetime
    from pynamodb.attributes import UnicodeAttribute
    from pynamodb_utils import DynamicMapAttribute, AsDictModel, JSONQueryModel, TimestampedModel

    class Post(AsDictModel, JSONQueryModel, TimestampedModel):
        name = UnicodeAttribute(hash_key=True)
        content = UnicodeAttribute()
        sub_name = UnicodeAttribute(null=True)
        tags = DynamicMapAttribute(default={})

        class Meta:
            table_name = 'example-table-name'
            TZINFO = timezone.utc

    Post.create_table(read_capacity_units=10, write_capacity_units=10)

    post = Post(
        name='A weekly news.',
        content='Last week took place...',
        tags={
            "type": "news",
            "topics": ["stock exchange", "NYSE"]
        }
    )
    post.save()

    condition = Post.get_conditions_from_json(query={
        "created_at__lte": str(datetime.now()),
        "sub_name": None,
        "tags.type__equals": "news",
        "tags.topics__contains": ["NYSE"]
    })
    results = Post.scan(filter_condition=condition)

    expected = {
        'content': 'Last week took place...',
        'created_at': '2019-01-01 00:00:00+00:00',
        'deleted_at': None,
        'name': 'A weekly news.',
        "sub_name": None,
        'tags': {
            'type': 'news',
            'topics': ['stock exchange', 'NYSE']
        },
        'updated_at': '2019-01-01 00:00:00+00:00'
    }

    assert next(results).as_dict() == expected

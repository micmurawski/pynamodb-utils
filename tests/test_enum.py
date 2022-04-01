import pytest
from freezegun import freeze_time


@freeze_time("2019-01-01 00:00:00+00:00")
def test_enum_query_not_member_of(dynamodb):
    import enum
    from datetime import datetime, timezone

    from pynamodb.attributes import UnicodeAttribute

    from pynamodb_utils import AsDictModel, DynamicMapAttribute, EnumAttribute, JSONQueryModel, TimestampedModel
    from pynamodb_utils.exceptions import FilterError

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

    post = Post(
        name='A weekly news.',
        content='Last week took place...',
        # category=CategoryEnum.finance,
        tags={
            "type": "news",
            "topics": ["stock exchange", "NYSE"]
        }
    )
    post.save()

    with pytest.raises(FilterError) as e:
        Post.get_conditions_from_json(query={
            "created_at__lte": str(datetime.now()),
            "sub_name": None,
            "category__equals": 1,
            "tags.type__equals": "news",
            "tags.topics__contains": ["NYSE"]
        })
        assert e.value.message == {'Query': {'category': ['1 is not member of finance, politics.']}}


@freeze_time("2019-01-01 00:00:00+00:00")
def test_enum_create_not_member_of(dynamodb):
    import enum
    from datetime import timezone

    from pynamodb.attributes import UnicodeAttribute

    from pynamodb_utils import AsDictModel, DynamicMapAttribute, EnumAttribute, JSONQueryModel, TimestampedModel

    class CategoryEnum(enum.Enum):
        finance = enum.auto()
        politics = enum.auto()

    class Post(AsDictModel, JSONQueryModel, TimestampedModel):
        name = UnicodeAttribute(hash_key=True)
        category = EnumAttribute(enum=CategoryEnum)
        content = UnicodeAttribute()
        sub_name = UnicodeAttribute(null=True)
        tags = DynamicMapAttribute(default={})

        class Meta:
            table_name = 'example-table-name'
            TZINFO = timezone.utc

    Post.create_table(read_capacity_units=10, write_capacity_units=10)

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

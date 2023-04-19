# Introduction

Pynamodb Utils is a collection of small helper functions, utilities and classes which make common patterns easier. It helped me make my job easier in the past.

[![Tests](https://github.com/micmurawski/pynamodb-utils/actions/workflows/main.yml/badge.svg)](https://github.com/micmurawski/pynamodb-utils/actions/workflows/main.yml) [![pypi](https://img.shields.io/pypi/v/pynamodb-utils.svg)](https://pypi.org/project/pynamodb-utils/)

## Examples are:

 - Models with automatic ``updated_at``, ``created_at`` and ``deleted_at`` fields
 - Attributes for enums and dynamic mappings
 - Class with methods that allow to generate from JSON/dict query/scan conditions

## To install:
Run ``pip install pynamodb-utils`` or execute ``python setup.py install`` in the source directory

## Example of Usage

To setup pynamodb models with authomaticly generated timestamps and useful functions allowing serialization of scan conditions from JSON input from API.

```python
from datetime import timezone, datetime
from pynamodb.attributes import UnicodeAttribute
from pynamodb_utils import DynamicMapAttribute, AsDictModel,
JSONQueryModel, TimestampedModel


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
        table_name = 'example-table-name'
        TZINFO = timezone.utc

Post.create_table(read_capacity_units=10, write_capacity_units=10)

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

condition = Post.make_index_query(
    query={
        "created_at__lte": str(datetime.now()),
        "sub_name__exists": None,
        "category__equals": "finance",
        "OR": {"tags.type__equals": "news", "tags.topics__contains": ["NYSE"]},
    }
) # class method executes query on the most optimal index
print(next(results).as_dict())
```
That lines of code should result with following output

```
{
        'name': 'A weekly news.',
        'created_at': '2019-01-01 00:00:00+00:00',
        'updated_at': '2019-01-01 00:00:00+00:00',
        'deleted_at': None,
        'content': 'Last week took place...',
        'tags': {
            'type': 'news',
            'topics': ['stock exchange', 'NYSE']
        }
    }
```

## Links
* https://github.com/pynamodb/PynamoDB
* https://pypi.org/project/pynamodb-utils/

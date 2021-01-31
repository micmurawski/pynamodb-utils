# Introduction

Pynamodb Utils is a collection of small helper functions, utilities and classes which make common patterns easier. It helped me make my job easier in the past.

## Examples are:

 - Models with automatic ``updated_at``, ``created_at`` and ``deleted_at`` fields
 - Attributes for enums and dynamic mappings
 - Class with methods that allow to generate from JSON/dict query/scan conditions

 ## To install:

 1. Run ``pip install pynamodb-utils or execute ``python setup.py install`` in the source directory
 2. Add ``pynamodb_utils`` to your ``INSTALLED_APPS``

## Example of Usage

To setup pynamodb models with authomaticly generated timestamps and useful functions allowing serialization of scan conditions from JSON input from API.

```python
from datetime import timezone
from pynamodb.attribiutes import UnicodeAttribiute
from pynamodb_utils import DynamicMappingAttribiute, AsDictModel,
JSONQueryModel, TimestampedModel


class Post(AsDictModel, JSONQueryModel, TimestampedModel):
    name = UnicodeAttribiute(hash_key=True)
    content = UnicodeAttribiute()
    tags = DynamicMappingAttribiute(default={})

    class Meta:
        table_name = 'example-table-name'
        TZINFO = timezone.utc


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
    "tags.type__equals": "news",
    "tags.topics__contains": ["NYSE"]
})
results = Post.scan(filter_condition=condition)
print(next(result).as_dict())
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
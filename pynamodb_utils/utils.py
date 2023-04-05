from datetime import datetime, timezone
from typing import Type

from pynamodb.attributes import MapAttribute
from pynamodb.indexes import GlobalSecondaryIndex, LocalSecondaryIndex
from pynamodb.models import Model

from pynamodb_utils.attributes import DynamicMapAttribute
from pynamodb_utils.exceptions import FilterError


def create_index_map(model: Type[Model]):
    idx_map = {
        (model._hash_keyname, model._range_keyname): model,
    }
    for k, v in model.__dict__.items():
        if isinstance(v, (GlobalSecondaryIndex, LocalSecondaryIndex)):
            schema = v._get_schema()
            hash_key = next(filter(lambda x: x['KeyType'] == 'HASH', schema['key_schema']))['AttributeName']
            range_key = next(filter(lambda x: x['KeyType'] == 'RANGE', schema['key_schema']), {}).get('AttributeName')
            idx_map[(hash_key, range_key)] = getattr(model, k)
    
    return idx_map



def parse_attr(attr):
    if isinstance(attr, DynamicMapAttribute):
        return attr.as_dict()
    elif isinstance(attr, MapAttribute):
        return parse_attrs_to_dict(attr)
    elif isinstance(attr, datetime):
        return datetime.isoformat(attr, sep='T')
    return attr


def parse_attrs_to_dict(obj):
    return {k: parse_attr(getattr(obj, k, None)) for k in obj.get_attributes().keys()}


def get_nested_attribute(model, attr_string, raise_exception=True):
    attrs = attr_string.split('.')
    result = model
    for attr in attrs:
        if isinstance(result, DynamicMapAttribute):
            result = result[attr]
        elif hasattr(result, attr):
            result = getattr(result, attr)
        elif raise_exception:
            raise FilterError(
                message={attr_string: [f'Parameter {attr} does not exist.'
                                       f' Choose some of available: {", ".join(result.get_attributes())}']},
                status_code=400
            )
        else:
            return None
    return result


def get_timestamp(tzinfo=None):
    return datetime.now(tzinfo or timezone.utc)

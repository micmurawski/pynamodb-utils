from datetime import datetime, timezone

from pynamodb.attributes import MapAttribute

from .attributes import DynamicMapAttribute
from .exceptions import FilterError


def parse_attr(attr):
    if isinstance(attr, DynamicMapAttribute):
        return attr.as_dict()
    elif isinstance(attr, MapAttribute):
        return parse_attrs_to_dict(attr)
    elif isinstance(attr, datetime):
        return str(attr)
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
                                       f' Choose some of available: {list(result.get_attributes())}']},
                status_code=400
            )
        else:
            return None
    return result


def get_timestamp(tzinfo=None):
    return datetime.now(tzinfo or timezone.utc)

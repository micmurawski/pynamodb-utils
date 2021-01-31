from datetime import datetime
from typing import Dict, List, Union

from pynamodb import attributes
from pynamodb.expressions.operand import Path

from pynamodb_utils.attributes import EnumAttribute

from .exceptions import FilterError


def parse_string_to_datetime(value: str, field_name: str, *args):
    for fmt in DATETIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise FilterError(message={field_name: [
        f"{value} is not valid type of {field_name}. Supported formats are {', '.join(DATETIME_FORMATS)}"]})


DATETIME_FORMATS = [
    '%Y-%m-%dT%H:%M:%S.%f+00:00',
    '%Y-%m-%dT%H:%M:%S.%f',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%dT%H:%M',
    '%Y-%m-%d %H:%M:%S.%f+00:00',
    '%Y-%m-%d %H:%M:%S.%f',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M',
    '%Y-%m-%d'
]


def default_parser(value, *args):
    return value


def default_list_parser(value: List, field_name: str, *args):
    if isinstance(value, list):
        return value
    raise FilterError(message={field_name: [f"{value} is not valid type of {field_name}."]})


def default_dict_parser(value: Dict, field_name: str, *args):
    if isinstance(value, dict):
        return value
    raise FilterError(message={field_name: [f"{value} is not valid type of {field_name}."]})


def default_bool_parser(value: bool, field_name: str, *args):
    if isinstance(value, bool):
        return value
    raise FilterError(message={field_name: [f"{value} is not valid type of {field_name}."]})


def default_str_parser(value, field_name: str, *args):
    if isinstance(value, str):
        return value
    raise FilterError(message={field_name: [f"{value} is not valid type of {field_name}."]})


def default_number_parser(value: Union[float, int], field_name: str, *args):
    if isinstance(value, (float, int)):
        return value
    raise FilterError(message={field_name: [f"{value} is not valid type of {field_name}."]})


def default_enum_parser(value, field_name: str, model):
    values = getattr(model, field_name).enum.__members__

    _value = set(value) if isinstance(value, list) else {value}

    if _value.issubset(set(values)):
        return value

    raise FilterError(message={field_name: [
        f"{', '.join(value) if isinstance(value, list) else value} is not member of {', '.join(values)}."]})


TYPE_MAPPING = {
    attributes.UTCDateTimeAttribute: parse_string_to_datetime,
    attributes.UnicodeAttribute: default_str_parser,
    Path: default_parser,
    attributes.ListAttribute: default_list_parser,
    attributes.JSONAttribute: default_dict_parser,
    attributes.MapAttribute: default_parser,
    attributes.BooleanAttribute: default_bool_parser,
    attributes.NumberAttribute: default_number_parser,
    EnumAttribute: default_enum_parser
}


def parse_value(model, field_name: str, value):
    attrs = field_name.split('.')
    if len(attrs) == 1:
        _type = type(getattr(model, field_name))
        return TYPE_MAPPING[_type](value, field_name, model)
    else:
        return TYPE_MAPPING[attributes.MapAttribute](value, field_name, model)


def get_equals_condition(model, field_name: str, attr, value):
    return attr.__eq__(parse_value(model, field_name, value))


def get_startswith_condition(model, field_name: str, attr, value):
    return attr.startswith(value)


def get_gt_condition(model, field_name: str, attr, value):
    return attr.__gt__(parse_value(model, field_name, value))


def get_lt_condition(model, field_name: str, attr, value):
    return attr.__lt__(parse_value(model, field_name, value))


def get_gte_condition(model, field_name: str, attr, value):
    return attr.__ge__(parse_value(model, field_name, value))


def get_lte_condition(model, field_name: str, attr, value):
    return attr.__le__(parse_value(model, field_name, value))


def get_contains_condition(model, field_name: str, attr, value):
    parsed_value = parse_value(model, field_name, value)
    if isinstance(parsed_value, list):
        return attr.contains(*parsed_value)
    return attr.contains(parsed_value)


def get_is_in_condition(model, field_name: str, attr, value):
    parsed_value = parse_value(model, field_name, value)
    if isinstance(parsed_value, list):
        return attr.is_in(*parsed_value)
    return attr.is_in(parsed_value)


OPERATORS_MAPPING = {
    '': get_equals_condition,
    'equals': get_equals_condition,
    'contains': get_contains_condition,
    'startswith': get_startswith_condition,
    'gt': get_gt_condition,
    'lt': get_lt_condition,
    'gte': get_gte_condition,
    'lte': get_lte_condition,
    'is_in': get_is_in_condition,
}

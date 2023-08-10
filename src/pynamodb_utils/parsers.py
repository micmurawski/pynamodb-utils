import json
from datetime import datetime
from functools import reduce
from operator import and_
from typing import Any, Dict, List, Union

from pynamodb import attributes
from pynamodb.attributes import Attribute
from pynamodb.expressions.condition import Condition
from pynamodb.expressions.operand import Path
from pynamodb.models import Model

from pynamodb_utils.attributes import EnumNumberAttribute, EnumUnicodeAttribute
from pynamodb_utils.exceptions import FilterError


def parse_string_to_datetime(value: str, field_name: str, *args):
    for fmt in DATETIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise FilterError(
        message={
            field_name: [
                f"{value} is not valid type of {field_name}. Supported formats are {', '.join(DATETIME_FORMATS)}"
            ]
        }
    )


DATETIME_FORMATS = [
    "%Y-%m-%dT%H:%M:%S.%f+00:00",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M:%S.%f+00:00",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
]

NoneType = type(None)


def default_parser(value: Any, *args) -> Any:
    return value


def default_list_parser(value: List[Any], field_name: str, model: Model) -> List[Any]:
    if isinstance(value, (list, NoneType)):
        return value
    elif isinstance(value, str):
        field = getattr(model, field_name)
        _type = field.element_type() if field else attributes.UnicodeAttribute()
        return [_type.deserialize(i) for i in value.split(',')]
    raise FilterError(message={field_name: [f"{value} is not valid type of {field_name}."]})


def default_dict_parser(value: Dict, field_name: str, *args) -> Dict[Any, Any]:
    if isinstance(value, (dict, NoneType)):
        return value
    elif isinstance(value, str):
        try:
            return json.dumps(value, default=str)
        except (ValueError, json.JSONDecodeError):
            pass
    raise FilterError(
        message={field_name: [f"{value} is not valid type of {field_name}."]}
    )


def default_bool_parser(value: bool, field_name: str, *args) -> bool:
    if isinstance(value, (bool, NoneType)):
        return value
    elif isinstance(value, str):
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        else:
            try:
                return bool(value)
            except ValueError:
                pass

    raise FilterError(
        message={field_name: [f"{value} is not valid type of {field_name}."]}
    )


def default_str_parser(value: Any, field_name: str, *args) -> str:
    if isinstance(value, (str, NoneType)):
        return value
    raise FilterError(
        message={field_name: [f"{value} is not valid type of {field_name}."]}
    )


def default_number_parser(value: Union[float, int], field_name: str, *args) -> Union[float, int]:
    if isinstance(value, (float, int, NoneType)):
        return value
    elif isinstance(value, (str)):
        try:
            return float(value)
        except ValueError:
            pass

    raise FilterError(
        message={field_name: [f"{value} is not valid type of {field_name}."]}
    )


def default_enum_parser(value: Any, field_name: str, model: Model) -> Any:
    if isinstance(value, NoneType):
        return None

    values = getattr(model, field_name).enum.__members__

    _value = set(value) if isinstance(value, list) else {value}

    if _value.issubset(set(values)):
        return value

    raise FilterError(
        message={
            field_name: [
                f"{', '.join(value) if isinstance(value, list) else value} is not member of {', '.join(values)}."
            ]
        }
    )


TYPE_MAPPING = {
    attributes.UTCDateTimeAttribute: parse_string_to_datetime,
    attributes.UnicodeAttribute: default_str_parser,
    attributes.UnicodeSetAttribute: default_str_parser,
    Path: default_parser,
    attributes.ListAttribute: default_list_parser,
    attributes.JSONAttribute: default_dict_parser,
    attributes.MapAttribute: default_parser,
    attributes.BooleanAttribute: default_bool_parser,
    attributes.NumberAttribute: default_number_parser,
    EnumNumberAttribute: default_enum_parser,
    EnumUnicodeAttribute: default_enum_parser,
}


def parse_value(model: Model, field_name: str, value: Any) -> Any:
    attrs = field_name.split(".")
    if len(attrs) == 1:
        _type = type(getattr(model, field_name))
        if issubclass(_type, attributes.MapAttribute):
            return TYPE_MAPPING[attributes.MapAttribute](value, field_name, model)
        return TYPE_MAPPING[_type](value, field_name, model)
    else:
        return TYPE_MAPPING[attributes.MapAttribute](value, field_name, model)


def get_equals_condition(model: Model, field_name: str, attr: Attribute, value: Any) -> Condition:
    parsed_value = parse_value(model, field_name, value)
    if parsed_value is None:
        return attr.does_not_exist()
    return attr.__eq__(parsed_value)


def get_startswith_condition(model: Model, field_name: str, attr: Attribute, value: Any) -> Condition:
    return attr.startswith(parse_value(model, field_name, value))


def get_exists_condition(model: Model, field_name: str, attr: Attribute, value: Any) -> Condition:
    return attr.exists()


def get_gt_condition(model: Model, field_name: str, attr: Attribute, value: Any) -> Condition:
    return attr.__gt__(parse_value(model, field_name, value))


def get_lt_condition(model: Model, field_name: str, attr: Attribute, value: Any) -> Condition:
    return attr.__lt__(parse_value(model, field_name, value))


def get_gte_condition(model: Model, field_name: str, attr: Attribute, value: Any) -> Condition:
    return attr.__ge__(parse_value(model, field_name, value))


def get_lte_condition(model: Model, field_name: str, attr: Attribute, value: Any) -> Condition:
    return attr.__le__(parse_value(model, field_name, value))


def get_contains_condition(model: Model, field_name: str, attr: Attribute, value: Any) -> Condition:
    parsed_value = parse_value(model, field_name, value)
    if isinstance(parsed_value, list):
        return attr.contains(*parsed_value)
    return attr.contains(parsed_value)


def get_is_in_condition(model: Model, field_name: str, attr: Attribute, value: Any) -> Condition:
    parsed_value = parse_value(model, field_name, value)
    if isinstance(parsed_value, list):
        return reduce(and_, [attr.is_in(item) for item in parsed_value])
    return attr.is_in(parsed_value)


OPERATORS_MAPPING = {
    "": get_equals_condition,
    "equals": get_equals_condition,
    "contains": get_contains_condition,
    "exists": get_exists_condition,
    "startswith": get_startswith_condition,
    "gt": get_gt_condition,
    "lt": get_lt_condition,
    "gte": get_gte_condition,
    "lte": get_lte_condition,
    "is_in": get_is_in_condition,
}

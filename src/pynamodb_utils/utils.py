from datetime import datetime, timezone
from typing import Any, Dict, Tuple, Union

from pynamodb.attributes import Attribute, MapAttribute
from pynamodb.indexes import GlobalSecondaryIndex, LocalSecondaryIndex
from pynamodb.models import Model

from pynamodb_utils.attributes import DynamicMapAttribute
from pynamodb_utils.exceptions import FilterError


def create_index_map(
        model: Model
) -> Dict[Tuple[str, str], Union[Model, GlobalSecondaryIndex, LocalSecondaryIndex]]:
    """
    Function creates dictionary which maps hash_key and range_key to specific index.
    """
    idx_map = {
        (model._hash_keyname, model._range_keyname): model,
    }
    for k, v in model.__dict__.items():
        try:
            if isinstance(v, (GlobalSecondaryIndex, LocalSecondaryIndex)):
                schema = v._get_schema()
                hash_key = next(
                    filter(lambda x: x["KeyType"] == "HASH", schema["key_schema"])
                )["AttributeName"]
                range_key = next(
                    filter(lambda x: x["KeyType"] == "RANGE", schema["key_schema"]), {}
                ).get("AttributeName")
                idx_map[(hash_key, range_key)] = getattr(model, k)
        except StopIteration as e:
            raise Exception("Could not find index keys") from e

    return idx_map


def pick_index_keys(
    idx_map: Dict[Tuple[str, str], Union[Model, GlobalSecondaryIndex, LocalSecondaryIndex]],
    _equals: Dict[str, str],
    _rest: Dict[str, str]
) -> Tuple[str, str]:
    common_keys = 0
    keys = None
    for k in idx_map:
        val_1 = len(set(_equals.keys()) & set(k))
        val_2 = int(k[0] in set(_equals.keys())) + int(k[1] in set(_rest.keys()))
        val = max(val_1, val_2)
        if val > common_keys:
            common_keys = val
            keys = k
    return keys


def parse_attr(attr: Attribute) -> Union[Dict, datetime]:
    """
    Function parses attribute to corresponding values
    """
    if isinstance(attr, DynamicMapAttribute):
        return attr.as_dict()
    elif isinstance(attr, MapAttribute):
        return parse_attrs_to_dict(attr)
    elif isinstance(attr, datetime):
        return datetime.isoformat(attr, sep="T")
    return attr


def parse_attrs_to_dict(obj: Any) -> Dict[str, Any]:
    """
    Function parses model/attribute to dictionary
    """
    return {k: parse_attr(getattr(obj, k, None)) for k in obj.get_attributes().keys()}


def get_nested_attribute(model: Model, attr_string: str, raise_exception: bool = True) -> Attribute:
    """
    Function gets nested attribute based on path (attr_string)
    """
    attrs = attr_string.split(".")
    result = model
    for attr in attrs:
        if isinstance(result, DynamicMapAttribute):
            result = result[attr]
        elif hasattr(result, attr):
            result = getattr(result, attr)
        elif raise_exception:
            raise FilterError(
                message={
                    attr_string: [
                        f"Parameter {attr} does not exist."
                        f' Choose some of available: {", ".join(result.get_attributes())}'
                    ]
                },
                status_code=400,
            )
        else:
            return None
    return result


def get_timestamp(tzinfo: timezone = None) -> datetime:
    return datetime.now(tzinfo or timezone.utc)

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from pynamodb.attributes import Attribute, MapAttribute
from pynamodb.indexes import GlobalSecondaryIndex, LocalSecondaryIndex
from pynamodb.models import Model

from pynamodb_utils.attributes import DynamicMapAttribute

NoneType = type(None)


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
) -> Optional[Tuple[str, str]]:
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


def get_attributes_list(model: Model, depth: int = 0) -> List[str]:
    attrs = []
    for attr_str in model.get_attributes().keys():
        attr = getattr(model, attr_str)
        if isinstance(attr, MapAttribute):
            attrs += [f"{attr_str}.{a}" for a in get_attributes_list(attr, depth=depth+1)]
        if isinstance(attr, DynamicMapAttribute):
            attrs.append(f"{attr_str}.*")
        attrs.append(attr_str)
    return attrs


def get_available_attributes_list(model: Model, unavaiable_attrs: List[str] = []) -> Set[str]:
    attrs: List[str] = get_attributes_list(model)
    return [attr for attr in attrs if attr not in unavaiable_attrs]


def get_attribute(model: Model, attr_string: str) -> Attribute:
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
        else:
            return None
    return result


def get_timestamp(tzinfo: timezone = None) -> datetime:
    return datetime.now(tzinfo or timezone.utc)

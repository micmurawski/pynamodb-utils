from __future__ import annotations

import json
from enum import Enum
from typing import Any, Callable, Collection, FrozenSet, Optional, Type, TypeVar, Union

import six
from pynamodb.attributes import Attribute, MapAttribute
from pynamodb.constants import NUMBER, STRING

T = TypeVar("T", bound=Enum)
_fail: Any = object()


def string_number(x: str) -> str:
    return str(int(x))


class DynamicMapAttribute(MapAttribute):
    element_type = None

    def __init__(self, *args, of=None, **kwargs):
        if "default" in kwargs:
            kwargs["default"] = json.dumps(kwargs["default"])

        if "default_for_new" in kwargs:
            kwargs["default_for_new"] = json.dumps(kwargs["default_for_new"])

        if of:
            if not issubclass(of, MapAttribute):
                raise ValueError("'of' must be subclass of MapAttribute")
            self.element_type = of
        super(DynamicMapAttribute, self).__init__(*args, **kwargs)

    def _set_attributes(self, **attributes):
        """
        Sets the attributes for this object
        """
        for attr_name, attr_value in six.iteritems(attributes):
            setattr(self, attr_name, attr_value)

    def deserialize(self, values):
        """
        Decode from map of AttributeValue types.
        """
        if not self.element_type:
            return super(DynamicMapAttribute, self).deserialize(values)

        class_for_deserialize = self.element_type()
        return {
            k: class_for_deserialize.deserialize(attr_value)
            for k, v in values.items()
            for _, attr_value in v.items()
        }

    @classmethod
    def is_raw(cls) -> bool:
        return cls == DynamicMapAttribute

    def keys(self) -> FrozenSet:
        return self.as_dict().keys()

    def items(self) -> Collection:
        return self.as_dict().items()

    def __str__(self) -> str:
        return str(self.__class__)


class EnumNumberAttribute(Attribute[T]):
    attr_type = NUMBER

    def __init__(
        self,
        enum: Type[Enum],
        default: Optional[Enum] = None,
        default_for_new: Optional[Enum] = None,
        unknown_value: Optional[T] = _fail,
        **kwargs,
    ):
        if not issubclass(enum, Enum):
            raise ValueError("enum must be Enum class")

        self.enum = enum
        self.unknown_value = unknown_value

        self._default = default
        self._default_for_new = default_for_new

        if default:
            def default(): return self._default

        if default_for_new:
            def default_for_new(): return self._default_for_new

        super().__init__(
            **kwargs,
            default=default,
            default_for_new=default_for_new
        )

    def serialize(self, value: Union[int, Callable[[], T]]) -> str:  # string number
        if callable(value):
            value = value()
        if isinstance(value, int):
            return string_number(self.enum(value).value)
        if isinstance(value, str):
            return string_number(getattr(self.enum, value).value)
        if not isinstance(value, self.enum):
            raise TypeError(
                f"{value} has invalid type of {type(value)} expected {self.enum}"
            )
        return string_number(value.value)

    def deserialize(self, value: str) -> Optional[T]:
        try:
            return self.enum(int(value))
        except ValueError as e:
            if self.unknown_value is _fail:
                raise ValueError(f"{value} is not present in {self.enum}") from e
            return self.unknown_value


class EnumUnicodeAttribute(Attribute[T]):
    attr_type = STRING

    def __init__(
        self,
        enum: Type[Enum],
        default: Optional[Enum] = None,
        default_for_new: Optional[Enum] = None,
        unknown_value: Optional[T] = _fail,
        **kwargs,
    ):
        if not issubclass(enum, Enum):
            raise ValueError("enum must be Enum class")

        self.enum = enum
        self.unknown_value = unknown_value

        self._default = default
        self._default_for_new = default_for_new

        if default:
            def default(): return self._default

        if default_for_new:
            def default_for_new(): return self._default_for_new

        super().__init__(
            **kwargs,
            default=default,
            default_for_new=default_for_new
        )

    def serialize(self, value: Union[str, Callable[[], T]]) -> str:
        if callable(value):
            value = value()
        if isinstance(value, str):
            return self.enum(value).value
        if not isinstance(value, self.enum):
            raise TypeError(
                f"{value} has invalid type of {type(value)} expected {self.enum}"
            )
        return value.value

    def deserialize(self, value: str) -> Optional[T]:
        try:
            return self.enum(value)
        except ValueError as e:
            if self.unknown_value is _fail:
                raise ValueError(f"{value} is not present in {self.enum}") from e
            return self.unknown_value


EnumAttribute = EnumNumberAttribute

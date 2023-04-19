from enum import Enum
from typing import Collection, FrozenSet, Union

import six
from pynamodb.attributes import MapAttribute, NumberAttribute, UnicodeAttribute


class DynamicMapAttribute(MapAttribute):
    element_type = None

    def __init__(self, *args, of=None, **kwargs):
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

    def __repr__(self) -> dict:
        return self.as_dict()

    def __str__(self) -> str:
        return str(self.__class__)


class EnumNumberAttribute(NumberAttribute):
    def __init__(
        self,
        enum,
        hash_key=False,
        range_key=False,
        null=None,
        default=None,
        attr_name=None,
    ):
        if isinstance(enum, Enum):
            raise ValueError("enum must be Enum class")
        self.enum = enum
        super().__init__(
            hash_key=hash_key,
            range_key=range_key,
            default=default,
            null=null,
            attr_name=attr_name,
        )

    def serialize(self, value: Union[Enum, str]) -> str:
        try:
            if isinstance(value, self.enum):
                return str(value.value)
            elif isinstance(value, str):
                if value in self.enum.__members__.keys():
                    return str(getattr(self.enum, value).value)
            raise ValueError(
                f'Value Error: {value} must be in {", ".join([item for item in self.enum.__members__.keys()])}'
            )
        except TypeError as e:
            raise Exception(value, self.enum) from e

    def deserialize(self, value: str) -> str:
        return self.enum(int(value)).name


class EnumUnicodeAttribute(UnicodeAttribute):
    def __init__(
        self,
        hash_key=False,
        range_key=False,
        null=None,
        default=None,
        attr_name=None,
        enum=None,
    ):
        if isinstance(enum, Enum):
            raise ValueError("enum must be Enum class")
        self.enum = enum
        super().__init__(
            hash_key=hash_key,
            range_key=range_key,
            default=default,
            null=null,
            attr_name=attr_name,
        )

    def serialize(self, value: Union[Enum, str]) -> str:
        if isinstance(value, self.enum):
            return str(value.value)
        elif isinstance(value, str):
            if value in self.enum.__members__.keys():
                return getattr(self.enum, value).value
        raise ValueError(
            f'Value Error: {value} must be in {", ".join([item for item in self.enum.__members__.keys()])}'
        )

    def deserialize(self, value: str) -> str:
        return self.enum(value).name


EnumAttribute = EnumNumberAttribute

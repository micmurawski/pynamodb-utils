from enum import Enum

import six
from pynamodb.attributes import MapAttribute, UnicodeAttribute


def _get_value_for_deserialize(value):
    return value


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
        deserialized_dict = {}
        for k in values:
            v = values[k]
            attr_value = _get_value_for_deserialize(v)
            deserialized_dict[k] = class_for_deserialize.deserialize(attr_value)
        return deserialized_dict

    @classmethod
    def is_raw(cls):
        return cls == DynamicMapAttribute

    def keys(self):
        return self.as_dict().keys()

    def items(self):
        return self.as_dict().items()

    def __repr__(self):
        return self.as_dict()

    def __str__(self):
        return str(self.__class__)


class EnumAttribute(UnicodeAttribute):
    def __init__(self, hash_key=False, range_key=False, null=None, default=None, attr_name=None, enum=None):
        if isinstance(enum, Enum):
            raise ValueError('enum must be Enum class')
        self.enum = enum
        super().__init__(hash_key=hash_key, range_key=range_key, default=default, null=null, attr_name=attr_name)

    def serialize(self, value):
        if isinstance(value, str):
            if value in self.enum.__members__.keys():
                return getattr(self.enum, value).value
        raise ValueError(f'{value} must be in {",".join([item for item in self.enum.__members__.keys()])}')

    def deserialize(self, value):
        return self.enum(value).name

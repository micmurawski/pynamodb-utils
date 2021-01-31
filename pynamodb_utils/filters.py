import operator
from functools import reduce
from typing import Type

from pynamodb.attributes import Attribute
from pynamodb.expressions.operand import Path
from pynamodb.models import Model

from .exceptions import FilterError
from .parsers import OPERATORS_MAPPING
from .utils import get_nested_attribute


def create_model_filter(model: Type[Model], args, _operator=operator.and_, raise_exception=True):
    conditions_list = []

    for key, value in args.items():
        array = key.rsplit('__', 1)
        field_name = array[0]
        operator_name = array[1] if len(array) > 1 and array[1] != 'not' else ''
        if operator_name.replace('not_', '') not in OPERATORS_MAPPING:
            raise FilterError(
                message={key: [f'Operator {operator_name} does not exist.'
                               f' Choose some of available: {list(OPERATORS_MAPPING.keys())}']},
                status_code=400
            )
        nested_attr = get_nested_attribute(model, field_name, raise_exception)
        if isinstance(nested_attr, (Attribute, Path)) and value is not None:
            if 'not_' in operator_name:
                operator_name = operator_name.replace('not_', '')
                operator_handler = OPERATORS_MAPPING.get(operator_name)
                conditions_list.append(~operator_handler(model, field_name, nested_attr, value))
            else:
                operator_handler = OPERATORS_MAPPING.get(operator_name)
                conditions_list.append(operator_handler(model, field_name, nested_attr, value))

    if not conditions_list:
        return None
    else:
        return reduce(_operator, conditions_list)

import operator
from functools import reduce
from typing import Any, Callable, Dict

from pynamodb.attributes import Attribute
from pynamodb.expressions.condition import Condition
from pynamodb.expressions.operand import Path
from pynamodb.models import Model

from pynamodb_utils.exceptions import FilterError
from pynamodb_utils.parsers import OPERATORS_MAPPING
from pynamodb_utils.utils import get_nested_attribute


def create_model_condition(
    model: Model,
    args: Dict[str, Any],
    _operator: Callable = operator.and_,
    raise_exception: bool = True
) -> Condition:
    """
        Function creates pynamodb conditions based on input dictionary (args)
        Parameters:
                model (pynamodb.model.Model): Corresponing pynamodb model
                args (dict): The input dictionary with query
                _operator (Callable): operator used to consolidate conditions
                raise_exception (bool): boolean value enabling expceptions on missing nested attrs
        Returns:
                condtion (Condition): computed pynamodb condition
    """
    conditions_list = []

    for key, value in args.items():
        array = key.rsplit('__', 1)
        field_name = array[0]
        operator_name = array[1] if len(array) > 1 and array[1] != 'not' else ''
        if operator_name.replace('not_', '') not in OPERATORS_MAPPING:
            raise FilterError(
                message={key: [f'Operator {operator_name} does not exist.'
                               f' Choose some of available: {", ".join(OPERATORS_MAPPING.keys())}']}
            )
        nested_attr = get_nested_attribute(model, field_name, raise_exception)

        if isinstance(nested_attr, (Attribute, Path)):
            if 'not_' in operator_name:
                operator_name = operator_name.replace('not_', '')
                operator_handler = OPERATORS_MAPPING[operator_name]
                conditions_list.append(~operator_handler(model, field_name, nested_attr, value))
            else:
                operator_handler = OPERATORS_MAPPING[operator_name]
                conditions_list.append(operator_handler(model, field_name, nested_attr, value))
    if not conditions_list:
        return None
    else:
        return reduce(_operator, conditions_list)

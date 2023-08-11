import operator
from functools import reduce
from typing import Any, Callable, Dict, List, Set

from pynamodb.attributes import Attribute
from pynamodb.expressions.condition import Condition
from pynamodb.expressions.operand import Path
from pynamodb.models import Model

from pynamodb_utils.exceptions import FilterError
from pynamodb_utils.parsers import OPERATORS_MAPPING
from pynamodb_utils.utils import get_attribute, get_available_attributes_list


def create_model_condition(
    model: Model,
    args: Dict[str, Any],
    _operator: Callable = operator.and_,
    raise_exception: bool = True,
    unavailable_attributes: List[str] = []
) -> Condition:
    """
        Function creates pynamodb conditions based on input dictionary (args)
        Parameters:
                model (pynamodb.model.Model): Corresponding pynamodb model
                args (dict): The input dictionary with query
                _operator (Callable): operator used to consolidate conditions
                raise_exception (bool): boolean value enabling exceptions on missing nested attrs
                unavailable_attributes (list): list of attributes that should be unavailable
        Returns:
                condition (Condition): computed pynamodb condition
    """
    conditions_list: List[Condition] = []

    available_attributes: Set[str] = get_available_attributes_list(
        model=model,
        unavaiable_attrs=unavailable_attributes
    )

    key: str
    value: Any
    for key, value in args.items():
        array: List[str] = key.rsplit('__', 1)
        field_path: str = array[0]
        operator_name: str = array[1] if len(array) > 1 and array[1] != 'not' else ''

        if "." in field_path:
            _field_path = field_path.split(".", 1)[0] + ".*"
            is_available = _field_path in available_attributes
        else:

            is_available = field_path in available_attributes

        if operator_name.replace('not_', '') not in OPERATORS_MAPPING:
            raise FilterError(
                message={key: [f'Operator {operator_name} does not exist.'
                               f' Choose some of available: {", ".join(OPERATORS_MAPPING.keys())}']}
            )
        if not is_available and raise_exception:
            raise FilterError(
                message={
                    field_path: [
                        f"Parameter {field_path} does not exist."
                        f' Choose some of available: {", ".join(available_attributes)}'
                    ]
                }
            )

        attr: Attribute = get_attribute(model, field_path)

        if isinstance(attr, (Attribute, Path)):
            if 'not_' in operator_name:
                operator_name = operator_name.replace('not_', '')
                operator_handler = OPERATORS_MAPPING[operator_name]
                conditions_list.append(~operator_handler(model, field_path, attr, value))
            else:
                operator_handler = OPERATORS_MAPPING[operator_name]
                conditions_list.append(operator_handler(model, field_path, attr, value))
    if not conditions_list:
        return None
    else:
        return reduce(_operator, conditions_list)

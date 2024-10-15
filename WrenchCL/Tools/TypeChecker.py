#  Copyright (c) $YEAR$. Copyright (c) $YEAR$ Wrench.AI., Willem van der Schans, Jeong Kim
#
#  MIT License
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#  All works within the Software are owned by their respective creators and are distributed by Wrench.AI.
#
#  For inquiries, please contact Willem van der Schans through the official Wrench.AI channels or directly via GitHub at [Kydoimos97](https://github.com/Kydoimos97).
#

from typing import Any, Dict, List, Type, Union, Iterable

from . import logger


def typechecker(
    data: Union[Dict[str, Any], List[Dict[str, Any]]],
    expected_types: Dict[str, Union[Type, List[Type]]],
    none_is_ok: bool = False,
    errors: str = 'raise'
) -> bool:
    """
    Validates that each entry in a dictionary or a list of dictionaries matches the expected type.

    Args:
        data: A dictionary or a list of dictionaries to validate.
        expected_types: A dictionary mapping parameter names to the expected types. Each type can be a single type or a list of types.
        none_is_ok: If True, allows None as a valid value.
        errors: A string that determines the error handling strategy. If set to 'raise', the function will raise a TypeError when a mismatch is found.
                If set to 'coerce', the function will attempt to coerce the value to the expected type.

    Raises:
        TypeError: If any parameter does not match the expected type and 'errors' is set to 'raise'.
        ValueError: If any required parameter is missing.

    Returns:
        bool: True if the data is valid, False otherwise.

    Usage example:
        >>> from WrenchCL.Tools import typechecker

        >>> data = [
        >>>     {"name": "John", "age": 30},
        >>>     {"name": "Jane", "age": "twenty"}
        >>> ]
        >>> expected_types = {"name": str, "age": int}

        >>> try:
        >>>     result = typechecker(data, expected_types, none_is_ok=False, errors='raise')
        >>>     print("Data is valid:", result)
        >>> except (TypeError, ValueError) as e:
        >>>     print(f"Validation failed: {e}")

        # This will raise a TypeError because the age of "Jane" is not an int
    """

    # Ensure data is iterable
    if not isinstance(data, Iterable) or isinstance(data, (str, bytes)):
        data = [data] if data is not None else []

    for item in data:
        # Check for incorrect types
        for param, expected in expected_types.items():
            logger.debug(f"Checking param: {param}, expected type(s): {expected}")

            if not isinstance(item, dict):
                item = {param: item}
                logger.debug(f"Converted item to dict: {item}")

            if none_is_ok and item.get(param) is None:
                continue

            actual_type = type(item.get(param))
            if isinstance(expected, list):
                if not any(isinstance(item.get(param), exp) for exp in expected):
                    error_message = f"'{param}' is {actual_type.__name__}, expected one of {[t.__name__ for t in expected]}"
                    if errors == 'raise':
                        raise TypeError(f"Incorrect param types: {error_message}")
                    elif errors == 'coerce':
                        logger.warning(f"Invalid input found when checking input dictionary: {error_message}")
                        return False
            else:
                if not isinstance(item.get(param), expected):
                    error_message = f"'{param}' is {actual_type.__name__}, expected {expected.__name__}"
                    if errors == 'raise':
                        raise TypeError(f"Incorrect param types: {error_message}")
                    elif errors == 'coerce':
                        logger.warning(f"Invalid input found when checking input dictionary: {error_message}")
                        return False

    return True

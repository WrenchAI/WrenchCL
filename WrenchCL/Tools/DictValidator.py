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

#
#  MIT License
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#
#
#  All works within the Software are owned by their respective creators and are distributed by Wrench.AI.
#
#  For inquiries, please contact Willem van der Schans through the official Wrench.AI channels or directly via GitHub at [Kydoimos97](https://github.com/Kydoimos97).
#

from typing import Any, Dict, Type, Literal
from .WrenchLogger import logger


def validate_input_dict(
    params: Dict[str, Any],
    expected_types: Dict[str, Type],
    errors: Literal['raise', 'coerce'] = 'raise'
) -> None:
    """
    Validates that each entry in a dictionary matches the expected type.

    This function iterates through a dictionary of parameters (params) and checks
    each value against a corresponding expected type defined in expected_types. If
    the type does not match, the function will either raise a TypeError or attempt
    to coerce the value to the correct type based on the 'errors' argument.

    Args:
        params: A dictionary of parameters to validate, where the key is a string
                representing the name of the parameter, and the value is the value
                of the parameter.
        expected_types: A dictionary mapping parameter names to the expected types.
                        The keys should correspond to keys in 'params'.
        errors: A string that determines the error handling strategy. If set to
                'raise', the function will raise a TypeError when a mismatch is found.
                If set to 'coerce', the function will attempt to coerce the value
                to the expected type.

    Raises:
        TypeError: If any parameter does not match the expected type and 'errors'
                   is set to 'raise'.
    """
    # Check for missing parameters
    missing_params = [param for param in expected_types if param not in params]
    if missing_params:
        raise ValueError(f"Missing required params: {', '.join(missing_params)}")

    # Check for incorrect types
    incorrect_types = {
        param: type(params[param])
        for param, expected in expected_types.items()
        if not isinstance(params[param], expected)
    }
    if incorrect_types:
        error_messages = [
            f"'{param}' is {actual.__name__}, expected {expected_types[param].__name__}"
            for param, actual in incorrect_types.items()
        ]
        if errors == 'raise':
            raise TypeError(f"Incorrect param types: {', '.join(error_messages)}")
        elif errors == 'coerce':
            logger.warning(f"Invalid input found when checking input dictionary {error_messages}")

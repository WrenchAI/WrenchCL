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
import json
from datetime import datetime, date
from decimal import Decimal


def robust_serializer(obj):
    """
    JSON serializer for objects not serializable by default JSON code.

    This function handles various types that are not natively serializable by the
    `json` module, including `datetime`, `date`, `Decimal`, and custom objects.

    The serialization logic is as follows:

    - `datetime` and `date` objects are converted to their ISO 8601 string representation.
    - `Decimal` objects are converted to floats.
    - Custom objects with a `__dict__` attribute are converted to their dictionary representation.
    - All other objects are converted to their string representation as a fallback.

    :param obj: The object to serialize.
    :type obj: Any
    :return: A JSON serializable representation of the object.
    :rtype: str, dict, float
    :raises TypeError: If the object cannot be serialized.

    Example:

    >>> robust_serializer(datetime(2024, 5, 17))
    '2024-05-17T00:00:00'

    >>> robust_serializer(Decimal('123.45'))
    123.45

    >>> class CustomObject:
    ...     def __init__(self, value):
    ...         self.value = value
    ...
    >>> obj = CustomObject(10)
    >>> robust_serializer(obj)
    {'value': 10}

    >>> robust_serializer(set([1, 2, 3]))
    '{1, 2, 3}'

    Using robust_serializer with json.dumps:

    >>> data = {
    ...     "name": "Alice",
    ...     "timestamp": datetime.now(),
    ...     "balance": Decimal("123.45"),
    ...     "birth_date": date.today(),
    ...     "custom": CustomObject(10)
    ... }
    >>> json.dumps(data, default=robust_serializer, indent=4)
    {
        "name": "Alice",
        "timestamp": "2024-05-17T12:34:56.789012",
        "balance": 123.45,
        "birth_date": "2024-05-17",
        "custom": {
            "value": 10
        }
    }
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif hasattr(obj, "__dict__"):
        return obj.__dict__
    else:
        return str(obj)  # Fallback for other types

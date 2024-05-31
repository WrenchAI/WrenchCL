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
import re
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


class single_quote_decoder(json.JSONDecoder):
    """
    A custom JSON decoder that pre-processes JSON strings to handle single quotes and Markdown block markers.
    Used when decoding JSON output from LLM's as they often use the wrong syntax
    
    This class extends the default `json.JSONDecoder` to allow for the decoding of JSON strings that:
    - Use single quotes for keys and values instead of double quotes.
    - May include Markdown block markers for JSON code blocks.

    :param object_hook: Optional function that will be called with the result of any object literal decoded (a dict). 
                        The return value of `object_hook` will be used instead of the `dict`. This can be used to 
                        provide custom deserializations (e.g., to support JSON-RPC class hinting).
    :param args: Additional positional arguments passed to the base `json.JSONDecoder`.
    :param kwargs: Additional keyword arguments passed to the base `json.JSONDecoder`.

    method decode: Decodes a JSON string after pre-processing it to handle single quotes and remove Markdown block markers.
    :param s: The JSON string to be decoded.
    :param args: Additional positional arguments passed to the base `decode` method.
    :param kwargs: Additional keyword arguments passed to the base `decode` method.
    :return: The Python object represented by the JSON string.

    Usage example:
        >>> import json
        >>> json_str = "{'name': 'John', 'age': 30, 'city': 'New York'}"
        >>> decoded_obj = json.loads(json_str, cls=single_quote_decoder)
        >>> print(decoded_obj)
        {'name': 'John', 'age': 30, 'city': 'New York'}
    """

    def __init__(self, object_hook=None, *args, **kwargs):
        super().__init__(object_hook=object_hook, *args, **kwargs)
        self.object_hook = object_hook

    def decode(self, s, *args, **kwargs):
        # Remove Markdown block markers if present
        s = re.sub(r'```json\s*', '', s)
        s = re.sub(r'```python\s*', '', s)
        s = re.sub(r'\s*```', '', s)

        # Pre-process string values for proper quote handling
        s = re.sub(r"(?<!\\)'(\w+)'", r'"\1"', s)  # Replace single quotes
        s = s.replace("\\'", "'")  # Fixes escaped quotes

        # Decode the pre-processed JSON string
        return super().decode(s, *args, **kwargs)
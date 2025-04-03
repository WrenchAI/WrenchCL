
#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

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
    A custom JSON decoder that preprocesses JSON strings to handle single quotes, Markdown block markers,
    and unescaped double quotes within string values. This is useful when decoding JSON output from LLMs
    as they often use incorrect syntax.

    This class extends the default `json.JSONDecoder` to allow for the decoding of JSON strings that:
    - Use single quotes for keys and values instead of double quotes.
    - May include Markdown block markers for JSON code blocks.
    - Contain unescaped double quotes within string values.

    :param object_hook: Optional function that will be called with the result of any object literal decoded (a dict).
                        The return value of `object_hook` will be used instead of the `dict`. This can be used to
                        provide custom deserializations (e.g., to support JSON-RPC class hinting).
    :param args: Additional positional arguments passed to the base `json.JSONDecoder`.
    :param kwargs: Additional keyword arguments passed to the base `json.JSONDecoder`.

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
        # Remove everything before ```json or ```python, including the marker itself
        s = re.sub(r'.*?```json\s*', '', s, flags=re.DOTALL)
        s = re.sub(r'.*?```python\s*', '', s, flags=re.DOTALL)

        # Remove trailing Markdown block marker
        s = re.sub(r'\s*```', '', s)

        # Replace single quotes around keys and values with double quotes
        s = re.sub(r"(?<!\\)'(\w+)'", r'"\1"', s)  # Replace single quotes around keys

        # Replace single quotes around string values with double quotes, considering the context
        s = re.sub(r'(?<!\\)\'([^\']*?)\'', r'"\1"', s)  # Replace single quotes around values

        # Properly handle escaped double quotes within string values
        s = re.sub(r'(?<!\\)"([^\"]*?)(?<!\\)"', lambda match: match.group(0).replace('"', '\\"'), s)

        s = s.replace("\\'", "'")  # Fixes escaped single quotes
        s = s.replace('\\"', '"')  # Fixes double quotes within string values

        # Sanitize unescaped quotes
        return self.sanitize_unescaped_quotes_and_load_json_str(s, **kwargs)

    @staticmethod
    def sanitize_unescaped_quotes_and_load_json_str(s: str, strict=False) -> dict:
        """
        Sanitizes a JSON string by escaping unescaped quotes and then loads it into a dictionary.

        :param s: The JSON string to be sanitized and loaded.
        :param strict: Whether to use strict JSON parsing.
        :return: The loaded JSON object as a dictionary.
        """
        js_str = s
        prev_pos = -1
        curr_pos = 0
        while curr_pos > prev_pos:
            prev_pos = curr_pos
            try:
                return json.loads(js_str, strict=strict)
            except json.JSONDecodeError as err:
                curr_pos = err.pos
                if curr_pos <= prev_pos:
                    raise err

                # Find the previous " before e.pos
                prev_quote_index = js_str.rfind('"', 0, curr_pos)
                if prev_quote_index == -1:
                    raise err

                # Escape it to \"
                js_str = js_str[:prev_quote_index] + "\\" + js_str[prev_quote_index:]


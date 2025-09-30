#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
import json
import re
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID


def robust_serializer(obj: Any) -> Any:
    """
    JSON serializer for objects not serializable by default JSON code.

    Handles common non-serializable types:
    - datetime/date → ISO 8601 string
    - Decimal → float
    - UUID → string
    - Path → string
    - Enum → value or name
    - set/frozenset → list
    - bytes/bytearray → hex string
    - Pydantic models → dict via .model_dump() or .dict()
    - Dataclasses → dict via asdict()
    - Custom objects with __dict__ → dict
    - Fallback → str()
    """

    # datetime/date
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    # Decimal
    if isinstance(obj, Decimal):
        return float(obj)

    # UUID
    if isinstance(obj, UUID):
        return str(obj)

    # Path
    if isinstance(obj, Path):
        return str(obj)

    # Enum
    if isinstance(obj, Enum):
        return obj.value if isinstance(obj.value, (str, int, float, bool, type(None))) else obj.name

    # set/frozenset
    if isinstance(obj, (set, frozenset)):
        return list(obj)

    # bytes/bytearray
    if isinstance(obj, (bytes, bytearray)):
        return obj.hex()

    # Pydantic model v2
    if hasattr(obj, "model_dump") and callable(getattr(obj, "model_dump")):
        return obj.model_dump()

    # Pydantic model v1
    if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
        return obj.dict()

    # Dataclass
    if hasattr(obj, "__dataclass_fields__"):
        # Avoid import of dataclasses.asdict — emulate
        return {f: getattr(obj, f) for f in obj.__dataclass_fields__}

    # Generic objects
    if hasattr(obj, "__dict__"):
        return obj.__dict__

    # Last fallback
    return str(obj)


class RobustJSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that uses robust_serializer for unsupported objects.
    """

    def default(self, obj: Any) -> Any:
        return robust_serializer(obj)


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

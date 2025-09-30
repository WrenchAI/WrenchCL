#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import json
from typing import Any


def truncate_display(value: Any, max_length: int = 200, max_items: int = 10) -> str:
    """
    Safely converts any value into a string for logging, truncating fields that are too long.

    :param value: Any Python object (dict, list, str, etc.).
    :param max_length: Max characters allowed per string field before truncation.
    :param max_items: Max items to display for lists/dicts before truncation.
    :return: A truncated string representation of the value.
    """

    def _truncate(obj: Any) -> Any:
        if isinstance(obj, str):
            return obj if len(obj) <= max_length else obj[:max_length] + "...[truncated]"
        elif isinstance(obj, list):
            truncated = [_truncate(x) for x in obj[:max_items]]
            if len(obj) > max_items:
                truncated.append(f"...[{len(obj) - max_items} more items truncated]")
            return truncated
        elif isinstance(obj, dict):
            truncated = {}
            for i, (k, v) in enumerate(obj.items()):
                if i >= max_items:
                    truncated["..."] = f"[{len(obj) - max_items} more keys truncated]"
                    break
                truncated[_truncate(k)] = _truncate(v)
            return truncated
        else:
            return obj

    try:
        return json.dumps(_truncate(value), default=str, ensure_ascii=False)
    except Exception:
        return str(value)

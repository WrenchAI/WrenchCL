#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import inspect
import re
from difflib import get_close_matches
from typing import Optional


class _ExceptionSuggestor:
    @staticmethod
    def suggest_similar(error: BaseException, frame_depth=20, n_suggestions=1, cutoff=0.6) -> Optional[str]:
        if not isinstance(error, BaseException):
            return None
        error_msg = error.args[0]
        if not error.__class__.__name__.lower() in error_msg.lower():
            error_msg = f"  {error.__class__.__name__}: {error_msg}"
        else:
            error_msg = f"  {error_msg}"

        obj_match = re.search(r"'(\w+)' object has no attribute", error_msg)
        key_match = re.search(r"has no attribute '(\w+)'", error_msg)

        if not key_match:
            return error_msg

        source_obj = obj_match.group(1) if obj_match else None
        missing_attr = key_match.group(1)

        for frame in reversed(inspect.stack()[:frame_depth]):
            for var in frame.frame.f_locals.values():
                if not hasattr(var, '__class__'):
                    continue
                if var.__class__.__name__ == source_obj:
                    keys = [k for k in dir(var) if not k.startswith('__')]
                    matches = get_close_matches(missing_attr, keys, n=n_suggestions, cutoff=cutoff)
                    if matches:
                        return f"{error_msg}\n    Did you mean: {', '.join(matches)}?\n"
        return error_msg

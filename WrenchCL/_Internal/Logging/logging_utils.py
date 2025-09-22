#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
import inspect
import os
import re
from datetime import datetime
from typing import Callable, Optional, Any


def __set_ansi_fn() -> Callable:
    _ansi_re = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def strip_ansi(text: str) -> str:
        return _ansi_re.sub('', text)

    try:
        from ansi2txt import Ansi2Text
        _ansi = Ansi2Text()

        def strip_ansi(text: str) -> str:
            return _ansi.convert(text)
    except Exception:
        pass
    return strip_ansi


__strip_ansi_fn: Callable = __set_ansi_fn()


def remove_ansi(text: str) -> str:
    return __strip_ansi_fn(text)


def ensure_str(val: bytes | str) -> Any:
    return val.decode("utf-8") if isinstance(val, bytes) else val


def get_depth(internal=False) -> int:
    """Get stack depth to determine log source."""
    for i, frame in enumerate(inspect.stack()):
        if frame.filename.endswith("cLogger.py") or 'WrenchCL' in frame.filename or frame.filename == '<string>':
            if internal:
                return i + 2
            else:
                continue
        return i
    # Fallback: If stack inspection fails, return depth 1 (assume direct caller).
    return 1


def suggest_exception(args) -> Optional[str]:
    """Generate improvement suggestions for certain exceptions."""
    suggestion = None
    if not hasattr(args, '__iter__') and args is not None:
        args = [args]
    else:
        return suggestion

    for a in args:
        if isinstance(a, Exception) or isinstance(a, BaseException):
            ex = a
            if hasattr(ex, 'args') and ex.args and isinstance(ex.args[0], str):
                from ...Exceptions.ExceptionSuggestor import ExceptionSuggestor
                suggestion = ExceptionSuggestor.suggest(ex)
            break
    return suggestion


def generate_run_id() -> str:
    """Generate a unique run ID for this logger instance."""
    now = datetime.now()
    return f"R-{os.urandom(1).hex().upper()}{now.strftime('%m%d')}{os.urandom(1).hex().upper()}"

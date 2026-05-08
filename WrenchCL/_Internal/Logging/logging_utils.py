#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
import re
import sys
import threading
from types import FrameType
from typing import Any, Callable, Optional


def __set_ansi_fn() -> Callable:
    _ansi_re = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    def strip_ansi(text: str) -> str:
        return _ansi_re.sub("", text)

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


_WCL_MODULE_PREFIX = "WrenchCL"
_FRAME_WALK_LIMIT = 25
_PROBE_DEPTH = 500
_cached_base_level: Optional[int] = None
_base_level_lock = threading.Lock()


def _owns_frame(frame: FrameType) -> bool:
    """Return True when the frame belongs to the WrenchCL package."""
    return str(frame.f_globals.get("__name__", "")).startswith(_WCL_MODULE_PREFIX)


def _measure_base_level() -> int:
    """
    Emit one probe record and walk its frame chain to find the first
    non-WrenchCL frame. Result is cached for the process lifetime.
    """
    import logging

    measured = 3

    class _Probe(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            nonlocal measured
            f: Optional[FrameType] = sys._getframe(0)
            for depth in range(1, _PROBE_DEPTH):
                if f is None:
                    break
                if not _owns_frame(f):
                    measured = depth
                    return
                f = f.f_back

    _logger = logging.getLogger("_wcl_depth_probe")
    _logger.propagate = False
    _h = _Probe()
    _logger.addHandler(_h)
    try:
        _logger.debug("probe")
    finally:
        _logger.removeHandler(_h)
    return measured


def get_depth(internal: bool = False) -> int:
    """
    Return the stacklevel needed to attribute a log record to the caller's
    call site rather than to WrenchCL internals.

    Walks frames lazily via sys._getframe. Falls back to a one-time measured
    baseline when the walk exhausts the depth limit or fails.
    """
    offset = 1 if internal else 0
    try:
        frame: Optional[FrameType] = sys._getframe(2)
        for depth in range(1, _FRAME_WALK_LIMIT):
            if frame is None:
                break
            if not _owns_frame(frame):
                return depth + offset
            frame = frame.f_back
    except (ValueError, AttributeError):
        pass

    global _cached_base_level
    if _cached_base_level is None:
        with _base_level_lock:
            if _cached_base_level is None:
                _cached_base_level = _measure_base_level()
    return (_cached_base_level + offset) if _cached_base_level is not None else (1 + offset)


def suggest_exception(args) -> Optional[str]:
    """Generate improvement suggestions for certain exceptions."""
    suggestion = None
    if not hasattr(args, "__iter__") and args is not None:
        args = [args]
    else:
        return suggestion

    for a in args:
        if isinstance(a, Exception) or isinstance(a, BaseException):
            ex = a
            if hasattr(ex, "args") and ex.args and isinstance(ex.args[0], str):
                from ...Exceptions.ExceptionSuggestor import ExceptionSuggestor

                suggestion = ExceptionSuggestor.suggest(ex)
            break
    return suggestion


def generate_run_id() -> str:
    """Generate a unique 5-character uppercase alphanumeric run ID."""
    import random
    import string
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=5))

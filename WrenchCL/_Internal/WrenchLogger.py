# Copyright (c) 2024-2025.
# Author: Willem van der Schans.
# Licensed under the MIT License (https://opensource.org/license/mit).
import contextvars
import logging
import uuid
import warnings
from typing import Any, Self

from logspark.Core.SparkLogger import SparkLogger
from logspark.Handlers import SparkJsonHandler, SparkTerminalHandler

from WrenchCL.Decorators import SingletonClass

_run_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "wrench_run_id",
    default=None,
)
_prefix_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "wrench_prefix",
    default=None,
)


class _PrefixFilter(logging.Filter):
    """Prepends the per-context prefix (e.g. HTTP method + path) to each log record.

    Reads from _prefix_var which is async-safe via contextvars — each asyncio task
    (i.e. each HTTP request) gets its own copy when set via logger.set_prefix().
    """

    def filter(self, record: logging.LogRecord) -> bool:
        prefix = _prefix_var.get()
        if prefix:
            record.msg = f"[{prefix}] {record.msg}"
        return True


@SingletonClass
class WrenchLogger(SparkLogger):
    def configure(  # type: ignore
        self,
        mode: str | None = None,
        level: str | int = "INFO",
        *,
        color_enabled: bool = True,
        highlight_syntax: bool = False,
        verbose: bool = False,
        trace_enabled: bool = False,
        deployment_mode: bool = False,
        suppress_autoconfig: bool = False,
        prefix: str | None = None,
        show_thread_name: bool = False,
        **kwargs: Any,
    ) -> None:
        _ = (
            color_enabled,
            highlight_syntax,
            verbose,
            trace_enabled,
            suppress_autoconfig,
            show_thread_name,
            kwargs,
        )
        if isinstance(level, str):
            level = level.upper()
        handler = SparkJsonHandler() if (mode == "json" or deployment_mode) else SparkTerminalHandler()
        self.eject_filters()
        super().configure(level=level, handler=handler, no_freeze=True)
        self.addFilter(_PrefixFilter())
        if prefix is not None:
            self.set_prefix(prefix)

    def initiate_new_run(self) -> str:
        run_id = uuid.uuid4().hex[:8].upper()
        _run_id_var.set(run_id)
        return run_id

    def cycle_run(self) -> str:
        return self.initiate_new_run()

    @property
    def run_id(self) -> str | None:
        return _run_id_var.get()

    @property
    def instance(self) -> Self:
        return self

    @property
    def level(self) -> "_LevelCompat":
        return _LevelCompat(self.__dict__.get("level", logging.NOTSET))

    @level.setter
    def level(self, value: int | str) -> None:
        if isinstance(value, str):
            numeric = logging.getLevelName(value)
            self.__dict__["level"] = numeric if isinstance(numeric, int) else logging.NOTSET
        else:
            self.__dict__["level"] = int(value)

    @property
    def streams(self) -> "_StreamsShim":
        return _StreamsShim(self)

    def success(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        warnings.warn(
            "logger.success() is deprecated, use logger.info()",
            UserWarning,
            stacklevel=2,
        )
        kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
        self.info(msg, *args, **kwargs)

    def data(self, obj: Any, compact: bool = False, **kwargs: Any) -> None:
        _ = compact
        warnings.warn(
            "logger.data() is deprecated, use logger.info()",
            UserWarning,
            stacklevel=2,
        )
        kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
        self.info(obj, **kwargs)

    def cdata(self, data: Any, **kwargs: Any) -> None:
        warnings.warn(
            "logger.cdata() is deprecated, use logger.info()",
            UserWarning,
            stacklevel=2,
        )
        kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
        self.info(data, **kwargs)

    def header(
        self,
        text: Any,
        size: Any = None,
        compact: bool = False,
        return_repr: bool = False,
        level: str = "HEADER",
        **kwargs: Any,
    ) -> None:
        _ = (size, compact, return_repr, level)
        warnings.warn(
            "logger.header() is deprecated, use logger.info()",
            UserWarning,
            stacklevel=2,
        )
        kwargs["stacklevel"] = kwargs.get("stacklevel", 1) + 1
        self.info(text, **kwargs)

    def set_prefix(self, prefix: str | None) -> None:
        """Set a per-context log prefix (e.g. HTTP method + path for request tagging).

        The value is stored in a ContextVar, so each asyncio task (HTTP request)
        gets its own isolated copy. Pass None to clear the prefix for the current context.
        """
        _prefix_var.set(prefix)

    @property
    def _internal(self) -> "_InternalLogShim":
        return _InternalLogShim(self)


class _InternalLogShim:
    """Shim for logger._internal.log_internal() calls in Connect/Tools modules."""

    def __init__(self, logger: Any) -> None:
        self._logger = logger

    def log_internal(self, *args: Any, **kwargs: Any) -> None:
        msg = " ".join(str(a) for a in args)
        self._logger.debug(msg, stacklevel=kwargs.get("stacklevel", 2) + 1)


class _LevelCompat(int):
    """int subclass that exposes .value for WrenchCL compat (logger.level.value)."""

    @property
    def value(self) -> int:
        return int(self)


class _StreamsShim:
    """Minimal shim for logger.streams.attach() used in AiAxis init."""

    def __init__(self, logger: Any) -> None:
        self._logger = logger

    def attach(
        self,
        level: str = "ERROR",
        silence_others: bool = False,
        stream: Any = None,
    ) -> None:
        _ = (self._logger, silence_others, stream)
        root = logging.getLogger()
        handler = SparkTerminalHandler()
        handler.setLevel(level)
        root.addHandler(handler)

    def intercept_exceptions(
        self,
        install_hooks: bool = True,
        std_stream_mode: str = "none",
    ) -> None:
        _ = (install_hooks, std_stream_mode)
        warnings.warn(
            "logger.streams.intercept_exceptions() is not supported in WrenchCL v6.",
            UserWarning,
            stacklevel=2,
        )

    def suppress(self, mode: str = "both") -> None:
        _ = mode
        warnings.warn(
            "logger.streams.suppress() is not supported in WrenchCL v6.",
            UserWarning,
            stacklevel=2,
        )

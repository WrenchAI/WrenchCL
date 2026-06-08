# Copyright (c) 2024-2025.
# Author: Willem van der Schans.
# Licensed under the MIT License (https://opensource.org/license/mit).
import contextvars
import logging
import uuid
import warnings
from typing import Any

from logspark.Core.SparkLogger import SparkLogger as _SparkLoggerDecorated
from logspark.Handlers import SparkJsonHandler, SparkTerminalHandler

from WrenchCL.Decorators import SingletonClass

_BaseSparkLogger = _SparkLoggerDecorated.__bases__[0]
_run_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "wrench_run_id",
    default=None,
)


@SingletonClass
class WrenchLogger(_BaseSparkLogger):
    def configure(
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
        handler = SparkJsonHandler() if (mode == "json" or deployment_mode) else SparkTerminalHandler()
        self.eject_filters()
        super().configure(level=level, handler=handler, no_freeze=True)
        set_prefix = getattr(self, "set_prefix", None)
        if prefix is not None and callable(set_prefix):
            set_prefix(prefix)

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
    def instance(self) -> "WrenchLogger":
        return self

    @property
    def level(self) -> "_LevelCompat":
        return _LevelCompat(self.__dict__.get("level", logging.NOTSET))

    @level.setter
    def level(self, value: int | str) -> None:
        self.__dict__["level"] = logging._checkLevel(value)

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


class _LevelCompat(int):
    """int subclass that exposes .value for WrenchCL compat (logger.level.value)."""

    @property
    def value(self) -> int:
        return int(self)


class _StreamsShim:
    """Minimal shim for logger.streams.attach() used in AiAxis init."""

    def __init__(self, logger: WrenchLogger) -> None:
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

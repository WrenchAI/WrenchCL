#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import logging
import sys
import threading
from io import TextIOBase
from typing import List, Dict, Optional, Type, Literal

from typing_extensions import TYPE_CHECKING

from .._custom_types import StdStreamMode

if TYPE_CHECKING:
    from .LoggerConfigState import LoggerConfigState

from ...Decorators import SingletonClass
from .DataClasses import LogLevel, logLevels
from .Formatters import FileLogFormatter


@SingletonClass
class GlobalLoggerManager:
    """
    Root-level logging governance:
      1) Ensure root logger emits via WrenchCL formatters
      2) Enable selective silencing for package loggers
      3) Optionally install exception hooks and suppress std streams
    """

    def __init__(self, formatter_factory, handler_manager, internal_logger):
        self.formatter_factory = formatter_factory
        self.handler_manager = handler_manager
        self.internal_logger = internal_logger
        self._lock = threading.RLock()
        self._global_stream_configured = False
        self._hooks_installed = False
        self._suppression_mode: StdStreamMode = StdStreamMode.NONE
        self._saved_streams = None  # (stdout, stderr, __stdout__, __stderr__)

    # ---------- 1) Wire the root logger to WrenchCL formatters ----------
    def attach_global_stream(
            self,
            level: logLevels,
            stream=sys.stdout,
            *,
            silence_others: bool = False,
            exclude_loggers: Optional[List[str]] = None,
            config_state=None,
            env_metadata=None,
            ) -> None:
        with self._lock:
            self.handler_manager.flush_all_handlers()
            root_logger = logging.getLogger()
            root_logger.setLevel(level or "INFO")

            formatter = self.formatter_factory.create_formatter(
                    level=level,
                    config_state=config_state,
                    env_metadata=env_metadata,
                    global_stream_configured=True,
                    )

            handler = logging.StreamHandler(stream)
            handler.setLevel(level or "INFO")
            handler.setFormatter(formatter)

            root_logger.handlers = [handler]
            root_logger.propagate = False

            if silence_others:
                if exclude_loggers:
                    for logger_name in logging.root.manager.loggerDict:
                        if logger_name not in exclude_loggers:
                            self.silence_logger(logger_name)
                else:
                    self.silence_other_loggers()

            self._global_stream_configured = True
            self._log_global_stream_status(root_logger)

    # ---------- 2) Install exception interception & select suppression ----------
    def configure_interception(
            self,
            *,
            install_hooks: bool = True,
            std_stream_mode: StdStreamMode = StdStreamMode.NONE,
            ) -> None:
        with self._lock:
            root_logger = logging.getLogger()
            if install_hooks and not self._hooks_installed:
                self._install_exception_hooks(root_logger)
                self._hooks_installed = True

            # apply suppression after hooks, so any fallback prints are neutralized
            self._apply_std_stream_suppression(std_stream_mode)

            root_logger.debug(
                    f"Interception configured. hooks_installed={self._hooks_installed}, "
                    f"std_stream_mode={self._suppression_mode.value}"
                    )

    # ---------- 3) Fine control for stream suppression (can be called independently) ----------
    def suppress_std_streams(self, mode: StdStreamMode) -> None:
        with self._lock:
            self._apply_std_stream_suppression(mode)

    # ---------- selective logger controls (unchanged logic) ----------
    def set_named_logger_level(self, logger_name: str, level: logLevels = 'INFO') -> None:
        level = LogLevel(level)
        with self._lock:
            loggers = logging.root.manager.loggerDict
            name_map = {name.lower(): name for name in loggers}
            normalized_name = logger_name.lower()

            if normalized_name not in name_map:
                self._log_logger_not_found(logger_name, name_map)
                return

            actual_name = name_map[normalized_name]
            logger = logging.getLogger(actual_name)
            logger.setLevel(int(level))

            if int(level) > logging.CRITICAL:
                logger.handlers = [logging.NullHandler()]
                logger.propagate = False
                self.internal_logger(f"🔇 Logger '{actual_name}' silenced (level={level})")
            else:
                logger.propagate = True
                self.internal_logger(f"🔧 Logger '{actual_name}' set to level {level}")

    def silence_logger(self, logger_name: str) -> None:
        level = logging.CRITICAL + 1
        self.set_named_logger_level(logger_name, level)

    def silence_other_loggers(self, exclude_logger: str = 'WrenchCL') -> None:
        silenced_count = 0
        for name in logging.root.manager.loggerDict:
            if name != exclude_logger:
                self.silence_logger(name)
                silenced_count += 1
        self.internal_logger(f"🔇 Silenced {silenced_count} loggers (excluded: {exclude_logger})")

    def refresh_root_formatter(self, config_state, env_metadata) -> None:
        """
        Re-bind the formatter for the root/global handler(s) to keep output shape
        (JSON/terminal fields) in sync with WrenchCL without touching levels or streams.
        No-ops if no global stream is configured.
        """
        if not self._global_stream_configured:
            return

        with self._lock:
            root = logging.getLogger()
            for h in root.handlers:
                if isinstance(h, logging.NullHandler):
                    continue
                fmt = self.formatter_factory.create_formatter(
                        level=config_state.level,  # used for record decoration only
                        config_state=config_state,
                        env_metadata=env_metadata,
                        global_stream_configured=True,
                        )
                h.setFormatter(fmt)

    def set_root_level(self, level: "logLevels") -> None:
        """
        Explicitly set the root logger effective level (does not touch instance).
        """
        with self._lock:
            lvl = int(LogLevel(level))
            root = logging.getLogger()
            root.setLevel(lvl)
            for h in root.handlers:
                if isinstance(h, logging.NullHandler):
                    continue
                h.setLevel(lvl)

    @staticmethod
    def get_active_loggers() -> List[str]:
        return [
                name for name in logging.root.manager.loggerDict
                if isinstance(logging.getLogger(name), logging.Logger)
                ]

    @staticmethod
    def get_logger_info() -> Dict[str, Dict]:
        info = {}
        for name in logging.root.manager.loggerDict:
            logger = logging.getLogger(name)
            if isinstance(logger, logging.Logger):
                info[name] = {
                        'level': logger.level,
                        'level_name': logging.getLevelName(logger.level),
                        'handlers': [type(h).__name__ for h in logger.handlers],
                        'propagate': logger.propagate,
                        'disabled': logger.disabled
                        }
        return info

    def cleanup_global_handlers(self):
        if self._global_stream_configured:
            root_logger = logging.getLogger()
            for handler in list(root_logger.handlers):
                try:
                    handler.close()
                    root_logger.removeHandler(handler)
                except Exception:
                    pass
            self._global_stream_configured = False

    @property
    def is_global_stream_configured(self) -> bool:
        return self._global_stream_configured

    # ---------- internals ----------
    def _install_exception_hooks(self, root_logger: logging.Logger) -> None:
        def handle_uncaught(exc_type, exc_value, exc_tb):
            if issubclass(exc_type, KeyboardInterrupt):
                return sys.__excepthook__(exc_type, exc_value, exc_tb)
            root_logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))

        def handle_thread(args: threading.ExceptHookArgs):
            root_logger.error(
                    f"Unhandled thread exception in {args.thread.name}",
                    exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
                    )

        def handle_async(loop, context):
            exc = context.get("exception")
            msg = context.get("message")
            root_logger.error(f"Async exception: {msg}", exc_info=exc)

        sys.excepthook = handle_uncaught
        threading.excepthook = handle_thread
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            loop.set_exception_handler(handle_async)
        except RuntimeError:
            pass

        root_logger.debug("✅ Global exception hooks installed.")

    def _apply_std_stream_suppression(self, mode: StdStreamMode) -> None:
        if mode == self._suppression_mode:
            return  # idempotent

        # restore first if we previously suppressed
        if self._suppression_mode != StdStreamMode.NONE and self._saved_streams:
            out, err, o_out, o_err = self._saved_streams
            sys.stdout, sys.stderr = out, err
            sys.__stdout__, sys.__stderr__ = o_out, o_err
            self._saved_streams = None

        if mode == StdStreamMode.NONE:
            self._suppression_mode = mode
            return

        class _NullStream:
            def write(self, *_a, **_kw): return 0

            def flush(self): return 0

            def isatty(self): return False

            def writelines(self, *_a, **_kw): return 0

        self._saved_streams = (sys.stdout, sys.stderr, sys.__stdout__, sys.__stderr__)
        null_stream = _NullStream()

        if mode == StdStreamMode.STDERR:
            sys.stderr = null_stream
            sys.__stderr__ = null_stream
        elif mode == StdStreamMode.BOTH:
            sys.stdout = null_stream
            sys.stderr = null_stream
            sys.__stdout__ = null_stream
            sys.__stderr__ = null_stream

        self._suppression_mode = mode
        logging.getLogger().debug(f"✅ Std stream suppression applied: {mode.value}")

    def _log_global_stream_status(self, root_logger):
        active_loggers = self.get_active_loggers()
        handler_count = len(root_logger.handlers)
        root_loggers = sorted({v.split('.')[0] for v in active_loggers})
        if len(root_loggers) > 10:
            joined_loggers = ', '.join(root_loggers[:10]) + f'...<{len(root_loggers) - 10} more>'
        else:
            joined_loggers = ', '.join(root_loggers)
        self.internal_logger(
                f"✅ Global stream attached to root with {handler_count} handler(s).\n"
                f"🔎 Active loggers: {len(active_loggers)}\n"
                f"📝 Roots: {joined_loggers}"
                )
        self.internal_logger("Global stream configured successfully.")

    def _log_logger_not_found(self, logger_name: str, name_map: Dict[str, str]) -> None:
        """Internal diagnostic when a target logger isn't found. Never raises."""
        try:
            from difflib import get_close_matches
            keys = list(name_map.keys())
            matches = get_close_matches(logger_name.lower(), keys, n=1, cutoff=0.6)
            hint = f" Did you mean '{name_map[matches[0]]}'?" if matches else ""
            sample = ", ".join(sorted(name_map.values())[:10])
            extra = f" Available: {sample}..." if sample else ""
            self.internal_logger(f"⚠️ Logger '{logger_name}' not found.{hint}{extra}")
        except Exception:
            pass


class HandlerManager:
    """Manages logging handlers - adding, removing, configuring."""

    def __init__(self, logger_instance: logging.Logger, formatter_factory):
        self.logger_instance = logger_instance
        self.formatter_factory = formatter_factory
        self._lock = threading.RLock()

    # HandlerManager.add_handler
    def add_handler(
            self,
            handler_cls: Type[logging.Handler],
            config_state: "LoggerConfigState",
            stream: Optional[TextIOBase] = None,
            level: logLevels = None,
            force_replace: bool = False,
            base_level: str = 'INFO',
            formatter: Optional[logging.Formatter] = None,
            *,
            owned: bool = True,  # <-- NEW
            ) -> logging.Handler:
        with self._lock:
            eff_level = level or base_level

            if issubclass(handler_cls, logging.StreamHandler):
                if stream is None:
                    raise ValueError("StreamHandler requires a valid `stream` argument.")
                handler = handler_cls(stream)
            else:
                handler = handler_cls()

            handler.setLevel(eff_level)

            if not formatter:
                formatter = self.formatter_factory.create_formatter(eff_level, config_state, {})
            handler.setFormatter(formatter)

            if owned:
                setattr(handler, "_wrench_owned", True)
                if not getattr(handler, "name", None):
                    handler.name = "WrenchCLPrimary"

            if force_replace:
                self.logger_instance.handlers = []

            self.logger_instance.addHandler(handler)
            return handler

    def add_file_handler(
            self,
            filename: str,
            config: "LoggerConfigState",
            max_bytes: int = 10485760,  # 10MB default
            backup_count: int = 5,
            level: logLevels = None,
            formatter: Optional[logging.Formatter] = None,
            base_level: str = 'INFO'
            ) -> Optional[logging.Handler]:
        """Add a rotating file handler."""
        from logging.handlers import RotatingFileHandler

        with self._lock:
            handler = RotatingFileHandler(
                    filename=filename,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    delay=True,
                    encoding="utf-8"
                    )
            level = level or base_level
            handler.setLevel(level)

            # Use ANSI-stripping formatter for files
            base_formatter = self.formatter_factory.create_formatter(level, config, {})
            handler.setFormatter(formatter or FileLogFormatter(base_formatter))

            self.logger_instance.addHandler(handler)
            return handler

    def flush_all_handlers(self):
        """Flush all handlers associated with the logger instance."""
        with self._lock:
            for handler in self.logger_instance.handlers:
                try:
                    handler.flush()
                except Exception:
                    pass

    def update_all_formatters(
            self, config_state, env_metadata: Dict,
            global_stream_configured: bool = False
            ):
        """Update formatters for all handlers based on new config."""
        with self._lock:
            for handler in self.logger_instance.handlers:
                if isinstance(handler, logging.NullHandler):
                    continue
                if getattr(handler, "_wrench_preserve_formatter", False):
                    continue
                owned = bool(getattr(handler, "_wrench_owned", False) or getattr(handler, "_wrench_adopted", False))
                if not owned:
                    continue

                level_name = logging.getLevelName(handler.level)
                base_fmt = self.formatter_factory.create_formatter(
                        level=level_name,
                        config_state=config_state,
                        env_metadata=env_metadata,
                        global_stream_configured=global_stream_configured,
                        )

                from .Formatters import FileLogFormatter
                if isinstance(handler.formatter, FileLogFormatter):
                    handler.setFormatter(FileLogFormatter(base_fmt))
                else:
                    handler.setFormatter(base_fmt)

    def update_handler_levels(
            self,
            level: LogLevel,
            *,
            scope: Literal['owned', 'others', 'all'] = 'owned',
            ) -> None:
        """
        Update handler levels on the WrenchCL logger instance.

        scope='owned'  -> only handlers tagged _wrench_owned (primary/managed)
        scope='others' -> only non-owned, user-attached handlers
        scope='all'    -> both
        """
        with self._lock:
            target_level = logging.getLevelName(int(level))
            for h in self.logger_instance.handlers:
                owned = bool(getattr(h, "_wrench_owned", False))
                if scope == 'owned' and not owned:
                    continue
                if scope == 'others' and owned:
                    continue
                h.setLevel(target_level)

    def close_all_handlers(self):
        """Close all handlers and clean up resources."""
        with self._lock:
            self.flush_all_handlers()
            for handler in list(self.logger_instance.handlers):
                try:
                    handler.close()
                    self.logger_instance.removeHandler(handler)
                except Exception as e:
                    sys.stderr.write(f"Error closing handler: {str(e)}\n")

    def get_handler_info(self) -> Dict[str, Dict]:
        """Get information about all attached handlers."""
        return_dict = {}
        for handler in self.logger_instance.handlers:
            return_dict[getattr(handler, 'name', type(handler).__name__)] = {
                    'level': handler.level,
                    'type': type(handler).__name__
                    }
        return return_dict

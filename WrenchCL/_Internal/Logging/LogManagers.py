#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import logging
import sys
import threading
from difflib import get_close_matches
from io import TextIOBase
from typing import List, Dict, Optional, Type

from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from .LoggerConfigState import LoggerConfigState

from ...Decorators import SingletonClass
from .DataClasses import LogLevel, logLevels
from .Formatters import FileLogFormatter


@SingletonClass
class GlobalLoggerManager:
    """
    Manages the global Python logging ecosystem - root logger, named loggers, etc.

    This service handles all interactions with loggers outside of our main WrenchCL logger,
    keeping that responsibility separate from the core logging functionality.
    """

    def __init__(self, formatter_factory, handler_manager, internal_logger):
        self.formatter_factory = formatter_factory
        self.handler_manager = handler_manager  # For creating handlers
        self.internal_logger = internal_logger  # For logging our own messages
        self._lock = threading.RLock()
        self._global_stream_configured = False

    def attach_global_stream(
            self, level: logLevels, silence_others: bool = False,
            stream=sys.stdout, config_state=None, env_metadata=None
            ) -> None:
        """
        Attaches a global stream handler to the root logger.

        :param level: The logging level for the global stream
        :param silence_others: Flag indicating whether to silence other loggers
        :param stream: The stream to which log messages will be written
        :param config_state: Current logger configuration state
        :param env_metadata: Environment metadata for formatting
        """
        with self._lock:
            self.handler_manager.flush_all_handlers()
            root_logger = logging.getLogger()
            root_logger.setLevel(level or 'INFO')

            # Create formatter using our factory
            formatter = self.formatter_factory.create_formatter(
                    level=level,
                    config_state=config_state,
                    env_metadata=env_metadata,
                    global_stream_configured=True  # This affects the formatter
                    )

            # Create handler
            handler = logging.StreamHandler(stream)
            handler.setLevel(level or 'INFO')
            handler.setFormatter(formatter)

            # Replace all root handlers with our new one
            root_logger.handlers = [handler]
            root_logger.propagate = False

            if silence_others:
                self.silence_other_loggers()

            self._global_stream_configured = True

            # Diagnostic output
            self._log_global_stream_status(root_logger)

    def set_named_logger_level(self, logger_name: str, level: logLevels = 'INFO') -> None:
        """
        Sets the logging level for a named logger in the global logging system.

        :param logger_name: The name of the logger to configure
        :param level: The logging level to set for the specified logger
        """
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

    def set_handler_level_by_name(
            self, handler_name: str, level: Optional[logLevels] = None,
            logger_instance=None, config_state=None, env_metadata=None,
            global_stream_configured=False
            ) -> None:
        """
        Sets the logging level and formatter of an attached handler by name.

        :param handler_name: The name of the handler to modify
        :param level: The logging level to set for the handler
        :param logger_instance: The logger instance to search for handlers
        :param config_state: Current configuration state for formatter creation
        :param env_metadata: Environment metadata for formatter creation
        :param global_stream_configured: Whether global stream is configured
        """
        if not level:
            level = 'INFO'
        level = LogLevel(level)

        if not logger_instance:
            return

        with self._lock:
            for handler in logger_instance.handlers:
                handler_identifier = getattr(handler, 'name', type(handler).__name__)
                if handler_identifier == handler_name:
                    handler.setLevel(int(level))

                    # Create new formatter with updated level
                    new_formatter = self.formatter_factory.create_formatter(
                            level=level,
                            config_state=config_state,
                            env_metadata=env_metadata,
                            global_stream_configured=global_stream_configured
                            )
                    handler.setFormatter(new_formatter)
                    self.internal_logger(f"🔧 Handler '{handler_name}' set to level {level}")
                    break
            else:
                self.internal_logger(f"⚠️ Handler '{handler_name}' not found")

    def silence_logger(self, logger_name: str) -> None:
        """
        Silences a specific logger by setting its level above CRITICAL.

        :param logger_name: The name of the logger to silence
        """
        level = logging.CRITICAL + 1  # Above CRITICAL to effectively silence
        self.set_named_logger_level(logger_name, level)

    def silence_other_loggers(self, exclude_logger: str = 'WrenchCL') -> None:
        """
        Silences all loggers except the specified one.

        :param exclude_logger: Logger name to exclude from silencing
        """
        silenced_count = 0
        for name in logging.root.manager.loggerDict:
            if name != exclude_logger:
                self.silence_logger(name)
                silenced_count += 1

        self.internal_logger(f"🔇 Silenced {silenced_count} loggers (excluded: {exclude_logger})")

    @staticmethod
    def get_active_loggers() -> List[str]:
        """
        Get a list of all active loggers in the system.

        :return: List of active logger names
        """
        return [
                name for name in logging.root.manager.loggerDict
                if isinstance(logging.getLogger(name), logging.Logger)
                ]

    @staticmethod
    def get_logger_info() -> Dict[str, Dict]:
        """
        Get detailed information about all loggers in the system.

        :return: Dictionary with logger info
        """
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
        """Clean up global logging handlers."""
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
        """Check if global stream is configured."""
        return self._global_stream_configured

    # ================== PRIVATE HELPER METHODS ==================

    def _log_global_stream_status(self, root_logger):
        """Log the status of global stream configuration."""
        active_loggers = self.get_active_loggers()
        handler_count = len(root_logger.handlers)
        root_loggers = sorted({v.split('.')[0] for v in active_loggers})

        if len(root_loggers) > 10:
            joined_loggers = ', '.join(root_loggers[:10]) + f'...<{len(root_loggers) - 10} more>'
        else:
            joined_loggers = ', '.join(root_loggers)

        self.internal_logger(
                f"✅ Global stream attached to root logger with {handler_count} handler(s).\n"
                f"🔎 Active loggers detected: {len(active_loggers)}\n"
                f"📝 Accessible root loggers: {joined_loggers}\n"
                f"---Get a full list of active loggers with `active_loggers` property---"
                )
        self.internal_logger("Global stream configured successfully.")

    def _log_logger_not_found(self, logger_name: str, name_map: Dict[str, str]):
        """Log when a requested logger is not found."""
        log_string = f"⚠️ Logger '{logger_name}' not found (case-insensitive match). "
        matches = get_close_matches(logger_name.lower(), name_map, n=1, cutoff=0.6)
        if matches:
            log_string += f"\n Did you mean '{matches[0]}'?"
        else:
            available = sorted(name_map.values())
            if len(available) > 10:
                shown = ', '.join(available[:10]) + f'...<{len(available) - 10} more>'
            else:
                shown = ', '.join(available)
            log_string += f"\nAvailable loggers: {shown}"
        self.internal_logger(log_string)

    def update_global_handlers(
            self,
            config_state: "LoggerConfigState",
            env_metadata: Dict,
            ) -> None:
        """
        Update all root/global handlers to reflect the latest config.
        Called from LoggerStateManager._apply_state_changes().
        """
        with self._lock:
            if not self._global_stream_configured:
                return

            root_logger = logging.getLogger()

            # Sync root logger level to config
            root_logger.setLevel(int(config_state.level))

            for handler in root_logger.handlers:
                # Update level
                handler.setLevel(int(config_state.level))

                # Update formatter
                new_formatter = self.formatter_factory.create_formatter(
                        level=config_state.level,
                        config_state=config_state,
                        env_metadata=env_metadata,
                        global_stream_configured=True,
                        )
                handler.setFormatter(new_formatter)

            self.internal_logger(
                    f"🔧 Global handlers updated (level={config_state.level}, mode={config_state.mode})"
                    )


class HandlerManager:
    """Manages logging handlers - adding, removing, configuring."""

    def __init__(self, logger_instance: logging.Logger, formatter_factory):
        self.logger_instance = logger_instance
        self.formatter_factory = formatter_factory
        self._lock = threading.RLock()

    def add_handler(
            self, handler_cls: Type[logging.Handler],
            config_state: "LoggerConfigState", stream: Optional[TextIOBase] = None,
            level: logLevels = None,
            force_replace: bool = False,
            base_level: str = 'INFO',
            formatter: Optional[logging.Formatter] = None
            ) -> logging.Handler:
        """Add a new logging handler to the logger instance."""

        with self._lock:
            if not level:
                level = base_level

            # Create handler based on type
            if issubclass(handler_cls, logging.StreamHandler):
                if stream is None:
                    raise ValueError("StreamHandler requires a valid `stream` argument.")
                handler = handler_cls(stream)
            else:
                handler = handler_cls()

            handler.setLevel(level)

            if not formatter:
                # This would use our FormatterFactory
                formatter = self.formatter_factory.create_formatter(level, config_state, {})
            handler.setFormatter(formatter)

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
                if not isinstance(handler, logging.NullHandler):
                    new_formatter = self.formatter_factory.create_formatter(
                            level=logging.getLevelName(handler.level),
                            config_state=config_state,
                            env_metadata=env_metadata,
                            global_stream_configured=global_stream_configured
                            )
                    handler.setFormatter(new_formatter)

    def update_handler_levels(self, level: LogLevel):
        """Update levels for all handlers based on new config."""
        with self._lock:
            for handler in self.logger_instance.handlers:
                handler.setLevel(logging.getLevelName(int(level)))

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

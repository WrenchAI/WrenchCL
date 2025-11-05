"""
ManagedLoggers - Manages other loggers and handlers in the system
"""
#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import logging
from io import TextIOBase
from typing import Optional, Union, List, Type

from ..DataClasses import logLevels


class ManagedLoggers:
    """Manages other loggers and handlers in the system"""

    def __init__(self, parent_logger):
        self.parent = parent_logger

    def add(
            self, handler_cls: Type[logging.Handler] = logging.StreamHandler,
            stream: Optional[TextIOBase] = None, level: logLevels = None,
            formatter: Optional[logging.Formatter] = None, force_replace: bool = False,
            owned: bool = True
            ) -> logging.Handler:
        """Add a new logging handler to the logger instance"""
        return self.parent.state_manager.handler_manager.add_handler(
                handler_cls=handler_cls,
                config_state=self.parent.state_manager.current_state,
                stream=stream,
                level=level,
                force_replace=force_replace,
                base_level=self.parent.state_manager.base_level,
                formatter=formatter,
                owned=owned
                )

    def adopt(self, handler: logging.Handler, preserve_formatter: bool = False) -> None:
        """Adopt an existing handler under WrenchCL management"""
        setattr(handler, "_wrench_adopted", True)
        if preserve_formatter:
            setattr(handler, "_wrench_preserve_formatter", True)
        self.parent._internal.log_internal(f"Adopted handler: {type(handler).__name__}")

    def sync(self) -> None:
        """Force all instance handlers to match the logger's current level"""
        self.parent.state_manager.handler_manager.update_handler_levels(
                self.parent.state_manager.current_state.level,
                scope='all',
                )
        self.parent._internal.log_internal("Synchronized all handler levels")

    def set_level(self, logger_name: str, level: logLevels = 'INFO') -> None:
        """Set the effective level for a specific named logger"""
        self.parent.state_manager.global_logger_manager.set_named_logger_level(logger_name, level)
        self.parent._internal.log_internal(f"Set logger '{logger_name}' level to {level}")

    def silence(self, target: Union[str, List[str]]) -> None:
        """Silence specific loggers or all others"""
        if target == 'all':
            self.parent.state_manager.global_logger_manager.silence_other_loggers(exclude_logger='WrenchCL')
            self.parent._internal.log_internal("Silenced all other loggers")
        elif isinstance(target, str):
            self.parent.state_manager.global_logger_manager.silence_logger(target)
            self.parent._internal.log_internal(f"Silenced logger: {target}")
        elif isinstance(target, list):
            for logger_name in target:
                self.parent.state_manager.global_logger_manager.silence_logger(logger_name)
            self.parent._internal.log_internal(f"Silenced loggers: {', '.join(target)}")
        else:
            raise ValueError("target must be 'all', a string, or a list of strings")

    @property
    def active(self) -> List[str]:
        """List of active logger names in the logging system"""
        if not self.parent.state_manager.global_stream_configured:
            return ['WrenchCL']
        else:
            return self.parent.state_manager.global_logger_manager.get_active_loggers()

    @property
    def info(self) -> dict:
        """Dictionary of attached handlers and their configurations"""
        return self.parent.state_manager.handler_manager.get_handler_info()

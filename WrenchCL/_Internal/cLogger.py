"""
cLogger - Main WrenchCL logger class
"""
#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import threading

from ..Decorators import SingletonClass
from .Logging.Api.base_logger import BaseLogger
from .Logging.Api.managed_loggers import ManagedLoggers
from .Logging.Api.stream_manager import StreamManager
from .Logging.DataClasses import logLevels
from .Logging.LoggerConfigState import LoggerStateManager


@SingletonClass
class cLogger(BaseLogger):
    """
    WrenchCL's structured, colorized logger with Datadog integration.
    
    Features:
    • Structured formatting with syntax highlighting
    • Multiple modes: terminal (colored), json (structured), compact (minimal)
    • Datadog APM correlation (trace_id, span_id)
    • Environment-aware configuration (AWS Lambda auto-detection)
    • Thread-safe operations
    • Smart exception suggestions
    """

    def __init__(self) -> None:
        super().__init__()
        self._lock = threading.RLock()

        # Core services - clean separation of concerns
        self.state_manager = LoggerStateManager()

        # Initialize component APIs
        self.managed = ManagedLoggers(self)
        self.streams = StreamManager(self)

        # Set up state manager
        self.state_manager.set_global_logger_manager(self._internal.log_internal)

        # Initialize
        self.state_manager.setup()
        self.reinitialize()

    @property
    def instance(self):
        """Underlying Python logging.Logger instance"""
        return self.state_manager.logging_instance

    @property
    def handlers(self):
        """List of handlers attached to the logger instance"""
        return self.state_manager.logging_instance.handlers

    def add_stream(self, stream=None, level: logLevels = None, formatter=None):
        """Add a stream handler for log output"""
        import logging
        return self.managed.add(
                handler_cls=logging.StreamHandler, stream=stream,
                level=level, formatter=formatter, owned=True
                )
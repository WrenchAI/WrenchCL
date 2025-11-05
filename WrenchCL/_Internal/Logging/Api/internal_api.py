"""
InternalAPI - Implementation details not exposed to users
"""
#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import logging

from ..DataClasses import LogLevel


class InternalAPI:
    """Implementation details not exposed to users"""

    def __init__(self, parent_logger):
        self.parent = parent_logger
        self._from_context = False

    def log_internal(self, *args) -> None:
        """Internal logging method for logger infrastructure messages"""
        if not self._from_context:
            self.parent._log("INTERNAL", args=args)

    def setup_ddtrace(self, trace_enabled: bool):
        """Set up ddtrace if requested"""
        if trace_enabled:
            try:
                import ddtrace
                ddtrace.patch(logging=True)
                self.log_internal("Datadog trace injection enabled")
                import os
                os.environ["DD_TRACE_ENABLED"] = "true"
            except ImportError:
                self.log_internal("Datadog trace injection disabled - missing ddtrace")

    def update_formatters(self, level: LogLevel, no_format: bool, no_color: bool) -> None:
        """Update formatters for the current log operation"""
        config = self.parent.state_manager.current_state
        env_metadata = self.parent.state_manager.get_env_metadata()

        for handler in self.parent.state_manager.logging_instance.handlers:
            if isinstance(handler, logging.NullHandler):
                continue

            # If user explicitly wants to keep their formatter, never touch it
            if getattr(handler, "_wrench_preserve_formatter", False):
                continue

            owned = bool(getattr(handler, "_wrench_owned", False))
            if not owned:
                # Non-owned: do not rewrite unless explicitly opted in
                if not getattr(handler, "_wrench_adopted", False):
                    continue

            # Build base formatter for current log context
            base_fmt = self.parent.state_manager.formatter_factory.create_formatter(
                    level=level,
                    config_state=config,
                    env_metadata=env_metadata,
                    global_stream_configured=self.parent.state_manager.global_stream_configured,
                    no_format=no_format,
                    no_color=no_color,
                    )

            # If the handler uses a file wrapper, preserve the wrapper

            from ..Formatters import FileLogFormatter
            if isinstance(handler.formatter, FileLogFormatter):
                handler.setFormatter(FileLogFormatter(base_fmt))
            else:
                handler.setFormatter(base_fmt)

            # Attach DD filter once
            if self.parent.state_manager.current_state.dd_trace_enabled:
                from ..DatadogTraceInjectionFilter import DatadogTraceInjectionFilter
                if not any(isinstance(f, DatadogTraceInjectionFilter) for f in handler.filters):
                    handler.addFilter(DatadogTraceInjectionFilter())

    def mini_state(self):
        """Log initial status information"""
        config = self.parent.state_manager.current_state
        if config.mode == 'json':
            self.log_internal({"Color": config.color_enabled, "Mode": config.mode.capitalize(), "Deployment": config.deployed})
        else:
            self.log_internal(f"Logger -> Color:{config.color_enabled} | Mode:{config.mode.capitalize()} | Deployment:{config.deployed}")

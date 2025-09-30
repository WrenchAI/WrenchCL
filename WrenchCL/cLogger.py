#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import logging
import sys
import threading
import warnings
from contextlib import contextmanager
from io import TextIOBase
from logging import Handler
from typing import Optional, Literal, Any, Union, Type, List

# Import existing modules (unchanged)
from .Decorators import SingletonClass
from ._Internal.Logging.DataClasses import LogLevel, LogOptions, logLevels
from ._Internal.Logging.LoggerConfigState import LoggerStateManager
from ._Internal.Logging.logging_utils import get_depth


@SingletonClass
class cLogger:
    """
    WrenchCL's structured, colorized logger with Datadog integration.

    Features:
    • Structured formatting with syntax highlighting
    • Multiple modes: terminal (colored), json (structured), compact (minimal)
    • Datadog APM correlation (trace_id, span_id)
    • Environment-aware configuration (AWS Lambda auto-detection)
    • Thread-safe operations
    • Smart exception suggestions

    Usage:
        from WrenchCL.Tools import logger

        logger.info("Application started")
        logger.error("Something failed", exc_info=True)
        logger.configure(mode="json", trace_enabled=True)
    """

    def __init__(self) -> None:
        self.__lock = threading.RLock()
        # Core services - clean separation of concerns
        self.state_manager = LoggerStateManager()
        self.state_manager.set_global_logger_manager(self._internal_log)

        # Context Tracker
        self.__from_context = False

        # Initialize
        self.state_manager.setup()
        self.reinitialize()

        self.__mini_state()

    # ---------------- Public Configuration API ----------------

    def configure(
            self,
            mode: Optional[Literal['terminal', 'json', 'compact']] = None,
            level: Optional[logLevels] = None,
            color_enabled: Optional[bool] = None,
            highlight_syntax: Optional[bool] = None,
            verbose: Optional[bool] = None,
            trace_enabled: Optional[bool] = None,
            deployment_mode: Optional[bool] = None,
            suppress_autoconfig: bool = True
            ) -> None:
        """
        Configure logger behavior and settings.

        :param mode: Output format - 'terminal', 'json', or 'compact'
        :param level: Logging level - 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
        :param color_enabled: Enable/disable colored output
        :param highlight_syntax: Enable/disable syntax highlighting
        :param verbose: Enable verbose mode
        :param trace_enabled: Enable Datadog trace injection (requires ddtrace)
        :param deployment_mode: Enable deployment configuration
        :param suppress_autoconfig: Prevent automatic configuration when mode changes
        """
        self._internal_log("Configuring logger...")
        # Handle ddtrace setup if needed
        if trace_enabled is not None:
            self._setup_ddtrace(trace_enabled)

        # Delegate to config manager
        self.state_manager.handler_manager.flush_all_handlers()
        new_config = self.state_manager.configure(
                mode=mode,
                level=level,
                color_enabled=color_enabled,
                highlight_syntax=highlight_syntax,
                verbose=verbose,
                trace_enabled=trace_enabled,
                deployment_mode=deployment_mode,
                suppress_autoconfig=suppress_autoconfig
                )

        self.level = new_config.level

        # Check for trace/mode mismatch
        if not new_config.should_enable_dd_trace_logging and new_config.dd_trace_enabled:
            self._internal_log("Trace injection requested, but trace_id/span_id only appear in JSON mode.")

        self.__mini_state()

    def reinitialize(self, verbose=False):
        """
        Reload environment configuration and update logger settings.

        :param verbose: Log detailed configuration state after reinitialization
        """
        self.state_manager.reinitialize()
        if verbose:
            import json
            self._internal_log(json.dumps(self.state, indent=2, default=lambda x: str(x), ensure_ascii=False))

    def setLevel(self, level: logLevels) -> None:
        """
        Set the logging level.

        :param level: Logging level - 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
        """
        level = LogLevel(level)
        self.state_manager.configure(level=level)

    def initiate_new_run(self):
        """Generate and assign a new run ID for process tracking."""
        with self.__lock:
            self.state_manager.set_new_run_id()

    # ---------------- Core Logging Methods ----------------
    def info(
            self,
            *args: Any,
            header: Optional[str] = None,
            log_opts: Optional[Union[LogOptions, dict]] = None,
            ) -> None:
        """
        Log an INFO-level message.

        :param args: Messages to log (joined with line breaks if multiple)
        :param header: Optional styled header text
        :param log_opts: Logging options (no_format, no_color, stack_info)
        """
        opts = LogOptions(log_opts)
        self.__log(level="INFO", args=args, no_format=opts.no_format,
                   no_color=opts.no_color, stack_info=opts.stack_info, header=header)

    def debug(
            self,
            *args: Any,
            log_opts: Optional[Union[LogOptions, dict]] = None,
            ) -> None:
        """
        Log a DEBUG-level message.

        :param args: Messages to log (joined with line breaks if multiple)
        :param log_opts: Logging options (no_format, no_color, stack_info)
        """
        opts = LogOptions(log_opts)
        self.__log(level="DEBUG", args=args, no_format=opts.no_format,
                   no_color=opts.no_color, stack_info=opts.stack_info)

    def warning(
            self,
            *args: Any,
            header: Optional[str] = None,
            log_opts: Optional[Union[LogOptions, dict]] = None,
            **kwargs,
            ) -> None:
        """
        Log a WARNING-level message.

        :param args: Messages to log (joined with line breaks if multiple)
        :param header: Optional styled header text
        :param log_opts: Logging options (no_format, no_color, stack_info)
        """
        opts = LogOptions(log_opts)
        if isinstance(kwargs.get('exc_info', ''), (Exception, BaseException)):
            args = args + (kwargs.get('exc_info'),)
        self.__log(level="WARNING", args=args, no_format=opts.no_format,
                   no_color=opts.no_color, stack_info=opts.stack_info, header=header)

    def error(
            self,
            *args: Any,
            header: Optional[str] = None,
            log_opts: Optional[Union[LogOptions, dict]] = None,
            **kwargs: Any
            ) -> None:
        """
        Log an ERROR-level message.

        :param args: Messages to log (joined with line breaks if multiple)
        :param header: Optional styled header text
        :param log_opts: Logging options (no_format, no_color, stack_info)
        :param kwargs: Legacy support for exc_info parameter
        """
        if log_opts is None:
            log_opts = LogOptions()
        elif isinstance(log_opts, dict):
            log_opts = LogOptions(**log_opts)
        if isinstance(kwargs.get('exc_info', ''), (Exception, BaseException)):
            args = args + (kwargs.get('exc_info'),)
        self.__log(level="ERROR", args=args, no_format=log_opts.no_format,
                   no_color=log_opts.no_color, stack_info=log_opts.stack_info, header=header)

    def critical(
            self,
            *args: Any,
            header: Optional[str] = None,
            log_opts: Optional[Union[LogOptions, dict]] = None,
            **kwargs: Any
            ) -> None:
        """
        Log a CRITICAL-level message.

        :param args: Messages to log (joined with line breaks if multiple)
        :param header: Optional styled header text
        :param log_opts: Logging options (no_format, no_color, stack_info)
        :param kwargs: Legacy support for exc_info parameter
        """
        if log_opts is None:
            log_opts = LogOptions()
        elif isinstance(log_opts, dict):
            log_opts = LogOptions(**log_opts)
        if isinstance(kwargs.get('exc_info', ''), (Exception, BaseException)):
            args = args + (kwargs.get('exc_info'),)
        self.__log(level="CRITICAL", args=args, no_format=log_opts.no_format,
                   no_color=log_opts.no_color, stack_info=log_opts.stack_info, header=header)

    def exception(
            self,
            *args: Any,
            header: Optional[str] = None,
            log_opts: Optional[Union[LogOptions, dict]] = None,
            **kwargs
            ) -> None:
        """
        Log an ERROR-level message with exception context.

        :param args: Messages to log (joined with line breaks if multiple)
        :param header: Optional styled header text
        :param log_opts: Logging options (no_format, no_color, stack_info)
        :param kwargs: Legacy support for exc_info parameter
        """
        opts = LogOptions(log_opts)
        if isinstance(kwargs.get('exc_info', ''), (Exception, BaseException)):
            args = args + (kwargs.get('exc_info'),)
        self.__log(level="ERROR", args=args, no_format=opts.no_format,
                   no_color=opts.no_color, stack_info=opts.stack_info, header=header)

    # Aliases
    success = info

    def _internal_log(self, *args) -> None:
        """Internal logging method for logger infrastructure messages."""
        if not self.__from_context:
            self.__log("INTERNAL", args=args)

    # ---------------- Additional Logging Features ----------------

    def start_time(self) -> None:
        """Start timing for performance measurement."""
        self.state_manager.start_timer()

    def reset_time(self) -> None:
        """Reset the performance timer."""
        self.state_manager.reset_timer()

    def log_time(self, message="Elapsed time", reset: bool = False) -> None:
        """
        Log elapsed time since timer was started.

        :param message: Custom message to include with elapsed time
        :param reset: Reset timer after logging
        """
        elapsed = self.state_manager.get_elapsed_time()
        if elapsed:
            self.info(f"{message}: {elapsed:.2f}s")
        else:
            self._internal_log(f"Timer never started, skipping...")
        if reset:
            self.reset_time()

    # noinspection PyInconsistentReturns
    def header(self, text: str, size: int = None, compact=False, return_repr=False, level: logLevels = 'HEADER') -> Optional[str]:
        """
        Create and log a formatted header.

        :param text: Header text
        :param size: Header size (affects formatting)
        :param compact: Use compact header style
        :param return_repr: Return formatted string instead of logging
        :param level: Color level for header styling
        :return: Formatted header string if return_repr=True, otherwise None
        """
        config = self.state_manager.current_state
        compact = compact or config.is_compact_header_mode

        result = self.state_manager.message_processor.create_header(
                text, level=level, size=size, compact=compact
                )

        if not return_repr:
            self.__log(level, args=(result,), no_format=True, no_color=True)
        else:
            return result

    def __pretty_log(self, obj: Any, compact: bool = False, **kwargs) -> None:
        """
        Log objects in a visually formatted manner.

        :param obj: Object to log
        :param compact: Use compact formatting for arrays/dicts
        :param kwargs: Additional formatting options (indent, cwidth)
        """
        from ._Internal.Logging.logging_utils import ensure_str
        from ._Internal import pd
        import json
        from pprint import pformat

        obj = ensure_str(obj)
        output = obj
        config = self.state_manager.current_state
        cwidth = kwargs.get('cwidth', 240)
        indent = kwargs.get('indent', 2)
        try:
            if isinstance(obj, pd.DataFrame):
                prefix_str = f"DataType: {type(obj).__name__} | Shape: {obj.shape[0]} rows | {obj.shape[1]} columns"
                pd.set_option('display.max_rows', 500, 'display.max_columns', None,
                              'display.width', None, 'display.max_colwidth', 50,
                              'display.colheader_justify', 'center')
                if config.mode != 'json':
                    output = f"{prefix_str}\n{obj}"
                else:
                    output = obj.to_json(orient='records', indent=indent, **kwargs)
            elif isinstance(obj, dict):
                output = json.dumps(obj, indent=indent, ensure_ascii=False, **kwargs) if not compact else pformat(obj, compact=True, width=cwidth)
            elif hasattr(obj, 'model_dump_json'):
                output = obj.model_dump_json(indent=indent, **kwargs)
            elif hasattr(obj, 'dump_json_schema'):
                output = obj.dump_json_schema(indent=indent, **kwargs)
            elif hasattr(obj, 'pretty_repr'):
                output = obj.pretty_repr(**kwargs)
            elif hasattr(obj, 'json'):
                raw = obj.json()
                output = json.dumps(raw, indent=indent, ensure_ascii=False, **kwargs) if not compact else pformat(raw, compact=compact, width=cwidth)
            elif isinstance(obj, str) or hasattr(obj, '__repr__') or hasattr(obj, '__str__'):
                try:
                    parsed = json.loads(obj)
                    output = json.dumps(parsed, indent=indent, ensure_ascii=False, default=str, **kwargs) if not compact else pformat(parsed, compact=True, width=cwidth)
                except Exception:
                    output = obj
            elif hasattr(obj, '__dict__'):
                raw = str(obj.__dict__)
                output = json.dumps(raw, indent=indent, ensure_ascii=False, **kwargs) if not compact else pformat(raw, compact=compact, width=cwidth)
            else:
                output = pformat(obj, compact=compact, width=cwidth)
        except Exception:
            output = obj
        finally:
            if isinstance(output, str):
                output = output.strip()
        self.__log("DATA", args=(output,))

    # ---------------- Resource Management ----------------

    def flush_handlers(self):
        """Flush all logger handlers to ensure pending records are written."""
        self.state_manager.handler_manager.flush_all_handlers()

    def close(self):
        """Close all handlers and clean up resources."""
        self.state_manager.handler_manager.close_all_handlers()
        self.state_manager.global_logger_manager.cleanup_global_handlers()

    # ---------------- Handler Management ----------------

    def add_new_handler(
            self,
            handler_cls: Type[logging.Handler] = logging.StreamHandler,
            stream: Optional[TextIOBase] = None,
            level: logLevels = None,
            formatter: Optional[logging.Formatter] = None,
            force_replace: bool = False,
            ) -> logging.Handler:
        """
        Add a new logging handler to the logger instance.

        :param handler_cls: Handler class to instantiate
        :param stream: Stream for StreamHandler (required if using StreamHandler)
        :param level: Logging level for the handler
        :param formatter: Custom formatter (uses default if None)
        :param force_replace: Replace all existing handlers before adding new one
        :return: Created and configured handler instance
        """
        return self.state_manager.handler_manager.add_handler(handler_cls=handler_cls,
                                                              config_state=self.state_manager.current_state,
                                                              stream=stream,
                                                              level=level,
                                                              force_replace=force_replace,
                                                              base_level=self.state_manager.base_level,
                                                              formatter=formatter)

    def enable_file_logging(
            self,
            filename: str,
            max_bytes: int = 10485760,  # 10MB default
            backup_count: int = 5,
            level: logLevels = None,
            formatter: Optional[logging.Formatter] = None,
            ) -> Optional[logging.Handler]:
        """
        Add a rotating file handler for log output.

        :param filename: Log file name
        :param max_bytes: Maximum file size before rotation (default 10MB)
        :param backup_count: Number of backup files to keep (default 5)
        :param level: Logging level for file handler
        :param formatter: Custom formatter (uses default if None)
        :return: Created rotating file handler
        """
        handler = self.state_manager.handler_manager.add_file_handler(
                filename=filename, config=self.state_manager.current_state, max_bytes=max_bytes, backup_count=backup_count,
                level=level, formatter=formatter, base_level=self.state_manager.base_level
                )
        self._internal_log(f"File handler added to logger instance: {filename}")
        return handler

    # ---------------- Global Configuration ----------------

    def attach_global_stream(self, level: logLevels, silence_others: bool = False, stream=sys.stdout) -> None:
        """
        Attach a global stream handler to the root logger.

        :param level: Logging level for the global stream
        :param silence_others: Silence other loggers
        :param stream: Output stream (default sys.stdout)
        """
        config = self.state_manager.current_state
        env_metadata = self.state_manager.get_env_metadata()

        self.state_manager.global_logger_manager.attach_global_stream(
                level=level,
                silence_others=silence_others,
                stream=stream,
                config_state=config,
                env_metadata=env_metadata
                )

    def set_named_logger_level(self, logger_name: str, level: logLevels = 'INFO') -> None:
        """
        Set the logging level for a specific named logger.

        :param logger_name: Name of the logger to configure
        :param level: Logging level to set
        """
        self.state_manager.global_logger_manager.set_named_logger_level(logger_name, level)

    def set_attached_handler_level(self, handler_name: str, level: Optional[logLevels] = None) -> None:
        """
        Set the logging level for a specific handler by name.

        :param handler_name: Name of the handler to modify
        :param level: Logging level to set (uses logger level if None)
        """
        config = self.state_manager.current_state
        env_metadata = self.state_manager.get_env_metadata()

        self.state_manager.global_logger_manager.set_handler_level_by_name(
                handler_name=handler_name,
                level=level,
                logger_instance=self.state_manager.logging_instance,
                config_state=config,
                env_metadata=env_metadata,
                global_stream_configured=self.state_manager.global_stream_configured
                )

    def silence_logger(self, logger_name: str) -> None:
        """
        Silence a logger by setting its level above CRITICAL.

        :param logger_name: Name of the logger to silence
        """
        self.state_manager.global_logger_manager.silence_logger(logger_name)

    def silence_other_loggers(self) -> None:
        """Silence all loggers except WrenchCL."""
        self.state_manager.global_logger_manager.silence_other_loggers(exclude_logger='WrenchCL')

    def force_markup(self) -> None:
        """
        Force enable colorful console output with ANSI escape codes.

        Enables color-coded output even in environments that normally disable it.
        Warning: Not recommended in deployment mode as it may interfere with log parsers.
        """
        try:
            import colorama

            # Configure colorama
            colorama.deinit()
            colorama.init(strip=False, convert=False)
            sys.stdout = colorama.AnsiToWin32(sys.stdout).stream
            sys.stderr = colorama.AnsiToWin32(sys.stderr).stream

            # Update config and color service
            self.state_manager.configure(force_markup=True, color_enabled=True)

            # Warning for deployment mode
            config = self.state_manager.current_state
            if config.force_markup and config.deployed:
                warnings.warn("Forcing Markup in deployment mode is not recommended...",
                              category=RuntimeWarning, stacklevel=5)

            self._internal_log("Forced color output enabled.")
        except ImportError:
            self._internal_log("Colorama not installed. Forcing markup is not possible.")

    # ---------------- Context Manager ----------------

    @contextmanager
    def temporary(
            self,
            level: Optional[logLevels] = None,
            mode: Optional[Literal['terminal', 'json', 'compact']] = None,
            color_enabled: Optional[bool] = None,
            verbose: Optional[bool] = None,
            trace_enabled: Optional[bool] = None,
            highlight_syntax: Optional[bool] = None,
            deployed: Optional[bool] = None,
            ):
        """
        Temporarily override logger configuration within a context.

        :param level: Temporary logging level
        :param mode: Temporary output mode
        :param color_enabled: Temporary color setting
        :param verbose: Temporary verbose setting
        :param trace_enabled: Temporary trace setting
        :param highlight_syntax: Temporary syntax highlighting setting
        :param deployed: Temporary deployment mode setting
        """
        self.__from_context = True

        # Create temporary config state
        overrides = {}
        if level is not None:
            overrides['level'] = LogLevel(level)
        if mode is not None:
            overrides['mode'] = mode
            if mode == 'json' and deployed is None:
                overrides['deployed'] = True
        if color_enabled is not None:
            overrides['color_enabled'] = color_enabled
        if verbose is not None:
            overrides['verbose'] = verbose
        if trace_enabled is not None:
            overrides['dd_trace_enabled'] = trace_enabled
        if highlight_syntax is not None:
            overrides['highlight_syntax'] = highlight_syntax
        if deployed is not None:
            overrides['deployed'] = deployed

        # Apply temporary state
        temp_state = self.state_manager.create_temporary_state(**overrides)
        old_state = self.state_manager.apply_temporary_state(temp_state)

        # Handle level changes
        if level is not None:
            with self.__lock:
                self.state_manager.handler_manager.flush_all_handlers()
                self.state_manager.logging_instance.setLevel(int(LogLevel(level)))

        try:
            yield
        finally:
            # Restore original state
            self.state_manager.restore_state(old_state)
            self.__from_context = False

    # ---------------- Properties ----------------

    @property
    def active_loggers(self) -> List[str]:
        """List of active logger names in the logging system."""
        if not self.state_manager.global_stream_configured:
            return ['WrenchCL']
        else:
            return self.state_manager.global_logger_manager.get_active_loggers()

    @property
    def mode(self) -> str:
        """Current logging mode (terminal, json, or compact)."""
        return self.state_manager.current_state.mode

    @property
    def loggers(self):
        """Dictionary of attached handlers and their configurations."""
        return self.state_manager.handler_manager.get_handler_info()

    @property
    def level(self) -> LogLevel:
        """Current logging level."""
        return LogLevel(logging.getLevelName(self.state_manager.logging_instance.level))

    @level.setter
    def level(self, level: LogLevel):
        try:
            self.setLevel(level)
        except Exception as e:
            self._internal_log(f"Failed to set logger level: {e}")

    @property
    def instance(self) -> logging.Logger:
        """Underlying Python logging.Logger instance."""
        return self.state_manager.logging_instance

    @property
    def handlers(self) -> list[Handler]:
        """List of handlers attached to the logger instance."""
        return self.state_manager.logging_instance.handlers

    @property
    def run_id(self) -> str:
        """Current run ID."""
        return self.state_manager.run_id

    @property
    def state(self) -> dict:
        """Complete logger state information including configuration and metadata."""
        config = self.state_manager.current_state
        env_metadata = self.state_manager.get_env_metadata()

        return {
                "Logging Level": self.level.value,
                "Run Id": self.state_manager.run_id,
                "Mode": config.mode,
                "Environment Metadata": env_metadata,
                "Configuration": {
                        "Color Enabled": config.color_enabled,
                        "Highlight Syntax": config.highlight_syntax,
                        "Verbose": config.verbose,
                        "Deployment Mode": config.deployed,
                        "DD Trace Enabled": config.dd_trace_enabled,
                        "Global Stream Configured": self.state_manager.global_stream_configured
                        },
                "Handlers": [type(h).__name__ for h in self.state_manager.logging_instance.handlers],
                }

    @property
    def highlight_syntax(self) -> bool:
        """Whether syntax highlighting is currently enabled."""
        return self.state_manager.current_state.highlight_syntax

    # ---------------- Internals ----------------

    def __mini_state(self):
        # Initial status log
        config = self.state_manager.current_state
        if config.mode == 'json':
            self._internal_log({"Color": config.color_enabled, "Mode": config.mode.capitalize(), "Deployment": config.deployed})
        else:
            self._internal_log(f"Logger -> Color:{config.color_enabled} | Mode:{config.mode.capitalize()} | Deployment:{config.deployed}")

    def __log(
            self, level: Union[LogLevel, logLevels], args,
            no_format: bool = False, no_color: bool = False,
            stack_info: bool = False, header: Optional[str] = None
            ) -> None:
        """Core logging method - now much cleaner thanks to services."""

        if not isinstance(level, LogLevel):
            level = LogLevel(level)

        config = self.state_manager.current_state

        # Process message using MessageProcessor
        msg, exc_info = self.state_manager.message_processor.process_log_message(
                level, args, config, header, no_color
                )

        # Handle exception info
        if level not in ['ERROR', 'CRITICAL'] and not stack_info:
            exc_info = None

        # Update formatters and log
        with self.__lock:
            self.state_manager.handler_manager.flush_all_handlers()
            self._update_handler_formatters(level, no_format, no_color)

        # Format final message
        if config.should_format_message(no_format):
            if len(msg.strip().splitlines()) > 1 and not msg.startswith('\n'):
                msg = '\n' + msg

        self.state_manager.logging_instance.log(
                int(level), msg, exc_info=exc_info, stack_info=stack_info,
                stacklevel=get_depth(internal=level == 'INTERNAL')
                )

    def _update_handler_formatters(self, level: LogLevel, no_format: bool, no_color: bool):
        """Update formatters for the current log operation."""
        config = self.state_manager.current_state
        env_metadata = self.state_manager.get_env_metadata()

        for handler in self.state_manager.logging_instance.handlers:
            if not isinstance(handler, logging.NullHandler):
                formatter = self.state_manager.formatter_factory.create_formatter(
                        level=level, config_state=config, env_metadata=env_metadata,
                        global_stream_configured=self.state_manager.global_stream_configured,
                        no_format=no_format, no_color=no_color
                        )
                handler.setFormatter(formatter)

    def _setup_ddtrace(self, trace_enabled: bool):
        """Set up ddtrace if requested."""
        if trace_enabled:
            try:
                import ddtrace
                ddtrace.patch(logging=True)
                self._internal_log("Datadog trace injection enabled")
                import os
                os.environ["DD_TRACE_ENABLED"] = "true"
            except ImportError:
                self._internal_log("Datadog trace injection disabled - missing ddtrace")

    # ---------------- Aliases/Shortcuts ----------------

    data = __pretty_log

    def cdata(self, data: Any, **kwargs) -> None:
        """
        Log data in compact format.

        :param data: Data to log
        :param kwargs: Additional formatting options
        """
        return self.__pretty_log(data, compact=True, **kwargs)

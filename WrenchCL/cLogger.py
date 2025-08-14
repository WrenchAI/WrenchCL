#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import logging
import sys
import threading
import time
import warnings
from contextlib import contextmanager
from io import TextIOBase
from logging import Handler
from typing import Optional, Literal, Any, Union, Type, List

# Import existing modules (unchanged)
from .Decorators import SingletonClass
from ._Internal.Logging.DataClasses import LogLevel, LogOptions, logLevels
from ._Internal.Logging.ColorService import ColorService
from ._Internal.Logging.Formatters import FormatterFactory
from ._Internal.Logging.LogManagers import GlobalLoggerManager, HandlerManager
from ._Internal.Logging.LoggerConfigState import ConfigManager
from ._Internal.Logging.MessageProcessors import MarkupProcessor, MessageProcessor
from ._Internal.Logging.logging_utils import get_depth, generate_run_id


@SingletonClass
class cLogger:
    """
    WrenchCL's structured, colorized, and extensible logger.

    Features:
    ---------
    • Structured formatting with optional syntax highlighting for Python/JSON-style literals.
    • Multiple output modes: 'terminal' (colored), 'json' (infra-readable), 'compact' (minimal).
    • Datadog APM correlation (trace_id, span_id) via ddtrace integration.
    • Colorized output with environment-aware fallback (e.g., AWS Lambda disables color).
    • Smart exception suggestion engine for attribute errors.
    • Thread-safe across logging, handler updates, and reconfiguration.
    • Singleton-safe with `logger()` for consistent usage across modules.

    Initialization:
    ---------------
    - On instantiation, the logger performs:
        1. Stream handler setup (`__setup`)
        2. Environment-aware configuration refresh (`reinitialize`)
    - All runtime changes to env vars (COLOR_MODE, LOG_DD_TRACE, etc.) should be followed by `reinitialize()`.

    Environment Variables:
    ----------------------
    - COLOR_MODE: "true" or "false" (defaults to true unless on Lambda)
    - LOG_DD_TRACE: "true" or "false" to enable Datadog trace injection
    - ENV, PROJECT_NAME, PROJECT_VERSION: Used in prefix metadata (optional)

    Usage Example:
    --------------
    ```python
    from WrenchCL.Tools import logger

    logger._internal_log("Starting job...")
    logger.error("Something failed", exc_info=True)

    # Runtime config switch
    logger.configure(mode="json", trace_enabled=True)
    ```

    To force colors and JSON highlighting in CI:
    ```python
    logger.force_markup()
    ```
    """
    def __init__(self) -> None:
        # Core services - clean separation of concerns
        self.config_manager = ConfigManager()
        self.color_service = ColorService()
        self.markup_processor = MarkupProcessor(self.color_service)
        self.message_processor = MessageProcessor(self.color_service, self.markup_processor)
        self.formatter_factory = FormatterFactory(self.color_service)

        # Logger setup
        self.__lock = threading.RLock()
        self.__logger_instance = logging.getLogger('WrenchCL')
        self.handler_manager = HandlerManager(self.__logger_instance, self.formatter_factory)
        self.global_logger_manager = GlobalLoggerManager(
            formatter_factory=self.formatter_factory,
            handler_manager=self.handler_manager,
            internal_logger=self._internal_log  # Pass our internal logging method
        )
        # State
        self.__global_stream_configured = False
        self.__initialized = False
        self.run_id = generate_run_id()
        self.__base_level = 'INFO'
        self.__start_time = None
        self.__from_context = False

        # Listen for config changes
        self.config_manager.add_change_listener(self._on_config_changed)

        # Initialize
        self.__setup()
        self.reinitialize()

        # Initial status log
        config = self.config_manager.current_state
        self._internal_log(f"Logger -> Color:{config.color_enabled} | Mode:{config.mode.capitalize()} | Deployment:{config.deployed}")
    # ---------------- Public Configuration API ----------------

    def configure(self,
                  mode: Optional[Literal['terminal', 'json', 'compact']] = None,
                  level: Optional[logLevels] = None,
                  color_enabled: Optional[bool] = None,
                  highlight_syntax: Optional[bool] = None,
                  verbose: Optional[bool] = None,
                  trace_enabled: Optional[bool] = None,
                  deployment_mode: Optional[bool] = None,
                  suppress_autoconfig: bool = True) -> None:
        """
        Configures the logger's behavior and settings based on the provided parameters.

        This method allows customizing various aspects of the logger's operation, such as
        output format (e.g., terminal, JSON, compact), log level, colorization, syntax
        highlighting, verbosity, trace injection, and deployment behavior. It also enables
        interaction with Datadog tracing if applicable.

        All configuration updates made by this method are thread-safe due to the use of
        internal synchronization.

        :param mode: Specifies the logging mode. Expected values are 'terminal', 'json',
                     or 'compact'. If None, the current mode is retained.
        :param level: Defines the logging verbosity level, aligning with standard
                      Python logging levels such as 'INFO', 'DEBUG', or 'ERROR'.
        :param color_enabled: Indicates whether colorization is turned on in logging
                              output. Set to True for enabling colorized logs, False
                              for plain output.
        :param highlight_syntax: Controls whether syntax highlighting is applied to
                                 the logs. True to enable syntax highlights; False
                                 to disable.
        :param verbose: Activates verbose mode for logging output when set to True.
                        Defaults to None, which retains the current verbosity setting.
        :param trace_enabled: Enables or disables Datadog trace injection. If True,
                              Datadog tracing features are activated. If False,
                              tracing is forcibly disabled.
        :param deployment_mode: Determines if the logger operates in a deployment
                                context. If True, the logger reflects a production-ready
                                configuration.
        :param suppress_autoconfig: Avoids triggering the automatic configuration
                                    of deployment metadata if set to True. Defaults
                                    to True for suppressing autoconfig behavior.
        :return: None
        """

        # Handle ddtrace setup if needed
        if trace_enabled is not None:
            self._setup_ddtrace(trace_enabled)

        # Delegate to config manager
        new_config = self.config_manager.configure(
            mode=mode,
            level=level,
            color_enabled=color_enabled,
            highlight_syntax=highlight_syntax,
            verbose=verbose,
            trace_enabled=trace_enabled,
            deployment_mode=deployment_mode
        )

        # Check for trace/mode mismatch
        if not new_config.should_enable_dd_trace_logging and new_config.dd_trace_enabled:
            self._internal_log("Trace injection requested, but trace_id/span_id only appear in JSON mode.")



    def reinitialize(self, verbose = False):
        """
        Reinitialized the current environment state by rechecking deployment
        configuration, color scheme, and fetching updated metadata for the
        environment. Optionally logs the internal state if verbose is enabled.

        :param verbose: A boolean indicating whether detailed internal logging
                        should be enabled during reinitialization.
        :type verbose: bool

        :return: None
        """
        self.config_manager.reinitialize()
        if verbose:
            import json
            self._internal_log(json.dumps(self.logger_state, indent=2, default=lambda x: str(x), ensure_ascii=False))

    def setLevel(self, level: logLevels) -> None:
        """
        Sets the logging level for the application, determining the severity of messages
        that should be handled. This method updates the logging configuration by flushing
        handlers and applying the new level to the logger instance.

        :param level: The desired logging level. Can either be an integer or one of the
            predefined logging level literals - "DEBUG", "INFO", "WARNING", "ERROR",
            or "CRITICAL". These levels regulate which log messages are processed.
        :return: None
        """
        level = LogLevel(level)
        with self.__lock:
            self.handler_manager.flush_all_handlers()
            self.__logger_instance.setLevel(int(level))
        self.config_manager.configure(level=level)

    def initiate_new_run(self):
        """
        Initializes and assigns a new run ID for the current process.

        This method generates a new run ID using the internal mechanism
        and assigns it to the `run_id` attribute under the protection of a
        thread lock to ensure thread safety. The method is useful for
        distinguishing and managing separate execution runs in a controlled
        environment.

        :return: None
        """
        with self.__lock:
            self.run_id = generate_run_id()

    # ---------------- Core Logging Methods ----------------
    def info(
        self,
        *args: Any,
        header: Optional[str] = None,
        log_opts: Optional[Union[LogOptions, dict]] = None,
    ) -> None:
        """
        Logs an INFO-level message.

        :param args: Strings or objects to log. Multiple values are joined with line breaks.
        :param header: Optional text to prepend as a stylized header.
        :param log_opts: Logging options (no_format, no_color, stack_info). Can be LogOptions instance or dict.
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
        Logs a DEBUG-level message.

        :param args: Strings or objects to log. Multiple values are joined with line breaks.
        :param log_opts: Logging options (no_format, no_color, stack_info). Can be LogOptions instance or dict.
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
        Logs a WARNING-level message.

        :param args: Strings or objects to log. Multiple values are joined with line breaks.
        :param header: Optional text to prepend as a stylized header.
        :param log_opts: Logging options (no_format, no_color, stack_info). Can be LogOptions instance or dict.
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
        Logs an ERROR-level message.

        :param args: Strings or objects to log. Multiple values are joined with line breaks.
        :param header: Optional text to prepend as a stylized header.
        :param log_opts: Logging options (no_format, no_color, stack_info). Can be LogOptions instance or dict.
        :param kwargs: [Legacy Support for depreciated exc_info] Additional keyword args passed to the underlying logger.
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
        Logs a CRITICAL-level message.

        :param args: Strings or objects to log. Multiple values are joined with line breaks.
        :param header: Optional text to prepend as a stylized header.
        :param log_opts: Logging options (no_format, no_color, stack_info). Can be LogOptions instance or dict.
        :param kwargs: [Legacy Support for depreciated exc_info] Additional keyword args passed to the underlying logger.
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
        Logs an ERROR-level message with optional exception context.

        :param args: Strings or objects to log. Multiple values are joined with line breaks.
        :param header: Optional text to prepend as a stylized header.
        :param log_opts: Logging options (no_format, no_color, stack_info). Can be LogOptions instance or dict.
        :param kwargs: [Legacy Support for depreciated exc_info] Additional keyword args passed to the underlying logger.
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
        """
        Records the current time as the start time.

        This method captures the current time using the `time.time()` function and
        stores it in the `__start_time` attribute. It is typically used to mark
        the beginning of a time-sensitive operation or process.

        :Attributes:
            __start_time (float): The recorded start time in seconds since
            the epoch, as provided by `time.time()`.

        :return: None
        """
        self.__start_time = time.time()

    def log_time(self, message="Elapsed time") -> None:
        """
        Logs the elapsed time since the timer was started.

        This method calculates the elapsed time by subtracting the start
        time from the current time and logs the elapsed duration along
        with the provided message. If the timer was not started, the method
        does nothing.

        :param message: Optional custom message to log along with the
            elapsed time. Defaults to "Elapsed time".
        :return: None
        """
        if self.__start_time:
            elapsed = time.time() - self.__start_time
            self.info(f"{message}: {elapsed:.2f}s")

    # noinspection PyInconsistentReturns
    def header(self, text: str, size:int = None, compact = False, return_repr = False, level: logLevels = 'HEADER') -> Optional[str]:
        """
        Formats and optionally logs or returns a header string based on the provided text
        and specified formatting options. The header can be adjusted for size, compactness,
        and can be returned as a string if needed.

        The text serves as the base for creating the header, and additional options allow
        for customization such as compact styling, size adjustment, or whether the method
        returns the formatted string or logs it.


        :param text: The text to format as a header.
        :type text: str
        :param size: Optional size for the formatted header. If not provided, defaults depend
            on the mode (compact or regular).
        :type size: int, optional
        :param compact: Determines whether the header should follow compact formatting. Defaults
            to False, or can be affected by the current configuration mode.
        :type compact: bool
        :param return_repr: If True, the method returns the formatted string instead of logging it.
        :type return_repr: bool
        :param level: Level to Color and return the Header as
        :type level: LogLevels
        :return: The formatted header string if `repr` is True, otherwise None.
        :rtype: Optional[str]
        """
        config = self.config_manager.current_state
        compact = compact or config.is_compact_header_mode

        result = self.message_processor.create_header(
            text, level=level, size=size, compact=compact
        )

        if not return_repr:
            self.__log(level, args=(result,), no_format=True, no_color=True)
        else:
            return result

    def __pretty_log(self, obj: Any, indent=2, compact: bool = False, **kwargs) -> None:
        """
        Logs a given object in a visually formatted manner.

        :param obj: Object to log.
        :param indent: Indentation for JSON formatting.
        :param compact: If True, uses pprint for more compact array formatting.
        :param kwargs: Passed to json.dumps or model_dump_json
        """
        from ._Internal.Logging.logging_utils import ensure_str
        from ._Internal import pd
        import json
        from pprint import pformat

        obj = ensure_str(obj)
        output = obj
        config = self.config_manager.current_state

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
                output = json.dumps(obj, indent=indent, ensure_ascii=False, **kwargs) if not compact else pformat(obj, compact=True)
            elif hasattr(obj, 'model_dump_json'):
                output = obj.model_dump_json(indent=indent, **kwargs)
            elif hasattr(obj, 'dump_json_schema'):
                output = obj.dump_json_schema(indent=indent, **kwargs)
            elif hasattr(obj, 'pretty_repr'):
                output = obj.pretty_repr(**kwargs)
            elif hasattr(obj, 'json'):
                raw = obj.json()
                output = json.dumps(raw, indent=indent, ensure_ascii=False, **kwargs) if not compact else pformat(raw, compact=compact)
            elif isinstance(obj, str) or hasattr(obj, '__repr__') or hasattr(obj, '__str__'):
                try:
                    parsed = json.loads(obj)
                    output = json.dumps(parsed, indent=indent, ensure_ascii=False, default=str, **kwargs) if not compact else pformat(parsed, compact=True)
                except Exception:
                    output = obj
            elif hasattr(obj, '__dict__'):
                raw = str(obj.__dict__)
                output = json.dumps(raw, indent=indent, ensure_ascii=False, **kwargs) if not compact else pformat(raw, compact=compact)
            else:
                output = pformat(obj, compact=compact)
        except Exception:
            output = obj
        finally:
            if config.mode == 'json' and isinstance(output, str):
                try:
                    output = json.loads(output)
                except Exception:
                    pass
        self.__log("DATA", args=(output,))

    # ---------------- Resource Management ----------------

    def flush_handlers(self):
        """
        Flushes all the handlers associated with the logger instance.

        This method iterates through all the handlers of the logger instance
        and attempts to flush each of them to ensure all pending log records
        are written out. If an exception occurs during the flush operation,
        it is caught and ignored.

        :raises Exception: Catches and ignores any exceptions raised during the
            flushing process for individual handlers.
        """
        self.handler_manager.flush_all_handlers()

    def close(self):
        """
        Closes all handlers associated with the logger instance, ensuring any buffered log
        entries are flushed before removing the handlers. It also manages the cleanup of
        global stream handlers if they were configured.

        This method ensures that all resources associated with logging handlers are properly
        released. If any errors occur while closing a handler, they are logged to standard
        error, but the process continues to ensure other handlers are also cleaned up.
        """
        self.handler_manager.close_all_handlers()
        self.global_logger_manager.cleanup_global_handlers()

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
        Adds a new logging handler to the logger instance. This function allows creating
        and configuring a logging handler dynamically with the specified attributes such
        as type of handler, associated stream, logging level, formatter, and whether to
        replace existing handlers.

        :param handler_cls: The logging handler class to instantiate. Should be a subclass
            of `logging.Handler`. Defaults to `logging.StreamHandler`.
        :param stream: The stream to be used by the handler, specifically required if
            `handler_cls` is `StreamHandler`. Accepts file-like objects or other valid
            streams. Defaults to None.
        :param level: The logging level for the handler. Can be specified as a string
            (e.g., `"INFO"`, `"DEBUG"`) or an integer corresponding to logging constants.
            Defaults to None, which uses the instance's base logging level.
        :param formatter: An instance of `logging.Formatter` to format log messages. If
            not provided, a default formatter is created based on the logging level.
            Defaults to None.
        :param force_replace: Whether to replace all existing handlers in the logger
            instance before adding the new handler. When set to True, any previously
            attached handlers will be removed. Defaults to False.

        :return: The instance of the created and configured logging handler attached to
            the logger instance.
        :rtype: logging.Handler
        """
        return self.handler_manager.add_handler(handler_cls=handler_cls,
                                                config_state=self.config_manager.current_state,
                                                stream=stream,
                                                level=level,
                                                force_replace=force_replace,
                                                base_level=self.__base_level,
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
        Adds a rotating file handler to the logger instance. This handler writes log
        messages to a file, creating new files when the current file reaches a
        specified maximum size. Old files are retained up to a set number of backups.

        :param filename: The name of the file to which log messages will be written.
        :param max_bytes: The maximum size, in bytes, that a log file can grow
            before it is rolled over. Default is 10MB.
        :param backup_count: The number of backup files to retain once the log file
            is rolled over. Default is 5.
        :param level: The logging level for the handler. If not provided, the logger's
            base level is used. Can be specified as a string or integer.
        :param formatter: A logging formatter instance to format the log messages.
            If not provided, the default formatter for the logger is used.
        :return: The newly created rotating file handler instance.
        """
        handler = self.handler_manager.add_file_handler(
            filename=filename, config=self.config_manager.current_state, max_bytes=max_bytes, backup_count=backup_count,
            level=level, formatter=formatter, base_level=self.__base_level
        )
        self._internal_log(f"File handler added to logger instance: {filename}")
        return handler

    # ---------------- Global Configuration ----------------

    def attach_global_stream(self, level: logLevels, silence_others: bool = False, stream = sys.stdout) -> None:
        """
        Attaches a global stream handler to the root logger, setting its level and
        silencing other loggers if specified. This method overwrites existing handlers
        on the root logger and configures one with the given stream and level.

        :param level: The logging level for the global stream, default is "INFO".
        :type level: str
        :param silence_others: Flag indicating whether to silence other loggers.
        :type silence_others: bool
        :param stream: The stream to which log messages will be written, default is sys.stdout.
        :type stream: `io.TextIOBase`
        """
        config = self.config_manager.current_state
        env_metadata = self.config_manager.get_env_metadata()

        self.global_logger_manager.attach_global_stream(
            level=level,
            silence_others=silence_others,
            stream=stream,
            config_state=config,
            env_metadata=env_metadata
        )

        self.__global_stream_configured = self.global_logger_manager.is_global_stream_configured

    def set_named_logger_level(self, logger_name: str, level: logLevels = 'INFO') -> None:
        """
        Sets the logging level for a named logger. If no logging level is provided, the
        level is set to a custom level above CRITICAL (CRITICAL + 1). This method ensures
        that the logger has its handlers properly flushed and replaced with a
        NullHandler when necessary. If the logging level exceeds CRITICAL + 1, the logger
        will not propagate messages to ancestor loggers.

        :param logger_name: The name of the logger to configure.
        :type logger_name: str
        :param level: The logging level to set for the specified logger. Defaults to None,
            which sets the level to CRITICAL + 1.
        :type level: Optional[logLevels]
        :return: None
        """
        self.global_logger_manager.set_named_logger_level(logger_name, level)

    def set_attached_handler_level(self, handler_name:str, level: Optional[logLevels] = None) -> None:
        """
        Sets the logging level and formatter of an attached handler identified
        by its name. If the level is not provided, the current logger level is used.

        :param handler_name: The name of the handler to modify.
        :type handler_name: str
        :param level: The logging level to set for the handler. If None, the
                      level of the logger is used.
        :type level: logLevels
        :return: None
        """
        config = self.config_manager.current_state
        env_metadata = self.config_manager.get_env_metadata()

        self.global_logger_manager.set_handler_level_by_name(
            handler_name=handler_name,
            level=level,
            logger_instance=self.__logger_instance,
            config_state=config,
            env_metadata=env_metadata,
            global_stream_configured=self.__global_stream_configured
        )
    def silence_logger(self, logger_name:str) -> None:
        """
        Sets the logging level to effectively silence the specified logger by assigning
        a level higher than CRITICAL.

        :param logger_name: The name of the logger to be silenced.
        :type logger_name: str
        :return: This method does not return anything.
        :rtype: None
        """
        self.global_logger_manager.silence_logger(logger_name)

    def silence_other_loggers(self) -> None:
        """
        Silences all loggers except for the logger named 'WrenchCL'.

        This function iterates through all loggers present in the logging manager's
        logger dictionary. For each logger found, it silences it by invoking the
        `silence_logger` method unless the logger's name is 'WrenchCL'.

        :return: None
        """
        self.global_logger_manager.silence_other_loggers(exclude_logger='WrenchCL')

    def enable_color(self):
        """
        Enables color support for terminal output. This method initializes the `colorama`
        library if available and updates the internal configuration to enable colorized
        output. It also initializes the presets for specific color and style usage.
        If `colorama` is not installed, the method disables color support.

        :raises ImportError: If the `colorama` module cannot be imported.
        """
        presets = self.color_service.enable_colors()
        self.config_manager.configure(color_enabled=True, highlight_syntax=True)
        return presets

    def disable_color(self):
        """
        Disables color output and syntax highlighting for the application.

        This method ensures that all color and styling configurations are reset
        to a mock implementation, effectively disabling any visual enhancements
        previously provided. It updates the internal configuration to mark color
        features as disabled and deinitializes the `colorama` module if present.

        :raises ImportError: If the `colorama` module is not installed when attempting
            to deinitialize it.

        """
        presets = self.color_service.disable_colors()
        self.config_manager.configure(color_enabled=False, highlight_syntax=False)
        return presets

    def force_markup(self) -> None:
        """
        Enables forced markup for colorful console output, updates logging
        formatting, and configures output streams for better compatibility with
        terminal emulators, particularly on Windows systems.

        This method forcibly enables color-coded output for logging by initializing
        Colorama to handle ANSI escape codes. It modifies standard output and error
        streams to ensure compatibility with Windows consoles. Additional checks
        are performed for deployment configurations and logging modes to ensure proper
        behavior in various environments.

        If Colorama is not installed, an appropriate warning will be logged,
        and colorized output cannot be forced.

        .. warning::

           Forcing markup in deployment mode is not recommended. It can cause
           issues in external parsers such as CloudWatch or Datadog. Use with caution
           in such scenarios.

        Raises:
            - A RuntimeWarning if markup is forced while deployed, signaling potential issues.

        Exceptions:
            - Logs a warning if the Colorama library is not installed.

        :raises RuntimeWarning: If markup is forced in deployment mode.
        """
        try:
            import colorama

            # Configure colorama
            colorama.deinit()
            colorama.init(strip=False, convert=False)
            sys.stdout = colorama.AnsiToWin32(sys.stdout).stream
            sys.stderr = colorama.AnsiToWin32(sys.stderr).stream

            # Update config and color service
            self.config_manager.configure(force_markup=True, color_enabled=True)
            self.color_service.enable_colors()

            # Warning for deployment mode
            config = self.config_manager.current_state
            if config.force_markup and config.deployed:
                warnings.warn("Forcing Markup in deployment mode is not recommended...",
                            category=RuntimeWarning, stacklevel=5)

            self._internal_log("Forced color output enabled.")
        except ImportError:
            self._internal_log("Colorama not installed. Forcing markup is not possible.")

    def display_logger_state(self) -> None:
        """
        Logs the current logger's configuration and settings.

        This method calls an internal function to output a summary
        of the logger's setup, including any relevant configurations or
        details about the logger state. It does not take any input
        parameters and does not return anything.

        :raises Exception: If an error occurs during the logging process

        :return: None
        """
        self.__log_setup_summary()

        # Optionally show global logger state too
        global_info = self.global_logger_manager.get_logger_info()
        if global_info:
            self._internal_log(f"📊 Global loggers managed: {len(global_info)}")

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
        Temporarily override logger configuration within a scoped context.

        :param level: logLevels.
        :param mode: Output mode ('terminal', 'json', 'compact').
        :param color_enabled: Enables or disables ANSI color output.
        :param verbose: Enables verbose logging.
        :param trace_enabled: Enables Datadog trace correlation.
        :param highlight_syntax: Enables literal highlighting.
        :param deployed: Toggles deployment mode behavior.
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
        temp_state = self.config_manager.create_temporary_state(**overrides)
        old_state = self.config_manager.apply_temporary_state(temp_state)

        # Handle level changes
        if level is not None:
            with self.__lock:
                self.handler_manager.flush_all_handlers()
                self.__logger_instance.setLevel(int(LogLevel(level)))

        try:
            yield
        finally:
            # Restore original state
            self.config_manager.restore_state(old_state)
            self.__from_context = False


    # ---------------- Properties (SIMPLIFIED) ----------------

    @property
    def active_loggers(self) -> List[str]:
        """
        Retrieves a list of active loggers from the logging system.

        This property gathers all the active logger names currently managed
        by the logging module. It filters logger names from the root logger's
        manager dictionary to include only valid instances of `logging.Logger`.

        :return: A list of active logger names.
        :rtype: List[str]
        """
        if not self.__global_stream_configured:
            return ['WrenchCL']
        else:
            return self.global_logger_manager.get_active_loggers()

    @property
    def mode(self) -> str:
        """
        Gets the value of the 'mode' configuration.

        This property retrieves the 'mode' setting from the internal configuration
        dictionary. If the 'mode' key is not present, it defaults to 'terminal'.

        :return: The current mode setting from the configuration.
        :rtype: str
        """
        return self.config_manager.current_state.mode

    @property
    def attached_loggers(self):
        """
        Provides a dictionary representation of the currently attached loggers and their configurations.

        The function retrieves all handlers attached to the logger instance and compiles
        a dictionary indicating the name and logging level of each handler.

        :return: Dictionary where keys are handler names, and values are dictionaries containing
                 the handler's configuration details such as logging level.
        :rtype: dict
        """
        return self.handler_manager.get_handler_info()


    @property
    def level(self) -> LogLevel:
        """
        Provides access to the logging level of the associated logger instance.

        This property retrieves the string representation of the logging level
        from the logger instance associated with the object.

        :return: The string representation of the logger instance's current
            logging level.
        :rtype: str
        """
        return LogLevel(logging.getLevelName(self.__logger_instance.level))

    @property
    def logger_instance(self) -> logging.Logger:
        """
        Provides access to the logger instance that is used by the class.

        This property returns a logging.Logger instance that can be used
        for logging within the scope of the class or associated operations.
        The logger is initialized privately within the class and is exposed
        through this read-only property.

        :return: The logger instance for the class.
        :rtype: logging.Logger
        """
        return self.__logger_instance

    @property
    def handlers(self) -> list[Handler]:
        """
        Provides access to the list of handlers associated with the logger instance.

        This property allows retrieval of all the handlers currently attached to the
        logger instance. Handlers are responsible for directing the logging output to
        its destination, such as a file, console, or remote server. The list of handlers
        can be used to inspect, modify, or interact with the output configuration of
        the logger.

        :return: List of handlers currently attached to the logger instance
        :rtype: list[Handler]
        """
        return self.__logger_instance.handlers

    @property
    def logger_state(self) -> dict:
        """
        Provides a dictionary that represents the current state of the logger.
        The state includes logging level, run identifier, mode, environment metadata,
        configuration details, and information about handlers attached to the logger.

        :return: A dictionary containing detailed state information of the logger.
        :rtype: dict
        """
        config = self.config_manager.current_state
        env_metadata = self.config_manager.get_env_metadata()

        return {
            "Logging Level": self.level.value,
            "Run Id": self.run_id,
            "Mode": config.mode,
            "Environment Metadata": env_metadata,
            "Configuration": {
                "Color Enabled": config.color_enabled,
                "Highlight Syntax": config.highlight_syntax,
                "Verbose": config.verbose,
                "Deployment Mode": config.deployed,
                "DD Trace Enabled": config.dd_trace_enabled,
                "Global Stream Configured": self.__global_stream_configured
            },
            "Handlers": [type(h).__name__ for h in self.__logger_instance.handlers],
        }

    @property
    def highlight_syntax(self) -> bool:
        """
        Indicates whether syntax highlighting is enabled in the current configuration.

        This property retrieves the value of the `highlight_syntax` setting from the
        internal configuration dictionary.

        :return: A boolean value indicating if syntax highlighting is enabled
        :rtype: bool
        """
        return self.config_manager.current_state.highlight_syntax

    # ---------------- Internals ----------------

    def __log(self, level: Union[LogLevel, logLevels], args,
              no_format: bool = False, no_color: bool = False,
              stack_info: bool = False, header: Optional[str] = None) -> None:
        """Core logging method - now much cleaner thanks to services."""

        if not isinstance(level, LogLevel):
            level = LogLevel(level)

        config = self.config_manager.current_state

        # Process message using MessageProcessor
        msg, exc_info = self.message_processor.process_log_message(
            level, args, config, header, no_color
        )

        # Handle exception info
        if level not in ['ERROR', 'CRITICAL']:
            exc_info = None

        # Update formatters and log
        with self.__lock:
            self.handler_manager.flush_all_handlers()
            self._update_handler_formatters(level, no_format, no_color)

        # Format final message
        if config.should_format_message(no_format):
            if len(msg.strip().splitlines()) > 1 and not msg.startswith('\n'):
                msg = '\n' + msg

        # Actual logging
        self.__logger_instance.log(
            int(level), msg, exc_info=exc_info, stack_info=stack_info,
            stacklevel=get_depth(internal=level == 'INTERNAL')
        )

    def _on_config_changed(self, old_config, new_config):
        """React to configuration changes."""
        # Update color service if needed
        if old_config.color_enabled != new_config.color_enabled:
            if new_config.color_enabled:
                self.color_service.enable_colors()
            else:
                self.color_service.disable_colors()

        # Update local formatters
        if self.config_manager.should_update_formatters(old_config, new_config):
            env_metadata = self.config_manager.get_env_metadata()
            self.handler_manager.update_all_formatters(new_config, env_metadata)

            # Also update global handlers if they exist
            if self.__global_stream_configured:
                # TODO
                pass

    def _update_handler_formatters(self, level: LogLevel, no_format: bool, no_color: bool):
        """Update formatters for the current log operation."""
        config = self.config_manager.current_state
        env_metadata = self.config_manager.get_env_metadata()

        for handler in self.__logger_instance.handlers:
            if not isinstance(handler, logging.NullHandler):
                formatter = self.formatter_factory.create_formatter(
                    level=level, config_state=config, env_metadata=env_metadata,
                    global_stream_configured=self.__global_stream_configured,
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

    def __setup(self) -> None:
        """Initialize the logger with basic configuration."""
        with self.__lock:
            if self.__initialized:
                self._internal_log("Logger already initialized. Skipping setup.")
                return

            # Set up color service based on initial config
            config = self.config_manager.current_state
            if config.color_enabled:
                self.color_service.enable_colors()
            else:
                self.color_service.disable_colors()

            # Add initial handler
            self.handler_manager.flush_all_handlers()
            self.__logger_instance.setLevel(self.__base_level)
            self.handler_manager.add_handler(logging.StreamHandler, config, stream=sys.stdout, force_replace=True)
            self.__logger_instance.propagate = False
            self.__initialized = True

    # ---------------- Aliases/Shortcuts ----------------

    data = __pretty_log

    def cdata(self, data: Any, **kwargs) -> None:
        """
        Logs the provided data in a compact and human-readable format.

        This method is responsible for processing the given data and formatting
        it into a compact, human-readable log.
        It accepts additional keyword arguments to configure logging behavior.

        :param data: Input data to be logged in a compact format.
        :type data: Any
        :param kwargs: Additional keyword arguments for logging configuration.
        """
        return self.__pretty_log(data, compact=True, **kwargs)

import importlib
import inspect
import logging
import os
import re
import sys
import time
import json
import warnings
from datetime import datetime
from logging import Handler
from types import TracebackType
from typing import Any, Optional, Union, Literal, Type, IO, Dict, Callable
from difflib import get_close_matches
from contextlib import contextmanager
import threading

from .._Internal._MockPandas import _MockPandas
from ..Decorators.Deprecated import Deprecated
from ..Decorators.SingletonClass import SingletonClass

try:
    import pandas as pd
except ImportError:
    pd = _MockPandas()


class _ExceptionSuggestor:
    @staticmethod
    def suggest_similar(error: BaseException, frame_depth=20, n_suggestions=1, cutoff=0.6) -> Optional[str]:
        if not isinstance(error, BaseException):
            return None
        error_msg = error.args[0]
        if not error.__class__.__name__.lower() in error_msg.lower():
            error_msg = f"  {error.__class__.__name__}: {error_msg}"
        else:
            error_msg = f"  {error_msg}"

        obj_match = re.search(r"'(\w+)' object has no attribute", error_msg)
        key_match = re.search(r"has no attribute '(\w+)'", error_msg)

        if not key_match:
            return error_msg

        source_obj = obj_match.group(1) if obj_match else None
        missing_attr = key_match.group(1)

        for frame in reversed(inspect.stack()[:frame_depth]):
            for var in frame.frame.f_locals.values():
                if not hasattr(var, '__class__'):
                    continue
                if var.__class__.__name__ == source_obj:
                    keys = [k for k in dir(var) if not k.startswith('__')]
                    matches = get_close_matches(missing_attr, keys, n=n_suggestions, cutoff=cutoff)
                    if matches:
                        return f"{error_msg}\n    Did you mean: {', '.join(matches)}?\n"
        return error_msg


class _MockColorama:
    pass


class ColorPresets:
    """
    Provides color presets for common log use-cases.
    Falls back to mock colors if colorama isn't installed.
    """
    _color_class = _MockColorama
    _style_class = _MockColorama
    INFO = None
    DEBUG = None
    WARNING = None
    ERROR = None
    CRITICAL = None
    HEADER = None
    BRIGHT = None
    NORMAL = None

    RESET = None
    RESET_FORE = None

    COLOR_TRUE = None
    COLOR_FALSE = None
    COLOR_NONE = None
    COLOR_NUMBER = None
    COLOR_UUID = None

    COLOR_BRACE_OPEN = None
    COLOR_BRACE_CLOSE = None
    COLOR_BRACKET_OPEN = None
    COLOR_BRACKET_CLOSE = None
    COLOR_PAREN_OPEN = None
    COLOR_PAREN_CLOSE = None
    COLOR_COLON = None
    COLOR_COMMA = None

    _INTERNAL_DIM_COLOR = None
    _INTERNAL_DIM_STYLE = None

    def __init__(self, color, style):
        super().__setattr__('_color_class', color)
        super().__setattr__('_style_class', style)
        super().__setattr__('INFO', getattr(self._color_class, 'GREEN', ''))
        super().__setattr__('DEBUG', getattr(self._color_class, 'WHITE', ''))
        super().__setattr__('WARNING', getattr(self._color_class, 'YELLOW', ''))
        super().__setattr__('ERROR', getattr(self._color_class, 'RED', ''))
        super().__setattr__('CRITICAL', getattr(self._color_class, 'MAGENTA', ''))
        super().__setattr__('HEADER', getattr(self._color_class, 'CYAN', ''))

        super().__setattr__('BRIGHT', getattr(self._style_class, 'BRIGHT', ''))
        super().__setattr__('NORMAL', getattr(self._style_class, 'NORMAL', ''))
        super().__setattr__('RESET', getattr(self._style_class, 'RESET_ALL', ''))
        super().__setattr__("RESET_FORE", getattr(self._color_class, 'RESET', ''))

        # Literal colors
        super().__setattr__('COLOR_TRUE', getattr(self._color_class, 'GREEN', ''))
        super().__setattr__('COLOR_FALSE', getattr(self._color_class, 'RED', ''))
        super().__setattr__('COLOR_NONE', getattr(self._color_class, 'WHITE', ''))
        super().__setattr__('COLOR_NUMBER', getattr(self._color_class, 'YELLOW', ''))
        super().__setattr__('COLOR_UUID', getattr(self._color_class, 'MAGENTA', ''))

        # Syntax colors
        super().__setattr__('COLOR_BRACE_OPEN', getattr(self._color_class, 'CYAN', ''))     # {
        super().__setattr__('COLOR_BRACE_CLOSE', getattr(self._color_class, 'CYAN', ''))    # }
        super().__setattr__('COLOR_BRACKET_OPEN', getattr(self._color_class, 'BLUE', ''))      # [
        super().__setattr__('COLOR_BRACKET_CLOSE', getattr(self._color_class, 'BLUE', ''))     # ]
        super().__setattr__('COLOR_PAREN_OPEN', getattr(self._color_class, 'BLUE', ''))        # (
        super().__setattr__('COLOR_PAREN_CLOSE', getattr(self._color_class, 'BLUE', ''))       # )
        super().__setattr__('COLOR_COLON', getattr(self._color_class, 'MAGENTA', ''))           # :
        super().__setattr__('COLOR_COMMA', getattr(self._color_class, 'MAGENTA', ''))            # ,

        super().__setattr__('_INTERNAL_DIM_COLOR', getattr(self._color_class, 'WHITE', ''))
        super().__setattr__('_INTERNAL_DIM_STYLE', getattr(self._style_class, 'DIM', ''))

    def __setattr__(self, name, value):
        allowed_color_values = [val.lower() for val in self._color_class.__dict__.values() if val != 'RESET']
        allowed_style_values = [val.lower() for val in self._style_class.__dict__.values() if val != 'RESET_ALL']
        allowed_names = [val.lower() for val in self.__dict__.keys() if val != 'RESET']

        if not name.lower() in allowed_names:
            raise ValueError(f"Invalid name for '{name}': {name}. Allowed names: {allowed_names}")

        if name.lower() in allowed_color_values:
            value = getattr(self._color_class, value.upper())
        elif name.lower() in allowed_style_values:
            value = getattr(self._style_class, value.upper())
        else:
            raise ValueError(
                f"Invalid value for '{name}': {value}. Allowed values: {allowed_color_values + allowed_style_values}")

        name = name.upper()
        super().__setattr__(name, value)

    def get_color_by_level(self, level: Union[str, int]):
        if isinstance(level, int):
            str_name = logging.getLevelName(level)
        else:
            str_name = level.upper()
        if str_name == 'INTERNAL':
            return self._INTERNAL_DIM_COLOR
        return getattr(self, str_name, '')


    def get_level_style(self, level: Union[str, int]):
        if isinstance(level, int):
            str_name = logging.getLevelName(level)
        else:
            str_name = level.upper()
        if str_name in ['INFO', 'DEBUG']:
            return self.NORMAL
        elif str_name in ['WARNING', 'ERROR', 'CRITICAL', 'HEADER']:
            return self.BRIGHT
        elif str_name == 'INTERNAL':
            return self._INTERNAL_DIM_STYLE
        else:
            return self.NORMAL

    def get_message_color(self, level: Union[str, int]):
        if isinstance(level, int):
            str_name = logging.getLevelName(level)
        else:
            str_name = level.upper()
        if str_name in ['CRITICAL', 'ERROR']:
            return getattr(self, str_name, '')
        else:
            return ''


    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

class _CustomFormatter(logging.Formatter):
    def __init__(self, fmt: str, datefmt: Optional[str], presets: ColorPresets):
        super().__init__(fmt, datefmt)
        self.presets = presets

    def formatStack(self, exc_info: str) -> str:
        dim_color = self.presets._INTERNAL_DIM_COLOR or ''
        dim_style = self.presets._INTERNAL_DIM_STYLE or ''
        reset = self.presets.RESET or ''
        return f"{dim_color}{dim_style}{exc_info}{reset}"

    def formatException(self, ei) -> str:
        original = super().formatException(ei)
        dim_color = self.presets._INTERNAL_DIM_COLOR or ''
        dim_style = self.presets._INTERNAL_DIM_STYLE or ''
        reset = self.presets.RESET or ''
        return f"{dim_color}{dim_style}{original}{reset}"


class _JSONLogFormatter(logging.Formatter):
    def __init__(self, env_metadata: dict, forced_color: bool, highlight_func: Callable):
        super().__init__()
        self.env_metadata = env_metadata
        self.color_mode = forced_color
        self.highlight_func = highlight_func


    def _extract_generic_context(self) -> dict:
        """
        Scan all active ContextVars for common keys like user_id, client_id, or organization_id.
        Supports deeply nested dicts and custom objects.
        """


        context_data = {}
        user_keys = {'user_id', 'usr_id', 'entity_id', 'user_entity_id'}
        org_keys = {'client_id', 'org_id', 'organization_id'}

        def scan_dict(d: dict):
            found = {}
            try:
                for k, v in d.items():
                    key_lower = k.lower()
                    if key_lower in user_keys:
                        found['user_id'] = v
                    elif key_lower in org_keys:
                        found['organization_id'] = v
                    elif isinstance(v, dict):
                        found.update(scan_dict(v))
                    elif hasattr(v, '__dict__'):
                        found.update(scan_dict(vars(v)))
            finally:
                return found

        try:
            import contextvars
            ctx = contextvars.copy_context()
            for var in ctx:
                val = var.get()
                if isinstance(val, dict):
                    context_data.update(scan_dict(val))
                elif hasattr(val, '__dict__'):
                    context_data.update(scan_dict(vars(val)))
        finally:
            return context_data



    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "level": record.levelname,
            "logger": record.name,
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),

            # Required for Datadog log correlation
            "dd.env": self.env_metadata.get("env"),
            "dd.service": self.env_metadata.get("project"),
            "dd.version": self.env_metadata.get("project_version"),
            "dd.trace_id": str(getattr(record, "dd.trace_id", "")),
            "dd.span_id": str(getattr(record, "dd.span_id", "")),
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        ctx = self._extract_generic_context()
        if len(ctx) > 0:
            log_record.update(ctx)

        dumped_json = json.dumps(log_record, default=str, ensure_ascii=False)

        if self.color_mode:
            dumped_json = self.highlight_func(dumped_json, True)

        return dumped_json

_exc_info_type = None | bool | tuple[Type[BaseException], BaseException, TracebackType | None] | tuple[
    None, None, None] | BaseException


class _BaseLogger:
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
    • Singleton-safe with `_logger_()` for consistent usage across modules.

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


    def __init__(self, level: str = 'INFO') -> None:
        # Thread safety lock

        self.__lock = threading.RLock()
        self.__logger_instance = logging.getLogger('WrenchCL')
        # Basic logger state
        self.__global_stream_configured = False
        self.__force_markup = False
        self.__initialized = False
        self.run_id = self.__generate_run_id()
        self.__base_level = 'DEBUG'

        # Mode flags (simplified to a single dictionary)
        self.__config = {
            'mode': 'terminal',      # 'terminal', 'json', or 'compact'
            'highlight_syntax': True,
            'verbose': False,
            'deployed': False,
            'dd_trace_enabled': False,
            'color_enabled': True
        }

        # Initialize objects
        self.__start_time = None
        self.__dd_log_flag = False
        self.presets = ColorPresets(None, None)
        self.__env_metadata = self.__fetch_env_metadata()

        # Read environment variables
        self.__config['dd_trace_enabled'] = os.environ.get("LOG_DD_TRACE", "false").lower() == "true"
        self.__config['color_enabled'] = os.environ.get("COLOR_MODE", "true").lower() == "true"
        self.__from_context = False
        # Set up logger instance
        self.__setup()
        self.reinitialize()
        self._internal_log(f"Logger -> Color:{self.__config['color_enabled']} | Mode:{self.__config['mode'].capitalize()} | Deployment:{self.__config['deployed']}")

    # ---------------- Public Configuration API ----------------

    def configure(self,
                  mode: Optional[Literal['terminal', 'json', 'compact']] = None,
                  level: Optional[str] = None,
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

        with self.__lock:
            if not suppress_autoconfig:
                self.__check_deployment()
            if mode is not None:
                self.__config['mode'] = mode
            if highlight_syntax is not None:
                self.__config['highlight_syntax'] = highlight_syntax
            if level is not None:
                self.setLevel(level)
            if color_enabled is not None:
                self.__config['color_enabled'] = color_enabled
            if verbose is not None:
                self.__config['verbose'] = verbose
            if deployment_mode is not None:
                self.__config['deployed'] = deployment_mode
            if trace_enabled is not None:
                self.__config['dd_trace_enabled'] = trace_enabled
                try:
                    import ddtrace
                    ddtrace.patch(logging=True)
                    self._internal_log("Datadog trace injection enabled via ddtrace.patch(logging=True)")
                    os.environ["DD_TRACE_ENABLED"] = "true"
                except ImportError:
                    self.__config['dd_trace_enabled'] = False
                    self._internal_log("   Datadog trace injection disabled: `ddtrace` module not available.")
            if self.__config.get('dd_trace_enabled') and self.__config['mode'] != 'json':
                self._internal_log("   Trace injection requested, but trace_id/span_id only appear in JSON mode.")
            self.__check_color()
            self.__env_metadata = self.__fetch_env_metadata()

    def reinitialize(self, verbose = False):
        """
        Reinitializes the current environment state by rechecking deployment
        configuration, color scheme, and fetching updated metadata for the
        environment. Optionally logs the internal state if verbose is enabled.

        :param verbose: A boolean indicating whether detailed internal logging
                        should be enabled during reinitialization.
        :type verbose: bool

        :return: None
        """
        with self.__lock:
            self.__check_deployment(verbose)
            self.__check_color()
            self.__env_metadata = self.__fetch_env_metadata()
            if verbose:
                self._internal_log(json.dumps(self.logger_state, indent=2, default=lambda x: str(x), ensure_ascii=False))

    def update_color_presets(self, **kwargs) -> None:
        """
        Updates the color presets dictionary with the given key-value pairs.

        This method is used to update the existing color presets with new or modified
        key-value pairs provided through the keyword arguments. It ensures thread-safety
        by acquiring a lock during the update to prevent race conditions.

        :param kwargs: Arbitrary keyword arguments representing the color presets
            to update. The keys are the preset names, and the values are their
            corresponding configurations.
        :return: None
        """
        with self.__lock:
            self.presets.update(**kwargs)

    def setLevel(self, level: Union[Literal["DEBUG", "INFO", 'WARNING', 'ERROR', 'CRITICAL'], int]) -> None:
        """
        Sets the logging level for the application, determining the severity of messages
        that should be handled. This method updates the logging configuration by flushing
        handlers and applying the new level to the logger instance.

        :param level: The desired logging level. Can either be an integer or one of the
            predefined logging level literals - "DEBUG", "INFO", "WARNING", "ERROR",
            or "CRITICAL". These levels regulate which log messages are processed.
        :return: None
        """
        with self.__lock:
            self.flush_handlers()
            self.__logger_instance.setLevel(self.__get_level(level))

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
            self.run_id = self.__generate_run_id()

    # ---------------- Core Logging Methods ----------------

    def info(self, *args, exc_info: _exc_info_type = None, **kwargs) -> None:
        """
        Logs an INFO-level message.

        :param args: Strings or objects to log
        :param exc_info: Optional exception info
        :param no_format: If True, disables structured formatting
        """
        self.__log(logging.INFO, *args, exc_info=exc_info, **kwargs)

    def warning(self, *args, exc_info: _exc_info_type = None, **kwargs) -> None:
        """
        Logs a WARNING-level message.

        :param args: Strings or objects to log
        :param exc_info: Optional exception info
        :param no_format: If True, disables structured formatting
        """
        self.__log(logging.WARNING, *args, exc_info=exc_info, **kwargs)

    def error(self, *args, exc_info: _exc_info_type = True, **kwargs) -> None:
        """
        Logs an ERROR-level message.

        :param args: Strings or objects to log
        :param exc_info: Exception info (defaults to True)
        :param no_format: If True, disables structured formatting
        """
        self.__log(logging.ERROR, *args, exc_info=exc_info, **kwargs)

    def critical(self, *args, exc_info: _exc_info_type = None, **kwargs) -> None:
        """
        Logs a CRITICAL-level message.

        :param args: Strings or objects to log
        :param exc_info: Optional exception info
        :param no_format: If True, disables structured formatting
        """
        self.__log(logging.CRITICAL, *args, exc_info=exc_info, **kwargs)

    def debug(self, *args, exc_info: _exc_info_type = None, **kwargs) -> None:
        """
        Logs a DEBUG-level message.

        :param args: Strings or objects to log
        :param exc_info: Optional exception info
        :param no_format: If True, disables structured formatting
        """
        self.__log(logging.DEBUG, *args, exc_info=exc_info, **kwargs)

    def exception(self, *args, exc_info: _exc_info_type = True, **kwargs) -> None:
        """
        Logs an ERROR-level message with exception info.

        :param args: Strings or objects to log
        :param exc_info: Exception info (defaults to True)
        :param no_format: If True, disables structured formatting
        """
        self.__log(logging.ERROR, *args, exc_info=exc_info, **kwargs)

    def _internal_log(self, *args) -> None:
        """Internal logging method for logger infrastructure messages."""
        if not self.__from_context:
            self.__log(logging.WARNING, *args, color_flag="INTERNAL")

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
            self._internal_log(f"{message}: {elapsed:.2f}s")

    def header(self, text: str, size:int =None, compact=False) -> None:
        """
        Formats and logs a text message as a header with optional size and compact
        mode settings.

        The method processes the provided text by replacing underscores and
        hyphens with spaces, trimming whitespace, and capitalizing the first
        letter. Depending on the compact mode or configuration, it formats the
        header differently and centers it within the given size width. Then it
        logs the formatted header.

        :param text: The text to be formatted and logged as a header.
        :param size: Optional size of the output header's width for centering the
            text. If not provided, defaults to 40 for compact mode or 80 otherwise.
        :param compact: A boolean flag that determines whether to use compact
            mode formatting. This also overrides the global configuration's
            compact mode setting. Defaults to False.
        :return: None
        """
        text = text.replace('_', ' ').replace('-', ' ').strip().capitalize()
        if compact or self.__config['mode'] == 'compact':
            size = size or 40
            formatted = self.__apply_color(text, self.presets.HEADER).center(size, "-")
        else:
            size = size or 80
            formatted = "\n" + self.__apply_color(text, self.presets.HEADER).center(size, "-")
        self.__log("INFO", formatted, no_format=True, no_color=True)

    def pretty_log(self, obj: Any, indent=4, **kwargs) -> None:
        """
        Logs a given object in a visually formatted manner, handling various object types including
        pandas DataFrames, objects with custom serialization methods, dictionaries, and JSON strings.
        The method includes options for indentation and keyword arguments for customization.

        :param obj: The object to be logged. Can be of type `pandas.DataFrame`, a dictionary, JSON
            string, or an object with methods like `pretty_print`, `model_dump_json`, `dump_json_schema`,
            or `json`.
        :type obj: Any
        :param indent: Indentation level for pretty printing JSON or similar structures.
            Defaults to 4.
        :type indent: int
        :param kwargs: Additional keyword arguments passed to specific serialization methods based
            on the object type.
        :type kwargs: dict
        :return: None
        """
        try:
            if isinstance(obj, pd.DataFrame):
                prefix_str = f"DataType: {type(obj).__name__} | Shape: {obj.shape[0]} rows | {obj.shape[1]} columns"
                pd.set_option(
                    'display.max_rows', 500,
                    'display.max_columns', None,
                    'display.width', None,
                    'display.max_colwidth', 50,
                    'display.colheader_justify', 'center'
                )
                output = str(obj)
            elif hasattr(obj, 'pretty_print'):
                output = obj.pretty_print(**kwargs)
            elif hasattr(obj, 'model_dump_json'):
                output = obj.model_dump_json(indent=indent, **kwargs)
            elif hasattr(obj, 'dump_json_schema'):
                output = obj.dump_json_schema(indent=indent, **kwargs)
            elif hasattr(obj, 'json'):
                output = json.dumps(obj.json(), indent=indent, ensure_ascii=False, **kwargs)
            elif isinstance(obj, dict):
                output = json.dumps(obj, indent=indent, ensure_ascii=False, **kwargs)
            elif isinstance(obj, str):
                try:
                    output = json.dumps(json.loads(obj), indent=indent, ensure_ascii=False, **kwargs, default=str)
                except Exception:
                    output = str(obj)
            else:
                output = str(obj)
        except Exception:
            output = str(obj)
        self.__log(logging.INFO, output, exc_info=False, color_flag="DATA")

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
        with self.__lock:
            for h in self.__logger_instance.handlers:
                try:
                    h.flush()
                except Exception:
                    pass

    def close(self):
        """
        Closes all handlers associated with the logger instance, ensuring any buffered log
        entries are flushed before removing the handlers. It also manages the cleanup of
        global stream handlers if they were configured.

        This method ensures that all resources associated with logging handlers are properly
        released. If any errors occur while closing a handler, they are logged to standard
        error, but the process continues to ensure other handlers are also cleaned up.

        :return: None
        :rtype: None
        """
        with self.__lock:
            self.flush_handlers()
            for handler in list(self.__logger_instance.handlers):
                try:
                    handler.close()
                    self.__logger_instance.removeHandler(handler)
                except Exception as e:
                    # Log failure but continue with remaining handlers
                    sys.stderr.write(f"Error closing handler: {str(e)}\n")

            # If we've configured global logging, clean that up too
            if self.__global_stream_configured:
                root_logger = logging.getLogger()
                for handler in list(root_logger.handlers):
                    try:
                        handler.close()
                        root_logger.removeHandler(handler)
                    except Exception:
                        pass

    # ---------------- Handler Management ----------------

    def add_new_handler(
        self,
        handler_cls: Type[logging.Handler] = logging.StreamHandler,
        stream: Optional[IO[str]] = None,
        level: Union[str, int] = None,
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
        with self.__lock:
            if not level:
                level = self.__base_level

            level = self.__get_level(level)

            if issubclass(handler_cls, logging.StreamHandler):
                if stream is None:
                    raise ValueError("StreamHandler requires a valid `stream` argument.")
                handler = handler_cls(stream)
            else:
                handler = handler_cls()

            handler.setLevel(level)

            if not formatter:
                formatter = self.__get_formatter(level)
            handler.setFormatter(formatter)

            if force_replace:
                self.__logger_instance.handlers = []

            self.__logger_instance.addHandler(handler)
            return handler

    def add_rotating_file_handler(
        self,
        filename: str,
        max_bytes: int = 10485760,  # 10MB default
        backup_count: int = 5,
        level: Union[str, int] = None,
        formatter: Optional[logging.Formatter] = None,
    ) -> logging.Handler:
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
        try:
            from logging.handlers import RotatingFileHandler
        except ImportError:
            self.error("Rotating file handler requires Python's logging.handlers module")
            return None

        with self.__lock:
            handler = RotatingFileHandler(
                filename=filename,
                maxBytes=max_bytes,
                backupCount=backup_count,
                delay=True  # Only create file when first log written
            )

            if not level:
                level = self.__base_level
            handler.setLevel(self.__get_level(level))

            if not formatter:
                formatter = self.__get_formatter(level)
            handler.setFormatter(formatter)

            self.__logger_instance.addHandler(handler)
            return handler

    # ---------------- Global Configuration ----------------

    def attach_global_stream(self, level: str = "INFO", silence_others: bool = False, stream = sys.stdout) -> None:
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
        :return: None
        :rtype: None
        """
        with self.__lock:
            self.flush_handlers()
            root_logger = logging.getLogger()
            root_logger.setLevel(self.__base_level)

            handler = self.add_new_handler(
                logging.StreamHandler,
                stream=stream,
                level=level,
                force_replace=True,
                formatter=self.__get_formatter(level),
            )
            root_logger.handlers = [handler]
            root_logger.propagate = False

            if silence_others:
                self.silence_other_loggers()

            self.__global_stream_configured = True

        # Log outside the lock
        self._internal_log(" Global stream configured successfully.")

    def set_named_logger_level(self, logger_name: str, level: Optional[int] = None) -> None:
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
        :type level: Optional[int]
        :return: None
        """
        if not level:
            level = logging.CRITICAL + 1

        with self.__lock:
            if not self.__global_stream_configured:
                logger = logging.getLogger(logger_name)
                for h in logger.handlers:
                    h.flush()
                logger.handlers = [logging.NullHandler()]
                logger.setLevel(level)
                if level >= logging.CRITICAL + 1:
                    logger.propagate = False

    def set_attached_handler_level(self, handler_name:str, level: Optional[int] = None) -> None:
        """
        Sets the logging level and formatter of an attached handler identified
        by its name. If the level is not provided, the current logger level is used.

        :param handler_name: The name of the handler to modify.
        :type handler_name: str
        :param level: The logging level to set for the handler. If None, the
                      level of the logger is used.
        :type level: Optional[int]
        :return: None
        """
        if handler_name in self.attached_loggers:
            for h in self.logger_instance.handlers:
                if h.name == handler_name:
                    h.setLevel(self.__get_level(level))
                    if level is None:
                        h.setFormatter(self.__get_formatter(self.level))
                    else:
                        h.setFormatter(self.__get_formatter(level))
                    break

    def silence_logger(self, logger_name:str) -> None:
        """
        Sets the logging level to effectively silence the specified logger by assigning
        a level higher than CRITICAL.

        :param logger_name: The name of the logger to be silenced.
        :type logger_name: str
        :return: This method does not return anything.
        :rtype: None
        """
        level = logging.CRITICAL + 1
        self.set_named_logger_level(logger_name, level)

    def silence_other_loggers(self) -> None:
        """
        Silences all loggers except for the logger named 'WrenchCL'.

        This function iterates through all loggers present in the logging manager's
        logger dictionary. For each logger found, it silences it by invoking the
        `silence_logger` method unless the logger's name is 'WrenchCL'.

        :return: None
        """
        for name in logging.root.manager.loggerDict:
            if name != 'WrenchCL':
                self.silence_logger(name)

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
            with self.__lock:
                import colorama
                self.__force_markup = True
                self.enable_color()
                colorama.deinit()
                colorama.init(strip=False, convert=False)
                sys.stdout = colorama.AnsiToWin32(sys.stdout).stream
                sys.stderr = colorama.AnsiToWin32(sys.stderr).stream
                if self.__force_markup and self.__config['deployed']:
                    warnings.warn("Forcing Markup in deployment mode is not recommended and will cause issues in external parsers like cloudwatch and Datadog", category=RuntimeWarning, stacklevel=5)
                # Update color presets and reconfigure formatters
                self.presets = ColorPresets(self._Color, self._Style)
                self.flush_handlers()
                if self.__config['mode'] == 'json':
                    self.__use_json_logging()
                else:
                    for handler in self.__logger_instance.handlers:
                        handler.setFormatter(self.__get_formatter(self.__logger_instance.level))

                if self.__global_stream_configured:
                    root_logger = logging.getLogger()
                    for handler in root_logger.handlers:
                        handler.setFormatter(self.__get_formatter(root_logger.level))

            self._internal_log("Forced color output enabled.")
        except ImportError:
            self.warning("Colorama is not installed; cannot force color output.")

    def enable_color(self):
        """
        Enables color support for terminal output. This method initializes the `colorama`
        library if available and updates the internal configuration to enable colorized
        output. It also initializes the presets for specific color and style usage.
        If `colorama` is not installed, the method disables color support.

        :raises ImportError: If the `colorama` module cannot be imported.
        """
        try:
            with self.__lock:
                colorama = importlib.import_module("colorama")
                self.__config['color_enabled'] = True
                self.__config['highlight_syntax'] = True if self.__config['highlight_syntax'] is not False else False
                self._Color = colorama.Fore
                self._Style = colorama.Style
                self.presets = ColorPresets(self._Color, self._Style)
                colorama.deinit()
                colorama.init(strip=False, autoreset=False)
        except ImportError:
            self._internal_log("Colorama not installed. Cannot enable color output.")
            self.disable_color()

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
        with self.__lock:
            self._Color = _MockColorama
            self._Style = _MockColorama
            self.__config['color_enabled'] = False
            self.__config['highlight_syntax'] = False
            try:
                colorama = importlib.import_module("colorama")
                colorama.deinit()
            except ImportError:
                pass
            self.presets = ColorPresets(self._Color, self._Style)

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

    # ---------------- Context Manager ----------------

    @contextmanager
    def temporary(
        self,
        level: Optional[Union[str, int]] = None,
        mode: Optional[Literal['terminal', 'json', 'compact']] = None,
        color_enabled: Optional[bool] = None,
        verbose: Optional[bool] = None,
        trace_enabled: Optional[bool] = None,
        highlight_syntax: Optional[bool] = None,
        deployed: Optional[bool] = None,
    ):
        """
        Temporarily override logger configuration within a scoped context.

        :param level: Log level (e.g. 'DEBUG', 'INFO', or int).
        :param mode: Output mode ('terminal', 'json', 'compact').
        :param color_enabled: Enables or disables ANSI color output.
        :param verbose: Enables verbose logging.
        :param trace_enabled: Enables Datadog trace correlation.
        :param highlight_syntax: Enables literal highlighting.
        :param deployed: Toggles deployment mode behavior.
        """
        with self.__lock:
            self.__from_context = True
            original_values = {}

            # Handle level separately
            if level is not None:
                original_values['level'] = self.level
                self.setLevel(level)

            # Save existing config values
            if mode is not None:
                original_values['mode'] = self.__config['mode']
            if color_enabled is not None:
                original_values['color_enabled'] = self.__config['color_enabled']
            if verbose is not None:
                original_values['verbose'] = self.__config['verbose']
            if trace_enabled is not None:
                original_values['dd_trace_enabled'] = self.__config['dd_trace_enabled']
            if highlight_syntax is not None:
                original_values['highlight_syntax'] = self.__config['highlight_syntax']
            if deployed is not None:
                original_values['deployed'] = self.__config['deployed']

            # Apply changes
            self.configure(
                mode=mode,
                color_enabled=color_enabled,
                verbose=verbose,
                trace_enabled=trace_enabled,
                highlight_syntax=highlight_syntax,
                deployment_mode=deployed,
                suppress_autoconfig=True
            )

        try:
            yield
        finally:
            with self.__lock:
                if 'level' in original_values:
                    self.setLevel(original_values['level'])

                self.configure(
                    mode=original_values.get('mode'),
                    color_enabled=original_values.get('color_enabled'),
                    verbose=original_values.get('verbose'),
                    trace_enabled=original_values.get('dd_trace_enabled'),
                    highlight_syntax=original_values.get('highlight_syntax'),
                    deployment_mode=original_values.get('deployed'),
                    suppress_autoconfig=True
                )
            self.__from_context = False


    # ---------------- Properties (SIMPLIFIED) ----------------

    @property
    def mode(self) -> str:
        """
        Gets the value of the 'mode' configuration.

        This property retrieves the 'mode' setting from the internal configuration
        dictionary. If the 'mode' key is not present, it defaults to 'terminal'.

        :return: The current mode setting from the configuration.
        :rtype: str
        """
        return self.__config.get('mode', 'terminal')

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
        return_dict = {}
        for h in self.__logger_instance.handlers:
            return_dict[h.name] = {'level': h.level}
        return return_dict

    @property
    def level(self) -> str:
        """
        Provides access to the logging level of the associated logger instance.

        This property retrieves the string representation of the logging level
        from the logger instance associated with the object.

        :return: The string representation of the logger instance's current
            logging level.
        :rtype: str
        """
        return logging.getLevelName(self.__logger_instance.level)

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
        return {
            "Logging Level": self.level,
            "Run Id": self.run_id,
            "Mode": self.__config['mode'],
            "Environment Metadata": self.__env_metadata,
            "Configuration": {
                "Color Enabled": self.__config['color_enabled'],
                "Highlight Syntax": self.__config['highlight_syntax'],
                "Verbose": self.__config['verbose'],
                "Deployment Mode": self.__config['deployed'],
                "DD Trace Enabled": self.__config['dd_trace_enabled'],
                "Global Stream Configured": self.__global_stream_configured
            },
            "Handlers": [type(h).__name__ for h in self.__logger_instance.handlers],
        }

    @property
    def color_presets(self) -> ColorPresets:
        """
        Provides access to predefined color presets associated with the object. These
        presets can be used to define color configurations or themes based on the
        underlying data.

        :rtype: ColorPresets
        :return: A collection of predefined color presets.
        """
        return self.presets

    @property
    def highlight_syntax(self) -> bool:
        """
        Indicates whether syntax highlighting is enabled in the current configuration.

        This property retrieves the value of the `highlight_syntax` setting from the
        internal configuration dictionary.

        :return: A boolean value indicating if syntax highlighting is enabled
        :rtype: bool
        """
        return self.__config['highlight_syntax']

    # ---------------- Internals ----------------

    def __log(self, level: Union[int, str], *args: str, exc_info: _exc_info_type = None,
              color_flag: Optional[Literal['INTERNAL', 'DATA']] = None, **kwargs) -> None:
        """Thread-safe logging implementation."""
        args = list(args)
        for idx, a in enumerate(args):
            if isinstance(a, Exception) or isinstance(a, BaseException):
                exc_info = args.pop(idx)

        if self.__config['mode'] == 'terminal':
            suggestion = self.__suggest_exception(exc_info)
            if suggestion:
                suggestion = f"{self.presets.ERROR}{suggestion}{self.presets.RESET}"
                args.append(suggestion)

        args = tuple(args)
        msg = '\n'.join(str(arg) for arg in args)

        if self.__config['highlight_syntax'] and self.__config['color_enabled'] and not self.__config['mode'] == 'json':
            msg = self.__highlight_literals(msg, data=color_flag == 'DATA')

        # Format based on mode
        if self.__config['mode'] == 'compact' or self.__config['deployed'] or self.__config['mode'] == 'json':
            lines = msg.splitlines()
            msg = ' '.join([line.strip() for line in lines if len(line.strip()) > 0])
            msg = msg.replace('\n', ' ').replace('\r', '').strip()

        if color_flag == 'INTERNAL':
            level = "INTERNAL"
        elif color_flag == 'DATA':
            level = "DATA"

        # Use lock for handler configuration
        with self.__lock:
            self.flush_handlers()
            for handler in self.__logger_instance.handlers:
                if not isinstance(handler, logging.NullHandler):
                    handler.setFormatter(self.__get_formatter(
                        level,
                        no_format=kwargs.get('no_format', False)
                    ))

            # Process multi-line messages
            lines = msg.splitlines()
            if len(lines) > 1:
                msg = "    " + "\n    ".join(lines)
            if exc_info:
                msg = "\n".join(lines)

            if isinstance(level, str):
                level = self.__get_level(level)
        # Actual logging outside the lock to prevent deadlocks
        self.__logger_instance.log(
            level,
            msg,
            exc_info=exc_info,
            stack_info=kwargs.get('stack_info', False),
            stacklevel=self.__get_depth(internal = color_flag == 'INTERNAL')
        )

    @staticmethod
    def __remove_ansi_codes(text: str) -> str:
        """Remove any existing ANSI escape codes from the text."""
        return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)

    def __highlight_literals(self, msg: str, data: bool = False) -> str:
        """Add syntax highlighting to literals in log messages."""
        msg = self.__remove_ansi_codes(msg)

        if self.__force_markup:
            pass
        elif not self.__config['color_enabled'] or not self.__config['highlight_syntax'] or self.__config['deployed']:
            return msg

        c = self.presets

        # Highlight numbers
        msg = re.sub(
            r'(?<![\w-])'            # no word char or hyphen before
            r'(\d+(?:\.\d+)?[a-zA-Z%]*)'  # number with optional decimal and unit suffix
            r'(?=\s|$|\)|(?=\W\s))',  # end must be space, end-of-line, closing paren, or punctuation+space
            lambda m: f"{c.COLOR_NUMBER}{m.group(1)}{c.RESET_FORE}",
            msg
        )

        # Boolean/None literals — match as full words
        msg = re.sub(r'\btrue\b', lambda m: f"{c.COLOR_TRUE}{m.group(0)}{c.RESET_FORE}", msg, flags=re.IGNORECASE)
        msg = re.sub(r'\bfalse\b', lambda m: f"{c.COLOR_FALSE}{m.group(0)}{c.RESET_FORE}", msg, flags=re.IGNORECASE)
        msg = re.sub(r'\bnone\b', lambda m: f"{c.COLOR_NONE}{m.group(0)}{c.RESET_FORE}", msg, flags=re.IGNORECASE)
        msg = re.sub(r'\bnull\b', lambda m: f"{c.COLOR_NONE}{m.group(0)}{c.RESET_FORE}", msg, flags=re.IGNORECASE)
        msg = re.sub(r'\bnan\b', lambda m: f"{c.COLOR_NONE}{m.group(0)}{c.RESET_FORE}", msg, flags=re.IGNORECASE)

        msg = re.sub(
            r'^[ \t]*\[(.*?)\]',  # only literal spaces/tabs allowed
            lambda m: f"{c.COLOR_COLON}[{m.group(1)}]{c.RESET_FORE}",
            msg
        )

        # Highlight %s and %{}s placeholders
        msg = re.sub(
            r'%\{?[a-zA-Z0-9]*[s]\}?\b',  # Match %s and %{xxc}s
            lambda m: f"{c.COLOR_COLON}{m.group(0)}{c.RESET_FORE}",
            msg
        )

        # Highlight only the literal curly braces and |
        msg = re.sub(
            r'(?<!\\)([\{\}\|])',
            lambda m: f"{c.COLOR_COLON}{m.group(1)}{c.RESET_FORE}",
            msg
        )

        #Highlight UUID
        msg = re.sub(
            r'\b([0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})\b',
            lambda m: f"{c.COLOR_UUID}{m.group(1)}{c.RESET_FORE}",
            msg,
            flags=re.IGNORECASE
        )

        if data and not self.__config['mode'] == 'json':
            msg = self.__highlight_data(msg)
        if self.__config['mode'] == 'json' and self.__force_markup:
            msg = self.__highlight_literals_json(msg)

        return msg

    def __highlight_literals_json(self, msg: str) -> str:
        c = self.presets

        # Highlight log level terms
        level_keywords = {
            "DEBUG": c.DEBUG,
            "INFO": c.INFO,
            "WARNING": c.WARNING,
            "WARN": c.WARNING,
            "ERROR": c.ERROR,
            "CRITICAL": c.CRITICAL
        }
        for keyword, color in level_keywords.items():
            msg = re.sub(
                rf'\b{keyword}\b',
                lambda m: f"{color}{m.group(0)}{c.RESET_FORE}",
                msg,
                flags=re.IGNORECASE
            )

        # Highlight JSON-style keys (with optional whitespace before colon)
        msg = re.sub(
            r'(?P<key>"[^"]+?")(?P<colon>\s*:)',
            lambda m: f"{c.COLOR_NUMBER}{m.group('key')}{c.RESET_FORE}{c.COLOR_COLON}{m.group('colon')}{c.RESET_FORE}",
            msg
        )

        # Highlight brackets, braces, commas, colons
        msg = msg.replace('{', f"{c.COLOR_BRACE_OPEN}{{{c.RESET_FORE}")
        msg = msg.replace('}', f"{c.COLOR_BRACE_CLOSE}}}{c.RESET_FORE}")
        msg = msg.replace('(', f"{c.COLOR_PAREN_OPEN}({c.RESET_FORE}")
        msg = msg.replace(')', f"{c.COLOR_PAREN_CLOSE}){c.RESET_FORE}")
        msg = msg.replace(':', f"{c.COLOR_COLON}:{c.RESET_FORE}")
        msg = msg.replace(',', f"{c.COLOR_COMMA},{c.RESET_FORE}")

        # Brackets: only color when at line-start or line-end to avoid nested breakage
        msg = re.sub(r'(?<=\n)(\s*)\[', lambda m: f"{m.group(1)}{c.COLOR_BRACKET_OPEN}[{c.RESET_FORE}", msg)
        msg = re.sub(r'\](?=\n)', lambda m: f"{c.COLOR_BRACKET_CLOSE}]{c.RESET_FORE}", msg)

        return msg


    def __highlight_data(self, msg):
        # Match string keys (only if followed by colon)
        c = self.presets
        msg = re.sub(
            r'(?P<key>"[^"]+?")(?P<colon>\s*:)',  # `"key":` only
            lambda m: f"{c.INFO}{m.group('key')}{c.RESET_FORE}{c.COLOR_COLON}{m.group('colon')}{c.RESET_FORE}",
            msg
        )

        # Brackets, braces, parens
        msg = msg.replace('{', f"{c.COLOR_BRACE_OPEN}{{{c.RESET_FORE}")
        msg = msg.replace('}', f"{c.COLOR_BRACE_CLOSE}}}{c.RESET_FORE}")
        msg = msg.replace('(', f"{c.COLOR_PAREN_OPEN}({c.RESET_FORE}")
        msg = msg.replace(')', f"{c.COLOR_PAREN_CLOSE}){c.RESET_FORE}")
        msg = msg.replace(':', f"{c.COLOR_COLON}:{c.RESET_FORE}")
        msg = msg.replace(',', f"{c.COLOR_COMMA},{c.RESET_FORE}")

        # Brackets: only color when at line-start or line-end to avoid nested breakage
        msg = re.sub(r'(?<=\n)(\s*)\[', lambda m: f"{m.group(1)}{c.COLOR_BRACKET_OPEN}[{c.RESET_FORE}", msg)
        msg = re.sub(r'\](?=\n)', lambda m: f"{c.COLOR_BRACKET_CLOSE}]{c.RESET_FORE}", msg)
        return msg

    def __get_env_prefix(self, dimmed_color, dimmed_style, color, style) -> str:
        """Generate environment prefix for log messages."""
        meta = self.__env_metadata
        if not self.__config['color_enabled'] or self.__config['deployed'] or self.__config['mode'] == 'json':
            dimmed_color = ''
            dimmed_style = ''
            color = ''
            style = ''

        prefix = []
        verbose = self.__config['verbose']
        first_color_flag = False
        if meta.get('project', None) is not None and (self.__config['deployed'] or verbose):
            prefix.append(f"{color}{style}{meta['project'].upper()}{self.presets.RESET}")
            first_color_flag = True
        if meta.get('env', None) is not None and (self.__config['deployed'] or verbose):
            if first_color_flag:
                prefix.append(f"{dimmed_color}{dimmed_style}{meta['env'].upper()}{self.presets.RESET}")
            else:
                prefix.append(f"{color}{style}{meta['env'].upper()}{self.presets.RESET}")
        if meta.get('project_version', None) is not None and (self.__config['deployed'] or verbose):
            if first_color_flag:
                prefix.append(f"{dimmed_color}{dimmed_style}{meta['project_version']}{self.presets.RESET}")
            else:
                prefix.append(f"{color}{style}{meta['project_version']}{self.presets.RESET}")
        if meta.get('run_id', None) is not None and (self.__config['deployed'] or verbose):
            if first_color_flag:
                prefix.append(f"{dimmed_color}{dimmed_style}{meta['run_id'].upper()}{self.presets.RESET}")
            else:
                prefix.append(f"{color}{style}{meta['run_id'].upper()}{self.presets.RESET}")

        if len(prefix) > 0:
            return f' {color}{style}:{self.presets.RESET} '.join(prefix) + f" {color}{style}|{self.presets.RESET} "
        else:
            return ''

    def __get_depth(self, internal = False) -> int:
        """Get stack depth to determine log source."""
        for i, frame in enumerate(inspect.stack()):
            if frame.filename.endswith("WrenchLogger.py") or 'WrenchCL' in frame.filename or frame.filename == '<string>':
                if internal:
                    return i + 2
                else:
                    continue
            return i

    def __suggest_exception(self, args) -> Optional[str]:
        """Generate improvement suggestions for certain exceptions."""
        suggestion = None
        if not hasattr(args, '__iter__') and args is not None:
            args = [args]
        else:
            return suggestion

        for a in args:
            if isinstance(a, Exception) or isinstance(a, BaseException):
                ex = a
                if hasattr(ex, 'args') and ex.args and isinstance(ex.args[0], str):
                    suggestion = _ExceptionSuggestor.suggest_similar(ex)
                break
        return suggestion

    def __apply_color(self, text: str, color: Optional[str]) -> str:
        """Apply ANSI colors to text if color mode is enabled."""
        return f"{color}{self.presets.BRIGHT}{text}{self.presets.RESET}" if color else text

    def __check_deployment(self, log = True):
        """Detect deployment environment and adjust settings accordingly."""
        if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None:
            self.__config['color_enabled'] = False
            self.__config['deployed'] = True
            self.disable_color()
            if log:
                self._internal_log("Detected Lambda deployment. Set color mode to False.")
            self.__config['mode'] = 'json'

        if os.environ.get("AWS_EXECUTION_ENV") is not None:
            self.__config['color_enabled'] = False
            self.__config['deployed'] = True
            self.disable_color()
            if log:
                self._internal_log("Detected AWS deployment. Set color mode to False.")
            self.__config['mode'] = 'json'

        if os.environ.get("COLOR_MODE") is not None:
            if os.environ.get("COLOR_MODE").lower() == "false":
                self.__config['color_enabled'] = False
            else:
                self.__config['color_enabled'] = True

        if os.environ.get("LOG_DD_TRACE") is not None:
            val = os.environ.get("LOG_DD_TRACE", "false").lower()
            self.__config['dd_trace_enabled'] = val == "true"
            state = "enabled" if self.__config['dd_trace_enabled'] else "disabled"
            if log:
                self._internal_log(f"LOG_DD_TRACE detected — Datadog tracing {state}. | Mode Json")
            if self.__config['dd_trace_enabled']:
                self.__config['mode'] = 'json'

    def __fetch_env_metadata(self) -> dict:
        """
        Extract environment metadata from system environment variables.
        """
        env_vars = {
            "env": os.getenv("ENV") or os.getenv('DD_ENV') or os.getenv("AWS_EXECUTION_ENV") or None,
            "project": os.getenv("PROJECT_NAME") or os.getenv('COMPOSE_PROJECT_NAME') or os.getenv("AWS_LAMBDA_FUNCTION_NAME") or None,
            "project_version": os.getenv("PROJECT_VERSION") or os.getenv("LAMBDA_TASK_ROOT") or os.getenv('REPO_VERSION') or None,
            "run_id": self.run_id
        }
        return env_vars

    def __setup(self) -> None:
        """Initialize the logger with basic configuration."""
        with self.__lock:
            if self.__initialized:
                self._internal_log("Logger already initialized. Skipping setup.")
                return

            self.flush_handlers()
            self.__logger_instance.setLevel(self.__base_level)
            self.add_new_handler(logging.StreamHandler, stream=sys.stdout, force_replace=True)
            self.__logger_instance.propagate = False
            self.__initialized = True

    def __check_color(self) -> None:
        """
        Check if color output is available and configure accordingly.
        """
        if self.__config['color_enabled']:
            try:
                self.enable_color()
                return
            except ImportError:
                self._internal_log("Color mode not available. Disabling.")
                pass
        self.disable_color()

    def __use_json_logging(self):
        """
        Configure the logger for JSON-structured output.
        """
        formatter = _JSONLogFormatter(self.__env_metadata, self.__force_markup, self.__highlight_literals)

        if not self.__logger_instance.handlers:
            self.add_new_handler(logging.StreamHandler, stream=sys.stdout, formatter=formatter, force_replace=True)
        else:
            self.flush_handlers()
            for i, handler in enumerate(self.__logger_instance.handlers):
                if not hasattr(getattr(handler, "stream", None), "write"):
                    self.__logger_instance.handlers[i] = self.add_new_handler(
                        logging.StreamHandler,
                        stream=sys.stdout,
                        formatter=formatter,
                        force_replace=False,
                    )
                else:
                    handler.setFormatter(formatter)

    def __log_setup_summary(self) -> None:
        """Log a summary of the current logger configuration."""
        if self.__config["mode"] == "json":
            self._internal_log(json.dumps(self.__config, indent=2, default=str))
            return

        settings = self.logger_state
        msg = '⚙️  Logger Configuration:\n'

        msg += f"  • Logging Level: {self.__apply_color(settings['Logging Level'], self.presets.get_color_by_level(settings['Logging Level']))}\n"
        msg += f"  • Mode: {settings['Mode']}\n"
        msg += f"  • Run ID: {settings['Run Id']}\n"

        msg += "  • Configuration:\n"
        for mode, enabled in settings["Configuration"].items():
            state = enabled
            msg += f"      - {mode:30s}: {state}\n"

        self._internal_log(msg)


    @staticmethod
    def __generate_run_id() -> str:
        """Generate a unique run ID for this logger instance."""
        now = datetime.now()
        return f"R-{os.urandom(1).hex().upper()}{now.strftime('%m%d')}{os.urandom(1).hex().upper()}"

    def __get_level(self, level: Union[str, int]) -> int:
        """Convert a level name to its numeric value."""
        if isinstance(level, str) and hasattr(logging, level.upper()):
            return getattr(logging, level.upper())
        elif isinstance(level, int):
            return level
        elif level == 'INTERNAL':
            return logging.DEBUG
        return logging.INFO

    def __get_formatter(self, level: Union[str, int], no_format=False) -> logging.Formatter:
        """Get the appropriate formatter based on log level and mode."""

        if self.__config['mode'] == 'json' and level != 'INTERNAL':
            return _JSONLogFormatter(self.__env_metadata, self.__force_markup, self.__highlight_literals)

        color = self.presets.get_color_by_level(level)
        style = self.presets.get_level_style(level)
        message_color = self.presets.get_message_color(level)

        if isinstance(level, int):
            str_name = logging.getLevelName(level)
        else:
            str_name = level.upper()

        if str_name in ['ERROR', 'CRITICAL', 'WARNING']:
            dimmed_color = self.presets.get_color_by_level(level)
        else:
            dimmed_color = self.presets.get_color_by_level('INTERNAL')

        dimmed_style = self.presets.get_level_style('INTERNAL')

        if level == 'INTERNAL':
            color = self.presets.CRITICAL
            style = self.presets.get_level_style('INTERNAL')


        file_section = f"{dimmed_color}{dimmed_style}%(filename)s:%(funcName)s:%(lineno)d]{self.presets.RESET}"
        verbose_section = f"{dimmed_color}{dimmed_style}[%(asctime)s|{file_section}{self.presets.RESET}"
        app_env_section = self.__get_env_prefix(dimmed_color, dimmed_style, color, style)
        level_name_section = f"{color}{style}%(levelname)-8s{self.presets.RESET}"
        colored_arrow_section = f"{color}{style} -> {self.presets.RESET}"
        message_section = f"{style}{message_color}%(message)s{self.presets.RESET}"

        if self.__global_stream_configured:
            name_section = f"{color}{style}[%(name)s] - {self.presets.RESET}"
        else:
            name_section = f""

        if level == "INTERNAL":
            level_name_section = f"{color}{style}  WrenchCLInternal{self.presets.RESET}"
        elif level == "DATA":
            level_name_section = f"{color}{style}DATA    {self.presets.RESET}"

        if self.__config['mode'] == 'compact':
            fmt = f"{level_name_section}{file_section}{colored_arrow_section}{message_section}"
        elif no_format:
            fmt = "%(message)s"
        if level == 'INTERNAL':
            fmt = f"{level_name_section}{colored_arrow_section}{message_section}"
        else:
            fmt = f"{app_env_section}{name_section}{level_name_section}{verbose_section}{colored_arrow_section}{message_section}"

        fmt = f"{self.presets.RESET}{fmt}{self.presets.RESET}"

        return _CustomFormatter(fmt, datefmt='%H:%M:%S', presets=self.presets)

    # ---------------- Aliases/Shortcuts ----------------

    def data(self, data, **kwargs):
        """
        Formats and logs the given data and additional keyword arguments.

        This method is responsible for processing input data and additional
        keyword arguments, formatting them appropriately, and logging
        the formatted result. It delegates the operation to the `pretty_log`
        method, ensuring the data is displayed in a well-structured format.

        :param data: The input data to be logged.
        :type data: Any
        :param kwargs: Additional keyword arguments passed to the logging operation.
        :type kwargs: dict
        :return: The result of the `pretty_log` method after formatting and logging the input.
        :rtype: Any
        """
        return self.pretty_log(data, **kwargs)


@SingletonClass
class _logger_(_BaseLogger):
    __doc__ = """Singleton thread-safe instance of BaseLogger.""" + _BaseLogger.__doc__

    def __init__(self):
        super().__init__()

    @property
    def baseClass(self) -> Type[_BaseLogger]:
        "Returns the base class of this instance."
        return _BaseLogger

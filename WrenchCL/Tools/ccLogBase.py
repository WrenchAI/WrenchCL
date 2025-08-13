import contextvars
import importlib
import inspect
import json
import logging
import os
import re
import sys
import threading
import time
import warnings
from contextlib import contextmanager
from contextvars import Context
from dataclasses import dataclass
from datetime import datetime
from difflib import get_close_matches
from enum import Enum
from io import TextIOBase
from logging import Handler
from pprint import pformat
from types import TracebackType
from typing import Any, Optional, Union, Literal, Type, Callable, List

from WrenchCL.Decorators.SingletonClass import SingletonClass
from WrenchCL._Internal._MockPandas import _MockPandas
from WrenchCL._Internal.require_module import gate_imports

try:
    import pandas as pd
except ImportError:
    pd = _MockPandas()

_exc_info_type = None | bool | tuple[Type[BaseException], BaseException, TracebackType | None] | tuple[
    None, None, None] | BaseException

class LogLevel(str, Enum):
    """
    Defines LogLevel, an enumeration for logging levels.

    The LogLevel class provides a specialized enumeration type for different logging
    levels, supporting standard, alias, and mapped values. It also provides convenient
    methods for resolving string and integer representations of log levels and for
    mapping custom aliases to specific log levels.

    :ivar DEBUG: Represents the DEBUG logging level.
    :type DEBUG: str
    :ivar INFO: Represents the INFO logging level.
    :type INFO: str
    :ivar WARNING: Represents the WARNING logging level.
    :type WARNING: str
    :ivar ERROR: Represents the ERROR logging level.
    :type ERROR: str
    :ivar CRITICAL: Represents the CRITICAL logging level.
    :type CRITICAL: str
    """
    DEBUG = "DEBUG"  # noqa
    INFO = "INFO"  # noqa
    WARNING = "WARNING"  # noqa
    ERROR = "ERROR"  # noqa
    CRITICAL = "CRITICAL"  # noqa

    __aMap__: dict[str, str] = {
        "WARN": "WARNING",
        "ERR": "ERROR",
        "CRI": "CRITICAL",
        "INTERNAL": "INTERNAL",
        "DATA": "DATA",
        "HEADER": "HEADER"
    }

    __byMap__: dict[str, str] = {"INTERNAL": "INFO", "DATA": "INFO", "HEADER": "INFO"}

    @classmethod
    def _missing_(cls, value: Union[str, int]):
        if value is None:
            return None
        if issubclass(type(value), Enum):
            value = value.value
        if isinstance(value, int):
            value = logging.getLevelName(value)
        value = str(value).upper()
        alias = cls.__aMap__.get(value, value)  # noqa

        if alias in cls.__byMap__:
            obj = str.__new__(cls, alias)
            obj._name_ = alias
            obj._value_ = alias
            return obj

        if alias in cls._value2member_map_:
            return cls._value2member_map_[alias]

        raise ValueError(f"Invalid log level: {value} (allowed: {[e for e in cls]})")

    def __int__(self) -> int:
        return getattr(logging, self.__byMap__.get(self.value, self.value)) # noqa

logLevels = Union[int, str, LogLevel]
"""
Represents a log level input accepted across the logging system.

Accepted Forms:

- int: Standard Python log levels (e.g., 10, 20, logging.WARNING)
- str: Case-insensitive log level names (see below)

Standard Levels:

- "DEBUG"

- "INFO"

- "WARNING"

- "ERROR"

- "CRITICAL"

Alias Str Inputs (automatically normalized):

- "WARN": "WARNING"

- "ERR": "ERROR"

- "CRI": "CRITICAL"
"""

@dataclass
class LoggerConfig:
    mode: str = 'terminal'              # 'terminal', 'json', or 'compact'
    highlight_syntax: bool = True
    verbose: bool = False
    deployed: bool = False
    dd_trace_enabled: bool = False
    color_enabled: bool = True

@dataclass
class LogOptions:
    """Configuration options for logging behavior and formatting."""
    no_format: bool = False
    no_color: bool = False
    stack_info: bool = False

    def __new__(cls, opts=None):
        """Create LogOptions from dict, LogOptions instance, or None."""
        if opts is None:
            return super().__new__(cls)
        elif isinstance(opts, dict):
            return super().__new__(cls)
        elif isinstance(opts, LogOptions):
            return opts
        else:
            raise TypeError(f"LogOptions expects dict, LogOptions, or None, got {type(opts)}")

    def __init__(self, opts=None, no_format=False, no_color=False, stack_info=False):
        if isinstance(opts, dict):
            self.no_format = opts.get('no_format', no_format)
            self.no_color = opts.get('no_color', no_color)
            self.stack_info = opts.get('stack_info', stack_info)
        elif opts is None:
            self.no_format = no_format
            self.no_color = no_color
            self.stack_info = stack_info

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
    DATA = None
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
    COLOR_KEY = None

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
        super().__setattr__('DATA', getattr(self._color_class, 'BLUE', ''))

        super().__setattr__('BRIGHT', getattr(self._style_class, 'BRIGHT', ''))
        super().__setattr__('NORMAL', getattr(self._style_class, 'NORMAL', ''))
        super().__setattr__('RESET', getattr(self._style_class, 'RESET_ALL', ''))
        super().__setattr__("RESET_FORE", getattr(self._color_class, 'RESET', ''))

        # Literal colors
        super().__setattr__('COLOR_TRUE', getattr(self._color_class, 'GREEN', ''))
        super().__setattr__('COLOR_FALSE', getattr(self._color_class, 'RED', ''))
        super().__setattr__('COLOR_NONE', getattr(self._color_class, 'WHITE', ''))
        super().__setattr__('COLOR_NUMBER', getattr(self._color_class, 'YELLOW', ''))
        super().__setattr__('COLOR_UUID', getattr(self._color_class, 'BLUE', ''))
        super().__setattr__('COLOR_KEY', getattr(self._color_class, 'BLUE', ''))

        # Syntax colors
        super().__setattr__('COLOR_BRACE_OPEN', getattr(self._color_class, 'CYAN', ''))     # {
        super().__setattr__('COLOR_BRACE_CLOSE', getattr(self._color_class, 'CYAN', ''))    # }
        super().__setattr__('COLOR_BRACKET_OPEN', getattr(self._color_class, 'CYAN', ''))      # [
        super().__setattr__('COLOR_BRACKET_CLOSE', getattr(self._color_class, 'CYAN', ''))     # ]
        super().__setattr__('COLOR_PAREN_OPEN', getattr(self._color_class, 'CYAN', ''))        # (
        super().__setattr__('COLOR_PAREN_CLOSE', getattr(self._color_class, 'CYAN', ''))       # )
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

    def get_color_by_level(self, level: logLevels):
        level = LogLevel(level)
        if level == 'INTERNAL':
            return self._INTERNAL_DIM_COLOR
        return getattr(self, level, '')


    def get_level_style(self, level: logLevels):
        level = LogLevel(level)
        if level in ['INFO', 'DEBUG']:
            return self.NORMAL
        elif level in ['WARNING', 'ERROR', 'CRITICAL', 'HEADER']:
            return self.BRIGHT
        elif level == 'INTERNAL':
            return self._INTERNAL_DIM_STYLE
        else:
            return self.NORMAL

    def get_message_color(self, level: logLevels):
        level = LogLevel(level)
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
    def __init__(self, env_metadata: dict, forced_color: bool, highlight_func: Callable, traced: bool = False, deployed: bool = False):
        super().__init__()
        self.env_metadata = env_metadata
        self.color_mode = forced_color
        self.highlight_func = highlight_func
        self.traced = traced
        self.deployed = deployed

    @staticmethod
    def _extract_generic_context(metadata: Optional[dict] = None) -> dict:
        """
        Extract known context values (user_id, organization_id, service_name) from:
        - os.environ
        - contextvars
        - deeply nested dicts or object trees (with cycle protection & depth limit)
        """
        context_data: dict = {}

        user_keys = {
            "user_id", "usr_id", "entity_id", "user_entity_id", "subject_id",
            "client_id", "user_name", "username",
        }
        org_keys = {
            "client_id", "org_id", "organization_id", "tenant_id",
            "team_id", "workspace_id", "project_id",
        }
        service_keys = {
            "service_id", "service_name", "application", "app_name", "dd_service",
            "aws_function_name", "aws_service", "lambda_name", "lambda_function",
            "aws_function", "project_name", "project",
        }

        # Prevent infinite recursion on cyclic structures; keep traversal shallow.
        MAX_DEPTH = 4
        seen: set[int] = set()

        def check_keys(key: str, value: object, depth: int) -> dict:
            result: dict = {}
            if not isinstance(key, str):
                try:
                    key = str(key)
                except Exception:
                    key = ""
            k = key.lower()

            if k in user_keys:
                result["user_id"] = value
            elif k in org_keys:
                result["organization_id"] = value
            elif k in service_keys:
                result["service_name"] = value

            if depth >= MAX_DEPTH:
                return result

            try:
                if isinstance(value, dict):
                    oid = id(value)
                    if oid in seen:
                        return result
                    seen.add(oid)
                    result.update(scan_dict(value, depth + 1))
                elif hasattr(value, "__dict__"):
                    oid = id(value)
                    if oid in seen:
                        return result
                    seen.add(oid)
                    try:
                        result.update(scan_dict(vars(value), depth + 1))
                    except Exception:
                        pass
            except Exception:
                pass

            return result

        def scan_dict(data: dict, depth: int) -> dict:
            found: dict = {}
            try:
                items = data.items()
            except Exception:
                return found
            for k, v in items:
                found.update(check_keys(k, v, depth))
            return found

        def scan_ctx(ctx: "Context") -> dict:
            found: dict = {}
            try:
                for var in ctx:
                    try:
                        value = ctx.get(var)
                    except Exception:
                        continue
                    found.update(check_keys(var.name, value, depth=0))
            except Exception:
                pass
            return found

        context_data.update(scan_ctx(contextvars.copy_context()))
        return context_data


    def format(self, record: logging.LogRecord) -> str:
        ctx = {}
        dd = {
            "dd.env": self.env_metadata.get("env"),
            "dd.service": self.env_metadata.get("project") or ctx.get('service_name'),
            "dd.version": self.env_metadata.get("project_version")
        }
        ctx.update(self._extract_generic_context())

        if self.traced:
            dd.update({
            "dd.trace_id": str(getattr(record, "dd.trace_id")),
            "dd.span_id": str(getattr(record, "dd.span_id"))})

        log_record = {
            "level": record.levelname,
            "message": record.getMessage(),
            "source" : {
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            },
            "log_info": {
                "logger": record.name,
                "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            }
        }

        if dd:
            log_record['trace'] = dd
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        if len(ctx) > 0:
            log_record['context'] = ctx

        if self.deployed:
            dumped_json = json.dumps(log_record, default=str, ensure_ascii=False)
        else:
            dumped_json = json.dumps(log_record, default=str, ensure_ascii=False, indent=2)

        if self.color_mode is True and not self.deployed:
            dumped_json = self.highlight_func(dumped_json)

        return dumped_json


# noinspection PyUnusedFunction,PySameParameterValue
@SingletonClass
class ccLogBase:
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
        # Thread safety lock
        self._Style = None
        self._Color = None
        self.__lock = threading.RLock()
        self.__logger_instance = logging.getLogger('WrenchCL')
        # Basic logger state
        self.__global_stream_configured = False
        self.__force_markup = False
        self.__initialized = False
        self.run_id = self.__generate_run_id()
        self.__base_level = 'INFO'

        # Mode flags (simplified to a single dictionary)
        self.__config = LoggerConfig()

        # Initialize objects
        self.__start_time = None
        self.__dd_log_flag = False
        self.presets = ColorPresets(None, None)
        self.__env_metadata = self.__fetch_env_metadata()
        self.__strip_ansi_fn: Optional[Callable] = None

        # Read environment variables
        self.__config.dd_trace_enabled = os.environ.get("LOG_DD_TRACE", "false").lower() == "true"
        self.__config.color_enabled = os.environ.get("COLOR_MODE", "true").lower() == "true"
        self.__from_context = False
        # Set up logger instance
        self.__setup()
        self.reinitialize()
        self._internal_log(f"Logger -> Color:{self.__config.color_enabled} | Mode:{self.__config.mode.capitalize()} | Deployment:{self.__config.deployed}")

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

        with self.__lock:
            if not suppress_autoconfig:
                self.__check_deployment()
            if mode is not None:
                self.__config.mode = mode
                if mode == 'json':
                    # Backup Fallback for json deployment mode (can be overridden)
                    self.__config.deployed = True
            if highlight_syntax is not None:
                self.__config.highlight_syntax = highlight_syntax
            if level is not None:
                self.setLevel(level)
            if color_enabled is not None:
                self.__config.color_enabled = color_enabled
            if verbose is not None:
                self.__config.verbose = verbose
            if deployment_mode is not None:
                self.__config.deployed = deployment_mode
            if trace_enabled is not None:
                self.__config.dd_trace_enabled = trace_enabled
                try:
                    import ddtrace # noqa
                    ddtrace.patch(logging=True)
                    self._internal_log("Datadog trace injection enabled via ddtrace.patch(logging=True)")
                    os.environ["DD_TRACE_ENABLED"] = "true"
                except ImportError:
                    self.__config.dd_trace_enabled = False
                    gate_imports(True, 'trace', 'ddtrace', False)
            if self.__config.dd_trace_enabled and self.__config.mode != 'json':
                self._internal_log("   Trace injection requested, but trace_id/span_id only appear in JSON mode.")
            self.__check_color()
            self.__env_metadata = self.__fetch_env_metadata()

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
            self.flush_handlers()
            self.__logger_instance.setLevel(int(level))

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

        self.__log(level="INFO", args=args, no_format=opts.no_format, no_color=opts.no_color, stack_info=opts.stack_info, header=header)

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

        self.__log(level="DEBUG", args=args, no_format=opts.no_format, no_color=opts.no_color, stack_info=opts.stack_info)

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
        :param exc_info: [DEPRECATED] Exception context. Raw exceptions in args are auto-detected.
        :param header: Optional text to prepend as a stylized header.
        :param log_opts: Logging options (no_format, no_color, stack_info). Can be LogOptions instance or dict.
        """
        opts = LogOptions(log_opts)
        if isinstance(kwargs.get('exc_info', ''), (Exception, BaseException)):
            args = args + (kwargs.get('exc_info'),)

        self.__log(level="WARNING", args=args, no_format=opts.no_format, no_color=opts.no_color, stack_info=opts.stack_info, header=header)

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

        self.__log(level="ERROR", args=args, no_format=log_opts.no_format, no_color=log_opts.no_color, stack_info=log_opts.stack_info, header=header)

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

        self.__log(level="CRITICAL", args=args, no_format=log_opts.no_format, no_color=log_opts.no_color, stack_info=log_opts.stack_info, header=header)

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

        self.__log(level="ERROR", args=args, no_format=opts.no_format, no_color=opts.no_color, stack_info=opts.stack_info, header=header)

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
        :return: The formatted header string if `repr` is True, otherwise None.
        :rtype: Optional[str]
        """

        if not level:
            level = 'HEADER'
        compact = compact or self.__config.mode == 'compact'
        level = LogLevel(level)
        color = self.presets.get_color_by_level(level)
        text = text.replace('_', ' ').replace('-', ' ').strip().upper()
        char = self.__get_safe_char("─", '-')
        size = size or (40 if compact else 80)
        formatted = f"{self.presets.RESET}"+ self.__apply_color(text, color).center(size, char)
        if not compact:
            formatted = f"\n" + formatted
        if not return_repr:
            self.__log("HEADER", args=(formatted,), no_format=True, no_color=True)
        else:
            return formatted

    def __pretty_log(self, obj: Any, indent=2, compact: bool = False, **kwargs) -> None:
        """
        Logs a given object in a visually formatted manner.

        :param obj: Object to log.
        :param indent: Indentation for JSON formatting.
        :param compact: If True, uses pprint for more compact array formatting.
        :param kwargs: Passed to json.dumps or model_dump_json
        """
        obj = self.__ensure_str(obj)
        output = obj
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
                if not self.__config.mode == 'json':
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
            if self.__config.mode == 'json' and isinstance(output, str):
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
        with self.__lock:
            if not level:
                level = self.__base_level
            if issubclass(handler_cls, logging.StreamHandler):
                if stream is None:
                    raise ValueError("StreamHandler requires a valid `stream` argument.")
                handler = handler_cls(stream) # noqa
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

    class __FileLogFormatter(logging.Formatter):
        def __init__(self, base_formatter: logging.Formatter):
            super().__init__(base_formatter._fmt, base_formatter.datefmt)
            self._base_formatter = base_formatter

        def format(self, record: logging.LogRecord) -> str:
            raw = self._base_formatter.format(record)
            return ccLogBase._remove_ansi_codes(raw)

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
        from logging.handlers import RotatingFileHandler

        with self.__lock:
            handler = RotatingFileHandler(
                filename=filename,
                maxBytes=max_bytes,
                backupCount=backup_count,
                delay=True,
                encoding="utf-8"  # Ensures proper handling of non-ASCII characters
            )
            level = level or self.__base_level
            handler.setLevel(level)

            # Use ANSI-stripping formatter if none provided
            handler.setFormatter(formatter or self.__FileLogFormatter(self.__get_formatter(level)))

            self.__logger_instance.addHandler(handler)
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
        with self.__lock:
            self.flush_handlers()
            root_logger = logging.getLogger()
            root_logger.setLevel(level or self.__base_level)

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
            # Diagnostic output
            active_loggers = [
                name for name in logging.root.manager.loggerDict
                if isinstance(logging.getLogger(name), logging.Logger)
            ]
            handler_count = len(root_logger.handlers)
            root_loggers = sorted({v.split('.')[0] for v in active_loggers})
            if len(root_loggers) > 10:
                joined_loggers = ', '.join(root_loggers[:10]) + f'...<{len(root_loggers) - 10} more>'
            else:
                joined_loggers = ', '.join(root_loggers)

            self._internal_log(
                f"✅ Global stream attached to root logger with {handler_count} handler(s).\n"
                f"🔎 Active loggers detected: {len(active_loggers)}\n"
                f"📝 Accessible root loggers: {joined_loggers}"
                f"---Get a full list of active loggers with `active_loggers` property---"
            )

        # Log outside the lock
        self._internal_log(" Global stream configured successfully.")

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
        level = LogLevel(level)
        with self.__lock:
            loggers = logging.root.manager.loggerDict
            name_map = {name.lower(): name for name in loggers}
            normalized_name = logger_name.lower()
            if normalized_name not in name_map:
                log_string = f"⚠️ Logger '{logger_name}' not found (case-insensitive match). "
                matches = get_close_matches(normalized_name, name_map, n=1, cutoff=0.6)
                if matches:
                    log_string += f"\n Did you mean '{matches[0]}'?"
                else:
                    log_string += f"\nAvailable loggers: {', '.join(sorted(loggers.keys()))}"
                self._internal_log(log_string)
                return

            actual_name = name_map[normalized_name]
            logger = logging.getLogger(actual_name)
            logger.setLevel(int(level))

            if int(level) > logging.CRITICAL:
                logger.handlers = [logging.NullHandler()]
                logger.propagate = False
                self._internal_log(f"🔇 Logger '{actual_name}' silenced (level={level})")
            else:
                logger.propagate = True
                self._internal_log(f"🔧 Logger '{actual_name}' set to level {level}")

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
        if not level:
            level = self.__base_level
        level = LogLevel(level)
        if handler_name in self.attached_loggers:
            for h in self.logger_instance.handlers:
                if h.name == handler_name:
                    h.setLevel(int(level))
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
        level = logging.CRITICAL
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
                if self.__force_markup and self.__config.deployed:
                    warnings.warn("Forcing Markup in deployment mode is not recommended and will cause issues in external parsers like cloudwatch and Datadog", category=RuntimeWarning, stacklevel=5)
                # Update color presets and reconfigure formatters
                self.presets = ColorPresets(self._Color, self._Style)
                self.flush_handlers()
                if self.__config.mode == 'json':
                    self.__use_json_logging()
                else:
                    for handler in self.__logger_instance.handlers:
                        handler.setFormatter(self.__get_formatter(logging.getLevelName(self.__logger_instance.level)))

                if self.__global_stream_configured:
                    root_logger = logging.getLogger()
                    for handler in root_logger.handlers:
                        handler.setFormatter(self.__get_formatter(logging.getLevelName(root_logger.level)))

            self._internal_log("Forced color output enabled.")
        except ImportError:
            gate_imports(True, "color", 'colorama', False)
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
                self.__config.color_enabled = True
                self.__config.highlight_syntax = True if self.__config.highlight_syntax is not False else False
                self._Color = colorama.Fore
                self._Style = colorama.Style
                self.presets = ColorPresets(self._Color, self._Style)
                colorama.deinit()
                colorama.init(strip=False, autoreset=False)
        except ImportError:
            gate_imports(True, "color", 'colorama', False)
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
            self.__config.color_enabled = False
            self.__config.highlight_syntax = False
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
        with self.__lock:
            self.__from_context = True
            original_values = {}

            # Handle level separately
            if level is not None:
                original_values['level'] = self.level
                self.setLevel(LogLevel(level))

            # Save existing config values
            if mode is not None:
                original_values['mode'] = self.__config.mode
                if mode == 'json' and deployed is None:
                    deployed = True
            if color_enabled is not None:
                original_values['color_enabled'] = self.__config.color_enabled
            if verbose is not None:
                original_values['verbose'] = self.__config.verbose
            if trace_enabled is not None:
                original_values['dd_trace_enabled'] = self.__config.dd_trace_enabled
            if highlight_syntax is not None:
                original_values['highlight_syntax'] = self.__config.highlight_syntax
            if deployed is not None:
                original_values['deployed'] = self.__config.deployed

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
                    self.setLevel(LogLevel(original_values['level']))

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
            active_loggers = [
                    name for name in logging.root.manager.loggerDict
                    if isinstance(logging.getLogger(name), logging.Logger)
            ]
            return active_loggers

    @property
    def mode(self) -> str:
        """
        Gets the value of the 'mode' configuration.

        This property retrieves the 'mode' setting from the internal configuration
        dictionary. If the 'mode' key is not present, it defaults to 'terminal'.

        :return: The current mode setting from the configuration.
        :rtype: str
        """
        return self.__config.mode

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
        return {
            "Logging Level": self.level.value,
            "Run Id": self.run_id,
            "Mode": self.__config.mode,
            "Environment Metadata": self.__env_metadata,
            "Configuration": {
                "Color Enabled": self.__config.color_enabled,
                "Highlight Syntax": self.__config.highlight_syntax,
                "Verbose": self.__config.verbose,
                "Deployment Mode": self.__config.deployed,
                "DD Trace Enabled": self.__config.dd_trace_enabled,
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
        return self.__config.highlight_syntax

    # ---------------- Internals ----------------

    def __log(self, level: Union[LogLevel, logLevels], args,
            no_format: bool =False, no_color: bool =False, stack_info: bool =False, header: Optional[str] = None) -> None:
        """Thread-safe logging implementation.
        :param no_format:
        :param no_color:
        :param stack_info:
        :param header:
        """
        if not isinstance(level, LogLevel):
            level = LogLevel(level)
        
        markup_flag = (
            self.__config.highlight_syntax
            and self.__config.color_enabled
            and not no_color
            and not (self.__force_markup and self.__config.mode == 'json')
        )
    
        single_line_flag = self.__config.mode in ('compact',) or self.__config.deployed
    
        # Convert args to list and process them
        args = list(args)
        args = [self.__ensure_str(arg) for arg in args if arg is not None]
        
        # Extract exceptions from args
        exc_info = None
        for idx, a in enumerate(args):
            if isinstance(a, (Exception, BaseException)):
                exc_info = args.pop(idx)
                break
    
        if self.__config.mode == 'terminal':
            suggestion = self.__suggest_exception(exc_info)
            if suggestion:
                args.append(suggestion)
    
        args = tuple(args)
        # This will strip ansi codes so no formatting before this!
        msg = '\n'.join(str(arg) for arg in args)
        if markup_flag:
            msg = self.__highlight_literals(msg)
    
        if header and markup_flag:
            header_str = self.header(header, level=level, compact=True, return_repr=True)
            msg = f"{header_str}\n{msg}"
    
        if not no_format:
            if single_line_flag:
                lines = msg.splitlines()
                msg = ' '.join([line.strip() for line in lines if len(line.strip()) > 0])
                msg = msg.replace('\n', ' ').replace('\r', '').strip()
            elif exc_info or level == 'DATA':
                msg = self.__add_data_markers(msg, level, True)
        
        if level not in ['ERROR', 'CRITICAL']:
            exc_info = None
    
        # Use lock for handler configuration
        with self.__lock:
            self.flush_handlers()
            for handler in self.__logger_instance.handlers:
                if not isinstance(handler, logging.NullHandler):
                    handler.setFormatter(self.__get_formatter(
                        level,
                        no_format=no_format,
                        no_color=no_color
                    ))
    
        if not no_format:
            if len(msg.strip().splitlines()) > 1 and not msg.startswith('\n'):
                msg = '\n' + msg
        
        # Actual logging outside the lock to prevent deadlocks
        self.__logger_instance.log(
            int(level),
            msg,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=self.__get_depth(internal=level == 'INTERNAL')
        )

    @staticmethod
    def __ensure_str(val: bytes | str) -> str:
        return val.decode("utf-8") if isinstance(val, bytes) else val

    def __add_data_markers(self, msg: str, level: LogLevel, head = False) -> str:
        if len(msg.strip().splitlines()) <= 1:
            return msg

        is_data = level == "DATA"
        header = head and not is_data
        color = self.presets.get_color_by_level(level)
        style = self.presets.get_level_style(level)
        reset = self.presets.RESET

        indent_size = 4
        pad = ' ' * indent_size
        lines = msg.splitlines(keepends=True)
        content_width = max(len(self._remove_ansi_codes(line.strip())) for line in lines)

        total_width = content_width + (indent_size * 2)

        arm_len = min(indent_size * 10, max(1, content_width // 2))
        bar_len = total_width - arm_len

        def get_spacer(word: str, length: int, char:str = '─') -> str:
            if not char:
                char = self.__get_safe_char('─')
            if len(word) >= length:
                return char * length

            length = (length - len(word)) // 2
            return char * length + word + char * length

        top_bar = (self.__get_safe_char('─') * total_width)
        bot_bar = (self.__get_safe_char('─') * total_width)
        right_corner = self.__get_safe_char('┐')
        left_corner = self.__get_safe_char('└')
        markup = f"{color}{style}"

        if is_data:
            top_bar = get_spacer("DATA", arm_len) + ' ' * bar_len
            bot_bar = ' ' * bar_len + get_spacer("END", arm_len)
            right_corner = ' '
            left_corner = ' '
        elif header:
            top_bar = get_spacer(level, total_width)

        top_border = f"{reset}{markup}{self.__get_safe_char('┌')}{top_bar}{right_corner}"
        if is_data:
            top_border = f"{markup}{self.__get_safe_char('┌')}{top_bar}{right_corner}{reset}"
        bottom_border = f"{markup}{left_corner}{bot_bar}{self.__get_safe_char('┘')}{reset}"


        content = ''.join(f"{pad}{line}" for line in lines)
        if not content.endswith('\n'):
            content += '\n'
        if not content.startswith('\n'):
            content = '\n' + content

        return top_border + content + bottom_border


    def _remove_ansi_codes(self, text: str) -> str:
        """
        Remove ANSI escape sequences from the input string.
        """
        if not self.__strip_ansi_fn:
            self.__set_ansi_fn()
        try:
            from ftfy import fix_text
            text = fix_text(text)
        except:
            pass
        return self.__strip_ansi_fn(text)

    def __set_ansi_fn(self):
        try:
            from ansi2txt import Ansi2Text
            _ansi = Ansi2Text()
            def _strip_ansi(text: str) -> str:
                return _ansi.convert(text)
        except Exception:
            _ansi_re = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            def _strip_ansi(text: str) -> str:
                return _ansi_re.sub('', text)
        finally:
            self.__strip_ansi_fn = _strip_ansi

    def __highlight_literals(self, msg: str) -> str:
        msg = self._remove_ansi_codes(msg)
        if not self.__force_markup and (
            not self.__config.color_enabled
            or not self.__config.highlight_syntax
            or self.__config.deployed
        ):
            return msg

        c = self.presets

        # Highlight numbers
        msg = re.sub(r'(?<![\w-])(\d+(?:\.\d+)?[a-zA-Z%]*)\b',
                     lambda m: f"{c.COLOR_NUMBER}{m.group(1)}{c.RESET_FORE}", msg)

        # Highlight UUIDs
        msg = re.sub(
            r'\b([0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})\b',
            lambda m: f"{c.COLOR_UUID}{m.group(1)}{c.RESET_FORE}",
            msg, flags=re.IGNORECASE)

        # Highlight placeholders like %s or %{name}s
        msg = re.sub(r'%\{?[a-zA-Z0-9_]*s}?\b',
                     lambda m: f"{c.COLOR_COLON}{m.group(0)}{c.RESET_FORE}", msg)

        # Highlight square brackets (at line start/end only)
        msg = re.sub(r'(?<=\n)(\s*)\[', lambda m: f"{m.group(1)}{c.COLOR_BRACKET_OPEN}[{c.RESET_FORE}", msg)
        msg = re.sub(r'](?=\n)', lambda m: f"{c.COLOR_BRACKET_CLOSE}]{c.RESET_FORE}", msg)

        # Highlight braces, parens, pipes
        msg = re.sub(r'(?<!\\)([{}|])', lambda m: f"{c.COLOR_COLON}{m.group(1)}{c.RESET_FORE}", msg)

        # Highlight literals: true, false, null, none, nan
        msg = re.sub(r'\b(true|false|null|none|nan)\b', lambda m: {
            "true": f"{c.COLOR_TRUE}{m.group(0)}{c.RESET_FORE}",
            "false": f"{c.COLOR_FALSE}{m.group(0)}{c.RESET_FORE}",
            "null": f"{c.COLOR_NONE}{m.group(0)}{c.RESET_FORE}",
            "none": f"{c.COLOR_NONE}{m.group(0)}{c.RESET_FORE}",
            "nan": f"{c.COLOR_NONE}{m.group(0)}{c.RESET_FORE}"
        }[m.group(0).lower()], msg, flags=re.IGNORECASE)

        if self.__config.mode != 'json':
            msg = self.__highlight_data(msg)
        elif self.__config.mode == 'json' and not self.__config.deployed:
             msg = self.__highlight_literals_json(msg)
        return msg


    def __highlight_literals_json(self, msg: str) -> str:
        c = self.presets

        # Highlight log levels
        level_keywords = {
            "DEBUG": c.DEBUG, "INFO": c.INFO, "WARNING": c.WARNING,
            "WARN": c.WARNING, "ERROR": c.ERROR, "CRITICAL": c.CRITICAL
        }
        for keyword, color in level_keywords.items():
            msg = re.sub(rf'\b{keyword}\b', f"{color}{keyword}{c.RESET_FORE}", msg, flags=re.IGNORECASE)

        # Highlight string keys with double quotes
        msg = re.sub(
            r'(?P<key>"[^"]+?")(?P<colon>\s*:)',
            lambda m: f"{c.COLOR_KEY}{m.group('key')}{c.RESET_FORE}{c.COLOR_COLON}{m.group('colon')}{c.RESET_FORE}",
            msg
        )

        # Highlight brackets/braces/commas
        msg = msg.replace('{', f"{c.COLOR_BRACE_OPEN}{{{c.RESET_FORE}")
        msg = msg.replace('}', f"{c.COLOR_BRACE_CLOSE}}}{c.RESET_FORE}")
        msg = msg.replace('(', f"{c.COLOR_PAREN_OPEN}({c.RESET_FORE}")
        msg = msg.replace(')', f"{c.COLOR_PAREN_CLOSE}){c.RESET_FORE}")
        msg = msg.replace(':', f"{c.COLOR_COLON}:{c.RESET_FORE}")
        msg = msg.replace(',', f"{c.COLOR_COMMA},{c.RESET_FORE}")

        msg = re.sub(r'(?<=\n)(\s*)\[', lambda m: f"{m.group(1)}{c.COLOR_BRACKET_OPEN}[{c.RESET_FORE}", msg)
        msg = re.sub(r'](?=\n)', lambda m: f"{c.COLOR_BRACKET_CLOSE}]{c.RESET_FORE}", msg)

        return msg


    def __highlight_data(self, msg: str) -> str:
        c = self.presets

        # Python style dicts: support both 'key' and "key"
        msg = re.sub(
            r'(?P<key>[\'"][^\'"]+[\'"])(?P<colon>\s*:)',
            lambda m: f"{c.INFO}{m.group('key')}{c.RESET_FORE}{c.COLOR_COLON}{m.group('colon')}{c.RESET_FORE}",
            msg
        )

        msg = msg.replace('{', f"{c.COLOR_BRACE_OPEN}{{{c.RESET_FORE}")
        msg = msg.replace('}', f"{c.COLOR_BRACE_CLOSE}}}{c.RESET_FORE}")
        msg = msg.replace('(', f"{c.COLOR_PAREN_OPEN}({c.RESET_FORE}")
        msg = msg.replace(')', f"{c.COLOR_PAREN_CLOSE}){c.RESET_FORE}")
        msg = msg.replace(':', f"{c.COLOR_COLON}:{c.RESET_FORE}")
        msg = msg.replace(',', f"{c.COLOR_COMMA},{c.RESET_FORE}")

        msg = re.sub(r'(?<=\n)(\s*)\[', lambda m: f"{m.group(1)}{c.COLOR_BRACKET_OPEN}[{c.RESET_FORE}", msg)
        msg = re.sub(r'](?=\n)', lambda m: f"{c.COLOR_BRACKET_CLOSE}]{c.RESET_FORE}", msg)

        return msg


    def __get_env_prefix(self, dimmed_color, dimmed_style, color, style) -> str:
        """Generate environment prefix for log messages."""
        meta = self.__env_metadata
        if not self.__config.color_enabled or self.__config.deployed or self.__config.mode == 'json':
            dimmed_color = ''
            dimmed_style = ''
            color = ''
            style = ''

        prefix = []
        verbose = self.__config.verbose
        first_color_flag = False
        if meta.get('project', None) is not None and (self.__config.deployed or verbose):
            prefix.append(f"{color}{style}{meta['project'].upper()}{self.presets.RESET}")
            first_color_flag = True
        if meta.get('env', None) is not None and (self.__config.deployed or verbose):
            if first_color_flag:
                prefix.append(f"{dimmed_color}{dimmed_style}{meta['env'].upper()}{self.presets.RESET}")
            else:
                prefix.append(f"{color}{style}{meta['env'].upper()}{self.presets.RESET}")
        if meta.get('project_version', None) is not None and (self.__config.deployed or verbose):
            if first_color_flag:
                prefix.append(f"{dimmed_color}{dimmed_style}{meta['project_version']}{self.presets.RESET}")
            else:
                prefix.append(f"{color}{style}{meta['project_version']}{self.presets.RESET}")
        if meta.get('run_id', None) is not None and (self.__config.deployed or verbose):
            if first_color_flag:
                prefix.append(f"{dimmed_color}{dimmed_style}{meta['run_id'].upper()}{self.presets.RESET}")
            else:
                prefix.append(f"{color}{style}{meta['run_id'].upper()}{self.presets.RESET}")

        if len(prefix) > 0:
            return f' {color}{style}:{self.presets.RESET} '.join(prefix) + f" {color}{style}|{self.presets.RESET} "
        else:
            return ''

    @staticmethod
    def __get_depth(internal = False) -> int:
        """Get stack depth to determine log source."""
        for i, frame in enumerate(inspect.stack()):
            if frame.filename.endswith("ccLogBase.py") or 'WrenchCL' in frame.filename or frame.filename == '<string>':
                if internal:
                    return i + 2
                else:
                    continue
            return i
        # Fallback: If stack inspection fails, return depth 1 (assume direct caller).
        return 1

    @staticmethod
    def __suggest_exception(args) -> Optional[str]:
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

    def __get_safe_char(self, char:str, backup:str = None) -> str:
        """Get safe character to use in log messages."""
        if not backup:
            backup = '-'
        safe_mode = not (self.__config.mode == 'terminal' and self.__config.color_enabled)
        return char if not safe_mode else backup



    def __apply_color(self, text: str, color: Optional[str]) -> str:
        """Apply ANSI colors to text if color mode is enabled."""
        return f"{self.presets.BRIGHT}{color} {text} {self.presets.RESET}" if color else text

    def __check_deployment(self, log = True):
        """Detect deployment environment and adjust settings accordingly."""
        if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None:
            self.__config.color_enabled = False
            self.__config.deployed = True
            self.disable_color()
            if log:
                self._internal_log("Detected Lambda deployment. Set color mode to False.")
            self.__config.mode = 'json'

        if os.environ.get("AWS_EXECUTION_ENV") is not None:
            self.__config.color_enabled = False
            self.__config.deployed = True
            self.disable_color()
            if log:
                self._internal_log("Detected AWS deployment. Set color mode to False.")
            self.__config.mode = 'json'

        if os.environ.get("COLOR_MODE") is not None:
            if os.environ.get("COLOR_MODE").lower() == "false":
                self.__config.color_enabled = False
            else:
                self.__config.color_enabled = True

        if os.environ.get("LOG_DD_TRACE") is not None:
            val = os.environ.get("LOG_DD_TRACE", "false").lower()
            self.__config.dd_trace_enabled = val == "true"
            state = "enabled" if self.__config.dd_trace_enabled else "disabled"
            if log:
                self._internal_log(f"LOG_DD_TRACE detected — Datadog tracing {state}. | Mode Json")
            if self.__config.dd_trace_enabled:
                self.__config.mode = 'json'

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
        if self.__config.color_enabled:
            try:
                self.enable_color()
                return
            except ImportError:
                pass
        self.disable_color()

    def __use_json_logging(self):
        """
        Configure the logger for JSON-structured output.
        """

        formatter = _JSONLogFormatter(self.__env_metadata, self.__force_markup, self.__highlight_literals, self.__config.dd_trace_enabled, self.__config.deployed)

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
        if self.__config.mode == "json":
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

    def __get_formatter(self, level: logLevels, no_format=False, no_color=False) -> logging.Formatter:
        """Get the appropriate formatter based on log level and mode."""
        if not isinstance(level, LogLevel):
            level = LogLevel(level)

        if no_format and no_color:
            return logging.Formatter(fmt='%(message)s')

        active_preset = self.presets
        if no_color:
            active_preset = ColorPresets(_MockColorama, _MockColorama)

        if self.__config.mode == 'json' and level != 'INTERNAL':
            return _JSONLogFormatter(self.__env_metadata, self.__force_markup, self.__highlight_literals, self.__config.dd_trace_enabled, self.__config.deployed)

        color = active_preset.get_color_by_level(level)
        style = active_preset.get_level_style(level)
        message_color = active_preset.get_message_color(level)

        if level in ['ERROR', 'CRITICAL', 'WARNING']:
            dimmed_color = active_preset.get_color_by_level(level)
        else:
            dimmed_color = active_preset.get_color_by_level(LogLevel('INTERNAL'))

        dimmed_style = active_preset.get_level_style(LogLevel('INTERNAL'))

        if level == 'INTERNAL':
            color = active_preset.CRITICAL
            style = active_preset.get_level_style(LogLevel('INTERNAL'))


        file_section = f"{dimmed_color}{dimmed_style}%(filename)s:%(funcName)s:%(lineno)d]{active_preset.RESET}"
        verbose_section = f"{dimmed_color}{dimmed_style}[%(asctime)s|{file_section}{active_preset.RESET}"
        app_env_section = self.__get_env_prefix(dimmed_color, dimmed_style, color, style)
        level_name_section = f"{color}{style}%(levelname)-8s{active_preset.RESET}"
        colored_arrow_section = f"{color}{style} -> {active_preset.RESET}"
        message_section = f"{style}{message_color}%(message)s{active_preset.RESET}"

        if self.__global_stream_configured:
            name_section = f"{color}{style}[%(name)s] - {active_preset.RESET}"
        else:
            name_section = f""

        if level == "INTERNAL":
            level_name_section = f"{color}{style}  WrenchCLInternal{active_preset.RESET}"
        elif level == "DATA":
            level_name_section = f"{color}{style}DATA    {active_preset.RESET}"

        if self.__config.mode == 'compact':
            fmt = f"{level_name_section}{file_section}{colored_arrow_section}{message_section}"
        elif no_format:
            fmt = "%(message)s"
        elif level == 'INTERNAL':
            fmt = f"{level_name_section}{colored_arrow_section}{message_section}"
        else:
            fmt = f"{app_env_section}{name_section}{level_name_section}{verbose_section}{colored_arrow_section}{message_section}"

        fmt = f"{active_preset.RESET}{fmt}{active_preset.RESET}"

        return _CustomFormatter(fmt, datefmt='%H:%M:%S', presets=self.presets)

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


logger: ccLogBase = ccLogBase()

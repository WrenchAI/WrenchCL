import importlib
import inspect
import logging
import os
import re
import sys
import time
import json
from datetime import datetime
from logging import Handler
from types import TracebackType
from typing import Any, Optional, Union, Literal, Type, IO
from difflib import get_close_matches

from .._Internal._MockPandas import MockPandas
from ..Decorators.Deprecated import Deprecated
from ..Decorators.SingletonClass import SingletonClass
import json
import logging

try:
    import pandas as pd
except ImportError:
    pd = MockPandas()


class ExceptionSuggestor:
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


class MockColorama:
    pass


class ColorPresets:
    """
    Provides color presets for common log use-cases.
    Falls back to mock colors if colorama isn't installed.
    """
    _color_class = MockColorama
    _style_class = MockColorama
    INFO = None
    DEBUG = None
    WARNING = None
    ERROR = None
    CRITICAL = None
    HEADER = None
    DATA = None
    BRIGHT = None
    NORMAL = None
    RESET = None
    COLOR_TRUE = None
    COLOR_FALSE = None
    COLOR_NONE = None
    COLOR_KEY = None
    COLOR_NUMBER = None

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
        super().__setattr__("DATA", getattr(self._color_class, 'BLUE', ''))

        super().__setattr__('BRIGHT', getattr(self._style_class, 'BRIGHT', ''))
        super().__setattr__('NORMAL', getattr(self._style_class, 'NORMAL', ''))
        super().__setattr__('RESET', getattr(self._style_class, 'RESET_ALL', ''))

        # Literal colors
        super().__setattr__('COLOR_TRUE', getattr(self._color_class, 'GREEN', ''))
        super().__setattr__('COLOR_FALSE', getattr(self._color_class, 'RED', ''))
        super().__setattr__('COLOR_NONE', getattr(self._color_class, 'WHITE', ''))
        super().__setattr__('COLOR_KEY', getattr(self._color_class, '', ''))
        super().__setattr__('COLOR_NUMBER', getattr(self._color_class, 'YELLOW', ''))

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

    def get_demo_string(self):
        demo_string = "\n  • Log Level Color Preview:\n"
        demo_string += f"    {self.DEBUG}{self.get_level_style('DEBUG')}[DEBUG] Debug message preview{self.RESET}\n"
        demo_string += f"    {self.INFO}{self.get_level_style('INFO')}[INFO] Info message preview{self.RESET}\n"
        demo_string += f"    {self.WARNING}{self.get_level_style('WARNING')}[WARNING] Warning message preview{self.RESET}\n"
        demo_string += f"    {self.ERROR}{self.get_level_style('ERROR')}[ERROR] Error message preview{self.RESET}\n"
        demo_string += f"    {self.CRITICAL}{self.get_level_style('CRITICAL')}[CRITICAL] Critical message preview{self.RESET}\n"
        demo_string += f"    {self.HEADER}{self.get_level_style('HEADER')}[HEADER] Section header example{self.RESET}\n"
        demo_string += f"    {self.DATA}{self.get_level_style('DATA')}[DATA] Structured data printout{self.RESET}\n"

        demo_string += "  • Literal/Syntax Highlight Preview:\n"
        demo_string += f"    - true → {self.COLOR_TRUE}{self.BRIGHT}true{self.RESET}\n"
        demo_string += f"    - false → {self.COLOR_FALSE}{self.BRIGHT}false{self.RESET}\n"
        demo_string += f"    - none → {self.COLOR_NONE}{self.BRIGHT}None{self.RESET}\n"
        demo_string += f"    - \"key\": → {self.COLOR_KEY}{self.BRIGHT}\"key\"{self.RESET}{self.COLOR_COLON}:{self.RESET}\n"
        demo_string += f"    - 123 → {self.COLOR_NUMBER}123{self.RESET}\n"
        demo_string += f"    - {{ }} → {self.COLOR_BRACE_OPEN}{{{self.RESET} content {self.COLOR_BRACE_CLOSE}}}{self.RESET}\n"
        demo_string += f"    - [ ] → {self.COLOR_BRACKET_OPEN}[{self.RESET} content {self.COLOR_BRACKET_CLOSE}]{self.RESET}\n"
        demo_string += f"    - ( ) → {self.COLOR_PAREN_OPEN}({self.RESET} content {self.COLOR_PAREN_CLOSE}){self.RESET}\n"
        demo_string += f"    - {self.COLOR_KEY}{self.BRIGHT}key{self.RESET}{self.COLOR_COLON}:{self.RESET}value{self.COLOR_COMMA},{self.RESET}\n"

        return demo_string


class CustomFormatter(logging.Formatter):
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

class JSONLogFormatter(logging.Formatter):
    def __init__(self, env_metadata: dict):
        super().__init__()
        self.env_metadata = env_metadata

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "meta": {
                "env": self.env_metadata.get("env"),
                "project": self.env_metadata.get("project"),
                "version": self.env_metadata.get("project_version"),
                "run_id": self.env_metadata.get("run_id"),
            }
        }

        if hasattr(record, "trace_id"):
            log_record["trace_id"] = record.trace_id
        if hasattr(record, "span_id"):
            log_record["span_id"] = record.span_id
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)


_exc_info_type = None | bool | tuple[Type[BaseException], BaseException, TracebackType | None] | tuple[
    None, None, None] | BaseException


class BaseLogger:
    """
    WrenchCL's structured, colorized, and extensible logger.

    Features:
    ---------
    • Structured formatting with optional syntax highlighting for Python/JSON-style literals.
    • Supports plain unformatted output via `no_format=True` (for tools or pipelines).
    • Optional Datadog APM trace correlation (trace_id, span_id) via ddtrace.
    • Intelligent error suggestions for common exceptions (e.g. attribute typos).
    • Compact/verbose toggles, ANSI color presets, and auto AWS Lambda adaptation.
    • Global stream override with support for silencing external loggers.

    Environment Variables:
    ----------------------
    - COLOR_MODE:
        Controls ANSI color output.
        Accepts: "true", "false"
        Default: "true" (disabled automatically in AWS Lambda)

    - LOG_DD_TRACE:
        Enables Datadog trace context injection (trace_id/span_id) if `ddtrace` is available.
        Accepts: "true", "false"
        Default: "false"

    - PROJECT_NAME, PROJECT_VERSION, ENV:
        Optional project metadata used in log headers.

    - Fallbacks:
        - `AWS_EXECUTION_ENV`, `AWS_LAMBDA_FUNCTION_NAME`, `LAMBDA_TASK_ROOT`, `REPO_VERSION` as safe fallbacks
          for metadata extraction in cloud environments.

    Key Properties:
    ---------------
    - logger.compact_mode         → If True, disables extra spacing and formatting.
    - logger.verbose_mode         → If True, enables timestamps and file/function context.
    - logger.color_mode           → Controls ANSI color output.
    - logger.dd_trace             → Enables Datadog trace injection (overrides env).
    - logger.log_mode             → One of: 'terminal' | 'json'
    - logger.highlight_syntax     → Enables literal/syntax highlighting.
    - logger.deployment_mode      → True if in Lambda/EC2 context.
    - logger.color_presets        → Active color config object.

    Logging Methods:
    ----------------
    - info(...), debug(...), warning(...), error(...), critical(...), exception(...)
        → Accepts `no_format=True` to emit raw output, bypassing prefix/formatting.
        → Accepts `exc_info=...` to attach or suppress tracebacks.
        → Accepts `stack_info=True` to include full stack details.

    Pretty Logging:
    ---------------
    - pretty_log(obj, indent=4, **kwargs)
        → Smart print of dicts, models, DataFrames, etc., respecting compact/color settings.

    Additional Methods:
    -------------------
    - header("title")                  → Stylized section output.
    - log_time("phase name")          → Elapsed time since last `start_time()`.
    - silence_logger("name")          → Mute a specific logger.
    - configure_global_stream(...)    → Apply Wrench formatting globally.
    - reinitialize()                  → Rereads all env-driven flags.
    - force_color()                   → Enables color in CI/Docker.
    - display_logger_state()          → Renders demo/config summary.

    """




    def __init__(self, level: str = 'INFO') -> None:
        self.__global_stream_configured = False
        self.__initialized = False
        self.run_id = self.__generate_run_id()
        self.__compact_mode = False
        self.__verbose_mode = False
        self.__start_time = None
        self.__dd_log_flag = False
        self.__log_mode = 'terminal'
        self.__base_level = 'DEBUG'

        self.__highlight_syntax = True
        self.presets = ColorPresets(None, None)

        self.__env_metadata = self.__fetch_env_metadata()
        self.__dd_trace_enabled = os.environ.get("LOG_DD_TRACE", "false").lower() == "true"
        self.__color_mode = os.environ.get("COLOR_MODE", "true").lower() == "true"

        self.__deployed = False
        self.__logger_instance = logging.getLogger('WrenchCL')
        self.__setup()
        self.__check_deployment()
        self.__check_color()
        
    def reinitialize(self):
        """
        Re-applies all environment-variable-driven settings (e.g., COLOR_MODE, LOG_DD_TRACE, ENV).

        This method refreshes internal flags such as deployment mode, color mode, and metadata
        without reinitializing logger handlers. Call this if env vars are updated at runtime.
        """
        self.__check_deployment()
        self.__check_color()
        self.__env_metadata = self.__fetch_env_metadata()

    def update_color_presets(self, **kwargs) -> None:
        self.presets.update(**kwargs)

    def initiate_new_run(self):
        self.run_id = self.__generate_run_id()

    def setLevel(self, level: Literal["DEBUG", "INFO", 'WARNING', 'ERROR', 'CRITICAL']) -> None:
        self.flush_handlers()
        self.__logger_instance.setLevel(self.__get_level(level))

    def info(self, *args, exc_info: _exc_info_type = None, **kwargs) -> None:
        """
        Logs an INFO-level message.

        :param args: Strings or objects to log. If an exception is passed, it will be extracted from args and used as exc_info.
        :param exc_info: Optional. Can override auto-detected exception. Accepts True, False, an Exception, or (type, value, traceback).
        :param no_format: If True, disables structured formatting and prints raw text only.
        :param stack_info: If True, appends stack trace to output.
        :param kwargs: Additional options like `compact_mode`, `color_flag`, or `no_color`.
        """
        self.__log(logging.INFO, *args, exc_info=exc_info, **kwargs)

    def warning(self, *args, exc_info: _exc_info_type = None, **kwargs) -> None:
        """
        Logs a WARNING-level message.

        :param args: Strings or exceptions. Exceptions in args will be extracted and used as exc_info.
        :param exc_info: Manually control exception output. Accepts True, False, or full exc tuple.
        :param no_format: Disable formatting if True.
        :param stack_info: Include stack trace in output if True.
        :param kwargs: Internal formatting flags (e.g., color override).
        """
        self.__log(logging.WARNING, *args, exc_info=exc_info, **kwargs)

    def error(self, *args, exc_info: _exc_info_type = True, **kwargs) -> None:
        """
        Logs an ERROR-level message, with exception handling enabled by default.

        :param args: Strings or objects to log. Exceptions in args will be auto-used as exc_info.
        :param exc_info: If True (default), uses current exception. Can override with actual Exception or (type, value, tb).
        :param no_format: If True, disables all formatting.
        :param stack_info: Includes stack trace if set.
        :param kwargs: Additional formatting flags or overrides.
        """
        self.__log(logging.ERROR, *args, exc_info=exc_info, **kwargs)

    def critical(self, *args, exc_info: _exc_info_type = None, **kwargs) -> None:
        """
        Logs a CRITICAL-level message.

        :param args: Strings or exceptions. First exception in args is used if present.
        :param exc_info: Overrides auto-detected exception.
        :param no_format: Output raw string with no styling if True.
        :param stack_info: Append call stack to message.
        :param kwargs: Extra logger behavior controls.
        """
        self.__log(logging.CRITICAL, *args, exc_info=exc_info, **kwargs)

    def exception(self, *args, exc_info: _exc_info_type = True, **kwargs) -> None:
        """
        Logs an ERROR-level message with full traceback.

        :param args: Strings or Exception objects. First Exception in args is extracted if `exc_info` not manually set.
        :param exc_info: Defaults to True. Can be set to an exception or tuple to override.
        :param no_format: Skips styling and output transforms if True.
        :param stack_info: Appends traceback and call stack if True.
        :param kwargs: Logger internals and control overrides.
        """
        self.__log(logging.ERROR, *args, exc_info=exc_info, **kwargs)

    def debug(self, *args, exc_info: _exc_info_type = None, **kwargs) -> None:
        """
        Logs a DEBUG-level message.

        :param args: Any loggable values (str, Exception, etc). Exceptions are auto-extracted from args if present.
        :param exc_info: Manually override exception context. If True, uses current exception.
        :param no_format: If True, disables formatting and outputs plain message.
        :param stack_info: If True, includes current call stack.
        :param kwargs: Additional control options passed to logger internals.
        """
        self.__log(logging.DEBUG, *args, exc_info=exc_info, **kwargs)

    def _internal_log(self, *args, exc_info: _exc_info_type = None, level: str | int = None) -> None:
        if level:
            level = self.__get_level(level)
        if not level:
            level = logging.DEBUG
        self.__log(level, *args, exc_info=exc_info, compact_mode=False,
                   color_flag="INTERNAL")


    def start_time(self) -> None:
        """
        Starts or resets the internal timer for measuring elapsed time in `log_time()`.
        """
        self.__start_time = time.time()

    def log_time(self, message="Elapsed time") -> None:
        """
        Logs the time elapsed since the last `start_time()` checkpoint.

        :param message: Prefix message to display alongside elapsed duration.
        """
        if self.__start_time:
            elapsed = time.time() - self.__start_time
            self.info(f"{message}: {elapsed:.2f}s")

    def header(self, text: str, size=80, compact=False) -> None:
        """
        Logs a stylized section header.

        :param text: The header text. Underscores and dashes are replaced with spaces.
        :param size: Width of the line used to center the header.
        :param compact: If True, uses a single-line compact format. Otherwise adds padding and line breaks.
        """
        text = text.replace('_', ' ').replace('-', ' ').strip().capitalize()
        if compact:
            size = 40
            formatted = self.__apply_color(text, self.presets.HEADER).center(size, "-")
        else:
            size = 80
            formatted = "\n\n" + self.__apply_color(text, self.presets.HEADER).center(size, "-") + "\n"
        self.__log("INFO", formatted, no_format = True, no_color = True)

    def pretty_log(self, obj: Any, indent=4, **kwargs) -> None:
        """
        Logs a prettified version of an object (e.g., dict, model, DataFrame).

        :param obj: Any printable object. Smart handling for Pydantic models, dicts, str, and pandas DataFrames.
        :param indent: Indentation level for structured formats like JSON.
        :param kwargs: Passed through to serialization methods like `.json()` or `json.dumps()`.
        """
        try:
            if isinstance(obj, pd.DataFrame):
                prefix_str = f"DataType: {type(obj).__name__} | Shape: {obj.shape[0]} rows | {obj.shape[1]} columns"
                pd.set_option(
                    'display.max_rows', 500,
                    'display.max_columns', None,
                    'display.width', None,           # Adjust width as needed
                    'display.max_colwidth', 50,
                    'display.colheader_justify', 'center'
                )
                output = str(obj)
            if hasattr(obj, 'pretty_print'):
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
        except Exception as e:
            output = str(obj)
        self.__log(logging.INFO, output, exc_info=False, compact_mode=self.__compact_mode, color_flag="DATA")

    # ---------------- Internals ---------------- #
    def __log(self, level: Union[int, str], *args: str, exc_info: _exc_info_type = None,
              compact_mode: bool = False, color_flag: Optional[Literal['INTERNAL', 'DATA']] = None, **kwargs) -> None:

        args = self._inject_dd_context(args)  # no-qa

        args = list(args)

        for idx, a in enumerate(args):
            if isinstance(a, Exception) or isinstance(a, BaseException):
                exc_info = args.pop(idx)
        suggestion = self.__suggest_exception(exc_info)

        if suggestion:
            suggestion = f"{self.presets.ERROR}{suggestion}{self.presets.RESET}"
            args.append(suggestion)

        args = tuple(args)

        msg = '\n'.join(str(arg) for arg in args)
        msg = self.__highlight_literals(msg, data=color_flag == 'DATA')
        if self.deployment_mode or self.compact_mode or compact_mode:
            lines = msg.splitlines()
            msg = ' '.join([line.strip() for line in lines if len(line.strip()) > 0])
            msg = msg.replace('\n', ' ').replace('\r', '').strip()

        if color_flag == 'INTERNAL':
            level = "INTERNAL"
        elif color_flag == 'DATA':
            level = "DATA"

        self.flush_handlers()
        for handler in self.__logger_instance.handlers:
            if not isinstance(handler, logging.NullHandler):
                handler.setFormatter(self.__get_formatter(level, no_format=kwargs.get('no_format', False)))

        lines = msg.splitlines()
        if len(lines) > 1:
            msg = "\n    " + "\n    ".join(lines)
        if exc_info:
            msg = "\n".join(lines)

        if isinstance(level, str):
            level = self.__get_level(level)

        self.__logger_instance.log(level, msg, exc_info=exc_info, stack_info=kwargs.get('stack_info', False), stacklevel=self.__get_depth())

    def __get_env_prefix(self, dimmed_color, dimmed_style, color, style) -> str:
        meta = self.__env_metadata
        if not self.__color_mode or self.__deployed or self.__log_mode == 'json':
            dimmed_color = ''
            dimmed_style = ''
            color = ''
            style = ''

        prefix = []
        if meta.get('env', None) is not None and (self.__deployed or self.__verbose_mode):
            prefix.append(f"{color}{style}{meta['project'].upper()}{self.presets.RESET}")
        if meta.get('project', None) is not None and (self.__deployed or self.__verbose_mode):
            prefix.append(f"{dimmed_color}{dimmed_style}{meta['env'].upper()}{self.presets.RESET}")
        if meta.get('project_version', None) is not None and (self.__deployed or self.__verbose_mode):
            prefix.append(f"{dimmed_color}{dimmed_style}{meta['project_version'].upper()}{self.presets.RESET}")
        if meta.get('run_id', None) is not None and (self.__deployed or self.__verbose_mode):
            prefix.append(f"{dimmed_color}{dimmed_style}{meta['run_id'].upper()}{self.presets.RESET}")
        if len(prefix) > 0:
            return ' : '.join(prefix) + f" {color}{style}|{self.presets.RESET} "
        else:
            return ''


    def __check_deployment(self):
        if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None:
            self._internal_log("Detected Lambda deployment. Setting color mode to False.")
            self.__color_mode = False
            self.__deployed = True
            self.__log_mode = 'json'
        if os.environ.get("AWS_EXECUTION_ENV") is not None:
            self._internal_log("Detected AWS deployment. Setting color mode to False.")
            self.__color_mode = False
            self.__deployed = True
            self.__log_mode = 'json'
        if os.environ.get("COLOR_MODE") is not None:
            if os.environ.get("COLOR_MODE").lower() == "false":
                self._internal_log("Detected COLOR_MODE Setting color mode to false.")
                self.__color_mode = False
            else:
                self._internal_log("Detected COLOR_MODE Setting color mode to True.")
                self.__color_mode = True
        if os.environ.get("LOG_DD_TRACE") is not None:
            val = os.environ.get("LOG_DD_TRACE", "false").lower()
            self.__dd_trace_enabled = val == "true"
            state = "enabled" if self.__dd_trace_enabled else "disabled"
            self._internal_log(f"LOG_DD_TRACE detected — Datadog tracing {state}.", level="INTERNAL")
            self.__log_mode = 'json'

    def __fetch_env_metadata(self) -> dict:
        """
        Returns environment metadata using primary and fallback AWS environment variables.
        """
        return {
            "env": os.getenv("ENV") or os.getenv('DD_ENV') or os.getenv("AWS_EXECUTION_ENV") or None,
            "project": os.getenv("PROJECT_NAME") or os.getenv('COMPOSE_PROJECT_NAME') or os.getenv("AWS_LAMBDA_FUNCTION_NAME") or None,
            "project_version": os.getenv("PROJECT_VERSION") or os.getenv("LAMBDA_TASK_ROOT") or os.getenv('REPO_VERSION') or None,
            "run_id": self.run_id
        }

    def _inject_dd_context(self, args: tuple[str]) -> tuple[str]:
        if not self.__dd_trace_enabled:
            return args
        try:
            ddtrace = importlib.import_module("ddtrace")
            context = ddtrace.tracer.get_log_correlation_context()
            trace_id = context.get("trace_id")
            span_id = context.get("span_id")
            if trace_id and span_id:
                prefix = f"[dd.trace_id={trace_id} dd.span_id={span_id}]"
                return (prefix, *args)
        except ImportError as e:
            if not self.__dd_log_flag:
                self._internal_log(
                    "Datadog trace is not installed while the feature is requested as enabled."
                    "You can install it with `pip install wrenchcl[trace]`.",
                    level=logging.WARNING
                )
                self.__dd_log_flag = True
        except Exception as e:
            self._internal_log(
                "Datadog trace injection failed",
                exc_info=e,
                level=logging.WARNING
            )
        return args



    def __highlight_literals(self, msg: str, data: bool = False) -> str:
        if not self.color_mode or not self.__highlight_syntax or self.__deployed:
            return msg

        c = self.presets

        # Boolean/None literals — match as full words
        msg = re.sub(r'\btrue\b', lambda m: f"{c.COLOR_TRUE}{c.BRIGHT}{m.group(0)}{c.RESET}", msg, flags=re.IGNORECASE)
        msg = re.sub(r'\bfalse\b', lambda m: f"{c.COLOR_FALSE}{c.BRIGHT}{m.group(0)}{c.RESET}", msg, flags=re.IGNORECASE)
        msg = re.sub(r'\bnone\b', lambda m: f"{c.COLOR_NONE}{c.BRIGHT}{m.group(0)}{c.RESET}", msg, flags=re.IGNORECASE)
        msg = re.sub(r'\bnull\b', lambda m: f"{c.COLOR_NONE}{c.BRIGHT}{m.group(0)}{c.RESET}", msg, flags=re.IGNORECASE)
        msg = re.sub(r'\bnan\b', lambda m: f"{c.COLOR_NONE}{c.BRIGHT}{m.group(0)}{c.RESET}", msg, flags=re.IGNORECASE)

        if data:
            # Match string keys (only if followed by colon)
            msg = re.sub(
                r'(?P<key>"[^"]+?")(?P<colon>\s*:)',  # `"key":` only
                lambda m: f"{c.COLOR_KEY}{c.BRIGHT}{m.group('key')}{c.RESET}{c.COLOR_COLON}{m.group('colon')}{c.RESET}",
                msg
            )

            # Match standalone integers (not quoted, surrounded by whitespace or symbols)
            msg = re.sub(
                r'(?<=\s)(\d+)(?=\s|[,|\]])',  # match int if followed by space, comma, or ]
                lambda m: f"{c.COLOR_NUMBER}{m.group(1)}{c.RESET}",
                msg
            )

            # Brackets, braces, parens
            msg = msg.replace('{', f"{c.COLOR_BRACE_OPEN}{{{c.RESET}")
            msg = msg.replace('}', f"{c.COLOR_BRACE_CLOSE}}}{c.RESET}")
            msg = msg.replace('(', f"{c.COLOR_PAREN_OPEN}({c.RESET}")
            msg = msg.replace(')', f"{c.COLOR_PAREN_CLOSE}){c.RESET}")
            msg = msg.replace(':', f"{c.COLOR_COLON}:{c.RESET}")
            msg = msg.replace(',', f"{c.COLOR_COMMA},{c.RESET}")

            # Brackets: only color when at line-start or line-end to avoid nested breakage
            msg = re.sub(r'(?<=\n)(\s*)\[', lambda m: f"{m.group(1)}{c.COLOR_BRACKET_OPEN}[{c.RESET}", msg)
            msg = re.sub(r'\](?=\n)', lambda m: f"{c.COLOR_BRACKET_CLOSE}]{c.RESET}", msg)

        return msg

    def __get_depth(self) -> int():
        for i, frame in enumerate(inspect.stack()):
            if frame.filename.endswith("WrenchLogger.py") or 'WrenchCL' in frame.filename or frame.filename == '<string>':
                continue
            return i

    def __suggest_exception(self, args) -> str | None:
        suggestion = None
        if not hasattr(args, '__iter__') and args is not None:
            args = [args]
        else:
            return suggestion
        for a in args:
            if isinstance(a, Exception) or isinstance(a, BaseException):
                ex = a
                if hasattr(ex, 'args') and ex.args and isinstance(ex.args[0], str):
                    suggestion = ExceptionSuggestor.suggest_similar(ex)
                break
        return suggestion

    def __apply_color(self, text: str, color: Optional[str]) -> str:
        return f"{color}{self.presets.BRIGHT}{text}{self.presets.RESET}" if color else text

    def __log_setup_summary(self) -> None:
        settings = self.logger_state
        msg = '⚙️  Logger Configuration:\n'

        msg += f"  • Logging Level: {self.__apply_color(logging.getLevelName(settings['Logging Level']), self.presets.get_color_by_level(settings['Logging Level']))}\n"
        msg += f"  • Run ID: {settings['Run Id']}\n"

        msg += "  • Mode Flags:\n"
        for mode, enabled in settings["Logging Modes"].items():
            state = "✓ Enabled" if enabled else "✗ Disabled"
            color = self.presets.INFO if enabled else self.presets.ERROR
            msg += f"      - {mode:20s}: {self.__apply_color(state, color)}\n"

        msg += self.presets.get_demo_string()  # Use the actual instance, not the dict
        self.__logger_instance.info(msg)


    @staticmethod
    def __generate_run_id() -> str:
        now = datetime.now()
        return f"R-{os.urandom(1).hex().upper()}{now.strftime('%m%d')}{os.urandom(1).hex().upper()}"

    def __get_level(self, level: Union[str, int]) -> int:
        if isinstance(level, str) and hasattr(logging, level.upper()):
            return getattr(logging, level.upper())
        elif isinstance(level, int):
            return level
        elif level == 'INTERNAL':
            return logging.DEBUG
        return logging.INFO

    def flush_handlers(self):
        """
        Flushes all handlers associated with the logger instance.

        This method ensures that any pending log messages in the handlers
        are written out, suppressing any exceptions that occur during the
        flush process.
        """
        for h in self.__logger_instance.handlers:
            try:
                h.flush()
            except Exception:
                pass

    def add_new_handler(
        self,
        handler_cls: Type[logging.Handler] = logging.StreamHandler,
        stream: Optional[IO[str]] = None,
        level: Union[str, int] = None,
        formatter: Optional[logging.Formatter] = None,
        force_replace: bool = False,
    ) -> logging.Handler:
        """
        Adds a new logging handler (e.g., StreamHandler, NullHandler, FileHandler) to the WrenchCL logger.

        :param handler_cls: A subclass of `logging.Handler` to use as the handler.
                            Supported options include:
                              - `logging.StreamHandler` (default, requires `stream`)
                              - `logging.FileHandler` (requires `filename` via partial or wrapper)
                              - `logging.NullHandler` (ignores all log messages)

        :param stream: A writable text stream (e.g., `sys.stdout`, `io.StringIO`).
                       Required if `handler_cls` is a stream-based handler (like `StreamHandler`).

        :param level: The logging level for the handler. Accepts string levels ("INFO", "DEBUG") or integer constants (e.g., logging.INFO).

        :param formatter: Optional `logging.Formatter` instance. If not provided, the active WrenchCL formatter is used.

        :param force_replace: If True, removes all existing handlers before attaching the new one.

        :return: The newly added `logging.Handler` instance.
        """
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



    def __get_formatter(self, level: Union[str, int], no_format=False) -> logging.Formatter:

        if self.__log_mode == 'json':
            return JSONLogFormatter(self.__env_metadata)

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

        file_section = f"{dimmed_color}{dimmed_style}%(filename)s:%(funcName)s:%(lineno)d]{self.presets.RESET}"
        verbose_section = f"{dimmed_color}{dimmed_style}[%(asctime)s|{file_section}{self.presets.RESET}"
        app_env_section = self.__get_env_prefix(dimmed_color, dimmed_style, color, style)
        level_name_section = f"{color}{style}%(levelname)-8s{self.presets.RESET}"
        colored_dash_section = f"{color}{style} -- {self.presets.RESET}"
        colored_arrow_section = f"{color}{style} -> {self.presets.RESET}"
        message_section = f"{style}{message_color}%(message)s{self.presets.RESET}"

        if level == "INTERNAL":
            level_name_section = f"{color}{style}WRENCHCL{self.presets.RESET}"
        elif level == "DATA":
            level_name_section = f"{color}{style}DATA    {self.presets.RESET}"

        if self.compact_mode:
            fmt = f"{level_name_section}{file_section}{colored_arrow_section}{message_section}"
        elif no_format:
            fmt = "%(message)s"
        else:
            fmt = f"{app_env_section}{level_name_section}{verbose_section}{colored_arrow_section}{message_section}"

        return CustomFormatter(fmt, datefmt='%H:%M:%S', presets=self.presets)

    def __use_json_logging(self):
        self.__log_mode = 'json'
        formatter = JSONLogFormatter(self.__env_metadata)

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

    def __check_color(self) -> None:
        if self.__color_mode:
            try:
                self.enable_color()
                return
            except ImportError as e:
                pass
        self.disable_color()

    def __setup(self) -> None:
        if self.__initialized:
            self._internal_log("Logger already initialized. Skipping setup.", level=logging.WARNING)
            return
        self.flush_handlers()
        self.__logger_instance.setLevel(self.__base_level)
        self.add_new_handler(logging.StreamHandler, stream=sys.stdout, force_replace=True)
        self.__logger_instance.propagate = False
        self.__initialized = True


    def disable_color(self):
        self._Color = MockColorama
        self._Style = MockColorama
        self.__color_mode = False
        self.highlight_syntax = False
        try:
            colorama = importlib.import_module("colorama")
            colorama.deinit()
        except ImportError:
            pass
        self.presets = ColorPresets(self._Color, self._Style)
        self._internal_log("Color output disabled.", level = logging.ERROR)

    def enable_color(self):
        try:
            colorama = importlib.import_module("colorama")
        except ImportError:
            self._internal_log("Colorama not installed. Cannot enable color output. You can install colorama with `pip install WrenchCL[color]`", level = logging.WARNING)
            self.disable_color()
            return
        self.__color_mode = True
        self.__highlight_syntax = True
        self._Color = colorama.Fore
        self._Style = colorama.Style
        self.presets = ColorPresets(self._Color, self._Style)
        colorama.deinit()
        colorama.init(strip=False, autoreset=False)
        self._internal_log("Color output enabled.", level = logging.INFO)

    # ---------------- Properties ---------------- #

    @property
    def level(self) -> str:
        """
        Returns the current log level as a string (e.g., 'INFO', 'DEBUG').
        """
        return logging.getLevelName(self.__logger_instance.level)

    @property
    def logger_instance(self) -> logging.Logger:
        """
        Returns the underlying `logging.Logger` instance.
        """
        return self.__logger_instance

    @property
    def handlers(self) -> list[Handler]:
        return self.__logger_instance.handlers

    @property
    def color_mode(self) -> bool:
        """
        Whether ANSI color output is currently enabled.
        """
        return self.__color_mode

    @color_mode.setter
    def color_mode(self, val: bool) -> None:
        """
        Enables or disables ANSI color output. Also re-triggers deployment mode detection.
        """
        if not isinstance(val, bool):
            raise TypeError("Expected bool, got %s" % type(val))
        if self.__color_mode == val:
            return
        self.__color_mode = val
        self.__check_deployment()
        self.__check_color()

    @property
    def dd_trace(self) -> bool:
        """
        Whether Datadog trace context injection is currently enabled.
        """
        return self.__dd_trace_enabled

    @dd_trace.setter
    def dd_trace(self, value: bool) -> None:
        """
        Enables or disables Datadog trace injection and adjusts output mode accordingly.
        """
        if not isinstance(value, bool):
            raise TypeError("Expected bool for dd_trace_enabled")
        self.__dd_trace_enabled = value
        if not self.__dd_trace_enabled and not self.__deployed:
            self.log_mode = 'terminal'
        else:
            self.log_mode = 'json'

    @property
    def deployment_mode(self) -> bool:
        """
        Indicates whether the logger is in deployment mode (e.g., AWS Lambda/EC2).
        """
        return self.__deployed

    @deployment_mode.setter
    def deployment_mode(self, val: bool) -> None:
        """
        Enables or disables deployment mode and toggles color/log_mode appropriately.
        """
        self.__deployed = val
        self.color_mode = not val
        if not self.__dd_trace_enabled and not self.__deployed:
            self.log_mode = 'terminal'
        else:
            self.log_mode = 'json'

    @property
    def compact_mode(self) -> bool:
        """
        Whether compact logging is enabled (one-liners without formatting).
        """
        return self.__compact_mode

    @compact_mode.setter
    def compact_mode(self, val: bool) -> None:
        """
        Enables or disables compact mode (minimal formatting).
        """
        self.__compact_mode = val

    @property
    def verbose_mode(self) -> bool:
        """
        Whether verbose logging is enabled (adds file, function, line info and run data).
        """
        return self.__verbose_mode

    @verbose_mode.setter
    def verbose_mode(self, val: bool) -> None:
        """"
        Enables or disables verbose mode for log output.
        """
        self.__verbose_mode = val

    @property
    def logger_state(self) -> dict:
        """
        Returns a structured summary of logger state, including mode flags, color config, metadata, and active settings.
        """
        return {
            "Logging Level": self.level,
            "Run Id": self.run_id,
            "Log Mode": self.log_mode,
            "Environment Metadata": self.__env_metadata,
            "Logging Modes": {
                "Global Streaming Mode": self.__global_stream_configured,
                "Color Mode": self.color_mode,
                "Highlight Syntax": self.highlight_syntax,
                "Compact Mode": self.compact_mode,
                "Verbose Mode": self.verbose_mode,
                "Deployment Mode": self.deployment_mode,
                "DD Trace Enabled": self.dd_trace,
            },
            "Color Settings": {
                key: val for key, val in self.presets.__dict__.items()
                if not key.startswith("_")
            },
            "Handlers": [type(h).__name__ for h in self.__logger_instance.handlers],
        }

    def display_logger_state(self) -> None:
        """
        Logs the current logger configuration, color presets, and formatting settings.
        """
        self.__log_setup_summary()

    @property
    def log_mode(self) -> str:
        """
        Returns current log mode: either 'terminal' or 'json'.
        """
        return self.__log_mode

    @log_mode.setter
    def log_mode(self, mode: Literal['terminal', 'json']) -> None:
        """
        Sets output log mode. 'json' disables color and structured prefixes used for cloudwatch/datadog. 'terminal' restores formatting.
        """
        if mode not in ('terminal', 'json'):
            raise ValueError("log_mode must be 'terminal' or 'json'")
        self.flush_handlers()
        self.__log_mode = mode
        if self.__log_mode == 'json':
            self.__use_json_logging()

    # Add this property for external access to presets
    @property
    def color_presets(self) -> ColorPresets:
        """
        Returns the active `ColorPresets` object used for ANSI styling.
        """
        return self.presets

    @property
    def highlight_syntax(self) -> bool:
        """
        Whether syntax highlighting for literals (e.g., true/false/None) is enabled.
        """
        return self.__highlight_syntax

    @highlight_syntax.setter
    def highlight_syntax(self, val: bool) -> None:
        """
        Enables or disables syntax highlighting for literals in log output.
        """
        self.__highlight_syntax = val

    # ---------------- Global Settings ---------------- #
    def configure_global_stream(self, level: str = "INFO", silence_others: bool = False, stream = sys.stdout) -> None:
        """
        Overrides the global logging stream and applies WrenchCL formatting to root logger.

        :param level: Log level for global stream (e.g., "INFO", "WARNING").
        :param silence_others: If True, disables propagation and silences other loggers.
        :param stream: Output stream to use (defaults to sys.stdout).
        """
        self.flush_handlers()
        root_logger = logging.getLogger()
        root_logger.setLevel(self.__base_level)

        handler = logging.StreamHandler(stream)
        self.flush_handlers()
        handler = self.add_new_handler(logging.StreamHandler, stream=stream, level=level, force_replace=True)
        root_logger.handlers = [handler]

        root_logger.propagate = False

        if silence_others:
            self.silence_other_loggers()

        self.__global_stream_configured = True
        self.__logger_instance.info("[Logger] Global stream configured successfully.")

    def silence_logger(self, logger_name: str, level: Optional[int] = None) -> None:
        """
        Silences a specific logger by attaching a NullHandler and disabling propagation.

        :param logger_name: Full name of the logger (e.g., 'uvicorn.error').
        :param level: Optional log level to enforce. Defaults to CRITICAL + 1.
        """
        logger = logging.getLogger(logger_name)
        for h in logger.handlers:
            h.flush()
        logger.handlers = [logging.NullHandler()]
        if not level:
            logger.setLevel(logging.CRITICAL + 1)
        else:
            logger.setLevel(level)
        logger.propagate = False

    def silence_other_loggers(self, level: Optional[int] = None) -> None:
        """
        Silences all third-party loggers except the root and WrenchCL logger.

        :param level: Optional override for silenced logger levels.
        """
        for name in logging.root.manager.loggerDict:
            if name != 'WrenchCL':
                self.silence_logger(name, level)

    def force_color(self) -> None:
        """
        Forces ANSI color output regardless of TTY detection (e.g., in Docker or CI).

        Automatically wraps stdout/stderr in colorama-compatible streams.
        """
        try:
            import colorama
            colorama.init(strip=False, convert=False)
            sys.stdout = colorama.AnsiToWin32(sys.stdout).stream
            sys.stderr = colorama.AnsiToWin32(sys.stderr).stream
            self._Color = colorama.Fore
            self._Style = colorama.Style
            self.__color_mode = True
            # Update color presets and reconfigure formatters
            self.presets = ColorPresets(self._Color, self._Style)
            self.flush_handlers()
            for handler in self.__logger_instance.handlers:
                handler.setFormatter(self.__get_formatter(self.__logger_instance.level))

            if self.__global_stream_configured:
                root_logger = logging.getLogger()
                for handler in root_logger.handlers:
                    handler.setFormatter(self.__get_formatter(root_logger.level))

            self.__logger_instance.info("[Logger] Forced color output enabled.")

        except ImportError:
            self.__logger_instance.warning("Colorama is not installed; cannot force color output.")


    # ---------------- Aliases ---------------- #
    def data(self, data, **kwargs):
        """
        Alias for `pretty_log()` used for structured or semantic logging.

        :param data: JSON-serializable object or printable value.
        :param kwargs: Optional formatting or indentation parameters.
        """
        return self.pretty_log(data, **kwargs)

    # ---------------- Deprecations ---------------- #
    @Deprecated(message="Use silence_logger() instead")
    def suppress_package_logger(self, package_name: str, level: int = logging.CRITICAL) -> None:
        """Routes to the new equivalent method: silence_logger()"""
        return self.silence_logger(package_name, level)

    @Deprecated(message="Use setLevel() to reconfigure logger")
    def revertLoggingLevel(self) -> None:
        """Routes to the equivalent functionality in the new API"""
        if hasattr(self, 'previous_level') and self.previous_level:
            self.setLevel(self.previous_level)
        else:
            self.setLevel("INFO")

    @Deprecated(message="Set force_stack_trace property directly")
    def set_global_traceback(self, setting: bool) -> None:
        """Routes to the equivalent property in the new API"""
        self.force_stack_trace = setting

    @Deprecated(message="Use header(compact=True) instead")
    def compact_header(self, text: str, size=40) -> None:
        """Maintains backward compatibility with old compact_header() method"""
        self.header(text, size, compact=True)

    @Deprecated(message="Use verbose_mode = True/False instead")
    def set_verbose(self, verbose: bool) -> None:
        """Maintains backward compatibility with old set_verbose() method"""
        self.verbose_mode = verbose

    @Deprecated(message="Use deployment_mode = True/False instead")
    def overwrite_lambda_mode(self, setting: bool) -> None:
        """Maintains backward compatibility with old overwrite_lambda_mode() method"""
        self.deployment_mode = setting

    @Deprecated(message="Use alternative file logging methods")
    def log_file(self, path: str, mode='a') -> None:
        """Deprecated method for backward compatibility"""
        pass

    @Deprecated(message="Use alternative file logging methods")
    def release_log_file(self) -> None:
        """Deprecated method for backward compatibility"""
        pass

    @Deprecated(message="Use info() instead")
    def context(self, *args, **kwargs):
        return self.info(*args, **kwargs)

    @Deprecated(message="Use info() instead")
    def flow(self, *args, **kwargs):
        return self.info(*args, **kwargs)

    @Deprecated(message="Use warning() instead")
    def log_handled_warning(self, *args, **kwargs):
        return self.warning(*args, **kwargs)

    @Deprecated(message="Use warning() instead")
    def log_hdl_warn(self, *args, **kwargs):
        return self.warning(*args, **kwargs)

    @Deprecated(message="Use error() instead")
    def log_handled_error(self, *args, **kwargs):
        return self.error(*args, **kwargs)

    @Deprecated(message="Use error() instead")
    def log_hdl_err(self, *args, **kwargs):
        return self.error(*args, **kwargs)

    @Deprecated(message="Use error() instead")
    def log_recoverable_error(self, *args, **kwargs):
        return self.error(*args, **kwargs)

    @Deprecated(message="Use error() instead")
    def log_recv_err(self, *args, **kwargs):
        return self.error(*args, **kwargs)

    @Deprecated(message="Use log_time() instead")
    def TIME(self, *args, **kwargs):
        return self.log_time(*args, **kwargs)




@SingletonClass
class _IntLogger(BaseLogger):
    pass

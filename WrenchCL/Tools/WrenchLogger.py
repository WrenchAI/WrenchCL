import io
import json
import logging
import os
import random
import string
import sys
import time
import traceback
from datetime import datetime, timedelta, date
from decimal import Decimal
from inspect import currentframe
from textwrap import fill
from typing import Any, Optional, Union

from ..Decorators import SingletonClass

try:
    from colorama import init
    from colorama import Fore as Color
    from colorama import Style

    colorama_imported = True
except ImportError:
    init = None
    Color = None
    Style = None
    colorama_imported = False
    logging.warning("colorama package not found. Colored logging is disabled.")

_srcfile = os.path.normcase(__file__)
_logging_src = os.path.normcase(logging.addLevelName.__code__.co_filename)


class BaseLogger:
    """
    Base class for custom logging with support for colorized output and advanced log handling.

    Provides methods for initializing loggers, managing log levels, and formatting logs with stack traces or
    additional contextual information.
    """

    def __init__(self, level: str = 'INFO') -> None:
        """
        Initializes the BaseLogger with a specified logging level.

        :param level: The desired logging level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        """
        self.non_verbose_mode = False
        self._start_time: Optional[float] = None
        self.run_id: str = self._generate_run_id()
        self.running_on_lambda: bool = 'AWS_LAMBDA_FUNCTION_NAME' in os.environ
        self.previous_level: Optional[int] = None
        self.logging_level: int = self._set_logging_level(level)
        self.force_stack_trace: bool = False
        self.logger: Optional[logging.Logger] = None
        self.console_handler: Optional[logging.Handler] = None
        self.file_handler: Optional[logging.Handler] = None

        # Custom log levels
        self.INFO_lvl = logging.INFO
        self.WARNING_lvl = logging.WARNING
        self.ERROR_lvl = logging.ERROR
        self.DEBUG_lvl = logging.DEBUG
        self.Critical_lvl = logging.CRITICAL
        self.CONTEXT_lvl = 21
        self.HDL_WARN_lvl = 31
        self.DATA_lvl = 33
        self.FLOW_lvl = 39
        self.HDL_ERR_lvl = 42
        self.RCV_ERR_lvl = 43

        # Adding custom levels
        logging.addLevelName(self.CONTEXT_lvl, "CONTEXT")
        logging.addLevelName(self.HDL_WARN_lvl, "HDL_WARN")
        logging.addLevelName(self.DATA_lvl, "DATA")
        logging.addLevelName(self.FLOW_lvl, "FLOW")
        logging.addLevelName(self.HDL_ERR_lvl, "HDL_ERR")
        logging.addLevelName(self.RCV_ERR_lvl, 'RCV_ERR')

    # Public Methods

    def suppress_package_logger(self, package_name: str, level: int = logging.CRITICAL) -> None:
        """
        Suppress logging for a specific package.

        :param package_name: The name of the package logger to suppress.
        :param level: The logging level to set for the package logger. Defaults to CRITICAL.
        """
        package_logger = logging.getLogger(package_name)
        package_logger.setLevel(level)
        package_logger.propagate = False

        if package_logger.handlers:
            for handler in package_logger.handlers:
                package_logger.removeHandler(handler)

        if not any(isinstance(handler, logging.NullHandler) for handler in package_logger.handlers):
            package_logger.addHandler(logging.NullHandler())

    def initiate_new_run(self) -> None:
        """
        Generates a new run ID for the current logger session.
        """
        self.run_id = self._generate_run_id()

    def set_verbose(self, verbose: bool) -> None:
        """
        Sets the logger to verbose or non-verbose mode.

        :param verbose: If True, enables verbose logging; otherwise, non-verbose logging is enabled.
        """
        self.non_verbose_mode = not verbose

    def setLevel(self, level: str) -> None:
        """
        Change the reporting level of the logger.

        :param level: The desired logging level as a string (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        """
        self.previous_level = self.logger.getEffectiveLevel() if self.logger else None
        numeric_level = self._set_logging_level(level)
        self.logger.setLevel(numeric_level)
        if self.file_handler:
            self.file_handler.setLevel(numeric_level)
        self.console_handler.setLevel(numeric_level)
        self.logging_level = numeric_level

    def set_global_traceback(self, setting: bool) -> None:
        """
        Enables or disables forced stack trace inclusion in logs.

        :param setting: If True, stack traces will be included in all logs.
        """
        self.force_stack_trace = setting

    def revertLoggingLevel(self) -> None:
        """
        Reverts the logger to the previous logging level before the last change.
        """
        if self.previous_level is None:
            self.previous_level = self.INFO_lvl
            print("No previous logging level saved, setting level to INFO.")
        self.logger.setLevel(self.previous_level)
        if self.file_handler:
            self.file_handler.setLevel(self.previous_level)
        self.console_handler.setLevel(self.previous_level)
        self.logging_level = self.previous_level

    def overwrite_lambda_mode(self, setting: bool) -> None:
        """
        Sets the logger to operate as if running on AWS Lambda.

        :param setting: If True, enables AWS Lambda mode.
        """
        self.running_on_lambda = setting

    # Non-Public Methods (Grouped Logically)

    def _generate_run_id(self) -> str:
        """Generates a unique run ID based on the current datetime."""
        date_seed = datetime.now().strftime("%y%m%d")
        random.seed(date_seed)
        random_part_1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        now = datetime.now()
        minute_second_seed = now.minute * 100 + now.second
        random.seed(minute_second_seed)
        random_part_2 = ''.join(random.choices(string.digits, k=4))
        return f"R-{random_part_1}-{random_part_2}"

    def _log(self, level: int, msg: str, stack_info: bool = False) -> None:
        """Handles the internal logging of messages, including stack trace formatting."""
        filepath_out, line_no_out, func_name_out, sinfo_out = self._findCaller(stack_info=stack_info)
        sinfo = None
        if stack_info:
            sinfo = f"\n ---Stack Trace--- \n {sinfo_out}" if str(traceback.format_exc()) == "NoneType: None\n" else f"\n ---Python Traceback--- \n {traceback.format_exc()}"
        record = self.logger.makeRecord(name=self.logger.name, level=level, fn=filepath_out, lno=line_no_out, msg=msg,
                                        exc_info=None, func=func_name_out, sinfo=sinfo, args=())
        self.logger.handle(record)

    def _log_with_color(self, level: int, text: str, color: Optional[str] = None,
                        stack_info: Optional[bool] = False, compact: Optional[bool] = False) -> None:
        """Logs a message with color formatting for better readability in the console."""
        indent_prefix = ': '
        prefix_col = Color.WHITE
        prefix_style = Style.DIM
        text_style = Style.NORMAL
        style_reset = Style.RESET_ALL
        if level == self.DATA_lvl and not self.running_on_lambda:
            header_style = Style.BRIGHT
            header_col = Color.LIGHTWHITE_EX
            text_col = Color.LIGHTWHITE_EX
        elif colorama_imported and color:
            header_style = Style.BRIGHT
            header_col = Color.LIGHTWHITE_EX
            text_col = Color.WHITE
        else:
            header_style = ""
            header_col = ""
            text_style = ""
            text_col = ""
            prefix_col = ""
            prefix_style = ""
            style_reset = ""

        lines = text.splitlines()
        colored_lines = [] if level != self.DATA_lvl else ['']
        if len(lines) == 1 or compact:
            colored_lines += [f"{header_col}{text_style}{' '.join(lines)}{style_reset}"]
        elif len(lines) <= 2:
            colored_lines += [f"{header_col}{header_style}{lines[0]}"]
            colored_lines += [
                f"{prefix_col}{prefix_style}{indent_prefix}{style_reset}{text_col}{text_style}{line}{style_reset}" for
                line in lines[1:]]
        else:
            colored_lines += [f"{header_col}{header_style}{lines[0]}"]
            colored_lines += [
                f"{prefix_col}{prefix_style}{idx + 1}:{style_reset} {text_col}{text_style}{line}{style_reset}" for
                idx, line in enumerate(lines[1:])]

        if level == self.DATA_lvl and len(lines) > 2:
            colored_lines += [f"{prefix_col}{prefix_style}---End of File----{style_reset}"]

        text = '\n'.join(colored_lines)
        if colorama_imported and color and not self.running_on_lambda:
            self._handlerFormat(color)
        elif self.running_on_lambda:
            text = " ".join(text.split())
            self._handlerFormat()
        else:
            self._handlerFormat()

        self._log(level, text, stack_info)

    def _format_data(self, data: Any, object_name: Optional[str] = None, content: bool = True,
                     wrap_length: Optional[int] = None, max_rows: Optional[int] = None, indent: int = 4) -> str:
        """Formats data for logging, applying wrapping and color formatting where applicable."""
        def serialize(obj):
            if isinstance(obj, dict):
                return {key: serialize(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [serialize(item) for item in obj]
            elif isinstance(obj, tuple):
                return tuple(serialize(item) for item in obj)
            elif isinstance(obj, set):
                return {serialize(item) for item in obj}
            elif isinstance(obj, str):
                return obj
            else:
                try:
                    return json.loads(json.dumps(obj, default=self._custom_serializer, indent=2))
                except TypeError:
                    return str(obj)

        try:
            import pandas as pd
        except ImportError:
            pd = None

        if isinstance(data, dict):
            prefix_str = f"DataType: {type(data).__name__} | Length: {len(data)}"
            formatted_text = json.dumps(serialize(data), indent=indent, default=self._custom_serializer)
        elif pd and isinstance(data, pd.DataFrame):
            prefix_str = f"DataType: {type(data).__name__} | Shape: {data.shape[0]} rows | {data.shape[1]} columns"
            with pd.option_context('display.max_rows', max_rows, 'display.max_columns', None):
                formatted_text = str(data)
        elif isinstance(data, (list, tuple, set)):
            prefix_str = f"DataType: {type(data).__name__} | Length: {len(data)}"
            formatted_text = json.dumps(serialize(data), indent=indent, default=self._custom_serializer)
        elif isinstance(data, str):
            prefix_str = f"DataType: {type(data).__name__} | Length: {len(data)}"
            formatted_text = data
        else:
            try:
                prefix_str = f"DataType: {type(data).__name__} | Length: {len(data)}"
            except TypeError:
                prefix_str = f"DataType: {type(data).__name__}"
            formatted_text = json.dumps(serialize(data), indent=indent, default=self._custom_serializer)

        if not content:
            formatted_text = ""
            wrapped_text = formatted_text
        elif wrap_length and not self.running_on_lambda:
            def wrap_with_indent(line, wrap_length):
                leading_whitespace = len(line) - len(line.lstrip())
                wrapped_lines = fill(line, width=wrap_length, subsequent_indent=' ' * leading_whitespace)
                return wrapped_lines

            wrapped_text = '\n'.join([wrap_with_indent(line, wrap_length) for line in formatted_text.splitlines()])
        else:
            wrapped_text = formatted_text

        if object_name is not None:
            final_text = f"--{object_name}--\n{wrapped_text}"
        else:
            final_text = wrapped_text

        return final_text

    def _is_internal_frame(self, frame) -> bool:
        """Checks if a frame is internal to CPython or the logging module."""
        filename = os.path.normcase(frame.f_code.co_filename)
        return filename == _srcfile or (
                "importlib" in filename and "_bootstrap" in filename) or filename == _logging_src

    def _findCaller(self, stack_info: bool = False, stacklevel: int = 1) -> tuple:
        """Finds the stack frame of the caller to extract file name, line number, and function name."""
        f = currentframe()
        if f is None:
            return "(unknown file)", 0, "(unknown function)", None
        orig_f = f
        while stacklevel > 0:
            next_f = f.f_back
            if next_f is None:
                break
            f = next_f
            if not self._is_internal_frame(f):
                stacklevel -= 1
        co = f.f_code
        sinfo = None
        if stack_info:
            with io.StringIO() as sio:
                sio.write("Stack (most recent call last):\n")
                traceback.print_stack(orig_f, file=sio)
                sinfo = sio.getvalue().strip()
        return co.co_filename, f.f_lineno, co.co_name, sinfo

    def _custom_serializer(self, obj: Any) -> str:
        """Custom serializer for objects that cannot be serialized by default."""
        try:
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            elif isinstance(obj, Exception):
                return f"{type(obj).__name__}: {str(obj)}"
            elif isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, bytes):
                return obj.decode('utf-8')
            elif isinstance(obj, str):
                return obj
            else:
                return str(obj)
        except:
            return str(obj)

    def _get_base_format(self) -> logging.Formatter:
        """Gets the base log format based on verbosity settings."""
        if not self.non_verbose_mode:
            return logging.Formatter(f"%(levelname)-8s: [{self.run_id}]"
                                     f"%(filename)s:%(funcName)s:%(lineno)d | "
                                     f"%(asctime)s | "
                                     f"%(message)s", datefmt='%Y-%m-%d %H:%M:%S')
        else:
            return logging.Formatter(f"%(levelname)-8s:"
                                     f"%(asctime)s | "
                                     f"%(message)s", datefmt='%Y-%m-%d %H:%M:%S')

    def _handlerFormat(self, color: Optional[str] = None) -> None:
        """Formats the handler with or without color based on settings."""
        if colorama_imported and color:
            reset_var = Style.RESET_ALL
            white_col = Color.LIGHTWHITE_EX
            if not self.non_verbose_mode:
                format_str = f"{color}%(levelname)-8s:  [{self.run_id}] %(filename)s:%(funcName)s:%(lineno)-4d | %(asctime)s | {white_col}%(message)s {reset_var}"
            else:
                format_str = f"{color}%(levelname)-8s: %(asctime)s | {white_col}%(message)s {reset_var}"
        else:
            if not self.non_verbose_mode:
                format_str = f"%(levelname)-8s: [{self.run_id}] %(filename)s:%(funcName)s:%(lineno)-4d | %(asctime)s | %(message)s"
            else:
                format_str = f"%(levelname)-8s: %(asctime)s | %(message)s"
        formatter = logging.Formatter(format_str, datefmt='%Y-%m-%d %H:%M:%S')
        if self.console_handler:
            self.console_handler.setFormatter(formatter)

    def _set_logging_level(self, level: Union[str, int]) -> int:
        """Sets the logging level based on a string or integer value."""
        if isinstance(level, str):
            level = level.lower()
            levels = {"debug": logging.DEBUG, "info": logging.INFO, "warning": logging.WARNING, "error": logging.ERROR,
                      "critical": logging.CRITICAL}
            if level not in levels:
                raise ValueError(f"Invalid logging level: {level}")
            return levels[level]
        elif isinstance(level, int):
            return level


@SingletonClass
class Logger(BaseLogger):
    """
    Logger class that extends BaseLogger with specific configuration for WrenchCL.

    Provides additional methods to configure log files and manages log handlers to avoid duplication.
    """

    def __init__(self, level: str = 'INFO') -> None:
        """
        Initializes the Logger with a specified logging level and configures console handler.

        :param level: The desired logging level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        """
        super().__init__(level)
        self.logger = logging.getLogger('WrenchCL')
        self.logger.setLevel(self.logging_level)
        self.console_handler = self._configure_console_handler()
        self.logger.handlers = []  # Clear existing handlers to avoid duplication
        self.logger.addHandler(self.console_handler)
        self.logger.propagate = False

    # non Public methods
    def _configure_console_handler(self) -> logging.StreamHandler:
        """
        Configures the console handler for logging to the stdout.

        Returns:
            logging.StreamHandler: Configured stream handler for console output.
        """
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.logging_level)
        handler.setFormatter(self._get_base_format())  # Use the base format depending on verbosity
        return handler

    # Public Methods

    def log_file(self, path: str, mode='a') -> None:
        """
        Configures logging to dump logs to the specified file while also logging to the console.

        :param path: The path to the file where logs should be saved.
        :param mode: The file operation mode that should be used to log
        """
        if self.file_handler:
            self.release_log_file()

        self.file_handler = logging.FileHandler(path, encoding='utf-8', mode=mode)
        self.file_handler.setLevel(self.logging_level)
        self.file_handler.setFormatter(self._get_base_format())
        self.logger.addHandler(self.file_handler)
        self.logger.info(f"Logging to file: {os.path.abspath(path)}")

    def release_log_file(self) -> None:
        """
        Releases file handler resources and stops logging to the file.
        """
        if self.file_handler:
            self.file_handler.close()
            self.logger.removeHandler(self.file_handler)
            self.file_handler = None
            self.logger.info("File logging stopped and resources released.")

    def info(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = True) -> None:
        """
        Logs an informational message.

        :param args: The message parts to log.
        :param stack_info: If True, includes stack trace information.
        :param compact: If True, condenses the message output.
        """
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.INFO_lvl, text, Color.GREEN if colorama_imported else None, stack_info, compact)

    def flow(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = True) -> None:
        """Logs a flow-level message."""
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.FLOW_lvl, text, Color.CYAN if colorama_imported else None, stack_info, compact)

    def context(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = True) -> None:
        """Logs a context-level message."""
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.CONTEXT_lvl, text, Color.MAGENTA if colorama_imported else None, stack_info, compact)

    def warning(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = True) -> None:
        """Logs a warning message."""
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.WARNING_lvl, text, Color.YELLOW if colorama_imported else None, stack_info, compact)

    def HDL_WARN(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = True) -> None:
        """Logs a handler warning message."""
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.HDL_WARN_lvl, text, Color.MAGENTA if colorama_imported else None, stack_info, compact)

    def error(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = False) -> None:
        """Logs an error message."""
        if any(isinstance(arg, Exception) for arg in args):
            stack_info = True
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.ERROR_lvl, text, Color.RED if colorama_imported else None, stack_info, compact)

    def data(self, data: Any, object_name: Optional[str] = None, content: Optional[bool] = True, wrap_length: Optional[int] = None,
             max_rows: Optional[int] = None, stack_info: Optional[bool] = False, indent: Optional[int] = 4) -> None:
        """Logs a data message with optional formatting."""
        object_name = object_name if object_name else f"Type: {type(data).__name__}"
        formatted_data = self._format_data(data, object_name, content, wrap_length, max_rows, indent=indent)
        self._log_with_color(self.DATA_lvl, formatted_data, Color.BLUE if colorama_imported else None, stack_info, False)

    def HDL_ERR(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = True) -> None:
        """Logs a handler error message."""
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.HDL_ERR_lvl, text, Color.LIGHTMAGENTA_EX if colorama_imported else None, stack_info, compact)

    def RECV_ERR(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = True) -> None:
        """Logs a recoverable error message."""
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.RCV_ERR_lvl, text, Color.LIGHTRED_EX if colorama_imported else None, stack_info, compact)

    def critical(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = False) -> None:
        """Logs a critical error message."""
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.Critical_lvl, text, Color.RED if colorama_imported else None, stack_info, compact)

    def debug(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = False) -> None:
        """Logs a debug message."""
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.DEBUG_lvl, text, Color.LIGHTWHITE_EX if colorama_imported else None, stack_info, compact)

    # Aliases
    log_info = INFO = info
    log_context = CONTEXT = context
    log_flow = FLOW = flow
    log_warning = WARNING = warning
    log_handled_warning = log_hdl_warn = HDL_WARN
    log_error = ERROR = error
    log_data = print_data = DATA = data
    log_handled_error = log_hdl_err = HDL_ERR
    log_recoverable_error = log_recv_err = RECV_ERR
    log_critical = CRITICAL = critical
    log_debug = DEBUG = debug

    def start_time(self) -> None:
        """Starts a timer for measuring elapsed time in logging."""
        self._start_time = time.time()

    def log_time(self, message: str = "Elapsed time", format: str = "seconds", stack_info: Optional[bool] = False) -> None:
        """
        Logs the elapsed time since the timer was started.

        :param message: Custom message for the elapsed time log.
        :param format: Format of the time ('seconds' or 'formatted').
        :param stack_info: If True, includes stack trace information.
        """
        if self._start_time is not None:
            elapsed_time = time.time() - self._start_time
            time_str = f"{elapsed_time:.2f} seconds" if format == "seconds" else str(timedelta(seconds=elapsed_time))
            self.info(f"{message}: {time_str}", stack_info=stack_info)
        else:
            self.warning("Timer was not started with start_time() before calling log_time().")

    TIME = log_time

    def compact_header(self, text: str, size: int = 40) -> None:
        """Logs a compact header message."""
        self.header(text, size, False)

    def header(self, text: str, size: int = 80, newline: bool = True) -> None:
        """
        Logs a header message with optional formatting.

        :param text: The header text to log.
        :param size: The size of the header.
        :param newline: If True, adds a newline before the header.
        """
        # Create the header text with optional color formatting
        header_text = text if not colorama_imported else f"{Color.CYAN}{Style.BRIGHT}{text}{Style.RESET_ALL}"

        # Save the current formatter to restore it later
        original_formatter = self.console_handler.formatter
        self.console_handler.setFormatter(logging.Formatter('%(message)s'))

        # Add a newline before the header if specified
        if newline:
            self.logger.info("")  # Logging an empty string to create a newline

        # Log the header message centered and surrounded by dashes
        self.logger.info(header_text.center(size, "-"))

        # Restore the original formatter
        self.console_handler.setFormatter(original_formatter)



# Provide backward compatibility
logger = Logger()

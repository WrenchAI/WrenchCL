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
    def __init__(self, level: str = 'INFO') -> None:
        self._start_time = None
        self.run_id = self._generate_run_id()
        self.running_on_lambda = 'AWS_LAMBDA_FUNCTION_NAME' in os.environ
        self.previous_level = None
        self.logging_level = logging.INFO
        self.non_verbose_mode = False
        self.console_handler = self._configure_console_handler()
        self.file_handler = None
        self._initialize_logger()
        self.logging_level = self._set_logging_level(level)
        self.force_stack_trace = False
        self.non_verbose_mode = False

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

        logging.addLevelName(self.CONTEXT_lvl, "CONTEXT")  # Backwards Support
        logging.addLevelName(self.HDL_WARN_lvl, "HDL_WARN")
        logging.addLevelName(self.DATA_lvl, "DATA")
        logging.addLevelName(self.FLOW_lvl, "FLOW")
        logging.addLevelName(self.HDL_ERR_lvl, "HDL_ERR")
        logging.addLevelName(self.RCV_ERR_lvl, 'RCV_ERR')


    def initiate_new_run(self):
        self.run_id = self._generate_run_id()

    def set_verbose(self, verbose: bool):
        if verbose:
            self.non_verbose_mode = False
        else:
            self.non_verbose_mode = True

    def setLevel(self, level: str) -> None:
        """
        Change the reporting level of the logger.

        Parameters:
            level (str): The desired logging level as a string (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        """
        self.previous_level = self.logger.getEffectiveLevel()
        numeric_level = self._set_logging_level(level)
        self.logger.setLevel(numeric_level)
        if self.file_handler:
            self.file_handler.setLevel(numeric_level)

        self.console_handler.setLevel(numeric_level)
        self.logging_level = numeric_level

    def set_global_traceback(self, setting: bool):
        self.force_stack_trace = setting

    def revertLoggingLevel(self):
        self.logger.setLevel(self.previous_level)
        if self.file_handler:
            self.file_handler.setLevel(self.previous_level)
        self.console_handler.setLevel(self.previous_level)
        self.logging_level = self.previous_level

    def overwrite_lambda_mode(self, setting: bool):
        self.running_on_lambda = setting

    @staticmethod
    def _generate_run_id():
        date_seed = datetime.now().strftime("%y%m%d")
        random.seed(date_seed)
        random_part_1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        now = datetime.now()
        minute_second_seed = now.minute * 100 + now.second
        random.seed(minute_second_seed)
        random_part_2 = ''.join(random.choices(string.digits, k=4))

        return f"R-{random_part_1}-{random_part_2}"

    def _log(self, level: int, msg: str, stack_info: bool = False) -> None:
        filepath_out, line_no_out, func_name_out, sinfo_out = self._findCaller(stack_info=stack_info)
        if stack_info:
            if str(traceback.format_exc()) != "NoneType: None\n":
                if colorama_imported:
                    sinfo = f"{Color.RED}{Style.BRIGHT} \n ---Stack Trace--- \n  {Style.RESET_ALL} {Color.LIGHTBLACK_EX}{Style.DIM} {sinfo_out} \n {Style.RESET_ALL} {Color.RED}{Style.BRIGHT} ---Python Traceback--- {Style.RESET_ALL}{Color.LIGHTBLACK_EX}{Style.DIM}\n {traceback.format_exc()} {Style.RESET_ALL}"
                else:
                    sinfo = f"\n ---Stack Trace--- \n {sinfo_out} \n ---Python Traceback--- \n {traceback.format_exc()}"
            else:
                if colorama_imported:
                    sinfo = f"\n {Color.RED}{Style.BRIGHT} ---Stack Trace--- \n{Style.RESET_ALL}  {Color.LIGHTBLACK_EX}{Style.DIM}{sinfo_out} \n {Style.RESET_ALL}"
                else:
                    sinfo = f"\n ---Stack Trace--- \n {sinfo_out}"
        else:
            sinfo = None

        record = self.logger.makeRecord(name=self.logger.name, level=level, fn=filepath_out, lno=line_no_out, msg=msg,
                                        exc_info=None, func=func_name_out, sinfo=sinfo, args=())

        self.logger.handle(record)

    def _log_with_color(self, level: int, text: str, color: Optional[str] = None,
            stack_info: Optional[bool] = False,  compact: Optional[bool] = False) -> None:
        indent_prefix = ': '
        prefix_col = Color.WHITE
        prefix_style = Style.DIM
        text_style = Style.NORMAL
        style_reset = Style.RESET_ALL
        if level == self.DATA_lvl:
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

        # Print the raw output for debugging

        self._log(level, text, stack_info)

    def _format_data(self, data, object_name=None, content=True, wrap_length=None, max_rows=None, indent=4):
        """Format data for logging, applying wrapping and color formatting where applicable."""

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

        # Determine the prefix based on the data type
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
            prefix_str = f"DataType: {type(data).__name__} | Length: {len(data)}"
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

        # Add color and whitespace for visual distinction
        if object_name is not None:
            final_text = f"--{object_name}--\n{wrapped_text}"
        else:
            final_text = wrapped_text

        return final_text

    @staticmethod
    def _is_internal_frame(frame):
        """Signal whether the frame is a CPython or logging module internal."""
        filename = os.path.normcase(frame.f_code.co_filename)
        return filename == _srcfile or (
                "importlib" in filename and "_bootstrap" in filename) or filename == _logging_src

    def _findCaller(self, stack_info=False, stacklevel=1):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number, and function name.
        """
        f = currentframe()
        if f is None:
            return "(unknown file)", 0, "(unknown function)", None
        orig_f = f  # Save the original frame for traceback
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

    @staticmethod
    def _custom_serializer(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Exception):
            return f"{type(obj).__name__}: {str(obj)}"
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, bytes):
            return obj.decode('utf-8')  # Decode bytes to string
        elif isinstance(obj, str):
            return obj
        else:
            return str(obj)

    def _get_base_format(self) -> logging.Formatter:
        if not self.non_verbose_mode:
            return logging.Formatter(f"%(levelname)-8s: [{self.run_id}]"
                                     f"%(filename)s:%(funcName)s:%(lineno)d | "
                                     f"%(asctime)s | "
                                     f"%(message)s", datefmt='%Y-%m-%d %H:%M:%S')
        else:
            return logging.Formatter(f"%(levelname)-8s:"
                                          f"%(asctime)s | "
                                          f"%(message)s", datefmt='%Y-%m-%d %H:%M:%S')

    @staticmethod
    def _set_logging_level(level: Union[str, int]) -> int:
        if isinstance(level, str):
            level = level.lower()
            levels = {"debug": logging.DEBUG, "info": logging.INFO, "warning": logging.WARNING, "error": logging.ERROR,
                      "critical": logging.CRITICAL}
            if level not in levels:
                raise ValueError(f"Invalid logging level: {level}")
            return levels[level]
        elif isinstance(level, int):
            return level

    def _configure_console_handler(self):
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.logging_level)
        handler.setFormatter(self._get_base_format())  # Apply the formatter here
        return handler

    def _initialize_logger(self) -> None:
        self.logger = logging.getLogger()
        self.logger.setLevel(self.logging_level)

        # Ensure there are no other handlers overriding the settings
        self.logger.handlers = []  # Clear existing handlers

        self.logger.addHandler(self.console_handler)

        if colorama_imported and not self.running_on_lambda:
            init(autoreset=True)

    def _handlerFormat(self, color: Optional[str] = None) -> None:
        if colorama_imported and color:
            if 'hex_color_palette' not in locals():
                reset_var = Style.RESET_ALL
                white_col = Color.LIGHTWHITE_EX
                if not self.non_verbose_mode:
                    format_str = f"{color}%(levelname)-8s:  [{self.run_id}] %(filename)s:%(funcName)s:%(lineno)-4d | %(asctime)s | {white_col}%(message)s {reset_var}"
                else:
                    format_str = f"{color}%(levelname)-8s: %(asctime)s | {white_col}%(message)s {reset_var}"
            else:
                reset_var = Style.RESET_ALL
                white_col = Color.RESET
                if not self.non_verbose_mode:
                    format_str = f"{color}%(levelname)-8s: [{self.run_id}] %(filename)s:%(funcName)s:%(lineno)-4d | %(asctime)s |{reset_var} \x1b[38;20m %(message)s \x1b[0m"
                else:
                    format_str = f"{color}%(levelname)-8s: %(asctime)s |{reset_var} \x1b[38;20m %(message)s \x1b[0m"
        else:
            if not self.non_verbose_mode:
                format_str = f"%(levelname)-8s: [{self.run_id}] %(filename)s:%(funcName)s:%(lineno)-4d | %(asctime)s | %(message)s"
            else:
                format_str = f"%(levelname)-8s: %(asctime)s | %(message)s"
        formatter = logging.Formatter(format_str, datefmt='%Y-%m-%d %H:%M:%S')
        self.console_handler.setFormatter(formatter)


@SingletonClass
class FileLogger(BaseLogger):
    def __init__(self, level: str = 'INFO', log_location: Optional[str] = None) -> None:
        super().__init__(level)
        self.file_logging = True
        self.filename = self._set_filename(log_location)
        self.file_handler = self._configure_file_handler()
        self.logger.addHandler(self.file_handler)

    @staticmethod
    def _set_filename(file_name_append_mode: Optional[str] = None) -> str:
        def find_project_root(anchor='.git') -> str:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            while current_dir != os.path.dirname(current_dir):
                if os.path.exists(os.path.join(current_dir, anchor)):
                    return current_dir
                current_dir = os.path.dirname(current_dir)
            return os.getcwd()

        root_folder = find_project_root()
        log_dir = os.path.join(root_folder, 'resources', 'logs')
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except PermissionError:
                log_dir = os.getcwd()
            except OSError:
                log_dir = os.getcwd()
            except Exception as e:
                raise e

        if file_name_append_mode:
            log_file_name = os.path.abspath(file_name_append_mode)
        elif root_folder == os.getcwd():
            log_file_name = 'python.log'
        else:
            timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
            log_file_name = f'log-{timestamp}.log'

        return os.path.join(log_dir, log_file_name)

    def _configure_file_handler(self) -> Optional[logging.FileHandler]:
        try:
            if self.filename:
                handler = logging.FileHandler(self.filename, encoding='utf-8')
                handler.setLevel(self.logging_level)
                handler.setFormatter(self._get_base_format())
                return handler
            else:
                return None
        except (PermissionError, FileNotFoundError) as e:
            logging.error(f"Error setting up file handler: {e}")
            return None

    def release_resources(self) -> None:
        """Releases file handler resources."""
        if self.file_handler:
            self.file_handler.close()
            self.logger.removeHandler(self.file_handler)

    def set_log_file_location(self, new_append_mode: Optional[str or None] = None) -> None:
        if self.file_logging and new_append_mode is not None:
            old_filename = self.filename
            self.filename = self._set_filename(new_append_mode)
            self._reconfigure_file_handler()

            if old_filename is not None:
                with open(old_filename, 'r') as old_file, open(self.filename, 'a') as new_file:
                    new_file.write(old_file.read())
                os.remove(old_filename)
        elif not self.file_logging:
            # self.set_file_logging(True)
            self.filename = self._set_filename(new_append_mode)
            self._reconfigure_file_handler()
        else:
            pass

    def _reconfigure_file_handler(self) -> None:
        if self.file_handler:
            self.file_handler.close()
            self.logger.removeHandler(self.file_handler)

        self.file_handler = self._configure_file_handler()
        if self.file_handler:
            self.logger.addHandler(self.file_handler)


@SingletonClass
class Logger(BaseLogger):
    def __init__(self, level: str = 'INFO') -> None:
        super().__init__(level)

    def info(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = True) -> None:
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.INFO_lvl, text, Color.GREEN if colorama_imported else None, stack_info, compact)

    def flow(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = True) -> None:
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.FLOW_lvl, text, Color.CYAN if colorama_imported else None, stack_info, compact)

    def context(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = True) -> None:
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.CONTEXT_lvl, text, Color.MAGENTA if colorama_imported else None, stack_info, compact)

    def warning(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = True) -> None:
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.WARNING_lvl, text, Color.YELLOW if colorama_imported else None, stack_info, compact)

    def HDL_WARN(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = True) -> None:
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.HDL_WARN_lvl, text, Color.MAGENTA if colorama_imported else None, stack_info, compact)

    def error(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = False) -> None:
        if any(isinstance(arg, Exception) for arg in args):
            stack_info = True
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.ERROR_lvl, text, Color.RED if colorama_imported else None, stack_info, compact)

    def data(self, data: Any, object_name: Optional[str] = None, content: Optional[bool] = True, wrap_length: Optional[int] = None,
            max_rows: Optional[int] = None, stack_info: Optional[bool] = False, indent: Optional[int] = 4) -> None:
        object_name = object_name if object_name else f"Type: {type(data).__name__}"
        formatted_data = self._format_data(data, object_name, content, wrap_length, max_rows, indent=indent)
        self._log_with_color(self.DATA_lvl, formatted_data, Color.BLUE if colorama_imported else None, stack_info, False)

    def HDL_ERR(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = True) -> None:
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.HDL_ERR_lvl, text, Color.LIGHTMAGENTA_EX if colorama_imported else None, stack_info, compact)

    def RECV_ERR(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = True) -> None:
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.RCV_ERR_lvl, text, Color.LIGHTRED_EX if colorama_imported else None, stack_info, compact)

    def critical(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = False) -> None:
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.Critical_lvl, text, Color.RED if colorama_imported else None, stack_info, compact)

    def debug(self, *args: Any, stack_info: Optional[bool] = False, compact: Optional[bool] = False) -> None:
        serialized_args = [self._custom_serializer(arg) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(self.DEBUG_lvl, text, Color.LIGHTWHITE_EX if colorama_imported else None, stack_info, compact)

    log_info = INFO = info  # Aliases for info
    log_context = CONTEXT = context # Aliases for Context
    log_flow = FLOW = flow  # Aliases for flow
    log_warning = WARNING = warning  # Aliases for warning
    log_handled_warning = log_hdl_warn = HDL_WARN  # Aliases for HDL_WARN
    log_error = ERROR = error  # Aliases for error
    log_data = print_data = DATA = data
    log_handled_error = log_hdl_err = HDL_ERR  # Aliases for HDL_ERR
    log_recoverable_error = log_recv_err = RECV_ERR  # Aliases for RECV_ERR
    log_critical = CRITICAL = critical  # Aliases for critical
    log_debug = DEBUG = debug  # Aliases for debug

    def start_time(self):
        self._start_time = time.time()

    def log_time(self, message: str = "Elapsed time", format: str = "seconds", stack_info: Optional[bool] = False):
        if hasattr(self, '_start_time'):
            elapsed_time = time.time() - self._start_time
            if format == "seconds":
                time_str = f"{elapsed_time:.2f} seconds"
            elif format == "formatted":
                td = timedelta(seconds=elapsed_time)
                time_str = str(td)
            else:
                self.warning("Invalid format specified for log_time(). Defaulting to seconds.")
                time_str = f"{elapsed_time:.2f} seconds"

            self.info(f"{message}: {time_str}", stack_info=stack_info)
        else:
            self.warning("Timer was not started with start_time() before calling log_time().")

    TIME = log_time

    def compact_header(self, text, size=40):
        self.header(text, size, False, )

    def header(self, text: str, size: int = 80, newline: bool = True) -> None:
        header = text if not colorama_imported else f"{Color.CYAN}{Style.BRIGHT}{text}{Style.RESET_ALL}"
        self.console_handler.setFormatter(logging.Formatter(f'%(message)s'))
        if newline:
            logging.info("\n")
        logging.info(header.center(size, "-"))
        self._handlerFormat()


# Provide backward compatibility
logger = None


def initialize_logger():
    global logger
    logger = Logger()


# Lazy instantiation of the logger for backward compatibility
if 'logger' in sys.modules:
    initialize_logger()

#  Copyright (c) $YEAR$. Copyright (c) $YEAR$ Wrench.AI., Willem van der Schans, Jeong Kim
#
#  MIT License
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#  All works within the Software are owned by their respective creators and are distributed by Wrench.AI.
#
#  For inquiries, please contact Willem van der Schans through the official Wrench.AI channels or directly via GitHub at [Kydoimos97](https://github.com/Kydoimos97).
#

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
from textwrap import fill
from typing import Any, Optional

try:
    from colorama import init, Fore as ColoramaFore, Style as ColoramaStyle

    colorama_imported = True
except ImportError:
    colorama_imported = False
    logging.warning("colorama package not found. Colored logging is disabled.")


def LoggerSingleton(cls):
    """
    Decorator for a class to implement the Singleton pattern. This decorator ensures that only one instance of the
    decorated class can exist at any time. If an instance of the class already exists, it returns that instance;
    otherwise, it creates and returns a new instance.

    The Singleton pattern is particularly useful when exactly one object is needed to coordinate actions across the
    system, such as in the case of managing database connections.

    :param cls: The class to be decorated as a Singleton.
    :type cls: type
    :returns: A wrapper function that manages the instantiation of the singleton class, ensuring that only one
              instance exists.
    :rtype: function

    **Example**::

        >>> @SingletonClass
        ... class DatabaseManager:
        ...     def __init__(self, connection_string):
        ...         self.connection_string = connection_string
        ...
        >>> db_manager1 = DatabaseManager('db_connection_string')
        >>> db_manager2 = DatabaseManager('db_connection_string')
        >>> assert db_manager1 is db_manager2  # Both variables point to the same instance
    """
    instances = {}

    def get_instance(*args, **kwargs):
        """
        Returns the singleton instance of the class, creating it if it does not already exist.

        :param args: Positional arguments for the class constructor.
        :param kwargs: Keyword arguments for the class constructor.
        :returns: The singleton instance of the class.
        """
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance



@LoggerSingleton
class _wrench_logger:

    def __init__(self, level: str = 'INFO', file_logging=False, file_name_append_mode: Optional[str] = None) -> None:
        self._start_time = None
        self.run_id = self._generate_run_id()
        self.running_on_lambda = 'AWS_LAMBDA_FUNCTION_NAME' in os.environ
        self.previous_level = None
        self.file_logging = file_logging
        self.base_format = self._get_base_format()
        self.logging_level = self._set_logging_level(level)
        if self.file_logging:
            self.filename = self._set_filename(file_name_append_mode)
            self.file_handler = self._configure_file_handler()
        else:
            self.file_handler = None
            self.filename = None
        self.console_handler = self._configure_console_handler()
        self._initialize_logger()
        self._initialized = True
        self.force_stack_trace = False

        logging.addLevelName(21, "CONTEXT")
        logging.addLevelName(31, "HDL_WARN")
        logging.addLevelName(41, "DATA")
        logging.addLevelName(42, "HDL_ERR")
        logging.addLevelName(43, 'RCV_ERR')

    def initiate_new_run(self):
        self.run_id = self._generate_run_id()

    @staticmethod
    def _generate_run_id():
        # Current date in YYMMDD format
        date_seed = datetime.now().strftime("%y%m%d")  # 6 characters
        random.seed(date_seed)
        random_part_1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        now = datetime.now()
        minute_second_seed = now.minute * 100 + now.second
        random.seed(minute_second_seed)
        random_part_2 = ''.join(random.choices(string.digits, k=4))

        return f"R-{random_part_1}-{random_part_2}"

    def overwrite_lambda_mode(self, setting: bool):
        self.running_on_lambda = setting

    def set_global_traceback(self, setting: bool):
        self.force_stack_trace = setting

    def release_resources(self) -> None:
        """Releases file handler resources."""
        if self.file_handler:
            self.file_handler.close()
            self.logger.removeHandler(self.file_handler)

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

    def revertLoggingLevel(self):
        self.logger.setLevel(self.previous_level)
        if self.file_handler:
            self.file_handler.setLevel(self.previous_level)
        self.console_handler.setLevel(self.previous_level)
        self.logging_level = self.previous_level

    def set_file_logging(self, file_logging: bool):
        self.file_logging = file_logging
        if not self.file_logging:
            self.release_resources()
        if self.file_logging:
            self.file_handler = self._configure_file_handler()
        self._initialize_logger()

    def set_log_file_location(self, new_append_mode: Optional[str or None] = None) -> None:
        """
        Change the file append mode, copy content from the old file to the new one,
        and optionally delete the old file.

        Parameters:
            new_append_mode (str): The new append mode for the log filename.
        """
        if self.file_logging and new_append_mode is not None:
            # Get the old file's name
            old_filename = self.filename

            # Set the new append mode and update the filename
            self.filename = self._set_filename(new_append_mode)

            # Reconfigure file handler to use the new filename
            self._reconfigure_file_handler()

            # Copy the content of the old file to the new one
            if old_filename is not None:
                with open(old_filename, 'r') as old_file, open(self.filename, 'a') as new_file:
                    new_file.write(old_file.read())
                # Optionally, delete the old file
                os.remove(old_filename)
        elif not self.file_logging:
            self.set_file_logging(True)
            # Set the new append mode and update the filename
            self.filename = self._set_filename(new_append_mode)
            # Reconfigure file handler to use the new filename
            self._reconfigure_file_handler()
        else:
            pass

    # Main Functional Methods
    def _log(self, level: int, msg: str, stack_info: bool = False) -> None:
        # Initialize stack_level_index
        stack_level_index = 1
        stack_trace = " --> InternalLogFrames"
        last_level = ""
        write_flag = False
        match_counter = 0
        filepath_out, line_no_out, func_name_out, sinfo_out = self.logger.findCaller(stack_info=stack_info,
                                                                                     stacklevel=stack_level_index)
        if stack_level_index == 1:
            first_index = f"{filepath_out}:{func_name_out}:{line_no_out}"
        # Loop to find the caller
        while stack_level_index:
            filepath, line_no, func_name, sinfo = self.logger.findCaller(stack_info=stack_info,
                                                                         stacklevel=stack_level_index)
            if f"{filepath}:{func_name}:{line_no}" != last_level and (
                    f"{filepath}:{func_name}:{line_no}" != first_index or stack_level_index == 1):
                match_counter = 0
                if self.running_on_lambda:
                    stack_trace = stack_trace + f" <-- {stack_level_index}|{os.path.basename(filepath)}:{func_name}:{line_no}"
                else:
                    stack_trace = stack_trace + f"\n -- {stack_level_index}|{os.path.basename(filepath)}:{func_name}:{line_no}"
                last_level = f"{filepath}:{func_name}:{line_no}"

                if write_flag is False and not self._is_internal_frame(os.path.normpath(filepath)):
                    filepath_out, line_no_out, func_name_out, sinfo_out = self.logger.findCaller(stack_info=stack_info,
                                                                                                 stacklevel=stack_level_index)
                    write_flag = True
            else:
                match_counter += 1
            if self._is_internal_frame(os.path.normpath(filepath)) and match_counter <= 5:
                stack_level_index += 1
                continue
            else:
                break

        # Handle stack_info
        if stack_info:
            if str(traceback.format_exc()) != "NoneType: None\n":
                if colorama_imported:
                    sinfo = f"\n ---Stack Trace--- \n {ColoramaFore.LIGHTBLACK_EX} {stack_trace[4:]} \n {ColoramaFore.RESET} ---Python Traceback--- {ColoramaFore.LIGHTBLACK_EX}\n {traceback.format_exc()} {ColoramaFore.RESET}"
                else:
                    sinfo = f"\n ---Stack Trace--- \n {stack_trace[4:]} \n ---Python Traceback--- \n {traceback.format_exc()}"
            else:
                sinfo = f"Stack Trace: {self._format_data(stack_trace[4:], stack_trace=True)}"
        else:
            sinfo = None

        # Create and handle the log record
        record = self.logger.makeRecord(name=self.logger.name, level=level, fn=filepath_out, lno=line_no_out, msg=msg,
            args=None, exc_info=None, func=func_name_out, sinfo=sinfo)
        self.logger.handle(record)

    def _log_with_color(self, level: int, text: str, color: Optional[str] = None,
                        stack_info: Optional[bool] = False) -> None:
        indent_prefix = '  -->    '  # Custom indent prefix for new lines
        if level <= 15:
            text_col = ColoramaFore.LIGHTWHITE_EX
        else:
            text_col = ColoramaFore.WHITE

        if colorama_imported and color and not self.running_on_lambda:
            # Apply color to each line and indent new lines
            lines = text.splitlines()
            colored_lines = [f"{lines[0]}"]
            colored_lines += [f"{text_col}{indent_prefix}{line}{ColoramaStyle.RESET_ALL}" for line in lines[1:]]
            text = '\n'.join(colored_lines)
            self._handlerFormat(color)

        elif self.running_on_lambda:

            # Join lines with a separator for AWS Lambda
            text = " ".join(text.split())
            self._handlerFormat()  # Use default handler format
        else:
            self._handlerFormat()  # Use default handler format

        if self.force_stack_trace and level >= 30:
            stack_info = True

        self._log(level, text, stack_info)

    def info(self, *args: str, stack_info: Optional[bool] = False) -> None:
        """Log information that might be helpful but isn't essential."""
        serialized_args = [str(self._custom_serializer(arg)) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(logging.INFO, text, ColoramaFore.LIGHTGREEN_EX if colorama_imported else None, stack_info)

    log_info = INFO = info  # Aliases for info

    def context(self, *args: str, stack_info: Optional[bool] = False) -> None:
        """Log contextual information for better understanding of the flow."""
        serialized_args = [str(self._custom_serializer(arg)) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(21, text, ColoramaFore.LIGHTMAGENTA_EX if colorama_imported else None, stack_info)

    log_context = CONTEXT = context  # Aliases for context

    def warning(self, *args: str, stack_info: Optional[bool] = False) -> None:
        """Log issues that aren't errors but might warrant investigation."""
        serialized_args = [str(self._custom_serializer(arg)) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(logging.WARNING, text, ColoramaFore.YELLOW if colorama_imported else None, stack_info)

    log_warning = WARNING = warning  # Aliases for warning

    def HDL_WARN(self, *args: str, stack_info: Optional[bool] = False) -> None:
        """Log warnings that have been handled and do not require further action."""
        serialized_args = [str(self._custom_serializer(arg)) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(31, text, ColoramaFore.MAGENTA if colorama_imported else None, stack_info)

    log_handled_warning = log_hdl_warn = HDL_WARN  # Aliases for HDL_WARN

    def error(self, *args: str, stack_info: Optional[bool] = False) -> None:
        """Log errors that could disrupt normal program flow."""
        serialized_args = [str(self._custom_serializer(arg)) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(logging.ERROR, text, ColoramaFore.RED if colorama_imported else None, stack_info)

    log_error = ERROR = error  # Aliases for error

    def data(self, data: Any, content: Optional[bool] = True, wrap_length: Optional[int] = None, max_rows: Optional[int] = None,
            stack_info: Optional[bool] = False, indent: Optional[int] = 4) -> None:
        """Log Data in a lower contrast, handling formatting for readability."""
        formatted_data = self._format_data(data, content, wrap_length, max_rows, indent=indent)
        self._log_with_color(41, formatted_data, ColoramaFore.LIGHTWHITE_EX if colorama_imported else None, stack_info)

    log_data = print_data = DATA = data

    def HDL_ERR(self, *args: str, stack_info: Optional[bool] = False) -> None:
        """Log errors that have been handled but still need to be reported."""
        serialized_args = [str(self._custom_serializer(arg)) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(42, text, ColoramaFore.LIGHTMAGENTA_EX if colorama_imported else None, stack_info)

    log_handled_error = log_hdl_err = HDL_ERR  # Aliases for HDL_ERR

    def RECV_ERR(self, *args: str, stack_info: Optional[bool] = False) -> None:
        """Log errors from which the system can recover with or without manual intervention."""
        serialized_args = [str(self._custom_serializer(arg)) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(43, text, ColoramaFore.LIGHTRED_EX if colorama_imported else None, stack_info)

    log_recoverable_error = log_recv_err = RECV_ERR  # Aliases for RECV_ERR

    def critical(self, *args: str, stack_info: Optional[bool] = False) -> None:
        """Log critical issues that require immediate attention."""
        serialized_args = [str(self._custom_serializer(arg)) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(logging.CRITICAL, text, ColoramaFore.RED if colorama_imported else None, stack_info)

    log_critical = CRITICAL = critical  # Aliases for critical

    def debug(self, *args: str, stack_info: Optional[bool] = False) -> None:
        """Log detailed information, typically of interest only when diagnosing problems."""
        serialized_args = [str(self._custom_serializer(arg)) for arg in args]
        text = ' '.join(serialized_args)
        self._log_with_color(logging.DEBUG, text, ColoramaFore.CYAN if colorama_imported else None, stack_info)

    log_debug = DEBUG = debug  # Aliases for debug

    # Formatting Methods

    def _format_data(self, data, content=True, wrap_length=None, max_rows=None, color=True, stack_trace=False, indent = 4):
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
        if colorama_imported and color and not self.running_on_lambda:
            if not stack_trace:
                final_text = f"\n{ColoramaFore.LIGHTBLUE_EX}{prefix_str}\n{ColoramaFore.LIGHTBLACK_EX}{wrapped_text}{ColoramaFore.RESET}\n"
            else:
                final_text = f"\n{ColoramaFore.LIGHTBLACK_EX}{wrapped_text}{ColoramaFore.RESET}\n"
        elif not self.running_on_lambda:
            final_text = f"\n\n{wrapped_text}\n"
        else:
            # In environments like AWS Lambda, where color might not be supported or desired
            final_text = wrapped_text

        return final_text

    @staticmethod
    def _custom_serializer(obj):
        """JSON serializer for objects not serializable by default JSON code"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        elif isinstance(obj, str):
            return obj
        else:
            return str(obj)  # Fallback for other types

    @staticmethod
    def _wrap_text(text: str, wrap_length: int) -> str:
        import textwrap
        return '\n'.join(textwrap.wrap(text, wrap_length))

    def _log_header(self, text: str, size: int = 80, newline: bool = True) -> None:
        """
        Logs a header text, centered and separated by dashes.

        Parameters:
            text (str): The header text.
            size (int, optional): The width of the header. Default is 80.
            newline (bool, optional): Whether to prepend a newline before the header. Default is True.
        """
        header = text
        if self.file_handler:
            self.file_handler.setFormatter(logging.Formatter(f'%(message)s'))
        self.console_handler.setFormatter(logging.Formatter(f'%(message)s'))
        if newline:
            logging.info("\n")
        logging.info(header.center(size, "-"))  # Print header centered in 80 characters
        if self.file_handler:
            self.file_handler.setFormatter(self.base_format)
        self._handlerFormat()

    def _handlerFormat(self, color: Optional[str] = None) -> None:
        """
        Configures the console handler's formatter with optional color.

        Parameters:
            color (str, optional): The color code for colorama. Default is None.
        """
        if colorama_imported and color:
            if 'hex_color_palette' not in locals() and color != ColoramaFore.LIGHTWHITE_EX:
                reset_var = ColoramaStyle.RESET_ALL
                white_col = ColoramaFore.LIGHTWHITE_EX
                format_str = f"{color}%(levelname)-8s:  [{self.run_id}] %(filename)s:%(funcName)s:%(lineno)-4d | %(asctime)s | {white_col}%(message)s {reset_var}"
            elif 'hex_color_palette' not in locals() and color == ColoramaFore.LIGHTWHITE_EX:
                reset_var = ColoramaStyle.RESET_ALL
                format_str = f"{color}-----%(levelname)s----- %(message)s{reset_var}"
            else:
                reset_var = ColoramaStyle.RESET_ALL
                white_col = ColoramaFore.RESET
                format_str = f"{color}%(levelname)-8s: [{self.run_id}] %(filename)s:%(funcName)s:%(lineno)-4d | %(asctime)s |{reset_var} \x1b[38;20m %(message)s \x1b[0m"
        else:
            format_str = f"%(levelname)-8s: [{self.run_id}] %(filename)s:%(funcName)s:%(lineno)-4d | %(asctime)s | %(message)s"

        self.console_handler.setFormatter(logging.Formatter(format_str, datefmt='%Y-%m-%d %H:%M:%S'))

    def _reconfigure_file_handler(self) -> None:
        """
        Reconfigure the file handler to use the updated filename.
        """
        # Close and remove the old file handler
        if self.file_handler:
            self.file_handler.close()
            self.logger.removeHandler(self.file_handler)

        # Configure the new file handler with the updated filename
        self.file_handler = self._configure_file_handler()
        if self.file_handler:
            self.logger.addHandler(self.file_handler)

    # Supplementary Methods
    def header(self, text: str, size: int = 80, newline: bool = True) -> None:
        """
        Logs a header, similar to `_log_header`, but intended for external use.

        Parameters:
            text (str): The header text.
            size (int): The width of the header.
            newline (bool, optional): Whether to prepend a newline before the header. Default is True.
        """
        self._log_header(text, size, newline)

    def compact_header(self, text, size=40):
        self.header(text, size, False, )

    # Private Utility Methods
    @staticmethod
    def _is_internal_frame(filepath: str) -> bool:
        check_strs = ['WrenchLogger.py', '_pytest']
        end_strs = ['__init__.py']

        for cstr in check_strs:
            if cstr in filepath:
                return True

        for estr in end_strs:
            if filepath.lower().endswith(estr):
                return True

        return False

    def _get_base_format(self) -> logging.Formatter:
        """
        Returns a logging formatter with a specific format.

        Returns:
            logging.Formatter: A logging formatter with a predefined format and date format.
        """
        return logging.Formatter(f"%(levelname)-8s: [{self.run_id}]"
                                 f"%(filename)s:%(funcName)s:%(lineno)d | "
                                 f"%(asctime)s | "
                                 f"%(message)s", datefmt='%Y-%m-%d %H:%M:%S')

    @staticmethod
    def _set_logging_level(level: str) -> int:
        """
        Converts a logging level string to its corresponding logging level constant.

        Parameters:
            level (str): The logging level as a string.

        Returns:
            int: The logging level constant from the `logging` module.
        """
        level = level.lower()
        levels = {"debug": logging.DEBUG, "info": logging.INFO, "warning": logging.WARNING, "error": logging.ERROR,
                  "critical": logging.CRITICAL}
        if level not in levels:
            raise ValueError(f"Invalid logging level: {level}")
        return levels[level]

    @staticmethod
    def _set_filename(file_name_append_mode: Optional = None) -> str:
        """
    Generates the log file name based on the provided `file_name_append_mode`.

    Parameters:
        file_name_append_mode (str or None): Additional information to append to the log file name.

    Returns:
        str: The log file name with a directory path.
    """

        def find_project_root(anchor='.git') -> str:
            """Finds the project root by searching for a specified anchor. If not found, returns the current working directory."""
            current_dir = os.path.dirname(os.path.abspath(__file__))
            while current_dir != os.path.dirname(current_dir):  # Stop when reaching the root directory
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
                log_dir = os.getcwd()  # If creation of the log directory fails, use the current working directory
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

    # Configuration Methods
    def _configure_file_handler(self) -> Optional[logging.FileHandler]:
        """
        Configures and returns a file handler for logging.

        Returns:
            logging.FileHandler: Configured file handler for logging.

        Raises:
            PermissionError, FileNotFoundError: If an error occurs while setting up the file handler.
        """
        try:
            if self.filename:
                handler = logging.FileHandler(self.filename, encoding='utf-8')
                handler.setLevel(self.logging_level)
                handler.setFormatter(self.base_format)
                return handler
            else:
                return None
        except (PermissionError, FileNotFoundError) as e:
            logging.error(f"Error setting up file handler: {e}")
            return None

    def _configure_console_handler(self):
        """
        Configures and returns a console handler for logging.

        Returns:
            logging.StreamHandler: Configured console handler for logging.
        """
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.logging_level)
        return handler

    def _initialize_logger(self) -> None:
        """
        Initializes the logger with file and console handlers, and sets the logging level.
        Adjusts initialization based on the running environment.
        """
        self.logger = logging.getLogger()
        self.logger.setLevel(self.logging_level)

        # Clear existing handlers in the AWS Lambda environment to avoid duplicates
        if self.running_on_lambda:
            self.logger.handlers = []  # Clear existing handlers

        if self.file_logging and self.file_handler:
            self.logger.addHandler(self.file_handler)

        self.logger.addHandler(self.console_handler)

        # Initialize colorama for colorful output if not running on AWS Lambda
        if colorama_imported and not self.running_on_lambda:
            init()

    def start_time(self):
        """Start a timer for performance measurement."""
        self._start_time = time.time()

    def log_time(self, message: str = "Elapsed time", format: str = "seconds", stack_info: Optional[bool] = False):
        """
        Log the elapsed time since start_time() was called with an optional message.
        
        Args:
        - message: The message to prefix the time with.
        - format: The format to display the time in ("seconds" or "formatted").
        - stack_info: Whether to include stack info.
        """
        if hasattr(self, '_start_time'):
            elapsed_time = time.time() - self._start_time
            if format == "seconds":
                time_str = f"{elapsed_time:.2f} seconds"
            elif format == "formatted":
                # Convert seconds to a timedelta object, then format as days, hours, minutes, and seconds
                td = timedelta(seconds=elapsed_time)
                time_str = str(td)
            else:
                self.warning("Invalid format specified for log_time(). Defaulting to seconds.")
                time_str = f"{elapsed_time:.2f} seconds"

            self.info(f"{message}: {time_str}", stack_info)
        else:
            self.warning("Timer was not started with start_time() before calling log_time().")

    # Alias for log_time
    Time = log_time


logger = _wrench_logger()

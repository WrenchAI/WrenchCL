import logging
import os
import sys
from datetime import datetime
import traceback
from typing import Any, Optional

try:
    from colorama import init, Fore as ColoramaFore, Style as ColoramaStyle
    colorama_imported = True
except ImportError:
    colorama_imported = False
    logging.warning("colorama package not found. Colored logging is disabled.")

class _wrench_logger:
    _instance = None

    # Lifecycle Methods
    def __new__(cls, *args: Any, **kwargs: Any) -> 'log':
        """
        Implement the Singleton pattern to ensure a single instance per unique combination of `level` and `file_name_append_mode`.
        """
        if cls._instance is None:
            cls._instance = super(_wrench_logger, cls).__new__(cls)
        return cls._instance

    def __init__(self, level: str = 'INFO', file_logging=False, file_name_append_mode: Optional[str] = None) -> None:
        if hasattr(self, '_initialized'):  # Check if __init__ has been called before
            return  # If yes, do nothing
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
        stack_level_index = 0
        stack_trace = " --> InternalLogFrames"
        last_level = ""
        # Loop to find the caller
        while True:
            filepath, line_no, func_name, sinfo = self.logger.findCaller(stack_info=stack_info,
                                                                         stacklevel=stack_level_index)
            if self._is_internal_frame(filepath):
                stack_level_index += 1
                continue
            elif stack_info and f"{filepath}:{func_name}:{line_no}" != last_level:
                stack_trace = f" --> {stack_level_index}|{os.path.basename(filepath)}:{func_name if func_name != '<module>' else '<callerFunc>'}:{line_no}" + stack_trace
                stack_level_index += 1
                last_level = f"{filepath}:{func_name}:{line_no}"
                continue
            else:
                break
        # Handle stack_info
        if stack_info and str(traceback.format_exc()) != "NoneType: None\n":
            sinfo = f"Stack Trace: {stack_trace[4:]} \n{traceback.format_exc()}"
        elif stack_info:
            sinfo = f"Stack Trace: {stack_trace[4:]}"
        else:
            sinfo = None

        # Create and handle the log record
        record = self.logger.makeRecord(
            self.logger.name, level, filepath, line_no,
            msg, None, None, func_name, sinfo=sinfo
        )
        self.logger.handle(record)

    def _log_with_color(self, level: int, text: str, color: Optional[str] = None,
                        stack_info: Optional[bool] = False) -> None:
        if colorama_imported and color and not self.running_on_lambda:
            self._handlerFormat(color)
        self._log(level, text, stack_info)
        if colorama_imported or self.running_on_lambda:
            self._handlerFormat()

    def info(self, text: str, stack_info: Optional[bool] = False) -> None:
        self._log_with_color(logging.INFO, text, ColoramaFore.LIGHTGREEN_EX if colorama_imported else None, stack_info)

    def context(self, text: str, stack_info: Optional[bool] = False) -> None:
        self._log_with_color(logging.INFO, text, ColoramaFore.MAGENTA if colorama_imported else None, stack_info)


    def warning(self, text: str, stack_info: Optional[bool] = False) -> None:
        self._log_with_color(logging.WARNING, text, ColoramaFore.YELLOW if colorama_imported else None, stack_info)

    def error(self, text: str, stack_info: Optional[bool] = False) -> None:
        self._log_with_color(logging.ERROR, text, ColoramaFore.LIGHTRED_EX if colorama_imported else None, stack_info)

    def critical(self, text: str, stack_info: Optional[bool] = False) -> None:
        self._log_with_color(logging.CRITICAL, text, ColoramaFore.RED if colorama_imported else None, stack_info)

    def debug(self, text: str, stack_info: Optional[bool] = False) -> None:
        self._log_with_color(logging.DEBUG, text, ColoramaFore.LIGHTBLUE_EX if colorama_imported else None, stack_info)

    # Formatting Methods
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
            if 'hex_color_palette' not in locals():
                reset_var = ColoramaStyle.RESET_ALL
                white_col = ColoramaFore.LIGHTWHITE_EX
                format_str = f"{color}%(levelname)-8s: %(filename)s:%(funcName)s:%(lineno)-4d | %(asctime)s | {white_col}%(message)s{reset_var}"
            else:
                reset_var = ColoramaStyle.RESET_ALL
                white_col = ColoramaFore.RESET
                format_str = f"{color}%(levelname)-8s: %(filename)s:%(funcName)s:%(lineno)-4d | %(asctime)s |{reset_var} \x1b[38;20m %(message)s \x1b[0m"
        else:
            format_str = f"%(levelname)-8s: %(filename)s:%(funcName)s:%(lineno)-4d | %(asctime)s | %(message)s"

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

    # Private Utility Methods
    @staticmethod
    def _is_internal_frame(filepath: str) -> bool:
        """Check if the frame is internal to logging or WrenchLogger."""
        normalized_filepath = os.path.normcase(filepath)
        return '\\logging\\' in normalized_filepath or '\\wrenchlogger.py' in normalized_filepath.lower()

    @staticmethod
    def _get_base_format() -> logging.Formatter:
        """
        Returns a logging formatter with a specific format.

        Returns:
            logging.Formatter: A logging formatter with a predefined format and date format.
        """
        return logging.Formatter(f"%(levelname)-8s: "
                                 f"%(filename)s:%(funcName)s:%(lineno)d | "
                                 f"%(asctime)s | "
                                 f"%(message)s",
                                 datefmt='%Y-%m-%d %H:%M:%S')

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


wrench_logger = _wrench_logger()

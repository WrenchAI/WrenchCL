import logging
import os
import sys
from datetime import datetime
import traceback
from typing import Any, Optional, Union

try:
    from colorama import init, Fore as ColoramaFore, Style as ColoramaStyle

    colorama_imported = True
except ImportError:
    colorama_imported = False
    logging.warning("colorama package not found. Colored logging is disabled.")


class _wrench_logger:
    """
    Logger Class for Configuring Logging with File and Console Handlers.

    This class is designed to be a Singleton, meaning it will only allow one instance per unique combination of `level` and `file_name_append_mode`. It provides a configurable logging utility that supports both file-based and console-based logging. It utilizes Python's built-in `logging` module and optionally integrates with the `colorama` package for colored console outputs.

    How to Use:
    -----------
    1. Import the instantiated object:
        ```python
        from your_module import wrench_logger
        ```

    2. Use the logger to log messages:
        ```python
        wrench_logger.info("This is an info message.")
        wrench_logger.warning("This is a warning message.")
        wrench_logger.error("This is an error message.")
        wrench_logger.critical("This is a critical message.")
        wrench_logger.debug("This is a debug message.")
        ```

    3. Log exceptions and tracebacks:
        ```python
        try:
            # some code that raises an exception
        except Exception as e:
            wrench_logger.log_traceback(e)
        ```

    4. Log headers for better readability:
        ```python
        wrench_logger.header("Your Header Text", size=80)
        ```

    5. Release resources when done:
        ```python
        wrench_logger.release_resources()
        ```

    Attributes:
    -----------
    - logging_level (int): The logging level for both file and console handlers.
    - base_format (logging.Formatter): The default logging format.
    - filename (str): The name of the log file.
    - file_handler (logging.FileHandler): File handler for logging.
    - console_handler (logging.StreamHandler): Console handler for logging.
    - logger (logging.Logger): The underlying logger object.

    Methods:
        Lifecycle Methods:
            __new__(cls, *args, **kwargs): Implements the Singleton pattern.
            __init__(level, file_name_append_mode): Initializes the logger.
            release_resources(): Releases file handler resources.

        Main Functional Methods:
            _log(level, msg): Logs a message at a specific logging level.
            _log_with_color(level, text, color): Logs a message with optional color.
            info(text): Logs an informational message.
            warning(text): Logs a warning message.
            error(text): Logs an error message.
            critical(text): Logs a critical message.
            debug(text): Logs a debug message.

        Formatting Methods:
            _log_header(text, size, newline): Logs a header text, centered and separated by dashes.
            _handlerFormat(color): Configures the console handler's formatter with optional color.

        Supplementary Methods:
            log_traceback(exception): Logs the traceback of an exception.
            header(text, size, newline): Logs a header, similar to `_log_header`, but intended for external use.

        Private Utility Methods:
            _get_base_format(): Returns a logging formatter with a specific format.
            _set_logging_level(level): Converts a logging level string to its corresponding constant.
            _set_filename(file_name_append_mode): Generates the log file name.

        Configuration Methods:
            _configure_file_handler(): Configures and returns a file handler for logging.
            _configure_console_handler(): Configures and returns a console handler for logging.
            _initialize_logger(): Initializes the logger with file and console handlers.
    """
    _instances = {}

    # Lifecycle Methods
    def __new__(cls, *args: Any, **kwargs: Any) -> 'log':
        """
        Implement the Singleton pattern to ensure a single instance per unique combination of `level` and `file_name_append_mode`.
        """
        level = kwargs.get('level', 'INFO')
        file_name_append_mode = kwargs.get('file_name_append_mode', None)
        key = hash((level, file_name_append_mode))
        if key not in cls._instances:
            instance = super(_wrench_logger, cls).__new__(cls)
            cls._instances[key] = instance
        return cls._instances[key]

    def __init__(self, level: str = 'INFO', file_name_append_mode: Optional[str] = None) -> None:
        self.base_format = self._get_base_format()
        self.logging_level = self._set_logging_level(level)
        self.filename = self._set_filename(file_name_append_mode)
        self.file_handler = self._configure_file_handler()
        self.console_handler = self._configure_console_handler()

        self._initialize_logger()

    def release_resources(self) -> None:
        """Releases file handler resources."""
        if self.file_handler:
            self.file_handler.close()
            self.logger.removeHandler(self.file_handler)

    # Main Functional Methods
    def _log(self, level: int, msg: str) -> None:
        """
        Logs a message at a specific logging level.

        Parameters:
            level (int): The logging level for the message.
            msg (str): The message to be logged.
        """
        if self.logger.isEnabledFor(level):
            caller_info = self.logger.findCaller(stack_info=False)
            record = self.logger.makeRecord(
                self.logger.name, level, caller_info[0], caller_info[1],
                msg, None, None, caller_info[2], None
            )
            self.logger.handle(record)

    def _log_with_color(self, level: int, text: str, color: Optional[str] = None) -> None:
        if colorama_imported and color:
            self._handlerFormat(color)
        self._log(level, text)
        if colorama_imported:
            self._handlerFormat()

    def info(self, text: str) -> None:
        self._log_with_color(logging.INFO, text, ColoramaFore.LIGHTGREEN_EX if colorama_imported else None)

    def warning(self, text: str) -> None:
        self._log_with_color(logging.WARNING, text, ColoramaFore.YELLOW if colorama_imported else None)

    def error(self, text: str) -> None:
        self._log_with_color(logging.ERROR, text, ColoramaFore.LIGHTRED_EX if colorama_imported else None)

    def critical(self, text: str) -> None:
        self._log_with_color(logging.CRITICAL, text, ColoramaFore.RED if colorama_imported else None)

    def debug(self, text: str) -> None:
        self._log_with_color(logging.DEBUG, text, ColoramaFore.LIGHTBLUE_EX if colorama_imported else None)

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
        self.file_handler.setFormatter(logging.Formatter(f'%(message)s'))
        self.console_handler.setFormatter(logging.Formatter(f'%(message)s'))
        if newline:
            logging.info("\n")
        logging.info(header.center(size, "-"))  # Print header centered in 80 characters
        self.file_handler.setFormatter(self.base_format)
        self._handlerFormat()

    def _handlerFormat(self, color: Optional[str] = None) -> None:
        """
        Configures the console handler's formatter with optional color.

        Parameters:
            color (str, optional): The color code for colorama. Default is None.
        """
        if colorama_imported and color:
            reset_var = ColoramaStyle.RESET_ALL
            white_col = ColoramaFore.LIGHTWHITE_EX
            format_str = f"{color}%(levelname)-8s: %(filename)s:%(funcName)s:%(lineno)-4d | %(asctime)s | {white_col}%(message)s{reset_var}"
        else:
            format_str = f"%(levelname)-8s: %(filename)s:%(funcName)s:%(lineno)-4d | %(asctime)s | %(message)s"

        self.console_handler.setFormatter(logging.Formatter(format_str, datefmt='%Y-%m-%d %H:%M:%S'))

    # Supplementary Methods
    def log_traceback(self, exception: Exception) -> None:
        """
        Logs the traceback of an exception.

        Parameters:
            exception (Exception): The caught exception.
        """
        tb = traceback.format_exc()
        self.logger.error(f"Exception: {exception}\nTraceback:\n{tb}")

    def header(self, text: str, size: int, newline: bool = True) -> None:
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
    def _set_filename(file_name_append_mode: Optional[str]) -> str:
        """
        Generates the log file name based on the provided `file_name_append_mode`.

        Parameters:
            file_name_append_mode (str or None): Additional information to append to the log file name.

        Returns:
            str: The log file name with a directory path.
        """
        # root_folder = os.path.abspath(os.path.join(os.getcwd(), '..'))
        root_folder = os.getcwd()
        log_dir = os.path.abspath(os.path.join(root_folder, f'../resources/logs/'))
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        if file_name_append_mode is None:
            timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
            return os.path.abspath(os.path.join(log_dir, f'log-{timestamp}.log'))
        else:
            return os.path.abspath(os.path.join(log_dir, file_name_append_mode.replace('/', '_')))

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
            handler = logging.FileHandler(self.filename)
            handler.setLevel(self.logging_level)
            handler.setFormatter(self.base_format)
            return handler
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
        """
        self.logger = logging.getLogger()
        self.logger.setLevel(self.logging_level)
        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.console_handler)

        if colorama_imported:
            init()

wrench_logger = _wrench_logger()

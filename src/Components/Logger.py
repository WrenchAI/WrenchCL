import logging
import sys
from datetime import datetime
import traceback
from colorama import init, Fore as ColoramaFore, Style as ColoramaStyle


class Logger:
    """
    Logger class for configuring logging with file and console handlers.

    Attributes:
        base_format: A logging formatter for the default logging format.
        file_handler: A handler to write log messages to a file.
        console_handler: A handler to write log messages to the console.

    Methods:
        _log_header: Private method to log the header information.
        _handlerFormat: Private method to set the formatter for the console handler with color.
    """

    def __init__(self, level='INFO', file_name_append_mode=None):
        logging_level = None
        self.base_format = logging.Formatter(f"%(levelname)-8s: "
                                             f"%(filename)s:%(lineno)d | "
                                             f"%(asctime)s | "
                                             f"%(message)s",
                                             datefmt='%Y-%m-%d %H:%M:%S')
        level = str(level)
        if file_name_append_mode is None:
            timestamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
            filename = f'resources/logs/log-{timestamp}.log'
        else:
            if 'resources/logs/' not in file_name_append_mode:
                filename = 'resources/logs/' + file_name_append_mode.replace('/', '_')
            else:
                filename = file_name_append_mode

        if level.lower() in ['debug', 'info', 'warning', 'error', 'critical']:
            if level.lower() == "debug":
                logging_level = logging.DEBUG
            elif level.lower() == "info":
                logging_level = logging.INFO
            elif level.lower() == 'warning':
                logging_level = logging.WARNING
            elif level.lower() == 'error':
                logging_level = logging.ERROR
            elif level.lower() == 'critical':
                logging_level = logging.CRITICAL
        else:
            print("Invalid value given for logging level reverting to lowest level")
            logging_level = logging.DEBUG

        # Initialize colorama
        init()

        # Configure logging to save to file
        self.file_handler = logging.FileHandler(filename)
        self.file_handler.setLevel(logging_level)
        self.file_handler.setFormatter(self.base_format)

        # Configure console handler
        self.console_handler = logging.StreamHandler(sys.stdout)
        self.console_handler.setLevel(logging_level)
        self._handlerFormat()

        # Create logger and add handlers
        self.logger = logging.getLogger()
        self.logger.setLevel(logging_level)
        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.console_handler)

        self._log_header(f" Run Initialized at {datetime.now()} ", 80)

    def _log_header(self, text, size = 80, newline = True):
        header = text
        self.file_handler.setFormatter(logging.Formatter(f'%(message)s'))
        self.console_handler.setFormatter(logging.Formatter(f'%(message)s'))
        if newline:
            logging.info("\n")
        logging.info(header.center(size, "-"))  # Print header centered in 80 characters
        self.file_handler.setFormatter(self.base_format)
        self._handlerFormat()

    def _handlerFormat(self, color=ColoramaFore.MAGENTA):
        reset_var = ColoramaStyle.RESET_ALL
        white_col = ColoramaFore.LIGHTWHITE_EX
        return self.console_handler.setFormatter(logging.Formatter(
            f"{color}%(levelname)-8s: "
            f"%(filename)s:%(lineno)-4d | %(asctime)s | "
            f"{white_col}%(message)s{reset_var}",
            datefmt='%Y-%m-%d %H:%M:%S'))


class writeLog(Logger):

    def info(self, text):
        self._handlerFormat(ColoramaFore.LIGHTGREEN_EX)
        logging.info(text)
        self._handlerFormat()

    def warning(self, text):
        self._handlerFormat(ColoramaFore.YELLOW)
        logging.warning(text)
        self._handlerFormat()

    def error(self, text):
        self._handlerFormat(ColoramaFore.LIGHTRED_EX)
        logging.error(text)
        self._handlerFormat()

    def critical(self, text):
        self._handlerFormat(ColoramaFore.RED)
        logging.critical(text)
        self._handlerFormat()

    def debug(self, text):
        self._handlerFormat(ColoramaFore.LIGHTBLUE_EX)
        logging.debug(text)
        self._handlerFormat()

    def header(self, text, size, newline = True):
        self._log_header(text, size, newline)



class ErrorHandler:
    def __init__(self, logger):
        self.logger = logger

    def log_error(self, error_message):
        self.logger.error(error_message)

    def log_traceback(self, exception):
        tb = traceback.format_exc()
        self.logger.error(f"Exception: {exception}\nTraceback:\n{tb}")

    # Case specific error codes and returns

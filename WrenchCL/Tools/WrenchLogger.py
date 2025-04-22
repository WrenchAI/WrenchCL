import importlib
import inspect
import logging
import os
import re
import sys
import time
import json
from datetime import datetime
from types import TracebackType
from typing import Any, Optional, Union, Literal, Type
from difflib import get_close_matches

from .._Internal._MockPandas import MockPandas
from ..Decorators.Deprecated import Deprecated
from ..Decorators.SingletonClass import SingletonClass

try:
    import pandas as pd
except ImportError:
    pd = MockPandas()


class ExceptionSuggestor:
    @staticmethod
    def suggest_similar(error_msg: str, frame_depth=20, n_suggestions=1, cutoff=0.6) -> Optional[str]:
        obj_match = re.search(r"'(\w+)' object has no attribute", error_msg)
        key_match = re.search(r"has no attribute '(\w+)'", error_msg)
        if not key_match:
            return None

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
                        return f"Did you mean: {', '.join(matches)}?"
        return None


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
        else:
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


_exc_info_type = None | bool | tuple[Type[BaseException], BaseException, TracebackType | None] | tuple[
    None, None, None] | BaseException


class BaseLogger:
    def __init__(self, level: str = 'INFO') -> None:
        self.__global_stream_configured = False
        self.run_id = self._generate_run_id()
        self._compact_mode = False
        self._verbose_mode = False
        self._highlight_syntax = True
        self._start_time = None

        self._logger_instance = logging.getLogger('WrenchCL')
        self._running_on_lambda = 'AWS_LAMBDA_FUNCTION_NAME' in os.environ
        self._check_colorama()
        self.presets = ColorPresets(self._Color, self._Style)
        self._setup(level)

    def update_color_presets(self, **kwargs) -> None:
        self.presets.update(**kwargs)

    def initiate_new_run(self):
        self.run_id = self._generate_run_id()

    def setLevel(self, level: Literal["DEBUG", "INFO", 'WARNING', 'ERROR', 'CRITICAL']) -> None:
        self._logger_instance.setLevel(self._get_level(level))

    def info(self, *args, exc_info: _exc_info_type = None, stack_info: bool = False) -> None:
        self._log(logging.INFO, *args, exc_info=exc_info, stack_info=stack_info)

    def warning(self, *args, exc_info: _exc_info_type = None, stack_info: bool = False) -> None:
        self._log(logging.WARNING, *args, exc_info=exc_info, stack_info=stack_info)

    def error(self, *args, exc_info: _exc_info_type = None, stack_info: bool = True) -> None:
        args = list(args)
        suggestion = self._suggest_exception(args)
        if suggestion:
            args.append(suggestion)
        self._log(logging.ERROR, *args, exc_info=exc_info, stack_info=stack_info)

    def critical(self, *args, exc_info: _exc_info_type = None, stack_info: bool = True) -> None:
        args = list(args)
        suggestion = self._suggest_exception(args)
        if suggestion:
            args.append(suggestion)
        self._log(logging.CRITICAL, *args, exc_info=exc_info, stack_info=stack_info)

    def debug(self, *args, exc_info: _exc_info_type = None, stack_info: bool = False) -> None:
        self._log(logging.DEBUG, *args, exc_info=exc_info, stack_info=stack_info)

    def _internal_log(self, *args, exc_info: _exc_info_type = None, stack_info: bool = False) -> None:
        self._log(logging.INFO, *args, exc_info=exc_info, stack_info=stack_info, compact_mode=False,
                  color_flag="INTERNAL")

    def start_time(self) -> None:
        self._start_time = time.time()

    def log_time(self, message="Elapsed time") -> None:
        if self._start_time:
            elapsed = time.time() - self._start_time
            self.info(f"{message}: {elapsed:.2f}s")

    def header(self, text: str, size=80, compact=False) -> None:
        text = text.replace('_', ' ').replace('-', ' ').strip().capitalize()
        if compact:
            size = 40
            formatted = self._apply_color(text, self.presets.HEADER).center(size, "-")
        else:
            size = 80
            formatted = "\n\n" + self._apply_color(text, self.presets.HEADER).center(size, "-") + "\n"
        self._logger_instance.info(formatted)

    def pretty_log(self, obj: Any, indent=4, **kwargs) -> None:
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
                output = json.dumps(obj.json(), indent=indent, **kwargs)
            elif isinstance(obj, dict):
                output = json.dumps(obj, indent=indent, **kwargs)
            elif isinstance(obj, str):
                try:
                    output = json.dumps(json.loads(obj), indent=indent, **kwargs, default=str)
                except Exception:
                    output = str(obj)
            else:
                output = str(obj)
        except Exception as e:
            output = str(obj)
        self._log(logging.INFO, output, exc_info=False, compact_mode=False, color_flag="DATA")

    # ---------------- Internals ---------------- #
    def _log(self, level: Union[int, str], *args, exc_info: _exc_info_type = None, stack_info: bool = False,
            compact_mode: bool = False, color_flag: Optional[Literal['INTERNAL', 'DATA']] = None) -> None:
        msg = '\n'.join(str(arg) for arg in args)
        msg = self._highlight_literals(msg, data=color_flag == 'DATA')
        if self.lambda_mode or self.compact_mode or compact_mode:
            lines = msg.splitlines()
            msg = ' '.join([line.strip() for line in lines if len(line.strip()) > 0])
            msg = msg.replace('\n', ' ').replace('\r', '').strip()

        if color_flag == 'INTERNAL':
            level = "INTERNAL"
        elif color_flag == 'DATA':
            level = "DATA"

        for handler in self._logger_instance.handlers:
            handler.setFormatter(self._get_formatter(level))

        lines = msg.splitlines()
        if len(lines) > 1:
            msg = "\n    " + "\n    ".join(lines)
        if exc_info:
            msg = "\n".join(lines)

        if isinstance(level, str):
            level = self._get_level(level)

        self._logger_instance.log(level, msg, exc_info=exc_info, stack_info=stack_info, stacklevel=self._get_depth())

    def _highlight_literals(self, msg: str, data: bool = False) -> str:
        if not self.colorama_enabled or not self._highlight_syntax:
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

    def _get_depth(self) -> int():
        for i, frame in enumerate(inspect.stack()):
            if frame.filename.endswith("WrenchLogger.py") or 'WrenchCL' in frame.filename or frame.filename == '<string>':
                continue
            return i

    def _suggest_exception(self, args) -> str | None:
        suggestion = None
        if args and isinstance(args[-1], Exception):
            ex = args[-1]
            if hasattr(ex, 'args') and ex.args and isinstance(ex.args[0], str):
                suggestion = ExceptionSuggestor.suggest_similar(ex.args[0])
        return suggestion

    def _apply_color(self, text: str, color: Optional[str]) -> str:
        return f"{color}{self.presets.BRIGHT}{text}{self.presets.RESET}" if color else text

    def _log_setup_summary(self) -> None:
        settings = self.logger_state
        msg = '⚙️  Logger Configuration:\n'

        msg += f"  • Logging Level: {self._apply_color(logging.getLevelName(settings['Logging Level']), self.presets.get_color_by_level(settings['Logging Level']))}\n"
        msg += f"  • Run ID: {settings['Run Id']}\n"

        msg += "  • Mode Flags:\n"
        for mode, enabled in settings["Logging Modes"].items():
            state = "✓ Enabled" if enabled else "✗ Disabled"
            color = self.presets.INFO if enabled else self.presets.ERROR
            msg += f"      - {mode:20s}: {self._apply_color(state, color)}\n"

        msg += self.presets.get_demo_string()  # Use the actual instance, not the dict
        self._logger_instance.info(msg)


    @staticmethod
    def _generate_run_id() -> str:
        now = datetime.now()
        return f"R-{os.urandom(1).hex().upper()}{now.strftime('%m%d')}{os.urandom(1).hex().upper()}"

    def _get_level(self, level: Union[str, int]) -> int:
        if isinstance(level, str) and hasattr(logging, level.upper()):
            return getattr(logging, level.upper())
        elif isinstance(level, int):
            return level
        return logging.INFO

    def _get_formatter(self, level: Union[str, int], no_format=False) -> logging.Formatter:
        color = self.presets.get_color_by_level(level)
        style = self.presets.get_level_style(level)
        message_color = self.presets.get_message_color(level)
        dimmed_color = self.presets.get_color_by_level('INTERNAL')
        dimmed_style = self.presets.get_level_style('INTERNAL')

        run_id_section = f"{self.run_id}|" if self.verbose_mode else ""
        verbose_section = f"{dimmed_color}{dimmed_style}[%(asctime)s|{run_id_section}%(filename)s:%(funcName)s:%(lineno)d]{self.presets.RESET}"
        level_name_section = f"{color}{style}%(levelname)-8s{self.presets.RESET}"
        colored_dash_section = f"{color}{style} -- {self.presets.RESET}"
        colored_arrow_section = f"{color}{style} -> {self.presets.RESET}"
        message_section = f"{style}{message_color}%(message)s{self.presets.RESET}"

        if level == "INTERNAL":
            level_name_section = f"{color}{style}INTERNAL{self.presets.RESET}"
        elif level == "DATA":
            level_name_section = f"{color}{style}DATA    {self.presets.RESET}"

        if self.compact_mode:
            fmt = f"{level_name_section}{colored_arrow_section}{message_section}"
        elif no_format:
            fmt = "%(message)s"
        else:
            fmt = f"{level_name_section}{verbose_section}{colored_arrow_section}{message_section}"

        return CustomFormatter(fmt, datefmt='%H:%M:%S', presets=self.presets)

    def _check_colorama(self) -> None:
        if self._running_on_lambda:
            self._Color = MockColorama
            self._Style = MockColorama
            self._colorama_imported = False
        else:
            try:
                colorama = importlib.import_module("colorama")
                self._Color = colorama.Fore
                self._Style = colorama.Style
                colorama.init(strip=self._running_on_lambda)
                self._colorama_imported = True
            except ImportError:
                self._Color = MockColorama
                self._Style = MockColorama
                self._colorama_imported = False

    def _setup(self, level: str) -> None:
        self._logger_instance.setLevel(self._get_level(level))
        handler = logging.StreamHandler(sys.stdout)
        self._logger_instance.handlers = [handler]
        self._logger_instance.propagate = False

    # ---------------- Properties ---------------- #

    @property
    def logger_instance(self) -> logging.Logger:
        return self._logger_instance

    @property
    def colorama_enabled(self) -> bool:
        return self._colorama_imported

    @property
    def lambda_mode(self) -> bool:
        return self._running_on_lambda

    @lambda_mode.setter
    def lambda_mode(self, val: bool) -> None:
        self._running_on_lambda = val
        self._check_colorama()

    @property
    def compact_mode(self) -> bool:
        return self._compact_mode

    @compact_mode.setter
    def compact_mode(self, val: bool) -> None:
        self._compact_mode = val

    @property
    def verbose_mode(self) -> bool:
        return self._verbose_mode

    @verbose_mode.setter
    def verbose_mode(self, val: bool) -> None:
        self._verbose_mode = val

    @property
    def logger_state(self) -> dict:
        return {"Logging Level": self._logger_instance.level, "Run Id": self.run_id,
                "Logging Modes": {"Global Streaming Mode": self.__global_stream_configured,
                                  "Lambda mode": self.lambda_mode, "Color Mode": self.colorama_enabled,
                                  "Compact Mode": self.compact_mode, "Verbose Mode": self.verbose_mode, "Highlight Syntax": self._highlight_syntax},
                "Color Settings": self.presets.__dict__,

                }

    def display_logger_state(self) -> None:
        self._log_setup_summary()

    # Add this property for external access to presets
    @property
    def color_presets(self) -> ColorPresets:
        return self.presets

    @property
    def highlight_syntax(self) -> bool:
        return self._highlight_syntax

    @highlight_syntax.setter
    def highlight_syntax(self, val: bool) -> None:
        self._highlight_syntax = val

    # ---------------- Global Settings ---------------- #
    def configure_global_stream(self, level: str = "INFO", silence_others: bool = False, stream = sys.stdout) -> None:

        """
            Overrides the global logging stream with this logger's handler and formatter.
            Optionally silences other loggers to prevent duplicate or noisy logs.
            """
        root_logger = logging.getLogger()
        root_logger.setLevel(self._get_level(level))

        handler = logging.StreamHandler(stream)
        handler.setFormatter(self._get_formatter(level))  # Use your formatter

        root_logger.handlers = [handler]
        root_logger.propagate = False

        if silence_others:
            self.silence_other_loggers()

        self.__global_stream_configured = True
        self._logger_instance.info("[Logger] Global stream configured successfully.")

    def silence_logger(self, logger_name: str, level: Optional[int] = None) -> None:
        """
        Silences a specific logger by name by attaching a NullHandler and disabling propagation.
        """
        logger = logging.getLogger(logger_name)
        logger.handlers = [logging.NullHandler()]
        if not level:
            logger.setLevel(logging.CRITICAL + 1)
        else:
            logger.setLevel(level)
        logger.propagate = False

    def silence_other_loggers(self, level: Optional[int] = None) -> None:
        """
        Silences all non-root, non-WrenchCL loggers.
        """
        for name in logging.root.manager.loggerDict:
            if name != 'WrenchCL':
                self.silence_logger(name, level)

    def force_color(self) -> None:
        """
        Forces color output even if stdout is not a TTY.
        Useful for environments like Docker or CI where ANSI detection fails.
        """
        try:
            import colorama
            colorama.init(strip=False, convert=False)
            sys.stdout = colorama.AnsiToWin32(sys.stdout).stream
            sys.stderr = colorama.AnsiToWin32(sys.stderr).stream
            self._Color = colorama.Fore
            self._Style = colorama.Style
            self._colorama_imported = True

            # Update color presets and reconfigure formatters
            self.presets = ColorPresets(self._Color, self._Style)
            for handler in self._logger_instance.handlers:
                handler.setFormatter(self._get_formatter(self._logger_instance.level))

            if self.__global_stream_configured:
                root_logger = logging.getLogger()
                for handler in root_logger.handlers:
                    handler.setFormatter(self._get_formatter(root_logger.level))

            self._logger_instance.info("[Logger] Forced color output enabled.")

        except ImportError:
            self._logger_instance.warning("Colorama is not installed; cannot force color output.")


    # ---------------- Aliases ---------------- #
    def data(self, data, **kwargs):
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

    @Deprecated(message="Use lambda_mode = True/False instead")
    def overwrite_lambda_mode(self, setting: bool) -> None:
        """Maintains backward compatibility with old overwrite_lambda_mode() method"""
        self.lambda_mode = setting

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

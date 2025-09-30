#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
import logging

from .DataClasses import logLevels, LogLevel


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
        super().__setattr__('COLOR_BRACE_OPEN', getattr(self._color_class, 'CYAN', ''))  # {
        super().__setattr__('COLOR_BRACE_CLOSE', getattr(self._color_class, 'CYAN', ''))  # }
        super().__setattr__('COLOR_BRACKET_OPEN', getattr(self._color_class, 'CYAN', ''))  # [
        super().__setattr__('COLOR_BRACKET_CLOSE', getattr(self._color_class, 'CYAN', ''))  # ]
        super().__setattr__('COLOR_PAREN_OPEN', getattr(self._color_class, 'CYAN', ''))  # (
        super().__setattr__('COLOR_PAREN_CLOSE', getattr(self._color_class, 'CYAN', ''))  # )
        super().__setattr__('COLOR_COLON', getattr(self._color_class, 'MAGENTA', ''))  # :
        super().__setattr__('COLOR_COMMA', getattr(self._color_class, 'MAGENTA', ''))  # ,

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


class ColorService:
    """Manages color system and presets."""

    def __init__(self):
        self._color_class = None
        self._style_class = None
        self.presets = ColorPresets(None, None)

    def enable_colors(self) -> ColorPresets:
        """Enable colors and return active presets."""
        try:
            import colorama
            self._color_class = colorama.Fore
            self._style_class = colorama.Style
            self.presets = ColorPresets(self._color_class, self._style_class)
            colorama.deinit()
            colorama.init(strip=False, autoreset=False)
            return self.presets
        except ImportError:
            return self.disable_colors()

    def disable_colors(self) -> ColorPresets:
        """Disable colors and return mock presets."""
        self._color_class = MockColorama
        self._style_class = MockColorama
        self.presets = ColorPresets(self._color_class, self._style_class)
        try:
            import colorama
            colorama.deinit()
        except ImportError:
            pass
        return self.presets

    def get_current_presets(self) -> ColorPresets:
        """Get current color presets."""
        return self.presets

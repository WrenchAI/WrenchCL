#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import logging
from dataclasses import dataclass
from enum import Enum
from math import ceil
from typing import Union


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

    __aMap__ = {
            "WARN": "WARNING",
            "ERR": "ERROR",
            "CRI": "CRITICAL",
            "INTERNAL": "INTERNAL",
            "DATA": "DATA",
            "HEADER": "HEADER"
            }

    __byMap__ = {"INTERNAL": "DEBUG", "DATA": "INFO", "HEADER": "INFO"}

    @classmethod
    def _missing_(cls, value: Union[str, int]):
        if value is None:
            return None
        if issubclass(type(value), Enum):
            value = value.value
        if isinstance(value, int):
            value = ceil(value / 10) * 10
            value = min(value, 50)
            value = max(value, 10)
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
        return getattr(logging, self.__byMap__.get(self.value, self.value))  # noqa

    def __str__(self) -> str:
        return self.value


logLevels = Union[int, str, LogLevel]


@dataclass
class LogOptions:
    """Configuration options for logging behavior and formatting."""
    no_format: bool = False
    no_color: bool = False
    stack_info: bool = False

    def __new__(cls, opts=None, *args, **kwargs):
        """Create LogOptions from dict, LogOptions instance, or None."""
        if isinstance(opts, LogOptions):
            return opts
        return super().__new__(cls)

    def __init__(self, opts=None, no_format=False, no_color=False, stack_info=False):
        if isinstance(opts, dict):
            self.no_format = opts.get('no_format', no_format)
            self.no_color = opts.get('no_color', no_color)
            self.stack_info = opts.get('stack_info', stack_info)
        elif isinstance(opts, LogOptions):
            # If we were passed another instance, copy it
            self.no_format = opts.no_format
            self.no_color = opts.no_color
            self.stack_info = opts.stack_info
        elif opts is None:
            self.no_format = no_format
            self.no_color = no_color
            self.stack_info = stack_info
        else:
            raise TypeError(
                    f"LogOptions expects dict, LogOptions, or None, got {type(opts)}"
                    )

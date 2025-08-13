#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
from typing import Optional


class IncompleteInitializationException(Exception):
    """
    Exception raised when an object is used without proper initialization.

    :param message: Custom error message to override the default.
    """
    def __init__(self, message: Optional[str] = None) -> None:
        msg = message or "Class is not initialized, please call initialization function first!"
        super().__init__(msg)


class InitializationException(Exception):
    """
    Exception raised when an object cannot be properly initialized.

    :param message: Custom error message to override the default.
    """
    def __init__(self, message: Optional[str] = None) -> None:
        msg = message or "Class could not be initialized!"
        super().__init__(msg)


class InvalidConfigurationException(Exception):
    """
    Exception raised when a configuration is invalid or missing required values.

    :param config_name: Name of the invalid configuration.
    :param reason: Reason why the configuration is invalid.
    :param message: Custom error message to override the default.
    """
    def __init__(self, config_name: Optional[str] = None, reason: Optional[str] = None, message: Optional[str] = None) -> None:
        msg = message or f"Configuration '{config_name}' is invalid. Reason: {reason or 'Unknown'}"
        super().__init__(msg)

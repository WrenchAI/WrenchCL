

#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

from typing import Optional, List


class IncompleteInitializationException(Exception):
    """
    Exception raised when an object is used without proper initialization.

    :param message: Custom error message to override the default.
    """
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "Class is not initialized, please call initialization function first!")


class InitializationException(Exception):
    """
    Exception raised when an object cannot be properly initialized.

    :param message: Custom error message to override the default.
    """
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "Class could not be initialized!")


class ArgumentTypeException(Exception):
    """
    Exception raised when an argument of an invalid type is passed.

    :param message: Custom error message to override the default.
    """
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "Invalid Argument Type passed")


class ArgumentValueException(Exception):
    """
    Exception raised when an argument with an invalid value is passed.

    :param message: Custom error message to override the default.
    """
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "Invalid Argument Value passed")


class ReferenceNotFoundException(Exception):
    """
    Exception raised when a required variable or value is not found.

    :param variable_name: Name of the missing variable or value.
    :param message: Custom error message to override the default.
    """
    def __init__(self, variable_name: Optional[str] = None, message: Optional[str] = None) -> None:
        super().__init__(message or f"The variable or value '{variable_name}' was not found.")


class InvalidConfigurationException(Exception):
    """
    Exception raised when a configuration is invalid or missing required values.

    :param config_name: Name of the invalid configuration.
    :param reason: Reason why the configuration is invalid.
    :param message: Custom error message to override the default.
    """
    def __init__(self, config_name: Optional[str] = None, reason: Optional[str] = None, message: Optional[str] = None) -> None:
        super().__init__(message or f"Configuration '{config_name}' is invalid. Reason: {reason or 'Unknown'}")


class ValidationTypeException(Exception):
    """
    Exception raised when validation fails due to type mismatch.

    :param field: Name of the field being validated.
    :param expected: Expected type or value.
    :param actual: Actual type or value received.
    :param message: Custom error message to override the default.
    """
    def __init__(
        self,
        field: Optional[str] = None,
        expected: Optional[str] = None,
        actual: Optional[str] = None,
        message: Optional[str] = None
    ) -> None:
        super().__init__(message or (
            f"Validation failed for field '{field}'. Expected: {expected}. Actual: {actual}."
            if field else "Validation failed."
        ))


class InvalidPayloadException(Exception):
    """
    Exception raised when a payload is invalid or missing required fields.

    :param missing_fields: List of fields that are missing from the payload.
    :param message: Custom error message to override the default.
    """
    def __init__(self, missing_fields: Optional[List[str]] = None, message: Optional[str] = None) -> None:
        super().__init__(message or (
            f"Payload is invalid. Missing required fields: {', '.join(missing_fields)}."
            if missing_fields else "Payload is invalid."
        ))


class SecurityViolationException(Exception):
    """
    Exception raised when a security violation is detected.

    :param message: Custom error message to override the default.
    """
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "Security violation detected!")


# Aliases for backward compatibility
IncompleteInitializationError = IncompleteInitializationException
InitializationError = InitializationException
ArgumentTypeError = ArgumentTypeException
ArgumentValueError = ArgumentValueException


__all__ = [
    'InitializationException',
    'IncompleteInitializationException',
    'ArgumentTypeException',
    'ArgumentValueException',
    'ReferenceNotFoundException',
    'InvalidConfigurationException',
    'ValidationTypeException',
    'InvalidPayloadException',
    'SecurityViolationException',

    # Backward compatibility aliases
    'InitializationError',
    'IncompleteInitializationError',
    'ArgumentTypeError',
    'ArgumentValueError',
]

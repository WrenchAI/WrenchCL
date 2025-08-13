#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
from typing import Optional


class ReferenceNotFoundException(Exception):
    """
    Exception raised when a required variable or value is not found.

    :param variable_name: Name of the missing variable or value.
    :param message: Custom error message to override the default.
    """
    def __init__(self, variable_name: Optional[str] = None, message: Optional[str] = None) -> None:
        msg = message or f"The variable or value '{variable_name}' was not found."
        super().__init__(msg)


class SecurityViolationException(Exception):
    """
    Exception raised when a security violation is detected.

    :param message: Custom error message to override the default.
    """
    def __init__(self, message: Optional[str] = None) -> None:
        msg = message or "Security violation detected!"
        super().__init__(msg)


class GuardedResponseTrigger(Exception):
    """Custom exception to signal early exit from the Lambda function.
    Holds response internally in `response` attribute.
    Reraise until to level when get_response() can be called"""

    def __init__(self, response):
        self.response = response

    def get_response(self):
        """
        Retrieves the response associated with this exception.

        :returns: The response dictionary associated with this exception.
        :rtype: dict
        """
        return self.response
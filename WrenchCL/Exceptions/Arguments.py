#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
from typing import Optional, List


class ArgumentTypeException(Exception):
    """
    Exception raised when an argument of an invalid type is passed.

    """

    def __init__(self, message: Optional[str] = None) -> None:
        msg = message or "Invalid Argument Type passed"
        super().__init__(msg)


class ArgumentValueException(Exception):
    """
    Exception raised when an argument with an invalid value is passed.

    """

    def __init__(self, message: Optional[str] = None) -> None:
        msg = message or "Invalid Argument Value passed"
        super().__init__(msg)


class ValidationTypeException(Exception):
    """
    Exception raised when validation fails due to type mismatch.




    """

    def __init__(
            self,
            field: Optional[str] = None,
            expected: Optional[str] = None,
            actual: Optional[str] = None,
            message: Optional[str] = None
            ) -> None:
        msg = message or (
                f"Validation failed for field '{field}'. Expected: {expected}. Actual: {actual}."
                if field else "Validation failed."
        )
        super().__init__(msg)


class InvalidPayloadException(Exception):
    """
    Exception raised when a payload is invalid or missing required fields.


    """

    def __init__(self, missing_fields: Optional[List[str]] = None, message: Optional[str] = None) -> None:
        msg = message or (
                f"Payload is invalid. Missing required fields: {', '.join(missing_fields)}."
                if missing_fields else "Payload is invalid."
        )
        super().__init__(msg)

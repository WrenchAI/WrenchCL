"""Exception classes - no optional dependencies."""

from .Arguments import (
    ArgumentTypeException,
    ArgumentValueException,
    InvalidPayloadException,
    ValidationTypeException,
)
from .Initializations import (
    IncompleteInitializationException,
    InitializationException,
    InvalidConfigurationException,
)
from .Misc import GuardedResponseTrigger, ReferenceNotFoundException, SecurityViolationException

__all__ = [
    "InitializationException",
    "IncompleteInitializationException",
    "ArgumentTypeException",
    "ArgumentValueException",
    "ReferenceNotFoundException",
    "InvalidConfigurationException",
    "ValidationTypeException",
    "InvalidPayloadException",
    "SecurityViolationException",
    "GuardedResponseTrigger",
]

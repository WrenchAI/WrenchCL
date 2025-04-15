#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
import warnings
from functools import wraps

__depr_tracker__ = set()

def Deprecated(message: str = None):
    """
    Wraps a function with a decorator that warns the user the function is Deprecated. It also allows
    an optional custom message to be displayed when the function is used.

    The warning message indicates that the function is no longer recommended for use and may be
    altered or removed in the future.

    :param message: Optional text to specify additional information about the deprecation. If not
        provided, a default message will be used.
    :return: A decorator that when applied to a function, wraps it with the deprecation warning behavior.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__module__}.{func.__name__}"
            if key not in __depr_tracker__:
                __depr_tracker__.add(key)
                warnings.warn(
                    f"{func.__module__}.{func.__name__} is deprecated {message}" or f"{func.__module__}.{func.__name__} is deprecated and may be removed in the future.",
                    category=DeprecationWarning,
                    stacklevel=2,
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator

#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
from typing import Type, TypeVar, cast

from ..Exceptions._internal import _SingletonViolationException

_T = TypeVar("_T")


def SingletonClass(cls: Type[_T]) -> Type[_T]:  # type: ignore[shadowed-type-variable,unsupported-base]
    """
    Enforces singleton behavior by wrapping the class in a custom subclass.

    Prevents the user-defined class from defining its own `__new__`, which would
    conflict with the singleton logic.

    :return: A singleton-enforcing subclass of the original
    """
    if "__new__" in cls.__dict__:
        raise _SingletonViolationException(cls)
    if "__cls_instance" in cls.__dict__:
        raise _SingletonViolationException(cls)

    class SingletonWrapper(cls):  # type: ignore
        __cls_instance = None

        def __new__(cls_, *args, **kwargs):  # type: ignore[shadowed-type-variable]
            if cls_.__cls_instance is None:
                cls_.__cls_instance = super(SingletonWrapper, cls_).__new__(cls_)
            return cls_.__cls_instance

        def __init__(self, *args, **kwargs):
            if not getattr(self, "__singleton_initialized__", False):
                super(SingletonWrapper, self).__init__(*args, **kwargs)
                setattr(self, "__singleton_initialized__", True)

    SingletonWrapper.__name__ = cls.__name__
    SingletonWrapper.__qualname__ = cls.__qualname__
    SingletonWrapper.__doc__ = cls.__doc__
    return cast(Type[_T], SingletonWrapper)

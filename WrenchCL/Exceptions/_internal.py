#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
from typing import Type, Any


class _SingletonViolationException(Exception):
    """
    Raised when a class using @SingletonClass improperly defines its own __new__ method.
    """

    def __init__(self, cls: Type[Any] = None) -> None:
        cls_name = getattr(cls, "__name__", "<unknown class>")
        msg = (
            f"Singleton violation in '{cls_name}':\n"
            f"  Classes decorated with @SingletonClass must not override the '__new__' method or define a __cls_instance attribute.\n"
            f"  This breaks singleton enforcement and leads to unexpected behavior.\n"
            f"\n  ➤ Fix: Remove the '__new__' method and __cls_instance attribute or do not use the @SingletonClass decorator.\n"
        )
        super().__init__(msg)

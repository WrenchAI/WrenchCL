from WrenchCL.Exceptions._internal import _SingletonViolationException as SvE


#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

def SingletonClass(cls: type) -> type:
    """
    Enforces singleton behavior by wrapping the class in a custom subclass.

    Prevents the user-defined class from defining its own `__new__`, which would
    conflict with the singleton logic.

    :param cls: The class to wrap
    :return: A singleton-enforcing subclass of the original
    """
    if "__new__" in cls.__dict__:
        raise SvE(cls)
    if "__cls_instance" in cls.__dict__:
        raise SvE(cls)

    class SingletonWrapper(cls):
        __cls_instance = None

        def __new__(cls_, *args, **kwargs):
            if cls_.__cls_instance is None:
                cls_.__cls_instance = super(SingletonWrapper, cls_).__new__(cls_)
            return cls_.__cls_instance

        def __init__(self, *args, **kwargs):
            if not getattr(self, '__singleton_initialized__', False):
                super(SingletonWrapper, self).__init__(*args, **kwargs)
                setattr(self, '__singleton_initialized__', True)

    SingletonWrapper.__name__ = cls.__name__
    SingletonWrapper.__qualname__ = cls.__qualname__
    SingletonWrapper.__doc__ = cls.__doc__
    return SingletonWrapper



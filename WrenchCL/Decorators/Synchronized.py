#  Copyright (c) $YEAR$. Copyright (c) $YEAR$ Wrench.AI., Willem van der Schans, Jeong Kim
#
#  MIT License
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#  All works within the Software are owned by their respective creators and are distributed by Wrench.AI.
#
#  For inquiries, please contact Willem van der Schans through the official Wrench.AI channels or directly via GitHub at [Kydoimos97](https://github.com/Kydoimos97).
#

import threading
from functools import wraps
from typing import Callable, Any


def Synchronized(lock: threading.Lock) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to ensure that a method is executed with a lock, preventing concurrent access from multiple threads.

    This decorator is useful in scenarios where thread safety is a concern, particularly when accessing shared resources
    such as database connections, files, or any other critical section of the code that should not be concurrently accessed.

    The `synchronized` decorator can be applied to any method that requires thread-safe execution. It uses a threading
    lock to ensure that only one thread can execute the decorated method at any given time.

    :param lock: A threading.Lock object used to lock the method. If no lock is provided, a ValueError is raised.
    :type lock: threading.Lock
    :raises ValueError: If the lock is not provided or is None.
    :returns: A decorator that wraps the target method with lock acquisition and release.
    :rtype: Callable[[Callable[..., Any]], Callable[..., Any]]

    **Example Usage**::

        >>> import threading
        >>> from mypackage.decorators import synchronized
        >>>
        >>> class SharedResource:
        >>>     _lock = threading.Lock()
        >>>
        >>>     @synchronized(_lock)
        >>>     def critical_section(self, value):
        >>>         # critical section that should not be accessed concurrently
        >>>         print(f"Processing value: {value}")
        >>>
        >>> resource = SharedResource()
        >>>
        >>> # Simulating concurrent access to the critical section
        >>> t1 = threading.Thread(target=resource.critical_section, args=(1,))
        >>> t2 = threading.Thread(target=resource.critical_section, args=(2,))
        >>> t1.start()
        >>> t2.start()
        >>> t1.join()
        >>> t2.join()
    """
    if lock is None:
        raise ValueError("A threading.Lock object must be provided to the synchronized decorator.")

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorates the target method to ensure thread-safe execution using the provided lock.

        :param func: The method to be decorated with thread safety.
        :type func: function
        :returns: A wrapper function that acquires the lock before method execution and releases it afterward.
        :rtype: Callable[..., Any]
        """

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            """
            Wrapper function that executes the decorated method within a thread-safe lock.

            :param args: Positional arguments for the decorated method.
            :param kwargs: Keyword arguments for the decorated method.
            :returns: The result of the decorated method execution.
            :rtype: Any
            """
            with lock:
                return func(*args, **kwargs)

        return wrapper

    return decorator



#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import time


def TimedMethod(func, level='DEBUG'):
    """
    Decorator that logs the execution time of the decorated function. This can be useful for monitoring performance
    and identifying bottlenecks in the code.

    :param func: The function to be decorated.
    :type func: function
    :param level: The logging level of the decorator
    :type level: String ['DEBUG', 'INFO', 'CONTEXT']
    :returns: The decorated function that logs its execution time.
    :rtype: function

    **Example**::

        >>> @TimedMethod
        ... def example_function():
        ...     time.sleep(2)
        ...
        >>> example_function()  # Logs: example_function took 2.00 seconds
    """

    def wrapper(*args, **kwargs):
        """
        Wraps the function call to log its execution time.

        :param args: Positional arguments for the function.
        :param kwargs: Keyword arguments for the function.
        :returns: The result of the function call.
        """
        from ..Tools.WrenchLogger import _IntLogger
        logger = _IntLogger()
        
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        log_string = f"{func.__name__} took {elapsed:.2f} seconds"
        if level.lower() == "info":
            logger.info(log_string)
        elif level.lower() == "context":
            logger.context(log_string)
        else:
            logger.debug(log_string)

        return result

    return wrapper

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
        from ..Tools import logger
        
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

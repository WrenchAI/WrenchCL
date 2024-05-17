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

from botocore.exceptions import ClientError, BotoCoreError

from ..Tools.WrenchLogger import logger

def Retryable(retry_on_exceptions=(ClientError, BotoCoreError), max_retries=3, delay=2):
    """
    Decorator to retry function calls based on specified exceptions. If the function raises any of the specified
    exceptions, it will be retried up to `max_retries` times with a delay between retries.

    :param retry_on_exceptions: A tuple of exceptions that should trigger a retry.
    :type retry_on_exceptions: tuple, optional
    :param max_retries: The maximum number of retries.
    :type max_retries: int, optional
    :param delay: The delay in seconds between retries.
    :type delay: int, optional
    :returns: The result of the decorated function if successful.
    :raises Exception: If the function raises an exception not in `retry_on_exceptions` or if `max_retries` is exceeded.
    """

    def decorator(func):
        """
        Decorates the given function with retry logic.

        :param func: The function to be decorated.
        :type func: function
        :returns: The decorated function with retry logic.
        :rtype: function
        """
        import time

        def wrapper(*args, **kwargs):
            """
            Wraps the function call with retry logic.

            :param args: Positional arguments for the function.
            :param kwargs: Keyword arguments for the function.
            :returns: The result of the function call if successful.
            :raises Exception: If the function raises an exception not in `retry_on_exceptions` or if `max_retries` is exceeded.
            """
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except retry_on_exceptions as e:
                    logger.warning(f"Retry {retries + 1} of {max_retries} for {func.__name__} due to {e}")
                    time.sleep(delay)
                    retries += 1
                except Exception as e:
                    logger.error(f"Error during {func.__name__}: {e}")
                    raise
            return func(*args, **kwargs)

        return wrapper

    return decorator

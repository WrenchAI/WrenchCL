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
import logging
from queue import Queue

from ..Tools.WrenchLogger import logger

def MultiThreaded(num_threads=2, logging_level="WARNING"):
    """
    A decorator that runs a function in multiple threads and collects the results.

    :param num_threads: The number of threads to spawn. Default is 2.
    :type num_threads: int
    :param logging_level: The logging level to use. Can be "DEBUG", "INFO", "WARNING", "ERROR", or "CRITICAL". Default is "WARNING".
    :type logging_level: str

    :return: A list of results from each thread.

    Usage example:
        >>> from your_module import MultiThreaded

        >>> @MultiThreaded(num_threads=4, logging_level="DEBUG")
        >>> def example_function(data):
        >>>     # Function logic here
        >>>     return data * 2

        >>> results = example_function(10)
        >>> print(results)

    This will run `example_function` in 4 separate threads and collect the results.
    """

    def decorator_multithreaded(func):
        @wraps(func)
        def wrapper_multithreaded(*args, **kwargs):
            threads = []
            results = Queue()
            logger.setLevel(logging_level.upper())

            def target():
                try:
                    result = func(*args, **kwargs)
                    results.put(result)
                except Exception as e:
                    logger.error(f"Error occurred in thread: {e}")

            for _ in range(num_threads):
                thread = threading.Thread(target=target)
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            return [results.get() for _ in range(num_threads)]

        return wrapper_multithreaded
    return decorator_multithreaded

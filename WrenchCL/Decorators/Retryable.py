import asyncio
import inspect
import time
from functools import wraps
from json import JSONDecodeError

import requests
from botocore.exceptions import ClientError, BotoCoreError


def Retryable(max_retries=5, retry_on_exceptions=None, delay=2, verbosity=1, logging_level="WARNING"):
    """
    A decorator that retries a function call a specified number of times if it raises an exception or if the request status code is not 200.

    This decorator catches `JSONDecodeError`, specific `requests` exceptions, `botocore` exceptions, and general `Exception` during the function execution,
    retries the function up to `max_retries` times, and logs each attempt. If the maximum number of retries is reached,
    it raises the last caught exception.

    :param max_retries: The maximum number of retries before giving up. Default is 5.
    :type max_retries: int
    :param retry_on_exceptions: A tuple of exception classes to retry on. If None, retries on all exceptions.
    :type retry_on_exceptions: tuple
    :param delay: The delay in seconds between retries. Default is 2.
    :type delay: int
    :param verbosity: Controls the verbosity of logging.
                      0 - No logging.
                      1 - Logs only the error when all retries fail.
                      2 - Logs the error and the state of the wrapped function.
                      3 - Logs warnings and everything in level 2.
                      4 - Logs warnings and the state of the function for every warning.
    :type verbosity: int
    :param logging_level: The logging level to use. Can be "DEBUG", "INFO", "WARNING", "ERROR", or "CRITICAL". Default is "WARNING".
    :type logging_level: str

    :return: The result of the decorated function, if it succeeds within the allowed retries.
    """
    from WrenchCL.Tools.WrenchLogger import Logger
    logger = Logger()
    if retry_on_exceptions is None:
        retry_on_exceptions = (Exception,)

    def log_state(func, *args, **kwargs):
        frame = inspect.currentframe().f_back
        local_vars = frame.f_locals
        state_info = [f"{key}: {str(value)[:250]}" for key, value in local_vars.get("kwargs", {}).items()]
        logger.context(f"State of function {func.__name__}:\n" + "\n".join(state_info))

    def decorator_retry(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            retry_count = 0
            logger.setLevel(logging_level.upper())

            while retry_count < max_retries:
                try:
                    response = await func(*args, **kwargs)
                    if hasattr(response, 'status_code') and response.status_code != 200:
                        response.raise_for_status()
                    logger.revertLoggingLevel()
                    return response
                except (JSONDecodeError, requests.exceptions.HTTPError, requests.exceptions.ConnectionError,
                        requests.exceptions.Timeout, requests.exceptions.RequestException, ClientError,
                        BotoCoreError) as e:
                    error_message = f"Retryable error occurred: {e}"
                    if retry_count + 1 < max_retries:
                        if verbosity >= 3:
                            logger.warning(
                                f"{retry_count + 1}/{max_retries} Retrying request. \n Error: {error_message}")
                        if verbosity == 4:
                            log_state(func, *args, **kwargs)
                        retry_count += 1
                        await asyncio.sleep(delay)
                    else:
                        if verbosity >= 1:
                            logger.error(f"Failed {max_retries} retries, \n Error: {error_message}")
                        if verbosity >= 2:
                            log_state(func, *args, **kwargs)
                        logger.revertLoggingLevel()
                        raise e
                except retry_on_exceptions as e:
                    error_message = f"Specified retryable error occurred: {e}"
                    if retry_count + 1 < max_retries:
                        if verbosity >= 3:
                            logger.warning(
                                f"{retry_count + 1}/{max_retries} Retrying request. \n Error: {error_message}")
                        if verbosity == 4:
                            log_state(func, *args, **kwargs)
                        retry_count += 1
                        await asyncio.sleep(delay)
                    else:
                        if verbosity >= 1:
                            logger.error(f"Failed {max_retries} retries, \n Error: {error_message}")
                        if verbosity >= 2:
                            log_state(func, *args, **kwargs)
                        logger.revertLoggingLevel()
                        raise e
                except Exception as e:
                    error_message = f"Unhandled error occurred: {e}"
                    if retry_count + 1 < max_retries:
                        if verbosity >= 3:
                            logger.warning(f"{retry_count + 1}/{max_retries} Retrying request: failed with error {e}")
                        if verbosity == 4:
                            log_state(func, *args, **kwargs)
                        retry_count += 1
                        await asyncio.sleep(delay)
                    else:
                        if verbosity >= 1:
                            logger.error(f"Failed {max_retries} retries, \n Error: {error_message}")
                        if verbosity >= 2:
                            log_state(func, *args, **kwargs)
                        logger.revertLoggingLevel()
                        raise e
            logger.revertLoggingLevel()

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            retry_count = 0
            logger.setLevel(logging_level.upper())

            while retry_count < max_retries:
                try:
                    response = func(*args, **kwargs)
                    if hasattr(response, 'status_code') and response.status_code != 200:
                        response.raise_for_status()
                    logger.revertLoggingLevel()
                    return response
                except (JSONDecodeError, requests.exceptions.HTTPError, requests.exceptions.ConnectionError,
                        requests.exceptions.Timeout, requests.exceptions.RequestException, ClientError,
                        BotoCoreError) as e:
                    error_message = f"Retryable error occurred: {e}"
                    if retry_count + 1 < max_retries:
                        if verbosity >= 3:
                            logger.warning(
                                f"{retry_count + 1}/{max_retries} Retrying request. \n Error: {error_message}")
                        if verbosity == 4:
                            log_state(func, *args, **kwargs)
                        retry_count += 1
                        time.sleep(delay)
                    else:
                        if verbosity >= 1:
                            logger.error(f"Failed {max_retries} retries, \n Error: {error_message}")
                        if verbosity >= 2:
                            log_state(func, *args, **kwargs)
                        logger.revertLoggingLevel()
                        raise e
                except retry_on_exceptions as e:
                    error_message = f"Specified retryable error occurred: {e}"
                    if retry_count + 1 < max_retries:
                        if verbosity >= 3:
                            logger.warning(
                                f"{retry_count + 1}/{max_retries} Retrying request. \n Error: {error_message}")
                        if verbosity == 4:
                            log_state(func, *args, **kwargs)
                        retry_count += 1
                        time.sleep(delay)
                    else:
                        if verbosity >= 1:
                            logger.error(f"Failed {max_retries} retries, \n Error: {error_message}")
                        if verbosity >= 2:
                            log_state(func, *args, **kwargs)
                        logger.revertLoggingLevel()
                        raise e
                except Exception as e:
                    error_message = f"Unhandled error occurred: {e}"
                    if retry_count + 1 < max_retries:
                        if verbosity >= 3:
                            logger.warning(f"{retry_count + 1}/{max_retries} Retrying request: failed with error {e}")
                        if verbosity == 4:
                            log_state(func, *args, **kwargs)
                        retry_count += 1
                        time.sleep(delay)
                    else:
                        if verbosity >= 1:
                            logger.error(f"Failed {max_retries} retries, \n Error: {error_message}")
                        if verbosity >= 2:
                            log_state(func, *args, **kwargs)
                        logger.revertLoggingLevel()
                        raise e
            logger.revertLoggingLevel()

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator_retry

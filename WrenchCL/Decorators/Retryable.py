import asyncio
import time
from functools import wraps
from json import JSONDecodeError

import requests
from botocore.exceptions import ClientError, BotoCoreError

def Retryable(_func=None, *, max_retries=5, retry_on_exceptions=None, delay=2, verbose=False):
    """
    A decorator that retries a function call a specified number of times if it raises an exception or if the request status code is not 200.

    This decorator catches `JSONDecodeError`, specific `requests` exceptions, `botocore` exceptions, and general `Exception` during the function execution,
    retries the function up to `max_retries` times, and logs warnings and errors based on verbosity. If the maximum number of retries is reached,
    it raises the last caught exception.

    :param max_retries: The maximum number of retries before giving up. Default is 5.
    :type max_retries: int
    :param retry_on_exceptions: A tuple of exception classes to retry on. If None, retries on all exceptions.
    :type retry_on_exceptions: tuple
    :param delay: The delay in seconds between retries. Default is 2.
    :type delay: int
    :param verbose: If True, logs warnings and errors; if False, logs only errors.
    :type verbose: bool

    :return: The result of the decorated function, if it succeeds within the allowed retries.
    """
    from ..Tools import logger

    if retry_on_exceptions is None:
        retry_on_exceptions = (Exception,)

    def log_message(level, message):
        if verbose:
            if level == "warning":
                logger.warning(message)
            elif level == "error":
                logger.error(message)
        else:
            if level == "error":
                logger.error(message)

    def decorator_retry(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            retry_count = 0
            while retry_count < max_retries:
                try:
                    response = await func(*args, **kwargs)
                    if hasattr(response, 'status_code') and response.status_code != 200:
                        response.raise_for_status()
                    return response
                except (JSONDecodeError, requests.exceptions.HTTPError, requests.exceptions.ConnectionError,
                        requests.exceptions.Timeout, requests.exceptions.RequestException, ClientError,
                        BotoCoreError) as e:
                    if retry_count + 1 < max_retries:
                        log_message("warning", f"Retry {retry_count + 1}/{max_retries} failed with error: {e}")
                        retry_count += 1
                        await asyncio.sleep(delay)
                    else:
                        log_message("error", f"Failed after {max_retries} retries with error: {e}")
                        raise e
                except retry_on_exceptions as e:
                    if retry_count + 1 < max_retries:
                        log_message("warning", f"Retry {retry_count + 1}/{max_retries} failed with error: {e}")
                        retry_count += 1
                        await asyncio.sleep(delay)
                    else:
                        log_message("error", f"Failed after {max_retries} retries with error: {e}")
                        raise e
                except Exception as e:
                    if retry_count + 1 < max_retries:
                        log_message("warning", f"Retry {retry_count + 1}/{max_retries} failed with unhandled error: {e}")
                        retry_count += 1
                        await asyncio.sleep(delay)
                    else:
                        log_message("error", f"Failed after {max_retries} retries with unhandled error: {e}")
                        raise e

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            retry_count = 0
            while retry_count < max_retries:
                try:
                    response = func(*args, **kwargs)
                    if hasattr(response, 'status_code') and response.status_code != 200:
                        response.raise_for_status()
                    return response
                except (JSONDecodeError, requests.exceptions.HTTPError, requests.exceptions.ConnectionError,
                        requests.exceptions.Timeout, requests.exceptions.RequestException, ClientError,
                        BotoCoreError) as e:
                    if retry_count + 1 < max_retries:
                        log_message("warning", f"Retry {retry_count + 1}/{max_retries} failed with error: {e}")
                        retry_count += 1
                        time.sleep(delay)
                    else:
                        log_message("error", f"Failed after {max_retries} retries with error: {e}")
                        raise e
                except retry_on_exceptions as e:
                    if retry_count + 1 < max_retries:
                        log_message("warning", f"Retry {retry_count + 1}/{max_retries} failed with error: {e}")
                        retry_count += 1
                        time.sleep(delay)
                    else:
                        log_message("error", f"Failed after {max_retries} retries with error: {e}")
                        raise e
                except Exception as e:
                    if retry_count + 1 < max_retries:
                        log_message("warning", f"Retry {retry_count + 1}/{max_retries} failed with unhandled error: {e}")
                        retry_count += 1
                        time.sleep(delay)
                    else:
                        log_message("error", f"Failed after {max_retries} retries with unhandled error: {e}")
                        raise e

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    if _func is None:
        return decorator_retry
    else:
        return decorator_retry(_func)

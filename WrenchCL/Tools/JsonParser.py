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

import json
from typing import Union, Any
from . import logger


def parse_json(response: Union[str, dict], max_depth: int = 25, verbose = False) -> dict:
    """
    Entry point to parse a JSON response into a Python dictionary. Handles nested JSON structures
    and enforces a maximum recursion depth.

    Parameters
    ----------
    response : Union[str, dict]
        The JSON response to parse. Can be a dictionary or a JSON-encoded string.
    max_depth : int, optional
        Maximum allowed recursion depth to prevent infinite loops (default is 25).
    verbose : bool, optional
        If True, logs information messages for key parsing. Otherwise, logs debug messages (default is False).

    Returns
    -------
    dict
        Parsed JSON response as a Python dictionary.

    Raises
    ------
    RecursionError
        If the maximum recursion depth is exceeded.
    TypeError
        If the response cannot be parsed into a dictionary.
    ValueError
        If the JSON is invalid.
    json.JSONDecodeError
        If the JSON decoding fails.

    Notes
    -----
    This function calls `recur_parse_json` to handle nested structures and uses `safe_json_loader`
    to handle malformed JSON gracefully.
    """
    try:
        logger.debug(f"Starting JSON parsing. Max depth: {max_depth}")
        return recur_parse_json(response, max_depth=max_depth, verbose = verbose)
    except RecursionError as e:
        logger.error(f"Recursion limit reached: {e}", stack_info=False)
        raise
    except (TypeError, ValueError, json.JSONDecodeError) as e:
        logger.error(f"Invalid input format: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in parse_json: {e}")
        raise


def recur_parse_json(d: Union[dict, str], depth: int = 0, max_depth: int = 25, verbose = False) -> dict:
    """
    Recursively parses nested JSON structures into a dictionary while enforcing a recursion depth limit.

    Parameters
    ----------
    d : Union[dict, str]
        The current JSON object or string to parse.
    depth : int, optional
        Current recursion depth (default is 0).
    max_depth : int, optional
        Maximum allowed recursion depth to prevent infinite loops (default is 25).
    verbose : bool, optional
        If True, logs parsed keys as information messages. Otherwise, logs them as debug messages (default is False).

    Returns
    -------
    dict
        Fully parsed JSON object.

    Raises
    ------
    RecursionError
        If the maximum recursion depth is exceeded.
    TypeError
        If the object cannot be parsed into a dictionary.

    Notes
    -----
    This function calls `safe_json_loader` for parsing strings and `list_loader` for handling lists.
    """
    if depth > max_depth:
        raise RecursionError(f"Maximum recursion depth of {max_depth} exceeded")

    d = safe_json_loader(d, raise_error=True)

    if not isinstance(d, dict):
        raise TypeError(f"Expected dictionary but got {type(d).__name__}")

    for k, v in d.items():
        if isinstance(v, dict):
            d[k] = recur_parse_json(v, depth=depth + 1, max_depth=max_depth)
        elif isinstance(v, str):
            parsed = safe_json_loader(v, raise_error=False)
            if isinstance(parsed, dict):
                d[k] = recur_parse_json(parsed, depth=depth + 1, max_depth=max_depth)
            elif isinstance(parsed, list):
                d[k] = list_loader(parsed, depth=depth + 1, max_depth=max_depth, verbose = verbose)
            else:
                d[k] = parsed
        elif isinstance(v, list):
            d[k] = list_loader(v, depth=depth + 1, max_depth=max_depth, verbose = verbose)
        indent = "--" * (depth + 1)
        if verbose:
            logger.info(f"{indent}>Parsed key '{k}': to type {type(d[k]).__name__}")
        else:
            logger.debug(f"{indent}>Parsed key '{k}': to type {type(d[k]).__name__}")
    return d


def list_loader(v: Any, depth: int = 0, max_depth: int = 25, verbose = False) -> list:
    """
    Recursively parses lists within a JSON structure. Handles both valid and malformed JSON strings.

    Parameters
    ----------
    v : Any
        The list to process. Elements can be dictionaries, JSON strings, or other data types.
    depth : int, optional
        Current recursion depth (default is 0).
    max_depth : int, optional
        Maximum allowed recursion depth to prevent infinite loops (default is 25).
    verbose : bool, optional
        If True, logs parsed list elements as information messages. Otherwise, logs them as debug messages (default is False).

    Returns
    -------
    list
        Fully parsed list with nested structures resolved.

    Raises
    ------
    RecursionError
        If the maximum recursion depth is exceeded.
    TypeError
        If the input is not a list.

    Notes
    -----
    The function calls `safe_json_loader` for string parsing and `recur_parse_json` for dictionary parsing.
    """
    if depth > max_depth:
        raise RecursionError(f"Maximum recursion depth of {max_depth} exceeded in list_loader")

    if not isinstance(v, list):
        raise TypeError(f"Expected list but got {type(v).__name__}")

    parsed_list = []
    for item in v:
        if isinstance(item, dict):
            parsed_list.append(recur_parse_json(item, depth=depth + 1, max_depth=max_depth, verbose = verbose))
        elif isinstance(item, str):
            parsed = safe_json_loader(item, raise_error=False)
            if isinstance(parsed, dict):
                parsed_list.append(recur_parse_json(parsed, depth=depth + 1, max_depth=max_depth, verbose = verbose))
            elif isinstance(parsed, list):
                parsed_list.append(list_loader(parsed, depth=depth + 1, max_depth=max_depth, verbose = verbose))
            else:
                parsed_list.append(parsed)
        else:
            parsed_list.append(item)

    return parsed_list


def safe_json_loader(content: Any, raise_error=False, depth=0, silent = False) -> Union[dict, str, Any]:
    """
    Safely parses JSON strings into Python dictionaries or leaves them as-is if they are malformed.

    Parameters
    ----------
    content : Any
        The content to parse. Expected to be a JSON string, dictionary, or list.
    raise_error : bool, optional
        If True, raises exceptions for JSON parsing errors. Otherwise, leaves malformed strings as-is (default is False).
    depth : int, optional
        Current recursion depth, used for logging indentation (default is 0).
    silent : bool, optional
        If True, suppresses warnings for malformed JSON (default is False).

    Returns
    -------
    Union[dict, str, Any]
        Parsed JSON object, string, or the original content if parsing fails.

    Raises
    ------
    json.JSONDecodeError
        If JSON decoding fails and `raise_error` is True.
    TypeError
        If the content is not a string, dictionary, or list.

    Notes
    -----
    - Properly handles nested structures by recursively calling itself for strings within dictionaries.
    - Logs warnings for malformed JSON strings unless `silent` is True.
    """

    if isinstance(content, dict):
        return content  # Already a valid dictionary

    if isinstance(content, str):
        try:
            parsed = json.loads(content.strip())  # Try parsing the whole string
            if isinstance(parsed, dict):
                for key, value in parsed.items():
                    if isinstance(value, str):
                        try:
                            parsed[key] = safe_json_loader(value, raise_error=True, depth=depth + 1, silent= True)
                        except json.JSONDecodeError as e:
                            indent = "--" * (depth + 2)
                            if '{' in value or '}' in value:
                                logger.warning(f"{indent}>Malformed JSON in key '{key}': {value}")
                            logger.debug(f"{indent}>End of structure at key: {key}, value: {value}'")
                            return parsed
                return parsed
            elif isinstance(parsed, list):
                return list_loader(parsed)
            return parsed
        except json.JSONDecodeError as e:
            if not silent:
                indent = "--" * (depth + 1)
                if '{' in content or '}' in content:
                    logger.warning(f"{indent}>Malformed JSON in content: {content}")
                logger.debug(f"{indent}>End of structure at depth: {depth + 1}")
            if raise_error:
                raise
            return content  # Leave malformed content as-is

    raise TypeError(f"safe_json_loader expected string or dict but got {type(content).__name__}")


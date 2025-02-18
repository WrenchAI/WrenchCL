


# Created by Jeong Kim
# Github: https://github.com/dalmad2
# Annotated by Willem van der Schans
# Github: https://github.com/Kydoimos97


import json
import warnings
from typing import Any, Dict, Optional

from ..Tools import robust_serializer


def build_return_json(
    code: int,
    response_body: Any,
    allow: Optional[str] = "GET, OPTIONS, POST",
    header_options: Optional[Dict[str, str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Constructs a JSON response body with default headers and allows additional customization.

    Args:
        code (int): The HTTP status code to include in the response.
        response_body (any): The main content of the response, serialized using robust_serializer.
        allow (str, optional): HTTP methods allowed by the server. Defaults to "GET, OPTIONS, POST".
        header_options (dict, optional): Custom headers to override defaults. Defaults to None.
        **kwargs: Additional fields to include in the response body.

    Returns:
        dict: The full response object with headers, status code, and body.
    """
    # Default headers
    warnings.warn("build_return_json is deprecated and will be removed in a future release, use please refrain from using", DeprecationWarning)
    default_headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'strict-transport-security': 'max-age=63072000; includeSubdomains; preload',
        'content-security-policy': "default-src 'none'; img-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'",
        'x-content-type-options': 'nosniff',
        'x-frame-options': 'DENY',
        'x-xss-protection': '1; mode=block',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': allow,
        'Access-Control-Allow-Headers': '*'
    }

    # Merge headers
    merged_headers = {**default_headers, **(header_options or {})}

    # Merge additional body fields
    final_body = {**response_body, **kwargs} if isinstance(response_body, dict) else response_body

    try:
        return {
            'statusCode': code,
            'headers': merged_headers,
            'body': json.dumps(final_body, default=robust_serializer)
        }
    except (TypeError, ValueError) as e:
        raise TypeError("Response body is not JSON serializable") from e


#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import json
from typing import Any, Dict, Optional, Union, Literal, get_args, TypedDict

from .. import logger
from ..Tools import RobustJSONEncoder
from ..Tools.truncate_display import truncate_display

# Allowed Lambda proxy response codes
LambdaStatusCodes = Literal[200, 201, 202, 204, 301, 302, 304, 307, 308, 400, 401, 403, 404, 405, 409, 429, 500, 502, 503, 504]

STATUS_CODE_MESSAGES: Dict[int, str] = {
        # 2xx: Success
        200: "OK: The request was successful.",
        201: "Created: A new resource has been created successfully.",
        202: "Accepted: The request has been accepted for processing, but is not yet complete.",
        204: "No Content: The request succeeded, but there is no content to return.",

        # 3xx: Redirection
        301: "Moved Permanently: The resource has been moved to a new URI permanently.",
        302: "Found: The resource is temporarily available at a different URI.",
        304: "Not Modified: The resource has not changed since the last request.",
        307: "Temporary Redirect: The request should be repeated with a different URI (same method).",
        308: "Permanent Redirect: The request should be repeated with a new URI (same method).",

        # 4xx: Client Errors
        400: "Bad Request: The request could not be understood or was missing required parameters.",
        401: "Unauthorized: Authentication is required or has failed.",
        403: "Forbidden: You do not have permission to access this resource.",
        404: "Not Found: The requested resource could not be found.",
        405: "Method Not Allowed: The HTTP method is not supported for this resource.",
        409: "Conflict: The request could not be completed due to a conflict with the current state.",
        429: "Too Many Requests: You have sent too many requests in a given timeframe.",

        # 5xx: Server Errors
        500: "Internal Server Error: An unexpected server error occurred.",
        502: "Bad Gateway: The server received an invalid response from an upstream service.",
        503: "Service Unavailable: The server is temporarily unable to handle the request.",
        504: "Gateway Timeout: The server did not receive a timely response from an upstream service.",
        }


class LambdaBodyProtocol(TypedDict, total=False):
    message: str
    data: Optional[Dict[str, Any]]


class SerializedLambdaResponse(TypedDict):
    statusCode: LambdaStatusCodes
    headers: Dict[str, str]
    body: str


class LambdaResponse:
    _statusCode: LambdaStatusCodes
    _headers: Dict[str, str]
    _message: str
    _body: LambdaBodyProtocol
    _serialized_body: str
    _default_headers: Dict[str, str] = {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS, POST",
            "Access-Control-Allow-Headers": "*",
            }

    def __init__(self, status_code: LambdaStatusCodes, body: Union[Dict[str, Any], str, None], headers: Dict[str, str]) -> None:
        self.statusCode = status_code
        self.headers = headers
        self.body = body

    @property
    def statusCode(self) -> LambdaStatusCodes:
        return self._statusCode

    @statusCode.setter
    def statusCode(self, value: LambdaStatusCodes) -> None:
        if not isinstance(value, int):
            raise TypeError("statusCode must be an integer")
        if value not in get_args(LambdaStatusCodes):
            raise ValueError("statusCode must be a valid Lambda response code")
        self._statusCode = value
        self._message = STATUS_CODE_MESSAGES[value]

    @property
    def headers(self) -> Dict[str, str]:
        if self._headers is None:
            self._headers = self._default_headers.copy()
        return self._headers

    @headers.setter
    def headers(self, value: Dict[str, str]) -> None:
        if not isinstance(value, dict):
            raise TypeError("headers must be a dictionary")
        self._headers = value

    @property
    def body(self) -> LambdaBodyProtocol:
        if self._body is None:
            self.body = {}
        return self._body

    @body.setter
    def body(self, value: Union[Dict[str, Any], str, None]) -> None:
        __im = None
        if value is None:
            value = {}
        if value is not None and not isinstance(value, (dict, str)):
            value = str(value)
        if not isinstance(value, dict):
            value = {'data': value}
        if 'message' in value:
            __im = value.pop('message')
        value['message'] = self._message if __im is None else f"{self._message} | {__im}"
        serialized_body = json.dumps(value, cls=RobustJSONEncoder)
        self._body = LambdaBodyProtocol(**value)
        self._serialized_body = serialized_body

    def as_dict(self) -> SerializedLambdaResponse:
        """Return AWS Lambda-compatible dict."""
        return {
                "statusCode": self.statusCode,
                "headers": self.headers,
                "body": self._serialized_body,
                }

    def json(self):
        return json.dumps(self.as_dict(), cls=RobustJSONEncoder)

    def __repr__(self) -> str:
        """Debug-friendly truncated representation."""
        return f"LambdaResponse(statusCode={self.statusCode}, headers={self.headers}, body={truncate_display(self.body)})"

    def __str__(self) -> str:
        return json.dumps(self.as_dict(), cls=RobustJSONEncoder, indent=2)

    def __iter__(self):
        yield from self.as_dict().items()

    # noinspection PyUnusedFunction
    def as_json(self) -> str:
        return self.json()

    # noinspection PyUnusedFunction
    def __json__(self) -> str:
        return self.json()


# Standardized short messages for supported codes
def handle_lambda_response(status_code: LambdaStatusCodes, body: Union[Dict[str, Any], str, None] = None, allow_methods: str = "GET, OPTIONS, POST", extra_headers: Optional[Dict[str, str]] = None, **extra_body_fields: Any) -> LambdaResponse:
    """
    Build a minimal AWS Lambda proxy response with:
      - Strictly typed HTTP status codes.
      - CORS + JSON defaults.
      - Standardized messages if body is None or empty.

    :param status_code: Valid HTTP status code for Lambda proxy responses.
    :param body: Response payload (dict, str, or None).
    :param allow_methods: Allowed HTTP methods for CORS (default: "GET, OPTIONS, POST").
    :param extra_headers: Optional headers to merge into the defaults.
    :param extra_body_fields: Extra key/value pairs merged into the body if it's a dict.
    :return: LambdaResponseDict.
    """
    try:
        headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": allow_methods,
                "Access-Control-Allow-Headers": "*",
                **(extra_headers or {}),
                }

        # If body is None, fall back to a standardized message
        if body is None:
            body = {"message": STATUS_CODE_MESSAGES.get(status_code, "Unknown Status")}
        elif isinstance(body, dict):
            body = {**body, **extra_body_fields}

        response = LambdaResponse(status_code, body, headers)
        logger._internal_log(f"Lambda response: {repr(response)}")
        return response
    except (TypeError, ValueError) as e:
        raise TypeError("Response body is not JSON serializable") from e
    except Exception as e:
        raise Exception("Error building Lambda response") from e

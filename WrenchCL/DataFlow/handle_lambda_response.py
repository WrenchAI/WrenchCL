import json
#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import os

from boto3 import client as boto3client

from .trigger_dataflow_metrics import trigger_minimum_dataflow_metrics
from ..Tools import robust_serializer
from ..Tools.WrenchLogger import _IntLogger
logger = _IntLogger()
from ..Tools.TypeChecker import typechecker  # Update this to the correct import path

lambda_response = None


class GuardedResponseTrigger(Exception):
    """Custom exception to signal early exit from the Lambda function."""

    def __init__(self, response):
        self.response = response

    def get_response(self):
        """
        Retrieves the response associated with this exception.

        :returns: The response dictionary associated with this exception.
        :rtype: dict
        """
        return self.response


def handle_lambda_response(code, message, params, response_body=None, client_id=None, entity_id=None):
    """
    Handles Lambda function responses, providing detailed custom error logging while
    ensuring valid HTTP status codes in API responses.

    Custom Error Code Mapping (Logged vs. API Response Codes):
        - Logged Codes (4xx, 5xx):
            - 400: Validation Error (Bad request, malformed inputs).
            - 401: Unauthorized (Invalid credentials, session expired).
            - 403: Forbidden (Permission denied, restricted access).
            - 404: Resource Not Found.
            - 409: Conflict (Resource locks, version conflicts).
            - 429: Rate Limit Exceeded.
            - 500: General Server Error (Unhandled exceptions, internal issues).
            - 502: Dependency Error (External service failures).
            - 503: Service Unavailable (System overload, downtime).
            - 504: Gateway Timeout (Function timeout, resource unavailability).
            - 550: Generic Custom Error (Unspecified issues for tracking purposes).
            - 551: Data Validation Error (Invalid inputs or constraints).
            - 552: Resource Lock or Conflict.
            - 553: Model or AI-related issues.
            - 554: API Gateway or Lambda-specific errors.
        - Returned API Codes:
            - 4xx (Client Errors): Mapped based on the custom code (400, 401, 403, etc.).
            - 5xx (Server Errors): Generalized to standard HTTP codes (500, 502, etc.).

    :param int code: Internal custom error code for logging purposes.
    :param str message: A descriptive message about the status or error.
    :param dict params: Parameters required for further processing.
    :param dict response_body: Custom JSON response body (optional).
    :param str client_id: The client ID (optional).
    :param str entity_id: The entity ID (optional).

    :raises GuardedResponseTrigger: Custom exception to signal early exit from the Lambda function.
    """
    code = int(code)
    expected_types = {
        'event': str,
        'context': str,
        'start_time': (int, float),
        'lambda_client': boto3client,
    }

    try:
        typechecker(params, expected_types, none_is_ok=True)
        if params.get('lambda_client') is None:
            params['lambda_client'] = boto3client('lambda')

        trigger_minimum_dataflow_metrics(
            event=params.get('event', {}),
            context=params.get('context', {}),
            lambda_client=params.get('lambda_client'),
            job_name=os.getenv('AWS_FUNCTION_NAME', ''),
            job_type=os.getenv('AWS_JOB_TYPE', 'lambda'),
            status_code=code,
            exception_msg=str(message)
        )
    except Exception as e:
        logger.error(f"Failed to invoke dataflow metrics with error {e}")

    # Consolidated Custom Error Messages
    custom_error_messages = {
        400: "Validation Error: Malformed or invalid request.",
        401: "Unauthorized: Invalid credentials or session expired.",
        403: "Forbidden: Access denied or restricted.",
        404: "Resource Not Found: The requested resource does not exist.",
        409: "Conflict: Resource is locked or has version conflicts.",
        429: "Rate Limit Exceeded: Too many requests.",
        500: "Internal Server Error: An unexpected server-side issue occurred.",
        502: "Dependency Error: External service failure.",
        503: "Service Unavailable: System overload or downtime.",
        504: "Gateway Timeout: Function timed out before completion.",
        550: "Generic Custom Error: Unspecified issue for tracking purposes.",
        551: "Data Validation Error: Inputs failed validation.",
        552: "Resource Conflict: Resource is locked or conflicting.",
        553: "Model Error: AI/ML operation failed.",
        554: "Lambda/API Gateway Error: Integration or execution issue.",
    }

    # Map custom codes to standard HTTP codes for API responses
    if code in {550, 551, 552, 553, 554}:
        api_code = 500  # Map custom server-side issues to HTTP 500
    elif code in custom_error_messages:
        api_code = code  # Use the provided code for 4xx and common 5xx errors
    else:
        api_code = 500  # Default to HTTP 500 for undefined server errors

    # Log the error with the internal custom code
    if code in custom_error_messages:
        logger.error(
            f"Custom Code = {code} | {custom_error_messages[code]} | [Client ID: {client_id}, Entity ID: {entity_id}] | Status Message: {message}"
        ,stack_info=True)
    else:
        logger.error(
            f"Custom Code = {code} | Unrecognized Error Code | [Client ID: {client_id}, Entity ID: {entity_id}] | Status Message: {message}"
        ,stack_info=True)

    default_headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Access-Control-Allow-Origin': '*'
    }

    # Build the response
    response = {
            'statusCode': api_code,
            'headers': default_headers,
            'body': json.dumps(dict(Message=message) if response_body is None else response_body, default=robust_serializer)
        }

    logger.context(f"Built Lambda Response: {response}")
    raise GuardedResponseTrigger(response)

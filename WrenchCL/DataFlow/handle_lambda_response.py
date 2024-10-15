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
import os

from boto3 import client as boto3client

from ..Tools.TypeChecker import typechecker  # Update this to the correct import path
from ..Tools import logger

from .build_return_json import build_return_json
from .trigger_dataflow_metrics import trigger_minimum_dataflow_metrics

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
    Handles the Lambda function response generation and logging based on the provided status code and message.

    :param int code: The HTTP status code to be included in the response.
    :param str message: The message to be included in the response body.
    :param dict params: A dictionary containing parameters required for further processing.
    :param dict response_body: The json response body (optional).
    :param str client_id: The client ID (optional).
    :param str entity_id: The entity ID (optional).

    :raises GuardedResponseTrigger: Custom exception to signal early exit from the Lambda function. If raised and not handled
        at the Lambda handler level, this exception will cause an immediate return with the generated response. If caught
        within nested calls, ensure to re-raise it as follows:
        ``except GuardedResponseTrigger as e: raise e``
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

    custom_error_messages = {
        700: "Generic Custom Error: A fallback error for unspecified issues.",
        701: "Invalid Request Format: The request body does not match the expected schema.",
        702: "Authentication Failed: Credentials provided are invalid or expired.",
        703: "Authorization Denied: The authenticated user does not have permission to access the requested resource.",
        704: "Resource Not Found: The requested resource does not exist or is not available.",
        705: "Resource Locked: The resource is currently locked or in use and cannot be modified.",
        706: "Rate Limit Exceeded: The request has exceeded the rate limit. Try again later.",
        707: "Data Validation Failed: The provided data does not meet validation criteria.",
        708: "Dependency Error: A failure occurred in an external service or dependency.",
        709: "Feature Deprecated: The requested feature is no longer supported.",
        710: "Uncaught Expected Exit Path: The Lambda has been exited in an expected manner without successfully ending.",
        730: "Model Training Error: An error occurred during the training process of a machine learning model.",
        731: "Model Not Found: The specified machine learning model could not be found.",
        732: "Prediction Error: An Internal error occurred while making a prediction with the model.",
        733: "Model Update Failure: Failed to update the machine learning model.",
        734: "Invalid Model Input: The input data for the model is invalid or malformed.",
        735: "Model Deployment Error: An error occurred while deploying the machine learning model.",
        736: "Model Version Conflict: There is a version conflict with the machine learning model.",
        737: "Prediction Error: Invalid prediction provided by model.",
        738: "Data Value Error: Returned score does not satisfy constraints or expected range.",
        740: "Lambda Invocation Error: An error occurred while invoking an AWS Lambda function.",
        741: "Lambda Timeout: The AWS Lambda function timed out before completion.",
        742: "Insufficient Permissions: The AWS Lambda function does not have the necessary permissions.",
        743: "Cold Start Delay: Delay due to AWS Lambda cold start.",
        744: "API Gateway Integration Error: An error occurred in the integration between Lambda and API Gateway.",
        745: "Lambda Resource Limit Exceeded: The AWS Lambda function exceeded its allocated resources.",
        750: "Data Retrieval Failure: Failed to retrieve data from the database or storage.",
        751: "Data Save Failure: Failed to save data to the database or storage.",
        752: "Data Integrity Error: The data integrity check failed.",
        753: "Data Serialization Error: An error occurred during data serialization or deserialization.",
        754: "Data Version Mismatch: The version of the data does not match the expected version.",
        755: "Data Expiry Error: Attempted to access data that has expired or is no longer valid.",
        756: "Data Encryption Error: An error occurred during data encryption or decryption.",
        757: "Data Typing Error: An error occurred during data type coercion.",
        758: "Data Retrieval Rejection: The requested data already exists.",
        800: "Payment Required: The request cannot be processed without payment.",
        801: "Quota Exceeded: The usage quota for the service or resource has been exceeded.",
        802: "Duplicate Request: The same request has been received more than once.",
        803: "Resource Conflict: The request could not be completed due to a conflict with the current state of the resource.",
        804: "Precondition Failed: One or more conditions in the request header fields evaluated to false.",
        805: "Validation Timeout: The validation process for the request has timed out.",
        806: "Operation Not Allowed: The requested operation is not allowed.",
        807: "Data Mismatch Error: The provided data does not match the expected data.",
        808: "Partial Success: The operation was partially successful.",
        809: "Dependent Resource Unavailable: A resource that the request depends on is not available."
    }

    if code in custom_error_messages:
        logger.warning(
            f"status code = {code} | {custom_error_messages[code]} | [Client ID: {client_id}, Entity ID: {entity_id}] | Status message: {message}"
        )
    elif 400 <= code < 500:
        logger.error(
            f"status code = {code} | Un-Handled Exception Status Code | [Client ID: {client_id}, Entity ID: {entity_id}] | Status message: {message}"
        )
    elif code != 200:
        logger.error(
            f"status code = {code} | Unexpected Status Code | [Client ID: {client_id}, Entity ID: {entity_id}] | Status message: {message}"
        )
    elif code == 200:
        logger.info(
            f"status code = {code} | Success Status | [Client ID: {client_id}, Entity ID: {entity_id}] | Status message: {message}"
        )

    response = build_return_json(
        code=code,
        response_body=dict(Message=message) if response_body is None else response_body
    )
    logger.context(f"Built Lambda Response: {response}")
    raise GuardedResponseTrigger(response)

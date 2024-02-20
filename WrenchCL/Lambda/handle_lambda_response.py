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

#
#  MIT License
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#
#
#  All works within the Software are owned by their respective creators and are distributed by Wrench.AI.
#
#  For inquiries, please contact Willem van der Schans through the official Wrench.AI channels or directly via GitHub at [Kydoimos97](https://github.com/Kydoimos97).
#

from boto3 import client as boto3client
from WrenchCL.Utility.validate_input_dict import validate_input_dict
from WrenchCL import wrench_logger
from .build_return_json import build_return_json
from .dataflow_metrics_helper import trigger_minimum_dataflow_metrics

lambda_response = None


class GuardedResponseTrigger(Exception):
    """Custom exception to signal early exit from the Lambda function."""

    def __init__(self, response):
        self.response = response

    def get_response(self):
        """
        Retrieves the response associated with this exception.

        Returns:
            dict: The response dictionary associated with this exception.
        """
        return self.response


def handle_lambda_response(code, message, params, client_id=None, entity_id=None):
    """
    Handles the Lambda function response generation and logging based on the provided status code and message.

    Args:
        code (int): The HTTP status code to be included in the response.
        message (str): The message to be included in the response body.
        params (dict): A dictionary containing parameters required for further processing.
        client_id (str, optional): The client ID. Defaults to None.
        entity_id (str, optional): The entity ID. Defaults to None.

    Raises:
        GuardedResponseTrigger: Custom exception to signal early exit from the Lambda function. If raised and not handled
                                at the Lambda handler level, this exception will cause an immediate return with the
                                generated response. If caught within nested calls, ensure to re-raise it as follows:
                                `except GuardedResponseTrigger as e: raise e`
    """
    code = int(code)
    expected_types = {
        'event': str,
        'context': str,
        'start_time': (int, float),
        'lambda_client': boto3client,
        }

    try:
        validate_input_dict(params, expected_types)
        trigger_minimum_dataflow_metrics(event=params.get('event'),
                                         context=params.get('context'),
                                         start_time=params.get('start_time'),
                                         lambda_client=params.get('lambda_client'),
                                         job_name='Model Inference Service',
                                         job_type='Lambda',
                                         status_code=str(code),
                                         message=str(message))
    except Exception as e:
        wrench_logger.error("Failed to invoke dataflow metrics with error {e}")

    if 700 <= code <= 899:
        # Custom Handled Response (Used to identify caught and uncaught exceptions without bloating code) -- These Need to be standardized for datadog
        wrench_logger.warning(
            f"status code = {code} | Reserved Wrench Handled Exception Status Code | [Client ID: {client_id}, Entity ID: {entity_id}] | Status message: {message}")
    elif 400 <= code < 500:
        wrench_logger.error(
            f"status code = {code} | Un-Handled Exception Status Code | [Client ID: {client_id}, Entity ID: {entity_id}] | Status message: {message}")
    elif code != 200:
        wrench_logger.error(
            f"status code = {code} | Unexpected Status Code | [Client ID: {client_id}, Entity ID: {entity_id}] | Status message: {message}")
    elif code == 200:
        wrench_logger.info(
            f"status code = {code} | Success Status | [Client ID: {client_id}, Entity ID: {entity_id}] | Status message: {message}")

    response = build_return_json(code=code, message=message)
    wrench_logger.context(f"Built Lambda Response: {response}")
    raise GuardedResponseTrigger(response)

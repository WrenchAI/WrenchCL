#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import os
from typing import Any, Optional

import requests

from .. import logger
from ._secret import resolve_secret


def slack_post(
    message: str,
    channel: str = "pipeline_runs",
    level: str = "INFO",
    metadata: Optional[dict] = None,
    *,
    base_url: Optional[str] = None,
    service_secret: Optional[str] = None,
    secret_env_var: str = "WRENCH_SERVICE_SECRET",
    secret_arn: Optional[str] = None,
    timeout: int = 10,
) -> bool:
    """
    Post a message to a Wrench Slack channel via the internal API.

    This function sends a message to a Wrench Slack channel using the internal API endpoint.
    It never raises exceptions — all errors are logged as warnings and the function returns
    False on any failure. This makes it safe to use in critical service paths without
    worrying about exception handling for network or configuration issues.

    The function reads credentials and endpoint configuration from environment variables
    if not provided explicitly. This pattern is designed to work with ECS task definitions
    that inject secrets via the Terraform `secrets` block.

    Parameters
    ----------
    message : str
        The message text to send to the Slack channel. This is the main content of the post.

    channel : str, optional
        The target Slack channel. Valid channels include legacy aliases that AiAxis resolves,
        such as "alerts" (critical channel), "logs" (debug channel), "pipeline_runs",
        "critical", "debug", and others. Default is "pipeline_runs".

    level : str, optional
        The severity level of the message. Valid values are "INFO", "WARN", and "ERROR".
        Default is "INFO".

    metadata : dict, optional
        Optional metadata dictionary to include with the message. This allows attaching
        structured data to the log entry. Default is None.

    base_url : str, optional
        The base URL of the Wrench API. If not provided, the function reads the
        WRENCH_API_BASE_URL environment variable. If that is also not set, defaults to
        the production API URL: https://api.v2.wrench.ai

    service_secret : str, optional
        The service secret for authentication with the Wrench API. If provided and
        non-empty, this value is used directly and takes priority over other sources.
        Default is None.

    secret_env_var : str, optional
        The name of the environment variable to read for the service secret if
        `service_secret` is not provided. The function reads `os.environ.get(secret_env_var)`
        and uses it if available. This is the second priority after direct `service_secret`.
        Default is "WRENCH_SERVICE_SECRET".

    secret_arn : str, optional
        The AWS Secrets Manager ARN to fetch the service secret from if both
        `service_secret` and the environment variable fail to resolve. This is the
        third priority and requires boto3 to be installed. Requires the service
        to have IAM permissions to read secrets. Default is None.

    timeout : int, optional
        The request timeout in seconds. Default is 10 seconds.

    Returns
    -------
    bool
        True if the message was successfully posted (2xx response from the API).
        False if any error occurred during the request, including missing credentials,
        network errors, or non-2xx responses. All errors are logged as warnings.

    Examples
    --------
    Simple post to the default pipeline_runs channel:

        >>> from WrenchCL.Wrench import slack_post
        >>> success = slack_post("Deployment started for version 1.2.3")
        >>> print(success)
        True

    Post with custom level and metadata:

        >>> success = slack_post(
        ...     message="Database migration completed",
        ...     channel="alerts",
        ...     level="WARN",
        ...     metadata={"duration_seconds": 45, "records_affected": 10000}
        ... )

    Using environment variables for configuration (typical ECS pattern):

        >>> # Set in ECS task definition or shell:
        >>> # export WRENCH_SERVICE_SECRET=your-service-secret
        >>> # export WRENCH_API_BASE_URL=https://api.v2.wrench.ai
        >>> success = slack_post(
        ...     message="Critical alert",
        ...     channel="critical",
        ...     level="ERROR"
        ... )

    Notes
    -----
    - This function never raises exceptions. All errors are caught and logged.
    - If the service_secret is missing, a warning is logged and the function returns False
      without making an HTTP request.
    - Non-2xx HTTP responses are logged with their status code and first 200 characters
      of the response body.
    - Network errors and timeouts are caught and logged.
    """
    resolved_secret = resolve_secret(
        value=service_secret,
        env_var=secret_env_var,
        arn=secret_arn,
    )

    if not resolved_secret:
        logger.warning("slack_post: no service secret available — message not sent")
        return False

    if base_url is None:
        base_url = os.environ.get(
            "WRENCH_API_BASE_URL", "https://api.v2.wrench.ai"
        )

    endpoint = f"{base_url}/dev/slack/post"

    payload: dict[str, Any] = {
        "channel": channel,
        "message": message,
        "level": level,
    }

    if metadata is not None:
        payload["metadata"] = metadata

    headers = {
        "x-api-secret": resolved_secret,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=timeout,
        )

        if response.status_code < 200 or response.status_code >= 300:
            response_text = response.text[:200]
            logger.warning(
                f"slack_post: API returned status {response.status_code}. "
                f"Response: {response_text}"
            )
            return False

        return True

    except requests.RequestException as exc:
        logger.warning(f"slack_post: Request failed with error: {str(exc)}")
        return False

    except Exception as exc:
        logger.warning(f"slack_post: Unexpected error: {str(exc)}")
        return False

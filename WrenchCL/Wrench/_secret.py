#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import os
from typing import Optional

from .. import logger


def resolve_secret(
    value: Optional[str] = None,
    env_var: Optional[str] = "WRENCH_SERVICE_SECRET",
    arn: Optional[str] = None,
    region: str = "us-east-1",
) -> Optional[str]:
    """
    Resolve a secret from multiple sources with a defined priority order.

    This function implements a flexible secret resolution strategy that supports
    three distinct sources: direct value, environment variable, and AWS Secrets
    Manager via ARN. The function returns the first non-None, non-empty result
    according to the priority order below. Never raises exceptions — all errors
    are logged as warnings and the function returns None on any failure.

    Resolution Priority
    -------------------
    1. Direct value: If `value` is provided and non-empty, it is returned immediately.
    2. Environment variable: If `value` is None or empty, the environment variable
       specified by `env_var` is checked. If it exists and is non-empty, its value
       is returned.
    3. Auto-derived ARN environment variable: If `env_var` is provided and empty,
       the function checks for `{env_var}_ARN` (e.g., if env_var="WRENCH_SERVICE_SECRET",
       it checks "WRENCH_SERVICE_SECRET_ARN"). If this ARN env var is set, it is used
       for AWS Secrets Manager fetch. This enables services using ARN-only patterns
       without requiring callers to pass explicit ARN parameters.
    4. AWS Secrets Manager ARN: If both `value` and the environment variables fail to
       resolve, the function attempts to fetch the secret from AWS Secrets Manager
       using the provided ARN and region.

    If none of the above sources provide a non-empty secret, the function logs a
    warning and returns None.

    Parameters
    ----------
    value : str, optional
        A secret value provided directly. If non-empty, this takes highest priority
        and is returned immediately without consulting other sources. Default is None.

    env_var : str, optional
        The name of the environment variable to read if `value` is not provided.
        The function reads `os.environ.get(env_var)` and returns the result if
        non-empty. Default is "WRENCH_SERVICE_SECRET".

    arn : str, optional
        The AWS Secrets Manager ARN to fetch the secret from if both `value` and
        the environment variable fail to resolve. Requires boto3 to be installed
        and available. If boto3 is not installed, a warning is logged and this
        step is skipped. Default is None.

    region : str, optional
        The AWS region to use when connecting to Secrets Manager for ARN resolution.
        This is passed directly to the boto3 client. Default is "us-east-1".

    Returns
    -------
    str or None
        The resolved secret string if any source provides a non-empty value.
        Returns None if all sources fail or are empty. Never raises exceptions.

    Examples
    --------
    Direct value takes priority:

        >>> secret = resolve_secret(value="my-secret")
        >>> print(secret)
        "my-secret"

    Environment variable fallback:

        >>> import os
        >>> os.environ["CUSTOM_SECRET"] = "env-secret"
        >>> secret = resolve_secret(env_var="CUSTOM_SECRET")
        >>> print(secret)
        "env-secret"

    Auto-ARN convention (ARN injected via env var):

        >>> os.environ["WRENCH_SERVICE_SECRET_ARN"] = "arn:aws:secretsmanager:us-east-1:123456789:secret:my-secret"
        >>> secret = resolve_secret(env_var="WRENCH_SERVICE_SECRET")
        >>> # Fetches from SM because WRENCH_SERVICE_SECRET is empty but _ARN is set

    ARN resolution (requires boto3):

        >>> secret = resolve_secret(arn="arn:aws:secretsmanager:us-east-1:123456789:secret:my-secret")
        >>> print(secret)
        "fetched-from-secrets-manager"

    Fallback chain:

        >>> secret = resolve_secret(
        ...     value=None,
        ...     env_var="MY_SECRET_ENV",
        ...     arn="arn:aws:secretsmanager:us-east-1:123456789:secret:my-secret"
        ... )
        >>> # Returns env var if set, otherwise attempts ARN fetch, otherwise None.

    Notes
    -----
    - Direct values and environment variables are preferred because they are
      always available. ARN resolution is only attempted as a last resort.
    - boto3 is optional and required only for ARN resolution. If ARN is provided
      but boto3 is not installed, a clear warning is logged and the function
      continues to other sources or returns None.
    - All errors during ARN resolution (API failures, invalid ARNs, network issues)
      are caught, logged, and treated as if the source failed.
    - This function is designed to be used in service-to-service communication
      patterns where secrets are injected via environment variables or fetched
      from AWS at runtime.
    """
    if value is not None and value:
        return value

    if env_var is not None:
        env_value = os.environ.get(env_var)
        if env_value is not None and env_value:
            return env_value

    # Auto-derive ARN from env var name convention when no explicit ARN was passed
    if arn is None and env_var is not None:
        auto_arn = os.environ.get(f"{env_var}_ARN")
        if auto_arn:
            arn = auto_arn

    if arn is not None:
        try:
            import boto3
        except ImportError:
            logger.warning(
                "resolve_secret: boto3 is required to fetch secrets by ARN. "
                "Install WrenchCL[aws]."
            )
            return None

        try:
            client = boto3.client("secretsmanager", region_name=region)
            response = client.get_secret_value(SecretId=arn)
            secret_value = response.get("SecretString")
            if secret_value is not None and secret_value:
                return secret_value
        except Exception as exc:
            logger.warning(
                f"resolve_secret: Failed to fetch secret from ARN: {str(exc)}"
            )
            return None

    logger.warning(
        f"resolve_secret: no secret could be resolved from value, "
        f"env_var={env_var!r}, arn={arn!r}"
    )
    return None

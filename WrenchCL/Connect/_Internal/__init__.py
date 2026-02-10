#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
"""Internal utilities - some require AWS dependencies."""

# AWS-dependent utilities - fail fast if not available
try:
    import boto3
    import botocore
    from sshtunnel import SSHTunnelForwarder

    assert SSHTunnelForwarder
    assert botocore
    assert boto3
    from ._boto_cache import _fetch_secret_from_secretsmanager, _get_boto3_session, _get_s3_client
    from ._ConfigurationManager import _ConfigurationManager
    from ._SshTunnelManager import _SshTunnelManager

except ImportError as e:
    raise ImportError(
        f"Internal AWS utilities require additional dependencies.\n"
        f"Install with: pip install 'WrenchCL[aws]'\n"
        f"Missing: {e}"
    ) from e

__all__ = [
    "_ConfigurationManager",
    "_SshTunnelManager",
    "_get_boto3_session",
    "_fetch_secret_from_secretsmanager",
    "_get_s3_client",
]

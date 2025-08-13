"""AWS service integrations - requires 'aws' extra."""

try:
    # Test all required AWS dependencies
    import boto3
    import psycopg2
    import paramiko
    from sshtunnel import SSHTunnelForwarder
    import botocore

    # Import our AWS classes
    from .AwsClientHub import AwsClientHub
    from .RdsServiceGateway import RdsServiceGateway
    from .S3ServiceGateway import S3ServiceGateway
    from .Lambda import handle_lambda_response

except ImportError as e:
    raise ImportError(
        f"AWS functionality requires additional dependencies.\n"
        f"Install with: pip install 'WrenchCL[aws]'\n"
        f"Missing: {e}"
    ) from e

__all__ = ['AwsClientHub', 'RdsServiceGateway', 'S3ServiceGateway', 'handle_lambda_response']
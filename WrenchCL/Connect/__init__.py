"""AWS service integrations - requires 'aws' extra."""

try:
    # Test all required AWS dependencies first
    import boto3
    import psycopg2
    import paramiko
    from sshtunnel import SSHTunnelForwarder
    import botocore

    # Now try to import our classes (which may have additional dependencies)
    from .AwsClientHub import AwsClientHub
    from .RdsServiceGateway import RdsServiceGateway
    from .S3ServiceGateway import S3ServiceGateway
    from .Lambda import handle_lambda_response

except ImportError as e:
    # Create a more specific error message based on what failed
    error_details = str(e)

    # Map common errors to specific packages
    if "boto3" in error_details:
        missing_pkg = "boto3 and related AWS packages"
    elif "psycopg2" in error_details:
        missing_pkg = "psycopg2-binary (PostgreSQL adapter)"
    elif "paramiko" in error_details:
        missing_pkg = "paramiko (SSH client)"
    elif "sshtunnel" in error_details:
        missing_pkg = "sshtunnel (SSH tunneling)"
    elif "botocore" in error_details:
        missing_pkg = "botocore and related AWS type stubs"
    else:
        missing_pkg = "AWS-related dependencies"

    raise ImportError(
        f"AWS functionality requires additional dependencies.\n"
        f"Missing: {missing_pkg}\n"
        f"Install with: pip install 'WrenchCL[aws]'\n"
        f"Original error: {error_details}"
    ) from e

__all__ = ['AwsClientHub', 'RdsServiceGateway', 'S3ServiceGateway', 'handle_lambda_response']
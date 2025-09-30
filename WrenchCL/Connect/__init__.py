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
    messages = []
    # Map common errors to specific packages
    if "boto3" in error_details:
        messages.append("boto3 and related AWS packages")
    elif "psycopg2" in error_details:
        messages.append("psycopg2-binary (PostgreSQL adapter)")
    elif "paramiko" in error_details:
        messages.append("paramiko (SSH client)")
    elif "sshtunnel" in error_details:
        messages.append("sshtunnel (SSH tunneling)")
    elif "botocore" in error_details:
        messages.append("botocore and related AWS type stubs")
    else:
        messages.append("AWS-related dependencies")
    missing_pkg = "\n  -".join(messages)
    raise ImportError(
            f"AWS functionality requires additional dependencies.\n"
            f"Missing Packages:\n  -{missing_pkg}\n"
            f"Install with: pip install 'WrenchCL[aws]'\n"
            f"Original error: {error_details}"
            ) from e

__all__ = ['AwsClientHub', 'RdsServiceGateway', 'S3ServiceGateway', 'handle_lambda_response']

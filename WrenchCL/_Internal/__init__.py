"""AWS service integrations - requires 'aws' extra."""

__all__ = []

# Always try to import AWS functionality
try:
    import boto3
    import psycopg2
    import paramiko
    from sshtunnel import SSHTunnelForwarder
    import botocore

    from .AwsClientHub import AwsClientHub
    from .RdsServiceGateway import RdsServiceGateway
    from .S3ServiceGateway import S3ServiceGateway
    from .Lambda import handle_lambda_response

    __all__.extend(['AwsClientHub', 'RdsServiceGateway', 'S3ServiceGateway', 'handle_lambda_response'])

except ImportError as e:
    # Don't export anything if dependencies missing
    _aws_import_error = e

def __getattr__(name):
    """Called when someone tries to import something not in __all__."""
    if name in ['AwsClientHub', 'RdsServiceGateway', 'S3ServiceGateway', 'handle_lambda_response']:
        raise ImportError(
            f"AWS functionality requires additional dependencies.\n"
            f"Install with: pip install 'WrenchCL[aws]'\n"
            f"Missing: {_aws_import_error}"
        ) from _aws_import_error
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
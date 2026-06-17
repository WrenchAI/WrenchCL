"""AWS service integrations - requires 'aws' extra."""

import importlib.util
import sys


def _dep_available(name: str) -> bool:
    if name in sys.modules:
        return True
    try:
        return importlib.util.find_spec(name) is not None
    except (ValueError, ModuleNotFoundError):
        return False


_aws_deps = {
    "boto3": "boto3",
    "botocore": "botocore",
    "paramiko": "paramiko",
    "psycopg2": "psycopg2-binary",
    "sshtunnel": "sshtunnel",
}
_missing = [pkg for mod, pkg in _aws_deps.items() if not _dep_available(mod)]

if _missing:
    missing_str = "\n  -".join(_missing)
    raise ImportError(
        f"AWS functionality requires additional dependencies.\n"
        f"Missing Packages:\n  -{missing_str}\n"
        f"Install with: pip install 'WrenchCL[aws]'"
    ) from None

from .AwsClientHub import AwsClientHub
from .Lambda import handle_lambda_response
from .RdsServiceGateway import RdsServiceGateway
from .S3ServiceGateway import S3ServiceGateway

__all__ = ["AwsClientHub", "RdsServiceGateway", "S3ServiceGateway", "handle_lambda_response"]

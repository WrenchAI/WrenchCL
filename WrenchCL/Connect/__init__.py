#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

# WrenchCL/Connect/__init__.py
from WrenchCL import logger
try:
    from .AwsClientHub import *
    from .RdsServiceGateway import *
    from .S3ServiceGateway import *
    from .Lambda import *
except ImportError:
    logger.debug('WrenchCL.Connect not available due to missing optional dependencies')
    AwsClientHub = None
    RdsServiceGateway = None
    S3ServiceGateway = None
    Lambda = None
    pass

__all__ = ['RdsServiceGateway', 'S3ServiceGateway', 'AwsClientHub', 'handle_lambda_response']

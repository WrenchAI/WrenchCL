#  Copyright (c) 2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

from functools import lru_cache
from typing import Optional
try:
    from botocore.config import Config
    import boto3
    @lru_cache(maxsize=3)
    def _get_boto3_session(profile_name: str) -> boto3.Session:
        return boto3.session.Session(profile_name=profile_name)

    @lru_cache(maxsize=6)
    def _fetch_secret_from_secretsmanager(profile: str, region: str, secret_arn: str) -> str:
        client = _get_boto3_session(profile).client('secretsmanager', region_name=region)
        return client.get_secret_value(SecretId=secret_arn)['SecretString']

    @lru_cache(maxsize=3)
    def _get_s3_client(profile:str, region:str, config: Optional[Config] = None) -> boto3.client:
        client = _get_boto3_session(profile).client(service_name = 's3', region_name = region, config=config)
        return client
except ImportError:
    _get_boto3_session = None
    _fetch_secret_from_secretsmanager = None
    _get_s3_client = None
    Config = None
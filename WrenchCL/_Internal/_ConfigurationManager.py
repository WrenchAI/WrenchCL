#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from WrenchCL.Decorators import SingletonClass
from WrenchCL.Exceptions import InvalidConfigurationException
from WrenchCL.Tools import Maybe
from WrenchCL.Tools.ccLogBase import logger


@SingletonClass
class _ConfigurationManager:
    """
    Loads configuration for AWS credentials, RDS secrets, SSH tunnel setup, and DB options.
    Configuration is loaded in order: optional .env → environment vars → kwargs.
    """

    def __init__(self, ):
        self.reset()

    def initialize(self, env_path: Optional[str] = None, silent: bool = False, **kwargs):
        """
        Initialize config from .env (if provided), environment, and kwargs.

        :param env_path: Optional path to a .env file.
        :param kwargs: Override variables (e.g. AWS_PROFILE, SSH_SERVER).
        :raises InvalidConfigurationException: If SECRET_ARN is missing.
        """
        if env_path:
            self.env_path = env_path

        if self._initialized:
            if not silent:
                raise InvalidConfigurationException(config_name="InternalConfig",
                    reason = "Configuration has already been initialized. call reset() first.")
            else:
                return

        if self.env_path:
            try:
                load_dotenv(self._resolve_path(self.env_path), override=True)
            except Exception as e:
                logger.debug(f"Skipping .env load. Error: {e}")

        self._load_from_env()
        self._apply_overrides(kwargs)
        self._initialized = True

    def reset(self):
        """Reset config to its initial state."""
        self._initialized = False
        self.env_path = None

        # Core AWS / Secret config
        self.aws_profile: Optional[str] = None
        self.region_name: Optional[str] = None
        self.secret_arn: Optional[str] = None
        self.openai_api_key: Optional[str] = None
        self.aws_deployment: Optional[bool] = None

        # RDS Secret-based
        self.db_user: Optional[str] = None
        self.db_pass: Optional[str] = None
        self.db_host: Optional[str] = None
        self.db_port: Optional[int] = None
        self.db_name: Optional[str] = None

        # SSH fields (used if all required values are set)
        self.ssh_server: Optional[str] = None
        self.ssh_port: int = 22
        self.ssh_user: Optional[str] = None
        self.ssh_password: Optional[str] = None
        self.pem_path: Optional[str] = None

        # Overrides for tunnel target
        self.pghost_override: Optional[str] = None
        self.pgport_override: Optional[str] = None

        # Misc
        self.db_batch_size: int = 10000

    def _resolve_path(self, path: str) -> str:
        """Resolve relative paths to absolute paths."""
        return path if Path(path).is_absolute() else os.path.join(os.getcwd(), path)

    def _load_from_env(self):
        """Populate values from environment variables."""
        self.aws_profile = os.getenv("AWS_PROFILE", self.aws_profile)
        self.region_name = os.getenv("REGION_NAME", self.region_name)
        self.secret_arn = os.getenv("SECRET_ARN", self.secret_arn)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)

        self.ssh_server = os.getenv("SSH_SERVER", self.ssh_server)
        self.ssh_user = os.getenv("SSH_USER", self.ssh_user)
        self.ssh_password = os.getenv("SSH_PASSWORD", self.ssh_password)
        self.pem_path = os.getenv("PEM_PATH", self.pem_path)
        self.ssh_port = int(os.getenv("SSH_PORT", self.ssh_port))

        self.pghost_override = os.getenv("PGHOST_OVERRIDE", self.pghost_override)
        self.pgport_override = os.getenv("PGPORT_OVERRIDE", self.pgport_override)

        self.db_batch_size = int(os.getenv("DB_BATCH_OVERRIDE", self.db_batch_size))
        self.aws_deployment = str(os.getenv("AWS_DEPLOYMENT", self.aws_deployment)).lower() == "true"

    def _apply_overrides(self, kwargs: dict):
        """Apply keyword argument overrides."""
        self.aws_profile = kwargs.get("AWS_PROFILE", self.aws_profile)
        self.region_name = kwargs.get("REGION_NAME", self.region_name)
        self.secret_arn = kwargs.get("SECRET_ARN", self.secret_arn)
        self.openai_api_key = kwargs.get("OPENAI_API_KEY", self.openai_api_key)

        self.ssh_server = kwargs.get("SSH_SERVER", self.ssh_server)
        self.ssh_user = kwargs.get("SSH_USER", self.ssh_user)
        self.ssh_password = kwargs.get("SSH_PASSWORD", self.ssh_password)
        self.pem_path = kwargs.get("PEM_PATH", self.pem_path)
        self.ssh_port = int(kwargs.get("SSH_PORT", self.ssh_port))

        self.pghost_override = kwargs.get("PGHOST_OVERRIDE", self.pghost_override)
        self.pgport_override = kwargs.get("PGPORT_OVERRIDE", self.pgport_override)

        self.db_batch_size = int(kwargs.get("DB_BATCH_OVERRIDE", self.db_batch_size))
        self.aws_deployment = str(kwargs.get("AWS_DEPLOYMENT", self.aws_deployment)).lower() == "true"

    def load_rds_secret(self, secret_dict: dict):
        """Populate DB connection fields from a secret dictionary."""
        self.db_user = secret_dict.get("username") or self.db_user
        self.db_pass = secret_dict.get("password") or self.db_pass
        self.db_name = secret_dict.get("dbname") or self.db_name
        self.db_host = secret_dict.get("host") or self.db_host
        self.db_port = Maybe(secret_dict.get("port")).int().out() if secret_dict.get("port") else None
        if self.db_user and self.db_pass and self.db_name and self.db_host:
            return True
        else:
            return False

    def construct_db_uri(self) -> str:
        """Build a SQLAlchemy/Postgres URI from the current DB config."""
        host = self.pghost_override or self.db_host
        port = int(self.pgport_override or self.db_port or 5432)
        return f"postgresql://{self.db_user}:{self.db_pass}@{host}:{port}/{self.db_name}"

#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import json

from typing import Optional, Union

try:
    import psycopg2
    from WrenchCL._Internal._ConfigurationManager import _ConfigurationManager
    from WrenchCL._Internal._SshTunnelManager import _SshTunnelManager
    from WrenchCL._Internal._boto_cache import _get_boto3_session, _fetch_secret_from_secretsmanager
    from mypy_boto3_lambda.client import LambdaClient
    from mypy_boto3_rds.client import RDSClient
    from mypy_boto3_s3.client import S3Client
    from mypy_boto3_secretsmanager.client import SecretsManagerClient
    imports = True
except ImportError:
    psycopg2 = None
    LambdaClient = None
    RDSClient = None
    S3Client = None
    SecretsManagerClient = None
    _ConfigurationManager = None
    _SshTunnelManager = None
    _get_boto3_session = None
    _fetch_secret_from_secretsmanager = None
    imports = False

from WrenchCL.Decorators.SingletonClass import SingletonClass
from WrenchCL.Exceptions import InvalidConfigurationException
from WrenchCL._Internal.require_module import gate_imports
from WrenchCL.Tools.ccLogBase import logger


# noinspection PyUnresolvedReferences
@SingletonClass
class AwsClientHub:
    """
    Singleton manager for AWS clients and secrets, with optional SSH tunneling.

    This class wraps configuration loading, boto3 session management, and RDS/S3/SecretsManager clients.
    """

    def __init__(self, env_path: Optional[str] = None, **kwargs):
        """
        Initialize the AwsClientHub singleton.

        :param env_path: Optional path to a `.env` file.
        :param kwargs: Override values for configuration (e.g., `AWS_PROFILE`, `SECRET_ARN`, etc.).
        """
        self.__config: Optional[_ConfigurationManager] = None
        self.__env_path = env_path
        self.__kwargs = kwargs
        self.__db_client: Optional[RDSClient] = None
        self.__lambda = None
        self.__initialized = False
        self.__init_mode = False

    def _initialize(self, need_secret=False):
        """Load config and secrets if not already initialized."""
        if not self.__initialized:
            gate_imports(imports, 'aws', ['boto3', 'paramiko', 'psycopg2', '...'])
            try:
                self.reload_config(env_path=self.__env_path, **self.__kwargs)
                self.__initialized = True
            except InvalidConfigurationException as e:
                logger._internal_log(f"AWS Client Hub initialization deferred: {e}")
        if self.__initialized:
            if need_secret:
                self._load_rds_secret()

    def reload_config(self, env_path: Optional[str] = None, **kwargs):
        """
        Reload configuration and secrets using a given `.env` path or kwargs.

        :param env_path: Optional .env path.
        :param kwargs: Overrides for configuration values.
        """
        self.__config = _ConfigurationManager()
        self.__config.reset()
        self.__config.initialize(env_path=env_path, **kwargs)

    @property
    def config(self) -> "_ConfigurationManager":
        """Loaded configuration object."""
        self._initialize()
        return self.__config

    @property
    def db_uri(self) -> str:
        """Constructed Postgres URI from loaded secret."""
        self._initialize(True)
        return self.config.construct_db_uri()

    @property
    def db(self):
        """Postgres connection (via psycopg2) with optional SSH tunnel."""
        self._initialize(True)
        if self.__db_client is None:
            self._init_rds_client()
        return self.__db_client

    @property
    def s3(self):
        """Return a boto3 S3 client."""
        self._initialize()
        return self.session.client("s3", region_name=self.config.region_name)

    @property
    def secretmanager(self):
        """Return a boto3 SecretsManager client."""
        self._initialize()
        return self.session.client("secretsmanager", region_name=self.config.region_name)

    @property
    def lambda_client(self):
        """Return a boto3 Lambda client."""
        self._initialize(True)
        if self.__lambda is None:
            self.__lambda = self.session.client("lambda", region_name=self.config.region_name)
        return self.__lambda

    @property
    def session(self):
        """Return a cached boto3 Session."""
        self._initialize()
        return _get_boto3_session(self.config.aws_profile)

    def _load_rds_secret(self):
        """
        Load the RDS secret from SecretsManager.
        """

        parsed = {}
        try:
            secret = _fetch_secret_from_secretsmanager(
            profile=self.__config.aws_profile,
            region=self.__config.region_name,
            secret_arn=self.__config.secret_arn
            )
            parsed = json.loads(secret) if isinstance(secret, str) else secret
        finally:
            configured = self.__config.load_rds_secret(parsed)
            if not configured:
                raise InvalidConfigurationException("Missing required RDS configuration values.")
            else:
                pass

    def _init_rds_client(self):
        """
        Initialize the database client, applying PGHOST/PGPORT override or setting up an SSH tunnel if configured.
        """
        try:
            if self.config and isinstance(self.config, _ConfigurationManager):
                config = {
                    "PGHOST": self.config.pghost_override or self.config.db_host,
                    "PGPORT": int(self.config.pgport_override or self.config.db_port),
                    "PGDATABASE": self.config.db_name,
                    "PGUSER": self.config.db_user,
                    "PGPASSWORD": self.config.db_pass
                }

                if not self.config.pghost_override and all([
                    self.config.ssh_server,
                    self.config.ssh_user,
                    self.config.pem_path or self.config.ssh_password
                ]):
                    config["SSH_TUNNEL"] = {
                        "SSH_SERVER": self.config.ssh_server,
                        "SSH_PORT": self.config.ssh_port,
                        "SSH_USER": self.config.ssh_user,
                        "SSH_PASSWORD": self.config.ssh_password,
                        "SSH_KEY_PATH": self.config.pem_path
                    }

                self.__db_client = self._rds_handle_configuration(config)
            else:
                raise InvalidConfigurationException("Missing required config due to missing dependencies.")

        except Exception as e:
            logger.error(f"Failed to initialize DB client: {e}")
            raise

    def _rds_handle_configuration(self, config: dict) -> "psycopg2.extensions.connection":
        """
        Establish a psycopg2 connection directly or through an SSH tunnel.

        :param config: Dictionary with DB + optional SSH_TUNNEL keys.
        :returns: psycopg2 DB connection
        """
        host, port = config["PGHOST"], config["PGPORT"]

        if "SSH_TUNNEL" in config:
            try:
                self.ssh_manager = _SshTunnelManager(config)
                host, port = self.ssh_manager.start_tunnel()
                logger.debug("SSH Tunnel Connected")
            except Exception as e:
                logger.error(f"SSH Tunnel failed: {e}")
                raise

        return psycopg2.connect(
            host=host,
            port=port,
            database=config["PGDATABASE"],
            user=config["PGUSER"],
            password=config["PGPASSWORD"]
        )

    def get_secret(self, secret_id: str = None) -> Union[dict, str, None]:
        """
        Retrieve a secret by ARN or default from config.

        :param secret_id: Secret to fetch
        :return: Parsed dict or raw secret string
        """
        self._initialize()
        try:
            raw = self.secretmanager.get_secret_value(SecretId=secret_id)["SecretString"]
            try:
                return json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return raw
        except Exception as e:
            logger.error(f"Error retrieving secret from SecretsManager: {e}")
            raise

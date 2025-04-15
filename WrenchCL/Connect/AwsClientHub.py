

#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).

import json
import os
from functools import wraps
from typing import Optional, Union

import boto3
import psycopg2
from botocore.config import Config
from mypy_boto3_lambda.client import LambdaClient
from mypy_boto3_rds.client import RDSClient
from mypy_boto3_s3.client import S3Client
from mypy_boto3_secretsmanager.client import SecretsManagerClient

from ..Decorators.SingletonClass import SingletonClass
from ..Exceptions import IncompleteInitializationException
from ..Exceptions import InvalidConfigurationException
from ..Tools.WrenchLogger import _IntLogger
logger = _IntLogger()
from ..Tools.Coalesce import coalesce
from .._Internal._ConfigurationManager import _ConfigurationManager
from .._Internal._SshTunnelManager import _SshTunnelManager


def require_initialized(method):
    """
    A decorator to ensure that the instance is initialized before executing the method.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not getattr(self, '_initialized', False):
            raise IncompleteInitializationException(
                f"{self.__class__.__name__} is not fully initialized. "
                "Please ensure initialization is complete before calling this method."
            )
        return method(self, *args, **kwargs)
    return wrapper


@SingletonClass
class AwsClientHub:
    """
    Manages AWS client services including RDS and S3. Ensures that client instances are created as singletons to
    maintain efficient use of resources and consistency across operations.

    Attributes:
        config (_ConfigurationManager): Instance of the configuration manager.
        aws_session_client (boto3.session.Session): The AWS session client for accessing various AWS services.
        db_client (object): Client for interacting with AWS RDS databases.
        s3_client (object): Client for interacting with AWS S3 storage.
        need_ssh_tunnel (bool): Indicates if an SSH tunnel is required for database connections, based on secret data.
    """

    def __init__(self, env_path=None, **kwargs):
        """
        Initializes the AwsClientHub by setting up the AWS session and fetching necessary secrets for configuring
        other AWS services. Supports additional configuration via keyword arguments or environment variable overrides.

        :param env_path: The path to the environment configuration file.
        :type env_path: str, optional
        :param kwargs: Additional keyword arguments to pass to the configuration manager.
                       These can override default configurations such as:
            - AWS_PROFILE (str): AWS profile name for creating sessions.
            - REGION_NAME (str): AWS region name.
            - SECRET_ARN (str): ARN of the AWS Secrets Manager secret.
            - OPENAI_API_KEY (str): API key for OpenAI.
            - SSH_SERVER (str): SSH server address.
            - SSH_PORT (int): SSH server port.
            - SSH_USER (str): SSH username.
            - SSH_PASSWORD (str): SSH user password.
            - PEM_PATH (str): Path to the PEM file for SSH authentication.
            - DB_BATCH_OVERRIDE (int): Batch size for database operations.
            - AWS_DEPLOYMENT (bool): Indicates if the deployment is on AWS, affecting SSH tunnel configuration.

        Note:
            The following environment variables can override the default configuration:
            - `PGHOST_OVERRIDE`: Overrides the RDS host specified in the secret. Used to access existing Tunnels.
            - `PGPORT_OVERRIDE`: Overrides the RDS port specified in the secret. Used to access existing Tunnels.
        """
        boto3.set_stream_logger(name='botocore.credentials', level=40)
        self.lambda_client = None
        self.config: Union[None, _ConfigurationManager] = None
        self.aws_session_client = None
        self.env_path = env_path
        self.kwargs = kwargs
        self.db_client = None
        self.s3_client = None
        self.secret_client = None
        self.need_ssh_tunnel = False
        self._kwargs = kwargs
        self._initialized = False
        self._recursive_depth = 0

    def __getattribute__(self, name):
        # Avoid recursive initialization logic
        if name == "_recursive_depth" or name == "_initialized" or name == '_kwargs':
            return object.__getattribute__(self, name)

        # Check initialization state
        if not object.__getattribute__(self, "_initialized") and object.__getattribute__(self, "_recursive_depth") == 0:
            object.__setattr__(self, "_recursive_depth", 1)
            try:
                self._initialize()
            finally:
                object.__setattr__(self, "_recursive_depth", 0)

        # Proceed with regular attribute access
        return object.__getattribute__(self, name)

    def _initialize(self):
        """
        Ensures the instance is initialized, attempting to initialize if necessary.
        """
        if not self._initialized:
            try:
                self.reload_config(env_path=self.env_path, **self.kwargs)
                self._initialized = True
            except InvalidConfigurationException as e:
                logger.debug(
                    f"AWS Client Hub initialization deferred, awaiting completion of environment initialization. Details: {str(e)}."
                )


    def reload_config(self, env_path=None, **kwargs):
        """
        Reloads the configuration from the specified environment path.

        :param env_path: The path to the environment configuration file.
        :type env_path: str, optional
        :param kwargs: Additional keyword arguments to pass to the configuration manager.
        """
        self.config = _ConfigurationManager(env_path=env_path, **kwargs)
        self._get_config_secret()

    def get_config(self):
        """
        Retrieves and returns the ConfigurationManager instance, initializing it if not already done.

        :returns: The initialized ConfigurationManager instance.
        :rtype: _ConfigurationManager

        :Usage:
            config = client_manager.get_config()
        """
        if self.config is None:
            self.reload_config(**self._kwargs)
        return self.config


    @require_initialized
    def get_db_uri(self) -> str:
        """
        Constructs and returns the database URI from the secret configuration.

        :returns: The database URI.
        :rtype: str
        """
        return self.config.construct_db_uri()


    @require_initialized
    def get_db_client(self) -> RDSClient:
        """
        Retrieves and returns the database client instance, initializing it if not already done.

        :returns: The initialized database client instance.
        :rtype: RDSClient

        :Usage:
            db_client = client_manager.get_db_client()
        """
        if self.db_client is None:
            self._init_rds_client()
        return self.db_client

    @require_initialized
    def get_s3_client(self, config: Optional[Config] = None, force_refresh: bool = False) -> S3Client:
        """
        Retrieves and returns the S3 client instance, initializing it if not already done.

        :param config: Optional configuration to initialize the S3 client. Defaults to None.
        :type config: Config, optional
        :param force_refresh: Flag to force re-initialization of the S3 client with the given config. Defaults to False.
        :type force_refresh: bool
        :returns: The initialized S3 client instance.
        :rtype: S3Client

        :Usage:
            s3_client = client_manager.get_s3_client()
            s3_client = client_manager.get_s3_client(config={'region_name': 'us-west-1'}, force_refresh=True)
        """
        if self.s3_client is None or force_refresh:
            self._init_s3_client(config)
        return self.s3_client

    @require_initialized
    def get_secret_client(self):
        """
        Retrieves and returns an AWS Secretmanager service client instance, initializing it if not already done.

        :returns: The initialized AWS Secretmanager client instance.
        :rtype: SecretsManagerClient
        """
        if self.secret_client is None:
            self.secret_client = self._init_other_client(aws_service='secretsmanager')
        return self.secret_client

    @require_initialized
    def get_lambda_client(self):
        """
        Retrieves and returns an AWS Lambda service client instance, initializing it if not already done.

        :returns: The initialized AWS Lambda client instance.
        :rtype: LambdaClient
        """
        if self.lambda_client is None:
            self.lambda_client = self._init_other_client(aws_service='lambda')
        return self.lambda_client

    @require_initialized
    def get_service_client(self, aws_service):
        """
        Retrieves and returns an AWS service client instance, initializing it if not already done.

        :param aws_service: The name of the AWS service.
        :type aws_service: str

        :returns: The initialized AWS service client instance.
        """
        return self._init_other_client(aws_service=aws_service)

    @require_initialized
    def _init_rds_client(self):
        """
        Initializes the RDS client with the necessary configuration derived from the AWS secrets manager.

        :raises Exception: If there is an issue initializing the RDS client.
        """
        pghost_env_override = self.config.pghost_override
        pgport_env_override = self.config.pgport_override

        try:
            config = dict(
                PGHOST=pghost_env_override or self.config.db_host,
                PGPORT=int(pgport_env_override or self.config.db_port),
                PGDATABASE=self.config.db_name,
                PGUSER=self.config.db_user,
                PGPASSWORD=self.config.db_pass
            )

            if self.need_ssh_tunnel:
                if self.config.qa_host_check in self.config.db_host:
                    config['SSH_TUNNEL'] = dict(
                        SSH_SERVER=coalesce(self.config.ssh_server, '34.201.30.245'),
                        SSH_PORT=coalesce(self.config.ssh_port, 22),
                        SSH_USER=coalesce(self.config.ssh_user, "ec2-user"),
                        SSH_PASSWORD=coalesce(self.config.ssh_password, None),
                        SSH_KEY_PATH=coalesce(self.config.pem_path, None)
                    )
                elif self.config.dev_host_check in self.config.db_host:
                    config['SSH_TUNNEL'] = dict(
                        SSH_SERVER=coalesce(self.config.ssh_server, '44.193.207.105'),
                        SSH_PORT=coalesce(self.config.ssh_port, 22),
                        SSH_USER=coalesce(self.config.ssh_user, "ec2-user"),
                        SSH_PASSWORD=coalesce(self.config.ssh_password, None),
                        SSH_KEY_PATH=coalesce(self.config.pem_path, None)
                    )
                else:
                    config['SSH_TUNNEL'] = dict(
                        SSH_SERVER=self.config.ssh_server,
                        SSH_PORT=self.config.ssh_port,
                        SSH_USER=self.config.ssh_user,
                        SSH_PASSWORD=self.config.ssh_password,
                        SSH_KEY_PATH=self.config.pem_path
                    )

            self.db_client = self._rds_handle_configuration(config)
        except Exception as e:
            logger.error(f"An exception occurred when initializing connection to DB: {e}")
            raise e

    @require_initialized
    def _rds_handle_configuration(self, config):
        """
        Sets up a psycopg2 Connection using a specified config.

        :param config: The configuration dictionary for the RDS connection.
        :type config: dict

        :returns: The database client connection.
        :rtype: psycopg2.extensions.connection
        """
        host, port = config['PGHOST'], config['PGPORT']

        if 'SSH_TUNNEL' in config:
            try:
                self.ssh_manager = _SshTunnelManager(config)
                host, port = self.ssh_manager.start_tunnel()
                logger.debug("SSH Tunnel Connected")
            except ValueError:
                pass
            except Exception as e:
                logger.error(f"SSH Tunnel failed: {e}")
                raise e

        db_client = psycopg2.connect(host=host, port=port, database=config['PGDATABASE'], user=config['PGUSER'],
                                     password=config['PGPASSWORD'])

        return db_client

    @require_initialized
    def _init_s3_client(self, config=None):
        """
        Initializes the S3 client, setting it up with the correct region configuration.

        :raises Exception: If there is an issue initializing the S3 client.
        """
        try:
            logger.debug(f"Creating session with profile: {self.aws_session_client.profile_name} and region: {self.config.region_name} for service [s3]...")
            self.s3_client = self.aws_session_client.client('s3', region_name=self.config.region_name, config=config)
            logger.debug(f"S3 client initialized with region: {self.config.region_name}")
        except Exception as e:
            logger.error(f"An exception occurred when initializing connection to S3: {e}")
            raise e

    @require_initialized
    def _init_other_client(self, aws_service):
        """
        Initializes an AWS service client, setting it up with the correct region configuration.

        :param aws_service: The name of the AWS service.
        :type aws_service: str

        :raises Exception: If there is an issue initializing the AWS service client.
        """
        try:
            logger.debug(f"Creating session with profile: {self.aws_session_client.profile_name} and region: {self.config.region_name} for service [{aws_service}]")
            client = self.aws_session_client.client(aws_service, region_name=self.config.region_name)
            logger.debug(f"{aws_service} client initialized with region: {self.config.region_name} and profile: {self.aws_session_client.profile_name}")
            return client
        except Exception as e:
            logger.error(f"An exception occurred when initializing connection to {aws_service}: {e}")
            raise e

    def _get_config_secret(self, secret_id=None) -> Optional[dict]:
        """
        Fetches and decodes the secret configuration from AWS Secrets Manager, setting up necessary client
        configuration and determining if SSH tunneling is required.

        :param secret_id: Optional; The ID of the secret to fetch. If not provided, uses the default secret ARN from the configuration.
        :type secret_id: str, optional

        :raises Exception: If there is an error fetching or interpreting the secret.
        :raises ValueError: If the secret string is invalid.

        :returns: The secret configuration as a dictionary if `secret_id` is provided.
        :rtype: dict, optional
        """
        try:
            sec_id = self.config.secret_arn if secret_id is None else secret_id
            logger.debug(f"Creating session with profile: {self.config.aws_profile}")
            self.aws_session_client = boto3.session.Session(profile_name=self.config.aws_profile)
            client_object = self.aws_session_client.client('secretsmanager', region_name=self.config.region_name)
            secret_data = client_object.get_secret_value(SecretId=sec_id)['SecretString']
            try:
                secret_string = json.loads(secret_data)
            except json.JSONDecodeError:
                secret_string = secret_data

            if secret_string is None:
                raise ValueError(f"Invalid secret string found {secret_string}")

            self.config.load_rds_secret(secret_string)

            if secret_id is not None:
                return secret_string
            else:
                self._determine_need_for_tunnel()
        except Exception as e:
            logger.error(f"An exception occurred when getting credentials from AWS: {e}")
            raise e

    @require_initialized
    def get_secret(self, secret_id=None) -> Optional[dict] | Optional[str]:
        """
        Fetches and decodes the secret configuration from AWS Secrets Manager, setting up necessary client
        configuration and determining if SSH tunneling is required.

        :param secret_id: Optional; The ID of the secret to fetch. If not provided, uses the default secret ARN from the configuration.
        :type secret_id: str, optional

        :raises Exception: If there is an error fetching or interpreting the secret.
        :raises ValueError: If the secret string is invalid.

        :returns: The secret configuration as a dictionary if `secret_id` is provided.
        :rtype: dict, optional
        """
        try:
            if not self.secret_client:
                self.secret_client = self.aws_session_client.client('secretsmanager', region_name=self.config.region_name)
            secret_data = self.secret_client.get_secret_value(SecretId=secret_id)
            try:
                secret_data = json.loads(secret_data)
            except (json.JSONDecodeError, TypeError):
                pass

            return secret_data

        except Exception as e:
            logger.error(f"An exception occurred when getting Secret from AWS: {e}")
            raise e


    def _determine_need_for_tunnel(self):
        """
        Determines whether an SSH tunnel is required based on various configuration checks.

        The method performs the following checks in sequence to determine if an SSH tunnel should be established:

        1. **Host Check (QA/Dev/Prod)**:
           - If the host string from the secret matches `qa_host_check`, `dev_host_check`, or `prod_host_check` in the configuration:
               - If `qa_host_check` is found, an SSH tunnel may be required.
               - If `dev_host_check` is found, an SSH tunnel may be required.
               - If `prod_host_check` is found, it indicates the program is running in production, and no SSH tunnel is required. The process stops here.
           - If none of these checks pass the server passed is unknown and no assumption on ssh requirements can be made, the method continues with further checks.

        2. **AWS Deployment Flag**:
           - If the `aws_deployment` flag is `False`, it indicates a local or non-AWS environment, which may require an SSH tunnel.
           - If the flag is `True`, no tunnel is required, and the process stops.

        3. **PGHOST Override**:
           - If the `PGHOST_OVERRIDE` environment variable is not set, the host specified in the secret is used.
           - If `PGHOST_OVERRIDE` is set, no tunnel is required, and the process stops.

        4. **SSH Tunnel Credentials**:
           - The method checks for the presence of SSH credentials such as PEM path or SSH password.
           - If neither is present, it logs an error and proceeds without creating an SSH tunnel.

        The method sets `self.need_ssh_tunnel` to `True` if all the checks pass and credentials are provided. If any check fails, it stops further processing and logs that no SSH tunnel is required.

        Raises:
            - Logs errors and warnings as necessary based on the checks performed.
        """
        continue_flag = False

        # host check
        if self.config.qa_host_check in self.config.db_host:
            logger.debug(f"QA host check passed: {self.config.qa_host_check} found in secret string host: {self.config.db_host}")
        elif self.config.dev_host_check in self.config.db_host:
            logger.debug(f"Dev host check passed: {self.config.dev_host_check} found in secret string host: {self.config.db_host}")
        elif self.config.prod_host_check in self.config.db_host:
            logger.debug(f"Running on Production: No SSH tunnel required, continuing.")
            continue_flag = True
        else:
            pass

        # AWS deployment flag check
        if not continue_flag:
            if not self.config.aws_deployment:
                logger.debug("AWS deployment flag is false, indicating a local or non-AWS environment.")
            else:
                logger.debug("AWS deployment flag is true, indicating an AWS environment. No SSH tunnel required, continuing.")
                continue_flag = True

        # PGHOST_OVERRIDE check
        if not continue_flag:
            if os.getenv("PGHOST_OVERRIDE") is None:
                logger.debug("No PGHOST_OVERRIDE environment variable detected, defaulting to using secret host.")
            else:
                logger.debug(f"PGHOST_OVERRIDE environment variable detected: {os.getenv('PGHOST_OVERRIDE')}. No SSH tunnel required, continuing.")
                continue_flag = True

        # SSH tunnel configuration check
        if not continue_flag:
            if self.config.pem_path is not None:
                logger.debug(f"SSH PEM path is specified: {self.config.pem_path}")
            elif self.config.ssh_password is not None:
                logger.debug("SSH password is specified.")
            elif self.config.ssh_server is not None:
                logger.error("No SSH credentials (PEM path or SSH password) provided. SSH credentials should be given, but proceeding without creating a tunnel.")
            else:
                logger.debug("No SSH arguments given, proceeding without creating a tunnel.")
                continue_flag = True

        # Final check: if all checks pass but no credentials are provided
        if not continue_flag:
            logger.debug("All conditions met for SSH tunnel.")
            self.need_ssh_tunnel = True
        else:
            logger.debug("Determined no need for SSH tunnel creation.")

    def _mask_sensitive(self, value):
        """
        Masks sensitive information, showing only the first and last 3 characters.

        :param value: The sensitive value to mask.
        :type value: str
        :returns: The masked value.
        :rtype: str
        """
        if value and isinstance(value, str) and len(value) > 6:
            return f"{value[:3]}...{value[-3:]}"
        return value

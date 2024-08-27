#  Copyright (c) $YEAR$. Copyright (c) $YEAR$ Wrench.AI., Willem van der Schans, Jeong Kim
#
#  MIT License
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#  All works within the Software are owned by their respective creators and are distributed by Wrench.AI.
#
#  For inquiries, please contact Willem van der Schans through the official Wrench.AI channels or directly via GitHub at [Kydoimos97](https://github.com/Kydoimos97).
#


import json
import os
from typing import Optional

import boto3
import psycopg2
from botocore.config import Config

from ..Decorators.SingletonClass import SingletonClass
from ..Tools.WrenchLogger import Logger
from .._Internal._ConfigurationManager import _ConfigurationManager
from .._Internal._SshTunnelManager import _SshTunnelManager

logger = Logger()
from ..Tools.Coalesce import coalesce
from mypy_boto3_s3.client import S3Client
from mypy_boto3_rds.client import RDSClient
from mypy_boto3_secretsmanager.client import SecretsManagerClient
from mypy_boto3_lambda.client import LambdaClient


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
        self.config = None
        self.aws_session_client = None
        self.db_client = None
        self.s3_client = None
        self.secret_client = None
        self.secret_string = None
        self.need_ssh_tunnel = False
        self._kwargs = kwargs  # Store kwargs as an instance variable
        self.reload_config(env_path=env_path, **kwargs)
        self.get_secret()
        self._initialized = True

    def reload_config(self, env_path=None, **kwargs):
        """
        Reloads the configuration from the specified environment path.

        :param env_path: The path to the environment configuration file.
        :type env_path: str, optional
        :param kwargs: Additional keyword arguments to pass to the configuration manager.
        """
        self.config = _ConfigurationManager(env_path=env_path, **kwargs)

    def get_config(self):
        """
        Retrieves and returns the ConfigurationManager instance, initializing it if not already done.

        :returns: The initialized ConfigurationManager instance.
        :rtype: _ConfigurationManager

        :Usage:
            config = client_manager.get_config()
        """
        if self.config is None:
            self.reload_config(**self._kwargs)  # Use stored kwargs when reloading the config
        return self.config

    def get_db_uri(self) -> str:
        """
        Constructs and returns the database URI from the secret configuration.

        :returns: The database URI.
        :rtype: str
        """
        RDS_DB_NAME = self.secret_string.get('dbname')
        RDS_ENDPOINT = self.secret_string.get('host')
        RDS_PASSWORD = self.secret_string.get('password')
        RDS_PORT = int(self.secret_string.get('port', 0))
        RDS_USERNAME = self.secret_string.get('username')

        RDS_URI = f"postgresql://{RDS_USERNAME}:{RDS_PASSWORD}@{RDS_ENDPOINT}:{RDS_PORT}/{RDS_DB_NAME}"
        return RDS_URI

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


    def get_secret_client(self):
        """
        Retrieves and returns an AWS Secretmanager service client instance, initializing it if not already done.

        :returns: The initialized AWS Secretmanager client instance.
        :rtype: SecretsManagerClient
        """
        if self.secret_client is None:
            self.secret_client = self._init_other_client(aws_service='secretsmanager')
        return self.secret_client

    def get_lambda_client(self):
        """
        Retrieves and returns an AWS Lambda service client instance, initializing it if not already done.

        :returns: The initialized AWS Lambda client instance.
        :rtype: LambdaClient
        """
        if self.lambda_client is None:
            self.lambda_client = self._init_other_client(aws_service='lambda')
        return self.lambda_client

    def get_service_client(self, aws_service):
        """
        Retrieves and returns an AWS service client instance, initializing it if not already done.

        :param aws_service: The name of the AWS service.
        :type aws_service: str

        :returns: The initialized AWS service client instance.
        """
        return self._init_other_client(aws_service=aws_service)

    def _init_rds_client(self):
        """
        Initializes the RDS client with the necessary configuration derived from the AWS secrets manager.

        :raises Exception: If there is an issue initializing the RDS client.
        """
        pghost_env_override = os.getenv("PGHOST_OVERRIDE")
        pgport_env_override = os.getenv("PGPORT_OVERRIDE")


        try:
            config = dict(PGHOST=self.secret_string['host'] if pghost_env_override is None else pghost_env_override,
                          PGPORT=int(self.secret_string['port']) if pgport_env_override is None else int(pgport_env_override),
                          PGDATABASE=self.secret_string['dbname'], PGUSER=self.secret_string['username'],
                          PGPASSWORD=self.secret_string['password'])

            if self.need_ssh_tunnel:
                config['SSH_TUNNEL'] = dict(SSH_SERVER=coalesce(self.config.ssh_server, '34.201.30.245'),
                                            SSH_PORT=coalesce(self.config.ssh_port, 22),
                                            SSH_USER=coalesce(self.config.ssh_user, "ec2-user"),
                                            SSH_PASSWORD=coalesce(self.config.ssh_password, None),
                                            SSH_KEY_PATH=coalesce(self.config.pem_path, None))

            self.db_client = self._rds_handle_configuration(config)
        except Exception as e:
            logger.error(f"An exception occurred when initializing connection to DB: {e}")
            raise e

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
                raise e
        logger.debug(f"Connecting to DB with {host}.{port} ")

        db_client = psycopg2.connect(host=host, port=port, database=config['PGDATABASE'], user=config['PGUSER'],
                                     password=config['PGPASSWORD'])

        return db_client

    def _init_s3_client(self, config=None):
        """
        Initializes the S3 client, setting it up with the correct region configuration.

        :raises Exception: If there is an issue initializing the S3 client.
        """
        try:
            self.s3_client = self.aws_session_client.client('s3', region_name=self.config.region_name, config=config)
        except Exception as e:
            logger.error(f"An exception occurred when initializing connection to S3: {e}")
            raise e

    def _init_other_client(self, aws_service):
        """
        Initializes an AWS service client, setting it up with the correct region configuration.

        :param aws_service: The name of the AWS service.
        :type aws_service: str

        :raises Exception: If there is an issue initializing the AWS service client.
        """
        try:
            return self.aws_session_client.client(aws_service, region_name=self.config.region_name)
        except Exception as e:
            logger.error(f"An exception occurred when initializing connection to {aws_service}: {e}")
            raise e

    def get_secret(self, secret_id=None) -> Optional[dict]:
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
            self.aws_session_client = boto3.session.Session(profile_name=self.config.aws_profile)
            client_object = self.aws_session_client.client('secretsmanager', region_name=self.config.region_name)
            secret_data = client_object.get_secret_value(SecretId=sec_id)['SecretString']
            self.secret_string = json.loads(secret_data)

            if self.secret_string is None:
                raise ValueError(f"Invalid secret string found {self.secret_string}")

            if secret_id is not None:
                return self.secret_string
            else:
                if self.config.qa_host_check in self.secret_string['host'] and not self.config.aws_deployment:
                    self.need_ssh_tunnel = True

        except Exception as e:
            logger.error(f"An exception occurred when getting credentials from AWS: {e}")
            raise e

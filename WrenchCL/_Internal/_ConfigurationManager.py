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


import os
from pathlib import Path

from dotenv import load_dotenv

from ..Tools.WrenchLogger import Logger

logger = Logger()


class _ConfigurationManager:
    """
    Manages the configuration settings for the application, including AWS and OpenAI credentials, SSH details,
    and database batch size. Configurations can be initialized from environment files, environment variables,
    or keyword arguments.

    Attributes:
        env_path (str): The path to the environment file.
        aws_profile (str): AWS profile name for creating sessions.
        region_name (str): AWS region name.
        secret_arn (str): ARN of the AWS Secrets Manager secret.
        openai_api_key (str): API key for OpenAI.
        ssh_server (str): SSH server address.
        ssh_port (int): SSH server port.
        ssh_user (str): SSH username.
        ssh_password (str): SSH user password.
        pem_path (str): Path to the PEM file for SSH authentication.
        qa_host_check (str): Host check identifier for QA environment.
        db_batch_size (int): Batch size for database operations.
        aws_deployment (bool): Override for ssh tunnel on QA (when actively deployed on aws shh tunnel is off)
    """

    def __init__(self, env_path=None, **kwargs):
        """
        Initializes the ConfigurationManager by loading configurations from the specified environment file,
        environment variables, and keyword arguments.

        :param env_path: The path to the environment configuration file.
        :type env_path: str, optional
        :param kwargs: Additional configuration parameters.
        """
        self.env_path = env_path

        # Initialize default values
        self.aws_profile = None
        self.region_name = None
        self.secret_arn = None
        self.openai_api_key = None
        self.ssh_server = None
        self.ssh_port = None
        self.ssh_user = None
        self.ssh_password = None
        self.pem_path = None
        self.qa_host_check = 'ce5sivkxtgbs'
        self.db_batch_size = 10000
        self.aws_deployment = None

        try:
            self._initialize_env()
        except Exception as e:
            logger.HDL_WARN(f"No env file found to load trying existing variables {e}")
        self._init_from_env()
        self._init_from_kwargs(kwargs)

        if self.secret_arn is None:
            err_string = "Error in loading environment variables, Secret ARN is missing"
            logger.error(err_string)
            raise ValueError(err_string)

    def _initialize_env(self):
        """
        Loads the environment variables from the specified .env file.
        """
        if self.env_path:
            env_path = self._resolve_path(self.env_path)
        else:
            env_path = self._find_env_file()

        logger.debug(f"Env file path: {env_path}")
        load_dotenv(env_path)

    def _resolve_path(self, path):
        """
        Resolves the given path to an absolute path.

        :param path: The relative or absolute path.
        :type path: str
        :returns: The absolute path.
        :rtype: str
        """
        if Path(path).is_absolute():
            return path
        return os.path.join(os.getcwd(), path)

    def _find_env_file(self):
        """
        Searches for the .env file in several potential locations.

        :returns: The path to the found .env file.
        :rtype: str
        :raises FileNotFoundError: If no .env file is found in the expected locations.
        """
        # Check different potential locations for the .env file
        possible_paths = [Path(__file__).resolve().parent,  # Current directory
                          Path(os.getcwd()),  # Working directory
                          Path(os.getcwd()).joinpath('Resources', 'Secrets'),
                          Path(os.getcwd()).joinpath('resources', 'secrets'),
                          Path(os.getcwd()).parent.joinpath('Resources', 'Secrets'),
                          Path(os.getcwd()).parent.joinpath('resources', 'secrets'),
                          Path(os.getcwd()).parent.parent.joinpath('Resources', 'Secrets'),
                          Path(os.getcwd()).parent.parent.joinpath('resources', 'secrets')]

        for base_path in possible_paths:
            if not str(base_path).endswith('.env'):
                env_path = base_path.joinpath('.env')
            else:
                env_path = base_path
            if env_path.exists():
                return str(env_path)
        raise FileNotFoundError("No .env file found in expected locations.")

    def _init_from_kwargs(self, kwargs):
        """
        Initializes configuration values from keyword arguments.

        :param kwargs: Additional configuration parameters.
        :type kwargs: dict
        """
        self.aws_profile = kwargs.get('AWS_PROFILE', self.aws_profile)
        self.region_name = kwargs.get('REGION_NAME', self.region_name)
        self.secret_arn = kwargs.get('SECRET_ARN', self.secret_arn)
        self.openai_api_key = kwargs.get('OPENAI_API_KEY', self.openai_api_key)
        self.ssh_server = kwargs.get('SSH_SERVER', self.ssh_server)
        self.ssh_port = int(kwargs.get('SSH_PORT', self.ssh_port or 22))
        self.ssh_user = kwargs.get('SSH_USER', self.ssh_user)
        self.ssh_password = kwargs.get('SSH_PASSWORD', self.ssh_password)
        self.pem_path = kwargs.get('PEM_PATH', self.pem_path)
        self.db_batch_size = int(kwargs.get('DB_BATCH_OVERRIDE', self.db_batch_size or 10000))
        self.aws_deployment = str(kwargs.get('AWS_DEPLOYMENT', self.aws_deployment)).lower() == 'true'

    def _init_from_env(self):
        """
        Initializes configuration values from environment variables.
        """
        self.aws_profile = os.getenv('AWS_PROFILE', self.aws_profile)
        self.region_name = os.getenv('REGION_NAME', self.region_name)
        self.secret_arn = os.getenv('SECRET_ARN', self.secret_arn)
        self.openai_api_key = os.getenv('OPENAI_API_KEY', self.openai_api_key)
        self.ssh_server = os.getenv('SSH_SERVER', self.ssh_server)
        self.ssh_port = int(os.getenv('SSH_PORT', self.ssh_port or 22))
        self.ssh_user = os.getenv('SSH_USER', self.ssh_user)
        self.ssh_password = os.getenv('SSH_PASSWORD', self.ssh_password)
        self.pem_path = os.getenv('PEM_PATH', self.pem_path)
        self.db_batch_size = int(os.getenv('DB_BATCH_OVERRIDE', self.db_batch_size or 10000))
        self.aws_deployment = str(os.getenv('AWS_DEPLOYMENT', None)).lower() == 'true'

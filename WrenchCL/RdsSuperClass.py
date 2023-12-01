import io
import os
import time
import json

import paramiko
import psycopg2
from sshtunnel import SSHTunnelForwarder
from WrenchCL.WrenchLogger import wrench_logger
from decimal import Decimal
import datetime
import pandas as pd


class SshTunnelManager:
    def __init__(self, config):
        self.config = config
        self.ssh_config = config['SSH_TUNNEL']
        self.tunnel = None

    def start_tunnel(self):
        wrench_logger.setLevel("warning")
        self.tunnel = SSHTunnelForwarder(
            ssh_address_or_host=(self.ssh_config['SSH_SERVER'], self.ssh_config['SSH_PORT']),
            ssh_username=self.ssh_config['SSH_USER'],
            ssh_password=self.ssh_config.get('SSH_PASSWORD', None),
            ssh_pkey=paramiko.RSAKey(file_obj=io.StringIO(os.environ['RSA_KEY'])) if self.ssh_config.get('USE_RSA_ENV',
                                                                                                         False) else self.ssh_config.get(
                'SSH_KEY_PATH', None),
            remote_bind_address=(self.config['PGHOST'], self.config['PGPORT'])
        )
        wrench_logger.revertLoggingLevel()
        self.tunnel.start()
        return '127.0.0.1', self.tunnel.local_bind_port

    def stop_tunnel(self):
        if self.tunnel:
            self.tunnel.stop()


class RDS:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RDS, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.config = None
        self.connection = None
        self.ssh_manager = None
        self.result = None  # Initialize the result variable
        self.column_names = None  # Initialize column names variable
        self.method = 'fetchall'  # Default method

    def load_configuration(self, db_config):
        self.config = db_config
        wrench_logger.debug(f"Config Loaded successfully")

    def _connect(self):
        host, port = self.config['PGHOST'], self.config['PGPORT']

        if 'SSH_TUNNEL' in self.config:
            self.ssh_manager = SshTunnelManager(self.config)
            host, port = self.ssh_manager.start_tunnel()
            wrench_logger.debug("SSH Tunnel Connected")
        wrench_logger.debug(f"Connecting to DB with {host}.{port} ")

        wrench_logger.setLevel("Warning")
        self.connection = psycopg2.connect(
            host=host,
            port=port,
            database=self.config['PGDATABASE'],
            user=self.config['PGUSER'],
            password=self.config['PGPASSWORD']
        )
        wrench_logger.revertLoggingLevel()

    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Handle any exceptions if you need
        if self.connection:
            self.connection.close()
            wrench_logger.debug("Database connection closed automatically via __exit__.")

        if self.ssh_manager:
            self.ssh_manager.stop_tunnel()
            wrench_logger.debug("SSH tunnel closed automatically via __exit__.")

    def batch_add_query(self, query, parameters=None):
        cursor = self.connection.cursor()
        if parameters is None:
            cursor.execute(query)
        else:
            cursor.execute(query, parameters)

    def batch_execute_query(self):
        start_time = time.time()
        try:
            self.connection.commit()
            minutes, seconds = divmod(time.time() - start_time, 60)
            wrench_logger.info(f"Query executed successfully, Query execution time: {int(minutes):02}:{seconds:05.2f}")
        except Exception as e:
            wrench_logger.error(f"Failed to execute query: {e}")
            return 'ERROR'

    def execute_query(self, query, output='raw', method='fetchall', parameters=None):
        if not self.connection:
            wrench_logger.error("Database connection is not established. Cannot execute query.")
            return None

        cursor = self.connection.cursor()

        try:
            start_time = time.time()
            if parameters is None:
                cursor.execute(query)
            else:
                cursor.execute(query, parameters)
            self.connection.commit()
            minutes, seconds = divmod(time.time() - start_time, 60)
            wrench_logger.info(
                f"Query executed successfully, Query execution time: {int(minutes):02}:{seconds:05.2f}")
            result = None

            wrench_logger.debug(f"SQL Pull Description: {cursor.description}")
            if cursor.description:
                self.column_names = [desc[0] for desc in cursor.description]
                if method.lower() == 'fetchall':
                    self.result = cursor.fetchall()
                    wrench_logger.debug(f"FetchedAll result length = {len(self.result)}")
                elif method.lower() == 'fetchone':
                    self.result = cursor.fetchone()
                    wrench_logger.debug(f"FetchedOne result = {self.result}")
                else:
                    wrench_logger.error("Invalid method; please use either 'fetchone' or 'fetchall'")
            else:
                self.result = None

            if output.lower() == "json":
                return self.parse_to_json()
            elif output.lower() in ['df', 'dataframe']:
                return self.parse_to_dataframe()
            elif output.lower() == 'raw':
                return self.result
            else:
                wrench_logger.error('Please provide valid input for output argument [json, df, dataframe, raw]')
                raise ValueError('Please provide valid input for output argument [json, df, dataframe, raw]')

        except Exception as e:
            wrench_logger.error(f"Failed to execute query: {e}")
            return 'ERROR'

    def parse_to_json(self):
        if self.result is None:
            wrench_logger.warning("Result is None, cannot parse to JSON.")
            return None
        try:
            json_result = json.dumps(self.result, default=self._handle_special_types)
            wrench_logger.debug("Result parsed to JSON successfully.")
            return json_result
        except Exception as e:
            wrench_logger.error("Failed to parse result to JSON: {}".format(e))
            return None

    def parse_to_dataframe(self):
        if self.result is None:
            wrench_logger.warning("Result is None, cannot parse to DataFrame.")
            return None
        try:
            if self.method == 'fetchall':
                pass
            elif self.method == 'fetchone':
                self.result = [self.result]

            if self.column_names is not None:
                dataframe_result = pd.DataFrame(self.result, columns=self.column_names)
            else:
                dataframe_result = pd.DataFrame(self.result)
            wrench_logger.debug("JSON parsed to DataFrame successfully.")
            return dataframe_result
        except Exception as e:
            wrench_logger.error("Failed to parse JSON to DataFrame: {}".format(e))
            return None

    def close(self):
        """
        Manually close the database connection and SSH tunnel (if established).
        """
        self.__exit__(None, None, None)
        wrench_logger.debug("Database connection and SSH tunnel (if established) closed manually via close().")

    @staticmethod
    def _handle_special_types(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        raise TypeError("Type not serializable")


rdsInstance = RDS()

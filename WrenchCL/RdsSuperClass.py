import json
import os
import pathlib
import time
from datetime import datetime
import pandas as pd
import psycopg2
from _decimal import Decimal
from dotenv import load_dotenv
from WrenchCL.WrenchLogger import wrench_logger


class _RdsSuperClass:
    """
    Superclass for Managing PostgreSQL Database Operations with Secrets Management.

    This class provides a convenient way to connect to a PostgreSQL database, execute queries, and parse results. It also manages secrets for database connection parameters by reading from an environment file.

    How to Use:
    -----------
    1. Import the instantiated object:
        ```python
        from your_module import rdsInstance
        ```

    2. Connect to the database:
        ```python
        rdsInstance.connect()
        ```

    3. Execute a query:
        ```python
        result = rdsInstance.execute_query("SELECT * FROM table", output='json', method='fetchall')
        ```

    4. Parse result to JSON or DataFrame:
        ```python
        json_result = rdsInstance.parse_to_json()
        df_result = rdsInstance.parse_to_dataframe()
        ```

    5. Close the database connection:
        ```python
        rdsInstance.close()
        ```

    Attributes:
    -----------
    - connection (psycopg2.connection): The database connection object.
    - result (Any): The result of the last executed query.
    - column_names (List[str]): Column names of the last query result.
    - secrets_input (str): Relative path to the secrets file.
    - secrets_path (str): Absolute path to the secrets file.
    - method (str): The fetch method used in the last query ('fetchall' or 'fetchone').

    Methods:
    --------
    Refer to the class definition for detailed information on each method.

    Note: This class is obfuscated and instantiated upon import, so you should only import the instantiated object, `rdsInstance`.

    """

    def __init__(self, secrets_path='../resources/secrets/Secrets.env'):
        # root_folder = os.path.abspath(os.path.join(os.getcwd(), '..'))
        root_folder = os.getcwd()
        self.connection = None
        self.result = None
        self.column_names = None
        self.secrets_input = secrets_path
        self.secrets_path = os.path.abspath(os.path.join(root_folder, self.secrets_input))
        self.method = None
        self.initialized = False
        try:
            self.load_configuration()
            self.initialized = True
        except Exception as e:
            wrench_logger.debug("Initialization of RDS instance failed")
            pass

    def load_configuration(self, secret_loc=None):
        if secret_loc is not None:
            self.secrets_path = os.path.abspath(os.path.join(os.getcwd(), secret_loc))

        # Add to readme how to overwrite secrets, so we can handle them where needed
        if 'PGPASSWORD' in locals() and 'PGHOST' in locals() and 'PGDATABASE' in locals() \
                and 'PGUSER' in locals() and 'PGPASSWORD' in locals():
            wrench_logger.debug('Found secrets in environment')
            self._host = PGHOST
            self._port = PGPORT
            self._database = PGDATABASE
            self._user = PGUSER
            self._password = PGPASSWORD
        else:
            if os.getenv('PGHOST') is None or os.getenv('PGPORT') is None or os.getenv('PGDATABASE') \
                    is None or os.getenv('PGUSER') is None or os.getenv('PGPASSWORD') is None:
                self._secrets_finder()
                load_dotenv(self.secrets_path)
            else:
                wrench_logger.debug(f'Found environment variables')
            self._host = os.getenv('PGHOST')
            self._port = os.getenv('PGPORT')
            self._database = os.getenv('PGDATABASE')
            self._user = os.getenv('PGUSER')
            self._password = os.getenv('PGPASSWORD')

    def _secrets_finder(self):
        parent_count = 0
        while True:
            time.sleep(0.05)
            try:
                if parent_count > 5:
                    raise ValueError('Maximum parent count reached.')
                wrench_logger.debug(f'Trying Secrets Path: {self.secrets_path}')
                if pathlib.Path(self.secrets_path).is_file():
                    wrench_logger.info(f"Found Secrets file at {self.secrets_path}")
                    break  # Exit loop if file exists
                else:
                    wrench_logger.debug(f'File not found: {self.secrets_path}. Trying parent directory...')
                    root_folder = pathlib.Path.cwd()
                    for _ in range(parent_count):
                        root_folder = root_folder.parent
                    self.secrets_path = os.path.join(root_folder, self.secrets_input)
                    parent_count += 1
            except ValueError as ve:
                wrench_logger.error(f'No suitable secret path found after 5 iterations. Check your secrets path.')
                raise ve
            except Exception as e:
                wrench_logger.error(f'An unexpected error occurred while loading secrets | {e}')
                raise e

    def connect(self):
        if not self.initialized:
            wrench_logger.error('RDS Class is not initialized please run the load_configuration() method')
            raise NotImplementedError

        try:
            self.connection = psycopg2.connect(
                host=self._host,
                port=self._port,
                database=self._database,
                user=self._user,
                password=self._password
            )
            wrench_logger.debug(
                "Database connection established successfully with host {}.".format(self._host))
        except Exception as e:
            wrench_logger.error("Failed to establish database connection: {}".format(e))
            self.connection = None

    def execute_query(self, query, output=None, method='fetchall'):
        if self.connection is None:
            wrench_logger.error("Database connection is not established. Cannot execute query.")
            return None

        cursor = self.connection.cursor()
        try:
            start_time = time.time()
            cursor.execute(query)
            self.connection.commit()
            minutes, seconds = divmod(time.time() - start_time, 60)
            wrench_logger.info(
                "Query executed successfully, Query execution time: {:0>2}:{:05.2f}".format(int(minutes), seconds))
            if cursor.description:
                if method.lower() == 'fetchall':
                    self.result = cursor.fetchall()
                    self.method = 'fetchall'
                elif method.lower() == 'fetchone':
                    self.result = cursor.fetchone()
                    self.method = 'fetchone'
                else:
                    wrench_logger.error("Invalid method please use either FetchOne or FetchAll")
                try:
                    self.column_names = [desc[0] for desc in cursor.description]
                except:
                    pass
            else:
                self.result = None
        except Exception as e:
            wrench_logger.error("Failed to execute query: {}".format(e))
            self.result = 'ERROR'

        if output is not None:
            if output.lower() == "json":
                return self.parse_to_json()
            elif output.lower() == 'df' or output.lower() == 'dataframe':
                return self.parse_to_dataframe()
            else:
                return self.result
        else:
            return self.result

    def parse_to_json(self):
        print(self.result)
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
        if self.connection:
            self.connection.close()
            wrench_logger.debug("Database connection closed successfully.")

    @staticmethod
    def _handle_special_types(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        raise TypeError("Type not serializable")


rdsInstance = _RdsSuperClass()

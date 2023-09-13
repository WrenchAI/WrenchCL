import json
import os
import pathlib
import time
from datetime import datetime
import pandas as pd
import psycopg2
from _decimal import Decimal
from WrenchCL.WrenchLogger import wrench_logger


class _RdsSuperClass:
    def __init__(self):
        # root_folder = os.path.abspath(os.path.join(os.getcwd(), '..'))
        self._host = None
        self._port = None
        self._database = None
        self._user = None
        self._password = None
        root_folder = os.getcwd()
        self.connection = None
        self.result = None
        self.column_names = None
        self.method = None
        self.initialized = False

    def load_configuration(self, PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD):
        self._host = PGHOST
        self._port = PGPORT
        self._database = PGDATABASE
        self._user = PGUSER
        self._password = PGPASSWORD
        self.initialized = True

    def connect(self, PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD):
        if not self.initialized:
            try:
                self.load_configuration(PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD)
            except:
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

import json
import os
import time
from datetime import datetime

import pandas as pd
import psycopg2
from _decimal import Decimal
from dotenv import load_dotenv


class RDSHandler:
    def __init__(self, log_writer, secrets_path):
        self.connection = None
        self.log_writer = log_writer
        self.result = None
        self.column_names = None
        self.secrets_path = secrets_path
        self.method = None
        self._load_configuration()

    def _load_configuration(self):
        load_dotenv(self.secrets_path)
        self._host = os.getenv('PGHOST')
        self._port = os.getenv('PGPORT')
        self._database = os.getenv('PGDATABASE')
        self._user = os.getenv('PGUSER')
        self._password = os.getenv('PGPASSWORD')

    def connect(self):

        try:
            self.connection = psycopg2.connect(
                host=self._host,
                port=self._port,
                database=self._database,
                user=self._user,
                password=self._password
            )
            self.log_writer.debug(
                "Database connection established successfully with host {}.".format(self._host))
        except Exception as e:
            self.log_writer.error("Failed to establish database connection: {}".format(e))
            self.connection = None

    def execute_query(self, query, output=None, method = 'fetchall'):
        if self.connection is None:
            self.log_writer.warning("Database connection is not established. Cannot execute query.")
            return None

        cursor = self.connection.cursor()
        try:
            start_time = time.time()
            cursor.execute(query)
            self.connection.commit()
            minutes, seconds = divmod(time.time() - start_time, 60)
            self.log_writer.info(
                "Query executed successfully, Query execution time: {:0>2}:{:05.2f}".format(int(minutes), seconds))
            if cursor.description:
                if method.lower() == 'fetchall':
                    self.result = cursor.fetchall()
                    self.method = 'fetchall'
                elif method.lower() == 'fetchone':
                    self.result = cursor.fetchone()
                    self.method = 'fetchone'
                else:
                    self.log_writer.error("Invalid method please use either FetchOne or FetchAll")
                try:
                    self.column_names = [desc[0] for desc in cursor.description]
                except:
                    pass
            else:
                self.result = None
        except Exception as e:
            self.log_writer.error("Failed to execute query: {}".format(e))
            self.result = None

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
            self.log_writer.warning("Result is None, cannot parse to JSON.")
            return None
        try:
            json_result = json.dumps(self.result, default=self._handle_special_types)
            self.log_writer.debug("Result parsed to JSON successfully.")
            return json_result
        except Exception as e:
            self.log_writer.error("Failed to parse result to JSON: {}".format(e))
            return None

    def parse_to_dataframe(self):
        if self.result is None:
            self.log_writer.warning("Result is None, cannot parse to DataFrame.")
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
            self.log_writer.debug("JSON parsed to DataFrame successfully.")
            return dataframe_result
        except Exception as e:
            self.log_writer.error("Failed to parse JSON to DataFrame: {}".format(e))
            return None

    def close(self):
        if self.connection:
            self.connection.close()
            self.log_writer.debug("Database connection closed successfully.")

    @staticmethod
    def _handle_special_types(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        raise TypeError("Type not serializable")


class queryStorage:

    def __init__(self, deal_id):
        self.deal_id = deal_id

    def get_chatgpt_query(self, query_text):
        query = f"""
        Can you give me a python dictionary summarizing the given text 
        The python dictionary should contain:
        id: A String containing {self.deal_id}
        Keywords: FIVE keywords summarizing the technology in the text 
        Concepts: THREE concept phrases to use as search queries summarizing the technology in the text
        Summary: A tech summary of the text in 300 words
        Make sure to wrap strings in double-quotes
        The text follows: 
        {query_text}
        """
        return query

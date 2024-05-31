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
import math
from typing import Optional, Any, Union, List, Dict

import psycopg2
import psycopg2.extras
import psycopg2.extensions

from .AwsClientHub import AwsClientHub
from ..Decorators.SingletonClass import SingletonClass
from ..Tools.WrenchLogger import logger

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


@SingletonClass
class RdsServiceGateway:
    """
    Provides methods to interact with an RDS database, including querying data and updating the database. Ensures
    that a single instance is used throughout the application via the Singleton pattern.

    Attributes:
        connection (psycopg2.extensions.connection): The database connection object.
        config (ConfigurationManager): The configuration manager for managing configuration settings.
    """
    psycopg2.extras.register_uuid()

    def __init__(self):
        """
        Initializes the RdsServiceGateway by establishing a connection to the database using the AwsClientHub.
        """
        client_manager = AwsClientHub()
        self.connection = client_manager.get_db_client()
        self.config = client_manager.get_config()

    def get_data(self, query: str, payload: Optional[tuple] = None, fetchall: bool = True, return_dict: bool = True) -> Optional[Any]:
        """
        Fetch data from the database based on the input query and parameters.

        :param query: SQL query to execute.
        :type query: str
        :param payload: Parameters to substitute into the query.
        :type payload: tuple, optional
        :param fetchall: Whether to fetch all rows or just one.
        :type fetchall: bool, optional
        :param return_dict: Whether to return a dictionary or raw dict cursor response.
        :type return_dict: bool, optional
        :returns: The fetched data or None if an error occurs.
                 - If `fetchall` is True and `return_dict` is True, returns a list of dictionaries.
                 - If `fetchall` is True and `return_dict` is False, returns a list of raw rows.
                 - If `fetchall` is False and `return_dict` is True, returns a single dictionary.
                 - If `fetchall` is False and `return_dict` is False, returns a single raw row.
        :rtype: Optional[Any]

        **Example**::

            >>> rds_client = RdsServiceGateway()
            >>> client_id = '123'
            >>> image_hash = '123'
            >>> rds_client.get_data(
            >>>     '''
            >>>     SELECT * FROM
            >>>     vecstore.doc_store WHERE
            >>>     client_id = %s AND sha1_hash = %s
            >>>     ''', (client_id, image_hash),
            >>>     fetchall=False, return_dict=False)
        """
        logger.debug("Executing query: %s", query)
        logger.debug("With payload: %s", payload)

        try:
            with self.connection as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute(query, payload)
                    data = cursor.fetchall() if fetchall else cursor.fetchone()
                    logger.debug("Fetched data: %s", str(data)[:100] if fetchall else str(data))
                    cursor.close()

            if return_dict and data is not None:
                return [dict(row) for row in data] if fetchall else dict(data)
            elif data is None:
                raise ValueError("None returned")
            else:
                return data
        except Exception as e:
            logger.error(f"Error executing query: {e}", stack_info=True)
            return None

    def update_database(self, query: str, payload: Union[tuple, 'pd.DataFrame'], returning: bool = False, column_order: Optional[List[str]] = None) -> Optional[List[tuple]]:
        """
        Updates the database by executing the given query with the provided payload.

        :param query: SQL query to execute.
        :type query: str
        :param payload: Data to use in the query. Can be a tuple for single operations or a DataFrame for batch operations.
        :type payload: Union[tuple, pd.DataFrame]
        :param returning: Flag to be able to return a postgres returning update statement
        :type returning: bool
        :param column_order: The order of columns to be used if the payload is a DataFrame.
        :type column_order: List[str], optional
        :returns: A list of tuples if returning is true else None
        :rtype: Optional[List[tuple]]
        """
        with self.connection as conn:
            if isinstance(payload, tuple):
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(query, payload)
                        return_value = cursor.fetchall() if returning else None
                        conn.commit()
                        return return_value
                except Exception as e:
                    logger.error(f"Error inserting data: {str(e)}")
                    conn.rollback()
            elif PANDAS_AVAILABLE and isinstance(payload, pd.DataFrame) and column_order:
                if returning:
                    logger.error("Returning values not compatible with batch processing, please use dictionary input")
                    raise ValueError("Returning values not compatible with batch processing, please use dictionary input")
                try:
                    with conn.cursor() as cursor:
                        data_batch = []
                        batch_counter = 1
                        total_batches = math.ceil(len(payload) / self.config.db_batch_size)
                        for index, row in payload.iterrows():
                            data_batch.append(tuple(row[col] for col in column_order))

                            if len(data_batch) == self.config.db_batch_size or index == len(payload) - 1:
                                psycopg2.extras.execute_values(cursor, query, data_batch, page_size=self.config.db_batch_size)
                                data_batch = []
                                logger.debug(f"Processed batch {batch_counter}/{total_batches} successfully")
                                batch_counter += 1

                        conn.commit()
                except Exception as e:
                    logger.error(f"Error processing batch: {str(e)}")
                    conn.rollback()
            else:
                logger.error("Invalid payload type or missing column_order for DataFrame payload.")

    def format_sql_query(self, query: str, payload: tuple) -> None:
        """
        Formats and prints the SQL query with the given payload.

        :param query: The SQL query to format.
        :type query: str
        :param payload: The parameters to substitute into the query.
        :type payload: tuple

        **Example**::

            >>> rds_client = RdsServiceGateway()
            >>> query = "SELECT * FROM users WHERE id = %s AND name = %s"
            >>> payload = (1, 'John')
            >>> rds_client.format_sql_query(query, payload)
        """
        formatted_query = query % tuple(map(lambda x: f"'{x}'" if isinstance(x, str) else x, payload))
        print(formatted_query)

    def get_cursor(self) -> psycopg2.extensions.cursor:
        """
        Returns a new database cursor.

        :returns: A new cursor object.
        :rtype: psycopg2.extensions.cursor

        **Example**::

            >>> rds_client = RdsServiceGateway()
            >>> cursor = rds_client.get_cursor()
            >>> cursor.execute("SELECT * FROM users")
            >>> data = cursor.fetchall()
            >>> print(data)
        """
        return self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def get_connection(self) -> psycopg2.extensions.connection:
        """
        Returns the current database connection.

        :returns: The database connection object.
        :rtype: psycopg2.extensions.connection

        **Example**::

            >>> rds_client = RdsServiceGateway()
            >>> conn = rds_client.get_connection()
            >>> with conn.cursor() as cursor:
            >>>     cursor.execute("SELECT * FROM users")
            >>>     data = cursor.fetchall()
            >>>     print(data)
        """
        return self.connection

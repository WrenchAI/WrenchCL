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
import collections
import math
from typing import Optional, Type, Any, Union, List, Tuple

import psycopg2
import psycopg2.extras

from .AwsClientHub import AwsClientHub
from ..Decorators.SingletonClass import SingletonClass
from ..Tools.Coalesce import coalesce
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

    def __init__(self):
        """
        Initializes the RdsServiceGateway by establishing a connection to the database using the AwsClientHub.
        """
        client_manager = AwsClientHub()
        self.connection = client_manager.get_db_client()
        self.config = client_manager.get_config()

    def get_data(self, query: str, payload: Optional[tuple] = None, fetchall: bool = True,
                 return_dict: bool = True,  accepted_type: Optional[Type] = None, none_is_ok: bool = False,
                 accepted_length: Tuple[Optional[int], Optional[int]] = (None, None)) -> Optional[Any]:
        """
        Fetch data from the database based on the input query and parameters.

        :param query: SQL query to execute.
        :type query: str
        :param payload: Parameters to substitute into the query.
        :type payload: dict, optional
        :param fetchall: Whether to fetch all rows or just one.
        :type fetchall: bool, optional
        :param return_dict: Whether to return a dictionary or raw dict cursor response
        :type return_dict: bool, optional
        :param accepted_type: Expected type of the fetched data.
        :type accepted_type: Type, optional
        :param none_is_ok: If True, None can be a valid return type if no data is found.
        :type none_is_ok: bool, optional
        :param accepted_length: A tuple of the minimum and maximum allowed lengths of the data.
        :type accepted_length: Tuple[Optional[int], Optional[int]], optional
        :returns: The fetched data or None if validations fail.
        :rtype: Optional[Any]
        """
        logger.debug("Executing query: ", query)
        logger.debug("With payload: ", payload)

        try:
            with self.connection as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute(query, payload)
                    data = cursor.fetchall() if fetchall else cursor.fetchone()
                    logger.debug("Fetched data: ", str(data)[:100])
                    cursor.close()

            if accepted_type:
                logger.debug("Validating output with type: %s", accepted_type)
                if self._validate_output(data, accepted_type, none_is_ok, accepted_length):
                    logger.debug("Output validated successfully")
                    if return_dict:
                        return [dict(row) for row in data] if fetchall else dict(data)
                    else:
                        return data

                else:
                    logger.debug("Output validation failed")
                    return None
            else:
                if return_dict:
                    return [dict(row) for row in data] if fetchall else dict(data)
                else:
                    return data
        except Exception as e:
            logger.error("Error executing query: ", e)
            return None

    def update_database(self, query: str, payload: Union[dict, 'pd.DataFrame'],
                        column_order: Optional[List[str]] = None) -> None:
        """
        Updates the database by executing the given query with the provided payload.

        :param query: SQL query to execute.
        :type query: str
        :param payload: Data to use in the query. Can be a dictionary for single operations or a DataFrame for batch operations.
        :type payload: Union[dict, pd.DataFrame]
        :param column_order: The order of columns to be used if the payload is a DataFrame.
        :type column_order: List[str], optional
        :returns: None
        """
        with self.connection as conn:
            if isinstance(payload, dict):
                try:
                    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                        cursor.execute(query, payload)
                        conn.commit()
                except Exception as e:
                    logger.error(f"Error inserting data: {str(e)}")
                    conn.rollback()
            elif PANDAS_AVAILABLE and isinstance(payload, pd.DataFrame) and column_order:
                try:
                    with conn.cursor() as cursor:
                        data_batch = []
                        batch_counter = 1
                        total_batches = math.ceil(len(payload) / self.config.db_batch_size)
                        for index, row in payload.iterrows():
                            data_batch.append(tuple(row[col] for col in column_order))

                            if len(data_batch) == self.config.db_batch_size or index == len(payload) - 1:
                                psycopg2.extras.execute_values(cursor, query, data_batch,
                                                               page_size=self.config.db_batch_size)
                                data_batch = []
                                logger.debug(f"Processed batch {batch_counter}/{total_batches} successfully")
                                batch_counter += 1

                        conn.commit()
                except Exception as e:
                    logger.error(f"Error processing batch: {str(e)}")
                    conn.rollback()
            else:
                logger.error("Invalid payload type or missing column_order for DataFrame payload.")

    @staticmethod
    def _validate_output(data: Any, accepted_type: Type, none_is_ok: bool = False,
                         accepted_length: Tuple[Optional[int], Optional[int]] = (None, None)) -> bool:
        """
        Validates the output data against the specified type and length constraints.

        :param data: The data to validate.
        :type data: Any
        :param accepted_type: The type the data is expected to conform to.
        :type accepted_type: Type
        :param none_is_ok: Allows None as a valid value of data.
        :type none_is_ok: bool, optional
        :param accepted_length: A tuple specifying the minimum and maximum length of the data.
        :type accepted_length: Tuple[Optional[int], Optional[int]], optional
        :returns: True if the data is valid, False otherwise.
        :rtype: bool
        """
        if none_is_ok and data is None:
            return True

        if not isinstance(data, accepted_type):
            logger.error(f"Data type check failed: {type(data).__name__} is not {accepted_type.__name__}")
            return False

        if isinstance(data, collections.abc.Sized):
            min_length = coalesce(accepted_length[0], 0)
            max_length = coalesce(accepted_length[1], math.inf)
            data_length = len(data)
            if not (min_length <= data_length <= max_length):
                logger.error(
                    f"Length check failed: {data_length} is not within the allowed range ({min_length}, {max_length})")
                return False

        return True

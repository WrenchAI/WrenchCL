#  Copyright (c) 2024-2025.
#  Author: Willem van der Schans.
#  Licensed under the MIT License (https://opensource.org/license/mit).
import json
import math
from datetime import datetime, timedelta
from typing import Optional, Any, Union, List, Tuple
from uuid import UUID

from WrenchCL._Internal.require_module import gate_imports

try:
    import psycopg2
    import psycopg2.extensions
    import psycopg2.extras
    from mypy_boto3_rds.client import RDSClient
    from psycopg2.pool import ThreadedConnectionPool
    imports = True
except ImportError:
    psycopg2 = None
    RDSClient = None
    ThreadedConnectionPool = None
    imports = False

from .AwsClientHub import AwsClientHub
from WrenchCL.Decorators.SingletonClass import SingletonClass
from WrenchCL.Tools.ccLogBase import logger

from WrenchCL._Internal._MockPandas import _MockPandas

try:
    import pandas as pd
except ImportError:
    pd = _MockPandas()
DataFrame = pd.DataFrame

@SingletonClass
class RdsServiceGateway:
    """
    Provides methods to interact with an RDS database, including querying data and updating the database.
    Ensures that a single instance is used throughout the application via the Singleton pattern.
    """



    def __init__(self, multithreaded: bool = False, min_pool_size: int = 1, max_pool_size: int = 10):
        """
        Initializes the RdsServiceGateway by establishing a connection or connection pool
        depending on the multithreading mode.

        :param multithreaded: Whether to use connection pooling for multithreading.
        :type multithreaded: bool
        :param min_pool_size: Minimum number of connections in the pool (only if multithreaded is True).
        :type min_pool_size: int
        :param max_pool_size: Maximum number of connections in the pool (only if multithreaded is True).
        :type max_pool_size: int
        """
        gate_imports(imports, 'aws', ['psycopg2'])
        psycopg2.extras.register_uuid()
        self.multithreaded = multithreaded
        self.test_mode = False
        self.client_manager = AwsClientHub()
        self.config = self.client_manager.config
        self.db_uri = self.client_manager.db_uri

        if self.multithreaded:
            # Initialize a threaded connection pool using the URI
            self.pool: Optional[psycopg2.pool] = ThreadedConnectionPool(minconn=min_pool_size, maxconn=max_pool_size, dsn=self.db_uri)
        else:
            # Establish a single connection if multithreading is not enabled
            self.connection: Optional["RDSClient"] = self.client_manager.db

    def set_test_mode(self, test_mode: bool = False):
        logger.warning("Test mode activated, database commits will not be commited.")
        self.test_mode = test_mode

    def get_connection(self) -> Union["psycopg2.extensions.connection", "RDSClient"]:
        """
        Retrieves a connection from the connection pool or direct connection based on initialization mode.

        :returns: A database connection object.
        :rtype: psycopg2.extensions.connection
        """
        if self.multithreaded:
            return self.pool.getconn()
        return self.connection

    def release_connection(self, conn: "psycopg2.extensions.connection"):
        """
        Releases a connection back to the pool if multithreaded, otherwise does nothing.

        :param conn: The database connection to release.
        :type conn: psycopg2.extensions.connection
        """
        if self.multithreaded:
            self.pool.putconn(conn)

    def get_data(self, query: str, payload: Optional[tuple] = None, fetchall: bool = True, return_dict: bool = True,
            show_query: bool = False, raise_on_error: bool = False) -> Optional[Any]:
        """
        Fetch data from the database based on the input query and parameters.
        """
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                if show_query:
                    logger.debug("Mogrified Query:\n", cursor.mogrify(query, payload))
                else:
                    logger.debug("Mogrified Query:\n", cursor.mogrify(query, payload))
                cursor.execute(query, payload)
                data = cursor.fetchall() if fetchall else cursor.fetchone()
                logger.debug("Fetched data\n: %s", str(data)[:100] if fetchall else str(data))
            if return_dict and data is not None:
                return [dict(row) for row in data] if fetchall else dict(data)
            elif data is None:
                raise ValueError("None returned")
            else:
                return data
        except Exception as e:
            conn.rollback()
            if raise_on_error:
                logger.warning(f"Error executing query: {e}")
                raise e
            else:
                logger.debug(f"Query returned None: {e}")
                return None
        finally:
            self.release_connection(conn)

    def update_database(self, query: str, payload: Union[tuple, list[tuple], pd.DataFrame], returning: bool = False,
                        column_order: Optional[List[str]] = None, raise_on_error: bool = True, test_mode: bool = False) -> Optional[List[tuple]]:
        """
        Updates the database by executing the specified SQL query with the given payload.

        Handles different payload formats including a single tuple, a list of tuples, or a DataFrame. Supports optional
        fetching of return values if `returning` is True. Commits the transaction by default unless in test mode, where
        changes are rolled back.

        Args:
            query (str): SQL query to execute.
            payload (Union[tuple, list[tuple], DataFrame]): Data to be used in the query. Can be a single tuple, a list of tuples,
                or a DataFrame.
            returning (bool): If True, fetches and returns results after executing the query.
            column_order (Optional[List[str]]): Order of columns when payload is a DataFrame. Ensures correct insertion order.
            raise_on_error (bool): If True, raises exceptions on errors; if False, logs errors without raising.
            test_mode (bool): If True, rolls back the transaction instead of committing changes to the database.

        Returns:
            Optional[List[tuple]]: List of tuples containing the query results if `returning` is True, otherwise None.

        Raises:
            ValueError: If column order is missing for DataFrame payloads or if the payload has incompatible data for batch processing.
            psycopg2.DataError: If no data was committed in batch processing.
        """
        conn = self.get_connection()

        if self.test_mode:
            test_mode = True

        if test_mode:
            logger.warning("Running RDSServiceGateway in test mode.")

        try:
            # Convert payload into a tuple if it's a single value or list
            payload = self.convert_payload(payload)
            logger.debug(f"Converted payload: {payload}")

            if isinstance(payload, tuple):
                logger.debug("Payload is a single tuple.")
                # Execute query for single tuple payload
                with conn.cursor() as cursor:
                    cursor.execute(query, payload)
                    return_value = cursor.fetchall() if returning else None
                    if not test_mode:
                        conn.commit()
                        logger.debug("Transaction committed successfully.")
                    else:
                        conn.rollback()
                        logger.debug("Transaction rolled back in test mode.")
                    return return_value

            elif isinstance(payload, list) and all(isinstance(item, tuple) for item in payload):
                logger.debug("Payload is a list of tuples.")
                # Execute batch query for list of tuples payload
                with conn.cursor() as cursor:
                    psycopg2.extras.execute_values(cursor, query, payload, page_size=self.config.db_batch_size)
                    return_value = cursor.fetchall() if returning else None
                    if not test_mode:
                        conn.commit()
                        logger.debug("Transaction committed successfully.")
                    else:
                        conn.rollback()
                        logger.debug("Transaction rolled back in test mode.")
                    return return_value

            elif isinstance(payload, pd.DataFrame) and column_order:
                logger.debug("Payload is a DataFrame with specified column order.")
                # Batch processing for DataFrame payloads with specified column order
                if returning:
                    raise ValueError("Returning values not compatible with batch processing, please use dictionary input")
                if not set(column_order).issubset(payload.columns):
                    missing_columns = set(column_order) - set(payload.columns)
                    raise ValueError(f"The following columns are missing from the payload: {missing_columns}")

                with conn.cursor() as cursor:
                    data_batch = []
                    batch_counter = 1
                    total_batches = math.ceil(len(payload) / self.config.db_batch_size)

                    for i, row in enumerate(payload.itertuples(index=False, name='Row')):
                        data_batch.append(tuple(getattr(row, col) for col in column_order))

                        if len(data_batch) == self.config.db_batch_size or i == len(payload) - 1:
                            psycopg2.extras.execute_values(cursor, query, data_batch, page_size=self.config.db_batch_size)
                            data_batch = []
                            logger.debug(f"Processed batch {batch_counter}/{total_batches} successfully")
                            batch_counter += 1

                    if batch_counter == 1:
                        raise psycopg2.DataError("Nothing to commit")

                    if not test_mode:
                        conn.commit()
                        logger.debug("Transaction committed successfully.")
                    else:
                        conn.rollback()
                        logger.debug("Transaction rolled back in test mode.")

        except Exception as e:
            conn.rollback()
            if isinstance(e, IndexError):
                try:
                    logger.warning(f"Error processing batch: IndexError | Got {query.count('%s')} placeholders and {len(payload)} values. {e}")
                except Exception as nested_exception:
                    logger.warning(f"Error processing batch: {str(e)}; Nested error: {str(nested_exception)}", exc_info=True)
            else:
                logger.warning(f"Error processing batch: {str(e)}", exc_info=True)
            if raise_on_error:
                raise e
        finally:
            self.release_connection(conn)

    def format_sql_query(self, query: str, payload: tuple) -> None:
        """
        Formats and prints the SQL query with the given payload.

        :param query: The SQL query to format.
        :type query: str
        :param payload: The parameters to substitute into the query.
        :type payload: tuple
        """
        formatted_query = query % tuple(map(lambda x: f"'{x}'" if isinstance(x, str) else x, payload))
        print(formatted_query)

    def get_cursor(self) -> "psycopg2.extensions.cursor":
        """
        Returns a new database cursor.

        :returns: A new cursor object.
        :rtype: psycopg2.extensions.cursor
        """
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        self.release_connection(conn)
        return cursor

    def convert_payload(self, payload: Tuple[Any, ...]) -> pd.DataFrame | tuple[Any, ...]:
        """
        Converts elements within a tuple payload to types compatible with psycopg2.

        :param payload: The payload tuple containing elements that may need conversion.
        :type payload: Tuple[Any, ...]
        :return: A tuple with converted values.
        :rtype: Tuple[Any, ...]
        """
        if isinstance(payload, DataFrame):
            return self._convert_dataframe_types(payload)
        else:
            return tuple(self._convert_value(val) for val in payload)

    @staticmethod
    def _convert_dataframe_types(df: pd.DataFrame) -> pd.DataFrame:
        """
        Converts DataFrame columns to types compatible with psycopg2.
        """
        for col in df.columns:
            if pd.api.types.is_object_dtype(df[col]):
                # Use json.dumps for objects like dicts or lists, otherwise cast to string
                df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                # Convert datetime types to Python datetime
                df[col] = df[col].apply(lambda x: x.to_pydatetime() if pd.notnull(x) else None)
            elif pd.api.types.is_timedelta64_dtype(df[col]):
                # Convert timedelta to seconds
                df[col] = df[col].apply(lambda x: x.total_seconds() if pd.notnull(x) else None)
        return df

    @staticmethod
    def _convert_value(value: Any) -> Any:
        """Converts individual values to types compatible with psycopg2."""
        if isinstance(value, (dict, list)):
            # Convert dicts and lists to JSON strings
            return json.dumps(value)
        elif isinstance(value, datetime):
            # Ensure datetime objects are timezone aware or naive appropriately
            return value if value.tzinfo else value.replace(tzinfo=None)
        elif isinstance(value, timedelta):
            # Convert timedelta to total seconds
            return value.total_seconds()
        elif isinstance(value, set):
            # Convert sets to lists and then to JSON strings
            return json.dumps(list(value))
        elif isinstance(value, UUID):
            # Convert UUIDs to strings
            return str(value)
        else:
            # Return value as-is for basic types like int, float, bool, and None
            return value

    # Aliases
    insert_data = update_database
    execute_insert_query = update_database

    fetch_data = get_data
    execute_fetch_query = get_data

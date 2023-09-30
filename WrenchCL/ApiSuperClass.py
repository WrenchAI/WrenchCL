import math
import time
import pandas as pd
import requests
from WrenchCL.WrenchLogger import wrench_logger


class MaxRetriesExceededError(Exception):
    pass


class ApiSuperClass:
    def __init__(self, base_url):
        self.base_url = base_url

    def _fetch_from_api(self, url, headers, payload):
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            wrench_logger.error(f'Failed to get data, status code: {response.status_code}')
            wrench_logger.error(f'Payload: {payload}')
            wrench_logger.error(f'Url: {response.url}')
            wrench_logger.error(f'Response text: {response.text}')
            return None

    def get_count(self):
        raise NotImplementedError("This method should be overridden by subclass")

    def fetch_data(self, batch_size, last_record_sort_value=None, last_record_unique_id=None, page=None):
        raise NotImplementedError("This method should be overridden by subclass")

    def batch_processor(self, batch_size=100, max_retries=5, incrementing=None):
        start_time = time.time()

        page_count = self.get_count()
        if page_count is None:
            wrench_logger.error("Couldn't get page count. Exiting batch processor.")
            return
        else:
            wrench_logger.debug(f'Query will retrieve {page_count} grant entries.')

        batch_count = math.ceil(page_count / batch_size)
        all_data = []

        last_record_sort_value = None
        last_record_unique_id = None
        page = 1
        has_next = True
        for batch in range(0, batch_count):
            if not has_next:
                page = page + 1
                last_record_sort_value = None
                last_record_unique_id = None
            retries = 0
            while retries < max_retries:
                try:
                    batch_start_time = time.time()
                    batch_out, last_record_sort_value, last_record_unique_id, has_next = self.fetch_data(
                        batch_size=batch_size,
                        last_record_sort_value=last_record_sort_value,
                        last_record_unique_id=last_record_unique_id,
                        page=page
                    )

                    if batch_out is not None:
                        all_data.extend(batch_out)
                    break  # Success, so exit the retry loop

                except ConnectionError as e:
                    wrench_logger.warning(
                        f'Connection Error: {e}. Retrying batch #{batch + 1}. | ({retries + 1}/{max_retries})')
                    time.sleep(1)
                    retries += 1
                except requests.exceptions.ConnectionError as e:
                    wrench_logger.warning(
                        f'Connection Error: {e}. Retrying batch #{batch + 1}. | ({retries + 1}/{max_retries})')
                    time.sleep(1)
                    retries += 1
                except Exception as e:
                    wrench_logger.error(f'An unexpected error occurred: {e}')

                finally:
                    if retries != max_retries:
                        batch_end_time = time.time()
                        total_time = batch_end_time - start_time
                        if batch != 0:
                            time_per_batch = total_time / batch
                        else:
                            time_per_batch = total_time / 1
                        eta = time_per_batch * (batch_count - batch)

                        wrench_logger.debug(
                            f'Current Batch: {batch + 1}/{batch_count}, Time per Batch: {time_per_batch:.2f}s, Batch ETA: {eta:.2f}s')
            else:
                # Does this make sense?
                wrench_logger.error(
                    f'MaxRetriesExceededError: Exceeded maximum retries of {max_retries}. Operation failed.')
                raise MaxRetriesExceededError(f'Exceeded maximum retries of {max_retries}. Operation failed.')

        end_time = time.time()
        total_run_time = end_time - start_time
        wrench_logger.debug(f'Total Run Time: {total_run_time:.2f}s')

        return pd.DataFrame(all_data)

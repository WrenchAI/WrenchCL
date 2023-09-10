import ast
import json
import os
import pathlib
import time

import openai
import requests
from dotenv import load_dotenv
from tenacity import retry, wait_random_exponential, stop_after_attempt

from WrenchCL import wrench_logger


class ChatGptSuperClass:

    def __init__(self, secrets_path='../resources/secrets/Secrets.env'):
        self.returned_response = None
        self.response = None
        self.secrets_input = pathlib.Path(secrets_path)
        self.secrets_path = pathlib.Path(self.secrets_input)
        self.message = None

        # Run Methods
        self._load_configuration()
        self.fetch_response()

    def _load_configuration(self):
        self.secrets_path = os.path.abspath(os.path.join(os.getcwd(), self.secrets_input))
        self._secrets_finder()

        load_dotenv(self.secrets_path)
        openai.api_key = os.getenv('CHATGPT_API_KEY')
        self.request_url = os.getenv('CHATGPT_API_ENDPOINT')
        wrench_logger.debug(f'Found request url: {self.request_url}')

    def _secrets_finder(self):
        parent_count = 0
        while True:
            time.sleep(0.05)
            try:
                if parent_count > 5:
                    raise ValueError('Maximum parent count reached.')

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

    def fetch_response(self):
        if self.message is None or self.function is None:
            if self.message is None:
                self._message_generator()
            if self.function is None:
                wrench_logger.warning("No custom function defined for Chatgpt Plugin.")
                self._function_generator()

        self.returned_response = self.chat_completion_request()
        self._parse_response()

    def _parse_response(self):
        if self.returned_response is not None:
            try:
                self.response = json.loads(self.returned_response.text)
                self.response = self.response['choices'][0]['message']['content']
                self.response = ast.literal_eval(self.response)
            except Exception as e:
                wrench_logger.error(e)

    def _message_generator(self):
        # These functions are meant to be overwritten in a subclass
        raise NotImplementedError
        pass



    def _function_generator(self):
        # This function is meant to be overwritten in a subclass.
        # If no function is meant to be passed make sure to pass self.function as None
        raise not NotImplementedError
        pass

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    def chat_completion_request(self):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + openai.api_key,
        }
        json_data = {"model": "gpt-4", "messages": self.message}
        if self.function is not None:
            json_data.update({"functions": self.function})

        try:
            wrench_logger.info("Getting ChatGPT Response...")
            response = requests.post(
                self.request_url,
                headers=headers,
                json=json_data,
            )

            if response.status_code != 200:
                wrench_logger.info(response.text)
                raise ConnectionError(f'ConnectionError: Invalid status code received = {response.status_code}')
            else:
                wrench_logger.info("ChatGPT response successfully received")
                return response
        except Exception as e:
            wrench_logger.error(f"Error while generating response | {e}")

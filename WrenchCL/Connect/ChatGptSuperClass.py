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

import ast
import json
import openai
import requests
from tenacity import retry, wait_random_exponential, stop_after_attempt

from WrenchCL.Utility.WrenchLogger import wrench_logger


class ChatGptSuperClass:

    def __init__(self, endpoint=None, key=None):
        self.function = None
        self.returned_response = None
        self.response = None
        self.message = None
        self.request_url = endpoint
        self.chat_gpt_key = key

        if self.request_url is None or self.chat_gpt_key is None:
            wrench_logger.error(f"Please provide the API key and endpoint")
        else:
            openai.api_key = self.chat_gpt_key
            self.request_url = self.request_url
        self.fetch_response()

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
        raise NotImplementedError
        pass

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    def chat_completion_request(self):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + str(openai.api_key),
        }
        json_data = {"model": "gpt-4", "messages": self.message}
        if self.function is not None:
            json_data.update({"functions": self.function})

        try:
            wrench_logger.debug("Getting ChatGPT Response...")
            response = requests.post(
                self.request_url,
                headers=headers,
                json=json_data,
            )
            if response.status_code != 200:
                wrench_logger.debug(response.text)
                raise ConnectionError(f'ConnectionError: Invalid status code received = {response.status_code}')
            else:
                wrench_logger.debug("ChatGPT response successfully received")
                return response
        except Exception as e:
            wrench_logger.error(f"Error while generating response | {e}")

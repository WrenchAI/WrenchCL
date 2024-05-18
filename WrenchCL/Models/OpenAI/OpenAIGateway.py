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

#
#  MIT License
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#
#
#  All works within the Software are owned by their respective creators and are distributed by Wrench.AI.
#
#  For inquiries, please contact Willem van der Schans through the official Wrench.AI channels or directly via GitHub at [Kydoimos97](https://github.com/Kydoimos97).
#

import json
import base64
import os
from openai import OpenAI

from ...Decorators.TimedMethod import TimedMethod
from ._ConversationManager import ConversationManager
from ...Tools.WrenchLogger import logger


class OpenAIGateway:
    """
    A gateway class to interact with OpenAI's API, providing methods to handle text, image, and audio processing.
    """

    def __init__(self, api_key=None):
        """
        Initializes the OpenAIGateway with the provided API key or retrieves it from environment variables.

        :param api_key: The OpenAI API key.
        :type api_key: str, optional
        """
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)

    def process_input(self, text=None, image_path=None, audio_path=None, operation="text", system_prompt=None,
                      json_mode=False, **kwargs):
        """
        Processes input based on the specified operation.

        :param text: The text input.
        :type text: str, optional
        :param image_path: The path to the image file.
        :type image_path: str, optional
        :param audio_path: The path to the audio file.
        :type audio_path: str, optional
        :param operation: The type of operation to perform (e.g., "text", "image", "audio").
        :type operation: str, optional
        :param system_prompt: A system prompt to include in the request.
        :type system_prompt: str, optional
        :param json_mode: If True, expects the response to be in JSON format.
        :type json_mode: bool, optional
        :returns: The result of the specified operation.
        :raises ValueError: If no input is provided or the parameters are invalid for the requested operation.
        """
        if not text and not image_path and not audio_path:
            raise ValueError("At least one of text, image_path, or audio_path must be provided.")

        if system_prompt:
            kwargs['system_prompt'] = system_prompt

        if json_mode:
            kwargs['response_format'] = {'type': 'json_object'}

        if operation == "embeddings":
            return self.get_embeddings(text, **kwargs)
        elif operation == "text":
            return self.text_response(text, **kwargs)
        elif operation == 'thread' or operation == 'conversation':
            return self.start_conversation(text, **kwargs)
        elif operation == "image" and text:
            return self.text_to_image(text, **kwargs)
        elif operation == "audio" and audio_path:
            return self.audio_to_text(audio_path, **kwargs)
        elif operation == "edit_image" and image_path:
            return self.modify_image(image_path, text, **kwargs)
        elif operation == "create_variation" and image_path:
            return self.generate_image_variations(image_path, **kwargs)
        elif operation == "vision" and text and image_path:
            return self.image_to_text(text, image_path, **kwargs)
        else:
            raise ValueError("Invalid or insufficient parameters for requested operation.")

    @TimedMethod
    def text_response(self, text, model="gpt-3.5-turbo", system_prompt=None, image_url=None, json_mode=False, stream=False, **kwargs):
        """
        Processes text input using the specified model and returns the response.

        :param text: The text input.
        :type text: str
        :param model: The model to use for text processing.
        :type model: str, optional
        :param system_prompt: A system prompt to include in the request.
        :type system_prompt: str, optional
        :param image_url: An image URL to include in the request.
        :type image_url: str, optional
        :param json_mode: If True, expects the response to be in JSON format.
        :type json_mode: bool, optional
        :param stream: If True, stream the response as it's generated.
        :type stream: bool, optional
        :returns: The processed text or JSON response.
        :raises ValueError: If the JSON response cannot be decoded.
        :raises InterruptedError: If the response cannot be completed due to content filters or other issues.
        :raises Exception: If an error occurs during text processing.
        """
        try:
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": [{"type": "text", "text": system_prompt}]})

            user_content = [{"type": "text", "text": text}]
            if image_url:
                user_content.append({"type": "image_url", "image_url": image_url})

            messages.append({"role": "user", "content": user_content})

            if stream:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=True,
                    max_tokens=kwargs.get('max_tokens', 2500)
                )
                return response
            else:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=kwargs.get('max_tokens', 2500)
                )

                finish_reason = response.choices[0].finish_reason
                if finish_reason == 'stop':
                    response_content = response.choices[0].message.content
                elif finish_reason == 'length':
                    logger.warning(f"Not enough tokens available to complete message. Please increase max tokens | current setting = {kwargs.get('max_tokens', 2500)}")
                    response_content = response.choices[0].message.content
                elif finish_reason == 'content_filter':
                    logger.error("ChatGPT does not allow processing of this content due to its content filters. Cannot return any output.")
                    response_content = None
                    raise InterruptedError
                else:
                    logger.error(f"LLM did not finish output due to reason {finish_reason}. No output returned.")
                    response_content = None
                    raise InterruptedError

                if json_mode:
                    try:
                        return json.loads(response_content)
                    except json.JSONDecodeError:
                        logger.error("Failed to decode JSON response.")
                        raise ValueError("Invalid JSON response.")

                return response_content

        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            raise


    @TimedMethod
    def get_embeddings(self, text, model="text-embedding-3-small"):
        """
        Retrieves embeddings for the given text using the specified model.

        :param text: The text input.
        :type text: str
        :param model: The model to use for generating embeddings.
        :type model: str, optional
        :returns: The generated embeddings.
        :raises Exception: If an error occurs while retrieving embeddings.
        """
        try:
            response = self.client.embeddings.create(input=text, model=model)
            embeddings = response.data[0].embedding
            return embeddings
        except Exception as e:
            logger.error(f"Error getting embeddings: {str(e)}")
            raise

    @TimedMethod
    def text_to_image(self, prompt, size="1024x1024", quality="standard", n=1):
        """
        Generates an image based on the provided prompt.

        :param prompt: The image prompt.
        :type prompt: str
        :param size: The size of the generated image.
        :type size: str, optional
        :param quality: The quality of the generated image.
        :type quality: str, optional
        :param n: The number of images to generate.
        :type n: int, optional
        :returns: The URL of the generated image.
        :raises Exception: If an error occurs while generating the image.
        """
        try:
            response = self.client.images.generate(model="dall-e-3", prompt=prompt, size=size, quality=quality, n=n)
            return response.data[0].url
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            raise

    @TimedMethod
    def audio_to_text(self, audio_path, model="whisper-1"):
        """
        Processes an audio file and returns its transcription.

        :param audio_path: The path to the audio file.
        :type audio_path: str
        :param model: The model to use for audio processing.
        :type model: str, optional
        :returns: The transcription of the audio file.
        :raises Exception: If an error occurs while processing the audio.
        """
        try:
            with open(audio_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(model=model, file=audio_file, response_format="verbose_json", timestamp_granularities=["segment"])
            transcript_text = """\n"""
            for segment in transcription.segments:
                segment_text = f"[{segment['start']*1000:.0f}ms-{segment['end']*1000:.0f}ms] {segment['text']}\n"
                transcript_text = transcript_text + segment_text
            return transcript_text
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            raise

    @TimedMethod
    def generate_image_variations(self, image_path, n=1, size="1024x1024"):
        """
        Creates variations of an image based on the provided image path.

        :param image_path: The path to the original image.
        :type image_path: str
        :param n: The number of image variations to create.
        :type n: int, optional
        :param size: The size of the generated image variations.
        :type size: str, optional
        :returns: The URL of the generated image variation.
        :raises Exception: If an error occurs while creating image variations.
        """
        try:
            with open(image_path, "rb") as image:
                response = self.client.images.create_variation(image=image, n=n, model="dall-e-2", size=size)
            return response.data[0].url
        except Exception as e:
            logger.error(f"Error creating image variation: {str(e)}")
            raise

    @TimedMethod
    def modify_image(self, image_path, prompt, mask_path, n=1, size="1024x1024"):
        """
        Edits an image based on the provided prompt and mask.

        :param image_path: The path to the original image.
        :type image_path: str
        :param prompt: The prompt describing the edits.
        :type prompt: str
        :param mask_path: The path to the mask image.
        :type mask_path: str
        :param n: The number of edited images to create.
        :type n: int, optional
        :param size: The size of the edited images.
        :type size: str, optional
        :returns: The URL of the edited image.
        :raises Exception: If an error occurs while editing the image.
        """
        try:
            with open(image_path, "rb") as image, open(mask_path, "rb") as mask:
                response = self.client.images.edit(model="dall-e-2", image=image, mask=mask, prompt=prompt, n=n, size=size)
            return response.data[0].url
        except Exception as e:
            logger.error(f"Error editing image: {str(e)}")
            raise

    @TimedMethod
    def image_to_text(self, question, image_path, **kwargs):
        """
        Processes a vision query based on the provided question and image.

        :param question: The question to ask.
        :type question: str
        :param image_path: The path to the image file.
        :type image_path: str
        :returns: The response to the vision query.
        :raises Exception: If an error occurs while processing the vision query.
        """
        try:
            image_content = self.convert_image_to_url_or_base64(image_path)
            messages = [{"role": "user", "content": [{"type": "text", "text": question},
                                                     {"type": "image_url", "image_url": {"url": image_content}}]}]
            response = self.client.chat.completions.create(model="gpt-4-turbo", messages=messages, max_tokens=300,
                                                           **kwargs)
            return response.choices[0]
        except Exception as e:
            logger.error(f"Error in vision query: {str(e)}")
            raise

    @TimedMethod
    def convert_image_to_url_or_base64(self, image_path):
        """
        Converts an image to a URL or base64 encoded string.

        :param image_path: The path to the image file.
        :type image_path: str
        :returns: The image URL or base64 encoded string.
        :raises ValueError: If the image path or data is invalid.
        :raises Exception: If an error occurs while processing the image.
        """
        if image_path.startswith("http://") or image_path.startswith("https://"):
            return image_path
        try:
            with open(image_path, "rb") as image_file:
                return f"data:image/jpeg;base64,{base64.b64encode(image_file.read()).decode('utf-8')}"
        except Exception as e:
            logger.error("Failed to process image for vision query")
            raise ValueError("Invalid image path or data.")

    @TimedMethod
    def start_conversation(self, **kwargs):
        """
        Initiates a conversation using the provided initial text.

        :raises Exception: If an error occurs while initiating the conversation.
        """
        conversation_manager = ConversationManager(self.client, kwargs.get("assistant_id"))
        conversation_manager.initiate_conversation()

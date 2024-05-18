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

from ...Decorators.TimedMethod import TimedMethod
from .OpenAIGateway import OpenAIGateway


class OpenAIFactory(OpenAIGateway):
    """
    A factory class that extends OpenAIGateway to provide additional methods for processing audio, images, and text,
    and generating embeddings using OpenAI's models.
    """

    def __init__(self, api_key):
        """
        Initializes the OpenAIFactory with the provided API key.

        :param api_key: The OpenAI API key.
        :type api_key: str
        """
        super().__init__(api_key)

    @TimedMethod
    def audio_to_text_to_embeddings(self, audio_path, embedding_model="text-embedding-3-small"):
        """
        Transcribes audio to text and then generates embeddings for the text.

        :param audio_path: The path to the audio file.
        :type audio_path: str
        :param embedding_model: The model to use for generating embeddings.
        :type embedding_model: str, optional
        :returns: The generated embeddings for the transcribed text.
        :rtype: list
        """
        transcription = self.audio_to_text(audio_path, model="whisper-1")
        embeddings = self.get_embeddings(transcription, model=embedding_model)
        return embeddings

    @TimedMethod
    def image_to_text_to_embeddings(self, image_path, question, embedding_model="text-embedding-3-small"):
        """
        Performs a vision query to understand an image and then generates embeddings for the response.

        :param image_path: The path to the image file.
        :type image_path: str
        :param question: The question to ask about the image.
        :type question: str
        :param embedding_model: The model to use for generating embeddings.
        :type embedding_model: str, optional
        :returns: The generated embeddings for the vision query response.
        :rtype: list
        """
        vision_response = self.image_to_text(question, image_path)
        embeddings = self.get_embeddings(vision_response, model=embedding_model)
        return embeddings

    @TimedMethod
    def validate_response_with_gpt(self, initial_response, validation_prompt):
        """
        Uses an initial response and validates or expands upon it with a secondary GPT call.

        :param initial_response: The initial response to validate or expand.
        :type initial_response: str
        :param validation_prompt: The prompt to use for validation or expansion.
        :type validation_prompt: str
        :returns: The validated or expanded response.
        :rtype: str
        """
        validated_response = self.text_response(validation_prompt + initial_response)
        return validated_response

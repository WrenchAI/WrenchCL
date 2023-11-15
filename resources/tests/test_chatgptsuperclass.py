import pytest
from unittest.mock import MagicMock, patch
from WrenchCL import ChatGptSuperClass

class TestChatGptSuperClass:

    @pytest.fixture
    def chat_gpt_instance(self, mocker):
        with patch('openai.api_key', new_callable=MagicMock(return_value="mock_api_key")):
            with patch.object(ChatGptSuperClass, '_message_generator', new_callable=MagicMock):
                with patch.object(ChatGptSuperClass, '_function_generator', new_callable=MagicMock):
                    instance = ChatGptSuperClass(endpoint="https://example.com", key="test-key")
                    instance.message = "default message"
                    instance.function = "default function"
                    return instance


    @pytest.fixture
    def mock_requests_post(self, mocker):
        return mocker.patch('requests.post')

    def test_initialization(self, chat_gpt_instance):
        assert chat_gpt_instance.request_url == "https://example.com"
        assert chat_gpt_instance.chat_gpt_key == "test-key"

    def test_fetch_response_no_message_no_function(self, chat_gpt_instance, mocker):
        mocker.patch.object(chat_gpt_instance, '_message_generator', return_value=None)
        mocker.patch.object(chat_gpt_instance, '_function_generator', return_value=None)
        mocker.patch.object(chat_gpt_instance, 'chat_completion_request', return_value=None)

        chat_gpt_instance.fetch_response()
        assert chat_gpt_instance.returned_response is None

    def test_chat_completion_request_success(self, chat_gpt_instance, mocker):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"choices": [{"message": {"content": "[\'response\']"}}]}'
        mocker.patch('requests.post', return_value=mock_response)

        chat_gpt_instance.message = ['test message']
        response = chat_gpt_instance.chat_completion_request()

        assert response.status_code == 200
        assert response.text == '{"choices": [{"message": {"content": "[\'response\']"}}]}'

    def test_chat_completion_request_failure(self, chat_gpt_instance, mocker, caplog):
        # Create a mock response object with a 500 status code
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = 'Server Error'

        # Apply the mock to requests.post
        mocker.patch('requests.post', return_value=mock_response)

        chat_gpt_instance.message = ['test message']

        # Execute the method
        chat_gpt_instance.chat_completion_request()

        # Check if the specific log message was generated
        assert any("Error while generating response" in message for message in caplog.messages)


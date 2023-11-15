import pytest
import requests
from unittest.mock import MagicMock
from WrenchCL import ApiSuperClass  # Replace 'your_module' with the actual module name
from WrenchCL.ApiSuperClass import MaxRetriesExceededError
import pandas as pd

class TestApiSuperClass:

    @pytest.fixture
    def api_super_class(self):
        return ApiSuperClass("https://example.com")

    @pytest.fixture
    def mock_requests_post(self, mocker):
        return mocker.patch('requests.post')

    def test_fetch_from_api_success(self, api_super_class, mock_requests_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': 'some data'}
        mock_requests_post.return_value = mock_response

        response = api_super_class._fetch_from_api("https://example.com/api", {}, {})
        assert response == {'data': 'some data'}

    def test_fetch_from_api_failure(self, api_super_class, mock_requests_post):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_requests_post.return_value = mock_response

        response = api_super_class._fetch_from_api("https://example.com/api", {}, {})
        assert response is None

    def test_batch_processor_success(self, api_super_class, mocker):
        mocker.patch.object(api_super_class, 'get_count', return_value=10)
        mocker.patch.object(api_super_class, 'fetch_data', return_value=([], None, None, False))
        mocker.patch('time.sleep')

        result = api_super_class.batch_processor()
        assert isinstance(result, pd.DataFrame)

    def test_batch_processor_with_data(self, api_super_class, mocker):
        # Mocking a scenario where fetch_data returns some data
        mocker.patch.object(api_super_class, 'get_count', return_value=10)
        mocker.patch.object(api_super_class, 'fetch_data', return_value=([{'id': 1}], None, None, True))
        mocker.patch('time.sleep')

        result = api_super_class.batch_processor()
        assert len(result) > 0  # Expecting some data in the DataFrame

    def test_batch_processor_max_retries_exceeded(self, api_super_class, mocker):
        mocker.patch.object(api_super_class, 'get_count', return_value=10)
        mocker.patch.object(api_super_class, 'fetch_data', side_effect=requests.exceptions.ConnectionError)
        mocker.patch('time.sleep')

        with pytest.raises(MaxRetriesExceededError):
            api_super_class.batch_processor()


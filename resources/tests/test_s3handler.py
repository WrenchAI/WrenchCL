import pytest
from unittest.mock import MagicMock, patch

from WrenchCL.S3Handler import S3Handler


@pytest.fixture(scope='function')
def s3_instance():
    S3Handler._instance = None  # Reset Singleton instance for each test
    handler = S3Handler()
    with patch('boto3.client', return_value=MagicMock()) as mock_boto3_client:
        handler.load_configuration('key_id', 'secret_key', 'region')
        yield handler


@pytest.fixture(scope='function')
def s3_instance_no_sub():
    S3Handler._instance = None  # Reset Singleton instance for each test
    with patch('boto3.client', return_value=MagicMock()):
        yield S3Handler()


@pytest.fixture
def mock_boto3_client(mocker):
    with patch('boto3.client') as mock_client:
        yield mock_client


def test_load_configuration_success(s3_instance, mock_boto3_client):
    s3_instance.load_configuration('key_id', 'secret_key', 'region')
    assert s3_instance.initialized is True
    assert mock_boto3_client.called


def test_load_configuration_failure(s3_instance, mocker):
    mocker.patch('boto3.client', side_effect=Exception("Error"))
    with pytest.raises(Exception):
        s3_instance.load_configuration('key_id', 'secret_key', 'region')
    assert s3_instance.initialized is False


def test_list_files_not_initialized(s3_instance_no_sub):
    with pytest.raises(NotImplementedError):
        s3_instance_no_sub.list_files('bucket')


def test_list_files_success(s3_instance):
    # Configure the mock s3_client to return a mock response for list_objects_v2
    s3_instance.s3_client.list_objects_v2.return_value = {'Contents': [{'Key': 'file1'}, {'Key': 'file2'}]}

    files = s3_instance.list_files('bucket')
    assert len(files) == 2
    assert 'file1' in files
    assert 'file2' in files


def test_upload_file_success(s3_instance):
    s3_instance.initialized = True  # Manually set to initialized
    result = s3_instance.upload_file('bucket', '/path/to/file', 's3_path')
    assert result is True


def test_upload_file_failure(s3_instance):
    s3_instance.s3_client.upload_file.side_effect = Exception("Error")
    s3_instance.initialized = True
    result = s3_instance.upload_file('bucket', '/path/to/file', 's3_path')
    assert result is False


def test_delete_file_success(s3_instance):
    s3_instance.initialized = True  # Manually set to initialized
    result = s3_instance.delete_file('bucket', 's3_path')
    assert result is True


def test_delete_file_failure(s3_instance):
    s3_instance.s3_client.delete_object.side_effect = Exception("Error")
    s3_instance.initialized = True
    result = s3_instance.delete_file('test bucket', 'test file')
    assert result is False

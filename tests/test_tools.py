import pytest
from WrenchCL.Tools import coalesce
from WrenchCL.Tools import get_metadata
from WrenchCL.Tools import get_file_type
from WrenchCL.Tools import image_to_base64, validate_base64
from WrenchCL.Tools import get_hash
from WrenchCL.Tools import robust_serializer
from WrenchCL.Tools import single_quote_decoder
from WrenchCL.Tools import Maybe
from WrenchCL.Tools import typechecker
from WrenchCL.Tools import logger
import json
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch, mock_open, MagicMock
import atexit
import logging

pytestmark = pytest.mark.skipif(False, reason="datadog_itr_unskippable")

def test_coalesce():
    assert coalesce(None, None, "first non-none", 5) == "first non-none"
    assert coalesce(None, None, None) is None

@patch('requests.head')
@patch('requests.get')
def test_get_metadata(mock_get, mock_head):
    mock_head.return_value.headers = {
        'Content-Type': 'text/plain',
        'Content-Length': '1024',
        'Last-Modified': 'Wed, 21 Oct 2015 07:28:00 GMT'
    }
    mock_head.return_value.raise_for_status = MagicMock()

    metadata = get_metadata("https://example.com/file.txt")
    assert metadata['content_type'] == 'text/plain'
    assert metadata['content_length'] == '1024'
    assert metadata['url'] == 'https://example.com/file.txt'
    assert metadata['last_modified'] == datetime(2015, 10, 21, 7, 28)

    with patch('os.path.getsize') as mock_getsize, patch('os.path.getctime') as mock_getctime:
        mock_getsize.return_value = 2048
        mock_getctime.return_value = 1598306400.0  # Example timestamp

        metadata = get_metadata("/files/file.txt", is_url=False)
        assert metadata['file_size'] == 2048
        assert metadata['creation_time'] == datetime.fromtimestamp(1598306400.0).isoformat()

@patch('requests.head')
def test_get_file_type(mock_head):
    mock_head.return_value.headers = {
        'Content-Type': 'image/png'
    }
    mock_head.return_value.raise_for_status = MagicMock()

    file_extension, mime_type = get_file_type("https://example.com/image.png")
    assert file_extension == '.png'
    assert mime_type == 'image/png'

    with patch('os.path.getsize'), patch('os.path.getctime'), patch('os.path.exists') as mock_exists:
        mock_exists.return_value = True
        file_extension, mime_type = get_file_type("/files/image.png", is_url=False)
        assert file_extension == '.png'

@patch('requests.get')
def test_image_to_base64(mock_get):
    mock_get.return_value.content = b'\x89PNG\r\n\x1a\n'
    mock_get.return_value.raise_for_status = MagicMock()

    base64_str = image_to_base64("https://example.com/image.png")
    assert validate_base64(base64_str)

    with patch('builtins.open', mock_open(read_data=b'\x89PNG\r\n\x1a\n')):
        base64_str = image_to_base64("/files/image.png", is_url=False)
        assert validate_base64(base64_str)

def test_get_hash():
    assert get_hash('test') == 'a94a8fe5ccb19ba61c4c0873d391e987982fbbd3'

def test_robust_serializer():
    assert robust_serializer(datetime(2024, 5, 17)) == '2024-05-17T00:00:00'
    assert robust_serializer(Decimal('123.45')) == 123.45

    class CustomObject:
        def __init__(self, value):
            self.value = value

    obj = CustomObject(10)
    assert robust_serializer(obj) == {'value': 10}

def test_single_quote_decoder():
    json_str = "{'name': 'John', 'age': 30, 'city': 'New York'}"
    decoded_obj = json.loads(json_str, cls=single_quote_decoder)
    assert decoded_obj == {'name': 'John', 'age': 30, 'city': 'New York'}

def test_maybe():
    assert Maybe(None).value is None
    assert Maybe(10).value == 10

    maybe = Maybe("test").upper().get_value()
    assert maybe == "TEST"

    maybe = Maybe(None).upper().get_value()
    assert maybe is None

def test_typechecker():
    data = [
        {"name": "John", "age": 30},
        {"name": "Jane", "age": 25}
    ]
    expected_types = {"name": str, "age": int}

    assert typechecker(data, expected_types)

    invalid_data = [
        {"name": "John", "age": 30},
        {"name": "Jane", "age": "twenty"}
    ]
    with pytest.raises(TypeError):
        typechecker(invalid_data, expected_types)

def test_logger_basic(caplog):
    
    # Attach the caplog handler to capture logs
    logger.logger.addHandler(caplog.handler)
    logger.logger.setLevel(logging.INFO)

    logger.info("Info message")
    assert "Info message" in caplog.text
    logger.warning("Warning message")
    assert "Warning message" in caplog.text
    logger.error(ValueError("Error message"))
    assert "Error message" in caplog.text
    assert "---Stack Trace---" in caplog.text

def test_logger_flow(caplog):
    
    # Attach the caplog handler to capture logs
    logger.logger.addHandler(caplog.handler)
    logger.logger.setLevel(logging.INFO)

    logger.flow("Flow message")
    assert "Flow message" in caplog.text

def test_logger_context(caplog):
    
    # Attach the caplog handler to capture logs
    logger.logger.addHandler(caplog.handler)
    logger.logger.setLevel(logging.INFO)

    logger.context("Context message")
    assert "Context message" in caplog.text

def test_logger_hdl_warn(caplog):
    
    # Attach the caplog handler to capture logs
    logger.logger.addHandler(caplog.handler)
    logger.logger.setLevel(logging.WARNING)

    logger.HDL_WARN("Handle warning message")
    assert "Handle warning message" in caplog.text

def test_logger_hdl_err(caplog):
    
    # Attach the caplog handler to capture logs
    logger.logger.addHandler(caplog.handler)
    logger.logger.setLevel(logging.ERROR)

    logger.HDL_ERR("Handle error message")
    assert "Handle error message" in caplog.text

def test_logger_recv_err(caplog):
    
    # Attach the caplog handler to capture logs
    logger.logger.addHandler(caplog.handler)
    logger.logger.setLevel(logging.ERROR)

    logger.RECV_ERR("Recoverable error message")
    assert "Recoverable error message" in caplog.text

def test_logger_data(caplog):
    
    # Attach the caplog handler to capture logs
    logger.logger.addHandler(caplog.handler)
    logger.logger.setLevel(logging.INFO)

    logger.data({"key": "value"}, object_name='Test Dict')
    assert '"key": "value"' in caplog.text
    assert 'Test Dict' in caplog.text

def test_logger_time(caplog):
    
    logger.start_time()
    # Attach the caplog handler to capture logs
    logger.logger.addHandler(caplog.handler)
    logger.logger.setLevel(logging.INFO)

    logger.log_time("Elapsed time")
    assert "Elapsed time" in caplog.text

def test_logger_compact_header(caplog):
    
    # Attach the caplog handler to capture logs
    logger.logger.addHandler(caplog.handler)
    logger.logger.setLevel(logging.INFO)
    logger.compact_header("Header message")
    assert "Header message" in caplog.text

def test_logger_set_level():
    
    logger.setLevel("DEBUG")
    assert logger.logger.getEffectiveLevel() == logging.DEBUG

def test_logger_revert_logging_level():
    
    logger.setLevel("INFO")
    logger.setLevel("ERROR")
    print(logging.ERROR)
    assert logger.logger.getEffectiveLevel() == logging.ERROR
    logger.revertLoggingLevel()
    assert logger.logger.getEffectiveLevel() == logging.INFO  # assuming default level is INFO

def test_logger_set_global_traceback():
    
    logger.set_global_traceback(True)
    assert logger.force_stack_trace
    logger.set_global_traceback(False)
    assert not logger.force_stack_trace

def test_logger_verbose_mode():
    
    assert not logger.non_verbose_mode
    logger.set_verbose(False)
    assert logger.non_verbose_mode

@atexit.register
def shutdown_logging():
    import logging
    logging.shutdown()

if __name__ == '__main__':
    pytest.main()

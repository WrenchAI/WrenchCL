import pytest
import logging
import os
from WrenchCL.WrenchLogger import _wrench_logger


@pytest.fixture
def logger():
    return _wrench_logger(level='DEBUG')


def test_singleton_behavior():
    logger1 = _wrench_logger(level='INFO')
    logger2 = _wrench_logger(level='INFO')
    assert logger1 is logger2, "Singleton pattern not maintained for same configuration"

    logger3 = _wrench_logger(level='DEBUG')
    assert logger1 is logger3, "Different configurations are resulting in the same instance"


def test_log_file_creation(logger):
    assert not os.path.exists(logger.filename), "Log file not created"
    logger.set_log_file_location()
    assert os.path.exists(logger.filename), 'Log file created after turning on file logging'


def test_setLevel(logger):
    logger.setLevel('DEBUG')
    assert logger.logging_level == logging.DEBUG, "setLevel() did not update the logger level correctly"


def test_info_log(logger, caplog):
    with caplog.at_level(logging.INFO):
        logger.info("Test info message.")
        assert "Test info message." in caplog.text


def test_warning_log(logger, caplog):
    with caplog.at_level(logging.WARNING):
        logger.warning("Test warning message.")
        assert "Test warning message." in caplog.text


def test_error_log(logger, caplog):
    with caplog.at_level(logging.ERROR):
        logger.error("Test error message.")
        assert "Test error message." in caplog.text


def test_critical_log(logger, caplog):
    with caplog.at_level(logging.CRITICAL):
        logger.critical("Test critical message.")
        assert "Test critical message." in caplog.text


def test_debug_log(logger, caplog):
    with caplog.at_level(logging.DEBUG):
        logger.debug("Test debug message.")
        assert "Test debug message." in caplog.text

def test_log_header(logger, caplog):
    with caplog.at_level(logging.INFO):
        logger.header("Test Header")
        assert "Test Header".center(80, "-") in caplog.text


def test_invalid_logging_level():
    with pytest.raises(ValueError, match="Invalid logging level"):
        _wrench_logger(level='INVALID_LEVEL')




if __name__ == "__main__":
    pytest.main([__file__])


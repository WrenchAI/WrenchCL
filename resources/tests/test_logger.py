import sys
from unittest.mock import patch

import pytest
import logging
import os
from WrenchCL.WrenchLogger import _wrench_logger


@pytest.fixture
def logger():
    log_instance = _wrench_logger(level='INFO')
    yield log_instance

def test_singleton_behavior():
    logger1 = _wrench_logger(level='INFO')
    logger2 = _wrench_logger(level='INFO')
    assert logger1 is logger2, "Singleton pattern not maintained for same configuration"

    logger3 = _wrench_logger(level='DEBUG')
    assert logger1 is logger3, "Different configurations are resulting in the same instance"

def test_log_file_creation(logger):
    assert logger.filename is None, "Log file not created"
    logger.set_log_file_location()
    assert os.path.exists(logger.filename), 'Log file created after turning on file logging'
    logger.release_resources()

    try:
        os.remove(logger.filename)
        if str(os.path.dirname(logger.filename)).split("\\")[-1].lower() == 'logs':
            os.rmdir(os.path.dirname(logger.filename))
            print("removed logs folder")
    except:
        pass


def test_setLevel(logger):
    logger.setLevel('DEBUG')
    assert logger.logging_level == logging.DEBUG, "setLevel() did not update the logger level correctly"
    logger.revertLoggingLevel()
    assert logger.logging_level == logging.INFO, "Logging level not successfully reverted"


def test_info_log(logger, caplog):
    with caplog.at_level(logging.INFO):
        logger.info("Test info message.")
        assert "Test info message." in caplog.text

def test_context_log(logger, caplog):
    with caplog.at_level(logging.INFO):
        logger.context("Test context message.")
        assert "Test context message." in caplog.text


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


def test_invalid_logging_level(logger):
    delattr(logger, '_initialized')  # circumvent singleton behaviour
    with pytest.raises(ValueError, match="Invalid logging level"):
        _wrench_logger(level='INVALID_LEVEL')

def test_lambda_environment_detection():
    with patch.dict(os.environ, {'AWS_LAMBDA_FUNCTION_NAME': 'test_lambda_function'}):
        lambda_logger = _wrench_logger(level='INFO')
        assert lambda_logger.running_on_lambda, "Failed to detect AWS Lambda environment"
        # Clean up by removing the logger instance to avoid interference with other tests
        del lambda_logger

def test_no_double_logging_in_lambda(caplog):
    # Simulate AWS Lambda's default logging setup by adding a handler to the root logger
    simulated_lambda_handler = logging.StreamHandler(sys.stdout)
    logging.getLogger().addHandler(simulated_lambda_handler)

    with patch.dict(os.environ, {'AWS_LAMBDA_FUNCTION_NAME': 'test_lambda_function'}), caplog.at_level(logging.INFO):
        # Instantiate the logger after modifying the environment to simulate Lambda detection
        lambda_logger = _wrench_logger(level='INFO')

        lambda_logger.info("Test message for no double logging.")

        # Count occurrences of the log message
        occurrences = caplog.text.count("Test message for no double logging.")
        assert occurrences == 1, "Log message should be logged exactly once in AWS Lambda environment"

    # Cleanup: Remove the simulated Lambda handler from the root logger
    logging.getLogger().removeHandler(simulated_lambda_handler)
    # Reset the singleton instance to prevent test side effects
    _wrench_logger._instance = None



if __name__ == "__main__":
    pytest.main([__file__])

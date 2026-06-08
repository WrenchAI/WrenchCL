import logging
from unittest.mock import patch

import pytest

from WrenchCL import logger


@pytest.fixture(autouse=True)
def fresh_logger():
    logger.configure()
    yield logger
    try:
        logger.kill()
    except Exception:
        pass


def test_from_wrenchcl_import_logger():
    from WrenchCL import logger as imported_logger

    assert imported_logger is not None


def test_isinstance_logging_logger():
    assert isinstance(logger, logging.Logger)


def test_configure_terminal_mode():
    logger.configure(mode="terminal")


def test_configure_json_mode():
    with patch("WrenchCL._Internal.WrenchLogger.SparkJsonHandler") as mock_handler:
        logger.configure(mode="json")

    mock_handler.assert_called_once_with()


def test_configure_deployment_mode():
    with patch("WrenchCL._Internal.WrenchLogger.SparkJsonHandler") as mock_handler:
        logger.configure(deployment_mode=True)

    mock_handler.assert_called_once_with()


def test_multiple_configure_calls():
    logger.configure()
    logger.configure(mode="terminal")
    with patch("WrenchCL._Internal.WrenchLogger.SparkJsonHandler") as mock_handler:
        logger.configure(mode="json")

    mock_handler.assert_called_once_with()


def test_initiate_new_run_returns_string():
    run_id = logger.initiate_new_run()

    assert isinstance(run_id, str)
    assert run_id


def test_run_id_matches_after_initiate():
    run_id = logger.initiate_new_run()

    assert logger.run_id == run_id


def test_cycle_run_changes_run_id():
    first_run_id = logger.cycle_run()
    second_run_id = logger.cycle_run()

    assert first_run_id != second_run_id


def test_instance_returns_self():
    assert logger.instance is logger


def test_level_has_value_attr():
    assert isinstance(logger.level.value, int)


def test_level_value_is_int():
    assert isinstance(logger.level.value, int)


def test_success_deprecated_warning():
    with pytest.warns(UserWarning):
        logger.success("x")


def test_data_deprecated_warning():
    with pytest.warns(UserWarning):
        logger.data({})


def test_header_deprecated_warning():
    with pytest.warns(UserWarning):
        logger.header("x")


def test_cdata_deprecated_warning():
    with pytest.warns(UserWarning):
        logger.cdata("x")


def test_streams_attach_adds_handler():
    root = logging.getLogger()
    initial_count = len(root.handlers)

    logger.streams.attach("ERROR")

    assert len(root.handlers) == initial_count + 1
    root.handlers.pop()


def test_streams_intercept_warns():
    with pytest.warns(UserWarning):
        logger.streams.intercept_exceptions()


def test_info_callable():
    logger.info("test")


def test_warning_callable():
    logger.warning("test")


def test_error_callable():
    logger.error("test")


def test_exception_callable_outside_except():
    logger.exception("test")

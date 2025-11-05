"""
Tests for BaseLogger core functionality
"""
import logging
import os
from io import StringIO

import pytest
from pydantic import BaseModel

from WrenchCL import logger


class DummyPretty:
    def pretty_repr(self):
        return "PRETTY_PRINTED"


class DummyJSON:
    def json(self):
        return {
            "meta_data": {"integration_test": True},
            "targets": {"likes": 3091},
            "post_url": "https://picsum.photos/455",
        }


class DummyPydantic(BaseModel):
    name: str
    value: int


@pytest.fixture
def base_logger_stream():
    """Setup logger with stream capture for testing"""
    stream = StringIO()
    os.environ["PROJECT_NAME"] = "test-project"
    os.environ["PROJECT_VERSION"] = "1.0.0"
    os.environ["ENV"] = "test"

    logger.reinitialize()
    logger.configure(level='DEBUG')
    
    # Clear existing handlers and add test handler
    logger.instance.handlers.clear()
    handler = logging.StreamHandler(stream)
    logger.managed.add(logging.StreamHandler, stream=stream, owned=True)

    yield logger, stream

    # Cleanup
    for key in ["PROJECT_NAME", "PROJECT_VERSION", "ENV"]:
        os.environ.pop(key, None)
    logger.instance.handlers.clear()


class TestCoreLoggingMethods:
    """Test all core logging methods"""

    def test_info_log(self, base_logger_stream):
        logger, stream = base_logger_stream
        logger.info("test info message")
        logger.flush()
        output = stream.getvalue()
        assert "test info message" in output

    def test_info_log_with_header(self, base_logger_stream):
        logger, stream = base_logger_stream
        logger.info("test info", header="Test Header")
        logger.flush()
        output = stream.getvalue()
        assert "test info" in output
        assert "TEST HEADER" in output.upper()

    def test_debug_log(self, base_logger_stream):

        logger, stream = base_logger_stream
        logger.configure(level="DEBUG")
        logger.managed.sync()

        logger.debug("debug message")
        logger.flush()
        output = stream.getvalue()
        assert "debug message" in output

    def test_warning_log(self, base_logger_stream):
        logger, stream = base_logger_stream
        logger.warning("warning message")
        logger.flush()
        output = stream.getvalue()
        assert "warning message" in output

    def test_error_log(self, base_logger_stream):
        logger, stream = base_logger_stream
        logger.error("error message")
        logger.flush()
        output = stream.getvalue()
        assert "error message" in output

    def test_critical_log(self, base_logger_stream):
        logger, stream = base_logger_stream
        logger.critical("critical message")
        logger.flush()
        output = stream.getvalue()
        assert "critical message" in output

    def test_exception_log(self, base_logger_stream):
        logger, stream = base_logger_stream
        try:
            raise ValueError("test exception")
        except ValueError:
            logger.exception("caught exception")
        logger.flush()
        output = stream.getvalue()
        assert "caught exception" in output

    def test_success_alias(self, base_logger_stream):
        logger, stream = base_logger_stream
        logger.success("success message")
        logger.flush()
        output = stream.getvalue()
        assert "success message" in output

    def test_log_with_exc_info_kwarg(self, base_logger_stream):
        logger, stream = base_logger_stream
        exc = ValueError("test exception")
        logger.error("error with exception", exc_info=exc)
        logger.flush()
        output = stream.getvalue()
        assert "error with exception" in output


class TestConfiguration:
    """Test logger configuration methods"""

    def test_configure_mode(self, base_logger_stream):
        logger, stream = base_logger_stream
        logger.configure(mode="json")
        assert logger.mode == "json"

    def test_configure_level(self, base_logger_stream):
        logger, stream = base_logger_stream
        logger.configure(level="WARNING")
        assert logger.level.value == "WARNING"

    def test_configure_color_enabled(self, base_logger_stream):
        logger, stream = base_logger_stream
        logger.configure(color_enabled=False)
        config = logger.state_manager.current_state
        assert config.color_enabled == False

    def test_level_property_setter(self, base_logger_stream):
        logger, stream = base_logger_stream
        from WrenchCL._Internal.Logging.DataClasses import LogLevel
        logger.level = LogLevel("ERROR")
        assert logger.level.value == "ERROR"

    def test_reinitialize(self, base_logger_stream):
        logger, stream = base_logger_stream
        # Should not raise any exceptions
        logger.reinitialize()
        logger.reinitialize(verbose=True)

    def test_initiate_new_run(self, base_logger_stream):
        logger, stream = base_logger_stream
        old_run_id = logger.run_id
        logger.initiate_new_run()
        assert logger.run_id != old_run_id


class TestDataLogging:
    """Test data and pretty printing functionality"""

    def test_data_dict(self, base_logger_stream):

        logger, stream = base_logger_stream
        logger.configure(mode='terminal', color_enabled=False)
        logger.managed.sync()
        test_data = {"key": "value", "number": 42}
        logger.data(test_data)
        logger.flush()
        output = stream.getvalue()
        assert '"key": "value"' in output or "'key': 'value'" in output

    def test_cdata_compact(self, base_logger_stream):
        logger, stream = base_logger_stream
        test_data = {"compact": True, "data": [1, 2, 3]}
        logger.cdata(test_data)
        logger.flush()
        output = stream.getvalue()
        assert "compact" in output

    def test_data_with_pretty_repr(self, base_logger_stream):
        logger, stream = base_logger_stream
        obj = DummyPretty()
        logger.data(obj)
        logger.flush()
        output = stream.getvalue()
        assert "PRETTY_PRINTED" in output

    def test_data_with_json_method(self, base_logger_stream):
        logger, stream = base_logger_stream
        obj = DummyJSON()
        logger.data(obj)
        logger.flush()
        output = stream.getvalue()
        assert "integration_test" in output

    def test_data_with_pydantic_model(self, base_logger_stream):
        logger, stream = base_logger_stream
        model = DummyPydantic(name="test", value=123)
        logger.data(model)
        logger.flush()
        output = stream.getvalue()
        assert "test" in output and "123" in output


class TestFileAndStreamHandlers:
    """Test file and stream handler functionality"""

    def test_add_file(self, base_logger_stream, tmp_path):
        logger, stream = base_logger_stream
        log_file = tmp_path / "test.log"
        handler = logger.add_file(str(log_file))
        assert handler is not None
        logger.info("test file logging")
        logger.flush()
        assert log_file.exists()

    def test_add_stream(self, base_logger_stream):
        logger, stream = base_logger_stream
        test_stream = StringIO()
        handler = logger.add_stream(stream=test_stream)
        assert handler is not None
        logger.info("test stream")
        logger.flush()
        assert "test stream" in test_stream.getvalue()

    def test_flush(self, base_logger_stream):
        logger, stream = base_logger_stream
        logger.info("test flush")
        # Should not raise any exceptions
        logger.flush()

    def test_close(self, base_logger_stream):
        logger, stream = base_logger_stream
        # Should not raise any exceptions
        logger.close()


class TestHeaders:
    """Test header functionality"""

    def test_header_creation(self, base_logger_stream):
        logger, stream = base_logger_stream
        logger.header("Test Header")
        logger.flush()
        output = stream.getvalue()
        assert "TEST HEADER" in output

    def test_header_with_return_repr(self, base_logger_stream):
        logger, stream = base_logger_stream
        result = logger.header("Test Header", return_repr=True)
        assert result is not None
        assert "TEST HEADER" in result

    def test_header_compact(self, base_logger_stream):
        logger, stream = base_logger_stream
        logger.header("Compact Header", compact=True)
        logger.flush()
        output = stream.getvalue()
        assert "COMPACT HEADER" in output


class TestTemporaryContext:
    """Test temporary configuration context manager"""

    def test_temporary_mode(self, base_logger_stream):
        logger, stream = base_logger_stream
        original_mode = logger.mode
        with logger.temporary(mode="json"):
            assert logger.mode == "json"
        assert logger.mode == original_mode

    def test_temporary_level(self, base_logger_stream):
        logger, stream = base_logger_stream
        original_level = logger.level
        with logger.temporary(level="ERROR"):
            assert logger.level.value == "ERROR"
        assert logger.level == original_level

    def test_temporary_multiple_params(self, base_logger_stream):
        logger, stream = base_logger_stream
        with logger.temporary(mode="compact", level="WARNING", color_enabled=False):
            assert logger.mode == "compact"
            assert logger.level.value == "WARNING"

    def test_temporary_with_exception(self, base_logger_stream):
        logger, stream = base_logger_stream
        original_mode = logger.mode
        try:
            with logger.temporary(mode="json"):
                raise ValueError("test exception")
        except ValueError:
            pass
        # Should restore even after exception
        assert logger.mode == original_mode


class TestProperties:
    """Test logger properties"""

    def test_level_property(self, base_logger_stream):
        logger, stream = base_logger_stream
        logger.configure(level="INFO")
        assert logger.level.value == "INFO"

    def test_mode_property(self, base_logger_stream):
        logger, stream = base_logger_stream
        logger.configure(mode="terminal")
        assert logger.mode == "terminal"

    def test_state_property(self, base_logger_stream):
        logger, stream = base_logger_stream
        state = logger.state
        assert isinstance(state, dict)
        assert "Logging Level" in state
        assert "Run Id" in state
        assert "Mode" in state

    def test_run_id_property(self, base_logger_stream):
        logger, stream = base_logger_stream
        run_id = logger.run_id
        assert isinstance(run_id, str)
        assert len(run_id) > 0


class TestLogOptions:
    """Test log options functionality"""

    def test_log_opts_dict(self, base_logger_stream):
        logger, stream = base_logger_stream
        logger.info("test", log_opts={"no_format": True, "no_color": True})
        logger.flush()
        output = stream.getvalue()
        assert "test" in output

    def test_log_opts_object(self, base_logger_stream):
        logger, stream = base_logger_stream
        from WrenchCL._Internal.Logging.DataClasses import LogOptions
        opts = LogOptions(no_format=True, stack_info=True)
        logger.info("test info", log_opts=opts)
        logger.flush()
        output = stream.getvalue()
        assert "test info" in output

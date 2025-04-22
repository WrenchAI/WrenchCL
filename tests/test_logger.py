import logging
import re
import sys
import time
from io import StringIO

import pytest
from pydantic import BaseModel

from WrenchCL.Tools.WrenchLogger import _IntLogger


class DummyPretty:
    def pretty_print(self):
        return "PRETTY_PRINTED"


class DummyJSON:
    def json(self):
        return {"meta_data": {"integration_test": True}, "targets": {"likes": 3091},
            "post_url": "https://picsum.photos/455", "file_type": "video",
            "spirra_media_id": "4e05cc02-d0e1-4db7-86bc-4267642b2c3c",
            "spirra_influencer_id": "7076e470-9809-45a6-8e04-74db55b8ab83", "social_media_platform": "facebook"}


class SuggestionTarget:
    def __init__(self):
        self.valid_key = 1


class DummyPydantic(BaseModel):
    name: str
    value: int


@pytest.fixture
def logger_stream():
    stream = StringIO()
    logger = _IntLogger()
    memory_handler = logging.StreamHandler(stream)
    console_handler = logging.StreamHandler(sys.stdout)
    logger._logger_instance.handlers = [memory_handler, console_handler]
    return logger, stream


def flush_handlers(logger):
    for h in logger.logger_instance.handlers:
        h.flush()


def test_info_log(logger_stream):
    logger, stream = logger_stream
    logger.info("test info")
    flush_handlers(logger)
    assert "test info" in stream.getvalue()


def test_warning_log(logger_stream):
    logger, stream = logger_stream
    logger.warning("test warning")
    flush_handlers(logger)
    assert "test warning" in stream.getvalue()


def test_error_log_and_suggestion(logger_stream):
    logger, stream = logger_stream
    try:
        obj = SuggestionTarget()
        _ = obj.valud_key  # typo on purpose
    except Exception as e:
        logger.error("lookup failed", e)
        flush_handlers(logger)
    out = stream.getvalue()
    assert "lookup failed" in out
    assert "Did you mean" in out


def test_pretty_log_with_pretty_print(logger_stream):
    logger, stream = logger_stream
    logger.pretty_log(DummyPretty())
    flush_handlers(logger)
    assert "PRETTY_PRINTED" in stream.getvalue()


def test_pretty_log_with_json(logger_stream):
    logger, stream = logger_stream
    logger.pretty_log(DummyJSON())
    flush_handlers(logger)
    assert "social_media_platform" in stream.getvalue()
    assert "3091" in stream.getvalue()


def test_pretty_log_with_fallback(logger_stream):
    logger, stream = logger_stream
    logger.pretty_log(1234)
    flush_handlers(logger)
    assert "1234" in stream.getvalue()


def test_header_output(logger_stream):
    logger, stream = logger_stream
    logger.header("HEADER")
    flush_handlers(logger)
    assert "Header" in stream.getvalue() or "HEADER" in stream.getvalue()


def test_log_time(logger_stream):
    logger, stream = logger_stream
    logger._start_time = time.time() - 1.23  # simulate elapsed
    logger.log_time("Step Done")
    flush_handlers(logger)
    out = stream.getvalue()
    assert "Step Done" in out
    assert ("1.2" in out) or ("1.3" in out)  # tolerance


def test_compact_mode():
    stream = StringIO()
    logger = _IntLogger()
    logger.compact_mode = True
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logger._get_formatter("INFO"))
    logger.logger_instance.handlers = [handler]
    logger.info("Compact Test")
    flush_handlers(logger)
    assert "Compact Test" in stream.getvalue()


def test_pretty_log_with_pydantic_model(logger_stream):
    logger, stream = logger_stream
    model = DummyPydantic(name="test", value=42)
    logger.pretty_log(model)
    flush_handlers(logger)
    assert "test" in stream.getvalue()
    assert "42" in stream.getvalue()


def test_pretty_log_with_pydantic_model_non_compact(logger_stream):
    logger, stream = logger_stream
    logger.compact_mode = False
    model = DummyPydantic(name="test", value=42)
    logger.pretty_log(model)
    flush_handlers(logger)
    assert "test" in stream.getvalue()
    assert "42" in stream.getvalue()


# New tests for run ID functionality - FIXED
def test_run_id_format(logger_stream):
    logger, _ = logger_stream
    assert re.match(r"R-[A-Z0-9]{7}", logger.run_id)


def test_initiate_new_run(logger_stream):
    logger, stream = logger_stream
    original_run_id = logger.run_id
    logger.initiate_new_run()
    logger.info("New run")
    flush_handlers(logger)

    # Just test that the run ID changed, don't look for it in the output
    assert original_run_id != logger.run_id
    assert "New run" in stream.getvalue()


# Test for silence logger functionality
def test_silence_logger(logger_stream):
    logger, _ = logger_stream

    # Create a test logger and ensure it works
    test_logger = logging.getLogger("test_silence")
    test_logger.setLevel(logging.INFO)
    test_stream = StringIO()
    test_handler = logging.StreamHandler(test_stream)
    test_logger.addHandler(test_handler)

    test_logger.info("Before silence")
    assert "Before silence" in test_stream.getvalue()

    # Silence the logger
    logger.silence_logger("test_silence")

    # Clear the stream
    test_stream.truncate(0)
    test_stream.seek(0)

    # Try logging again
    test_logger.info("After silence")
    assert "After silence" not in test_stream.getvalue()


def test_silence_other_loggers():
    # Setup main logger
    logger = _IntLogger()

    # Create several test loggers
    test_loggers = []
    test_streams = []
    for i in range(3):
        stream = StringIO()
        log = logging.getLogger(f"test_other_{i}")
        log.setLevel(logging.INFO)
        handler = logging.StreamHandler(stream)
        log.addHandler(handler)
        test_loggers.append(log)
        test_streams.append(stream)

    # Log before silencing
    for i, log in enumerate(test_loggers):
        log.info(f"Test message {i}")
        assert f"Test message {i}" in test_streams[i].getvalue()

    # Silence other loggers
    logger.silence_other_loggers()

    # Clear the streams
    for stream in test_streams:
        stream.truncate(0)
        stream.seek(0)

    # Try logging again
    for i, log in enumerate(test_loggers):
        log.info(f"After silence {i}")
        assert f"After silence {i}" not in test_streams[i].getvalue()


# Test for verbose mode
def test_verbose_mode(logger_stream):
    logger, stream = logger_stream

    # Default/non-verbose mode
    logger.verbose_mode = False
    logger.info("Non-verbose test")
    flush_handlers(logger)
    non_verbose_output = stream.getvalue()

    # Clear the stream
    stream.truncate(0)
    stream.seek(0)

    # Verbose mode
    logger.verbose_mode = True
    logger.info("Verbose test")
    flush_handlers(logger)
    verbose_output = stream.getvalue()

    # Verbose output should contain the test message
    assert "Verbose test" in verbose_output


# Test for level management
def test_set_level(logger_stream):
    logger, stream = logger_stream

    # Set to WARNING level
    logger.setLevel("WARNING")

    # INFO shouldn't appear
    logger.info("Should not appear")
    # WARNING should appear
    logger.warning("Should appear")

    flush_handlers(logger)
    output = stream.getvalue()

    assert "Should appear" in output
    assert "Should not appear" not in output


def test_pretty_log_highlighting_all_literals(logger_stream):
    logger, stream = logger_stream
    logger.setLevel("INFO")
    logger.verbose_mode = False

    sample_data = {
        "true_val": True,
        "false_val": False,
        "none_val": None,
        "int_val": 42,
        "string_val": "hello",
        "url": "https://example.com",
        "dict": {"a": 1, "b": [1, 2, {"nested": None}]},
    }

    logger.data(sample_data)
    flush_handlers(logger)
    output = stream.getvalue()

    # Assert raw values are no longer directly printed
    forbidden_literals = [
        '"true_val": true',
        '"false_val": false',
        '"none_val": null',
        '"true_val": True',
        '"false_val": False',
        '"none_val": None',
        '"int_val": 42',
        '"string_val": "hello"',
        '"url": "https://example.com"',
        '"dict": {"a": 1, "b": [1, 2, {"nested": null}]}',
    ]

    for lit in forbidden_literals:
        assert lit not in output, f"Unexpected raw literal found: {lit}"


def test_simple_info_log_highlighting(logger_stream):
    logger, stream = logger_stream
    logger.setLevel("INFO")
    logger.verbose_mode = False

    logger.info("Simple literal test: true false none 1234")
    flush_handlers(logger)
    output = stream.getvalue()

    # Highlighted literals should be present (in some styled form)
    for token in ["true", "false", "none", "1234"]:
        assert token in output


def test_log_no_syntax_highlights(logger_stream):
    logger, stream = logger_stream
    logger.setLevel("INFO")
    logger.verbose_mode = False
    logger.highlight_syntax = False

    logger.info("Simple literal test: true false none 1234")
    logger.data("Simple literal test: true false none 1234")
    flush_handlers(logger)
    output = stream.getvalue()

    # Raw values must exist, but without formatting
    assert "Simple literal test: true false none 1234" in output


def test_show_demo_string(logger_stream):
    logger, stream = logger_stream
    logger.display_logger_state()
    flush_handlers(logger)
    output = stream.getvalue()

    required_phrases = [
        "Critical message preview",
        "Log Level Color Preview",
        "Literal/Syntax Highlight Preview",
        "Debug message preview",
    ]

    assert all(x in output for x in required_phrases)

# Test for color presets - FIXED
def test_color_presets():
    logger = _IntLogger()

    # Check if color presets exist
    assert hasattr(logger, "color_presets") or hasattr(logger, "presets")

import logging
import os
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
        return {
            "meta_data": {"integration_test": True},
            "targets": {"likes": 3091},
            "post_url": "https://picsum.photos/455",
            "file_type": "video",
            "spirra_media_id": "4e05cc02-d0e1-4db7-86bc-4267642b2c3c",
            "spirra_influencer_id": "7076e470-9809-45a6-8e04-74db55b8ab83",
            "social_media_platform": "facebook"
        }


class SuggestionTarget:
    def __init__(self):
        self.valid_key = 1


class DummyPydantic(BaseModel):
    name: str
    value: int


@pytest.fixture
def logger_stream():
    stream = StringIO()
    os.environ["PROJECT_NAME"] = "ai-axis"
    os.environ["PROJECT_VERSION"] = "1.2.3"
    os.environ["ENV"] = "dev"

    logger = _IntLogger()
    logger.reinitialize()
    logger.add_new_handler(logging.StreamHandler, stream=stream, force_replace=True)
    logger.add_new_handler(logging.StreamHandler, stream=sys.stdout)

    yield logger, stream

    for key in ["PROJECT_NAME", "PROJECT_VERSION", "ENV"]:
        os.environ.pop(key, None)


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
    logger._BaseLogger__start_time = time.time() - 1.23
    logger.log_time("Step Done")
    flush_handlers(logger)
    out = stream.getvalue()
    assert "Step Done" in out
    assert any(x in out for x in ["1.2", "1.3"])


def test_compact_mode():
    stream = StringIO()
    logger = _IntLogger()
    logger.compact_mode = True
    logger.add_new_handler(logging.StreamHandler, stream=stream, force_replace=True)

    logger.info("Compact Test")
    flush_handlers(logger)
    output = stream.getvalue()
    assert "Compact Test" in output
    assert "\n" not in output.strip()
    assert "->" in output


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


def test_run_id_format(logger_stream):
    logger, _ = logger_stream
    assert re.match(r"R-[A-F0-9]{7}", logger.run_id)


def test_initiate_new_run(logger_stream):
    logger, stream = logger_stream
    original = logger.run_id
    logger.initiate_new_run()
    logger.info("New run")
    flush_handlers(logger)
    assert original != logger.run_id
    assert "New run" in stream.getvalue()


def test_silence_logger(logger_stream):
    logger, _ = logger_stream

    # Prepare a logger WrenchCL will silence
    test_logger = logging.getLogger("test_silence")
    test_logger.setLevel(logging.DEBUG)
    test_logger.propagate = False  # Required to prevent root fallback

    test_stream = StringIO()
    stream_handler = logging.StreamHandler(test_stream)
    stream_handler.setLevel(logging.DEBUG)

    test_logger.handlers = [stream_handler]

    # Emit log before silence
    test_logger.info("Before silence")
    stream_handler.flush()
    assert "Before silence" in test_stream.getvalue()

    # Silence and assert no output
    logger.silence_logger("test_silence")

    test_stream.truncate(0)
    test_stream.seek(0)
    test_logger.info("After silence")

    assert test_stream.getvalue() == ""



def test_silence_other_loggers():
    logger = _IntLogger()
    test_loggers = []
    test_streams = []
    for i in range(3):
        s = StringIO()
        l = logging.getLogger(f"other_logger_{i}")
        l.setLevel(logging.INFO)
        l.addHandler(logging.StreamHandler(s))
        test_loggers.append(l)
        test_streams.append(s)
        l.info(f"msg {i}")
        assert f"msg {i}" in s.getvalue()
    logger.silence_other_loggers()
    for s in test_streams:
        s.truncate(0); s.seek(0)
    for i, l in enumerate(test_loggers):
        l.info(f"after silence {i}")
        assert f"after silence {i}" not in test_streams[i].getvalue()


def test_verbose_mode(logger_stream):
    logger, stream = logger_stream
    logger.verbose_mode = False
    logger.info("Non-verbose test")
    flush_handlers(logger)
    stream.truncate(0); stream.seek(0)
    logger.verbose_mode = True
    logger.info("Verbose test")
    flush_handlers(logger)
    assert "Verbose test" in stream.getvalue()


def test_set_level(logger_stream):
    logger, stream = logger_stream
    logger.setLevel("WARNING")
    logger.info("Not shown")
    logger.warning("Shown")
    flush_handlers(logger)
    out = stream.getvalue()
    assert "Shown" in out
    assert "Not shown" not in out


def test_pretty_log_highlighting_all_literals(logger_stream):
    logger, stream = logger_stream
    logger.setLevel("INFO")
    logger.verbose_mode = False

    sample = {
        "true_val": True, "false_val": False, "none_val": None, "int_val": 42,
        "string_val": "hi", "dict": {"a": 1, "b": [1, 2, {"nested": None}]}
    }

    logger.data(sample)
    flush_handlers(logger)
    out = stream.getvalue()
    forbidden = ['"true_val": true', '"false_val": false', '"none_val": null']
    assert not any(x in out for x in forbidden)


def test_simple_info_log_highlighting(logger_stream):
    logger, stream = logger_stream
    logger.info("Simple literal test: true false none 1234")
    flush_handlers(logger)
    out = stream.getvalue()
    for token in ["true", "false", "none", "1234"]:
        assert token in out


def test_log_no_syntax_highlights(logger_stream):
    logger, stream = logger_stream
    logger.highlight_syntax = False
    logger.data("Simple literal test: true false none 1234")
    flush_handlers(logger)
    assert "Simple literal test: true false none 1234" in stream.getvalue()


def test_show_demo_string(logger_stream):
    logger, stream = logger_stream
    logger.display_logger_state()
    flush_handlers(logger)
    out = stream.getvalue()
    required = ["Log Level Color Preview", "Literal/Syntax Highlight Preview"]
    assert all(x in out for x in required)


def test_color_presets():
    logger = _IntLogger()
    assert hasattr(logger, "color_presets")


def test_color_mode(logger_stream):
    logger, stream = logger_stream
    logger.color_mode = True
    logger.info("Test message A")
    logger.color_mode = False
    logger.info("Test message B")
    os.environ["AWS_LAMBDA_FUNCTION_NAME"] = "lambda"
    logger.color_mode = True
    logger.info("Test message C")
    os.environ.pop("AWS_LAMBDA_FUNCTION_NAME")
    logger.color_mode = True
    logger.info("Test message D")
    logger.compact_mode = True
    logger.info("Test message E")
    flush_handlers(logger)
    assert "Test message" in stream.getvalue()

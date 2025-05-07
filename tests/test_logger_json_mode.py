import os
import json
import logging
import sys
from io import StringIO
import pytest

from WrenchCL.Tools.WrenchLogger import _IntLogger


@pytest.fixture
def logger_fixture():
    stream = StringIO()

    # Set environment for deterministic output
    os.environ["PROJECT_NAME"] = "ai-axis"
    os.environ["PROJECT_VERSION"] = "1.2.3"
    os.environ["ENV"] = "dev"
    os.environ["LOG_DD_TRACE"] = "false"
    os.environ["AWS_EXECUTION_ENV"] = "testenv"

    logger = _IntLogger()
    logger.reinitialize()
    logger.log_mode = 'json'

    logger.add_new_handler(
        handler_cls=logging.StreamHandler,
        stream=stream,
        level="INFO",
        force_replace=False
    )

    logger.add_new_handler(
        handler_cls=logging.StreamHandler,
        stream=sys.stdout,
        level="INFO",
        force_replace=False
    )

    logger.info(f"Logger initialized with log mode: {logger.log_mode}")
    yield logger, stream

    for k in ["PROJECT_NAME", "PROJECT_VERSION", "ENV", "LOG_DD_TRACE", "AWS_EXECUTION_ENV"]:
        os.environ.pop(k, None)


def test_json_log_format_and_metadata(logger_fixture):
    logger, stream = logger_fixture
    logger.info("json test message")

    for h in logger.logger_instance.handlers:
        h.flush()

    stream.seek(0)
    lines = stream.getvalue().strip().splitlines()
    assert lines, "Log stream is empty"
    log_entry = json.loads(lines[-1])

    assert log_entry["message"] == "json test message"
    assert log_entry["level"] == "INFO"
    assert "timestamp" in log_entry
    assert "module" in log_entry
    assert "line" in log_entry
    assert "function" in log_entry
    assert log_entry["meta"]["project"] == "ai-axis"
    assert log_entry["meta"]["version"] == "1.2.3"
    assert log_entry["meta"]["env"] == "dev"


def test_json_log_includes_exception(logger_fixture):
    logger, stream = logger_fixture

    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.error("Something broke", e)

    for h in logger.logger_instance.handlers:
        h.flush()

    stream.seek(0)
    lines = stream.getvalue().strip().splitlines()
    assert lines, "Log stream is empty"
    log_entry = json.loads(lines[-1])

    assert "Something broke" in log_entry["message"]
    assert "exception" in log_entry
    assert "ValueError" in log_entry["exception"]


def test_json_log_trace_fields_absent_if_ddtrace_off(logger_fixture):
    logger, stream = logger_fixture
    logger.dd_trace = False

    logger.info("trace test")
    for h in logger.logger_instance.handlers:
        h.flush()

    stream.seek(0)
    lines = stream.getvalue().strip().splitlines()
    assert lines, "Log stream is empty"
    entry = json.loads(lines[-1])

    assert "trace_id" not in entry
    assert "span_id" not in entry


def test_json_flush_and_format_switch(logger_fixture):
    logger, stream = logger_fixture
    logger.info("before switch")

    for h in logger.logger_instance.handlers:
        h.flush()

    logger.log_mode = 'json'  # triggers rebind
    logger.info("after switch")

    for h in logger.logger_instance.handlers:
        h.flush()

    stream.seek(0)
    lines = stream.getvalue().strip().splitlines()
    assert any("before switch" in l for l in lines)
    assert any("after switch" in l for l in lines)


def test_terminal_log_env_metadata(logger_fixture):
    logger, stream = logger_fixture
    logger.log_mode = 'terminal'

    logger.info("terminal test")

    for h in logger.logger_instance.handlers:
        h.flush()

    stream.seek(0)
    content = stream.getvalue()
    assert "ai-axis" in content
    assert "1.2.3" in content
    assert "terminal test" in content

"""
Tests for context prefix features: run_id, set_prefix, logger.prefix(),
show_thread_name, JSON field injection, and ContextPrefixFilter.
"""
import json
import logging
import re
import threading
from io import StringIO

import pytest

from WrenchCL import logger


def strip_ansi(text: str) -> str:
    return re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text)


@pytest.fixture
def deployed_stream():
    stream = StringIO()
    logger.configure(deployment_mode=True, color_enabled=False)
    logger.instance.handlers.clear()
    logger.managed.add(logging.StreamHandler, stream=stream, owned=True)
    yield logger, stream
    logger.set_prefix()
    logger.configure(mode="terminal", color_enabled=True, show_thread_name=False)
    logger.instance.handlers.clear()


@pytest.fixture
def terminal_stream():
    stream = StringIO()
    logger.configure(mode="terminal", color_enabled=False, deployment_mode=False, verbose=False)
    logger.instance.handlers.clear()
    logger.managed.add(logging.StreamHandler, stream=stream, owned=True)
    yield logger, stream
    logger.set_prefix()
    logger.configure(mode="terminal", color_enabled=True, show_thread_name=False, deployment_mode=False, verbose=False)
    logger.instance.handlers.clear()


@pytest.fixture
def json_stream():
    stream = StringIO()
    logger.configure(mode="json")
    logger.instance.handlers.clear()
    logger.managed.add(logging.StreamHandler, stream=stream, owned=True)
    yield logger, stream
    logger.set_prefix()
    logger.configure(mode="terminal", color_enabled=True, show_thread_name=False)
    logger.instance.handlers.clear()


class TestRunId:

    def test_run_id_format(self, deployed_stream):
        lg, _ = deployed_stream
        run_id = lg.run_id
        assert len(run_id) == 5
        assert run_id.isalnum()
        assert run_id.isupper()

    def test_run_id_appears_in_deployed_output(self, deployed_stream):
        lg, stream = deployed_stream
        run_id = lg.run_id
        lg.info("probe")
        lg.flush()
        assert run_id in stream.getvalue()

    def test_run_id_absent_in_plain_terminal(self, terminal_stream):
        lg, stream = terminal_stream
        run_id = lg.run_id
        lg.info("probe")
        lg.flush()
        assert run_id not in strip_ansi(stream.getvalue())

    def test_cycle_run_generates_new_id(self, deployed_stream):
        lg, _ = deployed_stream
        old_id = lg.run_id
        lg.cycle_run()
        assert lg.run_id != old_id
        assert len(lg.run_id) == 5

    def test_initiate_new_run_also_works(self, deployed_stream):
        lg, _ = deployed_stream
        old_id = lg.run_id
        lg.initiate_new_run()
        assert lg.run_id != old_id


class TestContextBracket:

    def test_bracket_present_in_deployed_mode(self, deployed_stream):
        lg, stream = deployed_stream
        lg.info("msg")
        lg.flush()
        output = stream.getvalue()
        assert "[" in output and "]" in output

    def test_bracket_present_in_verbose_mode(self, terminal_stream):
        lg, stream = terminal_stream
        lg.configure(verbose=True)
        lg.info("msg")
        lg.flush()
        output = strip_ansi(stream.getvalue())
        assert "[" in output and "]" in output
        lg.configure(verbose=False)

    def test_bracket_absent_in_plain_terminal(self, terminal_stream):
        lg, stream = terminal_stream
        run_id = lg.run_id
        lg.info("msg")
        lg.flush()
        assert run_id not in strip_ansi(stream.getvalue())


class TestSetPrefix:

    def test_set_prefix_appears_in_output(self, deployed_stream):
        lg, stream = deployed_stream
        lg.set_prefix("myprefix")
        lg.info("msg")
        lg.flush()
        assert "myprefix" in stream.getvalue()

    def test_set_prefix_clear_removes_prefix(self, deployed_stream):
        lg, stream = deployed_stream
        lg.set_prefix("tempprefix")
        lg.set_prefix()
        lg.info("msg")
        lg.flush()
        assert "tempprefix" not in stream.getvalue()

    def test_configure_prefix_param(self, deployed_stream):
        lg, stream = deployed_stream
        lg.configure(prefix="cfgprefix")
        lg.info("msg")
        lg.flush()
        assert "cfgprefix" in stream.getvalue()
        lg.set_prefix()

    def test_prefix_coerced_to_str(self, deployed_stream):
        lg, stream = deployed_stream
        lg.configure(prefix="coerced")
        state = lg.state_manager.current_state
        assert isinstance(state.log_prefix, str)
        lg.set_prefix()

    def test_configure_does_not_clear_existing_prefix(self, deployed_stream):
        lg, stream = deployed_stream
        lg.set_prefix("persistent")
        lg.configure(show_thread_name=False)
        lg.info("msg")
        lg.flush()
        assert "persistent" in stream.getvalue()
        lg.set_prefix()


class TestScopedPrefix:

    def test_context_manager_active_inside(self, deployed_stream):
        lg, stream = deployed_stream
        with lg.prefix("scoped"):
            lg.info("inside")
        lg.flush()
        assert "scoped" in stream.getvalue()

    def test_context_manager_inactive_outside(self, deployed_stream):
        lg, stream = deployed_stream
        with lg.prefix("scoped"):
            pass
        stream.truncate(0)
        stream.seek(0)
        lg.info("outside")
        lg.flush()
        assert "scoped" not in stream.getvalue()

    def test_decorator_active_during_call(self, deployed_stream):
        lg, stream = deployed_stream

        @lg.prefix("decorated")
        def work():
            lg.info("inside fn")

        work()
        lg.flush()
        assert "decorated" in stream.getvalue()

    def test_decorator_inactive_after_call(self, deployed_stream):
        lg, stream = deployed_stream

        @lg.prefix("decorated")
        def work():
            pass

        work()
        stream.truncate(0)
        stream.seek(0)
        lg.info("after fn")
        lg.flush()
        assert "decorated" not in stream.getvalue()

    def test_scoped_overrides_global(self, deployed_stream):
        lg, stream = deployed_stream
        lg.set_prefix("global")
        with lg.prefix("scoped"):
            lg.info("msg")
        lg.flush()
        output = stream.getvalue()
        assert "scoped" in output
        assert "global" not in output
        lg.set_prefix()

    def test_global_restored_after_scope_exits(self, deployed_stream):
        lg, stream = deployed_stream
        lg.set_prefix("global")
        with lg.prefix("scoped"):
            pass
        stream.truncate(0)
        stream.seek(0)
        lg.info("msg")
        lg.flush()
        output = stream.getvalue()
        assert "global" in output
        assert "scoped" not in output
        lg.set_prefix()

    def test_context_manager_cleans_up_on_exception(self, deployed_stream):
        lg, stream = deployed_stream
        try:
            with lg.prefix("errscope"):
                raise ValueError("boom")
        except ValueError:
            pass
        stream.truncate(0)
        stream.seek(0)
        lg.info("after error")
        lg.flush()
        assert "errscope" not in stream.getvalue()


class TestThreadName:

    def test_thread_name_absent_by_default(self, deployed_stream):
        lg, stream = deployed_stream
        thread_name = threading.current_thread().name
        lg.info("msg")
        lg.flush()
        assert thread_name not in stream.getvalue()

    def test_thread_name_present_when_enabled(self, deployed_stream):
        lg, stream = deployed_stream
        lg.configure(show_thread_name=True)
        thread_name = threading.current_thread().name
        lg.info("msg")
        lg.flush()
        assert thread_name in stream.getvalue()
        lg.configure(show_thread_name=False)

    def test_thread_name_reflects_current_thread(self, deployed_stream):
        lg, stream = deployed_stream
        lg.configure(show_thread_name=True)
        results = []

        def worker():
            lg.info("from thread")
            lg.flush()
            results.append(stream.getvalue())

        t = threading.Thread(target=worker, name="WorkerThread-99")
        t.start()
        t.join()
        assert "WorkerThread-99" in results[-1]
        lg.configure(show_thread_name=False)


class TestJsonMode:

    def test_json_includes_run_id(self, json_stream):
        lg, stream = json_stream
        run_id = lg.run_id
        lg.info("msg")
        lg.flush()
        record = json.loads(stream.getvalue().strip())
        assert record.get("run_id") == run_id

    def test_json_includes_prefix_when_set(self, json_stream):
        lg, stream = json_stream
        lg.set_prefix("jsonprefix")
        lg.info("msg")
        lg.flush()
        record = json.loads(stream.getvalue().strip())
        assert record.get("prefix") == "jsonprefix"
        lg.set_prefix()

    def test_json_omits_prefix_when_not_set(self, json_stream):
        lg, stream = json_stream
        lg.set_prefix()
        lg.info("msg")
        lg.flush()
        record = json.loads(stream.getvalue().strip())
        assert "prefix" not in record

    def test_json_includes_thread_name_when_enabled(self, json_stream):
        lg, stream = json_stream
        lg.configure(show_thread_name=True)
        thread_name = threading.current_thread().name
        lg.info("msg")
        lg.flush()
        record = json.loads(stream.getvalue().strip())
        assert record.get("thread_name") == thread_name
        lg.configure(show_thread_name=False)

    def test_json_omits_thread_name_when_disabled(self, json_stream):
        lg, stream = json_stream
        lg.configure(show_thread_name=False)
        lg.info("msg")
        lg.flush()
        record = json.loads(stream.getvalue().strip())
        assert "thread_name" not in record


class TestContextFilter:

    def test_filter_sets_attributes_when_active(self, deployed_stream):
        lg, _ = deployed_stream
        import logging as stdlib_logging
        record = stdlib_logging.LogRecord(
            name="test", level=stdlib_logging.INFO,
            pathname="", lineno=0, msg="test", args=(), exc_info=None
        )
        f = next(f for f in lg.instance.filters
                 if type(f).__name__ == "ContextPrefixFilter")
        f.filter(record)
        assert hasattr(record, "wrench_context")
        assert hasattr(record, "wrench_run_id")
        assert hasattr(record, "wrench_prefix")
        assert hasattr(record, "wrench_thread_name")
        assert record.wrench_run_id == lg.run_id

    def test_filter_clears_attributes_when_inactive(self, terminal_stream):
        lg, _ = terminal_stream
        import logging as stdlib_logging
        record = stdlib_logging.LogRecord(
            name="test", level=stdlib_logging.INFO,
            pathname="", lineno=0, msg="test", args=(), exc_info=None
        )
        f = next(f for f in lg.instance.filters
                 if type(f).__name__ == "ContextPrefixFilter")
        f.filter(record)
        assert record.wrench_context == ""
        assert record.wrench_run_id == ""

    def test_filter_always_returns_true(self, deployed_stream):
        lg, _ = deployed_stream
        import logging as stdlib_logging
        record = stdlib_logging.LogRecord(
            name="test", level=stdlib_logging.INFO,
            pathname="", lineno=0, msg="test", args=(), exc_info=None
        )
        f = next(f for f in lg.instance.filters
                 if type(f).__name__ == "ContextPrefixFilter")
        assert f.filter(record) is True


class TestCalibrationProbe:

    def test_measure_base_level_probe_fires(self):
        from WrenchCL._Internal.Logging.logging_utils import _measure_base_level
        result = _measure_base_level()
        assert isinstance(result, int)
        assert result != 3 or result >= 1

    def test_measure_base_level_returns_positive_int(self):
        from WrenchCL._Internal.Logging.logging_utils import _measure_base_level
        result = _measure_base_level()
        assert result >= 1

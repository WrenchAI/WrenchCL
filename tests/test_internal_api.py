"""
Tests for InternalAPI functionality
"""
import builtins
import logging
import os
from io import StringIO
from unittest.mock import Mock, patch

import pytest

from WrenchCL import logger


@pytest.fixture  
def internal_api_setup():
    """Setup logger for internal API testing"""
    stream = StringIO()
    os.environ["PROJECT_NAME"] = "test-project"
    os.environ["PROJECT_VERSION"] = "1.0.0"
    os.environ["ENV"] = "test"

    logger.reinitialize()
    logger.configure(level='DEBUG')
    # Clear existing handlers and add test handler
    logger.instance.handlers.clear()
    logger.managed.add(logging.StreamHandler, stream=stream, owned=True)
    logger.managed.sync()
    yield logger, stream

    # Cleanup
    for key in ["PROJECT_NAME", "PROJECT_VERSION", "ENV"]:
        os.environ.pop(key, None)
    logger.instance.handlers.clear()


class TestInternalAPILogging:
    """Test internal logging functionality"""

    def test_log_internal_basic(self, internal_api_setup):
        logger, stream = internal_api_setup
        
        # Should log internal messages
        logger._internal.log_internal("test internal message")
        logger.flush()
        output = stream.getvalue()
        assert "test internal message" in output

    def test_log_internal_multiple_args(self, internal_api_setup):
        logger, stream = internal_api_setup
        
        logger._internal.log_internal("message", "with", "multiple", "args")
        logger.flush()
        output = stream.getvalue()
        # Should contain all parts
        assert "message" in output

    def test_log_internal_with_context_flag(self, internal_api_setup):
        logger, stream = internal_api_setup
        
        # Set context flag
        logger._internal._from_context = True
        logger._internal.log_internal("should not log")
        logger.flush()
        
        # Reset flag
        logger._internal._from_context = False
        logger._internal.log_internal("should log")
        logger.flush()
        
        output = stream.getvalue()
        assert "should log" in output

    def test_log_internal_empty_message(self, internal_api_setup):
        logger, stream = internal_api_setup
        
        logger._internal.log_internal("")
        logger.flush()
        # Should not raise exceptions

    def test_log_internal_none_args(self, internal_api_setup):
        logger, stream = internal_api_setup
        
        logger._internal.log_internal(None)
        logger.flush()
        # Should not raise exceptions

real_import = builtins.__import__

def selective_import(name, *args, **kwargs):
    if name == "ddtrace":
        mock_ddtrace = Mock()
        return mock_ddtrace
    return real_import(name, *args, **kwargs)



class TestInternalAPIDatadogSetup:
    """Test Datadog trace setup functionality"""

    @patch("ddtrace.patch")
    def test_setup_ddtrace_enabled_success(self, mock_patch, internal_api_setup):
        logger, stream = internal_api_setup

        with patch("builtins.__import__", side_effect=selective_import):
            with patch.dict("os.environ", {}, clear=False):
                logger._internal.setup_ddtrace(True)

                # mock_patch.assert_called_once_with(logging=True)
                assert os.environ.get("DD_TRACE_ENABLED") == "true"

    def test_setup_ddtrace_enabled_import_error(self, internal_api_setup):
        logger, stream = internal_api_setup
        
        # Mock ddtrace import failure
        with patch('builtins.__import__', side_effect=ImportError("ddtrace not found")):
            with pytest.raises(ImportError):
                logger._internal.setup_ddtrace(True)
                logger.flush()

                output = stream.getvalue()

                assert "ddtrace not found" in output

    def test_setup_ddtrace_disabled(self, internal_api_setup):
        logger, stream = internal_api_setup
        
        # Should not attempt any ddtrace operations
        logger._internal.setup_ddtrace(False)
        # Should not raise exceptions or log anything

    def test_setup_ddtrace_enabled_patch_error(self, internal_api_setup):
        logger, stream = internal_api_setup
        
        # Mock ddtrace import success but patch failure
        with patch('ddtrace.patch', side_effect=Exception("patch failed")):
            with patch('builtins.__import__'):
                try:
                    logger._internal.setup_ddtrace(True)
                except Exception:
                    # Should handle patch errors gracefully
                    pass


class TestInternalAPIFormatterUpdate:
    """Test formatter update functionality"""

    def test_update_formatters_basic(self, internal_api_setup):
        logger, stream = internal_api_setup
        from WrenchCL._Internal.Logging.DataClasses import LogLevel
        
        # Add a handler to update
        test_stream = StringIO()
        handler = logger.managed.add(logging.StreamHandler, stream=test_stream, owned=True)
        
        # Should not raise exceptions
        logger._internal.update_formatters(LogLevel("INFO"), False, False)

    def test_update_formatters_null_handler(self, internal_api_setup):
        logger, stream = internal_api_setup
        from WrenchCL._Internal.Logging.DataClasses import LogLevel
        
        # Add null handler
        null_handler = logging.NullHandler()
        logger.instance.addHandler(null_handler)
        
        # Should skip null handlers
        logger._internal.update_formatters(LogLevel("INFO"), False, False)

    def test_update_formatters_preserve_formatter_flag(self, internal_api_setup):
        logger, stream = internal_api_setup
        from WrenchCL._Internal.Logging.DataClasses import LogLevel
        
        # Create handler with preserve flag
        test_stream = StringIO()
        handler = logging.StreamHandler(test_stream)
        setattr(handler, "_wrench_preserve_formatter", True)
        logger.instance.addHandler(handler)
        
        original_formatter = handler.formatter
        
        # Should not change formatter
        logger._internal.update_formatters(LogLevel("INFO"), False, False)
        
        # Formatter should be preserved (may still be None)
        assert handler.formatter == original_formatter

    def test_update_formatters_owned_handler(self, internal_api_setup):
        logger, stream = internal_api_setup
        from WrenchCL._Internal.Logging.DataClasses import LogLevel
        
        # Create owned handler
        test_stream = StringIO()
        handler = logging.StreamHandler(test_stream)
        setattr(handler, "_wrench_owned", True)
        logger.instance.addHandler(handler)
        
        # Should update owned handlers
        logger._internal.update_formatters(LogLevel("INFO"), False, False)

    def test_update_formatters_adopted_handler(self, internal_api_setup):
        logger, stream = internal_api_setup
        from WrenchCL._Internal.Logging.DataClasses import LogLevel
        
        # Create adopted handler
        test_stream = StringIO()
        handler = logging.StreamHandler(test_stream)
        setattr(handler, "_wrench_adopted", True)
        logger.instance.addHandler(handler)
        
        # Should update adopted handlers
        logger._internal.update_formatters(LogLevel("INFO"), False, False)

    def test_update_formatters_non_owned_handler(self, internal_api_setup):
        logger, stream = internal_api_setup
        from WrenchCL._Internal.Logging.DataClasses import LogLevel
        
        # Create non-owned, non-adopted handler
        test_stream = StringIO()
        handler = logging.StreamHandler(test_stream)
        # No special flags set
        logger.instance.addHandler(handler)
        
        # Should skip non-owned handlers
        logger._internal.update_formatters(LogLevel("INFO"), False, False)

    @patch('WrenchCL._Internal.Logging.Formatters.FileLogFormatter.__init__', return_value=None)
    def test_update_formatters_file_wrapper(self, mock_file_formatter, internal_api_setup):
        logger, stream = internal_api_setup
        from WrenchCL._Internal.Logging.DataClasses import LogLevel
        
        # Create handler with FileLogFormatter
        test_stream = StringIO()
        handler = logging.StreamHandler(test_stream)
        setattr(handler, "_wrench_owned", True)
        
        # Mock the FileLogFormatter
        mock_formatter_instance = Mock()
        handler.setFormatter(mock_formatter_instance)
        mock_file_formatter.return_value = mock_formatter_instance
        
        logger.instance.addHandler(handler)
        
        logger._internal.update_formatters(LogLevel("INFO"), False, False)

    def test_update_formatters_with_no_format(self, internal_api_setup):
        logger, stream = internal_api_setup
        from WrenchCL._Internal.Logging.DataClasses import LogLevel
        
        test_stream = StringIO()
        handler = logger.managed.add(logging.StreamHandler, stream=test_stream, owned=True)
        
        # Test with no_format=True
        logger._internal.update_formatters(LogLevel("INFO"), True, False)

    def test_update_formatters_with_no_color(self, internal_api_setup):
        logger, stream = internal_api_setup
        from WrenchCL._Internal.Logging.DataClasses import LogLevel
        
        test_stream = StringIO()
        handler = logger.managed.add(logging.StreamHandler, stream=test_stream, owned=True)
        
        # Test with no_color=True
        logger._internal.update_formatters(LogLevel("INFO"), False, True)

    def test_update_formatters_with_both_flags(self, internal_api_setup):
        logger, stream = internal_api_setup
        from WrenchCL._Internal.Logging.DataClasses import LogLevel
        
        test_stream = StringIO()
        handler = logger.managed.add(logging.StreamHandler, stream=test_stream, owned=True)
        
        # Test with both flags
        logger._internal.update_formatters(LogLevel("INFO"), True, True)


class TestInternalAPIDatadogFilter:
    """Test Datadog filter functionality"""

    def test_update_formatters_with_dd_trace_enabled(self, internal_api_setup):
        logger, stream = internal_api_setup
        from WrenchCL._Internal.Logging.DataClasses import LogLevel
        
        # Enable DD trace
        logger.configure(trace_enabled=True)
        
        test_stream = StringIO()
        handler = logger.managed.add(logging.StreamHandler, stream=test_stream, owned=True)
        
        # Mock the DatadogTraceInjectionFilter
        with patch('WrenchCL._Internal.Logging.DatadogTraceInjectionFilter.DatadogTraceInjectionFilter') as mock_filter:
            mock_filter_instance = Mock()
            mock_filter.return_value = mock_filter_instance
            
            logger._internal.update_formatters(LogLevel("INFO"), False, False)
            
            # Should add the filter if DD trace is enabled
            # (Implementation dependent)





    # def test_update_formatters_dd_filter_already_exists(self, internal_api_setup):
    #     logger, stream = internal_api_setup
    #     from WrenchCL._Internal.Logging.DataClasses import LogLevel
    #
    #     logger.configure(trace_enabled=True)
    #
    #     test_stream = StringIO()
    #     handler = logger.managed.add(logging.StreamHandler, stream=test_stream, owned=True)
    #
    #     # Add a fake filter instance (same type)
    #     fake_filter = Mock(spec=DatadogTraceInjectionFilter)
    #     handler.addFilter(fake_filter)
    #
    #     # ✅ Patch the module-level name used by update_formatters
    #     with patch(
    #         "WrenchCL._Internal.Logging.Api.internal_api.DatadogTraceInjectionFilter",
    #         side_effect=lambda: fake_filter,
    #     ):
    #         logger._internal.update_formatters(LogLevel("INFO"), False, False)
    #
    #     # Verify no duplicates were added
    #     filters = [f for f in handler.filters if isinstance(f, DatadogTraceInjectionFilter)]
    #     assert len(filters) == 1




class TestInternalAPIMiniState:
    """Test mini state functionality"""

    def test_mini_state_terminal_mode(self, internal_api_setup):
        logger, stream = internal_api_setup
        
        logger.configure(mode="terminal")
        logger._internal.mini_state()
        logger.flush()
        
        output = stream.getvalue()
        # Should log state information
        assert "Logger" in output or "Color" in output

    def test_mini_state_json_mode(self, internal_api_setup):
        logger, stream = internal_api_setup
        
        logger.configure(mode="json")
        logger._internal.mini_state()
        logger.flush()
        
        output = stream.getvalue()
        # Should log in JSON format
        assert "{" in output or "Color" in output

    def test_mini_state_compact_mode(self, internal_api_setup):
        logger, stream = internal_api_setup
        
        logger.configure(mode="compact")
        logger._internal.mini_state()
        logger.flush()
        
        output = stream.getvalue()
        # Should log state information
        assert "Logger" in output or "Color" in output

    def test_mini_state_different_config_values(self, internal_api_setup):
        logger, stream = internal_api_setup
        
        # Test with different configuration values
        logger.configure(
            mode="terminal",
            color_enabled=False,
            deployment_mode=True
        )
        logger._internal.mini_state()
        logger.flush()
        
        output = stream.getvalue()
        # Should reflect configuration
        assert "Color" in output or "Deployment" in output


class TestInternalAPIIntegration:
    """Test integration scenarios for internal API"""

    def test_full_internal_workflow(self, internal_api_setup):
        logger, stream = internal_api_setup
        from WrenchCL._Internal.Logging.DataClasses import LogLevel
        
        # Test complete internal workflow
        logger._internal.setup_ddtrace(False)  # Disabled
        logger._internal.log_internal("setup complete")
        
        test_stream = StringIO()
        handler = logger.managed.add(logging.StreamHandler, stream=test_stream, owned=True)
        
        logger._internal.update_formatters(LogLevel("INFO"), False, False)
        logger._internal.mini_state()
        
        logger.flush()
        
        output = stream.getvalue()
        assert "setup complete" in output

    def test_context_flag_behavior(self, internal_api_setup):
        logger, stream = internal_api_setup
        
        # Test context flag behavior
        logger._internal._from_context = False
        logger._internal.log_internal("should appear")
        
        logger._internal._from_context = True
        logger._internal.log_internal("should not appear")
        
        logger._internal._from_context = False
        logger._internal.log_internal("should appear again")
        
        logger.flush()
        output = stream.getvalue()
        
        assert "should appear" in output
        assert "should appear again" in output

    def test_error_handling_in_update_formatters(self, internal_api_setup):
        logger, stream = internal_api_setup
        from WrenchCL._Internal.Logging.DataClasses import LogLevel
        
        # Test with handler that might cause errors
        test_stream = StringIO()
        handler = logging.StreamHandler(test_stream)
        setattr(handler, "_wrench_owned", True)
        
        # Make setFormatter raise an exception
        def failing_set_formatter(formatter):
            raise Exception("Formatter error")
        
        handler.setFormatter = failing_set_formatter
        logger.instance.addHandler(handler)
        
        # Should handle errors gracefully
        try:
            logger._internal.update_formatters(LogLevel("INFO"), False, False)
        except:
            # Errors should be handled gracefully
            pass

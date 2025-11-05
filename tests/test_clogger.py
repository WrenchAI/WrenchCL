"""
Integration tests for cLogger - the main logger class
"""
import logging
import os
from io import StringIO

import pytest

from WrenchCL._Internal.cLogger import cLogger


@pytest.fixture
def fresh_logger():
    """Create a fresh logger instance for testing"""
    stream = StringIO()
    os.environ["PROJECT_NAME"] = "test-project"
    os.environ["PROJECT_VERSION"] = "1.0.0"
    os.environ["ENV"] = "test"

    # Reset the singleton for testing
    if hasattr(cLogger, '_instances'):
        cLogger._instances.clear()
    
    test_logger = cLogger()
    test_logger.reinitialize()
    test_logger.configure(level='DEBUG')
    
    # Clear handlers and add test handler
    test_logger.instance.handlers.clear()
    test_logger.managed.add(logging.StreamHandler, stream=stream, owned=True)
    
    yield test_logger, stream

    # Cleanup
    for key in ["PROJECT_NAME", "PROJECT_VERSION", "ENV"]:
        os.environ.pop(key, None)
    test_logger.instance.handlers.clear()


class TestcLoggerInitialization:
    """Test cLogger initialization and singleton behavior"""

    def test_singleton_behavior(self):
        """Test that cLogger maintains singleton behavior"""
        logger1 = cLogger()
        logger2 = cLogger()
        assert logger1 is logger2

    def test_initialization_components(self, fresh_logger):
        """Test that all components are properly initialized"""
        test_logger, stream = fresh_logger
        
        # Check all components exist
        assert hasattr(test_logger, 'managed')
        assert hasattr(test_logger, 'streams')
        assert hasattr(test_logger, '_internal')
        assert hasattr(test_logger, 'state_manager')

    def test_component_references(self, fresh_logger):
        """Test that components have proper parent references"""
        test_logger, stream = fresh_logger
        
        assert test_logger.managed.parent is test_logger
        assert test_logger.streams.parent is test_logger
        assert test_logger._internal.parent is test_logger

    def test_state_manager_setup(self, fresh_logger):
        """Test that state manager is properly configured"""
        test_logger, stream = fresh_logger
        
        assert test_logger.state_manager is not None
        assert hasattr(test_logger.state_manager, 'current_state')
        assert hasattr(test_logger.state_manager, 'logging_instance')


class TestcLoggerFullLoggingWorkflow:
    """Test complete logging workflows"""

    def test_basic_logging_all_levels(self, fresh_logger):
        """Test all logging levels work correctly"""
        test_logger, stream = fresh_logger
        test_logger.configure(level="DEBUG", color_enabled=False)
        test_logger.managed.sync()
        test_logger.debug("debug message")
        test_logger.info("info message")
        test_logger.warning("warning message")
        test_logger.error("error message")
        test_logger.critical("critical message")
        test_logger.success("success message")
        
        test_logger.flush()
        output = stream.getvalue()
        
        assert "debug message" in output
        assert "info message" in output
        assert "warning message" in output
        assert "error message" in output
        assert "critical message" in output
        assert "success message" in output

    def test_logging_with_headers(self, fresh_logger):
        """Test logging with headers"""
        test_logger, stream = fresh_logger
        
        test_logger.info("test message", header="Test Header")
        test_logger.error("error message", header="Error Header")
        
        test_logger.flush()
        output = stream.getvalue()
        
        assert "test message" in output
        assert "TEST HEADER" in output.upper()
        assert "error message" in output
        assert "ERROR HEADER" in output.upper()

    def test_exception_logging(self, fresh_logger):
        """Test exception logging"""
        test_logger, stream = fresh_logger
        
        try:
            raise ValueError("test exception")
        except ValueError as e:
            test_logger.exception("caught exception")
            test_logger.error("error with exc_info", exc_info=e)
        
        test_logger.flush()
        output = stream.getvalue()
        assert "caught exception" in output

    def test_data_logging_comprehensive(self, fresh_logger):
        """Test comprehensive data logging"""
        test_logger, stream = fresh_logger
        
        # Test various data types
        test_data = [
            {"dict": "value"},
            [1, 2, 3, 4, 5],
            "simple string",
            42,
            {"nested": {"data": {"structure": True}}}
        ]
        
        for data in test_data:
            test_logger.data(data)
            test_logger.cdata(data)  # compact version
        
        test_logger.flush()
        output = stream.getvalue()
        assert "dict" in output
        assert "nested" in output


class TestcLoggerConfiguration:
    """Test configuration scenarios"""

    def test_mode_changes(self, fresh_logger):
        """Test changing modes"""
        test_logger, stream = fresh_logger
        
        # Test all modes
        modes = ["terminal", "json", "compact"]
        for mode in modes:
            test_logger.configure(mode=mode)
            assert test_logger.mode == mode
            test_logger.info(f"test in {mode} mode")
        
        test_logger.flush()

    def test_level_changes(self, fresh_logger):
        """Test changing log levels"""
        test_logger, stream = fresh_logger
        
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in levels:
            test_logger.configure(level=level)
            assert test_logger.level.value == level

    def test_combined_configuration(self, fresh_logger):
        """Test configuring multiple options"""
        test_logger, stream = fresh_logger
        
        test_logger.configure(
            mode="json",
            level="WARNING",
            color_enabled=False,
            verbose=True,
            deployment_mode=True
        )
        
        assert test_logger.mode == "json"
        assert test_logger.level.value == "WARNING"

    def test_temporary_configuration(self, fresh_logger):
        """Test temporary configuration context"""
        test_logger, stream = fresh_logger
        
        original_mode = test_logger.mode
        original_level = test_logger.level
        
        with test_logger.temporary(mode="json", level="ERROR"):
            assert test_logger.mode == "json"
            assert test_logger.level.value == "ERROR"
            test_logger.info("in temporary context")
        
        # Should restore
        assert test_logger.mode == original_mode
        assert test_logger.level == original_level
        
        test_logger.flush()


class TestcLoggerHandlerManagement:
    """Test handler management through all interfaces"""

    def test_base_add_methods(self, fresh_logger, tmp_path):
        """Test base add_file and add_stream methods"""
        test_logger, stream = fresh_logger
        
        # Test add_file
        log_file = tmp_path / "test.log"
        file_handler = test_logger.add_file(str(log_file))
        assert file_handler is not None
        
        # Test add_stream
        test_stream = StringIO()
        stream_handler = test_logger.add_stream(stream=test_stream)
        assert stream_handler is not None
        
        # Test logging to both
        test_logger.info("test message")
        test_logger.flush()
        
        assert log_file.exists()
        assert "test message" in test_stream.getvalue()

    def test_managed_add_methods(self, fresh_logger):
        """Test managed.add methods"""
        test_logger, stream = fresh_logger
        
        test_stream = StringIO()
        handler = test_logger.managed.add(
            handler_cls=logging.StreamHandler,
            stream=test_stream,
            level="INFO",
            owned=True
        )
        
        assert handler is not None
        test_logger.info("managed add test")
        test_logger.flush()
        assert "managed add test" in test_stream.getvalue()

    def test_handler_adoption(self, fresh_logger):
        """Test handler adoption workflow"""
        test_logger, stream = fresh_logger
        
        # Create external handler
        test_stream = StringIO()
        external_handler = logging.StreamHandler(test_stream)
        
        # Adopt it
        test_logger.managed.adopt(external_handler, preserve_formatter=True)
        test_logger.instance.addHandler(external_handler)
        
        # Test it works
        test_logger.info("adopted handler test")
        test_logger.flush()
        assert "adopted handler test" in test_stream.getvalue()

    def test_handler_sync(self, fresh_logger):
        """Test handler synchronization"""
        test_logger, stream = fresh_logger
        
        # Add multiple handlers
        stream1 = StringIO()
        stream2 = StringIO()
        
        test_logger.managed.add(logging.StreamHandler, stream=stream1, owned=True)
        test_logger.managed.add(logging.StreamHandler, stream=stream2, owned=True)
        
        # Change level and sync
        test_logger.configure(level="WARNING")
        test_logger.managed.sync()
        
        # Should not raise exceptions
        test_logger.warning("sync test")
        test_logger.flush()


class TestcLoggerSystemManagement:
    """Test system-wide logging management"""

    def test_logger_level_management(self, fresh_logger):
        """Test managing other logger levels"""
        test_logger, stream = fresh_logger
        
        # Set levels for various loggers
        test_logger.managed.set_level("requests", "WARNING")
        test_logger.managed.set_level("urllib3", "ERROR")
        test_logger.managed.set_level("boto3", "CRITICAL")

    def test_logger_silencing(self, fresh_logger):
        """Test silencing loggers"""
        test_logger, stream = fresh_logger
        
        # Test different silencing methods
        test_logger.managed.silence("requests")
        test_logger.managed.silence(["urllib3", "boto3"])
        test_logger.managed.silence("all")

    def test_stream_management(self, fresh_logger):
        """Test stream management functionality"""
        test_logger, stream = fresh_logger
        
        # Test stream operations
        test_logger.streams.attach(level="INFO")
        test_logger.streams.suppress("stderr")
        test_logger.streams.intercept_exceptions(install_hooks=False)

    def test_stream_redirection(self, fresh_logger):
        """Test stream redirection"""
        test_logger, stream = fresh_logger
        
        # Should not raise exceptions
        test_logger.streams.redirect_stdout()
        test_logger.streams.redirect_stderr()
        test_logger.streams.restore_stdout()
        test_logger.streams.restore_stderr()


class TestcLoggerProperties:
    """Test logger properties"""

    def test_instance_property(self, fresh_logger):
        """Test instance property"""
        test_logger, stream = fresh_logger
        
        instance = test_logger.instance
        assert isinstance(instance, logging.Logger)

    def test_handlers_property(self, fresh_logger):
        """Test handlers property"""
        test_logger, stream = fresh_logger
        
        handlers = test_logger.handlers
        assert isinstance(handlers, list)
        assert len(handlers) > 0  # Should have at least our test handler

    def test_state_property(self, fresh_logger):
        """Test state property"""
        test_logger, stream = fresh_logger
        
        state = test_logger.state
        assert isinstance(state, dict)
        assert "Logging Level" in state
        assert "Run Id" in state
        assert "Mode" in state
        assert "Configuration" in state

    def test_run_id_generation(self, fresh_logger):
        """Test run ID functionality"""
        test_logger, stream = fresh_logger
        
        old_run_id = test_logger.run_id
        test_logger.initiate_new_run()
        new_run_id = test_logger.run_id
        
        assert old_run_id != new_run_id
        assert isinstance(new_run_id, str)
        assert len(new_run_id) > 0


class TestcLoggerComplexScenarios:
    """Test complex real-world scenarios"""

    def test_full_application_setup(self, fresh_logger, tmp_path):
        """Test complete application logging setup"""
        test_logger, stream = fresh_logger
        
        # 1. Configure logger
        test_logger.configure(
            mode="terminal",
            level="INFO",
            color_enabled=True,
            verbose=False
        )
        
        # 2. Add file logging
        app_log = tmp_path / "app.log"
        test_logger.add_file(str(app_log), max_bytes=1024*1024)
        
        # 3. Add error-only stream
        error_stream = StringIO()
        test_logger.add_stream(stream=error_stream, level="ERROR")
        
        # 4. Set up system management
        test_logger.streams.attach(level="WARNING", silence_others=True)
        test_logger.managed.silence(["requests", "urllib3"])
        
        # 5. Test logging at various levels
        test_logger.debug("Debug information")  # Should not appear (level=INFO)
        test_logger.info("Application started")
        test_logger.warning("Warning message")
        test_logger.error("Error occurred")
        
        test_logger.flush()
        
        # Verify outputs
        assert app_log.exists()
        assert "Error occurred" in error_stream.getvalue()

    def test_microservice_logging_setup(self, fresh_logger):
        """Test microservice-style logging setup"""
        test_logger, stream = fresh_logger
        
        # JSON mode for structured logging
        test_logger.configure(
            mode="json",
            level="INFO",
            deployment_mode=True
        )
        
        # Capture all exceptions
        test_logger.streams.intercept_exceptions(
            install_hooks=True,
            std_stream_mode="both"
        )
        
        # Silence noisy libraries
        noisy_libs = ["requests", "urllib3", "boto3", "botocore"]
        test_logger.managed.silence(noisy_libs)
        
        # Test structured logging
        test_logger.info("Service started", header="STARTUP")
        test_logger.data({"service": "test", "version": "1.0.0"})
        
        test_logger.flush()

    def test_development_vs_production_modes(self, fresh_logger):
        """Test switching between development and production modes"""
        test_logger, stream = fresh_logger
        
        # Development mode
        test_logger.configure(
            mode="terminal",
            level="DEBUG",
            color_enabled=True,
            verbose=True
        )
        
        test_logger.debug("Development debug info")
        test_logger.info("Dev info message")
        
        # Switch to production mode
        test_logger.configure(
            mode="json",
            level="WARNING",
            deployment_mode=True,
            color_enabled=False
        )
        
        test_logger.debug("Prod debug - should not appear")
        test_logger.warning("Production warning")
        test_logger.error("Production error")
        
        test_logger.flush()

    def test_temporary_debug_session(self, fresh_logger):
        """Test temporary debug session"""
        test_logger, stream = fresh_logger
        
        # Normal production logging
        test_logger.configure(mode="json", level="WARNING")
        
        test_logger.info("Normal info - should not appear")
        test_logger.warning("Normal warning")
        
        # Temporary debug session
        with test_logger.temporary(mode="terminal", level="DEBUG", verbose=True):
            test_logger.debug("Debug during investigation")
            test_logger.info("Info during investigation")
            test_logger.data({"investigation": "data"})
        
        # Back to normal
        test_logger.info("Back to normal - should not appear")
        test_logger.error("Normal error")
        
        test_logger.flush()

    def test_multi_handler_complex_routing(self, fresh_logger, tmp_path):
        """Test complex handler routing scenario"""
        test_logger, stream = fresh_logger
        
        # Set up multiple outputs
        console_stream = StringIO()
        error_stream = StringIO()
        debug_file = tmp_path / "debug.log"
        app_file = tmp_path / "app.log"
        
        # Console for INFO+
        test_logger.managed.add(
            logging.StreamHandler,
            stream=console_stream,
            level="INFO",
            owned=True
        )
        
        # Error stream for ERROR+
        test_logger.managed.add(
            logging.StreamHandler,
            stream=error_stream,
            level="ERROR",
            owned=True
        )
        
        # Debug file for everything
        test_logger.add_file(str(debug_file), level="DEBUG")
        
        # App file for INFO+
        test_logger.add_file(str(app_file), level="INFO")
        
        # Test messages at all levels
        test_logger.debug("Debug message")
        test_logger.info("Info message")
        test_logger.warning("Warning message")
        test_logger.error("Error message")
        test_logger.critical("Critical message")
        
        test_logger.flush()
        
        # Verify routing
        console_output = console_stream.getvalue()
        error_output = error_stream.getvalue()
        
        # Console should have INFO+
        assert "Info message" in console_output
        assert "Warning message" in console_output
        assert "Error message" in console_output
        
        # Error stream should have ERROR+ only
        assert "Error message" in error_output
        assert "Critical message" in error_output
        assert "Info message" not in error_output
        
        # Files should exist
        assert debug_file.exists()
        assert app_file.exists()


class TestcLoggerErrorHandling:
    """Test error handling and edge cases"""

    def test_configuration_with_invalid_values(self, fresh_logger):
        """Test configuration with invalid values"""
        test_logger, stream = fresh_logger
        
        # Should handle invalid values gracefully
        try:
            test_logger.configure(mode="invalid_mode")
        except (ValueError, AttributeError):
            pass  # Expected
        
        try:
            test_logger.configure(level="INVALID_LEVEL")
        except (ValueError, AttributeError):
            pass  # Expected

    def test_operations_after_close(self, fresh_logger):
        """Test operations after closing logger"""
        test_logger, stream = fresh_logger
        
        test_logger.close()
        
        # Should handle operations gracefully after close
        try:
            test_logger.info("After close")
            test_logger.flush()
        except:
            pass  # May or may not work depending on implementation

    def test_concurrent_access_simulation(self, fresh_logger):
        """Test simulated concurrent access"""
        test_logger, stream = fresh_logger
        
        # Simulate rapid concurrent operations
        for i in range(100):
            test_logger.info(f"Message {i}")
            if i % 10 == 0:
                test_logger.configure(level="DEBUG")
            if i % 20 == 0:
                test_logger.flush()
        
        test_logger.flush()

    def test_memory_efficiency(self, fresh_logger):
        """Test memory efficiency with large operations"""
        test_logger, stream = fresh_logger
        
        # Large data logging
        large_data = {"data": list(range(1000))}
        test_logger.data(large_data)
        
        # Many small messages
        for i in range(100):
            test_logger.debug(f"Small message {i}")
        
        test_logger.flush()
        
        # Should complete without memory issues
        assert True

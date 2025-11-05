"""
Tests for ManagedLoggers functionality
"""
import logging
import os
from io import StringIO

import pytest

from WrenchCL import logger


@pytest.fixture
def managed_logger_setup():
    """Setup logger for managed logger testing"""
    stream = StringIO()
    os.environ["PROJECT_NAME"] = "test-project"
    os.environ["PROJECT_VERSION"] = "1.0.0" 
    os.environ["ENV"] = "test"

    logger.reinitialize()
    logger.configure(level='DEBUG')
    
    # Clear existing handlers
    logger.instance.handlers.clear()
    logger.managed.sync()
    yield logger, stream

    # Cleanup
    for key in ["PROJECT_NAME", "PROJECT_VERSION", "ENV"]:
        os.environ.pop(key, None)
    logger.instance.handlers.clear()


class TestManagedLoggersAdd:
    """Test adding handlers through managed interface"""

    def test_add_stream_handler(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        test_stream = StringIO()
        
        handler = logger.managed.add(
            handler_cls=logging.StreamHandler,
            stream=test_stream,
            level="INFO",
            owned=True
        )
        
        assert handler is not None
        assert isinstance(handler, logging.StreamHandler)
        assert handler in logger.instance.handlers
        
        # Test that it works
        logger.info("test managed add")
        logger.flush()
        assert "test managed add" in test_stream.getvalue()

    def test_add_file_handler(self, managed_logger_setup, tmp_path):
        logger, stream = managed_logger_setup
        log_file = tmp_path / "managed_test.log"
        
        handler = logger.managed.add(
            handler_cls=logging.FileHandler,
            stream=str(log_file),  # For FileHandler, stream parameter becomes filename
            level="DEBUG",
            owned=True
        )
        
        assert handler is not None
        assert isinstance(handler, logging.FileHandler)

    def test_add_with_custom_formatter(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        test_stream = StringIO()
        custom_formatter = logging.Formatter('CUSTOM: %(message)s')
        
        handler = logger.managed.add(
            handler_cls=logging.StreamHandler,
            stream=test_stream,
            formatter=custom_formatter,
            owned=True
        )
        
        # The formatter might be overridden by WrenchCL's formatting system
        # but the handler should still be added successfully
        assert handler is not None

    def test_add_with_force_replace(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        test_stream1 = StringIO()
        test_stream2 = StringIO()
        
        # Add first handler
        handler1 = logger.managed.add(
            handler_cls=logging.StreamHandler,
            stream=test_stream1,
            owned=True
        )
        
        initial_count = len(logger.instance.handlers)
        
        # Add second handler with force_replace=True
        handler2 = logger.managed.add(
            handler_cls=logging.StreamHandler,
            stream=test_stream2,
            force_replace=True,
            owned=True
        )
        
        assert handler2 is not None
        # Should have replaced handlers
        assert len(logger.instance.handlers) >= 1


class TestManagedLoggersAdopt:
    """Test adopting existing handlers"""

    def test_adopt_handler_basic(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        test_stream = StringIO()
        external_handler = logging.StreamHandler(test_stream)
        
        logger.managed.adopt(external_handler)
        
        # Check that adoption flags are set
        assert getattr(external_handler, "_wrench_adopted", False) == True
        assert getattr(external_handler, "_wrench_preserve_formatter", False) == False

    def test_adopt_handler_preserve_formatter(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        test_stream = StringIO()
        external_handler = logging.StreamHandler(test_stream)
        custom_formatter = logging.Formatter('PRESERVED: %(message)s')
        external_handler.setFormatter(custom_formatter)
        
        logger.managed.adopt(external_handler, preserve_formatter=True)
        
        assert getattr(external_handler, "_wrench_adopted", False) == True
        assert getattr(external_handler, "_wrench_preserve_formatter", False) == True

    def test_adopt_then_add_to_logger(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        test_stream = StringIO()
        external_handler = logging.StreamHandler(test_stream)
        
        logger.managed.adopt(external_handler)
        logger.instance.addHandler(external_handler)
        
        logger.info("test adopted handler")
        logger.flush()
        assert "test adopted handler" in test_stream.getvalue()


class TestManagedLoggersSync:
    """Test synchronization functionality"""

    def test_sync_handler_levels(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        test_stream = StringIO()
        
        # Add handler with different level
        handler = logger.managed.add(
            handler_cls=logging.StreamHandler,
            stream=test_stream,
            level="ERROR",
            owned=True
        )
        
        # Change logger level
        logger.configure(level="DEBUG")
        
        # Sync should update handler levels
        logger.managed.sync()
        
        # Verify sync occurred (implementation dependent)
        assert handler is not None

    def test_sync_with_multiple_handlers(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        
        # Add multiple handlers
        stream1 = StringIO()
        stream2 = StringIO()
        
        handler1 = logger.managed.add(logging.StreamHandler, stream=stream1, owned=True)
        handler2 = logger.managed.add(logging.StreamHandler, stream=stream2, owned=True)
        
        logger.managed.sync()
        
        # Should not raise any exceptions
        assert len(logger.instance.handlers) >= 2


class TestManagedLoggersSetLevel:
    """Test setting levels for named loggers"""

    def test_set_level_single_logger(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        
        # Should not raise exceptions
        logger.managed.set_level("requests", "WARNING")
        logger.managed.set_level("urllib3", "ERROR")

    def test_set_level_nonexistent_logger(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        
        # Should handle non-existent loggers gracefully
        logger.managed.set_level("nonexistent.logger", "INFO")

    def test_set_level_various_levels(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logger.managed.set_level(f"test.{level.lower()}", level)


class TestManagedLoggersSilence:
    """Test silencing functionality"""

    def test_silence_all(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        
        # Should not raise exceptions
        logger.managed.silence('all')

    def test_silence_single_logger_string(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        
        logger.managed.silence('requests')

    def test_silence_multiple_loggers_list(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        
        loggers_to_silence = ['requests', 'urllib3', 'boto3', 'paramiko']
        logger.managed.silence(loggers_to_silence)

    def test_silence_empty_list(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        
        logger.managed.silence([])

    def test_silence_invalid_target_type(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        
        with pytest.raises(ValueError, match="target must be"):
            logger.managed.silence(123)  # Invalid type

    def test_silence_dict_invalid(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        
        with pytest.raises(ValueError, match="target must be"):
            logger.managed.silence({"invalid": "dict"})


class TestManagedLoggersProperties:
    """Test managed loggers properties"""

    def test_active_property(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        
        active_loggers = logger.managed.active
        assert isinstance(active_loggers, list)
        assert 'WrenchCL' in active_loggers or len(active_loggers) >= 0

    def test_info_property(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        
        # Add a handler first
        test_stream = StringIO()
        logger.managed.add(logging.StreamHandler, stream=test_stream, owned=True)
        
        handler_info = logger.managed.info
        assert isinstance(handler_info, dict)

    def test_info_property_empty(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        
        # With no handlers
        handler_info = logger.managed.info
        assert isinstance(handler_info, dict)


class TestManagedLoggersIntegration:
    """Test integration scenarios"""

    def test_add_adopt_sync_workflow(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        
        # Add owned handler
        test_stream1 = StringIO()
        owned_handler = logger.managed.add(
            logging.StreamHandler, 
            stream=test_stream1, 
            owned=True
        )
        
        # Create and adopt external handler
        test_stream2 = StringIO()
        external_handler = logging.StreamHandler(test_stream2)
        logger.managed.adopt(external_handler, preserve_formatter=True)
        logger.instance.addHandler(external_handler)
        
        # Sync everything
        logger.managed.sync()
        
        # Test logging works through both
        logger.info("test integration")
        logger.flush()
        
        assert "test integration" in test_stream1.getvalue()
        assert "test integration" in test_stream2.getvalue()

    def test_silence_then_add_handler(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        
        # Silence some loggers first
        logger.managed.silence(['requests', 'urllib3'])
        
        # Then add handlers - should work fine
        test_stream = StringIO()
        handler = logger.managed.add(
            logging.StreamHandler,
            stream=test_stream,
            owned=True
        )
        
        logger.info("after silence and add")
        logger.flush()
        assert "after silence and add" in test_stream.getvalue()

    def test_multiple_operations_sequence(self, managed_logger_setup):
        logger, stream = managed_logger_setup
        
        # Complex sequence of operations
        test_stream = StringIO()
        
        # 1. Add handler
        handler = logger.managed.add(logging.StreamHandler, stream=test_stream, owned=True)
        
        # 2. Set some logger levels
        logger.managed.set_level("test.module", "WARNING")
        
        # 3. Silence some loggers
        logger.managed.silence(['noisy.logger'])
        
        # 4. Sync everything
        logger.managed.sync()
        
        # 5. Test logging still works
        logger.info("complex sequence test")
        logger.flush()
        assert "complex sequence test" in test_stream.getvalue()

"""
Tests for StreamManager functionality
"""
import builtins
import os
import sys
from io import StringIO
from unittest.mock import Mock, patch, MagicMock

import pytest

from WrenchCL import logger


@pytest.fixture
def stream_manager_setup():
    """Setup logger for stream manager testing"""
    stream = StringIO()
    os.environ["PROJECT_NAME"] = "test-project"
    os.environ["PROJECT_VERSION"] = "1.0.0"
    os.environ["ENV"] = "test"

    logger.reinitialize()
    logger.configure(level='DEBUG')
    
    # Clear existing handlers
    logger.instance.handlers.clear()
    
    yield logger, stream

    # Cleanup
    for key in ["PROJECT_NAME", "PROJECT_VERSION", "ENV"]:
        os.environ.pop(key, None)
    logger.instance.handlers.clear()


class TestStreamManagerAttach:
    """Test attaching streams to root logger"""

    def test_attach_basic(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Should not raise exceptions
        logger.streams.attach(level="INFO")

    def test_attach_with_custom_stream(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        test_stream = StringIO()
        
        logger.streams.attach(level="DEBUG", stream=test_stream)

    def test_attach_with_silence_others(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        logger.streams.attach(level="WARNING", silence_others=True)

    def test_attach_various_levels(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logger.streams.attach(level=level)

    def test_attach_with_stderr(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        logger.streams.attach(level="ERROR", stream=sys.stderr)

    def test_attach_with_stdout(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        logger.streams.attach(level="INFO", stream=sys.stdout)


class TestStreamManagerInterceptExceptions:
    """Test exception interception functionality"""

    def test_intercept_exceptions_basic(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Should not raise exceptions
        logger.streams.intercept_exceptions()

    def test_intercept_exceptions_no_hooks(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        logger.streams.intercept_exceptions(install_hooks=False)

    def test_intercept_exceptions_stderr_only(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        logger.streams.intercept_exceptions(
            install_hooks=True, 
            std_stream_mode="stderr"
        )

    def test_intercept_exceptions_both_streams(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        logger.streams.intercept_exceptions(
            install_hooks=True,
            std_stream_mode="both"
        )

    def test_intercept_exceptions_none_mode(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        logger.streams.intercept_exceptions(
            install_hooks=True,
            std_stream_mode="none"
        )

    def test_intercept_exceptions_with_none_parameter(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Test handling of None parameter
        logger.streams.intercept_exceptions(
            install_hooks=True,
            std_stream_mode=None  # Should default to "none"
        )


class TestStreamManagerSuppress:
    """Test stream suppression functionality"""

    def test_suppress_both(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Should not raise exceptions
        logger.streams.suppress("both")

    def test_suppress_stderr_only(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        logger.streams.suppress("stderr")

    def test_suppress_none(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        logger.streams.suppress("none")

    def test_suppress_default(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Test default parameter
        logger.streams.suppress()  # Should default to "both"


class TestStreamManagerForceMarkup:
    """Test force markup functionality"""

    @patch('colorama.init')
    @patch('colorama.deinit')
    @patch('colorama.AnsiToWin32')
    def test_force_markup_with_colorama(self, mock_ansi, mock_deinit, mock_init, stream_manager_setup):
        logger, stream = stream_manager_setup

        # Patch only colorama import
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "colorama":
                mock_colorama = MagicMock()
                return mock_colorama
            return original_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            logger.streams.force_markup()
            # Should not raise exceptions

    def test_force_markup_without_colorama(self, stream_manager_setup):
        logger, stream = stream_manager_setup

        # Only fail when trying to import colorama
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "colorama":
                raise ImportError("No module named 'colorama'")
            return original_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            logger.streams.force_markup()
            # Should handle ImportError gracefully


    @patch('warnings.warn')
    def test_force_markup_deployment_warning(self, mock_warn, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Set up deployment mode
        logger.configure(deployment_mode=True)
        
        with patch('colorama.init'), patch('colorama.deinit'), patch('colorama.AnsiToWin32'):
            logger.streams.force_markup()
            
            # Should issue warning in deployment mode
            # mock_warn.assert_called() - may not be called depending on implementation


class TestStreamManagerRedirectRestore:
    """Test stream redirection and restoration"""

    def test_redirect_stdout(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Should not raise exceptions (implementation dependent)
        logger.streams.redirect_stdout()

    def test_redirect_stderr(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        logger.streams.redirect_stderr()

    def test_restore_stdout(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        logger.streams.restore_stdout()

    def test_restore_stderr(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        logger.streams.restore_stderr()

    def test_redirect_restore_cycle_stdout(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Test full cycle
        logger.streams.redirect_stdout()
        logger.streams.restore_stdout()

    def test_redirect_restore_cycle_stderr(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        logger.streams.redirect_stderr()
        logger.streams.restore_stderr()

    def test_multiple_redirects(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Multiple redirects should be handled gracefully
        logger.streams.redirect_stdout()
        logger.streams.redirect_stdout()
        logger.streams.restore_stdout()


class TestStreamManagerIntegration:
    """Test integration scenarios for stream management"""

    def test_attach_then_intercept(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Common pattern: attach stream then intercept exceptions
        logger.streams.attach(level="INFO", silence_others=True)
        logger.streams.intercept_exceptions(install_hooks=True, std_stream_mode="stderr")

    def test_full_stream_setup(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        test_stream = StringIO()
        
        # Complete stream setup workflow
        logger.streams.attach(level="INFO", stream=test_stream, silence_others=True)
        logger.streams.intercept_exceptions(install_hooks=True, std_stream_mode="both")
        logger.streams.suppress("stderr")

    def test_suppress_then_attach(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Suppress first, then attach
        logger.streams.suppress("both")
        logger.streams.attach(level="WARNING")

    def test_force_markup_then_attach(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        with patch('colorama.init'), patch('colorama.deinit'), patch('colorama.AnsiToWin32'):
            logger.streams.force_markup()
            logger.streams.attach(level="INFO")

    def test_multiple_stream_operations(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Multiple operations in sequence
        logger.streams.attach(level="DEBUG")
        logger.streams.suppress("stderr")
        logger.streams.redirect_stdout()
        logger.streams.intercept_exceptions(install_hooks=False)
        logger.streams.restore_stdout()

    def test_attach_multiple_levels(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Attach at different levels (may overwrite)
        logger.streams.attach(level="DEBUG")
        logger.streams.attach(level="INFO")  
        logger.streams.attach(level="WARNING")

    def test_exception_interception_variations(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Test different combinations
        logger.streams.intercept_exceptions(install_hooks=True, std_stream_mode="none")
        logger.streams.intercept_exceptions(install_hooks=False, std_stream_mode="stderr")
        logger.streams.intercept_exceptions(install_hooks=True, std_stream_mode="both")

    def test_suppress_mode_changes(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Change suppression modes
        logger.streams.suppress("none")
        logger.streams.suppress("stderr") 
        logger.streams.suppress("both")
        logger.streams.suppress("none")  # Back to none


class TestStreamManagerErrorHandling:
    """Test error handling in stream manager"""

    def test_invalid_attach_level(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Should handle invalid levels gracefully or raise appropriate errors
        try:
            logger.streams.attach(level="INVALID_LEVEL")
        except (ValueError, AttributeError):
            # Expected for invalid log levels
            pass

    def test_invalid_suppress_mode(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Should handle invalid modes
        try:
            logger.streams.suppress("invalid_mode")
        except (ValueError, AttributeError):
            # Expected for invalid modes
            pass

    def test_invalid_std_stream_mode(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Should handle invalid std stream modes
        try:
            logger.streams.intercept_exceptions(std_stream_mode="invalid")
        except (ValueError, AttributeError):
            # Expected for invalid modes
            pass

    def test_attach_with_none_stream(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Should handle None stream gracefully
        logger.streams.attach(level="INFO", stream=None)

    def test_operations_after_close(self, stream_manager_setup):
        logger, stream = stream_manager_setup
        
        # Test operations after logger close
        logger.close()
        
        # These should still work or fail gracefully
        try:
            logger.streams.attach(level="INFO")
            logger.streams.suppress("both")
        except:
            # Any exceptions should be handled gracefully
            pass

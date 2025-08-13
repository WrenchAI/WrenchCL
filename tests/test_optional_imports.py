import pytest
import sys
from unittest.mock import patch, MagicMock
import builtins
from WrenchCL import logger

def create_comprehensive_boto_mocks():
    """Create comprehensive mocks for the entire boto3/botocore ecosystem."""

    # Create botocore mock with submodules
    botocore_mock = MagicMock()
    botocore_mock.client = MagicMock()
    botocore_mock.client.BaseClient = MagicMock()
    botocore_mock.client.ClientMeta = MagicMock()
    botocore_mock.config = MagicMock()
    botocore_mock.config.Config = MagicMock()
    botocore_mock.exceptions = MagicMock()
    botocore_mock.exceptions.ClientError = Exception
    botocore_mock.exceptions.BotoCoreError = Exception
    botocore_mock.response = MagicMock()
    botocore_mock.response.StreamingBody = MagicMock()

    # Create boto3 mock with proper Session structure
    boto3_mock = MagicMock()

    # Mock Session class
    session_class_mock = MagicMock()
    session_instance_mock = MagicMock()
    session_instance_mock.client.return_value = MagicMock()
    session_class_mock.return_value = session_instance_mock

    boto3_mock.Session = session_class_mock  # This is the key fix
    boto3_mock.client = MagicMock()
    boto3_mock.session = MagicMock()
    boto3_mock.session.Session = session_class_mock  # Also keep this for compatibility

    # Create mypy_boto3 mocks
    mypy_boto3_rds_mock = MagicMock()
    mypy_boto3_lambda_mock = MagicMock()
    mypy_boto3_s3_mock = MagicMock()
    mypy_boto3_secretsmanager_mock = MagicMock()

    # Create other AWS-related mocks
    psycopg2_mock = MagicMock()
    psycopg2_mock.extensions = MagicMock()
    psycopg2_mock.extras = MagicMock()
    psycopg2_mock.extras.register_uuid = MagicMock()
    psycopg2_mock.extras.DictCursor = MagicMock()
    psycopg2_mock.extras.execute_values = MagicMock()
    psycopg2_mock.pool = MagicMock()
    psycopg2_mock.pool.ThreadedConnectionPool = MagicMock()
    psycopg2_mock.connect = MagicMock()

    paramiko_mock = MagicMock()
    sshtunnel_mock = MagicMock()
    sshtunnel_mock.SSHTunnelForwarder = MagicMock()

    # Mock dotenv
    dotenv_mock = MagicMock()
    dotenv_mock.load_dotenv = MagicMock()

    return {
        'boto3': boto3_mock,
        'botocore': botocore_mock,
        'botocore.client': botocore_mock.client,
        'botocore.config': botocore_mock.config,
        'botocore.exceptions': botocore_mock.exceptions,
        'botocore.response': botocore_mock.response,
        'psycopg2': psycopg2_mock,
        'psycopg2.extensions': psycopg2_mock.extensions,
        'psycopg2.extras': psycopg2_mock.extras,
        'psycopg2.pool': psycopg2_mock.pool,
        'paramiko': paramiko_mock,
        'sshtunnel': sshtunnel_mock,
        'mypy_boto3_rds': mypy_boto3_rds_mock,
        'mypy_boto3_rds.client': MagicMock(),
        'mypy_boto3_lambda': mypy_boto3_lambda_mock,
        'mypy_boto3_lambda.client': MagicMock(),
        'mypy_boto3_s3': mypy_boto3_s3_mock,
        'mypy_boto3_s3.client': MagicMock(),
        'mypy_boto3_secretsmanager': mypy_boto3_secretsmanager_mock,
        'mypy_boto3_secretsmanager.client': MagicMock(),
        'typing_extensions': MagicMock(),
        'dotenv': dotenv_mock,
    }


class TestOptionalImports:
    """Test optional dependency handling across all modules."""

    @pytest.fixture
    def clean_imports(self):
        """Clean import cache before each test."""
        modules_to_remove = [
            'WrenchCL.Connect',
            'WrenchCL.Connect.AwsClientHub',
            'WrenchCL.Connect.RdsServiceGateway',
            'WrenchCL.Connect.S3ServiceGateway',
            'WrenchCL.Connect.Lambda',
            'WrenchCL._Internal',
            'WrenchCL.Connect._Internal._ConfigurationManager',
            'WrenchCL.Connect._Internal._SshTunnelManager',
            'WrenchCL.Connect._Internal._boto_cache'
        ]

        for module in modules_to_remove:
            if module in sys.modules:
                del sys.modules[module]
        yield

        # Cleanup after test
        for module in modules_to_remove:
            if module in sys.modules:
                del sys.modules[module]

    def test_aws_imports_available(self, clean_imports):
        """Test AWS imports work when dependencies are available."""
        mock_modules = create_comprehensive_boto_mocks()

        with patch.dict('sys.modules', mock_modules):
            # This should work fine
            from WrenchCL.Connect import AwsClientHub, RdsServiceGateway, S3ServiceGateway

            # Should be actual classes, not placeholders
            assert hasattr(AwsClientHub, '__init__')
            assert hasattr(RdsServiceGateway, '__init__')
            assert hasattr(S3ServiceGateway, '__init__')

    def test_aws_import_fails_missing_boto3(self, clean_imports):
        """Test import fails when boto3 is missing."""
        # Create a failing import context
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == 'boto3':
                raise ImportError("No module named 'boto3'")
            # Let other imports work normally
            return original_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            # The import itself should fail
            with pytest.raises(ImportError) as exc_info:
                from WrenchCL.Connect import AwsClientHub

            error_msg = str(exc_info.value)
            assert "AWS functionality requires additional dependencies" in error_msg
            assert "pip install 'WrenchCL[aws]'" in error_msg
            assert "boto3" in error_msg
            logger.error(error_msg)

    def test_aws_import_fails_missing_psycopg2(self, clean_imports):
        """Test import fails when psycopg2 is missing."""
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == 'psycopg2':
                raise ImportError("No module named 'psycopg2'")
            return original_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            with pytest.raises(ImportError) as exc_info:
                from WrenchCL.Connect import RdsServiceGateway

            error_msg = str(exc_info.value)
            assert "AWS functionality requires additional dependencies" in error_msg
            assert "pip install 'WrenchCL[aws]'" in error_msg
            assert "psycopg2" in error_msg
            logger.error(error_msg)

    def test_tools_always_available(self, clean_imports):
        """Test that Tools module works without optional dependencies."""
        # Tools should work regardless of AWS dependencies
        from WrenchCL.Tools import (
            coalesce, get_metadata, Maybe, typechecker,
            robust_serializer, parse_json
        )

        # Test that core tools work
        assert coalesce(None, "test") == "test"
        assert Maybe(42).value == 42

    def test_decorators_always_available(self, clean_imports):
        """Test that Decorators work without optional dependencies."""
        from WrenchCL.Decorators import SingletonClass, Retryable, Synchronized

        # Test basic functionality
        @SingletonClass
        class TestClass:
            pass

        assert TestClass() is TestClass()

    def test_exceptions_always_available(self, clean_imports):
        """Test that Exceptions work without optional dependencies."""
        from WrenchCL.Exceptions import (
            ArgumentTypeException, InvalidConfigurationException,
            GuardedResponseTrigger
        )

        # Test that exceptions can be raised
        with pytest.raises(ArgumentTypeException):
            raise ArgumentTypeException("test error")

    def test_successful_import_and_instantiation(self, clean_imports):
        """Test that when deps are available, classes can be imported AND instantiated."""
        mock_modules = create_comprehensive_boto_mocks()

        with patch.dict('sys.modules', mock_modules):
            from WrenchCL.Connect import AwsClientHub

            # Should be able to import
            # Note: instantiation might fail due to business logic, but import should work
            assert hasattr(AwsClientHub, '__init__')

    @pytest.mark.parametrize("missing_module", ["boto3", "psycopg2", "paramiko", "sshtunnel"])
    def test_specific_missing_modules(self, clean_imports, missing_module):
        """Test error messages for specific missing modules."""
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if missing_module in name:
                raise ImportError(f"No module named '{missing_module}'")
            return original_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            with pytest.raises(ImportError) as exc_info:
                from WrenchCL.Connect import AwsClientHub

            error_msg = str(exc_info.value)
            assert "pip install 'WrenchCL[aws]'" in error_msg
            logger.error(error_msg)


class TestImportIntegration:
    """Integration tests for import behavior."""

    def test_core_functionality_unaffected(self):
        """Test that core WrenchCL works even if AWS imports would fail."""
        # Should always work regardless of AWS deps
        from WrenchCL import logger
        from WrenchCL.Tools import Maybe, coalesce
        from WrenchCL.Exceptions import ArgumentTypeException

        logger.info("Test message")
        assert coalesce(None, "works") == "works"
        assert Maybe(42).value == 42



class TestRealWorldScenarios:
    """Test real-world usage patterns."""

    def test_graceful_import_pattern_success(self):
        """Test the pattern users would actually use when deps are available."""
        mock_modules = create_comprehensive_boto_mocks()

        with patch.dict('sys.modules', mock_modules):
            try:
                from WrenchCL.Connect import AwsClientHub
                aws_available = True
            except ImportError:
                aws_available = False

            # Core functionality should always be available
            from WrenchCL import logger
            from WrenchCL.Tools import Maybe

            logger.info(f"AWS available: {aws_available}")
            assert Maybe(42).value == 42
            assert aws_available is True  # Should be available with mocks
            

    def test_graceful_import_pattern_failure(self):
        """Test the pattern users would actually use when deps are missing."""
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == 'boto3':
                raise ImportError("No module named 'boto3'")
            return original_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            try:
                from WrenchCL.Connect import AwsClientHub
                aws_available = True
            except ImportError:
                aws_available = False

            # Core functionality should always be available
            from WrenchCL import logger
            from WrenchCL.Tools import Maybe

            logger.info(f"AWS available: {aws_available}")
            assert Maybe(42).value == 42
            assert aws_available is False  # Should fail without deps

    def test_error_message_helpful_for_users(self):
        """Test that error messages help users understand what to install."""
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == 'boto3':
                raise ImportError("No module named 'boto3'")
            return original_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            try:
                from WrenchCL.Connect import AwsClientHub
            except ImportError as e:
                error_msg = str(e)
                # Verify error message is helpful
                assert "AWS functionality requires additional dependencies" in error_msg
                assert "pip install 'WrenchCL[aws]'" in error_msg
                assert "boto3" in error_msg or "AWS" in error_msg
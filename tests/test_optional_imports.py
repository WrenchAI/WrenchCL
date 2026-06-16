import builtins
import sys
from unittest.mock import patch, MagicMock

import pytest

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

    boto3_mock.Session = session_class_mock
    boto3_mock.client = MagicMock()
    boto3_mock.session = MagicMock()
    boto3_mock.session.Session = session_class_mock

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
            'WrenchCL._Internal',
            'WrenchCL.Connect._Internal._ConfigurationManager',
            'WrenchCL.Connect._Internal._SshTunnelManager',
            'WrenchCL.Connect._Internal._boto_cache'
        ]
        for module in modules_to_remove:
            sys.modules.pop(module, None)
        yield
        for module in modules_to_remove:
            sys.modules.pop(module, None)

    def test_aws_imports_available(self, clean_imports):
        """Test AWS imports work when dependencies are available."""
        mock_modules = create_comprehensive_boto_mocks()

        with patch.dict('sys.modules', mock_modules):
            from WrenchCL.Connect import AwsClientHub, RdsServiceGateway, S3ServiceGateway

            assert hasattr(AwsClientHub, '__init__')
            assert hasattr(RdsServiceGateway, '__init__')
            assert hasattr(S3ServiceGateway, '__init__')

    def test_aws_import_fails_missing_boto3(self, clean_imports):
        """Test import fails when boto3 is missing."""
        import importlib.util as _iutil
        original_find_spec = _iutil.find_spec

        def mock_find_spec(name, *args, **kwargs):
            if name == 'boto3':
                return None
            return original_find_spec(name, *args, **kwargs)

        sys.modules.pop('boto3', None)
        with patch('importlib.util.find_spec', side_effect=mock_find_spec):
            with pytest.raises(ImportError) as exc_info:
                from WrenchCL.Connect import AwsClientHub

            error_msg = str(exc_info.value)
            assert "AWS functionality requires additional dependencies" in error_msg
            assert "pip install 'WrenchCL[aws]'" in error_msg
            assert "boto3" in error_msg
            logger.error(error_msg)

    def test_aws_import_fails_missing_psycopg2(self, clean_imports):
        """Test import fails when psycopg2 is missing."""
        import importlib.util as _iutil
        original_find_spec = _iutil.find_spec

        def mock_find_spec(name, *args, **kwargs):
            if 'psycopg2' in name:
                return None
            return original_find_spec(name, *args, **kwargs)

        sys.modules.pop('psycopg2', None)
        with patch('importlib.util.find_spec', side_effect=mock_find_spec):
            with pytest.raises(ImportError) as exc_info:
                from WrenchCL.Connect import AwsClientHub

            error_msg = str(exc_info.value)
            assert "AWS functionality requires additional dependencies" in error_msg
            assert "pip install 'WrenchCL[aws]'" in error_msg
            assert "psycopg2" in error_msg
            logger.error(error_msg)

    def test_tools_always_available(self, clean_imports):
        from WrenchCL.Tools import coalesce, Maybe
        assert coalesce(None, "test") == "test"
        assert Maybe(42).value == 42

    def test_decorators_always_available(self, clean_imports):
        from WrenchCL.Decorators import SingletonClass

        @SingletonClass
        class TestClass:
            pass

        assert TestClass() is TestClass()

    def test_exceptions_always_available(self, clean_imports):
        from WrenchCL.Exceptions import ArgumentTypeException
        with pytest.raises(ArgumentTypeException):
            raise ArgumentTypeException("test error")

    def test_successful_import_and_instantiation(self, clean_imports):
        mock_modules = create_comprehensive_boto_mocks()
        with patch.dict('sys.modules', mock_modules):
            from WrenchCL.Connect import AwsClientHub
            assert hasattr(AwsClientHub, '__init__')

    @pytest.mark.parametrize("missing_module", ["boto3", "psycopg2", "paramiko", "sshtunnel"])
    def test_specific_missing_modules(self, clean_imports, missing_module):
        import importlib.util as _iutil
        original_find_spec = _iutil.find_spec

        def mock_find_spec(name, *args, **kwargs):
            if missing_module in name:
                return None
            return original_find_spec(name, *args, **kwargs)

        sys.modules.pop(missing_module, None)
        with patch('importlib.util.find_spec', side_effect=mock_find_spec):
            with pytest.raises(ImportError) as exc_info:
                from WrenchCL.Connect import AwsClientHub

            error_msg = str(exc_info.value)
            assert "pip install 'WrenchCL[aws]'" in error_msg
            logger.error(error_msg)

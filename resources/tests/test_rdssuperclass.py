import pytest
from unittest.mock import MagicMock, patch
import psycopg2
import json

from WrenchCL.RdsSuperClass import RDS, SshTunnelManager


class MockSSHTunnelForwarder:
    def __init__(self, *args, **kwargs):
        self.local_bind_port = 5432  # Mocked port
        self._transport = MagicMock()  # Simulate the internal _transport
        self.start = MagicMock()  # Mock start method
        self.stop = MagicMock()  # Mock stop method

    def __enter__(self):
        return self  # Return the mock object itself

    def __exit__(self, exc_type, exc_value, traceback):
        pass  # Mock exit method for context management


class TestRDS:

    @pytest.fixture
    def rds_instance(self):
        return RDS()

    @pytest.fixture
    def mock_psycopg2_connect(self, mocker):
        return mocker.patch('psycopg2.connect')

    @pytest.fixture
    def mock_tunnel(self, mocker):
        mock_tunnel = MagicMock()
        mock_tunnel.local_bind_port = 5432
        mocker.patch('sshtunnel.SSHTunnelForwarder', return_value=mock_tunnel)
        return mock_tunnel

    def test_load_configuration(self, rds_instance):
        db_config = {'PGHOST': 'localhost', 'PGPORT': 5432}
        rds_instance.load_configuration(db_config)
        assert rds_instance.config == db_config

    def test_connect_with_ssh_tunnel(self, mocker):
        rds_instance = RDS()
        db_config = {
            'PGHOST': 'localhost',
            'PGPORT': 5432,
            'PGDATABASE': 'testdb',
            'PGUSER': 'masteruser',
            'PGPASSWORD': None,
            'SSH_TUNNEL': {
                'SSH_SERVER': 'ssh.example.com',
                'SSH_PORT': 22,
                'SSH_USER': 'user'
            }
        }
        rds_instance.load_configuration(db_config)

        mock_tunnel_forwarder_instance = MockSSHTunnelForwarder()

        # Mock SSHTunnelForwarder in the RDS class
        mock_tunnel_forwarder = mocker.patch('WrenchCL.RdsSuperClass.SSHTunnelForwarder',
                                             return_value=mock_tunnel_forwarder_instance)
        # Mock psycopg2.connect to return a MagicMock object
        mock_psycopg2_connect = mocker.patch('psycopg2.connect', return_value=MagicMock())

        rds_instance._connect()

        # Assertions
        mock_tunnel_forwarder.assert_called_once()
        mock_tunnel_forwarder_instance.start.assert_called_once()
        mock_psycopg2_connect.assert_called_once_with(
            host='127.0.0.1',
            port=5432,
            database='testdb',
            user='masteruser',
            password=None
        )

        # Check if the connection object is a mock (as expected)
        assert isinstance(rds_instance.connection, MagicMock)

    def test_connect_without_ssh_tunnel(self, rds_instance, mock_psycopg2_connect):
        db_config = {
            'PGHOST': 'localhost',
            'PGPORT': 5432,
            'PGDATABASE': 'testdb',
            'PGUSER': 'masteruser',
            'PGPASSWORD': None}

        rds_instance.load_configuration(db_config)
        rds_instance._connect()
        assert mock_psycopg2_connect.called

    def test_batch_add_query(self, rds_instance, mock_psycopg2_connect):
        rds_instance.connection = MagicMock()
        rds_instance.batch_add_query('SELECT 1')
        assert rds_instance.connection.cursor().execute.called

    def test_batch_execute_query_success(self, rds_instance, mock_psycopg2_connect):
        rds_instance.connection = MagicMock()
        assert rds_instance.batch_execute_query() != 'ERROR'

    def test_execute_query_connection_not_established(self, rds_instance):
        result = rds_instance.execute_query('SELECT 1')
        assert result is None

    def test_execute_query_success(self, rds_instance, mock_psycopg2_connect):
        rds_instance.connection = MagicMock()
        rds_instance.execute_query('SELECT 1')
        assert rds_instance.connection.cursor().execute.called

    def test_parse_to_json_none_result(self, rds_instance):
        rds_instance.result = None
        assert rds_instance.parse_to_json() is None

    def test_parse_to_dataframe_none_result(self, rds_instance):
        rds_instance.result = None
        assert rds_instance.parse_to_dataframe() is None

    def test_close_connection(self, rds_instance, mock_psycopg2_connect, mock_tunnel):
        rds_instance.connection = MagicMock()
        rds_instance.ssh_manager = MagicMock(spec=SshTunnelManager)
        rds_instance.close()
        assert rds_instance.connection.close.called
        assert rds_instance.ssh_manager.stop_tunnel.called

    def test_handle_special_types(self):
        with pytest.raises(TypeError):
            RDS._handle_special_types({})  # Test with an unserializable type

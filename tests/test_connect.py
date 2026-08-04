# tests/test_connect.py

from unittest.mock import MagicMock, PropertyMock, patch

import psycopg2
import pytest

try:
    from WrenchCL.Connect import AwsClientHub, RdsServiceGateway, S3ServiceGateway
except ImportError:
    AwsClientHub = None
    S3ServiceGateway = None
    RdsServiceGateway = None


# ─────────────────────────────────────────────────────────────
# AwsClientHub Tests
# ─────────────────────────────────────────────────────────────


@patch("WrenchCL.Connect.AwsClientHub._fetch_secret_from_secretsmanager")
@patch("WrenchCL.Connect.AwsClientHub._get_boto3_session")
@patch("WrenchCL.Connect.AwsClientHub._ConfigurationManager")
def test_aws_client_hub_initialization(mock_cfg_cls, mock_boto_session, mock_fetch_secret):
    mock_config = MagicMock()
    mock_config.secret_arn = "arn:aws:secretsmanager:us-east-1:123456:secret"
    mock_config.aws_profile = "test-profile"
    mock_config.region_name = "us-west-2"
    mock_config.construct_db_uri.return_value = "postgresql://u:p@h:5432/d"
    mock_cfg_cls.return_value = mock_config

    mock_fetch_secret.return_value = {
            "username": "u", "password": "p", "host": "h", "port": 5432, "dbname": "d"
            }

    hub = AwsClientHub(env_path=None, AWS_PROFILE="test-profile", SECRET_ARN="arn:aws:secretsmanager:us-east-1:123456:secret")
    assert hub.db_uri.startswith("postgresql://")
    assert hub.config.secret_arn == "arn:aws:secretsmanager:us-east-1:123456:secret"


@patch.object(AwsClientHub, "config", new_callable=PropertyMock)
@patch.object(AwsClientHub, "session", new_callable=PropertyMock)
def test_get_s3_client(mock_session_prop, mock_config_prop, ):
    # Config mock
    mock_config = MagicMock()
    mock_config.secret_arn = "arn"
    mock_config.aws_profile = "p"
    mock_config.region_name = "us-east-1"
    mock_config_prop.return_value = mock_config

    # Boto3 session and client mock
    mock_boto_client = MagicMock()
    mock_boto_session = MagicMock()
    mock_boto_session.client.return_value = mock_boto_client
    mock_session_prop.return_value = mock_boto_session

    hub = AwsClientHub(env_path=None, AWS_PROFILE="p", SECRET_ARN="arn")
    s3_client = hub.s3
    assert s3_client is mock_boto_client


# ─────────────────────────────────────────────────────────────
# RdsServiceGateway Tests
# ─────────────────────────────────────────────────────────────

from WrenchCL.Connect import RdsServiceGateway


@pytest.fixture(autouse=True)
def reset_rds_singleton():
    RdsServiceGateway._SingletonWrapper__cls_instance = None
    yield
    RdsServiceGateway._SingletonWrapper__cls_instance = None


def _mock_rds_hub(connection=None):
    mock_hub = MagicMock()
    mock_hub.config.db_batch_size = 100
    mock_hub.db_uri = "postgresql://u:p@h:5432/d"
    mock_hub.db = connection
    return mock_hub


@patch("WrenchCL.Connect.RdsServiceGateway.ThreadedConnectionPool")
@patch("WrenchCL.Connect.RdsServiceGateway.AwsClientHub")
def test_rds_multithreaded_connection(mock_hub_cls, mock_pool_cls):
    mock_hub = _mock_rds_hub()
    mock_hub_cls.return_value = mock_hub

    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [{"id": 1}]
    mock_conn.cursor.return_value = mock_cursor
    mock_pool.getconn.return_value = mock_conn
    mock_pool_cls.return_value = mock_pool

    svc = RdsServiceGateway(multithreaded=True)
    result = svc.get_data("SELECT * FROM foo", payload=None)
    assert result == [{"id": 1}]


@patch("WrenchCL.Connect.RdsServiceGateway.AwsClientHub")
def test_rds_update_tuple_commit(mock_hub_cls):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [{'id': 1}]

    mock_hub = _mock_rds_hub(mock_conn)
    mock_hub_cls.return_value = mock_hub

    svc = RdsServiceGateway(multithreaded=False)
    result = svc.update_database("UPDATE table SET x = %s", payload=("val",), returning=True)
    assert result == [{'id': 1}]


@patch("WrenchCL.Connect.RdsServiceGateway.psycopg2.connect")
@patch("WrenchCL.Connect.RdsServiceGateway.AwsClientHub")
def test_rds_single_reconnect_swaps_connection_and_skips_in_test_mode(mock_hub_cls, mock_connect):
    old_conn = MagicMock()
    new_conn = MagicMock()
    mock_hub_cls.return_value = _mock_rds_hub(old_conn)
    mock_connect.return_value = new_conn

    svc = RdsServiceGateway(multithreaded=False)
    svc.reconnect()

    assert svc.connection is new_conn
    old_conn.close.assert_called_once_with()
    mock_connect.assert_called_once_with("postgresql://u:p@h:5432/d")

    svc.set_test_mode(True)
    svc.reconnect()
    assert svc.connection is new_conn
    assert mock_connect.call_count == 1


def test_rds_connection_level_error_classification():
    assert RdsServiceGateway._is_connection_level_error(
        psycopg2.OperationalError("failed")
    )
    assert RdsServiceGateway._is_connection_level_error(psycopg2.InterfaceError("failed"))
    assert not RdsServiceGateway._is_connection_level_error(psycopg2.IntegrityError("failed"))
    assert RdsServiceGateway._is_connection_level_error(ValueError("connection already closed"))
    assert not RdsServiceGateway._is_connection_level_error(ValueError("unrelated failure"))


@patch("WrenchCL.Connect.RdsServiceGateway.psycopg2.connect")
@patch("WrenchCL.Connect.RdsServiceGateway.AwsClientHub")
def test_rds_single_get_data_reconnects_once(mock_hub_cls, mock_connect):
    old_conn = MagicMock()
    old_cursor = MagicMock()
    old_cursor.__enter__.return_value = old_cursor
    old_cursor.execute.side_effect = psycopg2.OperationalError("connection already closed")
    old_conn.cursor.return_value = old_cursor

    new_conn = MagicMock()
    new_cursor = MagicMock()
    new_cursor.__enter__.return_value = new_cursor
    new_cursor.fetchall.return_value = [{"id": 1}]
    new_conn.cursor.return_value = new_cursor

    mock_hub_cls.return_value = _mock_rds_hub(old_conn)
    mock_connect.return_value = new_conn

    svc = RdsServiceGateway(multithreaded=False)
    assert svc.get_data("SELECT * FROM foo", payload=None) == [{"id": 1}]

    mock_connect.assert_called_once_with("postgresql://u:p@h:5432/d")
    old_conn.rollback.assert_called_once_with()


@patch("WrenchCL.Connect.RdsServiceGateway.psycopg2.connect")
@patch("WrenchCL.Connect.RdsServiceGateway.AwsClientHub")
def test_rds_integrity_error_does_not_reconnect(mock_hub_cls, mock_connect):
    conn = MagicMock()
    cursor = MagicMock()
    cursor.__enter__.return_value = cursor
    cursor.execute.side_effect = psycopg2.IntegrityError("duplicate key")
    conn.cursor.return_value = cursor
    mock_hub_cls.return_value = _mock_rds_hub(conn)

    svc = RdsServiceGateway(multithreaded=False)
    assert svc.get_data("SELECT * FROM foo", payload=None) is None
    with pytest.raises(psycopg2.IntegrityError):
        svc.update_database("UPDATE foo SET x = %s", payload=("value",))
    mock_connect.assert_not_called()


@patch("WrenchCL.Connect.RdsServiceGateway.ThreadedConnectionPool")
@patch("WrenchCL.Connect.RdsServiceGateway.AwsClientHub")
def test_rds_pool_get_data_replaces_only_failed_connection(mock_hub_cls, mock_pool_cls):
    bad_conn = MagicMock()
    bad_cursor = MagicMock()
    bad_cursor.__enter__.return_value = bad_cursor
    bad_cursor.execute.side_effect = psycopg2.OperationalError("connection dropped")
    bad_conn.cursor.return_value = bad_cursor

    healthy_conn = MagicMock()
    healthy_cursor = MagicMock()
    healthy_cursor.__enter__.return_value = healthy_cursor
    healthy_cursor.fetchall.return_value = [{"id": 1}]
    healthy_conn.cursor.return_value = healthy_cursor

    mock_hub_cls.return_value = _mock_rds_hub()
    mock_pool = MagicMock()
    mock_pool.getconn.side_effect = [bad_conn, healthy_conn]
    mock_pool_cls.return_value = mock_pool

    svc = RdsServiceGateway(multithreaded=True)
    assert svc.get_data("SELECT * FROM foo", payload=None) == [{"id": 1}]

    assert mock_pool.getconn.call_count == 2
    mock_pool.putconn.assert_any_call(bad_conn, close=True)
    mock_pool.putconn.assert_any_call(healthy_conn, close=False)
    mock_pool.closeall.assert_not_called()


@patch("WrenchCL.Connect.RdsServiceGateway.ThreadedConnectionPool")
@patch("WrenchCL.Connect.RdsServiceGateway.AwsClientHub")
def test_rds_pool_get_data_returns_healthy_connection(mock_hub_cls, mock_pool_cls):
    healthy_conn = MagicMock()
    healthy_cursor = MagicMock()
    healthy_cursor.__enter__.return_value = healthy_cursor
    healthy_cursor.fetchall.return_value = [{"id": 1}]
    healthy_conn.cursor.return_value = healthy_cursor

    mock_hub_cls.return_value = _mock_rds_hub()
    mock_pool = MagicMock()
    mock_pool.getconn.return_value = healthy_conn
    mock_pool_cls.return_value = mock_pool

    svc = RdsServiceGateway(multithreaded=True)
    assert svc.get_data("SELECT * FROM foo", payload=None) == [{"id": 1}]

    mock_pool.putconn.assert_called_once_with(healthy_conn, close=False)
    mock_pool.closeall.assert_not_called()

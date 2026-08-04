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
def reset_rds_gateway_singleton():
    RdsServiceGateway._SingletonWrapper__cls_instance = None
    yield
    RdsServiceGateway._SingletonWrapper__cls_instance = None


@patch("WrenchCL.Connect.RdsServiceGateway.ThreadedConnectionPool")
@patch("WrenchCL.Connect.RdsServiceGateway.AwsClientHub")
def test_rds_multithreaded_connection(mock_hub_cls, mock_pool_cls):
    mock_hub = MagicMock()
    mock_hub.config.db_batch_size = 100
    mock_hub.db_uri = "postgresql://u:p@h:5432/d"
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

    mock_hub = MagicMock()
    mock_hub.db = mock_conn
    mock_hub.db_uri = "postgresql://..."
    mock_hub.config.db_batch_size = 1000
    mock_hub_cls.return_value = mock_hub

    svc = RdsServiceGateway(multithreaded=False)
    result = svc.update_database("UPDATE table SET x = %s", payload=("val",), returning=True)
    assert result == [{'id': 1}]


@patch("WrenchCL.Connect.RdsServiceGateway.psycopg2.connect")
@patch("WrenchCL.Connect.RdsServiceGateway.AwsClientHub")
def test_rds_reconnect_swaps_single_connection(mock_hub_cls, mock_connect):
    old_conn = MagicMock()
    new_conn = MagicMock()
    mock_hub = MagicMock()
    mock_hub.db = old_conn
    mock_hub.db_uri = "postgresql://u:p@h:5432/d"
    mock_hub.config.db_batch_size = 100
    mock_hub_cls.return_value = mock_hub
    mock_connect.return_value = new_conn

    svc = RdsServiceGateway(multithreaded=False)
    svc.reconnect()

    mock_connect.assert_called_once_with(mock_hub.db_uri)
    old_conn.close.assert_called_once_with()
    assert svc.connection is new_conn


@patch("WrenchCL.Connect.RdsServiceGateway.psycopg2.connect")
@patch("WrenchCL.Connect.RdsServiceGateway.AwsClientHub")
def test_rds_reconnect_is_noop_in_test_mode(mock_hub_cls, mock_connect):
    mock_hub = MagicMock()
    mock_hub.db = MagicMock()
    mock_hub.db_uri = "postgresql://u:p@h:5432/d"
    mock_hub.config.db_batch_size = 100
    mock_hub_cls.return_value = mock_hub

    svc = RdsServiceGateway(multithreaded=False)
    svc.set_test_mode(True)
    svc.reconnect()

    mock_connect.assert_not_called()


@pytest.mark.parametrize(
    ("exception", "expected"),
    [
        (psycopg2.OperationalError("stale"), True),
        (psycopg2.InterfaceError("stale"), True),
        (psycopg2.IntegrityError("constraint"), False),
        (Exception("connection already closed"), True),
        (Exception("unrelated failure"), False),
    ],
)
def test_is_connection_level_error(exception, expected):
    assert RdsServiceGateway._is_connection_level_error(exception) is expected


@patch("WrenchCL.Connect.RdsServiceGateway.AwsClientHub")
def test_rds_get_data_reconnects_and_retries_once(mock_hub_cls):
    first_cursor = MagicMock()
    first_cursor.__enter__.return_value = first_cursor
    first_cursor.execute.side_effect = psycopg2.OperationalError("connection already closed")
    second_cursor = MagicMock()
    second_cursor.__enter__.return_value = second_cursor
    second_cursor.fetchall.return_value = [{"id": 1}]

    conn = MagicMock()
    conn.cursor.side_effect = [first_cursor, second_cursor]
    mock_hub = MagicMock()
    mock_hub.db = conn
    mock_hub.db_uri = "postgresql://u:p@h:5432/d"
    mock_hub.config.db_batch_size = 100
    mock_hub_cls.return_value = mock_hub

    svc = RdsServiceGateway(multithreaded=False)
    with patch.object(svc, "reconnect") as reconnect:
        result = svc.get_data("SELECT * FROM foo", payload=None)

    reconnect.assert_called_once_with()
    assert result == [{"id": 1}]
    assert conn.cursor.call_count == 2


@patch("WrenchCL.Connect.RdsServiceGateway.AwsClientHub")
def test_rds_get_data_integrity_error_does_not_reconnect(mock_hub_cls):
    cursor = MagicMock()
    cursor.__enter__.return_value = cursor
    cursor.execute.side_effect = psycopg2.IntegrityError("constraint")
    conn = MagicMock()
    conn.cursor.return_value = cursor
    mock_hub = MagicMock()
    mock_hub.db = conn
    mock_hub.db_uri = "postgresql://u:p@h:5432/d"
    mock_hub.config.db_batch_size = 100
    mock_hub_cls.return_value = mock_hub

    svc = RdsServiceGateway(multithreaded=False)
    with patch.object(svc, "reconnect") as reconnect:
        result = svc.get_data("SELECT * FROM foo", payload=None)

    reconnect.assert_not_called()
    assert result is None


@patch("WrenchCL.Connect.RdsServiceGateway.AwsClientHub")
def test_rds_update_integrity_error_does_not_reconnect(mock_hub_cls):
    cursor = MagicMock()
    cursor.__enter__.return_value = cursor
    cursor.execute.side_effect = psycopg2.IntegrityError("constraint")
    conn = MagicMock()
    conn.cursor.return_value = cursor
    mock_hub = MagicMock()
    mock_hub.db = conn
    mock_hub.db_uri = "postgresql://u:p@h:5432/d"
    mock_hub.config.db_batch_size = 100
    mock_hub_cls.return_value = mock_hub

    svc = RdsServiceGateway(multithreaded=False)
    with patch.object(svc, "reconnect") as reconnect:
        with pytest.raises(psycopg2.IntegrityError):
            svc.update_database("UPDATE table SET x = %s", payload=("val",))

    reconnect.assert_not_called()

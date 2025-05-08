# tests/test_connect.py

import io
import pytest
from unittest.mock import patch, MagicMock, mock_open

from WrenchCL.Connect import AwsClientHub, RdsServiceGateway, S3ServiceGateway


# ─────────────────────────────────────────────────────────────
# AwsClientHub Tests
# ─────────────────────────────────────────────────────────────

@patch("WrenchCL.Connect.AwsClientHub._ConfigurationManager")
@patch("WrenchCL.Connect.AwsClientHub.boto3")
def test_aws_client_hub_initialization(mock_boto3, mock_config_cls):
    mock_config = MagicMock()
    mock_config.secret_arn = "arn:aws:secret"
    mock_config.aws_profile = "test"
    mock_config.region_name = "us-west-2"
    mock_config_cls.return_value = mock_config

    mock_session = MagicMock()
    mock_boto3.session.Session.return_value = mock_session
    mock_session.client.return_value.get_secret_value.return_value = {
        "SecretString": '{"username":"u","password":"p","host":"h","port":5432,"dbname":"d"}'
    }

    hub = AwsClientHub(env_path=None, AWS_PROFILE="test", SECRET_ARN="arn:aws:secret")
    uri = hub.get_db_uri()
    assert uri.startswith("postgresql://")


@patch("WrenchCL.Connect.AwsClientHub.boto3.session.Session")
@patch("WrenchCL.Connect.AwsClientHub._ConfigurationManager")
def test_get_s3_client(mock_config_cls, mock_session_cls):
    mock_config = MagicMock()
    mock_config.secret_arn = "arn"
    mock_config.aws_profile = "p"
    mock_config.region_name = "us-east-1"
    mock_config_cls.return_value = mock_config

    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client
    mock_session_cls.return_value = mock_session

    hub = AwsClientHub(env_path=None, AWS_PROFILE="p", SECRET_ARN="arn")
    s3 = hub.get_s3_client()
    assert s3 is not None


# ─────────────────────────────────────────────────────────────
# RdsServiceGateway Tests
# ─────────────────────────────────────────────────────────────

@patch("WrenchCL.Connect.RdsServiceGateway.ThreadedConnectionPool")
@patch("WrenchCL.Connect.RdsServiceGateway.AwsClientHub")
def test_rds_multithreaded_connection(mock_hub_cls, mock_pool_cls):
    mock_hub = MagicMock()
    mock_hub.get_config.return_value.db_batch_size = 100
    mock_hub.get_db_uri.return_value = "postgresql://u:p@h:5432/d"
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
    mock_hub.get_db_uri.return_value = "postgresql://..."
    mock_hub.get_db_client.return_value = mock_conn
    mock_hub.get_config.return_value.db_batch_size = 1000
    mock_hub_cls.return_value = mock_hub

    svc = RdsServiceGateway(multithreaded=False)
    result = svc.update_database("UPDATE table SET x = %s", payload=("val",), returning=True)
    assert result == [{'id': 1}]


# ─────────────────────────────────────────────────────────────
# S3ServiceGateway Tests
# ─────────────────────────────────────────────────────────────

@patch("WrenchCL.Connect.S3ServiceGateway.AwsClientHub")
def test_s3_upload_bytes(mock_hub_cls):
    mock_client = MagicMock()
    mock_hub_cls.return_value.get_s3_client.return_value = mock_client

    svc = S3ServiceGateway()
    svc.set_test_mode(True)

    # No actual upload because test_mode=True
    result = svc.upload_file(b"binarydata", "my-bucket", "test/file.txt")
    assert result is None
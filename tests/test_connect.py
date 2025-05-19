# tests/test_connect.py

import io
import pytest
from unittest.mock import patch, MagicMock, mock_open, PropertyMock

from WrenchCL.Connect import AwsClientHub, RdsServiceGateway, S3ServiceGateway


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

from unittest.mock import patch, MagicMock

from WrenchCL.Connect import RdsServiceGateway


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
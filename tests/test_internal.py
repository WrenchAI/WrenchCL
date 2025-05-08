# tests/test_internal.py

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from WrenchCL._Internal._ConfigurationManager import _ConfigurationManager
from WrenchCL._Internal._MockPandas import _MockPandas
from WrenchCL._Internal._SshTunnelManager import _SshTunnelManager

# ─────────────────────────────────────────────────────────────
# Tests for _ConfigurationManager
# ─────────────────────────────────────────────────────────────

def test_configuration_manager_env(monkeypatch):
    monkeypatch.setenv("SECRET_ARN", "arn:aws:secretsmanager:us-east-1:123456789012:secret:example")
    cfg = _ConfigurationManager()
    assert cfg.secret_arn.startswith("arn:aws")

def test_configuration_manager_env_path(tmp_path, monkeypatch):
    dotenv = tmp_path / ".env"
    dotenv.write_text("SECRET_ARN=arn:aws:secretsmanager:us-east-1:123456789012:secret:test\nAWS_PROFILE=test-profile")
    cfg = _ConfigurationManager(env_path=str(dotenv))
    assert cfg.aws_profile == "test-profile"
    assert cfg.secret_arn.endswith(":test")

def test_configuration_manager_kwargs():
    cfg = _ConfigurationManager(SECRET_ARN="x", REGION_NAME="us-west-2", SSH_PORT=2200)
    assert cfg.region_name == "us-west-2"
    assert cfg.ssh_port == 2200

def test_configuration_manager_uri_construction():
    cfg = _ConfigurationManager(SECRET_ARN="x")
    secret = {
        "username": "test",
        "password": "pass",
        "host": "db.host.com",
        "port": 5432,
        "dbname": "main"
    }
    cfg.load_rds_secret(secret)
    uri = cfg.construct_db_uri()
    assert uri.startswith("postgresql://test:pass@db.host.com:5432/main")

def test_configuration_manager_log_safe_config():
    cfg = _ConfigurationManager(SECRET_ARN="verysecret", OPENAI_API_KEY="openaikey")
    masked = cfg._log_safe_config()
    assert masked["secret_arn"].startswith("ver...")
    assert "..." in masked["openai_api_key"]

# ─────────────────────────────────────────────────────────────
# Tests for _MockPandas
# ─────────────────────────────────────────────────────────────

def test_mock_dataframe_basic_usage():
    df = _MockPandas.DataFrame(data={"a": [1, 2], "b": [3, 4]})
    rows = list(df.itertuples())
    assert rows == [(1, 3), (2, 4)]

def test_mock_dataframe_applymap():
    df = _MockPandas.DataFrame(data={"a": [1, 2]})
    assert df.applymap(lambda x: x * 2) is df

def test_mock_series_apply():
    series = _MockPandas.Series(data=[1, 2, 3])
    assert series.apply(lambda x: x * 2) is series

def test_mock_isna_and_notnull():
    assert _MockPandas.isna(None)
    assert not _MockPandas.notnull(None)
    assert _MockPandas.notnull("value")

# ─────────────────────────────────────────────────────────────
# Tests for _SshTunnelManager
# ─────────────────────────────────────────────────────────────

@patch("WrenchCL._Internal._SshTunnelManager.SSHTunnelForwarder")
def test_ssh_tunnel_start_and_stop(mock_forwarder_class):
    mock_forwarder = MagicMock()
    mock_forwarder.local_bind_port = 7777
    mock_forwarder_class.return_value = mock_forwarder

    config = {
        "PGHOST": "remote.db",
        "PGPORT": 5432,
        "PGDATABASE": "mydb",
        "PGUSER": "admin",
        "PGPASSWORD": "pass",
        "SSH_TUNNEL": {
            "SSH_SERVER": "bastion.host",
            "SSH_PORT": 22,
            "SSH_USER": "ec2-user",
            "SSH_PASSWORD": "secret"
        }
    }
    manager = _SshTunnelManager(config)
    host, port = manager.start_tunnel()
    assert host == "127.0.0.1"
    assert port == 7777

    manager.stop_tunnel()
    mock_forwarder.stop.assert_called_once()


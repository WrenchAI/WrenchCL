import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from WrenchCL.Wrench._secret import resolve_secret

pytestmark = pytest.mark.skipif(False, reason="datadog_itr_unskippable")


class TestDirectValue:
    def test_returns_direct_value_when_provided(self):
        result = resolve_secret(value="direct-secret")
        assert result == "direct-secret"

    def test_returns_direct_value_even_when_env_var_set(self):
        with patch.dict("os.environ", {"WRENCH_SERVICE_SECRET": "env-secret"}, clear=False):
            result = resolve_secret(value="direct-secret")
            assert result == "direct-secret"

    def test_returns_direct_value_even_when_arn_provided(self):
        result = resolve_secret(value="direct-secret", arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test")
        assert result == "direct-secret"

    def test_ignores_empty_string_value(self):
        with patch.dict("os.environ", {"WRENCH_SERVICE_SECRET": "env-secret"}, clear=False):
            result = resolve_secret(value="")
            assert result == "env-secret"

    def test_ignores_none_value(self):
        with patch.dict("os.environ", {"WRENCH_SERVICE_SECRET": "env-secret"}, clear=False):
            result = resolve_secret(value=None)
            assert result == "env-secret"


class TestEnvironmentVariable:
    def test_returns_env_var_value_when_value_not_provided(self):
        with patch.dict("os.environ", {"WRENCH_SERVICE_SECRET": "env-secret"}, clear=False):
            result = resolve_secret()
            assert result == "env-secret"

    def test_returns_env_var_value_when_value_is_empty(self):
        with patch.dict("os.environ", {"WRENCH_SERVICE_SECRET": "env-secret"}, clear=False):
            result = resolve_secret(value="")
            assert result == "env-secret"

    def test_respects_custom_env_var_name(self):
        with patch.dict("os.environ", {"CUSTOM_SECRET": "custom-secret"}, clear=False):
            result = resolve_secret(env_var="CUSTOM_SECRET")
            assert result == "custom-secret"

    def test_returns_none_when_custom_env_var_not_set(self):
        with patch.dict("os.environ", {}, clear=False):
            if "CUSTOM_SECRET" in os.environ:
                del os.environ["CUSTOM_SECRET"]
            result = resolve_secret(env_var="CUSTOM_SECRET")
            assert result is None

    def test_env_var_takes_priority_over_arn(self):
        with patch.dict("os.environ", {"WRENCH_SERVICE_SECRET": "env-secret"}, clear=False):
            mock_boto3 = MagicMock()
            mock_client = MagicMock()
            mock_boto3.client.return_value = mock_client

            with patch.dict(sys.modules, {"boto3": mock_boto3}):
                result = resolve_secret(arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test")
                assert result == "env-secret"
                mock_boto3.client.assert_not_called()

    def test_ignores_empty_env_var_value(self):
        with patch.dict("os.environ", {"WRENCH_SERVICE_SECRET": ""}, clear=False):
            result = resolve_secret()
            assert result is None


class TestArnResolution:
    def test_returns_arn_fetched_value_when_boto3_available(self):
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_secret_value.return_value = {"SecretString": "arn-secret"}

        with patch.dict("os.environ", {}, clear=False):
            if "WRENCH_SERVICE_SECRET" in os.environ:
                del os.environ["WRENCH_SERVICE_SECRET"]
            with patch.dict(sys.modules, {"boto3": mock_boto3}):
                result = resolve_secret(arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test")

        assert result == "arn-secret"
        mock_boto3.client.assert_called_once_with("secretsmanager", region_name="us-east-1")
        mock_client.get_secret_value.assert_called_once_with(SecretId="arn:aws:secretsmanager:us-east-1:123456789:secret:test")

    def test_respects_custom_region(self):
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_secret_value.return_value = {"SecretString": "arn-secret"}

        with patch.dict("os.environ", {}, clear=False):
            if "WRENCH_SERVICE_SECRET" in os.environ:
                del os.environ["WRENCH_SERVICE_SECRET"]
            with patch.dict(sys.modules, {"boto3": mock_boto3}):
                result = resolve_secret(arn="arn:aws:secretsmanager:us-west-2:123456789:secret:test", region="us-west-2")

        assert result == "arn-secret"
        mock_boto3.client.assert_called_once_with("secretsmanager", region_name="us-west-2")

    @patch("WrenchCL.Wrench._secret.logger")
    def test_logs_warning_when_boto3_not_available(self, mock_logger):
        with patch.dict("os.environ", {}, clear=False):
            if "WRENCH_SERVICE_SECRET" in os.environ:
                del os.environ["WRENCH_SERVICE_SECRET"]
            with patch.dict(sys.modules, {"boto3": None}):
                result = resolve_secret(arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test")

        assert result is None
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args[0][0]
        assert "boto3 is required" in call_args

    @patch("WrenchCL.Wrench._secret.logger")
    def test_returns_none_and_logs_on_boto3_exception(self, mock_logger):
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_secret_value.side_effect = Exception("Access Denied")

        with patch.dict("os.environ", {}, clear=False):
            if "WRENCH_SERVICE_SECRET" in os.environ:
                del os.environ["WRENCH_SERVICE_SECRET"]
            with patch.dict(sys.modules, {"boto3": mock_boto3}):
                result = resolve_secret(arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test")

        assert result is None
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args[0][0]
        assert "Access Denied" in call_args

    def test_returns_none_when_secret_string_empty(self):
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_secret_value.return_value = {"SecretString": ""}

        with patch.dict("os.environ", {}, clear=False):
            if "WRENCH_SERVICE_SECRET" in os.environ:
                del os.environ["WRENCH_SERVICE_SECRET"]
            with patch.dict(sys.modules, {"boto3": mock_boto3}):
                result = resolve_secret(arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test")

        assert result is None

    def test_returns_none_when_secret_string_missing(self):
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_secret_value.return_value = {}

        with patch.dict("os.environ", {}, clear=False):
            if "WRENCH_SERVICE_SECRET" in os.environ:
                del os.environ["WRENCH_SERVICE_SECRET"]
            with patch.dict(sys.modules, {"boto3": mock_boto3}):
                result = resolve_secret(arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test")

        assert result is None


class TestResolutionPriority:
    def test_value_takes_priority_over_env_var_and_arn(self):
        with patch.dict("os.environ", {"WRENCH_SERVICE_SECRET": "env-secret"}, clear=False):
            mock_boto3 = MagicMock()
            mock_client = MagicMock()
            mock_boto3.client.return_value = mock_client
            mock_client.get_secret_value.return_value = {"SecretString": "arn-secret"}

            with patch.dict(sys.modules, {"boto3": mock_boto3}):
                result = resolve_secret(
                    value="direct-secret",
                    arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test"
                )

            assert result == "direct-secret"
            mock_boto3.client.assert_not_called()

    def test_env_var_takes_priority_over_arn(self):
        with patch.dict("os.environ", {"WRENCH_SERVICE_SECRET": "env-secret"}, clear=False):
            mock_boto3 = MagicMock()
            mock_client = MagicMock()
            mock_boto3.client.return_value = mock_client
            mock_client.get_secret_value.return_value = {"SecretString": "arn-secret"}

            with patch.dict(sys.modules, {"boto3": mock_boto3}):
                result = resolve_secret(arn="arn:aws:secretsmanager:us-east-1:123456789:secret:test")

            assert result == "env-secret"
            mock_boto3.client.assert_not_called()


class TestLogging:
    @patch("WrenchCL.Wrench._secret.logger")
    @patch.dict("os.environ", {}, clear=False)
    def test_logs_warning_when_all_sources_fail(self, mock_logger):
        result = resolve_secret()

        assert result is None
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args[0][0]
        assert "no secret could be resolved" in call_args
        assert "WRENCH_SERVICE_SECRET" in call_args

    @patch("WrenchCL.Wrench._secret.logger")
    @patch.dict("os.environ", {}, clear=False)
    def test_logs_warning_with_custom_env_var_name(self, mock_logger):
        result = resolve_secret(env_var="CUSTOM_SECRET")

        assert result is None
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args[0][0]
        assert "CUSTOM_SECRET" in call_args
        assert "no secret could be resolved" in call_args


class TestAutoArnFallback:
    def test_auto_arn_fallback_when_env_var_empty(self):
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_secret_value.return_value = {"SecretString": "auto-arn-secret"}

        with patch.dict("os.environ", {"WRENCH_SERVICE_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:test"}, clear=False):
            if "WRENCH_SERVICE_SECRET" in os.environ:
                del os.environ["WRENCH_SERVICE_SECRET"]
            with patch.dict(sys.modules, {"boto3": mock_boto3}):
                result = resolve_secret(env_var="WRENCH_SERVICE_SECRET")

        assert result == "auto-arn-secret"
        mock_boto3.client.assert_called_once_with("secretsmanager", region_name="us-east-1")

    def test_auto_arn_fallback_with_custom_region(self):
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_secret_value.return_value = {"SecretString": "auto-arn-secret"}

        with patch.dict("os.environ", {"WRENCH_SERVICE_SECRET_ARN": "arn:aws:secretsmanager:us-west-2:123456789:secret:test"}, clear=False):
            if "WRENCH_SERVICE_SECRET" in os.environ:
                del os.environ["WRENCH_SERVICE_SECRET"]
            with patch.dict(sys.modules, {"boto3": mock_boto3}):
                result = resolve_secret(env_var="WRENCH_SERVICE_SECRET", region="us-west-2")

        assert result == "auto-arn-secret"
        mock_boto3.client.assert_called_once_with("secretsmanager", region_name="us-west-2")

    def test_auto_arn_does_not_override_explicit_arn(self):
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_secret_value.return_value = {"SecretString": "explicit-arn-secret"}

        with patch.dict("os.environ", {"WRENCH_SERVICE_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:111111111:secret:auto"}, clear=False):
            if "WRENCH_SERVICE_SECRET" in os.environ:
                del os.environ["WRENCH_SERVICE_SECRET"]
            with patch.dict(sys.modules, {"boto3": mock_boto3}):
                result = resolve_secret(
                    env_var="WRENCH_SERVICE_SECRET",
                    arn="arn:aws:secretsmanager:us-east-1:123456789:secret:explicit"
                )

        assert result == "explicit-arn-secret"
        mock_client.get_secret_value.assert_called_once_with(SecretId="arn:aws:secretsmanager:us-east-1:123456789:secret:explicit")

    def test_auto_arn_does_not_apply_when_env_var_has_value(self):
        mock_boto3 = MagicMock()
        with patch.dict("os.environ", {
            "WRENCH_SERVICE_SECRET": "env-secret",
            "WRENCH_SERVICE_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:test"
        }, clear=False):
            with patch.dict(sys.modules, {"boto3": mock_boto3}):
                result = resolve_secret(env_var="WRENCH_SERVICE_SECRET")

        assert result == "env-secret"
        mock_boto3.client.assert_not_called()

    def test_auto_arn_with_custom_env_var_name(self):
        mock_boto3 = MagicMock()
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_secret_value.return_value = {"SecretString": "custom-auto-arn-secret"}

        with patch.dict("os.environ", {"CUSTOM_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:custom"}, clear=False):
            if "CUSTOM_SECRET" in os.environ:
                del os.environ["CUSTOM_SECRET"]
            with patch.dict(sys.modules, {"boto3": mock_boto3}):
                result = resolve_secret(env_var="CUSTOM_SECRET")

        assert result == "custom-auto-arn-secret"

    def test_auto_arn_skipped_when_env_var_is_none(self):
        mock_boto3 = MagicMock()
        with patch.dict("os.environ", {"WRENCH_SERVICE_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:test"}, clear=False):
            with patch.dict(sys.modules, {"boto3": mock_boto3}):
                result = resolve_secret(env_var=None)

        assert result is None
        mock_boto3.client.assert_not_called()

    def test_auto_arn_returns_none_when_arn_env_var_empty(self):
        mock_boto3 = MagicMock()
        with patch.dict("os.environ", {"WRENCH_SERVICE_SECRET_ARN": ""}, clear=False):
            if "WRENCH_SERVICE_SECRET" in os.environ:
                del os.environ["WRENCH_SERVICE_SECRET"]
            with patch.dict(sys.modules, {"boto3": mock_boto3}):
                result = resolve_secret(env_var="WRENCH_SERVICE_SECRET")

        assert result is None
        mock_boto3.client.assert_not_called()


class TestEdgeCases:
    def test_none_env_var_parameter_skips_env_var_check(self):
        with patch.dict("os.environ", {"WRENCH_SERVICE_SECRET": "env-secret"}, clear=False):
            result = resolve_secret(env_var=None)
            assert result is None

    def test_empty_arn_parameter_skips_arn_check(self):
        result = resolve_secret(value=None, env_var=None, arn="")
        assert result is None

    def test_none_arn_parameter_skips_arn_check(self):
        mock_boto3 = MagicMock()
        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            result = resolve_secret(value=None, env_var=None, arn=None)

        mock_boto3.client.assert_not_called()
        assert result is None


if __name__ == "__main__":
    pytest.main()

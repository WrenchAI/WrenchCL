import os
from unittest.mock import MagicMock, patch

import pytest

from WrenchCL.Wrench._notify import job_close, job_register, job_update

pytestmark = pytest.mark.skipif(False, reason="datadog_itr_unskippable")


class TestJobRegister:
    @patch("WrenchCL.Wrench._notify.requests.post")
    def test_job_register_returns_job_id_on_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"job_id": "uuid-123"}}
        mock_post.return_value = mock_response

        result = job_register(
            workspace_id="ws-123",
            message="Processing data",
            source="elt",
            service_secret="test-secret"
        )

        assert result == "uuid-123"

    @patch("WrenchCL.Wrench._notify.requests.post")
    def test_job_register_handles_nested_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"job_id": "uuid-456"}
        mock_post.return_value = mock_response

        result = job_register(
            workspace_id="ws-123",
            message="Processing data",
            source="elt",
            service_secret="test-secret"
        )

        assert result == "uuid-456"

    @patch("WrenchCL.Wrench._notify.logger")
    @patch("WrenchCL.Wrench._notify.requests.post")
    def test_job_register_returns_none_on_missing_job_id(self, mock_post, mock_logger):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {}}
        mock_post.return_value = mock_response

        result = job_register(
            workspace_id="ws-123",
            message="Processing data",
            source="elt",
            service_secret="test-secret"
        )

        assert result is None
        mock_logger.warning.assert_called()

    @patch("WrenchCL.Wrench._notify.logger")
    @patch("WrenchCL.Wrench._notify.requests.post")
    def test_job_register_returns_none_on_api_error(self, mock_post, mock_logger):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.return_value = mock_response

        result = job_register(
            workspace_id="ws-123",
            message="Processing data",
            source="elt",
            service_secret="test-secret"
        )

        assert result is None
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args[0][0]
        assert "500" in call_args

    @patch("WrenchCL.Wrench._notify.logger")
    @patch("WrenchCL.Wrench._notify.requests.post")
    def test_job_register_returns_none_on_request_exception(self, mock_post, mock_logger):
        import requests
        mock_post.side_effect = requests.RequestException("Connection failed")

        result = job_register(
            workspace_id="ws-123",
            message="Processing data",
            source="elt",
            service_secret="test-secret"
        )

        assert result is None
        mock_logger.warning.assert_called()

    @patch("WrenchCL.Wrench._notify.logger")
    @patch.dict("os.environ", {}, clear=False)
    def test_job_register_returns_none_when_secret_missing(self, mock_logger):
        if "WRENCH_SERVICE_SECRET" in os.environ:
            del os.environ["WRENCH_SERVICE_SECRET"]

        result = job_register(
            workspace_id="ws-123",
            message="Processing data",
            source="elt"
        )

        assert result is None
        mock_logger.warning.assert_called()

    @patch("WrenchCL.Wrench._notify.requests.post")
    def test_job_register_sends_correct_payload(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"job_id": "uuid-123"}}
        mock_post.return_value = mock_response

        job_register(
            workspace_id="ws-123",
            message="Processing data",
            source="elt",
            service_name="elt_processor",
            processor_name="custom_processor",
            reference="ref-456",
            service_secret="test-secret"
        )

        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["workspace_id"] == "ws-123"
        assert payload["message"] == "Processing data"
        assert payload["source"] == "elt"
        assert payload["service_name"] == "elt_processor"
        assert payload["processor_name"] == "custom_processor"
        assert payload["reference"] == "ref-456"

    @patch("WrenchCL.Wrench._notify.requests.post")
    def test_job_register_uses_default_base_url(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"job_id": "uuid-123"}}
        mock_post.return_value = mock_response

        job_register(
            workspace_id="ws-123",
            message="Processing data",
            source="elt",
            service_secret="test-secret"
        )

        call_args = mock_post.call_args[0]
        endpoint = call_args[0]
        assert "api.v2.wrench.ai" in endpoint

    @patch("WrenchCL.Wrench._notify.requests.post")
    def test_job_register_uses_custom_base_url(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"job_id": "uuid-123"}}
        mock_post.return_value = mock_response

        job_register(
            workspace_id="ws-123",
            message="Processing data",
            source="elt",
            service_secret="test-secret",
            base_url="https://api.qa.wrench.ai"
        )

        call_args = mock_post.call_args[0]
        endpoint = call_args[0]
        assert "api.qa.wrench.ai" in endpoint


class TestJobUpdate:
    @patch("WrenchCL.Wrench._notify.requests.patch")
    def test_job_update_returns_true_on_success(self, mock_patch):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_patch.return_value = mock_response

        result = job_update(
            job_id="uuid-123",
            progress=50,
            service_secret="test-secret"
        )

        assert result is True

    @patch("WrenchCL.Wrench._notify.requests.patch")
    def test_job_update_returns_true_on_rate_limit(self, mock_patch):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 429
        mock_patch.return_value = mock_response

        result = job_update(
            job_id="uuid-123",
            progress=50,
            service_secret="test-secret"
        )

        assert result is True  # Rate limit is not an error

    @patch("WrenchCL.Wrench._notify.logger")
    @patch("WrenchCL.Wrench._notify.requests.patch")
    def test_job_update_returns_false_on_api_error(self, mock_patch, mock_logger):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_patch.return_value = mock_response

        result = job_update(
            job_id="uuid-123",
            progress=50,
            service_secret="test-secret"
        )

        assert result is False
        mock_logger.warning.assert_called()

    @patch("WrenchCL.Wrench._notify.logger")
    @patch("WrenchCL.Wrench._notify.requests.patch")
    def test_job_update_returns_false_on_request_exception(self, mock_patch, mock_logger):
        import requests
        mock_patch.side_effect = requests.RequestException("Connection failed")

        result = job_update(
            job_id="uuid-123",
            progress=50,
            service_secret="test-secret"
        )

        assert result is False
        mock_logger.warning.assert_called()

    @patch("WrenchCL.Wrench._notify.logger")
    def test_job_update_returns_false_when_job_id_empty(self, mock_logger):
        result = job_update(
            job_id="",
            progress=50,
            service_secret="test-secret"
        )

        assert result is False

    @patch("WrenchCL.Wrench._notify.logger")
    @patch.dict("os.environ", {}, clear=False)
    def test_job_update_returns_false_when_secret_missing(self, mock_logger):
        if "WRENCH_SERVICE_SECRET" in os.environ:
            del os.environ["WRENCH_SERVICE_SECRET"]

        result = job_update(
            job_id="uuid-123",
            progress=50
        )

        assert result is False
        mock_logger.warning.assert_called()

    @patch("WrenchCL.Wrench._notify.requests.patch")
    def test_job_update_clamps_progress(self, mock_patch):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_patch.return_value = mock_response

        job_update(
            job_id="uuid-123",
            progress=150,
            service_secret="test-secret"
        )

        call_kwargs = mock_patch.call_args[1]
        payload = call_kwargs["json"]
        assert payload["progress"] == 100

        mock_patch.reset_mock()

        job_update(
            job_id="uuid-123",
            progress=-10,
            service_secret="test-secret"
        )

        call_kwargs = mock_patch.call_args[1]
        payload = call_kwargs["json"]
        assert payload["progress"] == 0

    @patch("WrenchCL.Wrench._notify.requests.patch")
    def test_job_update_includes_description_when_provided(self, mock_patch):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_patch.return_value = mock_response

        job_update(
            job_id="uuid-123",
            progress=50,
            description="Processing step 2",
            service_secret="test-secret"
        )

        call_kwargs = mock_patch.call_args[1]
        payload = call_kwargs["json"]
        assert payload["progress_description"] == "Processing step 2"

    @patch("WrenchCL.Wrench._notify.requests.patch")
    def test_job_update_includes_workspace_id_when_provided(self, mock_patch):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_patch.return_value = mock_response

        job_update(
            job_id="uuid-123",
            progress=50,
            workspace_id="ws-456",
            service_secret="test-secret"
        )

        call_kwargs = mock_patch.call_args[1]
        payload = call_kwargs["json"]
        assert payload["workspace_id"] == "ws-456"


class TestJobClose:
    @patch("WrenchCL.Wrench._notify.requests.post")
    def test_job_close_returns_true_on_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        result = job_close(
            job_id="uuid-123",
            workspace_id="ws-123",
            status_code=200,
            message="Job completed",
            source="elt",
            service_secret="test-secret"
        )

        assert result is True

    @patch("WrenchCL.Wrench._notify.logger")
    @patch("WrenchCL.Wrench._notify.requests.post")
    def test_job_close_returns_false_on_api_error(self, mock_post, mock_logger):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.return_value = mock_response

        result = job_close(
            job_id="uuid-123",
            workspace_id="ws-123",
            status_code=200,
            message="Job completed",
            source="elt",
            service_secret="test-secret"
        )

        assert result is False
        mock_logger.warning.assert_called()

    @patch("WrenchCL.Wrench._notify.logger")
    @patch("WrenchCL.Wrench._notify.requests.post")
    def test_job_close_returns_false_on_request_exception(self, mock_post, mock_logger):
        import requests
        mock_post.side_effect = requests.RequestException("Connection failed")

        result = job_close(
            job_id="uuid-123",
            workspace_id="ws-123",
            status_code=200,
            message="Job completed",
            source="elt",
            service_secret="test-secret"
        )

        assert result is False
        mock_logger.warning.assert_called()

    @patch("WrenchCL.Wrench._notify.logger")
    def test_job_close_returns_false_when_job_id_empty(self, mock_logger):
        result = job_close(
            job_id="",
            workspace_id="ws-123",
            status_code=200,
            message="Job completed",
            source="elt",
            service_secret="test-secret"
        )

        assert result is False

    @patch("WrenchCL.Wrench._notify.logger")
    @patch.dict("os.environ", {}, clear=False)
    def test_job_close_returns_false_when_secret_missing(self, mock_logger):
        if "WRENCH_SERVICE_SECRET" in os.environ:
            del os.environ["WRENCH_SERVICE_SECRET"]

        result = job_close(
            job_id="uuid-123",
            workspace_id="ws-123",
            status_code=200,
            message="Job completed",
            source="elt"
        )

        assert result is False
        mock_logger.warning.assert_called()

    @patch("WrenchCL.Wrench._notify.requests.post")
    def test_job_close_sends_correct_payload(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        job_close(
            job_id="uuid-123",
            workspace_id="ws-456",
            status_code=500,
            message="Job failed with error",
            source="featureforge",
            notify=False,
            service_secret="test-secret"
        )

        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["job_id"] == "uuid-123"
        assert payload["workspace_id"] == "ws-456"
        assert payload["status_code"] == 500
        assert payload["message"] == "Job failed with error"
        assert payload["source"] == "featureforge"
        assert payload["notify"] is False

    @patch("WrenchCL.Wrench._notify.requests.post")
    def test_job_close_default_notify_is_true(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        job_close(
            job_id="uuid-123",
            workspace_id="ws-456",
            status_code=200,
            message="Job completed",
            source="elt",
            service_secret="test-secret"
        )

        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["notify"] is True


class TestAutoArnIntegration:
    @patch("WrenchCL.Wrench._notify.requests.post")
    def test_job_register_uses_auto_arn_env_var(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"job_id": "uuid-123"}}
        mock_post.return_value = mock_response

        with patch.dict("os.environ", {
            "WRENCH_SERVICE_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123456789:secret:test"
        }, clear=False):
            if "WRENCH_SERVICE_SECRET" in os.environ:
                del os.environ["WRENCH_SERVICE_SECRET"]

            with patch("WrenchCL.Wrench._notify.resolve_secret") as mock_resolve:
                mock_resolve.return_value = "auto-arn-resolved-secret"
                result = job_register(
                    workspace_id="ws-123",
                    message="Processing data",
                    source="elt"
                )

        assert result == "uuid-123"
        mock_resolve.assert_called_once()

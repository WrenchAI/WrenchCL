import os
from unittest.mock import patch, MagicMock

import pytest

from WrenchCL.Wrench._slack import slack_post

pytestmark = pytest.mark.skipif(False, reason="datadog_itr_unskippable")


@patch("WrenchCL.Wrench._slack.requests.post")
def test_slack_post_returns_true_on_200_response(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    result = slack_post(
        message="Test message",
        service_secret="test-secret"
    )

    assert result is True


@patch("WrenchCL.Wrench._slack.requests.post")
def test_slack_post_returns_true_on_299_response(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 299
    mock_post.return_value = mock_response

    result = slack_post(
        message="Test message",
        service_secret="test-secret"
    )

    assert result is True


@patch("WrenchCL.Wrench._slack.logger")
@patch("WrenchCL.Wrench._slack.requests.post")
def test_slack_post_returns_false_on_401_response(mock_post, mock_logger):
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized error"
    mock_post.return_value = mock_response

    result = slack_post(
        message="Test message",
        service_secret="test-secret"
    )

    assert result is False
    mock_logger.warning.assert_called_once()
    call_args = mock_logger.warning.call_args[0][0]
    assert "401" in call_args


@patch("WrenchCL.Wrench._slack.logger")
@patch("WrenchCL.Wrench._slack.requests.post")
def test_slack_post_returns_false_on_500_response(mock_post, mock_logger):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal server error"
    mock_post.return_value = mock_response

    result = slack_post(
        message="Test message",
        service_secret="test-secret"
    )

    assert result is False
    mock_logger.warning.assert_called_once()


@patch("WrenchCL.Wrench._slack.logger")
@patch("WrenchCL.Wrench._slack.requests.post")
def test_slack_post_returns_false_on_request_exception(mock_post, mock_logger):
    import requests
    mock_post.side_effect = requests.RequestException("Connection failed")

    result = slack_post(
        message="Test message",
        service_secret="test-secret"
    )

    assert result is False
    mock_logger.warning.assert_called_once()
    call_args = mock_logger.warning.call_args[0][0]
    assert "Connection failed" in call_args


@patch("WrenchCL.Wrench._slack.logger")
@patch.dict("os.environ", {}, clear=False)
def test_slack_post_returns_false_when_secret_missing(mock_logger):
    if "WRENCH_SERVICE_SECRET" in os.environ:
        del os.environ["WRENCH_SERVICE_SECRET"]

    result = slack_post(
        message="Test message"
    )

    assert result is False
    mock_logger.warning.assert_called_once()
    call_args = mock_logger.warning.call_args[0][0]
    assert "WRENCH_SERVICE_SECRET" in call_args


@patch("WrenchCL.Wrench._slack.requests.post")
def test_slack_post_reads_secret_from_environment(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    with patch.dict("os.environ", {"WRENCH_SERVICE_SECRET": "env-secret"}, clear=False):
        result = slack_post(
            message="Test message"
        )

    assert result is True
    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["headers"]["x-api-secret"] == "env-secret"


@patch("WrenchCL.Wrench._slack.requests.post")
def test_slack_post_reads_base_url_from_environment(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    custom_url = "https://api.qa.wrench.ai"
    with patch.dict("os.environ", {
        "WRENCH_SERVICE_SECRET": "secret",
        "WRENCH_API_BASE_URL": custom_url
    }, clear=False):
        result = slack_post(
            message="Test message"
        )

    assert result is True
    call_args = mock_post.call_args[0]
    assert custom_url in call_args[0]


@patch("WrenchCL.Wrench._slack.requests.post")
def test_slack_post_falls_back_to_prod_url(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    with patch.dict("os.environ", {"WRENCH_SERVICE_SECRET": "secret"}, clear=False):
        if "WRENCH_API_BASE_URL" in os.environ:
            del os.environ["WRENCH_API_BASE_URL"]

        result = slack_post(
            message="Test message"
        )

    assert result is True
    call_args = mock_post.call_args[0]
    assert "api.v2.wrench.ai" in call_args[0]


@patch("WrenchCL.Wrench._slack.requests.post")
def test_slack_post_sends_correct_payload(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    slack_post(
        message="Test message",
        channel="alerts",
        level="ERROR",
        metadata={"key": "value"},
        service_secret="secret"
    )

    call_kwargs = mock_post.call_args[1]
    payload = call_kwargs["json"]
    assert payload["message"] == "Test message"
    assert payload["channel"] == "alerts"
    assert payload["level"] == "ERROR"
    assert payload["metadata"] == {"key": "value"}


@patch("WrenchCL.Wrench._slack.requests.post")
def test_slack_post_does_not_include_metadata_when_none(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    slack_post(
        message="Test message",
        service_secret="secret"
    )

    call_kwargs = mock_post.call_args[1]
    payload = call_kwargs["json"]
    assert "metadata" not in payload


@patch("WrenchCL.Wrench._slack.requests.post")
def test_slack_post_uses_x_api_secret_header(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    slack_post(
        message="Test message",
        service_secret="my-secret"
    )

    call_kwargs = mock_post.call_args[1]
    headers = call_kwargs["headers"]
    assert "x-api-secret" in headers
    assert headers["x-api-secret"] == "my-secret"
    assert "Authorization" not in headers


@patch("WrenchCL.Wrench._slack.requests.post")
def test_slack_post_explicit_secret_takes_precedence(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    with patch.dict("os.environ", {"WRENCH_SERVICE_SECRET": "env-secret"}, clear=False):
        slack_post(
            message="Test message",
            service_secret="explicit-secret"
        )

    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["headers"]["x-api-secret"] == "explicit-secret"


@patch("WrenchCL.Wrench._slack.requests.post")
def test_slack_post_explicit_base_url_takes_precedence(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    with patch.dict("os.environ", {
        "WRENCH_SERVICE_SECRET": "secret",
        "WRENCH_API_BASE_URL": "https://api.dev.wrench.ai"
    }, clear=False):
        slack_post(
            message="Test message",
            base_url="https://api.custom.wrench.ai"
        )

    call_args = mock_post.call_args[0]
    assert "api.custom.wrench.ai" in call_args[0]


@patch("WrenchCL.Wrench._slack.requests.post")
def test_slack_post_default_channel(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    slack_post(
        message="Test message",
        service_secret="secret"
    )

    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["json"]["channel"] == "pipeline_runs"


@patch("WrenchCL.Wrench._slack.requests.post")
def test_slack_post_default_level(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    slack_post(
        message="Test message",
        service_secret="secret"
    )

    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["json"]["level"] == "INFO"


@patch("WrenchCL.Wrench._slack.requests.post")
def test_slack_post_custom_timeout(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    slack_post(
        message="Test message",
        service_secret="secret",
        timeout=30
    )

    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["timeout"] == 30


@patch("WrenchCL.Wrench._slack.requests.post")
def test_slack_post_default_timeout(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    slack_post(
        message="Test message",
        service_secret="secret"
    )

    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["timeout"] == 10


@patch("WrenchCL.Wrench._slack.logger")
@patch("WrenchCL.Wrench._slack.requests.post")
def test_slack_post_logs_response_body_on_error(mock_post, mock_logger):
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad request with very long error message that should be truncated to 200 characters or less to prevent log spam and maintain readability in warning messages sent to log systems"
    mock_post.return_value = mock_response

    slack_post(
        message="Test message",
        service_secret="secret"
    )

    call_args = mock_logger.warning.call_args[0][0]
    assert "400" in call_args
    assert len(call_args) <= 300


@patch("WrenchCL.Wrench._slack.requests.post")
def test_slack_post_builds_correct_endpoint(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    slack_post(
        message="Test message",
        service_secret="secret"
    )

    call_args = mock_post.call_args[0]
    endpoint = call_args[0]
    assert endpoint.endswith("/dev/slack/post")


if __name__ == "__main__":
    pytest.main()

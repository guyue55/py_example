import unittest
from unittest.mock import Mock, patch

import pytest
import requests

from example import __version__
from example.client import APIClient
from example.exceptions import APIError, AuthenticationError, RateLimitError


class TestAPIClient(unittest.TestCase):
    """Test cases for the APIClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_url = "https://api.example.com"
        self.client = APIClient(self.base_url)

    def tearDown(self):
        self.client.close()

    def test_build_url(self):
        """Test URL building functionality."""
        # Test with leading slash
        endpoint = "/endpoint"
        expected = "https://api.example.com/endpoint"
        self.assertEqual(self.client._build_url(endpoint), expected)

        # Test without leading slash
        endpoint = "endpoint"
        expected = "https://api.example.com/endpoint"
        self.assertEqual(self.client._build_url(endpoint), expected)

    def test_user_agent_is_versioned(self):
        """The default User-Agent should be derived from the package version."""
        with patch("requests.Session.request") as mock_request:
            mock_response = Mock(spec=requests.Response)
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_request.return_value = mock_response

            self.client.get("/endpoint")
            _, kwargs = mock_request.call_args
            self.assertEqual(
                kwargs["headers"]["User-Agent"],
                f"{APIClient.__module__.split('.')[0]}/{__version__}",
            )

    @patch("requests.Session.request")
    def test_request_success(self, mock_request):
        """Test successful API request."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        response = self.client.get("/endpoint")

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs["method"], "GET")
        self.assertEqual(kwargs["url"], "https://api.example.com/endpoint")
        self.assertEqual(response, mock_response)

    @patch("requests.Session.request")
    def test_rate_limit_error(self, mock_request):
        """Test rate limit error handling."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_request.return_value = mock_response

        with self.assertRaises(RateLimitError):
            self.client.get("/endpoint")

    @patch("requests.Session.request")
    def test_auth_error(self, mock_request):
        """Test authentication error handling."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_request.return_value = mock_response

        with self.assertRaises(AuthenticationError):
            self.client.get("/endpoint")

    @patch("requests.Session.request")
    def test_server_error(self, mock_request):
        """A 5xx response (after retries) should surface as APIError."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_request.return_value = mock_response

        with self.assertRaises(APIError):
            self.client.get("/endpoint")

    def test_api_error_preserves_status_code_from_error_response(self):
        """APIError must keep status_code even for non-ok (falsy) responses.

        ``requests.Response`` is falsy for error statuses, so the constructor
        must not rely on truthiness to read the status code.
        """
        resp = requests.Response()
        resp.status_code = 503
        err = APIError("boom", response=resp)
        self.assertEqual(err.status_code, 503)
        self.assertIs(err.response, resp)

    def test_transport_retry_exhausted_raises_api_error(self):
        """When retries are exhausted on a transport error, raise APIError."""
        with patch(
            "requests.Session.request",
            side_effect=requests.exceptions.RetryError("exhausted"),
        ):
            with self.assertRaises(APIError):
                self.client.get("/endpoint")

    def test_retry_adapter_is_configured(self):
        """默认重试只允许读取方法，读取错误不重放。"""
        adapter = self.client.session.get_adapter("https://")
        retry = adapter.max_retries
        self.assertEqual(retry.total, 3)
        self.assertEqual(retry.status_forcelist, [429, 500, 502, 503, 504])
        self.assertEqual(set(retry.allowed_methods), {"GET", "HEAD", "OPTIONS"})
        self.assertEqual(retry.read, 0)
        self.assertEqual(retry.other, 0)
        self.assertEqual(retry.backoff_jitter, 0.2)
        self.assertFalse(retry.raise_on_status)

    def test_context_manager_closes_session(self):
        """APIClient supports the context manager protocol and closes on exit."""
        client = APIClient(self.base_url)
        with patch.object(client.session, "close") as mock_close:
            with client:
                self.assertIsInstance(client, APIClient)
            mock_close.assert_called_once()


if __name__ == "__main__":
    unittest.main()


def test_request_options_and_headers_do_not_mutate_caller():
    client = APIClient("https://example.invalid")
    headers = {"user-agent": "caller"}
    with client, patch.object(client.session, "request") as send:
        response = Mock(spec=requests.Response)
        response.raise_for_status.return_value = None
        send.return_value = response
        client.get("/x", headers=headers, timeout=0.5)
        assert send.call_args.kwargs["timeout"] == 0.5
        assert send.call_args.kwargs["headers"]["User-Agent"] == "caller"
        assert send.call_args.kwargs["allow_redirects"] is False
    assert headers == {"user-agent": "caller"}


@pytest.mark.parametrize(
    "options",
    [
        {"max_retries": -1},
        {"retry_jitter": float("inf")},
        {"retry_methods": "POST"},
        {"retry_methods": []},
    ],
)
def test_invalid_retry_configuration_is_rejected(options):
    with pytest.raises(ValueError):
        APIClient("https://example.invalid", **options)

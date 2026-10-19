import unittest
from unittest.mock import Mock, patch

import requests

from example.client import APIClient
from example.exceptions import APIError, AuthenticationError, RateLimitError


class TestAPIClient(unittest.TestCase):
    """Test cases for the APIClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_url = "https://api.example.com"
        self.client = APIClient(self.base_url)

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
            self.assertTrue(kwargs["headers"]["User-Agent"].startswith("example/"))

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
        """The mounted adapter must retry 429/5xx and the write methods."""
        adapter = self.client.session.get_adapter("https://")
        retry = adapter.max_retries
        self.assertEqual(retry.total, 3)
        self.assertEqual(retry.status_forcelist, [429, 500, 502, 503, 504])
        self.assertTrue({"POST", "PUT", "PATCH", "DELETE"}.issubset(set(retry.allowed_methods)))
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

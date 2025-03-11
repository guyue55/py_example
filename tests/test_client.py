import unittest
from unittest.mock import patch, Mock
import requests

from py_example.client import APIClient
from py_example.exceptions import APIError, RateLimitError, AuthenticationError


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
    
    @patch("requests.Session.request")
    def test_request_success(self, mock_request):
        """Test successful API request."""
        # Setup mock response
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        # Make request
        response = self.client.get("/endpoint")
        
        # Verify request was made correctly
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs["method"], "GET")
        self.assertEqual(kwargs["url"], "https://api.example.com/endpoint")
        self.assertEqual(response, mock_response)
    
    @patch("requests.Session.request")
    def test_rate_limit_error(self, mock_request):
        """Test rate limit error handling."""
        # Setup mock response for rate limit error
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_request.return_value = mock_response
        
        # Test that rate limit error is raised
        with self.assertRaises(RateLimitError):
            self.client.get("/endpoint")
    
    @patch("requests.Session.request")
    def test_auth_error(self, mock_request):
        """Test authentication error handling."""
        # Setup mock response for auth error
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_request.return_value = mock_response
        
        # Test that auth error is raised
        with self.assertRaises(AuthenticationError):
            self.client.get("/endpoint")


if __name__ == "__main__":
    unittest.main()
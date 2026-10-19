import unittest

import requests
from requests.auth import HTTPBasicAuth

from example.auth import ApiKeyAuth, BasicAuth, BearerAuth


class TestAuth(unittest.TestCase):
    """Test cases for the authentication classes."""

    def _prepare(self, url="https://api.example.com/endpoint", params=None):
        return requests.Request("GET", url, params=params).prepare()

    def test_bearer_auth_sets_header(self):
        auth = BearerAuth("my-token")
        req = self._prepare()
        auth(req)
        self.assertEqual(req.headers["Authorization"], "Bearer my-token")

    def test_basic_auth_sets_authorization_header(self):
        """BasicAuth must actually emit an Authorization header (bug fix)."""
        auth = BasicAuth("user", "pass")
        # It should be a proper requests BasicAuth under the hood.
        self.assertIsInstance(auth, HTTPBasicAuth)
        req = self._prepare()
        auth(req)
        self.assertIn("Authorization", req.headers)
        self.assertTrue(req.headers["Authorization"].startswith("Basic "))

    def test_api_key_auth_header(self):
        auth = ApiKeyAuth("secret", param_name="api_key", location="header")
        req = self._prepare()
        auth(req)
        self.assertEqual(req.headers["api_key"], "secret")

    def test_api_key_auth_query_appends_to_url(self):
        """ApiKeyAuth(location='query') must actually put the key in the URL."""
        auth = ApiKeyAuth("secret", param_name="api_key", location="query")
        req = self._prepare(params={"existing": "1"})
        auth(req)
        self.assertIn("api_key=secret", req.url)
        self.assertIn("existing=1", req.url)

    def test_api_key_auth_invalid_location_raises(self):
        with self.assertRaises(ValueError):
            ApiKeyAuth("secret", location="cookie")


if __name__ == "__main__":
    unittest.main()

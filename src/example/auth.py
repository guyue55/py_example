"""Authentication module for the example SDK template.

This module provides authentication classes for API clients.
"""

from requests.auth import AuthBase
from requests.auth import HTTPBasicAuth as _HTTPBasicAuth


class BearerAuth(AuthBase):
    """Bearer token authentication for requests.

    This class implements the Bearer token authentication scheme
    commonly used in API requests.

    Attributes:
        token: The Bearer token to use for authentication.
    """

    def __init__(self, token: str):
        """Initialize the Bearer token authentication.

        Args:
            token: The Bearer token to use for authentication.
        """
        self.token = token

    def __call__(self, request):
        """Add the Bearer token to the request headers.

        Args:
            request: The request to authenticate.

        Returns:
            The authenticated request.
        """
        request.headers["Authorization"] = f"Bearer {self.token}"
        return request


class BasicAuth(_HTTPBasicAuth):
    """Basic authentication for requests.

    Thin wrapper around :class:`requests.HTTPBasicAuth`. It keeps the same
    public constructor (``BasicAuth(username, password)``) while delegating
    the (correct) Authorization header encoding to ``requests``.

    Attributes:
        username: The username for authentication.
        password: The password for authentication.
    """


class ApiKeyAuth(AuthBase):
    """API Key authentication for requests.

    This class implements API Key authentication by adding the API key to
    either request headers or query parameters.

    Attributes:
        api_key: The API key to use for authentication.
        param_name: The name of the parameter to use for the API key.
        location: Where to add the API key ("header" or "query").
    """

    def __init__(self, api_key: str, param_name: str = "api_key", location: str = "header"):
        """Initialize the API Key authentication.

        Args:
            api_key: The API key to use for authentication.
            param_name: The name of the parameter to use for the API key.
            location: Where to add the API key ("header" or "query").
        """
        self.api_key = api_key
        self.param_name = param_name
        self.location = location.lower()

        if self.location not in ["header", "query"]:
            raise ValueError("Location must be either 'header' or 'query'")

    def __call__(self, request):
        """Add the API key to the request.

        Args:
            request: The request to authenticate (a ``PreparedRequest``).

        Returns:
            The authenticated request.
        """
        if self.location == "header":
            request.headers[self.param_name] = self.api_key
        else:  # query
            # A PreparedRequest has no mutable ``.params`` attribute; the URL is
            # already fixed. Use ``prepare_url`` to append the API key to the
            # query string so that it is actually carried on the wire.
            request.prepare_url(request.url, {self.param_name: self.api_key})

        return request

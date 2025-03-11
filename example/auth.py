"""Authentication module for SDK Utils.

This module provides authentication classes for API clients.
"""

from typing import Dict, Optional, Any
from requests.auth import AuthBase


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


class BasicAuth(AuthBase):
    """Basic authentication for requests.
    
    This class implements the Basic authentication scheme
    using username and password.
    
    Attributes:
        username: The username for authentication.
        password: The password for authentication.
    """
    
    def __init__(self, username: str, password: str):
        """Initialize the Basic authentication.
        
        Args:
            username: The username for authentication.
            password: The password for authentication.
        """
        self.username = username
        self.password = password
    
    def __call__(self, request):
        """Add the Basic authentication to the request.
        
        Args:
            request: The request to authenticate.
            
        Returns:
            The authenticated request.
        """
        # requests will handle the actual Basic auth header encoding
        request.auth = (self.username, self.password)
        return request


class ApiKeyAuth(AuthBase):
    """API Key authentication for requests.
    
    This class implements API Key authentication by adding
    the API key to either headers or query parameters.
    
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
            request: The request to authenticate.
            
        Returns:
            The authenticated request.
        """
        if self.location == "header":
            request.headers[self.param_name] = self.api_key
        else:  # query
            # Get the existing params or initialize an empty dict
            params = request.params if hasattr(request, "params") else {}
            
            # Add the API key to the params
            params[self.param_name] = self.api_key
            
            # Update the request with the new params
            request.params = params
        
        return request
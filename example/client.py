"""Client module for making API requests.

This module provides the APIClient class for making HTTP requests to APIs.
"""

import time
import logging
from typing import Dict, Any, Optional, Union, List
import requests
from requests.auth import AuthBase
from .exceptions import APIError, RateLimitError, AuthenticationError

logger = logging.getLogger(__name__)

class APIClient:
    """A client for making API requests with built-in retry and error handling.
    
    Attributes:
        base_url (str): The base URL for the API.
        auth (AuthBase, optional): Authentication method to use.
        timeout (int): Timeout for requests in seconds.
        max_retries (int): Maximum number of retry attempts for failed requests.
        retry_delay (int): Delay between retries in seconds.
    """
    
    def __init__(
        self, 
        base_url: str, 
        auth: Optional[AuthBase] = None,
        timeout: int = 60,
        max_retries: int = 3,
        retry_delay: int = 1
    ):
        """Initialize the API client.
        
        Args:
            base_url: The base URL for the API.
            auth: Authentication method to use.
            timeout: Timeout for requests in seconds.
            max_retries: Maximum number of retry attempts for failed requests.
            retry_delay: Delay between retries in seconds.
        """
        self.base_url = base_url.rstrip('/')
        self.auth = auth
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        
        if auth:
            self.session.auth = auth
    
    def _build_url(self, endpoint: str) -> str:
        """Build the full URL for the API endpoint.
        
        Args:
            endpoint: The API endpoint path.
            
        Returns:
            The full URL for the API endpoint.
        """
        endpoint = endpoint.lstrip('/')
        return f"{self.base_url}/{endpoint}"
    
    def _handle_response(self, response: requests.Response) -> requests.Response:
        """Handle the API response and raise appropriate exceptions.
        
        Args:
            response: The API response.
            
        Returns:
            The API response if successful.
            
        Raises:
            RateLimitError: If the API rate limit is exceeded.
            AuthenticationError: If authentication fails.
            APIError: For other API errors.
        """
        try:
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                raise RateLimitError(f"Rate limit exceeded: {response.text}", response=response) from e
            elif response.status_code in (401, 403):
                raise AuthenticationError(f"Authentication failed: {response.text}", response=response) from e
            else:
                raise APIError(f"API error: {response.text}", response=response) from e
    
    def request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> requests.Response:
        """Make an API request with retry logic.
        
        Args:
            method: The HTTP method to use.
            endpoint: The API endpoint path.
            params: Query parameters for the request.
            data: Form data for the request.
            json: JSON data for the request.
            headers: Headers for the request.
            files: Files to upload.
            **kwargs: Additional arguments to pass to requests.
            
        Returns:
            The API response.
            
        Raises:
            APIError: If the API request fails after all retries.
        """
        url = self._build_url(endpoint)
        headers = headers or {}
        
        # Add default headers
        if 'User-Agent' not in headers:
            headers['User-Agent'] = f"sdk_utils/1.0"
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json,
                    headers=headers,
                    files=files,
                    timeout=self.timeout,
                    **kwargs
                )
                
                return self._handle_response(response)
            
            except (RateLimitError, requests.exceptions.RequestException) as e:
                if isinstance(e, RateLimitError) or isinstance(e, requests.exceptions.ConnectionError):
                    if attempt < self.max_retries:
                        sleep_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Request failed, retrying in {sleep_time} seconds... (Attempt {attempt + 1}/{self.max_retries})")                        
                        time.sleep(sleep_time)
                        continue
                
                if isinstance(e, requests.exceptions.RequestException) and not isinstance(e, RateLimitError):
                    raise APIError(f"Request failed: {str(e)}") from e
                raise
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a GET request.
        
        Args:
            endpoint: The API endpoint path.
            **kwargs: Additional arguments to pass to request().
            
        Returns:
            The API response.
        """
        return self.request('GET', endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a POST request.
        
        Args:
            endpoint: The API endpoint path.
            **kwargs: Additional arguments to pass to request().
            
        Returns:
            The API response.
        """
        return self.request('POST', endpoint, **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a PUT request.
        
        Args:
            endpoint: The API endpoint path.
            **kwargs: Additional arguments to pass to request().
            
        Returns:
            The API response.
        """
        return self.request('PUT', endpoint, **kwargs)
    
    def patch(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a PATCH request.
        
        Args:
            endpoint: The API endpoint path.
            **kwargs: Additional arguments to pass to request().
            
        Returns:
            The API response.
        """
        return self.request('PATCH', endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a DELETE request.
        
        Args:
            endpoint: The API endpoint path.
            **kwargs: Additional arguments to pass to request().
            
        Returns:
            The API response.
        """
        return self.request('DELETE', endpoint, **kwargs)
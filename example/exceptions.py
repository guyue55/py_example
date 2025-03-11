"""Exceptions module for SDK Utils.

This module defines custom exceptions used throughout the SDK.
"""

from typing import Optional
import requests


class APIError(Exception):
    """Base exception for all API errors.
    
    Attributes:
        message: Error message.
        response: The API response that caused the error.
    """
    
    def __init__(self, message: str, response: Optional[requests.Response] = None):
        """Initialize the API error.
        
        Args:
            message: Error message.
            response: The API response that caused the error.
        """
        super().__init__(message)
        self.message = message
        self.response = response
        self.status_code = response.status_code if response else None


class AuthenticationError(APIError):
    """Exception raised when authentication fails."""
    pass


class RateLimitError(APIError):
    """Exception raised when API rate limit is exceeded."""
    pass


class ValidationError(APIError):
    """Exception raised when request validation fails."""
    pass


class ResourceNotFoundError(APIError):
    """Exception raised when a requested resource is not found."""
    pass
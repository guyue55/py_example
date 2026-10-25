"""Client module for making API requests.

This module provides the APIClient class for making HTTP requests to APIs.
"""

import logging
import math
from typing import Any, Dict, Iterable, Optional

import requests
from requests.adapters import HTTPAdapter
from requests.auth import AuthBase
from requests.structures import CaseInsensitiveDict
from urllib3.util.retry import Retry

from . import __version__
from .exceptions import APIError, AuthenticationError, RateLimitError

# Top-level package name, derived at runtime so the User-Agent stays correct
# even after this template is renamed to a real package name.
_PACKAGE_NAME = __name__.split(".")[0]

logger = logging.getLogger(__name__)

# Status codes that are safe (and worthwhile) to retry: 429 (rate limit) and
# the transient 5xx server errors. 401/403 are auth failures and must NOT be
# retried.
DEFAULT_STATUS_FORCELIST = [429, 500, 502, 503, 504]

# 只读方法默认可重试；写操作必须由调用方依据服务端幂等保证显式开启。
RETRY_ALLOWED_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


class APIClient:
    """A client for making API requests with built-in retry and error handling.

    Retries (including exponential backoff with jitter) are handled at the
    transport layer via :class:`urllib3.util.retry.Retry` mounted on the
    underlying :class:`requests.Session`. This covers 429 rate-limit responses,
    5xx server errors and pre-send connection errors. Read errors are not
    retried because the remote side may already have performed the operation.
    Request timeout is not an overall deadline including backoff/Retry-After.

    Attributes:
        base_url (str): The base URL for the API.
        auth (AuthBase, optional): Authentication method to use.
        timeout (int): Timeout for requests in seconds.
        max_retries (int): Maximum number of retry attempts for failed requests.
        retry_delay (int): Base backoff factor in seconds between retries.
    """

    def __init__(
        self,
        base_url: str,
        auth: Optional[AuthBase] = None,
        timeout: int = 60,
        max_retries: int = 3,
        retry_delay: float = 1,
        *,
        retry_methods: Optional[Iterable[str]] = None,
        retry_jitter: float = 0.2,
    ):
        """Initialize the API client.

        Args:
            base_url: The base URL for the API.
            auth: Authentication method to use.
            timeout: Timeout for requests in seconds.
            max_retries: Maximum number of retry attempts for failed requests.
            retry_delay: Base backoff factor (seconds) for exponential backoff.
            retry_methods: Explicit retry allowlist; defaults to GET/HEAD/OPTIONS.
                Writes require a server-side idempotency guarantee.
            retry_jitter: Maximum random jitter added to exponential backoff.
        """
        if isinstance(max_retries, bool) or not isinstance(max_retries, int) or max_retries < 0:
            raise ValueError("max_retries必须是非负整数")
        if any(not math.isfinite(v) or v < 0 for v in (retry_delay, retry_jitter)):
            raise ValueError("退避与抖动必须是有限非负数")
        if isinstance(retry_methods, str):
            raise ValueError("retry_methods必须是方法名集合，不能是单个字符串")
        methods = RETRY_ALLOWED_METHODS if retry_methods is None else frozenset(retry_methods)
        if not methods or any(
            not isinstance(m, str) or not m.isascii() or not m.isalpha() for m in methods
        ):
            raise ValueError("retry_methods必须包含合法HTTP方法名")
        self.retry_methods = frozenset(m.upper() for m in methods)
        self.retry_jitter = retry_jitter
        self.base_url = base_url.rstrip("/")
        self.auth = auth
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()

        if auth:
            self.session.auth = auth

        self._mount_retry_adapter()

    def _mount_retry_adapter(self) -> None:
        """Mount a Retry-configured HTTPAdapter on the session.

        ``raise_on_status=False`` ensures that, once retries are exhausted on a
        retriable status (429/5xx), the final response is returned to the
        caller (instead of raising) so that :meth:`_handle_response` can map it
        to a typed exception.
        """
        retry = Retry(
            total=self.max_retries,
            connect=self.max_retries,
            read=0,
            other=0,
            backoff_factor=self.retry_delay,
            backoff_jitter=self.retry_jitter,
            status_forcelist=DEFAULT_STATUS_FORCELIST,
            allowed_methods=self.retry_methods,
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _build_url(self, endpoint: str) -> str:
        """Build the full URL for the API endpoint.

        Args:
            endpoint: The API endpoint path.

        Returns:
            The full URL for the API endpoint.
        """
        endpoint = endpoint.lstrip("/")
        return f"{self.base_url}/{endpoint}"

    def _handle_response(self, response: requests.Response) -> requests.Response:
        """Handle the API response and raise appropriate exceptions.

        Args:
            response: The API response.

        Returns:
            The API response if successful.

        Raises:
            RateLimitError: If the API rate limit is exceeded (429).
            AuthenticationError: If authentication fails (401/403).
            APIError: For other API errors.
        """
        try:
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                raise RateLimitError("API rate limit exceeded (HTTP 429)", response=response) from e
            elif response.status_code in (401, 403):
                raise AuthenticationError(
                    f"API authentication failed (HTTP {response.status_code})", response=response
                ) from e
            else:
                raise APIError(f"API error (HTTP {response.status_code})", response=response) from e

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, Any]] = None,
        **kwargs,
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
            APIError: If the request fails after all retries.
        """
        url = self._build_url(endpoint)
        # 不修改调用方字典；HTTP头大小写不敏感。
        request_headers = CaseInsensitiveDict(headers or {})
        timeout = kwargs.pop("timeout", self.timeout)
        # 自定义API-Key头未必会在跨域跳转时被移除，默认不自动跟随重定向。
        kwargs.setdefault("allow_redirects", False)

        # Add default User-Agent (driven by the package version).
        if "User-Agent" not in request_headers:
            request_headers["User-Agent"] = f"{_PACKAGE_NAME}/{__version__}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json,
                headers=request_headers,
                files=files,
                timeout=timeout,
                **kwargs,
            )
        except requests.exceptions.RequestException as e:
            # 默认消息不复制URL、响应正文或认证信息；保留cause供受控诊断。
            raise APIError("API transport failed; check the underlying cause") from e

        return self._handle_response(response)

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a GET request.

        Args:
            endpoint: The API endpoint path.
            **kwargs: Additional arguments to pass to request().

        Returns:
            The API response.
        """
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a POST request.

        Args:
            endpoint: The API endpoint path.
            **kwargs: Additional arguments to pass to request().

        Returns:
            The API response.
        """
        return self.request("POST", endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a PUT request.

        Args:
            endpoint: The API endpoint path.
            **kwargs: Additional arguments to pass to request().

        Returns:
            The API response.
        """
        return self.request("PUT", endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a PATCH request.

        Args:
            endpoint: The API endpoint path.
            **kwargs: Additional arguments to pass to request().

        Returns:
            The API response.
        """
        return self.request("PATCH", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Make a DELETE request.

        Args:
            endpoint: The API endpoint path.
            **kwargs: Additional arguments to pass to request().

        Returns:
            The API response.
        """
        return self.request("DELETE", endpoint, **kwargs)

    def close(self) -> None:
        """Close the underlying session and release connections."""
        self.session.close()

    def __enter__(self) -> "APIClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

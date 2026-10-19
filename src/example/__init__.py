"""Example - A minimal Python SDK utility template.

This is a template package. Rename ``example`` to your own package name
(search-and-replace ``example`` across the repository, or use
``scripts/rename_template.py``) before publishing.
"""

import logging

# Defined before the submodule imports so that ``from . import __version__``
# inside client.py resolves cleanly (no circular import during package init).
__version__ = "0.3.0"

from .auth import ApiKeyAuth, BasicAuth, BearerAuth
from .client import APIClient
from .exceptions import (
    APIError,
    AuthenticationError,
    RateLimitError,
    ResourceNotFoundError,
    ValidationError,
)

# Library logging hygiene: attach a NullHandler so this package never emits
# rogue log records to the consuming application's root logger unless that
# application configures logging explicitly (per the Python logging docs).
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    "APIClient",
    "ApiKeyAuth",
    "BasicAuth",
    "BearerAuth",
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "ResourceNotFoundError",
    "__version__",
]

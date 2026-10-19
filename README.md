# Example

> **Template notice:** This repository is a template. The package is named
> `example` as a neutral placeholder. Before publishing, rename it to your own
> package name by search-and-replacing `example` across the whole repository
> (directory `src/example`, `pyproject.toml` `name`, imports, and tests).

A minimal Python SDK utility template that provides common building blocks for
building Python SDKs: an HTTP client wrapper with auth, retry, and error
handling.

## Installation

For development (editable install):

```bash
pip install -e .
```

To install the runtime dependencies only:

```bash
pip install ".[dev]"   # includes pytest and ruff for development
```

## Features

- API client utilities (`APIClient`) with built-in retry and error handling
- Authentication helpers (`BearerAuth`, `BasicAuth`, `ApiKeyAuth`)
- Automatic retry with exponential backoff + jitter (429 and 5xx)
- Typed error handling (`APIError`, `RateLimitError`, `AuthenticationError`)

## Usage

```python
from example.client import APIClient
from example.auth import BearerAuth

# Create an authenticated client
client = APIClient(
    base_url="https://api.example.com",
    auth=BearerAuth("your_token_here"),
    timeout=30,
)

# The client is also a context manager
with client:
    # Make API requests with automatic retry and error handling
    response = client.get("/endpoint", params={"key": "value"})

    # Parse the response
    data = response.json()
    print(data)
```

## Documentation

For full documentation, visit [the project repository](https://github.com/guyue55/py_example).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

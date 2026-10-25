"""本地真实HTTP验证重试次数、写入保护、超时和重定向，不调用外部服务。"""

import threading
import time
from collections import Counter
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from example import APIClient, APIError, AuthenticationError, RateLimitError


def api_client(*args, **kwargs):
    client = APIClient(*args, **kwargs)
    client.session.trust_env = False
    return client


@contextmanager
def server():
    calls = Counter()

    class Handler(BaseHTTPRequestHandler):
        def handle_request(self):
            calls[self.command, self.path] += 1
            if self.path == "/slow":
                time.sleep(0.2)
            if self.path == "/rate":
                status = 429
            elif self.path == "/auth":
                status = 401
            elif self.path == "/redirect":
                status = 302
            elif self.path == "/write":
                status = 503
            elif self.path == "/retry" and calls[self.command, self.path] < 3:
                status = 503
            else:
                status = 200
            self.send_response(status)
            if status == 429:
                self.send_header("Retry-After", "0")
            if status == 302:
                self.send_header("Location", "/destination")
            self.end_headers()
            try:
                self.wfile.write(b"SYNTHETIC_RESPONSE_BODY")
            except (BrokenPipeError, ConnectionResetError):
                pass

        do_GET = handle_request
        do_POST = handle_request
        do_PATCH = handle_request
        do_PUT = handle_request
        do_DELETE = handle_request

        def log_message(self, *args):
            pass

    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{http.server_port}", calls
    finally:
        http.shutdown()
        http.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def test_get_retries_status_with_real_connection():
    with server() as (base, calls), api_client(base, retry_delay=0, retry_jitter=0) as client:
        assert client.get("/retry").status_code == 200
        assert calls["GET", "/retry"] == 3


@pytest.mark.parametrize("method", ["POST", "PATCH", "PUT", "DELETE"])
def test_write_status_is_not_replayed_by_default(method):
    with server() as (base, calls), api_client(base, retry_delay=0, retry_jitter=0) as client:
        with pytest.raises(APIError):
            client.request(method, "/write")
        assert calls[method, "/write"] == 1


def test_write_retry_requires_explicit_allowlist():
    with (
        server() as (base, calls),
        api_client(base, retry_methods={"POST"}, retry_delay=0, retry_jitter=0) as client,
    ):
        assert client.post("/retry").status_code == 200
        assert calls["POST", "/retry"] == 3


def test_read_timeout_is_not_replayed():
    with server() as (base, calls), api_client(base, retry_delay=0, retry_jitter=0) as client:
        with pytest.raises(APIError):
            client.get("/slow", timeout=0.03)
        assert calls["GET", "/slow"] == 1


def test_redirect_is_returned_without_following_and_errors_hide_body():
    with server() as (base, calls), api_client(base) as client:
        assert client.get("/redirect").status_code == 302
        assert calls["GET", "/destination"] == 0
        with pytest.raises(AuthenticationError) as error:
            client.get("/auth")
        assert "SYNTHETIC_RESPONSE_BODY" not in str(error.value)
        assert error.value.response.status_code == 401


def test_rate_limit_retry_budget_is_bounded():
    with (
        server() as (base, calls),
        api_client(base, max_retries=2, retry_delay=0, retry_jitter=0) as client,
    ):
        with pytest.raises(RateLimitError):
            client.get("/rate")
        assert calls["GET", "/rate"] == 3

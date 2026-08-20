"""Production CORS + security headers (Phase 5D)."""
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_security_headers_present_on_every_response():
    r = client.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "default-src 'self'" in r.headers["content-security-policy"]


def test_security_headers_present_even_on_a_404():
    """Headers must land on framework-level error responses too, not
    just successful route handler responses -- SecurityHeadersMiddleware
    wraps the whole app, not individual routes."""
    r = client.get("/this-route-does-not-exist")
    assert r.status_code == 404
    assert r.headers["x-frame-options"] == "DENY"


def test_hsts_absent_in_dev():
    # ENVIRONMENT defaults to "dev" for the test suite (tests/conftest.py
    # never sets it to "prod") -- HSTS on a plain-HTTP local dev server
    # would tell the browser to upgrade a connection that doesn't
    # support it.
    r = client.get("/health")
    assert "strict-transport-security" not in r.headers


def test_cors_preflight_from_allowed_origin_succeeds():
    r = client.options(
        "/health", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"}
    )
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_preflight_from_disallowed_origin_fails():
    r = client.options(
        "/health", headers={"Origin": "https://evil.example.com", "Access-Control-Request-Method": "GET"}
    )
    assert r.status_code == 400
    assert "access-control-allow-origin" not in r.headers


def test_cors_actual_request_from_disallowed_origin_gets_no_cors_header():
    """The server still processes the request (CORS is enforced by the
    browser, not the server refusing to run the handler) -- what must
    be true is that the response carries no Access-Control-Allow-Origin,
    so a real browser's JS can't read the response body cross-origin."""
    r = client.get("/health", headers={"Origin": "https://evil.example.com"})
    assert r.status_code == 200
    assert "access-control-allow-origin" not in r.headers

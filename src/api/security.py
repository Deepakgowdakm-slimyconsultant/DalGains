"""Security headers middleware for production hardening.

Never log request bodies: this app handles health-adjacent data (meal
logs, weight, medical_flags) on every write route. No middleware or
route in this codebase reads request.body()/request.json() purely to
log it, and none should be added -- uvicorn's default access log only
records method/path/status, never the body, which is the behavior to
preserve. There's nothing to opt out of here; the rule is "don't add
body logging," enforced by review, not by code.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.config import get_settings

# A restrictive default-deny CSP: only this origin's own resources, plus
# Google Fonts (the frontend's declared font source) and the API itself
# for XHR/fetch. No inline scripts, no third-party trackers, no wildcard.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds the standard hardening headers to every response. This API
    is meant to be called by the DalGains frontend (fetch/XHR), never
    rendered as a page or framed -- CSP and X-Frame-Options both assume
    that, not "this serves HTML that needs a permissive script-src."
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
        # HSTS only makes sense once the app is actually served over
        # HTTPS -- sending it over plain HTTP (local dev) just tells the
        # browser to upgrade a connection that doesn't support it yet.
        # Gated on ENVIRONMENT rather than request.url.scheme: HF Spaces
        # terminates TLS at its own edge and forwards plain HTTP to this
        # container, so the ASGI app never actually sees "https" on
        # request.url.scheme even in production -- only trusting
        # X-Forwarded-Proto (itself spoofable unless the proxy is
        # trusted) would work there, and ENVIRONMENT is the signal this
        # app already trusts for the same distinction (see
        # src/api/routes/auth.py's cookie Secure flag).
        if get_settings().is_prod:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

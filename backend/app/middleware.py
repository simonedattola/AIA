"""Security middleware: headers + basic request hardening."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        # API JSON — avoid caching authenticated responses by default
        if request.url.path.startswith("/api/") and "Cache-Control" not in response.headers:
            if request.url.path.startswith("/api/uploads"):
                response.headers.setdefault("Cache-Control", "public, max-age=86400")
            else:
                response.headers.setdefault("Cache-Control", "no-store")
        return response

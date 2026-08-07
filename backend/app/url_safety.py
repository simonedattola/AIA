"""URL safety helpers (SSRF mitigation)."""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


def is_safe_outbound_url(url: str, *, allowed_hosts: set[str] | None = None) -> bool:
    """
    Reject non-http(s), credentials-in-URL, and private/link-local IP targets.
    Optional allowlist of hostnames (exact match, lowercased).
    """
    raw = (url or "").strip()
    if not raw:
        return False
    try:
        parsed = urlparse(raw)
    except Exception:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    if parsed.username or parsed.password:
        return False
    host = (parsed.hostname or "").lower()
    if not host:
        return False
    if allowed_hosts is not None and host not in {h.lower() for h in allowed_hosts}:
        return False
    # Block obvious local names
    if host in {"localhost", "metadata", "metadata.google.internal"}:
        return False
    try:
        infos = socket.getaddrinfo(host, parsed.port or 80, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return False
    for info in infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return False
    return True

"""Sanitize user-provided text and URLs before they enter HTML templates."""

from __future__ import annotations

import html
import re
from urllib.parse import urlparse

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_ALLOWED_SCHEMES = {"http", "https", "mailto", "tel"}
_FORBIDDEN_SCHEMES = {"javascript", "data", "vbscript", "file", "about"}
_HOST_RE = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$",
    re.I,
)


def escape_text(value: str) -> str:
    """Escape HTML special characters in visible text."""
    return html.escape((value or "").strip(), quote=True)


def normalize_http_url(value: str) -> str:
    """Return a safe http(s) URL, or an empty string if the value is not usable.

    Bare domains such as cac.com.ar get an https:// prefix. javascript:, data:
    and other schemes are rejected.
    """
    raw = (value or "").strip()
    if not raw:
        return ""
    lower = raw.lower()
    for scheme in _FORBIDDEN_SCHEMES:
        if lower.startswith(scheme + ":"):
            return ""
    if raw.startswith("//"):
        raw = "https:" + raw
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urlparse(raw)
    if parsed.scheme.lower() not in {"http", "https"}:
        return ""
    host = parsed.hostname or ""
    if not host or not _HOST_RE.match(host):
        return ""
    return raw


def normalize_mailto(value: str) -> str:
    """Return a mailto: URL if the value looks like an email, else empty."""
    raw = (value or "").strip()
    if not raw:
        return ""
    if raw.lower().startswith("mailto:"):
        raw = raw[7:]
    if not _EMAIL_RE.match(raw):
        return ""
    return f"mailto:{raw}"


def normalize_tel(value: str) -> str:
    """Return a tel: URL keeping digits and leading plus; empty if nothing usable."""
    raw = (value or "").strip()
    if not raw:
        return ""
    digits = re.sub(r"[^\d+]", "", raw)
    if len(re.sub(r"\D", "", digits)) < 6:
        return ""
    return f"tel:{digits}"


def is_safe_url(value: str) -> bool:
    """Return True if the URL uses an allowed scheme."""
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme.lower() in _ALLOWED_SCHEMES


def looks_like_email(value: str) -> bool:
    """Return True if the string is a plausible email address."""
    return bool(_EMAIL_RE.match((value or "").strip()))


def compose_org_email(local_part: str, domain: str = "cac.com.ar") -> str:
    """Build user@domain, ignoring a typed @domain and stripping junk from the local part."""
    local = (local_part or "").strip()
    if not local:
        return ""
    local = local.split("@")[0].strip()
    local = re.sub(r"[^a-zA-Z0-9._+-]", "", local)
    if not local:
        return ""
    clean_domain = (domain or "cac.com.ar").strip().lstrip("@").lower()
    if not clean_domain:
        clean_domain = "cac.com.ar"
    return f"{local}@{clean_domain}"

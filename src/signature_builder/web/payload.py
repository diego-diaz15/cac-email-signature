"""Map JSON form payloads to PersonData. The email domain is never taken from the client."""

from __future__ import annotations

from typing import Any

from signature_builder.core.models import PersonData
from signature_builder.core.sanitizer import compose_org_email
from signature_builder.core.template_engine import normalize_template

_TEXT_KEYS = (
    "first_name",
    "last_name",
    "title",
    "department",
    "phone",
    "website",
    "linkedin",
)


def person_from_payload(raw: Any, email_domain: str) -> PersonData:
    """Build PersonData from a JSON object. Unknown keys and a full email are ignored."""
    if not isinstance(raw, dict):
        raise ValueError("El cuerpo tiene que ser un objeto JSON")
    values = {key: str(raw.get(key) or "") for key in _TEXT_KEYS}
    local = str(raw.get("email_local") or "")
    return PersonData(
        **values,
        email=compose_org_email(local, email_domain),
    )


def template_from_payload(raw: Any) -> str:
    """Return a known template name from JSON. Unknown values fall back to corporate."""
    if not isinstance(raw, dict):
        return "corporate"
    return normalize_template(str(raw.get("template") or "corporate").strip())

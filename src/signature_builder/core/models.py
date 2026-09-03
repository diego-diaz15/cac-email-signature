"""Typed data objects for person fields and brand configuration."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any


@dataclass
class PersonData:
    """User-entered fields for one signature. Empty strings mean 'omit from HTML'."""

    first_name: str = ""
    last_name: str = ""
    title: str = ""
    department: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    linkedin: str = ""
    instagram: str = ""
    facebook: str = ""
    twitter: str = ""

    def full_name(self) -> str:
        """Return first + last name with a single space, omitting blanks."""
        return " ".join(part for part in (self.first_name.strip(), self.last_name.strip()) if part)

    def has_socials(self) -> bool:
        """Return True if LinkedIn is present."""
        return bool(self.linkedin.strip())

    def filled_contact_fields(self) -> list[str]:
        """Return names of contact fields that have a value."""
        names = ("phone", "email", "website")
        return [name for name in names if getattr(self, name).strip()]


@dataclass
class BrandColors:
    """Corporate palette used by templates (inline CSS)."""

    primary: str = "#008ACB"
    secondary: str = "#1E4B8E"
    text: str = "#1A1A1A"
    muted: str = "#5C5F66"
    divider: str = "#D2D6DA"
    link: str = "#1E4B8E"


@dataclass
class LogoConfig:
    """Paths and display size for the static and animated logos."""

    source: str = "assets/brand/logo-source.png"
    animated: str = "assets/brand/logo-animated.gif"
    static: str = "assets/brand/logo.png"
    public_url: str = ""
    display_width: int = 140
    display_height: int = 140


@dataclass
class AnimationConfig:
    """Parameters for the one-time GIF build (process A)."""

    max_angle: float = 0.0
    fps: int = 10
    motion_frames: int = 20
    pause_frames: int = 28
    output_size: int = 380


@dataclass
class BrandConfig:
    """Brand settings loaded from brand.json. Not user-editable in the main form."""

    name: str = "Empresa"
    short_name: str = ""
    website: str = ""
    email_domain: str = "cac.com.ar"
    template: str = "corporate"
    colors: BrandColors = field(default_factory=BrandColors)
    logo: LogoConfig = field(default_factory=LogoConfig)
    animation: AnimationConfig = field(default_factory=AnimationConfig)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> BrandConfig:
        """Build a BrandConfig from a parsed JSON object."""
        colors_raw = raw.get("colors") or {}
        logo_raw = raw.get("logo") or {}
        animation_raw = raw.get("animation") or {}
        return cls(
            name=str(raw.get("name") or "Empresa"),
            short_name=str(raw.get("short_name") or ""),
            website=str(raw.get("website") or ""),
            email_domain=str(raw.get("email_domain") or "cac.com.ar"),
            template=str(raw.get("template") or "corporate"),
            colors=_from_dict(BrandColors, colors_raw),
            logo=_from_dict(LogoConfig, logo_raw),
            animation=_from_dict(AnimationConfig, animation_raw),
        )


def _from_dict(cls: type, raw: dict[str, Any]) -> Any:
    """Fill a dataclass from a dict, ignoring unknown keys."""
    allowed = {item.name for item in fields(cls)}
    filtered = {key: value for key, value in raw.items() if key in allowed}
    return cls(**filtered)

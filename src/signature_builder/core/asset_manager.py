"""Locate brand images and expose file URIs / data URIs for the HTML generator."""

from __future__ import annotations

import base64
import logging
import mimetypes
from pathlib import Path

from signature_builder.core.exceptions import AssetError
from signature_builder.core.models import BrandConfig
from signature_builder.paths import bundled_root, project_root

logger = logging.getLogger(__name__)

ICON_KEYS = ("phone", "email", "web", "linkedin")


class AssetManager:
    """Resolve logo and icon files relative to the app root."""

    def __init__(self, brand: BrandConfig, root: Path | None = None) -> None:
        self.brand = brand
        self.root = root or project_root()

    def resolve(self, relative: str) -> Path:
        """Resolve a brand-relative path, trying the user root then the bundle."""
        rel = Path(relative)
        candidates = [self.root / rel, bundled_root() / rel]
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        return candidates[0]

    def logo_animated_path(self) -> Path:
        """Return the animated GIF path. Raises AssetError if missing."""
        path = self.resolve(self.brand.logo.animated)
        if not path.is_file():
            raise AssetError(f"Falta el logo animado: {path}")
        return path

    def logo_static_path(self) -> Path:
        """Return the static PNG path if present, else the GIF."""
        path = self.resolve(self.brand.logo.static)
        if path.is_file():
            return path
        return self.logo_animated_path()

    def icon_path(self, name: str) -> Path:
        """Return a social/contact icon PNG."""
        path = self.root / "assets" / "icons" / f"{name}.png"
        if path.is_file():
            return path
        bundled = bundled_root() / "assets" / "icons" / f"{name}.png"
        if bundled.is_file():
            return bundled
        raise AssetError(f"Falta el icono {name}: {path}")

    def file_uri(self, path: Path) -> str:
        """Return a file:// URI for preview in the local WebEngine."""
        return path.resolve().as_uri()

    def data_uri(self, path: Path) -> str:
        """Return a data: URI. Used only for isolated tests / local preview fallback."""
        if not path.is_file():
            raise AssetError(f"No se puede embeber {path}")
        mime = mimetypes.guess_type(path.name)[0] or "image/png"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{encoded}"

    def missing_required(self) -> list[str]:
        """Return human-readable names of assets that must exist before copy/export."""
        missing: list[str] = []
        if not self.resolve(self.brand.logo.animated).is_file():
            missing.append("logo animado")
        for key in ("phone", "email", "web"):
            try:
                self.icon_path(key)
            except AssetError:
                missing.append(f"icono {key}")
        return missing

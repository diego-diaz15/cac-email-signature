"""Resolve project, bundled and user-writable paths for source and frozen builds."""

from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    """Return True when running from a PyInstaller executable."""
    return bool(getattr(sys, "frozen", False))


def project_root() -> Path:
    """Return the directory that contains brand.json and assets/.

    In a frozen build this is the folder of SignatureBuilder.exe so operators
    can replace brand files without rebuilding. During development it is the
    repository root (two levels above this module: src/signature_builder/).
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def bundled_root() -> Path:
    """Return the read-only bundle root (PyInstaller _MEIPASS or project root)."""
    if is_frozen():
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
    return project_root()


def assets_dir() -> Path:
    """Return the writable assets directory next to the app."""
    return project_root() / "assets"


def brand_config_path() -> Path:
    """Prefer a brand.json next to the exe; fall back to the bundled copy."""
    user_path = project_root() / "brand.json"
    if user_path.is_file():
        return user_path
    bundled = bundled_root() / "brand.json"
    if bundled.is_file():
        return bundled
    return user_path


def app_data_dir() -> Path:
    """Return a writable directory for logs (AppData on Windows, project logs otherwise)."""
    if is_frozen():
        base = Path.home() / "AppData" / "Roaming" / "SignatureBuilder"
        base.mkdir(parents=True, exist_ok=True)
        return base
    path = project_root() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path

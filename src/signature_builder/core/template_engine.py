"""Minimal {{token}} / {{#if key}} template renderer. No Jinja dependency."""

from __future__ import annotations

import re
from pathlib import Path

from signature_builder.core.exceptions import TemplateError
from signature_builder.paths import bundled_root, project_root

_IF_BLOCK = re.compile(r"\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}", re.DOTALL)
_TOKEN = re.compile(r"\{\{(\w+)\}\}")

TEMPLATE_FILENAMES = {
    "corporate": "corporate.html",
    "original": "original.html",
    "modern": "modern.html",
    "minimal": "minimal.html",
}


def templates_dir() -> Path:
    """Return the directory that stores HTML templates."""
    package = Path(__file__).resolve().parent.parent / "templates"
    if (package / "corporate.html").is_file():
        return package
    bundled = bundled_root() / "src" / "signature_builder" / "templates"
    if (bundled / "corporate.html").is_file():
        return bundled
    return project_root() / "src" / "signature_builder" / "templates"


def load_template(name: str) -> str:
    """Load a named template (corporate, original, modern, minimal)."""
    filename = TEMPLATE_FILENAMES.get(name, TEMPLATE_FILENAMES["corporate"])
    path = templates_dir() / filename
    if not path.is_file():
        raise TemplateError(f"No se encontró la plantilla: {path}")
    return path.read_text(encoding="utf-8")


def render_template(template: str, context: dict[str, str]) -> str:
    """Replace if-blocks and tokens. Nested ifs are not supported."""

    def replace_if(match: re.Match[str]) -> str:
        key = match.group(1)
        body = match.group(2)
        value = context.get(key, "")
        return body if value else ""

    with_ifs = _IF_BLOCK.sub(replace_if, template)

    def replace_token(match: re.Match[str]) -> str:
        return context.get(match.group(1), "")

    return _TOKEN.sub(replace_token, with_ifs)


def normalize_template(name: str) -> str:
    """Return a known template name, or corporate if the value is unknown."""
    if name in TEMPLATE_FILENAMES:
        return name
    return "corporate"

"""Brand.json loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from signature_builder.core.config_manager import load_brand_config
from signature_builder.core.exceptions import BrandConfigError


def test_load_brand_config_reads_colors(tmp_path: Path) -> None:
    path = tmp_path / "brand.json"
    path.write_text(
        json.dumps({"name": "CAC", "colors": {"primary": "#008ACB"}, "template": "corporate"}),
        encoding="utf-8",
    )
    config = load_brand_config(path)
    assert config.name == "CAC"
    assert config.colors.primary == "#008ACB"
    assert config.template == "corporate"


def test_missing_brand_json_raises(tmp_path: Path) -> None:
    with pytest.raises(BrandConfigError):
        load_brand_config(tmp_path / "missing.json")

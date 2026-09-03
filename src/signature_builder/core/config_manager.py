"""Load brand.json into BrandConfig."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from signature_builder.core.exceptions import BrandConfigError
from signature_builder.core.models import BrandConfig
from signature_builder.paths import brand_config_path

logger = logging.getLogger(__name__)


def load_brand_config(path: Path | None = None) -> BrandConfig:
    """Read brand.json. Raises BrandConfigError if the file is missing or invalid."""
    config_path = path or brand_config_path()
    if not config_path.is_file():
        raise BrandConfigError(f"No se encontró brand.json en {config_path}")
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BrandConfigError(f"brand.json inválido: {exc}") from exc
    if not isinstance(raw, dict):
        raise BrandConfigError("brand.json debe ser un objeto JSON")
    config = BrandConfig.from_dict(raw)
    logger.info("Marca cargada: %s (plantilla %s)", config.name, config.template)
    return config

"""Shared fixtures: a throwaway brand folder with a tiny logo and icons."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from signature_builder.animation.icon_set import save_icon_set
from signature_builder.core.models import BrandConfig, PersonData
from signature_builder.core.signature_generator import SignatureGenerator
from signature_builder.core.asset_manager import AssetManager


@pytest.fixture
def person() -> PersonData:
    return PersonData(
        first_name="María",
        last_name="González",
        title="Analista de Soporte",
        department="Tecnología",
        phone="(+54 11) 5300-9000 int. 200",
        email="maria.gonzalez@cac.com.ar",
        website="www.cac.com.ar",
        linkedin="https://www.linkedin.com/in/ejemplo",
    )


@pytest.fixture
def brand_dir(tmp_path: Path) -> Path:
    assets = tmp_path / "assets"
    (assets / "brand").mkdir(parents=True)
    logo = Image.new("RGBA", (80, 80), (0, 138, 203, 255))
    gif_frames = [logo.convert("P")]
    gif_path = assets / "brand" / "logo-animated.gif"
    logo.convert("P").save(gif_path, save_all=True, append_images=gif_frames, loop=0, duration=80)
    static = assets / "brand" / "logo.png"
    logo.save(static)
    save_icon_set(assets / "icons")
    return tmp_path


@pytest.fixture
def brand() -> BrandConfig:
    return BrandConfig(
        name="Cámara Argentina de Comercio y Servicios",
        short_name="CAC",
        website="https://www.cac.com.ar",
    )


@pytest.fixture
def generator(brand: BrandConfig, brand_dir: Path) -> SignatureGenerator:
    assets = AssetManager(brand, root=brand_dir)
    return SignatureGenerator(brand, assets)

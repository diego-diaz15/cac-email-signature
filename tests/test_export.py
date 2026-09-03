"""Export folder and ZIP contain only the signature HTML plus assets."""

from __future__ import annotations

import zipfile
from pathlib import Path

from signature_builder.core.export_manager import ExportManager
from signature_builder.core.models import PersonData
from signature_builder.core.signature_generator import SignatureGenerator
from signature_builder.core.asset_manager import AssetManager
from signature_builder.core.models import BrandConfig


def test_export_folder_and_zip(brand_dir: Path, person: PersonData) -> None:
    brand = BrandConfig()
    assets = AssetManager(brand, root=brand_dir)
    generator = SignatureGenerator(brand, assets)
    exporter = ExportManager(brand, generator, assets)

    folder = brand_dir / "out"
    html_path = exporter.export_folder(folder, person)
    assert html_path.is_file()
    html = html_path.read_text(encoding="utf-8")
    assert "assets/logo-animated.gif" in html
    assert (folder / "assets" / "logo-animated.gif").is_file()
    assert (folder / "assets" / "phone.png").is_file()

    zip_path = brand_dir / "firma.zip"
    exporter.export_zip(zip_path, person)
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
    assert "firma.html" in names
    assert "assets/logo-animated.gif" in names
    assert not any(name.endswith(".py") for name in names)


def test_hosted_export_uses_public_logo_and_data_icons(brand_dir: Path, person: PersonData) -> None:
    brand = BrandConfig()
    brand.logo.public_url = "https://cdn.example.com/logo-cac.png"
    assets = AssetManager(brand, root=brand_dir)
    exporter = ExportManager(brand, SignatureGenerator(brand, assets), assets)
    folder = brand_dir / "hosted-out"
    html = exporter.export_folder(folder, person, image_mode="hosted").read_text(encoding="utf-8")
    assert "https://cdn.example.com/logo-cac.png" in html
    assert "data:image" in html
    assert "assets/logo-animated.gif" not in html
    assert "assets/phone.png" not in html


def test_required_assets_skip_empty_socials(brand_dir: Path) -> None:
    brand = BrandConfig()
    exporter = ExportManager(
        brand,
        SignatureGenerator(brand, AssetManager(brand, brand_dir)),
        AssetManager(brand, brand_dir),
    )
    names = exporter.required_asset_names(PersonData(first_name="A", email="a@b.com"))
    assert "email.png" in names
    assert "linkedin.png" not in names

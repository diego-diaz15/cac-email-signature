"""Export signature HTML and optional ZIP with assets."""

from __future__ import annotations

import logging
import shutil
import zipfile
from pathlib import Path

from signature_builder.core.asset_manager import ICON_KEYS, AssetManager
from signature_builder.core.models import BrandConfig, PersonData
from signature_builder.core.signature_generator import SignatureGenerator

logger = logging.getLogger(__name__)


class ExportManager:
    """Write firma.html and the image files the signature needs."""

    def __init__(self, brand: BrandConfig, generator: SignatureGenerator, assets: AssetManager) -> None:
        self.brand = brand
        self.generator = generator
        self.assets = assets

    def export_folder(
        self,
        dest: Path,
        person: PersonData,
        image_mode: str = "relative",
        template: str | None = None,
    ) -> Path:
        """Write dest/firma.html and dest/assets/*. Returns the HTML path."""
        dest.mkdir(parents=True, exist_ok=True)
        assets_dir = dest / "assets"
        assets_dir.mkdir(exist_ok=True)

        copied = self._copy_assets(assets_dir)
        html = self.generator.render_document(person, image_mode=image_mode, template=template)
        html_path = dest / "firma.html"
        html_path.write_text(html, encoding="utf-8")
        logger.info("Exportado HTML a %s (%s assets)", html_path, len(copied))
        return html_path

    def export_zip(self, zip_path: Path, person: PersonData, template: str | None = None) -> Path:
        """Write a zip with firma.html + assets/. Returns the zip path."""
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        staging_parent = zip_path.parent / f".{zip_path.stem}_staging"
        if staging_parent.exists():
            shutil.rmtree(staging_parent)
        html_path = self.export_folder(staging_parent, person, template=template)
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(html_path, arcname="firma.html")
            for file in sorted((staging_parent / "assets").glob("*")):
                archive.write(file, arcname=f"assets/{file.name}")
        shutil.rmtree(staging_parent, ignore_errors=True)
        logger.info("Exportado ZIP a %s", zip_path)
        return zip_path

    def required_asset_names(self, person: PersonData) -> list[str]:
        """Return the image filenames this signature will reference."""
        names = [Path(self.brand.logo.animated).name]
        if person.phone.strip():
            names.append("phone.png")
        if person.email.strip():
            names.append("email.png")
        if person.website.strip() or self.brand.website:
            names.append("web.png")
        for key in ("linkedin",):
            if getattr(person, key).strip():
                names.append(f"{key}.png")
        return names

    def _copy_assets(self, assets_dir: Path) -> list[Path]:
        copied: list[Path] = []
        logo = self.assets.logo_animated_path()
        target = assets_dir / logo.name
        shutil.copy2(logo, target)
        copied.append(target)
        static = self.assets.resolve(self.brand.logo.static)
        if static.is_file():
            shutil.copy2(static, assets_dir / static.name)
            copied.append(assets_dir / static.name)
        for key in ICON_KEYS:
            try:
                icon = self.assets.icon_path(key)
            except Exception:
                continue
            shutil.copy2(icon, assets_dir / icon.name)
            copied.append(assets_dir / icon.name)
        return copied

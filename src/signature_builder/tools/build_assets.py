"""Build logo-source.png, logo.png, logo-animated.gif and icons once (process A)."""

from __future__ import annotations

import logging
from pathlib import Path

from signature_builder.animation.frame_generator import build_loop, render_frames
from signature_builder.animation.gif_optimizer import save_gif
from signature_builder.animation.icon_set import save_icon_set
from signature_builder.animation.logo_processor import fit_square, isolate_mark, load_logo
from signature_builder.core.config_manager import load_brand_config
from signature_builder.core.models import BrandConfig
from signature_builder.paths import project_root

logger = logging.getLogger(__name__)

REFERENCE_CANDIDATES = (
    "ISO-CAC.png",
    "Logo CAC_Cybermonday 300x300.png",
    "logo HotSale 300x300.jpg",
    "firma soporte.jpeg",
)


def build_brand_assets(
    brand: BrandConfig | None = None,
    source: Path | None = None,
) -> dict[str, Path]:
    """Generate reusable brand images. Safe to run multiple times; overwrites outputs."""
    brand = brand or load_brand_config()
    root = project_root()
    source_path = source or _resolve_source(brand, root)
    logger.info("Fuente del logo: %s", source_path)

    mark = isolate_mark(load_logo(source_path))
    square = fit_square(mark, brand.animation.output_size)

    source_out = root / brand.logo.source
    static_out = root / brand.logo.static
    gif_out = root / brand.logo.animated
    source_out.parent.mkdir(parents=True, exist_ok=True)
    mark.save(source_out)
    square.save(static_out)

    angles = build_loop(
        motion_frames=brand.animation.motion_frames,
        pause_frames=brand.animation.pause_frames,
        max_angle=brand.animation.max_angle,
    )
    frames = render_frames(square, angles)
    save_gif(
        frames,
        gif_out,
        fps=brand.animation.fps,
        colors=256,
        pause_frames=brand.animation.pause_frames,
    )

    icons = save_icon_set(root / "assets" / "icons")
    logger.info("Assets de marca listos (%s iconos)", len(icons))
    return {
        "source": source_out,
        "static": static_out,
        "animated": gif_out,
        "icons_dir": root / "assets" / "icons",
    }


def _resolve_source(brand: BrandConfig, root: Path) -> Path:
    """Prefer the original campaign files over the already-cropped logo-source.png."""
    del brand
    for name in REFERENCE_CANDIDATES:
        candidate = root / name
        if candidate.is_file():
            return candidate
    configured = root / "assets" / "brand" / "logo-source.png"
    if configured.is_file():
        return configured
    raise FileNotFoundError(
        "No hay logo de origen. Colocá un PNG/JPG en assets/brand/logo-source.png"
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    paths = build_brand_assets()
    for key, path in paths.items():
        print(f"{key}: {path}")


if __name__ == "__main__":
    main()

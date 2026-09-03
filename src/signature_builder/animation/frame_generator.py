"""Render a static logo with a slow, eased shine sweep (no tilt)."""

from __future__ import annotations

from collections.abc import Sequence

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from signature_builder.core.exceptions import AssetError


def motion_angles(motion_frames: int, max_angle: float) -> list[float]:
    """Keep the mark frontal. Angle is unused; the loop is shine-only."""
    if motion_frames < 4:
        raise AssetError("Se necesitan al menos 4 frames de movimiento")
    del max_angle
    return [0.0] * motion_frames


def build_loop(motion_frames: int, pause_frames: int, max_angle: float) -> list[float]:
    """Return one rest pose per frame. Pause is applied when saving the GIF."""
    del pause_frames
    return motion_angles(motion_frames, max_angle)


def shine_progress(index: int, count: int) -> float:
    """Return 0 on the rest poses, or an eased 0–1 while the highlight travels."""
    if count <= 2 or index <= 0 or index >= count - 1:
        return 0.0
    t = index / (count - 1)
    return t * t * (3.0 - 2.0 * t)


def render_frame(image: Image.Image, yaw_degrees: float = 0.0, shine_t: float = 0.0) -> Image.Image:
    """Keep the logo still. Shine is drawn at native size so the mark is not resampled."""
    del yaw_degrees
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    if 0.0 < shine_t < 1.0:
        return _apply_shine(image, shine_t)
    return image.copy()


def render_frames(image: Image.Image, angles: Sequence[float]) -> list[Image.Image]:
    """Render a still logo with a shine that travels across once per loop."""
    count = max(1, len(angles))
    return [render_frame(image, shine_t=shine_progress(index, count)) for index, _angle in enumerate(angles)]


def _apply_shine(image: Image.Image, t: float) -> Image.Image:
    """Soft cool highlight: wide veil plus a thin specular core, clipped to the mark."""
    base = image.convert("RGBA")
    width, height = base.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    center = int((-0.20 + t * 1.48) * width)
    slope = int(height * 0.50)
    _draw_band(draw, center, slope, height, radius=32, peak=34, color=(216, 236, 255), width=2)
    _draw_band(draw, center, slope, height, radius=6, peak=82, color=(255, 255, 255), width=1)
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=2.2))
    _, _, _, sheen = overlay.split()
    _, _, _, logo = base.split()
    overlay.putalpha(ImageChops.multiply(sheen, logo))
    return Image.alpha_composite(base, overlay)


def _draw_band(
    draw: ImageDraw.ImageDraw,
    center: int,
    slope: int,
    height: int,
    radius: int,
    peak: int,
    color: tuple[int, int, int],
    width: int,
) -> None:
    """Draw a diagonal band whose alpha falls off from the center line."""
    red, green, blue = color
    for offset in range(-radius, radius + 1):
        falloff = 1 - abs(offset) / radius
        alpha = int(peak * falloff * falloff)
        if alpha < 5:
            continue
        draw.line(
            [(center + offset, -height), (center + offset + slope, height * 2)],
            fill=(red, green, blue, alpha),
            width=width,
        )

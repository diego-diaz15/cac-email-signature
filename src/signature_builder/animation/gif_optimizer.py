"""Quantize and save a looping GIF with a transparent background for light and dark mail."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image

from signature_builder.core.exceptions import AssetError

logger = logging.getLogger(__name__)

# Magenta is not in the CAC mark; it becomes the GIF transparent index.
KEY = (255, 0, 255)
ALPHA_CUTOFF = 128
TARGET_SWEEP_MS = 1100
TARGET_REST_MS = 3200
MIN_SHINE_MS = 70


def keyed_rgb(frame: Image.Image) -> Image.Image:
    """Make empty padding transparent. Do not erode or punch holes in the mark."""
    rgba = frame.convert("RGBA")
    red, green, blue, alpha = rgba.split()
    mask = alpha.point(lambda value: 255 if value >= ALPHA_CUTOFF else 0)
    canvas = Image.new("RGB", rgba.size, KEY)
    canvas.paste(Image.merge("RGB", (red, green, blue)), mask=mask)
    return canvas


def save_gif(
    frames: list[Image.Image],
    dest: Path,
    fps: int = 12,
    colors: int = 256,
    pause_frames: int = 0,
) -> Path:
    """Save an optimized looping GIF. Empty pixels stay transparent in Gmail dark mode."""
    if not frames:
        raise AssetError("No hay frames para el GIF")
    if fps < 6 or fps > 24:
        raise AssetError("FPS fuera de rango (6–24)")
    dest.parent.mkdir(parents=True, exist_ok=True)

    keyed = [keyed_rgb(frame) for frame in frames]
    shared = _shared_palette(keyed, colors=colors)
    trans = int(shared.getpixel((0, 0)))
    quantized = [frame.quantize(palette=shared, dither=Image.Dither.NONE) for frame in keyed]
    for frame in quantized:
        frame.info["transparency"] = trans
    unique = _collapse_identical(quantized)
    durations = _loop_durations(len(unique), fps=fps, pause_frames=pause_frames)
    unique[0].save(
        dest,
        save_all=True,
        append_images=unique[1:],
        loop=0,
        duration=durations,
        disposal=2,
        transparency=trans,
        background=trans,
        optimize=False,
    )
    size_kb = dest.stat().st_size / 1024
    logger.info("GIF guardado %s (%.1f KB, %s frames, %s fps)", dest, size_kb, len(unique), fps)
    if size_kb > 350:
        logger.warning("El GIF pesa %.1f KB; conviene bajar frames o colores", size_kb)
    return dest


def _shared_palette(frames: list[Image.Image], colors: int) -> Image.Image:
    """Build one palette from every frame so shine colors and the key stay aligned."""
    width, height = frames[0].size
    atlas = Image.new("RGB", (width * len(frames), height), KEY)
    for index, frame in enumerate(frames):
        atlas.paste(frame, (index * width, 0))
    return atlas.quantize(colors=max(2, min(colors, 256)), method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)


def _collapse_identical(frames: list[Image.Image]) -> list[Image.Image]:
    """Keep one copy of each run of identical quantized frames."""
    unique: list[Image.Image] = []
    previous: bytes | None = None
    for frame in frames:
        payload = frame.tobytes()
        if payload == previous:
            continue
        unique.append(frame)
        previous = payload
    return unique or frames


def _loop_durations(count: int, fps: int, pause_frames: int) -> list[int]:
    """Hold at rest so the next shine does not start immediately."""
    base_ms = max(40, round(1000 / fps))
    durations = [base_ms] * count
    if count < 3:
        return durations
    shine_n = count - 2
    shine_ms = max(MIN_SHINE_MS, int(round(TARGET_SWEEP_MS / shine_n / 10) * 10))
    for index in range(1, count - 1):
        durations[index] = shine_ms
    if pause_frames > 0:
        durations[0] = base_ms
        durations[-1] = max(base_ms * (1 + pause_frames), TARGET_REST_MS)
    return durations

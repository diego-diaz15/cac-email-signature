"""Load PNG/JPG logos, preserve aspect ratio and transparency, crop lockups."""

from __future__ import annotations

import logging
from collections import deque
from pathlib import Path

from PIL import Image

from signature_builder.core.exceptions import AssetError

logger = logging.getLogger(__name__)

WHITE_THRESHOLD = 240
PAPER_CHROMA = 22
MIN_CONTENT_RATIO = 0.004


def load_logo(path: Path) -> Image.Image:
    """Load SVG/PNG/JPG. SVG is not decoded here (no extra runtime dependency)."""
    if not path.is_file():
        raise AssetError(f"No se encontró el logo: {path}")
    suffix = path.suffix.lower()
    if suffix == ".svg":
        raise AssetError(
            "Este build acepta PNG y JPG. Exportá el SVG a PNG (fondo transparente) y volvé a generar el asset."
        )
    try:
        image = Image.open(path)
        image.load()
    except OSError as exc:
        raise AssetError(f"No se pudo abrir el logo {path}: {exc}") from exc
    return image.convert("RGBA")


def isolate_mark(image: Image.Image) -> Image.Image:
    """Return the logo mark with a transparent background, cropped to content.

    Wide lockups (icon + wordmark) are reduced to the leftmost coloured cluster
    so the animated asset is the hexagon, not the full wordmark.
    """
    rgba = image.convert("RGBA")
    if _has_real_transparency(rgba):
        cropped = _crop_to_alpha(rgba)
        if _aspect(cropped) > 1.7:
            cropped = _left_colour_cluster(cropped)
            cropped = _crop_to_alpha(cropped)
        cropped = _flatten_existing_alpha(cropped)
        logger.info("Logo aislado %sx%s (PNG con transparencia)", cropped.width, cropped.height)
        return cropped
    keyed = _key_background(rgba)
    cropped = _crop_to_alpha(keyed)
    if _aspect(cropped) > 1.7:
        cropped = _left_colour_cluster(cropped)
        cropped = _crop_to_alpha(cropped)
    cropped = _solidify_mark(cropped)
    logger.info("Logo aislado %sx%s", cropped.width, cropped.height)
    return cropped


def fit_square(image: Image.Image, size: int, padding_ratio: float = 0.04) -> Image.Image:
    """Letterbox the mark into a square canvas without stretching it."""
    if size < 16:
        raise AssetError("El tamaño de salida del logo es demasiado pequeño")
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    inner = max(1, int(size * (1 - 2 * padding_ratio)))
    ratio = min(inner / image.width, inner / image.height)
    new_size = (max(1, round(image.width * ratio)), max(1, round(image.height * ratio)))
    scaled = image.resize(new_size, Image.Resampling.LANCZOS)
    offset = ((size - scaled.width) // 2, (size - scaled.height) // 2)
    canvas.paste(scaled, offset, scaled)
    return canvas


def _key_background(image: Image.Image) -> Image.Image:
    """Remove paper connected to the border. Never punch highlights or dark facets."""
    pixels = image.copy()
    width, height = pixels.size
    px = pixels.load()
    visited = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()
    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if x < 0 or y < 0 or x >= width or y >= height:
            continue
        index = y * width + x
        if visited[index]:
            continue
        visited[index] = 1
        red, green, blue, alpha = px[x, y]
        if not _is_paper(red, green, blue, alpha):
            continue
        if alpha != 0:
            px[x, y] = (red, green, blue, 0)
        queue.append((x - 1, y))
        queue.append((x + 1, y))
        queue.append((x, y - 1))
        queue.append((x, y + 1))

    opaque = 0
    for y in range(height):
        for x in range(width):
            if px[x, y][3] > 0:
                opaque += 1
    if opaque / max(1, width * height) < MIN_CONTENT_RATIO:
        logger.warning("El recorte por blanco dejó muy poco contenido; se usa el original")
        return image
    return pixels


def _has_real_transparency(image: Image.Image) -> bool:
    """True when corners are empty and a meaningful share of pixels is transparent."""
    width, height = image.size
    px = image.load()
    corners = ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1))
    if any(px[x, y][3] >= 16 for x, y in corners):
        return False
    empty = 0
    for y in range(height):
        for x in range(width):
            if px[x, y][3] < 16:
                empty += 1
    return empty / max(1, width * height) >= 0.08


def _flatten_existing_alpha(image: Image.Image, cutoff: int = 160) -> Image.Image:
    """Keep the PNG silhouette. Do not un-matte from white: this file is over empty/black."""
    pixels = image.copy()
    px = pixels.load()
    width, height = pixels.size
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = px[x, y]
            if alpha >= cutoff:
                px[x, y] = (red, green, blue, 255)
            else:
                px[x, y] = (0, 0, 0, 0)
    return pixels


def _is_paper(red: int, green: int, blue: int, alpha: int) -> bool:
    """True for empty pixels and low-chroma paper. False for cyan highlights."""
    if alpha < 16:
        return True
    chroma = max(red, green, blue) - min(red, green, blue)
    luma = (red + green + blue) / 3
    return chroma < PAPER_CHROMA and luma >= WHITE_THRESHOLD


def _solidify_mark(image: Image.Image) -> Image.Image:
    """Un-matte outer anti-alias. Drop hole fringe so the 3D gaps stay empty."""
    pixels = image.convert("RGBA")
    width, height = pixels.size
    px = pixels.load()
    empty = [[False] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = px[x, y]
            if alpha < 16 or _is_paper(red, green, blue, alpha):
                empty[y][x] = True

    exterior = [[False] * width for _ in range(height)]
    seen = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()
    for x in range(width):
        if empty[0][x]:
            queue.append((x, 0))
        if empty[height - 1][x]:
            queue.append((x, height - 1))
    for y in range(height):
        if empty[y][0]:
            queue.append((0, y))
        if empty[y][width - 1]:
            queue.append((width - 1, y))
    while queue:
        x, y = queue.popleft()
        if x < 0 or y < 0 or x >= width or y >= height:
            continue
        index = y * width + x
        if seen[index] or not empty[y][x]:
            continue
        seen[index] = 1
        exterior[y][x] = True
        queue.append((x - 1, y))
        queue.append((x + 1, y))
        queue.append((x, y - 1))
        queue.append((x, y + 1))

    out = pixels.copy()
    dest = out.load()
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = px[x, y]
            if empty[y][x]:
                dest[x, y] = (0, 0, 0, 0)
                continue
            if alpha >= 250:
                dest[x, y] = (red, green, blue, 255)
                continue
            touches_hole = False
            touches_exterior = False
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = x + dx, y + dy
                if nx < 0 or ny < 0 or nx >= width or ny >= height:
                    touches_exterior = True
                    continue
                if exterior[ny][nx]:
                    touches_exterior = True
                elif empty[ny][nx]:
                    touches_hole = True
            if touches_hole or not touches_exterior:
                dest[x, y] = (0, 0, 0, 0)
                continue
            fade = alpha / 255.0
            recovered = tuple(
                int(max(0, min(255, round((channel - (1.0 - fade) * 255.0) / fade))))
                for channel in (red, green, blue)
            )
            chroma = max(recovered) - min(recovered)
            luma = sum(recovered) / 3
            if chroma < 12 and luma >= WHITE_THRESHOLD:
                dest[x, y] = (0, 0, 0, 0)
            else:
                dest[x, y] = (recovered[0], recovered[1], recovered[2], 255)
    return out


def _crop_to_alpha(image: Image.Image) -> Image.Image:
    bbox = image.getbbox()
    if bbox is None:
        raise AssetError("El logo quedó vacío después de quitar el fondo")
    return image.crop(bbox)


def _aspect(image: Image.Image) -> float:
    return image.width / max(1, image.height)


def _left_colour_cluster(image: Image.Image) -> Image.Image:
    """Keep the left coloured mark; ignore black/gray wordmark anti-aliasing."""
    pixels = image.load()
    width, height = image.size
    xs: list[int] = []
    ys: list[int] = []
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a < 20:
                continue
            chroma = max(r, g, b) - min(r, g, b)
            if chroma < 28:
                continue
            xs.append(x)
            ys.append(y)
    if not xs:
        return image
    pad = 6
    box = (
        max(0, min(xs) - pad),
        max(0, min(ys) - pad),
        min(width, max(xs) + pad),
        min(height, max(ys) + pad),
    )
    return image.crop(box)

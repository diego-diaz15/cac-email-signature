"""Write small contact and LinkedIn icons as PNG (no extra icon pack dependency)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ICON_SIZE = 32
PRIMARY = (30, 75, 142, 255)  # CAC secondary blue
TRANSPARENT = (255, 255, 255, 0)


def save_icon_set(dest: Path, color: tuple[int, int, int, int] = PRIMARY) -> list[Path]:
    """Write phone, email, web and LinkedIn PNGs into dest."""
    dest.mkdir(parents=True, exist_ok=True)
    drawers = {
        "phone": _draw_phone,
        "email": _draw_email,
        "web": _draw_web,
        "linkedin": _draw_linkedin,
    }
    written: list[Path] = []
    for name, drawer in drawers.items():
        image = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), TRANSPARENT)
        drawer(image, color)
        path = dest / f"{name}.png"
        image.save(path)
        written.append(path)
    return written


def _line_width() -> int:
    return 2


def _draw_phone(image: Image.Image, color: tuple[int, int, int, int]) -> None:
    """Simple device outline, same 2px weight as the envelope and globe."""
    size = 256
    layer = Image.new("RGBA", (size, size), TRANSPARENT)
    draw = ImageDraw.Draw(layer)
    width = 16
    draw.rounded_rectangle((76, 20, 180, 236), radius=32, outline=color, width=width)
    draw.rounded_rectangle((108, 44, 148, 56), radius=6, fill=color)
    fitted = layer.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
    image.paste(fitted, (0, 0), fitted)


def _draw_email(image: Image.Image, color: tuple[int, int, int, int]) -> None:
    draw = ImageDraw.Draw(image)
    w = _line_width()
    draw.rounded_rectangle((4, 8, 28, 24), radius=2, outline=color, width=w)
    draw.line((4, 10, 16, 18), fill=color, width=w)
    draw.line((28, 10, 16, 18), fill=color, width=w)


def _draw_web(image: Image.Image, color: tuple[int, int, int, int]) -> None:
    draw = ImageDraw.Draw(image)
    w = _line_width()
    draw.ellipse((5, 5, 27, 27), outline=color, width=w)
    draw.ellipse((11, 5, 21, 27), outline=color, width=w)
    draw.line((5, 16, 27, 16), fill=color, width=w)


def _draw_linkedin(image: Image.Image, color: tuple[int, int, int, int]) -> None:
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((4, 4, 28, 28), radius=4, fill=color)
    draw.rectangle((8, 13, 12, 24), fill=(255, 255, 255, 255))
    draw.ellipse((8, 7, 12, 11), fill=(255, 255, 255, 255))
    draw.rectangle((15, 13, 19, 24), fill=(255, 255, 255, 255))
    draw.pieslice((15, 13, 24, 25), start=270, end=90, fill=(255, 255, 255, 255))
    draw.rectangle((19, 18, 24, 24), fill=color)

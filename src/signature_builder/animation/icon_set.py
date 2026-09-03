"""Write small contact and LinkedIn icons as PNG (no extra icon pack dependency)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ICON_SIZE = 32
PRIMARY = (30, 75, 142, 255)  # CAC secondary blue
INK = (26, 26, 26, 255)
WHITE = (255, 255, 255, 255)
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
        fill = INK if name in {"phone", "web"} else color
        drawer(image, fill)
        path = dest / f"{name}.png"
        image.save(path)
        written.append(path)
    return written


def _line_width() -> int:
    return 2


def _draw_phone(image: Image.Image, color: tuple[int, int, int, int]) -> None:
    """Circle outline + solid classic handset — matches firma soporte.jpeg."""
    size = 256
    layer = Image.new("RGBA", (size, size), TRANSPARENT)
    draw = ImageDraw.Draw(layer)
    draw.ellipse((14, 14, 242, 242), outline=color, width=18)

    hand = Image.new("RGBA", (size, size), TRANSPARENT)
    hd = ImageDraw.Draw(hand)
    # Solid handset silhouette: thick curved bridge + rounded ends
    hd.pieslice((55, 45, 201, 211), start=200, end=340, fill=color)
    hd.ellipse((95, 85, 161, 171), fill=TRANSPARENT)
    # Restore bridge thickness by redrawing arc band
    for width in range(28, 50):
        hd.arc((70, 60, 186, 196), start=205, end=335, fill=color, width=2)
    hd.ellipse((62, 52, 120, 110), fill=color)
    hd.ellipse((136, 146, 194, 204), fill=color)

    hand = hand.rotate(42, resample=Image.Resampling.BICUBIC, center=(128, 128))
    layer.alpha_composite(hand)
    fitted = layer.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
    image.paste(fitted, (0, 0), fitted)


def _draw_email(image: Image.Image, color: tuple[int, int, int, int]) -> None:
    draw = ImageDraw.Draw(image)
    w = _line_width()
    draw.rounded_rectangle((4, 8, 28, 24), radius=2, outline=color, width=w)
    draw.line((4, 10, 16, 18), fill=color, width=w)
    draw.line((28, 10, 16, 18), fill=color, width=w)


def _draw_web(image: Image.Image, color: tuple[int, int, int, int]) -> None:
    """Circle outline + wireframe globe — matches firma soporte.jpeg."""
    size = 256
    layer = Image.new("RGBA", (size, size), TRANSPARENT)
    draw = ImageDraw.Draw(layer)
    draw.ellipse((14, 14, 242, 242), outline=color, width=18)
    draw.ellipse((48, 48, 208, 208), outline=color, width=14)
    draw.ellipse((96, 48, 160, 208), outline=color, width=12)
    draw.line((48, 128, 208, 128), fill=color, width=12)
    draw.arc((48, 78, 208, 178), start=200, end=340, fill=color, width=11)
    draw.arc((48, 78, 208, 178), start=20, end=160, fill=color, width=11)
    fitted = layer.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
    image.paste(fitted, (0, 0), fitted)


def _draw_linkedin(image: Image.Image, color: tuple[int, int, int, int]) -> None:
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((4, 4, 28, 28), radius=4, fill=color)
    draw.rectangle((8, 13, 12, 24), fill=WHITE)
    draw.ellipse((8, 7, 12, 11), fill=WHITE)
    draw.rectangle((15, 13, 19, 24), fill=WHITE)
    draw.pieslice((15, 13, 24, 25), start=270, end=90, fill=WHITE)
    draw.rectangle((19, 18, 24, 24), fill=color)

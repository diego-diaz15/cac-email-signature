"""Logo isolation, square fit, GIF loop and dimensions."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from signature_builder.animation.frame_generator import build_loop, render_frames, shine_progress
from signature_builder.animation.gif_optimizer import save_gif
from signature_builder.animation.logo_processor import fit_square, isolate_mark


def _lockup() -> Image.Image:
    """Wide white canvas: blue mark on the left, black bars on the right (fake wordmark)."""
    image = Image.new("RGBA", (400, 120), (255, 255, 255, 255))
    for x in range(20, 100):
        for y in range(20, 100):
            image.putpixel((x, y), (0, 140, 200, 255))
    for x in range(140, 360):
        for y in range(40, 80):
            image.putpixel((x, y), (0, 0, 0, 255))
    return image


def _rms(first: Image.Image, second: Image.Image) -> float:
    left = first.convert("RGB")
    right = second.convert("RGB")
    pixels_a = left.load()
    pixels_b = right.load()
    total = 0.0
    count = left.size[0] * left.size[1]
    for y in range(left.size[1]):
        for x in range(left.size[0]):
            color_a = pixels_a[x, y]
            color_b = pixels_b[x, y]
            total += sum((color_a[i] - color_b[i]) ** 2 for i in range(3))
    return (total / count) ** 0.5


def test_isolate_keeps_bright_logo_highlights() -> None:
    image = Image.new("RGBA", (48, 48), (255, 255, 255, 255))
    for x in range(8, 40):
        for y in range(8, 40):
            image.putpixel((x, y), (180, 230, 255, 255))
    mark = isolate_mark(image)
    sample = mark.getpixel((mark.width // 2, mark.height // 2))
    assert sample[3] == 255
    assert sample[2] > 200


def test_isolate_preserves_transparent_png_holes() -> None:
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    for x in range(8, 56):
        for y in range(8, 56):
            image.putpixel((x, y), (0, 140, 200, 255))
    for x in range(24, 40):
        for y in range(24, 40):
            image.putpixel((x, y), (0, 0, 0, 0))
    mark = isolate_mark(image)
    assert mark.getpixel((mark.width // 2, mark.height // 2))[3] == 0
    assert mark.getpixel((4, mark.height // 2))[3] == 255


def test_isolate_keeps_inner_holes_empty() -> None:
    image = Image.new("RGBA", (64, 64), (255, 255, 255, 255))
    for x in range(8, 56):
        for y in range(8, 56):
            image.putpixel((x, y), (0, 140, 200, 255))
    for x in range(24, 40):
        for y in range(24, 40):
            image.putpixel((x, y), (255, 255, 255, 255))
    for x in range(24, 40):
        image.putpixel((x, 24), (0, 140, 200, 120))
        image.putpixel((x, 39), (0, 140, 200, 120))
    for y in range(24, 40):
        image.putpixel((24, y), (0, 140, 200, 120))
        image.putpixel((39, y), (0, 140, 200, 120))
    mark = isolate_mark(image)
    assert mark.getpixel((mark.width // 2, mark.height // 2))[3] == 0
    assert mark.getpixel((4, mark.height // 2))[3] == 255


def test_isolate_mark_keys_white_and_crops_left_icon() -> None:
    mark = isolate_mark(_lockup())
    assert mark.width < 180
    assert mark.height < 120
    sample = mark.getpixel((mark.width // 2, mark.height // 2))
    assert sample[3] in (0, 255) or sample[2] > sample[0]


def test_gif_transparency_does_not_eat_the_mark(tmp_path: Path) -> None:
    mark = Image.new("RGBA", (80, 80), (255, 255, 255, 0))
    for x in range(16, 64):
        for y in range(16, 64):
            mark.putpixel((x, y), (180, 230, 255, 255))
    dest = tmp_path / "logo.gif"
    save_gif([mark, mark, mark, mark], dest, fps=10, colors=32, pause_frames=0)
    with Image.open(dest) as gif:
        rgba = gif.convert("RGBA")
        sample = rgba.getpixel((40, 40))
        assert sample[3] > 200
        assert sample[0] > 100
        assert rgba.getpixel((2, 2))[3] == 0


def test_fit_square_keeps_aspect_ratio() -> None:
    mark = Image.new("RGBA", (50, 80), (0, 100, 180, 255))
    square = fit_square(mark, 140)
    assert square.size == (140, 140)
    assert square.getpixel((0, 0))[3] == 0


def test_gif_loop_has_rest_frames_and_reasonable_size(tmp_path: Path) -> None:
    mark = fit_square(isolate_mark(_lockup()), 80)
    angles = build_loop(motion_frames=8, pause_frames=4, max_angle=5.0)
    assert angles[0] == pytest.approx(0.0, abs=1e-9)
    assert angles[-1] == pytest.approx(0.0, abs=1e-9)
    assert max(abs(angle) for angle in angles) == pytest.approx(0.0, abs=1e-9)
    frames = render_frames(mark, angles)
    assert len(frames) == 8
    dest = tmp_path / "logo.gif"
    save_gif(frames, dest, fps=12, colors=48, pause_frames=4)
    assert dest.is_file()
    with Image.open(dest) as gif:
        assert gif.format == "GIF"
        assert gif.size == (80, 80)
        assert gif.n_frames >= 4
    assert dest.stat().st_size < 200_000


def test_shine_progress_holds_at_both_ends() -> None:
    assert shine_progress(0, 32) == 0.0
    assert shine_progress(31, 32) == 0.0
    mid = shine_progress(16, 32)
    assert 0.2 < mid < 1.0


def test_shine_frames_are_visibly_different() -> None:
    mark = fit_square(isolate_mark(_lockup()), 80)
    angles = build_loop(motion_frames=24, pause_frames=0, max_angle=0.0)
    frames = render_frames(mark, angles)
    rest = frames[0]
    assert _rms(rest, frames[-1]) < 0.5
    peak_rms = max(_rms(rest, frame) for frame in frames)
    assert peak_rms > 1.5


def test_quantized_gif_keeps_a_visible_sweep(tmp_path: Path) -> None:
    mark = fit_square(isolate_mark(_lockup()), 80)
    frames = render_frames(mark, build_loop(motion_frames=20, pause_frames=0, max_angle=0.0))
    dest = tmp_path / "logo.gif"
    save_gif(frames, dest, fps=10, colors=128, pause_frames=6)
    with Image.open(dest) as gif:
        n_frames = gif.n_frames
        rgb = []
        for index in range(n_frames):
            gif.seek(index)
            rgb.append(gif.convert("RGB"))
    assert n_frames >= 4
    peak_rms = max(_rms(rgb[0], frame) for frame in rgb)
    assert peak_rms > 2.5


def test_gif_keeps_transparent_background(tmp_path: Path) -> None:
    mark = fit_square(isolate_mark(_lockup()), 80)
    frames = render_frames(mark, build_loop(motion_frames=8, pause_frames=0, max_angle=0.0))
    dest = tmp_path / "logo.gif"
    save_gif(frames, dest, fps=10, colors=64, pause_frames=2)
    with Image.open(dest) as gif:
        assert gif.info.get("transparency") is not None
        gif.seek(0)
        rgba = gif.convert("RGBA")
        assert rgba.getpixel((0, 0))[3] == 0
        center = rgba.getpixel((rgba.width // 2, rgba.height // 2))
        assert center[3] > 200
        assert center[2] > center[0]


def test_gif_holds_before_repeating_the_sweep(tmp_path: Path) -> None:
    mark = fit_square(isolate_mark(_lockup()), 80)
    frames = render_frames(mark, build_loop(motion_frames=8, pause_frames=0, max_angle=0.0))
    dest = tmp_path / "logo.gif"
    save_gif(frames, dest, fps=10, colors=32, pause_frames=12)
    with Image.open(dest) as gif:
        gif.seek(gif.n_frames - 1)
        assert gif.info.get("duration") >= 3000

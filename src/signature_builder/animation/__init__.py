"""One-time brand asset pipeline: isolate logo, render GIF, draw contact icons."""

from signature_builder.animation.frame_generator import build_loop, render_frames
from signature_builder.animation.gif_optimizer import save_gif
from signature_builder.animation.logo_processor import fit_square, isolate_mark, load_logo

__all__ = [
    "build_loop",
    "fit_square",
    "isolate_mark",
    "load_logo",
    "render_frames",
    "save_gif",
]

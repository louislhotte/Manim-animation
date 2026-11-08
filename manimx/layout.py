"""Frame safety: nothing off-screen, nothing in the header's way.

The frame is ``x in [-7.11, 7.11]``, ``y in [-4, 4]``; keep content at least
``SAFE`` units from every edge (``edgecheck.py`` flags anything closer). The
section header owns the top-left corner, captions own the bottom band.
"""

from __future__ import annotations

from manim import config

SAFE = 0.35  # minimum margin from every frame edge
HEADER_CLEAR_Y = 2.6  # top of the content area under a section header
CAPTION_Y = -3.42  # baseline band of the running bottom caption
CAPTION_W = 12.6  # captions are clamped to this width


def frame_w() -> float:
    return config.frame_width


def frame_h() -> float:
    return config.frame_height


def keep_inside(mob, margin=SAFE):
    """Shift ``mob`` (no scaling) so its bounding box sits inside the safe area."""
    xr, yr = config.frame_x_radius - margin, config.frame_y_radius - margin
    dx = max(0.0, -xr - mob.get_left()[0]) - max(0.0, mob.get_right()[0] - xr)
    dy = max(0.0, -yr - mob.get_bottom()[1]) - max(0.0, mob.get_top()[1] - yr)
    return mob.shift([dx, dy, 0])


def fit_in_frame(mob, margin=SAFE):
    """Scale ``mob`` down (never up) to fit the safe area, then keep it inside."""
    max_w = config.frame_width - 2 * margin
    max_h = config.frame_height - 2 * margin
    f = min(
        1.0,
        max_w / mob.width if mob.width else 1.0,
        max_h / mob.height if mob.height else 1.0,
    )
    if f < 1.0:
        mob.scale(f)
    return keep_inside(mob, margin)

"""Small reusable glyphs: chips, pills, arrows, ticks, stamps.

These are the most-copied helpers of the older films, in their most common
form. They are deliberately plain: the *hero visual* of a scene (a heatmap, a
graph, a chart, the real data structure) is film-specific and should carry
the explanation; these only label and connect it.
"""

from __future__ import annotations

import numpy as np
from manim import (
    RIGHT,
    Arrow,
    Dot,
    Line,
    Mobject,
    RoundedRectangle,
    VGroup,
    VMobject,
)

from .palette import BAD, BG, GOOD, INK, MUTED
from .text import Text, txt


def chip(text, color, fs=20, fill=0.14, w=None, h=0.56, tcolor=None, weight="NORMAL", radius=0.12):
    """A tinted rounded box with a centred label that auto-fits.

    Width hugs the label unless ``w`` is given. ``g.box`` / ``g.label`` expose
    the parts (e.g. ``g.box.animate.set_stroke(BAD)``).
    """
    label = txt(text, fs=fs, color=tcolor or INK, weight=weight)
    width = label.width + 0.5 if w is None else w
    if label.width > width - 0.3:
        label.scale((width - 0.3) / label.width)
    box = RoundedRectangle(
        width=width, height=h, corner_radius=radius,
        stroke_color=color, stroke_width=2.5, fill_color=color, fill_opacity=fill,
    )
    label.move_to(box)
    g = VGroup(box, label)
    g.box = box
    g.label = label
    return g


def pill(text, color, fs=22, fill=0.16, weight="BOLD"):
    """A coloured tag (column headers, legends, "HIT" / "MISS" badges)."""
    t = txt(text, fs=fs, color=color, weight=weight)
    box = RoundedRectangle(
        width=t.width + 0.44, height=t.height + 0.26, corner_radius=0.13,
        stroke_color=color, stroke_width=2, fill_color=color, fill_opacity=fill,
    )
    box.move_to(t)
    return VGroup(box, t)


def stamp(text, color, fs=40):
    """A tilted rubber stamp: ``stamp("BLOCKED", BAD)``. Land it with ``FadeIn(scale=1.4)``."""
    t = txt(text, fs=fs, color=color, weight="BOLD")
    box = RoundedRectangle(
        width=t.width + 0.5, height=t.height + 0.36, corner_radius=0.14,
        stroke_color=color, stroke_width=5, fill_opacity=0,
    )
    t.move_to(box)
    return VGroup(box, t).rotate(-0.16)


def plate(mob, pad_x=0.14, pad_y=0.09, op=0.72):
    """Put a background-coloured plate behind ``mob`` so it reads over wires/grids."""
    bg = RoundedRectangle(
        width=mob.width + 2 * pad_x, height=mob.height + 2 * pad_y, corner_radius=0.08,
        stroke_width=0, fill_color=BG, fill_opacity=op,
    ).move_to(mob)
    return VGroup(bg, mob)


def _point(p, which):
    if isinstance(p, Mobject):
        raise TypeError(
            f"arr() {which} must be a point, got a {type(p).__name__}. Pass an edge "
            "point such as box.get_right(): Arrow(mobject, mobject) resolves "
            "endpoints from the raw bezier cloud and comes out diagonal."
        )
    return p


def arr(a, b, color=MUTED, sw=4, buff=0.12, tip=0.2):
    """A straight arrow between two *points* (``box.get_right()``, never ``box``)."""
    return Arrow(
        _point(a, "start"), _point(b, "end"), buff=buff, stroke_width=sw, color=color,
        max_tip_length_to_length_ratio=0.35, tip_length=tip,
    )


def wire(a, b, color=MUTED, sw=2.0, op=0.85):
    """A plain connecting line (no head), for many-to-many wiring."""
    return Line(_point(a, "start"), _point(b, "end"), stroke_width=sw, color=color).set_stroke(opacity=op)


def make_tick(color=GOOD, sw=7, scale=1.0):
    """A hand-drawn check mark."""
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])]
    )
    return v.set_stroke(color=color, width=sw).scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    """A hand-drawn cross."""
    a = Line([-0.18, -0.18, 0], [0.18, 0.18, 0])
    b = Line([-0.18, 0.18, 0], [0.18, -0.18, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


def dot_label(text, color, fs=24):
    """A coloured dot followed by a label: legends and key rows."""
    d = Dot(radius=0.08, color=color)
    t = Text(text, font_size=fs, color=INK).next_to(d, RIGHT, buff=0.2)
    return VGroup(d, t)

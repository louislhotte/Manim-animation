"""Data as pictures: the primitives behind the series' strongest scenes.

What separates the films viewers love (Transformer, KV Cache, Mixtral, Neural
Network) from the ones that feel like slides is that the *data structure is
the visual*: an embedding is a column of cells, attention is a heatmap, a
prediction is a row of probability bars, and the numbers move. Build scenes
from these, fed with real computed values, instead of boxes with labels.

All of them are LaTeX-free (no ``DecimalNumber``/``MathTex``).
"""

from __future__ import annotations

import numpy as np
from manim import DOWN, RIGHT, Rectangle, Square, VGroup, always_redraw

from .palette import AMBER, BG, INK, MUTED
from .text import Text


def _norm(values, lo, hi):
    v = np.asarray(values, dtype=float)
    span = float(v.max() - v.min())
    z = (v - v.min()) / span if span > 0 else np.full_like(v, 0.5)
    return lo + z * (hi - lo)


def heatmap(values, color, cell=0.3, gap=0.04, lo=0.08, hi=0.95, stroke=BG):
    """A matrix as a grid of squares whose fill opacity encodes the value.

    ``values`` is 2-D (rows x cols). Returns a ``VGroup`` of rows; address a
    cell as ``grid[r][c]``. Opacity is min-max normalised into ``[lo, hi]``.
    """
    ops = _norm(values, lo, hi)
    grid = VGroup()
    for r in range(ops.shape[0]):
        row = VGroup()
        for c in range(ops.shape[1]):
            s = Square(side_length=cell, stroke_width=1, stroke_color=stroke)
            s.set_fill(color, opacity=float(ops[r, c]))
            row.add(s)
        row.arrange(RIGHT, buff=gap)
        grid.add(row)
    grid.arrange(DOWN, buff=gap)
    return grid


def vcells(values, color, cw=0.2, lo=0.2, hi=0.9, stroke=BG, sw=1.0):
    """A vector as a vertical stack of cells (an embedding, a K or V column).

    ``values`` is a 1-D sequence, or an int ``n`` for ``n`` random cells
    (illustration only: prefer real values).
    """
    if isinstance(values, int):
        values = np.random.default_rng(values).uniform(size=values)
    ops = _norm(values, lo, hi)
    cells = VGroup()
    for o in ops:
        s = Square(side_length=cw, stroke_width=sw, stroke_color=stroke)
        s.set_fill(color, opacity=float(o))
        cells.add(s)
    return cells.arrange(DOWN, buff=0)


def prob_bars(items, unit=3.2, fs=22, color=AMBER, gap=0.52, fmt="{:.2f}"):
    """Right-aligned labels + horizontal bars + value readouts.

    ``items`` is ``[(label, p), ...]``; bar length is ``unit * p``. Each row is
    ``VGroup(label, bar, value)`` so rows can be highlighted or re-grown.
    """
    grp = VGroup()
    for i, (name, p) in enumerate(items):
        y = -i * gap
        lab = Text(name, font_size=fs, color=INK)
        lab.move_to([-lab.width / 2 - 0.2, y, 0])
        bw = max(0.03, unit * p)
        bar = Rectangle(
            width=bw, height=0.36, stroke_width=0, fill_color=color, fill_opacity=0.9
        )
        bar.move_to([0.2 + bw / 2, y, 0])
        val = Text(fmt.format(p), font_size=fs - 5, color=MUTED).next_to(
            bar, RIGHT, buff=0.15
        )
        grp.add(VGroup(lab, bar, val))
    return grp


def live_number(tracker, fmt="{:,.0f}", fs=28, color=INK, anchor=None, **text_kw):
    """A number that follows a ``ValueTracker`` (the LaTeX-free ``DecimalNumber``).

    ``anchor(mob)`` positions each redraw, e.g. ``lambda m: m.next_to(bar, RIGHT)``.
    Never ``Create``/``FadeIn`` the live mobject itself: fade in a static copy,
    then ``add`` the live one (strict-zip crash otherwise).
    """

    def build():
        m = Text(fmt.format(tracker.get_value()), font_size=fs, color=color, **text_kw)
        if anchor is not None:
            anchor(m)
        return m

    return always_redraw(build)

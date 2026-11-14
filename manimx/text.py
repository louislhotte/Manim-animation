"""Crisp text: the #1 house rule, implemented once.

Manim's ``Text`` (Pango) mangles letter and word spacing below ~20 pt and can
fall back to a different font for small glyphs (sub/superscripts). The fix is
to rasterise every glyph at a large base size and scale the mobject *down*.
Importing ``manimx`` shadows ``Text`` with that behaviour, so every call in a
film benefits, including the small pieces ``mtext`` builds.

It also sets the house font (Helvetica Neue) as the default. Without it Pango
silently falls back to a serif, which is why half the older films looked
inconsistent. Override with the ``MX_FONT`` env var (empty = Pango default).
"""

from __future__ import annotations

import os

from manim import DEFAULT_FONT_SIZE, DOWN, RIGHT, UP, VGroup, VMobject
from manim import Text as BaseText

from .palette import FONT, INK, MONO

_BaseText = BaseText  # legacy name used by older films
TEXT_BASE = 60
_TEXT_BASE = TEXT_BASE

_font = os.environ.get("MX_FONT", FONT)
if _font:
    BaseText.set_default(font=_font)


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: N802 - shadows manim.Text
    """``manim.Text`` rendered at >= 60 pt and scaled down: correct spacing and font."""
    if font_size >= TEXT_BASE:
        return BaseText(text, font_size=font_size, **kw)
    return BaseText(text, font_size=TEXT_BASE, **kw).scale(font_size / TEXT_BASE)


def txt(text, fs=24, color=INK, weight="NORMAL", font=None, slant=None, **extra):
    """Short-hand ``Text`` that drops ``font=None`` / ``slant=None`` (Pango chokes on them)."""
    kw = {"font_size": fs, "color": color, "weight": weight}
    if font:
        kw["font"] = font
    if slant:
        kw["slant"] = slant
    kw.update(extra)
    return Text(text, **kw)


def mono(text, fs=22, color=INK, **kw):
    """Monospaced text (Menlo): code, identifiers, aligned numbers."""
    return txt(text, fs=fs, color=color, font=MONO, **kw)


LINE_UP, LINE_DOWN = 1.42, 0.42  # a line box, in cap heights above / below the baseline


class _Strut(VMobject):
    """An invisible vertical segment that only gives its group a height. Its stroke
    width stays 0 whatever style the group is given (``Write`` strokes outlines)."""

    def __init__(self, bottom, top):
        super().__init__(stroke_width=0, fill_opacity=0)
        self.set_points_as_corners([bottom, top])

    def set_stroke(
        self, color=None, width=None, opacity=None, background=False, family=True
    ):
        return super().set_stroke(
            color=color, width=0, opacity=opacity, background=background, family=family
        )


def line_txt(text, fs=24, color=INK, **kw):
    """``txt`` in a box as tall as its *line*, so pieces placed by their boxes share
    a baseline.

    Manim places a mobject by its bounding box, and a ``Text``'s box hugs its glyphs:
    "0", "none yet" and "1,000" centred on the same y sit on three baselines, and a
    column of names wobbles with their descenders. This returns ``VGroup(text,
    strut)`` whose height depends only on the font and the size (``LINE_UP`` cap
    heights above the baseline, ``LINE_DOWN`` below), and whose centre is the middle
    of a capital letter. Use it for rows and columns of text (tables, legends, log
    lines, a label over a value) and for a value that changes in place: ``move_to``,
    ``arrange`` and ``next_to`` then line the text up, not its ink. Pieces of
    different sizes in one row: ``align_baselines``. ``.body`` is the Text.
    """
    t = txt("H" + text, fs=fs, color=color, **kw)  # the H is a ruler: it sits on the
    h = t.submobjects[0]  # baseline and is one cap height tall
    cap, base = h.height, h.get_bottom()[1]
    t.remove(h)
    x = t.get_left()[0] if t.submobjects else h.get_left()[0]
    g = VGroup(t, _Strut([x, base - LINE_DOWN * cap, 0], [x, base + LINE_UP * cap, 0]))
    g.body = t
    return g


def baseline_of(line):
    """The y of the baseline of a ``line_txt``."""
    strut = line.submobjects[-1]
    return strut.get_bottom()[1] + strut.height * LINE_DOWN / (LINE_UP + LINE_DOWN)


def align_baselines(*lines):
    """Shift each ``line_txt`` vertically onto the baseline of the first; returns them
    as a ``VGroup``. For a row that mixes sizes (a big number, then a small unit)."""
    y = baseline_of(lines[0])
    for m in lines[1:]:
        m.shift(UP * (y - baseline_of(m)))
    return VGroup(*lines)


def mtext(parts, base_fs=32):
    """An inline "formula" from ``Text`` pieces, so no LaTeX is needed.

    ``parts`` is a list of ``(s, role[, color])`` with role ``"b"`` (base),
    ``"^"`` (superscript) or ``"_"`` (subscript)::

        mtext([("x", "b"), ("t", "_"), (" = r", "b"), ("2", "^")])

    Siblings are separated by real gaps: Pango trims leading/trailing spaces,
    so pad spaces inside a piece do nothing at its edges.
    """
    grp = VGroup()
    last_base = None
    for p in parts:
        s, role = p[0], p[1]
        col = p[2] if len(p) > 2 else INK
        if role == "b":
            m = Text(s, font_size=base_fs, color=col)
            if len(grp) > 0:
                m.next_to(grp, RIGHT, buff=0.05, aligned_edge=DOWN)
            grp.add(m)
            last_base = m
        else:
            m = Text(s, font_size=int(base_fs * 0.6), color=col)
            anchor = last_base if last_base is not None else grp
            m.next_to(anchor, RIGHT, buff=0.02)
            m.align_to(anchor, UP if role == "^" else DOWN)
            grp.add(m)
    return grp


def safe_t2c(s, table):
    """The subset of a ``t2c`` colour table that is safe for string ``s``.

    ``Text(t2c=...)`` raises when two coloured substrings overlap (``setUser``
    inside ``setUserId``), even with equal colours. Keep only the keys present
    in ``s`` that are not a substring of another present key.
    """
    present = {k: v for k, v in table.items() if k in s}
    keys = list(present)
    return {
        k: v for k, v in present.items() if not any(k != o and k in o for o in keys)
    }


_safe_t2c = safe_t2c  # legacy name


def clamp_width(mob, max_w, about_edge=None):
    """Scale ``mob`` down (never up) so it is at most ``max_w`` wide."""
    if mob.width > max_w:
        if about_edge is None:
            mob.scale_to_fit_width(max_w)
        else:
            mob.scale(max_w / mob.width, about_point=mob.get_edge_center(about_edge))
    return mob

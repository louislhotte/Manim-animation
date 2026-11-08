"""Code panels: real code, set in Menlo, inside an editor-like window.

Showing the *real* API (a real ``nginx.conf``, a real ``StateGraph``) and
syncing a line highlight with the diagram it drives is one of the strongest
devices in the series (see LangGraph, ReactHooks). ``code_panel`` builds the
window; ``hl_lines`` builds the highlight bar; ``ExplainerMixin.focus`` moves
one highlight from line to line.
"""

from __future__ import annotations

from manim import DOWN, ITALIC, LEFT, RIGHT, UP, Dot, Rectangle, RoundedRectangle, VGroup

from .palette import CODE_BAR, CODE_BG, FAINT, GOLD, MONO, MUTED
from .text import Text, safe_t2c, txt

PLAIN = "#D6DEEB"  # default code text
COMMENT = "#5F6B7E"  # comments (grey-blue)
KW = "#C792EA"  # keywords
STR = "#C3E88D"  # string literals
FUNC = "#82AAFF"  # function / method names
NUM = "#F78C6C"  # numeric literals
CODE_FS = 19


def code_panel(
    spec,
    table=None,
    title="main.py",
    fs=CODE_FS,
    indent_unit=0.44,
    line_buff=0.15,
    target_h=5.9,
    target_w=6.6,
    comment="#",
):
    """An editor window around ``spec``; returns ``(panel, lines)``.

    ``spec`` is a list of ``(indent_level, text)``; ``""`` is a blank line.
    ``table`` is a ``t2c`` map (token -> colour) applied safely per line; lines
    starting with ``comment`` render italic in ``COMMENT``. The code is scaled
    down (never up) to fit ``target_w`` x ``target_h``. ``panel.code`` is the
    lines group; ``lines[i]`` addresses one line for ``hl_lines``.
    """
    table = table or {}
    lines = []
    for indent, s in spec:
        if s == "":
            m = Rectangle(width=0.02, height=0.26, fill_opacity=0, stroke_opacity=0)
        elif comment and s.lstrip().startswith(comment):
            m = txt(s, fs=fs, color=COMMENT, font=MONO, slant=ITALIC)
        else:
            m = Text(s, font=MONO, font_size=fs, color=PLAIN, t2c=safe_t2c(s, table))
        m._indent = indent
        lines.append(m)
    code = VGroup(*lines).arrange(DOWN, aligned_edge=LEFT, buff=line_buff)
    for m in lines:
        m.shift(RIGHT * indent_unit * m._indent)
    f = min(target_h / code.height, target_w / code.width)
    if f < 1:
        code.scale(f)

    bg = RoundedRectangle(
        width=code.width + 0.9, height=code.height + 1.15, corner_radius=0.16,
        stroke_color=FAINT, stroke_width=2, fill_color=CODE_BG, fill_opacity=1.0,
    )
    bg.move_to(code)
    bar = RoundedRectangle(
        width=bg.width, height=0.5, corner_radius=0.16,
        stroke_width=0, fill_color=CODE_BAR, fill_opacity=1.0,
    )
    # centre first: the indent-shifted code re-centres bg, so align_to(UP)
    # alone would leave the title bar offset in x.
    bar.move_to(bg).align_to(bg, UP)
    dots = VGroup(
        *[Dot(radius=0.045, color=c) for c in ("#FF5F57", "#FEBC2E", "#28C840")]
    ).arrange(RIGHT, buff=0.11)
    dots.move_to([bg.get_left()[0] + 0.42, bar.get_center()[1], 0])
    ttl = txt(title, fs=15, color=MUTED, font=MONO)
    if ttl.width > bg.width - 1.5:
        ttl.scale_to_fit_width(bg.width - 1.5)
    ttl.next_to(dots, RIGHT, buff=0.34).set_y(bar.get_center()[1])
    code.shift(DOWN * 0.2)  # clear the title bar
    panel = VGroup(bg, bar, dots, ttl, code)
    panel.code = code
    return panel, lines


def hl_lines(panel, lines, idxs, color=GOLD, opacity=0.16, pad=0.05, xpad=0.34):
    """A translucent bar spanning ``lines[idxs]`` across the panel width."""
    tops = [lines[i].get_top()[1] for i in idxs]
    bots = [lines[i].get_bottom()[1] for i in idxs]
    y_hi, y_lo = max(tops) + pad, min(bots) - pad
    rect = RoundedRectangle(
        width=panel[0].width - xpad, height=y_hi - y_lo, corner_radius=0.08,
        stroke_width=0, fill_color=color, fill_opacity=opacity,
    )
    rect.move_to([panel[0].get_center()[0], (y_hi + y_lo) / 2, 0])
    return rect

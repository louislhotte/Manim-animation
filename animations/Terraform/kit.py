"""kit.py: the 2D building blocks of the Terraform film (built on manimx).

* ``TextPanel``  an editor / terminal window whose lines are laid out every frame
                 from plain attributes: blocks fold and unfold (``Fold.open``), lines
                 appear (``Row.vis``), commands are typed (``Row.typed``), the content
                 scrolls (``scroll``), highlight bars and dependency arcs follow the
                 lines they are attached to. ``Tween`` animates all of it.
* ``ResCard``    a resource as a node: icon, address, a progress bar.
* icons          one flat glyph per resource type, echoing the 3D stage.

Text is coloured per character by small tokenizers (``hcl_colors``,
``term_colors``): no ``t2c`` substring matching, so ``"web"`` inside another string
never gets the wrong colour.
"""

from __future__ import annotations

import math
import re

import numpy as np
from manimx import *

from stage import BUCKET_C, SERVER_C, SG_C, SUBNET_C, VPC_C

# ---- colours ---------------------------------------------------------------- #
ADD_C, CHANGE_C, DESTROY_C = GOOD, GOLD, BAD  # the plan's + ~ - (as the CLI prints)
REF_C = "#7FB4FF"  # a reference to another block
ATTR_C = "#B8C4DA"  # argument names
PUNCT_C = "#7E8AA3"  # = { } [ ]
WINDOW_BG = "#0B1018"
WINDOW_BAR = "#151D2B"
TERM_BG = "#080C12"
KIND_C = {
    "aws_vpc": VPC_C,
    "aws_subnet": SUBNET_C,
    "aws_security_group": SG_C,
    "aws_instance": SERVER_C,
    "aws_s3_bucket": BUCKET_C,
}

_ADV: dict[int, float] = {}


def char_adv(fs):
    """The advance of one Menlo character at font size ``fs`` (scene units)."""
    if fs not in _ADV:
        t = Text("M" * 41, font=MONO, font_size=fs, disable_ligatures=True)
        _ADV[fs] = float(t[40].get_center()[0] - t[0].get_center()[0]) / 40
    return _ADV[fs]


# --------------------------------------------------------------------------- #
# per-character colours
# --------------------------------------------------------------------------- #
_HCL_KW = (
    "resource",
    "provider",
    "module",
    "variable",
    "terraform",
    "backend",
    "required_providers",
    "output",
    "data",
)


def hcl_colors(s):
    """A colour for every character of one line of Terraform configuration."""
    out = [PLAIN] * len(s)

    def paint(a, b, c):
        out[a:b] = [c] * (b - a)

    if s.lstrip().startswith("#"):
        return [COMMENT] * len(s)
    for m in re.finditer(r"[={}\[\],]", s):
        paint(m.start(), m.end(), PUNCT_C)
    m = re.match(r"\s*(\w+)\s*=", s)
    if m:
        paint(m.start(1), m.end(1), ATTR_C)
    m = re.match(r"\s*(\w+)\b", s)
    if m and m.group(1) in _HCL_KW:
        paint(m.start(1), m.end(1), KW)
    for m in re.finditer(r"\b(aws_\w+\.\w+(?:\.\w+)?|var\.\w+)", s):
        paint(m.start(), m.end(), REF_C)
    for m in re.finditer(r"(?<![\w.\"-])\d+\b(?![\w.\"-])", s):
        paint(m.start(), m.end(), NUM)
    for m in re.finditer(r"\b(true|false)\b", s):
        paint(m.start(), m.end(), NUM)
    for m in re.finditer(r'"[^"]*"', s):
        paint(m.start(), m.end(), STR)
    for m in re.finditer(r"[…]", s):
        paint(m.start(), m.end(), MUTED)
    return out


def term_colors(s):
    """Terraform's own terminal colours: green ``+``, yellow ``~``, red ``-``."""
    out = [PLAIN] * len(s)

    def paint(a, b, c):
        out[a:b] = [c] * (b - a)

    t = s.lstrip()
    lead = len(s) - len(t)
    if t.startswith("$ "):
        paint(lead, lead + 1, MUTED)
        paint(lead + 2, len(s), INK)
        return out
    if t.startswith("#"):
        paint(0, len(s), INK if "forces replacement" not in t else DESTROY_C)
        return out
    if t.startswith("…"):
        return [MUTED] * len(s)
    if t.startswith("Plan:"):  # the CLI prints the summary plain: no coloured counts
        return [INK] * len(s)
    if t.startswith("No changes."):
        paint(0, len(s), INK)
        paint(lead, lead + len("No changes."), ADD_C)
        return out
    # "Apply complete! ..." is green from end to end (also when a narrow terminal
    # wraps it onto a second line)
    if t.startswith("Apply complete!") or re.fullmatch(
        r"(\d+ added, )?\d+ changed, \d+ destroyed\.", t
    ):
        return [ADD_C] * len(s)
    if "Error" in t or t.startswith("│"):
        paint(0, len(s), PLAIN)
        for m in re.finditer(r"Error:?[^│]*", s):
            paint(m.start(), m.end(), DESTROY_C)
        for m in re.finditer(r"[│╷╵]", s):
            paint(m.start(), m.end(), DESTROY_C)
        return out
    if t.startswith("-/+"):
        paint(lead, lead + 1, DESTROY_C)
        paint(lead + 1, lead + 2, MUTED)
        paint(lead + 2, lead + 3, ADD_C)
    elif t[:2] in ("+ ", "~ ", "- "):
        paint(lead, lead + 1, {"+": ADD_C, "~": CHANGE_C, "-": DESTROY_C}[t[0]])
    for m in re.finditer(r'"[^"]*"', s):
        paint(m.start(), m.end(), STR)
    for m in re.finditer(r"->", s):
        paint(m.start(), m.end(), CHANGE_C)
    for m in re.finditer(r"\(known after apply\)", s):
        paint(m.start(), m.end(), MUTED)
    for m in re.finditer(r"# forces replacement", s):
        paint(m.start(), m.end(), DESTROY_C)
    for m in re.finditer(r"(Creation|Modifications|Destruction) complete", s):
        paint(m.start(), m.end(), ADD_C)
    for m in re.finditer(r"\[id=[^\]]*\]", s):
        paint(m.start(), m.end(), MUTED)
    for m in re.finditer(r"[…]", s):
        paint(m.start(), m.end(), MUTED)
    return out


def shell_colors(s):
    """An AWS CLI script: the verbs (the *steps*) stand out."""
    out = [PLAIN] * len(s)

    def paint(a, b, c):
        out[a:b] = [c] * (b - a)

    for m in re.finditer(r"--[\w-]+", s):
        paint(m.start(), m.end(), MUTED)
    for m in re.finditer(r"\b(create-[\w-]+|run-instances|wait)\b", s):
        paint(m.start(), m.end(), AMBER)
    for m in re.finditer(r"\$\w+|\$\(|\)$|^\w+=", s):
        paint(m.start(), m.end(), REF_C)
    for m in re.finditer(r"\.\.\.", s):
        paint(m.start(), m.end(), MUTED)
    return out


# --------------------------------------------------------------------------- #
# rows, folds, the panel
# --------------------------------------------------------------------------- #
class Row:
    """One line of monospaced text. ``mob`` holds one glyph per character.

    ``vis``    0..1: the share of a line's height the row takes (it appears by
               pushing the following rows down);
    ``alpha``  an extra fade;
    ``typed``  how many characters are shown (``None`` = all): a typed command;
    ``fold``   the ``Fold`` this row is the body of (hidden while it is closed).
    """

    def __init__(self, text, fs, colors=hcl_colors, weight="NORMAL"):
        self.text = text
        body = text.lstrip(" ")
        self.lead = len(text) - len(body)
        self.fs = fs
        # a strut in front: every row then has the same box, whatever its letters
        self.mob = Text(
            "|" + (body or " "),
            font=MONO,
            font_size=fs,
            color=PLAIN,
            weight=weight,
            disable_ligatures=True,
        )
        self.strut = self.mob[0]
        self.strut.set_opacity(0)
        self.glyphs = list(self.mob[1 : 1 + len(body)])
        for g, c in zip(self.glyphs, colors(text)[self.lead :], strict=False):
            g.set_fill(c)
            g.set_stroke(c)
        self.galpha = np.ones(len(self.glyphs))  # per-glyph fade (token swaps, folds)
        self.vis, self.alpha, self.typed = 1.0, 1.0, None
        self.dy = 0.0  # lines above (+) / below (-) its slot: blocks changing places
        self.fold = None
        self.role = "line"  # line | head | body | closer
        self.marks = []  # (mobject, attr holder) riding at the right edge
        self.y = 0.0  # set by the panel's layout
        self.op = -1.0
        self._seen = None

    def col(self, sub, nth=0):
        """(start, end) character columns of the ``nth`` occurrence of ``sub``."""
        i = -1
        for _ in range(nth + 1):
            i = self.text.index(sub, i + 1)
        return i, i + len(sub)

    def span(self, sub, nth=0):
        """The glyphs of a substring (for braces, underlines, arrows)."""
        a, b = self.col(sub, nth)
        gs = [g for g in self.glyphs[a - self.lead : b - self.lead] if g.has_points()]
        return VGroup(*gs)

    def n_chars(self):
        return len(self.glyphs)


class Fold:
    """A block that folds: a head line, body lines, a closing line. ``open`` in
    [0, 1]. Folded, the head ends in ``…}``; unfolding fades that out."""

    def __init__(self, head, body, closer):
        self.head, self.body, self.closer = head, body, closer
        self.open = 0.0
        self.glow = 0.0  # 0..1: a highlight over the whole block

    @property
    def rows(self):
        return [self.head, *self.body, self.closer]


class Mark:
    """A small mobject riding on a row, at the right edge of the panel."""

    def __init__(self, mob, alpha=0.0, dx=0.0):
        self.mob, self.alpha, self.dx = mob, alpha, dx
        self.base = [
            (m, m.get_fill_opacity(), m.get_stroke_opacity())
            for m in mob.family_members_with_points()
        ]


class Bar:
    """A highlight bar spanning rows ``a`` .. ``b`` (it follows them)."""

    def __init__(self, a, b, color=GOLD, alpha=0.0, op=0.16):
        self.a, self.b, self.color, self.alpha, self.op = a, b, color, alpha, op
        self.mob = RoundedRectangle(
            width=1, height=1, corner_radius=0.06, stroke_width=0, fill_color=color
        )
        self.mob.set_fill(opacity=0)


class Link:
    """A dependency arc in the gutter, from row ``a`` (which references) to row
    ``b`` (what it references). ``grow`` in [0, 1] draws it; ``lane`` nests arcs."""

    def __init__(self, a, b, color=REF_C, lane=0):
        self.a, self.b, self.color, self.lane = a, b, color, lane
        self.grow, self.alpha = 0.0, 1.0
        self.path = VMobject(stroke_color=color, stroke_width=2.6)
        self.tip = Triangle(fill_color=color, fill_opacity=1, stroke_width=0)
        self.mob = VGroup(self.path, self.tip)


class TextPanel(VGroup):
    """An editor or terminal window. ``n`` lines are visible; content beyond is
    clipped (rows fade at the edges) and reached with ``scroll`` (in lines)."""

    PAD_X, PAD_Y = 0.24, 0.16

    def __init__(
        self,
        cols,
        n,
        title="main.tf",
        fs=18,
        kind="editor",
        pitch=None,
        bar_h=0.40,
        gutter=None,
        w=None,
    ):
        super().__init__()
        self.kind, self.fs, self.n = kind, fs, n
        self.adv = char_adv(fs)
        self.pitch = pitch or fs * 0.0205
        self.gutter = (0.34 if kind == "editor" else 0.0) if gutter is None else gutter
        self.w0 = w or (cols * self.adv + 2 * self.PAD_X + self.gutter)
        self.h0 = bar_h + n * self.pitch + 2 * self.PAD_Y
        self.bar_h = bar_h
        self.scroll = 0.0
        self.rows: list[Row] = []
        self.folds: list[Fold] = []
        self.bars: list[Bar] = []
        self.links: list[Link] = []
        self.active = None  # the row the terminal cursor sits on
        self.t = 0.0
        self.px = self.py = (
            None  # set by anchor(): then Tween(px=, py=) slides the window
        )
        self.cursor_on = kind == "terminal"

        bg = RoundedRectangle(
            width=self.w0,
            height=self.h0,
            corner_radius=0.14,
            stroke_color=FAINT,
            stroke_width=2,
            fill_color=WINDOW_BG if kind == "editor" else TERM_BG,
            fill_opacity=1.0,
        )
        bar = RoundedRectangle(
            width=self.w0,
            height=bar_h,
            corner_radius=0.14,
            stroke_width=0,
            fill_color=WINDOW_BAR,
            fill_opacity=1.0,
        )
        bar.move_to(bg).align_to(bg, UP)
        dots = VGroup(
            *[Dot(radius=0.042, color=c) for c in ("#FF5F57", "#FEBC2E", "#28C840")]
        ).arrange(RIGHT, buff=0.10)
        dots.move_to([bg.get_left()[0] + 0.36, bar.get_center()[1], 0])
        ttl = txt(title or "-", fs=15, color=MUTED, font=MONO)
        ttl.next_to(dots, RIGHT, buff=0.28).set_y(bar.get_center()[1])
        if not bar_h:  # a bare strip: no title bar
            for m in (bar, dots, ttl):
                m.set_opacity(0)
        self.bg, self.bar, self.dots, self.ttl = bg, bar, dots, ttl
        self.hl_layer = VGroup()  # highlight bars sit under the text
        self.text_layer = VGroup()
        self.link_layer = VGroup()
        self.cursor = Rectangle(
            width=self.adv * 0.92,
            height=self.pitch * 0.74,
            stroke_width=0,
            fill_color=INK,
            fill_opacity=0.0,
        )
        self.add(bg, bar, dots, ttl, self.hl_layer, self.link_layer, self.text_layer)
        self.add(self.cursor)
        self.add_updater(TextPanel._tick)

    # ---- content -------------------------------------------------------------- #
    def _colors(self):
        return hcl_colors if self.kind == "editor" else term_colors

    def line(self, text, vis=1.0, colors=None, weight="NORMAL", index=None):
        """Append (or insert) one line; returns its ``Row``."""
        r = Row(text, self.fs, colors or self._colors(), weight=weight)
        r.vis = vis
        if index is None:
            self.rows.append(r)
        else:
            self.rows.insert(index, r)
        self._adopt(r.mob, self.text_layer)
        return r

    def _adopt(self, mob, layer):
        """Add ``mob`` to a layer at the panel's z-index (a panel raised with
        ``set_z_index`` would otherwise draw later content under its window)."""
        mob.set_z_index(self.bg.z_index)
        layer.add(mob)
        return mob

    def lines(self, texts, vis=1.0, **kw):
        return [self.line(t, vis=vis, **kw) for t in texts]

    def block(self, texts, open=0.0, index=None, vis=1.0):
        """A foldable block from its source lines (head, body..., closing brace).
        ``index`` inserts it before the row at that position (default: at the end);
        with ``vis=0`` its head is hidden until ``show([fold.head])``."""
        at = len(self.rows) if index is None else index
        head = self.line(texts[0] + "…}", index=at, vis=vis)
        head.role = "head"
        body = [self.line(t, index=at + 1 + i) for i, t in enumerate(texts[1:-1])]
        closer = self.line(texts[-1], index=at + len(texts) - 1)
        f = Fold(head, body, closer)
        f.open = open
        for r in body:
            r.fold, r.role = f, "body"
        closer.fold, closer.role = f, "closer"
        head.fold = f
        tri = Triangle(fill_color=MUTED, fill_opacity=1, stroke_width=0)
        tri.set_width(0.13)
        f.chevron = tri
        self._adopt(tri, self.text_layer)
        before = sum(
            1 for g in self.folds if self.rows.index(g.head) < self.rows.index(head)
        )
        self.folds.insert(before, f)
        return f

    def reorder(self, folds, run_time=0.9):
        """Put the blocks in a new order; they travel to their new places (and the
        arcs attached to them follow)."""
        self.refresh()
        before = {id(r): r.slot for r in self.rows}
        loose = [r for r in self.rows if r.fold is None]
        assert not loose, "reorder() expects a panel made of blocks only"
        self.rows = [r for f in folds for r in f.rows]
        self.folds = list(folds)
        cum = -self.scroll
        for r in self.rows:
            f = self.row_factor(r)
            r.dy = (cum + f / 2) - before[id(r)]
            cum += f
        self.refresh()
        return AnimationGroup(
            *[
                Tween(r, run_time=run_time, dy=0.0)
                for r in self.rows
                if abs(r.dy) > 1e-6
            ]
        )

    def mark(self, row, mob, alpha=0.0, dx=0.0):
        """Attach a small mobject (a tick, a ``+``) at the right end of ``row``."""
        m = Mark(mob, alpha, dx)
        row.marks.append(m)
        self._adopt(mob, self.text_layer)
        return m

    def bar_over(self, a, b=None, color=GOLD, op=0.16):
        """A highlight bar over rows ``a`` .. ``b`` (fade it in with ``Tween``)."""
        bar = Bar(a, b or a, color, 0.0, op)
        self.bars.append(bar)
        self._adopt(bar.mob, self.hl_layer)
        return bar

    def link(self, a, b, color=REF_C, lane=0):
        """A dependency arc from row ``a`` to row ``b`` in the gutter."""
        ln = Link(a, b, color, lane)
        self.links.append(ln)
        self._adopt(ln.mob, self.link_layer)
        return ln

    # ---- geometry ---------------------------------------------------------------- #
    @property
    def k(self):
        """The panel's current scale (it can be scaled as a whole)."""
        return self.bg.width / self.w0

    def x_text(self):
        return self.bg.get_left()[0] + (self.PAD_X + self.gutter) * self.k

    def y_top(self):
        return self.bg.get_top()[1] - (self.bar_h + self.PAD_Y) * self.k

    def row_factor(self, r):
        f = float(np.clip(r.vis, 0, 1))
        if r.fold is not None and r.role in ("body", "closer"):
            f *= float(np.clip(r.fold.open, 0, 1))
        return f

    def height_in_lines(self, upto=None):
        """How many lines the content takes now (up to row ``upto``, exclusive)."""
        total = 0.0
        for r in self.rows:
            if r is upto:
                break
            total += self.row_factor(r)
        return total

    def row_point(self, row, col=None, edge=0.0):
        """A point on ``row``: at character column ``col`` (default: its start),
        ``edge`` = -1 bottom / 0 middle / +1 top of the line."""
        c = row.lead if col is None else col
        return np.array(
            [
                self.x_text() + c * self.adv * self.k,
                row.y + edge * self.pitch * self.k * 0.5,
                0.0,
            ]
        )

    # ---- layout --------------------------------------------------------------------- #
    @staticmethod
    def _tick(m, dt):
        m.t += dt
        m.refresh()

    def anchor(self):
        """Make the window's place animatable: after this, ``Tween(panel, px=x,
        py=top)`` slides it (centre x, top y) while its content keeps laying out."""
        self.px, self.py = float(self.bg.get_center()[0]), float(self.bg.get_top()[1])
        return self

    def refresh(self):
        k = self.k
        pitch, adv = self.pitch * k, self.adv * k
        if self.px is not None:
            d = np.array(
                [self.px - self.bg.get_center()[0], self.py - self.bg.get_top()[1], 0]
            )
            if np.abs(d).max() > 1e-6:
                for m in (self.bg, self.bar, self.dots, self.ttl):
                    m.shift(d)
        want_h = (self.bar_h + self.n * self.pitch + 2 * self.PAD_Y) * k
        if abs(want_h - self.bg.height) > 1e-4:  # the window was resized (Tween n)
            top, cx = self.bg.get_top()[1], self.bg.get_center()[0]
            new = RoundedRectangle(
                width=self.bg.width, height=want_h, corner_radius=0.14 * k
            )
            new.move_to([cx, top - want_h / 2, self.bg.get_center()[2]])
            self.bg.set_points(new.points)
        x0, y0 = self.x_text(), self.y_top()
        y_bot = y0 - self.n * pitch
        z = self.bg.get_center()[2]
        cum = -self.scroll
        for r in self.rows:
            f = self.row_factor(r)
            r.slot = cum + f / 2  # its place, in lines from the top of the content
            r.y = y0 - (r.slot - r.dy) * pitch
            cum += f
            op = float(np.clip((f - 0.35) / 0.65, 0, 1)) ** 2 * float(
                np.clip(r.alpha, 0, 1)
            )
            top_room = (y0 - (r.y + pitch / 2)) / (0.7 * pitch)
            bot_room = ((r.y - pitch / 2) - y_bot) / (0.7 * pitch)
            op *= float(np.clip(1 + top_room, 0, 1)) * float(
                np.clip(1 + bot_room, 0, 1)
            )
            want = np.array([x0 + (r.lead - 0.5) * adv, r.y, z])
            if np.abs(r.strut.get_center() - want).max() > 1e-6:
                r.mob.shift(want - r.strut.get_center())
            fold_open = (
                r.fold.open if (r.fold is not None and r.role == "head") else None
            )
            seen = (round(op, 4), r.typed, fold_open, r.galpha.tobytes())
            if seen != r._seen:
                r._seen = seen
                r.op = op
                n = len(r.glyphs)
                for i, g in enumerate(r.glyphs):
                    a = op * r.galpha[i]
                    if r.typed is not None and i + r.lead >= r.typed:
                        a = 0.0
                    if (
                        fold_open is not None and i >= n - 2
                    ):  # the "…}" of a folded head
                        a *= float(np.clip(1 - 1.6 * fold_open, 0, 1))
                    g.set_opacity(a)
            for mk in r.marks:
                mk.mob.move_to([self.bg.get_right()[0] - (0.34 + mk.dx) * k, r.y, z])
                a = r.op * float(np.clip(mk.alpha, 0, 1))
                for mob, fo, so in mk.base:
                    mob.set_fill(opacity=fo * a)
                    mob.set_stroke(opacity=so * a)
        for f in self.folds:
            tri = f.chevron
            ang = -PI / 2 - (PI / 2) * float(np.clip(f.open, 0, 1))  # > closed, v open
            c = np.array([self.bg.get_left()[0] + (self.PAD_X + 0.02) * k, f.head.y, z])
            rad = 0.075 * k
            tri.set_points_as_corners(
                [c + rad * np.array([math.cos(ang + j * TAU / 3 + PI / 2),
                                     math.sin(ang + j * TAU / 3 + PI / 2), 0])
                 for j in (0, 1, 2, 0)]
            )  # fmt: skip
            tri.set_fill(mix(MUTED, INK, f.glow), opacity=f.head.op * 0.9)
        left, right = self.bg.get_left()[0], self.bg.get_right()[0]
        for b in self.bars:
            ya, yb = b.a.y + pitch / 2, b.b.y - pitch / 2
            ya, yb = min(ya, y0), max(yb, y_bot)
            h = max(ya - yb, 1e-3)
            b.mob.stretch_to_fit_width(right - left - 0.16 * k)
            b.mob.stretch_to_fit_height(h)
            b.mob.move_to([(left + right) / 2, (ya + yb) / 2, z])
            vis = 1.0 if ya - yb > pitch * 0.3 else 0.0
            b.mob.set_fill(b.color, opacity=b.op * float(np.clip(b.alpha, 0, 1)) * vis)
        for ln in self.links:
            self._draw_link(ln, k, z)
        # the terminal cursor: a block after the last typed character, blinking
        if self.cursor_on and self.active is not None:
            r = self.active
            n = r.n_chars() + r.lead if r.typed is None else r.typed
            self.cursor.stretch_to_fit_width(adv * 0.92)
            self.cursor.stretch_to_fit_height(pitch * 0.74)
            self.cursor.move_to([x0 + (n + 0.5) * adv, r.y, z])
            blink = 0.5 + 0.5 * math.cos(self.t * TAU / 1.1)
            self.cursor.set_fill(
                opacity=(0.25 + 0.65 * blink) * (1.0 if r.op > 0.5 else 0.0)
            )
        else:
            self.cursor.set_fill(opacity=0.0)
        return self

    def _anchor_y(self, row):
        """Where an arc touches ``row``: on its own line when its block is open, on
        the block's head line when it is folded."""
        if row.fold is not None and row.role in ("body", "closer"):
            o = float(np.clip(row.fold.open, 0, 1))
            return row.fold.head.y * (1 - o) + row.y * o
        return row.y

    def _draw_link(self, ln, k, z):
        """An arc outside the panel's left edge: it leaves row ``a`` a little below
        its middle and arrives on row ``b`` a little above, so a row that both
        references and is referenced reads clearly."""
        port = 0.17 * self.pitch * k
        ya, yb = self._anchor_y(ln.a) - port, self._anchor_y(ln.b) + port
        edge = self.bg.get_left()[0]
        x_out = edge - (0.20 + 0.19 * ln.lane) * k
        r = min(0.13 * k, abs(ya - yb) / 2)
        s = 1.0 if yb > ya else -1.0
        tip_len = 0.13 * k
        pts = [np.array([edge, ya, z]), np.array([x_out + r, ya, z])]
        for j in range(1, 7):  # a rounded corner
            a = j / 6 * PI / 2
            pts.append(
                np.array(
                    [x_out + r - r * math.sin(a), ya + s * (r - r * math.cos(a)), z]
                )
            )
        pts.append(np.array([x_out, yb - s * r, z]))
        for j in range(1, 7):
            a = j / 6 * PI / 2
            pts.append(
                np.array(
                    [x_out + r - r * math.cos(a), yb - s * r + s * r * math.sin(a), z]
                )
            )
        pts.append(np.array([edge - tip_len, yb, z]))
        g = float(np.clip(ln.grow, 0, 1))
        full = VMobject().set_points_as_corners(pts)
        if g < 1e-3:
            ln.path.set_points_as_corners([pts[0], pts[0]])
        else:
            ln.path.pointwise_become_partial(full, 0, g)
        op = float(np.clip(ln.alpha, 0, 1))
        ln.path.set_stroke(ln.color, width=2.6, opacity=op * (1.0 if g > 1e-3 else 0.0))
        h = 0.075 * k
        ln.tip.set_points_as_corners(
            [np.array([edge - 0.01 * k, yb, z]), np.array([edge - tip_len, yb + h, z]),
             np.array([edge - tip_len, yb - h, z]), np.array([edge - 0.01 * k, yb, z])]
        )  # fmt: skip
        ln.tip.set_fill(ln.color, opacity=op * float(np.clip((g - 0.9) / 0.1, 0, 1)))

    # ---- animations ------------------------------------------------------------------ #
    def show(self, rows, lag=0.12, each=0.3, scroll=True):
        """Bring hidden rows in, one after the other (they push the next ones down)."""
        rows = list(rows)
        anims = [Tween(r, run_time=each, vis=1.0) for r in rows]
        group = LaggedStart(*anims, lag_ratio=lag / each if each else 0)
        if not scroll:
            return group
        vis = [r.vis for r in rows]
        for r in rows:
            r.vis = 1.0
        target = max(self.scroll, self.height_in_lines() - self.n)
        for r, v in zip(rows, vis, strict=True):
            r.vis = v
        if target <= self.scroll + 1e-6:
            return group
        return AnimationGroup(
            group, Tween(self, run_time=group.run_time, scroll=target)
        )

    def fade_rows(self, rows=None, run_time=0.3):
        """Animations that fade rows out (follow with ``drop`` to forget them)."""
        return [Tween(r, run_time=run_time, alpha=0.0) for r in (rows or self.rows)]

    def drop(self, rows=None):
        """Forget rows that were faded out: what follows moves up. Call between
        plays (a mobject removed mid-play is still drawn until the play ends)."""
        rows = list(self.rows if rows is None else rows)
        for r in rows:
            r.mob.set_opacity(0)
            self.text_layer.remove(r.mob)
            for mk in r.marks:
                mk.mob.set_opacity(0)
                self.text_layer.remove(mk.mob)
            self.rows.remove(r)
        if self.active in rows:
            self.active = None
        if not self.rows:
            self.scroll = 0.0
        return self.refresh()

    def type(self, row, cps=16.0):
        """Type the command of ``row`` (it keeps its prompt)."""
        self.active = row
        n = row.n_chars() + row.lead
        return Tween(
            row,
            run_time=max(0.2, (n - row.typed) / cps),
            rate_func=linear,
            typed=float(n),
        )

    def command(self, text, vis=1.0):
        """A prompt line ``$ text`` with nothing typed yet; returns its row."""
        r = self.line("$ " + text, vis=vis, weight="BOLD")
        r.typed = 2.0
        self.active = r
        return r


class Retype(Animation):
    """Change part of a row's text in place: the old characters leave, then the new
    ones arrive (``2`` -> ``3``, ``"t3.micro"`` -> ``"t3.small"``)."""

    def __init__(self, panel, row, new_text, run_time=0.7, **kw):
        self.panel, self.row, self.new_text = panel, row, new_text
        super().__init__(
            Mobject(), run_time=run_time, rate_func=linear, remover=True,
            suspend_mobject_updating=False, **kw,
        )  # fmt: skip

    def begin(self):
        row, panel = self.row, self.panel
        old, new = row.text, self.new_text
        a = 0
        while a < min(len(old), len(new)) and old[a] == new[a]:
            a += 1
        b = 0
        while b < min(len(old), len(new)) - a and old[-1 - b] == new[-1 - b]:
            b += 1
        self.a, self.b = a, b
        self.fresh = Row(new, row.fs, panel._colors())
        self.fresh.galpha[:] = 0.0
        # both rows share the slot until the swap is over
        self.fresh.vis, self.fresh.fold, self.fresh.role = 0.0, row.fold, row.role
        self.old_mob = row.mob
        panel._adopt(self.fresh.mob, panel.text_layer)
        self.starting_mobject = Mobject()
        self.interpolate(0)

    def interpolate_mobject(self, alpha):
        row, fresh = self.row, self.fresh
        a, b = self.a - row.lead, self.b
        n_old, n_new = len(row.glyphs), len(fresh.glyphs)
        out = float(np.clip(1 - alpha / 0.45, 0, 1))
        inn = float(np.clip((alpha - 0.55) / 0.45, 0, 1))
        if alpha < 0.5:
            row.galpha[:] = 1.0
            row.galpha[max(a, 0) : n_old - b] = out
            fresh.galpha[:] = 0.0
        else:
            row.galpha[:] = 0.0
            fresh.galpha[:] = 1.0
            fresh.galpha[max(a, 0) : n_new - b] = inn
        # the fresh text rides exactly on the old one
        fresh.mob.shift(row.strut.get_center() - fresh.strut.get_center())
        op = row.op if row.op >= 0 else 1.0
        for i, g in enumerate(fresh.glyphs):
            g.set_opacity(op * fresh.galpha[i])
        row._seen = None

    def clean_up_from_scene(self, scene):
        super().clean_up_from_scene(scene)
        row, fresh, panel = self.row, self.fresh, self.panel
        for g in row.glyphs:  # (a mobject removed mid-play is still drawn: hide it)
            g.set_opacity(0)
        row.strut.set_opacity(0)
        panel.text_layer.remove(self.old_mob)
        row.text, row.mob, row.strut = fresh.text, fresh.mob, fresh.strut
        row.glyphs, row.lead = fresh.glyphs, fresh.lead
        row.galpha = np.ones(len(row.glyphs))
        if row.typed is not None:  # a typed command stays fully typed
            row.typed = float(row.n_chars() + row.lead)
        row._seen = None
        panel.refresh()


# --------------------------------------------------------------------------- #
# icons: one flat glyph per resource type (they echo the 3D stage)
# --------------------------------------------------------------------------- #
def res_icon(kind, s=0.44):
    """A flat icon for a resource type, ``s`` units tall."""
    c = KIND_C[kind]
    if kind == "aws_vpc":
        g = VGroup(
            RoundedRectangle(width=1.0, height=0.74, corner_radius=0.12, stroke_color=c,
                             stroke_width=3, fill_color=c, fill_opacity=0.22),
            RoundedRectangle(width=0.58, height=0.36, corner_radius=0.07, stroke_color=c,
                             stroke_width=2, fill_opacity=0).set_stroke(opacity=0.6),
        )  # fmt: skip
    elif kind == "aws_subnet":
        box = RoundedRectangle(width=1.0, height=0.74, corner_radius=0.12, stroke_color=c,
                               stroke_width=3, fill_color=c, fill_opacity=0.26)  # fmt: skip
        dots = VGroup(*[Dot([x, y, 0], radius=0.05, color=c)
                        for x in (-0.24, 0, 0.24) for y in (-0.13, 0.13)])  # fmt: skip
        g = VGroup(box, dots)
    elif kind == "aws_security_group":
        sh = Polygon(
            [-0.42, 0.36, 0], [0, 0.48, 0], [0.42, 0.36, 0], [0.40, -0.06, 0],
            [0.22, -0.34, 0], [0, -0.48, 0], [-0.22, -0.34, 0], [-0.40, -0.06, 0],
            stroke_color=c, stroke_width=3, fill_color=c, fill_opacity=0.22,
        )  # fmt: skip
        tick = VMobject(stroke_color=c, stroke_width=3.5)
        tick.set_points_as_corners(
            [[-0.17, 0.0, 0], [-0.04, -0.14, 0], [0.19, 0.16, 0]]
        )
        g = VGroup(sh, tick)
    elif kind == "aws_instance":
        case = RoundedRectangle(width=0.78, height=1.0, corner_radius=0.08, stroke_color=c,
                                stroke_width=3, fill_color=c, fill_opacity=0.20)  # fmt: skip
        bays = VGroup(*[Line([-0.22, y, 0], [0.22, y, 0], stroke_color=c, stroke_width=3)
                        for y in (-0.26, -0.06, 0.14)])  # fmt: skip
        led = Dot([0.22, 0.34, 0], radius=0.055, color=GOOD)
        g = VGroup(case, bays, led)
    else:  # aws_s3_bucket
        body = Polygon([-0.44, 0.34, 0], [0.44, 0.34, 0], [0.32, -0.44, 0], [-0.32, -0.44, 0],
                       stroke_color=c, stroke_width=3, fill_color=c, fill_opacity=0.24)  # fmt: skip
        rim = Ellipse(width=0.88, height=0.26, stroke_color=c, stroke_width=3,
                      fill_color=mix(c, BG, 0.55), fill_opacity=1).move_to([0, 0.34, 0])  # fmt: skip
        g = VGroup(body, rim)
    g.scale(s / g.height)
    return g


def plan_badge(symbol, s=0.36):
    """The plan's verdict for one resource: ``+`` ``~`` ``-/+`` ``-`` in a disc."""
    c = {"+": ADD_C, "~": CHANGE_C, "-": DESTROY_C, "-/+": DESTROY_C, "=": MUTED}[
        symbol
    ]
    t = txt(
        symbol, fs=22 if len(symbol) == 1 else 16, color=BG, weight="BOLD", font=MONO
    )
    w = max(s, t.width + 0.18)
    disc = RoundedRectangle(width=w, height=s, corner_radius=s / 2, stroke_width=0,
                            fill_color=c, fill_opacity=1)  # fmt: skip
    t.move_to(disc)
    g = VGroup(disc, t)
    g.disc = disc
    return g


class ResCard(VGroup):
    """A resource as a graph node: icon, address, progress bars along the bottom.

    Plain attributes, animated with ``Tween``: ``prog`` (0..1, the bars fill),
    ``done`` (0..1, bars and border turn green, a tick lands), ``gone`` (0..1, the
    card empties: destroyed), ``lit`` (0..1, border in the resource's colour).
    """

    def __init__(self, address, kind, w=3.9, h=0.74, fs=16, n=1):
        super().__init__()
        self.kind, self.address, self.n = kind, address, n
        self.prog, self.done, self.gone, self.lit = 0.0, 0.0, 0.0, 0.0
        c = KIND_C[kind]
        self.box = RoundedRectangle(width=w, height=h, corner_radius=0.13, stroke_color=FAINT,
                                    stroke_width=2.5, fill_color=PANEL, fill_opacity=1)  # fmt: skip
        self.icon = res_icon(kind, s=h * 0.56)
        self.icon.move_to([self.box.get_left()[0] + 0.42, 0.03, 0])
        self.label = txt(address, fs=fs, color=INK, font=MONO)
        self.label.next_to(self.icon, RIGHT, buff=0.20).set_y(0.04)
        self.extra = VGroup()
        if n > 1:
            badge = txt(f"×{n}", fs=fs, color=c, weight="BOLD", font=MONO)
            badge.next_to(self.label, RIGHT, buff=0.16)
            self.extra.add(badge)
        self.tick = make_tick(GOOD, sw=4.5, scale=0.5)
        self.tick.move_to([self.box.get_right()[0] - 0.30, 0.03, 0])
        self.tracks, self.bars = VGroup(), VGroup()
        bw, bh, gap = w - 0.36, 0.045, 0.035
        for i in range(n):
            y = self.box.get_bottom()[1] + 0.10 + i * (bh + gap)
            tr = Rectangle(
                width=bw, height=bh, stroke_width=0, fill_color=FAINT, fill_opacity=0.0
            )
            tr.move_to([0, y, 0])
            self.tracks.add(tr)
            self.bars.add(tr.copy())
        self.w, self.c = bw, c
        self.add(
            self.box,
            self.tracks,
            self.bars,
            self.icon,
            self.label,
            self.extra,
            self.tick,
        )
        self._ink = [
            (m, m.get_fill_opacity(), m.get_stroke_opacity())
            for part in (self.icon, self.label, self.extra)
            for m in part.family_members_with_points()
        ]
        self.refresh()

    def refresh(self):
        p, dn, gn = (float(np.clip(v, 0, 1)) for v in (self.prog, self.done, self.gone))
        live = 1 - gn
        # lit: a muted tint of the resource's colour (never as bright as "done")
        border = mix(mix(FAINT, self.c, 0.62 * self.lit), GOOD, dn)
        border = mix(border, DESTROY_C, min(1.0, 2.2 * gn) * (1 - gn))
        self.box.set_stroke(mix(border, FAINT, gn**2), width=2.5)
        self.box.set_fill(PANEL, opacity=1 - 0.75 * gn)
        for m, fo, so in self._ink:
            m.set_fill(opacity=fo * (0.25 + 0.75 * live))
            m.set_stroke(opacity=so * (0.25 + 0.75 * live))
        left = self.tracks[0].get_left()[0]
        running = 1.0 if (p > 0 or dn > 0) else 0.0
        for tr, bar in zip(self.tracks, self.bars, strict=True):
            tr.set_fill(FAINT, opacity=0.9 * running * live)
            wdt = max(1e-3, self.w * p)
            bar.stretch_to_fit_width(wdt)
            bar.move_to([left + wdt / 2, tr.get_center()[1], tr.get_center()[2]])
            bar.set_fill(
                mix(CHANGE_C, GOOD, dn), opacity=(1.0 if p > 0 else 0.0) * live
            )
        for m in self.tick.family_members_with_points():
            m.set_stroke(GOOD, opacity=dn * live)
        return self

    def point(self, edge):
        """Top (``UP``) or bottom (``DOWN``) middle of the card, for edges."""
        return self.box.get_edge_center(edge)


def window(w, h, title, role=None, bar_h=0.40, fill=WINDOW_BG, lights=True):
    """An empty window: body, title bar, traffic lights (``lights``), a title and an
    optional one-word role at the right of the bar. ``.bg`` / ``.bar`` expose the parts."""
    bg = RoundedRectangle(width=w, height=h, corner_radius=0.14, stroke_color=FAINT,
                          stroke_width=2, fill_color=fill, fill_opacity=1.0)  # fmt: skip
    bar = RoundedRectangle(width=w, height=bar_h, corner_radius=0.14, stroke_width=0,
                           fill_color=WINDOW_BAR, fill_opacity=1.0)  # fmt: skip
    bar.move_to(bg).align_to(bg, UP)
    dots = VGroup(
        *[Dot(radius=0.042, color=c) for c in ("#FF5F57", "#FEBC2E", "#28C840")]
    ).arrange(RIGHT, buff=0.10)
    dots.move_to([bg.get_left()[0] + 0.36, bar.get_center()[1], 0])
    ttl = txt(title, fs=16, color=INK, font=MONO)
    if lights:
        ttl.next_to(dots, RIGHT, buff=0.26).set_y(bar.get_center()[1])
        g = VGroup(bg, bar, dots, ttl)
    else:
        ttl.move_to([bg.get_left()[0] + 0.26 + ttl.width / 2, bar.get_center()[1], 0])
        g = VGroup(bg, bar, ttl)
    if role:
        r = txt(role, fs=16, color=MUTED, weight="BOLD")
        r.move_to([bg.get_right()[0] - r.width / 2 - 0.22, bar.get_center()[1], 0])
        g.add(r)
        g.role = r
    g.bg, g.bar, g.ttl = bg, bar, ttl
    return g


def pointer(s=1.0):
    """A mouse pointer (its tip is at the mobject's top-left corner)."""
    a = Polygon(
        [0, 0, 0], [0, -0.42, 0], [0.10, -0.33, 0], [0.18, -0.50, 0],
        [0.25, -0.47, 0], [0.17, -0.30, 0], [0.30, -0.30, 0],
        stroke_color=BG, stroke_width=2, fill_color=INK, fill_opacity=1,
    )  # fmt: skip
    return a.scale(s, about_point=ORIGIN)


def click_ring(at, color=INK):
    """The ring a click leaves: returns ``(mobject, animation)``."""
    c = Circle(radius=0.07, stroke_color=color, stroke_width=3).move_to(at)
    return c, Succession(
        FadeIn(c, run_time=0.06),
        c.animate(run_time=0.34, rate_func=rate_functions.ease_out_cubic)
        .scale(3.4)
        .set_stroke(opacity=0),
        FadeOut(c, run_time=0.01),
    )


def padlock(color=GOLD, s=1.0, shut=True):
    """A padlock, shut or open."""
    body = RoundedRectangle(width=0.50, height=0.40, corner_radius=0.08, stroke_width=0,
                            fill_color=color, fill_opacity=1)  # fmt: skip
    hook = ArcBetweenPoints([0.15, 0.18, 0], [-0.15, 0.18, 0], angle=PI)
    hook.set_stroke(color, width=5)
    legs = VGroup(
        Line([0.15, 0.18, 0], [0.15, 0.06, 0]), Line([-0.15, 0.18, 0], [-0.15, 0.06, 0])
    )
    legs.set_stroke(color, width=5)
    shackle = VGroup(hook, legs)
    if not shut:
        shackle.rotate(-0.7, about_point=[0.15, 0.10, 0]).shift(UP * 0.05)
    hole = Dot([0, -0.02, 0], radius=0.05, color=BG)
    return VGroup(shackle, body, hole).scale(s)


def doc_icon(label, color=INK, w=1.5, fs=16, h=None):
    """A file: a sheet with a folded corner and its name."""
    h, c = h or w * 0.42, 0.14
    sheet = Polygon(
        [-w / 2, h / 2, 0], [w / 2 - c, h / 2, 0], [w / 2, h / 2 - c, 0],
        [w / 2, -h / 2, 0], [-w / 2, -h / 2, 0],
        stroke_color=color, stroke_width=2.2, fill_color=PANEL, fill_opacity=1,
    )  # fmt: skip
    t = txt(label, fs=fs, color=color, font=MONO)
    if t.width > w - 0.24:
        t.scale((w - 0.24) / t.width)
    t.move_to(sheet)
    g = VGroup(sheet, t)
    g.sheet = sheet
    return g


def laptop(name, color=MUTED, w=1.5):
    """Someone's machine: a screen, a base, a name."""
    screen = RoundedRectangle(width=w, height=w * 0.62, corner_radius=0.08, stroke_color=color,
                              stroke_width=2.6, fill_color=PANEL, fill_opacity=1)  # fmt: skip
    base = Line([-w * 0.62, 0, 0], [w * 0.62, 0, 0], stroke_color=color, stroke_width=4)
    base.next_to(screen, DOWN, buff=0.05)
    prompt = txt("$ _", fs=18, color=color, font=MONO).move_to(screen)
    label = txt(name, fs=18, color=INK, weight="MEDIUM").next_to(base, DOWN, buff=0.14)
    g = VGroup(screen, base, prompt, label)
    g.screen = screen
    return g

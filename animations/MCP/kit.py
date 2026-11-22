"""Film-local components of the MCP film.

The stage has three actors, left to right, in the order a request crosses them:

    model (its context)  |  host (the app, its user, a client)  ==wire==  server (a tool, a table)

Everything is built at fixed stage coordinates, so that a scene can rebuild exactly
the picture the previous one ended on (``mcp_film.py``, "hand-offs"). Two habits keep
Manim from taking groups apart: whatever is animated on its own is a top-level
mobject (a frame's outline, its name, a block, a line of a card), and text that is
typed, marked token by token or recoloured is a ``Chars`` line, with one glyph per
character, animated through its owner.
"""

from __future__ import annotations

import io
import keyword
import math
import re
import tokenize

import numpy as np
from manimx import *

import wire as W

# ---- the film's colour language -------------------------------------------------- #
MODEL_C = "#C170BB"  # the model and what it writes
HOST_C = "#508FF9"  # the application: host and client
SERVER_C = "#E26E1A"  # servers and the text that comes from them
USER_C = "#30A46E"  # the person, and what the person allows
LOOK_C = GOLD  # the one thing to look at
HOSTILE_C = BAD
STEEL = "#9AA5BD"  # cables, machines
DOT_C = "#414B60"  # an order nobody is looking at
ORIGIN_C = {"user": USER_C, "model": MODEL_C, "server": SERVER_C, "hostile": HOSTILE_C}

J_KEY, J_STR, J_NUM, J_PUNCT = "#D6DEEB", "#C3E88D", "#F78C6C", "#7F8AA3"

# ---- the stage ---------------------------------------------------------------------- #
TOP, BOT = 2.72, -2.95
MODEL_X = (-6.76, -2.26)
HOST_X = (-2.01, 0.79)
SERVER_X = (2.89, 6.76)
WIRE_Y = 2.05
MID_Y = (TOP + BOT) / 2
GAP_X = (HOST_X[1] + SERVER_X[0]) / 2  # the middle of the wire
Z_TAG, Z_BAND, Z_VEIL, Z_LINK, Z_CARD, Z_HEAD = 1, 3, 5, 6, 8, 12


def _mono_advance():
    t = BaseText("HH", font=MONO, font_size=60, disable_ligatures=True)
    return float(t.submobjects[1].get_left()[0] - t.submobjects[0].get_left()[0]) / 60


MONO_ADV = _mono_advance()  # width of a Menlo cell, per unit of font size


# ---------------------------------------------------------------------------------- #
# Text with one glyph per character
# ---------------------------------------------------------------------------------- #
class Chars(VGroup):
    """A line of text with one submobject per character (spaces included), in a box as
    tall as its line. ``glyphs[a:b]`` index ``string``; Menlo lines align by column
    (``x_left`` is where column 0 starts), prose lines by their ink."""

    def __init__(self, text, fs=18, color=INK, font=None, weight="NORMAL"):
        kw = {"font": font} if font else {}
        g = line_txt(
            "H" + text, fs=fs, color=color, weight=weight, disable_ligatures=True, **kw
        )
        body, strut = g.body, g.submobjects[-1]
        body.remove(body.submobjects[0])  # the ruler: it gave the strut its x
        super().__init__(body, strut)
        self.body, self.string, self.fs = body, text, fs
        self.cell = MONO_ADV * fs if font == MONO else None

    @property
    def glyphs(self):
        return self.body.submobjects

    def x_left(self):
        if self.cell is not None:
            return self.submobjects[-1].get_x() + self.cell
        return self.body.get_left()[0]

    def x_right(self):
        return self.body.get_right()[0]

    def at(self, x, y):
        """Put the line's left edge at ``x`` and its middle at ``y``."""
        return self.shift([x - self.x_left(), y - self.get_center()[1], 0])

    def ending_at(self, x, y):
        return self.shift([x - self.x_right(), y - self.get_center()[1], 0])

    def span(self, token, nth=0):
        """The glyphs of the ``nth`` occurrence of ``token`` (a throw-away group: use
        it for geometry and copies, never animate it)."""
        a = -1
        for _ in range(nth + 1):
            a = self.string.index(token, a + 1)
        return VGroup(*self.glyphs[a : a + len(token)])

    def tint(self, token, color, nth=0):
        self.span(token, nth).set_color(color)
        return self

    def hide(self):
        for g in self.glyphs:
            g.set_opacity(0)
        return self


def small(text, fs=16, color=MUTED, **kw):
    return txt(text, fs=fs, color=color, **kw)


def mark(line, token=None, color=LOOK_C, buff=None, nth=0):
    """A box around a token of a ``Chars`` line (or around the whole line). Menlo is
    set tight: with more than a hair of padding the box lands on the next glyph."""
    target = line.span(token, nth) if token else line.body
    if buff is None:
        buff = 0.035 if line.cell is not None else 0.06
    box = SurroundingRectangle(target, buff=buff, corner_radius=0.07, color=color)
    return box.set_stroke(color, width=2.5).set_fill(color, opacity=0.14)


class TypeOut(Animation):
    """Reveal ``Chars`` lines character by character, as a model writes them.

    ``owner`` is the top-level mobject the lines belong to (a block, or the line
    itself): it is what Manim animates, so the lines are never taken out of it. The
    glyphs are hidden as soon as the animation is built.
    """

    def __init__(self, owner, *lines, run_time=1.0, rate_func=linear, **kw):
        self.cells = [g for ln in (lines or (owner,)) for g in ln.glyphs]
        for g in self.cells:
            g.set_opacity(0)
        super().__init__(owner, run_time=run_time, rate_func=rate_func, **kw)

    def begin(self):
        self.starting_mobject = Mobject()
        self.interpolate(0)

    def interpolate_mobject(self, alpha):
        k = round(self.rate_func(alpha) * len(self.cells))
        for i, g in enumerate(self.cells):
            g.set_opacity(1.0 if i < k else 0.0)


_JSON_TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|-?\d+(?:\.\d+)?|\btrue\b|\bfalse\b|\bnull\b')


def paint_json(line, key=J_KEY, string=J_STR, number=J_NUM, punct=J_PUNCT):
    """Colour a line of JSON: keys, strings, numbers, punctuation."""
    s, g = line.string, line.glyphs
    for ch in g:
        ch.set_color(punct)
    for m in _JSON_TOKEN.finditer(s):
        if m.group().startswith('"'):
            color = key if s[m.end() :].lstrip().startswith(":") else string
        else:
            color = number
        for ch in g[m.start() : m.end()]:
            ch.set_color(color)
    return line


def paint_python(lines):
    """Colour lines of Python with the language's own tokenizer."""
    source = "\n".join(ln.string for ln in lines) + "\n"
    previous = None
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        (r0, c0), (r1, c1) = tok.start, tok.end
        color = None
        if tok.type == tokenize.STRING:
            color = STR
        elif tok.type == tokenize.NUMBER:
            color = NUM
        elif tok.type == tokenize.NAME:
            if keyword.iskeyword(tok.string):
                color = KW
            elif previous == "def" or tok.line[c1 : c1 + 1] == "(":
                color = FUNC
        if color and r0 == r1 and r0 - 1 < len(lines):
            for ch in lines[r0 - 1].glyphs[c0:c1]:
                ch.set_color(color)
        previous = tok.string
    return lines


def paint_http(line):
    s = line.string
    if ": " in s and not s.startswith(("POST", "GET", "HTTP")):
        k = s.index(":")
        for ch in line.glyphs[:k]:
            ch.set_color(J_KEY)
        for ch in line.glyphs[k : k + 1]:
            ch.set_color(J_PUNCT)
        for ch in line.glyphs[k + 1 :]:
            ch.set_color(J_STR)
    return line


# ---------------------------------------------------------------------------------- #
# Small glyphs
# ---------------------------------------------------------------------------------- #
def sparkle(s=0.16, color=INK):
    """A four-pointed star: the mark of the model."""
    a = 0.27 * s
    pts = [(0, s), (a, a), (s, 0), (a, -a), (0, -s), (-a, -a), (-s, 0), (-a, a)]
    star = Polygon(*[np.array([x, y, 0.0]) for x, y in pts])
    return star.set_stroke(width=0).set_fill(color, opacity=1)


def model_chip(side=0.4):
    k = side / 0.4
    box = RoundedRectangle(width=side, height=side, corner_radius=side * 0.24)
    box.set_stroke(MODEL_C, width=2.5).set_fill(mix(MODEL_C, BG, 0.62), opacity=1)
    big = sparkle(side * 0.3).move_to(box.get_center() + np.array([-0.03, -0.03, 0]) * k)
    tiny = sparkle(side * 0.13).move_to(box.get_center() + np.array([0.11, 0.11, 0]) * k)
    return VGroup(box, big, tiny)


def avatar(r=0.2, color=USER_C):
    ring = Circle(radius=r, stroke_color=color, stroke_width=2.5)
    ring.set_fill(mix(color, BG, 0.8), opacity=1)
    head = Circle(radius=r * 0.3, stroke_width=0, fill_color=color, fill_opacity=1)
    head.shift(UP * r * 0.24)
    body = Arc(radius=r * 0.52, start_angle=0, angle=PI, color=color)
    body.set_stroke(width=0).set_fill(color, opacity=1).shift(DOWN * r * 0.66)
    return VGroup(ring, head, body)


def client_port(color=HOST_C, s=0.3):
    box = RoundedRectangle(width=s, height=s, corner_radius=0.07)
    return box.set_stroke(color, width=2.5).set_fill(mix(color, BG, 0.12), opacity=1)


def socket_glyph(color=SERVER_C, w=0.3, h=0.44):
    body = RoundedRectangle(width=w, height=h, corner_radius=0.07)
    body.set_stroke(color, width=2.5).set_fill(mix(color, BG, 0.12), opacity=1)
    holes = VGroup(
        *[
            Rectangle(width=0.15, height=0.075)
            .set_stroke(width=0)
            .set_fill(BG, opacity=1)
            .move_to(body.get_left() + RIGHT * 0.075 + UP * dy)
            for dy in (0.095, -0.095)
        ]
    )
    return VGroup(body, holes)


def plug_glyph(color=HOST_C, w=0.3, h=0.38):
    body = RoundedRectangle(width=w, height=h, corner_radius=0.07)
    body.set_stroke(color, width=2.5).set_fill(mix(color, BG, 0.12), opacity=1)
    prongs = VGroup(
        *[
            Rectangle(width=0.13, height=0.06)
            .set_stroke(width=0)
            .set_fill(INK, opacity=1)
            .move_to(body.get_right() + RIGHT * 0.06 + UP * dy)
            for dy in (0.095, -0.095)
        ]
    )
    g = VGroup(prongs, body)
    g.body = body
    return g


def envelope(color, w=0.46, h=0.31):
    body = RoundedRectangle(width=w, height=h, corner_radius=0.05)
    body.set_stroke(color, width=2.5).set_fill(mix(color, BG, 0.72), opacity=1)
    flap = VMobject().set_points_as_corners(
        [
            body.get_corner(UL) + np.array([0.04, -0.04, 0]),
            body.get_center() + np.array([0, -0.03, 0]),
            body.get_corner(UR) + np.array([-0.04, -0.04, 0]),
        ]
    )
    flap.set_stroke(color, width=2.2)
    return VGroup(body, flap)


def gear_icon(r=0.13, color=SERVER_C, teeth=7):
    pts = []
    for k in range(teeth):
        a0 = TAU * k / teeth
        for da, rad in ((-0.2, 0.74), (-0.11, 1.0), (0.11, 1.0), (0.2, 0.74)):
            ang = a0 + da * TAU / teeth * 2.2
            pts.append(np.array([math.cos(ang), math.sin(ang), 0.0]) * r * rad)
    rim = Polygon(*pts).set_stroke(color, width=2).set_fill(opacity=0)
    hub = Circle(radius=r * 0.3, stroke_color=color, stroke_width=2)
    return VGroup(rim, hub)


def doc_icon(h=0.28, color=SERVER_C):
    w, c = h * 0.78, h * 0.3
    sheet = Polygon(
        [-w / 2, -h / 2, 0], [-w / 2, h / 2, 0], [w / 2 - c, h / 2, 0],
        [w / 2, h / 2 - c, 0], [w / 2, -h / 2, 0],
    )  # fmt: skip
    sheet.set_stroke(color, width=2).set_fill(opacity=0)
    rows = VGroup(
        *[
            Line([-w * 0.26, y, 0], [w * 0.26, y, 0]).set_stroke(color, width=2)
            for y in (0.0, -h * 0.22)
        ]
    )
    return VGroup(sheet, rows)


def prompt_icon(h=0.26, color=SERVER_C):
    box = RoundedRectangle(width=h * 1.2, height=h * 0.86, corner_radius=h * 0.2)
    box.set_stroke(color, width=2).set_fill(opacity=0)
    slash = Line([-h * 0.12, -h * 0.22, 0], [h * 0.12, h * 0.22, 0])
    return VGroup(box, slash.set_stroke(color, width=2.2))


def clip_icon(h=0.26, color=MUTED):
    outer = RoundedRectangle(width=h * 0.46, height=h, corner_radius=h * 0.22)
    outer.set_stroke(color, width=2).set_fill(opacity=0)
    inner = Line([0, h * 0.24, 0], [0, -h * 0.2, 0]).set_stroke(color, width=2)
    return VGroup(outer, inner).rotate(-35 * DEGREES)


def cylinder_icon(h=0.3, color=STEEL):
    w, e = h * 0.86, h * 0.26
    top = Ellipse(width=w, height=e, color=color).shift(UP * (h - e) / 2)
    left = Line([-w / 2, (h - e) / 2, 0], [-w / 2, -(h - e) / 2, 0])
    right = Line([w / 2, (h - e) / 2, 0], [w / 2, -(h - e) / 2, 0])
    foot = Arc(radius=w / 2, start_angle=PI, angle=PI, color=color).stretch(e / w, 1)
    foot.move_to([0, -(h - e) / 2 - e / 4, 0])
    return VGroup(top, left, right, foot).set_stroke(color, width=2).set_fill(opacity=0)


def lock_icon(h=0.3, color=STEEL):
    body = RoundedRectangle(width=h * 0.8, height=h * 0.58, corner_radius=0.04)
    body.set_stroke(color, width=2).set_fill(color, opacity=0.9).shift(DOWN * h * 0.2)
    bow = Arc(radius=h * 0.25, start_angle=0, angle=PI, color=color)
    bow.set_stroke(color, width=2.5).set_fill(opacity=0).shift(UP * h * 0.09)
    return VGroup(bow, body)


def tap_ring(p, color=INK):
    """A touch on the screen: the animation of a ring that spreads and fades."""
    ring = Circle(radius=0.11, stroke_color=color, stroke_width=4).move_to(p)
    ring.set_z_index(Z_HEAD)
    return Succession(
        FadeIn(ring, scale=0.5, run_time=0.12),
        ring.animate(run_time=0.45).scale(2.8).set_stroke(opacity=0.0),
        FadeOut(ring, run_time=0.02),
    )


def glow(box, color, width=7, rt=1.0):
    """An outline lights up and dies down: "this one" (``rt`` seconds in all). The
    halo sits just above its box: over what the box holds, but under the plate that
    carries a frame's name, so a glowing frame never strikes through its own name."""
    halo = box.copy().set_fill(opacity=0).set_stroke(color, width=width, opacity=0.95)
    halo.set_z_index(box.z_index + 0.5)
    return Succession(FadeIn(halo, run_time=0.25 * rt), FadeOut(halo, run_time=0.75 * rt))


def spinner(center, r=0.22, color=LOOK_C):
    """Three quarters of a ring, to turn around something that is working."""
    arc = Arc(radius=r, start_angle=0, angle=1.5 * PI, color=color)
    return arc.set_stroke(color, width=3).set_fill(opacity=0).move_arc_center_to(center)


# ---------------------------------------------------------------------------------- #
# Frames
# ---------------------------------------------------------------------------------- #
class Frame:
    """A rounded frame whose name interrupts its top border, as two mobjects: the
    outline (``box``, to draw) and the name on its plate (``tag``, to fade in).
    ``icon_w`` leaves room for an icon before the name (``icon_at`` is its centre)."""

    def __init__(self, x, color, name, icon_w=0.0, top=TOP, bot=BOT, fs=20):
        x0, x1 = x
        self.box = RoundedRectangle(width=x1 - x0, height=top - bot, corner_radius=0.2)
        self.box.set_stroke(color, width=2.5, opacity=0.85).set_fill(opacity=0)
        self.box.move_to([(x0 + x1) / 2, (top + bot) / 2, 0])
        title = txt(name, fs=fs, color=color, weight="BOLD")
        w = icon_w + (0.13 if icon_w else 0.0) + title.width
        left = x0 + 0.4
        title.move_to([left + w - title.width / 2, top, 0])
        plate = Rectangle(width=w + 0.26, height=0.36)
        plate.set_stroke(width=0).set_fill(BG, opacity=1).move_to([left + w / 2, top, 0])
        self.tag = VGroup(plate, title).set_z_index(Z_TAG)
        self.title, self.color = title, color
        self.icon_at = np.array([left + icon_w / 2, top, 0.0])

    def mobs(self):
        return [self.box, self.tag]


# ---------------------------------------------------------------------------------- #
# The model and its context
# ---------------------------------------------------------------------------------- #
ROW_STYLE = {
    "prose": {"fs": 18, "color": INK},
    "mono": {"fs": 17, "color": INK, "font": MONO},
    "dim": {"fs": 16, "color": MUTED},
    "small": {"fs": 16, "color": INK},
}


class Block(VGroup):
    """One entry of the context: a tag, then one or two lines of content, tinted by
    where the text came from (the user, the model, a server)."""

    PAD_X, PAD_TOP, TAG_H, GAP, PITCH, PAD_BOT = 0.15, 0.09, 0.2, 0.05, 0.33, 0.11

    def __init__(self, tag, rows, origin, x, y, w):
        color = ORIGIN_C[origin]
        h = self.PAD_TOP + self.TAG_H + self.GAP + len(rows) * self.PITCH + self.PAD_BOT
        box = RoundedRectangle(width=w, height=h, corner_radius=0.1)
        box.set_stroke(color, width=1.5, opacity=0.6).set_fill(color, opacity=0.11)
        box.move_to([x + w / 2, y - h / 2, 0])
        label = Chars(tag, fs=16, color=color, weight="MEDIUM")
        label.at(x + self.PAD_X, y - self.PAD_TOP - self.TAG_H / 2)
        self.rows = []
        for i, (text, style) in enumerate(rows):
            ln = Chars(text, **ROW_STYLE[style])
            ln.at(
                x + self.PAD_X,
                y - self.PAD_TOP - self.TAG_H - self.GAP - self.PITCH * (i + 0.5),
            )
            self.rows.append(ln)
        super().__init__(box, label, *self.rows)
        self.box, self.label, self.kind, self.origin = box, label, tag, origin

    def typed(self, run_time=1.2):
        """The animation that writes the content (it hides it first)."""
        return TypeOut(self, *self.rows, run_time=run_time)


class ModelPanel:
    """The model: a frame, and inside it the context, a list of blocks that grows
    downwards. Blocks are separate mobjects (``mobs()``), never children of a group."""

    GAP = 0.08

    def __init__(self):
        x0, x1 = MODEL_X
        self.frame = Frame(MODEL_X, MODEL_C, "model", icon_w=0.36)
        self.chip = model_chip(0.36).move_to(self.frame.icon_at).set_z_index(Z_TAG)
        self.ctx = small("context", fs=16, color=MODEL_C)
        self.ctx.move_to([x0 + 0.24 + self.ctx.width / 2, TOP - 0.44, 0])
        self.rule = Line(
            [self.ctx.get_right()[0] + 0.12, TOP - 0.44, 0], [x1 - 0.22, TOP - 0.44, 0]
        ).set_stroke(FAINT, width=1.5)
        self.x, self.w = x0 + 0.18, (x1 - x0) - 0.36
        self.y0 = TOP - 0.68
        self.blocks = []

    def next_y(self):
        return self.y0 - sum(b.box.height + self.GAP for b in self.blocks)

    def block(self, tag, rows, origin):
        """A new block in the next free slot (registered, not yet on screen)."""
        b = Block(tag, rows, origin, self.x, self.next_y(), self.w)
        self.blocks.append(b)
        return b

    def drop(self, *blocks):
        for b in blocks:
            self.blocks.remove(b)

    def shifted(self, dx):
        """Put the whole panel ``dx`` to the right (and its future blocks with it)."""
        for m in self.mobs():
            m.shift(RIGHT * dx)
        self.x += dx
        return self

    def slide(self, dx):
        """The animations of that move."""
        anims = [m.animate.shift(RIGHT * dx) for m in self.mobs()]
        self.x += dx
        return anims

    def furniture(self):
        return [*self.frame.mobs(), self.chip, self.ctx, self.rule]

    def mobs(self):
        return [*self.furniture(), *self.blocks]

    def reading(self, run_time=0.9):
        """The model reads its context: a band of light runs down the blocks."""
        cx = self.x + self.w / 2
        top, bottom = self.y0, self.next_y() + self.GAP
        band = Rectangle(width=self.w + 0.08, height=0.4)
        band.set_stroke(width=0).set_fill(MODEL_C, opacity=0.26).set_z_index(Z_BAND)
        band.move_to([cx, top - 0.2, 0])
        travel = max(0.3, run_time - 0.3)
        return Succession(
            FadeIn(band, run_time=0.15),
            band.animate(run_time=travel, rate_func=linear).move_to([cx, bottom + 0.2, 0]),
            FadeOut(band, run_time=0.15),
        )


# ---------------------------------------------------------------------------------- #
# The host: the application, with its user and its client
# ---------------------------------------------------------------------------------- #
def speech(rows, color, x, y, fs=18, pitch=0.3, w=None):
    """A chat bubble whose top-left corner is at (x, y)."""
    lines = [Chars(r, fs=fs) for r in rows]
    width = w or max(ln.body.width for ln in lines) + 0.3
    h = len(rows) * pitch + 0.2
    box = RoundedRectangle(width=width, height=h, corner_radius=0.13)
    box.set_stroke(color, width=1.5, opacity=0.7).set_fill(color, opacity=0.14)
    box.move_to([x + width / 2, y - h / 2, 0])
    for i, ln in enumerate(lines):
        ln.at(x + 0.15, y - 0.1 - pitch * (i + 0.5))
    g = VGroup(box, *lines)
    g.box, g.lines = box, lines
    return g


def button(text, color, w=1.08, h=0.42, fs=17, pressed=False):
    box = RoundedRectangle(width=w, height=h, corner_radius=0.1)
    box.set_stroke(color, width=2).set_fill(color, opacity=0.95 if pressed else 0.1)
    label = txt(text, fs=fs, color=BG if pressed else color, weight="MEDIUM").move_to(box)
    g = VGroup(box, label)
    g.box, g.label = box, label
    return g


class Consent:
    """The host asks the user before a tool runs: which server, which tool, with
    which arguments. Separate parts (``mobs()``), so the buttons can change."""

    W, H = 2.5, 2.0

    def __init__(self, server, tool, arguments, y_top, edge=LOOK_C, danger=False):
        cx = (HOST_X[0] + HOST_X[1]) / 2
        x = cx - self.W / 2 + 0.18
        self.ask = Chars("allow this call?", fs=16, color=MUTED).at(x, y_top - 0.29)
        self.server = Chars(server, fs=16, color=SERVER_C, font=MONO)
        self.server.at(x, y_top - 0.61)
        self.tool = Chars(tool, fs=17, color=INK, font=MONO).at(x, y_top - 0.92)
        self.args = Chars(
            arguments, fs=16, color=HOSTILE_C if danger else J_STR, font=MONO
        ).at(x, y_top - 1.22)
        # saying no is the user's right, not a hostile act: never drawn in red
        self.deny = button("Deny", INK if danger else MUTED)
        self.allow = button("Allow", USER_C)
        self.deny.move_to([cx - 0.6, y_top - 1.69, 0])
        self.allow.move_to([cx + 0.6, y_top - 1.69, 0])
        self.box = RoundedRectangle(width=self.W, height=self.H, corner_radius=0.15)
        self.box.set_stroke(edge, width=2.5).set_fill(PANEL, opacity=1)
        self.box.move_to([cx, y_top - self.H / 2, 0])

    def pressed(self, which="allow"):
        """The button after the tap, to fade in over the idle one."""
        idle = self.allow if which == "allow" else self.deny
        text, color = ("Allow", USER_C) if which == "allow" else ("Deny", INK)
        return button(text, color, pressed=True).move_to(idle)

    def mobs(self):
        return [self.box, self.ask, self.server, self.tool, self.args, self.deny, self.allow]


class HostFrame:
    """The application the user talks to. Top row: its client (the end of the wire).
    Below: a chat, with the user, a place for one request for consent, an input bar."""

    USER_Y, SAY_Y, ASK_Y, ANSWER_Y = 1.46, 1.13, -0.13, -0.3

    def __init__(self):
        x0, x1 = HOST_X
        self.frame = Frame(HOST_X, HOST_C, "host")
        self.x = x0 + 0.17
        self.avatar = avatar().move_to([x0 + 0.4, self.USER_Y, 0])
        self.who = small("user", fs=16, color=USER_C)
        self.who.next_to(self.avatar, RIGHT, buff=0.12)
        bar = RoundedRectangle(width=(x1 - x0) - 0.34, height=0.42, corner_radius=0.21)
        bar.set_stroke(FAINT, width=2).set_fill(BG, opacity=1)
        bar.move_to([(x0 + x1) / 2, BOT + 0.4, 0])
        self.clip = clip_icon().move_to(bar.get_left() + RIGHT * 0.3)
        self.bar = bar
        self.field_x = bar.get_left()[0] + 0.58  # where typed text starts
        self.field_y = bar.get_center()[1]

    def furniture(self):
        return [*self.frame.mobs(), self.avatar, self.who, self.bar, self.clip]

    def say(self, rows):
        return speech(rows, USER_C, self.x, self.SAY_Y)

    def answer(self, rows):
        return speech(rows, MODEL_C, self.x, self.ANSWER_Y)

    def consent(self, server, tool, arguments, **kw):
        return Consent(server, tool, arguments, self.ASK_Y, **kw)


# ---------------------------------------------------------------------------------- #
# The server: what it offers, and the system it wraps
# ---------------------------------------------------------------------------------- #
OFFER_ICON = {"tool": gear_icon, "resource": doc_icon, "prompt": prompt_icon}


def offer(kind, name, y, color=SERVER_C, name_fs=17):
    """One thing a server offers: its kind and its name."""
    x0, x1 = SERVER_X[0] + 0.17, SERVER_X[1] - 0.17
    box = RoundedRectangle(width=x1 - x0, height=0.62, corner_radius=0.12)
    box.set_stroke(color, width=2, opacity=0.9).set_fill(color, opacity=0.12)
    box.move_to([(x0 + x1) / 2, y, 0])
    icon = OFFER_ICON[kind](color=color).move_to([x0 + 0.34, y, 0])
    tag = Chars(kind, fs=16, color=color, weight="MEDIUM").at(x0 + 0.66, y + 0.145)
    label = Chars(name, fs=name_fs, color=INK, font=MONO).at(x0 + 0.66, y - 0.14)
    g = VGroup(box, icon, tag, label)
    g.box, g.icon, g.tag, g.label, g.kind = box, icon, tag, label, kind
    return g


_CIRCLE = Circle(radius=1.0).points.copy()


def dots(centers, r, color, opacity=1.0):
    """Many dots as ONE mobject (a subpath each): cheap to draw, and revealed dot by
    dot by ``DotsReveal``."""
    m = VMobject()
    m.set_points(
        np.concatenate([_CIRCLE * r + np.array([x, y, 0.0]) for x, y in centers])
    )
    m.set_stroke(width=0).set_fill(color, opacity=opacity)
    m.per_dot = len(_CIRCLE)
    return m


class DotsReveal(Animation):
    """Show the dots of a ``dots`` mobject one after another."""

    def __init__(self, mob, run_time=1.0, rate_func=linear, **kw):
        self.all = mob.points.copy()
        self.per = mob.per_dot
        self.n = len(self.all) // self.per
        self.full = mob.get_fill_opacity()
        mob.set_points(self.all[: self.per])  # never empty: Manim skips empty mobjects
        mob.set_fill(opacity=0)
        super().__init__(mob, run_time=run_time, rate_func=rate_func, **kw)

    def begin(self):
        self.starting_mobject = Mobject()
        self.interpolate(0)

    def interpolate_mobject(self, alpha):
        k = max(1, round(self.rate_func(alpha) * self.n))
        self.mobject.set_points(self.all[: k * self.per])
        self.mobject.set_fill(opacity=self.full if alpha > 0 else 0.0)


class OrdersGrid:
    """The table behind the server: one dot per order, a band per week."""

    COLS, R = 37, 0.031

    def __init__(self, top=1.5, weeks=None):
        """``weeks``: the bands to draw (all of them by default)."""
        sizes = {w: n for w, n in W.WEEK_SIZES.items() if weeks is None or w in weeks}
        x0, x1 = SERVER_X[0] + 0.24, SERVER_X[1] - 0.24
        self.x0, self.x1 = x0, x1
        pitch = (x1 - x0) / self.COLS
        self.pitch = pitch
        icon = cylinder_icon().move_to([x0 + 0.13, top - 0.2, 0])
        name = Chars("orders", fs=17, color=INK, font=MONO).at(x0 + 0.38, top - 0.2)
        shown = sum(sizes.values())
        count = f"{len(W.db):,} rows" if weeks is None else f"{shown} of {len(W.db):,} rows"
        rows = small(count, fs=16)
        rows.move_to([x1 - rows.width / 2, top - 0.2, 0])
        self.title = VGroup(icon, name, rows)
        # the table is behind credentials that only the server holds
        self.lock = lock_icon(0.26, STEEL).move_to([name.x_right() + 0.28, top - 0.2, 0])
        y = top - 0.52
        self.heads, self.centers, self.head_y = {}, {}, {}
        for week, n in sizes.items():
            self.heads[week] = Chars(f"week {week}", fs=16, color=MUTED).at(x0, y - 0.1)
            self.head_y[week] = y - 0.1
            y -= 0.3
            self.centers[week] = [
                (x0 + pitch * (i % self.COLS + 0.5), y - pitch * (i // self.COLS + 0.5))
                for i in range(n)
            ]
            y -= math.ceil(n / self.COLS) * pitch + 0.13
        self.bottom = y + 0.13
        self.base = dots([c for w in self.centers.values() for c in w], self.R, DOT_C)
        self.late_index = {
            week: [i for i, o in enumerate(W.db.where(week=week)) if o.late]
            for week in sizes
        }

    def furniture(self):
        return [self.title, self.lock, *self.heads.values(), self.base]

    def lit(self, week=W.WEEK, color=STEEL):
        """Every order of a week, lit."""
        return dots(self.centers[week], self.R, color)

    def late(self, week=W.WEEK, color=LOOK_C):
        """The late orders of a week."""
        return dots(
            [self.centers[week][i] for i in self.late_index[week]], self.R * 1.32, color
        )

    def count(self, text, color, slot=0, week=W.WEEK):
        """A counter on the header line of a week: slot 0 is the rows read, slot 1
        (right-aligned on the frame) the rows kept."""
        m = Chars(text, fs=16, color=color, font=MONO)
        if slot == 0:
            return m.at(self.x0 + 1.0, self.head_y[week])
        return m.ending_at(self.x1, self.head_y[week])


class ServerFrame:
    """A server: what it offers (top), the system it wraps (below). ``grid``: the
    table, when it is on screen already."""

    def __init__(self, grid=None):
        self.frame = Frame(SERVER_X, SERVER_C, "server")
        self.tool = offer("tool", W.TOOL["name"], WIRE_Y)
        self.grid = grid or OrdersGrid()

    def furniture(self):
        return [*self.frame.mobs(), self.tool, *self.grid.furniture()]


# ---------------------------------------------------------------------------------- #
# The wire between a client and a server
# ---------------------------------------------------------------------------------- #
class Link:
    """A client's port on the host, a cable, a plug in the server's socket; and the
    two labels that say what is crossing: the method under the cable, the id above."""

    def __init__(self):
        xh, xs = HOST_X[1], SERVER_X[0]
        self.port = client_port().move_to([xh, WIRE_Y, 0])
        self.socket = socket_glyph().move_to([xs - 0.17, WIRE_Y, 0])
        self.plug = plug_glyph()
        self.plug.shift(
            [self.socket.get_left()[0] - 0.04 - self.plug.body.get_right()[0], WIRE_Y, 0]
        )
        self.a = self.port.get_right()
        self.b = self.plug.body.get_left()
        self.cable = Line(self.a, self.b).set_stroke(STEEL, width=5)
        self.name = small("client", fs=16, color=HOST_C)
        self.name.move_to([xh - 0.3 - self.name.width / 2, WIRE_Y, 0])
        for m in self.mobs():
            m.set_z_index(Z_LINK)

    def mobs(self):
        return [self.cable, self.socket, self.plug, self.port, self.name]

    def parked(self):
        """Where the plug's centre is when it is out of the socket: beside its port,
        a gap apart (``plug.move_to(link.parked())``)."""
        dx = self.port.get_right()[0] + 0.07 - self.plug.body.get_left()[0]
        return self.plug.get_center() + RIGHT * dx

    def path(self, back=False, stop=1.0):
        """The way of a message along the cable (``stop``: how far it goes)."""
        a, b = self.port.get_center(), self.plug.body.get_center()
        if back:
            a, b = b, a
        return Line(a, a + (b - a) * stop)

    def middle(self):
        return (self.port.get_center() + self.plug.body.get_center()) / 2

    def method(self, text, color=INK):
        m = Chars(text, fs=16, color=color, font=MONO)
        m.at(GAP_X - m.body.width / 2, WIRE_Y - 0.43)
        return m.set_z_index(Z_LINK)

    def ident(self, n, color=LOOK_C):
        m = Chars(f"id {n}", fs=16, color=color, font=MONO)
        m.at(self.middle()[0] - m.body.width / 2, WIRE_Y + 0.4)
        return m.set_z_index(Z_LINK)

    def letter(self, back=False):
        return envelope(SERVER_C if back else HOST_C).set_z_index(Z_LINK + 1)


# ---------------------------------------------------------------------------------- #
# Close-ups: a message or a piece of code, large, with addressable tokens
# ---------------------------------------------------------------------------------- #
class MsgCard:
    """Lines of Menlo in a panel, its title above its top-left corner. ``kind`` picks
    the colouring: json, python, http, plain. The parts are separate mobjects
    (``mobs()``), so that lines can arrive one by one. ``at`` is the top-left corner."""

    def __init__(self, rows, at, fs=19, title="", edge=FAINT, kind="json", w=None,
                 title_color=None, z=Z_CARD, pitch=None):  # fmt: skip
        self.rows, self.fs = rows, fs
        self.pitch = pitch or fs * 0.0182
        cell = MONO_ADV * fs
        self.w = w or max(len(r) for r in rows) * cell + 0.7
        self.h = len(rows) * self.pitch + 0.46
        x0, top = at[0], at[1]
        self.x0, self.top = x0, top
        self.box = RoundedRectangle(width=self.w, height=self.h, corner_radius=0.16)
        self.box.set_stroke(edge, width=2.2).set_fill(CODE_BG, opacity=1)
        self.box.move_to([x0 + self.w / 2, top - self.h / 2, 0])
        self.lines = []
        for i, r in enumerate(rows):
            ln = Chars(r, fs=fs, color=PLAIN, font=MONO)
            ln.at(x0 + 0.35, top - 0.23 - self.pitch * (i + 0.5))
            if kind == "json":
                paint_json(ln)
            elif kind == "http":
                paint_http(ln)
            self.lines.append(ln)
        if kind == "python":
            paint_python(self.lines)
        self.title = None
        if title:
            self.title = small(title, fs=16, color=title_color or edge)
            self.title.move_to([x0 + 0.2 + self.title.width / 2, top + 0.2, 0])
        for m in self.mobs():
            m.set_z_index(z)

    @property
    def center(self):
        return self.box.get_center()

    def mobs(self):
        return [self.box, *([self.title] if self.title is not None else []), *self.lines]

    def line(self, token, nth=0):
        """The ``nth`` line that contains ``token``."""
        return [ln for ln in self.lines if token in ln.string][nth]

    def mark(self, token, color=LOOK_C, nth=0, z=Z_CARD + 1):
        return mark(self.line(token, nth), token, color).set_z_index(z)

    def fade_in(self, shift=UP * 0.15, run_time=0.5, only=None):
        mobs = self.mobs() if only is None else only
        return AnimationGroup(*[FadeIn(m, shift=shift) for m in mobs], run_time=run_time)

    def fade_out(self, run_time=0.4, **kw):
        return AnimationGroup(*[FadeOut(m, **kw) for m in self.mobs()], run_time=run_time)


def veil(opacity=0.84, z=Z_VEIL):
    """Dims the whole stage, under the wire and the close-ups."""
    v = Rectangle(width=15, height=9).set_stroke(width=0).set_fill(BG, opacity=opacity)
    return v.set_z_index(z)


def name_words():
    """The three words of the name, set in the gap between the model and the world:
    (lines, the three initials in gold, to lay over them)."""
    cx = (MODEL_X[1] + SERVER_X[0]) / 2
    lines, caps = [], []
    for i, word in enumerate(("Model", "Context", "Protocol")):
        ln = Chars(word, fs=40, color=MODEL_C if word == "Context" else INK, weight="BOLD")
        ln.at(cx - 1.1, 0.75 - 0.72 * i)
        cap = ln.glyphs[0].copy().set_color(LOOK_C)
        lines.append(ln)
        caps.append(cap)
    return lines, caps


# ---------------------------------------------------------------------------------- #
# Compact actors: for the scenes about the wire, and about many hosts and servers
# ---------------------------------------------------------------------------------- #
def host_tile(center, name="host", w=3.1, h=1.8, clients=1):
    """A host, small: its frame, its user and its model, and its clients on the edge:
    one port per server it talks to (``ports`` lists them, top to bottom)."""
    cx, cy = center
    k = min(1.0, h / 1.8)
    fr = Frame((cx - w / 2, cx + w / 2), HOST_C, name, top=cy + h / 2, bot=cy - h / 2, fs=19)
    who = avatar(0.3 * k).move_to([cx - 0.6, cy - 0.06, 0])
    chip = model_chip(0.6 * k).move_to([cx + 0.5, cy - 0.06, 0])
    side, pitch = (0.34, 0.0) if clients == 1 else (0.2, 0.27)
    ports = [
        client_port(s=side).move_to([cx + w / 2, cy + pitch * ((clients - 1) / 2 - i), 0])
        for i in range(clients)
    ]
    g = VGroup(fr.box, fr.tag, who, chip, *ports)
    g.box, g.port, g.ports = fr.box, ports[0], ports
    return g


def server_tile(center, name="server", label=None, color=SERVER_C, w=3.1, h=1.45):
    """A server, small: its frame, what it runs, its socket on the edge."""
    cx, cy = center
    fr = Frame((cx - w / 2, cx + w / 2), color, name, top=cy + h / 2, bot=cy - h / 2, fs=19)
    parts = [fr.box, fr.tag]
    if label:
        parts.append(gear_icon(0.2, color).move_to([cx - w / 2 + 0.5, cy - 0.06, 0]))
        parts.append(Chars(label, fs=18, color=INK, font=MONO).at(cx - w / 2 + 0.88, cy - 0.06))
    else:
        parts.append(gear_icon(0.24, color).move_to([cx, cy - 0.06, 0]))
    sock = socket_glyph(color).move_to([cx - w / 2 - 0.17, cy, 0])
    g = VGroup(*parts, sock)
    g.box, g.socket = fr.box, sock
    return g


def balancer(center, s=0.62):
    """A load balancer: one way in, several ways out."""
    c = np.array([center[0], center[1], 0.0])
    box = RoundedRectangle(width=s, height=s, corner_radius=0.12)
    box.set_stroke(STEEL, width=3).set_fill(PANEL, opacity=1).move_to(c)
    fan = VGroup(
        *[
            Line(c + LEFT * s * 0.28, c + RIGHT * s * 0.28 + UP * dy)
            for dy in (s * 0.24, 0.0, -s * 0.24)
        ]
    ).set_stroke(STEEL, width=2.5)
    return VGroup(box, fan)


def struck(text, fs=17):
    """A name the protocol no longer has: greyed, struck through."""
    t = Chars(text, fs=fs, color=MUTED, font=MONO)
    line = Line(t.body.get_left() + LEFT * 0.07, t.body.get_right() + RIGHT * 0.07)
    return VGroup(t, line.set_stroke(HOSTILE_C, width=3))


def badge(who):
    """Who decided: the user, the application or the model, as a small mark."""
    if who == "user":
        return avatar(0.13)
    if who == "model":
        return model_chip(0.26)
    win = RoundedRectangle(width=0.32, height=0.25, corner_radius=0.05)
    win.set_stroke(HOST_C, width=2).set_fill(mix(HOST_C, BG, 0.8), opacity=1)
    bar = Line(win.get_corner(UL) + DOWN * 0.08, win.get_corner(UR) + DOWN * 0.08)
    return VGroup(win, bar.set_stroke(HOST_C, width=2))


def badge_on(block, who):
    """That mark, in the top right corner of a block of the context."""
    return badge(who).move_to(
        [block.box.get_right()[0] - 0.28, block.box.get_top()[1] - 0.22, 0]
    )


def door_offers():
    """The two other things the server offers: (prompt, resource)."""
    return (
        offer("prompt", W.PROMPT["name"], WIRE_Y - 0.74),
        offer("resource", W.SCHEMA_URI, WIRE_Y - 1.48, name_fs=16),
    )


def slash_menu(host):
    """The menu a "/" opens above the input bar: the prompt the server listed.
    Returns (box, item)."""
    bar = host.bar
    box = RoundedRectangle(width=bar.width, height=0.5, corner_radius=0.1)
    box.set_stroke(USER_C, width=2).set_fill(PANEL, opacity=1)
    box.move_to([bar.get_center()[0], bar.get_top()[1] + 0.37, 0])
    item = Chars("/" + W.PROMPT["name"], fs=16, color=INK, font=MONO)
    item.at(box.get_left()[0] + 0.2, box.get_center()[1])
    return box, item

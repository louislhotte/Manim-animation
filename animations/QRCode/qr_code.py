"""How QR Codes Work — a short (~3 min) explainer, house-style.

A QR code looks like random noise, but it is a strictly-structured, self-healing
way to store a short string — most often a URL. This film takes one **real,
scannable** QR code (encoding ``https://ptoleme.dev``) and shows, end to end, how
a link becomes that grid of squares:

    1. A link in disguise   -- point a camera at squares, out comes a URL
    2. Text -> bits          -- byte mode: every character becomes 8 bits
    3. Anatomy               -- finders / timing / alignment / format / data
    4. Placing & masking     -- bits snake in bottom-right; a mask evens it out
    5. Error correction      -- cover the middle with a logo, it still scans

The matrix below is not a drawing: it was generated with a real QR encoder
(``segno``: version 2, error level Q, mask 7) and baked in as a literal, so the
code that appears on screen is a genuine, scannable QR for that URL. Everything
structural (which module is a finder, the zig-zag data order, the mask) is
derived from the QR spec at import time — nothing is faked.

Everything uses ``Text`` (Pango), never ``Tex`` — no LaTeX toolchain needed.

Scenes are exposed individually (``Intro``, ``Hook``, ``Encode``, ``Anatomy``,
``Placement``, ``Robustness``, ``Outro``) and as one film (``QRCodes``).

Env knobs:
    QR_QUICK=1     collapse every reading hold (and end-holds) for a fast render
    QR_DELAY=1.6   override the reading-hold multiplier (seconds per "beat")
"""

from __future__ import annotations

import os

import numpy as np
from manim import *

# --- crisp text (shared house fix) ----------------------------------------- #
# Manim's ``Text`` quantises glyph positions badly below ~20 pt. Render every
# glyph at a large base size and scale the mobject *down* — spacing stays crisp.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("QR_QUICK") == "1"
DELAY = float(os.environ.get("QR_DELAY", "0.28" if QUICK else "1.6"))
END_HOLD = 0.2 if QUICK else 2.0
ANIM_SLOW = 1.0 if QUICK else 1.15

# ---- palette -------------------------------------------------------------- #
BG = "#0E1117"
PANEL = "#151A23"
INK = "#F5F3EF"
MUTED = "#8A93A6"
FAINT = "#2A3140"
ACCENT = "#FFD166"
GOOD = "#3DD68C"
BAD = "#FF5C5C"
WARN = "#FFC24B"

# structural accents (one per QR region)
FINDER_C = "#5B8DEF"   # the three big "eyes"
TIMING_C = "#2EC4B6"   # the alternating ruler lines
ALIGN_C = "#C792EA"    # the small alignment square
FORMAT_C = "#F4A259"   # format-info stripe
QUIET_C = "#8A93A6"    # the empty margin
DATA_C = "#3DD68C"     # data + error-correction
SHIELD_C = "#4CC9F0"   # error-correction / robustness

# the printed code itself: dark modules on a light "sticker" card
CARD_C = "#F6F4EF"
MOD_DARK = "#0F1319"

MONO = "Menlo"

# ========================================================================== #
# The real QR code (segno: "https://ptoleme.dev", version 2, level Q, mask 7)
# ========================================================================== #
QR_URL = "https://ptoleme.dev"
QR_VERSION = 2
QR_MASK = 7
_QR_ROWS = [
    "1111111011111011001111111",
    "1000001000101011101000001",
    "1011101010100010001011101",
    "1011101011011011001011101",
    "1011101001010101101011101",
    "1000001011011001001000001",
    "1111111010101010101111111",
    "0000000010101000000000000",
    "0101011110101001111101101",
    "1010010011110100001000001",
    "0010101100011110111110011",
    "1000010110110111100110000",
    "1010111111101010111101011",
    "0001110101011100011101101",
    "1001101100110110000110101",
    "0110000110110001101010010",
    "1100101100101011111111100",
    "0000000010011011100011001",
    "1111111010000011101011011",
    "1000001010101010100011101",
    "1011101001111100111111011",
    "1011101010000010000111100",
    "1011101000001011000110101",
    "1000001011111111111001000",
    "1111111001110011101100011",
]
_N = len(_QR_ROWS)

# ---- structure derived from the QR spec (nothing faked) ------------------- #
_ALIGN = {(_N - 7 + dr, _N - 7 + dc) for dr in range(-2, 3) for dc in range(-2, 3)}
_DARK = (4 * QR_VERSION + 9, 8)          # the one always-dark module
_FMT = set()
for _c in list(range(0, 6)) + [7, 8]:
    _FMT.add((8, _c))
for _r in list(range(0, 6)) + [7, 8]:
    _FMT.add((_r, 8))
for _r in range(_N - 7, _N):
    _FMT.add((_r, 8))
for _c in range(_N - 8, _N):
    _FMT.add((8, _c))
_FMT.discard(_DARK)


def _in_finder(r, c):
    for br, bc in ((0, 0), (0, _N - 7), (_N - 7, 0)):
        if br <= r < br + 7 and bc <= c < bc + 7:
            return True
    return False


def _in_sep(r, c):
    for br, bc in ((0, 0), (0, _N - 8), (_N - 8, 0)):
        if br <= r < br + 8 and bc <= c < bc + 8 and not _in_finder(r, c):
            return True
    return False


def _role(r, c):
    if _in_finder(r, c):
        return "F"
    if _in_sep(r, c):
        return "S"
    if (r, c) == _DARK:
        return "K"
    if (r, c) in _ALIGN:
        return "A"
    if r == 6 or c == 6:
        return "T"          # timing
    if (r, c) in _FMT:
        return "M"          # format info
    return "."              # data + error-correction


def _cells(role):
    return [(r, c) for r in range(_N) for c in range(_N) if _role(r, c) == role]


def _data_order():
    """The real QR placement walk: up/down pairs of columns from bottom-right."""
    order, col, up = [], _N - 1, True
    while col > 0:
        if col == 6:                 # skip the vertical timing column
            col -= 1
            continue
        rows = range(_N - 1, -1, -1) if up else range(0, _N)
        for r in rows:
            for c in (col, col - 1):
                if _role(r, c) == ".":
                    order.append((r, c))
        up = not up
        col -= 2
    return order


def _mask7(r, c):
    return ((r + c) % 2 + (r * c) % 3) % 2 == 0


# ========================================================================== #
# small reusable pieces
# ========================================================================== #
def txt(text, fs=24, color=INK, weight="NORMAL", font=None, slant=None):
    kw = {"font_size": fs, "color": color, "weight": weight}
    if font:
        kw["font"] = font
    if slant:
        kw["slant"] = slant
    return Text(text, **kw)


def chip(text, color, fs=18, fill=0.14, w=None, h=0.54, tcolor=None, weight="NORMAL"):
    label = txt(text, fs=fs, color=tcolor or INK, weight=weight)
    width = (label.width + 0.5) if w is None else w
    box = RoundedRectangle(width=width, height=h, corner_radius=0.12,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=fill)
    label.move_to(box)
    grp = VGroup(box, label)
    grp.box = box
    grp.label = label
    return grp


def arr(a, b, color=MUTED, sw=4, buff=0.14, tip=0.22):
    return Arrow(a, b, buff=buff, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.35, tip_length=tip)


def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])])
    return v.set_stroke(color=color, width=sw).scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.16, -0.16, 0], [0.16, 0.16, 0])
    b = Line([-0.16, 0.16, 0], [0.16, -0.16, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


def globe(color=SHIELD_C, r=0.16):
    """A tiny web/URL glyph: circle + a meridian + a parallel."""
    c = Circle(radius=r, stroke_color=color, stroke_width=2.5, fill_opacity=0)
    merid = Ellipse(width=r * 0.9, height=r * 2, color=color).set_stroke(
        color=color, width=2).set_fill(opacity=0)
    par = Line([-r, 0, 0], [r, 0, 0], stroke_color=color, stroke_width=2)
    return VGroup(c, merid, par)


def phone(w=1.85, h=3.5):
    body = RoundedRectangle(width=w, height=h, corner_radius=0.24,
                            stroke_color=INK, stroke_width=3,
                            fill_color=PANEL, fill_opacity=1.0)
    screen = RoundedRectangle(width=w - 0.28, height=h - 0.66, corner_radius=0.12,
                              stroke_width=0, fill_color="#0A0E15", fill_opacity=1.0)
    screen.move_to(body)
    cam = Dot(radius=0.035, color=MUTED).move_to(body.get_top() + DOWN * 0.2)
    home = Line(LEFT * 0.28, RIGHT * 0.28, stroke_color=MUTED, stroke_width=3)
    home.move_to(body.get_bottom() + UP * 0.2)
    grp = VGroup(body, screen, cam, home)
    grp.screen = screen
    grp.body = body
    return grp


def viewfinder(center, size, color=SHIELD_C, ln=0.22, sw=4):
    """Four corner brackets forming a scan reticle."""
    h = size / 2
    g = VGroup()
    for sx, sy in ((-1, 1), (1, 1), (1, -1), (-1, -1)):
        cx, cy = center[0] + sx * h, center[1] + sy * h
        a = Line([cx, cy, 0], [cx - sx * ln, cy, 0], stroke_color=color, stroke_width=sw)
        b = Line([cx, cy, 0], [cx, cy - sy * ln, 0], stroke_color=color, stroke_width=sw)
        g.add(a, b)
    return g


def logo_badge(letter="P", color=ACCENT, side=1.15):
    halo = RoundedRectangle(width=side + 0.14, height=side + 0.14, corner_radius=0.18,
                            stroke_width=0, fill_color=CARD_C, fill_opacity=1.0)
    box = RoundedRectangle(width=side, height=side, corner_radius=0.16,
                           stroke_color=color, stroke_width=4,
                           fill_color="#1B2130", fill_opacity=1.0)
    box.move_to(halo)
    mark = txt(letter, fs=int(side * 44), color=color, weight="BOLD").move_to(box)
    return VGroup(halo, box, mark)


# ========================================================================== #
# the QR code as a Manim mobject
# ========================================================================== #
def make_qr(rows=_QR_ROWS, module=0.176):
    """A real QR code as a light 'sticker' card + a grid of module squares.

    Returns a VGroup with ``.mods`` (2-D list of Squares), ``.card``, ``.module``.
    Dark modules are opaque; light modules are transparent (the card shows
    through) so recolouring/highlighting is easy and seams never split a block.
    """
    n = len(rows)
    span = n * module
    quiet = 3
    side = span + 2 * quiet * module
    card = RoundedRectangle(width=side, height=side, corner_radius=0.16,
                            stroke_color=FAINT, stroke_width=2,
                            fill_color=CARD_C, fill_opacity=1.0)
    card.move_to(ORIGIN)
    mods = [[None] * n for _ in range(n)]
    squares = VGroup()
    inflate = 1.04                     # kill sub-pixel seams inside dark blocks
    for r in range(n):
        for c in range(n):
            dark = rows[r][c] == "1"
            s = Square(side_length=module * inflate, stroke_width=0,
                       fill_color=MOD_DARK if dark else CARD_C,
                       fill_opacity=1.0 if dark else 0.0)
            s.move_to([-span / 2 + (c + 0.5) * module,
                       span / 2 - (r + 0.5) * module, 0])
            mods[r][c] = s
            squares.add(s)
    grp = VGroup(card, squares)
    grp.card = card
    grp.squares = squares
    grp.mods = mods
    grp.module = module
    grp.n = n
    return grp


def _mw(qr):
    return qr.mods[0][0].width


def _center(qr, r, c):
    return qr.mods[r][c].get_center()


def region_tint(qr, cells, color, opacity=0.5):
    w = _mw(qr)
    g = VGroup()
    for r, c in cells:
        s = Square(side_length=w, stroke_width=0, fill_color=color, fill_opacity=opacity)
        s.move_to(_center(qr, r, c))
        g.add(s)
    return g


def region_box(qr, cells, color, pad=0.14, sw=3.5, radius=0.1):
    w = _mw(qr)
    xs = [_center(qr, r, c)[0] for r, c in cells]
    ys = [_center(qr, r, c)[1] for r, c in cells]
    left, right = min(xs) - w / 2, max(xs) + w / 2
    bot, top = min(ys) - w / 2, max(ys) + w / 2
    p = w * pad
    rect = RoundedRectangle(width=(right - left) + 2 * p, height=(top - bot) + 2 * p,
                            corner_radius=radius, stroke_color=color, stroke_width=sw,
                            fill_opacity=0)
    rect.move_to([(left + right) / 2, (top + bot) / 2, 0])
    return rect


# ========================================================================== #
class _QRBase(Scene):
    def setup(self):
        self.camera.background_color = BG
        self._cap = None

    def play(self, *anims, **kwargs):
        is_wait = any(type(a).__name__ == "Wait" for a in anims)
        if not QUICK and anims and not is_wait:
            rt = kwargs.get("run_time")
            if rt is None:
                rts = [r for r in (getattr(a, "run_time", None) for a in anims) if r]
                rt = max(rts) if rts else 1.0
            kwargs["run_time"] = rt * ANIM_SLOW
        return super().play(*anims, **kwargs)

    # ---- timing helpers --------------------------------------------------- #
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.25 if QUICK else 1.0))

    def settle(self):
        self.wait(END_HOLD)

    def wipe(self, rt=0.6):
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)
        self._cap = None

    # ---- headers & captions ---------------------------------------------- #
    def section_header(self, part, label, color):
        tag = txt(part, fs=20, color=color, weight="BOLD")
        tagbox = RoundedRectangle(width=tag.width + 0.4, height=0.44, corner_radius=0.1,
                                  stroke_color=color, stroke_width=2,
                                  fill_color=color, fill_opacity=0.12)
        tag.move_to(tagbox)
        title = txt(label, fs=32, color=INK, weight="BOLD")
        head = VGroup(VGroup(tagbox, tag), title).arrange(RIGHT, buff=0.3)
        head.to_corner(UL, buff=0.5)
        line = Line(head.get_left(), head.get_right()).next_to(head, DOWN, buff=0.13)
        line.set_stroke(color=color, width=3)
        grp = VGroup(head, line)
        self.play(FadeIn(head, shift=RIGHT * 0.2), Create(line), run_time=0.7)
        return grp

    def say(self, text, color=INK, fs=25, rt=0.5, weight="BOLD"):
        new = txt(text, fs=fs, color=color, weight=weight).to_edge(DOWN, buff=0.42)
        if new.width > 12.6:
            new.scale_to_fit_width(12.6)
        if self._cap is None:
            self._cap = new
            self.play(FadeIn(new, shift=UP * 0.12), run_time=rt)
        else:
            self.play(ReplacementTransform(self._cap, new), run_time=rt)
            self._cap = new
        return new

    def clear_cap(self, rt=0.4):
        if self._cap is not None:
            self.play(FadeOut(self._cap), run_time=rt)
            self._cap = None

    # ---- bookend cards ---------------------------------------------------- #
    def _bookend_title(self, title, subtitle=None):
        header = txt(title, fs=48, color=INK, weight="BOLD")
        if header.width > 11.5:
            header.scale_to_fit_width(11.5)
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=ACCENT)
        writer = txt("Created by Ptolémé", fs=28, color=ACCENT)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.4)
        self.card_wait(0.6)
        if subtitle:
            sub = txt(subtitle, fs=28, color=MUTED)
            if sub.width > 12:
                sub.scale_to_fit_width(12)
            sub.move_to(header)
            self.play(Transform(header, sub), run_time=0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        return VGroup(header, writer, line)

    def play_intro(self):
        # a small QR assembles above the title
        mini = make_qr(module=0.12).scale(0.62).to_edge(UP, buff=0.55)
        darks = VGroup(*[mini.mods[r][c] for r in range(_N) for c in range(_N)
                         if _QR_ROWS[r][c] == "1"])
        for s in darks:
            s.save_state()
            s.set_opacity(0)
        self.play(FadeIn(mini.card, scale=0.9), run_time=0.7)
        self.play(LaggedStart(*[Restore(s) for s in darks], lag_ratio=0.004),
                  run_time=1.4)
        vf = viewfinder(mini.card.get_center(), mini.card.width + 0.18,
                        color=ACCENT, ln=0.28, sw=4)
        self.play(Create(vf), run_time=0.6)
        grp = self._bookend_title(
            "How QR Codes Work",
            "how a link becomes a grid of squares")
        self.card_wait(1.6)
        self.play(FadeOut(grp), FadeOut(mini), FadeOut(vf), run_time=0.9)
        self.card_wait(0.2)

    def play_outro(self):
        self.card_wait(0.3)
        recap1 = txt("A link → bits → a structured,", fs=27, color=MUTED)
        recap2 = txt("self-healing grid of squares.", fs=27, color=MUTED)
        recap = VGroup(recap1, recap2).arrange(DOWN, buff=0.16).move_to(UP * 1.35)
        self.play(FadeIn(recap, shift=UP * 0.2), run_time=0.9)
        self.card_wait(1.2)
        header = txt("Thanks for watching!", fs=46, color=INK, weight="BOLD")
        header.move_to(DOWN * 0.35)
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=ACCENT)
        writer = txt("Created by Ptolémé", fs=28, color=ACCENT)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.2)
        self.card_wait(0.5)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.card_wait(1.6)
        self.play(FadeOut(VGroup(recap, header, line, writer)), run_time=1.0)
        self.card_wait(0.3)

    # ====================================================================== #
    # Scene 1 — A link in disguise
    # ====================================================================== #
    def scene_hook(self):
        self.section_header("01", "A Link in Disguise", ACCENT)

        qr = make_qr().scale(0.86).move_to(LEFT * 2.85 + DOWN * 0.5)
        self.play(FadeIn(qr.card, scale=0.96), run_time=0.6)
        darks = VGroup(*[qr.mods[r][c] for r in range(_N) for c in range(_N)
                         if _QR_ROWS[r][c] == "1"])
        for s in darks:
            s.save_state()
            s.set_opacity(0)
        self.play(LaggedStart(*[Restore(s) for s in darks], lag_ratio=0.002), run_time=1.3)
        self.say("A QR code is just black-and-white squares.", color=INK)
        self.beat(1.4)

        ph = phone().scale(0.9).move_to(RIGHT * 3.9 + DOWN * 0.4)
        self.play(FadeIn(ph, shift=LEFT * 0.3), run_time=0.7)
        vf = viewfinder(ph.screen.get_center(), ph.screen.width - 0.35,
                        color=SHIELD_C, ln=0.2, sw=3.5)
        self.play(Create(vf), run_time=0.5)
        self.say("Point a camera at it…", color=SHIELD_C)

        # a scan line sweeps the code
        line = Rectangle(width=qr.card.width * 0.92, height=0.06, stroke_width=0,
                         fill_color=SHIELD_C, fill_opacity=0.9)
        glow = Rectangle(width=qr.card.width * 0.92, height=0.34, stroke_width=0,
                         fill_color=SHIELD_C, fill_opacity=0.18)
        scan = VGroup(glow, line).move_to([qr.card.get_center()[0], qr.card.get_top()[1] - 0.2, 0])
        self.add(scan)
        self.play(scan.animate.move_to([qr.card.get_center()[0], qr.card.get_bottom()[1] + 0.2, 0]),
                  run_time=1.3, rate_func=linear)
        self.play(FadeOut(scan), run_time=0.3)

        # the URL resolves on the phone screen
        check = make_tick(GOOD, sw=8, scale=1.2).move_to(ph.screen.get_center() + UP * 0.55)
        url = txt(QR_URL, fs=15, color=INK, weight="BOLD")
        gl = globe(SHIELD_C, r=0.13)
        urow = VGroup(gl, url).arrange(RIGHT, buff=0.12)
        if urow.width > ph.screen.width - 0.3:
            urow.scale_to_fit_width(ph.screen.width - 0.3)
        urow.move_to(ph.screen.get_center() + DOWN * 0.35)
        open_lbl = txt("Opening link…", fs=13, color=MUTED).next_to(urow, DOWN, buff=0.18)
        self.play(FadeOut(vf), GrowFromCenter(check), run_time=0.5)
        self.play(FadeIn(urow, shift=UP * 0.1), FadeIn(open_lbl), run_time=0.6)
        self.say("…and out comes a link.", color=GOOD)
        self.beat(1.6)

        # the reveal: it isn't random
        big = chip(QR_URL, SHIELD_C, fs=20, w=4.4, h=0.7, weight="BOLD", tcolor=INK)
        big.next_to(qr, UP, buff=0.3)
        if big.get_top()[1] > 2.8:                     # never collide the header
            big.shift(DOWN * (big.get_top()[1] - 2.8))
        self.play(FadeIn(big, shift=UP * 0.15),
                  Flash(qr.card.get_center(), color=SHIELD_C, line_length=0.3,
                        flash_radius=qr.card.width * 0.55), run_time=0.7)
        self.say("Those squares aren't random — they encode this URL.", color=SHIELD_C)
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — Text -> bits
    # ====================================================================== #
    def scene_encode(self):
        self.section_header("02", "From Text to Bits", FINDER_C)

        # the URL as a row of character tiles
        chars = list(QR_URL)
        tiles = VGroup()
        for ch in chars:
            box = Square(side_length=0.5, stroke_color=FINDER_C, stroke_width=2,
                         fill_color=FINDER_C, fill_opacity=0.10)
            glyph = txt(ch if ch != " " else "·", fs=19, color=INK, weight="BOLD").move_to(box)
            tiles.add(VGroup(box, glyph))
        tiles.arrange(RIGHT, buff=0.06)
        if tiles.width > 12.4:
            tiles.scale_to_fit_width(12.4)
        tiles.move_to(UP * 2.05)
        self.play(LaggedStart(*[FadeIn(t, shift=DOWN * 0.15) for t in tiles],
                              lag_ratio=0.04), run_time=1.1)
        self.say("Start with the link — to a computer, just text.", color=INK)
        self.beat(1.3)

        mode = chip("byte mode · 1 byte per character", FINDER_C, fs=16, w=5.0, h=0.5)
        mode.next_to(tiles, DOWN, buff=0.45)
        self.play(FadeIn(mode, shift=UP * 0.1), run_time=0.5)
        self.say("A URL is stored in byte mode — each character is one byte.", color=FINDER_C)
        self.beat(1.6)

        # map three example characters: char -> decimal -> 8 bits
        def bit_row(ch):
            code = ord(ch)
            bits = format(code, "08b")
            t_ch = txt(ch, fs=22, color=INK, weight="BOLD")
            cbox = Square(side_length=0.5, stroke_color=FINDER_C, stroke_width=2,
                          fill_color=FINDER_C, fill_opacity=0.12)
            t_ch.move_to(cbox)
            a1 = txt("→", fs=20, color=MUTED)
            dec = txt(str(code), fs=20, color=WARN, font=MONO)
            a2 = txt("→", fs=20, color=MUTED)
            bit = txt(bits, fs=22, color=DATA_C, font=MONO)
            row = VGroup(VGroup(cbox, t_ch), a1, dec, a2, bit).arrange(RIGHT, buff=0.26)
            return row, bits

        rows = VGroup()
        allbits = []
        for ch in QR_URL[:3]:
            row, bits = bit_row(ch)
            rows.add(row)
            allbits.append(bits)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.24)
        rows.next_to(mode, DOWN, buff=0.5)
        colhdr = VGroup(
            txt("char", fs=14, color=MUTED),
            txt("code", fs=14, color=MUTED),
            txt("8 bits", fs=14, color=MUTED),
        )
        # align headers roughly over the columns of the first row
        colhdr[0].next_to(rows[0][0], UP, buff=0.18)
        colhdr[1].next_to(rows[0][2], UP, buff=0.18)
        colhdr[2].next_to(rows[0][4], UP, buff=0.18)
        self.play(FadeIn(colhdr), run_time=0.4)
        for row in rows:
            self.play(FadeIn(row[0], shift=RIGHT * 0.1), run_time=0.35)
            self.play(FadeIn(row[1]), FadeIn(row[2], shift=RIGHT * 0.1), run_time=0.3)
            self.play(FadeIn(row[3]), FadeIn(row[4], shift=RIGHT * 0.1), run_time=0.35)
        self.say("Look up each character's code, write it in 8 bits.", color=DATA_C)
        self.beat(1.8)

        # collapse to one long bit stream
        self.play(FadeOut(colhdr), FadeOut(mode),
                  rows.animate.scale(0.9).next_to(tiles, DOWN, buff=0.4), run_time=0.6)
        stream_txt = "".join(allbits) + "01101100…"
        stream = txt(stream_txt, fs=20, color=DATA_C, font=MONO)
        if stream.width > 12.4:
            stream.scale_to_fit_width(12.4)
        stream.next_to(rows, DOWN, buff=0.55)
        slbl = txt("the whole link, as one binary string", fs=15, color=MUTED)
        slbl.next_to(stream, DOWN, buff=0.2)
        self.play(Write(stream), run_time=1.0)
        self.play(FadeIn(slbl), run_time=0.4)
        self.say("Every character becomes 8 bits — the link is now binary.", color=DATA_C)
        self.beat(1.8)

        # what actually gets packed
        self.clear_cap(0.4)
        self.play(FadeOut(tiles), FadeOut(rows), FadeOut(stream), FadeOut(slbl), run_time=0.5)
        seg_specs = [("mode", FINDER_C, 1.4), ("length", WARN, 1.6),
                     ("your link, as bits", DATA_C, 5.0),
                     ("error-correction bytes", SHIELD_C, 4.2)]
        segs = VGroup()
        for name, col, w in seg_specs:
            segs.add(chip(name, col, fs=15, w=w, h=0.7, fill=0.16))
        segs.arrange(RIGHT, buff=0.12)
        if segs.width > 12.6:
            segs.scale_to_fit_width(12.6)
        segs.move_to(UP * 0.35)
        cap = txt("This is what gets placed into the grid:", fs=22, color=INK, weight="BOLD")
        cap.next_to(segs, UP, buff=0.5)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.5)
        self.play(LaggedStart(*[GrowFromEdge(s, LEFT) for s in segs], lag_ratio=0.15),
                  run_time=1.2)
        self.say("Add a short header and error-correction bytes — ready to place.",
                color=SHIELD_C)
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Anatomy
    # ====================================================================== #
    def scene_anatomy(self):
        self.section_header("03", "Not All Squares Are Data", ALIGN_C)

        qr = make_qr().scale(0.9).move_to(LEFT * 3.05 + DOWN * 0.2)
        self.play(FadeIn(qr, shift=RIGHT * 0.2), run_time=0.8)
        self.say("Zoom in: the code is built from fixed parts + your data.", color=INK)
        self.beat(1.2)

        legend_specs = [
            ("Quiet zone", QUIET_C, "quiet"),
            ("Finder patterns", FINDER_C, "finder"),
            ("Timing pattern", TIMING_C, "timing"),
            ("Alignment", ALIGN_C, "align"),
            ("Format info", FORMAT_C, "format"),
            ("Data + error-correction", DATA_C, "data"),
        ]
        rows = VGroup()
        for name, col, _ in legend_specs:
            sw = Square(side_length=0.28, stroke_width=0, fill_color=col, fill_opacity=0.9)
            lbl = txt(name, fs=18, color=INK)
            row = VGroup(sw, lbl).arrange(RIGHT, buff=0.22)
            if row.width > 3.7:
                row.scale_to_fit_width(3.7)
            rows.add(row)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(RIGHT * 3.95 + DOWN * 0.2)

        captions = {
            "quiet": ("An empty margin so a scanner finds the edges.", QUIET_C),
            "finder": ("Three big 'eyes' fix orientation — found first.", FINDER_C),
            "timing": ("An alternating line: a ruler for the grid size.", TIMING_C),
            "align": ("Keeps the grid true when the code is tilted.", ALIGN_C),
            "format": ("A stripe naming the error level and mask used.", FORMAT_C),
            "data": ("Everything left carries your link — and its backup.", DATA_C),
        }

        highlights = {}
        for i, (name, col, key) in enumerate(legend_specs):
            if key == "quiet":
                hi = RoundedRectangle(width=qr.card.width - 0.08, height=qr.card.height - 0.08,
                                      corner_radius=0.14, stroke_color=col, stroke_width=4,
                                      fill_opacity=0).move_to(qr.card)
            elif key == "finder":
                hi = VGroup(*[region_box(qr, [(br + dr, bc + dc) for dr in range(7)
                                              for dc in range(7)], col, sw=4)
                             for br, bc in ((0, 0), (0, _N - 7), (_N - 7, 0))])
            elif key == "timing":
                hi = VGroup(
                    region_box(qr, [(6, c) for c in range(8, 17)], col, sw=3.5),
                    region_box(qr, [(r, 6) for r in range(8, 17)], col, sw=3.5),
                )
            elif key == "align":
                hi = region_box(qr, list(_ALIGN), col, sw=4)
            elif key == "format":
                hi = region_tint(qr, _cells("M"), col, opacity=0.72)
            else:
                hi = region_tint(qr, _cells("."), col, opacity=0.38)
            highlights[key] = hi

            self.play(FadeIn(rows[i], shift=LEFT * 0.15), FadeIn(hi), run_time=0.5)
            self.say(*captions[key])
            self.beat(1.3)
            if key not in ("data",):
                self.play(FadeOut(hi), run_time=0.35)

        # final "exploded" composite: everybody at once
        self.clear_cap(0.4)
        composite = VGroup(
            region_tint(qr, _cells("F") + _cells("S"), FINDER_C, 0.6),
            region_tint(qr, _cells("T"), TIMING_C, 0.7),
            region_tint(qr, list(_ALIGN), ALIGN_C, 0.65),
            region_tint(qr, _cells("M") + [_DARK], FORMAT_C, 0.65),
        )
        self.play(FadeIn(composite), run_time=0.8)
        self.say("Fixed patterns are the scaffolding; the rest is your link.",
                color=INK)
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Placing & masking
    # ====================================================================== #
    def scene_placement(self):
        self.section_header("04", "Placing & Masking", DATA_C)

        qr = make_qr().scale(0.98).move_to(LEFT * 1.7 + DOWN * 0.12)
        data_cells = _data_order()
        data_set = set(data_cells)

        # start with only the function patterns visible; data cells emptied
        for r in range(_N):
            for c in range(_N):
                if (r, c) in data_set:
                    qr.mods[r][c].set_opacity(0)
        self.play(FadeIn(qr, shift=RIGHT * 0.1), run_time=0.8)
        self.say("Place the fixed patterns first — the rest is empty space.", color=INK)
        self.beat(1.4)

        # faint "slots" over every data cell
        slots = region_tint(qr, data_cells, DATA_C, opacity=0.12)
        self.play(FadeIn(slots), run_time=0.5)

        # a little "reading order" inset on the right
        inset = VGroup(
            txt("reading order", fs=16, color=MUTED),
            VGroup(
                arr(DOWN * 0.5, UP * 0.5, color=DATA_C, sw=4, buff=0.02),
                arr(UP * 0.5, DOWN * 0.5, color=DATA_C, sw=4, buff=0.02),
            ).arrange(RIGHT, buff=0.4),
            txt("2 columns\nat a time", fs=14, color=MUTED),
        ).arrange(DOWN, buff=0.2)
        inset.move_to(RIGHT * 4.7 + DOWN * 0.1)
        self.play(FadeIn(inset), run_time=0.5)

        # place the UNMASKED data bits, in the real zig-zag order
        reveal = []
        for r, c in data_cells:
            unmasked_dark = (int(_QR_ROWS[r][c]) ^ (1 if _mask7(r, c) else 0)) == 1
            m = qr.mods[r][c]
            m.set_fill(MOD_DARK if unmasked_dark else CARD_C,
                       opacity=1.0 if unmasked_dark else 0.0)
            if unmasked_dark:
                m.save_state()
                m.set_opacity(0)
                reveal.append(m)
        self.say("Bits snake in from the bottom-right, zig-zagging up and down.",
                color=DATA_C)
        self.play(LaggedStart(*[Restore(m) for m in reveal], lag_ratio=0.006),
                  run_time=3.0)
        self.beat(1.2)

        # the raw pattern can clump — enter masking
        self.play(FadeOut(slots), FadeOut(inset), run_time=0.4)
        self.say("Raw, that can leave big blank patches — hard to scan.", color=WARN)
        self.beat(1.4)

        mask_cells = [(r, c) for (r, c) in data_cells if _mask7(r, c)]
        mask_tint = region_tint(qr, mask_cells, SHIELD_C, opacity=0.5)
        mlabel = chip("XOR  mask #7", SHIELD_C, fs=16, w=2.7, h=0.5)
        mlabel.move_to(RIGHT * 4.6 + UP * 0.2)
        self.play(FadeIn(mask_tint), FadeIn(mlabel, shift=UP * 0.1), run_time=0.7)
        self.say("So one of eight mask patterns is XOR-ed over the data…", color=SHIELD_C)
        self.beat(1.4)

        # apply the mask: flip every data cell the mask covers -> the real code
        flips = []
        for r, c in mask_cells:
            real_dark = _QR_ROWS[r][c] == "1"
            flips.append(qr.mods[r][c].animate.set_fill(
                MOD_DARK if real_dark else CARD_C, opacity=1.0 if real_dark else 0.0))
        self.play(FadeOut(mask_tint),
                  LaggedStart(*flips, lag_ratio=0.004), run_time=1.6)
        self.say("…flipping cells to even out light and dark. Now it scans.", color=GOOD)
        self.play(Flash(qr.card.get_center(), color=GOOD, line_length=0.3,
                        flash_radius=qr.card.width * 0.55), run_time=0.6)
        self.beat(1.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — Error correction / robustness
    # ====================================================================== #
    def scene_robust(self):
        self.section_header("05", "Damage It — It Still Works", SHIELD_C)

        qr = make_qr().scale(0.92).move_to(LEFT * 2.7 + DOWN * 0.15)
        self.play(FadeIn(qr, shift=RIGHT * 0.15), run_time=0.7)
        self.say("Remember those error-correction bytes? Here's the payoff.", color=INK)
        self.beat(1.4)

        ph = phone().scale(0.95).move_to(RIGHT * 3.9 + DOWN * 0.15)
        self.play(FadeIn(ph, shift=LEFT * 0.2), run_time=0.6)

        # slap a logo over the middle of the code — kept small enough that the
        # real code genuinely still decodes (level-Q tolerates a ~7-module patch)
        logo = logo_badge("P", ACCENT, side=0.9).move_to(qr.card.get_center())
        self.play(FadeIn(logo, scale=1.4), run_time=0.6)
        self.say("Cover the middle with a logo — data lost underneath.", color=WARN)
        self.beat(1.6)

        # scan it anyway
        vf = viewfinder(ph.screen.get_center(), ph.screen.width - 0.35,
                        color=SHIELD_C, ln=0.2, sw=3.5)
        self.play(Create(vf), run_time=0.4)
        line = Rectangle(width=qr.card.width * 0.92, height=0.06, stroke_width=0,
                         fill_color=SHIELD_C, fill_opacity=0.9)
        glow = Rectangle(width=qr.card.width * 0.92, height=0.34, stroke_width=0,
                         fill_color=SHIELD_C, fill_opacity=0.18)
        scan = VGroup(glow, line).move_to([qr.card.get_center()[0], qr.card.get_top()[1] - 0.2, 0])
        self.add(scan)
        self.play(scan.animate.move_to(
            [qr.card.get_center()[0], qr.card.get_bottom()[1] + 0.2, 0]),
            run_time=1.2, rate_func=linear)
        self.play(FadeOut(scan), run_time=0.25)

        check = make_tick(GOOD, sw=8, scale=1.2).move_to(ph.screen.get_center() + UP * 0.55)
        url = txt(QR_URL, fs=15, color=INK, weight="BOLD")
        gl = globe(SHIELD_C, r=0.13)
        urow = VGroup(gl, url).arrange(RIGHT, buff=0.12)
        if urow.width > ph.screen.width - 0.3:
            urow.scale_to_fit_width(ph.screen.width - 0.3)
        urow.move_to(ph.screen.get_center() + DOWN * 0.35)
        self.play(FadeOut(vf), GrowFromCenter(check),
                  FadeIn(urow, shift=UP * 0.1), run_time=0.6)
        self.say("It still resolves to the link — nothing missing.", color=GOOD)
        self.beat(1.6)

        # why: a recoverability meter
        track = RoundedRectangle(width=4.4, height=0.42, corner_radius=0.1,
                                 stroke_color=FAINT, stroke_width=2,
                                 fill_color=PANEL, fill_opacity=1.0)
        fill = RoundedRectangle(width=4.4 * 0.25, height=0.42, corner_radius=0.1,
                                stroke_width=0, fill_color=SHIELD_C, fill_opacity=0.85)
        fill.align_to(track, LEFT).move_to([track.get_left()[0] + fill.width / 2,
                                            track.get_center()[1], 0])
        meter = VGroup(track, fill)
        mlbl = txt("level Q → up to ~25% recoverable", fs=16, color=SHIELD_C)
        mgrp = VGroup(mlbl, meter).arrange(DOWN, buff=0.2)
        mgrp.move_to(RIGHT * 3.9 + DOWN * 2.5)         # under the phone, clear of the caption
        self.play(FadeIn(mlbl), Create(track), run_time=0.5)
        self.play(GrowFromEdge(fill, LEFT), run_time=0.7)
        self.say("Reed–Solomon math rebuilds the covered bits from the rest.",
                color=SHIELD_C)
        self.beat(1.8)

        # the one caveat
        self.clear_cap(0.4)
        self.play(FadeOut(VGroup(ph, check, urow, mgrp)), run_time=0.5)
        self.play(qr.animate.scale(1.0).move_to(LEFT * 3.0 + DOWN * 0.15), run_time=0.5)
        finders = VGroup(*[region_box(qr, [(br + dr, bc + dc) for dr in range(7)
                                           for dc in range(7)], FINDER_C, sw=4)
                          for br, bc in ((0, 0), (0, _N - 7), (_N - 7, 0))])
        note1 = txt("The one rule:", fs=26, color=INK, weight="BOLD")
        note2 = txt("keep the three eyes", fs=24, color=FINDER_C, weight="BOLD")
        note3 = txt("clear — the scanner", fs=24, color=INK)
        note4 = txt("needs them to lock on.", fs=24, color=INK)
        notes = VGroup(note1, note2, note3, note4).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        notes.move_to(RIGHT * 3.2 + DOWN * 0.15)
        self.play(Create(finders), run_time=0.6)
        self.play(FadeIn(notes, shift=RIGHT * 0.15), run_time=0.7)
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ---- the whole film --------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_hook()
        self.scene_encode()
        self.scene_anatomy()
        self.scene_placement()
        self.scene_robust()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_QRBase):
    def construct(self):
        self.play_intro()


class Hook(_QRBase):
    def construct(self):
        self.scene_hook()


class Encode(_QRBase):
    def construct(self):
        self.scene_encode()


class Anatomy(_QRBase):
    def construct(self):
        self.scene_anatomy()


class Placement(_QRBase):
    def construct(self):
        self.scene_placement()


class Robustness(_QRBase):
    def construct(self):
        self.scene_robust()


class Outro(_QRBase):
    def construct(self):
        self.play_outro()


class QRCodes(_QRBase):
    """The whole ~3 minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    QRCodes().render()

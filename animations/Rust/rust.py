"""What is Rust? — a short, house-style explainer.

Rust is a compiled systems programming language whose claim to fame is doing
two things at once that used to be a trade-off: memory safety and C-level
speed. It gets both from one idea, ownership, enforced by the borrow checker
at compile time, so the finished binary carries no garbage collector and no
runtime checks.

The film builds the idea in eight beats:

    1. Definition  — what Rust actually is (compiled, systems-level, no GC)
    2. Tradeoff    — the old safety-vs-speed chart, and the empty corner
    3. Ownership   — one owner per value, freed at scope end, moves
                     (with rustc's REAL E0382 error, captured verbatim)
    4. Borrowing   — shared & vs exclusive &mut: many readers XOR one writer
    5. Dangling    — the use-after-free that `Vec::push` reallocation causes,
                     and the REAL E0502 borrow-checker rejection
    6. Speed       — no GC pauses, checks at compile time, zero-cost abstractions
    7. Bench       — a REAL measured benchmark baked by generate_assets.py:
                     the same prime-count loop in CPython vs rustc -O (~54x)
    8. World       — Linux kernel, Android's memory-bug drop, most admired

Everything is drawn with Manim ``Text`` (Pango), never ``Tex`` — no LaTeX.
Scenes render individually (``Definition``, ``Tradeoff``, ``Ownership``,
``Borrow``, ``Dangling``, ``Speed``, ``Bench``, ``World``, ``Intro``,
``Outro``) or as one film (``WhatIsRust``).

Env knobs:
    RS_QUICK=1   collapse every hold for a fast sanity render
    RS_DELAY=..  reading-rhythm multiplier for small inter-step pauses
    RS_READ=..   absolute hold after a caption lands (seconds) — reading time
"""
from __future__ import annotations

import json
import os

import numpy as np
from manim import *

# --- crisp text (shared house fix) ----------------------------------------- #
# Manim's ``Text`` mangles letter/word spacing below ~20 pt. Render every glyph
# at a large base size and scale the mobject *down* — spacing stays crisp. This
# shadow is MANDATORY (it also fixes super/subscripts rendered by helpers).
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("RS_QUICK") == "1"
DELAY = float(os.environ.get("RS_DELAY", 0.28 if QUICK else 1.0))
READ = float(os.environ.get("RS_READ", 0.32 if QUICK else 2.35))
ANIM_SLOW = 1.0 if QUICK else 1.25
END_HOLD = 0.2 if QUICK else 2.1  # settle held on a finished scene before it wipes

# ---- palette (dark house style, shared across the series) ----------------- #
BG = "#0E1117"          # dark slate background
PANEL = "#151A23"       # panel fill
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
FAINT = "#2A3140"       # gridlines / faint wires
GOLD = "#FFD166"        # accent / rules

RUST_C = "#F97B4F"      # Rust itself — warm rust orange — HERO
SAFE_C = "#3DD68C"      # memory safety / shared borrows / pass (green)
BAD = "#FF5C5C"         # errors, dangling pointers, GC pauses (red)
GC_C = "#5B8DEF"        # managed / garbage-collected languages (indigo)
CPP_C = "#C792EA"       # C and C++ (violet)
ACCENT = GOLD

MONO = "Menlo"          # code / compiler output
FONT = "Helvetica Neue"
_BaseText.set_default(font=FONT)

NBSP = " "         # Pango trims real leading spaces; NBSP survives

# ---- real, baked data (see generate_assets.py) ----------------------------- #
_BENCH_FALLBACK = {
    "limit": 1_000_000, "count": 78_498,
    "py_s": 2.4311, "rs_s": 0.04507, "speedup": 53.9,
    "py_ver": "CPython 3.12.12", "rs_ver": "rustc 1.93.0", "chip": "Apple M4 Max",
}

_ERRORS_FALLBACK = {
    "move": (
        "error[E0382]: borrow of moved value: `s`\n"
        " --> move_demo.rs:4:16\n"
        "  |\n"
        "3 |     let t = s;\n"
        "  |             - value moved here\n"
        "4 |     println!(\"{s}\");\n"
        "  |                ^ value borrowed here after move\n"
        "  |\n"
        "help: consider cloning the value if the performance cost is acceptable\n"
        "  |\n"
        "3 |     let t = s.clone();\n"
        "  |              ++++++++\n"
    ),
    "borrow": (
        "error[E0502]: cannot borrow `v` as mutable because it is also "
        "borrowed as immutable\n"
        " --> borrow_demo.rs:4:5\n"
        "  |\n"
        "3 |     let first = &v[0];\n"
        "  |                  - immutable borrow occurs here\n"
        "4 |     v.push(4);\n"
        "  |     ^^^^^^^^^ mutable borrow occurs here\n"
        "5 |     println!(\"{first}\");\n"
        "  |                ----- immutable borrow later used here\n"
    ),
}


def _load_asset(name, fallback):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", name)
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return dict(fallback)


BENCH = _load_asset("bench.json", _BENCH_FALLBACK)
ERRORS = _load_asset("errors.json", _ERRORS_FALLBACK)
if BENCH.get("limit") == 1_000_000:
    assert BENCH["count"] == 78_498, BENCH["count"]  # π(10^6), a known constant
SPEEDUP = int(round(BENCH["speedup"]))

# ---- code-panel syntax colours --------------------------------------------- #
CODE_FS = 19
PLAIN = "#D6DEEB"       # default code text
COMMENT = "#5F6B7E"     # comments (grey-blue)
KW = "#C792EA"          # keywords (violet)
TYP = "#38BDF8"         # types (cyan)
FUNC = "#82AAFF"        # function / macro names
STR = "#C3E88D"         # strings

RS_T2C = {
    "fn": KW, "let": KW, "mut": KW, "while": KW, "for": KW, "in": KW,
    "if": KW, "break": KW, "return": KW,
    "String": TYP, "u64": TYP, "Vec": TYP,
    "true": GOLD, "false": GOLD,
    "println!": FUNC, "vec!": FUNC, "count_primes": FUNC, "push": FUNC,
    "from": FUNC,
    '"hello"': STR, '"{t}"': STR, '"{s}"': STR, '"{first}"': STR,
    "&mut": GOLD, "&": SAFE_C,
}

PY_T2C = {
    "def": KW, "return": KW, "for": KW, "in": KW, "while": KW, "if": KW,
    "break": KW, "True": GOLD, "False": GOLD,
    "range": FUNC, "count_primes": FUNC,
}


def _safe_t2c(s, table):
    """Per-line text->colour map, pruned so no key overlaps another."""
    present = {k: v for k, v in table.items() if k in s}
    keys = list(present)
    return {k: v for k, v in present.items()
            if not any(k != o and k in o for o in keys)}


# ---- real rustc output -> coloured terminal rows ---------------------------- #
def _err_color(line):
    s = line.strip()
    if s.startswith("error["):
        return BAD, "BOLD"
    if s.startswith("-->"):
        return MUTED, "NORMAL"
    if s.startswith("help:"):
        return FUNC, "NORMAL"
    if "^" in s:
        return BAD, "NORMAL"
    if s and set(s) <= set("|+ "):
        return SAFE_C, "NORMAL"
    if s[:1].isdigit() and "|" in s:
        return PLAIN, "NORMAL"
    if s.startswith("|") and "-" in s:
        return FUNC, "NORMAL"
    if s == "|":
        return "#4A5366", "NORMAL"
    return PLAIN, "NORMAL"


def _wrap_line(line, width=58):
    """Terminal-style soft wrap; continuations indent 8 spaces."""
    out, cur = [], line.rstrip()
    while len(cur) > width:
        cut = cur.rfind(" ", 20, width)
        if cut < 20:
            cut = width
        out.append(cur[:cut])
        cur = "        " + cur[cut:].lstrip()
    out.append(cur)
    return out


def error_rows(raw, drop=(), width=58):
    """Trim rustc stderr to its essential block, keep the text verbatim."""
    rows = []
    for ln in raw.splitlines():
        s = ln.strip()
        if s.startswith(("warning", "error: aborting", "For more information")):
            break
        if s.startswith("= note"):
            continue
        if any(d in ln for d in drop):
            continue
        color, weight = _err_color(ln)
        for piece in _wrap_line(ln, width):
            rows.append((piece, color, weight))
    while rows and rows[-1][0].strip() == "":
        rows.pop()
    return rows


ERR_MOVE_ROWS = error_rows(ERRORS["move"],
                           drop=("move occurs because", "String::from"))
ERR_BORROW_ROWS = error_rows(ERRORS["borrow"])


# ========================================================================== #
# small reusable pieces
# ========================================================================== #
def txt(text, fs=24, color=INK, weight="NORMAL", font=None, slant=None, **extra):
    """``Text`` with optional kwargs, skipping None so Pango never chokes."""
    kw = {"font_size": fs, "color": color, "weight": weight, **extra}
    if font:
        kw["font"] = font
    if slant:
        kw["slant"] = slant
    return Text(text, **kw)


def mono(text, fs=18, color=INK, weight="NORMAL"):
    return Text(text, font_size=fs, color=color, font=MONO, weight=weight)


def chip(text, color, fs=20, fill=0.14, w=None, h=0.56, tcolor=None, weight="NORMAL", radius=0.12):
    label = txt(text, fs=fs, color=tcolor or INK, weight=weight)
    width = (label.width + 0.5) if w is None else w
    if label.width > width - 0.3:
        label.scale((width - 0.3) / label.width)
    box = RoundedRectangle(width=width, height=h, corner_radius=radius,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=fill)
    label.move_to(box)
    g = VGroup(box, label)
    g.box = box
    g.label = label
    return g


def pill(text, color, fs=22, fill=0.16, weight="BOLD"):
    t = txt(text, fs=fs, color=color, weight=weight)
    box = RoundedRectangle(width=t.width + 0.44, height=t.height + 0.26,
                           corner_radius=0.13, stroke_color=color, stroke_width=2,
                           fill_color=color, fill_opacity=fill)
    box.move_to(t)
    return VGroup(box, t)


def arr(a, b, color=MUTED, sw=4, buff=0.12, tip=0.2):
    """Arrow between two EXPLICIT points (pass .get_right()/.get_left(), never a
    bare Mobject — get_boundary_point on a compound glyph renders diagonally)."""
    return Arrow(a, b, buff=buff, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.35, tip_length=tip)


def wire(a, b, color=MUTED, sw=2.0, op=0.75):
    """A thin connecting line that sits behind the glyphs."""
    ln = Line(a, b, stroke_color=color, stroke_width=sw, stroke_opacity=op)
    ln.set_z_index(-1)
    return ln


def make_tick(color=SAFE_C, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])])
    return v.set_stroke(color=color, width=sw).scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.18, -0.18, 0], [0.18, 0.18, 0])
    b = Line([-0.18, 0.18, 0], [0.18, -0.18, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


# ---- glyphs (all hand-drawn Manim mobjects, no image assets) -------------- #
def rust_gear(color=RUST_C, s=1.0, letter=True):
    """A gear with an R — a nod to Rust's logo, drawn by hand."""
    teeth = VGroup()
    for k in range(8):
        a = k * TAU / 8
        t = RoundedRectangle(width=0.17, height=0.14, corner_radius=0.035,
                             stroke_width=0, fill_color=color, fill_opacity=0.95)
        t.move_to([0.485 * np.cos(a), 0.485 * np.sin(a), 0]).rotate(a)
        teeth.add(t)
    outer = Circle(radius=0.44, stroke_color=color, stroke_width=4,
                   fill_color=color, fill_opacity=0.10)
    inner = Circle(radius=0.295, stroke_color=color, stroke_width=1.8, fill_opacity=0)
    g = VGroup(teeth, outer, inner)
    if letter:
        g.add(txt("R", fs=30, color=color, weight="BOLD").move_to(outer))
    return g.scale(s)


def owner_tag(name, color=RUST_C):
    """A little name tag with a down-pointing tip — 'this variable owns that'."""
    c = chip(name, color, fs=19, h=0.46, fill=0.24, weight="BOLD")
    tip = Polygon([-0.1, 0, 0], [0.1, 0, 0], [0, -0.17, 0],
                  stroke_width=0, fill_color=color, fill_opacity=0.9)
    tip.next_to(c, DOWN, buff=-0.01)
    g = VGroup(c, tip)
    g.chip = c
    return g


def mem_cell(label, color=RUST_C, w=0.62, h=0.62, fs=18, fill=0.12):
    """One heap cell holding a value."""
    box = RoundedRectangle(width=w, height=h, corner_radius=0.08,
                           stroke_color=color, stroke_width=2.4,
                           fill_color=color, fill_opacity=fill)
    lab = mono(label, fs=fs, color=INK)
    if lab.width > w - 0.16:
        lab.scale((w - 0.16) / lab.width)
    lab.move_to(box)
    g = VGroup(box, lab)
    g.box = box
    return g


def heap_region(w=5.4, h=2.9, label="the heap"):
    """A faint region of memory to place cells in."""
    r = RoundedRectangle(width=w, height=h, corner_radius=0.18,
                         stroke_color=FAINT, stroke_width=2.2,
                         fill_color=PANEL, fill_opacity=0.45)
    lab = txt(label, fs=15, color=MUTED)
    lab.move_to(r.get_corner(UL) + np.array([lab.width / 2 + 0.22, -0.3, 0]))
    g = VGroup(r, lab)
    g.box = r
    return g


def stamp(text, color, fs=40):
    """A rotated rubber-stamp verdict."""
    t = txt(text, fs=fs, color=color, weight="BOLD")
    box = RoundedRectangle(width=t.width + 0.5, height=t.height + 0.36, corner_radius=0.14,
                           stroke_color=color, stroke_width=5, fill_opacity=0)
    t.move_to(box)
    return VGroup(box, t).rotate(-0.16)


# ========================================================================== #
class _RustBase(Scene):
    def setup(self):
        self.camera.background_color = BG
        self.hlrect = None

    # ---- timing helpers --------------------------------------------------- #
    def play(self, *anims, **kwargs):
        if not (len(anims) == 1 and isinstance(anims[0], Wait)):
            rt = kwargs.get("run_time")
            if rt is not None:
                kwargs["run_time"] = rt * ANIM_SLOW
        return super().play(*anims, **kwargs)

    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def read(self, k=1.0):
        self.wait(k * READ)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.0))

    def settle(self):
        self.wait(END_HOLD)

    def wipe(self, rt=0.7):
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)
        self.hlrect = None

    # ---- text helpers ----------------------------------------------------- #
    def section_header(self, label, color):
        t = txt(label, fs=33, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=4)
        return VGroup(t, line)

    def say(self, text, color=INK, fs=23, y=-3.42, weight="NORMAL"):
        """A bottom caption, width-clamped so it never runs off-screen."""
        m = txt(text, fs=fs, color=color, weight=weight)
        if m.width > 12.7:
            m.scale_to_fit_width(12.7)
        m.move_to([0, y, 0])
        return m

    def swap_cap(self, old, new_text, **kw):
        """Replace the current bottom caption with a new one; return it."""
        new = self.say(new_text, **kw)
        if old is None:
            self.play(FadeIn(new), run_time=0.5)
        else:
            self.play(ReplacementTransform(old, new), run_time=0.5)
        return new

    def takeaway(self, line1, line2, c2=GOLD):
        """Fade to a clean frame, land a two-line takeaway centred."""
        k1 = Text(line1, font_size=36, color=INK, weight="BOLD")
        k2 = Text(line2, font_size=27, color=c2, weight="BOLD")
        if k1.width > 12.8:
            k1.scale_to_fit_width(12.8)
        if k2.width > 12.8:
            k2.scale_to_fit_width(12.8)
        VGroup(k1, k2).arrange(DOWN, buff=0.36).move_to(ORIGIN)
        self.play(FadeIn(k1, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(k2, shift=UP * 0.1), run_time=0.6)
        self.read(1.4)

    # ---- code panel ------------------------------------------------------- #
    def code_panel(self, spec, table=RS_T2C, title="main.rs", fs=CODE_FS,
                   indent_unit=0.46, line_buff=0.16, target_h=5.6, target_w=7.2):
        """spec: list of (indent, text); "" is a blank line. Returns (panel, lines)."""
        lines = []
        for indent, s in spec:
            if s == "":
                m = Rectangle(width=0.02, height=0.26, fill_opacity=0, stroke_opacity=0)
            elif s.lstrip().startswith(("#", "//")):
                m = txt(s, fs=fs, color=COMMENT, font=MONO, slant=ITALIC)
            else:
                m = Text(s, font=MONO, font_size=fs, color=PLAIN, t2c=_safe_t2c(s, table))
            m._indent = indent
            lines.append(m)
        code = VGroup(*lines).arrange(DOWN, aligned_edge=LEFT, buff=line_buff)
        for m in lines:
            m.shift(RIGHT * indent_unit * m._indent)
        f = min(target_h / code.height, target_w / code.width)
        if f < 1:
            code.scale(f)

        bg = RoundedRectangle(width=code.width + 0.9, height=code.height + 1.15,
                              corner_radius=0.16, stroke_color=FAINT, stroke_width=2,
                              fill_color="#0A0E15", fill_opacity=1.0)
        bg.move_to(code)
        bar = RoundedRectangle(width=bg.width, height=0.5, corner_radius=0.16,
                               stroke_width=0, fill_color="#141C29", fill_opacity=1.0)
        bar.move_to(bg).align_to(bg, UP)
        dots = VGroup(*[Dot(radius=0.045, color=c)
                        for c in ("#FF5F57", "#FEBC2E", "#28C840")]).arrange(RIGHT, buff=0.11)
        dots.move_to([bg.get_left()[0] + 0.42, bar.get_center()[1], 0])
        ttl = txt(title, fs=15, color=MUTED, font=MONO)
        max_ttl_w = bg.width - 1.5
        if ttl.width > max_ttl_w:
            ttl.scale_to_fit_width(max_ttl_w)
        ttl.next_to(dots, RIGHT, buff=0.34).set_y(bar.get_center()[1])
        code.shift(DOWN * 0.2)
        panel = VGroup(bg, bar, dots, ttl, code)
        panel.code = code
        return panel, lines

    def hl_lines(self, panel, lines, idxs, color=ACCENT, opacity=0.16, pad=0.05, xpad=0.34):
        tops = [lines[i].get_top()[1] for i in idxs]
        bots = [lines[i].get_bottom()[1] for i in idxs]
        y_hi, y_lo = max(tops) + pad, min(bots) - pad
        rect = RoundedRectangle(width=panel[0].width - xpad, height=(y_hi - y_lo),
                                corner_radius=0.08, stroke_width=0,
                                fill_color=color, fill_opacity=opacity)
        rect.move_to([panel[0].get_center()[0], (y_hi + y_lo) / 2, 0])
        return rect

    def focus(self, panel, lines, idxs, color=ACCENT, rt=0.4):
        new = self.hl_lines(panel, lines, idxs, color)
        if self.hlrect is None:
            self.hlrect = new
            self.play(FadeIn(new), run_time=rt)
        else:
            self.play(Transform(self.hlrect, new), run_time=rt)
        return self.hlrect

    # ---- terminal panel for REAL rustc output ------------------------------ #
    def term_panel(self, rows, title="$ rustc main.rs", fs=16, line_buff=0.13,
                   target_h=4.3, target_w=7.4):
        """rows: list of (text, color, weight) — text shown verbatim.

        Pango/Manim strip LEADING whitespace (even NBSP) from a Text, which
        would wreck rustc's aligned `|` gutter — so leading spaces become an
        explicit x-shift measured in real Menlo character widths, and only the
        interior spaces are NBSP-protected.
        """
        char_w = Text("0" * 10, font=MONO, font_size=fs).width / 10
        lines = VGroup()
        for text, color, weight in rows:
            if text.strip() == "":
                m = Rectangle(width=0.02, height=0.2,
                              fill_opacity=0, stroke_opacity=0)
                m._lead = 0.0
            else:
                lead = len(text) - len(text.lstrip(" "))
                m = Text(text.lstrip(" ").replace(" ", NBSP), font=MONO,
                         font_size=fs, color=color, weight=weight)
                m._lead = lead * char_w
            lines.add(m)
        lines.arrange(DOWN, aligned_edge=LEFT, buff=line_buff)
        for m in lines:
            m.shift(RIGHT * m._lead)
        f = min(target_h / lines.height, target_w / lines.width)
        if f < 1:
            lines.scale(f)
        bg = RoundedRectangle(width=lines.width + 0.8, height=lines.height + 1.05,
                              corner_radius=0.16, stroke_color=FAINT, stroke_width=2,
                              fill_color="#0A0E15", fill_opacity=1.0)
        bg.move_to(lines)
        bar = RoundedRectangle(width=bg.width, height=0.48, corner_radius=0.16,
                               stroke_width=0, fill_color="#141C29", fill_opacity=1.0)
        bar.move_to(bg).align_to(bg, UP)
        dots = VGroup(*[Dot(radius=0.045, color=c)
                        for c in ("#FF5F57", "#FEBC2E", "#28C840")]).arrange(RIGHT, buff=0.11)
        dots.move_to([bg.get_left()[0] + 0.42, bar.get_center()[1], 0])
        ttl = txt(title, fs=14, color=MUTED, font=MONO)
        if ttl.width > bg.width - 1.5:
            ttl.scale_to_fit_width(bg.width - 1.5)
        ttl.next_to(dots, RIGHT, buff=0.3).set_y(bar.get_center()[1])
        lines.shift(DOWN * 0.18)
        panel = VGroup(bg, bar, dots, ttl, lines)
        panel.rows = lines
        return panel

    # ---- house-style intro / outro cards ---------------------------------- #
    def play_intro(self):
        header = Text("Rust", font_size=74, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1.6, header.get_bottom()[1] - 0.42, 0],
            [header.get_right()[0] + 1.6, header.get_bottom()[1] - 0.42, 0],
        ).set_stroke(width=3, color=GOLD)
        mark = rust_gear(RUST_C, s=0.85, letter=False)
        mark.move_to(line.get_right() + RIGHT * 0.5 + UP * 0.34)
        writer = Text("Created by Ptolémé", font_size=28, color=GC_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.5)
        self.play(FadeIn(mark, shift=DOWN * 0.15),
                  Rotate(mark, angle=TAU / 8), run_time=0.9)
        self.read(0.7)
        sub = Text("The language that is fast and memory safe at the same time.",
                   font_size=29, color=MUTED)
        if sub.width > 12.6:
            sub.scale_to_fit_width(12.6)
        sub.move_to(header)
        self.play(Transform(header, sub), FadeOut(mark), run_time=1.0)
        self.read(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        src = Text("Ownership · Borrowing · The borrow checker · Zero-cost speed",
                   font_size=22, color=MUTED)
        if src.width > 12.0:
            src.scale_to_fit_width(12.0)
        src.next_to(writer, DOWN, buff=0.4)
        self.play(FadeIn(src), run_time=0.8)
        self.read(1.3)
        self.play(FadeOut(VGroup(header, writer, line, src)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        writer = Text("Created by Ptolémé", font_size=28, color=GC_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = Text("Ownership makes it safe. Zero overhead makes it fast.",
                     font_size=26, color=ACCENT)
        recap.next_to(writer, DOWN, buff=0.5)
        self.play(Write(header), Create(line), run_time=1.5)
        self.read(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap), run_time=0.8)
        self.read(1.6)
        self.play(FadeOut(VGroup(header, line, writer, recap)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 — What is Rust? (the direct answer)
    # ====================================================================== #
    def scene_definition(self):
        header = self.section_header("What is Rust?", RUST_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        gear = rust_gear(RUST_C, s=1.1)
        name = txt("Rust", fs=46, color=INK, weight="BOLD")
        lockup = VGroup(gear, name).arrange(RIGHT, buff=0.3).move_to([0.8, 2.0, 0])
        self.play(FadeIn(gear, scale=0.6), FadeIn(name, shift=LEFT * 0.1), run_time=0.7)
        cap = self.say("Rust is a programming language for the lowest,"
                       " most performance-critical layers of software.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.1)

        facts = [
            "A compiled systems programming language.",
            "Created at Mozilla. Version 1.0 shipped in 2015.",
            "No garbage collector, no virtual machine, almost no runtime.",
            "Built for what C and C++ build: kernels, browsers, games, servers.",
        ]
        rows = VGroup()
        for f in facts:
            d = Dot(radius=0.06, color=RUST_C)
            rows.add(VGroup(d, txt(f, fs=23, color=INK)).arrange(RIGHT, buff=0.24))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.44).move_to([0, -0.35, 0])
        for row in rows:
            self.play(FadeIn(row, shift=RIGHT * 0.12), run_time=0.5)
            self.beat(0.8)
        cap = self.swap_cap(cap, "It compiles straight to machine code, like C."
                                 " There is no interpreter and no virtual machine in the way.")
        self.read(1.4)

        self.play(FadeOut(rows), run_time=0.5)
        cap = self.swap_cap(cap, "Its claim to fame is doing two things at once"
                                 " that always used to be a trade-off.")
        p1 = pill("memory safe", SAFE_C, fs=28)
        mid = txt("and", fs=22, color=MUTED)
        p2 = pill("as fast as C", RUST_C, fs=28)
        promise = VGroup(p1, mid, p2).arrange(RIGHT, buff=0.4).move_to([0, -0.3, 0])
        self.play(FadeIn(p1, scale=0.8), run_time=0.5)
        self.beat(0.7)
        self.play(FadeIn(mid), FadeIn(p2, scale=0.8), run_time=0.55)
        self.read(1.0)
        cap = self.swap_cap(cap, "Memory safety, and C-level speed."
                                 " The rest of this film is how Rust gets both.", color=GOLD)
        self.read(1.4)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — The old tradeoff: safety or speed, pick one
    # ====================================================================== #
    def scene_tradeoff(self):
        header = self.section_header("The old tradeoff", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        origin = np.array([-5.3, -2.3, 0])
        xax = arr(origin, np.array([6.0, -2.3, 0]), color=MUTED, sw=3, buff=0)
        yax = arr(origin, np.array([-5.3, 2.45, 0]), color=MUTED, sw=3, buff=0)
        xlab = txt("speed", fs=18, color=MUTED).move_to([5.45, -2.68, 0])
        ylab = txt("memory safety", fs=17, color=MUTED).move_to([-3.85, 2.5, 0])
        self.play(GrowArrow(xax), GrowArrow(yax), FadeIn(xlab), FadeIn(ylab),
                  run_time=0.8)
        cap = self.say("For decades, choosing a language meant choosing a side of this chart.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.0)

        managed = VGroup(
            chip("Python", GC_C, fs=20).move_to([-3.7, 1.35, 0]),
            chip("Java", GC_C, fs=20).move_to([-2.35, 1.9, 0]),
            chip("Go", GC_C, fs=20).move_to([-1.35, 1.05, 0]),
        )
        gc_note = txt("kept safe by a garbage collector", fs=17, color=GC_C)
        gc_note.move_to([-2.6, 0.35, 0])
        self.play(LaggedStart(*[FadeIn(c, scale=0.8) for c in managed],
                              lag_ratio=0.15, run_time=0.7))
        self.play(FadeIn(gc_note), run_time=0.4)
        cap = self.swap_cap(cap, "A garbage collector cleans up behind the program to"
                                 " keep it safe, and the price is speed.", color=GC_C)
        self.read(1.5)

        cpp = chip("C / C++", CPP_C, fs=20).move_to([3.8, -1.45, 0])
        cpp_note = txt("memory managed by hand", fs=17, color=CPP_C).move_to([3.8, -2.0, 0])
        self.play(FadeIn(cpp, scale=0.8), FadeIn(cpp_note), run_time=0.5)
        cap = self.swap_cap(cap, "C and C++ run at full speed, but memory is managed"
                                 " by hand, and mistakes slip through.", color=CPP_C)
        self.read(1.3)

        stat = VGroup(
            pill("~70%", BAD, fs=24),
            txt("of severe security bugs are memory bugs", fs=17, color=BAD),
        ).arrange(RIGHT, buff=0.2).move_to([2.6, -0.5, 0])
        self.play(FadeIn(stat, shift=UP * 0.1), run_time=0.5)
        cap = self.swap_cap(cap, "Microsoft and the Chrome team both report it: about 70"
                                 " percent of severe security bugs are memory bugs.",
                            color=BAD)
        self.read(1.6)

        ring = DashedVMobject(Circle(radius=0.62, stroke_color=MUTED, stroke_width=2.6,
                                     fill_opacity=0), num_dashes=26)
        ring.move_to([4.35, 1.75, 0])
        qm = txt("?", fs=34, color=MUTED).move_to(ring)
        self.play(Create(ring), FadeIn(qm), run_time=0.6)
        cap = self.swap_cap(cap, "So the top right corner stayed empty. Fast and safe"
                                 " at the same time seemed impossible.")
        self.read(1.3)

        rust_lock = VGroup(rust_gear(RUST_C, s=0.6), txt("Rust", fs=24, color=INK, weight="BOLD"))
        rust_lock.arrange(RIGHT, buff=0.18).move_to(ring)
        self.play(FadeOut(qm), FadeOut(ring),
                  FadeIn(rust_lock, scale=0.6), run_time=0.7)
        self.play(Flash(rust_lock, color=RUST_C, flash_radius=1.1), run_time=0.5)
        cap = self.swap_cap(cap, "Rust was designed for exactly that corner.", color=RUST_C)
        self.read(1.1)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.takeaway("Rust's bet: prove memory safety at compile time.",
                      "Then run at full speed, with no garbage collector.", c2=RUST_C)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Ownership: one owner, freed at scope end, moves (real E0382)
    # ====================================================================== #
    def scene_ownership(self):
        header = self.section_header("Ownership", RUST_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        spec = [
            (0, "fn main() {"),
            (1, 'let s = String::from("hello");'),
            (1, "let t = s;"),
            (1, 'println!("{t}");'),
            (0, "}"),
        ]
        panel, lines = self.code_panel(spec, title="move_demo.rs",
                                       target_h=3.2, target_w=4.6)
        panel.move_to([-4.05, 0.8, 0])
        self.play(FadeIn(panel, shift=UP * 0.15), run_time=0.7)
        cap = self.say("Ownership is Rust's core idea, and four lines are enough to see it.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.0)

        region = heap_region(w=5.4, h=2.9)
        region.move_to([3.5, 0.85, 0])
        cells = VGroup(*[mem_cell(ch, RUST_C, w=0.56, h=0.56, fs=17)
                         for ch in "hello"]).arrange(RIGHT, buff=0.07)
        cells.move_to([3.5, 0.42, 0])
        tag_s = owner_tag("s", RUST_C)
        tag_s.move_to([3.5, 1.52, 0])
        self.focus(panel, lines, [1], color=RUST_C)
        self.play(FadeIn(region), run_time=0.4)
        self.play(LaggedStart(*[GrowFromCenter(c) for c in cells],
                              lag_ratio=0.1, run_time=0.6))
        self.play(FadeIn(tag_s, shift=DOWN * 0.15), run_time=0.45)
        cap = self.swap_cap(cap, "String::from places hello on the heap. The variable s"
                                 " owns that memory. Every value has exactly one owner.",
                            color=RUST_C)
        self.read(1.6)

        self.focus(panel, lines, [2], color=GOLD)
        tag_t = owner_tag("t", GOLD).move_to(tag_s)
        self.play(ReplacementTransform(tag_s, tag_t), run_time=0.6)
        cap = self.swap_cap(cap, "Assigning s to t moves ownership. Nothing is copied,"
                                 " and s simply stops being valid.", color=GOLD)
        self.read(1.4)

        self.focus(panel, lines, [3], color=SAFE_C)
        tick = make_tick(SAFE_C, sw=6, scale=0.8).next_to(lines[3], RIGHT, buff=0.3)
        self.play(FadeIn(tick), Indicate(cells, color=SAFE_C, scale_factor=1.06),
                  run_time=0.5)
        cap = self.swap_cap(cap, "Using the new owner is fine. This compiles, runs,"
                                 " and prints hello.", color=SAFE_C)
        self.read(1.1)

        self.focus(panel, lines, [4], color=MUTED)
        freed = pill("freed", SAFE_C, fs=18).move_to(cells)
        self.play(FadeOut(tag_t, shift=UP * 0.1), run_time=0.4)
        self.play(ReplacementTransform(cells, freed), run_time=0.6)
        cap = self.swap_cap(cap, "The owner dies at the closing brace, so Rust frees the"
                                 " memory right there. No collector is needed.")
        self.read(1.7)

        # now break the rule: print the dead variable s instead of t
        bad_src = 'println!("{s}");'
        new3 = Text(bad_src, font=MONO, font_size=CODE_FS, color=PLAIN,
                    t2c={"println!": FUNC, '"{s}"': BAD})
        new3.scale(lines[3].width / new3.width)  # same char count -> match width
        new3.move_to(lines[3], aligned_edge=LEFT)
        self.focus(panel, lines, [3], color=BAD)
        self.play(FadeOut(lines[3], shift=UP * 0.12), FadeOut(tick),
                  FadeIn(new3, shift=UP * 0.12), run_time=0.6)
        cap = self.swap_cap(cap, "Now break the rule: print s, the dead variable,"
                                 " after the move.", color=BAD)
        self.read(1.1)

        err = self.term_panel(ERR_MOVE_ROWS, title="$ rustc move_demo.rs",
                              target_w=6.5, target_h=4.1)
        err.move_to([3.15, 0.25, 0])
        self.play(FadeOut(region), FadeOut(freed), run_time=0.4)
        self.play(FadeIn(err, shift=UP * 0.2), run_time=0.8)
        cap = self.swap_cap(cap, "The compiler rejects the program. This is rustc's"
                                 " real output, not a mock-up.", color=BAD)
        self.read(1.7)
        helps = [i for i, r in enumerate(ERR_MOVE_ROWS) if r[0].startswith("help")]
        if helps:
            self.play(Indicate(err.rows[helps[0]], color=FUNC, scale_factor=1.05),
                      run_time=0.7)
        cap = self.swap_cap(cap, "It even suggests the fix. The whole conversation happens"
                                 " before the program ever runs.", color=GOLD)
        self.read(1.5)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.hlrect = None
        self.takeaway("One owner per value, freed the moment the owner dies.",
                      "All tracked at compile time. It costs nothing at run time.",
                      c2=RUST_C)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Borrowing: many readers XOR one writer
    # ====================================================================== #
    def scene_borrow(self):
        header = self.section_header("Borrowing", SAFE_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        vbox = RoundedRectangle(width=2.4, height=1.1, corner_radius=0.14,
                                stroke_color=INK, stroke_width=2.6,
                                fill_color=PANEL, fill_opacity=0.65)
        vlab = txt("a value", fs=22, color=INK)
        value = VGroup(vbox, vlab).move_to([0.55, 1.45, 0])
        self.play(GrowFromCenter(value), run_time=0.5)
        cap = self.say("Moving ownership around for every read would be painful."
                       " So Rust lets you borrow instead.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.2)

        rpos = [(-3.0, 2.35), (-3.55, 1.45), (-3.0, 0.55)]
        readers = VGroup(*[chip("&", SAFE_C, fs=24, w=0.72, h=0.6, weight="BOLD")
                           .move_to([x, y, 0]) for x, y in rpos])
        r_arrows = VGroup(*[
            arr(r.get_right(), np.array([-0.75, ty, 0]), color=SAFE_C, sw=3.2)
            for r, ty in zip(readers, (1.78, 1.45, 1.12))
        ])
        rlab = txt("shared borrows, read only", fs=18, color=SAFE_C).move_to([-3.2, -0.4, 0])
        self.play(LaggedStart(*[FadeIn(r, scale=0.7) for r in readers],
                              lag_ratio=0.15, run_time=0.6))
        self.play(*[GrowArrow(a) for a in r_arrows], FadeIn(rlab), run_time=0.6)
        cap = self.swap_cap(cap, "A shared borrow, written with an ampersand, is a read-only"
                                 " loan. Any number may exist at the same time.", color=SAFE_C)
        self.read(1.5)

        wchip = chip("&mut", GOLD, fs=22, h=0.6, weight="BOLD").move_to([4.15, 1.45, 0])
        w_arrow = arr(wchip.get_left(), np.array([1.85, 1.45, 0]), color=GOLD, sw=3.6)
        wlab = txt("exclusive borrow, can write", fs=18, color=GOLD).move_to([3.95, -0.4, 0])
        self.play(FadeIn(wchip, scale=0.7), GrowArrow(w_arrow), FadeIn(wlab),
                  readers.animate.set_opacity(0.2),
                  r_arrows.animate.set_opacity(0.15),
                  rlab.animate.set_opacity(0.3), run_time=0.7)
        cap = self.swap_cap(cap, "A mutable borrow can change the value, so it must be"
                                 " exclusive. While it lives, no other borrow may exist.",
                            color=GOLD)
        self.read(1.5)

        cross = make_cross(BAD, sw=8, scale=1.1).move_to([0.55, 2.6, 0])
        self.play(readers[1].animate.set_opacity(1.0),
                  r_arrows[1].animate.set_opacity(1.0), run_time=0.5)
        self.play(FadeIn(cross, scale=0.7),
                  vbox.animate.set_stroke(BAD, 3.2),
                  Flash(value, color=BAD, flash_radius=1.6), run_time=0.6)
        cap = self.swap_cap(cap, "A reader and a writer alive at once is the root of most"
                                 " memory bugs. Rust forbids the combination outright.",
                            color=BAD)
        self.read(1.5)

        rule = pill("Any number of readers, or exactly one writer. Never both.",
                    GOLD, fs=22)
        rule.move_to([0.1, -1.75, 0])
        self.play(FadeOut(cross), vbox.animate.set_stroke(INK, 2.6),
                  readers[1].animate.set_opacity(0.2),
                  r_arrows[1].animate.set_opacity(0.15), run_time=0.5)
        self.play(FadeIn(rule, shift=UP * 0.15), run_time=0.6)
        self.play(Circumscribe(rule, color=GOLD, buff=0.12), run_time=0.8)
        cap = self.swap_cap(cap, "That single rule is the borrow checker. It runs inside"
                                 " the compiler, on every build.", color=GOLD)
        self.read(1.5)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.takeaway("Borrows are checked at compile time, like ownership.",
                      "Break the rule and the program never builds.", c2=SAFE_C)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — The bug it kills: use-after-free via Vec::push (real E0502)
    # ====================================================================== #
    def scene_dangling(self):
        header = self.section_header("The bug it kills", BAD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        spec = [
            (0, "let mut v = vec![1, 2, 3];"),
            (0, "let first = &v[0];"),
            (0, "v.push(4);"),
            (0, 'println!("{first}");'),
        ]
        panel, lines = self.code_panel(spec, title="borrow_demo.rs",
                                       target_h=3.0, target_w=4.8)
        panel.move_to([-4.55, 1.15, 0])
        self.play(FadeIn(panel, shift=UP * 0.15), run_time=0.7)

        old_cells = VGroup(*[mem_cell(str(i), RUST_C, fs=17) for i in (1, 2, 3)])
        old_cells.arrange(RIGHT, buff=0.08).move_to([2.1, 2.2, 0])
        captag = txt("capacity 3", fs=14, color=MUTED).next_to(old_cells, RIGHT, buff=0.3)
        tag_v = owner_tag("v", RUST_C)
        tag_v.move_to([old_cells[0].get_center()[0], 2.2 + 0.74, 0])
        self.focus(panel, lines, [0], color=RUST_C)
        self.play(LaggedStart(*[GrowFromCenter(c) for c in old_cells],
                              lag_ratio=0.12, run_time=0.55),
                  FadeIn(captag), FadeIn(tag_v))
        cap = self.say("Here is the bug that rule kills. A vector owns a buffer on the"
                       " heap, with room for exactly three numbers.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.4)

        self.focus(panel, lines, [1], color=SAFE_C)
        fchip = chip("first", SAFE_C, fs=18, h=0.5).move_to([-1.3, 0.75, 0])
        farr = arr(fchip.get_top(), old_cells[0].get_bottom() + DOWN * 0.02,
                   color=SAFE_C, sw=3.4)
        self.play(FadeIn(fchip, scale=0.8), GrowArrow(farr), run_time=0.6)
        cap = self.swap_cap(cap, "first borrows a pointer straight into that buffer.",
                            color=SAFE_C)
        self.read(1.1)

        self.focus(panel, lines, [2], color=GOLD)
        new_cells = VGroup(*[mem_cell(str(i), RUST_C, fs=17) for i in (1, 2, 3, 4)])
        new_cells.arrange(RIGHT, buff=0.08)
        new_cells.move_to([old_cells[0].get_left()[0] + new_cells.width / 2, 0.55, 0])
        captag2 = txt("capacity 6", fs=14, color=MUTED).next_to(new_cells, RIGHT, buff=0.3)
        freedlab = txt("freed", fs=15, color=BAD, weight="BOLD").move_to(captag)
        tag_v2 = owner_tag("v", RUST_C)
        tag_v2.move_to([new_cells[0].get_center()[0], 0.55 + 0.72, 0])
        self.play(*[TransformFromCopy(old_cells[i], new_cells[i]) for i in range(3)],
                  FadeIn(new_cells[3], shift=DOWN * 0.1), FadeIn(captag2),
                  ReplacementTransform(tag_v, tag_v2), run_time=0.9)
        self.play(old_cells.animate.set_opacity(0.18),
                  ReplacementTransform(captag, freedlab), run_time=0.6)
        dang = pill("dangling", BAD, fs=16).move_to([-1.3, 2.2, 0])
        self.play(farr.animate.set_color(BAD), fchip.box.animate.set_stroke(BAD, 2.6),
                  FadeIn(dang, shift=UP * 0.1), run_time=0.6)
        cap = self.swap_cap(cap, "push needs room for a fourth value, so the buffer moves"
                                 " and the old one is freed. first still points there.",
                            color=BAD)
        self.read(1.7)

        self.focus(panel, lines, [3], color=BAD)
        cap = self.swap_cap(cap, "In C or C++ this compiles fine, and reads freed memory"
                                 " at run time. It is called a use-after-free.", color=BAD)
        self.read(1.5)

        verdict = stamp("DOES NOT COMPILE", BAD, fs=27).move_to([2.3, 1.45, 0])
        cap = self.swap_cap(cap, "Not in Rust. The borrow checker rejects the program"
                                 " at compile time.", color=SAFE_C)
        self.play(FadeIn(verdict, scale=1.4), run_time=0.5)
        self.read(1.2)
        heap_bits = Group(old_cells, new_cells, captag2, freedlab, tag_v2,
                          fchip, farr, dang, verdict)
        self.play(FadeOut(heap_bits), run_time=0.5)

        err = self.term_panel(ERR_BORROW_ROWS, title="$ rustc borrow_demo.rs",
                              target_w=6.8, target_h=4.0)
        err.move_to([2.55, 0.5, 0])
        self.play(FadeIn(err, shift=UP * 0.2), run_time=0.8)
        cap = self.swap_cap(cap, "It sees the write while first is still borrowing."
                                 " This is the actual compiler output.", color=SAFE_C)
        self.read(1.7)
        self.play(Indicate(err.rows[0], color=BAD, scale_factor=1.04), run_time=0.7)
        cap = self.swap_cap(cap, "The program that would crash never gets to exist.",
                            color=SAFE_C)
        self.read(1.2)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.hlrect = None
        self.takeaway("Use-after-free, double free, data races:",
                      "whole bug classes are rejected before the program runs.",
                      c2=SAFE_C)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 6 — Why Rust is fast: no GC, compile-time checks, zero-cost
    # ====================================================================== #
    def scene_speed(self):
        header = self.section_header("Why Rust is fast", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        cap = self.say("Now the performance half of the promise. The first reason"
                       " Rust is fast: there is no garbage collector.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.3)

        lab1 = txt("with a garbage collector", fs=19, color=GC_C)
        lab1.move_to([-6.4 + lab1.width / 2, 2.15, 0])
        track1 = RoundedRectangle(width=12.0, height=0.56, corner_radius=0.12,
                                  stroke_color=FAINT, stroke_width=2,
                                  fill_color=PANEL, fill_opacity=0.5).move_to([0, 1.6, 0])
        lab2 = txt("Rust", fs=19, color=RUST_C)
        lab2.move_to([-6.4 + lab2.width / 2, 0.45, 0])
        track2 = track1.copy().move_to([0, -0.1, 0])
        self.play(FadeIn(lab1), FadeIn(track1), FadeIn(lab2), FadeIn(track2),
                  run_time=0.6)

        x0 = track1.get_left()[0]
        W = track1.width
        pattern = [(0.00, 0.20), (0.26, 0.47), (0.535, 0.76), (0.825, 1.00)]
        pauses = [(0.20, 0.26), (0.47, 0.535), (0.76, 0.825)]

        def seg(f0, f1, y, color, h=0.36, op=0.9):
            r = Rectangle(width=W * (f1 - f0), height=h, stroke_width=0,
                          fill_color=color, fill_opacity=op)
            r.move_to([x0 + W * f0, y, 0], aligned_edge=LEFT)
            return r

        cap = self.swap_cap(cap, "A collector must pause the program while it scans memory."
                                 " Those pauses land as latency spikes.", color=GC_C)
        gcp_lab = txt("GC pause", fs=15, color=BAD)
        gcp_lab.move_to([x0 + W * 0.23, 1.02, 0])
        for i, ((w0, w1), p) in enumerate(zip(pattern, pauses + [None])):
            self.play(GrowFromEdge(seg(w0, w1, 1.6, GC_C), LEFT), run_time=0.5)
            if p is not None:
                pb = seg(p[0], p[1], 1.6, BAD, h=0.44, op=0.95)
                if i == 0:
                    self.play(FadeIn(pb), FadeIn(gcp_lab), run_time=0.35)
                else:
                    self.play(FadeIn(pb), run_time=0.3)
                self.beat(0.35)
        self.read(1.2)

        work = sum(f1 - f0 for f0, f1 in pattern)
        rust_fill = seg(0.0, work, -0.1, RUST_C)
        done = VGroup(make_tick(SAFE_C, sw=6, scale=0.7),
                      txt("same work, done sooner", fs=16, color=SAFE_C))
        done.arrange(RIGHT, buff=0.16)
        # below the lane's end, clamped well inside the right edge
        done.move_to([x0 + W * work + 0.1, -0.78, 0], aligned_edge=LEFT)
        cap = self.swap_cap(cap, "Rust freed everything at scope ends, so the same work"
                                 " just runs, start to finish, with nothing to wait for.",
                            color=RUST_C)
        self.play(GrowFromEdge(rust_fill, LEFT), run_time=1.6)
        self.play(FadeIn(done, shift=LEFT * 0.15), run_time=0.5)
        self.read(1.4)
        cap = self.swap_cap(cap, "This is why Discord rewrote a busy Go service in Rust"
                                 " in 2020: to erase exactly those pause spikes.")
        self.read(1.4)

        keep = {id(header), id(cap)}
        fade = [m for m in self.mobjects if id(m) not in keep]
        self.play(*[FadeOut(m) for m in fade], run_time=0.5)

        ch1 = chip("your code + safety proofs", SAFE_C, fs=19).move_to([-4.15, 1.4, 0])
        ch2 = chip("rustc + LLVM", RUST_C, fs=19).move_to([0.25, 1.4, 0])
        ch3 = chip("bare machine code", GOLD, fs=19).move_to([4.4, 1.4, 0])
        a1 = arr(ch1.get_right(), ch2.get_left(), color=MUTED, sw=3.2)
        a2 = arr(ch2.get_right(), ch3.get_left(), color=MUTED, sw=3.2)
        note = txt("no checks left inside", fs=16, color=MUTED).next_to(ch3, DOWN, buff=0.2)
        self.play(FadeIn(ch1, shift=RIGHT * 0.1), run_time=0.4)
        self.play(GrowArrow(a1), FadeIn(ch2), run_time=0.45)
        self.play(GrowArrow(a2), FadeIn(ch3), FadeIn(note), run_time=0.45)
        cap = self.swap_cap(cap, "Second reason: every safety check ran at compile time."
                                 " The binary contains your logic and nothing else.",
                            color=SAFE_C)
        self.read(1.6)

        code = mono("let total: u64 = v.iter().map(|x| x * x).sum();", fs=20, color=PLAIN)
        code.move_to([0, -0.75, 0])
        eq = txt("compiles to the same machine code as the loop you would write by hand",
                 fs=19, color=GOLD).move_to([0, -1.6, 0])
        self.play(FadeIn(code, shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(eq), run_time=0.5)
        cap = self.swap_cap(cap, "Third reason: high-level code is free. Iterators compile"
                                 " down to the loop you would write by hand.", color=GOLD)
        self.read(1.6)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.takeaway("No collector, no runtime, no leftover checks.",
                      "At run time, there is nothing but your program.", c2=GOLD)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 7 — Let's measure it: the real, baked benchmark
    # ====================================================================== #
    def scene_bench(self):
        header = self.section_header("Let's measure it", SAFE_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        cap = self.say("Talk is cheap. A real measurement from this machine:"
                       " count every prime below one million.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.4)

        py_spec = [
            (0, "def count_primes(limit):"),
            (1, "count = 0"),
            (1, "for n in range(2, limit):"),
            (2, "is_prime = True"),
            (2, "d = 2"),
            (2, "while d * d <= n:"),
            (3, "if n % d == 0:"),
            (4, "is_prime = False"),
            (4, "break"),
            (3, "d += 1"),
            (2, "if is_prime:"),
            (3, "count += 1"),
        ]
        rs_spec = [
            (0, "fn count_primes(limit: u64) -> u64 {"),
            (1, "let mut count = 0;"),
            (1, "for n in 2..limit {"),
            (2, "let mut is_prime = true;"),
            (2, "let mut d = 2;"),
            (2, "while d * d <= n {"),
            (3, "if n % d == 0 { is_prime = false; break; }"),
            (3, "d += 1;"),
            (2, "}"),
            (2, "if is_prime { count += 1; }"),
            (1, "}"),
            (1, "count"),
            (0, "}"),
        ]
        py_panel, _ = self.code_panel(py_spec, table=PY_T2C, title="count_primes.py",
                                      target_h=4.3, target_w=5.2)
        rs_panel, _ = self.code_panel(rs_spec, table=RS_T2C, title="count_primes.rs",
                                      target_h=4.3, target_w=5.9)
        py_panel.move_to([-3.85, -0.45, 0])
        rs_panel.move_to([3.3, -0.45, 0])
        rs_panel.align_to(py_panel, UP)
        self.play(FadeIn(py_panel, shift=UP * 0.15), FadeIn(rs_panel, shift=UP * 0.15),
                  run_time=0.8)
        cap = self.swap_cap(cap, "The same algorithm, line for line. One thread each,"
                                 " no libraries, no tricks.")
        self.read(2.0)

        self.play(FadeOut(py_panel), FadeOut(rs_panel), run_time=0.5)

        b = BENCH
        vers = VGroup(
            mono(b["py_ver"], fs=19, color=GC_C),
            txt("vs", fs=18, color=MUTED),
            mono("rustc 1.93  -O", fs=19, color=RUST_C),
        ).arrange(RIGHT, buff=0.4).move_to([0.3, 2.3, 0])
        correct = VGroup(
            make_tick(SAFE_C, sw=6, scale=0.7),
            txt(f"both find exactly {b['count']:,} primes", fs=22, color=SAFE_C),
        ).arrange(RIGHT, buff=0.22).move_to([0.25, 1.5, 0])
        self.play(FadeIn(vers), run_time=0.5)
        self.play(FadeIn(correct, shift=UP * 0.1), run_time=0.5)
        cap = self.swap_cap(cap, "Correctness first: both programs find exactly"
                                 f" {b['count']:,} primes below one million.", color=SAFE_C)
        self.read(1.3)

        bx0 = -4.3
        bw = 8.7
        py_bar = RoundedRectangle(width=bw, height=0.56, corner_radius=0.1,
                                  stroke_color=GC_C, stroke_width=2.2,
                                  fill_color=GC_C, fill_opacity=0.5)
        py_bar.move_to([bx0, 0.55, 0], aligned_edge=LEFT)
        rs_w = max(bw * b["rs_s"] / b["py_s"], 0.14)
        rs_bar = RoundedRectangle(width=rs_w, height=0.56, corner_radius=0.07,
                                  stroke_color=RUST_C, stroke_width=2.2,
                                  fill_color=RUST_C, fill_opacity=0.85)
        rs_bar.move_to([bx0, -0.55, 0], aligned_edge=LEFT)
        py_lab = txt("Python", fs=21, color=GC_C).move_to([-5.35, 0.55, 0])
        rs_lab = txt("Rust", fs=21, color=RUST_C).move_to([-5.35, -0.55, 0])
        py_time = txt(f"{b['py_s']:.2f} s", fs=22, color=GC_C, weight="BOLD")
        py_time.next_to(py_bar, RIGHT, buff=0.22)
        rs_time = txt(f"{b['rs_s'] * 1000:.0f} ms", fs=22, color=RUST_C, weight="BOLD")
        rs_time.next_to(rs_bar, RIGHT, buff=0.22)

        self.play(FadeIn(py_lab), FadeIn(rs_lab), run_time=0.4)
        self.play(GrowFromEdge(py_bar, LEFT), run_time=1.5)
        self.play(FadeIn(py_time), run_time=0.3)
        self.play(GrowFromEdge(rs_bar, LEFT), FadeIn(rs_time), run_time=0.4)
        self.play(Flash(rs_bar, color=RUST_C, flash_radius=0.9), run_time=0.4)
        cap = self.swap_cap(cap, f"Python takes {b['py_s']:.2f} seconds. Rust takes"
                                 f" {b['rs_s'] * 1000:.0f} milliseconds. Measured,"
                                 f" not estimated: a {SPEEDUP}x gap.", color=RUST_C)
        self.read(1.6)

        spd = pill(f"{SPEEDUP}x faster", GOLD, fs=32).move_to([0.3, -1.85, 0])
        sub = txt(f"same algorithm, best of three runs, {b.get('chip', 'this machine')}",
                  fs=16, color=MUTED).move_to([0.3, -2.52, 0])
        self.play(FadeIn(spd, scale=0.7), run_time=0.5)
        self.play(FadeIn(sub), run_time=0.4)
        cap = self.swap_cap(cap, "And the Rust version carries every safety guarantee"
                                 " you just saw. The speed did not cost anything.", color=GOLD)
        self.read(1.6)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.takeaway(f"The same loop, {SPEEDUP}x faster.",
                      "C-class speed, with the safety already proven.", c2=RUST_C)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 8 — Rust in the real world
    # ====================================================================== #
    def scene_world(self):
        header = self.section_header("Rust in the real world", RUST_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        names1 = ["Linux kernel", "Windows", "Android", "Firefox"]
        names2 = ["Cloudflare", "Discord", "AWS"]
        row1 = VGroup(*[chip(n, RUST_C, fs=19, fill=0.10) for n in names1])
        row1.arrange(RIGHT, buff=0.35).move_to([0.3, 1.95, 0])
        row2 = VGroup(*[chip(n, RUST_C, fs=19, fill=0.10) for n in names2])
        row2.arrange(RIGHT, buff=0.35).move_to([0.3, 1.2, 0])
        cap = self.say("This is not a research toy. The most careful codebases"
                       " in the world have let Rust in.")
        self.play(FadeIn(cap), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(c, scale=0.8) for c in [*row1, *row2]],
                              lag_ratio=0.08, run_time=1.0))
        self.read(1.2)

        facts = [
            ("In the Linux kernel since 2022. Drivers are written in Rust today.", RUST_C),
            ("Android: memory bugs fell from 76% to 24% of vulnerabilities"
             " as new code moved to safe languages.", SAFE_C),
            ("Voted the most admired language in Stack Overflow's survey,"
             " nine years in a row.", GOLD),
        ]
        rows = VGroup()
        for f, c in facts:
            d = Dot(radius=0.06, color=c)
            t = txt(f, fs=21, color=INK)
            if t.width > 11.4:
                t.scale_to_fit_width(11.4)
            rows.add(VGroup(d, t).arrange(RIGHT, buff=0.24))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.52).move_to([0.1, -0.85, 0])

        self.play(FadeIn(rows[0], shift=RIGHT * 0.12), run_time=0.5)
        self.read(1.1)
        self.play(FadeIn(rows[1], shift=RIGHT * 0.12), run_time=0.5)
        cap = self.swap_cap(cap, "The payoff is measurable in production,"
                                 " not just in papers.", color=SAFE_C)
        self.read(1.4)
        self.play(FadeIn(rows[2], shift=RIGHT * 0.12), run_time=0.5)
        cap = self.swap_cap(cap, "And the people who write it keep voting for it.", color=GOLD)
        self.read(1.3)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.takeaway("Fast like C. Safe without a garbage collector.",
                      "The compiler does the work, so your program does not have to.",
                      c2=GOLD)
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_definition()
        self.scene_tradeoff()
        self.scene_ownership()
        self.scene_borrow()
        self.scene_dangling()
        self.scene_speed()
        self.scene_bench()
        self.scene_world()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_RustBase):
    def construct(self):
        self.play_intro()


class Definition(_RustBase):
    def construct(self):
        self.scene_definition()


class Tradeoff(_RustBase):
    def construct(self):
        self.scene_tradeoff()


class Ownership(_RustBase):
    def construct(self):
        self.scene_ownership()


class Borrow(_RustBase):
    def construct(self):
        self.scene_borrow()


class Dangling(_RustBase):
    def construct(self):
        self.scene_dangling()


class Speed(_RustBase):
    def construct(self):
        self.scene_speed()


class Bench(_RustBase):
    def construct(self):
        self.scene_bench()


class World(_RustBase):
    def construct(self):
        self.scene_world()


class Outro(_RustBase):
    def construct(self):
        self.play_outro()


class WhatIsRust(_RustBase):
    """The whole short film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    WhatIsRust().render()

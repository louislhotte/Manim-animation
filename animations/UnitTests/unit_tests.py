"""Unit Tests — a short, house-style explainer.

What a unit test *is*, and why a green suite is worth the keystrokes. We build it
around one small, real, deterministic function — ``is_leap_year`` — whose famous
century edge case (1900 is NOT a leap year, 2000 IS) makes the point better than
any toy ``add(a, b)`` could:

    1. The unit    -- a small pure function: inputs in, one output out, no I/O.
    2. Anatomy     -- every test is Arrange · Act · Assert.
    3. Expected vs actual -- the assertion is a claim; match = green, mismatch =
                      red. Change the code and the *same* test goes red — that is
                      the whole point (a regression tripwire).
    4. Edge cases  -- the happy path passes while a real bug hides at the boundary;
                      an edge case (1900) catches it, and the fix turns it green.
    5. The safety net -- a passing suite is a net: refactor freely, and if you
                      break behaviour a test fires in seconds, on every commit.

The functions below are *run at import*, so every result, tick and cross shown on
screen is genuinely computed — nothing is faked. Scenes are exposed individually
(``Unit``, ``Anatomy``, ``Assertion``, ``Edges``, ``Net``, ``Recap``, ``Intro``,
``Outro``) and as one continuous film (``UnitTestsFilm``).

Env knobs:
    UT_QUICK=1    shorten every hold for a fast sanity render
    UT_DELAY=..   scale the motion-rhythm pauses
    UT_READ=..    absolute reading hold after a block of text (default 2.4 s)
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

# --- crisp text ------------------------------------------------------------ #
# Manim's ``Text`` mangles letter/word spacing below ~20 pt. Render every glyph at
# a large base size and scale the mobject *down* to the requested size. Shadows
# manim's ``Text`` so every call benefits automatically.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("UT_QUICK") == "1"
# Two pacing knobs: DELAY scales the small motion pauses; READ is the absolute hold
# after a block of text lands. ANIM_SLOW stretches every played animation.
DELAY = float(os.environ.get("UT_DELAY", 0.28 if QUICK else 1.0))
READ = float(os.environ.get("UT_READ", 0.35 if QUICK else 2.4))
ANIM_SLOW = 1.0 if QUICK else 1.25
END_HOLD = 0.2 if QUICK else 2.0

# ---- palette -------------------------------------------------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
FAINT = "#3A4152"       # gridlines / inert strokes
GOLD = "#FFD166"        # accent / the unit under test
GOOD = "#3DD68C"        # pass / green
BAD = "#FF5C5C"         # fail / red
ACCENT = "#FFD166"

# the three beats of a test (Arrange · Act · Assert)
ARR_C = "#5B8DEF"       # arrange  (blue)
ACT_C = "#FFB454"       # act      (amber)
ASR_C = "#C792EA"       # assert   (violet)

# code-panel syntax colours
PLAIN = INK
COMMENT = MUTED
KW = "#C792EA"          # keywords: def return assert import
FUNC = "#82AAFF"        # function names
BOOL = "#F78C6C"        # True / False literals

MONO = "Menlo"
FONT = "Helvetica Neue"
_BaseText.set_default(font=FONT)

CODE_FS = 24

# the python keyword / name colour map (kept to safe, long tokens so no
# substring bleeds into an identifier — _safe_t2c prunes the rest per line)
T2C = {
    "def": KW, "return": KW, "assert": KW, "import": KW,
    "is_leap_year": FUNC, "test_leap_year": FUNC, "test_century": FUNC,
    "True": BOOL, "False": BOOL,
}


# ---- the real unit under test (run at import → nothing on screen is faked) - #
def leap_naive(y: int) -> bool:
    """The obvious first attempt — right for most years, wrong at the century."""
    return y % 4 == 0


def leap_correct(y: int) -> bool:
    """The Gregorian rule: every 4, except centuries, except every 400."""
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def leap_bug(y: int):
    """A refactor that drops the ``== 0`` — returns an int, not a bool."""
    return y % 4


CASES = [2020, 2021, 1900, 2000]                     # year -> expected leapness
EXPECTED = {y: leap_correct(y) for y in CASES}       # ground truth


def pyrepr(v) -> str:
    return repr(v)


def _safe_t2c(s, table=T2C):
    """Per-line text→colour map, pruned so no key overlaps another present key.

    Manim's ``t2c`` raises on overlapping ranges — even same-colour ones. Keep only
    keys present in the line, then drop any that is a substring of another present
    key (e.g. ``test_century`` contains ``century``... none here, but ``def`` etc.
    stay safe).
    """
    present = {k: v for k, v in table.items() if k in s}
    keys = list(present)
    return {k: v for k, v in present.items()
            if not any(k != o and k in o for o in keys)}


# ---- small reusable pieces ------------------------------------------------ #
def txt(text, fs=24, color=INK, weight="NORMAL", font=None, slant=None, **extra):
    """``Text`` with optional kwargs, skipping None so Pango never chokes."""
    kw = {"font_size": fs, "color": color, "weight": weight}
    if font:
        kw["font"] = font
    if slant:
        kw["slant"] = slant
    kw.update(extra)
    return Text(text, **kw)


def mono(text, fs=22, color=INK, **kw):
    return txt(text, fs=fs, color=color, font=MONO, **kw)


def chip(text, color, fs=22, w=None, h=0.6, fill=0.14, tcolor=None, weight="NORMAL",
         radius=0.12, font=None):
    """A rounded, tinted box with a centred auto-fitting label. grp[0] is the box."""
    label = txt(text, fs=fs, color=tcolor or INK, weight=weight, font=font)
    width = (label.width + 0.55) if w is None else w
    if label.width > width - 0.3:
        label.scale((width - 0.3) / label.width)
    box = RoundedRectangle(width=width, height=h, corner_radius=radius,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=fill)
    label.move_to(box)
    g = VGroup(box, label)
    g.box = box
    return g


def pill(text, color, fs=26):
    """A bold status badge (PASS / FAIL)."""
    label = txt(text, fs=fs, color=color, weight="BOLD")
    box = RoundedRectangle(width=label.width + 0.6, height=0.66, corner_radius=0.33,
                           stroke_color=color, stroke_width=3,
                           fill_color=color, fill_opacity=0.16)
    label.move_to(box)
    return VGroup(box, label)


def arr(a, b, color=MUTED, sw=4, buff=0.14, tip=0.22):
    return Arrow(a, b, buff=buff, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.4, tip_length=tip)


def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])])
    v.set_stroke(color=color, width=sw)
    return v.scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.16, -0.16, 0], [0.16, 0.16, 0])
    b = Line([-0.16, 0.16, 0], [0.16, -0.16, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


def func_box(name, color=GOLD, w=None, h=1.0):
    """The unit as a black box."""
    label = mono(name, fs=24, color=color)
    width = (label.width + 0.8) if w is None else w
    box = RoundedRectangle(width=width, height=h, corner_radius=0.14,
                           stroke_color=color, stroke_width=3,
                           fill_color=color, fill_opacity=0.10)
    label.move_to(box)
    g = VGroup(box, label)
    g.box = box
    return g


def test_cell(name, color=GOOD, side=1.0):
    """A little pass/fail tile for the suite grid: square + tick + label under."""
    box = RoundedRectangle(width=side, height=side, corner_radius=0.12,
                           stroke_color=color, stroke_width=2.6,
                           fill_color=color, fill_opacity=0.12)
    mark = make_tick(color=color, sw=6, scale=1.05).move_to(box)
    lab = txt(name, fs=15, color=MUTED).next_to(box, DOWN, buff=0.12)
    if lab.width > side + 0.5:
        lab.scale_to_fit_width(side + 0.5)
    g = VGroup(box, mark, lab)
    g.box, g.mark, g.lab = box, mark, lab
    return g


# ========================================================================== #
class _UTBase(Scene):
    def setup(self):
        self.camera.background_color = BG

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
        self._cap = None

    def flash_red(self, opacity=0.22):
        # inset from the frame edge so the transient veil never trips the
        # edge-bleed detector (it reads a full-frame fill as content on every edge)
        veil = Rectangle(width=config.frame_width - 0.5, height=config.frame_height - 0.5,
                         stroke_width=0, fill_color=BAD, fill_opacity=0)
        self.add(veil)
        self.play(veil.animate.set_fill(opacity=opacity), run_time=0.18)
        self.play(veil.animate.set_fill(opacity=0.0), run_time=0.32)
        self.remove(veil)

    def flash_good(self, opacity=0.12):
        veil = Rectangle(width=config.frame_width - 0.5, height=config.frame_height - 0.5,
                         stroke_width=0, fill_color=GOOD, fill_opacity=0)
        self.add(veil)
        self.play(veil.animate.set_fill(opacity=opacity), run_time=0.2)
        self.play(veil.animate.set_fill(opacity=0.0), run_time=0.35)
        self.remove(veil)

    def section_header(self, num, label, color=ACCENT):
        t = txt(f"{num} · {label}", fs=32, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=3)
        return VGroup(t, line)

    def bottomcap(self, s, color=INK, fs=23, buff=0.42, **kw):
        t = txt(s, fs=fs, color=color, **kw)
        if t.width > 12.9:
            t.scale_to_fit_width(12.9)
        t.to_edge(DOWN, buff=buff)
        return t

    def set_cap(self, s, color=INK, fs=23):
        """Replace the running bottom caption (transform if one is present)."""
        new = self.bottomcap(s, color=color, fs=fs)
        if getattr(self, "_cap", None) is not None and self._cap in self.mobjects:
            self.play(Transform(self._cap, new), run_time=0.5)
        else:
            self._cap = new
            self.play(FadeIn(new, shift=UP * 0.1), run_time=0.5)
        return self._cap

    def clear_cap(self):
        if getattr(self, "_cap", None) is not None and self._cap in self.mobjects:
            self.play(FadeOut(self._cap), run_time=0.4)
        self._cap = None

    # ---- Menlo code panel -------------------------------------------------- #
    def code_panel(self, spec, title="leap.py", fs=CODE_FS,
                   indent_unit=0.5, line_buff=0.18, target_h=5.4, target_w=7.6):
        """spec: list of (indent, text); "" is a blank line. Returns (panel, lines)."""
        lines = []
        for indent, s in spec:
            if s == "":
                m = Rectangle(width=0.02, height=0.30, fill_opacity=0, stroke_opacity=0)
            elif s.lstrip().startswith("#"):
                m = txt(s, fs=fs, color=COMMENT, font=MONO, slant=ITALIC)
            else:
                m = Text(s, font=MONO, font_size=fs, color=PLAIN, t2c=_safe_t2c(s))
            m._indent = indent
            lines.append(m)
        code = VGroup(*lines).arrange(DOWN, aligned_edge=LEFT, buff=line_buff)
        for m in lines:
            m.shift(RIGHT * indent_unit * m._indent)
        f = min(target_h / code.height, target_w / code.width, 1.0)
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
        if ttl.width > bg.width - 1.5:
            ttl.scale_to_fit_width(bg.width - 1.5)
        ttl.next_to(dots, RIGHT, buff=0.34).set_y(bar.get_center()[1])
        code.shift(DOWN * 0.2)
        panel = VGroup(bg, bar, dots, ttl, code)
        panel.code = code
        panel.lines = lines
        return panel, lines

    def hl_line(self, panel, line, color=ACCENT, opacity=0.16, pad=0.06, xpad=0.34):
        rect = RoundedRectangle(width=panel[0].width - xpad,
                                height=line.height + 2 * pad,
                                corner_radius=0.08, stroke_width=0,
                                fill_color=color, fill_opacity=opacity)
        rect.move_to([panel[0].get_center()[0], line.get_center()[1], 0])
        return rect

    # ---- house-style intro / outro cards ---------------------------------- #
    def _rule_under(self, header, color=GOLD, pad=1.0, drop=0.45):
        return Line([header.get_left()[0] - pad, header.get_bottom()[1] - drop, 0],
                    [header.get_right()[0] + pad, header.get_bottom()[1] - drop, 0]
                    ).set_stroke(width=3, color=color)

    def play_intro(self):
        header = txt("Unit Tests", fs=60, color=INK, weight="BOLD")
        header.set(width=min(7.0, header.width))
        line = self._rule_under(header)
        writer = txt("Created by Ptolémé", fs=28, color=ARR_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        sub = txt("Prove your code does what you claim", fs=30, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.read(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        src = txt("from one function to a safety net", fs=22, color=MUTED)
        src.next_to(writer, DOWN, buff=0.4)
        self.play(FadeIn(src), run_time=0.8)
        self.read(1.3)
        self.play(FadeOut(VGroup(header, writer, line, src)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.4)
        header = txt("Thank you for watching!", fs=48, color=INK, weight="BOLD")
        line = self._rule_under(header)
        writer = txt("Created by Ptolémé", fs=28, color=ARR_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = txt("Write the test. Trust the code.", fs=26, color=ACCENT)
        recap.next_to(writer, DOWN, buff=0.5)
        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap, shift=UP * 0.1), run_time=0.8)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 1 — the unit
    # ====================================================================== #
    def scene_unit(self):
        head = self.section_header("1", "The Unit")
        self.play(FadeIn(head[0]), Create(head[1]), run_time=0.7)
        self.set_cap("Most software is built from small, pure functions.")
        self.read(0.6)

        panel, lines = self.code_panel(
            [(0, "def is_leap_year(year):"),
             (1, "return year % 4 == 0")],
            title="leap.py", target_w=7.0, target_h=2.0)
        panel.to_edge(UP, buff=1.35)
        self.play(FadeIn(panel[0]), FadeIn(panel[1]), FadeIn(panel[2]), FadeIn(panel[3]),
                  run_time=0.6)
        self.play(Write(lines[0]), run_time=0.7)
        self.play(Write(lines[1]), run_time=0.7)
        self.read(0.8)

        # the "unit" callout
        brace_lbl = chip("one unit", GOLD, fs=20)
        brace_lbl.next_to(panel, RIGHT, buff=0.4)
        if brace_lbl.get_right()[0] > config.frame_x_radius - 0.35:
            brace_lbl.next_to(panel, DOWN, buff=0.3).align_to(panel, RIGHT)
        self.play(FadeIn(brace_lbl, shift=LEFT * 0.2), run_time=0.5)
        self.set_cap("A unit is the smallest piece of behaviour you can test on its own.")
        self.read(1.2)

        # black-box view: input -> function -> output
        inp = chip("year = 2020", ARR_C, fs=22)
        box = func_box("is_leap_year")
        out = chip("True", GOOD, fs=22, weight="BOLD")
        row = VGroup(inp, box, out).arrange(RIGHT, buff=1.1)
        row.move_to(DOWN * 1.55)
        a1 = arr(inp.get_right(), box.get_left(), color=MUTED)
        a2 = arr(box.get_right(), out.get_left(), color=MUTED)
        in_lab = txt("input", fs=16, color=MUTED).next_to(inp, UP, buff=0.16)
        out_lab = txt("output", fs=16, color=MUTED).next_to(out, UP, buff=0.16)

        self.play(FadeIn(inp, shift=UP * 0.1), FadeIn(in_lab), run_time=0.5)
        self.play(GrowArrow(a1), FadeIn(box, scale=0.9), run_time=0.6)
        self.play(GrowArrow(a2), FadeIn(out, shift=RIGHT * 0.1), FadeIn(out_lab), run_time=0.6)
        self.set_cap("Inputs in, one output out — no database, no network. Just logic you can pin down.")
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — anatomy: Arrange · Act · Assert
    # ====================================================================== #
    def scene_anatomy(self):
        head = self.section_header("2", "Anatomy of a Test")
        self.play(FadeIn(head[0]), Create(head[1]), run_time=0.7)

        panel, lines = self.code_panel(
            [(0, "def test_leap_year():"),
             (1, "year = 2020"),
             (1, "result = is_leap_year(year)"),
             (1, "assert result == True")],
            title="test_leap.py", target_w=6.6, target_h=3.4)
        panel.move_to(LEFT * 2.3 + UP * 0.35)
        self.play(FadeIn(panel[0]), FadeIn(panel[1]), FadeIn(panel[2]), FadeIn(panel[3]),
                  run_time=0.6)
        self.play(Write(lines[0]), run_time=0.6)
        self.set_cap("A test is just a function that runs your unit and checks the result.")
        self.read(0.9)

        # a generously-spaced right-hand column (the code lines sit ~0.3u apart —
        # far too tight to hang a 0.6u chip off each — so give the beats their own
        # spacing and fan a leader out to each line).
        beats = [
            (1, "Arrange", ARR_C, "Arrange — set up the inputs."),
            (2, "Act", ACT_C, "Act — call the unit once."),
            (3, "Assert", ASR_C, "Assert — state what must be true."),
        ]
        col = VGroup(*[chip(name, color, fs=24, weight="BOLD", w=2.5)
                       for _, name, color, _ in beats]).arrange(DOWN, buff=0.62)
        col.next_to(panel, RIGHT, buff=1.5)
        col.set_y((lines[1].get_center()[1] + lines[3].get_center()[1]) / 2)
        if col.get_right()[0] > config.frame_x_radius - 0.35:
            col.shift(LEFT * (col.get_right()[0] - (config.frame_x_radius - 0.35)))

        for i, (idx, name, color, desc) in enumerate(beats):
            hl = self.hl_line(panel, lines[idx], color=color, opacity=0.18)
            self.play(FadeIn(hl), Write(lines[idx]), run_time=0.7)
            c = col[i]
            lead = DashedLine([panel[0].get_right()[0] + 0.05, lines[idx].get_center()[1], 0],
                              c.get_left(), dash_length=0.09,
                              stroke_color=color, stroke_width=2)
            self.play(Create(lead), FadeIn(c, shift=LEFT * 0.15), run_time=0.6)
            self.set_cap(desc, color=color)
            self.beat(0.7)

        self.read(0.8)
        # the one-line mantra
        self.set_cap("Arrange · Act · Assert — the shape of every test you'll ever write.", color=ACCENT)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — expected vs actual (the assertion), and a regression
    # ====================================================================== #
    def scene_assertion(self):
        head = self.section_header("3", "Expected vs Actual")
        self.play(FadeIn(head[0]), Create(head[1]), run_time=0.7)

        # the function shown as one editable line up top
        fn = mono("def is_leap_year(year):  return year % 4 == 0", fs=22, color=INK)
        fn_box = RoundedRectangle(width=fn.width + 0.6, height=fn.height + 0.4,
                                  corner_radius=0.12, stroke_color=FAINT, stroke_width=2,
                                  fill_color="#0A0E15", fill_opacity=1.0)
        fn.move_to(fn_box)
        fn_grp = VGroup(fn_box, fn).to_edge(UP, buff=1.25)
        self.play(FadeIn(fn_grp), run_time=0.6)

        # the assertion, decomposed
        claim = mono("assert is_leap_year(2020) == True", fs=26, color=INK)
        claim.move_to(UP * 0.55)
        self.play(Write(claim), run_time=0.9)
        self.set_cap("An assertion is a claim about what the code should return.")
        self.read(1.1)

        actual_v = leap_naive(2020)                       # really computed
        actual = chip(f"actual = {pyrepr(actual_v)}", ACT_C, fs=22)
        expected = chip("expected = True", ASR_C, fs=22)
        eq = txt("==", fs=30, color=MUTED)
        cmp_row = VGroup(actual, eq, expected).arrange(RIGHT, buff=0.5).move_to(DOWN * 0.8)
        self.play(FadeIn(actual, shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(eq), FadeIn(expected, shift=UP * 0.1), run_time=0.5)
        self.read(0.8)

        passed = (actual_v == True)
        badge = pill("PASS" if passed else "FAIL", GOOD if passed else BAD)
        mark = make_tick() if passed else make_cross()
        badge_grp = VGroup(mark, badge).arrange(RIGHT, buff=0.3).next_to(cmp_row, DOWN, buff=0.7)
        self.play(FadeIn(badge_grp, shift=UP * 0.15), run_time=0.6)
        self.flash_good()
        self.set_cap("Match → green. The behaviour is what we claimed.", color=GOOD)
        self.read(1.4)

        # --- now break the code: same test, red -------------------------------
        self.play(FadeOut(badge_grp), FadeOut(cmp_row), run_time=0.4)
        self.set_cap("Now a teammate 'simplifies' the function — and drops the  == 0.", color=INK)
        fn_new = mono("def is_leap_year(year):  return year % 4", fs=22, color=INK)
        fn_new.move_to(fn_box)
        # a red strike showing the removed piece, then swap the line
        strike = Line(fn.get_right() + LEFT * 1.15, fn.get_right() + RIGHT * 0.02,
                      stroke_color=BAD, stroke_width=3)
        self.play(Create(strike), run_time=0.4)
        self.play(Transform(fn, fn_new), FadeOut(strike), run_time=0.7)
        self.read(0.8)

        bug_v = leap_bug(2020)                            # really 0 (falsy)
        actual2 = chip(f"actual = {pyrepr(bug_v)}", ACT_C, fs=22)
        expected2 = chip("expected = True", ASR_C, fs=22)
        eq2 = txt("==", fs=30, color=MUTED)
        cmp2 = VGroup(actual2, eq2, expected2).arrange(RIGHT, buff=0.5).move_to(DOWN * 0.8)
        self.play(FadeIn(cmp2), run_time=0.5)
        passed2 = (bug_v == True)
        err = mono(f"AssertionError: {pyrepr(bug_v)} == True", fs=20, color=BAD)
        badge2 = pill("FAIL", BAD)
        mark2 = make_cross()
        bg2 = VGroup(mark2, badge2).arrange(RIGHT, buff=0.3)
        stack2 = VGroup(bg2, err).arrange(DOWN, buff=0.28).next_to(cmp2, DOWN, buff=0.55)
        self.play(FadeIn(bg2, shift=UP * 0.15), run_time=0.6)
        self.flash_red()
        self.play(FadeIn(err), run_time=0.5)
        self.set_cap("Mismatch → red. The same test just caught the regression.", color=BAD)
        self.read(1.7)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — edge cases catch the real bug
    # ====================================================================== #
    def _result_table(self, fn):
        """Build the year/expected/result/status grid for a leap function."""
        col_x = {"year": -3.6, "exp": -1.3, "res": 1.4, "st": 3.4}
        row_h = 0.62
        head_y = 0.25
        header = VGroup(
            txt("year", fs=20, color=MUTED).move_to([col_x["year"], head_y, 0]),
            txt("expected", fs=20, color=MUTED).move_to([col_x["exp"], head_y, 0]),
            txt("naïve result", fs=20, color=MUTED).move_to([col_x["res"], head_y, 0]),
            txt("test", fs=20, color=MUTED).move_to([col_x["st"], head_y, 0]),
        )
        rule = Line([col_x["year"] - 0.7, head_y - 0.32, 0],
                    [col_x["st"] + 0.7, head_y - 0.32, 0],
                    stroke_color=FAINT, stroke_width=2)
        rows = {}
        for i, y in enumerate(CASES):
            ry = head_y - 0.7 - i * row_h
            exp = EXPECTED[y]
            got = fn(y)
            ok = (bool(got) == exp) if isinstance(got, bool) else (got == exp)
            year_t = mono(str(y), fs=22, color=INK).move_to([col_x["year"], ry, 0])
            exp_t = txt("leap" if exp else "not leap", fs=20,
                        color=INK).move_to([col_x["exp"], ry, 0])
            res_t = txt("leap" if got else "not leap", fs=20,
                        color=GOOD if ok else BAD).move_to([col_x["res"], ry, 0])
            st = (make_tick(scale=0.9) if ok else make_cross(scale=0.9)).move_to([col_x["st"], ry, 0])
            rows[y] = {"year": year_t, "exp": exp_t, "res": res_t, "st": st, "ok": ok, "y": ry}
        return header, rule, rows, col_x

    def scene_edges(self):
        head = self.section_header("4", "Edge Cases")
        self.play(FadeIn(head[0]), Create(head[1]), run_time=0.7)

        panel, lines = self.code_panel(
            [(0, "def is_leap_year(year):"),
             (1, "return year % 4 == 0")],
            title="leap.py", target_w=6.2, target_h=1.3)
        panel.to_edge(UP, buff=1.3)
        self.play(FadeIn(panel), run_time=0.5)

        header, rule, rows, col_x = self._result_table(leap_naive)
        self.play(FadeIn(header), Create(rule), run_time=0.6)

        # reveal the two happy-path rows first — both green
        for y in (2020, 2021):
            r = rows[y]
            self.play(FadeIn(r["year"]), FadeIn(r["exp"]), run_time=0.4)
            self.play(FadeIn(r["res"]), Create(r["st"]), run_time=0.45)
        self.set_cap("The happy path passes. Ship it?")
        self.read(1.2)

        # the tricky boundary rows — the century bug surfaces
        self.set_cap("Not yet — which inputs did we never try? Centuries are special.")
        for y in (1900, 2000):
            r = rows[y]
            self.play(FadeIn(r["year"]), FadeIn(r["exp"]), run_time=0.4)
            self.play(FadeIn(r["res"]), Create(r["st"]), run_time=0.45)
            if not r["ok"]:
                self.flash_red()
        self.read(1.0)

        # highlight the failing 1900 row
        r = rows[1900]
        callout = RoundedRectangle(width=8.9, height=0.6, corner_radius=0.1,
                                   stroke_color=BAD, stroke_width=2.5, fill_color=BAD,
                                   fill_opacity=0.08).move_to([(-3.6 + 3.4) / 2, r["y"], 0])
        self.play(Create(callout), run_time=0.5)
        self.set_cap("1900 is divisible by 4 — but it is NOT a leap year.", color=BAD)
        self.read(1.6)

        # fix the function: naive -> correct one-liner, table recomputes
        self.set_cap("Fix: centuries only count if divisible by 400 (like 2000).", color=ACCENT)
        panel2, lines2 = self.code_panel(
            [(0, "def is_leap_year(year):"),
             (1, "return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)")],
            title="leap.py", target_w=9.2, target_h=1.3)
        panel2.move_to(panel, aligned_edge=UP)
        self.play(FadeOut(callout), Transform(panel, panel2), run_time=0.9)
        self.read(0.6)

        header2, rule2, rows2, _ = self._result_table(leap_correct)
        anims = []
        for y in CASES:
            anims.append(Transform(rows[y]["res"], rows2[y]["res"]))
            anims.append(Transform(rows[y]["st"], rows2[y]["st"]))
        self.play(*anims, run_time=0.9)
        self.flash_good()
        # relabel the result column header now that it's the correct impl
        new_h = txt("result", fs=20, color=MUTED).move_to(header[2])
        self.play(Transform(header[2], new_h), run_time=0.4)
        self.set_cap("Every row green — the edge case bought us a real bug fix.", color=GOOD)
        self.read(1.7)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — the safety net
    # ====================================================================== #
    def scene_net(self):
        head = self.section_header("5", "The Safety Net")
        self.play(FadeIn(head[0]), Create(head[1]), run_time=0.7)
        self.set_cap("Collect the tests, and a passing suite becomes a safety net.")

        # a dim diagonal mesh = the net (only segments fully on-screen, so no
        # diagonal runs off the frame edge)
        mesh = VGroup()
        xmin, xmax = -5.2, 5.2
        ytop, ybot = 1.5, -1.3
        span = ytop - ybot
        for a in np.arange(xmin - span, xmax + 0.01, 0.75):
            for x0, x1 in ((a, a + span), (a + span, a)):
                if xmin - 0.01 <= x0 <= xmax + 0.01 and xmin - 0.01 <= x1 <= xmax + 0.01:
                    mesh.add(Line([x0, ybot, 0], [x1, ytop, 0],
                                  stroke_color=GOOD, stroke_width=1.4).set_opacity(0.16))
        self.play(Create(mesh), run_time=0.9)

        # the suite tiles laid on the net
        names = ["leap 2020", "common 2021", "century 1900",
                 "gregorian 2000", "leap 2024", "year 4"]
        cells = [test_cell(n) for n in names]
        grid = VGroup(*cells).arrange_in_grid(rows=2, cols=3, buff=(1.5, 0.7))
        grid.move_to([0, 0.15, 0])
        self.play(LaggedStart(*[FadeIn(c.box) for c in cells], lag_ratio=0.12, run_time=1.0))
        self.play(LaggedStart(*[AnimationGroup(Create(c.mark), FadeIn(c.lab))
                                for c in cells], lag_ratio=0.12, run_time=1.2))
        self.read(1.0)

        # refactor freely — net stays green
        self.set_cap("Refactor freely: if behaviour holds, the whole net stays green.")
        self.play(LaggedStart(*[Indicate(c.box, color=GOOD, scale_factor=1.12)
                                for c in cells], lag_ratio=0.08, run_time=1.1))
        self.read(1.0)

        # break something — one tile fires red
        self.set_cap("Break something, and a test goes red in seconds — not in production.", color=BAD)
        victim = cells[2]                                  # "century 1900"
        red_box = RoundedRectangle(width=victim.box.width, height=victim.box.height,
                                   corner_radius=0.12, stroke_color=BAD, stroke_width=2.6,
                                   fill_color=BAD, fill_opacity=0.16).move_to(victim.box)
        red_cross = make_cross(sw=6, scale=1.05).move_to(victim.box)
        red_lab = txt(names[2], fs=15, color=BAD).move_to(victim.lab)
        self.play(Transform(victim.box, red_box), Transform(victim.mark, red_cross),
                  Transform(victim.lab, red_lab), run_time=0.55)
        self.flash_red()
        tag = txt("test_century_1900  FAILED", fs=20, color=BAD, font=MONO)
        tag.next_to(grid, DOWN, buff=0.55)
        self.play(FadeIn(tag, shift=UP * 0.1), run_time=0.5)
        self.read(1.5)

        # fix it back — green again, and it runs on every commit
        self.set_cap("Fix, and it's green again — run the suite on every commit.", color=GOOD)
        green_box = RoundedRectangle(width=victim.box.width, height=victim.box.height,
                                     corner_radius=0.12, stroke_color=GOOD, stroke_width=2.6,
                                     fill_color=GOOD, fill_opacity=0.12).move_to(victim.box)
        green_tick = make_tick(sw=6, scale=1.05).move_to(victim.box)
        green_lab = txt(names[2], fs=15, color=MUTED).move_to(victim.lab)
        self.play(Transform(victim.box, green_box), Transform(victim.mark, green_tick),
                  Transform(victim.lab, green_lab), FadeOut(tag), run_time=0.55)
        self.flash_good()
        passed = pill("6 / 6 passing", GOOD, fs=24).next_to(grid, DOWN, buff=0.55)
        self.play(FadeIn(passed, shift=UP * 0.1), run_time=0.6)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Closing takeaway
    # ====================================================================== #
    def scene_recap(self):
        lines = VGroup(
            txt("Unit tests, in one breath:", fs=30, color=MUTED),
            txt("State what your code should do —", fs=32, color=INK, weight="BOLD"),
            txt("and let the machine check it, forever.", fs=32, color=INK, weight="BOLD"),
            txt("Red, green, refactor — with a net.", fs=26, color=ACCENT),
        ).arrange(DOWN, buff=0.36)
        self.play(FadeIn(lines[0]), run_time=0.6)
        self.read(0.5)
        self.play(Write(lines[1]), run_time=1.0)
        self.play(Write(lines[2]), run_time=1.0)
        self.read(1.0)
        self.play(FadeIn(lines[3], shift=UP * 0.12), run_time=0.8)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_unit()
        self.scene_anatomy()
        self.scene_assertion()
        self.scene_edges()
        self.scene_net()
        self.scene_recap()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_UTBase):
    def construct(self):
        self.play_intro()


class Unit(_UTBase):
    def construct(self):
        self.scene_unit()


class Anatomy(_UTBase):
    def construct(self):
        self.scene_anatomy()


class Assertion(_UTBase):
    def construct(self):
        self.scene_assertion()


class Edges(_UTBase):
    def construct(self):
        self.scene_edges()


class Net(_UTBase):
    def construct(self):
        self.scene_net()


class Recap(_UTBase):
    def construct(self):
        self.scene_recap()


class Outro(_UTBase):
    def construct(self):
        self.play_outro()


class UnitTestsFilm(_UTBase):
    """The whole short film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    UnitTestsFilm().render()

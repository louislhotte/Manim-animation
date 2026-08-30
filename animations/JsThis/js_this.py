"""JavaScript's ``this`` — a ~3-minute explainer, house-style.

The single most-confused keyword in JavaScript, built from the ground up around
the one idea that unlocks it: **``this`` is decided by *how* a function is
called (its call-site), not by where the function is written.** Arrow functions
are the deliberate exception — they capture ``this`` lexically.

    1. The puzzle -- one function body, four call-sites, four different values
                     of ``this``. What changed? Only the call-site.
    2. The dot    -- the everyday rule: ``obj.method()`` sets ``this = obj``.
                     Look immediately left of the dot at the call.
    3. The bug    -- rip the method off the object (or hand it to a callback)
                     and the dot is gone: ``this`` falls back to ``undefined``
                     in strict mode -> TypeError. The classic "lost this".
    4. The rules  -- the four bindings, in precedence order:
                     ``new`` > ``call``/``apply``/``bind`` > ``obj.fn()`` > ``fn()``.
    5. The fix    -- ``bind`` nails ``this`` to a value once; arrow functions
                     have no ``this`` of their own and borrow the enclosing one
                     (the ``setInterval`` classic).
    6. Takeaway   -- call-site, not definition — unless it's an arrow.

Everything uses ``Text`` (Pango) rather than ``Tex`` so it renders with no LaTeX
install. Scenes are exposed individually (``Hook``, ``DotRule``, ``Lost``,
``Rules``, ``Fix``, ``Takeaway``, ``Intro``, ``Outro``) and as one continuous
film (``ThisKeyword``).

Env knobs:
    THIS_QUICK=1   shorten every hold for a fast sanity render
    THIS_DELAY=..  override the motion-rhythm multiplier
    THIS_READ=..   absolute reading hold after each block of text (default 2.5 s)
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

# --- crisp text ------------------------------------------------------------ #
# Manim's ``Text`` mangles letter/word spacing below ~20 pt. Fix it once: render
# every glyph at a large base size and scale the mobject *down* to the requested
# size. This shadows manim's ``Text`` so every call benefits automatically.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("THIS_QUICK") == "1"
# Two separate pacing knobs so nothing feels rushed:
#   DELAY  scales the small pauses *between* animation steps (motion rhythm).
#   READ   is the absolute hold after any block of text lands, so there is always
#          time to actually read it.
# ANIM_SLOW stretches every played animation so transitions aren't abrupt.
DELAY = float(os.environ.get("THIS_DELAY", 0.28 if QUICK else 1.0))
READ = float(os.environ.get("THIS_READ", 0.35 if QUICK else 2.5))
ANIM_SLOW = 1.0 if QUICK else 1.25
END_HOLD = 0.2 if QUICK else 2.1  # settle held on a finished scene before it wipes
SCENE_GAP = 0.0 if QUICK else 0.3

# ---- palette -------------------------------------------------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
FAINT = "#3A4152"       # gridlines / inert strokes
GOLD = "#FFD166"        # accent
GOOD = "#3DD68C"        # correct / bound / ok
BAD = "#FF5C5C"         # broken / undefined / danger
ACCENT = "#FFD166"
BYLINE = "#5B8DEF"      # the byline blue
PANEL = "#1B2130"       # code-panel title bar

# JS syntax colours
KW = "#C792EA"          # keywords: function const return class new =>
FN = "#82AAFF"          # function / method names
STR = "#C3E88D"         # strings
NUM = "#F78C6C"         # numbers
RECV = "#7FDBFF"        # the receiver — the thing left of the dot
THISC = "#FFD166"       # this (the star) — gold, pops everywhere
COM = "#6B7A99"         # comments
CYAN = "#4CC9F0"        # a fourth distinct result colour

MONO = "Menlo"
FONT = "Helvetica Neue"
_BaseText.set_default(font=FONT)

_NBSP = chr(160)


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


def _safe_t2c(d):
    """Drop any key that is a substring of another present key (Text.t2c raises
    on overlapping coloured runs, even when the colour is equal)."""
    keys = list(d)
    return {k: v for k, v in d.items() if not any(k != o and k in o for o in keys)}


def t2c_of(d):
    """nbsp-substitute the keys (code lines render internal spaces as nbsp) and
    prune overlaps."""
    return _safe_t2c({k.replace(" ", _NBSP): v for k, v in d.items()})


def code_line(core, fs=20, base=INK, t2c=None):
    """One monospace source line. ``core`` is already stripped of indentation.
    Internal spaces are rendered as nbsp so column math (for token highlights)
    stays exact: ``len(core) == column count == rendered width / char_w``."""
    rendered = core.replace(" ", _NBSP)
    if t2c:
        m = mono(rendered, fs=fs, color=base, t2c=t2c_of(t2c))
    else:
        m = mono(rendered, fs=fs, color=base)
    m.core = core
    return m


def chip(text, color, fs=22, w=None, h=0.62, fill=0.14, tcolor=None, weight="NORMAL",
         radius=0.12, font=None):
    """A rounded, tinted box with a centered auto-fitting label. grp[0] is the box."""
    label = txt(text, fs=fs, color=tcolor or INK, weight=weight, font=font)
    width = (label.width + 0.55) if w is None else w
    if label.width > width - 0.3:
        label.scale((width - 0.3) / label.width)
    box = RoundedRectangle(width=width, height=h, corner_radius=radius,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=fill)
    label.move_to(box)
    grp = VGroup(box, label)
    grp.box = box
    return grp


def harrow(start, end, color=MUTED, sw=4, tip=0.22):
    return Arrow(start, end, buff=0.12, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.4, tip_length=tip)


def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])])
    v.set_stroke(color=color, width=sw)
    return v.scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.18, -0.18, 0], [0.18, 0.18, 0])
    b = Line([-0.18, 0.18, 0], [0.18, -0.18, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


def stamp(text="TypeError", color=BAD):
    """A rubber-stamp badge, rotated for impact."""
    label = txt(text, fs=38, color=color, weight="BOLD")
    box = RoundedRectangle(width=label.width + 0.7, height=label.height + 0.45,
                           corner_radius=0.12, stroke_color=color, stroke_width=6,
                           fill_opacity=0)
    label.move_to(box)
    return VGroup(box, label).rotate(-13 * DEGREES)


def code_panel(lines, title="", fs=20, pad=0.34, min_w=0.0):
    """A Menlo code card with a mac-style title bar.

    ``lines`` = list of ``(raw_text[, t2c_dict[, base_color]])``. Pango excludes
    leading whitespace from a Text's ink bounds, so ``arrange(aligned_edge=LEFT)``
    flushes every line to the same x and the indentation vanishes. Fix: build each
    line from its *stripped* text, then place its left edge explicitly at
    ``base_x + indent * char_w`` (one monospace column per leading space). A blank
    line — otherwise a point-less mobject that corrupts ``arrange`` — is rendered
    as an invisible real-height glyph.
    """
    char_w = mono("0", fs=fs).width
    mobs, indents = [], []
    for entry in lines:
        raw = entry[0]
        t2c = entry[1] if len(entry) > 1 else None
        base = entry[2] if len(entry) > 2 else INK
        core = raw.strip()
        ind = len(raw) - len(raw.lstrip(" "))
        if core:
            m = code_line(core, fs=fs, base=base, t2c=t2c)
        else:
            m = mono(".", fs=fs).set_opacity(0)
            m.core = ""
        mobs.append(m)
        indents.append(ind)

    body = VGroup(*mobs).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    base_x = body.get_left()[0]
    for m, ind in zip(mobs, indents):
        m.align_to(np.array([base_x + ind * char_w, 0.0, 0.0]), LEFT)

    w = max(min_w, body.width + 2 * pad)
    h = body.height + 2 * pad + 0.5
    bg = RoundedRectangle(width=w, height=h, corner_radius=0.12,
                          stroke_color=FAINT, stroke_width=2,
                          fill_color="#0B0E14", fill_opacity=1)
    bar = Rectangle(width=w, height=0.44, stroke_width=0, fill_color=PANEL, fill_opacity=1)
    bar.move_to(bg).align_to(bg, UP)
    dots = VGroup(*[Dot(radius=0.052, color=c) for c in (BAD, GOLD, GOOD)])
    dots.arrange(RIGHT, buff=0.11).move_to(bar.get_left() + RIGHT * 0.34)
    grp = VGroup(bg, bar, dots)
    if title:
        ttl = mono(title, fs=15, color=MUTED).next_to(dots, RIGHT, buff=0.22)
        grp.add(ttl)
    body.next_to(bar, DOWN, buff=0.2).align_to(bg, LEFT).shift(RIGHT * pad)
    grp.add(body)
    grp.body = body
    grp.lines = mobs
    return grp


# ---- token highlights (computed live, so they survive move / scale) ------- #
def _tok_geo(line, token):
    """(x_left, y_center, width, height) of ``token`` inside a rendered code
    line, from the *current* on-screen geometry (monospace => exact columns)."""
    core = line.core
    cw = line.width / len(core)
    off = core.index(token)
    x0 = line.get_left()[0] + off * cw
    return x0, line.get_center()[1], len(token) * cw, line.height


def tok_rect(line, token, color, xpad=0.06, ypad=0.07, fill=0.16):
    x0, yc, w, h = _tok_geo(line, token)
    r = RoundedRectangle(width=w + 2 * xpad, height=h + 2 * ypad, corner_radius=0.07,
                         stroke_color=color, stroke_width=2.6,
                         fill_color=color, fill_opacity=fill)
    r.move_to([x0 + w / 2, yc, 0])
    return r


def tok_point(line, token, dy=0.0):
    x0, yc, w, h = _tok_geo(line, token)
    return np.array([x0 + w / 2, yc + dy, 0])


# ========================================================================== #
class _ThisBase(Scene):
    def setup(self):
        self.camera.background_color = BG
        self._cap = None

    # ---- timing helpers --------------------------------------------------- #
    def play(self, *anims, **kwargs):
        # stretch every real animation so transitions aren't abrupt, but never
        # scale a bare Wait (that is a reading hold, handled by read()/beat()).
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
        if SCENE_GAP > 0:
            self.wait(SCENE_GAP)

    def flash_red(self, opacity=0.22):
        # inset from every edge so the transient veil doesn't trip the edge-bleed
        # detector (it only ever needs to tint the working area, not the border).
        veil = Rectangle(width=config.frame_width - 0.8, height=config.frame_height - 0.8,
                         stroke_width=0, fill_color=BAD, fill_opacity=0)
        self.add(veil)
        self.play(veil.animate.set_fill(opacity=opacity), run_time=0.18)
        self.play(veil.animate.set_fill(opacity=0.0), run_time=0.32)
        self.remove(veil)

    def flash_good(self, opacity=0.10):
        veil = Rectangle(width=config.frame_width - 0.8, height=config.frame_height - 0.8,
                         stroke_width=0, fill_color=GOOD, fill_opacity=0)
        self.add(veil)
        self.play(veil.animate.set_fill(opacity=opacity), run_time=0.2)
        self.play(veil.animate.set_fill(opacity=0.0), run_time=0.35)
        self.remove(veil)

    def section_header(self, num, label, color=ACCENT):
        t = txt(f"{num} · {label}", fs=30, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=3)
        return VGroup(t, line)

    def bottomcap(self, s, color=INK, fs=23, buff=0.42, **kw):
        t = txt(s, fs=fs, color=color, **kw)
        if t.width > 12.9:
            t.scale_to_fit_width(12.9)
        t.to_edge(DOWN, buff=buff)
        return t

    def set_cap(self, s, color=INK, fs=23, **kw):
        """Replace the running bottom caption (transform if one is present)."""
        new = self.bottomcap(s, color=color, fs=fs, **kw)
        if getattr(self, "_cap", None) is not None and self._cap in self.mobjects:
            self.play(Transform(self._cap, new), run_time=0.5)
        else:
            self._cap = new
            self.play(FadeIn(new, shift=UP * 0.1), run_time=0.5)
        return self._cap

    # ---- house-style intro / outro cards ---------------------------------- #
    def _rule_under(self, header, color=GOLD, pad=1.0, drop=0.45):
        return Line([header.get_left()[0] - pad, header.get_bottom()[1] - drop, 0],
                    [header.get_right()[0] + pad, header.get_bottom()[1] - drop, 0]
                    ).set_stroke(width=3, color=color)

    def play_intro(self):
        header = txt("The this Keyword", fs=60, color=INK, weight="BOLD",
                     t2c={"this": THISC})
        header.set(width=min(9.2, header.width))
        line = self._rule_under(header)
        writer = txt("Created by Ptolémé", fs=28, color=BYLINE)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        sub = txt("Its value comes from how you call it — not where you write it",
                  fs=27, color=MUTED)
        sub.set(width=min(11.5, sub.width))
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.read(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        src = txt("JavaScript's most-confused keyword, unmystified", fs=22, color=MUTED)
        src.next_to(writer, DOWN, buff=0.4)
        self.play(FadeIn(src), run_time=0.8)
        self.read(1.3)
        self.play(FadeOut(VGroup(header, writer, line, src)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = txt("Thank you for watching!", fs=48, color=INK, weight="BOLD")
        line = self._rule_under(header)
        writer = txt("Created by Ptolémé", fs=28, color=BYLINE)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = txt("this is the call-site — unless it's an arrow.", fs=26, color=ACCENT,
                    t2c={"this": THISC})
        recap.next_to(writer, DOWN, buff=0.5)
        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap), run_time=0.8)
        self.read(1.5)
        self.play(FadeOut(VGroup(header, line, writer, recap)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 — the puzzle: one function, four values of ``this``
    # ====================================================================== #
    def scene_hook(self):
        hdr = self.section_header("01", "The puzzle")
        self.play(FadeIn(hdr, shift=DOWN * 0.2), run_time=0.6)

        panel = code_panel([
            ("function whoAmI() {", {"function": KW, "whoAmI": FN}),
            ("  return this;", {"return": KW, "this": THISC}),
            ("}",),
        ], title="what is this?", fs=22)
        panel.to_edge(UP, buff=1.05)
        self.play(FadeIn(panel, shift=UP * 0.15), run_time=0.8)
        self.set_cap("One function body. It just hands back this.", color=INK)
        self.read(1.0)

        # four call-sites, four answers
        entries = [
            ("whoAmI()", "undefined", BAD, {"whoAmI": FN}),
            ("obj.whoAmI()", "obj", GOOD, {"whoAmI": FN, "obj": RECV}),
            ("whoAmI.call(cat)", "cat", CYAN, {"whoAmI": FN, "call": FN, "cat": RECV}),
            ("new whoAmI()", "a fresh { }", KW, {"new": KW, "whoAmI": FN}),
        ]
        CALLX, ARR0, ARR1, CHIPX = -5.5, -1.1, 0.25, 0.55
        y0 = 0.35
        rows = []
        for i, (call, res, rc, t2c) in enumerate(entries):
            y = y0 - i * 0.86
            cm = code_line(call, fs=24, t2c=t2c)
            cm.align_to([CALLX, y, 0], LEFT).set_y(y)
            ar = harrow([ARR0, y, 0], [ARR1, y, 0], color=MUTED, sw=3)
            ch = chip(res, rc, fs=22, h=0.58)
            ch.align_to([CHIPX, y, 0], LEFT).set_y(y)
            rows.append((cm, ar, ch, rc))

        for cm, ar, ch, rc in rows:
            self.play(FadeIn(cm, shift=RIGHT * 0.1), run_time=0.4)
            self.play(GrowArrow(ar), FadeIn(ch, shift=RIGHT * 0.1), run_time=0.45)
            self.beat(0.4)
        self.set_cap("Same code — four call-sites, four different values of this.",
                     color=INK, t2c={"this": THISC})
        self.read(1.6)
        self.play(LaggedStart(*[Indicate(ch, color=rc, scale_factor=1.08)
                                for _, _, ch, rc in rows], lag_ratio=0.18), run_time=1.1)
        self.set_cap("So what decides this? Not the code — the call-site.",
                     color=GOLD, t2c={"this": THISC})
        self.read(1.5)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — the dot rule (implicit binding)
    # ====================================================================== #
    def scene_dot(self):
        hdr = self.section_header("02", "The dot rule")
        self.play(FadeIn(hdr, shift=DOWN * 0.2), run_time=0.6)

        panel = code_panel([
            ("const user = {", {"const": KW, "user": RECV}),
            ('  name: "Ada",', {"name": FN, '"Ada"': STR}),
            ("  greet() {", {"greet": FN}),
            ("    return `Hi, I'm ${this.name}`;", {"return": KW, "this": THISC}),
            ("  }",),
            ("};",),
            ("",),
            ("user.greet();", {"user": RECV, "greet": FN}),
        ], title="user.js", fs=20)
        if panel.height > 5.0:
            panel.scale(5.0 / panel.height)
        panel.move_to([-2.1, -0.1, 0])
        self.play(FadeIn(panel, shift=UP * 0.15), run_time=0.9)
        self.set_cap("Call a method through its object…", color=INK)
        self.read(1.0)

        call_line = panel.lines[7]
        ret_line = panel.lines[3]
        ubox = tok_rect(call_line, "user", RECV)
        self.play(Create(ubox), run_time=0.5)
        self.set_cap("…and this is set to whatever sits left of the dot.",
                     color=INK, t2c={"this": THISC})
        self.read(1.1)

        tbox = tok_rect(ret_line, "this", THISC)
        self.play(Create(tbox), run_time=0.5)
        arr = CurvedArrow(ubox.get_top() + UP * 0.02, tbox.get_bottom() + DOWN * 0.02,
                          angle=-TAU / 4, color=THISC, stroke_width=3, tip_length=0.18)
        self.play(Create(arr), run_time=0.7)
        self.beat(0.6)

        # right-hand rule + result
        lbl1 = txt("left of the dot", fs=23, color=RECV, weight="BOLD")
        down = Arrow(UP * 0.22, DOWN * 0.22, buff=0, color=MUTED, stroke_width=4)
        lbl2 = txt("becomes this", fs=23, color=INK, weight="BOLD", t2c={"this": THISC})
        rule = VGroup(lbl1, down, lbl2).arrange(DOWN, buff=0.16).move_to([4.15, 1.15, 0])
        self.play(FadeIn(rule, shift=UP * 0.15), run_time=0.7)

        res = chip('"Hi, I\'m Ada"', GOOD, fs=22)
        res.move_to([4.15, -0.7, 0])
        tick = make_tick(GOOD, scale=1.0).next_to(res, LEFT, buff=0.22)
        self.play(FadeIn(res, shift=UP * 0.1), Create(tick), run_time=0.6)
        self.flash_good()
        self.set_cap("this.name reads Ada — because this is the user object.",
                     color=GOOD, t2c={"this": THISC, "Ada": STR})
        self.read(1.7)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — the lost ``this`` (default binding / the bug)
    # ====================================================================== #
    def scene_lost(self):
        hdr = self.section_header("03", "The lost this")
        self.play(FadeIn(hdr, shift=DOWN * 0.2), run_time=0.6)

        panel = code_panel([
            ("const greet = user.greet;", {"const": KW, "greet": FN, "user": RECV}),
            ("",),
            ("greet();", {"greet": FN}),
        ], title="detached.js", fs=22)
        panel.move_to([-2.4, 1.35, 0])
        self.play(FadeIn(panel, shift=UP * 0.15), run_time=0.8)
        self.set_cap("Pull the method off the object, then call it on its own…", color=INK)
        self.read(1.2)

        # no receiver at the call-site
        call_line = panel.lines[2]
        box = tok_rect(call_line, "greet", BAD)
        no_dot = txt("no dot at the call — nothing to its left", fs=20, color=BAD)
        no_dot.next_to(panel, DOWN, buff=0.32)
        self.play(Create(box), FadeIn(no_dot, shift=UP * 0.1), run_time=0.6)
        self.beat(0.5)

        # this -> undefined
        this_tag = txt("this", fs=30, color=THISC, weight="BOLD")
        eq = txt("=  undefined", fs=30, color=BAD, weight="BOLD")
        tag = VGroup(this_tag, eq).arrange(RIGHT, buff=0.24).move_to([3.7, 1.5, 0])
        self.play(FadeIn(tag, shift=UP * 0.1), run_time=0.6)
        self.set_cap("No dot at the call → this falls back to undefined (strict mode).",
                     color=BAD, t2c={"this": THISC})
        self.read(1.3)
        self.flash_red()

        err = stamp("TypeError").scale(0.9).move_to([3.7, -0.55, 0])
        sub = mono("Cannot read properties of undefined", fs=17, color=BAD)
        sub.next_to(err, DOWN, buff=0.28)
        self.play(FadeIn(err, scale=1.2), run_time=0.6)
        self.play(FadeIn(sub), run_time=0.4)
        self.read(1.3)

        # the callback trap
        trap = code_panel([
            ("setTimeout(user.greet, 1000);",
             {"setTimeout": FN, "user": RECV, "greet": FN, "1000": NUM}),
        ], title="the callback trap", fs=22)
        trap.move_to([-2.4, -1.75, 0])
        self.play(FadeIn(trap, shift=UP * 0.12), run_time=0.7)
        self.set_cap("Hand a method to a callback and it's detached too — same bug.",
                     color=BAD)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — the four rules, in precedence order
    # ====================================================================== #
    def scene_rules(self):
        hdr = self.section_header("04", "Who sets this?")
        self.play(FadeIn(hdr, shift=DOWN * 0.2), run_time=0.6)

        specs = [
            ("new Fn()", "→  a brand-new object", KW, {"new": KW, "Fn": FN}),
            ("fn.call(obj) · fn.bind(obj)", "→  obj  (explicit)", CYAN,
             {"fn": FN, "call": FN, "bind": FN, "obj": RECV}),
            ("obj.fn()", "→  obj  (left of the dot)", GOOD, {"obj": RECV, "fn": FN}),
            ("fn()", "→  undefined  (strict mode)", BAD, {"fn": FN}),
        ]
        W, H = 9.2, 0.82
        rungs = VGroup()
        for pat, res, col, t2c in specs:
            box = RoundedRectangle(width=W, height=H, corner_radius=0.12,
                                   stroke_color=col, stroke_width=2.4,
                                   fill_color=col, fill_opacity=0.08)
            pm = code_line(pat, fs=20, t2c=t2c)
            pm.next_to(box.get_left(), RIGHT, buff=0.38)
            rm = txt(res, fs=22, color=col, weight="BOLD")
            rm.align_to([0.35, 0, 0], LEFT).set_y(0)
            rungs.add(VGroup(box, pm, rm))
        rungs.arrange(DOWN, buff=0.22).move_to([0.35, 0.45, 0])

        # precedence arrow on the far left
        top_y = rungs[0][0].get_top()[1]
        bot_y = rungs[-1][0].get_bottom()[1]
        px = rungs.get_left()[0] - 0.55
        prio = Arrow([px, top_y, 0], [px, bot_y, 0], buff=0.05, color=MUTED, stroke_width=5,
                     max_tip_length_to_length_ratio=0.08)
        plab = txt("first match\nwins", fs=17, color=MUTED, weight="BOLD",
                   line_spacing=0.8).next_to(prio, LEFT, buff=0.2)

        self.play(Create(prio), FadeIn(plab), run_time=0.6)
        for r in rungs:
            self.play(FadeIn(r, shift=RIGHT * 0.12), run_time=0.45)
            self.beat(0.35)
        self.set_cap("this is chosen by the call-site — these four, top-down.",
                     color=INK, t2c={"this": THISC})
        self.read(1.6)

        aside = txt("Arrow functions ignore all four — they take this from where "
                    "they're written.", fs=20, color=KW, t2c={"this": THISC})
        if aside.width > 12.8:
            aside.scale_to_fit_width(12.8)
        aside.to_edge(DOWN, buff=0.42)
        self.play(self._cap.animate.set_opacity(0), run_time=0.2)
        self.remove(self._cap)
        self._cap = None
        self.play(FadeIn(aside, shift=UP * 0.1), run_time=0.7)
        self.play(Indicate(aside, color=GOLD, scale_factor=1.04), run_time=0.9)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — the fix: bind, then arrow functions
    # ====================================================================== #
    def scene_fix(self):
        hdr = self.section_header("05", "Pinning this down")
        self.play(FadeIn(hdr, shift=DOWN * 0.2), run_time=0.6)

        # --- part A: bind -------------------------------------------------- #
        bind_panel = code_panel([
            ("const greet = user.greet.bind(user);",
             {"const": KW, "greet": FN, "user": RECV, "bind": FN}),
            ("",),
            ("greet();", {"greet": FN}),
        ], title="bind.js", fs=22)
        bind_panel.move_to([-1.9, 0.9, 0])
        self.play(FadeIn(bind_panel, shift=UP * 0.12), run_time=0.8)

        bline = bind_panel.lines[0]
        bbox = tok_rect(bline, "bind(user)", GOOD)
        self.play(Create(bbox), run_time=0.5)
        res = chip('✓  "Hi, I\'m Ada"', GOOD, fs=22).move_to([3.9, 0.9, 0])
        self.play(FadeIn(res, shift=RIGHT * 0.1), run_time=0.5)
        self.set_cap("bind() locks this to a value — once, permanently.",
                     color=GOOD, t2c={"this": THISC})
        self.read(1.6)
        self.play(FadeOut(VGroup(bind_panel, bbox, res)), run_time=0.5)

        # --- part B: arrow functions -------------------------------------- #
        arrow_panel = code_panel([
            ("class Timer {", {"class": KW, "Timer": FN}),
            ("  seconds = 0;", {"seconds": RECV, "0": NUM}),
            ("  start() {", {"start": FN}),
            ("    // arrow -> this stays the Timer", None, COM),
            ("    setInterval(() => this.seconds++, 1000);",
             {"setInterval": FN, "=>": KW, "this": THISC, "seconds": RECV, "1000": NUM}),
            ("  }",),
            ("}",),
        ], title="timer.js", fs=19)
        arrow_panel.move_to([-2.4, 0.15, 0])
        self.play(FadeIn(arrow_panel, shift=UP * 0.12), run_time=0.9)
        self.set_cap("Arrow functions have no this of their own…", color=INK,
                     t2c={"this": THISC})
        self.read(1.1)

        arrow_line = arrow_panel.lines[4]
        tbox = tok_rect(arrow_line, "this", THISC)
        self.play(Create(tbox), run_time=0.5)
        note = VGroup(
            txt("this = the Timer", fs=24, color=GOLD, weight="BOLD", t2c={"this": THISC}),
            txt("captured from start()", fs=18, color=MUTED),
        ).arrange(DOWN, buff=0.14)
        note.next_to(arrow_panel, RIGHT, buff=0.55).set_y(tbox.get_center()[1])
        avail = (config.frame_x_radius - 0.35) - note.get_left()[0]  # clamp to right margin
        if note.width > avail:
            note.scale(avail / note.width, about_point=note.get_left())
        arr = harrow(tbox.get_right(), [note.get_left()[0] - 0.15, tbox.get_center()[1], 0],
                     color=GOLD, sw=3)
        self.play(GrowArrow(arr), FadeIn(note, shift=RIGHT * 0.1), run_time=0.7)
        self.flash_good()
        self.set_cap("…so they borrow the enclosing this — exactly what a callback needs.",
                     color=GOOD, t2c={"this": THISC})
        self.read(1.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 6 — takeaway card
    # ====================================================================== #
    def scene_takeaway(self):
        title = txt("this, in one breath", fs=44, color=INK, weight="BOLD",
                    t2c={"this": THISC})
        title.to_edge(UP, buff=1.2)
        rule = Line(title.get_left(), title.get_right()).next_to(title, DOWN, buff=0.16)
        rule.set_stroke(GOLD, 3)
        self.play(Write(title), Create(rule), run_time=1.2)
        self.read(0.6)

        points = [
            ("It's the call-site, not where the code is written.", INK),
            ("Look left of the dot — no dot, no this.", INK),
            ("Arrow functions capture this from their scope.", KW),
        ]
        rows = VGroup()
        for s, col in points:
            dot = Dot(radius=0.07, color=GOLD)
            line = txt(s, fs=26, color=col, t2c={"this": THISC})
            rows.add(VGroup(dot, line).arrange(RIGHT, buff=0.3))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to([0, -0.5, 0])
        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.15), run_time=0.6)
            self.read(0.8)
        self.read(1.2)
        self.settle()
        self.wipe()

    # ---- the whole film --------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_hook()
        self.scene_dot()
        self.scene_lost()
        self.scene_rules()
        self.scene_fix()
        self.scene_takeaway()
        self.play_outro()


# ---- individual scenes (render one at a time) ----------------------------- #
class Intro(_ThisBase):
    def construct(self):
        self.play_intro()


class Hook(_ThisBase):
    def construct(self):
        self.scene_hook()


class DotRule(_ThisBase):
    def construct(self):
        self.scene_dot()


class Lost(_ThisBase):
    def construct(self):
        self.scene_lost()


class Rules(_ThisBase):
    def construct(self):
        self.scene_rules()


class Fix(_ThisBase):
    def construct(self):
        self.scene_fix()


class Takeaway(_ThisBase):
    def construct(self):
        self.scene_takeaway()


class Outro(_ThisBase):
    def construct(self):
        self.play_outro()


# ---- the full film -------------------------------------------------------- #
class ThisKeyword(_ThisBase):
    def construct(self):
        self.play_all()

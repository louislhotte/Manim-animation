"""The Story of Gravity — a short, house-style explainer.

A self-explanatory (no voice-over) film that tells the story in four beats:

    1. Falling  -- why things fall; Aristotle's wrong hunch vs. Galileo's test;
                   every object falls with the *same* acceleration g ≈ 9.8 m/s².
    2. Newton   -- the 1666 apple, the leap ("the same pull reaches the Moon"),
                   and the cannonball thought-experiment: an orbit is just
                   falling while moving sideways fast enough to keep missing.
    3. Law      -- the universal law  F = G·m₁·m₂ / r² : every mass pulls every
                   other; stronger with mass, weaker with the square of distance.
    4. Cosmos   -- one equation, from a falling apple to the planets (and a nod
                   to Einstein's curved spacetime).

Bookended by the channel's intro card and the "Thank you for watching!" outro,
matching animations/HarnessEngineering/harness_engineering.py and the rest of
the series.

Everything uses ``Text`` (Pango), never ``Tex`` — so it renders with no LaTeX
toolchain and stays fast to iterate on. The free-fall motion is physically
honest: objects drop with position ∝ t² (constant acceleration), so the light
and heavy balls really do land together.

Scenes are exposed individually (``Falling``, ``Newton``, ``Law``, ``Cosmos``,
``Intro``, ``Outro``) and as one film (``Gravity``).

Env knobs:
    GRAV_QUICK=1   shorten every hold for a fast sanity render
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

# --- crisp text ------------------------------------------------------------ #
# Manim's ``Text`` quantises glyph positions badly at small font sizes, so body
# text below ~20 pt comes out with uneven letter/word spacing. Work around it
# once, here: always render glyphs at a large, crisp base size and scale the
# mobject *down* to the requested size. This shadows manim's ``Text`` so every
# call in this module benefits automatically.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("GRAV_QUICK") == "1"
# One knob for pacing: every reading "hold" is scaled by this. QUICK collapses
# the holds for a fast iteration render; otherwise it sets a relaxed, readable
# rhythm (~2 s per line) that still keeps the whole film under three minutes.
DELAY = 0.3 if QUICK else 1.6

# ---- palette (shared house style) ---------------------------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / axes
FAINT = "#3A4152"       # gridlines / guides
GOLD = "#FFD166"        # highlight / the force / the equation
APPLE = "#FF5C5C"       # the apple / heavy accents (red)
LEAF = "#3DD68C"        # apple leaf / "correct" green
STEM = "#8A6A44"        # apple stem / tree trunk (brown)
EARTH_C = "#5B8DEF"     # Earth (blue)
LAND_C = "#3DA35D"      # Earth's land
MOON_C = "#C7CBD1"      # the Moon (grey)
SUN_C = "#FFB703"       # the Sun (amber)
FORCE_C = "#FF6FB5"     # the gravitational force (pink)
GOOD = "#3DD68C"        # ✓ green
BAD = "#FF5C5C"         # ✗ red
M1_C = "#5B8DEF"        # mass 1 (blue)
M2_C = "#FF8C42"        # mass 2 (orange)


def lerp(a, b, t):
    return a + (b - a) * t


# ========================================================================== #
# Small reusable pieces
# ========================================================================== #
def mtext(parts, base_fs=32):
    """Assemble an inline 'formula' from ``Text`` pieces — no LaTeX needed.

    Each part is ``(s, role[, color])`` with role in {"b" base, "^" super, "_" sub}.
    Supers/subs attach to the previous base, so ``r`` then ``("2","^")`` reads r².
    """
    grp = VGroup()
    last_base = None
    for p in parts:
        s, role = p[0], p[1]
        col = p[2] if len(p) > 2 else INK
        if role == "b":
            m = Text(s, font_size=base_fs, color=col)
            if len(grp) > 0:
                m.next_to(grp, RIGHT, buff=0.06, aligned_edge=DOWN)
            grp.add(m)
            last_base = m
        else:
            m = Text(s, font_size=int(base_fs * 0.62), color=col)
            anchor = last_base if last_base is not None else grp
            m.next_to(anchor, RIGHT, buff=0.02)
            if role == "^":
                m.align_to(anchor, UP).shift(UP * anchor.height * 0.30)
            else:
                m.align_to(anchor, DOWN).shift(DOWN * anchor.height * 0.12)
            grp.add(m)
    return grp


def apple(r=0.26, color=APPLE):
    """A little red apple: body + soft highlight + stem + leaf."""
    body = Circle(radius=r, color=color, fill_opacity=1, stroke_width=0)
    body2 = Circle(radius=r * 0.82, color=color, fill_opacity=1, stroke_width=0)
    body2.move_to(body.get_center() + RIGHT * r * 0.42)
    shine = Dot(body.get_center() + UL * r * 0.42, radius=r * 0.17, color=INK).set_opacity(0.4)
    stem = Line(body.get_top() + DOWN * 0.03, body.get_top() + UP * 0.15,
                stroke_color=STEM, stroke_width=4)
    leaf = Ellipse(width=0.2, height=0.1, color=LEAF, fill_opacity=1, stroke_width=0)
    leaf.rotate(0.5).next_to(stem.get_top(), RIGHT, buff=-0.02).shift(DOWN * 0.01)
    return VGroup(body, body2, shine, stem, leaf)


def ball(r=0.3, color=MUTED):
    """A shaded sphere-ish ball."""
    b = Circle(radius=r, color=color, fill_opacity=1, stroke_width=0)
    shine = Dot(b.get_center() + UL * r * 0.4, radius=r * 0.22, color=INK).set_opacity(0.35)
    return VGroup(b, shine)


def planet(r, color, land=None, stroke=None):
    """A filled circle with optional land blobs and rim stroke."""
    body = Circle(radius=r, color=color, fill_opacity=1, stroke_width=0)
    grp = VGroup(body)
    if land is not None:
        for (dx, dy, w, h) in land:
            blob = Ellipse(width=w * r, height=h * r, color=land_col(color),
                           fill_opacity=1, stroke_width=0)
            blob.move_to(body.get_center() + np.array([dx * r, dy * r, 0]))
            grp.add(blob)
    if stroke:
        body.set_stroke(stroke, 2)
    shine = Arc(radius=r * 0.82, start_angle=0.5, angle=1.2, stroke_color=INK,
                stroke_width=2).set_opacity(0.25).move_arc_center_to(body.get_center())
    grp.add(shine)
    return grp


def land_col(_c):
    return LAND_C


def force_arrow(start, end, color=FORCE_C, sw=6):
    return Arrow(start, end, buff=0.0, color=color, stroke_width=sw,
                 max_tip_length_to_length_ratio=0.35, tip_length=0.22)


def gravity_formula(base_fs=52):
    """Build  F = G · m₁m₂ / r²  from Text pieces + a fraction bar.

    Returns (group, parts) where parts = dict of the highlightable sub-mobjects.
    """
    F = Text("F", font_size=base_fs, color=FORCE_C, weight="BOLD")
    eq = Text("=", font_size=base_fs, color=INK).next_to(F, RIGHT, buff=0.28)
    G = Text("G", font_size=base_fs, color=GOLD, weight="BOLD").next_to(eq, RIGHT, buff=0.28)

    m1 = mtext([("m", "b", M1_C), ("1", "_", M1_C)], base_fs=int(base_fs * 0.82))
    dot = Text("·", font_size=base_fs, color=INK).next_to(m1, RIGHT, buff=0.12)
    m2 = mtext([("m", "b", M2_C), ("2", "_", M2_C)], base_fs=int(base_fs * 0.82))
    m2.next_to(dot, RIGHT, buff=0.12)
    num = VGroup(m1, dot, m2)

    den = mtext([("r", "b", INK), ("2", "^", INK)], base_fs=int(base_fs * 0.82))

    bar = Line(LEFT, RIGHT, stroke_color=INK, stroke_width=3)
    bar.set_length(max(num.width, den.width) + 0.34)
    bar.next_to(G, RIGHT, buff=0.3)
    num.next_to(bar, UP, buff=0.14)
    den.next_to(bar, DOWN, buff=0.14)

    grp = VGroup(F, eq, G, bar, num, den)
    parts = dict(F=F, G=G, m1=m1, m2=m2, r=den, bar=bar, num=num, den=den)
    return grp, parts


# ========================================================================== #
class _GravBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # ---- timing helpers --------------------------------------------------- #
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.0))

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    def section_header(self, label, color):
        txt = Text(label, font_size=34, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(txt.get_left(), txt.get_right()).next_to(txt, DOWN, buff=0.12)
        line.set_stroke(color=color, width=4)
        return VGroup(txt, line)

    def caption(self, text, color=MUTED, fs=26, y=-3.35):
        m = Text(text, font_size=fs, color=color)
        m.move_to([0, y, 0])
        return m

    def ground(self, y=-3.05, color=FAINT):
        g = Line([-7.0, y, 0], [7.0, y, 0], stroke_color=color, stroke_width=3)
        return g

    def free_fall(self, mob, y_ground, run_time=1.5, extra=ORIGIN):
        """Drop ``mob`` so its bottom rests on ``y_ground`` with position ∝ t²."""
        target = mob.copy()
        dy = y_ground - mob.get_bottom()[1]
        target.shift(np.array([0, dy, 0]) + extra)
        self.play(Transform(mob, target), rate_func=lambda t: t * t, run_time=run_time)

    # ---- house-style intro / outro cards ---------------------------------- #
    def introduction(self, title1, title2):
        header = Text(title1, font_size=54, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        writer = Text("Created by Ptolémé", font_size=28, color=EARTH_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        # a small apple falls onto the title bar — a wink at the story
        a = apple(0.22).move_to([header.get_right()[0] + 0.55, 3.2, 0])
        self.play(Write(header), Create(line), run_time=1.6)
        self.play(a.animate.move_to([header.get_right()[0] + 0.55,
                                     line.get_center()[1] + 0.22, 0]),
                  rate_func=lambda t: t * t, run_time=0.9)
        self.card_wait(0.5)
        sub = Text(title2, font_size=34, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), FadeOut(a), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.card_wait(1.8)
        return VGroup(header, writer, line)

    def play_intro(self):
        group = self.introduction(
            "The Story of Gravity",
            "Why things fall · Newton's insight · The universal law",
        )
        self.play(FadeOut(group), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        writer = Text("Created by Ptolémé", font_size=28, color=EARTH_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.5)
        self.card_wait(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.1)
        self.card_wait(2.0)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.3)
        self.card_wait(0.4)

    # ====================================================================== #
    # Scene 1 — Falling: why things fall
    # ====================================================================== #
    def scene_falling(self):
        title = Text("Why do things fall?", font_size=46, color=INK, weight="BOLD")
        self.play(Write(title), run_time=1.2)
        self.beat(0.7)
        header = self.section_header("Why things fall", GOLD)
        self.play(ReplacementTransform(title, header), run_time=0.7)

        gnd = self.ground()
        self.play(Create(gnd), run_time=0.5)

        # a single apple: let go, and it drops.
        a = apple(0.3).move_to([-4.6, 2.6, 0])
        self.play(FadeIn(a, shift=DOWN * 0.1), run_time=0.5)
        cap = self.caption("Let go of anything, and it drops — always down.")
        self.play(FadeIn(cap), run_time=0.4)
        self.free_fall(a, gnd.get_y(), run_time=1.3)
        self.play(a.animate.shift(UP * 0.12), rate_func=there_and_back, run_time=0.35)
        self.beat(1.2)

        # The old, intuitive-but-wrong idea: heavier falls faster.
        self.play(FadeOut(a), FadeOut(cap), run_time=0.4)
        claim = Text("For 2000 years, the intuition was:", font_size=27, color=MUTED)
        claim.move_to([0, 2.5, 0])
        claim2 = Text("\"heavier objects must fall faster.\"", font_size=30,
                      color=INK, weight="BOLD").next_to(claim, DOWN, buff=0.22)
        who = Text("— Aristotle, ~350 BC", font_size=22, color=MUTED).next_to(claim2, DOWN, buff=0.18)
        self.play(FadeIn(claim), run_time=0.5)
        self.play(FadeIn(claim2, shift=UP * 0.1), FadeIn(who), run_time=0.6)
        self.beat(1.3)

        heavy = ball(0.42, MUTED).move_to([-2.4, 0.3, 0])
        light = ball(0.2, MUTED).move_to([2.4, 0.3, 0])
        hl = Text("heavy", font_size=22, color=MUTED).next_to(heavy, UP, buff=0.18)
        ll = Text("light", font_size=22, color=MUTED).next_to(light, UP, buff=0.18)
        self.play(FadeIn(heavy), FadeIn(light), FadeIn(hl), FadeIn(ll), run_time=0.5)
        # the (wrong) intuition: heavy lands first
        self.play(
            heavy.animate.move_to([-2.4, gnd.get_y() + 0.42, 0]),
            rate_func=lambda t: t * t, run_time=0.9,
        )
        self.play(
            light.animate.move_to([2.4, gnd.get_y() + 0.2, 0]),
            rate_func=lambda t: t * t, run_time=1.5,
        )
        wrong = Cross(VGroup(claim, claim2), stroke_color=BAD, stroke_width=8).scale(1.05)
        self.play(Create(wrong), run_time=0.6)
        verdict = Text("Sounds right… but it's wrong.", font_size=26, color=BAD, weight="BOLD")
        verdict.move_to([0, gnd.get_y() + 0.55, 0])
        self.play(FadeIn(verdict, shift=UP * 0.1), run_time=0.5)
        self.beat(1.4)

        # Galileo's test: same fall for both.
        self.play(
            FadeOut(VGroup(claim, claim2, who, wrong, verdict, hl, ll)),
            FadeOut(heavy), FadeOut(light), run_time=0.5,
        )
        gal = Text("Galileo's test (~1590): drop them together.", font_size=28,
                   color=INK, weight="BOLD").move_to([0, 2.5, 0])
        self.play(FadeIn(gal, shift=DOWN * 0.1), run_time=0.6)
        heavy = ball(0.42, EARTH_C).move_to([-1.6, 2.0, 0])
        light = ball(0.2, GOLD).move_to([1.6, 2.0, 0])
        self.play(FadeIn(heavy), FadeIn(light), run_time=0.4)
        self.beat(0.6)
        # identical acceleration → identical run_time & rate → land together
        self.play(
            heavy.animate.move_to([-1.6, gnd.get_y() + 0.42, 0]),
            light.animate.move_to([1.6, gnd.get_y() + 0.2, 0]),
            rate_func=lambda t: t * t, run_time=1.5,
        )
        tie = Text("They land at the same instant.", font_size=26, color=GOOD, weight="BOLD")
        tie.move_to([0, gnd.get_y() + 0.7, 0])
        self.play(Flash(heavy, color=GOOD, flash_radius=0.7),
                  Flash(light, color=GOOD, flash_radius=0.5),
                  FadeIn(tie, shift=UP * 0.1), run_time=0.8)
        self.beat(1.6)

        # The reveal: same acceleration g, velocity builds every second.
        self.play(FadeOut(VGroup(gal, tie, heavy, light)), run_time=0.4)
        reveal = Text("Ignore the air, and every object falls identically.",
                      font_size=28, color=INK).move_to([0, 2.55, 0])
        self.play(FadeIn(reveal, shift=DOWN * 0.1), run_time=0.6)
        self.beat(1.0)

        # strobe: equal time-steps, position ∝ t², velocity ∝ t (arrows grow)
        x0 = -4.4
        y_top, y_bot = 2.0, gnd.get_y() + 0.25
        strobe = VGroup()
        varrows = VGroup()
        steps = [0.25, 0.5, 0.75, 1.0]
        for i, t in enumerate(steps):
            y = lerp(y_top, y_bot, t * t)
            gh = apple(0.2).move_to([x0 + i * 0.0, y, 0]).set_opacity(0.9)
            strobe.add(gh)
            vlen = 0.35 + t * 1.15
            arr = Arrow([x0 + 0.55, y, 0], [x0 + 0.55, y - vlen, 0], buff=0,
                        color=GOLD, stroke_width=5, tip_length=0.16)
            varrows.add(arr)
        self.play(LaggedStart(*[FadeIn(s) for s in strobe], lag_ratio=0.35, run_time=1.3))
        vcap = Text("equal time steps →", font_size=20, color=MUTED)
        vcap.next_to(strobe, LEFT, buff=0.3).shift(UP * 0.2)
        self.play(FadeIn(vcap), LaggedStart(*[GrowArrow(v) for v in varrows],
                                            lag_ratio=0.3, run_time=1.2))
        vlabel = Text("speed keeps growing", font_size=21, color=GOLD)
        vlabel.next_to(varrows, RIGHT, buff=0.35).shift(DOWN * 0.2)
        self.play(FadeIn(vlabel, shift=LEFT * 0.1), run_time=0.5)
        self.beat(1.0)

        g_eq = Text("Same acceleration for all:  g ≈ 9.8 m/s²", font_size=30,
                    color=GOLD, weight="BOLD").move_to([1.7, 0.4, 0])
        note = Text("a feather and a cannonball, in a vacuum, fall together",
                    font_size=22, color=MUTED).next_to(g_eq, DOWN, buff=0.25)
        self.play(FadeIn(g_eq, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(note), run_time=0.5)
        self.beat(1.8)
        self.wipe()

    # ====================================================================== #
    # Scene 2 — Newton: the apple, the Moon, the cannonball
    # ====================================================================== #
    def scene_newton(self):
        header = self.section_header("Newton's leap · 1666", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)
        gnd = self.ground()

        # a tree with a hanging apple
        trunk = Rectangle(width=0.4, height=1.7, color=STEM, fill_opacity=1, stroke_width=0)
        trunk.move_to([-4.4, gnd.get_y() + 0.85, 0])
        canopy = VGroup(*[
            Circle(radius=r, color=LEAF, fill_opacity=1, stroke_width=0).move_to(
                trunk.get_top() + np.array([dx, dy, 0]))
            for (dx, dy, r) in [(-0.55, 0.35, 0.7), (0.55, 0.35, 0.7),
                                (0.0, 0.75, 0.8), (0.0, 0.2, 0.75)]
        ])
        tree = VGroup(trunk, canopy)
        a = apple(0.22).move_to(canopy.get_center() + np.array([0.35, -0.35, 0]))
        self.play(Create(gnd), FadeIn(tree), run_time=0.7)
        self.play(FadeIn(a, scale=0.6), run_time=0.4)

        # a seated observer (Newton) as a simple silhouette
        newton = VGroup(
            Circle(radius=0.16, color=INK, fill_opacity=1, stroke_width=0),  # head
            RoundedRectangle(width=0.34, height=0.5, corner_radius=0.1,
                             color=MUTED, fill_opacity=1, stroke_width=0),  # body
        )
        newton[0].next_to(newton[1], UP, buff=0.02)
        newton.move_to([-2.7, gnd.get_y() + 0.45, 0])
        bubble = VGroup(
            Ellipse(width=1.5, height=0.9, color=INK, fill_opacity=0.06,
                    stroke_color=MUTED, stroke_width=2),
            Text("?", font_size=34, color=GOLD, weight="BOLD"),
        )
        bubble[1].move_to(bubble[0])
        bubble.next_to(newton, UR, buff=0.05).shift(UP * 0.3)
        self.play(FadeIn(newton), run_time=0.4)

        cap = self.caption("An apple falls. Newton asks a bigger question…")
        self.play(FadeIn(cap), run_time=0.4)
        self.free_fall(a, gnd.get_y() + 0.2, run_time=1.0)
        self.play(FadeIn(bubble, shift=UP * 0.15), run_time=0.6)
        self.beat(1.5)

        # The leap
        self.play(FadeOut(cap), run_time=0.3)
        leap = Text("How far up does this pull reach?", font_size=28, color=INK)
        leap.move_to([1.8, 2.4, 0])
        chain = VGroup(
            Text("the treetop…", font_size=24, color=MUTED),
            Text("the mountain-top…", font_size=24, color=MUTED),
            Text("all the way to the Moon?", font_size=26, color=GOLD, weight="BOLD"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22).next_to(leap, DOWN, aligned_edge=LEFT, buff=0.3)
        self.play(FadeIn(leap, shift=DOWN * 0.1), run_time=0.6)
        for c in chain:
            self.play(FadeIn(c, shift=RIGHT * 0.12), run_time=0.45)
            self.beat(0.6)
        self.beat(1.0)
        self.play(FadeOut(VGroup(tree, a, newton, bubble, leap, chain, gnd)), run_time=0.6)

        # The cosmic view: Earth + Moon, and the insight.
        earth = planet(1.3, EARTH_C,
                       land=[(-0.3, 0.25, 0.9, 0.6), (0.35, -0.2, 0.8, 0.5),
                             (0.0, 0.55, 0.5, 0.35)]).move_to([-3.4, -0.4, 0])
        elab = Text("Earth", font_size=22, color=MUTED).next_to(earth, DOWN, buff=0.2)
        moon = planet(0.34, MOON_C).move_to([3.6, 1.6, 0])
        mlab = Text("Moon", font_size=20, color=MUTED).next_to(moon, UP, buff=0.15)
        orbit = DashedVMobject(
            Circle(radius=np.linalg.norm(moon.get_center() - earth.get_center()),
                   color=FAINT, stroke_width=2).move_to(earth.get_center()),
            num_dashes=60,
        )
        self.play(FadeIn(earth), FadeIn(elab), run_time=0.6)
        self.play(Create(orbit), FadeIn(moon), FadeIn(mlab), run_time=0.9)

        insight = Text("The same force that pulls the apple", font_size=27, color=INK)
        insight2 = Text("also holds the Moon in its orbit.", font_size=27,
                        color=GOLD, weight="BOLD")
        VGroup(insight, insight2).arrange(DOWN, buff=0.18).move_to([0, 2.5, 0])
        pull = force_arrow(moon.get_center() + (earth.get_center() - moon.get_center()) * 0.14,
                           earth.get_center() + (moon.get_center() - earth.get_center()) * 0.55,
                           color=FORCE_C, sw=5)
        self.play(FadeIn(insight, shift=DOWN * 0.1), run_time=0.6)
        self.play(FadeIn(insight2, shift=DOWN * 0.1), GrowArrow(pull), run_time=0.7)
        self.beat(1.6)

        # Why doesn't the Moon fall? It does — it keeps missing.
        q = Text("So why doesn't the Moon just fall down?", font_size=26, color=INK)
        q.move_to([0, 2.55, 0])
        self.play(ReplacementTransform(VGroup(insight, insight2), q),
                  FadeOut(pull), run_time=0.6)
        self.beat(1.2)
        ans = Text("It is falling — it just moves sideways fast", font_size=25, color=MOON_C)
        ans2 = Text("enough to keep missing the Earth.", font_size=25, color=MOON_C)
        VGroup(ans, ans2).arrange(DOWN, buff=0.15).move_to([0, 2.55, 0])
        self.play(ReplacementTransform(q, VGroup(ans, ans2)), FadeOut(mlab), run_time=0.6)
        # let the Moon swing along its orbit a little
        self.play(Rotate(moon, angle=-1.0, about_point=earth.get_center()),
                  run_time=2.2, rate_func=linear)
        self.beat(1.2)
        self.play(FadeOut(VGroup(ans, ans2, orbit)), run_time=0.5)

        # Newton's cannonball thought-experiment
        cball_head = Text("Newton's cannonball", font_size=27, color=INK, weight="BOLD")
        cball_head.move_to([0, 3.2, 0])
        self.play(FadeIn(cball_head, shift=DOWN * 0.1),
                  earth.animate.scale(1.15).move_to([-0.2, -1.4, 0]),
                  FadeOut(moon), FadeOut(elab), run_time=0.8)
        ec = earth.get_center()
        R = earth[0].width / 2  # Earth's radius on screen after scaling
        # a mountain + cannon on top of the Earth
        top = ec + UP * R
        mtn = Polygon(top + LEFT * 0.5, top + RIGHT * 0.5, top + UP * 0.55,
                      color=FAINT, fill_opacity=1, stroke_width=0)
        mouth = top + UP * 0.55
        barrel = Rectangle(width=0.55, height=0.2, color=MUTED, fill_opacity=1, stroke_width=0)
        barrel.move_to(mouth + RIGHT * 0.2)
        self.play(FadeIn(mtn), FadeIn(barrel), run_time=0.4)

        launch = mouth + UP * 0.02
        # sub-orbital shots that fall back to the surface
        shots = [
            (-0.9, 2.2, MUTED, "too slow — it falls back"),
            (-1.4, 3.6, MOON_C, "faster — it flies further"),
        ]
        for ang, reach, col, note in shots:
            # a point on Earth's surface, 'reach' radians around toward the right
            phi = PI / 2 - reach * 0.28
            land = ec + R * np.array([np.cos(phi), np.sin(phi), 0])
            path = ArcBetweenPoints(launch, land, angle=ang)
            traj = DashedVMobject(path.copy().set_stroke(col, 3), num_dashes=34)
            cannon = Dot(launch, radius=0.1, color=INK)
            nt = Text(note, font_size=22, color=col).move_to([2.7, 1.3, 0])
            self.play(Create(traj), FadeIn(nt), run_time=0.5)
            self.play(MoveAlongPath(cannon, path), run_time=1.0, rate_func=linear)
            self.play(FadeOut(cannon), FadeOut(nt), traj.animate.set_opacity(0.35), run_time=0.3)
            self.beat(0.4)

        # the orbit: fast enough → a closed circle
        orbit_r = R + 0.55
        orbit_path = Circle(radius=orbit_r, color=GOLD, stroke_width=3).move_to(ec)
        orbit_dash = DashedVMobject(orbit_path.copy(), num_dashes=64)
        self.play(Create(orbit_dash), run_time=0.8)
        th = ValueTracker(PI / 2)
        cball = always_redraw(lambda: Dot(
            ec + orbit_r * np.array([np.cos(th.get_value()), np.sin(th.get_value()), 0]),
            radius=0.1, color=GOLD).set_stroke(INK, 1.2))
        self.add(cball)
        fast = Text("Fast enough sideways, and it never lands —", font_size=25, color=GOLD)
        fast2 = Text("it orbits. That's what the Moon is doing.", font_size=25,
                     color=GOLD, weight="BOLD")
        VGroup(fast, fast2).arrange(DOWN, buff=0.15).move_to([0, 2.5, 0])
        self.play(ReplacementTransform(cball_head, VGroup(fast, fast2)), run_time=0.6)
        self.play(th.animate.increment_value(TAU), run_time=3.2, rate_func=linear)
        self.beat(1.4)
        cball.clear_updaters()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Law: the universal law of gravitation
    # ====================================================================== #
    def scene_law(self):
        header = self.section_header("The universal law of gravitation", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        lead = Text("Newton's punchline:", font_size=27, color=MUTED).move_to([0, 2.6, 0])
        lead2 = Text("every mass attracts every other mass.", font_size=30,
                     color=INK, weight="BOLD").next_to(lead, DOWN, buff=0.2)
        self.play(FadeIn(lead), run_time=0.5)
        self.play(FadeIn(lead2, shift=UP * 0.1), run_time=0.6)
        self.beat(1.0)

        # two masses pulling on each other
        mA = ball(0.5, M1_C).move_to([-3.0, 0.4, 0])
        mB = ball(0.34, M2_C).move_to([3.0, 0.4, 0])
        lA = mtext([("m", "b", M1_C), ("1", "_", M1_C)], base_fs=28).next_to(mA, DOWN, buff=0.2)
        lB = mtext([("m", "b", M2_C), ("2", "_", M2_C)], base_fs=28).next_to(mB, DOWN, buff=0.2)
        rline = DoubleArrow(mA.get_right() + RIGHT * 0.1, mB.get_left() + LEFT * 0.1,
                            buff=0, color=MUTED, stroke_width=3, tip_length=0.18)
        rlab = mtext([("r", "b", INK)], base_fs=28).next_to(rline, UP, buff=0.12)
        fA = force_arrow(mA.get_center() + RIGHT * 0.62, mA.get_center() + RIGHT * 1.5)
        fB = force_arrow(mB.get_center() + LEFT * 0.46, mB.get_center() + LEFT * 1.34)
        self.play(FadeIn(mA), FadeIn(mB), FadeIn(lA), FadeIn(lB), run_time=0.5)
        self.play(GrowArrow(fA), GrowArrow(fB), run_time=0.7)
        self.play(Create(rline), FadeIn(rlab), run_time=0.6)
        pull_lbl = Text("they pull on each other, equally", font_size=22, color=FORCE_C)
        pull_lbl.move_to([0, -1.0, 0])
        self.play(FadeIn(pull_lbl), run_time=0.5)
        self.beat(1.4)

        # collapse the diagram up and reveal the formula
        diagram = VGroup(mA, mB, lA, lB, rline, rlab, fA, fB, pull_lbl)
        self.play(FadeOut(VGroup(lead, lead2)),
                  diagram.animate.scale(0.6).to_edge(UP, buff=1.5), run_time=0.8)

        formula, parts = gravity_formula(base_fs=54)
        formula.move_to([0, -0.7, 0])
        self.play(Write(formula), run_time=1.6)
        self.play(Circumscribe(formula, color=GOLD, run_time=1.4))
        self.beat(1.4)

        # annotate the two behaviours
        note_mass = mtext([("more mass  →  ", "b", INK), ("stronger pull", "b", M2_C)], base_fs=26)
        note_mass.next_to(formula, DOWN, buff=0.55).shift(LEFT * 2.6)
        note_r = Text("farther apart  →  much weaker", font_size=26, color=INK)
        note_r.next_to(note_mass, RIGHT, buff=0.9)
        self.play(Indicate(parts["num"], color=M2_C, scale_factor=1.2), run_time=0.8)
        self.play(FadeIn(note_mass, shift=UP * 0.1), run_time=0.5)
        self.beat(0.8)
        self.play(Indicate(parts["den"], color=GOLD, scale_factor=1.3), run_time=0.8)
        self.play(FadeIn(note_r, shift=UP * 0.1), run_time=0.5)
        self.beat(1.4)
        self.play(FadeOut(VGroup(diagram, note_mass, note_r)),
                  formula.animate.scale(0.8).to_edge(UP, buff=1.05), run_time=0.7)

        # the inverse-square, made concrete
        isq = Text("Inverse-square: double the distance → a quarter of the force.",
                   font_size=26, color=INK).move_to([0, 1.4, 0])
        self.play(FadeIn(isq, shift=DOWN * 0.1), run_time=0.6)
        src = ball(0.5, M1_C).move_to([-5.2, -1.2, 0])
        self.play(FadeIn(src), run_time=0.4)
        rows = [(1, 1.0, "r", "F"), (2, 0.25, "2r", "F / 4"), (3, 1 / 9, "3r", "F / 9")]
        group = VGroup()
        for i, (d, frac, dlab, flab) in enumerate(rows):
            x = -5.2 + d * 1.55
            probe = Dot([x, -1.2, 0], radius=0.11, color=M2_C)
            arr = Arrow([x, -1.2, 0], [x + 0.2 + frac * 1.7, -1.2, 0], buff=0,
                        color=FORCE_C, stroke_width=6, tip_length=0.2)
            dl = Text(dlab, font_size=22, color=MUTED).next_to(probe, DOWN, buff=0.22)
            fl = Text(flab, font_size=23, color=FORCE_C, weight="BOLD").next_to(arr, UP, buff=0.12)
            row = VGroup(probe, arr, dl, fl)
            self.play(FadeIn(probe), GrowArrow(arr), FadeIn(dl), FadeIn(fl), run_time=0.55)
            self.beat(0.7)
            group.add(row)
        self.beat(1.2)

        # G is tiny → gravity is weak, but mass wins at planetary scale
        self.play(FadeOut(VGroup(isq, src, group)), run_time=0.5)
        gline = mtext([("G  =  6.674 × 10", "b", GOLD), ("−11", "^", GOLD),
                       ("  N·m", "b", MUTED), ("2", "^", MUTED),
                       (" / kg", "b", MUTED), ("2", "^", MUTED)], base_fs=32)
        gline.move_to([0, 0.5, 0])
        gnote = Text("So tiny that gravity is by far the weakest force —", font_size=25, color=INK)
        gnote2 = Text("but mass piles up, and planets are enormous.", font_size=25,
                      color=GOLD, weight="BOLD")
        VGroup(gnote, gnote2).arrange(DOWN, buff=0.16).next_to(gline, DOWN, buff=0.5)
        self.play(FadeIn(gline, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(gnote), run_time=0.5)
        self.play(FadeIn(gnote2, shift=UP * 0.1), run_time=0.5)
        self.beat(1.8)
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Cosmos: one law explains it all
    # ====================================================================== #
    def scene_cosmos(self):
        header = self.section_header("One law — from an apple to the cosmos", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # a little solar system on the left
        sun = planet(0.6, SUN_C).move_to([-3.6, -0.3, 0])
        glow = Circle(radius=0.85, color=SUN_C, fill_opacity=0.12,
                      stroke_width=0).move_to(sun.get_center())
        self.play(FadeIn(glow), GrowFromCenter(sun), run_time=0.6)

        specs = [(1.35, 0.16, M1_C, 0.9), (2.1, 0.2, M2_C, 0.65), (2.85, 0.26, EARTH_C, 0.5)]
        rings = VGroup()
        planets = VGroup()
        for (rr, pr, col, _sp) in specs:
            ring = DashedVMobject(Circle(radius=rr, color=FAINT, stroke_width=1.5).move_to(
                sun.get_center()), num_dashes=48)
            p = planet(pr, col).move_to(sun.get_center() + RIGHT * rr)
            rings.add(ring)
            planets.add(p)
        # a moon on the outer (Earth-like) planet
        earthlike = planets[2]
        moon = planet(0.09, MOON_C).move_to(earthlike.get_center() + RIGHT * 0.4)
        self.play(Create(rings), *[FadeIn(p) for p in planets], FadeIn(moon), run_time=1.0)

        # set them orbiting (inner faster), moon around its planet
        earth_moon = VGroup(earthlike, moon)
        self.play(
            Rotate(planets[0], angle=TAU * 0.9, about_point=sun.get_center()),
            Rotate(planets[1], angle=TAU * 0.6, about_point=sun.get_center()),
            Rotate(earth_moon, angle=TAU * 0.42, about_point=sun.get_center()),
            run_time=3.0, rate_func=linear,
        )

        # the checklist: one equation behind all of it
        mini, _ = gravity_formula(base_fs=30)
        mini.move_to([3.1, 2.5, 0])
        box = SurroundingRectangle(mini, color=GOLD, buff=0.2)
        self.play(FadeIn(mini), Create(box), run_time=0.7)

        items = [
            "the apple that falls",
            "the Moon around the Earth",
            "the planets around the Sun",
            "the ocean tides",
            "comets, stars, whole galaxies",
        ]
        checks = VGroup()
        for s in items:
            c = Text("✓", font_size=26, color=GOOD, weight="BOLD")
            t = Text(s, font_size=25, color=INK).next_to(c, RIGHT, buff=0.2)
            checks.add(VGroup(c, t))
        checks.arrange(DOWN, aligned_edge=LEFT, buff=0.26).next_to(mini, DOWN, buff=0.5)
        checks.to_edge(RIGHT, buff=0.7)
        for row in checks:
            self.play(FadeIn(row, shift=RIGHT * 0.12), run_time=0.4)
            self.beat(0.55)
        self.beat(1.2)

        # Einstein footnote — honest and forward-looking
        self.play(FadeOut(VGroup(checks, box, mini)),
                  VGroup(sun, glow, rings, planets, moon).animate.scale(0.8).to_edge(LEFT, buff=0.6),
                  run_time=0.7)
        foot = Text("Two centuries later, Einstein recast gravity", font_size=26, color=MUTED)
        foot2 = Text("as the curving of space and time —", font_size=26, color=MUTED)
        foot3 = Text("but for apples and planets, Newton still rules.", font_size=26,
                     color=INK, weight="BOLD")
        VGroup(foot, foot2, foot3).arrange(DOWN, buff=0.18).move_to([2.2, 0.9, 0])
        for f in (foot, foot2, foot3):
            self.play(FadeIn(f, shift=UP * 0.08), run_time=0.5)
            self.beat(0.6)
        self.beat(1.2)
        self.play(FadeOut(VGroup(foot, foot2, foot3)), run_time=0.5)

        punch = Text("From a falling apple to the motion of the planets —",
                     font_size=23, color=INK).move_to([1.8, 0.6, 0])
        punch2 = Text("one equation.", font_size=29, color=GOLD, weight="BOLD")
        punch2.next_to(punch, DOWN, buff=0.25)
        self.play(FadeIn(punch, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(punch2, shift=UP * 0.1), run_time=0.6)
        self.beat(2.2)
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_falling()
        self.scene_newton()
        self.scene_law()
        self.scene_cosmos()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_GravBase):
    def construct(self):
        self.play_intro()


class Falling(_GravBase):
    def construct(self):
        self.scene_falling()


class Newton(_GravBase):
    def construct(self):
        self.scene_newton()


class Law(_GravBase):
    def construct(self):
        self.scene_law()


class Cosmos(_GravBase):
    def construct(self):
        self.scene_cosmos()


class Outro(_GravBase):
    def construct(self):
        self.play_outro()


class Gravity(_GravBase):
    """The whole ~3-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    Gravity().render()

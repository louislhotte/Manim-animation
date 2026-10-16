"""Momentum — a short, house-style explainer on why momentum speeds up training.

A self-explanatory (no voice-over) film that answers one question: why does
adding a momentum term make gradient descent so much faster? It builds from the
problem (loss surfaces are often long, narrow valleys) to a genuine 3D payoff
(two balls racing down the valley: plain gradient descent versus momentum):

    1. Problem    -- training is gradient descent: step downhill, repeat. But real
                     loss surfaces form long, narrow valleys. Plain descent bounces
                     between the steep walls and barely creeps toward the goal.
    2. Idea       -- momentum keeps a velocity: v <- b*v - a*grad ; th <- th + v.
                     A heavy ball that remembers where it was going.
    3. Valley     -- **3D**: the real valley surface. Two balls start together; the
                     plain one zig-zags up the walls and crawls, the momentum one
                     damps the bounce and glides straight down the floor to the
                     minimum. The camera orbits the valley so its shape is clear.
                     This is the one scene where camera movement earns its keep.
    4. Mechanism  -- why it works: across the walls the gradient flips every step so
                     the accumulated velocity cancels; along the floor it always
                     points the same way so velocity compounds. Effective step grows
                     to a/(1-b).
    5. Recap      -- one card: the update rule and what momentum buys you.

Camera policy (house rule `camera-control-only-for-3d`): the 2D scenes use a
**static camera** -- zooming into a flat formula or diagram adds nothing. Camera
control is reserved for the one real `ThreeDScene` (Valley), where orbiting
reveals the shape of the loss valley from every side.

Everything on screen comes from one source of truth: the ravine
L(x, y) = 0.5*(KS*x^2 + KH*y^2) with a real learning rate, a real momentum
coefficient, and the two real optimiser paths (GD_PATH, MOM_PATH) computed by
running the actual update rules. The numbers in the captions are asserted below.

Scenes render individually (`Problem`, `Idea`, `Valley`, `Mechanism`, `Recap`,
`Intro`, `Outro`); the whole film is the stitch of them in order
(`./render.sh full` / `--stitch`) -- there is no single all-in-one class because
the film mixes 2D `Scene` and 3D `ThreeDScene`.

Env knobs:
    MOM_QUICK=1   shorten every hold for a fast sanity render
    MOM_DELAY=x   override the reading-hold multiplier
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

# ---- crisp text: render big, scale down (Pango mangles small sizes) ------- #
# MANDATORY shadow (manim-explainer SKILL 2).
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("MOM_QUICK") == "1"
DELAY = float(os.environ.get("MOM_DELAY", "0.3" if QUICK else "2.2"))
END_HOLD = 0.2 if QUICK else 1.9

# ---- palette (shared house style + momentum roles) ----------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / axes
GRID = "#232A38"        # faint gridlines / panel fills
FAINT = "#3A4152"       # guides

GD_C = "#FF7A5C"        # plain gradient descent (coral, the plodder)
MOM_C = "#43E08A"       # momentum (green, the hero)
GOAL_C = "#FFD166"      # the minimum / goal / formula rule (gold)
VELO_C = "#5B8DEF"      # the velocity vector (blue)
GOLD = GOAL_C

# surface height ramp: cool + muted so the bright warm/green balls pop on top
FLOOR_C = "#2C6E7F"     # valley floor (low loss)
MIDW_C = "#39507E"      # mid wall
WALL_C = "#5A3A7A"      # high wall (high loss)


# ========================================================================== #
# The ravine and the two real optimiser paths (one source of truth)
# ========================================================================== #
KS, KH = 0.5, 16.0      # curvature: KS shallow floor (x), KH steep walls (y)
ALPHA = 0.10            # learning rate
BETA = 0.80             # momentum coefficient
START = np.array([-3.0, 0.65])   # start part-way up the far wall of the valley
STEPS = 26
MINPT = np.array([0.0, 0.0])     # global minimum, L = 0
KAPPA = KH / KS                  # condition number (32)


def loss(p):
    return 0.5 * (KS * p[0] ** 2 + KH * p[1] ** 2)


def grad(p):
    return np.array([KS * p[0], KH * p[1]])


def _gd_path():
    p = START.copy()
    out = [p.copy()]
    for _ in range(STEPS):
        p = p - ALPHA * grad(p)
        out.append(p.copy())
    return np.array(out)


def _mom_path():
    p = START.copy()
    v = np.zeros(2)
    out = [p.copy()]
    for _ in range(STEPS):
        v = BETA * v - ALPHA * grad(p)
        p = p + v
        out.append(p.copy())
    return np.array(out)


GD_PATH = _gd_path()
MOM_PATH = _mom_path()
GD_DIST = np.hypot(GD_PATH[:, 0], GD_PATH[:, 1])
MOM_DIST = np.hypot(MOM_PATH[:, 0], MOM_PATH[:, 1])


def _sign_changes(col):
    s = np.sign(col[np.abs(col) > 1e-6])
    return int(np.sum(s[1:] != s[:-1]))


# step where momentum first gets within 0.2 of the goal
MOM_ARRIVE = int(np.where(MOM_DIST < 0.2)[0][0])

# ---- assertions: the story the captions tell must actually be true -------- #
assert 5.4 < loss(START) < 5.9, loss(START)
assert GD_DIST[-1] > 0.6, GD_DIST[-1]                 # plain GD misses the minimum
assert MOM_DIST[-1] < 0.15, MOM_DIST[-1]              # momentum reaches it
assert GD_DIST.min() > 0.5, GD_DIST.min()             # GD never even enters the basin
assert MOM_ARRIVE <= 10, MOM_ARRIVE                   # momentum arrives ~3x sooner
assert _sign_changes(GD_PATH[:, 1]) >= 6, _sign_changes(GD_PATH[:, 1])   # zig-zag
assert MOM_PATH[:, 0].max() < 0.9, MOM_PATH[:, 0].max()   # overshoot stays on surface
assert abs(KAPPA - 32.0) < 1e-6, KAPPA

# ---- 3D surface framing --------------------------------------------------- #
XMIN, XMAX = -3.35, 0.9        # along the valley floor (shallow)
YMIN, YMAX = -1.05, 1.05       # across the valley (steep walls)
ZTOP = 3.4
ZSCALE = ZTOP / loss(np.array([XMIN, YMAX]))   # scale so the tallest corner ~= ZTOP


def zof(x, y):
    return ZSCALE * loss(np.array([x, y]))


# ---- 2D top-down valley map (manual coord map: full control, no axis box) - #
OX, OY = 0.0, -0.35            # screen anchor of the valley minimum
XU, YU = 1.12, 1.55            # screen units per data unit (exaggerate the width)


def P2(x, y):
    return np.array([OX + x * XU, OY + y * YU, 0.0])


def contour2d(c, color=FAINT, width=2.0, opacity=1.0):
    """A single loss level-set L=c as a closed ellipse on the 2D map."""
    sx, sy = np.sqrt(2 * c / KS), np.sqrt(2 * c / KH)
    ts = np.linspace(0, TAU, 120)
    pts = [P2(sx * np.cos(t), sy * np.sin(t)) for t in ts]
    e = VMobject().set_points_smoothly(pts)
    e.set_stroke(color=color, width=width, opacity=opacity)
    return e


def path2d(pts, color, width=4.0):
    """A polyline through data points on the 2D map (sharp corners kept)."""
    v = VMobject().set_points_as_corners([P2(x, y) for (x, y) in pts])
    v.set_stroke(color=color, width=width)
    return v


# ========================================================================== #
# Small reusable pieces
# ========================================================================== #
def bullet(text, color=INK, fs=24, dot=GOLD, dot_r=0.06):
    d = Dot(radius=dot_r, color=dot)
    t = Text(text, font_size=fs, color=color)
    t.next_to(d, RIGHT, buff=0.24)
    d.align_to(t, UP).shift(DOWN * 0.10)
    return VGroup(d, t)


def piece_row(pieces, buff=0.16):
    """A formula row from (text, color[, size]) tuples, baseline-aligned."""
    mobs = []
    for spec in pieces:
        txt, col = spec[0], spec[1]
        fs = spec[2] if len(spec) > 2 else 38
        mobs.append(Text(txt, font_size=fs, color=col, weight=BOLD))
    g = VGroup(*mobs).arrange(RIGHT, buff=buff, aligned_edge=DOWN)
    return g


# ========================================================================== #
# Shared helpers (no camera control -- that lives only in the 3D scene)
# ========================================================================== #
class _Common:
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.25))

    def section_header(self, label, color):
        t = Text(label, font_size=33, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=4)
        return VGroup(t, line)

    def say(self, text, color=INK, fs=25, y=-3.45, weight=NORMAL):
        cap = Text(text, font_size=fs, color=color, weight=weight)
        if cap.width > 12.6:
            cap.scale_to_fit_width(12.6)
        cap.move_to([0, y, 0])
        return cap

    def clamp_w(self, mob, w=12.4):
        if mob.width > w:
            mob.scale_to_fit_width(w)
        return mob


# ========================================================================== #
class _MoBase(_Common, Scene):
    """Base for every 2D scene. Static camera by design."""

    def setup(self):
        self.camera.background_color = BG

    def wipe(self, rt=0.7):
        self.wait(END_HOLD)
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    # ---- house-style intro / outro cards ---------------------------------- #
    def _rule_under(self, header, color=GOLD, pad=1.0, drop=0.45):
        return Line(
            [header.get_left()[0] - pad, header.get_bottom()[1] - drop, 0],
            [header.get_right()[0] + pad, header.get_bottom()[1] - drop, 0],
        ).set_stroke(width=3, color=color)

    def introduction(self, title1, title2):
        header = Text(title1, font_size=54, color=INK, weight="BOLD")
        header.set(width=min(10.5, header.width))
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=VELO_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        sub = Text(title2, font_size=30, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.card_wait(2.0)
        return VGroup(header, writer, line)

    def play_intro(self):
        group = self.introduction(
            "Momentum",
            "Why a running start makes gradient descent so much faster",
        )
        self.play(FadeOut(group), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=VELO_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.5)
        self.card_wait(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.1)
        self.card_wait(2.2)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 -- the problem: narrow valleys
    # ====================================================================== #
    def scene_problem(self):
        header = self.section_header("The problem: narrow valleys", GD_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        rule = piece_row([
            ("θ", INK), ("←", MUTED), ("θ", INK), ("−", MUTED),
            ("α", GOLD), ("∇L(θ)", GD_C),
        ]).scale(0.92).move_to([0, 2.55, 0])
        cap = self.say("Training a model is gradient descent: take a step downhill "
                       "in the loss, then repeat.", color=MUTED)
        self.play(Write(rule), run_time=1.1)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.6)
        self.beat(1.7)

        # the top-down valley map
        contours = VGroup(
            contour2d(7.2, color=FAINT, width=2.0, opacity=0.55),
            contour2d(4.6, color=FAINT, width=2.0, opacity=0.7),
            contour2d(2.6, color=MIDW_C, width=2.2, opacity=0.9),
            contour2d(1.2, color=MIDW_C, width=2.4),
            contour2d(0.4, color=FLOOR_C, width=2.6),
        )
        goal = VGroup(
            Dot(P2(0, 0), radius=0.11, color=GOAL_C),
            Text("goal", font_size=20, color=GOAL_C, weight=BOLD).move_to(P2(0, 0) + DOWN * 0.42 + RIGHT * 0.15),
        )
        vlabel = Text("a long, narrow valley in the loss", font_size=22, color=INK)
        vlabel.move_to([0, 1.35, 0])
        cap2 = self.say("Real loss surfaces are not round bowls. They often form "
                        "long, narrow valleys.", color=INK)
        self.play(ReplacementTransform(cap, cap2),
                  rule.animate.scale(0.8).to_corner(UR, buff=0.5),
                  run_time=0.8)
        self.play(LaggedStart(*[Create(c) for c in contours], lag_ratio=0.18),
                  run_time=1.8)
        self.play(FadeIn(goal), FadeIn(vlabel, shift=DOWN * 0.1), run_time=0.7)
        self.beat(1.8)

        # the GD zig-zag path
        start_dot = Dot(P2(*START), radius=0.09, color=GD_C)
        start_lab = Text("start", font_size=20, color=GD_C, weight=BOLD)
        start_lab.next_to(start_dot, UP, buff=0.16)
        gd_line = path2d(GD_PATH, GD_C, width=4.0)
        cap3 = self.say("Plain gradient descent bounces between the steep walls and "
                        "barely creeps toward the goal.", color=GD_C)
        self.play(FadeIn(start_dot), FadeIn(start_lab, shift=DOWN * 0.1),
                  ReplacementTransform(cap2, cap3), run_time=0.8)
        self.play(Create(gd_line), run_time=3.0, rate_func=linear)
        end_dot = Dot(P2(*GD_PATH[-1]), radius=0.09, color=GD_C)
        self.play(FadeIn(end_dot, scale=1.4), run_time=0.4)
        self.beat(1.6)

        take = Text("Almost every step is spent crossing the valley, not moving "
                    "down it.", font_size=26, color=INK, weight=BOLD)
        self.clamp_w(take).move_to([0, -2.55, 0])
        self.play(FadeIn(take, shift=UP * 0.1), run_time=0.7)
        self.beat(2.2)
        self.wipe()

    # ====================================================================== #
    # Scene 2 -- the idea: keep a velocity
    # ====================================================================== #
    def scene_idea(self):
        header = self.section_header("The idea: keep a velocity", MOM_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        intro = Text("Instead of stepping by the gradient, roll a heavy ball "
                     "downhill.", font_size=27, color=INK)
        self.clamp_w(intro, 11.0).move_to([0, 2.6, 0])
        self.play(FadeIn(intro, shift=DOWN * 0.15), run_time=0.7)
        self.beat(1.4)

        # the two update rules, side by side
        gd_title = Text("plain gradient descent", font_size=22, color=GD_C, weight=BOLD)
        gd_rule = piece_row([
            ("θ", INK), ("←", MUTED), ("θ", INK), ("−", MUTED),
            ("α", GOLD), ("∇L", GD_C),
        ]).scale(0.9)
        gd_box = VGroup(gd_title, gd_rule).arrange(DOWN, buff=0.35)
        gd_box.move_to([-3.5, 0.9, 0])

        mom_title = Text("with momentum", font_size=22, color=MOM_C, weight=BOLD)
        mom_r1 = piece_row([
            ("v", VELO_C), ("←", MUTED), ("β", GOLD), ("v", VELO_C), ("−", MUTED),
            ("α", GOLD), ("∇L", GD_C),
        ]).scale(0.9)
        mom_r2 = piece_row([
            ("θ", INK), ("←", MUTED), ("θ", INK), ("+", MUTED), ("v", VELO_C),
        ]).scale(0.9)
        # align the two momentum rows on their assignment arrow
        mom_r2.next_to(mom_r1, DOWN, buff=0.3)
        mom_r2.shift(RIGHT * (mom_r1[1].get_x() - mom_r2[1].get_x()))
        mom_rule = VGroup(mom_r1, mom_r2)
        mom_box = VGroup(mom_title, mom_rule).arrange(DOWN, buff=0.35)
        mom_box.move_to([3.4, 0.82, 0])

        divider = DashedLine([0, 1.9, 0], [0, -0.2, 0], color=FAINT, stroke_width=2)

        self.play(FadeIn(gd_box, shift=RIGHT * 0.1), run_time=0.7)
        self.beat(0.8)
        self.play(FadeIn(mom_box, shift=LEFT * 0.1), Create(divider), run_time=0.9)
        cap = self.say("Keep a velocity v. Each step nudges the velocity by the "
                       "gradient, then moves along it.", color=INK)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.6)
        self.play(Circumscribe(mom_r1, color=VELO_C, buff=0.14, run_time=1.5))
        self.beat(1.8)

        cap2 = self.say("The β term keeps most of the old velocity, so the ball "
                        "remembers where it was already going.", color=VELO_C)
        self.play(ReplacementTransform(cap, cap2),
                  Indicate(mom_r1[2], color=GOLD, scale_factor=1.4), run_time=1.0)
        self.beat(2.0)

        # clear the rules, then race both real paths on the same valley
        self.play(FadeOut(intro, gd_box, mom_box, divider, cap2), run_time=0.7)

        contours = VGroup(
            contour2d(7.2, color=FAINT, width=1.8, opacity=0.5),
            contour2d(4.6, color=FAINT, width=1.8, opacity=0.65),
            contour2d(2.6, color=MIDW_C, width=2.0, opacity=0.85),
            contour2d(1.2, color=MIDW_C, width=2.2),
            contour2d(0.4, color=FLOOR_C, width=2.4),
        )
        goal = Dot(P2(0, 0), radius=0.10, color=GOAL_C)
        goal_lab = Text("goal", font_size=20, color=GOAL_C, weight=BOLD).next_to(goal, DOWN, buff=0.18)
        start_dot = Dot(P2(*START), radius=0.08, color=INK)
        start_lab = Text("start", font_size=20, color=INK).next_to(start_dot, UP, buff=0.14)
        self.play(LaggedStart(*[Create(c) for c in contours], lag_ratio=0.15),
                  FadeIn(goal), FadeIn(goal_lab), FadeIn(start_dot), FadeIn(start_lab),
                  run_time=1.4)

        gd_line = path2d(GD_PATH, GD_C, width=3.0).set_stroke(opacity=0.6)
        mom_line = path2d(MOM_PATH, MOM_C, width=4.5)
        cap3 = self.say("On the very same valley, plain descent stays stuck near the "
                        "start.", color=GD_C)
        self.play(Create(gd_line), FadeIn(cap3, shift=UP * 0.1),
                  run_time=1.8, rate_func=linear)
        self.beat(1.4)

        cap4 = self.say("Momentum keeps its speed and sweeps all the way down to the "
                        "goal.", color=MOM_C)
        self.play(Create(mom_line), ReplacementTransform(cap3, cap4),
                  run_time=2.6, rate_func=linear)
        self.beat(2.2)
        self.wipe()

    # ====================================================================== #
    # Scene 4 -- why it works (the mechanism)
    # ====================================================================== #
    def scene_mechanism(self):
        header = self.section_header("Why momentum wins", MOM_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # velocity as a running, discounted sum of past gradients
        vsum = piece_row([
            ("v", VELO_C), ("=", MUTED), ("−α (", MUTED), ("g", GD_C), ("+", MUTED),
            ("β g", GD_C), ("+", MUTED), ("β²g", GD_C), ("+ …", MUTED), (")", MUTED),
        ], buff=0.14).scale(0.82).move_to([0, 2.5, 0])
        cap = self.say("The velocity is really a running, fading sum of every past "
                       "gradient.", color=INK)
        self.play(Write(vsum), run_time=1.2)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.6)
        self.beat(1.8)

        # two panels: across the walls (cancel) vs along the floor (add up)
        # LEFT panel: across the steep walls -> gradients alternate -> cancel
        left_ttl = Text("across the steep walls", font_size=22, color=GD_C, weight=BOLD)
        up, dn = UP * 0.7, DOWN * 0.7
        left_arrows = VGroup(*[
            Arrow(ORIGIN, d, buff=0, color=GD_C, stroke_width=6,
                  max_tip_length_to_length_ratio=0.35)
            for d in (up, dn, up, dn, up)
        ]).arrange(RIGHT, buff=0.34)
        left_sum = VGroup(
            Text("sum ≈ 0", font_size=24, color=MUTED, weight=BOLD),
            Text("the bounce cancels", font_size=20, color=GD_C),
        ).arrange(DOWN, buff=0.16)
        left = VGroup(left_ttl, left_arrows, left_sum).arrange(DOWN, buff=0.42)
        left.move_to([-3.4, -0.55, 0])

        # RIGHT panel: along the floor -> gradients agree -> add up
        right_ttl = Text("along the shallow floor", font_size=22, color=MOM_C, weight=BOLD)
        right_arrows = VGroup(*[
            Arrow(ORIGIN, RIGHT * 0.62, buff=0, color=MOM_C, stroke_width=6,
                  max_tip_length_to_length_ratio=0.35)
            for _ in range(5)
        ]).arrange(RIGHT, buff=0.22)
        big = Arrow(ORIGIN, RIGHT * 2.6, buff=0, color=MOM_C, stroke_width=9,
                    max_tip_length_to_length_ratio=0.16)
        right_sum = VGroup(
            big,
            Text("velocity builds up", font_size=20, color=MOM_C),
        ).arrange(DOWN, buff=0.18)
        right = VGroup(right_ttl, right_arrows, right_sum).arrange(DOWN, buff=0.42)
        right.move_to([3.4, -0.6, 0])

        divider = DashedLine([0, 0.85, 0], [0, -2.2, 0], color=FAINT, stroke_width=2)

        cap2 = self.say("Across the valley the gradient flips every step, so the "
                        "stored velocity cancels itself out.", color=GD_C)
        self.play(FadeIn(left_ttl, shift=DOWN * 0.1), ReplacementTransform(cap, cap2),
                  Create(divider), run_time=0.8)
        self.play(LaggedStart(*[GrowArrow(a) for a in left_arrows], lag_ratio=0.22),
                  run_time=1.4)
        self.play(FadeIn(left_sum, shift=UP * 0.1), run_time=0.7)
        self.beat(1.8)

        cap3 = self.say("Along the floor every gradient points the same way, so the "
                        "velocity keeps adding up.", color=MOM_C)
        self.play(FadeIn(right_ttl, shift=DOWN * 0.1), ReplacementTransform(cap2, cap3),
                  run_time=0.7)
        self.play(LaggedStart(*[GrowArrow(a) for a in right_arrows], lag_ratio=0.22),
                  run_time=1.4)
        self.play(GrowArrow(big), FadeIn(right_sum[1], shift=UP * 0.1), run_time=0.8)
        self.beat(1.8)

        # the effective-step payoff (centered; panels have done their job)
        eff = piece_row([
            ("effective step", MUTED, 30), ("→", MUTED, 30),
            ("α / (1 − β)", GOLD, 36), ("=", MUTED, 30), ("5α here", INK, 30),
        ], buff=0.26).move_to([0, -0.4, 0])
        self.play(FadeOut(left_sum, right_sum, left_arrows, right_arrows,
                          left_ttl, right_ttl, divider),
                  cap3.animate.set_opacity(0.0), run_time=0.6)
        self.play(FadeIn(eff, shift=UP * 0.1), run_time=0.8)
        self.play(Circumscribe(eff[2], color=GOLD, buff=0.14, run_time=1.4))
        cap4 = self.say("Consistent directions compound; conflicting ones cancel. "
                        "That is all momentum is.", color=INK, weight=BOLD)
        self.play(FadeIn(cap4, shift=UP * 0.1), run_time=0.7)
        self.beat(2.4)
        self.wipe()

    # ====================================================================== #
    # Scene 5 -- recap card
    # ====================================================================== #
    def scene_recap(self):
        title = Text("Momentum, in one card", font_size=40, color=INK, weight="BOLD")
        title.to_edge(UP, buff=0.6)
        rule = Line(title.get_left(), title.get_right()).next_to(title, DOWN, buff=0.14)
        rule.set_stroke(GOLD, 3)
        self.play(Write(title), Create(rule), run_time=1.1)
        self.beat(0.5)

        r1 = piece_row([
            ("v", VELO_C), ("←", MUTED), ("β", GOLD), ("v", VELO_C), ("−", MUTED),
            ("α", GOLD), ("∇L", GD_C),
        ]).scale(0.85)
        r2 = piece_row([
            ("θ", INK), ("←", MUTED), ("θ", INK), ("+", MUTED), ("v", VELO_C),
        ]).scale(0.85)
        r2.next_to(r1, DOWN, buff=0.28)
        r2.shift(RIGHT * (r1[1].get_x() - r2[1].get_x()))
        formula = VGroup(r1, r2).next_to(rule, DOWN, buff=0.42)
        self.play(FadeIn(formula, shift=UP * 0.1), run_time=0.8)
        self.beat(0.8)

        points = [
            ("It remembers past gradients as a velocity, not just the latest step.", VELO_C),
            ("It builds speed along the shallow direction, where plain descent only crawls.", MOM_C),
            ("It reaches the minimum in far fewer steps on these narrow valleys.", GOAL_C),
            ("It also rolls through small bumps and flat spots that stall plain descent.", MUTED),
        ]
        rows = VGroup(*[bullet(t, fs=24, dot=c, dot_r=0.06) for t, c in points])
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.34)
        rows.next_to(formula, DOWN, buff=0.55)
        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.15), run_time=0.55)
            self.beat(0.9)
        self.beat(0.6)

        punch = Text("A running start beats starting from scratch every step.",
                     font_size=26, color=INK, weight=BOLD, slant=ITALIC)
        punch.next_to(rows, DOWN, buff=0.5)
        self.play(FadeIn(punch, shift=UP * 0.1), run_time=0.7)
        self.beat(2.2)
        self.wipe()


# ========================================================================== #
# Scene 3 -- the 3D payoff: two balls race down the real valley.
# The ONLY scene with camera movement -- because there is real 3D to see.
# ========================================================================== #
class Valley(_Common, ThreeDScene):
    def hud_swap(self, old, new, rt=0.6):
        """Cross-fade a fixed-in-frame (2D HUD) caption for another."""
        self.add_fixed_in_frame_mobjects(new)
        self.play(FadeOut(old), FadeIn(new), run_time=rt)

    def construct(self):
        self.camera.background_color = BG

        axes = ThreeDAxes(
            x_range=[XMIN, XMAX, 1], y_range=[YMIN, YMAX, 0.5], z_range=[0, ZTOP + 0.2, 1],
            x_length=8.2, y_length=4.4, z_length=3.2,
            axis_config={"stroke_color": MUTED, "stroke_width": 2},
        )
        surf = Surface(
            lambda u, v: axes.c2p(u, v, zof(u, v)),
            u_range=[XMIN, XMAX], v_range=[YMIN, YMAX], resolution=(52, 34),
        )
        surf.set_style(fill_opacity=0.92, stroke_width=0.6, stroke_color=BG)
        surf.set_fill_by_value(
            axes=axes,
            colorscale=[(FLOOR_C, 0.0), (MIDW_C, 0.5 * ZTOP), (WALL_C, ZTOP)],
            axis=2,
        )

        # billboard direction labels (face the camera); shown only while we
        # establish the valley, then faded so the race stays clean
        xl = Text("along the floor", font_size=20, color=INK)
        xl.move_to(axes.c2p(-0.9, 0.0, ZTOP * 0.52))
        yl = Text("across the walls", font_size=20, color=INK)
        yl.move_to(axes.c2p(XMIN - 0.15, 0.0, ZTOP * 0.62))

        header = self.section_header("Two runs down the same valley", GOLD)

        # ---- establish the valley -------------------------------------- #
        self.set_camera_orientation(phi=70 * DEGREES, theta=-52 * DEGREES, zoom=0.9)
        self.add_fixed_in_frame_mobjects(header)
        self.play(FadeIn(header), run_time=0.6)
        self.play(Create(axes), run_time=1.1)
        self.add_fixed_orientation_mobjects(xl, yl)
        self.play(FadeIn(surf), run_time=1.8)

        cap = self.say("This is a loss surface shaped like a long, narrow valley. "
                       "Height is the loss.", color=MUTED)
        self.add_fixed_in_frame_mobjects(cap)
        self.play(FadeIn(cap), run_time=0.6)
        self.beat(1.6)

        # slow reveal: swing to look down the length of the valley
        cap2 = self.say("It falls steeply across, but only gently along the floor "
                        "toward the goal.", color=INK)
        self.hud_swap(cap, cap2)
        self.move_camera(phi=64 * DEGREES, theta=-86 * DEGREES, run_time=3.4)
        self.beat(1.2)

        # mark the goal at the minimum
        gmark = axes.c2p(0, 0, zof(0, 0) + 0.06)
        gstem = Line(axes.c2p(0, 0, 0), axes.c2p(0, 0, ZTOP * 0.82), color=GOAL_C, stroke_width=3)
        gdiamond = Dot3D(gmark, radius=0.14, color=GOAL_C)
        glab = Text("goal", font_size=22, color=GOAL_C, weight=BOLD)
        glab.move_to(axes.c2p(0, 0, ZTOP * 0.82) + np.array([0, 0, 0.3]))
        self.add_fixed_orientation_mobjects(glab)
        self.play(Create(gstem), FadeIn(gdiamond, scale=1.5), FadeIn(glab), run_time=0.9)
        self.beat(1.4)

        # swing back to a 3/4 racing view
        self.move_camera(phi=68 * DEGREES, theta=-46 * DEGREES, run_time=2.4)

        # ---- the two balls -------------------------------------------- #
        gd3 = [axes.c2p(x, y, zof(x, y) + 0.10) for (x, y) in GD_PATH]
        mom3 = [axes.c2p(x, y, zof(x, y) + 0.10) for (x, y) in MOM_PATH]

        gd_ball = Dot3D(gd3[0], radius=0.13, color=GD_C)
        mom_ball = Dot3D(mom3[0], radius=0.13, color=MOM_C)

        # fixed-in-frame legend so the viewer knows which ball is which
        leg = VGroup(
            VGroup(Dot(radius=0.09, color=MOM_C),
                   Text("momentum", font_size=22, color=MOM_C, weight=BOLD)).arrange(RIGHT, buff=0.18),
            VGroup(Dot(radius=0.09, color=GD_C),
                   Text("plain gradient descent", font_size=22, color=GD_C, weight=BOLD)).arrange(RIGHT, buff=0.18),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).to_corner(UR, buff=0.5)

        cap3 = self.say("Both balls start together at the same point.", color=INK)
        self.hud_swap(cap2, cap3)
        self.add_fixed_in_frame_mobjects(leg)
        self.play(FadeIn(gd_ball, scale=1.6), FadeIn(mom_ball, scale=1.6),
                  FadeIn(leg), FadeOut(xl), FadeOut(yl), run_time=0.7)
        self.beat(1.4)

        # sampler + trails driven by a single step tracker
        sv = ValueTracker(0.0)

        def sampler(pts):
            def upd(m):
                s = float(np.clip(sv.get_value(), 0, len(pts) - 1))
                i = min(int(np.floor(s)), len(pts) - 2)
                f = s - i
                m.move_to(pts[i] * (1 - f) + pts[i + 1] * f)
            return upd

        gd_ball.add_updater(sampler(gd3))
        mom_ball.add_updater(sampler(mom3))
        gd_trail = TracedPath(gd_ball.get_center, stroke_color=GD_C, stroke_width=4)
        mom_trail = TracedPath(mom_ball.get_center, stroke_color=MOM_C, stroke_width=5)
        self.add(gd_trail, mom_trail)

        cap4 = self.say("Momentum gathers speed along the floor and races down to "
                        "the goal, while plain descent barely moves.", color=INK)
        self.hud_swap(cap3, cap4)

        self.begin_ambient_camera_rotation(rate=0.055)
        self.play(sv.animate.set_value(STEPS), run_time=7.5, rate_func=linear)
        self.beat(0.8)

        # freeze positions, drop the updaters
        gd_ball.clear_updaters()
        mom_ball.clear_updaters()
        gd_trail.clear_updaters()
        mom_trail.clear_updaters()

        # flash the winner at the goal
        self.play(Flash(mom_ball, color=MOM_C, line_length=0.25, num_lines=16,
                        flash_radius=0.4), run_time=0.8)
        self.stop_ambient_camera_rotation()

        cap5 = self.say("Same twenty-six steps. Momentum reached the goal; plain "
                        "descent is still far short of it.", color=MOM_C, weight=BOLD)
        self.hud_swap(cap4, cap5)
        self.beat(2.4)

        # wipe
        self.wait(END_HOLD)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)


# ---- individually renderable scenes -------------------------------------- #
class Intro(_MoBase):
    def construct(self):
        self.play_intro()


class Problem(_MoBase):
    def construct(self):
        self.scene_problem()


class Idea(_MoBase):
    def construct(self):
        self.scene_idea()


class Mechanism(_MoBase):
    def construct(self):
        self.scene_mechanism()


class Recap(_MoBase):
    def construct(self):
        self.scene_recap()


class Outro(_MoBase):
    def construct(self):
        self.play_outro()


if __name__ == "__main__":
    # sanity: print the headline numbers the film asserts
    print(f"kappa={KAPPA:.0f}  accel~{1/(1-BETA):.0f}x  start loss={loss(START):.2f}")
    print(f"GD  final dist={GD_DIST[-1]:.3f}  MOM final dist={MOM_DIST[-1]:.3f}")
    print(f"momentum within 0.2 of goal at step {MOM_ARRIVE} of {STEPS}")
    print(f"GD y sign-changes={_sign_changes(GD_PATH[:,1])}")

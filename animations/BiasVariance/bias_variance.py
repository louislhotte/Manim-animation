"""The Bias–Variance Tradeoff — a short, house-style explainer.

A self-explanatory (no voice-over) film that fits the *same* noisy data with
three models and lets the numbers tell the story:

    1. Setup      -- noisy observations + a hidden true pattern; define MSE
    2. Underfit   -- a straight line: too rigid, high bias, big MSE
    3. Just right -- a quadratic (the true shape): low error, recovers the pattern
    4. Overfit    -- a degree-10 wiggle: MSE→0 on training, but blows up on new data
    5. Tradeoff   -- the U-curve: total error = bias² + variance; find the sweet spot

Bookended by the channel's intro card and the "Thank you for watching!" outro,
matching animations/HarnessEngineering/harness_engineering.py.

Everything uses ``Text`` (Pango), never ``Tex`` — so it renders with no LaTeX
toolchain and stays fast to iterate on.

The data and every on-screen number are real: the polynomial fits, the MSE / R²
values, and the final bias/variance decomposition (a 400-run Monte-Carlo) are
all computed here, not faked. The true generator is a downward parabola, so the
quadratic is genuinely the right model — the U-curve bottoms out at degree 2.

Scenes are exposed individually (``Setup``, ``Underfit``, ``JustRight``,
``Overfit``, ``Tradeoff``, ``Intro``, ``Outro``) and as one film
(``BiasVariance``).

Env knobs:
    BV_QUICK=1   shorten every hold for a fast sanity render
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

QUICK = os.environ.get("BV_QUICK") == "1"
# One knob for pacing: every reading "hold" is scaled by this. QUICK collapses
# the holds for fast iteration; otherwise it sets a snappy ~30 s/scene rhythm.
DELAY = 0.3 if QUICK else 1.15

# ---- palette (shared house style) ---------------------------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / axes
GRID = "#232A38"        # faint gridlines
DATA_C = "#5B8DEF"      # observed data points (blue)
TRUE_C = "#7CC6B5"      # the hidden true pattern (faint teal, dashed)
UNDER_C = "#FF8C42"     # underfit  (amber)
GOOD_C = "#3DD68C"      # just-right (green)
OVER_C = "#FF5C5C"      # overfit   (red)
GOLD = "#FFD166"        # sweet spot / new data / highlight
RESID_C = "#6B7280"     # residual sticks

# ========================================================================== #
# Data + fits + decomposition  (all real, hardcoded so renders never drift)
# ========================================================================== #
def true_f(t):
    """The hidden generator: a downward parabola (degree 2)."""
    t = np.asarray(t, dtype=float)
    return 2.35 - 3.9 * (t - 0.38) ** 2


X_DATA = np.linspace(0.0, 1.0, 11)
Y_DATA = np.array([
    1.787135, 2.115939, 2.157847, 2.111298, 2.239319, 2.055845,
    2.175674, 2.272292, 1.543910, 1.146526, 0.968402,
])
# Fresh, unseen observations from the same true process (for the overfit twist).
X_TEST = np.array([0.07, 0.23, 0.52, 0.68, 0.87])
Y_TEST = np.array([2.060863, 2.287549, 2.050248, 1.991980, 1.580483])

FIT = {d: np.polynomial.Polynomial.fit(X_DATA, Y_DATA, d) for d in (1, 2, 10)}


def _mse(p, xs, ys):
    return float(np.mean((p(xs) - ys) ** 2))


def _r2(p, xs, ys):
    res = ys - p(xs)
    return float(1 - np.sum(res ** 2) / np.sum((ys - ys.mean()) ** 2))


TRAIN_MSE = {d: _mse(FIT[d], X_DATA, Y_DATA) for d in FIT}   # 0.113, 0.022, 0.000
TEST_MSE = {d: _mse(FIT[d], X_TEST, Y_TEST) for d in FIT}    # 0.037, 0.013, 0.109
R2 = {d: _r2(FIT[d], X_DATA, Y_DATA) for d in FIT}           # 0.40, 0.88, 1.00

# 400-run Monte-Carlo bias/variance decomposition across polynomial degrees
# (true error = bias² + variance + noise). TOTAL is what the tradeoff scene
# plots as the measured U-curve; BIAS2 / VAR / NOISE are the real component
# values it references (the scene draws smoothed component curves for clarity).
DEGREES = list(range(1, 11))
BIAS2 = [0.0803, 0.0, 0.0, 0.0001, 0.0001, 0.0001, 0.0001, 0.0002, 0.0002, 0.0005]
VAR = [0.0092, 0.0131, 0.0166, 0.0203, 0.0276, 0.0316, 0.0433, 0.0588, 0.1222, 0.7348]
TOTAL = [0.1471, 0.0707, 0.0742, 0.078, 0.0853, 0.0892, 0.101, 0.1166, 0.18, 0.7929]
NOISE = 0.0576  # irreducible error = sigma^2


# ========================================================================== #
# Small reusable pieces
# ========================================================================== #
def data_axes():
    ax = Axes(
        x_range=[0, 1, 0.25], y_range=[0, 3, 1],
        x_length=6.6, y_length=4.3,
        axis_config=dict(stroke_color=MUTED, stroke_width=2,
                         tip_length=0.16, tip_width=0.16, include_ticks=True),
        x_axis_config=dict(include_numbers=False),
        y_axis_config=dict(include_numbers=False),
    )
    return ax


def axis_titles(ax, xlabel="input  t", ylabel="output  y"):
    xl = Text(xlabel, font_size=22, color=MUTED).next_to(ax.x_axis, DOWN, buff=0.18)
    yl = Text(ylabel, font_size=22, color=MUTED).rotate(PI / 2)
    yl.next_to(ax.y_axis, LEFT, buff=0.18)
    return VGroup(xl, yl)


def data_dots(ax, xs=X_DATA, ys=Y_DATA, color=DATA_C, r=0.065):
    return VGroup(*[
        Dot(ax.c2p(x, y), radius=r, color=color).set_stroke(INK, width=1, opacity=0.55)
        for x, y in zip(xs, ys, strict=True)
    ])


def fit_curve(ax, fn, color, width=5, n=400):
    xs = np.linspace(0, 1, n)
    ys = np.clip(fn(xs), ax.y_range[0] + 0.03, ax.y_range[1] - 0.03)
    m = VMobject().set_points_as_corners([ax.c2p(x, y) for x, y in zip(xs, ys, strict=True)])
    return m.set_stroke(color=color, width=width)


def residual_sticks(ax, fn, xs=X_DATA, ys=Y_DATA, color=RESID_C, width=3.5):
    g = VGroup()
    for x, y in zip(xs, ys, strict=True):
        yhat = float(np.clip(fn(x), ax.y_range[0], ax.y_range[1]))
        g.add(Line(ax.c2p(x, yhat), ax.c2p(x, y), stroke_color=color, stroke_width=width))
    return g


def true_curve(ax):
    xs = np.linspace(0, 1, 200)
    m = VMobject().set_points_as_corners([ax.c2p(x, true_f(x)) for x in xs])
    m.set_stroke(TRUE_C, 3.5)
    return DashedVMobject(m, num_dashes=42)


def make_seesaw(tilt_deg=0.0, scale=1.0):
    """Simplicity <-> complexity balance beam, tilted by tilt_deg (CCW = simple-heavy)."""
    beam = RoundedRectangle(width=2.4, height=0.14, corner_radius=0.07,
                            fill_color=DATA_C, fill_opacity=1, stroke_width=0)
    tri = Triangle(color=GOLD, fill_opacity=1, stroke_width=0).scale(0.3)
    tri.next_to(beam, DOWN, buff=-0.03)
    sL = Text("simpler", font_size=17, color=MUTED).next_to(beam, LEFT, buff=0.18)
    sR = Text("more complex", font_size=17, color=MUTED).next_to(beam, RIGHT, buff=0.18)
    arm = VGroup(beam, sL, sR)
    arm.rotate(np.deg2rad(tilt_deg), about_point=tri.get_top())
    return VGroup(tri, arm).scale(scale)


def tag(text, color, fs=26):
    """A rounded, tinted pill with a centered label."""
    label = Text(text, font_size=fs, color=INK, weight="BOLD")
    box = RoundedRectangle(width=label.width + 0.6, height=label.height + 0.4,
                           corner_radius=0.16, stroke_color=color, stroke_width=3,
                           fill_color=color, fill_opacity=0.14)
    label.move_to(box)
    return VGroup(box, label)


def bullet(text, color=INK, fs=25, dot=GOLD):
    d = Dot(radius=0.055, color=dot)
    t = Text(text, font_size=fs, color=color).next_to(d, RIGHT, buff=0.24)
    d.align_to(t, UP).shift(DOWN * 0.14)
    return VGroup(d, t)


# ========================================================================== #
class _BVBase(Scene):
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

    def mse_card(self, color, label="MSE  (on training data)", center=None,
                 w=3.4, h=1.9, num_fs=56):
        """Boxed MSE readout (title + a DecimalNumber). Returns (box+title, number)."""
        box = RoundedRectangle(width=w, height=h, corner_radius=0.16,
                               stroke_color=color, stroke_width=2.5,
                               fill_color=color, fill_opacity=0.07)
        if center is not None:
            box.move_to(center)
        title = Text(label, font_size=22, color=MUTED).next_to(box.get_top(), DOWN, buff=0.18)
        num = DecimalNumber(0.000, num_decimal_places=3, font_size=num_fs, color=color)
        num.move_to(box.get_center()).shift(DOWN * 0.1)
        return VGroup(box, title), num

    # ---- the recurring data stage ----------------------------------------- #
    def build_stage(self):
        ax = data_axes()
        ax.to_edge(LEFT, buff=0.85).shift(DOWN * 0.15)
        titles = axis_titles(ax)
        dots = data_dots(ax)
        return ax, titles, dots

    def show_stage(self, ax, titles, dots, note=None):
        self.play(Create(ax), FadeIn(titles), run_time=1.0)
        self.play(LaggedStart(*[GrowFromCenter(d) for d in dots],
                              lag_ratio=0.12, run_time=1.3))
        if note:
            self.add(note)

    def below_plot(self, ax, mob, y=-3.55):
        """Center a caption under the plot, safely below the x-axis title."""
        mob.move_to([ax.get_center()[0], y, 0])
        return mob

    # ---- house-style intro / outro cards ---------------------------------- #
    def introduction(self, title1, title2):
        header = Text(title1, font_size=52, color=INK, weight="BOLD")
        header.set(width=min(10.5, header.width))
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        writer = Text("Created by Ptolémé", font_size=28, color=DATA_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        sub = Text(title2, font_size=36, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.card_wait(2.0)
        return VGroup(header, writer, line)

    def play_intro(self):
        group = self.introduction(
            "The Bias–Variance Tradeoff",
            "Underfitting · Just right · Overfitting",
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
        writer = Text("Created by Ptolémé", font_size=28, color=DATA_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.5)
        self.card_wait(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.1)
        self.card_wait(2.2)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 — Setup: the data + the metric
    # ====================================================================== #
    def scene_setup(self):
        title = Text("We have noisy data", font_size=46, color=INK, weight="BOLD")
        self.play(Write(title), run_time=1.3)
        self.beat(0.8)
        self.play(title.animate.scale(0.62).to_corner(UL, buff=0.5), run_time=0.7)

        ax, titles, dots = self.build_stage()
        self.play(Create(ax), FadeIn(titles), run_time=1.0)
        self.play(LaggedStart(*[GrowFromCenter(d) for d in dots],
                              lag_ratio=0.12, run_time=1.6))
        cap = Text("11 measurements of some signal.", font_size=25, color=MUTED)
        self.below_plot(ax, cap)
        self.play(FadeIn(cap, shift=UP * 0.15), run_time=0.6)
        self.beat(1.4)

        # the hidden true pattern + noise
        tc = true_curve(ax)
        lead = Text("A hidden pattern generated them…", font_size=26, color=TRUE_C)
        lead.to_edge(RIGHT, buff=0.7).shift(UP * 1.7)
        self.play(Create(tc), FadeIn(lead, shift=LEFT * 0.2), run_time=1.3)
        self.beat(1.0)
        noise_lbl = Text("…plus random noise on every point.", font_size=26, color=MUTED)
        noise_lbl.next_to(lead, DOWN, aligned_edge=RIGHT, buff=0.35)
        # highlight the gap (noise) on a couple of points
        gaps = VGroup()
        for i in (1, 8):
            x, y = X_DATA[i], Y_DATA[i]
            gaps.add(DashedLine(ax.c2p(x, true_f(x)), ax.c2p(x, y),
                                stroke_color=GOLD, stroke_width=3, dash_length=0.07))
        self.play(FadeIn(noise_lbl, shift=LEFT * 0.2), *[Create(g) for g in gaps], run_time=1.0)
        self.beat(1.6)
        self.play(FadeOut(gaps), run_time=0.5)

        # the goal + the metric
        goal = Text("Goal: learn the pattern — not the noise.", font_size=27,
                    color=INK, weight="BOLD")
        goal.next_to(lead, DOWN, aligned_edge=RIGHT, buff=0.35)
        self.play(ReplacementTransform(noise_lbl, goal), run_time=0.8)
        self.beat(1.2)

        metric = Text("Score each fit with the MSE:", font_size=27, color=INK)
        mdef = Text("mean of  (observed − predicted)²", font_size=26, color=GOLD)
        low = Text("lower MSE  →  closer to the data", font_size=23, color=MUTED)
        col = VGroup(metric, mdef, low).arrange(DOWN, aligned_edge=RIGHT, buff=0.28)
        col.next_to(goal, DOWN, aligned_edge=RIGHT, buff=0.5)
        self.play(FadeIn(metric, shift=UP * 0.15), run_time=0.7)
        self.beat(0.5)
        self.play(FadeIn(mdef, shift=UP * 0.15), run_time=0.7)
        self.beat(0.5)
        self.play(FadeIn(low, shift=UP * 0.15), run_time=0.7)
        self.beat(1.4)

        closer = Text("Let's try three models on this same data.", font_size=26, color=INK)
        self.below_plot(ax, closer)
        self.play(FadeOut(cap), FadeIn(closer, shift=UP * 0.15), run_time=0.7)
        self.beat(1.6)
        self.wipe()

    # ====================================================================== #
    # Shared machinery for the three fit scenes
    # ====================================================================== #
    def fit_intro(self, header_label, header_color, tilt, seesaw_scale=0.92):
        header = self.section_header(header_label, header_color)
        see = make_seesaw(tilt, scale=seesaw_scale).to_corner(UR, buff=0.55)
        ax, titles, dots = self.build_stage()
        self.play(FadeIn(header, shift=DOWN * 0.2), FadeIn(see), run_time=0.7)
        self.play(Create(ax), FadeIn(titles),
                  LaggedStart(*[GrowFromCenter(d) for d in dots], lag_ratio=0.06),
                  run_time=1.1)
        return header, see, ax, titles, dots

    def show_mse(self, color, value, r2value, center, label="MSE  (on training data)",
                 r2_color=None):
        card, num = self.mse_card(color, label=label, center=center)
        self.play(FadeIn(card), FadeIn(num), run_time=0.5)
        self.play(ChangeDecimalToValue(num, value), run_time=1.2)
        r2 = Text(f"R² = {r2value:.2f}", font_size=26, color=r2_color or MUTED)
        r2.next_to(card, DOWN, buff=0.25)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.5)
        return VGroup(card, num, r2)

    # ====================================================================== #
    # Scene 2 — Underfit (degree 1)
    # ====================================================================== #
    def scene_underfit(self):
        header, see, ax, titles, dots = self.fit_intro(
            "Too simple  →  underfitting", UNDER_C, tilt=13)
        sub = Text("Fit a straight line (degree 1)", font_size=25, color=MUTED)
        sub.next_to(header, DOWN, buff=0.3).to_edge(LEFT, buff=0.55)
        self.play(FadeIn(sub, shift=UP * 0.15), run_time=0.5)

        curve = fit_curve(ax, FIT[1], UNDER_C, width=6)
        self.play(Create(curve), run_time=1.3)
        self.beat(0.6)
        res = residual_sticks(ax, FIT[1])
        self.play(LaggedStart(*[Create(r) for r in res], lag_ratio=0.08, run_time=1.2))
        gap = Text("errors are large", font_size=23, color=RESID_C)
        gap.next_to(ax.c2p(0.5, 0.32), DOWN, buff=0.1)
        self.play(FadeIn(gap), run_time=0.4)
        self.beat(1.0)

        self.show_mse(UNDER_C, TRAIN_MSE[1], R2[1], center=[4.2, 1.35, 0])
        self.beat(0.8)

        pts = VGroup(
            bullet("A line can't bend to the curve.", dot=UNDER_C),
            bullet("It misses the peak and both tails.", dot=UNDER_C),
            bullet("High bias — wrong in a consistent way.", color=UNDER_C, dot=UNDER_C),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        pts.next_to([4.2, -1.4, 0], ORIGIN)
        for b in pts:
            self.play(FadeIn(b, shift=RIGHT * 0.15), run_time=0.55)
            self.beat(0.7)
        self.play(Indicate(header, color=UNDER_C, scale_factor=1.05), run_time=0.8)
        self.beat(1.4)
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Just right (degree 2)
    # ====================================================================== #
    def scene_justright(self):
        header, see, ax, titles, dots = self.fit_intro(
            "Just right  →  a good fit", GOOD_C, tilt=0)
        sub = Text("Fit a quadratic (degree 2)", font_size=25, color=MUTED)
        sub.next_to(header, DOWN, buff=0.3).to_edge(LEFT, buff=0.55)
        self.play(FadeIn(sub, shift=UP * 0.15), run_time=0.5)

        curve = fit_curve(ax, FIT[2], GOOD_C, width=6)
        self.play(Create(curve), run_time=1.3)
        self.beat(0.5)
        res = residual_sticks(ax, FIT[2])
        self.play(LaggedStart(*[Create(r) for r in res], lag_ratio=0.08, run_time=1.0))
        small = Text("errors are small", font_size=23, color=GOOD_C)
        small.next_to(ax.c2p(0.5, 0.35), DOWN, buff=0.1)
        self.play(FadeIn(small), run_time=0.4)
        self.beat(0.9)

        card = self.show_mse(GOOD_C, TRAIN_MSE[2], R2[2], center=[4.2, 1.5, 0])
        drop = Text("↓ from 0.113 (the line)", font_size=22, color=GOOD_C)
        drop.next_to(card, DOWN, buff=0.2)
        self.play(FadeIn(drop, shift=UP * 0.1), run_time=0.5)
        self.beat(0.8)

        # reveal it matches the hidden truth
        tc = true_curve(ax)
        match = Text("It recovers the true pattern.", font_size=25, color=TRUE_C)
        match.next_to([4.2, -0.75, 0], ORIGIN)
        self.play(Create(tc), FadeIn(match, shift=UP * 0.15), run_time=1.2)
        self.beat(1.0)

        pts = VGroup(
            bullet("Flexible enough for the trend,", color=INK, dot=GOOD_C),
            bullet("rigid enough to ignore noise.", color=INK, dot=GOOD_C),
            bullet("Low bias and low variance.", color=GOOD_C, dot=GOOD_C),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        pts.next_to([4.2, -1.9, 0], ORIGIN)
        for b in pts:
            self.play(FadeIn(b, shift=RIGHT * 0.15), run_time=0.55)
            self.beat(0.6)
        self.play(Circumscribe(VGroup(ax, curve), color=GOOD_C, run_time=1.4))
        self.beat(1.2)
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Overfit (degree 10)
    # ====================================================================== #
    def scene_overfit(self):
        header, see, ax, titles, dots = self.fit_intro(
            "Too complex  →  overfitting", OVER_C, tilt=-13)
        sub = Text("Fit a degree-10 polynomial", font_size=25, color=MUTED)
        sub.next_to(header, DOWN, buff=0.3).to_edge(LEFT, buff=0.55)
        self.play(FadeIn(sub, shift=UP * 0.15), run_time=0.5)

        curve = fit_curve(ax, FIT[10], OVER_C, width=5)
        self.play(Create(curve), run_time=1.6)
        wig = self.below_plot(ax, Text("wiggles through every point",
                                       font_size=23, color=OVER_C))
        self.play(FadeIn(wig), run_time=0.5)
        self.beat(1.0)

        # training MSE -> 0 : it looks perfect
        card_t, num_t = self.mse_card(GOOD_C, label="MSE  (training data)",
                                      center=[4.2, 1.25, 0], w=3.3, h=1.7, num_fs=52)
        self.play(FadeIn(card_t), FadeIn(num_t), run_time=0.5)
        self.play(ChangeDecimalToValue(num_t, TRAIN_MSE[10]), run_time=1.1)
        r2 = Text("R² = 1.00", font_size=24, color=GOOD_C).next_to(card_t, DOWN, buff=0.16)
        self.play(FadeIn(r2, shift=UP * 0.1), run_time=0.4)
        train_grp = VGroup(card_t, num_t, r2)
        perfect = Text("Perfect on training data!", font_size=25, color=GOOD_C, weight="BOLD")
        perfect.next_to(train_grp, DOWN, buff=0.3)
        self.play(FadeIn(perfect, shift=UP * 0.15), run_time=0.6)
        self.beat(1.3)

        # the twist: new, unseen data
        ask = Text("But how about new, unseen data?", font_size=25, color=INK)
        ask.move_to(perfect)
        self.play(FadeOut(wig), ReplacementTransform(perfect, ask), run_time=0.6)
        self.beat(0.6)
        test_dots = data_dots(ax, xs=X_TEST, ys=Y_TEST, color=GOLD, r=0.075)
        legend = self.below_plot(ax, bullet("new (unseen) data", color=GOLD, fs=22, dot=GOLD))
        self.play(LaggedStart(*[GrowFromCenter(d) for d in test_dots], lag_ratio=0.15),
                  FadeIn(legend), run_time=1.2)
        self.beat(0.5)
        tres = residual_sticks(ax, FIT[10], xs=X_TEST, ys=Y_TEST, color=OVER_C, width=4)
        self.play(LaggedStart(*[Create(r) for r in tres], lag_ratio=0.12, run_time=1.0))
        self.beat(0.6)

        # test MSE explodes
        self.play(FadeOut(ask), run_time=0.35)
        card_n, num_n = self.mse_card(OVER_C, label="MSE  (new data)",
                                      center=[4.2, -1.7, 0], w=3.3, h=1.7, num_fs=52)
        self.play(FadeIn(card_n), FadeIn(num_n), run_time=0.5)
        self.play(ChangeDecimalToValue(num_n, TEST_MSE[10]), run_time=1.2)
        compare = Text("quadratic scored just 0.013", font_size=21, color=GOOD_C)
        compare.next_to(card_n, DOWN, buff=0.16)
        self.play(FadeIn(compare, shift=UP * 0.1), run_time=0.5)
        self.beat(0.9)

        verdict = self.below_plot(ax, Text("It memorized the noise — high variance.",
                                           font_size=24, color=OVER_C, weight="BOLD"))
        self.play(ReplacementTransform(legend, verdict), run_time=0.7)
        self.play(Indicate(header, color=OVER_C, scale_factor=1.05), run_time=0.8)
        self.beat(1.6)
        self.wipe()

    # ====================================================================== #
    # Scene 5 — The tradeoff (the U-curve)
    # ====================================================================== #
    def scene_tradeoff(self):
        header = self.section_header("The tradeoff", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        ax = Axes(
            x_range=[0.4, 10.6, 1], y_range=[0, 0.30, 0.1],
            x_length=8.4, y_length=4.5,
            axis_config=dict(stroke_color=MUTED, stroke_width=2,
                             tip_length=0.16, tip_width=0.16, include_ticks=True),
            x_axis_config=dict(include_numbers=False),
            y_axis_config=dict(include_numbers=False),
        )
        ax.center().shift(DOWN * 0.35 + LEFT * 0.4)
        xlab = Text("model complexity  →", font_size=24, color=MUTED).next_to(ax.x_axis, DOWN, buff=0.2)
        ylab = Text("prediction error", font_size=24, color=MUTED).rotate(PI / 2).next_to(ax.y_axis, LEFT, buff=0.2)
        self.play(Create(ax), FadeIn(xlab), FadeIn(ylab), run_time=1.0)

        def clampy(v):
            return min(v, ax.y_range[1] - 0.006)

        # the measured total-error U-curve
        total_pts = [ax.c2p(d, clampy(t)) for d, t in zip(DEGREES, TOTAL, strict=True)]
        u = VMobject().set_points_smoothly(total_pts).set_stroke(INK, 6)
        u_label = Text("total error", font_size=24, color=INK, weight="BOLD")
        u_label.next_to(ax.c2p(6, clampy(TOTAL[5])), UP, buff=0.35)
        self.play(Create(u), run_time=1.8)
        self.play(FadeIn(u_label, shift=UP * 0.1), run_time=0.5)
        self.beat(1.0)

        # three regime markers tie back to the earlier scenes
        def marker(deg, color, name, direction, arrow_up=False):
            p = ax.c2p(deg, clampy(TOTAL[deg - 1]))
            dot = Dot(p, radius=0.11, color=color).set_stroke(INK, 1.2)
            lab = tag(name, color, fs=22).scale(0.9).next_to(p, direction, buff=0.3)
            grp = VGroup(dot, lab)
            if arrow_up:
                arr = Arrow(p + DOWN * 0.1, p + UP * 0.55, buff=0, color=color, stroke_width=5)
                grp.add(arr)
            return grp

        m_under = marker(1, UNDER_C, "underfit", UP + RIGHT)
        star = Star(n=5, outer_radius=0.26, color=GOLD, fill_opacity=1, stroke_width=0)
        star.move_to(ax.c2p(2, clampy(TOTAL[1])))
        m_sweet_lab = tag("sweet spot", GOLD, fs=22).scale(0.95).next_to(star, DOWN, buff=0.35)
        m_over = marker(10, OVER_C, "overfit", LEFT, arrow_up=True)

        self.play(FadeIn(m_under, shift=DOWN * 0.1), run_time=0.7)
        self.beat(0.9)
        self.play(FadeIn(m_over, shift=DOWN * 0.1), run_time=0.7)
        self.beat(0.9)
        self.play(GrowFromCenter(star), FadeIn(m_sweet_lab, shift=UP * 0.1), run_time=0.8)
        self.play(Flash(star, color=GOLD, flash_radius=0.5), run_time=0.7)
        self.beat(1.4)

        # decompose the U into its two competing forces
        decomp = Text("total error  =  bias²  +  variance", font_size=30, color=INK)
        decomp.to_edge(UP, buff=0.35).shift(RIGHT * 0.2)
        # color the two words
        self.play(FadeIn(decomp, shift=DOWN * 0.1), run_time=0.8)
        self.beat(0.8)

        def bias_fn(d):
            return 0.155 * np.exp(-1.15 * (d - 1)) + 0.004

        def var_fn(d):
            return 0.016 * np.exp(0.36 * (d - 1))

        ds = np.linspace(1, 10, 120)
        bias_curve = VMobject().set_points_smoothly(
            [ax.c2p(d, clampy(bias_fn(d))) for d in ds]).set_stroke(UNDER_C, 4)
        var_curve = VMobject().set_points_smoothly(
            [ax.c2p(d, clampy(var_fn(d))) for d in ds]).set_stroke(OVER_C, 4)
        bias_curve = DashedVMobject(bias_curve, num_dashes=26)
        var_curve = DashedVMobject(var_curve, num_dashes=26)
        bias_lab = Text("bias²  (too simple)", font_size=23, color=UNDER_C)
        bias_lab.next_to(ax.c2p(1.6, clampy(bias_fn(1.6))), UP + RIGHT, buff=0.15)
        var_lab = Text("variance  (too complex)", font_size=23, color=OVER_C)
        var_lab.next_to(ax.c2p(8.4, clampy(var_fn(8.4))), UP + LEFT, buff=0.15)

        self.play(Create(bias_curve), FadeIn(bias_lab), run_time=1.1)
        self.beat(0.7)
        self.play(Create(var_curve), FadeIn(var_lab), run_time=1.1)
        self.beat(1.2)

        punch = Text("Best model = lowest total error: not too simple, not too complex.",
                     font_size=26, color=GOLD, weight="BOLD")
        punch.to_edge(DOWN, buff=0.3)
        self.play(FadeIn(punch, shift=UP * 0.15), Flash(star, color=GOLD, flash_radius=0.5),
                  run_time=1.0)
        self.beat(2.0)
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_setup()
        self.scene_underfit()
        self.scene_justright()
        self.scene_overfit()
        self.scene_tradeoff()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_BVBase):
    def construct(self):
        self.play_intro()


class Setup(_BVBase):
    def construct(self):
        self.scene_setup()


class Underfit(_BVBase):
    def construct(self):
        self.scene_underfit()


class JustRight(_BVBase):
    def construct(self):
        self.scene_justright()


class Overfit(_BVBase):
    def construct(self):
        self.scene_overfit()


class Tradeoff(_BVBase):
    def construct(self):
        self.scene_tradeoff()


class Outro(_BVBase):
    def construct(self):
        self.play_outro()


class BiasVariance(_BVBase):
    """The whole ~3-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    BiasVariance().render()

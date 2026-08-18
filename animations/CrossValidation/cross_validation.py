"""Cross-Validation — a fast, dynamic ~1-minute demo, house-style.

Four snappy scenes that show *why* a single train/test split lies to you and how
k-fold cross-validation fixes it:

    1. Overfitting   -- a wiggly model memorises the training data, then falls
                        apart on unseen test points (train error ~ 0, test error high)
    2. K-Fold CV     -- rotate the validation fold across the data so every point
                        is tested exactly once; average the fold scores
    3. Why it wins   -- one split gives a jumpy, untrustworthy number; CV gives a
                        tight estimate with a confidence band + the benefits

Bookended by the channel's intro card and the "Thank you for watching!" outro.

Everything uses ``Text`` (Pango) rather than ``Tex`` so it renders without a
LaTeX install and stays fast to iterate on.

Scenes are exposed both individually (``Intro``, ``Overfit``, ``KFold``,
``Payoff``, ``Outro``) and as one continuous film (``CrossValidation``).

Env knobs:
    CV_QUICK=1   shorten every hold for a fast sanity render
"""
from __future__ import annotations

import os
import warnings

import numpy as np
from manim import *

QUICK = os.environ.get("CV_QUICK") == "1"
# Single pacing knob: every reading hold is self.beat(t) == self.wait(t * DELAY).
# Animation run-times are NOT scaled by it, so the piece still feels dynamic —
# DELAY only sets how long text lingers so you can read it. QUICK collapses the
# holds entirely for iteration.
DELAY = 0.25 if QUICK else 1.5

# ---- palette -------------------------------------------------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / axes
GOOD = "#3DD68C"        # generalising model / pass (green)
BAD = "#FF5C5C"         # overfit model / errors (red)
ACCENT = "#FFD166"      # highlights / CV result (gold)
TRAIN_C = "#5B8DEF"     # training folds (blue)
VAL_C = "#FF8C42"       # validation fold (orange)


# ========================================================================== #
# Shared, deterministic data + fitted models (numpy only — no LaTeX, no scipy)
# ========================================================================== #
def _true_f(x):
    """The hidden signal the data is drawn from."""
    return 1.5 * np.sin(0.95 * x) + 0.12 * x


# Seed / noise chosen so the interpolating (overfit) polynomial genuinely
# generalises worse: it threads the noisy training points (train err == 0) but
# wiggles across the whole range and misses the cleaner test points (test err
# high), while the degree-3 model stays consistent train-to-test. The test set
# is drawn a little cleaner so the overfit model's failure is unambiguous.
_rng = np.random.default_rng(2)
X_TRAIN = np.array([0.35, 0.95, 1.55, 2.15, 2.85, 3.55, 4.15, 4.85, 5.55])
Y_TRAIN = _true_f(X_TRAIN) + _rng.normal(0, 0.8, size=X_TRAIN.size)
X_TEST = np.array([0.65, 1.25, 1.9, 2.5, 3.2, 3.85, 4.5, 5.2])
Y_TEST = _true_f(X_TEST) + _rng.normal(0, 0.56, size=X_TEST.size)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    # Exact interpolation through every training point -> train error == 0
    # (the textbook overfit). And a gentle degree-3 fit that generalises.
    _OVERFIT_COEFS = np.polyfit(X_TRAIN, Y_TRAIN, X_TRAIN.size - 1)
    _GOOD_COEFS = np.polyfit(X_TRAIN, Y_TRAIN, 3)


def overfit_fn(x):
    # Clip only catches extreme edge excursions so a stray spike can't streak
    # off-screen; the interior wiggle (the whole point) stays visible.
    return float(np.clip(np.polyval(_OVERFIT_COEFS, x), -4.5, 4.5))


def good_fn(x):
    return float(np.polyval(_GOOD_COEFS, x))


def _rmse(y, yhat):
    return float(np.sqrt(np.mean((y - yhat) ** 2)))


OF_TRAIN = _rmse(Y_TRAIN, np.polyval(_OVERFIT_COEFS, X_TRAIN))   # ~0.00
OF_TEST = _rmse(Y_TEST, np.polyval(_OVERFIT_COEFS, X_TEST))      # large
GD_TRAIN = _rmse(Y_TRAIN, np.polyval(_GOOD_COEFS, X_TRAIN))
GD_TEST = _rmse(Y_TEST, np.polyval(_GOOD_COEFS, X_TEST))

# Illustrative per-fold validation scores for the k-fold scene (R²-like).
FOLD_SCORES = [0.70, 0.75, 0.69, 0.73, 0.74]
CV_MEAN = float(np.mean(FOLD_SCORES))
CV_STD = float(np.std(FOLD_SCORES))


# ---- small reusable pieces ------------------------------------------------ #
def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])]
    )
    v.set_stroke(color=color, width=sw)
    return v.scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.18, -0.18, 0], [0.18, 0.18, 0])
    b = Line([-0.18, 0.18, 0], [0.18, -0.18, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


def line_swatch(color, text, fs=22):
    ln = Line(LEFT * 0.24, RIGHT * 0.24, color=color, stroke_width=6)
    t = Text(text, font_size=fs, color=INK).next_to(ln, RIGHT, buff=0.18)
    return VGroup(ln, t)


def chip(text, color, fs=24, fill=0.14, w=None, h=0.6, tcolor=None):
    label = Text(text, font_size=fs, color=tcolor or INK)
    width = (label.width + 0.5) if w is None else w
    box = RoundedRectangle(
        width=width, height=h, corner_radius=0.12,
        stroke_color=color, stroke_width=2.5,
        fill_color=color, fill_opacity=fill,
    )
    label.move_to(box)
    return VGroup(box, label)


# ========================================================================== #
class _CVBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # ---- timing helpers --------------------------------------------------- #
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.25 if QUICK else 1.0))

    def wipe(self, rt=0.6):
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    def section_header(self, index, label, color):
        tag = Text(f"{index}", font_size=30, color=color, weight="BOLD")
        box = RoundedRectangle(width=0.62, height=0.62, corner_radius=0.12,
                               stroke_color=color, stroke_width=3, fill_opacity=0)
        tag.move_to(box)
        txt = Text(label, font_size=34, color=INK, weight="BOLD")
        grp = VGroup(VGroup(box, tag), txt).arrange(RIGHT, buff=0.28)
        grp.to_corner(UL, buff=0.5)
        line = Line(grp.get_left(), grp.get_right()).next_to(grp, DOWN, buff=0.14)
        line.set_stroke(color=color, width=3)
        return VGroup(grp, line)

    # ---- house-style bookend cards ---------------------------------------- #
    def _card(self, title, subtitle=None):
        header = Text(title, font_size=54, color=INK, weight="BOLD")
        header.set(width=min(10.0, header.width))
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=ACCENT)
        writer = Text("Created by Ptolémé", font_size=28, color=TRAIN_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.3)
        self.card_wait(0.5)
        if subtitle:
            sub = Text(subtitle, font_size=34, color=MUTED)
            sub.move_to(header)
            self.play(Transform(header, sub), run_time=0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.8)
        self.card_wait(1.4)
        return VGroup(header, writer, line)

    def play_intro(self):
        grp = self._card("Cross-Validation", "Why one split lies to you")
        self.play(FadeOut(grp), run_time=0.8)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.4)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=ACCENT)
        writer = Text("Created by Ptolémé", font_size=28, color=TRAIN_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.2)
        self.card_wait(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.card_wait(1.8)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.0)
        self.card_wait(0.4)

    # ====================================================================== #
    # Scene 1 — Overfitting
    # ====================================================================== #
    def scene_overfit(self):
        head = self.section_header("1", "Overfitting", BAD)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.6)

        axes = Axes(
            x_range=[0, 6, 1], y_range=[-4, 4, 2],
            x_length=8.8, y_length=4.5, tips=False,
            axis_config={"include_numbers": False, "include_ticks": False,
                         "stroke_color": MUTED, "stroke_width": 2},
        )
        axes.to_edge(DOWN, buff=0.55).shift(LEFT * 0.6)
        xlab = Text("input", font_size=20, color=MUTED).next_to(axes.x_axis.get_right(), DOWN, buff=0.15)
        ylab = Text("target", font_size=20, color=MUTED).next_to(axes.y_axis.get_top(), UP, buff=0.12)
        self.play(Create(axes), FadeIn(xlab), FadeIn(ylab), run_time=0.7)

        # --- training data --------------------------------------------------- #
        cap = Text("We fit a model to the training data…", font_size=25, color=INK)
        cap.next_to(head, DOWN, buff=0.2).to_edge(LEFT, buff=0.5)
        self.play(FadeIn(cap, shift=UP * 0.15), run_time=0.4)
        train_dots = VGroup(*[
            Dot(axes.c2p(x, y), radius=0.07, color=INK, stroke_width=1.5, stroke_color=BG)
            for x, y in zip(X_TRAIN, Y_TRAIN)
        ])
        self.play(LaggedStart(*[GrowFromCenter(d) for d in train_dots],
                              lag_ratio=0.15, run_time=1.1))
        self.beat(0.5)

        # --- the two candidate models --------------------------------------- #
        good_curve = axes.plot(good_fn, x_range=[0.2, 5.72, 0.03], color=GOOD, stroke_width=5)
        overfit_curve = axes.plot(overfit_fn, x_range=[0.33, 5.57, 0.012], color=BAD, stroke_width=5)

        legend = VGroup(
            line_swatch(BAD, "overfit — threads every point"),
            line_swatch(GOOD, "simple — follows the trend"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        legend.to_corner(UR, buff=0.5).shift(DOWN * 0.1)

        self.play(Create(overfit_curve), FadeIn(legend[0], shift=LEFT * 0.2), run_time=1.2)
        self.beat(0.5)
        # train error ~ 0 badge (the trap)
        trap = chip(f"training error ≈ {OF_TRAIN:.2f}", BAD, fs=22).move_to(
            axes.c2p(4.55, -3.1)
        )
        self.play(FadeIn(trap, scale=0.85), run_time=0.5)
        self.beat(0.8)
        self.play(Create(good_curve), FadeIn(legend[1], shift=LEFT * 0.2), run_time=1.0)
        self.beat(0.6)

        # --- the reveal: unseen test points --------------------------------- #
        cap2 = Text("…then unseen test data arrives.", font_size=25, color=ACCENT)
        cap2.move_to(cap, aligned_edge=LEFT)
        self.play(FadeOut(cap, shift=UP * 0.15), FadeIn(cap2, shift=UP * 0.15), run_time=0.5)
        test_dots = VGroup(*[
            Dot(axes.c2p(x, y), radius=0.08, color=ACCENT, stroke_width=1.5, stroke_color=BG)
            for x, y in zip(X_TEST, Y_TEST)
        ])
        self.play(LaggedStart(*[GrowFromCenter(d) for d in test_dots],
                              lag_ratio=0.12, run_time=1.0))
        self.beat(0.4)

        # residuals from the test points to the overfit curve — big red misses
        resid = VGroup(*[
            DashedLine(axes.c2p(x, y), axes.c2p(x, overfit_fn(x)),
                       color=BAD, stroke_width=2.5, dash_length=0.09)
            for x, y in zip(X_TEST, Y_TEST)
        ])
        self.play(LaggedStart(*[Create(r) for r in resid], lag_ratio=0.1, run_time=1.0))
        self.play(FadeOut(trap), run_time=0.3)

        # error scoreboard
        board = VGroup(
            VGroup(chip("overfit", BAD, fs=20, w=1.9),
                   Text(f"test error {OF_TEST:.2f}", font_size=22, color=BAD),
                   make_cross(scale=0.8)).arrange(RIGHT, buff=0.25),
            VGroup(chip("simple", GOOD, fs=20, w=1.9),
                   Text(f"test error {GD_TEST:.2f}", font_size=22, color=GOOD),
                   make_tick(scale=0.8)).arrange(RIGHT, buff=0.25),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        board.move_to(axes.c2p(3.9, 2.9)).align_to(axes.c2p(2.2, 0), LEFT)
        self.play(FadeIn(board[0], shift=LEFT * 0.2), run_time=0.6)
        self.beat(0.6)
        self.play(FadeIn(board[1], shift=LEFT * 0.2), run_time=0.6)
        self.beat(0.7)

        punch = Text("Perfect on training, lost on new data — that's overfitting.",
                     font_size=26, color=INK).to_edge(DOWN, buff=0.28)
        self.play(Write(punch), run_time=1.1)
        self.play(Circumscribe(punch, color=BAD, run_time=1.2))
        self.beat(1.0)
        self.wipe()

    # ====================================================================== #
    # Scene 2 — K-Fold Cross-Validation
    # ====================================================================== #
    def _fold_row(self, val_index, k=5, bw=1.02, bh=0.5, buff=0.13):
        blocks = VGroup()
        for j in range(k):
            is_val = j == val_index
            color = VAL_C if is_val else TRAIN_C
            r = RoundedRectangle(width=bw, height=bh, corner_radius=0.09,
                                 stroke_width=2, stroke_color=color,
                                 fill_color=color, fill_opacity=0.9 if is_val else 0.22)
            blocks.add(r)
        blocks.arrange(RIGHT, buff=buff)
        return blocks

    def scene_kfold(self):
        head = self.section_header("2", "K-Fold Cross-Validation", TRAIN_C)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.6)
        sub = Text("Split the data into K = 5 folds — rotate which one is held out",
                   font_size=25, color=MUTED)
        sub.next_to(head, DOWN, buff=0.25).to_edge(LEFT, buff=0.5)
        self.play(FadeIn(sub, shift=UP * 0.15), run_time=0.5)
        self.beat(0.4)

        # legend for the block colours
        leg = VGroup(
            VGroup(RoundedRectangle(width=0.42, height=0.34, corner_radius=0.07,
                                    stroke_color=TRAIN_C, stroke_width=2,
                                    fill_color=TRAIN_C, fill_opacity=0.22),
                   Text("train", font_size=20, color=INK)).arrange(RIGHT, buff=0.16),
            VGroup(RoundedRectangle(width=0.42, height=0.34, corner_radius=0.07,
                                    stroke_color=VAL_C, stroke_width=2,
                                    fill_color=VAL_C, fill_opacity=0.9),
                   Text("validation", font_size=20, color=INK)).arrange(RIGHT, buff=0.16),
        ).arrange(RIGHT, buff=0.6).to_edge(UP, buff=0.55).to_edge(RIGHT, buff=0.7)
        self.play(FadeIn(leg), run_time=0.5)

        # five stacked fold-rows, validation block sweeping left -> right
        rows = VGroup(*[self._fold_row(i) for i in range(5)])
        rows.arrange(DOWN, buff=0.28).move_to([-1.9, -0.5, 0])
        round_labels = VGroup(*[
            Text(f"round {i+1}", font_size=20, color=MUTED).next_to(rows[i], LEFT, buff=0.35)
            for i in range(5)
        ])
        score_labels = VGroup(*[
            Text(f"{s:.2f}", font_size=26, color=ACCENT, weight="BOLD").next_to(rows[i], RIGHT, buff=0.5)
            for i, s in enumerate(FOLD_SCORES)
        ])
        arrows = VGroup(*[
            Arrow(rows[i].get_right(), score_labels[i].get_left(), buff=0.15,
                  stroke_width=3, color=MUTED, max_tip_length_to_length_ratio=0.4, tip_length=0.14)
            for i in range(5)
        ])

        for i in range(5):
            self.play(
                FadeIn(round_labels[i], shift=RIGHT * 0.15),
                LaggedStart(*[FadeIn(b, scale=0.8) for b in rows[i]], lag_ratio=0.08),
                run_time=0.55,
            )
            self.play(GrowArrow(arrows[i]), FadeIn(score_labels[i], shift=LEFT * 0.15), run_time=0.4)
            self.beat(0.2)

        # every point tested once — sweep highlight down the validation column
        note = Text("every point is validated exactly once", font_size=23, color=GOOD)
        note.next_to(rows, DOWN, buff=0.4)
        self.play(FadeIn(note, shift=UP * 0.15), run_time=0.5)
        self.beat(0.5)

        # collapse the fold scores into a single averaged estimate
        brace = Brace(score_labels, RIGHT, color=MUTED)
        cv = VGroup(
            Text("CV score", font_size=24, color=MUTED),
            Text(f"{CV_MEAN:.2f} ± {CV_STD:.2f}", font_size=40, color=ACCENT, weight="BOLD"),
        ).arrange(DOWN, buff=0.12)
        cv.next_to(brace, RIGHT, buff=0.3)
        self.play(GrowFromCenter(brace), run_time=0.5)
        self.play(FadeIn(cv, shift=RIGHT * 0.2), run_time=0.6)
        self.play(Circumscribe(cv[1], color=ACCENT, run_time=1.1))
        self.beat(1.0)
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Why it wins
    # ====================================================================== #
    def scene_payoff(self):
        head = self.section_header("3", "Why it wins", GOOD)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.6)

        # --- reliability comparison: one split vs 5-fold CV ----------------- #
        base_y = -1.9
        scale = 3.0

        def sy(s):
            return base_y + s * scale

        yaxis = Line([-4.6, base_y, 0], [-4.6, sy(1.0) + 0.2, 0]).set_stroke(MUTED, 2)
        y_top = Text("1.0", font_size=18, color=MUTED).next_to(yaxis.get_top(), LEFT, buff=0.12)
        y_bot = Text("0", font_size=18, color=MUTED).next_to([-4.6, base_y, 0], LEFT, buff=0.12)
        y_name = Text("score", font_size=19, color=MUTED).rotate(PI / 2).next_to(yaxis, LEFT, buff=0.5)
        self.play(Create(yaxis), FadeIn(y_top), FadeIn(y_bot), FadeIn(y_name), run_time=0.6)

        def bar_with_whisker(x, s, err, color, label, sub):
            bar = Rectangle(width=1.05, height=s * scale, stroke_width=0,
                            fill_color=color, fill_opacity=0.85)
            bar.move_to([x, base_y + s * scale / 2, 0])
            whisker = VGroup(
                Line([x, sy(s - err), 0], [x, sy(s + err), 0]),
                Line([x - 0.2, sy(s + err), 0], [x + 0.2, sy(s + err), 0]),
                Line([x - 0.2, sy(s - err), 0], [x - 0 + 0.2, sy(s - err), 0]),
            ).set_stroke(INK, 3)
            name = Text(label, font_size=22, color=INK, weight="BOLD").next_to(bar, DOWN, buff=0.18)
            tag = Text(sub, font_size=18, color=color).next_to(name, DOWN, buff=0.1)
            return VGroup(bar, whisker, name, tag)

        one = bar_with_whisker(-3.0, 0.71, 0.15, BAD, "1 split", "± 0.15  jumpy")
        cv = bar_with_whisker(-1.2, CV_MEAN, CV_STD, GOOD, "5-fold CV", f"± {CV_STD:.2f}  steady")

        self.play(GrowFromEdge(one[0], DOWN), FadeIn(one[2]), FadeIn(one[3]), run_time=0.7)
        self.play(Create(one[1]), run_time=0.5)
        self.beat(0.5)
        # jitter the single-split estimate to show how much it can swing
        jitter = Text("could be 0.56 … 0.86", font_size=20, color=BAD, slant=ITALIC)
        jitter.next_to(one[1], UP, buff=0.18)  # sit above the whisker cap, not on it
        self.play(FadeIn(jitter, shift=UP * 0.1), run_time=0.4)
        self.play(Indicate(one[1], color=BAD, scale_factor=1.15), run_time=0.6)
        self.beat(0.3)

        self.play(GrowFromEdge(cv[0], DOWN), FadeIn(cv[2]), FadeIn(cv[3]), run_time=0.7)
        self.play(Create(cv[1]), run_time=0.5)
        self.play(Indicate(cv[0], color=GOOD, scale_factor=1.06), run_time=0.6)
        self.beat(0.6)

        illus = Text("illustrative", font_size=16, color=MUTED, slant=ITALIC)
        illus.next_to(yaxis, UP, buff=0.1).shift(RIGHT * 0.55)
        self.play(FadeIn(illus), run_time=0.3)

        # --- the benefits list ---------------------------------------------- #
        benefits = [
            "Uses all the data — train and validate",
            "Every point is tested exactly once",
            "Reports a confidence band, not one number",
            "Exposes overfitting before deployment",
            "Fair, low-variance model selection",
        ]
        rows = VGroup()
        for b in benefits:
            tx = Text(b, font_size=21, color=INK)
            tk = make_tick(scale=0.7).next_to(tx, LEFT, buff=0.22)
            rows.add(VGroup(tk, tx))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.3).to_edge(RIGHT, buff=0.7).shift(UP * 0.15)
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.2) for r in rows],
                              lag_ratio=0.35, run_time=2.0))
        self.beat(0.6)

        punch = Text("Cross-validation turns a lucky score into a trustworthy one.",
                     font_size=26, color=INK, weight="BOLD").to_edge(DOWN, buff=0.3)
        self.play(Write(punch), run_time=1.2)
        self.play(Circumscribe(punch, color=ACCENT, run_time=1.2))
        self.beat(1.2)
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_overfit()
        self.scene_kfold()
        self.scene_payoff()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_CVBase):
    def construct(self):
        self.play_intro()


class Overfit(_CVBase):
    def construct(self):
        self.scene_overfit()


class KFold(_CVBase):
    def construct(self):
        self.scene_kfold()


class Payoff(_CVBase):
    def construct(self):
        self.scene_payoff()


class Outro(_CVBase):
    def construct(self):
        self.play_outro()


class CrossValidation(_CVBase):
    """The whole ~1-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    CrossValidation().render()

"""Cross-Entropy — a short, house-style explainer.

A self-explanatory (no voice-over) film that answers two questions: what is the
cross-entropy loss, and why is it the right way to score a probabilistic
prediction? It builds from one concrete 3-class example, and ends on a genuine
3D payoff (gradient descent down the convex loss bowl):

    1. Setup     -- a classifier outputs a *distribution* (cat 0.70, dog 0.20,
                    bird 0.10); the truth is one class. How wrong is this?
    2. Formula   -- H(p, q) = -Σ p(x) log q(x). With a one-hot label the sum
                    collapses to  L = -log q(true): the negative log-likelihood
                    of the correct class.
    3. Surprise  -- plot L = -ln q. Confident-and-right -> ~0; confident-and-wrong
                    -> infinity. Cross-entropy is your average surprise at the truth.
    4. Gradient  -- softmax + cross-entropy gives  dL/dz = q - p  (prediction minus
                    target). Simple, and it never saturates, so training stays fast.
    5. Descent   -- **3D**: the cross-entropy loss over a model's two parameters is
                    a single convex bowl. A ball runs gradient descent straight to
                    the global minimum while the camera orbits the bowl. This is the
                    one scene where camera movement earns its keep: it shows a real
                    3D object from every side.
    6. Honest    -- H(p, q) = H(p) + KL(p || q). H(p) is fixed, so minimising
                    cross-entropy = minimising KL(p || q), which is 0 only when
                    q = p. A proper scoring rule: you can't win by hedging.
    7. Recap     -- one card: what it is and why we use it.

Camera policy (learned the hard way): the 2D scenes use a **static camera** —
zooming into a flat formula or number adds nothing. Camera control is reserved
for the one real `ThreeDScene` (Descent), where orbiting reveals the shape of the
loss bowl. See the memory note `camera-control-only-for-3d`.

Everything text is `Text` (Pango), never `Tex` — no LaTeX toolchain. Every number
comes from one source of truth: the softmax [0.70, 0.20, 0.10] from `LOGITS`, the
loss -ln 0.70, the gradient q - p, and the 3D bowl is a real logistic-regression
cross-entropy surface (`ce_loss`) with a real gradient-descent path (`CE_PATH`).

Scenes render individually (`Setup`, `Formula`, `Surprise`, `Gradient`,
`Descent`, `Honest`, `Recap`, `Intro`, `Outro`); the whole film is the stitch of
them in order (`./render.sh full` / `--stitch`).

Env knobs:
    XCE_QUICK=1   shorten every hold for a fast sanity render
    XCE_DELAY=x   override the reading-hold multiplier
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

# ---- crisp text: render big, scale down (Pango mangles small sizes) ------- #
# MANDATORY shadow (manim-explainer SKILL §2).
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("XCE_QUICK") == "1"
DELAY = float(os.environ.get("XCE_DELAY", "0.3" if QUICK else "1.95"))
END_HOLD = 0.2 if QUICK else 1.8

# ---- palette (shared house style) ---------------------------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / axes
GRID = "#232A38"        # faint gridlines / panel fills
FAINT = "#3A4152"       # guides

TRUE_C = "#3DD68C"      # the true class / target distribution p (green)
PRED_C = "#5B8DEF"      # the predicted distribution q (blue)
LOSS_C = "#FF8C42"      # the loss / "surprise" (orange)
GOLD = "#FFD166"        # formula highlight / the underline rule
BAD = "#FF5C5C"         # confidently wrong (red)
KL_C = "#C792EA"        # KL divergence / information (violet)


# ---- the running example (one source of truth for every number) ----------- #
CLASSES = ["cat", "dog", "bird"]
LOGITS = np.array([1.9459, 0.6931, 0.0])       # chosen so softmax == [.70,.20,.10]


def _softmax(z):
    e = np.exp(z - z.max())
    return e / e.sum()


Q = _softmax(LOGITS)                # predicted distribution  ~ [0.70, 0.20, 0.10]
P = np.array([1.0, 0.0, 0.0])       # true (one-hot) distribution: class "cat"
TRUE_IDX = 0
GRAD = Q - P                        # softmax+CE gradient wrt logits = q - p
CE = float(-np.log(Q[TRUE_IDX]))    # cross-entropy loss = -ln(0.70) = 0.357
assert [f"{x:.2f}" for x in Q] == ["0.70", "0.20", "0.10"], Q
assert [f"{x:.2f}" for x in GRAD] == ["-0.30", "0.20", "0.10"], GRAD
assert f"{CE:.2f}" == "0.36", CE


# ---- the 3D bowl: a real logistic-regression cross-entropy surface --------- #
# tiny, deliberately non-separable data so the loss has a finite, interior,
# convex minimum (a clean bowl). L(w, b) is the mean binary cross-entropy of a
# 1-feature logistic model; gradient descent on it gives CE_PATH.
CE_XS = np.array([-2.2, -1.5, -0.9, -0.3, 0.3, 0.9, 1.5, 2.2])
CE_YS = np.array([0, 0, 1, 0, 1, 0, 1, 1], dtype=float)


def _sig(z):
    return 1.0 / (1.0 + np.exp(-z))


def ce_loss(w, b):
    q = np.clip(_sig(w * CE_XS + b), 1e-9, 1 - 1e-9)
    return float(np.mean(-(CE_YS * np.log(q) + (1 - CE_YS) * np.log(1 - q))))


def _ce_grad(w, b):
    e = _sig(w * CE_XS + b) - CE_YS
    return float(np.mean(e * CE_XS)), float(np.mean(e))


def _descent_path(w0, b0, lr=0.9, steps=26):
    w, b = w0, b0
    path = [(w, b)]
    for _ in range(steps):
        gw, gb = _ce_grad(w, b)
        w -= lr * gw
        b -= lr * gb
        path.append((w, b))
    return path


CE_PATH = _descent_path(-2.6, 3.0)        # start high on the bowl, roll to the min
_wg = np.linspace(-3, 4, 80)
_bg = np.linspace(-3.5, 3.5, 80)
_grid = np.array([[ce_loss(w, b) for w in _wg] for b in _bg])
_i, _j = np.unravel_index(_grid.argmin(), _grid.shape)
CE_MIN = (float(_wg[_j]), float(_bg[_i]))  # global minimum of the bowl
# surface height range, used to place the camera / colour scale
CE_ZMIN, CE_ZMAX = float(_grid.min()), float(_grid.max())


# ========================================================================== #
# Small reusable pieces
# ========================================================================== #
def bullet(text, color=INK, fs=23, dot=GOLD, dot_r=0.055):
    d = Dot(radius=dot_r, color=dot)
    t = Text(text, font_size=fs, color=color)
    t.next_to(d, RIGHT, buff=0.22)
    d.align_to(t, UP).shift(DOWN * 0.11)
    return VGroup(d, t)


class DistBars(VGroup):
    """A horizontal probability bar chart with left-aligned tracks."""

    def __init__(self, probs, labels, colors=None, unit=3.6, bar_h=0.46,
                 gap=0.30, val_fs=22, lab_fs=24, **kw):
        super().__init__(**kw)
        self.unit, self.bar_h = unit, bar_h
        colors = colors or [PRED_C] * len(probs)
        self.colors = colors
        self.tracks, self.fills, self.vals, self.labels = [], [], [], []
        for i, (p, lab, col) in enumerate(zip(probs, labels, colors)):
            y = -i * (bar_h + gap)
            track = RoundedRectangle(width=unit, height=bar_h, corner_radius=bar_h / 2,
                                     stroke_color=GRID, stroke_width=1.5,
                                     fill_color=GRID, fill_opacity=0.55)
            track.move_to([0, y, 0])
            fill = self._mk_fill(p, col, track)
            lb = Text(lab, font_size=lab_fs, color=INK)
            lb.next_to(track, LEFT, buff=0.28)
            vl = Text(f"{p:.2f}", font_size=val_fs, color=col, weight=BOLD)
            vl.next_to(track, RIGHT, buff=0.24)
            self.tracks.append(track)
            self.fills.append(fill)
            self.vals.append(vl)
            self.labels.append(lb)
            self.add(track, fill, lb, vl)

    def _mk_fill(self, p, col, track):
        w = max(self.bar_h, self.unit * float(p))
        fill = RoundedRectangle(width=w, height=self.bar_h, corner_radius=self.bar_h / 2,
                                stroke_width=0, fill_color=col, fill_opacity=1.0)
        fill.align_to(track, LEFT).set_y(track.get_y())
        return fill

    def retarget(self, i, p):
        col = self.colors[i]
        new_fill = self._mk_fill(p, col, self.tracks[i])
        new_val = Text(f"{p:.2f}", font_size=22, color=col, weight=BOLD)
        new_val.next_to(self.tracks[i], RIGHT, buff=0.24)
        return AnimationGroup(Transform(self.fills[i], new_fill),
                              Transform(self.vals[i], new_val))


# ========================================================================== #
# Shared helpers (no camera control — that lives only in the 3D scene)
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

    def say(self, text, color=INK, fs=25, y=-3.4, weight=NORMAL):
        cap = Text(text, font_size=fs, color=color, weight=weight)
        if cap.width > 12.6:
            cap.scale_to_fit_width(12.6)
        cap.move_to([0, y, 0])
        return cap

    def clamp_w(self, mob, w=6.6):
        if mob.width > w:
            mob.scale_to_fit_width(w)
        return mob


# ========================================================================== #
class _CEBase(_Common, Scene):
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
        writer = Text("Created by Ptolémé", font_size=28, color=PRED_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        sub = Text(title2, font_size=32, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.card_wait(2.0)
        return VGroup(header, writer, line)

    def play_intro(self):
        group = self.introduction(
            "Cross-Entropy",
            "How we score a prediction, and why it is the right loss",
        )
        self.play(FadeOut(group), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=PRED_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.5)
        self.card_wait(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.1)
        self.card_wait(2.2)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 — a prediction is a distribution
    # ====================================================================== #
    def scene_setup(self):
        header = self.section_header("A prediction is a distribution", INK)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        model = RoundedRectangle(width=1.9, height=1.25, corner_radius=0.14,
                                 stroke_color=MUTED, stroke_width=2.5,
                                 fill_color=GRID, fill_opacity=0.5)
        model.move_to([-4.6, 0.3, 0])
        mlab = Text("model", font_size=24, color=INK).move_to(model)
        img = Text("photo", font_size=19, color=MUTED)
        img.next_to(model, UP, buff=0.28)
        self.play(FadeIn(model, mlab), FadeIn(img, shift=DOWN * 0.1), run_time=0.7)

        bars = DistBars([0.70, 0.20, 0.10], CLASSES, unit=3.6)
        bars.move_to([1.5, 0.3, 0])
        arrow = Arrow(model.get_right(), bars.get_left() + LEFT * 0.2,
                      buff=0.22, color=MUTED, stroke_width=4,
                      max_tip_length_to_length_ratio=0.16)

        cap1 = self.say("A classifier does not pick one answer. It gives a "
                        "probability to every class.", color=MUTED)
        self.play(GrowArrow(arrow),
                  FadeIn(VGroup(*bars.tracks)), FadeIn(*bars.labels),
                  LaggedStart(*[GrowFromEdge(f, LEFT) for f in bars.fills], lag_ratio=0.15),
                  run_time=1.3)
        self.play(LaggedStart(*[FadeIn(v, shift=LEFT * 0.1) for v in bars.vals],
                              lag_ratio=0.15), FadeIn(cap1, shift=UP * 0.1), run_time=0.9)
        self.beat(1.6)

        summ = Text("0.70 + 0.20 + 0.10  =  1.00", font_size=22, color=INK)
        summ.next_to(bars, DOWN, buff=0.55)
        self.play(FadeIn(summ, shift=UP * 0.1), run_time=0.6)
        self.beat(1.2)

        ring = SurroundingRectangle(VGroup(bars.labels[0], bars.tracks[0], bars.vals[0]),
                                    color=TRUE_C, buff=0.12, corner_radius=0.12).set_stroke(width=4)
        tlab = Text("true label", font_size=20, color=TRUE_C, weight=BOLD)
        tlab.next_to(ring, UP, buff=0.14).align_to(ring, RIGHT)
        cap2 = self.say("Here the true label is cat, and the model gave it "
                        "probability 0.70.", color=TRUE_C)
        self.play(Create(ring), FadeIn(tlab, shift=DOWN * 0.1),
                  ReplacementTransform(cap1, cap2), run_time=0.9)
        self.play(Indicate(VGroup(bars.fills[0], bars.vals[0]), color=TRUE_C,
                           scale_factor=1.12), run_time=0.9)
        self.beat(1.4)

        cap3 = self.say("How wrong is this guess? Cross-entropy turns it into a "
                        "single number.", color=INK, weight=BOLD)
        self.play(ReplacementTransform(cap2, cap3), run_time=0.7)
        self.beat(1.6)
        self.wipe()

    # ====================================================================== #
    # Scene 2 — the formula, and how it collapses
    # ====================================================================== #
    def scene_formula(self):
        header = self.section_header("The formula", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        gen = Text("H(p, q)  =  − Σ p(x) log q(x)", font_size=42,
                   t2c={"p": TRUE_C, "q": PRED_C})
        gen.move_to([0, 2.0, 0])
        self.play(Write(gen), run_time=1.4)
        cap = self.say("Cross-entropy compares the true distribution p with the "
                       "prediction q.", color=MUTED)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.6)
        self.play(Circumscribe(gen, color=GOLD, buff=0.18, run_time=1.4))
        self.beat(1.2)

        oneh = VGroup(
            Text("For one label the truth is one-hot: ", font_size=30),
            Text("p = (1, 0, 0)", font_size=30, color=TRUE_C),
        ).arrange(RIGHT, buff=0.18).move_to([0, 1.0, 0])
        cap2 = self.say("It is 1 for the correct class and 0 for every other class.",
                        color=TRUE_C)
        self.play(FadeIn(oneh, shift=UP * 0.1), ReplacementTransform(cap, cap2),
                  run_time=0.9)
        self.beat(1.6)

        L0 = Text("L  =  −[", font_size=34)
        t1 = VGroup(Text("1", font_size=34, color=TRUE_C),
                    Text("· log 0.70", font_size=34)).arrange(RIGHT, buff=0.06, aligned_edge=DOWN)
        plus1 = Text("+", font_size=34)
        t2 = VGroup(Text("0", font_size=34, color=MUTED),
                    Text("· log 0.20", font_size=34, color=MUTED)).arrange(RIGHT, buff=0.06, aligned_edge=DOWN)
        plus2 = Text("+", font_size=34)
        t3 = VGroup(Text("0", font_size=34, color=MUTED),
                    Text("· log 0.10", font_size=34, color=MUTED)).arrange(RIGHT, buff=0.06, aligned_edge=DOWN)
        R0 = Text("]", font_size=34)
        expand = VGroup(L0, t1, plus1, t2, plus2, t3, R0).arrange(RIGHT, buff=0.16, aligned_edge=DOWN)
        expand.move_to([0, -0.5, 0])
        cap3 = self.say("Write the sum out. Every wrong class is multiplied by 0, "
                        "so it drops away.", color=INK)
        self.play(FadeIn(expand, shift=UP * 0.1), ReplacementTransform(cap2, cap3),
                  run_time=1.0)
        self.beat(1.6)

        strikes = VGroup(
            Line(t2.get_left(), t2.get_right(), color=BAD, stroke_width=4),
            Line(t3.get_left(), t3.get_right(), color=BAD, stroke_width=4),
        )
        self.play(Create(strikes), run_time=0.6)
        self.play(FadeOut(t2, plus2, t3, plus1, strikes),
                  t1[0].animate.set_opacity(0.0),      # the "1·" is identity
                  run_time=0.8)
        self.beat(0.5)

        collapsed = VGroup(
            Text("L  =  − log 0.70  =  ", font_size=40),
            Text("0.36", font_size=40, color=LOSS_C, weight=BOLD),
        ).arrange(RIGHT, buff=0.14).move_to([0, -0.5, 0])
        self.play(FadeOut(L0, R0, t1), FadeIn(collapsed), run_time=0.7)
        self.beat(1.4)

        rule = Text("L  =  − log q(true)", font_size=44, weight=BOLD,
                    t2c={"q": PRED_C})
        rule.move_to([0, -0.5, 0])
        under = Line(rule.get_left() + DOWN * 0.35, rule.get_right() + DOWN * 0.35,
                     ).set_stroke(GOLD, 3)
        name = Text("the negative log-likelihood of the correct class",
                    font_size=24, color=MUTED, slant=ITALIC)
        name.next_to(under, DOWN, buff=0.22)
        cap4 = self.say("Cross-entropy is the negative log-probability the model "
                        "gave the right answer.", color=INK, weight=BOLD)
        self.play(ReplacementTransform(collapsed, rule), FadeOut(gen, oneh),
                  ReplacementTransform(cap3, cap4), run_time=1.0)
        self.play(Create(under), FadeIn(name, shift=UP * 0.1), run_time=0.8)
        self.beat(2.2)
        self.wipe()

    # ====================================================================== #
    # Scene 3 — the surprise curve: why the log
    # ====================================================================== #
    def scene_surprise(self):
        header = self.section_header("Why the log", LOSS_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        axes = Axes(
            x_range=[0, 1, 0.2], y_range=[0, 5, 1], x_length=8.2, y_length=4.2,
            axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": True,
                         "tip_length": 0.16, "font_size": 20},
            x_axis_config={"numbers_to_include": np.arange(0.2, 1.01, 0.2),
                           "decimal_number_config": {"num_decimal_places": 1}},
            y_axis_config={"numbers_to_include": [1, 2, 3, 4, 5]},
        )
        axes.move_to([0.15, 0.4, 0])
        xlab = Text("q  =  probability given to the true class", font_size=22, color=INK)
        xlab.next_to(axes, DOWN, buff=0.18)
        ylab = Text("loss  =  − ln q", font_size=22, color=LOSS_C, weight=BOLD)
        ylab.next_to(axes.y_axis.get_top(), RIGHT, buff=0.18).shift(DOWN * 0.05)
        self.play(Create(axes), FadeIn(xlab, ylab), run_time=1.2)

        curve = axes.plot(lambda x: -np.log(x), x_range=[np.exp(-5), 1.0, 0.004],
                          color=LOSS_C, stroke_width=4)
        self.play(Create(curve), run_time=1.6)
        self.beat(0.6)

        qv = ValueTracker(0.92)
        dot = always_redraw(lambda: Dot(axes.c2p(qv.get_value(), -np.log(qv.get_value())),
                                        radius=0.10, color=INK, stroke_color=BG, stroke_width=2))
        self.add(dot)
        self.beat(0.4)

        cap = self.say("Predict the truth with high confidence and the loss is "
                       "almost nothing.", color=TRUE_C)
        self.play(qv.animate.set_value(0.70), FadeIn(cap, shift=UP * 0.1), run_time=1.2)
        mk_right = self._mark(axes, 0.70, TRUE_C)
        self.play(FadeIn(mk_right, shift=UP * 0.1), run_time=0.5)
        self.beat(1.6)

        cap2 = self.say("Grow unsure, and the loss climbs.", color=INK)
        self.play(qv.animate.set_value(0.10), ReplacementTransform(cap, cap2), run_time=1.6)
        mk_mid = self._mark(axes, 0.10, LOSS_C)
        self.play(FadeIn(mk_mid), run_time=0.5)
        self.beat(1.4)

        cap3 = self.say("Be confident and wrong, and the loss runs off toward "
                        "infinity.", color=BAD, weight=BOLD)
        self.play(qv.animate.set_value(np.exp(-4.6)), ReplacementTransform(cap2, cap3),
                  run_time=1.6)
        arrowup = Arrow(axes.c2p(0.05, 3.5), axes.c2p(0.022, 4.85), buff=0.05,
                        color=BAD, stroke_width=5)
        inf = Text("∞", font_size=40, color=BAD).next_to(arrowup.get_end(), RIGHT, buff=0.12)
        self.play(GrowArrow(arrowup), FadeIn(inf), run_time=0.7)
        self.play(Flash(inf, color=BAD, line_length=0.2, num_lines=12), run_time=0.7)
        self.beat(1.4)

        dot.clear_updaters()
        self.play(FadeOut(arrowup, inf, mk_mid, mk_right, cap3, dot), run_time=0.5)
        take = Text("−ln q is your surprise at the truth: confident mistakes are "
                    "punished the hardest.", font_size=25, color=INK, weight=BOLD)
        self.clamp_w(take, 12.4).move_to([0, -3.4, 0])
        self.play(FadeIn(take, shift=UP * 0.1), run_time=0.7)
        self.beat(2.2)
        self.wipe()

    def _mark(self, axes, x, color):
        y = -np.log(x)
        p = axes.c2p(x, y)
        d = Dot(p, radius=0.06, color=color)
        drop = DashedLine(p, axes.c2p(x, 0), color=color, stroke_width=2, dash_length=0.08)
        val = Text(f"{y:.2f}", font_size=20, color=color, weight=BOLD)
        val.next_to(d, UR, buff=0.06)
        return VGroup(drop, d, val)

    # ====================================================================== #
    # Scene 4 — the gradient: q - p, and it never saturates
    # ====================================================================== #
    def scene_gradient(self):
        header = self.section_header("Why training loves it", PRED_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        qbars = DistBars([0.70, 0.20, 0.10], CLASSES,
                         colors=[PRED_C, PRED_C, PRED_C], unit=2.7, lab_fs=22, val_fs=20)
        qbars.move_to([-3.4, 1.0, 0])
        qtitle = Text("prediction  q", font_size=24, color=PRED_C, weight=BOLD)
        qtitle.next_to(qbars, UP, buff=0.35)

        pbars = DistBars([1.0, 0.0, 0.0], CLASSES,
                         colors=[TRUE_C, TRUE_C, TRUE_C], unit=2.7, lab_fs=22, val_fs=20)
        pbars.move_to([3.5, 1.0, 0])
        ptitle = Text("target  p", font_size=24, color=TRUE_C, weight=BOLD)
        ptitle.next_to(pbars, UP, buff=0.35)

        self.play(FadeIn(qbars, shift=RIGHT * 0.1), FadeIn(qtitle), run_time=0.8)
        self.play(FadeIn(pbars, shift=LEFT * 0.1), FadeIn(ptitle), run_time=0.8)
        cap = self.say("Line up the prediction q against the one-hot target p.",
                       color=MUTED)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.5)
        self.beat(1.4)

        grad = Text("∂L / ∂z   =   q  −  p", font_size=40, weight=BOLD,
                    t2c={"q": PRED_C, "p": TRUE_C})
        grad.move_to([0, -1.4, 0])
        self.play(Write(grad), run_time=1.0)
        cap2 = self.say("Softmax and cross-entropy together give a strikingly "
                        "simple gradient.", color=INK)
        self.play(ReplacementTransform(cap, cap2), run_time=0.6)
        self.play(Circumscribe(grad, color=PRED_C, buff=0.18, run_time=1.4))
        self.beat(1.2)

        vals = VGroup()
        for lab, g in zip(CLASSES, GRAD):
            col = TRUE_C if g < 0 else BAD
            sign = "push up" if g < 0 else "push down"
            row = VGroup(
                Text(f"{lab}", font_size=22, color=INK),
                Text(f"{g:+.2f}", font_size=24, color=col, weight=BOLD),
                Text(sign, font_size=19, color=col),
            ).arrange(RIGHT, buff=0.26)
            vals.add(row)
        vals.arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([0, -1.4, 0])
        cap3 = self.say("Each number is how far a class sits from its target: raise "
                        "the truth, lower the rest.", color=INK)
        self.play(ReplacementTransform(grad, vals), ReplacementTransform(cap2, cap3),
                  run_time=1.0)
        self.beat(2.0)

        self.play(FadeOut(qbars, qtitle, pbars, ptitle),
                  vals.animate.move_to([0, 1.7, 0]), run_time=0.8)
        punch = VGroup(
            Text("The signal never saturates.", font_size=30, color=PRED_C, weight=BOLD),
            Text("Even a confidently wrong prediction keeps a large gradient,",
                 font_size=24, color=INK),
            Text("so learning stays fast where squared error would stall.",
                 font_size=24, color=INK),
        ).arrange(DOWN, buff=0.22)
        self.clamp_w(punch, 12.0).move_to([0, -0.7, 0])
        cap4 = self.say("That clean, non-vanishing gradient is why classifiers are "
                        "trained with cross-entropy.", color=INK, weight=BOLD)
        self.play(FadeIn(punch, shift=UP * 0.1), ReplacementTransform(cap3, cap4),
                  run_time=0.9)
        self.beat(2.2)
        self.wipe()

    # ====================================================================== #
    # Scene 6 — honesty: cross-entropy = H(p) + KL(p||q)
    # ====================================================================== #
    def scene_honest(self):
        header = self.section_header("Why it is honest", KL_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        ident = VGroup(
            Text("H(p, q)", font_size=40, t2c={"p": TRUE_C, "q": PRED_C}),
            Text("=", font_size=40),
            Text("H(p)", font_size=40, t2c={"p": TRUE_C}),
            Text("+", font_size=40),
            Text("KL(p ‖ q)", font_size=40, color=KL_C),
        ).arrange(RIGHT, buff=0.28).move_to([0, 2.0, 0])
        self.play(Write(ident), run_time=1.3)
        cap = self.say("Cross-entropy splits neatly into two pieces.", color=MUTED)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.5)
        self.play(Circumscribe(ident, color=KL_C, buff=0.18, run_time=1.4))
        self.beat(1.0)

        const_note = Text("fixed by the data", font_size=20, color=MUTED)
        const_note.next_to(ident[2], DOWN, buff=0.55)
        arrow_c = Arrow(const_note.get_top(), ident[2].get_bottom(), buff=0.1,
                        color=MUTED, stroke_width=3, max_tip_length_to_length_ratio=0.32)
        cap2 = self.say("The first piece depends only on the labels, so it is a "
                        "constant we cannot change.", color=INK)
        self.play(FadeIn(const_note), GrowArrow(arrow_c),
                  ReplacementTransform(cap, cap2), run_time=0.8)
        self.beat(1.8)

        min_line = VGroup(
            Text("minimise cross-entropy   =   minimise ", font_size=30),
            Text("KL(p ‖ q)", font_size=30, color=KL_C),
        ).arrange(RIGHT, buff=0.14).move_to([0, 0.55, 0])
        cap3 = self.say("So minimising cross-entropy is exactly minimising the "
                        "distance from the truth.", color=KL_C)
        self.play(FadeIn(min_line, shift=UP * 0.1), ReplacementTransform(cap2, cap3),
                  run_time=0.9)
        self.beat(1.8)

        self.play(FadeOut(ident, const_note, arrow_c), run_time=0.8)

        bars = DistBars([0.70, 0.20, 0.10], CLASSES, unit=3.0, lab_fs=22, val_fs=20)
        bars.move_to([-3.3, -1.7, 0])
        tmarks = VGroup()
        for i, tp in enumerate(P):
            x = bars.tracks[i].get_left()[0] + max(bars.bar_h, bars.unit * tp)
            m = DashedLine([x, bars.tracks[i].get_y() + 0.34, 0],
                           [x, bars.tracks[i].get_y() - 0.34, 0],
                           color=TRUE_C, stroke_width=2.5, dash_length=0.06)
            tmarks.add(m)
        tmk_lab = Text("target", font_size=18, color=TRUE_C)
        tmk_lab.next_to(tmarks[0], UP, buff=0.12)
        klbox = VGroup(
            Text("KL(p ‖ q)", font_size=26, color=KL_C, weight=BOLD),
            DecimalNumber(CE, num_decimal_places=2, font_size=46, color=KL_C),
        ).arrange(DOWN, buff=0.22).move_to([3.3, -1.7, 0])

        self.play(FadeIn(bars), FadeIn(tmarks, tmk_lab), FadeIn(klbox), run_time=0.8)
        cap4 = self.say("KL is never negative, and it is zero only when the "
                        "prediction equals the truth.", color=INK)
        self.play(ReplacementTransform(cap3, cap4), run_time=0.6)
        self.beat(1.4)

        kl = klbox[1]
        self.play(bars.retarget(0, 1.0), bars.retarget(1, 0.0), bars.retarget(2, 0.0),
                  ChangeDecimalToValue(kl, 0.0), run_time=2.0)
        self.play(Flash(kl, color=TRUE_C, line_length=0.22, num_lines=14), run_time=0.7)
        self.beat(1.0)

        cap5 = self.say("It is a proper scoring rule: the only way to lower the "
                        "loss is to report your true beliefs.", color=KL_C, weight=BOLD)
        self.play(ReplacementTransform(cap4, cap5), run_time=0.7)
        self.beat(2.2)
        self.wipe()

    # ====================================================================== #
    # Scene 7 — recap card
    # ====================================================================== #
    def scene_recap(self):
        title = Text("Cross-entropy, in one card", font_size=40, color=INK, weight="BOLD")
        title.to_edge(UP, buff=0.6)
        rule = Line(title.get_left(), title.get_right()).next_to(title, DOWN, buff=0.14)
        rule.set_stroke(GOLD, 3)
        self.play(Write(title), Create(rule), run_time=1.1)
        self.beat(0.5)

        formula = Text("L  =  − log q(true)", font_size=40, weight=BOLD,
                       t2c={"q": PRED_C})
        formula.next_to(rule, DOWN, buff=0.45)
        self.play(FadeIn(formula, shift=UP * 0.1), run_time=0.7)
        self.beat(0.8)

        points = [
            ("It scores your confidence, not just your answer.", GOLD),
            ("Confident mistakes cost the most, so it rewards honest probabilities.", LOSS_C),
            ("Its gradient is just  q − p , simple and it never saturates.", PRED_C),
            ("The loss is convex, so gradient descent reaches the global minimum.", TRUE_C),
            ("It equals the KL divergence up to a constant: lowest only when q matches the truth.", KL_C),
        ]
        rows = VGroup(*[bullet(t, fs=24, dot=c, dot_r=0.06) for t, c in points])
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        rows.next_to(formula, DOWN, buff=0.5)
        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.15), run_time=0.55)
            self.beat(0.9)
        self.beat(0.8)

        punch = Text("The standard loss for every classifier.",
                     font_size=26, color=INK, weight=BOLD, slant=ITALIC)
        punch.next_to(rows, DOWN, buff=0.45)
        self.play(FadeIn(punch, shift=UP * 0.1), run_time=0.7)
        self.beat(2.2)
        self.wipe()


# ========================================================================== #
# Scene 5 — the 3D payoff: gradient descent down the convex loss bowl.
# The ONLY scene with camera movement — because there is real 3D to see.
# ========================================================================== #
class Descent(_Common, ThreeDScene):
    def hud_swap(self, old, new, rt=0.6):
        """Cross-fade a fixed-in-frame (2D HUD) caption for another."""
        self.add_fixed_in_frame_mobjects(new)
        self.play(FadeOut(old), FadeIn(new), run_time=rt)

    def construct(self):
        self.camera.background_color = BG

        axes = ThreeDAxes(
            x_range=[-3, 4, 1], y_range=[-3.5, 3.5, 1], z_range=[0, 3.6, 1],
            x_length=6.4, y_length=6.4, z_length=3.2,
            axis_config={"stroke_color": MUTED, "stroke_width": 2},
        )
        surf = Surface(
            lambda u, v: axes.c2p(u, v, ce_loss(u, v)),
            u_range=[-3, 4], v_range=[-3.5, 3.5], resolution=(44, 44),
        )
        surf.set_style(fill_opacity=0.9, stroke_width=0.5, stroke_color=BG)
        surf.set_fill_by_value(
            axes=axes,
            colorscale=[(TRUE_C, CE_ZMIN), (GOLD, 0.5 * (CE_ZMIN + CE_ZMAX)), (BAD, CE_ZMAX)],
            axis=2,
        )

        # billboard axis labels (always face the camera)
        xl = Text("w", font_size=26, color=INK).move_to(axes.x_axis.get_end() + np.array([0.35, 0, 0.25]))
        yl = Text("b", font_size=26, color=INK).move_to(axes.y_axis.get_end() + np.array([0, 0.35, 0.25]))
        zl = Text("loss", font_size=24, color=LOSS_C, weight=BOLD).move_to(axes.z_axis.get_end() + np.array([0, 0, 0.35]))

        # 2D HUD, fixed in frame
        header = self.section_header("Cross-entropy is convex", GOLD)

        self.set_camera_orientation(phi=66 * DEGREES, theta=-52 * DEGREES, zoom=0.78)
        self.add_fixed_in_frame_mobjects(header)
        self.play(FadeIn(header), run_time=0.6)
        self.play(Create(axes), run_time=1.1)
        self.add_fixed_orientation_mobjects(xl, yl, zl)
        self.play(FadeIn(surf), run_time=1.6)

        cap = self.say("This is the cross-entropy loss over a model's two "
                       "parameters.", color=MUTED)
        self.add_fixed_in_frame_mobjects(cap)
        self.play(FadeIn(cap), run_time=0.6)
        self.beat(1.6)

        cap2 = self.say("It is a single convex bowl: one global minimum, no traps.",
                        color=INK)
        self.hud_swap(cap, cap2)
        self.beat(1.4)

        # gradient-descent ball + trail (lifted slightly above the surface)
        pts = [axes.c2p(w, b, ce_loss(w, b) + 0.12) for (w, b) in CE_PATH]
        trail = VMobject().set_points_smoothly(pts).set_stroke(INK, 4)
        ball = Dot3D(pts[0], radius=0.15, color=INK)
        self.play(FadeIn(ball, scale=1.6), run_time=0.5)

        cap3 = self.say("Gradient descent follows  q − p  downhill, straight to "
                        "the bottom.", color=TRUE_C)
        self.hud_swap(cap2, cap3)

        self.begin_ambient_camera_rotation(rate=0.12)
        self.play(Create(trail), MoveAlongPath(ball, trail),
                  run_time=5.0, rate_func=linear)
        self.beat(0.8)

        # mark the global minimum
        mpt = axes.c2p(CE_MIN[0], CE_MIN[1], ce_loss(*CE_MIN) + 0.12)
        stem = Line(axes.c2p(CE_MIN[0], CE_MIN[1], 0), mpt, color=GOLD, stroke_width=3)
        minlab = Text("global minimum", font_size=24, color=GOLD, weight=BOLD)
        minlab.move_to(mpt + np.array([0, 0, 0.7]))
        self.add_fixed_orientation_mobjects(minlab)
        self.play(Create(stem), FadeIn(minlab),
                  ball.animate.set_color(GOLD).scale(1.25), run_time=0.9)
        self.beat(1.6)

        self.stop_ambient_camera_rotation()
        cap4 = self.say("Convex means gradient descent always reaches the one best "
                        "answer.", color=INK, weight=BOLD)
        self.hud_swap(cap3, cap4)
        self.beat(2.0)

        # wipe
        self.wait(END_HOLD)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)


# ---- individually renderable scenes -------------------------------------- #
class Intro(_CEBase):
    def construct(self):
        self.play_intro()


class Setup(_CEBase):
    def construct(self):
        self.scene_setup()


class Formula(_CEBase):
    def construct(self):
        self.scene_formula()


class Surprise(_CEBase):
    def construct(self):
        self.scene_surprise()


class Gradient(_CEBase):
    def construct(self):
        self.scene_gradient()


class Honest(_CEBase):
    def construct(self):
        self.scene_honest()


class Recap(_CEBase):
    def construct(self):
        self.scene_recap()


class Outro(_CEBase):
    def construct(self):
        self.play_outro()


if __name__ == "__main__":
    # render order for the stitched film:
    # Intro · Setup · Formula · Surprise · Gradient · Descent · Honest · Recap · Outro
    Setup().render()

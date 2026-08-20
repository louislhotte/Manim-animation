"""Parameter Evolution During Training — a dynamic ~3-minute explainer, house-style.

What actually *changes* inside a model while it learns: its parameters. We watch
them move, one gradient step at a time, first on a model with **two** knobs, then
on one with **many** — and use cross-validation to keep the story honest.

Two symmetric parts, three scenes each, bookended by the channel cards:

    PART 1 — Linear regression  (2 parameters)
      1. Setup     -- 200 noisy points; the model ŷ = w·x + b has two knobs
      2. Descent   -- gradient descent: watch (w, b) slide down the loss bowl
                      while the line swings into place and the loss collapses
      3. Cross-val -- 5-fold CV: every fold learns the *same* two numbers →
                      a stable, trustworthy fit (no overfitting to fear)

    PART 2 — Neural network  (121 parameters)
      4. Many knobs-- a 1→40→1 net: 121 weights, a landscape we can't draw
      5. Training  -- the fitted curve grows from a line into the true shape…
                      and then starts memorising noise (weights still moving)
      6. Cross-val -- train loss keeps falling but validation turns back up;
                      CV finds the sweet spot → early stopping

Every on-screen number is real: the gradient-descent trajectory, the loss-surface
contours (an exact quadratic bowl), the 5-fold CV scores, and the neural net
(real numpy back-prop) are all computed here, not faked.

Everything uses ``Text`` (Pango), never ``Tex`` — renders with no LaTeX toolchain.

Scenes are exposed individually (``Setup``, ``Descent``, ``CVLinear``,
``ManyKnobs``, ``TrainNet``, ``CVNet``, ``Intro``, ``Outro``) and as one film
(``ParameterEvolution``).

Env knobs:
    PE_QUICK=1   collapse every hold (and the 5 s end-holds) for a fast render
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


QUICK = os.environ.get("PE_QUICK") == "1"
# Single pacing knob: every reading "hold" is self.beat(t) == wait(t * DELAY).
# Animation run-times are NOT scaled, so the piece stays dynamic — DELAY only
# sets how long text lingers. Each scene also ends on a fixed >=5 s hold
# (self.settle) as requested. QUICK collapses everything for iteration.
DELAY = 0.25 if QUICK else 1.8
END_HOLD = 0.2 if QUICK else 5.0

# ---- palette -------------------------------------------------------------- #
BG = "#0E1117"       # dark slate background
INK = "#F5F3EF"      # warm white text
MUTED = "#8A93A6"    # secondary text / axes
FAINT = "#2A3140"    # gridlines / contours
DATA_C = "#5B8DEF"   # data points (blue)
W_C = "#5B8DEF"      # the slope parameter w (blue)
B_C = "#2EC4B6"      # the intercept parameter b (teal)
MODEL_C = "#FFD166"  # the fitted model / line (gold)
LOSS_C = "#FFD166"   # loss readout (gold)
GOOD = "#3DD68C"     # good / train / pass (green)
BAD = "#FF5C5C"      # bad / overfit / miss (red)
ACCENT = "#FFD166"   # highlight (gold)
TRAIN_C = "#5B8DEF"  # training loss (blue)
VAL_C = "#FF8C42"    # validation loss (orange)


# ========================================================================== #
# PART 1 data + gradient descent + CV   (all real, numpy only)
# ========================================================================== #
_rng = np.random.default_rng(7)
N = 200
X = _rng.uniform(-2.6, 2.6, N)                 # mean≈0 → axis-aligned loss bowl
W_TRUE, B_TRUE = 1.15, 0.55
Y = W_TRUE * X + B_TRUE + _rng.normal(0, 0.9, N)


def mse(w, b, xs=X, ys=Y):
    return float(np.mean((w * xs + b - ys) ** 2))


# closed-form optimum + the exact quadratic bowl it sits in
_A = np.c_[X, np.ones_like(X)]
W_OPT, B_OPT = (float(v) for v in np.linalg.lstsq(_A, Y, rcond=None)[0])
L_MIN = mse(W_OPT, B_OPT)                       # ≈ 0.759
MEAN_X2 = float(np.mean(X ** 2))                # ≈ 2.302  (bowl aspect ratio)

# full-batch gradient descent, recorded step by step
LR, STEPS = 0.10, 60
W0, B0 = -0.70, 2.70                            # deliberately bad init (wrong slope)
_w, _b = W0, B0
WTR, BTR, LTR = [_w], [_b], [mse(_w, _b)]
for _ in range(STEPS):
    _r = (_w * X + _b) - Y
    _w -= LR * 2 * np.mean(_r * X)
    _b -= LR * 2 * np.mean(_r)
    WTR.append(_w); BTR.append(_b); LTR.append(mse(_w, _b))
WTR, BTR, LTR = np.array(WTR), np.array(BTR), np.array(LTR)

# 5-fold CV for the linear model: every fold's learned (w, b) + its val MSE
_idx = _rng.permutation(N)
_folds = np.array_split(_idx, 5)
FOLD_WB, FOLD_VAL = [], []
for _k in range(5):
    _va = _folds[_k]
    _tr = np.concatenate([_folds[j] for j in range(5) if j != _k])
    _M = np.c_[X[_tr], np.ones_like(X[_tr])]
    _wk, _bk = (float(v) for v in np.linalg.lstsq(_M, Y[_tr], rcond=None)[0])
    FOLD_WB.append((_wk, _bk))
    FOLD_VAL.append(mse(_wk, _bk, X[_va], Y[_va]))
CV_MEAN_L = float(np.mean(FOLD_VAL))            # ≈ 0.78
CV_STD_L = float(np.std(FOLD_VAL))              # small
FOLD_W = np.array([w for w, _ in FOLD_WB])
FOLD_B = np.array([b for _, b in FOLD_WB])


# ========================================================================== #
# PART 2 data + a real neural net (numpy back-prop) + CV
# ========================================================================== #
_rng2 = np.random.default_rng(3)
NN_N = 30
NX = np.sort(_rng2.uniform(-3, 3, NN_N))


def _f_true(x):
    return 1.5 * np.sin(1.1 * x) + 0.18 * x


NY = _f_true(NX) + _rng2.normal(0, 0.5, NN_N)
_XM, _XS = NX.mean(), NX.std()
_YM, _YS = NY.mean(), NY.std()
NXS = (NX - _XM) / _XS
NYS = (NY - _YM) / _YS
NN_H = 40
NN_PARAMS = NN_H + NN_H + NN_H + 1              # W1,b1,W2,b2 for 1→H→1 = 121


def _net(seed):
    g = np.random.default_rng(seed)
    return dict(W1=g.normal(0, 1, (NN_H, 1)), b1=np.zeros((NN_H, 1)),
                W2=g.normal(0, 1, (1, NN_H)) / np.sqrt(NN_H), b2=np.zeros((1, 1)))


def _fwd(p, x):
    a1 = np.tanh(p["W1"] @ x + p["b1"])
    return p["W2"] @ a1 + p["b2"], a1


def _step(p, xt, yt, lr=0.06):
    z2, a1 = _fwd(p, xt)
    M = xt.shape[1]
    d2 = (2.0 / M) * (z2 - yt)
    gW2 = d2 @ a1.T; gb2 = d2.sum(1, keepdims=True)
    d1 = (p["W2"].T @ d2) * (1 - a1 ** 2)
    gW1 = d1 @ xt.T; gb1 = d1.sum(1, keepdims=True)
    for k, g in (("W1", gW1), ("b1", gb1), ("W2", gW2), ("b2", gb2)):
        p[k] -= lr * g


# fitted-curve snapshots (train on ALL points → watch it form, then overfit)
NN_GRID = np.linspace(-3, 3, 240)
_grid_s = (NN_GRID - _XM) / _XS
_p = _net(0)
_xt, _yt = NXS.reshape(1, -1), NYS.reshape(1, -1)
SNAP_EPOCHS = [0, 40, 150, 600, 12000]
SNAP_CURVES = {}
for _e in range(12001):
    if _e in SNAP_EPOCHS:
        _zg, _ = _fwd(_p, _grid_s.reshape(1, -1))
        SNAP_CURVES[_e] = _zg.ravel() * _YS + _YM      # de-standardised (raw y)
    _step(_p, _xt, _yt)

# 5-fold CV learning curves (averaged), in RAW MSE units
NN_EP = 6000
_tr = np.zeros(NN_EP + 1)
_va = np.zeros(NN_EP + 1)
_idxn = np.random.default_rng(11).permutation(NN_N)
_foldsn = np.array_split(_idxn, 5)
for _k in range(5):
    _v = _foldsn[_k]
    _t = np.concatenate([_foldsn[j] for j in range(5) if j != _k])
    _p = _net(1)
    _xt, _yt = NXS[_t].reshape(1, -1), NYS[_t].reshape(1, -1)
    _xv, _yv = NXS[_v].reshape(1, -1), NYS[_v].reshape(1, -1)
    for _e in range(NN_EP + 1):
        _z2, _a1 = _fwd(_p, _xt)
        _tr[_e] += np.mean((_z2 - _yt) ** 2)
        _zv, _ = _fwd(_p, _xv)
        _va[_e] += np.mean((_zv - _yv) ** 2)
        _step(_p, _xt, _yt)
NN_TR = _tr / 5 * _YS ** 2
NN_VA = _va / 5 * _YS ** 2
NN_BEST = int(np.argmin(NN_VA))                # ≈ 208  (early-stop epoch)
NN_VAL_MIN = float(NN_VA[NN_BEST])             # ≈ 0.283
NN_VAL_END = float(NN_VA[-1])                  # ≈ 0.355
NN_TR_END = float(NN_TR[-1])                   # ≈ 0.185

# down-sample (geometric) for a cheap, smooth log-x plot
E_START = 8
_ep = np.unique(np.round(np.geomspace(E_START, NN_EP, 120)).astype(int))
EP_PLOT = _ep[(_ep >= E_START) & (_ep <= NN_EP)]
_ylo = float(min(NN_TR[EP_PLOT].min(), NN_VA[EP_PLOT].min()))
_yhi = float(max(NN_TR[EP_PLOT].max(), NN_VA[EP_PLOT].max()))
CURVE_YLO = max(0.0, _ylo - 0.06)
CURVE_YHI = _yhi + 0.05


# ========================================================================== #
# small reusable pieces
# ========================================================================== #
def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])])
    return v.set_stroke(color=color, width=sw).scale(scale)


def chip(text, color, fs=24, fill=0.14, w=None, h=0.62, tcolor=None):
    label = Text(text, font_size=fs, color=tcolor or INK)
    width = (label.width + 0.5) if w is None else w
    box = RoundedRectangle(width=width, height=h, corner_radius=0.12,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=fill)
    label.move_to(box)
    return VGroup(box, label)


def stat(label, color, dp=2, start=0.0, lab_fs=22, num_fs=34):
    """A little 'label = number' readout; returns (group, DecimalNumber)."""
    lab = Text(label, font_size=lab_fs, color=color, weight="BOLD")
    num = DecimalNumber(start, num_decimal_places=dp, font_size=num_fs, color=INK)
    grp = VGroup(lab, num).arrange(RIGHT, buff=0.18)
    return grp, num


def clamp(v, lo, hi):
    return float(min(max(v, lo), hi))


# ========================================================================== #
class _PEBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # ---- timing helpers --------------------------------------------------- #
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.25 if QUICK else 1.0))

    def settle(self):
        """The mandatory >=5 s hold on the finished scene before it wipes."""
        self.wait(END_HOLD)

    def wipe(self, rt=0.6):
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    def section_header(self, part, label, color):
        tag = Text(part, font_size=20, color=color, weight="BOLD")
        tagbox = RoundedRectangle(width=tag.width + 0.4, height=0.44, corner_radius=0.1,
                                  stroke_color=color, stroke_width=2,
                                  fill_color=color, fill_opacity=0.12)
        tag.move_to(tagbox)
        title = Text(label, font_size=34, color=INK, weight="BOLD")
        head = VGroup(VGroup(tagbox, tag), title).arrange(RIGHT, buff=0.3)
        head.to_corner(UL, buff=0.5)
        line = Line(head.get_left(), head.get_right()).next_to(head, DOWN, buff=0.13)
        line.set_stroke(color=color, width=3)
        return VGroup(head, line)

    # ---- house-style bookend cards ---------------------------------------- #
    def _bookend(self, title, subtitle=None):
        header = Text(title, font_size=52, color=INK, weight="BOLD")
        header.set(width=min(11.0, header.width))
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=ACCENT)
        writer = Text("Created by Ptolémé", font_size=28, color=DATA_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.4)
        self.card_wait(0.6)
        if subtitle:
            sub = Text(subtitle, font_size=34, color=MUTED)
            sub.move_to(header)
            self.play(Transform(header, sub), run_time=0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        return VGroup(header, writer, line)

    def play_intro(self):
        grp = self._bookend("Parameter Evolution During Training",
                            "How a model learns — one gradient step at a time")
        self.card_wait(1.8)
        self.play(FadeOut(grp), run_time=0.9)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.4)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=ACCENT)
        writer = Text("Created by Ptolémé", font_size=28, color=DATA_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.2)
        self.card_wait(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.card_wait(1.8)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.0)
        self.card_wait(0.4)

    # ---- shared builders -------------------------------------------------- #
    def lin_axes(self):
        ax = Axes(x_range=[-3, 3, 1], y_range=[-6, 6, 2],
                  x_length=6.3, y_length=4.7, tips=False,
                  axis_config={"include_numbers": False, "include_ticks": False,
                               "stroke_color": MUTED, "stroke_width": 2})
        return ax

    def lin_dots(self, ax, color=DATA_C, r=0.055):
        return VGroup(*[
            Dot(ax.c2p(x, clamp(y, -6, 6)), radius=r, color=color)
            .set_stroke(INK, width=1, opacity=0.5)
            for x, y in zip(X, Y)])

    def line_from(self, ax, w, b):
        x0, x1 = ax.x_range[0], ax.x_range[1]
        p0 = ax.c2p(x0, clamp(w * x0 + b, -6, 6))
        p1 = ax.c2p(x1, clamp(w * x1 + b, -6, 6))
        return Line(p0, p1, color=MODEL_C, stroke_width=5)

    # ====================================================================== #
    # Scene 1 — Linear setup: the data + the two knobs
    # ====================================================================== #
    def scene_setup(self):
        head = self.section_header("PART 1", "Linear Regression", W_C)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.6)

        ax = self.lin_axes().to_edge(LEFT, buff=0.95).shift(DOWN * 0.15)
        xlab = Text("input  x", font_size=21, color=MUTED).next_to(ax.get_bottom(), DOWN, buff=0.18)
        ylab = Text("output  y", font_size=21, color=MUTED).rotate(PI / 2).next_to(ax.get_left(), LEFT, buff=0.18)
        self.play(Create(ax), FadeIn(xlab), FadeIn(ylab), run_time=0.8)

        cap = Text("200 noisy observations", font_size=25, color=MUTED)
        cap.next_to(head, DOWN, buff=0.22).to_edge(LEFT, buff=0.55)
        self.play(FadeIn(cap, shift=UP * 0.15), run_time=0.4)
        dots = self.lin_dots(ax)
        self.play(LaggedStart(*[GrowFromCenter(d) for d in dots],
                              lag_ratio=0.006, run_time=1.6))
        self.beat(0.8)

        # the model + its two parameters
        panel = VGroup(
            Text("The model is a straight line:", font_size=26, color=INK),
            Text("ŷ  =  w · x  +  b", font_size=40, color=MODEL_C, weight="BOLD"),
        ).arrange(DOWN, buff=0.28).to_edge(RIGHT, buff=0.6).shift(UP * 1.35)
        self.play(FadeIn(panel[0], shift=UP * 0.1), run_time=0.6)
        self.play(Write(panel[1]), run_time=0.9)
        self.beat(0.8)

        knobs = VGroup(
            VGroup(Dot(radius=0.09, color=W_C),
                   Text("w  —  the slope", font_size=25, color=INK)).arrange(RIGHT, buff=0.22),
            VGroup(Dot(radius=0.09, color=B_C),
                   Text("b  —  the intercept", font_size=25, color=INK)).arrange(RIGHT, buff=0.22),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).next_to(panel, DOWN, buff=0.5)
        two = Text("Just two 'knobs' to set.", font_size=24, color=ACCENT, slant=ITALIC)
        two.next_to(knobs, DOWN, aligned_edge=LEFT, buff=0.35)
        for k in knobs:
            self.play(FadeIn(k, shift=RIGHT * 0.15), run_time=0.5)
            self.beat(0.4)
        self.play(FadeIn(two, shift=UP * 0.1), run_time=0.5)
        self.beat(0.6)

        # a random starting guess — a bad line
        guess = self.line_from(ax, W0, B0)
        glab = Text("a random starting guess", font_size=23, color=BAD)
        glab.next_to(ax.c2p(0, -4.7), DOWN, buff=0.1)
        self.play(Create(guess), FadeIn(glab, shift=UP * 0.1), run_time=0.9)
        self.beat(0.5)
        punch = Text("Training = adjust w and b until the line fits.",
                     font_size=26, color=INK, weight="BOLD").to_edge(DOWN, buff=0.3)
        self.play(Write(punch), run_time=1.0)
        self.play(Indicate(panel[1], color=MODEL_C, scale_factor=1.08), run_time=0.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — Gradient descent: the two parameters slide down the loss bowl
    # ====================================================================== #
    def scene_descent(self):
        head = self.section_header("PART 1", "Gradient Descent", W_C)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.5)

        # left: data + the current line ; right: the (w, b) loss landscape
        axL = self.lin_axes().scale(0.92).to_edge(LEFT, buff=0.55).shift(DOWN * 0.35)
        xlab = Text("x", font_size=20, color=MUTED).next_to(axL.x_axis.get_right(), DOWN, buff=0.12)
        ylab = Text("y", font_size=20, color=MUTED).next_to(axL.y_axis.get_top(), LEFT, buff=0.12)
        dots = self.lin_dots(axL, r=0.045)

        axC = Axes(x_range=[-1.3, 2.9, 1], y_range=[-2.1, 3.1, 1],
                   x_length=5.0, y_length=4.7, tips=False,
                   axis_config={"include_numbers": False, "include_ticks": False,
                                "stroke_color": MUTED, "stroke_width": 2})
        axC.to_edge(RIGHT, buff=0.55).shift(DOWN * 0.35)
        cxlab = Text("w  →", font_size=22, color=W_C).next_to(axC.x_axis.get_right(), DOWN, buff=0.12)
        cylab = Text("b  →", font_size=22, color=B_C).rotate(PI / 2).next_to(axC.y_axis.get_top(), LEFT, buff=0.12)
        ctitle = Text("loss landscape  L(w, b)", font_size=22, color=MUTED)
        ctitle.next_to(axC, UP, buff=0.18)

        # the exact quadratic bowl: nested similar ellipses about (W_OPT, B_OPT)
        def ellipse(db, n=120):
            dw = db / np.sqrt(MEAN_X2)
            th = np.linspace(0, TAU, n)
            pts = [axC.c2p(W_OPT + dw * np.cos(t), B_OPT + db * np.sin(t)) for t in th]
            return VMobject().set_points_as_corners(pts).set_stroke(FAINT, 2)

        rings = VGroup(*[ellipse(db) for db in (0.5, 0.9, 1.35, 1.9, 2.5)])
        minstar = Star(n=5, outer_radius=0.12, color=GOOD, fill_opacity=1, stroke_width=0)
        minstar.move_to(axC.c2p(W_OPT, B_OPT))
        minlab = Text("minimum", font_size=19, color=GOOD).next_to(minstar, DOWN, buff=0.12)
        hi = Text("high loss", font_size=19, color=BAD).move_to(axC.c2p(-0.5, 2.35))

        self.play(Create(axL), FadeIn(xlab), FadeIn(ylab),
                  LaggedStart(*[GrowFromCenter(d) for d in dots], lag_ratio=0.004),
                  run_time=1.2)
        self.play(Create(axC), FadeIn(cxlab), FadeIn(cylab), FadeIn(ctitle),
                  LaggedStart(*[Create(r) for r in rings], lag_ratio=0.15),
                  run_time=1.2)
        self.play(GrowFromCenter(minstar), FadeIn(minlab), FadeIn(hi), run_time=0.6)
        self.beat(0.6)

        # readout strip (step / w / b / loss), all driven live by `prog`
        prog = ValueTracker(0.0)

        def wb_at(v):
            i0 = int(np.floor(v)); i1 = min(i0 + 1, STEPS); fr = v - i0
            return (WTR[i0] * (1 - fr) + WTR[i1] * fr, BTR[i0] * (1 - fr) + BTR[i1] * fr)

        g_step, n_step = stat("step", MUTED, dp=0, start=0, num_fs=32)
        g_w, n_w = stat("w =", W_C, start=W0)
        g_b, n_b = stat("b =", B_C, start=B0)
        g_loss, n_loss = stat("loss =", LOSS_C, start=LTR[0])
        readout = VGroup(g_step, g_w, g_b, g_loss).arrange(RIGHT, buff=0.55)
        readout.next_to(head, RIGHT, buff=0.7).align_to(head, UP)

        # introduce the readout + a *static* starting line/dot, then hand off to
        # live updaters (you can't Create an always_redraw mobject — its per-frame
        # rebuild fights the animation).
        line0 = self.line_from(axL, W0, B0)
        ball0 = Dot(axC.c2p(W0, B0), radius=0.09, color=MODEL_C).set_stroke(INK, 1.2)
        self.play(FadeIn(readout), Create(line0), FadeIn(ball0), run_time=0.7)

        n_step.add_updater(lambda m: m.set_value(int(round(prog.get_value()))))
        n_w.add_updater(lambda m: m.set_value(wb_at(prog.get_value())[0]))
        n_b.add_updater(lambda m: m.set_value(wb_at(prog.get_value())[1]))
        n_loss.add_updater(lambda m: m.set_value(mse(*wb_at(prog.get_value()))))
        line = always_redraw(lambda: self.line_from(axL, *wb_at(prog.get_value())))

        def path_mob():
            v = prog.get_value(); n = int(np.ceil(v))
            pts = [axC.c2p(WTR[i], BTR[i]) for i in range(min(n, STEPS) + 1)]
            pts.append(axC.c2p(*wb_at(v)))
            return VMobject().set_points_as_corners(pts).set_stroke(MODEL_C, 4)

        path = always_redraw(path_mob)
        ball = always_redraw(lambda: Dot(axC.c2p(*wb_at(prog.get_value())),
                                         radius=0.09, color=MODEL_C).set_stroke(INK, 1.2))
        self.remove(line0, ball0)
        self.add(path, line, ball)
        self.beat(0.5)

        # phase 1 — the first steps: the wrong-sloped line flips upward
        note1 = Text("each step nudges w and b downhill…", font_size=24, color=INK)
        note1.next_to(axL, DOWN, buff=0.25)
        self.play(FadeIn(note1, shift=UP * 0.1), run_time=0.4)
        self.play(prog.animate.set_value(10), run_time=3.3, rate_func=rate_functions.ease_in_out_sine)
        self.beat(0.9)

        # phase 2 — race down into the bowl
        note2 = Text("…and the loss collapses toward the minimum.", font_size=24, color=ACCENT)
        note2.move_to(note1)
        self.play(FadeOut(note1, shift=UP * 0.1), FadeIn(note2, shift=UP * 0.1), run_time=0.4)
        self.play(prog.animate.set_value(STEPS), run_time=6.4, rate_func=rate_functions.ease_in_out_sine)
        self.play(Flash(minstar, color=GOOD, flash_radius=0.5), run_time=0.7)

        # freeze the readout on the converged values
        for n in (n_step, n_w, n_b, n_loss):
            n.clear_updaters()
        conv = chip(f"converged:  w ≈ {WTR[-1]:.2f},  b ≈ {BTR[-1]:.2f},  loss ≈ {LTR[-1]:.2f}",
                    GOOD, fs=23).next_to(axL, DOWN, buff=0.25)
        self.play(ReplacementTransform(note2, conv), run_time=0.6)
        self.play(Indicate(g_loss, color=GOOD, scale_factor=1.1), run_time=0.7)
        self.beat(0.6)
        punch = Text("Two parameters, one downhill walk — that's learning.",
                     font_size=26, color=INK, weight="BOLD").to_edge(DOWN, buff=0.28)
        self.play(Write(punch), run_time=1.0)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Cross-validation for the linear model
    # ====================================================================== #
    def scene_cv_linear(self):
        head = self.section_header("PART 1", "Cross-Validation", GOOD)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.5)
        sub = Text("Refit on 5 folds — do the parameters stay put?",
                   font_size=25, color=MUTED)
        sub.next_to(head, DOWN, buff=0.22).to_edge(LEFT, buff=0.55)
        self.play(FadeIn(sub, shift=UP * 0.1), run_time=0.4)

        # compact k-fold strip: validation block sweeping across 5 rounds
        def fold_row(vi, k=5, bw=0.66, bh=0.34, buff=0.09):
            row = VGroup()
            for j in range(k):
                is_v = j == vi
                c = VAL_C if is_v else TRAIN_C
                row.add(RoundedRectangle(width=bw, height=bh, corner_radius=0.06,
                                         stroke_width=1.5, stroke_color=c,
                                         fill_color=c, fill_opacity=0.9 if is_v else 0.22))
            return row.arrange(RIGHT, buff=buff)

        rows = VGroup(*[fold_row(i) for i in range(5)]).arrange(DOWN, buff=0.16)
        rows.to_edge(LEFT, buff=0.9).shift(DOWN * 0.05)
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.1) for r in rows],
                              lag_ratio=0.15, run_time=1.2))
        leg = VGroup(
            VGroup(Square(0.24, stroke_width=0, fill_color=TRAIN_C, fill_opacity=0.5),
                   Text("train", font_size=19, color=INK)).arrange(RIGHT, buff=0.14),
            VGroup(Square(0.24, stroke_width=0, fill_color=VAL_C, fill_opacity=0.9),
                   Text("validate", font_size=19, color=INK)).arrange(RIGHT, buff=0.14),
        ).arrange(RIGHT, buff=0.5).next_to(rows, UP, buff=0.3)
        self.play(FadeIn(leg), run_time=0.4)
        self.beat(0.6)

        # right: the 5 fitted lines land almost on top of each other
        ax = Axes(x_range=[-3, 3, 1], y_range=[-6, 6, 2], x_length=5.2, y_length=4.2,
                  tips=False, axis_config={"include_numbers": False, "include_ticks": False,
                                           "stroke_color": MUTED, "stroke_width": 2})
        ax.to_edge(RIGHT, buff=0.7).shift(DOWN * 0.35)
        dots = self.lin_dots(ax, r=0.04)
        self.play(Create(ax), LaggedStart(*[GrowFromCenter(d) for d in dots],
                                          lag_ratio=0.004), run_time=1.0)
        fit_lines = VGroup(*[
            Line(ax.c2p(-3, clamp(w * -3 + b, -6, 6)), ax.c2p(3, clamp(w * 3 + b, -6, 6)),
                 color=GOOD, stroke_width=3).set_opacity(0.7)
            for w, b in FOLD_WB])
        tlab = Text("5 folds → 5 fits", font_size=22, color=GOOD).next_to(ax, UP, buff=0.15)
        self.play(FadeIn(tlab), LaggedStart(*[Create(l) for l in fit_lines],
                                            lag_ratio=0.25, run_time=1.8))
        self.beat(0.5)
        same = Text("nearly identical lines", font_size=22, color=ACCENT)
        same.next_to(ax.c2p(0, -5.2), DOWN, buff=0.08)
        self.play(FadeIn(same, shift=UP * 0.1), run_time=0.5)
        self.play(Circumscribe(fit_lines, color=ACCENT, run_time=1.1))
        self.beat(0.6)

        # the payoff numbers: parameters barely move, CV score is tight
        spread = VGroup(
            Text(f"w = {FOLD_W.mean():.2f}  ± {FOLD_W.std():.3f}", font_size=26, color=W_C, weight="BOLD"),
            Text(f"b = {FOLD_B.mean():.2f}  ± {FOLD_B.std():.3f}", font_size=26, color=B_C, weight="BOLD"),
            Text(f"CV error = {CV_MEAN_L:.2f}  ± {CV_STD_L:.2f}", font_size=26, color=GOOD, weight="BOLD"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.26)
        spread.next_to(rows, DOWN, buff=0.32).to_edge(LEFT, buff=0.9)
        for s in spread:
            self.play(FadeIn(s, shift=RIGHT * 0.12), run_time=0.5)
            self.beat(0.4)
        punch = Text("Every fold learns the same two numbers → a stable, trustworthy fit.",
                     font_size=25, color=INK, weight="BOLD").to_edge(DOWN, buff=0.28)
        self.play(Write(punch), run_time=1.1)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Neural network: many knobs, a landscape we can't draw
    # ====================================================================== #
    def _mini_net(self, n_shown=9, width=3.2, height=3.4):
        """A schematic 1→(many)→1 net; returns (group, in_dot, hidden dots, out_dot)."""
        left = LEFT * width / 2
        right = RIGHT * width / 2
        in_dot = Dot(left, radius=0.11, color=DATA_C)
        out_dot = Dot(right, radius=0.11, color=MODEL_C)
        ys = np.linspace(height / 2, -height / 2, n_shown)
        hidden = VGroup(*[Dot([0, y, 0], radius=0.08, color=INK) for y in ys])
        # an ellipsis to signal "more neurons than drawn"
        dots3 = VGroup(*[Dot([0, y, 0], radius=0.02, color=MUTED)
                         for y in (-height / 2 - 0.18, -height / 2 - 0.33, -height / 2 - 0.48)])
        edges = VGroup()
        for h in hidden:
            edges.add(Line(in_dot.get_center(), h.get_center(), stroke_width=1.6,
                           stroke_color=MUTED, stroke_opacity=0.6))
        for h in hidden:
            edges.add(Line(h.get_center(), out_dot.get_center(), stroke_width=1.6,
                           stroke_color=MUTED, stroke_opacity=0.6))
        grp = VGroup(edges, in_dot, hidden, dots3, out_dot)
        return grp, in_dot, hidden, out_dot, edges

    def scene_nn_arch(self):
        head = self.section_header("PART 2", "Neural Network", VAL_C)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.6)
        sub = Text("Same idea — a lot more knobs.", font_size=25, color=MUTED)
        sub.next_to(head, DOWN, buff=0.22).to_edge(LEFT, buff=0.55)
        self.play(FadeIn(sub, shift=UP * 0.1), run_time=0.4)

        net, in_dot, hidden, out_dot, edges = self._mini_net()
        net.shift(LEFT * 3.3 + DOWN * 0.25)
        inlab = Text("x", font_size=24, color=DATA_C).next_to(in_dot, LEFT, buff=0.2)
        outlab = Text("ŷ", font_size=24, color=MODEL_C).next_to(out_dot, RIGHT, buff=0.2)
        hlab = Text("40 hidden neurons", font_size=20, color=MUTED).next_to(hidden, UP, buff=0.25)

        self.play(FadeIn(in_dot), FadeIn(out_dot), FadeIn(inlab), FadeIn(outlab), run_time=0.5)
        self.play(LaggedStart(*[GrowFromCenter(h) for h in hidden], lag_ratio=0.05),
                  FadeIn(net[3]), FadeIn(hlab), run_time=1.0)
        self.play(LaggedStart(*[Create(e) for e in edges], lag_ratio=0.02, run_time=1.4))
        self.beat(0.6)

        # each edge is a weight — a parameter
        wnote = Text("every edge is a weight — a parameter", font_size=23, color=INK)
        wnote.next_to(net, DOWN, buff=0.4)
        self.play(FadeIn(wnote, shift=UP * 0.1), run_time=0.5)
        self.play(LaggedStart(*[Indicate(e, color=VAL_C, scale_factor=1.0)
                               for e in edges], lag_ratio=0.03, run_time=1.6))
        self.beat(0.5)

        # the count, and the punchline: no 2-D bowl to draw anymore
        facts = VGroup(
            Text("linear model", font_size=24, color=W_C),
            Text("2 parameters", font_size=40, color=W_C, weight="BOLD"),
            Text("this network", font_size=24, color=VAL_C),
            Text(f"{NN_PARAMS} parameters", font_size=40, color=VAL_C, weight="BOLD"),
        ).arrange_in_grid(rows=2, cols=2, col_widths=[3.0, 3.0], buff=(0.6, 0.2))
        facts.to_edge(RIGHT, buff=0.7).shift(UP * 0.35)
        self.play(FadeIn(facts[0]), FadeIn(facts[1], shift=UP * 0.1), run_time=0.6)
        self.beat(0.4)
        self.play(FadeIn(facts[2]), FadeIn(facts[3], shift=UP * 0.1), run_time=0.6)
        self.play(Circumscribe(facts[3], color=VAL_C, run_time=1.0))
        self.beat(0.5)
        punch = Text("121 knobs → a landscape we can't draw. So we watch what the net does.",
                     font_size=24, color=INK, weight="BOLD").to_edge(DOWN, buff=0.28)
        self.play(FadeIn(punch, shift=UP * 0.1), run_time=0.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — Training the net: the fitted curve forms, then overfits
    # ====================================================================== #
    def _nn_axes(self):
        ax = Axes(x_range=[-3, 3, 1], y_range=[-3, 3, 1], x_length=7.4, y_length=4.6,
                  tips=False, axis_config={"include_numbers": False, "include_ticks": False,
                                           "stroke_color": MUTED, "stroke_width": 2})
        return ax

    def _curve(self, ax, ys, color=MODEL_C, width=5):
        pts = [ax.c2p(x, clamp(y, -3, 3)) for x, y in zip(NN_GRID, ys)]
        return VMobject().set_points_as_corners(pts).set_stroke(color, width)

    def scene_nn_train(self):
        head = self.section_header("PART 2", "Training the Net", VAL_C)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.5)

        ax = self._nn_axes().shift(DOWN * 0.35 + LEFT * 0.2)
        xlab = Text("x", font_size=20, color=MUTED).next_to(ax.x_axis.get_right(), DOWN, buff=0.12)
        ylab = Text("y", font_size=20, color=MUTED).next_to(ax.y_axis.get_top(), LEFT, buff=0.12)
        data = VGroup(*[Dot(ax.c2p(x, clamp(y, -3, 3)), radius=0.06, color=DATA_C)
                        .set_stroke(INK, 1, opacity=0.5) for x, y in zip(NX, NY)])
        self.play(Create(ax), FadeIn(xlab), FadeIn(ylab),
                  LaggedStart(*[GrowFromCenter(d) for d in data], lag_ratio=0.03),
                  run_time=1.3)

        # a small live net in the corner whose weights visibly jitter & settle
        mini, _, mh, _, medges = self._mini_net(n_shown=6, width=1.7, height=1.7)
        mini.scale(0.9).to_corner(UR, buff=0.5).shift(DOWN * 0.1)
        mtitle = Text("weights updating", font_size=18, color=MUTED).next_to(mini, DOWN, buff=0.15)
        self.play(FadeIn(mini), FadeIn(mtitle), run_time=0.5)

        eprog = ValueTracker(0.0)
        phases = np.array([0.0, 0.02, 0.20, 0.55, 1.0])  # eases across snapshots
        rphase = np.random.default_rng(5).uniform(0, TAU, len(medges))
        ramp = np.random.default_rng(6).uniform(3, 7, len(medges))

        def style_edges(m):
            t = eprog.get_value()
            for i, e in enumerate(m):
                # weight magnitude wobbles early, settles late (looks like GD)
                wob = np.sin(rphase[i] + ramp[i] * t) * np.exp(-2.2 * t)
                mag = 0.55 + 0.45 * abs(np.tanh(1.4 * (0.3 + wob)))
                e.set_stroke(width=1.2 + 3.0 * mag,
                             color=VAL_C if wob >= 0 else BAD, opacity=0.85)
        medges.add_updater(style_edges)

        # epoch readout
        g_ep, n_ep = stat("epoch", MUTED, dp=0, start=0, num_fs=30)
        g_ep.next_to(head, RIGHT, buff=0.8).align_to(head, UP)
        self.play(FadeIn(g_ep), run_time=0.3)
        n_ep.add_updater(lambda m: m.set_value(int(round(
            np.interp(eprog.get_value(), [0, 1], [0, 12000])))))

        # morph the fitted curve through the real snapshots
        order = SNAP_EPOCHS
        captions = {
            0:    ("random weights → a flat guess", MUTED),
            40:   ("it finds the overall trend", INK),
            150:  ("the curve takes the true shape", GOOD),
            600:  ("sharper — fitting finer detail", ACCENT),
            12000:("now it's chasing the noise: overfitting", BAD),
        }
        curve = self._curve(ax, SNAP_CURVES[order[0]], color=MODEL_C)
        cap = Text(captions[order[0]][0], font_size=24, color=captions[order[0]][1])
        cap.next_to(ax, DOWN, buff=0.28)
        self.play(Create(curve), FadeIn(cap, shift=UP * 0.1), run_time=0.8)
        self.beat(0.7)

        for a, e in zip(order[:-1], order[1:]):
            target = self._curve(ax, SNAP_CURVES[e],
                                 color=BAD if e == order[-1] else MODEL_C)
            newcap = Text(captions[e][0], font_size=24, color=captions[e][1])
            newcap.next_to(ax, DOWN, buff=0.28)
            frac = phases[order.index(e)]
            self.play(Transform(curve, target),
                      eprog.animate.set_value(frac),
                      ReplacementTransform(cap, newcap),
                      run_time=2.4, rate_func=rate_functions.ease_in_out_sine)
            cap = newcap
            self.beat(0.9)

        medges.clear_updaters()
        n_ep.clear_updaters()
        self.play(Circumscribe(ax, color=BAD, run_time=1.2))
        punch = Text("The parameters never stop moving — but newer isn't always better.",
                     font_size=25, color=INK, weight="BOLD").to_edge(DOWN, buff=0.26)
        self.play(FadeIn(punch, shift=UP * 0.1), run_time=0.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 6 — Cross-validation for the net: when to stop
    # ====================================================================== #
    def scene_cv_nn(self):
        head = self.section_header("PART 2", "Cross-Validation", GOOD)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.5)
        sub = Text("Track train vs. validation loss across training (5-fold average)",
                   font_size=24, color=MUTED)
        sub.next_to(head, DOWN, buff=0.2).to_edge(LEFT, buff=0.55)
        self.play(FadeIn(sub, shift=UP * 0.1), run_time=0.4)

        lx0, lx1 = np.log10(E_START), np.log10(NN_EP)
        ax = Axes(x_range=[lx0, lx1, 1], y_range=[CURVE_YLO, CURVE_YHI, 0.1],
                  x_length=8.6, y_length=4.5, tips=False,
                  axis_config={"include_numbers": False, "include_ticks": False,
                               "stroke_color": MUTED, "stroke_width": 2})
        ax.center().shift(DOWN * 0.35)
        xlab = Text("training epochs  (log scale)  →", font_size=22, color=MUTED)
        xlab.next_to(ax.x_axis, DOWN, buff=0.22)
        ylab = Text("loss", font_size=22, color=MUTED).rotate(PI / 2).next_to(ax.y_axis, LEFT, buff=0.2)
        # a few epoch tick labels on the log axis
        ticks = VGroup()
        for e, s in [(10, "10"), (100, "100"), (1000, "1k"), (6000, "6k")]:
            if lx0 <= np.log10(e) <= lx1:
                p = ax.c2p(np.log10(e), CURVE_YLO)
                tk = Line(p, p + UP * 0.12, stroke_color=MUTED, stroke_width=2)
                lb = Text(s, font_size=18, color=MUTED).next_to(tk, DOWN, buff=0.08)
                ticks.add(VGroup(tk, lb))
        self.play(Create(ax), FadeIn(xlab), FadeIn(ylab), FadeIn(ticks), run_time=1.0)

        def poly(arr, color, width=5):
            pts = [ax.c2p(np.log10(e), arr[e]) for e in EP_PLOT]
            return VMobject().set_points_as_corners(pts).set_stroke(color, width)

        train_curve = poly(NN_TR, TRAIN_C)
        val_curve = poly(NN_VA, VAL_C)
        tl = Text("training loss", font_size=23, color=TRAIN_C, weight="BOLD")
        tl.next_to(ax.c2p(np.log10(4000), NN_TR[4000]), DOWN, buff=0.18)
        vl = Text("validation loss", font_size=23, color=VAL_C, weight="BOLD")
        vl.next_to(ax.c2p(np.log10(2500), NN_VA[2500]), UP, buff=0.2)

        self.play(Create(train_curve), FadeIn(tl), run_time=1.6)
        keep = Text("training loss keeps dropping…", font_size=24, color=TRAIN_C)
        keep.next_to(ax, UP, buff=0.18).shift(RIGHT * 0.2)
        self.play(FadeIn(keep, shift=UP * 0.1), run_time=0.5)
        self.beat(0.8)
        self.play(Create(val_curve), FadeIn(vl), run_time=1.8)
        turn = Text("…but validation loss turns back up.", font_size=24, color=VAL_C)
        turn.move_to(keep)
        self.play(ReplacementTransform(keep, turn), run_time=0.5)
        self.beat(0.8)

        # mark the sweet spot (early-stopping epoch) + the overfitting gap
        best_pt = ax.c2p(np.log10(NN_BEST), NN_VA[NN_BEST])
        star = Star(n=5, outer_radius=0.16, color=GOOD, fill_opacity=1, stroke_width=0).move_to(best_pt)
        vline = DashedLine(ax.c2p(np.log10(NN_BEST), CURVE_YLO), best_pt,
                           color=GOOD, stroke_width=2.5, dash_length=0.08)
        stoplab = chip(f"stop here · epoch ≈ {NN_BEST}", GOOD, fs=21).next_to(star, UP, buff=0.25)
        self.play(Create(vline), GrowFromCenter(star), FadeIn(stoplab, shift=DOWN * 0.1), run_time=0.8)
        self.play(Flash(star, color=GOOD, flash_radius=0.5), run_time=0.7)
        self.beat(0.6)

        # the overfitting gap at the end
        end_gap = VGroup(
            DashedLine(ax.c2p(lx1, NN_TR[-1]), ax.c2p(lx1, NN_VA[-1]),
                       color=BAD, stroke_width=3, dash_length=0.07),
            Text("overfit gap", font_size=19, color=BAD),
        )
        end_gap[1].next_to(end_gap[0], RIGHT, buff=0.12)
        self.play(Create(end_gap[0]), FadeIn(end_gap[1]), run_time=0.6)
        self.beat(0.6)

        # the takeaway numbers
        scoreboard = VGroup(
            Text(f"best validation loss  {NN_VAL_MIN:.2f}", font_size=23, color=GOOD),
            Text(f"if we don't stop      {NN_VAL_END:.2f}", font_size=23, color=BAD),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        scoreboard.to_corner(UR, buff=0.55).shift(DOWN * 0.1)
        self.play(FadeIn(scoreboard[0], shift=LEFT * 0.1), run_time=0.5)
        self.beat(0.3)
        self.play(FadeIn(scoreboard[1], shift=LEFT * 0.1), run_time=0.5)
        self.beat(0.5)
        punch = Text("Cross-validation tells you which parameters to keep — and when to stop.",
                     font_size=24, color=INK, weight="BOLD").to_edge(DOWN, buff=0.26)
        self.play(Write(punch), run_time=1.2)
        self.play(Circumscribe(punch, color=GOOD, run_time=1.2))
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 7 — Recap: the through-line
    # ====================================================================== #
    def scene_recap(self):
        head = self.section_header("RECAP", "The Through-Line", ACCENT)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.6)

        # the contrast we just watched — same recipe, two knobs → many
        contrast = VGroup(
            chip("linear · 2 parameters", W_C, fs=24, w=4.2),
            Text("→", font_size=36, color=MUTED),
            chip("network · 121 parameters", VAL_C, fs=24, w=4.9),
        ).arrange(RIGHT, buff=0.35).move_to([0, 1.95, 0])
        self.play(FadeIn(contrast[0], shift=RIGHT * 0.1), run_time=0.5)
        self.play(FadeIn(contrast[1]), FadeIn(contrast[2], shift=RIGHT * 0.1), run_time=0.5)
        self.beat(0.7)

        points = [
            ("Parameters are the knobs the model turns.", W_C),
            ("Training walks downhill on the loss — one gradient step at a time.", MODEL_C),
            ("Cross-validation keeps it honest: a stable fit, and when to stop.", GOOD),
        ]
        rows = VGroup()
        for txt, c in points:
            tick = make_tick(color=c, scale=0.95)
            t = Text(txt, font_size=26, color=INK)
            rows.add(VGroup(tick, t).arrange(RIGHT, buff=0.28))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to([0, -0.35, 0])
        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.2), run_time=0.7)
            self.beat(0.8)

        hook = Text("Same recipe — whether it's 2 knobs or 175 billion.",
                    font_size=28, color=ACCENT, weight="BOLD").to_edge(DOWN, buff=0.5)
        self.play(Write(hook), run_time=1.3)
        self.play(Circumscribe(hook, color=ACCENT, run_time=1.3))
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_setup()
        self.scene_descent()
        self.scene_cv_linear()
        self.scene_nn_arch()
        self.scene_nn_train()
        self.scene_cv_nn()
        self.scene_recap()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_PEBase):
    def construct(self):
        self.play_intro()


class Setup(_PEBase):
    def construct(self):
        self.scene_setup()


class Descent(_PEBase):
    def construct(self):
        self.scene_descent()


class CVLinear(_PEBase):
    def construct(self):
        self.scene_cv_linear()


class ManyKnobs(_PEBase):
    def construct(self):
        self.scene_nn_arch()


class TrainNet(_PEBase):
    def construct(self):
        self.scene_nn_train()


class CVNet(_PEBase):
    def construct(self):
        self.scene_cv_nn()


class Recap(_PEBase):
    def construct(self):
        self.scene_recap()


class Outro(_PEBase):
    def construct(self):
        self.play_outro()


class ParameterEvolution(_PEBase):
    """The whole ~3-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    ParameterEvolution().render()

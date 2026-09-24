"""Backpropagation — a house-style, no-voice-over explainer.

The power of backpropagation, told through a real 3D loss landscape:

    1. Intro      -- title card.
    2. Setup      -- a network's prediction depends on its weights; a wrong
                     prediction means a high loss. Learning = change the weights
                     to shrink the loss. With two weights we can *see* it.
    3. Landscape  -- 3D. The loss over two weights is a surface. The camera rises
                     from a top-down "map" into a tilted terrain: two low valleys
                     (good weights) with a ridge between them. Height = loss.
    4. Descent    -- 3D. To improve, step downhill: the negative gradient is the
                     steepest way down. A ball rolls down the real gradient-descent
                     path into a valley; a second ball, started elsewhere, rolls
                     into the other valley. Simple. But which way is downhill, for
                     millions of weights at once?
    5. Backward   -- 2D. Backpropagation. One forward pass gives the loss; one
                     backward pass sends the error back through the network,
                     multiplying the local derivative at each step (the chain
                     rule), and out fall every weight's gradient. Real numbers.
    6. Power      -- 2D. Why it matters. The slow way (nudge each weight and
                     re-run) costs one forward pass per weight. Backprop gets
                     every gradient in a single backward pass. That is the power.
    7. Recap      -- one card.
    8. Outro      -- thank-you card.

Camera policy (house rule `camera-control-only-for-3d`): only the two real 3D
scenes move the camera; every 2D scene is a static `Scene` whose motion comes
from the mobjects. Zooming a flat formula adds nothing.

All text is `Text` (Pango), never `Tex` — no LaTeX. Every number is real: the
loss surface, both descent paths, the tiny network's forward values AND backward
gradients, and the cost comparison all come from `assets/backprop.npz`, baked by
`generate_assets.py` (which `render.sh` runs automatically).

Env knobs:
    BP_QUICK=1   shorten every hold for a fast sanity render
    BP_DELAY=x   override the reading-hold multiplier
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from manim import *

# ---- crisp text: render big, scale down (Pango mangles small sizes) ------- #
# MANDATORY shadow (manim-explainer SKILL §2). Must be defined before any use.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("BP_QUICK") == "1"
DELAY = float(os.environ.get("BP_DELAY", "0.3" if QUICK else "2.3"))
END_HOLD = 0.2 if QUICK else 2.0

# ---- palette (shared house style) ---------------------------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / axes
GRID = "#232A38"        # faint gridlines / panel fills
FAINT = "#3A4152"       # guides

GOOD = "#3DD68C"        # low loss / downhill / good weights (green)
FWD_C = "#5B8DEF"       # the forward pass / activations (blue)
LOSS_C = "#FF8C42"      # the loss (orange)
GRAD_C = "#C792EA"      # the backward pass / gradients (violet) — the hero signal
GOLD = "#FFD166"        # rule / highlight / mid loss
BAD = "#FF5C5C"         # high loss / error (red)


# ========================================================================== #
# Real numbers, baked once (see generate_assets.py). Loaded, never fabricated.
# ========================================================================== #
ROOT = Path(__file__).resolve().parent
_NPZ = ROOT / "assets" / "backprop.npz"
if not _NPZ.exists():
    raise SystemExit(
        "Missing assets/backprop.npz — run  python generate_assets.py  first "
        "(render.sh does this automatically)."
    )
_D = np.load(_NPZ)
XS, YS = _D["XS"], _D["YS"]
W1_MIN, W1_MAX = float(_D["W1_MIN"]), float(_D["W1_MAX"])
W2_MIN, W2_MAX = float(_D["W2_MIN"]), float(_D["W2_MAX"])
PATH, PATH2 = _D["PATH"], _D["PATH2"]
MIN_A, MIN_B = _D["MIN_A"], _D["MIN_B"]
MIN_LOSS = float(_D["MIN_LOSS"])
BW = {str(k): float(v) for k, v in zip(_D["BW_KEYS"], _D["BW_VALS"])}
DEMO_PARAMS = int(_D["DEMO_PARAMS"])
FD_PASSES = int(_D["FD_PASSES"])
BP_PASSES = int(_D["BP_PASSES"])
SPEEDUP = float(_D["SPEEDUP"])


def loss(w1, w2):
    """Real MSE of  f(x)=w2*tanh(w1*x)  over the baked dataset."""
    r = w2 * np.tanh(w1 * XS) - YS
    return float(np.mean(r * r))


def loss_grad(w1, w2):
    """Analytic [dL/dw1, dL/dw2] (backprop for the two-parameter model)."""
    t = np.tanh(w1 * XS)
    r = w2 * t - YS
    d = 2.0 * r / XS.size
    return np.array([float(np.sum(d * w2 * (1.0 - t * t) * XS)),
                     float(np.sum(d * t))])


def plain_gd(start, lr=0.10, steps=70):
    """Plain (no-momentum) gradient descent, so the gradient arrow drawn at each
    step is exactly the direction the ball then moves. Returns (steps+1, 2)."""
    w = np.array(start[:2], dtype=float)
    pts = [w.copy()]
    for _ in range(steps):
        w = w - lr * loss_grad(*w)
        pts.append(w.copy())
    return np.array(pts)


# steep, visibly-high starts that roll cleanly to each valley bottom
DESC_START_A = (1.8, 1.7)      # -> valley A (~1.6, 0.9)
DESC_START_B = (-1.8, -1.7)    # -> valley B (the mirror valley)


# Display-height transform: a smooth soft-cap so the towering sign-mismatch
# corners (loss ~6) don't dwarf the valleys and ridge. tanh is monotonic, so
# "downhill" is preserved exactly; it is near-linear where the action is (the
# valleys ~0, the ridge ~0.6, the trajectory) and only rounds off the far walls.
CAP = 1.6


def disp(l):
    return float(CAP * np.tanh(l / CAP))


# ---- fake diffuse shading -------------------------------------------------- #
# Cairo renders a Surface as flat-shaded polygons with NO lighting, which looks
# papery. We light it ourselves: multiply each face's colour-mapped fill by a
# diffuse term from that face's own normal against a fixed light direction. It is
# baked once at build time and stays correct as the camera orbits (the surface
# never moves), so the terrain gains real, readable relief.
_LIGHT = np.array([-0.62, -0.5, 0.95])
_LIGHT = _LIGHT / np.linalg.norm(_LIGHT)


def shade_surface(surf, ambient=0.34, strength=0.92, spec=0.55, shininess=14):
    """Diffuse + a soft specular sheen from each face's normal. Also strokes each
    face with its own shaded colour so the face seams blend into a smooth skin."""
    for face in surf:
        a = face.get_anchors()
        m = len(a)
        if m < 4:
            continue
        # a face is a quad sampled around its perimeter; take three real corners
        # (indices 0, m/4, m/2) so the two edge vectors are not colinear
        p0, p1, p2 = a[0], a[m // 4], a[m // 2]
        n = np.cross(p1 - p0, p2 - p0)
        ln = np.linalg.norm(n)
        if ln < 1e-9:
            continue
        n = n / ln
        if n[2] < 0:
            n = -n
        diff = max(0.0, float(np.dot(n, _LIGHT)))
        s = ambient + strength * diff + spec * (diff ** shininess)
        rgb = np.clip(color_to_rgb(face.get_fill_color()) * s, 0.0, 1.0)
        col = rgb_to_color(rgb)
        face.set_fill(col, opacity=1.0)
        face.set_stroke(col, width=0.7, opacity=1.0)
    return surf


# ========================================================================== #
# Small reusable pieces
# ========================================================================== #
def bullet(text, color=INK, fs=24, dot=GOLD, dot_r=0.06):
    d = Dot(radius=dot_r, color=dot)
    t = Text(text, font_size=fs, color=color)
    t.next_to(d, RIGHT, buff=0.22)
    d.align_to(t, UP).shift(DOWN * 0.11)
    return VGroup(d, t)


def neuron(label="", color=INK, r=0.40, fill=GRID, label_fs=24):
    c = Circle(radius=r, stroke_color=color, stroke_width=3,
               fill_color=fill, fill_opacity=0.95)
    if label:
        t = Text(label, font_size=label_fs, color=color).move_to(c)
        return VGroup(c, t)
    return VGroup(c)


# ========================================================================== #
# Shared, camera-agnostic helpers (used by both 2D and 3D scenes)
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

    def say(self, text, color=INK, fs=25, y=-3.42, weight=NORMAL):
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
# 2D base — static camera by design. Owns the intro/outro + 2D scenes.
# ========================================================================== #
class _BPBase(_Common, Scene):
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
        writer = Text("Created by Ptolémé", font_size=28, color=FWD_C)
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
            "Backpropagation",
            "How a network learns which way is downhill",
        )
        self.play(FadeOut(group), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=FWD_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.5)
        self.card_wait(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.1)
        self.card_wait(2.2)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 2 — a prediction depends on the weights; learning shrinks the loss
    # ====================================================================== #
    def scene_setup(self):
        header = self.section_header("Learning means changing the weights", GOOD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # tiny network: input -> hidden -> output
        xin = neuron("x", FWD_C).move_to([-4.7, 0.7, 0])
        hid = neuron("h", INK).move_to([-1.7, 0.7, 0])
        out = neuron("ŷ", INK).move_to([1.3, 0.7, 0])
        e1 = Arrow(xin.get_right(), hid.get_left(), buff=0.08, color=MUTED,
                   stroke_width=4, max_tip_length_to_length_ratio=0.14)
        e2 = Arrow(hid.get_right(), out.get_left(), buff=0.08, color=MUTED,
                   stroke_width=4, max_tip_length_to_length_ratio=0.14)
        w1l = Text("w1", font_size=24, color=GOLD).next_to(e1, UP, buff=0.12)
        w2l = Text("w2", font_size=24, color=GOLD).next_to(e2, UP, buff=0.12)
        net = VGroup(xin, hid, out, e1, e2, w1l, w2l)
        self.play(FadeIn(xin), run_time=0.4)
        self.play(GrowArrow(e1), FadeIn(w1l), FadeIn(hid), run_time=0.6)
        self.play(GrowArrow(e2), FadeIn(w2l), FadeIn(out), run_time=0.6)

        cap = self.say("A network turns its input into a prediction using its "
                       "weights.", color=MUTED)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.6)
        self.beat(1.4)

        # prediction vs target -> loss
        pred_box = VGroup(
            Text("prediction", font_size=20, color=MUTED),
            Text("0.80", font_size=34, color=INK, weight=BOLD),
        ).arrange(DOWN, buff=0.1).next_to(out, RIGHT, buff=0.9)
        tgt_box = VGroup(
            Text("target", font_size=20, color=MUTED),
            Text("0.50", font_size=34, color=GOOD, weight=BOLD),
        ).arrange(DOWN, buff=0.1).next_to(pred_box, RIGHT, buff=0.9)
        oarrow = Arrow(out.get_right(), pred_box.get_left(), buff=0.12, color=MUTED,
                       stroke_width=4, max_tip_length_to_length_ratio=0.2)
        self.play(GrowArrow(oarrow), FadeIn(pred_box), run_time=0.6)
        self.play(FadeIn(tgt_box, shift=LEFT * 0.1), run_time=0.5)

        cap2 = self.say("Here the prediction misses the target, so the loss is high.",
                        color=INK)
        loss_box = VGroup(
            Text("loss", font_size=22, color=LOSS_C, weight=BOLD),
            Text("0.09", font_size=40, color=LOSS_C, weight=BOLD),
        ).arrange(DOWN, buff=0.12).move_to([4.9, -1.15, 0])
        gap = BraceBetweenPoints(pred_box.get_bottom() + DOWN * 0.1,
                                 tgt_box.get_bottom() + DOWN * 0.1, direction=DOWN)
        self.play(ReplacementTransform(cap, cap2), GrowFromCenter(gap), run_time=0.7)
        self.play(FadeIn(loss_box, shift=UP * 0.1), run_time=0.6)
        self.play(Indicate(loss_box, color=LOSS_C, scale_factor=1.15), run_time=0.8)
        self.beat(1.8)

        cap3 = self.say("Training means adjusting the weights until the loss is as "
                        "small as it can be.", color=INK, weight=BOLD)
        self.play(ReplacementTransform(cap2, cap3),
                  Indicate(VGroup(w1l, w2l), color=GOLD, scale_factor=1.3),
                  run_time=1.0)
        self.beat(2.0)

        # collapse to "two weights -> a landscape"
        self.play(FadeOut(pred_box, tgt_box, oarrow, gap, loss_box),
                  net.animate.scale(0.8).move_to([-3.6, 0.9, 0]), run_time=0.9)
        pair = VGroup(
            Text("two weights", font_size=26, color=GOLD, weight=BOLD),
            Text("(w1, w2)", font_size=30, color=INK),
        ).arrange(DOWN, buff=0.16).move_to([3.0, 1.5, 0])
        axes_mini = Axes(x_range=[0, 1, 1], y_range=[0, 1, 1], x_length=2.4, y_length=2.4,
                         axis_config={"color": MUTED, "include_ticks": False,
                                      "tip_length": 0.14})
        axes_mini.move_to([3.0, -0.9, 0])
        axl = Text("w1", font_size=20, color=MUTED).next_to(axes_mini.x_axis, RIGHT, buff=0.1)
        ayl = Text("w2", font_size=20, color=MUTED).next_to(axes_mini.y_axis, UP, buff=0.1)
        cap4 = self.say("To picture this, keep just two weights. Every setting is a "
                        "point on a map.", color=INK)
        self.play(ReplacementTransform(cap3, cap4), FadeIn(pair),
                  Create(axes_mini), FadeIn(axl, ayl), run_time=1.0)
        self.beat(1.6)

        cap5 = self.say("The loss at each point is a height above the map. That gives "
                        "us a landscape.", color=GOOD, weight=BOLD)
        self.play(ReplacementTransform(cap4, cap5), run_time=0.8)
        self.beat(2.0)
        self.wipe()

    # ====================================================================== #
    # Scene 5 — backpropagation: the chain rule, run backward
    # ====================================================================== #
    def scene_backward(self):
        header = self.section_header("Backpropagation: the chain rule, backward",
                                     GRAD_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # --- the tiny network, laid out left -> right --------------------- #
        y0 = 1.15
        xin = neuron("x", FWD_C).move_to([-5.0, y0, 0])
        hid = neuron("h", INK).move_to([-1.5, y0, 0])
        out = neuron("ŷ", INK).move_to([2.0, y0, 0])
        lossn = RoundedRectangle(width=1.0, height=0.8, corner_radius=0.12,
                                 stroke_color=LOSS_C, stroke_width=3,
                                 fill_color=GRID, fill_opacity=0.95).move_to([5.2, y0, 0])
        losst = Text("L", font_size=26, color=LOSS_C, weight=BOLD).move_to(lossn)
        e1 = Arrow(xin.get_right(), hid.get_left(), buff=0.08, color=MUTED, stroke_width=4,
                   max_tip_length_to_length_ratio=0.13)
        e2 = Arrow(hid.get_right(), out.get_left(), buff=0.08, color=MUTED, stroke_width=4,
                   max_tip_length_to_length_ratio=0.13)
        e3 = Arrow(out.get_right(), lossn.get_left(), buff=0.08, color=MUTED, stroke_width=4,
                   max_tip_length_to_length_ratio=0.16)
        w1l = Text("w1", font_size=23, color=GOLD).next_to(e1, UP, buff=0.10)
        w2l = Text("w2", font_size=23, color=GOLD).next_to(e2, UP, buff=0.10)
        net = VGroup(xin, hid, out, lossn, losst, e1, e2, e3, w1l, w2l)
        self.play(LaggedStart(FadeIn(xin), GrowArrow(e1), FadeIn(hid), GrowArrow(e2),
                              FadeIn(out), GrowArrow(e3), FadeIn(lossn, losst),
                              lag_ratio=0.4, run_time=1.8),
                  FadeIn(w1l), FadeIn(w2l))
        self.beat(0.6)

        # --- forward pass: values populate above each node ---------------- #
        def fval(node, s):
            return Text(s, font_size=22, color=FWD_C, weight=BOLD).next_to(node, UP, buff=0.28)

        fx = fval(xin, f"x = {BW['x']:.2f}")
        fh = fval(hid, f"h = {BW['a1']:.2f}")
        fo = fval(out, f"ŷ = {BW['pred']:.2f}")
        fL = Text(f"L = {BW['L']:.2f}", font_size=22, color=LOSS_C, weight=BOLD).next_to(lossn, UP, buff=0.28)
        cap = self.say("The forward pass sends the input through the network and "
                       "computes the loss.", color=FWD_C)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.6)
        pulse = Dot(color=FWD_C, radius=0.11).move_to(xin.get_center())
        self.add(pulse)
        self.play(FadeIn(fx), run_time=0.4)
        self.play(pulse.animate.move_to(hid.get_center()), run_time=0.6, rate_func=linear)
        self.play(FadeIn(fh), run_time=0.4)
        self.play(pulse.animate.move_to(out.get_center()), run_time=0.6, rate_func=linear)
        self.play(FadeIn(fo), run_time=0.4)
        self.play(pulse.animate.move_to(lossn.get_center()), run_time=0.6, rate_func=linear)
        self.play(FadeIn(fL), FadeOut(pulse), run_time=0.4)
        self.beat(1.6)

        # --- backward pass: gradients flow right -> left ------------------ #
        # Clean vertical bands so nothing collides:
        #   nodes (y=1.15) -> seed (y=0.0) -> arrows (y=-0.7)
        #   -> multipliers (y=-1.05) -> gradient results (y=-1.75) -> caption
        cap2 = self.say("The backward pass sends the error back, multiplying the "
                        "local derivative at each step.", color=GRAD_C)
        self.play(ReplacementTransform(cap, cap2), run_time=0.7)

        # the error signal at the output, sitting just below the y-hat node
        g_seed = Text(f"dL/dŷ = {BW['dpred']:.2f}", font_size=22, color=GRAD_C, weight=BOLD)
        g_seed.next_to(out, DOWN, buff=0.55)
        self.play(FadeIn(g_seed, shift=DOWN * 0.1), run_time=0.6)
        self.beat(1.0)

        yb = -0.7  # the backward-arrow lane, well below the node row
        mid2 = 0.5 * (out.get_x() + hid.get_x())
        mid1 = 0.5 * (hid.get_x() + xin.get_x())
        b2 = Arrow([out.get_x(), yb, 0], [hid.get_x(), yb, 0], buff=0.18,
                   color=GRAD_C, stroke_width=5, max_tip_length_to_length_ratio=0.13)
        b1 = Arrow([hid.get_x(), yb, 0], [xin.get_x(), yb, 0], buff=0.18,
                   color=GRAD_C, stroke_width=5, max_tip_length_to_length_ratio=0.13)

        # w2's gradient: multiply the error by the value on that wire (h)
        m2 = Text("× h", font_size=21, color=INK).move_to([mid2, -1.05, 0])
        gw2 = Text(f"dL/dw2 = {BW['dw2']:.2f}", font_size=23, color=GRAD_C, weight=BOLD)
        gw2.move_to([mid2, -1.78, 0])
        self.play(GrowArrow(b2), run_time=0.7)
        self.play(FadeIn(m2, shift=UP * 0.08), run_time=0.4)
        self.play(FadeIn(gw2, shift=UP * 0.08), run_time=0.5)
        self.beat(1.4)

        # keep going back through the tanh and w1: the chain of local derivatives
        m1 = Text("× w2·(1 − h²)·x", font_size=21, color=INK).move_to([mid1, -1.05, 0])
        gw1 = Text(f"dL/dw1 = {BW['dw1']:.2f}", font_size=23, color=GRAD_C, weight=BOLD)
        gw1.move_to([mid1, -1.78, 0])
        self.play(GrowArrow(b1), run_time=0.7)
        self.play(FadeIn(m1, shift=UP * 0.08), run_time=0.4)
        self.play(FadeIn(gw1, shift=UP * 0.08), run_time=0.5)
        self.beat(1.2)

        cap3 = self.say("Each weight gets its own gradient from that chain of local "
                        "derivatives: the chain rule.", color=INK)
        self.play(ReplacementTransform(cap2, cap3),
                  Circumscribe(VGroup(m1, m2), color=GRAD_C, buff=0.15, run_time=1.6))
        self.beat(1.8)

        # --- takeaway: one forward, one backward = every gradient --------- #
        self.play(FadeOut(net, fx, fh, fo, fL, b1, b2, m1, m2, g_seed, gw1, gw2),
                  run_time=0.8)
        take = VGroup(
            Text("One forward pass gives the loss.", font_size=30, color=FWD_C, weight=BOLD),
            Text("One backward pass gives the gradient for every weight.",
                 font_size=30, color=GRAD_C, weight=BOLD),
        ).arrange(DOWN, buff=0.3).move_to([0, 0.6, 0])
        cap4 = self.say("Each gradient says which way, and how hard, to nudge its "
                        "weight to lower the loss.", color=INK, weight=BOLD)
        self.play(FadeIn(take[0], shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(take[1], shift=UP * 0.1), ReplacementTransform(cap3, cap4),
                  run_time=0.8)
        self.beat(2.2)
        self.wipe()

    # ====================================================================== #
    # Scene 6 — why it is powerful: one backward pass vs a pass per weight
    # ====================================================================== #
    def scene_power(self):
        header = self.section_header("Why it is powerful", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        cap = self.say("How else could you find the slope for every weight?",
                       color=MUTED)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.6)
        self.beat(1.2)

        # --- left panel: the slow way (finite differences) ---------------- #
        slow = VGroup(
            Text("The slow way", font_size=28, color=BAD, weight=BOLD),
            Text("Nudge one weight, run the whole", font_size=22, color=INK),
            Text("network again, and see if the loss", font_size=22, color=INK),
            Text("moved. Repeat for every weight.", font_size=22, color=INK),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        slow_box = SurroundingRectangle(slow, color=BAD, buff=0.3, corner_radius=0.12
                                        ).set_stroke(width=2).set_fill(GRID, 0.35)
        slow_p = VGroup(slow_box, slow).move_to([-3.55, 0.9, 0])

        fast = VGroup(
            Text("Backpropagation", font_size=28, color=GOOD, weight=BOLD),
            Text("One forward pass, then one", font_size=22, color=INK),
            Text("backward pass, and every", font_size=22, color=INK),
            Text("gradient falls out at once.", font_size=22, color=INK),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        fast_box = SurroundingRectangle(fast, color=GOOD, buff=0.3, corner_radius=0.12
                                        ).set_stroke(width=2).set_fill(GRID, 0.35)
        fast_p = VGroup(fast_box, fast).move_to([3.55, 0.9, 0])

        cap2 = self.say("The slow way re-runs the whole network once for every "
                        "single weight.", color=INK)
        self.play(FadeIn(slow_p, shift=RIGHT * 0.1), ReplacementTransform(cap, cap2),
                  run_time=0.9)
        self.beat(1.8)
        self.play(FadeIn(fast_p, shift=LEFT * 0.1), run_time=0.8)
        cap3 = self.say("Backpropagation gets all of them from a single backward "
                        "pass instead.", color=GOOD)
        self.play(ReplacementTransform(cap2, cap3), run_time=0.7)
        self.beat(1.8)

        # --- the number: a million-weight network ------------------------- #
        self.play(slow_p.animate.scale(0.82).to_edge(LEFT, buff=0.5),
                  fast_p.animate.scale(0.82).to_edge(RIGHT, buff=0.5), run_time=0.8)
        count = VGroup(
            Text(f"A network with {DEMO_PARAMS:,} weights", font_size=27, color=INK, weight=BOLD),
        ).move_to([0, 1.7, 0])
        rows = VGroup(
            VGroup(Text("slow way:", font_size=25, color=BAD),
                   Text(f"{FD_PASSES:,} passes", font_size=25, color=BAD, weight=BOLD)
                   ).arrange(RIGHT, buff=0.3),
            VGroup(Text("backprop:", font_size=25, color=GOOD),
                   Text(f"{BP_PASSES} passes", font_size=25, color=GOOD, weight=BOLD)
                   ).arrange(RIGHT, buff=0.3),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.28).move_to([0, 0.4, 0])
        cap4 = self.say("For a network with a million weights, that is a million "
                        "re-runs versus one.", color=INK)
        self.play(FadeIn(count, shift=DOWN * 0.1), ReplacementTransform(cap3, cap4),
                  run_time=0.8)
        self.play(LaggedStart(FadeIn(rows[0], shift=RIGHT * 0.1),
                              FadeIn(rows[1], shift=RIGHT * 0.1), lag_ratio=0.6, run_time=1.2))
        self.beat(1.4)

        punch = Text(f"about {SPEEDUP:,.0f}× less work, for the same gradient",
                     font_size=27, color=GOLD, weight=BOLD)
        punch.move_to([0, -1.0, 0])
        self.play(Write(punch), run_time=1.0)
        self.play(Flash(punch, color=GOLD, line_length=0.2, num_lines=16, flash_radius=1.6),
                  run_time=0.8)
        self.beat(1.6)

        cap5 = self.say("That single backward pass is what makes training networks "
                        "with billions of weights possible.", color=INK, weight=BOLD)
        self.play(ReplacementTransform(cap4, cap5), run_time=0.8)
        self.beat(2.2)
        self.wipe()

    # ====================================================================== #
    # Scene 7 — recap card
    # ====================================================================== #
    def scene_recap(self):
        title = Text("Backpropagation, in one card", font_size=40, color=INK, weight="BOLD")
        title.to_edge(UP, buff=0.6)
        rule = Line(title.get_left(), title.get_right()).next_to(title, DOWN, buff=0.14)
        rule.set_stroke(GOLD, 3)
        self.play(Write(title), Create(rule), run_time=1.1)
        self.beat(0.5)

        points = [
            ("The loss over the weights is a landscape; learning walks downhill.", GOOD),
            ("The gradient is the steepest way down: which way to nudge each weight.", GOLD),
            ("Backprop is the chain rule run backward through the network.", GRAD_C),
            ("One forward pass, one backward pass, and every gradient falls out.", FWD_C),
            ("That efficiency is what lets us train enormous networks.", LOSS_C),
        ]
        rows = VGroup(*[bullet(t, fs=25, dot=c, dot_r=0.065) for t, c in points])
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.34)
        rows.next_to(rule, DOWN, buff=0.7)
        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.15), run_time=0.55)
            self.beat(0.9)
        self.beat(0.7)

        punch = Text("The algorithm that makes deep learning learn.",
                     font_size=27, color=INK, weight=BOLD, slant=ITALIC)
        punch.next_to(rows, DOWN, buff=0.55)
        self.play(FadeIn(punch, shift=UP * 0.1), run_time=0.7)
        self.beat(2.2)
        self.wipe()


# ========================================================================== #
# 3D mixin — the loss landscape, its camera, and the fixed-in-frame HUD.
# Shared by the two 3D scenes (Landscape, Descent). Camera control lives here
# and ONLY here (house rule camera-control-only-for-3d).
# ========================================================================== #
class _ValleyMixin:
    def make_axes(self):
        axes = ThreeDAxes(
            x_range=[W1_MIN, W1_MAX, 1.3], y_range=[W2_MIN, W2_MAX, 0.9],
            z_range=[0, CAP, 0.4],
            x_length=6.0, y_length=4.2, z_length=2.7,
            axis_config={"stroke_color": MUTED, "stroke_width": 2},
        )
        return axes

    def make_surface(self, axes, res=None):
        if res is None:
            res = (30, 22) if QUICK else (72, 52)
        surf = Surface(
            lambda u, v: axes.c2p(u, v, disp(loss(u, v))),
            u_range=[W1_MIN, W1_MAX], v_range=[W2_MIN, W2_MAX], resolution=res,
        )
        # smooth (no facet grid) + a rich multi-stop loss ramp; then hand-light it
        surf.set_style(fill_opacity=1.0, stroke_width=0)
        surf.set_fill_by_value(
            axes=axes,
            colorscale=[(GOOD, 0.0), ("#8FD94A", 0.26 * CAP), (GOLD, 0.52 * CAP),
                        ("#FF9E4A", 0.76 * CAP), (BAD, CAP)],
            axis=2,
        )
        shade_surface(surf)
        return surf

    def surf_point(self, axes, w1, w2, lift=0.0):
        return axes.c2p(w1, w2, disp(loss(w1, w2)) + lift)

    # ---- active gradient-descent pieces ---------------------------------- #
    def grad_arrow(self, axes, w, lift=0.2):
        """A bright arrow floating just above the surface, pointing along the
        negative gradient (the steepest way down) = the direction the ball steps.
        Its length scales with the gradient magnitude (a magnified version of the
        real step), clamped so it never overshoots the valley onto the far slope."""
        g = loss_grad(w[0], w[1])
        gm = float(np.linalg.norm(g)) + 1e-9
        length = float(np.clip(0.45 * gm, 0.2, 0.6))
        d = -g / gm
        end = (w[0] + length * d[0], w[1] + length * d[1])
        return Arrow3D(self.surf_point(axes, w[0], w[1], lift),
                       self.surf_point(axes, end[0], end[1], lift),
                       color="#C79BFF", thickness=0.04, base_radius=0.12)

    def step_path(self, axes, w0, w1, lift=0.11):
        return VMobject().set_points_as_corners(
            [self.surf_point(axes, w0[0], w0[1], lift),
             self.surf_point(axes, w1[0], w1[1], lift)])

    def roll_path(self, axes, wlist, lift=0.11):
        return VMobject().set_points_smoothly(
            [self.surf_point(axes, w[0], w[1], lift) for w in wlist])

    def make_readout(self, val):
        panel = VGroup(
            Text("loss", font_size=22, color=LOSS_C, weight=BOLD),
            Text(f"{val:.2f}", font_size=40, color=INK, weight=BOLD),
        ).arrange(DOWN, buff=0.1).to_corner(UR, buff=0.55)
        return panel

    # ---- fixed-in-frame HUD helpers (2D overlay that ignores the orbit) --- #
    def _fix(self, *ms):
        self.add_fixed_in_frame_mobjects(*ms)
        for m in ms:
            self.remove(m)

    def show_hud(self, m, rt=0.6):
        self._fix(m)
        self.play(FadeIn(m), run_time=rt)

    def hud_swap(self, old, new, rt=0.6):
        self._fix(new)
        self.play(FadeOut(old), FadeIn(new), run_time=rt)

    def wipe3d(self, rt=0.8):
        self.wait(END_HOLD)
        if getattr(self, "_orbiting", False):
            self.stop_ambient_camera_rotation()
            self._orbiting = False
        for m in self.mobjects:
            m.clear_updaters()
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    def orbit(self, rate=0.055):
        self.begin_ambient_camera_rotation(rate=rate)
        self._orbiting = True

    def stop_orbit(self):
        if getattr(self, "_orbiting", False):
            self.stop_ambient_camera_rotation()
            self._orbiting = False


# ========================================================================== #
# Scene 3 — the loss landscape (3D). Reveal a top-down map, then rise into
# terrain. The first place the camera earns its keep.
# ========================================================================== #
class Landscape(_ValleyMixin, _Common, ThreeDScene):
    def construct(self):
        self.camera.background_color = BG
        axes = self.make_axes()
        surf = self.make_surface(axes)

        header = self.section_header("The loss landscape", GOOD)

        # start looking straight down: the surface reads as a coloured map
        self.set_camera_orientation(phi=0, theta=-90 * DEGREES, zoom=0.95)
        self.show_hud(header)
        self.play(FadeIn(surf), run_time=1.6)
        cap = self.say("Seen from above, this is the map of every setting of the two "
                       "weights.", color=MUTED)
        self.show_hud(cap)
        self.beat(1.6)

        cap2 = self.say("Green is a low loss and red is a high loss.", color=INK)
        self.hud_swap(cap, cap2)
        self.beat(1.6)

        # rise into a tilted 3/4 view: the relief appears
        cap3 = self.say("Now lift the map so the loss becomes the height.", color=INK)
        self.hud_swap(cap2, cap3)
        self.move_camera(phi=62 * DEGREES, theta=-52 * DEGREES, zoom=0.82, run_time=3.2)

        # billboard axis labels (legible once tilted)
        xl = Text("w1", font_size=26, color=INK).move_to(
            axes.x_axis.get_end() + np.array([0.35, 0, 0.2]))
        yl = Text("w2", font_size=26, color=INK).move_to(
            axes.y_axis.get_end() + np.array([0, 0.35, 0.2]))
        zl = Text("loss", font_size=24, color=LOSS_C, weight=BOLD).move_to(
            axes.z_axis.get_end() + np.array([0, -0.25, 0.5]))
        self.add_fixed_orientation_mobjects(xl, yl, zl)
        self.play(Create(axes), FadeIn(xl, yl, zl), run_time=1.2)
        self.beat(1.0)

        self.orbit(rate=0.06)
        cap4 = self.say("The low ground is where the weights are good. The high "
                        "ground is where they are bad.", color=INK)
        self.hud_swap(cap3, cap4)
        self.beat(2.0)

        # mark the two valleys
        va = self.surf_point(axes, MIN_A[0], MIN_A[1], lift=0.06)
        vb = self.surf_point(axes, MIN_B[0], MIN_B[1], lift=0.06)
        da = Dot3D(va, radius=0.11, color=GOOD)
        db = Dot3D(vb, radius=0.11, color=GOOD)
        la = Text("valley", font_size=22, color=GOOD, weight=BOLD).move_to(va + np.array([0, 0, 0.55]))
        lb = Text("valley", font_size=22, color=GOOD, weight=BOLD).move_to(vb + np.array([0, 0, 0.55]))
        self.add_fixed_orientation_mobjects(la, lb)
        self.play(FadeIn(da, db, scale=1.5), FadeIn(la, lb), run_time=0.9)
        cap5 = self.say("This landscape has two low valleys, with a ridge rising "
                        "between them.", color=GOOD, weight=BOLD)
        self.hud_swap(cap4, cap5)
        self.beat(2.2)

        cap6 = self.say("To learn, the network has to get from high ground down "
                        "into a valley.", color=INK, weight=BOLD)
        self.hud_swap(cap5, cap6)
        self.beat(2.0)
        self.wipe3d()


# ========================================================================== #
# Scene 4 — gradient descent (3D). A ball rolls down the real path into a
# valley; a second ball rolls into the other valley. Then the hook: which way
# is downhill, for millions of weights?
# ========================================================================== #
class Descent(_ValleyMixin, _Common, ThreeDScene):
    def construct(self):
        self.camera.background_color = BG
        axes = self.make_axes()
        surf = self.make_surface(axes)
        header = self.section_header("Rolling downhill", GOLD)

        xl = Text("w1", font_size=26, color=INK).move_to(
            axes.x_axis.get_end() + np.array([0.35, 0, 0.2]))
        yl = Text("w2", font_size=26, color=INK).move_to(
            axes.y_axis.get_end() + np.array([0, 0.35, 0.2]))
        zl = Text("loss", font_size=24, color=LOSS_C, weight=BOLD).move_to(
            axes.z_axis.get_end() + np.array([0, -0.25, 0.5]))

        # re-establish the tilted terrain (a clean cut from the previous scene)
        self.set_camera_orientation(phi=62 * DEGREES, theta=-52 * DEGREES, zoom=0.82)
        self.show_hud(header)
        self.add_fixed_orientation_mobjects(xl, yl, zl)
        self.play(FadeIn(surf), Create(axes), FadeIn(xl, yl, zl), run_time=1.6)

        # the real (plain) gradient-descent trajectory this scene animates
        gdp = plain_gd(DESC_START_A, lr=0.10, steps=70)
        losses = [loss(w[0], w[1]) for w in gdp]
        ball = Dot3D(self.surf_point(axes, gdp[0][0], gdp[0][1], 0.12),
                     radius=0.16, color=INK)

        # a live loss readout, fixed in the top-right (updated at milestones)
        ro = self.make_readout(losses[0])
        self.show_hud(ro)

        def ro_to(val, rt=0.45):
            nonlocal ro
            new = self.make_readout(val)
            self._fix(new)
            self.play(FadeOut(ro), FadeIn(new), run_time=rt)
            ro = new

        # --- forward pass: drop the ball onto the surface; its height = loss - #
        p_land = self.surf_point(axes, gdp[0][0], gdp[0][1], 0.12)
        ball.move_to(p_land + np.array([0, 0, 1.5]))
        self.play(FadeIn(ball, scale=1.4), run_time=0.4)
        cap = self.say("Run the weights through the network to get the loss: the ball's "
                       "height on the surface. That is the forward pass.", color=MUTED)
        self.show_hud(cap)
        self.play(ball.animate.move_to(p_land), run_time=0.8,
                  rate_func=rate_functions.ease_in_quad)
        self.play(Flash(ball, color=INK, line_length=0.16, num_lines=12,
                        flash_radius=0.32), run_time=0.5)
        self.beat(1.8)

        # --- backward pass: the gradient, then the step (slow, explicit) ----- #
        arr = self.grad_arrow(axes, gdp[0])
        cap2 = self.say("The backward pass gives the gradient: the steepest way down "
                        "from here.", color=GRAD_C)
        self.hud_swap(cap, cap2)
        self.play(FadeIn(arr), run_time=0.7)
        self.beat(2.0)
        cap3 = self.say("Step along that gradient, and the loss drops.", color=INK)
        self.hud_swap(cap2, cap3)
        self.play(MoveAlongPath(ball, self.step_path(axes, gdp[0], gdp[1])),
                  FadeOut(arr), run_time=1.1)
        ro_to(losses[1])
        self.beat(1.6)

        self.orbit(rate=0.05)

        # --- steps 1..3: recompute the gradient and step, faster ------------- #
        cap4 = self.say("Every step: read the loss, compute the gradient, move down.",
                        color=INK)
        self.hud_swap(cap3, cap4)
        for k in range(1, 4):
            arrk = self.grad_arrow(axes, gdp[k])
            self.play(FadeIn(arrk), run_time=0.4)
            self.play(MoveAlongPath(ball, self.step_path(axes, gdp[k], gdp[k + 1])),
                      FadeOut(arrk), run_time=0.7)
        ro_to(losses[4])
        self.beat(1.2)

        # --- repeat many times: roll to the bottom --------------------------- #
        cap5 = self.say("Repeat this thousands of times, and the ball rolls to the "
                        "bottom.", color=INK)
        self.hud_swap(cap4, cap5)
        trail = self.roll_path(axes, gdp[4:]).set_stroke(GRAD_C, 5)
        self.play(Create(trail), MoveAlongPath(ball, trail), run_time=4.5, rate_func=linear)
        ro_to(losses[-1])
        self.beat(0.8)

        # --- mark the bottom ------------------------------------------------- #
        end = gdp[-1]
        etop = self.surf_point(axes, end[0], end[1], 0.10)
        gstem = Line(axes.c2p(end[0], end[1], 0), etop, color=GOLD, stroke_width=3)
        minlab = Text("lowest loss", font_size=22, color=GOLD, weight=BOLD).move_to(
            etop + np.array([0, 0, 0.55]))
        self.add_fixed_orientation_mobjects(minlab)
        self.play(Create(gstem), FadeIn(minlab), ball.animate.set_color(GOLD).scale(1.2),
                  run_time=0.9)
        cap6 = self.say("It settles at the lowest loss: the weights that fit the data "
                        "best.", color=GOLD, weight=BOLD)
        self.hud_swap(cap5, cap6)
        self.beat(2.0)
        self.play(FadeOut(ro), run_time=0.4)   # readout did its job for this run

        # --- a second ball, mirror start -> the other valley ----------------- #
        gdp2 = plain_gd(DESC_START_B, lr=0.10, steps=70)
        ball2 = Dot3D(self.surf_point(axes, gdp2[0][0], gdp2[0][1], 0.12),
                      radius=0.15, color=FWD_C)
        trail2 = self.roll_path(axes, gdp2).set_stroke(FWD_C, 4)
        cap7 = self.say("Start somewhere else and it rolls into the other valley. Both "
                        "are good answers.", color=FWD_C)
        self.hud_swap(cap6, cap7)
        self.play(FadeIn(ball2, scale=1.5), run_time=0.4)
        self.play(Create(trail2), MoveAlongPath(ball2, trail2), run_time=5.0,
                  rate_func=linear)
        self.beat(1.4)

        # --- side profile, then the hook into backprop ----------------------- #
        self.stop_orbit()
        cap8 = self.say("From the side you can see both valleys and the ridge between "
                        "them.", color=INK)
        self.hud_swap(cap7, cap8)
        self.move_camera(phi=78 * DEGREES, theta=-90 * DEGREES, zoom=0.9, run_time=3.0)
        self.beat(2.0)

        cap9 = self.say("Every step needs the gradient. Backpropagation is how we "
                        "compute it for millions of weights at once.", color=INK, weight=BOLD)
        self.hud_swap(cap8, cap9)
        self.beat(2.4)
        self.wipe3d()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_BPBase):
    def construct(self):
        self.play_intro()


class Setup(_BPBase):
    def construct(self):
        self.scene_setup()


class Backward(_BPBase):
    def construct(self):
        self.scene_backward()


class Power(_BPBase):
    def construct(self):
        self.scene_power()


class Recap(_BPBase):
    def construct(self):
        self.scene_recap()


class Outro(_BPBase):
    def construct(self):
        self.play_outro()


if __name__ == "__main__":
    # stitched order: Intro · Setup · Landscape · Descent · Backward · Power · Recap · Outro
    Setup().render()

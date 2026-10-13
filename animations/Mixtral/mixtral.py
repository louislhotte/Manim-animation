"""Mixtral of Experts — a ~5-minute explainer, house-style.

One model, eight experts, and every token picks just two. We build the Sparse
Mixture-of-Experts (SMoE) idea from the ground up, following

    "Mixtral of Experts" — Jiang et al., Mistral AI, 2024 (arXiv:2401.04088)

a decoder-only transformer that replaces each feed-forward block with 8 expert
FFNs and a router that activates only the top-2 per token. This is a sequel to
the Transformer-inference and KV-cache films and shares their palette and the
Q/K/V colour language.

Eight scenes plus the channel's intro/outro cards:

    1. Dense cost   -- a dense model runs every token through all its FFN weights
    2. The experts  -- split that block into 8 experts + a router (the SMoE layer)
    3. The router   -- G(x)=Softmax(TopK(x·Wg)); pick 2 of 8, blend by softmax
    4. Why two?     -- capacity is free, compute is per-expert; 2 is the knee
    5. Full scale   -- 32 layers, a fresh 2-of-8 each layer; 47B total / 13B active
    6. What experts learn -- not topic; syntactic & positional locality (grows w/ depth)
    7. The payoff   -- matches Llama-2-70B & GPT-3.5 at 13B active; Instruct MT-Bench 8.30
    8. (recap)      -- route smart, not hard

Everything uses ``Text`` (Pango) rather than ``Tex`` so it renders with no LaTeX
install. Scenes are exposed individually and as one continuous film
(``MixtralFilm``).

Env knobs:
    MX_QUICK=1   shorten every hold for a fast sanity render
    MX_DELAY=..  override the between-step pause multiplier
    MX_READ=..   override the absolute per-subtitle reading hold (default ~3 s)
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


QUICK = os.environ.get("MX_QUICK") == "1"
# Two separate pacing knobs so nothing feels rushed:
#   DELAY  scales the small pauses *between* animation steps (motion rhythm).
#   READ   is the absolute hold after a block of text lands, so there is always
#          time to actually read it (the viewer asked to be generous — ~3 s).
# ANIM_SLOW stretches every played animation so transitions aren't abrupt.
DELAY = float(os.environ.get("MX_DELAY", 0.28 if QUICK else 1.05))
READ = float(os.environ.get("MX_READ", 0.35 if QUICK else 3.0))
ANIM_SLOW = 1.0 if QUICK else 1.32
END_HOLD = 0.2 if QUICK else 2.4  # settle held on a finished scene before it wipes

# ---- palette (shared with the Transformer / KV-cache films) --------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
FAINT = "#3A4152"       # gridlines / dimmed
TOK = "#C792EA"         # tokens / embeddings (violet)
Q_C = "#5B8DEF"         # queries (blue)
K_C = "#2EC4B6"         # keys (teal)
V_C = "#FFD166"         # values (gold)
GATE = "#FFB454"        # the router / gating amber (Mistral-ish)
GOOD = "#3DD68C"        # chosen / cheap / good (green)
BAD = "#FF5C5C"         # wasted / dropped (red)
ACCENT = "#FFD166"      # gold accent (rules, key numbers)
DENSE = "#9AA4B8"       # "all the weights" grey

# Eight distinct, harmonious expert hues (categorical, readable on dark).
EXPERTS = [
    "#5B8DEF",  # 1 blue
    "#2EC4B6",  # 2 teal
    "#3DD68C",  # 3 green
    "#E6C34D",  # 4 amber
    "#FF8C42",  # 5 orange
    "#FF5C8A",  # 6 pink
    "#C792EA",  # 7 violet
    "#5FD0E0",  # 8 cyan
]

RNG = np.random.default_rng(7)

# A clean, well-hinted sans everywhere (Pango's serif default drops spaces at
# these sizes). Set on the *real* Text (we shadowed it above).
FONT = "Helvetica Neue"
_BaseText.set_default(font=FONT)


# ---- small reusable pieces ------------------------------------------------ #
def chip(text, color, w=2.3, h=0.95, fs=26, fill=0.14, tcolor=None, radius=0.14, weight=None):
    """A rounded, tinted box with a centered auto-fitting label. grp[0] is the box."""
    box = RoundedRectangle(
        width=w, height=h, corner_radius=radius,
        stroke_color=color, stroke_width=3,
        fill_color=color, fill_opacity=fill,
    )
    label = Text(text, font_size=fs, color=tcolor or INK, line_spacing=0.8,
                 weight=weight or NORMAL)
    if label.width > w - 0.3:
        label.scale((w - 0.3) / label.width)
    label.move_to(box)
    return VGroup(box, label)


def harrow(start, end, color=MUTED, sw=4, tip=0.2):
    return Arrow(
        start, end, buff=0.12, stroke_width=sw, color=color,
        max_tip_length_to_length_ratio=0.4, tip_length=tip,
    )


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


def tok_box(text, color=TOK, w=None, h=0.62, fs=22):
    """A small rounded token box, auto-sized to its label."""
    label = Text(text, font_size=fs, color=INK)
    w = w or max(0.85, label.width + 0.4)
    box = RoundedRectangle(width=w, height=h, corner_radius=0.12,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=0.16)
    label.move_to(box)
    return VGroup(box, label)


def vcells(n, color, cw=0.2, lo=0.2, hi=0.9, stroke=BG, sw=1.0, seed=None):
    """A vertical stack of squares whose fill opacity encodes a value in [0,1]."""
    rng = np.random.default_rng(seed) if seed is not None else RNG
    cells = VGroup()
    for _ in range(n):
        s = Square(side_length=cw, stroke_width=sw, stroke_color=stroke)
        s.set_fill(color, opacity=float(rng.uniform(lo, hi)))
        cells.add(s)
    cells.arrange(DOWN, buff=0)
    return cells


def expert_block(color, w=1.35, h=1.05, fs=22, label="", sub="FFN", fill=0.15,
                 glyph=True, sw=3):
    """An expert = a small feed-forward network, drawn as a rounded coloured box
    with a tiny 3→3 MLP glyph and a label. grp[0] is the box, grp[1] the label."""
    box = RoundedRectangle(width=w, height=h, corner_radius=0.12,
                           stroke_color=color, stroke_width=sw,
                           fill_color=color, fill_opacity=fill)
    parts = VGroup(box)
    lab = Text(label, font_size=fs, color=INK, weight="BOLD").move_to(box)
    if glyph:
        # a faint 2-layer perceptron glyph behind the label
        left = VGroup(*[Dot(radius=0.033, color=color) for _ in range(3)])
        left.arrange(DOWN, buff=0.11)
        right = VGroup(*[Dot(radius=0.033, color=color) for _ in range(2)])
        right.arrange(DOWN, buff=0.14)
        right.next_to(left, RIGHT, buff=0.34)
        edges = VGroup(*[Line(a.get_center(), b.get_center(),
                              stroke_width=0.8, stroke_color=color, stroke_opacity=0.5)
                         for a in left for b in right])
        g = VGroup(edges, left, right).set_opacity(0.55).scale(min(1.0, (h - 0.2) / 0.7))
        g.move_to(box).shift(UP * 0.16)
        lab.scale(0.9).move_to(box).shift(DOWN * 0.24)
        parts.add(g)
    parts.add(lab)
    return parts


def stat_tile(top, bottom, color=ACCENT, w=2.6, h=1.3, top_fs=40, bot_fs=20):
    """A number-on-top / label-below stat card."""
    box = RoundedRectangle(width=w, height=h, corner_radius=0.14,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=0.08)
    big = Text(top, font_size=top_fs, color=color, weight="BOLD")
    if big.width > w - 0.35:
        big.scale((w - 0.35) / big.width)
    small = Text(bottom, font_size=bot_fs, color=INK, line_spacing=0.78)
    if small.width > w - 0.3:
        small.scale((w - 0.3) / small.width)
    col = VGroup(big, small).arrange(DOWN, buff=0.14).move_to(box)
    return VGroup(box, col)


# ========================================================================== #
class _MixBase(Scene):
    def setup(self):
        self.camera.background_color = BG

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
        # the reading hold: ~3 s (× k) so every subtitle stays up long enough.
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

    def section_header(self, label, color=GATE):
        txt = Text(label, font_size=32, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(txt.get_left(), txt.get_right()).next_to(txt, DOWN, buff=0.12)
        line.set_stroke(color=color, width=3)
        return VGroup(txt, line)

    def bottomcap(self, s, color=INK, fs=23, buff=0.42, **kw):
        t = Text(s, font_size=fs, color=color, **kw)
        if t.width > 12.9:
            t.scale_to_fit_width(12.9)
        t.to_edge(DOWN, buff=buff)
        return t

    def cite(self, s):
        return Text(s, font_size=15, color=MUTED, slant=ITALIC).to_edge(DOWN, buff=0.16)

    def set_cap(self, s, color=INK, fs=23):
        """Transform the persistent bottom caption to new text (creates it lazily).

        Robust across the full film: if the previous caption was already wiped
        (so it is no longer on screen), fade a fresh one in rather than morphing a
        stale, removed mobject — which would otherwise diverge from the per-scene
        renders and risk a glyph-morph artefact.
        """
        new = self.bottomcap(s, color=color, fs=fs)
        cur = getattr(self, "_cap", None)
        if cur is None or cur not in self.mobjects:
            self._cap = new
            self.play(FadeIn(self._cap, shift=UP * 0.1), run_time=0.6)
        else:
            self.play(Transform(self._cap, new), run_time=0.5)
        return self._cap

    # ---- house-style intro / outro cards ---------------------------------- #
    def play_intro(self):
        header = Text("Mixtral of Experts", font_size=60, color=INK, weight="BOLD")
        header.set(width=min(9.2, header.width))
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GATE)
        writer = Text("Created by Ptolémé", font_size=28, color=Q_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        sub = Text("One model, eight experts — every token picks just two",
                   font_size=30, color=MUTED)
        sub.set(width=min(11.0, sub.width))
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.read(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        src = Text("Sparse Mixture-of-Experts · Mistral AI, 2024 · arXiv:2401.04088",
                   font_size=20, color=MUTED)
        src.next_to(writer, DOWN, buff=0.4)
        self.play(FadeIn(src), run_time=0.8)
        self.read(1.5)
        self.play(FadeOut(VGroup(header, writer, line, src)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GATE)
        writer = Text("Created by Ptolémé", font_size=28, color=Q_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = Text("Route smart, not hard: 47B of knowledge at 13B of compute.",
                     font_size=25, color=ACCENT)
        recap.set(width=min(11.5, recap.width))
        recap.next_to(writer, DOWN, buff=0.5)
        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap), run_time=0.8)
        self.read(1.6)
        self.play(FadeOut(VGroup(header, line, writer, recap)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 — The cost of a dense model
    # ====================================================================== #
    def scene_dense(self):
        title = Text("Bigger models know more — and cost more",
                     font_size=40, color=INK, weight="BOLD")
        self.play(Write(title), run_time=1.4)
        self.read(0.8)
        self.play(title.animate.scale(0.62).to_edge(UP, buff=0.42), run_time=0.7)

        # one transformer layer: attention -> feed-forward (the FFN is the focus)
        tok = tok_box("token", color=TOK, fs=20, h=0.58).move_to([-5.4, 0.4, 0])
        tlbl = Text("one token", font_size=16, color=MUTED).next_to(tok, UP, buff=0.14)
        attn = chip("Self-Attention", Q_C, w=2.5, h=0.9, fs=21).next_to(tok, RIGHT, buff=1.0)

        # dense FFN as a solid grid of weight cells
        cols, rows_ = 10, 6
        cw = 0.2
        grid = VGroup()
        for r in range(rows_):
            for c in range(cols):
                s = Square(cw, stroke_width=0.6, stroke_color=BG)
                s.set_fill(DENSE, opacity=0.16)
                s.move_to([c * cw, -r * cw, 0])
                grid.add(s)
        grid.move_to([2.4, 0.4, 0])
        ffn_box = SurroundingRectangle(grid, color=DENSE, buff=0.16, corner_radius=0.1)
        ffn_box.set_stroke(width=2.5)
        ffn_lbl = Text("Feed-Forward network", font_size=20, color=DENSE, weight="BOLD")
        ffn_lbl.next_to(ffn_box, UP, buff=0.16)
        a1 = harrow(tok.get_right(), attn.get_left(), sw=3)
        a2 = harrow(attn.get_right(), ffn_box.get_left(), sw=3)

        self.play(FadeIn(tok), FadeIn(tlbl), run_time=0.5)
        self.play(GrowArrow(a1), FadeIn(attn), run_time=0.6)
        self.play(GrowArrow(a2), FadeIn(ffn_box), FadeIn(ffn_lbl),
                  LaggedStart(*[FadeIn(s) for s in grid], lag_ratio=0.01, run_time=1.0))
        cap0 = self.bottomcap(
            "Every layer ends in a big feed-forward network — most of the model's weights live here.",
            fs=23)
        self.play(FadeIn(cap0), run_time=0.5)
        self.read(1.3)

        # the token lights up the WHOLE block -> full cost, every time
        pulse = grid.copy().set_fill(DENSE, opacity=0.85)
        cost = VGroup(
            Text("FLOPs / token", font_size=18, color=MUTED),
            Rectangle(width=2.9, height=0.34, stroke_color=DENSE, stroke_width=2,
                      fill_color=BAD, fill_opacity=0.0),
        ).arrange(DOWN, buff=0.12).next_to(ffn_box, DOWN, buff=0.7)
        bar_fill = Rectangle(width=2.86, height=0.30, stroke_width=0,
                             fill_color=BAD, fill_opacity=0.85)
        bar_fill.move_to(cost[1].get_left(), LEFT).shift(RIGHT * 0.02)
        self.play(FadeIn(cost), run_time=0.4)
        self.play(FadeIn(pulse), GrowFromEdge(bar_fill, LEFT), run_time=0.9)
        self.play(FadeOut(pulse), run_time=0.5)
        cap1 = self.bottomcap(
            "In a dense model, every token flows through all of those weights — the full price, every step.",
            color=INK, fs=23)
        self.play(Transform(cap0, cap1), run_time=0.5)
        self.read(1.6)

        # the tension: to know more you grow the FFN, and cost grows with it
        q = Text("What if each token only used the part it actually needs?",
                 font_size=27, color=ACCENT, weight="BOLD")
        q.move_to([0, -2.05, 0])
        self.play(FadeOut(cap0), FadeOut(cost), FadeOut(bar_fill), run_time=0.4)
        self.play(FadeIn(q, shift=UP * 0.12), run_time=0.8)
        self.read(1.7)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — Split the FFN into 8 experts + a router
    # ====================================================================== #
    def scene_experts(self):
        header = self.section_header("1 · Mixture of Experts", GATE)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # the same dense FFN block, small, on the left
        dense = VGroup()
        cw = 0.16
        for r in range(6):
            for c in range(8):
                s = Square(cw, stroke_width=0.5, stroke_color=BG)
                s.set_fill(DENSE, opacity=0.18)
                s.move_to([c * cw, -r * cw, 0])
                dense.add(s)
        dbox = SurroundingRectangle(dense, color=DENSE, buff=0.14, corner_radius=0.1).set_stroke(width=2.5)
        dgrp = VGroup(dense, dbox).move_to([-4.7, 0.9, 0])
        dcap = Text("one big FFN", font_size=18, color=DENSE).next_to(dgrp, DOWN, buff=0.2)
        self.play(FadeIn(dgrp), FadeIn(dcap), run_time=0.6)
        self.set_cap("Mixtral keeps the transformer as-is — but swaps this one block.", fs=23)
        self.read(1.2)

        # fan out into 8 experts on the right (4 x 2)
        experts = VGroup()
        for i in range(8):
            e = expert_block(EXPERTS[i], w=1.15, h=0.86, fs=18,
                             label=f"E{i+1}", glyph=True)
            experts.add(e)
        experts.arrange_in_grid(rows=2, cols=4, buff=(0.32, 0.5))
        experts.move_to([2.6, 0.85, 0])
        ebox = SurroundingRectangle(experts, color=GATE, buff=0.28, corner_radius=0.14).set_stroke(width=2)
        ebox_lbl = Text("Sparse Mixture of Experts", font_size=20, color=GATE, weight="BOLD")
        ebox_lbl.next_to(ebox, UP, buff=0.16)

        # transform the dense block into the 8 experts
        self.play(
            ReplacementTransform(dgrp.copy(), experts, run_time=1.2),
            FadeOut(dcap, run_time=0.4),
        )
        self.play(FadeIn(experts), Create(ebox), FadeIn(ebox_lbl), run_time=0.8)
        self.set_cap("Replace it with 8 experts — each a full feed-forward network of its own.", fs=23)
        self.read(1.5)

        # the router feeds them
        router = chip("Router", GATE, w=1.7, h=0.8, fs=22, weight="BOLD")
        router.next_to(dgrp, RIGHT, buff=0.55).align_to(experts, UP).shift(DOWN * 0.5)
        rlbl = Text("learned gate  Wg", font_size=15, color=MUTED).next_to(router, DOWN, buff=0.14)
        fan = VGroup(*[harrow(router.get_right(), experts[i][0].get_left(), color=MUTED, sw=2)
                       for i in range(8)])
        self.play(FadeOut(dgrp), FadeIn(router), FadeIn(rlbl), run_time=0.6)
        self.play(LaggedStart(*[GrowArrow(a) for a in fan], lag_ratio=0.06, run_time=1.0))
        self.set_cap("A small router reads each token and decides which experts should run.", fs=23)
        self.read(1.5)

        # the punchline: only a couple ever fire per token
        note = Text("Only a few experts fire per token — the rest stay dark.",
                    font_size=25, color=ACCENT, weight="BOLD")
        note.move_to([0.4, -2.1, 0])
        # dim 6 experts, light 2
        chosen = [1, 5]
        self.play(
            *[experts[i].animate.set_opacity(0.22) for i in range(8) if i not in chosen],
            *[fan[i].animate.set_stroke(opacity=0.15) for i in range(8) if i not in chosen],
            *[Indicate(experts[i], color=EXPERTS[i], scale_factor=1.12) for i in chosen],
            run_time=1.0,
        )
        self.play(FadeOut(self._cap), FadeIn(note, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(self.cite("Mixtral of Experts — Jiang et al., Mistral AI, 2024 (arXiv:2401.04088)")),
                  run_time=0.4)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — The router: pick 2 of 8, blend by softmax  (core mechanism)
    # ====================================================================== #
    def scene_router(self):
        self._cap = None
        header = self.section_header("2 · The router picks 2 of 8", GATE)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # token -> router (left)
        x = vcells(6, TOK, cw=0.2, seed=3).move_to([-6.0, 1.1, 0])
        xlbl = Text("token x", font_size=17, color=TOK, weight="BOLD").next_to(x, DOWN, buff=0.16)
        router = chip("Router", GATE, w=1.5, h=0.85, fs=22, weight="BOLD").move_to([-4.2, 1.1, 0])
        rw = Text("Wg", font_size=15, color=MUTED).next_to(router, DOWN, buff=0.12)
        a_in = harrow(x.get_right(), router.get_left(), sw=3)
        self.play(FadeIn(x), FadeIn(xlbl), run_time=0.5)
        self.play(GrowArrow(a_in), FadeIn(router), FadeIn(rw), run_time=0.6)
        self.set_cap("The router multiplies the token by a small matrix Wg to score all 8 experts.", fs=23)
        self.read(1.2)

        # 8 gate scores as horizontal bars in the middle
        logits = [2.9, 0.7, 1.1, 3.4, 0.5, 0.9, 1.8, 0.6]  # E1..E8; E4 & E1 win
        chosen = [3, 0]  # top-2 (0-indexed): E4 then E1
        maxl = max(logits)
        rows = VGroup()
        bars, names, vals = [], [], []
        gap = 0.5
        x0 = -2.55           # left edge of bars
        unit = 2.7           # bar length per logit unit... scaled below
        for i in range(8):
            y = 1.95 - i * gap
            nm = Text(f"E{i+1}", font_size=18, color=EXPERTS[i], weight="BOLD")
            nm.move_to([x0 - 0.5, y, 0])
            bw = max(0.05, (logits[i] / maxl) * unit)
            bar = RoundedRectangle(width=bw, height=0.32, corner_radius=0.06,
                                   stroke_width=0, fill_color=EXPERTS[i], fill_opacity=0.9)
            bar.move_to([x0 + bw / 2, y, 0])
            vv = Text(f"{logits[i]:.1f}", font_size=16, color=MUTED).next_to(bar, RIGHT, buff=0.14)
            names.append(nm); bars.append(bar); vals.append(vv)
            rows.add(VGroup(nm, bar, vv))
        gate_ttl = Text("gate scores  x·Wg", font_size=17, color=MUTED)
        gate_ttl.move_to([x0 + 0.4, 2.35, 0])
        self.play(FadeIn(gate_ttl), run_time=0.4)
        self.play(LaggedStart(*[GrowFromEdge(b, LEFT) for b in bars], lag_ratio=0.07, run_time=1.1),
                  LaggedStart(*[FadeIn(n) for n in names], lag_ratio=0.07, run_time=1.1),
                  LaggedStart(*[FadeIn(v) for v in vals], lag_ratio=0.07, run_time=1.1))
        self.read(1.0)

        # TopK: keep the top-2, send the other six to -infinity (dim to grey)
        self.set_cap("TopK keeps the two highest and sends the other six to −∞.", fs=23)
        drops = VGroup()
        for i in range(8):
            if i not in chosen:
                ninf = Text("−∞", font_size=16, color=FAINT).move_to(vals[i], LEFT)
                drops.add(ninf)
        self.play(
            *[bars[i].animate.set_fill(FAINT, opacity=0.5) for i in range(8) if i not in chosen],
            *[names[i].animate.set_color(FAINT) for i in range(8) if i not in chosen],
            *[FadeOut(vals[i]) for i in range(8) if i not in chosen],
            FadeIn(drops),
            run_time=0.9,
        )
        # highlight the two survivors
        halos = VGroup(*[SurroundingRectangle(rows[i], color=EXPERTS[i], buff=0.06,
                                              corner_radius=0.06).set_stroke(width=2.5)
                         for i in chosen])
        self.play(*[Create(h) for h in halos],
                  *[bars[i].animate.set_fill(EXPERTS[i], opacity=1.0) for i in chosen],
                  run_time=0.7)
        self.read(1.2)

        # softmax over the two survivors -> weights that sum to 1
        self.set_cap("A softmax over just those two turns their scores into weights that sum to 1.", fs=23)
        w_vals = np.exp([logits[i] for i in chosen])
        w_vals = w_vals / w_vals.sum()   # ~ (0.62, 0.38)
        wlabels = VGroup()
        for k, i in enumerate(chosen):
            wl = Text(f"g{k+1} = {w_vals[k]:.2f}", font_size=19, color=EXPERTS[i], weight="BOLD")
            wl.next_to(halos[k], RIGHT, buff=0.3)
            wlabels.add(wl)
        self.play(LaggedStart(*[FadeIn(w, shift=RIGHT * 0.1) for w in wlabels],
                              lag_ratio=0.2, run_time=0.8))
        self.read(1.2)

        # the two chosen experts run on x, then we blend their outputs by g1,g2.
        # Order the blocks to match the bar order (E1 above E4) so nothing crosses,
        # and put y to their right so the merge arrows never pass behind a block.
        self.set_cap("Only those two experts run. Blend their outputs by the weights → the layer's output.", fs=23)
        top_i, bot_i = sorted(chosen)                 # 0 (E1) above, 3 (E4) below
        halo_of = {chosen[0]: halos[0], chosen[1]: halos[1]}
        e_top = expert_block(EXPERTS[top_i], w=1.45, h=1.0, fs=20,
                             label=f"E{top_i+1}").move_to([4.5, 1.5, 0])
        e_bot = expert_block(EXPERTS[bot_i], w=1.45, h=1.0, fs=20,
                             label=f"E{bot_i+1}").move_to([4.5, 0.1, 0])
        fa1 = harrow(halo_of[top_i].get_right(), e_top.get_left(), color=EXPERTS[top_i], sw=3)
        fa2 = harrow(halo_of[bot_i].get_right(), e_bot.get_left(), color=EXPERTS[bot_i], sw=3)
        self.play(GrowArrow(fa1), GrowArrow(fa2), FadeIn(e_top), FadeIn(e_bot), run_time=0.8)

        # blend to y, sitting to the right: two converging arrows, no occlusion
        y_out = vcells(6, GATE, cw=0.2, seed=8).move_to([6.35, 0.8, 0])
        y_lbl = Text("y", font_size=24, color=GATE, weight="BOLD").next_to(y_out, UP, buff=0.12)
        m1 = harrow(e_top.get_right(), y_out.get_left(), color=EXPERTS[top_i], sw=3)
        m2 = harrow(e_bot.get_right(), y_out.get_left(), color=EXPERTS[bot_i], sw=3)
        self.play(GrowArrow(m1), GrowArrow(m2),
                  TransformFromCopy(e_top[0], y_out), FadeIn(y_lbl), run_time=0.9)
        self.read(1.3)

        # the formula, centered under everything
        self.play(FadeOut(self._cap), run_time=0.4)
        formula = Text("y  =  Σ  softmax( Top2( x·Wg ) )ᵢ · Eᵢ(x)",
                       font_size=30, color=INK,
                       t2c={"softmax": Q_C, "Top2": GATE, "Eᵢ(x)": GOOD})
        formula.move_to([0.2, -2.55, 0])
        if formula.width > 12.9:
            formula.scale_to_fit_width(12.9)
        self.play(Write(formula), run_time=1.3)
        self.read(1.9)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Why exactly two?  (the compute-vs-capacity knee)
    # ====================================================================== #
    def scene_why2(self):
        header = self.section_header("3 · Why exactly two?", GATE)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # 8 experts in a row up top
        experts = VGroup(*[expert_block(EXPERTS[i], w=1.05, h=0.8, fs=17,
                                        label=f"E{i+1}", glyph=False) for i in range(8)])
        experts.arrange(RIGHT, buff=0.22).move_to([0, 2.0, 0])
        self.play(LaggedStart(*[FadeIn(e) for e in experts], lag_ratio=0.06, run_time=0.9))

        # the 47B capacity "track" — fill = active params for the current k
        track_w = 8.0
        track = RoundedRectangle(width=track_w, height=0.52, corner_radius=0.1,
                                 stroke_color=DENSE, stroke_width=2.5, fill_opacity=0.0)
        track.move_to([0, 0.35, 0])
        cap_lbl = Text("total capacity = 47B parameters", font_size=18, color=DENSE)
        cap_lbl.next_to(track, UP, buff=0.18)
        fill = Rectangle(width=0.01, height=0.48, stroke_width=0,
                         fill_color=GOOD, fill_opacity=0.85)
        fill.move_to(track.get_left(), LEFT).shift(RIGHT * 0.02)
        active_lbl = Text("active / token", font_size=17, color=MUTED)
        active_lbl.next_to(track, DOWN, buff=0.55).shift(LEFT * 3.3)
        num_slot = active_lbl.get_center() + DOWN * 0.55
        self.play(Create(track), FadeIn(cap_lbl), FadeIn(active_lbl), FadeIn(fill), run_time=0.8)
        self.set_cap("Total capacity is fixed at 47B. What changes with k is how much runs per token.", fs=23)
        self.read(1.3)

        # sweep k = 1 → 2 → 8. The bracket LINE morphs smoothly, but the label and
        # the big number are *crossfaded* (never glyph-morphed — that garbles digits).
        # anchor points from the paper: k=2 → 13B active ; k=8 → 47B (dense).
        approx = {1: "≈7B", 2: "13B", 8: "47B"}
        frac = {1: 7 / 47, 2: 13 / 47, 8: 1.0}
        state = {"line": None, "lbl": None, "num": None}

        def line_for(k):
            lft = experts[0][0].get_left()[0]
            rgt = experts[k - 1][0].get_right()[0]
            y = experts.get_bottom()[1] - 0.16
            return Line([lft, y, 0], [rgt, y, 0]).set_stroke(GATE, 4)

        def go_k(k, hold=1.0):
            new_line = line_for(k)
            new_lbl = Text(f"k = {k}", font_size=20, color=GATE, weight="BOLD"
                           ).next_to(new_line, DOWN, buff=0.12)
            new_fill = Rectangle(width=max(0.02, frac[k] * (track_w - 0.06)), height=0.48,
                                 stroke_width=0, fill_color=GOOD, fill_opacity=0.85)
            new_fill.move_to(track.get_left(), LEFT).shift(RIGHT * 0.03)
            new_num = Text(approx[k], font_size=38, color=GOOD, weight="BOLD").move_to(num_slot)
            light = (
                [experts[i][0].animate.set_fill(EXPERTS[i], opacity=0.16).set_stroke(opacity=1.0)
                 for i in range(k)]
                + [experts[i][1].animate.set_opacity(1.0) for i in range(k)]
                + [experts[i].animate.set_opacity(0.2) for i in range(k, 8)]
            )
            if state["line"] is None:
                extras = [Create(new_line), FadeIn(new_lbl, shift=UP * 0.08), FadeIn(new_num)]
                state["line"] = new_line
            else:
                extras = [Transform(state["line"], new_line),
                          FadeOut(state["lbl"]), FadeIn(new_lbl, shift=UP * 0.08),
                          FadeOut(state["num"]), FadeIn(new_num)]
            self.play(*light, Transform(fill, new_fill), *extras, run_time=0.8)
            state["lbl"], state["num"] = new_lbl, new_num
            self.read(hold)
            return new_num

        # k = 1  (brittle)
        go_k(1, hold=0.4)
        v1 = self.bottomcap(
            "k = 1: cheapest, but brittle — one wrong pick can't be undone, and the router learns from a weak signal.",
            color=BAD, fs=22)
        self.play(Transform(self._cap, v1), run_time=0.5)
        self.read(1.6)

        # k = 2  (sweet spot)
        n2 = go_k(2, hold=0.3)
        check = make_tick(GOOD, sw=6, scale=1.3).next_to(n2, RIGHT, buff=0.4)
        v2 = self.bottomcap(
            "k = 2: blend two specialists, give the router a smooth signal — yet only a quarter of the experts run.",
            color=GOOD, fs=22)
        self.play(Transform(self._cap, v2), FadeIn(check, scale=1.3), run_time=0.6)
        self.read(1.8)

        # k = 8  (dense again)
        self.play(FadeOut(check), run_time=0.3)
        go_k(8, hold=0.3)
        v8 = self.bottomcap(
            "k = 8: all experts fire — maximum capacity, but it's just a dense 47B model again. No savings.",
            color=BAD, fs=22)
        self.play(Transform(self._cap, v8), run_time=0.5)
        self.read(1.6)

        # settle on the verdict: two is the knee of the curve
        go_k(2, hold=0.2)
        verdict = Text("Capacity is free to grow; compute is paid per expert.  Two is the knee of the curve.",
                       font_size=24, color=ACCENT, weight="BOLD")
        if verdict.width > 12.9:
            verdict.scale_to_fit_width(12.9)
        verdict.to_edge(DOWN, buff=0.42)
        self.play(Transform(self._cap, verdict), run_time=0.6)
        self.read(1.9)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — 32 layers: a fresh 2-of-8 at every layer
    # ====================================================================== #
    def scene_scale(self):
        header = self.section_header("4 · A fresh choice, every layer", GATE)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # a stack of layers on the left; a token rises through them, lighting a
        # different 2-of-8 at each. Show 6 layers + an ellipsis + "×32".
        shown = 6
        rowg = VGroup()
        cells_by_row = []
        cw = 0.26
        for r in range(shown):
            cells = VGroup()
            for i in range(8):
                s = RoundedRectangle(width=cw, height=cw, corner_radius=0.04,
                                     stroke_color=EXPERTS[i], stroke_width=1.4,
                                     fill_color=EXPERTS[i], fill_opacity=0.10)
                cells.add(s)
            cells.arrange(RIGHT, buff=0.1)
            lbl = Text(f"layer {r+1}", font_size=15, color=MUTED)
            lbl.next_to(cells, LEFT, buff=0.3)
            row = VGroup(lbl, cells)
            rowg.add(row)
            cells_by_row.append(cells)
        rowg.arrange(DOWN, buff=0.26, aligned_edge=LEFT)
        rowg.move_to([-3.2, 0.1, 0])
        dots = Text("⋮", font_size=30, color=MUTED).next_to(rowg, DOWN, buff=0.12)
        x32 = Text("× 32 layers", font_size=20, color=GATE, weight="BOLD").next_to(dots, DOWN, buff=0.18)
        self.play(LaggedStart(*[FadeIn(r) for r in rowg], lag_ratio=0.12, run_time=1.0),
                  FadeIn(dots), FadeIn(x32))
        self.set_cap("Every one of the 32 layers has its own 8 experts and its own router.", fs=23)
        self.read(1.3)

        # the token rides up, lighting a different pair each layer
        token = Dot(radius=0.12, color=TOK).next_to(rowg, DOWN, buff=0.05).shift(RIGHT * 0.5)
        token.move_to([rowg.get_right()[0] + 0.5, rowg.get_bottom()[1] - 0.1, 0])
        tok_tag = Text("token", font_size=15, color=TOK).next_to(token, RIGHT, buff=0.14)
        self.play(FadeIn(token), FadeIn(tok_tag), run_time=0.5)
        self.set_cap("A single token takes a different 2-of-8 at each layer — its own path through the model.", fs=23)
        picks = [(0, 3), (2, 5), (1, 6), (0, 4), (3, 7), (2, 5)]
        for r in range(shown - 1, -1, -1):     # bottom layer first (rises upward)
            cells = cells_by_row[r]
            self.play(token.animate.move_to([token.get_x(), cells.get_center()[1], 0]),
                      run_time=0.45)
            a, b = picks[r]
            self.play(
                cells[a].animate.set_fill(EXPERTS[a], opacity=0.95).set_stroke(width=2.5),
                cells[b].animate.set_fill(EXPERTS[b], opacity=0.95).set_stroke(width=2.5),
                run_time=0.4,
            )
            self.beat(0.35)
        self.play(FadeOut(VGroup(token, tok_tag)), run_time=0.4)
        self.read(1.2)

        # the numbers on the right — move the whole layers unit (grid + ⋮ + "×32")
        # together so its label never drifts into the combinatorics line below.
        self.play(VGroup(rowg, dots, x32).animate.scale(0.9).to_edge(LEFT, buff=0.55),
                  run_time=0.6)
        tiles = VGroup(
            stat_tile("47B", "total\nparameters", color=ACCENT, w=2.5, h=1.25),
            stat_tile("13B", "active\nper token", color=GOOD, w=2.5, h=1.25),
            stat_tile("8 × 32", "experts\n× layers", color=GATE, w=2.5, h=1.25),
            stat_tile("32k", "context\ntokens", color=Q_C, w=2.5, h=1.25),
        ).arrange_in_grid(rows=2, cols=2, buff=(0.35, 0.35))
        tiles.move_to([3.4, 0.35, 0])
        self.play(LaggedStart(*[FadeIn(t, shift=UP * 0.1) for t in tiles],
                              lag_ratio=0.12, run_time=1.1))
        self.set_cap("47B parameters of knowledge — but only 13B ever run for any single token.", fs=23)
        self.read(1.7)

        # combinatorial flourish
        combo = Text("28 pairs per layer  →  ~10⁴⁶ possible expert paths",
                     font_size=24, color=ACCENT, weight="BOLD")
        combo.move_to([0.2, -2.15, 0])
        self.play(FadeOut(self._cap), FadeIn(combo, shift=UP * 0.1), run_time=0.7)
        self.read(1.7)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 6 — What do the experts actually learn?
    # ====================================================================== #
    def scene_learn(self):
        header = self.section_header("5 · What do experts specialize in?", GATE)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # PART A — is it by topic?  Four domains, near-identical expert usage.
        qa = Text("A tempting guess: one expert for biology, one for code, one for math…",
                  font_size=24, color=INK).move_to([0, 2.35, 0])
        self.play(FadeIn(qa), run_time=0.6)
        self.read(1.2)

        domains = ["Code", "Biology", "Philosophy", "Math (DM)"]
        base = np.array([0.13, 0.11, 0.14, 0.12, 0.13, 0.12, 0.13, 0.12])
        clusters = VGroup()
        for d, name in enumerate(domains):
            usage = base + np.random.default_rng(20 + d).uniform(-0.012, 0.012, 8)
            if name.startswith("Math"):     # DM Mathematics is marginally different
                usage = usage.copy(); usage[4] += 0.05; usage[1] -= 0.03
            barset = VGroup()
            for i in range(8):
                h = max(0.05, usage[i] * 5.6)
                b = Rectangle(width=0.12, height=h, stroke_width=0,
                              fill_color=EXPERTS[i], fill_opacity=0.9)
                barset.add(b)
            barset.arrange(RIGHT, buff=0.05, aligned_edge=DOWN)
            axis = Line(barset.get_corner(DL) + LEFT * 0.05, barset.get_corner(DR) + RIGHT * 0.05,
                        stroke_color=MUTED, stroke_width=1.5)
            lbl = Text(name, font_size=17, color=INK).next_to(axis, DOWN, buff=0.14)
            clusters.add(VGroup(barset, axis, lbl))
        clusters.arrange(RIGHT, buff=0.85, aligned_edge=DOWN)
        clusters.move_to([0, 0.1, 0])
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in clusters],
                              lag_ratio=0.15, run_time=1.3))
        self.set_cap("But expert usage barely moves across domains — the histograms look the same.", fs=23)
        self.read(1.6)
        ans = Text("No clear specialization by subject.", font_size=25, color=BAD, weight="BOLD")
        ans.move_to([0, -2.15, 0])
        self.play(FadeIn(ans, shift=UP * 0.1), run_time=0.6)
        self.read(1.5)

        self.play(FadeOut(VGroup(qa, clusters, ans)), FadeOut(self._cap), run_time=0.6)
        self._cap = None

        # PART B — it IS structured: syntactic + positional locality.
        qb = Text("The structure is syntactic and positional, not semantic.",
                  font_size=26, color=INK, weight="BOLD").move_to([0, 2.35, 0])
        self.play(FadeIn(qb), run_time=0.6)
        self.read(1.0)

        # a token strip: consecutive tokens often share an expert (same colour run)
        toks = ["def", "get", "_", "user", "(", "self", ",", "id", ")", ":"]
        runs = [0, 0, 4, 4, 6, 2, 6, 4, 6, 6]   # colour = assigned expert (locality)
        strip = VGroup()
        for w, e in zip(toks, runs):
            tb = tok_box(w, color=EXPERTS[e], fs=18, h=0.56)
            tb[0].set_fill(EXPERTS[e], opacity=0.28)
            strip.add(tb)
        strip.arrange(RIGHT, buff=0.14).move_to([0, 1.05, 0])
        self.play(LaggedStart(*[FadeIn(t, shift=UP * 0.1) for t in strip],
                              lag_ratio=0.1, run_time=1.1))
        strip_note = Text("colour = chosen expert · neighbours often repeat",
                          font_size=17, color=MUTED).next_to(strip, DOWN, buff=0.22)
        self.play(FadeIn(strip_note), run_time=0.5)
        self.read(1.2)

        # a small chart: same-expert-as-previous-token rises with layer depth
        ax_o = np.array([-3.7, -2.65, 0])
        ax_w, ax_h = 7.4, 1.7
        xax = Line(ax_o, ax_o + RIGHT * ax_w, stroke_color=MUTED, stroke_width=2)
        yax = Line(ax_o, ax_o + UP * ax_h, stroke_color=MUTED, stroke_width=2)
        base_y = ax_o[1] + (12.5 / 40.0) * ax_h    # random baseline 12.5%
        baseline = DashedLine([ax_o[0], base_y, 0], [ax_o[0] + ax_w, base_y, 0],
                              stroke_color=FAINT, stroke_width=2, dash_length=0.1)
        base_lbl = Text("random = 12.5%", font_size=14, color=FAINT).next_to(baseline, RIGHT, buff=0.1).shift(UP*0.02)
        # rising curve from ~14% (layer 0) to ~35% (layer 31)
        pts_pct = [14, 15, 17, 20, 23, 27, 30, 33, 35]
        pts = []
        for k, p in enumerate(pts_pct):
            xx = ax_o[0] + (k / (len(pts_pct) - 1)) * ax_w
            yy = ax_o[1] + (p / 40.0) * ax_h
            pts.append([xx, yy, 0])
        curve = VMobject().set_points_as_corners(pts).set_stroke(GATE, 4)
        dots = VGroup(*[Dot(p, radius=0.05, color=GATE) for p in pts])
        ylab = Text("same expert as\nprevious token", font_size=15, color=INK, line_spacing=0.7)
        ylab.next_to(yax, LEFT, buff=0.2).shift(UP * 0.3)
        xlab = Text("layer depth  →", font_size=15, color=MUTED).next_to(xax, DOWN, buff=0.16).shift(RIGHT * 1.6)
        self.play(Create(xax), Create(yax), FadeIn(ylab), FadeIn(xlab), run_time=0.7)
        self.play(Create(baseline), FadeIn(base_lbl), run_time=0.5)
        self.play(Create(curve), LaggedStart(*[GrowFromCenter(d) for d in dots],
                                             lag_ratio=0.08), run_time=1.3)
        self.set_cap("Neighbouring tokens keep hitting the same expert — a locality that grows with depth.",
                     fs=22)
        self.read(1.7)

        take = Text("Experts specialize by syntax & position — not by topic.",
                    font_size=24, color=ACCENT, weight="BOLD")
        take.move_to([2.6, 1.05, 0])
        if take.width > 5.4:
            take.scale_to_fit_width(5.4)
        self.play(FadeOut(strip_note), FadeOut(qb),
                  strip.animate.scale(0.8).move_to([2.6, 2.0, 0]),
                  run_time=0.6)
        self.play(FadeIn(take, shift=UP * 0.1), run_time=0.7)
        src = Text("routing analysis on The Pile — §5, Jiang et al. 2024",
                   font_size=15, color=MUTED, slant=ITALIC).next_to(take, DOWN, buff=0.45)
        if src.width > 5.6:
            src.scale_to_fit_width(5.6)
        self.play(FadeIn(src), run_time=0.4)
        self.read(1.7)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 7 — The payoff
    # ====================================================================== #
    def scene_results(self):
        header = self.section_header("6 · The payoff", GATE)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # active-parameter contrast chips
        chips = VGroup(
            chip("Mixtral 8×7B\n13B active", GOOD, w=3.0, h=1.05, fs=21, weight="BOLD"),
            chip("Llama 2 70B\n70B active", DENSE, w=3.0, h=1.05, fs=21, weight="BOLD"),
        ).arrange(RIGHT, buff=0.7).move_to([0, 2.05, 0])
        vs = Text("vs", font_size=22, color=MUTED).move_to(chips)
        self.play(FadeIn(chips[0], shift=RIGHT * 0.1), FadeIn(chips[1], shift=LEFT * 0.1),
                  FadeIn(vs), run_time=0.8)
        self.set_cap("Mixtral runs ~5× fewer active parameters than Llama 2 70B — and still matches or beats it.",
                     fs=23)
        self.read(1.4)

        # a compact grouped bar chart on three benchmarks
        benches = [("MMLU", 70.6, 69.9, 70.0), ("GSM8K", 58.4, 53.6, 57.1),
                   ("MBPP", 60.7, 49.8, 52.2)]
        series_c = [GOOD, DENSE, Q_C]
        series_n = ["Mixtral", "Llama 2 70B", "GPT-3.5"]
        chart = VGroup()
        gw = 3.4               # width per benchmark group
        bw = 0.42
        base_y = -1.4
        maxv = 80.0
        for gi, (name, *vals) in enumerate(benches):
            gx = -gw + gi * gw
            for si, v in enumerate(vals):
                h = (v / maxv) * 2.4
                bar = Rectangle(width=bw, height=h, stroke_width=0,
                                fill_color=series_c[si], fill_opacity=0.9)
                bar.move_to([gx + (si - 1) * (bw + 0.08), base_y + h / 2, 0])
                num = Text(f"{v:.1f}", font_size=14, color=INK).next_to(bar, UP, buff=0.06)
                chart.add(bar, num)
            blbl = Text(name, font_size=18, color=INK).move_to([gx, base_y - 0.28, 0])
            chart.add(blbl)
        axis = Line([-gw - 0.9, base_y, 0], [gw + 0.9, base_y, 0],
                    stroke_color=MUTED, stroke_width=2)
        legend = VGroup(*[
            VGroup(Square(0.2, stroke_width=0, fill_color=series_c[i], fill_opacity=0.9),
                   Text(series_n[i], font_size=16, color=INK)).arrange(RIGHT, buff=0.12)
            for i in range(3)
        ]).arrange(RIGHT, buff=0.5)
        legend.next_to(axis, DOWN, buff=0.55)
        self.play(Create(axis), run_time=0.4)
        self.play(LaggedStart(*[GrowFromEdge(m, DOWN) if isinstance(m, Rectangle) else FadeIn(m)
                               for m in chart], lag_ratio=0.04, run_time=1.5))
        self.play(FadeIn(legend), run_time=0.5)
        self.read(1.7)

        # instruct + open weights takeaways
        self.play(FadeOut(VGroup(chart, axis, legend)), run_time=0.5)
        rows = VGroup(
            Text("Mixtral 8×7B — Instruct scores 8.30 on MT-Bench,", font_size=25, color=INK, weight="BOLD"),
            Text("beating GPT-3.5 Turbo, Claude-2.1, Gemini Pro & Llama 2 70B-chat.",
                 font_size=23, color=INK),
            Text("Open weights, Apache 2.0.", font_size=23, color=ACCENT, weight="BOLD"),
        ).arrange(DOWN, buff=0.28).move_to([0, -0.7, 0])
        for r in rows:
            if r.width > 12.9:
                r.scale_to_fit_width(12.9)
        self.play(FadeIn(rows[0], shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(rows[1]), run_time=0.6)
        self.read(1.3)
        self.play(FadeIn(rows[2], shift=UP * 0.1), run_time=0.6)
        self.set_cap("Frontier quality at a fraction of the inference cost — and anyone can run it.", fs=23)
        self.read(1.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Closing takeaway (before the outro card)
    # ====================================================================== #
    def scene_recap(self):
        lines = VGroup(
            Text("Mixtral, in one breath:", font_size=30, color=MUTED),
            Text("Split every feed-forward block into 8 experts,", font_size=32, color=INK, weight="BOLD"),
            Text("let a router pick the best 2 for each token.", font_size=32, color=INK, weight="BOLD"),
            Text("47B of knowledge, 13B of compute — route smart, not hard.",
                 font_size=26, color=ACCENT),
        ).arrange(DOWN, buff=0.34)
        for m in lines:
            if m.width > 12.9:
                m.scale_to_fit_width(12.9)
        self.play(FadeIn(lines[0]), run_time=0.6)
        self.read(0.5)
        self.play(Write(lines[1]), run_time=1.0)
        self.play(Write(lines[2]), run_time=1.0)
        self.read(1.1)
        self.play(FadeIn(lines[3], shift=UP * 0.12), run_time=0.8)
        self.read(1.7)
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_dense()
        self.scene_experts()
        self.scene_router()
        self.scene_why2()
        self.scene_scale()
        self.scene_learn()
        self.scene_results()
        self.scene_recap()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_MixBase):
    def construct(self):
        self.play_intro()


class Dense(_MixBase):
    def construct(self):
        self.scene_dense()


class Experts(_MixBase):
    def construct(self):
        self.scene_experts()


class Router(_MixBase):
    def construct(self):
        self.scene_router()


class WhyTwo(_MixBase):
    def construct(self):
        self.scene_why2()


class Scale(_MixBase):
    def construct(self):
        self.scene_scale()


class Learn(_MixBase):
    def construct(self):
        self.scene_learn()


class Results(_MixBase):
    def construct(self):
        self.scene_results()


class Recap(_MixBase):
    def construct(self):
        self.scene_recap()


class Outro(_MixBase):
    def construct(self):
        self.play_outro()


class MixtralFilm(_MixBase):
    """The whole ~5-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    MixtralFilm().render()

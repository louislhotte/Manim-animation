"""Transformer Inference — a ~3-minute explainer, house-style.

How a trained Transformer language model turns a prompt into text, one token at
a time. Grounded in the original architecture from

    "Attention Is All You Need" — Vaswani, Shazeer, Parmar, Uszkoreit, Jones,
    Gomez, Kaiser & Polosukhin, NeurIPS 2017  (arXiv:1706.03762)

We follow the *decoder* stack with masked self-attention — the basis of
GPT-style autoregressive inference — and walk the full forward path:

    1. Task        -- inference = next-token prediction (a loop over a frozen net)
    2. Embed       -- text -> tokens -> vectors, plus sinusoidal positional encoding
    3. Architecture-- the decoder stack: N x (Masked MHA -> Add&Norm -> FFN -> Add&Norm)
    4. Attention   -- scaled dot-product attention, the causal mask, multi-head
    5. Sample      -- final Linear -> softmax over the vocabulary -> pick a token
    6. Generate    -- append, feed back, repeat; the KV cache keeps it fast

Bookended by the channel's intro/outro cards. Everything uses ``Text`` (Pango)
rather than ``Tex`` so it renders with no LaTeX install and stays fast to iterate.

Scenes are exposed individually (``Task``, ``Embed``, ``Architecture``,
``Attention``, ``Sample``, ``Generate``, ``Intro``, ``Outro``) and as one
continuous film (``TransformerInference``).

Env knobs:
    TF_QUICK=1   shorten every hold for a fast sanity render
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

QUICK = os.environ.get("TF_QUICK") == "1"
# Single pacing knob: every on-screen "hold" is scaled by DELAY. QUICK collapses
# the holds for fast iteration; otherwise it sets the reading rhythm so the whole
# film lands near three minutes. Intro/outro cards use their own fixed rhythm.
# TF_DELAY overrides the value (used to tune the total runtime).
DELAY = float(os.environ.get("TF_DELAY", 0.28 if QUICK else 1.8))

# ---- palette -------------------------------------------------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
TOK = "#C792EA"         # tokens / embeddings (violet)
POS = "#8A7CFF"         # positional encoding (indigo)
Q_C = "#5B8DEF"         # queries (blue)
K_C = "#2EC4B6"         # keys (teal)
V_C = "#FFD166"         # values (gold)
ATTN = "#FF8C42"        # attention weights / logits (orange)
MODEL_C = "#FFD166"     # the model core (gold)
GOOD = "#3DD68C"        # pass / chosen (green)
BAD = "#FF5C5C"         # masked / stop (red)
ACCENT = "#FFD166"

RNG = np.random.default_rng(7)

# Use a clean, well-hinted sans-serif everywhere. Pango's serif default drops the
# spaces between words at these sizes ("across tokens" -> "acrosstokens"); setting
# a real font fixes the kerning and gives plain, standard-looking text.
FONT = "Helvetica Neue"
Text.set_default(font=FONT)


# ---- small reusable pieces ------------------------------------------------ #
def chip(text, color, w=2.3, h=0.95, fs=26, fill=0.14, tcolor=None, radius=0.14):
    """A rounded, tinted box with a centered auto-fitting label. grp[0] is the box."""
    box = RoundedRectangle(
        width=w, height=h, corner_radius=radius,
        stroke_color=color, stroke_width=3,
        fill_color=color, fill_opacity=fill,
    )
    label = Text(text, font_size=fs, color=tcolor or INK, line_spacing=0.8)
    if label.width > w - 0.3:
        label.scale((w - 0.3) / label.width)
    label.move_to(box)
    return VGroup(box, label)


def harrow(start, end, color=MUTED, sw=4):
    return Arrow(
        start, end, buff=0.12, stroke_width=sw, color=color,
        max_tip_length_to_length_ratio=0.18, tip_length=0.2,
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


def dot_label(text, color, fs=24):
    d = Dot(radius=0.08, color=color)
    t = Text(text, font_size=fs, color=INK).next_to(d, RIGHT, buff=0.2)
    return VGroup(d, t)


def tok_box(text, color=TOK, w=None, h=0.7, fs=24):
    """A small rounded token box, auto-sized to its label."""
    label = Text(text, font_size=fs, color=INK)
    w = w or max(0.85, label.width + 0.4)
    box = RoundedRectangle(width=w, height=h, corner_radius=0.12,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=0.16)
    label.move_to(box)
    return VGroup(box, label)


def mtext(parts, base_fs=32):
    """Assemble an inline 'formula' from ``Text`` pieces — no LaTeX needed.

    Each part is ``(s, role[, color])`` with role in {"b" base, "^" super, "_" sub}.
    Supers/subs attach to the previous base, so ``K`` then ``("T","^")`` reads Kᵀ.
    """
    grp = VGroup()
    last_base = None
    for p in parts:
        s, role = p[0], p[1]
        col = p[2] if len(p) > 2 else INK
        if role == "b":
            m = Text(s, font_size=base_fs, color=col)
            if len(grp) > 0:
                m.next_to(grp, RIGHT, buff=0.05, aligned_edge=DOWN)
            grp.add(m)
            last_base = m
        else:
            m = Text(s, font_size=int(base_fs * 0.6), color=col)
            anchor = last_base if last_base is not None else grp
            m.next_to(anchor, RIGHT, buff=0.02)
            m.align_to(anchor, UP if role == "^" else DOWN)
            grp.add(m)
    return grp


def vec_col(vals, color=V_C, cw=0.3, stroke=MUTED):
    """A vertical stack of squares whose opacity encodes each value in [0,1]."""
    cells = VGroup()
    for v in vals:
        s = Square(side_length=cw, stroke_width=1, stroke_color=stroke)
        s.set_fill(color, opacity=float(0.15 + 0.8 * np.clip(v, 0, 1)))
        cells.add(s)
    cells.arrange(DOWN, buff=0)
    return cells


def prob_bars(items, unit=4.0, fs=22, color=ATTN, gap=0.52):
    """Right-aligned labels + horizontal probability bars + value readouts."""
    grp = VGroup()
    labs = [Text(n, font_size=fs, color=INK) for n, _ in items]
    for i, ((n, p), lab) in enumerate(zip(items, labs)):
        y = -i * gap
        lab.move_to([-lab.width / 2 - 0.2, y, 0])
        bw = max(0.03, unit * p)
        bar = Rectangle(width=bw, height=0.36, stroke_width=0,
                        fill_color=color, fill_opacity=0.9)
        bar.move_to([0.2 + bw / 2, y, 0])
        val = Text(f"{p:.2f}", font_size=fs - 5, color=MUTED).next_to(bar, RIGHT, buff=0.15)
        grp.add(VGroup(lab, bar, val))
    return grp


# ========================================================================== #
class _TfBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # ---- timing helpers --------------------------------------------------- #
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.0))

    def reveal(self, items, hold=1.4, run_time=0.5, shift=RIGHT * 0.2):
        for m in items:
            self.play(FadeIn(m, shift=shift), run_time=run_time)
            self.beat(hold)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    def section_header(self, label, color=INK):
        txt = Text(label, font_size=34, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(txt.get_left(), txt.get_right()).next_to(txt, DOWN, buff=0.12)
        line.set_stroke(color=color, width=3)
        return VGroup(txt, line)

    def cite(self, short=True):
        s = ("Vaswani et al., “Attention Is All You Need,” NeurIPS 2017"
             if short else
             "“Attention Is All You Need” — Vaswani et al., NeurIPS 2017 (arXiv:1706.03762)")
        t = Text(s, font_size=15, color=MUTED, slant=ITALIC).to_edge(DOWN, buff=0.16)
        return t

    # ---- house-style intro / outro cards ---------------------------------- #
    def play_intro(self):
        header = Text("Transformer Inference", font_size=54, color=INK, weight="BOLD")
        header.set(width=min(9.8, header.width))
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=ATTN)
        writer = Text("Created by Ptolémé", font_size=28, color=Q_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        sub = Text("How an LLM writes text — one token at a time", font_size=34, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        src = Text("based on “Attention Is All You Need” · Vaswani et al., 2017",
                   font_size=22, color=MUTED)
        src.next_to(writer, DOWN, buff=0.4)
        self.play(FadeIn(src), run_time=0.8)
        self.card_wait(2.0)
        self.play(FadeOut(VGroup(header, writer, line, src)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=ATTN)
        writer = Text("Created by Ptolémé", font_size=28, color=Q_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.1)
        self.card_wait(2.2)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.3)
        self.card_wait(0.6)

    # ====================================================================== #
    # Scene 1 — Inference = next-token prediction
    # ====================================================================== #
    def scene_task(self):
        title = Text("Inference = next-token prediction", font_size=44, color=INK, weight="BOLD")
        self.play(Write(title), run_time=1.4)
        self.beat(0.9)
        self.play(title.animate.scale(0.62).to_edge(UP, buff=0.4), run_time=0.7)

        # the prompt tokens -> a box "Transformer" -> "?"
        words = ["Not", "all", "those", "who", "wander"]
        toks = VGroup(*[tok_box(w) for w in words]).arrange(RIGHT, buff=0.18)
        toks.next_to(title, DOWN, buff=0.75).shift(LEFT * 1.2)
        cap = Text("the tokens so far  (the prompt)", font_size=22, color=MUTED)
        cap.next_to(toks, UP, buff=0.25)
        attr = Text("a line by J.R.R. Tolkien", font_size=18, color=MUTED, slant=ITALIC)
        attr.next_to(toks, DOWN, buff=0.2).align_to(toks, RIGHT)
        self.play(LaggedStartMap(FadeIn, toks, shift=UP * 0.15, lag_ratio=0.25, run_time=1.4),
                  FadeIn(cap))
        self.play(FadeIn(attr), run_time=0.5)
        self.beat(1.0)

        model = chip("Transformer", MODEL_C, w=2.7, h=1.1, fs=26)
        model.next_to(toks, DOWN, buff=0.9).align_to(toks, LEFT).shift(RIGHT * 0.6)
        qbox = tok_box("?", color=ATTN, w=0.9)
        qbox.next_to(model, RIGHT, buff=1.4)
        a_in = harrow(toks.get_bottom(), model.get_top())
        a_out = harrow(model.get_right(), qbox.get_left(), color=ATTN)
        self.play(GrowArrow(a_in), FadeIn(model), run_time=0.8)
        self.play(GrowArrow(a_out), FadeIn(qbox), run_time=0.7)
        self.beat(0.8)

        # it outputs a probability distribution over the whole vocabulary
        dist = prob_bars([("are", 0.61), ("is", 0.18), ("were", 0.09), ("seem", 0.05)],
                         unit=3.0, fs=22)
        dist.next_to(qbox, RIGHT, buff=0.7).shift(UP * 0.1)
        explain = Text("a probability distribution over every token in the vocabulary",
                       font_size=22, color=INK).next_to(model, DOWN, buff=0.7)
        self.play(FadeIn(explain, shift=UP * 0.2), run_time=0.7)
        self.play(FadeOut(qbox), FadeOut(a_out),
                  LaggedStart(*[GrowFromEdge(r[1], LEFT) for r in dist],
                              *[FadeIn(r[0]) for r in dist], *[FadeIn(r[2]) for r in dist],
                              lag_ratio=0.12, run_time=1.6))
        self.beat(1.4)

        # pick one, append it, repeat -> the loop
        pick = SurroundingRectangle(dist[0], color=GOOD, buff=0.08, corner_radius=0.06)
        self.play(Create(pick), run_time=0.6)
        self.beat(0.8)
        loop = Text("pick a token  →  append it  →  predict again",
                    font_size=25, color=ACCENT).next_to(explain, DOWN, buff=0.7)
        self.play(FadeIn(loop, shift=UP * 0.2), run_time=0.8)
        self.beat(1.0)
        frozen = Text("The weights are frozen — no learning happens at inference.",
                      font_size=22, color=MUTED).next_to(loop, DOWN, buff=0.35)
        self.play(FadeIn(frozen), run_time=0.7)
        self.beat(0.6)
        self.play(FadeIn(self.cite()), run_time=0.5)
        self.beat(1.6)
        self.wipe()

    # ====================================================================== #
    # Scene 2 — Tokenize, embed, add position
    # ====================================================================== #
    def scene_embed(self):
        header = self.section_header("1 · From text to vectors", TOK)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # (a) text -> subword tokens with integer IDs
        sentence = Text("“Not all those who wander”", font_size=30, color=INK)
        sentence.next_to(header, DOWN, buff=0.55).to_edge(LEFT, buff=0.7)
        self.play(FadeIn(sentence), run_time=0.6)
        self.beat(0.6)

        pairs = [("Not", "3673"), ("all", "477"), ("those", "883"), ("who", "508"), ("wander", "11569")]
        cols = VGroup()
        for w, i in pairs:
            t = tok_box(w, color=TOK, fs=22, h=0.6)
            idt = Text(i, font_size=18, color=MUTED).next_to(t, DOWN, buff=0.14)
            cols.add(VGroup(t, idt))
        cols.arrange(RIGHT, buff=0.32).next_to(sentence, DOWN, buff=0.55).to_edge(LEFT, buff=0.7)
        tcap = Text("tokenizer  →  sub-word tokens + integer IDs   (BPE)",
                    font_size=20, color=MUTED).next_to(cols, DOWN, buff=0.3).align_to(cols, LEFT)
        self.play(LaggedStartMap(FadeIn, cols, shift=UP * 0.15, lag_ratio=0.2, run_time=1.4))
        self.play(FadeIn(tcap), run_time=0.5)
        self.beat(1.2)

        # (b) each ID indexes a row of the embedding matrix -> a d_model vector
        emb = VGroup(*[Square(0.16, stroke_width=0.5, stroke_color=MUTED).set_fill(
            TOK, opacity=float(RNG.uniform(0.1, 0.9))) for _ in range(8 * 12)])
        emb.arrange_in_grid(rows=12, cols=8, buff=0)
        emb.scale(1.0).to_edge(RIGHT, buff=2.2).shift(UP * 0.2)
        emb_lbl = Text("embedding\nmatrix", font_size=18, color=MUTED,
                       line_spacing=0.7).next_to(emb, UP, buff=0.18)
        vdim = Text("vocab", font_size=16, color=MUTED).rotate(PI / 2).next_to(emb, LEFT, buff=0.15)
        self.play(FadeIn(emb), FadeIn(emb_lbl), FadeIn(vdim), run_time=0.8)

        row = emb[3 * 8:(3 * 8) + 8]  # the row for token "on"/etc, illustrative
        vals = [RNG.uniform(0.15, 0.95) for _ in range(12)]
        vec = vec_col(vals, color=TOK, cw=0.28).next_to(emb, RIGHT, buff=1.1)
        vlab = Text("d = 512", font_size=18, color=MUTED).next_to(vec, DOWN, buff=0.18)
        a_lookup = harrow(emb.get_right(), vec.get_left(), color=TOK, sw=3)
        self.play(Indicate(row, color=ACCENT, scale_factor=1.1), run_time=0.7)
        self.play(GrowArrow(a_lookup), TransformFromCopy(row, vec), FadeIn(vlab), run_time=1.1)
        look_cap = Text("look up each ID  →  a 512-dim embedding vector",
                        font_size=20, color=INK).next_to(cols, DOWN, buff=0.3).align_to(cols, LEFT)
        self.play(FadeOut(tcap), FadeIn(look_cap), run_time=0.6)
        self.beat(1.4)

        # (c) attention is order-agnostic -> add a sinusoidal positional encoding
        self.play(FadeOut(VGroup(emb, emb_lbl, vdim, a_lookup)), run_time=0.5)
        vec_group = VGroup(vec, vlab)
        self.play(vec_group.animate.to_edge(RIGHT, buff=4.6).shift(UP * 0.1), run_time=0.6)

        pe = mtext([("PE(pos, 2i)   = sin( pos / 10000", "b", POS), ("2i/d", "^", POS), (" )", "b", POS)],
                   base_fs=24)
        pe2 = mtext([("PE(pos, 2i+1) = cos( pos / 10000", "b", POS), ("2i/d", "^", POS), (" )", "b", POS)],
                    base_fs=24)
        pe_grp = VGroup(pe, pe2).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        pe_grp.next_to(look_cap, DOWN, buff=0.55).to_edge(LEFT, buff=0.7)
        why = Text("Self-attention has no built-in sense of order,",
                   font_size=21, color=INK)
        why2 = Text("so we add a fixed positional signal to every token.",
                    font_size=21, color=INK)
        whys = VGroup(why, why2).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        whys.next_to(pe_grp, DOWN, buff=0.4).align_to(pe_grp, LEFT)
        self.play(FadeIn(pe_grp, shift=UP * 0.2), run_time=0.8)
        self.play(FadeIn(whys, shift=UP * 0.1), run_time=0.7)
        self.beat(1.0)

        # the iconic PE heatmap: positions x dims, value = sin/cos -> diagonal stripes
        P, Dn = 12, 16
        heat = VGroup()
        for pos in range(P):
            for i in range(Dn):
                if i % 2 == 0:
                    v = np.sin(pos / (10000 ** (i / Dn)))
                else:
                    v = np.cos(pos / (10000 ** ((i - 1) / Dn)))
                c = interpolate_color(ManimColor(POS), ManimColor(V_C), (v + 1) / 2)
                sq = Square(0.2, stroke_width=0).set_fill(c, opacity=0.95)
                heat.add(sq)
        heat.arrange_in_grid(rows=P, cols=Dn, buff=0)
        heat.to_edge(RIGHT, buff=1.6).shift(UP * 0.1)
        hlab = Text("positional encoding", font_size=18, color=MUTED).next_to(heat, UP, buff=0.16)
        self.play(FadeIn(heat, lag_ratio=0.002, run_time=1.2), FadeIn(hlab))
        self.beat(0.8)

        # summary band placed clearly BELOW the heatmap so nothing overlaps:
        #   token embedding  ⊕  positional encoding  =  input to the stack
        self.play(FadeOut(vec_group), run_time=0.4)
        ev = vec_col([RNG.uniform(0.2, 0.9) for _ in range(6)], color=TOK, cw=0.17)
        plus = Text("⊕", font_size=30, color=INK)
        pe_zoom = heat.copy().scale(0.30)
        eq = Text("=", font_size=30, color=INK)
        iv = vec_col([RNG.uniform(0.2, 0.9) for _ in range(6)], color=ACCENT, cw=0.17)
        comp = VGroup(ev, plus, pe_zoom, eq, iv).arrange(RIGHT, buff=0.3)
        elab = Text("embedding", font_size=14, color=MUTED).next_to(ev, DOWN, buff=0.14)
        plab = Text("position", font_size=14, color=MUTED).next_to(pe_zoom, DOWN, buff=0.14)
        ilab = Text("input to the stack", font_size=17, color=ACCENT).next_to(iv, DOWN, buff=0.14)
        comp_all = VGroup(comp, elab, plab, ilab).next_to(heat, DOWN, buff=0.5)
        # keep the row on-screen horizontally
        over = comp_all.get_right()[0] - 6.95
        if over > 0:
            comp_all.shift(LEFT * over)
        self.play(FadeIn(ev), FadeIn(elab), run_time=0.4)
        self.play(FadeIn(plus), FadeIn(pe_zoom), FadeIn(plab), run_time=0.5)
        self.play(FadeIn(eq), TransformFromCopy(VGroup(ev, pe_zoom), iv), FadeIn(ilab), run_time=0.7)
        self.beat(1.6)
        self.wipe()

    # ====================================================================== #
    # Scene 3 — The decoder stack (architecture)
    # ====================================================================== #
    def scene_arch(self):
        header = self.section_header("2 · The decoder stack", ATTN)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)
        hp = Text("N = 6 layers · d = 512 · h = 8 heads · d_ff = 2048   (Vaswani et al., 2017)",
                  font_size=19, color=MUTED)
        hp.next_to(header, DOWN, buff=0.28).to_edge(LEFT, buff=0.5)
        self.play(FadeIn(hp), run_time=0.5)

        # --- build the tall stack, bottom (input) -> top (output) ---------- #
        emb = chip("Token Embeddings  ⊕  Positional Encoding", TOK, w=5.4, h=0.6, fs=19)
        mha = chip("Masked Multi-Head Self-Attention", ATTN, w=4.9, h=0.66, fs=19)
        an1 = chip("Add & Norm", MUTED, w=4.9, h=0.4, fs=17)
        ffn = chip("Feed-Forward  (ReLU)", V_C, w=4.9, h=0.66, fs=19)
        an2 = chip("Add & Norm", MUTED, w=4.9, h=0.4, fs=17)
        inner = VGroup(mha, an1, ffn, an2).arrange(UP, buff=0.24)  # mha at the bottom

        block = SurroundingRectangle(inner, buff=0.26, color=INK, corner_radius=0.16)
        block.set_stroke(width=2)
        # two faint offset copies behind -> reads as a repeated stack (N layers)
        sh1 = block.copy().set_stroke(INK, width=2, opacity=0.28).shift(UR * 0.13)
        sh2 = block.copy().set_stroke(INK, width=2, opacity=0.16).shift(UR * 0.26)
        nlab = Text("× N", font_size=22, color=INK, weight="BOLD")

        lin = chip("Final Linear  (un-embed)", Q_C, w=4.9, h=0.56, fs=19)
        soft = chip("Softmax", GOOD, w=4.9, h=0.56, fs=19)
        probs = chip("next-token probabilities", ACCENT, w=4.9, h=0.56, fs=19)

        # arrange UP so the first element (emb) sits at the bottom, probs on top
        column = VGroup(emb, block, lin, soft, probs).arrange(UP, buff=0.42)
        # keep the decoder block's internals aligned inside the surrounding rect
        inner.move_to(block)
        stack = VGroup(sh2, sh1, block, inner, emb, lin, soft, probs)
        stack.scale_to_fit_height(5.7).move_to(LEFT * 1.4 + DOWN * 0.7)
        nlab.next_to(block, RIGHT, buff=0.1).align_to(block, UP).shift(DOWN * 0.12)

        # short arrows up the spine (small buff so the head stays visible)
        def up_arrow(a, b):
            return Arrow(a.get_top(), b.get_bottom(), buff=0.05, stroke_width=3,
                         color=MUTED, max_tip_length_to_length_ratio=0.5, tip_length=0.13)
        spine = VGroup(
            up_arrow(emb, block), up_arrow(block, lin),
            up_arrow(lin, soft), up_arrow(soft, probs),
        )

        # reveal bottom -> top
        self.play(FadeIn(emb, shift=UP * 0.2), run_time=0.6)
        self.play(GrowArrow(spine[0]), FadeIn(VGroup(sh2, sh1, block)), FadeIn(nlab), run_time=0.8)
        self.beat(0.4)
        for m in (mha, an1, ffn, an2):
            self.play(FadeIn(m, shift=UP * 0.1), run_time=0.4)
        self.beat(0.3)

        # residual "skip" hooks around each sub-layer (the "Add"), on the left
        def skip(sub, addnorm):
            x = block.get_left()[0] + 0.12
            y0 = sub.get_bottom()[1]
            y1 = addnorm.get_center()[1]
            p = VMobject(stroke_color=GOOD, stroke_width=2.5)
            p.set_points_as_corners([
                np.array([sub.get_left()[0], y0, 0]),
                np.array([x, y0, 0]),
                np.array([x, y1, 0]),
                np.array([addnorm.get_left()[0], y1, 0]),
            ])
            return p
        res1, res2 = skip(mha, an1), skip(ffn, an2)
        self.play(Create(res1), Create(res2), run_time=0.7)
        self.beat(0.4)
        # continue up: Linear -> Softmax -> probabilities appear with their arrows
        self.play(LaggedStart(
            GrowArrow(spine[1]), FadeIn(lin, shift=UP * 0.1),
            GrowArrow(spine[2]), FadeIn(soft, shift=UP * 0.1),
            GrowArrow(spine[3]), FadeIn(probs, shift=UP * 0.1),
            lag_ratio=0.35, run_time=1.9))
        self.beat(0.5)

        # --- annotate each part on the right, with a dashed connector ------ #
        def note(anchor, text, color):
            t = Text(text, font_size=18, color=INK)
            t.move_to([1.2 + t.width / 2, anchor.get_center()[1], 0])
            d = Dot(radius=0.055, color=color).next_to(t, LEFT, buff=0.14)
            ln = DashedLine(anchor.get_right(), d.get_left(), stroke_width=1.5,
                            color=color, dash_length=0.06).set_opacity(0.5)
            return VGroup(ln, d, t)
        notes = [
            (mha, "mix information across tokens", ATTN),
            (an1, "residual + LayerNorm — keep signals stable", GOOD),
            (ffn, "transform each token  (512 → 2048 → 512)", V_C),
            (lin, "project to |vocab| logits  (tied to embeddings)", Q_C),
            (soft, "logits → a probability distribution", GOOD),
        ]
        for anchor, txt, col in notes:
            n = note(anchor, txt, col)
            self.play(FadeIn(n, shift=RIGHT * 0.12),
                      Indicate(anchor, color=col, scale_factor=1.04), run_time=0.7)
            self.beat(0.8)

        self.play(Circumscribe(block, color=ATTN, run_time=1.4))
        self.beat(1.6)
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Self-attention (the heart)
    # ====================================================================== #
    def scene_attention(self):
        header = self.section_header("3 · Self-attention", ATTN)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)
        sub = Text("every token looks at the others and mixes in what matters",
                   font_size=23, color=MUTED).next_to(header, DOWN, buff=0.3).to_edge(LEFT, buff=0.5)
        self.play(FadeIn(sub, shift=UP * 0.15), run_time=0.6)
        self.beat(0.5)

        # (a) each token -> Query, Key, Value via learned projections
        x = vec_col([RNG.uniform(0.2, 0.9) for _ in range(6)], color=TOK, cw=0.26)
        xlbl = Text("token\nvector", font_size=17, color=MUTED, line_spacing=0.7).next_to(x, DOWN, buff=0.16)
        xg = VGroup(x, xlbl).to_edge(LEFT, buff=1.2).shift(UP * 0.3)

        def proj(name, color, shift):
            # Q/K/V are shorter than the token vector — a nod to dₖ < d_model
            v = vec_col([RNG.uniform(0.2, 0.9) for _ in range(5)], color=color, cw=0.26)
            lbl = Text(name, font_size=20, color=color, weight="BOLD").next_to(v, RIGHT, buff=0.18)
            g = VGroup(v, lbl).next_to(xg, RIGHT, buff=2.1).shift(shift)
            wlab = Text(f"W{name[0]}", font_size=17, color=MUTED)
            ar = harrow(x.get_right(), v.get_left(), color=color, sw=3)
            # place along the arrow (not above its bbox) so the three don't collide
            wlab.move_to(ar.point_from_proportion(0.5)).shift(UP * 0.22)
            return g, ar, wlab

        self.play(FadeIn(xg), run_time=0.6)
        qg, qa, qw = proj("Query", Q_C, UP * 1.5)
        kg, ka, kw = proj("Key", K_C, ORIGIN)
        vg, va, vw = proj("Value", V_C, DOWN * 1.5)
        for g, a, w in [(qg, qa, qw), (kg, ka, kw), (vg, va, vw)]:
            self.play(GrowArrow(a), FadeIn(w), TransformFromCopy(x, g[0]), FadeIn(g[1]), run_time=0.7)
        pcap = Text("Q, K, V — three learned projections of the same token",
                    font_size=21, color=INK).to_edge(DOWN, buff=1.0)
        self.play(FadeIn(pcap), run_time=0.6)
        self.beat(1.4)

        # (b) the scaled dot-product attention formula (on a fresh slate)
        self.play(FadeOut(VGroup(xg, qg, kg, vg, qa, ka, va, qw, kw, vw, pcap)), run_time=0.5)
        # written as a real stacked fraction so QKᵀ / √dₖ is unambiguous
        head = mtext([("Attention(", "b"), ("Q", "b", Q_C), (", ", "b"), ("K", "b", K_C),
                      (", ", "b"), ("V", "b", V_C), (")   =   softmax(", "b")], base_fs=30)
        num = mtext([("Q", "b", Q_C), ("K", "b", K_C), ("T", "^", K_C)], base_fs=30)
        den = mtext([("√d", "b"), ("k", "_")], base_fs=30)
        bar = Line(ORIGIN, RIGHT * (max(num.width, den.width) + 0.3)).set_stroke(INK, 2.5)
        num.next_to(bar, UP, buff=0.08)
        den.next_to(bar, DOWN, buff=0.04)
        frac = VGroup(num, bar, den)
        tail = mtext([(")", "b"), ("  V", "b", V_C)], base_fs=30)
        formula = VGroup(head, frac, tail).arrange(RIGHT, buff=0.16)
        formula.move_to(UP * 1.55)
        self.play(Write(head), run_time=0.9)
        self.play(FadeIn(frac, shift=UP * 0.1), FadeIn(tail), run_time=0.8)
        steps = VGroup(
            dot_label("Q·K  →  relevance score for every pair", Q_C, fs=20),
            dot_label("÷ √d  keeps the scores in a stable range", MUTED, fs=20),
            dot_label("softmax  →  weights that sum to 1", GOOD, fs=20),
            dot_label("weighted sum of the V vectors", V_C, fs=20),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        steps.next_to(formula, DOWN, buff=0.6).align_to(formula, LEFT)
        self.reveal(steps, hold=0.9, run_time=0.4)
        self.beat(0.6)

        # move the formula + steps to the upper-left, bring in the matrix on the right
        self.play(VGroup(formula, steps).animate.scale(0.8).to_edge(LEFT, buff=0.5).shift(UP * 0.5),
                  run_time=0.7)

        # (c) the causal attention matrix: rows = query, cols = key
        toks = ["Not", "all", "those", "who", "wander"]
        n = len(toks)
        cell = 0.62
        grid = VGroup()
        for r in range(n):
            raw = np.array([RNG.uniform(0.2, 1.0) if c <= r else 0.0 for c in range(n)])
            raw = raw / raw.sum() if raw.sum() > 0 else raw
            for c in range(n):
                sq = Square(cell, stroke_width=1, stroke_color=BG)
                if c <= r:
                    sq.set_fill(ATTN, opacity=float(0.12 + 0.85 * raw[c]))
                else:
                    sq.set_fill(MUTED, opacity=0.10)
                grid.add(sq)
        grid.arrange_in_grid(rows=n, cols=n, buff=0.05)
        grid.to_edge(RIGHT, buff=1.4).shift(DOWN * 0.1)

        def gcell(r, c):
            return grid[r * n + c]
        col_lbls = VGroup(*[Text(t, font_size=15, color=K_C).next_to(gcell(0, c), UP, buff=0.12)
                            for c, t in enumerate(toks)])
        row_lbls = VGroup(*[Text(t, font_size=15, color=Q_C).next_to(gcell(r, 0), LEFT, buff=0.14)
                            for r, t in enumerate(toks)])
        qk = Text("keys →", font_size=16, color=K_C).next_to(col_lbls, UP, buff=0.14)
        vk = Text("queries ↓", font_size=16, color=Q_C).rotate(PI / 2).next_to(row_lbls, LEFT, buff=0.1)
        self.play(FadeIn(grid, lag_ratio=0.01, run_time=1.0),
                  FadeIn(col_lbls), FadeIn(row_lbls), FadeIn(qk), FadeIn(vk))
        self.beat(0.8)

        # highlight one query row ("sat" attends to The/cat/sat)
        qrow = 2
        box = SurroundingRectangle(VGroup(gcell(qrow, 0), gcell(qrow, n - 1)),
                                   color=Q_C, buff=0.02, corner_radius=0.02)
        rc = Text("“those” attends to itself and the words before it",
                  font_size=19, color=INK).next_to(grid, DOWN, buff=0.35)
        rc.shift(LEFT * max(0.0, rc.get_right()[0] - 6.95))
        self.play(Create(box), FadeIn(rc), run_time=0.8)
        self.beat(1.2)

        # (d) the causal mask: future cells are blocked
        mask_cells = VGroup(*[gcell(r, c) for r in range(n) for c in range(n) if c > r])
        crosses = VGroup()
        for r in range(n):
            for c in range(n):
                if c > r:
                    crosses.add(make_cross(scale=0.42).move_to(gcell(r, c)))
        self.play(Indicate(mask_cells, color=BAD, scale_factor=1.0),
                  Create(crosses), run_time=1.0)
        maskcap = Text("Causal mask: no token may attend to the future.",
                       font_size=21, color=BAD)
        maskcap2 = Text("This is what makes generation autoregressive.",
                        font_size=20, color=MUTED)
        mcg = VGroup(maskcap, maskcap2).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        mcg.next_to(grid, DOWN, buff=0.35)
        mcg.shift(LEFT * max(0.0, mcg.get_right()[0] - 6.95))
        # clean cross-fade (a char-by-char Transform between different sentences garbles)
        self.play(FadeOut(rc), FadeIn(mcg), run_time=0.7)
        self.beat(1.6)

        # (e) multi-head: h parallel heads, concatenated
        self.play(FadeOut(VGroup(box, mcg, crosses, qk, vk, col_lbls, row_lbls)),
                  grid.animate.scale(0.5).to_corner(DR, buff=0.9), run_time=0.7)
        mh_title = Text("Multi-head attention", font_size=26, color=ATTN, weight="BOLD")
        mh_title.next_to(steps, DOWN, buff=0.5).to_edge(LEFT, buff=0.6)
        heads = VGroup()
        for k in range(8):
            hm = VGroup(*[Square(0.12, stroke_width=0).set_fill(
                ATTN, opacity=float(RNG.uniform(0.1, 0.9))) for _ in range(9)])
            hm.arrange_in_grid(rows=3, cols=3, buff=0.02)
            heads.add(SurroundingRectangle(hm, color=ATTN, buff=0.06, corner_radius=0.04
                                           ).set_stroke(width=1.5))
            heads[-1].add(hm)
        heads.arrange(RIGHT, buff=0.16).next_to(mh_title, DOWN, buff=0.35).to_edge(LEFT, buff=0.6)
        mh_cap = Text("h = 8 heads run in parallel — each learns a different\n"
                      "relationship (syntax, coreference, …) — then concatenate.",
                      font_size=19, color=INK, line_spacing=0.8)
        mh_cap.next_to(heads, DOWN, buff=0.35).to_edge(LEFT, buff=0.6)
        self.play(FadeIn(mh_title), run_time=0.5)
        self.play(LaggedStartMap(FadeIn, heads, shift=UP * 0.1, lag_ratio=0.12, run_time=1.4))
        self.play(FadeIn(mh_cap, shift=UP * 0.1), run_time=0.7)
        self.beat(1.8)
        self.wipe()

    # ====================================================================== #
    # Scene 5 — Logits -> softmax -> a token
    # ====================================================================== #
    def scene_sample(self):
        header = self.section_header("4 · Choosing the next token", GOOD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # last position's vector -> Linear -> logits over the whole vocabulary
        h = vec_col([RNG.uniform(0.2, 0.9) for _ in range(8)], color=TOK, cw=0.26)
        hlbl = Text("last-token\noutput vector", font_size=17, color=MUTED,
                    line_spacing=0.7).next_to(h, DOWN, buff=0.16)
        hg = VGroup(h, hlbl).to_edge(LEFT, buff=1.0).shift(UP * 0.6)
        lin = chip("Linear", Q_C, w=1.7, h=0.9, fs=22).next_to(hg, RIGHT, buff=1.0).align_to(h, UP).shift(DOWN * 0.9)

        logits_vals = RNG.uniform(-3, 3, size=28)
        logit_bars = VGroup()
        for v in logits_vals:
            bar = Rectangle(width=0.13, height=abs(v) * 0.16 + 0.02, stroke_width=0,
                            fill_color=Q_C if v >= 0 else BAD, fill_opacity=0.85)
            logit_bars.add(bar)
        logit_bars.arrange(RIGHT, buff=0.03, aligned_edge=DOWN)
        logit_bars.next_to(lin, RIGHT, buff=0.9)
        llbl = Text("logits — one score per token  (|vocab| ≈ 50,000)",
                    font_size=19, color=MUTED).next_to(logit_bars, UP, buff=0.2)
        a1 = harrow(h.get_right(), lin.get_left(), sw=3)
        a2 = harrow(lin.get_right(), logit_bars.get_left(), color=Q_C, sw=3)
        self.play(FadeIn(hg), run_time=0.5)
        self.play(GrowArrow(a1), FadeIn(lin), run_time=0.6)
        self.play(GrowArrow(a2), LaggedStartMap(GrowFromEdge, logit_bars, edge=DOWN,
                                                lag_ratio=0.03, run_time=1.2), FadeIn(llbl))
        self.beat(1.2)

        # softmax -> a normalized distribution over candidate tokens
        soft = chip("softmax", GOOD, w=2.0, h=0.7, fs=22).next_to(logit_bars, DOWN, buff=1.4)
        soft.set_x(logit_bars.get_center()[0])
        a3 = harrow(logit_bars.get_bottom(), soft.get_top(), color=GOOD, sw=3)
        self.play(GrowArrow(a3), FadeIn(soft), run_time=0.6)

        dist = prob_bars([("are", 0.62), ("is", 0.16), ("were", 0.10),
                          ("seem", 0.07), ("roam", 0.05)], unit=3.2, fs=22)
        dist.next_to(soft, DOWN, buff=0.5)
        dist.set_x(soft.get_center()[0] + 0.4)
        scap = Text("probabilities — they sum to 1", font_size=19, color=MUTED)
        scap.next_to(dist, DOWN, buff=0.3)
        self.play(LaggedStart(*[FadeIn(r[0]) for r in dist],
                              *[GrowFromEdge(r[1], LEFT) for r in dist],
                              *[FadeIn(r[2]) for r in dist], lag_ratio=0.1, run_time=1.4),
                  FadeIn(scap))
        self.beat(1.2)

        # decoding strategies on the left
        strat_title = Text("Decoding strategy", font_size=24, color=INK, weight="BOLD")
        strat_title.to_edge(LEFT, buff=0.8).shift(DOWN * 1.75)
        strats = VGroup(
            dot_label("greedy — take the argmax", GOOD, fs=20),
            dot_label("temperature — sharpen / flatten", ATTN, fs=20),
            dot_label("top-k / top-p — sample the plausible few", Q_C, fs=20),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        strats.next_to(strat_title, DOWN, buff=0.3).align_to(strat_title, LEFT)
        self.play(FadeIn(strat_title), run_time=0.5)
        self.reveal(strats, hold=1.0, run_time=0.45)

        # pick "are"
        pick = SurroundingRectangle(dist[0], color=GOOD, buff=0.08, corner_radius=0.06)
        chosen = Text("→  “are”", font_size=26, color=GOOD, weight="BOLD").next_to(dist[0], RIGHT, buff=1.1)
        self.play(Create(pick), FadeIn(chosen, shift=RIGHT * 0.2), run_time=0.8)
        self.play(Flash(dist[0], color=GOOD, flash_radius=0.9), run_time=0.6)
        self.beat(1.8)
        self.wipe()

    # ====================================================================== #
    # Scene 6 — Autoregressive generation + KV cache
    # ====================================================================== #
    def scene_generate(self):
        header = self.section_header("5 · Autoregressive generation", ATTN)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)
        sub = Text("append the new token and feed the sequence back in",
                   font_size=23, color=MUTED).next_to(header, DOWN, buff=0.3).to_edge(LEFT, buff=0.5)
        self.play(FadeIn(sub, shift=UP * 0.15), run_time=0.6)
        self.beat(0.4)

        # the growing sequence of tokens (smaller, so the finished line fits)
        base = ["Not", "all", "those", "who", "wander"]
        row = VGroup(*[tok_box(w, fs=20) for w in base]).arrange(RIGHT, buff=0.16)
        row.next_to(sub, DOWN, buff=0.7).to_edge(LEFT, buff=0.6)
        self.play(LaggedStartMap(FadeIn, row, lag_ratio=0.12, run_time=1.0))
        self.beat(0.5)

        model = chip("Transformer\n(decoder stack)", MODEL_C, w=3.2, h=1.1, fs=20)
        model.next_to(row, DOWN, buff=1.4).to_edge(LEFT, buff=1.4)

        # KV cache panels on the right — one column per past token
        kbg = RoundedRectangle(width=2.4, height=1.7, corner_radius=0.1,
                               stroke_color=K_C, stroke_width=2, fill_opacity=0)
        vbgr = RoundedRectangle(width=2.4, height=1.7, corner_radius=0.1,
                                stroke_color=V_C, stroke_width=2, fill_opacity=0)
        kv = VGroup(kbg, vbgr).arrange(DOWN, buff=0.4).to_edge(RIGHT, buff=1.0).shift(UP * 0.2)
        ktitle = Text("K cache", font_size=18, color=K_C).next_to(kbg, UP, buff=0.1)
        vtitle = Text("V cache", font_size=18, color=V_C).next_to(vbgr, UP, buff=0.1)
        self.play(FadeIn(model), FadeIn(kv), FadeIn(ktitle), FadeIn(vtitle), run_time=0.7)

        # seed the cache with the prompt's columns
        kcols, vcols = VGroup(), VGroup()

        def add_cache_column(bg, cols, color):
            i = len(cols)
            col = VGroup(*[Square(0.16, stroke_width=0).set_fill(
                color, opacity=float(RNG.uniform(0.2, 0.9))) for _ in range(6)])
            col.arrange(DOWN, buff=0.02)
            col.move_to(bg.get_left() + RIGHT * (0.28 + i * 0.22) + UP * 0.0)
            cols.add(col)
            return col

        seed = []
        for _ in range(len(base)):
            seed.append(add_cache_column(kbg, kcols, K_C))
            seed.append(add_cache_column(vbgr, vcols, V_C))
        self.play(LaggedStartMap(FadeIn, VGroup(*seed), lag_ratio=0.05, run_time=0.8))
        self.beat(0.6)

        # generation loop: predict -> append -> cache one new column
        gen = [("are", GOOD), ("lost", GOOD), ("<eos>", BAD)]
        loop_lbl = Text("decode → append → repeat", font_size=20, color=ACCENT)
        loop_lbl.next_to(model, DOWN, buff=0.5)
        self.play(FadeIn(loop_lbl), run_time=0.5)

        for word, col in gen:
            a_in = harrow(row.get_bottom(), model.get_top(), sw=3)
            newtok = tok_box(word, color=col, fs=20)
            newtok.next_to(row, RIGHT, buff=0.16)
            a_out = harrow(model.get_right(), newtok.get_left() + DOWN * 0.0, color=col, sw=3)
            self.play(GrowArrow(a_in), run_time=0.35)
            self.play(Indicate(model, color=MODEL_C, scale_factor=1.05), run_time=0.4)
            self.play(GrowArrow(a_out), FadeIn(newtok, shift=RIGHT * 0.15), run_time=0.5)
            row.add(newtok)
            # cache grows by exactly one K and one V column
            nk = add_cache_column(kbg, kcols, K_C)
            nv = add_cache_column(vbgr, vcols, V_C)
            self.play(FadeIn(nk, shift=UP * 0.1), FadeIn(nv, shift=UP * 0.1),
                      FadeOut(a_in), FadeOut(a_out), run_time=0.5)
            if word == "<eos>":
                stop = SurroundingRectangle(newtok, color=BAD, buff=0.06, corner_radius=0.08)
                self.play(Create(stop), run_time=0.4)
            self.beat(0.7)

        cache_note = Text("KV cache: past keys & values are stored, so each new token\n"
                          "adds just one column — generation stays fast (O(1) per step).",
                          font_size=19, color=INK, line_spacing=0.8)
        cache_note.next_to(model, DOWN, buff=1.15).to_edge(LEFT, buff=0.6)
        self.play(FadeIn(cache_note, shift=UP * 0.1),
                  Indicate(kv, color=ACCENT, scale_factor=1.03), run_time=0.9)
        self.beat(1.0)
        stopcap = Text("stop at <eos> — or a length limit",
                       font_size=20, color=BAD).next_to(cache_note, DOWN, buff=0.3).to_edge(LEFT, buff=0.6)
        self.play(FadeIn(stopcap), run_time=0.6)
        self.beat(1.2)

        # closing: the completed quote, its attribution, and the one-line summary
        self.play(*[FadeOut(m) for m in self.mobjects if m not in (row,)], run_time=0.7)
        self.play(row.animate.move_to(UP * 1.15), run_time=0.7)
        attr = Text("“Not all those who wander are lost.”   — J.R.R. Tolkien",
                    font_size=24, color=MUTED, slant=ITALIC).next_to(row, DOWN, buff=0.45)
        self.play(FadeIn(attr), Circumscribe(row, color=ATTN, run_time=1.4))
        self.beat(1.0)
        closing = Text("embed → attend → predict → append,  looped —\n"
                       "that is a language model writing.",
                       font_size=28, color=INK, weight="BOLD", line_spacing=0.9)
        closing.next_to(attr, DOWN, buff=0.6)
        self.play(Write(closing), run_time=1.6)
        self.beat(2.0)
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_task()
        self.scene_embed()
        self.scene_arch()
        self.scene_attention()
        self.scene_sample()
        self.scene_generate()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_TfBase):
    def construct(self):
        self.play_intro()


class Task(_TfBase):
    def construct(self):
        self.scene_task()


class Embed(_TfBase):
    def construct(self):
        self.scene_embed()


class Architecture(_TfBase):
    def construct(self):
        self.scene_arch()


class Attention(_TfBase):
    def construct(self):
        self.scene_attention()


class Sample(_TfBase):
    def construct(self):
        self.scene_sample()


class Generate(_TfBase):
    def construct(self):
        self.scene_generate()


class Outro(_TfBase):
    def construct(self):
        self.play_outro()


class TransformerInference(_TfBase):
    """The whole ~3-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    TransformerInference().render()

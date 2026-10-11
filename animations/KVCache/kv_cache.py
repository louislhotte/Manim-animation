"""The KV Cache — a ~3-minute explainer, house-style.

Why autoregressive LLMs don't re-read their own words: the key/value cache that
makes generating the 1000th token almost as cheap as the first.

We build the idea from the ground up, following decoder-only (GPT-style)
inference and the attention mechanism of

    "Attention Is All You Need" — Vaswani et al., NeurIPS 2017 (arXiv:1706.03762)

and the cache-shrinking techniques that followed:

    Multi-Query Attention   — Shazeer, 2019   (arXiv:1911.02150)
    Grouped-Query Attention — Ainslie et al., 2023 (arXiv:2305.13245)
    PagedAttention (vLLM)   — Kwon et al., 2023 (arXiv:2309.06180)

Six scenes plus the channel's intro/outro cards:

    1. The waste     -- generation is a loop that recomputes K & V every step
    2. Reuse         -- a token's Key and Value never change: compute them once
    3. The KV cache  -- append one column per step; the query sweeps the cache
    4. Two phases    -- prefill (compute-bound) then decode (bandwidth-bound)
    5. The price     -- cache memory grows linearly and can rival the weights
    6. Shrinking it  -- MHA -> GQA -> MQA, and PagedAttention

Everything uses ``Text`` (Pango) rather than ``Tex`` so it renders with no LaTeX
install. Scenes are exposed individually (``Waste``, ``Reuse``, ``Cache``,
``Phases``, ``Memory``, ``Shrink``, ``Intro``, ``Outro``) and as one continuous
film (``KVCacheFilm``).

Env knobs:
    KV_QUICK=1   shorten every hold for a fast sanity render
    KV_DELAY=..  override the reading-hold multiplier (tunes total runtime)
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

# --- crisp text ------------------------------------------------------------ #
# Manim's ``Text`` mangles letter/word spacing below ~20 pt. Fix it once: render
# every glyph at a large base size and scale the mobject *down* to the requested
# size (scaling a correctly-spaced render down stays crisp; rendering small does
# not). This shadows manim's ``Text`` so every call benefits automatically.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("KV_QUICK") == "1"
# Two separate pacing knobs so nothing feels rushed:
#   DELAY  scales the small pauses *between* animation steps (motion rhythm).
#   READ   is the absolute hold after any block of text lands, so there is always
#          time to actually read it (the viewer asked for ~3 s per subtitle).
# ANIM_SLOW stretches every played animation so transitions aren't abrupt.
DELAY = float(os.environ.get("KV_DELAY", 0.28 if QUICK else 1.1))
READ = float(os.environ.get("KV_READ", 0.35 if QUICK else 3.0))
ANIM_SLOW = 1.0 if QUICK else 1.35
END_HOLD = 0.2 if QUICK else 2.6  # settle held on a finished scene before it wipes

# ---- palette (shared with the Transformer film for series continuity) ----- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
FAINT = "#3A4152"       # gridlines
TOK = "#C792EA"         # tokens / embeddings (violet)
Q_C = "#5B8DEF"         # queries (blue)
K_C = "#2EC4B6"         # keys (teal)
V_C = "#FFD166"         # values (gold)
ATTN = "#FF8C42"        # attention weights / logits (orange)
MODEL_C = "#FFD166"     # the model core (gold)
GOOD = "#3DD68C"        # keep / chosen / cheap (green)
BAD = "#FF5C5C"         # wasted / masked / stop (red)
ACCENT = "#FFD166"

RNG = np.random.default_rng(7)

# A clean, well-hinted sans-serif everywhere (Pango's serif default drops the
# spaces between words at these sizes). Set on the *real* Text (we shadowed it).
FONT = "Helvetica Neue"
_BaseText.set_default(font=FONT)


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
        max_tip_length_to_length_ratio=0.35, tip_length=0.2,
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


def prob_bars(items, unit=3.2, fs=22, color=ATTN, gap=0.52):
    """Right-aligned labels + horizontal probability bars + value readouts."""
    grp = VGroup()
    labs = [Text(n, font_size=fs, color=INK) for n, _ in items]
    for (n, p), lab in zip(items, labs):
        i = len(grp)
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
class _KVBase(Scene):
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

    def reveal(self, items, hold=1.0, run_time=0.45, shift=RIGHT * 0.2):
        for m in items:
            self.play(FadeIn(m, shift=shift), run_time=run_time)
            self.read(hold)

    def wipe(self, rt=0.7):
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    def section_header(self, label, color=INK):
        txt = Text(label, font_size=34, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(txt.get_left(), txt.get_right()).next_to(txt, DOWN, buff=0.12)
        line.set_stroke(color=color, width=3)
        return VGroup(txt, line)

    def bottomcap(self, s, color=INK, fs=22, buff=0.42, **kw):
        t = Text(s, font_size=fs, color=color, **kw)
        if t.width > 12.9:
            t.scale_to_fit_width(12.9)
        t.to_edge(DOWN, buff=buff)
        return t

    def cite(self, s):
        return Text(s, font_size=15, color=MUTED, slant=ITALIC).to_edge(DOWN, buff=0.16)

    # ---- house-style intro / outro cards ---------------------------------- #
    def play_intro(self):
        header = Text("The KV Cache", font_size=60, color=INK, weight="BOLD")
        header.set(width=min(8.6, header.width))
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=ATTN)
        writer = Text("Created by Ptolémé", font_size=28, color=Q_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        sub = Text("Why the 1000th token is almost as cheap as the first",
                   font_size=32, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.read(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        src = Text("the optimization behind fast LLM inference",
                   font_size=22, color=MUTED)
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
        ).set_stroke(width=3, color=ATTN)
        writer = Text("Created by Ptolémé", font_size=28, color=Q_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = Text("Compute the past once — reuse it forever.",
                     font_size=26, color=ACCENT)
        recap.next_to(writer, DOWN, buff=0.5)
        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap), run_time=0.8)
        self.read(1.6)
        self.play(FadeOut(VGroup(header, line, writer, recap)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 — Generation is a loop, and it repeats itself
    # ====================================================================== #
    def scene_waste(self):
        title = Text("Generating text is a loop", font_size=46, color=INK, weight="BOLD")
        self.play(Write(title), run_time=1.4)
        self.read(0.8)
        self.play(title.animate.scale(0.60).to_edge(UP, buff=0.42), run_time=0.7)

        # the loop: tokens -> model -> next token -> append
        prompt = ["Not", "all", "those", "who", "wander"]
        row = VGroup(*[tok_box(w, fs=20, h=0.58) for w in prompt]).arrange(RIGHT, buff=0.16)
        row.next_to(title, DOWN, buff=0.5)
        model = chip("Transformer", MODEL_C, w=2.6, h=0.9, fs=22).next_to(row, DOWN, buff=0.55)
        a_in = harrow(row.get_bottom(), model.get_top(), sw=3)
        nxt = tok_box("are", color=GOOD, fs=20, h=0.58).next_to(model, RIGHT, buff=1.0)
        a_out = harrow(model.get_right(), nxt.get_left(), color=GOOD, sw=3)
        self.play(LaggedStartMap(FadeIn, row, shift=UP * 0.12, lag_ratio=0.18, run_time=1.0))
        self.play(GrowArrow(a_in), FadeIn(model), run_time=0.6)
        self.play(GrowArrow(a_out), FadeIn(nxt, shift=RIGHT * 0.15), run_time=0.6)
        loop = Text("predict → append → repeat", font_size=22, color=ACCENT)
        loop.next_to(model, DOWN, buff=0.5)
        self.play(FadeIn(loop, shift=UP * 0.15), run_time=0.6)
        self.read()

        # But how much work is each step? Fold the loop away and count.
        q = Text("But each step re-runs the whole network over the whole sequence.",
                 font_size=24, color=INK).next_to(model, DOWN, buff=0.5)
        self.play(FadeOut(VGroup(a_in, a_out, nxt, loop, model)),
                  row.animate.scale(0.9).next_to(title, DOWN, buff=0.35),
                  run_time=0.7)
        self.play(FadeIn(q, shift=UP * 0.12), run_time=0.7)
        self.read(1.2)
        self.play(FadeOut(q), run_time=0.4)

        # the triangle of waste: each row = one step, one cell per token's (K,V)
        cw = 0.34
        base = len(prompt)          # prompt length (prefill row)
        nsteps = 4                  # prefill + 3 decode rows shown
        origin = np.array([-4.9, 1.35, 0])
        rows = VGroup()
        cell_at = {}
        for r in range(nsteps):
            ncells = base + r
            rowg = VGroup()
            for c in range(ncells):
                sq = Square(cw, stroke_width=1.2, stroke_color=BG)
                new = (r == 0) or (c == ncells - 1)  # prefill row is all new work
                sq.set_fill(GOOD if new else BAD, opacity=0.9 if new else 0.0)
                sq.move_to(origin + RIGHT * (c * (cw + 0.06)) + DOWN * (r * (cw + 0.26)))
                cell_at[(r, c)] = sq
                rowg.add(sq)
            rows.add(rowg)
        step_lbls = VGroup()
        for r in range(nsteps):
            name = "prefill" if r == 0 else f"decode {r}"
            lbl = Text(name, font_size=17, color=MUTED)
            lbl.next_to(rows[r], LEFT, buff=0.35).align_to(origin, UP).shift(DOWN * (r * (cw + 0.26)))
            step_lbls.add(lbl)

        # legend + counter on the right
        leg = VGroup(
            VGroup(Square(0.24, stroke_width=0, fill_color=GOOD, fill_opacity=0.9),
                   Text("new work", font_size=18, color=INK)).arrange(RIGHT, buff=0.18),
            VGroup(Square(0.24, stroke_width=1.2, stroke_color=BAD, fill_color=BAD, fill_opacity=0.55),
                   Text("recomputed (identical)", font_size=18, color=INK)).arrange(RIGHT, buff=0.18),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.24)
        leg.to_edge(RIGHT, buff=0.7).shift(UP * 1.1)
        counter = Text("K,V vectors computed:  0", font_size=20, color=INK)
        counter.next_to(leg, DOWN, buff=0.6).align_to(leg, LEFT)

        self.play(FadeIn(step_lbls[0]),
                  LaggedStart(*[GrowFromCenter(cell_at[(0, c)]) for c in range(base)],
                              lag_ratio=0.12, run_time=1.0),
                  FadeIn(leg), FadeIn(counter))
        total = base
        new_counter = Text(f"K,V vectors computed:  {total}", font_size=20, color=INK
                           ).move_to(counter, LEFT)
        self.play(Transform(counter, new_counter), run_time=0.3)
        self.beat(0.8)

        # decode rows: recomputed cells flash on (red), the new one is green
        for r in range(1, nsteps):
            ncells = base + r
            recompute = [cell_at[(r, c)] for c in range(ncells - 1)]
            for sq in recompute:
                sq.set_fill(BAD, opacity=0.55)
            newcell = cell_at[(r, ncells - 1)]
            self.play(FadeIn(step_lbls[r]),
                      LaggedStart(*[FadeIn(sq) for sq in recompute], lag_ratio=0.05,
                                  run_time=0.7),
                      run_time=0.7)
            self.play(GrowFromCenter(newcell), run_time=0.35)
            total += ncells
            nc = Text(f"K,V vectors computed:  {total}", font_size=20, color=INK).move_to(counter, LEFT)
            self.play(Transform(counter, nc), run_time=0.3)
            self.beat(0.5)

        # the punchline: the whole red triangle is redundant
        red_cells = VGroup(*[cell_at[(r, c)] for r in range(nsteps)
                             for c in range(base + r - 1) if r >= 1])
        self.play(Indicate(red_cells, color=BAD, scale_factor=1.0), run_time=1.0)
        cap = self.bottomcap(
            "Every step rebuilds the Keys and Values of every earlier token — "
            "the same numbers, over and over.  Work grows like n².",
            color=INK, fs=23)
        self.play(FadeIn(cap, shift=UP * 0.12), run_time=0.7)
        self.read(1.5)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — A token's Key and Value never change
    # ====================================================================== #
    def scene_reuse(self):
        header = self.section_header("1 · Keys & Values are per-token", K_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # (a) one token -> Q, K, V via three learned projections
        x = vcells(6, TOK, cw=0.26, seed=1)
        xlbl = Text("token\nvector", font_size=17, color=MUTED, line_spacing=0.7).next_to(x, DOWN, buff=0.16)
        xg = VGroup(x, xlbl).to_edge(LEFT, buff=1.1).shift(UP * 0.6)
        self.play(FadeIn(xg), run_time=0.5)

        def proj(name, color, shift, seed):
            v = vcells(5, color, cw=0.26, seed=seed)
            lbl = Text(name, font_size=20, color=color, weight="BOLD").next_to(v, RIGHT, buff=0.16)
            g = VGroup(v, lbl).next_to(xg, RIGHT, buff=2.0).shift(shift)
            ar = harrow(x.get_right(), v.get_left(), color=color, sw=3)
            wlab = Text(f"W{name[0].lower()}", font_size=16, color=MUTED)
            wlab.move_to(ar.point_from_proportion(0.5)).shift(UP * 0.2)
            return g, ar, wlab

        qg, qa, qw = proj("Query", Q_C, UP * 1.5, 2)
        kg, ka, kw = proj("Key", K_C, ORIGIN, 3)
        vg, va, vw = proj("Value", V_C, DOWN * 1.5, 4)
        for g, a, w in [(qg, qa, qw), (kg, ka, kw), (vg, va, vw)]:
            self.play(GrowArrow(a), FadeIn(w), TransformFromCopy(x, g[0]), FadeIn(g[1]), run_time=0.6)
        cap0 = self.bottomcap("Each token is projected into a Query, a Key and a Value.",
                              color=INK, fs=23)
        self.play(FadeIn(cap0), run_time=0.5)
        self.read(1.1)

        # (b) the invariance: K and V depend ONLY on that token (and its position)
        self.play(FadeOut(VGroup(xg, qg, qa, qw, cap0)),
                  VGroup(kg, ka, kw, vg, va, vw).animate.set_opacity(0.0),
                  run_time=0.5)
        self.remove(kg, ka, kw, vg, va, vw)

        insight = Text("A Key and Value depend only on their own token.",
                       font_size=30, color=INK, weight="BOLD").move_to(UP * 2.3)
        insight2 = Text("Adding tokens later never changes the ones already there.",
                        font_size=24, color=MUTED).next_to(insight, DOWN, buff=0.25)
        self.play(FadeIn(insight, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(insight2), run_time=0.6)
        self.read(1.2)

        # a row of tokens, each with its fixed (K,V) tag below
        words = ["Not", "all", "those", "who"]
        toks = VGroup()
        for i, w in enumerate(words):
            tb = tok_box(w, fs=20, h=0.56)
            kv = VGroup(vcells(3, K_C, cw=0.16, seed=10 + i),
                        vcells(3, V_C, cw=0.16, seed=20 + i)).arrange(RIGHT, buff=0.08)
            kvlbl = Text("k  v", font_size=14, color=MUTED)
            col = VGroup(tb, kv, kvlbl).arrange(DOWN, buff=0.14)
            toks.add(col)
        toks.arrange(RIGHT, buff=0.6).move_to(DOWN * 0.35)
        self.play(LaggedStartMap(FadeIn, toks, shift=UP * 0.12, lag_ratio=0.15, run_time=1.2))
        self.read(0.7)

        # append a 5th token -> the first four (K,V) are untouched (checks), only #5 is new
        new = tok_box("wander", fs=20, h=0.56)
        newkv = VGroup(vcells(3, K_C, cw=0.16, seed=99), vcells(3, V_C, cw=0.16, seed=98)).arrange(RIGHT, buff=0.08)
        newlbl = Text("k  v", font_size=14, color=MUTED)
        newcol = VGroup(new, newkv, newlbl).arrange(DOWN, buff=0.14)
        newcol.next_to(toks, RIGHT, buff=0.6).align_to(toks, UP)
        self.play(FadeIn(newcol, shift=RIGHT * 0.2), run_time=0.6)
        self.play(Indicate(newkv, color=GOOD, scale_factor=1.15), run_time=0.6)
        checks = VGroup(*[make_tick(GOOD, sw=5, scale=0.8).next_to(toks[i][1], DOWN, buff=0.02)
                          for i in range(len(words))])
        # place checks just over the "k v" labels of the existing tokens
        for i in range(len(words)):
            checks[i].move_to(toks[i][2]).shift(UP * 0.02)
            toks[i][2].set_opacity(0.0)
        self.play(LaggedStartMap(FadeIn, checks, lag_ratio=0.15, run_time=0.9))
        self.play(FadeOut(VGroup(insight, insight2)), run_time=0.4)
        cap = self.bottomcap(
            "So why recompute them every step?  Compute each token's K and V once — and store them.",
            color=ACCENT, fs=23)
        self.play(FadeIn(cap, shift=UP * 0.12), run_time=0.7)
        self.play(FadeIn(self.cite("attention: Vaswani et al., “Attention Is All You Need,” 2017")),
                  run_time=0.4)
        self.read(1.5)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — The KV cache (the core mechanism)
    # ====================================================================== #
    def scene_cache(self):
        header = self.section_header("2 · The KV cache", ACCENT)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # the growing sentence along the top
        prompt = ["Not", "all", "those", "who", "wander"]
        row = VGroup(*[tok_box(w, fs=18, h=0.5) for w in prompt]).arrange(RIGHT, buff=0.14)
        row.move_to(UP * 2.75)
        self.play(LaggedStartMap(FadeIn, row, lag_ratio=0.12, run_time=0.9))

        # two cache matrices, side by side on the right (K teal, V gold) — side by
        # side (not stacked) keeps the vertical strip above/below each box free for
        # the attention weights and the output vector.
        rows_n, cap_cols, colw = 6, 8, 0.24
        cell = 0.19
        bw = cap_cols * colw + 0.42
        bh = rows_n * cell + 0.5

        def cache_box(color, title, center):
            bg = RoundedRectangle(width=bw, height=bh, corner_radius=0.1,
                                  stroke_color=color, stroke_width=2.5, fill_opacity=0.04,
                                  fill_color=color).move_to(center)
            t = Text(title, font_size=18, color=color, weight="BOLD").next_to(bg, UP, buff=0.12)
            return bg, t

        kbg, ktitle = cache_box(K_C, "K cache", np.array([1.75, 1.0, 0]))
        vbg, vtitle = cache_box(V_C, "V cache", np.array([4.55, 1.0, 0]))
        self.play(FadeIn(VGroup(kbg, ktitle, vbg, vtitle)), run_time=0.6)

        kcols, vcols = VGroup(), VGroup()

        def add_col(bg, cols, color, seed):
            i = len(cols)
            col = VGroup(*[Square(cell, stroke_width=0).set_fill(
                color, opacity=float(np.random.default_rng(seed + j).uniform(0.2, 0.9)))
                for j in range(rows_n)])
            col.arrange(DOWN, buff=0)
            col.move_to([bg.get_left()[0] + 0.28 + i * colw, bg.get_center()[1], 0])
            cols.add(col)
            return col

        # prefill: the prompt fills both caches (one column per prompt token)
        seed_cols = []
        for i in range(len(prompt)):
            seed_cols.append(add_col(kbg, kcols, K_C, 100 + i * 7))
            seed_cols.append(add_col(vbg, vcols, V_C, 300 + i * 7))
        cap = self.bottomcap("Prefill: the prompt fills the cache — one K and one V column per token.",
                             color=INK, fs=23)
        self.play(LaggedStartMap(FadeIn, VGroup(*seed_cols), shift=UP * 0.08,
                                 lag_ratio=0.06, run_time=1.0), FadeIn(cap))
        self.read(1.1)

        # the decode pipeline on the left: current token -> q, k, v
        cur = tok_box("wander", color=TOK, fs=18, h=0.5).move_to([-5.35, 1.35, 0])
        cur_lbl = Text("current token", font_size=15, color=MUTED).next_to(cur, UP, buff=0.12)

        def small_vec(color, seed, y):
            return vcells(4, color, cw=0.19, seed=seed).move_to([-4.5, y, 0])

        step_cap = {
            0: "Decode: compute q, k, v for the new token only.",
            1: "Append its k and v — the cache grows by exactly one column.",
            2: "The new query attends across every cached Key → attention weights.",
            3: "Blend the Values by those weights → the next token.",
        }

        def decode_step(nxt_word, nxt_color, sd, rk=1.0):
            # 1) project the current token -> q, k, v (left)
            qv = small_vec(Q_C, sd + 1, 0.85)
            kv = small_vec(K_C, sd + 2, -0.15)
            vv = small_vec(V_C, sd + 3, -1.15)
            qlab = Text("q", font_size=18, color=Q_C, weight="BOLD").next_to(qv, LEFT, buff=0.12)
            klab = Text("k", font_size=18, color=K_C, weight="BOLD").next_to(kv, LEFT, buff=0.12)
            vlab = Text("v", font_size=18, color=V_C, weight="BOLD").next_to(vv, LEFT, buff=0.12)
            proj = VGroup(qv, kv, vv, qlab, klab, vlab)
            c0 = self.bottomcap(step_cap[0], color=INK, fs=23)
            self.play(Transform(self._cap, c0), FadeIn(proj, shift=RIGHT * 0.1), run_time=0.7)
            self.read(rk)

            # 2) append k and v as one new column each
            nk = add_col(kbg, kcols, K_C, sd + 40)
            nv = add_col(vbg, vcols, V_C, sd + 60)
            ka = harrow(kv.get_right(), nk.get_left(), color=K_C, sw=3)
            vaa = harrow(vv.get_right(), nv.get_left(), color=V_C, sw=3)
            c1 = self.bottomcap(step_cap[1], color=INK, fs=23)
            self.play(Transform(self._cap, c1), GrowArrow(ka), GrowArrow(vaa), run_time=0.6)
            self.play(TransformFromCopy(kv, nk), TransformFromCopy(vv, nv), run_time=0.7)
            self.play(FadeOut(VGroup(ka, vaa)), run_time=0.3)
            self.read(rk)

            # 3) the query sweeps the K cache -> weights hang BELOW the K box
            c2 = self.bottomcap(step_cap[2], color=INK, fs=23)
            self.play(Transform(self._cap, c2), run_time=0.4)
            sweep = SurroundingRectangle(kcols[0], color=Q_C, buff=0.03,
                                         corner_radius=0.02).set_stroke(width=3)
            self.play(FadeIn(sweep), run_time=0.3)
            rng = np.random.default_rng(sd)
            raw = rng.uniform(0.25, 1.0, size=len(kcols))
            raw = raw / raw.sum()
            weights = VGroup()
            top_y = kbg.get_bottom()[1] - 0.06
            for ci in range(len(kcols)):
                self.play(sweep.animate.move_to(kcols[ci]), run_time=0.1)
                h = max(0.05, raw[ci] / raw.max() * 0.55)
                bar = Rectangle(width=colw * 0.7, height=h, stroke_width=0,
                                fill_color=ATTN, fill_opacity=0.9)
                bar.move_to([kcols[ci].get_center()[0], top_y - h / 2, 0])
                weights.add(bar)
                self.add(bar)
            wlbl = Text("attention weights", font_size=15, color=ATTN).next_to(weights, DOWN, buff=0.1)
            self.play(FadeOut(sweep), FadeIn(wlbl), run_time=0.3)
            self.read(rk)

            # 4) blend the V columns by those weights -> output -> next token
            c3 = self.bottomcap(step_cap[3], color=INK, fs=23)
            self.play(Transform(self._cap, c3), run_time=0.4)
            self.play(*[vcols[ci].animate.set_opacity(float(0.2 + 0.8 * raw[ci] / raw.max()))
                        for ci in range(len(vcols))], run_time=0.6)
            out = vcells(4, TOK, cw=0.19, seed=sd + 7)
            out.move_to([vbg.get_center()[0], vbg.get_bottom()[1] - 0.55, 0])
            out_lbl = Text("output", font_size=15, color=TOK).next_to(out, DOWN, buff=0.08)
            self.play(TransformFromCopy(vcols, out), FadeIn(out_lbl), run_time=0.7)
            newtok = tok_box(nxt_word, color=nxt_color, fs=18, h=0.5).next_to(row, RIGHT, buff=0.14)
            self.play(TransformFromCopy(out, newtok), run_time=0.7)  # output rises into the token
            row.add(newtok)
            self.read(rk)

            # reset the V opacity and clear the per-step scratch
            self.play(FadeOut(VGroup(proj, weights, wlbl, out, out_lbl)),
                      *[vcols[ci].animate.set_opacity(0.75) for ci in range(len(vcols))],
                      run_time=0.5)

        self.play(FadeIn(VGroup(cur, cur_lbl)), run_time=0.5)
        self._cap = cap
        decode_step("are", GOOD, 500, rk=1.0)   # first pass: full reading time
        # second step (viewer already knows the loop): swap the current token first
        cur2 = tok_box("are", color=TOK, fs=18, h=0.5).move_to(cur)
        self.play(Transform(cur, cur2), run_time=0.4)
        decode_step("lost", GOOD, 700, rk=0.5)   # familiar now: shorter holds

        # closing contrast: naive O(n^2) vs cache O(n)
        self.play(FadeOut(VGroup(cur, cur_lbl)), run_time=0.4)
        naive = chip("naïve:  recompute all  →  O(n²)", BAD, w=5.3, h=0.8, fs=22)
        cached = chip("KV cache:  append one  →  O(n)", GOOD, w=5.3, h=0.8, fs=22)
        badges = VGroup(naive, cached).arrange(DOWN, buff=0.3).move_to([-3.0, -0.6, 0])
        c_final = self.bottomcap("Compute each token's K and V once, then reuse them for every future step.",
                                 color=ACCENT, fs=23)
        self.play(FadeIn(naive, shift=UP * 0.1), run_time=0.5)
        self.read(0.7)
        self.play(FadeIn(cached, shift=UP * 0.1), run_time=0.5)
        self.read(0.7)
        self.play(Transform(self._cap, c_final), run_time=0.5)
        self.read(1.4)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Two phases: prefill and decode
    # ====================================================================== #
    def scene_phases(self):
        header = self.section_header("3 · Two phases: prefill & decode", Q_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # the cache meter across the top: a row of slots that fill up
        n_prompt, n_gen = 6, 6
        slot = 0.34
        meter = VGroup(*[Square(slot, stroke_width=1.4, stroke_color=FAINT)
                         for _ in range(n_prompt + n_gen)])
        meter.arrange(RIGHT, buff=0.06).move_to(UP * 1.7)
        mlbl = Text("KV cache", font_size=18, color=MUTED).next_to(meter, LEFT, buff=0.3)
        self.play(FadeIn(meter), FadeIn(mlbl), run_time=0.6)

        # timeline baseline
        base_y = -0.7
        axis = Arrow([-5.6, base_y, 0], [6.0, base_y, 0], buff=0, stroke_width=3, color=MUTED,
                     max_tip_length_to_length_ratio=0.03, tip_length=0.18)
        tlbl = Text("time →", font_size=18, color=MUTED).next_to(axis.get_end(), UP, buff=0.12)
        self.play(GrowArrow(axis), FadeIn(tlbl), run_time=0.6)

        # --- PREFILL: one wide block; whole prompt processed in parallel ---- #
        pf = RoundedRectangle(width=2.4, height=1.0, corner_radius=0.1,
                              stroke_color=K_C, stroke_width=2.5, fill_color=K_C, fill_opacity=0.16)
        pf.move_to([-4.3, base_y + 0.9, 0])
        pf_lbl = Text("PREFILL", font_size=20, color=K_C, weight="BOLD").move_to(pf)
        pf_sub = Text("whole prompt\nin one pass", font_size=15, color=INK, line_spacing=0.8).next_to(pf, DOWN, buff=0.16)
        self.play(FadeIn(pf, shift=UP * 0.1), FadeIn(pf_lbl), FadeIn(pf_sub), run_time=0.6)
        # cache fills the first n_prompt slots at once
        self.play(LaggedStart(*[meter[i].animate.set_fill(K_C, opacity=0.8).set_stroke(K_C)
                                for i in range(n_prompt)], lag_ratio=0.04, run_time=0.9))
        pf_note = Text("compute-bound — big parallel matmuls; the GPU is busy",
                       font_size=20, color=K_C).move_to([0, base_y - 1.15, 0])
        self.play(FadeIn(pf_note, shift=UP * 0.1), run_time=0.6)
        self.read(1.2)

        # --- DECODE: a train of small steps; one token, one slot each ------- #
        dec_note = Text("decode — one token at a time",
                        font_size=20, color=ATTN).move_to(pf_note)
        self.play(FadeOut(pf_note), FadeIn(dec_note), run_time=0.5)
        ticks = VGroup()
        for s in range(n_gen):
            t = RoundedRectangle(width=0.42, height=0.7, corner_radius=0.06,
                                 stroke_color=ATTN, stroke_width=2, fill_color=ATTN, fill_opacity=0.18)
            t.move_to([-2.2 + s * 0.92, base_y + 0.9, 0])
            ticks.add(t)
        for s in range(n_gen):
            self.play(FadeIn(ticks[s], shift=UP * 0.1), run_time=0.22)
            self.play(meter[n_prompt + s].animate.set_fill(ATTN, opacity=0.8).set_stroke(ATTN),
                      run_time=0.22)
        self.read(0.7)
        dec_note2 = Text("memory-bandwidth-bound — each step streams the whole cache to add one column",
                         font_size=20, color=ATTN).move_to(dec_note)
        if dec_note2.width > 12.9:
            dec_note2.scale_to_fit_width(12.9)
        self.play(Transform(dec_note, dec_note2), run_time=0.6)
        self.read(1.3)

        cap = self.bottomcap("Prefill is a sprint; decode is a stroll — but each stroll step re-reads the entire cache.",
                             color=INK, fs=23)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.6)
        self.read(1.5)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — The price is memory
    # ====================================================================== #
    def scene_memory(self):
        header = self.section_header("4 · The price is memory", BAD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # (a) the size formula, plugged in for Llama-2-7B — centred, one line at a time
        f1 = Text("cache =  2  ×  layers  ×  heads  ×  d_head  ×  tokens  ×  bytes",
                  font_size=28, color=INK).move_to(UP * 1.7)
        two = Text("(2 = one K + one V)", font_size=18, color=MUTED).next_to(f1, DOWN, buff=0.2)
        self.play(FadeIn(f1, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(two), run_time=0.4)
        self.read(1.1)

        f2 = Text("Llama-2-7B:  2 × 32 × 32 × 128 × tokens × 2 B",
                  font_size=26, color=INK).next_to(two, DOWN, buff=0.5)
        self.play(FadeIn(f2, shift=UP * 0.1), run_time=0.6)
        self.read()
        per = Text("≈ 0.5 MB  per token",
                   font_size=32, color=ACCENT, weight="BOLD").next_to(f2, DOWN, buff=0.45)
        self.play(FadeIn(per, shift=UP * 0.1), run_time=0.6)
        self.read(1.3)

        # (b) fade the derivation; keep only the punchline, parked top-right, clear
        # of the header — the chart then owns the whole frame.
        keep = Text("≈ 0.5 MB / token", font_size=24, color=ACCENT, weight="BOLD").to_corner(UR, buff=0.5)
        self.play(FadeOut(VGroup(f1, two, f2)), ReplacementTransform(per, keep), run_time=0.7)

        ox, oy = -4.7, -2.5
        aw, ah = 9.3, 4.5
        xaxis = Arrow([ox, oy, 0], [ox + aw, oy, 0], buff=0, stroke_width=3, color=MUTED,
                      max_tip_length_to_length_ratio=0.03, tip_length=0.16)
        yaxis = Arrow([ox, oy, 0], [ox, oy + ah, 0], buff=0, stroke_width=3, color=MUTED,
                      max_tip_length_to_length_ratio=0.03, tip_length=0.16)
        xname = Text("context length (tokens)", font_size=18, color=MUTED).move_to([ox + aw / 2, oy - 0.62, 0])
        # y-axis name sits FAR left, clear of the numeric tick labels (which hug the axis)
        yname = Text("KV cache (GB)", font_size=18, color=MUTED).rotate(PI / 2)
        yname.move_to([ox - 0.9, oy + ah / 2, 0])

        gb_max, ctx_max = 18.0, 32.0  # y in GB, x in K tokens

        def PX(ctx_k):
            return ox + (ctx_k / ctx_max) * aw

        def PY(gb):
            return oy + (gb / gb_max) * ah

        xt = [(8, "8K"), (16, "16K"), (24, "24K"), (32, "32K")]
        xticks = VGroup()
        for cx, lab in xt:
            tk = Line([PX(cx), oy - 0.08, 0], [PX(cx), oy + 0.08, 0], stroke_color=MUTED)
            tl = Text(lab, font_size=15, color=MUTED).next_to(tk, DOWN, buff=0.06)
            xticks.add(VGroup(tk, tl))
        yt = [(4, "4"), (8, "8"), (14, "14"), (16, "16")]
        yticks = VGroup()
        for gy, lab in yt:
            tk = Line([ox - 0.08, PY(gy), 0], [ox + 0.08, PY(gy), 0], stroke_color=MUTED)
            tl = Text(lab, font_size=15, color=MUTED).next_to(tk, LEFT, buff=0.08)
            yticks.add(VGroup(tk, tl))
        self.play(GrowArrow(xaxis), GrowArrow(yaxis), FadeIn(xname), FadeIn(yname),
                  FadeIn(xticks), FadeIn(yticks), run_time=0.9)
        self.read(0.5)

        # the cache line: 0.5 MB/token -> at 32K = 16 GB (linear)
        line = Line([PX(0), PY(0), 0], [PX(32), PY(16), 0]).set_stroke(BAD, width=5)
        line_lbl = Text("KV cache  (grows linearly)", font_size=18, color=BAD)
        line_lbl.move_to([PX(23), PY(16) + 0.35, 0])
        self.play(Create(line), run_time=1.4)
        self.play(FadeIn(line_lbl), run_time=0.5)
        self.read(0.9)

        # model-weights reference line at 14 GB (label parked in the open upper-left)
        wline = DashedLine([PX(0), PY(14), 0], [PX(32), PY(14), 0], dash_length=0.14).set_stroke(MUTED, width=3)
        wlbl = Text("model weights ≈ 14 GB", font_size=17, color=MUTED).move_to([PX(8.5), PY(14) + 0.42, 0])
        self.play(Create(wline), FadeIn(wlbl), run_time=0.8)
        self.read(0.9)

        # the crossing: past ~28K a single sequence's cache outweighs the model
        cross = Dot(point=[PX(28), PY(14), 0], radius=0.09, color=ACCENT)
        cross_lbl = Text("cache > weights", font_size=17, color=ACCENT).next_to(cross, UP, buff=0.14).shift(RIGHT * 0.2)
        self.play(FadeIn(cross, scale=1.6), FadeIn(cross_lbl), run_time=0.6)
        self.read()

        cap = self.bottomcap("It grows with context and with batch size — at long context the cache can rival the model itself.",
                             color=INK, fs=22)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.6)
        self.read(1.5)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 6 — Shrinking the cache: MHA -> GQA -> MQA
    # ====================================================================== #
    def scene_shrink(self):
        header = self.section_header("5 · Shrinking the cache", GOOD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)
        sub = Text("share Keys & Values across query heads",
                   font_size=23, color=MUTED).next_to(header, DOWN, buff=0.3).to_edge(LEFT, buff=0.5)
        self.play(FadeIn(sub, shift=UP * 0.12), run_time=0.5)
        self.read(0.7)

        qh = 8  # query heads

        def qhead(x, y, color=Q_C):
            return Triangle().scale(0.16).set_fill(color, 0.85).set_stroke(width=0).move_to([x, y, 0])

        def kvhead(x, y):
            k = Square(0.22, stroke_width=0, fill_color=K_C, fill_opacity=0.9)
            v = Square(0.22, stroke_width=0, fill_color=V_C, fill_opacity=0.9)
            return VGroup(k, v).arrange(RIGHT, buff=0.05).move_to([x, y, 0])

        def variant(title_txt, groups, cx, kv_saving):
            """One column: query heads on top, connectors to `groups` K/V heads below."""
            title = Text(title_txt, font_size=22, color=INK, weight="BOLD").move_to([cx, 1.9, 0])
            xs = np.linspace(cx - 1.5, cx + 1.5, qh)
            qs = VGroup(*[qhead(x, 0.95) for x in xs])
            # kv heads: `groups` of them, evenly spread
            kx = np.linspace(cx - 1.5, cx + 1.5, groups) if groups > 1 else [cx]
            kvs = VGroup(*[kvhead(x, -0.55) for x in kx])
            # connectors: each query head to its group's kv head
            conns = VGroup()
            for i, x in enumerate(xs):
                g = int(i / (qh / groups)) if groups > 1 else 0
                g = min(g, groups - 1)
                conns.add(Line([x, 0.82, 0], [kx[g], -0.35, 0], stroke_width=1.6,
                               color=FAINT).set_opacity(0.8))
            save = Text(kv_saving, font_size=18, color=GOOD).move_to([cx, -1.45, 0])
            return VGroup(title, qs, conns, kvs, save)

        mha = variant("MHA", 8, -4.4, "8 KV heads")
        gqa = variant("GQA", 2, 0.0, "2 groups  →  cache ÷ 4")
        mqa = variant("MQA", 1, 4.4, "1 KV head  →  cache ÷ 8")

        # reveal MHA first, with a "one K/V per query head" note
        self.play(FadeIn(mha[0]), LaggedStartMap(GrowFromCenter, mha[1], lag_ratio=0.06, run_time=0.9))
        self.play(Create(mha[2]), LaggedStartMap(FadeIn, mha[3], lag_ratio=0.08, run_time=0.7),
                  FadeIn(mha[4]))
        legend = VGroup(
            VGroup(Triangle().scale(0.13).set_fill(Q_C, 0.85).set_stroke(width=0),
                   Text("query head", font_size=16, color=INK)).arrange(RIGHT, buff=0.16),
            VGroup(VGroup(Square(0.18, stroke_width=0, fill_color=K_C, fill_opacity=0.9),
                          Square(0.18, stroke_width=0, fill_color=V_C, fill_opacity=0.9)).arrange(RIGHT, buff=0.04),
                   Text("K / V head", font_size=16, color=INK)).arrange(RIGHT, buff=0.16),
        ).arrange(RIGHT, buff=0.7).to_edge(DOWN, buff=1.5)
        self.play(FadeIn(legend), run_time=0.5)
        self.read(1.1)

        # GQA, then MQA
        self.play(FadeIn(gqa[0]), LaggedStartMap(GrowFromCenter, gqa[1], lag_ratio=0.05, run_time=0.7))
        self.play(Create(gqa[2]), FadeIn(gqa[3]), FadeIn(gqa[4]), run_time=0.7)
        self.read()
        self.play(FadeIn(mqa[0]), LaggedStartMap(GrowFromCenter, mqa[1], lag_ratio=0.05, run_time=0.7))
        self.play(Create(mqa[2]), FadeIn(mqa[3]), FadeIn(mqa[4]), run_time=0.7)
        self.read()

        # who uses what + a nod to PagedAttention
        self.play(FadeOut(legend), run_time=0.4)
        use = Text("GQA powers Llama-2/3 & Mistral — most of the memory win, little quality loss.",
                   font_size=21, color=INK).to_edge(DOWN, buff=1.4)
        if use.width > 12.9:
            use.scale_to_fit_width(12.9)
        self.play(FadeIn(use, shift=UP * 0.1), run_time=0.6)
        self.read(1.2)
        paged = Text("PagedAttention (vLLM) then manages the cache like OS virtual memory — no waste, higher throughput.",
                     font_size=20, color=ACCENT).to_edge(DOWN, buff=0.8)
        if paged.width > 12.9:
            paged.scale_to_fit_width(12.9)
        self.play(FadeIn(paged, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(self.cite("MQA: Shazeer 2019 · GQA: Ainslie et al. 2023 · PagedAttention: Kwon et al. 2023")),
                  run_time=0.4)
        self.read(1.5)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Closing takeaway (before the outro card)
    # ====================================================================== #
    def scene_recap(self):
        lines = VGroup(
            Text("The KV cache, in one breath:", font_size=30, color=MUTED),
            Text("A token's Keys and Values never change,", font_size=32, color=INK, weight="BOLD"),
            Text("so compute them once and store them.", font_size=32, color=INK, weight="BOLD"),
            Text("Generating the 1000th token is then almost as cheap as the first.",
                 font_size=26, color=ACCENT),
        ).arrange(DOWN, buff=0.34)
        self.play(FadeIn(lines[0]), run_time=0.6)
        self.read(0.5)
        self.play(Write(lines[1]), run_time=1.0)
        self.play(Write(lines[2]), run_time=1.0)
        self.read(1.1)
        self.play(FadeIn(lines[3], shift=UP * 0.12), run_time=0.8)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_waste()
        self.scene_reuse()
        self.scene_cache()
        self.scene_phases()
        self.scene_memory()
        self.scene_shrink()
        self.scene_recap()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_KVBase):
    def construct(self):
        self.play_intro()


class Waste(_KVBase):
    def construct(self):
        self.scene_waste()


class Reuse(_KVBase):
    def construct(self):
        self.scene_reuse()


class Cache(_KVBase):
    def construct(self):
        self.scene_cache()


class Phases(_KVBase):
    def construct(self):
        self.scene_phases()


class Memory(_KVBase):
    def construct(self):
        self.scene_memory()


class Shrink(_KVBase):
    def construct(self):
        self.scene_shrink()


class Recap(_KVBase):
    def construct(self):
        self.scene_recap()


class Outro(_KVBase):
    def construct(self):
        self.play_outro()


class KVCacheFilm(_KVBase):
    """The whole ~3-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    KVCacheFilm().render()

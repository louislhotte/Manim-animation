"""Vision Transformers — a ~3-minute explainer, house-style (measured 3:02).

How a Transformer, built for sequences of words, is made to see an image: cut the
picture into fixed-size patches, turn each patch into a token, and let self-
attention do the rest. Grounded in

    "An Image Is Worth 16x16 Words: Transformers for Image Recognition at Scale"
    Dosovitskiy, Beyer, Kolesnikov, Weissenborn, Zhai, Unterthiner, Dehghani,
    Minderer, Heigold, Gelly, Uszkoreit & Houlsby, ICLR 2021 (arXiv:2010.11929)

and the original attention mechanism of

    "Attention Is All You Need" — Vaswani et al., NeurIPS 2017 (arXiv:1706.03762)

Six scenes plus the channel's intro/outro cards:

    1. Idea      -- Transformers read sequences; treat an image as a sequence of patches
    2. Patchify  -- cut the image into a grid, flatten it into a sequence  [the headline]
    3. Embed     -- flatten each patch, project it, add a position, prepend [CLS]
    4. Encoder   -- the Transformer encoder block: LN, MSA, MLP, residuals, x L
    5. Attention -- self-attention is global from layer 1  (ViT vs a CNN's local kernel)
    6. Head      -- the [CLS] output -> MLP head -> softmax -> a class

The example image (a clean flat-design mountain landscape) is generated from
numpy at import time, so there are no asset files and nothing to download.

Everything uses ``Text`` (Pango) rather than ``Tex`` so it renders with no LaTeX
install. Scenes are exposed individually (``Idea``, ``Patchify``, ``Embed``,
``Encoder``, ``Attention``, ``Head``, ``Intro``, ``Outro``) and as one continuous
film (``VisionTransformerFilm``).

Env knobs:
    VIT_QUICK=1   shorten every hold for a fast sanity render
    VIT_DELAY=..  override the reading-hold multiplier (tunes total runtime)
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

# --- crisp text: render big, scale down (Pango mangles small sizes) --------- #
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("VIT_QUICK") == "1"
# One reading-rhythm knob. Every on-screen "hold" is scaled by DELAY; QUICK
# collapses the holds for fast iteration. Formula/diagram screens earn longer
# beats than prose, so DELAY sits a touch above 2.0.
DELAY = float(os.environ.get("VIT_DELAY", 0.28 if QUICK else 2.1))
END_HOLD = 0.2 if QUICK else 2.3  # settle held on a finished scene before it wipes

# ---- palette (shared with the Transformer / KV-cache films for continuity) - #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
FAINT = "#3A4152"       # gridlines
PATCH = "#C792EA"       # patches / tokens / embeddings (violet)
POS = "#8A7CFF"         # positional embeddings (indigo)
CLS_C = "#FF8C42"       # the [CLS] token (orange)
Q_C = "#5B8DEF"         # queries / CNN contrast (blue)
K_C = "#2EC4B6"         # keys (teal)
V_C = "#FFD166"         # values (gold)
ATTN = "#FF8C42"        # attention / ViT (orange)
MODEL_C = "#FFD166"     # model core (gold)
GOOD = "#3DD68C"        # chosen / pass (green)
BAD = "#FF5C5C"         # blocked / stop (red)
ACCENT = "#FFD166"      # gold rule

RNG = np.random.default_rng(7)

# A clean, well-hinted sans-serif everywhere (set on the *real* Text, shadowed).
FONT = "Helvetica Neue"
_BaseText.set_default(font=FONT)


# ======================================================================== #
#  The example image: a clean flat-design mountain landscape, from numpy
# ======================================================================== #
def make_landscape(px=512):
    ys = (np.arange(px)[:, None] / px) * np.ones((1, px))   # 0..1 top->bottom
    xs = (np.arange(px)[None, :] / px) * np.ones((px, 1))    # 0..1 left->right
    Y, X = ys, xs
    img = np.zeros((px, px, 3))

    sky_top = np.array([0.118, 0.227, 0.400])
    sky_bot = np.array([0.560, 0.745, 0.900])
    t = np.clip(Y / 0.74, 0, 1)[..., None]
    img[:] = sky_top * (1 - t) + sky_bot * t

    # sun with a soft glow
    sun_c = np.array([0.25, 0.24]); sun_r = 0.105
    sun_col = np.array([1.0, 0.82, 0.40])
    d = np.sqrt((X - sun_c[0]) ** 2 + (Y - sun_c[1]) ** 2)
    glow = np.clip(1 - d / (sun_r * 2.6), 0, 1)[..., None] ** 2
    img = img * (1 - glow * 0.55) + sun_col * (glow * 0.55)
    img[d < sun_r] = sun_col

    def mountain(cx, apex_y, half_w, base_y, color, snow, snow_to):
        prof = apex_y + (np.abs(X - cx) / half_w) * (base_y - apex_y)
        mask = (Y >= prof) & (Y <= base_y)
        img[mask] = color
        img[mask & (Y <= snow_to)] = snow

    snow = np.array([0.94, 0.96, 0.99])
    mountain(0.66, 0.36, 0.46, 0.82, np.array([0.31, 0.35, 0.50]), snow, 0.45)
    mountain(0.34, 0.44, 0.34, 0.84, np.array([0.20, 0.23, 0.35]), snow, 0.52)

    # grass band (covers the mountain feet -> a clean horizon)
    g_top = np.array([0.36, 0.62, 0.38]); g_bot = np.array([0.22, 0.45, 0.26])
    gt = np.clip((Y - 0.75) / 0.25, 0, 1)[..., None]
    grass = g_top * (1 - gt) + g_bot * gt
    gmask = Y >= 0.75
    img[gmask] = grass[gmask]

    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


PHOTO = make_landscape(512)   # baked once
NPATCH = 4                    # 4x4 = 16 patches (illustrative; ViT-B/16 -> 14x14)


def photo(height=3.8):
    return ImageMobject(PHOTO).set_height(height)


def make_tiles(n=NPATCH, tile_h=0.95):
    """A list of n*n ImageMobject tiles (raster order), each a crop of PHOTO."""
    ps = PHOTO.shape[0] // n
    tiles = []
    for r in range(n):
        for c in range(n):
            crop = PHOTO[r * ps:(r + 1) * ps, c * ps:(c + 1) * ps].copy()
            tiles.append(ImageMobject(crop).set_height(tile_h))
    return tiles


def place_grid(tiles, center, n, tile_h, buff=0.0):
    step = tile_h + buff
    for i, t in enumerate(tiles):
        r, c = divmod(i, n)
        t.set_height(tile_h)
        t.move_to([center[0] + (c - (n - 1) / 2) * step,
                   center[1] - (r - (n - 1) / 2) * step, 0])
    return tiles


def grid_overlay(center, size, n, color=INK, sw=2.6, op=0.95):
    half = size / 2
    g = VGroup()
    for k in range(1, n):
        off = -half + size * k / n
        g.add(Line([center[0] - half, center[1] + off, 0],
                   [center[0] + half, center[1] + off, 0]))
        g.add(Line([center[0] + off, center[1] - half, 0],
                   [center[0] + off, center[1] + half, 0]))
    border = Rectangle(width=size, height=size).move_to(center)
    g.add(border)
    g.set_stroke(color=color, width=sw, opacity=op)
    return g


# ---- small reusable pieces ------------------------------------------------ #
def txt(text, fs=24, color=INK, weight="NORMAL", slant=None, **extra):
    kw = {"font_size": fs, "color": color, "weight": weight}
    if slant:
        kw["slant"] = slant
    kw.update(extra)
    return Text(text, **kw)


def chip(text, color, w=2.3, h=0.95, fs=26, fill=0.14, tcolor=None, radius=0.14):
    box = RoundedRectangle(width=w, height=h, corner_radius=radius,
                           stroke_color=color, stroke_width=3,
                           fill_color=color, fill_opacity=fill)
    label = Text(text, font_size=fs, color=tcolor or INK, line_spacing=0.8)
    if label.width > w - 0.3:
        label.scale((w - 0.3) / label.width)
    label.move_to(box)
    return VGroup(box, label)


def harrow(start, end, color=MUTED, sw=4):
    return Arrow(start, end, buff=0.12, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.35, tip_length=0.2)


def dot_label(text, color, fs=22):
    d = Dot(radius=0.07, color=color)
    t = Text(text, font_size=fs, color=INK).next_to(d, RIGHT, buff=0.2)
    d.align_to(t, UP).shift(DOWN * 0.09)
    return VGroup(d, t)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.18, -0.18, 0], [0.18, 0.18, 0])
    b = Line([-0.18, 0.18, 0], [0.18, -0.18, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


def vec_col(vals, color=V_C, cw=0.3, stroke=FAINT):
    cells = VGroup()
    for v in vals:
        s = Square(side_length=cw, stroke_width=1, stroke_color=stroke)
        s.set_fill(color, opacity=float(0.15 + 0.8 * np.clip(v, 0, 1)))
        cells.add(s)
    cells.arrange(DOWN, buff=0)
    return cells


def rand_col(n, color=PATCH, cw=0.18):
    return vec_col([RNG.uniform(0.2, 0.95) for _ in range(n)], color=color, cw=cw)


def prob_bars(items, unit=3.4, fs=22, color=ATTN, gap=0.56):
    grp = VGroup()
    for i, (n, p) in enumerate(items):
        y = -i * gap
        lab = Text(n, font_size=fs, color=INK)
        lab.move_to([-lab.width / 2 - 0.2, y, 0])
        bw = max(0.03, unit * p)
        bar = Rectangle(width=bw, height=0.36, stroke_width=0,
                        fill_color=color, fill_opacity=0.9)
        bar.move_to([0.2 + bw / 2, y, 0])
        val = Text(f"{p:.2f}", font_size=fs - 5, color=MUTED).next_to(bar, RIGHT, buff=0.15)
        grp.add(VGroup(lab, bar, val))
    return grp


def mtext(parts, base_fs=32):
    """Inline 'formula' from Text pieces. Each part is (s, role[, color]) with
    role in {"b" base, "^" super, "_" sub}. Supers/subs attach to the last base."""
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


# ========================================================================== #
class _ViTBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # ---- timing helpers --------------------------------------------------- #
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.25))

    def wipe(self, rt=0.7):
        self.wait(END_HOLD)
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    def section_header(self, label, color):
        t = txt(label, fs=34, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=4)
        return VGroup(t, line)

    def say(self, text, color=INK, fs=25, y=-3.35, weight=NORMAL):
        cap = txt(text, fs=fs, color=color, weight=weight)
        if cap.width > 12.8:
            cap.scale_to_fit_width(12.8)
        cap.move_to([0, y, 0])
        return cap

    def cite(self):
        t = txt("An Image Is Worth 16x16 Words  ·  Dosovitskiy et al., ICLR 2021",
                fs=15, color=MUTED, slant=ITALIC).to_edge(DOWN, buff=0.16)
        return t

    # ---- house-style intro / outro cards ---------------------------------- #
    def _byline_and_rule(self, header):
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=ACCENT)
        writer = txt("Created by Ptolémé", fs=28, color=Q_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        return line, writer

    def play_intro(self):
        header = txt("Vision Transformers", fs=54, color=INK, weight="BOLD")
        header.set(width=min(10.5, header.width))
        line, writer = self._byline_and_rule(header)
        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        sub = txt("How a Transformer learns to see, one patch at a time", fs=32, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        src = txt("based on “An Image Is Worth 16x16 Words” · Dosovitskiy et al., 2021",
                  fs=22, color=MUTED)
        src.next_to(writer, DOWN, buff=0.4)
        self.play(FadeIn(src), run_time=0.8)
        self.card_wait(2.0)
        self.play(FadeOut(VGroup(header, writer, line, src)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = txt("Thank you for watching!", fs=48, color=INK, weight="BOLD")
        line, writer = self._byline_and_rule(header)
        self.play(Write(header), Create(line), run_time=1.5)
        self.card_wait(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.1)
        self.card_wait(2.2)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 — The idea: an image as a sequence of patches
    # ====================================================================== #
    def scene_idea(self):
        title = txt("Transformers read a sequence.", fs=44, color=INK, weight="BOLD")
        self.play(Write(title), run_time=1.4)
        self.beat(0.8)
        self.play(title.animate.scale(0.62).to_edge(UP, buff=0.45), run_time=0.7)

        # (a) words -> Transformer : the familiar case
        words = ["Not", "all", "those", "who", "wander"]
        toks = VGroup(*[chip(w, PATCH, w=1.25, h=0.6, fs=22) for w in words])
        toks.arrange(RIGHT, buff=0.18).move_to([0, 1.4, 0])
        model = chip("Transformer", MODEL_C, w=3.0, h=0.9, fs=24).move_to([0, 0.0, 0])
        a_in = harrow(toks.get_bottom(), model.get_top())
        self.play(LaggedStartMap(FadeIn, toks, shift=UP * 0.12, lag_ratio=0.18), run_time=1.2)
        self.play(GrowArrow(a_in), FadeIn(model), run_time=0.8)
        ok = txt("words in, meaning out. This is what it was built for.",
                 fs=22, color=MUTED).move_to([0, -1.0, 0])
        self.play(FadeIn(ok, shift=UP * 0.15), run_time=0.7)
        self.beat(1.4)

        # (b) but an image is not a sequence...
        self.play(FadeOut(VGroup(toks, a_in, ok)), FadeOut(model), run_time=0.6)
        pic = photo(2.9).move_to([-3.2, 0.15, 0])
        q = txt("?", fs=64, color=BAD, weight="BOLD").move_to([0.1, 0.15, 0])
        model2 = chip("Transformer", MODEL_C, w=3.0, h=0.9, fs=24).move_to([3.4, 0.15, 0])
        a_q = harrow(pic.get_right(), model2.get_left(), color=BAD)
        self.play(FadeIn(pic, shift=RIGHT * 0.2), run_time=0.8)
        self.play(FadeIn(model2), run_time=0.5)
        self.play(GrowArrow(a_q), FadeIn(q, scale=0.5), run_time=0.7)
        prob = txt("An image is a grid of pixels, not a line of words.",
                   fs=24, color=INK).move_to([0, -2.1, 0])
        self.play(FadeIn(prob, shift=UP * 0.15), run_time=0.7)
        self.beat(1.6)

        # (c) the pivot: cut it into patches, and each patch is a "word"
        self.play(FadeOut(VGroup(q, a_q, prob)), FadeOut(model2),
                  pic.animate.move_to([-3.4, 0.35, 0]).set_height(2.6), run_time=0.7)
        grid = grid_overlay(pic.get_center(), pic.height, NPATCH, color=INK, sw=2.2)
        self.play(Create(grid), run_time=1.0)
        idea = VGroup(
            txt("The trick:", fs=26, color=ACCENT, weight="BOLD"),
            txt("cut the image into fixed-size patches,", fs=24, color=INK),
            txt("and treat each patch as a “word.”", fs=24, color=INK),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to([2.4, 0.5, 0])
        self.play(LaggedStartMap(FadeIn, idea, shift=RIGHT * 0.12, lag_ratio=0.3), run_time=1.5)
        self.beat(1.2)
        paper = txt("“An Image Is Worth 16x16 Words”", fs=26, color=PATCH, weight="BOLD")
        paper.move_to([2.4, -1.5, 0])
        self.play(FadeIn(paper, shift=UP * 0.1), run_time=0.8)
        self.play(FadeIn(self.cite()), run_time=0.5)
        self.beat(1.6)
        self.wipe()

    # ====================================================================== #
    # Scene 2 — Patchify: cut the image into a sequence  [the headline]
    # ====================================================================== #
    def scene_patchify(self):
        header = self.section_header("1 · Cut the image into patches", PATCH)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        H = 3.7
        center = [0, 0.15, 0]
        pic = photo(H).move_to(center)
        self.play(FadeIn(pic, scale=0.96), run_time=0.9)
        self.beat(0.8)

        # (a) overlay the patch grid
        grid = grid_overlay(center, H, NPATCH, color=INK, sw=2.6)
        gcap = self.say("A grid of fixed-size squares. Here 4x4 = 16 patches.", y=-2.25)
        self.play(Create(grid), run_time=1.1)
        self.play(FadeIn(gcap, shift=UP * 0.12), run_time=0.6)
        self.beat(1.0)
        scale_note = txt("ViT-B/16 on a 224x224 image: 14x14 = 196 patches.",
                         fs=19, color=MUTED).move_to([0, -2.9, 0])
        self.play(FadeIn(scale_note), run_time=0.6)
        self.beat(1.2)

        # (b) swap the seamless photo for real tiles, then open the gaps
        tiles = make_tiles(NPATCH, tile_h=H / NPATCH)
        place_grid(tiles, center, NPATCH, H / NPATCH, buff=0.0)
        tg = Group(*tiles)
        self.add(tg)
        self.remove(pic)
        self.play(FadeOut(grid), FadeOut(scale_note), run_time=0.4)
        place_targets = {}
        step = H / NPATCH + 0.12
        for i, t in enumerate(tiles):
            r, c = divmod(i, NPATCH)
            place_targets[i] = [center[0] + (c - (NPATCH - 1) / 2) * step,
                                center[1] - (r - (NPATCH - 1) / 2) * step, 0]
        self.play(*[t.animate.move_to(place_targets[i]) for i, t in enumerate(tiles)],
                  run_time=1.1)
        self.play(FadeOut(gcap), run_time=0.4)
        self.beat(0.8)

        # (c) flatten in reading order into a single sequence
        flat_h = 0.62
        fstep = 0.66
        row_y = -0.2
        x0 = -(NPATCH * NPATCH - 1) / 2 * fstep
        row_cap = self.say("The patches are lined up in reading order: left to right, "
                           "then top to bottom.", y=-3.35)
        self.play(FadeIn(row_cap, shift=UP * 0.1), run_time=0.6)
        self.play(
            LaggedStart(*[t.animate.set_height(flat_h).move_to([x0 + i * fstep, row_y, 0])
                          for i, t in enumerate(tiles)],
                        lag_ratio=0.10),
            run_time=2.6,
        )
        self.beat(0.8)

        # brace + label: this is now a sequence
        brace = Brace(Group(*tiles), DOWN, color=MUTED)
        seqlab = txt("a sequence of 16 patches", fs=24, color=PATCH).next_to(brace, DOWN, buff=0.18)
        self.play(FadeOut(row_cap), GrowFromCenter(brace), FadeIn(seqlab), run_time=0.9)
        self.beat(1.0)
        punch = self.say("Now the image is a sequence, just like tokens of text.",
                         color=INK, y=1.7)
        self.play(FadeIn(punch, shift=UP * 0.12), run_time=0.7)
        self.beat(1.8)
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Embed: patch -> token (+ position, + [CLS])
    # ====================================================================== #
    def scene_embed(self):
        header = self.section_header("2 · Turn each patch into a token", PATCH)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # one patch, enlarged (the sun patch reads nicely)
        ps = PHOTO.shape[0] // NPATCH
        crop = PHOTO[0:ps, ps:2 * ps].copy()   # row 0, col 1 -> the sun
        one = ImageMobject(crop).set_height(1.5).to_edge(LEFT, buff=1.0).shift(UP * 1.4)
        olab = txt("one patch\n(16x16x3)", fs=18, color=MUTED, line_spacing=0.7).next_to(one, DOWN, buff=0.2)
        self.play(FadeIn(one, scale=0.9), FadeIn(olab), run_time=0.8)
        self.beat(0.6)

        # flatten -> a long vector of raw numbers
        flat = vec_col([RNG.uniform(0.2, 0.95) for _ in range(11)], color=MUTED, cw=0.22)
        flat.next_to(one, RIGHT, buff=1.5).align_to(one, UP)
        flab = txt("flatten\n768 numbers", fs=18, color=MUTED, line_spacing=0.7).next_to(flat, DOWN, buff=0.2)
        a1 = harrow(one.get_right(), flat.get_left(), color=MUTED, sw=3)
        self.play(GrowArrow(a1), FadeIn(flat, shift=RIGHT * 0.1), FadeIn(flab), run_time=0.9)
        self.beat(0.8)

        # linear projection -> a patch embedding
        emb = vec_col([RNG.uniform(0.2, 0.95) for _ in range(8)], color=PATCH, cw=0.24)
        emb.next_to(flat, RIGHT, buff=1.9).align_to(one, UP).shift(DOWN * 0.15)
        elab = txt("patch\nembedding", fs=18, color=PATCH, line_spacing=0.7).next_to(emb, DOWN, buff=0.2)
        a2 = harrow(flat.get_right(), emb.get_left(), color=PATCH, sw=3)
        wp = mtext([("W", "b"), ("p", "_")], base_fs=19)
        wlab = VGroup(txt("×", fs=19), wp, txt("(linear)", fs=19, color=MUTED)).arrange(
            RIGHT, buff=0.14, aligned_edge=DOWN).next_to(a2, UP, buff=0.16)
        self.play(GrowArrow(a2), FadeIn(wlab), TransformFromCopy(flat, emb), FadeIn(elab), run_time=1.1)
        dnote = self.say("A learned linear projection: each patch becomes one "
                         "D-dimensional vector  (ViT-B: D = 768).", y=-1.3)
        self.play(FadeIn(dnote), run_time=0.6)
        self.beat(1.4)

        # every patch -> its own embedding column, laid out as a row
        self.play(FadeOut(VGroup(a1, a2, wlab, flat, flab, olab, elab, dnote)),
                  FadeOut(one),
                  emb.animate.set_height(1.1), run_time=0.6)
        cols = VGroup(*[rand_col(6, color=PATCH, cw=0.17) for _ in range(NPATCH * NPATCH)])
        cols.arrange(RIGHT, buff=0.13).move_to([0, 1.2, 0])
        self.play(ReplacementTransform(emb, cols[0]),
                  LaggedStartMap(FadeIn, cols[1:], shift=UP * 0.1, lag_ratio=0.05), run_time=1.6)
        allcap = txt("Do this for all 16 patches: 16 embedding vectors.",
                     fs=22, color=INK).next_to(cols, DOWN, buff=0.45)
        self.play(FadeIn(allcap, shift=UP * 0.1), run_time=0.6)
        self.beat(1.2)

        # add positional embeddings
        self.play(FadeOut(allcap), run_time=0.3)
        pos_chips = VGroup(*[rand_col(6, color=POS, cw=0.17) for _ in range(NPATCH * NPATCH)])
        for pc, col in zip(pos_chips, cols):
            pc.next_to(col, DOWN, buff=0.55).match_x(col)
        plus = VGroup(*[txt("+", fs=20, color=INK).move_to(
            [col.get_center()[0], (col.get_bottom()[1] + pc.get_top()[1]) / 2, 0])
            for col, pc in zip(cols, pos_chips)])
        poslab = txt("+ position embeddings  (learned: which patch went where)",
                     fs=21, color=POS).next_to(pos_chips, DOWN, buff=0.35)
        self.play(LaggedStartMap(FadeIn, pos_chips, shift=UP * 0.1, lag_ratio=0.04),
                  FadeIn(plus), run_time=1.3)
        self.play(FadeIn(poslab, shift=UP * 0.1), run_time=0.6)
        self.beat(1.0)
        # fold position into the token (sum) -> single tokens
        toks = VGroup(*[rand_col(6, color=PATCH, cw=0.17) for _ in range(NPATCH * NPATCH)])
        toks.arrange(RIGHT, buff=0.12).move_to(cols)
        self.play(FadeOut(pos_chips), FadeOut(plus), FadeOut(poslab),
                  ReplacementTransform(cols, toks), run_time=0.9)
        self.beat(0.5)

        # prepend the [CLS] token, then explain it in plain sentences
        cls = chip("CLS", CLS_C, w=0.7, h=toks.height + 0.06, fs=20)
        cls.next_to(toks, LEFT, buff=0.22).align_to(toks, UP)
        seq = Group(cls, toks)
        self.play(FadeIn(cls, shift=RIGHT * 0.15), run_time=0.7)
        self.play(seq.animate.move_to([0, 1.4, 0]), run_time=0.7)
        clslab = self.say("We also add one extra learnable token, called [CLS], "
                          "at the front.", color=INK, y=-0.2)
        clslab2 = self.say("After the encoder, its output vector will stand for the "
                           "whole image.", color=MUTED, y=-1.0)
        self.play(FadeIn(clslab, shift=UP * 0.1), run_time=0.6)
        self.beat(1.0)
        self.play(FadeIn(clslab2, shift=UP * 0.1), run_time=0.6)
        self.beat(1.2)
        result = txt("The image is now a sequence of tokens, which is exactly what a "
                     "Transformer reads.", fs=24, color=ACCENT, weight="BOLD")
        if result.width > 12.8:
            result.scale_to_fit_width(12.8)
        result.move_to([0, -2.3, 0])
        self.play(FadeIn(result, shift=UP * 0.1), run_time=0.7)
        self.beat(1.8)
        self.wipe()

    # ====================================================================== #
    # Scene 4 — The Transformer encoder block
    # ====================================================================== #
    def scene_encoder(self):
        header = self.section_header("3 · The Transformer encoder", ATTN)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # the encoder block, bottom -> top:  LN -> MSA -> (+) -> LN -> MLP -> (+)
        ln1 = chip("LayerNorm", MUTED, w=4.0, h=0.42, fs=18)
        msa = chip("Multi-Head Self-Attention", ATTN, w=4.0, h=0.62, fs=18)
        ln2 = chip("LayerNorm", MUTED, w=4.0, h=0.42, fs=18)
        mlp = chip("MLP  (GELU)", V_C, w=4.0, h=0.58, fs=19)
        inner = VGroup(ln1, msa, ln2, mlp).arrange(UP, buff=0.44)
        block = SurroundingRectangle(inner, buff=0.28, color=INK, corner_radius=0.16).set_stroke(width=2)
        sh1 = block.copy().set_stroke(INK, width=2, opacity=0.28).shift(UR * 0.12)
        sh2 = block.copy().set_stroke(INK, width=2, opacity=0.16).shift(UR * 0.24)
        stack = Group(sh2, sh1, block, inner)
        stack.move_to([-2.7, 0.2, 0])
        inner.move_to(block)
        nlab = txt("× L", fs=22, color=INK, weight="BOLD").move_to(
            [sh2.get_right()[0] + 0.45, sh2.get_top()[1] - 0.12, 0])

        # short input / output arrows; a light hint of the tokens coming in
        a_in = Arrow(block.get_bottom() + DOWN * 0.85, block.get_bottom(), buff=0.04,
                     stroke_width=3, color=MUTED, max_tip_length_to_length_ratio=0.4, tip_length=0.16)
        tin = txt("patch tokens in  (+ CLS, + position)", fs=17, color=MUTED).next_to(a_in, DOWN, buff=0.16)
        a_out = Arrow(block.get_top(), block.get_top() + UP * 0.7, buff=0.04,
                      stroke_width=3, color=MUTED, max_tip_length_to_length_ratio=0.4, tip_length=0.16)

        self.play(FadeIn(Group(sh2, sh1, block)), FadeIn(nlab), run_time=0.8)
        self.play(GrowArrow(a_in), FadeIn(tin), run_time=0.5)
        for m in (ln1, msa, ln2, mlp):
            self.play(FadeIn(m, shift=UP * 0.1), run_time=0.4)
        self.beat(0.4)

        # residual skips (the "+") tucked inside the block's left edge
        def skip(sub_lo, sub_hi):
            x = block.get_left()[0] + 0.16
            y0 = sub_lo.get_bottom()[1] - 0.12
            y1 = sub_hi.get_top()[1] + 0.12
            p = VMobject(stroke_color=GOOD, stroke_width=2.6)
            p.set_points_as_corners([
                np.array([sub_lo.get_left()[0], y0, 0]), np.array([x, y0, 0]),
                np.array([x, y1, 0]), np.array([sub_hi.get_left()[0], y1, 0]),
            ])
            plus = txt("+", fs=20, color=GOOD).move_to([sub_hi.get_left()[0] + 0.14, y1, 0])
            return VGroup(p, plus)
        res1, res2 = skip(ln1, msa), skip(ln2, mlp)
        rescap = txt("residual\nconnections", fs=15, color=GOOD, line_spacing=0.7)
        rescap.next_to(block, LEFT, buff=0.25)
        self.play(Create(res1), Create(res2), FadeIn(rescap), run_time=0.9)
        self.beat(0.5)

        # short annotations on the RIGHT, with a clear gap from the block
        def note(anchor, s, color):
            d = Dot(radius=0.05, color=color).move_to([0.55, anchor.get_center()[1], 0])
            t = txt(s, fs=19, color=INK).next_to(d, RIGHT, buff=0.16)
            ln = DashedLine(anchor.get_right(), d.get_left(), stroke_width=1.5,
                            color=color, dash_length=0.06).set_opacity(0.55)
            return VGroup(ln, d, t)
        notes = [
            (msa, "mixes information across all patches", ATTN),
            (mlp, "transforms each token on its own", V_C),
            (ln1, "normalizes; keeps the signal stable", MUTED),
        ]
        for anchor, s, col in notes:
            n = note(anchor, s, col)
            self.play(FadeIn(n, shift=RIGHT * 0.1), Indicate(anchor, color=col, scale_factor=1.05),
                      run_time=0.7)
            self.beat(0.6)

        self.play(GrowArrow(a_out), run_time=0.5)
        # the key contrast with a text decoder, as a bottom caption (clear of the header)
        nomask = self.say("No causal mask: unlike a text decoder, a patch may attend "
                          "in every direction.", color=GOOD, y=-3.45)
        self.play(FadeIn(nomask, shift=UP * 0.1), Circumscribe(block, color=ATTN, run_time=1.4))
        self.beat(1.8)
        self.wipe()

    # ====================================================================== #
    # Scene 5 — Attention is global (ViT vs CNN)
    # ====================================================================== #
    def scene_attention(self):
        header = self.section_header("4 · Attention is global", ATTN)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # two copies of the image grid, side by side
        gh = 2.7
        left_c = [-3.5, 0.5, 0]
        right_c = [3.5, 0.5, 0]
        left_tiles = make_tiles(NPATCH, gh / NPATCH)
        place_grid(left_tiles, left_c, NPATCH, gh / NPATCH, buff=0.0)
        right_tiles = make_tiles(NPATCH, gh / NPATCH)
        place_grid(right_tiles, right_c, NPATCH, gh / NPATCH, buff=0.0)
        lg, rg = Group(*left_tiles), Group(*right_tiles)
        lgrid = grid_overlay(left_c, gh, NPATCH, color=BG, sw=1.5, op=0.7)
        rgrid = grid_overlay(right_c, gh, NPATCH, color=BG, sw=1.5, op=0.7)
        ltitle = txt("CNN", fs=26, color=Q_C, weight="BOLD").next_to(lg, UP, buff=0.28)
        rtitle = txt("ViT", fs=26, color=ATTN, weight="BOLD").next_to(rg, UP, buff=0.28)
        self.play(FadeIn(lg), FadeIn(rg), FadeIn(lgrid), FadeIn(rgrid),
                  FadeIn(ltitle), FadeIn(rtitle), run_time=1.0)
        self.beat(0.6)

        def cell_center(center, i):
            r, c = divmod(i, NPATCH)
            s = gh / NPATCH
            return np.array([center[0] + (c - (NPATCH - 1) / 2) * s,
                             center[1] - (r - (NPATCH - 1) / 2) * s, 0])

        # (a) CNN: a small local kernel around one cell
        qi = 9  # a mountain cell (row 2, col 1)
        kernel_cells = [qi - NPATCH - 1, qi - NPATCH, qi - NPATCH + 1,
                        qi - 1, qi, qi + 1,
                        qi + NPATCH - 1, qi + NPATCH, qi + NPATCH + 1]
        s = gh / NPATCH
        kbox = VGroup(*[Square(s, stroke_width=0).move_to(cell_center(left_c, k))
                        for k in kernel_cells if 0 <= k < NPATCH * NPATCH])
        kbox_o = SurroundingRectangle(kbox, color=Q_C, buff=0.0, corner_radius=0.0).set_stroke(width=4)
        qmark_l = SurroundingRectangle(
            VGroup(Square(s).move_to(cell_center(left_c, qi))), color=INK, buff=0.0).set_stroke(width=3)
        lcap = txt("sees a small\nlocal neighborhood", fs=19, color=Q_C, line_spacing=0.8)
        lcap.next_to(lg, DOWN, buff=0.35)
        self.play(Create(kbox_o), Create(qmark_l), run_time=0.8)
        self.play(FadeIn(lcap, shift=UP * 0.1), run_time=0.6)
        self.beat(1.2)

        # (b) ViT: one query attends to ALL cells (lines + weighted glow)
        rq = 9
        weights = RNG.uniform(0.15, 1.0, size=NPATCH * NPATCH)
        weights[[8, 9, 10, 6, 5]] = [0.9, 1.0, 0.85, 0.7, 0.6]  # nearby mountains hot
        lines = VGroup()
        for i in range(NPATCH * NPATCH):
            if i == rq:
                continue
            ln = Line(cell_center(right_c, rq), cell_center(right_c, i),
                      stroke_width=1.0 + 3.0 * weights[i], color=ATTN)
            ln.set_stroke(opacity=0.25 + 0.6 * weights[i])
            lines.add(ln)
        qmark_r = SurroundingRectangle(
            VGroup(Square(s).move_to(cell_center(right_c, rq))), color=INK, buff=0.0).set_stroke(width=3)
        rcap = txt("attends to every patch,\nfrom the very first layer", fs=19, color=ATTN, line_spacing=0.8)
        rcap.next_to(rg, DOWN, buff=0.35)
        self.play(Create(qmark_r), run_time=0.5)
        self.play(LaggedStartMap(Create, lines, lag_ratio=0.04), run_time=1.6)
        self.play(FadeIn(rcap, shift=UP * 0.1), run_time=0.6)
        self.beat(1.6)

        # the takeaway line
        take = self.say("A CNN builds up context slowly with depth. A ViT has the "
                        "whole picture at once.", color=INK, y=-2.7)
        self.play(FadeIn(take, shift=UP * 0.1), run_time=0.7)
        self.beat(1.2)
        cost = txt("The price: fewer built-in priors, so ViTs need lots of data. "
                   "Given it, they scale beautifully.", fs=20, color=MUTED)
        if cost.width > 12.8:
            cost.scale_to_fit_width(12.8)
        cost.move_to([0, -3.45, 0])
        self.play(FadeIn(cost), run_time=0.7)
        self.beat(1.8)
        self.wipe()

    # ====================================================================== #
    # Scene 6 — The classification head
    # ====================================================================== #
    def scene_head(self):
        header = self.section_header("5 · Read out the class", GOOD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # the output sequence, with the CLS token highlighted
        seq = VGroup(*[rand_col(5, color=PATCH, cw=0.14) for _ in range(9)])
        seq.arrange(RIGHT, buff=0.1)
        cls = chip("CLS", CLS_C, w=0.55, h=seq.height + 0.05, fs=15).next_to(seq, LEFT, buff=0.14)
        tokens = VGroup(cls, seq).move_to([-2.4, 2.0, 0])
        tlab = txt("encoder output (after x L)", fs=18, color=MUTED).next_to(tokens, UP, buff=0.16)
        self.play(FadeIn(tokens), FadeIn(tlab), run_time=0.7)
        pick = SurroundingRectangle(cls, color=GOOD, buff=0.06, corner_radius=0.08)
        take = txt("take only the [CLS] output", fs=20, color=GOOD).next_to(tokens, DOWN, buff=0.3)
        take.align_to(cls, LEFT)
        self.play(Create(pick), FadeIn(take, shift=UP * 0.1), run_time=0.8)
        self.beat(1.0)

        # CLS vector -> MLP head -> softmax -> probabilities
        clsvec = vec_col([RNG.uniform(0.2, 0.95) for _ in range(6)], color=CLS_C, cw=0.2)
        clsvec.move_to([-4.6, -0.7, 0])
        head = chip("MLP head", Q_C, w=1.9, h=0.85, fs=22).next_to(clsvec, RIGHT, buff=1.0)
        soft = chip("softmax", GOOD, w=1.7, h=0.7, fs=20).next_to(head, RIGHT, buff=1.0)
        a0 = harrow(cls.get_bottom(), clsvec.get_top(), color=GOOD, sw=3)
        a1 = harrow(clsvec.get_right(), head.get_left(), sw=3)
        a2 = harrow(head.get_right(), soft.get_left(), color=Q_C, sw=3)
        self.play(GrowArrow(a0), FadeIn(clsvec, shift=DOWN * 0.1), run_time=0.7)
        self.play(GrowArrow(a1), FadeIn(head), run_time=0.6)
        self.play(GrowArrow(a2), FadeIn(soft), run_time=0.6)

        dist = prob_bars([("mountain", 0.91), ("volcano", 0.04),
                          ("hill", 0.03), ("valley", 0.02)], unit=2.6, fs=22)
        dist.next_to(soft, RIGHT, buff=1.1).shift(UP * 0.15)
        a3 = harrow(soft.get_right(), dist.get_left() + LEFT * 0.1, color=GOOD, sw=3)
        self.play(GrowArrow(a3),
                  LaggedStart(*[FadeIn(r[0]) for r in dist],
                              *[GrowFromEdge(r[1], LEFT) for r in dist],
                              *[FadeIn(r[2]) for r in dist], lag_ratio=0.1), run_time=1.5)
        self.beat(1.0)

        # the winner, stamped on the picture
        win = SurroundingRectangle(dist[0], color=GOOD, buff=0.08, corner_radius=0.06)
        pic = photo(1.9).move_to([-4.7, -0.75, 0])
        stamp = txt("mountain", fs=22, color=GOOD, weight="BOLD").next_to(pic, DOWN, buff=0.18)
        self.play(Create(win), Flash(dist[0], color=GOOD, flash_radius=0.9), run_time=0.8)
        self.play(FadeOut(VGroup(clsvec, a0, a1, head, a2, soft, a3)), run_time=0.5)
        self.play(FadeIn(pic, shift=RIGHT * 0.1), FadeIn(stamp), run_time=0.6)
        self.beat(1.2)

        # recap
        self.play(FadeOut(VGroup(tokens, tlab, pick, take, dist, win)),
                  FadeOut(pic), FadeOut(stamp), run_time=0.7)
        recap = VGroup(
            txt("patchify", fs=30, color=PATCH, weight="BOLD"),
            txt("→", fs=30, color=MUTED),
            txt("embed", fs=30, color=POS, weight="BOLD"),
            txt("→", fs=30, color=MUTED),
            txt("attend", fs=30, color=ATTN, weight="BOLD"),
            txt("→", fs=30, color=MUTED),
            txt("classify", fs=30, color=GOOD, weight="BOLD"),
        ).arrange(RIGHT, buff=0.3).move_to([0, 0.7, 0])
        self.play(LaggedStartMap(FadeIn, recap, shift=UP * 0.12, lag_ratio=0.18), run_time=1.6)
        kicker = txt("No convolutions. Just attention over patches.",
                     fs=30, color=INK, weight="BOLD").move_to([0, -0.9, 0])
        self.play(Write(kicker), run_time=1.4)
        self.beat(2.0)
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_idea()
        self.scene_patchify()
        self.scene_embed()
        self.scene_encoder()
        self.scene_attention()
        self.scene_head()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_ViTBase):
    def construct(self):
        self.play_intro()


class Idea(_ViTBase):
    def construct(self):
        self.scene_idea()


class Patchify(_ViTBase):
    def construct(self):
        self.scene_patchify()


class Embed(_ViTBase):
    def construct(self):
        self.scene_embed()


class Encoder(_ViTBase):
    def construct(self):
        self.scene_encoder()


class Attention(_ViTBase):
    def construct(self):
        self.scene_attention()


class Head(_ViTBase):
    def construct(self):
        self.scene_head()


class Outro(_ViTBase):
    def construct(self):
        self.play_outro()


class VisionTransformerFilm(_ViTBase):
    """The whole ~3-minute film (measured 3:02), intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    VisionTransformerFilm().render()

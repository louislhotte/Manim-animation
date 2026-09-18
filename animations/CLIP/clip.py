"""What is CLIP? — a short, house-style explainer.

How one model learns to line up images and text in a single vector space, and
why that turns plain language into an open-ended image classifier. Grounded in

    "Learning Transferable Visual Models From Natural Language Supervision"
    — Radford, Kim, Hallacy, Ramesh, Goh, Agarwal, Sastry, Askell, Mishkin,
      Clark, Krueger & Sutskever, ICML 2021  (arXiv:2103.00020)

The path:

    1. Problem   -- fixed-label classifiers only know their list; the web is full
                    of (image, caption) pairs, so let language be the supervision.
    2. Encoders  -- an image encoder and a text encoder map into ONE shared space.
    3. Contrast  -- score every image against every caption; pull the matching
                    (diagonal) pairs together and push the rest apart.
    4. Zero-shot -- write the labels as prompts, embed them, pick the closest.
                    Swap the words and you have a brand-new classifier, no retrain.

Bookended by the channel's intro/outro cards. Everything uses ``Text`` (Pango)
rather than ``Tex`` so it renders with no LaTeX install and stays fast to iterate.

Scenes are exposed individually (``Problem``, ``Encoders``, ``Contrast``,
``ZeroShot``, ``Intro``, ``Outro``) and as one continuous film (``WhatIsCLIP``).

Env knobs:
    CLIP_QUICK=1        shorten every hold for a fast sanity render
    CLIP_DELAY=<sec>    override the reading-hold multiplier (default 2.0)
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

QUICK = os.environ.get("CLIP_QUICK") == "1"
# Single pacing knob: every on-screen "hold" is scaled by DELAY. QUICK collapses
# the holds for fast iteration; otherwise it sets the reading rhythm.
DELAY = float(os.environ.get("CLIP_DELAY", 0.28 if QUICK else 2.0))
END_HOLD = 0.2 if QUICK else 2.0

# ---- palette -------------------------------------------------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
FAINT = "#3A4251"       # hairlines
PANEL = "#161B26"       # panel fill
IMG_C = "#2EC4B6"       # the image modality (teal)
TXT_C = "#C792EA"       # the text modality (violet)
GOOD = "#3DD68C"        # a match / chosen (green)
BAD = "#FF5C5C"         # a mismatch / rejected (red)
GOLD = "#FFD166"        # accent
BLUE = "#5B8DEF"        # byline

# distinct colours for the five example concepts (kept clear of the modality
# colours so a glyph never reads as "an image encoder" or "a text encoder").
CONCEPT_COLORS = {
    "cat": "#FF8C42",     # orange
    "dog": "#57B6FF",     # sky blue
    "plane": "#E06CD9",   # pink
    "car": "#FFD166",     # gold
    "ship": "#7C8CFF",    # periwinkle
}

RNG = np.random.default_rng(7)

FONT = "Helvetica Neue"

# ---- crisp text (MANDATORY house shim) ------------------------------------ #
# Pango mangles letter/word spacing below ~20 pt. Render every ``Text`` at a
# large base size and scale the mobject DOWN so spacing stays crisp and any
# small piece (sub/superscript) keeps the body font.
_BaseText = Text
_BaseText.set_default(font=FONT)
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


# ========================================================================== #
# small reusable pieces
# ========================================================================== #
def txt(text, fs=26, color=INK, weight="NORMAL", slant=None, **extra):
    kw = dict(font_size=fs, color=color, weight=weight, **extra)
    if slant is not None:
        kw["slant"] = slant
    return Text(text, **kw)


def arr(a, b, color=MUTED, sw=4, buff=0.15, tip=0.2):
    return Arrow(a, b, buff=buff, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.32, tip_length=tip)


def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])])
    v.set_stroke(color=color, width=sw)
    return v.scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.18, -0.18, 0], [0.18, 0.18, 0])
    b = Line([-0.18, 0.18, 0], [0.18, -0.18, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


def chip(text, color, w=None, h=0.6, fs=24, fill=0.14, tcolor=None, radius=0.14):
    """A rounded, tinted box with a centred, auto-fitting label. grp[0] is the box."""
    label = Text(text, font_size=fs, color=tcolor or INK)
    w = w or max(0.9, label.width + 0.45)
    box = RoundedRectangle(width=w, height=h, corner_radius=radius,
                           stroke_color=color, stroke_width=2.4,
                           fill_color=color, fill_opacity=fill)
    if label.width > w - 0.25:
        label.scale((w - 0.25) / label.width)
    label.move_to(box)
    g = VGroup(box, label)
    g.box, g.label = box, label
    return g


# ========================================================================== #
# concept glyphs — hand-drawn, no assets. Each ~1 unit tall, centred on origin.
# ========================================================================== #
def _poly(pts, color, fill=0.18, sw=3):
    return Polygon(*[np.array([x, y, 0]) for x, y in pts],
                   stroke_color=color, stroke_width=sw, fill_color=color, fill_opacity=fill)


def cat_glyph(color, s=1.0):
    ear_l = _poly([(-0.36, 0.22), (-0.52, 0.62), (-0.10, 0.40)], color, fill=0.16)
    ear_r = _poly([(0.36, 0.22), (0.52, 0.62), (0.10, 0.40)], color, fill=0.16)
    head = Circle(radius=0.40, stroke_color=color, stroke_width=3.2,
                  fill_color=color, fill_opacity=0.16)
    eye_l = Dot(radius=0.055, color=color).move_to([-0.15, 0.05, 0])
    eye_r = Dot(radius=0.055, color=color).move_to([0.15, 0.05, 0])
    nose = _poly([(-0.05, -0.06), (0.05, -0.06), (0.0, -0.15)], color, fill=0.6, sw=2)
    wh = VGroup()
    for sgn in (-1, 1):
        wh.add(Line([sgn * 0.07, -0.10, 0], [sgn * 0.42, -0.04, 0], stroke_color=color, stroke_width=2))
        wh.add(Line([sgn * 0.07, -0.15, 0], [sgn * 0.42, -0.18, 0], stroke_color=color, stroke_width=2))
    return VGroup(ear_l, ear_r, head, eye_l, eye_r, nose, wh).scale(s)


def dog_glyph(color, s=1.0):
    ear_l = RoundedRectangle(width=0.24, height=0.56, corner_radius=0.12,
                             stroke_color=color, stroke_width=3, fill_color=color,
                             fill_opacity=0.22).move_to([-0.40, 0.04, 0]).rotate(0.20)
    ear_r = RoundedRectangle(width=0.24, height=0.56, corner_radius=0.12,
                             stroke_color=color, stroke_width=3, fill_color=color,
                             fill_opacity=0.22).move_to([0.40, 0.04, 0]).rotate(-0.20)
    head = RoundedRectangle(width=0.74, height=0.66, corner_radius=0.26,
                            stroke_color=color, stroke_width=3.2, fill_color=color, fill_opacity=0.16)
    snout = RoundedRectangle(width=0.44, height=0.30, corner_radius=0.12,
                             stroke_color=color, stroke_width=2.6, fill_color=color,
                             fill_opacity=0.28).move_to([0, -0.19, 0])
    nose = Dot(radius=0.07, color=color).move_to([0, -0.29, 0])
    eye_l = Dot(radius=0.055, color=color).move_to([-0.16, 0.11, 0])
    eye_r = Dot(radius=0.055, color=color).move_to([0.16, 0.11, 0])
    return VGroup(ear_l, ear_r, head, snout, nose, eye_l, eye_r).scale(s)


def plane_glyph(color, s=1.0):
    fuse = RoundedRectangle(width=1.5, height=0.28, corner_radius=0.14,
                            stroke_color=color, stroke_width=3.2, fill_color=color, fill_opacity=0.16)
    nose = _poly([(0.74, 0.14), (0.74, -0.14), (1.02, 0.0)], color)
    wing = _poly([(0.12, 0.02), (-0.5, 0.66), (-0.24, 0.66), (0.34, 0.02)], color)
    wing2 = _poly([(0.12, -0.02), (-0.5, -0.66), (-0.24, -0.66), (0.34, -0.02)], color)
    tail = _poly([(-0.62, 0.06), (-0.86, 0.44), (-0.66, 0.44), (-0.44, 0.06)], color)
    win = VGroup(*[Dot(radius=0.045, color=color).set_opacity(0.7).move_to([x, 0.0, 0])
                   for x in (-0.1, 0.06, 0.22, 0.38)])
    return VGroup(wing, wing2, fuse, nose, tail, win).scale(s)


def car_glyph(color, s=1.0):
    body = RoundedRectangle(width=1.5, height=0.5, corner_radius=0.16,
                            stroke_color=color, stroke_width=3.2, fill_color=color, fill_opacity=0.16)
    body.shift(UP * 0.05)
    cabin = _poly([(-0.5, 0.28), (0.18, 0.28), (0.34, 0.62), (-0.34, 0.62)], color, sw=3.2)
    win = _poly([(-0.34, 0.32), (0.04, 0.32), (0.14, 0.56), (-0.24, 0.56)], color, fill=0.32)
    wheels = VGroup()
    for wx in (-0.45, 0.45):
        outer = Circle(radius=0.2, stroke_color=color, stroke_width=3, fill_color=BG, fill_opacity=1)
        inner = Circle(radius=0.09, stroke_width=0, fill_color=color, fill_opacity=0.7)
        wheels.add(VGroup(outer, inner).move_to([wx, -0.22, 0]))
    return VGroup(body, cabin, win, wheels).scale(s)


def ship_glyph(color, s=1.0):
    hull = _poly([(-0.78, -0.02), (0.78, -0.02), (0.56, -0.42), (-0.56, -0.42)], color)
    deck = RoundedRectangle(width=0.62, height=0.3, corner_radius=0.05,
                            stroke_color=color, stroke_width=3, fill_color=color, fill_opacity=0.16)
    deck.move_to([-0.06, 0.16, 0])
    funnel = RoundedRectangle(width=0.16, height=0.34, corner_radius=0.04,
                              stroke_color=color, stroke_width=2.6, fill_color=color, fill_opacity=0.3)
    funnel.move_to([0.2, 0.28, 0])
    mast = Line([-0.32, 0.3, 0], [-0.32, 0.66, 0], stroke_color=color, stroke_width=2.6)
    flag = _poly([(-0.32, 0.66), (-0.12, 0.58), (-0.32, 0.5)], color, fill=0.5, sw=2)
    wave = VMobject(stroke_color=color, stroke_width=2.4).set_points_as_corners(
        [np.array([x, -0.5 + 0.05 * (i % 2), 0]) for i, x in enumerate(np.linspace(-0.8, 0.8, 9))])
    return VGroup(hull, deck, funnel, mast, flag, wave).scale(s)


_GLYPHS = {"cat": cat_glyph, "dog": dog_glyph, "plane": plane_glyph,
           "car": car_glyph, "ship": ship_glyph}


def concept_glyph(name, s=1.0, color=None):
    return _GLYPHS[name](color or CONCEPT_COLORS[name], s=s)


def photo_card(name, size=1.4, frame_c=IMG_C, glyph_s=None):
    """A framed 'photo': the concept glyph inside a teal-framed square card."""
    card = RoundedRectangle(width=size, height=size, corner_radius=0.12,
                            stroke_color=frame_c, stroke_width=2.6,
                            fill_color=PANEL, fill_opacity=0.75)
    g = concept_glyph(name, s=glyph_s or size * 0.58).move_to(card)
    grp = VGroup(card, g)
    grp.card, grp.glyph = card, g
    return grp


def caption_chip(text, color=TXT_C, w=None, h=0.62, fs=24):
    return chip(text, color, w=w, h=h, fs=fs, fill=0.14)


def embedding_vector(color, n=6, seed=0, cw=0.26):
    """A short vertical column of value-shaded cells = one embedding vector."""
    rng = np.random.default_rng(seed)
    cells = VGroup()
    for v in rng.uniform(0.25, 1.0, n):
        sq = Square(cw, stroke_width=1.0, stroke_color=FAINT)
        sq.set_fill(color, opacity=float(v))
        cells.add(sq)
    cells.arrange(DOWN, buff=0.03)
    frame = SurroundingRectangle(cells, buff=0.06, color=color, corner_radius=0.06)
    frame.set_stroke(width=2.2)
    g = VGroup(cells, frame)
    g.cells = cells
    return g


def encoder_block(color, w=1.9, h=2.3, narrow=0.46):
    """A trapezoid that narrows to the right (wide input -> compact vector)."""
    hl, hr = h / 2, h * narrow / 2
    body = Polygon([-w / 2, hl, 0], [w / 2, hr, 0], [w / 2, -hr, 0], [-w / 2, -hl, 0],
                   stroke_color=color, stroke_width=3, fill_color=color, fill_opacity=0.12)
    layers = VGroup()
    for fx in (-0.28, 0.05, 0.38):
        x = fx * w
        yy = np.interp(x, [-w / 2, w / 2], [hl, hr])
        layers.add(Line([x, yy - 0.05, 0], [x, -yy + 0.05, 0],
                        stroke_color=color, stroke_width=1.6).set_opacity(0.55))
    g = VGroup(body, layers)
    g.body = body
    return g


# ========================================================================== #
class _ClipBase(Scene):
    def setup(self):
        self.camera.background_color = BG
        self._cap = None

    # ---- timing ----------------------------------------------------------- #
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.0))

    def settle(self):
        self.wait(END_HOLD)

    def wipe(self, rt=0.7):
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)
        self._cap = None

    # ---- chrome ----------------------------------------------------------- #
    def section_header(self, label, color=GOLD):
        t = Text(label, font_size=34, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=3)
        return VGroup(t, line)

    def say(self, text, color=INK, fs=27):
        """A single running caption pinned to the bottom; replaces the last one."""
        m = Text(text, font_size=fs, color=color)
        if m.width > 12.6:
            m.scale(12.6 / m.width)
        m.to_edge(DOWN, buff=0.5)
        if self._cap is not None:
            self.play(FadeOut(self._cap, shift=DOWN * 0.1),
                      FadeIn(m, shift=UP * 0.1), run_time=0.5)
        else:
            self.play(FadeIn(m, shift=UP * 0.1), run_time=0.5)
        self._cap = m
        return m

    # ---- house intro / outro --------------------------------------------- #
    def play_intro(self):
        title = Text("What is CLIP?", font_size=62, color=INK, weight="BOLD").move_to(UP * 0.9)
        rule = Line([title.get_left()[0] - 1, title.get_bottom()[1] - 0.35, 0],
                    [title.get_right()[0] + 1, title.get_bottom()[1] - 0.35, 0]
                    ).set_stroke(width=3, color=GOLD)
        self.play(Write(title), Create(rule), run_time=1.6)
        self.card_wait(0.6)
        sub = Text("Teaching one model to see and read", font_size=32, color=MUTED)
        sub.next_to(rule, DOWN, buff=0.5)
        self.play(FadeIn(sub, shift=UP * 0.2), run_time=0.9)
        writer = Text("Created by Ptolémé", font_size=26, color=BLUE).next_to(sub, DOWN, buff=0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        src = Text("based on Radford et al., “Learning Transferable Visual Models…”, 2021",
                   font_size=19, color=MUTED).next_to(writer, DOWN, buff=0.4)
        self.play(FadeIn(src), run_time=0.7)
        self.card_wait(2.0)
        self.play(FadeOut(VGroup(title, rule, sub, writer, src)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.4)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD").move_to(UP * 0.7)
        rule = Line([header.get_left()[0] - 1, header.get_bottom()[1] - 0.4, 0],
                    [header.get_right()[0] + 1, header.get_bottom()[1] - 0.4, 0]
                    ).set_stroke(width=3, color=GOLD)
        recap = Text("Line up images and text in one space,\n"
                     "and plain language becomes an open-ended classifier.",
                     font_size=26, color=MUTED, line_spacing=0.9)
        recap.next_to(rule, DOWN, buff=0.55)
        writer = Text("Created by Ptolémé", font_size=26, color=BLUE).next_to(recap, DOWN, buff=0.6)
        self.play(Write(header), Create(rule), run_time=1.6)
        self.play(FadeIn(recap, shift=UP * 0.2), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.card_wait(2.4)
        self.play(FadeOut(VGroup(header, rule, recap, writer)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 — the problem: fixed labels vs. language supervision
    # ====================================================================== #
    def scene_problem(self):
        head = self.section_header("The old way: a fixed list of labels")
        self.play(FadeIn(head, shift=RIGHT * 0.2), run_time=0.8)
        self.beat(0.5)

        # image -> classifier -> a closed list of labels
        img = photo_card("cat", size=1.5).move_to([-4.7, 0.4, 0])
        enc = chip("classifier", GOLD, w=2.3, h=0.9, fs=26, fill=0.16).move_to([-1.7, 0.4, 0])
        labels = ["cat", "dog", "car", "ship", "…1,000 classes"]
        rows = VGroup(*[chip(t, MUTED, w=2.6, h=0.52, fs=22, fill=0.06) for t in labels])
        rows.arrange(DOWN, buff=0.16).move_to([2.4, 0.4, 0])
        box = SurroundingRectangle(rows, buff=0.22, color=MUTED, corner_radius=0.1).set_stroke(width=2)
        a1 = arr(img.get_right(), enc.get_left())
        a2 = arr(enc.get_right(), box.get_left())

        self.play(FadeIn(img, shift=UP * 0.2), run_time=0.8)
        self.play(GrowArrow(a1), FadeIn(enc, scale=0.9), run_time=0.7)
        self.play(GrowArrow(a2), Create(box), LaggedStart(*[FadeIn(r) for r in rows], lag_ratio=0.25), run_time=1.4)
        self.beat(1.2)
        # it picks one
        pick = rows[0]
        self.play(pick.box.animate.set_stroke(GOOD, width=3).set_fill(GOOD, 0.18),
                  pick.label.animate.set_color(INK), run_time=0.6)
        self.play(Indicate(pick, color=GOOD, scale_factor=1.06), run_time=0.6)
        self.say("It can only ever answer with a label from that list.", color=INK)
        self.beat(1.6)

        # the limitation: something new
        newq = caption_chip("“a corgi wearing sunglasses”", color=TXT_C, fs=22, h=0.6)
        newq.move_to([2.4, -2.05, 0])
        qmark = Text("?", font_size=44, color=BAD, weight="BOLD").move_to(enc).shift(DOWN * 0.02)
        aq = arr(newq.get_left(), [enc.get_x(), newq.get_y(), 0], color=BAD)
        self.play(FadeIn(newq, shift=UP * 0.2), run_time=0.7)
        self.play(GrowArrow(aq), run_time=0.5)
        # hide the label and detach it from the chip, so a later group-fade of the
        # chip can never bring the "classifier" text back on top of the "?".
        lbl = enc[1]
        self.play(lbl.animate.set_opacity(0), enc.box.animate.set_stroke(BAD, width=3), run_time=0.4)
        enc.remove(lbl)
        self.play(FadeIn(qmark, scale=1.3), run_time=0.4)
        self.say("Anything outside the list means starting over: new labels, new training.", color=BAD)
        self.beat(1.8)

        # transition to the CLIP idea
        self.play(FadeOut(VGroup(img, enc, a1, a2, box, rows, newq, qmark, aq)),
                  FadeOut(self._cap), run_time=0.7)
        self._cap = None
        self.play(head[0].animate.become(
            Text("CLIP's idea: learn from the web", font_size=34, color=INK, weight="BOLD").to_corner(UL, buff=0.5)),
            head[1].animate.set_stroke(IMG_C), run_time=0.7)

        pairs = VGroup()
        data = [("cat", "a cat sitting on a sofa"),
                ("ship", "a red boat in the harbor"),
                ("plane", "a plane taking off at dawn")]
        for nm, cap in data:
            ph = photo_card(nm, size=1.0)
            cp = caption_chip(f"“{cap}”", fs=20, h=0.56)
            row = VGroup(ph, cp).arrange(RIGHT, buff=0.3)
            pairs.add(row)
        pairs.arrange(DOWN, buff=0.4, aligned_edge=LEFT).move_to([-1.7, 0.1, 0])
        self.play(LaggedStart(*[FadeIn(p, shift=RIGHT * 0.25) for p in pairs], lag_ratio=0.3), run_time=1.6)
        big = Text("400,000,000", font_size=46, color=GOLD, weight="BOLD").move_to([3.7, 0.7, 0])
        big_sub = Text("image + caption pairs\nscraped from the internet",
                       font_size=22, color=MUTED, line_spacing=0.85).next_to(big, DOWN, buff=0.25)
        self.play(FadeIn(big, scale=0.8), run_time=0.8)
        self.play(FadeIn(big_sub), run_time=0.6)
        self.beat(1.2)
        self.say("No hand-labeling. The caption already is the label.", color=GOOD)
        self.beat(1.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — two encoders, one shared space
    # ====================================================================== #
    def scene_encoders(self):
        head = self.section_header("Two encoders, one shared space")
        self.play(FadeIn(head, shift=RIGHT * 0.2), run_time=0.8)
        self.beat(0.4)

        y_top, y_bot = 1.35, -1.55
        # image lane
        img = photo_card("dog", size=1.25).move_to([-5.3, y_top, 0])
        ienc = encoder_block(IMG_C, w=1.8, h=2.0).move_to([-2.9, y_top, 0])
        ienc_lab = Text("image encoder", font_size=20, color=IMG_C).next_to(ienc, UP, buff=0.16)
        ienc_sub = Text("ViT / ResNet", font_size=15, color=MUTED).next_to(ienc, DOWN, buff=0.14)
        ivec = embedding_vector(IMG_C, n=6, seed=3).move_to([-1.05, y_top, 0])
        ia1 = arr(img.get_right(), ienc.get_left(), color=IMG_C)
        ia2 = arr(ienc.get_right(), ivec.get_left(), color=IMG_C)

        # text lane
        cap = caption_chip("“a photo of a dog”", fs=22, h=0.66).move_to([-5.3, y_bot, 0])
        tenc = encoder_block(TXT_C, w=1.8, h=2.0).move_to([-2.9, y_bot, 0])
        tenc_lab = Text("text encoder", font_size=20, color=TXT_C).next_to(tenc, UP, buff=0.16)
        tenc_sub = Text("Transformer", font_size=15, color=MUTED).next_to(tenc, DOWN, buff=0.14)
        tvec = embedding_vector(TXT_C, n=6, seed=8).move_to([-1.05, y_bot, 0])
        ta1 = arr(cap.get_right(), tenc.get_left(), color=TXT_C)
        ta2 = arr(tenc.get_right(), tvec.get_left(), color=TXT_C)

        # shared space on the right
        space = RoundedRectangle(width=4.3, height=4.4, corner_radius=0.18,
                                 stroke_color=MUTED, stroke_width=2, fill_color=PANEL, fill_opacity=0.5)
        space.move_to([3.7, -0.1, 0])
        space_lab = Text("shared embedding space", font_size=20, color=INK).next_to(space.get_top(), DOWN, buff=0.18)
        grid = VGroup()
        for gx in np.linspace(space.get_left()[0] + 0.4, space.get_right()[0] - 0.4, 5):
            grid.add(Line([gx, space.get_bottom()[1] + 0.3, 0], [gx, space.get_top()[1] - 0.7, 0],
                          stroke_color=FAINT, stroke_width=1).set_opacity(0.5))
        for gy in np.linspace(space.get_bottom()[1] + 0.4, space.get_top()[1] - 0.8, 4):
            grid.add(Line([space.get_left()[0] + 0.3, gy, 0], [space.get_right()[0] - 0.3, gy, 0],
                          stroke_color=FAINT, stroke_width=1).set_opacity(0.5))

        # reveal image lane
        self.play(FadeIn(img, shift=UP * 0.2), run_time=0.6)
        self.play(GrowArrow(ia1), FadeIn(ienc), FadeIn(ienc_lab), FadeIn(ienc_sub), run_time=0.7)
        beam_i = Line(ienc.get_left(), ienc.get_right()).set_stroke(GOLD, 6)
        self.play(ShowPassingFlash(beam_i, time_width=0.5), run_time=0.9)
        self.play(GrowArrow(ia2), FadeIn(ivec, shift=RIGHT * 0.2), run_time=0.7)
        self.beat(0.7)
        # reveal text lane
        self.play(FadeIn(cap, shift=UP * 0.2), run_time=0.6)
        self.play(GrowArrow(ta1), FadeIn(tenc), FadeIn(tenc_lab), FadeIn(tenc_sub), run_time=0.7)
        beam_t = Line(tenc.get_left(), tenc.get_right()).set_stroke(GOLD, 6)
        self.play(ShowPassingFlash(beam_t, time_width=0.5), run_time=0.9)
        self.play(GrowArrow(ta2), FadeIn(tvec, shift=RIGHT * 0.2), run_time=0.7)
        self.say("Each encoder turns its input into a vector of the same length.")
        self.beat(1.4)

        # bring in the shared space and drop both vectors into it as points
        self.play(FadeIn(space), FadeIn(space_lab), Create(grid), run_time=1.0)
        idot = VGroup(Dot(radius=0.11, color=IMG_C),
                      concept_glyph("dog", s=0.26).set_color(IMG_C))
        idot[1].move_to(idot[0])
        tdot = Dot(radius=0.11, color=TXT_C)
        idot.move_to([2.9, 0.55, 0])
        tdot.move_to([4.3, -0.7, 0])
        ilab = Text("image vector", font_size=16, color=IMG_C).next_to(idot, UP, buff=0.12)
        tlab = Text("text vector", font_size=16, color=TXT_C).next_to(tdot, DOWN, buff=0.12)
        self.play(TransformFromCopy(ivec, idot), FadeIn(ilab), run_time=0.9)
        self.play(TransformFromCopy(tvec, tdot), FadeIn(tlab), run_time=0.9)
        self.beat(1.0)
        self.say("A matching image and caption should land in the same spot.", color=GOOD)
        link = DashedLine(idot.get_center(), tdot.get_center(), color=GOOD, stroke_width=3)
        target = [3.5, -0.05, 0]
        self.play(Create(link), run_time=0.6)
        self.play(idot.animate.move_to(target + np.array([-0.28, 0.12, 0])),
                  tdot.animate.move_to(target + np.array([0.28, -0.12, 0])),
                  ilab.animate.next_to(target + np.array([-0.28, 0.12, 0]), UP, buff=0.12),
                  tlab.animate.next_to(target + np.array([0.28, -0.12, 0]), DOWN, buff=0.12),
                  link.animate.put_start_and_end_on(target + np.array([-0.28, 0.12, 0]),
                                                    target + np.array([0.28, -0.12, 0])),
                  run_time=1.3)
        self.play(Flash(np.array(target), color=GOOD, line_length=0.25, num_lines=14, flash_radius=0.5), run_time=0.7)
        self.beat(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — contrastive pre-training (the N x N matrix)
    # ====================================================================== #
    def scene_contrast(self):
        head = self.section_header("Contrastive pre-training")
        self.play(FadeIn(head, shift=RIGHT * 0.2), run_time=0.8)

        concepts = ["cat", "dog", "plane", "car", "ship"]
        n = len(concepts)
        cs = 0.72
        gx0, gy0 = 0.55, -0.45  # grid centre
        colx = [gx0 + (j - (n - 1) / 2) * cs for j in range(n)]
        rowy = [gy0 + ((n - 1) / 2 - i) * cs for i in range(n)]

        # row thumbnails (image embeddings, teal frame)
        thumbs = VGroup()
        for i, nm in enumerate(concepts):
            t = photo_card(nm, size=0.62, glyph_s=0.34).move_to([colx[0] - cs / 2 - 0.55, rowy[i], 0])
            thumbs.add(t)
        # column headers (text embeddings, violet word)
        heads = VGroup()
        for j, nm in enumerate(concepts):
            c = Text(nm, font_size=22, color=TXT_C)
            if c.width > cs - 0.06:
                c.scale((cs - 0.06) / c.width)
            c.move_to([colx[j], rowy[0] + cs / 2 + 0.34, 0])
            heads.add(c)
        img_tag = Text("images", font_size=18, color=IMG_C, weight="BOLD")
        img_tag.rotate(PI / 2).next_to(thumbs, LEFT, buff=0.28)
        txt_tag = Text("captions", font_size=18, color=TXT_C, weight="BOLD").next_to(heads, UP, buff=0.22)

        # the cells
        before = RNG.uniform(0.20, 0.62, (n, n))
        cells = {}
        for i in range(n):
            for j in range(n):
                sq = Square(cs, stroke_width=1.2, stroke_color=FAINT)
                sq.set_fill(INK, opacity=float(before[i, j]) * 0.55)
                sq.move_to([colx[j], rowy[i], 0])
                cells[(i, j)] = sq
        grid = VGroup(*cells.values())

        self.play(LaggedStart(*[FadeIn(t, shift=RIGHT * 0.2) for t in thumbs], lag_ratio=0.15),
                  FadeIn(img_tag), run_time=1.1)
        self.play(LaggedStart(*[FadeIn(h, shift=DOWN * 0.2) for h in heads], lag_ratio=0.15),
                  FadeIn(txt_tag), run_time=1.1)
        self.play(LaggedStart(*[FadeIn(c) for c in grid], lag_ratio=0.02), run_time=1.4)
        self.say("Score every image against every caption: cosine similarity.")
        self.beat(1.2)

        # highlight one cell = one comparison
        hi = cells[(1, 3)]
        halo = SurroundingRectangle(hi, color=GOLD, buff=0.0).set_stroke(width=3)
        rp = arr(thumbs[1].get_right(), hi.get_left(), color=GOLD, sw=3, buff=0.08)
        cp = arr(heads[3].get_bottom(), hi.get_top(), color=GOLD, sw=3, buff=0.08)
        self.play(Create(halo), GrowArrow(rp), GrowArrow(cp), run_time=0.8)
        self.beat(1.2)
        self.play(FadeOut(halo), FadeOut(rp), FadeOut(cp), run_time=0.5)

        # diagonal = the true pairs; off-diagonal = the impostors
        diag_box = VGroup(*[SurroundingRectangle(cells[(k, k)], color=GOOD, buff=0.0).set_stroke(width=3)
                            for k in range(n)])
        self.say("The N matching pairs sit on the diagonal.", color=GOOD)
        self.play(LaggedStart(*[Create(b) for b in diag_box], lag_ratio=0.15), run_time=1.2)
        self.beat(1.2)

        # train: pull the diagonal up (green), push the rest down (dim)
        after_anims = []
        for i in range(n):
            for j in range(n):
                if i == j:
                    after_anims.append(cells[(i, j)].animate.set_fill(GOOD, 0.92).set_stroke(GOOD, width=1.4))
                else:
                    after_anims.append(cells[(i, j)].animate.set_fill(INK, 0.05))
        self.say("Training pulls matching pairs up and pushes the rest down.")
        self.play(LaggedStart(*after_anims, lag_ratio=0.02), run_time=1.8)
        # a couple of representative similarity readouts
        v_hi = Text("0.94", font_size=20, color=BG, weight="BOLD").move_to(cells[(2, 2)])
        v_lo = Text("0.03", font_size=18, color=MUTED).move_to(cells[(2, 4)])
        self.play(FadeIn(v_hi), FadeIn(v_lo), run_time=0.6)
        self.beat(1.6)

        if self._cap:
            self.play(FadeOut(self._cap), run_time=0.3)
        self._cap = None
        rowp = VGroup(Dot(color=GOOD, radius=0.09),
                      Text("pull matching pairs together", font_size=22, color=GOOD)).arrange(RIGHT, buff=0.2)
        rowq = VGroup(Dot(color=BAD, radius=0.09),
                      Text("push mismatched pairs apart", font_size=22, color=BAD)).arrange(RIGHT, buff=0.2)
        legend = VGroup(rowp, rowq).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        legend.next_to(grid, RIGHT, buff=0.55)
        avail = (config.frame_x_radius - 0.35) - legend.get_left()[0]
        if legend.width > avail:
            legend.scale(avail / legend.width, about_point=legend.get_left())
        self.play(FadeIn(legend, shift=RIGHT * 0.15), run_time=0.8)
        self.beat(1.0)
        punch = Text("That is the whole training signal.", font_size=28, color=INK, weight="BOLD")
        punch.move_to([0, -3.1, 0])
        if punch.width > 12.6:
            punch.scale(12.6 / punch.width)
        self.play(Write(punch), run_time=1.0)
        self.beat(1.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — zero-shot classification (the payoff)
    # ====================================================================== #
    def scene_zeroshot(self):
        head = self.section_header("Zero-shot classification")
        self.play(FadeIn(head, shift=RIGHT * 0.2), run_time=0.8)
        self.beat(0.4)

        sims = [("cat", 0.18, CONCEPT_COLORS["cat"]),
                ("dog", 0.71, CONCEPT_COLORS["dog"]),
                ("plane", 0.11, CONCEPT_COLORS["plane"])]

        # the query photo, shown once on the left
        img = photo_card("dog", size=1.5).move_to([-5.75, 0.15, 0])
        phototag = Text("the photo", font_size=20, color=IMG_C).next_to(img, DOWN, buff=0.22)
        self.play(FadeIn(img, shift=UP * 0.2), FadeIn(phototag), run_time=0.8)
        self.say("Give CLIP a new photo, and any labels you choose.")
        self.beat(1.0)

        # each label, written as a sentence (one prompt per row)
        prompts = VGroup(*[caption_chip(f"“a photo of a {nm}”", fs=20, h=0.6, w=3.15)
                           for nm, _, _ in sims])
        prompts.arrange(DOWN, buff=0.5).move_to([-1.7, 0.15, 0])
        self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.15) for p in prompts], lag_ratio=0.2), run_time=1.1)
        self.say("Write each candidate label as a short sentence.")
        self.beat(1.2)

        # ONE arrow: the photo is compared against each sentence
        brace = Brace(prompts, LEFT, color=IMG_C, buff=0.18)
        cmp_arrow = arr(img.get_right(), brace.get_tip() + LEFT * 0.05, color=IMG_C, sw=4)
        self.play(GrowArrow(cmp_arrow), FadeIn(brace), run_time=0.8)

        # bars, one per prompt row, on the same row (no duplicated label text)
        eq_x, bar_x0, unit = 0.35, 0.85, 3.0
        bar_rows = VGroup()
        grow = []
        for i, (nm, val, col) in enumerate(sims):
            y = prompts[i].get_y()
            eq = Text("=", font_size=30, color=MUTED).move_to([eq_x, y, 0])
            track = Rectangle(width=unit, height=0.36, stroke_width=0, fill_color=FAINT,
                              fill_opacity=0.4).move_to([bar_x0 + unit / 2, y, 0])
            bar = Rectangle(width=0.001, height=0.36, stroke_width=0, fill_color=col,
                            fill_opacity=0.95).move_to(track).align_to(track, LEFT)
            val_t = Text(f"{val:.2f}", font_size=22, color=INK).next_to(track, RIGHT, buff=0.2)
            bar_rows.add(VGroup(eq, track, bar, val_t))
            grow.append(bar.animate.stretch_to_fit_width(unit * val).align_to(track, LEFT))
        cmp = Text("cosine similarity", font_size=20, color=INK).move_to([bar_x0 + unit / 2, 1.95, 0])
        self.play(FadeIn(cmp), FadeIn(bar_rows), run_time=0.8)
        self.say("Compare the photo with each sentence: how close are their vectors?")
        self.play(LaggedStart(*grow, lag_ratio=0.2), run_time=1.5)
        self.beat(1.4)

        # winner: the closest sentence
        win_i = int(np.argmax([v for _, v, _ in sims]))
        win_row = VGroup(prompts[win_i], bar_rows[win_i])
        halo = SurroundingRectangle(win_row, color=GOOD, buff=0.16, corner_radius=0.1).set_stroke(width=3)
        tick = make_tick(GOOD, sw=9, scale=1.3).next_to(bar_rows[win_i], RIGHT, buff=0.55)
        self.play(Create(halo), run_time=0.6)
        self.play(FadeIn(tick, scale=0.6), Indicate(win_row, color=GOOD, scale_factor=1.03), run_time=0.7)
        self.say("The closest sentence wins, and CLIP never trained on these labels.", color=GOOD)
        self.beat(1.8)

        # swap the labels => a new classifier, no retraining. Clear the
        # comparison first so the takeaway has the whole frame to itself.
        self.play(FadeOut(self._cap),
                  *[FadeOut(m) for m in (img, phototag, prompts, brace, cmp_arrow, cmp, bar_rows, halo, tick)],
                  run_time=0.7)
        self._cap = None
        swap = Text("Swap the candidate labels, and you have a brand-new classifier.",
                    font_size=28, color=INK, weight="BOLD").move_to(UP * 1.1)
        if swap.width > 12.6:
            swap.scale(12.6 / swap.width)
        sub = Text("No retraining. No new data.", font_size=25, color=GOOD).next_to(swap, DOWN, buff=0.4)
        new_labels = VGroup(*[chip(t, GOLD, h=0.62, fs=22, fill=0.12)
                              for t in ["a husky", "a golden retriever", "a wolf", "a cartoon dog"]])
        new_labels.arrange(RIGHT, buff=0.35).next_to(sub, DOWN, buff=0.8)
        if new_labels.width > 12.6:
            new_labels.scale(12.6 / new_labels.width)
        self.play(Write(swap), run_time=1.2)
        self.play(FadeIn(sub, shift=UP * 0.15), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(l, shift=UP * 0.2) for l in new_labels], lag_ratio=0.2), run_time=1.1)
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_problem()
        self.scene_encoders()
        self.scene_contrast()
        self.scene_zeroshot()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_ClipBase):
    def construct(self):
        self.play_intro()


class Problem(_ClipBase):
    def construct(self):
        self.scene_problem()


class Encoders(_ClipBase):
    def construct(self):
        self.scene_encoders()


class Contrast(_ClipBase):
    def construct(self):
        self.scene_contrast()


class ZeroShot(_ClipBase):
    def construct(self):
        self.scene_zeroshot()


class Outro(_ClipBase):
    def construct(self):
        self.play_outro()


class WhatIsCLIP(_ClipBase):
    """The whole short film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    WhatIsCLIP().render()

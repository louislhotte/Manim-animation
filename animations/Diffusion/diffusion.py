"""Diffusion Models, Visually — a short, house-style explainer (no voice-over).

Answers the question people actually have when they first see an image model:
why on earth does it start from a screen of random static and then "denoise" its
way to a picture?

    1. Hook     -- pure static resolves into a real, detailed image. That image
                   never existed anywhere; it was denoised out of noise.
    2. Forward  -- you cannot paint a good image in one shot (almost every pixel
                   combination is garbage). But DESTROYING an image is trivial:
                   add noise, and more, until any picture becomes the same static.
                   So static is a starting point we can always reach.
    3. Reverse  -- so run the arrow backwards. Train a network to look at a noisy
                   image and answer one question: which part of this is noise?
                   Subtract a sliver of it. You are slightly closer to a picture.
    4. Steps    -- repeat that a few dozen times and static becomes an image. Why
                   not one big jump? Because that is the impossible problem again;
                   a single leap gives a blurry average. Many small nudges do not.
    5. Prompt   -- the noise fixes the layout; a text prompt fixes the content.
                   Same seed, different words, different picture.
    6. ComfyUI  -- how it is wired in practice: load the denoiser, encode the
                   prompt, run the sampler loop (steps / cfg / seed), decode the
                   latent to pixels, save the image.

The hero image is a real ComfyUI generation (the one in the screenshot). Every
noise<->image morph is a baked trajectory (see generate_assets.py) so it is
smooth and reproducible.

Everything uses ``Text`` (Pango), never ``Tex`` -- no LaTeX toolchain needed.

Scenes render alone (``Intro``, ``Hook``, ``Forward``, ``Reverse``, ``Steps``,
``Prompt``, ``Comfy``, ``Outro``) or as one film (``DiffusionModels``).

Env knobs:
    DIFF_QUICK=1        shorten every hold for a fast sanity render
    DIFF_DELAY=<float>  override the between-step rhythm (motion pacing)
    DIFF_READ=<float>   override the per-subtitle reading hold (~3 s by default)
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from manim import *

# --- crisp text ------------------------------------------------------------ #
# Manim's ``Text`` mangles letter/word spacing below ~20 pt. Fix it once: render
# every glyph at a large base size and scale the mobject *down*. Shadowing
# ``Text`` this way is mandatory so every subscript/superscript stays in-font.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("DIFF_QUICK") == "1"
DELAY = float(os.environ.get("DIFF_DELAY", 0.28 if QUICK else 1.15))
READ = float(os.environ.get("DIFF_READ", 0.35 if QUICK else 2.9))
ANIM_SLOW = 1.0 if QUICK else 1.25
END_HOLD = 0.2 if QUICK else 2.2

# ---- palette (shared house style) ---------------------------------------- #
BG = "#0E1117"
PANEL = "#161B26"
INK = "#F5F3EF"
MUTED = "#8A93A6"
FAINT = "#3A4152"
GOLD = "#FFD166"
NOISE_C = "#7C8AA6"     # "static" grey-blue
SIGNAL_C = "#3DD68C"    # clean signal / image (green)
MODEL_C = "#FFB703"     # the denoiser / network (amber)
PROMPT_C = "#C792EA"    # text prompt (violet)
CYAN = "#4CC9F0"        # accents / latent
RED = "#FF5C5C"

FRAME_R = config.frame_x_radius   # 7.111…
FONT = "Helvetica Neue"
_BaseText.set_default(font=FONT)

# ---- baked trajectories --------------------------------------------------- #
ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
SCREENS = ROOT / "src_screens"
_NPZ = ASSETS / "diffusion.npz"
if not _NPZ.exists():
    raise SystemExit("Missing assets/diffusion.npz — run: python generate_assets.py")
_A = np.load(_NPZ)
FOX = _A["fox"]           # [N,H,W,4] uint8 : static (0) -> fox image (N-1)
LAND = _A["land"]         # [N,H,W,4] uint8 : same static -> sunset
X0_FOX = _A["x0_fox"]     # clean fox
X0_LAND = _A["x0_land"]   # clean sunset
NOISE_IMG = _A["noise"]   # the shared gaussian static
FOX_BLUR = _A["fox_blur"] # the "one big leap" mush
GALLERY = ASSETS / "gallery"   # example-output PNGs (what diffusion can make)


# ========================================================================== #
# Small reusable helpers
# ========================================================================== #
def txt(s, fs=26, color=INK, **kw):
    """Text wrapper that drops a None font/slant (a None font chokes Pango)."""
    for k in ("font", "slant", "weight"):
        if k in kw and kw[k] is None:
            kw.pop(k)
    return Text(s, font_size=fs, color=color, **kw)


class NoiseField:
    """An ImageMobject that morphs along a baked trajectory via a ValueTracker.

    ``p`` in [0, 1] maps to frame index: 0 -> first frame (pure static),
    1 -> last frame (clean image). Animate ``p`` up to denoise, down to add
    noise. Wrap in ``Group`` (never ``VGroup`` — an ImageMobject is not vector).
    """

    def __init__(self, frames, height=3.2, p0=0.0, border=True, border_color=None):
        self.frames = frames
        self.N = len(frames)
        self.p = ValueTracker(float(p0))
        self.img = ImageMobject(frames[self._i(p0)])
        self.img.height = height
        self.grp = Group(self.img)
        self.border = None
        if border:
            self.border = Rectangle(width=self.img.width, height=self.img.height,
                                    stroke_color=border_color or FAINT, stroke_width=3)
            self.border.move_to(self.img)
            self.grp.add(self.border)

    def _i(self, p):
        return max(0, min(self.N - 1, int(round(float(p) * (self.N - 1)))))

    def move_to(self, pt):
        self.grp.move_to(pt)
        return self

    def scale(self, f):
        self.grp.scale(f)
        return self

    def live(self):
        # reference self.frames/self.p dynamically so a later frames-swap
        # (same-seed, different prompt) is honoured by the running updater.
        def upd(m):
            m.pixel_array = self.frames[self._i(self.p.get_value())]
        self.img.add_updater(upd)
        return self

    def freeze(self):
        self.img.clear_updaters()
        return self

    def set_p(self, v):
        self.p.set_value(v)
        self.img.pixel_array = self.frames[self._i(v)]
        return self


def still(frames_or_img, height=3.2, p=None, border=True, border_color=None):
    """A single (non-animated) framed image from a trajectory frame or array."""
    arr = frames_or_img if p is None else frames_or_img[
        max(0, min(len(frames_or_img) - 1, int(round(p * (len(frames_or_img) - 1)))))]
    img = ImageMobject(arr)
    img.height = height
    g = Group(img)
    if border:
        b = Rectangle(width=img.width, height=img.height,
                      stroke_color=border_color or FAINT, stroke_width=3).move_to(img)
        g.add(b)
    return g


def noise_tile(res=30, seed=0, h=0.95):
    """A small square of grey gaussian static (for the 'space of images' beat)."""
    rs = np.random.default_rng(seed)
    v = np.clip(0.5 + 0.32 * rs.standard_normal((res, res)), 0, 1)
    arr = np.empty((res, res, 4), np.uint8)
    arr[..., :3] = (v[..., None] * 255).astype(np.uint8)
    arr[..., 3] = 255
    im = ImageMobject(arr)
    im.height = h
    return im


def unet_icon(s=1.0, color=MODEL_C):
    """A little hourglass: compress then expand — the U-Net silhouette."""
    top = Polygon([-0.5 * s, 0.5 * s, 0], [0.5 * s, 0.5 * s, 0], [0, 0, 0],
                  stroke_color=color, stroke_width=2.4, fill_color=color, fill_opacity=0.18)
    bot = Polygon([-0.5 * s, -0.5 * s, 0], [0.5 * s, -0.5 * s, 0], [0, 0, 0],
                  stroke_color=color, stroke_width=2.4, fill_color=color, fill_opacity=0.18)
    return VGroup(top, bot)


def model_box(w=2.6, h=1.7, label="denoiser", sub="predicts the noise", color=MODEL_C):
    box = RoundedRectangle(width=w, height=h, corner_radius=0.14, stroke_color=color,
                           stroke_width=2.6, fill_color=PANEL, fill_opacity=1)
    ic = unet_icon(0.42, color).move_to(box.get_top() + DOWN * 0.46)
    lab = Text(label, font_size=23, color=INK, weight="BOLD")
    sb = Text(sub, font_size=16, color=MUTED)
    tx = VGroup(lab, sb).arrange(DOWN, buff=0.08).move_to(box.get_center() + DOWN * 0.3)
    return VGroup(box, ic, tx)


def arrow(a, b, color=INK, sw=4, buff=0.12):
    return Arrow(a, b, color=color, stroke_width=sw, buff=buff,
                 max_tip_length_to_length_ratio=0.28, tip_length=0.22)


def repeat_glyph(r=0.32, color=GOLD):
    """A compact circular 'repeat' arrow (Arc + hand-built arrowhead). Used to
    show the loop WITHOUT a scene-spanning arc that would cross other content."""
    start_a, sweep = -35 * DEGREES, 300 * DEGREES
    arc = Arc(radius=r, start_angle=start_a, angle=sweep,
              stroke_color=color, stroke_width=4)
    end_a = start_a + sweep
    tip = Polygon([0, 0.12, 0], [-0.1, -0.07, 0], [0.1, -0.07, 0],
                  color=color, fill_color=color, fill_opacity=1, stroke_width=0)
    tip.rotate(end_a)                       # point the head along the CCW tangent
    tip.move_to(arc.get_end())
    return VGroup(arc, tip)


# ========================================================================== #
class _DiffBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # ---- timing ----------------------------------------------------------- #
    def play(self, *anims, **kwargs):
        if not (len(anims) == 1 and isinstance(anims[0], Wait)):
            rt = kwargs.get("run_time")
            if rt is not None:
                kwargs["run_time"] = rt * ANIM_SLOW
        return super().play(*anims, **kwargs)

    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def read(self, k=1.0):
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

    # ---- text helpers ----------------------------------------------------- #
    def section_header(self, label, color=GOLD):
        t = Text(label, font_size=32, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=4)
        return VGroup(t, line)

    def say(self, text, color=MUTED, fs=26, y=-3.5, **kw):
        m = Text(text, font_size=fs, color=color, **kw)
        if m.width > 12.6:
            m.scale_to_fit_width(12.6)
        m.move_to([0, y, 0])
        return m

    def pill(self, text, color, fs=22, fill_op=0.16):
        t = Text(text, font_size=fs, color=color, weight="BOLD")
        box = RoundedRectangle(width=t.width + 0.42, height=t.height + 0.28,
                               corner_radius=0.13, stroke_color=color, stroke_width=2,
                               fill_color=color, fill_opacity=fill_op)
        box.move_to(t)
        return VGroup(box, t)

    def progress_bar(self, p_tracker, width=4.8, y=-2.55, color=GOLD,
                     left="pure noise", right="clean image"):
        """A left->right fill bound to a NoiseField.p tracker, plus end labels."""
        track = RoundedRectangle(width=width, height=0.24, corner_radius=0.12,
                                 stroke_color=FAINT, stroke_width=2,
                                 fill_opacity=0).move_to([0, y, 0])
        fill = Rectangle(width=0.02, height=0.24, stroke_width=0,
                         fill_color=color, fill_opacity=0.92)

        def upd(m):
            s = min(max(p_tracker.get_value(), 0.0), 1.0)
            m.stretch_to_fit_width(max(0.02, width * s))
            m.align_to(track.get_left(), LEFT)
            m.set_y(track.get_y())
        fill.add_updater(upd)
        ll = Text(left, font_size=17, color=MUTED).next_to(track, LEFT, buff=0.22)
        rl = Text(right, font_size=17, color=MUTED).next_to(track, RIGHT, buff=0.22)
        return VGroup(track, ll, rl), fill

    # ---- house-style intro / outro cards ---------------------------------- #
    def play_intro(self):
        header = Text("Diffusion Models", font_size=60, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        writer = Text("Created by Ptolémé", font_size=28, color=CYAN)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        # a small tile of static resolves toward a picture as the title lands
        chip = NoiseField(FOX, height=1.5, p0=0.0, border=True)
        chip.move_to([0, 2.35, 0]).live()

        self.play(FadeIn(chip.grp, scale=0.9), run_time=0.7)
        self.play(chip.p.animate.set_value(1.0), run_time=1.6, rate_func=smooth)
        self.play(Write(header), Create(line), run_time=1.5)
        chip.freeze()
        self.read(0.5)
        sub = Text("How AI paints from pure noise  ·  Generative models",
                   font_size=30, color=MUTED)
        sub.move_to(header)
        self.play(FadeOut(chip.grp, shift=UP * 0.2), Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.read(1.2)
        self.play(FadeOut(VGroup(header, writer, line)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.4)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        writer = Text("Created by Ptolémé", font_size=28, color=CYAN)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = Text("Start from noise. Predict it. Subtract a little. Repeat.",
                     font_size=26, color=GOLD)
        recap.next_to(writer, DOWN, buff=0.5)
        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.6)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap), run_time=0.8)
        self.read(1.6)
        self.play(FadeOut(VGroup(header, line, writer, recap)), run_time=1.3)
        self.card_wait(0.4)

    # ====================================================================== #
    # Scene 1 — HOOK: static resolves into a real image
    # ====================================================================== #
    def scene_hook(self):
        field = NoiseField(FOX, height=3.9, p0=0.0).move_to([0, 0.35, 0]).live()
        cap = self.say("This is pure random noise.", color=NOISE_C, fs=30)
        self.play(FadeIn(field.grp), run_time=0.6)
        self.play(FadeIn(cap), run_time=0.4)
        self.beat(1.6)

        cap2 = self.say("Watch.", color=INK, fs=30)
        self.play(Transform(cap, cap2), run_time=0.5)
        self.beat(0.6)
        self.play(field.p.animate.set_value(1.0), run_time=4.2, rate_func=smooth)
        field.freeze()
        self.beat(1.0)

        cap3 = self.say("This image never existed. It was denoised out of that noise.",
                        color=INK, fs=28)
        self.play(Transform(cap, cap3), run_time=0.6)
        self.read(1.4)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — GALLERY: what diffusion can make (breadth)
    # ====================================================================== #
    def scene_gallery(self):
        header = self.section_header("One idea, all of this", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        specs = [("anime", "Anime"), ("photo", "Photos"), ("art", "Digital art"),
                 ("render3d", "3D renders"), ("concept", "Concept art"), ("video", "Video")]
        H = 1.75
        cols = [-3.95, 0.0, 3.95]
        rows = [1.35, -1.5]

        def tile(name, h):
            img = ImageMobject(str(GALLERY / f"{name}.png"))
            img.height = h
            b = Rectangle(width=img.width, height=img.height,
                          stroke_color=FAINT, stroke_width=3).move_to(img)
            return Group(img, b)

        tiles, labels = [], []
        for i, (name, lab) in enumerate(specs):
            t = tile(name, H).move_to([cols[i % 3], rows[i // 3], 0])
            L = Text(lab, font_size=18, color=MUTED)
            if L.width > H + 0.15:
                L.scale_to_fit_width(H + 0.15)
            L.next_to(t, DOWN, buff=0.14)
            tiles.append(t)
            labels.append(L)

        self.play(LaggedStart(*[FadeIn(t, scale=0.85) for t in tiles],
                              lag_ratio=0.12), run_time=1.7)
        self.play(LaggedStart(*[FadeIn(l) for l in labels], lag_ratio=0.08), run_time=0.9)
        cap = self.say("Photos, art, characters, 3D, even video. All the same denoising trick.",
                       color=INK)
        self.play(FadeIn(cap), run_time=0.4)
        self.read(1.7)
        cap2 = self.say("One idea makes all of it. But why start from pure noise?",
                        color=GOLD, fs=27)
        self.play(Transform(cap, cap2), run_time=0.6)
        self.read(1.5)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — FORWARD: destroying an image is easy; static is the endpoint
    # ====================================================================== #
    def scene_forward(self):
        header = self.section_header("Why start from noise?", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # (a) you cannot just paint the pixels: almost all of them are garbage
        tiles = Group(*[noise_tile(seed=i, h=1.15) for i in range(6)])
        for i, t in enumerate(tiles):
            t.move_to([-4.5 + i * 1.8, 0.7, 0])
        q = self.say("Could a network just paint every pixel in one shot?",
                     color=INK, fs=27, y=2.15)
        self.play(FadeIn(q, shift=DOWN * 0.2), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(t, scale=0.8) for t in tiles],
                              lag_ratio=0.12), run_time=1.3)
        cap = self.say("Almost every combination of pixels is just noise.", color=NOISE_C)
        self.play(FadeIn(cap), run_time=0.4)
        self.read(1.0)
        cap2 = self.say("A real image is a vanishing needle in that haystack. Painting one "
                        "blind is hopeless.", color=NOISE_C)
        self.play(Transform(cap, cap2), run_time=0.5)
        self.read(1.4)
        self.play(FadeOut(tiles), FadeOut(q), run_time=0.6)

        # (b) but wrecking an image is trivial and completely understood
        field = NoiseField(FOX, height=3.5, p0=1.0).move_to([0, 0.35, 0]).live()
        cap3 = self.say("But wrecking one is trivial. Take a real image...", color=INK)
        self.play(FadeIn(field.grp), Transform(cap, cap3), run_time=0.7)
        self.read(0.8)

        bar_grp, fill = self.progress_bar(field.p, width=5.0, y=-2.55,
                                          left="clean image", right="pure noise")
        # bar reads 'amount of noise added': flip so full = noise. Bind to (1-p).
        noise_tr = ValueTracker(0.0)

        def nfill(m):
            s = min(max(noise_tr.get_value(), 0.0), 1.0)
            m.stretch_to_fit_width(max(0.02, 5.0 * s))
            m.align_to(bar_grp[0].get_left(), LEFT)
            m.set_y(bar_grp[0].get_y())
        fill.clear_updaters()
        fill.add_updater(nfill)
        fill.set_fill(NOISE_C)
        self.play(FadeIn(bar_grp), FadeIn(fill), run_time=0.5)

        cap4 = self.say("...add a little noise...", color=INK)
        self.play(Transform(cap, cap4),
                  field.p.animate.set_value(0.62), noise_tr.animate.set_value(0.38),
                  run_time=1.6)
        self.read(0.5)
        cap5 = self.say("...and more...", color=INK)
        self.play(Transform(cap, cap5),
                  field.p.animate.set_value(0.28), noise_tr.animate.set_value(0.72),
                  run_time=1.6)
        self.read(0.4)
        cap6 = self.say("...until nothing of the picture is left.", color=INK)
        self.play(Transform(cap, cap6),
                  field.p.animate.set_value(0.0), noise_tr.animate.set_value(1.0),
                  run_time=1.8)
        field.freeze()
        self.read(0.8)

        recap = self.say("Every image, drowned in enough noise, becomes the same thing: "
                         "static. So static is a place we can always start from.",
                         color=GOLD, fs=26)
        self.play(Transform(cap, recap), run_time=0.6)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — REVERSE: learn to undo ONE small step
    # ====================================================================== #
    def scene_reverse(self):
        header = self.section_header("Run the arrow backwards", SIGNAL_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        intro = self.say("If we can add noise, can we learn to remove it?", color=INK, fs=28)
        self.play(FadeIn(intro), run_time=0.5)
        self.read(1.1)
        self.play(FadeOut(intro), run_time=0.4)

        # Three clean lanes so no arrow ever crosses another element:
        #   top    -> the "repeat" loop glyph
        #   middle -> the pipeline  noisy image -> denoiser -> a little cleaner
        #   bottom -> the down arrow to the predicted noise
        xt = still(FOX, height=2.3, p=0.34).move_to([-4.7, 0.35, 0])
        xt_lab = Text("noisy image", font_size=20, color=NOISE_C).next_to(xt, DOWN, buff=0.2)
        model = model_box(2.5, 1.6, "denoiser", "a trained network").move_to([0, 0.35, 0])
        xprev = still(FOX, height=2.3, p=0.5).move_to([4.7, 0.35, 0])
        xprev_lab = Text("a little cleaner", font_size=20, color=SIGNAL_C).next_to(xprev, DOWN, buff=0.2)
        eps = still(NOISE_IMG, height=1.15).move_to([0, -2.15, 0])
        eps_lab = Text("predicted noise", font_size=19, color=MODEL_C).next_to(eps, DOWN, buff=0.14)

        self.play(FadeIn(xt), FadeIn(xt_lab), run_time=0.6)
        a1 = arrow(xt.get_right(), model.get_left(), color=INK)
        self.play(GrowArrow(a1), FadeIn(model), run_time=0.7)
        cap = self.say("Show it a noisy image. It answers one question: which part is noise?",
                       color=INK)
        self.play(FadeIn(cap), run_time=0.4)
        self.read(0.9)

        a2 = arrow(model.get_bottom(), eps.get_top(), color=MODEL_C)
        self.play(GrowArrow(a2), FadeIn(eps), FadeIn(eps_lab), run_time=0.7)
        self.read(1.0)

        cap2 = self.say("Subtract a sliver of that noise, and it is one small step cleaner.",
                        color=INK)
        self.play(Transform(cap, cap2), run_time=0.5)
        a3 = arrow(model.get_right(), xprev.get_left(), color=SIGNAL_C)
        minus = Text("− noise", font_size=18, color=SIGNAL_C, weight="BOLD").next_to(a3, UP, buff=0.12)
        self.play(GrowArrow(a3), FadeIn(minus),
                  FadeIn(xprev), FadeIn(xprev_lab), run_time=0.8)
        self.read(1.2)

        # the loop: a compact glyph in the top lane (no scene-spanning arc)
        rep = repeat_glyph(0.34, GOLD)
        rep_lab = Text("repeat about 30 times", font_size=20, color=GOLD, weight="BOLD")
        rep_grp = VGroup(rep, rep_lab).arrange(RIGHT, buff=0.28).move_to([0, 2.5, 0])
        cap3 = self.say("It never paints the picture. It only removes a little noise, again "
                        "and again.", color=GOLD, fs=25)
        self.play(Transform(cap, cap3), FadeIn(rep_grp, shift=DOWN * 0.15), run_time=0.9)
        self.read(1.5)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — STEPS: many small nudges (the money shot) + why not one leap
    # ====================================================================== #
    def scene_steps(self):
        header = self.section_header("Denoise, one small step at a time", SIGNAL_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        field = NoiseField(FOX, height=3.7, p0=0.0).move_to([0, 0.55, 0]).live()
        self.play(FadeIn(field.grp), run_time=0.6)
        bar_grp, fill = self.progress_bar(field.p, width=5.4, y=-2.45,
                                          left="pure noise", right="image")
        self.play(FadeIn(bar_grp), FadeIn(fill), run_time=0.5)
        cap = self.say("Start from static. Predict noise, remove a little, repeat.",
                       color=INK, y=-3.45)
        self.play(FadeIn(cap), run_time=0.4)
        self.beat(0.8)

        # the money shot: a slow, deliberate, stepped denoise
        self.play(field.p.animate.set_value(1.0), run_time=6.0, rate_func=linear)
        field.freeze()
        cap2 = self.say("A few dozen tiny steps, and noise becomes an image.",
                        color=SIGNAL_C, y=-3.45)
        self.play(Transform(cap, cap2), run_time=0.5)
        self.read(1.4)

        self.play(FadeOut(field.grp), FadeOut(bar_grp), FadeOut(fill),
                  FadeOut(cap), run_time=0.6)

        # why not one giant leap?
        q = self.say("Why not jump straight there in one step?", color=GOLD, fs=28, y=2.5)
        self.play(FadeIn(q, shift=DOWN * 0.2), run_time=0.5)

        # top: one leap -> blur ; bottom: many steps -> sharp
        noise_a = still(NOISE_IMG, height=2.2).move_to([-3.7, 0.75, 0])
        noise_b = still(NOISE_IMG, height=2.2).move_to([-3.7, -1.9, 0])
        leap = still(FOX_BLUR, height=2.2).move_to([3.7, 0.75, 0])
        sharp = still(FOX, height=2.2, p=1.0).move_to([3.7, -1.9, 0])
        a_top = arrow(noise_a.get_right(), leap.get_left(), color=RED)
        a_bot = arrow(noise_b.get_right(), sharp.get_left(), color=SIGNAL_C)
        lab_top = Text("one big leap", font_size=20, color=RED, weight="BOLD").next_to(a_top, UP, buff=0.12)
        lab_bot = Text("many small steps", font_size=20, color=SIGNAL_C, weight="BOLD").next_to(a_bot, UP, buff=0.12)
        res_top = Text("a blurry average", font_size=19, color=RED).next_to(leap, DOWN, buff=0.16)
        res_bot = Text("sharp detail", font_size=19, color=SIGNAL_C).next_to(sharp, DOWN, buff=0.16)

        self.play(FadeIn(noise_a), FadeIn(noise_b), run_time=0.5)
        self.play(GrowArrow(a_top), FadeIn(lab_top), FadeIn(leap), FadeIn(res_top), run_time=0.8)
        self.read(1.1)
        self.play(GrowArrow(a_bot), FadeIn(lab_bot), FadeIn(sharp), FadeIn(res_bot), run_time=0.8)
        self.read(1.2)

        recap = self.say("One giant leap is the impossible problem again. Many small nudges "
                         "are each easy.", color=GOLD, fs=26, y=-3.55)
        self.play(FadeIn(recap), run_time=0.5)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — PROMPT: same noise, different words, different image
    # ====================================================================== #
    def scene_prompt(self):
        header = self.section_header("Steering the noise with words", PROMPT_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # the shared starting noise in the middle
        field = NoiseField(FOX, height=3.3, p0=0.0).move_to([0, 0.15, 0]).live()
        seed_lab = Text("same starting noise (seed)", font_size=20, color=NOISE_C)
        seed_lab.next_to(field.grp, DOWN, buff=0.22)
        self.play(FadeIn(field.grp), FadeIn(seed_lab), run_time=0.6)
        self.beat(0.8)

        prompt_a = self.pill("\"anime fox girl by a campfire\"", PROMPT_C, fs=22)
        prompt_a.next_to(field.grp, UP, buff=0.35)
        self.play(FadeIn(prompt_a, shift=DOWN * 0.15), run_time=0.5)
        cap = self.say("At every step, the prompt nudges the denoiser toward the words.",
                       color=INK)
        self.play(FadeIn(cap), run_time=0.4)
        self.read(0.9)
        self.play(field.p.animate.set_value(1.0), run_time=3.0, rate_func=smooth)
        field.freeze()
        self.read(1.1)

        # rewind to the SAME noise, change the words, get a different picture
        cap2 = self.say("Rewind to the same noise. Change the words:", color=INK)
        field.live()                                   # re-attach the morph updater
        self.play(Transform(cap, cap2),
                  FadeOut(prompt_a, shift=UP * 0.15),
                  field.p.animate.set_value(0.0), run_time=1.4, rate_func=smooth)
        # swap to the sunset trajectory at p=0 (both share the SAME static, so no snap)
        field.frames = LAND
        prompt_b = self.pill("\"a mountain lake at sunset\"", CYAN, fs=22)
        prompt_b.move_to(prompt_a)
        self.play(FadeIn(prompt_b, shift=DOWN * 0.15), run_time=0.5)
        self.play(field.p.animate.set_value(1.0), run_time=3.0, rate_func=smooth)
        field.freeze()
        self.read(1.2)

        recap = self.say("The noise fixes the layout. The prompt fixes what it becomes.",
                         color=GOLD, fs=27)
        self.play(Transform(cap, recap), run_time=0.6)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 6 — COMFY: how it is wired in practice
    # ====================================================================== #
    def scene_comfy(self):
        title = Text("In practice: ComfyUI", font_size=34, color=INK, weight="BOLD")
        title.move_to([0, 3.5, 0])
        self.play(FadeIn(title, shift=DOWN * 0.2), run_time=0.6)

        shot = ImageMobject(str(SCREENS / "comfyui_full.png"))
        shot.height = 5.0                          # 1590x795 -> width ~10.0
        shot.move_to([0, 0.15, 0])
        border = Rectangle(width=shot.width, height=shot.height,
                           stroke_color=FAINT, stroke_width=2).move_to(shot)
        self.play(FadeIn(shot), Create(border), run_time=0.9)
        cap = self.say("You wire the same pieces together as a graph.", color=MUTED)
        self.play(FadeIn(cap), run_time=0.4)
        self.read(1.0)

        # pixel bboxes in the 1590x795 screenshot -> rects over the placed image
        def node_rect(bbox, color):
            x0, y0, x1, y1 = bbox
            W, H = shot.width, shot.height
            L, T = shot.get_left()[0], shot.get_top()[1]
            X = lambda px: L + (px / 1590.0) * W
            Y = lambda py: T - (py / 795.0) * H
            r = Rectangle(width=X(x1) - X(x0), height=Y(y0) - Y(y1),
                          color=color, stroke_width=3.5)
            r.move_to([(X(x0) + X(x1)) / 2, (Y(y0) + Y(y1)) / 2, 0])
            return r

        steps = [
            ((95, 150, 393, 268), MODEL_C, "Load Diffusion Model", "the denoiser we trained"),
            ((395, 293, 772, 470), PROMPT_C, "CLIP Text Encode", "turns your prompt into numbers"),
            ((815, 318, 1064, 592), GOLD, "KSampler", "runs the denoise loop"),
            ((1074, 318, 1306, 412), CYAN, "VAE Decode", "latent  ->  pixels"),
            ((1314, 318, 1544, 662), SIGNAL_C, "Save Image", "the finished picture"),
        ]

        prev_rect = None
        prev_lab = None
        for i, (bbox, color, name, sub) in enumerate(steps):
            r = node_rect(bbox, color)
            lab = VGroup(
                Text(name, font_size=20, color=color, weight="BOLD"),
                Text(sub, font_size=16, color=MUTED),
            ).arrange(DOWN, buff=0.06)
            lab.move_to([0, -3.35, 0])
            anims = [Create(r), FadeIn(lab)]
            if prev_rect is not None:
                anims += [FadeOut(prev_rect), FadeOut(prev_lab)]
            if i == 0:
                anims.append(FadeOut(cap))
            self.play(*anims, run_time=0.7)

            # when we hit the KSampler, dim the graph and pop a readable zoom of
            # its parameters (the scrim keeps the notes off the busy screenshot)
            if name == "KSampler":
                self.read(0.5)
                scrim = Rectangle(width=shot.width + 0.1, height=shot.height + 0.1,
                                  stroke_width=0, fill_color=BG, fill_opacity=0.86).move_to(shot)
                inset = ImageMobject(str(SCREENS / "ksampler.png"))
                inset.height = 3.3
                inset.move_to([4.15, 0.15, 0])
                ib = Rectangle(width=inset.width, height=inset.height,
                               stroke_color=GOLD, stroke_width=2.5).move_to(inset)
                note = VGroup(
                    Text("steps  =  how many nudges", font_size=19, color=INK),
                    Text("cfg      =  how hard to follow the prompt", font_size=19, color=INK),
                    Text("seed   =  which random noise to start from", font_size=19, color=INK),
                ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to([-3.5, 0.15, 0])
                self.play(FadeIn(scrim), run_time=0.4)
                self.play(FadeIn(Group(inset, ib), shift=LEFT * 0.2), run_time=0.7)
                self.play(FadeIn(note, shift=RIGHT * 0.2), run_time=0.6)
                self.read(1.8)
                self.play(FadeOut(scrim), FadeOut(Group(inset, ib)), FadeOut(note), run_time=0.6)
            else:
                self.read(1.1)
            prev_rect, prev_lab = r, lab

        self.play(FadeOut(prev_rect), FadeOut(prev_lab), run_time=0.5)
        note = self.say("Real systems denoise in a compressed latent space, then the VAE "
                        "decodes it to pixels.", color=CYAN, fs=24)
        self.play(FadeIn(note), run_time=0.5)
        self.read(1.6)

        # closing takeaway: ComfyUI is a general framework, not just this graph
        self.play(FadeOut(note), FadeOut(shot), FadeOut(border), FadeOut(title), run_time=0.7)
        fw_t = Text("ComfyUI is a framework", font_size=42, color=INK, weight="BOLD").move_to([0, 0.7, 0])
        rule = Line(fw_t.get_left(), fw_t.get_right()).next_to(fw_t, DOWN, buff=0.18)
        rule.set_stroke(GOLD, 3)
        fw_s = Text("Chain these blocks into almost any generative workflow you can imagine, "
                    "in a visual node editor.", font_size=25, color=MUTED)
        if fw_s.width > 12.4:
            fw_s.scale_to_fit_width(12.4)
        fw_s.next_to(rule, DOWN, buff=0.45)
        self.play(Write(fw_t), Create(rule), run_time=1.2)
        self.play(FadeIn(fw_s, shift=UP * 0.2), run_time=0.7)
        self.read(1.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Full film
    # ====================================================================== #
    def play_all(self):
        self.play_intro()
        self.scene_hook()
        self.scene_gallery()
        self.scene_forward()
        self.scene_reverse()
        self.scene_steps()
        self.scene_prompt()
        self.scene_comfy()
        self.play_outro()


# ---- thin per-scene classes + full film ---------------------------------- #
class Intro(_DiffBase):
    def construct(self):
        self.play_intro()


class Hook(_DiffBase):
    def construct(self):
        self.scene_hook()


class Examples(_DiffBase):
    def construct(self):
        self.scene_gallery()


class Forward(_DiffBase):
    def construct(self):
        self.scene_forward()


class Reverse(_DiffBase):
    def construct(self):
        self.scene_reverse()


class Steps(_DiffBase):
    def construct(self):
        self.scene_steps()


class Prompt(_DiffBase):
    def construct(self):
        self.scene_prompt()


class Comfy(_DiffBase):
    def construct(self):
        self.scene_comfy()


class Outro(_DiffBase):
    def construct(self):
        self.play_outro()


class DiffusionModels(_DiffBase):
    def construct(self):
        self.play_all()

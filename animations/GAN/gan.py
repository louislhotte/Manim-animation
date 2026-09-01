"""What is a GAN? — a dynamic, 3-D, house-style explainer with camera control.

The one idea: a GAN is two neural networks playing a game. A **generator** turns
random noise into fake samples; a **discriminator** scores how real a sample looks.
They train against each other: the generator learns to fool the discriminator, the
discriminator learns to catch the fakes. At the end the generator has learned to
produce data indistinguishable from the real thing, and the discriminator is reduced
to a coin flip.

Everything on screen is driven by a **real** toy GAN trained in NumPy
(`generate_assets.py` bakes `assets/gan.npz`): the target is the classic 8-Gaussians
ring, the fake cloud really does morph from a blob into the ring, and the
discriminator's "how real does this look" surface really does collapse from a sharp
terrain to a flat plateau.

Visual language (inspired by the Quantization field): the discriminator's confidence
is a field of glowing bars on a dark plane, orbited by a slow ambient camera. Every
word the viewer reads is a fixed-in-frame overlay so it stays put while the field
turns. All text is ``Text`` (Pango), no LaTeX.

Scenes render individually (``Goal``, ``Players``, ``Generator``, ``Discriminator``,
``Game``, ``Convergence`` …) or as one film (``WhatIsAGAN``).

Env knobs:
    GAN_QUICK=1   collapse every hold for a fast layout render
    GAN_DELAY=<s> override the reading-rhythm multiplier
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from manim import *

QUICK = os.environ.get("GAN_QUICK") == "1"
DELAY = float(os.environ.get("GAN_DELAY", 0.28 if QUICK else 2.3))
ANIM_SLOW = 1.0 if QUICK else 1.15
END_HOLD = 0.2 if QUICK else 2.2

# ---- palette (shared with the Transformer / Quantization / Tensors series) --- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text
FAINT = "#3A4152"       # hairlines, faint structure
GEN = "#43C6E8"         # the generator + its fake samples (bright cyan)
REAL = "#FFD166"        # real data (warm gold)
DISC = "#A78BFA"        # the discriminator (violet)
GOOD = "#3DD68C"        # green (verdict: real / correct)
BAD = "#FF5C5C"         # red (verdict: fake / caught)
PANEL = "#141C29"       # HUD / box fill
EDGE = "#CDEEFF"        # neon edge on the bars
MONO = "Menlo"
FONT = "Helvetica Neue"

# The discriminator "realness" ramp: deep indigo (looks fake) -> gold (looks real).
TERRAIN_RAMP = ["#26305E", "#3E6FB0", "#6FA8DC", "#F5C25B"]

# ---- crisp small text (mandatory shadow: rasterise big, scale down) ---------- #
_BaseText = Text
_BaseText.set_default(font=FONT)
_TEXT_BASE = 60


def Text(text, font_size=48, **kw):  # noqa: F811 (intentional shadow)
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


def txt(s, fs=28, color=INK, font=None, slant=None, weight=None, **extra):
    kw = dict(font_size=fs, color=color, **extra)
    if font is not None:
        kw["font"] = font
    if slant is not None:
        kw["slant"] = slant
    if weight is not None:
        kw["weight"] = weight
    return Text(s, **kw)


# =========================================================================== #
# Baked assets from the real toy GAN
# =========================================================================== #
ROOT = Path(__file__).resolve().parent
_NPZ = ROOT / "assets" / "gan.npz"
if not _NPZ.exists():
    raise SystemExit(
        "Missing assets/gan.npz — run  python generate_assets.py  first "
        "(render.sh does this automatically).")
D = np.load(_NPZ)

DEXT = float(D["extent"])            # data plane is [-DEXT, DEXT]^2  (3.3)
BAR_N = int(D["bar_n"])              # coarse grid (14) -> BAR_N^2 prisms
RING_R = float(D["ring_r"])         # 2.0
ITERS = D["iters"]                   # snapshot iteration numbers
G_SAMPLES = D["G_samples"]           # (S, 700, 2)
D_BARS = D["D_bars"]                 # (S, 14, 14)  co-training terrain
D_TEACH_BAR = D["D_teach_bar"]       # (14, 14)     sharp "catch the blob" terrain
REAL_PTS = D["real"]                 # (1400, 2)
CENTERS = D["centers"]               # (8, 2)
D_REAL = D["d_real"]                 # (S,)  mean D score on real
D_FAKE = D["d_fake"]                 # (S,)  mean D score on fake
WALK_Z = D["walk_z"]                 # (140, 2)
WALK_XY = D["walk_xy"]               # (140, 2)

# ---- data-space <-> world-space -------------------------------------------- #
WORLD_R = 3.15                       # DEXT maps to this half-width in world units
S2W = WORLD_R / DEXT                 # ~0.95


def w2(p):
    """Data coords -> world (on the z=0 plane)."""
    return np.array([p[0] * S2W, p[1] * S2W, 0.0])


# ---- colour ramp helpers --------------------------------------------------- #
def _hex_to_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


_RAMP_STOPS = np.array([_hex_to_rgb(c) for c in TERRAIN_RAMP])


def ramp_rgb(v):
    """v in [0,1] -> (3,) uint8 along the terrain ramp."""
    t = float(np.clip(v, 0, 1)) * (len(_RAMP_STOPS) - 1)
    i = min(int(t), len(_RAMP_STOPS) - 2)
    f = t - i
    return (_RAMP_STOPS[i] * (1 - f) + _RAMP_STOPS[i + 1] * f).astype(np.uint8)


def ramp_color(v):
    r, g, b = ramp_rgb(v)
    return rgb_to_color((r / 255, g / 255, b / 255))


def heatmap_image(fine):
    """A smooth ImageMobject of a D-score grid (fine[i=x, j=y] in [0,1])."""
    n = fine.shape[0]
    rgb = np.zeros((n, n, 3), np.uint8)
    for i in range(n):
        for j in range(n):
            rgb[i, j] = ramp_rgb(fine[i, j])
    # array[row, col]: row = y (descending downward), col = x
    img = np.transpose(rgb, (1, 0, 2))[::-1]
    im = ImageMobject(img)
    im.set_resampling_algorithm(RESAMPLING_ALGORITHMS["linear"])
    im.stretch_to_fit_width(2 * WORLD_R).stretch_to_fit_height(2 * WORLD_R)
    im.move_to(ORIGIN)
    return im


# =========================================================================== #
# The discriminator terrain: an N×N field of glowing bars, height = D score.
# =========================================================================== #
_STEP = 2 * WORLD_R / (BAR_N - 1)
BAR_W = _STEP * 0.58
HSCALE = 2.5                          # D = 1 -> HSCALE tall
BAR_CELLS = [(i, j) for i in range(BAR_N) for j in range(BAR_N)]


def bar_xy(i, j):
    return -WORLD_R + i * _STEP, -WORLD_R + j * _STEP


def make_bar(x, y, d, op=1.0):
    h = max(0.05, float(d) * HSCALE)
    p = Prism(dimensions=[BAR_W, BAR_W, h]).move_to([x, y, h / 2])
    p.set_fill(ramp_color(d), opacity=op)
    p.set_stroke(EDGE, width=1.0, opacity=min(1.0, op) * 0.85)
    return p


def make_ground(color=FAINT, n=BAR_N):
    ext = WORLD_R + _STEP * 0.5
    g = VGroup()
    for k in range(n + 1):
        c = -ext + k * _STEP
        g.add(Line([c, -ext, 0], [c, ext, 0]))
        g.add(Line([-ext, c, 0], [ext, c, 0]))
    return g.set_stroke(color=color, width=1.0, opacity=0.28)


# ---- point clouds ---------------------------------------------------------- #
def cloud(points, color, r=0.036, op=0.9, zlift=0.0):
    g = VGroup()
    for p in points:
        wp = w2(p)
        wp[2] = zlift
        g.add(Dot(wp, radius=r, color=color, fill_opacity=op).set_stroke(width=0))
    return g


# =========================================================================== #
# Base scene
# =========================================================================== #
class _GANBase(ThreeDScene):
    def setup(self):
        self.camera.background_color = BG
        self._orbiting = False
        self.bars = {}
        self.field_group = None
        self.ground = None

    def play(self, *anims, **kw):
        if "run_time" in kw:
            kw["run_time"] *= ANIM_SLOW
        super().play(*anims, **kw)

    # ---- timing ----------------------------------------------------------- #
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.0))

    def settle(self):
        self.wait(END_HOLD)

    # ---- camera ----------------------------------------------------------- #
    def go_3d(self, phi=64, theta=-64, zoom=0.9, rate=0.045, focal=None):
        kw = dict(phi=phi * DEGREES, theta=theta * DEGREES, zoom=zoom)
        if focal is not None:
            kw["focal_distance"] = focal
        self.set_camera_orientation(**kw)
        self.begin_ambient_camera_rotation(rate=rate)
        self._orbiting = True

    def stop_orbit(self):
        if self._orbiting:
            self.stop_ambient_camera_rotation()
            self._orbiting = False

    def go_flat_instant(self):
        self.stop_orbit()
        self.set_camera_orientation(phi=0, theta=-90 * DEGREES, zoom=1.0)

    # ---- fixed-in-frame HUD ---------------------------------------------- #
    def _fix(self, *ms):
        self.add_fixed_in_frame_mobjects(*ms)
        for m in ms:
            self.remove(m)

    def say(self, s, color=INK, fs=27, italic=False, buff=0.5):
        m = txt(s, fs=fs, color=color, slant=ITALIC if italic else None)
        if m.width > 12.4:
            m.scale_to_fit_width(12.4)
        m.to_edge(DOWN, buff=buff)
        return m

    def show_say(self, s, old=None, **kw):
        m = self.say(s, **kw)
        self._fix(m)
        anims = [FadeIn(m, shift=UP * 0.1)]
        if old is not None:
            anims.append(FadeOut(old, shift=UP * 0.1))
        self.play(*anims, run_time=0.55)
        return m

    def replace_say(self, old, s, **kw):
        return self.show_say(s, old=old, **kw)

    def section_header(self, label, color=GEN):
        t = Text(label, font_size=30, color=INK, weight="BOLD")
        line = Line(t.get_left(), t.get_right()).set_stroke(color=color, width=3)
        line.next_to(t, DOWN, buff=0.12)
        g = VGroup(t, line).to_corner(UL, buff=0.5)
        self._fix(g)
        self.play(FadeIn(g, shift=DOWN * 0.1), run_time=0.55)
        return g

    # ---- the terrain field ------------------------------------------------ #
    def build_terrain(self, dgrid, grow=True, rt=1.7, op=1.0):
        self.ground = make_ground()
        bars = {}
        for (i, j) in BAR_CELLS:
            x, y = bar_xy(i, j)
            bars[(i, j)] = make_bar(x, y, dgrid[i][j], op=op)
        self.bars = bars
        self.field_group = VGroup(*[bars[c] for c in BAR_CELLS])
        order = sorted(BAR_CELLS, key=lambda ij: -bar_xy(*ij)[1])  # back -> front
        if grow:
            self.play(FadeIn(self.ground), run_time=0.6)
            anims = [GrowFromPoint(bars[c], [*bar_xy(*c), 0]) for c in order]
            self.play(LaggedStart(*anims, lag_ratio=0.006), run_time=rt)
        else:
            self.add(self.ground, self.field_group)
        return self.field_group

    def morph_terrain(self, dgrid, rt=2.0, lag=0.010):
        order = sorted(BAR_CELLS, key=lambda ij: -bar_xy(*ij)[1])
        anims = []
        for (i, j) in order:
            x, y = bar_xy(i, j)
            anims.append(Transform(self.bars[(i, j)], make_bar(x, y, dgrid[i][j])))
        self.play(LaggedStart(*anims, lag_ratio=lag), run_time=rt)

    # ---- teardown --------------------------------------------------------- #
    def wipe(self, rt=0.7):
        self.stop_orbit()
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            super().play(*[FadeOut(m) for m in self.mobjects], run_time=rt)
        self.bars = {}
        self.field_group = None
        self.ground = None

    # ---- house intro / outro rule ---------------------------------------- #
    def _rule_under(self, header, pad=1.0, color=REAL, drop=0.45):
        return Line([header.get_left()[0] - pad, header.get_bottom()[1] - drop, 0],
                    [header.get_right()[0] + pad, header.get_bottom()[1] - drop, 0]
                    ).set_stroke(width=3, color=color)

    # ====================================================================== #
    # Intro card
    # ====================================================================== #
    def play_intro(self):
        self.go_flat_instant()
        header = Text("What is a GAN?", font_size=58, color=INK, weight="BOLD")
        header.set(width=min(8.6, header.width))
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=GEN)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        sub = Text("Two neural networks compete, and one learns to create.",
                   font_size=30, color=MUTED)
        if sub.width > line.width + 1.4:
            sub.scale_to_fit_width(line.width + 1.4)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.card_wait(1.8)
        self.play(FadeOut(VGroup(header, writer, line)), run_time=1.0)
        self.card_wait(0.3)

    # ====================================================================== #
    # Scene 1 — the goal: invent new samples that look like the real data
    # ====================================================================== #
    def scene_goal(self):
        self.go_flat_instant()
        hdr = self.section_header("The goal", color=REAL)

        real = cloud(REAL_PTS, REAL, r=0.038, op=0.9)
        rlbl = txt("real data", 26, REAL).next_to(real, UP, buff=0.35).shift(RIGHT * 0.1)
        cap = self.show_say(
            "Here is a set of real data: samples drawn from some true distribution.")
        self.play(LaggedStart(*[GrowFromCenter(d) for d in real],
                              lag_ratio=0.002), run_time=1.6)
        self.play(FadeIn(rlbl), run_time=0.5)
        self.beat(1.8)

        cap = self.replace_say(
            cap, "It clusters into eight blobs arranged in a ring.")
        ring = Circle(radius=RING_R * S2W, color=REAL, stroke_width=1.6,
                      stroke_opacity=0.5, fill_opacity=0)
        self.play(Create(ring), run_time=0.9)
        self.beat(1.6)

        cap = self.replace_say(
            cap, "We want a machine that invents brand new samples that fit right in.")
        # a few "new" gold sparks appear on the ring
        ang = np.linspace(0.3, 2 * np.pi + 0.3, 6, endpoint=False)
        news = VGroup(*[
            Star(n=5, outer_radius=0.11, color=REAL, fill_opacity=1).set_stroke(width=0)
            .move_to(w2([RING_R * np.cos(a), RING_R * np.sin(a)])) for a in ang])
        self.play(LaggedStart(*[GrowFromCenter(s) for s in news],
                              lag_ratio=0.15), run_time=1.2)
        self.beat(1.8)

        cap = self.replace_say(
            cap, "Not copies of the data, but new points from the same distribution.")
        self.beat(2.0)
        self.settle()
        self.play(FadeOut(Group(real, rlbl, ring, news, hdr, cap)), run_time=0.8)

    # ====================================================================== #
    # Scene 2 — two players: the generator and the discriminator
    # ====================================================================== #
    def scene_players(self):
        self.go_flat_instant()
        hdr = self.section_header("Two players", color=INK)

        gbox = self._role_box("Generator", "makes fake samples", GEN)
        dbox = self._role_box("Discriminator", "scores real vs fake", DISC)
        gbox.move_to([-3.25, 0.7, 0])
        dbox.move_to([3.25, 0.7, 0])

        cap = self.show_say(
            "A GAN is two neural networks with opposite jobs.")
        self.play(FadeIn(gbox, shift=RIGHT * 0.3), run_time=0.7)
        self.play(FadeIn(dbox, shift=LEFT * 0.3), run_time=0.7)
        self.beat(1.7)

        cap = self.replace_say(
            cap, "The generator turns random noise into fake samples.")
        noise = self._noise_chip().next_to(gbox, LEFT, buff=0.42)
        a1 = Arrow(noise.get_right(), gbox.get_left(), buff=0.12,
                   color=GEN, stroke_width=4, max_tip_length_to_length_ratio=0.32)
        self.play(FadeIn(noise), GrowArrow(a1), run_time=0.7)
        self.beat(1.6)

        cap = self.replace_say(
            cap, "The discriminator looks at a sample and judges: real, or fake?")
        verdict = VGroup(txt("real?", 24, GOOD), txt("fake?", 24, BAD)
                         ).arrange(DOWN, buff=0.18).next_to(dbox, RIGHT, buff=0.55)
        a2 = Arrow(dbox.get_right(), verdict.get_left(), buff=0.12,
                   color=DISC, stroke_width=4, max_tip_length_to_length_ratio=0.3)
        self.play(GrowArrow(a2), FadeIn(verdict), run_time=0.7)
        self.beat(1.8)

        cap = self.replace_say(
            cap, "They are adversaries: each one is trying to beat the other.")
        vs = txt("vs", 40, INK, weight="BOLD").move_to([0, 0.7, 0])
        clash = VGroup(
            Line(gbox.get_right(), vs.get_left(), buff=0.2).set_stroke(FAINT, 2),
            Line(dbox.get_left(), vs.get_right(), buff=0.2).set_stroke(FAINT, 2))
        self.play(Create(clash), FadeIn(vs, scale=1.4), run_time=0.8)
        self.beat(2.0)
        self.settle()
        self.play(FadeOut(Group(gbox, dbox, noise, a1, verdict, a2, vs, clash,
                                hdr, cap)), run_time=0.8)

    def _role_box(self, title, sub, color, w=3.4, h=1.7):
        box = RoundedRectangle(width=w, height=h, corner_radius=0.16,
                               stroke_color=color, stroke_width=2.6,
                               fill_color=PANEL, fill_opacity=0.92)
        t = txt(title, 30, color, weight="BOLD")
        s = txt(sub, 21, MUTED)
        VGroup(t, s).arrange(DOWN, buff=0.18).move_to(box)
        return VGroup(box, t, s)

    def _noise_chip(self):
        box = RoundedRectangle(width=1.15, height=1.15, corner_radius=0.1,
                               stroke_color=MUTED, stroke_width=1.8,
                               fill_color=BG, fill_opacity=0.9)
        rng = np.random.default_rng(1)
        dots = VGroup(*[Dot([rng.uniform(-0.42, 0.42), rng.uniform(-0.42, 0.42), 0],
                            radius=0.028, color=INK, fill_opacity=0.8)
                        for _ in range(22)]).move_to(box)
        lbl = txt("noise", 18, MUTED).next_to(box, DOWN, buff=0.12)
        return VGroup(box, dots, lbl)

    # ====================================================================== #
    # Scene 3 — the generator: noise z -> fake sample (a blob at first)
    # ====================================================================== #
    def scene_generator(self):
        self.go_flat_instant()
        hdr = self.section_header("The generator", color=GEN)

        # latent space on the left, data plane on the right
        zpanel = self._panel("latent space", GEN, [-4.3, 0.4, 0], 3.0, 3.0)
        gbox = RoundedRectangle(width=1.5, height=1.0, corner_radius=0.12,
                                stroke_color=GEN, stroke_width=2.4,
                                fill_color=PANEL, fill_opacity=0.95).move_to([-0.9, 0.4, 0])
        glab = txt("G", 34, GEN, weight="BOLD").move_to(gbox)
        gfull = txt("generator", 18, MUTED).next_to(gbox, DOWN, buff=0.12)

        cap = self.show_say(
            "The generator starts from a random noise vector, called z.")
        rng = np.random.default_rng(3)
        zpts = rng.normal(0, 0.62, (26, 2))
        zdots = VGroup(*[Dot(zpanel[0].get_center() + np.array([p[0], p[1], 0]),
                             radius=0.03, color=INK, fill_opacity=0.75) for p in zpts])
        self.play(FadeIn(zpanel), run_time=0.6)
        self.play(LaggedStart(*[GrowFromCenter(d) for d in zdots],
                              lag_ratio=0.03), run_time=1.0)
        self.play(FadeIn(VGroup(gbox, glab, gfull)), run_time=0.5)
        self.beat(1.6)

        # sample one z, push it through G, out comes a fake point on the right
        zpick = zdots[7]
        az = Arrow(zpick.get_center(), gbox.get_left(), buff=0.1, color=GEN,
                   stroke_width=3.5, max_tip_length_to_length_ratio=0.28)
        cap = self.replace_say(
            cap, "It passes z through the network and outputs one fake sample.")
        self.play(zpick.animate.set_color(GEN).scale(1.6), Create(az), run_time=0.6)
        fake0 = G_SAMPLES[0]
        one = Dot(w2(fake0[0]) + RIGHT * 3.9 + UP * 0.4, radius=0.07, color=GEN)
        aout = Arrow(gbox.get_right(), one.get_center() + LEFT * 0.25, buff=0.1,
                     color=GEN, stroke_width=3.5, max_tip_length_to_length_ratio=0.24)
        self.play(GrowArrow(aout), GrowFromCenter(one), run_time=0.7)
        self.beat(1.6)

        # many samples -> a blob, next to the (faint) real ring
        cap = self.replace_say(
            cap, "Draw many z, and you get many fakes: right now, a shapeless blob.")
        self.play(FadeOut(VGroup(zpanel, zdots, gbox, glab, gfull, az, aout)),
                  one.animate.move_to(w2(fake0[0])), run_time=0.8)
        realr = cloud(REAL_PTS, REAL, r=0.03, op=0.35)
        ring = Circle(radius=RING_R * S2W, color=REAL, stroke_width=1.4,
                      stroke_opacity=0.4, fill_opacity=0)
        idx = np.random.default_rng(5).choice(len(fake0), 180, replace=False)
        blob = cloud(fake0[idx], GEN, r=0.04, op=0.9)
        self.play(FadeIn(realr), Create(ring), run_time=0.7)
        self.play(FadeOut(one), LaggedStart(*[GrowFromCenter(d) for d in blob],
                                            lag_ratio=0.004), run_time=1.5)
        gl = txt("fake samples", 22, GEN).to_edge(LEFT, buff=0.7).shift(UP * 2.6)
        rl = txt("real data", 22, REAL).to_edge(RIGHT, buff=0.7).shift(UP * 2.6)
        self.play(FadeIn(gl), FadeIn(rl), run_time=0.5)
        self.beat(1.8)

        cap = self.replace_say(
            cap, "The fakes miss the ring completely. The generator has to learn.")
        self.beat(2.0)
        self.settle()
        self.play(FadeOut(Group(realr, ring, blob, gl, rl, hdr, cap)), run_time=0.8)

    def _panel(self, label, color, center, w, h):
        box = RoundedRectangle(width=w, height=h, corner_radius=0.14,
                               stroke_color=color, stroke_width=2.0,
                               fill_color=PANEL, fill_opacity=0.55).move_to(center)
        lbl = txt(label, 20, color).next_to(box, UP, buff=0.14)
        return VGroup(box, lbl)

    # ====================================================================== #
    # Scene 4 — the discriminator: a 3-D confidence terrain (sharp: catches fakes)
    # ====================================================================== #
    def scene_discriminator(self):
        self.go_flat_instant()
        hdr = self.section_header("The discriminator", color=DISC)

        realr = cloud(REAL_PTS, REAL, r=0.03, op=0.8)
        blob = cloud(G_SAMPLES[0], GEN, r=0.03, op=0.85)
        cap = self.show_say(
            "The discriminator scores every point: how real does this look?")
        self.play(FadeIn(realr), FadeIn(blob), run_time=0.8)
        self.beat(1.4)

        # a smooth 2-D decision heatmap (blue = looks fake, gold = looks real)
        heat = heatmap_image(D["D_teach_fine"]).set_opacity(0.0)
        self.add(heat)
        self.play(heat.animate.set_opacity(0.9), realr.animate.set_opacity(0.5),
                  blob.animate.set_opacity(0.6), run_time=1.0)
        cap = self.replace_say(
            cap, "Gold where samples look real, deep blue where they look fake.")
        self.beat(2.0)

        # lift the score into the third dimension and orbit
        cap = self.replace_say(
            cap, "Read that score as height, and it becomes a landscape.")
        self.play(FadeOut(heat), FadeOut(realr), FadeOut(blob), run_time=0.6)
        self.go_3d(phi=64, theta=-66, zoom=0.92, rate=0.05)
        self.build_terrain(D_TEACH_BAR, rt=2.0)
        self.beat(1.2)

        cap = self.replace_say(
            cap, "It carves a deep valley exactly where the generator's fakes are.")
        self.beat(2.0)
        cap = self.replace_say(
            cap, "So right now the discriminator wins: it spots the fakes easily.")
        self.beat(2.1)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — the game: the minimax loop, then the real training morph
    # ====================================================================== #
    def scene_game(self):
        self.go_flat_instant()
        hdr = self.section_header("The game", color=INK)

        # --- the adversarial loop diagram --- #
        z = self._mini_chip("z", MUTED, 0.9).move_to([-5.3, 1.5, 0])
        G = self._mini_box("G", GEN).move_to([-3.0, 1.5, 0])
        fake = self._mini_chip("fake", GEN, 1.2).move_to([-0.6, 1.5, 0])
        Dd = self._mini_box("D", DISC).move_to([1.8, 1.5, 0])
        score = self._mini_chip("real?", DISC, 1.3).move_to([4.4, 1.5, 0])
        row = [z, G, fake, Dd, score]
        arrs = VGroup(*[
            Arrow(a.get_right(), b.get_left(), buff=0.12, color=INK,
                  stroke_width=3.2, max_tip_length_to_length_ratio=0.28)
            for a, b in zip(row[:-1], row[1:])])

        cap = self.show_say(
            "Training is a loop. Noise goes in, a fake comes out, the judge scores it.")
        self.play(LaggedStart(*[FadeIn(m) for m in row], lag_ratio=0.15),
                  run_time=1.2)
        self.play(LaggedStart(*[GrowArrow(a) for a in arrs], lag_ratio=0.15),
                  run_time=1.0)
        self.beat(1.8)

        # two feedback lanes (own lanes, orthogonal elbows, heads enter head-on)
        cap = self.replace_say(
            cap, "The score trains both networks, pulling them in opposite directions.")
        d_lane, d_lbl = self._feedback(score, Dd, y=-0.15, color=BAD,
                                       label="update D: catch fakes")
        g_lane, g_lbl = self._feedback(score, G, y=-1.15, color=GOOD,
                                       label="update G: fool D")
        self.play(Create(d_lane), FadeIn(d_lbl), run_time=0.9)
        self.play(Create(g_lane), FadeIn(g_lbl), run_time=0.9)
        self.beat(1.8)

        # the minimax, in plain language
        cap = self.replace_say(
            cap, "The discriminator wants to be right; the generator wants it to be wrong.")
        mm = self._minimax().next_to(g_lbl, DOWN, buff=0.55)
        self.play(FadeIn(mm, shift=UP * 0.15), run_time=0.8)
        self.beat(2.2)

        self.play(FadeOut(Group(*[m for m in row], arrs, d_lane, d_lbl,
                                g_lane, g_lbl, mm)), run_time=0.7)

        # --- the real training morph: blob -> ring --- #
        cap = self.replace_say(
            cap, "Watch what happens as the two networks train against each other.")
        ring = Circle(radius=RING_R * S2W, color=REAL, stroke_width=1.4,
                      stroke_opacity=0.4, fill_opacity=0)
        realr = cloud(REAL_PTS, REAL, r=0.026, op=0.3)
        # morph through these snapshots; only draw fakes that stay on-screen at
        # every step (a few real outliers streak off-frame mid-training).
        seq = [0, 1, 2, 3, 5, 6]
        maxabs = np.abs(G_SAMPLES[seq]).max(axis=(0, 2))     # (700,) over snaps & xy
        safe = np.where(maxabs < 2.9)[0]
        idx = np.random.default_rng(9).choice(safe, min(170, len(safe)), replace=False)
        fakes = cloud(G_SAMPLES[0][idx], GEN, r=0.04, op=0.9)
        self.play(FadeIn(realr), Create(ring), FadeIn(fakes), run_time=0.8)

        hud = self._score_hud(D_REAL[0], D_FAKE[0], ITERS[0])
        self._fix(hud)
        self.play(FadeIn(hud), run_time=0.5)
        self.beat(1.4)

        show = seq[1:]                   # snapshot indices to morph through
        for si in show:
            tgt = G_SAMPLES[si][idx]
            anims = [fakes[k].animate.move_to(w2(tgt[k])) for k in range(len(idx))]
            new_hud = self._score_hud(D_REAL[si], D_FAKE[si], ITERS[si])
            self._fix(new_hud)
            self.play(LaggedStart(*anims, lag_ratio=0.002),
                      FadeIn(new_hud), FadeOut(hud), run_time=1.5)
            hud = new_hud
            self.beat(0.9)

        cap = self.replace_say(
            cap, "The fakes spread out and lock onto all eight modes of the real data.")
        self.beat(1.8)
        cap = self.replace_say(
            cap, "And the judge's scores for real and fake drift to the same value.")
        self.beat(2.0)
        self.settle()
        self.play(FadeOut(Group(realr, ring, fakes, hud, hdr, cap)), run_time=0.8)

    def _mini_box(self, s, color):
        box = RoundedRectangle(width=1.05, height=1.05, corner_radius=0.12,
                               stroke_color=color, stroke_width=2.6,
                               fill_color=PANEL, fill_opacity=0.95)
        return VGroup(box, txt(s, 32, color, weight="BOLD").move_to(box))

    def _mini_chip(self, s, color, w=1.0):
        box = RoundedRectangle(width=w, height=0.72, corner_radius=0.14,
                               stroke_color=color, stroke_width=2.0,
                               fill_color=BG, fill_opacity=0.9)
        t = txt(s, 22, color)
        if t.width > w - 0.2:
            t.scale_to_fit_width(w - 0.2)
        return VGroup(box, t.move_to(box))

    def _feedback(self, src, dst, y, color, label):
        """A clean right-angle return edge in its own lane (head enters head-on)."""
        x0 = src.get_bottom()[0]
        drop = np.array([x0, y, 0])
        target = np.array([dst.get_center()[0], dst.get_bottom()[1] - 0.06, 0])
        corner = np.array([target[0], y, 0])
        lane = VGroup(
            Line(src.get_bottom(), drop).set_stroke(color, 3),
            Line(drop, corner).set_stroke(color, 3),
            Arrow(corner, target, buff=0.02, color=color, stroke_width=3,
                  max_tip_length_to_length_ratio=0.5, tip_length=0.16))
        lbl = txt(label, 19, color).move_to([(x0 + target[0]) / 2, y - 0.32, 0])
        return lane, lbl

    def _minimax(self):
        mn = VGroup(txt("min", 30, GEN), txt("G", 19, GEN)).arrange(RIGHT, buff=0.03)
        mn[1].align_to(mn[0], DOWN).shift(DOWN * 0.12)
        mx = VGroup(txt("max", 30, DISC), txt("D", 19, DISC)).arrange(RIGHT, buff=0.03)
        mx[1].align_to(mx[0], DOWN).shift(DOWN * 0.12)
        body = txt("V(D, G)", 30, INK)
        row = VGroup(mn, mx, body).arrange(RIGHT, buff=0.28)
        gloss = txt("a two-player minimax game", 21, MUTED).next_to(row, DOWN, buff=0.16)
        return VGroup(row, gloss)

    def _score_hud(self, dreal, dfake, it):
        rows = VGroup(
            VGroup(txt("D(real)", 22, REAL), txt(f"{dreal:.2f}", 24, INK, font=MONO)
                   ).arrange(RIGHT, buff=0.25),
            VGroup(txt("D(fake)", 22, GEN), txt(f"{dfake:.2f}", 24, INK, font=MONO)
                   ).arrange(RIGHT, buff=0.25),
        ).arrange(DOWN, buff=0.16, aligned_edge=LEFT)
        step = txt(f"step {int(it)}", 19, MUTED).next_to(rows, DOWN, buff=0.18)
        inner = VGroup(rows, step)
        box = RoundedRectangle(width=inner.width + 0.7, height=inner.height + 0.55,
                               corner_radius=0.12, stroke_color=FAINT, stroke_width=1.6,
                               fill_color=PANEL, fill_opacity=0.92)
        inner.move_to(box)
        return VGroup(box, inner).to_corner(UR, buff=0.5)

    # ====================================================================== #
    # Scene 6 — convergence: the terrain melts flat, then a latent-space walk
    # ====================================================================== #
    def scene_convergence(self):
        self.go_3d(phi=64, theta=-58, zoom=0.92, rate=0.05)
        hdr = self.section_header("Convergence", color=GOOD)
        cap = self.show_say(
            "Rewind to the discriminator's landscape, back when the fakes were bad.")
        self.build_terrain(D_TEACH_BAR, rt=1.6)
        self.beat(1.6)

        cap = self.replace_say(
            cap, "As the fakes get good, that sharp valley has nowhere to hide.")
        self.morph_terrain(D_BARS[2], rt=2.0)
        self.beat(1.2)
        self.morph_terrain(D_BARS[4], rt=1.8)
        self.beat(1.0)

        cap = self.replace_say(
            cap, "The whole landscape flattens: every point scores about one half.")
        self.morph_terrain(D_BARS[6], rt=2.2)
        self.beat(1.6)
        cap = self.replace_say(
            cap, "The discriminator is reduced to a coin flip. It cannot tell them apart.")
        self.beat(2.2)
        self.settle()
        self.wipe()

        # --- latent-space walk: continuity of the learned distribution --- #
        self.go_flat_instant()
        hdr2 = self.section_header("The payoff", color=GEN)
        zc = np.array([-3.6, -0.1, 0])
        oc = np.array([3.6, -0.1, 0])
        zpanel = self._panel("latent space z", GEN, zc, 2.9, 2.9)
        opanel = self._panel("generated samples", REAL, oc, 2.9, 2.9)
        # a scaled latent circle path + a moving dot
        zpath_pts = [zc + np.array([p[0] * 0.62, p[1] * 0.62, 0]) for p in WALK_Z]
        zpath = VMobject().set_points_smoothly(zpath_pts).set_stroke(GEN, 2, opacity=0.4)
        zdot = Dot(zpath_pts[0], radius=0.07, color=GEN)

        ring = Circle(radius=RING_R * S2W * 0.62, color=REAL, stroke_width=1.5,
                      stroke_opacity=0.45).move_to(oc)
        opath_pts = [oc + np.array([p[0], p[1], 0]) * S2W * 0.62 for p in WALK_XY]
        odot = Dot(opath_pts[0], radius=0.07, color=GEN)
        trail = TracedPath(odot.get_center, stroke_color=GEN, stroke_width=3.5)

        cap = self.show_say(
            "Now every point in the latent space maps to a new generated sample.")
        self.play(FadeIn(zpanel), Create(zpath), FadeIn(zdot), run_time=0.9)
        self.play(FadeIn(opanel), FadeIn(ring), FadeIn(odot), run_time=0.7)
        self.add(trail)
        self.beat(1.4)

        cap = self.replace_say(
            cap, "Glide smoothly through z, and the outputs sweep smoothly around the ring.")
        zmove = VMobject().set_points_smoothly(zpath_pts)
        omove = VMobject().set_points_smoothly(opath_pts)
        self.play(MoveAlongPath(zdot, zmove), MoveAlongPath(odot, omove),
                  run_time=5.0, rate_func=linear)
        self.beat(1.6)

        cap = self.replace_say(
            cap, "The generator has learned the whole distribution, not just the samples.")
        self.beat(2.2)
        self.settle()
        trail.clear_updaters()
        self.play(FadeOut(Group(zpanel, opanel, zpath, zdot, ring, odot, trail,
                                hdr2, cap)), run_time=0.8)

    # ====================================================================== #
    # Outro — a pretty orbiting terrain behind the thank-you.
    # ====================================================================== #
    def play_outro(self):
        self.go_3d(phi=62, theta=-52, zoom=0.9, rate=0.05)
        self.build_terrain(D_TEACH_BAR, rt=1.6)
        self.beat(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=GEN)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = Text("A generator and a discriminator, locked in a game: one learns to create.",
                     font_size=24, color="#B7C0D0")
        recap.next_to(writer, DOWN, buff=0.5)
        if recap.width > 12.4:
            recap.scale_to_fit_width(12.4)
        card = VGroup(header, line, writer, recap)
        scrim = RoundedRectangle(width=card.width + 1.4, height=card.height + 1.1,
                                 corner_radius=0.2, stroke_width=0,
                                 fill_color=BG, fill_opacity=0.9).move_to(card)
        self._fix(scrim, card)
        self.play(FadeIn(scrim), run_time=0.5)
        self.play(Write(header), Create(line), run_time=1.5)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.play(FadeIn(recap), run_time=0.7)
        self.card_wait(2.4)
        self.stop_orbit()
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)

    # ====================================================================== #
    # The whole film
    # ====================================================================== #
    def play_all(self):
        self.play_intro()
        self.scene_goal()
        self.scene_players()
        self.scene_generator()
        self.scene_discriminator()
        self.scene_game()
        self.scene_convergence()
        self.play_outro()


# ---- thin per-scene classes + the whole film ------------------------------ #
class Intro(_GANBase):
    def construct(self):
        self.play_intro()


class Goal(_GANBase):
    def construct(self):
        self.scene_goal()


class Players(_GANBase):
    def construct(self):
        self.scene_players()


class Generator(_GANBase):
    def construct(self):
        self.scene_generator()


class Discriminator(_GANBase):
    def construct(self):
        self.scene_discriminator()


class Game(_GANBase):
    def construct(self):
        self.scene_game()


class Convergence(_GANBase):
    def construct(self):
        self.scene_convergence()


class Outro(_GANBase):
    def construct(self):
        self.play_outro()


class WhatIsAGAN(_GANBase):
    def construct(self):
        self.play_all()

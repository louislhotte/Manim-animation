"""Moiré of Life
================

Two overlapping grids of sine waves. One rotates slowly against the other and
their interference blooms into breathing, swirling mandalas. Then the camera
falls into the centre — the giant macro-pattern grows past the edges of the
frame and dissolves back into the bare micro sine waves that were there all
along.

Nothing is drawn as vector geometry. Every frame is a scalar interference field

    grid(θ) = Σ_{k<N} sin( k_f · (x·cos a_k + y·sin a_k) ),   a_k = θ + kπ/N

    F(x, y) = grid(spin) + grid(spin + φ)              (a "moiré")

computed on a numpy pixel array, coloured through a hand-built look-up table and
pushed straight into a full-frame ``ImageMobject`` whose ``pixel_array`` is
mutated in place on every frame (Manim re-reads it each time it rasterises).

Each *grid* is a fan of ``N`` sine gratings evenly spread over a half-turn, so a
single grid already has N-fold rotational symmetry — a mandala. Overlaying two,
the second turned by ``φ``, gives their moiré. Rotation is that relative angle
``φ``; the zoom is an *exponential* shrink of the sampling frequency
``k_f ∝ 1/zoom`` about the origin, so the centre of the frame is what we plunge
into, until the giant mandala inflates past the edges and the bare sine waves
remain.

Only numpy + Pillow are needed (both already ship with Manim) — no matplotlib,
no LaTeX.

Knobs (env vars):
    MOIRE_RES     field height in px (width follows the 16:9 frame). Default 720.
    MOIRE_FREQ    grid density: sine cycles across the frame height. Default 26.
    MOIRE_ZOOM    final zoom factor reached at the bottom of the dive. Default 11.
    MOIRE_SYM     gratings per grid = the fold of the mandala. Default 6.
    MOIRE_QUICK   1 = shorten every beat (fast sanity check).

Render:
    ./render.sh                # 480p sanity check
    ./render.sh -q m           # 720p
    ./render.sh -q h           # 1080p60 final
"""

from __future__ import annotations

import math
import os

import numpy as np
from manim import (
    BLACK,
    DOWN,
    ORIGIN,
    UP,
    WHITE,
    FadeIn,
    FadeOut,
    ImageMobject,
    Line,
    Scene,
    Text,
    ValueTracker,
    VGroup,
    config,
    linear,
)

# --------------------------------------------------------------------------- #
# Tunables
# --------------------------------------------------------------------------- #
RES = int(os.environ.get("MOIRE_RES", "720"))          # field height, px
FREQ = float(os.environ.get("MOIRE_FREQ", "26"))       # sine cycles / frame-height
ZOOM_MAX = float(os.environ.get("MOIRE_ZOOM", "11"))   # final dive magnification
SYM = int(os.environ.get("MOIRE_SYM", "6"))            # gratings per grid (fold)
QUICK = os.environ.get("MOIRE_QUICK", "0") == "1"

SPEED = 0.30 if QUICK else 1.0                          # global time compression


def rt(seconds: float) -> float:
    """Run-time, compressed when MOIRE_QUICK is on (never below Manim's floor)."""
    return max(0.4, seconds * SPEED)


# --------------------------------------------------------------------------- #
# Colour: a hand-built indigo -> violet -> magenta -> ember -> gold ramp,
# baked into a 256-entry look-up table so per-frame colouring is a single
# fancy-index instead of three interpolations.
# --------------------------------------------------------------------------- #
_STOPS = [
    (0.00, (6, 6, 26)),      # near-black indigo (the void between fringes)
    (0.16, (28, 14, 78)),    # deep violet
    (0.34, (86, 24, 132)),   # royal purple
    (0.50, (168, 40, 128)),  # magenta
    (0.64, (224, 74, 96)),   # rose / ember
    (0.80, (246, 158, 70)),  # gold
    (0.92, (252, 214, 138)),
    (1.00, (255, 245, 214)),  # warm white (the crests)
]


def _build_lut() -> np.ndarray:
    pos = np.array([s[0] for s in _STOPS])
    cols = np.array([s[1] for s in _STOPS], dtype=np.float32)
    grid = np.linspace(0.0, 1.0, 256)
    lut = np.empty((256, 3), dtype=np.float32)
    for c in range(3):
        lut[:, c] = np.interp(grid, pos, cols[:, c])
    return lut / 255.0


def _field_rgba(
    X: np.ndarray,
    Y: np.ndarray,
    lut: np.ndarray,
    vig: np.ndarray,
    out: np.ndarray,
    freq: float,
    n_sym: int,
    phi: float,
    zoom: float,
    spin: float,
) -> np.ndarray:
    """One frame of the interference field, written into ``out`` (H, W, 4 uint8).

    Each *grid* is a fan of ``n_sym`` sine gratings, evenly fanned over a
    half-turn (angles ``k·π/n_sym``). A single fan already has ``n_sym``-fold
    rotational symmetry about the origin — a mandala. We overlay two such grids,
    the second rotated by ``phi``; their interference is the moiré. ``zoom``
    shrinks the sampling frequency about the origin (the dive) and ``spin``
    turns the whole field. Kept at module scope so it can be exercised without a
    Manim scene.
    """
    # kf * coordinate gives freq/zoom sine cycles across the frame height.
    kf = math.pi * freq / zoom

    F = np.zeros(X.shape, dtype=np.float32)
    for offset in (spin, spin + phi):                    # the two grids
        for k in range(n_sym):                           # fan of gratings
            a = offset + math.pi * k / n_sym
            F += np.sin(kf * (X * math.cos(a) + Y * math.sin(a)))

    # F is a sum of M = 2·n_sym sines (~Gaussian). Scale by its spread so the
    # colours keep their punch instead of collapsing to mid-grey, then clip.
    m = 2 * n_sym
    scale = 1.0 / (2.7 * math.sqrt(m / 2.0))
    v = 0.5 + scale * F
    idx = (v * 255.0).astype(np.int32)
    np.clip(idx, 0, 255, out=idx)
    rgb = lut[idx]                                        # (H, W, 3) float

    # Etch fine contour lines where the field crosses integers -> the crisp
    # filigree that makes it read as a mandala rather than a blur.
    ridge = 0.5 + 0.5 * np.cos(math.pi * F)
    rgb = rgb * (0.72 + 0.28 * ridge)[..., None]
    rgb = rgb * vig

    np.multiply(rgb, 255.0, out=rgb)
    np.clip(rgb, 0, 255, out=rgb)
    out[..., :3] = rgb.astype(np.uint8)
    return out


class MoireOfLife(Scene):
    def construct(self):
        config.background_color = BLACK

        H = RES
        W = int(round(H * config.frame_width / config.frame_height))  # 16:9
        asp = W / H

        # Static sampling grid, aspect-corrected so mandalas stay circular.
        xs = np.linspace(-asp, asp, W, dtype=np.float32)
        ys = np.linspace(-1.0, 1.0, H, dtype=np.float32)
        X, Y = np.meshgrid(xs, ys)                       # (H, W)

        lut = _build_lut()

        # Radial vignette -> a dark "portal" rim, precomputed once.
        rn2 = (X * X + Y * Y) / (asp * asp + 1.0)
        vig = np.clip(1.10 - 0.62 * rn2, 0.34, 1.0).astype(np.float32)[..., None]

        out = np.empty((H, W, 4), dtype=np.uint8)
        out[..., 3] = 255                                # fully opaque, always

        def field_rgba(phi: float, zoom: float, spin: float) -> np.ndarray:
            return _field_rgba(X, Y, lut, vig, out, FREQ, SYM, phi, zoom, spin)

        # ----- animated parameters ----------------------------------------- #
        phi = ValueTracker(0.055)      # relative rotation of the two grids
        logz = ValueTracker(0.0)       # log-zoom (exponential dive)
        spin = ValueTracker(0.0)       # global orientation drift

        field = ImageMobject(
            field_rgba(phi.get_value(), 1.0, 0.0),
            scale_to_resolution=H,
        )
        field.stretch_to_fit_height(config.frame_height)
        field.stretch_to_fit_width(config.frame_width)
        field.move_to(ORIGIN)

        def redraw(m):
            m.pixel_array = field_rgba(
                phi.get_value(), math.exp(logz.get_value()), spin.get_value()
            )

        field.add_updater(redraw)
        self.add(field)

        # ----- title card --------------------------------------------------- #
        title = _title("Moiré of Life", 0.92)
        rule = Line(title.get_left(), title.get_right(), color=WHITE, stroke_width=1.5)
        rule.set_opacity(0.7).next_to(title, DOWN, buff=0.16)
        subtitle = _label("two grids of sine waves, interfering", 0.32)
        subtitle.next_to(rule, DOWN, buff=0.22)
        titles = VGroup(title, rule, subtitle).move_to(ORIGIN).set_z_index(10)

        self.play(
            FadeIn(titles, shift=UP * 0.15),
            phi.animate.set_value(0.08),
            run_time=rt(3.0),
        )
        self.play(phi.animate.set_value(0.11), run_time=rt(1.6))
        self.play(FadeOut(titles), phi.animate.set_value(0.15), run_time=rt(1.6))

        # ----- Act I: the mandala swirls ----------------------------------- #
        # Rising phi re-tiles the rosette (the 12-fold cells regroup into ever
        # larger flowers); the spin turns the whole tapestry -> a slow swirl.
        self.play(
            phi.animate.set_value(0.30),
            spin.animate.set_value(0.50),
            run_time=rt(16.0),
            rate_func=linear,
        )
        # A breath: cells swell, then tighten again — spin keeps advancing.
        self.play(
            phi.animate.set_value(0.22),
            spin.animate.set_value(0.60),
            run_time=rt(4.5),
            rate_func=linear,
        )
        self.play(
            phi.animate.set_value(0.40),
            spin.animate.set_value(0.74),
            run_time=rt(4.5),
            rate_func=linear,
        )

        # ----- Act II: the dive -------------------------------------------- #
        # Exponential zoom about the centre. The macro mandala inflates past the
        # frame and the bare micro sine waves emerge.
        self.play(
            logz.animate.set_value(math.log(ZOOM_MAX)),
            phi.animate.set_value(0.44),
            spin.animate.set_value(1.00),
            run_time=rt(20.0),
            rate_func=linear,
        )

        # ----- Act III: down to the micro waves ---------------------------- #
        caption = _label("the same wave, all the way down", 0.36).set_z_index(10)
        caption.to_edge(DOWN, buff=0.7)
        self.play(FadeIn(caption, shift=UP * 0.1), run_time=rt(1.4))
        self.play(
            spin.animate.set_value(1.22),
            phi.animate.set_value(0.48),
            run_time=rt(5.0),
            rate_func=linear,
        )
        self.play(FadeOut(caption), run_time=rt(1.2))

        # ----- fade out (drop the updater first so alpha isn't overwritten) - #
        field.clear_updaters()
        self.play(FadeOut(field), run_time=rt(2.2))


# --------------------------------------------------------------------------- #
# Text helpers.  Manim mangles letter spacing at small font sizes, so build
# every label large and scale it down to the target height.
# --------------------------------------------------------------------------- #
_BASE_FS = 96


def _title(s: str, height: float) -> Text:
    t = Text(s, font_size=_BASE_FS, weight="BOLD", color=WHITE)
    t.scale(height / t.height)
    return t


def _label(s: str, height: float) -> Text:
    t = Text(s, font_size=_BASE_FS, color=WHITE)
    t.set_opacity(0.85)
    t.scale(height / t.height)
    return t

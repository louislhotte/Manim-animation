"""Model Quantization — a short, 3D, perpetually-orbiting house-style explainer.

The one idea: a trained model is millions of numbers stored at full precision
(FP32, 32 bits each). Quantization stores each number with far fewer bits by
snapping every value onto a small grid of allowed levels (2^b of them for b
bits) and keeping one shared scale. Fewer bits means a much smaller, faster
model; the price is a little rounding error. INT8 is nearly free; INT4 is where
you trade a little quality for a lot of memory.

Visual language (inspired by a 3D "field of numbers" landscape): the model's
weights are a field of glowing bars standing on a dark plane. A slow ambient
camera orbit keeps the whole piece gently in motion. Every word the viewer reads
(title, captions, HUD) is a fixed-in-frame overlay so it stays put while the
field turns underneath.

All text is ``Text`` (Pango), no LaTeX. Scenes render individually (``Field``,
``Precision``, ``Snap``, ``BitWidth``, ``Mapping``, ``Payoff`` …) or as one film
(``ModelQuantization``).

Env knobs:
    QZ_QUICK=1   collapse every hold for a fast layout render
    QZ_DELAY=<s> override the reading-rhythm multiplier
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

QUICK = os.environ.get("QZ_QUICK") == "1"
# Reading rhythm. 2.3 so the formulas / HUD read comfortably.
DELAY = float(os.environ.get("QZ_DELAY", 0.28 if QUICK else 2.3))
ANIM_SLOW = 1.0 if QUICK else 1.15
END_HOLD = 0.2 if QUICK else 2.2

# ---- palette (shared with the Transformer / KV-cache / Tensors series) ---- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text
FAINT = "#3A4152"       # hairlines, faint structure
BAR = "#43C6E8"         # the glowing bars (bright cyan-blue)
AX1 = "#5B8DEF"         # blue
GOOD = "#3DD68C"        # green
GOLD = "#FFD166"        # accent / gold
BAD = "#FF5C5C"         # red / stop
PANEL = "#141C29"       # HUD panel fill
MONO = "Menlo"
FONT = "Helvetica Neue"

# ---- crisp small text ----------------------------------------------------- #
# Pango mangles glyphs/spacing below ~20 pt (subscripts come out in a fallback
# font). Shadow Text so every call rasterises at a large base and is scaled DOWN.
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
# The weight field: an N×N grid of glowing bars on a dark plane.
# =========================================================================== #
N = 12                       # grid is N×N bars
FIELD_R = 4.3                # half-extent of the field in x and y (world units)
BAR_W = 0.30                 # bar footprint (square)
H_MIN, H_MAX = 0.18, 2.75    # bar height range
CELLS = [(i, j) for i in range(N) for j in range(N)]


def grid_xy(i, j, n=N, R=FIELD_R):
    step = 2 * R / (n - 1)
    return -R + i * step, -R + j * step


def _raw_field(n=N, seed=7):
    """A smooth-ish 'landscape' of positive values in [H_MIN, H_MAX]."""
    rng = np.random.default_rng(seed)
    noise = rng.random((n, n))
    xs = np.linspace(-1, 1, n)
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    wave = (0.55 * np.sin(2.3 * X + 0.6) * np.cos(2.0 * Y - 0.3)
            + 0.30 * np.sin(1.4 * X * Y + 1.1)
            + 0.22 * np.cos(3.1 * Y + 0.2)
            + 0.18 * np.sin(2.7 * X - 0.5))
    wave = (wave - wave.min()) / (wave.max() - wave.min())
    f = 0.62 * wave + 0.38 * noise
    f = (f - f.min()) / (f.max() - f.min())
    return H_MIN + f * (H_MAX - H_MIN)


FIELD = _raw_field()


EDGE = "#CDEEFF"        # bright neon edge on the bars


def make_bar(x, y, h, color=BAR, op=1.0, bw=BAR_W):
    h = max(0.06, float(h))
    p = Prism(dimensions=[bw, bw, h])
    p.move_to([x, y, h / 2])
    p.set_fill(color, opacity=op)
    p.set_stroke(EDGE, width=1.1, opacity=min(1.0, op) * 0.9)  # neon glow edge
    return p


def make_ground(n=N, R=FIELD_R, color=FAINT):
    step = 2 * R / (n - 1)
    ext = R + step * 0.5
    g = VGroup()
    for k in range(n + 1):
        c = -ext + k * step
        g.add(Line([c, -ext, 0], [c, ext, 0]))
        g.add(Line([-ext, c, 0], [ext, c, 0]))
    g.set_stroke(color=color, width=1.0, opacity=0.28)
    return g


def quantize(vals, K, lo=H_MIN, hi=H_MAX):
    """Snap each value to one of K evenly-spaced levels. Returns (levels, idx)."""
    step = (hi - lo) / K
    idx = np.clip(((np.asarray(vals) - lo) / step).astype(int), 0, K - 1)
    centers = lo + (idx + 0.5) * step
    return centers, idx


def level_palette(K):
    return color_gradient([BAR, GOOD, GOLD, BAD], max(2, K))


def level_colors(K):
    """Per-cell colour, keyed by which of K height-levels the value lands in."""
    _, idx = quantize(FIELD, K)
    pal = level_palette(K)
    return {(i, j): pal[idx[i][j]] for (i, j) in CELLS}


def height_colors():
    """Per-cell colour along the ramp by continuous height (for the pretty field)."""
    return level_colors(64)


def field_error_pct(K):
    q, _ = quantize(FIELD, K)
    return 100.0 * float(np.mean(np.abs(q - FIELD))) / (H_MAX - H_MIN)


# ---- small comparison fields (FP32 / INT8 / INT4 side by side) ------------- #
def subfield(m=6):
    idx = np.linspace(0, N - 1, m).astype(int)
    return FIELD[np.ix_(idx, idx)]


def smooth_field(m=8):
    """A smooth two-bump surface. When quantized it terraces cleanly, so the
    FP32 / INT8 / INT4 comparison shows the coarsening at a glance."""
    xs = np.linspace(-1, 1, m)
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    h = (np.exp(-((X - 0.30) ** 2 + (Y - 0.20) ** 2) * 2.2) * 1.00
         + np.exp(-((X + 0.45) ** 2 + (Y + 0.50) ** 2) * 3.0) * 0.72)
    h = (h - h.min()) / (h.max() - h.min())
    return H_MIN + h * (H_MAX - H_MIN)


def colors_for(heights, K):
    step = (H_MAX - H_MIN) / K
    idx = np.clip(((heights - H_MIN) / step).astype(int), 0, K - 1)
    pal = level_palette(K)
    return {(i, j): pal[idx[i][j]]
            for i in range(heights.shape[0]) for j in range(heights.shape[1])}


def make_mini_field(heights, colors, center, cell=0.34, bw=0.20, hscale=0.62):
    """A small NxM bar field centred at `center` (on the z=0 plane)."""
    rows, cnt = heights.shape
    ox = (rows - 1) / 2.0
    oy = (cnt - 1) / 2.0
    bars = VGroup()
    for i in range(rows):
        for j in range(cnt):
            x = center[0] + (i - ox) * cell
            y = center[1] + (j - oy) * cell
            h = max(0.05, float(heights[i][j]) * hscale)
            p = Prism(dimensions=[bw, bw, h]).move_to([x, y, h / 2])
            p.set_fill(colors[(i, j)], opacity=1.0)
            p.set_stroke(EDGE, width=0.8, opacity=0.85)
            bars.add(p)
    return bars


def mini_ground(center, half, color=FAINT, n=7):
    g = VGroup()
    for k in range(n + 1):
        c = -half + 2 * half * k / n
        g.add(Line([center[0] + c, center[1] - half, 0],
                   [center[0] + c, center[1] + half, 0]))
        g.add(Line([center[0] - half, center[1] + c, 0],
                   [center[0] + half, center[1] + c, 0]))
    return g.set_stroke(color=color, width=1.0, opacity=0.25)


# =========================================================================== #
# Base scene
# =========================================================================== #
class _QuantBase(ThreeDScene):
    def setup(self):
        self.camera.background_color = BG
        self._orbiting = False
        self.bars = {}          # (i,j) -> Prism currently on screen
        self.field_group = None
        self.ground = None

    # slow every played animation slightly; never scale a bare wait
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
    def go_3d(self, phi=66, theta=-58, zoom=0.85, rate=0.045, focal=None):
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

    def show_title(self, s, color=INK, fs=46, buff=0.42):
        t = Text(s, font_size=fs, color=color, weight="BOLD")
        if t.width > 12.8:
            t.scale_to_fit_width(12.8)
        t.to_edge(UP, buff=buff)
        self._fix(t)
        self.play(FadeIn(t, shift=DOWN * 0.12), run_time=0.7)
        return t

    def section_header(self, label, color=GOLD):
        t = Text(label, font_size=30, color=INK, weight="BOLD")
        line = Line(t.get_left(), t.get_right()).set_stroke(color=color, width=3)
        line.next_to(t, DOWN, buff=0.12)
        g = VGroup(t, line).to_corner(UL, buff=0.5)
        self._fix(g)
        self.play(FadeIn(g, shift=DOWN * 0.1), run_time=0.55)
        return g

    # ---- the weight field ------------------------------------------------- #
    def build_field(self, heights=None, colors=None, color=BAR, grow=True, rt=1.7):
        if heights is None:
            heights = FIELD
        self.ground = make_ground()
        self.add(self.ground)
        bars = {}
        for (i, j) in CELLS:
            x, y = grid_xy(i, j)
            col = colors[(i, j)] if colors is not None else color
            bars[(i, j)] = make_bar(x, y, heights[i][j], col)
        self.bars = bars
        self.field_group = VGroup(*[bars[c] for c in CELLS])
        order = sorted(CELLS, key=lambda ij: -grid_xy(*ij)[1])  # back -> front
        if grow:
            self.play(FadeIn(self.ground), run_time=0.6)
            anims = [GrowFromPoint(bars[c], [*grid_xy(*c), 0]) for c in order]
            self.play(LaggedStart(*anims, lag_ratio=0.006), run_time=rt)
        else:
            self.add(self.field_group)
        return self.field_group

    def morph_field(self, new_h, colors=None, rt=1.9, ripple=True, lag=0.010):
        """Transform every bar to a new height (and optional per-cell colour)."""
        order = sorted(CELLS, key=lambda ij: -grid_xy(*ij)[1])
        anims = []
        for (i, j) in order:
            x, y = grid_xy(i, j)
            col = colors[(i, j)] if colors is not None else BAR
            tgt = make_bar(x, y, new_h[i][j], col)
            anims.append(Transform(self.bars[(i, j)], tgt))
        if ripple:
            self.play(LaggedStart(*anims, lag_ratio=lag), run_time=rt)
        else:
            self.play(*anims, run_time=rt)

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
    def _rule_under(self, header, pad=1.0, color=GOLD, drop=0.45):
        return Line([header.get_left()[0] - pad, header.get_bottom()[1] - drop, 0],
                    [header.get_right()[0] + pad, header.get_bottom()[1] - drop, 0]
                    ).set_stroke(width=3, color=color)

    # ====================================================================== #
    # Intro card (flat)
    # ====================================================================== #
    def play_intro(self):
        self.go_flat_instant()
        header = Text("Model Quantization", font_size=56, color=INK, weight="BOLD")
        header.set(width=min(9.8, header.width))
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=AX1)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        sub = Text("How a huge model shrinks to run on small hardware",
                   font_size=30, color=MUTED)
        if sub.width > line.width:
            sub.scale_to_fit_width(line.width)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.card_wait(1.8)
        self.play(FadeOut(VGroup(header, writer, line)), run_time=1.0)
        self.card_wait(0.3)

    # ====================================================================== #
    # Scene: the neural network -> one layer's weights -> the 3D field
    # ====================================================================== #
    def scene_network(self, cap=None):
        self.go_flat_instant()
        hdr = self.section_header("Where the numbers come from")

        sizes = [4, 6, 6, 3]
        xs = [-5.9, -3.7, -1.5, 0.7]

        def col_ys(n):
            return np.linspace(2.0, -2.0, n) if n > 1 else np.array([0.0])

        neurons = []
        for li, n in enumerate(sizes):
            col = []
            for y in col_ys(n):
                d = Dot([xs[li], float(y), 0], radius=0.14)
                d.set_fill(AX1, opacity=0.95).set_stroke(EDGE, width=1.2, opacity=0.7)
                col.append(d)
            neurons.append(col)
        edge_groups = []
        for li in range(len(sizes) - 1):
            eg = VGroup()
            for a in neurons[li]:
                for b in neurons[li + 1]:
                    eg.add(Line(a.get_center(), b.get_center(),
                                stroke_color=FAINT, stroke_width=1.4,
                                stroke_opacity=0.55))
            edge_groups.append(eg)
        all_neurons = [d for col in neurons for d in col]

        cap = self.show_say(
            "A neural network is layers of neurons joined by weighted connections.")
        self.play(LaggedStart(*[Create(eg) for eg in edge_groups],
                              lag_ratio=0.25), run_time=1.4)
        self.play(LaggedStart(*[GrowFromCenter(d) for d in all_neurons],
                              lag_ratio=0.02), run_time=0.9)
        self.beat(1.6)

        # highlight ONE layer's connections
        cap = self.replace_say(cap, "Every connection is one weight: a single number.")
        self.play(edge_groups[1].animate.set_stroke(BAR, width=2.4, opacity=1.0),
                  edge_groups[0].animate.set_stroke(opacity=0.10),
                  edge_groups[2].animate.set_stroke(opacity=0.10),
                  run_time=1.0)
        self.beat(1.7)

        # gather that layer's weights into a grid of numbers
        cap = self.replace_say(cap, "One layer's weights are just a grid of numbers.")
        gv = np.round(np.random.default_rng(4).uniform(-0.95, 0.95, (5, 6)), 2)
        grid = VGroup(*[VGroup(*[self._num_cell(f"{gv[r][c]:+.2f}") for c in range(6)]
                               ).arrange(RIGHT, buff=0.12) for r in range(5)]
                      ).arrange(DOWN, buff=0.12).scale(0.8)
        grid.to_edge(RIGHT, buff=0.55).shift(DOWN * 0.15)
        gl = txt("one layer's weights", 22, BAR).next_to(grid, UP, buff=0.22)
        self.play(FadeIn(VGroup(grid, gl), shift=LEFT * 0.2), run_time=0.9)
        self.beat(2.0)

        # to 3D: fade the diagram, reveal the field, ground it as ONE layer
        cap = self.replace_say(cap, "Picture that grid as a landscape, one bar per weight.")
        self.play(FadeOut(VGroup(*edge_groups, *all_neurons)),
                  FadeOut(VGroup(grid, gl)), FadeOut(hdr), run_time=0.7)
        self.go_3d()
        self.build_field()
        cap = self.replace_say(
            cap, "This whole field is one layer. A real model stacks hundreds of them.")
        self.beat(2.2)
        return cap

    def _num_cell(self, s, color=BAR):
        box = RoundedRectangle(width=0.92, height=0.5, corner_radius=0.08,
                               stroke_color=color, stroke_width=1.4,
                               fill_color=PANEL, fill_opacity=0.9)
        t = txt(s, 20, INK, font=MONO)
        if t.width > 0.78:
            t.scale_to_fit_width(0.78)
        t.move_to(box)
        return VGroup(box, t)

    # ====================================================================== #
    # Scene: each weight is a number; removing bits coarsens it (flicker)
    # ====================================================================== #
    def scene_numbers(self, cap=None):
        hdr = self.section_header("Each weight is a number")
        weights = [0.732612, -0.183904, 0.556120]

        row_labels = VGroup(*[txt(f"weight {i + 1}", 24, MUTED) for i in range(3)])
        row_labels.arrange(DOWN, buff=0.52, aligned_edge=LEFT)
        meta_labels = VGroup(txt("precision", 22, MUTED), txt("error", 22, MUTED))
        meta_labels.arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        meta_labels.next_to(row_labels, DOWN, buff=0.5, aligned_edge=LEFT)
        chrome = VGroup(row_labels, meta_labels).move_to([-2.1, 0.35, 0])

        vx = row_labels.get_right()[0] + 2.5
        self._val_anchors = [[vx, row_labels[i].get_center()[1], 0] for i in range(3)]
        self._tag_anchor = [meta_labels[0].get_right()[0] + 1.7,
                            meta_labels[0].get_center()[1], 0]
        self._err_anchor = [meta_labels[1].get_right()[0] + 1.7,
                            meta_labels[1].get_center()[1], 0]

        self._vals = [txt(f"{w:+.6f}", 28, BAR, font=MONO).move_to(self._val_anchors[i])
                      for i, w in enumerate(weights)]
        self._tag = txt("FP32", 26, INK, font=MONO, weight="BOLD").move_to(self._tag_anchor)
        self._err = txt("0.0%", 26, GOOD, font=MONO).move_to(self._err_anchor)
        content = VGroup(chrome, *self._vals, self._tag, self._err)
        scrim = RoundedRectangle(width=content.width + 1.3, height=content.height + 0.9,
                                 corner_radius=0.2, stroke_color=BAR, stroke_width=1.5,
                                 fill_color=BG, fill_opacity=0.9).move_to(content)

        self._fix(scrim)
        self.play(FadeIn(scrim), run_time=0.45)
        reveal = [chrome, *self._vals, self._tag, self._err]
        self.add_fixed_in_frame_mobjects(*reveal)
        for m in reveal:
            self.remove(m)
        cap = self.replace_say(
            cap, "Zoom in, and each bar is really a number stored in 32 bits.")
        self.play(*[FadeIn(m) for m in reveal], run_time=0.6)
        self.beat(2.0)

        cap = self.replace_say(
            cap, "Store it in 8 bits and each value snaps to the nearest step.")
        self._flicker_values([self._q_sym(w, 8) for w in weights])
        self._swap_meta("INT8", f"{self._sym_err(weights, 8):.1f}%", GOOD)
        self.beat(2.0)

        cap = self.replace_say(
            cap, "In 4 bits it is coarser still, and a little accuracy is lost.")
        self._flicker_values([self._q_sym(w, 4) for w in weights])
        self._swap_meta("INT4", f"{self._sym_err(weights, 4):.1f}%", GOLD)
        self.beat(2.2)

        self.play(FadeOut(scrim), FadeOut(chrome), FadeOut(self._tag),
                  FadeOut(self._err), *[FadeOut(v) for v in self._vals],
                  FadeOut(hdr), run_time=0.6)
        return cap

    @staticmethod
    def _q_sym(w, b):
        maxq = 2 ** (b - 1) - 1
        return round(w * maxq) / maxq

    @staticmethod
    def _sym_err(ws, b):
        maxq = 2 ** (b - 1) - 1
        return 100.0 * float(np.mean([abs(round(w * maxq) / maxq - w) for w in ws]))

    def _flicker_values(self, finals, decimals=4, n=9, hold=0.05):
        curs = list(self._vals)
        for _ in range(n):
            news = [txt(f"{np.random.uniform(-0.95, 0.95):+.{decimals}f}", 28, INK,
                        font=MONO).move_to(a) for a in self._val_anchors]
            self.add_fixed_in_frame_mobjects(*news)
            for c in curs:
                self.remove(c)
            curs = news
            self.wait(hold)
        finals_m = [txt(f"{finals[i]:+.{decimals}f}", 28, BAR, font=MONO).move_to(a)
                    for i, a in enumerate(self._val_anchors)]
        self.add_fixed_in_frame_mobjects(*finals_m)
        for c in curs:
            self.remove(c)
        self._vals = finals_m

    def _swap_meta(self, tag_s, err_s, err_col):
        nt = txt(tag_s, 26, INK, font=MONO, weight="BOLD").move_to(self._tag_anchor)
        ne = txt(err_s, 26, err_col, font=MONO).move_to(self._err_anchor)
        self.add_fixed_in_frame_mobjects(nt, ne)
        self.play(FadeOut(self._tag), FadeIn(nt), FadeOut(self._err), FadeIn(ne),
                  run_time=0.4)
        self._tag, self._err = nt, ne

    # ====================================================================== #
    # Scene: the snap (the core mechanic)
    # ====================================================================== #
    SNAP_K = 8

    def beat_snap(self, cap=None):
        hdr = self.section_header("Quantize")
        msg = "Pick a small set of allowed levels."
        cap = self.replace_say(cap, msg) if cap else self.show_say(msg)
        self.beat(1.6)

        cap = self.replace_say(
            cap, "Then snap every weight to its nearest level.")
        centers, _ = quantize(FIELD, self.SNAP_K)
        cols = level_colors(self.SNAP_K)
        self.morph_field(centers, cols, rt=2.4, lag=0.012)
        self.beat(1.9)

        cap = self.replace_say(
            cap, "Now a weight is just a level number, plus one shared scale.")
        self.beat(2.0)
        cap = self.replace_say(
            cap, "A small integer instead of a full 32-bit number.")
        self.beat(1.9)
        self.play(FadeOut(hdr), run_time=0.4)
        return cap

    # ====================================================================== #
    # Scene: FP32 / INT8 / INT4 side by side (the coarsening)
    # ====================================================================== #
    def scene_compare(self, cap=None):
        # No section header here: the three big FP32/INT8/INT4 plates span the top
        # and act as the header, so a corner header would collide with them.
        msg = "The bit budget sets how many levels each weight can take."
        cap = self.replace_say(cap, msg) if cap else self.show_say(msg)
        self.beat(1.8)

        sub = smooth_field(8)
        specs = [("FP32", "continuous", None, GOOD),
                 ("INT8", "256 levels", 256, GOOD),
                 ("INT4", "16 levels", 16, GOLD)]
        cx = [-4.6, 0.0, 4.6]
        minis, plates = [], []
        for k, (name, desc, K, col) in enumerate(specs):
            h = sub if K is None else quantize(sub, K)[0]
            cols = colors_for(h, K if K else 64)
            mf = make_mini_field(h, cols, [cx[k], 0.0, 0], cell=0.30, bw=0.19, hscale=1.05)
            mg = mini_ground([cx[k], 0.0, 0], half=1.35)
            minis.append(VGroup(mg, mf))

        # swing to a clean front-on view so the three sit side by side (no orbit,
        # so the coarsening reads clearly); the big field fades out as we move.
        self.stop_orbit()
        drop = [m for m in (self.field_group, self.ground) if m is not None]
        self.move_camera(phi=60 * DEGREES, theta=-90 * DEGREES, zoom=0.82,
                         added_anims=[FadeOut(m) for m in drop], run_time=1.3)
        self.bars, self.field_group, self.ground = {}, None, None
        self.play(LaggedStart(*[FadeIn(m, shift=UP * 0.15) for m in minis],
                              lag_ratio=0.25), run_time=1.3)

        # billboard labels floating above each field
        for k, (name, desc, K, col) in enumerate(specs):
            g = VGroup(txt(name, 30, INK, weight="BOLD"), txt(desc, 20, col)
                       ).arrange(DOWN, buff=0.08)
            g.move_to([cx[k], -0.2, 3.6])
            self.add_fixed_orientation_mobjects(g)
            plates.append(g)
        self.beat(1.4)

        cap = self.replace_say(
            cap, "FP32 is the original. INT8 keeps 256 levels and looks the same.")
        self.beat(2.1)
        cap = self.replace_say(
            cap, "INT4 keeps only 16. It visibly steps, but the model still runs.")
        self.beat(2.2)
        cap = self.replace_say(
            cap, "Fewer bits, a coarser grid, and far less memory.")
        self.beat(1.9)
        self.play(*[FadeOut(m) for m in minis],
                  *[FadeOut(g) for g in plates], run_time=0.6)
        return cap

    # ====================================================================== #
    # Scene: the mapping (scale + zero-point), flat 2D
    # ====================================================================== #
    def scene_mapping(self, cap=None):
        self.go_flat_instant()
        hdr = self.section_header("The recipe")

        # concrete numbers, computed (never fabricated)
        w = 0.63
        wmin, wmax = -1.0, 1.0
        b = 4
        levels = 2 ** b
        scale = (wmax - wmin) / (levels - 1)          # 2.0 / 15
        zero = int(round(-wmin / scale))              # 8
        q = int(round(w / scale)) + zero              # 13
        q = max(0, min(levels - 1, q))
        recon = scale * (q - zero)                    # 0.6667

        # number line (real values)
        axis = Line([-5.6, 1.5, 0], [5.6, 1.5, 0]).set_stroke(INK, 2.5)
        ticks = VGroup()
        for k in range(levels):
            x = -5.6 + (5.6 - -5.6) * k / (levels - 1)
            ticks.add(Line([x, 1.5 - 0.12, 0], [x, 1.5 + 0.12, 0]).set_stroke(MUTED, 2))
        lo_lab = txt(f"{wmin:+.1f}", 22, MUTED).next_to(ticks[0], DOWN, buff=0.18)
        hi_lab = txt(f"{wmax:+.1f}", 22, MUTED).next_to(ticks[-1], DOWN, buff=0.18)
        idx_lab = txt("integers  0 … 15", 22, GOLD).next_to(axis, UP, buff=0.55)
        line_grp = VGroup(axis, ticks, lo_lab, hi_lab, idx_lab)

        self.play(Create(axis), LaggedStart(*[Create(t) for t in ticks],
                                            lag_ratio=0.02), run_time=1.1)
        self.play(FadeIn(lo_lab), FadeIn(hi_lab), FadeIn(idx_lab), run_time=0.5)

        # the sample weight, mapped to its bucket
        xw = -5.6 + (5.6 - -5.6) * (w - wmin) / (wmax - wmin)
        dot = Dot([xw, 1.5, 0], color=BAR, radius=0.10)
        wlab = txt(f"w = {w:+.2f}", 24, BAR).next_to(dot, UP, buff=0.9)
        wlab.set_x(xw)
        wlead = Line(wlab.get_bottom(), dot.get_top()).set_stroke(BAR, 2)
        xq = -5.6 + (5.6 - -5.6) * q / (levels - 1)
        arr = Arrow([xw, 1.5, 0], [xq, 1.5, 0], buff=0.05, color=GOLD,
                    stroke_width=4, max_tip_length_to_length_ratio=0.4)
        qmark = Dot([xq, 1.5, 0], color=GOLD, radius=0.10)
        cap = self.show_say("Split the value range into 16 evenly spaced buckets.")
        self.play(FadeIn(wlab), Create(wlead), FadeIn(dot), run_time=0.6)
        self.beat(1.6)
        cap = self.replace_say(cap, "Round each weight to the nearest bucket index.")
        self.play(GrowArrow(arr), FadeIn(qmark), run_time=0.7)
        self.beat(1.6)

        # the round trip, as plain arithmetic
        store = self._recipe_row("store", f"q = round( w / s ) + z  =  {q}", GOLD)
        recon_row = self._recipe_row(
            "recover", f"w  ≈  s × ( q − z )  =  {recon:+.2f}", GOOD)
        sz = self._recipe_row(
            "here", f"s = {scale:.3f},   z = {zero},   4 bits", MUTED)
        recipe = VGroup(store, recon_row, sz).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        recipe.move_to([0, -1.2, 0])
        self.play(FadeIn(store, shift=UP * 0.1), run_time=0.6)
        self.beat(1.4)
        self.play(FadeIn(recon_row, shift=UP * 0.1), run_time=0.6)
        self.beat(1.4)
        self.play(FadeIn(sz, shift=UP * 0.1), run_time=0.6)
        cap = self.replace_say(
            cap, "Store one small integer per weight, plus one scale for the tensor.")
        self.beat(2.2)
        self.settle()
        self.play(FadeOut(VGroup(line_grp, dot, wlab, wlead, arr, qmark, recipe,
                                 hdr, cap)), run_time=0.8)

    def _recipe_row(self, tag, body, color):
        t = txt(tag, 22, color, font=MONO)
        tbox = RoundedRectangle(width=1.9, height=0.6, corner_radius=0.1,
                                stroke_color=color, stroke_width=2,
                                fill_color=PANEL, fill_opacity=0.9)
        t.move_to(tbox)
        chip = VGroup(tbox, t)
        body_t = txt(body, 26, INK, font=MONO)
        row = VGroup(chip, body_t).arrange(RIGHT, buff=0.4)
        return row

    # ====================================================================== #
    # Scene: the payoff (memory), flat 2D
    # ====================================================================== #
    def scene_payoff(self):
        self.go_flat_instant()
        hdr = self.section_header("Why it matters")
        title = txt("A 7-billion-parameter model", 30, INK).to_edge(UP, buff=1.15)

        rows = [("FP32", 28.0, BAR), ("INT8", 7.0, GOOD), ("INT4", 3.5, GOLD)]
        maxw = 8.4
        bars = VGroup()
        for name, gb, col in rows:
            w = maxw * gb / 28.0
            bar = RoundedRectangle(width=w, height=0.8, corner_radius=0.08,
                                   stroke_color=col, stroke_width=2.5,
                                   fill_color=col, fill_opacity=0.28)
            nm = txt(name, 24, col, weight="BOLD")
            gbl = txt(f"{gb:g} GB", 24, INK)
            bars.add(VGroup(bar, nm, gbl))
        bars.arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        bars.next_to(title, DOWN, buff=0.7).to_edge(LEFT, buff=1.2)
        for grp in bars:
            bar, nm, gbl = grp
            nm.next_to(bar, LEFT, buff=0.3)
            gbl.next_to(bar, RIGHT, buff=0.3)

        self.play(FadeIn(title, shift=DOWN * 0.1), run_time=0.6)
        cap = self.show_say("At full precision it needs 28 gigabytes of memory.")
        bar0, nm0, gb0 = bars[0]
        self.play(GrowFromEdge(bar0, LEFT), FadeIn(nm0), FadeIn(gb0), run_time=0.8)
        self.beat(1.7)
        cap = self.replace_say(
            cap, "In INT8 it is 7 gigabytes. In INT4, under four.")
        for grp in bars[1:]:
            bar, nm, gbl = grp
            self.play(GrowFromEdge(bar, LEFT), FadeIn(nm), FadeIn(gbl), run_time=0.7)
            self.beat(0.7)
        self.beat(1.3)
        cap = self.replace_say(
            cap, "The same model now fits on a laptop, even a phone.")
        self.beat(2.0)
        cap = self.replace_say(
            cap, "Fewer bits to move also means faster inference.")
        self.beat(1.9)
        self.settle()
        self.play(FadeOut(VGroup(title, bars, hdr, cap)), run_time=0.8)

    # ====================================================================== #
    # Outro — back in motion: a pretty orbiting field behind the thank-you.
    # ====================================================================== #
    def play_outro(self):
        self.go_3d(phi=64, theta=-52, zoom=0.85, rate=0.05)
        self.build_field(colors=height_colors(), rt=1.6)
        self.beat(0.6)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=AX1)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = Text("Fewer bits per weight: a smaller, faster model, almost for free.",
                     font_size=24, color="#B7C0D0")
        recap.next_to(writer, DOWN, buff=0.5)
        if recap.width > 12.4:
            recap.scale_to_fit_width(12.4)
        card = VGroup(header, line, writer, recap)
        scrim = RoundedRectangle(width=card.width + 1.4, height=card.height + 1.1,
                                 corner_radius=0.2, stroke_width=0,
                                 fill_color=BG, fill_opacity=0.88).move_to(card)
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
        cap = self.scene_network()      # neural net -> one layer's weights -> 3D field
        cap = self.scene_numbers(cap)   # each weight is a number; bits -> precision
        cap = self.beat_snap(cap)       # snap to discrete levels + a shared scale
        cap = self.scene_compare(cap)   # FP32 / INT8 / INT4 side by side
        self.wipe()
        self.scene_mapping()            # the scale + zero-point recipe
        self.scene_payoff()             # smaller memory, faster inference
        self.play_outro()


# ---- thin per-scene classes + the whole film ------------------------------ #
class Intro(_QuantBase):
    def construct(self):
        self.play_intro()


class Network(_QuantBase):
    def construct(self):
        self.scene_network()
        self.wipe()


class Numbers(_QuantBase):
    def construct(self):
        self.go_3d()
        self.build_field(grow=False)
        self.scene_numbers()
        self.wipe()


class Snap(_QuantBase):
    def construct(self):
        self.go_3d()
        self.build_field()
        self.beat_snap()
        self.wipe()


class Compare(_QuantBase):
    def construct(self):
        self.go_3d()
        self.build_field(grow=False)
        self.scene_compare()
        self.wipe()


class Mapping(_QuantBase):
    def construct(self):
        self.scene_mapping()


class Payoff(_QuantBase):
    def construct(self):
        self.scene_payoff()


class Outro(_QuantBase):
    def construct(self):
        self.play_outro()


class Probe(_QuantBase):
    def construct(self):
        self.go_3d()
        self.build_field()
        centers, _ = quantize(FIELD, 8)
        self.morph_field(centers, level_colors(8), rt=2.0)
        self.beat(1.0)
        self.wipe()


class ModelQuantization(_QuantBase):
    def construct(self):
        self.play_all()

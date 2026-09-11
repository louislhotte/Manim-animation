"""What is a Tensor? — a short, house-style explainer.

The one idea, in N dimensions:

    rank 0   scalar   ()                a single number
    rank 1   vector   (d,)              a list of numbers along one axis
    rank 2   matrix   (r, c)            a grid: rows and columns
    rank 3   tensor   (c, h, w)         a stack of matrices (an RGB image)
    rank 4   tensor   (n, c, h, w)      a batch of those
    ...      tensor   (..., ..., ...)   just keep nesting

A tensor is an N-dimensional array of numbers.  "Rank" counts the axes; "shape"
sizes them.  The film walks scalar -> vector -> matrix -> higher dimensions, then
shows how deep learning is really just tensors flowing and changing shape.

All text is ``Text`` (Pango), no LaTeX.  Scenes render individually (``Scalar``,
``Vector``, ``Matrix``, ``Higher``, ``DataUse``, ``Compute``, ``Recap``) or as one
film (``WhatIsATensor``).

Env knobs:
    TN_QUICK=1   collapse every hold for a fast layout render
    TN_DELAY=<s> override the reading-rhythm multiplier
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

QUICK = os.environ.get("TN_QUICK") == "1"
# Reading rhythm. 2.3 so the matrices / shape tuples get real time to read.
DELAY = float(os.environ.get("TN_DELAY", 0.28 if QUICK else 2.3))
ANIM_SLOW = 1.0 if QUICK else 1.15
END_HOLD = 0.2 if QUICK else 2.2

# ---- palette (shared with the Transformer / KV-cache series) -------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
FAINT = "#3A4152"       # hairlines, faint structure
AX1 = "#5B8DEF"         # first axis  (columns / width)  blue
AX2 = "#2EC4B6"         # second axis (rows / height)    teal
AX3 = "#FFD166"         # third axis  (depth / channels) gold
GOLD = "#FFD166"        # accent
ACCENT = "#FFD166"
GOOD = "#3DD68C"        # green
BAD = "#FF5C5C"         # red / stop
RCOL = "#FF6B6B"        # colour channel R
GCOL = "#3DD68C"        # colour channel G
BCOL = "#5B8DEF"        # colour channel B
CODE_FS = 21
MONO = "Menlo"

FONT = "Helvetica Neue"

# --- crisp small text -------------------------------------------------------
# Pango mangles glyphs/spacing below ~20 pt (subscripts come out in a fallback
# font). Shadow Text so every call rasterises at a large base size and is scaled
# DOWN geometrically — same visual size, correct font, crisp at any size.
_BaseText = Text
_BaseText.set_default(font=FONT)
_TEXT_BASE = 60


def Text(text, font_size=48, **kw):  # noqa: F811 (intentional shadow)
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


# ---- small text helper: drop None kwargs Pango dislikes ------------------- #
def txt(s, fs=28, color=INK, font=None, slant=None, weight=None):
    kw = dict(font_size=fs, color=color)
    if font is not None:
        kw["font"] = font
    if slant is not None:
        kw["slant"] = slant
    if weight is not None:
        kw["weight"] = weight
    return Text(s, **kw)


def _safe_t2c(s, table):
    """Prune a t2c map so no key is a substring of another present key."""
    present = [k for k in table if k and k in s]
    keep = {}
    for k in present:
        if any(k != o and k in o for o in present):
            continue
        keep[k] = table[k]
    return keep


# ---- reusable glyphs ------------------------------------------------------ #
def chip(text, color, w=2.3, h=0.95, fs=26, fill=0.14, tcolor=None, radius=0.14):
    box = RoundedRectangle(width=w, height=h, corner_radius=radius,
                           stroke_color=color, stroke_width=3,
                           fill_color=color, fill_opacity=fill)
    label = Text(text, font_size=fs, color=tcolor or INK, line_spacing=0.8)
    if label.width > w - 0.3:
        label.scale((w - 0.3) / label.width)
    label.move_to(box)
    return VGroup(box, label)


def harrow(start, end, color=MUTED, sw=4, tip=0.22):
    return Arrow(start, end, buff=0.0, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.28, tip_length=tip)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.18, -0.18, 0], [0.18, 0.18, 0])
    b = Line([-0.18, 0.18, 0], [0.18, -0.18, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


# ---- the tensor primitive: a numbered cell -------------------------------- #
def cell(val=None, color=AX1, size=0.72, fill=0.16, fs=26, tcolor=INK,
         radius=0.1, sw=2.5, stroke=None):
    box = RoundedRectangle(width=size, height=size, corner_radius=radius,
                           stroke_color=stroke if stroke is not None else color,
                           stroke_width=sw, fill_color=color, fill_opacity=fill)
    g = VGroup(box)
    g.box = box
    g.label = None
    if val is not None:
        label = Text(str(val), font_size=fs, color=tcolor)
        maxw = size * 0.74
        if label.width > maxw:
            label.scale(maxw / label.width)
        label.move_to(box)
        g.add(label)
        g.label = label
    return g


def tensor_grid(values, color=AX1, size=0.72, buff=0.1, fs=22, fill=0.16,
                intensity=False, vmax=9.0, show_vals=True, tcolor=INK,
                stroke=None, sw=2.5):
    """A matrix of cells from a 2-D array. rows[i][j] indexes a cell VGroup."""
    row_groups = []
    for row in values:
        rcells = []
        for v in row:
            fo = float(v) / vmax if intensity else fill
            fo = max(0.0, min(1.0, fo))
            rcells.append(cell(v if show_vals else None, color=color, size=size,
                               fill=fo, fs=fs, tcolor=tcolor, stroke=stroke, sw=sw))
        row_groups.append(VGroup(*rcells).arrange(RIGHT, buff=buff))
    g = VGroup(*row_groups).arrange(DOWN, buff=buff)
    g.rows = list(g.submobjects)
    return g


# ---- shape / rank badge (top-right chrome) -------------------------------- #
_RANK_NAME = {0: "scalar", 1: "vector", 2: "matrix"}


def shape_tuple(dims):
    if len(dims) == 0:
        return "( )"
    if len(dims) == 1:
        return f"({dims[0]},)"
    return "(" + ", ".join(str(d) for d in dims) + ")"


def shape_badge(dims, color=GOLD):
    rk = len(dims)
    name = _RANK_NAME.get(rk, "tensor")
    shp = txt("shape  " + shape_tuple(dims), fs=23, color=INK, font=MONO)
    sub = txt(f"rank {rk}  ·  {name}", fs=20, color=color)
    inner = VGroup(shp, sub).arrange(DOWN, buff=0.16, aligned_edge=LEFT)
    bg = RoundedRectangle(width=inner.width + 0.5, height=inner.height + 0.42,
                          corner_radius=0.12, stroke_color=color, stroke_width=2,
                          fill_color="#141C29", fill_opacity=0.92).move_to(inner)
    g = VGroup(bg, inner)
    g.shp, g.sub = shp, sub
    return g


# ---- isometric projection for the "cube" scene ---------------------------- #
_EX = np.array([0.98, -0.30, 0.0])    # width  -> right, tilt down
_EY = np.array([-0.66, -0.42, 0.0])   # depth  -> back-left, down
_EZ = np.array([0.0, 1.0, 0.0])       # height -> up


def iso(p, center=ORIGIN, s=1.0):
    x, y, z = p
    return np.array(center, dtype=float) + s * (x * _EX + y * _EY + z * _EZ)


def _face_grid(O, U, V, n, color, sw, op):
    g = VGroup()
    for t in range(1, n):
        f = t / n
        g.add(Line(O + f * U, O + f * U + V))
        g.add(Line(O + f * V, O + f * V + U))
    return g.set_stroke(color=color, width=sw, opacity=op)


def iso_cube(ext=1.6, center=ORIGIN, edge=INK, sw=2.6, n=0,
             tints=(AX3, AX1, AX2), face_op=0.13, grid_op=0.5):
    """Isometric wireframe cube with 3 shaded visible faces and optional n×n×n
    face subdivisions.  Returns a VGroup; .C maps (i,j,k)->screen point."""
    C = {(i, j, k): iso((i, j, k), center, ext)
         for i in (0, 1) for j in (0, 1) for k in (0, 1)}
    top = Polygon(C[0, 0, 1], C[1, 0, 1], C[1, 1, 1], C[0, 1, 1],
                  stroke_width=0, fill_color=tints[0], fill_opacity=face_op)
    front = Polygon(C[0, 0, 0], C[1, 0, 0], C[1, 0, 1], C[0, 0, 1],
                    stroke_width=0, fill_color=tints[1], fill_opacity=face_op)
    right = Polygon(C[1, 0, 0], C[1, 1, 0], C[1, 1, 1], C[1, 0, 1],
                    stroke_width=0, fill_color=tints[2], fill_opacity=face_op)
    faces = VGroup(top, front, right)
    grids = VGroup()
    if n > 1:
        grids.add(_face_grid(C[0, 0, 1], C[1, 0, 1] - C[0, 0, 1],
                             C[0, 1, 1] - C[0, 0, 1], n, edge, 1.2, grid_op))
        grids.add(_face_grid(C[0, 0, 0], C[1, 0, 0] - C[0, 0, 0],
                             C[0, 0, 1] - C[0, 0, 0], n, edge, 1.2, grid_op))
        grids.add(_face_grid(C[1, 0, 0], C[1, 1, 0] - C[1, 0, 0],
                             C[1, 0, 1] - C[1, 0, 0], n, edge, 1.2, grid_op))
    edge_pairs = [((0, 0, 0), (1, 0, 0)), ((0, 0, 0), (0, 1, 0)),
                  ((0, 0, 0), (0, 0, 1)), ((1, 1, 1), (0, 1, 1)),
                  ((1, 1, 1), (1, 0, 1)), ((1, 1, 1), (1, 1, 0)),
                  ((1, 0, 0), (1, 1, 0)), ((1, 0, 0), (1, 0, 1)),
                  ((0, 1, 0), (1, 1, 0)), ((0, 1, 0), (0, 1, 1)),
                  ((0, 0, 1), (1, 0, 1)), ((0, 0, 1), (0, 1, 1))]
    edges = VGroup(*[Line(C[a], C[b], stroke_color=edge, stroke_width=sw)
                     for a, b in edge_pairs])
    g = VGroup(faces, grids, edges)
    g.C = C
    g.faces, g.edges = faces, edges
    return g


# ---- the 8x8 heart, reused for the grayscale image and the RGB image ------- #
HEART = [
    [1, 9, 9, 1, 1, 9, 9, 1],
    [9, 9, 9, 9, 9, 9, 9, 9],
    [9, 9, 9, 9, 9, 9, 9, 9],
    [9, 9, 9, 9, 9, 9, 9, 9],
    [1, 9, 9, 9, 9, 9, 9, 1],
    [1, 1, 9, 9, 9, 9, 1, 1],
    [1, 1, 1, 9, 9, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1],
]


def color_grid_from_rgb(R, G, B, size=0.42, buff=0.06, vmax=9.0, stroke=FAINT):
    """A grid whose every cell is filled with its own rgb colour."""
    row_groups = []
    for i in range(len(R)):
        rcells = []
        for j in range(len(R[0])):
            col = rgb_to_color([R[i][j] / vmax, G[i][j] / vmax, B[i][j] / vmax])
            rcells.append(cell(None, color=col, size=size, fill=1.0,
                               stroke=stroke, sw=1.0))
        row_groups.append(VGroup(*rcells).arrange(RIGHT, buff=buff))
    g = VGroup(*row_groups).arrange(DOWN, buff=buff)
    return g


# ---- a light coordinate frame for the vector-as-arrow scene --------------- #
def coord_frame(origin, xr=4, yr=3, unit=0.62, grid_color=FAINT, axis_color=MUTED):
    O = np.array(origin, dtype=float)
    grid = VGroup()
    for gx in range(0, xr + 1):
        grid.add(Line(O + RIGHT * gx * unit, O + RIGHT * gx * unit + UP * yr * unit))
    for gy in range(0, yr + 1):
        grid.add(Line(O + UP * gy * unit, O + UP * gy * unit + RIGHT * xr * unit))
    grid.set_stroke(color=grid_color, width=1.2, opacity=0.7)
    xax = harrow(O, O + RIGHT * (xr * unit + 0.32), color=axis_color, sw=3, tip=0.18)
    yax = harrow(O, O + UP * (yr * unit + 0.32), color=axis_color, sw=3, tip=0.18)
    frame = VGroup(grid, xax, yax)
    frame.O = O
    frame.pt = lambda x, y: O + RIGHT * x * unit + UP * y * unit
    return frame


# ========================================================================== #
class _TensorBase(Scene):
    def setup(self):
        self.camera.background_color = BG

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

    def wipe(self, rt=0.7):
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            super().play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    # ---- chrome ----------------------------------------------------------- #
    def section_header(self, label, color=ACCENT):
        t = Text(label, font_size=33, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=3)
        g = VGroup(t, line)
        self.play(FadeIn(g, shift=DOWN * 0.15), run_time=0.6)
        return g

    def say(self, s, color=INK, fs=26, italic=False, buff=0.45):
        m = txt(s, fs=fs, color=color, slant=ITALIC if italic else None)
        if m.width > 12.6:
            m.scale_to_fit_width(12.6)
        m.to_edge(DOWN, buff=buff)
        return m

    def show_say(self, s, **kw):
        m = self.say(s, **kw)
        self.play(FadeIn(m, shift=UP * 0.1), run_time=0.5)
        return m

    def replace_say(self, old, s, **kw):
        m = self.say(s, **kw)
        if old is not None:
            self.play(FadeOut(old, shift=UP * 0.1), FadeIn(m, shift=UP * 0.1), run_time=0.55)
        else:
            self.play(FadeIn(m, shift=UP * 0.1), run_time=0.5)
        return m

    # ---- shape badge helpers ---------------------------------------------- #
    def show_badge(self, dims, color=GOLD):
        b = shape_badge(dims, color=color).to_corner(UR, buff=0.5)
        self.play(FadeIn(b, shift=DOWN * 0.15), run_time=0.5)
        return b

    def update_badge(self, old, dims, color=GOLD):
        b = shape_badge(dims, color=color).to_corner(UR, buff=0.5)
        self.play(ReplacementTransform(old, b), run_time=0.6)
        return b

    # ---- house intro / outro cards ---------------------------------------- #
    def _rule_under(self, header, pad=1.0, color=GOLD, drop=0.45):
        return Line([header.get_left()[0] - pad, header.get_bottom()[1] - drop, 0],
                    [header.get_right()[0] + pad, header.get_bottom()[1] - drop, 0]
                    ).set_stroke(width=3, color=color)

    def play_intro(self):
        header = Text("What is a Tensor?", font_size=56, color=INK, weight="BOLD")
        header.set(width=min(9.6, header.width))
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=AX1)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        sub = Text("From a single number to the arrays behind deep learning",
                   font_size=30, color=MUTED)
        if sub.width > line.width:
            sub.scale_to_fit_width(line.width)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.card_wait(1.8)
        self.play(FadeOut(VGroup(header, writer, line)), run_time=1.0)
        self.card_wait(0.3)

    def play_hook(self):
        """Cold open: a number grows an axis at a time, the shape tuple ticking."""
        title = txt("everything below is one thing", fs=30, color=MUTED).to_edge(UP, buff=1.0)

        s = cell("7", color=AX1, size=0.9, fill=0.18, fs=40)
        row = tensor_grid([[3, 1, 4]], color=AX1, size=0.72, fs=26)
        grid = tensor_grid([[3, 1, 4], [1, 5, 9], [2, 6, 5]], color=AX2, size=0.72, fs=26)
        cube = iso_cube(ext=1.5, center=ORIGIN, edge=INK, n=3)
        stages = [s, row, grid, cube]
        for m in stages:
            m.move_to(ORIGIN)

        labels = ["( )", "(3,)", "(3, 3)", "(3, 3, 3)"]
        names = ["scalar", "vector", "matrix", "tensor"]

        def tag(i):
            t = txt(labels[i], fs=34, color=GOLD, font=MONO)
            nm = txt(names[i], fs=24, color=INK)
            g = VGroup(t, nm).arrange(DOWN, buff=0.18)
            g.to_edge(DOWN, buff=1.0)
            return g

        self.play(FadeIn(title, shift=DOWN * 0.15), run_time=0.6)
        cur = s
        curtag = tag(0)
        self.play(GrowFromCenter(cur), run_time=0.7)
        self.play(FadeIn(curtag, shift=UP * 0.1), run_time=0.5)
        self.card_wait(0.9)
        for i in range(1, 4):
            nxt = stages[i]
            ntag = tag(i)
            # move the shape and its tag together so the label never lags the glyph
            if i < 3:
                self.play(ReplacementTransform(cur, nxt),
                          ReplacementTransform(curtag, ntag), run_time=0.8)
            else:
                self.play(FadeOut(cur, scale=0.7), FadeIn(nxt, scale=0.9),
                          ReplacementTransform(curtag, ntag), run_time=0.9)
            cur, curtag = nxt, ntag
            self.card_wait(0.7)
        self.card_wait(0.8)
        self.play(FadeOut(VGroup(title, cur, curtag)), run_time=0.9)
        self.card_wait(0.2)

    def play_outro(self):
        self.card_wait(0.4)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=AX1)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = Text("Scalar, vector, matrix, tensor: one idea, N dimensions.",
                     font_size=24, color=MUTED)
        recap.next_to(writer, DOWN, buff=0.5)
        if recap.width > 12.4:
            recap.scale_to_fit_width(12.4)
        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap), run_time=0.8)
        self.card_wait(2.2)
        self.play(FadeOut(VGroup(header, line, writer, recap)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 — scalar (rank 0)
    # ====================================================================== #
    def scene_scalar(self):
        self.section_header("1 · Scalar")
        badge = self.show_badge([])

        big = Text("7", font_size=120, color=AX1, weight="BOLD").move_to(UP * 0.3)
        self.play(Write(big), run_time=0.9)
        cap = self.show_say("A scalar is a single number. Just magnitude, no direction.")
        self.beat(1.6)

        # tuck the number into one cell
        c = cell("7", color=AX1, size=1.2, fill=0.18, fs=64).move_to(UP * 0.3)
        self.play(ReplacementTransform(big, c), run_time=0.8)
        self.beat(0.8)

        # zero axes -> empty shape tuple
        note = txt("zero axes  →  shape ( )", fs=28, color=GOLD, font=MONO)
        note.next_to(c, DOWN, buff=0.5)
        self.play(FadeIn(note, shift=UP * 0.1), run_time=0.6)
        self.beat(1.2)

        cap = self.replace_say(cap, "A temperature. A price. A model's loss. Each is one scalar.")
        exs = VGroup(
            chip("loss = 0.03", GOLD, w=2.8, h=0.7, fs=22),
            chip("21 °C", AX2, w=2.0, h=0.7, fs=22),
            chip("$4.99", GOOD, w=2.0, h=0.7, fs=22),
        ).arrange(RIGHT, buff=0.4).next_to(note, DOWN, buff=0.7)
        self.play(LaggedStart(*[FadeIn(e, shift=UP * 0.15) for e in exs],
                              lag_ratio=0.3), run_time=1.2)
        self.beat(1.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — vector (rank 1)
    # ====================================================================== #
    def scene_vector(self):
        self.section_header("2 · Vector")
        badge = self.show_badge([5])

        cap = self.show_say("Line up numbers along one axis. That is a vector.")
        vals = [7, 2, 9, 4, 1]
        row = tensor_grid([vals], color=AX1, size=0.82, fs=30).move_to(UP * 1.1)
        self.play(LaggedStart(*[GrowFromCenter(c) for c in row.rows[0]],
                              lag_ratio=0.18), run_time=1.2)
        self.beat(1.0)

        # one axis arrow beneath the row
        axis = harrow(row.get_left() + DOWN * 0.75 + LEFT * 0.1,
                      row.get_right() + DOWN * 0.75 + RIGHT * 0.1,
                      color=AX1, sw=4)
        axlab = txt("axis 0", fs=22, color=AX1).next_to(axis, DOWN, buff=0.15)
        self.play(GrowArrow(axis), FadeIn(axlab), run_time=0.7)
        self.beat(0.8)

        # indexing v[2] = 9
        target = row.rows[0][2]
        box = SurroundingRectangle(target, color=GOLD, buff=0.06, corner_radius=0.08)
        idx = txt("v[2] = 9", fs=28, color=GOLD, font=MONO).next_to(row, UP, buff=0.55)
        self.play(Create(box), FadeIn(idx, shift=DOWN * 0.1), run_time=0.7)
        self.beat(1.4)
        self.play(FadeOut(idx), run_time=0.4)

        # a vector also has DIRECTION: draw [3,2] as an arrow in the plane
        cap = self.replace_say(cap, "With two numbers we can draw it: magnitude and direction.")
        self.play(FadeOut(box), FadeOut(axis), FadeOut(axlab),
                  row.animate.scale(0.72).to_corner(UL, buff=1.4), run_time=0.8)

        frame = coord_frame([-0.2, -2.6, 0], xr=4, yr=3, unit=0.62)
        self.play(Create(frame), run_time=1.0)
        v2 = tensor_grid([[3, 2]], color=GOLD, size=0.66, fs=26)
        v2.next_to(row, DOWN, buff=0.5).align_to(row, LEFT)
        vlab = txt("[3, 2]", fs=24, color=GOLD, font=MONO).next_to(v2, DOWN, buff=0.2)
        self.play(FadeIn(v2, shift=DOWN * 0.1), FadeIn(vlab), run_time=0.7)

        tip = frame.pt(3, 2)
        arrow = Arrow(frame.O, tip, buff=0.0, color=GOLD, stroke_width=6,
                      max_tip_length_to_length_ratio=0.16)
        dx = DashedLine(frame.O, frame.pt(3, 0), color=AX1, stroke_width=3)
        dy = DashedLine(frame.pt(3, 0), tip, color=AX2, stroke_width=3)
        xlb = txt("3", fs=22, color=AX1).next_to(dx, DOWN, buff=0.12)
        ylb = txt("2", fs=22, color=AX2).next_to(dy, RIGHT, buff=0.12)
        self.play(Create(dx), Create(dy), FadeIn(xlb), FadeIn(ylb), run_time=0.8)
        self.play(GrowArrow(arrow), run_time=0.7)
        self.beat(1.6)

        cap = self.replace_say(cap, "A word's embedding is just a vector: a point in meaning-space.")
        self.beat(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — matrix (rank 2)
    # ====================================================================== #
    def scene_matrix(self):
        self.section_header("3 · Matrix")
        badge = self.show_badge([3, 4])

        cap = self.show_say("Add a second axis: now we have rows and columns. A matrix.")
        M = [[3, 1, 4, 1], [5, 9, 2, 6], [8, 7, 1, 3]]
        grid = tensor_grid(M, color=AX2, size=0.82, fs=30).move_to(UP * 0.35 + RIGHT * 0.2)
        self.play(LaggedStart(*[GrowFromCenter(c) for r in grid.rows for c in r],
                              lag_ratio=0.04), run_time=1.4)
        self.beat(0.8)

        # two axes: columns (AX1) along the top, rows (AX2) down the left
        col_axis = harrow(grid.get_corner(UL) + UP * 0.28 + LEFT * 0.0,
                          grid.get_corner(UR) + UP * 0.28, color=AX1, sw=4)
        col_lab = txt("axis 1 · columns", fs=21, color=AX1).next_to(col_axis, UP, buff=0.12)
        row_axis = harrow(grid.get_corner(UL) + LEFT * 0.32,
                          grid.get_corner(DL) + LEFT * 0.32, color=AX2, sw=4)
        row_lab = txt("axis 0", fs=21, color=AX2).rotate(PI / 2).next_to(row_axis, LEFT, buff=0.12)
        self.play(GrowArrow(col_axis), FadeIn(col_lab), run_time=0.6)
        self.play(GrowArrow(row_axis), FadeIn(row_lab), run_time=0.6)
        self.beat(1.0)

        # index M[1][2] = 2  (row 1, column 2)
        target = grid.rows[1][2]
        box = SurroundingRectangle(target, color=GOLD, buff=0.06, corner_radius=0.08)
        idx = txt("M[1][2] = 2", fs=28, color=GOLD, font=MONO).next_to(grid, DOWN, buff=0.55)
        self.play(Create(box), FadeIn(idx, shift=UP * 0.1), run_time=0.7)
        self.beat(1.2)
        cap = self.replace_say(cap, "Two numbers, a row and a column, name every cell.")
        self.beat(1.4)
        self.play(FadeOut(VGroup(box, idx, col_axis, col_lab, row_axis, row_lab)), run_time=0.5)

        # an image IS a matrix: numbers -> brightness
        cap = self.replace_say(cap, "The same grid stores an image: each cell is a pixel's brightness.")
        self.play(grid.animate.scale(0.62).to_corner(UL, buff=1.5), run_time=0.7)
        badge = self.update_badge(badge, [8, 8])

        img = tensor_grid(HEART, color=AX1, size=0.5, buff=0.06, fs=17, fill=0.14,
                          stroke=FAINT, sw=1.4).move_to(RIGHT * 0.7 + DOWN * 0.15)
        self.play(FadeIn(img), run_time=0.8)
        self.beat(1.0)
        # each number -> brightness; the picture appears
        anims = []
        for i, rowv in enumerate(HEART):
            for j, v in enumerate(rowv):
                cg = img.rows[i][j]
                anims.append(cg.box.animate.set_fill(INK, opacity=max(0.04, v / 9.0))
                             .set_stroke(FAINT, width=1.0))
                if cg.label is not None:
                    anims.append(FadeOut(cg.label))
        self.play(*anims, run_time=1.7)
        legend = txt("0 = black      9 = white", fs=20, color=MUTED).next_to(img, DOWN, buff=0.3)
        self.play(FadeIn(legend), run_time=0.5)
        self.beat(1.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — higher dimensions (rank 3, then 4)
    # ====================================================================== #
    def scene_higher(self):
        self.section_header("4 · Higher dimensions")
        badge = self.show_badge([3, 3, 3])

        cap = self.show_say("Stack matrices into depth and you get a third axis.")
        cube = iso_cube(ext=1.9, center=LEFT * 2.3 + DOWN * 0.2, edge=INK, n=3)
        self.play(FadeIn(cube.faces), Create(cube.edges), run_time=1.2)
        self.play(FadeIn(cube[1]), run_time=0.6)   # face subdivision grids
        self.beat(0.8)

        # three axis arrows i, j, k
        C = cube.C
        ax_i = harrow(C[0, 0, 0], C[1, 0, 0] + _EX * 0.28 * 1.9, color=AX1, sw=4, tip=0.2)
        ax_k = harrow(C[0, 0, 0], C[0, 0, 1] + _EZ * 0.28 * 1.9, color=AX2, sw=4, tip=0.2)
        ax_j = harrow(C[0, 0, 0], C[0, 1, 0] + _EY * 0.28 * 1.9, color=AX3, sw=4, tip=0.2)
        li = txt("i", fs=24, color=AX1).next_to(ax_i.get_end(), DOWN, buff=0.08)
        lk = txt("j", fs=24, color=AX2).next_to(ax_k.get_end(), LEFT, buff=0.12)
        lj = txt("k", fs=24, color=AX3).next_to(ax_j.get_end(), LEFT, buff=0.1)
        self.play(GrowArrow(ax_i), GrowArrow(ax_k), GrowArrow(ax_j),
                  FadeIn(li), FadeIn(lk), FadeIn(lj), run_time=1.0)

        three = VGroup(
            txt("Two indices named a matrix cell.", fs=25, color=INK),
            txt("A rank-3 tensor needs three.", fs=25, color=GOLD),
        ).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        three.to_edge(RIGHT, buff=0.9).shift(UP * 0.4)
        self.play(FadeIn(three, shift=LEFT * 0.2), run_time=0.8)
        self.beat(2.0)

        self.play(FadeOut(VGroup(cube, ax_i, ax_j, ax_k, li, lj, lk, three)), run_time=0.7)

        # concrete: an RGB image = 3 stacked colour channels
        cap = self.replace_say(cap, "A colour photo is a rank-3 tensor: three stacked channels.")
        badge = self.update_badge(badge, [3, 8, 8])
        is_heart = [[HEART[i][j] >= 5 for j in range(8)] for i in range(8)]
        R = [[9 if is_heart[i][j] else 2 for j in range(8)] for i in range(8)]
        G = [[1 if is_heart[i][j] else 2 for j in range(8)] for i in range(8)]
        B = [[1 if is_heart[i][j] else 2 for j in range(8)] for i in range(8)]

        def chan(vals, col, label):
            g = tensor_grid(vals, color=col, size=0.34, buff=0.04, intensity=True,
                            show_vals=False, stroke=FAINT, sw=0.8)
            lab = txt(label, fs=22, color=col, weight="BOLD").next_to(g, UP, buff=0.12)
            return VGroup(g, lab)

        gap = np.array([0.62, 0.5, 0.0])
        base = LEFT * 3.1 + DOWN * 0.1
        chans = VGroup(chan(B, BCOL, "B"), chan(G, GCOL, "G"), chan(R, RCOL, "R"))
        for idx, cg in enumerate(chans):   # back (B) to front (R)
            cg.move_to(base + gap * (2 - idx))
        self.play(LaggedStart(FadeIn(chans[0], shift=gap * 0.4),
                              FadeIn(chans[1], shift=gap * 0.4),
                              FadeIn(chans[2], shift=gap * 0.4),
                              lag_ratio=0.4), run_time=1.4)
        self.beat(1.6)

        # combine into one colour image
        cap = self.replace_say(cap, "Read all three per pixel and the colour picture appears.")
        color_img = color_grid_from_rgb(R, G, B, size=0.42, buff=0.06).move_to(RIGHT * 3.3 + DOWN * 0.1)
        arrow = harrow(chans.get_right() + RIGHT * 0.1, color_img.get_left() + LEFT * 0.15,
                       color=MUTED, sw=4)
        hw = txt("height × width × 3", fs=22, color=MUTED).next_to(color_img, DOWN, buff=0.3)
        self.play(GrowArrow(arrow), run_time=0.5)
        self.play(FadeIn(color_img, scale=0.9), run_time=0.9)
        self.play(FadeIn(hw), run_time=0.5)
        self.beat(2.0)

        self.play(FadeOut(VGroup(chans, arrow, color_img, hw)), run_time=0.6)

        # rank 4: a batch of images
        cap = self.replace_say(cap, "Stack many images and the batch becomes a fourth axis.")
        badge = self.update_badge(badge, [6, 3, 8, 8])
        minis = VGroup(*[iso_cube(ext=0.72, edge=INK, sw=1.8, face_op=0.16,
                                  tints=(RCOL, GCOL, BCOL)) for _ in range(6)])
        for k, m in enumerate(minis):
            m.move_to(LEFT * 4.2 + RIGHT * 1.7 * k + UP * 0.35)
        self.play(LaggedStart(*[FadeIn(m, shift=UP * 0.15) for m in minis],
                              lag_ratio=0.15), run_time=1.3)
        brace = Line(minis.get_corner(DL) + DOWN * 0.25, minis.get_corner(DR) + DOWN * 0.25,
                     color=GOLD, stroke_width=3)
        blab = txt("batch of 6 images", fs=22, color=GOLD).next_to(brace, DOWN, buff=0.15)
        self.play(Create(brace), FadeIn(blab), run_time=0.7)
        self.beat(1.4)

        law = VGroup(
            txt("A tensor is an N-dimensional array of numbers.", fs=27, color=INK),
            Text("Rank counts the axes. Shape sizes them.", font_size=25, color=GOLD,
                 t2c={"Rank": AX1, "Shape": AX2}),
        ).arrange(DOWN, buff=0.22)
        law.next_to(blab, DOWN, buff=0.5)
        self.play(FadeIn(law, shift=UP * 0.15), run_time=0.9)
        self.beat(2.2)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — tensors are the data
    # ====================================================================== #
    def scene_data(self):
        self.section_header("5 · Tensors are the data")
        cap = self.show_say("Every input a model sees is a tensor. Only the rank changes.")

        # column headers
        hy = 2.35
        h_what = txt("what it is", fs=21, color=MUTED)
        h_ex = txt("in deep learning", fs=21, color=MUTED)
        h_shape = txt("shape", fs=21, color=MUTED)
        xg, xn, xe, xs = -5.2, -3.7, -0.7, 3.9
        h_what.move_to([xn, hy, 0])
        h_ex.move_to([xe, hy, 0])
        h_shape.move_to([xs, hy, 0])
        headers = VGroup(h_what, h_ex, h_shape)
        underline = Line([-6.2, hy - 0.28, 0], [5.7, hy - 0.28, 0]).set_stroke(FAINT, 2)
        self.play(FadeIn(headers), Create(underline), run_time=0.6)

        # mini glyphs
        def mini_scalar():
            return cell("7", color=AX1, size=0.42, fs=20)

        def mini_vector():
            return tensor_grid([[0, 0, 0, 0]], color=AX1, size=0.3, buff=0.04,
                               show_vals=False)

        def mini_matrix():
            return tensor_grid([[0] * 3 for _ in range(3)], color=AX2, size=0.26,
                               buff=0.04, show_vals=False)

        def mini_cube(tints=(AX3, AX1, AX2)):
            return iso_cube(ext=0.52, edge=INK, sw=1.6, face_op=0.18, tints=tints)

        def mini_batch():
            g = VGroup(*[iso_cube(ext=0.4, edge=INK, sw=1.3, face_op=0.18,
                                  tints=(RCOL, GCOL, BCOL)) for _ in range(3)])
            for k, m in enumerate(g):
                m.move_to(RIGHT * 0.42 * k)
            return g

        rows = [
            (mini_scalar(), "scalar", "a loss value", "( )"),
            (mini_vector(), "vector", "a word embedding", "(768,)"),
            (mini_matrix(), "matrix", "a grayscale image", "(28, 28)"),
            (mini_cube(), "rank 3", "an RGB image", "(3, 224, 224)"),
            (mini_batch(), "rank 4", "a batch of images", "(64, 3, 224, 224)"),
            (mini_batch(), "rank 5", "a batch of video", "(8, 16, 3, 224, 224)"),
        ]
        ys = np.linspace(1.55, -2.35, len(rows))
        row_mobs = []
        for (glyph, name, ex, shp), y in zip(rows, ys):
            glyph.scale_to_fit_height(min(0.55, glyph.height))
            glyph.move_to([xg, y, 0])
            nm = txt(name, fs=23, color=INK, weight="BOLD")
            nm.move_to([xn, y, 0])
            ext = txt(ex, fs=22, color=MUTED)
            if ext.width > 3.4:
                ext.scale_to_fit_width(3.4)
            ext.move_to([xe, y, 0])
            sh = txt(shp, fs=21, color=GOLD, font=MONO)
            if sh.width > 3.6:
                sh.scale_to_fit_width(3.6)
            sh.move_to([xs, y, 0])
            row_mobs.append(VGroup(glyph, nm, ext, sh))

        self.play(LaggedStart(*[FadeIn(r, shift=UP * 0.12) for r in row_mobs],
                              lag_ratio=0.22), run_time=2.0)
        self.beat(2.6)
        cap = self.replace_say(cap, "One idea covers all of it: numbers, in a shape.")
        self.beat(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 6 — tensors are the computation
    # ====================================================================== #
    def scene_compute(self):
        self.section_header("6 · Tensors are the computation")
        cap = self.show_say("A network is tensors flowing. The shape changes at every layer.")

        stages = [
            ("RGB image", "(1, 3, 224, 224)", AX1),
            ("Conv + Pool", "(1, 32, 112, 112)", AX2),
            ("Conv + Pool", "(1, 64, 56, 56)", AX2),
            ("Flatten", "(1, 200704)", AX3),
            ("Linear", "(1, 10)", GOLD),
        ]
        nodes = VGroup()
        shapes = VGroup()
        for name, shp, col in stages:
            box = chip(name, col, w=2.15, h=0.82, fs=21)
            sh = txt(shp, fs=18, color=col, font=MONO)
            nodes.add(box)
            shapes.add(sh)
        nodes.arrange(RIGHT, buff=0.62).move_to(UP * 1.15)
        for box, sh in zip(nodes, shapes):
            sh.next_to(box, DOWN, buff=0.18)

        arrows = VGroup(*[harrow(nodes[i].get_right(), nodes[i + 1].get_left(),
                                 color=MUTED, sw=3.5, tip=0.16)
                          for i in range(len(nodes) - 1)])
        flow = VGroup(nodes, shapes, arrows)
        if flow.width > 13.4:
            flow.scale_to_fit_width(13.4)

        self.play(FadeIn(nodes[0]), FadeIn(shapes[0]), run_time=0.6)
        for i in range(1, len(nodes)):
            self.play(GrowArrow(arrows[i - 1]), run_time=0.4)
            self.play(FadeIn(nodes[i], shift=RIGHT * 0.1), FadeIn(shapes[i]), run_time=0.5)
            self.beat(0.5)
        self.beat(1.4)

        # the matmul shape rule on the Linear step
        cap = self.replace_say(cap, "Layers are matrix multiplies, and the inner dimensions must match.")
        # one Text (not arranged pieces) so spacing survives Pango's space-trimming;
        # t2c colours both shared inner-dim "k"s gold.
        rule = Text("(1, k) · (k, 10) = (1, 10)", font_size=30, color=INK, font=MONO,
                    t2c={"k": GOLD})
        rbox = RoundedRectangle(width=rule.width + 0.7, height=rule.height + 0.5,
                                corner_radius=0.12, stroke_color=GOLD, stroke_width=2,
                                fill_color="#141C29", fill_opacity=0.9).move_to(rule)
        ruleg = VGroup(rbox, rule).move_to(DOWN * 0.7)
        self.play(FadeIn(ruleg, shift=UP * 0.15), run_time=0.8)
        match = txt("the shared k must line up, or the shapes do not fit", fs=21,
                    color=GOLD).next_to(ruleg, DOWN, buff=0.35)
        self.play(FadeIn(match), run_time=0.5)
        self.beat(2.0)

        # softmax -> probabilities.  Fade the whole pipeline so the bars own the
        # frame (it had its two beats above) and nothing collides.
        cap = self.replace_say(cap, "The last 10 numbers become probabilities. A prediction.")
        self.play(FadeOut(ruleg), FadeOut(match), FadeOut(flow), run_time=0.6)
        probs = [0.02, 0.03, 0.86, 0.02, 0.03, 0.01, 0.01, 0.005, 0.005, 0.01]
        bars = VGroup()
        for i, p in enumerate(probs):
            h = 0.15 + p * 2.4
            b = Rectangle(width=0.5, height=h, stroke_width=0,
                          fill_color=GOLD if i == 2 else AX1,
                          fill_opacity=0.95 if i == 2 else 0.5)
            bars.add(b)
        bars.arrange(RIGHT, buff=0.2, aligned_edge=DOWN).move_to(DOWN * 0.35)
        baseline = Line(bars.get_corner(DL) + LEFT * 0.15, bars.get_corner(DR) + RIGHT * 0.15,
                        color=FAINT, stroke_width=2)
        logit = txt("(1, 10)  →  softmax", fs=22, color=MUTED).next_to(bars, UP, buff=0.9)
        win = txt("“cat”  0.86", fs=24, color=GOLD, weight="BOLD").next_to(bars[2], UP, buff=0.18)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars],
                              lag_ratio=0.06), Create(baseline), run_time=1.1)
        self.play(FadeIn(win, shift=UP * 0.1), FadeIn(logit), run_time=0.6)
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Recap — the takeaway card
    # ====================================================================== #
    def scene_recap(self):
        title = Text("One idea, N dimensions", font_size=40, color=INK, weight="BOLD")
        title.to_edge(UP, buff=1.1)
        line = self._rule_under(title, pad=0.7, drop=0.4)
        self.play(Write(title), Create(line), run_time=1.1)

        def mini_scalar():
            return cell("7", color=AX1, size=0.5, fs=22)

        def mini_vector():
            return tensor_grid([[0, 0, 0]], color=AX1, size=0.34, buff=0.05, show_vals=False)

        def mini_matrix():
            return tensor_grid([[0] * 3 for _ in range(3)], color=AX2, size=0.3,
                               buff=0.05, show_vals=False)

        def mini_cube():
            return iso_cube(ext=0.6, edge=INK, sw=1.7, face_op=0.18)

        rows = [
            (mini_scalar(), "scalar", "( )"),
            (mini_vector(), "vector", "(d,)"),
            (mini_matrix(), "matrix", "(r, c)"),
            (mini_cube(), "tensor", "(a, b, c, ...)"),
        ]
        xg, xn, xs = -3.4, -1.6, 2.2
        ys = np.linspace(1.0, -1.7, len(rows))
        row_mobs = []
        for (glyph, name, shp), y in zip(rows, ys):
            glyph.scale_to_fit_height(min(0.6, glyph.height)).move_to([xg, y, 0])
            nm = txt(name, fs=26, color=INK, weight="BOLD").move_to([xn, y, 0])
            sh = txt(shp, fs=24, color=GOLD, font=MONO).move_to([xs, y, 0])
            row_mobs.append(VGroup(glyph, nm, sh))
        self.play(LaggedStart(*[FadeIn(r, shift=UP * 0.12) for r in row_mobs],
                              lag_ratio=0.25), run_time=1.6)
        self.beat(2.0)

        punch = Text("Every model is tensors in, tensors out.", font_size=27, color=GOLD,
                     t2c={"tensors in": AX1, "tensors out": AX2})
        punch.next_to(row_mobs[-1], DOWN, buff=0.7)
        if punch.width > 12.4:
            punch.scale_to_fit_width(12.4)
        self.play(FadeIn(punch, shift=UP * 0.15), run_time=0.9)
        self.beat(2.2)
        self.settle()
        self.wipe()

    # ====================================================================== #
    def play_all(self):
        self.play_hook()
        self.play_intro()
        self.scene_scalar()
        self.scene_vector()
        self.scene_matrix()
        self.scene_higher()
        self.scene_data()
        self.scene_compute()
        self.scene_recap()
        self.play_outro()


# ---- thin per-scene classes + the whole film ------------------------------ #
class Hook(_TensorBase):
    def construct(self):
        self.play_hook()


class Intro(_TensorBase):
    def construct(self):
        self.play_intro()


class Scalar(_TensorBase):
    def construct(self):
        self.scene_scalar()


class Vector(_TensorBase):
    def construct(self):
        self.scene_vector()


class Matrix(_TensorBase):
    def construct(self):
        self.scene_matrix()


class Higher(_TensorBase):
    def construct(self):
        self.scene_higher()


class DataUse(_TensorBase):
    def construct(self):
        self.scene_data()


class Compute(_TensorBase):
    def construct(self):
        self.scene_compute()


class Recap(_TensorBase):
    def construct(self):
        self.scene_recap()


class Outro(_TensorBase):
    def construct(self):
        self.play_outro()


class WhatIsATensor(_TensorBase):
    def construct(self):
        self.play_all()


# a tiny glyph probe (render once to confirm symbols are not tofu)
class Probe(_TensorBase):
    def construct(self):
        rows = [
            "( )   (3,)   (3, 4)   (3, 3, 3)   × · →",
            "v[2]=9   M[1][2]=2   height × width × 3",
            "shape (64, 3, 224, 224)   rank 4",
        ]
        g = VGroup(*[Text(r, font_size=34, color=INK) for r in rows]).arrange(DOWN, buff=0.6)
        self.add(g)
        self.wait(0.2)

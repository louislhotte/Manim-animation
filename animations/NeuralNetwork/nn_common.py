"""Shared foundation for the "How a Neural Network Learns" explainer.

One dark, house-style film in five ~2-minute scenes, teaching supervised image
classification end-to-end on a real (tiny) task: telling a **car** from a
**plane** from a **ship**. Every number the film shows is baked by
``generate_assets.py`` into ``assets/nn_learn.npz`` (real dataset, real numpy
MLPs, real training curves and accuracies).

This module holds everything the five scene files share, so they stay visually
consistent and can be built independently:

    * the crisp-``Text`` shim + palette + fonts (house style),
    * the class colours + hand-drawn car / plane / ship glyphs,
    * pixel-image helpers (show a 12x12 sample; flatten to a vector),
    * ``build_network(...)`` — a reusable feed-forward diagram with forward /
      backward "signal flow" animations and weight re-styling,
    * ``DATA`` — the loaded npz (accuracies, curves, confusion, demos, …),
    * ``_NNBase`` — the Scene base class: timing (``beat`` / ``settle`` /
      ``wipe``), ``section_header``, running ``say`` caption, and the house
      intro / outro cards.

Scenes live in ``scene1_task.py`` … ``scene5_verdict.py`` as
``build_<name>(scene)`` functions (drawing on a passed-in scene, ending with
``scene.wipe()``) plus a thin renderable ``Scene`` subclass; ``neural_network.py``
runs them back-to-back as the full film.
"""
from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from manim import *

# --- crisp text (shared house fix, MANDATORY) ------------------------------ #
# Manim's ``Text`` quantises glyph positions badly below ~20 pt. Render every
# glyph at a large base size and scale the mobject *down* — spacing stays crisp,
# and super/subscripts never fall back to a different font.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


# --- pacing ---------------------------------------------------------------- #
QUICK = os.environ.get("NN_QUICK") == "1"
# self.beat(t) == wait(t * DELAY): the reading rhythm. Animations keep explicit
# run_times (not scaled) so the film stays dynamic. Each scene ends on a settle.
# Paced generously (a dense technical caption wants 3-4 s) so the ~2-min-per-scene
# target is met with reading time, not dead air.
DELAY = float(os.environ.get("NN_DELAY", 0.25 if QUICK else 2.4))
READ = float(os.environ.get("NN_READ", 0.3 if QUICK else 3.1))   # hold after a caption
END_HOLD = 0.2 if QUICK else 3.0

# ---- palette (dark house style) ------------------------------------------- #
BG = "#0E1117"       # dark slate background
PANEL = "#151A23"    # panel fill
INK = "#F5F3EF"      # warm white text
MUTED = "#8A93A6"    # secondary text / axes / edges
FAINT = "#2A3140"    # gridlines / faint wires
GOLD = "#FFD166"     # accent / rules / the model
GOOD = "#3DD68C"     # correct / pass (green)
BAD = "#FF5C5C"      # wrong / miss (red)
WARN = "#FF8C42"     # loss / error signal (orange)

# the three classes — one colour each, the film's through-line
CAR_C = "#5B8DEF"    # car   (blue)
PLANE_C = "#C792EA"  # plane (violet)
SHIP_C = "#2EC4B6"   # ship  (teal)
CLASS_COLORS = [CAR_C, PLANE_C, SHIP_C]

WPOS = "#5B8DEF"     # positive weight (blue)
WNEG = "#FF7A7A"     # negative weight (red)

MONO = "Menlo"
FONT = "Helvetica Neue"
_BaseText.set_default(font=FONT)


# ========================================================================== #
# data
# ========================================================================== #
ROOT = Path(__file__).resolve().parent
_NPZ = ROOT / "assets" / "nn_learn.npz"


def load_data():
    d = np.load(_NPZ, allow_pickle=True)
    ns = SimpleNamespace(**{k: d[k] for k in d.files})
    ns.classes = [str(c) for c in ns.classes]
    return ns


DATA = load_data() if _NPZ.exists() else None


def class_color(i):
    return CLASS_COLORS[int(i)]


def class_name(i):
    return ("car", "plane", "ship")[int(i)]


# ========================================================================== #
# small reusable pieces
# ========================================================================== #
def txt(text, fs=24, color=INK, weight="NORMAL", slant=None):
    kw = {"font_size": fs, "color": color, "weight": weight}
    if slant:
        kw["slant"] = slant
    return Text(text, **kw)


def mono(text, fs=20, color=INK):
    return Text(text, font_size=fs, color=color, font=MONO)


def chip(text, color, fs=22, fill=0.14, w=None, h=0.6, tcolor=None, weight="NORMAL", radius=0.12):
    label = txt(text, fs=fs, color=tcolor or INK, weight=weight)
    width = (label.width + 0.5) if w is None else w
    if label.width > width - 0.3:
        label.scale((width - 0.3) / label.width)
    box = RoundedRectangle(width=width, height=h, corner_radius=radius,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=fill)
    label.move_to(box)
    g = VGroup(box, label)
    g.box = box
    g.label = label
    return g


def pill(text, color, fs=22, fill=0.16, weight="BOLD"):
    t = txt(text, fs=fs, color=color, weight=weight)
    box = RoundedRectangle(width=t.width + 0.5, height=t.height + 0.3,
                           corner_radius=0.14, stroke_color=color, stroke_width=2,
                           fill_color=color, fill_opacity=fill)
    box.move_to(t)
    return VGroup(box, t)


def plate(mob, pad_x=0.16, pad_y=0.1, op=0.75):
    bg = RoundedRectangle(width=mob.width + 2 * pad_x, height=mob.height + 2 * pad_y,
                          corner_radius=0.09, stroke_width=0,
                          fill_color=BG, fill_opacity=op).move_to(mob)
    return VGroup(bg, mob)


def arr(a, b, color=MUTED, sw=4, buff=0.14, tip=0.2):
    return Arrow(a, b, buff=buff, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.32, tip_length=tip)


def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])])
    return v.set_stroke(color=color, width=sw).scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.18, -0.18, 0], [0.18, 0.18, 0])
    b = Line([-0.18, 0.18, 0], [0.18, -0.18, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


def check_badge(color=GOOD, r=0.22):
    c = Circle(radius=r, stroke_color=color, stroke_width=3, fill_color=color, fill_opacity=0.18)
    return VGroup(c, make_tick(color=color, sw=5, scale=0.9 * r / 0.22).move_to(c))


def cross_badge(color=BAD, r=0.22):
    c = Circle(radius=r, stroke_color=color, stroke_width=3, fill_color=color, fill_opacity=0.18)
    return VGroup(c, make_cross(color=color, sw=5, scale=0.8 * r / 0.22).move_to(c))


def prob_bars(probs, names=("car", "plane", "ship"), colors=None, unit=2.6, fs=20,
              gap=0.5, bar_h=0.32, show_val=True):
    """Right-of-label horizontal probability bars, coloured per class."""
    colors = colors or CLASS_COLORS
    grp = VGroup()
    rows = []
    labw = max(txt(n, fs=fs).width for n in names) + 0.15
    for i, (n, p) in enumerate(zip(names, probs)):
        y = -i * gap
        lab = txt(n, fs=fs, color=INK)
        lab.move_to([-labw + lab.width / 2, y, 0]).align_to([-labw, y, 0], LEFT)
        bw = max(0.04, unit * float(p))
        bar = Rectangle(width=bw, height=bar_h, stroke_width=0,
                        fill_color=colors[i], fill_opacity=0.9)
        bar.move_to([0.15 + bw / 2, y, 0])
        row = VGroup(lab, bar)
        if show_val:
            val = txt(f"{float(p):.2f}", fs=fs - 4, color=MUTED).next_to(bar, RIGHT, buff=0.14)
            row.add(val)
        row.bar = bar
        row.lab = lab
        rows.append(row)
        grp.add(row)
    grp.rows = rows
    return grp


# ========================================================================== #
# class glyphs — hand-drawn, no assets. Each ~1 unit tall, centred on origin.
# ========================================================================== #
def _poly(pts, color, fill=0.18, sw=3):
    return Polygon(*[np.array([x, y, 0]) for x, y in pts],
                   stroke_color=color, stroke_width=sw, fill_color=color, fill_opacity=fill)


def car_glyph(color=CAR_C, s=1.0):
    body = RoundedRectangle(width=1.5, height=0.5, corner_radius=0.16,
                            stroke_color=color, stroke_width=3.2,
                            fill_color=color, fill_opacity=0.16)
    body.shift(UP * 0.05)
    cabin = _poly([(-0.5, 0.28), (0.18, 0.28), (0.34, 0.62), (-0.34, 0.62)], color, sw=3.2)
    win = _poly([(-0.34, 0.32), (0.04, 0.32), (0.14, 0.56), (-0.24, 0.56)], color, fill=0.32)
    wheels = VGroup()
    for wx in (-0.45, 0.45):
        outer = Circle(radius=0.2, stroke_color=color, stroke_width=3, fill_color=BG, fill_opacity=1)
        inner = Circle(radius=0.09, stroke_width=0, fill_color=color, fill_opacity=0.7)
        wheels.add(VGroup(outer, inner).move_to([wx, -0.22, 0]))
    g = VGroup(body, cabin, win, wheels)
    return g.scale(s)


def plane_glyph(color=PLANE_C, s=1.0):
    fuse = RoundedRectangle(width=1.5, height=0.28, corner_radius=0.14,
                            stroke_color=color, stroke_width=3.2,
                            fill_color=color, fill_opacity=0.16)
    nose = _poly([(0.74, 0.14), (0.74, -0.14), (1.02, 0.0)], color)
    wing = _poly([(0.12, 0.02), (-0.5, 0.66), (-0.24, 0.66), (0.34, 0.02)], color)
    wing2 = _poly([(0.12, -0.02), (-0.5, -0.66), (-0.24, -0.66), (0.34, -0.02)], color)
    tail = _poly([(-0.62, 0.06), (-0.86, 0.44), (-0.66, 0.44), (-0.44, 0.06)], color)
    win = VGroup(*[Dot(radius=0.045, color=color).set_opacity(0.7).move_to([x, 0.0, 0])
                   for x in (-0.1, 0.06, 0.22, 0.38)])
    g = VGroup(wing, wing2, fuse, nose, tail, win)
    return g.scale(s)


def ship_glyph(color=SHIP_C, s=1.0):
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
        [np.array([x, -0.5 + 0.05 * ((i) % 2), 0]) for i, x in enumerate(np.linspace(-0.8, 0.8, 9))])
    g = VGroup(hull, deck, funnel, mast, flag, wave)
    return g.scale(s)


CLASS_GLYPHS = {"car": car_glyph, "plane": plane_glyph, "ship": ship_glyph}


def class_glyph(i_or_name, s=1.0, color=None):
    name = i_or_name if isinstance(i_or_name, str) else class_name(i_or_name)
    col = color or CLASS_COLORS[("car", "plane", "ship").index(name)]
    return CLASS_GLYPHS[name](color=col, s=s)


def labeled_example(name, s=0.62, card_w=1.9, card_h=1.9, show_label=True):
    """A framed dataset example: the class glyph in a card + a coloured label tag."""
    col = CLASS_COLORS[("car", "plane", "ship").index(name)]
    card = RoundedRectangle(width=card_w, height=card_h, corner_radius=0.12,
                            stroke_color=MUTED, stroke_width=2, fill_color=PANEL, fill_opacity=0.6)
    g = class_glyph(name, s=s).move_to(card).shift(UP * (0.16 if show_label else 0))
    grp = VGroup(card, g)
    if show_label:
        tag = chip(name, col, fs=17, h=0.36, w=card_w - 0.5)
        tag.next_to(card.get_bottom(), UP, buff=0.12)
        grp.add(tag)
        grp.tag = tag
    grp.card = card
    grp.glyph = g
    return grp


# ========================================================================== #
# pixel image (what the network actually sees)
# ========================================================================== #
def pixel_grid(arr, cell=0.2, stroke=0.4, color=INK, frame=True, frame_c=MUTED):
    """A grayscale square grid from a HxW float array in [0,1]."""
    arr = np.asarray(arr)
    H, W = arr.shape
    cells = VGroup()
    for r in range(H):
        for c in range(W):
            sq = Square(cell, stroke_width=stroke, stroke_color=BG)
            sq.set_fill(color, opacity=float(np.clip(arr[r, c], 0, 1)) * 0.95 + 0.03)
            sq.move_to([c * cell, -r * cell, 0])
            cells.add(sq)
    cells.move_to(ORIGIN)
    if frame:
        box = SurroundingRectangle(cells, buff=0.02, color=frame_c, corner_radius=0.03)
        box.set_stroke(width=2)
        g = VGroup(cells, box)
        g.cells = cells
        g.box = box
        return g
    cells.cells = cells
    return cells


def vec_column(vals, cw=0.16, color=INK, stroke=FAINT, cap=None):
    """A tall vertical vector of value-shaded cells (optionally capped with …)."""
    vals = list(vals)
    shown = vals if cap is None else vals[:cap]
    col = VGroup()
    for v in shown:
        s = Square(cw, stroke_width=0.8, stroke_color=stroke)
        s.set_fill(color, opacity=float(np.clip(v, 0, 1)) * 0.9 + 0.05)
        col.add(s)
    col.arrange(DOWN, buff=0.015)
    return col


# ========================================================================== #
# the network diagram
# ========================================================================== #
class Network(VGroup):
    """A drawn feed-forward net.

    Attributes
    ----------
    sizes   : true layer sizes (e.g. [144, 8, 3]) — for labels / counts
    shown   : nodes actually drawn per layer
    layers  : list[VGroup[Dot]]  drawn nodes, input→output
    ell     : list[VGroup]       ellipsis dots per layer (may be empty groups)
    gaps    : list[VGroup[Line]] gaps[i] holds every edge from layer i → i+1
    edges   : VGroup             all edges, flattened
    nodes   : VGroup             all drawn nodes, flattened
    """

    def node(self, li, ni):
        return self.layers[li][ni]

    def style_edges(self, seed=None, settled=False, base_op=0.5):
        """Colour/thicken edges. random init = faint & uniform; settled = varied
        signed weights (blue +, red −). Mutates in place; returns self."""
        g = np.random.default_rng(seed if seed is not None else 0)
        for e in self.edges:
            if settled:
                w = g.normal(0, 1)
                e.set_stroke(color=WPOS if w >= 0 else WNEG,
                             width=0.6 + 2.6 * min(abs(w), 2.2) / 2.2,
                             opacity=0.85)
            else:
                e.set_stroke(color=MUTED, width=1.4, opacity=base_op)
        return self


def build_network(sizes, shown=None, width=6.2, height=4.3, node_r=0.11,
                  out_colors=None, hidden_color=INK, in_color=CAR_C,
                  edge_op=0.5, edge_cap=None):
    """A feed-forward diagram. ``sizes`` are the *true* sizes (for labels); big
    layers are drawn with a few nodes + an ellipsis. Returns a :class:`Network`.

    shown  : nodes drawn per layer (default: capped, with ellipsis when < size).
    """
    L = len(sizes)
    if shown is None:
        caps = []
        for i, s in enumerate(sizes):
            if i == L - 1:
                caps.append(s)                     # always draw all outputs
            elif i == 0:
                caps.append(min(s, 6))
            else:
                caps.append(min(s, 7))
        shown = caps
    xs = np.linspace(-width / 2, width / 2, L)

    layers, ell = [], []
    for i, (n_true, n_show) in enumerate(zip(sizes, shown)):
        ys = np.linspace(height / 2, -height / 2, max(n_show, 1))
        if n_show == 1:
            ys = np.array([0.0])
        col = (out_colors or CLASS_COLORS) if i == L - 1 else None
        nodes = VGroup()
        for j in range(n_show):
            c = (col[j % len(col)] if i == L - 1 else
                 (in_color if i == 0 else hidden_color))
            d = Dot([xs[i], ys[j], 0], radius=node_r, color=c)
            d.set_fill(c, opacity=0.9).set_stroke(BG, width=1.2)
            nodes.add(d)
        layers.append(nodes)
        # ellipsis if we hid nodes
        e = VGroup()
        if n_show < n_true:
            for k in range(3):
                e.add(Dot([xs[i], -height / 2 - 0.22 - 0.16 * k, 0], radius=0.028, color=MUTED))
        ell.append(e)

    gaps = VGroup()
    all_edges = VGroup()
    for i in range(L - 1):
        gap = VGroup()
        pairs = [(a, b) for a in layers[i] for b in layers[i + 1]]
        if edge_cap is not None and len(pairs) > edge_cap:
            pairs = pairs[:edge_cap]
        for a, b in pairs:
            ln = Line(a.get_center(), b.get_center(), stroke_color=MUTED,
                      stroke_width=1.4, stroke_opacity=edge_op)
            ln.set_z_index(-1)
            gap.add(ln)
            all_edges.add(ln)
        gaps.add(gap)

    net = Network()
    net.sizes = list(sizes)
    net.shown = list(shown)
    net.layers = layers
    net.ell = ell
    net.gaps = list(gaps)
    net.edges = all_edges
    net.nodes = VGroup(*[d for lyr in layers for d in lyr])
    net.add(all_edges, *layers, *[e for e in ell if len(e)])
    return net


# ========================================================================== #
class NNBase(Scene):
    def setup(self):
        self.camera.background_color = BG
        self._cap = None

    # ---- timing ----------------------------------------------------------- #
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def read(self, t=1.0):
        self.wait(t * READ)

    def card_wait(self, t=1.0):
        self.wait(t * (0.25 if QUICK else 1.0))

    def settle(self):
        self.wait(END_HOLD)

    def wipe(self, rt=0.6):
        for m in self.mobjects:
            m.clear_updaters()
        self._cap = None
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    # ---- section header (top-left tag + title + rule) --------------------- #
    def section_header(self, part, label, color=GOLD):
        tag = txt(part, fs=20, color=color, weight="BOLD")
        tagbox = RoundedRectangle(width=tag.width + 0.4, height=0.44, corner_radius=0.1,
                                  stroke_color=color, stroke_width=2,
                                  fill_color=color, fill_opacity=0.12)
        tag.move_to(tagbox)
        title = txt(label, fs=33, color=INK, weight="BOLD")
        head = VGroup(VGroup(tagbox, tag), title).arrange(RIGHT, buff=0.3)
        head.to_corner(UL, buff=0.5)
        line = Line(head.get_left(), head.get_right()).next_to(head, DOWN, buff=0.13)
        line.set_stroke(color=color, width=3)
        g = VGroup(head, line)
        g.title = title
        return g

    # ---- running bottom caption ("say") ----------------------------------- #
    def say(self, text, color=INK, fs=27, weight="NORMAL", hold=None, rt=0.7,
            edge=0.42, keep=False):
        """Land a one-line caption at the bottom; replaces the previous one.

        Clamps its own width so it never runs off-screen. ``hold`` (in READ
        units) defaults to a content-scaled pause; pass ``keep=True`` to leave
        it on screen (else the caller/next ``say`` removes it)."""
        m = txt(text, fs=fs, color=color, weight=weight)
        maxw = 2 * config.frame_x_radius - 1.1
        if m.width > maxw:
            m.scale(maxw / m.width)
        m.to_edge(DOWN, buff=edge)
        if self._cap is not None:
            self.play(FadeOut(self._cap, shift=DOWN * 0.12),
                      FadeIn(m, shift=UP * 0.12), run_time=rt)
        else:
            self.play(FadeIn(m, shift=UP * 0.12), run_time=rt)
        self._cap = m
        if hold is None:
            hold = 0.7 + 0.02 * len(text)
        self.read(hold)
        if keep:
            self._cap = None
        return m

    def clear_cap(self, rt=0.4):
        if self._cap is not None:
            self.play(FadeOut(self._cap), run_time=rt)
            self._cap = None

    # ---- signal flow along the net (forward / backprop) ------------------- #
    def flow(self, net, color=INK, reverse=False, rt=0.6, lag=0.55,
             node_color=None, time_width=0.55):
        """Animate a signal travelling through ``net`` gap-by-gap.

        forward (reverse=False): input→output. reverse=True: output→input, for
        backprop (use color=WARN/BAD). Also pulses the destination nodes."""
        gap_order = list(range(len(net.gaps)))
        if reverse:
            gap_order = gap_order[::-1]
        seq = []
        for gi in gap_order:
            flashes = []
            for e in net.gaps[gi]:
                seg = e.copy().set_stroke(color, width=4.2, opacity=1)
                if reverse:
                    seg.reverse_points()
                flashes.append(ShowPassingFlash(seg, time_width=time_width, run_time=rt))
            dest = net.layers[gi + (0 if reverse else 1)]
            pulse = AnimationGroup(*[Indicate(d, color=node_color or color,
                                              scale_factor=1.5) for d in dest],
                                   lag_ratio=0.02, run_time=rt)
            seq.append(AnimationGroup(*flashes, pulse))
        self.play(LaggedStart(*seq, lag_ratio=lag))

    # ---- house-style bookend cards ---------------------------------------- #
    def play_intro(self, title="How a Neural Network Learns",
                   subtitle="Teaching a machine to tell a car from a plane from a ship"):
        header = txt(title, fs=52, color=INK, weight="BOLD")
        header.set(width=min(11.4, header.width)).shift(UP * 0.15)
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.4, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.4, 0],
        ).set_stroke(width=3, color=GOLD)
        sub = txt(subtitle, fs=26, color=MUTED)
        if sub.width > 11.6:
            sub.scale(11.6 / sub.width)
        sub.next_to(line, DOWN, buff=0.42)
        writer = txt("Created by Ptolémé", fs=27, color=CAR_C)
        writer.next_to(sub, DOWN, buff=0.42)

        # a trio of class glyphs drifting above the title
        trio = VGroup(car_glyph(s=0.7), plane_glyph(s=0.7), ship_glyph(s=0.7))
        trio.arrange(RIGHT, buff=1.1).next_to(header, UP, buff=0.85)

        self.play(LaggedStart(*[FadeIn(g, shift=UP * 0.2) for g in trio],
                              lag_ratio=0.25, run_time=1.4))
        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.4)
        self.play(FadeIn(sub), run_time=0.8)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.card_wait(1.9)
        self.play(FadeOut(VGroup(header, writer, line, sub, trio)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self, recap=None):
        self.card_wait(0.4)
        header = txt("Thank you for watching!", fs=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        writer = txt("Created by Ptolémé", fs=28, color=CAR_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        grp = VGroup(header, line, writer)
        if recap:
            r = txt(recap, fs=24, color=MUTED, slant="ITALIC")
            if r.width > 11.6:
                r.scale(11.6 / r.width)
            r.next_to(writer, DOWN, buff=0.5)
            grp.add(r)
        self.play(Write(header), Create(line), run_time=1.4)
        self.card_wait(0.6)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        if recap:
            self.play(FadeIn(grp[-1]), run_time=0.7)
        self.card_wait(2.0)
        self.play(FadeOut(grp), run_time=1.1)
        self.card_wait(0.4)

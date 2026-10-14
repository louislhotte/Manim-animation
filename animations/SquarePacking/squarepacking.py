"""The 17 Squares Problem - why the best known packing looks broken.

The film behind the meme "this is the optimal packing of 17 squares. you have
to live with this now":

    1. Problem    16 unit squares pack a 4x4 box perfectly; the 17th forces the
                  grid to side 5 and leaves a third of the box empty.
    2. Record     Bidwell's 1998 packing, drawn from the EXACT published
                  coordinates (side 4.675530..., squares at 0, +39.80 and
                  -36.62 degrees). Best known, never beaten, NOT proven optimal.
    3. WhyTilt    the proven 5-square case (Goebel packing, 2 + 1/sqrt2) shows
                  why a tilted square beats the grid.
    4. Search     the method that finds such packings: simulated annealing on
                  the maximal-inflation score (Gensane & Ryckelynck 2005).
    5. Evolution  playback of OUR OWN search run (assets/packing_run.npz,
                  baked by generate_assets.py): the grid melts, tilts appear,
                  the box shrinks. Every frame is a real state of the search.
    6. Status     for which n the optimum is actually proven; sources.

All data on screen is real: the record coordinates are verified by a
separating-axis check at import time, and so is our own best packing.

Env knobs:
    SQ_QUICK=1   collapse holds for fast layout checks
    SQ_DELAY=<x> reading-rhythm multiplier override
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

QUICK = os.environ.get("SQ_QUICK") == "1"
DELAY = float(os.environ.get("SQ_DELAY", 0.28 if QUICK else 2.3))
ANIM_SLOW = 1.0 if QUICK else 1.15
END_HOLD = 0.2 if QUICK else 2.2

# ---- palette (house) ------------------------------------------------------- #
BG = "#0E1117"
INK = "#F5F3EF"
MUTED = "#8A93A6"
FAINT = "#3A4152"
GOLD = "#FFD166"
AX1 = "#5B8DEF"          # blue  (the +39.8 degree family)
AX2 = "#2EC4B6"          # teal
GOOD = "#3DD68C"
BAD = "#FF6B6B"          # red   (the -36.6 degree square)
SQ_FILL = "#4E5866"      # the meme-gray squares
SQ_EDGE = "#AEB6C2"
MONO = "Menlo"
FONT = "Helvetica Neue"

# --- crisp small text: render large, scale down (MANDATORY house shadow) ---- #
_BaseText = Text
_BaseText.set_default(font=FONT)
_TEXT_BASE = 60


def Text(text, font_size=48, **kw):  # noqa: F811 (intentional shadow)
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


def txt(s, fs=28, color=INK, font=None, slant=None, weight=None, t2c=None):
    kw = dict(font_size=fs, color=color)
    if font is not None:
        kw["font"] = font
    if slant is not None:
        kw["slant"] = slant
    if weight is not None:
        kw["weight"] = weight
    if t2c is not None:
        kw["t2c"] = t2c
    return Text(s, **kw)


# =========================================================================== #
# real data: the record packing, the proven 5-pack, and our own search run
# =========================================================================== #
BIDWELL_S = 4.675530093604550
_A = 39.8049589797678          # degrees
_B = -36.6237863834466
_E = BIDWELL_S - 0.5           # 4.17553...
# published coordinates (y up); flipped vertically below to match the meme image
_BIDWELL_RAW = [
    (0.5, 0.5, 0.0), (0.5, 1.5, 0.0), (1.5, 0.5, 0.0),
    (0.5, _E, 0.0), (_E, 0.5, 0.0), (_E, 1.5, 0.0),
    (3.1755300936, 0.5, 0.0), (_E, _E, 0.0),
    (2.3473248265, _E, 0.0), (_E, 2.6134601325, 0.0),
    (0.7042021557, 2.7042021557, _A),
    (1.4360434940, 3.3880434333, _A),
    (1.5567371632, 2.1129358718, _A),
    (2.2885785015, 2.7967771494, _A),
    (2.2952864462, 1.4266835477, _A),
    (3.0271277845, 2.1105248253, _A),
    (3.2450737127, 3.3724938615, _B),
]
BIDWELL = [(x, BIDWELL_S - y, -a) for (x, y, a) in _BIDWELL_RAW]

GOBEL5_S = 2.0 + 1.0 / np.sqrt(2.0)            # 2.7071..., proven optimal
GOBEL5 = [
    (0.5, 0.5, 0.0), (GOBEL5_S - 0.5, 0.5, 0.0),
    (0.5, GOBEL5_S - 0.5, 0.0), (GOBEL5_S - 0.5, GOBEL5_S - 0.5, 0.0),
    (GOBEL5_S / 2, GOBEL5_S / 2, 45.0),
]

GREEN_LOWER = (40 * np.sqrt(2) + 19) / 17       # 4.4452..., proven floor

# proven-optimal counts (Friedman survey + Wikipedia), n <= 48
PROVEN = {1, 4, 9, 16, 25, 36} | {2, 3, 5, 6, 7, 8, 10, 13, 14, 15,
                                  24, 34, 35, 46, 47, 48}


def _sat_worst(coords, s):
    """Worst pair penetration / wall protrusion for unit squares (SAT)."""
    c = np.array([[x, y] for x, y, _ in coords], dtype=float)
    th = np.radians(np.array([a for _, _, a in coords], dtype=float))
    n = len(c)
    worst = 0.0
    u = np.stack([np.cos(th), np.sin(th)], axis=1)
    v = np.stack([-np.sin(th), np.cos(th)], axis=1)
    for i in range(n - 1):
        for j in range(i + 1, n):
            axes = np.stack([u[i], v[i], u[j], v[j]])
            d = c[j] - c[i]
            dist = np.abs(axes @ d)
            ri = 0.5 * (np.abs(axes @ u[i]) + np.abs(axes @ v[i]))
            rj = 0.5 * (np.abs(axes @ u[j]) + np.abs(axes @ v[j]))
            worst = max(worst, np.min(ri + rj - dist))
    r = 0.5 * (np.abs(np.cos(th)) + np.abs(np.sin(th)))
    worst = max(worst, float(np.max(r[:, None] - c)),
                float(np.max(c + r[:, None] - s)))
    return worst


# verify the on-screen packings before we show them to anyone
assert _sat_worst(BIDWELL, BIDWELL_S) <= 1e-6, "Bidwell coordinates invalid?!"
assert _sat_worst(GOBEL5, GOBEL5_S) <= 1e-9, "Goebel 5-pack invalid?!"

# ---- our own run ----------------------------------------------------------- #
_HERE = os.path.dirname(os.path.abspath(__file__))
_NPZ = os.path.join(_HERE, "assets", "packing_run.npz")
if not os.path.exists(_NPZ):
    raise FileNotFoundError("assets/packing_run.npz missing; "
                            "run generate_assets.py first")
_RUN = np.load(_NPZ)
TRAJ_C = _RUN["traj_c"]            # (F,17,2) centers, container coords [0,s]
TRAJ_TH = _RUN["traj_th"]          # (F,17)   angles, radians
TRAJ_S = _RUN["traj_s"]            # (F,)     container side
TRAJ_P = _RUN["traj_pen"]          # (F,17)   contact pressure in [0,1]
TRAJ_IT = _RUN["traj_it"]          # (F,)     proposal count
N_FRAMES = len(TRAJ_S)
BEST_S = float(_RUN["best_s"])
BEST_C = _RUN["best_c"]
BEST_TH = _RUN["best_th"]
OUR_PROPS = int(_RUN["props"])
_ours = [(BEST_C[i, 0], BEST_C[i, 1], np.degrees(BEST_TH[i])) for i in range(17)]
assert _sat_worst(_ours, BEST_S) <= 1e-9, "our best packing is not feasible?!"


# =========================================================================== #
# drawing helpers
# =========================================================================== #
def sq_corners(cx, cy, deg, k=1.0, origin=ORIGIN, s=0.0):
    """Scene-space corners of a unit square centered (cx,cy), rotated deg,
    drawn at scale k with the CONTAINER center mapped to ``origin``."""
    t = np.radians(deg)
    u = np.array([np.cos(t), np.sin(t)])
    v = np.array([-np.sin(t), np.cos(t)])
    mid = np.array([s / 2.0, s / 2.0])
    pts = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        p = (np.array([cx, cy]) + 0.5 * (sx * u + sy * v) - mid) * k
        pts.append(origin + np.array([p[0], p[1], 0.0]))
    return pts


def square_poly(cx, cy, deg, k, origin, s, fill=SQ_FILL, fill_op=0.92,
                stroke=SQ_EDGE, sw=1.6):
    return Polygon(*sq_corners(cx, cy, deg, k, origin, s),
                   fill_color=fill, fill_opacity=fill_op,
                   stroke_color=stroke, stroke_width=sw)


def container_rect(s, k, origin, color=INK, sw=3.0, dashed=False):
    half = s * k / 2.0
    corners = [origin + np.array(p) for p in
               ((-half, -half, 0), (half, -half, 0),
                (half, half, 0), (-half, half, 0))]
    poly = Polygon(*corners, stroke_color=color, stroke_width=sw,
                   fill_opacity=0.0)
    if dashed:
        return DashedVMobject(poly, num_dashes=60)
    return poly


def pack_group(coords, s, k, origin=ORIGIN, fills=None, sw=1.6,
               cont_color=INK, cont_sw=3.0):
    """Container + squares as one VGroup. ``coords`` = [(x, y, deg), ...]."""
    cont = container_rect(s, k, origin, color=cont_color, sw=cont_sw)
    squares = VGroup(*[
        square_poly(x, y, d, k, origin, s,
                    fill=(fills[i] if fills else SQ_FILL), sw=sw)
        for i, (x, y, d) in enumerate(coords)])
    g = VGroup(cont, squares)
    g.cont, g.squares = cont, squares
    return g


def side_brace(pack, s_val, k, origin, color=GOLD, fs=30, decimals=3):
    """A measuring line under a pack with the side length label."""
    half = s_val * k / 2.0
    y = origin[1] - half - 0.34
    line = Line([origin[0] - half, y, 0], [origin[0] + half, y, 0],
                stroke_color=color, stroke_width=2.6)
    ticks = VGroup(*[Line([x, y - 0.09, 0], [x, y + 0.09, 0],
                          stroke_color=color, stroke_width=2.6)
                     for x in (origin[0] - half, origin[0] + half)])
    lab = txt(f"side {s_val:.{decimals}f}" if decimals else f"side {s_val:g}",
              fs=fs, color=color)
    lab.next_to(line, DOWN, buff=0.16)
    return VGroup(line, ticks, lab)


def _safe_t2c(s, table):
    """Prune a t2c map so no key is a substring of another present key."""
    present = [k for k in table if k and k in s]
    keep = {}
    for k in present:
        if any(k != o and k in o for o in present):
            continue
        keep[k] = table[k]
    return keep


def code_panel(lines, title="search.py", fs=17, t2c_map=None, pad=0.45):
    """Menlo code card. Lines are placed explicitly (Pango trims leading
    spaces, so indentation is re-applied geometrically)."""
    ch = txt("0" * 20, fs=fs, font=MONO).width / 20.0
    lh = txt("Ag()", fs=fs, font=MONO).height * 1.65
    rows = VGroup()
    maxw = 0.0
    for k, ln in enumerate(lines):
        stripped = ln.strip()
        if not stripped:
            continue
        indent = (len(ln) - len(ln.lstrip(" "))) * ch
        t2c = _safe_t2c(stripped, t2c_map or {})
        t = txt(stripped, fs=fs, font=MONO, t2c=t2c or None)
        t.move_to([indent, -k * lh, 0], aligned_edge=LEFT)
        rows.add(t)
        maxw = max(maxw, indent + t.width)
    body_h = (len(lines) - 1) * lh + lh
    bg = RoundedRectangle(width=maxw + 2 * pad, height=body_h + 2 * pad + 0.5,
                          corner_radius=0.14, stroke_color=FAINT,
                          stroke_width=2, fill_color="#121722",
                          fill_opacity=0.96)
    bar = Rectangle(width=bg.width, height=0.5, stroke_width=0,
                    fill_color="#1A2030", fill_opacity=1.0)
    bar.move_to(bg).align_to(bg, UP)
    # slide the rows into the panel body, keeping their own left alignment
    target_ul = np.array([bg.get_left()[0] + pad,
                          bar.get_bottom()[1] - pad * 0.9, 0.0])
    rows.shift(target_ul - rows.get_corner(UL))
    dots = VGroup(*[Dot(radius=0.05, color=c)
                    for c in ("#FF5F56", "#FFBD2E", "#27C93F")])
    dots.arrange(RIGHT, buff=0.12)
    dots.move_to(bar.get_left() + RIGHT * 0.45)
    name = txt(title, fs=15, color=MUTED, font=MONO)
    name.move_to(bar).align_to(dots.get_right() + RIGHT * 0.3, LEFT)
    name.set_y(bar.get_y())
    return VGroup(bg, bar, dots, name, rows)


# =========================================================================== #
# base scene
# =========================================================================== #
class _SqBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    def play(self, *anims, **kw):
        if "run_time" in kw:
            kw["run_time"] *= ANIM_SLOW
        super().play(*anims, **kw)

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

    def section_header(self, label, color=GOLD):
        t = Text(label, font_size=33, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=3)
        g = VGroup(t, line)
        self.play(FadeIn(g, shift=DOWN * 0.15), run_time=0.6)
        return g

    def say(self, s, color=INK, fs=26, italic=False, buff=0.42):
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
            self.play(FadeOut(old, shift=UP * 0.1), FadeIn(m, shift=UP * 0.1),
                      run_time=0.55)
        else:
            self.play(FadeIn(m, shift=UP * 0.1), run_time=0.5)
        return m

    # ---- house intro / outro ---------------------------------------------- #
    def _rule_under(self, header, pad=1.0, color=GOLD, drop=0.45):
        return Line([header.get_left()[0] - pad, header.get_bottom()[1] - drop, 0],
                    [header.get_right()[0] + pad, header.get_bottom()[1] - drop, 0]
                    ).set_stroke(width=3, color=color)

    def play_intro(self):
        header = Text("The 17 Squares Problem", font_size=56, color=INK,
                      weight="BOLD")
        header.set(width=min(10.2, header.width))
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=AX1)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        sub = Text("Why the best known packing looks like a mistake",
                   font_size=30, color=MUTED)
        if sub.width > line.width:
            sub.scale_to_fit_width(line.width)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.card_wait(1.8)
        self.play(FadeOut(VGroup(header, writer, line)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.4)
        header = Text("Thank you for watching!", font_size=48, color=INK,
                      weight="BOLD")
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=AX1)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = Text("Side 4.675, found in 1998, still unproven. Feel free to beat it.",
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
    # Scene 1 - the problem
    # ====================================================================== #
    def scene_problem(self):
        self.section_header("1 · The problem")
        K = 0.72
        origin = np.array([0.0, 0.35, 0.0])

        one = square_poly(0.5, 0.5, 0, 1.6, origin, 1.0)
        one_lab = txt("1 × 1", fs=26, color=MUTED).next_to(one, DOWN, buff=0.3)
        cap = self.show_say("Take identical unit squares, side exactly 1.")
        self.play(DrawBorderThenFill(one), FadeIn(one_lab), run_time=0.9)
        self.beat(1.4)

        # sixteen pack perfectly
        grid16 = [(i + 0.5, j + 0.5, 0.0) for j in range(4) for i in range(4)]
        pack16 = pack_group(grid16, 4.0, K, origin)
        br16 = side_brace(pack16, 4, K, origin, decimals=0)
        cap = self.replace_say(cap, "Sixteen of them fill a 4 by 4 box perfectly. "
                                    "There is nothing to improve.")
        self.play(ReplacementTransform(VGroup(one, one_lab), pack16),
                  run_time=1.1)
        self.play(FadeIn(br16), run_time=0.5)
        self.beat(1.8)

        # the 17th breaks it
        grid17 = grid16 + [(4.5, 0.5, 0.0)]
        pack17 = pack_group(grid17, 5.0, K, origin)
        pack17.squares[16].set_fill(GOLD, opacity=0.9)
        br17 = side_brace(pack17, 5, K, origin, decimals=0)
        cap = self.replace_say(cap, "Now add one more. In a grid, the 17th square "
                                    "forces a whole new row.")
        self.play(ReplacementTransform(pack16, pack17),
                  ReplacementTransform(br16, br17), run_time=1.2)
        self.beat(1.8)

        stat = VGroup(
            txt("17 tiles in a box of area 25.", fs=24, color=MUTED),
            txt("A third of it is empty.", fs=24, color=MUTED),
        ).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        stat.next_to(pack17, RIGHT, buff=0.5).shift(UP * 0.6)
        cap = self.replace_say(cap, "That feels wasteful. So what is the smallest "
                                    "box that really holds 17 unit squares?")
        self.play(FadeIn(stat, shift=LEFT * 0.2), run_time=0.6)
        self.beat(2.2)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 - the record (Bidwell 1998, exact coordinates)
    # ====================================================================== #
    def scene_record(self):
        self.section_header("2 · The best known answer")
        K = 1.06
        origin = np.array([-2.55, 0.28, 0.0])

        # naive box for scale, then the record inside it
        naive = container_rect(5.0, K, origin, color=FAINT, sw=2.5, dashed=True)
        naive_lab = txt("the 5 × 5 grid box", fs=20, color=MUTED)
        naive_lab.move_to([naive.get_right()[0] + 0.25, naive.get_top()[1] - 0.05, 0],
                          aligned_edge=LEFT)
        cap = self.show_say("In 1998, John Bidwell found this packing. "
                            "It is still the best known.")
        self.play(Create(naive), FadeIn(naive_lab), run_time=0.8)

        pack = pack_group(BIDWELL, BIDWELL_S, K, origin)
        br = side_brace(pack, BIDWELL_S, K, origin, fs=27, decimals=4)
        self.play(DrawBorderThenFill(pack.cont),
                  LaggedStart(*[DrawBorderThenFill(sq) for sq in pack.squares],
                              lag_ratio=0.06), run_time=2.4)
        self.play(FadeIn(br), run_time=0.5)
        self.beat(2.0)

        # the three angle families
        fam_a = [i for i, (_, _, d) in enumerate(BIDWELL) if d == -_A]
        fam_b = [i for i, (_, _, d) in enumerate(BIDWELL) if d == -_B]
        legend = VGroup(
            txt("10 squares stay upright", fs=24, color=INK),
            txt("6 lean at 39.80°", fs=24, color=AX1),
            txt("1 leans at 36.62°", fs=24, color=BAD),
            txt("none of them at 45°", fs=24, color=MUTED),
        ).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        note = txt("side 4.675530…", fs=25, color=GOLD)
        note2 = txt("6.5% shorter than 5.", fs=22, color=MUTED)
        note3 = txt("Never beaten since.", fs=22, color=MUTED)
        ng = VGroup(note, note2, note3).arrange(DOWN, buff=0.22,
                                                aligned_edge=LEFT)
        col = VGroup(legend, ng).arrange(DOWN, buff=0.6, aligned_edge=LEFT)
        col.move_to([4.15, 0.55, 0])
        avail = config.frame_x_radius - 0.4 - col.get_left()[0]
        if col.width > avail:
            col.scale(avail / col.width, about_point=col.get_left())
        cap = self.replace_say(cap, "Ten squares stay upright, and seven tilt. "
                                    "And none of the tilts is 45 degrees.")
        self.play(FadeIn(legend[0], shift=LEFT * 0.15), run_time=0.5)
        self.beat(0.8)
        self.play(*[pack.squares[i].animate.set_fill(AX1, opacity=0.85)
                    for i in fam_a],
                  FadeIn(legend[1], shift=LEFT * 0.15), run_time=0.8)
        self.beat(1.0)
        self.play(*[pack.squares[i].animate.set_fill(BAD, opacity=0.85)
                    for i in fam_b],
                  FadeIn(legend[2], shift=LEFT * 0.15), run_time=0.8)
        self.beat(0.8)
        self.play(FadeIn(legend[3], shift=LEFT * 0.15), run_time=0.5)
        self.beat(1.2)

        cap = self.replace_say(cap, "The side is 4.675530, verified to machine "
                                    "precision. The squares really do fit.")
        self.play(FadeIn(ng, shift=UP * 0.1), run_time=0.6)
        self.beat(2.2)

        cap = self.replace_say(cap, "But here is the twist: the meme says "
                                    "optimal, and that word is wrong.",
                               color=GOLD)
        self.beat(2.2)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 - nobody has proven it (the gap)
    # ====================================================================== #
    def scene_gap(self):
        self.section_header("3 · Best known is not proven")
        cap = self.show_say("For 17 squares, mathematics so far gives only a "
                            "window, not an answer.")

        # a number line for the side length
        lo, hi = 4.30, 5.10
        X0, X1 = -5.6, 5.6

        def nx(v):
            return X0 + (v - lo) / (hi - lo) * (X1 - X0)

        line = Line([X0, 0.1, 0], [X1, 0.1, 0], stroke_color=FAINT,
                    stroke_width=4)
        self.play(Create(line), run_time=0.7)

        marks = [
            (GREEN_LOWER, GOOD, "4.4452", "proven floor", "T. Green"),
            (BIDWELL_S, GOLD, "4.6755", "best known", "Bidwell 1998"),
            (5.0, MUTED, "5.0", "the naive grid", ""),
        ]
        mgroups = []
        for v, colr, num, name, who in marks:
            x = nx(v)
            tick = Line([x, -0.08, 0], [x, 0.28, 0], stroke_color=colr,
                        stroke_width=4)
            numt = txt(num, fs=27, color=colr, weight="BOLD")
            numt.next_to(tick, UP, buff=0.18)
            namet = txt(name, fs=21, color=colr)
            namet.next_to(tick, DOWN, buff=0.22)
            g = VGroup(tick, numt, namet)
            if who:
                whot = txt(who, fs=18, color=MUTED)
                whot.next_to(namet, DOWN, buff=0.12)
                g.add(whot)
            mgroups.append(g)
        for g in mgroups:
            self.play(FadeIn(g, shift=UP * 0.1), run_time=0.55)
            self.beat(0.7)

        # the open gap
        span = Line([nx(GREEN_LOWER), 1.45, 0], [nx(BIDWELL_S), 1.45, 0],
                    stroke_color=BAD, stroke_width=5)
        caps = VGroup(Line([nx(GREEN_LOWER), 1.3, 0], [nx(GREEN_LOWER), 1.6, 0]),
                      Line([nx(BIDWELL_S), 1.3, 0], [nx(BIDWELL_S), 1.6, 0]))
        caps.set_stroke(color=BAD, width=5)
        gap_lab = txt("the open gap", fs=23, color=BAD)
        gap_lab.next_to(span, UP, buff=0.16)
        cap = self.replace_say(cap, "A packing better than 4.6755 might exist. "
                                    "Nobody has found one, and nobody has ruled "
                                    "one out.")
        self.play(Create(span), Create(caps), FadeIn(gap_lab), run_time=0.9)
        self.beat(2.4)

        cap = self.replace_say(cap, "So the honest caption is: the best packing "
                                    "of 17 squares that anyone knows.", color=GOLD)
        self.beat(2.2)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 - why tilting helps (the proven 5-square case)
    # ====================================================================== #
    def scene_whytilt(self):
        self.section_header("4 · Why tilting wins")
        K = 0.98
        oL = np.array([-3.4, 0.30, 0.0])
        oR = np.array([2.9, 0.30, 0.0])

        cap = self.show_say("The effect starts small. Five squares, packed as a "
                            "grid, need a 3 by 3 box.")
        grid5 = [(i + 0.5, j + 0.5, 0.0) for j in range(2) for i in range(2)]
        grid5 = grid5 + [(2.5, 0.5, 0.0)]
        packL = pack_group(grid5, 3.0, K, oL)
        brL = side_brace(packL, 3, K, oL, color=MUTED, fs=26, decimals=0)
        self.play(DrawBorderThenFill(packL), FadeIn(brL), run_time=1.0)
        self.beat(1.6)

        packR = pack_group(GOBEL5, GOBEL5_S, K, oR)
        packR.squares[4].set_fill(GOLD, opacity=0.9)
        brR = side_brace(packR, GOBEL5_S, K, oR, fs=26)
        cap = self.replace_say(cap, "Tilt the middle square by 45 degrees and "
                                    "everything huddles into side 2.707.")
        self.play(DrawBorderThenFill(packR), FadeIn(brR), run_time=1.2)
        self.beat(1.8)

        proof = txt("proven optimal (packing: Göbel 1979)", fs=20, color=GOOD)
        proof.next_to(brR, DOWN, buff=0.18)
        cap = self.replace_say(cap, "For five squares this is settled: the tilted "
                                    "packing is provably the best possible.")
        self.play(FadeIn(proof, shift=UP * 0.1), run_time=0.6)
        self.beat(1.8)

        cap = self.replace_say(cap, "A tilted square braces against its "
                                    "neighbours and borrows space from two "
                                    "directions at once.")
        self.beat(2.0)
        cap = self.replace_say(cap, "Erdős and Graham proved in 1975 that tilted "
                                    "packings beat every grid when the side is "
                                    "not a whole number.")
        self.beat(2.4)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 - how such packings are found
    # ====================================================================== #
    def scene_search(self):
        self.section_header("5 · How you find one")
        cap = self.show_say("Bidwell's packing was not drawn by hand. "
                            "Packings like it come out of a search.")

        state = txt("state = (x, y, θ) for each square  →  51 numbers",
                    fs=25, color=INK, t2c={"(x, y, θ)": GOLD, "51": GOLD})
        state.move_to([0, 2.35, 0])
        self.play(FadeIn(state, shift=DOWN * 0.15), run_time=0.6)
        self.beat(1.6)

        lines = [
            "score(state): the size the squares could inflate to",
            "              before touching     # side = 1 / score",
            "",
            "for step in range(10_000_000):",
            "    trial = nudge | rotate | snap45 | teleport",
            "    dF = score(trial) - score(state)",
            "    if dF >= 0 or rand() < exp(dF / T):",
            "        state = trial      # accept some bad moves",
            "    T = cool(T)            # then freeze slowly",
        ]
        panel = code_panel(lines, title="simulated_annealing.py", fs=17,
                           t2c_map={"score": GOLD, "teleport": AX2,
                                    "snap45": AX2, "nudge": AX2,
                                    "rotate": AX2, "exp(dF / T)": AX1})
        panel.scale(0.92).move_to([0, -0.22, 0])
        cap = self.replace_say(cap, "Score any arrangement by how far its squares "
                                    "could inflate before touching.")
        self.play(FadeIn(panel, shift=UP * 0.15), run_time=0.9)
        self.beat(2.2)

        cap = self.replace_say(cap, "Then anneal: try random moves, accept every "
                                    "improvement and a few setbacks, and cool "
                                    "down slowly.")
        self.beat(2.6)
        cite = txt("This is the method of Gensane and Ryckelynck (2005), "
                   "who found several record packings this way.",
                   fs=20, color=MUTED)
        if cite.width > 11.8:
            cite.scale_to_fit_width(11.8)
        cite.next_to(panel, DOWN, buff=0.26)
        self.play(FadeIn(cite, shift=UP * 0.1), run_time=0.6)
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 6 - our own run, replayed from the real trajectory
    # ====================================================================== #
    def scene_evolution(self):
        self.section_header("6 · Watching a search run")
        KU = 5.0                       # screen size of the fixed box
        origin = np.array([-2.1, 0.28, 0.0])
        LAM_FLOOR = 0.185              # draw floor while the state is molten

        CF = TRAJ_C / TRAJ_S[:, None, None]      # centers as box fractions
        LAM = 1.0 / TRAJ_S                       # true inflation per frame
        BSF = 1.0 / np.minimum.accumulate(TRAJ_S)  # best-so-far inflation

        idx = ValueTracker(0.0)

        def state_at(t):
            a = int(np.clip(np.floor(t), 0, N_FRAMES - 1))
            b = min(a + 1, N_FRAMES - 1)
            u = float(t) - a
            cf = (1 - u) * CF[a] + u * CF[b]
            th = (1 - u) * TRAJ_TH[a] + u * TRAJ_TH[b]
            lam = (1 - u) * LAM[a] + u * LAM[b]
            p = (1 - u) * TRAJ_P[a] + u * TRAJ_P[b]
            return cf, th, lam, p

        def corners_frac(cf_i, th_i, a):
            """Corners of a square of side ``a`` (box units) in the unit box."""
            u = np.array([np.cos(th_i), np.sin(th_i)])
            v = np.array([-np.sin(th_i), np.cos(th_i)])
            pts = []
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                p = (cf_i + 0.5 * a * (sx * u + sy * v) - 0.5) * KU
                pts.append(origin + np.array([p[0], p[1], 0.0]))
            return pts

        base_rgb = color_to_rgb(ManimColor(SQ_FILL))
        hot_rgb = color_to_rgb(ManimColor(GOLD))

        cf0, th0, lam0, p0 = state_at(0.0)
        cont = container_rect(1.0, KU, origin, color=INK, sw=3.0)
        polys = VGroup(*[
            Polygon(*corners_frac(cf0[i], th0[i], lam0),
                    fill_color=SQ_FILL, fill_opacity=0.92,
                    stroke_color=SQ_EDGE, stroke_width=1.5)
            for i in range(17)])

        def upd_polys(grp):
            cf, th, lam, p = state_at(idx.get_value())
            a = max(lam, LAM_FLOOR)
            for i, poly in enumerate(grp):
                pts = corners_frac(cf[i], th[i], a)
                poly.set_points_as_corners([*pts, pts[0]])
                rgb = (1 - 0.4 * p[i]) * base_rgb + 0.4 * p[i] * hot_rgb
                poly.set_fill(rgb_to_color(rgb), opacity=0.92)

        # HUD (right side): best side so far + proposal counter
        hud_head = txt("best side", fs=21, color=MUTED)
        hud_side = txt("5.0000", fs=34, color=GOLD, font=MONO)
        hud_it = txt("0.00M proposals", fs=21, color=MUTED, font=MONO)
        hud_rec = txt("record 4.6755", fs=21, color=FAINT, font=MONO)
        hud = VGroup(hud_head, hud_side, hud_it, hud_rec)
        hud.arrange(DOWN, buff=0.26, aligned_edge=LEFT).move_to(
            [3.55, 1.7, 0], aligned_edge=LEFT)

        def make_hud_upd(fmt, getter, fs, color):
            cache = {"s": None}

            def _u(m):
                t = idx.get_value()
                sval = fmt(getter(t))
                if sval != cache["s"]:
                    cache["s"] = sval
                    new = txt(sval, fs=fs, color=color, font=MONO)
                    new.move_to(m, aligned_edge=LEFT)
                    m.become(new)
            return _u

        cap = self.show_say("This is our own run of that loop: 17 squares "
                            "growing inside one fixed box.")
        self.play(Create(cont), FadeIn(polys), FadeIn(hud), run_time=0.9)
        polys.add_updater(upd_polys)
        hud_side.add_updater(make_hud_upd(
            lambda v: f"{1.0/v:.4f}",
            lambda t: float(np.interp(t, np.arange(N_FRAMES), BSF)), 34, GOLD))
        hud_it.add_updater(make_hud_upd(
            lambda v: f"{v/1e6:.2f}M proposals",
            lambda t: float(np.interp(t, np.arange(N_FRAMES), TRAJ_IT)),
            21, MUTED))
        self.beat(1.6)

        F = N_FRAMES - 1
        seg1 = 0.30 if QUICK else 12.0
        seg2 = 0.30 if QUICK else 14.0
        seg3 = 0.30 if QUICK else 10.0
        self.play(idx.animate.set_value(0.28 * F), run_time=seg1,
                  rate_func=linear)
        cap = self.replace_say(cap, "First the search shrinks and scrambles "
                                    "them. Making it worse is how it escapes "
                                    "the grid.")
        self.play(idx.animate.set_value(0.72 * F), run_time=seg2,
                  rate_func=linear)
        cap = self.replace_say(cap, "Then it cools. Tilted clusters appear on "
                                    "their own, and the squares grow past the "
                                    "grid size.")
        self.play(idx.animate.set_value(1.0 * F), run_time=seg3,
                  rate_func=linear)
        self.beat(0.8)

        polys.clear_updaters()
        hud_side.clear_updaters()
        hud_it.clear_updaters()

        # freeze on our best, compare to the record
        ours = [(BEST_C[i, 0], BEST_C[i, 1], np.degrees(BEST_TH[i]))
                for i in range(17)]
        k_fin = KU / BEST_S            # same on-screen box size as the run view
        final = pack_group(ours, BEST_S, k_fin, origin)
        for i in range(17):
            d = abs(((np.degrees(BEST_TH[i]) + 45) % 90) - 45)
            if d > 3:
                final.squares[i].set_fill(AX1, opacity=0.85)
        br = side_brace(final, BEST_S, k_fin, origin, fs=26, decimals=4)
        cap = self.replace_say(cap,
                               f"Our budget was ten minutes on a laptop. "
                               f"Final answer: side {BEST_S:.4f}.")
        self.play(ReplacementTransform(polys, final.squares),
                  ReplacementTransform(cont, final.cont),
                  FadeIn(br), run_time=1.0)
        self.beat(1.8)

        verdict = txt(f"ours {BEST_S:.4f}  vs  record 4.6755", fs=24,
                      color=INK, t2c={"4.6755": GOLD})
        verdict.move_to([4.05, -0.9, 0])
        if verdict.get_right()[0] > config.frame_x_radius - 0.35:
            verdict.scale_to_fit_width(2 * (config.frame_x_radius - 0.35 - 4.05))
        cap = self.replace_say(cap, "The record needed years of refinement. "
                                    "The last hundredth is the hardest part.")
        self.play(FadeIn(verdict, shift=UP * 0.1), run_time=0.6)
        self.beat(2.2)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 7 - what is actually proven
    # ====================================================================== #
    def scene_status(self):
        self.section_header("7 · What is actually proven")
        cap = self.show_say("For how many squares do we truly know the best "
                            "packing? Here is the scoreboard up to 48.")

        cells = VGroup()
        for n in range(1, 49):
            proven = n in PROVEN
            col = GOOD if proven else FAINT
            if n == 17:
                col = GOLD
            box = RoundedRectangle(width=0.62, height=0.62, corner_radius=0.1,
                                   stroke_color=col, stroke_width=2.2,
                                   fill_color=col,
                                   fill_opacity=0.30 if proven or n == 17 else 0.06)
            num = txt(str(n), fs=20,
                      color=INK if (proven or n == 17) else MUTED)
            num.move_to(box)
            cells.add(VGroup(box, num))
        cells.arrange_in_grid(rows=6, cols=8, buff=0.14)
        cells.move_to([0, 0.5, 0])
        self.play(LaggedStart(*[FadeIn(cl, scale=0.8) for cl in cells],
                              lag_ratio=0.015), run_time=1.8)

        legend = VGroup(
            VGroup(Square(0.24, stroke_color=GOOD, stroke_width=2.2,
                          fill_color=GOOD, fill_opacity=0.3),
                   txt("proven optimal", fs=21, color=INK)).arrange(RIGHT, buff=0.18),
            VGroup(Square(0.24, stroke_color=GOLD, stroke_width=2.2,
                          fill_color=GOLD, fill_opacity=0.3),
                   txt("17: open since 1998", fs=21, color=INK)).arrange(RIGHT, buff=0.18),
        ).arrange(RIGHT, buff=0.9)
        legend.next_to(cells, DOWN, buff=0.4)
        self.play(FadeIn(legend, shift=UP * 0.1), run_time=0.6)
        self.beat(2.4)

        cap = self.replace_say(cap, "Perfect squares are easy, and a few small "
                                    "cases have real proofs. Almost everything "
                                    "else is open.")
        self.beat(2.4)
        self.settle()
        self.wipe()

        # sources card
        cap2 = self.show_say("The numbers in this film come from these sources.",
                             fs=24)
        refs = VGroup(
            txt("E. Friedman, Packing Unit Squares in Squares: A Survey, "
                "Electron. J. Combin. DS7 (2009)", fs=21, color=INK),
            txt("J. Bidwell 1998, packing of 17, in Friedman's survey. "
                "Exact value: D. Ellsworth 2023", fs=21, color=INK),
            txt("T. Gensane, P. Ryckelynck, Improved Dense Packings, "
                "Discrete Comput. Geom. 34 (2005)", fs=21, color=INK),
            txt("P. Erdős, R. Graham, On Packing Squares with Equal Squares, "
                "JCTA 19 (1975)", fs=21, color=INK),
            txt("W. Stromquist, Packing 10 or 11 Unit Squares, "
                "Electron. J. Combin. 10 (2003)", fs=21, color=INK),
        ).arrange(DOWN, buff=0.34, aligned_edge=LEFT)
        for r in refs:
            if r.width > 11.8:
                r.scale_to_fit_width(11.8)
        refs.move_to([0, 0.75, 0])
        rule = Line(refs.get_corner(UL) + UP * 0.35 + LEFT * 0.2,
                    refs.get_corner(UR) + UP * 0.35 + RIGHT * 0.2,
                    stroke_color=GOLD, stroke_width=3)
        self.play(FadeIn(rule), LaggedStart(*[FadeIn(r, shift=UP * 0.08)
                                              for r in refs],
                                            lag_ratio=0.12), run_time=1.4)
        self.beat(3.0)
        self.settle()
        self.wipe()

    # ---- film assembly ----------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_problem()
        self.scene_record()
        self.scene_gap()
        self.scene_whytilt()
        self.scene_search()
        self.scene_evolution()
        self.scene_status()
        self.play_outro()


# ---- thin scene classes ---------------------------------------------------- #
class SeventeenSquares(_SqBase):
    def construct(self):
        self.play_all()


class Intro(_SqBase):
    def construct(self):
        self.play_intro()


class Problem(_SqBase):
    def construct(self):
        self.scene_problem()


class Record(_SqBase):
    def construct(self):
        self.scene_record()


class Gap(_SqBase):
    def construct(self):
        self.scene_gap()


class WhyTilt(_SqBase):
    def construct(self):
        self.scene_whytilt()


class Search(_SqBase):
    def construct(self):
        self.scene_search()


class Evolution(_SqBase):
    def construct(self):
        self.scene_evolution()


class Status(_SqBase):
    def construct(self):
        self.scene_status()


class Outro(_SqBase):
    def construct(self):
        self.play_outro()

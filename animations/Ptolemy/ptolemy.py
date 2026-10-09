"""Ptolemy's Theorem — a short, house-style visual explainer.

A self-explanatory (no voice-over) film about the most beautiful fact linking the
sides and the diagonals of a four-sided figure drawn inside a circle:

        AC · BD  =  AB · CD  +  BC · DA

For a cyclic quadrilateral ABCD (four points on a circle, in order), the product
of the two diagonals equals the sum of the products of the two pairs of opposite
sides. It is named for Claudius Ptolemy (~150 AD), who used it to build the first
table of chords, the ancestor of the sine table.

Scenes:

    1. Setup       -- a circle, four points A B C D on it, the quadrilateral and
                      its two diagonals, and the statement, colour-coded.
    2. Check       -- a concrete cyclic quadrilateral with real coordinates: the
                      six lengths, the two products, and a live check as D slides
                      around the circle: the two sides stay exactly equal.
    3. Proof       -- the classic proof. Place K on diagonal AC so ∠ABK = ∠DBC.
                      Two pairs of similar triangles give AK·BD = AB·CD and
                      KC·BD = BC·DA; adding them (AK + KC = AC) finishes it.
    4. Pythagoras  -- the special case: inscribe a rectangle. Its diagonals are a
                      diameter, so Ptolemy becomes  d² = a² + b². Pythagoras is
                      hiding inside Ptolemy.
    5. Space       -- **3D**: keep A B C on the circle and lift D up out of the
                      plane. Now  AC·BD < AB·CD + BC·DA : equality is knife-edge,
                      holding exactly when the four points share one circle. The
                      camera orbits so you can see the point leave the plane.
    6. Recap       -- one card: what it says, and the four things we saw.

Camera policy (memory: camera-control-only-for-3d): every 2D scene uses a static
camera; camera movement is reserved for the one real `ThreeDScene` (Space), where
orbiting shows a point genuinely leaving the plane of the circle.

Everything is `Text` (Pango), never `Tex` — no LaTeX toolchain. Every number comes
from one source of truth: the point coordinates on the circle, so the displayed
lengths and products are real distances (computed and asserted at import).

Scenes render individually (`Intro`, `Setup`, `Check`, `Proof`, `Pythagoras`,
`Space`, `Recap`, `Outro`); the whole film is the stitch of them in order
(`./render.sh full` / `--stitch`), because it mixes 2D `Scene` and 3D
`ThreeDScene` classes.

Env knobs:
    PTOL_QUICK=1   shorten every hold for a fast sanity render
    PTOL_DELAY=x   override the reading-hold multiplier
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

# ---- crisp text: render big, scale down (Pango mangles small sizes) -------- #
# MANDATORY shadow (manim-explainer SKILL §2). Must come BEFORE mtext so the
# super/subscript helper binds this shadowed Text and its small pieces stay crisp.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("PTOL_QUICK") == "1"
DELAY = float(os.environ.get("PTOL_DELAY", "0.3" if QUICK else "2.2"))
END_HOLD = 0.2 if QUICK else 2.0

# ---- palette (shared house style) ---------------------------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / axes
FAINT = "#3A4152"       # guides / gridlines
GRID = "#232A38"        # faint panel fills
GOLD = "#FFD166"        # highlights / rules / the QED result

DIAG = "#C792EA"        # the diagonals AC, BD (violet)
SIDE1 = "#5B8DEF"       # one pair of opposite sides AB, CD (blue)
SIDE2 = "#3DD68C"       # the other pair BC, DA (green)
RING = "#7C8AA5"        # the circle itself (muted blue-grey)
BAD = "#FF5C5C"         # "not equal" / off the circle (red)
GOOD = "#43D17A"        # the running check (green)


# ========================================================================== #
# Geometry helpers
# ========================================================================== #
def cpt(center, r, deg):
    """A point on the circle of radius ``r`` about ``center`` at ``deg`` degrees."""
    a = deg * DEGREES
    return np.array([center[0] + r * np.cos(a), center[1] + r * np.sin(a), 0.0])


def dist(p, q):
    return float(np.linalg.norm(np.array(p) - np.array(q)))


def unit(v):
    """Unit vector in the direction of ``v`` (zero vector maps to zero)."""
    v = np.array(v, dtype=float)
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v * 0.0


def quad_points(center, r, ang):
    """Return dict A,B,C,D of scene points, given a dict of degree angles."""
    return {k: cpt(center, r, v) for k, v in ang.items()}


def seg(p, q, color=INK, width=4.0, opacity=1.0):
    return Line(p, q, stroke_color=color, stroke_width=width, stroke_opacity=opacity)


def dseg(p, q, color=INK, width=3.0, dl=0.14):
    return DashedLine(p, q, stroke_color=color, stroke_width=width, dash_length=dl)


def vdot(p, color=INK, r=0.075):
    return Dot(point=p, radius=r, color=color).set_stroke(BG, 1.5)


def vlabel(name, p, center, color=INK, buff=0.34, fs=30):
    """A vertex label placed radially outward from ``center``."""
    d = np.array(p) - np.array(center)
    n = np.linalg.norm(d)
    direction = d / n if n > 1e-6 else RIGHT
    t = Text(name, font_size=fs, color=color, weight=BOLD)
    t.move_to(np.array(p) + direction * buff)
    return t


def tri(p, q, r, color, op=0.34, sw=0.0):
    return Polygon(p, q, r, stroke_width=sw, stroke_color=color,
                   fill_color=color, fill_opacity=op)


def _ang_of(v):
    return float(np.arctan2(v[1], v[0]))


def _wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def angle_mark(vertex, p1, p2, color=GOLD, radius=0.42, sw=3.5, double=False):
    """A small arc at ``vertex`` spanning the (interior) angle p1-vertex-p2."""
    a1 = _ang_of(np.array(p1) - np.array(vertex))
    a2 = _ang_of(np.array(p2) - np.array(vertex))
    d = _wrap(a2 - a1)
    grp = VGroup()
    grp.add(Arc(radius=radius, start_angle=a1, angle=d, arc_center=np.array(vertex),
                stroke_color=color, stroke_width=sw))
    if double:
        grp.add(Arc(radius=radius + 0.09, start_angle=a1, angle=d,
                    arc_center=np.array(vertex), stroke_color=color, stroke_width=sw))
    return grp


def right_angle_mark(vertex, p1, p2, color=INK, size=0.28, sw=3.0):
    """A small square marking a right angle at ``vertex``."""
    v = np.array(vertex)
    u1 = (np.array(p1) - v) / np.linalg.norm(np.array(p1) - v)
    u2 = (np.array(p2) - v) / np.linalg.norm(np.array(p2) - v)
    pts = [v + u1 * size, v + (u1 + u2) * size, v + u2 * size]
    return VMobject(stroke_color=color, stroke_width=sw).set_points_as_corners(pts)


def line_intersect(p1, p2, p3, p4):
    """Intersection of line (p1,p2) with line (p3,p4), in 2D."""
    x1, y1 = p1[0], p1[1]
    x2, y2 = p2[0], p2[1]
    x3, y3 = p3[0], p3[1]
    x4, y4 = p4[0], p4[1]
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / den
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / den
    return np.array([px, py, 0.0])


def construct_K(A, B, C, D):
    """Point K on AC with ∠ABK = ∠DBC (the classical Ptolemy construction)."""
    aBA = _ang_of(A - B)
    aBC = _ang_of(C - B)
    aBD = _ang_of(D - B)
    angDBC = abs(_wrap(aBD - aBC))
    s = np.sign(_wrap(aBC - aBA))      # rotate BA toward BC (interior)
    aBK = aBA + s * angDBC
    far = B + 6.0 * np.array([np.cos(aBK), np.sin(aBK), 0.0])
    return line_intersect(B, far, A, C)


def mtext(parts, base_fs=34):
    """Assemble an inline 'formula' from Text pieces — no LaTeX.

    Each part is ``(s, role[, color])`` with role in {"b" base, "^" super, "_" sub}.
    Supers/subs attach to the previous base, so ``d`` then ``("2","^")`` reads d².
    """
    grp = VGroup()
    last_base = None
    for p in parts:
        s, role = p[0], p[1]
        col = p[2] if len(p) > 2 else INK
        if role == "b":
            m = Text(s, font_size=base_fs, color=col, weight=BOLD)
            if len(grp) > 0:
                m.next_to(grp, RIGHT, buff=0.06, aligned_edge=DOWN)
            grp.add(m)
            last_base = m
        else:
            m = Text(s, font_size=int(base_fs * 0.62), color=col, weight=BOLD)
            anchor = last_base if last_base is not None else grp
            m.next_to(anchor, RIGHT, buff=0.02)
            if role == "^":
                m.align_to(anchor, UP).shift(UP * anchor.height * 0.32)
            else:
                m.align_to(anchor, DOWN).shift(DOWN * anchor.height * 0.12)
            grp.add(m)
    return grp


def squared(letter, color, fs=44):
    """A single squared symbol, e.g. d², with a crisp raised exponent."""
    return mtext([(letter, "b", color), ("2", "^", color)], base_fs=fs)


def theorem_eq(fs=40, buff=0.16):
    """Build  AC·BD = AB·CD + BC·DA  as separately-coloured pieces."""
    def T(s, c, w=BOLD):
        return Text(s, font_size=fs, color=c, weight=w)

    ac = T("AC", DIAG); d1 = T("·", MUTED, NORMAL); bd = T("BD", DIAG)
    eq = T("=", MUTED, NORMAL)
    ab = T("AB", SIDE1); d2 = T("·", MUTED, NORMAL); cd = T("CD", SIDE1)
    pl = T("+", MUTED, NORMAL)
    bc = T("BC", SIDE2); d3 = T("·", MUTED, NORMAL); da = T("DA", SIDE2)
    row = VGroup(ac, d1, bd, eq, ab, d2, cd, pl, bc, d3, da).arrange(RIGHT, buff=buff)
    parts = dict(ac=ac, bd=bd, eq=eq, ab=ab, cd=cd, pl=pl, bc=bc, da=da,
                 lhs=VGroup(ac, d1, bd), rhs1=VGroup(ab, d2, cd),
                 rhs2=VGroup(bc, d3, da))
    return row, parts


# ========================================================================== #
# The hero cyclic quadrilateral (one source of truth; real distances)
# ========================================================================== #
CENTER = np.array([-3.15, 0.12, 0.0])
R = 2.5
ANG = dict(A=145, B=212, C=308, D=44)      # CCW order A,B,C,D around the circle
HERO = quad_points(CENTER, R, ANG)
_A, _B, _C, _D = HERO["A"], HERO["B"], HERO["C"], HERO["D"]

# real lengths (scene units) — the film's numbers all come from these
LEN = dict(
    AB=dist(_A, _B), BC=dist(_B, _C), CD=dist(_C, _D), DA=dist(_D, _A),
    AC=dist(_A, _C), BD=dist(_B, _D),
)
_LHS = LEN["AC"] * LEN["BD"]
_RHS = LEN["AB"] * LEN["CD"] + LEN["BC"] * LEN["DA"]
assert abs(_LHS - _RHS) < 1e-9, (_LHS, _RHS)      # Ptolemy holds exactly
_K = construct_K(_A, _B, _C, _D)
_tK = float(np.dot(_K - _A, _C - _A) / np.dot(_C - _A, _C - _A))
assert 0.05 < _tK < 0.95, _tK                     # K is interior to AC


# ========================================================================== #
class _Common:
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.2))

    def section_header(self, label, color=GOLD):
        t = Text(label, font_size=33, color=INK, weight=BOLD).to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=4)
        return VGroup(t, line)

    def say(self, text, color=INK, fs=26, y=-3.42, weight=NORMAL):
        cap = Text(text, font_size=fs, color=color, weight=weight)
        if cap.width > 12.7:
            cap.scale_to_fit_width(12.7)
        cap.move_to([0, y, 0])
        return cap

    def clamp_w(self, mob, w=6.5):
        if mob.width > w:
            mob.scale_to_fit_width(w)
        return mob


# ========================================================================== #
class _PtolBase(_Common, Scene):
    """Base for every 2D scene. Static camera by design."""

    def setup(self):
        self.camera.background_color = BG

    def wipe(self, rt=0.7):
        self.wait(END_HOLD)
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    # ---- house-style intro / outro cards ---------------------------------- #
    def _rule_under(self, header, color=GOLD, pad=1.0, drop=0.45):
        return Line(
            [header.get_left()[0] - pad, header.get_bottom()[1] - drop, 0],
            [header.get_right()[0] + pad, header.get_bottom()[1] - drop, 0],
        ).set_stroke(width=3, color=color)

    def _emblem(self, center, r=0.9):
        """A tiny inscribed-quadrilateral emblem for the title card."""
        ring = Circle(radius=r, color=RING, stroke_width=3).move_to(center)
        pts = [cpt(center, r, d) for d in (160, 235, 315, 40)]
        quad = Polygon(*pts, stroke_color=INK, stroke_width=2.5, fill_opacity=0)
        dgs = VGroup(seg(pts[0], pts[2], DIAG, 2.5), seg(pts[1], pts[3], DIAG, 2.5))
        dots = VGroup(*[vdot(p, INK, 0.05) for p in pts])
        return VGroup(ring, quad, dgs, dots)

    def introduction(self, title1, title2):
        header = Text(title1, font_size=54, color=INK, weight=BOLD)
        header.set(width=min(10.5, header.width))
        emblem = self._emblem(ORIGIN).next_to(header, UP, buff=0.55)
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=DIAG)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Create(emblem), run_time=1.4)
        self.play(Write(header), Create(line), run_time=1.5)
        self.card_wait(0.7)
        sub = Text(title2, font_size=31, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.card_wait(2.0)
        return VGroup(emblem, header, writer, line)

    def play_intro(self):
        group = self.introduction(
            "Ptolemy's Theorem",
            "The diagonals and sides of a quadrilateral drawn in a circle",
        )
        self.play(FadeOut(group), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight=BOLD)
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=DIAG)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.5)
        self.card_wait(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.1)
        self.card_wait(2.2)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 — Setup: the circle, the quadrilateral, the statement
    # ====================================================================== #
    def _build_quad(self, colored=True, diag=True):
        """Build the hero figure. Returns a dict of its parts."""
        circle = Circle(radius=R, color=RING, stroke_width=3).move_to(CENTER)
        A, B, C, D = _A, _B, _C, _D
        c_ab = SIDE1 if colored else INK
        c_bc = SIDE2 if colored else INK
        s_ab = seg(A, B, c_ab); s_bc = seg(B, C, c_bc)
        s_cd = seg(C, D, c_ab); s_da = seg(D, A, c_bc)
        sides = VGroup(s_ab, s_bc, s_cd, s_da)
        dots = VGroup(*[vdot(p) for p in (A, B, C, D)])
        labs = VGroup(
            vlabel("A", A, CENTER), vlabel("B", B, CENTER),
            vlabel("C", C, CENTER), vlabel("D", D, CENTER),
        )
        d_ac = seg(A, C, DIAG, 4.0); d_bd = seg(B, D, DIAG, 4.0)
        diags = VGroup(d_ac, d_bd)
        return dict(circle=circle, sides=sides, dots=dots, labs=labs, diags=diags,
                    s_ab=s_ab, s_bc=s_bc, s_cd=s_cd, s_da=s_da, d_ac=d_ac, d_bd=d_bd)

    def scene_setup(self):
        header = self.section_header("A quadrilateral inside a circle", RING)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        fig = self._build_quad(colored=False, diag=True)
        self.play(Create(fig["circle"]), run_time=1.1)
        cap = self.say("Start with a circle, and pick four points on it.", color=MUTED)
        self.play(FadeIn(cap), run_time=0.5)
        self.play(LaggedStart(*[GrowFromCenter(d) for d in fig["dots"]],
                              lag_ratio=0.35), FadeIn(fig["labs"]), run_time=1.4)
        self.beat(1.2)

        cap2 = self.say("Join them in order into a four-sided figure: a cyclic "
                        "quadrilateral.", color=INK)
        self.play(FadeOut(cap), FadeIn(cap2), run_time=0.4)
        self.play(Create(fig["sides"]), run_time=1.6)
        self.beat(1.4)

        cap3 = self.say("Now draw its two diagonals, AC and BD.", color=DIAG)
        self.play(FadeOut(cap2), FadeIn(cap3), run_time=0.4)
        self.play(Create(fig["d_ac"]), Create(fig["d_bd"]), run_time=1.2)
        cross = vdot(line_intersect(_A, _C, _B, _D), DIAG, 0.06)
        self.play(FadeIn(cross, scale=0.5), run_time=0.4)
        self.beat(1.4)

        # colour the opposite side-pairs to match the statement
        cap4 = self.say("Opposite sides come in two pairs: AB with CD, and BC "
                        "with DA.", color=INK)
        self.play(FadeOut(cap3), FadeIn(cap4), run_time=0.4)
        self.play(fig["s_ab"].animate.set_stroke(SIDE1),
                  fig["s_cd"].animate.set_stroke(SIDE1), run_time=0.7)
        self.play(fig["s_bc"].animate.set_stroke(SIDE2),
                  fig["s_da"].animate.set_stroke(SIDE2), run_time=0.7)
        self.beat(1.2)

        # the statement, colour-coded, on the right
        eq, _ = theorem_eq(fs=38)
        self.clamp_w(eq, 6.6).move_to([3.15, 1.1, 0])
        title = Text("Ptolemy's Theorem", font_size=30, color=GOLD, weight=BOLD)
        title.next_to(eq, UP, buff=0.5)
        self.play(FadeOut(cap4), FadeIn(title, shift=DOWN * 0.1), run_time=0.5)
        self.play(Write(eq), run_time=1.6)
        box = SurroundingRectangle(eq, color=GOLD, buff=0.22, corner_radius=0.1)
        self.play(Create(box), run_time=0.7)
        cap5 = self.say("The product of the diagonals equals the sum of the products "
                        "of the opposite sides.", color=GOLD, weight=BOLD)
        self.play(FadeIn(cap5, shift=UP * 0.1), run_time=0.6)
        self.beat(2.4)
        self.wipe()

    # ====================================================================== #
    # Scene 2 — Check: real coordinates, and a live drag
    # ====================================================================== #
    def scene_check(self):
        header = self.section_header("Check it with real numbers", GOOD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        A, B, C, D = _A, _B, _C, _D
        circle = Circle(radius=R, color=RING, stroke_width=3).move_to(CENTER)
        s_ab = seg(A, B, SIDE1); s_bc = seg(B, C, SIDE2)
        s_cd = seg(C, D, SIDE1); s_da = seg(D, A, SIDE2)
        d_ac = seg(A, C, DIAG); d_bd = seg(B, D, DIAG)
        dots = VGroup(*[vdot(p) for p in (A, B, C, D)])
        labs = VGroup(vlabel("A", A, CENTER), vlabel("B", B, CENTER),
                      vlabel("C", C, CENTER), vlabel("D", D, CENTER))
        fig = VGroup(circle, s_ab, s_bc, s_cd, s_da, d_ac, d_bd, dots, labs)
        self.play(Create(circle), Create(VGroup(s_ab, s_bc, s_cd, s_da)),
                  FadeIn(dots), FadeIn(labs), run_time=1.3)
        self.play(Create(d_ac), Create(d_bd), run_time=0.8)

        # the six real lengths, briefly, in two colour-coded columns
        def lrow(name, val, col):
            return Text(f"{name} = {val:.2f}", font_size=24, color=col)

        lens_col1 = VGroup(lrow("AB", LEN["AB"], SIDE1), lrow("BC", LEN["BC"], SIDE2),
                           lrow("AC", LEN["AC"], DIAG)).arrange(DOWN, aligned_edge=LEFT, buff=0.34)
        lens_col2 = VGroup(lrow("CD", LEN["CD"], SIDE1), lrow("DA", LEN["DA"], SIDE2),
                           lrow("BD", LEN["BD"], DIAG)).arrange(DOWN, aligned_edge=LEFT, buff=0.34)
        lens = VGroup(lens_col1, lens_col2).arrange(RIGHT, buff=0.75, aligned_edge=UP)
        lens.move_to([3.2, 1.85, 0])
        cap = self.say("Measure all six lengths from the coordinates.", color=MUTED)
        self.play(FadeIn(cap),
                  LaggedStart(*[FadeIn(m, shift=UP * 0.1) for col in lens for m in col],
                              lag_ratio=0.15), run_time=1.6)
        self.beat(1.8)

        # the two products
        lhs_row = VGroup(
            Text("AC · BD", font_size=30, color=DIAG, weight=BOLD),
            Text("=", font_size=30, color=MUTED),
            Text(f"{_LHS:.2f}", font_size=32, color=GOLD, weight=BOLD),
        ).arrange(RIGHT, buff=0.25)
        rhs_row = VGroup(
            VGroup(Text("AB·CD", font_size=30, color=SIDE1, weight=BOLD),
                   Text("+", font_size=30, color=MUTED),
                   Text("BC·DA", font_size=30, color=SIDE2, weight=BOLD)).arrange(RIGHT, buff=0.18),
            Text("=", font_size=30, color=MUTED),
            Text(f"{_RHS:.2f}", font_size=32, color=GOLD, weight=BOLD),
        ).arrange(RIGHT, buff=0.25)
        prod = VGroup(lhs_row, rhs_row).arrange(DOWN, aligned_edge=RIGHT, buff=0.5)
        prod.next_to(lens, DOWN, buff=0.6).align_to(lens, LEFT)
        self.play(FadeOut(cap), FadeIn(lhs_row, shift=UP * 0.1), run_time=0.7)
        self.beat(0.8)
        self.play(FadeIn(rhs_row, shift=UP * 0.1), run_time=0.7)
        eqbox = SurroundingRectangle(VGroup(lhs_row[-1], rhs_row[-1]),
                                     color=GOOD, buff=0.18, corner_radius=0.1)
        chk = Text(f"both equal {_LHS:.2f}  ✓", font_size=26, color=GOOD, weight=BOLD)
        chk.next_to(prod, DOWN, buff=0.45).align_to(prod, LEFT)
        self.play(Create(eqbox), FadeIn(chk, shift=UP * 0.1), run_time=0.8)
        self.beat(2.0)

        # ---- live drag: slide D around the circle, the equation stays balanced #
        self.play(FadeOut(lens), FadeOut(prod), FadeOut(eqbox), FadeOut(chk),
                  FadeOut(d_bd), FadeOut(s_cd), FadeOut(s_da),
                  FadeOut(dots[3]), FadeOut(labs[3]), run_time=0.6)

        d_ang = ValueTracker(ANG["D"])

        def Dpt():
            return cpt(CENTER, R, d_ang.get_value())

        def d_group():
            d = Dpt()
            g = VGroup(
                seg(C, d, SIDE1), seg(d, A, SIDE2), seg(B, d, DIAG),
                vdot(d), vlabel("D", d, CENTER),
            )
            return g

        live = always_redraw(d_group)
        self.add(live)

        def f_lhs():
            return LEN["AC"] * dist(B, Dpt())

        def f_rhs():
            d = Dpt()
            return dist(A, B) * dist(C, d) + LEN["BC"] * dist(d, A)

        panel_l = VGroup(
            Text("AC · BD", font_size=30, color=DIAG, weight=BOLD),
            Text("=", font_size=30, color=MUTED),
        ).arrange(RIGHT, buff=0.22)
        panel_r = VGroup(
            Text("AB·CD", font_size=30, color=SIDE1, weight=BOLD),
            Text("+", font_size=30, color=MUTED),
            Text("BC·DA", font_size=30, color=SIDE2, weight=BOLD),
            Text("=", font_size=30, color=MUTED),
        ).arrange(RIGHT, buff=0.18)
        panel = VGroup(panel_l, panel_r).arrange(DOWN, aligned_edge=LEFT, buff=0.6)
        panel.move_to([3.15, 1.2, 0])

        num_l = DecimalNumber(f_lhs(), num_decimal_places=2, font_size=34, color=GOLD)
        num_r = DecimalNumber(f_rhs(), num_decimal_places=2, font_size=34, color=GOLD)
        num_l.add_updater(lambda m: m.set_value(f_lhs()).next_to(panel_l, RIGHT, buff=0.25))
        num_r.add_updater(lambda m: m.set_value(f_rhs()).next_to(panel_r, RIGHT, buff=0.25))

        cap2 = self.say("Now slide D anywhere along the circle and watch both sides.",
                        color=INK)
        self.play(FadeIn(panel), FadeIn(num_l), FadeIn(num_r), FadeIn(cap2), run_time=0.8)
        eqmark = Text("always equal", font_size=25, color=GOOD, weight=BOLD)
        eqmark.next_to(panel, DOWN, buff=0.5)
        self.play(FadeIn(eqmark, shift=UP * 0.1), run_time=0.5)
        self.beat(1.0)

        self.play(d_ang.animate.set_value(108), run_time=2.6, rate_func=smooth)
        self.beat(0.8)
        self.play(d_ang.animate.set_value(6), run_time=3.0, rate_func=smooth)
        self.beat(0.8)
        self.play(d_ang.animate.set_value(ANG["D"]), run_time=2.2, rate_func=smooth)
        self.beat(0.6)

        num_l.clear_updaters()
        num_r.clear_updaters()
        live.clear_updaters()
        punch = self.say("Wherever D sits on the circle, the two sides stay exactly "
                         "equal.", color=GOLD, weight=BOLD)
        self.play(FadeOut(cap2), FadeIn(punch, shift=UP * 0.1),
                  Flash(num_l, color=GOOD, flash_radius=0.8),
                  Flash(num_r, color=GOOD, flash_radius=0.8), run_time=0.8)
        self.beat(2.2)
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Proof: two pairs of similar triangles
    # ====================================================================== #
    def scene_proof(self):
        header = self.section_header("Why it is true", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        A, B, C, D, K = _A, _B, _C, _D, _K
        fig = self._build_quad(colored=True, diag=True)
        base = VGroup(fig["circle"], fig["sides"], fig["diags"], fig["dots"], fig["labs"])
        self.play(Create(fig["circle"]), Create(fig["sides"]),
                  FadeIn(fig["dots"]), FadeIn(fig["labs"]), run_time=1.4)
        self.play(Create(fig["diags"]), run_time=0.9)
        cap = self.say("We prove it with two pairs of similar triangles.", color=MUTED)
        self.play(FadeIn(cap), run_time=0.5)
        self.beat(1.2)

        # --- the construction: K on AC with ∠ABK = ∠DBC --------------------- #
        kdot = vdot(K, GOLD, 0.075)
        klab = Text("K", font_size=28, color=GOLD, weight=BOLD)
        klab.move_to(K + np.array([0.17, -0.26, 0]))
        bk = seg(B, K, GOLD, 3.0)
        m1 = angle_mark(B, A, K, GOLD, radius=0.5, double=True)     # ∠ABK
        m2 = angle_mark(B, D, C, GOLD, radius=0.72, double=True)    # ∠DBC
        cap2 = self.say("Place K on diagonal AC so that angle ABK equals angle DBC.",
                        color=GOLD)
        self.play(FadeOut(cap), FadeIn(cap2), run_time=0.4)
        self.play(Create(bk), FadeIn(kdot, scale=0.6), FadeIn(klab), run_time=0.9)
        self.play(Create(m1), Create(m2), run_time=0.9)
        self.beat(1.8)

        # right-hand derivation column, built up line by line
        col_x = 3.15

        def dline(parts, buff=0.16):
            row = VGroup(*parts).arrange(RIGHT, buff=buff)
            return row

        line_sim1 = dline([Text("△ABK", 28, color=SIDE1, weight=BOLD),
                           Text("~", 28, color=MUTED),
                           Text("△DBC", 28, color=SIDE1, weight=BOLD)])
        line_eq1 = dline([Text("AK", 28, color=INK, weight=BOLD),
                          Text("·", 26, color=MUTED), Text("BD", 28, color=DIAG, weight=BOLD),
                          Text("=", 28, color=MUTED),
                          Text("AB", 28, color=SIDE1, weight=BOLD),
                          Text("·", 26, color=MUTED), Text("CD", 28, color=SIDE1, weight=BOLD)])
        line_sim2 = dline([Text("△CBK", 28, color=SIDE2, weight=BOLD),
                           Text("~", 28, color=MUTED),
                           Text("△DBA", 28, color=SIDE2, weight=BOLD)])
        line_eq2 = dline([Text("KC", 28, color=INK, weight=BOLD),
                          Text("·", 26, color=MUTED), Text("BD", 28, color=DIAG, weight=BOLD),
                          Text("=", 28, color=MUTED),
                          Text("BC", 28, color=SIDE2, weight=BOLD),
                          Text("·", 26, color=MUTED), Text("DA", 28, color=SIDE2, weight=BOLD)])
        deriv = VGroup(line_sim1, line_eq1, line_sim2, line_eq2)
        deriv.arrange(DOWN, aligned_edge=LEFT, buff=0.42)
        deriv.move_to([col_x, 1.6, 0])
        if deriv.get_right()[0] > 6.85:
            deriv.shift(LEFT * (deriv.get_right()[0] - 6.85))

        # --- pair 1: △ABK ~ △DBC -------------------------------------------- #
        t_abk = tri(A, B, K, SIDE1, op=0.5)
        t_dbc = tri(D, B, C, SIDE1, op=0.28)
        ins1a = angle_mark(A, B, C, SIDE1, radius=0.42)   # ∠BAC (= ∠BAK)
        ins1b = angle_mark(D, B, C, SIDE1, radius=0.42)   # ∠BDC
        cap3 = self.say("The angle at A and the angle at D stand on the same arc BC, "
                        "so they are equal.", color=SIDE1)
        self.play(FadeOut(cap2), FadeIn(cap3),
                  FadeIn(t_abk), FadeIn(t_dbc), run_time=0.7)
        self.play(Create(ins1a), Create(ins1b), run_time=0.7)
        self.beat(1.6)
        cap4 = self.say("With the equal angle at B, the two triangles are similar. "
                        "Matching their sides gives AK·BD = AB·CD.", color=SIDE1)
        self.play(FadeOut(cap3), FadeIn(cap4),
                  FadeIn(line_sim1, shift=UP * 0.1), run_time=0.7)
        # morph the small triangle onto the big one: literally the similarity map
        morph1 = t_abk.copy().set_fill(SIDE1, opacity=0.75)
        self.add(morph1)
        self.play(Transform(morph1, tri(D, B, C, SIDE1, op=0.75)), run_time=1.1)
        self.play(FadeOut(morph1), run_time=0.3)
        self.play(FadeIn(line_eq1, shift=UP * 0.1), run_time=0.7)
        self.beat(1.6)
        self.play(FadeOut(ins1a), FadeOut(ins1b),
                  FadeOut(t_abk), FadeOut(t_dbc), run_time=0.5)

        # --- pair 2: △CBK ~ △DBA -------------------------------------------- #
        t_cbk = tri(C, B, K, SIDE2, op=0.5)
        t_dba = tri(D, B, A, SIDE2, op=0.28)
        ins2a = angle_mark(C, A, B, SIDE2, radius=0.42)   # ∠BCA (= ∠BCK)
        ins2b = angle_mark(D, A, B, SIDE2, radius=0.60)   # ∠BDA
        cap5 = self.say("The same trick on arc AB makes a second similar pair, giving "
                        "KC·BD = BC·DA.", color=SIDE2)
        self.play(FadeOut(cap4), FadeIn(cap5),
                  FadeIn(t_cbk), FadeIn(t_dba), run_time=0.7)
        self.play(Create(ins2a), Create(ins2b),
                  FadeIn(line_sim2, shift=UP * 0.1), run_time=0.7)
        morph2 = t_cbk.copy().set_fill(SIDE2, opacity=0.75)
        self.add(morph2)
        self.play(Transform(morph2, tri(D, B, A, SIDE2, op=0.75)), run_time=1.1)
        self.play(FadeOut(morph2), run_time=0.3)
        self.play(FadeIn(line_eq2, shift=UP * 0.1), run_time=0.7)
        self.beat(1.6)
        self.play(FadeOut(ins2a), FadeOut(ins2b),
                  FadeOut(t_cbk), FadeOut(t_dba), run_time=0.5)

        # --- add them: (AK + KC)·BD = AC·BD --------------------------------- #
        rule = Line(deriv.get_left(), deriv.get_left() + RIGHT * 4.3,
                    stroke_color=MUTED, stroke_width=2)
        rule.next_to(deriv, DOWN, aligned_edge=LEFT, buff=0.35)
        add_line = dline([Text("(AK + KC)", 27, color=INK, weight=BOLD),
                          Text("·", 25, color=MUTED), Text("BD", 27, color=DIAG, weight=BOLD),
                          Text("=", 27, color=MUTED),
                          Text("AB·CD", 27, color=SIDE1, weight=BOLD),
                          Text("+", 25, color=MUTED),
                          Text("BC·DA", 27, color=SIDE2, weight=BOLD)])
        add_line.next_to(rule, DOWN, aligned_edge=LEFT, buff=0.3)
        avail = 6.85 - rule.get_left()[0]
        self.clamp_w(add_line, avail).align_to(rule, LEFT)
        cap6 = self.say("Add the two lines. On the left, AK + KC is the whole diagonal "
                        "AC.", color=INK)
        self.play(FadeOut(cap5), FadeIn(cap6), Create(rule),
                  FadeIn(add_line, shift=UP * 0.1), run_time=0.9)
        # flash the whole diagonal AC on the figure
        self.play(Indicate(fig["d_ac"], color=GOLD, scale_factor=1.05),
                  Indicate(bk, color=GOLD, scale_factor=1.0), run_time=1.0)
        self.beat(1.4)

        result, _ = theorem_eq(fs=32)
        qed = Text("∎", font_size=32, color=GOLD, weight=BOLD)
        res_grp = VGroup(result, qed).arrange(RIGHT, buff=0.32)
        res_grp.next_to(add_line, DOWN, buff=0.5).align_to(rule, LEFT)
        self.clamp_w(res_grp, avail).align_to(rule, LEFT)
        rbox = SurroundingRectangle(result, color=GOLD, buff=0.18, corner_radius=0.1)
        cap7 = self.say("The two products add up to the diagonal product. That is "
                        "Ptolemy's theorem.", color=GOLD, weight=BOLD)
        self.play(FadeOut(cap6), FadeIn(cap7),
                  TransformFromCopy(add_line, result), run_time=1.0)
        self.play(Create(rbox), FadeIn(qed), run_time=0.7)
        self.beat(2.4)
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Pythagoras: the rectangle special case
    # ====================================================================== #
    def scene_pythagoras(self):
        header = self.section_header("A rectangle hides Pythagoras", SIDE1)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        rc = np.array([-3.1, 0.1, 0.0])
        w, h = 3.4, 2.2                      # b (horizontal), a (vertical)
        Rr = np.hypot(w / 2, h / 2)
        A = rc + np.array([-w / 2, h / 2, 0])    # top-left
        B = rc + np.array([-w / 2, -h / 2, 0])   # bottom-left
        C = rc + np.array([w / 2, -h / 2, 0])    # bottom-right
        D = rc + np.array([w / 2, h / 2, 0])     # top-right
        a_val, b_val = h, w
        d_val = float(np.hypot(w, h))
        assert abs(d_val**2 - (a_val**2 + b_val**2)) < 1e-9

        circle = Circle(radius=Rr, color=RING, stroke_width=3).move_to(rc)
        s_ab = seg(A, B, SIDE1); s_cd = seg(C, D, SIDE1)     # verticals = a
        s_bc = seg(B, C, SIDE2); s_da = seg(D, A, SIDE2)     # horizontals = b
        dots = VGroup(*[vdot(p) for p in (A, B, C, D)])
        labs = VGroup(vlabel("A", A, rc, buff=0.3), vlabel("B", B, rc, buff=0.3),
                      vlabel("C", C, rc, buff=0.3), vlabel("D", D, rc, buff=0.3))
        self.play(Create(circle), run_time=0.8)
        self.play(Create(VGroup(s_ab, s_bc, s_cd, s_da)), FadeIn(dots), FadeIn(labs),
                  run_time=1.2)
        cap = self.say("Take the special case where ABCD is a rectangle.", color=INK)
        self.play(FadeIn(cap), run_time=0.5)
        self.beat(1.2)

        # side labels a, a, b, b
        la1 = Text("a", 26, color=SIDE1, weight=BOLD).next_to(s_ab, LEFT, buff=0.18)
        la2 = Text("a", 26, color=SIDE1, weight=BOLD).next_to(s_cd, RIGHT, buff=0.18)
        lb1 = Text("b", 26, color=SIDE2, weight=BOLD).next_to(s_bc, DOWN, buff=0.16)
        lb2 = Text("b", 26, color=SIDE2, weight=BOLD).next_to(s_da, UP, buff=0.16)
        self.play(FadeIn(VGroup(la1, la2, lb1, lb2), shift=UP * 0.05), run_time=0.7)
        self.beat(0.8)

        # the diagonals: equal, and each a diameter through the centre
        d_ac = seg(A, C, DIAG); d_bd = seg(B, D, DIAG)
        ld = Text("d", 26, color=DIAG, weight=BOLD).move_to(
            (A + C) / 2 + np.array([0.28, 0.24, 0]))
        cap2 = self.say("Both diagonals pass through the centre, so each is a "
                        "diameter, and they are equal: call it d.", color=DIAG)
        self.play(FadeOut(cap), FadeIn(cap2), Create(d_ac), Create(d_bd), run_time=1.0)
        self.play(FadeIn(ld), run_time=0.4)
        self.beat(1.6)

        # Ptolemy -> d*d = a*a + b*b
        eq1, _ = theorem_eq(fs=34)
        eq1.move_to([3.2, 2.1, 0])
        self.clamp_w(eq1, 6.6)
        self.play(FadeOut(cap2), FadeIn(eq1, shift=DOWN * 0.1), run_time=0.7)

        def Tt(s, c, w=BOLD, fs=32):
            return Text(s, font_size=fs, color=c, weight=w)

        sub = VGroup(
            Tt("d", DIAG), Tt("·", MUTED, NORMAL), Tt("d", DIAG),
            Tt("=", MUTED, NORMAL),
            Tt("a", SIDE1), Tt("·", MUTED, NORMAL), Tt("a", SIDE1),
            Tt("+", MUTED, NORMAL),
            Tt("b", SIDE2), Tt("·", MUTED, NORMAL), Tt("b", SIDE2),
        ).arrange(RIGHT, buff=0.18)
        sub.next_to(eq1, DOWN, buff=0.55)
        self.clamp_w(sub, 6.6)
        cap3 = self.say("Opposite sides are equal, and both diagonals are d, so "
                        "Ptolemy becomes:", color=INK)
        self.play(FadeIn(cap3), FadeIn(sub, shift=UP * 0.1), run_time=0.8)
        self.beat(1.4)

        pyth = VGroup(
            squared("d", DIAG, 44), Text("=", font_size=44, color=MUTED),
            squared("a", SIDE1, 44), Text("+", font_size=44, color=MUTED),
            squared("b", SIDE2, 44),
        ).arrange(RIGHT, buff=0.26)
        pyth.next_to(sub, DOWN, buff=0.6)
        box = SurroundingRectangle(pyth, color=GOLD, buff=0.2, corner_radius=0.1)
        self.play(FadeOut(cap3), FadeIn(pyth, shift=UP * 0.1), run_time=0.9)
        self.play(Create(box), run_time=0.6)
        self.beat(1.2)

        # highlight the right triangle ABC (right angle at B, Thales)
        rt = tri(A, B, C, GOLD, op=0.2)
        rmark = right_angle_mark(B, A, C, color=INK, size=0.3)
        cap4 = self.say("That is the Pythagorean theorem: triangle ABC is "
                        "right-angled at B, with hypotenuse d.", color=GOLD, weight=BOLD)
        self.play(FadeIn(rt), Create(rmark), FadeIn(cap4, shift=UP * 0.1), run_time=0.9)
        self.play(Indicate(pyth, color=GOLD, scale_factor=1.08), run_time=1.0)
        self.beat(2.4)
        self.wipe()

    # ---- full film (2D part only; the 3D Space scene stands alone) --------- #
    def play_all_2d(self):
        self.play_intro()
        self.scene_setup()
        self.scene_check()
        self.scene_proof()
        self.scene_pythagoras()


# ========================================================================== #
# Scene 5 — Space (3D): equality lives on the circle
# ========================================================================== #
class Space(_Common, ThreeDScene):
    def hud_swap(self, old, new, rt=0.5):
        self.add_fixed_in_frame_mobjects(new)
        self.play(FadeOut(old), FadeIn(new), run_time=rt)

    def construct(self):
        self.camera.background_color = BG

        c0 = np.array([-2.35, -0.55, 0.0])
        R3 = 2.05
        ang = dict(A=145, B=212, C=308, D=44)
        A = cpt(c0, R3, ang["A"]); B = cpt(c0, R3, ang["B"])
        C = cpt(c0, R3, ang["C"]); Dbase = cpt(c0, R3, ang["D"])
        h_lift = 2.1
        Dtop = Dbase + np.array([0, 0, h_lift])

        # real products on and off the circle (asserted)
        def products(Dp):
            lhs = dist(A, C) * dist(B, Dp)
            rhs = dist(A, B) * dist(C, Dp) + dist(B, C) * dist(Dp, A)
            return lhs, rhs

        lhs0, rhs0 = products(Dbase)
        lhs1, rhs1 = products(Dtop)
        assert abs(lhs0 - rhs0) < 1e-9, (lhs0, rhs0)      # equal on the circle
        assert lhs1 < rhs1 - 0.3, (lhs1, rhs1)            # strictly less off it

        # the circle (ring) lying in the z = 0 plane
        ring = Circle(radius=R3, color=RING, stroke_width=3).move_to(c0)
        disc = Circle(radius=R3, color=RING, stroke_width=0,
                      fill_color=RING, fill_opacity=0.05).move_to(c0)
        dot_A = Dot3D(A, radius=0.08, color=INK)
        dot_B = Dot3D(B, radius=0.08, color=INK)
        dot_C = Dot3D(C, radius=0.08, color=INK)
        dot_D = Dot3D(Dbase, radius=0.09, color=GOLD)

        s_ab = seg(A, B, SIDE1); s_bc = seg(B, C, SIDE2)
        s_cd = seg(C, Dbase, SIDE1); s_da = seg(Dbase, A, SIDE2)
        d_ac = seg(A, C, DIAG); d_bd = seg(B, Dbase, DIAG)

        # billboard vertex labels
        lA = Text("A", font_size=26, color=INK, weight=BOLD).move_to(A + unit(A - c0) * 0.35)
        lB = Text("B", font_size=26, color=INK, weight=BOLD).move_to(B + unit(B - c0) * 0.35)
        lC = Text("C", font_size=26, color=INK, weight=BOLD).move_to(C + unit(C - c0) * 0.35)
        lD = Text("D", font_size=26, color=GOLD, weight=BOLD).move_to(Dbase + unit(Dbase - c0) * 0.35)

        header = self.section_header("Equality lives on the circle", GOLD)

        self.set_camera_orientation(phi=62 * DEGREES, theta=-72 * DEGREES, zoom=0.88)
        self.add_fixed_in_frame_mobjects(header)
        self.play(FadeIn(header), run_time=0.6)
        self.play(FadeIn(disc), Create(ring), run_time=1.1)
        self.play(*[GrowFromCenter(d) for d in (dot_A, dot_B, dot_C, dot_D)], run_time=0.7)
        self.add_fixed_orientation_mobjects(lA, lB, lC, lD)
        self.play(Create(VGroup(s_ab, s_bc, s_cd, s_da)), run_time=1.0)
        self.play(Create(d_ac), Create(d_bd), run_time=0.8)

        # --- the scoreboard (fixed in frame, top-right) --------------------- #
        lab_l = VGroup(Text("AC · BD", font_size=25, color=DIAG, weight=BOLD),
                       Text("=", font_size=25, color=MUTED)).arrange(RIGHT, buff=0.18)
        lab_r = VGroup(Text("AB·CD", font_size=25, color=SIDE1, weight=BOLD),
                       Text("+", font_size=25, color=MUTED),
                       Text("BC·DA", font_size=25, color=SIDE2, weight=BOLD),
                       Text("=", font_size=25, color=MUTED)).arrange(RIGHT, buff=0.14)
        lab_g = VGroup(Text("shortfall", font_size=25, color=MUTED),
                       Text("=", font_size=25, color=MUTED)).arrange(RIGHT, buff=0.18)
        labs = VGroup(lab_l, lab_r, lab_g).arrange(DOWN, aligned_edge=RIGHT, buff=0.42)

        def mk_num(val, col, lab):
            return Text(f"{val:.2f}", font_size=29, color=col, weight=BOLD).next_to(
                lab, RIGHT, buff=0.22)

        num_l = mk_num(lhs0, GOLD, lab_l)
        num_r = mk_num(rhs0, GOLD, lab_r)
        num_g = mk_num(0.0, GOOD, lab_g)
        board = VGroup(labs, num_l, num_r, num_g)
        board.to_corner(UR, buff=0.5).shift(DOWN * 0.2)   # group first, THEN corner
        verdict = Text("the two sides are equal", font_size=24, color=GOOD, weight=BOLD)
        verdict.next_to(board, DOWN, buff=0.45).align_to(board, RIGHT)
        self.add_fixed_in_frame_mobjects(board, verdict)
        self.play(FadeIn(board), FadeIn(verdict), run_time=0.8)

        cap = self.say("With all four points on the circle, the two sides are exactly "
                       "equal.", color=INK)
        self.add_fixed_in_frame_mobjects(cap)
        self.play(FadeIn(cap), run_time=0.6)
        self.begin_ambient_camera_rotation(rate=0.055)
        self.beat(1.8)

        # --- lift D up out of the plane ------------------------------------- #
        guide = dseg(Dbase, Dtop, GOLD, 2.5)
        cap2 = self.say("Now lift point D straight up, off the plane of the circle.",
                        color=GOLD)
        self.hud_swap(cap, cap2)
        self.play(
            dot_D.animate.move_to(Dtop),
            lD.animate.move_to(Dtop + unit(Dbase - c0) * 0.33 + np.array([0, 0, 0.12])),
            Transform(s_cd, seg(C, Dtop, SIDE1)),
            Transform(s_da, seg(Dtop, A, SIDE2)),
            Transform(d_bd, seg(B, Dtop, DIAG)),
            Create(guide),
            run_time=2.4,
        )
        # scoreboard update: the two products diverge, the shortfall opens up.
        # Swap the whole numbers by fade (never Transform a number->number: it
        # glyph-morphs into a garbled overlap mid-transition).
        new_l = mk_num(lhs1, GOLD, lab_l)
        new_r = mk_num(rhs1, GOLD, lab_r)
        new_g = mk_num(rhs1 - lhs1, BAD, lab_g)
        new_verdict = Text("AC · BD now falls short", font_size=24, color=BAD, weight=BOLD)
        new_verdict.move_to(verdict, RIGHT)
        # fade the old values out FIRST, then add + fade the new ones in (adding
        # them earlier would show them at full opacity over the fading old ones).
        old_board = VGroup(num_l, num_r, num_g, verdict)
        self.play(FadeOut(old_board), run_time=0.35)
        self.add_fixed_in_frame_mobjects(new_l, new_r, new_g, new_verdict)
        self.play(FadeIn(VGroup(new_l, new_r, new_g, new_verdict)), run_time=0.45)
        self.play(Indicate(new_g, color=BAD, scale_factor=1.3), run_time=0.6)
        num_l, num_r, num_g, verdict = new_l, new_r, new_g, new_verdict
        cap3 = self.say("Off the circle, the diagonal product is strictly smaller "
                        "than the sum of the opposite-side products.", color=BAD)
        self.hud_swap(cap2, cap3)
        self.beat(2.2)

        # --- return D to the circle: equality snaps back -------------------- #
        cap4 = self.say("Bring D back down onto the circle, and equality snaps back.",
                        color=GOOD)
        self.hud_swap(cap3, cap4)
        back_l = mk_num(lhs0, GOLD, lab_l)
        back_r = mk_num(rhs0, GOLD, lab_r)
        back_g = mk_num(0.0, GOOD, lab_g)
        back_verdict = Text("the two sides are equal", font_size=24, color=GOOD, weight=BOLD)
        back_verdict.move_to(verdict, RIGHT)
        # geometry returns while the "fallen-short" numbers fade out with it...
        self.play(
            dot_D.animate.move_to(Dbase),
            lD.animate.move_to(Dbase + unit(Dbase - c0) * 0.35),
            Transform(s_cd, seg(C, Dbase, SIDE1)),
            Transform(s_da, seg(Dbase, A, SIDE2)),
            Transform(d_bd, seg(B, Dbase, DIAG)),
            FadeOut(guide),
            FadeOut(VGroup(num_l, num_r, num_g, verdict)),
            run_time=2.2,
        )
        # ...then the equal-state numbers snap back in (add only now, so they
        # never sit at full opacity over the fading old ones)
        self.add_fixed_in_frame_mobjects(back_l, back_r, back_g, back_verdict)
        self.play(FadeIn(VGroup(back_l, back_r, back_g, back_verdict)), run_time=0.5)
        self.play(Indicate(back_g, color=GOOD, scale_factor=1.2), run_time=0.5)
        num_l, num_r, num_g, verdict = back_l, back_r, back_g, back_verdict
        self.beat(1.4)

        self.stop_ambient_camera_rotation()
        punch = self.say("Equality holds exactly when the four points share one "
                         "circle. That is what Ptolemy's theorem captures.",
                         color=GOLD, weight=BOLD)
        self.hud_swap(cap4, punch)
        self.beat(2.4)

        self.wait(END_HOLD)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)


# ========================================================================== #
# Scene 6 — Recap card
# ========================================================================== #
class Recap(_PtolBase):
    def construct(self):
        self.scene_recap()

    def scene_recap(self):
        title = Text("Ptolemy's Theorem", font_size=44, color=INK, weight=BOLD)
        title.to_edge(UP, buff=0.9)
        eq, _ = theorem_eq(fs=42)
        self.clamp_w(eq, 10.5).next_to(title, DOWN, buff=0.5)
        rule = Line([eq.get_left()[0] - 0.5, 0, 0], [eq.get_right()[0] + 0.5, 0, 0])
        rule.set_stroke(GOLD, 3).next_to(eq, DOWN, buff=0.45)
        self.play(FadeIn(title, shift=DOWN * 0.1), run_time=0.6)
        self.play(Write(eq), Create(rule), run_time=1.4)
        self.beat(1.0)

        items = [
            ("It holds for any four points on a circle,", GOOD),
            ("we proved it with two pairs of similar triangles,", SIDE1),
            ("a rectangle turns it into the Pythagorean theorem,", DIAG),
            ("and equality breaks the moment a point leaves the circle.", GOLD),
        ]
        rows = VGroup()
        for s, col in items:
            d = Dot(radius=0.06, color=col)
            t = Text(s, font_size=26, color=INK)
            row = VGroup(d, t).arrange(RIGHT, buff=0.25)
            rows.add(row)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.34).next_to(rule, DOWN, buff=0.5)
        self.clamp_w(rows, 11.5)
        for row in rows:
            self.play(FadeIn(row, shift=RIGHT * 0.12), run_time=0.5)
            self.beat(0.6)
        self.beat(1.0)

        note = Text("Ptolemy used it around 150 AD to build the first table of "
                    "chords: the ancestor of trigonometry.",
                    font_size=23, color=MUTED)
        self.clamp_w(note, 11.5).to_edge(DOWN, buff=0.7)
        self.play(FadeIn(note, shift=UP * 0.1), run_time=0.7)
        self.beat(2.4)
        self.wipe()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_PtolBase):
    def construct(self):
        self.play_intro()


class Setup(_PtolBase):
    def construct(self):
        self.scene_setup()


class Check(_PtolBase):
    def construct(self):
        self.scene_check()


class Proof(_PtolBase):
    def construct(self):
        self.scene_proof()


class Pythagoras(_PtolBase):
    def construct(self):
        self.scene_pythagoras()


class Outro(_PtolBase):
    def construct(self):
        self.play_outro()


if __name__ == "__main__":
    # Render the 2D portion end-to-end; the 3D Space scene renders separately
    # and the whole film is assembled by ./render.sh --stitch.
    class _Film2D(_PtolBase):
        def construct(self):
            self.play_all_2d()

    _Film2D().render()

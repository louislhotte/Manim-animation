"""The Jacobian Conjecture — a short, house-style explainer.

A famous 87-year-old problem in algebraic geometry — and how, in July 2026, an
explicit counterexample was found with an AI in the loop.

    The Jacobian Conjecture (O.-H. Keller, 1939)
    Let F : C^n -> C^n be a polynomial map whose Jacobian determinant det(DF)
    is a nonzero constant.  Then F is invertible (with a polynomial inverse).

For 87 years it stood: proved for n = 1, open for n = 2, believed true for all
n.  Experts guessed the smallest counterexample, if one existed, would need a
huge degree.  Then Levent Alpoge, with Anthropic's Claude Fable 5, produced an
explicit degree-7 map  F : C^3 -> C^3  with det(DF) = -2 that is NOT injective:

    F1 = (1+z1*z2)**3*z3 + z2**2*(1+z1*z2)*(4+3*z1*z2)
    F2 = z2 + 3*z1*(1+z1*z2)**2*z3 + 3*z1*z2**2*(4+3*z1*z2)
    F3 = 2*z1 - 3*z1**2*z2 - z1**3*z3

    F(0, 0, -1/4) = F(1, -3/2, 13/2) = F(-1, 3/2, 13/2) = (-1/4, 0, 0)

Three distinct inputs, one image -> not one-to-one -> not invertible.  The
conjecture is false for every dimension n >= 3.  (n = 2 remains open.)  Terence
Tao published a "digestion" explaining why the construction works.  Every number
above was machine-checked before this film was drawn (see verify in README).

All text is ``Text`` (Pango), no LaTeX.  Scenes render individually
(``Intro``, ``Conjecture``, ``Intuition``, ``Counterexample``, ``Collision``,
``Significance``, ``Outro``) or as one film (``JacobianConjecture``).

Env knobs:
    JC_QUICK=1   collapse every hold for a fast layout render
    JC_DELAY=<s> override the reading-rhythm multiplier
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

QUICK = os.environ.get("JC_QUICK") == "1"
# Reading rhythm. Bumped to 2.4 so formula-heavy screens have real time to read.
DELAY = float(os.environ.get("JC_DELAY", 0.28 if QUICK else 2.4))
ANIM_SLOW = 1.0 if QUICK else 1.15
END_HOLD = 0.2 if QUICK else 2.4

# ---- palette (shared with the Transformer / KV-cache series) -------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
FAINT = "#3A4152"       # hairlines, faint structure
AX1 = "#5B8DEF"         # first axis / coordinate z1 (blue)
AX2 = "#2EC4B6"         # second axis / coordinate z2 (teal)
AX3 = "#FFD166"         # third axis / coordinate z3 (gold)
PA = "#C792EA"          # point a (violet)
PB = "#FF8C42"          # point b (orange)
PC = "#3DD68C"          # point c (green)
GOLD = "#FFD166"        # the map F / accent
ACCENT = "#FFD166"
GOOD = "#3DD68C"        # pass / verified
BAD = "#FF5C5C"         # false / stop
CODE_FS = 21
MONO = "Menlo"

# 'C' for the complex numbers.  Blackboard-bold U+2102 is not in Helvetica Neue,
# so we render a bold serif capital C and italicise it slightly to read as a
# math symbol.  (Verified against a glyph probe render.)
CSYM = "C"

FONT = "Helvetica Neue"

# --- crisp small text -------------------------------------------------------
# Pango mangles glyphs/spacing below ~20 pt (subscripts came out in a fallback
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


def harrow(start, end, color=MUTED, sw=4):
    return Arrow(start, end, buff=0.12, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.2, tip_length=0.22)


def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners([np.array([-0.2, 0.0, 0]),
                             np.array([-0.05, -0.18, 0]),
                             np.array([0.24, 0.22, 0])])
    v.set_stroke(color=color, width=sw)
    return v.scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.18, -0.18, 0], [0.18, 0.18, 0])
    b = Line([-0.18, 0.18, 0], [0.18, -0.18, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


def mtext(parts, base_fs=32):
    """Inline 'formula' from Text pieces. Each part: (s, role[, color]),
    role in {"b" base, "^" super, "_" sub}. Supers/subs attach to prev base."""
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
            m = Text(s, font_size=int(base_fs * 0.62), color=col)
            anchor = last_base if last_base is not None else grp
            m.next_to(anchor, RIGHT, buff=0.02)
            m.align_to(anchor, UP if role == "^" else DOWN)
            grp.add(m)
    return grp


def cspace(n, base_fs=34, color=INK):
    """The symbol  C^n  (complex n-space)."""
    return mtext([(CSYM, "b", color), (str(n), "^", color)], base_fs=base_fs)


# ---- isometric projection for the 3-D "space" scene ----------------------- #
_EX = np.array([0.96, -0.26, 0.0])   # z1 axis on screen  (right, tilt down)
_EY = np.array([-0.66, -0.40, 0.0])  # z2 axis on screen  (back-left)
_EZ = np.array([0.0, 1.0, 0.0])      # z3 axis on screen  (up)


def iso(p, center, s=1.0):
    x, y, z = p
    return np.array(center) + s * (x * _EX + y * _EY + z * _EZ)


# ========================================================================== #
class _JacBase(Scene):
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

    def say(self, s, color=INK, fs=26, italic=False, buff=0.42):
        """One-line caption on the bottom band, auto-fit to a safe width."""
        m = txt(s, fs=fs, color=color, slant=ITALIC if italic else None)
        if m.width > 12.6:
            m.scale_to_fit_width(12.6)
        m.to_edge(DOWN, buff=buff)
        return m

    def cite(self):
        t = txt("after T. Tao, “A digestion of the Jacobian conjecture counterexample” (2026)",
                fs=15, color=MUTED, slant=ITALIC).to_edge(DOWN, buff=0.16)
        return t

    # ---- code panel (house helper) ---------------------------------------- #
    def code_panel(self, spec, table, title="counterexample.py", fs=CODE_FS,
                   indent_unit=0.5, line_buff=0.19, target_h=5.4, target_w=11.4):
        lines = []
        for indent, s in spec:
            if s == "":
                m = Rectangle(width=0.02, height=0.28, fill_opacity=0, stroke_opacity=0)
            elif s.lstrip().startswith("#"):
                m = txt(s, fs=fs, color=MUTED, font=MONO, slant=ITALIC)
            else:
                m = Text(s, font=MONO, font_size=fs, color=INK, t2c=_safe_t2c(s, table))
            m._indent = indent
            lines.append(m)
        code = VGroup(*lines).arrange(DOWN, aligned_edge=LEFT, buff=line_buff)
        for m in lines:
            m.shift(RIGHT * indent_unit * m._indent)
        f = min(target_h / code.height, target_w / code.width)
        if f < 1:
            code.scale(f)
        bg = RoundedRectangle(width=code.width + 0.9, height=code.height + 1.15,
                              corner_radius=0.16, stroke_color=FAINT, stroke_width=2,
                              fill_color="#0A0E15", fill_opacity=1.0).move_to(code)
        bar = RoundedRectangle(width=bg.width, height=0.5, corner_radius=0.16,
                               stroke_width=0, fill_color="#141C29", fill_opacity=1.0)
        bar.move_to(bg).align_to(bg, UP)
        dots = VGroup(*[Dot(radius=0.045, color=c)
                        for c in ("#FF5F57", "#FEBC2E", "#28C840")]).arrange(RIGHT, buff=0.11)
        dots.move_to([bg.get_left()[0] + 0.42, bar.get_center()[1], 0])
        ttl = txt(title, fs=15, color=MUTED, font=MONO)
        ttl.next_to(dots, RIGHT, buff=0.34).set_y(bar.get_center()[1])
        code.shift(DOWN * 0.22)
        panel = VGroup(bg, bar, dots, ttl, code)
        panel.code = code
        panel.lines = lines
        return panel

    # ---- house intro / outro cards ---------------------------------------- #
    def _rule_under(self, header, pad=1.0, color=GOLD, drop=0.45):
        return Line([header.get_left()[0] - pad, header.get_bottom()[1] - drop, 0],
                    [header.get_right()[0] + pad, header.get_bottom()[1] - drop, 0]
                    ).set_stroke(width=3, color=color)

    def play_intro(self):
        header = Text("The Jacobian Conjecture", font_size=54, color=INK, weight="BOLD")
        header.set(width=min(10.2, header.width))
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=AX1)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        sub = Text("An 87-year-old problem — and how AI broke it", font_size=32, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        src = Text("counterexample by L. Alpöge × Claude Fable 5, 2026",
                   font_size=21, color=MUTED)
        src.next_to(writer, DOWN, buff=0.4)
        self.play(FadeIn(src), run_time=0.8)
        self.card_wait(2.0)
        self.play(FadeOut(VGroup(header, writer, line, src)), run_time=1.0)
        self.card_wait(0.3)

    def play_hook(self):
        """Cold open: F folds a grid onto itself; det J = -2. (Image #5 look.)"""
        ext = 3.3
        gvals = np.linspace(-ext, ext, 13)
        samp = np.linspace(-ext, ext, 44)

        def mkgrid(warp):
            g = VGroup()
            for gx in gvals:
                g.add(VMobject().set_points_smoothly([warp(np.array([gx, y, 0.0])) for y in samp]))
            for gy in gvals:
                g.add(VMobject().set_points_smoothly([warp(np.array([x, gy, 0.0])) for x in samp]))
            return g.set_stroke(AX2, width=1.6, opacity=0.7)

        def swirl(p):
            x, y = p[0], p[1]
            a = 2.1 * np.exp(-(x * x + y * y) / 2.4)
            ca, sa = np.cos(a), np.sin(a)
            return np.array([ca * x - sa * y, sa * x + ca * y, 0.0])

        straight = mkgrid(lambda p: p)
        warped = mkgrid(swirl)
        glow = VGroup(*[Circle(radius=r, stroke_width=0, fill_color=GOLD, fill_opacity=op)
                        for r, op in [(0.62, 0.10), (0.40, 0.18), (0.22, 0.95)]])
        detj = mtext([("det J = -2", "b", INK)], base_fs=34)
        djbox = RoundedRectangle(width=detj.width + 0.5, height=detj.height + 0.42,
                                 corner_radius=0.12, stroke_color=GOLD, stroke_width=2,
                                 fill_color=BG, fill_opacity=0.92).move_to(detj)
        dj = VGroup(djbox, detj).to_corner(UR, buff=0.85)
        self.add(straight)
        self.play(Transform(straight, warped), run_time=2.4)
        self.play(FadeIn(glow, scale=0.6), run_time=0.8)
        self.play(FadeIn(dj, shift=DOWN * 0.2), run_time=0.7)
        self.card_wait(1.8)
        self.play(FadeOut(straight), FadeOut(glow), FadeOut(dj), run_time=0.9)
        self.card_wait(0.2)

    def play_outro(self):
        self.card_wait(0.4)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=AX1)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = Text("A constant Jacobian no longer means invertible — in dimension three and up.",
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
    # Scene 1 — what the conjecture says
    # ====================================================================== #
    def scene_conjecture(self):
        self.section_header("1 · The conjecture")

        # A polynomial map  F : C^n -> C^n
        title = txt("A polynomial map", fs=30, color=INK).to_edge(UP, buff=1.35)
        cn1, cn2 = cspace("n", 40), cspace("n", 40)
        fbox = chip("F", GOLD, w=1.15, h=1.0, fs=34)
        arr1 = harrow(ORIGIN, RIGHT * 1.0)
        arr2 = harrow(ORIGIN, RIGHT * 1.0, color=GOLD)
        row = VGroup(cn1, arr1, fbox, arr2, cn2).arrange(RIGHT, buff=0.4)
        row.next_to(title, DOWN, buff=0.5)
        self.play(FadeIn(title, shift=DOWN * 0.15), run_time=0.6)
        self.play(LaggedStart(FadeIn(cn1), GrowArrow(arr1), FadeIn(fbox),
                              GrowArrow(arr2), FadeIn(cn2), lag_ratio=0.35, run_time=1.8))
        # "each output coordinate is a polynomial in z1 ... zn" — subscripts via mtext
        subm = VGroup(txt("each output coordinate is a polynomial in", fs=24, color=MUTED),
                      mtext([("z", "b", MUTED), ("1", "_", MUTED), (", ... , ", "b", MUTED),
                             ("z", "b", MUTED), ("n", "_", MUTED)], base_fs=24)
                      ).arrange(RIGHT, buff=0.2)
        subm.next_to(row, DOWN, buff=0.5)
        self.play(FadeIn(subm), run_time=0.6)
        self.beat(1.4)
        self.play(FadeOut(subm), run_time=0.4)

        # The Jacobian matrix DF — a grid of partial derivatives
        jlabel = VGroup(txt("Its Jacobian", fs=28, color=INK),
                        mtext([("DF", "b", INK)], base_fs=28),
                        txt("= the grid of partial derivatives", fs=28, color=INK)
                        ).arrange(RIGHT, buff=0.22)
        jlabel.next_to(row, DOWN, buff=0.55)

        def cell(i, j):
            return mtext([("∂F", "b"), (str(i), "_"), ("/∂z", "b"), (str(j), "_")], base_fs=24)
        grid = VGroup(*[cell(i, j) for i in (1, 2, 3) for j in (1, 2, 3)])
        grid.arrange_in_grid(rows=3, cols=3, buff=(0.5, 0.4))
        lb = Line(grid.get_corner(UL) + LEFT * 0.18 + UP * 0.1,
                  grid.get_corner(DL) + LEFT * 0.18 + DOWN * 0.1).set_stroke(INK, 3)
        rb = Line(grid.get_corner(UR) + RIGHT * 0.18 + UP * 0.1,
                  grid.get_corner(DR) + RIGHT * 0.18 + DOWN * 0.1).set_stroke(INK, 3)
        matrix = VGroup(lb, grid, rb)
        matrix.next_to(jlabel, DOWN, buff=0.5)
        self.play(FadeIn(jlabel), run_time=0.6)
        self.play(FadeIn(matrix, lag_ratio=0.05), run_time=1.4)
        self.beat(1.6)

        # Its determinant — one number
        detm = VGroup(mtext([("det DF", "b", GOLD)], base_fs=30),
                      txt("collapses the grid to a single number", fs=26, color=MUTED)
                      ).arrange(RIGHT, buff=0.22)
        detm.next_to(matrix, DOWN, buff=0.55)
        self.play(FadeIn(detm, shift=UP * 0.15), run_time=0.7)
        self.beat(1.6)
        self.play(FadeOut(VGroup(title, row, jlabel, matrix, detm)), run_time=0.6)

        # The hypothesis  ->  the claim
        hyp = VGroup(mtext([("det DF", "b", GOLD)], base_fs=34),
                     txt("is a nonzero constant", fs=30, color=INK)).arrange(RIGHT, buff=0.24)
        note = txt("never locally squished — invertible near every single point",
                   fs=23, color=MUTED)
        big_arrow = Arrow(UP * 0.55, DOWN * 0.55, buff=0.0, stroke_width=8, color=GOOD,
                          max_tip_length_to_length_ratio=0.4)
        claim = txt("F is globally invertible", fs=34, color=GOOD, weight="BOLD")
        claim_note = VGroup(txt("one input for every output — with a polynomial inverse", fs=23, color=MUTED),
                            mtext([("F", "b", MUTED), ("-1", "^", MUTED)], base_fs=23)
                            ).arrange(RIGHT, buff=0.16)

        hyp.to_edge(UP, buff=1.5)
        note.next_to(hyp, DOWN, buff=0.28)
        big_arrow.next_to(note, DOWN, buff=0.4)
        claim.next_to(big_arrow, DOWN, buff=0.4)
        claim_note.next_to(claim, DOWN, buff=0.28)
        self.play(FadeIn(hyp, shift=DOWN * 0.1), run_time=0.7)
        self.play(FadeIn(note), run_time=0.5)
        self.beat(1.2)
        self.play(GrowArrow(big_arrow), run_time=0.6)
        self.play(FadeIn(claim, shift=DOWN * 0.1), run_time=0.7)
        self.play(FadeIn(claim_note), run_time=0.5)
        self.beat(1.2)

        punch = self.say("Local invertibility  →  global invertibility?  For 87 years, the guess was yes.",
                         color=ACCENT)
        self.play(FadeIn(punch, shift=UP * 0.15), run_time=0.7)
        self.beat(1.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — why everyone believed it (1-D) + the subtlety + the wall
    # ====================================================================== #
    def scene_intuition(self):
        self.section_header("2 · Why everyone believed it")

        lead = VGroup(txt("In one variable it is obvious.  If", fs=27, color=INK),
                      mtext([("F", "b"), ("'", "^"), ("(z) = a", "b")], base_fs=27),
                      txt("is constant …", fs=27, color=INK)).arrange(RIGHT, buff=0.2)
        lead.to_edge(UP, buff=1.35)
        self.play(FadeIn(lead, shift=DOWN * 0.12), run_time=0.7)

        # a straight line on a small pair of axes
        axes = Axes(x_range=[-3, 3, 1], y_range=[-3, 3, 1], x_length=4.6, y_length=4.6,
                    axis_config=dict(stroke_color=FAINT, stroke_width=2,
                                     include_ticks=False, include_tip=False))
        axes.next_to(lead, DOWN, buff=0.5).to_edge(LEFT, buff=1.3)
        graph = axes.plot(lambda x: 0.8 * x + 0.5, x_range=[-2.7, 2.7], stroke_color=AX1, stroke_width=5)
        glabel = VGroup(mtext([("F(z) = a z + b", "b", AX1)], base_fs=26))
        glabel.next_to(axes, UP, buff=0.12).align_to(axes, RIGHT)
        self.play(Create(axes), run_time=0.8)
        self.play(Create(graph), FadeIn(glabel), run_time=1.0)

        # horizontal-line test: one output <-> one input
        yv = 1.4
        hline = DashedLine(axes.c2p(-2.7, yv), axes.c2p(2.7, yv), stroke_color=PB, stroke_width=3)
        xhit = (yv - 0.5) / 0.8
        hit = Dot(axes.c2p(xhit, yv), color=PB, radius=0.09)
        drop = DashedLine(axes.c2p(xhit, yv), axes.c2p(xhit, -3), stroke_color=PB, stroke_width=2)
        self.play(Create(hline), run_time=0.6)
        self.play(FadeIn(hit, scale=1.4), Create(drop), run_time=0.6)
        oneone = txt("one output  ↔  exactly one input", fs=24, color=PB)
        oneone.next_to(axes, DOWN, buff=0.3)
        self.play(FadeIn(oneone), run_time=0.5)
        self.beat(1.2)
        conc = VGroup(txt("… a straight line.", fs=27, color=INK),
                      txt("Invertible.", fs=27, color=GOOD, weight="BOLD"),
                      make_tick().scale(1.1)).arrange(RIGHT, buff=0.22)
        conc.next_to(lead, DOWN, buff=0.5).to_edge(RIGHT, buff=1.5)
        self.play(FadeIn(conc[0]), run_time=0.4)
        self.play(FadeIn(conc[1]), Create(conc[2]), run_time=0.5)
        # a small theorem badge for n = 1
        thm = VGroup(mtext([("n = 1", "b", GOOD)], base_fs=26),
                     txt("proved.", fs=24, color=MUTED)).arrange(RIGHT, buff=0.18)
        thm.next_to(conc, DOWN, buff=0.9).align_to(conc, LEFT)
        self.play(FadeIn(thm, shift=UP * 0.1), run_time=0.5)
        self.beat(1.4)

        # THE CATCH
        self.play(FadeOut(VGroup(axes, graph, glabel, hline, hit, drop, oneone, conc, thm, lead)),
                  run_time=0.5)
        catch = txt("But in higher dimensions there is room to hide:", fs=29, color=INK).to_edge(UP, buff=1.4)
        self.play(FadeIn(catch, shift=DOWN * 0.1), run_time=0.6)
        catch2 = VGroup(mtext([("det DF", "b", GOLD)], base_fs=30),
                        txt("can stay constant while every entry twists and bends.", fs=27, color=INK)
                        ).arrange(RIGHT, buff=0.22)
        catch2.next_to(catch, DOWN, buff=0.45)
        self.play(FadeIn(catch2), run_time=0.7)

        # a 3x3 of wiggling entries whose determinant stays pinned
        def wig():
            return mtext([("∂F", "b"), ("i", "_"), ("/∂z", "b"), ("j", "_")], base_fs=22)
        cells = VGroup(*[wig() for _ in range(9)]).arrange_in_grid(rows=3, cols=3, buff=(0.55, 0.42))
        pinned = VGroup(txt("=", fs=30, color=MUTED),
                        mtext([("const", "b", GOLD)], base_fs=28)).arrange(RIGHT, buff=0.16)
        grp = VGroup(cells, pinned).arrange(RIGHT, buff=0.7)
        det_label = mtext([("det", "b", MUTED)], base_fs=26).next_to(cells, LEFT, buff=0.2)
        block = VGroup(det_label, grp).arrange(RIGHT, buff=0.15)
        block.next_to(catch2, DOWN, buff=0.7)
        self.play(FadeIn(cells, lag_ratio=0.05), FadeIn(det_label), run_time=1.0)
        self.play(FadeIn(pinned), run_time=0.5)
        # jitter the entries to signal they vary, while the constant holds
        for _ in range(2 if not QUICK else 1):
            self.play(*[c.animate.shift(np.array([np.random.uniform(-0.05, 0.05),
                                                   np.random.uniform(-0.05, 0.05), 0]))
                        for c in cells],
                      pinned[1].animate.set_color(GOLD), run_time=0.5)
        self.beat(1.4)

        # the 87-year wall — a compact timeline strip
        self.play(FadeOut(VGroup(catch, catch2, block)), run_time=0.5)
        wall = txt("So the wall stood — for 87 years.", fs=30, color=INK, weight="BOLD").to_edge(UP, buff=1.4)
        self.play(FadeIn(wall, shift=DOWN * 0.1), run_time=0.6)
        base = Line(LEFT * 5.6, RIGHT * 5.6, stroke_color=FAINT, stroke_width=3).shift(DOWN * 0.2)
        stops = [(-5.0, "1939", "Keller poses it"),
                 (-1.9, "n = 1", "proved true"),
                 (1.0, "decades", "believed for all n"),
                 (4.3, "≈ deg 100+", "where a counterexample\nwas thought to live")]
        marks = VGroup()
        for x, top, bot in stops:
            d = Dot([x, base.get_center()[1], 0], color=ACCENT, radius=0.07)
            tl = txt(top, fs=22, color=INK, weight="BOLD").next_to(d, UP, buff=0.22)
            bl = txt(bot, fs=18, color=MUTED).next_to(d, DOWN, buff=0.22)
            marks.add(VGroup(d, tl, bl))
        self.play(Create(base), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(m, shift=UP * 0.1) for m in marks], lag_ratio=0.3, run_time=1.8))
        self.beat(1.4)
        note = self.say("Everyone believed it. No one could break it.", color=MUTED, italic=True)
        self.play(FadeIn(note), run_time=0.5)
        self.beat(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — the counterexample (the explicit map + det = -2)
    # ====================================================================== #
    def scene_counterexample(self):
        self.section_header("3 · The counterexample")

        intro = VGroup(txt("July 2026 — an explicit map", fs=27, color=INK),
                       cspace("3", 30), txt("→", fs=27, color=INK), cspace("3", 30)
                       ).arrange(RIGHT, buff=0.18)
        intro.to_edge(UP, buff=1.15)
        self.play(FadeIn(intro, shift=DOWN * 0.1), run_time=0.7)

        table = {"z1": AX1, "z2": AX2, "z3": AX3}
        spec = [
            (0, "# a degree-7 polynomial map  F : C^3 -> C^3"),
            (0, "z1, z2, z3 = symbols('z1 z2 z3')"),
            (0, "F1 = (1+z1*z2)**3*z3 + z2**2*(1+z1*z2)*(4+3*z1*z2)"),
            (0, "F2 = z2 + 3*z1*(1+z1*z2)**2*z3 + 3*z1*z2**2*(4+3*z1*z2)"),
            (0, "F3 = 2*z1 - 3*z1**2*z2 - z1**3*z3"),
            (0, ""),
            (0, "det( Matrix([F1,F2,F3]).jacobian([z1,z2,z3]) )"),
        ]
        panel = self.code_panel(spec, table, title="counterexample.py", target_h=2.7)
        panel.next_to(intro, DOWN, buff=0.42)
        self.play(FadeIn(panel[0]), FadeIn(panel[1]), FadeIn(panel[2]), FadeIn(panel[3]), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.1) for l in panel.lines],
                              lag_ratio=0.22, run_time=2.4))
        self.beat(1.8)

        # the determinant is a nonzero constant — a clean, aligned, boxed result
        det_eq = VGroup(mtext([("det DF", "b", INK)], base_fs=34),
                        txt("=", fs=34, color=INK),
                        mtext([("-2", "b", GOOD)], base_fs=42)).arrange(RIGHT, buff=0.3)
        rbox = SurroundingRectangle(det_eq, color=GOLD, buff=0.28, corner_radius=0.12)
        rbox.set_stroke(width=2.5)
        tick = make_tick(scale=1.3).next_to(rbox, RIGHT, buff=0.35)
        boxed = VGroup(rbox, det_eq, tick).next_to(panel, DOWN, buff=0.5)
        self.play(FadeIn(rbox), FadeIn(det_eq), run_time=0.6)
        self.play(Create(tick), run_time=0.45)
        self.beat(1.4)
        # caption anchored to the safe bottom band (say clamps width + position)
        cap = self.say("a nonzero constant — F satisfies the conjecture's hypothesis exactly.",
                       color=MUTED, fs=23)
        self.play(FadeIn(cap), run_time=0.6)
        self.beat(2.4)

        # the shock: degree 7, not 100+
        self.play(FadeOut(cap), run_time=0.4)
        shock = VGroup(txt("Degree", fs=30, color=INK),
                       txt("7", fs=46, color=ACCENT, weight="BOLD"),
                       txt("— not 100, just seven.  216 characters.", fs=30, color=INK)
                       ).arrange(RIGHT, buff=0.2)
        shock.to_edge(DOWN, buff=0.5)
        if shock.width > 12.8:
            shock.scale_to_fit_width(12.8)
        self.play(FadeIn(shock, shift=UP * 0.12), run_time=0.8)
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — the collision: three inputs, one image  (the "example")
    # ====================================================================== #
    def scene_collision(self):
        self.section_header("4 · One image, three preimages")

        # The real geometry (Tao's picture): a curve through the three preimages
        # b -> a -> c, whose image under F self-intersects at ONE point. Every
        # coordinate below is F evaluated on that curve — nothing is faked.
        A = np.array([0.0, 0.0, -0.25]); B = np.array([1.0, -1.5, 6.5]); C = np.array([-1.0, 1.5, 6.5])

        def gamma(t):                      # b(0) -> a(0.5) -> c(1)
            return B * 2 * (t - .5) * (t - 1) + A * (-4 * t * (t - 1)) + C * 2 * t * (t - .5)

        def Fmap(z):
            z1, z2, z3 = z
            return np.array([
                (1 + z1 * z2) ** 3 * z3 + z2 ** 2 * (1 + z1 * z2) * (4 + 3 * z1 * z2),
                z2 + 3 * z1 * (1 + z1 * z2) ** 2 * z3 + 3 * z1 * z2 ** 2 * (4 + 3 * z1 * z2),
                2 * z1 - 3 * z1 ** 2 * z2 - z1 ** 3 * z3])

        ts = np.linspace(0.0, 1.0, 160)
        src = np.array([gamma(t) for t in ts])
        img = np.array([Fmap(gamma(t)) for t in ts])

        def normalizer(data):
            mn, mx = data.min(axis=0), data.max(axis=0)
            rng = np.where(mx - mn < 1e-9, 1.0, mx - mn)
            return lambda v: 2 * (np.asarray(v, float) - mn) / rng - 1.0

        nsrc, nimg = normalizer(src), normalizer(img)
        s = 1.2
        lc = np.array([-3.75, -0.6, 0.0])    # left panel centre (source)
        rc = np.array([3.65, -0.6, 0.0])     # right panel centre (image)
        GRAD = [PA, AX1, AX2, PC, GOLD, PB]

        def cube(center):
            g = VGroup()
            verts = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
            for v in verts:
                for k in range(3):
                    w = list(v); w[k] = -w[k]; w = tuple(w)
                    if v < w:
                        ln = Line(iso(v, center, s), iso(w, center, s), stroke_width=1.4)
                        ln.set_stroke(FAINT, opacity=0.45)
                        g.add(ln)
            return g

        def axes3(center, names):
            base = np.array([-1.0, -1.0, -1.0])
            tips = [np.array([1.4, -1, -1]), np.array([-1, 1.4, -1]), np.array([-1, -1, 1.25])]
            ax, lab = VGroup(), VGroup()
            for tip, nm in zip(tips, names):
                ax.add(Arrow(iso(base, center, s), iso(tip, center, s), buff=0.0, color=MUTED,
                             stroke_width=2.4, max_tip_length_to_length_ratio=0.12, tip_length=0.14))
                lab.add(txt(nm, fs=20, color=MUTED).move_to(iso(base + (tip - base) * 1.06, center, s)))
            return ax, lab

        def project(data, norm, center):
            return [iso(norm(p), center, s) for p in data]

        # ---- left panel: the source curve through the three points ---------- #
        lcube = cube(lc)
        lax, llab = axes3(lc, ["x", "y", "z"])
        ltitle = txt("Three points on a source curve", fs=24, color=INK)
        ltitle.move_to([lc[0], 2.45, 0])
        self.play(FadeIn(lcube), Create(lax), FadeIn(llab), FadeIn(ltitle), run_time=1.1)

        scurve = VMobject().set_points_smoothly(project(src, nsrc, lc))
        scurve.set_stroke(width=4).set_color_by_gradient(*GRAD)
        self.play(Create(scurve), run_time=1.6)

        tvals = {"a": 0.5, "b": 0.0, "c": 1.0}
        pcol = {"a": PA, "b": PB, "c": PC}
        ldirs = {"a": DOWN, "b": RIGHT, "c": LEFT}
        sdot, slab = {}, {}
        for k, t in tvals.items():
            sdot[k] = Dot(iso(nsrc(gamma(t)), lc, s), color=pcol[k], radius=0.1).set_stroke(INK, width=1.2)
            slab[k] = mtext([(k, "b", pcol[k])], base_fs=24).next_to(sdot[k], ldirs[k], buff=0.12)
        self.play(LaggedStart(*[GrowFromCenter(sdot[k]) for k in "abc"], lag_ratio=0.3, run_time=1.0),
                  LaggedStart(*[FadeIn(slab[k]) for k in "abc"], lag_ratio=0.3, run_time=1.0))

        # the three true (distinct) coordinates, one line at the bottom
        def crow(k, coord):
            return VGroup(mtext([(k, "b", pcol[k])], base_fs=22),
                          txt(coord, fs=21, color=INK, font=MONO)).arrange(RIGHT, buff=0.16)
        coord = VGroup(crow("a", "(0, 0, -1/4)"), crow("b", "(1, -3/2, 13/2)"),
                       crow("c", "(-1, 3/2, 13/2)")).arrange(RIGHT, buff=0.7)
        if coord.width > 12.8:
            coord.scale_to_fit_width(12.8)
        coord.to_edge(DOWN, buff=0.55)
        self.play(FadeIn(coord), run_time=0.7)
        self.beat(2.4)

        # ---- right panel: F folds the curve onto one image point ------------ #
        rcube = cube(rc)
        rax, rlab = axes3(rc, ["P", "Q", "R"])
        rtitle = txt("F folds it onto one point", fs=24, color=INK)
        rtitle.move_to([rc[0], 2.45, 0])
        fwater = txt("F", fs=70, color=GOLD).set_opacity(0.16).move_to([-0.05, 0.15, 0])
        self.play(FadeIn(rcube), Create(rax), FadeIn(rlab), FadeIn(rtitle), FadeIn(fwater), run_time=1.1)

        icurve = VMobject().set_points_smoothly(project(img, nimg, rc))
        icurve.set_stroke(width=4).set_color_by_gradient(*GRAD)
        self.play(Create(icurve), run_time=1.8)

        p_img = Fmap(gamma(0.5))                     # = (-1/4, 0, 0)
        pdot = Dot(iso(nimg(p_img), rc, s), color=GOLD, radius=0.13).set_stroke(INK, width=1.5)
        pring = Circle(radius=0.36, stroke_color=GOLD, stroke_width=3).move_to(pdot)
        self.play(FadeIn(pdot, scale=1.4), Create(pring), run_time=0.7)
        self.beat(1.6)

        # ---- the punchline: three colours, one target ----------------------- #
        fcen = np.array([-0.05, 0.15, 0.0])
        for k in ["b", "a", "c"]:
            conn = VMobject().set_points_smoothly([sdot[k].get_center(), fcen, pdot.get_center()])
            conn.set_stroke(pcol[k], width=3.5, opacity=0.9)
            self.play(Create(conn), run_time=0.9)
            self.play(Flash(pdot.get_center(), color=pcol[k], line_length=0.22,
                            num_lines=12, flash_radius=0.42), run_time=0.5)
            self.beat(0.6)
        self.beat(1.4)

        # verdict — clear the coord strip first so the lower band is free
        self.play(FadeOut(coord), run_time=0.4)
        v1 = VGroup(mtext([("F(a) = F(b) = F(c)", "b", INK)], base_fs=28),
                    txt("— three different inputs, one image", fs=24, color=MUTED)).arrange(RIGHT, buff=0.24)
        if v1.width > 12.8:
            v1.scale_to_fit_width(12.8)
        v1.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(v1, shift=UP * 0.12), run_time=0.7)
        self.beat(2.4)

        # full-screen takeaway
        keep = v1
        self.play(FadeOut(Group(*[m for m in self.mobjects if m is not keep])), run_time=0.6)
        self.play(keep.animate.move_to(UP * 0.6).scale(1.02), run_time=0.7)
        line2 = VGroup(txt("Not one-to-one", fs=32, color=BAD, weight="BOLD"),
                       txt("→  not invertible.", fs=32, color=INK)).arrange(RIGHT, buff=0.2)
        line2.next_to(keep, DOWN, buff=0.5)
        false_card = txt("The conjecture is FALSE for every  n ≥ 3.", fs=38, color=BAD, weight="BOLD")
        false_card.next_to(line2, DOWN, buff=0.5)
        if false_card.width > 12.6:
            false_card.scale_to_fit_width(12.6)
        self.play(FadeIn(line2, shift=UP * 0.1), run_time=0.7)
        self.beat(1.0)
        self.play(Write(false_card), run_time=1.0)
        self.beat(2.2)
        self.settle()
        self.wipe()


    # ====================================================================== #
    # Scene 5 — how it was found (Anthropic / Tao / what's left)
    # ====================================================================== #
    def scene_significance(self):
        self.section_header("5 · How it was found")

        # the collaborators
        human = chip("Levent Alpöge", AX1, w=3.1, h=0.95, fs=24)
        model = chip("Claude Fable 5", GOLD, w=3.1, h=0.95, fs=24)
        anth = txt("Anthropic", fs=18, color=MUTED).next_to(model, DOWN, buff=0.14)
        pair = VGroup(human, VGroup(model, anth)).arrange(RIGHT, buff=1.2)
        pair.to_edge(UP, buff=1.3)
        times = txt("×", fs=34, color=MUTED)
        times.move_to([pair.get_center()[0], human.get_center()[1], 0])
        self.play(FadeIn(human, shift=RIGHT * 0.1), run_time=0.5)
        self.play(FadeIn(times), run_time=0.3)
        self.play(FadeIn(model, shift=LEFT * 0.1), FadeIn(anth), run_time=0.5)
        found = txt("searched low-degree maps — and returned an explicit counterexample.",
                    fs=24, color=INK).next_to(pair, DOWN, buff=0.45)
        if found.width > 12.6:
            found.scale_to_fit_width(12.6)
        self.play(FadeIn(found), run_time=0.6)
        self.beat(2.0)

        # the casual announcement — a tweet card (Image #5 style)
        tweet = self._tweet_card()
        tweet.next_to(found, DOWN, buff=0.55)
        self.play(FadeIn(tweet, shift=UP * 0.12), run_time=0.8)
        self.beat(2.8)

        # three quick facts (own screen, so there is time to read)
        self.play(FadeOut(found), FadeOut(tweet), run_time=0.5)
        facts = VGroup(
            self._fact("Machine-checkable", "verified in seconds with sympy", GOOD),
            self._fact("Digested by T. Tao", "explained why the construction works", AX1),
            self._fact("Pending peer review", "tracked at openconjectures.org", MUTED),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.42)
        facts.next_to(pair, DOWN, buff=0.8)
        self.play(LaggedStart(*[FadeIn(f, shift=RIGHT * 0.12) for f in facts],
                              lag_ratio=0.35, run_time=1.8))
        self.beat(2.6)

        # what's left — status strip
        self.play(FadeOut(VGroup(pair, times, facts)), run_time=0.5)
        status_title = txt("Where the problem stands now", fs=28, color=INK, weight="BOLD").to_edge(UP, buff=1.5)
        self.play(FadeIn(status_title, shift=DOWN * 0.1), run_time=0.5)
        items = [("n = 1", "true", GOOD, make_tick),
                 ("n = 2", "still open", ACCENT, None),
                 ("n ≥ 3", "FALSE", BAD, make_cross)]
        cards = VGroup()
        for label, verdict, col, glyph in items:
            box = RoundedRectangle(width=3.3, height=1.7, corner_radius=0.14,
                                   stroke_color=col, stroke_width=3,
                                   fill_color=col, fill_opacity=0.08)
            nm = mtext([(label, "b", INK)], base_fs=30).move_to(box).shift(UP * 0.4)
            vd = txt(verdict, fs=26, color=col, weight="BOLD").move_to(box).shift(DOWN * 0.35)
            g = VGroup(box, nm, vd)
            if glyph is not None:
                mk = glyph(color=col).scale(0.9).next_to(vd, RIGHT, buff=0.2)
                g.add(mk)
            cards.add(g)
        cards.arrange(RIGHT, buff=0.55).next_to(status_title, DOWN, buff=0.8)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.12) for c in cards], lag_ratio=0.25, run_time=1.4))
        self.beat(2.2)
        closer = self.say("An 87-year-old wall — cleared with AI in the loop.",
                          color=ACCENT, fs=28)
        self.play(FadeIn(closer, shift=UP * 0.12), run_time=0.7)
        self.play(FadeIn(self.cite()), run_time=0.5)
        self.beat(2.4)
        self.settle()
        self.wipe()

    def _fact(self, head, body, col):
        d = Dot(radius=0.07, color=col)
        h = txt(head, fs=24, color=INK, weight="BOLD")
        b = txt("—  " + body, fs=22, color=MUTED)
        return VGroup(d, h, b).arrange(RIGHT, buff=0.2)

    def _tweet_card(self):
        """A stylised X/tweet card for the announcement (Image #5 look)."""
        av = Circle(radius=0.32, stroke_color=MUTED, stroke_width=2,
                    fill_color=AX1, fill_opacity=0.30)
        initials = txt("LA", fs=20, color=INK, weight="BOLD").move_to(av)
        avatar = VGroup(av, initials)
        name = txt("Levent Alpöge", fs=23, color=INK, weight="BOLD")
        bcircle = Circle(radius=0.13, stroke_width=0, fill_color=AX1, fill_opacity=1.0)
        btick = make_tick(color=INK, sw=4).scale(0.42).move_to(bcircle)
        badge = VGroup(bcircle, btick)
        name_row = VGroup(name, badge).arrange(RIGHT, buff=0.12)
        handle = txt("@alpoge", fs=17, color=MUTED)
        id_col = VGroup(name_row, handle).arrange(DOWN, aligned_edge=LEFT, buff=0.05)
        head = VGroup(avatar, id_col).arrange(RIGHT, buff=0.22)
        line1 = VGroup(txt("the jacobian conjecture is", fs=23, color=INK),
                       txt("false", fs=23, color=BAD, weight="BOLD")).arrange(RIGHT, buff=0.16)
        line2 = VGroup(txt("thanks to", fs=23, color=INK),
                       txt("fable 5", fs=23, color=AX2, weight="BOLD")).arrange(RIGHT, buff=0.16)
        body = VGroup(line1, line2).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        inner = VGroup(head, body).arrange(DOWN, aligned_edge=LEFT, buff=0.26)
        bg = RoundedRectangle(width=inner.width + 0.8, height=inner.height + 0.7,
                              corner_radius=0.18, stroke_color=FAINT, stroke_width=2,
                              fill_color="#171B24", fill_opacity=1.0).move_to(inner)
        xlogo = txt("X", fs=24, color=MUTED, weight="BOLD")
        xlogo.move_to([bg.get_right()[0] - 0.38, bg.get_top()[1] - 0.36, 0])
        return VGroup(bg, inner, xlogo)


    # ====================================================================== #
    def play_all(self):
        self.play_hook()
        self.play_intro()
        self.scene_conjecture()
        self.scene_intuition()
        self.scene_counterexample()
        self.scene_collision()
        self.scene_significance()
        self.play_outro()


# ---- thin per-scene classes + the whole film ------------------------------ #
class Hook(_JacBase):
    def construct(self):
        self.play_hook()


class Intro(_JacBase):
    def construct(self):
        self.play_intro()


class Conjecture(_JacBase):
    def construct(self):
        self.scene_conjecture()


class Intuition(_JacBase):
    def construct(self):
        self.scene_intuition()


class Counterexample(_JacBase):
    def construct(self):
        self.scene_counterexample()


class Collision(_JacBase):
    def construct(self):
        self.scene_collision()


class Significance(_JacBase):
    def construct(self):
        self.scene_significance()


class Outro(_JacBase):
    def construct(self):
        self.play_outro()


class JacobianConjecture(_JacBase):
    def construct(self):
        self.play_all()


# a tiny glyph probe (render once to confirm C / partial / arrows are not tofu)
class Probe(_JacBase):
    def construct(self):
        rows = [
            "C  C^n  partial:∂  arrow:→  neq:≠  ge:≥  times:×",
            "∂F₁/∂z₁   z₁ z₂ z₃   -1/4   13/2",
        ]
        g = VGroup(*[Text(r, font_size=34, color=INK) for r in rows]).arrange(DOWN, buff=0.6)
        self.add(g)
        self.wait(0.2)

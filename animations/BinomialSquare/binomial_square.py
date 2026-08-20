"""The Geometry of (a + b)² — a short, house-style visual proof.

A self-explanatory (no voice-over) film that *proves* the perfect-square
identity by area: build a square of side (a + b), split each side into a and b,
and read off the four quadrant-aligned blocks.

        (a + b)²  =  a²  +  2ab  +  b²
                     └┬┘   └─┬─┘   └┬┘
                    corner   two    corner
                    square  strips  square

Scenes:

    1. Hook       -- the identity, and why it is NOT a² + b² (the missing 2ab)
    2. Proof      -- the square of side (a+b), split into a², ab, ab, b²
    3. Vary       -- slide the split (a+b fixed at 5): the four areas always
                     total 25 — three live examples: (3,2), (4,1), (2,3)
    4. Grid       -- a countable unit grid, a=2 b=1: 4 + 2 + 2 + 1 = 9 = 3²,
                     plus the mental-math payoff (21² = 400 + 40 + 1 = 441)

Bookended by the channel's intro card and the "Thank you for watching!" outro,
matching animations/HarnessEngineering/harness_engineering.py.

Everything uses ``Text`` (Pango), never ``Tex`` — so it renders with no LaTeX
toolchain and stays fast to iterate on. Superscripts use the unicode "²".

Scenes are exposed individually (``Hook``, ``Proof``, ``Vary``, ``Grid``,
``Intro``, ``Outro``) and as one film (``BinomialSquare``).

Env knobs:
    PS_QUICK=1   shorten every hold for a fast sanity render
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

# --- crisp text ------------------------------------------------------------ #
# Manim's ``Text`` quantises glyph positions badly at small font sizes, so body
# text below ~20 pt comes out with uneven letter/word spacing. Work around it
# once, here: always render glyphs at a large, crisp base size and scale the
# mobject *down* to the requested size. This shadows manim's ``Text`` so every
# call in this module benefits automatically.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("PS_QUICK") == "1"
# One knob for pacing: every reading "hold" is scaled by this. QUICK collapses
# the holds for fast iteration; otherwise it sets a calm, readable ~2-min rhythm
# (tuned so viewers have time to read every panel before it moves on).
DELAY = 0.3 if QUICK else 1.5

# ---- palette (shared house style) ---------------------------------------- #
BG = "#0E1117"       # dark slate background
INK = "#F5F3EF"      # warm white text
MUTED = "#8A93A6"    # secondary text / axes
GRID = "#2A3242"     # faint gridlines
A_C = "#5B8DEF"      # the length a, and the a² block   (blue)
B_C = "#3DD68C"      # the length b, and the b² block   (green)
AB_C = "#FF9F45"     # the two a·b blocks               (amber)
GOLD = "#FFD166"     # totals / highlights
BAD = "#FF5C5C"      # the "wrong" guess

# ---- the master square: side S = a + b, drawn from bottom-left ORIG -------- #
S = 5.0                                   # a + b for the symbolic / Vary scenes
UNIT = 0.92                               # scene-units per math-unit
MAIN_ORIG = np.array([-6.0, -2.45, 0.0])  # bottom-left corner of the square


# ========================================================================== #
# Small reusable geometry helpers
# ========================================================================== #
def sqp(orig, unit, x, y):
    """Map math-coords (x, y) on the square to a scene point."""
    return orig + np.array([x * unit, y * unit, 0.0])


def block(orig, unit, x0, y0, w, h, color, op=0.5, sw=2.0):
    """A filled rectangle whose bottom-left math-corner sits at (x0, y0)."""
    r = Rectangle(width=w * unit, height=h * unit,
                  fill_color=color, fill_opacity=op,
                  stroke_color=color, stroke_width=sw)
    r.move_to(sqp(orig, unit, x0, y0), aligned_edge=DL)
    return r


def fit(mob, max_w):
    """Scale a mobject down (never up) so it fits within max_w."""
    if mob.width > max_w:
        mob.scale(max_w / mob.width)
    return mob


def identity_row(fs=40, buff=0.2):
    """Build (a+b)² = a² + 2ab + b² as separately-colored pieces.

    Returns (row VGroup, dict of the named pieces) so blocks can be transformed
    into individual terms and terms can be highlighted independently.
    """
    lhs = Text("(a + b)²", font_size=fs, weight="BOLD", color=INK)
    eq = Text("=", font_size=fs, color=MUTED)
    a2 = Text("a²", font_size=fs, weight="BOLD", color=A_C)
    p1 = Text("+", font_size=fs, color=MUTED)
    ab2 = Text("2ab", font_size=fs, weight="BOLD", color=AB_C)
    p2 = Text("+", font_size=fs, color=MUTED)
    b2 = Text("b²", font_size=fs, weight="BOLD", color=B_C)
    row = VGroup(lhs, eq, a2, p1, ab2, p2, b2).arrange(RIGHT, buff=buff)
    return row, dict(lhs=lhs, eq=eq, a2=a2, p1=p1, ab2=ab2, p2=p2, b2=b2)


# ========================================================================== #
class _Base(Scene):
    def setup(self):
        self.camera.background_color = BG

    # ---- timing helpers --------------------------------------------------- #
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.0))

    def wipe(self, rt=0.7):
        movers = [m for m in self.mobjects]
        for m in movers:
            m.clear_updaters()
        if movers:
            self.play(*[FadeOut(m) for m in movers], run_time=rt)

    def section_header(self, label, color):
        txt = Text(label, font_size=34, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(txt.get_left(), txt.get_right()).next_to(txt, DOWN, buff=0.12)
        line.set_stroke(color=color, width=4)
        return VGroup(txt, line)

    # ---- house-style intro / outro cards ---------------------------------- #
    def title_card(self, title1, title2):
        header = Text(title1, font_size=52, color=INK, weight="BOLD")
        fit(header, 11.0)
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        writer = Text("Created by Ptolémé", font_size=28, color=A_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        sub = Text(title2, font_size=34, color=MUTED)
        fit(sub, 11.0).move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.card_wait(2.0)
        return VGroup(header, writer, line)

    def play_intro(self):
        group = self.title_card(
            "The Geometry of  (a + b)²",
            "a² + 2ab + b²,  proved as an area",
        )
        self.play(FadeOut(group), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        writer = Text("Created by Ptolémé", font_size=28, color=A_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.5)
        self.card_wait(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.1)
        self.card_wait(2.2)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 — Hook: the identity, and the common mistake
    # ====================================================================== #
    def scene_hook(self):
        title = Text("Squaring a sum", font_size=46, color=INK, weight="BOLD").to_edge(UP, buff=1.0)
        self.play(Write(title), run_time=1.2)
        self.beat(0.6)

        expr = Text("(a + b)²", font_size=64, color=INK, weight="BOLD").shift(UP * 0.7)
        self.play(FadeIn(expr, shift=UP * 0.2), run_time=0.8)
        self.beat(0.8)

        # the tempting wrong guess
        wrong = Text("a² + b²", font_size=52, color=BAD, weight="BOLD")
        neq = Text("≠", font_size=52, color=BAD, weight="BOLD")
        guess = VGroup(expr.copy(), neq, wrong).arrange(RIGHT, buff=0.35)
        guess.shift(DOWN * 0.4 - guess[0].get_center() + expr.get_center() + DOWN * 1.5)
        # place cleanly: center the trio under expr
        guess.move_to(DOWN * 0.55)
        self.play(TransformFromCopy(expr, guess[0]), run_time=0.7)
        self.play(FadeIn(guess[2], shift=RIGHT * 0.2), Write(guess[1]), run_time=0.7)
        cross = Cross(guess[2], stroke_color=BAD, stroke_width=6).scale(1.15)
        self.play(Create(cross), run_time=0.6)
        note = Text("a common mistake", font_size=26, color=BAD).next_to(guess, DOWN, buff=0.4)
        self.play(FadeIn(note, shift=UP * 0.1), run_time=0.5)
        self.beat(1.8)

        # the truth, with the middle term called out
        self.play(FadeOut(guess), FadeOut(cross), FadeOut(note),
                  expr.animate.shift(UP * 0.4), run_time=0.7)
        row, parts = identity_row(fs=54, buff=0.24)
        fit(row, 11.5).move_to(DOWN * 0.7)
        self.play(ReplacementTransform(expr, parts["lhs"]), run_time=0.7)
        self.play(FadeIn(parts["eq"]), FadeIn(parts["a2"], shift=UP * 0.1),
                  FadeIn(parts["p1"]), FadeIn(parts["p2"]),
                  FadeIn(parts["b2"], shift=UP * 0.1), run_time=0.8)
        self.beat(0.5)
        self.play(FadeIn(parts["ab2"], scale=1.4), run_time=0.7)
        box = SurroundingRectangle(parts["ab2"], color=GOLD, buff=0.12, corner_radius=0.08)
        self.play(Create(box), run_time=0.6)
        mid = Text("the middle term everyone forgets", font_size=26, color=GOLD)
        mid.next_to(row, DOWN, buff=0.55)
        self.play(FadeIn(mid, shift=UP * 0.1), run_time=0.6)
        self.beat(1.8)

        ask = Text("Where does  2ab  come from?  Let's see it as area.",
                   font_size=30, color=INK).to_edge(DOWN, buff=0.7)
        self.play(FadeOut(mid), FadeIn(ask, shift=UP * 0.15), run_time=0.7)
        self.beat(2.0)
        self.wipe()

    # ====================================================================== #
    # Scene 2 — Proof: the square of side (a+b), split into four blocks
    # ====================================================================== #
    def scene_proof(self):
        header = self.section_header("Build a square of side (a + b)", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        orig, unit = MAIN_ORIG, UNIT
        a, b = 3.0, 2.0  # concrete proportions for the picture (labels stay symbolic)

        # the whole square + its area label
        outline = Rectangle(width=S * unit, height=S * unit,
                            stroke_color=INK, stroke_width=3, fill_opacity=0)
        outline.move_to(sqp(orig, unit, 0, 0), aligned_edge=DL)
        # side brace + "a + b"
        bottom = Line(sqp(orig, unit, 0, 0), sqp(orig, unit, S, 0))
        brace = Brace(bottom, DOWN, color=MUTED)
        side_lbl = Text("a + b", font_size=30, color=INK).next_to(brace, DOWN, buff=0.12)
        area_lbl = Text("(a + b)²", font_size=34, color=INK, weight="BOLD").move_to(outline)

        self.play(Create(outline), run_time=1.0)
        self.play(GrowFromCenter(brace), FadeIn(side_lbl, shift=UP * 0.1), run_time=0.7)
        self.beat(0.6)
        area_note = Text("area  =  (a + b)²", font_size=30, color=INK)
        area_note.to_edge(RIGHT, buff=0.9).shift(UP * 2.1)
        self.play(FadeIn(area_lbl, scale=0.8), run_time=0.6)
        self.play(FadeIn(area_note, shift=LEFT * 0.2), run_time=0.6)
        self.beat(1.6)

        # split each side at a | b
        split_note = Text("Split each side into  a  and  b.", font_size=28, color=MUTED)
        split_note.next_to(area_note, DOWN, aligned_edge=RIGHT, buff=0.5)
        vline = DashedLine(sqp(orig, unit, a, 0), sqp(orig, unit, a, S),
                           stroke_color=INK, stroke_width=2.5, dash_length=0.12)
        hline = DashedLine(sqp(orig, unit, 0, a), sqp(orig, unit, S, a),
                           stroke_color=INK, stroke_width=2.5, dash_length=0.12)
        self.play(FadeOut(brace), FadeOut(side_lbl), FadeOut(area_lbl),
                  FadeIn(split_note, shift=LEFT * 0.2), run_time=0.6)
        self.play(Create(vline), Create(hline), run_time=1.0)

        # edge labels: a, b along bottom and left, colored
        def edge_label(text, color, x, y, direction):
            t = Text(text, font_size=30, color=color, weight="BOLD")
            t.move_to(sqp(orig, unit, x, y)).shift(direction)
            return t

        ea = edge_label("a", A_C, a / 2, 0, DOWN * 0.35)
        eb = edge_label("b", B_C, a + b / 2, 0, DOWN * 0.35)
        la = edge_label("a", A_C, 0, a / 2, LEFT * 0.35)
        lb = edge_label("b", B_C, 0, a + b / 2, LEFT * 0.35)
        self.play(*[FadeIn(m, shift=0.1 * d) for m, d in
                    [(ea, UP), (eb, UP), (la, RIGHT), (lb, RIGHT)]], run_time=0.7)
        self.beat(1.0)

        # the four quadrant blocks + their area labels
        blk_a2 = block(orig, unit, 0, 0, a, a, A_C)
        blk_ab1 = block(orig, unit, a, 0, b, a, AB_C)     # bottom-right : a·b
        blk_ab2 = block(orig, unit, 0, a, a, b, AB_C)     # top-left     : a·b
        blk_b2 = block(orig, unit, a, a, b, b, B_C)

        def blabel(text, color, blk):
            t = Text(text, font_size=30, color=INK, weight="BOLD").move_to(blk)
            return fit(t, min(blk.width, blk.height) * 0.75)

        lbl_a2 = blabel("a²", A_C, blk_a2)
        lbl_ab1 = blabel("ab", AB_C, blk_ab1)
        lbl_ab2 = blabel("ab", AB_C, blk_ab2)
        lbl_b2 = blabel("b²", B_C, blk_b2)

        for blk, lbl in [(blk_a2, lbl_a2), (blk_ab1, lbl_ab1),
                         (blk_ab2, lbl_ab2), (blk_b2, lbl_b2)]:
            self.play(FadeIn(blk), FadeIn(lbl, scale=0.7), run_time=0.5)
            self.beat(0.5)
        self.beat(0.8)

        # assemble the identity on the right, area-by-area
        self.play(FadeOut(split_note), run_time=0.4)
        row, parts = identity_row(fs=40, buff=0.2)
        fit(row, 7.6)
        row.to_edge(RIGHT, buff=0.6).shift(UP * 0.15)
        self.play(FadeIn(parts["lhs"]), FadeIn(parts["eq"]), run_time=0.6)
        self.play(TransformFromCopy(lbl_a2, parts["a2"]), run_time=0.8)
        self.beat(0.4)
        self.play(FadeIn(parts["p1"]),
                  TransformFromCopy(VGroup(lbl_ab1, lbl_ab2), parts["ab2"]), run_time=0.9)
        self.beat(0.4)
        self.play(FadeIn(parts["p2"]), TransformFromCopy(lbl_b2, parts["b2"]), run_time=0.8)
        self.beat(0.8)

        finalbox = SurroundingRectangle(row, color=GOLD, buff=0.18, corner_radius=0.1)
        self.play(Create(finalbox), run_time=0.8)

        # emphasise: the two off-diagonal strips ARE the 2ab
        two = Text("two equal strips  →  2ab", font_size=26, color=AB_C)
        two.next_to(finalbox, DOWN, buff=0.5)
        self.play(FadeIn(two, shift=UP * 0.1),
                  blk_ab1.animate.set_fill(opacity=0.85),
                  blk_ab2.animate.set_fill(opacity=0.85), run_time=0.7)
        self.play(Indicate(VGroup(blk_ab1, blk_ab2), color=GOLD, scale_factor=1.04),
                  Indicate(parts["ab2"], color=GOLD, scale_factor=1.1), run_time=1.0)
        self.play(blk_ab1.animate.set_fill(opacity=0.5),
                  blk_ab2.animate.set_fill(opacity=0.5), run_time=0.5)
        self.beat(2.2)
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Vary: slide the split; the four areas always total 25
    # ====================================================================== #
    def scene_vary(self):
        header = self.section_header("One identity — every split", A_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        orig, unit = MAIN_ORIG, UNIT
        a_t = ValueTracker(3.0)

        def diagram():
            a = float(a_t.get_value())
            b = S - a
            g = VGroup()
            specs = [
                (0, 0, a, a, A_C, a * a),      # a²
                (a, 0, b, a, AB_C, a * b),     # ab (bottom-right)
                (0, a, a, b, AB_C, a * b),     # ab (top-left)
                (a, a, b, b, B_C, b * b),      # b²
            ]
            for x0, y0, w, h, col, _ in specs:
                g.add(block(orig, unit, x0, y0, w, h, col, op=0.55))
            for x0, y0, w, h, col, val in specs:
                num = DecimalNumber(val, num_decimal_places=0, font_size=30,
                                    color=INK).move_to(sqp(orig, unit, x0 + w / 2, y0 + h / 2))
                fit(num, min(w, h) * unit * 0.7)
                g.add(num)
            # moving edge letters
            for txt, col, x, y, d in [("a", A_C, a / 2, 0, DOWN * 0.33),
                                      ("b", B_C, a + b / 2, 0, DOWN * 0.33),
                                      ("a", A_C, 0, a / 2, LEFT * 0.33),
                                      ("b", B_C, 0, a + b / 2, LEFT * 0.33)]:
                t = Text(txt, font_size=26, color=col, weight="BOLD")
                t.move_to(sqp(orig, unit, x, y)).shift(d)
                g.add(t)
            return g

        diagram_mob = always_redraw(diagram)
        outline = Rectangle(width=S * unit, height=S * unit,
                            stroke_color=INK, stroke_width=3, fill_opacity=0)
        outline.move_to(sqp(orig, unit, 0, 0), aligned_edge=DL)
        self.play(Create(outline), run_time=0.7)
        self.add(diagram_mob)
        self.play(FadeIn(diagram_mob), run_time=0.6)

        # live readout panel on the right
        labs = VGroup(
            Text("a²   =", font_size=30, color=A_C, weight="BOLD"),
            Text("2ab =", font_size=30, color=AB_C, weight="BOLD"),
            Text("b²   =", font_size=30, color=B_C, weight="BOLD"),
        ).arrange(DOWN, aligned_edge=RIGHT, buff=0.55).shift(UP * 0.7)

        rule = Line(ORIGIN, RIGHT * 3.9, stroke_color=MUTED, stroke_width=2)
        rule.next_to(labs, DOWN, aligned_edge=LEFT, buff=0.4)
        total = VGroup(
            Text("(a + b)²  =", font_size=30, color=INK, weight="BOLD"),
            Text("25", font_size=40, color=GOLD, weight="BOLD"),
            Text("=  5²", font_size=28, color=MUTED),
        ).arrange(RIGHT, buff=0.22)
        total.next_to(rule, DOWN, aligned_edge=LEFT, buff=0.35)

        # centre the panel in the right-hand region, kept fully on-screen
        panel = VGroup(labs, rule, total)
        panel.move_to([3.05, panel.get_center()[1], 0])
        if panel.get_right()[0] > 6.9:
            panel.shift(LEFT * (panel.get_right()[0] - 6.9))

        def bind(lab, fn, color):
            num = DecimalNumber(fn(), num_decimal_places=0, font_size=40,
                                color=color)

            def upd(m):
                m.set_value(fn())
                m.next_to(lab, RIGHT, buff=0.3)
            num.add_updater(upd)
            return num

        n_a2 = bind(labs[0], lambda: a_t.get_value() ** 2, A_C)
        n_ab = bind(labs[1], lambda: 2 * a_t.get_value() * (S - a_t.get_value()), AB_C)
        n_b2 = bind(labs[2], lambda: (S - a_t.get_value()) ** 2, B_C)

        self.play(FadeIn(labs, shift=LEFT * 0.2),
                  FadeIn(n_a2), FadeIn(n_ab), FadeIn(n_b2), run_time=0.8)
        self.play(Create(rule), FadeIn(total, shift=UP * 0.1), run_time=0.7)
        cap = Text("a + b is fixed at 5 — only the split moves.",
                   font_size=26, color=MUTED).to_edge(DOWN, buff=0.55)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.6)
        self.beat(1.6)

        # example 1 already on screen: (3, 2) -> 9 + 12 + 4
        tag1 = Text("a = 3,  b = 2", font_size=26, color=INK).next_to(cap, UP, buff=0.3)
        self.play(FadeIn(tag1), Flash(total[1], color=GOLD, flash_radius=0.7), run_time=0.7)
        self.beat(1.6)

        # example 2: slide to (4, 1) -> 16 + 8 + 1
        tag2 = Text("a = 4,  b = 1", font_size=26, color=INK).move_to(tag1)
        self.play(a_t.animate.set_value(4.0), run_time=2.4, rate_func=smooth)
        self.play(FadeTransform(tag1, tag2), Flash(total[1], color=GOLD, flash_radius=0.7),
                  run_time=0.7)
        self.beat(1.8)

        # example 3: slide across to (2, 3) -> now b² is the big one
        tag3 = Text("a = 2,  b = 3", font_size=26, color=INK).move_to(tag1)
        self.play(a_t.animate.set_value(2.0), run_time=2.8, rate_func=smooth)
        self.play(FadeTransform(tag2, tag3), Flash(total[1], color=GOLD, flash_radius=0.7),
                  run_time=0.7)
        self.beat(1.8)

        punch = Text("Whatever the split, the four areas always total 25.",
                     font_size=28, color=GOLD, weight="BOLD").to_edge(DOWN, buff=0.55)
        self.play(FadeOut(cap), FadeOut(tag3), FadeIn(punch, shift=UP * 0.1), run_time=0.7)
        self.beat(2.2)

        for n in (n_a2, n_ab, n_b2):
            n.clear_updaters()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Grid: countable unit squares (a=2, b=1) + mental-math payoff
    # ====================================================================== #
    def scene_grid(self):
        header = self.section_header("Count the squares", B_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        s = 3
        a, b = 2, 1
        unit = 1.35
        orig = np.array([-6.0, -2.25, 0.0])

        outline = Rectangle(width=s * unit, height=s * unit,
                            stroke_color=INK, stroke_width=3, fill_opacity=0)
        outline.move_to(sqp(orig, unit, 0, 0), aligned_edge=DL)
        # faint unit grid
        gridlines = VGroup()
        for i in range(1, s):
            gridlines.add(Line(sqp(orig, unit, i, 0), sqp(orig, unit, i, s),
                               stroke_color=GRID, stroke_width=1.5))
            gridlines.add(Line(sqp(orig, unit, 0, i), sqp(orig, unit, s, i),
                               stroke_color=GRID, stroke_width=1.5))
        self.play(Create(outline), run_time=0.7)
        self.play(Create(gridlines), run_time=0.8)

        # the four blocks (semi-transparent so unit cells still show through)
        blk_a2 = block(orig, unit, 0, 0, a, a, A_C, op=0.4)
        blk_ab1 = block(orig, unit, a, 0, b, a, AB_C, op=0.4)
        blk_ab2 = block(orig, unit, 0, a, a, b, AB_C, op=0.4)
        blk_b2 = block(orig, unit, a, a, b, b, B_C, op=0.4)

        ea = Text("a = 2", font_size=26, color=A_C, weight="BOLD")
        ea.move_to(sqp(orig, unit, a / 2, 0)).shift(DOWN * 0.35)
        eb = Text("b = 1", font_size=26, color=B_C, weight="BOLD")
        eb.move_to(sqp(orig, unit, a + b / 2, 0)).shift(DOWN * 0.35)
        self.play(FadeIn(ea, shift=UP * 0.1), FadeIn(eb, shift=UP * 0.1), run_time=0.6)
        self.beat(0.6)

        # reveal each region with its unit-count, tallying on the right
        tally = VGroup(
            Text("a²", font_size=34, color=A_C, weight="BOLD"),
            Text("= 4", font_size=34, color=A_C, weight="BOLD"),
            Text("2ab", font_size=34, color=AB_C, weight="BOLD"),
            Text("= 4", font_size=34, color=AB_C, weight="BOLD"),
            Text("b²", font_size=34, color=B_C, weight="BOLD"),
            Text("= 1", font_size=34, color=B_C, weight="BOLD"),
        )
        # arrange as a little 3-row table
        rows = VGroup(
            VGroup(tally[0], tally[1]).arrange(RIGHT, buff=0.4),
            VGroup(tally[2], tally[3]).arrange(RIGHT, buff=0.4),
            VGroup(tally[4], tally[5]).arrange(RIGHT, buff=0.4),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to([2.45, 0.95, 0])

        def count_label(blk, txt, color):
            t = Text(txt, font_size=30, color=INK, weight="BOLD").move_to(blk)
            return fit(t, min(blk.width, blk.height) * 0.7)

        seq = [
            (blk_a2, count_label(blk_a2, "4", A_C), rows[0]),
            (blk_ab1, count_label(blk_ab1, "2", AB_C), None),
            (blk_ab2, count_label(blk_ab2, "2", AB_C), rows[1]),
            (blk_b2, count_label(blk_b2, "1", B_C), rows[2]),
        ]
        for blk, clabel, trow in seq:
            anims = [FadeIn(blk), FadeIn(clabel, scale=0.7)]
            if trow is not None:
                anims.append(FadeIn(trow, shift=LEFT * 0.2))
            self.play(*anims, run_time=0.55)
            self.beat(0.6)
        self.beat(0.6)

        # sum it up: 4 + 4 + 1 = 9 = 3²
        rule = Line(rows.get_left(), rows.get_left() + RIGHT * 3.2,
                    stroke_color=MUTED, stroke_width=2).next_to(rows, DOWN, aligned_edge=LEFT, buff=0.4)
        summ = Text("4 + 4 + 1  =  9", font_size=34, color=INK, weight="BOLD")
        summ.next_to(rule, DOWN, aligned_edge=LEFT, buff=0.35)
        check = Text("=  3²  ✓", font_size=34, color=GOLD, weight="BOLD").next_to(summ, RIGHT, buff=0.3)
        self.play(Create(rule), FadeIn(summ, shift=UP * 0.1), run_time=0.7)
        self.beat(0.5)
        self.play(FadeIn(check, shift=LEFT * 0.15),
                  Circumscribe(outline, color=GOLD, run_time=1.3))
        self.beat(2.0)

        # the payoff: mental math
        self.play(FadeOut(VGroup(outline, gridlines, blk_a2, blk_ab1, blk_ab2, blk_b2,
                                 ea, eb, seq[0][1], seq[1][1], seq[2][1], seq[3][1],
                                 rows, rule, summ, check)),
                  run_time=0.7)
        payoff = Text("The trick for squaring in your head:", font_size=32,
                      color=INK, weight="BOLD").shift(UP * 1.3)
        line1 = Text("21²  =  (20 + 1)²", font_size=40, color=INK)
        line2 = VGroup(
            Text("=  400", font_size=40, color=A_C, weight="BOLD"),
            Text("+  40", font_size=40, color=AB_C, weight="BOLD"),
            Text("+  1", font_size=40, color=B_C, weight="BOLD"),
        ).arrange(RIGHT, buff=0.35)
        line3 = Text("=  441", font_size=44, color=GOLD, weight="BOLD")
        col = VGroup(line1, line2, line3).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        col.next_to(payoff, DOWN, buff=0.6)
        self.play(FadeIn(payoff, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(line1, shift=UP * 0.1), run_time=0.7)
        self.beat(0.9)
        self.play(FadeIn(line2, shift=UP * 0.1), run_time=0.9)
        self.beat(1.2)
        self.play(FadeIn(line3, scale=1.15), run_time=0.7)
        self.beat(2.2)
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_hook()
        self.scene_proof()
        self.scene_vary()
        self.scene_grid()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_Base):
    def construct(self):
        self.play_intro()


class Hook(_Base):
    def construct(self):
        self.scene_hook()


class Proof(_Base):
    def construct(self):
        self.scene_proof()


class Vary(_Base):
    def construct(self):
        self.scene_vary()


class Grid(_Base):
    def construct(self):
        self.scene_grid()


class Outro(_Base):
    def construct(self):
        self.play_outro()


class BinomialSquare(_Base):
    """The whole ~2-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    BinomialSquare().render()

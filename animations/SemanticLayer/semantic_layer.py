"""Semantic Layers — a short (~2-minute) explainer, house-style.

What a "semantic layer" is, where it sits in the data model, and what it's
actually used for — told in four beats:

    1. The problem   -- every tool queries the warehouse directly and invents
                         its own definition of "Revenue" — three tools, three
                         different numbers.
    2. The stack      -- Sources -> Storage (warehouse/lake) -> Semantic Layer
                         -> Consumption (BI / ML / apps / SQL). The semantic
                         layer is the seam between the *physical* data model
                         (how it's stored) and the *business* model (how
                         everyone talks about it).
    3. What it is     -- raw columns (orders.amount, orders.status, …) are
                         mapped onto named, governed business concepts
                         (metrics, dimensions, hierarchies) — defined once.
    4. What it's for  -- every tool now asks the same question and gets the
                         same answer: consistency, governance, self-service,
                         trust. (Real examples: dbt Semantic Layer, LookML,
                         Cube, AtScale.)

Everything uses ``Text`` (Pango), never ``Tex`` — no LaTeX toolchain needed.
Nothing is a screenshot: the warehouse, the layers glyph, the tool icons and
the metric card are all Manim mobjects.

Scenes are exposed individually (``Intro``, ``Problem``, ``Stack``,
``WhatIsIt``, ``UsedFor``, ``Outro``) and as one film (``SemanticLayers``).

Env knobs:
    SEM_QUICK=1     collapse every reading hold (and end-holds) for a fast render
    SEM_DELAY=1.2   override the reading-hold multiplier (seconds per "beat")
"""

from __future__ import annotations

import os

import numpy as np
from manim import *

# --- crisp text (shared house fix) ----------------------------------------- #
# Manim's ``Text`` quantises glyph positions badly below ~20 pt. Render every
# glyph at a large base size and scale the mobject *down* — spacing stays crisp.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("SEM_QUICK") == "1"
DELAY = float(os.environ.get("SEM_DELAY", "0.28" if QUICK else "2.0"))
END_HOLD = 0.2 if QUICK else 2.3
ANIM_SLOW = 1.0 if QUICK else 1.2

# ---- palette -------------------------------------------------------------- #
BG = "#0E1117"
INK = "#F5F3EF"
MUTED = "#8A93A6"
FAINT = "#2A3140"
ACCENT = "#FFD166"
GOOD = "#3DD68C"
BAD = "#FF5C5C"
WARN = "#FFC24B"

SRC_C = "#2EC4B6"    # sources (teal)
WH_C = "#5B8DEF"     # storage / warehouse (blue)
SEM_C = ACCENT       # the semantic layer itself (gold) — the star of the film
CONS_C = "#FF9F45"   # consumption tools (orange)

MONO = "Menlo"
PLAIN = "#D6DEEB"
KW = "#C792EA"
FN = "#82AAFF"
VAL = "#F78C6C"

SQL_T2C = {
    "SUM": KW, "WHERE": KW,
    "orders.amount": FN, "orders.status": FN,
    "'completed'": VAL, "Revenue": ACCENT,
}


def _safe_t2c(s, table):
    present = {k: v for k, v in table.items() if k in s}
    keys = list(present)
    return {k: v for k, v in present.items()
            if not any(k != o and k in o for o in keys)}


# ========================================================================== #
# small reusable pieces
# ========================================================================== #
def txt(text, fs=24, color=INK, weight="NORMAL", font=None, slant=None):
    kw = {"font_size": fs, "color": color, "weight": weight}
    if font:
        kw["font"] = font
    if slant:
        kw["slant"] = slant
    return Text(text, **kw)


def chip(text, color, fs=20, fill=0.14, w=None, h=0.56, tcolor=None, weight="NORMAL"):
    label = txt(text, fs=fs, color=tcolor or INK, weight=weight)
    width = (label.width + 0.5) if w is None else w
    box = RoundedRectangle(width=width, height=h, corner_radius=0.12,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=fill)
    label.move_to(box)
    return VGroup(box, label)


def arr(a, b, color=MUTED, sw=4, buff=0.1, tip=0.2):
    return Arrow(a, b, buff=buff, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.35, tip_length=tip)


def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])])
    return v.set_stroke(color=color, width=sw).scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.16, -0.16, 0], [0.16, 0.16, 0])
    b = Line([-0.16, 0.16, 0], [0.16, -0.16, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


def tick_row(text, color=GOOD, fs=20):
    tick = make_tick(color, sw=6).scale(0.75)
    label = txt(text, fs=fs, color=INK)
    return VGroup(tick, label).arrange(RIGHT, buff=0.3)


# ---- glyphs ----------------------------------------------------------------- #
def db_cyl(w=0.85, h=0.75, color=SRC_C, label=None, fs=13):
    """A little database cylinder: two ellipses + straight sides."""
    top = Ellipse(width=w, height=h * 0.34, stroke_color=color, stroke_width=2.5,
                  fill_color=color, fill_opacity=0.18)
    body = Rectangle(width=w, height=h * 0.62, stroke_width=0,
                     fill_color=color, fill_opacity=0.10)
    body.move_to(top.get_center() + DOWN * h * 0.31)
    bottom = Ellipse(width=w, height=h * 0.34, stroke_color=color, stroke_width=2.5,
                     fill_color=color, fill_opacity=0.18)
    bottom.move_to(body.get_bottom())
    sideL = Line(top.get_left(), bottom.get_left(), stroke_color=color, stroke_width=2.5)
    sideR = Line(top.get_right(), bottom.get_right(), stroke_color=color, stroke_width=2.5)
    grp = VGroup(body, bottom, sideL, sideR, top)
    if label:
        lbl = txt(label, fs=fs, color=INK).next_to(grp, DOWN, buff=0.14)
        grp.add(lbl)
    return grp


def warehouse_box(w=2.6, h=1.5, color=WH_C, title="Warehouse"):
    """A titled box with a faint table-grid icon — structured raw storage."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.14,
                            stroke_color=color, stroke_width=3,
                            fill_color=color, fill_opacity=0.06)
    bar = RoundedRectangle(width=w, height=0.44, corner_radius=0.14, stroke_width=0,
                           fill_color=color, fill_opacity=0.18)
    bar.move_to(body).align_to(body, UP)
    ttl = txt(title, fs=15, color=INK, weight="BOLD").move_to(bar)
    gw, gh = w * 0.55, h * 0.48
    grid = VGroup()
    rows, cols = 3, 3
    for r in range(rows + 1):
        y = gh / 2 - r * gh / rows
        grid.add(Line([-gw / 2, y, 0], [gw / 2, y, 0],
                     stroke_color=color, stroke_width=1.3, stroke_opacity=0.55))
    for c in range(cols + 1):
        x = -gw / 2 + c * gw / cols
        grid.add(Line([x, gh / 2, 0], [x, -gh / 2, 0],
                     stroke_color=color, stroke_width=1.3, stroke_opacity=0.55))
    grid.move_to(body.get_center() + DOWN * 0.16)
    grp = VGroup(body, bar, ttl, grid)
    grp.body = body
    return grp


def layers_icon(r=0.5, color=SEM_C, n=3):
    """A stack-of-layers glyph (n stacked diamonds) — the semantic layer's mark."""
    grp = VGroup()
    for i in range(n):
        rhomb = Polygon(
            np.array([0, r * 0.42, 0]), np.array([r, 0, 0]),
            np.array([0, -r * 0.42, 0]), np.array([-r, 0, 0]),
            stroke_color=color, stroke_width=2.4,
            fill_color=color, fill_opacity=0.12 + i * 0.10)
        rhomb.shift(UP * (i - (n - 1) / 2) * r * 0.34)
        grp.add(rhomb)
    return grp


def sem_band(w=5.6, h=1.3, color=SEM_C, title="Semantic Layer",
             sub="metrics · dimensions · business logic"):
    body = RoundedRectangle(width=w, height=h, corner_radius=0.16,
                            stroke_color=color, stroke_width=3.5,
                            fill_color=color, fill_opacity=0.12)
    icon = layers_icon(r=0.28, color=color)
    ttl = txt(title, fs=20, color=color, weight="BOLD")
    head = VGroup(icon, ttl).arrange(RIGHT, buff=0.22)
    subt = txt(sub, fs=13, color=MUTED)
    inner = VGroup(head, subt).arrange(DOWN, buff=0.12)
    inner.move_to(body)
    grp = VGroup(body, inner)
    grp.body = body
    return grp


def bars_icon(color=CONS_C):
    heights = [0.42, 0.85, 0.62]
    bars = VGroup(*[Rectangle(width=0.13, height=0.5 * f, stroke_width=0,
                              fill_color=color, fill_opacity=0.9) for f in heights])
    bars.arrange(RIGHT, buff=0.05, aligned_edge=DOWN)
    return bars


def dots_icon(color=CONS_C, r=0.06):
    d1 = Dot(radius=r, color=color).shift(UP * 0.2)
    d2 = Dot(radius=r, color=color).shift(LEFT * 0.2 + DOWN * 0.12)
    d3 = Dot(radius=r, color=color).shift(RIGHT * 0.2 + DOWN * 0.12)
    lines = VGroup(
        Line(d1.get_center(), d2.get_center(), stroke_color=color, stroke_width=1.6),
        Line(d1.get_center(), d3.get_center(), stroke_color=color, stroke_width=1.6),
        Line(d2.get_center(), d3.get_center(), stroke_color=color, stroke_width=1.6),
    )
    return VGroup(lines, d1, d2, d3)


def grid_icon(color=CONS_C, n=3, s=0.12):
    cells = VGroup(*[Square(side_length=s, stroke_color=color, stroke_width=1.4,
                            fill_color=color, fill_opacity=0.22) for _ in range(n * n)])
    cells.arrange_in_grid(rows=n, cols=n, buff=0.04)
    return cells


def app_icon(color=CONS_C):
    body = RoundedRectangle(width=0.32, height=0.48, corner_radius=0.06,
                            stroke_color=color, stroke_width=2,
                            fill_color=color, fill_opacity=0.18)
    dot = Dot(radius=0.03, color=color).move_to(body.get_bottom() + UP * 0.08)
    return VGroup(body, dot)


def sql_icon(color=CONS_C):
    return txt(">_", fs=20, color=color, weight="BOLD", font=MONO)


def tool_card(title, icon, color, w=1.9, h=1.25):
    box = RoundedRectangle(width=w, height=h, corner_radius=0.12,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=0.08)
    lbl = txt(title, fs=14, color=INK, weight="BOLD")
    inner = VGroup(icon, lbl).arrange(DOWN, buff=0.16)
    if inner.width > w - 0.3:
        inner.scale_to_fit_width(w - 0.3)
    inner.move_to(box)
    grp = VGroup(box, inner)
    grp.body = box
    return grp


def consumption_cards(w=1.9, h=1.25):
    specs = [("BI Dashboard", bars_icon(CONS_C)), ("Notebook", dots_icon(CONS_C)),
             ("Spreadsheet", grid_icon(CONS_C))]
    return [tool_card(t, ic, CONS_C, w=w, h=h) for t, ic in specs]


def metric_card(title, formula, table, color=SEM_C, fs=17):
    ttl = txt(title, fs=16, color=color, weight="BOLD")
    body = Text(formula, font=MONO, font_size=fs, color=PLAIN, t2c=_safe_t2c(formula, table))
    inner = VGroup(ttl, body).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
    bg = RoundedRectangle(width=inner.width + 0.7, height=inner.height + 0.5,
                          corner_radius=0.14, stroke_color=color, stroke_width=2.5,
                          fill_color="#0A0E15", fill_opacity=1.0)
    bg.move_to(inner)
    grp = VGroup(bg, inner)
    grp.bg = bg
    return grp


# ========================================================================== #
class _SemBase(Scene):
    def setup(self):
        self.camera.background_color = BG
        self._cap = None

    def play(self, *anims, **kwargs):
        is_wait = any(type(a).__name__ == "Wait" for a in anims)
        if not QUICK and anims and not is_wait:
            rt = kwargs.get("run_time")
            if rt is None:
                rts = [r for r in (getattr(a, "run_time", None) for a in anims) if r]
                rt = max(rts) if rts else 1.0
            kwargs["run_time"] = rt * ANIM_SLOW
        return super().play(*anims, **kwargs)

    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.25 if QUICK else 1.0))

    def settle(self):
        self.wait(END_HOLD)

    def wipe(self, rt=0.6):
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)
        self._cap = None

    def section_header(self, part, label, color):
        tag = txt(part, fs=20, color=color, weight="BOLD")
        tagbox = RoundedRectangle(width=tag.width + 0.4, height=0.44, corner_radius=0.1,
                                  stroke_color=color, stroke_width=2,
                                  fill_color=color, fill_opacity=0.12)
        tag.move_to(tagbox)
        title = txt(label, fs=32, color=INK, weight="BOLD")
        head = VGroup(VGroup(tagbox, tag), title).arrange(RIGHT, buff=0.3)
        head.to_corner(UL, buff=0.5)
        line = Line(head.get_left(), head.get_right()).next_to(head, DOWN, buff=0.13)
        line.set_stroke(color=color, width=3)
        self.play(FadeIn(head, shift=RIGHT * 0.2), Create(line), run_time=0.7)
        return VGroup(head, line)

    def say(self, text, color=INK, fs=24, rt=0.5, weight="BOLD"):
        new = txt(text, fs=fs, color=color, weight=weight).to_edge(DOWN, buff=0.42)
        if new.width > 12.6:
            new.scale_to_fit_width(12.6)
        if self._cap is None:
            self._cap = new
            self.play(FadeIn(new, shift=UP * 0.12), run_time=rt)
        else:
            self.play(ReplacementTransform(self._cap, new), run_time=rt)
            self._cap = new
        return new

    def _bookend_title(self, title, subtitle=None):
        header = txt(title, fs=52, color=INK, weight="BOLD")
        if header.width > 11.5:
            header.scale_to_fit_width(11.5)
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=SEM_C)
        writer = txt("Created by Ptolémé", fs=28, color=SEM_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.4)
        self.card_wait(0.6)
        if subtitle:
            sub = txt(subtitle, fs=28, color=MUTED)
            if sub.width > 12:
                sub.scale_to_fit_width(12)
            sub.move_to(header)
            self.play(Transform(header, sub), run_time=0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        return VGroup(header, writer, line)

    def play_intro(self):
        icon = layers_icon(r=1.05, color=SEM_C).to_edge(UP, buff=0.95)
        self.play(LaggedStart(*[GrowFromCenter(m) for m in icon], lag_ratio=0.25), run_time=1.3)
        self.play(Indicate(icon, color=INK, scale_factor=1.08), run_time=0.8)
        grp = self._bookend_title("Semantic Layers", "one definition, every tool, same answer")
        self.card_wait(1.7)
        self.play(FadeOut(grp), FadeOut(icon), run_time=0.9)
        self.card_wait(0.2)

    def play_outro(self):
        self.card_wait(0.3)
        header = txt("Thanks for watching!", fs=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=SEM_C)
        writer = txt("Created by Ptolémé", fs=28, color=SEM_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.2)
        self.card_wait(0.6)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.card_wait(1.6)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.0)
        self.card_wait(0.3)

    # ====================================================================== #
    # Scene 1 — the problem: no shared definition
    # ====================================================================== #
    def scene_problem(self):
        self.section_header("01", "Without A Semantic Layer", BAD)

        wh = warehouse_box(w=2.6, h=1.9, color=WH_C, title="Data Warehouse")
        wh.move_to(LEFT * 4.2 + DOWN * 0.2)
        self.play(FadeIn(wh, shift=UP * 0.2), run_time=0.7)
        self.say("Every tool queries the raw warehouse directly.", color=INK)
        self.beat(1.4)

        cards = consumption_cards(w=2.0, h=1.2)
        ys = [1.75, 0.0, -1.75]
        specs = [
            ("naive SUM(amount)", "$1.32M"),
            ("SUM(amount) where paid", "$0.98M"),
            ("SUM(amount) minus refunds", "$1.05M"),
        ]
        notes = VGroup()
        arrows = VGroup()
        for card, y, (formula, amount) in zip(cards, ys, specs):
            card.move_to(RIGHT * 3.15 + UP * y)
            start = wh.body.get_right() + UP * (y * 0.26)
            a = arr(start, card.get_left(), color=MUTED, sw=2.5)
            arrows.add(a)
            f = txt(formula, fs=13, color=MUTED)
            amt = txt(amount, fs=24, color=BAD, weight="BOLD")
            note = VGroup(f, amt).arrange(DOWN, buff=0.1)
            note.next_to(card, RIGHT, buff=0.35)
            avail = (config.frame_x_radius - 0.35) - note.get_left()[0]
            if note.width > avail:
                note.scale(avail / note.width, about_point=note.get_left())
            notes.add(note)

        for card, a, note in zip(cards, arrows, notes):
            self.play(GrowArrow(a), FadeIn(card, shift=LEFT * 0.2), run_time=0.5)
            self.play(FadeIn(note, shift=LEFT * 0.15), run_time=0.4)
            self.beat(0.6)

        self.say("Same question, three different definitions of “Revenue.”", color=WARN)
        self.beat(1.2)

        marks = VGroup(*[make_cross(BAD, sw=5, scale=0.55).next_to(note, UP, buff=0.16)
                        for note in notes])
        self.play(LaggedStart(*[FadeIn(m, scale=1.3) for m in marks], lag_ratio=0.2), run_time=0.8)
        self.say("No one agrees on the number — and no one is technically wrong.", color=BAD)
        self.beat(1.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — where it lives: the data stack
    # ====================================================================== #
    def scene_stack(self):
        self.section_header("02", "Where It Lives In The Stack", SEM_C)

        srcs = VGroup(
            db_cyl(color=SRC_C, label="Orders DB"),
            db_cyl(color=SRC_C, label="CRM"),
            db_cyl(color=SRC_C, label="Events"),
        ).arrange(RIGHT, buff=0.9)
        srcs.move_to(DOWN * 2.35)
        src_lbl = txt("Sources", fs=15, color=SRC_C, weight="BOLD").next_to(srcs, LEFT, buff=0.5)
        self.play(FadeIn(srcs, shift=UP * 0.2), FadeIn(src_lbl), run_time=0.8)
        self.say("Raw data starts in many places — databases, events, APIs.", color=SRC_C)
        self.beat(1.4)

        wh = warehouse_box(w=2.6, h=1.3, color=WH_C, title="Warehouse / Lake")
        wh.move_to(UP * -1.05)
        a1 = arr(srcs.get_top() + UP * 0.02, wh.get_bottom() + DOWN * 0.02, color=WH_C, sw=3)
        self.play(GrowArrow(a1), FadeIn(wh, shift=UP * 0.2), run_time=0.8)
        self.say("It lands in a warehouse or lake — structured, but still raw.", color=WH_C)
        self.beat(1.4)

        sem = sem_band(w=5.6, h=1.3, color=SEM_C)
        sem.move_to(UP * 0.5)
        a2 = arr(wh.get_top() + UP * 0.02, sem.get_bottom() + DOWN * 0.02, color=SEM_C, sw=3)
        self.play(GrowArrow(a2), FadeIn(sem, shift=UP * 0.2), run_time=0.8)
        self.play(Indicate(sem, color=INK, scale_factor=1.05), run_time=0.8)
        self.say("The semantic layer sits right here — raw tables become business terms.",
                 color=SEM_C)
        self.beat(1.6)

        tools = [("BI", bars_icon(CONS_C)), ("ML", dots_icon(CONS_C)),
                 ("Apps", app_icon(CONS_C)), ("SQL", sql_icon(CONS_C))]
        cons_cards = VGroup(*[tool_card(t, ic, CONS_C, w=1.3, h=1.0) for t, ic in tools])
        cons_cards.arrange(RIGHT, buff=0.32)
        cons_cards.move_to(UP * 1.95)
        fan = VGroup(*[arr(sem.get_top() + RIGHT * (c.get_x() * 0.5), c.get_bottom(),
                           color=CONS_C, sw=2.5) for c in cons_cards])
        self.play(FadeIn(cons_cards, shift=UP * 0.2), run_time=0.6)
        self.play(LaggedStart(*[GrowArrow(a) for a in fan], lag_ratio=0.15), run_time=1.0)
        self.say("Every tool — BI, ML, apps, ad-hoc SQL — reads through it, never around it.",
                 color=CONS_C)
        self.beat(1.8)

        phys_grp = VGroup(srcs, wh)
        biz_grp = VGroup(sem, cons_cards)
        brace_p = Brace(phys_grp, RIGHT, color=MUTED)
        lbl_p = txt("Physical model", fs=15, color=MUTED).next_to(brace_p, RIGHT, buff=0.15)
        brace_b = Brace(biz_grp, RIGHT, color=SEM_C)
        lbl_b = txt("Business / logical model", fs=15, color=SEM_C).next_to(brace_b, RIGHT, buff=0.15)
        self.play(GrowFromCenter(brace_p), FadeIn(lbl_p), run_time=0.6)
        self.play(GrowFromCenter(brace_b), FadeIn(lbl_b), run_time=0.6)
        self.say("Physical model below. Business model above. The semantic layer is the seam.",
                 color=INK)
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — what it actually is
    # ====================================================================== #
    def scene_whatisit(self):
        self.section_header("03", "What It Actually Is", SEM_C)

        sem = sem_band(w=5.2, h=1.1, color=SEM_C)
        sem.to_edge(UP, buff=1.25)
        self.play(FadeIn(sem, shift=UP * 0.15), run_time=0.6)
        self.say("It maps raw, physical columns onto named business concepts.", color=SEM_C)
        self.beat(1.4)

        phys = VGroup(
            chip("orders.amount", MUTED, fs=15),
            chip("orders.status", MUTED, fs=15),
            chip("customers.region", MUTED, fs=15),
            chip("customers.id", MUTED, fs=15),
        ).arrange(DOWN, buff=0.3)
        phys.to_edge(LEFT, buff=1.0).shift(DOWN * 0.55)
        phys_lbl = txt("Physical columns", fs=15, color=MUTED, weight="BOLD").next_to(
            phys, UP, buff=0.28)

        biz = VGroup(
            chip("Revenue  (metric)", SEM_C, fs=15, tcolor=INK),
            chip("Order Status  (attribute)", SEM_C, fs=15, tcolor=INK),
            chip("Region  (hierarchy)", SEM_C, fs=15, tcolor=INK),
            chip("Customer  (dimension)", SEM_C, fs=15, tcolor=INK),
        ).arrange(DOWN, buff=0.3)
        biz.to_edge(RIGHT, buff=1.0).shift(DOWN * 0.55)
        biz_lbl = txt("Business concepts", fs=15, color=SEM_C, weight="BOLD").next_to(
            biz, UP, buff=0.28)

        self.play(FadeIn(phys_lbl),
                  LaggedStart(*[FadeIn(c, shift=RIGHT * 0.15) for c in phys], lag_ratio=0.15),
                  run_time=1.0)
        self.play(FadeIn(biz_lbl),
                  LaggedStart(*[FadeIn(c, shift=LEFT * 0.15) for c in biz], lag_ratio=0.15),
                  run_time=1.0)
        self.beat(0.8)

        links = VGroup(
            arr(phys[0].get_right(), biz[0].get_left(), color=SEM_C, sw=2),
            arr(phys[1].get_right(), biz[0].get_left(), color=SEM_C, sw=2),
            arr(phys[1].get_right(), biz[1].get_left(), color=MUTED, sw=2),
            arr(phys[2].get_right(), biz[2].get_left(), color=MUTED, sw=2),
            arr(phys[3].get_right(), biz[3].get_left(), color=MUTED, sw=2),
        )
        self.play(LaggedStart(*[GrowArrow(a) for a in links], lag_ratio=0.15), run_time=1.2)
        self.say("Two raw columns collapse into one governed metric: Revenue.", color=SEM_C)
        self.beat(1.6)

        self.play(FadeOut(VGroup(phys, biz, phys_lbl, biz_lbl, links)), run_time=0.6)

        card = metric_card("Revenue  (metric)",
                           "SUM(orders.amount) WHERE orders.status = 'completed'",
                           SQL_T2C, color=SEM_C)
        card.move_to(DOWN * 0.7)
        self.play(FadeIn(card, shift=UP * 0.2), run_time=0.7)
        self.say("Defined once, in one place — computed the same way, everywhere.", color=SEM_C)
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — what it's used for
    # ====================================================================== #
    def scene_usedfor(self):
        self.section_header("04", "What It's Used For", GOOD)

        card = metric_card("Revenue  (metric)",
                           "SUM(orders.amount) WHERE orders.status = 'completed'",
                           SQL_T2C, color=SEM_C)
        card.to_edge(UP, buff=1.3)
        self.play(FadeIn(card, shift=UP * 0.15), run_time=0.6)
        self.say("Now every tool asks the semantic layer the same question…", color=SEM_C)
        self.beat(1.2)

        trio = VGroup(*consumption_cards(w=1.9, h=1.05))
        trio.arrange(RIGHT, buff=1.0)
        trio.move_to(DOWN * 0.7)
        fan = VGroup(*[arr(card.get_bottom(), c.get_top(), color=GOOD, sw=2.5) for c in trio])
        self.play(FadeIn(trio, shift=DOWN * 0.15), run_time=0.6)
        self.play(LaggedStart(*[GrowArrow(a) for a in fan], lag_ratio=0.2), run_time=0.9)

        amounts = VGroup()
        for c in trio:
            amt = txt("$1.24M", fs=22, color=GOOD, weight="BOLD")
            tick = make_tick(GOOD, sw=6, scale=0.7)
            row = VGroup(tick, amt).arrange(RIGHT, buff=0.15)
            row.next_to(c, DOWN, buff=0.3)
            amounts.add(row)
        self.play(LaggedStart(*[FadeIn(a, shift=UP * 0.1) for a in amounts], lag_ratio=0.2),
                  run_time=0.9)
        self.say("…and gets the same answer, every time.", color=GOOD)
        self.beat(1.6)

        self.play(FadeOut(VGroup(card, trio, fan, amounts)), run_time=0.6)

        benefits = VGroup(
            tick_row("Consistency — one number, every tool", GOOD),
            tick_row("Governance — fix a definition once, it updates everywhere", GOOD),
            tick_row("Self-service — analysts explore without duplicating logic", GOOD),
            tick_row("Trust — everyone speaks the same business language", GOOD),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        for row in benefits:
            avail = (config.frame_x_radius * 2) - 1.4
            if row.width > avail:
                row.scale(avail / row.width, about_point=row.get_left())
        benefits.move_to(UP * 0.3)
        self.play(LaggedStart(*[FadeIn(b, shift=RIGHT * 0.15) for b in benefits], lag_ratio=0.25),
                  run_time=1.6)
        self.beat(1.8)

        tools_row = VGroup(*[chip(t, MUTED, fs=14)
                             for t in ["dbt Semantic Layer", "LookML", "Cube", "AtScale"]])
        tools_row.arrange(RIGHT, buff=0.3)
        if tools_row.width > 12.0:
            tools_row.scale_to_fit_width(12.0)
        tools_row.next_to(benefits, DOWN, buff=0.6)
        self.play(LaggedStart(*[FadeIn(t, shift=UP * 0.1) for t in tools_row], lag_ratio=0.15),
                  run_time=0.9)
        self.say("This is what dbt's Semantic Layer, LookML, Cube and AtScale actually do.",
                 color=MUTED)
        self.beat(1.8)

        self.play(FadeOut(VGroup(benefits, tools_row)), FadeOut(self._cap), run_time=0.5)
        self._cap = None
        punch = txt("One definition. Every tool. Same answer.", fs=30, color=SEM_C, weight="BOLD")
        if punch.width > 12.6:
            punch.scale_to_fit_width(12.6)
        self.play(Write(punch), run_time=1.1)
        self.beat(2.2)
        self.settle()
        self.wipe()

    # ---- the whole film --------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_problem()
        self.scene_stack()
        self.scene_whatisit()
        self.scene_usedfor()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_SemBase):
    def construct(self):
        self.play_intro()


class Problem(_SemBase):
    def construct(self):
        self.scene_problem()


class Stack(_SemBase):
    def construct(self):
        self.scene_stack()


class WhatIsIt(_SemBase):
    def construct(self):
        self.scene_whatisit()


class UsedFor(_SemBase):
    def construct(self):
        self.scene_usedfor()


class Outro(_SemBase):
    def construct(self):
        self.play_outro()


class SemanticLayers(_SemBase):
    """The whole ~2-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    SemanticLayers().render()

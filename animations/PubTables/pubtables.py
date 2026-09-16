"""PubTables-1M — a short house-style explainer of one paper.

    Brandon Smock, Rohith Pesala, Robin Abraham.
    "PubTables-1M: Towards comprehensive table extraction from
    unstructured documents." CVPR 2022. arXiv:2110.00061.

The paper's own figures (CC BY 4.0) are reused verbatim, baked into assets/
by fetch_assets.py, and credited on screen. Story:

    1. Paper      -- the citation card, then Figure 1: a table's structure
                     is implicit; recovering it is table extraction.
    2. Tasks      -- Figure 2: detection, structure recognition,
                     functional analysis.
    3. Scale      -- PDF + XML alignment over PubMed Central, then the
                     dataset-size bar chart (947,642 tables).
    4. Canonical  -- Figure 3: oversegmentation, the ambiguity it creates,
                     and the canonicalization fix (Algorithm 1).
    5. Model      -- Figure 4: six dilated box classes, one DETR, and the
                     results (TD 0.966, TSR+FA 0.912, complex-table exact
                     match 0.536 -> 0.694 from better labels alone).

Bookended by the channel intro / "Thank you for watching!" outro. Everything
uses ``Text`` (Pango), never ``Tex``.

Env knobs:
    PT_QUICK=1   collapse every hold for a fast layout render
    PT_DELAY=x   override the reading-hold multiplier
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

QUICK = os.environ.get("PT_QUICK") == "1"
DELAY = float(os.environ.get("PT_DELAY", "0.28" if QUICK else "2.2"))
ANIM_SLOW = 1.0 if QUICK else 1.15
END_HOLD = 0.2 if QUICK else 2.2

# ---- palette (house style + this film's accents) --------------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text
FAINT = "#2A3446"       # hairlines, card borders
PANEL = "#141C29"       # card fill
GOLD = "#FFD166"        # accent / payoff
CYAN = "#55C1E7"        # table detection
VIOLET = "#B388EB"      # structure recognition
GREEN = "#7AE582"       # functional analysis
RED = "#FF6B6B"         # the flaw / oversegmentation
STEEL = "#4C5A75"       # baseline bars
FONT = "Helvetica Neue"

# ---- crisp small text: Pango mangles glyphs/spacing below ~20pt ----------- #
# Shadow Text so every call rasterises at a large base size and scales DOWN.
_BaseText = Text
_BaseText.set_default(font=FONT)
_TEXT_BASE = 60


def Text(text, font_size=48, **kw):  # noqa: F811 (intentional shadow)
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


def txt(s, fs=26, color=INK, font=None, slant=None, weight=None, t2c=None):
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


# ---- small reusable glyphs ------------------------------------------------- #
def chip(text, color, w=2.6, h=0.85, fs=22, fill=0.14, tcolor=None, radius=0.14):
    box = RoundedRectangle(width=w, height=h, corner_radius=radius,
                           stroke_color=color, stroke_width=3,
                           fill_color=color, fill_opacity=fill)
    label = txt(text, fs=fs, color=tcolor or INK)
    if label.width > w - 0.3:
        label.scale((w - 0.3) / label.width)
    label.move_to(box)
    return VGroup(box, label)


def harrow(start, end, color=MUTED, sw=4, tip=0.2):
    return Arrow(start, end, buff=0.0, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.28, tip_length=tip)


# ---- the paper's figures, reused verbatim (CC BY 4.0) ---------------------- #
# Native pixel sizes, so uv coordinates can be read off the source images.
SRC = {
    "fig1_example.jpg": (1545, 604),
    "fig2_tasks.jpg": (1800, 790),
    "fig3a_overseg.jpg": (1589, 608),
    "fig3b_canonical.jpg": (1589, 608),
    "fig4_dilated.jpg": (2374, 1611),
    "page1.jpg": (1836, 2376),
    "alg1_canon.jpg": (1000, 1440),
}


def image_card(filename, height=4.0, border=FAINT, sw=2):
    img = ImageMobject(os.path.join(ASSETS, filename))
    img.height = height
    frame = SurroundingRectangle(img, color=border, buff=0.0, stroke_width=sw)
    return Group(img, frame)


def uv_point(card, u, v):
    """Scene-space point at relative image coords (u right, v down) in [0,1]."""
    img = card[0]
    dx = (u - 0.5) * img.width
    dy = (0.5 - v) * img.height
    return img.get_center() + np.array([dx, dy, 0.0])


def uv_rect(card, u0, v0, u1, v1, color=GOLD, sw=3.5, fill=0.0):
    img = card[0]
    r = Rectangle(width=(u1 - u0) * img.width, height=(v1 - v0) * img.height,
                  stroke_color=color, stroke_width=sw,
                  fill_color=color, fill_opacity=fill)
    r.move_to(uv_point(card, (u0 + u1) / 2, (v0 + v1) / 2))
    return r


def uv_cover(card, u0, v0, u1, v1, opacity=0.78):
    """A BG-coloured veil over part of a figure (for spotlighting the rest)."""
    img = card[0]
    r = Rectangle(width=(u1 - u0) * img.width, height=(v1 - v0) * img.height,
                  stroke_width=0, fill_color=BG, fill_opacity=opacity)
    r.move_to(uv_point(card, (u0 + u1) / 2, (v0 + v1) / 2))
    return r


def credit(card, label, fs=15):
    """Small attribution line under a reused figure."""
    t = txt(label, fs=fs, color=MUTED)
    t.next_to(card, DOWN, buff=0.14)
    return t


# ========================================================================== #
class _PTBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    def play(self, *anims, **kw):
        if "run_time" in kw:
            kw["run_time"] *= ANIM_SLOW
        super().play(*anims, **kw)

    # ---- timing ------------------------------------------------------------
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

    # ---- chrome --------------------------------------------------------------
    def section_header(self, label, color=GOLD):
        t = txt(label, fs=32, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=3)
        g = VGroup(t, line)
        self.play(FadeIn(g, shift=DOWN * 0.15), run_time=0.6)
        return g

    def say(self, s, color=INK, fs=25, buff=0.45):
        m = txt(s, fs=fs, color=color)
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

    # ---- house intro / outro cards -----------------------------------------
    def _rule_under(self, header, pad=1.0, color=GOLD, drop=0.45):
        return Line([header.get_left()[0] - pad, header.get_bottom()[1] - drop, 0],
                    [header.get_right()[0] + pad, header.get_bottom()[1] - drop, 0]
                    ).set_stroke(width=3, color=color)

    def play_intro(self):
        header = txt("PubTables-1M", fs=56, color=INK, weight="BOLD")
        line = self._rule_under(header)
        writer = txt("Created by Ptolémé", fs=28, color=CYAN)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        sub = txt("A million labeled tables, and the label flaw they fixed first",
                  fs=28, color=MUTED)
        if sub.width > 11.8:
            sub.scale_to_fit_width(11.8)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.card_wait(1.8)
        self.play(FadeOut(VGroup(header, writer, line)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.4)
        header = txt("Thank you for watching!", fs=46, color=INK, weight="BOLD")
        line = self._rule_under(header)
        writer = txt("Created by Ptolémé", fs=28, color=CYAN)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = txt("Paper: Smock, Pesala and Abraham. PubTables-1M, CVPR 2022. "
                    "arXiv:2110.00061, figures CC BY 4.0.",
                    fs=22, color=MUTED)
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
    # Scene 1 -- the paper, and the problem it opens with
    # ====================================================================== #
    def scene_paper(self):
        self.section_header("1 · The paper", color=CYAN)

        page = image_card("page1.jpg", height=5.1)
        page.move_to([3.95, -0.35, 0])

        title1 = txt("PubTables-1M: Towards comprehensive", fs=26, weight="BOLD")
        title2 = txt("table extraction from unstructured documents",
                     fs=26, weight="BOLD")
        authors = txt("Brandon Smock · Rohith Pesala · Robin Abraham", fs=21)
        org = txt("Microsoft, Redmond", fs=20, color=MUTED)
        venue = txt("CVPR 2022 · arXiv:2110.00061", fs=20, color=MUTED)
        lic = txt("Open access, CC BY 4.0: its figures appear here verbatim.",
                  fs=19, color=MUTED, t2c={"CC BY 4.0": GOLD})
        block = VGroup(title1, title2, authors, org, venue, lic)
        for m in block:
            if m.width > 6.4:
                m.scale_to_fit_width(6.4)
        block.arrange(DOWN, aligned_edge=LEFT, buff=0.26)
        block.to_edge(LEFT, buff=0.7)
        block.set_y(0.3)

        self.play(FadeIn(page, shift=UP * 0.2), run_time=0.9)
        self.play(LaggedStart(*[FadeIn(m, shift=RIGHT * 0.15) for m in block],
                              lag_ratio=0.15), run_time=1.6)
        cap = self.show_say("One 2021 paper from Microsoft set out to fix how "
                            "machines learn to read tables.")
        self.beat(2.0)
        cap = self.replace_say(cap, "Everything in this film, including every "
                                    "figure, comes straight from that paper.")
        self.beat(2.0)

        # ---- zoom into Figure 1: structure is implicit ----------------------
        fig1 = image_card("fig1_example.jpg", height=3.05)
        fig1.move_to([0, 0.65, 0])
        cred = credit(fig1, "Figure 1 of the paper (CC BY 4.0)")
        self.play(FadeOut(block), FadeOut(page), run_time=0.7)
        self.play(FadeIn(fig1, scale=1.05), FadeIn(cred), run_time=0.9)
        cap = self.replace_say(cap, "The paper opens with this table. You read "
                                    "its structure without even trying.")
        self.beat(2.0)

        span = uv_rect(fig1, 0.205, 0.005, 0.775, 0.175, color=GOLD)
        self.play(Create(span), run_time=0.8)
        cap = self.replace_say(cap, "The label ΔSDM silently applies to the "
                                    "three columns underneath it.")
        self.beat(2.0)

        stub = uv_rect(fig1, 0.0, 0.005, 0.2, 0.31, color=VIOLET)
        self.play(Create(stub), run_time=0.8)
        cap = self.replace_say(cap, "This corner is simply empty, and you "
                                    "understand that it belongs to no column.")
        self.beat(2.0)
        cap = self.replace_say(cap, "None of this is written down in the file. "
                                    "The structure lives only in your head.")
        self.beat(2.2)
        cap = self.replace_say(cap, "Teaching a model to recover it is called "
                                    "table extraction, and it needs data.",
                               color=GOLD)
        self.beat(2.2)

        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 -- the three subtasks (Figure 2)
    # ====================================================================== #
    def scene_tasks(self):
        self.section_header("2 · Three subtasks", color=VIOLET)

        fig2 = image_card("fig2_tasks.jpg", height=3.35)
        fig2.move_to([0, 0.72, 0])
        cred = credit(fig2, "Figure 2 of the paper (CC BY 4.0)")
        self.play(FadeIn(fig2, shift=UP * 0.2), FadeIn(cred), run_time=0.9)
        cap = self.show_say("The paper splits table extraction into three "
                            "subtasks, shown on one real page.")
        self.beat(2.0)

        # Panel bounds (relative image coords, full height).
        panels = [(0.000, 0.295, CYAN), (0.300, 0.645, VIOLET), (0.650, 1.000, GREEN)]
        covers = [uv_cover(fig2, u0, 0.0, u1, 1.0) for u0, u1, _ in panels]
        for c in covers:
            c.set_opacity(0)
            self.add(c)

        lines = [
            "Table detection draws a box around every table on the page.",
            "Structure recognition recovers the grid: every row, every column, every cell.",
            "Functional analysis labels which cells are headers and which hold the data.",
        ]
        frame = None
        for k, ((u0, u1, col), line) in enumerate(zip(panels, lines)):
            new_frame = uv_rect(fig2, u0, 0.0, u1, 1.0, color=col, sw=4)
            anims = [covers[i].animate.set_opacity(0.0 if i == k else 0.78)
                     for i in range(3)]
            if frame is None:
                anims.append(Create(new_frame))
            else:
                anims.append(Transform(frame, new_frame))
            self.play(*anims, run_time=0.9)
            if frame is None:
                frame = new_frame
            cap = self.replace_say(cap, line, color=col)
            self.beat(2.2)

        self.play(FadeOut(frame),
                  *[c.animate.set_opacity(0.0) for c in covers], run_time=0.8)
        cap = self.replace_say(cap, "PubTables-1M is the first dataset that "
                                    "labels all three of these at scale.",
                               color=GOLD)
        self.beat(2.2)

        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 -- where a million labeled tables come from
    # ====================================================================== #
    def scene_scale(self):
        self.section_header("3 · A million real tables", color=GOLD)

        pdf = chip("PDF page", CYAN, w=2.9)
        xml = chip("XML markup", VIOLET, w=2.9)
        pdf.move_to([-4.7, 1.75, 0])
        xml.move_to([-4.7, 0.15, 0])
        merged = chip("one fully labeled table", GOLD, w=4.6, h=1.0)
        merged.move_to([0.7, 0.95, 0])
        a1 = harrow(pdf.get_right(), merged.get_left() + UP * 0.18, color=CYAN)
        a2 = harrow(xml.get_right(), merged.get_left() + DOWN * 0.18, color=VIOLET)
        note = txt("how it looks", fs=18, color=MUTED).next_to(pdf, DOWN, buff=0.16)
        note2 = txt("what it says", fs=18, color=MUTED).next_to(xml, DOWN, buff=0.16)

        cap = self.show_say("The source is PubMed Central Open Access, "
                            "millions of real scientific articles.")
        self.play(FadeIn(pdf, shift=RIGHT * 0.2), FadeIn(note), run_time=0.7)
        self.play(FadeIn(xml, shift=RIGHT * 0.2), FadeIn(note2), run_time=0.7)
        self.beat(1.6)
        cap = self.replace_say(cap, "Every article ships twice: a PDF carries how "
                                    "each page looks, XML carries what it says.")
        self.beat(2.0)
        self.play(GrowArrow(a1), GrowArrow(a2), FadeIn(merged, scale=0.9),
                  run_time=1.0)
        cap = self.replace_say(cap, "Aligning the two, character by character, "
                                    "gives every cell pixel coordinates. No "
                                    "human annotation.")
        self.beat(2.4)

        # ---- the size chart -------------------------------------------------
        diagram = VGroup(pdf, xml, merged, a1, a2, note, note2)
        self.play(FadeOut(diagram), run_time=0.6)

        sub = txt("Number of annotated tables per dataset (paper, Table 1)",
                  fs=20, color=MUTED)
        sub.move_to([0, 2.55, 0])
        self.play(FadeIn(sub), run_time=0.6)

        data = [
            ("SciTSR", 15, STEEL),
            ("FinTabNet", 113, STEEL),
            ("TableBank", 145, STEEL),
            ("PubTabNet", 510, STEEL),
            ("PubTables-1M", 948, GOLD),
        ]
        x0 = -3.75
        rows = Group()
        bars = []
        for i, (name, val, col) in enumerate(data):
            y = 1.85 - i * 0.82
            label = txt(name, fs=20,
                        color=INK if col == GOLD else MUTED,
                        weight="BOLD" if col == GOLD else None)
            label.move_to([x0 - 0.25 - label.width / 2, y, 0])
            w = max(0.12, val / 948 * 7.0)
            bar = Rectangle(width=w, height=0.48, stroke_width=0,
                            fill_color=col, fill_opacity=0.92)
            bar.move_to([x0 + w / 2, y, 0])
            vtxt = txt(f"{val}K", fs=19,
                       color=GOLD if col == GOLD else MUTED)
            vtxt.move_to([x0 + w + 0.22 + vtxt.width / 2, y, 0])
            rows.add(label, vtxt)
            bars.append(bar)
        axis = Line([x0, 1.85 + 0.42, 0], [x0, 1.85 - 4 * 0.82 - 0.42, 0],
                    stroke_width=2, color=FAINT)
        self.play(Create(axis),
                  LaggedStart(*[FadeIn(m) for m in rows if isinstance(m, VMobject)],
                              lag_ratio=0.06),
                  run_time=0.9)
        self.play(LaggedStart(*[GrowFromEdge(b, LEFT) for b in bars],
                              lag_ratio=0.15), run_time=1.6)
        cap = self.replace_say(cap, "The result is 947,642 labeled tables, "
                                    "nearly twice the largest dataset before it.",
                               color=GOLD)
        self.beat(2.4)
        cap = self.replace_say(cap, "And the labels are complete: every row, "
                                    "column, and cell has a box, even blank cells.")
        self.beat(2.4)

        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 -- oversegmentation, and the canonicalization fix (Figure 3)
    # ====================================================================== #
    def scene_canonical(self):
        self.section_header("4 · The flaw and the fix", color=RED)

        cap = self.show_say("But there was a catch, and it sat inside the "
                            "labels themselves.")
        fig_h, fig_pos = 2.85, np.array([0, 0.72, 0])
        f3a = image_card("fig3a_overseg.jpg", height=fig_h)
        f3a.move_to(fig_pos)
        cred = credit(f3a, "Figure 3 of the paper (CC BY 4.0)")
        self.play(FadeIn(f3a, shift=UP * 0.2), FadeIn(cred), run_time=0.9)
        self.beat(1.4)

        cap = self.replace_say(cap, "In the source markup, one spanning header "
                                    "is often stored as several separate blank "
                                    "cells.")
        marks = VGroup(
            uv_rect(f3a, 0.012, 0.02, 0.214, 0.35, color=RED, sw=4),
            uv_rect(f3a, 0.757, 0.02, 0.983, 0.35, color=RED, sw=4),
            uv_rect(f3a, 0.012, 0.35, 0.109, 0.965, color=RED, sw=4),
        )
        self.play(LaggedStart(*[Create(m) for m in marks], lag_ratio=0.25),
                  run_time=1.4)
        self.beat(2.2)

        cap = self.replace_say(cap, "The rendered table looks identical either "
                                    "way, so the same layout gets encoded in "
                                    "conflicting ways.")
        self.beat(2.4)
        cap = self.replace_say(cap, "The paper calls this oversegmentation, and "
                                    "in crowd-sourced datasets it is the norm, "
                                    "not the exception.")
        self.beat(2.2)
        cap = self.replace_say(cap, "Among tables with a projected row header: "
                                    "58.7% oversegmented in PubTabNet, 98.9% in "
                                    "FinTabNet.", color=RED)
        self.beat(2.6)

        # ---- the fix: canonicalization (Algorithm 1) ------------------------
        alg = image_card("alg1_canon.jpg", height=4.5)
        alg.move_to([4.05, 0.15, 0])
        alg_cred = credit(alg, "Algorithm 1 of the paper", fs=13)
        self.play(
            f3a.animate.scale(2.32 / fig_h).move_to([-3.35, 0.85, 0]),
            FadeOut(cred), FadeOut(marks),
            run_time=0.9,
        )
        self.play(FadeIn(alg, shift=LEFT * 0.3), FadeIn(alg_cred), run_time=0.9)
        cap = self.replace_say(cap, "The fix is a short mechanical procedure "
                                    "the paper calls canonicalization.")
        self.beat(2.0)
        cap = self.replace_say(cap, "It infers the true header cells, then "
                                    "merges fragments that belong to one "
                                    "spanning cell.")
        self.beat(2.4)

        # ---- before -> after crossfade --------------------------------------
        self.play(FadeOut(alg), FadeOut(alg_cred), run_time=0.7)
        self.play(f3a.animate.scale(fig_h / 2.32).move_to(fig_pos), run_time=0.8)
        f3b = image_card("fig3b_canonical.jpg", height=fig_h)
        f3b.move_to(fig_pos)
        cred2 = credit(f3b, "Figure 3 of the paper (CC BY 4.0)")
        self.play(FadeIn(f3b), FadeOut(f3a), FadeIn(cred2), run_time=1.2)
        pulse = uv_rect(f3b, 0.757, 0.02, 0.983, 0.35, color=GOLD, sw=4)
        self.play(Create(pulse), run_time=0.7)
        self.play(FadeOut(pulse), run_time=0.7)
        cap = self.replace_say(cap, "After the merge, shown in pale gold, every "
                                    "table has exactly one valid structure.",
                               color=GOLD)
        self.beat(2.2)
        cap = self.replace_say(cap, "Canonicalization adjusted 34.7% of all "
                                    "tables. Oversegmented headers left in the "
                                    "final data: zero.")
        self.beat(2.6)

        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 -- one detector, six boxes, and the payoff (Figure 4)
    # ====================================================================== #
    def scene_model(self):
        self.section_header("5 · One detector, and the payoff", color=GREEN)

        fig4 = image_card("fig4_dilated.jpg", height=4.3)
        fig4.move_to([-3.35, 0.42, 0])
        cred = credit(fig4, "Figure 4 of the paper (CC BY 4.0)", fs=14)

        bullets = VGroup(
            txt("Every subtask becomes object detection.", fs=21),
            txt("Six box classes describe a whole table:", fs=21),
            txt("rows, columns, two kinds of header,", fs=21, color=MUTED),
            txt("spanning cells, and the table itself.", fs=21, color=MUTED),
            txt("Dilated boxes tile it with no gaps.", fs=21),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        bullets.move_to([4.05, 1.0, 0])
        for m in bullets:
            if m.width > 5.6:
                m.scale_to_fit_width(5.6)

        self.play(FadeIn(fig4, shift=UP * 0.2), FadeIn(cred), run_time=0.9)
        cap = self.show_say("Now the model. The paper frames all three "
                            "subtasks as plain object detection.")
        self.play(FadeIn(bullets[0], shift=RIGHT * 0.15), run_time=0.6)
        self.beat(2.0)
        cap = self.replace_say(cap, "Six kinds of boxes are enough, drawn here "
                                    "over a real table from the dataset.")
        self.play(LaggedStart(*[FadeIn(m, shift=RIGHT * 0.15)
                                for m in bullets[1:4]], lag_ratio=0.2),
                  run_time=1.0)
        self.beat(2.2)
        cap = self.replace_say(cap, "Each box is dilated until neighbours meet "
                                    "halfway, so the classes tile the table "
                                    "with no gaps and no overlaps.")
        self.play(FadeIn(bullets[4], shift=RIGHT * 0.15), run_time=0.6)
        self.beat(2.4)
        cap = self.replace_say(cap, "A standard DETR learns this end to end. "
                                    "No custom table architecture at all.",
                               color=GREEN)
        self.beat(2.2)

        # ---- results ---------------------------------------------------------
        self.play(FadeOut(fig4), FadeOut(cred), FadeOut(bullets), run_time=0.7)

        base_y = -1.55
        baseline = Line([-6.6, base_y, 0], [6.6, base_y, 0],
                        stroke_width=2, color=FAINT)
        self.play(Create(baseline), run_time=0.5)

        def bar_pair(cx, title, l_name, r_name, l_val, r_val, r_col):
            g = Group()
            t = txt(title, fs=21, weight="BOLD").move_to([cx, 2.0, 0])
            if t.width > 4.3:
                t.scale_to_fit_width(4.3)
            pieces = []
            for dx, name, val, col in [(-0.62, l_name, l_val, STEEL),
                                       (0.62, r_name, r_val, r_col)]:
                h = val * 3.1
                bar = Rectangle(width=0.95, height=h, stroke_width=0,
                                fill_color=col, fill_opacity=0.92)
                bar.move_to([cx + dx, base_y + h / 2, 0])
                v = txt(f"{val:.3f}", fs=20,
                        color=col if col != STEEL else MUTED)
                v.next_to(bar, UP, buff=0.12)
                n = txt(name, fs=16, color=MUTED)
                if n.width > 1.75:
                    n.scale_to_fit_width(1.75)
                n.move_to([cx + dx, base_y - 0.28, 0])
                pieces.append((bar, v, n))
            return t, pieces

        pairs = [
            bar_pair(-4.45, "Table detection (AP)",
                     "Faster R-CNN", "DETR", 0.825, 0.966, CYAN),
            bar_pair(0.0, "Structure + analysis (AP)",
                     "Faster R-CNN", "DETR", 0.722, 0.912, VIOLET),
            bar_pair(4.45, "Exact match, complex tables",
                     "original labels", "canonical", 0.536, 0.694, GOLD),
        ]
        for t, pieces in pairs[:2]:
            self.play(FadeIn(t), run_time=0.5)
            self.play(*[GrowFromEdge(b, DOWN) for b, _, _ in pieces],
                      *[FadeIn(v) for _, v, _ in pieces],
                      *[FadeIn(n) for _, _, n in pieces], run_time=0.9)
        cap = self.replace_say(None, "Trained on PubTables-1M, DETR reaches "
                                     "0.966 AP on detection and 0.912 on "
                                     "structure plus analysis.")
        self.beat(2.6)

        t, pieces = pairs[2]
        self.play(FadeIn(t), run_time=0.5)
        self.play(*[GrowFromEdge(b, DOWN) for b, _, _ in pieces],
                  *[FadeIn(v) for _, v, _ in pieces],
                  *[FadeIn(n) for _, _, n in pieces], run_time=0.9)
        cap = self.replace_say(cap, "And on the hardest tables, exact content "
                                    "match jumps from 0.536 to 0.694.",
                               color=GOLD)
        self.beat(2.4)
        cap = self.replace_say(cap, "Same architecture in both runs. The only "
                                    "change is cleaner, canonicalized labels.")
        self.beat(2.6)

        # ---- takeaway card ---------------------------------------------------
        self.wipe(rt=0.8)
        take = txt("Clean ground truth is a model upgrade.", fs=34,
                   color=INK, weight="BOLD")
        rule = self._rule_under(take, pad=0.6)
        sub = txt("The dataset and models are open source: Microsoft's "
                  "Table Transformer.", fs=22, color=MUTED)
        sub.move_to([0, rule.get_bottom()[1] - 0.6, 0])
        self.play(Write(take), Create(rule), run_time=1.4)
        self.play(FadeIn(sub, shift=UP * 0.15), run_time=0.7)
        self.beat(2.6)

        self.settle()
        self.wipe()

    # ---- the whole film ------------------------------------------------------
    def play_all(self):
        self.play_intro()
        self.scene_paper()
        self.scene_tasks()
        self.scene_scale()
        self.scene_canonical()
        self.scene_model()
        self.play_outro()


# ---- one class per scene, plus the full film ------------------------------- #
class Intro(_PTBase):
    def construct(self):
        self.play_intro()


class Paper(_PTBase):
    def construct(self):
        self.scene_paper()


class Tasks(_PTBase):
    def construct(self):
        self.scene_tasks()


class Scale(_PTBase):
    def construct(self):
        self.scene_scale()


class Canonical(_PTBase):
    def construct(self):
        self.scene_canonical()


class ModelResults(_PTBase):
    def construct(self):
        self.scene_model()


class Outro(_PTBase):
    def construct(self):
        self.play_outro()


class PubTables1M(_PTBase):
    def construct(self):
        self.play_all()

"""OmniDocBench -- can AI actually read a document? A ~4-minute explainer.

OmniDocBench (Ouyang, Qu, Zhou, Zhu, Zhang et al., Shanghai AI Laboratory,
arXiv:2412.07626) is a benchmark for document parsing: given a PDF page, how
well does a model (a classic pipeline or a vision-language model) recover its
text, tables, formulas and reading order.

This film builds the idea from the ground up:

    1. Problem      -- existing benchmarks cover 1-2 document types with crude
                       text-similarity metrics; Table 1 shows OmniDocBench is
                       the only one that covers all of it.
    2. Dataset       -- 200k PDFs -> clustering -> 6,000 diverse pages ->
                       981 final pages across 9 real document types.
    3. Annotation    -- every page gets layout boxes, attributes, reading
                       order; a 3-stage auto-annotate / correct / inspect
                       pipeline builds it.
    4. Evaluation    -- Extract -> Match -> per-type metric -> Overall.
    5. Contenders    -- Pipeline Tools vs Expert VLMs vs General VLMs.
    6. Results I      -- Table 2, verbatim, panned with a moving camera.
    7. Results II     -- Table 3, verbatim, the "no free lunch" twist.
    8. Takeaway      -- why a fine-grained benchmark matters.

Everything uses ``Text`` (Pango) instead of ``Tex`` so it renders with no
LaTeX. Every number shown in a table is transcribed verbatim from the paper's
PDF (cross-checked against both a text extraction and a hi-res crop of each
table) -- see README for the exact table/page mapping.

Env knobs:
    ODB_QUICK=1   shorten every hold for a fast sanity render
    ODB_DELAY=..  override the between-step motion rhythm
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")

# --- crisp text ------------------------------------------------------------ #
# Manim's Text (Pango) mangles letter/word spacing below ~20pt. Fix it once:
# render every glyph at a large base size and scale the mobject *down*.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("ODB_QUICK") == "1"
DELAY = float(os.environ.get("ODB_DELAY", "0.28" if QUICK else "1.8"))
ANIM_SLOW = 1.0 if QUICK else 1.1
END_HOLD = 0.2 if QUICK else 1.8

# ---- palette (house style, shared with Docling/Transformer/GeoDetect) ----- #
BG = "#0E1117"
INK = "#F5F3EF"
MUTED = "#8A93A6"
FAINT = "#3A4152"
PAPER = "#F4F1EA"
PAPER_INK = "#2A2E37"
PAPER_EDGE = "#C9C4B6"

TITLE_C = "#FFD166"     # gold    -- titles / headings / "best" highlight
TEXT_C = "#5B8DEF"      # blue    -- text / OCR
TABLE_C = "#2EC4B6"     # teal    -- tables
FIG_C = "#C792EA"       # violet  -- figures / formulas
CAP_C = "#9AA3B2"       # grey    -- captions
FURN_C = "#FF5C5C"      # red     -- bad / worst
GOOD = "#3DD68C"
BAD = "#FF5C5C"
ACCENT = "#FFD166"
BYLINE = "#5B8DEF"

# model-class colours (Pipeline Tools / Expert VLMs / General VLMs)
PIPE_C = "#5B8DEF"      # blue
EXPERT_C = "#C792EA"    # violet
GENERAL_C = "#FFD166"   # gold
OCR_C = "#FF8C42"       # orange -- OCR / reading pixels

MONO = "Menlo"
PLAIN = "#D6DEEB"
COMMENT = "#5F6B7E"

RNG = np.random.default_rng(7)
FONT = "Helvetica Neue"
_BaseText.set_default(font=FONT)


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


def _safe_t2c(s, table):
    present = {k: v for k, v in table.items() if k in s}
    keys = list(present)
    return {k: v for k, v in present.items()
            if not any(k != o and k in o for o in keys)}


def chip(text, color, fs=20, fill=0.14, w=None, h=0.56, tcolor=None,
         weight="NORMAL", radius=0.12):
    label = txt(text, fs=fs, color=tcolor or INK, weight=weight)
    width = (label.width + 0.5) if w is None else w
    if label.width > width - 0.24:
        label.scale((width - 0.24) / label.width)
    box = RoundedRectangle(width=width, height=h, corner_radius=radius,
                            stroke_color=color, stroke_width=2.5,
                            fill_color=color, fill_opacity=fill)
    label.move_to(box)
    return VGroup(box, label)


def arr(a, b, color=MUTED, sw=4, buff=0.14, tip=0.22):
    """``a``/``b`` MUST be explicit points (``chip.get_right()``, not ``chip``).

    Passing a bare compound Mobject (a VGroup of a RoundedRectangle + Text)
    routes through Manim's ``get_boundary_point()``, which searches the
    mobject's raw bezier point cloud for the extremal point along the
    connecting direction -- for a rectangle+text group this is NOT the clean
    mid-edge point and is asymmetric between the two ends, so the arrow comes
    out diagonal or offset even when both mobjects share the same y-center.
    Always pass ``.get_right()``/``.get_left()``/``.get_top()``/``.get_bottom()``
    (bounding-box based, reliable) instead.
    """
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


def doc_icon(kind="text", w=0.9, h=1.2, color=INK):
    """A small page icon whose interior sketch hints at the document TYPE.

    kind in {"text","table","slides","photo","exam","newspaper"} -- used by
    the 9-document-type grid (each real type maps to one of these looks).
    """
    body = RoundedRectangle(width=w, height=h, corner_radius=0.07,
                             stroke_color=color, stroke_width=2.2,
                             fill_color=PAPER, fill_opacity=0.96)
    g = VGroup(body)

    def hline(frac, y, sw=2.0, col=PAPER_INK, op=0.7):
        ln = Line(ORIGIN, [w * frac, 0, 0], stroke_color=col, stroke_width=sw).set_opacity(op)
        ln.move_to([body.get_left()[0] + 0.09 + ln.width / 2, y, 0])
        return ln

    top = body.get_top()[1] - 0.14
    if kind == "table":
        g.add(hline(0.55, top, col=TITLE_C, sw=2.6))
        rows, cols = 3, 2
        gw, gh = w * 0.78, h * 0.42
        gx = body.get_left()[0] + 0.11
        gy = top - 0.22 - gh
        grid = Rectangle(width=gw, height=gh, stroke_color=TABLE_C, stroke_width=1.6,
                          fill_opacity=0)
        grid.move_to([gx + gw / 2, gy + gh / 2, 0])
        g.add(grid)
        for r in range(1, rows):
            y = gy + gh - r * (gh / rows)
            g.add(Line([gx, y, 0], [gx + gw, y, 0], stroke_color=TABLE_C,
                       stroke_width=1.1).set_opacity(0.7))
        for c in range(1, cols):
            x = gx + c * (gw / cols)
            g.add(Line([x, gy, 0], [x, gy + gh, 0], stroke_color=TABLE_C,
                       stroke_width=1.1).set_opacity(0.7))
        g.add(hline(0.7, gy - 0.16, col=PAPER_INK, op=0.55))
        g.add(hline(0.5, gy - 0.32, col=PAPER_INK, op=0.55))
    elif kind == "slides":
        box = Rectangle(width=w * 0.82, height=h * 0.5, stroke_color=TITLE_C,
                        stroke_width=2.0, fill_opacity=0)
        box.move_to([0, h * 0.14, 0])
        g.add(box)
        g.add(Line([-w * 0.3, h * 0.14, 0], [-w * 0.05, h * 0.14, 0],
                   stroke_color=FIG_C, stroke_width=8).set_opacity(0.65))
        g.add(hline(0.6, -h * 0.24))
        g.add(hline(0.4, -h * 0.36))
    elif kind == "photo":
        g.add(hline(0.5, top, col=TITLE_C, sw=2.6))
        frame = Rectangle(width=w * 0.8, height=h * 0.42, stroke_color=CAP_C,
                          stroke_width=1.6, fill_opacity=0)
        frame.move_to([0, top - 0.24 - h * 0.21, 0])
        mtn = Polygon([-w * 0.32, -h * 0.14, 0], [-w * 0.08, h * 0.08, 0],
                      [w * 0.08, -h * 0.04, 0], [w * 0.32, -h * 0.14, 0])
        mtn.move_to(frame).set_stroke(CAP_C, 1.4).set_fill(opacity=0)
        g.add(frame, mtn)
        for i in range(2):
            g.add(hline(0.6, frame.get_bottom()[1] - 0.16 - i * 0.14, op=0.5))
    elif kind == "exam":
        g.add(hline(0.4, top, col=TITLE_C, sw=2.4))
        for i in range(4):
            y = top - 0.24 - i * 0.2
            box = Square(0.09, stroke_color=PAPER_INK, stroke_width=1.4, fill_opacity=0)
            box.move_to([body.get_left()[0] + 0.18, y, 0])
            ln = hline(0.55, y)
            ln.move_to([body.get_left()[0] + 0.34 + ln.width / 2, y, 0])
            g.add(box, ln)
    elif kind == "newspaper":
        g.add(hline(0.7, top, col=PAPER_INK, sw=3.2))
        colgap = 0.06
        colw = (w * 0.82 - colgap) / 2
        for c in range(2):
            cx = body.get_left()[0] + 0.09 + colw / 2 + c * (colw + colgap)
            for i in range(5):
                y = top - 0.22 - i * 0.14
                ln = Line(ORIGIN, [colw, 0, 0], stroke_color=PAPER_INK,
                          stroke_width=1.4).set_opacity(0.55)
                ln.move_to([cx, y, 0])
                g.add(ln)
    else:  # "text" -- academic paper / textbook / book / magazine / notes default
        g.add(hline(0.55, top, col=TITLE_C, sw=2.6))
        for i in range(5):
            y = top - 0.26 - i * 0.16
            frac = 0.82 if i % 3 != 2 else 0.5
            g.add(hline(frac, y))
    return g


DOC_TYPES = [
    ("Academic Papers", "text"),
    ("Textbooks", "text"),
    ("Exam Papers", "exam"),
    ("Slides", "slides"),
    ("Books", "text"),
    ("Magazines", "photo"),
    ("Notes", "text"),
    ("Newspapers", "newspaper"),
    ("Financial Reports", "table"),
]


def doc_type_card(name, kind, color=INK, icon_w=0.85, icon_h=1.12, fs=15):
    icon = doc_icon(kind, w=icon_w, h=icon_h, color=color)
    lab = txt(name, fs=fs, color=INK)
    if lab.width > icon_w + 0.5:
        lab.scale((icon_w + 0.5) / lab.width)
    card = VGroup(icon, lab).arrange(DOWN, buff=0.12)
    return card


# ========================================================================== #
# Verbatim paper screenshots -- real crops of the actual PDF (300-500dpi),
# never a hand-rebuilt reconstruction. Pattern matches animations/PubTables.
# ========================================================================== #
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


def uv_rect(card, u0, v0, u1, v1, color=TITLE_C, sw=3.2, fill=0.0, radius=0.03):
    img = card[0]
    r = RoundedRectangle(width=(u1 - u0) * img.width, height=(v1 - v0) * img.height,
                          corner_radius=radius, stroke_color=color, stroke_width=sw,
                          fill_color=color, fill_opacity=fill)
    r.move_to(uv_point(card, (u0 + u1) / 2, (v0 + v1) / 2))
    return r


def uv_cover(card, u0, v0, u1, v1, opacity=0.82):
    """A BG-coloured veil over part of a screenshot (spotlight the rest)."""
    img = card[0]
    r = Rectangle(width=(u1 - u0) * img.width, height=(v1 - v0) * img.height,
                  stroke_width=0, fill_color=BG, fill_opacity=opacity)
    r.move_to(uv_point(card, (u0 + u1) / 2, (v0 + v1) / 2))
    return r


def credit(card, label, fs=15, color=MUTED):
    t = txt(label, fs=fs, color=color, slant=ITALIC)
    t.next_to(card, DOWN, buff=0.16)
    return t


def _num_badge(n, center, color=ACCENT, r=0.16):
    """A small numbered circle marking one step of a reading-order sequence."""
    c = Circle(radius=r, stroke_color=color, stroke_width=2.4,
               fill_color=BG, fill_opacity=1.0)
    t = txt(str(n), fs=20, color=INK, weight="BOLD")
    t.scale_to_fit_height(r * 1.05)
    return VGroup(c, t).move_to([center[0], center[1], 0])


def _annot_page(w=2.9, h=4.3):
    """A simple wireframe PDF-page mockup: a title bar, one paragraph of
    wire-frame lines, a small figure box and a small table grid with a
    one-line caption underneath -- just enough structure to hang colour-coded
    bounding boxes, attribute chips, reading-order badges and an affiliation
    link on top of. Built centered on the origin; the caller moves the whole
    returned group afterwards (the ``regions`` entries are the same objects,
    so they move with it).

    Returns ``(page_group, regions)`` with ``regions`` keys
    "title", "para", "figure", "table", "caption".
    """
    page = Rectangle(width=w, height=h, fill_color=PAPER, fill_opacity=1.0,
                      stroke_color=PAPER_EDGE, stroke_width=1.6)
    g = VGroup(page)
    regions = {}
    margin = 0.22
    left = -w / 2 + margin
    cw = w - 2 * margin
    y = h / 2 - margin - 0.08

    # title bar (one thick rule)
    title = Line(ORIGIN, [cw * 0.55, 0, 0], stroke_color=PAPER_INK,
                 stroke_width=5).set_opacity(0.88)
    title.move_to([left + title.width / 2, y, 0])
    g.add(title)
    regions["title"] = title
    y -= 0.34

    # one paragraph of wire-frame lines
    rng = np.random.default_rng(11)
    para = VGroup()
    for i in range(4):
        frac = rng.uniform(0.72, 1.0) if i < 3 else rng.uniform(0.4, 0.6)
        ln = Line(ORIGIN, [cw * frac, 0, 0], stroke_color=PAPER_INK,
                  stroke_width=2.2).set_opacity(0.72)
        para.add(ln)
    para.arrange(DOWN, buff=0.11, aligned_edge=LEFT)
    para.move_to([left + para.width / 2, y - para.height / 2, 0])
    g.add(para)
    regions["para"] = para
    y -= para.height + 0.26

    # figure box: a bordered rectangle with a tiny mountain + sun sketch
    fig_w, fig_h = cw * 0.62, 0.95
    fig_box = Rectangle(width=fig_w, height=fig_h, stroke_color=PAPER_INK,
                        stroke_width=1.8, fill_opacity=0)
    fig_box.move_to([left + fig_w / 2, y - fig_h / 2, 0])
    sun = Circle(radius=0.09, stroke_width=0, fill_color=PAPER_INK,
                fill_opacity=0.5)
    sun.move_to([fig_box.get_left()[0] + fig_w * 0.24,
                fig_box.get_top()[1] - fig_h * 0.28, 0])
    mtn = Polygon([fig_box.get_left()[0] + fig_w * 0.1, fig_box.get_bottom()[1] + fig_h * 0.18, 0],
                  [fig_box.get_center()[0] - fig_w * 0.05, fig_box.get_top()[1] - fig_h * 0.2, 0],
                  [fig_box.get_center()[0] + fig_w * 0.18, fig_box.get_bottom()[1] + fig_h * 0.32, 0],
                  [fig_box.get_right()[0] - fig_w * 0.08, fig_box.get_top()[1] - fig_h * 0.28, 0],
                  [fig_box.get_right()[0] - fig_w * 0.06, fig_box.get_bottom()[1] + fig_h * 0.18, 0])
    mtn.set_stroke(PAPER_INK, 1.6).set_fill(opacity=0)
    figure = VGroup(fig_box, sun, mtn)
    g.add(figure)
    regions["figure"] = figure
    y -= fig_h + 0.24

    # table: a small grid
    tab_w, tab_h = cw * 0.86, 0.86
    rows, cols = 3, 2
    outer = Rectangle(width=tab_w, height=tab_h, stroke_color=PAPER_INK,
                      stroke_width=1.8, fill_opacity=0)
    outer.move_to([left + tab_w / 2, y - tab_h / 2, 0])
    table = VGroup(outer)
    for r in range(1, rows):
        yy = outer.get_top()[1] - r * (tab_h / rows)
        table.add(Line([outer.get_left()[0], yy, 0], [outer.get_right()[0], yy, 0],
                       stroke_color=PAPER_INK, stroke_width=1.2).set_opacity(0.6))
    for c in range(1, cols):
        xx = outer.get_left()[0] + c * (tab_w / cols)
        table.add(Line([xx, outer.get_top()[1], 0], [xx, outer.get_bottom()[1], 0],
                       stroke_color=PAPER_INK, stroke_width=1.2).set_opacity(0.6))
    g.add(table)
    regions["table"] = table
    y -= tab_h + 0.4

    # one-line caption under the table (its own region, well clear of the
    # table so a short affiliation connector can be drawn between them)
    cap = Line(ORIGIN, [tab_w * 0.62, 0, 0], stroke_color=PAPER_INK,
              stroke_width=2.0).set_opacity(0.55)
    cap.move_to([left + tab_w * 0.31, y, 0])
    g.add(cap)
    regions["caption"] = cap

    return g, regions


# NEW HELPER (added for scene_contenders only, flag for review before merge):
# a single class-of-system card -- coloured header, a short plain-sentence
# description, and its representative model names as chip() tags stacked
# underneath. Module-level like chip()/arr()/doc_icon() above since it needs
# no scene state; kept as close to scene_contenders (its only caller) as a
# module-level function can be.
def _contender_card(name, color, desc_lines, models, box_w=4.15, box_h=4.3):
    header = txt(name, fs=25, color=color, weight="BOLD")
    rule = Line(LEFT, RIGHT).set_width(box_w - 0.7).set_stroke(color=color, width=2.5)
    rule.next_to(header, DOWN, buff=0.16)

    desc = VGroup(*[txt(line, fs=16.5, color=INK) for line in desc_lines])
    desc.arrange(DOWN, buff=0.08)
    if desc.width > box_w - 0.5:
        desc.scale((box_w - 0.5) / desc.width)
    desc.next_to(rule, DOWN, buff=0.22)

    chip_tags = []
    for m in models:
        c = chip(m, color, fs=17, h=0.5)
        if c.width > box_w - 0.5:
            c.scale((box_w - 0.5) / c.width)
        chip_tags.append(c)
    chips = VGroup(*chip_tags).arrange(DOWN, buff=0.15)
    chips.next_to(desc, DOWN, buff=0.32)

    content = VGroup(header, rule, desc, chips)
    box = RoundedRectangle(width=box_w, height=box_h, corner_radius=0.18,
                            stroke_color=color, stroke_width=2.5,
                            fill_color=color, fill_opacity=0.07)
    content.move_to(box)
    return VGroup(box, content)


# ========================================================================== #
# ========================================================================== #
class _OmniDocBenchBase(MovingCameraScene):
    """MovingCameraScene throughout (not just Scene) so the Table 2 results
    scene can pan/zoom its camera across a wide verbatim table; every other
    scene simply never touches ``self.camera.frame`` and behaves like a plain
    ``Scene``."""

    def setup(self):
        super().setup()
        self.camera.background_color = BG
        self._cap = None

    def play(self, *anims, **kwargs):
        if not (len(anims) == 1 and isinstance(anims[0], Wait)):
            rt = kwargs.get("run_time")
            if rt is not None:
                kwargs["run_time"] = rt * ANIM_SLOW
        return super().play(*anims, **kwargs)

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
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)
        self._cap = None

    def section_header(self, label, color=ACCENT):
        t = Text(label, font_size=32, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=3)
        return VGroup(t, line)

    def caption(self, s, color=INK, fs=23):
        t = Text(s, font_size=fs, color=color)
        if t.width > 12.9:
            t.scale_to_fit_width(12.9)
        t.to_edge(DOWN, buff=0.45)
        return t

    def say(self, s, color=INK, fs=23, rt=0.6):
        new = self.caption(s, color, fs)
        if self._cap is None:
            self._cap = new
            self.play(FadeIn(new, shift=UP * 0.1), run_time=rt)
        else:
            self.play(Transform(self._cap, new), run_time=rt)
        return self._cap

    def cite(self, s):
        return Text(s, font_size=15, color=MUTED, slant=ITALIC).to_edge(DOWN, buff=0.16)

    def _rule(self, m, color=ACCENT, pad=1.0, drop=0.45, sw=3):
        return Line([m.get_left()[0] - pad, m.get_bottom()[1] - drop, 0],
                    [m.get_right()[0] + pad, m.get_bottom()[1] - drop, 0]
                    ).set_stroke(color=color, width=sw)

    def code_pill(self, s, table, fs=19, w_max=11.0):
        code = Text(s, font=MONO, font_size=fs, color=PLAIN, t2c=_safe_t2c(s, table))
        bg = RoundedRectangle(width=code.width + 0.5, height=code.height + 0.36,
                              corner_radius=0.1, stroke_color=FAINT, stroke_width=1.6,
                              fill_color="#0A0E15", fill_opacity=1.0)
        bg.move_to(code)
        pill = VGroup(bg, code)
        if pill.width > w_max:
            pill.scale(w_max / pill.width)
        return pill

    # ---- house intro / outro cards ---------------------------------------- #
    def introduction(self, title1, title2, byline_color=BYLINE):
        header = Text(title1, font_size=56, color=INK, weight="BOLD")
        if header.width > 12.0:
            header.scale(12.0 / header.width)
        line = self._rule(header, ACCENT, pad=1.0, drop=0.45)
        writer = Text("Created by Ptolémé", font_size=28, color=byline_color)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        sub = Text(title2, font_size=30, color=MUTED)
        if sub.width > 12.4:
            sub.scale(12.4 / sub.width)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.card_wait(2.0)
        return VGroup(header, writer, line)

    def play_intro(self):
        grp = self.introduction("OmniDocBench",
                                 "Can AI actually read a document?")
        self.play(FadeOut(grp), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = self._rule(header, ACCENT, pad=1.0, drop=0.45)
        writer = Text("Created by Ptolémé", font_size=28, color=BYLINE)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = Text("A fair benchmark doesn't just score you. It shows you where you fail.",
                     font_size=25, color=ACCENT)
        if recap.width > 12.4:
            recap.scale(12.4 / recap.width)
        recap.next_to(writer, DOWN, buff=0.5)
        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap), run_time=0.8)
        self.card_wait(2.2)
        self.play(FadeOut(VGroup(header, line, writer, recap)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene stubs -- filled in below (each is a self-contained beat)
    # ====================================================================== #
    def scene_problem(self):
        header = self.section_header("The problem: can we trust a parser's score?", ACCENT)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        self.say("Large language models and RAG systems increasingly depend on "
                  "high-quality, knowledge-rich data.", color=INK)
        self.beat(1.1)
        self.say("So accurately parsing a PDF page into structured text, tables, "
                  "formulas and reading order has become critical.", color=INK)
        self.beat(1.3)
        self.play(FadeOut(self._cap), run_time=0.4)
        self._cap = None

        # ---- two families of parsing systems -------------------------------- #
        # Built with a real input/output bookend (a page feeding in, structured
        # data coming out) so the diagram reads as a real system, not four
        # boxes floating in empty space -- and every arrow below connects
        # explicit .get_right()/.get_left() points, never bare mobjects (see
        # the docstring on arr(): passing a mobject routes through Manim's
        # unreliable get_boundary_point() and comes out diagonal).
        def input_glyph(color):
            return doc_icon("text", w=0.62, h=0.82, color=color)

        def output_glyph(color):
            g = RoundedRectangle(width=0.62, height=0.82, corner_radius=0.06,
                                 stroke_color=color, stroke_width=2.2,
                                 fill_color=color, fill_opacity=0.12)
            rows = VGroup(*[Rectangle(width=0.62 * f, height=0.07, stroke_width=0,
                                      fill_color=color, fill_opacity=0.85)
                            for f in (0.7, 0.55, 0.7, 0.4)])
            rows.arrange(DOWN, buff=0.08).move_to(g)
            return VGroup(g, rows)

        def pipeline_row(names_w, color, in_glyph, out_glyph):
            chips = [chip(s, color, fs=14, w=w, h=0.78) for s, w in names_w]
            row = VGroup(*chips).arrange(RIGHT, buff=0.55)
            src = in_glyph(color).next_to(row, LEFT, buff=0.55)
            dst = out_glyph(color).next_to(row, RIGHT, buff=0.55)
            arrows = VGroup(arr(src.get_right(), chips[0].get_left(), color=color, sw=3, tip=0.16))
            for i in range(len(chips) - 1):
                arrows.add(arr(chips[i].get_right(), chips[i + 1].get_left(),
                               color=color, sw=3, tip=0.16))
            arrows.add(arr(chips[-1].get_right(), dst.get_left(), color=color, sw=3, tip=0.16))
            return VGroup(src, row, dst), chips, arrows

        pipe_names_w = [("Layout\nDetection", 1.7), ("OCR", 1.1),
                         ("Table + Formula\nRecognition", 2.3),
                         ("Reading-Order\nAssembly", 2.0)]
        pipe_body, pipe_chips, pipe_arrows = pipeline_row(
            pipe_names_w, PIPE_C, input_glyph, output_glyph)
        pipe_label = txt("Pipeline-based systems", fs=22, color=PIPE_C, weight="BOLD")
        pipe_label.next_to(pipe_body, UP, buff=0.32)

        vlm_names_w = [("Vision-Language\nModel", 2.4)]
        vlm_body, vlm_chips, vlm_arrows = pipeline_row(
            vlm_names_w, GENERAL_C, input_glyph, output_glyph)
        vlm_label = txt("End-to-end vision-language models", fs=22, color=GENERAL_C,
                         weight="BOLD")
        vlm_label.next_to(vlm_body, UP, buff=0.32)

        pipe_block = VGroup(pipe_label, pipe_body, pipe_arrows)
        vlm_block = VGroup(vlm_label, vlm_body, vlm_arrows)
        diagram = VGroup(pipe_block, vlm_block).arrange(DOWN, buff=1.3)
        diagram.move_to([0, 0.35, 0])

        self.play(FadeIn(pipe_label, shift=RIGHT * 0.15), run_time=0.5)
        self.play(FadeIn(pipe_body[0], shift=RIGHT * 0.15), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in pipe_chips],
                               lag_ratio=0.18), run_time=1.0)
        self.play(FadeIn(pipe_body[2], shift=LEFT * 0.15), run_time=0.4)
        self.play(LaggedStart(*[GrowArrow(a) for a in pipe_arrows], lag_ratio=0.2),
                   run_time=0.9)
        self.say("One family, pipeline-based systems, chains layout detection, "
                  "OCR, table and formula recognition, then reading-order "
                  "assembly.", color=PIPE_C)
        self.beat(1.3)

        self.play(FadeIn(vlm_label, shift=RIGHT * 0.15), run_time=0.5)
        self.play(FadeIn(vlm_body[0], shift=RIGHT * 0.15), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in vlm_chips],
                               lag_ratio=0.18), run_time=0.7)
        self.play(FadeIn(vlm_body[2], shift=LEFT * 0.15), run_time=0.4)
        self.play(LaggedStart(*[GrowArrow(a) for a in vlm_arrows], lag_ratio=0.2),
                   run_time=0.7)
        self.say("The other family, end-to-end vision-language models, reads "
                  "the page image directly and writes structured Markdown in "
                  "one shot.", color=GENERAL_C)
        self.beat(1.3)

        self.play(FadeOut(diagram), FadeOut(self._cap), run_time=0.7)
        self._cap = None

        # ---- the three real limitations -------------------------------------- #
        self.say("But the benchmarks used to judge these systems have three "
                  "real limitations.", color=INK)
        self.beat(1.0)
        self.say("First, existing benchmarks mostly cover academic papers, "
                  "ignoring textbooks, exam papers, financial reports, "
                  "newspapers, notes and slides.", color=INK)
        self.beat(1.5)
        self.say("Second, generic text-similarity metrics like Edit Distance "
                  "or BLEU cannot fairly judge a table or formula that is "
                  "correct but formatted differently.", color=INK)
        self.beat(1.6)
        self.say("Third, most report only one overall score, with no "
                  "breakdown by element type or document type, hiding "
                  "exactly where a system is weak.", color=INK)
        self.beat(1.5)
        self.play(FadeOut(self._cap), run_time=0.4)
        self._cap = None

        # ---- Table 1, the paper's own page, reused verbatim -------------------- #
        self.say("Here is the paper's own comparison of benchmark coverage, "
                  "straight off the page.", color=ACCENT)
        self.beat(1.2)
        self.play(FadeOut(self._cap), run_time=0.4)
        self._cap = None

        t1 = image_card("table1_shot.jpg", height=4.9)
        t1.move_to([0, 0.35, 0])
        cred1 = credit(t1, "Table 1 of the paper, arXiv:2412.07626")
        self.play(FadeIn(t1, shift=UP * 0.15), FadeIn(cred1), run_time=1.1)
        self.beat(1.3)

        omni_box = uv_rect(t1, 0.002, 0.683, 0.998, 0.722, color=TITLE_C, sw=3.5)
        self.play(Create(omni_box), run_time=0.7)
        self.say("OmniDocBench is the only one with every box checked, "
                  "spanning nine document domains where the others cover "
                  "just one or two.", color=TITLE_C)
        self.beat(1.8)
        self.play(FadeOut(omni_box), FadeOut(t1), FadeOut(cred1), FadeOut(self._cap),
                  run_time=0.7)
        self._cap = None

        self.say("OmniDocBench is the first benchmark to check every box.",
                  color=TITLE_C)
        self.beat(1.5)
        self.settle()
        self.wipe()

    def scene_dataset(self):
        header = self.section_header("Building a diverse, 981-page benchmark", ACCENT)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        self.say("Building a fair benchmark starts with a genuinely diverse "
                  "pool of real documents.", color=INK)
        self.beat(1.4)
        self.play(FadeOut(self._cap), run_time=0.4)
        self._cap = None

        # ---- the collect -> cluster -> balance funnel -------------------------- #
        # Each stage also gets a little dot-cluster beneath the number (dot
        # COUNT actually shrinks stage to stage) so the "funnel" reads as a
        # real filtering process, not three bare numbers floating in space.
        def dot_cluster(n, color, radius=0.55, seed=0):
            rng = np.random.default_rng(seed)
            pts = []
            while len(pts) < n:
                x, y = rng.uniform(-1, 1, 2)
                if x * x + y * y <= 1.0:
                    pts.append((x * radius, y * radius, 0))
            return VGroup(*[Dot(np.array(p), radius=0.028, color=color, fill_opacity=0.85)
                           for p in pts])

        def stage_block(number, label, color, fs, ndots, seed):
            num = txt(number, fs=fs, color=color, weight="BOLD")
            dots = dot_cluster(ndots, color, seed=seed)
            lab = txt(label, fs=15, color=MUTED)
            return VGroup(num, dots, lab).arrange(DOWN, buff=0.22)

        s1 = stage_block("200,000+", "Collected", MUTED, 38, 55, seed=1)
        s2 = stage_block("6,000", "Clustered & sampled", TEXT_C, 34, 26, seed=2)
        s3 = stage_block("981", "Balanced", TITLE_C, 32, 10, seed=3)
        funnel_row = VGroup(s1, s2, s3).arrange(RIGHT, buff=1.5)
        funnel_row.move_to([0, 0.3, 0])
        a1 = arr(s1.get_right(), s2.get_left(), color=MUTED, sw=4, tip=0.2)
        a2 = arr(s2.get_right(), s3.get_left(), color=MUTED, sw=4, tip=0.2)
        funnel_group = VGroup(s1, a1, s2, a2, s3)

        self.play(FadeIn(s1, shift=UP * 0.2), run_time=0.7)
        self.say("The team began by collecting more than 200,000 PDF "
                  "documents from Common Crawl, Google, Baidu and internal "
                  "sources.", color=MUTED)
        self.beat(2.0)

        self.play(GrowArrow(a1), run_time=0.5)
        self.play(FadeIn(s2, shift=UP * 0.2), run_time=0.7)
        self.say("Each page's visual features were extracted with ResNet-50 "
                  "and clustered with Faiss, sampling 6,000 visually diverse "
                  "pages from 10 cluster centers.", color=TEXT_C)
        self.beat(2.2)

        self.play(GrowArrow(a2), run_time=0.5)
        self.play(FadeIn(s3, shift=UP * 0.2), run_time=0.7)
        self.say("Annotators added page-level attributes such as page type, "
                  "layout type and language, then manually balanced the set "
                  "down to the final 981 pages.", color=TITLE_C)
        self.beat(2.2)
        self.play(FadeOut(self._cap), run_time=0.4)
        self._cap = None

        self.play(FadeOut(funnel_group), run_time=0.6)

        # ---- the 3x3 grid of the nine real document types ----------------------- #
        self.say("Those 981 pages span nine real-world document types.",
                  color=INK)
        self.beat(1.5)
        self.play(FadeOut(self._cap), run_time=0.4)
        self._cap = None

        cards = [doc_type_card(name, kind, color=INK) for name, kind in DOC_TYPES]
        rows = [VGroup(*cards[r * 3:(r + 1) * 3]).arrange(RIGHT, buff=0.85)
                for r in range(3)]
        grid = VGroup(*rows).arrange(DOWN, buff=0.5)
        grid.move_to([0, -0.15, 0])
        if grid.width > 13.0:
            grid.scale(13.0 / grid.width)
        if grid.height > 5.6:
            grid.scale(5.6 / grid.height)

        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2, scale=0.85) for c in cards],
                               lag_ratio=0.1), run_time=2.4)
        self.beat(1.6)

        self.say("981 pages. 9 real document types. One benchmark.",
                  color=TITLE_C)
        self.beat(1.8)
        self.settle()
        self.wipe()

    def scene_annotation(self):
        self._cap = None
        header = self.section_header("How rich is one page's label?", TEXT_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)
        self.say("OmniDocBench labels four kinds of layout information on every page.",
                 color=INK)
        self.beat(1.6)
        self.play(FadeOut(header), run_time=0.5)

        page_grp, regions = _annot_page(w=3.3, h=4.7)
        page_grp.move_to([-3.5, -0.35, 0])
        self.play(FadeIn(page_grp, shift=UP * 0.1), run_time=0.8)

        # ---- (1) Layout Bounding Boxes ---- #
        box_title = SurroundingRectangle(regions["title"], color=TITLE_C, buff=0.09,
                                         corner_radius=0.04, stroke_width=2.6)
        box_para = SurroundingRectangle(regions["para"], color=TEXT_C, buff=0.1,
                                        corner_radius=0.04, stroke_width=2.6)
        box_figure = SurroundingRectangle(regions["figure"], color=FIG_C, buff=0.08,
                                          corner_radius=0.04, stroke_width=2.6)
        box_table = SurroundingRectangle(regions["table"], color=TABLE_C, buff=0.08,
                                         corner_radius=0.04, stroke_width=2.6)

        legend_items = [("Title", TITLE_C), ("Paragraph", TEXT_C),
                        ("Figure", FIG_C), ("Table", TABLE_C)]
        legend = VGroup()
        for name, col in legend_items:
            sw = Square(0.22, stroke_width=0, fill_color=col, fill_opacity=0.85)
            lab = txt(name, fs=18, color=INK)
            legend.add(VGroup(sw, lab).arrange(RIGHT, buff=0.18))
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.24)
        legend.move_to([3.9, 1.3, 0])
        ltitle = txt("19 region categories", fs=17, color=MUTED, weight="BOLD")
        ltitle.next_to(legend, UP, buff=0.28).align_to(legend, LEFT)

        self.play(LaggedStart(Create(box_title), Create(box_para), Create(box_figure),
                              Create(box_table), lag_ratio=0.2),
                  FadeIn(ltitle),
                  LaggedStart(*[FadeIn(it, shift=RIGHT * 0.12) for it in legend],
                              lag_ratio=0.15), run_time=1.3)
        self.say("Layout Bounding Boxes cover 19 distinct region categories: "
                 "titles, text paragraphs, tables, figures, isolated equations, "
                 "headers, footers, and more.", color=INK)
        self.beat(2.0)

        # ---- (2) Layout Attributes ---- #
        text_attrs = VGroup(*[chip(t, TEXT_C, fs=14, w=1.5, h=0.4, fill=0.16)
                              for t in ["EN", "White bg", "Normal rotate"]])
        text_attrs.arrange(DOWN, buff=0.12).next_to(box_para, RIGHT, buff=0.35)
        table_attrs = VGroup(*[chip(t, TABLE_C, fs=14, w=1.6, h=0.4, fill=0.16)
                              for t in ["Merge Cell", "Full Frame"]])
        table_attrs.arrange(DOWN, buff=0.12).next_to(box_table, RIGHT, buff=0.35)

        self.play(LaggedStart(*[FadeIn(c, shift=LEFT * 0.1) for c in text_attrs],
                              lag_ratio=0.15),
                  LaggedStart(*[FadeIn(c, shift=LEFT * 0.1) for c in table_attrs],
                              lag_ratio=0.15), run_time=1.0)
        self.say("Layout Attributes tag each box too: language, background and "
                 "rotation for text, or language, frame type and merged cells "
                 "for tables.", color=INK)
        self.beat(2.0)
        self.play(FadeOut(text_attrs), FadeOut(table_attrs), run_time=0.5)

        # ---- (3) Reading Order ---- #
        order = ["title", "para", "figure", "table"]
        centers = [regions[n].get_center() for n in order]
        path = VGroup()
        badges = VGroup()
        self.say("Reading Order numbers every box in the order a person would "
                 "actually read the page, not just top-to-bottom.", color=MUTED)
        for i, c in enumerate(centers):
            if i > 0:
                seg = Line(centers[i - 1], c, stroke_color=MUTED, stroke_width=3)
                seg.set_opacity(0.85)
                self.play(Create(seg), run_time=0.3)
                path.add(seg)
            badge = _num_badge(i + 1, c, color=ACCENT)
            self.play(FadeIn(badge, scale=0.5), run_time=0.25)
            badges.add(badge)
        self.beat(1.6)
        self.play(FadeOut(path), FadeOut(badges), run_time=0.4)

        # ---- (4) Affiliation ---- #
        cap_box = SurroundingRectangle(regions["caption"], color=CAP_C, buff=0.06,
                                       corner_radius=0.03, stroke_width=2.2)
        link = arr(cap_box.get_top(), box_table.get_bottom(), color=CAP_C,
                  sw=2.6, buff=0.02, tip=0.1)
        self.play(Create(cap_box), Create(link), run_time=0.5)
        self.say("Affiliation links every caption back to the table, figure, "
                 "or formula it belongs to.", color=CAP_C)
        self.beat(1.8)

        self.play(FadeOut(page_grp), FadeOut(box_title), FadeOut(box_para),
                  FadeOut(box_figure), FadeOut(box_table), FadeOut(legend),
                  FadeOut(ltitle), FadeOut(cap_box), FadeOut(link),
                  FadeOut(self._cap), run_time=0.8)
        self._cap = None

        # ---- content recognition ---- #
        c_text = chip("Text\nplain Unicode text", TEXT_C, fs=16, w=2.9, h=0.85)
        c_formula = chip("Formula\nLaTeX: inline, display,\nand subscripts",
                         FIG_C, fs=15, w=3.3, h=1.05)
        c_table = chip("Table\nHTML and LaTeX both",
                       TABLE_C, fs=16, w=3.0, h=0.85)
        content_row = VGroup(c_text, c_formula, c_table).arrange(RIGHT, buff=0.5)
        content_row.move_to([0, 0.6, 0])
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in content_row],
                              lag_ratio=0.2), run_time=1.0)
        self.say("Every region's content is captured too: plain text, LaTeX "
                 "formulas, and tables provided in both HTML and LaTeX.",
                 color=INK)
        self.beat(2.0)
        self.play(FadeOut(content_row), FadeOut(self._cap), run_time=0.5)
        self._cap = None

        # ---- scale ---- #
        big_num = txt("100,000+", fs=52, color=TITLE_C, weight="BOLD")
        big_lab = txt("total annotations", fs=22, color=MUTED)
        big = VGroup(big_num, big_lab).arrange(DOWN, buff=0.14).move_to([0, 1.4, 0])
        self.play(FadeIn(big, shift=UP * 0.1), run_time=0.7)
        self.say("Across 981 pages and 9 document types, that adds up to over "
                 "100,000 total annotations.", color=INK)
        self.beat(2.0)

        def stat_card(num, color, label, sub=None):
            parts = [txt(num, fs=30, color=color, weight="BOLD"),
                    txt(label, fs=14, color=INK)]
            if sub:
                parts.append(txt(sub, fs=12, color=MUTED))
            return VGroup(*parts).arrange(DOWN, buff=0.1)

        card1 = stat_card("20,000+", TEXT_C, "block-level, 15 categories",
                         "15,979 paragraphs · 989 images · 428 tables")
        card2 = stat_card("16,000+", ACCENT, "reading-order annotations")
        card3 = stat_card("70,000+", FIG_C, "span-level annotations",
                         "incl. 4,009 inline formulas")
        cards = VGroup(card1, card2, card3).arrange(RIGHT, buff=0.7).move_to([0, -1.3, 0])
        if cards.width > 13.0:
            cards.scale(13.0 / cards.width)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in cards],
                              lag_ratio=0.2), run_time=1.0)
        self.say("That includes more than 20,000 block-level annotations across "
                 "15 categories, over 16,000 reading-order annotations, and "
                 "more than 70,000 span-level annotations.", color=INK)
        self.beat(2.4)
        self.play(FadeOut(big), FadeOut(cards), FadeOut(self._cap), run_time=0.6)
        self._cap = None

        # ---- 3-stage annotation pipeline ---- #
        header2 = self.section_header("How the labels were actually built", TITLE_C)
        self.play(FadeIn(header2, shift=DOWN * 0.2), run_time=0.6)

        s1 = chip("Intelligent\nAnnotate", MUTED, fs=18, w=2.7, h=0.9, weight="BOLD")
        s2 = chip("Annotator\nCorrect", TEXT_C, fs=18, w=2.7, h=0.9, weight="BOLD")
        s3 = chip("Expert Quality\nInspection", TITLE_C, fs=17, w=2.9, h=0.9, weight="BOLD")
        VGroup(s1, s2, s3).arrange(RIGHT, buff=1.3).move_to([0, 0.4, 0])
        a1 = arr(s1.get_right(), s2.get_left(), color=MUTED)
        a2 = arr(s2.get_right(), s3.get_left(), color=MUTED)
        badge1 = _num_badge(1, s1.get_top() + UP * 0.32, color=MUTED, r=0.19)
        badge2 = _num_badge(2, s2.get_top() + UP * 0.32, color=TEXT_C, r=0.19)
        badge3 = _num_badge(3, s3.get_top() + UP * 0.32, color=TITLE_C, r=0.19)

        self.play(FadeIn(s1), FadeIn(badge1, scale=0.5), run_time=0.4)
        self.play(Indicate(s1, color=MUTED, scale_factor=1.08), run_time=0.4)
        self.say("Stage 1, Intelligent Annotate: fine-tuned models pre-label "
                 "everything automatically. LayoutLMv3 handles layout; "
                 "PaddleOCR, UniMERNet and GPT-4o handle text, formula and "
                 "table content.", color=MUTED)
        self.beat(2.3)

        self.play(Create(a1), FadeIn(s2), FadeIn(badge2, scale=0.5), run_time=0.5)
        self.play(Indicate(s2, color=TEXT_C, scale_factor=1.08), run_time=0.4)
        self.say("Stage 2, Annotator Correct: human annotators verify and fix "
                 "every box and character, using Tables Generator and "
                 "latexlive to check the hardest tables and formulas.",
                 color=TEXT_C)
        self.beat(2.3)

        self.play(Create(a2), FadeIn(s3), FadeIn(badge3, scale=0.5), run_time=0.5)
        self.play(Indicate(s3, color=TITLE_C, scale_factor=1.08), run_time=0.4)
        self.say("Stage 3, Expert Quality Inspection: PhD-level reviewers do a "
                 "final pass, using CDM's rendering check to catch LaTeX that "
                 "doesn't actually render.", color=TITLE_C)
        self.beat(2.3)

        self.play(FadeOut(header2),
                  FadeOut(VGroup(s1, s2, s3, a1, a2, badge1, badge2, badge3)),
                  FadeOut(self._cap), run_time=0.6)
        self._cap = None

        closing = txt("Over 100,000 annotations. Every one checked by a human, "
                      "then reviewed by a PhD.", fs=26, color=TITLE_C, weight="BOLD")
        if closing.width > 12.6:
            closing.scale(12.6 / closing.width)
        closing.move_to([0, 0, 0])
        self.play(FadeIn(closing, shift=UP * 0.15), run_time=0.7)
        self.beat(1.6)
        self.settle()
        self.wipe()

    def scene_evaluation(self):
        self._cap = None
        header = self.section_header("Scoring wildly different outputs, fairly", ACCENT)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)
        self.say("Models output totally different formats: Markdown, LaTeX "
                 "tables, HTML tables, plain text. You can't just string-diff "
                 "the raw output against the ground truth.", color=INK)
        self.beat(2.0)
        self.play(FadeOut(header), run_time=0.4)

        # ---- the five-stage pipeline row (positions fixed once up front) ---- #
        c_pred = chip("Model\nPrediction", MUTED, fs=17, w=2.0, h=0.85, weight="BOLD")
        c_extract = chip("Extract", TEXT_C, fs=18, w=1.8, h=0.85, weight="BOLD")
        c_match = chip("Match", FIG_C, fs=18, w=1.8, h=0.85, weight="BOLD")
        c_metric = chip("Metric", TABLE_C, fs=18, w=1.8, h=0.85, weight="BOLD")
        c_overall = chip("Overall", TITLE_C, fs=18, w=2.0, h=0.85, weight="BOLD")
        _layout_row = VGroup(c_pred, c_extract, c_match, c_metric, c_overall)
        _layout_row.arrange(RIGHT, buff=0.75)
        if _layout_row.width > 12.8:
            _layout_row.scale(12.8 / _layout_row.width)
        _layout_row.move_to([0, 2.5, 0])

        self.play(FadeIn(c_pred), run_time=0.5)
        self.say("It starts from the model's raw Markdown output, after light "
                 "preprocessing: images stripped, markdown tags removed, "
                 "repeated characters normalized.", color=MUTED)
        self.beat(2.2)

        a1 = arr(c_pred.get_right(), c_extract.get_left(), color=MUTED)
        self.play(Create(a1), FadeIn(c_extract), run_time=0.5)
        self.say("Extract pulls elements out in a fixed order so they don't "
                 "interfere: LaTeX tables, HTML tables, formulas, Markdown "
                 "tables converted to HTML, then code blocks. Whatever is "
                 "left over is pure text.", color=TEXT_C)
        self.beat(2.3)

        a2 = arr(c_extract.get_right(), c_match.get_left(), color=MUTED)
        self.play(Create(a2), FadeIn(c_match), run_time=0.6)
        self.say('Match is the clever part: an "Adjacency Search Match."', color=FIG_C)
        self.beat(1.4)

        # ---- Match mini-visual: a naive pairing fails, so paragraphs merge ---- #
        dim_targets = VGroup(c_pred, c_extract, c_match, a1, a2)
        self.play(dim_targets.animate.set_opacity(0.35), run_time=0.5)

        gt_label = txt("Ground Truth", fs=15, color=MUTED)
        gt_box = chip("GT", TABLE_C, fs=16, w=1.3, h=0.5, fill=0.12)
        gt_group = VGroup(gt_label, gt_box).arrange(DOWN, buff=0.14).move_to([0, 0.7, 0])

        pred_label = txt("Prediction", fs=15, color=MUTED)
        pred1 = chip("Pred 1", TEXT_C, fs=15, w=1.4, h=0.5, fill=0.12)
        pred2 = chip("Pred 2", TEXT_C, fs=15, w=1.4, h=0.5, fill=0.12)
        pred_row = VGroup(pred1, pred2).arrange(RIGHT, buff=0.3)
        # label goes BELOW the row (not above) so the GT-to-Pred connector
        # lines (which land on pred_row's top edge) never cross the label text
        pred_group = VGroup(pred_row, pred_label).arrange(DOWN, buff=0.14).move_to([0, -0.55, 0])

        self.play(FadeIn(gt_group), FadeIn(pred_group), run_time=0.7)
        self.say("First, it computes the Normalized Edit Distance between every "
                 "ground-truth and prediction paragraph pair; close matches "
                 "are accepted immediately.", color=FIG_C)
        self.beat(2.0)

        naive_line = Line(gt_box.get_bottom(), pred1.get_top(), stroke_color=BAD,
                          stroke_width=2.6)
        naive_x = make_cross(BAD, sw=5, scale=0.55).move_to(naive_line.get_center())
        self.play(Create(naive_line), FadeIn(naive_x), run_time=0.6)
        self.beat(0.9)
        self.play(FadeOut(naive_line), FadeOut(naive_x), run_time=0.4)

        merge_box = SurroundingRectangle(pred_row, color=FIG_C, buff=0.12,
                                         corner_radius=0.06, stroke_width=2.4)
        self.play(Create(merge_box), run_time=0.5)
        good_line = Line(gt_box.get_bottom(), merge_box.get_top(), stroke_color=GOOD,
                         stroke_width=2.8)
        good_tick = make_tick(GOOD, sw=5, scale=0.65).move_to(good_line.get_center())
        self.play(Create(good_line), FadeIn(good_tick), run_time=0.6)
        self.say("For the rest, it iteratively merges adjacent paragraphs, in "
                 "both ground truth and prediction, until the edit distance "
                 "stops improving, exactly what's needed when a model splits "
                 "one paragraph into two.", color=INK)
        self.beat(2.4)

        self.play(FadeOut(gt_group), FadeOut(pred_group), FadeOut(merge_box),
                  FadeOut(good_line), FadeOut(good_tick), run_time=0.6)
        self.play(dim_targets.animate.set_opacity(1.0), run_time=0.4)

        # ---- Metric: each element type, its own dedicated score ---- #
        a3 = arr(c_match.get_right(), c_metric.get_left(), color=MUTED)
        self.play(Create(a3), FadeIn(c_metric), run_time=0.6)
        self.say("Each matched element type gets scored with its own dedicated "
                 "metric, because a generic text-similarity score can't fairly "
                 "judge structured content.", color=TABLE_C)
        self.beat(2.1)

        b_text = chip("Text\nEdit Distance ↓", TEXT_C, fs=14, w=2.1, h=0.85)
        b_table = chip("Table\nTEDS ↑ + Edit Dist.", TABLE_C, fs=13, w=2.3, h=0.85)
        b_formula = chip("Formula\nCDM ↑, Edit Dist., BLEU", FIG_C, fs=12, w=2.7, h=0.85)
        b_order = chip("Reading Order\nEdit Distance ↓", MUTED, fs=13, w=2.4, h=0.85)
        badges = VGroup(b_text, b_table, b_formula, b_order).arrange(RIGHT, buff=0.35)
        if badges.width > 12.8:
            badges.scale(12.8 / badges.width)
        badges.move_to([0, -1.1, 0])
        fan = VGroup(*[Line(c_metric.get_bottom(), b.get_top(), stroke_color=MUTED,
                            stroke_width=2.0).set_opacity(0.7) for b in badges])
        self.play(LaggedStart(*[Create(f) for f in fan], lag_ratio=0.12),
                  LaggedStart(*[FadeIn(b, scale=0.85) for b in badges], lag_ratio=0.12),
                  run_time=1.2)
        self.say("Text uses Edit Distance. Tables convert to HTML and get TEDS "
                 "plus Edit Distance. Formulas get CDM, a rendering-based "
                 "check, plus Edit Distance and BLEU. Reading Order is Edit "
                 "Distance over the sequence of block IDs.", color=INK)
        self.beat(2.5)
        self.say("Headers, footers, page numbers and footnotes are excluded "
                 "from scoring entirely, since different models handle them "
                 "inconsistently.", color=MUTED)
        self.beat(2.0)
        self.play(FadeOut(fan), FadeOut(badges), run_time=0.4)

        # ---- Overall ---- #
        a4 = arr(c_metric.get_right(), c_overall.get_left(), color=MUTED)
        self.play(Create(a4), FadeIn(c_overall), run_time=0.5)
        self.say("All of it rolls up into one Overall score, a fair yardstick "
                 "no matter what format the model actually speaks.", color=TITLE_C)
        self.beat(2.0)

        self.play(FadeOut(VGroup(c_pred, c_extract, c_match, c_metric, c_overall,
                                 a1, a2, a3, a4)), FadeOut(self._cap), run_time=0.6)
        self._cap = None

        punch = txt("One fair yardstick, whether the model speaks Markdown, "
                    "LaTeX, or HTML.", fs=26, color=TITLE_C, weight="BOLD")
        if punch.width > 12.6:
            punch.scale(12.6 / punch.width)
        punch.move_to([0, 0, 0])
        self.play(FadeIn(punch, shift=UP * 0.15), run_time=0.7)
        self.beat(1.6)
        self.settle()
        self.wipe()

    def scene_contenders(self):
        header = self.section_header("Contenders: three classes of systems", ACCENT)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)
        self.say("Now that the benchmark exists, who actually gets tested on it?", color=INK)
        self.beat(1.4)

        pipe = _contender_card(
            "Pipeline Tools", PIPE_C,
            ["Chains layout detection, OCR, table and", "formula recognition into one pipeline."],
            ["MinerU (v0.9.3)", "Marker (v1.2.3)", "Mathpix"])
        expert = _contender_card(
            "Expert VLMs", EXPERT_C,
            ["Large multimodal models trained", "specifically for document parsing."],
            ["GOT-OCR2.0", "Nougat"])
        general = _contender_card(
            "General VLMs", GENERAL_C,
            ["General-purpose multimodal models that", "parse documents with no special training."],
            ["GPT-4o", "Qwen2-VL-72B", "InternVL2-76B"])

        cards = VGroup(pipe, expert, general).arrange(RIGHT, buff=0.35)
        cards.move_to([0, 0.55, 0])

        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.25) for c in cards], lag_ratio=0.4),
                  run_time=2.0)
        self.beat(0.8)

        self.play(Indicate(pipe, color=PIPE_C, scale_factor=1.04), run_time=0.7)
        self.say("Pipeline tools integrate layout detection with OCR, table and "
                 "formula recognition: MinerU, Marker, Mathpix.", color=PIPE_C)
        self.beat(1.3)

        self.play(Indicate(expert, color=EXPERT_C, scale_factor=1.04), run_time=0.7)
        self.say("Expert VLMs are trained specifically for document parsing: "
                 "GOT-OCR2.0 and Nougat.", color=EXPERT_C)
        self.beat(1.3)

        self.play(Indicate(general, color=GENERAL_C, scale_factor=1.04), run_time=0.7)
        self.say("General VLMs need no special fine-tuning at all: GPT-4o, "
                 "Qwen2-VL-72B, InternVL2-76B.", color=GENERAL_C)
        self.beat(1.4)

        legend = self.legend_row(fs=16).next_to(cards, DOWN, buff=0.4)
        self.play(FadeIn(legend), run_time=0.6)
        self.beat(0.9)

        self.say("Eight systems. Three philosophies. One test.", color=ACCENT, fs=25)
        self.beat(1.8)
        self.settle()
        self.wipe()
    # ====================================================================== #
    # Scene 6 -- Results I: Table 2, verbatim, panned with a moving camera
    # ====================================================================== #
    def legend_row(self, fs=17):
        items = [("Pipeline Tools", PIPE_C), ("Expert VLMs", EXPERT_C),
                 ("General VLMs", GENERAL_C)]
        row = VGroup()
        for name, col in items:
            sw = RoundedRectangle(width=0.26, height=0.26, corner_radius=0.05,
                                  stroke_width=0, fill_color=col, fill_opacity=0.9)
            lab = txt(name, fs=fs, color=INK)
            row.add(VGroup(sw, lab).arrange(RIGHT, buff=0.16))
        row.arrange(RIGHT, buff=0.55)
        return row

    def frame_cap(self, s, color=INK, fs=22, y=None):
        """A caption positioned relative to the CURRENT camera frame (not the
        default scene bounds) -- safe to call after ``self.camera.frame`` has
        been panned/zoomed, where plain ``to_edge``/``to_corner`` would place
        text outside the visible window. ``y`` pins it to an explicit
        world-space height (e.g. a fixed gap below a table) so it never
        collides with content whose own bottom edge sits at a different
        height than "near the frame's bottom edge"; if omitted, falls back to
        a frame-relative bottom margin."""
        f = self.camera.frame
        t = Text(s, font_size=fs, color=color)
        avail_w = f.width * 0.92
        if t.width > avail_w:
            t.scale(avail_w / t.width)
        cy = y if y is not None else (f.get_center()[1] - f.height / 2 + f.height * 0.12)
        t.move_to([f.get_center()[0], cy, 0])
        return t

    def frame_say(self, s, color=INK, fs=22, rt=0.5, y=None):
        """Like ``self.say`` but frame-relative (see ``frame_cap``). Always
        call this only once the camera has *finished* moving (sequential
        ``self.play`` calls), never concurrently with a camera animation."""
        if self._cap is not None:
            self.play(FadeOut(self._cap), run_time=rt * 0.6)
        new = self.frame_cap(s, color, fs, y=y)
        self.play(FadeIn(new, shift=UP * 0.1), run_time=rt)
        self._cap = new
        return self._cap

    # ====================================================================== #
    # Scene -- OCR: what "reading a page" actually looks like under the hood
    # ====================================================================== #
    def scene_ocr(self):
        self._cap = None
        header = self.section_header("Reading pixels: what OCR actually does", OCR_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)
        self.say("Every system in this benchmark, pipeline or VLM, starts from "
                 "the same raw material: pixels, not characters.", color=INK)
        self.beat(1.6)
        self.play(FadeOut(self._cap), run_time=0.4)
        self._cap = None

        # ---- left: a scanned page with noisy, "trapped" pixel text ---------- #
        pw, ph = 3.6, 4.4
        page = Rectangle(width=pw, height=ph, fill_color=PAPER, fill_opacity=1.0,
                         stroke_color=PAPER_EDGE, stroke_width=1.8)
        title_bar = Line(ORIGIN, [pw * 0.55, 0, 0], stroke_color=PAPER_INK,
                         stroke_width=5).set_opacity(0.85)
        title_bar.move_to([page.get_left()[0] + 0.28 + title_bar.width / 2,
                           page.get_top()[1] - 0.32, 0])

        rng = np.random.default_rng(4)
        n_lines = 9
        ys = np.linspace(title_bar.get_bottom()[1] - 0.32,
                         page.get_bottom()[1] + 0.4, n_lines)
        noisy_lines = VGroup()
        for y in ys:
            frac = rng.uniform(0.55, 0.85)
            ln = VGroup(*[Line(ORIGIN, [0.05, 0, 0], stroke_color=PAPER_INK,
                               stroke_width=3.4).set_opacity(rng.uniform(0.35, 0.75))
                         for _ in range(int(pw * frac / 0.09))])
            ln.arrange(RIGHT, buff=0.03)
            ln.move_to([page.get_left()[0] + 0.28 + ln.width / 2, y, 0])
            noisy_lines.add(ln)
        scan_tag = txt("scanned page, no text layer", fs=15, color=MUTED)

        page_grp = VGroup(page, title_bar, noisy_lines).move_to([-4.05, 0.1, 0])
        scan_tag.next_to(page_grp, DOWN, buff=0.22)
        self.play(FadeIn(page_grp, shift=UP * 0.1), FadeIn(scan_tag), run_time=0.9)
        self.beat(1.0)

        # ---- right: the recognized-text output panel ------------------------- #
        panel = RoundedRectangle(width=pw, height=ph, corner_radius=0.1,
                                 stroke_color=OCR_C, stroke_width=2,
                                 fill_color="#0A0E15", fill_opacity=1.0)
        panel.move_to([1.9, 0.1, 0])
        panel_lbl = txt("recognized text", fs=15, color=OCR_C)
        panel_lbl.move_to([panel.get_left()[0] + panel_lbl.width / 2 + 0.22,
                           panel.get_top()[1] - 0.28, 0])
        self.play(FadeIn(panel), FadeIn(panel_lbl), run_time=0.6)

        engines = VGroup(*[chip(e, OCR_C, fs=14, w=1.7, h=0.46, fill=0.1)
                           for e in ["PaddleOCR", "GOT-OCR", "a VLM's own reader"]])
        engines.arrange(RIGHT, buff=0.28).next_to(header, DOWN, buff=0.35).align_to(header, LEFT)
        engines.shift(RIGHT * 2.6)
        self.play(LaggedStart(*[FadeIn(e, shift=DOWN * 0.1) for e in engines],
                              lag_ratio=0.15), run_time=0.7)
        self.say("A classic OCR engine, or a vision-language model's own visual "
                 "reader, both have to solve this same problem.", color=OCR_C)
        self.beat(1.6)
        self.play(FadeOut(self._cap), run_time=0.4)
        self._cap = None

        # ---- the scanning beam sweeps down; text resolves line by line ------- #
        recognized_full = ["Financial Report Q3", "Revenue grew 12% year", "over year, driven",
                           "by strong demand in", "EMEA and APAC markets.", "Operating margin",
                           "held steady at 34%,", "in line with prior", "guidance."]
        beam = Rectangle(width=pw, height=0.14, stroke_width=0,
                         fill_color=OCR_C, fill_opacity=0.95)
        glow = Rectangle(width=pw, height=0.5, stroke_width=0,
                         fill_color=OCR_C, fill_opacity=0.18)
        beam.move_to([page.get_center()[0], noisy_lines[0].get_center()[1], 0])
        glow.move_to(beam)
        self.add(glow, beam)
        out_lines = VGroup()
        for i, src in enumerate(noisy_lines):
            self.play(beam.animate.move_to([page.get_center()[0], src.get_center()[1], 0]),
                     glow.animate.move_to([page.get_center()[0], src.get_center()[1], 0]),
                     run_time=0.22)
            crisp = txt(recognized_full[i], fs=17, color=INK,
                       weight="BOLD" if i == 0 else "NORMAL")
            if crisp.width > pw - 0.3:
                crisp.scale((pw - 0.3) / crisp.width)
            crisp.move_to([panel.get_left()[0] + 0.24 + crisp.width / 2,
                          panel_lbl.get_bottom()[1] - 0.34 - i * 0.4, 0])
            self.play(Indicate(src, color=OCR_C, scale_factor=1.06),
                     TransformFromCopy(src, crisp), run_time=0.32)
            out_lines.add(crisp)
        self.play(FadeOut(beam), FadeOut(glow), run_time=0.3)
        self.beat(0.8)

        # ---- the twist: a single character mismatch is exactly what Edit
        # Distance is built to catch --------------------------------------- #
        self.say("But recognition is never perfect. Look closely at one word.",
                 color=BAD)
        self.beat(1.4)
        target = out_lines[3]  # "by strong demand in"
        box = SurroundingRectangle(target, color=BAD, buff=0.06, corner_radius=0.03,
                                   stroke_width=2.6)
        self.play(Create(box), run_time=0.5)
        wrong = txt("by strong demand ln", fs=17, color=BAD)
        if wrong.width > pw - 0.3:
            wrong.scale((pw - 0.3) / wrong.width)
        wrong.move_to(target)
        self.play(Transform(target, wrong), run_time=0.5)
        # scan_tag sat right under the page mockup; fade it out first so the
        # ground-truth/recognized comparison below never collides with it.
        self.play(FadeOut(scan_tag), run_time=0.3)
        gt_row = txt("ground truth:  \"...demand in EMEA...\"", fs=16, color=GOOD)
        pred_row = txt("recognized:    \"...demand ln EMEA...\"", fs=16, color=BAD)
        cmp_rows = VGroup(gt_row, pred_row).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
        cmp_rows.move_to([-1.1, -2.75, 0])
        self.play(FadeIn(cmp_rows, shift=UP * 0.1), run_time=0.6)
        self.say('One swapped character: "in" misread as "ln." A human skims '
                 "past it. A naive string match wouldn't.", color=BAD)
        self.beat(2.0)
        self.play(FadeOut(box), run_time=0.3)

        self.play(FadeOut(VGroup(page_grp, scan_tag, panel, panel_lbl, out_lines,
                                 engines, cmp_rows)), FadeOut(self._cap), run_time=0.7)
        self._cap = None
        punch = txt("That single-character gap is exactly what Edit Distance "
                    "is built to measure, fairly, at scale.", fs=25, color=OCR_C,
                    weight="BOLD")
        if punch.width > 12.4:
            punch.scale(12.4 / punch.width)
        punch.move_to(ORIGIN)
        self.play(FadeIn(punch, shift=UP * 0.15), run_time=0.7)
        self.beat(1.8)
        self.settle()
        self.wipe()

    def scene_results1(self):
        self._cap = None
        frame = self.camera.frame
        frame.save_state()
        header = self.section_header("Results I: the comprehensive scoreboard", ACCENT)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)
        self.say("Eight parsing systems, scored on OmniDocBench's ground truth. "
                 "This is the paper's own table, verbatim.", color=INK)
        self.beat(1.6)
        self.play(FadeOut(header), FadeOut(self._cap), run_time=0.6)
        self._cap = None

        t2 = image_card("table2_shot.jpg", height=3.35)
        t2.move_to([0, 0.55, 0])
        cred2 = credit(t2, "Table 2 of the paper, arXiv:2412.07626")
        self.play(FadeIn(t2, shift=UP * 0.15), FadeIn(cred2), run_time=1.1)
        self.beat(1.0)

        # every highlight below is a uv_rect over the REAL screenshot -- no
        # rebuilt cells, just boxes drawn at the image's own pixel fractions
        # (verified against the source PDF's own text-box coordinates).
        text_box = uv_rect(t2, 0.288, 0.0, 0.392, 0.76, color=TEXT_C)
        self.play(Create(text_box), run_time=0.6)
        self.frame_say("Text Edit: character-level Normalized Edit Distance. Lower is better.",
                       color=TEXT_C, fs=20, y=t2.get_bottom()[1] - 0.75)
        self.beat(1.5)
        self.play(FadeOut(text_box), run_time=0.3)

        formula_box = uv_rect(t2, 0.392, 0.0, 0.565, 0.76, color=FIG_C)
        self.play(Create(formula_box), run_time=0.6)
        self.frame_say("Formulas get two scores: Edit Distance, and CDM, character-level "
                       "matching, since LaTeX has many equally valid spellings.",
                       color=FIG_C, fs=20, y=t2.get_bottom()[1] - 0.75)
        self.beat(1.7)
        self.play(FadeOut(formula_box), run_time=0.3)

        table_box = uv_rect(t2, 0.565, 0.0, 0.735, 0.76, color=TABLE_C)
        self.play(Create(table_box), run_time=0.6)
        self.frame_say("Tables use TEDS: tree-edit-distance similarity between predicted "
                       "and true HTML. Higher is better.", color=TABLE_C, fs=20,
                       y=t2.get_bottom()[1] - 0.75)
        self.beat(1.6)
        self.play(FadeOut(table_box), run_time=0.3)

        overall_box = uv_rect(t2, 0.822, 0.0, 0.912, 0.76, color=ACCENT)
        self.play(Create(overall_box), run_time=0.6)
        self.frame_say("Everything rolls up into one Overall Edit score per language.",
                       color=ACCENT, fs=20, y=t2.get_bottom()[1] - 0.75)
        self.beat(1.3)
        self.play(FadeOut(overall_box), run_time=0.3)
        self.play(FadeOut(self._cap), run_time=0.4)
        self._cap = None

        self.frame_say("Pipeline tools lead most sub-tasks, but the general VLMs "
                       "are closing in.", color=INK, y=t2.get_bottom()[1] - 0.75)
        self.beat(1.4)

        # climax: zoom the camera into the Overall column, compare best-EN vs best-ZH
        en_box = uv_rect(t2, 0.833, 0.196, 0.869, 0.259, color=TITLE_C, sw=3.5)
        zh_box = uv_rect(t2, 0.876, 0.637, 0.912, 0.70, color=TITLE_C, sw=3.5)
        zoom_c = uv_point(t2, 0.872, 0.45)
        self.play(FadeOut(self._cap),
                  frame.animate.move_to(zoom_c).set(width=4.6), run_time=1.5)
        self._cap = None
        self.play(Create(en_box), run_time=0.6)
        self.frame_say("MinerU posts the best English score: 0.15.", color=TITLE_C,
                       y=zoom_c[1] - 1.4)
        self.beat(1.4)
        self.play(Create(zh_box), run_time=0.6)
        self.frame_say("But the best Chinese score belongs to a general VLM: "
                       "Qwen2-VL-72B, at 0.327.", color=TITLE_C, y=zoom_c[1] - 1.4)
        self.beat(1.7)
        self.play(FadeOut(self._cap), FadeOut(en_box), FadeOut(zh_box),
                  frame.animate.restore(), run_time=1.3)
        self._cap = None
        self.say("A specialized pipeline still wins English. A general model "
                 "already wins Chinese.", color=INK)
        self.beat(1.7)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 7 -- Results II: Table 3, the "no free lunch" twist
    # ====================================================================== #
    def scene_results2(self):
        self._cap = None
        header = self.section_header("Results II: no single system wins everywhere", ACCENT)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)
        self.say("Break the same eight systems down by document type instead. "
                 "Again, verbatim from the paper.", color=INK)
        self.beat(1.5)
        self.play(FadeOut(self._cap), run_time=0.4)
        self._cap = None

        t3 = image_card("table3_shot.jpg", height=3.15)
        t3.move_to([0, 0.35, 0])
        cred3 = credit(t3, "Table 3 of the paper, arXiv:2412.07626")
        self.play(FadeIn(t3, shift=UP * 0.15), FadeIn(cred3), run_time=1.1)
        self.beat(1.0)

        # highlight MinerU's six bold wins: Book, Fin. Report, Textbook,
        # Exam Paper, Acad. Papers, Newspaper.
        miner_cols = [(0.316, 0.354), (0.409, 0.469), (0.476, 0.536),
                      (0.543, 0.60), (0.66, 0.73), (0.777, 0.846)]
        boxes_m = VGroup(*[uv_rect(t3, u0, 0.193, u1, 0.261, color=TITLE_C, sw=2.6)
                          for u0, u1 in miner_cols])
        self.say("MinerU wins six of the nine page types outright.", color=PIPE_C)
        self.play(LaggedStart(*[Create(b) for b in boxes_m], lag_ratio=0.12), run_time=1.2)
        self.beat(1.4)
        self.play(FadeOut(boxes_m), run_time=0.4)

        # Qwen2-VL-72B's four bold wins: Slides, Magazine, Notes, Overall.
        qwen_cols = [(0.361, 0.403), (0.591, 0.654), (0.73, 0.77), (0.854, 0.904)]
        boxes_q = VGroup(*[uv_rect(t3, u0, 0.677, u1, 0.745, color=TITLE_C, sw=2.6)
                          for u0, u1 in qwen_cols])
        self.say("Qwen2-VL-72B wins slides, magazines and notes. And one more thing.",
                 color=GENERAL_C)
        self.play(LaggedStart(*[Create(b) for b in boxes_q], lag_ratio=0.12), run_time=1.2)
        self.beat(1.5)
        self.play(FadeOut(boxes_q), run_time=0.4)
        self.play(FadeOut(self._cap), run_time=0.4)
        self._cap = None

        # the catastrophic-failure twist: MinerU's Notes cell vs Qwen's
        box_bad = uv_rect(t3, 0.728, 0.193, 0.772, 0.261, color=BAD, sw=3.2)
        box_good = uv_rect(t3, 0.728, 0.677, 0.772, 0.745, color=GOOD, sw=3.2)
        self.say("Look at Notes: MinerU collapses to 0.984, almost a total miss on "
                 "handwritten pages. Qwen2-VL-72B scores 0.168.", color=BAD)
        self.play(Create(box_bad), run_time=0.6)
        self.play(Indicate(box_bad, color=BAD, scale_factor=1.08), run_time=0.7)
        self.play(Create(box_good), run_time=0.6)
        self.beat(1.8)
        self.play(FadeOut(box_bad), FadeOut(box_good), FadeOut(self._cap), run_time=0.4)
        self._cap = None

        box_om = uv_rect(t3, 0.852, 0.193, 0.906, 0.261, color=MUTED, sw=2.8)
        box_oq = uv_rect(t3, 0.852, 0.677, 0.906, 0.745, color=TITLE_C, sw=3.2)
        self.play(Create(box_om), Create(box_oq), run_time=0.7)
        self.say("That one catastrophic failure drags MinerU's overall average to 0.206, "
                 "behind Qwen2-VL-72B's 0.179.", color=TITLE_C)
        self.beat(1.8)
        self.play(FadeOut(box_om), FadeOut(box_oq), FadeOut(self._cap), run_time=0.4)
        self._cap = None

        punch = txt("The system with the most wins isn't the system with the best "
                    "overall score.", fs=25, color=TITLE_C, weight="BOLD")
        if punch.width > 12.4:
            punch.scale(12.4 / punch.width)
        punch.next_to(t3, DOWN, buff=0.65)
        self.play(FadeIn(punch, shift=UP * 0.15), run_time=0.7)
        self.beat(1.9)
        self.settle()
        self.wipe()

    def scene_takeaway(self):
        # each "paragraph" is built from separate Text lines + arrange(DOWN)
        # (not one Text with embedded "\n") so every line centers relative to
        # its neighbours -- Manim's multi-line Text left-justifies wrapped
        # lines by default, which reads ragged for a centered recap card.
        def para(strs, fs, color, weight="NORMAL"):
            g = VGroup(*[txt(s, fs=fs, color=color, weight=weight) for s in strs])
            g.arrange(DOWN, buff=0.12)
            return g

        holds = [1.5, 1.6, 1.8, 2.0]
        blocks = VGroup(
            para(["Document parsing used to be graded on a",
                  "narrow test, with a blunt ruler."], 27, INK),
            para(["OmniDocBench replaced that narrow test with 981 pages",
                  "across 9 real document types, each richly annotated",
                  "and scored element by element."], 24, INK),
            para(["No single system wins everywhere. Pipeline tools like MinerU",
                  "dominate standard documents, while general VLMs like",
                  "Qwen2-VL-72B generalize further and stay far more consistent overall."],
                 23, INK),
            para(["The right question was never which system is best.",
                  "It was best at what, and where it breaks."],
                 27, TITLE_C, weight="BOLD"),
        )
        for b in blocks:
            if b.width > 12.6:
                b.scale(12.6 / b.width)
        blocks.arrange(DOWN, buff=0.5)
        blocks.move_to(ORIGIN)

        for i, b in enumerate(blocks):
            if i == len(blocks) - 1:
                self.play(Write(b), run_time=1.2)
            else:
                self.play(FadeIn(b, shift=UP * 0.15), run_time=0.7)
            self.beat(holds[i])
        self.beat(1.0)
        self.settle()
        self.wipe()

    def play_all(self):
        self.play_intro()
        self.scene_problem()
        self.scene_dataset()
        self.scene_annotation()
        self.scene_contenders()
        self.scene_ocr()
        self.scene_evaluation()
        self.scene_results1()
        self.scene_results2()
        self.scene_takeaway()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_OmniDocBenchBase):
    def construct(self):
        self.play_intro()


class Problem(_OmniDocBenchBase):
    def construct(self):
        self.scene_problem()


class Dataset(_OmniDocBenchBase):
    def construct(self):
        self.scene_dataset()


class Annotation(_OmniDocBenchBase):
    def construct(self):
        self.scene_annotation()


class Evaluation(_OmniDocBenchBase):
    def construct(self):
        self.scene_evaluation()


class Contenders(_OmniDocBenchBase):
    def construct(self):
        self.scene_contenders()


class Ocr(_OmniDocBenchBase):
    def construct(self):
        self.scene_ocr()


class Results1(_OmniDocBenchBase):
    def construct(self):
        self.scene_results1()


class Results2(_OmniDocBenchBase):
    def construct(self):
        self.scene_results2()


class Takeaway(_OmniDocBenchBase):
    def construct(self):
        self.scene_takeaway()


class Outro(_OmniDocBenchBase):
    def construct(self):
        self.play_outro()


class OmniDocBenchFilm(_OmniDocBenchBase):
    """The whole ~4-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    OmniDocBenchFilm().render()

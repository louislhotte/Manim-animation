"""Docling — how it chunks documents (PDF) and plugs in OCR. A ~4-minute explainer.

Docling (open-source, IBM Research) turns messy documents — PDFs, scans, DOCX —
into one clean, structured ``DoclingDocument``, then into RAG-ready chunks.

This film builds the idea from the ground up:

    1. The problem  -- naïve text extraction destroys structure (bag of words)
    2. The pipeline -- parse -> layout -> OCR -> tables -> assemble
    3. Layout       -- detect & type every block, recover the reading order
    4. OCR          -- a pluggable step that reads text trapped in pixels
    5. Chunking     -- Hierarchical then Hybrid (token-aware) chunks for RAG

Everything uses ``Text`` (Pango) instead of ``Tex`` so it renders with no LaTeX.
Code snippets are set in Menlo. Scenes are exposed individually (``Problem``,
``Pipeline``, ``Layout``, ``OCR``, ``Chunk``, ``Intro``, ``Outro``, ``Recap``)
and as one continuous film (``DoclingFilm``).

Env knobs:
    DL_QUICK=1   shorten every hold for a fast sanity render
    DL_DELAY=..  override the between-step motion rhythm
    DL_READ=..   override the absolute reading hold after text lands (~2.8 s)
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

# --- crisp text ------------------------------------------------------------ #
# Manim's ``Text`` mangles letter/word spacing below ~20 pt. Fix it once: render
# every glyph at a large base size and scale the mobject *down* to the requested
# size. This shadows manim's ``Text`` so every call benefits automatically.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("DL_QUICK") == "1"
# Two separate pacing knobs so nothing feels rushed:
#   DELAY scales the small pauses *between* animation steps (motion rhythm).
#   READ  is the absolute hold after a block of text lands, so there is always
#         time to actually read it.
# ANIM_SLOW stretches every played animation so transitions aren't abrupt.
DELAY = float(os.environ.get("DL_DELAY", 0.28 if QUICK else 1.0))
READ = float(os.environ.get("DL_READ", 0.35 if QUICK else 2.8))
ANIM_SLOW = 1.0 if QUICK else 1.3
END_HOLD = 0.2 if QUICK else 2.4

# ---- palette -------------------------------------------------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
FAINT = "#3A4152"       # gridlines / rails
PAPER = "#F4F1EA"       # a document page (light)
PAPER_INK = "#2A2E37"   # ink printed on the page
PAPER_EDGE = "#C9C4B6"  # page border

# block-type / semantic colours (used for layout bounding boxes)
TITLE_C = "#FFD166"     # gold   — titles / section headings
TEXT_C = "#5B8DEF"      # blue   — body text / paragraphs
TABLE_C = "#2EC4B6"     # teal   — tables
FIG_C = "#C792EA"       # violet — figures / images
CAP_C = "#9AA3B2"       # grey   — captions
FURN_C = "#FF5C5C"      # red    — page furniture (header / footer / page no.)
OCR_C = "#FF8C42"       # orange — OCR
PATH_C = "#FF5DA2"      # pink   — the reading-order path
CHUNK_C = "#F78C6C"     # salmon — chunk cards

GOOD = "#3DD68C"
BAD = "#FF5C5C"
ACCENT = "#FFD166"
BYLINE = "#5B8DEF"

# ---- code (Night-Owl-ish) palette ----------------------------------------- #
MONO = "Menlo"
PLAIN = "#D6DEEB"
COMMENT = "#5F6B7E"
KW = "#C792EA"          # keywords
FN = "#82AAFF"          # functions / fields
VAL = "#F78C6C"         # literals
STR = "#7FDBCA"         # strings / paths

RNG = np.random.default_rng(7)

FONT = "Helvetica Neue"
_BaseText.set_default(font=FONT)


# ========================================================================== #
# small reusable pieces
# ========================================================================== #
def txt(text, fs=24, color=INK, weight="NORMAL", font=None, slant=None):
    """``Text`` with optional kwargs, skipping None so Pango never chokes."""
    kw = {"font_size": fs, "color": color, "weight": weight}
    if font:
        kw["font"] = font
    if slant:
        kw["slant"] = slant
    return Text(text, **kw)


def _safe_t2c(s, table):
    """Per-line text->colour map, pruned so no key overlaps another (manim raises)."""
    present = {k: v for k, v in table.items() if k in s}
    keys = list(present)
    return {k: v for k, v in present.items()
            if not any(k != o and k in o for o in keys)}


def chip(text, color, fs=20, fill=0.14, w=None, h=0.56, tcolor=None, weight="NORMAL", radius=0.12):
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


def num_badge(n, center, color=PATH_C, r=0.16):
    c = Circle(radius=r, stroke_color=color, stroke_width=2.6,
               fill_color=BG, fill_opacity=1.0)
    t = Text(str(n), font_size=20, color=INK, weight="BOLD")
    t.scale_to_fit_height(r * 1.05)
    return VGroup(c, t).move_to([center[0], center[1], 0])


def wire_para(nlines, width, seed, lh=0.135, sw=2.6, color=PAPER_INK,
              last_short=True, opacity=0.75):
    """A wireframe paragraph: a stack of thin horizontal lines of varying length."""
    g = VGroup()
    r = np.random.default_rng(seed)
    for i in range(nlines):
        frac = r.uniform(0.72, 1.0)
        if last_short and i == nlines - 1:
            frac = r.uniform(0.4, 0.66)
        ln = Line(ORIGIN, [max(0.1, width * frac), 0, 0],
                  stroke_color=color, stroke_width=sw).set_opacity(opacity)
        g.add(ln)
    g.arrange(DOWN, buff=lh, aligned_edge=LEFT)
    return g


def wire_table(w, h, rows=4, cols=3, color=PAPER_INK, sw=2.0):
    """A wireframe table: an outer box with row/column rules and a header band."""
    outer = Rectangle(width=w, height=h, stroke_color=color, stroke_width=sw,
                      fill_opacity=0).set_stroke(opacity=0.85)
    g = VGroup(outer)
    for r in range(1, rows):
        y = h / 2 - r * (h / rows)
        g.add(Line([-w / 2, y, 0], [w / 2, y, 0], stroke_color=color,
                   stroke_width=sw * 0.7).set_opacity(0.6))
    for c in range(1, cols):
        x = -w / 2 + c * (w / cols)
        g.add(Line([x, -h / 2, 0], [x, h / 2, 0], stroke_color=color,
                   stroke_width=sw * 0.7).set_opacity(0.6))
    # header band (top row) a touch heavier
    band = Rectangle(width=w, height=h / rows, stroke_width=0,
                     fill_color=color, fill_opacity=0.18)
    band.move_to([0, h / 2 - h / rows / 2, 0])
    g.add(band)
    g.move_to(ORIGIN)
    return g


def wire_figure(w, h, color=PAPER_INK, seed=1):
    """A wireframe figure: a framed box with a little line chart inside."""
    box = Rectangle(width=w, height=h, stroke_color=color, stroke_width=2,
                    fill_opacity=0).set_stroke(opacity=0.85)
    r = np.random.default_rng(seed)
    n = 7
    xs = np.linspace(-w / 2 + 0.12, w / 2 - 0.12, n)
    ys = np.linspace(-h / 2 + 0.12, h / 2 - 0.16, n) * 0.0
    vals = np.cumsum(r.uniform(-0.4, 0.7, n))
    vals = (vals - vals.min()) / (np.ptp(vals) + 1e-6)
    pts = [[xs[i], -h / 2 + 0.14 + vals[i] * (h - 0.3), 0] for i in range(n)]
    curve = VMobject().set_points_as_corners([np.array(p) for p in pts])
    curve.set_stroke(color, 2).set_opacity(0.8)
    return VGroup(box, curve)


def make_page(w=3.5, h=4.75, seed=7):
    """A realistic wireframe page: title, two columns, a figure, a table, furniture.

    Returns ``(page_group, regions)`` where ``regions`` maps a name to the content
    mobject occupying that region (so later scenes can box / number them)."""
    shadow = Rectangle(width=w, height=h, fill_color="#000000", fill_opacity=0.30,
                       stroke_width=0).shift(RIGHT * 0.09 + DOWN * 0.10)
    page = Rectangle(width=w, height=h, fill_color=PAPER, fill_opacity=1.0,
                     stroke_color=PAPER_EDGE, stroke_width=1.6)

    margin = 0.26
    top = h / 2 - margin
    left = -w / 2 + margin
    right = w / 2 - margin
    colgap = 0.28
    colw = (right - left - colgap) / 2
    xL = left + colw / 2
    xR = right - colw / 2

    # title — two thick centred rules
    title = VGroup(
        Line(ORIGIN, [w * 0.60, 0, 0], stroke_color=PAPER_INK, stroke_width=6),
        Line(ORIGIN, [w * 0.42, 0, 0], stroke_color=PAPER_INK, stroke_width=6),
    ).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
    title.move_to([0, top - 0.30, 0])

    body_top = title.get_bottom()[1] - 0.22
    avail_h = body_top - (-h / 2 + 0.42)

    # left column: paragraph, figure, caption, paragraph
    fig = wire_figure(colw, 0.92, seed=seed + 5)
    cap = wire_para(1, colw * 0.9, seed + 6, sw=2.0, opacity=0.5, last_short=False)
    left_col = VGroup(
        wire_para(5, colw, seed + 1),
        fig, cap,
        wire_para(3, colw, seed + 2),
    ).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
    if left_col.height > avail_h:
        left_col.scale(avail_h / left_col.height)

    # right column: paragraph, table, paragraph
    tbl = wire_table(colw, 1.02, rows=4, cols=3)
    right_col = VGroup(
        wire_para(4, colw, seed + 3),
        tbl,
        wire_para(4, colw, seed + 4),
    ).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
    if right_col.height > avail_h:
        right_col.scale(avail_h / right_col.height)

    left_col.move_to([xL, body_top - left_col.height / 2, 0])
    right_col.move_to([xR, body_top - right_col.height / 2, 0])

    # page furniture — running header + footer + page number (faint)
    header = Line(ORIGIN, [1.0, 0, 0], stroke_color=PAPER_INK,
                  stroke_width=2).set_opacity(0.32).move_to([0, h / 2 - 0.15, 0])
    footer = Line(ORIGIN, [0.8, 0, 0], stroke_color=PAPER_INK,
                  stroke_width=2).set_opacity(0.32).move_to([left + 0.4, -h / 2 + 0.17, 0])
    pageno = Line(ORIGIN, [0.14, 0, 0], stroke_color=PAPER_INK,
                  stroke_width=2).set_opacity(0.32).move_to([right - 0.1, -h / 2 + 0.17, 0])

    page_group = VGroup(shadow, page, title, header, footer, pageno, left_col, right_col)
    regions = {
        "title": title,
        "header": header,
        "footer": VGroup(footer, pageno),
        "p1": left_col[0], "figure": fig, "caption": cap, "p2": left_col[3],
        "p3": right_col[0], "table": tbl, "p4": right_col[2],
    }
    return page_group, regions


def doc_glyph(w=1.15, h=1.5, color=INK, lines=3):
    """A small page icon (used as the token riding the pipeline conveyor)."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.07,
                            stroke_color=color, stroke_width=2.4,
                            fill_color=PAPER, fill_opacity=0.96)
    g = VGroup(body)
    for i in range(lines):
        ln = Line(ORIGIN, [w * 0.62, 0, 0], stroke_color=PAPER_INK,
                  stroke_width=2).set_opacity(0.7)
        ln.move_to([body.get_center()[0], body.get_top()[1] - 0.32 - i * 0.24, 0])
        ln.align_to([body.get_left()[0] + 0.18, 0, 0], LEFT)
        g.add(ln)
    g.body = body
    return g


def structured_doc(w=1.4, h=1.85):
    """A clean, 'resolved' structured document — typed blocks on a page."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.09,
                            stroke_color=ACCENT, stroke_width=2.6,
                            fill_color=PAPER, fill_opacity=0.97)

    def bar(frac, col, hh=0.11):
        return Rectangle(width=w * frac, height=hh, stroke_width=0,
                         fill_color=col, fill_opacity=0.9)

    inner = VGroup(
        bar(0.6, TITLE_C, 0.14),
        bar(0.74, TEXT_C),
        bar(0.68, TEXT_C),
        wire_table(w * 0.72, 0.34, rows=2, cols=3, color=TABLE_C, sw=1.4),
        bar(0.74, TEXT_C),
    ).arrange(DOWN, buff=0.1, aligned_edge=LEFT).move_to(body)
    return VGroup(body, inner)


def token_meter(ntok, budget=512, cap=680, w=1.55, h=0.15):
    """A little token-count bar with a budget marker. Green if within budget."""
    frac = min(1.0, ntok / cap)
    bfrac = budget / cap
    track = RoundedRectangle(width=w, height=h, corner_radius=h / 2,
                             stroke_color=FAINT, stroke_width=1.3, fill_opacity=0)
    over = ntok > budget
    col = BAD if over else GOOD
    fw = max(0.06, frac * w)
    fill = RoundedRectangle(width=fw, height=h, corner_radius=h / 2, stroke_width=0,
                            fill_color=col, fill_opacity=0.92)
    fill.move_to([track.get_left()[0] + fw / 2, track.get_center()[1], 0])
    mx = track.get_left()[0] + bfrac * w
    mark = Line([mx, track.get_center()[1] - h * 0.95, 0],
                [mx, track.get_center()[1] + h * 0.95, 0]).set_stroke(INK, 1.6)
    return VGroup(track, fill, mark)


def chunk_card(heading, ntok, budget=512, w=2.55, h=0.98, color=CHUNK_C, nlines=2):
    """A chunk: heading-path tag, a couple of text lines, and a token meter."""
    box = RoundedRectangle(width=w, height=h, corner_radius=0.1,
                           stroke_color=color, stroke_width=2,
                           fill_color=color, fill_opacity=0.09)
    tag = txt(heading, fs=15, color=color, weight="BOLD")
    if tag.width > w - 0.3:
        tag.scale((w - 0.3) / tag.width)
    tag.move_to([box.get_left()[0] + 0.16 + tag.width / 2, box.get_top()[1] - 0.18, 0])
    lines = VGroup(*[Line(ORIGIN, [(w - 0.5) * f, 0, 0], stroke_color=INK,
                          stroke_width=2).set_opacity(0.55)
                     for f in (0.95, 0.6)][:nlines]).arrange(DOWN, buff=0.1, aligned_edge=LEFT)
    lines.move_to([box.get_left()[0] + 0.16 + lines.width / 2,
                   box.get_center()[1] - 0.02, 0])
    meter = token_meter(ntok, budget, w=w - 0.9, h=0.13)
    lab = txt(f"{ntok} tok", fs=13, color=(BAD if ntok > budget else MUTED))
    mrow = VGroup(meter, lab).arrange(RIGHT, buff=0.14)
    mrow.move_to([box.get_center()[0], box.get_bottom()[1] + 0.18, 0])
    card = VGroup(box, tag, lines, mrow)
    card.box = box
    card.meter = meter
    card.toklab = lab
    return card


def db_cyl(w=1.5, h=1.7, color=TABLE_C):
    """A database cylinder (explicit colours — Ellipse defaults to red fill)."""
    ry = 0.22
    body = Rectangle(width=w, height=h - ry, stroke_width=0,
                     fill_color=color, fill_opacity=0.16)
    top = Ellipse(width=w, height=ry * 2, stroke_color=color, stroke_width=2.5,
                  fill_color=color, fill_opacity=0.28).move_to([0, (h - ry) / 2, 0])
    bot = Ellipse(width=w, height=ry * 2, stroke_color=color, stroke_width=2.5,
                  fill_color=color, fill_opacity=0.16).move_to([0, -(h - ry) / 2, 0])
    left = Line([-w / 2, -(h - ry) / 2, 0], [-w / 2, (h - ry) / 2, 0],
                stroke_color=color, stroke_width=2.5)
    right = Line([w / 2, -(h - ry) / 2, 0], [w / 2, (h - ry) / 2, 0],
                 stroke_color=color, stroke_width=2.5)
    return VGroup(body, bot, left, right, top)


# ========================================================================== #
class _DoclingBase(Scene):
    def setup(self):
        self.camera.background_color = BG
        self._cap = None

    # ---- timing helpers --------------------------------------------------- #
    def play(self, *anims, **kwargs):
        if not (len(anims) == 1 and isinstance(anims[0], Wait)):
            rt = kwargs.get("run_time")
            if rt is not None:
                kwargs["run_time"] = rt * ANIM_SLOW
        return super().play(*anims, **kwargs)

    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def read(self, k=1.0):
        self.wait(k * READ)

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

    # ---- text furniture --------------------------------------------------- #
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
        """The running bottom caption — Transformed in place so it reads smoothly."""
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

    # ---- code pill / panel ------------------------------------------------- #
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
    def play_intro(self):
        header = Text("Docling", font_size=66, color=INK, weight="BOLD")
        line = self._rule(header, ACCENT, pad=1.1, drop=0.45)
        writer = Text("Created by Ptolémé", font_size=28, color=BYLINE)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        sub = Text("How it turns a PDF into RAG-ready chunks — and where OCR plugs in",
                   font_size=30, color=MUTED)
        if sub.width > 12.0:
            sub.scale_to_fit_width(12.0)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.read(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        src = Text("open-source document parsing for generative AI",
                   font_size=22, color=MUTED)
        src.next_to(writer, DOWN, buff=0.4)
        self.play(FadeIn(src), run_time=0.8)
        self.read(1.4)
        self.play(FadeOut(VGroup(header, writer, line, src)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = self._rule(header, ACCENT, pad=1.0, drop=0.45)
        writer = Text("Created by Ptolémé", font_size=28, color=BYLINE)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = Text("Read the page like a human — then chunk it like a machine.",
                     font_size=26, color=ACCENT)
        recap.next_to(writer, DOWN, buff=0.5)
        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap), run_time=0.8)
        self.read(1.6)
        self.play(FadeOut(VGroup(header, line, writer, recap)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 — the problem: naïve extraction destroys structure
    # ====================================================================== #
    def scene_problem(self):
        self._cap = None
        title = Text("To a machine, a PDF is just ink on a page",
                     font_size=40, color=INK, weight="BOLD")
        self.play(Write(title), run_time=1.4)
        self.read(0.7)
        self.play(title.animate.scale(0.62).to_edge(UP, buff=0.4), run_time=0.7)

        # the page, centre stage
        page, regions = make_page(w=3.4, h=4.6, seed=7)
        page.scale(0.98).move_to([0, -0.35, 0])
        self.play(FadeIn(page, shift=UP * 0.15), run_time=0.9)
        self.say("We instantly see structure — a title, two columns, a figure, a table.",
                 color=INK)
        self.read(1.3)

        # slide the page left, bring in a slim extraction pill
        self.play(page.animate.scale(0.9).move_to([-4.0, -0.3, 0]), run_time=0.8)
        pill = self.code_pill('raw = extract_text("report.pdf")',
                              {"raw": FN, "extract_text": FN, '"report.pdf"': STR}, fs=20)
        pill.move_to([2.0, 2.05, 0])
        self.play(FadeIn(pill, shift=DOWN * 0.15), run_time=0.6)
        self.say("But naïve extraction just scrapes characters off the canvas…", color=INK)
        self.read(1.1)

        # the tumble: a jumbled bag of words spills out to the right
        pieces = ["Revenue", "the", "Q3", "42", "3.14", "results", "Figure", "2",
                  "and", "table", "of", "2024", "growth", "▢▢", "market", "see",
                  "1.2M", "EMEA", "total", "model", "▢", "data", "§", "…"]
        rng = np.random.default_rng(3)
        cloud = VGroup()
        region_x = (0.1, 5.9)
        region_y = (-2.1, 1.9)
        for wtok in pieces:
            if wtok.startswith("▢"):
                col = BAD
            elif any(ch.isdigit() for ch in wtok):
                col = OCR_C
            else:
                col = INK
            t = txt(wtok, fs=float(rng.uniform(19, 26)), color=col)
            t.move_to([rng.uniform(*region_x), rng.uniform(*region_y), 0])
            t.rotate(rng.uniform(-0.5, 0.5))
            cloud.add(t)
        beam = arr(page.get_right(), [region_x[0] - 0.1, 0.0, 0], color=MUTED, sw=3)
        self.play(GrowArrow(beam), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(t, scale=0.4) for t in cloud],
                              lag_ratio=0.06), run_time=1.8)
        lbl = txt("“bag of words”", fs=22, color=BAD, slant=ITALIC)
        lbl.move_to([(region_x[0] + region_x[1]) / 2, region_y[0] - 0.35, 0])
        self.play(FadeIn(lbl), run_time=0.5)
        self.say("…and the structure is gone: order scrambled, table flattened, scan unreadable.",
                 color=BAD)
        self.read(1.6)
        self.say("Feed this to a RAG system and you get garbage in, garbage out.",
                 color=INK)
        self.read(1.5)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — the pipeline (a conveyor the document rides through)
    # ====================================================================== #
    def scene_pipeline(self):
        self._cap = None
        header = self.section_header("The Docling pipeline", ACCENT)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # the conveyor track
        track = RoundedRectangle(width=12.4, height=0.5, corner_radius=0.25,
                                 stroke_color=FAINT, stroke_width=2,
                                 fill_color="#151A22", fill_opacity=1.0)
        track.move_to([0, -1.95, 0])
        dashes = VGroup(*[Line([x, -1.95, 0], [x + 0.22, -1.95, 0],
                               stroke_color=FAINT, stroke_width=2).set_opacity(0.7)
                          for x in np.arange(-5.9, 6.0, 0.6)])
        self.play(FadeIn(track), Create(dashes), run_time=0.7)

        # five stations across the top
        stns = [("Parse", MUTED), ("Layout", TEXT_C), ("OCR", OCR_C),
                ("Tables", TABLE_C), ("Assemble", ACCENT)]
        xs = np.linspace(-5.0, 5.0, len(stns))
        chips = VGroup()
        for (name, col), x in zip(stns, xs):
            c = chip(name, col, fs=20, w=1.95, h=0.62, fill=0.10, weight="BOLD")
            c.move_to([x, 1.45, 0])
            chips.add(c)
        self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.15) for c in chips],
                              lag_ratio=0.12), run_time=1.0)
        self.say("Docling runs a document through a pipeline of stages.", color=INK)
        self.read(1.0)

        # the document rides on
        doc = doc_glyph(w=1.05, h=1.4).move_to([-6.1, -1.15, 0])
        self.play(FadeIn(doc, shift=RIGHT * 0.3), run_time=0.6)

        stage_caps = [
            ("Parse the file — pull out characters, images and their geometry.", MUTED),
            ("Detect and type every block on the page.", TEXT_C),
            ("Read text that is trapped inside images.", OCR_C),
            ("Rebuild tables — cells, rows and spans.", TABLE_C),
            ("Assemble one structured DoclingDocument.", ACCENT),
        ]

        def beam(chip_m, doc_m, col):
            return Line([doc_m.get_center()[0], chip_m.get_bottom()[1] - 0.02, 0],
                        [doc_m.get_center()[0], doc_m.get_top()[1] + 0.02, 0],
                        stroke_color=col, stroke_width=4).set_opacity(0.85)

        for i, (name, col) in enumerate(stns):
            self.play(doc.animate.move_to([xs[i], -1.15, 0]), run_time=0.7)
            b = beam(chips[i], doc, col)
            self.play(chips[i].animate.set_fill(col, opacity=0.28),
                      chips[i][0].animate.set_stroke(width=3.5),
                      Create(b), Flash(chips[i].get_center(), color=col,
                                       line_length=0.14, num_lines=10, flash_radius=0.5),
                      run_time=0.55)
            # give the doc that stage's feature
            feat = None
            if name == "Layout":
                feat = VGroup(
                    SurroundingRectangle(doc[1], color=TITLE_C, buff=0.02, stroke_width=2.4),
                    SurroundingRectangle(doc[2], color=TEXT_C, buff=0.02, stroke_width=2.4),
                    SurroundingRectangle(doc[3], color=TABLE_C, buff=0.02, stroke_width=2.4),
                )
                self.play(LaggedStart(*[Create(r) for r in feat], lag_ratio=0.2),
                          run_time=0.6)
                doc.add(feat)
            elif name == "OCR":
                patch = Square(0.3, stroke_width=0, fill_color=OCR_C,
                               fill_opacity=0.6).move_to(doc[3])
                self.add(patch)
                newl = Line(ORIGIN, [0.5, 0, 0], stroke_color=OCR_C,
                            stroke_width=2.4).move_to(doc[3])
                self.play(Transform(patch, newl), run_time=0.55)
                doc.add(patch)
            elif name == "Tables":
                grid = wire_table(0.6, 0.42, rows=3, cols=3, color=TABLE_C, sw=1.6)
                grid.move_to(doc[2])
                self.play(FadeIn(grid, scale=0.6), run_time=0.5)
                doc.add(grid)
            self.say(stage_caps[i][0], color=stage_caps[i][1])
            self.read(0.9)
            self.play(FadeOut(b), run_time=0.25)

        # arrive: collapse the ride into a clean, resolved DoclingDocument
        self.play(doc.animate.move_to([6.0, -1.15, 0]), run_time=0.7)
        clean = structured_doc(w=1.5, h=1.95).move_to([0, 0.1, 0])
        self.play(FadeOut(VGroup(track, dashes, chips)),
                  ReplacementTransform(doc, clean), run_time=0.8)
        result = chip("DoclingDocument", ACCENT, fs=24, w=4.0, h=0.8,
                      fill=0.16, weight="BOLD")
        result.next_to(clean, UP, buff=0.4)
        exports = VGroup(chip("Markdown", TEXT_C, fs=19, w=2.0),
                         chip("JSON", TABLE_C, fs=19, w=1.7),
                         chip("HTML", FIG_C, fs=19, w=1.7)).arrange(RIGHT, buff=0.4)
        exports.next_to(clean, DOWN, buff=0.5)
        e_arrows = VGroup(*[arr(clean.get_bottom(), c.get_top(), color=MUTED, sw=3)
                            for c in exports])
        self.play(FadeIn(result, shift=DOWN * 0.15), run_time=0.6)
        self.say("The output is one clean, structured document…", color=ACCENT)
        self.read(1.0)
        self.play(LaggedStart(*[GrowArrow(a) for a in e_arrows], lag_ratio=0.15),
                  LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in exports],
                              lag_ratio=0.15), run_time=1.0)
        self.say("…exportable to Markdown, JSON or HTML. Now let's zoom into two stages.",
                 color=INK)
        self.read(1.5)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — layout understanding & reading order
    # ====================================================================== #
    def scene_layout(self):
        self._cap = None
        header = self.section_header("Understanding the page", TEXT_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        page, regions = make_page(w=3.5, h=4.75, seed=7)
        page.scale(0.86).move_to([-3.1, -0.25, 0])
        self.play(FadeIn(page, shift=UP * 0.1), run_time=0.8)
        self.say("Docling first looks at the page as an image.", color=INK)
        self.read(1.0)

        # bounding boxes, colour-coded by type
        box_spec = [
            ("title", TITLE_C), ("p1", TEXT_C), ("figure", FIG_C), ("caption", CAP_C),
            ("p2", TEXT_C), ("p3", TEXT_C), ("table", TABLE_C), ("p4", TEXT_C),
        ]
        boxes = {}
        for name, col in box_spec:
            r = SurroundingRectangle(regions[name], color=col, buff=0.04,
                                     corner_radius=0.03, stroke_width=2.6)
            boxes[name] = r
        furn = VGroup(
            SurroundingRectangle(regions["header"], color=FURN_C, buff=0.03, stroke_width=2.2),
            SurroundingRectangle(regions["footer"], color=FURN_C, buff=0.03, stroke_width=2.2),
        )

        # legend on the right
        legend_items = [("Title / heading", TITLE_C), ("Text", TEXT_C),
                        ("Figure", FIG_C), ("Caption", CAP_C),
                        ("Table", TABLE_C), ("Page furniture", FURN_C)]
        legend = VGroup()
        for name, col in legend_items:
            sw = Square(0.24, stroke_color=col, stroke_width=2.4, fill_color=col,
                        fill_opacity=0.18)
            lab = txt(name, fs=19, color=INK)
            legend.add(VGroup(sw, lab).arrange(RIGHT, buff=0.2))
        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.26).move_to([3.3, 0.35, 0])
        ltitle = txt("Detected blocks", fs=20, color=MUTED, weight="BOLD")
        ltitle.next_to(legend, UP, buff=0.3).align_to(legend, LEFT)

        self.play(FadeIn(ltitle), run_time=0.4)
        self.play(LaggedStart(*[Create(boxes[n]) for n, _ in box_spec], lag_ratio=0.12),
                  LaggedStart(*[FadeIn(it, shift=RIGHT * 0.12) for it in legend],
                              lag_ratio=0.12), run_time=1.6)
        self.say("Every block is detected and typed.", color=INK)
        self.read(1.1)

        # furniture is detected then discarded
        self.play(Create(furn), run_time=0.5)
        xs = VGroup(*[make_cross(FURN_C, sw=4, scale=0.7).move_to(f) for f in furn])
        self.play(LaggedStart(*[FadeIn(x) for x in xs], lag_ratio=0.2), run_time=0.5)
        self.play(FadeOut(furn), FadeOut(xs), run_time=0.5)
        self.say("Running headers, footers and page numbers are dropped.", color=FURN_C)
        self.read(1.2)

        # reading order — number the blocks, thread a path through them
        order = ["title", "p1", "figure", "caption", "p2", "p3", "table", "p4"]
        centers = [regions[n].get_center() for n in order]
        self.say("Then it recovers the reading order — down the left column, then the right.",
                 color=PATH_C)
        segs = VGroup()
        badges = VGroup()
        for i, c in enumerate(centers):
            badge = num_badge(i + 1, c)
            if i > 0:
                seg = Line(centers[i - 1], c, stroke_color=PATH_C, stroke_width=3.5)
                seg.set_opacity(0.9)
                self.play(Create(seg), run_time=0.32)
                segs.add(seg)
            self.play(FadeIn(badge, scale=0.5), run_time=0.28)
            badges.add(badge)
        self.read(1.3)

        # table structure micro-moment (TableFormer)
        self.play(Indicate(boxes["table"], color=TABLE_C, scale_factor=1.08), run_time=0.6)
        grid = wire_table(regions["table"].width, regions["table"].height,
                          rows=4, cols=3, color=TABLE_C, sw=2.2)
        grid.move_to(regions["table"])
        span = Rectangle(width=regions["table"].width * 0.62,
                         height=regions["table"].height / 4,
                         stroke_color=ACCENT, stroke_width=2.4, fill_opacity=0)
        span.move_to([regions["table"].get_center()[0],
                      regions["table"].get_top()[1] - regions["table"].height / 8, 0])
        self.play(Create(grid), run_time=0.5)
        self.play(Create(span), Flash(span.get_center(), color=ACCENT,
                                      line_length=0.12, num_lines=10, flash_radius=0.4),
                  run_time=0.5)
        self.say("Tables get their own model — cells, rows and spans rebuilt (TableFormer).",
                 color=TABLE_C)
        self.read(1.4)
        self.say("Every block: typed, located, and in the right order.", color=INK)
        self.read(1.3)
        self.play(FadeIn(self.cite("layout & table structure: Docling — Auer et al., IBM Research 2024")),
                  run_time=0.4)
        self.read(0.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — OCR: a pluggable step that reads pixels
    # ====================================================================== #
    def scene_ocr(self):
        self._cap = None
        header = self.section_header("Plugging in OCR", OCR_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # left: a scanned tile with text trapped in pixels
        tw, th = 3.0, 3.2
        img = Rectangle(width=tw, height=th, fill_color="#D8D2C4", fill_opacity=1.0,
                        stroke_color="#B9B2A2", stroke_width=1.6)
        noise = VGroup(*[Line([-tw / 2 + 0.1, y, 0], [tw / 2 - 0.1, y, 0],
                              stroke_color="#C4BDAD", stroke_width=3).set_opacity(0.5)
                        for y in np.linspace(-th / 2 + 0.3, th / 2 - 0.3, 14)])
        trapped = VGroup()
        r = np.random.default_rng(11)
        ys = np.linspace(th / 2 - 0.55, -th / 2 + 0.4, 6)
        for y in ys:
            ln = Line(ORIGIN, [tw * r.uniform(0.45, 0.8), 0, 0],
                      stroke_color="#8C8676", stroke_width=3.2).set_opacity(0.55)
            ln.move_to([-tw / 2 + 0.28 + ln.width / 2, y, 0])
            trapped.add(ln)
        tile = VGroup(img, noise, trapped).rotate(-0.02).move_to([-3.7, 0.35, 0])
        tlbl = txt("scanned image — pixels, no text layer", fs=18, color=MUTED)
        tlbl.next_to(tile, DOWN, buff=0.22)
        self.play(FadeIn(tile, shift=UP * 0.1), FadeIn(tlbl), run_time=0.8)
        self.say("Some pages have no text layer at all — a scan, a photo, a screenshot.",
                 color=INK)
        self.read(1.3)

        # naïve extraction returns nothing
        empty = txt("∅  no text found", fs=24, color=BAD)
        empty.move_to([3.6, 0.35, 0])
        dashed = DashedVMobject(arr(tile.get_right(), [1.6, 0.35, 0], color=BAD, sw=3),
                                num_dashes=18)
        self.play(Create(dashed), FadeIn(empty, shift=RIGHT * 0.2), run_time=0.7)
        self.say("Plain extraction returns nothing — the words are trapped in pixels.",
                 color=BAD)
        self.read(1.4)
        self.play(FadeOut(dashed), FadeOut(empty), run_time=0.4)

        # the pluggable OCR socket in the middle
        socket = DashedVMobject(
            RoundedRectangle(width=1.8, height=1.05, corner_radius=0.12,
                             stroke_color=OCR_C, stroke_width=2.6), num_dashes=34)
        socket.move_to([0, 0.35, 0])
        slbl = txt("OCR engine", fs=17, color=OCR_C).move_to(socket)
        # output panel on the right
        panel = RoundedRectangle(width=tw, height=th, corner_radius=0.12,
                                 stroke_color=OCR_C, stroke_width=2,
                                 fill_color="#0A0E15", fill_opacity=1.0)
        panel.move_to([3.7, 0.35, 0])
        pttl = txt("recognized text", fs=16, color=OCR_C)
        pttl.move_to([panel.get_left()[0] + pttl.width / 2 + 0.2,
                      panel.get_top()[1] - 0.22, 0])
        self.play(FadeIn(socket), FadeIn(slbl), FadeIn(panel), FadeIn(pttl), run_time=0.7)

        # engine option cards along the bottom
        engines = ["EasyOCR", "Tesseract", "RapidOCR", "ocrmac"]
        cards = VGroup(*[chip(e, OCR_C, fs=18, w=2.0, h=0.6, fill=0.10, weight="BOLD")
                         for e in engines]).arrange(RIGHT, buff=0.35)
        cards.move_to([0, -2.7, 0])
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in cards],
                              lag_ratio=0.12), run_time=0.9)
        pill = self.code_pill('PdfPipelineOptions(do_ocr=True, ocr_options=EasyOcrOptions())',
                              {"PdfPipelineOptions": FN, "do_ocr": FN, "True": VAL,
                               "ocr_options": FN, "EasyOcrOptions": FN}, fs=17, w_max=8.6)
        pill.move_to([0, 2.45, 0])
        self.play(FadeIn(pill, shift=DOWN * 0.1), run_time=0.5)
        self.say("Docling makes OCR a pluggable step — choose your engine.", color=OCR_C)
        self.read(1.2)

        # dock EasyOCR into the socket
        chosen = cards[0]
        ghost = chosen.copy()
        self.play(ghost.animate.move_to(socket).scale(0.92), FadeOut(slbl),
                  socket.animate.set_stroke(opacity=1.0), run_time=0.7)
        self.play(Indicate(ghost, color=OCR_C, scale_factor=1.1),
                  chosen.animate.set_fill(OCR_C, opacity=0.28), run_time=0.5)

        # the scanning beam sweeps down; characters materialize into the panel
        self.say("A scanning pass turns pixels into characters.", color=OCR_C)
        beam = Rectangle(width=tw, height=0.12, stroke_width=0,
                         fill_color=OCR_C, fill_opacity=0.9)
        beam.move_to([tile.get_center()[0], tile.get_top()[1] - 0.1, 0])
        glow = Rectangle(width=tw, height=0.5, stroke_width=0,
                         fill_color=OCR_C, fill_opacity=0.16)
        glow.move_to(beam)
        self.add(glow, beam)
        out_lines = VGroup()
        for i, src in enumerate(trapped):
            self.play(beam.animate.move_to([tile.get_center()[0], src.get_center()[1], 0]),
                      glow.animate.move_to([tile.get_center()[0], src.get_center()[1], 0]),
                      run_time=0.28)
            # first line reads as a real header; the rest are crisp wire-lines
            if i == 0:
                crisp = txt("INVOICE  #4471", fs=19, color=INK, weight="BOLD")
                crisp.move_to([panel.get_left()[0] + 0.24 + crisp.width / 2,
                               panel.get_top()[1] - 0.62, 0])
            else:
                crisp = Line(ORIGIN, [src.width * 1.02, 0, 0], stroke_color=INK,
                             stroke_width=3).set_opacity(0.85)
                crisp.move_to([panel.get_left()[0] + 0.24 + crisp.width / 2,
                               panel.get_top()[1] - 0.62 - i * 0.38, 0])
            self.play(Indicate(src, color=OCR_C, scale_factor=1.05),
                      TransformFromCopy(src, crisp), run_time=0.4)
            out_lines.add(crisp)
        self.play(FadeOut(beam), FadeOut(glow), run_time=0.3)
        conf = txt("confidence 0.98", fs=15, color=GOOD)
        conf.move_to([panel.get_center()[0], panel.get_bottom()[1] + 0.22, 0])
        self.play(FadeIn(conf), run_time=0.4)
        self.read(1.3)

        # swap the engine — same interface, same result
        self.play(FadeOut(ghost),
                  cards[0].animate.set_fill(OCR_C, opacity=0.10), run_time=0.4)
        ghost2 = cards[1].copy()
        self.play(ghost2.animate.move_to(socket).scale(0.92),
                  cards[1].animate.set_fill(OCR_C, opacity=0.28), run_time=0.6)
        self.play(Indicate(ghost2, color=OCR_C, scale_factor=1.1),
                  Indicate(out_lines, color=OCR_C, scale_factor=1.02), run_time=0.5)
        self.say("Same interface, any engine — EasyOCR, Tesseract, RapidOCR, ocrmac.",
                 color=OCR_C)
        self.read(1.4)
        self.say("Scanned pages stop being black holes — they become structured text.",
                 color=INK)
        self.read(1.4)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — chunking for RAG: Hierarchical, then Hybrid (token-aware)
    # ====================================================================== #
    def scene_chunk(self):
        self._cap = None
        header = self.section_header("Chunking for RAG", CHUNK_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # ---- the DoclingDocument as a hierarchy, on the left ---- #
        tree_rows = [
            ("Annual Report 2024", "title"),
            ("Overview", "h"),
            ("paragraph", "p"), ("paragraph", "p"),
            ("Results", "h"),
            ("paragraph", "p"), ("[ table ]", "tbl"), ("paragraph", "p"),
            ("Outlook", "h"),
            ("paragraph", "p"),
        ]
        rows = VGroup()
        for text_s, kind in tree_rows:
            if kind == "title":
                m = txt(text_s, fs=20, color=INK, weight="BOLD")
                indent = 0.0
            elif kind == "h":
                dot = Triangle().scale(0.06).set_fill(TITLE_C, 1).set_stroke(width=0).rotate(-PI / 2)
                lab = txt(text_s, fs=18, color=TITLE_C, weight="BOLD")
                m = VGroup(dot, lab).arrange(RIGHT, buff=0.12)
                indent = 0.35
            elif kind == "tbl":
                m = txt(text_s, fs=16, color=TABLE_C)
                indent = 0.75
            else:
                m = Line(ORIGIN, [1.3, 0, 0], stroke_color=TEXT_C, stroke_width=3).set_opacity(0.7)
                indent = 0.75
            m._indent = indent
            rows.add(m)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        for m in rows:
            m.shift(RIGHT * m._indent)
        rows.move_to([-4.4, 0.15, 0])
        brace = Line(rows.get_top() + LEFT * 0.05, rows.get_bottom() + LEFT * 0.05
                     ).set_stroke(FAINT, 3).next_to(rows, LEFT, buff=0.2)
        self.play(LaggedStart(*[FadeIn(m, shift=RIGHT * 0.1) for m in rows],
                              lag_ratio=0.08), Create(brace), run_time=1.4)
        self.say("Docling hands you one clean, hierarchical document.", color=INK)
        self.read(1.1)
        self.say("But RAG doesn't retrieve documents — it retrieves chunks.", color=CHUNK_C)
        self.read(1.3)

        # ---- Hierarchical chunker: one chunk per structural unit ---- #
        sub = txt("HierarchicalChunker — split along the structure", fs=20,
                  color=CHUNK_C, weight="BOLD").to_edge(UP, buff=0.55).shift(RIGHT * 1.6)
        self.play(FadeIn(sub, shift=DOWN * 0.1), run_time=0.5)

        specs = [("Overview", 150), ("Results • intro", 95), ("Results • table", 45),
                 ("Results • detail", 690), ("Outlook", 80)]
        cards = VGroup(*[chunk_card(h, n) for h, n in specs])
        cards.arrange(DOWN, buff=0.16).move_to([1.7, -0.15, 0])
        if cards.height > 5.4:
            cards.scale(5.4 / cards.height)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.15) for c in cards],
                              lag_ratio=0.12), run_time=1.6)
        self.say("Each chunk keeps its heading trail as metadata — where it came from.",
                 color=INK)
        self.read(1.4)

        # highlight the size problem
        tiny = cards[2]
        big = cards[3]
        self.play(Indicate(tiny, color=ACCENT, scale_factor=1.05),
                  Indicate(big, color=BAD, scale_factor=1.05), run_time=0.7)
        self.say("But sizes are all over the place — some tiny, one blows past the token limit.",
                 color=BAD)
        self.read(1.5)

        # ---- Hybrid chunker: merge the small, split the big ---- #
        self.play(FadeOut(brace), rows.animate.set_opacity(0.28), run_time=0.5)
        sub2 = txt("HybridChunker — make it tokenizer-aware", fs=20,
                   color=GOOD, weight="BOLD").move_to(sub)
        self.play(Transform(sub, sub2), run_time=0.5)

        # merge: 'Results • intro' (95) + 'Results • table' (45) -> 140
        self.say("Merge chunks that are too small…", color=GOOD)
        merged = chunk_card("Results • intro", 140, color=CHUNK_C)
        merged.move_to((cards[1].get_center() + cards[2].get_center()) / 2)
        self.play(cards[1].animate.move_to(merged).set_opacity(0.0),
                  cards[2].animate.move_to(merged).set_opacity(0.0), run_time=0.6)
        self.play(FadeIn(merged, scale=1.05), run_time=0.5)
        self.read(1.0)

        # split: 'Results • detail' (690) -> 360 + 330
        self.say("…and split the ones that are too big — at sentence boundaries.", color=GOOD)
        part_a = chunk_card("Results • detail (1/2)", 360, color=CHUNK_C)
        part_b = chunk_card("Results • detail (2/2)", 330, color=CHUNK_C)
        parts = VGroup(part_a, part_b).arrange(DOWN, buff=0.16).move_to(big)
        self.play(big.animate.scale(1.02).set_stroke(BAD, 3), run_time=0.4)
        self.play(FadeOut(big, scale=0.9), run_time=0.35)
        self.play(LaggedStart(FadeIn(part_a, shift=UP * 0.1),
                              FadeIn(part_b, shift=DOWN * 0.1), lag_ratio=0.3), run_time=0.7)
        self.read(1.0)

        # re-stack the final chunks; all meters within budget
        final = VGroup(cards[0], merged, part_a, part_b, cards[4])
        final.generate_target()
        final.target.arrange(DOWN, buff=0.14).move_to([1.7, -0.15, 0])
        if final.target.height > 5.4:
            final.target.scale(5.4 / final.target.height)
        self.play(MoveToTarget(final), run_time=0.9)
        budget_note = txt("all ≤ 512 tokens", fs=17, color=GOOD)
        budget_note.next_to(final, UP, buff=0.22)
        self.play(FadeIn(budget_note), run_time=0.4)
        self.say("Every chunk sized to the embedding model's token budget — context kept.",
                 color=GOOD)
        self.read(1.4)

        pill = self.code_pill('HybridChunker(tokenizer=tok, max_tokens=512)',
                              {"HybridChunker": FN, "tokenizer": FN, "tok": VAL,
                               "max_tokens": FN, "512": VAL}, fs=17, w_max=5.2)
        pill.move_to([-2.7, -2.55, 0])
        self.play(FadeIn(pill, shift=UP * 0.1), run_time=0.5)
        self.read(1.1)

        # ---- flow into embeddings + a vector store ---- #
        self.play(FadeOut(VGroup(rows, sub, budget_note, pill)),
                  final.animate.scale(0.8).arrange(DOWN, buff=0.1).move_to([-4.6, 0.0, 0]),
                  run_time=0.8)
        embed = chip("Embedding\nmodel", TEXT_C, fs=18, w=2.0, h=1.0, fill=0.14, weight="BOLD")
        embed.move_to([-1.4, 0.0, 0])
        store = db_cyl(1.5, 1.9, color=TABLE_C).move_to([2.2, 0.0, 0])
        store_lbl = txt("vector store", fs=18, color=TABLE_C).next_to(store, DOWN, buff=0.2)
        a1 = arr(final.get_right(), embed.get_left(), color=MUTED, sw=3)
        a2 = arr(embed.get_right(), store.get_left(), color=MUTED, sw=3)
        self.play(GrowArrow(a1), FadeIn(embed), run_time=0.6)
        vecs = VGroup(*[Dot(radius=0.06, color=CHUNK_C) for _ in range(5)])
        for d in vecs:
            d.move_to(embed.get_right())
        self.play(GrowArrow(a2), FadeIn(store), FadeIn(store_lbl), run_time=0.6)
        self.play(LaggedStart(*[d.animate.move_to(
            store.get_center() + np.array([np.cos(t) * 0.4, np.sin(t) * 0.5, 0]))
            for t, d in zip(np.linspace(0, TAU, 5, endpoint=False), vecs)],
            lag_ratio=0.12), run_time=1.0)
        self.say("Then embed each chunk, store the vectors, and retrieve the right ones on demand.",
                 color=INK)
        self.read(1.5)
        self.say("Structure-aware and token-aware — the chunk is the unit RAG retrieves.",
                 color=CHUNK_C)
        self.read(1.5)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Closing takeaway
    # ====================================================================== #
    def scene_recap(self):
        self._cap = None
        lines = VGroup(
            Text("Docling, in one breath:", font_size=30, color=MUTED),
            Text("Read the page like a human —", font_size=34, color=INK, weight="BOLD"),
            Text("layout, reading order, tables, OCR.", font_size=26, color=TEXT_C),
            Text("Then chunk it like a machine —", font_size=34, color=INK, weight="BOLD"),
            Text("structure-aware and token-aware.", font_size=26, color=CHUNK_C),
            Text("Messy PDF in, RAG-ready chunks out.", font_size=28, color=ACCENT),
        ).arrange(DOWN, buff=0.3)
        self.play(FadeIn(lines[0]), run_time=0.6)
        self.read(0.5)
        self.play(Write(lines[1]), run_time=0.9)
        self.play(FadeIn(lines[2], shift=UP * 0.1), run_time=0.6)
        self.read(1.0)
        self.play(Write(lines[3]), run_time=0.9)
        self.play(FadeIn(lines[4], shift=UP * 0.1), run_time=0.6)
        self.read(1.0)
        self.play(FadeIn(lines[5], shift=UP * 0.12), run_time=0.8)
        self.read(1.7)
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_problem()
        self.scene_pipeline()
        self.scene_layout()
        self.scene_ocr()
        self.scene_chunk()
        self.scene_recap()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_DoclingBase):
    def construct(self):
        self.play_intro()


class Problem(_DoclingBase):
    def construct(self):
        self.scene_problem()


class Pipeline(_DoclingBase):
    def construct(self):
        self.scene_pipeline()


class Layout(_DoclingBase):
    def construct(self):
        self.scene_layout()


class OCR(_DoclingBase):
    def construct(self):
        self.scene_ocr()


class Chunk(_DoclingBase):
    def construct(self):
        self.scene_chunk()


class Recap(_DoclingBase):
    def construct(self):
        self.scene_recap()


class Outro(_DoclingBase):
    def construct(self):
        self.play_outro()


class DoclingFilm(_DoclingBase):
    """The whole ~4-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    DoclingFilm().render()

"""React.js & a Chatbot System Design — a ~3-minute explainer, house-style.

Two halves:

  Part A — what React.js actually is (a bit past "it's for frontends")
    1. What is React?     -- a JS library for UIs; declarative + component-based
    2. Components         -- the UI is a tree of small, reusable components
    3. Reconciliation     -- the deep bit: state → re-render → Virtual-DOM diff →
                             minimal real-DOM patch (useState / useEffect)
    4. What it's used for  -- SPAs, dashboards, chat UIs; Next.js / React Native

  Part B — a concrete system, front to back
    5. Architecture       -- a chatbot: React FE · FastAPI streaming backend · LLM ·
                             Celery + Docling ingestion data-service · Postgres ·
                             vector store · observability
    6. The two flows      -- offline async ingestion (Celery/Docling) vs. the
                             online streaming chat path (retrieve → generate →
                             stream → persist → observe)

Bookended by the channel's intro card and the "Thank you for watching!" outro
(matches animations/HarnessEngineering/harness_engineering.py).

Everything uses ``Text`` (Pango) rather than ``Tex`` so it renders without a
LaTeX install and stays fast to iterate on.

Scenes are exposed both individually (``WhatIs``, ``Components``, ``Reconcile``,
``UsedFor``, ``Architecture``, ``Flows``, ``Intro``, ``Outro``) and as one
continuous film (``ReactChatbot``).

Env knobs:
    RC_QUICK=1   shorten every hold for a fast sanity render
"""

from __future__ import annotations

import os

import numpy as np
from manim import *

# --- crisp text ------------------------------------------------------------ #
# Manim's ``Text`` quantises glyph positions badly at small font sizes, so body
# text below ~20 pt comes out with uneven letter/word spacing ("com pon ent").
# Work around it once, here: always render glyphs at a large, crisp base size and
# scale the mobject *down* to the requested size (scaling a large, correctly-spaced
# render down stays crisp; rendering small does not). This shadows manim's ``Text``
# so every call in this module benefits automatically.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("RC_QUICK") == "1"
# Single knob for pacing: every on-screen "hold" is scaled by this. QUICK
# collapses the holds for fast iteration; otherwise it sets the reading rhythm.
# 1.5 lands the whole film around ~3 minutes.
DELAY = 0.25 if QUICK else 1.5
# Slow every played animation to ~85% speed so motion doesn't feel rushed.
ANIM_SLOW = 1.0 if QUICK else 1.15
# Beat held on the finished scene before it wipes to the next one.
SCENE_GAP = 0.0 if QUICK else 3.5

# ---- palette -------------------------------------------------------------- #
BG = "#0E1117"       # dark slate background
PANEL = "#151A23"    # panel fill
INK = "#F5F3EF"      # warm white text
MUTED = "#8A93A6"    # secondary text / faint arrows
FAINT = "#3A4152"    # gridlines / idle connectors

REACT_C = "#61DAFB"  # React's signature cyan — the frontend
API_C = "#5B8DEF"    # backend API (blue)
LLM_C = "#B197FC"    # the model (purple)
WORK_C = "#3DD68C"   # Celery workers (green)
OCR_C = "#FF8C42"    # Docling / ingestion (orange)
DB_C = "#2EC4B6"     # storage (teal)
OBS_C = "#FF6FB5"    # observability (pink)
ACCENT = "#FFD166"   # highlight (gold)
GOOD = "#3DD68C"
BAD = "#FF5C5C"


# ---- small reusable pieces ------------------------------------------------ #
def fitted_text(text, max_width=None, font_size=26, **kw):
    """A crisp ``Text`` shrunk to fit ``max_width``."""
    t = Text(text, font_size=font_size, **kw)
    if max_width is not None and t.width > max_width:
        t.scale(max_width / t.width)
    return t


def node_box(title, center, color, sub=None, w=2.6, h=1.0, fs=23, subfs=16,
             fill=0.10):
    """A rounded, tinted box with a bold title and an optional muted subtitle.

    grp[0] is always the rectangle, so connectors can anchor on grp[0].
    ``center`` may be a 2-tuple ``(x, y)`` or a full 3-D point.
    """
    center = np.array([center[0], center[1], center[2] if len(center) > 2 else 0.0])
    rect = RoundedRectangle(
        width=w, height=h, corner_radius=0.14,
        stroke_color=color, stroke_width=3,
        fill_color=color, fill_opacity=fill,
    ).move_to(center)
    if sub:
        t = Text(title, font_size=fs, color=INK, weight="BOLD")
        s = Text(sub, font_size=subfs, color=MUTED)
        lab = VGroup(t, s).arrange(DOWN, buff=0.09)
    else:
        lab = Text(title, font_size=fs, color=INK, weight="BOLD")
    if lab.width > w - 0.32:
        lab.scale((w - 0.32) / lab.width)
    lab.move_to(rect)
    return VGroup(rect, lab)


def chip(text, color, w=2.3, h=0.95, fs=24, fill=0.12, tcolor=None, radius=0.14):
    """A rounded, tinted box with a centered auto-fitting label."""
    box = RoundedRectangle(
        width=w, height=h, corner_radius=radius,
        stroke_color=color, stroke_width=3,
        fill_color=color, fill_opacity=fill,
    )
    label = fitted_text(text, max_width=w - 0.32, font_size=fs, color=tcolor or INK)
    label.move_to(box)
    return VGroup(box, label)


def harrow(start, end, color=MUTED, sw=4):
    return Arrow(
        start, end, buff=0.12, stroke_width=sw, color=color,
        max_tip_length_to_length_ratio=0.16, tip_length=0.22,
    )


def edge_pts(a, b):
    """Boundary points on boxes ``a`` and ``b`` along their connecting direction.

    Picks the left/right edges when the link is mostly horizontal, top/bottom when
    mostly vertical. ``a``/``b`` are node VGroups (rect at index 0).
    """
    ra, rb = a[0], b[0]
    ca, cb = ra.get_center(), rb.get_center()
    dx, dy = cb[0] - ca[0], cb[1] - ca[1]
    if abs(dx) >= abs(dy):
        pa = ra.get_right() if dx > 0 else ra.get_left()
        pb = rb.get_left() if dx > 0 else rb.get_right()
    else:
        pa = ra.get_top() if dy > 0 else ra.get_bottom()
        pb = rb.get_bottom() if dy > 0 else rb.get_top()
    return pa, pb


def connector(a, b, color=FAINT, sw=2.5, dashed=False):
    pa, pb = edge_pts(a, b)
    if dashed:
        ln = DashedLine(pa, pb, dash_length=0.12, dashed_ratio=0.55)
    else:
        ln = Line(pa, pb)
    ln.set_stroke(color, sw)
    return ln


def react_logo(color=REACT_C, scale=1.0):
    """The classic React 'atom': a nucleus + three rotated orbital ellipses."""
    nucleus = Dot(radius=0.13, color=color)
    orbits = VGroup()
    for ang in (0, 60, 120):
        e = Ellipse(width=3.4, height=1.28, color=color, stroke_width=4)
        e.set_fill(opacity=0)
        e.rotate(ang * DEGREES)
        orbits.add(e)
    return VGroup(orbits, nucleus).scale(scale)


def browser(w=4.6, h=2.7, color=MUTED, title="chat"):
    """A little browser window: a title bar with three dots + a content area."""
    frame = RoundedRectangle(
        width=w, height=h, corner_radius=0.12,
        stroke_color=color, stroke_width=2.5,
        fill_color=PANEL, fill_opacity=0.85,
    )
    bar_y = frame.get_top()[1] - 0.28
    dots = VGroup(*[Dot([frame.get_left()[0] + 0.32 + i * 0.26, bar_y, 0],
                        radius=0.055, color=c)
                    for i, c in enumerate([BAD, ACCENT, GOOD])])
    sep = Line([frame.get_left()[0], bar_y - 0.22, 0],
               [frame.get_right()[0], bar_y - 0.22, 0]).set_stroke(color, 1.5)
    lab = Text(title, font_size=15, color=MUTED)
    lab.move_to([frame.get_center()[0], bar_y, 0])
    return dict(group=VGroup(frame, dots, sep, lab), frame=frame,
                content_top=bar_y - 0.4)


def bubble(text, color, fs=18, buff=0.17):
    """A chat message bubble whose rounded box always surrounds its label.

    Sizing the box from ``label.width/height`` is unreliable for the scaled
    crisp-``Text`` (the glyph metrics don't leave room), so wrap the label with a
    ``SurroundingRectangle`` — that guarantees consistent padding on every side.
    """
    label = fitted_text(text, font_size=fs, color=INK)
    box = SurroundingRectangle(
        label, buff=buff, corner_radius=0.12, color=color, stroke_width=2,
    ).set_fill(color, opacity=0.16)
    return VGroup(box, label)


def mini_tree(highlight=None, color=INK, hcolor=GOOD, scale=1.0):
    """A tiny DOM/VDOM sketch: a root with three leaves. ``highlight`` (0/1/2)
    tints one leaf to mark 'the node that changed'."""
    root = Dot([0, 0.5, 0], radius=0.07, color=color)
    xs = [-0.45, 0.0, 0.45]
    leaves = VGroup()
    edges = VGroup()
    for i, x in enumerate(xs):
        c = hcolor if highlight == i else color
        leaf = Dot([x, -0.35, 0], radius=0.07, color=c)
        edge = Line(root.get_center(), leaf.get_center(),
                    stroke_width=2.5, color=c if highlight == i else MUTED)
        leaves.add(leaf)
        edges.add(edge)
    return VGroup(edges, root, leaves).scale(scale)


def poly_path(points):
    """A VMobject polyline through ``points`` (2- or 3-tuples) — used both to draw
    orthogonal connectors and as a motion path for signal pulses along them."""
    pts = [np.array([p[0], p[1], p[2] if len(p) > 2 else 0.0]) for p in points]
    v = VMobject()
    v.set_points_as_corners(pts)
    return v


def ortho_conn(points, color=FAINT, sw=2.4, tip=True, dashed=False):
    """A right-angle connector through ``points``, with an optional arrow tip.

    ``points`` should already sit on the box edges (right-angle turns only), so the
    diagram reads like an architecture drawing rather than a web of diagonals. The
    tip is a hand-built triangle (plain VMobjects have no ``add_tip``).
    """
    line = poly_path(points)
    line.set_stroke(color, sw)
    if dashed:
        line = DashedVMobject(line, num_dashes=14)
        line.set_stroke(color, sw)
    if not tip:
        return line
    p_last = np.array([points[-1][0], points[-1][1], 0.0])
    p_prev = np.array([points[-2][0], points[-2][1], 0.0])
    d = p_last - p_prev
    nrm = float(np.linalg.norm(d))
    d = d / nrm if nrm > 1e-6 else np.array([1.0, 0.0, 0.0])
    perp = np.array([-d[1], d[0], 0.0])
    s = 0.18
    head = Polygon(
        p_last, p_last - d * 1.7 * s + perp * s, p_last - d * 1.7 * s - perp * s,
        color=color, fill_color=color, fill_opacity=1.0, stroke_width=0,
    )
    return VGroup(line, head)


def lane_panel(x0, x1, y0, y1, color, label):
    """A faint rounded 'swimlane' background with a small bold top-left tag."""
    panel = RoundedRectangle(
        width=x1 - x0, height=y1 - y0, corner_radius=0.18,
        stroke_color=color, stroke_width=2, fill_color=color, fill_opacity=0.05,
    ).move_to([(x0 + x1) / 2, (y0 + y1) / 2, 0])
    tag = Text(label, font_size=17, color=color, weight="BOLD")
    tag.next_to(panel.get_corner(UL), DR, buff=0.16)
    return VGroup(panel, tag)


# ========================================================================== #
class _RCBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # Slow every animation uniformly by stretching its run time (see ANIM_SLOW).
    # NB: self.wait() routes through self.play(Wait(...)), so we must NOT scale
    # those — beats/holds are governed by DELAY, not by the animation slowdown.
    def play(self, *anims, **kwargs):
        is_wait = any(type(a).__name__ == "Wait" for a in anims)
        if not QUICK and anims and not is_wait:
            rt = kwargs.get("run_time")
            if rt is None:
                rts = [r for r in (getattr(a, "run_time", None) for a in anims) if r]
                rt = max(rts) if rts else 1.0
            kwargs["run_time"] = rt * ANIM_SLOW
        return super().play(*anims, **kwargs)

    # ---- timing helpers --------------------------------------------------- #
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.0))

    def reveal(self, items, hold=1.0, run_time=0.5, shift=RIGHT * 0.2):
        for m in items:
            self.play(FadeIn(m, shift=shift), run_time=run_time)
            self.beat(hold)

    def wipe(self, rt=0.7, gap=True):
        if gap and SCENE_GAP:
            self.wait(SCENE_GAP)
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    def section_header(self, label, color=REACT_C):
        txt = Text(label, font_size=34, color=INK, weight="BOLD").to_corner(
            UL, buff=0.5
        )
        line = Line(txt.get_left(), txt.get_right()).next_to(txt, DOWN, buff=0.12)
        line.set_stroke(color=color, width=3)
        return VGroup(txt, line)

    def subtitle(self, header, text, color=MUTED):
        s = Text(text, font_size=25, color=color)
        s.next_to(header, DOWN, buff=0.32).to_edge(LEFT, buff=0.5)
        return s

    # ---- house-style intro / outro cards ---------------------------------- #
    def introduction(self, title1, title2):
        header = fitted_text(
            title1, max_width=11.0, font_size=52, color=INK, weight="BOLD"
        )
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=REACT_C)
        writer = Text("Created by Ptolémé", font_size=28, color=API_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.8)
        sub = fitted_text(title2, max_width=11.5, font_size=34, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.card_wait(2.2)
        return VGroup(header, writer, line)

    def play_intro(self):
        group = self.introduction(
            "React.js & System Design",
            "the frontend framework — then a chatbot, front to back",
        )
        self.play(FadeOut(group), run_time=1.0)
        self.card_wait(0.4)

    def play_outro(self):
        self.card_wait(0.6)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=REACT_C)
        writer = Text("Created by Ptolémé", font_size=28, color=API_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.2)
        self.card_wait(2.6)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.4)
        self.card_wait(0.8)

    # ====================================================================== #
    # Scene 1 — What is React.js?
    # ====================================================================== #
    def scene_whatis(self):
        title = Text("What is React.js?", font_size=46, color=INK, weight="BOLD")
        logo = react_logo(scale=0.62)
        title.to_edge(UP, buff=1.0)
        logo.next_to(title, DOWN, buff=0.55)
        self.play(Write(title), run_time=1.2)
        # spin the atom in as it appears — the React signature
        self.play(FadeIn(logo, scale=0.4), Rotate(logo, 0.6 * TAU), run_time=1.6)
        self.beat(1.0)

        # lift the title/logo up and lay out what it actually is
        self.play(
            title.animate.scale(0.62).to_edge(UP, buff=0.4),
            logo.animate.scale(0.5).to_corner(UR, buff=0.5),
            run_time=0.9,
        )

        rows = [
            ("A JavaScript library for building user interfaces",
             "not a full framework — it does the view layer well", REACT_C),
            ("Declarative",
             "you describe what the UI is for a given state, not the DOM steps",
             ACCENT),
            ("Component-based",
             "build the screen from small, reusable, self-contained pieces",
             GOOD),
        ]
        cards = VGroup()
        for head, note, col in rows:
            h = Text(head, font_size=27, color=col, weight="BOLD")
            n = Text(note, font_size=20, color=MUTED)
            card = VGroup(h, n).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
            cards.add(card)
        cards.arrange(DOWN, aligned_edge=LEFT, buff=0.55).move_to(LEFT * 0.6 + DOWN * 0.4)
        for c in cards:
            self.play(FadeIn(c, shift=RIGHT * 0.25), run_time=0.6)
            self.beat(1.2)

        foot = Text(
            "Created & open-sourced by Meta (2013) — one of the most used UI tools today",
            font_size=20, color=MUTED,
        ).to_edge(DOWN, buff=0.55)
        self.play(FadeIn(foot, shift=UP * 0.2), run_time=0.7)
        self.beat(1.6)
        self.wipe()

    # ====================================================================== #
    # Scene 2 — The UI is a tree of components
    # ====================================================================== #
    def scene_components(self):
        header = self.section_header("Components", REACT_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)
        sub = self.subtitle(header, "the screen is one tree of small, reusable pieces")
        self.play(FadeIn(sub, shift=UP * 0.2), run_time=0.5)

        # --- build a component tree for a chat app ------------------------- #
        App = node_box("<App>", (0, 1.75), REACT_C, w=2.2, h=0.75, fs=22)
        Header = node_box("<Header>", (-4.1, 0.35), MUTED, w=2.3, h=0.7, fs=19)
        Chat = node_box("<ChatWindow>", (0, 0.35), API_C, w=2.7, h=0.7, fs=19)
        Side = node_box("<Sidebar>", (4.0, 0.35), MUTED, w=2.3, h=0.7, fs=19)
        MsgList = node_box("<MessageList>", (-1.7, -1.05), LLM_C, w=2.7, h=0.7, fs=18)
        Composer = node_box("<Composer>", (1.7, -1.05), GOOD, w=2.5, h=0.7, fs=18)
        Msg1 = node_box("<Message/>", (-3.0, -2.35), ACCENT, w=2.2, h=0.65, fs=17)
        Msg2 = node_box("<Message/>", (-0.5, -2.35), ACCENT, w=2.2, h=0.65, fs=17)

        links = [
            (App, Header), (App, Chat), (App, Side),
            (Chat, MsgList), (Chat, Composer),
            (MsgList, Msg1), (MsgList, Msg2),
        ]
        lines = VGroup(*[connector(a, b, color=FAINT, sw=2.5) for a, b in links])

        self.play(FadeIn(App, shift=DOWN * 0.2), run_time=0.6)
        self.beat(0.5)
        self.play(
            LaggedStart(*[Create(lines[i]) for i in range(3)], lag_ratio=0.3),
            LaggedStart(FadeIn(Header), FadeIn(Chat), FadeIn(Side), lag_ratio=0.3),
            run_time=1.3,
        )
        self.beat(0.8)
        self.play(
            LaggedStart(*[Create(lines[i]) for i in range(3, 5)], lag_ratio=0.3),
            LaggedStart(FadeIn(MsgList), FadeIn(Composer), lag_ratio=0.3),
            run_time=1.1,
        )
        self.play(
            LaggedStart(*[Create(lines[i]) for i in range(5, 7)], lag_ratio=0.3),
            LaggedStart(FadeIn(Msg1), FadeIn(Msg2), lag_ratio=0.3),
            run_time=1.1,
        )
        self.beat(1.0)

        # highlight reuse: the same <Message/> component, rendered per line
        self.play(
            Indicate(Msg1, color=ACCENT, scale_factor=1.12),
            Indicate(Msg2, color=ACCENT, scale_factor=1.12),
            run_time=1.1,
        )
        note = Text(
            "one <Message/> component — rendered once per chat line",
            font_size=20, color=ACCENT,
        ).next_to(VGroup(Msg1, Msg2), DOWN, buff=0.4)
        self.play(FadeIn(note, shift=UP * 0.15), run_time=0.7)
        self.beat(1.4)

        # data flow: props down, events up
        pdown = Text("props flow down  ↓", font_size=22, color=REACT_C)
        eup = Text("events bubble up  ↑", font_size=22, color=GOOD)
        flow = VGroup(pdown, eup).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        flow.to_corner(DR, buff=0.6)
        self.play(FadeIn(flow, shift=LEFT * 0.2), run_time=0.7)
        self.beat(1.8)
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Reconciliation: state → Virtual DOM diff → minimal patch
    # ====================================================================== #
    def scene_reconcile(self):
        header = self.section_header("How React updates the screen", REACT_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # --- the pipeline of chips (sits well below the header) ----------- #
        stages = [
            ("setState()", "new state", ACCENT),
            ("re-render", "→ new Virtual DOM", REACT_C),
            ("diff", "vs. previous tree\n(reconciliation)", LLM_C),
            ("patch", "minimal real-DOM\nupdate", GOOD),
        ]
        chips = VGroup()
        for head, note, col in stages:
            h = Text(head, font_size=23, color=col, weight="BOLD")
            n = Text(note, font_size=15, color=MUTED, line_spacing=0.7)
            body = VGroup(h, n).arrange(DOWN, buff=0.12)
            box = RoundedRectangle(
                width=2.75, height=1.25, corner_radius=0.14,
                stroke_color=col, stroke_width=3, fill_color=col, fill_opacity=0.10,
            )
            body.move_to(box)
            chips.add(VGroup(box, body))
        chips.arrange(RIGHT, buff=0.45).move_to(UP * 1.45)
        arrows = VGroup(*[
            harrow(chips[i][0].get_right(), chips[i + 1][0].get_left(), sw=3)
            for i in range(len(chips) - 1)
        ])
        for i, c in enumerate(chips):
            self.play(FadeIn(c, shift=RIGHT * 0.2), run_time=0.5)
            if i < len(arrows):
                self.play(GrowArrow(arrows[i]), run_time=0.4)
            self.beat(0.9)
        self.beat(0.6)

        # --- LEFT: the trees — old vs new, one leaf changed --------------- #
        old = mini_tree(color=MUTED, scale=0.9)
        new = mini_tree(highlight=2, color=MUTED, scale=0.9)
        lo = Text("previous", font_size=15, color=MUTED)
        ln = Text("next", font_size=15, color=INK)
        oldg = VGroup(old, lo).arrange(DOWN, buff=0.16)
        newg = VGroup(new, ln).arrange(DOWN, buff=0.16)
        trees = VGroup(oldg, newg).arrange(RIGHT, buff=0.95)
        trees.move_to([-3.7, -0.55, 0])
        vs = Text("≠", font_size=28, color=LLM_C).move_to(trees.get_center())
        self.play(FadeIn(oldg), FadeIn(newg), run_time=0.7)
        self.play(Write(vs), run_time=0.4)
        self.play(Indicate(new[2][2], color=GOOD, scale_factor=1.6), run_time=1.0)
        self.beat(0.8)

        # --- RIGHT: the browser — only the new node is inserted ----------- #
        br = browser(w=4.3, h=2.55, title="chat")
        br["group"].move_to([3.4, -0.72, 0])
        frame = br["frame"]
        b1 = bubble("Hi!", API_C, fs=15)
        b2 = bubble("How can I help?", REACT_C, fs=15)
        lines_old = VGroup(b1, b2).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        # Position from the frame's ACTUAL top (it has already been moved);
        # br["content_top"] is measured at the origin and would place the first
        # bubble above the title bar once the browser is repositioned.
        inside_top = frame.get_top()[1] - 0.62
        lines_old.align_to([0, inside_top, 0], UP)
        lines_old.align_to([frame.get_left()[0] + 0.30, 0, 0], LEFT)
        self.play(FadeIn(br["group"]), run_time=0.7)
        self.play(FadeIn(lines_old), run_time=0.5)
        self.beat(0.8)

        newline = bubble("What's Docling?", GOOD, fs=15)
        newline.next_to(b2, DOWN, aligned_edge=LEFT, buff=0.16)
        self.play(Indicate(chips[3], color=GOOD, scale_factor=1.06), run_time=0.6)
        self.play(FadeIn(newline, shift=UP * 0.2), run_time=0.6)
        self.play(Indicate(newline, color=GOOD, scale_factor=1.1), run_time=0.9)
        self.play(lines_old.animate.set_opacity(0.4), run_time=0.5)
        self.beat(1.0)

        # --- hooks (under the trees) + the declarative punchline ---------- #
        hooks = VGroup(
            chip("useState → state", ACCENT, w=3.2, h=0.6, fs=17),
            chip("useEffect → side effects", REACT_C, w=3.2, h=0.6, fs=17),
        ).arrange(DOWN, buff=0.16)
        hooks.move_to([-3.7, -2.15, 0])
        self.play(FadeIn(hooks, shift=UP * 0.2), run_time=0.7)
        self.beat(1.0)
        key = Text("You set the state; React figures out the DOM.",
                   font_size=24, color=ACCENT).to_edge(DOWN, buff=0.35)
        self.play(Write(key), run_time=1.2)
        self.beat(1.6)
        self.wipe()

    # ====================================================================== #
    # Scene 4 — What React is used for
    # ====================================================================== #
    def scene_usedfor(self):
        header = self.section_header("What React is used for", REACT_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        uses = [
            ("Single-page apps", "one page, no full reloads", REACT_C),
            ("Dashboards & data apps", "live, interactive views", API_C),
            ("Chat & realtime UIs", "streaming, updating state", GOOD),
            ("Design systems", "shared component libraries", LLM_C),
        ]
        cards = VGroup()
        for head, note, col in uses:
            h = Text(head, font_size=24, color=col, weight="BOLD")
            n = Text(note, font_size=18, color=MUTED)
            body = VGroup(h, n).arrange(DOWN, buff=0.12)
            box = RoundedRectangle(
                width=5.2, height=1.35, corner_radius=0.16,
                stroke_color=col, stroke_width=3, fill_color=col, fill_opacity=0.10,
            )
            body.move_to(box)
            cards.add(VGroup(box, body))
        cards.arrange_in_grid(rows=2, cols=2, buff=(0.55, 0.55)).move_to(UP * 0.7)
        self.play(
            LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in cards],
                        lag_ratio=0.25),
            run_time=1.8,
        )
        self.beat(1.6)

        eco_title = Text("and a huge ecosystem", font_size=20, color=MUTED)
        eco = VGroup(
            chip("Next.js — routing & SSR", API_C, w=4.1, h=0.7, fs=18),
            chip("React Native — mobile", GOOD, w=3.9, h=0.7, fs=18),
            chip("npm — thousands of components", ACCENT, w=4.9, h=0.7, fs=18),
        ).arrange(RIGHT, buff=0.35)
        block = VGroup(eco_title, eco).arrange(DOWN, buff=0.25)
        block.next_to(cards, DOWN, buff=0.55)
        self.play(FadeIn(eco_title), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.15) for c in eco],
                              lag_ratio=0.3), run_time=1.3)
        self.beat(1.6)

        bridge = Text(
            "So a chatbot's frontend is React — now let's design the whole system →",
            font_size=24, color=ACCENT,
        ).to_edge(DOWN, buff=0.45)
        self.play(Write(bridge), run_time=1.4)
        self.beat(2.0)
        self.wipe()

    # ====================================================================== #
    # Part B — the chatbot system.  Shared architecture builder + two flows.
    # ====================================================================== #
    def _build_arch(self):
        """Construct (but do not add) the swimlane diagram: two lanes (online chat /
        offline ingestion) sharing a storage band, with right-angle connectors and
        directional arrows. Returns nodes, connector mobjects, pulse routes, lanes.
        """
        W, H = 2.35, 0.8
        spec = {
            # online lane (top)
            "USER":   ((-5.0, 1.95), "User", "browser", MUTED),
            "FE":     ((-2.4, 1.95), "Frontend", "React.js", REACT_C),
            "API":    (( 0.2, 1.95), "Backend API", "FastAPI", API_C),
            "LLM":    (( 2.8, 1.95), "LLM", "streamed", LLM_C),
            # shared storage band (middle)
            "OBS":    ((-2.4, 0.35), "Observability", "traces · cost", OBS_C),
            "VEC":    (( 0.2, 0.35), "Vector store", "embeddings", DB_C),
            "DB":     (( 2.8, 0.35), "Database", "Postgres", DB_C),
            # offline ingestion lane (bottom)
            "DATA":   ((-5.0, -1.25), "Data service", "Python", OCR_C),
            "CELERY": ((-2.4, -1.25), "Celery", "workers", WORK_C),
            "DOCLING":(( 0.2, -1.25), "Docling", "OCR → text", OCR_C),
        }
        nodes = {
            k: node_box(t, c, col, sub=s, w=W, h=H, fs=20, subfs=14)
            for k, (c, t, s, col) in spec.items()
        }
        rect = {k: nodes[k][0] for k in nodes}
        GAP = 1.0  # empty routing channel between the online lane and storage band

        def top(k):  return rect[k].get_top()
        def bot(k):  return rect[k].get_bottom()
        def lft(k):  return rect[k].get_left()
        def rgt(k):  return rect[k].get_right()
        def botx(k, dx):
            b = rect[k].get_bottom(); return [b[0] + dx, b[1], 0]

        # every segment is horizontal or vertical (right-angle turns only)
        routes = {
            ("USER", "FE"):       [rgt("USER"), lft("FE")],
            ("FE", "API"):        [rgt("FE"), lft("API")],
            ("API", "LLM"):       [rgt("API"), lft("LLM")],
            ("API", "VEC"):       [botx("API", 0.0), top("VEC")],
            ("DOCLING", "VEC"):   [top("DOCLING"), bot("VEC")],
            ("DATA", "CELERY"):   [rgt("DATA"), lft("CELERY")],
            ("CELERY", "DOCLING"): [rgt("CELERY"), lft("DOCLING")],
            ("API", "DB"):        [botx("API", 0.55), [botx("API", 0.55)[0], GAP],
                                   [top("DB")[0], GAP], top("DB")],
            ("API", "OBS"):       [botx("API", -0.55), [botx("API", -0.55)[0], GAP],
                                   [top("OBS")[0], GAP], top("OBS")],
            ("CELERY", "OBS"):    [top("CELERY"), bot("OBS")],
        }
        conns = {}
        for key, pts in routes.items():
            dashed = key[1] == "OBS"  # telemetry taps: dashed, no arrowhead
            conns[key] = ortho_conn(pts, color=FAINT, sw=2.4,
                                    tip=not dashed, dashed=dashed)

        lanes = {
            "online": lane_panel(-6.45, 4.15, 1.25, 2.78, REACT_C, "ONLINE · chat"),
            "offline": lane_panel(-6.45, 1.55, -2.05, -0.52, OCR_C,
                                  "OFFLINE · ingestion"),
        }
        return dict(nodes=nodes, conns=conns, routes=routes, lanes=lanes)

    def _ensure_arch(self):
        """For standalone renders: build + add the diagram instantly."""
        if getattr(self, "_nodes", None):
            return
        arch = self._build_arch()
        self._nodes = arch["nodes"]
        self._conns = arch["conns"]
        self._routes = arch["routes"]
        self.add(arch["lanes"]["online"], arch["lanes"]["offline"])
        self.add(*arch["conns"].values(), *arch["nodes"].values())

    # ---- animated signal along a connector -------------------------------- #
    def send(self, s, d, color, n=1, rt=0.9, lag=0.22, radius=0.09, flash=True):
        pts = self._routes.get((s, d))
        if pts is None:  # a return trip (e.g. VEC→API): walk the wire backwards
            pts = list(reversed(self._routes[(d, s)]))
        path = poly_path(pts)
        start = path.get_start()
        dots = VGroup()
        for _ in range(max(1, n)):
            halo = Dot(start, radius=radius * 2.0, color=color).set_opacity(0.22)
            core = Dot(start, radius=radius, color=color)
            dots.add(VGroup(halo, core))
        self.add(dots)
        if n == 1:
            anims = [MoveAlongPath(dots[0], path)]
            if flash:
                anims.append(ShowPassingFlash(
                    path.copy().set_stroke(color, 6), time_width=0.6))
            self.play(*anims, run_time=rt)
        else:
            self.play(LaggedStart(*[MoveAlongPath(x, path) for x in dots],
                                  lag_ratio=lag), run_time=rt)
        # remove the pulse dots thoroughly (parent group + every halo/core), so
        # none linger on the wires after the signal has passed
        self.remove(dots)
        for grp in list(dots):
            self.remove(grp, *grp.submobjects)

    def caption(self, text, color=INK, rt=0.5):
        new = fitted_text(text, max_width=12.5, font_size=24, color=color)
        new.to_edge(DOWN, buff=0.35)
        if getattr(self, "_cap", None) is not None:
            self.play(FadeOut(self._cap, shift=DOWN * 0.1),
                      FadeIn(new, shift=UP * 0.1), run_time=rt)
        else:
            self.play(FadeIn(new, shift=UP * 0.1), run_time=rt)
        self._cap = new

    # ====================================================================== #
    # Scene 5 — the architecture
    # ====================================================================== #
    def scene_architecture(self, keep=False):
        header = self.section_header("A chatbot, front to back", REACT_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        arch = self._build_arch()
        n, c = arch["nodes"], arch["conns"]
        self._nodes, self._conns, self._routes = n, c, arch["routes"]
        online_lane, offline_lane = arch["lanes"]["online"], arch["lanes"]["offline"]

        def show(node_keys, conn_keys, cap, cap_col=MUTED, hold=1.0, extra=None):
            anims = [FadeIn(n[k], shift=UP * 0.12) for k in node_keys]
            anims += [Create(c[k]) for k in conn_keys]
            if extra:
                anims += extra
            self.play(*anims, run_time=0.9)
            if cap:
                self.caption(cap, color=cap_col)
            self.beat(hold)

        # --- the online lane: the chat request path ----------------------- #
        self.play(FadeIn(online_lane), run_time=0.6)
        show(["USER", "FE", "API", "LLM"],
             [("USER", "FE"), ("FE", "API"), ("API", "LLM")],
             "online: the browser → React → a Python API → the LLM", REACT_C,
             hold=1.3)

        # --- the shared storage the API uses ------------------------------ #
        show(["VEC", "DB"], [("API", "VEC"), ("API", "DB")],
             "the API retrieves context and saves the session", DB_C, hold=1.3)

        # --- the offline lane: async ingestion ---------------------------- #
        self.play(FadeIn(offline_lane), run_time=0.6)
        show(["DATA", "CELERY", "DOCLING"],
             [("DATA", "CELERY"), ("CELERY", "DOCLING")],
             "offline: a separate async pipeline ingests documents", OCR_C, hold=1.3)

        # --- the one place the two planes meet ---------------------------- #
        show([], [("DOCLING", "VEC")],
             "the two planes meet only at the vector store", ACCENT, hold=1.0)
        self.play(Indicate(n["VEC"], color=ACCENT, scale_factor=1.1), run_time=0.9)
        self.beat(0.6)

        # --- observability is cross-cutting ------------------------------- #
        show(["OBS"], [("API", "OBS"), ("CELERY", "OBS")],
             "observability is cross-cutting (traces · tokens · cost)", OBS_C,
             hold=1.6)

        self.play(FadeOut(self._cap), run_time=0.4)
        self._cap = None
        if not keep:
            self.wipe()

    # ====================================================================== #
    # Scene 6 — the two flows
    # ====================================================================== #
    def scene_flows(self):
        standalone = not getattr(self, "_nodes", None)
        if standalone:
            header = self.section_header("A chatbot, front to back", REACT_C)
            self.add(header)
            self._ensure_arch()
        n = self._nodes

        # ---- Flow 1: ingestion (offline / async) -------------------------- #
        badge = self._flow_badge("1", "Ingestion  ·  offline, async", OCR_C)
        self.play(FadeIn(badge, shift=DOWN * 0.15), run_time=0.6)

        # a PDF drops into the ingestion lane
        dtop = n["DATA"][0].get_top()
        up = Arrow([dtop[0], dtop[1] + 0.7, 0], [dtop[0], dtop[1] + 0.06, 0],
                   buff=0, color=OCR_C, stroke_width=5,
                   max_tip_length_to_length_ratio=0.35, tip_length=0.16)
        pdf = Text("PDF", font_size=16, color=OCR_C).next_to(up, UP, buff=0.06)
        self.caption("a document is uploaded for ingestion", OCR_C)
        self.play(FadeIn(pdf, shift=DOWN * 0.15), GrowArrow(up), run_time=0.7)
        self.play(Indicate(n["DATA"], color=OCR_C, scale_factor=1.07), run_time=0.7)

        self.caption("the data-service enqueues Celery tasks (async queue)", WORK_C)
        self.send("DATA", "CELERY", WORK_C, n=3, rt=1.4, lag=0.25)

        self.caption("a worker runs Docling — OCR turns the PDF into clean text",
                     OCR_C)
        self.send("CELERY", "DOCLING", WORK_C, rt=0.9)
        self.play(Indicate(n["DOCLING"], color=OCR_C, scale_factor=1.08), run_time=0.9)

        self.caption("chunk · embed · index into the vector store", DB_C)
        self.send("DOCLING", "VEC", OCR_C, n=3, rt=1.3, lag=0.22)
        self.play(Indicate(n["VEC"], color=DB_C, scale_factor=1.07), run_time=0.7)
        self.send("CELERY", "OBS", OBS_C, rt=0.9, flash=False)
        self.beat(0.6)

        key1 = fitted_text("heavy work runs in the background — the chat stays fast",
                           max_width=7.5, font_size=21, color=ACCENT)
        key1.next_to(badge, DOWN, buff=0.28).to_edge(RIGHT, buff=0.5)
        self.play(FadeIn(key1, shift=LEFT * 0.2), run_time=0.7)
        self.beat(1.6)
        self.play(FadeOut(key1), FadeOut(badge), FadeOut(up), FadeOut(pdf),
                  run_time=0.5)

        # ---- Flow 2: chat (online / streaming) ---------------------------- #
        badge = self._flow_badge("2", "Chat  ·  online, streaming", REACT_C)
        self.play(FadeIn(badge, shift=DOWN * 0.15), run_time=0.6)

        self.caption("you ask a question", REACT_C)
        self.send("USER", "FE", MUTED, rt=0.6)
        self.send("FE", "API", REACT_C, rt=0.8)

        self.caption("retrieve the most relevant chunks  (RAG)", DB_C)
        self.send("API", "VEC", API_C, rt=0.8)
        self.send("VEC", "API", DB_C, rt=0.8)

        self.caption("prompt + retrieved context  →  the LLM", LLM_C)
        self.send("API", "LLM", API_C, rt=0.8)
        self.play(Indicate(n["LLM"], color=LLM_C, scale_factor=1.08), run_time=0.9)

        self.caption("tokens stream back to the browser, live", REACT_C)
        self.send("LLM", "API", LLM_C, n=6, rt=1.4, lag=0.16)
        self.send("API", "FE", REACT_C, n=6, rt=1.4, lag=0.16)
        self.play(Indicate(n["FE"], color=REACT_C, scale_factor=1.08), run_time=0.8)
        self.beat(0.4)

        self.caption("save the session & messages", DB_C)
        self.send("API", "DB", DB_C, rt=0.8)
        self.play(Indicate(n["DB"], color=DB_C, scale_factor=1.07), run_time=0.6)

        self.caption("trace latency, tokens & cost", OBS_C)
        self.send("API", "OBS", OBS_C, rt=0.9, flash=False)
        self.play(Indicate(n["OBS"], color=OBS_C, scale_factor=1.07), run_time=0.6)

        self.play(FadeOut(self._cap), FadeOut(badge), run_time=0.4)
        self._cap = None
        key2 = Text("retrieve  →  generate  →  stream  →  persist  →  observe",
                    font_size=24, color=ACCENT).to_edge(DOWN, buff=0.4)
        self.play(Write(key2), run_time=1.4)
        self.beat(2.0)
        self.wipe()

    def _flow_badge(self, num, label, color):
        num_c = VGroup(
            Circle(radius=0.24, color=color, fill_color=color, fill_opacity=0.9),
            Text(num, font_size=24, color=BG, weight="BOLD"),
        )
        txt = Text(label, font_size=24, color=color, weight="BOLD")
        badge = VGroup(num_c, txt).arrange(RIGHT, buff=0.25)
        badge.to_corner(UR, buff=0.5)
        return badge

    # ---- the whole film --------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_whatis()
        self.scene_components()
        self.scene_reconcile()
        self.scene_usedfor()
        self.scene_architecture(keep=True)
        self.scene_flows()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_RCBase):
    def construct(self):
        self.play_intro()


class WhatIs(_RCBase):
    def construct(self):
        self.scene_whatis()


class Components(_RCBase):
    def construct(self):
        self.scene_components()


class Reconcile(_RCBase):
    def construct(self):
        self.scene_reconcile()


class UsedFor(_RCBase):
    def construct(self):
        self.scene_usedfor()


class Architecture(_RCBase):
    def construct(self):
        self.scene_architecture()


class Flows(_RCBase):
    def construct(self):
        self.scene_flows()


class Outro(_RCBase):
    def construct(self):
        self.play_outro()


class ReactChatbot(_RCBase):
    """The whole ~3-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    ReactChatbot().render()

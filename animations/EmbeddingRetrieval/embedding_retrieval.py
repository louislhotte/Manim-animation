"""Embeddings & Retrieval — a ~5-minute explainer, house-style.

How a chunk of text becomes a point in a latent space, and how vector
retrievers (OpenSearch, Azure AI Search, pgvector) find the right chunks by
*similarity* — the machinery behind RAG.

Six roughly one-minute scenes:

    1. Search by meaning   -- keyword search misses meaning; the roadmap
    2. From chunk to vector-- chunking → embedding model → a point in space
    3. The geometry of it  -- latent space, clusters, cosine similarity
    4. Retrieval           -- a query → nearest-neighbour search → top-k
    5. The retrievers      -- OpenSearch · Azure AI Search · pgvector (ANN/HNSW)
    6. Why it matters (RAG)-- retrieved chunks become the model's context

Bookended by the channel's intro card and the "Thank you for watching!" outro
(matches animations/HarnessEngineering/harness_engineering.py).

Everything uses ``Text`` (Pango) rather than ``Tex`` so it renders without a
LaTeX install and stays fast to iterate on.

Scenes are exposed both individually (``Problem``, ``Embed``, ``Space``,
``Retrieve``, ``Systems``, ``Why``, ``Intro``, ``Outro``) and as one continuous
film (``EmbeddingRetrieval``).

Env knobs:
    EMB_QUICK=1   shorten every hold for a fast sanity render
"""

from __future__ import annotations

import os

import numpy as np
from manim import *

# --- crisp text ------------------------------------------------------------ #
# Manim's ``Text`` quantises glyph positions badly at small font sizes, so body
# text below ~20 pt comes out with uneven letter/word spacing ("card iac ar rest").
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


QUICK = os.environ.get("EMB_QUICK") == "1"
# Single knob for pacing: every on-screen "hold" is scaled by this. QUICK
# collapses the holds for fast iteration; otherwise it sets the reading rhythm.
# The intro/outro cards use a fixed rhythm (card_wait) so they stay crisp.
# 2.7 gives a slow, readable cadence (~+8-13 s per scene vs. the old 1.6).
DELAY = 0.3 if QUICK else 2.7
# Slow every played animation to 80% speed (i.e. 25% longer) so motion doesn't
# feel rushed. QUICK keeps full speed for fast iteration.
ANIM_SLOW = 1.0 if QUICK else 1.25
# Beat held on the finished scene before it wipes to the next one.
SCENE_GAP = 0.0 if QUICK else 5.0

# ---- palette -------------------------------------------------------------- #
BG = "#0E1117"  # dark slate background
PANEL = "#151A23"  # latent-space panel fill
INK = "#F5F3EF"  # warm white text
MUTED = "#8A93A6"  # secondary text / arrows
FAINT = "#3A4152"  # gridlines
MODEL_C = "#FFD166"  # the embedding model (gold)
VEC_C = "#FFD166"  # a vector (gold)
QUERY_C = "#FF6FB5"  # the query (pink)
MED_C = "#2EC4B6"  # topic cluster: medical (teal)
FIN_C = "#5B8DEF"  # topic cluster: finance (blue)
COOK_C = "#FF8C42"  # topic cluster: cooking (orange)
GOOD = "#3DD68C"  # match / green
BAD = "#FF5C5C"  # miss / red
ACCENT = "#FFD166"

# ---- the tiny corpus used across scenes ----------------------------------- #
# (text, topic, normalised [-1,1]^2 position). Positions are hand-placed so the
# three clusters read cleanly and — crucially — the medical points are spread
# far enough apart that the query's k-NN rings/labels never pile on top of
# each other. The query sits just inside the medical triangle.
CHUNKS = [
    ("Aspirin is given after a heart attack", "med", (-0.60, 0.24)),
    ("Myocardial infarction: chest-pain triage", "med", (-0.30, 0.44)),
    ("CPR restores flow during cardiac arrest", "med", (-0.18, 0.08)),
    ("Diversify a portfolio to lower risk", "fin", (0.42, 0.50)),
    ("Rising rates push bond prices down", "fin", (0.78, 0.28)),
    ("Compound interest grows your savings", "fin", (0.55, -0.02)),
    ("Sear the steak over very high heat", "cook", (0.10, -0.55)),
    ("Whisk the eggs before folding in flour", "cook", (0.44, -0.78)),
    ("Simmer the tomato sauce for twenty minutes", "cook", (-0.14, -0.40)),
]
TCOLOR = {"med": MED_C, "fin": FIN_C, "cook": COOK_C}
TCENTER = {"med": (-0.55, 0.48), "fin": (0.62, 0.5), "cook": (0.08, -0.62)}
# The query lands inside the medical triangle (semantically "heart attack"),
# closest to chunk 0 (Aspirin), then 1 (Myocardial), then 2 (CPR).
QUERY_NORM = (-0.46, 0.26)
QUERY_TEXT = "What do I do during a heart attack?"


def layout_points():
    """The hand-placed normalised ([-1,1]^2) positions, index-aligned to CHUNKS."""
    return [(x, y, topic, text) for (text, topic, (x, y)) in CHUNKS]


# ---- small reusable pieces ------------------------------------------------ #
def fitted_text(text, max_width=None, font_size=26, **kw):
    """A crisp ``Text`` shrunk to fit ``max_width``. ``Text`` is the crisp wrapper
    (renders at a large base, scales down), so shrinking further to fit keeps the
    spacing correct.
    """
    t = Text(text, font_size=font_size, **kw)
    if max_width is not None and t.width > max_width:
        t.scale(max_width / t.width)
    return t


def chip(text, color, w=2.3, h=0.95, fs=26, fill=0.12, tcolor=None, radius=0.14):
    """A rounded, tinted box with a centered auto-fitting label. grp[0] is the box."""
    box = RoundedRectangle(
        width=w,
        height=h,
        corner_radius=radius,
        stroke_color=color,
        stroke_width=3,
        fill_color=color,
        fill_opacity=fill,
    )
    label = fitted_text(text, max_width=w - 0.35, font_size=fs, color=tcolor or INK)
    label.move_to(box)
    return VGroup(box, label)


def harrow(start, end, color=MUTED, sw=4):
    return Arrow(
        start,
        end,
        buff=0.12,
        stroke_width=sw,
        color=color,
        max_tip_length_to_length_ratio=0.16,
        tip_length=0.22,
    )


def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [
            np.array([-0.2, 0.0, 0]),
            np.array([-0.05, -0.18, 0]),
            np.array([0.24, 0.22, 0]),
        ]
    )
    v.set_stroke(color=color, width=sw)
    return v.scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.18, -0.18, 0], [0.18, 0.18, 0])
    b = Line([-0.18, 0.18, 0], [0.18, -0.18, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


def dot_label(text, color, fs=25):
    """A color dot + label row (for legends)."""
    d = Dot(radius=0.09, color=color)
    t = Text(text, font_size=fs, color=INK).next_to(d, RIGHT, buff=0.22)
    return VGroup(d, t)


def vector_row(values, color=VEC_C, fs=26):
    """A bracketed row of floats — the visual shorthand for 'a vector'."""
    body = "   ".join(f"{v:+.2f}" for v in values)
    return Text(f"[  {body}   …  ]", font_size=fs, color=color)


def doc_glyph(w=1.9, h=2.5, color=MUTED, n_lines=7):
    """A little 'document': a page with text lines."""
    page = RoundedRectangle(
        width=w,
        height=h,
        corner_radius=0.08,
        stroke_color=color,
        stroke_width=2.5,
        fill_color=PANEL,
        fill_opacity=0.7,
    )
    lines = VGroup()
    top = page.get_top()[1] - 0.28
    for i in range(n_lines):
        y = top - i * (h - 0.5) / (n_lines - 1)
        ln = Line(
            [page.get_left()[0] + 0.22, y, 0],
            [page.get_right()[0] - (0.22 if i % 3 else 0.7), y, 0],
        )
        ln.set_stroke(MUTED, 3).set_opacity(0.55)
        lines.add(ln)
    return VGroup(page, lines)


def encoder(w=2.6, h=1.9, color=MODEL_C):
    """A stylised encoder: a box holding a small 3-column network (many→few)."""
    box = RoundedRectangle(
        width=w,
        height=h,
        corner_radius=0.16,
        stroke_color=color,
        stroke_width=3,
        fill_color=color,
        fill_opacity=0.10,
    )
    cols = [5, 4, 3]
    xs = np.linspace(-w * 0.27, w * 0.27, len(cols))
    layers = []
    for c, x in zip(cols, xs, strict=False):
        ys = np.linspace(h * 0.26, -h * 0.26, c)
        layers.append(VGroup(*[Dot([x, y, 0], radius=0.05, color=color) for y in ys]))
    edges = VGroup()
    for a, b in zip(layers[:-1], layers[1:], strict=False):
        for da in a:
            for db in b:
                edges.add(
                    Line(
                        da.get_center(),
                        db.get_center(),
                        stroke_width=1,
                        stroke_color=color,
                    ).set_opacity(0.22)
                )
    net = VGroup(edges, *layers)
    return dict(group=VGroup(box, net), box=box, net=net)


def latent_panel(w=6.4, h=5.3, center=ORIGIN, color=MUTED):
    """A titled 2-D 'latent space' panel with faint axes. Returns dict + placer."""
    panel = RoundedRectangle(
        width=w,
        height=h,
        corner_radius=0.22,
        stroke_color=color,
        stroke_width=2.5,
        fill_color=PANEL,
        fill_opacity=0.55,
    ).move_to(center)
    ax = Line(panel.get_left() + RIGHT * 0.35, panel.get_right() + LEFT * 0.35)
    ay = Line(panel.get_bottom() + UP * 0.35, panel.get_top() + DOWN * 0.35)
    for a in (ax, ay):
        a.set_stroke(FAINT, 1.5)
    ax.set_y(center[1])
    ay.set_x(center[0])
    axes = VGroup(ax, ay)

    pad = 0.84
    hw, hh = w / 2 * pad, h / 2 * pad

    def place(nx, ny):
        return np.array([center[0] + nx * hw, center[1] + ny * hh, 0])

    return dict(panel=panel, axes=axes, place=place, center=np.array(center))


def angle_arc(pc, p1, p2, radius=0.9, color=INK, sw=3):
    """A small arc marking the angle between (p1-pc) and (p2-pc)."""
    a1 = float(np.arctan2(p1[1] - pc[1], p1[0] - pc[0]))
    a2 = float(np.arctan2(p2[1] - pc[1], p2[0] - pc[0]))
    d = (a2 - a1 + np.pi) % (2 * np.pi) - np.pi  # signed, shortest
    return Arc(
        radius=radius,
        start_angle=a1,
        angle=d,
        arc_center=pc,
        color=color,
        stroke_width=sw,
    )


# ========================================================================== #
class _EmbBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # Slow every animation uniformly by stretching its run time (see ANIM_SLOW).
    # Works whether the run time is passed to .play() or carried on the animation
    # itself (e.g. LaggedStart(..., run_time=…), Circumscribe(..., run_time=…)).
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

    def reveal(self, items, hold=1.5, run_time=0.5, shift=RIGHT * 0.2):
        for m in items:
            self.play(FadeIn(m, shift=shift), run_time=run_time)
            self.beat(hold)

    def wipe(self, rt=0.7, gap=True):
        # Hold the finished scene for SCENE_GAP seconds (so it can be read) before
        # clearing to the next one. gap=False for mid-scene clears.
        if gap and SCENE_GAP:
            self.wait(SCENE_GAP)
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    def section_header(self, label, color=INK):
        txt = Text(label, font_size=34, color=INK, weight="BOLD").to_corner(
            UL, buff=0.5
        )
        line = Line(txt.get_left(), txt.get_right()).next_to(txt, DOWN, buff=0.12)
        line.set_stroke(color=color, width=3)
        return VGroup(txt, line)

    def subtitle(self, header, text):
        s = Text(text, font_size=26, color=MUTED)
        s.next_to(header, DOWN, buff=0.35).to_edge(LEFT, buff=0.5)
        return s

    # ---- house-style intro / outro cards ---------------------------------- #
    def introduction(self, title1, title2):
        header = fitted_text(
            title1, max_width=10.5, font_size=52, color=INK, weight="BOLD"
        )
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=VEC_C)
        writer = Text("Created by Ptolémé", font_size=28, color=FIN_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.8)
        sub = Text(title2, font_size=36, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.card_wait(2.4)
        return VGroup(header, writer, line)

    def play_intro(self):
        group = self.introduction(
            "Embeddings & Retrieval",
            "chunk → vector → nearest-neighbour search",
        )
        self.play(FadeOut(group), run_time=1.0)
        self.card_wait(0.4)

    def play_outro(self):
        self.card_wait(0.6)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=VEC_C)
        writer = Text("Created by Ptolémé", font_size=28, color=FIN_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.2)
        self.card_wait(2.6)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.4)
        self.card_wait(0.8)

    # ---- a reusable cluster scatter for the latent panel ------------------ #
    def scatter(self, place, radius=0.11):
        """Return dict: dots (VGroup, index-aligned to CHUNKS), positions, meta."""
        pts = layout_points()
        dots, positions, meta = VGroup(), [], []
        for nx, ny, topic, text in pts:
            p = place(nx, ny)
            d = Dot(p, radius=radius, color=TCOLOR[topic])
            d.set_stroke(INK, 1, opacity=0.35)
            dots.add(d)
            positions.append(p)
            meta.append((topic, text))
        return dict(dots=dots, positions=positions, meta=meta)

    # ====================================================================== #
    # Scene 1 — Search by meaning, not by words
    # ====================================================================== #
    def scene_problem(self):
        title = Text(
            "How does a machine search by meaning?",
            font_size=44,
            color=INK,
            weight="BOLD",
        )
        self.play(Write(title), run_time=1.5)
        self.beat(1.0)
        # Re-render smaller (don't .scale() a Text — that distorts the spacing).
        title_small = Text(
            "How does a machine search by meaning?",
            font_size=27,
            color=INK,
            weight="BOLD",
        ).to_edge(UP, buff=0.4)
        self.play(ReplacementTransform(title, title_small), run_time=0.8)
        title = title_small

        # --- the query vs. a passage that never shares its words ----------- #
        q = chip("“heart attack”", QUERY_C, w=3.2, h=0.95, fs=27)
        q.next_to(title, DOWN, buff=0.7).to_edge(LEFT, buff=1.1)
        passage = VGroup(
            Text("a stored document says:", font_size=20, color=MUTED),
            Text("“…treatment for acute", font_size=24, color=INK),
            Text("myocardial infarction…”", font_size=24, color=INK),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        pbox = SurroundingRectangle(passage, buff=0.3, color=MED_C, corner_radius=0.12)
        pbox.set_stroke(width=2)
        passage_g = (
            VGroup(pbox, passage)
            .next_to(title, DOWN, buff=0.55)
            .to_edge(RIGHT, buff=1.1)
        )
        self.play(FadeIn(q, shift=RIGHT * 0.2), run_time=0.6)
        self.play(FadeIn(passage_g, shift=LEFT * 0.2), run_time=0.7)
        self.beat(1.3)

        # --- two ways to search, two verdicts ------------------------------ #
        def verdict(name, note, ok, color):
            head = Text(name, font_size=25, color=color, weight="BOLD")
            desc = Text(note, font_size=21, color=MUTED)
            mark = (make_tick if ok else make_cross)(scale=1.3)
            body = VGroup(desc, mark).arrange(RIGHT, buff=0.3)
            return VGroup(head, body).arrange(DOWN, aligned_edge=LEFT, buff=0.18)

        kw = verdict(
            "Keyword search  (BM25)", "no shared words  →  misses it", False, BAD
        )
        sem = verdict("Semantic search", "same meaning  →  finds it", True, GOOD)
        rows = VGroup(kw, sem).arrange(DOWN, aligned_edge=LEFT, buff=0.6)
        rows.next_to(q, DOWN, buff=0.9).to_edge(LEFT, buff=1.1)
        self.play(FadeIn(kw, shift=UP * 0.2), run_time=0.7)
        self.beat(1.6)
        self.play(FadeIn(sem, shift=UP * 0.2), run_time=0.7)
        self.beat(1.8)

        key = Text(
            "The trick: turn text into vectors that capture meaning.",
            font_size=27,
            color=ACCENT,
        ).to_edge(DOWN, buff=0.7)
        self.play(Write(key), run_time=1.4)
        self.beat(2.0)
        self.wipe(gap=False)  # mid-scene clear — no long hold

        # --- the roadmap: an offline pipeline that builds a searchable index #
        road_title = Text(
            "The pipeline", font_size=34, color=INK, weight="BOLD"
        ).to_edge(UP, buff=0.5)
        self.play(FadeIn(road_title, shift=DOWN * 0.2), run_time=0.6)
        stages = [
            ("Documents", MUTED),
            ("Chunks", INK),
            ("Embedding\nmodel", MODEL_C),
            ("Vectors", VEC_C),
            ("Vector\nindex", MED_C),
        ]
        boxes = VGroup(*[chip(t, c, w=2.0, h=1.15, fs=22) for t, c in stages])
        boxes.arrange(RIGHT, buff=0.7).move_to(UP * 0.5)
        arrows = VGroup(
            *[
                harrow(boxes[i].get_right(), boxes[i + 1].get_left(), sw=3)
                for i in range(len(boxes) - 1)
            ]
        )
        self.reveal(boxes, hold=0.5, run_time=0.4, shift=UP * 0.15)
        self.play(
            LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.3, run_time=1.6)
        )
        self.beat(1.0)

        offline = Text(
            "done once, offline — build the index", font_size=22, color=MUTED
        )
        offline.next_to(boxes, DOWN, buff=0.7)
        brace = Line(
            boxes[0].get_bottom() + DOWN * 0.2, boxes[-1].get_bottom() + DOWN * 0.2
        )
        brace.set_stroke(MUTED, 2).next_to(offline, UP, buff=0.18)
        self.play(Create(brace), FadeIn(offline), run_time=0.9)
        self.beat(1.4)
        online = Text(
            "then, at query time, we search it by similarity  →",
            font_size=24,
            color=QUERY_C,
        ).to_edge(DOWN, buff=0.7)
        self.play(FadeIn(online, shift=UP * 0.2), run_time=0.8)
        self.play(Indicate(boxes[-1], color=MED_C, scale_factor=1.08), run_time=0.9)
        self.beat(1.8)
        self.wipe()

    # ====================================================================== #
    # Scene 2 — From chunk to vector
    # ====================================================================== #
    def scene_embed(self):
        header = self.section_header("1 · From chunk to vector", MODEL_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)
        sub = self.subtitle(header, "Split the text, then embed each piece")
        self.play(FadeIn(sub, shift=UP * 0.2), run_time=0.6)
        self.beat(0.5)

        # --- a document splits into overlapping chunks --------------------- #
        doc = doc_glyph(w=1.9, h=2.6).to_edge(LEFT, buff=0.9).shift(DOWN * 0.3)
        dlabel = Text("document", font_size=20, color=MUTED).next_to(
            doc, DOWN, buff=0.2
        )
        self.play(FadeIn(doc, shift=RIGHT * 0.2), FadeIn(dlabel), run_time=0.7)
        self.beat(0.6)

        chunk_txts = ["…aspirin is given", "after a heart", "attack to thin…"]
        chunks = VGroup(
            *[chip(t, MED_C, w=2.6, h=0.66, fs=20, fill=0.10) for t in chunk_txts]
        )
        chunks.arrange(DOWN, buff=0.28).next_to(doc, RIGHT, buff=1.5).shift(UP * 0.1)
        c_arrows = VGroup(
            *[harrow(doc.get_right(), ch.get_left(), sw=2.5) for ch in chunks]
        )
        clabel = Text("overlapping chunks", font_size=20, color=MUTED).next_to(
            chunks, DOWN, buff=0.3
        )
        self.play(
            LaggedStart(*[GrowArrow(a) for a in c_arrows], lag_ratio=0.3, run_time=1.0)
        )
        self.play(
            LaggedStart(
                *[FadeIn(c, shift=RIGHT * 0.2) for c in chunks],
                lag_ratio=0.3,
                run_time=1.2,
            )
        )
        self.play(FadeIn(clabel), run_time=0.5)
        self.beat(1.6)

        # --- take ONE chunk → encoder → a vector --------------------------- #
        self.play(
            FadeOut(doc),
            FadeOut(dlabel),
            FadeOut(c_arrows),
            FadeOut(clabel),
            FadeOut(chunks[0]),
            FadeOut(chunks[2]),
            chunks[1].animate.move_to(LEFT * 4.6 + DOWN * 0.2),
            run_time=0.8,
        )
        one = chunks[1]
        enc = encoder(w=2.5, h=1.85)
        enc["group"].move_to(LEFT * 1.4 + DOWN * 0.2)
        enc_label = Text("embedding model", font_size=20, color=MODEL_C).next_to(
            enc["group"], DOWN, buff=0.22
        )
        a1 = harrow(one.get_right(), enc["box"].get_left())
        self.play(GrowArrow(a1), FadeIn(enc["group"]), FadeIn(enc_label), run_time=1.0)
        self.play(
            LaggedStart(
                *[
                    Indicate(c, color=MODEL_C, scale_factor=1.2)
                    for col in enc["net"][1:]
                    for c in col
                ],
                lag_ratio=0.02,
                run_time=1.2,
            )
        )
        vec = vector_row([0.12, -0.83, 0.47, 0.05], fs=24)
        vec.next_to(enc["group"], RIGHT, buff=0.8)
        a2 = harrow(enc["box"].get_right(), vec.get_left())
        self.play(GrowArrow(a2), Write(vec), run_time=1.0)
        dim = Text("a list of d numbers  (often 384 – 3072)", font_size=20, color=MUTED)
        dim.next_to(vec, DOWN, buff=0.3)
        self.play(FadeIn(dim, shift=UP * 0.15), run_time=0.6)
        self.beat(2.0)

        # --- that vector is a point in a latent space ---------------------- #
        self.play(
            FadeOut(VGroup(one, a1, enc["group"], enc_label, a2, dim)), run_time=0.6
        )
        L = latent_panel(w=6.0, h=5.0, center=RIGHT * 2.9 + DOWN * 0.35)
        ltitle = Text("latent space", font_size=24, color=MUTED).next_to(
            L["panel"], UP, buff=0.2
        )
        d1lab = Text("dim 1", font_size=16, color=FAINT).next_to(
            L["panel"], DOWN, buff=0.12
        )
        d2lab = (
            Text("dim 2", font_size=16, color=FAINT)
            .rotate(PI / 2)
            .next_to(L["panel"], LEFT, buff=0.12)
        )
        self.play(
            Create(L["panel"]),
            Create(L["axes"]),
            FadeIn(ltitle),
            FadeIn(d1lab),
            FadeIn(d2lab),
            run_time=1.0,
        )
        self.play(
            vec.animate.next_to(L["panel"], LEFT, buff=0.5).shift(UP * 2.0),
            run_time=0.8,
        )

        # the vector "flies" in and becomes a dot — landing exactly where chunk 0
        # sits in the scatter, so it coincides with the cluster we grow next.
        target = L["place"](*CHUNKS[0][2])
        flyer = Dot(vec.get_center(), radius=0.12, color=MED_C)
        self.play(FadeIn(flyer, scale=0.5), run_time=0.3)
        self.play(flyer.animate.move_to(target), run_time=1.0)
        self.play(Flash(flyer, color=MED_C, flash_radius=0.4), run_time=0.6)
        one_lab = Text("one chunk = one point", font_size=21, color=INK).to_edge(
            DOWN, buff=0.5
        )
        self.play(FadeIn(one_lab), run_time=0.6)
        self.beat(1.6)

        # --- do it for every chunk → clusters emerge ----------------------- #
        self.play(FadeOut(one_lab), FadeOut(vec), run_time=0.5)
        many = Text("…now embed the whole corpus:", font_size=23, color=INK)
        many.next_to(L["panel"], LEFT, buff=0.5).shift(UP * 1.3)
        self.play(FadeIn(many, shift=UP * 0.2), run_time=0.6)
        sc = self.scatter(L["place"])
        # index 0 (a medical chunk) is already on-screen as the flyer dot; add the rest
        add_dots = VGroup(*[sc["dots"][i] for i in range(1, len(CHUNKS))])
        self.play(
            LaggedStart(
                *[FadeIn(d, scale=0.5) for d in add_dots], lag_ratio=0.12, run_time=1.8
            )
        )
        self.beat(0.8)

        legend = VGroup(
            dot_label("medical", MED_C, fs=20),
            dot_label("finance", FIN_C, fs=20),
            dot_label("cooking", COOK_C, fs=20),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        legend.next_to(L["panel"], LEFT, buff=0.5).shift(DOWN * 0.9)
        self.play(FadeIn(legend, shift=UP * 0.2), run_time=0.7)
        self.beat(0.8)
        punch = Text(
            "Similar meaning → nearby points.", font_size=27, color=ACCENT
        ).to_edge(DOWN, buff=0.5)
        self.play(Write(punch), run_time=1.2)
        self.beat(2.0)
        self.wipe()

    # ====================================================================== #
    # Scene 3 — The geometry of meaning (similarity)
    # ====================================================================== #
    def scene_space(self):
        header = self.section_header("2 · The geometry of meaning", MED_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)
        sub = self.subtitle(header, "Closeness = similarity")
        self.play(FadeIn(sub, shift=UP * 0.2), run_time=0.6)
        self.beat(0.5)

        L = latent_panel(w=6.4, h=5.2, center=RIGHT * 2.7 + DOWN * 0.35)
        self.play(Create(L["panel"]), Create(L["axes"]), run_time=0.8)
        sc = self.scatter(L["place"], radius=0.10)
        self.play(
            LaggedStart(
                *[FadeIn(d, scale=0.5) for d in sc["dots"]],
                lag_ratio=0.06,
                run_time=1.4,
            )
        )
        self.beat(0.6)

        pc = L["center"]
        # two medical points (nearby) and one cooking point (far)
        p_a = sc["positions"][0]  # medical
        p_b = sc["positions"][1]  # medical
        p_c = sc["positions"][7]  # cooking
        va = Arrow(
            pc,
            p_a,
            buff=0,
            color=MED_C,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.12,
        )
        vb = Arrow(
            pc,
            p_b,
            buff=0,
            color=MED_C,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.12,
        )
        vc = Arrow(
            pc,
            p_c,
            buff=0,
            color=COOK_C,
            stroke_width=4,
            max_tip_length_to_length_ratio=0.12,
        )

        # --- similar pair: small angle, high cosine ------------------------ #
        self.play(GrowArrow(va), GrowArrow(vb), run_time=0.9)
        arc1 = angle_arc(pc, p_a, p_b, radius=0.8, color=INK)
        self.play(Create(arc1), run_time=0.5)
        sim_lab = VGroup(
            Text("small angle", font_size=22, color=INK),
            Text("cos θ ≈ 0.93", font_size=26, color=GOOD, weight="BOLD"),
            Text("→ similar", font_size=22, color=GOOD),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        sim_lab.to_edge(LEFT, buff=0.8).shift(UP * 0.9)
        self.play(FadeIn(sim_lab, shift=UP * 0.2), run_time=0.7)
        self.beat(1.8)

        # --- unrelated: wide angle, low cosine ----------------------------- #
        self.play(GrowArrow(vc), run_time=0.8)
        arc2 = angle_arc(pc, p_b, p_c, radius=0.55, color=MUTED)
        self.play(Create(arc2), run_time=0.5)
        dis_lab = VGroup(
            Text("wide angle", font_size=22, color=INK),
            Text("cos θ ≈ 0.16", font_size=26, color=BAD, weight="BOLD"),
            Text("→ unrelated", font_size=22, color=BAD),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        dis_lab.to_edge(LEFT, buff=0.8).shift(DOWN * 1.3)
        self.play(FadeIn(dis_lab, shift=UP * 0.2), run_time=0.7)
        self.beat(1.8)

        # --- the formula + the common metrics ------------------------------ #
        self.play(
            FadeOut(sim_lab),
            FadeOut(dis_lab),
            FadeOut(arc1),
            FadeOut(arc2),
            FadeOut(va),
            FadeOut(vb),
            FadeOut(vc),
            run_time=0.6,
        )
        formula = fitted_text(
            "cosine similarity = cos θ = (a·b) / (‖a‖‖b‖)",
            max_width=5.9,
            font_size=26,
            color=INK,
        )
        formula.to_edge(LEFT, buff=0.5).shift(UP * 1.55)
        self.play(Write(formula), run_time=1.4)
        self.beat(1.0)
        metrics = VGroup(
            dot_label("cosine — angle between vectors", GOOD, fs=21),
            dot_label("dot product — angle + magnitude", FIN_C, fs=21),
            dot_label("Euclidean (L2) — straight-line gap", COOK_C, fs=21),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.38)
        metrics.next_to(formula, DOWN, buff=0.6).align_to(formula, LEFT)
        mtitle = Text("ways to measure closeness:", font_size=22, color=MUTED)
        mtitle.next_to(metrics, UP, buff=0.3).align_to(metrics, LEFT)
        self.play(FadeIn(mtitle, shift=UP * 0.2), run_time=0.5)
        self.reveal(metrics, hold=1.3, run_time=0.5)

        note = Text(
            "Retrieval = find the vectors closest to your query.",
            font_size=26,
            color=ACCENT,
        ).to_edge(DOWN, buff=0.5)
        self.play(Write(note), run_time=1.3)
        self.beat(2.0)
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Retrieval: nearest neighbours
    # ====================================================================== #
    def scene_retrieve(self):
        header = self.section_header("3 · Retrieval by similarity", QUERY_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)
        sub = self.subtitle(header, "Embed the query, then find its neighbours")
        self.play(FadeIn(sub, shift=UP * 0.2), run_time=0.6)
        self.beat(0.4)

        L = latent_panel(w=6.4, h=5.3, center=RIGHT * 2.6 + DOWN * 0.3)
        self.play(Create(L["panel"]), Create(L["axes"]), run_time=0.8)
        sc = self.scatter(L["place"], radius=0.10)
        self.play(
            LaggedStart(
                *[FadeIn(d, scale=0.5) for d in sc["dots"]],
                lag_ratio=0.05,
                run_time=1.2,
            )
        )
        self.beat(0.4)

        # --- the query is embedded the same way, then dropped into the space #
        # Single-line box, tucked clearly BELOW the subtitle so nothing overlaps.
        qline = Text(f"“{QUERY_TEXT}”", font_size=21, color=QUERY_C)
        qbox = SurroundingRectangle(
            qline, buff=0.22, color=QUERY_C, corner_radius=0.12
        ).set_stroke(width=2)
        qg = VGroup(qbox, qline).to_edge(LEFT, buff=0.7).shift(UP * 1.4)
        qtitle = (
            Text("query", font_size=17, color=MUTED)
            .next_to(qbox, UP, buff=0.12)
            .align_to(qbox, LEFT)
        )
        embed_lab = (
            Text("embed · same model", font_size=18, color=MODEL_C)
            .next_to(qbox, DOWN, buff=0.2)
            .align_to(qbox, LEFT)
        )
        self.play(
            FadeIn(qtitle),
            FadeIn(qg, shift=RIGHT * 0.2),
            FadeIn(embed_lab),
            run_time=0.7,
        )
        self.beat(0.8)

        # query lands in the space, embedded exactly like the corpus
        qpos = L["place"](*QUERY_NORM)
        star = Star(5, outer_radius=0.2, color=QUERY_C, fill_opacity=1, stroke_width=0)
        star.move_to(qbox.get_right())
        a_in = harrow(qbox.get_right(), qpos, sw=2.5, color=QUERY_C)
        self.play(GrowArrow(a_in), run_time=0.6)
        self.play(star.animate.move_to(qpos), run_time=1.0)
        self.play(Flash(star, color=QUERY_C, flash_radius=0.5), run_time=0.6)
        self.beat(1.2)

        # --- nearest-neighbour search: rank by distance -------------------- #
        positions = np.array(sc["positions"])
        dists = np.linalg.norm(positions - qpos, axis=1)
        order = np.argsort(dists)
        k = 3
        topk = order[:k].tolist()
        dmin, dmax = float(dists.min()), float(dists.max())
        scores = {
            i: 0.99 - 0.55 * (float(dists[i]) - dmin) / (dmax - dmin + 1e-9)
            for i in range(len(dists))
        }

        # draw connector lines to the k nearest, ring + rank them
        connectors, rings, ranks = VGroup(), VGroup(), VGroup()
        for rank, i in enumerate(topk, start=1):
            P = sc["positions"][i]
            u = P - qpos
            u = u / (np.linalg.norm(u) + 1e-9)  # unit vector, away from the query
            ln = DashedLine(qpos, P, color=QUERY_C, stroke_width=2.5, dash_length=0.08)
            ring = Circle(radius=0.18, color=GOOD, stroke_width=3).move_to(P)
            # rank number sits on the far side of the dot (outward), never on it
            rk = Text(str(rank), font_size=20, color=GOOD, weight="BOLD").move_to(
                P + u * 0.34
            )
            connectors.add(ln)
            rings.add(ring)
            ranks.add(rk)
        self.play(
            LaggedStart(*[Create(c) for c in connectors], lag_ratio=0.3, run_time=1.1)
        )
        self.play(
            LaggedStart(
                *[Create(r) for r in rings],
                *[FadeIn(t) for t in ranks],
                lag_ratio=0.15,
                run_time=1.0,
            )
        )
        self.beat(1.2)

        # --- the ranked results panel -------------------------------------- #
        res_rows = VGroup()
        for rank, i in enumerate(topk, start=1):
            text = sc["meta"][i][1]
            bg = Circle(radius=0.2, color=GOOD, fill_opacity=1, stroke_width=0)
            badge = Text(str(rank), font_size=20, color=BG, weight="BOLD").move_to(bg)
            score = Text(f"{scores[i]:.2f}", font_size=20, color=GOOD, weight="BOLD")
            body = fitted_text(text, max_width=3.9, font_size=19, color=INK)
            row = VGroup(VGroup(bg, badge), body, score).arrange(RIGHT, buff=0.28)
            res_rows.add(row)
        res_rows.arrange(DOWN, aligned_edge=LEFT, buff=0.34)
        rtitle = Text(
            "top-k chunks · k-NN  (k = 3)", font_size=22, color=GOOD, weight="BOLD"
        )
        rcard = VGroup(rtitle, res_rows).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        rcard.to_edge(LEFT, buff=0.7).shift(DOWN * 1.35)
        self.play(FadeIn(rtitle, shift=UP * 0.2), run_time=0.6)
        for row in res_rows:
            self.play(FadeIn(row, shift=RIGHT * 0.2), run_time=0.5)
            self.beat(1.0)

        note = Text(
            "Return the closest chunks — the most relevant context.",
            font_size=25,
            color=ACCENT,
        ).to_edge(DOWN, buff=0.45)
        self.play(Write(note), run_time=1.2)
        self.beat(2.0)
        self.wipe()

    # ====================================================================== #
    # Scene 5 — The retrievers (real systems)
    # ====================================================================== #
    def scene_systems(self):
        header = self.section_header("4 · The retrievers", FIN_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)
        sub = self.subtitle(header, "Engines that store vectors and search them fast")
        self.play(FadeIn(sub, shift=UP * 0.2), run_time=0.6)
        self.beat(0.5)

        # --- three product cards ------------------------------------------- #
        def product(name, desc, color):
            bar = Rectangle(
                width=3.5, height=0.14, stroke_width=0, fill_color=color, fill_opacity=1
            )
            nm = Text(name, font_size=26, color=INK, weight="BOLD")
            ds = Text(desc, font_size=18, color=MUTED, line_spacing=0.8)
            body = VGroup(nm, ds).arrange(DOWN, buff=0.22)
            box = RoundedRectangle(
                width=3.9,
                height=2.2,
                corner_radius=0.14,
                stroke_color=color,
                stroke_width=2.5,
                fill_color=color,
                fill_opacity=0.07,
            )
            bar.next_to(box.get_top(), DOWN, buff=0)
            body.move_to(box).shift(DOWN * 0.1)
            return VGroup(box, bar, body)

        cards = (
            VGroup(
                product("OpenSearch", "k-NN plugin\nHNSW · Faiss / Lucene", FIN_C),
                product(
                    "Azure AI Search", "vector search\nHNSW · exhaustive kNN", MED_C
                ),
                product(
                    "pgvector",
                    "Postgres extension\nIVFFlat · HNSW  ·  <=> cosine",
                    GOOD,
                ),
            )
            .arrange(RIGHT, buff=0.5)
            .move_to(UP * 1.35)
        )
        self.reveal(cards, hold=1.4, run_time=0.6, shift=UP * 0.2)

        unify = fitted_text(
            "Same core idea:  store vectors  →  index them  →  nearest-neighbour search",
            max_width=12.8,
            font_size=24,
            color=INK,
        )
        unify.next_to(cards, DOWN, buff=0.6)
        self.play(Write(unify), run_time=1.3)
        self.beat(1.4)

        # --- exact vs approximate (the index) ------------------------------ #
        self.play(FadeOut(cards), FadeOut(unify), FadeOut(sub), run_time=0.6)
        idx_title = Text(
            "Why an index?  a million vectors is too many to scan.",
            font_size=26,
            color=INK,
        ).to_edge(UP, buff=1.7)
        self.play(FadeIn(idx_title, shift=DOWN * 0.2), run_time=0.7)

        # exact kNN (left): compare against everything
        exact_dots = VGroup(*[Dot(radius=0.06, color=MUTED) for _ in range(24)])
        exact_dots.arrange_in_grid(rows=4, buff=0.32)
        qx = Star(5, outer_radius=0.14, color=QUERY_C, fill_opacity=1, stroke_width=0)
        qx.move_to(exact_dots.get_center())
        rays = VGroup(
            *[
                Line(
                    qx.get_center(), d.get_center(), stroke_width=1, stroke_color=MUTED
                ).set_opacity(0.4)
                for d in exact_dots
            ]
        )
        exact = VGroup(exact_dots, rays, qx)
        ex_lab = VGroup(
            Text("Exact kNN", font_size=24, color=INK, weight="BOLD"),
            Text("compare to all", font_size=19, color=MUTED),
            Text("accurate · slow", font_size=19, color=BAD),
        ).arrange(DOWN, buff=0.14)
        VGroup(exact, ex_lab).arrange(DOWN, buff=0.4).to_edge(LEFT, buff=1.3).shift(
            DOWN * 0.5
        )
        self.play(FadeIn(exact_dots), run_time=0.6)
        self.play(
            FadeIn(qx, scale=0.5),
            LaggedStart(*[Create(r) for r in rays], lag_ratio=0.02, run_time=1.2),
        )
        self.play(FadeIn(ex_lab, shift=UP * 0.2), run_time=0.6)
        self.beat(1.4)

        # approximate (right): a small HNSW-like graph, hop to the neighbour
        rng = np.random.default_rng(3)
        n = 10
        gpos = [
            np.array([rng.uniform(-1.1, 1.1), rng.uniform(-1.1, 1.1), 0])
            for _ in range(n)
        ]
        gdots = VGroup(*[Dot(p, radius=0.07, color=FIN_C) for p in gpos])
        gedges = VGroup()
        for i in range(n):
            d = sorted(range(n), key=lambda j: np.linalg.norm(gpos[i] - gpos[j]))
            for j in d[1:3]:
                gedges.add(
                    Line(
                        gpos[i], gpos[j], stroke_width=1.5, stroke_color=FIN_C
                    ).set_opacity(0.35)
                )
        graph = VGroup(gedges, gdots)
        graph.move_to(ORIGIN)
        qg2 = Star(5, outer_radius=0.14, color=QUERY_C, fill_opacity=1, stroke_width=0)
        # path: greedy hops toward the query target (nearest graph node)
        tgt = int(
            np.argmin([np.linalg.norm(p - np.array([0.9, -0.8, 0])) for p in gpos])
        )
        path_idx, cur = [0], 0
        for _ in range(4):
            nxt = min(
                range(n),
                key=lambda j: np.linalg.norm(gpos[j] - gpos[tgt]) if j != cur else 1e9,
            )
            if np.linalg.norm(gpos[nxt] - gpos[tgt]) >= np.linalg.norm(
                gpos[cur] - gpos[tgt]
            ):
                break
            path_idx.append(nxt)
            cur = nxt
            if cur == tgt:
                break
        ap_lab = VGroup(
            Text("Approximate NN", font_size=24, color=INK, weight="BOLD"),
            Text("hop through a graph (HNSW)", font_size=19, color=MUTED),
            Text("~exact · fast", font_size=19, color=GOOD),
        ).arrange(DOWN, buff=0.14)
        VGroup(graph, ap_lab).arrange(DOWN, buff=0.4).to_edge(RIGHT, buff=1.3).shift(
            DOWN * 0.5
        )
        self.play(FadeIn(gedges), FadeIn(gdots), run_time=0.7)
        qg2.move_to(gpos[0] + graph.get_center())
        self.play(FadeIn(qg2, scale=0.6), run_time=0.4)
        for a, b in zip(path_idx[:-1], path_idx[1:], strict=False):
            seg = Line(
                gpos[a] + graph.get_center(),
                gpos[b] + graph.get_center(),
                color=QUERY_C,
                stroke_width=4,
            )
            self.play(
                Create(seg),
                qg2.animate.move_to(gpos[b] + graph.get_center()),
                run_time=0.45,
            )
        self.play(Flash(qg2, color=GOOD, flash_radius=0.35), run_time=0.5)
        self.play(FadeIn(ap_lab, shift=UP * 0.2), run_time=0.6)
        self.beat(1.6)

        tradeoff = Text(
            "The knob every engine gives you:  recall  ↔  latency",
            font_size=26,
            color=ACCENT,
        ).to_edge(DOWN, buff=0.5)
        self.play(Write(tradeoff), run_time=1.3)
        self.beat(2.0)
        self.wipe()

    # ====================================================================== #
    # Scene 6 — Why it matters (RAG)
    # ====================================================================== #
    def scene_why(self):
        header = self.section_header("Why it matters — RAG", ACCENT)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)
        sub = self.subtitle(header, "Retrieved chunks become the model's context")
        self.play(FadeIn(sub, shift=UP * 0.2), run_time=0.6)
        self.beat(0.5)

        # --- the RAG loop -------------------------------------------------- #
        q = chip("Query", QUERY_C, w=1.9, h=1.0, fs=22)
        ret = chip("Vector\nretriever", MED_C, w=2.0, h=1.0, fs=21)
        ctx = chip("Top-k chunks\n→ context", GOOD, w=2.3, h=1.0, fs=20)
        llm = chip("LLM", MODEL_C, w=1.7, h=1.0, fs=24)
        ans = chip("Grounded\nanswer", INK, w=2.0, h=1.0, fs=21)
        row = VGroup(q, ret, ctx, llm, ans).arrange(RIGHT, buff=0.55)
        row.move_to(UP * 1.35)
        arrows = VGroup(
            *[
                harrow(row[i].get_right(), row[i + 1].get_left(), sw=3)
                for i in range(len(row) - 1)
            ]
        )
        self.reveal(row, hold=0.55, run_time=0.45, shift=UP * 0.15)
        self.play(
            LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.3, run_time=1.5)
        )
        self.beat(0.8)

        token = Dot(radius=0.12, color=ACCENT).move_to(row[0].get_center())
        self.add(token)
        for i in range(len(row)):
            self.play(
                token.animate.move_to(row[i].get_center()),
                row[i][0].animate.set_fill(opacity=0.3),
                run_time=0.5,
            )
            self.beat(0.5)
        self.play(
            FadeOut(token), Flash(row[-1], color=GOOD, flash_radius=0.8), run_time=0.6
        )
        tie = Text(
            "the retriever fills the context window with the right facts",
            font_size=22,
            color=MUTED,
        ).next_to(row, DOWN, buff=0.55)
        self.play(FadeIn(tie, shift=UP * 0.2), run_time=0.7)
        self.beat(1.6)
        self.play(FadeOut(tie), run_time=0.4)

        # --- benefits ------------------------------------------------------ #
        benefits = [
            "Fresh & private knowledge — no re-training",
            "Grounded answers — fewer hallucinations",
            "Citations — point back to the source chunk",
            "Scales to millions of documents",
        ]
        rows = VGroup()
        for b in benefits:
            tk = make_tick(scale=0.75)
            tx = Text(b, font_size=22, color=INK).next_to(tk, RIGHT, buff=0.25)
            rows.add(VGroup(tk, tx))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.34).move_to(DOWN * 0.6)
        self.reveal(rows, hold=1.2, run_time=0.5)

        punch = fitted_text(
            "Embeddings turn your data into the model's long-term memory.",
            max_width=13.0,
            font_size=27,
            color=INK,
            weight="BOLD",
        ).to_edge(DOWN, buff=0.6)
        self.play(Write(punch), run_time=1.6)
        self.play(Circumscribe(punch, color=VEC_C, run_time=1.4))
        self.beat(2.0)
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_problem()
        self.scene_embed()
        self.scene_space()
        self.scene_retrieve()
        self.scene_systems()
        self.scene_why()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_EmbBase):
    def construct(self):
        self.play_intro()


class Problem(_EmbBase):
    def construct(self):
        self.scene_problem()


class Embed(_EmbBase):
    def construct(self):
        self.scene_embed()


class Space(_EmbBase):
    def construct(self):
        self.scene_space()


class Retrieve(_EmbBase):
    def construct(self):
        self.scene_retrieve()


class Systems(_EmbBase):
    def construct(self):
        self.scene_systems()


class Why(_EmbBase):
    def construct(self):
        self.scene_why()


class Outro(_EmbBase):
    def construct(self):
        self.play_outro()


class EmbeddingRetrieval(_EmbBase):
    """The whole ~6-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    EmbeddingRetrieval().render()

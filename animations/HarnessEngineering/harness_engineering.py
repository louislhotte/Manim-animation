"""Harness Engineering — a ~6-minute explainer, house-style.

Six roughly one-minute scenes that build the mental model of *engineering the
system around* a language model, not just the model itself:

    1. What is Harness Engineering   -- the nested picture: Prompt < Context < Harness
    2. Prompt Engineering            -- what you *say* to the model
    3. Context Engineering           -- what the model *sees* (the window as a budget)
    4. Harness Engineering           -- the system it *runs in* (the agent loop)
    5. Harness Pipeline Example      -- a concrete coding-agent pipeline with a retry loop
    6. Why it matters                -- reliability climbs; the harness is the moat

Bookended by the channel's intro card and the "Thank you for watching!" outro
(see animations/2024/Intro.py and animations/CNN/Part 6_ Conclusion/scene_3.py).

Everything uses ``Text`` (Pango) rather than ``Tex`` so it renders without a
LaTeX install and stays fast to iterate on.

Scenes are exposed both individually (``What``, ``Prompt``, ``Context``,
``Harness``, ``Pipeline``, ``Why``, ``Intro``, ``Outro``) and as one continuous
film (``HarnessEngineering``).

Env knobs:
    HARNESS_QUICK=1   shorten every hold for a fast sanity render
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

QUICK = os.environ.get("HARNESS_QUICK") == "1"
# Single knob for pacing: every on-screen "hold" in the six content scenes is
# scaled by this. QUICK collapses the holds for fast iteration; otherwise it
# sets the reading rhythm (~50 s per scene). The intro/outro cards use a fixed
# rhythm (card_wait) so they stay crisp regardless of DELAY.
DELAY = 0.3 if QUICK else 1.85

# ---- palette -------------------------------------------------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
MODEL_C = "#FFD166"     # the model core (gold)
PROMPT_C = "#5B8DEF"    # prompt layer (blue)
CONTEXT_C = "#2EC4B6"   # context layer (teal)
HARNESS_C = "#FF8C42"   # harness layer (orange)
GOOD = "#3DD68C"        # pass / green
BAD = "#FF5C5C"         # fail / red
ACCENT = "#FFD166"


# ---- small reusable pieces ------------------------------------------------ #
def chip(text, color, w=2.3, h=0.95, fs=26, fill=0.12, tcolor=None, radius=0.14):
    """A rounded, tinted box with a centered auto-fitting label. grp[0] is the box."""
    box = RoundedRectangle(
        width=w, height=h, corner_radius=radius,
        stroke_color=color, stroke_width=3,
        fill_color=color, fill_opacity=fill,
    )
    label = Text(text, font_size=fs, color=tcolor or INK)
    if label.width > w - 0.35:
        label.scale((w - 0.35) / label.width)
    label.move_to(box)
    return VGroup(box, label)


def harrow(start, end, color=MUTED, sw=4):
    return Arrow(
        start, end, buff=0.12, stroke_width=sw, color=color,
        max_tip_length_to_length_ratio=0.16, tip_length=0.22,
    )


def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])]
    )
    v.set_stroke(color=color, width=sw)
    return v.scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.18, -0.18, 0], [0.18, 0.18, 0])
    b = Line([-0.18, 0.18, 0], [0.18, -0.18, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


def dot_label(text, color, fs=26):
    """A color dot + label row (for legends)."""
    d = Dot(radius=0.09, color=color)
    t = Text(text, font_size=fs, color=INK).next_to(d, RIGHT, buff=0.22)
    return VGroup(d, t)


# ========================================================================== #
class _HarnessBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # ---- timing helpers --------------------------------------------------- #
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        # intro/outro rhythm — independent of the scene DELAY so title cards
        # stay tight; still collapses under QUICK for fast iteration.
        self.wait(t * (0.3 if QUICK else 1.0))

    def reveal(self, items, hold=1.6, run_time=0.5, shift=RIGHT * 0.2):
        """Fade items in one at a time, each with a reading hold after it."""
        for m in items:
            self.play(FadeIn(m, shift=shift), run_time=run_time)
            self.beat(hold)

    def wipe(self, rt=0.7):
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    # ---- the recurring nested-layers diagram ------------------------------ #
    def build_layers(self, scale=1.0):
        core = RoundedRectangle(
            width=1.7, height=0.95, corner_radius=0.18,
            stroke_color=MODEL_C, stroke_width=4,
            fill_color=MODEL_C, fill_opacity=0.18,
        )
        core_label = Text("LLM", font_size=26, color=MODEL_C, weight="BOLD").move_to(core)
        prompt = RoundedRectangle(width=3.4, height=2.05, corner_radius=0.22,
                                  stroke_color=PROMPT_C, stroke_width=4, fill_opacity=0)
        context = RoundedRectangle(width=5.1, height=3.35, corner_radius=0.26,
                                   stroke_color=CONTEXT_C, stroke_width=4, fill_opacity=0)
        harness = RoundedRectangle(width=7.0, height=4.75, corner_radius=0.30,
                                   stroke_color=HARNESS_C, stroke_width=4, fill_opacity=0)
        pl = Text("Prompt", font_size=22, color=PROMPT_C).move_to(prompt.get_top() + DOWN * 0.26)
        cl = Text("Context", font_size=22, color=CONTEXT_C).move_to(context.get_top() + DOWN * 0.26)
        hl = Text("Harness", font_size=22, color=HARNESS_C).move_to(harness.get_top() + DOWN * 0.28)
        group = VGroup(harness, context, prompt, core, core_label, hl, cl, pl).scale(scale)
        return dict(group=group, core=core, core_label=core_label, prompt=prompt,
                    context=context, harness=harness, pl=pl, cl=cl, hl=hl)

    def mini_layers(self, highlight=None):
        d = self.build_layers(scale=0.30)
        d["pl"].set_opacity(0); d["cl"].set_opacity(0); d["hl"].set_opacity(0)
        rings = {"prompt": d["prompt"], "context": d["context"], "harness": d["harness"]}
        for name, ring in rings.items():
            if highlight and name != highlight:
                ring.set_stroke(opacity=0.25)
            elif highlight and name == highlight:
                ring.set_stroke(width=8)
        g = d["group"]
        g.to_corner(UR, buff=0.4)
        return g

    def section_header(self, label, color=INK):
        txt = Text(label, font_size=34, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(txt.get_left(), txt.get_right()).next_to(txt, DOWN, buff=0.12)
        line.set_stroke(color=color, width=3)
        return VGroup(txt, line)

    # ---- 1 & bookend: house-style intro/outro cards ----------------------- #
    def introduction(self, title1, title2):
        header = Text(title1, font_size=52, color=INK, weight="BOLD")
        header.set(width=min(9.5, header.width))
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=HARNESS_C)
        writer = Text("Created by Ptolémé", font_size=28, color=PROMPT_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.8)
        sub = Text(title2, font_size=38, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.card_wait(2.4)
        return VGroup(header, writer, line)

    def play_intro(self):
        group = self.introduction(
            "Harness Engineering",
            "Prompt · Context · Harness",
        )
        self.play(FadeOut(group), run_time=1.0)
        self.card_wait(0.4)

    def play_outro(self):
        self.card_wait(0.6)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=HARNESS_C)
        writer = Text("Created by Ptolémé", font_size=28, color=PROMPT_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.2)
        self.card_wait(2.6)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.4)
        self.card_wait(0.8)

    # ====================================================================== #
    # Scene 1 — What is Harness Engineering
    # ====================================================================== #
    def scene_what(self):
        title = Text("What is Harness Engineering?", font_size=46, color=INK, weight="BOLD")
        self.play(Write(title), run_time=1.5)
        self.beat(1.0)
        self.play(title.animate.scale(0.62).to_edge(UP, buff=0.4), run_time=0.8)

        # --- the naïve picture: prompt -> LLM -> output --------------------- #
        cap = Text("The naïve picture:", font_size=26, color=MUTED).next_to(title, DOWN, buff=0.5)
        p = chip("Prompt", PROMPT_C, w=2.1, h=0.9)
        m = chip("LLM", MODEL_C, w=2.1, h=0.9)
        o = chip("Output", MUTED, w=2.1, h=0.9)
        row = VGroup(p, m, o).arrange(RIGHT, buff=1.2).next_to(cap, DOWN, buff=0.55)
        a1 = harrow(p.get_right(), m.get_left())
        a2 = harrow(m.get_right(), o.get_left())
        self.play(FadeIn(cap, shift=UP * 0.2), run_time=0.6)
        self.play(LaggedStart(FadeIn(p), GrowArrow(a1), FadeIn(m), GrowArrow(a2), FadeIn(o),
                              lag_ratio=0.5, run_time=2.4))
        self.beat(1.4)
        hope = Text("You tweak the wording and hope for the best.",
                    font_size=24, color=MUTED).next_to(row, DOWN, buff=0.55)
        self.play(FadeIn(hope, shift=UP * 0.2), run_time=0.7)
        self.beat(1.8)
        warn = Text("brittle · unreliable · doesn't scale", font_size=24, color=BAD)
        warn.move_to(hope)
        x = make_cross(scale=1.5).next_to(warn, LEFT, buff=0.3)
        self.play(Transform(hope, warn), Create(x), run_time=0.9)
        self.beat(2.0)

        naive = VGroup(cap, row, a1, a2, hope, x)
        self.play(FadeOut(naive), run_time=0.8)

        # --- the real picture: nested layers ------------------------------- #
        lead = Text("Real systems wrap the model in layers:", font_size=27, color=INK)
        lead.next_to(title, DOWN, buff=0.45)
        self.play(FadeIn(lead, shift=UP * 0.2), run_time=0.7)
        self.beat(0.8)

        d = self.build_layers(scale=0.92)
        d["group"].shift(LEFT * 1.7 + DOWN * 0.35)
        self.play(Create(d["core"]), Write(d["core_label"]), run_time=0.9)
        self.beat(0.8)
        self.play(Create(d["prompt"]), FadeIn(d["pl"]), run_time=0.9)
        self.beat(0.7)
        self.play(Create(d["context"]), FadeIn(d["cl"]), run_time=0.9)
        self.beat(0.7)
        self.play(Create(d["harness"]), FadeIn(d["hl"]), run_time=1.0)
        self.beat(1.0)

        # color-coded legend on the right, revealed with each ring lit
        legend = VGroup(
            dot_label("what you say", PROMPT_C, fs=25),
            dot_label("what it sees", CONTEXT_C, fs=25),
            dot_label("the system it runs in", HARNESS_C, fs=25),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.6)
        legend.next_to(d["harness"], RIGHT, buff=0.7)
        for ring, lab, item in [
            (d["prompt"], d["pl"], legend[0]),
            (d["context"], d["cl"], legend[1]),
            (d["harness"], d["hl"], legend[2]),
        ]:
            self.play(FadeIn(item, shift=RIGHT * 0.2),
                      Indicate(ring, color=ring.get_stroke_color(), scale_factor=1.06),
                      Indicate(lab, scale_factor=1.06), run_time=0.9)
            self.beat(1.6)

        # --- the thesis ---------------------------------------------------- #
        thesis = Text("Engineer everything around the model — not just the model.",
                      font_size=28, color=INK).to_edge(DOWN, buff=0.75)
        self.play(Write(thesis), run_time=1.4)
        self.beat(1.6)
        punch = Text("Model quality is table-stakes; the harness is the product.",
                     font_size=24, color=ACCENT).next_to(thesis, DOWN, buff=0.25)
        self.play(FadeIn(punch, shift=UP * 0.2), Circumscribe(d["harness"], color=HARNESS_C, run_time=1.4))
        self.beat(2.2)
        self.wipe()

    # ====================================================================== #
    # Scene 2 — Prompt Engineering
    # ====================================================================== #
    def scene_prompt(self):
        header = self.section_header("1 · Prompt Engineering", PROMPT_C)
        mini = self.mini_layers(highlight="prompt")
        self.play(FadeIn(header, shift=DOWN * 0.2), FadeIn(mini), run_time=0.9)
        subtitle = Text("Craft what you say to the model", font_size=27, color=MUTED)
        subtitle.next_to(header, DOWN, buff=0.35).to_edge(LEFT, buff=0.5)
        self.play(FadeIn(subtitle, shift=UP * 0.2), run_time=0.6)
        self.beat(0.8)

        # --- prompt anatomy card (left), each part annotated --------------- #
        parts = [
            ("System / Role", "who the model is"),
            ("Instructions", "what to do"),
            ("Output format", "shape of the answer"),
            ("Few-shot examples", "show, don't just tell"),
        ]
        rows = VGroup(*[chip(t, PROMPT_C, w=3.3, h=0.62, fs=22) for t, _ in parts])
        rows.arrange(DOWN, buff=0.30)
        card = SurroundingRectangle(rows, buff=0.3, color=PROMPT_C, corner_radius=0.15).set_stroke(width=2)
        title_card = Text("A prompt", font_size=22, color=PROMPT_C).next_to(card, UP, buff=0.18)
        prompt_card = VGroup(card, title_card, rows).to_edge(LEFT, buff=0.8).shift(DOWN * 0.3)
        self.play(Create(card), FadeIn(title_card), run_time=0.7)
        anns = VGroup()
        for (t, desc), rowbox in zip(parts, rows):
            ann = Text(desc, font_size=19, color=MUTED, slant=ITALIC).next_to(rowbox, RIGHT, buff=0.3)
            anns.add(ann)
            self.play(FadeIn(rowbox, shift=RIGHT * 0.2), run_time=0.45)
            self.play(FadeIn(ann, shift=RIGHT * 0.15), run_time=0.4)
            self.beat(1.3)

        # --- vague vs. structured comparison (right) ----------------------- #
        def output_lines(neat, color):
            g = VGroup()
            rng = np.random.default_rng(7)
            for _ in range(5):
                length = 2.0 if neat else float(rng.uniform(0.7, 2.0))
                g.add(Line([0, 0, 0], [length, 0, 0]).set_stroke(color=color, width=5))
            g.arrange(DOWN, aligned_edge=LEFT, buff=0.16)
            return g

        vague_out = output_lines(False, MUTED)
        vbox = SurroundingRectangle(vague_out, buff=0.25, color=BAD, corner_radius=0.1).set_stroke(width=2)
        vlabel = Text("“write about dogs”", font_size=22, color=MUTED).next_to(vbox, UP, buff=0.15)
        vx = make_cross(scale=1.3).next_to(vbox, RIGHT, buff=0.25)
        vague = VGroup(vlabel, vbox, vague_out, vx)

        neat_out = output_lines(True, INK)
        nbox = SurroundingRectangle(neat_out, buff=0.25, color=GOOD, corner_radius=0.1).set_stroke(width=2)
        nlabel = Text("role + steps + format", font_size=22, color=INK).next_to(nbox, UP, buff=0.15)
        nt = make_tick(scale=1.5).next_to(nbox, RIGHT, buff=0.25)
        neat = VGroup(nlabel, nbox, neat_out, nt)

        compare = VGroup(vague, neat).arrange(DOWN, buff=0.75).to_edge(RIGHT, buff=1.0).shift(DOWN * 0.3)
        self.play(FadeIn(vlabel), Create(vbox), Create(vague_out), run_time=1.0)
        self.play(Create(vx), run_time=0.5)
        self.beat(1.4)
        self.play(FadeIn(nlabel), Create(nbox), Create(neat_out), run_time=1.0)
        self.play(Create(nt), run_time=0.5)
        self.beat(1.0)
        note = Text("same model — better wording", font_size=20, color=ACCENT).next_to(compare, DOWN, buff=0.3)
        self.play(FadeIn(note), run_time=0.6)
        self.beat(1.8)

        # --- techniques tick list (replaces the card) ---------------------- #
        self.play(FadeOut(prompt_card), FadeOut(anns), run_time=0.6)
        techs = ["Clear, specific instructions", "Few-shot examples",
                 "Step-by-step (chain of thought)", "Constrain the output format"]
        tech_rows = VGroup()
        for t in techs:
            tk = make_tick(scale=0.9)
            tx = Text(t, font_size=24, color=INK).next_to(tk, RIGHT, buff=0.25)
            tech_rows.add(VGroup(tk, tx))
        tech_rows.arrange(DOWN, aligned_edge=LEFT, buff=0.4).to_edge(LEFT, buff=0.9).shift(DOWN * 0.2)
        ttitle = Text("Techniques", font_size=26, color=PROMPT_C, weight="BOLD")
        ttitle.next_to(tech_rows, UP, buff=0.35).align_to(tech_rows, LEFT)
        self.play(FadeIn(ttitle, shift=UP * 0.2), run_time=0.5)
        self.reveal(tech_rows, hold=1.5, run_time=0.5, shift=RIGHT * 0.25)

        # --- limitation -> motivates context ------------------------------- #
        limit = Text("But prompting alone hits a ceiling →  control the context.",
                     font_size=27, color=HARNESS_C).to_edge(DOWN, buff=0.5)
        self.play(Write(limit), run_time=1.4)
        self.beat(2.0)
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Context Engineering
    # ====================================================================== #
    def scene_context(self):
        header = self.section_header("2 · Context Engineering", CONTEXT_C)
        mini = self.mini_layers(highlight="context")
        self.play(FadeIn(header, shift=DOWN * 0.2), FadeIn(mini), run_time=0.9)
        subtitle = Text("Assemble what the model can see", font_size=27, color=MUTED)
        subtitle.next_to(header, DOWN, buff=0.35).to_edge(LEFT, buff=0.5)
        self.play(FadeIn(subtitle, shift=UP * 0.2), run_time=0.6)
        self.beat(0.6)

        # --- the context window as a bounded budget ------------------------ #
        window = RoundedRectangle(width=3.4, height=4.2, corner_radius=0.18,
                                  stroke_color=CONTEXT_C, stroke_width=3, fill_opacity=0)
        window.move_to(RIGHT * 2.4 + DOWN * 0.3)
        wtitle = Text("Context window", font_size=24, color=CONTEXT_C).next_to(window, UP, buff=0.2)
        bar_bg = Rectangle(width=0.35, height=4.2, stroke_color=MUTED, stroke_width=2, fill_opacity=0)
        bar_bg.next_to(window, RIGHT, buff=0.35)
        budget_txt = Text("token\nbudget", font_size=18, color=MUTED, line_spacing=0.7).next_to(bar_bg, RIGHT, buff=0.2)
        self.play(Create(window), FadeIn(wtitle), Create(bar_bg), FadeIn(budget_txt), run_time=1.0)
        self.beat(0.6)

        bar_bottom = bar_bg.get_bottom()[1]

        def bar_to(frac):
            h = max(0.02, 4.2 * frac)
            r = Rectangle(width=0.33, height=h, stroke_width=0, fill_color=CONTEXT_C, fill_opacity=0.85)
            r.move_to([bar_bg.get_center()[0], bar_bottom + h / 2, 0])
            return r

        bar_fill = bar_to(0.0)
        self.add(bar_fill)

        # --- sources feed into the window --------------------------------- #
        sources = [
            ("System prompt", PROMPT_C),
            ("Retrieved docs (RAG)", CONTEXT_C),
            ("Tools & schemas", HARNESS_C),
            ("Memory / history", MODEL_C),
            ("Examples", GOOD),
        ]
        src_boxes = VGroup(*[chip(t, c, w=3.0, h=0.62, fs=21) for t, c in sources])
        src_boxes.arrange(DOWN, buff=0.30).to_edge(LEFT, buff=0.8).shift(DOWN * 0.3)

        inner_w = window.width - 0.5
        block_h = 0.6
        filled = 0.0
        bottom = window.get_bottom()[1] + 0.15
        placed = []
        for i, (label, color) in enumerate(sources):
            sb = src_boxes[i]
            self.play(FadeIn(sb, shift=RIGHT * 0.2), run_time=0.5)
            ar = harrow(sb.get_right(), window.get_left(), color=color, sw=3)
            block = Rectangle(width=inner_w, height=block_h, stroke_width=1,
                              stroke_color=color, fill_color=color, fill_opacity=0.35)
            block.move_to([window.get_center()[0], bottom + filled + block_h / 2, 0])
            btxt = Text(label, font_size=18, color=INK)
            if btxt.width > inner_w - 0.2:
                btxt.scale((inner_w - 0.2) / btxt.width)
            btxt.move_to(block)
            filled += block_h + 0.06
            self.play(GrowArrow(ar), FadeIn(block, shift=DOWN * 0.15), FadeIn(btxt),
                      Transform(bar_fill, bar_to(filled / 4.2)), run_time=0.7)
            self.remove(ar)
            placed.append(VGroup(block, btxt))
            self.beat(0.9)

        self.beat(0.5)
        full_note = Text("limited budget", font_size=22, color=BAD).next_to(bar_bg, DOWN, buff=0.25)
        self.play(FadeIn(full_note), Flash(bar_bg, color=BAD, flash_radius=0.6), run_time=0.9)
        self.beat(1.4)

        # --- curate: drop the low-signal block, budget recedes ------------- #
        curate = Text("curate: prune low-signal context", font_size=21, color=ACCENT)
        curate.next_to(src_boxes, DOWN, buff=0.45).to_edge(LEFT, buff=0.8)
        top_block = placed[-1]
        self.play(FadeIn(curate, shift=UP * 0.2), run_time=0.6)
        filled -= block_h + 0.06
        self.play(FadeOut(top_block, shift=RIGHT * 0.4), FadeOut(src_boxes[-1]),
                  Transform(bar_fill, bar_to(filled / 4.2)), run_time=0.8)
        self.beat(1.6)

        # --- principle ----------------------------------------------------- #
        self.play(FadeOut(src_boxes[:-1]), FadeOut(curate), run_time=0.6)
        principle = VGroup(
            Text("Right info · right place · right time", font_size=27, color=INK),
            Text("relevance  >  volume", font_size=26, color=CONTEXT_C, weight="BOLD"),
            Text("garbage in → garbage out", font_size=23, color=MUTED),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.4).to_edge(LEFT, buff=0.8).shift(DOWN * 0.1)
        self.reveal(principle, hold=1.7, run_time=0.55)
        self.play(Indicate(principle[1], color=CONTEXT_C, scale_factor=1.12), run_time=1.0)
        self.beat(1.8)
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Harness Engineering
    # ====================================================================== #
    def scene_harness(self):
        header = self.section_header("3 · Harness Engineering", HARNESS_C)
        mini = self.mini_layers(highlight="harness")
        self.play(FadeIn(header, shift=DOWN * 0.2), FadeIn(mini), run_time=0.9)
        subtitle = Text("Build the system the model runs inside", font_size=27, color=MUTED)
        subtitle.next_to(header, DOWN, buff=0.35).to_edge(LEFT, buff=0.5)
        self.play(FadeIn(subtitle, shift=UP * 0.2), run_time=0.6)
        self.beat(0.6)

        # --- the agent loop: Model -> Act -> Observe -> Model -------------- #
        # Built centered so it reads well on its own during the pulse, then slid
        # left (below) once the component list needs the right-hand space.
        center = LEFT * 0.3 + DOWN * 0.15
        model = chip("Model\n(decide)", MODEL_C, w=2.1, h=1.1, fs=22).move_to(center + UP * 1.7)
        act = chip("Act\n(tools)", HARNESS_C, w=2.1, h=1.1, fs=22).move_to(center + RIGHT * 1.9 + DOWN * 1.0)
        obs = chip("Observe\n(result)", CONTEXT_C, w=2.1, h=1.1, fs=22).move_to(center + LEFT * 1.9 + DOWN * 1.0)
        self.play(LaggedStart(FadeIn(model), FadeIn(act), FadeIn(obs), lag_ratio=0.4, run_time=1.6))
        self.beat(0.6)

        c1 = CurvedArrow(model.get_right() + RIGHT * 0.02, act.get_top(), angle=-TAU / 6, color=MUTED)
        c2 = CurvedArrow(act.get_left(), obs.get_right(), angle=-TAU / 6, color=MUTED)
        c3 = CurvedArrow(obs.get_top(), model.get_left() + LEFT * 0.02, angle=-TAU / 6, color=MUTED)
        for c in (c1, c2, c3):
            c.set_stroke(width=4)
        self.play(LaggedStart(Create(c1), Create(c2), Create(c3), lag_ratio=0.5, run_time=1.8))
        loop_title = Text("the agent loop", font_size=22, color=MUTED).move_to(center + DOWN * 0.05)
        self.play(FadeIn(loop_title), run_time=0.5)
        self.beat(0.8)

        pulse = Dot(radius=0.12, color=ACCENT).move_to(model.get_center())
        self.add(pulse)
        for _ in range(2):
            self.play(MoveAlongPath(pulse, c1), run_time=0.6)
            self.play(MoveAlongPath(pulse, c2), run_time=0.6)
            self.play(MoveAlongPath(pulse, c3), run_time=0.6)
        self.play(FadeOut(pulse), run_time=0.3)
        self.beat(0.6)

        # slide the whole loop left to open up room for the component list
        loop_group = VGroup(model, act, obs, c1, c2, c3, loop_title)
        self.play(loop_group.animate.shift(LEFT * 1.6), run_time=0.9)
        self.beat(0.3)

        # --- the harness components (right list) --------------------------- #
        comps = [
            ("Orchestration & control flow", HARNESS_C),
            ("Tools & environment", HARNESS_C),
            ("Verification & feedback", GOOD),
            ("Memory & state", MODEL_C),
            ("Sub-agents", PROMPT_C),
            ("Guardrails & retries", BAD),
        ]
        comp_rows = VGroup()
        for t, c in comps:
            d = Dot(radius=0.08, color=c)
            tx = Text(t, font_size=23, color=INK).next_to(d, RIGHT, buff=0.22)
            comp_rows.add(VGroup(d, tx))
        comp_rows.arrange(DOWN, aligned_edge=LEFT, buff=0.34).to_edge(RIGHT, buff=0.9).shift(DOWN * 0.3)
        ctitle = Text("The harness =", font_size=25, color=HARNESS_C, weight="BOLD")
        ctitle.next_to(comp_rows, UP, buff=0.3).align_to(comp_rows, LEFT)
        self.play(FadeIn(ctitle, shift=UP * 0.2), run_time=0.5)
        self.reveal(comp_rows, hold=1.15, run_time=0.45)

        # --- self-correction: verifier gate with retry --------------------- #
        gate = chip("Verify", GOOD, w=1.7, h=0.85, fs=22).next_to(act, DOWN, buff=0.65)
        a_out = harrow(act.get_bottom(), gate.get_top(), color=MUTED)
        self.play(FadeIn(gate), GrowArrow(a_out), run_time=0.7)
        x = make_cross(scale=1.0).next_to(gate, RIGHT, buff=0.2)
        retry = CurvedArrow(gate.get_left(), act.get_bottom() + LEFT * 0.3, angle=TAU / 5, color=BAD)
        retry_txt = Text("retry", font_size=18, color=BAD).next_to(retry, LEFT, buff=0.08)
        self.play(Create(x), Create(retry), FadeIn(retry_txt), run_time=1.0)
        self.beat(1.4)
        tk = make_tick(scale=1.1).move_to(x)
        self.play(Transform(x, tk), Indicate(gate, color=GOOD, scale_factor=1.1), run_time=0.9)
        self.beat(1.2)
        self.play(FadeOut(VGroup(gate, a_out, x, retry, retry_txt)), run_time=0.6)

        line = Text("The harness turns one call into a reliable, self-correcting system.",
                    font_size=27, color=INK).to_edge(DOWN, buff=0.55)
        self.play(Write(line), run_time=1.6)
        self.play(Circumscribe(line, color=HARNESS_C, run_time=1.4))
        self.beat(2.0)
        self.wipe()

    # ====================================================================== #
    # Scene 5 — Harness Pipeline Example
    # ====================================================================== #
    def scene_pipeline(self):
        header = self.section_header("Harness Pipeline — a coding agent", ACCENT)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)
        subtitle = Text("One task, flowing through the harness", font_size=26, color=MUTED)
        subtitle.next_to(header, DOWN, buff=0.35).to_edge(LEFT, buff=0.5)
        self.play(FadeIn(subtitle, shift=UP * 0.2), run_time=0.6)
        self.beat(0.6)

        # --- pipeline of stages -------------------------------------------- #
        stages = [
            ("Task", MUTED),
            ("Plan", PROMPT_C),
            ("Gather\ncontext", CONTEXT_C),
            ("Act\n(edit · run)", HARNESS_C),
            ("Verify\n(tests)", GOOD),
            ("Reflect", MODEL_C),
            ("Done", GOOD),
        ]
        boxes = VGroup(*[chip(t, c, w=1.7, h=1.1, fs=20) for t, c in stages])
        boxes.arrange(RIGHT, buff=0.55).scale_to_fit_width(12.6).move_to(UP * 0.7)
        arrows = VGroup(*[harrow(boxes[i].get_right(), boxes[i + 1].get_left(), sw=3)
                          for i in range(len(boxes) - 1)])
        self.reveal(boxes, hold=0.5, run_time=0.4, shift=UP * 0.15)
        self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.3, run_time=1.6))
        self.beat(1.0)

        # --- a task token travels the pipeline ----------------------------- #
        token = Dot(radius=0.14, color=ACCENT).move_to(boxes[0].get_center())
        glow = token.copy().set_opacity(0.35).scale(2)
        self.add(glow, token)
        glow.add_updater(lambda g: g.move_to(token))
        for i in range(len(boxes)):
            self.play(token.animate.move_to(boxes[i].get_center()),
                      boxes[i][0].animate.set_fill(opacity=0.35), run_time=0.5)
            self.beat(0.8)
            if stages[i][0].startswith("Verify"):
                break
        glow.clear_updaters()

        # --- verify FAILS -> loop back to Act -> attempt 2 ----------------- #
        verify_box, act_box = boxes[4], boxes[3]
        x = make_cross(scale=1.3).next_to(verify_box, UP, buff=0.2)
        fail_txt = Text("tests fail", font_size=20, color=BAD).next_to(x, RIGHT, buff=0.15)
        self.play(Create(x), FadeIn(fail_txt), verify_box[0].animate.set_stroke(color=BAD), run_time=0.8)
        self.beat(1.0)
        # retry drawn as a clean feedback wire BELOW the row of boxes: straight
        # down from Verify, left underneath, then a short arrow pointing UP into
        # Act's bottom. Fully explicit so the arrowhead direction is unambiguous.
        box_bottom = act_box.get_bottom()[1]
        vx = verify_box.get_center()[0]
        ax = act_box.get_center()[0]
        y_low = box_bottom - 0.7
        elbow = VMobject(stroke_color=BAD, stroke_width=3)
        elbow.set_points_as_corners([
            np.array([vx, box_bottom - 0.04, 0]),
            np.array([vx, y_low, 0]),
            np.array([ax, y_low, 0]),
        ])
        up_arrow = Arrow(np.array([ax, y_low, 0]), np.array([ax, box_bottom - 0.03, 0]),
                         buff=0, color=BAD, stroke_width=3,
                         max_tip_length_to_length_ratio=0.45, tip_length=0.2)
        loopback = VGroup(elbow, up_arrow)
        attempt = Text("attempt 2", font_size=20, color=BAD).next_to(loopback, DOWN, buff=0.12)
        self.play(Create(loopback), FadeIn(attempt), run_time=0.9)
        self.beat(0.8)
        self.play(token.animate.move_to(act_box.get_center()), run_time=0.6)
        self.play(Indicate(act_box, color=HARNESS_C, scale_factor=1.08), run_time=0.7)
        self.play(token.animate.move_to(verify_box.get_center()), run_time=0.6)
        self.beat(0.6)

        # --- verify PASSES -> Reflect -> Done ------------------------------ #
        tk = make_tick(scale=1.4).move_to(x)
        pass_txt = Text("tests pass", font_size=20, color=GOOD).move_to(fail_txt, LEFT)
        self.play(Transform(x, tk), Transform(fail_txt, pass_txt),
                  verify_box[0].animate.set_stroke(color=GOOD).set_fill(opacity=0.35), run_time=0.8)
        self.beat(0.8)
        # name the thing that just happened
        loop_note = Text("self-correction loop", font_size=20, color=GOOD).move_to(attempt, UP)
        self.play(Transform(attempt, loop_note),
                  Indicate(loopback, color=GOOD, scale_factor=1.05), run_time=1.0)
        self.beat(1.0)
        for i in (5, 6):
            self.play(token.animate.move_to(boxes[i].get_center()),
                      boxes[i][0].animate.set_fill(opacity=0.35), run_time=0.55)
            self.beat(0.6)
        self.play(Flash(boxes[6], color=GOOD, flash_radius=0.9), run_time=0.7)
        self.beat(0.6)
        self.play(Indicate(VGroup(boxes, arrows), color=ACCENT, scale_factor=1.02), run_time=1.2)
        self.beat(0.6)

        caption = Text("Plan · Retrieve · Act · Verify · Reflect  —  looped until correct.",
                       font_size=26, color=INK).to_edge(DOWN, buff=0.55)
        self.play(Write(caption), run_time=1.5)
        self.beat(2.2)
        self.wipe()

    # ====================================================================== #
    # Scene 6 — Why it matters
    # ====================================================================== #
    def scene_why(self):
        header = self.section_header("Why it matters", HARNESS_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)
        subtitle = Text("Same model — reliability climbs as you add layers",
                        font_size=26, color=MUTED)
        subtitle.next_to(header, DOWN, buff=0.35).to_edge(LEFT, buff=0.5)
        self.play(FadeIn(subtitle, shift=UP * 0.2), run_time=0.6)
        self.beat(0.6)

        # --- bar chart: reliability climbs -------------------------------- #
        base_y = -1.95
        top_y = 1.35
        base = Line(LEFT * 4.7 + UP * base_y, LEFT * 0.2 + UP * base_y).set_stroke(MUTED, 2)
        yaxis = Line(LEFT * 4.7 + UP * base_y, LEFT * 4.7 + UP * top_y).set_stroke(MUTED, 2)
        ylabel = Text("task success", font_size=20, color=MUTED).rotate(PI / 2).next_to(yaxis, LEFT, buff=0.2)
        self.play(Create(yaxis), Create(base), FadeIn(ylabel), run_time=0.9)

        # Illustrative climb — the bar heights only suggest the trend; no invented
        # figures are shown as data (the real, cited number lives in the source line).
        bar_specs = [("Prompt\nonly", 1.4, PROMPT_C),
                     ("+ Context", 2.2, CONTEXT_C),
                     ("+ Harness", 2.9, HARNESS_C)]
        xs = [-3.6, -2.3, -1.0]
        for (label, h, color), x in zip(bar_specs, xs):
            bar = Rectangle(width=0.95, height=h, stroke_width=0, fill_color=color, fill_opacity=0.85)
            bar.move_to([x, base_y + h / 2, 0])
            lab = Text(label, font_size=17, color=INK, line_spacing=0.7).next_to(bar, DOWN, buff=0.14)
            self.play(GrowFromEdge(bar, DOWN), FadeIn(lab), run_time=0.7)
            self.beat(1.4)
        illus = Text("illustrative", font_size=17, color=MUTED, slant=ITALIC)
        illus.next_to(yaxis, UP, buff=0.15).shift(RIGHT * 0.35)
        self.play(FadeIn(illus), run_time=0.5)

        # source line for the (illustrative) trend, quoted at the bottom —
        # peer-reviewed, not a blog
        source = Text(
            "Real example: a self-reflection loop lifts GPT-4 on HumanEval "
            "pass@1 from 80% to 91%   —   Reflexion, Shinn et al., NeurIPS 2023 (Table 1)",
            font_size=15, color=MUTED,
        )
        if source.width > 13.6:
            source.scale(13.6 / source.width)
        source.to_edge(DOWN, buff=0.16)
        self.play(FadeIn(source), run_time=0.6)
        self.beat(0.4)

        # --- benefit list (right), checkmarks on the right ----------------- #
        benefits = [
            "Reliability ↑ — fewer silent failures",
            "Scales to long, complex tasks",
            "Model-agnostic — swap the model, keep the harness",
            "Autonomy — self-corrects without a human",
            "Control over cost & latency",
        ]
        rows = VGroup()
        for b in benefits:
            tx = Text(b, font_size=19, color=INK)
            tk = make_tick(scale=0.7).next_to(tx, RIGHT, buff=0.25)
            rows.add(VGroup(tx, tk))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.34).to_edge(RIGHT, buff=0.6).shift(UP * 0.12)
        self.reveal(rows, hold=1.4, run_time=0.5)

        # --- punchline ----------------------------------------------------- #
        punch = Text("The moat isn't the model — it's the harness around it.",
                     font_size=26, color=INK, weight="BOLD").to_edge(DOWN, buff=0.68)
        self.play(Write(punch), run_time=1.6)
        self.play(Circumscribe(punch, color=HARNESS_C, run_time=1.4))
        self.beat(1.8)

        # --- recap the nested layers as a closing bookend ------------------ #
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        d = self.build_layers(scale=0.85)
        d["group"].shift(UP * 0.3)
        self.play(LaggedStart(Create(d["harness"]), Create(d["context"]),
                              Create(d["prompt"]), Create(d["core"]),
                              lag_ratio=0.3, run_time=1.8),
                  FadeIn(VGroup(d["hl"], d["cl"], d["pl"], d["core_label"])))
        recap = Text("Prompt · Context · Harness", font_size=30, color=INK)
        recap.next_to(d["harness"], DOWN, buff=0.5)
        self.play(Write(recap), run_time=1.2)
        self.play(Indicate(d["prompt"], color=PROMPT_C, scale_factor=1.03),
                  Indicate(d["context"], color=CONTEXT_C, scale_factor=1.03),
                  Indicate(d["harness"], color=HARNESS_C, scale_factor=1.03), run_time=1.4)
        self.beat(2.0)
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_what()
        self.scene_prompt()
        self.scene_context()
        self.scene_harness()
        self.scene_pipeline()
        self.scene_why()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_HarnessBase):
    def construct(self):
        self.play_intro()


class What(_HarnessBase):
    def construct(self):
        self.scene_what()


class Prompt(_HarnessBase):
    def construct(self):
        self.scene_prompt()


class Context(_HarnessBase):
    def construct(self):
        self.scene_context()


class Harness(_HarnessBase):
    def construct(self):
        self.scene_harness()


class Pipeline(_HarnessBase):
    def construct(self):
        self.scene_pipeline()


class Why(_HarnessBase):
    def construct(self):
        self.scene_why()


class Outro(_HarnessBase):
    def construct(self):
        self.play_outro()


class HarnessEngineering(_HarnessBase):
    """The whole ~6-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    HarnessEngineering().render()

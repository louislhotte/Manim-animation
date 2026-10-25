"""How AI Benchmarks Work — a short, house-style explainer (no voice-over).

A benchmark is just a standardized exam for a model: a fixed set of tasks, a
fixed way to grade them, and one score you can compare across models. This film
builds that idea and then shows the two families of grading that matter, with a
deep dive on the one that made agents interesting — running the code.

    1. Whatis    -- a benchmark = a fixed task set + a fixed grader + one score,
                    so every model sits the same exam and the scores compare.
    2. Tour      -- four real benchmarks, four different skills: MMLU (knowledge),
                    GSM8K / MATH (math), HumanEval (writing code), SWE-bench
                    (fixing real bugs) -- and the two ways they are graded.
    3. Grading   -- the two "check the answer" styles up close: multiple-choice
                    accuracy (a 20-question grid -> 85%) and exact match on a
                    worked GSM8K problem (48 + 24 = 72).
    4. SweBench  -- the execution pipeline: a real GitHub issue -> the model
                    writes a patch -> apply it -> run the project's own hidden
                    tests -> resolved only if they pass. Score = % of 500 solved.
    5. PassK     -- one try or many: pass@k = 1 - (1 - p)^k. A model right 40% of
                    the time hits 99% at pass@10, so always ask which k was used.
    6. Arena     -- open-ended tasks have no answer to match: show two responses,
                    let a human (or a model judge) vote, and rate models by Elo.
    7. Progress  -- SWE-bench Verified, best score over time: 33% (Jun 2024) ->
                    49% (Oct 2024) -> ~72% (2025) -> ~93% (2026). Older tests
                    (MMLU, GSM8K) are already near human level and saturated.
    8. Catch     -- why a score is only a proxy: contamination (the test leaks
                    into training), Goodhart's law (a target stops being a good
                    measure), and saturation.

Numbers on screen are real, published milestones (see README for sources) or
clearly-labelled illustrations. The GSM8K answer (48 + 24 = 72), the SWE-bench
Verified size (500), the accuracy (17/20) and pass@k values are asserted.

Everything uses ``Text`` (Pango) / Menlo for code, never ``Tex`` -- so it needs
no LaTeX toolchain. Scenes render alone (``Whatis``, ``Tour``, ``Grading``,
``SweBench``, ``PassK``, ``Arena``, ``Progress``, ``Catch``, ``Intro``,
``Outro``) or as one film (``AIBenchmarks``).

Env knobs:
    BM_QUICK=1   shorten every hold for a fast sanity render
    BM_DELAY=x   override the reading-hold multiplier
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

QUICK = os.environ.get("BM_QUICK") == "1"
# One knob for pacing: every reading "hold" is scaled by this. QUICK collapses
# the holds for fast iteration; otherwise it sets a comfortable reading rhythm.
DELAY = float(os.environ.get("BM_DELAY", "0.3" if QUICK else "2.2"))
# Extra hold on each scene's final frame, before it wipes to the next scene.
END_HOLD = 0.2 if QUICK else 2.0

# ---- palette (shared house style) ---------------------------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / axes
GRID = "#232A38"        # faint gridlines / panel fills
PANEL = "#0B0E14"       # code-panel fill (a touch darker than BG)

GOLD = "#FFD166"        # rules / underlines / the score
OK_C = "#3DD68C"        # pass / correct  (green)
BAD_C = "#FF5C5C"       # fail / wrong    (red)

KNOW_C = "#5B8DEF"      # MMLU  — knowledge      (blue)
MATH_C = "#C77DFF"      # GSM8K / MATH           (violet)
CODE_C = "#4CC9F0"      # HumanEval — write code (cyan)
SWE_C = "#FF8C42"       # SWE-bench — fix a bug  (amber)

# ---- real / asserted numbers --------------------------------------------- #
GSM8K_ANSWER = 48 + 48 // 2                 # Natalia: 48 in April, half in May
assert GSM8K_ANSWER == 72, GSM8K_ANSWER
SWE_N = 500                                 # SWE-bench Verified task count
# SWE-bench Verified, best published score over time (see README for sources).
PROGRESS = [("Jun 2024", 33), ("Oct 2024", 49), ("2025", 72), ("2026", 93)]
assert [v for _, v in PROGRESS] == sorted(v for _, v in PROGRESS)


# ---- crisp text: render big, scale down (Pango mangles small sizes) ------- #
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


def mono(text, font_size=20, color=INK, **kw):
    """Monospace text (Menlo), routed through the crisp-text shadow above."""
    return Text(text, font_size=font_size, color=color, font="Menlo", **kw)


# ========================================================================== #
# Small reusable pieces
# ========================================================================== #
def bullet(text, color=INK, fs=24, dot=GOLD, dot_r=0.06):
    d = Dot(radius=dot_r, color=dot)
    t = Text(text, font_size=fs, color=color)
    t.next_to(d, RIGHT, buff=0.22)
    d.align_to(t, UP).shift(DOWN * 0.11)
    return VGroup(d, t)


def arr(start, end, color=MUTED, sw=3.0, buff=0.12):
    """Straight arrow. ALWAYS pass explicit points (.get_right()/.get_left()),
    never a bare compound Mobject — Manim's boundary search on a rect+text group
    resolves off-centre and the arrow renders diagonal (house gotcha §5)."""
    return Arrow(start, end, buff=buff, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.28, tip_length=0.2)


def check(color=OK_C, fs=26):
    return Text("✓", font_size=fs, color=color, weight="BOLD")


def cross(color=BAD_C, fs=26):
    return Text("✗", font_size=fs, color=color, weight="BOLD")


def play_tri(color=SWE_C, r=0.11):
    return Polygon([-r, r, 0], [-r, -r, 0], [r * 1.3, 0, 0],
                   stroke_width=0, fill_color=color, fill_opacity=1.0)


def pill(text, color, fs=18):
    t = Text(text, font_size=fs, color=color, weight="BOLD")
    box = RoundedRectangle(width=t.width + 0.3, height=t.height + 0.2,
                           corner_radius=0.12, stroke_color=color, stroke_width=2,
                           fill_color=color, fill_opacity=0.14).move_to(t)
    return VGroup(box, t)


# ========================================================================== #
class _BMBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # ---- timing helpers --------------------------------------------------- #
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.25))

    def wipe(self, rt=0.7):
        self.wait(END_HOLD)
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    def section_header(self, label, color):
        txt = Text(label, font_size=34, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(txt.get_left(), txt.get_right()).next_to(txt, DOWN, buff=0.12)
        line.set_stroke(color=color, width=4)
        return VGroup(txt, line)

    def say(self, text, color=INK, fs=26, y=-3.35, weight=NORMAL):
        cap = Text(text, font_size=fs, color=color, weight=weight)
        if cap.width > 12.6:
            cap.scale_to_fit_width(12.6)
        cap.move_to([0, y, 0])
        return cap

    def clamp_w(self, mob, w=6.6):
        if mob.width > w:
            mob.scale_to_fit_width(w)
        return mob

    # ---- house-style intro / outro cards ---------------------------------- #
    def introduction(self, title1, title2):
        header = Text(title1, font_size=52, color=INK, weight="BOLD")
        header.set(width=min(11.0, header.width))
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        writer = Text("Created by Ptolémé", font_size=28, color=KNOW_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.card_wait(0.7)
        sub = Text(title2, font_size=32, color=MUTED)
        sub.set(width=min(11.5, sub.width)).move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.card_wait(2.0)
        return VGroup(header, writer, line)

    def play_intro(self):
        group = self.introduction(
            "How AI Benchmarks Work",
            "Giving every model the same exam, then grading it",
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
        writer = Text("Created by Ptolémé", font_size=28, color=KNOW_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.5)
        self.card_wait(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.1)
        self.card_wait(2.2)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.3)
        self.card_wait(0.5)

    # ---- a Menlo code / diff panel ---------------------------------------- #
    def code_panel(self, lines, title="patch.diff", fs=20, min_w=0.0):
        """lines: list of (text, kind); kind in ctx/del/add/head."""
        colours = {"ctx": INK, "del": BAD_C, "add": OK_C, "head": MUTED}
        body = VGroup(*[mono(s, font_size=fs, color=colours[k]) for s, k in lines])
        body.arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        w = max(body.width, min_w) + 0.6
        h = body.height + 0.95
        bg = RoundedRectangle(width=w, height=h, corner_radius=0.12,
                              stroke_color=GRID, stroke_width=2,
                              fill_color=PANEL, fill_opacity=1.0)
        bar = Rectangle(width=w, height=0.44, stroke_width=0,
                        fill_color=GRID, fill_opacity=1.0)
        bar.move_to(bg).align_to(bg, UP)
        dots = VGroup(*[Dot(radius=0.055, color=c)
                        for c in ("#FF5F56", "#FFBD2E", "#27C93F")]).arrange(RIGHT, buff=0.1)
        dots.next_to(bar.get_left(), RIGHT, buff=0.22)
        ttl = mono(title, font_size=15, color=MUTED).next_to(dots, RIGHT, buff=0.35)
        body.next_to(bar, DOWN, buff=0.22).align_to(bg, LEFT).shift(RIGHT * 0.34)
        return VGroup(bg, bar, dots, ttl, body)

    # ---- a live counting number (ValueTracker + become, no DecimalNumber) - #
    def count_label(self, tracker, fmt, fs, color, center, weight="BOLD"):
        """A number that follows a ValueTracker via ``become`` (DecimalNumber
        rejects ``weight=``). Add with ``self.add`` and animate the tracker; do
        not FadeIn a live updater label — animate the tracker from its start."""
        center = np.array(center, dtype=float)

        def mk():
            return Text(fmt(tracker.get_value()), font_size=fs, color=color,
                        weight=weight).move_to(center)

        lbl = mk()
        lbl.add_updater(lambda m: m.become(mk()))
        return lbl

    # ====================================================================== #
    # Scene 1 — What is a benchmark?
    # ====================================================================== #
    def scene_whatis(self):
        header = self.section_header("What is a benchmark?", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # the one-line definition
        defn = Text(
            "A benchmark is a fixed set of tasks, a fixed way to grade them, "
            "and one score.",
            font_size=27, color=INK,
        )
        self.clamp_w(defn, 12.4).move_to([0, 2.35, 0])
        self.play(FadeIn(defn, shift=UP * 0.1), run_time=0.8)
        self.beat(1.6)

        # the pipeline: task set -> model -> grader -> score
        def node(title, sub, color):
            t = Text(title, font_size=23, color=color, weight="BOLD")
            s = Text(sub, font_size=16, color=MUTED)
            inner = VGroup(t, s).arrange(DOWN, buff=0.12)
            box = RoundedRectangle(width=inner.width + 0.6, height=inner.height + 0.5,
                                   corner_radius=0.14, stroke_color=color,
                                   stroke_width=2.5, fill_color=color,
                                   fill_opacity=0.09).move_to(inner)
            return VGroup(box, inner)

        n_tasks = node("Task set", "500 fixed questions", GOLD)
        n_model = node("Model", "the system under test", KNOW_C)
        n_grade = node("Grader", "same rule every time", MATH_C)
        n_score = node("Score", "one number: 72%", OK_C)
        row = VGroup(n_tasks, n_model, n_grade, n_score).arrange(RIGHT, buff=0.72)
        row.move_to([0, 0.85, 0])
        arrows = VGroup(*[arr(row[i].get_right(), row[i + 1].get_left())
                          for i in range(3)])

        self.play(FadeIn(n_tasks, shift=UP * 0.1), run_time=0.5)
        for i in range(1, 4):
            self.play(GrowArrow(arrows[i - 1]),
                      FadeIn(row[i], shift=RIGHT * 0.15), run_time=0.55)
        self.beat(1.6)

        # run every model through the SAME pipeline -> a comparable leaderboard
        cap = self.say("Run every model through the same pipeline, and the scores "
                       "line up into a leaderboard.", color=INK)

        def lb_row(name, val, color, y):
            lab = Text(name, font_size=22, color=INK, weight="BOLD")
            lab.move_to([-3.7, y, 0])
            track = RoundedRectangle(width=5.2, height=0.34, corner_radius=0.17,
                                     stroke_color=GRID, stroke_width=1.5,
                                     fill_color=GRID, fill_opacity=0.6)
            track.move_to([0.1, y, 0]).align_to([-2.5, y, 0], LEFT)
            fill = RoundedRectangle(width=max(0.34, 5.2 * val / 100), height=0.34,
                                    corner_radius=0.17, stroke_width=0,
                                    fill_color=color, fill_opacity=1.0)
            fill.align_to(track, LEFT).set_y(y)
            num = Text(f"{val}%", font_size=22, color=color, weight="BOLD")
            num.next_to(track, RIGHT, buff=0.25)
            return VGroup(lab, track, fill, num)

        r1 = lb_row("Model A", 82, OK_C, -0.4)
        r2 = lb_row("Model B", 74, KNOW_C, -1.1)
        r3 = lb_row("Model C", 61, MATH_C, -1.8)
        board = VGroup(r1, r2, r3)
        note = Text("illustrative scores", font_size=15, color=MUTED, slant=ITALIC)
        note.next_to(board, DOWN, buff=0.2).align_to(board, RIGHT)

        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.2) for r in board],
                              lag_ratio=0.3), run_time=1.4)
        self.play(FadeIn(note), run_time=0.4)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.6)
        self.beat(2.2)
        self.wipe()

    # ====================================================================== #
    # Scene 2 — A tour: four skills, two ways to grade
    # ====================================================================== #
    def scene_tour(self):
        header = self.section_header("Different tests, different skills", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        def bench_card(name, name_c, what, task, grade, grade_c):
            nm = Text(name, font_size=26, color=name_c, weight="BOLD")
            wt = Text(what, font_size=19, color=INK)
            tk = Text(task, font_size=17, color=MUTED)
            # grading tag with a tiny glyph
            gl = (check(grade_c, 20) if grade == "check the answer"
                  else play_tri(grade_c, 0.09))
            gt = Text(grade, font_size=17, color=grade_c, weight="BOLD")
            tag = VGroup(gl, gt).arrange(RIGHT, buff=0.16)
            inner = VGroup(nm, wt, tk, tag).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
            box = RoundedRectangle(width=5.55, height=inner.height + 0.55,
                                   corner_radius=0.16, stroke_color=name_c,
                                   stroke_width=2.5, fill_color=name_c,
                                   fill_opacity=0.07)
            inner.move_to(box).align_to(box, LEFT).shift(RIGHT * 0.32)
            return VGroup(box, inner)

        c_mmlu = bench_card("MMLU", KNOW_C, "Broad knowledge, 57 subjects",
                            "Task: multiple choice, pick A–D", "check the answer", KNOW_C)
        c_math = bench_card("GSM8K / MATH", MATH_C, "Math word problems",
                            "Task: produce the final answer", "check the answer", MATH_C)
        c_he = bench_card("HumanEval", CODE_C, "Write a function from a spec",
                          "Task: generate the code", "run the code", CODE_C)
        c_swe = bench_card("SWE-bench", SWE_C, "Fix a real GitHub issue",
                           "Task: produce a working patch", "run the code", SWE_C)

        grid = VGroup(VGroup(c_mmlu, c_math).arrange(RIGHT, buff=0.55),
                      VGroup(c_he, c_swe).arrange(RIGHT, buff=0.55)) \
            .arrange(DOWN, buff=0.45).move_to([0, 0.35, 0])
        for card in (c_mmlu, c_math, c_he, c_swe):
            self.play(FadeIn(card, shift=UP * 0.12), run_time=0.55)
        self.beat(2.0)

        cap = self.say("Two families of grading: check the answer, or run the code.",
                       color=INK, weight=BOLD)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.6)
        # nudge the grading tags
        self.play(Indicate(c_math[1][3], color=MATH_C, scale_factor=1.12),
                  Indicate(c_swe[1][3], color=SWE_C, scale_factor=1.12), run_time=1.0)
        self.beat(2.2)
        self.wipe()

    # ====================================================================== #
    # Scene 3 — SWE-bench: grading by running the code
    # ====================================================================== #
    def scene_swebench(self):
        header = self.section_header("SWE-bench: graded by running the code", SWE_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # --- bridge from the Grading scene: matching text won't work here --- #
        cap0 = self.say("Checking a stored answer was easy. A whole code fix is not: "
                        "it has millions of correct forms.", color=INK)
        line2 = Text("So we do not match text. We run the project's own tests.",
                     font_size=27, color=INK, weight="BOLD").move_to([0, 0.35, 0])
        self.play(FadeIn(cap0, shift=UP * 0.1), run_time=0.6)
        self.beat(1.6)
        self.play(FadeIn(line2, shift=UP * 0.1), run_time=0.6)
        self.beat(1.8)
        self.play(FadeOut(cap0), FadeOut(line2), run_time=0.5)

        # --- the stepper --------------------------------------------------- #
        steps = ["Issue", "Patch", "Apply", "Run tests"]
        chips = VGroup()
        for i, s in enumerate(steps):
            lab = Text(f"{i + 1}. {s}", font_size=20, color=MUTED, weight="BOLD")
            box = RoundedRectangle(width=lab.width + 0.5, height=0.62,
                                   corner_radius=0.14, stroke_color=GRID,
                                   stroke_width=2, fill_color=GRID,
                                   fill_opacity=0.35).move_to(lab)
            chips.add(VGroup(box, lab))
        chips.arrange(RIGHT, buff=0.62).move_to([0, 2.35, 0])
        step_arrows = VGroup(*[arr(chips[i].get_right(), chips[i + 1].get_left(),
                                   sw=2.5, buff=0.08) for i in range(3)])
        self.play(FadeIn(chips), *[GrowArrow(a) for a in step_arrows], run_time=0.8)

        def light(k, color):
            box, lab = chips[k]
            return AnimationGroup(
                box.animate.set_stroke(color, width=3).set_fill(color, opacity=0.16),
                lab.animate.set_color(color))

        stage_c = [0, -0.55, 0]

        # step 1 — the real GitHub issue
        self.play(light(0, SWE_C), run_time=0.4)
        repo = mono("django/django", font_size=20, color=INK)
        tag = pill("SWE-bench task", SWE_C, fs=15)
        top = VGroup(repo, tag).arrange(RIGHT, buff=0.35)
        title = Text("TimeField drops microseconds when serialized",
                     font_size=22, color=INK, weight="BOLD")
        b1 = mono("Expected:  12:30:45.123456", font_size=18, color=MUTED)
        b2 = mono("Actual:    12:30:45", font_size=18, color=MUTED)
        body = VGroup(top, title, b1, b2).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        ibox = RoundedRectangle(width=body.width + 0.7, height=body.height + 0.6,
                                corner_radius=0.16, stroke_color=SWE_C,
                                stroke_width=2, fill_color=SWE_C, fill_opacity=0.06)
        body.move_to(ibox)
        issue = VGroup(ibox, body).move_to(stage_c)
        cap = self.say("Step 1: a real, unsolved bug report from a GitHub project.",
                       color=SWE_C)
        self.play(FadeIn(issue, shift=UP * 0.12), FadeIn(cap), run_time=0.8)
        self.beat(2.0)

        # step 2 — the model writes a patch
        self.play(light(1, SWE_C), FadeOut(issue), run_time=0.5)
        patch = self.code_panel([
            ("  def serialize(self, value):", "ctx"),
            ("-     return value.isoformat()", "del"),
            ("+     if value.microsecond:", "add"),
            ("+         return value.isoformat(\"microseconds\")", "add"),
            ("+     return value.isoformat()", "add"),
        ], title="patch.diff", fs=19).move_to(stage_c)
        cap2 = self.say("Step 2: the model reads the repo and writes a patch, "
                        "a diff over the source.", color=INK)
        self.play(ReplacementTransform(cap, cap2), FadeIn(patch, shift=UP * 0.1),
                  run_time=0.8)
        self.beat(2.2)

        # step 3 — apply to a fresh checkout
        self.play(light(2, SWE_C), patch.animate.scale(0.82).move_to([-3.4, -0.55, 0]),
                  run_time=0.6)
        applyln = mono("$ git apply patch.diff", font_size=19, color=INK)
        okln = VGroup(check(OK_C, 22),
                      Text("applied to a fresh checkout", font_size=19, color=MUTED)) \
            .arrange(RIGHT, buff=0.2)
        appl = VGroup(applyln, okln).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        appl.move_to([3.0, -0.55, 0])
        cap3 = self.say("Step 3: apply the patch to a clean copy of the project.",
                        color=INK)
        self.play(ReplacementTransform(cap2, cap3), FadeIn(appl, shift=RIGHT * 0.15),
                  run_time=0.8)
        self.beat(1.8)

        # step 4 — run the project's own hidden tests
        self.play(light(3, SWE_C), FadeOut(patch), FadeOut(appl), run_time=0.5)

        def test_row(name, ok):
            g = check(OK_C, 22) if ok else cross(BAD_C, 22)
            t = mono(name, font_size=19, color=INK)
            return VGroup(g, t).arrange(RIGHT, buff=0.24)

        # FAIL_TO_PASS: the bug's own tests (must flip failing -> passing)
        f2p = VGroup(test_row("test_time_microseconds", False),
                     test_row("test_timefield_json", False)) \
            .arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        f2p_lab = Text("must flip: fail → pass", font_size=17, color=SWE_C, weight="BOLD")
        f2p_lab.next_to(f2p, UP, buff=0.2).align_to(f2p, LEFT)
        colA = VGroup(f2p_lab, f2p).arrange(DOWN, aligned_edge=LEFT, buff=0.24)
        # PASS_TO_PASS: unrelated tests (must stay passing)
        p2p = VGroup(test_row("test_backward_compat", True),
                     test_row("test_date_serialize", True),
                     test_row("test_null_values", True)) \
            .arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        p2p_lab = Text("must stay: pass → pass", font_size=17, color=MUTED, weight="BOLD")
        p2p_lab.next_to(p2p, UP, buff=0.2).align_to(p2p, LEFT)
        colB = VGroup(p2p_lab, p2p).arrange(DOWN, aligned_edge=LEFT, buff=0.24)
        cols = VGroup(colA, colB).arrange(RIGHT, buff=1.3, aligned_edge=UP)
        cols.move_to([0, -0.55, 0])

        cap4 = self.say("Step 4: run the project's own test suite. The bug's tests "
                        "start red.", color=BAD_C)
        self.play(ReplacementTransform(cap3, cap4), FadeIn(cols, shift=UP * 0.1),
                  run_time=0.9)
        self.beat(1.8)

        # flip the failing tests to green
        flips = []
        for row in f2p:
            new = check(OK_C, 22).move_to(row[0])
            flips.append(Transform(row[0], new))
        cap5 = self.say("The patch turns them green, and nothing else breaks. "
                        "Only then is the issue resolved.", color=OK_C, weight=BOLD)
        self.play(ReplacementTransform(cap4, cap5), *flips, run_time=1.0)
        stamp = pill("RESOLVED ✓", OK_C, fs=24)
        stamp[1].set_color(OK_C)
        stamp.scale(1.15).move_to([0, -2.35, 0])
        self.play(GrowFromCenter(stamp), run_time=0.6)
        self.beat(2.2)

        # the score
        self.play(FadeOut(cols), FadeOut(stamp), ReplacementTransform(cap5, self.say("")),
                  run_time=0.5)
        score = Text(f"Score  =  issues fully resolved  /  {SWE_N} tasks",
                     font_size=30, color=INK, weight="BOLD").move_to([0, 0.1, 0])
        sub = Text("No partial credit. The tests decide, not a human judge.",
                   font_size=24, color=MUTED).next_to(score, DOWN, buff=0.4)
        self.play(FadeIn(score, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(sub, shift=UP * 0.1), run_time=0.6)
        self.beat(2.4)
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Progress: SWE-bench Verified over time
    # ====================================================================== #
    def scene_progress(self):
        header = self.section_header("Progress: SWE-bench Verified", SWE_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        base_y = -1.85
        xs = [-4.6, -1.55, 1.5, 4.55]
        max_h, w = 3.5, 1.25
        colors = [MUTED, KNOW_C, MATH_C, OK_C]
        axis = Line([-6.2, base_y, 0], [6.2, base_y, 0]).set_stroke(MUTED, 2)
        ylab = Text("% of issues resolved", font_size=18, color=MUTED)
        ylab.rotate(PI / 2).move_to([-6.6, base_y + max_h / 2, 0])
        self.play(Create(axis), FadeIn(ylab), run_time=0.6)

        for (yr, val), x, col in zip(PROGRESS, xs, colors):
            h = max_h * val / 100
            bar = RoundedRectangle(width=w, height=h, corner_radius=0.06,
                                   stroke_width=0, fill_color=col, fill_opacity=1.0)
            bar.move_to([x, base_y + h / 2, 0])
            yrl = Text(yr, font_size=20, color=INK).next_to([x, base_y, 0], DOWN, buff=0.22)
            tr = ValueTracker(0)
            pnum = self.count_label(tr, lambda v: f"{int(round(v))}%", 26, col,
                                    [x, base_y + h + 0.34, 0])
            self.add(pnum)
            self.play(GrowFromEdge(bar, DOWN), FadeIn(yrl),
                      tr.animate.set_value(val), run_time=0.75)
        self.beat(1.4)

        cap = self.say("In under two years the best score went from a third of the "
                       "issues to nearly all of them.", color=INK, weight=BOLD)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.7)
        self.beat(2.2)

        # older benchmarks are already saturated
        note = Text("Older tests are already maxed out: MMLU and GSM8K sit near "
                    "90–100%, close to human level.", font_size=22, color=MATH_C)
        self.clamp_w(note, 12.4).move_to([0, 2.35, 0])
        self.play(ReplacementTransform(cap, self.say("So the field keeps building "
                  "harder tests to tell the best models apart.", color=INK, weight=BOLD)),
                  FadeIn(note, shift=DOWN * 0.1), run_time=0.8)
        self.beat(2.4)
        self.wipe()

    # ====================================================================== #
    # Scene 5 — The catch: a score is only a proxy
    # ====================================================================== #
    def scene_catch(self):
        header = self.section_header("The catch", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        def catch_card(title, color, body):
            box = RoundedRectangle(width=11.6, height=1.05, corner_radius=0.14,
                                   stroke_color=color, stroke_width=2.5,
                                   fill_color=color, fill_opacity=0.07)
            nm = Text(title, font_size=23, color=color, weight="BOLD")
            nm.align_to(box, LEFT).shift(RIGHT * 0.45).set_y(box.get_y())
            div = Line(box.get_top(), box.get_bottom()).set_stroke(color, 1.5, opacity=0.55)
            div.scale(0.62).set_x(box.get_left()[0] + 3.25)
            bd = Text(body, font_size=20, color=INK)
            if bd.width > 7.55:
                bd.scale_to_fit_width(7.55)
            bd.align_to(box, LEFT).shift(RIGHT * 3.55).set_y(box.get_y())
            return VGroup(box, nm, div, bd)

        c1 = catch_card("Contamination", BAD_C,
                        "The test leaks into training data, so the score is just memory.")
        c2 = catch_card("Goodhart's law", SWE_C,
                        "When a measure becomes a target, it stops being a good measure.")
        c3 = catch_card("Saturation", MATH_C,
                        "Once every model scores near 100%, the test can't tell them apart.")
        row = VGroup(c1, c2, c3).arrange(DOWN, buff=0.32).move_to([0, 0.5, 0])
        for c in row:
            self.play(FadeIn(c, shift=UP * 0.14), run_time=0.6)
            self.beat(1.5)
        self.beat(0.8)

        punch = Text("A benchmark is a proxy for a skill, not the skill itself.",
                     font_size=30, color=GOLD, weight="BOLD")
        self.clamp_w(punch, 12.0).move_to([0, -2.6, 0])
        self.play(FadeIn(punch, shift=UP * 0.12), run_time=0.8)
        self.beat(2.4)
        self.wipe()

    # ====================================================================== #
    # Scene — Grading, up close: the two "check the answer" styles
    # ====================================================================== #
    def scene_grading(self):
        header = self.section_header("Grading, up close", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # ---- Part 1: multiple choice -> accuracy (MMLU) ------------------ #
        sub1 = Text("Multiple choice: grading is just counting.",
                    font_size=25, color=KNOW_C).move_to([0, 2.5, 0])
        self.play(FadeIn(sub1, shift=DOWN * 0.1), run_time=0.6)

        q = Text("Which organelle makes most of the ATP?", font_size=21, color=INK)
        opts = [("A", "Nucleus", False), ("B", "Ribosome", False),
                ("C", "Mitochondrion", True), ("D", "Golgi apparatus", False)]
        orows, correct_row = VGroup(), None
        for letter, label, ok in opts:
            r = VGroup(Text(f"{letter}.", font_size=20, color=MUTED, weight="BOLD"),
                       Text(label, font_size=20, color=INK)).arrange(RIGHT, buff=0.2)
            orows.add(r)
            if ok:
                correct_row = r
        orows.arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        qblock = VGroup(q, orows).arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        qbox = RoundedRectangle(width=qblock.width + 0.7, height=qblock.height + 0.6,
                                corner_radius=0.16, stroke_color=KNOW_C, stroke_width=2,
                                fill_color=KNOW_C, fill_opacity=0.06)
        qblock.move_to(qbox)
        card = VGroup(qbox, qblock).move_to([-3.55, 0.2, 0])
        self.play(FadeIn(card, shift=UP * 0.1), run_time=0.7)
        self.beat(1.4)
        pick = SurroundingRectangle(correct_row, color=OK_C, buff=0.12,
                                    corner_radius=0.1).set_stroke(width=4)
        tick = check(OK_C, 24).next_to(pick, RIGHT, buff=0.2)
        self.play(Create(pick), FadeIn(tick, shift=LEFT * 0.1), run_time=0.7)
        self.beat(1.2)

        # accuracy grid: 20 questions, 17 right / 3 wrong
        wrong = {4, 11, 17}
        assert 20 - len(wrong) == 17
        tiles = VGroup()
        for i in range(20):
            ok = i not in wrong
            col = OK_C if ok else BAD_C
            sq = RoundedRectangle(width=0.52, height=0.52, corner_radius=0.1,
                                  stroke_color=col, stroke_width=2,
                                  fill_color=col, fill_opacity=0.16)
            g = (check(col, 20) if ok else cross(col, 20)).scale(0.9).move_to(sq)
            tiles.add(VGroup(sq, g))
        for i, t in enumerate(tiles):
            r, c = divmod(i, 5)
            t.move_to([3.45 + (c - 2) * 0.66, 1.35 - r * 0.66, 0])
        grid_lbl = Text("the whole 20-question test", font_size=17, color=MUTED)
        grid_lbl.next_to(tiles, UP, buff=0.2)
        self.play(FadeIn(grid_lbl), LaggedStart(*[GrowFromCenter(t) for t in tiles],
                                                lag_ratio=0.08), run_time=1.8)
        self.beat(1.0)

        acc = ValueTracker(0)
        base = Text("Accuracy  17 / 20  =  ", font_size=26, color=INK, weight="BOLD")
        num = self.count_label(acc, lambda v: f"{int(round(v))}%", 26, OK_C, ORIGIN)
        prow = VGroup(base, num).arrange(RIGHT, buff=0.1).move_to([3.45, -1.75, 0])
        num.clear_updaters()
        num.add_updater(lambda m: m.become(
            Text(f"{int(round(acc.get_value()))}%", font_size=26, color=OK_C,
                 weight="BOLD").next_to(base, RIGHT, buff=0.1)))
        self.add(num)
        self.play(FadeIn(base), run_time=0.4)
        self.play(acc.animate.set_value(85), run_time=1.2)
        self.beat(2.0)

        num.clear_updaters()
        self.play(FadeOut(VGroup(sub1, card, pick, tick, tiles, grid_lbl, base, num)),
                  run_time=0.6)

        # ---- Part 2: exact match (GSM8K) --------------------------------- #
        sub2 = Text("Exact match: compare the final answer to the stored one.",
                    font_size=25, color=MATH_C).move_to([0, 2.5, 0])
        prob = Text("Natalia sold 48 clips in April, then half as many in May. "
                    "How many did she sell in total?", font_size=23, color=INK)
        self.clamp_w(prob, 11.5)
        pbox = RoundedRectangle(width=prob.width + 0.6, height=prob.height + 0.5,
                                corner_radius=0.14, stroke_color=MATH_C, stroke_width=2,
                                fill_color=MATH_C, fill_opacity=0.06)
        prob.move_to(pbox)
        pcard = VGroup(pbox, prob).move_to([0, 1.35, 0])
        self.play(FadeIn(sub2, shift=DOWN * 0.1), FadeIn(pcard, shift=UP * 0.1),
                  run_time=0.8)
        self.beat(1.6)

        def chipn(label, value, color):
            lab = Text(label, font_size=17, color=MUTED)
            val = Text(str(value), font_size=30, color=color, weight="BOLD")
            inner = VGroup(lab, val).arrange(DOWN, buff=0.08)
            box = RoundedRectangle(width=inner.width + 0.6, height=inner.height + 0.4,
                                   corner_radius=0.12, stroke_color=color,
                                   stroke_width=2, fill_color=color, fill_opacity=0.1)
            inner.move_to(box)
            return VGroup(box, inner)

        cA = chipn("April", 48, INK)
        plus = Text("+", font_size=30, color=MUTED)
        cM = chipn("May (half)", 24, INK)
        eqs = Text("=", font_size=30, color=MUTED)
        cT = chipn("Total", 72, MATH_C)
        calc = VGroup(cA, plus, cM, eqs, cT).arrange(RIGHT, buff=0.3).move_to([0, -0.35, 0])
        self.play(FadeIn(cA, shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(plus), FadeIn(cM, shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(eqs), FadeIn(cT, shift=UP * 0.1), run_time=0.5)
        self.beat(1.4)

        mout = mono("model: \"The answer is 72.\"", font_size=20, color=INK)
        gold = mono(f"gold: {GSM8K_ANSWER}", font_size=20, color=INK)
        tick2 = check(OK_C, 24)
        mrow = VGroup(mout, gold, tick2).arrange(RIGHT, buff=0.5).move_to([0, -1.95, 0])
        self.play(FadeIn(mrow, shift=UP * 0.1), run_time=0.7)
        self.beat(1.2)
        cap = self.say("Both styles just compare to a stored answer.",
                       color=INK, weight=BOLD)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.6)
        self.beat(2.2)
        self.wipe()

    # ====================================================================== #
    # Scene — One try, or many? (pass@k)
    # ====================================================================== #
    def scene_passk(self):
        header = self.section_header("One try, or many?", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        sub = Text("Let the model attempt the same coding task several times.",
                   font_size=25, color=CODE_C).move_to([0, 2.55, 0])
        self.play(FadeIn(sub, shift=DOWN * 0.1), run_time=0.6)

        # five attempts; passes at #2 and #5  ->  p = 2/5 = 0.4
        passes = [False, True, False, False, True]
        p = sum(passes) / len(passes)
        assert abs(p - 0.4) < 1e-9
        cards = VGroup()
        for i, ok in enumerate(passes):
            col = OK_C if ok else BAD_C
            lab = Text(f"try {i + 1}", font_size=18, color=INK)
            mark = check(col, 26) if ok else cross(col, 26)
            inner = VGroup(lab, mark).arrange(DOWN, buff=0.14)
            box = RoundedRectangle(width=1.55, height=1.35, corner_radius=0.12,
                                   stroke_color=col, stroke_width=2.5,
                                   fill_color=col, fill_opacity=0.1)
            inner.move_to(box)
            cards.add(VGroup(box, inner))
        cards.arrange(RIGHT, buff=0.4).move_to([0, 1.55, 0])
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.12) for c in cards],
                              lag_ratio=0.25), run_time=1.6)
        self.beat(1.0)
        line = Text("2 of 5 tries pass, so a single try works about 40% of the time.",
                    font_size=24, color=INK).move_to([0, 0.5, 0])
        self.clamp_w(line, 12.4)
        self.play(FadeIn(line, shift=UP * 0.1), run_time=0.6)
        self.beat(1.6)

        # pass@k = 1 - (1 - p)^k
        ks = [1, 3, 5, 10]
        vals = [round(100 * (1 - (1 - p) ** k)) for k in ks]
        assert vals == [40, 78, 92, 99], vals
        base_y, xs, max_h, w = -1.95, [-4.5, -1.5, 1.5, 4.5], 1.9, 1.15
        cols = [BAD_C, SWE_C, KNOW_C, OK_C]
        axis = Line([-6.1, base_y, 0], [6.1, base_y, 0]).set_stroke(MUTED, 2)
        self.play(Create(axis), run_time=0.4)
        for k, v, x, col in zip(ks, vals, xs, cols):
            h = max_h * v / 100
            bar = RoundedRectangle(width=w, height=h, corner_radius=0.06,
                                   stroke_width=0, fill_color=col, fill_opacity=1.0)
            bar.move_to([x, base_y + h / 2, 0])
            klab = Text(f"pass@{k}", font_size=20, color=INK)
            klab.next_to([x, base_y, 0], DOWN, buff=0.2)
            tr = ValueTracker(0)
            plab = self.count_label(tr, lambda v: f"{int(round(v))}%",
                                    24, col, [x, base_y + h + 0.32, 0])
            self.add(plab)
            self.play(GrowFromEdge(bar, DOWN), FadeIn(klab),
                      tr.animate.set_value(v), run_time=0.7)
        self.beat(1.4)
        punch = Text("pass@k scores a task solved if ANY of k tries passes, "
                     "so always ask which k a number used.",
                     font_size=24, color=CODE_C, weight="BOLD")
        self.clamp_w(punch, 12.6).move_to([0, -3.35, 0])
        self.play(FadeIn(punch, shift=UP * 0.1), run_time=0.7)
        self.beat(2.4)
        self.wipe()

    # ====================================================================== #
    # Scene — When there is no right answer (preference / Elo arena)
    # ====================================================================== #
    def scene_arena(self):
        header = self.section_header("When there is no right answer", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        sub = Text("Many tasks are open-ended, so there is no answer to match.",
                   font_size=25, color=INK).move_to([0, 2.55, 0])
        self.play(FadeIn(sub, shift=DOWN * 0.1), run_time=0.6)

        prompt = Text("Prompt:  Explain recursion to a five-year-old.",
                      font_size=23, color=GOLD)
        pbox = RoundedRectangle(width=prompt.width + 0.6, height=prompt.height + 0.4,
                                corner_radius=0.12, stroke_color=GOLD, stroke_width=2,
                                fill_color=GOLD, fill_opacity=0.07)
        prompt.move_to(pbox)
        pcard = VGroup(pbox, prompt).move_to([0, 1.55, 0])
        self.play(FadeIn(pcard, shift=DOWN * 0.1), run_time=0.6)
        self.beat(1.2)

        def resp(name, color, body):
            nm = Text(name, font_size=22, color=color, weight="BOLD")
            bd = Text(body, font_size=19, color=INK, line_spacing=0.85)
            bd.set(width=min(4.6, bd.width))
            inner = VGroup(nm, bd).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
            box = RoundedRectangle(width=5.3, height=2.2, corner_radius=0.16,
                                   stroke_color=color, stroke_width=2.5,
                                   fill_color=color, fill_opacity=0.07)
            inner.move_to(box).align_to(box, UP).shift(DOWN * 0.3)
            inner.align_to(box, LEFT).shift(RIGHT * 0.32)
            return VGroup(box, inner)

        rA = resp("Model A", KNOW_C, "Like nesting dolls: open\none and a smaller one\n"
                  "is inside, until the tiniest.")
        rB = resp("Model B", MATH_C, "A function that calls\nitself on a smaller\n"
                  "input, stopping at a base case.")
        pair = VGroup(rA, rB).arrange(RIGHT, buff=0.7).move_to([0, -0.55, 0])
        self.play(FadeIn(rA, shift=RIGHT * 0.15), FadeIn(rB, shift=LEFT * 0.15),
                  run_time=0.8)
        self.beat(2.0)
        winner = SurroundingRectangle(rA, color=OK_C, buff=0.08,
                                      corner_radius=0.16).set_stroke(width=4)
        vlab = VGroup(check(OK_C, 26),
                      Text("you pick the better one", font_size=20, color=OK_C)) \
            .arrange(RIGHT, buff=0.2).next_to(rA, DOWN, buff=0.25)
        self.play(Create(winner), FadeIn(vlab, shift=UP * 0.1), run_time=0.8)
        self.beat(2.0)

        # thousands of votes -> an Elo leaderboard
        self.play(FadeOut(VGroup(pcard, rA, rB, winner, vlab)),
                  ReplacementTransform(sub, Text("Repeat over thousands of pairs. "
                  "Each model earns an Elo rating, like chess.", font_size=25,
                  color=INK).move_to([0, 2.55, 0])), run_time=0.8)

        board = [("Model A", 1361, KNOW_C), ("Model B", 1327, MATH_C),
                 ("Model C", 1294, OK_C), ("Model D", 1248, SWE_C)]
        lo, hi = 1180, 1400
        rows = VGroup()
        trackers = []
        ys = [1.15, 0.35, -0.45, -1.25]
        for (name, elo, col), y in zip(board, ys):
            lab = Text(name, font_size=22, color=INK, weight="BOLD").move_to([-4.2, y, 0])
            track = RoundedRectangle(width=5.4, height=0.36, corner_radius=0.18,
                                     stroke_color=GRID, stroke_width=1.5,
                                     fill_color=GRID, fill_opacity=0.6)
            track.move_to([0.2, y, 0]).align_to([-2.4, y, 0], LEFT)
            frac = (elo - lo) / (hi - lo)
            fill = RoundedRectangle(width=max(0.36, 5.4 * frac), height=0.36,
                                    corner_radius=0.18, stroke_width=0,
                                    fill_color=col, fill_opacity=1.0)
            fill.align_to(track, LEFT).set_y(y)
            tr = ValueTracker(lo)
            trackers.append((tr, elo))
            num = self.count_label(tr, lambda v: f"{int(round(v))}",
                                   24, col, [track.get_right()[0] + 0.6, y, 0])
            self.add(num)
            rows.add(VGroup(lab, track, fill, num))
        note = Text("illustrative Elo", font_size=15, color=MUTED, slant=ITALIC)
        note.next_to(rows, DOWN, buff=0.2).align_to(rows, RIGHT)
        self.play(LaggedStart(*[FadeIn(VGroup(r[0], r[1], r[2]), shift=RIGHT * 0.15)
                                for r in rows], lag_ratio=0.2), run_time=1.2)
        self.play(*[t.animate.set_value(e) for t, e in trackers], FadeIn(note),
                  run_time=1.3)
        self.beat(1.6)
        punch = Text("This builds the LMArena leaderboard. The judge can even be "
                     "another model.", font_size=24, color=GOLD, weight="BOLD")
        self.clamp_w(punch, 12.6).move_to([0, -2.75, 0])
        self.play(FadeIn(punch, shift=UP * 0.1), run_time=0.7)
        self.beat(2.4)
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_whatis()
        self.scene_tour()
        self.scene_grading()
        self.scene_swebench()
        self.scene_passk()
        self.scene_arena()
        self.scene_progress()
        self.scene_catch()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_BMBase):
    def construct(self):
        self.play_intro()


class Whatis(_BMBase):
    def construct(self):
        self.scene_whatis()


class Tour(_BMBase):
    def construct(self):
        self.scene_tour()


class Grading(_BMBase):
    def construct(self):
        self.scene_grading()


class SweBench(_BMBase):
    def construct(self):
        self.scene_swebench()


class PassK(_BMBase):
    def construct(self):
        self.scene_passk()


class Arena(_BMBase):
    def construct(self):
        self.scene_arena()


class Progress(_BMBase):
    def construct(self):
        self.scene_progress()


class Catch(_BMBase):
    def construct(self):
        self.scene_catch()


class Outro(_BMBase):
    def construct(self):
        self.play_outro()


class AIBenchmarks(_BMBase):
    """The whole ~4-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    AIBenchmarks().render()

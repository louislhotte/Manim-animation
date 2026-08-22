"""LLM-as-a-Judge — a ~4-minute explainer, house-style.

Traditional observability (latency, error rate, token counts) can't tell you
whether an LLM's *answer* was actually good. This film covers the fix the
industry reaches for — using a second LLM to grade the first one's output —
and, crucially, shows *how you actually build one*, then is honest about where
the technique itself breaks down:

    1. The observability gap  -- green dashboards, wrong answers
    2. The idea               -- a second LLM + a rubric -> {score, reasoning};
                                 the three ways to ask (score / pairwise / ref)
    3. Anatomy of a judge     -- the actual prompt: rubric, inputs, JSON verdict
    4. Custom evaluators      -- real Anthropic SDK code; define ANY criterion
                                 and run a whole suite (groundedness/tone/policy)
    5. In production          -- the verdict rides the trace -> a graphed,
                                 alertable quality metric
    6. The limitations        -- position bias (shown live), verbosity, cost,
                                 self-preference; calibrate against humans

Everything uses ``Text`` (Pango), never ``Tex`` — no LaTeX toolchain. The judge
prompt and the Python evaluator are set in Menlo and syntax-coloured; nothing is
a screenshot.

Scenes are exposed individually (``Intro``, ``Gap``, ``Idea``, ``Prompt``,
``Evaluators``, ``Pipeline``, ``Limits``, ``Outro``) and as one film
(``LLMAsJudge``).

Env knobs:
    LLMJ_QUICK=1     collapse every reading hold (and end-holds) for a fast render
    LLMJ_DELAY=1.5   override the reading-hold multiplier (seconds per "beat")
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


QUICK = os.environ.get("LLMJ_QUICK") == "1"
DELAY = float(os.environ.get("LLMJ_DELAY", "0.26" if QUICK else "1.5"))
END_HOLD = 0.2 if QUICK else 1.9
ANIM_SLOW = 1.0 if QUICK else 1.15

# ---- palette -------------------------------------------------------------- #
BG = "#0E1117"
PANEL = "#151A23"
INK = "#F5F3EF"
MUTED = "#8A93A6"
FAINT = "#2A3140"
ACCENT = "#FFD166"
GOOD = "#3DD68C"
BAD = "#FF5C5C"
WARN = "#FFC24B"

APP_C = "#5B8DEF"     # the production / app LLM (blue)
JUDGE_C = "#C792EA"   # the judge LLM (purple)
OBS_C = "#2EC4B6"      # observability stack (teal)
HUMAN_C = "#FF9F45"   # human reviewer (orange)

# ---- code (Night-Owl-ish) palette ----------------------------------------- #
MONO = "Menlo"
CODE_FS = 19
PLAIN = "#D6DEEB"
COMMENT = "#5F6B7E"
KW = "#C792EA"
FN = "#82AAFF"
VAL = "#F78C6C"
STR = "#7FDBCA"

JSON_T2C = {
    '"trace_id"': FN, '"input"': FN, '"output"': FN, '"latency_ms"': FN,
    '"judge_score"': JUDGE_C, '"judge_verdict"': JUDGE_C,
    '"a1b2c3"': STR, '"45 days, no questions asked."': STR,
    '"not grounded in policy docs"': STR,
}

# python judge-function panel
PY_T2C = {
    "from": KW, "import": KW, "class": KW, "def": KW, "return": KW,
    "Anthropic": FN, "BaseModel": FN, "Verdict": FN,
    "messages": FN, "parse": FN, "parsed_output": FN, "output_format": FN,
    "model": FN, "system": FN, "max_tokens": FN,
    '"claude-opus-4-8"': VAL,
    "score": JUDGE_C, "reasoning": JUDGE_C,
}

# judge-prompt panel
PROMPT_T2C = {
    "SYSTEM": JUDGE_C, "USER": APP_C,
    "GROUNDEDNESS": ACCENT, "JSON": STR,
    "CONTEXT": OBS_C, "QUESTION": OBS_C, "ANSWER": OBS_C,
    "score": JUDGE_C, "reasoning": JUDGE_C,
}


def _safe_t2c(s, table):
    """Per-line text->colour map, pruned so no key overlaps another."""
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


def chip(text, color, fs=18, fill=0.14, w=None, h=0.54, tcolor=None, weight="NORMAL"):
    label = txt(text, fs=fs, color=tcolor or INK, weight=weight)
    width = (label.width + 0.5) if w is None else w
    box = RoundedRectangle(width=width, height=h, corner_radius=0.12,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=fill)
    label.move_to(box)
    return VGroup(box, label)


def arr(a, b, color=MUTED, sw=4.5, buff=0.18, tip=0.24):
    """A straight arrow with a consistent, well-proportioned head.

    Caller passes real edge points (e.g. box.get_right(), box.get_left()); a
    small fixed tip and a capped tip-ratio keep short arrows from growing a
    giant head. Boxes are spaced with a real gap so arrows always read.
    """
    return Arrow(a, b, buff=buff, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.28,
                 max_stroke_width_to_length_ratio=6.0, tip_length=tip)


def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])])
    return v.set_stroke(color=color, width=sw).scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.16, -0.16, 0], [0.16, 0.16, 0])
    b = Line([-0.16, 0.16, 0], [0.16, -0.16, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


def make_star(color=ACCENT, r=0.22):
    pts = []
    for i in range(10):
        rad = r if i % 2 == 0 else r * 0.42
        a = PI / 2 + i * PI / 5
        pts.append(np.array([rad * np.cos(a), rad * np.sin(a), 0]))
    s = Polygon(*pts, stroke_width=2, stroke_color=color,
                fill_color=color, fill_opacity=1.0)
    return s


def llm_chip(label, color, w=1.9, h=1.35, fs=16):
    """A little LLM: a titled box holding a 3-layer mini neural net."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.14,
                            stroke_color=color, stroke_width=3,
                            fill_color=color, fill_opacity=0.12)
    xs = np.linspace(-w * 0.26, w * 0.26, 3)
    counts = [2, 3, 2]
    layers = []
    net = VGroup()
    for x, n in zip(xs, counts):
        col = VGroup(*[Dot(radius=0.05, color=color) for _ in range(n)])
        col.arrange(DOWN, buff=0.15)
        col.move_to([x, h * 0.16, 0])
        layers.append(col)
        net.add(col)
    lines = VGroup()
    for a, b in zip(layers[:-1], layers[1:]):
        for da in a:
            for db in b:
                lines.add(Line(da.get_center(), db.get_center(),
                               stroke_color=color, stroke_width=1.2, stroke_opacity=0.5))
    lbl = txt(label, fs=fs, color=INK, weight="BOLD")
    lbl.move_to([0, -h * 0.34, 0])
    if lbl.width > w - 0.2:
        lbl.scale_to_fit_width(w - 0.2)
    grp = VGroup(body, lines, net, lbl)
    grp.body = body
    return grp


def scale_icon(color=JUDGE_C, w=2.4, h=1.7, tilt=0.0, pan_scale=(1.0, 1.0)):
    """A balance scale: stand + beam (rotatable) + two hanging pans."""
    stand = Line([0, -h * 0.46, 0], [0, h * 0.30, 0], stroke_color=color, stroke_width=5)
    base = Line([-w * 0.16, -h * 0.46, 0], [w * 0.16, -h * 0.46, 0],
               stroke_color=color, stroke_width=5)
    beam_len = w * 0.46
    beam = Line([-beam_len, 0, 0], [beam_len, 0, 0], stroke_color=color, stroke_width=5)
    beam.move_to([0, h * 0.30, 0])
    beam.rotate(tilt)
    chains = VGroup()
    pans = VGroup()
    ends = [beam.get_start(), beam.get_end()]
    for end, ps in zip(ends, pan_scale):
        pan_c = end + DOWN * 0.42
        chains.add(Line(end, pan_c, stroke_color=color, stroke_width=2.2))
        pan = Arc(radius=0.22 * ps, start_angle=PI, angle=PI,
                  stroke_color=color, stroke_width=4).move_to(pan_c + DOWN * 0.04)
        pans.add(pan)
    grp = VGroup(base, stand, beam, chains, pans)
    grp.beam = beam
    return grp


def trace_card(prompt, response, color=APP_C, w=5.4, fs=16):
    ptag = chip("IN", MUTED, fs=12, w=0.7, h=0.36, weight="BOLD")
    rtag = chip("OUT", color, fs=12, w=0.85, h=0.36, weight="BOLD", tcolor=color)
    p = txt(f"“{prompt}”", fs=fs, color=MUTED)
    r = txt(f"“{response}”", fs=fs, color=INK)
    row1 = VGroup(ptag, p).arrange(RIGHT, buff=0.2)
    row2 = VGroup(rtag, r).arrange(RIGHT, buff=0.2)
    inner = VGroup(row1, row2).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    if inner.width > w - 0.6:
        inner.scale((w - 0.6) / inner.width, about_point=inner.get_left())
    box = RoundedRectangle(width=w, height=inner.height + 0.45, corner_radius=0.14,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=0.07)
    inner.move_to(box)
    grp = VGroup(box, inner)
    grp.box = box
    return grp


def verdict_badge(score, note, color=GOOD, w=4.6, mark=None):
    s = txt(score, fs=22, color=color, weight="BOLD")
    n = txt(note, fs=15, color=MUTED)
    body = VGroup(s, n).arrange(DOWN, buff=0.12)
    if body.width > w - 0.7:
        body.scale((w - 0.7) / body.width, about_point=body.get_left())
    box = RoundedRectangle(width=w, height=body.height + 0.4, corner_radius=0.14,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=0.12)
    body.move_to(box)
    grp = VGroup(box, body)
    if mark is not None:
        m = mark.copy().scale(0.6).move_to([box.get_right()[0] - 0.32, box.get_top()[1] - 0.28, 0])
        grp.add(m)
    grp.box = box
    return grp


def ans_card(letter, text, color, w=3.0, fs=15):
    """A short answer card with a big letter badge — used in the bias demo."""
    badge = chip(letter, color, fs=18, w=0.6, h=0.6, weight="BOLD", tcolor=color)
    body = txt(text, fs=fs, color=INK)
    inner = VGroup(badge, body).arrange(RIGHT, buff=0.22)
    if inner.width > w - 0.5:
        inner.scale((w - 0.5) / inner.width, about_point=inner.get_left())
    box = RoundedRectangle(width=w, height=inner.height + 0.5, corner_radius=0.14,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=0.08)
    inner.move_to(box)
    grp = VGroup(box, inner)
    grp.box = box
    grp.letter = letter
    return grp


def human_icon(color=HUMAN_C, s=1.0):
    """A tiny person glyph (head + shoulders)."""
    head = Circle(radius=0.16 * s, stroke_color=color, stroke_width=3,
                  fill_color=color, fill_opacity=0.18)
    head.move_to([0, 0.22 * s, 0])
    body = Arc(radius=0.30 * s, start_angle=PI, angle=PI,
               stroke_color=color, stroke_width=3)
    body.move_to([0, -0.12 * s, 0])
    return VGroup(head, body)


# ========================================================================== #
class _JudgeBase(Scene):
    def setup(self):
        self.camera.background_color = BG
        self._cap = None
        self.hlrect = None

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
        self.wait(t * (0.25 if QUICK else 1.0))

    def settle(self):
        self.wait(END_HOLD)

    def wipe(self, rt=0.6):
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)
        self._cap = None
        self.hlrect = None

    # ---- headers & captions ---------------------------------------------- #
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
        grp = VGroup(head, line)
        self.play(FadeIn(head, shift=RIGHT * 0.2), Create(line), run_time=0.7)
        return grp

    def say(self, text, color=INK, fs=25, rt=0.5, weight="BOLD"):
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

    def clear_cap(self, rt=0.3):
        if self._cap is not None:
            self.play(FadeOut(self._cap), run_time=rt)
            self._cap = None

    # ---- bookend cards ---------------------------------------------------- #
    def _bookend_title(self, title, subtitle=None):
        header = txt(title, fs=48, color=INK, weight="BOLD")
        if header.width > 11.5:
            header.scale_to_fit_width(11.5)
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=JUDGE_C)
        writer = txt("Created by Ptolémé", fs=28, color=JUDGE_C)
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
        scale = scale_icon(color=JUDGE_C, w=2.6, h=1.9, tilt=0.16).to_edge(UP, buff=0.85)
        self.play(Create(scale, lag_ratio=0.05), run_time=1.4)
        self.play(Rotate(scale.beam, angle=-0.16, about_point=scale.beam.get_center()),
                  run_time=1.0, rate_func=there_and_back)
        grp = self._bookend_title(
            "LLM-as-a-Judge",
            "grading AI output at scale — and where it breaks")
        self.card_wait(1.6)
        self.play(FadeOut(grp), FadeOut(scale), run_time=0.9)
        self.card_wait(0.2)

    def play_outro(self):
        self.card_wait(0.3)
        header = txt("Thanks for watching!", fs=46, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=JUDGE_C)
        writer = txt("Created by Ptolémé", fs=28, color=JUDGE_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.2)
        self.card_wait(0.6)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.card_wait(1.6)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.0)
        self.card_wait(0.3)

    # ---- code panel (Menlo, adapted from the house code-panel helper) ----- #
    def code_panel(self, spec, table, title="trace.json", fs=CODE_FS,
                   indent_unit=0.5, line_buff=0.16, target_h=5.6, target_w=6.6):
        lines = []
        for indent, s in spec:
            if s == "":
                m = Rectangle(width=0.02, height=0.28, fill_opacity=0, stroke_opacity=0)
            elif s.lstrip().startswith("#"):
                m = txt(s, fs=fs, color=COMMENT, font=MONO, slant=ITALIC)
            else:
                m = Text(s, font=MONO, font_size=fs, color=PLAIN, t2c=_safe_t2c(s, table))
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
                              fill_color="#0A0E15", fill_opacity=1.0)
        bg.move_to(code)
        bar = RoundedRectangle(width=bg.width, height=0.5, corner_radius=0.16,
                               stroke_width=0, fill_color="#141C29", fill_opacity=1.0)
        bar.move_to(bg).align_to(bg, UP)
        dots = VGroup(*[Dot(radius=0.045, color=c)
                        for c in ("#FF5F57", "#FEBC2E", "#28C840")]).arrange(RIGHT, buff=0.11)
        dots.move_to([bg.get_left()[0] + 0.42, bar.get_center()[1], 0])
        ttl = txt(title, fs=15, color=MUTED, font=MONO)
        max_ttl_w = bg.width - 1.5
        if ttl.width > max_ttl_w:
            ttl.scale_to_fit_width(max_ttl_w)
        ttl.next_to(dots, RIGHT, buff=0.34).set_y(bar.get_center()[1])
        code.shift(DOWN * 0.2)
        panel = VGroup(bg, bar, dots, ttl, code)
        panel.code = code
        return panel, lines

    def hl_lines(self, panel, lines, idxs, color=ACCENT, opacity=0.16, pad=0.05, xpad=0.34):
        tops = [lines[i].get_top()[1] for i in idxs]
        bots = [lines[i].get_bottom()[1] for i in idxs]
        y_hi, y_lo = max(tops) + pad, min(bots) - pad
        rect = RoundedRectangle(width=panel[0].width - xpad, height=(y_hi - y_lo),
                                corner_radius=0.08, stroke_width=0,
                                fill_color=color, fill_opacity=opacity)
        rect.move_to([panel[0].get_center()[0], (y_hi + y_lo) / 2, 0])
        return rect

    def focus(self, panel, lines, idxs, color=ACCENT, rt=0.4):
        new = self.hl_lines(panel, lines, idxs, color)
        if self.hlrect is None:
            self.hlrect = new
            self.play(FadeIn(new), run_time=rt)
        else:
            self.play(Transform(self.hlrect, new), run_time=rt)
        return self.hlrect

    def drop_focus(self, rt=0.3):
        if self.hlrect is not None:
            self.play(FadeOut(self.hlrect), run_time=rt)
            self.hlrect = None

    # ====================================================================== #
    # Scene 1 — The observability gap
    # ====================================================================== #
    def scene_gap(self):
        self.section_header("01", "The Observability Gap", WARN)

        user = chip("User", MUTED, fs=18, w=1.5, weight="BOLD")
        app = llm_chip("App LLM", APP_C, w=2.0, h=1.35)
        resp = chip("“You're fully covered.”", GOOD, fs=15, w=3.6, h=0.6)
        row = VGroup(user, app, resp).arrange(RIGHT, buff=1.0).move_to(UP * 1.35)
        a1 = arr(user.get_right(), app.get_left(), color=MUTED)
        a2 = arr(app.get_right(), resp.get_left(), color=APP_C)
        self.play(FadeIn(user, shift=RIGHT * 0.2), run_time=0.5)
        self.play(GrowArrow(a1), GrowFromCenter(app), run_time=0.6)
        self.play(GrowArrow(a2), FadeIn(resp, shift=LEFT * 0.2), run_time=0.6)
        self.say("A request comes in, the model answers.", color=INK)
        self.beat(1.2)

        metrics = VGroup(
            chip("latency  240ms", GOOD, fs=16, w=2.6),
            chip("error rate  0.1%", GOOD, fs=16, w=2.7),
            chip("tokens  512", GOOD, fs=16, w=2.2),
        ).arrange(RIGHT, buff=0.5).next_to(row, DOWN, buff=1.0)
        ticks = VGroup(*[make_tick(GOOD, sw=6, scale=0.5).next_to(m, RIGHT, buff=0.14)
                        for m in metrics])
        self.play(LaggedStart(*[FadeIn(m, shift=UP * 0.15) for m in metrics], lag_ratio=0.2),
                  LaggedStart(*[GrowFromCenter(t) for t in ticks], lag_ratio=0.2), run_time=1.0)
        self.say("Standard observability watches latency, errors, cost — all green.",
                color=GOOD)
        self.beat(1.7)

        bad_resp = chip("“Yes, pre-existing conditions are covered.”", BAD, fs=14,
                        w=4.7, h=0.6)
        bad_resp.move_to(resp)
        qbadge = Circle(radius=0.24, color=BAD, stroke_width=3, fill_color=BAD, fill_opacity=0.15)
        qmark = txt("?", fs=30, color=BAD, weight="BOLD").move_to(qbadge)
        qgrp = VGroup(qbadge, qmark).next_to(bad_resp, UP, buff=0.2)
        self.play(ReplacementTransform(resp, bad_resp), a2.animate.set_color(BAD), run_time=0.6)
        self.play(FadeIn(qgrp, scale=1.3), run_time=0.4)
        self.say("This answer is flat-out wrong — policy says the opposite.", color=BAD)
        self.beat(1.3)

        self.play(Indicate(metrics, color=GOOD, scale_factor=1.03), run_time=0.6)
        self.say("...but latency, errors and tokens look identical. Nothing fires.", color=WARN)
        self.beat(1.7)

        self.play(FadeOut(VGroup(row, a1, a2, bad_resp, qgrp, metrics, ticks)),
                  FadeOut(self._cap), run_time=0.7)
        self._cap = None
        q = txt("Who checks that millions of answers are actually", fs=26, color=INK)
        q2 = txt("correct, safe and on-topic — automatically?", fs=26, color=ACCENT,
                weight="BOLD")
        qg = VGroup(q, q2).arrange(DOWN, buff=0.25).move_to(UP * 0.2)
        self.play(FadeIn(qg, shift=UP * 0.2), run_time=0.9)
        self.beat(2.1)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — The idea + the three ways to ask
    # ====================================================================== #
    def scene_idea(self):
        self.section_header("02", "The Idea", JUDGE_C)

        # the grading flow --------------------------------------------------- #
        card = trace_card("Are pre-existing conditions covered?",
                          "Yes, you're fully covered.",
                          color=APP_C, w=4.6, fs=14)
        card.move_to(LEFT * 4.2 + UP * 0.7)
        judge = llm_chip("Judge LLM", JUDGE_C, w=2.1, h=1.5).move_to(UP * 0.7)
        badge = verdict_badge("score  1 / 5", "contradicts the policy", color=BAD,
                              w=3.7, mark=make_cross(BAD))
        badge.move_to(RIGHT * 4.3 + UP * 0.7)
        a1 = arr(card.get_right(), judge.get_left(), color=JUDGE_C)
        a2 = arr(judge.get_right(), badge.get_left(), color=JUDGE_C)

        self.play(FadeIn(card, shift=RIGHT * 0.2), run_time=0.6)
        self.say("Take the input/output the app already produced…", color=INK)
        self.beat(1.2)
        self.play(GrowArrow(a1), GrowFromCenter(judge), run_time=0.6)

        rubric = chip("+ a rubric: what does 'good' mean?", JUDGE_C, fs=14, w=4.2, h=0.5)
        rubric.next_to(judge, DOWN, buff=0.85)
        aR = arr(rubric.get_top(), judge.get_bottom(), color=JUDGE_C, sw=3, tip=0.16, buff=0.1)
        self.play(FadeIn(rubric, shift=UP * 0.15), GrowArrow(aR), run_time=0.6)
        self.say("…hand it to a second LLM, with a rubric.", color=JUDGE_C)
        self.beat(1.4)

        self.play(GrowArrow(a2), FadeIn(badge, shift=LEFT * 0.2), run_time=0.6)
        self.say("It returns a score and a reason — like a reviewer, in one call.",
                color=INK)
        self.beat(1.8)

        # the three ways to ask --------------------------------------------- #
        self.play(FadeOut(VGroup(card, a1, judge, rubric, aR, a2, badge)),
                  FadeOut(self._cap), run_time=0.6)
        self._cap = None
        modes_title = txt("Three ways to ask the judge", fs=24, color=JUDGE_C, weight="BOLD")
        modes_title.to_edge(UP, buff=1.5)
        self.play(FadeIn(modes_title, shift=DOWN * 0.1), run_time=0.5)

        def mode_card(title, inner, sub):
            head = txt(title, fs=18, color=INK, weight="BOLD")
            subl = txt(sub, fs=13, color=MUTED)
            body = VGroup(head, inner, subl).arrange(DOWN, buff=0.22)
            box = RoundedRectangle(width=3.9, height=2.5, corner_radius=0.14,
                                   stroke_color=JUDGE_C, stroke_width=2,
                                   fill_color=JUDGE_C, fill_opacity=0.06)
            body.move_to(box)
            return VGroup(box, body)

        # 1: direct score
        d_in = VGroup(chip("answer", APP_C, fs=13, w=1.5, h=0.44),
                      arr([0, 0, 0], [0.7, 0, 0], color=MUTED, sw=3, tip=0.16, buff=0.05),
                      chip("2 / 5", ACCENT, fs=15, w=1.1, h=0.44, weight="BOLD", tcolor=ACCENT)
                      ).arrange(RIGHT, buff=0.14)
        m1 = mode_card("Direct score", d_in, "grade one answer on a rubric")
        # 2: pairwise
        p_in = VGroup(
            VGroup(chip("A", APP_C, fs=14, w=0.55, h=0.44, weight="BOLD"),
                   chip("B", OBS_C, fs=14, w=0.55, h=0.44, weight="BOLD")
                   ).arrange(RIGHT, buff=0.14),
            arr([0, 0, 0], [0.7, 0, 0], color=MUTED, sw=3, tip=0.16, buff=0.05),
            chip("B wins", GOOD, fs=14, w=1.3, h=0.44, weight="BOLD", tcolor=GOOD)
        ).arrange(RIGHT, buff=0.14)
        m2 = mode_card("Pairwise", p_in, "which of two is better?")
        # 3: reference
        r_in = VGroup(
            VGroup(chip("answer", APP_C, fs=12, w=1.4, h=0.4),
                   chip("gold ✓", GOOD, fs=12, w=1.3, h=0.4, tcolor=GOOD)
                   ).arrange(DOWN, buff=0.1),
            arr([0, 0, 0], [0.6, 0, 0], color=MUTED, sw=3, tip=0.16, buff=0.05),
            chip("match?", ACCENT, fs=14, w=1.4, h=0.44, weight="BOLD", tcolor=ACCENT)
        ).arrange(RIGHT, buff=0.14)
        m3 = mode_card("Reference-based", r_in, "compare to a known-good answer")

        modes = VGroup(m1, m2, m3).arrange(RIGHT, buff=0.4).next_to(modes_title, DOWN, buff=0.5)
        self.play(LaggedStart(*[FadeIn(m, shift=UP * 0.15) for m in modes],
                              lag_ratio=0.25), run_time=1.3)
        self.say("Score one, compare two, or match a reference.", color=JUDGE_C)
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Anatomy of a judge prompt
    # ====================================================================== #
    def scene_prompt(self):
        self.section_header("03", "Anatomy of a Judge", ACCENT)

        spec = [
            (0, "SYSTEM"),
            (0, "You are a strict evaluator. Score the"),
            (0, "ANSWER 1-5 on GROUNDEDNESS:"),
            (1, "5  every claim supported by CONTEXT"),
            (1, "1  contradicts or invents facts"),
            (0, "Reply as JSON: { score, reasoning }"),
            (0, ""),
            (0, "USER"),
            (0, "CONTEXT   Refunds: 45 days. Pre-existing"),
            (1, "conditions are NOT covered."),
            (0, "QUESTION  Are pre-existing conditions covered?"),
            (0, "ANSWER    “Yes, you're fully covered.”"),
        ]
        panel, lines = self.code_panel(spec, PROMPT_T2C, title="judge_prompt",
                                       target_h=5.0, target_w=6.6, fs=18)
        panel.to_edge(LEFT, buff=0.6).shift(DOWN * 0.15)
        self.play(FadeIn(panel, shift=UP * 0.2), run_time=0.8)
        self.say("A judge is just a prompt. Three parts do the work.", color=ACCENT)
        self.beat(1.4)

        # highlight the three parts in turn -------------------------------- #
        self.focus(panel, lines, [1, 2, 3, 4], color=ACCENT)
        self.say("1 — the rubric: spell out exactly what a 5 and a 1 mean.", color=ACCENT)
        self.beat(1.6)
        self.focus(panel, lines, [8, 9, 10, 11], color=OBS_C)
        self.say("2 — the inputs: the context, the question, the answer to grade.",
                color=OBS_C)
        self.beat(1.6)
        self.focus(panel, lines, [5], color=JUDGE_C)
        self.say("3 — demand structured output: a JSON {score, reasoning}.", color=JUDGE_C)
        self.beat(1.6)

        # run it -> the verdict -------------------------------------------- #
        self.drop_focus()
        vspec = [
            (0, "{"),
            (1, '"score": 1,'),
            (1, '"reasoning":'),
            (1, '  "contradicts policy —'),
            (1, '   pre-existing are excluded"'),
            (0, "}"),
        ]
        vpanel, _ = self.code_panel(vspec, {'"score"': JUDGE_C, '"reasoning"': JUDGE_C,
                                            '"contradicts policy —': STR,
                                            'pre-existing are excluded"': STR},
                                    title="verdict", target_h=2.2, target_w=4.3, fs=16)
        judge = llm_chip("Judge LLM", JUDGE_C, w=1.9, h=1.3)
        # judge sits above the verdict; the column lives in the clear space to
        # the right of the prompt panel (never overlapping it or the edge).
        col = VGroup(judge, vpanel).arrange(DOWN, buff=0.7)
        col.next_to(panel, RIGHT, buff=0.6, aligned_edge=UP)
        min_left = panel.get_right()[0] + 0.5
        if col.get_left()[0] < min_left:
            col.shift(RIGHT * (min_left - col.get_left()[0]))
        over = col.get_right()[0] - (config.frame_x_radius - 0.35)
        if over > 0:
            col.shift(LEFT * over)
        aJ = arr([panel.get_right()[0], judge.get_center()[1], 0], judge.get_left(),
                 color=JUDGE_C)
        aV = arr(judge.get_bottom(), vpanel.get_top(), color=JUDGE_C, sw=3.5, tip=0.18, buff=0.1)
        self.play(GrowArrow(aJ), GrowFromCenter(judge), run_time=0.6)
        self.play(GrowArrow(aV), FadeIn(vpanel, shift=UP * 0.15), run_time=0.6)
        self.say("Run it, and every answer comes back with a graded, explained verdict.",
                color=JUDGE_C)
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Custom evaluators (real Anthropic SDK code)
    # ====================================================================== #
    def scene_evaluators(self):
        self.section_header("04", "Custom Evaluators", GOOD)

        spec = [
            (0, "from anthropic import Anthropic"),
            (0, "from pydantic import BaseModel"),
            (0, ""),
            (0, "client = Anthropic()"),
            (0, ""),
            (0, "class Verdict(BaseModel):        # structured output"),
            (1, "score: int                   # 1-5"),
            (1, "reasoning: str"),
            (0, ""),
            (0, "def judge(criteria, question, answer, context=\"\"):"),
            (1, "r = client.messages.parse("),
            (2, "model=\"claude-opus-4-8\","),
            (2, "system=RUBRIC.format(criteria=criteria),"),
            (2, "messages=[frame(question, answer, context)],"),
            (2, "output_format=Verdict)      # validated JSON"),
            (1, "return r.parsed_output"),
        ]
        panel, lines = self.code_panel(spec, PY_T2C, title="evaluators.py",
                                       target_h=4.5, target_w=8.2, fs=17)
        panel.move_to(DOWN * 0.4)
        self.play(FadeIn(panel, shift=UP * 0.2), run_time=0.8)
        self.say("In code, a judge is one reusable function.", color=GOOD)
        self.beat(1.4)

        self.focus(panel, lines, [5, 6, 7], color=JUDGE_C)
        self.say("Ask for a typed Verdict — the SDK validates the JSON for you.",
                color=JUDGE_C)
        self.beat(1.6)
        self.focus(panel, lines, [10, 11, 12, 13, 14], color=GOOD)
        self.say("One `messages.parse` call: your rubric as the system prompt,",
                color=GOOD)
        self.beat(0.8)
        self.say("the answer to grade, and `output_format=Verdict`.", color=GOOD)
        self.beat(1.6)

        # the payoff: criteria is just an argument -> run a whole suite ----- #
        self.drop_focus()
        self.play(panel.animate.scale(0.82).to_edge(LEFT, buff=0.5), run_time=0.6)
        self.focus(panel, lines, [9], color=ACCENT)

        head = txt("`criteria` is just an argument —", fs=19, color=INK, weight="BOLD")
        head2 = txt("define ANY criterion, run them as a suite:", fs=19, color=ACCENT,
                    weight="BOLD")
        heading = VGroup(head, head2).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        heading.next_to(panel, RIGHT, buff=0.5).align_to(panel, UP).shift(DOWN * 0.1)
        if heading.get_right()[0] > config.frame_x_radius - 0.3:
            heading.scale_to_fit_width((config.frame_x_radius - 0.3) - heading.get_left()[0])
        self.play(FadeIn(heading, shift=RIGHT * 0.15), run_time=0.6)

        suite = [("Groundedness", "supported by the policy docs?", "2/5", BAD),
                 ("Tone", "polite, professional, on-brand?", "4/5", GOOD),
                 ("Policy", "never promises what isn't covered?", "1/5", BAD)]
        rows = VGroup()
        for name, desc, sc, col in suite:
            crit = chip(name, JUDGE_C, fs=15, w=2.5, h=0.6, weight="BOLD")
            d = txt(desc, fs=12, color=MUTED)
            critcol = VGroup(crit, d).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
            a = arr([0, 0, 0], [0.7, 0, 0], color=JUDGE_C, sw=3, tip=0.16, buff=0.05)
            score = chip(sc, col, fs=17, w=1.0, h=0.56, weight="BOLD", tcolor=col)
            rows.add(VGroup(critcol, a, score).arrange(RIGHT, buff=0.22))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        rows.next_to(heading, DOWN, buff=0.4).align_to(heading, LEFT)
        avail = (config.frame_x_radius - 0.3) - rows.get_left()[0]
        if rows.width > avail:
            rows.scale(avail / rows.width, about_point=rows.get_left())
        for row in rows:
            self.play(FadeIn(row, shift=RIGHT * 0.15), run_time=0.45)
            self.beat(0.5)
        self.say("Groundedness, tone, policy compliance — whatever you care about.",
                color=GOOD)
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — In production: judges in the observability stack
    # ====================================================================== #
    def scene_pipeline(self):
        self.section_header("05", "Judges in the Stack", OBS_C)

        spec = [
            (0, "{"),
            (1, '"trace_id": "a1b2c3",'),
            (1, '"input": "What is our refund window?",'),
            (1, '"output": "45 days, no questions asked.",'),
            (1, '"latency_ms": 812,'),
            (1, '"judge_score": 2,'),
            (1, '"judge_verdict": "not grounded in policy docs"'),
            (0, "}"),
        ]
        panel, lines = self.code_panel(spec, JSON_T2C, title="trace.json",
                                       target_h=4.6, target_w=6.0)
        panel.to_edge(LEFT, buff=0.6).shift(DOWN * 0.1)
        judge_lines = VGroup(lines[5], lines[6])
        judge_lines.set_opacity(0)
        self.play(FadeIn(panel, shift=UP * 0.2), run_time=0.8)
        self.say("Every request is already traced: input, output, latency…", color=OBS_C)
        self.beat(1.5)

        judge = llm_chip("Judge LLM", JUDGE_C, w=1.9, h=1.3).next_to(panel, RIGHT, buff=1.0)
        a1 = arr(panel.get_right(), judge.get_left(), color=JUDGE_C)
        self.play(GrowArrow(a1), GrowFromCenter(judge), run_time=0.6)
        self.say("…a sampled slice gets graded by the judge on the way through.",
                color=JUDGE_C)
        self.play(Flash(judge.get_center(), color=JUDGE_C, line_length=0.18), run_time=0.4)
        self.play(judge_lines.animate.set_opacity(1), run_time=0.6)
        self.say("The verdict is appended right onto the trace.", color=JUDGE_C)
        self.beat(1.7)

        self.play(FadeOut(VGroup(panel, judge, a1)), run_time=0.6)

        values = [4.3, 4.4, 4.2, 4.5, 4.3, 2.1, 1.8, 2.0]
        threshold = 3.5
        w, h = 8.6, 3.4
        body = RoundedRectangle(width=w, height=h, corner_radius=0.16,
                                stroke_color=FAINT, stroke_width=2,
                                fill_color=PANEL, fill_opacity=1.0)
        body.move_to(DOWN * 0.35)
        title = txt("avg judge score / hour", fs=17, color=MUTED)
        title.next_to(body, UP, buff=0.18).align_to(body, LEFT).shift(RIGHT * 0.35)
        inner_w, inner_h = w - 1.0, h - 1.1
        baseline_y = body.get_bottom()[1] + 0.55
        left_x = body.get_left()[0] + 0.6
        n = len(values)
        bar_w = inner_w / n * 0.55
        xs = np.linspace(left_x + bar_w, body.get_right()[0] - 0.6 - bar_w, n)
        thresh_y = baseline_y + inner_h * (threshold / 5.0)
        thresh_line = DashedLine([left_x, thresh_y, 0], [body.get_right()[0] - 0.4, thresh_y, 0],
                                 stroke_color=WARN, stroke_width=2, dash_length=0.1)
        thresh_lbl = txt("min acceptable", fs=13, color=WARN).next_to(
            thresh_line.get_left(), LEFT, buff=0.15)
        deploy_x = (xs[4] + xs[5]) / 2
        deploy_line = DashedLine([deploy_x, baseline_y - 0.1, 0],
                                 [deploy_x, body.get_top()[1] - 0.2, 0],
                                 stroke_color=MUTED, stroke_width=2, dash_length=0.08)
        deploy_lbl = txt("v2 deployed", fs=13, color=MUTED).next_to(
            deploy_line, UP, buff=0.08)
        self.play(FadeIn(body), FadeIn(title), run_time=0.6)
        self.play(Create(thresh_line), FadeIn(thresh_lbl), run_time=0.5)
        self.say("Now 'quality' is a metric — graphed and thresholded like any other.",
                color=OBS_C)
        bars = VGroup()
        for x, v in zip(xs, values):
            bh = inner_h * (v / 5.0)
            col = GOOD if v >= threshold else BAD
            bar = Rectangle(width=bar_w, height=bh, stroke_width=0,
                            fill_color=col, fill_opacity=0.85)
            bar.move_to([x, baseline_y + bh / 2, 0])
            bars.add(bar)
        self.play(LaggedStart(*[GrowFromCenter(b) for b in bars], lag_ratio=0.12), run_time=1.4)
        self.beat(1.1)
        self.play(Create(deploy_line), FadeIn(deploy_lbl), run_time=0.5)
        alert = txt("⚠ quality regression", fs=16, color=BAD, weight="BOLD")
        alert.next_to(bars[-1], UP, buff=0.35)
        if alert.get_right()[0] > body.get_right()[0] - 0.2:
            alert.align_to(body, RIGHT).shift(LEFT * 0.2)
        self.play(FadeIn(alert, shift=DOWN * 0.15), Flash(bars[-1].get_top(), color=BAD),
                  run_time=0.6)
        self.say("A bad model rollout shows up here — and pages someone, fast.", color=BAD)
        self.beat(1.7)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 6 — Limitations (shown, not listed)
    # ====================================================================== #
    def scene_limits(self):
        self.section_header("06", "But the Judge Has Blind Spots", BAD)

        # --- position bias, demonstrated live ------------------------------ #
        prompt = txt("Ask the judge: which answer is better, A or B?", fs=20, color=INK,
                     weight="BOLD").to_edge(UP, buff=1.5)
        self.play(FadeIn(prompt, shift=DOWN * 0.1), run_time=0.5)

        cardA = ans_card("A", "45 days, per policy.", APP_C, w=3.4)
        cardB = ans_card("B", "Around a month or so, I think.", OBS_C, w=3.4)
        left_x, right_x, yc = -3.1, 3.1, 0.15
        cardA.move_to([left_x, yc, 0])
        cardB.move_to([right_x, yc, 0])
        self.play(FadeIn(cardA, shift=RIGHT * 0.1), FadeIn(cardB, shift=LEFT * 0.1),
                  run_time=0.7)

        def crown(card):
            star = make_star(ACCENT, r=0.22).next_to(card, UP, buff=0.16)
            lbl = txt("judge picks this", fs=13, color=ACCENT).next_to(star, UP, buff=0.1)
            return VGroup(star, lbl)

        pick1 = crown(cardA)
        self.play(FadeIn(pick1, scale=1.2), cardA.box.animate.set_stroke(ACCENT, 4),
                  run_time=0.5)
        self.say("It prefers A — the answer on the left.", color=ACCENT)
        self.beat(1.5)

        # swap positions; nothing about the answers changes
        self.play(FadeOut(pick1), cardA.box.animate.set_stroke(APP_C, 2.5), run_time=0.3)
        self.say("Now swap their positions — same two answers.", color=INK)
        self.play(cardA.animate.move_to([right_x, yc, 0]),
                  cardB.animate.move_to([left_x, yc, 0]),
                  run_time=1.0, path_arc=-0.9)
        self.beat(0.8)
        pick2 = crown(cardB)  # cardB now sits on the left
        self.play(FadeIn(pick2, scale=1.2), cardB.box.animate.set_stroke(ACCENT, 4),
                  run_time=0.5)
        self.say("…and it picks the left one again — now that's B. The verdict flipped.",
                color=BAD)
        self.beat(1.8)
        punch = txt("Position bias: the score can track order, not quality.", fs=20,
                    color=BAD, weight="BOLD").next_to(prompt, DOWN, buff=0.0)
        punch.to_edge(UP, buff=2.15)
        self.clear_cap()
        self.play(FadeOut(VGroup(cardA, cardB, pick2)), run_time=0.5)

        # --- and it's not the only blind spot ------------------------------ #
        self.play(ReplacementTransform(prompt, punch), run_time=0.5)
        more = [("Verbosity bias", "longer, confident answers score higher", WARN),
                ("Cost & latency", "every grade is another LLM call, at scale", ACCENT),
                ("Self-preference", "models rate their own family's output higher", JUDGE_C)]
        cards = VGroup()
        for name, desc, col in more:
            head = txt(name, fs=18, color=col, weight="BOLD")
            d = txt(desc, fs=13, color=MUTED)
            if d.width > 3.4:
                d.scale_to_fit_width(3.4)
            inner = VGroup(head, d).arrange(DOWN, buff=0.14)
            box = RoundedRectangle(width=3.9, height=1.5, corner_radius=0.14,
                                   stroke_color=col, stroke_width=2,
                                   fill_color=col, fill_opacity=0.07)
            inner.move_to(box)
            cards.add(VGroup(box, inner))
        cards.arrange(RIGHT, buff=0.35).move_to(UP * 0.35)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.12) for c in cards],
                              lag_ratio=0.2), run_time=1.1)
        self.beat(1.8)

        # --- the discipline: calibrate against humans ---------------------- #
        human = human_icon(HUMAN_C, s=1.1)
        jn = llm_chip("Judge", JUDGE_C, w=1.5, h=1.05, fs=14)
        pair = VGroup(human, jn).arrange(RIGHT, buff=1.3).next_to(cards, DOWN, buff=0.7)
        link = DashedLine(human.get_right(), jn.get_left(), stroke_color=HUMAN_C,
                          stroke_width=3, dash_length=0.1)
        agree = txt("agreement: 87%", fs=15, color=HUMAN_C, weight="BOLD").next_to(
            link, UP, buff=0.12)
        hlbl = txt("human labels", fs=13, color=HUMAN_C).next_to(human, DOWN, buff=0.12)
        self.play(FadeIn(human, shift=RIGHT * 0.1), FadeIn(jn, shift=LEFT * 0.1),
                  FadeIn(hlbl), run_time=0.6)
        self.play(Create(link), FadeIn(agree, shift=UP * 0.1), run_time=0.6)
        self.say("So calibrate: check the judge against a set of human labels.",
                color=HUMAN_C)
        self.beat(1.8)

        # takeaway ---------------------------------------------------------- #
        self.play(FadeOut(VGroup(cards, pair, link, agree, hlbl, punch)),
                  FadeOut(self._cap), run_time=0.6)
        self._cap = None
        t1 = txt("Treat the judge as a scalable signal —", fs=30, color=INK, weight="BOLD")
        t2 = txt("not as ground truth.", fs=30, color=JUDGE_C, weight="BOLD")
        tk = VGroup(t1, t2).arrange(DOWN, buff=0.2).move_to(ORIGIN)
        self.play(Write(t1), run_time=0.8)
        self.play(FadeIn(t2, shift=UP * 0.1), run_time=0.6)
        self.beat(2.2)
        self.settle()
        self.wipe()

    # ---- the whole film --------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_gap()
        self.scene_idea()
        self.scene_prompt()
        self.scene_evaluators()
        self.scene_pipeline()
        self.scene_limits()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_JudgeBase):
    def construct(self):
        self.play_intro()


class Gap(_JudgeBase):
    def construct(self):
        self.scene_gap()


class Idea(_JudgeBase):
    def construct(self):
        self.scene_idea()


class Prompt(_JudgeBase):
    def construct(self):
        self.scene_prompt()


class Evaluators(_JudgeBase):
    def construct(self):
        self.scene_evaluators()


class Pipeline(_JudgeBase):
    def construct(self):
        self.scene_pipeline()


class Limits(_JudgeBase):
    def construct(self):
        self.scene_limits()


class Outro(_JudgeBase):
    def construct(self):
        self.play_outro()


class LLMAsJudge(_JudgeBase):
    """The whole ~4 minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    LLMAsJudge().render()

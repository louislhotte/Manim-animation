"""The Bitter Lesson — a short, house-style explainer.

Richard Sutton's 2019 essay in one sitting: the biggest lesson from 70 years of
AI research is that *general methods that leverage computation* end up winning —
and by a large margin — over methods that build in what humans know.

    "The Bitter Lesson" — Rich Sutton, 2019
    http://www.incompleteideas.net/IncIdeas/BitterLesson.html

A companion to the Transformer / KV-cache / Mixtral films; it shares their dark
palette. Five content scenes, bookended by the channel's intro/outro cards:

    Roads    -- two ways to build intelligence: human knowledge vs. computation
    1 Moore  -- the exponential engine: knowledge plateaus, compute overtakes
    2 Pattern-- the same defeat, again and again (chess, Go, speech, vision)
    3 Scale  -- the only two things that scale with compute: search & learning
    4 Lesson -- why it's *bitter*, and what to build instead (meta-methods)
    (recap)  -- build a machine that discovers, don't hand it what you know

Everything is drawn with ``Text`` (Pango), never ``Tex`` — the repo stays
LaTeX-free. Scenes render individually or as one film (``BitterLessonFilm``).

Env knobs:
    BL_QUICK=1   shorten every hold for a fast sanity render
    BL_DELAY=..  override the between-step pause multiplier
    BL_READ=..   override the absolute per-subtitle reading hold (default ~2.6 s)
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


QUICK = os.environ.get("BL_QUICK") == "1"
# Two separate pacing knobs so nothing feels rushed:
#   DELAY scales the small pauses *between* animation steps (motion rhythm).
#   READ  is the absolute hold after a block of text lands, so there is always
#         time to actually read it (the viewer asked to be generous).
# ANIM_SLOW stretches every played animation so transitions aren't abrupt.
DELAY = float(os.environ.get("BL_DELAY", 0.28 if QUICK else 1.0))
READ = float(os.environ.get("BL_READ", 0.35 if QUICK else 2.6))
ANIM_SLOW = 1.0 if QUICK else 1.25
END_HOLD = 0.2 if QUICK else 2.2  # settle held on a finished scene before it wipes

# ---- palette (shared with the Transformer / KV-cache / Mixtral films) ------ #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
FAINT = "#3A4152"       # gridlines / dimmed
HUMAN = "#FF8C42"       # human knowledge (warm orange — hand-crafted, tempting)
COMPUTE = "#5B8DEF"     # computation / general methods (cool blue — it scales)
SEARCH = "#5B8DEF"      # search (blue, compute family)
LEARN = "#2EC4B6"       # learning (teal, compute family)
GOOD = "#3DD68C"        # wins / breakthrough (green)
BAD = "#FF5C5C"         # plateaued / lost (red)
GOLD = "#FFD166"        # accent (rules, thesis, key lines)
ACCENT = GOLD
PANEL = "#151A22"       # card fill

# A clean, well-hinted sans everywhere (Pango's serif default drops spaces at
# these sizes). Set on the *real* Text (we shadowed it above).
FONT = "Helvetica Neue"
_BaseText.set_default(font=FONT)


# ---- small reusable pieces ------------------------------------------------ #
def chip(text, color, w=2.3, h=0.95, fs=26, fill=0.14, tcolor=None, radius=0.14, weight=None):
    """A rounded, tinted box with a centered auto-fitting label. grp[0] is the box."""
    box = RoundedRectangle(
        width=w, height=h, corner_radius=radius,
        stroke_color=color, stroke_width=3,
        fill_color=color, fill_opacity=fill,
    )
    label = Text(text, font_size=fs, color=tcolor or INK, line_spacing=0.8,
                 weight=weight or NORMAL)
    if label.width > w - 0.3:
        label.scale((w - 0.3) / label.width)
    label.move_to(box)
    return VGroup(box, label)


def harrow(start, end, color=MUTED, sw=4, tip=0.2, buff=0.12):
    return Arrow(
        start, end, buff=buff, stroke_width=sw, color=color,
        max_tip_length_to_length_ratio=0.4, tip_length=tip,
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


def rules_glyph(color=HUMAN, w=0.66, h=0.82):
    """A little 'rulebook / knowledge' card: a cover with a few text lines."""
    cover = RoundedRectangle(width=w, height=h, corner_radius=0.07,
                             stroke_color=color, stroke_width=2.5,
                             fill_color=color, fill_opacity=0.14)
    lines = VGroup()
    for _ in range(4):
        lines.add(Line([-w * 0.27, 0, 0], [w * 0.27, 0, 0],
                       stroke_color=color, stroke_width=2.2))
    lines.arrange(DOWN, buff=h * 0.13).move_to(cover)
    lines[-1].scale(0.55, about_point=lines[-1].get_left())  # ragged last line
    return VGroup(cover, lines)


def cpu_glyph(color=COMPUTE, size=0.64):
    """A CPU chip: a square die with little pins on all four sides."""
    body = RoundedRectangle(width=size, height=size, corner_radius=0.07,
                            stroke_color=color, stroke_width=2.6,
                            fill_color=color, fill_opacity=0.14)
    inner = Square(size * 0.46, stroke_color=color, stroke_width=1.8,
                   fill_opacity=0).move_to(body)
    pins = VGroup()
    for i in range(3):
        off = (i - 1) * size * 0.28
        pins.add(Line([off, size / 2, 0], [off, size / 2 + 0.1, 0], stroke_color=color, stroke_width=2.4))
        pins.add(Line([off, -size / 2, 0], [off, -size / 2 - 0.1, 0], stroke_color=color, stroke_width=2.4))
        pins.add(Line([size / 2, off, 0], [size / 2 + 0.1, off, 0], stroke_color=color, stroke_width=2.4))
        pins.add(Line([-size / 2, off, 0], [-size / 2 - 0.1, off, 0], stroke_color=color, stroke_width=2.4))
    return VGroup(body, inner, pins)


def tree_glyph(color=SEARCH):
    """A 3-level search tree. Returned as VGroup(root, level1, level2) so the
    scene can *grow* it one layer at a time (search going deeper)."""
    root_pt = np.array([0.0, 0.5, 0])
    l1_pts = [np.array([-0.45, 0.03, 0]), np.array([0.45, 0.03, 0])]
    l2_pts = [np.array([x, -0.48, 0]) for x in (-0.66, -0.24, 0.24, 0.66)]

    def dot(p, r=0.052):
        return Dot(p, radius=r, color=color)

    def edge(a, b):
        return Line(a, b, stroke_color=color, stroke_width=2)

    root = VGroup(dot(root_pt, 0.06))
    lvl1 = VGroup(edge(root_pt, l1_pts[0]), edge(root_pt, l1_pts[1]),
                  dot(l1_pts[0]), dot(l1_pts[1]))
    lvl2 = VGroup(
        edge(l1_pts[0], l2_pts[0]), edge(l1_pts[0], l2_pts[1]),
        edge(l1_pts[1], l2_pts[2]), edge(l1_pts[1], l2_pts[3]),
        *[dot(p, 0.046) for p in l2_pts],
    )
    return VGroup(root, lvl1, lvl2)


def learn_curve(color=LEARN, w=1.05, h=0.78, top=1.0):
    """A tiny 'learning' chart: faint axes + a rising accuracy curve with dots.
    ``top`` in (0,1] sets how high the curve climbs (so it can be re-grown)."""
    ax = VGroup(
        Line([-w / 2, -h / 2, 0], [w / 2, -h / 2, 0], stroke_color=MUTED, stroke_width=1.6),
        Line([-w / 2, -h / 2, 0], [-w / 2, h / 2, 0], stroke_color=MUTED, stroke_width=1.6),
    )
    xs = np.linspace(0, 1, 7)
    ys = (1 - np.exp(-2.6 * xs)) / (1 - np.exp(-2.6))   # saturating rise 0..1
    pts = [np.array([-w / 2 + x * w, -h / 2 + (y * top) * h, 0]) for x, y in zip(xs, ys)]
    curve = VMobject().set_points_smoothly(pts).set_stroke(color, 3)
    dots = VGroup(*[Dot(p, radius=0.035, color=color) for p in pts])
    return VGroup(ax, curve, dots)


# ========================================================================== #
class _BLBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # ---- timing helpers --------------------------------------------------- #
    def play(self, *anims, **kwargs):
        # stretch every real animation so transitions aren't abrupt, but never
        # scale a bare Wait (reading holds are handled by read()/beat()).
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

    def section_header(self, label, color=GOLD):
        txt = Text(label, font_size=32, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(txt.get_left(), txt.get_right()).next_to(txt, DOWN, buff=0.12)
        line.set_stroke(color=color, width=3)
        return VGroup(txt, line)

    def bottomcap(self, s, color=INK, fs=23, buff=0.42, **kw):
        t = Text(s, font_size=fs, color=color, **kw)
        if t.width > 12.9:
            t.scale_to_fit_width(12.9)
        t.to_edge(DOWN, buff=buff)
        return t

    def cite(self, s):
        return Text(s, font_size=15, color=MUTED, slant=ITALIC).to_edge(DOWN, buff=0.16)

    def set_cap(self, s, color=INK, fs=23):
        """Transform the persistent bottom caption to new text (creates it lazily).

        If the previous caption was already wiped (no longer on screen), fade a
        fresh one in rather than morphing a stale, removed mobject.
        """
        new = self.bottomcap(s, color=color, fs=fs)
        cur = getattr(self, "_cap", None)
        if cur is None or cur not in self.mobjects:
            self._cap = new
            self.play(FadeIn(self._cap, shift=UP * 0.1), run_time=0.6)
        else:
            self.play(Transform(self._cap, new), run_time=0.5)
        return self._cap

    # ---- house-style intro / outro cards ---------------------------------- #
    def _rule_under(self, header, color=GOLD, pad=1.0, drop=0.45):
        return Line(
            [header.get_left()[0] - pad, header.get_bottom()[1] - drop, 0],
            [header.get_right()[0] + pad, header.get_bottom()[1] - drop, 0],
        ).set_stroke(width=3, color=color)

    def play_intro(self):
        header = Text("The Bitter Lesson", font_size=62, color=INK, weight="BOLD")
        header.set(width=min(9.4, header.width))
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=COMPUTE)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        sub = Text("70 years of AI research, distilled into one hard truth",
                   font_size=30, color=MUTED)
        sub.set(width=min(11.0, sub.width))
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.read(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        src = Text("Richard S. Sutton · 2019 · “The Bitter Lesson”",
                   font_size=20, color=MUTED)
        src.next_to(writer, DOWN, buff=0.4)
        self.play(FadeIn(src), run_time=0.8)
        self.read(1.4)
        self.play(FadeOut(VGroup(header, writer, line, src)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=COMPUTE)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = Text("General methods win. Bet on compute — on search and learning.",
                     font_size=25, color=ACCENT)
        recap.set(width=min(11.5, recap.width))
        recap.next_to(writer, DOWN, buff=0.5)
        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap), run_time=0.8)
        self.read(1.6)
        self.play(FadeOut(VGroup(header, line, writer, recap)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 (cold open) — Two roads to intelligence
    # ====================================================================== #
    def scene_roads(self):
        # the thesis, stated first and plainly
        t1 = Text("The biggest lesson from 70 years of AI:", font_size=30, color=MUTED)
        t2 = Text("general methods that leverage computation win —", font_size=34,
                  color=INK, weight="BOLD", t2c={"leverage computation": GOLD})
        t3 = Text("and by a large margin.", font_size=34, color=INK, weight="BOLD")
        thesis = VGroup(t1, t2, t3).arrange(DOWN, buff=0.3)
        for m in thesis:
            if m.width > 12.6:
                m.scale_to_fit_width(12.6)
        self.play(FadeIn(t1, shift=UP * 0.1), run_time=0.8)
        self.play(Write(t2), run_time=1.3)
        self.play(FadeIn(t3, shift=UP * 0.1), run_time=0.7)
        self.read(1.7)
        self.play(FadeOut(thesis), run_time=0.7)

        # then the setup: two roads out of "AI research"
        title = Text("Two ways to build intelligence", font_size=32, color=INK, weight="BOLD")
        title.to_edge(UP, buff=0.5)
        self.play(FadeIn(title, shift=DOWN * 0.15), run_time=0.7)

        origin = chip("AI", INK, w=1.5, h=1.0, fs=30, fill=0.06, weight="BOLD")
        origin.move_to([-5.0, 0.15, 0])

        # road A — human knowledge (orange, the tempting one)
        boxA = RoundedRectangle(width=4.9, height=1.55, corner_radius=0.16,
                                stroke_color=HUMAN, stroke_width=3,
                                fill_color=HUMAN, fill_opacity=0.10).move_to([1.55, 1.5, 0])
        gA = rules_glyph(HUMAN).move_to(boxA.get_center() + LEFT * 1.75)
        tA = Text("Human knowledge", font_size=22, color=HUMAN, weight="BOLD")
        sA = Text("hand-built rules,\nfeatures, expertise", font_size=15, color=INK,
                  line_spacing=0.8)
        colA = VGroup(tA, sA).arrange(DOWN, buff=0.14)
        colA.move_to(boxA.get_center() + RIGHT * 0.7)
        roadA = VGroup(boxA, gA, colA)

        # road B — computation (blue, the one that scales)
        boxB = RoundedRectangle(width=4.9, height=1.55, corner_radius=0.16,
                                stroke_color=COMPUTE, stroke_width=3,
                                fill_color=COMPUTE, fill_opacity=0.10).move_to([1.55, -1.2, 0])
        gB = cpu_glyph(COMPUTE).move_to(boxB.get_center() + LEFT * 1.75)
        tB = Text("Computation", font_size=22, color=COMPUTE, weight="BOLD")
        sB = Text("general methods:\nsearch & learning", font_size=15, color=INK,
                  line_spacing=0.8)
        colB = VGroup(tB, sB).arrange(DOWN, buff=0.14)
        colB.move_to(boxB.get_center() + RIGHT * 0.75)
        roadB = VGroup(boxB, gB, colB)

        aA = harrow(origin.get_right(), boxA.get_left(), color=HUMAN, sw=3)
        aB = harrow(origin.get_right(), boxB.get_left(), color=COMPUTE, sw=3)

        self.play(FadeIn(origin, scale=0.9), run_time=0.6)
        self.play(GrowArrow(aA), FadeIn(roadA, shift=RIGHT * 0.15), run_time=0.8)
        self.play(GrowArrow(aB), FadeIn(roadB, shift=RIGHT * 0.15), run_time=0.8)
        self.set_cap("Teach the machine what we know — or hand it compute and let it work things out.",
                     fs=23)
        self.read(1.7)

        # the tension: which road wins?
        self.play(Indicate(roadB, color=COMPUTE, scale_factor=1.06),
                  aB.animate.set_stroke(width=5), run_time=1.0)
        punch = Text("One of these keeps winning. This is the story of why.",
                     font_size=26, color=ACCENT, weight="BOLD")
        punch.to_edge(DOWN, buff=0.42)
        self.play(FadeOut(self._cap), FadeIn(punch, shift=UP * 0.1), run_time=0.7)
        self.read(1.7)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — The exponential engine (Moore's Law crossover)
    # ====================================================================== #
    def scene_moore(self):
        self._cap = None
        header = self.section_header("1 · The exponential engine", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # --- plot frame ---------------------------------------------------- #
        ax_o = np.array([-5.3, -2.15, 0.0])
        ax_w, ax_h = 9.7, 4.15

        def P(xd, yd):
            return ax_o + np.array([xd * ax_w, yd * ax_h, 0.0])

        def yH(x):   # human knowledge: quick gains, hard plateau
            return 0.50 * (1 - np.exp(-4.0 * x))

        def yC(x):   # general method + compute: starts *below*, then climbs
            return 0.05 * np.exp(3.0 * x) - 0.035

        xax = Arrow(ax_o, P(1.0, 0) + RIGHT * 0.35, buff=0, stroke_width=3, color=MUTED,
                    max_tip_length_to_length_ratio=0.035, tip_length=0.2)
        yax = Arrow(ax_o, P(0, 1.0) + UP * 0.2, buff=0, stroke_width=3, color=MUTED,
                    max_tip_length_to_length_ratio=0.05, tip_length=0.2)
        xlab = Text("computation  ·  time  →", font_size=18, color=MUTED)
        xlab.next_to(xax.get_end(), DOWN, buff=0.18).shift(LEFT * 0.5)
        ylab = Text("capability", font_size=18, color=INK).rotate(PI / 2)
        ylab.next_to(yax, LEFT, buff=0.18)
        self.play(Create(yax), Create(xax), FadeIn(ylab), FadeIn(xlab), run_time=0.9)

        xs = np.linspace(0.02, 1.0, 60)
        human_curve = VMobject().set_points_smoothly([P(x, yH(x)) for x in xs]).set_stroke(HUMAN, 4)
        compute_curve = VMobject().set_points_smoothly([P(x, yC(x)) for x in xs]).set_stroke(COMPUTE, 4)

        # human first — fast, then flat
        hlab = Text("hand-crafted knowledge", font_size=19, color=HUMAN, weight="BOLD")
        hlab.move_to(P(0.30, 0.5) + UP * 0.42)
        self.play(Create(human_curve), run_time=1.5)
        self.play(FadeIn(hlab, shift=UP * 0.1), run_time=0.6)
        self.set_cap("Build in what humans know, and you get fast gains — then a plateau.", fs=23)
        self.read(1.5)

        # compute second — behind, then explodes
        clab = Text("general method + compute", font_size=19, color=COMPUTE, weight="BOLD")
        clab.move_to(P(0.60, 0.86))
        self.play(Create(compute_curve), run_time=1.6)
        self.play(FadeIn(clab, shift=UP * 0.1), run_time=0.6)
        self.set_cap("A general method starts behind — but it rides Moore's Law upward.", fs=23)
        self.read(1.6)

        # crossover point = the *last* place compute overtakes knowledge (the
        # curves are built to cross exactly once inside the sampled range)
        diff = np.array([yC(x) - yH(x) for x in xs])
        sign_changes = np.where(np.diff(np.sign(diff)) != 0)[0]
        xg = float(xs[sign_changes[-1]]) if len(sign_changes) else 0.78

        # --- animated sweep: a cursor rides both curves and we watch compute win #
        t = ValueTracker(0.05)
        vline = always_redraw(lambda: DashedLine(
            P(t.get_value(), 0.0), P(t.get_value(), 0.98),
            stroke_color=GOLD, stroke_width=2.2, dash_length=0.09))
        dotH = always_redraw(lambda: Dot(P(t.get_value(), yH(t.get_value())), radius=0.08, color=HUMAN))
        dotC = always_redraw(lambda: Dot(P(t.get_value(), yC(t.get_value())), radius=0.08, color=COMPUTE))
        # static copies to fade in (never Create/FadeIn an always_redraw mobject)
        v0 = DashedLine(P(0.05, 0), P(0.05, 0.98), stroke_color=GOLD, stroke_width=2.2, dash_length=0.09)
        h0 = Dot(P(0.05, yH(0.05)), radius=0.08, color=HUMAN)
        c0 = Dot(P(0.05, yC(0.05)), radius=0.08, color=COMPUTE)
        self.play(FadeIn(v0), FadeIn(h0), FadeIn(c0), run_time=0.4)
        self.remove(v0, h0, c0)
        self.add(vline, dotH, dotC)
        self.set_cap("Give it enough compute, and the general method overtakes —", fs=23)
        self.play(t.animate.set_value(xg), run_time=1.6, rate_func=linear)
        self.play(Flash(P(xg, yC(xg)), color=GOLD, flash_radius=0.5, line_length=0.3), run_time=0.7)
        self.play(t.animate.set_value(1.0), run_time=1.6, rate_func=linear)
        self.set_cap("— then leaves hand-tuned knowledge far behind.", fs=23)
        self.read(1.4)

        # settle: freeze the cursor, shade the two regimes, name them
        self.remove(vline, dotH, dotC)
        endH = Dot(P(1.0, yH(1.0)), radius=0.08, color=HUMAN)
        endC = Dot(P(1.0, yC(1.0)), radius=0.08, color=COMPUTE)
        self.add(endH, endC)
        leftR = Rectangle(width=xg * ax_w, height=ax_h, stroke_width=0,
                          fill_color=HUMAN, fill_opacity=0.05).move_to(P(xg / 2, 0.5))
        rightR = Rectangle(width=(1 - xg) * ax_w, height=ax_h, stroke_width=0,
                           fill_color=COMPUTE, fill_opacity=0.07).move_to(P((xg + 1) / 2, 0.5))
        self.add(leftR, rightR)
        self.bring_to_back(leftR, rightR)
        # regime labels sit at the TOP of each shaded band, clear of the x-axis label
        st = Text("short term", font_size=16, color=HUMAN).move_to(P(0.20, 0.92))
        lt = Text("long term", font_size=16, color=COMPUTE).move_to(P(0.92, 0.92))
        self.play(FadeIn(leftR), FadeIn(rightR), FadeIn(st), FadeIn(lt), run_time=0.7)

        verdict = Text("Short-term, knowledge leads. Long-term, computation wins — every time.",
                       font_size=24, color=ACCENT, weight="BOLD")
        if verdict.width > 12.9:
            verdict.scale_to_fit_width(12.9)
        verdict.to_edge(DOWN, buff=0.42)
        self.play(FadeOut(self._cap), FadeIn(verdict, shift=UP * 0.1), run_time=0.7)
        self.read(1.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — The same defeat, again and again (case files)
    # ====================================================================== #
    def _case_card(self, domain, year, loser, winner, w=5.75, h=1.72):
        box = RoundedRectangle(width=w, height=h, corner_radius=0.14,
                               stroke_color=FAINT, stroke_width=2.2,
                               fill_color=PANEL, fill_opacity=0.6)
        head = Text(domain, font_size=23, color=INK, weight="BOLD")
        yr = Text(year, font_size=16, color=MUTED)

        def row(mark, s, col, fs):
            txt = Text(s, font_size=fs, color=col)
            if txt.width > w - 1.25:
                txt.scale((w - 1.25) / txt.width)
            mark.next_to(txt, LEFT, buff=0.18)
            return VGroup(mark, txt)

        lose_row = row(make_cross(BAD, sw=5, scale=0.7), loser, HUMAN, 15)
        win_row = row(make_tick(GOOD, sw=5, scale=0.8), winner, COMPUTE, 16)
        body = VGroup(head, lose_row, win_row).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        body.move_to(box).align_to(box, LEFT).shift(RIGHT * 0.32)
        yr.move_to([box.get_right()[0] - 0.32 - yr.width / 2, head.get_center()[1], 0])
        return VGroup(box, body, yr), win_row

    def scene_pattern(self):
        header = self.section_header("2 · The same defeat, again and again", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        specs = [
            ("Chess", "1997", "grandmaster heuristics & opening books", "brute-force deep search — Deep Blue"),
            ("Go", "2016", "hand-coded shapes & Go intuition", "self-play + search — AlphaGo / Zero"),
            ("Speech", "1970s →", "phonemes & vocal-tract models", "statistics, then deep learning"),
            ("Vision", "2012", "SIFT, edges, hand-built features", "deep conv nets — ImageNet"),
        ]
        cards, wins = [], []
        for d, y, lo, wi in specs:
            c, w = self._case_card(d, y, lo, wi)
            cards.append(c)
            wins.append(w)
        grid = VGroup(*cards).arrange_in_grid(rows=2, cols=2, buff=(0.5, 0.45))
        grid.move_to([0, 0.18, 0])

        self.set_cap("Each field started with human expertise. Watch what beat it.", fs=23)
        for c in cards:
            self.play(FadeIn(c, shift=UP * 0.12), run_time=0.55)
            self.beat(0.7)
        self.read(1.4)

        # drive the pattern home: pulse every blue "winner" at once
        self.play(LaggedStart(*[Indicate(w, color=COMPUTE, scale_factor=1.08) for w in wins],
                              lag_ratio=0.12, run_time=1.4))
        self.set_cap("Same script every time: hand-built knowledge stalls; scaled search & learning break through.",
                     fs=22)
        self.play(FadeIn(self.cite("Deep Blue 1997 · AlphaGo 2016 · DARPA speech · ImageNet 2012")),
                  run_time=0.4)
        self.read(1.9)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — The only two things that scale: search & learning
    # ====================================================================== #
    def scene_scale(self):
        self._cap = None
        header = self.section_header("3 · The two things that scale", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # a compute "fuel" bar on the left that fills as compute grows
        track = RoundedRectangle(width=0.56, height=3.1, corner_radius=0.12,
                                 stroke_color=MUTED, stroke_width=2.5, fill_opacity=0.0)
        track.move_to([-5.55, 0.15, 0])
        cap_top = Text("more\ncompute", font_size=16, color=GOLD, line_spacing=0.8, weight="BOLD")
        cap_top.next_to(track, UP, buff=0.16)
        up_arr = Text("↑", font_size=22, color=GOLD).next_to(track, DOWN, buff=0.12)
        moore = Text("Moore's Law", font_size=13, color=MUTED).next_to(up_arr, DOWN, buff=0.1)

        def fuel(frac):
            f = Rectangle(width=0.5, height=max(0.02, frac * 3.0), stroke_width=0,
                          fill_color=GOLD, fill_opacity=0.85)
            f.move_to(track.get_bottom(), DOWN).shift(UP * 0.05)
            return f

        fill = fuel(0.12)
        self.play(Create(track), FadeIn(cap_top), FadeIn(up_arr), FadeIn(moore),
                  FadeIn(fill), run_time=0.8)

        # two engines on the right
        def engine(title, sub, glyph, color, center):
            box = RoundedRectangle(width=4.35, height=1.95, corner_radius=0.16,
                                   stroke_color=color, stroke_width=3,
                                   fill_color=color, fill_opacity=0.09).move_to(center)
            glyph.move_to(box.get_center() + LEFT * 1.35)
            tt = Text(title, font_size=24, color=color, weight="BOLD")
            ss = Text(sub, font_size=15, color=INK, line_spacing=0.8)
            col = VGroup(tt, ss).arrange(DOWN, buff=0.16)
            if col.width > 2.6:
                col.scale(2.6 / col.width)
            col.move_to(box.get_center() + RIGHT * 0.7)
            return VGroup(box, glyph, col), box

        tree = tree_glyph(SEARCH).scale(0.72)
        s_engine, s_box = engine("Search", "explore many futures,\nkeep what wins",
                                 tree, SEARCH, [2.15, 1.42, 0])
        curve = learn_curve(LEARN, top=0.5)
        l_engine, l_box = engine("Learning", "improve from data\n& from self-play",
                                 curve, LEARN, [2.15, -1.12, 0])

        aS = harrow(track.get_right(), s_box.get_left(), color=GOLD, sw=2.6)
        aL = harrow(track.get_right(), l_box.get_left(), color=GOLD, sw=2.6)

        # reveal the two engines (start with search shallow / learning short)
        self.set_cap("Only two techniques scale arbitrarily with compute.", fs=23)
        self.play(GrowArrow(aS), GrowArrow(aL), run_time=0.6)
        self.play(FadeIn(s_engine[0]), FadeIn(s_engine[2]),
                  FadeIn(tree[0]), FadeIn(tree[1]), run_time=0.7)
        self.play(FadeIn(l_engine[0]), FadeIn(l_engine[2]),
                  FadeIn(curve), run_time=0.7)
        self.read(1.3)
        self.set_cap("Search explores possibilities; learning improves from experience.", fs=23)
        self.read(1.4)

        # feed them compute — they grow (search goes deeper, learning climbs higher)
        def feed(new_frac, new_curve_top, add_tree_level):
            anims = [Transform(fill, fuel(new_frac)),
                     ShowPassingFlash(aS.copy().set_color(GOLD).set_stroke(width=5), time_width=0.5),
                     ShowPassingFlash(aL.copy().set_color(GOLD).set_stroke(width=5), time_width=0.5)]
            new_curve = learn_curve(LEARN, top=new_curve_top).move_to(curve)
            anims.append(Transform(curve, new_curve))
            self.play(*anims, run_time=1.0)
            if add_tree_level:
                self.play(Create(tree[2]), run_time=0.7)

        self.set_cap("Add compute, and they simply get better — search deeper, learn more.", fs=23)
        feed(0.55, 0.78, add_tree_level=True)
        self.read(1.0)
        feed(1.0, 1.0, add_tree_level=False)
        self.play(Indicate(s_engine, color=SEARCH, scale_factor=1.05),
                  Indicate(l_engine, color=LEARN, scale_factor=1.05), run_time=0.9)
        self.read(1.2)

        # the punchline + a tie-back to the case files
        note = Text("No ceiling. Everything else is a detour.",
                    font_size=26, color=ACCENT, weight="BOLD")
        note.to_edge(DOWN, buff=0.42)
        self.play(FadeOut(self._cap), FadeIn(note, shift=UP * 0.1), run_time=0.7)
        self.read(1.4)
        tie = Text("Deep Blue searched.  AlphaZero searched and learned.",
                   font_size=20, color=MUTED)
        tie.next_to(note, UP, buff=0.3)
        self.play(FadeIn(tie), run_time=0.6)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — Why it's bitter, and what to build instead
    # ====================================================================== #
    def scene_lesson(self):
        self._cap = None
        header = self.section_header("4 · The bitter lesson", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # PART A — why is it "bitter"?
        q = Text("So why is it the “bitter” lesson?", font_size=34, color=GOLD, weight="BOLD")
        q.move_to([0, 2.35, 0])
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.8)
        self.read(1.0)

        b1 = VGroup(make_tick(HUMAN, sw=5, scale=0.85),
                    Text("Building in what we know feels good — and helps at first.",
                         font_size=24, color=INK))
        b2 = VGroup(make_cross(BAD, sw=5, scale=0.85),
                    Text("But it plateaus — and blocks the methods that would scale.",
                         font_size=24, color=INK))
        b3 = Text("“The knowledge-based researchers were not good losers.”",
                  font_size=22, color=MUTED, slant=ITALIC)
        for b in (b1, b2):
            b[0].next_to(b[1], LEFT, buff=0.22)
        rows = VGroup(b1, b2, b3).arrange(DOWN, buff=0.4, aligned_edge=LEFT)
        for r in rows:
            if r.width > 12.4:
                r.scale_to_fit_width(12.4)
        rows.move_to([0, 0.05, 0])
        self.play(FadeIn(b1, shift=UP * 0.1), run_time=0.7)
        self.read(1.2)
        self.play(FadeIn(b2, shift=UP * 0.1), run_time=0.7)
        self.read(1.4)
        self.play(FadeIn(b3, shift=UP * 0.1), run_time=0.7)
        self.read(1.6)

        self.play(FadeOut(rows), FadeOut(q), run_time=0.6)

        # PART B — what should we build in instead?
        q2 = Text("So what should we build in?", font_size=32, color=INK, weight="BOLD")
        q2.move_to([0, 2.5, 0])
        self.play(FadeIn(q2, shift=DOWN * 0.1), run_time=0.7)
        self.read(0.9)

        # left: a capped box crammed with hand-written rules (can't fit it all)
        capbox = RoundedRectangle(width=4.3, height=2.5, corner_radius=0.16,
                                  stroke_color=HUMAN, stroke_width=3,
                                  fill_color=HUMAN, fill_opacity=0.07).move_to([-3.5, -0.25, 0])
        tags = VGroup()
        for _ in range(10):
            tags.add(RoundedRectangle(width=1.15, height=0.34, corner_radius=0.08,
                                      stroke_color=HUMAN, stroke_width=1.6,
                                      fill_color=HUMAN, fill_opacity=0.16))
        tags.arrange_in_grid(rows=4, cols=3, buff=(0.16, 0.16))
        tags.scale_to_fit_width(capbox.width - 0.4).move_to(capbox.get_center() + DOWN * 0.1)
        ceil = Line(capbox.get_corner(UL) + RIGHT * 0.12 + DOWN * 0.06,
                    capbox.get_corner(UR) + LEFT * 0.12 + DOWN * 0.06).set_stroke(BAD, 5)
        capttl = Text("the contents of a mind", font_size=18, color=HUMAN, weight="BOLD")
        capttl.next_to(capbox, UP, buff=0.16)
        capsub = Text("endlessly complex — you\ncan't hand-code it all", font_size=15, color=BAD,
                      line_spacing=0.8).next_to(capbox, DOWN, buff=0.18)

        # right: an open-ended engine that discovers (rays expanding out)
        core = RoundedRectangle(width=1.5, height=1.5, corner_radius=0.16,
                                stroke_color=COMPUTE, stroke_width=3,
                                fill_color=COMPUTE, fill_opacity=0.12).move_to([3.5, -0.25, 0])
        gear = cpu_glyph(COMPUTE, size=0.7).move_to(core)
        rays = VGroup()
        for k in range(10):
            ang = k * TAU / 10
            d = np.array([np.cos(ang), np.sin(ang), 0])
            rays.add(Line(core.get_center() + d * 1.0, core.get_center() + d * 1.55,
                          stroke_color=GOLD, stroke_width=3))
        engttl = Text("a method that discovers", font_size=18, color=COMPUTE, weight="BOLD")
        engttl.move_to([core.get_center()[0], 0, 0]).match_y(capttl)  # align with the left title
        engsub = Text("open-ended — no ceiling", font_size=15, color=GOOD)
        engsub.next_to(capsub, RIGHT, buff=0.0).match_y(capsub)
        engsub.set_x(core.get_center()[0])

        self.play(FadeIn(capbox), FadeIn(capttl),
                  LaggedStart(*[FadeIn(t) for t in tags], lag_ratio=0.05, run_time=0.9))
        self.play(Create(ceil), FadeIn(capsub), run_time=0.6)
        self.set_cap("Don't build in the contents of the mind — they're endlessly complex.", fs=23)
        self.read(1.5)

        self.play(FadeIn(core), FadeIn(gear), FadeIn(engttl), run_time=0.7)
        self.play(LaggedStart(*[GrowFromCenter(r) for r in rays], lag_ratio=0.05, run_time=0.9),
                  FadeIn(engsub))
        self.set_cap("Build in the meta-methods that can find that complexity for themselves.", fs=23)
        self.read(1.7)

        # the hero quote
        self.play(FadeOut(self._cap), run_time=0.4)
        quote = VGroup(
            Text("Build agents that can discover like we can —", font_size=27, color=INK, weight="BOLD"),
            Text("not agents that contain what we've already discovered.", font_size=27,
                 color=ACCENT, weight="BOLD"),
        ).arrange(DOWN, buff=0.22)
        for m in quote:
            if m.width > 12.9:
                m.scale_to_fit_width(12.9)
        quote.to_edge(DOWN, buff=0.4)
        self.play(Write(quote[0]), run_time=1.1)
        self.play(Write(quote[1]), run_time=1.1)
        self.read(2.0)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Closing takeaway (before the outro card)
    # ====================================================================== #
    def scene_recap(self):
        lines = VGroup(
            Text("The Bitter Lesson, in one breath:", font_size=30, color=MUTED),
            Text("General methods that scale with compute", font_size=32, color=INK, weight="BOLD"),
            Text("beat the knowledge we hand-build in.", font_size=32, color=INK, weight="BOLD"),
            Text("Search and learning are the only things that scale.", font_size=25, color=COMPUTE),
            Text("So build a machine that discovers — don't just teach it what you know.",
                 font_size=25, color=ACCENT),
        ).arrange(DOWN, buff=0.32)
        for m in lines:
            if m.width > 12.9:
                m.scale_to_fit_width(12.9)
        self.play(FadeIn(lines[0]), run_time=0.6)
        self.read(0.5)
        self.play(Write(lines[1]), run_time=0.9)
        self.play(Write(lines[2]), run_time=0.9)
        self.read(1.0)
        self.play(FadeIn(lines[3], shift=UP * 0.1), run_time=0.7)
        self.read(1.0)
        self.play(FadeIn(lines[4], shift=UP * 0.12), run_time=0.7)
        self.read(1.8)
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_roads()
        self.scene_moore()
        self.scene_pattern()
        self.scene_scale()
        self.scene_lesson()
        self.scene_recap()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_BLBase):
    def construct(self):
        self.play_intro()


class Roads(_BLBase):
    def construct(self):
        self.scene_roads()


class Moore(_BLBase):
    def construct(self):
        self.scene_moore()


class Pattern(_BLBase):
    def construct(self):
        self.scene_pattern()


class Scale(_BLBase):
    def construct(self):
        self.scene_scale()


class Lesson(_BLBase):
    def construct(self):
        self.scene_lesson()


class Recap(_BLBase):
    def construct(self):
        self.scene_recap()


class Outro(_BLBase):
    def construct(self):
        self.play_outro()


class BitterLessonFilm(_BLBase):
    """The whole short film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    BitterLessonFilm().render()

"""Fourier-series ("epicycle") drawing of a portrait, with a theory interlude.

Structure (one continuous animation, rendered by the ``FourierPortrait`` scene):

    1. intro card        -- house-style title (see animations/2024/Intro.py)
    2. the drawing       -- ~200 rotating vectors trace louis.png from a single
                            closed path (data/louis_path.npy, made by
                            generate_path.py)
    3. the theory        -- the complex Fourier series + coefficients + the DFT
                            we actually used, with a live 3-vector mini-demo
    4. intro card again  -- the same intro, as a bookend

The individual sections are also exposed as their own scenes (``Intro``,
``Drawing``, ``Theory``) so they can be rendered in isolation while iterating.

Env knobs (handy while iterating):
    FOURIER_QUICK=1   fewer vectors + shorter draw time for a fast test render
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from manim import *

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "louis_path.npy"
IMG = HERE / "assets" / "louis.png"

QUICK = os.environ.get("FOURIER_QUICK") == "1"
NUM_VECTORS = 90 if QUICK else 200     # epicycles drawn during the performance
CIRCLE_COUNT = 28 if QUICK else 50     # how many of them also show their circle
DRAW_TIME = 9 if QUICK else 24         # seconds for the pen to close the loop
DRAW_RES = 4000                        # samples of the analytic curve we reveal

# palette
VEC_COLOR = BLUE_B
CIRCLE_COLOR = BLUE_D
PEN_COLOR = YELLOW
INK = "#FFF7E6"     # warm white for the drawn line
GLOW = "#FFE08A"    # soft glow behind the pen line
ACCENT = YELLOW
EXP_COLOR = TEAL


def load_epicycles(num_vectors: int):
    """Load the path and return (freqs, coeffs) for the ``num_vectors`` lowest
    frequencies, ordered 0, +1, -1, +2, -2, ... so partial sums add detail."""
    z = np.load(DATA)
    n = len(z)
    coeffs = np.fft.fft(z) / n
    freqs = np.round(np.fft.fftfreq(n, d=1.0 / n)).astype(int)
    # order by |frequency|, positive before negative on ties -> nice nesting
    order = sorted(range(n), key=lambda k: (abs(freqs[k]), -freqs[k]))
    order = order[:num_vectors]
    return freqs[order], coeffs[order]


def path_to_corners(z: np.ndarray) -> np.ndarray:
    """Complex path -> (N+1, 3) closed corner array for a VMobject."""
    pts = np.column_stack([z.real, z.imag, np.zeros_like(z.real)])
    return np.vstack([pts, pts[:1]])


class _FourierBase(Scene):
    # ---- 1 & 4: the house-style intro card ------------------------------- #
    def introduction(self, title1, title2):
        header = Tex(title1)
        header.set_width(9)
        from_pos = [header.get_left()[0] - 1, header.get_bottom()[1] - 0.5, 0]
        to_pos = [header.get_right()[0] + 1, header.get_bottom()[1] - 0.5, 0]
        line = Line(from_pos, to_pos)
        writer = Tex("Created by Ptolémé")
        writer_pos = [(line.get_left()[0] + line.get_right()[0]) / 2, line.get_bottom()[1] - 1, 0]
        writer.move_to(writer_pos)

        self.play(Write(header), Write(line))
        self.wait(0.5)
        self.play(Transform(header, Tex(title2)))
        self.play(Write(writer))
        self.wait(2)
        return VGroup(header, writer, line)

    def play_intro(self):
        group = self.introduction(
            "Handbook of Statistics — Fourier Series",
            "Drawing a portrait with rotating vectors",
        )
        self.play(FadeOut(group))
        self.wait(0.5)

    # ---- 2: the epicycle drawing ----------------------------------------- #
    def section_draw(self):
        z = np.load(DATA)
        freqs, coeffs = load_epicycles(NUM_VECTORS)

        # (a) show the real painting: "an image is just a curve in disguise"
        img = ImageMobject(str(IMG)).scale_to_fit_height(6.2)
        caption = Tex("A picture is just a point moving through the plane\\dots") \
            .scale(0.8).to_edge(DOWN)
        self.play(FadeIn(img), FadeIn(caption))
        self.wait(1.5)
        self.play(FadeOut(img), FadeOut(caption))

        # (b) set up the rotating-vector machine
        formula = MathTex(r"f(t)=\sum_{k} c_k\,e^{\,2\pi i k t}").to_edge(UP)
        count = Tex(f"{NUM_VECTORS} rotating vectors").scale(0.6) \
            .to_corner(DR).set_opacity(0.7)
        self.play(Write(formula), FadeIn(count))

        t = ValueTracker(0.0)

        def pen_point():
            tt = t.get_value()
            p = np.sum(coeffs * np.exp(2j * np.pi * freqs * tt))
            return np.array([p.real, p.imag, 0.0])

        def make_vectors():
            tt = t.get_value()
            terms = coeffs * np.exp(2j * np.pi * freqs * tt)
            tips = np.cumsum(terms)
            centers = np.concatenate([[0.0 + 0.0j], tips[:-1]])
            g = VGroup()
            for k in range(len(freqs)):
                cen = np.array([centers[k].real, centers[k].imag, 0.0])
                tip = np.array([tips[k].real, tips[k].imag, 0.0])
                r = abs(coeffs[k])
                if k < CIRCLE_COUNT and r > 0.03:
                    g.add(Circle(radius=r, stroke_width=1.2, color=CIRCLE_COLOR)
                          .set_stroke(opacity=0.4).move_to(cen))
                g.add(Line(cen, tip, stroke_width=1.9, color=VEC_COLOR))
            return g

        # The line we reveal is the *exact* analytic curve these vectors trace
        # (the band-limited partial sum), sampled densely -> smooth and crisp at
        # any frame rate, instead of a jagged frame-sampled TracedPath.
        ts = np.linspace(0.0, 1.0, DRAW_RES, endpoint=False)
        recon = (coeffs[:, None] * np.exp(2j * np.pi * np.outer(freqs, ts))).sum(axis=0)
        recon_pts = np.column_stack([recon.real, recon.imag, np.zeros(DRAW_RES)])
        recon_pts = np.vstack([recon_pts, recon_pts[:1]])  # close the loop

        glow = VMobject(stroke_color=GLOW, stroke_width=9).set_stroke(opacity=0.25)
        ink = VMobject(stroke_color=INK, stroke_width=3.2)

        def reveal(m):
            n = int(t.get_value() * (len(recon_pts) - 1)) + 2
            m.set_points_as_corners(recon_pts[:n])

        for m in (glow, ink):
            reveal(m)
            m.add_updater(reveal)

        vectors = always_redraw(make_vectors)
        pen_dot = always_redraw(lambda: Dot(pen_point(), radius=0.05, color=PEN_COLOR))

        self.add(glow, ink, vectors, pen_dot)
        self.play(t.animate.set_value(1.0), run_time=DRAW_TIME, rate_func=linear)

        for m in (vectors, pen_dot, glow, ink):
            m.clear_updaters()

        # (c) sharpen: morph the band-limited line into the exact outline
        outline = VMobject(stroke_color=INK, stroke_width=3.2)
        outline.set_points_as_corners(path_to_corners(z))
        self.play(FadeOut(vectors), FadeOut(pen_dot), FadeOut(glow),
                  Transform(ink, outline), run_time=1.0)

        # (d) fade the painting back in behind, to show the match
        match = ImageMobject(str(IMG)).scale_to_fit_height(6.2).set_opacity(0.0)
        self.add(match)
        self.bring_to_back(match)
        self.play(match.animate.set_opacity(0.45), FadeOut(formula), run_time=1.5)
        self.wait(2)
        self.play(FadeOut(match), FadeOut(count))
        self.wait(0.5)
        self.play(FadeOut(ink))

    # ---- 3: the theory ---------------------------------------------------- #
    def _mini_epicycle(self, center, scale):
        """A small 3-vector demo that draws a little curve, to make 'sum of
        rotating vectors' concrete next to the formulas. Position and scale are
        baked into the point functions (updaters would otherwise override any
        group transform), so the pieces can be added/faded individually."""
        demo_freqs = np.array([0, 1, -2])
        demo_coeffs = np.array([0.0 + 0.0j, 1.0 + 0.0j, 0.45j])
        s = ValueTracker(0.0)

        def to_pt(cz):
            return center + scale * np.array([cz.real, cz.imag, 0.0])

        def tip(tt):
            return np.sum(demo_coeffs * np.exp(2j * np.pi * demo_freqs * tt))

        def make():
            tt = s.get_value()
            terms = demo_coeffs * np.exp(2j * np.pi * demo_freqs * tt)
            tips = np.cumsum(terms)
            centers = np.concatenate([[0.0 + 0.0j], tips[:-1]])
            g = VGroup()
            for k in range(len(demo_freqs)):
                cen = to_pt(centers[k])
                tp = to_pt(tips[k])
                if abs(demo_coeffs[k]) > 1e-6:
                    g.add(Circle(radius=abs(demo_coeffs[k]) * scale, stroke_width=1.2,
                                 color=CIRCLE_COLOR).set_stroke(opacity=0.4).move_to(cen))
                g.add(Line(cen, tp, stroke_width=2, color=VEC_COLOR))
            return g

        vecs = always_redraw(make)
        dot = always_redraw(lambda: Dot(to_pt(tip(s.get_value())), radius=0.04, color=PEN_COLOR))
        trace = TracedPath(lambda: to_pt(tip(s.get_value())),
                           stroke_color=ACCENT, stroke_width=2.5)
        return vecs, dot, trace, s

    def _layout_below(self, title, *mobjects, gap=0.5, top_buff=0.55,
                      max_h=5.4, max_w=12.4):
        """Stack ``mobjects`` vertically, scale them to fit the frame, and place
        the block just under ``title``. This is what keeps a page of formulas
        from ever running off the bottom edge (the old chained ``next_to`` did)."""
        body = VGroup(*mobjects).arrange(DOWN, buff=gap)
        scale = min(1.0, max_h / body.height, max_w / body.width)
        if scale < 1.0:
            body.scale(scale)
        body.next_to(title, DOWN, buff=top_buff)
        spill = body.get_bottom()[1] - (-config.frame_y_radius + 0.3)
        if spill < 0:                       # nudge up if it still reaches too low
            body.shift(UP * (-spill))
        return body

    def section_theory(self):
        title = Tex("The idea behind the drawing").to_edge(UP).set_color(ACCENT)
        self.play(Write(title))

        # ---- page 1: a drawing is a path; Fourier = a sum of rotating vectors
        intro = Tex("A drawing is a \\emph{path}: a point moving in the plane over time.") \
            .scale(0.8)
        f_def = MathTex(r"f(t) = x(t) + i\,y(t), \qquad t \in [0,1]")
        thm = Tex("Fourier: every periodic path is a sum of rotating vectors.").scale(0.8)
        series = MathTex(
            r"f(t)", r"=", r"\sum_{k=-\infty}^{\infty}", r"c_k", r"\,e^{\,2\pi i k t}"
        ).scale(1.15)
        series.set_color_by_tex("c_k", ACCENT)
        series.set_color_by_tex("e^{\\,2\\pi i k t}", EXP_COLOR)
        self._layout_below(title, intro, f_def, thm, series, gap=0.55)

        self.play(Write(intro))
        self.play(Write(f_def))
        self.wait(0.4)
        self.play(Write(thm))
        self.play(Write(series))
        self.wait(0.4)

        brace = Brace(VGroup(series[3], series[4]), DOWN, buff=0.12)
        note = brace.get_text("length $|c_k|$, phase $\\arg c_k$, speed $k$")
        note.scale(0.7)
        self.play(GrowFromCenter(brace), FadeIn(note, shift=0.15 * DOWN))
        self.wait(0.8)

        # live 3-vector mini demo, lower-right, clear of the formulas
        vecs, dot, trace, s = self._mini_epicycle(RIGHT * 5.0 + DOWN * 2.4, 0.55)
        self.add(trace, vecs, dot)
        self.play(s.animate.set_value(1.0), run_time=5, rate_func=linear)
        for m in (vecs, dot, trace):
            m.clear_updaters()
        self.wait(0.5)

        self.play(FadeOut(VGroup(intro, f_def, thm, series, brace, note)),
                  FadeOut(vecs), FadeOut(dot), FadeOut(trace))
        self.remove(vecs, dot, trace)   # belt-and-braces: no traced-path ghost

        # ---- page 2: the coefficient (continuous) ---------------------------
        coeff = MathTex(r"c_k = \int_0^1 f(t)\, e^{-2\pi i k t}\, dt")
        coeff.set_color_by_tex_to_color_map({"c_k": ACCENT})
        because = Tex("Project the path onto each pure rotation to read off its vector.") \
            .scale(0.75).set_opacity(0.9)
        self._layout_below(title, coeff, because, gap=0.6)

        self.play(Write(coeff))
        self.play(FadeIn(because, shift=0.2 * UP))
        self.wait(1.5)
        self.play(FadeOut(VGroup(coeff, because)))

        # ---- page 3: the discrete version we actually used ------------------
        disc_txt = Tex("In practice we sample the path at $N$ points\\,---\\,the DFT:").scale(0.85)
        dft = MathTex(
            r"c_k = \frac{1}{N}\sum_{n=0}^{N-1} f(t_n)\, e^{-2\pi i k n / N},"
            r"\qquad t_n = \tfrac{n}{N}"
        )
        real_form = MathTex(
            r"f(t) = \frac{a_0}{2} + \sum_{n\ge 1}\big[a_n\cos(2\pi n t) + b_n\sin(2\pi n t)\big]"
        ).set_opacity(0.9)
        kicker = Tex(f"We keep the {NUM_VECTORS} slowest vectors\\,---\\,and the face appears.") \
            .scale(0.85).set_color(ACCENT)
        self._layout_below(title, disc_txt, dft, real_form, kicker, gap=0.55)

        self.play(Write(disc_txt))
        self.play(Write(dft))
        self.wait(0.4)
        self.play(Write(real_form))
        self.wait(0.4)
        self.play(Write(kicker))
        self.wait(2)

        self.play(FadeOut(VGroup(title, disc_txt, dft, real_form, kicker)))
        self.wait(0.3)


class Intro(_FourierBase):
    def construct(self):
        self.play_intro()


class Drawing(_FourierBase):
    def construct(self):
        self.section_draw()


class Theory(_FourierBase):
    def construct(self):
        self.section_theory()


class FourierPortrait(_FourierBase):
    """The full animation: intro -> drawing -> theory -> intro (bookend)."""

    def construct(self):
        self.play_intro()
        self.section_draw()
        self.section_theory()
        self.play_intro()

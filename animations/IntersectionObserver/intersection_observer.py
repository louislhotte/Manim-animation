"""IntersectionObserver in React — a ~3-minute no-voiceover explainer, house style.

Scrolling a long list and reacting when items come into view is one of the most
common jobs on the front end: infinite scroll, lazy-loading images, "mark as
read" analytics. The naive way is to listen for every ``scroll`` event and call
``getBoundingClientRect()`` by hand. That runs on the main thread, on every pixel
of scroll, and forces the browser to re-measure layout each time.

``IntersectionObserver`` flips it around: you hand the browser a list of target
elements and a callback, and the browser tells you *asynchronously* when an
element crosses a visibility threshold you defined. In React you wire it up once
inside a ``useEffect`` (create the observer, ``observe`` your nodes) and tear it
down in the cleanup (``disconnect``).

The film:

    1. The old way    -- scroll listener + getBoundingClientRect, on the main thread
    2. The idea       -- give the browser targets + a callback; root / rootMargin / threshold
    3. The API        -- new IntersectionObserver(cb, opts); entries; entry.isIntersecting
    4. Count as you scroll ★  -- the real React hook, a scrolling viewport, and a live
                                 "seen" counter that increments the exact moment each
                                 card crosses the threshold line; unobserve so it counts
                                 once; a sentinel triggers "load more" (infinite scroll)
    5. Recap          -- the mental model in three lines

The star (scene 4) is exactly the request: a strict scrolling example plus a
count. The count is not faked. Every card has a known position; a single updater
moves the list by a ``scroll`` ValueTracker and counts, every frame, how many
card centers have risen past the threshold line. The on-screen number is that
count, so it is provably correct.

Everything uses ``Text`` (Pango), never ``Tex`` — no LaTeX toolchain. Code is set
in Menlo. Nothing is a screenshot: the browser frame, the cards, the cursor and
the spinner are all drawn Manim mobjects.

Scenes are exposed individually (``Intro``, ``Problem``, ``Idea``, ``Api``,
``Count``, ``Recap``, ``Outro``) and as one film (``IntersectionObserverReact``).

Env knobs:
    IO_QUICK=1     collapse every reading hold (and the end-holds) for a fast render
    IO_DELAY=1.2   override the reading-hold multiplier (seconds per "beat")
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


QUICK = os.environ.get("IO_QUICK") == "1"
# Single pacing knob: every reading "hold" is self.beat(t) == wait(t * DELAY).
# Animation run-times are NOT scaled, so the piece stays dynamic — DELAY only
# sets how long text lingers. Each scene ends on a short hold (self.settle).
DELAY = float(os.environ.get("IO_DELAY", "0.28" if QUICK else "2.4"))
END_HOLD = 0.2 if QUICK else 2.5

# ---- palette -------------------------------------------------------------- #
BG = "#0E1117"        # dark slate background
INK = "#F5F3EF"       # warm white text
MUTED = "#8A93A6"     # secondary text / axes
FAINT = "#2A3140"     # gridlines / tracks
ACCENT = "#FFD166"    # highlight (gold) — the threshold line
GOOD = "#3DD68C"      # visible / counted (green)
BAD = "#FF5C5C"       # bad / wasteful (red)
REACT = "#61DAFB"     # React cyan — brand accent
STATE_C = "#C792EA"   # state (purple)
EFFECT_C = "#FFCB6B"  # effects (gold)

# ---- code (Night-Owl-ish) palette ----------------------------------------- #
MONO = "Menlo"
CODE_FS = 19
PLAIN = "#D6DEEB"     # default code text
COMMENT = "#5F6B7E"   # comments (grey-blue)
HOOK = "#FFCB6B"      # the hooks (gold)
KW = "#C792EA"        # keywords: function / const / return / new (purple)
FN = "#82AAFF"        # calls / methods (blue)
VAL = "#F78C6C"       # options / literals (orange)
IO_C = "#61DAFB"      # the IntersectionObserver name itself (cyan)
DEVICE_BG = "#121A26"  # mock-app body

# distinctive, non-overlapping keys → safe substring colouring for every code line
CODE_T2C = {
    "function": KW, "const": KW, "return": KW, "new": KW,
    "useState": HOOK, "useEffect": HOOK, "useRef": HOOK,
    "IntersectionObserver": IO_C,
    "isIntersecting": GOOD,
    "setSeen": FN, "forEach": FN, "observe": FN, "unobserve": FN,
    "disconnect": FN, "addEventListener": FN, "getBoundingClientRect": FN,
    "threshold": VAL, "rootMargin": VAL, "root": VAL,
    "null": VAL, "true": VAL, "false": VAL,
}


def _safe_t2c(s):
    """Per-line text→colour map, pruned so no key overlaps another.

    Manim's ``t2c`` raises on overlapping colour ranges — even when the colour is
    identical (e.g. ``observe`` sitting inside ``unobserve``, or ``root`` inside
    ``rootMargin``). Keep only the keys present in this line, and drop any key
    that is a substring of another present key so their ranges can never collide.
    """
    present = {k: v for k, v in CODE_T2C.items() if k in s}
    keys = list(present)
    return {k: v for k, v in present.items()
            if not any(k != o and k in o for o in keys)}


# ========================================================================== #
# small reusable pieces
# ========================================================================== #
def make_tick(color=GOOD, sw=6, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])])
    return v.set_stroke(color=color, width=sw).scale(scale)


def arr(a, b, color=MUTED, sw=4, tip=0.22, buff=0.1):
    """A straight arrow between two *points*.

    Always pass explicit points (``chip.get_right()`` / ``.get_left()``), never a
    compound Mobject — Manim resolves a bare mobject endpoint through
    ``get_boundary_point`` on its raw bezier cloud, which for a rectangle+text
    group is not the clean mid-edge and comes out diagonal.
    """
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    return Arrow(a, b, buff=buff, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=tip / max(np.linalg.norm(b - a), 1e-3))


def chip(text, color, fs=22, fill=0.14, w=None, h=0.6, tcolor=None):
    label = Text(text, font_size=fs, color=tcolor or INK)
    width = (label.width + 0.5) if w is None else w
    box = RoundedRectangle(width=width, height=h, corner_radius=0.12,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=fill)
    label.move_to(box)
    return VGroup(box, label)


def code_line_1(s, fs=30, t2c=None):
    """One code line as a *single* ``Text`` — correct kerning, natural monospace
    spacing. Ligatures disabled so one glyph == one character (``glyph_slice``
    can index by raw string position)."""
    return Text(s, font=MONO, font_size=fs, color=PLAIN,
                disable_ligatures=True, t2c=(t2c if t2c is not None else _safe_t2c(s)))


def glyph_slice(mob, full, token, occ=0):
    """Sub-mobjects of ``mob`` covering ``token`` in ``full`` (Manim makes one
    submobject per character, spaces included → index directly)."""
    start = -1
    for _ in range(occ + 1):
        start = full.index(token, start + 1)
    return mob[start:start + len(token)]


def make_button(label, color=REACT, fill=0.16, w=2.4, h=0.66, fs=21):
    box = RoundedRectangle(width=w, height=h, corner_radius=0.14,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=fill)
    t = Text(label, font_size=fs, color=INK, weight="BOLD").move_to(box)
    return VGroup(box, t)


def make_cursor():
    """A little arrow mouse-pointer; its tip is (roughly) the group's UL corner."""
    pts = [(0, 0), (0, -0.36), (0.10, -0.26), (0.17, -0.40),
           (0.22, -0.38), (0.15, -0.24), (0.26, -0.23)]
    cur = Polygon(*[np.array([x, y, 0]) for x, y in pts],
                  color=BG, fill_color=INK, fill_opacity=1, stroke_width=2.5,
                  stroke_color=BG)
    return cur.scale(1.35)


def make_spinner(r=0.22, color=REACT, width=4):
    track = Circle(radius=r, stroke_color=FAINT, stroke_width=width)
    arc = Arc(radius=r, start_angle=PI / 2, angle=-1.45 * PI,
              stroke_color=color, stroke_width=width)
    arc.set_cap_style(CapStyleType.ROUND)
    return VGroup(track, arc), arc


# ========================================================================== #
class _IOBase(Scene):
    def setup(self):
        self.camera.background_color = BG
        self._cap = None
        self.hlrect = None

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

    def section_header(self, part, label, color):
        tag = Text(part, font_size=20, color=color, weight="BOLD")
        tagbox = RoundedRectangle(width=tag.width + 0.4, height=0.44, corner_radius=0.1,
                                  stroke_color=color, stroke_width=2,
                                  fill_color=color, fill_opacity=0.12)
        tag.move_to(tagbox)
        title = Text(label, font_size=34, color=INK, weight="BOLD")
        head = VGroup(VGroup(tagbox, tag), title).arrange(RIGHT, buff=0.3)
        head.to_corner(UL, buff=0.5)
        line = Line(head.get_left(), head.get_right()).next_to(head, DOWN, buff=0.13)
        line.set_stroke(color=color, width=3)
        return VGroup(head, line)

    def say(self, text, color=INK, fs=26, rt=0.5, weight="BOLD"):
        new = Text(text, font_size=fs, color=color, weight=weight).to_edge(DOWN, buff=0.42)
        if new.width > 12.8:
            new.scale_to_fit_width(12.8)
        new.set_z_index(10)  # captions always sit above any panel/mask/device
        if self._cap is None:
            self._cap = new
            self.play(FadeIn(new, shift=UP * 0.12), run_time=rt)
        else:
            # clean cross-dissolve (not a glyph morph, which reads as garbled text)
            self.play(FadeOut(self._cap, shift=UP * 0.12),
                      FadeIn(new, shift=UP * 0.12), run_time=rt)
            self._cap = new
        return new

    def clear_cap(self, rt=0.35):
        if self._cap is not None:
            self.play(FadeOut(self._cap, shift=DOWN * 0.12), run_time=rt)
            self._cap = None

    # ---- bookend cards ---------------------------------------------------- #
    def play_intro(self):
        # a spinning React-ish atom while the title writes in
        core = Dot(radius=0.12, color=REACT)
        rings = VGroup(*[
            Ellipse(width=2.0, height=0.8, stroke_color=REACT, stroke_width=3).rotate(a)
            for a in (0, PI / 3, -PI / 3)])
        atom = VGroup(rings, core).to_edge(UP, buff=1.05)
        self.play(Create(rings, lag_ratio=0.2), GrowFromCenter(core), run_time=1.1)
        self.play(Rotate(rings, angle=TAU, about_point=atom.get_center()),
                  run_time=1.6, rate_func=linear)

        header = Text("IntersectionObserver", font_size=54, color=INK, weight="BOLD")
        header.set(width=min(11.4, header.width))
        sub_in = Text("in React", font_size=34, color=REACT, weight="BOLD")
        sub_in.next_to(header, DOWN, buff=0.28)
        line = Line(
            [header.get_left()[0] - 1, sub_in.get_bottom()[1] - 0.32, 0],
            [header.get_right()[0] + 1, sub_in.get_bottom()[1] - 0.32, 0],
        ).set_stroke(width=3, color=REACT)
        self.play(Write(header), run_time=1.3)
        self.play(FadeIn(sub_in, shift=UP * 0.1), Create(line), run_time=0.8)
        self.card_wait(0.6)
        sub = Text("Watch elements enter the viewport, without the scroll math.",
                   font_size=25, color=MUTED)
        if sub.width > 11.5:
            sub.scale_to_fit_width(11.5)
        sub.next_to(line, DOWN, buff=0.4)
        writer = Text("Created by Ptolémé", font_size=26, color=REACT)
        writer.next_to(sub, DOWN, buff=0.4)
        self.play(FadeIn(sub, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(writer, shift=UP * 0.2), run_time=0.8)
        self.card_wait(1.6)
        self.play(FadeOut(VGroup(header, sub_in, line, sub, writer)), FadeOut(atom),
                  run_time=0.9)
        self.card_wait(0.2)

    def play_outro(self):
        self.card_wait(0.3)
        header = Text("Thanks for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=REACT)
        recap = Text("Stop watching the scroll. Let the browser tell you.",
                     font_size=26, color=MUTED)
        recap.next_to(line, DOWN, buff=0.4)
        writer = Text("Created by Ptolémé", font_size=26, color=REACT)
        writer.next_to(recap, DOWN, buff=0.4)
        self.play(Write(header), Create(line), run_time=1.2)
        self.card_wait(0.5)
        self.play(FadeIn(recap, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(writer, shift=UP * 0.2), run_time=0.8)
        self.card_wait(1.6)
        self.play(FadeOut(VGroup(header, line, recap, writer)), run_time=1.0)
        self.card_wait(0.3)

    # ---- code panel ------------------------------------------------------- #
    def code_panel(self, spec, title="Feed.jsx", fs=CODE_FS, indent_unit=0.40,
                   line_buff=0.15, target_h=6.0, target_w=7.1):
        """spec: list of (indent, text) — text "" means a blank line.

        Returns (panel_group, code_lines). code_lines[i] is the mobject for row i.
        """
        lines = []
        for indent, s in spec:
            if s == "":
                m = Rectangle(width=0.02, height=0.28, fill_opacity=0, stroke_opacity=0)
            elif s.lstrip().startswith("//"):
                m = Text(s, font=MONO, font_size=fs, color=COMMENT, slant=ITALIC)
            else:
                m = Text(s, font=MONO, font_size=fs, color=PLAIN,
                         disable_ligatures=True, t2c=_safe_t2c(s))
            m._indent = indent
            lines.append(m)
        code = VGroup(*lines).arrange(DOWN, aligned_edge=LEFT, buff=line_buff)
        for m in lines:
            m.shift(RIGHT * indent_unit * m._indent)
        f = min(target_h / code.height, target_w / code.width)
        if f < 1:
            code.scale(f)

        CR, HB = 0.16, 0.5
        # body fill (stroke drawn separately on top so nothing can cover the border)
        bg = RoundedRectangle(width=code.width + 0.9, height=code.height + 0.95,
                              corner_radius=CR, stroke_width=0,
                              fill_color="#0A0E15", fill_opacity=1.0)
        bg.move_to(code)
        top_y = bg.get_top()[1]
        cx = bg.get_center()[0]
        # header band spans the FULL panel width and its top corners are rounded to
        # match the container. `header` gives the rounded top; `header_fill` is a
        # square strip that hides the rounded bottom corners (no notch at the divider).
        header = RoundedRectangle(width=bg.width, height=HB, corner_radius=CR,
                                  stroke_width=0, fill_color="#141C29", fill_opacity=1.0)
        header.move_to([cx, top_y - HB / 2, 0])
        header_fill = Rectangle(width=bg.width, height=HB - CR, stroke_width=0,
                                fill_color="#141C29", fill_opacity=1.0)
        header_fill.move_to([cx, top_y - CR - (HB - CR) / 2, 0])
        divider = Line([bg.get_left()[0] + CR, top_y - HB, 0],
                       [bg.get_right()[0] - CR, top_y - HB, 0],
                       stroke_color=FAINT, stroke_width=1.5)
        dots = VGroup(*[Dot(radius=0.045, color=c)
                        for c in ("#FF5F57", "#FEBC2E", "#28C840")]).arrange(RIGHT, buff=0.11)
        dots.move_to([bg.get_left()[0] + 0.42, top_y - HB / 2, 0])
        ttl = Text(title, font=MONO, font_size=15, color=MUTED)
        ttl.next_to(dots, RIGHT, buff=0.35)
        ttl.set_y(top_y - HB / 2)
        code.shift(DOWN * 0.24)
        border = RoundedRectangle(width=bg.width, height=bg.height, corner_radius=CR,
                                  stroke_color=FAINT, stroke_width=2, fill_opacity=0.0)
        border.move_to(bg)
        panel = VGroup(bg, header, header_fill, divider, dots, ttl, code, border)
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

    def unfocus(self, rt=0.3):
        if self.hlrect is not None:
            self.play(FadeOut(self.hlrect), run_time=rt)
            self.hlrect = None

    # ====================================================================== #
    # Scene 1 — The old way: scroll listener + getBoundingClientRect
    # ====================================================================== #
    def scene_problem(self):
        self._cap = None
        head = self.section_header("1", "The old way", REACT)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.6)

        spec = [
            (0, 'window.addEventListener("scroll", () => {'),
            (1, "const r = card.getBoundingClientRect()"),
            (1, "if (r.top < window.innerHeight) {"),
            (2, "// it is visible… maybe. do work."),
            (1, "}"),
            (0, "})"),
        ]
        panel, plines = self.code_panel(spec, title="old-way.js",
                                        target_h=2.6, target_w=6.6)
        panel.to_edge(LEFT, buff=0.7).shift(UP * 1.0)
        self.play(FadeIn(panel, shift=UP * 0.1), run_time=0.7)
        self.beat(1.4)

        # a scrollbar with a thumb the "user" drags, and a runaway event counter
        track = RoundedRectangle(width=0.32, height=3.4, corner_radius=0.16,
                                 stroke_color=FAINT, stroke_width=2,
                                 fill_color="#0A0E15", fill_opacity=1.0)
        track.to_edge(RIGHT, buff=1.0).shift(DOWN * 0.35)
        thumb = RoundedRectangle(width=0.30, height=0.9, corner_radius=0.14,
                                 stroke_width=0, fill_color=MUTED, fill_opacity=0.9)
        thumb.move_to(track.get_top() + DOWN * 0.5)

        cnt_lab = Text("scroll events fired", font_size=19, color=MUTED)
        cnt = Integer(0, font_size=52, color=BAD)
        cntg = VGroup(cnt_lab, cnt).arrange(DOWN, buff=0.16)
        cntg.next_to(track, LEFT, buff=0.8)  # to the LEFT of the scrollbar (stays on-screen)

        note = VGroup(
            Text("Fires on every scroll frame.", font_size=22, color=INK),
            Text("Each call re-measures layout.", font_size=22, color=INK),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        note.next_to(panel, DOWN, buff=0.55).align_to(panel, LEFT)

        self.play(FadeIn(track), FadeIn(thumb), FadeIn(cntg), run_time=0.6)
        self.play(FadeIn(note[0], shift=UP * 0.08), run_time=0.5)
        self.beat(0.8)

        # drag the thumb down while the counter spikes into the hundreds
        n = ValueTracker(0)
        cnt.add_updater(lambda m: m.set_value(int(n.get_value())))
        travel = track.get_top()[1] - track.get_bottom()[1] - 0.9
        self.play(
            thumb.animate.move_to([track.get_center()[0], track.get_top()[1] - 0.5 - travel, 0]),
            n.animate.set_value(348),
            Indicate(plines[0], color=BAD, scale_factor=1.04),
            run_time=2.6, rate_func=linear,
        )
        cnt.clear_updaters()
        self.play(FadeIn(note[1], shift=UP * 0.08),
                  Indicate(plines[1], color=BAD, scale_factor=1.05), run_time=0.7)
        self.beat(1.0)

        # the getBoundingClientRect cost
        cost = Text("getBoundingClientRect() forces a synchronous reflow.",
                    font_size=21, color=BAD)
        cost.next_to(note, DOWN, buff=0.4).align_to(note, LEFT)
        if cost.width > 8.2:
            cost.scale_to_fit_width(8.2)
        self.play(FadeIn(cost, shift=UP * 0.08), run_time=0.6)
        self.beat(1.0)

        punch = Text("You are polling the scroll, by hand, on the main thread.",
                     font_size=26, color=REACT, weight="BOLD").to_edge(DOWN, buff=0.42)
        self.play(Write(punch), run_time=1.1)
        self.play(Circumscribe(punch, color=REACT, run_time=1.1))
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — The idea: hand it to the browser
    # ====================================================================== #
    def scene_idea(self):
        self._cap = None
        head = self.section_header("2", "Hand it to the browser", REACT)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.6)

        # Two aligned columns joined by two perfectly HORIZONTAL arrows.
        box_y = -0.55            # shared vertical center of the callback box & viewport
        BW, BH = 3.5, 1.95
        lx, rx = -4.05, 4.05     # column centers

        # --- left column: "Your component" header + the callback box ---
        cbbox = RoundedRectangle(width=BW, height=BH, corner_radius=0.16,
                                 stroke_color=FN, stroke_width=2,
                                 fill_color=FN, fill_opacity=0.07).move_to([lx, box_y, 0])
        cbinner = VGroup(
            Text("a callback", font_size=22, color=FN, weight="BOLD"),
            Text("+ the elements", font_size=18, color=MUTED),
            Text("to watch", font_size=18, color=MUTED),
        ).arrange(DOWN, buff=0.12).move_to(cbbox)
        cbg = VGroup(cbbox, cbinner)
        you = chip("Your component", STATE_C, fs=22, w=BW, h=0.8)
        you.next_to(cbbox, UP, buff=0.4)

        # --- right column: "The browser" header + a little viewport ---
        view = RoundedRectangle(width=BW, height=BH, corner_radius=0.16, stroke_width=0,
                                fill_color=DEVICE_BG, fill_opacity=1.0).move_to([rx, box_y, 0])
        vborder = RoundedRectangle(width=BW, height=BH, corner_radius=0.16,
                                   stroke_color=MUTED, stroke_width=2,
                                   fill_opacity=0.0).move_to([rx, box_y, 0])
        thr = DashedLine([view.get_left()[0] + 0.18, box_y, 0],
                         [view.get_right()[0] - 0.18, box_y, 0],
                         dash_length=0.1, color=ACCENT).set_stroke(width=2.5)
        # element on the LEFT half, threshold label on the RIGHT — never overlapping
        el = RoundedRectangle(width=1.15, height=0.42, corner_radius=0.1,
                              stroke_color=GOOD, stroke_width=2,
                              fill_color=GOOD, fill_opacity=0.12)
        el.move_to([rx - 0.62, box_y - 0.4, 0])
        thr_lab = Text("threshold", font_size=14, color=ACCENT)
        thr_lab.move_to([rx + 0.8, box_y + 0.3, 0])
        viewg = VGroup(view, thr, el, thr_lab, vborder)
        brow = chip("The browser", REACT, fs=22, w=BW, h=0.8)
        brow.next_to(view, UP, buff=0.4)

        self.play(FadeIn(you, shift=DOWN * 0.1), FadeIn(cbg, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(brow, shift=DOWN * 0.1), FadeIn(viewg, shift=UP * 0.1), run_time=0.7)
        self.beat(0.8)

        gap_mid = (cbbox.get_right()[0] + view.get_left()[0]) / 2
        avail = (view.get_left()[0] - cbbox.get_right()[0]) - 0.3

        # --- horizontal arrow 1: observe(targets)  (component → browser) ---
        y1 = box_y + 0.5
        a1 = arr([cbbox.get_right()[0], y1, 0], [view.get_left()[0], y1, 0], color=FN, sw=4)
        a1_lab = Text("observe(targets)", font=MONO, font_size=17, color=FN)
        a1_lab.move_to([gap_mid, y1 + 0.3, 0])
        self.play(FadeIn(a1_lab, shift=UP * 0.05), GrowArrow(a1), run_time=0.7)
        self.beat(0.7)

        # the element crosses the threshold line; the browser notices
        self.play(el.animate.move_to([rx - 0.62, box_y + 0.34, 0]), run_time=0.9)
        self.play(el.animate.set_fill(GOOD, 0.32),
                  Flash(el, color=GOOD, flash_radius=0.7), run_time=0.5)
        self.beat(0.4)

        # --- horizontal arrow 2: callback(entries)  (browser → component) ---
        y2 = box_y - 0.5
        a2 = arr([view.get_left()[0], y2, 0], [cbbox.get_right()[0], y2, 0], color=GOOD, sw=4)
        a2_lab = Text('callback(entries): "it is visible now"', font_size=17, color=GOOD)
        if a2_lab.width > avail:
            a2_lab.scale_to_fit_width(avail)
        a2_lab.move_to([gap_mid, y2 - 0.3, 0])
        self.play(GrowArrow(a2), FadeIn(a2_lab, shift=DOWN * 0.05), run_time=0.7)
        self.beat(1.0)

        # --- the three knobs ---
        knobs = VGroup(
            Text("root: the scrolling box (the viewport)", font_size=20, color=INK,
                 t2c={"root": VAL}),
            Text("rootMargin: grow or shrink that box", font_size=20, color=INK,
                 t2c={"rootMargin": VAL}),
            Text("threshold: how much must show, from 0 to 1", font_size=20, color=INK,
                 t2c={"threshold": VAL}),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        knobs.to_edge(DOWN, buff=0.7)
        kbox = SurroundingRectangle(knobs, color=VAL, buff=0.26, corner_radius=0.12).set_stroke(width=2)
        self.play(FadeIn(knobs, shift=UP * 0.1), Create(kbox), run_time=0.8)
        self.beat(1.4)

        punch = Text("You describe when an element counts. The browser watches, off the main thread.",
                     font_size=23, color=REACT, weight="BOLD").to_edge(DOWN, buff=0.4)
        if punch.width > 12.8:
            punch.scale_to_fit_width(12.8)
        self.play(FadeOut(VGroup(knobs, kbox)), run_time=0.3)
        self.play(Write(punch), run_time=1.1)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — The API
    # ====================================================================== #
    def scene_api(self):
        self._cap = None
        head = self.section_header("3", "The observer API", REACT)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.6)

        spec = [
            (0, "const io = new IntersectionObserver("),
            (1, "(entries) => {"),
            (2, "entries.forEach((entry) => {"),
            (3, "if (entry.isIntersecting) {"),
            (4, "// entry.target just crossed"),
            (3, "}"),
            (2, "})"),
            (1, "},"),
            (1, "{ threshold: 0.6 }"),
            (0, ")"),
            (0, ""),
            (0, "io.observe(target)      // start watching one"),
            (0, "io.unobserve(target)    // stop watching one"),
            (0, "io.disconnect()         // stop watching all"),
        ]
        panel, plines = self.code_panel(spec, title="observer.js",
                                        target_h=4.6, target_w=8.4)
        panel.move_to(ORIGIN).shift(DOWN * 0.2)
        self.play(FadeIn(panel, shift=UP * 0.1), run_time=0.8)
        self.beat(1.0)

        # the callback
        self.focus(panel, plines, [1, 2, 3, 4, 5, 6, 7], color=FN)
        self.say("The callback runs only when a target crosses your threshold.",
                 color=FN)
        self.beat(1.2)

        self.focus(panel, plines, [2], color=STATE_C)
        self.say("entries is the list of targets that just changed.", color=STATE_C)
        self.beat(1.0)

        self.focus(panel, plines, [3], color=GOOD)
        self.say("entry.isIntersecting is true when it is on screen.", color=GOOD)
        self.beat(1.2)

        self.focus(panel, plines, [11, 12, 13], color=VAL)
        self.say("You observe elements, and disconnect to stop.", color=VAL)
        self.beat(1.2)

        self.unfocus()
        punch = Text("Give it a callback and options. Then observe what you care about.",
                     font_size=25, color=REACT, weight="BOLD").to_edge(DOWN, buff=0.42)
        self.play(ReplacementTransform(self._cap, punch), run_time=0.6)
        self._cap = punch
        self.play(Circumscribe(punch, color=REACT, run_time=1.1))
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 ★ — Count as you scroll (the strict scrolling example + count)
    # ====================================================================== #
    # geometry constants
    CARD_W = 3.55
    CARD_H = 0.82

    def make_item(self, i):
        box = RoundedRectangle(width=self.CARD_W, height=self.CARD_H, corner_radius=0.14,
                               stroke_color=FAINT, stroke_width=2.0,
                               fill_color="#0F1725", fill_opacity=1.0)
        dot = Circle(radius=0.15, fill_color=MUTED, fill_opacity=1.0, stroke_width=0)
        dot.move_to(box.get_left() + RIGHT * 0.42)
        label = Text(f"Item {i:02d}", font_size=18, color=INK)
        label.next_to(dot, RIGHT, buff=0.26)
        check = make_tick(color=GOOD, scale=0.85)
        check.move_to(box.get_right() + LEFT * 0.38)
        check.set_opacity(0)
        row = VGroup(box, dot, label, check)
        row.box, row.dot, row.label, row.check = box, dot, label, check
        row.is_item = True
        for m in row:
            m.set_z_index(2)
        row.set_z_index(2)
        return row

    def make_sentinel(self):
        box = RoundedRectangle(width=self.CARD_W, height=self.CARD_H, corner_radius=0.14,
                               stroke_color=REACT, stroke_width=2.0,
                               fill_color="#0E1B26", fill_opacity=1.0)
        spin, arc = make_spinner(r=0.15, color=REACT, width=3.5)
        spin.move_to(box.get_left() + RIGHT * 0.42)
        label = Text("loading more…", font_size=17, color=REACT)
        label.next_to(spin, RIGHT, buff=0.26)
        row = VGroup(box, spin, label)
        row.is_item = False
        for m in row:
            m.set_z_index(2)
        row.set_z_index(2)
        return row

    def style_item(self, it, seen):
        if seen:
            it.box.set_stroke(GOOD, width=2.2)
            it.box.set_fill(GOOD, 0.15)
            it.dot.set_fill(GOOD, 1.0)
            it.label.set_color(GOOD)
            it.check.set_opacity(1.0)
        else:
            it.box.set_stroke(FAINT, width=2.0)
            it.box.set_fill("#0F1725", 1.0)
            it.dot.set_fill(MUTED, 1.0)
            it.label.set_color(INK)
            it.check.set_opacity(0.0)

    def _drive(self, m):
        """One updater to rule the viewport: reposition every row by
        ``home_y + scroll``, recolor items whose center has crossed the line,
        and set the live counter to that (monotone, provably correct) tally."""
        s = self.scroll.get_value()
        for row in self.all_rows:
            row.move_to([self.col_x, row.home_y + s, 0])
        n = 0
        for it in self.items:
            seen = it.get_center()[1] >= self.line_y - 1e-3
            self.style_item(it, seen)
            if seen:
                n += 1
        if n != self._seen_shown:
            self._seen_shown = n
            new = Text(str(n), font_size=34, color=GOOD, weight="BOLD")
            new.move_to(self.seen_anchor)
            new.set_z_index(9)
            self.seen_num.become(new)
            self.seen_num.set_z_index(9)

    def scroll_to(self, s, rt=1.0, rate=smooth):
        self.play(self.scroll.animate.set_value(s), run_time=rt, rate_func=rate)

    def load_more(self):
        """The sentinel scrolled into view → append four more items below it and
        push the sentinel to the new bottom. The same observer keeps counting."""
        self.play(Indicate(self.sentinel, color=REACT, scale_factor=1.05), run_time=0.5)
        slot = self.sentinel.home_y
        start = len(self.items)
        s_now = self.scroll.get_value()
        for k in range(4):
            it = self.make_item(start + 1 + k)
            it.home_y = slot - k * self.pitch
            it.move_to([self.col_x, it.home_y + s_now, 0])
            self.items.append(it)
            self.all_rows.append(it)
            self.content.add(it)
        self.sentinel.home_y = slot - 4 * self.pitch

    def scene_count(self):
        self._cap = None
        self.hlrect = None
        self._seen_shown = 0
        head = self.section_header("4", "Count as you scroll", REACT)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.6)

        # ---- code panel (left) : the real React hook ----
        spec = [
            (0, "function Feed() {"),
            (0, ""),
            (1, "const [seen, setSeen] = useState(0)"),
            (0, ""),
            (1, "useEffect(() => {"),
            (2, "const io = new IntersectionObserver("),
            (3, "(entries) => {"),
            (4, "entries.forEach((e) => {"),
            (5, "if (e.isIntersecting) {"),
            (6, "setSeen((n) => n + 1)"),
            (6, "io.unobserve(e.target)"),
            (5, "}"),
            (4, "})"),
            (3, "},"),
            (3, "{ threshold: 0.6 }"),
            (2, ")"),
            (2, "cards().forEach((c) => io.observe(c))"),
            (2, "return () => io.disconnect()"),
            (1, "}, [])"),
            (0, ""),
            (1, "return <List />"),
            (0, "}"),
        ]
        panel, plines = self.code_panel(spec, title="Feed.jsx",
                                        indent_unit=0.30, line_buff=0.12,
                                        target_h=5.0, target_w=6.3)
        panel.to_edge(LEFT, buff=0.45).shift(DOWN * 0.3)

        # ---- viewport (right) ----
        devx = 4.5
        fw, fh = 4.3, 5.5
        cy = -0.2
        CRv = 0.26
        fill = RoundedRectangle(width=fw, height=fh, corner_radius=CRv, stroke_width=0,
                                fill_color=DEVICE_BG, fill_opacity=1.0).move_to([devx, cy, 0])
        top_y = fill.get_top()[1]
        bot_y = fill.get_bottom()[1]
        HB = 0.54
        # full-width header band: top corners rounded to embrace the container, a
        # square strip hides the rounded bottom corners, border drawn last on top
        header = RoundedRectangle(width=fw, height=HB, corner_radius=CRv, stroke_width=0,
                                  fill_color="#1A2231", fill_opacity=1.0)
        header.move_to([devx, top_y - HB / 2, 0]).set_z_index(6)
        header_fill = Rectangle(width=fw, height=HB - CRv, stroke_width=0,
                                fill_color="#1A2231", fill_opacity=1.0)
        header_fill.move_to([devx, top_y - CRv - (HB - CRv) / 2, 0]).set_z_index(6)
        border = RoundedRectangle(width=fw, height=fh, corner_radius=CRv,
                                  stroke_color=MUTED, stroke_width=2.2,
                                  fill_opacity=0.0).move_to([devx, cy, 0]).set_z_index(6)
        dots = VGroup(*[Dot(radius=0.05, color=c)
                        for c in ("#FF5F57", "#FEBC2E", "#28C840")]).arrange(RIGHT, buff=0.12)
        dots.move_to([fill.get_left()[0] + 0.42, top_y - HB / 2, 0]).set_z_index(7)
        ttl = Text("localhost:3000", font=MONO, font_size=13, color=MUTED)
        ttl.next_to(dots, RIGHT, buff=0.3).set_y(top_y - HB / 2).set_z_index(7)

        interior_top = top_y - HB
        interior_bottom = bot_y
        self.col_x = devx
        self.line_y = cy + 0.5
        self.pitch = self.CARD_H + 0.30

        # "items seen" counter is its OWN readout ABOVE the viewport, so no card
        # ever scrolls behind it (kept above the masks with a high z-index)
        cbar = RoundedRectangle(width=fw, height=0.66, corner_radius=0.14,
                                stroke_color=FAINT, stroke_width=1.5,
                                fill_color="#0F1926", fill_opacity=1.0)
        cbar.move_to([devx, top_y + 0.56, 0]).set_z_index(8)
        seen_lab = Text("items seen", font_size=16, color=MUTED)
        seen_lab.move_to(cbar.get_left() + RIGHT * 1.0).set_z_index(9)
        self.seen_anchor = cbar.get_right() + LEFT * 0.62
        self.seen_num = Text("0", font_size=34, color=GOOD, weight="BOLD")
        self.seen_num.move_to(self.seen_anchor).set_z_index(9)
        counter = VGroup(cbar, seen_lab, self.seen_num)

        # the threshold line
        thr = DashedLine([fill.get_left()[0] + 0.14, self.line_y, 0],
                         [fill.get_right()[0] - 0.14, self.line_y, 0],
                         dash_length=0.13, color=ACCENT).set_stroke(width=2.5)
        thr.set_z_index(7)
        # threshold label sits in the gap to the LEFT of the viewport, clear of the
        # card column, so a crossing card's checkmark never collides with it
        thr_lbl = Text("threshold 0.6", font_size=14, color=ACCENT)
        line_left = np.array([fill.get_left()[0], self.line_y, 0])
        thr_lbl.next_to(line_left, LEFT, buff=0.26)
        min_cx = panel.get_right()[0] + 0.2 + thr_lbl.width / 2
        if thr_lbl.get_center()[0] < min_cx:
            thr_lbl.move_to([min_cx, self.line_y, 0])
        thr_tick = Line(thr_lbl.get_right() + RIGHT * 0.06, line_left,
                        color=ACCENT, stroke_width=2)
        thr_tag = VGroup(thr_lbl, thr_tick)
        thr_tag.set_z_index(9)

        # overflow masks (scene-BG coloured → invisible over the background, they
        # only hide the card stack above/below the viewport)
        mask_w = fw - 0.5
        top_mask = Rectangle(width=mask_w, height=6.0, stroke_width=0,
                             fill_color=BG, fill_opacity=1.0)
        top_mask.move_to([devx, interior_top + 3.0, 0]).set_z_index(5)
        bot_mask = Rectangle(width=mask_w, height=6.0, stroke_width=0,
                             fill_color=BG, fill_opacity=1.0)
        bot_mask.move_to([devx, interior_bottom - 3.0, 0]).set_z_index(5)

        self.play(FadeIn(panel, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(fill), FadeIn(header), FadeIn(header_fill), FadeIn(border),
                  FadeIn(dots), FadeIn(ttl), FadeIn(counter), run_time=0.7)
        # (masks are invisible over the BG; add them without a fade)
        self.add(top_mask, bot_mask)

        # ---- build the list ----
        self.scroll = ValueTracker(0.0)
        self.items = []
        self.all_rows = []
        home0 = self.line_y - 0.7
        for i in range(1, 8):                       # items 01..07
            it = self.make_item(i)
            it.home_y = home0 - (i - 1) * self.pitch
            it.move_to([self.col_x, it.home_y, 0])
            self.items.append(it)
            self.all_rows.append(it)
        self.sentinel = self.make_sentinel()
        self.sentinel.home_y = home0 - 7 * self.pitch
        self.sentinel.move_to([self.col_x, self.sentinel.home_y, 0])
        self.all_rows.append(self.sentinel)

        self.content = VGroup(*self.all_rows)
        self.add(self.content)
        for it in self.items:
            self.style_item(it, False)
        self.play(FadeIn(self.content, lag_ratio=0.05), run_time=0.6)
        self.play(Create(thr), FadeIn(thr_tag), run_time=0.6)
        self.content.add_updater(self._drive)
        self.beat(0.6)

        # ---- narrate the setup ----
        self.focus(panel, plines, [4, 5, 15, 16], color=EFFECT_C)
        self.say("Inside useEffect we make one observer and watch every card.",
                 color=EFFECT_C)
        self.beat(1.3)
        self.focus(panel, plines, [8, 9], color=GOOD)
        self.say("When a card crosses the line, isIntersecting fires and seen goes up.",
                 color=GOOD)
        self.beat(1.2)

        # ---- step through the first three, in lock-step with the code ----
        for i in (1, 2, 3):
            s_i = self.line_y - (home0 - (i - 1) * self.pitch)
            self.scroll_to(s_i + 0.32 * self.pitch, rt=0.95 if i == 1 else 0.8)
            self.play(Indicate(self.seen_num, color=GOOD, scale_factor=1.25), run_time=0.4)
            self.beat(0.5 if i < 3 else 0.7)

        self.focus(panel, plines, [10], color=FN)
        self.say("Then unobserve that card, so it never counts twice.", color=FN)
        self.beat(1.2)

        # ---- the flurry: keep scrolling, the count races 3 → 7 ----
        self.focus(panel, plines, [8, 9, 10], color=GOOD)
        self.say("Keep scrolling. The browser reports each one as it enters.", color=REACT)
        s_7 = self.line_y - (home0 - 6 * self.pitch)
        self.scroll_to(s_7 + 0.32 * self.pitch, rt=2.7, rate=linear)
        self.beat(0.8)

        # ---- the sentinel → load more (infinite scroll) ----
        self.unfocus(0.3)
        self.say("At the bottom sits a sentinel row that we also observe.", color=REACT)
        # scroll a touch so the sentinel is clearly in view near the line
        s_sent_view = self.line_y - self.sentinel.home_y - 0.9 * self.pitch
        self.scroll_to(max(self.scroll.get_value(), s_sent_view),
                       rt=0.9, rate=linear)
        self.beat(0.8)
        self.say("It scrolls into view, so we load more items below it.", color=REACT)
        self.load_more()
        self.say("The same observer just keeps counting the new cards.", color=GOOD)
        s_last = self.line_y - (home0 - 10 * self.pitch)
        self.scroll_to(s_last + 0.28 * self.pitch, rt=2.6, rate=linear)
        self.play(Indicate(self.seen_num, color=GOOD, scale_factor=1.25),
                  Flash(self.seen_num, color=GOOD, flash_radius=0.7), run_time=0.6)
        self.beat(1.0)

        # ---- the punch ----
        self.unfocus(0.3)
        self.clear_cap(0.3)
        punch = Text("No scroll handler. No layout math. The browser told us exactly when.",
                     font_size=24, color=REACT, weight="BOLD").to_edge(DOWN, buff=0.4)
        if punch.width > 12.8:
            punch.scale_to_fit_width(12.8)
        punch.set_z_index(10)
        self.play(Write(punch), run_time=1.1)
        self.play(Circumscribe(punch, color=REACT, run_time=1.2))
        self.settle()
        self.content.clear_updaters()
        # fade the list out while the masks still cover the off-screen stack, so
        # the wipe never briefly reveals cards sitting above/below the viewport
        self.play(FadeOut(self.content), run_time=0.4)
        self.remove(self.content)
        self.wipe()

    # ====================================================================== #
    # Scene 5 — Recap
    # ====================================================================== #
    def scene_recap(self):
        self._cap = None
        head = self.section_header("RECAP", "The mental model", ACCENT)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.6)

        points = [
            ("You give the browser targets and a callback. It watches for you.", REACT),
            ("The callback fires only when an element crosses your threshold, "
             "asynchronously, off the main thread.", GOOD),
            ("In React: set it up in useEffect, observe your nodes, and "
             "disconnect on cleanup.", EFFECT_C),
        ]
        rows = VGroup()
        for txt, c in points:
            tick = make_tick(color=c, scale=0.95)
            t = Text(txt, font_size=24, color=INK)
            t.scale_to_fit_width(min(t.width, 10.6))
            rows.add(VGroup(tick, t).arrange(RIGHT, buff=0.28))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.6).move_to(UP * 0.35)
        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.2), run_time=0.7)
            self.beat(0.9)

        hook = Text("Stop watching the scroll. Let the browser tell you.",
                    font_size=28, color=ACCENT, weight="BOLD").to_edge(DOWN, buff=0.6)
        self.play(Write(hook), run_time=1.3)
        self.play(Circumscribe(hook, color=ACCENT, run_time=1.3))
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_problem()
        self.scene_idea()
        self.scene_api()
        self.scene_count()
        self.scene_recap()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_IOBase):
    def construct(self):
        self.play_intro()


class Problem(_IOBase):
    def construct(self):
        self.scene_problem()


class Idea(_IOBase):
    def construct(self):
        self.scene_idea()


class Api(_IOBase):
    def construct(self):
        self.scene_api()


class Count(_IOBase):
    def construct(self):
        self.scene_count()


class Recap(_IOBase):
    def construct(self):
        self.scene_recap()


class Outro(_IOBase):
    def construct(self):
        self.play_outro()


class IntersectionObserverReact(_IOBase):
    """The whole ~3-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    IntersectionObserverReact().render()

"""React Hooks & useEffect — a dynamic ~3-minute explainer, house-style.

A function component is *just a function that returns UI*. On its own a function
forgets everything the moment it returns. **Hooks** are the special functions
(their names start with ``use``) that let a component remember things and react
to change. This film builds the two you reach for every day:

    1. What is a hook?   -- a component is a function; hooks give it memory + lifecycle
    2. useState          -- change state → React re-renders (a live counter)
    3. Why useEffect?    -- rendering is pure; talking to the outside world is a side effect
    4. Anatomy           -- useEffect(fn, [deps]) + cleanup; what the dependency array means
    5. The example ★     -- a real "click a button → it loads → the UI updates" component,
                            code on the left, a live mock app on the right, kept in sync
    6. The render cycle  -- state → re-render → paint → effect (if deps changed) → …
    7. Recap             -- the mental model in three lines

The star (scene 5) is exactly the use-case asked for: click a button, a spinner
shows while it "loads", then the component updates with the new data — because the
clicked value is in the effect's dependency array, so the effect re-runs.

Everything uses ``Text`` (Pango), never ``Tex`` — renders with no LaTeX toolchain.
Code is set in Menlo. Nothing is faked with images: the app, the spinner, the
profile cards and the cursor are all drawn Manim mobjects.

Scenes are exposed individually (``Hooks``, ``State``, ``SideEffects``,
``Anatomy``, ``Example``, ``Cycle``, ``Recap``, ``Intro``, ``Outro``) and as one
film (``ReactHooks``).

Env knobs:
    RX_QUICK=1     collapse every reading hold (and the end-holds) for a fast render
    RX_DELAY=1.2   override the reading-hold multiplier (seconds per "beat")
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


QUICK = os.environ.get("RX_QUICK") == "1"
# Single pacing knob: every reading "hold" is self.beat(t) == wait(t * DELAY).
# Animation run-times are NOT scaled, so the piece stays dynamic — DELAY only
# sets how long text lingers. Each scene ends on a short hold (self.settle).
DELAY = float(os.environ.get("RX_DELAY", "0.28" if QUICK else "2.3"))
END_HOLD = 0.2 if QUICK else 2.5

# ---- palette -------------------------------------------------------------- #
BG = "#0E1117"        # dark slate background
INK = "#F5F3EF"       # warm white text
MUTED = "#8A93A6"     # secondary text / axes
FAINT = "#2A3140"     # gridlines / tracks
ACCENT = "#FFD166"    # highlight (gold)
GOOD = "#3DD68C"      # good / pass (green)
BAD = "#FF5C5C"       # bad / error (red)
REACT = "#61DAFB"     # React cyan — brand accent
STATE_C = "#C792EA"   # state (purple)
EFFECT_C = "#FFCB6B"  # effects (gold)

# ---- code (Night-Owl-ish) palette ----------------------------------------- #
MONO = "Menlo"
CODE_FS = 19
PLAIN = "#D6DEEB"     # default code text
COMMENT = "#5F6B7E"   # comments (grey-blue)
HOOK = "#FFCB6B"      # the hooks themselves — the stars (gold)
KW = "#C792EA"        # keywords: function / const / return (purple)
FN = "#82AAFF"        # calls / handlers (blue)
VAL = "#F78C6C"       # literals: null / true / false (orange)
JSX = "#7FDBCA"       # jsx element names (teal)
DEVICE_BG = "#121A26"  # mock-app body

# distinctive, non-overlapping keys → safe substring colouring for every code line
CODE_T2C = {
    "function": KW, "const": KW, "return": KW,
    "useState": HOOK, "useEffect": HOOK,
    "null": VAL, "true": VAL, "false": VAL,
    "fetchUser": FN, "setUserId": FN, "setUser": FN, "setLoading": FN,
    "onNext": FN, "onClick": FN, "setCount": FN,
    "Spinner": JSX, "Profile": JSX, "button": JSX,
}


def _safe_t2c(s):
    """Per-line text→colour map, pruned so no key overlaps another.

    Manim's ``t2c`` raises on overlapping colour ranges — even when the colour is
    identical (e.g. ``setUser`` sitting inside ``setUserId``). Keep only the keys
    present in this line, and drop any key that is a substring of another present
    key so their ranges can never collide.
    """
    present = {k: v for k, v in CODE_T2C.items() if k in s}
    keys = list(present)
    return {k: v for k, v in present.items()
            if not any(k != o and k in o for o in keys)}


# ========================================================================== #
# small reusable pieces
# ========================================================================== #
def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])])
    return v.set_stroke(color=color, width=sw).scale(scale)


def chip(text, color, fs=22, fill=0.14, w=None, h=0.6, tcolor=None, font=None):
    label = Text(text, font_size=fs, color=tcolor or INK, font=font) if font \
        else Text(text, font_size=fs, color=tcolor or INK)
    width = (label.width + 0.5) if w is None else w
    box = RoundedRectangle(width=width, height=h, corner_radius=0.12,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=fill)
    label.move_to(box)
    return VGroup(box, label)


def code_line_1(s, fs=30, t2c=None):
    """One code line as a *single* ``Text`` — correct kerning, commas on the
    baseline, natural monospace spacing. Colour via ``t2c`` (falls back to the
    house map). Ligatures are disabled so one glyph == one character, which lets
    ``glyph_slice`` anchor braces by raw string index.
    """
    return Text(s, font=MONO, font_size=fs, color=PLAIN,
                disable_ligatures=True, t2c=(t2c if t2c is not None else _safe_t2c(s)))


def glyph_slice(mob, full, token, occ=0):
    """Return the sub-mobjects of ``mob`` covering ``token`` in ``full`` (Manim
    makes one submobject per character, spaces included → index directly)."""
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


def make_spinner(r=0.5, color=REACT, width=6):
    track = Circle(radius=r, stroke_color=FAINT, stroke_width=width)
    arc = Arc(radius=r, start_angle=PI / 2, angle=-1.45 * PI,
              stroke_color=color, stroke_width=width)
    arc.set_cap_style(CapStyleType.ROUND)
    return VGroup(track, arc), arc


def initials_of(name):
    parts = [p for p in name.split() if p]
    return "".join(p[0] for p in parts[:2]).upper()


def make_profile(user):
    """A little user card: avatar w/ initials, name, role, id-chip."""
    idx, name, role, col = user
    avatar = Circle(radius=0.6, stroke_width=0, fill_color=col, fill_opacity=0.95)
    ini = Text(initials_of(name), font_size=30, color=BG, weight="BOLD").move_to(avatar)
    nm = Text(name, font_size=25, color=INK, weight="BOLD")
    rl = Text(role, font_size=17, color=MUTED)
    idc = chip(f"user id: {idx}", col, fs=15, h=0.4)
    return VGroup(VGroup(avatar, ini), nm, rl, idc).arrange(DOWN, buff=0.2)


# the three users the example cycles through (fun, recognisable)
USERS = [
    ("1", "Ada Lovelace", "First programmer · 1843", "#F78C6C"),
    ("2", "Alan Turing", "Father of computer science", "#82AAFF"),
    ("3", "Grace Hopper", "Compiler pioneer · COBOL", GOOD),
]


# ========================================================================== #
class _RXBase(Scene):
    def setup(self):
        self.camera.background_color = BG
        self._cap = None
        self.hlrect = None
        self.dev_content = None

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
        self.dev_content = None

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
        if self._cap is None:
            self._cap = new
            self.play(FadeIn(new, shift=UP * 0.12), run_time=rt)
        else:
            self.play(ReplacementTransform(self._cap, new), run_time=rt)
            self._cap = new
        return new

    # ---- bookend cards ---------------------------------------------------- #
    def _bookend_title(self, title, subtitle=None):
        header = Text(title, font_size=52, color=INK, weight="BOLD")
        header.set(width=min(11.2, header.width))
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=REACT)
        writer = Text("Created by Ptolémé", font_size=28, color=REACT)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.4)
        self.card_wait(0.6)
        if subtitle:
            sub = Text(subtitle, font_size=32, color=MUTED)
            sub.move_to(header)
            self.play(Transform(header, sub), run_time=0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        return VGroup(header, writer, line)

    def play_intro(self):
        # a spinning React-ish atom while the title writes in
        core = Dot(radius=0.12, color=REACT)
        rings = VGroup(*[
            Ellipse(width=2.0, height=0.8, stroke_color=REACT, stroke_width=3).rotate(a)
            for a in (0, PI / 3, -PI / 3)])
        atom = VGroup(rings, core).to_edge(UP, buff=1.1)
        self.play(Create(rings, lag_ratio=0.2), GrowFromCenter(core), run_time=1.1)
        self.play(Rotate(rings, angle=TAU, about_point=atom.get_center()),
                  run_time=1.6, rate_func=linear)
        grp = self._bookend_title("React Hooks & useEffect",
                                  "Give your components memory — and let them react")
        self.card_wait(1.6)
        self.play(FadeOut(grp), FadeOut(atom), run_time=0.9)
        self.card_wait(0.2)

    def play_outro(self):
        self.card_wait(0.3)
        header = Text("Thanks for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=REACT)
        writer = Text("Created by Ptolémé", font_size=28, color=REACT)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.2)
        self.card_wait(0.6)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.card_wait(1.6)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.0)
        self.card_wait(0.3)

    # ---- code panel ------------------------------------------------------- #
    def code_panel(self, spec, title="Component.jsx", fs=CODE_FS, indent_unit=0.44,
                   line_buff=0.155, target_h=6.0, target_w=7.1):
        """spec: list of (indent, text) — text "" means a blank line.

        Returns (panel_group, code_lines). code_lines[i] is the mobject for row i.
        """
        lines = []
        for indent, s in spec:
            if s == "":
                m = Rectangle(width=0.02, height=0.30, fill_opacity=0, stroke_opacity=0)
            elif s.lstrip().startswith("//"):
                m = Text(s, font=MONO, font_size=fs, color=COMMENT, slant=ITALIC)
            else:
                m = Text(s, font=MONO, font_size=fs, color=PLAIN, t2c=_safe_t2c(s))
            m._indent = indent
            lines.append(m)
        code = VGroup(*lines).arrange(DOWN, aligned_edge=LEFT, buff=line_buff)
        for m in lines:
            m.shift(RIGHT * indent_unit * m._indent)
        f = min(target_h / code.height, target_w / code.width)
        if f < 1:
            code.scale(f)

        CR, HB = 0.16, 0.5
        bg = RoundedRectangle(width=code.width + 0.9, height=code.height + 0.95,
                              corner_radius=CR, stroke_color=FAINT, stroke_width=2,
                              fill_color="#0A0E15", fill_opacity=1.0)
        bg.move_to(code)
        # header band: a flat strip inset within the rounded top corners so it sits
        # flush (no floating-pill seam), with a hairline divider beneath it
        top_y = bg.get_top()[1]
        header = Rectangle(width=bg.width - 2 * CR, height=HB, stroke_width=0,
                           fill_color="#141C29", fill_opacity=1.0)
        header.move_to([bg.get_center()[0], top_y - HB / 2, 0])
        divider = Line([bg.get_left()[0] + CR, top_y - HB, 0],
                       [bg.get_right()[0] - CR, top_y - HB, 0],
                       stroke_color=FAINT, stroke_width=1.5)
        dots = VGroup(*[Dot(radius=0.045, color=c)
                        for c in ("#FF5F57", "#FEBC2E", "#28C840")]).arrange(RIGHT, buff=0.11)
        dots.move_to([bg.get_left()[0] + 0.42, top_y - HB / 2, 0])
        ttl = Text(title, font=MONO, font_size=15, color=MUTED)
        ttl.move_to([bg.get_center()[0], top_y - HB / 2, 0])
        code.shift(DOWN * 0.24)  # nudge below the header band
        panel = VGroup(bg, header, divider, dots, ttl, code)
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

    # ---- mock app device -------------------------------------------------- #
    def make_device(self, center=(3.75, -0.2, 0), title="localhost:3000"):
        CR, HB = 0.30, 0.58
        frame = RoundedRectangle(width=4.5, height=5.3, corner_radius=CR,
                                 stroke_color=MUTED, stroke_width=2.2,
                                 fill_color=DEVICE_BG, fill_opacity=1.0)
        top_y = frame.get_top()[1]
        header = Rectangle(width=frame.width - 2 * CR, height=HB, stroke_width=0,
                           fill_color="#1A2231", fill_opacity=1.0)
        header.move_to([frame.get_center()[0], top_y - HB / 2, 0])
        divider = Line([frame.get_left()[0] + CR, top_y - HB, 0],
                       [frame.get_right()[0] - CR, top_y - HB, 0],
                       stroke_color=MUTED, stroke_width=1.2).set_opacity(0.45)
        dots = VGroup(*[Dot(radius=0.05, color=c)
                        for c in ("#FF5F57", "#FEBC2E", "#28C840")]).arrange(RIGHT, buff=0.12)
        dots.move_to([frame.get_left()[0] + 0.5, top_y - HB / 2, 0])
        ttl = Text(title, font=MONO, font_size=15, color=MUTED)
        ttl.move_to([frame.get_center()[0], top_y - HB / 2, 0])
        device = VGroup(frame, header, divider, dots, ttl)
        device.move_to(np.array(center))

        button = make_button("Next user")
        button.move_to([frame.get_center()[0], header.get_bottom()[1] - 0.55, 0])
        self.dev_frame = frame
        self.dev_button = button
        self.content_center = frame.get_center() + DOWN * 0.55
        return VGroup(device, button)

    def swap_content(self, new_mob, rt=0.45, shift=UP * 0.15):
        # sequential (out, then in) so old and new content never overlap
        new_mob.move_to(self.content_center)
        if self.dev_content is not None:
            self.play(FadeOut(self.dev_content, shift=UP * 0.12), run_time=rt * 0.55)
        self.play(FadeIn(new_mob, shift=shift), run_time=rt * 0.7)
        self.dev_content = new_mob

    def show_loading(self, n, rt=1.4):
        spin, arc = make_spinner()
        lbl = Text(f"loading user {n}…", font_size=17, color=MUTED)
        grp = VGroup(spin, lbl).arrange(DOWN, buff=0.34)
        self.swap_content(grp, rt=0.4)
        self.play(Rotate(arc, angle=-TAU * max(1, round(rt / 0.5)),
                         about_point=arc.get_center()),
                  run_time=rt, rate_func=linear)

    def click(self, button, cursor, rt=0.55):
        self.play(cursor.animate.move_to(
            button.get_center() + RIGHT * 0.42 + DOWN * 0.24), run_time=rt)
        ripple = Circle(radius=0.12, color=REACT, stroke_width=3,
                        fill_opacity=0).move_to(button.get_center())
        self.add(ripple)
        self.play(button.animate.scale(0.94), run_time=0.12)
        self.play(button.animate.scale(1 / 0.94),
                  ripple.animate.scale(7).set_stroke(opacity=0), run_time=0.42)
        self.remove(ripple)

    # ====================================================================== #
    # Scene 1 — What is a hook?
    # ====================================================================== #
    def scene_hooks(self):
        self._cap = None
        head = self.section_header("1", "What is a hook?", REACT)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.6)

        # a component is just a function that returns UI
        spec = [
            (0, "function Greeting() {"),
            (1, "return <h1>Hello!</h1>"),
            (0, "}"),
        ]
        panel, _ = self.code_panel(spec, title="Greeting.jsx", target_h=2.1, target_w=5.3)
        panel.to_edge(LEFT, buff=0.9).shift(UP * 1.35)
        self.play(FadeIn(panel, shift=UP * 0.1), run_time=0.7)
        note = Text("A component is just a function that returns UI.",
                    font_size=25, color=INK).next_to(panel, DOWN, buff=0.4).to_edge(LEFT, buff=0.9)
        self.play(FadeIn(note, shift=UP * 0.1), run_time=0.5)
        self.beat(1.0)

        # the problem
        prob = VGroup(
            Text("But a plain function forgets everything", font_size=24, color=MUTED),
            Text("the moment it returns.", font_size=24, color=MUTED),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        prob.next_to(note, DOWN, buff=0.45).to_edge(LEFT, buff=0.9)
        for p in prob:
            self.play(FadeIn(p, shift=UP * 0.08), run_time=0.45)
        self.beat(0.9)

        # hooks = the fix (right side)
        htitle = Text("Hooks let it \"hook into\" React:", font_size=25, color=INK, weight="BOLD")
        htitle.to_edge(RIGHT, buff=0.85).shift(UP * 2.15).align_to(head, RIGHT)
        htitle.to_edge(RIGHT, buff=0.85)
        self.play(FadeIn(htitle, shift=DOWN * 0.1), run_time=0.5)

        rows = VGroup(
            VGroup(chip("useState", STATE_C, fs=22, w=2.5),
                   Text("→ memory", font_size=23, color=STATE_C)).arrange(RIGHT, buff=0.3),
            VGroup(chip("useEffect", EFFECT_C, fs=22, w=2.5),
                   Text("→ lifecycle", font_size=23, color=EFFECT_C)).arrange(RIGHT, buff=0.3),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        rows.next_to(htitle, DOWN, buff=0.4).align_to(htitle, LEFT)
        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.15), run_time=0.55)
            self.beat(0.5)

        others = Text("…plus useRef, useContext, useMemo, useReducer",
                      font_size=18, color=MUTED)
        if others.width > 5.6:
            others.scale_to_fit_width(5.6)
        others.next_to(rows, DOWN, buff=0.4).align_to(rows, LEFT)
        rule = Text("Every hook's name starts with \"use\".",
                    font_size=21, color=REACT, slant=ITALIC)
        rule.next_to(others, DOWN, buff=0.3).align_to(rows, LEFT)
        self.play(FadeIn(others), run_time=0.5)
        self.beat(0.5)
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.5)

        punch = Text("This video: the two you'll use every single day.",
                     font_size=26, color=INK, weight="BOLD").to_edge(DOWN, buff=0.4)
        self.play(Write(punch), run_time=1.0)
        self.play(Indicate(rows[0][0], color=STATE_C, scale_factor=1.08),
                  Indicate(rows[1][0], color=EFFECT_C, scale_factor=1.08), run_time=0.9)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — useState: change state → re-render
    # ====================================================================== #
    def scene_state(self):
        self._cap = None
        head = self.section_header("2", "useState — memory", STATE_C)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.5)

        # the one line, as a single Text (correct spacing / commas on the baseline)
        S = "const [count, setCount] = useState(0)"
        line = code_line_1(S, fs=30)
        line.shift(UP * 1.75)
        self.play(Write(line), run_time=1.1)
        self.beat(0.6)

        val_piece = glyph_slice(line, S, "count")
        set_piece = glyph_slice(line, S, "setCount")
        b1 = Brace(val_piece, DOWN, color=MUTED)
        l1 = Text("the current value", font_size=20, color=PLAIN).next_to(b1, DOWN, buff=0.12)
        b2 = Brace(set_piece, UP, color=MUTED)
        l2 = Text("the updater", font_size=20, color=FN).next_to(b2, UP, buff=0.12)
        self.play(GrowFromCenter(b1), FadeIn(l1, shift=DOWN * 0.1), run_time=0.5)
        self.play(GrowFromCenter(b2), FadeIn(l2, shift=UP * 0.1), run_time=0.5)
        self.beat(0.8)
        self.play(FadeOut(VGroup(b1, l1, b2, l2)), run_time=0.4)

        # a live counter card + a +1 button
        card = RoundedRectangle(width=3.0, height=2.4, corner_radius=0.22,
                                stroke_color=STATE_C, stroke_width=2.5,
                                fill_color=DEVICE_BG, fill_opacity=1.0)
        card.shift(LEFT * 3.4 + DOWN * 1.1)
        clab = Text("count", font_size=20, color=MUTED).next_to(card.get_top(), DOWN, buff=0.25)
        num = Integer(0, font_size=76, color=INK)
        num.move_to(card.get_center() + UP * 0.15)
        btn = make_button("+1", color=STATE_C, w=1.5, h=0.6, fs=24)
        btn.next_to(card, DOWN, buff=0.35)
        cursor = make_cursor().move_to(btn.get_center() + RIGHT * 2.0 + DOWN * 1.0)
        self.play(FadeIn(card), FadeIn(clab), FadeIn(num), FadeIn(btn), FadeIn(cursor), run_time=0.7)

        expl = VGroup(
            Text("Click the button → call setCount →", font_size=24, color=INK),
            Text("React re-renders with the new value.", font_size=24, color=STATE_C, weight="BOLD"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        expl.to_edge(RIGHT, buff=0.85).shift(DOWN * 0.6)
        self.play(FadeIn(expl[0], shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(expl[1], shift=UP * 0.1), run_time=0.5)
        self.beat(0.7)

        # three clicks, each: highlight setCount, bump number, flash "re-render"
        for k in range(1, 4):
            self.click(btn, cursor, rt=0.4 if k > 1 else 0.55)
            self.play(Indicate(set_piece, color=FN, scale_factor=1.15), run_time=0.4)
            rr = Text("re-render", font_size=18, color=STATE_C, weight="BOLD")
            rr.next_to(card, UP, buff=0.18)
            self.play(num.animate.set_value(k),
                      FadeIn(rr, shift=UP * 0.1),
                      Indicate(card, color=STATE_C, scale_factor=1.03), run_time=0.5)
            self.play(FadeOut(rr, shift=UP * 0.15), run_time=0.3)
            self.beat(0.4)

        punch = Text("State is memory that survives re-renders. Change it → React redraws.",
                     font_size=25, color=INK, weight="BOLD").to_edge(DOWN, buff=0.4)
        self.play(Write(punch), run_time=1.1)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Why useEffect? side effects run after paint
    # ====================================================================== #
    def scene_side_effects(self):
        self._cap = None
        head = self.section_header("3", "Why useEffect?", EFFECT_C)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.5)

        # left: rendering is pure
        pure = VGroup(
            Text("Rendering should be pure", font_size=26, color=INK, weight="BOLD"),
            Text("UI  =  f( state )", font=MONO, font_size=30, color=GOOD),
            Text("same state → same UI,", font_size=21, color=MUTED),
            Text("no surprises.", font_size=21, color=MUTED),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        pure.to_edge(LEFT, buff=0.9).shift(UP * 1.1)
        purebox = SurroundingRectangle(pure, color=GOOD, buff=0.3, corner_radius=0.14)
        purebox.set_stroke(width=2)
        self.play(FadeIn(pure, shift=UP * 0.1), Create(purebox), run_time=0.9)
        self.beat(0.9)

        # right: real apps must reach the outside world = side effects
        side = Text("But real apps must reach the outside world:",
                    font_size=25, color=INK)
        side.to_edge(RIGHT, buff=0.7).shift(UP * 2.05)
        side.to_edge(RIGHT, buff=0.7)
        self.play(FadeIn(side, shift=DOWN * 0.1), run_time=0.5)
        effects = VGroup(
            chip("fetch data from a server", REACT, fs=20, w=4.6, h=0.62),
            chip("start a timer / interval", ACCENT, fs=20, w=4.6, h=0.62),
            chip("subscribe to events", STATE_C, fs=20, w=4.6, h=0.62),
            chip("change the document title", GOOD, fs=20, w=4.6, h=0.62),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        effects.next_to(side, DOWN, buff=0.35).align_to(side, LEFT)
        for e in effects:
            self.play(FadeIn(e, shift=RIGHT * 0.12), run_time=0.4)
        sidelbl = Text("these are \"side effects\"", font_size=21, color=EFFECT_C, slant=ITALIC)
        sidelbl.next_to(effects, DOWN, buff=0.3).align_to(effects, LEFT)
        self.play(FadeIn(sidelbl), run_time=0.4)
        self.beat(0.9)

        # the timeline: render → paint → THEN effect
        self.play(FadeOut(VGroup(pure, purebox, side, effects, sidelbl)), run_time=0.5)
        nodes = VGroup(
            chip("render", GOOD, fs=22, w=2.3, h=0.7),
            chip("browser paints", REACT, fs=22, w=3.1, h=0.7),
            chip("useEffect runs", EFFECT_C, fs=22, w=3.1, h=0.7),
        ).arrange(RIGHT, buff=1.15).move_to(UP * 0.4)
        arrows = VGroup(*[
            Arrow(nodes[i].get_right(), nodes[i + 1].get_left(), buff=0.12,
                  stroke_width=4, color=MUTED, max_tip_length_to_length_ratio=0.25)
            for i in range(2)])
        tl = Text("useEffect runs your side-effect code AFTER the screen is painted.",
                  font_size=24, color=INK).next_to(nodes, DOWN, buff=0.9)
        self.play(FadeIn(nodes[0], shift=RIGHT * 0.1), run_time=0.4)
        self.play(GrowArrow(arrows[0]), FadeIn(nodes[1], shift=RIGHT * 0.1), run_time=0.5)
        self.play(GrowArrow(arrows[1]), FadeIn(nodes[2], shift=RIGHT * 0.1), run_time=0.5)
        self.play(FadeIn(tl, shift=UP * 0.1), run_time=0.6)
        self.play(Indicate(nodes[2], color=EFFECT_C, scale_factor=1.08), run_time=0.7)
        self.beat(0.7)
        punch = Text("So render stays pure — the messy outside stuff goes in an effect.",
                     font_size=25, color=EFFECT_C, weight="BOLD").to_edge(DOWN, buff=0.42)
        self.play(Write(punch), run_time=1.1)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Anatomy: useEffect(fn, [deps]) + cleanup
    # ====================================================================== #
    def scene_anatomy(self):
        self._cap = None
        head = self.section_header("4", "Anatomy of useEffect", EFFECT_C)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.5)

        # the signature, as a single Text; colour the two parts by glyph slice
        S = "useEffect(() => { … }, [deps])"
        sig = code_line_1(S, fs=32, t2c={"useEffect": HOOK})
        glyph_slice(sig, S, "() => { … }").set_color(FN)
        glyph_slice(sig, S, "[deps]").set_color(VAL)
        sig.shift(UP * 1.95)
        self.play(Write(sig), run_time=1.1)
        self.beat(0.5)

        fn_piece = glyph_slice(sig, S, "() => { … }")
        dep_piece = glyph_slice(sig, S, "[deps]")
        bf = Brace(fn_piece, DOWN, color=MUTED)
        lf = VGroup(
            Text("the effect", font_size=21, color=FN, weight="BOLD"),
            Text("your side-effect code", font_size=18, color=MUTED),
        ).arrange(DOWN, buff=0.08).next_to(bf, DOWN, buff=0.14)
        bd = Brace(dep_piece, DOWN, color=MUTED)
        ld = VGroup(
            Text("dependencies", font_size=21, color=VAL, weight="BOLD"),
            Text("WHEN to re-run it", font_size=18, color=MUTED),
        ).arrange(DOWN, buff=0.08).next_to(bd, DOWN, buff=0.14)
        self.play(GrowFromCenter(bf), FadeIn(lf, shift=UP * 0.1), run_time=0.6)
        self.beat(0.5)
        self.play(GrowFromCenter(bd), FadeIn(ld, shift=UP * 0.1), run_time=0.6)
        self.beat(0.8)
        self.play(FadeOut(VGroup(bf, lf, bd, ld)), run_time=0.4)

        # the dependency-array rulebook (three cases)
        cases_title = Text("The dependency array decides when the effect fires:",
                           font_size=24, color=INK).move_to(UP * 1.15)
        self.play(FadeIn(cases_title, shift=UP * 0.1), run_time=0.5)

        def case(code, colr, desc):
            c = Text(code, font=MONO, font_size=24, color=colr, weight="BOLD")
            cbox = RoundedRectangle(width=2.5, height=0.66, corner_radius=0.1,
                                    stroke_color=colr, stroke_width=2,
                                    fill_color=colr, fill_opacity=0.1)
            c.move_to(cbox)
            d = Text(desc, font_size=22, color=INK)
            return VGroup(VGroup(cbox, c), d).arrange(RIGHT, buff=0.45)

        cases = VGroup(
            case("[]", GOOD, "run once — after the first render  (on mount)"),
            case("[a, b]", REACT, "re-run whenever a or b change  (on update)"),
            case("(omitted)", BAD, "run after every render  (rarely what you want)"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.34)
        cases.move_to(DOWN * 0.85)
        for c in cases:
            self.play(FadeIn(c[0], shift=RIGHT * 0.1), FadeIn(c[1], shift=RIGHT * 0.1), run_time=0.55)
            self.beat(0.6)

        clean = Text("Return a function to clean up — cancel timers, unsubscribe, "
                     "ignore stale replies.",
                     font_size=22, color=EFFECT_C).to_edge(DOWN, buff=0.42)
        self.play(FadeIn(clean, shift=UP * 0.1), run_time=0.7)
        self.play(Circumscribe(cases[1], color=REACT, run_time=1.1))
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — THE EXAMPLE: click → load → update
    # ====================================================================== #
    def scene_example(self):
        self._cap = None
        self.hlrect = None
        self.dev_content = None
        head = self.section_header("5", "Click → load → update", REACT)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.5)

        spec = [
            (0, "function UserProfile() {"),
            (0, ""),
            (1, "const [userId, setUserId] = useState(1)"),
            (1, "const [user, setUser] = useState(null)"),
            (1, "const [loading, setLoading] = useState(false)"),
            (0, ""),
            (1, "useEffect(() => {"),
            (2, "setLoading(true)"),
            (2, "fetchUser(userId).then(u => {"),
            (3, "setUser(u)"),
            (3, "setLoading(false)"),
            (2, "})"),
            (1, "}, [userId])"),
            (0, ""),
            (1, "const onNext = () => setUserId(userId + 1)"),
            (0, ""),
            (1, "return ("),
            (2, "<>"),
            (3, "<button onClick={onNext}>Next user</button>"),
            (3, "{loading ? <Spinner/> : <Profile user={user}/>}"),
            (2, "</>"),
            (1, ")"),
            (0, "}"),
        ]
        panel, lines = self.code_panel(spec, title="UserProfile.jsx",
                                       target_h=4.9, target_w=6.9)
        panel.to_edge(LEFT, buff=0.5).shift(DOWN * 0.5)
        self.play(FadeIn(panel, shift=UP * 0.1), run_time=0.8)

        device = self.make_device(center=(4.15, -0.35, 0))
        self.play(FadeIn(device, shift=UP * 0.1), run_time=0.7)
        cursor = make_cursor().move_to(self.dev_button.get_center() + RIGHT * 1.6 + DOWN * 1.4)
        self.play(FadeIn(cursor), run_time=0.3)
        self.beat(0.4)

        USEEFFECT = [6, 7, 8, 9, 10, 11, 12]

        # ---------- mount: the effect runs on first render ----------
        self.say("First render — state starts here.", color=INK, rt=0.5)
        self.focus(panel, lines, [2, 3, 4], color=STATE_C)
        self.beat(1.0)
        self.say("After the first render, the effect runs.", color=EFFECT_C)
        self.focus(panel, lines, USEEFFECT, color=EFFECT_C)
        self.beat(0.7)
        self.focus(panel, lines, [7], color=EFFECT_C)      # setLoading(true)
        self.show_loading("1", rt=1.5)
        self.focus(panel, lines, [8, 9, 10], color=EFFECT_C)  # fetch .then → setState
        self.say("Data arrives → setState → re-render.", color=GOOD)
        self.swap_content(make_profile(USERS[0]), rt=0.55)
        self.play(Flash(self.dev_content, color=GOOD, flash_radius=1.4), run_time=0.7)
        self.beat(1.1)

        # ---------- the click the user asked about ----------
        self.unfocus(rt=0.3)
        self.say("Now click the button.", color=REACT)
        self.beat(0.3)
        self.click(self.dev_button, cursor)
        self.focus(panel, lines, [14], color=FN)           # onNext → setUserId(userId+1)
        self.say("Click calls setUserId:  1 → 2", color=STATE_C)
        self.beat(0.7)

        # deps callout — the crux — tucked in the gap just above the panel, with
        # the highlight bar already pointing at `}, [userId]`
        callout = Text("userId is a dependency  →  the effect re-runs",
                       font_size=21, color=VAL, weight="BOLD")
        if callout.width > panel[0].width:
            callout.scale_to_fit_width(panel[0].width)
        callout.next_to(panel, UP, buff=0.1)
        self.focus(panel, lines, [12], color=VAL)
        self.play(FadeIn(callout, shift=DOWN * 0.1), run_time=0.6)
        self.beat(0.7)
        self.focus(panel, lines, USEEFFECT, color=EFFECT_C)
        self.show_loading("2", rt=1.4)
        self.swap_content(make_profile(USERS[1]), rt=0.55)
        self.play(Flash(self.dev_content, color=REACT, flash_radius=1.4), run_time=0.7)
        self.say("The UI updated — with no manual redraw.", color=GOOD)
        self.beat(1.0)

        # ---------- one more click, fast, to show the loop ----------
        self.play(FadeOut(callout), run_time=0.3)
        self.click(self.dev_button, cursor, rt=0.45)
        self.focus(panel, lines, [14], color=FN)
        self.focus(panel, lines, USEEFFECT, color=EFFECT_C)
        self.show_loading("3", rt=1.2)
        self.swap_content(make_profile(USERS[2]), rt=0.5)
        self.play(Flash(self.dev_content, color=GOOD, flash_radius=1.4), run_time=0.6)
        self.beat(0.6)

        # the loop, spelled out
        self.unfocus(rt=0.3)
        loop = Text("click  →  setState  →  deps changed  →  effect re-runs  →  "
                    "loading  →  data  →  re-render",
                    font_size=20, color=INK, weight="BOLD")
        loop.scale_to_fit_width(min(loop.width, 13.0)).to_edge(DOWN, buff=0.35)
        if self._cap is not None:
            self.play(ReplacementTransform(self._cap, loop), run_time=0.6)
            self._cap = loop
        else:
            self.play(FadeIn(loop), run_time=0.6)
        self.play(Circumscribe(loop, color=REACT, run_time=1.2))
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 6 — The render cycle (mental model)
    # ====================================================================== #
    def scene_cycle(self):
        self._cap = None
        head = self.section_header("6", "The render cycle", REACT)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.5)

        C = np.array([0.0, -0.35, 0.0])
        R = 2.35                       # boxes sit ON this circle
        specs = [("state changes", STATE_C, 90),
                 ("React re-renders", REACT, 0),
                 ("screen paints", GOOD, -90),
                 ("effect runs", EFFECT_C, 180)]
        boxes = []
        for text, color, deg in specs:
            a = np.radians(deg)
            b = chip(text, color, fs=21, h=0.74,
                     w=Text(text, font_size=21).width + 0.7, fill=0.16)
            b.move_to(C + R * np.array([np.cos(a), np.sin(a), 0]))
            b.set_z_index(2)           # boxes always on top
            boxes.append(b)

        # arrows ride the SAME circle, trimmed to start/end at the box borders and
        # tucked behind the boxes (z=0) so nothing crosses the labels
        DEG = [90, 0, -90, 180]        # clockwise order
        gap = 0.40                     # radians trimmed at each box
        arcs = []
        for i in range(4):
            a0 = np.radians(DEG[i]) - gap
            a1 = np.radians(DEG[i] - 90) + gap
            p0 = C + R * np.array([np.cos(a0), np.sin(a0), 0])
            p1 = C + R * np.array([np.cos(a1), np.sin(a1), 0])
            arc = ArcBetweenPoints(p0, p1, angle=(a0 - a1),
                                   color=MUTED, stroke_width=3.5)
            arc.add_tip(tip_length=0.22, tip_width=0.22)
            arc.set_z_index(0)
            arcs.append(arc)

        self.play(LaggedStart(*[FadeIn(b, scale=0.85) for b in boxes],
                              lag_ratio=0.14), run_time=1.0)
        self.play(LaggedStart(*[Create(a) for a in arcs], lag_ratio=0.18), run_time=1.5)

        gate = Text("only if deps changed", font_size=18, color=VAL, slant=ITALIC)
        gate.next_to(boxes[3], LEFT, buff=0.3)
        self.play(FadeIn(gate, shift=RIGHT * 0.1), run_time=0.5)
        self.beat(0.7)

        # a token travels the loop twice
        token = Dot(radius=0.13, color=ACCENT).set_z_index(3).move_to(boxes[0].get_center())
        self.add(token)
        self.say("state → re-render → paint → effect → …", color=INK)
        for _ in range(2):
            for a in arcs:
                self.play(MoveAlongPath(token, a), run_time=0.55, rate_func=linear)
        self.play(FadeOut(token), run_time=0.3)
        self.beat(0.4)

        warn = VGroup(
            Text("No deps + setState in the effect", font_size=21, color=BAD),
            Text("→ runs every render → infinite loop", font_size=21, color=BAD, weight="BOLD"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        warn.to_corner(UR, buff=0.6).shift(DOWN * 0.2)
        self.play(FadeIn(warn, shift=LEFT * 0.1), run_time=0.6)
        self.beat(0.8)

        # clear the white caption BEFORE writing the blue punch (no overlap)
        if self._cap is not None:
            self.play(FadeOut(self._cap, shift=DOWN * 0.15), run_time=0.35)
            self._cap = None
        punch = Text("The dependency array decides when your effect re-syncs.",
                     font_size=25, color=REACT, weight="BOLD").to_edge(DOWN, buff=0.42)
        self.play(Write(punch), run_time=1.1)
        self.play(Circumscribe(punch, color=REACT, run_time=1.1))
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 7 — Recap
    # ====================================================================== #
    def scene_recap(self):
        self._cap = None
        head = self.section_header("RECAP", "The mental model", ACCENT)
        self.play(FadeIn(head, shift=DOWN * 0.2), run_time=0.6)

        points = [
            ("Hooks give a function component memory + lifecycle.", REACT),
            ("useState:  change state  →  React re-renders.", STATE_C),
            ("useEffect(fn, [deps]):  run after render, re-run when deps change, "
             "clean up after yourself.", EFFECT_C),
        ]
        rows = VGroup()
        for txt, c in points:
            tick = make_tick(color=c, scale=0.95)
            t = Text(txt, font_size=25, color=INK)
            t.scale_to_fit_width(min(t.width, 10.6))
            rows.add(VGroup(tick, t).arrange(RIGHT, buff=0.28))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.55).move_to(UP * 0.35)
        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.2), run_time=0.7)
            self.beat(0.8)

        hook = Text("Render for the screen. useEffect for everything else.",
                    font_size=28, color=ACCENT, weight="BOLD").to_edge(DOWN, buff=0.6)
        self.play(Write(hook), run_time=1.3)
        self.play(Circumscribe(hook, color=ACCENT, run_time=1.3))
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_hooks()
        self.scene_state()
        self.scene_side_effects()
        self.scene_anatomy()
        self.scene_example()
        self.scene_cycle()
        self.scene_recap()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_RXBase):
    def construct(self):
        self.play_intro()


class Hooks(_RXBase):
    def construct(self):
        self.scene_hooks()


class State(_RXBase):
    def construct(self):
        self.scene_state()


class SideEffects(_RXBase):
    def construct(self):
        self.scene_side_effects()


class Anatomy(_RXBase):
    def construct(self):
        self.scene_anatomy()


class Example(_RXBase):
    def construct(self):
        self.scene_example()


class Cycle(_RXBase):
    def construct(self):
        self.scene_cycle()


class Recap(_RXBase):
    def construct(self):
        self.scene_recap()


class Outro(_RXBase):
    def construct(self):
        self.play_outro()


class ReactHooks(_RXBase):
    """The whole ~3-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    ReactHooks().render()

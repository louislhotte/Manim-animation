"""Race Conditions in React — a short, house-style explainer.

The classic React bug: an effect fetches data when a prop changes, the user
changes it faster than the network responds, and the responses come back out of
order — so a *stale* response overwrites the fresh one and the UI shows the
wrong data. Then the one-line fix (an ``ignore`` cleanup flag), and the upgrade
(``AbortController``).

    1. The Setup  -- a Profile fetches a user in useEffect on every userId change
    2. The Race   -- click Alice then Bob; Bob returns first, Alice returns LAST
                     and wins -> the screen shows Alice while Bob is selected  X
    3. The Fix    -- a cleanup flag: `let ignore=false; return ()=>ignore=true`
                     so the stale response is dropped by `if (!ignore) setUser()`
    4. Level Up   -- AbortController cancels the in-flight fetch; the recap + rule

No voice-over: everything is on screen and every hold is timed to be read. Uses
``Text`` (Pango), never ``Tex``, so it renders with no LaTeX toolchain. Code is
set in Menlo, syntax-coloured, and highlighted line-by-line as it's explained.

Scenes render alone (``Intro``, ``Setup``, ``Race``, ``Fix``, ``Recap``,
``Outro``) or as one film (``RaceConditionsReact``).

Env knobs:
    RACE_QUICK=1    collapse every reading hold for a fast render
    RACE_DELAY=1.2  override the reading-hold multiplier (seconds per "beat")
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


QUICK = os.environ.get("RACE_QUICK") == "1"
# Reading rhythm: every hold is self.beat(t) == wait(t * DELAY). Short film, so
# DELAY is a touch snappier than the sibling explainers but still readable.
DELAY = float(os.environ.get("RACE_DELAY", "0.28" if QUICK else "1.7"))
END_HOLD = 0.2 if QUICK else 2.2
ANIM_SLOW = 1.0 if QUICK else 1.2

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

REACT = "#61DAFB"     # React brand cyan (headers, logo, punchlines)
USER_A = "#C792EA"    # Alice — purple  (the SLOW request, clicked first)
USER_B = "#38BDF8"    # Bob   — sky blue (the FAST request, clicked last)

# ---- code (Night-Owl-ish) palette ----------------------------------------- #
MONO = "Menlo"
CODE_FS = 20
PLAIN = "#D6DEEB"
COMMENT = "#5F6B7E"
KW = "#C792EA"        # language keywords
FN = "#82AAFF"        # hooks / calls
VAL = "#F78C6C"       # literals
STR = "#7FDBCA"       # strings

# distinctive tokens -> colour; pruned per-line so ranges never collide (below)
JSX_KW = {"function": KW, "const": KW, "let": KW, "return": KW, "if": KW,
          "new": KW, "async": KW, "await": KW}
JSX_FN = {"useEffect": FN, "useState": FN, "fetchUser": FN, "setUser": FN,
          "fetch": FN, "then": FN, "catch": FN, "json": FN,
          "AbortController": FN, "signal": FN, "abort": FN}
JSX_VAL = {"userId": VAL, "null": VAL, "true": VAL, "false": VAL}
JSX_T2C = {**JSX_FN, **JSX_KW, **JSX_VAL}


def _safe_t2c(s, table):
    """Per-line text->colour map, pruned so no key overlaps another.

    Manim's ``t2c`` raises on overlapping colour ranges — even for the same
    colour (e.g. ``fetch`` sitting inside ``fetchUser``). Keep only keys present
    in this line, then drop any key that is a substring of another present key.
    """
    present = {k: v for k, v in table.items() if k in s}
    keys = list(present)
    return {k: v for k, v in present.items()
            if not any(k != o and k in o for o in keys)}


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


def chip(text, color, fs=20, fill=0.14, w=None, h=0.56, tcolor=None, weight="NORMAL"):
    label = txt(text, fs=fs, color=tcolor or INK, weight=weight)
    width = (label.width + 0.5) if w is None else w
    box = RoundedRectangle(width=width, height=h, corner_radius=0.12,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=fill)
    label.move_to(box)
    g = VGroup(box, label)
    g.box = box
    g.label = label
    return g


def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]),
         np.array([0.24, 0.22, 0])])
    return v.set_stroke(color=color, width=sw).scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.16, -0.16, 0], [0.16, 0.16, 0])
    b = Line([-0.16, 0.16, 0], [0.16, -0.16, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


def react_atom(r=1.0, color=REACT, sw=4):
    """The React logo: a nucleus dot orbited by three tilted ellipses."""
    nucleus = Dot(ORIGIN, radius=0.13 * r, color=color)
    orbits = VGroup()
    for a in (0.0, PI / 3, 2 * PI / 3):
        e = Ellipse(width=2.0 * r, height=0.76 * r,
                    stroke_color=color, stroke_width=sw, fill_opacity=0)
        e.rotate(a)
        orbits.add(e)
    grp = VGroup(orbits, nucleus)
    grp.orbits = orbits
    grp.nucleus = nucleus
    return grp


def avatar(initials, color, r=0.5):
    ring = Circle(radius=r, stroke_color=color, stroke_width=3,
                  fill_color=color, fill_opacity=0.18)
    t = txt(initials, fs=int(round(44 * r)), color=color, weight="BOLD").move_to(ring)
    return VGroup(ring, t)


def app_frame(tag="Profile", w=3.4, h=2.5):
    """A little browser/app card (title bar + traffic lights), empty content."""
    bg = RoundedRectangle(width=w, height=h, corner_radius=0.16,
                          stroke_color=FAINT, stroke_width=2,
                          fill_color=PANEL, fill_opacity=1.0)
    bar = RoundedRectangle(width=w, height=0.5, corner_radius=0.16,
                           stroke_width=0, fill_color="#1B2230", fill_opacity=1.0)
    bar.move_to(bg).align_to(bg, UP)
    dots = VGroup(*[Dot(radius=0.045, color=c)
                    for c in ("#FF5F57", "#FEBC2E", "#28C840")]).arrange(RIGHT, buff=0.11)
    dots.move_to([bg.get_left()[0] + 0.4, bar.get_center()[1], 0])
    ttl = txt(tag, fs=14, color=MUTED, font=MONO)
    ttl.next_to(dots, RIGHT, buff=0.3).set_y(bar.get_center()[1])
    grp = VGroup(bg, bar, dots, ttl)
    grp.bg = bg
    grp.content_center = np.array([bg.get_center()[0], bg.get_center()[1] - 0.15, 0])
    return grp


def lifeline(label, x, color, y_top=2.15, y_bot=-2.55):
    """A sequence-diagram lifeline: a titled header over a vertical dashed line."""
    hdr = chip(label, color, fs=16, h=0.52, weight="BOLD").move_to([x, 2.62, 0])
    line = DashedLine([x, y_top, 0], [x, y_bot, 0], dash_length=0.13, dashed_ratio=0.6)
    line.set_stroke(MUTED, 2, opacity=0.55)
    g = VGroup(hdr, line)
    g.x = x
    g.hdr = hdr
    return g


def msg(x1, y1, x2, y2, color, label=None, sw=4.5):
    """A sloped message arrow between two lifelines, with an optional label."""
    start, end = np.array([x1, y1, 0]), np.array([x2, y2, 0])
    a = Arrow(start, end, buff=0.05, stroke_width=sw, color=color,
              max_tip_length_to_length_ratio=0.06, tip_length=0.22)
    g = VGroup(a)
    g.arrow = a
    if label:
        lab = txt(label, fs=15, color=color)
        maxw = abs(x2 - x1) - 0.6
        if lab.width > maxw:
            lab.scale_to_fit_width(max(1.2, maxw))
        lab.move_to((start + end) / 2).shift(UP * 0.22)
        g.add(lab)
        g.lab = lab
    return g


# ========================================================================== #
class _RaceBase(Scene):
    def setup(self):
        self.camera.background_color = BG
        self._cap = None
        self.hlrect = None

    # Slow every played animation uniformly (see ANIM_SLOW). self.wait() routes
    # through play(Wait(...)), so we must NOT scale those — holds obey DELAY.
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
        title = txt(label, fs=34, color=INK, weight="BOLD")
        head = VGroup(VGroup(tagbox, tag), title).arrange(RIGHT, buff=0.3)
        head.to_corner(UL, buff=0.5)
        line = Line(head.get_left(), head.get_right()).next_to(head, DOWN, buff=0.13)
        line.set_stroke(color=color, width=3)
        grp = VGroup(head, line)
        self.play(FadeIn(head, shift=RIGHT * 0.2), Create(line), run_time=0.7)
        return grp

    def say(self, text, color=INK, fs=26, rt=0.5, weight="BOLD"):
        """A single running caption pinned to the bottom edge."""
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

    # ---- bookend cards ---------------------------------------------------- #
    def _bookend_title(self, title, subtitle=None):
        header = txt(title, fs=52, color=INK, weight="BOLD")
        if header.width > 11.5:
            header.scale_to_fit_width(11.5)
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=REACT)
        writer = txt("Created by Ptolémé", fs=28, color=REACT)
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
        atom = react_atom(r=1.0, color=REACT).to_edge(UP, buff=0.9)
        self.play(Create(atom), run_time=1.5)
        self.play(Rotate(atom.orbits, angle=TAU / 2, about_point=atom.get_center()),
                  run_time=1.6, rate_func=smooth)
        grp = self._bookend_title(
            "Race Conditions in React",
            "why your UI shows the wrong data — and the one-line fix")
        self.card_wait(1.7)
        self.play(FadeOut(grp), FadeOut(atom), run_time=0.9)
        self.card_wait(0.2)

    def play_outro(self):
        self.card_wait(0.3)
        header = txt("Thanks for watching!", fs=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=REACT)
        writer = txt("Created by Ptolémé", fs=28, color=REACT)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.2)
        self.card_wait(0.6)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.card_wait(1.6)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.0)
        self.card_wait(0.3)

    # ---- code panel (house helper; also treats // as a comment) ----------- #
    def code_panel(self, spec, table, title="Profile.jsx", fs=CODE_FS,
                   indent_unit=0.5, line_buff=0.17, target_h=5.6, target_w=6.6):
        """spec: list of (indent, text); "" is a blank line. Returns (panel, lines)."""
        lines = []
        for indent, s in spec:
            if s == "":
                m = Rectangle(width=0.02, height=0.30, fill_opacity=0, stroke_opacity=0)
            elif s.lstrip().startswith(("#", "//")):
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
        # centre the bar on the panel first — the code VGroup is indent-shifted,
        # so align_to(UP) alone would leave the bar off in x.
        bar.move_to(bg).align_to(bg, UP)
        dots = VGroup(*[Dot(radius=0.045, color=c)
                        for c in ("#FF5F57", "#FEBC2E", "#28C840")]).arrange(RIGHT, buff=0.11)
        dots.move_to([bg.get_left()[0] + 0.42, bar.get_center()[1], 0])
        ttl = txt(title, fs=15, color=MUTED, font=MONO)
        max_ttl_w = bg.width - 1.5
        if ttl.width > max_ttl_w:
            ttl.scale_to_fit_width(max_ttl_w)
        ttl.next_to(dots, RIGHT, buff=0.34).set_y(bar.get_center()[1])
        code.shift(DOWN * 0.2)  # nudge below the title bar
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

    # ====================================================================== #
    # Scene 1 — The Setup (the innocent effect)
    # ====================================================================== #
    def scene_setup(self):
        self.section_header("01", "The Setup", REACT)

        spec = [
            (0, "function Profile({ userId }) {"),
            (1, "const [user, setUser] = useState(null);"),
            (0, ""),
            (1, "useEffect(() => {"),
            (2, "fetchUser(userId).then(user => {"),
            (3, "setUser(user);"),
            (2, "});"),
            (1, "}, [userId]);"),
            (0, ""),
            (1, "return <ProfileCard user={user} />;"),
            (0, "}"),
        ]
        panel, lines = self.code_panel(spec, JSX_T2C, title="Profile.jsx",
                                       target_h=5.4, target_w=6.0)
        panel.to_edge(LEFT, buff=0.55).shift(DOWN * 0.12)
        self.play(FadeIn(panel, shift=UP * 0.2), run_time=0.8)
        self.say("A Profile fetches a user whenever userId changes.", color=REACT)
        self.beat(1.4)

        self.focus(panel, lines, [3, 7], color=REACT)
        self.say("The effect re-runs on every new userId: fetch, then setUser.", color=REACT)
        self.beat(1.6)

        # right: the rendered card resolving one fetch --------------------- #
        frame = app_frame(tag="Profile", w=3.4, h=2.5)
        frame.to_edge(RIGHT, buff=0.8).shift(DOWN * 0.12)
        # content_center must be read AFTER positioning the frame
        cc = frame.bg.get_center() + np.array([0.0, -0.15, 0.0])
        self.play(FadeIn(frame, shift=UP * 0.15), run_time=0.5)
        uid = chip("userId = 1", ACCENT, fs=16, h=0.5, weight="BOLD").next_to(frame, UP, buff=0.3)
        self.play(FadeIn(uid, shift=DOWN * 0.1), run_time=0.4)

        self.focus(panel, lines, [4, 5], color=REACT)
        loading = txt("loading…", fs=18, color=MUTED).move_to(cc)
        self.play(FadeIn(loading), run_time=0.4)
        self.beat(0.8)
        who = VGroup(avatar("A", USER_A, r=0.46),
                     txt("Alice", fs=22, color=INK, weight="BOLD")).arrange(DOWN, buff=0.18)
        who.move_to(cc)
        self.play(ReplacementTransform(loading, who), run_time=0.6)
        self.play(Flash(who.get_center(), color=GOOD, line_length=0.15), run_time=0.3)
        self.say("The fetch resolves → setUser(Alice) → the card shows Alice.  ✓", color=GOOD)
        self.beat(1.8)

        # the question that sets up the bug -------------------------------- #
        q = txt("But what if userId changes faster than the fetch returns?",
                fs=25, color=WARN, weight="BOLD").to_edge(DOWN, buff=0.5)
        if q.width > 12.6:
            q.scale_to_fit_width(12.6)
        self.play(FadeOut(self._cap), run_time=0.3)
        self._cap = None
        if self.hlrect:
            self.play(FadeOut(self.hlrect), run_time=0.3)
            self.hlrect = None
        self.play(Write(q), run_time=1.0)
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — The Race (the bug), as a sequence diagram
    # ====================================================================== #
    def scene_race(self):
        self.section_header("02", "The Race", WARN)

        cx, sx = -3.2, 4.0
        client = lifeline("Client · Profile", cx, REACT)
        server = lifeline("Server · API", sx, ACCENT)
        self.play(FadeIn(client), FadeIn(server), run_time=0.7)

        # the user's clicks (buttons on the left) -------------------------- #
        btnA = chip("click Alice", USER_A, fs=15, h=0.5, weight="BOLD").move_to([-5.5, 1.8, 0])
        btnB = chip("click Bob", USER_B, fs=15, h=0.5, weight="BOLD").move_to([-5.5, 1.15, 0])
        self.play(FadeIn(btnA), FadeIn(btnB), run_time=0.5)
        self.say("You click Alice — then immediately click Bob.", color=INK)
        self.beat(1.0)

        # request A (Alice): the SLOW one, fired first --------------------- #
        self.play(Indicate(btnA, color=USER_A, scale_factor=1.12), run_time=0.5)
        reqA = msg(cx, 1.55, sx, 1.05, USER_A, label="GET /user/1")
        self.play(GrowArrow(reqA.arrow), run_time=0.6)
        self.play(FadeIn(reqA.lab), run_time=0.2)
        slowA = txt("slow ~900ms", fs=14, color=USER_A).next_to([sx, 1.05, 0], RIGHT, buff=0.2)
        self.play(FadeIn(slowA), run_time=0.3)

        # request B (Bob): the FAST one, fired second, now the selection --- #
        self.play(Indicate(btnB, color=USER_B, scale_factor=1.12), run_time=0.5)
        selring = SurroundingRectangle(btnB, color=USER_B, buff=0.08, corner_radius=0.12)
        self.play(Create(selring), run_time=0.4)
        reqB = msg(cx, 0.7, sx, 0.2, USER_B, label="GET /user/2")
        self.play(GrowArrow(reqB.arrow), run_time=0.6)
        self.play(FadeIn(reqB.lab), run_time=0.2)
        fastB = txt("fast ~300ms", fs=14, color=USER_B).next_to([sx, 0.2, 0], RIGHT, buff=0.2)
        self.play(FadeIn(fastB), run_time=0.3)
        self.say("Two requests are in flight. Bob is the current selection.", color=USER_B)
        self.beat(1.6)

        # response B returns FIRST -> setUser(Bob) ------------------------- #
        resB = msg(sx, -0.25, cx, -0.85, USER_B, label="200  Bob")
        self.play(GrowArrow(resB.arrow), run_time=0.6)
        self.play(FadeIn(resB.lab), run_time=0.2)
        noteB = chip("user ← Bob", USER_B, fs=15, h=0.5, weight="BOLD", tcolor=USER_B)
        if noteB.width > 2.4:
            noteB.scale_to_fit_width(2.4)
        noteB.next_to([cx, -0.85, 0], LEFT, buff=0.28)
        self.play(FadeIn(noteB, shift=LEFT * 0.1), run_time=0.4)
        self.say("Bob's response is quick — it lands first.  setUser(Bob).", color=USER_B)
        self.beat(1.6)

        # response A returns LAST -> setUser(Alice), overwriting Bob ------- #
        resA = msg(sx, -1.4, cx, -2.15, USER_A, label="200  Alice")
        self.play(GrowArrow(resA.arrow), run_time=0.7)
        self.play(FadeIn(resA.lab), run_time=0.2)
        noteA = chip("user ← Alice", USER_A, fs=15, h=0.5, weight="BOLD", tcolor=USER_A)
        if noteA.width > 2.4:
            noteA.scale_to_fit_width(2.4)
        noteA.next_to([cx, -2.15, 0], LEFT, buff=0.28)
        self.play(FadeIn(noteA, shift=LEFT * 0.1), run_time=0.4)
        self.say("Alice was slower — her response lands LAST and overwrites Bob.", color=USER_A)
        self.beat(1.8)

        # the bug: selected Bob, but showing Alice ------------------------- #
        self.play(FadeOut(self._cap), run_time=0.3)
        self._cap = None
        bad_sel = SurroundingRectangle(btnB, color=BAD, buff=0.09, corner_radius=0.12)
        bad_note = SurroundingRectangle(noteA, color=BAD, buff=0.08, corner_radius=0.12)
        cross = make_cross(BAD, sw=8).scale(1.1).next_to(noteA, DOWN, buff=0.2)
        self.play(ReplacementTransform(selring, bad_sel), Create(bad_note), run_time=0.6)
        self.play(FadeIn(cross, scale=1.3), run_time=0.4)
        verdict = txt("Selected Bob — but the screen shows Alice. The stale response won.",
                      fs=24, color=BAD, weight="BOLD").to_edge(DOWN, buff=0.5)
        if verdict.width > 12.6:
            verdict.scale_to_fit_width(12.6)
        self.play(Write(verdict), run_time=1.0)
        self._cap = verdict
        self.beat(2.2)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — The Fix (the ignore cleanup flag)
    # ====================================================================== #
    def scene_fix(self):
        self.section_header("03", "The Fix", GOOD)

        spec = [
            (0, "useEffect(() => {"),
            (1, "let ignore = false;"),
            (0, ""),
            (1, "fetchUser(userId).then(user => {"),
            (2, "if (!ignore) setUser(user);"),
            (1, "});"),
            (0, ""),
            (1, "// runs before the next effect"),
            (1, "return () => { ignore = true; };"),
            (0, "}, [userId]);"),
        ]
        panel, lines = self.code_panel(spec, JSX_T2C, title="Profile.jsx  (fixed)",
                                       target_h=5.0, target_w=5.6)
        panel.to_edge(LEFT, buff=0.5).shift(DOWN * 0.1)
        self.play(FadeIn(panel, shift=UP * 0.2), run_time=0.8)
        self.say("Add a flag. Its cleanup runs before the next effect.", color=GOOD)
        self.beat(1.4)

        # right: two effect instances, each with its own ignore flag ------- #
        RX = 3.0

        def effect_row(tag, col, y):
            title_c = chip(tag, col, fs=15, h=0.48, weight="BOLD", tcolor=col)
            flag = chip("ignore = false", col, fs=15, h=0.48, tcolor=col)
            row = VGroup(title_c, flag).arrange(DOWN, buff=0.14)
            box = RoundedRectangle(width=row.width + 0.5, height=row.height + 0.4,
                                   corner_radius=0.12, stroke_color=col, stroke_width=2,
                                   fill_color=col, fill_opacity=0.06)
            row.move_to(box)
            g = VGroup(box, row)
            g.flag = flag
            g.box = box
            g.move_to([RX, y, 0])
            return g

        rowA = effect_row("userId = 1", USER_A, 1.35)
        self.focus(panel, lines, [0, 1], color=GOOD)
        self.play(FadeIn(rowA, shift=UP * 0.15), run_time=0.6)
        self.say("Alice's effect runs — its own ignore starts false.", color=USER_A)
        self.beat(1.4)

        # userId changes -> cleanup of A fires (ignore=true) --------------- #
        self.focus(panel, lines, [8], color=GOOD)
        newflagA = chip("ignore = true", BAD, fs=15, h=0.48, tcolor=BAD)
        newflagA.move_to(rowA.flag)
        self.play(rowA.box.animate.set_stroke(MUTED).set_fill(MUTED, 0.05),
                  ReplacementTransform(rowA.flag, newflagA), run_time=0.6)
        rowA.flag = newflagA
        self.play(Flash(newflagA.get_center(), color=BAD, line_length=0.12), run_time=0.3)
        self.say("userId → 2 runs Alice's cleanup first:  ignore = true.", color=BAD)
        self.beat(1.6)

        # then Bob's effect runs (fresh ignore=false) ---------------------- #
        rowB = effect_row("userId = 2", USER_B, -0.95)
        self.focus(panel, lines, [0, 1], color=GOOD)
        self.play(FadeIn(rowB, shift=UP * 0.15), run_time=0.6)
        self.say("Then Bob's effect runs — a fresh ignore = false.", color=USER_B)
        self.beat(1.4)

        showing = VGroup(txt("showing:", fs=18, color=MUTED),
                         txt("—", fs=20, color=MUTED, weight="BOLD")).arrange(RIGHT, buff=0.2)
        showing.move_to([RX, -2.25, 0])
        self.play(FadeIn(showing), run_time=0.3)

        # Bob's response arrives -> passes the guard ----------------------- #
        self.focus(panel, lines, [4], color=GOOD)
        rB = msg(6.6, -0.95, rowB.box.get_right()[0] + 0.05, -0.95, USER_B, label="Bob")
        self.play(GrowArrow(rB.arrow), run_time=0.5)
        self.play(FadeIn(rB.lab), run_time=0.2)
        okB = make_tick(GOOD, sw=7).scale(0.9).next_to(rowB.box, UP, buff=0.12)
        newshow = VGroup(txt("showing:", fs=18, color=MUTED),
                         txt("Bob", fs=20, color=USER_B, weight="BOLD")).arrange(RIGHT, buff=0.2)
        newshow.move_to(showing)
        self.play(FadeIn(okB, scale=1.2), ReplacementTransform(showing, newshow), run_time=0.5)
        showing = newshow
        self.say("Bob's response: !ignore is true → setUser(Bob).  ✓", color=USER_B)
        self.beat(1.6)

        # Alice's late response -> blocked by the guard -------------------- #
        rA = msg(6.6, 1.35, rowA.box.get_right()[0] + 0.05, 1.35, USER_A, label="Alice (late)")
        self.play(GrowArrow(rA.arrow), run_time=0.5)
        self.play(FadeIn(rA.lab), run_time=0.2)
        block = make_cross(BAD, sw=7).scale(1.0).next_to(rowA.box, UP, buff=0.12)
        strike = Line(rA.lab.get_left(), rA.lab.get_right()).set_stroke(BAD, 4)
        self.play(FadeIn(block, scale=1.2), Create(strike),
                  rA.arrow.animate.set_color(MUTED),
                  rA.lab.animate.set_opacity(0.5), run_time=0.6)
        self.say("Alice's stale response hits ignore = true → dropped.  ✗", color=BAD)
        self.beat(1.6)

        # verdict ----------------------------------------------------------- #
        self.play(FadeOut(self._cap), run_time=0.3)
        self._cap = None
        okbox = SurroundingRectangle(showing, color=GOOD, buff=0.12, corner_radius=0.1)
        verdict = txt("The screen stays on Bob — the fresh selection wins.",
                      fs=25, color=GOOD, weight="BOLD").to_edge(DOWN, buff=0.5)
        if verdict.width > 12.6:
            verdict.scale_to_fit_width(12.6)
        self.play(Create(okbox), Write(verdict), run_time=1.0)
        self._cap = verdict
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Level up (AbortController) + the recap
    # ====================================================================== #
    def scene_recap(self):
        self.section_header("04", "Level Up & Recap", REACT)

        spec = [
            (0, "useEffect(() => {"),
            (1, "const c = new AbortController();"),
            (1, "fetch(url, { signal: c.signal })"),
            (2, ".then(res => res.json())"),
            (2, ".then(setUser);"),
            (0, ""),
            (1, "// the cleanup cancels it"),
            (1, "return () => c.abort();"),
            (0, "}, [userId]);"),
        ]
        panel, lines = self.code_panel(spec, JSX_T2C, title="with AbortController",
                                       target_h=3.3, target_w=7.4)
        # centre it: sits clear of the top-left section header, with room below
        panel.move_to(ORIGIN).shift(UP * 0.15)
        self.play(FadeIn(panel, shift=UP * 0.2), run_time=0.8)
        self.say("Even better: cancel the request you no longer need.", color=REACT)
        self.beat(1.2)
        self.focus(panel, lines, [2], color=REACT)
        self.say("Pass an AbortSignal into fetch…", color=REACT)
        self.beat(1.0)
        self.focus(panel, lines, [7], color=REACT)
        self.say("…and the cleanup aborts it — no stale response to arrive at all.", color=REACT)
        self.beat(1.8)

        # clear code, land the takeaway ------------------------------------ #
        fades = [FadeOut(panel), FadeOut(self._cap)]
        if self.hlrect:
            fades.append(FadeOut(self.hlrect))
            self.hlrect = None
        self.play(*fades, run_time=0.5)
        self._cap = None

        title = txt("Race conditions in React", fs=30, color=INK, weight="BOLD")
        rows_data = [
            ("Async responses can arrive out of order",
             "the last setState wins — even when it's stale", WARN, False),
            ("Guard state with a cleanup flag",
             "let ignore = false … return () => (ignore = true)", GOOD, True),
            ("Or cancel the work itself",
             "AbortController + return () => controller.abort()", REACT, True),
            ("The rule",
             "every effect that starts async work must clean it up", ACCENT, False),
        ]
        rows = VGroup()
        for head_s, sub_s, col, mono in rows_data:
            tick = make_tick(col, sw=6).scale(0.9)
            head = txt(head_s, fs=24, color=INK, weight="BOLD")
            sub = (txt(sub_s, fs=17, color=MUTED, font=MONO) if mono
                   else txt(sub_s, fs=18, color=MUTED))
            body = VGroup(head, sub).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
            row = VGroup(tick, body).arrange(RIGHT, buff=0.3, aligned_edge=UP)
            rows.add(row)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.34)
        # group title + rows and centre the block, clear of the header up top
        block = VGroup(title, rows).arrange(DOWN, buff=0.5)
        if block.width > 12.6:
            block.scale_to_fit_width(12.6)
        block.move_to(ORIGIN).shift(UP * 0.1)

        self.play(FadeIn(title, shift=DOWN * 0.1), run_time=0.5)
        for row in rows:
            self.play(GrowFromCenter(row[0]), FadeIn(row[1], shift=RIGHT * 0.2), run_time=0.45)
            self.beat(0.7)
        self.beat(1.2)

        punch = txt("Clean up your effects.", fs=30, color=REACT, weight="BOLD")
        punch.to_edge(DOWN, buff=0.55)
        self.play(Write(punch), run_time=0.9)
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ---- the whole film --------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_setup()
        self.scene_race()
        self.scene_fix()
        self.scene_recap()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_RaceBase):
    def construct(self):
        self.play_intro()


class Setup(_RaceBase):
    def construct(self):
        self.scene_setup()


class Race(_RaceBase):
    def construct(self):
        self.scene_race()


class Fix(_RaceBase):
    def construct(self):
        self.scene_fix()


class Recap(_RaceBase):
    def construct(self):
        self.scene_recap()


class Outro(_RaceBase):
    def construct(self):
        self.play_outro()


class RaceConditionsReact(_RaceBase):
    """The whole ~2.5-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    RaceConditionsReact().render()

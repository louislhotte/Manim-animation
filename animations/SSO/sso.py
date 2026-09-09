"""How SSO Actually Works — a ~4-minute explainer, house-style.

Single Sign-On feels like magic: type your password once, and every other app
just lets you in. This film takes the magic apart and shows the real machinery —
the redirect dance, the cryptographically signed token, and the one trust
relationship that ties it all together.

We build it from the ground up:

    1. The problem   -- one password per app doesn't scale, and it leaks
    2. The players   -- User, App (Service Provider) and Identity Provider
    3. The dance     -- the redirect flow; your password only touches the IdP
    4. The token     -- a signed proof you can read but can't forge (JWT / SAML)
    5. The magic     -- one IdP session → every other app opens instantly
    6. In the wild   -- SAML vs OIDC, real IdPs, and the honest trade-off

The protocols shown are the two that actually run the internet's SSO:

    SAML 2.0     — XML assertions (enterprise SSO)
    OpenID Connect — a signed JWT id_token on top of OAuth 2.0 ("Sign in with…")

Everything is drawn with Manim ``Text`` (Pango), never ``Tex`` — so it renders
with no LaTeX toolchain. Scenes are exposed individually (``Problem``,
``Players``, ``Dance``, ``Token``, ``Magic``, ``World``, ``Recap``, ``Intro``,
``Outro``) and as one continuous film (``HowSSOWorks``).

Env knobs:
    SSO_QUICK=1   collapse every hold for a fast sanity render
    SSO_DELAY=..  reading-rhythm multiplier for the small inter-step pauses
    SSO_READ=..   absolute hold after a subtitle lands (seconds) — reading time
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

# --- crisp text (shared house fix) ----------------------------------------- #
# Manim's ``Text`` mangles letter/word spacing below ~20 pt. Render every glyph
# at a large base size and scale the mobject *down* — spacing stays crisp. This
# shadows manim's ``Text`` so every call benefits automatically.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("SSO_QUICK") == "1"
# Two separate pacing knobs so nothing feels rushed:
#   DELAY scales the small pauses *between* animation steps (motion rhythm).
#   READ  is the absolute hold after a block of text lands, so there is always
#         time to actually read it (the viewer wants a comfortable reading pace).
# ANIM_SLOW stretches every played animation so transitions aren't abrupt.
DELAY = float(os.environ.get("SSO_DELAY", 0.28 if QUICK else 1.05))
READ = float(os.environ.get("SSO_READ", 0.35 if QUICK else 2.8))
ANIM_SLOW = 1.0 if QUICK else 1.3
END_HOLD = 0.2 if QUICK else 2.4  # settle held on a finished scene before it wipes

# ---- palette (dark house style, shared across the series) ----------------- #
BG = "#0E1117"          # dark slate background
PANEL = "#151A23"       # panel fill
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
FAINT = "#2A3140"       # gridlines / lifelines
GOLD = "#FFD166"        # accent / rules

USER_C = "#5B8DEF"      # the user / browser (blue)
APP_C = "#2EC4B6"       # apps / service providers (teal)
IDP_C = "#C792EA"       # the Identity Provider (violet — the star)
TOKEN_C = "#FFD166"     # the signed token (gold — the hero object)
KEY_C = "#FF8C42"       # keys / signing / password (orange)
GOOD = "#3DD68C"        # verified / granted (green)
BAD = "#FF5C5C"         # breach / reject (red)
ACCENT = GOLD

MONO = "Menlo"          # code / base64 / claims
FONT = "Helvetica Neue"
_BaseText.set_default(font=FONT)


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


def mono(text, fs=18, color=INK):
    return Text(text, font_size=fs, color=color, font=MONO)


def chip(text, color, fs=20, fill=0.14, w=None, h=0.56, tcolor=None, weight="NORMAL", radius=0.12):
    label = txt(text, fs=fs, color=tcolor or INK, weight=weight)
    width = (label.width + 0.5) if w is None else w
    if label.width > width - 0.3:
        label.scale((width - 0.3) / label.width)
    box = RoundedRectangle(width=width, height=h, corner_radius=radius,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=fill)
    label.move_to(box)
    return VGroup(box, label)


def pill(text, color, fs=22, fill=0.16, weight="BOLD"):
    t = txt(text, fs=fs, color=color, weight=weight)
    box = RoundedRectangle(width=t.width + 0.44, height=t.height + 0.26,
                           corner_radius=0.13, stroke_color=color, stroke_width=2,
                           fill_color=color, fill_opacity=fill)
    box.move_to(t)
    return VGroup(box, t)


def plate(mob, pad_x=0.14, pad_y=0.09, op=0.72):
    """A translucent dark plate behind a label so it reads over anything."""
    bg = RoundedRectangle(width=mob.width + 2 * pad_x, height=mob.height + 2 * pad_y,
                          corner_radius=0.08, stroke_width=0,
                          fill_color=BG, fill_opacity=op).move_to(mob)
    return VGroup(bg, mob)


def arr(a, b, color=MUTED, sw=4, buff=0.12, tip=0.22):
    return Arrow(a, b, buff=buff, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.3, tip_length=tip)


def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])])
    return v.set_stroke(color=color, width=sw).scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.18, -0.18, 0], [0.18, 0.18, 0])
    b = Line([-0.18, 0.18, 0], [0.18, -0.18, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


def make_star(n=5, outer=0.09, inner=0.042, color=BG):
    pts = []
    for i in range(2 * n):
        ang = PI / 2 + i * PI / n
        r = outer if i % 2 == 0 else inner
        pts.append([r * np.cos(ang), r * np.sin(ang), 0])
    return Polygon(*pts, stroke_width=0, fill_color=color, fill_opacity=1)


# ---- glyphs (all hand-drawn Manim mobjects, no assets) -------------------- #
def person(color=USER_C, s=1.0):
    """A simple 'user' silhouette: head + body."""
    body = RoundedRectangle(width=0.5 * s, height=0.56 * s, corner_radius=0.14 * s,
                            color=color, fill_opacity=1, stroke_width=0)
    head = Circle(radius=0.18 * s, color=color, fill_opacity=1, stroke_width=0)
    head.next_to(body, UP, buff=0.04 * s)
    g = VGroup(body, head)
    g.body = body
    return g


def app_window(title, color=APP_C, w=1.95, h=1.2, fs=19):
    """A little app / browser window: title bar with traffic-lights + a name."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.1,
                            stroke_color=color, stroke_width=2.5,
                            fill_color=color, fill_opacity=0.06)
    bar = RoundedRectangle(width=w, height=0.3, corner_radius=0.1, stroke_width=0,
                           fill_color=color, fill_opacity=0.2)
    bar.move_to(body).align_to(body, UP)
    dots = VGroup(*[Dot(radius=0.037, color=c) for c in (BAD, GOLD, GOOD)]).arrange(RIGHT, buff=0.07)
    dots.move_to(bar).align_to(bar, LEFT).shift(RIGHT * 0.17)
    name = txt(title, fs=fs, color=INK, weight="BOLD")
    if name.width > w - 0.3:
        name.scale((w - 0.3) / name.width)
    name.move_to(body).shift(DOWN * 0.06)
    g = VGroup(body, bar, dots, name)
    g.body = body
    g.name = name
    return g


def shield(color=IDP_C, s=1.0, keyhole=True):
    """The Identity Provider: a crest shield with a keyhole — the guardian of
    who-you-are. Angular, so it reads as authority even at small size."""
    w, h = 0.95 * s, 1.0 * s
    pts = [
        [-w, 0.62 * h, 0],      # top-left shoulder
        [0, 0.82 * h, 0],       # domed top
        [w, 0.62 * h, 0],       # top-right shoulder
        [w, -0.05 * h, 0],      # right flank
        [0, -0.95 * h, 0],      # point
        [-w, -0.05 * h, 0],     # left flank
    ]
    body = Polygon(*pts, stroke_color=color, stroke_width=3,
                   fill_color=color, fill_opacity=0.14)
    g = VGroup(body)
    if keyhole:
        ring = Circle(radius=0.16 * s, stroke_width=0, fill_color=color, fill_opacity=0.95)
        ring.move_to(body.get_center() + UP * 0.06 * s)
        stem = Polygon([-0.07 * s, 0, 0], [0.07 * s, 0, 0], [0.045 * s, -0.24 * s, 0],
                       [-0.045 * s, -0.24 * s, 0], stroke_width=0,
                       fill_color=color, fill_opacity=0.95)
        stem.next_to(ring, DOWN, buff=-0.03 * s)
        g.add(ring, stem)
    g.body = body
    return g


def padlock(color=IDP_C, s=1.0, closed=True):
    """A padlock: a body, a shackle, a keyhole. ``closed`` seats the shackle;
    open lifts and tilts it."""
    body = RoundedRectangle(width=0.52 * s, height=0.44 * s, corner_radius=0.08 * s,
                            stroke_color=color, stroke_width=3,
                            fill_color=color, fill_opacity=0.18)
    shackle = Arc(radius=0.16 * s, start_angle=0, angle=PI, color=color, stroke_width=3.2)
    kh = VGroup(
        Dot(radius=0.035 * s, color=color),
        Line([0, 0, 0], [0, -0.1 * s, 0], color=color, stroke_width=2.4),
    ).arrange(DOWN, buff=0.0).move_to(body)
    if closed:
        shackle.next_to(body, UP, buff=-0.03 * s)
    else:
        shackle.next_to(body, UP, buff=-0.03 * s).shift(UP * 0.09 * s + LEFT * 0.08 * s)
        shackle.rotate(-0.5, about_point=shackle.get_bottom() + RIGHT * 0.16 * s)
    g = VGroup(body, shackle, kh)
    g.body = body
    g.shackle = shackle
    return g


def key_icon(color=KEY_C, s=1.0):
    """A key: a ring, a shaft and two teeth."""
    ring = Circle(radius=0.13 * s, stroke_color=color, stroke_width=3.4, fill_opacity=0)
    shaft = Rectangle(width=0.42 * s, height=0.065 * s, fill_color=color, fill_opacity=1, stroke_width=0)
    shaft.next_to(ring, RIGHT, buff=-0.02 * s)
    t1 = Rectangle(width=0.055 * s, height=0.14 * s, fill_color=color, fill_opacity=1, stroke_width=0)
    t1.next_to(shaft, DOWN, buff=0).align_to(shaft, RIGHT).shift(LEFT * 0.03 * s)
    t2 = Rectangle(width=0.055 * s, height=0.1 * s, fill_color=color, fill_opacity=1, stroke_width=0)
    t2.next_to(shaft, DOWN, buff=0).align_to(shaft, RIGHT).shift(LEFT * 0.16 * s)
    return VGroup(ring, shaft, t1, t2)


def token_chip(w=1.15, h=0.72, color=TOKEN_C, seal=True):
    """A compact signed token: a card with claim-lines and a wax seal."""
    card = RoundedRectangle(width=w, height=h, corner_radius=0.09,
                            stroke_color=color, stroke_width=2.5,
                            fill_color=color, fill_opacity=0.16)
    lines = VGroup(*[Line([0, 0, 0], [w * 0.42, 0, 0], stroke_color=color, stroke_width=2.4)
                     for _ in range(3)]).arrange(DOWN, buff=0.09)
    lines.move_to(card).shift(LEFT * w * 0.12 + UP * 0.02)
    g = VGroup(card, lines)
    if seal:
        s = VGroup(Circle(radius=0.1, stroke_width=0, fill_color=color, fill_opacity=1),
                   make_star(6, 0.075, 0.032, BG))
        s.move_to(card.get_corner(DR) + np.array([-0.16, 0.16, 0]))
        g.add(s)
    g.card = card
    return g


def cookie(s=1.0):
    """The IdP's browser session, drawn as a cookie."""
    body = Circle(radius=0.26 * s, fill_color="#E6B34D", fill_opacity=1,
                  stroke_color="#B8860B", stroke_width=2.4)
    chips = VGroup(*[Dot(radius=0.032 * s, color="#5B4310").move_to(
        body.get_center() + np.array([dx * s, dy * s, 0]))
        for dx, dy in [(0.08, 0.07), (-0.1, 0.03), (0.02, -0.11), (-0.03, 0.12), (0.12, -0.05)]])
    return VGroup(body, chips)


# ========================================================================== #
class _SSOBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # ---- timing helpers --------------------------------------------------- #
    def play(self, *anims, **kwargs):
        # stretch every real animation so transitions aren't abrupt, but never
        # scale a bare Wait (a reading hold, handled by read()/beat()).
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

    # ---- text helpers ----------------------------------------------------- #
    def section_header(self, label, color):
        t = txt(label, fs=33, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=4)
        return VGroup(t, line)

    def say(self, text, color=INK, fs=23, y=-3.42, weight="NORMAL"):
        """A bottom caption, width-clamped so it never runs off-screen."""
        m = txt(text, fs=fs, color=color, weight=weight)
        if m.width > 12.8:
            m.scale_to_fit_width(12.8)
        m.move_to([0, y, 0])
        return m

    def cite(self, s):
        return txt(s, fs=15, color=MUTED, slant=ITALIC).to_edge(DOWN, buff=0.16)

    # ---- packet motion ---------------------------------------------------- #
    def send(self, path, color=USER_C, rt=1.0, r=0.085, keep=False, rate=linear):
        p = Dot(radius=r, color=color).set_stroke(INK, 1.0).move_to(path.get_start())
        self.add(p)
        self.play(MoveAlongPath(p, path), run_time=rt, rate_func=rate)
        if keep:
            return p
        self.remove(p)
        return None

    # ---- house-style intro / outro cards ---------------------------------- #
    def play_intro(self):
        header = Text("How SSO Actually Works", font_size=58, color=INK, weight="BOLD")
        header.set(width=min(9.0, header.width))
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        # a padlock rides the rule and clicks OPEN — the wink
        lock = padlock(GOLD, s=0.9, closed=True).move_to(line.get_right() + RIGHT * 0.05 + UP * 0.28)
        writer = Text("Created by Ptolémé", font_size=28, color=USER_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.play(FadeIn(lock, shift=DOWN * 0.15), run_time=0.6)
        open_lock = padlock(GOLD, s=0.9, closed=False).move_to(lock)
        self.play(Transform(lock, open_lock), run_time=0.5)
        self.read(0.7)
        sub = Text("One login. Every door. Your password stays secret.",
                   font_size=30, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), FadeOut(lock), run_time=1.0)
        self.read(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        src = Text("the machinery behind “Sign in with…” · System Design",
                   font_size=22, color=MUTED)
        src.next_to(writer, DOWN, buff=0.4)
        self.play(FadeIn(src), run_time=0.8)
        self.read(1.4)
        self.play(FadeOut(VGroup(header, writer, line, src)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        writer = Text("Created by Ptolémé", font_size=28, color=USER_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = Text("Prove it once. Trust it everywhere.",
                     font_size=26, color=ACCENT)
        recap.next_to(writer, DOWN, buff=0.5)
        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap), run_time=0.8)
        self.read(1.6)
        self.play(FadeOut(VGroup(header, line, writer, recap)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 — The problem: a password per app doesn't scale
    # ====================================================================== #
    def scene_problem(self):
        title = Text("A password for every app", font_size=46, color=INK, weight="BOLD")
        self.play(Write(title), run_time=1.3)
        self.read(0.7)
        self.play(title.animate.scale(0.58).to_edge(UP, buff=0.42), run_time=0.7)

        # the user on the left, a grid of apps on the right
        user = person(USER_C, s=1.15).move_to([-5.2, 0.35, 0])
        ulbl = txt("you", fs=20, color=USER_C, weight="BOLD").next_to(user, DOWN, buff=0.2)
        self.play(FadeIn(user, shift=RIGHT * 0.2), FadeIn(ulbl), run_time=0.6)

        names = ["Email", "Chat", "Drive", "HR", "Cloud", "Bank"]
        grid = VGroup()
        for nm in names:
            w = app_window(nm, APP_C, w=1.95, h=1.16, fs=19)
            # a little password field inside each
            fld = RoundedRectangle(width=1.4, height=0.3, corner_radius=0.07,
                                   stroke_color=MUTED, stroke_width=1.6, fill_opacity=0)
            dots = VGroup(*[Dot(radius=0.035, color=INK) for _ in range(6)]).arrange(RIGHT, buff=0.07)
            dots.move_to(fld)
            fld_g = VGroup(fld, dots).next_to(w.name, DOWN, buff=0.12)
            w.add(fld_g)
            w.pw = fld_g
            grid.add(w)
        grid.arrange_in_grid(rows=2, cols=3, buff=(0.45, 0.5))
        grid.move_to([1.7, 0.2, 0])
        self.play(LaggedStart(*[FadeIn(w, shift=UP * 0.12) for w in grid],
                              lag_ratio=0.12, run_time=1.4))
        cap = self.say("Every app keeps its own copy of your password.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.2)

        # each app pulls a password from the user (same one — reuse)
        rays = VGroup(*[arr(user.get_right() + RIGHT * 0.1, w.pw.get_left(), color=KEY_C, sw=2.2, buff=0.12)
                        for w in grid])
        self.play(LaggedStart(*[Create(r) for r in rays], lag_ratio=0.08, run_time=1.0))
        cap2 = self.say("So you reuse one password everywhere — because who could remember six?",
                        color=INK)
        self.play(ReplacementTransform(cap, cap2), run_time=0.5)
        self.read(1.4)
        self.play(FadeOut(rays), run_time=0.4)

        # the breach: one app is popped, the reused password lights up everywhere
        victim = grid[2]  # top-right, so the "breached" tag sits in open space
        tag = pill("breached", BAD, fs=18).next_to(victim, UP, buff=0.12)
        self.play(victim.body.animate.set_stroke(BAD).set_fill(BAD, 0.14),
                  victim.pw[1].animate.set_color(BAD),
                  FadeIn(tag, shift=DOWN * 0.1), run_time=0.5)
        self.play(Flash(victim, color=BAD, flash_radius=1.1), run_time=0.6)
        cap3 = self.say("One breach leaks that password…", color=BAD, weight="BOLD")
        self.play(ReplacementTransform(cap2, cap3), run_time=0.5)
        self.read(0.9)

        # red arcs jump from the victim to every other app + the reused pw turns red
        jumps = VGroup()
        for w in grid:
            if w is victim:
                continue
            a = ArcBetweenPoints(victim.get_center(), w.get_center(), angle=-0.5)
            jumps.add(DashedVMobject(a, num_dashes=14).set_stroke(BAD, 2.4, opacity=0.85))
        self.play(LaggedStart(*[Create(j) for j in jumps], lag_ratio=0.06, run_time=0.9))
        self.play(*[w.pw[1].animate.set_color(BAD) for w in grid if w is not victim],
                  *[w.body.animate.set_stroke(BAD) for w in grid if w is not victim],
                  run_time=0.6)
        cap4 = self.say("…and every door with the same password swings open.", color=BAD, weight="BOLD")
        self.play(ReplacementTransform(cap3, cap4), run_time=0.5)
        self.read(1.5)

        # takeaway card
        self.play(FadeOut(Group(user, ulbl, grid, jumps, tag, cap4, title)), run_time=0.6)
        k1 = Text("Passwords don't scale.", font_size=40, color=INK, weight="BOLD")
        k2 = Text("Six apps shouldn't mean six secrets to leak.",
                  font_size=30, color=GOLD, weight="BOLD")
        VGroup(k1, k2).arrange(DOWN, buff=0.34).move_to(ORIGIN)
        self.play(FadeIn(k1, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(k2, shift=UP * 0.1), run_time=0.6)
        self.read(1.3)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — The players: User, App (SP) and Identity Provider
    # ====================================================================== #
    def scene_players(self):
        header = self.section_header("The idea: one trusted doorman", IDP_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # three actors laid out with room to breathe
        user = person(USER_C, s=1.25).move_to([-5.0, 0.6, 0])
        u_lab = pill("You", USER_C, fs=20).next_to(user, DOWN, buff=0.24)

        apps = VGroup(*[app_window(n, APP_C, w=2.0, h=0.9, fs=18) for n in ["Email", "Chat", "Drive"]])
        apps.arrange(DOWN, buff=0.3).move_to([0.2, 0.55, 0])
        a_lab = pill("Apps  ·  Service Providers", APP_C, fs=18).next_to(apps, DOWN, buff=0.26)

        idp = shield(IDP_C, s=1.35).move_to([5.05, 0.75, 0])
        i_lab = pill("Identity Provider", IDP_C, fs=19).next_to(idp, DOWN, buff=0.2)
        i_sub = txt("Okta · Google · Azure AD", fs=16, color=MUTED).next_to(i_lab, DOWN, buff=0.12)

        self.play(FadeIn(user, shift=RIGHT * 0.2), FadeIn(u_lab), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(a, shift=UP * 0.1) for a in apps], lag_ratio=0.15, run_time=0.9),
                  FadeIn(a_lab))
        self.read(0.6)
        self.play(FadeIn(idp, shift=LEFT * 0.2), FadeIn(i_lab), FadeIn(i_sub), run_time=0.7)
        cap = self.say("Three players. Your password will live in exactly one of them.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.4)

        # the trust relationship: the IdP hands each app its public key beforehand
        trust = VGroup(*[arr(idp.get_left() + LEFT * 0.05, a.get_right() + RIGHT * 0.05,
                            color=IDP_C, sw=2.6, buff=0.18) for a in apps])
        self.play(LaggedStart(*[GrowArrow(t) for t in trust], lag_ratio=0.12, run_time=0.9))
        # a key travels IdP -> apps: "trust established"
        for a in apps:
            k = key_icon(IDP_C, s=0.9).move_to(idp.get_left() + LEFT * 0.2)
            path = Line(idp.get_left() + LEFT * 0.2, a.get_right() + RIGHT * 0.25)
            self.add(k)
            self.play(MoveAlongPath(k, path), run_time=0.5, rate_func=linear)
            self.remove(k)
        tlbl = plate(txt("trust established (public keys)", fs=16, color=IDP_C))
        tlbl.move_to([2.4, 2.62, 0])
        self.play(FadeIn(tlbl), run_time=0.4)
        cap2 = self.say("Each app is set up once to trust the IdP — it holds the IdP's public key.")
        self.play(ReplacementTransform(cap, cap2), run_time=0.5)
        self.read(1.5)

        # the shift: apps stop checking passwords; they ask the IdP to vouch
        cross = make_cross(BAD, sw=5, scale=1.0).scale(0.7)
        no_pw = VGroup(txt("no passwords stored", fs=16, color=BAD)).arrange(RIGHT)
        badge = VGroup(cross, no_pw).arrange(RIGHT, buff=0.14)
        badge_plate = plate(badge).next_to(apps, LEFT, buff=0.35).shift(UP * 0.0)
        # keep it clear of the user glyph
        if badge_plate.get_left()[0] < user.get_right()[0] + 0.25:
            badge_plate.next_to(apps, UP, buff=0.2)
        self.play(FadeIn(badge_plate, shift=UP * 0.1), run_time=0.5)
        cap3 = self.say("Apps no longer store passwords. They just trust whoever the IdP vouches for.",
                        color=ACCENT)
        self.play(ReplacementTransform(cap2, cap3), run_time=0.5)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — The dance: the redirect flow
    # ====================================================================== #
    def scene_dance(self):
        header = self.section_header("The dance: how one login happens", USER_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        UX, AX, IX = -4.8, 0.0, 4.8
        top, bot = 1.7, -2.05

        # lane headers
        u_g = person(USER_C, s=0.9).move_to([UX, 2.35, 0])
        u_t = txt("You / Browser", fs=17, color=USER_C, weight="BOLD").next_to(u_g, DOWN, buff=0.12)
        a_g = app_window("App", APP_C, w=1.5, h=0.72, fs=17).move_to([AX, 2.35, 0])
        a_t = txt("App (SP)", fs=17, color=APP_C, weight="BOLD").next_to(a_g, DOWN, buff=0.12)
        i_g = shield(IDP_C, s=0.9).move_to([IX, 2.4, 0])
        i_t = txt("Identity Provider", fs=17, color=IDP_C, weight="BOLD").next_to(i_g, DOWN, buff=0.1)
        heads = VGroup(u_g, u_t, a_g, a_t, i_g, i_t)
        lifelines = VGroup(*[DashedLine([x, top, 0], [x, bot, 0], dash_length=0.11,
                                        stroke_color=FAINT, stroke_width=1.6)
                             for x in (UX, AX, IX)])
        self.play(FadeIn(heads), Create(lifelines), run_time=0.9)

        ys = [1.25, 0.63, 0.01, -0.61, -1.23, -1.85]
        cap = self.say("Step 1 — you open the app.")
        self.play(FadeIn(cap), run_time=0.4)

        def flow(y, x1, x2, color, label, rt=0.8, thick=4, tip=0.22):
            a = arr([x1, y, 0], [x2, y, 0], color=color, sw=thick, buff=0.1, tip=tip)
            lab = plate(txt(label, fs=15, color=color))
            lab.move_to([(x1 + x2) / 2, y + 0.22, 0])
            self.play(GrowArrow(a), FadeIn(lab), run_time=rt)
            return VGroup(a, lab)

        # 1. user -> app
        f1 = flow(ys[0], UX + 0.35, AX - 0.35, MUTED, "GET  /app")
        self.read(0.9)

        # 2. app -> idp (redirect)
        c = self.say("Step 2 — the app has no session, so it redirects you to the IdP.")
        self.play(ReplacementTransform(cap, c), run_time=0.4); cap = c
        f2 = flow(ys[1], AX + 0.35, IX - 0.35, MUTED, "redirect → IdP  (via browser)")
        self.read(1.2)

        # 3. user -> idp : password + MFA (the ONLY place the password appears)
        c = self.say("Step 3 — you sign in, once. This is the only place your password is ever typed.")
        self.play(ReplacementTransform(cap, c), run_time=0.4); cap = c
        f3 = flow(ys[2], UX + 0.35, IX - 0.35, KEY_C, "password + MFA  (once)", thick=4.5)
        # a padlock clicks shut at the IdP — creds captured & protected here only
        lock = padlock(KEY_C, s=0.7, closed=False).move_to([IX - 0.05, ys[2] - 0.02, 0]).shift(UP * 0.0)
        self.play(FadeIn(lock, scale=0.6), run_time=0.4)
        closed = padlock(GOOD, s=0.7, closed=True).move_to(lock)
        self.play(Transform(lock, closed), Flash(i_g, color=IDP_C, flash_radius=0.8), run_time=0.6)
        self.read(1.4)

        # 4. idp -> app : signed token (a token chip physically travels)
        c = self.say("Step 4 — the IdP mints a signed token that says who you are, and sends it back.")
        self.play(ReplacementTransform(cap, c), run_time=0.4); cap = c
        f4 = flow(ys[3], IX - 0.35, AX + 0.35, TOKEN_C, "signed token  (via browser)", thick=4.5)
        tok = token_chip(w=0.7, h=0.46).move_to([IX - 0.35, ys[3], 0])
        self.add(tok)
        self.play(tok.animate.move_to([AX + 0.1, ys[3], 0]), run_time=0.9, rate_func=linear)
        self.read(1.2)

        # 5. app verifies the signature (self-check at the App) — no call needed
        c = self.say("Step 5 — the app checks the signature with the IdP's public key. No password, no phone-call.")
        self.play(ReplacementTransform(cap, c), run_time=0.4); cap = c
        vkey = key_icon(GOOD, s=0.85).move_to([AX - 0.7, ys[4], 0])
        check = make_tick(GOOD, sw=6, scale=1.15).move_to([AX + 0.5, ys[4], 0])
        self.play(FadeIn(vkey, shift=RIGHT * 0.1), run_time=0.4)
        self.play(Write(check), Circumscribe(a_g, color=GOOD), run_time=1.0)
        self.read(1.2)

        # 6. app -> user : session started (a cookie rides back)
        c = self.say("Step 6 — the app starts your session. You're in.")
        self.play(ReplacementTransform(cap, c), run_time=0.4); cap = c
        f6 = flow(ys[5], AX - 0.35, UX + 0.35, GOOD, "session started — you're in")
        ck = cookie(0.7).move_to([AX - 0.35, ys[5], 0])
        self.add(ck)
        self.play(ck.animate.move_to([UX + 0.2, ys[5], 0]), run_time=0.8, rate_func=linear)
        self.read(1.2)

        # the payoff line of this scene: where the password went
        self.play(FadeOut(VGroup(f1, f2, f3, f4, f6, lock, tok, vkey, check, ck)),
                  run_time=0.5)
        b1 = VGroup(padlock(GOOD, s=0.55, closed=True), txt("IdP saw your password", fs=17, color=GOOD)).arrange(RIGHT, buff=0.16)
        b2 = VGroup(token_chip(0.5, 0.34), txt("App only saw a signed token", fs=17, color=TOKEN_C)).arrange(RIGHT, buff=0.16)
        badges = VGroup(plate(b1), plate(b2)).arrange(RIGHT, buff=0.7).move_to([0, -0.6, 0])
        c = self.say("Your password touched the IdP and nothing else. That's the whole security win.",
                     color=ACCENT)
        self.play(ReplacementTransform(cap, c), FadeIn(badges, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(self.cite("SP-initiated flow — the shape of both SAML 2.0 and OpenID Connect")),
                  run_time=0.4)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — The token: a proof you can read but can't forge
    # ====================================================================== #
    def scene_token(self):
        header = self.section_header("The token: read it, but can't forge it", TOKEN_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # the JWT: three base64 segments, dot-separated, colour-coded
        seg_specs = [("HEADER", "eyJhbGciOiJSUzI1NiJ9", USER_C),
                     ("PAYLOAD", "eyJzdWIiOiJhbGljZSIsimF1ZCI6…", IDP_C),
                     ("SIGNATURE", "Rk9SR0VELVBST09G…", KEY_C)]
        segs = VGroup()
        for name, b64, col in seg_specs:
            body = mono(b64, fs=16, color=col)
            if body.width > 3.4:
                body.scale_to_fit_width(3.4)
            box = RoundedRectangle(width=body.width + 0.34, height=0.62, corner_radius=0.09,
                                   stroke_color=col, stroke_width=2.2, fill_color=col, fill_opacity=0.1)
            body.move_to(box)
            lab = txt(name, fs=14, color=col, weight="BOLD").next_to(box, UP, buff=0.1)
            segs.add(VGroup(box, body, lab))
        segs.arrange(RIGHT, buff=0.36).move_to([0, 2.1, 0])
        dots = VGroup(*[txt(".", fs=40, color=MUTED).move_to(
            (segs[i].get_right() + segs[i + 1].get_left()) / 2 + DOWN * 0.08) for i in range(2)])
        self.play(LaggedStart(*[FadeIn(s, shift=UP * 0.1) for s in segs], lag_ratio=0.2, run_time=1.1),
                  FadeIn(dots))
        cap = self.say("This is a token — three Base64 parts: header, payload, signature.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.3)

        # expand the PAYLOAD into human-readable claims
        claims_rows = [("iss", "the IdP", "who issued it", IDP_C),
                       ("sub", "alice", "who you are", USER_C),
                       ("aud", "Email app", "who it's for", APP_C),
                       ("exp", "10:45", "when it expires", MUTED)]
        rows = VGroup()
        for k, v, note, col in claims_rows:
            kk = mono(f'"{k}"', fs=18, color=col)
            vv = mono(f': "{v}"', fs=18, color=INK)
            nn = txt(f"←  {note}", fs=16, color=MUTED)
            row = VGroup(kk, vv, nn).arrange(RIGHT, buff=0.18)
            rows.add(row)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        panel = RoundedRectangle(width=rows.width + 0.7, height=rows.height + 0.6, corner_radius=0.12,
                                 stroke_color=IDP_C, stroke_width=2, fill_color=PANEL, fill_opacity=0.55)
        rows.move_to(panel)
        claim_g = VGroup(panel, rows).move_to([0, -0.35, 0])
        link = arr(segs[1].get_bottom(), panel.get_top(), color=IDP_C, sw=2.4, buff=0.12)
        self.play(GrowArrow(link), FadeIn(claim_g, shift=UP * 0.1), run_time=0.8)
        cap2 = self.say("The payload is just claims — plain facts. Anyone can read them.")
        self.play(ReplacementTransform(cap, cap2), run_time=0.5)
        self.read(1.5)

        # signing: the IdP signs the hash with its PRIVATE key
        self.play(FadeOut(VGroup(link)), claim_g.animate.scale(0.92).to_edge(LEFT, buff=0.7).shift(DOWN * 0.1),
                  run_time=0.6)
        priv = VGroup(key_icon(KEY_C, s=1.1), txt("IdP private key", fs=16, color=KEY_C)).arrange(DOWN, buff=0.14)
        priv.move_to([3.6, 0.45, 0])
        sign_lbl = plate(txt("sign( hash(header.payload),  private key )", fs=15, color=KEY_C))
        sign_lbl.move_to([3.6, -0.7, 0])
        self.play(FadeIn(priv, shift=DOWN * 0.1), run_time=0.5)
        self.play(Indicate(segs[2], color=KEY_C, scale_factor=1.08),
                  segs[2][0].animate.set_fill(KEY_C, 0.22), run_time=0.7)
        self.play(FadeIn(sign_lbl), run_time=0.4)
        cap3 = self.say("The IdP signs it with its private key — only the IdP has that key.", color=KEY_C)
        self.play(ReplacementTransform(cap2, cap3), run_time=0.5)
        self.read(1.5)

        # verification: any app verifies with the PUBLIC key -> green check
        pub = VGroup(key_icon(GOOD, s=1.1), txt("IdP public key", fs=16, color=GOOD)).arrange(DOWN, buff=0.14)
        pub.move_to(priv)
        self.play(FadeOut(priv), FadeIn(pub, shift=UP * 0.1), run_time=0.5)
        big_check = make_tick(GOOD, sw=9, scale=1.6).move_to([5.6, 0.5, 0])
        self.play(Transform(sign_lbl, plate(txt("verify( token,  public key )  →  ✓", fs=15, color=GOOD)).move_to(sign_lbl)),
                  run_time=0.4)
        self.play(Write(big_check), segs[2][0].animate.set_stroke(GOOD).set_fill(GOOD, 0.16), run_time=0.7)
        cap4 = self.say("Any app verifies it with the IdP's public key — offline, in milliseconds.", color=GOOD)
        self.play(ReplacementTransform(cap3, cap4), run_time=0.5)
        self.read(1.5)

        # the tamper: flip a claim -> signature no longer matches -> REJECT
        self.play(FadeOut(VGroup(pub, sign_lbl, big_check)), run_time=0.4)
        forged = mono(': "Bank app"', fs=18, color=BAD)
        forged.move_to(rows[2][1], aligned_edge=LEFT)
        self.play(Indicate(rows[2], color=BAD, scale_factor=1.05), run_time=0.5)
        self.play(Transform(rows[2][1], forged),
                  rows[2][0].animate.set_color(BAD), run_time=0.6)
        steal = plate(txt("attacker edits a claim…", fs=16, color=BAD)).move_to([3.7, 0.6, 0])
        self.play(FadeIn(steal, shift=DOWN * 0.1), run_time=0.4)
        cap5 = self.say("Change one character, and the signature no longer matches the payload.", color=BAD)
        self.play(ReplacementTransform(cap4, cap5), run_time=0.5)
        self.read(1.2)
        # signature breaks
        neq = txt("hash ≠ signature", fs=20, color=BAD, weight="BOLD")
        neq_p = plate(neq).move_to([3.7, -0.5, 0])
        big_cross = make_cross(BAD, sw=10, scale=1.9).move_to([5.7, 0.4, 0])
        self.play(segs[2][0].animate.set_stroke(BAD).set_fill(BAD, 0.24),
                  FadeIn(neq_p), Write(big_cross), run_time=0.7)
        stamp = pill("FORGED — rejected", BAD, fs=22).rotate(-0.12).move_to([0.7, 1.05, 0])
        self.play(FadeIn(stamp, scale=1.4), Flash(stamp, color=BAD, flash_radius=1.4), run_time=0.7)
        cap6 = self.say("You can read the token. You can't forge it. That's the whole trick.",
                        color=ACCENT, weight="BOLD")
        self.play(ReplacementTransform(cap5, cap6), run_time=0.5)
        self.play(FadeIn(self.cite("OIDC id_token = a signed JWT · SAML = a signed XML assertion")),
                  run_time=0.4)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — The magic: one login, every door
    # ====================================================================== #
    def scene_magic(self):
        header = self.section_header("The magic: one login, every door", GOOD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # the IdP with a live session (cookie) sits centre-top
        idp = shield(IDP_C, s=1.0).move_to([0, 2.05, 0])
        ck = cookie(0.85).next_to(idp, RIGHT, buff=0.25)
        i_lab = plate(txt("IdP  ·  you're already signed in here", fs=16, color=IDP_C))
        i_lab.next_to(idp, LEFT, buff=0.3)
        self.play(FadeIn(idp), FadeIn(i_lab), run_time=0.5)
        self.play(FadeIn(ck, scale=0.6), Flash(ck, color=GOLD, flash_radius=0.6), run_time=0.6)
        cap = self.say("You've signed in once. The IdP now has a session for you — a cookie in your browser.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.5)

        # a row of doors, all locked
        doors = VGroup()
        labels = ["Email", "Chat", "Drive", "Cloud", "Bank"]
        for nm in labels:
            frame = RoundedRectangle(width=1.35, height=1.75, corner_radius=0.1,
                                     stroke_color=APP_C, stroke_width=2.5,
                                     fill_color=APP_C, fill_opacity=0.05)
            knob = Dot(radius=0.05, color=APP_C).move_to(frame.get_right() + LEFT * 0.2)
            lk = padlock(MUTED, s=0.62, closed=True).move_to(frame.get_center() + UP * 0.15)
            nlab = txt(nm, fs=17, color=INK, weight="BOLD").move_to(frame.get_bottom() + UP * 0.3)
            d = VGroup(frame, knob, lk, nlab)
            d.frame = frame
            d.lock = lk
            doors.add(d)
        doors.arrange(RIGHT, buff=0.42).move_to([0, -0.75, 0])
        self.play(LaggedStart(*[FadeIn(d, shift=UP * 0.1) for d in doors], lag_ratio=0.1, run_time=1.0))
        self.read(0.6)

        # first door: the full dance (quick recap), then it opens
        d0 = doors[0]
        recap = plate(txt("first app → the full dance", fs=15, color=MUTED)).next_to(d0, UP, buff=0.2)
        self.play(FadeIn(recap), run_time=0.4)
        path0 = Line(ck.get_bottom(), d0.get_top())
        self.send(path0, TOKEN_C, rt=0.9)
        self._open_door(d0)
        cap2 = self.say("Open the first app: redirect, sign in, signed token — you know the steps now.")
        self.play(ReplacementTransform(cap, cap2), run_time=0.5)
        self.read(1.3)
        self.play(FadeOut(recap), run_time=0.3)

        # the rest: instant. No password — the IdP session issues a fresh token each time.
        cap3 = self.say("Now every other app just redirects to the IdP — which already knows you.", color=ACCENT)
        self.play(ReplacementTransform(cap2, cap3), run_time=0.5)
        for d in doors[1:]:
            path = Line(ck.get_bottom(), d.get_top())
            self.send(path, TOKEN_C, rt=0.5)
            self._open_door(d, quick=True)
        self.play(Flash(doors, color=GOLD, flash_radius=2.2, line_length=0.28), run_time=0.8)
        cap4 = self.say("No new password. No new prompt. Every door opens instantly. That's Single Sign-On.",
                        color=GOOD, weight="BOLD")
        self.play(ReplacementTransform(cap3, cap4), run_time=0.5)
        self.read(1.6)

        # single logout: kill the IdP session, every door relocks
        cap5 = self.say("And it runs in reverse — one logout at the IdP, and every door relocks.")
        self.play(ReplacementTransform(cap4, cap5), run_time=0.5)
        self.play(ck.animate.set_opacity(0.25), Flash(ck, color=BAD, flash_radius=0.7), run_time=0.5)
        for d in doors:
            self._relock_door(d)
        self.play(LaggedStart(*[Indicate(d.lock, color=BAD, scale_factor=1.1) for d in doors],
                              lag_ratio=0.06, run_time=0.9))
        self.read(1.4)
        self.settle()
        self.wipe()

    def _open_door(self, d, quick=False):
        openlock = padlock(GOOD, s=0.62, closed=False).move_to(d.lock)
        check = make_tick(GOOD, sw=6, scale=1.2).move_to(d.frame.get_center() + UP * 0.15)
        self.play(d.frame.animate.set_stroke(GOOD).set_fill(GOOD, 0.16),
                  Transform(d.lock, openlock), run_time=0.35 if quick else 0.5)
        self.play(FadeIn(check, scale=0.6), run_time=0.2 if quick else 0.35)
        d.check = check

    def _relock_door(self, d):
        closed = padlock(MUTED, s=0.62, closed=True).move_to(d.lock)
        anims = [d.frame.animate.set_stroke(APP_C).set_fill(APP_C, 0.05), Transform(d.lock, closed)]
        if hasattr(d, "check"):
            anims.append(FadeOut(d.check))
        self.play(*anims, run_time=0.3)

    # ====================================================================== #
    # Scene 6 — In the wild: SAML vs OIDC and the trade-off
    # ====================================================================== #
    def scene_world(self):
        header = self.section_header("In the wild: two protocols, one shape", IDP_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        def proto_card(title, sub, bullets, color, cx):
            ttl = txt(title, fs=26, color=color, weight="BOLD")
            st = txt(sub, fs=16, color=MUTED)
            rows = VGroup(*[VGroup(Dot(radius=0.05, color=color),
                                   txt(b, fs=18, color=INK)).arrange(RIGHT, buff=0.18) for b in bullets])
            rows.arrange(DOWN, aligned_edge=LEFT, buff=0.2)
            inner = VGroup(ttl, st, rows).arrange(DOWN, buff=0.2)
            box = RoundedRectangle(width=inner.width + 0.7, height=inner.height + 0.6, corner_radius=0.14,
                                   stroke_color=color, stroke_width=2.5, fill_color=PANEL, fill_opacity=0.5)
            inner.move_to(box)
            return VGroup(box, inner).move_to([cx, 0.85, 0])

        saml = proto_card("SAML 2.0", "the enterprise classic",
                          ["XML assertions", "Signed with XML-DSig", "SSO for corporate apps"],
                          APP_C, -3.4)
        oidc = proto_card("OpenID Connect", "modern, built on OAuth 2.0",
                          ["Signed JWT id_token", "“Sign in with Google”", "Web · mobile · APIs"],
                          IDP_C, 3.4)
        self.play(FadeIn(saml, shift=RIGHT * 0.15), run_time=0.6)
        self.read(1.2)
        self.play(FadeIn(oidc, shift=LEFT * 0.15), run_time=0.6)
        self.read(1.2)
        same = plate(txt("same dance:  redirect → authenticate → signed proof → verify", fs=17, color=ACCENT))
        same.move_to([0, -0.85, 0])
        self.play(FadeIn(same, shift=UP * 0.1), run_time=0.5)
        cap = self.say("Different formats, identical idea — a signed proof from a trusted issuer.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.5)

        # real IdPs
        idps = VGroup(*[chip(n, IDP_C, fs=16, h=0.5) for n in
                        ["Okta", "Microsoft Entra ID", "Google", "Ping", "Auth0"]])
        idps.arrange(RIGHT, buff=0.24)
        if idps.width > 12.6:
            idps.scale_to_fit_width(12.6)
        idps.move_to([0, -1.85, 0])
        ilbl = txt("Identity Providers you've met:", fs=16, color=MUTED).next_to(idps, UP, buff=0.16)
        self.play(FadeIn(ilbl), LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in idps],
                                            lag_ratio=0.1, run_time=1.0))
        self.read(1.3)

        # the honest trade-off, on a takeaway card
        self.play(FadeOut(VGroup(saml, oidc, same, idps, ilbl, cap)), run_time=0.5)
        good = VGroup(
            txt("The upside", fs=24, color=GOOD, weight="BOLD"),
            txt("One hardened login · MFA once · instant company-wide revoke",
                fs=20, color=INK),
        ).arrange(DOWN, buff=0.2)
        warn = VGroup(
            txt("The catch", fs=24, color=BAD, weight="BOLD"),
            txt("The IdP becomes the keys to the kingdom — protect it fiercely",
                fs=20, color=INK),
        ).arrange(DOWN, buff=0.2)
        cards = VGroup(good, warn).arrange(DOWN, buff=0.6).move_to([0, 0.3, 0])
        gb = RoundedRectangle(width=good.width + 0.6, height=good.height + 0.4, corner_radius=0.12,
                              stroke_color=GOOD, stroke_width=2, fill_color=PANEL, fill_opacity=0.4).move_to(good)
        wb = RoundedRectangle(width=warn.width + 0.6, height=warn.height + 0.4, corner_radius=0.12,
                              stroke_color=BAD, stroke_width=2, fill_color=PANEL, fill_opacity=0.4).move_to(warn)
        self.play(FadeIn(VGroup(gb, good), shift=UP * 0.1), run_time=0.6)
        self.read(1.4)
        self.play(FadeIn(VGroup(wb, warn), shift=UP * 0.1), run_time=0.6)
        self.read(1.4)
        tag = txt("so: phishing-resistant MFA (passkeys) on the IdP is non-negotiable.",
                  fs=19, color=ACCENT).next_to(wb, DOWN, buff=0.4)
        if tag.width > 12.6:
            tag.scale_to_fit_width(12.6)
        self.play(FadeIn(tag, shift=UP * 0.1), run_time=0.5)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Closing takeaway (before the outro card)
    # ====================================================================== #
    def scene_recap(self):
        lines = VGroup(
            Text("SSO, in one breath:", font_size=30, color=MUTED),
            Text("Apps never see your password.", font_size=34, color=INK, weight="BOLD"),
            Text("They trust a signed token from one Identity Provider.", font_size=30, color=INK, weight="BOLD"),
            Text("Log in once — every door verifies the signature and opens.",
                 font_size=26, color=ACCENT),
        ).arrange(DOWN, buff=0.36)
        self.play(FadeIn(lines[0]), run_time=0.6)
        self.read(0.5)
        self.play(Write(lines[1]), run_time=1.0)
        self.play(Write(lines[2]), run_time=1.1)
        self.read(1.2)
        self.play(FadeIn(lines[3], shift=UP * 0.12), run_time=0.8)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_problem()
        self.scene_players()
        self.scene_dance()
        self.scene_token()
        self.scene_magic()
        self.scene_world()
        self.scene_recap()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_SSOBase):
    def construct(self):
        self.play_intro()


class Problem(_SSOBase):
    def construct(self):
        self.scene_problem()


class Players(_SSOBase):
    def construct(self):
        self.scene_players()


class Dance(_SSOBase):
    def construct(self):
        self.scene_dance()


class Token(_SSOBase):
    def construct(self):
        self.scene_token()


class Magic(_SSOBase):
    def construct(self):
        self.scene_magic()


class World(_SSOBase):
    def construct(self):
        self.scene_world()


class Recap(_SSOBase):
    def construct(self):
        self.scene_recap()


class Outro(_SSOBase):
    def construct(self):
        self.play_outro()


class HowSSOWorks(_SSOBase):
    """The whole ~4-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    HowSSOWorks().render()

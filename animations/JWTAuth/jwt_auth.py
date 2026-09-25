"""JWT Authentication — a ~4-minute explainer, house-style.

How a *signed token* lets a server trust you without remembering you. We build
the idea from the ground up:

    1. The problem  -- HTTP is stateless; the classic fix (server sessions) puts
                       all the memory back on the server and becomes a bottleneck.
    2. The idea     -- flip it: don't remember, *verify*. Hand the client a
                       tamper-proof, self-describing token.
    3. Anatomy      -- header.payload.signature, the three Base64url parts — and
                       the twist: the payload is readable, NOT encrypted.
    4. The signature-- HMAC with a server secret. Change one byte and it breaks:
                       the tamper attack, live, ending in a REJECTED stamp.
    5. The round trip- login -> issue token -> Authorization: Bearer on every
                       request -> verify locally (no DB) -> and why it scales.
    6. The catch    -- readable payload, revocation, and the alg:none attack;
                       the best-practice card.

Grounded in the JWT / JWS standards:

    JSON Web Token (JWT)      — RFC 7519
    JSON Web Signature (JWS)  — RFC 7515
    HMAC                      — RFC 2104

Everything uses ``Text`` (Pango) rather than ``Tex`` so it renders with no LaTeX
install. The base64 shown is *real* (computed at import from an HS256 sign), so
the tamper mismatch is genuine. Scenes are exposed individually (``Problem``,
``Idea``, ``Anatomy``, ``Sign``, ``Flow``, ``Catch``, ``Recap``, ``Intro``,
``Outro``) and as one continuous film (``JWTAuthFilm``).

Env knobs:
    JWT_QUICK=1   shorten every hold for a fast sanity render
    JWT_DELAY=..  override the reading-hold multiplier (tunes total runtime)
    JWT_READ=..   absolute reading hold after each block of text (default 2.6 s)
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
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


QUICK = os.environ.get("JWT_QUICK") == "1"
# Two separate pacing knobs so nothing feels rushed:
#   DELAY  scales the small pauses *between* animation steps (motion rhythm).
#   READ   is the absolute hold after any block of text lands, so there is always
#          time to actually read it.
# ANIM_SLOW stretches every played animation so transitions aren't abrupt.
DELAY = float(os.environ.get("JWT_DELAY", 0.28 if QUICK else 1.0))
READ = float(os.environ.get("JWT_READ", 0.35 if QUICK else 2.6))
ANIM_SLOW = 1.0 if QUICK else 1.25
END_HOLD = 0.2 if QUICK else 2.2  # settle held on a finished scene before it wipes

# ---- palette -------------------------------------------------------------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
FAINT = "#3A4152"       # gridlines / inert strokes
GOLD = "#FFD166"        # the secret key / accent
GOOD = "#3DD68C"        # verified / OK / trusted
BAD = "#FF5C5C"         # rejected / tampered / danger
ACCENT = "#FFD166"

# JWT's three iconic segments (jwt.io colour language)
HDR = "#FF6B9D"         # header   (pink)
PAY = "#C792EA"         # payload  (violet)
SIG = "#4CC9F0"         # signature (cyan)

CLIENT_C = "#5B8DEF"    # the client / browser (blue)
SERVER_C = "#FF9E4A"    # the server (orange)

# JSON syntax colours (used only inside the decoded cards)
J_KEY = "#82AAFF"
J_STR = "#C3E88D"
J_NUM = "#F78C6C"

MONO = "Menlo"
FONT = "Helvetica Neue"
_BaseText.set_default(font=FONT)

# ---- a real HS256 token (so the base64 & the tamper mismatch are genuine) -- #
_SECRET = b"a-string-secret-at-least-256-bits-long"
_HEADER = {"alg": "HS256", "typ": "JWT"}
_PAYLOAD = {"sub": "1024", "name": "Alice", "role": "user", "exp": 1767225600}
_TAMPERED = {"sub": "1024", "name": "Alice", "role": "admin", "exp": 1767225600}


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _seg(obj) -> str:
    return _b64(json.dumps(obj, separators=(",", ":")).encode())


def _sign(h64: str, p64: str) -> str:
    return _b64(hmac.new(_SECRET, f"{h64}.{p64}".encode(), hashlib.sha256).digest())


H64 = _seg(_HEADER)
P64 = _seg(_PAYLOAD)
SIG64 = _sign(H64, P64)                     # the legitimate signature
P64_BAD = _seg(_TAMPERED)
SIG_RECOMPUTED = _sign(H64, P64_BAD)        # what the server gets from tampered data


def _trunc(s: str, n: int = 20) -> str:
    return s if len(s) <= n else s[:n] + "…"


# ---- small reusable pieces ------------------------------------------------ #
def txt(text, fs=24, color=INK, weight="NORMAL", font=None, slant=None, **extra):
    """``Text`` with optional kwargs, skipping None so Pango never chokes."""
    kw = {"font_size": fs, "color": color, "weight": weight}
    if font:
        kw["font"] = font
    if slant:
        kw["slant"] = slant
    kw.update(extra)
    return Text(text, **kw)


def mono(text, fs=22, color=INK, **kw):
    return txt(text, fs=fs, color=color, font=MONO, **kw)


def chip(text, color, fs=22, w=None, h=0.62, fill=0.14, tcolor=None, weight="NORMAL",
         radius=0.12, font=None):
    """A rounded, tinted box with a centered auto-fitting label. grp[0] is the box."""
    label = txt(text, fs=fs, color=tcolor or INK, weight=weight, font=font)
    width = (label.width + 0.55) if w is None else w
    if label.width > width - 0.3:
        label.scale((width - 0.3) / label.width)
    box = RoundedRectangle(width=width, height=h, corner_radius=radius,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=fill)
    label.move_to(box)
    return VGroup(box, label)


def harrow(start, end, color=MUTED, sw=4, tip=0.22):
    return Arrow(start, end, buff=0.12, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.4, tip_length=tip)


def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])])
    v.set_stroke(color=color, width=sw)
    return v.scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.18, -0.18, 0], [0.18, 0.18, 0])
    b = Line([-0.18, 0.18, 0], [0.18, -0.18, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


# ---- glyphs (built by hand — no emoji, no assets) ------------------------- #
def browser_window(w=2.3, h=1.7, color=CLIENT_C, label="Client"):
    """A little browser window = the client."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.12,
                            stroke_color=color, stroke_width=2.6,
                            fill_color=color, fill_opacity=0.08)
    bar = RoundedRectangle(width=w, height=0.34, corner_radius=0.12,
                           stroke_width=0, fill_color=color, fill_opacity=0.30)
    bar.move_to(body).align_to(body, UP)
    dots = VGroup(*[Dot(radius=0.045, color=BG) for _ in range(3)]).arrange(RIGHT, buff=0.09)
    dots.move_to([body.get_left()[0] + 0.32, bar.get_center()[1], 0])
    glyph = VGroup(body, bar, dots)
    if label:
        lab = txt(label, fs=20, color=color, weight="BOLD").next_to(body, DOWN, buff=0.16)
        glyph.add(lab)
    glyph.body = body
    return glyph


def server_stack(color=SERVER_C, label="Server", w=2.1):
    """A three-unit server rack."""
    units = VGroup()
    for _ in range(3):
        u = RoundedRectangle(width=w, height=0.5, corner_radius=0.08,
                             stroke_color=color, stroke_width=2.2,
                             fill_color=color, fill_opacity=0.12)
        dot = Dot(radius=0.05, color=GOOD).move_to(u.get_left() + RIGHT * 0.28)
        bars = VGroup(*[Line(ORIGIN, RIGHT * 0.45, stroke_width=3, color=color).set_opacity(0.6)
                        for _ in range(2)]).arrange(DOWN, buff=0.09)
        bars.next_to(dot, RIGHT, buff=0.18)
        units.add(VGroup(u, dot, bars))
    units.arrange(DOWN, buff=0.1)
    glyph = VGroup(units)
    if label:
        lab = txt(label, fs=20, color=color, weight="BOLD").next_to(units, DOWN, buff=0.16)
        glyph.add(lab)
    glyph.body = units
    return glyph


def db_cylinder(color=BAD, w=1.5, h=1.5, label="session store"):
    """The classic database cylinder (explicit colours — Ellipse defaults to RED)."""
    yt, yb = h / 2, -h / 2
    ew = 0.42
    body = Rectangle(width=w, height=h, stroke_width=0, fill_color=color, fill_opacity=0.12)
    left = Line([-w / 2, yb, 0], [-w / 2, yt, 0], stroke_color=color, stroke_width=2.4)
    right = Line([w / 2, yb, 0], [w / 2, yt, 0], stroke_color=color, stroke_width=2.4)
    bot = Ellipse(width=w, height=ew, stroke_color=color, stroke_width=2.4,
                  fill_color=BG, fill_opacity=1.0).move_to([0, yb, 0])
    top = Ellipse(width=w, height=ew, stroke_color=color, stroke_width=2.4,
                  fill_color=color, fill_opacity=0.20).move_to([0, yt, 0])
    glyph = VGroup(body, bot, left, right, top)
    if label:
        lab = txt(label, fs=17, color=color).next_to(glyph, DOWN, buff=0.18)
        glyph.add(lab)
    return glyph


def key_icon(color=GOLD, scale=1.0):
    """A little key = the server's secret."""
    ring = Circle(radius=0.16, stroke_color=color, stroke_width=4, fill_opacity=0)
    shaft = Line(ring.get_right(), ring.get_right() + RIGHT * 0.5,
                 stroke_color=color, stroke_width=4)
    t1 = Line(shaft.get_end(), shaft.get_end() + DOWN * 0.16, stroke_color=color, stroke_width=4)
    t2 = Line(shaft.get_end() + LEFT * 0.16, shaft.get_end() + LEFT * 0.16 + DOWN * 0.12,
              stroke_color=color, stroke_width=4)
    return VGroup(ring, shaft, t1, t2).scale(scale)


def padlock(color=GOOD, scale=1.0):
    """A padlock glyph (Arc default is RED — set stroke explicitly)."""
    body = RoundedRectangle(width=0.56, height=0.46, corner_radius=0.08,
                            stroke_color=color, stroke_width=3,
                            fill_color=color, fill_opacity=0.14)
    shackle = Arc(radius=0.17, start_angle=0, angle=PI, stroke_color=color,
                  stroke_width=3.5).next_to(body, UP, buff=-0.02)
    hole = Dot(radius=0.045, color=color).move_to(body).shift(UP * 0.03)
    slit = Line(hole.get_center(), hole.get_center() + DOWN * 0.12,
                stroke_color=color, stroke_width=3)
    return VGroup(shackle, body, hole, slit).scale(scale)


def eye_icon(color=BAD, scale=1.0):
    """An open eye = 'anyone can read this'."""
    outline = VMobject(stroke_color=color, stroke_width=3)
    pts = []
    for a in np.linspace(-1, 1, 24):
        pts.append(np.array([a * 0.4, 0.22 * (1 - a * a), 0]))
    for a in np.linspace(1, -1, 24):
        pts.append(np.array([a * 0.4, -0.22 * (1 - a * a), 0]))
    outline.set_points_as_corners(pts)
    iris = Circle(radius=0.11, stroke_color=color, stroke_width=3, fill_color=color,
                  fill_opacity=0.35)
    pupil = Dot(radius=0.045, color=color)
    return VGroup(outline, iris, pupil).scale(scale)


def clock_icon(color=GOLD, scale=1.0):
    face = Circle(radius=0.24, stroke_color=color, stroke_width=3, fill_opacity=0)
    h1 = Line(ORIGIN, UP * 0.16, stroke_color=color, stroke_width=3)
    h2 = Line(ORIGIN, RIGHT * 0.12, stroke_color=color, stroke_width=3)
    return VGroup(face, h1, h2).scale(scale)


def hmac_box(w=2.5, h=1.15, color=GOLD):
    """The signing/verifying processor."""
    box = RoundedRectangle(width=w, height=h, corner_radius=0.14,
                           stroke_color=color, stroke_width=3,
                           fill_color=color, fill_opacity=0.10)
    name = txt("HMAC", fs=26, color=color, weight="BOLD", font=MONO)
    sub = txt("SHA-256", fs=17, color=MUTED, font=MONO)
    lab = VGroup(name, sub).arrange(DOWN, buff=0.08).move_to(box)
    return VGroup(box, lab)


def seg_box(raw, color, title, w=3.5, h=0.9, fs=17):
    """One raw Base64url segment of the token, tinted by its part colour."""
    box = RoundedRectangle(width=w, height=h, corner_radius=0.1,
                           stroke_color=color, stroke_width=2.5,
                           fill_color=color, fill_opacity=0.16)
    code = mono(_trunc(raw, 24), fs=fs, color=INK)
    if code.width > w - 0.3:
        code.scale((w - 0.3) / code.width)
    code.move_to(box)
    tag = txt(title, fs=15, color=color, weight="BOLD").next_to(box, UP, buff=0.08).align_to(box, LEFT)
    grp = VGroup(box, code, tag)
    grp.box = box
    return grp


def stamp(text="REJECTED", color=BAD):
    """A rubber-stamp badge, rotated for impact."""
    label = txt(text, fs=40, color=color, weight="BOLD")
    box = RoundedRectangle(width=label.width + 0.7, height=label.height + 0.45,
                           corner_radius=0.12, stroke_color=color, stroke_width=6,
                           fill_opacity=0)
    label.move_to(box)
    return VGroup(box, label).rotate(-14 * DEGREES)


# ========================================================================== #
class _JWTBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # ---- timing helpers --------------------------------------------------- #
    def play(self, *anims, **kwargs):
        # stretch every real animation so transitions aren't abrupt, but never
        # scale a bare Wait (that is a reading hold, handled by read()/beat()).
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

    def flash_red(self, opacity=0.22):
        veil = Rectangle(width=config.frame_width, height=config.frame_height,
                         stroke_width=0, fill_color=BAD, fill_opacity=0)
        self.add(veil)
        self.play(veil.animate.set_fill(opacity=opacity), run_time=0.18)
        self.play(veil.animate.set_fill(opacity=0.0), run_time=0.32)
        self.remove(veil)

    def flash_good(self, opacity=0.10):
        veil = Rectangle(width=config.frame_width, height=config.frame_height,
                         stroke_width=0, fill_color=GOOD, fill_opacity=0)
        self.add(veil)
        self.play(veil.animate.set_fill(opacity=opacity), run_time=0.2)
        self.play(veil.animate.set_fill(opacity=0.0), run_time=0.35)
        self.remove(veil)

    def section_header(self, num, label, color=ACCENT):
        t = txt(f"{num} · {label}", fs=32, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=3)
        return VGroup(t, line)

    def bottomcap(self, s, color=INK, fs=23, buff=0.42, **kw):
        t = txt(s, fs=fs, color=color, **kw)
        if t.width > 12.9:
            t.scale_to_fit_width(12.9)
        t.to_edge(DOWN, buff=buff)
        return t

    def set_cap(self, s, color=INK, fs=23):
        """Replace the running bottom caption (transform if one is present)."""
        new = self.bottomcap(s, color=color, fs=fs)
        if getattr(self, "_cap", None) is not None and self._cap in self.mobjects:
            self.play(Transform(self._cap, new), run_time=0.5)
        else:
            self._cap = new
            self.play(FadeIn(new, shift=UP * 0.1), run_time=0.5)
        return self._cap

    def cite(self, s):
        return txt(s, fs=15, color=MUTED, slant=ITALIC).to_edge(DOWN, buff=0.16)

    # ---- house-style intro / outro cards ---------------------------------- #
    def _rule_under(self, header, color=GOLD, pad=1.0, drop=0.45):
        return Line([header.get_left()[0] - pad, header.get_bottom()[1] - drop, 0],
                    [header.get_right()[0] + pad, header.get_bottom()[1] - drop, 0]
                    ).set_stroke(width=3, color=color)

    def play_intro(self):
        header = txt("JWT Authentication", fs=60, color=INK, weight="BOLD")
        header.set(width=min(9.2, header.width))
        line = self._rule_under(header)
        writer = txt("Created by Ptolémé", fs=28, color=CLIENT_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        sub = txt("How a signed token replaces the server's memory", fs=30, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.read(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        src = txt("stateless auth — from login to verify", fs=22, color=MUTED)
        src.next_to(writer, DOWN, buff=0.4)
        self.play(FadeIn(src), run_time=0.8)
        self.read(1.4)
        self.play(FadeOut(VGroup(header, writer, line, src)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = txt("Thank you for watching!", fs=48, color=INK, weight="BOLD")
        line = self._rule_under(header)
        writer = txt("Created by Ptolémé", fs=28, color=CLIENT_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = txt("Don't store the session — sign it.", fs=26, color=ACCENT)
        recap.next_to(writer, DOWN, buff=0.5)
        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap), run_time=0.8)
        self.read(1.6)
        self.play(FadeOut(VGroup(header, line, writer, recap)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 — HTTP has no memory
    # ====================================================================== #
    def scene_problem(self):
        title = txt("HTTP has no memory", fs=46, color=INK, weight="BOLD")
        self.play(Write(title), run_time=1.4)
        self.read(0.8)
        self.play(title.animate.scale(0.60).to_edge(UP, buff=0.42), run_time=0.7)

        client = browser_window(label="Client").move_to([-4.6, 0.5, 0])
        server = server_stack(label="Server").move_to([3.6, 0.5, 0])
        self.play(FadeIn(client, shift=RIGHT * 0.2), FadeIn(server, shift=LEFT * 0.2),
                  run_time=0.8)

        # three requests, each answered with amnesia
        def request_pair(text, y, ans="Who are you?"):
            a1 = harrow([client.body.get_right()[0] + 0.1, y, 0],
                        [server.body.get_left()[0] - 0.1, y, 0], color=CLIENT_C, sw=3)
            q = txt(text, fs=18, color=CLIENT_C).next_to(a1, UP, buff=0.1)
            a2 = harrow([server.body.get_left()[0] - 0.1, y - 0.5, 0],
                        [client.body.get_right()[0] + 0.1, y - 0.5, 0], color=SERVER_C, sw=3)
            r = txt(ans, fs=18, color=SERVER_C).next_to(a2, DOWN, buff=0.1)
            return VGroup(a1, q, a2, r)

        self._cap = None
        p = request_pair("GET /account", 1.15)
        self.play(GrowArrow(p[0]), FadeIn(p[1]), run_time=0.6)
        self.play(GrowArrow(p[2]), FadeIn(p[3]), run_time=0.6)
        self.set_cap("Every request stands alone. The server forgets you the instant it replies.",
                     color=INK)
        self.read(1.3)

        # the classic fix: remember everyone in a session store (kept high enough
        # that its label clears the running bottom caption)
        self.play(FadeOut(p), run_time=0.4)
        store = db_cylinder(color=SERVER_C, w=1.5, h=1.3, label="session store")
        store.move_to([server.body.get_center()[0], -1.55, 0])
        cookie = chip("Cookie: sid=abc123", CLIENT_C, fs=17, h=0.5)
        cookie.move_to([client.body.get_center()[0], -1.55, 0])
        self.play(FadeIn(store, shift=UP * 0.15), FadeIn(cookie, shift=UP * 0.1), run_time=0.7)
        self.set_cap("The old fix: hand out a session id, and store who they are on the server.", color=INK)
        self.read(1.0)

        # a lookup on every single request -> the store fills and every hit costs a query
        rows = VGroup()
        for i, (sid, who) in enumerate([("abc123", "Alice"), ("def456", "Bob"), ("gh789", "Carol")]):
            row = mono(f"{sid}  →  {who}", fs=16, color=INK)
            rows.add(row)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to(store[0])
        rows.scale(min(1.0, (store[0].width - 0.28) / rows.width,
                       (store[0].height - 0.45) / rows.height))
        look = harrow([cookie.get_right()[0] + 0.12, -1.55, 0],
                      [store.get_left()[0] - 0.12, -1.55, 0], color=ACCENT, sw=3)
        look_lbl = txt("look me up…", fs=17, color=ACCENT).next_to(look, UP, buff=0.1)
        self.play(LaggedStart(*[FadeIn(m) for m in rows], lag_ratio=0.2, run_time=0.9))
        self.play(GrowArrow(look), FadeIn(look_lbl), run_time=0.6)
        self.set_cap("Now the server must remember everyone — and look them up on every request.",
                     color=INK)
        self.read(1.3)

        # the punchline: state lives on the server -> bottleneck
        self.play(Indicate(store, color=BAD, scale_factor=1.08), run_time=1.0)
        self.set_cap("State lives on the server. That store becomes the thing that has to scale.",
                     color=BAD)
        self.read(1.5)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — Don't remember, verify
    # ====================================================================== #
    def scene_idea(self):
        title = txt("Don't remember — verify", fs=46, color=INK, weight="BOLD")
        self.play(Write(title), run_time=1.3)
        self.read(0.7)
        self.play(title.animate.scale(0.6).to_edge(UP, buff=0.42), run_time=0.7)

        # left: the stateful world (crossed out). right: the stateless idea.
        client = browser_window(label="Client").scale(0.9).move_to([-4.4, -0.2, 0])
        server = server_stack(label="Server").scale(0.9).move_to([3.9, -0.2, 0])
        self.play(FadeIn(client), FadeIn(server), run_time=0.6)

        # the server signs a badge once and hands it over
        badge = VGroup(
            RoundedRectangle(width=2.5, height=0.66, corner_radius=0.12, stroke_color=GOLD,
                             stroke_width=2.6, fill_color=GOLD, fill_opacity=0.14),
        )
        badge_lbl = mono("eyJ… . eyJ… . S3f…", fs=17, color=INK).move_to(badge)
        seal = padlock(color=GOLD, scale=0.7).next_to(badge, LEFT, buff=0.12)
        token = VGroup(badge, badge_lbl, seal)
        key = key_icon(GOLD, scale=1.1).next_to(server.body, UP, buff=0.3)
        key_lbl = txt("secret key", fs=15, color=GOLD).next_to(key, UP, buff=0.1)

        self.play(FadeIn(key), FadeIn(key_lbl), run_time=0.5)
        token.next_to(server.body, LEFT, buff=0.5).shift(UP * 0.1)
        self.play(FadeIn(token, shift=LEFT * 0.1), run_time=0.6)
        self.set_cap("Sign a tamper-proof token once, and hand it to the client.", color=INK)
        self.read(1.0)

        # move the token to the client — the server keeps nothing but the secret
        self.play(token.animate.next_to(client.body, UP, buff=0.35), run_time=1.1)
        self.set_cap("The client carries it. The server keeps nothing but the key to check it.",
                     color=INK)
        self.read(1.2)

        # each request just shows the badge -> instant verify, no lookup
        a1 = harrow([client.body.get_right()[0] + 0.1, -0.2, 0],
                    [server.body.get_left()[0] - 0.1, -0.2, 0], color=CLIENT_C, sw=3)
        show = txt("here's my token", fs=17, color=CLIENT_C).next_to(a1, UP, buff=0.1)
        check = make_tick(GOOD, sw=7, scale=1.3).next_to(server.body, LEFT, buff=0.2)
        self.play(GrowArrow(a1), FadeIn(show), run_time=0.6)
        self.play(Create(check), run_time=0.5)
        self.flash_good()
        self.set_cap("Every request just proves itself — verify the signature, no database.", color=GOOD)
        self.read(1.2)

        # the two-word contrast — clear the whole diagram so the chips land in the
        # empty centre, well clear of the bottom caption (they must not collide)
        self.play(FadeOut(VGroup(a1, show, check, client, server, token, key, key_lbl)),
                  run_time=0.5)
        stateful = chip("Stateful:  the server remembers you", BAD, fs=22, h=0.72, w=5.9)
        stateless = chip("Stateless:  the token proves itself", GOOD, fs=22, h=0.72, w=5.9)
        cards = VGroup(stateful, stateless).arrange(DOWN, buff=0.45).move_to([0, 0.4, 0])
        self.play(FadeIn(stateful, shift=UP * 0.1), run_time=0.5)
        self.read(0.6)
        self.play(FadeIn(stateless, shift=UP * 0.1), run_time=0.5)
        self.set_cap("That self-proving token is a JWT — a JSON Web Token.", color=ACCENT)
        self.read(1.4)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Anatomy of a JWT
    # ====================================================================== #
    def scene_anatomy(self):
        header = self.section_header("01", "Anatomy of a token", HDR)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # the full token string, three colours joined by dots
        parts = [(H64, HDR), (P64, PAY), (SIG64, SIG)]
        pieces = VGroup()
        for i, (raw, col) in enumerate(parts):
            if i > 0:
                pieces.add(mono(".", fs=30, color=MUTED))
            pieces.add(mono(_trunc(raw, 18), fs=24, color=col))
        pieces.arrange(RIGHT, buff=0.12)
        if pieces.width > 12.6:
            pieces.scale(12.6 / pieces.width)
        pieces.move_to(UP * 2.25)
        self.play(LaggedStart(*[FadeIn(m) for m in pieces], lag_ratio=0.08, run_time=1.2))
        cap = self.bottomcap("One compact string — three Base64url parts, separated by dots.",
                             color=INK)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.6)
        self.read(1.2)

        # split into three rows: raw segment (left) -> decoded card (right)
        rows_y = [1.15, -0.55, -2.35]
        titles = ["HEADER", "PAYLOAD", "SIGNATURE"]
        cols = [HDR, PAY, SIG]
        raws = [H64, P64, SIG64]
        segs = VGroup()
        for y, ttl, col, raw in zip(rows_y, titles, cols, raws):
            s = seg_box(raw, col, ttl, w=3.3, h=0.82).move_to([-4.4, y, 0])
            segs.add(s)

        # decoded contents (JSON / formula)
        def json_card(lines, color, w=None):
            body = VGroup(*[mono(s, fs=18, color=INK) for s in lines])
            body.arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            width = (body.width + 0.6) if w is None else w
            box = RoundedRectangle(width=width, height=body.height + 0.5, corner_radius=0.12,
                                   stroke_color=color, stroke_width=2.4,
                                   fill_color=color, fill_opacity=0.07)
            body.move_to(box)
            return VGroup(box, body)

        hdr_card = json_card(['{ "alg": "HS256",', '  "typ": "JWT" }'], HDR)
        pay_card = json_card(['{ "sub": "1024", "name": "Alice",',
                              '  "role": "user", "exp": 1767225600 }'], PAY)
        sig_lines = VGroup(
            mono("HMAC-SHA256(", fs=18, color=INK),
            mono("  base64url(header) + \".\" +", fs=18, color=INK),
            mono("  base64url(payload),", fs=18, color=INK),
            mono("  secret )", fs=18, color=GOLD),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        sig_box = RoundedRectangle(width=sig_lines.width + 0.6, height=sig_lines.height + 0.5,
                                   corner_radius=0.12, stroke_color=SIG, stroke_width=2.4,
                                   fill_color=SIG, fill_opacity=0.07)
        sig_lines.move_to(sig_box)
        sig_card = VGroup(sig_box, sig_lines)

        cards = [hdr_card, pay_card, sig_card]
        for card, y in zip(cards, rows_y):
            card.move_to([2.7, y, 0]).align_to([0.2, 0, 0], LEFT)

        notes = ["which algorithm signed it", "the claims — who you are, what you can do, when it expires",
                 "proof it hasn't been touched"]

        # reveal the token string collapsing into the three stacked segments
        self.play(FadeOut(cap), run_time=0.3)
        self.play(pieces.animate.set_opacity(0.0), run_time=0.4)
        self.remove(pieces)
        self.play(LaggedStart(*[FadeIn(m, shift=RIGHT * 0.12) for m in segs],
                              lag_ratio=0.15, run_time=1.0))
        self.read(0.7)

        arrows = VGroup()
        for seg, card, note, col in zip(segs, cards, notes, cols):
            ar = harrow([seg.box.get_right()[0] + 0.05, seg.get_center()[1], 0],
                        [card[0].get_left()[0] - 0.05, seg.get_center()[1], 0], color=col, sw=3)
            arrows.add(ar)

        for i, (seg, card, ar, note, col) in enumerate(zip(segs, cards, arrows, notes, cols)):
            self.play(GrowArrow(ar), FadeIn(card, shift=RIGHT * 0.1), run_time=0.6)
            note_t = self.bottomcap(f"{titles[i].title()}:  {note}", color=col)
            if getattr(self, "_cap", None) is not None and self._cap in self.mobjects:
                self.play(Transform(self._cap, note_t), run_time=0.4)
            else:
                self._cap = note_t
                self.play(FadeIn(note_t), run_time=0.4)
            self.read(1.2 if i == 1 else 0.9)

        # the twist: the payload is only Base64 — not encrypted. Drop the other
        # two rows entirely and isolate the payload centre-stage (no crowding).
        self.beat(0.5)
        drop = VGroup(segs[0], segs[2], cards[0], cards[2], arrows[0], arrows[2])
        pay_row = VGroup(segs[1], arrows[1], cards[1])
        self.play(FadeOut(drop), FadeOut(self._cap), run_time=0.6)
        self._cap = None
        self.play(pay_row.animate.move_to(UP * 0.35), run_time=0.7)
        eye = eye_icon(BAD, scale=1.4).next_to(cards[1], UP, buff=0.32)
        warn = txt("Base64, not encrypted — anyone can read it.",
                   fs=24, color=BAD, weight="BOLD")
        warn.next_to(cards[1], DOWN, buff=0.6)
        if warn.width > 12.9:
            warn.scale_to_fit_width(12.9)
        self.play(FadeIn(eye, shift=DOWN * 0.1), Circumscribe(cards[1], color=BAD, run_time=1.4))
        self.play(FadeIn(warn, shift=UP * 0.1), run_time=0.6)
        self.set_cap("So never put a password or a secret in the payload.", color=BAD)
        self.play(FadeIn(self.cite("JWT: RFC 7519  ·  signature (JWS): RFC 7515")), run_time=0.4)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — The signature: trust, then tamper
    # ====================================================================== #
    def scene_sign(self):
        header = self.section_header("02", "The signature", SIG)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        q = txt("How can a server trust a token it doesn't remember?",
                fs=28, color=INK).move_to(UP * 2.4)
        self.play(FadeIn(q, shift=UP * 0.1), run_time=0.7)
        self.read(1.2)

        # --- signing at issue time ---------------------------------------- #
        hp = chip("header . payload", PAY, fs=20, h=0.66, w=3.4)
        hp.move_to([-4.5, 0.4, 0])
        machine = hmac_box().move_to([-0.3, 0.4, 0])
        key = key_icon(GOLD, scale=1.2).next_to(machine, UP, buff=0.35)
        key_lbl = txt("server secret", fs=16, color=GOLD).next_to(key, UP, buff=0.1)
        out_sig = chip(_trunc(SIG64, 12), SIG, fs=19, h=0.66, w=2.9, font=MONO)
        out_sig.move_to([4.6, 0.4, 0])
        a_in = harrow(hp.get_right(), machine[0].get_left(), color=PAY, sw=3)
        a_key = harrow(key.get_bottom(), machine[0].get_top(), color=GOLD, sw=3)
        a_out = harrow(machine[0].get_right(), out_sig.get_left(), color=SIG, sw=3)

        self.play(FadeOut(q), run_time=0.3)
        self.play(FadeIn(hp), FadeIn(machine), FadeIn(key), FadeIn(key_lbl), run_time=0.7)
        self.play(GrowArrow(a_in), GrowArrow(a_key), run_time=0.6)
        self.play(GrowArrow(a_out), FadeIn(out_sig, shift=RIGHT * 0.1), run_time=0.6)
        self.set_cap("At login the server signs header + payload with its secret → the signature.",
                     color=INK)
        self.read(1.4)

        # collapse the signing rig into a compact reference at the top
        rig = VGroup(hp, machine, key, key_lbl, out_sig, a_in, a_key, a_out)
        self.play(rig.animate.scale(0.62).to_edge(UP, buff=1.0), run_time=0.9)
        self.beat(0.5)

        # --- the tamper attack -------------------------------------------- #
        attacker = chip("attacker", BAD, fs=18, h=0.5)
        attacker.move_to([-4.9, -0.7, 0])
        # the payload claim being edited, live
        claim = mono('"role": "user"', fs=26, color=INK).move_to([-1.3, -0.7, 0])
        self.play(FadeIn(attacker, shift=RIGHT * 0.1), FadeIn(claim), run_time=0.6)
        self.set_cap("An attacker grabs the token and edits one claim…", color=BAD)
        self.read(1.0)

        claim2 = mono('"role": "admin"', fs=26, color=BAD, weight="BOLD").move_to(claim)
        self.play(FadeOut(claim, shift=UP * 0.2), FadeIn(claim2, shift=UP * 0.2), run_time=0.6)
        self.play(Wiggle(claim2, scale_value=1.2), run_time=0.8)
        self.set_cap("…flipping their role to admin, and re-encodes the payload.", color=BAD)
        self.read(1.2)

        # server re-derives the signature from the tampered data and compares
        self.play(FadeOut(VGroup(attacker, claim2)), run_time=0.4)
        verify = hmac_box(color=SIG).move_to([-3.6, -1.0, 0])
        vin = chip("header . payload'", BAD, fs=17, h=0.56, w=3.0).next_to(verify, UP, buff=0.4)
        vkey = key_icon(GOLD, scale=0.9).next_to(verify, LEFT, buff=0.3)
        a_v1 = harrow(vin.get_bottom(), verify[0].get_top(), color=BAD, sw=3)
        a_v2 = harrow(vkey.get_right(), verify[0].get_left(), color=GOLD, sw=3)
        self.play(FadeIn(verify), FadeIn(vin), FadeIn(vkey),
                  GrowArrow(a_v1), GrowArrow(a_v2), run_time=0.8)
        self.set_cap("The server recomputes the signature from the data it received…", color=INK)
        self.read(1.1)

        # two signatures compared, side by side
        got = mono(_trunc(SIG_RECOMPUTED, 10), fs=22, color=SIG)
        want = mono(_trunc(SIG64, 10), fs=22, color=INK)
        got_lbl = txt("recomputed", fs=15, color=SIG)
        want_lbl = txt("in the token", fs=15, color=MUTED)
        gcol = VGroup(got_lbl, got).arrange(DOWN, buff=0.1)
        wcol = VGroup(want_lbl, want).arrange(DOWN, buff=0.1)
        neq = txt("≠", fs=44, color=BAD, weight="BOLD")
        compare = VGroup(gcol, neq, wcol).arrange(RIGHT, buff=0.7).move_to([3.4, -1.0, 0])
        a_cmp = harrow(verify[0].get_right(), compare.get_left(), color=SIG, sw=3)
        self.play(GrowArrow(a_cmp), FadeIn(gcol, shift=RIGHT * 0.1), run_time=0.6)
        self.play(FadeIn(wcol), run_time=0.5)
        self.play(Write(neq), run_time=0.5)
        self.set_cap("…and it no longer matches the signature in the token.", color=BAD)
        self.read(1.2)

        # REJECTED — fade the machinery, keep the mismatch as evidence up top,
        # and slam the verdict into the cleared centre (nothing to bury).
        self.play(FadeOut(VGroup(verify, vin, vkey, a_v1, a_v2, a_cmp)),
                  compare.animate.move_to([0, 1.05, 0]), run_time=0.6)
        self.flash_red()
        rej = stamp("REJECTED", BAD).scale(1.5).move_to([0, -1.15, 0])
        self.play(FadeIn(rej, scale=1.8), run_time=0.5)
        self.play(Wiggle(rej, scale_value=1.1), run_time=0.7)
        self.set_cap("Change one byte and the signature breaks — forgery needs the secret.",
                     color=BAD)
        self.play(FadeIn(self.cite("HMAC: RFC 2104  ·  the secret never leaves the server")),
                  run_time=0.4)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — The round trip (sequence) and why it scales
    # ====================================================================== #
    def scene_flow(self):
        header = self.section_header("03", "The round trip", CLIENT_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # two lifelines
        cx, sx = -3.9, 3.9
        top_y, bot_y = 2.4, -3.05
        client = browser_window(label="Client").scale(0.62).move_to([cx, top_y, 0])
        server = server_stack(label="Server").scale(0.62).move_to([sx, top_y, 0])
        cl = DashedLine([cx, top_y - 0.9, 0], [cx, bot_y, 0], dash_length=0.12).set_stroke(CLIENT_C, 2, opacity=0.6)
        sl = DashedLine([sx, top_y - 0.9, 0], [sx, bot_y, 0], dash_length=0.12).set_stroke(SERVER_C, 2, opacity=0.6)
        self.play(FadeIn(client), FadeIn(server), Create(cl), Create(sl), run_time=0.9)

        def message(y, l2r, label, color, note=None, note_side=None):
            x0, x1 = (cx + 0.15, sx - 0.15) if l2r else (sx - 0.15, cx + 0.15)
            ar = harrow([x0, y, 0], [x1, y, 0], color=color, sw=3, tip=0.2)
            lab = mono(label, fs=17, color=color).next_to(ar, UP, buff=0.1)
            if lab.width > 5.4:
                lab.scale(5.4 / lab.width).next_to(ar, UP, buff=0.1)
            grp = VGroup(ar, lab)
            self.play(GrowArrow(ar), FadeIn(lab), run_time=0.55)
            if note:
                nb = txt(note, fs=15, color=MUTED, slant=ITALIC)
                anchor = sx if note_side == "server" else cx
                nb.move_to([anchor, y - 0.32, 0])
                if note_side == "server":
                    nb.shift(LEFT * 0.1)
                self.play(FadeIn(nb), run_time=0.4)
                grp.add(nb)
            return grp

        m1 = message(1.35, True, "POST /login  {user, pw}", CLIENT_C)
        self.read(0.6)
        # server verifies + signs (a self-note near the server lifeline)
        sign_note = VGroup(
            RoundedRectangle(width=2.5, height=0.7, corner_radius=0.1, stroke_color=GOLD,
                             stroke_width=2, fill_color=GOLD, fill_opacity=0.10),
            txt("verify once,\nsign a JWT", fs=15, color=GOLD, line_spacing=0.8),
        )
        sign_note[1].move_to(sign_note[0])
        sign_note.move_to([sx + 0.0, 0.55, 0]).align_to([sx - 1.25, 0, 0], LEFT)
        self.play(FadeIn(sign_note, shift=DOWN * 0.1), run_time=0.5)
        self.read(0.7)
        m2 = message(-0.15, False, "200  { token: eyJ… }", GOOD)
        self.set_cap("Log in once: the server checks your password, then signs and returns a JWT.",
                     color=INK)
        self.read(1.2)

        # the client stores it
        store_chip = chip("stored in the browser", CLIENT_C, fs=15, h=0.46)
        store_chip.move_to([cx, -0.62, 0])
        self.play(FadeIn(store_chip, shift=UP * 0.1), run_time=0.4)
        self.read(0.5)

        m3 = message(-1.25, True, "GET /api/data   Authorization: Bearer eyJ…", GOLD)
        m4y = -2.35
        # server verifies locally, no DB
        v_note = txt("verify signature + exp — no DB", fs=15, color=GOOD, slant=ITALIC)
        v_note.move_to([sx, m4y + 0.42, 0]).align_to([sx + 1.25, 0, 0], RIGHT)
        self.play(FadeIn(v_note), run_time=0.4)
        m4 = message(m4y, False, "200 OK", GOOD)
        self.set_cap("After that, every request carries the token — verified locally, no lookup.",
                     color=GOOD)
        self.read(1.5)

        # --- why it scales: fold the sequence, show the fan-out ------------ #
        self.play(FadeOut(VGroup(m1, m2, m3, m4, sign_note, store_chip, v_note, cl, sl,
                                 client, server)), run_time=0.7)
        lb = chip("load balancer", CLIENT_C, fs=18, h=0.6, w=2.8).move_to([-3.3, 0.8, 0])
        clientb = browser_window(label="Client").scale(0.5).move_to([-5.9, 0.8, 0])
        a_cl = harrow([clientb.body.get_right()[0] + 0.08, 0.8, 0], lb.get_left(),
                      color=CLIENT_C, sw=3)
        servers = VGroup()
        for i, y in enumerate([2.2, 0.8, -0.6]):
            s = server_stack(label="", w=1.7).scale(0.6).move_to([3.2, y, 0])
            k = key_icon(GOLD, scale=0.65).next_to(s.body, RIGHT, buff=0.16)
            tick = make_tick(GOOD, sw=5, scale=0.8).next_to(s.body, LEFT, buff=0.16)
            servers.add(VGroup(s, k, tick))
        fan = VGroup()
        for s in servers:
            fan.add(harrow([lb.get_right()[0] + 0.1, 0.8, 0],
                           [s[2].get_left()[0] - 0.12, s[0].body.get_center()[1], 0],
                           color=MUTED, sw=2.5))
        self.play(FadeIn(clientb), FadeIn(lb), GrowArrow(a_cl), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(m) for m in servers], lag_ratio=0.15, run_time=0.9),
                  LaggedStart(*[GrowArrow(m) for m in fan], lag_ratio=0.15, run_time=0.9))
        # crossed-out shared session store — parked centre, clear of the caption
        deadstore = db_cylinder(color=BAD, label="shared session store").scale(0.62)
        deadstore.move_to([-0.6, -1.9, 0])
        nope = make_cross(BAD, sw=6, scale=1.5).move_to(deadstore[0])
        self.play(FadeIn(deadstore), run_time=0.4)
        self.play(Create(nope), run_time=0.4)
        self.set_cap("Any server can verify with the same secret — no shared store to bottleneck. It scales.",
                     color=ACCENT)
        self.read(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 6 — The catch
    # ====================================================================== #
    def scene_catch(self):
        header = self.section_header("04", "The catch", BAD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.7)

        # a quick alg:none demo, then the best-practice cards
        tok = VGroup(
            chip('{ "alg": "none" }', HDR, fs=18, h=0.6, w=3.2, font=MONO),
            mono(".", fs=26, color=MUTED),
            chip('{ "role": "admin" }', PAY, fs=18, h=0.6, w=3.2, font=MONO),
            mono(".", fs=26, color=MUTED),
            chip("(no signature)", MUTED, fs=17, h=0.6, w=2.6),
        ).arrange(RIGHT, buff=0.14).move_to(UP * 1.9)
        self.play(FadeIn(tok, shift=UP * 0.1), run_time=0.8)
        self.set_cap("An attacker sets alg to \"none\" and drops the signature entirely.", color=BAD)
        self.read(1.2)

        shield = padlock(GOOD, scale=1.6).move_to([0, 0.35, 0])
        naive = txt("naïve server: accepts it", fs=20, color=BAD).move_to([-3.4, -0.55, 0])
        hard = txt("pin the algorithm: rejected", fs=20, color=GOOD).move_to([3.2, -0.55, 0])
        self.play(FadeIn(shield, scale=1.3), run_time=0.6)
        self.play(FadeIn(naive, shift=UP * 0.1), run_time=0.5)
        self.read(0.6)
        self.play(FadeIn(hard, shift=UP * 0.1), run_time=0.5)
        self.play(Indicate(shield, color=GOOD, scale_factor=1.15), run_time=0.8)
        self.read(1.0)

        # three best-practice cards
        self.play(FadeOut(VGroup(tok, shield, naive, hard)),
                  FadeOut(getattr(self, "_cap", VGroup())), run_time=0.5)
        self._cap = None

        def practice(icon, head_s, body_s, color):
            box = RoundedRectangle(width=3.9, height=2.3, corner_radius=0.14,
                                   stroke_color=color, stroke_width=2.4,
                                   fill_color=color, fill_opacity=0.06)
            ic = icon.copy().scale(1.2)
            ic.move_to(box.get_top() + DOWN * 0.5)
            h = txt(head_s, fs=22, color=color, weight="BOLD").next_to(ic, DOWN, buff=0.22)
            b = txt(body_s, fs=17, color=INK, line_spacing=0.85)
            if b.width > box.width - 0.5:
                b.scale_to_fit_width(box.width - 0.5)
            b.next_to(h, DOWN, buff=0.2)
            return VGroup(box, ic, h, b)

        c1 = practice(eye_icon(PAY), "Readable", "It's not encrypted.\nKeep secrets out of it.", PAY)
        c2 = practice(clock_icon(GOLD), "Short-lived", "You can't un-issue it.\nExpire fast, refresh.", GOLD)
        c3 = practice(padlock(SIG), "Pin the alg", "Reject alg:none.\nVerify the way you signed.", SIG)
        cards = VGroup(c1, c2, c3).arrange(RIGHT, buff=0.45).move_to(DOWN * 0.35)
        if cards.width > 13.0:
            cards.scale_to_fit_width(13.0)
        self.play(LaggedStart(*[FadeIn(m, shift=UP * 0.15) for m in cards],
                              lag_ratio=0.25, run_time=1.4))
        cap = self.bottomcap("Powerful, but not magic — respect the trade-offs.", color=INK)
        self.play(FadeIn(cap, shift=UP * 0.1), run_time=0.6)
        self.read(1.7)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Closing takeaway
    # ====================================================================== #
    def scene_recap(self):
        lines = VGroup(
            txt("JWT authentication, in one breath:", fs=30, color=MUTED),
            txt("The server stops remembering you —", fs=32, color=INK, weight="BOLD"),
            txt("and starts verifying a signed token instead.", fs=32, color=INK, weight="BOLD"),
            txt("Stateless, scalable — and only as safe as the secret.", fs=26, color=ACCENT),
        ).arrange(DOWN, buff=0.36)
        self.play(FadeIn(lines[0]), run_time=0.6)
        self.read(0.5)
        self.play(Write(lines[1]), run_time=1.0)
        self.play(Write(lines[2]), run_time=1.0)
        self.read(1.1)
        self.play(FadeIn(lines[3], shift=UP * 0.12), run_time=0.8)
        self.read(1.7)
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_problem()
        self.scene_idea()
        self.scene_anatomy()
        self.scene_sign()
        self.scene_flow()
        self.scene_catch()
        self.scene_recap()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_JWTBase):
    def construct(self):
        self.play_intro()


class Problem(_JWTBase):
    def construct(self):
        self.scene_problem()


class Idea(_JWTBase):
    def construct(self):
        self.scene_idea()


class Anatomy(_JWTBase):
    def construct(self):
        self.scene_anatomy()


class Sign(_JWTBase):
    def construct(self):
        self.scene_sign()


class Flow(_JWTBase):
    def construct(self):
        self.scene_flow()


class Catch(_JWTBase):
    def construct(self):
        self.scene_catch()


class Recap(_JWTBase):
    def construct(self):
        self.scene_recap()


class Outro(_JWTBase):
    def construct(self):
        self.play_outro()


class JWTAuthFilm(_JWTBase):
    """The whole ~4-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    JWTAuthFilm().render()

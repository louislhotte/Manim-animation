"""nginx — a short, house-style explainer.

nginx (say "engine-x") is the process that sits at the edge of most of the web.
It is three things wearing one coat:

    * a **web server** — it serves files and responses,
    * a **reverse proxy** — it stands in front of your app servers, and
    * a **load balancer** — it spreads traffic across a pool of them.

What made it win the internet is *how* it waits. The old model gave every
connection its own thread and let it block on I/O; at ten thousand connections
that model falls over (the "C10K" wall). nginx instead runs a handful of worker
processes, each a single **event loop** juggling thousands of sockets without
ever blocking. That is the whole trick, and the reason it is fast.

We build the story in four beats:

    1. The front door   -- client → nginx → app; what a reverse proxy is
    2. The event loop    -- thread-per-connection vs. one non-blocking loop (C10K)
    3. Load balancing    -- an upstream pool, round-robin, reroute on failure,
                            and the real nginx.conf that declares it
    4. At the edge       -- TLS, static files, caching, compression — before your
                            app does any work — then the takeaway

Everything is drawn with Manim ``Text`` (Pango), never ``Tex`` — no LaTeX
toolchain. Scenes render individually (``FrontDoor``, ``EventLoop``, ``Balance``,
``Edge``, ``Intro``, ``Outro``) or as one film (``HowNginxWorks``).

Env knobs:
    NGINX_QUICK=1   collapse every hold for a fast sanity render
    NGINX_DELAY=..  reading-rhythm multiplier for small inter-step pauses
    NGINX_READ=..   absolute hold after a caption lands (seconds) — reading time
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

# --- crisp text (shared house fix) ----------------------------------------- #
# Manim's ``Text`` mangles letter/word spacing below ~20 pt. Render every glyph
# at a large base size and scale the mobject *down* — spacing stays crisp.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("NGINX_QUICK") == "1"
DELAY = float(os.environ.get("NGINX_DELAY", 0.28 if QUICK else 1.0))
READ = float(os.environ.get("NGINX_READ", 0.32 if QUICK else 2.3))
ANIM_SLOW = 1.0 if QUICK else 1.25
END_HOLD = 0.2 if QUICK else 2.0  # settle held on a finished scene before it wipes

# ---- palette (dark house style, shared across the series) ----------------- #
BG = "#0E1117"          # dark slate background
PANEL = "#151A23"       # panel fill
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
FAINT = "#2A3140"       # gridlines / faint wires
GOLD = "#FFD166"        # accent / rules

NGINX = "#57D98A"       # nginx itself — the hero green (proxy at the edge)
CLIENT_C = "#5B8DEF"    # clients / browsers (blue)
SERVER_C = "#C792EA"    # backend app servers (violet)
WARN = "#FF8C42"        # load / blocking / the old thread model (orange)
BAD = "#FF5C5C"         # a server that's down / memory exhausted (red)
GOOD = "#3DD68C"        # served / healthy (green)
ACCENT = GOLD

MONO = "Menlo"          # code / addresses
FONT = "Helvetica Neue"
_BaseText.set_default(font=FONT)

# ---- code-panel syntax colours (nginx.conf) ------------------------------- #
CODE_FS = 18
PLAIN = "#D6DEEB"       # default code text
COMMENT = "#5F6B7E"     # comments (grey-blue)
KW = NGINX              # context blocks: http / upstream / server / location
DIRECTIVE = "#82AAFF"   # directives: worker_processes / listen / proxy_pass ...
VALUE = GOLD            # values: 443 / ssl / auto
URLC = "#C3E88D"        # the upstream url: http://app

NG_T2C = {
    "http": KW, "upstream": KW, "location": KW,
    "worker_processes": DIRECTIVE, "least_conn": DIRECTIVE,
    "listen": DIRECTIVE, "proxy_pass": DIRECTIVE, "server": KW,
    "auto": VALUE, "ssl": VALUE, "443": VALUE,
    "http://app": URLC,
}


def _safe_t2c(s, table):
    """Per-line text→colour map, pruned so no key overlaps another.

    Manim's ``t2c`` raises on overlapping colour ranges — even for the same
    colour (e.g. ``http`` sitting inside ``http://app``). Keep only keys present
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
    g = VGroup(box, label)
    g.box = box
    g.label = label
    return g


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


def arr(a, b, color=MUTED, sw=4, buff=0.12, tip=0.2):
    return Arrow(a, b, buff=buff, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.35, tip_length=tip)


def wire(a, b, color=MUTED, sw=2.0, op=0.75):
    """A thin connecting line that sits behind the glyphs."""
    ln = Line(a, b, stroke_color=color, stroke_width=sw, stroke_opacity=op)
    ln.set_z_index(-1)
    return ln


def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])])
    return v.set_stroke(color=color, width=sw).scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.18, -0.18, 0], [0.18, 0.18, 0])
    b = Line([-0.18, 0.18, 0], [0.18, -0.18, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


# ---- glyphs (all hand-drawn Manim mobjects, no assets) -------------------- #
def nginx_emblem(color=NGINX, s=1.0):
    """The nginx mark: an 'N' zig-zag inside a soft ring."""
    ring = Circle(radius=0.34 * s, stroke_color=color, stroke_width=4,
                  fill_color=color, fill_opacity=0.12)
    n = VMobject().set_points_as_corners([
        np.array([-0.13, -0.17, 0]), np.array([-0.13, 0.17, 0]),
        np.array([0.13, -0.17, 0]), np.array([0.13, 0.17, 0]),
    ]).scale(s)
    n.set_stroke(color=color, width=4)
    return VGroup(ring, n)


def nginx_box(w=2.5, h=1.55, sub="reverse proxy"):
    """The hero: nginx as a titled green card with its emblem and a subtitle."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.15,
                            stroke_color=NGINX, stroke_width=3.2,
                            fill_color=NGINX, fill_opacity=0.10)
    mark = nginx_emblem(NGINX, s=0.82)
    name = txt("nginx", fs=27, color=INK, weight="BOLD")
    head = VGroup(mark, name).arrange(RIGHT, buff=0.18)
    subt = txt(sub, fs=17, color=NGINX)
    inner = VGroup(head, subt).arrange(DOWN, buff=0.13).move_to(body)
    g = VGroup(body, inner)
    g.body = body
    g.subt = subt
    return g


def browser(label="GET /", color=CLIENT_C, w=1.95, h=1.35):
    """A client: a little browser window with a title bar and a request line."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.1,
                            stroke_color=color, stroke_width=2.6,
                            fill_color=color, fill_opacity=0.07)
    bar = RoundedRectangle(width=w, height=0.34, corner_radius=0.1, stroke_width=0,
                           fill_color=color, fill_opacity=0.2)
    bar.align_to(body, UP)
    dots = VGroup(*[Dot(radius=0.035, color=color) for _ in range(3)]).arrange(RIGHT, buff=0.08)
    dots.move_to([body.get_left()[0] + 0.28, bar.get_center()[1], 0])
    lbl = mono(label, fs=18, color=INK)
    if lbl.width > w - 0.3:
        lbl.scale((w - 0.3) / lbl.width)
    lbl.move_to([body.get_center()[0], body.get_center()[1] - 0.12, 0])
    g = VGroup(body, bar, dots, lbl)
    g.body = body
    g.label = lbl
    return g


def server_box(title="app", color=SERVER_C, w=2.15, h=1.02, healthy=True):
    """A backend app server: a titled box with a small health LED."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.12,
                            stroke_color=color, stroke_width=2.8,
                            fill_color=color, fill_opacity=0.08)
    bar = RoundedRectangle(width=w, height=0.34, corner_radius=0.12, stroke_width=0,
                           fill_color=color, fill_opacity=0.16)
    bar.align_to(body, UP)
    led = Dot(radius=0.06, color=GOOD if healthy else BAD)
    led.move_to([body.get_left()[0] + 0.24, bar.get_center()[1], 0])
    ttl = txt(title, fs=17, color=INK, weight="BOLD").next_to(led, RIGHT, buff=0.14)
    # two faint "rack" bars to read as a machine
    racks = VGroup(*[RoundedRectangle(width=w - 0.5, height=0.12, corner_radius=0.06,
                                      stroke_width=0, fill_color=color, fill_opacity=0.18)
                     for _ in range(2)]).arrange(DOWN, buff=0.12)
    racks.move_to([body.get_center()[0], body.get_center()[1] - 0.18, 0])
    g = VGroup(body, bar, led, ttl, racks)
    g.body = body
    g.led = led
    return g


def padlock(color=NGINX, s=1.0, closed=True):
    """A padlock: body, shackle (an Arc — defaults RED, so pass color), keyhole."""
    body = RoundedRectangle(width=0.52 * s, height=0.44 * s, corner_radius=0.08 * s,
                            stroke_color=color, stroke_width=3,
                            fill_color=color, fill_opacity=0.18)
    shackle = Arc(radius=0.16 * s, start_angle=0, angle=PI, color=color, stroke_width=3.2)
    kh = VGroup(
        Dot(radius=0.035 * s, color=color),
        Line([0, 0, 0], [0, -0.1 * s, 0], color=color, stroke_width=2.4),
    ).arrange(DOWN, buff=0.0).move_to(body)
    shackle.next_to(body, UP, buff=-0.03 * s)
    if not closed:
        shackle.shift(UP * 0.09 * s + LEFT * 0.08 * s)
        shackle.rotate(-0.5, about_point=shackle.get_bottom() + RIGHT * 0.16 * s)
    g = VGroup(body, shackle, kh)
    g.body = body
    return g


def stamp(text, color):
    """A rotated rubber-stamp verdict."""
    t = txt(text, fs=40, color=color, weight="BOLD")
    box = RoundedRectangle(width=t.width + 0.55, height=t.height + 0.4, corner_radius=0.14,
                           stroke_color=color, stroke_width=6, fill_opacity=0)
    t.move_to(box)
    return VGroup(box, t).rotate(-0.18)


def meter_track(w=2.3, h=0.24, color=MUTED):
    return RoundedRectangle(width=w, height=h, corner_radius=h / 2,
                            stroke_color=color, stroke_width=1.6,
                            fill_color=BG, fill_opacity=0.4)


def meter_fill(track, frac, color=WARN):
    """A left-anchored fill sized to `track`. Rebuild + Transform to animate.

    (The load-balancer bug: a fill placed with only ``align_to(LEFT)`` floats at
    y=0 — set both, anchoring the left edge to the track's left point.)
    """
    frac = max(0.0, min(1.0, frac))
    w = track.width * frac
    h = track.height * 0.68
    fill = RoundedRectangle(width=max(w, h), height=h, corner_radius=h / 2,
                            stroke_width=0, fill_color=color, fill_opacity=0.95)
    fill.move_to(track.get_left(), aligned_edge=LEFT)
    if frac <= 0.001:
        fill.set_opacity(0)
    return fill


# ========================================================================== #
class _NginxBase(Scene):
    def setup(self):
        self.camera.background_color = BG
        self.hlrect = None

    # ---- timing helpers --------------------------------------------------- #
    def play(self, *anims, **kwargs):
        # stretch real animations so transitions aren't abrupt, but never scale a
        # bare Wait (a reading hold, handled by read()/beat()).
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
        self.hlrect = None

    # ---- text helpers ----------------------------------------------------- #
    def section_header(self, label, color):
        t = txt(label, fs=33, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(t.get_left(), t.get_right()).next_to(t, DOWN, buff=0.12)
        line.set_stroke(color=color, width=4)
        return VGroup(t, line)

    def say(self, text, color=INK, fs=23, y=-3.42, weight="NORMAL"):
        """A bottom caption, width-clamped so it never runs off-screen."""
        m = txt(text, fs=fs, color=color, weight=weight)
        if m.width > 12.7:
            m.scale_to_fit_width(12.7)
        m.move_to([0, y, 0])
        return m

    def takeaway(self, line1, line2, c2=GOLD):
        """Fade to a clean frame, land a two-line takeaway centred."""
        k1 = Text(line1, font_size=36, color=INK, weight="BOLD")
        k2 = Text(line2, font_size=27, color=c2, weight="BOLD")
        if k1.width > 12.8:
            k1.scale_to_fit_width(12.8)
        if k2.width > 12.8:
            k2.scale_to_fit_width(12.8)
        VGroup(k1, k2).arrange(DOWN, buff=0.36).move_to(ORIGIN)
        self.play(FadeIn(k1, shift=UP * 0.1), run_time=0.7)
        self.play(FadeIn(k2, shift=UP * 0.1), run_time=0.6)
        self.read(1.4)

    # ---- code panel (adapted from the house code-panel helper) ------------ #
    def code_panel(self, spec, table=NG_T2C, title="nginx.conf", fs=CODE_FS,
                   indent_unit=0.44, line_buff=0.15, target_h=5.9, target_w=6.6):
        """spec: list of (indent, text); "" is a blank line. Returns (panel, lines)."""
        lines = []
        for indent, s in spec:
            if s == "":
                m = Rectangle(width=0.02, height=0.26, fill_opacity=0, stroke_opacity=0)
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
        # centre the bar on the panel first — the code VGroup is indent-shifted, so
        # bg is re-centred on it; align_to(UP) alone would leave the bar off in x.
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

    # ---- house-style intro / outro cards ---------------------------------- #
    def play_intro(self):
        header = Text("nginx", font_size=76, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        mark = nginx_emblem(GOLD, s=1.0).move_to(line.get_right() + RIGHT * 0.14 + UP * 0.32)
        writer = Text("Created by Ptolémé", font_size=28, color=CLIENT_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.5)
        self.play(FadeIn(mark, shift=DOWN * 0.15), run_time=0.6)
        self.read(0.7)
        sub = Text("The web server that became the internet's front door.",
                   font_size=29, color=MUTED)
        if sub.width > 12.6:
            sub.scale_to_fit_width(12.6)
        sub.move_to(header)
        self.play(Transform(header, sub), FadeOut(mark), run_time=1.0)
        self.read(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        src = Text("reverse proxy · load balancer · web server  ·  System Design",
                   font_size=22, color=MUTED)
        if src.width > 12.0:
            src.scale_to_fit_width(12.0)
        src.next_to(writer, DOWN, buff=0.4)
        self.play(FadeIn(src), run_time=0.8)
        self.read(1.3)
        self.play(FadeOut(VGroup(header, writer, line, src)), run_time=1.0)
        self.card_wait(0.3)

    def play_outro(self):
        self.card_wait(0.5)
        header = Text("Thank you for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        writer = Text("Created by Ptolémé", font_size=28, color=CLIENT_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = Text("One event loop, at the edge of the web.",
                     font_size=26, color=ACCENT)
        recap.next_to(writer, DOWN, buff=0.5)
        self.play(Write(header), Create(line), run_time=1.5)
        self.read(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap), run_time=0.8)
        self.read(1.6)
        self.play(FadeOut(VGroup(header, line, writer, recap)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # helper: send a request dot along a path a→b, return it (added to scene)
    # ====================================================================== #
    def send_dot(self, a, b, color=CLIENT_C, r=0.08, rt=0.6):
        d = Dot(a, radius=r, color=color)
        self.add(d)
        self.play(d.animate.move_to(b), run_time=rt, rate_func=rate_functions.ease_in_out_sine)
        return d

    # ====================================================================== #
    # Scene 1 — The front door: client → nginx → app (what a reverse proxy is)
    # ====================================================================== #
    def scene_frontdoor(self):
        title = Text("nginx", font_size=58, color=NGINX, weight="BOLD")
        sub = txt("say “engine-x” — it runs a huge share of the web.", fs=25, color=MUTED)
        sub.next_to(title, DOWN, buff=0.32)
        self.play(Write(title), run_time=1.1)
        self.play(FadeIn(sub, shift=UP * 0.1), run_time=0.7)
        self.read(1.2)
        self.play(FadeOut(sub), FadeOut(title), run_time=0.6)

        header = self.section_header("The front door", NGINX)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        # direct: browser -> app server
        client = browser("GET /", CLIENT_C).move_to([-4.7, 0.4, 0])
        app = server_box("app server", SERVER_C, w=2.4).move_to([4.6, 0.4, 0])
        c_lbl = txt("client", fs=18, color=CLIENT_C).next_to(client, DOWN, buff=0.22)
        self.play(FadeIn(client, shift=RIGHT * 0.15), FadeIn(c_lbl), run_time=0.6)
        self.play(FadeIn(app, shift=LEFT * 0.15), run_time=0.6)
        direct = arr(client.get_right(), app.get_left(), color=MUTED, sw=4)
        self.play(GrowArrow(direct), run_time=0.6)
        cap = self.say("Your browser asks a web server for a page.")
        self.play(FadeIn(cap), run_time=0.5)
        d = self.send_dot(client.get_right() + RIGHT * 0.1, app.get_left() + LEFT * 0.1, rt=0.7)
        self.play(FadeOut(d), run_time=0.2)
        self.read(1.2)

        # the strain: one exposed server does everything
        chips = VGroup(
            chip("TLS", WARN, fs=15, h=0.44),
            chip("static files", WARN, fs=15, h=0.44),
            chip("app logic", WARN, fs=15, h=0.44),
        ).arrange(RIGHT, buff=0.18).next_to(app, UP, buff=0.3)
        flood = VGroup(*[Dot(radius=0.06, color=WARN) for _ in range(9)])
        flood.arrange_in_grid(rows=3, cols=3, buff=0.14).next_to(client, LEFT, buff=0.55)
        self.play(LaggedStart(*[FadeIn(x, shift=RIGHT * 0.15) for x in flood],
                              lag_ratio=0.06, run_time=0.9),
                  FadeIn(chips, shift=DOWN * 0.1))
        self.play(app.body.animate.set_stroke(WARN, 4.0),
                  Flash(app, color=WARN, flash_radius=1.3), run_time=0.6)
        cap2 = self.say("One server, doing everything, exposed straight to the internet.",
                        color=WARN)
        self.play(ReplacementTransform(cap, cap2), run_time=0.5)
        self.read(1.4)

        # slide nginx into the middle
        self.play(FadeOut(flood), FadeOut(chips),
                  app.body.animate.set_stroke(SERVER_C, 2.8), run_time=0.5)
        ng = nginx_box(w=2.5, sub="reverse proxy").move_to([0.0, 0.4, 0])
        self.play(FadeOut(direct), run_time=0.3)
        self.play(client.animate.move_to([-5.0, 0.4, 0]),
                  app.animate.move_to([5.0, 0.4, 0]),
                  c_lbl.animate.move_to([-5.0, -0.55, 0]), run_time=0.5)
        self.play(GrowFromCenter(ng), run_time=0.7)
        a1 = arr(client.get_right(), ng.get_left(), color=CLIENT_C, sw=4)
        a2 = arr(ng.get_right(), app.get_left(), color=NGINX, sw=4)
        self.play(GrowArrow(a1), GrowArrow(a2), run_time=0.6)
        cap3 = self.say("Put nginx in front. Every request hits it first.", color=NGINX)
        self.play(ReplacementTransform(cap2, cap3), run_time=0.5)
        # a request flows through
        d1 = self.send_dot(client.get_right() + RIGHT * 0.1, ng.get_left() + LEFT * 0.1,
                           color=CLIENT_C, rt=0.55)
        self.play(d1.animate.move_to(app.get_left() + LEFT * 0.1).set_color(NGINX),
                  run_time=0.55, rate_func=rate_functions.ease_in_out_sine)
        self.play(FadeOut(d1), run_time=0.2)
        self.read(1.2)

        # define reverse proxy
        note = plate(txt("The client thinks it's talking to your site — it's talking to nginx.",
                         fs=21, color=INK, weight="BOLD"))
        note.move_to([0, 2.35, 0])
        self.play(FadeIn(note, shift=DOWN * 0.1), run_time=0.5)
        cap4 = self.say("That's a reverse proxy: one public door in front of your servers.",
                        color=ACCENT)
        self.play(ReplacementTransform(cap3, cap4), run_time=0.5)
        self.read(1.6)

        self.play(FadeOut(Group(client, c_lbl, app, ng, a1, a2, note, header, cap4)),
                  run_time=0.6)
        self.takeaway("nginx is the front door.",
                      "Every request enters through it — before your app sees a thing.")
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — The event loop: thread-per-connection vs one non-blocking loop
    # ====================================================================== #
    def scene_eventloop(self):
        header = self.section_header("Why it's fast", NGINX)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        q = txt("A server has to hold thousands of connections at once. How?",
                fs=25, color=INK)
        q.move_to([0, 2.5, 0])
        self.play(FadeIn(q, shift=DOWN * 0.1), run_time=0.6)
        self.read(1.2)

        divider = DashedLine([0, 1.95, 0], [0, -2.55, 0], color=FAINT, stroke_width=2)
        self.play(Create(divider), run_time=0.4)

        # ---------- LEFT: thread per connection ---------------------------- #
        lhead = pill("thread per connection", WARN, fs=16).move_to([-3.6, 1.6, 0])
        lbox = RoundedRectangle(width=3.0, height=3.0, corner_radius=0.14,
                                stroke_color=WARN, stroke_width=2.2,
                                fill_color=WARN, fill_opacity=0.04).move_to([-3.6, -0.35, 0])
        self.play(FadeIn(lhead), Create(lbox), run_time=0.6)

        l_track = meter_track(w=2.3, color=WARN).move_to([-3.6, -2.05, 0])
        l_ram = txt("RAM", fs=15, color=MUTED).next_to(l_track, LEFT, buff=0.18)
        l_fill = meter_fill(l_track, 0.12, WARN)
        self.play(FadeIn(l_track), FadeIn(l_ram), FadeIn(l_fill), run_time=0.4)

        # each connection spawns its own (mostly blocked) thread
        thread_ys = [0.78, 0.30, -0.18, -0.66]
        threads = VGroup()
        for i, ty in enumerate(thread_ys):
            conn = Dot(radius=0.06, color=CLIENT_C).move_to([-4.95, ty, 0])
            tb = RoundedRectangle(width=1.7, height=0.32, corner_radius=0.09,
                                  stroke_color=WARN, stroke_width=2,
                                  fill_color=WARN, fill_opacity=0.16)
            tb.move_to([-3.35, ty, 0])
            tl = txt("blocked", fs=13, color=WARN).move_to(tb)
            w = wire(conn.get_center(), tb.get_left(), color=CLIENT_C, sw=1.6, op=0.6)
            row = VGroup(w, conn, tb, tl)
            threads.add(row)
            self.play(FadeIn(conn, shift=RIGHT * 0.1), Create(w),
                      GrowFromCenter(VGroup(tb, tl)), run_time=0.32)
            new_fill = meter_fill(l_track, 0.12 + 0.20 * (i + 1), WARN)
            self.play(Transform(l_fill, new_fill), run_time=0.28)
        cap = self.say("The old model: one thread per connection — most just sit, blocked on I/O.",
                       color=WARN)
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.3)

        # 10k connections -> memory exhausted
        c10k = txt("10,000 connections?", fs=22, color=INK, weight="BOLD").move_to([-3.6, -1.35, 0])
        self.play(FadeIn(c10k, shift=UP * 0.1), run_time=0.5)
        full_fill = meter_fill(l_track, 1.0, BAD)
        self.play(Transform(l_fill, full_fill),
                  lbox.animate.set_stroke(BAD, 3.2),
                  Flash(lbox, color=BAD, flash_radius=1.7), run_time=0.7)
        xmark = make_cross(BAD, sw=7, scale=1.1).move_to(l_track)
        self.play(FadeIn(xmark), run_time=0.3)
        cap2 = self.say("10,000 threads, 10,000 stacks — the machine runs out of memory.",
                        color=BAD, weight="BOLD")
        self.play(ReplacementTransform(cap, cap2), run_time=0.5)
        self.read(1.5)

        # ---------- RIGHT: one event loop --------------------------------- #
        rhead = pill("nginx · event loop", NGINX, fs=16).move_to([3.6, 1.6, 0])
        rbox = RoundedRectangle(width=3.0, height=3.0, corner_radius=0.14,
                                stroke_color=NGINX, stroke_width=2.2,
                                fill_color=NGINX, fill_opacity=0.04).move_to([3.6, -0.35, 0])
        self.play(FadeIn(rhead), Create(rbox), run_time=0.6)

        r_track = meter_track(w=2.3, color=NGINX).move_to([3.6, -2.05, 0])
        r_ram = txt("RAM", fs=15, color=MUTED).next_to(r_track, LEFT, buff=0.18)
        r_fill = meter_fill(r_track, 0.14, NGINX)
        self.play(FadeIn(r_track), FadeIn(r_ram), FadeIn(r_fill), run_time=0.4)

        # loop sits in the upper 2/3 of the box so the ring of sockets never
        # reaches the "10,000 connections?" label below it (box y in [-1.85, 1.15]).
        loop_c = np.array([3.6, 0.12, 0])
        ring = Circle(radius=0.62, stroke_color=NGINX, stroke_width=4,
                      fill_color=NGINX, fill_opacity=0.06).move_to(loop_c)
        worker = txt("1 worker", fs=15, color=NGINX, weight="BOLD").move_to(loop_c)
        conns = VGroup()
        for k in range(8):
            a = k * TAU / 8 + PI / 2
            p = loop_c + 0.84 * np.array([np.cos(a), np.sin(a), 0])
            conns.add(Dot(p, radius=0.055, color=CLIENT_C))
        self.play(Create(ring), FadeIn(worker),
                  LaggedStart(*[FadeIn(d, scale=0.6) for d in conns],
                              lag_ratio=0.05, run_time=0.7))
        cap3 = self.say("nginx runs one loop that checks every socket and only touches the ready ones.",
                        color=NGINX)
        self.play(ReplacementTransform(cap2, cap3), run_time=0.5)

        # the loop sweeps, servicing ready sockets; RAM barely moves.
        # a scanning arc on the rim (not a radial line — that would cross the label).
        pointer = Arc(radius=0.62, start_angle=PI / 2, angle=-0.7, arc_center=loop_c,
                      stroke_color=GOLD, stroke_width=6)
        self.add(pointer)
        self.play(Rotate(pointer, angle=-TAU, about_point=loop_c, run_time=3.0),
                  LaggedStart(*[Indicate(d, color=GOOD, scale_factor=1.5) for d in conns],
                              lag_ratio=0.11, run_time=3.0),
                  Transform(r_fill, meter_fill(r_track, 0.22, NGINX), run_time=3.0))
        self.read(1.0)

        # 10k connections -> loop just gets busier, RAM flat
        c10k_r = txt("10,000 connections?", fs=22, color=INK, weight="BOLD").move_to([3.6, -1.35, 0])
        self.play(FadeIn(c10k_r, shift=UP * 0.1), run_time=0.5)
        # a dense cloud of sockets hugging the ring — contained to an annulus that
        # stays inside the box and clear of the label (seeded for a stable render).
        np.random.seed(7)
        swarm = VGroup()
        for k in range(20):
            a = np.random.uniform(0, TAU)
            rr = np.random.uniform(0.66, 0.86)
            swarm.add(Dot(loop_c + rr * np.array([np.cos(a), np.sin(a), 0]),
                          radius=0.045, color=CLIENT_C))
        self.play(LaggedStart(*[FadeIn(d, scale=0.5) for d in swarm], lag_ratio=0.02, run_time=1.0),
                  Transform(r_fill, meter_fill(r_track, 0.32, NGINX), run_time=1.0),
                  Rotate(pointer, angle=-TAU, about_point=loop_c, run_time=1.0))
        tick = make_tick(GOOD, sw=7, scale=1.2).next_to(r_track, RIGHT, buff=0.2)
        self.play(FadeIn(tick), run_time=0.3)
        cap4 = self.say("Same handful of workers. RAM barely moves. This is how nginx beat C10K.",
                        color=ACCENT)
        self.play(ReplacementTransform(cap3, cap4), run_time=0.5)
        self.read(1.6)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.takeaway("Thousands of connections. A handful of processes.",
                      "Event-driven, non-blocking I/O — never a thread per request.")
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Load balancing: an upstream pool + the real nginx.conf
    # ====================================================================== #
    def scene_balance(self):
        header = self.section_header("Load balancing", NGINX)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        ng = nginx_box(w=2.4, sub="load balancer").move_to([-3.7, 0.35, 0])
        client = browser("GET /", CLIENT_C, w=1.5, h=1.05).move_to([-6.05, 0.35, 0])
        ys = [1.85, 0.35, -1.15]
        servers = VGroup(*[server_box(f"app {i+1}", SERVER_C, w=2.05).move_to([4.35, y, 0])
                           for i, y in enumerate(ys)])
        wires = VGroup(*[wire(ng.get_right(), s.get_left(), color=NGINX, sw=2.2, op=0.7)
                         for s in servers])

        self.play(FadeIn(client, shift=RIGHT * 0.1), GrowFromCenter(ng), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(s, shift=LEFT * 0.12) for s in servers],
                              lag_ratio=0.12, run_time=0.8))
        self.play(LaggedStart(*[Create(w) for w in wires], lag_ratio=0.1, run_time=0.7))
        a_in = arr(client.get_right(), ng.get_left(), color=CLIENT_C, sw=3.5)
        self.play(GrowArrow(a_in), run_time=0.4)
        pool = pill("upstream pool", SERVER_C, fs=15).move_to([4.35, 3.0, 0])
        self.play(FadeIn(pool), run_time=0.4)
        cap = self.say("Behind nginx: a pool of identical app servers.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.2)

        # round-robin: send requests to app1, app2, app3, app1 ...
        order = [0, 1, 2, 0, 1]
        cap2 = self.say("Each request goes to the next server in turn — round robin.", color=NGINX)
        self.play(ReplacementTransform(cap, cap2), run_time=0.5)
        for i, si in enumerate(order):
            d = Dot(ng.get_right() + RIGHT * 0.05, radius=0.075, color=NGINX)
            self.add(d)
            self.play(d.animate.move_to(servers[si].get_left() + LEFT * 0.08),
                      run_time=0.42, rate_func=rate_functions.ease_in_out_sine)
            self.play(Indicate(servers[si].body, color=GOOD, scale_factor=1.05),
                      FadeOut(d), run_time=0.28)
        self.read(1.0)

        # app 2 dies -> reroute
        dead = servers[1]
        self.play(dead.led.animate.set_color(BAD),
                  dead.body.animate.set_stroke(BAD, 3.0).set_fill(BAD, 0.05),
                  wires[1].animate.set_stroke(BAD, 2.0, opacity=0.4),
                  run_time=0.5)
        xr = make_cross(BAD, sw=6, scale=0.9).move_to(dead.get_center())
        self.play(FadeIn(xr), Flash(dead, color=BAD, flash_radius=1.1), run_time=0.5)
        cap3 = self.say("A backend goes down…", color=BAD, weight="BOLD")
        self.play(ReplacementTransform(cap2, cap3), run_time=0.5)
        self.read(0.8)

        # the request meant for app2 reroutes to app3
        d = Dot(ng.get_right() + RIGHT * 0.05, radius=0.075, color=NGINX)
        self.add(d)
        self.play(d.animate.move_to(dead.get_left() + LEFT * 0.35), run_time=0.4)
        bounce = curved_reroute = ArcBetweenPoints(
            dead.get_left() + LEFT * 0.35, servers[2].get_left() + LEFT * 0.08,
            angle=-1.1, stroke_opacity=0)
        self.play(MoveAlongPath(d, bounce), run_time=0.55,
                  rate_func=rate_functions.ease_in_out_sine)
        self.play(Indicate(servers[2].body, color=GOOD, scale_factor=1.06),
                  FadeOut(d), run_time=0.3)
        cap4 = self.say("…nginx skips it and routes to a healthy one. The user never notices.",
                        color=GOOD)
        self.play(ReplacementTransform(cap3, cap4), run_time=0.5)
        self.read(1.5)

        # ---------- the config that declares all of this ------------------ #
        self.play(FadeOut(Group(client, ng, servers, wires, a_in, pool, xr, cap4)),
                  run_time=0.6)
        spec = [
            (0, "# nginx.conf"),
            (0, "http {"),
            (1, "upstream app {"),
            (2, "least_conn;"),
            (2, "server 10.0.0.1:8080;"),
            (2, "server 10.0.0.2:8080;"),
            (2, "server 10.0.0.3:8080;"),
            (1, "}"),
            (1, "server {"),
            (2, "listen 443 ssl;"),
            (2, "location / {"),
            (3, "proxy_pass http://app;"),
            (2, "}"),
            (1, "}"),
            (0, "}"),
        ]
        panel, lines = self.code_panel(spec, title="nginx.conf", target_h=4.9)
        panel.move_to([0, -0.05, 0])
        self.play(FadeIn(panel, shift=UP * 0.15), run_time=0.8)
        capA = self.say("The whole load balancer is just a few lines of nginx.conf.")
        self.play(FadeIn(capA), run_time=0.5)
        self.read(1.0)

        self.focus(panel, lines, [2, 3, 4, 5, 6, 7], color=SERVER_C)
        cap5 = self.say("upstream: the pool of servers, and how to pick one (least_conn).",
                        color=SERVER_C)
        self.play(ReplacementTransform(capA, cap5), run_time=0.5)
        self.read(1.4)

        self.focus(panel, lines, [11], color=NGINX)
        cap6 = self.say("proxy_pass: forward matching requests to that pool. That's it.",
                        color=NGINX)
        self.play(ReplacementTransform(cap5, cap6), run_time=0.5)
        self.read(1.5)

        self.play(FadeOut(Group(panel, self.hlrect, header, cap6)), run_time=0.6)
        self.hlrect = None
        self.takeaway("One address in front. A pool behind.",
                      "nginx picks a healthy server for every request.")
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — At the edge: TLS, static, cache, compression + the takeaway
    # ====================================================================== #
    def scene_edge(self):
        header = self.section_header("More than a proxy", NGINX)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        ng = nginx_box(w=2.7, h=1.7, sub="at the edge").move_to([0, 0.5, 0])
        self.play(GrowFromCenter(ng), run_time=0.6)
        cap = self.say("Sitting at the edge, nginx does a lot before your app is even asked.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.2)

        # four capability chips arranged around nginx
        specs = [
            ("TLS termination", NGINX, [-3.7, 2.05, 0]),
            ("static files", CLIENT_C, [3.7, 2.05, 0]),
            ("response cache", GOLD, [-3.7, -1.05, 0]),
            ("gzip / compression", SERVER_C, [3.7, -1.05, 0]),
        ]
        caps = VGroup()
        conns = VGroup()
        for label, color, pos in specs:
            c = chip(label, color, fs=18, h=0.56).move_to(pos)
            ln = wire(ng.get_center(), c.get_center(), color=color, sw=1.8, op=0.5)
            caps.add(c)
            conns.add(ln)
        self.play(LaggedStart(*[AnimationGroup(Create(ln), FadeIn(c, scale=0.8))
                                for ln, c in zip(conns, caps)],
                              lag_ratio=0.15, run_time=1.4))
        # a small padlock nods at TLS termination
        lock = padlock(NGINX, s=0.72).next_to(caps[0], LEFT, buff=0.16)
        self.play(FadeIn(lock, shift=RIGHT * 0.1), run_time=0.4)
        cap2 = self.say("It ends HTTPS, serves files, caches replies, compresses them.", color=INK)
        self.play(ReplacementTransform(cap, cap2), run_time=0.5)
        self.read(1.5)

        # the split: static/cached served at the edge, dynamic proxied on
        self.play(FadeOut(Group(caps, conns, lock)), run_time=0.5)
        edge_lbl = pill("served at the edge", NGINX, fs=15).move_to([-4.5, 2.45, 0])
        app = server_box("app server", SERVER_C, w=2.3).move_to([4.7, 0.5, 0])
        w_app = wire(ng.get_right(), app.get_left(), color=NGINX, sw=2.2, op=0.7)
        self.play(FadeIn(app, shift=LEFT * 0.1), Create(w_app), run_time=0.5)

        # static asset: bounces straight back from nginx (never reaches the app)
        req_s = mono("/logo.png", fs=16, color=CLIENT_C).move_to([-4.7, 1.5, 0])
        self.play(FadeIn(req_s, shift=RIGHT * 0.1), run_time=0.4)
        d = Dot(req_s.get_right() + RIGHT * 0.15, radius=0.075, color=CLIENT_C)
        self.add(d)
        self.play(d.animate.move_to(ng.get_left() + LEFT * 0.08), run_time=0.4)
        back = ArcBetweenPoints(ng.get_left() + LEFT * 0.08, req_s.get_right() + RIGHT * 0.15,
                                angle=1.4, stroke_opacity=0)
        self.play(MoveAlongPath(d.set_color(NGINX), back), run_time=0.5)
        tick = make_tick(GOOD, sw=7, scale=1.0).next_to(req_s, UP, buff=0.14)
        self.play(FadeIn(tick), FadeOut(d), run_time=0.3)
        self.play(FadeIn(edge_lbl), run_time=0.3)
        cap3 = self.say("Static & cached responses never touch your app — served in microseconds.",
                        color=NGINX)
        self.play(ReplacementTransform(cap2, cap3), run_time=0.5)
        self.read(1.4)

        # dynamic request: proxied through to the app
        req_d = mono("/api/orders", fs=16, color=CLIENT_C).move_to([-4.7, -0.7, 0])
        self.play(FadeIn(req_d, shift=RIGHT * 0.1), run_time=0.4)
        d2 = Dot(req_d.get_right() + RIGHT * 0.15, radius=0.075, color=CLIENT_C)
        self.add(d2)
        self.play(d2.animate.move_to(ng.get_left() + LEFT * 0.08), run_time=0.4)
        self.play(d2.animate.move_to(ng.get_right() + RIGHT * 0.08), run_time=0.28)
        self.play(d2.animate.move_to(app.get_left() + LEFT * 0.08).set_color(NGINX), run_time=0.45)
        self.play(Indicate(app.body, color=GOOD, scale_factor=1.05), FadeOut(d2), run_time=0.3)
        cap4 = self.say("Only the dynamic ones get proxied to a backend.", color=SERVER_C)
        self.play(ReplacementTransform(cap3, cap4), run_time=0.5)
        self.read(1.4)

        self.play(FadeOut(Group(ng, app, w_app, req_s, req_d, tick, edge_lbl, header, cap4)),
                  run_time=0.6)
        self.takeaway("One process at the edge: TLS, cache, compression, load balancing —",
                      "all before your app lifts a finger.")
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_frontdoor()
        self.scene_eventloop()
        self.scene_balance()
        self.scene_edge()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_NginxBase):
    def construct(self):
        self.play_intro()


class FrontDoor(_NginxBase):
    def construct(self):
        self.scene_frontdoor()


class EventLoop(_NginxBase):
    def construct(self):
        self.scene_eventloop()


class Balance(_NginxBase):
    def construct(self):
        self.scene_balance()


class Edge(_NginxBase):
    def construct(self):
        self.scene_edge()


class Outro(_NginxBase):
    def construct(self):
        self.play_outro()


class HowNginxWorks(_NginxBase):
    """The whole short film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    HowNginxWorks().render()

"""Rate Limiting — a short, house-style explainer.

A self-explanatory (no voice-over) film that answers, in five beats, what rate
limiting is, why every serious backend needs it, and how the classic algorithms
actually work:

    1. The flood   -- with no limits, one misbehaving client (or a spike) buries
                      a server: the load gauge redlines, it overheats and crashes,
                      taking every honest user down with it.
    2. The limiter -- put a gate in front. Requests under the limit pass (200);
                      over the limit, a shutter drops and they bounce (429).
                      The server behind stays cool.
    3. Token bucket-- the popular algorithm, animated: tokens drip into a bucket
                      at a steady rate; each request spends one; a full bucket
                      absorbs a burst; an empty bucket returns 429 until it refills.
    4. Algorithms  -- the four you meet in the wild: fixed window, sliding window,
                      token bucket, leaky bucket — and the trade-off each makes.
    5. In practice -- the 429 response (Retry-After, X-RateLimit-* headers), where
                      limits live (per key, at the edge, shared in Redis) and why
                      teams add them: abuse & DDoS, fairness, cost, and stopping a
                      cascading failure.

Bookended by the channel's intro card and the "Thank you for watching!" outro,
matching animations/CDN/cdn.py and the rest of the series.

Everything uses ``Text`` (Pango), never ``Tex`` — so it renders with no LaTeX
toolchain and stays fast to iterate on.

Scenes are exposed individually (``Flood``, ``Limiter``, ``TokenBucket``,
``Algorithms``, ``Practice``, ``Intro``, ``Outro``) and as one film
(``RateLimiting``).

Env knobs:
    RL_QUICK=1        shorten every hold for a fast sanity render
    RL_DELAY=<float>  override the between-step rhythm (motion pacing)
    RL_READ=<float>   override the per-subtitle reading hold (~3 s by default)
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

# --- crisp text ------------------------------------------------------------ #
# Manim's ``Text`` mangles letter/word spacing below ~20 pt. Fix it once: render
# every glyph at a large base size and scale the mobject *down* to the requested
# size (scaling a correctly-spaced render down stays crisp; rendering small does
# not). This shadows manim's ``Text`` so every call benefits automatically.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("RL_QUICK") == "1"
# Two separate pacing knobs so nothing feels rushed:
#   DELAY  scales the small pauses *between* animation steps (motion rhythm).
#   READ   is the absolute hold after a block of text lands, so there is always
#          time to actually read it (~3 s per subtitle).
# ANIM_SLOW stretches every played animation so transitions aren't abrupt.
DELAY = float(os.environ.get("RL_DELAY", 0.28 if QUICK else 1.1))
READ = float(os.environ.get("RL_READ", 0.35 if QUICK else 2.9))
ANIM_SLOW = 1.0 if QUICK else 1.28
END_HOLD = 0.2 if QUICK else 2.4  # settle held on a finished scene before it wipes

# ---- palette (shared house style) ---------------------------------------- #
BG = "#0E1117"          # dark slate background
PANEL = "#161B26"       # server chassis / card fill
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / axes
FAINT = "#3A4152"       # gridlines / guides
GOLD = "#FFD166"        # highlight / headings accent / tokens
REQ_C = "#4CC9F0"       # request packet (cyan)
OK_C = "#3DD68C"        # allowed / 200 OK (green)
DENY_C = "#FF5C5C"      # rejected / 429 / overload (red)
USER_C = "#5B8DEF"      # legitimate client (blue)
BOT_C = "#E5484D"       # attacker / abusive client (crimson)
SRV_C = "#FFB703"       # server (amber)
LIM_C = "#C792EA"       # limiter / gate (violet)
TOKEN_C = "#FFD166"     # tokens (gold)
TOKEN_EDGE = "#B98900"  # token rim
WATER_C = "#4CC9F0"     # water / drip
METAL = "#9AA4B2"       # bucket / metal outline
GOOD = OK_C
WARN = DENY_C

FRAME_R = config.frame_x_radius   # 7.111…

FONT = "Helvetica Neue"           # clean, well-hinted sans everywhere
_BaseText.set_default(font=FONT)


# ========================================================================== #
# Small reusable glyphs
# ========================================================================== #
def server(w=1.2, h=0.95, color=SRV_C, fill=PANEL, n_slots=3, led=True):
    """A little server/rack glyph: chassis + drive slots + a status LED."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.09,
                            stroke_color=color, stroke_width=2.6,
                            fill_color=fill, fill_opacity=1)
    parts = VGroup(body)
    for y in np.linspace(h * 0.27, -h * 0.27, n_slots):
        ln = Line([-w * 0.30, y, 0], [w * 0.14, y, 0],
                  stroke_color=color, stroke_width=2).set_opacity(0.6)
        parts.add(ln)
    if led:
        d = Dot(radius=0.05, color=color)
        d.move_to(body.get_corner(UR) + np.array([-0.15, -0.16, 0]))
        parts.add(d)
    return parts


def person(color=USER_C, s=1.0):
    """A simple 'user' silhouette: head + body."""
    body = RoundedRectangle(width=0.44 * s, height=0.5 * s, corner_radius=0.12 * s,
                            color=color, fill_opacity=1, stroke_width=0)
    head = Circle(radius=0.16 * s, color=color, fill_opacity=1, stroke_width=0)
    head.next_to(body, UP, buff=0.03 * s)
    return VGroup(body, head)


def bot(color=BOT_C, s=1.0):
    """A menacing 'bot' client: an antenna, a square head with angry eyes."""
    head = RoundedRectangle(width=0.62 * s, height=0.5 * s, corner_radius=0.1 * s,
                            stroke_color=color, stroke_width=2.4,
                            fill_color=color, fill_opacity=0.20)
    eye_l = Line([-0.15 * s, 0.05 * s, 0], [-0.03 * s, -0.02 * s, 0])
    eye_r = Line([0.15 * s, 0.05 * s, 0], [0.03 * s, -0.02 * s, 0])
    VGroup(eye_l, eye_r).set_stroke(color, 3)
    mouth = Line([-0.13 * s, -0.13 * s, 0], [0.13 * s, -0.13 * s, 0]).set_stroke(color, 2.4)
    stalk = Line([0, 0.25 * s, 0], [0, 0.4 * s, 0]).set_stroke(color, 2.4)
    ant = Dot(radius=0.05 * s, color=color).move_to([0, 0.44 * s, 0])
    return VGroup(head, eye_l, eye_r, mouth, stalk, ant)


def req_packet(color=REQ_C, w=0.4, h=0.3):
    """A request, drawn as a little data 'envelope' (not just a dot)."""
    box = RoundedRectangle(width=w, height=h, corner_radius=0.055,
                           stroke_color=color, stroke_width=2.2,
                           fill_color=color, fill_opacity=0.22)
    fl = VMobject()
    fl.set_points_as_corners([[-w / 2 + 0.03, h / 2 - 0.03, 0], [0, -0.02, 0],
                              [w / 2 - 0.03, h / 2 - 0.03, 0]])
    fl.set_stroke(color, 1.8)
    return VGroup(box, fl)


def recolor_packet(pkt, color):
    pkt[0].set_stroke(color).set_fill(color, 0.22)
    pkt[1].set_stroke(color)
    return pkt


def token(r=0.16):
    """A gold token/coin: a filled disc with an inner ring."""
    c = Circle(radius=r, color=TOKEN_C, fill_color=TOKEN_C, fill_opacity=0.95,
               stroke_color=TOKEN_EDGE, stroke_width=2)
    inner = Circle(radius=r * 0.52, color=TOKEN_EDGE, stroke_width=1.6, fill_opacity=0)
    return VGroup(c, inner)


def bucket(top_w=2.3, bot_w=1.6, h=2.0, color=METAL):
    """A metal pail: two slanted sides + base, an open top with a rim lip."""
    tl = np.array([-top_w / 2, h / 2, 0]);  tr = np.array([top_w / 2, h / 2, 0])
    bl = np.array([-bot_w / 2, -h / 2, 0]); br = np.array([bot_w / 2, -h / 2, 0])
    fill = Polygon(tl, bl, br, tr, stroke_width=0, fill_color=PANEL, fill_opacity=0.55)
    walls = VMobject().set_points_as_corners([tl, bl, br, tr])
    walls.set_stroke(color, 3.2)
    rim = Line(tl, tr).set_stroke(color, 4.2)
    lip = Arc(radius=top_w / 2, start_angle=PI, angle=-PI, stroke_color=color,
              stroke_width=2).stretch_to_fit_height(0.16).move_to((tl + tr) / 2)
    return VGroup(fill, walls, rim, lip)


def stamp(text, color=DENY_C, fs=22, angle=8 * DEGREES):
    """A rubber-stamp badge, slightly rotated for a 'stamped' feel."""
    t = Text(text, font_size=fs, color=color, weight="BOLD")
    box = RoundedRectangle(width=t.width + 0.3, height=t.height + 0.22, corner_radius=0.08,
                           stroke_color=color, stroke_width=3,
                           fill_color=color, fill_opacity=0.14).move_to(t)
    return VGroup(box, t).rotate(angle)


def build_gauge(radius=1.05):
    """A semicircular load gauge (green→amber→red) with a needle.

    Returns (group, needle, hub_point) — the needle starts pointing left
    (load = 0) and is rotated about ``hub_point`` to show higher load.
    """
    g = VGroup()
    for col, a0, a1 in [(OK_C, 180, 120), (GOLD, 120, 60), (DENY_C, 60, 0)]:
        g.add(Arc(radius=radius, start_angle=a0 * DEGREES, angle=(a1 - a0) * DEGREES,
                  stroke_color=col, stroke_width=12))
    for a in (180, 135, 90, 45, 0):
        u = np.array([np.cos(a * DEGREES), np.sin(a * DEGREES), 0])
        g.add(Line(radius * u, (radius + 0.13) * u, stroke_color=MUTED, stroke_width=2))
    needle = Line([0, 0, 0], [-radius * 0.82, 0, 0]).set_stroke(INK, 4)
    hub = Dot(radius=0.09, color=INK)
    g.add(needle, hub)
    return g, needle, np.array([0.0, 0.0, 0.0])


def code_panel(lines, title="", fs=20, pad=0.34, min_w=0.0):
    """A Menlo code/response card with a mac-style title bar.

    ``lines`` is a list of (text, color). ``title`` sits after the traffic dots.
    """
    body = VGroup(*[Text(t, font="Menlo", font_size=fs, color=c)
                    for t, c in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    w = max(min_w, body.width + 2 * pad)
    h = body.height + 2 * pad + 0.5
    bg = RoundedRectangle(width=w, height=h, corner_radius=0.12,
                          stroke_color=FAINT, stroke_width=2,
                          fill_color="#0B0E14", fill_opacity=1)
    bar = Rectangle(width=w, height=0.44, stroke_width=0, fill_color=PANEL, fill_opacity=1)
    bar.move_to(bg).align_to(bg, UP)
    dots = VGroup(*[Dot(radius=0.052, color=c) for c in ("#FF5F56", "#FFBD2E", "#27C93F")])
    dots.arrange(RIGHT, buff=0.11).move_to(bar.get_left() + RIGHT * 0.34)
    grp = VGroup(bg, bar, dots)
    if title:
        ttl = Text(title, font="Menlo", font_size=15, color=MUTED)
        ttl.next_to(dots, RIGHT, buff=0.22)
        grp.add(ttl)
    body.next_to(bar, DOWN, buff=0.2).align_to(bg, LEFT).shift(RIGHT * pad)
    grp.add(body)
    return grp


# ========================================================================== #
class _RLBase(Scene):
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

    # ---- text helpers ----------------------------------------------------- #
    def section_header(self, label, color=INK):
        txt = Text(label, font_size=33, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(txt.get_left(), txt.get_right()).next_to(txt, DOWN, buff=0.12)
        line.set_stroke(color=color, width=4)
        return VGroup(txt, line)

    def say(self, text, color=MUTED, fs=26, y=-3.5, **kw):
        """A bottom caption, width-clamped so it never runs off-screen."""
        m = Text(text, font_size=fs, color=color, **kw)
        if m.width > 12.8:
            m.scale_to_fit_width(12.8)
        m.move_to([0, y, 0])
        return m

    def pill(self, text, color, fs=24, fill_op=0.16):
        t = Text(text, font_size=fs, color=color, weight="BOLD")
        box = RoundedRectangle(width=t.width + 0.44, height=t.height + 0.3,
                               corner_radius=0.14, stroke_color=color, stroke_width=2,
                               fill_color=color, fill_opacity=fill_op)
        box.move_to(t)
        return VGroup(box, t)

    def check_line(self, head, tail="", color=GOOD, fs=25):
        c = Text("✓", font_size=fs, color=color, weight="BOLD")
        h = Text(head, font_size=fs, color=INK, weight="BOLD").next_to(c, RIGHT, buff=0.2)
        grp = VGroup(c, h)
        if tail:
            t = Text(tail, font_size=fs - 3, color=MUTED).next_to(h, RIGHT, buff=0.14)
            grp.add(t)
        return grp

    def card_box(self, content, color, pad=0.34, fill_op=0.5, corner=0.16):
        box = RoundedRectangle(width=content.width + 2 * pad,
                               height=content.height + 2 * pad, corner_radius=corner,
                               stroke_color=color, stroke_width=2,
                               fill_color=PANEL, fill_opacity=fill_op)
        box.move_to(content)
        return box

    # ---- packet motion ---------------------------------------------------- #
    def fly(self, mob, path, rt=1.0, rate=linear):
        self.play(MoveAlongPath(mob, path), run_time=rt, rate_func=rate)

    # ---- house-style intro / outro cards ---------------------------------- #
    def play_intro(self):
        header = Text("Rate Limiting", font_size=60, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        writer = Text("Created by Ptolémé", font_size=28, color=USER_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.6)
        # a packet zips along the rule — then a red barrier stops it: a wink at
        # the whole idea (traffic, gated).
        pkt = req_packet(REQ_C).scale(0.9).move_to(line.get_left())
        bar = Line(line.get_center() + UP * 0.22, line.get_center() + DOWN * 0.22)
        bar.set_stroke(DENY_C, 5).move_to([line.get_center()[0] + 0.6, line.get_center()[1], 0])
        self.play(FadeIn(pkt), run_time=0.3)
        self.play(pkt.animate.move_to(bar.get_center() + LEFT * 0.35),
                  run_time=0.7, rate_func=rush_into)
        self.play(Create(bar), recolor_packet(pkt, DENY_C).animate.shift(LEFT * 0.25),
                  run_time=0.3)
        self.play(FadeOut(pkt, shift=LEFT * 0.3), FadeOut(bar), run_time=0.4)
        self.read(0.6)
        sub = Text("How your backend survives the flood  ·  System Design",
                   font_size=30, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.read(1.3)
        self.play(FadeOut(VGroup(header, writer, line)), run_time=1.0)
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
        recap = Text("Let the good traffic in — keep the flood out.",
                     font_size=26, color=GOLD)
        recap.next_to(writer, DOWN, buff=0.5)
        self.play(Write(header), Create(line), run_time=1.6)
        self.read(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap), run_time=0.8)
        self.read(1.6)
        self.play(FadeOut(VGroup(header, line, writer, recap)), run_time=1.3)
        self.card_wait(0.5)

    # ====================================================================== #
    # Scene 1 — The flood: no limits, one client buries the server
    # ====================================================================== #
    def scene_flood(self):
        header = self.section_header("No limits: what a flood does", DENY_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # the target server, centre-right, with a load gauge above-right
        srv = server(1.5, 1.15, color=SRV_C).move_to([2.7, -0.15, 0])
        srv_lab = Text("API server", font_size=22, color=SRV_C, weight="BOLD")
        srv_lab.next_to(srv, DOWN, buff=0.24)
        gauge, needle, hub = build_gauge(1.0)
        gpt = np.array([4.7, 1.35, 0])
        gauge.shift(gpt)
        gauge_lab = Text("LOAD", font_size=18, color=MUTED).next_to(gauge, DOWN, buff=0.12)
        self.play(FadeIn(srv), FadeIn(srv_lab), run_time=0.6)
        self.play(Create(gauge), FadeIn(gauge_lab), run_time=0.7)

        state = {"f": 0.0}

        def set_load(f, rt=0.6):
            new = 180 - f * 180
            old = 180 - state["f"] * 180
            self.play(Rotate(needle, (new - old) * DEGREES, about_point=gpt), run_time=rt)
            state["f"] = f

        # three honest users on the left, sending politely
        users = VGroup(*[person(USER_C, 0.9) for _ in range(3)])
        users.arrange(DOWN, buff=0.7).move_to([-5.2, 0.2, 0])
        ulab = Text("Real users", font_size=20, color=USER_C, weight="BOLD")
        ulab.next_to(users, DOWN, buff=0.22)
        self.play(LaggedStart(*[FadeIn(u, shift=RIGHT * 0.15) for u in users],
                              lag_ratio=0.2, run_time=0.9), FadeIn(ulab))
        cap = self.say("A few honest requests — the server barely notices.")
        self.play(FadeIn(cap), run_time=0.4)

        def send_from(src, color=REQ_C, rt=0.7, r=0.0):
            p = req_packet(color).move_to(src)
            path = ArcBetweenPoints(np.array(src), srv.get_left() + LEFT * 0.05,
                                    angle=r if r else 0.0001)
            self.add(p)
            self.play(MoveAlongPath(p, path), run_time=rt, rate_func=linear)
            self.remove(p)

        for u in users:
            send_from(u.get_right() + RIGHT * 0.1, REQ_C, rt=0.7, r=-0.3)
        set_load(0.18, rt=0.6)
        self.play(Flash(srv, color=OK_C, flash_radius=0.9), run_time=0.4)
        self.read()

        # the attacker arrives and floods
        self.play(FadeOut(cap), run_time=0.3)
        attacker = bot(BOT_C, 1.1).move_to([-5.2, -2.4, 0])
        alab = Text("Abusive client / bot", font_size=20, color=BOT_C, weight="BOLD")
        alab.next_to(attacker, RIGHT, buff=0.25)
        self.play(FadeIn(attacker, scale=0.6), FadeIn(alab), run_time=0.6)
        cap2 = self.say("Then one bot decides to hammer it — thousands of requests a second.")
        self.play(FadeIn(cap2), run_time=0.4)
        self.read(0.8)

        # a rising storm of packets from the bot; the gauge climbs into the red
        loads = [0.42, 0.68, 0.9, 1.0]
        src = attacker.get_right() + RIGHT * 0.15
        for wave, f in enumerate(loads):
            n = 4 + wave * 3
            pkts = VGroup(*[req_packet(BOT_C).scale(0.9).move_to(src) for _ in range(n)])
            paths = []
            for i in range(n):
                jitter = (np.random.default_rng(wave * 10 + i).uniform(-0.4, 0.9))
                target = srv.get_left() + LEFT * 0.05 + UP * np.random.default_rng(i + wave).uniform(-0.5, 0.5)
                paths.append(ArcBetweenPoints(src, target, angle=jitter))
            self.add(pkts)
            self.play(LaggedStart(*[MoveAlongPath(p, pa) for p, pa in zip(pkts, paths)],
                                  lag_ratio=0.03, run_time=0.9 - wave * 0.12),
                      Rotate(needle, ((180 - f * 180) - (180 - state["f"] * 180)) * DEGREES,
                             about_point=gpt),
                      rate_func=linear)
            state["f"] = f
            self.remove(*pkts)
            if f < 1.0:
                self.play(srv[0].animate.set_fill(
                    interpolate_color(ManimColor(PANEL), ManimColor(DENY_C), f)), run_time=0.25)

        # redline: the server overheats, shakes, cracks and blows
        redline = self.pill("OVERLOADED", DENY_C, fs=20)
        redline.next_to(gauge, UP, buff=0.2)
        self.play(FadeIn(redline, shift=DOWN * 0.1),
                  Flash(gauge, color=DENY_C, flash_radius=1.1), run_time=0.5)
        cap3 = self.say("The load gauge redlines. No brakes, no back-pressure…")
        self.play(ReplacementTransform(cap2, cap3), run_time=0.5)
        self.play(srv.animate.set_color(DENY_C), run_time=0.3)
        srv[0].set_fill(DENY_C, 0.5)
        self.play(Wiggle(srv, scale_value=1.12, rotation_angle=0.04 * TAU), run_time=0.7)
        self.play(Wiggle(srv, scale_value=1.14, rotation_angle=0.05 * TAU), run_time=0.6)

        # crack + explode
        crack = VMobject().set_points_as_corners([
            srv.get_top() + LEFT * 0.1, srv.get_center() + UP * 0.15 + RIGHT * 0.12,
            srv.get_center() + DOWN * 0.05 + LEFT * 0.1, srv.get_bottom() + RIGHT * 0.15,
        ]).set_stroke(INK, 3)
        self.play(Create(crack), run_time=0.3)
        shards = VGroup(*[
            Triangle().scale(0.14).set_fill(SRV_C, 0.8).set_stroke(DENY_C, 1.5)
            .move_to(srv.get_center()) for _ in range(12)
        ])
        rng = np.random.default_rng(3)
        dirs = [np.array([np.cos(a), np.sin(a), 0]) for a in rng.uniform(0, TAU, 12)]
        cap4 = self.say("…it crashes. 503 — Service Unavailable.", color=DENY_C, fs=27)
        self.play(
            Flash(srv, color=DENY_C, flash_radius=1.4, num_lines=24, line_length=0.6),
            FadeOut(crack),
            *[shards[i].animate.shift(dirs[i] * rng.uniform(1.2, 2.4)).set_opacity(0)
              for i in range(12)],
            srv.animate.set_opacity(0.12),
            ReplacementTransform(cap3, cap4),
            run_time=0.9,
        )
        down = stamp("503", DENY_C, fs=40, angle=-9 * DEGREES).move_to(srv)
        self.play(FadeIn(down, scale=1.3), run_time=0.4)
        self.remove(*shards)
        self.read(0.8)

        # collateral: the honest users now get errors too
        for u in users:
            x = Cross(scale_factor=0.16).set_stroke(DENY_C, 4).move_to(u.get_right() + RIGHT * 0.55)
            self.play(FadeIn(x, scale=0.5), run_time=0.2)
        cap5 = self.say("Everyone loses — including the users who did nothing wrong.",
                        color=INK, fs=27)
        self.play(ReplacementTransform(cap4, cap5), run_time=0.5)
        self.read(1.2)

        # takeaway
        self.wipe()
        k1 = Text("With no limit,", font_size=36, color=INK, weight="BOLD")
        k2 = Text("one client can take down everyone.", font_size=36, color=GOLD, weight="BOLD")
        VGroup(k1, k2).arrange(DOWN, buff=0.3).move_to(ORIGIN)
        self.play(FadeIn(k1, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(k2, shift=UP * 0.1), run_time=0.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — The limiter: a gate that passes 200 and bounces 429
    # ====================================================================== #
    def scene_limiter(self):
        header = self.section_header("The fix: a limiter in front", LIM_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # the limiter wall: two violet posts with a slot (gap) in the middle
        wall_x = -0.2
        gap_y = 0.2
        gap_h = 1.0
        # two posts short enough that the title pill above them never overlaps
        top_post = RoundedRectangle(width=0.5, height=1.45, corner_radius=0.1,
                                    stroke_color=LIM_C, stroke_width=2.6,
                                    fill_color=LIM_C, fill_opacity=0.18)
        top_post.move_to([wall_x, gap_y + gap_h / 2 + 0.725, 0])   # top edge ≈ 2.15
        bot_post = RoundedRectangle(width=0.5, height=1.35, corner_radius=0.1,
                                    stroke_color=LIM_C, stroke_width=2.6,
                                    fill_color=LIM_C, fill_opacity=0.18)
        bot_post.move_to([wall_x, gap_y - gap_h / 2 - 0.675, 0])   # bottom edge ≈ -1.65
        wall = VGroup(top_post, bot_post)
        self.play(FadeIn(wall, shift=UP * 0.1), run_time=0.7)

        # cool server on the right (the contrast with the meltdown)
        srv = server(1.4, 1.1, color=SRV_C).move_to([4.7, gap_y, 0])
        srv_lab = Text("API server", font_size=20, color=SRV_C, weight="BOLD").next_to(srv, DOWN, buff=0.22)
        cool = Text("cool  ·  healthy", font_size=17, color=OK_C).next_to(srv_lab, DOWN, buff=0.08)
        self.play(FadeIn(srv), FadeIn(srv_lab), FadeIn(cool), run_time=0.6)

        # the limit + a little window counter on the limiter
        limit = 6
        limpill = self.pill("RATE LIMITER  ·  6 req / window", LIM_C, fs=21)
        limpill.move_to([wall_x, 2.62, 0])
        self.play(FadeIn(limpill, shift=DOWN * 0.1), run_time=0.5)

        ctr_track = RoundedRectangle(width=1.9, height=0.26, corner_radius=0.13,
                                     stroke_color=MUTED, stroke_width=1.6, fill_opacity=0)
        ctr_track.move_to([wall_x, gap_y - 2.0, 0])
        ctr_lbl = Text("0 / 6", font_size=18, color=INK).next_to(ctr_track, DOWN, buff=0.12)
        self.play(Create(ctr_track), FadeIn(ctr_lbl), run_time=0.4)

        client = person(USER_C, 0.95).move_to([-5.5, gap_y, 0])
        clab = Text("client", font_size=19, color=USER_C, weight="BOLD").next_to(client, DOWN, buff=0.2)
        self.play(FadeIn(client), FadeIn(clab), run_time=0.5)

        cap = self.say("Requests must pass the limiter first. Under the limit → they go through.")
        self.play(FadeIn(cap), run_time=0.4)

        slot_c = np.array([wall_x, gap_y, 0])
        count = {"n": 0}

        def set_counter(n, color=OK_C):
            frac = min(n, limit) / limit
            fill = RoundedRectangle(width=max(0.03, 1.9 * frac), height=0.26, corner_radius=0.12,
                                    stroke_width=0, fill_color=color, fill_opacity=0.9)
            fill.move_to(ctr_track.get_left(), aligned_edge=LEFT)
            new_lbl = Text(f"{min(n, limit)} / {limit}", font_size=18, color=INK).move_to(ctr_lbl)
            return fill, new_lbl

        ctr_fill = None

        def allow_one(rt=0.9):
            nonlocal ctr_fill
            p = req_packet(REQ_C).move_to(client.get_right() + RIGHT * 0.15)
            self.add(p)
            p_in = Line(p.get_center(), slot_c + LEFT * 0.35)
            self.play(MoveAlongPath(p, p_in), run_time=rt * 0.5, rate_func=linear)
            # pass through the slot, turn green (200), continue to the server
            recolor_packet(p, OK_C)
            p_out = Line(slot_c + LEFT * 0.35, srv.get_left() + LEFT * 0.08)
            count["n"] += 1
            nf, nl = set_counter(count["n"])
            if ctr_fill is None:
                ctr_fill = nf
                self.add(ctr_fill)
                self.play(MoveAlongPath(p, p_out), Transform(ctr_lbl, nl), run_time=rt * 0.7,
                          rate_func=linear)
            else:
                self.play(MoveAlongPath(p, p_out), Transform(ctr_fill, nf),
                          Transform(ctr_lbl, nl), run_time=rt * 0.7, rate_func=linear)
            self.play(Flash(srv, color=OK_C, flash_radius=0.7), run_time=0.3)
            self.remove(p)

        for _ in range(3):
            allow_one(0.8)
        ok_badge = stamp("200 OK", OK_C, fs=20, angle=-6 * DEGREES).next_to(srv, UP, buff=0.3)
        self.play(FadeIn(ok_badge, shift=DOWN * 0.1), run_time=0.4)
        self.read()

        # now the client bursts past the limit → shutter drops, 429 bounce
        self.play(FadeOut(cap), FadeOut(ok_badge), run_time=0.3)
        cap2 = self.say("Burst past the limit and the gate shuts: 429 — Too Many Requests.",
                        color=INK)
        self.play(FadeIn(cap2), run_time=0.4)
        for _ in range(3):
            allow_one(0.5)   # fills 4,5,6 — reaches the limit

        # the shutter drops across the slot, turns the counter red
        shutter = Rectangle(width=0.5, height=gap_h + 0.1, stroke_width=0,
                            fill_color=DENY_C, fill_opacity=0.9)
        shutter.move_to([wall_x, gap_y + gap_h + 0.6, 0])
        self.add(shutter)
        red_fill, red_lbl = set_counter(limit, color=DENY_C)
        self.play(shutter.animate.move_to(slot_c), Transform(ctr_fill, red_fill),
                  Transform(ctr_lbl, red_lbl), run_time=0.5)

        # further requests slam the shutter and bounce back with a 429
        for i in range(3):
            p = req_packet(BOT_C).move_to(client.get_right() + RIGHT * 0.15)
            self.add(p)
            hit = slot_c + LEFT * 0.55 + UP * (0.25 * (i - 1))
            self.play(MoveAlongPath(p, Line(p.get_center(), hit)), run_time=0.4, rate_func=rush_into)
            recolor_packet(p, DENY_C)
            back = client.get_right() + RIGHT * 0.4 + DOWN * 1.1
            self.play(MoveAlongPath(p, ArcBetweenPoints(hit, back, angle=-1.2)),
                      run_time=0.5, rate_func=rush_from)
            self.remove(p)
        deny_badge = stamp("429", DENY_C, fs=26, angle=8 * DEGREES)
        deny_badge.move_to([wall_x - 1.7, gap_y - 1.2, 0])
        self.play(FadeIn(deny_badge, scale=1.2),
                  Flash(shutter, color=DENY_C, flash_radius=0.7), run_time=0.4)
        self.read()

        # the server never even sees them — it stays cool
        self.play(Indicate(VGroup(srv, srv_lab, cool), color=OK_C, scale_factor=1.06), run_time=0.6)
        cap3 = self.say("The server never even sees them — it stays up for the good traffic.",
                        color=OK_C)
        self.play(ReplacementTransform(cap2, cap3), run_time=0.5)
        self.read(1.0)

        # takeaway
        self.wipe()
        k1 = Text("The limiter absorbs the abuse", font_size=34, color=INK, weight="BOLD")
        k2 = Text("so the server doesn't have to.", font_size=34, color=GOLD, weight="BOLD")
        VGroup(k1, k2).arrange(DOWN, buff=0.3).move_to(ORIGIN)
        self.play(FadeIn(k1, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(k2, shift=UP * 0.1), run_time=0.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Token bucket: the popular algorithm, animated
    # ====================================================================== #
    def scene_bucket(self):
        header = self.section_header("How it decides: the token bucket", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # the bucket sits upper-centre; requests flow on a clear lane *below* it
        bkt = bucket(2.3, 1.6, 2.0).move_to([0, 0.5, 0])
        # a faucet above, dripping tokens in
        fau_body = RoundedRectangle(width=0.7, height=0.32, corner_radius=0.06,
                                    stroke_color=METAL, stroke_width=2.4,
                                    fill_color=PANEL, fill_opacity=1).move_to([0.0, 2.42, 0])
        spout = RoundedRectangle(width=0.16, height=0.3, corner_radius=0.04,
                                 stroke_color=METAL, stroke_width=2.4,
                                 fill_color=PANEL, fill_opacity=1)
        spout.next_to(fau_body, DOWN, buff=0.0)
        pipe = Line([0.35, 2.58, 0], [1.5, 2.58, 0]).set_stroke(METAL, 3)
        faucet = VGroup(pipe, fau_body, spout)
        self.play(FadeIn(bkt, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(faucet), run_time=0.5)

        # token slots inside the bucket (fill bottom-up), capacity 8
        C = 8
        slots = []
        for row_y in (-0.2, 0.24):        # two rows near the base, bottom then top
            for cx in (-0.5, -0.17, 0.17, 0.5):
                slots.append(np.array([cx, row_y, 0]))
        toks = [None] * C

        num = DecimalNumber(0, num_decimal_places=0, font_size=40, color=TOKEN_C)
        num.set_stroke(width=0)
        cap_txt = Text(f"/ {C}", font_size=26, color=MUTED)
        rgroup = VGroup(num, cap_txt).arrange(RIGHT, buff=0.14)
        rlab = Text("tokens", font_size=20, color=MUTED)
        rout = VGroup(rlab, rgroup).arrange(DOWN, buff=0.12).move_to([3.6, 0.7, 0])
        self.play(FadeIn(rout), run_time=0.4)

        spout_pt = spout.get_bottom() + DOWN * 0.05

        def refresh_num(rt=0.2):
            self.play(ChangeDecimalToValue(num, sum(x is not None for x in toks)), run_time=rt)

        def drop_token(rt=0.32):
            """Refill: a token drops from the faucet into the next empty slot."""
            idx = next((i for i in range(C) if toks[i] is None), None)
            if idx is None:
                return
            t = token().move_to(spout_pt)
            self.add(t)
            self.play(t.animate.move_to(slots[idx]), run_time=rt, rate_func=rush_into)
            toks[idx] = t
            refresh_num()

        def take_top():
            idx = next((i for i in reversed(range(C)) if toks[i] is not None), None)
            if idx is None:
                return None
            t = toks[idx]; toks[idx] = None
            return t

        # fill the bucket
        cap = self.say("Tokens drip into a bucket at a fixed rate, up to its capacity.")
        self.play(FadeIn(cap), run_time=0.4)
        for _ in range(C):
            drop_token(0.2 if not QUICK else 0.1)
        self.read(0.8)

        # the request lane, below the bucket
        lane_y = -1.9
        client = person(USER_C, 0.95).move_to([-5.5, lane_y, 0])
        clab = Text("requests", font_size=19, color=USER_C, weight="BOLD").next_to(client, DOWN, buff=0.18)
        srv = server(1.1, 0.85, color=OK_C).move_to([5.3, lane_y, 0])
        slab = Text("server", font_size=18, color=OK_C, weight="BOLD").next_to(srv, DOWN, buff=0.16)
        lane = DashedLine([-4.6, lane_y, 0], [4.7, lane_y, 0], dash_length=0.12).set_stroke(FAINT, 2)
        self.play(FadeIn(client), FadeIn(clab), FadeIn(srv), FadeIn(slab), Create(lane), run_time=0.6)
        cap2 = self.say("Each request must spend one token to pass — otherwise it's refused.")
        self.play(ReplacementTransform(cap, cap2), run_time=0.5)

        mid = np.array([0, lane_y, 0])

        def request(rt=0.6):
            p = req_packet(REQ_C).move_to(client.get_right() + RIGHT * 0.2)
            self.add(p)
            self.play(MoveAlongPath(p, Line(p.get_center(), mid)), run_time=rt, rate_func=linear)
            t = take_top()
            if t is not None:
                # a token drops out of the bucket onto the request → it turns green
                recolor_packet(p, OK_C)
                self.play(t.animate.move_to(p.get_center()).scale(0.5).set_opacity(0), run_time=0.4)
                self.remove(t); refresh_num()
                self.play(MoveAlongPath(p, Line(mid, srv.get_left() + LEFT * 0.1)), run_time=rt, rate_func=linear)
                self.play(Flash(srv, color=OK_C, flash_radius=0.6), run_time=0.25)
                self.remove(p)
                return True
            # empty bucket → 429, peel off downward
            recolor_packet(p, DENY_C)
            b = stamp("429", DENY_C, fs=16, angle=8 * DEGREES).move_to(mid + UP * 0.45)
            self.play(MoveAlongPath(p, ArcBetweenPoints(mid, mid + DOWN * 0.85 + LEFT * 1.4, angle=1.0)),
                      FadeIn(b), run_time=rt, rate_func=rush_from)
            self.play(FadeOut(p), FadeOut(b), run_time=0.25)
            return False

        for _ in range(3):
            request(0.55)
        self.read()

        # a full bucket absorbs a burst
        self.play(FadeOut(cap2), run_time=0.3)
        cap3 = self.say("A full bucket absorbs a burst — many requests pass at once.")
        self.play(FadeIn(cap3), run_time=0.4)
        n = 5
        # queue the burst to the RIGHT of the client (toward the bucket), so none
        # of the packets spawn off the left edge
        burst = VGroup(*[req_packet(REQ_C).move_to(client.get_right() + RIGHT * (0.3 + 0.42 * i))
                         for i in range(n)])
        self.add(burst)
        targets = [mid + RIGHT * (0.52 * (i - (n - 1) / 2)) for i in range(n)]
        self.play(LaggedStart(*[MoveAlongPath(p, Line(p.get_center(), tg))
                                for p, tg in zip(burst, targets)], lag_ratio=0.06, run_time=0.9),
                  rate_func=linear)
        spent = VGroup()
        for p in burst:
            t = take_top()
            if t is not None:
                recolor_packet(p, OK_C)
                spent.add(t)
        self.play(LaggedStart(*[t.animate.move_to(p.get_center()).scale(0.5).set_opacity(0)
                                for t, p in zip(spent, burst)], lag_ratio=0.05, run_time=0.7))
        self.remove(*spent); refresh_num()
        self.play(LaggedStart(*[MoveAlongPath(p, Line(p.get_center(), srv.get_left() + LEFT * 0.1 + UP * (0.09 * (i - 2))))
                                for i, p in enumerate(burst)], lag_ratio=0.06, run_time=0.9), rate_func=linear)
        self.play(Flash(srv, color=OK_C, flash_radius=0.8), run_time=0.3)
        self.remove(*burst)
        self.read()

        # empty → 429 until it refills
        self.play(FadeOut(cap3), run_time=0.3)
        cap4 = self.say("Bucket empty → further requests get 429.", color=DENY_C)
        self.play(FadeIn(cap4), run_time=0.4)
        request(0.55)
        request(0.55)
        self.read(0.8)

        cap5 = self.say("The refill rate is your real, long-run limit.", color=GOLD)
        self.play(ReplacementTransform(cap4, cap5), run_time=0.5)
        drop_token(0.42)
        self.play(Indicate(rgroup, color=TOKEN_C, scale_factor=1.15), run_time=0.5)
        request(0.55)
        self.read(1.0)

        # takeaway
        self.wipe()
        k1 = Text("Refill rate = your steady limit.", font_size=33, color=INK, weight="BOLD")
        k2 = Text("Bucket size = the burst you'll tolerate.", font_size=33, color=GOLD, weight="BOLD")
        VGroup(k1, k2).arrange(DOWN, buff=0.32).move_to(ORIGIN)
        self.play(FadeIn(k1, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(k2, shift=UP * 0.1), run_time=0.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — The four algorithms you meet in the wild
    # ====================================================================== #
    def scene_algorithms(self):
        header = self.section_header("Four ways to count", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        def glyph_fixed():
            g = VGroup()
            for i, hgt in enumerate((0.3, 0.5, 0.72, 0.32)):
                b = Rectangle(width=0.16, height=hgt, stroke_width=0,
                              fill_color=USER_C, fill_opacity=0.85)
                b.move_to([i * 0.22 - 0.33, hgt / 2 - 0.36, 0])
                g.add(b)
            sep = DashedLine([0.11, -0.42, 0], [0.11, 0.42, 0]).set_stroke(DENY_C, 2)
            g.add(sep)
            return g

        def glyph_sliding():
            frame = RoundedRectangle(width=0.9, height=0.7, corner_radius=0.06,
                                     stroke_color=USER_C, stroke_width=2.4, fill_opacity=0)
            inner = RoundedRectangle(width=0.9, height=0.7, corner_radius=0.06,
                                     stroke_color=OK_C, stroke_width=2.4, fill_opacity=0)
            inner.shift(RIGHT * 0.22)
            arr = Arrow([0.1, 0, 0], [0.5, 0, 0], buff=0, stroke_width=3, color=OK_C,
                        max_tip_length_to_length_ratio=0.4)
            return VGroup(frame, inner, arr)

        def glyph_token():
            b = bucket(0.8, 0.55, 0.7, color=TOKEN_C).scale(1.0)
            coins = VGroup(*[token(0.08).move_to(b.get_center() + np.array([dx, -0.16, 0]))
                             for dx in (-0.16, 0.02, 0.2)])
            return VGroup(b, coins)

        def glyph_leaky():
            b = bucket(0.8, 0.5, 0.7, color=WATER_C)
            water = Rectangle(width=0.46, height=0.4, stroke_width=0,
                              fill_color=WATER_C, fill_opacity=0.5).move_to(b.get_center() + DOWN * 0.1)
            drip = VGroup(*[Dot(radius=0.03, color=WATER_C).move_to(b.get_bottom() + DOWN * (0.1 + i * 0.16))
                            for i in range(2)])
            return VGroup(b, water, drip)

        specs = [
            ("Fixed window", USER_C, glyph_fixed,
             ["Tally hits per clock window.", "Simple — but 2× burst at the edges."]),
            ("Sliding window", OK_C, glyph_sliding,
             ["Weighted rolling window.", "Smooth; a little more bookkeeping."]),
            ("Token bucket", GOLD, glyph_token,
             ["Refill rate r, capacity C.", "Allows bursts up to the bucket."]),
            ("Leaky bucket", WATER_C, glyph_leaky,
             ["Queue drains at a constant rate.", "Smooths output; can add latency."]),
        ]
        centers = [[-3.35, 1.15, 0], [3.35, 1.15, 0], [-3.35, -1.55, 0], [3.35, -1.55, 0]]

        cards = []
        for (name, color, gl, desc), ctr in zip(specs, centers):
            title = Text(name, font_size=25, color=color, weight="BOLD")
            g = gl().scale(1.0)
            d0 = Text(desc[0], font_size=18, color=INK)
            d1 = Text(desc[1], font_size=18, color=MUTED)
            texts = VGroup(title, d0, d1).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            row = VGroup(g, texts).arrange(RIGHT, buff=0.32, aligned_edge=UP)
            box = RoundedRectangle(width=row.width + 0.6, height=row.height + 0.5,
                                   corner_radius=0.14, stroke_color=color, stroke_width=2,
                                   fill_color=PANEL, fill_opacity=0.5)
            box.move_to(row)
            card = VGroup(box, row).move_to(ctr)
            cards.append(card)

        for i, card in enumerate(cards):
            self.play(FadeIn(card, shift=UP * 0.12), run_time=0.55)
            self.read(0.7 if i < 3 else 1.0)

        # highlight the two that dominate in practice
        note = self.say("In practice, token bucket and sliding window win most designs.",
                        color=GOLD)
        self.play(FadeIn(note), run_time=0.4)
        self.play(cards[2][0].animate.set_stroke(GOLD, 4),
                  cards[1][0].animate.set_stroke(OK_C, 4),
                  Circumscribe(cards[2], color=GOLD, run_time=1.2),
                  run_time=1.2)
        self.read(1.4)

        self.wipe()
        k1 = Text("Same goal — shape how", font_size=34, color=INK, weight="BOLD")
        k2 = Text("'too fast' is allowed to look.", font_size=34, color=GOLD, weight="BOLD")
        VGroup(k1, k2).arrange(DOWN, buff=0.3).move_to(ORIGIN)
        self.play(FadeIn(k1, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(k2, shift=UP * 0.1), run_time=0.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — In practice: the 429, where limits live, and why
    # ====================================================================== #
    def scene_practice(self):
        header = self.section_header("In practice", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # ---- the 429 response the client actually gets ----
        panel = code_panel([
            ("HTTP/1.1 429 Too Many Requests", DENY_C),
            ("Retry-After: 30", GOLD),
            ("X-RateLimit-Limit: 100", MUTED),
            ("X-RateLimit-Remaining: 0", MUTED),
            ("X-RateLimit-Reset: 1712345678", MUTED),
        ], title="response", fs=21)
        panel.move_to([0, 0.55, 0])
        self.play(FadeIn(panel, shift=UP * 0.1), run_time=0.7)
        cap = self.say("A good limiter tells the client what happened — and when to retry.")
        self.play(FadeIn(cap), run_time=0.4)
        self.read(1.4)

        self.play(panel.animate.scale(0.9).move_to([0, 1.1, 0]), FadeOut(cap), run_time=0.6)

        # ---- where limits live ----
        pills = VGroup(
            self.pill("per IP", USER_C, fs=20),
            self.pill("per user / API key", OK_C, fs=20),
            self.pill("per endpoint", GOLD, fs=20),
        ).arrange(RIGHT, buff=0.4).move_to([0, -0.7, 0])
        self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.1) for p in pills],
                              lag_ratio=0.3, run_time=1.0))
        where = self.say("Enforce at the edge / API gateway — with counters shared in Redis "
                         "so every server agrees.")
        self.play(FadeIn(where), run_time=0.4)
        self.read(1.6)

        self.wipe()

        # ---- why teams add one ----
        why = Text("Why every serious API has one", font_size=27, color=GOLD, weight="BOLD")
        why.move_to([0, 2.5, 0])
        benefits = VGroup(
            self.check_line("Stops abuse & DDoS", "— absorb the flood at the door", GOOD),
            self.check_line("Fair usage", "— one tenant can't starve the rest", GOOD),
            self.check_line("Controls cost", "— cap spend on pricey / LLM calls", GOOD),
            self.check_line("Prevents cascading failure", "— back-pressure, not collapse", GOOD),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([0, 0.35, 0])
        self.play(FadeIn(why, shift=DOWN * 0.1), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(m, shift=RIGHT * 0.12) for m in benefits],
                              lag_ratio=0.35, run_time=1.8))
        self.read(1.6)

        providers = Text("In the wild:  Stripe · GitHub · Cloudflare · AWS API Gateway · "
                         "OpenAI & Anthropic APIs", font_size=20, color=MUTED)
        providers.move_to([0, -2.5, 0])
        if providers.width > 12.8:
            providers.scale_to_fit_width(12.8)
        self.play(FadeIn(providers), run_time=0.5)
        self.read(1.4)

        self.play(FadeOut(VGroup(why, benefits, providers)), run_time=0.6)
        k = Text("Rate limiting is the bouncer for your backend:", font_size=31, color=INK, weight="BOLD")
        k2 = Text("let the good traffic in, keep the flood out.", font_size=31, color=GOLD, weight="BOLD")
        VGroup(k, k2).arrange(DOWN, buff=0.3).move_to(ORIGIN)
        self.play(FadeIn(k, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(k2, shift=UP * 0.1), run_time=0.6)
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_flood()
        self.scene_limiter()
        self.scene_bucket()
        self.scene_algorithms()
        self.scene_practice()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_RLBase):
    def construct(self):
        self.play_intro()


class Flood(_RLBase):
    def construct(self):
        self.scene_flood()


class Limiter(_RLBase):
    def construct(self):
        self.scene_limiter()


class TokenBucket(_RLBase):
    def construct(self):
        self.scene_bucket()


class Algorithms(_RLBase):
    def construct(self):
        self.scene_algorithms()


class Practice(_RLBase):
    def construct(self):
        self.scene_practice()


class Outro(_RLBase):
    def construct(self):
        self.play_outro()


class RateLimiting(_RLBase):
    """The whole ~3½-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    RateLimiting().render()

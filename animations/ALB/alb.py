"""What is an ALB? — a short, house-style explainer.

An ALB (Application Load Balancer) is AWS's managed Layer 7 load balancer: one
front door that receives every HTTP(S) request for your app and forwards each
one to a healthy server behind it. Because it speaks HTTP, it can route by
path, hostname and headers, check every target's health, span availability
zones, and scale itself.

The film builds the idea in six beats:

    1. FrontDoor — many servers, one DNS name: what a load balancer is for
    2. Anatomy   — listener -> rules -> target groups -> targets (the real chain,
                   with the real AWS CLI call that wires a rule)
    3. Routing   — the Layer 7 superpower: route by path and host, live
    4. Health    — health checks: unhealthy targets are routed around (real
                   target-group defaults: 30 s interval, 2 fails out, 5 passes in)
    5. Layers    — Layer 7 (ALB) vs Layer 4 (NLB): the envelope and the letter
    6. Scale     — one node per availability zone, auto-registration, auto-scaling

Everything is drawn with Manim ``Text`` (Pango), never ``Tex`` — no LaTeX. Scenes
render individually (``FrontDoor``, ``Anatomy``, ``Routing``, ``Health``,
``Layers``, ``Scale``, ``Intro``, ``Outro``) or as one film (``WhatIsAnALB``).

Env knobs:
    ALB_QUICK=1   collapse every hold for a fast sanity render
    ALB_DELAY=..  reading-rhythm multiplier for small inter-step pauses
    ALB_READ=..   absolute hold after a caption lands (seconds) — reading time
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

# --- crisp text (shared house fix) ----------------------------------------- #
# Manim's ``Text`` mangles letter/word spacing below ~20 pt. Render every glyph
# at a large base size and scale the mobject *down* — spacing stays crisp. This
# shadow is MANDATORY (it also fixes super/subscripts rendered by helpers).
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("ALB_QUICK") == "1"
DELAY = float(os.environ.get("ALB_DELAY", 0.28 if QUICK else 1.0))
READ = float(os.environ.get("ALB_READ", 0.32 if QUICK else 2.35))
ANIM_SLOW = 1.0 if QUICK else 1.25
END_HOLD = 0.2 if QUICK else 2.1  # settle held on a finished scene before it wipes

# ---- palette (dark house style, shared across the series) ----------------- #
BG = "#0E1117"          # dark slate background
PANEL = "#151A23"       # panel fill
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
FAINT = "#2A3140"       # gridlines / faint wires
GOLD = "#FFD166"        # accent / rules

ALB_C = "#FF9900"       # the ALB — AWS orange — HERO
CLIENT_C = "#5B8DEF"    # clients / browsers (indigo blue)
WEB_C = "#38BDF8"       # web target group / NLB (sky cyan)
API_C = "#C792EA"       # api target group (violet)
ADMIN_C = GOLD          # admin target group (gold)
GOOD = "#3DD68C"        # healthy / passing checks (green)
BAD = "#FF5C5C"         # failing / unhealthy (red) — used sparingly
WARN = "#FF8C42"        # load / warnings (orange)
ACCENT = GOLD

MONO = "Menlo"          # code / addresses / HTTP
FONT = "Helvetica Neue"
_BaseText.set_default(font=FONT)

# ---- code-panel syntax colours (AWS CLI) ----------------------------------- #
CODE_FS = 19
PLAIN = "#D6DEEB"       # default code text
COMMENT = "#5F6B7E"     # comments (grey-blue)
FUNC = "#82AAFF"        # command names
STR = "#C3E88D"         # strings

CLI_T2C = {
    "aws elbv2 create-rule": FUNC,
    "path-pattern": GOLD,
    "'/api/*'": STR,
    "forward": GOOD,
    "$LISTENER": CLIENT_C,
    "$API_TG": API_C,
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
def txt(text, fs=24, color=INK, weight="NORMAL", font=None, slant=None, **extra):
    """``Text`` with optional kwargs, skipping None so Pango never chokes."""
    kw = {"font_size": fs, "color": color, "weight": weight, **extra}
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
    """Arrow between two EXPLICIT points (pass .get_right()/.get_left(), never a
    bare Mobject — get_boundary_point on a compound glyph renders diagonally)."""
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


# ---- glyphs (all hand-drawn Manim mobjects, no image assets) -------------- #
def fan_mark(color=INK, s=1.0):
    """One dot fanning out into three — the load balancer's mark."""
    src = Dot(radius=0.06 * s, color=color).move_to([-0.3 * s, 0, 0])
    outs = VGroup(*[Line([-0.3 * s, 0, 0], [0.3 * s, y * s, 0],
                         stroke_color=color, stroke_width=3)
                    for y in (0.22, 0.0, -0.22)])
    tips = VGroup(*[Dot(radius=0.045 * s, color=color).move_to([0.3 * s, y * s, 0])
                    for y in (0.22, 0.0, -0.22)])
    return VGroup(outs, src, tips)


def alb_card(w=2.8, h=1.6, title="ALB", sub="Application Load Balancer",
             color=ALB_C, fs_title=26, fs_sub=14):
    """The hero: the ALB as a titled AWS-orange card with a fan-out mark."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.15,
                            stroke_color=color, stroke_width=3.2,
                            fill_color=color, fill_opacity=0.10)
    mark = fan_mark(color, s=0.78)
    name = txt(title, fs=fs_title, color=INK, weight="BOLD")
    head = VGroup(mark, name).arrange(RIGHT, buff=0.18)
    if head.width > w - 0.4:
        head.scale((w - 0.4) / head.width)
    if sub:
        subt = txt(sub, fs=fs_sub, color=color)
        if subt.width > w - 0.3:
            subt.scale((w - 0.3) / subt.width)
        inner = VGroup(head, subt).arrange(DOWN, buff=0.14).move_to(body)
        g = VGroup(body, inner)
        g.subt = subt
    else:
        inner = VGroup(head).move_to(body)
        g = VGroup(body, inner)
    g.body = body
    g.mark = mark
    return g


def target_box(title="web-1", color=WEB_C, w=1.7, h=1.0, healthy=True, fs=15):
    """A backend target: a titled box with a small health LED and rack bars."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.12,
                            stroke_color=color, stroke_width=2.6,
                            fill_color=color, fill_opacity=0.08)
    bar = RoundedRectangle(width=w, height=0.32, corner_radius=0.12, stroke_width=0,
                           fill_color=color, fill_opacity=0.16)
    bar.align_to(body, UP)
    led = Dot(radius=0.055, color=GOOD if healthy else BAD)
    led.move_to([body.get_left()[0] + 0.21, bar.get_center()[1], 0])
    ttl = txt(title, fs=fs, color=INK, weight="BOLD")
    if ttl.width > w - 0.55:
        ttl.scale((w - 0.55) / ttl.width)
    ttl.next_to(led, RIGHT, buff=0.12)
    ttl.set_y(bar.get_center()[1])
    racks = VGroup(*[RoundedRectangle(width=w - 0.45, height=0.1, corner_radius=0.05,
                                      stroke_width=0, fill_color=color, fill_opacity=0.18)
                     for _ in range(2)]).arrange(DOWN, buff=0.11)
    racks.move_to([body.get_center()[0], body.get_center()[1] - 0.17, 0])
    g = VGroup(body, bar, led, ttl, racks)
    g.body = body
    g.led = led
    return g


def tg_frame(title, color, w=3.3, h=1.55):
    """A target group: a dashed, tinted frame with its name on the border."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.14, stroke_width=0,
                            fill_color=color, fill_opacity=0.05)
    rim = RoundedRectangle(width=w, height=h, corner_radius=0.14,
                           stroke_color=color, stroke_width=2.2)
    rim = DashedVMobject(rim, num_dashes=max(26, int((w + h) * 6)), dashed_ratio=0.6)
    tag_t = txt(title, fs=15, color=color, weight="BOLD")
    tag = plate(tag_t, pad_x=0.1, pad_y=0.04, op=1.0)
    tag.move_to(body.get_corner(UL) + RIGHT * (tag.width / 2 + 0.3))
    g = VGroup(body, rim, tag)
    g.body = body
    g.tag = tag
    return g


def tg_card(title, color, w=2.6, h=1.2):
    """A compact target-group card (name + rack bars) for busy scenes."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.13,
                            stroke_color=color, stroke_width=2.8,
                            fill_color=color, fill_opacity=0.09)
    ttl = txt(title, fs=17, color=INK, weight="BOLD")
    if ttl.width > w - 0.4:
        ttl.scale((w - 0.4) / ttl.width)
    ttl.move_to([body.get_center()[0], body.get_center()[1] + h * 0.22, 0])
    racks = VGroup(*[RoundedRectangle(width=w - 0.5, height=0.11, corner_radius=0.055,
                                      stroke_width=0, fill_color=color, fill_opacity=0.22)
                     for _ in range(2)]).arrange(DOWN, buff=0.1)
    racks.move_to([body.get_center()[0], body.get_center()[1] - h * 0.18, 0])
    g = VGroup(body, ttl, racks)
    g.body = body
    g.ttl = ttl
    return g


def az_frame(title, w=5.9, h=3.35):
    """An availability zone: a muted dashed frame with its name on the border."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.16, stroke_width=0,
                            fill_color=PANEL, fill_opacity=0.3)
    rim = RoundedRectangle(width=w, height=h, corner_radius=0.16,
                           stroke_color=MUTED, stroke_width=1.8)
    rim = DashedVMobject(rim, num_dashes=max(30, int((w + h) * 5)), dashed_ratio=0.55)
    rim.set_stroke(opacity=0.7)
    tag_t = txt(title, fs=14, color=MUTED)
    tag = plate(tag_t, pad_x=0.1, pad_y=0.04, op=1.0)
    tag.move_to(body.get_corner(UL) + RIGHT * (tag.width / 2 + 0.3))
    g = VGroup(body, rim, tag)
    g.body = body
    g.tag = tag
    return g


def browser(label="GET /", color=CLIENT_C, w=2.1, h=1.35):
    """A client: a little browser window with a title bar and a request line."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.1,
                            stroke_color=color, stroke_width=2.6,
                            fill_color=color, fill_opacity=0.07)
    bar = RoundedRectangle(width=w, height=0.34, corner_radius=0.1, stroke_width=0,
                           fill_color=color, fill_opacity=0.2)
    bar.align_to(body, UP)
    dots = VGroup(*[Dot(radius=0.035, color=color) for _ in range(3)]).arrange(RIGHT, buff=0.08)
    dots.move_to([body.get_left()[0] + 0.28, bar.get_center()[1], 0])
    lbl = mono(label, fs=17, color=INK)
    if lbl.width > w - 0.3:
        lbl.scale((w - 0.3) / lbl.width)
    lbl.move_to([body.get_center()[0], body.get_center()[1] - 0.12, 0])
    g = VGroup(body, bar, dots, lbl)
    g.body = body
    g.label = lbl
    return g


def dns_pill(name="shop-alb-8f3d21a7.eu-west-1.elb.amazonaws.com", fs=13.5):
    """The ALB's DNS name, as AWS hands it to you."""
    t = mono(name, fs=fs, color=INK)
    if t.width > 5.6:
        t.scale_to_fit_width(5.6)
    box = RoundedRectangle(width=t.width + 0.4, height=t.height + 0.28,
                           corner_radius=0.12, stroke_color=ALB_C, stroke_width=2,
                           fill_color=ALB_C, fill_opacity=0.07)
    box.move_to(t)
    g = VGroup(box, t)
    g.box = box
    return g


def rule_row(num, cond, tg, color, fs=15):
    """One listener rule: a priority, a condition, and a forward action."""
    n = txt(num, fs=12.5, color=MUTED)
    c = txt(cond, fs=fs, color=INK)
    a = Arrow(ORIGIN, RIGHT * 0.5, buff=0, stroke_width=3, color=MUTED,
              max_tip_length_to_length_ratio=0.4, tip_length=0.14)
    ch = chip(tg, color, fs=13.5, h=0.4, fill=0.18)
    row = VGroup(n, c, a, ch).arrange(RIGHT, buff=0.18)
    row.cond = c
    row.chip = ch
    return row


def request_card(path, host, cookie="sid=9f2c", method="GET", w=3.0):
    """A real-looking HTTP request, with the path and host as separate pieces
    so the scene can highlight exactly what the ALB reads."""
    l1 = VGroup(mono(method, fs=14, color=CLIENT_C),
                mono(path, fs=14, color=INK),
                mono("HTTP/1.1", fs=14, color=MUTED)).arrange(RIGHT, buff=0.14)
    l2 = VGroup(mono("Host:", fs=14, color=MUTED),
                mono(host, fs=14, color=INK)).arrange(RIGHT, buff=0.14)
    l3 = VGroup(mono("Cookie:", fs=14, color=MUTED),
                mono(cookie, fs=14, color=MUTED)).arrange(RIGHT, buff=0.14)
    lines = VGroup(l1, l2, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    if lines.width > w - 0.36:
        lines.scale((w - 0.36) / lines.width)
    bg = RoundedRectangle(width=w, height=lines.height + 0.82, corner_radius=0.12,
                          stroke_color=FAINT, stroke_width=2,
                          fill_color=PANEL, fill_opacity=1.0)
    bar = RoundedRectangle(width=w, height=0.34, corner_radius=0.12, stroke_width=0,
                           fill_color=CLIENT_C, fill_opacity=0.18)
    bar.move_to(bg).align_to(bg, UP)
    ttl = txt("HTTP request", fs=12, color=MUTED).move_to(bar)
    lines.move_to([bg.get_left()[0] + 0.2 + lines.width / 2,
                   (bar.get_bottom()[1] + bg.get_bottom()[1]) / 2, 0])
    g = VGroup(bg, bar, ttl, lines)
    g.body = bg
    g.path = l1[1]
    g.host = l2[1]
    return g


def envelope(w=3.1, h=1.8, color=MUTED):
    """A sealed letter: the address outside, the message inside."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.08,
                            stroke_color=color, stroke_width=2.6,
                            fill_color=PANEL, fill_opacity=1.0)
    flap = VGroup(
        Line(body.get_corner(UL), [body.get_center()[0], body.get_center()[1] + h * 0.1, 0],
             stroke_color=color, stroke_width=2.2),
        Line(body.get_corner(UR), [body.get_center()[0], body.get_center()[1] + h * 0.1, 0],
             stroke_color=color, stroke_width=2.2),
    )
    addr = mono("to 52.31.8.10 : 443", fs=14, color=INK)
    addr.move_to([body.get_center()[0], body.get_center()[1] - h * 0.24, 0])
    stamp_sq = RoundedRectangle(width=0.34, height=0.28, corner_radius=0.04,
                                stroke_color=color, stroke_width=1.6,
                                fill_color=color, fill_opacity=0.18)
    stamp_sq.move_to(body.get_corner(UR) + LEFT * 0.33 + DOWN * 0.29)
    g = VGroup(body, flap, addr, stamp_sq)
    g.body = body
    g.addr = addr
    return g


def letter_card(w=2.55, h=1.35):
    """The message inside the envelope: the HTTP request itself."""
    paper = RoundedRectangle(width=w, height=h, corner_radius=0.06,
                             stroke_color="#C9C4B8", stroke_width=1.6,
                             fill_color="#F2EFE9", fill_opacity=1.0)
    lines = VGroup(
        mono("GET /api/orders HTTP/1.1", fs=11.5, color="#1B2430"),
        mono("Host: shop.com", fs=11.5, color="#1B2430"),
        mono("Cookie: sid=9f2c", fs=11.5, color="#6B7484"),
    ).arrange(DOWN, aligned_edge=LEFT, buff=0.13)
    if lines.width > w - 0.3:
        lines.scale((w - 0.3) / lines.width)
    lines.move_to(paper)
    g = VGroup(paper, lines)
    g.paper = paper
    g.lines = lines
    return g


# ========================================================================== #
class _ALBBase(Scene):
    def setup(self):
        self.camera.background_color = BG
        self.hlrect = None

    # ---- timing helpers --------------------------------------------------- #
    def play(self, *anims, **kwargs):
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

    def swap_cap(self, old, new_text, **kw):
        """Replace the current bottom caption with a new one; return it."""
        new = self.say(new_text, **kw)
        if old is None:
            self.play(FadeIn(new), run_time=0.5)
        else:
            self.play(ReplacementTransform(old, new), run_time=0.5)
        return new

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

    # ---- code panel ------------------------------------------------------- #
    def code_panel(self, spec, table=CLI_T2C, title="terminal", fs=CODE_FS,
                   indent_unit=0.46, line_buff=0.16, target_h=5.6, target_w=7.2):
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

    # ---- house-style intro / outro cards ---------------------------------- #
    def play_intro(self):
        header = Text("What is an ALB?", font_size=68, color=INK, weight="BOLD")
        if header.width > 12.6:
            header.scale_to_fit_width(12.6)
        line = Line(
            [header.get_left()[0] - 0.8, header.get_bottom()[1] - 0.42, 0],
            [header.get_right()[0] + 0.8, header.get_bottom()[1] - 0.42, 0],
        ).set_stroke(width=3, color=GOLD)
        mark = fan_mark(GOLD, s=1.2).move_to(line.get_right() + RIGHT * 0.45 + UP * 0.32)
        writer = Text("Created by Ptolémé", font_size=28, color=CLIENT_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.5)
        self.play(FadeIn(mark, shift=DOWN * 0.15), run_time=0.6)
        self.read(0.7)
        sub = Text("One managed front door for your app on AWS.",
                   font_size=29, color=MUTED)
        if sub.width > 12.6:
            sub.scale_to_fit_width(12.6)
        sub.move_to(header)
        self.play(Transform(header, sub), FadeOut(mark), run_time=1.0)
        self.read(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        src = Text("AWS · Application Load Balancer · System Design",
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
        recap = Text("Listener, rules, target groups. Now you know the whole machine.",
                     font_size=26, color=ACCENT)
        if recap.width > 12.4:
            recap.scale_to_fit_width(12.4)
        recap.next_to(writer, DOWN, buff=0.5)
        self.play(Write(header), Create(line), run_time=1.5)
        self.read(0.7)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.play(FadeIn(recap), run_time=0.8)
        self.read(1.6)
        self.play(FadeOut(VGroup(header, line, writer, recap)), run_time=1.3)
        self.card_wait(0.5)

    # ---- request-dot helper ---------------------------------------------- #
    def send_dot(self, a, b, color=CLIENT_C, r=0.085, rt=0.6, add=True):
        d = Dot(a, radius=r, color=color)
        if add:
            self.add(d)
        self.play(d.animate.move_to(b), run_time=rt, rate_func=rate_functions.ease_in_out_sine)
        return d

    # ====================================================================== #
    # Scene 1 — One address, many servers: what the front door is for
    # ====================================================================== #
    def scene_frontdoor(self):
        header = self.section_header("One address, many servers", ALB_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        client = browser("GET /", CLIENT_C).move_to([-5.15, 0.9, 0])
        c_lbl = txt("client", fs=17, color=CLIENT_C).next_to(client, DOWN, buff=0.2)
        targets = VGroup(*[target_box(f"web-{i+1}", WEB_C, w=1.9, h=1.0)
                           for i in range(3)])
        for t, y in zip(targets, (2.25, 0.9, -0.45)):
            t.move_to([4.75, y, 0])

        self.play(FadeIn(client, shift=RIGHT * 0.12), FadeIn(c_lbl), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(t, shift=LEFT * 0.12) for t in targets],
                              lag_ratio=0.15, run_time=0.8))
        cap = self.say("Your app runs on three identical servers. Which one should a client call?")
        self.play(FadeIn(cap), run_time=0.5)

        dashed = VGroup(*[DashedLine(client.get_right(), t.get_left(),
                                     stroke_color=MUTED, stroke_width=2, stroke_opacity=0.55)
                          for t in targets])
        qmark = txt("?", fs=46, color=GOLD, weight="BOLD").move_to([-0.3, 1.45, 0])
        self.play(LaggedStart(*[Create(d) for d in dashed], lag_ratio=0.15, run_time=0.8))
        self.play(FadeIn(qmark, scale=0.7), run_time=0.4)
        self.read(1.3)

        # the ALB lands in front of the pool
        alb = alb_card(w=2.8, h=1.6).move_to([-0.5, 0.9, 0])
        self.play(FadeOut(dashed), FadeOut(qmark), run_time=0.35)
        self.play(GrowFromCenter(alb), run_time=0.7)
        cap = self.swap_cap(cap, "An Application Load Balancer, an ALB, is one managed front door in front of them all.",
                            color=ALB_C)
        a_in = arr(client.get_right(), alb.body.get_left(), color=CLIENT_C, sw=3.5)
        fans = VGroup(*[arr(alb.body.get_right(), t.get_left(), color=MUTED, sw=3.0)
                        for t in targets])
        self.play(GrowArrow(a_in), run_time=0.4)
        self.play(LaggedStart(*[GrowArrow(a) for a in fans], lag_ratio=0.15, run_time=0.7))
        self.read(1.3)

        # the single DNS name AWS hands you
        dns = dns_pill().next_to(alb, DOWN, buff=0.3)
        self.play(FadeIn(dns, shift=UP * 0.12), run_time=0.5)
        cap = self.swap_cap(cap, "Clients only ever see one DNS name. AWS hands it to you when you create the balancer.")
        self.read(1.4)

        # requests flow: each one lands on the ALB, then on one healthy server
        cap = self.swap_cap(cap, "The ALB accepts every request, then forwards each one to a healthy server behind it.")
        for i in (0, 1, 2, 0):
            d = Dot(client.get_right() + RIGHT * 0.08, radius=0.075, color=CLIENT_C)
            self.add(d)
            self.play(d.animate.move_to(alb.body.get_left() + LEFT * 0.05),
                      run_time=0.4, rate_func=rate_functions.ease_in_out_sine)
            self.play(d.animate.move_to(targets[i].get_left() + LEFT * 0.05).set_color(ALB_C),
                      run_time=0.45, rate_func=rate_functions.ease_in_out_sine)
            self.play(Indicate(targets[i], color=WEB_C, scale_factor=1.06),
                      FadeOut(d), run_time=0.3)
        self.read(1.2)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.takeaway("One address in front, many servers behind.",
                      "The ALB is AWS's managed Layer 7 load balancer.", c2=ALB_C)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — Anatomy: listener -> rules -> target groups -> targets
    # ====================================================================== #
    def scene_anatomy(self):
        header = self.section_header("Inside the ALB", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        cap = self.say("Open one up, and every ALB is the same simple machine with three parts.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.0)

        # 1) the listener
        l_body = RoundedRectangle(width=2.0, height=1.1, corner_radius=0.13,
                                  stroke_color=ALB_C, stroke_width=2.8,
                                  fill_color=ALB_C, fill_opacity=0.08)
        l_ttl = txt("listener", fs=19, color=INK, weight="BOLD")
        l_sub = mono("HTTPS :443", fs=15, color=ALB_C)
        l_in = VGroup(l_ttl, l_sub).arrange(DOWN, buff=0.12).move_to(l_body)
        listener = VGroup(l_body, l_in).move_to([-5.35, 1.35, 0])
        self.play(FadeIn(listener, shift=RIGHT * 0.12), run_time=0.5)
        cap = self.swap_cap(cap, "A listener waits for traffic on one port and protocol. Here, HTTPS on port 443.",
                            color=ALB_C)
        self.read(1.3)

        # 2) the rules, in priority order
        r_body = RoundedRectangle(width=4.5, height=2.3, corner_radius=0.15,
                                  stroke_color=FAINT, stroke_width=2.2,
                                  fill_color=PANEL, fill_opacity=0.55).move_to([-1.45, 1.35, 0])
        r_ttl = txt("rules, in priority order", fs=14, color=MUTED)
        r_ttl.move_to([-1.45, 2.18, 0])
        row1 = rule_row("1", "path is /api/*", "api-tg", API_C)
        row2 = rule_row("2", "default: everything else", "web-tg", WEB_C)
        for r, y in ((row1, 1.5), (row2, 0.8)):
            if r.width > 4.1:
                r.scale(4.1 / r.width)
            r.move_to([-1.45, y, 0])
        a_lr = arr(listener.get_right(), r_body.get_left(), color=MUTED, sw=3.2)
        self.play(FadeIn(r_body), FadeIn(r_ttl), GrowArrow(a_lr), run_time=0.55)
        self.play(FadeIn(row1, shift=DOWN * 0.08), run_time=0.45)
        self.play(FadeIn(row2, shift=DOWN * 0.08), run_time=0.45)
        cap = self.swap_cap(cap, "The listener keeps an ordered list of rules, and checks each request from the top down.")
        self.read(1.4)

        # 3) the target groups
        api_tg = tg_frame("api-tg", API_C, w=3.3, h=1.55).move_to([4.55, 2.1, 0])
        api_targets = VGroup(target_box("api-1", API_C, w=1.35, h=0.85, fs=13),
                             target_box("api-2", API_C, w=1.35, h=0.85, fs=13))
        api_targets.arrange(RIGHT, buff=0.22).move_to([4.55, 2.0, 0])
        web_tg = tg_frame("web-tg", WEB_C, w=3.3, h=1.55).move_to([4.55, 0.0, 0])
        web_targets = VGroup(target_box("web-1", WEB_C, w=1.35, h=0.85, fs=13),
                             target_box("web-2", WEB_C, w=1.35, h=0.85, fs=13))
        web_targets.arrange(RIGHT, buff=0.22).move_to([4.55, -0.1, 0])
        a_r1 = arr([0.8, 1.5, 0], api_tg.body.get_left(), color=API_C, sw=3.0)
        a_r2 = arr([0.8, 0.8, 0], web_tg.body.get_left(), color=WEB_C, sw=3.0)
        self.play(FadeIn(api_tg), FadeIn(api_targets), run_time=0.5)
        self.play(FadeIn(web_tg), FadeIn(web_targets), run_time=0.5)
        self.play(GrowArrow(a_r1), GrowArrow(a_r2), run_time=0.5)
        cap = self.swap_cap(cap, "Each rule forwards its matches to a target group, which is a named pool of servers.",
                            color=API_C)
        self.read(1.5)

        # what a target can be
        kinds = VGroup(
            chip("EC2 instances", MUTED, fs=16, h=0.5, fill=0.1),
            chip("containers", MUTED, fs=16, h=0.5, fill=0.1),
            chip("private IPs", MUTED, fs=16, h=0.5, fill=0.1),
            chip("Lambda functions", MUTED, fs=16, h=0.5, fill=0.1),
        ).arrange(RIGHT, buff=0.3).move_to([0, -1.95, 0])
        kinds_lbl = txt("a target can be:", fs=15, color=MUTED)
        kinds_lbl.next_to(kinds, UP, buff=0.24).align_to(kinds, LEFT)
        self.play(FadeIn(kinds_lbl), run_time=0.3)
        self.play(LaggedStart(*[FadeIn(k, scale=0.85) for k in kinds],
                              lag_ratio=0.12, run_time=0.8))
        cap = self.swap_cap(cap, "A target can be an EC2 instance, a container, a private IP address, or a Lambda function.")
        self.read(1.5)

        # the real CLI call that wires the /api/* rule
        self.play(FadeOut(Group(*[m for m in self.mobjects if m is not header])), run_time=0.6)
        cap = self.swap_cap(None, "This is not pseudocode. One real CLI call creates the /api/* rule.")
        spec = [
            (0, "aws elbv2 create-rule \\"),
            (1, "--listener-arn  $LISTENER \\"),
            (1, "--priority 10 \\"),
            (1, "--conditions Field=path-pattern,Values='/api/*' \\"),
            (1, "--actions Type=forward,TargetGroupArn=$API_TG"),
        ]
        panel, lines = self.code_panel(spec, title="terminal", target_h=3.4)
        panel.move_to([0, 0.5, 0])
        self.play(FadeIn(panel, shift=UP * 0.15), run_time=0.8)
        self.read(1.1)
        self.focus(panel, lines, [3], color=GOLD)
        cap = self.swap_cap(cap, "The condition reads the request's path before any server is chosen.", color=GOLD)
        self.read(1.3)
        self.focus(panel, lines, [4], color=GOOD)
        cap = self.swap_cap(cap, "The action forwards every match to your api target group.", color=GOOD)
        self.read(1.3)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.hlrect = None
        self.takeaway("Listener, rules, target group, target.",
                      "Every request that reaches an ALB walks this exact chain.")
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Routing by content: the Layer 7 superpower
    # ====================================================================== #
    def scene_routing(self):
        header = self.section_header("Routing by content", API_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        alb = alb_card(w=2.5, h=1.3, sub="Layer 7", fs_title=24).move_to([-0.95, 1.95, 0])
        r_body = RoundedRectangle(width=4.7, height=2.35, corner_radius=0.15,
                                  stroke_color=FAINT, stroke_width=2.2,
                                  fill_color=PANEL, fill_opacity=0.55).move_to([-0.95, -0.8, 0])
        r_ttl = txt("listener rules", fs=14, color=MUTED).move_to([-0.95, 0.08, 0])
        rows = VGroup(
            rule_row("1", "path is /api/*", "api-tg", API_C, fs=14.5),
            rule_row("2", "host is admin.shop.com", "admin-tg", ADMIN_C, fs=14.5),
            rule_row("3", "default: everything else", "web-tg", WEB_C, fs=14.5),
        )
        for r, y in zip(rows, (-0.5, -1.1, -1.7)):
            if r.width > 4.3:
                r.scale(4.3 / r.width)
            r.move_to([-0.95, y, 0])
        a_ar = arr(alb.body.get_bottom(), [-0.95, 0.38, 0], color=MUTED, sw=2.8, buff=0.08)

        tgs = VGroup(
            tg_card("api-tg", API_C, w=2.6, h=1.2).move_to([4.8, 2.2, 0]),
            tg_card("admin-tg", ADMIN_C, w=2.6, h=1.2).move_to([4.8, 0.55, 0]),
            tg_card("web-tg", WEB_C, w=2.6, h=1.2).move_to([4.8, -1.1, 0]),
        )
        fans = VGroup(*[arr(alb.body.get_right(), tg.body.get_left(),
                            color=MUTED, sw=2.6) for tg in tgs])
        for f in fans:
            f.set_stroke(opacity=0.55)

        self.play(GrowFromCenter(alb), run_time=0.6)
        self.play(FadeIn(r_body), FadeIn(r_ttl), GrowArrow(a_ar), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(r, shift=DOWN * 0.08) for r in rows],
                              lag_ratio=0.12, run_time=0.8))
        self.play(LaggedStart(*[FadeIn(tg, shift=LEFT * 0.1) for tg in tgs],
                              lag_ratio=0.12, run_time=0.8))
        self.play(LaggedStart(*[GrowArrow(f) for f in fans], lag_ratio=0.1, run_time=0.6))
        cap = self.say("An ALB speaks HTTP, so it reads each request before choosing where it goes.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.4)

        def route(card, hi_piece, row_idx, tg_idx, color, cap_text, cap_old):
            hi = SurroundingRectangle(hi_piece, color=GOLD, buff=0.06, stroke_width=2.5)
            row_hl = RoundedRectangle(width=4.4, height=0.52, corner_radius=0.08,
                                      stroke_width=0, fill_color=color, fill_opacity=0.14)
            row_hl.move_to(rows[row_idx])
            c = self.swap_cap(cap_old, cap_text, color=color)
            self.play(Create(hi), run_time=0.4)
            d = self.send_dot(card.body.get_right() + RIGHT * 0.06,
                              alb.body.get_left() + LEFT * 0.05, color=CLIENT_C, rt=0.5)
            self.play(FadeIn(row_hl), run_time=0.35)
            self.beat(0.6)
            self.play(fans[tg_idx].animate.set_stroke(color, width=4.2, opacity=1.0),
                      run_time=0.3)
            self.play(d.animate.move_to(tgs[tg_idx].body.get_left() + LEFT * 0.05).set_color(color),
                      run_time=0.55, rate_func=rate_functions.ease_in_out_sine)
            self.play(Indicate(tgs[tg_idx], color=color, scale_factor=1.06),
                      FadeOut(d), run_time=0.4)
            self.read(1.2)
            self.play(FadeOut(hi), FadeOut(row_hl),
                      fans[tg_idx].animate.set_stroke(MUTED, width=2.6, opacity=0.55),
                      run_time=0.35)
            return c

        # request 1: the path matches /api/*
        card1 = request_card("/api/orders", "shop.com").move_to([-5.2, 1.7, 0])
        self.play(FadeIn(card1, shift=RIGHT * 0.12), run_time=0.5)
        cap = self.swap_cap(cap, "The first request asks for /api/orders.")
        self.read(0.8)
        cap = route(card1, card1.path, 0, 0, API_C,
                    "Its path matches /api/*, so rule 1 fires and it lands on the api servers.", cap)

        # request 2: the host header matches the admin subdomain
        card2 = request_card("/dashboard", "admin.shop.com").move_to([-5.2, 1.7, 0])
        self.play(FadeOut(card1), FadeIn(card2), run_time=0.5)
        cap = self.swap_cap(cap, "The next request is for the admin subdomain.")
        self.read(0.8)
        cap = route(card2, card2.host, 1, 1, ADMIN_C,
                    "Its host header matches rule 2, so it goes to the admin servers.", cap)

        # request 3: nothing matches, the default rule catches it
        card3 = request_card("/checkout", "shop.com").move_to([-5.2, 1.7, 0])
        self.play(FadeOut(card2), FadeIn(card3), run_time=0.5)
        cap = route(card3, card3.path, 2, 2, WEB_C,
                    "Nothing above matches /checkout, so the default rule sends it to the web servers.", cap)

        cap = self.swap_cap(cap, "Three different services behind one balancer, one DNS name, one certificate.",
                            color=ALB_C)
        self.read(1.5)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.takeaway("Paths, hostnames, headers: the ALB routes on content.",
                      "One front door can serve your entire platform.", c2=API_C)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Health checks: failures are routed around
    # ====================================================================== #
    def scene_health(self):
        header = self.section_header("Health checks", GOOD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        alb = alb_card(w=2.3, h=1.3, sub=None, fs_title=24).move_to([-5.2, -0.3, 0])
        frame = tg_frame("web-tg", WEB_C, w=4.6, h=3.5).move_to([2.35, -0.3, 0])
        targets = VGroup(*[target_box(f"web-{i+1}", WEB_C, w=1.7, h=0.95, fs=14)
                           for i in range(3)])
        for t, y in zip(targets, (0.75, -0.3, -1.35)):
            t.move_to([1.8, y, 0])
        wires = VGroup(*[wire(alb.body.get_right(), t.get_left(), color=WEB_C, sw=2.2, op=0.7)
                         for t in targets])

        self.play(GrowFromCenter(alb), run_time=0.5)
        self.play(FadeIn(frame), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(t, shift=LEFT * 0.1) for t in targets],
                              lag_ratio=0.15, run_time=0.7))
        self.play(*[Create(w) for w in wires], run_time=0.5)
        cap = self.say("The ALB never trusts a target blindly. It keeps checking every one of them.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.2)

        probe_lbl = VGroup(mono("GET /health", fs=15, color=GOLD),
                           txt("every 30 s", fs=14, color=MUTED)).arrange(RIGHT, buff=0.22)
        probe_lbl.move_to([2.35, 1.82, 0])
        self.play(FadeIn(probe_lbl, shift=DOWN * 0.1), run_time=0.4)
        cap = self.swap_cap(cap, "Every 30 seconds it calls each target's health route and expects an HTTP 200.",
                            color=GOLD)

        ticks = VGroup()
        for t in targets:
            d = Dot(alb.body.get_right() + RIGHT * 0.06, radius=0.06, color=GOLD)
            self.add(d)
            self.play(d.animate.move_to(t.get_left() + LEFT * 0.05),
                      run_time=0.38, rate_func=rate_functions.ease_in_out_sine)
            tick = make_tick(GOOD, sw=5, scale=0.5).next_to(t, RIGHT, buff=0.24)
            ticks.add(tick)
            self.play(FadeIn(tick, scale=0.7), FadeOut(d), run_time=0.22)
        self.read(1.1)
        self.play(FadeOut(ticks), run_time=0.3)

        defaults = VGroup(
            chip("interval 30 s", MUTED, fs=15, h=0.48, fill=0.1),
            chip("timeout 5 s", MUTED, fs=15, h=0.48, fill=0.1),
            chip("unhealthy after 2 fails", BAD, fs=15, h=0.48, fill=0.1),
            chip("healthy after 5 passes", GOOD, fs=15, h=0.48, fill=0.1),
        ).arrange(RIGHT, buff=0.28).move_to([0, -2.68, 0])
        self.play(LaggedStart(*[FadeIn(c, scale=0.85) for c in defaults],
                              lag_ratio=0.12, run_time=0.8))
        cap = self.swap_cap(cap, "These are the real target group defaults, and every one of them is tunable.")
        self.read(1.4)

        # web-2 starts failing its checks
        sick = targets[1]
        cap = self.swap_cap(cap, "web-2 starts failing. Two bad checks in a row, and it is marked unhealthy.",
                            color=BAD)
        crosses = VGroup()
        for k in range(2):
            d = Dot(alb.body.get_right() + RIGHT * 0.06, radius=0.06, color=GOLD)
            self.add(d)
            self.play(d.animate.move_to(sick.get_left() + LEFT * 0.05),
                      run_time=0.38, rate_func=rate_functions.ease_in_out_sine)
            x = make_cross(BAD, sw=5, scale=0.5)
            x.move_to(sick.get_right() + RIGHT * (0.38 + 0.44 * k) + UP * 0.2)
            crosses.add(x)
            self.play(FadeIn(x, scale=0.7), FadeOut(d), run_time=0.22)
        sick_tag = txt("unhealthy", fs=14, color=BAD, weight="BOLD")
        sick_tag.move_to(sick.get_right() + RIGHT * 0.62 + DOWN * 0.26)
        self.play(sick.led.animate.set_color(BAD),
                  sick.body.animate.set_stroke(BAD, 2.8).set_fill(BAD, 0.08),
                  wires[1].animate.set_stroke(opacity=0.12),
                  FadeIn(sick_tag), run_time=0.6)
        self.play(Flash(sick, color=BAD, flash_radius=1.25), run_time=0.5)
        self.read(1.2)

        cap = self.swap_cap(cap, "New traffic simply flows around it. Users never notice a thing.", color=GOOD)
        for i in (0, 2, 0, 2):
            d = Dot(alb.body.get_right() + RIGHT * 0.06, radius=0.07, color=CLIENT_C)
            self.add(d)
            self.play(d.animate.move_to(targets[i].get_left() + LEFT * 0.05).set_color(GOOD),
                      run_time=0.36, rate_func=rate_functions.ease_in_out_sine)
            self.play(FadeOut(d), run_time=0.1)
        self.read(1.2)

        # recovery: five passes in a row and it rejoins
        cap = self.swap_cap(cap, "When it passes five checks in a row, it rejoins the pool automatically.",
                            color=GOOD)
        passes = pill("5 checks pass", GOOD, fs=12.5)
        passes.move_to(sick.get_right() + RIGHT * (0.22 + passes.width / 2))
        self.play(FadeOut(crosses), FadeOut(sick_tag), FadeIn(passes, shift=UP * 0.1), run_time=0.5)
        self.play(sick.led.animate.set_color(GOOD),
                  sick.body.animate.set_stroke(WEB_C, 2.6).set_fill(WEB_C, 0.08),
                  wires[1].animate.set_stroke(opacity=0.7), run_time=0.6)
        d = self.send_dot(alb.body.get_right() + RIGHT * 0.06,
                          sick.get_left() + LEFT * 0.05, color=CLIENT_C, rt=0.45)
        self.play(Indicate(sick, color=GOOD, scale_factor=1.06), FadeOut(d), FadeOut(passes),
                  run_time=0.45)
        self.read(1.3)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.takeaway("Traffic goes only to targets that keep passing their checks.",
                      "Failure is routed around automatically, not fixed by hand.", c2=GOOD)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — Layer 7 vs Layer 4: the envelope and the letter
    # ====================================================================== #
    def scene_layers(self):
        header = self.section_header("Layer 7 vs Layer 4", WEB_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        cap = self.say("Why does the layer matter? Picture each request as a sealed letter.")
        self.play(FadeIn(cap), run_time=0.5)

        env = envelope(w=3.1, h=1.8).move_to([-3.7, 0.3, 0])
        letter = letter_card(w=2.55, h=1.35).move_to(env.body.get_center())
        letter.set_z_index(-2)
        self.play(FadeIn(env, scale=0.92), run_time=0.7)
        self.add(letter)  # hidden behind the opaque envelope body until it slides out
        self.read(1.2)

        # Layer 4: the NLB reads only the address on the outside
        nlb_body = RoundedRectangle(width=2.7, height=1.15, corner_radius=0.13,
                                    stroke_color=WEB_C, stroke_width=2.8,
                                    fill_color=WEB_C, fill_opacity=0.09)
        nlb_in = VGroup(txt("NLB · Layer 4", fs=19, color=WEB_C, weight="BOLD"),
                        txt("Network Load Balancer", fs=12.5, color=MUTED)).arrange(DOWN, buff=0.12)
        nlb_in.move_to(nlb_body)
        nlb = VGroup(nlb_body, nlb_in).move_to([3.3, 0.3, 0])
        addr_hi = SurroundingRectangle(env.addr, color=WEB_C, buff=0.08, stroke_width=2.5)
        a_nlb = arr(env.body.get_right(), nlb_body.get_left(), color=WEB_C, sw=3.0)
        cap = self.swap_cap(cap, "A Layer 4 balancer, like the NLB, reads only the outside: an IP address and a port.",
                            color=WEB_C)
        self.play(FadeIn(nlb, shift=LEFT * 0.12), run_time=0.5)
        self.play(Create(addr_hi), GrowArrow(a_nlb), run_time=0.5)
        self.read(1.5)

        # Layer 7: the ALB opens it and reads the HTTP inside
        alb_body = RoundedRectangle(width=2.7, height=1.15, corner_radius=0.13,
                                    stroke_color=ALB_C, stroke_width=2.8,
                                    fill_color=ALB_C, fill_opacity=0.09)
        alb_in = VGroup(txt("ALB · Layer 7", fs=19, color=ALB_C, weight="BOLD"),
                        txt("Application Load Balancer", fs=12.5, color=MUTED)).arrange(DOWN, buff=0.12)
        alb_in.move_to(alb_body)
        albc = VGroup(alb_body, alb_in).move_to([3.3, 2.05, 0])
        self.play(FadeIn(albc, shift=LEFT * 0.12), run_time=0.5)
        cap = self.swap_cap(cap, "An ALB works at Layer 7. It opens the envelope and reads the HTTP inside.",
                            color=ALB_C)
        self.play(letter.animate.move_to([-3.7, 2.05, 0]), run_time=0.9,
                  rate_func=rate_functions.ease_in_out_sine)
        a_alb = arr(letter.paper.get_right(), alb_body.get_left(), color=ALB_C, sw=3.0)
        letter_hi = SurroundingRectangle(letter.lines, color=ALB_C, buff=0.08, stroke_width=2.5)
        self.play(GrowArrow(a_alb), Create(letter_hi), run_time=0.5)
        self.read(1.4)
        cap = self.swap_cap(cap, "The path, the host, the cookies: that is the content it can route on.",
                            color=ALB_C)
        self.read(1.3)

        # side-by-side: what each one gives you
        self.play(FadeOut(Group(env, letter, nlb, albc, addr_hi, letter_hi, a_nlb, a_alb)),
                  run_time=0.6)

        def feature_col(title, color, rows, x):
            t = txt(title, fs=23, color=color, weight="BOLD")
            items = VGroup(*[VGroup(make_tick(color, sw=5, scale=0.5),
                                    txt(r, fs=18, color=INK)).arrange(RIGHT, buff=0.22)
                             for r in rows]).arrange(DOWN, aligned_edge=LEFT, buff=0.38)
            g = VGroup(t, items).arrange(DOWN, buff=0.45)
            if g.width > 5.9:
                g.scale(5.9 / g.width)
            g.move_to([x, 0.35, 0])
            return g

        col_alb = feature_col("ALB · Layer 7", ALB_C,
                              ["routes by path, host and headers",
                               "terminates HTTPS with your certificate",
                               "speaks WebSockets and gRPC"], -3.4)
        col_nlb = feature_col("NLB · Layer 4", WEB_C,
                              ["forwards raw TCP and UDP",
                               "millions of requests per second",
                               "one static IP per zone"], 3.4)
        divider = Line([0, 2.0, 0], [0, -1.3, 0], stroke_color=FAINT, stroke_width=2)
        self.play(FadeIn(col_alb, shift=UP * 0.1), run_time=0.6)
        self.play(Create(divider), FadeIn(col_nlb, shift=UP * 0.1), run_time=0.6)
        cap = self.swap_cap(cap, "Both are AWS Elastic Load Balancers. They just read different layers of each request.")
        self.read(1.7)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.takeaway("Serving an HTTP app? You want the ALB.",
                      "Need raw TCP speed or a static IP? That is the NLB.", c2=WEB_C)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 6 — Zones and scale: no single point of failure, no resizing
    # ====================================================================== #
    def scene_scale(self):
        header = self.section_header("Zones and scale", CLIENT_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        cap = self.say("One more thing: the ALB itself is not a single machine either.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.0)

        az_a = az_frame("zone a (eu-west-1a)", w=5.9, h=3.35).move_to([-3.5, -0.75, 0])
        az_b = az_frame("zone b (eu-west-1b)", w=5.9, h=3.35).move_to([3.5, -0.75, 0])
        node_a = alb_card(w=2.0, h=0.9, title="ALB node", sub=None, fs_title=17).move_to([-3.5, 0.35, 0])
        node_b = alb_card(w=2.0, h=0.9, title="ALB node", sub=None, fs_title=17).move_to([3.5, 0.35, 0])
        t_a = VGroup(target_box("web-1", WEB_C, w=1.45, h=0.95, fs=13).move_to([-4.65, -1.55, 0]),
                     target_box("web-2", WEB_C, w=1.45, h=0.95, fs=13).move_to([-2.35, -1.55, 0]))
        t_b = VGroup(target_box("web-3", WEB_C, w=1.45, h=0.95, fs=13).move_to([2.3, -1.55, 0]),
                     target_box("web-4", WEB_C, w=1.45, h=0.95, fs=13).move_to([4.0, -1.55, 0]))
        wires_a = VGroup(*[wire(node_a.body.get_bottom(), t.get_top(), color=WEB_C, sw=2.0, op=0.6)
                           for t in t_a])
        wires_b = VGroup(*[wire(node_b.body.get_bottom(), t.get_top(), color=WEB_C, sw=2.0, op=0.6)
                           for t in t_b])

        self.play(Create(az_a[1]), FadeIn(az_a[0]), FadeIn(az_a[2]),
                  Create(az_b[1]), FadeIn(az_b[0]), FadeIn(az_b[2]), run_time=0.8)
        self.play(FadeIn(node_a), FadeIn(node_b), run_time=0.5)
        self.play(FadeIn(t_a), FadeIn(t_b), *[Create(w) for w in (*wires_a, *wires_b)],
                  run_time=0.6)
        cap = self.swap_cap(cap, "AWS runs a balancer node in every availability zone you enable, at least two.",
                            color=ALB_C)
        self.read(1.4)

        dns = dns_pill().move_to([0, 2.55, 0])
        a_d1 = arr(dns.box.get_bottom() + LEFT * 1.1, node_a.body.get_top(), color=MUTED, sw=2.6)
        a_d2 = arr(dns.box.get_bottom() + RIGHT * 1.1, node_b.body.get_top(), color=MUTED, sw=2.6)
        self.play(FadeIn(dns, shift=DOWN * 0.12), run_time=0.5)
        self.play(GrowArrow(a_d1), GrowArrow(a_d2), run_time=0.5)
        cap = self.swap_cap(cap, "The single DNS name resolves to all of them, so the front door has no single point of failure.")
        self.read(1.5)

        cross = wire(node_a.body.get_bottom(), t_b[0].get_top(), color=MUTED, sw=1.8, op=0.45)
        self.play(Create(cross), run_time=0.5)
        self.play(ShowPassingFlash(cross.copy().set_stroke(GOLD, 3.5, opacity=1.0), time_width=0.6),
                  run_time=0.9)
        cap = self.swap_cap(cap, "Cross-zone routing means every node can reach every healthy target.")
        self.read(1.3)

        # Auto Scaling adds a server; it registers itself with the target group
        new_t = target_box("web-5", WEB_C, w=1.45, h=0.95, fs=13, healthy=False).move_to([5.7, -1.55, 0])
        new_t.led.set_color(MUTED)
        cap = self.swap_cap(cap, "When Auto Scaling launches a new server, it registers itself with the target group.",
                            color=GOOD)
        self.play(FadeIn(new_t, shift=LEFT * 0.3), run_time=0.5)
        w_new = wire(node_b.body.get_bottom(), new_t.get_top(), color=WEB_C, sw=2.0, op=0.6)
        self.play(Create(w_new), new_t.led.animate.set_color(GOOD), run_time=0.5)
        self.play(Flash(new_t, color=GOOD, flash_radius=1.0), run_time=0.45)
        self.read(1.3)

        cap = self.swap_cap(cap, "And the balancer nodes grow with your traffic too. You never resize an ALB yourself.",
                            color=ALB_C)
        self.play(node_a.body.animate.set_stroke(width=4.2),
                  node_b.body.animate.set_stroke(width=4.2), run_time=0.5)
        self.read(1.4)

        # the recap chain: the journey of one request
        self.play(FadeOut(Group(*[m for m in self.mobjects if m is not header])), run_time=0.6)
        steps = [("DNS name", CLIENT_C), ("listener", ALB_C), ("rule", GOLD),
                 ("target group", API_C), ("healthy target", GOOD)]
        pieces = []
        for i, (label, color) in enumerate(steps):
            pieces.append(chip(label, color, fs=17, h=0.56, fill=0.14))
            if i < len(steps) - 1:
                pieces.append(Arrow(ORIGIN, RIGHT * 0.5, buff=0, stroke_width=3.2, color=MUTED,
                                    max_tip_length_to_length_ratio=0.4, tip_length=0.15))
        chain = VGroup(*pieces).arrange(RIGHT, buff=0.16)
        if chain.width > 12.6:
            chain.scale_to_fit_width(12.6)
        chain.move_to([0, 0.6, 0])
        self.play(LaggedStart(*[FadeIn(p, shift=RIGHT * 0.1) for p in pieces],
                              lag_ratio=0.08, run_time=1.1))
        cap = self.say("Every single request walks this chain, in a few milliseconds.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.5)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.takeaway("That is an ALB: a managed, Layer 7 front door.",
                      "It routes by content, survives failures, and scales itself.", c2=ALB_C)
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_frontdoor()
        self.scene_anatomy()
        self.scene_routing()
        self.scene_health()
        self.scene_layers()
        self.scene_scale()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_ALBBase):
    def construct(self):
        self.play_intro()


class FrontDoor(_ALBBase):
    def construct(self):
        self.scene_frontdoor()


class Anatomy(_ALBBase):
    def construct(self):
        self.scene_anatomy()


class Routing(_ALBBase):
    def construct(self):
        self.scene_routing()


class Health(_ALBBase):
    def construct(self):
        self.scene_health()


class Layers(_ALBBase):
    def construct(self):
        self.scene_layers()


class Scale(_ALBBase):
    def construct(self):
        self.scene_scale()


class Outro(_ALBBase):
    def construct(self):
        self.play_outro()


class WhatIsAnALB(_ALBBase):
    """The whole short film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    WhatIsAnALB().render()

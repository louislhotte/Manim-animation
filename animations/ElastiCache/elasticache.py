"""Amazon ElastiCache — a short, house-style explainer.

ElastiCache is AWS's managed, in-memory cache: a fast key/value store (Redis /
Valkey / Memcached) that you put *in front of* your database. Reads that would
otherwise travel all the way to the database are served from memory instead, in
a fraction of the time, and the database stops doing the same work over and over.

The film builds the idea in six beats:

    1. Problem     — every read hits the database; on disk, and hammered under load
    2. Memory      — RAM vs disk: why an in-memory store is orders of magnitude faster
                     (with a real, measured dict-vs-SQLite benchmark)
    3. Cache-aside — the read path: check cache, miss -> read db + store, hit -> instant
    4. Payoff      — a high hit ratio collapses database load and average latency
    5. Eviction    — memory is finite: TTL expiry, LRU eviction, and stale data
    6. Service     — what ElastiCache gives you: managed nodes in your VPC,
                     primary + replicas with automatic failover, cluster sharding

Everything is drawn with Manim ``Text`` (Pango), never ``Tex`` — no LaTeX. Scenes
render individually (``Problem``, ``Memory``, ``CacheAside``, ``Payoff``,
``Eviction``, ``Service``, ``Intro``, ``Outro``) or as one film
(``HowElastiCacheWorks``).

Env knobs:
    EC_QUICK=1   collapse every hold for a fast sanity render
    EC_DELAY=..  reading-rhythm multiplier for small inter-step pauses
    EC_READ=..   absolute hold after a caption lands (seconds) — reading time
"""
from __future__ import annotations

import json
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


QUICK = os.environ.get("EC_QUICK") == "1"
DELAY = float(os.environ.get("EC_DELAY", 0.28 if QUICK else 1.0))
READ = float(os.environ.get("EC_READ", 0.32 if QUICK else 2.35))
ANIM_SLOW = 1.0 if QUICK else 1.25
END_HOLD = 0.2 if QUICK else 2.1  # settle held on a finished scene before it wipes

# ---- palette (dark house style, shared across the series) ----------------- #
BG = "#0E1117"          # dark slate background
PANEL = "#151A23"       # panel fill
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / arrows
FAINT = "#2A3140"       # gridlines / faint wires
GOLD = "#FFD166"        # accent / rules

CLIENT_C = "#5B8DEF"    # clients / browsers (indigo blue)
APP_C = "#C792EA"       # application servers (violet)
CACHE_C = "#FF6B6B"     # the cache — hot, in-memory (Redis/ElastiCache coral) — HERO
DB_C = "#38BDF8"        # the database — persistent store, on disk (sky/cyan)
GOOD = "#3DD68C"        # a cache HIT / fast / healthy (green)
BAD = "#FF5C5C"         # failure / eviction (red) — used sparingly
WARN = "#FF8C42"        # latency / database under load (orange)
ACCENT = GOLD

MONO = "Menlo"          # code / addresses / keys
FONT = "Helvetica Neue"
_BaseText.set_default(font=FONT)

# ---- real, measured latency numbers (see generate_assets.py) --------------- #
_BENCH_FALLBACK = {"ram_ns": 113.8, "db_us": 2.3, "speedup": 20.2}


def _load_bench():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "bench.json")
    try:
        with open(path) as fh:
            d = json.load(fh)
        return {k: d[k] for k in ("ram_ns", "db_us", "speedup")}
    except (OSError, KeyError, ValueError):
        return dict(_BENCH_FALLBACK)


BENCH = _load_bench()

# ---- code-panel syntax colours (Python) ----------------------------------- #
CODE_FS = 19
PLAIN = "#D6DEEB"       # default code text
COMMENT = "#5F6B7E"     # comments (grey-blue)
KW = APP_C              # keywords: def / return / if / None
FUNC = "#82AAFF"        # function names
STR = "#C3E88D"         # strings

PY_T2C = {
    "def": KW, "return": KW, "None": FUNC,
    "get_user": FUNC, "query": FUNC,
    "cache": CACHE_C, "db": DB_C, "ttl": GOLD, "60": GOLD,
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
def bolt(color=GOLD, s=1.0, fill=0.85):
    """A lightning bolt — 'fast'. The cache's mark."""
    pts = [(-0.05, 0.34), (-0.24, 0.03), (-0.07, 0.03), (-0.13, -0.34),
           (0.24, 0.05), (0.05, 0.05)]
    v = VMobject()
    corners = [np.array([x, y, 0]) for x, y in pts]
    corners.append(corners[0])
    v.set_points_as_corners(corners)
    v.set_stroke(color=color, width=2).set_fill(color=color, opacity=fill)
    return v.scale(s)


def cache_box(w=2.75, h=1.62, title="ElastiCache", sub="in-memory cache", color=CACHE_C):
    """The hero: the cache as a titled coral card with a lightning mark."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.15,
                            stroke_color=color, stroke_width=3.2,
                            fill_color=color, fill_opacity=0.10)
    mark = bolt(color, s=0.92)
    name = txt(title, fs=25, color=INK, weight="BOLD")
    if name.width > w - 1.0:
        name.scale((w - 1.0) / name.width)
    head = VGroup(mark, name).arrange(RIGHT, buff=0.16)
    if sub:
        subt = txt(sub, fs=17, color=color)
        if subt.width > w - 0.4:
            subt.scale((w - 0.4) / subt.width)
        inner = VGroup(head, subt).arrange(DOWN, buff=0.13).move_to(body)
        g = VGroup(body, inner)
        g.subt = subt
    else:
        inner = VGroup(head).move_to(body)
        g = VGroup(body, inner)
    g.body = body
    g.mark = mark
    return g


def db_cylinder(color=DB_C, w=1.9, h=1.9, label="database", fs=18):
    """The classic database cylinder (explicit colours — Ellipse defaults RED)."""
    yt, yb = h / 2, -h / 2
    ew = 0.5
    body = Rectangle(width=w, height=h, stroke_width=0, fill_color=color, fill_opacity=0.10)
    left = Line([-w / 2, yb, 0], [-w / 2, yt, 0], stroke_color=color, stroke_width=2.6)
    right = Line([w / 2, yb, 0], [w / 2, yt, 0], stroke_color=color, stroke_width=2.6)
    bot = Ellipse(width=w, height=ew, stroke_color=color, stroke_width=2.6,
                  fill_color=BG, fill_opacity=1.0).move_to([0, yb, 0])
    mid1 = Arc(radius=w / 2, start_angle=PI, angle=-PI, arc_center=[0, yt - ew * 0.9, 0],
               stroke_color=color, stroke_width=1.6).stretch_to_fit_height(ew * 0.5)
    top = Ellipse(width=w, height=ew, stroke_color=color, stroke_width=2.6,
                  fill_color=color, fill_opacity=0.22).move_to([0, yt, 0])
    glyph = VGroup(body, bot, left, right, mid1, top)
    glyph.body = body
    glyph.top = top
    if label:
        lab = txt(label, fs=fs, color=color, weight="BOLD").next_to(glyph, DOWN, buff=0.18)
        glyph.add(lab)
        glyph.label = lab
    return glyph


def browser(label="GET /user/42", color=CLIENT_C, w=2.1, h=1.35):
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


def server_box(title="app", color=APP_C, w=2.2, h=1.05, healthy=True, sub=None):
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
    racks = VGroup(*[RoundedRectangle(width=w - 0.5, height=0.12, corner_radius=0.06,
                                      stroke_width=0, fill_color=color, fill_opacity=0.18)
                     for _ in range(2)]).arrange(DOWN, buff=0.12)
    racks.move_to([body.get_center()[0], body.get_center()[1] - 0.18, 0])
    g = VGroup(body, bar, led, ttl, racks)
    g.body = body
    g.led = led
    return g


def kv_chip(key, color=CACHE_C, w=1.55, h=0.5, fill=0.16):
    """A small key/value entry in the cache: a rounded chip labelled with a key."""
    box = RoundedRectangle(width=w, height=h, corner_radius=0.1,
                           stroke_color=color, stroke_width=2.2,
                           fill_color=color, fill_opacity=fill)
    lbl = mono(key, fs=15, color=INK)
    if lbl.width > w - 0.22:
        lbl.scale((w - 0.22) / lbl.width)
    lbl.move_to(box)
    g = VGroup(box, lbl)
    g.box = box
    g.key = lbl
    return g


def padlock(color=CACHE_C, s=1.0):
    """A padlock (Arc default is RED — set stroke explicitly)."""
    body = RoundedRectangle(width=0.52 * s, height=0.44 * s, corner_radius=0.08 * s,
                            stroke_color=color, stroke_width=3,
                            fill_color=color, fill_opacity=0.18)
    shackle = Arc(radius=0.16 * s, start_angle=0, angle=PI, color=color, stroke_width=3.2)
    shackle.next_to(body, UP, buff=-0.03 * s)
    hole = Dot(radius=0.04 * s, color=color).move_to(body)
    return VGroup(body, shackle, hole)


def clock(color=GOLD, s=1.0):
    """A little clock face for the TTL beat."""
    ring = Circle(radius=0.24 * s, stroke_color=color, stroke_width=3, fill_opacity=0)
    h1 = Line(ORIGIN, [0, 0.14 * s, 0], stroke_color=color, stroke_width=3)
    h2 = Line(ORIGIN, [0.1 * s, 0.02 * s, 0], stroke_color=color, stroke_width=3)
    g = VGroup(ring, h1, h2)
    g.ring = ring
    return g


def meter_track(w=2.3, h=0.24, color=MUTED):
    return RoundedRectangle(width=w, height=h, corner_radius=h / 2,
                            stroke_color=color, stroke_width=1.6,
                            fill_color=BG, fill_opacity=0.4)


def meter_fill(track, frac, color=WARN):
    """A left-anchored fill sized to `track`. Rebuild + Transform to animate."""
    frac = max(0.0, min(1.0, frac))
    w = track.width * frac
    h = track.height * 0.68
    fill = RoundedRectangle(width=max(w, h), height=h, corner_radius=h / 2,
                            stroke_width=0, fill_color=color, fill_opacity=0.95)
    fill.move_to(track.get_left(), aligned_edge=LEFT)
    if frac <= 0.001:
        fill.set_opacity(0)
    return fill


def stamp(text, color, fs=40):
    """A rotated rubber-stamp verdict."""
    t = txt(text, fs=fs, color=color, weight="BOLD")
    box = RoundedRectangle(width=t.width + 0.5, height=t.height + 0.36, corner_radius=0.14,
                           stroke_color=color, stroke_width=5, fill_opacity=0)
    t.move_to(box)
    return VGroup(box, t).rotate(-0.16)


# ========================================================================== #
class _ECBase(Scene):
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
    def code_panel(self, spec, table=PY_T2C, title="app.py", fs=CODE_FS,
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
        header = Text("Amazon ElastiCache", font_size=68, color=INK, weight="BOLD")
        if header.width > 12.6:
            header.scale_to_fit_width(12.6)
        line = Line(
            [header.get_left()[0] - 0.8, header.get_bottom()[1] - 0.42, 0],
            [header.get_right()[0] + 0.8, header.get_bottom()[1] - 0.42, 0],
        ).set_stroke(width=3, color=GOLD)
        mark = bolt(GOLD, s=1.25).move_to(line.get_right() + RIGHT * 0.28 + UP * 0.3)
        writer = Text("Created by Ptolémé", font_size=28, color=CLIENT_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        self.play(Write(header), Create(line), run_time=1.5)
        self.play(FadeIn(mark, shift=DOWN * 0.15), run_time=0.6)
        self.read(0.7)
        sub = Text("A managed in-memory cache that makes your app fast.",
                   font_size=29, color=MUTED)
        if sub.width > 12.6:
            sub.scale_to_fit_width(12.6)
        sub.move_to(header)
        self.play(Transform(header, sub), FadeOut(mark), run_time=1.0)
        self.read(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        src = Text("Redis · Valkey · Memcached  ·  System Design",
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
        recap = Text("Check the cache first. Touch the database last.",
                     font_size=26, color=ACCENT)
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
    # Scene 1 — The problem: every read hits the database
    # ====================================================================== #
    def scene_problem(self):
        header = self.section_header("The problem", WARN)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        client = browser("GET /user/42", CLIENT_C).move_to([-5.15, 0.7, 0])
        app = server_box("app", APP_C, w=2.15).move_to([-1.2, 0.7, 0])
        db = db_cylinder(DB_C, w=1.95, h=1.95, label="database").move_to([3.75, 0.7, 0])
        c_lbl = txt("client", fs=17, color=CLIENT_C).next_to(client, DOWN, buff=0.2)

        self.play(FadeIn(client, shift=RIGHT * 0.12), FadeIn(c_lbl), run_time=0.5)
        self.play(FadeIn(app, shift=UP * 0.1), run_time=0.5)
        self.play(FadeIn(db, shift=LEFT * 0.12), run_time=0.6)
        a1 = arr(client.get_right(), app.get_left(), color=MUTED, sw=3.5)
        a2 = arr(app.get_right(), db.body.get_left(), color=MUTED, sw=3.5)
        self.play(GrowArrow(a1), GrowArrow(a2), run_time=0.6)

        cap = self.say("Every read travels all the way to the database.")
        self.play(FadeIn(cap), run_time=0.5)
        d = self.send_dot(client.get_right() + RIGHT * 0.1, app.get_left() + LEFT * 0.05,
                          color=CLIENT_C, rt=0.5)
        self.play(d.animate.move_to(db.body.get_left() + LEFT * 0.05).set_color(APP_C),
                  run_time=0.55, rate_func=rate_functions.ease_in_out_sine)
        self.play(Indicate(db.body, color=DB_C, scale_factor=1.05),
                  d.animate.move_to(app.get_right() + RIGHT * 0.05).set_color(DB_C),
                  run_time=0.55)
        self.play(FadeOut(d), run_time=0.2)
        self.read(1.1)

        # the database is slow: it reads from disk
        lat = pill("~30 ms", WARN, fs=20).next_to(db, UP, buff=0.28)
        disk = txt("reads from disk", fs=16, color=MUTED).next_to(db.label, DOWN, buff=0.14)
        self.play(FadeIn(lat, shift=DOWN * 0.1), FadeIn(disk), run_time=0.5)
        cap2 = self.swap_cap(cap, "The database reads from disk, so each query is slow.", color=WARN)
        self.read(1.3)

        # under load: the same query, again and again -> the db is hammered
        cap3 = self.swap_cap(cap2, "The same popular rows are requested again and again.", color=WARN)
        rep = VGroup(*[mono("GET /user/42", fs=14, color=CLIENT_C) for _ in range(3)])
        rep.arrange(DOWN, buff=0.14).next_to(client, UP, buff=0.3)
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.1) for r in rep],
                              lag_ratio=0.2, run_time=0.8))
        self.read(0.8)

        # a burst of identical requests floods through to the DB; load meter climbs
        track = meter_track(w=2.4, color=WARN).move_to([3.75, -1.75, 0])
        load_lbl = txt("DB load", fs=15, color=MUTED).next_to(track, LEFT, buff=0.18)
        fill = meter_fill(track, 0.14, WARN)
        self.play(FadeIn(track), FadeIn(load_lbl), FadeIn(fill), run_time=0.4)
        cap4 = self.swap_cap(cap3, "Under load, one database does the same expensive work over and over.",
                             color=WARN)
        for i in range(6):
            d = Dot(client.get_right() + RIGHT * 0.1, radius=0.07, color=CLIENT_C)
            self.add(d)
            self.play(d.animate.move_to(db.body.get_left() + LEFT * 0.05).set_color(APP_C),
                      run_time=0.3, rate_func=rate_functions.ease_in_out_sine)
            self.play(Transform(fill, meter_fill(track, 0.14 + 0.14 * (i + 1), WARN)),
                      FadeOut(d), run_time=0.18)
        self.play(Transform(fill, meter_fill(track, 1.0, BAD)),
                  db.body.animate.set_fill(BAD, 0.14),
                  Flash(db, color=BAD, flash_radius=1.5), run_time=0.6)
        self.play(lat.animate.become(pill("~120 ms", BAD, fs=20).next_to(db, UP, buff=0.28)),
                  run_time=0.4)
        self.read(1.4)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.takeaway("The database is the bottleneck.",
                      "It is slow, and it keeps repeating the same work.")
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — Memory vs disk: why an in-memory cache is fast (real numbers)
    # ====================================================================== #
    def scene_memory(self):
        header = self.section_header("Why memory is fast", CACHE_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        q = txt("How much faster is memory than disk? Let's measure it.",
                fs=25, color=INK).move_to([0, 2.5, 0])
        self.play(FadeIn(q, shift=DOWN * 0.1), run_time=0.6)
        self.read(1.1)

        # a log-scale latency ladder: RAM, a local SSD, a real database call.
        # names sit ABOVE each bar (a long name won't fit a left gutter), the
        # measured/typical time at the bar's right end.
        rows = [
            ("in-memory (RAM)", f"~{BENCH['ram_ns']:.0f} ns", CACHE_C, np.log10(BENCH["ram_ns"])),
            ("local SSD read", "~100 µs", MUTED, np.log10(100_000)),
            ("database call (network + disk)", "~10 ms", DB_C, np.log10(10_000_000)),
        ]
        base = min(r[3] for r in rows)
        span = max(r[3] for r in rows) - base
        max_w = 7.6
        ys = [1.35, -0.05, -1.45]
        x0 = -4.6
        bars, labels = VGroup(), VGroup()
        for (name, num, color, lg), y in zip(rows, ys):
            frac = 0.06 + 0.94 * ((lg - base) / span)
            bar = RoundedRectangle(width=max_w * frac, height=0.6, corner_radius=0.1,
                                   stroke_color=color, stroke_width=2.4,
                                   fill_color=color, fill_opacity=0.28)
            bar.move_to([x0, y, 0], aligned_edge=LEFT)
            name_t = txt(name, fs=18, color=INK)
            name_t.move_to([x0, y + 0.5, 0], aligned_edge=LEFT)
            num_t = txt(num, fs=20, color=color, weight="BOLD").next_to(bar, RIGHT, buff=0.18)
            bars.add(bar)
            labels.add(VGroup(name_t, num_t))
        note = txt("(log scale: each step down is far larger than it looks)",
                   fs=15, color=MUTED).move_to([0.4, -2.45, 0])

        for bar, lab in zip(bars, labels):
            self.play(GrowFromEdge(bar, LEFT), FadeIn(lab), run_time=0.5)
        self.play(FadeIn(note), run_time=0.4)
        cap = self.say("Memory reads are measured in nanoseconds; a database call, in milliseconds.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.6)

        # the measured, real benchmark (avoid × / → glyphs: not all fonts have them)
        self.play(FadeOut(q), run_time=0.3)
        meas = VGroup(
            txt("measured here:", fs=18, color=MUTED),
            mono(f"dict {BENCH['ram_ns']:.0f} ns", fs=18, color=CACHE_C),
            txt("vs", fs=16, color=MUTED),
            mono(f"SQLite {BENCH['db_us']:.1f} µs", fs=18, color=DB_C),
            txt(f"=  {BENCH['speedup']:.0f}x faster", fs=19, color=GOOD, weight="BOLD"),
        ).arrange(RIGHT, buff=0.24).move_to([0, 2.55, 0])
        if meas.width > 12.6:
            meas.scale_to_fit_width(12.6)
        self.play(FadeIn(meas, shift=DOWN * 0.1), run_time=0.6)
        cap2 = self.swap_cap(cap, "Even against a warm local database, an in-memory read wins easily.",
                             color=CACHE_C)
        self.read(1.5)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.takeaway("So put a small, fast store in memory,",
                      "in front of the slow database.", c2=CACHE_C)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Cache-aside: the read path (miss, then hit) + the code
    # ====================================================================== #
    def scene_cacheaside(self):
        header = self.section_header("The read path", CACHE_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        app = server_box("app", APP_C, w=2.05).move_to([-4.7, 0.55, 0])
        cache = cache_box(w=2.9, h=1.8, title="cache", sub=None).move_to([0.0, 0.55, 0])
        cache[1].align_to(cache.body, UP).shift(DOWN * 0.2)   # title at top, slot free below
        slot_pt = np.array([cache.body.get_center()[0],
                            (cache[1].get_bottom()[1] + cache.body.get_bottom()[1]) / 2, 0])
        db = db_cylinder(DB_C, w=1.8, h=1.8, label="database").move_to([4.9, 0.55, 0])
        self.play(FadeIn(app, shift=RIGHT * 0.1), run_time=0.45)
        self.play(GrowFromCenter(cache), run_time=0.55)
        self.play(FadeIn(db, shift=LEFT * 0.1), run_time=0.45)
        a1 = arr(app.get_right(), cache.body.get_left(), color=APP_C, sw=3.5)
        a2 = arr(cache.body.get_right(), db.body.get_left(), color=MUTED, sw=3.0)
        self.play(GrowArrow(a1), GrowArrow(a2), run_time=0.5)

        # ---- MISS: first request for user:42 ----
        cap = self.say("The app asks the cache first: is user 42 here?")
        self.play(FadeIn(cap), run_time=0.5)
        d = self.send_dot(app.get_right() + RIGHT * 0.08, cache.body.get_left() + LEFT * 0.05,
                          color=APP_C, rt=0.5)
        miss = pill("MISS", WARN, fs=18).next_to(cache, UP, buff=0.2)
        self.play(FadeIn(miss, shift=DOWN * 0.1), run_time=0.35)
        cap = self.swap_cap(cap, "Cache miss: it isn't there yet, so the app reads the database.",
                            color=WARN)
        self.play(d.animate.move_to(db.body.get_left() + LEFT * 0.05).set_color(DB_C), run_time=0.6,
                  rate_func=rate_functions.ease_in_out_sine)
        self.play(Indicate(db.body, color=DB_C, scale_factor=1.06), run_time=0.5)
        # data returns, and is stored in the cache's slot on the way back
        self.play(d.animate.move_to(cache.body.get_right() + RIGHT * 0.05).set_color(DB_C),
                  run_time=0.55, rate_func=rate_functions.ease_in_out_sine)
        stored = kv_chip("user:42", CACHE_C, w=1.95, h=0.52).move_to(slot_pt)
        self.play(ReplacementTransform(d, stored), run_time=0.45)
        self.play(Flash(stored, color=CACHE_C, flash_radius=0.7), run_time=0.4)
        cap = self.swap_cap(cap, "Then it stores the result in the cache for next time.",
                            color=CACHE_C)
        self.read(1.4)

        # ---- HIT: second request for user:42 ----
        cap = self.swap_cap(cap, "Next time the same row is asked for, it's a cache hit.",
                            color=GOOD)
        d2 = self.send_dot(app.get_right() + RIGHT * 0.08, cache.body.get_left() + LEFT * 0.05,
                           color=APP_C, rt=0.5)
        hit = pill("HIT", GOOD, fs=18).next_to(cache, UP, buff=0.2)
        self.play(ReplacementTransform(miss, hit),
                  Indicate(stored, color=GOOD, scale_factor=1.15),
                  cache.body.animate.set_stroke(GOOD, 3.4), run_time=0.45)
        self.play(d2.animate.move_to(app.get_right() + RIGHT * 0.08).set_color(GOOD),
                  run_time=0.5, rate_func=rate_functions.ease_in_out_sine)
        self.play(FadeOut(d2), run_time=0.15)
        # the database is untouched: dim the cache-to-db arrow
        self.play(a2.animate.set_stroke(opacity=0.25), db.body.animate.set_fill(DB_C, 0.04),
                  run_time=0.4)
        cap = self.swap_cap(cap, "Served from memory in under a millisecond. The database is never touched.",
                            color=GOOD)
        self.read(1.6)

        # ---- the code that does it ----
        self.play(FadeOut(Group(app, cache, db, a1, a2, stored, hit, cap)), run_time=0.6)
        spec = [
            (0, "def get_user(uid):"),
            (1, "key = f\"user:{uid}\""),
            (1, "hit = cache.get(key)"),
            (1, "if hit is not None:"),
            (2, "return hit"),
            (1, "row = db.query(uid)"),
            (1, "cache.set(key, row, ttl=60)"),
            (1, "return row"),
        ]
        panel, lines = self.code_panel(spec, title="app.py", target_h=4.7)
        panel.move_to([0, 0.1, 0])
        self.play(FadeIn(panel, shift=UP * 0.15), run_time=0.8)
        capA = self.say("This is the cache-aside pattern, and it's only a few lines.")
        self.play(FadeIn(capA), run_time=0.5)
        self.read(1.1)

        self.focus(panel, lines, [2, 3], color=CACHE_C)
        capA = self.swap_cap(capA, "First, check the cache.", color=CACHE_C)
        self.read(1.0)
        self.focus(panel, lines, [3, 4], color=GOOD)
        capA = self.swap_cap(capA, "On a hit, return it right away.", color=GOOD)
        self.read(1.1)
        self.focus(panel, lines, [5, 6], color=DB_C)
        capA = self.swap_cap(capA, "On a miss, read the database, then store it for next time.", color=DB_C)
        self.read(1.5)

        self.play(FadeOut(Group(panel, self.hlrect, header, capA)), run_time=0.6)
        self.hlrect = None
        self.takeaway("Check the cache. On a miss, read the database and remember the answer.",
                      "That is cache-aside, or lazy loading.", c2=CACHE_C)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — The payoff: a high hit ratio collapses load and latency
    # ====================================================================== #
    def scene_payoff(self):
        header = self.section_header("The payoff", GOOD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        app = server_box("app", APP_C, w=1.9).move_to([-5.1, 1.15, 0])
        cache = cache_box(w=2.7, h=1.45, title="cache", sub="in-memory").move_to([-0.9, 1.15, 0])
        db = db_cylinder(DB_C, w=1.55, h=1.5, label="database").move_to([3.9, 1.15, 0])
        self.play(FadeIn(app), GrowFromCenter(cache), FadeIn(db), run_time=0.6)
        a1 = arr(app.get_right(), cache.body.get_left(), color=APP_C, sw=3.0)
        a2 = arr(cache.body.get_right(), db.body.get_left(), color=MUTED, sw=2.6)
        self.play(GrowArrow(a1), GrowArrow(a2), run_time=0.4)

        # dashboard: a hit-ratio meter, a DB-load meter, an average-latency readout
        # (all Helvetica — no DecimalNumber, whose digits render in a LaTeX font)
        hr_track = meter_track(w=2.5, color=GOOD).move_to([-3.3, -1.6, 0])
        hr_lbl = txt("hit ratio", fs=15, color=MUTED).next_to(hr_track, LEFT, buff=0.2)
        hr_fill = meter_fill(hr_track, 0.0, GOOD)

        load_track = meter_track(w=2.5, color=WARN).move_to([-3.3, -2.6, 0])
        load_lbl = txt("DB load", fs=15, color=MUTED).next_to(load_track, LEFT, buff=0.2)
        load_fill = meter_fill(load_track, 1.0, WARN)

        lat_val = txt("30 ms", fs=30, color=WARN, weight="BOLD")
        lat_lbl = txt("avg latency", fs=15, color=MUTED)
        lat = VGroup(lat_val, lat_lbl).arrange(DOWN, buff=0.12).move_to([4.3, -2.1, 0])

        self.play(FadeIn(VGroup(hr_track, hr_lbl, hr_fill)),
                  FadeIn(VGroup(load_track, load_lbl, load_fill)),
                  FadeIn(lat), run_time=0.5)
        cap = self.say("Send ten reads through the cache. Most of them are hits.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(0.9)

        # ten requests: nine hits (served at the cache) and one miss (falls through)
        order = [True] * 10
        order[3] = False
        hits = 0
        for is_hit in order:
            d = Dot(app.get_right() + RIGHT * 0.06, radius=0.06, color=APP_C)
            self.add(d)
            self.play(d.animate.move_to(cache.body.get_left() + LEFT * 0.04), run_time=0.24,
                      rate_func=rate_functions.ease_in_out_sine)
            if is_hit:
                hits += 1
                self.play(d.animate.move_to(app.get_right() + RIGHT * 0.06).set_color(GOOD),
                          Transform(hr_fill, meter_fill(hr_track, hits / 10.0, GOOD)),
                          Transform(load_fill, meter_fill(load_track, 1 - hits / 10.0, WARN)),
                          run_time=0.26)
                self.play(FadeOut(d), run_time=0.08)
            else:
                self.play(d.animate.move_to(db.body.get_left() + LEFT * 0.04).set_color(DB_C),
                          run_time=0.3)
                self.play(Indicate(db.body, color=DB_C, scale_factor=1.08),
                          d.animate.move_to(app.get_right() + RIGHT * 0.06).set_color(DB_C),
                          run_time=0.34)
                self.play(FadeOut(d), run_time=0.08)
        # final picture: 90% hits, DB load a tenth, latency collapses
        self.play(Transform(load_fill, meter_fill(load_track, 0.1, GOOD)),
                  lat_val.animate.become(
                      txt("3.5 ms", fs=30, color=GOOD, weight="BOLD").move_to(lat_val)),
                  run_time=0.7)
        pct = pill("90%", GOOD, fs=22).next_to(hr_track, RIGHT, buff=0.24)
        self.play(FadeIn(pct, scale=0.7), Flash(pct, color=GOOD, flash_radius=0.7), run_time=0.5)
        cap = self.swap_cap(cap, "At a 90% hit ratio, nine of ten reads never reach the database.",
                            color=GOOD)
        self.read(1.6)

        # the arithmetic, made explicit and asserted
        p, c_ms, d_ms = 0.9, 0.5, 30.0
        eff = round(p * c_ms + (1 - p) * (c_ms + d_ms), 1)
        assert eff == 3.5, eff
        cap = self.swap_cap(cap, "Database load falls ten-fold, and average latency collapses with it.",
                            color=ACCENT)
        self.read(1.5)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.takeaway("A high hit ratio is the whole game:",
                      "less database load, and a fraction of the latency.", c2=GOOD)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — Eviction: memory is finite (TTL, LRU, stale data)
    # ====================================================================== #
    def scene_eviction(self):
        header = self.section_header("Memory is finite", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        cache = cache_box(w=3.0, h=1.5, title="cache", sub="limited RAM").move_to([0, 2.0, 0])
        self.play(GrowFromCenter(cache), run_time=0.5)

        # a row of four slots
        keys = ["user:42", "cart:7", "post:9", "user:88"]
        slots = VGroup(*[kv_chip(k, CACHE_C, w=2.1, h=0.62) for k in keys])
        slots.arrange(RIGHT, buff=0.3).move_to([0, 0.35, 0])
        self.play(LaggedStart(*[FadeIn(s, scale=0.8) for s in slots],
                              lag_ratio=0.12, run_time=0.8))
        cap = self.say("A cache only holds so much. Entries don't live forever.")
        self.play(FadeIn(cap), run_time=0.5)
        self.read(1.2)

        # --- TTL: an entry expires ---
        clk = clock(GOLD, s=1.0).next_to(slots[1], UP, buff=0.16)
        ttl_tag = txt("ttl 60s", fs=14, color=GOLD).next_to(clk, RIGHT, buff=0.12)
        self.play(FadeIn(clk), FadeIn(ttl_tag), run_time=0.4)
        cap = self.swap_cap(cap, "Give each entry a TTL: after it expires, the cache forgets it.",
                            color=GOLD)
        self.play(Rotate(clk[1], angle=-TAU, about_point=clk.ring.get_center()),
                  Rotate(clk[2], angle=-TAU, about_point=clk.ring.get_center()),
                  run_time=1.1)
        exp = txt("expired", fs=15, color=MUTED).move_to(slots[1])
        self.play(slots[1].animate.set_opacity(0.12),
                  FadeOut(clk), FadeOut(ttl_tag), run_time=0.5)
        self.play(FadeIn(exp), run_time=0.3)
        self.read(1.3)
        self.play(FadeOut(slots[1]), FadeOut(exp), run_time=0.4)

        # --- LRU: cache full, evict least-recently-used to make room ---
        cap = self.swap_cap(cap, "When the cache is full, it evicts the least recently used entry.",
                            color=BAD)
        # mark the leftmost as LRU
        lru_tag = txt("least recently used", fs=13, color=BAD).next_to(slots[0], DOWN, buff=0.16)
        self.play(slots[0].box.animate.set_stroke(BAD, 2.6), FadeIn(lru_tag), run_time=0.5)
        newkey = kv_chip("order:5", GOOD, w=2.1, h=0.62).next_to(cache, DOWN, buff=0.16)
        new_lbl = txt("new key", fs=13, color=GOOD).next_to(newkey, RIGHT, buff=0.14)
        self.play(FadeIn(newkey, shift=DOWN * 0.1), FadeIn(new_lbl), run_time=0.4)
        # evict slot 0 (fly out left + fade), move new key into its place
        target = slots[0].get_center()
        self.play(slots[0].animate.shift(LEFT * 2.2).set_opacity(0.0),
                  FadeOut(lru_tag), run_time=0.55)
        self.play(newkey.animate.move_to(target).set_color(CACHE_C), FadeOut(new_lbl),
                  run_time=0.5)
        self.play(newkey[0].animate.set_stroke(CACHE_C, 2.2).set_fill(CACHE_C, 0.16),
                  newkey[1].animate.set_color(INK), run_time=0.3)
        self.read(1.3)

        # --- stale data: the classic caching hazard ---
        cap = self.swap_cap(cap, "And a cache is only a copy, so it can go stale.", color=WARN)
        stale = slots[2]  # post:9
        stale_tag = txt("db changed → cached copy is stale", fs=15, color=WARN)
        stale_tag.next_to(slots, DOWN, buff=0.5)
        self.play(stale.box.animate.set_stroke(WARN, 2.6).set_fill(WARN, 0.14),
                  FadeIn(stale_tag), run_time=0.5)
        self.play(Indicate(stale, color=WARN, scale_factor=1.08), run_time=0.4)
        self.read(1.3)
        cap = self.swap_cap(cap, "On a write, update or delete the cached copy to keep reads correct.",
                            color=GOOD)
        self.play(stale.box.animate.set_stroke(GOOD, 2.6).set_fill(GOOD, 0.14),
                  FadeOut(stale_tag),
                  stale.key.animate.set_color(INK), run_time=0.5)
        tick = make_tick(GOOD, sw=6, scale=0.9).next_to(stale, UP, buff=0.12)
        self.play(FadeIn(tick), run_time=0.3)
        self.read(1.4)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)
        self.takeaway("A cache is a fast copy, not the source of truth.",
                      "Expire it, size it, and invalidate it on writes.", c2=GOLD)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 6 — The service: what Amazon ElastiCache gives you
    # ====================================================================== #
    def scene_service(self):
        header = self.section_header("Amazon ElastiCache", CACHE_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        cap = self.say("ElastiCache runs the cache for you, as a managed service.")
        self.play(FadeIn(cap), run_time=0.5)

        # engines you can run
        engines = VGroup(
            chip("Redis", CACHE_C, fs=19, h=0.56),
            chip("Valkey", CACHE_C, fs=19, h=0.56),
            chip("Memcached", DB_C, fs=19, h=0.56),
        ).arrange(RIGHT, buff=0.3).move_to([0, 2.35, 0])
        self.play(LaggedStart(*[FadeIn(e, scale=0.8) for e in engines],
                              lag_ratio=0.15, run_time=0.7))
        self.read(1.1)

        # a VPC boundary with a primary + two replicas inside
        vpc = RoundedRectangle(width=6.8, height=3.1, corner_radius=0.2,
                               stroke_color=FAINT, stroke_width=2.2,
                               fill_color=PANEL, fill_opacity=0.35).move_to([1.1, -0.3, 0])
        vpc_lbl = txt("Your VPC", fs=16, color=MUTED).next_to(vpc.get_corner(UL), DR, buff=0.16)
        self.play(Create(vpc), FadeIn(vpc_lbl), run_time=0.6)

        # primary on top, two replicas symmetric below it (a clean replication tree)
        primary_pos = np.array([1.1, 0.45, 0])
        primary = cache_box(w=2.4, h=1.15, title="primary", sub="read + write").move_to(primary_pos)
        repL = cache_box(w=2.0, h=0.98, title="replica", sub="read").scale(0.92).move_to([-0.15, -1.05, 0])
        repR = cache_box(w=2.0, h=0.98, title="replica", sub="read").scale(0.92).move_to([2.35, -1.05, 0])
        self.play(GrowFromCenter(primary), run_time=0.5)
        self.play(FadeIn(repL, shift=UP * 0.1), FadeIn(repR, shift=UP * 0.1), run_time=0.5)
        w1 = wire(primary.body.get_bottom(), repL.body.get_top(), color=CACHE_C, sw=2.0, op=0.6)
        w2 = wire(primary.body.get_bottom(), repR.body.get_top(), color=CACHE_C, sw=2.0, op=0.6)
        self.play(Create(w1), Create(w2), run_time=0.4)

        app = server_box("app", APP_C, w=1.7, h=0.95).move_to([-5.1, 0.45, 0])
        a_in = arr(app.get_right(), primary.body.get_left(), color=APP_C, sw=3.0)
        self.play(FadeIn(app), GrowArrow(a_in), run_time=0.5)
        cap = self.swap_cap(cap, "A primary node takes writes; replicas keep copies for reads.",
                            color=CACHE_C)
        self.read(1.5)

        # failover: the primary fails, is removed, and a replica is promoted up into
        # its slot — so only one node ever reads "primary" and the arrows stay clean.
        cap = self.swap_cap(cap, "If the primary fails, a replica is promoted automatically.",
                            color=GOLD)
        xr = make_cross(BAD, sw=7, scale=1.2).move_to(primary)
        self.play(primary.body.animate.set_stroke(BAD, 3.0).set_fill(BAD, 0.10),
                  w1.animate.set_stroke(opacity=0.12), w2.animate.set_stroke(opacity=0.12),
                  a_in.animate.set_stroke(opacity=0.2),
                  Flash(primary, color=BAD, flash_radius=1.2), run_time=0.6)
        self.play(FadeIn(xr), run_time=0.3)
        self.read(0.9)
        self.play(FadeOut(Group(primary, xr, w1, w2, a_in)), run_time=0.45)
        new_primary = cache_box(w=2.4, h=1.15, title="primary", sub="read + write").move_to(primary_pos)
        new_primary.body.set_stroke(GOOD, 3.2)
        self.play(ReplacementTransform(repL, new_primary), run_time=0.7)
        a_in2 = arr(app.get_right(), new_primary.body.get_left(), color=APP_C, sw=3.0)
        w3 = wire(new_primary.body.get_bottom(), repR.body.get_top(), color=CACHE_C, sw=2.0, op=0.6)
        self.play(GrowArrow(a_in2), Create(w3),
                  Flash(new_primary, color=GOOD, flash_radius=1.2), run_time=0.55)
        self.read(1.5)

        # collapse the cluster; state cluster-mode sharding as the scale story
        self.play(FadeOut(Group(vpc, vpc_lbl, new_primary, repR, w3, a_in2, app, engines)),
                  run_time=0.6)
        cap = self.swap_cap(cap, "Need more room? Cluster mode shards your keys across many nodes.",
                            color=DB_C)
        shards = VGroup(*[cache_box(w=1.9, h=1.0, title=f"shard {i+1}", sub=rng)
                          for i, rng in enumerate(["keys A-H", "keys I-P", "keys Q-Z"])])
        for s in shards:
            s.scale(0.95)
        shards.arrange(RIGHT, buff=0.5).move_to([0, 0.5, 0])
        self.play(LaggedStart(*[FadeIn(s, shift=UP * 0.1) for s in shards],
                              lag_ratio=0.15, run_time=0.9))
        self.read(1.5)

        self.play(FadeOut(Group(shards, header, cap)), run_time=0.6)
        self.takeaway("A fast, managed, highly available cache.",
                      "You don't run the servers. AWS does.", c2=CACHE_C)
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_problem()
        self.scene_memory()
        self.scene_cacheaside()
        self.scene_payoff()
        self.scene_eviction()
        self.scene_service()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_ECBase):
    def construct(self):
        self.play_intro()


class Problem(_ECBase):
    def construct(self):
        self.scene_problem()


class Memory(_ECBase):
    def construct(self):
        self.scene_memory()


class CacheAside(_ECBase):
    def construct(self):
        self.scene_cacheaside()


class Payoff(_ECBase):
    def construct(self):
        self.scene_payoff()


class Eviction(_ECBase):
    def construct(self):
        self.scene_eviction()


class Service(_ECBase):
    def construct(self):
        self.scene_service()


class Outro(_ECBase):
    def construct(self):
        self.play_outro()


class HowElastiCacheWorks(_ECBase):
    """The whole short film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    HowElastiCacheWorks().render()

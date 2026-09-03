"""Designing the News Feed — a ~3-minute system-design explainer, house-style.

How does a post reach every follower's home timeline — fast — when one author has
200 followers and the next has 100 million?  The film builds the answer the way a
real design review would:

    1. Your Feed        -- how a user actually interacts with the feed
    2. Fan-out on Write -- PUSH: precompute each follower's feed in Redis (great at 200)
    3. The Celebrity    -- the same push, at 100M followers, becomes a write storm
    4. Push + Pull      -- the hybrid fix: push for the many, PULL for the few
    5. The Architecture -- the full production system, a write then a read flowing
    6. Recap            -- push for the many, pull for the few

Everything is a Manim mobject — phones, avatars, databases, the Redis cache, the
Kafka log, the API gateway, the CDN — drawn as clean high-level service icons.
Text is Pango ``Text`` (never ``Tex``), rendered large and scaled down so spacing
stays crisp; the one code snippet is set in Menlo.

Scenes are exposed individually (``Intro``, ``Feed``, ``Push``, ``Celebrity``,
``Hybrid``, ``Architecture``, ``Recap``, ``Outro``) and as one film (``NewsFeed``).

Env knobs:
    NF_QUICK=1     collapse every reading hold (and end-holds) for a fast render
    NF_DELAY=1.2   override the reading-hold multiplier (seconds per "beat")
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


QUICK = os.environ.get("NF_QUICK") == "1"
# Reading rhythm: every hold is self.beat(t) == wait(t * DELAY). Generous, so
# captions linger long enough to read. QUICK collapses every hold.
DELAY = float(os.environ.get("NF_DELAY", "0.26" if QUICK else "1.95"))
# Beat held on the finished scene before it wipes to the next one.
END_HOLD = 0.2 if QUICK else 2.3
# Slow every *played* animation to ~83% speed so motion never feels rushed; the
# reading holds above are governed by DELAY, not by this. QUICK keeps full speed.
ANIM_SLOW = 1.0 if QUICK else 1.2

# ---- palette -------------------------------------------------------------- #
BG = "#0E1117"        # dark slate background
PANEL = "#151A23"     # panel fill
INK = "#F5F3EF"       # warm white text
MUTED = "#8A93A6"     # secondary text / arrows
FAINT = "#2A3140"     # gridlines / tracks / card borders
ACCENT = "#FFD166"    # highlight (gold)
GOOD = "#3DD68C"      # healthy / pass (green)
BAD = "#FF5C5C"       # failing / overload (red)
WARN = "#FFC24B"      # warning (amber)

BRAND = "#5B8DEF"     # feed / client blue (bookends, headers)
PUSH = "#F6C453"      # fan-out on WRITE — warm gold (work up front)
PULL = "#4CC9F0"      # fan-out on READ — cool cyan (gather on read)
WRITEC = "#5B8DEF"    # write data path (blue)
READC = "#3DD68C"     # read data path (green)
REDIS = "#E23B2E"     # Redis brand red
KAFKA = "#9AA3FF"     # message log (indigo)
GATE = "#C792EA"      # API gateway (purple)
DBC = "#2EC4B6"       # databases (teal)
STORE = "#FF9F45"     # object storage (orange)
CDNC = "#64B5F6"      # CDN (light blue)
CELEB = "#F4C430"     # celebrity / verified gold
AVATAR = "#5B8DEF"    # default user

# ---- code (Night-Owl-ish) palette ----------------------------------------- #
MONO = "Menlo"
CODE_FS = 20
PLAIN = "#D6DEEB"     # default code text
COMMENT = "#5F6B7E"   # comments (grey-blue)
KW = "#C792EA"        # keywords (purple)
FN = "#82AAFF"        # function / field names (blue)


def _safe_t2c(s, table):
    """Per-line text->colour map, pruned so no key overlaps another.

    Manim's ``t2c`` raises on overlapping colour ranges even for equal colours
    (e.g. ``push`` inside ``push_to_feeds``). Keep only keys present in this line,
    then drop any key that is a substring of another present key.
    """
    present = {k: v for k, v in table.items() if k in s}
    keys = list(present)
    return {k: v for k, v in present.items()
            if not any(k != o and k in o for o in keys)}


def _unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


# ========================================================================== #
# SVG icon system — a consistent, line-art design system (Lucide-style, 24px
# grid, uniform stroke). Icons live in assets/icons/*.svg; loaded once & cached.
# ========================================================================== #
_ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icons")
_ICON_CACHE = {}


def _icon_tpl(name):
    if name not in _ICON_CACHE:
        _ICON_CACHE[name] = SVGMobject(os.path.join(_ICON_DIR, name + ".svg"))
    return _ICON_CACHE[name]


def icon(name, color=INK, height=0.6, sw=3.2, fill=False):
    """A copy of the named SVG icon, sized to ``height``, coloured ``color``.

    ``fill=False`` keeps it line-art (stroke only); ``fill=True`` renders it as a
    solid glyph (for avatars / a liked heart).
    """
    m = _icon_tpl(name).copy().scale_to_fit_height(height)
    if fill:
        m.set_fill(color, opacity=1.0).set_stroke(color, width=max(1.0, sw * 0.35))
    else:
        m.set_fill(opacity=0.0).set_stroke(color, width=sw)
    return m


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
    return VGroup(box, label)


def arr(a, b, color=MUTED, sw=4, buff=0.14, tip=0.22):
    return Arrow(a, b, buff=buff, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.35, tip_length=tip)


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


# ========================================================================== #
# service & user glyphs — clean, high-level icons
# ========================================================================== #
def person(color=AVATAR, s=1.0):
    """A user avatar glyph (line-art), sized like the old silhouette."""
    return icon("user", color=color, height=0.5 * s, sw=max(1.4, 2.7 * s))


def verified(color=CELEB, s=1.0):
    """A verified badge: a solid disc with a white tick."""
    disc = Circle(radius=0.19, stroke_width=0, fill_color=color, fill_opacity=1.0)
    tick = make_tick(color=BG, sw=5, scale=0.55).move_to(disc)
    return VGroup(disc, tick).scale(s)


def avatar_tile(color=AVATAR, size=0.8, badge=False):
    tile = RoundedRectangle(width=size, height=size, corner_radius=0.16,
                            stroke_color=color, stroke_width=2.6,
                            fill_color=color, fill_opacity=0.14)
    p = icon("user", color=color, height=size * 0.56, sw=2.8).move_to(tile)
    g = VGroup(tile, p)
    if badge:
        b = verified(CELEB, s=0.8).move_to(tile.get_corner(UR))
        g.add(b)
    g.tile = tile
    return g


def heart(color=BAD, s=1.0, filled=True):
    """A single clean heart (SVG); ``filled`` toggles solid vs outline."""
    return icon("heart", color=color, height=0.26 * s, sw=2.4, fill=filled)


def post_card(w=2.5, accent=AVATAR, liked=False, img=True):
    """A feed post whose border always wraps its content.

    Content (header · image · like-row) is laid out left-aligned, then the card
    background is sized *to the content* + padding — so the border encloses the
    like row too. The whole card is finally scaled to the requested width ``w``.
    """
    pad = 0.17
    base_w = 2.5           # design width; scaled to w at the end
    inner = base_w - 2 * pad
    av = icon("user", color=accent, height=0.34, sw=2.2)
    name = RoundedRectangle(width=inner * 0.52, height=0.12, corner_radius=0.05,
                            stroke_width=0, fill_color=INK, fill_opacity=0.9)
    handle = RoundedRectangle(width=inner * 0.34, height=0.09, corner_radius=0.045,
                              stroke_width=0, fill_color=MUTED, fill_opacity=0.7)
    bars = VGroup(name, handle).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
    header = VGroup(av, bars).arrange(RIGHT, buff=0.15)
    parts = [header]
    if img:
        ih = 0.62
        block = RoundedRectangle(width=inner, height=ih, corner_radius=0.09,
                                 stroke_width=0, fill_color=accent, fill_opacity=0.2)
        sun = Circle(radius=0.1, stroke_width=0, fill_color=ACCENT, fill_opacity=0.9)
        sun.move_to(block.get_corner(UR) + np.array([-0.24, -0.2, 0]))
        m1 = Triangle(stroke_width=0, fill_color=accent, fill_opacity=0.5).scale(0.22)
        m1.move_to(block.get_bottom() + np.array([-inner * 0.16, 0.16, 0]))
        m2 = Triangle(stroke_width=0, fill_color=accent, fill_opacity=0.38).scale(0.17)
        m2.move_to(block.get_bottom() + np.array([inner * 0.12, 0.12, 0]))
        parts.append(VGroup(block, m1, m2))
    ht = heart(color=BAD if liked else MUTED, s=0.7, filled=liked)
    likes = RoundedRectangle(width=inner * 0.34, height=0.1, corner_radius=0.05,
                             stroke_width=0, fill_color=MUTED, fill_opacity=0.6)
    likerow = VGroup(ht, likes).arrange(RIGHT, buff=0.12)
    parts.append(likerow)
    content = VGroup(*parts).arrange(DOWN, aligned_edge=LEFT, buff=0.13)
    card = RoundedRectangle(width=content.width + 2 * pad, height=content.height + 2 * pad,
                            corner_radius=0.13, stroke_color=FAINT, stroke_width=2.0,
                            fill_color=PANEL, fill_opacity=1.0)
    card.move_to(content)
    grp = VGroup(card, content)
    grp.card = card
    grp.heart = ht
    grp.scale(w / grp.width)
    return grp


def phone(w=2.7, h=5.2, screen_color=BG):
    """A phone: body, screen, notch. Returns group with .screen for placing a feed."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.34,
                            stroke_color=MUTED, stroke_width=3.5,
                            fill_color="#0A0E15", fill_opacity=1.0)
    screen = RoundedRectangle(width=w - 0.28, height=h - 0.5, corner_radius=0.24,
                              stroke_color=FAINT, stroke_width=1.5,
                              fill_color=screen_color, fill_opacity=1.0)
    screen.move_to(body)
    notch = RoundedRectangle(width=w * 0.34, height=0.16, corner_radius=0.08,
                             stroke_width=0, fill_color="#0A0E15", fill_opacity=1.0)
    notch.move_to(screen.get_top() + DOWN * 0.16)
    g = VGroup(body, screen, notch)
    g.screen = screen
    g.body = body
    return g


def redis_glyph(w=2.9, h=3.3, rows=4):
    """Redis feed cache: a red panel holding per-user feed lists (rows)."""
    bg = RoundedRectangle(width=w, height=h, corner_radius=0.16,
                          stroke_color=REDIS, stroke_width=3,
                          fill_color=REDIS, fill_opacity=0.07)
    zap = icon("zap", color=REDIS, height=0.34, fill=True)
    ttl = txt("Redis", fs=19, color=REDIS, weight="BOLD")
    sub = txt("feed cache", fs=13, color=MUTED)
    head = VGroup(zap, ttl).arrange(RIGHT, buff=0.12)
    head = VGroup(head, sub).arrange(DOWN, buff=0.06)
    head.move_to(bg.get_top() + DOWN * 0.42)
    g = VGroup(bg, head)
    # per-user feed rows ---------------------------------------------------- #
    feed_rows = VGroup()
    for _ in range(rows):
        who = person(color=AVATAR, s=0.42)
        cells = VGroup(*[RoundedRectangle(width=0.34, height=0.24, corner_radius=0.05,
                                          stroke_width=0, fill_color=AVATAR,
                                          fill_opacity=0.32) for _ in range(4)])
        cells.arrange(RIGHT, buff=0.08)
        row = VGroup(who, cells).arrange(RIGHT, buff=0.16)
        feed_rows.add(row)
    feed_rows.arrange(DOWN, aligned_edge=LEFT, buff=0.2)
    feed_rows.next_to(head, DOWN, buff=0.24)
    dots = txt("· · ·", fs=18, color=MUTED).next_to(feed_rows, DOWN, buff=0.12)
    g.add(feed_rows, dots)
    g.bg = bg
    g.rows = feed_rows
    return g


def node(icon_name, label, color, w=1.55, h=1.12, icon_h=0.5, icon_fill=False,
         icon_color=None):
    """A design-system service node: rounded box + centred SVG icon + label."""
    box = RoundedRectangle(width=w, height=h, corner_radius=0.16,
                           stroke_color=color, stroke_width=2.6,
                           fill_color=color, fill_opacity=0.07)
    ic = icon(icon_name, color=icon_color or color, height=icon_h, fill=icon_fill)
    ic.move_to(box).shift(UP * 0.14)
    lab = txt(label, fs=14, color=INK, weight="BOLD")
    if lab.width > w - 0.16:
        lab.scale_to_fit_width(w - 0.16)
    lab.move_to([box.get_center()[0], box.get_bottom()[1] + 0.22, 0])
    g = VGroup(box, ic, lab)
    g.box = box
    g.ic = ic
    return g


# ========================================================================== #
class _FeedBase(Scene):
    def setup(self):
        self.camera.background_color = BG
        self._cap = None
        self.hlrect = None

    # Slow every animation uniformly by stretching its run time (see ANIM_SLOW).
    # self.wait() routes through self.play(Wait(...)); do NOT scale those.
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
        title = txt(label, fs=32, color=INK, weight="BOLD")
        head = VGroup(VGroup(tagbox, tag), title).arrange(RIGHT, buff=0.3)
        head.to_corner(UL, buff=0.5)
        # keep the header from ever running under the right edge
        if head.width > 2 * config.frame_x_radius - 1.0:
            head.scale_to_fit_width(2 * config.frame_x_radius - 1.0).to_corner(UL, buff=0.5)
        line = Line(head.get_left(), head.get_right()).next_to(head, DOWN, buff=0.13)
        line.set_stroke(color=color, width=3)
        grp = VGroup(head, line)
        self.play(FadeIn(head, shift=RIGHT * 0.2), Create(line), run_time=0.7)
        self.header = grp
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
        ).set_stroke(width=3, color=BRAND)
        writer = txt("Created by Ptolémé", fs=28, color=BRAND)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.4)
        self.card_wait(0.6)
        if subtitle:
            sub = txt(subtitle, fs=30, color=MUTED)
            if sub.width > 12:
                sub.scale_to_fit_width(12)
            sub.move_to(header)
            self.play(Transform(header, sub), run_time=0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        return VGroup(header, writer, line)

    def play_intro(self):
        # signature fan-out glyph: one post bursting to a ring of avatars
        hub = post_card(w=1.5, accent=BRAND, img=False)
        hub.to_edge(UP, buff=1.05)
        ring = VGroup(*[person(color=BRAND, s=0.62) for _ in range(9)])
        for i, p in enumerate(ring):
            a = i * TAU / 9 + PI / 2
            p.move_to(hub.get_center() + 0.9 * np.array([np.cos(a), np.sin(a), 0]))
        spokes = VGroup(*[arr(hub.get_center(), p.get_center(), color=PUSH, sw=2.5,
                              buff=0.42, tip=0.1) for p in ring])
        self.play(FadeIn(hub, scale=0.8), run_time=0.7)
        self.play(LaggedStart(*[GrowArrow(s) for s in spokes], lag_ratio=0.06),
                  LaggedStart(*[FadeIn(p, scale=0.6) for p in ring], lag_ratio=0.06),
                  run_time=1.4)
        glyph = VGroup(hub, spokes, ring)
        grp = self._bookend_title(
            "Designing the News Feed",
            "push, pull, and the celebrity fan-out problem")
        self.card_wait(1.7)
        self.play(FadeOut(grp), FadeOut(glyph), run_time=0.9)
        self.card_wait(0.2)

    def play_outro(self):
        self.card_wait(0.3)
        header = txt("Thanks for watching!", fs=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=BRAND)
        writer = txt("Created by Ptolémé", fs=28, color=BRAND)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.2)
        self.card_wait(0.6)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.card_wait(1.6)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.0)
        self.card_wait(0.3)

    # ---- code panel (house helper, trimmed) ------------------------------- #
    def code_panel(self, spec, table, title="fanout.py", fs=CODE_FS,
                   indent_unit=0.5, line_buff=0.18, target_h=4.6, target_w=6.2):
        lines = []
        for indent, s in spec:
            if s == "":
                m = Rectangle(width=0.02, height=0.30, fill_opacity=0, stroke_opacity=0)
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
        ttl.next_to(dots, RIGHT, buff=0.34).set_y(bar.get_center()[1])
        code.shift(DOWN * 0.2)
        panel = VGroup(bg, bar, dots, ttl, code)
        panel.code = code
        return panel, lines

    def focus(self, panel, lines, idxs, color=ACCENT, rt=0.4, opacity=0.16):
        tops = [lines[i].get_top()[1] for i in idxs]
        bots = [lines[i].get_bottom()[1] for i in idxs]
        y_hi, y_lo = max(tops) + 0.05, min(bots) - 0.05
        rect = RoundedRectangle(width=panel[0].width - 0.34, height=(y_hi - y_lo),
                                corner_radius=0.08, stroke_width=0,
                                fill_color=color, fill_opacity=opacity)
        rect.move_to([panel[0].get_center()[0], (y_hi + y_lo) / 2, 0])
        if self.hlrect is None:
            self.hlrect = rect
            self.play(FadeIn(rect), run_time=rt)
        else:
            self.play(Transform(self.hlrect, rect), run_time=rt)
        return self.hlrect

    def roll(self, anchor, color, end, run_time, start=0, fs=52):
        """A rolling integer counter (comma-grouped) fixed at ``anchor``."""
        vt = ValueTracker(start)
        num = DecimalNumber(start, num_decimal_places=0, group_with_commas=True,
                            color=color, font_size=fs)

        def upd(m):
            m.set_value(vt.get_value())
            m.move_to(anchor)
        num.add_updater(upd)
        self.add(num)
        self.play(vt.animate.set_value(end), run_time=run_time, rate_func=rush_into)
        return num, vt

    # ====================================================================== #
    # Scene 1 — Your Feed (how a user interacts)
    # ====================================================================== #
    def scene_feed(self):
        self.section_header("01", "Your Feed", BRAND)

        ph = phone(w=2.95, h=5.35).to_edge(RIGHT, buff=1.0).shift(DOWN * 0.12)
        self.play(FadeIn(ph, shift=UP * 0.2), run_time=0.7)
        self.say("You open the app…", color=BRAND)
        self.beat(0.8)

        # the feed populates, top to bottom -------------------------------- #
        scr = ph.screen
        cw = scr.width - 0.34
        cards = VGroup(*[post_card(w=cw, accent=c, liked=False)
                         for c in (AVATAR, GOOD, ACCENT)])
        cards.arrange(DOWN, buff=0.18)
        avail = scr.height - 0.4
        if cards.height > avail:
            cards.scale(avail / cards.height)
        cards.move_to(scr).align_to(scr, UP).shift(DOWN * 0.28)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.3) for c in cards],
                              lag_ratio=0.25), run_time=1.3)
        self.say("…and your feed is already there — in milliseconds.", color=INK)
        self.beat(1.6)

        # a like — a real interaction -------------------------------------- #
        mid = cards[1]
        self.play(Indicate(mid.heart, color=BAD, scale_factor=1.7), run_time=0.5)
        self.play(mid.heart.animate.set_color(BAD),
                  Flash(mid.heart.get_center(), color=BAD, line_length=0.12,
                        num_lines=10), run_time=0.4)
        self.say("You scroll. You like. You move on.", color=MUTED)
        self.beat(1.2)

        # the feed = posts from the accounts you follow -------------------- #
        follows = VGroup(*[avatar_tile(color=c, size=0.74) for c in (GOOD, ACCENT, PULL)])
        follows.arrange(DOWN, buff=0.42).to_edge(LEFT, buff=1.25).shift(UP * 0.25)
        flbl = txt("accounts you follow", fs=17, color=MUTED)
        flbl.next_to(follows, DOWN, buff=0.3)
        tgt = scr.get_left() + LEFT * 0.05
        fan = VGroup(*[arr(a.get_right(), [tgt[0], a.get_center()[1] * 0.5, 0],
                           color=BRAND, sw=2.5, buff=0.18, tip=0.14) for a in follows])
        self.play(LaggedStart(*[FadeIn(a, shift=RIGHT * 0.2) for a in follows],
                              lag_ratio=0.2), FadeIn(flbl), run_time=1.0)
        self.play(LaggedStart(*[GrowArrow(a) for a in fan], lag_ratio=0.15), run_time=0.9)
        self.say("Your feed is the latest posts from the people you follow.", color=INK)
        self.beat(1.8)

        # the question that drives the rest of the film -------------------- #
        self.play(FadeOut(follows), FadeOut(flbl), FadeOut(fan), run_time=0.5)
        self.say("So when someone posts — how does it reach every follower's feed, fast?",
                 color=ACCENT, fs=24)
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — Fan-out on Write (PUSH)
    # ====================================================================== #
    def scene_push(self):
        self.section_header("02", "Fan-out on Write  ·  Push", PUSH)

        # the author, left ------------------------------------------------- #
        alice = avatar_tile(color=AVATAR, size=0.95)
        alab = txt("Alice", fs=18, color=INK, weight="BOLD")
        afol = txt("200 followers", fs=15, color=MUTED)
        author = VGroup(alice, alab, afol).arrange(DOWN, buff=0.12)
        author.to_edge(LEFT, buff=0.9).shift(UP * 0.9)
        apost = post_card(w=1.9, accent=AVATAR, img=False)
        apost.next_to(author, DOWN, buff=0.45)
        self.play(FadeIn(author, shift=UP * 0.2), run_time=0.6)
        self.say("Alice posts.", color=INK)
        self.play(FadeIn(apost, scale=0.8), run_time=0.5)
        self.beat(0.9)

        # post service, middle --------------------------------------------- #
        psvc = node("post", "Post Service", WRITEC, w=1.7, h=1.1)
        psvc.move_to([-1.7, 0.3, 0])
        # redis with per-user feeds, right --------------------------------- #
        redis = redis_glyph(w=3.0, h=3.5, rows=4).move_to([3.0, -0.15, 0])
        feed_lbl = txt("one feed list per follower", fs=15, color=MUTED)
        feed_lbl.next_to(redis, UP, buff=0.16)
        self.play(FadeIn(psvc, shift=UP * 0.15), run_time=0.5)
        self.play(FadeIn(redis, shift=UP * 0.15), FadeIn(feed_lbl), run_time=0.8)

        # Alice's post travels to the post service ------------------------- #
        token = apost.copy().scale(0.5)
        self.play(token.animate.move_to(psvc.get_center()).scale(0.7), run_time=0.7)
        self.play(FadeOut(token, scale=0.5),
                  Flash(psvc.get_center(), color=WRITEC, line_length=0.16), run_time=0.4)
        self.say("Fan-out on write: copy it into every follower's feed — now.", color=PUSH)

        # fan-out: a gold token into the front of each feed list ----------- #
        drops = VGroup(*[Dot(radius=0.07, color=PUSH).move_to(psvc.get_right())
                         for _ in redis.rows])
        moves = []
        for d, row in zip(drops, redis.rows):
            dest = row[1].get_left() + LEFT * 0.02
            moves.append(d.animate.move_to(dest))
        self.play(LaggedStart(*moves, lag_ratio=0.18), run_time=1.1)
        self.play(*[row[1][0].animate.set_fill(PUSH, 0.95).set_stroke(PUSH, 1.5)
                    for row in redis.rows],
                  FadeOut(drops), run_time=0.4)
        # count the writes -------------------------------------------------- #
        cpos = [0.6, 2.35, 0]
        wlab = txt("writes", fs=18, color=PUSH).move_to([cpos[0], cpos[1] - 0.42, 0])
        num, _ = self.roll(cpos, PUSH, 200, run_time=1.1, fs=40)
        self.play(FadeIn(wlab), run_time=0.3)
        self.beat(1.4)

        # a follower opens the app → the post is already waiting ----------- #
        bob = phone(w=1.5, h=2.7).move_to([5.75, -0.35, 0])
        self.play(FadeIn(bob, shift=UP * 0.15), run_time=0.5)
        pull = arr(redis.get_right(), bob.get_left(), color=READC, sw=3, buff=0.14)
        card = post_card(w=bob.screen.width - 0.24, accent=AVATAR)
        if card.height > bob.screen.height - 0.4:
            card.scale((bob.screen.height - 0.4) / card.height)
        card.move_to(bob.screen)
        card.card.set_stroke(PUSH, 2.5)
        self.play(GrowArrow(pull), run_time=0.5)
        self.play(FadeIn(card, shift=UP * 0.2), run_time=0.6)
        self.say("A follower opens the app — the feed is already built. Reads are instant.",
                 color=READC, fs=23)
        self.beat(1.8)

        # takeaway ---------------------------------------------------------- #
        self.play(FadeOut(self._cap), run_time=0.3)
        self._cap = None
        punch = txt("200 followers  →  200 quick writes.  Perfect for a normal account.",
                    fs=25, color=PUSH, weight="BOLD").to_edge(DOWN, buff=0.5)
        if punch.width > 12.6:
            punch.scale_to_fit_width(12.6)
        self.play(Write(punch), run_time=1.0)
        self.beat(1.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — The Celebrity Problem
    # ====================================================================== #
    def scene_celebrity(self):
        self.section_header("03", "The Celebrity Problem", BAD)

        # the celebrity, left ---------------------------------------------- #
        star = avatar_tile(color=CELEB, size=1.0, badge=True)
        slab = txt("Celebrity", fs=18, color=CELEB, weight="BOLD")
        sfol = txt("100,000,000 followers", fs=15, color=MUTED)
        author = VGroup(star, slab, sfol).arrange(DOWN, buff=0.12)
        author.move_to([-5.2, 0.6, 0])
        psvc = node("post", "Post Service", WRITEC, w=1.5, h=1.0).move_to([-3.2, 0.6, 0])
        kafka = node("kafka", "Kafka", KAFKA, w=1.4, h=1.0).move_to([-1.35, 0.6, 0])
        klab = txt("fan-out queue", fs=14, color=KAFKA).next_to(kafka, DOWN, buff=0.12)
        self.play(FadeIn(author, shift=UP * 0.2), run_time=0.6)
        self.play(FadeIn(psvc), FadeIn(kafka), FadeIn(klab), run_time=0.6)
        self.say("Now a celebrity posts — once.", color=CELEB)
        self.beat(1.0)

        # the wall of followers, right ------------------------------------- #
        wall = VGroup(*[Dot(radius=0.045, color=MUTED, fill_opacity=0.45)
                        for _ in range(12 * 16)])
        wall.arrange_in_grid(rows=12, cols=16, buff=0.12).move_to([3.1, -0.25, 0])
        self.play(LaggedStart(*[FadeIn(d) for d in wall], lag_ratio=0.002), run_time=1.0)

        # the push explodes: a flood of writes + a rolling counter --------- #
        self.say("Push would copy that one post 100 million times.", color=BAD)
        cpos = [1.2, 3.0, 0]
        wlbl = txt("writes", fs=18, color=BAD).move_to([cpos[0], cpos[1] - 0.5, 0])
        self.add(wlbl)
        flood = VGroup(*[Dot(radius=0.06, color=PUSH).move_to(kafka.get_right())
                         for _ in range(46)])
        targets = np.random.default_rng(3).choice(len(wall), size=46, replace=False)
        moves = [d.animate.move_to(wall[t].get_center()).set_color(BAD)
                 for d, t in zip(flood, targets)]
        self.add(flood)
        self.play(LaggedStart(*moves, lag_ratio=0.03), run_time=1.6)
        # the counter races up as the wall turns hot
        num, _ = self.roll(cpos, PUSH, 100_000_000, run_time=1.8, fs=50)
        self.play(*[wall[t].animate.set_color(BAD).set_opacity(0.9) for t in targets],
                  num.animate.set_color(BAD), FadeOut(flood), run_time=0.6)
        self.beat(1.2)

        # the fallout: backlog, hot shards, lag ---------------------------- #
        self.play(kafka.box.animate.set_stroke(BAD).set_fill(BAD, 0.18),
                  kafka.ic.animate.set_stroke(BAD), run_time=0.4)
        lag = chip("feed lag:  minutes", BAD, fs=17, weight="BOLD")
        lag.next_to(kafka, DOWN, buff=0.7)
        waste = chip("most followers aren't even online", WARN, fs=16)
        waste.next_to(lag, DOWN, buff=0.25).align_to(lag, LEFT)
        self.play(FadeIn(lag, shift=UP * 0.1), run_time=0.5)
        self.say("The queue backs up, shards go hot, and feeds lag for minutes.", color=BAD)
        self.beat(1.4)
        self.play(FadeIn(waste, shift=UP * 0.1), run_time=0.5)
        self.beat(1.6)

        # punchline --------------------------------------------------------- #
        self.play(FadeOut(VGroup(wall, num, wlbl, lag, waste, kafka, klab, psvc, author)),
                  FadeOut(self._cap), run_time=0.7)
        self._cap = None
        punch = txt("Push alone doesn't scale.", fs=46, color=BAD, weight="BOLD")
        sub = txt("One post shouldn't cost 100 million writes.", fs=26, color=MUTED)
        grp = VGroup(punch, sub).arrange(DOWN, buff=0.35)
        self.play(Write(punch), run_time=1.0)
        self.play(FadeIn(sub, shift=UP * 0.2), run_time=0.6)
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Push + Pull, the hybrid fix
    # ====================================================================== #
    def scene_hybrid(self):
        self.section_header("04", "Push for the Many, Pull for the Few", GOOD)

        # ---- Beat A: the decision --------------------------------------- #
        spec = [
            (0, "def on_new_post(author):"),
            (1, "n = follower_count(author)"),
            (1, "if n < CELEB_LIMIT:"),
            (2, "push_to_feeds(author)"),
            (1, "else:"),
            (2, "keep_in_hot_cache(author)"),
        ]
        table = {"def": KW, "if": KW, "else": KW, "push_to_feeds": PUSH,
                 "keep_in_hot_cache": PULL, "CELEB_LIMIT": ACCENT,
                 "follower_count": FN, "on_new_post": FN}
        panel, lines = self.code_panel(spec, table, title="fanout_worker.py",
                                       target_h=3.0, target_w=5.4, fs=19)
        panel.to_edge(LEFT, buff=0.7).shift(UP * 0.5)
        self.play(FadeIn(panel, shift=UP * 0.15), run_time=0.7)
        self.say("The fan-out worker checks one number: how many followers.", color=INK)
        self.beat(1.4)

        # routing on the right --------------------------------------------- #
        normal = avatar_tile(color=AVATAR, size=0.7)
        nlab = txt("normal author", fs=14, color=MUTED).next_to(normal, DOWN, buff=0.1)
        normal_g = VGroup(normal, nlab).move_to([2.6, 1.75, 0])
        star = avatar_tile(color=CELEB, size=0.7, badge=True)
        clab = txt("celebrity", fs=14, color=MUTED).next_to(star, DOWN, buff=0.1)
        star_g = VGroup(star, clab).move_to([2.6, -1.15, 0])
        feeds = chip("→ push to 200 feeds", PUSH, fs=15, weight="BOLD").move_to([5.2, 1.75, 0])
        hot = chip("→ kept in 1 hot cache", PULL, fs=15, weight="BOLD").move_to([5.2, -1.15, 0])
        a_push = arr(normal.get_right(), feeds.get_left(), color=PUSH, sw=3.5)
        a_pull = arr(star.get_right(), hot.get_left(), color=PULL, sw=3.5)

        self.focus(panel, lines, [2, 3], color=PUSH)
        self.play(FadeIn(normal_g, shift=UP * 0.1), run_time=0.4)
        self.play(GrowArrow(a_push), FadeIn(feeds, shift=RIGHT * 0.1), run_time=0.6)
        self.say("Few followers?  Push the post into every feed.", color=PUSH)
        self.beat(1.5)

        self.focus(panel, lines, [4, 5], color=PULL)
        self.play(FadeIn(star_g, shift=UP * 0.1), run_time=0.4)
        self.play(GrowArrow(a_pull), FadeIn(hot, shift=RIGHT * 0.1), run_time=0.6)
        self.say("Millions?  Don't fan out — keep it in one hot cache, pull it later.",
                 color=PULL)
        self.beat(1.8)

        # ---- Beat B: the read merge ------------------------------------- #
        beatA = VGroup(panel, normal_g, star_g, feeds, hot, a_push, a_pull, self.hlrect)
        self.play(FadeOut(beatA), FadeOut(self._cap), run_time=0.6)
        self.hlrect = None
        self._cap = None

        # two sources (top), the merger (middle), your phone (bottom). Descriptor
        # labels sit BELOW each source; the arrows exit the boxes' INNER sides, so
        # they never cross the labels.
        redis = node("zap", "Redis feeds", REDIS, w=1.95, h=1.08).move_to([-4.35, 1.85, 0])
        cache = node("zap", "Hot cache", PULL, w=1.95, h=1.08).move_to([4.35, 1.85, 0])
        tl = node("list", "Timeline Svc", READC, w=2.0, h=1.08).move_to([0, 0.35, 0])
        rlab = txt("your prebuilt feed", fs=14, color=PUSH).next_to(redis, DOWN, buff=0.14)
        clab2 = txt("the few you follow", fs=14, color=PULL).next_to(cache, DOWN, buff=0.14)
        you = phone(w=1.75, h=2.15).move_to([0, -2.02, 0])
        self.play(FadeIn(redis, shift=DOWN * 0.1), FadeIn(rlab),
                  FadeIn(cache, shift=DOWN * 0.1), FadeIn(clab2),
                  FadeIn(tl, shift=UP * 0.1), FadeIn(you, shift=UP * 0.1), run_time=0.9)

        a_read = arr(redis.box.get_right(), tl.box.get_left(), color=PUSH, sw=3, buff=0.14)
        a_pull = arr(cache.box.get_left(), tl.box.get_right(), color=PULL, sw=3, buff=0.14)
        a_out = arr(tl.box.get_bottom(), you.get_top(), color=READC, sw=3, buff=0.14)
        merge = txt("⊕", fs=30, color=READC, weight="BOLD").move_to(
            tl.box.get_top() + UP * 0.3)
        self.play(GrowArrow(a_read), GrowArrow(a_pull), run_time=0.6)

        gold = VGroup(*[Dot(radius=0.06, color=PUSH).move_to(redis.box.get_right())
                        for _ in range(3)])
        cyan = VGroup(*[Dot(radius=0.06, color=PULL).move_to(cache.box.get_left())
                        for _ in range(2)])
        self.add(gold, cyan)
        self.play(LaggedStart(*[d.animate.move_to(tl.box.get_center()) for d in gold],
                              *[d.animate.move_to(tl.box.get_center()) for d in cyan],
                              lag_ratio=0.1), FadeIn(merge), run_time=1.1)
        self.play(FadeOut(gold), FadeOut(cyan),
                  Flash(tl.box.get_center(), color=READC, line_length=0.18), run_time=0.4)
        self.say("Read your prebuilt feed  ⊕  pull the few celebrities you follow…",
                 color=INK, fs=23)
        self.beat(1.4)

        # merged, ranked feed drops into the phone ------------------------- #
        self.play(GrowArrow(a_out), run_time=0.4)
        cw2 = you.screen.width - 0.2
        feed = VGroup(post_card(w=cw2, accent=CELEB, liked=True),
                      post_card(w=cw2, accent=AVATAR),
                      post_card(w=cw2, accent=GOOD)).arrange(DOWN, buff=0.12)
        avail = you.screen.height - 0.3
        if feed.height > avail:
            feed.scale(avail / feed.height)
        feed.move_to(you.screen)
        feed[0].card.set_stroke(PULL, 2.5)   # a pulled celebrity post
        feed[1].card.set_stroke(PUSH, 2.5)   # pushed posts
        feed[2].card.set_stroke(PUSH, 2.5)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in feed],
                              lag_ratio=0.2), run_time=0.9)
        self.say("…merge and rank the two — that's your timeline.", color=READC, fs=23)
        self.beat(1.8)

        self.play(FadeOut(self._cap), run_time=0.3)
        self._cap = None
        punch = txt("Push for the many.  Pull for the few.  Bounded either way.",
                    fs=25, color=GOOD, weight="BOLD").to_edge(DOWN, buff=0.5)
        if punch.width > 12.6:
            punch.scale_to_fit_width(12.6)
        self.play(Write(punch), run_time=1.0)
        self.beat(1.8)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — The production architecture
    # ====================================================================== #
    def scene_architecture(self):
        self.section_header("05", "The Production Architecture", BRAND)

        # nodes on a compact grid: write row (top), client/gateway/redis (middle),
        # read row (bottom). Redis sits on the vertical spine under Fan-out so both
        # the write (down) and the read (up) meet it cleanly.
        N = {}
        specs = [
            ("phone",   node("smartphone", "Client", BRAND, w=1.3, h=1.15, icon_h=0.6), (-6.0, -0.35)),
            ("gateway", node("gateway", "Gateway + LB", GATE, w=1.55, h=1.05), (-4.15, -0.35)),
            ("post",    node("post", "Post Service", WRITEC, w=1.55, h=1.02), (-1.95, 1.42)),
            ("kafka",   node("kafka", "Kafka", KAFKA, w=1.35, h=1.02), (0.35, 1.42)),
            ("fanout",  node("share", "Fan-out", PUSH, w=1.45, h=1.02), (2.55, 1.42)),
            ("graph",   node("users", "Social Graph", DBC, w=1.7, h=1.02), (4.85, 1.42)),
            ("redis",   node("zap", "Redis feeds", REDIS, w=1.6, h=1.12), (2.55, -0.5)),
            ("tl",      node("list", "Timeline Svc", READC, w=1.6, h=1.02), (-4.15, -2.2)),
            ("postdb",  node("database", "Post DB", DBC, w=1.4, h=1.02), (-1.7, -2.2)),
            ("store",   node("bucket", "Object Store", STORE, w=1.55, h=1.02), (4.15, -2.2)),
            ("cdn",     node("globe", "CDN", CDNC, w=1.3, h=1.02), (5.8, -2.2)),
        ]
        parts = VGroup()
        for key, g, pos in specs:
            g.move_to([pos[0], pos[1], 0])
            N[key] = g
            parts.add(g)
        self.play(LaggedStart(*[FadeIn(g, shift=UP * 0.1) for g in parts],
                              lag_ratio=0.07), run_time=1.9)
        self.beat(0.7)

        def B(k):
            return N[k].box

        def pt(x, y):
            return np.array([x, y, 0.0])

        def straight(a, b, color, sw=3.2, tip=0.2, buff=0.12, opacity=1.0):
            pa, pb = a.get_center(), b.get_center()
            d = _unit(pb - pa)
            p1 = a.get_boundary_point(d) + d * buff
            p2 = b.get_boundary_point(-d) - d * buff
            m = Arrow(p1, p2, buff=0, color=color, stroke_width=sw,
                      max_tip_length_to_length_ratio=0.4, tip_length=tip)
            if opacity < 1.0:
                m.set_stroke(opacity=opacity)
            return m

        def elbow(corners, color, sw=3.2, tip=0.2):
            pts = [c if len(c) == 3 else pt(c[0], c[1]) for c in corners]
            shaft = VMobject().set_points_as_corners(pts).set_stroke(color, width=sw)
            a, b = pts[-2], pts[-1]
            d = _unit(b - a)
            perp = np.array([-d[1], d[0], 0.0])
            head = Polygon(b, b - d * tip + perp * tip * 0.55,
                           b - d * tip - perp * tip * 0.55,
                           stroke_width=0, fill_color=color, fill_opacity=1.0)
            return VGroup(shaft, head)

        # ---- WRITE path (blue), all straight, no crossings -------------- #
        w_pg = straight(B("phone"), B("gateway"), WRITEC)
        w_gp = straight(B("gateway"), B("post"), WRITEC)
        w_pk = straight(B("post"), B("kafka"), WRITEC)
        w_kf = straight(B("kafka"), B("fanout"), WRITEC)
        w_fr = straight(B("fanout"), B("redis"), WRITEC)          # down the spine
        w_fg = straight(B("fanout"), B("graph"), PUSH, sw=2.6, opacity=0.85)
        w_pd = straight(B("post"), B("postdb"), WRITEC, sw=2.6, opacity=0.85)  # persist
        m_sc = straight(B("store"), B("cdn"), MUTED, sw=2.4, opacity=0.65)     # media
        chain = [w_pg, w_gp, w_pk, w_kf, w_fr]

        self.say("A write:  Alice posts.", color=WRITEC)
        self.play(LaggedStart(*[GrowArrow(a) for a in chain], lag_ratio=0.42),
                  run_time=1.9)
        tok = Dot(radius=0.09, color=WRITEC).move_to(B("phone").get_center())
        self.add(tok)
        for k in ("gateway", "post", "kafka", "fanout", "redis"):
            self.play(tok.animate.move_to(B(k).get_center()), run_time=0.3)
        self.play(Flash(B("redis").get_center(), color=REDIS, line_length=0.2),
                  FadeOut(tok), run_time=0.4)
        self.play(GrowArrow(w_fg), GrowArrow(w_pd), Create(m_sc), run_time=0.7)
        self.say("Persist the post, read the social graph, fan out into every Redis feed.",
                 color=WRITEC, fs=22)
        self.beat(1.7)

        # dim the write path so the read path reads on its own
        wpath = [w_pg, w_gp, w_pk, w_kf, w_fr, w_fg, w_pd]
        self.play(*[a.animate.set_opacity(0.14) for a in wpath],
                  m_sc.animate.set_opacity(0.1), run_time=0.5)

        # ---- READ path (green) ------------------------------------------ #
        r_gt = straight(B("gateway"), B("tl"), READC)                    # down
        r_tpd = straight(B("tl"), B("postdb"), READC, sw=2.6)            # pull + hydrate
        r_tr = elbow([B("tl").get_bottom(), pt(B("tl").get_center()[0], -2.98),
                      pt(B("redis").get_center()[0], -2.98), B("redis").get_bottom()],
                     READC)                                              # read feed
        r_tp = elbow([B("tl").get_left(),
                      pt(B("phone").get_center()[0], B("tl").get_center()[1]),
                      B("phone").get_bottom()], READC)                   # ranked feed back
        self.say("A read:  you open the app.", color=READC)
        self.play(GrowArrow(r_gt), run_time=0.5)
        self.play(Create(r_tr), GrowArrow(r_tpd), run_time=0.9)
        rtok = Dot(radius=0.09, color=READC).move_to(B("gateway").get_center())
        self.add(rtok)
        for k in ("tl", "redis"):
            self.play(rtok.animate.move_to(B(k).get_center()), run_time=0.3)
        self.say("Timeline service reads your feed, pulls & hydrates from Post DB…",
                 color=READC, fs=22)
        self.beat(1.3)
        self.play(Create(r_tp), rtok.animate.move_to(B("phone").get_center()),
                  run_time=0.8)
        self.play(FadeOut(rtok), run_time=0.2)
        self.say("…and returns a ranked timeline — media served from the CDN.",
                 color=READC, fs=22)
        self.beat(1.9)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 6 — Recap
    # ====================================================================== #
    def scene_recap(self):
        self.section_header("06", "The Takeaway", ACCENT)

        items = [
            ("Push  ·  fan-out on write", "normal authors — the feed is prebuilt, reads are instant", PUSH),
            ("Pull  ·  fan-out on read", "celebrities — no write storm, kept in one hot cache", PULL),
            ("Redis holds every feed", "one precomputed list per user — the read is O(1)", REDIS),
            ("Merge, then rank", "read = your pushed feed  ⊕  a pull from the few you follow", READC),
        ]
        rows = VGroup()
        for title_s, sub_s, col in items:
            tick = make_tick(col, sw=6).scale(0.95)
            head = txt(title_s, fs=24, color=INK, weight="BOLD")
            sub = txt(sub_s, fs=17, color=MUTED)
            body = VGroup(head, sub).arrange(DOWN, aligned_edge=LEFT, buff=0.07)
            row = VGroup(tick, body).arrange(RIGHT, buff=0.34, aligned_edge=UP)
            rows.add(row)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.34)
        rows.scale_to_fit_height(4.4).move_to(UP * 0.15)
        if rows.width > 12.4:
            rows.scale_to_fit_width(12.4)

        self.say("Push for the many, pull for the few:", color=ACCENT)
        for row in rows:
            self.play(GrowFromCenter(row[0]), FadeIn(row[1], shift=RIGHT * 0.2),
                      run_time=0.5)
            self.beat(0.7)
        self.beat(1.2)

        punch = txt("200 or 100,000,000 followers — the feed stays fast.",
                    fs=25, color=BRAND, weight="BOLD").to_edge(DOWN, buff=0.5)
        if punch.width > 12.6:
            punch.scale_to_fit_width(12.6)
        self.play(FadeOut(self._cap), run_time=0.3)
        self._cap = None
        self.play(Write(punch), run_time=1.0)
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ---- the whole film --------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_feed()
        self.scene_push()
        self.scene_celebrity()
        self.scene_hybrid()
        self.scene_architecture()
        self.scene_recap()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_FeedBase):
    def construct(self):
        self.play_intro()


class Feed(_FeedBase):
    def construct(self):
        self.scene_feed()


class Push(_FeedBase):
    def construct(self):
        self.scene_push()


class Celebrity(_FeedBase):
    def construct(self):
        self.scene_celebrity()


class Hybrid(_FeedBase):
    def construct(self):
        self.scene_hybrid()


class Architecture(_FeedBase):
    def construct(self):
        self.scene_architecture()


class Recap(_FeedBase):
    def construct(self):
        self.scene_recap()


class Outro(_FeedBase):
    def construct(self):
        self.play_outro()


class NewsFeed(_FeedBase):
    """The whole ~3-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    NewsFeed().render()

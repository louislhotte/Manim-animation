"""Content Delivery Networks — a short, house-style explainer.

A self-explanatory (no voice-over) film that answers, in four beats, what a CDN
is, why it exists and when to reach for one in a system design:

    1. Problem  -- your app lives on one origin server, in one place; users are
                   spread across the planet. Distance adds latency, and a single
                   origin strains under the whole world's traffic.
    2. Idea     -- a CDN is a globally distributed network of edge servers that
                   keep cached copies of your content close to users. Requests
                   travel a short hop instead of across an ocean.
    3. How      -- the request flow: cache MISS (edge fetches from the origin and
                   stores a copy) vs. cache HIT (served straight from the edge);
                   TTLs and nearest-edge (anycast/DNS) routing.
    4. Use      -- what to cache (static/media) vs. what stays at the origin
                   (dynamic/personalised), when a CDN pays off, and the payoff:
                   lower latency, less origin load, resilience, cheaper egress
                   and built-in security.

Bookended by the channel's intro card and the "Thank you for watching!" outro,
matching animations/Gravity/gravity.py and the rest of the series.

Everything uses ``Text`` (Pango), never ``Tex`` — so it renders with no LaTeX
toolchain and stays fast to iterate on.

Scenes are exposed individually (``Problem``, ``Idea``, ``HowItWorks``,
``UseCases``, ``Intro``, ``Outro``) and as one film (``CDN``).

Env knobs:
    CDN_QUICK=1        shorten every hold for a fast sanity render
    CDN_DELAY=<float>  override the reading rhythm (seconds per unit hold)
"""
from __future__ import annotations

import math
import os

import numpy as np
from manim import *

# --- crisp text ------------------------------------------------------------ #
# Manim's ``Text`` quantises glyph positions badly at small font sizes, so body
# text below ~20 pt comes out with uneven letter/word spacing. Work around it
# once, here: always render glyphs at a large, crisp base size and scale the
# mobject *down* to the requested size. This shadows manim's ``Text`` so every
# call in this module benefits automatically.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


QUICK = os.environ.get("CDN_QUICK") == "1"
# One knob for pacing: every reading "hold" is scaled by this. QUICK collapses
# the holds for a fast iteration render; otherwise it sets a relaxed, readable
# rhythm that keeps the whole film around three minutes.
DELAY = float(os.environ.get("CDN_DELAY", "0.3" if QUICK else "1.45"))

# ---- palette (shared house style) ---------------------------------------- #
BG = "#0E1117"          # dark slate background
PANEL = "#161B26"       # server chassis / card fill
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text / axes
FAINT = "#3A4152"       # gridlines / guides
GOLD = "#FFD166"        # highlight / headings accent
ORIGIN_C = "#FFB703"    # the origin server (amber)
EDGE_C = "#3DD68C"      # edge servers / cache (green)
USER_C = "#5B8DEF"      # users / clients (blue)
HIT_C = "#3DD68C"       # cache hit (green)
MISS_C = "#FF5C5C"      # cache miss / overload (red)
REQ_C = "#4CC9F0"       # request packet (cyan)
RES_C = "#3DD68C"       # response / content packet (green)
WARN = "#FF5C5C"        # warning / problem accent
GOOD = "#3DD68C"        # ✓ green
GLOBE_EDGE = "#4A5568"  # globe rim
GLOBE_FILL = "#12233A"  # globe disk tint
GRID = "#33405A"        # globe wireframe

FRAME_R = config.frame_x_radius   # 7.111…

# Baked planet texture (see assets/make_planet.py). Absolute path so it resolves
# no matter what cwd manim runs from.
_PLANET_IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "assets", "planet_blue.png")


def lerp(a, b, t):
    return a + (b - a) * t


def outdir(fx, fy):
    v = np.array([fx, fy, 0.0])
    n = np.linalg.norm(v)
    return v / n if n > 1e-6 else np.array([0.0, 1.0, 0.0])


# The five "regions" placed on the globe, as fractions of its radius from the
# centre. Geography is suggested by the labels, not by exact coordinates.
REGIONS = {
    "origin":   dict(fx=0.05,  fy=0.40,  label="Frankfurt"),   # Europe
    "london":   dict(fx=-0.34, fy=0.50,  label="London"),      # UK
    "mumbai":   dict(fx=0.60,  fy=0.10,  label="Mumbai"),      # S. Asia
    "capetown": dict(fx=0.10,  fy=-0.66, label="Cape Town"),   # S. Africa
    "lagos":    dict(fx=-0.20, fy=-0.18, label="Lagos"),       # W. Africa
}
USER_KEYS = ["london", "mumbai", "capetown", "lagos"]
FAR_KEY = "capetown"   # the far-from-origin user for the latency demos


# ========================================================================== #
# Small reusable pieces
# ========================================================================== #
def server(w=0.72, h=0.56, color=EDGE_C, fill=PANEL, n_slots=3, led=True):
    """A little server/rack glyph: chassis + drive slots + a status LED."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.07,
                            stroke_color=color, stroke_width=2.2,
                            fill_color=fill, fill_opacity=1)
    parts = VGroup(body)
    for y in np.linspace(h * 0.26, -h * 0.26, n_slots):
        ln = Line([-w * 0.30, y, 0], [w * 0.16, y, 0],
                  stroke_color=color, stroke_width=2).set_opacity(0.6)
        parts.add(ln)
    if led:
        d = Dot(radius=0.045, color=color)
        d.move_to(body.get_corner(UR) + np.array([-0.11, -0.12, 0]))
        parts.add(d)
    return parts


def origin_icon(s=1.0):
    """The origin server: an amber rack with a soft glow behind it."""
    rack = server(w=0.92 * s, h=0.72 * s, color=ORIGIN_C, n_slots=3)
    glow = Circle(radius=0.72 * s, color=ORIGIN_C, fill_opacity=0.16,
                  stroke_width=0).move_to(rack)
    return VGroup(glow, rack)


def edge_icon(s=1.0):
    """An edge/PoP server: a small green rack with a faint glow."""
    rack = server(w=0.58 * s, h=0.46 * s, color=EDGE_C, n_slots=3)
    glow = Circle(radius=0.44 * s, color=EDGE_C, fill_opacity=0.12,
                  stroke_width=0).move_to(rack)
    return VGroup(glow, rack)


def client_dot(color=USER_C, r=0.10):
    """A user location marker that pops on land or ocean: a soft dark halo, a
    white ring and a bright core (a little map pin)."""
    back = Circle(radius=r * 2.0, stroke_width=0, fill_color=BG, fill_opacity=0.5)
    ring = Circle(radius=r * 2.0, stroke_color=WHITE, stroke_width=2.4, fill_opacity=0)
    core = Dot(radius=r, color=color).set_stroke(WHITE, 1.4)
    return VGroup(back, ring, core)


def person(color=USER_C, s=1.0):
    """A simple 'user' silhouette: head + body."""
    body = RoundedRectangle(width=0.44 * s, height=0.5 * s, corner_radius=0.12 * s,
                            color=color, fill_opacity=1, stroke_width=0)
    head = Circle(radius=0.16 * s, color=color, fill_opacity=1, stroke_width=0)
    head.next_to(body, UP, buff=0.03 * s)
    return VGroup(body, head)


def content_chip(color=EDGE_C, filled=True, s=1.0):
    """A tiny 'stored copy' chip — filled (cached) or hollow (empty)."""
    return RoundedRectangle(width=0.30 * s, height=0.24 * s, corner_radius=0.05,
                            stroke_color=color, stroke_width=2.2,
                            fill_color=color, fill_opacity=0.9 if filled else 0.0)


def globe(R=2.4, c=(0, -0.45, 0)):
    """A shaded blue 'planet' (baked texture) with a soft atmospheric halo."""
    c = np.array(c, float)
    planet = ImageMobject(_PLANET_IMG).move_to(c)
    planet.scale_to_fit_height(2 * R)
    atmo = Circle(radius=R * 1.012, stroke_color="#8FD4FF", stroke_width=3,
                  stroke_opacity=0.35, fill_opacity=0).move_to(c)
    glow = Circle(radius=R * 1.035, stroke_color="#4CC9F0", stroke_width=12,
                  stroke_opacity=0.08, fill_opacity=0).move_to(c)
    return Group(glow, atmo, planet)


def geo_label(txt, color=INK, fs=19, weight=None):
    """A map-style label on a translucent dark plate so it reads over the bright
    planet as well as the dark background."""
    kw = {"weight": weight} if weight else {}
    t = Text(txt, font_size=fs, color=color, **kw)
    plate = RoundedRectangle(width=t.width + 0.22, height=t.height + 0.14,
                             corner_radius=0.07, stroke_width=0,
                             fill_color=BG, fill_opacity=0.5).move_to(t)
    return VGroup(plate, t)


def gpoint(c, R, key):
    reg = REGIONS[key]
    return np.array(c, float) + np.array([reg["fx"] * R, reg["fy"] * R, 0.0])


def arc_path(p1, p2, center, bow=0.55):
    """A circular arc from p1 to p2 that bows *outward* from ``center``.

    Returns the solid arc (used both to draw a dashed copy and as a motion path).
    """
    p1 = np.array(p1, float)
    p2 = np.array(p2, float)
    c = np.array(center, float)
    mid = (p1 + p2) / 2
    outward = mid - c
    if np.linalg.norm(outward) < 1e-6:
        outward = np.array([0.0, 1.0, 0.0])
    d = p2 - p1
    perp = np.array([-d[1], d[0], 0.0])
    if np.linalg.norm(perp) < 1e-6:
        perp = np.array([0.0, 1.0, 0.0])
    sign = 1.0 if np.dot(perp, outward) >= 0 else -1.0
    return ArcBetweenPoints(p1, p2, angle=sign * bow)


def dashed(vm, color=REQ_C, sw=3.0, n=26, opacity=0.9):
    dv = DashedVMobject(vm.copy(), num_dashes=n)
    dv.set_stroke(color, sw, opacity=opacity)
    return dv


# ========================================================================== #
class _CDNBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # ---- timing helpers --------------------------------------------------- #
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.0))

    def settle(self):
        self.wait(0.2 if QUICK else 1.5)

    def wipe(self, rt=0.6):
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)

    # ---- text helpers ----------------------------------------------------- #
    def section_header(self, label, color):
        txt = Text(label, font_size=33, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(txt.get_left(), txt.get_right()).next_to(txt, DOWN, buff=0.12)
        line.set_stroke(color=color, width=4)
        return VGroup(txt, line)

    def say(self, text, color=MUTED, fs=26, y=-3.5):
        """A bottom caption, width-clamped so it never runs off-screen."""
        m = Text(text, font_size=fs, color=color)
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
    def send(self, path, color=REQ_C, rt=1.0, r=0.085, keep=False, rate=linear):
        p = Dot(radius=r, color=color).set_stroke(INK, 1.0).move_to(path.get_start())
        self.add(p)
        self.play(MoveAlongPath(p, path), run_time=rt, rate_func=rate)
        if keep:
            return p
        self.remove(p)
        return None

    # ---- house-style intro / outro cards ---------------------------------- #
    def introduction(self, title1, title2):
        header = Text(title1, font_size=52, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=GOLD)
        writer = Text("Created by Ptolémé", font_size=28, color=USER_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])

        # a little packet zips along the title bar — a wink at content in flight
        pkt = Dot(radius=0.09, color=REQ_C).set_stroke(INK, 1.0)
        pkt.move_to(line.get_left())
        self.play(Write(header), Create(line), run_time=1.6)
        self.play(pkt.animate.move_to(line.get_right()), run_time=0.9, rate_func=linear)
        self.play(FadeOut(pkt, scale=0.4), run_time=0.3)
        self.card_wait(0.4)
        sub = Text(title2, font_size=30, color=MUTED)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.card_wait(1.8)
        return VGroup(header, writer, line)

    def play_intro(self):
        group = self.introduction(
            "Content Delivery Networks",
            "Why your app stays fast — everywhere · System Design",
        )
        self.play(FadeOut(group), run_time=1.0)
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
        self.play(Write(header), Create(line), run_time=1.5)
        self.card_wait(0.9)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.1)
        self.card_wait(2.0)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.3)
        self.card_wait(0.4)

    # ---- shared globe topology ------------------------------------------- #
    def build_globe(self, R=2.4, c=(0, -0.45, 0), with_origin=True):
        g = globe(R, c)
        users = {}
        labels = VGroup()
        for key in USER_KEYS:
            p = gpoint(c, R, key)
            d = client_dot(USER_C).move_to(p)
            lab = geo_label(REGIONS[key]["label"], fs=18)
            lab.next_to(d, outdir(REGIONS[key]["fx"], REGIONS[key]["fy"]), buff=0.1)
            users[key] = d
            labels.add(lab)
        obj = dict(globe=g, users=users, labels=labels, R=R, c=np.array(c, float))
        if with_origin:
            op = gpoint(c, R, "origin")
            origin = origin_icon(0.85).move_to(op)
            olab = geo_label("Origin", color=ORIGIN_C, fs=20, weight="BOLD")
            olab.next_to(origin, DOWN, buff=0.12)
            obj["origin"] = origin
            obj["origin_label"] = olab
            obj["origin_pt"] = op
        return obj

    # ====================================================================== #
    # Scene 1 — Problem: one origin, a whole planet of users
    # ====================================================================== #
    def scene_problem(self):
        header = self.section_header("The problem: one server, one place", WARN)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        t = self.build_globe()
        g, users, labels = t["globe"], t["users"], t["labels"]
        origin, olab = t["origin"], t["origin_label"]
        R, c, opt = t["R"], t["c"], t["origin_pt"]

        self.play(FadeIn(g), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(users[k], scale=0.5) for k in USER_KEYS],
                              lag_ratio=0.25, run_time=1.2),
                  LaggedStart(*[FadeIn(m) for m in labels], lag_ratio=0.25, run_time=1.2))
        cap = self.say("Your users are scattered across the whole planet.")
        self.play(FadeIn(cap), run_time=0.4)
        self.beat(1.3)

        self.play(FadeIn(origin, scale=0.6), FadeIn(olab), run_time=0.7)
        cap2 = self.say("But your app lives on an origin server in ONE location.")
        self.play(ReplacementTransform(cap, cap2), run_time=0.5)
        self.beat(1.5)

        # Focus on the far user (Cape Town): the long round-trip.
        syd = users[FAR_KEY]
        far = arc_path(syd.get_center(), opt, c, bow=0.62)
        far_dash = dashed(far, REQ_C, sw=3, n=30)
        self.play(FadeOut(cap2), run_time=0.3)
        cap3 = self.say("A request from Cape Town must cross continents to the origin…")
        self.play(FadeIn(cap3), Create(far_dash), run_time=0.7)
        self.send(far, REQ_C, rt=1.7)                       # request out
        back = arc_path(opt, syd.get_center(), c, bow=0.62)
        self.send(back, RES_C, rt=1.7)                      # response back

        badge_lines = VGroup(
            Text("Cape Town → Frankfurt", font_size=21, color=INK, weight="BOLD"),
            Text("≈ 9,000 km", font_size=20, color=MUTED),
            Text("≈ 150 ms round-trip", font_size=20, color=WARN, weight="BOLD"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        badge = VGroup(self.card_box(badge_lines, WARN, pad=0.26, fill_op=0.35), badge_lines)
        badge.to_edge(RIGHT, buff=0.5).shift(UP * 1.7)
        self.play(FadeIn(badge, shift=LEFT * 0.2), run_time=0.6)
        cap3b = self.say("…and every image, script and video makes that same trip.")
        self.play(ReplacementTransform(cap3, cap3b), run_time=0.5)
        self.beat(1.8)

        # Now the whole world hits the single origin at once → overload.
        self.play(FadeOut(far_dash), FadeOut(badge), run_time=0.4)
        arcs = [arc_path(users[k][1].get_center(), opt, c, bow=0.5) for k in USER_KEYS]
        dashes = VGroup(*[dashed(a, REQ_C, sw=2.4, n=22, opacity=0.7) for a in arcs])
        self.play(LaggedStart(*[Create(d) for d in dashes], lag_ratio=0.15, run_time=0.9))
        cap4 = self.say("And one origin has to serve the entire world at once.")
        self.play(ReplacementTransform(cap3b, cap4), run_time=0.5)
        # packets stream inward, repeatedly (track & remove so none linger)
        for _ in range(2 if not QUICK else 1):
            dots = [Dot(radius=0.07, color=REQ_C).set_stroke(INK, 1).move_to(a.get_start())
                    for a in arcs]
            self.play(LaggedStart(*[MoveAlongPath(d, a) for d, a in zip(dots, arcs)],
                                  lag_ratio=0.12, run_time=1.1), rate_func=linear)
            self.remove(*dots)
        # the origin strains: red pulse + overload tag
        red_ring = Circle(radius=0.95, color=MISS_C, stroke_width=5).move_to(origin)
        overtag = self.pill("origin overloaded", MISS_C, fs=20)
        overtag.next_to(origin, UP, buff=0.28)
        self.play(origin[0].animate.set_color(MISS_C).set_opacity(0.28),
                  origin[1][-1].animate.set_color(MISS_C),
                  FadeIn(overtag, shift=DOWN * 0.1), run_time=0.5)
        self.play(Flash(origin, color=MISS_C, flash_radius=0.9),
                  Create(red_ring), run_time=0.6)
        self.play(FadeOut(red_ring), run_time=0.4)
        self.beat(1.6)

        # Takeaway card.
        self.play(FadeOut(Group(g, *users.values(), labels,
                                origin, olab, overtag, dashes, cap4)), run_time=0.6)
        k1 = Text("Distance adds delay.", font_size=34, color=INK, weight="BOLD")
        k2 = Text("One server can't sit next to everyone.", font_size=34,
                  color=GOLD, weight="BOLD")
        VGroup(k1, k2).arrange(DOWN, buff=0.3).move_to(ORIGIN)
        self.play(FadeIn(k1, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(k2, shift=UP * 0.1), run_time=0.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — Idea: cache content close to users
    # ====================================================================== #
    def scene_idea(self):
        # Full-screen definition card first (no crowding), then the topology.
        title = Text("A CDN — Content Delivery Network", font_size=40,
                     color=GOLD, weight="BOLD").move_to([0, 1.2, 0])
        d1 = Text("A worldwide network of servers", font_size=30, color=INK)
        d2 = Text("that keep cached copies of your content", font_size=30, color=INK)
        d3 = Text("close to your users.", font_size=30, color=EDGE_C, weight="BOLD")
        body = VGroup(d1, d2, d3).arrange(DOWN, buff=0.2).next_to(title, DOWN, buff=0.55)
        self.play(Write(title), run_time=1.1)
        self.play(LaggedStart(*[FadeIn(m, shift=UP * 0.1) for m in (d1, d2, d3)],
                              lag_ratio=0.4, run_time=1.4))
        self.beat(2.0)
        self.play(FadeOut(VGroup(title, body)), run_time=0.6)

        header = self.section_header("The idea: bring content closer", EDGE_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        t = self.build_globe()
        g, users, labels = t["globe"], t["users"], t["labels"]
        origin, olab = t["origin"], t["origin_label"]
        R, c, opt = t["R"], t["c"], t["origin_pt"]
        self.play(FadeIn(g),
                  *[FadeIn(users[k]) for k in USER_KEYS], FadeIn(labels),
                  FadeIn(origin), FadeIn(olab), run_time=1.0)

        # place an edge server next to every user region; nudge the user dot and
        # its city label outward so the three read clearly instead of piling up
        edges = {}
        lab_of = {k: labels[i] for i, k in enumerate(USER_KEYS)}
        for k in USER_KEYS:
            e = edge_icon(0.8).move_to(users[k][1].get_center())
            od = outdir(REGIONS[k]["fx"], REGIONS[k]["fy"])
            users[k].generate_target()
            users[k].target.move_to(e.get_center() + od * 0.5)
            lab_of[k].generate_target()
            lab_of[k].target.next_to(users[k].target, od, buff=0.12)
            edges[k] = e

        cap = self.say("A CDN pushes copies of your content out to edge servers "
                       "near every region.")
        self.play(FadeIn(cap), run_time=0.4)
        # content fans out origin -> each edge, and each edge lights up "cached"
        for k in USER_KEYS:
            a = arc_path(opt, edges[k].get_center(), c, bow=0.4)
            self.play(FadeIn(edges[k], scale=0.5), MoveToTarget(users[k]),
                      MoveToTarget(lab_of[k]), run_time=0.4)
            self.send(a, RES_C, rt=0.85)
            self.play(Flash(edges[k], color=EDGE_C, flash_radius=0.5), run_time=0.35)
        self.beat(1.4)

        # near vs far, for one user
        self.play(FadeOut(cap), run_time=0.3)
        syd = users[FAR_KEY]
        se = edges[FAR_KEY]
        far = arc_path(syd.get_center(), opt, c, bow=0.6)
        far_dash = dashed(far, MUTED, sw=2.4, n=28, opacity=0.5)
        near = Line(syd.get_center(), se.get_center(), stroke_color=EDGE_C, stroke_width=4)
        far_tag = Text("✗  far origin · ≈150 ms", font_size=19, color=WARN)
        far_tag.next_to(far_dash, RIGHT, buff=0.1).shift(UP * 0.2)
        near_tag = Text("✓  nearby edge · ≈15 ms", font_size=19, color=EDGE_C, weight="BOLD")
        near_tag.next_to(se, DOWN, buff=0.35)
        self.play(Create(far_dash), FadeIn(far_tag), run_time=0.6)
        self.send(far, MUTED, rt=1.3)
        cap2 = self.say("The far origin is now the slow path…")
        self.play(FadeIn(cap2), run_time=0.4)
        self.beat(1.0)
        self.play(Create(near), FadeIn(near_tag), run_time=0.5)
        self.send(near, RES_C, rt=0.5)
        cap3 = self.say("…Cape Town is served from a server next door, not across continents.")
        self.play(ReplacementTransform(cap2, cap3), run_time=0.5)
        self.beat(1.7)

        # key terms
        self.play(FadeOut(Group(g, *users.values(), labels,
                                origin, olab, *edges.values(),
                                far_dash, near, far_tag, near_tag, cap3)), run_time=0.6)
        terms = VGroup(
            self._term("Origin", "where your content really lives", ORIGIN_C),
            self._term("Edge / PoP", "a cache near users (Point of Presence)", EDGE_C),
            self._term("Cache", "a stored copy, ready to serve instantly", USER_C),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.4).move_to(ORIGIN)
        self.play(LaggedStart(*[FadeIn(m, shift=RIGHT * 0.15) for m in terms],
                              lag_ratio=0.4, run_time=1.4))
        self.beat(1.8)
        self.settle()
        self.wipe()

    def _term(self, name, desc, color):
        n = Text(name, font_size=30, color=color, weight="BOLD")
        dsh = Text("—", font_size=30, color=MUTED).next_to(n, RIGHT, buff=0.22)
        d = Text(desc, font_size=27, color=INK).next_to(dsh, RIGHT, buff=0.22)
        return VGroup(n, dsh, d)

    # ====================================================================== #
    # Scene 3 — How it works: cache miss vs. cache hit
    # ====================================================================== #
    def scene_howitworks(self):
        header = self.section_header("How a request actually flows", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # Three columns: User — Edge — Origin
        yrow = 0.55
        u = person(USER_C, 1.0).move_to([-4.9, yrow, 0])
        ulab = Text("User", font_size=23, color=USER_C, weight="BOLD").next_to(u, DOWN, buff=0.25)
        e = server(w=1.0, h=0.8, color=EDGE_C, n_slots=3).move_to([0, yrow, 0])
        elab = Text("Edge server", font_size=23, color=EDGE_C, weight="BOLD").next_to(e, DOWN, buff=0.25)
        esub = Text("(near the user)", font_size=18, color=MUTED).next_to(elab, DOWN, buff=0.08)
        o = server(w=1.0, h=0.8, color=ORIGIN_C, n_slots=3).move_to([4.9, yrow, 0])
        olab = Text("Origin", font_size=23, color=ORIGIN_C, weight="BOLD").next_to(o, DOWN, buff=0.25)
        osub = Text("(your data centre)", font_size=18, color=MUTED).next_to(olab, DOWN, buff=0.08)
        chip = content_chip(EDGE_C, filled=False).move_to(e.get_center())  # empty at first

        self.play(FadeIn(u), FadeIn(ulab), FadeIn(e), FadeIn(elab), FadeIn(esub),
                  FadeIn(o), FadeIn(olab), FadeIn(osub), FadeIn(chip), run_time=0.9)

        def seg(a, b, buff=0.16):
            pa = np.array(a); pb = np.array(b)
            u_ = (pb - pa) / np.linalg.norm(pb - pa)
            return Line(pa + u_ * buff, pb - u_ * buff)

        ue = seg(u.get_right(), e.get_left())
        eo = seg(e.get_right(), o.get_left())
        for ln in (ue, eo):
            ln.set_stroke(FAINT, 2)
        self.play(Create(ue), Create(eo), run_time=0.5)

        # ---- MISS (first request) ----
        miss_pill = self.pill("First request  ·  cache MISS", MISS_C, fs=23)
        miss_pill.move_to([0, 2.35, 0])
        self.play(FadeIn(miss_pill, shift=DOWN * 0.1), run_time=0.5)
        cap = self.say("The edge has no copy yet, so it fetches from the origin…")
        self.play(FadeIn(cap), run_time=0.4)
        self.send(ue, REQ_C, rt=0.8)                       # user -> edge
        self.play(Indicate(chip, color=MISS_C, scale_factor=1.3), run_time=0.5)
        self.send(eo, REQ_C, rt=1.0)                       # edge -> origin (miss)
        self.send(Line(eo.get_end(), eo.get_start()), RES_C, rt=1.0)   # origin -> edge (content)
        # edge now caches it
        self.play(chip.animate.set_fill(EDGE_C, 0.9).set_stroke(EDGE_C, 2.2), run_time=0.4)
        cap2 = self.say("…stores a copy, then answers the user. (Slower — one-time cost.)")
        self.play(ReplacementTransform(cap, cap2), run_time=0.5)
        self.send(Line(ue.get_end(), ue.get_start()), RES_C, rt=0.8)   # edge -> user
        self.beat(1.7)

        # ---- HIT (everyone after) ----
        hit_pill = self.pill("Every request after  ·  cache HIT", HIT_C, fs=23)
        hit_pill.move_to([0, 2.35, 0])
        self.play(ReplacementTransform(miss_pill, hit_pill), run_time=0.5)
        cap3 = self.say("Now the copy is at the edge — served in milliseconds, "
                        "origin untouched.")
        self.play(ReplacementTransform(cap2, cap3), run_time=0.5)
        self.play(Indicate(o, color=FAINT, scale_factor=1.0), run_time=0.3)
        for _ in range(3 if not QUICK else 1):
            self.send(ue, REQ_C, rt=0.42)
            self.send(Line(ue.get_end(), ue.get_start()), RES_C, rt=0.42)
        self.play(Flash(e, color=HIT_C, flash_radius=0.8), run_time=0.5)
        self.beat(1.3)

        # ---- TTL + routing notes ----
        self.play(FadeOut(cap3), run_time=0.3)
        note1 = Text("Copies expire after a TTL, then the edge re-checks the origin.",
                     font_size=22, color=MUTED)
        note2 = Text("Anycast / DNS routes each user to their nearest edge — automatically.",
                     font_size=22, color=MUTED)
        notes = VGroup(note1, note2).arrange(DOWN, buff=0.18).move_to([0, -1.7, 0])
        self.play(FadeIn(note1, shift=UP * 0.08), run_time=0.5)
        self.beat(0.9)
        self.play(FadeIn(note2, shift=UP * 0.08), run_time=0.5)
        self.beat(1.4)

        self.play(FadeOut(VGroup(u, ulab, e, elab, esub, o, olab, osub, chip,
                                 ue, eo, hit_pill, notes)), run_time=0.6)
        k1 = Text("The first visitor pays the trip.", font_size=34, color=INK, weight="BOLD")
        k2 = Text("Everyone after flies.", font_size=34, color=GOLD, weight="BOLD")
        VGroup(k1, k2).arrange(DOWN, buff=0.3).move_to(ORIGIN)
        self.play(FadeIn(k1, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(k2, shift=UP * 0.1), run_time=0.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Use cases: what to cache, when to use, and the payoff
    # ====================================================================== #
    def scene_usecases(self):
        header = self.section_header("When should you reach for a CDN?", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # ---- left card: what to cache ----
        lt = Text("Great to cache at the edge", font_size=25, color=EDGE_C, weight="BOLD")
        litems = VGroup(*[self.check_line(h, "", EDGE_C, fs=24) for h in (
            "Images & media",
            "CSS, JS & fonts",
            "Video & large downloads",
            "Anything static — same for everyone",
        )]).arrange(DOWN, aligned_edge=LEFT, buff=0.24)
        litems.next_to(lt, DOWN, aligned_edge=LEFT, buff=0.3)
        lgroup = VGroup(lt, litems)
        lbox = self.card_box(lgroup, EDGE_C, pad=0.36)
        left = VGroup(lbox, lgroup).move_to([-3.55, 0.45, 0])

        # ---- right card: when ----
        rt = Text("Reach for a CDN when…", font_size=25, color=USER_C, weight="BOLD")
        ritems = VGroup(*[self.check_line(h, "", USER_C, fs=24) for h in (
            "Users are spread worldwide",
            "You serve lots of static media",
            "Traffic is spiky or viral",
            "You want to offload & shield the origin",
        )]).arrange(DOWN, aligned_edge=LEFT, buff=0.24)
        ritems.next_to(rt, DOWN, aligned_edge=LEFT, buff=0.3)
        rgroup = VGroup(rt, ritems)
        rbox = self.card_box(rgroup, USER_C, pad=0.36)
        right = VGroup(rbox, rgroup).move_to([3.55, 0.45, 0])

        self.play(FadeIn(left, shift=RIGHT * 0.15), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(m, shift=RIGHT * 0.1) for m in litems],
                              lag_ratio=0.3, run_time=1.0))
        self.beat(1.0)
        self.play(FadeIn(right, shift=LEFT * 0.15), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(m, shift=RIGHT * 0.1) for m in ritems],
                              lag_ratio=0.3, run_time=1.0))
        self.beat(1.2)

        dyn = Text("Dynamic or personalised data → still the origin (or edge compute).",
                   font_size=21, color=MUTED).move_to([0, -2.15, 0])
        self.play(FadeIn(dyn), run_time=0.5)
        self.beat(1.6)

        # ---- collapse to the payoff ----
        self.play(FadeOut(VGroup(left, right, dyn)), run_time=0.6)
        why = Text("Why teams add one", font_size=27, color=GOLD, weight="BOLD")
        why.move_to([0, 2.55, 0])
        benefits = VGroup(
            self.check_line("Lower latency", "— content sits next to users", GOOD),
            self.check_line("Less origin load", "— edges absorb the traffic", GOOD),
            self.check_line("Survives spikes & outages", "— it scales and stays up", GOOD),
            self.check_line("Cheaper egress bandwidth", "— fewer bytes from origin", GOOD),
            self.check_line("Security built in", "— DDoS absorption, WAF, TLS", GOOD),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.26).move_to([0, 0.15, 0])
        self.play(FadeIn(why, shift=DOWN * 0.1), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(m, shift=RIGHT * 0.12) for m in benefits],
                              lag_ratio=0.35, run_time=1.6))
        self.beat(1.6)

        providers = Text("In the wild:  Cloudflare · Akamai · CloudFront · Fastly · "
                         "Google Cloud CDN", font_size=20, color=MUTED)
        providers.move_to([0, -2.55, 0])
        if providers.width > 12.8:
            providers.scale_to_fit_width(12.8)
        self.play(FadeIn(providers), run_time=0.5)
        self.beat(1.6)

        self.play(FadeOut(VGroup(why, benefits, providers)), run_time=0.6)
        k = Text("A CDN = your content, cached worldwide,", font_size=32, color=INK, weight="BOLD")
        k2 = Text("one short hop from every user.", font_size=32, color=GOLD, weight="BOLD")
        VGroup(k, k2).arrange(DOWN, buff=0.28).move_to(ORIGIN)
        self.play(FadeIn(k, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(k2, shift=UP * 0.1), run_time=0.6)
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_problem()
        self.scene_idea()
        self.scene_howitworks()
        self.scene_usecases()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_CDNBase):
    def construct(self):
        self.play_intro()


class Problem(_CDNBase):
    def construct(self):
        self.scene_problem()


class Idea(_CDNBase):
    def construct(self):
        self.scene_idea()


class HowItWorks(_CDNBase):
    def construct(self):
        self.scene_howitworks()


class UseCases(_CDNBase):
    def construct(self):
        self.scene_usecases()


class Outro(_CDNBase):
    def construct(self):
        self.play_outro()


class CDN(_CDNBase):
    """The whole ~3-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    CDN().render()

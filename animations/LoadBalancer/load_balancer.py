"""Load Balancers — a short, house-style explainer.

A self-explanatory (no voice-over) film that answers, in six beats, what a load
balancer is, what it does under the hood, and why it is non-negotiable for any
production system that has to scale and stay up. Replicas are assumed known (see
the Kubernetes film): here we ask *who do clients talk to* once there are many.

    1. Why           -- one server overloads and is a single point of failure;
                        replicas fix capacity, but now there are many addresses.
    2. Front door    -- the load balancer: one stable public address in front of
                        a pool of identical replicas; it spreads requests over them.
    3. Choosing      -- how it picks a server: round-robin, least-connections,
                        weighted, and sticky sessions (session affinity).
    4. Health        -- health checks + failover: a sick server is pulled out of
                        rotation, traffic reroutes, and it rejoins when it heals.
    5. Under the hood-- L4 vs L7, path/host routing and TLS termination at the
                        edge, shown against a real nginx `upstream` config.
    6. Why it matters-- scale out live with zero downtime; the checklist of what a
                        load balancer buys you, and the one-line takeaway.

Bookended by the channel's intro card and the "Thanks for watching!" outro,
matching animations/Gravity/gravity.py, animations/Kubernetes/kubernetes_cd.py
and the rest of the series.

Everything uses ``Text`` (Pango), never ``Tex`` — so it renders with no LaTeX
toolchain. Nothing is a screenshot: the clients, the balancer, the servers, the
requests and the config panel are all Manim mobjects.

Scenes are exposed individually (``Why``, ``Frontdoor``, ``Choosing``,
``Health``, ``Layers``, ``Scale``, ``Intro``, ``Outro``) and as one film
(``LoadBalancer``).

Env knobs:
    LB_QUICK=1       collapse every reading hold (and end-holds) for a fast render
    LB_DELAY=1.5     override the reading-hold multiplier (seconds per "beat")
    LB_ANIM_SLOW=1.15 stretch every played animation's run_time
    LB_END_HOLD=1.8  hold at the end of each scene before the wipe
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

# --- crisp text ------------------------------------------------------------ #
# Manim's ``Text`` quantises glyph positions badly below ~20 pt, so small body
# text comes out with uneven spacing. Render at a large base and scale *down*.
_BaseText = Text
_TEXT_BASE = 60


def Text(text, font_size=DEFAULT_FONT_SIZE, **kw):  # noqa: F811
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


# ---- pacing knobs --------------------------------------------------------- #
QUICK = os.environ.get("LB_QUICK") == "1"
DELAY = float(os.environ.get("LB_DELAY", "0.28" if QUICK else "1.5"))
ANIM_SLOW = 1.0 if QUICK else float(os.environ.get("LB_ANIM_SLOW", "1.15"))
END_HOLD = 0.3 if QUICK else float(os.environ.get("LB_END_HOLD", "1.8"))

# ---- palette (shared house style, from the Kubernetes film) --------------- #
BG = "#0E1117"        # dark slate background
PANEL = "#151A23"     # panel / card fill
INK = "#F5F3EF"       # warm white text
MUTED = "#8A93A6"     # secondary text / axes
FAINT = "#2A3140"     # gridlines / guides / slots
GOLD = "#FFD166"      # requests / highlight / the takeaway
GOOD = "#3DD68C"      # healthy / ✓ green
BAD = "#FF5C5C"       # down / ✗ red
WARN = "#FFC24B"      # near-capacity amber
TEAL = "#2EC4B6"      # the load balancer (the Service colour)
NODE_C = "#5B8DEF"    # servers / replicas (blue)
CLIENT_C = "#C792EA"  # clients (purple)
ACCENT = "#A371F7"    # L7 / accents
ORANGE = "#FF9F45"    # weighted / secondary accent

# code panel (Menlo) colours
CODE_BG = "#0A0E15"
CODE_BAR = "#141C29"
COMMENT = "#5F6B7E"
KW = "#82AAFF"
STR = "#7FDBCA"
NUM = "#F78C6C"

# ---- geometry shared across scenes ---------------------------------------- #
LB_POS = np.array([-1.7, 0.0, 0.0])
POOL_X = 3.95


def lerp(a, b, t):
    return a + (b - a) * t


# ========================================================================== #
class _LBBase(Scene):
    def setup(self):
        self.camera.background_color = BG

    # ---- pacing ----------------------------------------------------------- #
    def play(self, *anims, **kw):
        # Stretch played animations by ANIM_SLOW, but never scale a bare Wait
        # (self.wait routes through play(Wait(...))).
        is_wait = len(anims) == 1 and isinstance(anims[0], Wait)
        if ANIM_SLOW != 1.0 and not is_wait:
            kw["run_time"] = kw.get("run_time", 1.0) * ANIM_SLOW
        super().play(*anims, **kw)

    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.0))

    def settle(self):
        self.wait(END_HOLD)

    def wipe(self, rt=0.6):
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=rt)
        self._focus_bars = None

    # ---- chrome ----------------------------------------------------------- #
    def section_header(self, label, color=TEAL):
        txt = Text(label, font_size=32, color=INK, weight="BOLD").to_corner(UL, buff=0.5)
        line = Line(txt.get_left(), txt.get_right()).next_to(txt, DOWN, buff=0.12)
        line.set_stroke(color=color, width=4)
        return VGroup(txt, line)

    def say(self, text, color=MUTED, fs=25, y=-3.5):
        """A single bottom caption, clamped to the frame width."""
        m = Text(text, font_size=fs, color=color)
        avail = 2 * config.frame_x_radius - 0.9
        if m.width > avail:
            m.scale_to_fit_width(avail)
        m.move_to([0, y, 0])
        return m

    def clamp_right(self, grp, pad=0.35):
        """Shrink a group in place if it runs past the right edge."""
        avail = config.frame_x_radius - pad - grp.get_left()[0]
        if grp.width > avail and avail > 0:
            grp.scale(avail / grp.width, about_point=grp.get_left())
        return grp

    # ====================================================================== #
    # Reusable glyphs
    # ====================================================================== #
    def pill(self, text, color=TEAL, fs=16, fill_c=None, txt_c=None, mono=True):
        kw = {"font": "Menlo"} if mono else {}
        t = Text(text, font_size=fs, color=txt_c or color, **kw)
        box = RoundedRectangle(
            width=t.width + 0.26, height=t.height + 0.16, corner_radius=0.09,
            stroke_color=color, stroke_width=1.6,
            fill_color=fill_c or BG, fill_opacity=1.0 if fill_c else 0.0,
        )
        t.move_to(box)
        g = VGroup(box, t)
        g.box, g.label = box, t
        return g

    def client(self, w=0.98, h=0.68, color=CLIENT_C):
        """A little browser card: title bar with traffic-light dots + content lines."""
        outer = RoundedRectangle(width=w, height=h, corner_radius=0.08,
                                 stroke_color=color, stroke_width=2,
                                 fill_color=PANEL, fill_opacity=1)
        bar = Rectangle(width=w - 0.05, height=0.15, stroke_width=0,
                        fill_color=FAINT, fill_opacity=1)
        bar.move_to(outer.get_top() + DOWN * 0.105)
        dots = VGroup(*[Dot(radius=0.028, color=c) for c in (BAD, WARN, GOOD)])
        dots.arrange(RIGHT, buff=0.05).move_to(bar.get_left() + RIGHT * 0.16)
        lines = VGroup(*[Line(ORIGIN, RIGHT * (w * 0.52), stroke_color=MUTED, stroke_width=2)
                         for _ in range(2)])
        lines.arrange(DOWN, buff=0.11, aligned_edge=LEFT).move_to(outer.get_center() + DOWN * 0.06)
        g = VGroup(outer, bar, dots, lines)
        g.outer = outer
        return g

    def server(self, label="app", color=NODE_C, w=1.7, h=0.98, healthy=True):
        """A server node: a titled box with slot bars and a health LED."""
        box = RoundedRectangle(width=w, height=h, corner_radius=0.1,
                               stroke_color=color, stroke_width=2.5,
                               fill_color=PANEL, fill_opacity=1)
        title = Text(label, font_size=17, color=INK).move_to(box.get_top() + DOWN * 0.21)
        slots = VGroup(*[Rectangle(width=w * 0.5, height=0.075, stroke_width=0,
                                   fill_color=FAINT, fill_opacity=1) for _ in range(2)])
        slots.arrange(DOWN, buff=0.09, aligned_edge=LEFT)
        slots.move_to(box.get_center() + np.array([-w * 0.12, -0.13, 0]))
        led = Dot(radius=0.055, color=GOOD if healthy else BAD)
        led.move_to(box.get_corner(UR) + np.array([-0.17, -0.17, 0]))
        g = VGroup(box, title, slots, led)
        g.box, g.title, g.slots, g.led = box, title, slots, led
        return g

    def load_balancer(self, w=1.95, h=2.5):
        """The balancer: a teal card with a fan-out icon and one VIP address."""
        box = RoundedRectangle(width=w, height=h, corner_radius=0.14,
                               stroke_color=TEAL, stroke_width=3,
                               fill_color=PANEL, fill_opacity=1)
        t = VGroup(Text("LOAD", font_size=22, color=TEAL, weight="BOLD"),
                   Text("BALANCER", font_size=22, color=TEAL, weight="BOLD"))
        t.arrange(DOWN, buff=0.05)
        # keep the title inside the box for whatever width was requested
        if t.width > w - 0.28:
            t.scale((w - 0.28) / t.width)
        t.move_to(box.get_top() + DOWN * 0.46)
        hub = Dot(radius=0.07, color=GOLD).move_to(box.get_center() + np.array([-0.52, -0.05, 0]))
        fan = VGroup(*[
            Arrow(hub.get_center(), box.get_center() + np.array([0.6, dy, 0]),
                  buff=0.08, color=TEAL, stroke_width=3, tip_length=0.13,
                  max_tip_length_to_length_ratio=0.4)
            for dy in (0.42, -0.05, -0.52)
        ])
        vip = self.pill("203.0.113.9:443", color=TEAL, fs=15, fill_c=CODE_BG)
        if vip.width > w - 0.2:  # address pill must not spill past the borders
            vip.scale((w - 0.2) / vip.width)
        vip.next_to(box.get_bottom(), UP, buff=0.16)
        g = VGroup(box, t, hub, fan, vip)
        g.box, g.title, g.vip = box, t, vip
        return g

    def connect(self, a_pt, b_pt, color=FAINT, sw=2.5, dashed=False):
        ln = Line(a_pt, b_pt, stroke_color=color, stroke_width=sw)
        if dashed:
            ln = DashedVMobject(ln, num_dashes=14)
        return ln

    def packet(self, pt, color=GOLD, r=0.085):
        glow = Dot(pt, radius=r * 2.5, color=color).set_opacity(0.20)
        core = Dot(pt, radius=r, color=color).set_stroke(INK, 0.6)
        return VGroup(glow, core)

    def make_cross(self, mob, color=BAD, sw=6):
        return Cross(mob, stroke_color=color, stroke_width=sw).scale(0.62)

    def padlock(self, color=GOOD, s=1.0):
        """A tiny drawn padlock (Pango can't render the lock emoji)."""
        body = RoundedRectangle(width=0.22 * s, height=0.18 * s, corner_radius=0.04 * s,
                                stroke_width=0, fill_color=color, fill_opacity=1)
        shackle = Arc(radius=0.08 * s, start_angle=0, angle=PI,
                      stroke_color=color, stroke_width=3)
        shackle.next_to(body, UP, buff=-0.03 * s)
        hole = Dot(radius=0.022 * s, color=BG).move_to(body)
        return VGroup(shackle, body, hole)

    # ---- request flow helpers -------------------------------------------- #
    def flow_in(self, src_pts, dst_pt, color=GOLD, rt=0.55):
        """A batch of packets travelling from several sources to one point."""
        pks = VGroup(*[self.packet(p, color) for p in src_pts])
        self.add(pks)
        self.play(*[pk.animate.move_to(dst_pt) for pk in pks],
                  run_time=rt, rate_func=rush_into)
        return pks

    def flow_out(self, src_pt, dst_pts, targets, color=GOLD, rt=0.6, flash=True):
        """One-to-many dispatch: a packet flies from the LB to each target."""
        pks = VGroup(*[self.packet(src_pt, color) for _ in dst_pts])
        self.add(pks)
        self.play(*[pk.animate.move_to(p) for pk, p in zip(pks, dst_pts)],
                  run_time=rt, rate_func=rush_from)
        if flash:
            self.play(*[Flash(t, color=color, flash_radius=0.5, line_length=0.12)
                        for t in targets], FadeOut(pks), run_time=0.4)
        else:
            self.play(FadeOut(pks), run_time=0.25)

    def route_one(self, start_pt, mid_pt, end_pt, color=GOLD, rt=0.45, target=None):
        """A single request: source → balancer → chosen server."""
        pk = self.packet(start_pt, color)
        self.add(pk)
        self.play(pk.animate.move_to(mid_pt), run_time=rt, rate_func=linear)
        self.play(pk.animate.move_to(end_pt), run_time=rt, rate_func=linear)
        if target is not None:
            self.play(Flash(target, color=color, flash_radius=0.5, line_length=0.12),
                      FadeOut(pk), run_time=0.35)
        else:
            self.play(FadeOut(pk), run_time=0.2)

    # ---- code panel (Menlo) ---------------------------------------------- #
    def code_panel(self, spec, fs=19, title="nginx.conf"):
        """A macOS-style code window. spec: list of (text, t2c) — '' is a blank line.

        Comments (starting with '#') are muted/italic; everything else is inked.
        """
        rendered = []
        for text, t2c in spec:
            if text == "":
                rendered.append(Text(" ", font_size=fs, font="Menlo"))
                continue
            if text.lstrip().startswith("#"):
                rendered.append(Text(text, font_size=fs, font="Menlo",
                                     color=COMMENT, slant=ITALIC))
            else:
                rendered.append(Text(text, font_size=fs, font="Menlo",
                                     color="#D6DEEB", t2c=t2c or {}))
        lines = VGroup(*rendered).arrange(DOWN, aligned_edge=LEFT, buff=0.16)

        pad = 0.34
        bg = RoundedRectangle(width=lines.width + 2 * pad, height=lines.height + 2 * pad + 0.4,
                              corner_radius=0.1, stroke_color=FAINT, stroke_width=1.5,
                              fill_color=CODE_BG, fill_opacity=1)
        bar = Rectangle(width=bg.width, height=0.4, stroke_width=0,
                        fill_color=CODE_BAR, fill_opacity=1)
        bar.move_to(bg).align_to(bg, UP)
        tl = VGroup(*[Dot(radius=0.045, color=c) for c in ("#FF5F57", "#FEBC2E", "#28C840")])
        tl.arrange(RIGHT, buff=0.09).move_to(bar.get_left() + RIGHT * 0.3)
        fname = Text(title, font_size=14, color=MUTED).next_to(tl, RIGHT, buff=0.25)
        lines.next_to(bar, DOWN, buff=0.18).align_to(bg, LEFT).shift(RIGHT * pad)
        panel = VGroup(bg, bar, tl, fname, lines)
        panel.bg, panel.lines = bg, lines
        return panel, lines

    def focus(self, lines, idxs, color=GOLD):
        """Dim all code lines, spotlight the given indices with a highlight bar.

        Removes the previous focus's bars so highlights never accumulate.
        """
        prev = getattr(self, "_focus_bars", None)
        bars = VGroup()
        for i, ln in enumerate(lines):
            if i in idxs:
                bar = RoundedRectangle(width=ln.width + 0.2, height=ln.height + 0.12,
                                       corner_radius=0.05, stroke_width=0,
                                       fill_color=color, fill_opacity=0.16)
                bar.move_to(ln)
                bars.add(bar)
        anims = [ln.animate.set_opacity(1.0 if i in idxs else 0.34)
                 for i, ln in enumerate(lines)]
        outs = [FadeOut(prev)] if prev is not None and len(prev) else []
        self.play(*outs, *[FadeIn(b) for b in bars], *anims, run_time=0.6)
        self._focus_bars = bars
        return bars

    # ---- house-style intro / outro cards --------------------------------- #
    def _bookend(self, title, subtitle):
        header = Text(title, font_size=52, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.42, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.42, 0],
        ).set_stroke(width=3, color=TEAL)
        writer = Text("Created by Ptolémé", font_size=27, color=NODE_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.52, 0])
        return header, line, writer, subtitle

    def play_intro(self):
        header, line, writer, subtitle = self._bookend(
            "Load Balancers",
            "One address · many servers · always on",
        )
        # a gold request rolls in along the underline — a wink at incoming traffic
        pk = self.packet([line.get_left()[0], line.get_center()[1] + 0.22, 0])
        self.play(Write(header), Create(line), run_time=1.5)
        self.play(pk.animate.move_to([line.get_right()[0], line.get_center()[1] + 0.22, 0]),
                  run_time=0.9, rate_func=rush_from)
        self.card_wait(0.4)
        sub = Text(subtitle, font_size=32, color=MUTED).move_to(header)
        self.play(Transform(header, sub), FadeOut(pk), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.card_wait(1.7)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.0)
        self.card_wait(0.2)

    def play_outro(self):
        self.card_wait(0.4)
        header = Text("Thanks for watching!", font_size=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.42, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.42, 0],
        ).set_stroke(width=3, color=TEAL)
        writer = Text("Created by Ptolémé", font_size=27, color=NODE_C)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.52, 0])
        self.play(Write(header), Create(line), run_time=1.4)
        self.card_wait(0.8)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=1.0)
        self.card_wait(1.9)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.2)
        self.card_wait(0.3)

    # ====================================================================== #
    # small builders for the shared topology
    # ====================================================================== #
    def build_pool(self, labels, color=NODE_C, w=1.7, h=0.98, gap=1.55, x=POOL_X):
        ys = [(len(labels) - 1) / 2 * gap - i * gap for i in range(len(labels))]
        pool = VGroup()
        for lab, y in zip(labels, ys):
            s = self.server(lab, color=color, w=w, h=h).move_to([x, y, 0])
            pool.add(s)
        return pool

    def lb_to_pool_links(self, lb, pool, color=FAINT):
        return VGroup(*[self.connect(lb.get_right(), s.get_left(), color=color)
                        for s in pool])

    # ====================================================================== #
    # Scene 1 — Why we need one
    # ====================================================================== #
    def scene_why(self):
        title = Text("Why do we need a load balancer?", font_size=42,
                     color=INK, weight="BOLD")
        self.play(Write(title), run_time=1.2)
        self.beat(0.8)
        header = self.section_header("Why we need one", TEAL)
        self.play(ReplacementTransform(title, header), run_time=0.7)

        # one server, taking all the traffic
        srv = self.server("app", NODE_C, w=2.0, h=1.2).move_to([1.4, 0.4, 0])
        clients = VGroup(*[self.client().scale(0.85) for _ in range(3)])
        clients.arrange(DOWN, buff=0.4).move_to([-4.7, 0.4, 0])
        links = VGroup(*[self.connect(c.get_right(), srv.get_left(), MUTED, 2) for c in clients])
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.15) for c in clients],
                              lag_ratio=0.2), run_time=0.9)
        self.play(FadeIn(srv), *[Create(l) for l in links], run_time=0.8)
        cap = self.say("One server behind everything — it can only take so much.")
        self.play(FadeIn(cap), run_time=0.4)
        self.beat(1.2)

        # a capacity meter that fills past the red line as traffic grows
        track = RoundedRectangle(width=1.7, height=0.2, corner_radius=0.1,
                                 stroke_color=MUTED, stroke_width=1.6, fill_opacity=0)
        track.next_to(srv, UP, buff=0.35)
        fill = RoundedRectangle(width=0.28, height=0.2, corner_radius=0.1, stroke_width=0,
                                fill_color=GOOD, fill_opacity=1)
        fill.move_to(track).align_to(track, LEFT)  # sit ON the track, not at y=0
        cap_lbl = Text("load", font_size=17, color=MUTED).next_to(track, LEFT, buff=0.18)
        self.play(FadeIn(track), FadeIn(fill), FadeIn(cap_lbl), run_time=0.4)

        def grow(frac, col, rt=0.7):
            self.play(fill.animate.stretch_to_fit_width(1.7 * frac)
                      .align_to(track, LEFT).set_fill(col), run_time=rt)

        grow(0.55, GOOD)
        self.play(*[Flash(c, color=GOLD, flash_radius=0.3, line_length=0.08) for c in clients],
                  run_time=0.4)
        grow(0.85, WARN)
        self.play(FadeOut(cap), run_time=0.2)
        cap = self.say("Traffic spikes → it slows, then falls over — and you're down.")
        self.play(FadeIn(cap), run_time=0.4)
        grow(1.0, BAD)
        # the server dies
        self.play(srv.box.animate.set_stroke(BAD), Wiggle(srv), run_time=0.7)
        srv.led.set_color(BAD)
        cross = self.make_cross(srv.box)
        # clients get 503s
        errs = VGroup(*[self.pill("503", color=BAD, fs=15, fill_c=CODE_BG).scale(0.9)
                        .next_to(c, RIGHT, buff=0.12) for c in clients])
        self.play(Create(cross), *[FadeIn(e, scale=0.6) for e in errs],
                  *[l.animate.set_stroke(BAD, 2) for l in links], run_time=0.7)
        self.beat(1.6)

        spof = Text("A single point of failure.", font_size=27, color=BAD, weight="BOLD")
        spof.next_to(track, UP, buff=0.55)
        self.play(FadeIn(spof, shift=UP * 0.1), run_time=0.5)
        self.beat(1.4)

        # replicas fix capacity — but now there are many addresses
        self.play(FadeOut(VGroup(cross, errs, spof, track, fill, cap_lbl, cap)),
                  *[l.animate.set_stroke(MUTED, 2) for l in links], run_time=0.5)
        srv.led.set_color(GOOD)
        self.play(srv.box.animate.set_stroke(NODE_C), run_time=0.3)
        recap = self.say("We already fixed capacity with replicas: many identical copies.")
        self.play(FadeIn(recap), run_time=0.4)
        # fan the one server into three replicas
        r1 = self.server("app 1", NODE_C).move_to([2.3, 2.0, 0])
        r2 = self.server("app 2", NODE_C).move_to([2.3, 0.4, 0])
        r3 = self.server("app 3", NODE_C).move_to([2.3, -1.2, 0])
        self.play(FadeOut(links), ReplacementTransform(srv, r2), run_time=0.6)
        self.play(FadeIn(r1, shift=UP * 0.2), FadeIn(r3, shift=DOWN * 0.2), run_time=0.6)
        self.beat(0.8)

        # the crisscross problem: every client wiring to every server
        self.play(FadeOut(recap), run_time=0.2)
        mess = VGroup()
        for c in clients:
            for s in (r1, r2, r3):
                mess.add(self.connect(c.get_right(), s.get_left(), MUTED, 1.6))
        self.play(LaggedStart(*[Create(m) for m in mess], lag_ratio=0.05), run_time=1.2)
        q = self.say("But now — which copy does each client call? And if one dies?",
                     color=WARN)
        self.play(FadeIn(q), run_time=0.4)
        self.play(mess.animate.set_stroke(WARN), run_time=0.5)
        self.beat(1.6)

        # clear the tangle, then land the takeaway centered on a clean frame
        self.play(FadeOut(VGroup(mess, q, clients, r1, r2, r3)), run_time=0.5)
        need = Text("We need one thing in front to decide.", font_size=34,
                    color=TEAL, weight="BOLD").move_to(ORIGIN)
        self.play(FadeIn(need, shift=UP * 0.1), run_time=0.7)
        self.beat(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — The front door
    # ====================================================================== #
    def scene_frontdoor(self):
        header = self.section_header("One front door", TEAL)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        clients = VGroup(*[self.client().scale(0.85) for _ in range(3)])
        clients.arrange(DOWN, buff=0.55).move_to([-5.5, 0, 0])
        lb = self.load_balancer().move_to(LB_POS)
        pool = self.build_pool(["app 1", "app 2", "app 3"])

        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.15) for c in clients],
                              lag_ratio=0.15), run_time=0.8)
        self.play(GrowFromCenter(lb), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(s, shift=LEFT * 0.15) for s in pool],
                              lag_ratio=0.15), run_time=0.8)

        c_links = VGroup(*[self.connect(c.get_right(), lb.get_left(), MUTED, 2) for c in clients])
        s_links = self.lb_to_pool_links(lb, pool, color=FAINT)
        self.play(*[Create(l) for l in c_links], run_time=0.6)
        self.play(*[Create(l) for l in s_links], run_time=0.6)

        cap = self.say("Clients only ever talk to the balancer's single address.")
        self.play(FadeIn(cap), Indicate(lb.vip, color=TEAL, scale_factor=1.15), run_time=0.8)
        self.beat(1.6)

        # two rounds of "batch in → fan out" across the pool
        self.play(FadeOut(cap), run_time=0.2)
        cap = self.say("It spreads incoming requests across the pool of replicas.")
        self.play(FadeIn(cap), run_time=0.4)
        src_pts = [c.get_right() + RIGHT * 0.1 for c in clients]
        dst_pts = [s.get_left() + LEFT * 0.05 for s in pool]
        for _ in range(2):
            pks = self.flow_in(src_pts, lb.get_left() + LEFT * 0.05)
            self.play(FadeOut(pks), run_time=0.15)
            self.flow_out(lb.get_right() + RIGHT * 0.05, dst_pts, pool)
        self.beat(1.2)

        # the takeaway line
        self.play(FadeOut(cap), run_time=0.2)
        take = VGroup(
            Text("One stable address in front,", font_size=27, color=INK),
            Text("a pool of identical replicas behind.", font_size=27, color=TEAL, weight="BOLD"),
        ).arrange(DOWN, buff=0.16).move_to([0, -3.05, 0])
        self.play(FadeIn(take, shift=UP * 0.1), run_time=0.7)
        self.beat(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — Choosing a server
    # ====================================================================== #
    def scene_choosing(self):
        header = self.section_header("Under the hood: choosing a server", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        # a compact LB + pool on the right, strategy list on the left
        lb = self.load_balancer().scale(0.82).move_to([-0.5, 0.3, 0])
        pool = self.build_pool(["app 1", "app 2", "app 3"], w=1.4, h=0.8, gap=1.25,
                               x=4.2).shift(UP * 0.3)
        s_links = self.lb_to_pool_links(lb, pool, FAINT)
        arrow_in = Arrow([-6.1, 0.3, 0], lb.get_left(), buff=0.1, color=GOLD,
                         stroke_width=4, tip_length=0.16)
        req_lbl = Text("requests", font_size=18, color=GOLD).next_to(arrow_in, UP, buff=0.1)
        self.play(GrowFromCenter(lb), FadeIn(pool), *[Create(l) for l in s_links],
                  GrowArrow(arrow_in), FadeIn(req_lbl), run_time=0.9)

        q = self.say("Which server gets the next request? Pick a strategy:")
        self.play(FadeIn(q), run_time=0.4)
        self.beat(1.0)

        src = lb.get_right() + RIGHT * 0.05
        dsts = [s.get_left() + LEFT * 0.04 for s in pool]

        def strat_title(txt, color):
            t = Text(txt, font_size=23, color=color, weight="BOLD").move_to([-3.7, -2.7, 0])
            return t

        # 1) Round robin — 1, 2, 3, 1 ...
        st = strat_title("1 · Round robin — take turns", GOLD)
        self.play(FadeOut(q), FadeIn(st), run_time=0.5)
        order = [0, 1, 2, 0]
        for k in order:
            self.route_one(src, src, dsts[k], color=GOLD, rt=0.28, target=pool[k])
        self.beat(1.2)

        # 2) Least connections — counts shown; the freest wins
        st2 = strat_title("2 · Least connections — send to the freest", NODE_C)
        self.play(ReplacementTransform(st, st2), run_time=0.5)
        counts = [3, 1, 2]
        badges = VGroup()
        for s, n in zip(pool, counts):
            b = self.pill(f"conns: {n}", color=NODE_C, fs=14, fill_c=CODE_BG).scale(0.92)
            b.next_to(s, RIGHT, buff=0.18)
            badges.add(b)
        self.clamp_right(VGroup(pool, badges))
        self.play(LaggedStart(*[FadeIn(b, shift=LEFT * 0.1) for b in badges],
                              lag_ratio=0.15), run_time=0.7)
        # the min (app 2) is chosen
        self.play(Indicate(badges[1], color=GOOD, scale_factor=1.2),
                  pool[1].box.animate.set_stroke(GOOD), run_time=0.7)
        self.route_one(src, src, dsts[1], color=GOOD, rt=0.3, target=pool[1])
        self.play(pool[1].box.animate.set_stroke(NODE_C), run_time=0.3)
        self.beat(1.0)
        self.play(FadeOut(badges), run_time=0.3)

        # 3) Weighted — a bigger server takes more
        st3 = strat_title("3 · Weighted — bigger servers, more traffic", ORANGE)
        self.play(ReplacementTransform(st2, st3), run_time=0.5)
        self.play(pool[0].animate.scale(1.28), pool[0].box.animate.set_stroke(ORANGE),
                  run_time=0.5)
        wlbl = Text("×2", font_size=20, color=ORANGE, weight="BOLD").next_to(pool[0], RIGHT, buff=0.18)
        self.play(FadeIn(wlbl), run_time=0.3)
        for k in [0, 0, 1, 2]:
            self.route_one(src, src, pool[k].get_left() + LEFT * 0.04,
                           color=ORANGE, rt=0.26, target=pool[k])
        self.beat(1.0)
        self.play(pool[0].animate.scale(1 / 1.28), pool[0].box.animate.set_stroke(NODE_C),
                  FadeOut(wlbl), run_time=0.4)

        # 4) Sticky sessions — same client → same server
        st4 = strat_title("4 · Sticky sessions — same user, same server", ACCENT)
        self.play(ReplacementTransform(st3, st4), run_time=0.5)
        user = self.client().scale(0.7).next_to(arrow_in, LEFT, buff=0.05).shift(UP * 0.02)
        user.outer.set_stroke(ACCENT)
        self.play(FadeIn(user), run_time=0.3)
        for _ in range(3):
            self.route_one(user.get_right() + RIGHT * 0.05, src, dsts[2],
                           color=ACCENT, rt=0.3, target=pool[2])
        pin = Text("session pinned", font_size=16, color=ACCENT).next_to(pool[2], DOWN, buff=0.18)
        self.play(FadeIn(pin), pool[2].box.animate.set_stroke(ACCENT), run_time=0.5)
        self.beat(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Health checks & failover
    # ====================================================================== #
    def scene_health(self):
        header = self.section_header("Health checks & failover", GOOD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        lb = self.load_balancer().move_to(LB_POS)
        pool = self.build_pool(["app 1", "app 2", "app 3"])
        s_links = self.lb_to_pool_links(lb, pool, FAINT)
        arrow_in = Arrow([-6.1, 0, 0], lb.get_left(), buff=0.1, color=GOLD,
                         stroke_width=4, tip_length=0.16)
        self.play(GrowFromCenter(lb), FadeIn(pool), *[Create(l) for l in s_links],
                  GrowArrow(arrow_in), run_time=0.9)

        cap = self.say("The balancer constantly asks each server: are you healthy?")
        self.play(FadeIn(cap), run_time=0.4)
        # a health probe to each server that comes back 200 OK
        for s in pool:
            probe = self.pill("GET /healthz", color=GOOD, fs=13, fill_c=CODE_BG).scale(0.85)
            probe.move_to(lb.get_right() + RIGHT * 0.3)
            self.add(probe)
            self.play(probe.animate.next_to(s, LEFT, buff=0.08), run_time=0.3, rate_func=linear)
            ok = self.pill("200 ✓", color=GOOD, fs=13, fill_c=CODE_BG).scale(0.85)
            ok.move_to(probe)
            self.play(ReplacementTransform(probe, ok), run_time=0.25)
            self.play(FadeOut(ok), run_time=0.2)
        self.beat(1.2)

        # app 2 goes dark
        self.play(FadeOut(cap), run_time=0.2)
        cap = self.say("One server stops answering — the health check fails.", color=WARN)
        self.play(FadeIn(cap), run_time=0.4)
        victim = pool[1]
        self.play(victim.box.animate.set_stroke(BAD).set_fill(CODE_BG),
                  victim.led.animate.set_color(BAD), Wiggle(victim), run_time=0.7)
        probe = self.pill("GET /healthz", color=WARN, fs=13, fill_c=CODE_BG).scale(0.85)
        probe.move_to(lb.get_right() + RIGHT * 0.3)
        self.add(probe)
        self.play(probe.animate.next_to(victim, LEFT, buff=0.08), run_time=0.3, rate_func=linear)
        timeout = self.pill("✗ timeout", color=BAD, fs=13, fill_c=CODE_BG).scale(0.85).move_to(probe)
        self.play(ReplacementTransform(probe, timeout), run_time=0.3)
        self.beat(0.8)

        # pull it out of rotation
        self.play(FadeOut(timeout), run_time=0.2)
        cap2 = self.say("So the balancer pulls it out of rotation.", color=WARN)
        self.play(FadeOut(cap), FadeIn(cap2), run_time=0.4)
        out_tag = self.pill("out of rotation", color=BAD, fs=13, fill_c=CODE_BG).scale(0.85)
        out_tag.next_to(victim, RIGHT, buff=0.2)
        self.clamp_right(VGroup(pool, out_tag))
        dead_link = s_links[1]
        self.play(dead_link.animate.set_stroke(BAD, 2),
                  FadeIn(out_tag, scale=0.7), run_time=0.5)
        dead_dash = DashedVMobject(Line(lb.get_right(), victim.get_left(),
                                        stroke_color=BAD, stroke_width=2), num_dashes=12)
        self.play(ReplacementTransform(dead_link, dead_dash), run_time=0.3)
        self.beat(1.0)

        # traffic reroutes only to the healthy two
        self.play(FadeOut(cap2), run_time=0.2)
        cap3 = self.say("Traffic reroutes to the healthy servers — users never notice.",
                        color=GOOD)
        self.play(FadeIn(cap3), run_time=0.4)
        healthy_dsts = [pool[0].get_left() + LEFT * 0.04, pool[2].get_left() + LEFT * 0.04]
        for _ in range(2):
            self.flow_out(lb.get_right() + RIGHT * 0.05, healthy_dsts, [pool[0], pool[2]])
        self.beat(1.2)

        # it self-heals and rejoins (callback to replicas)
        self.play(FadeOut(cap3), run_time=0.2)
        cap4 = self.say("Replicas self-heal; when it recovers, it rejoins automatically.")
        self.play(FadeIn(cap4), run_time=0.4)
        healthy_link = self.connect(lb.get_right(), victim.get_left(), FAINT)
        self.play(victim.box.animate.set_stroke(NODE_C).set_fill(PANEL, 1),
                  victim.led.animate.set_color(GOOD),
                  FadeOut(out_tag), ReplacementTransform(dead_dash, healthy_link),
                  run_time=0.7)
        self.play(Flash(victim, color=GOOD, flash_radius=0.6), run_time=0.5)
        self.route_one(lb.get_right() + RIGHT * 0.05, lb.get_right() + RIGHT * 0.05,
                       victim.get_left() + LEFT * 0.04, color=GOOD, rt=0.35, target=victim)
        self.beat(1.2)

        punch = Text("No single server is a single point of failure.", font_size=27,
                     color=GOOD, weight="BOLD").move_to([0, 2.5, 0])
        self.play(FadeOut(cap4), FadeIn(punch, shift=DOWN * 0.1), run_time=0.6)
        self.beat(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — L4, L7 & the edge
    # ====================================================================== #
    def scene_layers(self):
        header = self.section_header("Under the hood: L4, L7 & the edge", ACCENT)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        spec = [
            ("# one virtual IP, many real servers", None),
            ("upstream app {", {"upstream": KW}),
            ("    least_conn;", {"least_conn": STR}),
            ("    server app1:8080;", {"server": KW, "8080": NUM}),
            ("    server app2:8080;", {"server": KW, "8080": NUM}),
            ("    server app3:8080;", {"server": KW, "8080": NUM}),
            ("}", None),
            ("server {", {"server": KW}),
            ("    listen 443 ssl;", {"listen": KW, "443": NUM, "ssl": STR}),
            ("    location /api  { proxy_pass http://app; }", {"location": KW, "proxy_pass": KW}),
            ("}", None),
        ]
        panel, lines = self.code_panel(spec, fs=18)
        panel.scale(0.92).to_edge(LEFT, buff=0.5).shift(DOWN * 0.15)
        self.play(FadeIn(panel, shift=RIGHT * 0.2), run_time=0.8)
        self.beat(0.8)

        # L4 vs L7 explainer on the right
        rx = 3.5
        l4 = VGroup(
            Text("L4 · transport", font_size=24, color=NODE_C, weight="BOLD"),
            Text("forwards TCP/UDP by IP + port.", font_size=20, color=INK),
            Text("Doesn't read your data — blazing fast.", font_size=20, color=MUTED),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        l7 = VGroup(
            Text("L7 · application", font_size=24, color=ACCENT, weight="BOLD"),
            Text("reads HTTP — routes by path or host,", font_size=20, color=INK),
            Text("does retries, rate-limits, sticky cookies.", font_size=20, color=MUTED),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.14)
        VGroup(l4, l7).arrange(DOWN, aligned_edge=LEFT, buff=0.5).move_to([rx, 1.4, 0])
        for grp in (l4, l7):
            self.clamp_right(grp)
        self.play(FadeIn(l4, shift=UP * 0.1), run_time=0.6)
        self.focus(lines, [3, 4, 5])
        self.beat(1.4)
        self.play(FadeIn(l7, shift=UP * 0.1), run_time=0.6)
        self.focus(lines, [9])
        self.beat(1.4)

        # TLS termination: an anchored client → edge → server strip, encrypted
        # up to the balancer and plaintext behind it.
        self.play(FadeOut(VGroup(l4, l7)), run_time=0.3)
        self.focus(lines, [8])
        cap = self.say("TLS terminates at the edge: HTTPS in, plaintext to the pool.")
        self.play(FadeIn(cap), run_time=0.4)
        cx, ex, sx, yv = 1.9, 3.85, 5.7, 0.25
        cl = self.client().scale(0.6).move_to([cx, yv, 0])
        cl.outer.set_stroke(CLIENT_C)
        edge = VGroup(
            RoundedRectangle(width=0.95, height=1.0, corner_radius=0.1, stroke_color=TEAL,
                             stroke_width=2.5, fill_color=PANEL, fill_opacity=1),
            Text("edge", font_size=15, color=TEAL),
        )
        edge[1].move_to(edge[0])
        edge.move_to([ex, yv, 0])
        srv = self.server("app", NODE_C, w=1.0, h=0.82).move_to([sx, yv, 0])
        a1 = Arrow(cl.get_right(), edge.get_left(), buff=0.1, color=GOOD,
                   stroke_width=4, tip_length=0.14)
        a2 = Arrow(edge[0].get_right(), srv.get_left(), buff=0.1, color=MUTED,
                   stroke_width=4, tip_length=0.14)
        lock = self.padlock(GOOD, 0.95).next_to(a1, UP, buff=0.05)
        https = Text("HTTPS", font_size=15, color=GOOD).next_to(lock, UP, buff=0.04)
        http = Text("HTTP", font_size=15, color=MUTED).next_to(a2, UP, buff=0.12)
        self.play(FadeIn(cl), FadeIn(edge), FadeIn(srv), run_time=0.5)
        self.play(GrowArrow(a1), FadeIn(lock), FadeIn(https), run_time=0.5)
        self.play(GrowArrow(a2), FadeIn(http), run_time=0.5)
        self.beat(1.6)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 6 — Why it's paramount for scalability
    # ====================================================================== #
    def scene_scale(self):
        header = self.section_header("Why it's paramount", GOLD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.5)

        # five vertical slots, centred; start with the middle three filled so the
        # two new replicas can slot in above and below without running off-screen.
        ys5 = [2.2, 1.1, 0.0, -1.1, -2.2]
        lb = self.load_balancer().scale(0.82).move_to([-2.2, 0.0, 0])
        pool = VGroup(*[self.server(lab, NODE_C, w=1.5, h=0.72).move_to([3.3, ys5[i + 1], 0])
                        for i, lab in enumerate(["app 1", "app 2", "app 3"])])
        s_links = self.lb_to_pool_links(lb, pool, FAINT)
        arrow_in = Arrow([-6.3, 0.0, 0], lb.get_left(), buff=0.1, color=GOLD,
                         stroke_width=5, tip_length=0.18)
        self.play(GrowFromCenter(lb), FadeIn(pool), *[Create(l) for l in s_links],
                  GrowArrow(arrow_in), run_time=0.9)

        cap = self.say("Traffic doubles. The pool is running hot.")
        self.play(FadeIn(cap), run_time=0.4)
        # heavy incoming traffic
        heavy_src = [np.array([-5.4, dy, 0]) for dy in (0.3, 0, -0.3)]
        dsts = [s.get_left() + LEFT * 0.04 for s in pool]
        pks = self.flow_in(heavy_src, lb.get_left() + LEFT * 0.05)
        self.play(FadeOut(pks), run_time=0.15)
        self.flow_out(lb.get_right() + RIGHT * 0.05, dsts, pool)
        self.play(*[s.box.animate.set_stroke(WARN) for s in pool], run_time=0.4)
        self.beat(1.0)

        # scale out — add two replicas; the LB uses them at once
        self.play(FadeOut(cap), run_time=0.2)
        cap = self.say("Add replicas to the pool — the balancer uses them instantly.",
                       color=GOOD)
        self.play(FadeIn(cap), run_time=0.4)
        new4 = self.server("app 4", NODE_C, w=1.5, h=0.72).move_to([3.3, ys5[0], 0])
        new5 = self.server("app 5", NODE_C, w=1.5, h=0.72).move_to([3.3, ys5[4], 0])
        link4 = self.connect(lb.get_right(), new4.get_left(), FAINT)
        link5 = self.connect(lb.get_right(), new5.get_left(), FAINT)
        self.play(GrowFromCenter(new4), GrowFromCenter(new5),
                  Create(link4), Create(link5), run_time=0.7)
        full_pool = VGroup(*pool, new4, new5)
        self.play(*[s.box.animate.set_stroke(GOOD) for s in full_pool], run_time=0.5)
        all_dsts = [s.get_left() + LEFT * 0.04 for s in full_pool]
        self.flow_out(lb.get_right() + RIGHT * 0.05, all_dsts, full_pool, color=GOOD)
        self.play(*[s.box.animate.set_stroke(NODE_C) for s in full_pool], run_time=0.4)
        hscale = Text("Horizontal scaling: add machines, not bigger ones.",
                      font_size=22, color=GOLD).move_to([0, -3.5, 0])
        self.clamp_right(hscale)
        self.play(FadeOut(cap), FadeIn(hscale), run_time=0.5)
        self.beat(1.6)

        # collapse the diagram and land the checklist
        diagram = VGroup(lb, full_pool, s_links, link4, link5, arrow_in, hscale)
        self.play(FadeOut(diagram), run_time=0.6)
        title = Text("What a load balancer buys you", font_size=30, color=INK,
                     weight="BOLD").to_edge(UP, buff=1.2)
        self.play(FadeIn(title, shift=DOWN * 0.1), run_time=0.5)
        items = [
            "One stable entry point — clients never track servers",
            "Even load, no hotspots",
            "Health checks + failover → high availability",
            "Add or remove capacity live → zero-downtime scaling & deploys",
            "TLS, routing & rate-limiting at the edge",
        ]
        rows = VGroup()
        for s in items:
            c = Text("✓", font_size=25, color=GOOD, weight="BOLD")
            t = Text(s, font_size=23, color=INK).next_to(c, RIGHT, buff=0.2)
            rows.add(VGroup(c, t))
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.28).next_to(title, DOWN, buff=0.5)
        for row in rows:
            self.clamp_right(row)
            self.play(FadeIn(row, shift=RIGHT * 0.12), run_time=0.4)
            self.beat(0.5)
        self.beat(1.0)

        # the one-line takeaway
        self.play(FadeOut(VGroup(title, rows)), run_time=0.5)
        punch = VGroup(
            Text("A load balancer turns many servers", font_size=30, color=INK),
            Text("into one scalable, always-on service.", font_size=30, color=TEAL, weight="BOLD"),
        ).arrange(DOWN, buff=0.2).move_to(ORIGIN)
        self.play(Write(punch), run_time=1.4)
        self.play(Circumscribe(punch, color=TEAL, run_time=1.4))
        self.beat(1.8)
        self.settle()
        self.wipe()

    # ---- full film -------------------------------------------------------- #
    def play_all(self):
        self.play_intro()
        self.scene_why()
        self.scene_frontdoor()
        self.scene_choosing()
        self.scene_health()
        self.scene_layers()
        self.scene_scale()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_LBBase):
    def construct(self):
        self.play_intro()


class Why(_LBBase):
    def construct(self):
        self.scene_why()


class Frontdoor(_LBBase):
    def construct(self):
        self.scene_frontdoor()


class Choosing(_LBBase):
    def construct(self):
        self.scene_choosing()


class Health(_LBBase):
    def construct(self):
        self.scene_health()


class Layers(_LBBase):
    def construct(self):
        self.scene_layers()


class Scale(_LBBase):
    def construct(self):
        self.scene_scale()


class Outro(_LBBase):
    def construct(self):
        self.play_outro()


class LoadBalancer(_LBBase):
    """The whole ~3-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    LoadBalancer().render()

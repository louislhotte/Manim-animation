"""Kubernetes & Continuous Delivery — a ~3.5-minute explainer, house-style.

From a single Dockerfile to a self-healing cluster that ships itself. The film
builds the mental model one layer at a time, then puts it to work in a real CD
pipeline:

    1. Why Kubernetes?  -- one app on one server can't scale and won't heal
    2. Containers       -- a Dockerfile → layers → an image → a running container
    3. The cluster      -- container ⊂ Pod ⊂ Node ⊂ Cluster (+ the Control Plane)
    4. Replicas         -- a Deployment keeps N copies alive; self-healing + scaling
    5. The CD pipeline  -- git push → GitHub Actions → registry → rolling update
    6. A strong CD      -- the checklist: what "good" actually needs

Every term the user asked about is defined on screen as its glyph appears:
container, Pod, Node, Cluster, replicas — plus the Control Plane and a Service.

Everything uses ``Text`` (Pango), never ``Tex`` — renders with no LaTeX
toolchain. Code (the Dockerfile and the GitHub Actions workflow) is set in Menlo
and syntax-coloured, and highlighted line-by-line as it's explained. Nothing is a
screenshot: the whale, the pods, the nodes and the pipeline are all Manim
mobjects.

Scenes are exposed individually (``Why``, ``Containers``, ``Cluster``,
``Replicas``, ``Pipeline``, ``Checklist``, ``Intro``, ``Outro``) and as one film
(``KubernetesCD``).

Env knobs:
    K8S_QUICK=1     collapse every reading hold (and end-holds) for a fast render
    K8S_DELAY=1.2   override the reading-hold multiplier (seconds per "beat")
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


QUICK = os.environ.get("K8S_QUICK") == "1"
# Reading rhythm: every hold is self.beat(t) == wait(t * DELAY). This is a
# teaching piece, so DELAY is generous — captions linger long enough to read.
# QUICK collapses every hold for a fast sanity render.
DELAY = float(os.environ.get("K8S_DELAY", "0.28" if QUICK else "2.1"))
# Beat held on the finished scene before it wipes to the next one.
END_HOLD = 0.2 if QUICK else 2.5
# Slow every *played* animation to ~83% speed so motion never feels rushed; the
# reading holds above are governed by DELAY, not by this. QUICK keeps full speed.
ANIM_SLOW = 1.0 if QUICK else 1.2

# ---- palette -------------------------------------------------------------- #
BG = "#0E1117"        # dark slate background
PANEL = "#151A23"     # panel fill
INK = "#F5F3EF"       # warm white text
MUTED = "#8A93A6"     # secondary text / arrows
FAINT = "#2A3140"     # gridlines / tracks
ACCENT = "#FFD166"    # highlight (gold)
GOOD = "#3DD68C"      # healthy / pass (green)
BAD = "#FF5C5C"       # failing / error (red)
WARN = "#FFC24B"      # warning (amber)

K8S = "#326CE5"       # Kubernetes blue (brand)
DOCKER = "#2496ED"    # Docker blue
POD_C = "#5B8DEF"     # pods (blue)
NODE_C = "#2EC4B6"    # nodes (teal)
CTRL_C = "#C792EA"    # control plane (purple)
SVC_C = "#FF9F45"     # service (orange)
GH = "#A371F7"        # GitHub Actions (purple)

# ---- code (Night-Owl-ish) palette ----------------------------------------- #
MONO = "Menlo"
CODE_FS = 20
PLAIN = "#D6DEEB"     # default code text
COMMENT = "#5F6B7E"   # comments (grey-blue)
KW = "#C792EA"        # keywords / instructions (purple)
FN = "#82AAFF"        # keys / fields (blue)
VAL = "#F78C6C"       # literals (orange)
STR = "#7FDBCA"       # strings / paths (teal)

# distinctive tokens → colour; pruned per-line so ranges never collide (see below)
DOCKER_T2C = {
    "FROM": KW, "WORKDIR": KW, "COPY": KW, "RUN": KW, "EXPOSE": KW, "CMD": KW,
    "python:3.12-slim": VAL, "requirements.txt": STR, "app.py": STR,
    "pip": FN, "8080": VAL,
}
YAML_T2C = {
    "name": FN, "on": FN, "push": FN, "branches": FN, "jobs": FN,
    "runs-on": FN, "steps": FN, "uses": FN, "run": FN,
    "actions/checkout@v4": STR, "ubuntu-latest": VAL, "[main]": VAL,
    "docker": DOCKER, "kubectl": K8S, "$IMG": ACCENT,
}


def _safe_t2c(s, table):
    """Per-line text→colour map, pruned so no key overlaps another.

    Manim's ``t2c`` raises on overlapping colour ranges — even for the same
    colour (e.g. ``run`` sitting inside ``runs-on``). Keep only keys present in
    this line, then drop any key that is a substring of another present key.
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
    return VGroup(box, label)


def arr(a, b, color=MUTED, sw=4, buff=0.14, tip=0.22):
    return Arrow(a, b, buff=buff, stroke_width=sw, color=color,
                 max_tip_length_to_length_ratio=0.35, tip_length=tip)


def make_tick(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners(
        [np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]), np.array([0.24, 0.22, 0])])
    return v.set_stroke(color=color, width=sw).scale(scale)


def make_cross(color=BAD, sw=7, scale=1.0):
    a = Line([-0.16, -0.16, 0], [0.16, 0.16, 0])
    b = Line([-0.16, 0.16, 0], [0.16, -0.16, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


def container_box(w=0.92, h=0.66, color=DOCKER, fill=0.16, label=None, ridges=4, sw=3):
    """A little shipping container: a tinted box with vertical ridges."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.06,
                            stroke_color=color, stroke_width=sw,
                            fill_color=color, fill_opacity=fill)
    grp = VGroup(body)
    for x in np.linspace(-w * 0.30, w * 0.30, ridges):
        grp.add(Line([x, -h * 0.28, 0], [x, h * 0.28, 0],
                     stroke_color=color, stroke_width=2).set_opacity(0.7)
                .move_to([body.get_center()[0] + x, body.get_center()[1], 0]))
    if label:
        grp.add(txt(label, fs=15, color=INK).move_to(body))
    grp.body = body
    return grp


def pod_hex(r=0.55, color=POD_C, n_containers=1, ccolor=DOCKER):
    """A Pod drawn as a flat-top hexagon holding one (or more) container(s)."""
    hexo = RegularPolygon(n=6, start_angle=0, radius=r,
                          stroke_color=color, stroke_width=3,
                          fill_color=color, fill_opacity=0.10)
    grp = VGroup(hexo)
    cs = VGroup(*[container_box(w=r * 1.0, h=r * 0.62, color=ccolor)
                  for _ in range(n_containers)])
    cs.arrange(DOWN, buff=0.06).scale_to_fit_width(min(r * 1.1, cs.width)).move_to(hexo)
    grp.add(cs)
    grp.hexo = hexo
    return grp


def node_box(w=2.7, h=2.2, color=NODE_C, title="Node"):
    """A worker machine: a titled box (with a tiny CPU chip) that holds pods."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.14,
                            stroke_color=color, stroke_width=3,
                            fill_color=color, fill_opacity=0.05)
    bar = RoundedRectangle(width=w, height=0.5, corner_radius=0.14, stroke_width=0,
                           fill_color=color, fill_opacity=0.16)
    bar.align_to(body, UP)
    cpu = Square(side_length=0.2, stroke_color=color, stroke_width=2,
                 fill_color=color, fill_opacity=0.35)
    cpu.move_to([body.get_left()[0] + 0.34, bar.get_center()[1], 0])
    ttl = txt(title, fs=17, color=INK, weight="BOLD").next_to(cpu, RIGHT, buff=0.15)
    grp = VGroup(body, bar, cpu, ttl)
    grp.body = body
    grp.bar = bar
    return grp


def control_plane(w=6.8):
    """The brain of the cluster: API server / Scheduler / Controllers / etcd.

    A wide, short bar (title over a single row of chips) sized so nothing
    overflows — chips are scaled together only if the row is wider than the box.
    """
    ttl = txt("Control Plane", fs=18, color=CTRL_C, weight="BOLD")
    chips = VGroup(*[chip(t, CTRL_C, fs=14, h=0.52, fill=0.16)
                     for t in ["API server", "Scheduler", "Controllers", "etcd"]])
    chips.arrange(RIGHT, buff=0.2)
    if chips.width > w - 0.6:
        chips.scale_to_fit_width(w - 0.6)
    inner = VGroup(ttl, chips).arrange(DOWN, buff=0.18)
    body = RoundedRectangle(width=w, height=inner.height + 0.5,
                            corner_radius=0.16, stroke_color=CTRL_C, stroke_width=3,
                            fill_color=CTRL_C, fill_opacity=0.08)
    inner.move_to(body)
    grp = VGroup(body, inner)
    grp.body = body
    return grp


def whale(scale=1.0, color=DOCKER):
    """A small, friendly Docker-style whale carrying a stack of containers."""
    body = VMobject(stroke_width=0, fill_color=color, fill_opacity=1.0)
    body.set_points_smoothly([
        np.array([-1.35, -0.10, 0]), np.array([-0.9, 0.28, 0]),
        np.array([0.0, 0.40, 0]), np.array([1.15, 0.30, 0]),
        np.array([1.5, 0.05, 0]), np.array([1.15, -0.32, 0]),
        np.array([-0.7, -0.40, 0]), np.array([-1.35, -0.10, 0]),
    ])
    tail = Polygon(np.array([-1.28, -0.05, 0]), np.array([-1.85, 0.28, 0]),
                   np.array([-1.72, -0.22, 0]),
                   stroke_width=0, fill_color=color, fill_opacity=1.0)
    eye = Dot(np.array([1.05, 0.08, 0]), radius=0.05, color=INK)
    spout = VGroup(*[Line([0.55 + 0.14 * i, 0.42, 0], [0.5 + 0.24 * i, 0.78, 0],
                          stroke_color="#BFD9F2", stroke_width=3) for i in range(3)])
    deck = VGroup(*[container_box(w=0.34, h=0.26, color=c, ridges=3, sw=2, fill=0.9)
                    for c in ("#E4572E", "#F4A259", "#4C86A8")])
    deck.arrange(RIGHT, buff=0.07)
    deck.next_to(body.get_top(), UP, buff=-0.05).shift(LEFT * 0.1)
    grp = VGroup(tail, body, eye, spout, deck)
    return grp.scale(scale)


def helm_wheel(r=1.0, color=K8S, spokes=7):
    """A ship's-helm / Kubernetes motif: a spoked wheel with outer handles."""
    ring = Circle(radius=r, color=color, stroke_width=6)
    inner = Circle(radius=r * 0.62, color=color, stroke_width=3).set_opacity(0.6)
    hub = Circle(radius=r * 0.15, color=color, stroke_width=5,
                 fill_color=BG, fill_opacity=1)
    grp = VGroup(ring, inner, hub)
    for i in range(spokes):
        a = i * TAU / spokes + PI / 2
        d = np.array([np.cos(a), np.sin(a), 0])
        grp.add(Line(d * r * 0.15, d * r, stroke_color=color, stroke_width=5))
        grp.add(Line(d * r, d * r * 1.20, stroke_color=color, stroke_width=6))
        grp.add(Dot(d * r * 1.20, radius=r * 0.055, color=color))
    return grp


# ========================================================================== #
class _K8sBase(Scene):
    def setup(self):
        self.camera.background_color = BG
        self._cap = None
        self.hlrect = None

    # Slow every animation uniformly by stretching its run time (see ANIM_SLOW).
    # Works whether the run time is passed to .play() or carried on the animation
    # itself (e.g. Circumscribe(..., run_time=…)). self.wait() routes through
    # self.play(Wait(...)), so we must NOT scale those — holds are set by DELAY.
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
        ).set_stroke(width=3, color=K8S)
        writer = txt("Created by Ptolémé", fs=28, color=K8S)
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
        wheel = helm_wheel(r=1.05, color=K8S).to_edge(UP, buff=0.95)
        self.play(Create(wheel, lag_ratio=0.05), run_time=1.5)
        self.play(Rotate(wheel, angle=TAU / 7, about_point=wheel.get_center()),
                  run_time=1.4, rate_func=smooth)
        grp = self._bookend_title(
            "Kubernetes & Continuous Delivery",
            "from a Dockerfile to a self-healing cluster")
        self.card_wait(1.7)
        self.play(FadeOut(grp), FadeOut(wheel), run_time=0.9)
        self.card_wait(0.2)

    def play_outro(self):
        self.card_wait(0.3)
        header = txt("Thanks for watching!", fs=48, color=INK, weight="BOLD")
        line = Line(
            [header.get_left()[0] - 1, header.get_bottom()[1] - 0.45, 0],
            [header.get_right()[0] + 1, header.get_bottom()[1] - 0.45, 0],
        ).set_stroke(width=3, color=K8S)
        writer = txt("Created by Ptolémé", fs=28, color=K8S)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.2)
        self.card_wait(0.6)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.card_wait(1.6)
        self.play(FadeOut(VGroup(header, line, writer)), run_time=1.0)
        self.card_wait(0.3)

    # ---- code panel (adapted from the house code-panel helper) ------------ #
    def code_panel(self, spec, table, title="Dockerfile", fs=CODE_FS,
                   indent_unit=0.5, line_buff=0.17, target_h=5.6, target_w=6.6):
        """spec: list of (indent, text); "" is a blank line. Returns (panel, lines)."""
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
        # centre the bar on the panel first — the code VGroup is indent-shifted, so
        # bg is re-centred on it; align_to(UP) alone would leave the bar off in x.
        bar.move_to(bg).align_to(bg, UP)
        dots = VGroup(*[Dot(radius=0.045, color=c)
                        for c in ("#FF5F57", "#FEBC2E", "#28C840")]).arrange(RIGHT, buff=0.11)
        dots.move_to([bg.get_left()[0] + 0.42, bar.get_center()[1], 0])
        # filename sits left, just after the traffic-light dots (an editor tab)
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
    # Scene 1 — Why Kubernetes?
    # ====================================================================== #
    def scene_why(self):
        head = self.section_header("01", "Why Kubernetes?", ACCENT)

        # one app on one server -------------------------------------------- #
        server = node_box(w=3.0, h=2.4, color=NODE_C, title="server")
        app = chip("app  v1", DOCKER, fs=20, w=1.9, h=0.7, fill=0.2, weight="BOLD")
        app.move_to(server.body).shift(DOWN * 0.1)
        machine = VGroup(server, app).move_to(LEFT * 3.4 + UP * 0.3)
        self.play(FadeIn(server, shift=UP * 0.2), run_time=0.6)
        self.play(GrowFromCenter(app), run_time=0.5)
        self.say("One app, running on one server.", color=INK)
        self.beat(1.4)

        # traffic floods in ------------------------------------------------ #
        reqs = VGroup(*[Dot(radius=0.07, color=WARN) for _ in range(9)])
        reqs.arrange_in_grid(rows=3, cols=3, buff=0.16).next_to(machine, LEFT, buff=0.9)
        self.play(LaggedStart(*[FadeIn(d, shift=RIGHT * 0.2) for d in reqs],
                              lag_ratio=0.08), run_time=0.9)
        self.say("Traffic spikes…", color=WARN)
        self.play(reqs.animate.move_to(machine.get_center()).scale(0.5).set_opacity(0.0),
                  run_time=1.0)

        # …it can't cope: overload → crack → down -------------------------- #
        crack = VMobject(stroke_color=BAD, stroke_width=5)
        crack.set_points_as_corners([
            server.body.get_top() + DOWN * 0.1,
            server.body.get_center() + np.array([-0.25, 0.35, 0]),
            server.body.get_center() + np.array([0.28, -0.15, 0]),
            server.body.get_center() + np.array([-0.15, -0.55, 0]),
            server.body.get_bottom() + UP * 0.1,
        ])
        self.play(server.body.animate.set_stroke(BAD).set_fill(BAD, 0.10),
                  app.animate.set_color(BAD), run_time=0.5)
        self.play(Wiggle(machine, scale_value=1.06, rotation_angle=0.02 * TAU), run_time=0.7)
        self.play(Create(crack), run_time=0.5)
        down = txt("✕  DOWN", fs=26, color=BAD, weight="BOLD").next_to(machine, DOWN, buff=0.5)
        self.play(FadeIn(down, scale=1.2), run_time=0.4)
        self.say("…one machine falls over — and you're down.", color=BAD)
        self.beat(1.6)

        # the wish list ---------------------------------------------------- #
        wish = VGroup(
            txt("We want many identical copies…", fs=23, color=INK),
            txt("…spread across many machines…", fs=23, color=INK),
            txt("…that heal and update themselves,", fs=23, color=GOOD, weight="BOLD"),
            txt("with zero downtime.", fs=23, color=GOOD, weight="BOLD"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        wish.next_to(machine, RIGHT, buff=0.7)
        # never let it run off the right edge
        avail = (config.frame_x_radius - 0.35) - wish.get_left()[0]
        if wish.width > avail:
            wish.scale(avail / wish.width, about_point=wish.get_left())
        self.play(LaggedStart(*[FadeIn(w, shift=RIGHT * 0.2) for w in wish],
                              lag_ratio=0.4), run_time=1.9)
        self.beat(2.0)

        # roadmap ---------------------------------------------------------- #
        self.play(FadeOut(VGroup(machine, crack, down, wish)), run_time=0.6)
        road = txt("The road there:", fs=24, color=MUTED).move_to(UP * 1.4)
        stops = VGroup(
            chip("Containers", DOCKER, fs=20),
            chip("Pods", POD_C, fs=20),
            chip("Nodes", NODE_C, fs=20),
            chip("Cluster", K8S, fs=20),
            chip("Replicas", GOOD, fs=20),
            chip("Continuous Delivery", GH, fs=20),
        )
        stops.arrange_in_grid(rows=2, cols=3, buff=(0.4, 0.5)).next_to(road, DOWN, buff=0.5)
        self.play(FadeIn(road), run_time=0.4)
        self.play(LaggedStart(*[GrowFromCenter(s) for s in stops], lag_ratio=0.18),
                  run_time=1.8)
        self.say("Kubernetes gives us all of this.", color=K8S)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 2 — Containers & the Dockerfile
    # ====================================================================== #
    def scene_containers(self):
        self.section_header("02", "Containers", DOCKER)

        spec = [
            (0, "# a recipe for one immutable image"),
            (0, "FROM python:3.12-slim"),
            (0, "WORKDIR /app"),
            (0, ""),
            (0, "COPY requirements.txt ."),
            (0, "RUN pip install -r requirements.txt"),
            (0, ""),
            (0, "COPY . ."),
            (0, "EXPOSE 8080"),
            (0, 'CMD ["python", "app.py"]'),
        ]
        panel, lines = self.code_panel(spec, DOCKER_T2C, title="Dockerfile",
                                       target_h=5.4, target_w=6.2)
        panel.to_edge(LEFT, buff=0.7).shift(DOWN * 0.15)
        self.play(FadeIn(panel, shift=UP * 0.2), run_time=0.8)
        self.say("A Dockerfile is a recipe: base image, deps, your code.", color=DOCKER)
        self.beat(1.6)

        # right side: build layers → image → container --------------------- #
        rx = 4.2
        build_lbl = txt("docker build", fs=20, color=INK, font=MONO)
        build_lbl.move_to([rx, 2.5, 0])
        self.play(FadeIn(build_lbl, shift=DOWN * 0.15), run_time=0.4)

        # each instruction becomes a read-only layer, stacking up
        layer_specs = [(1, "python:3.12-slim", NODE_C),
                       (4, "requirements", CTRL_C),
                       (5, "pip install", CTRL_C),
                       (7, "app code", POD_C)]
        layers = VGroup()
        for k, (li, name, col) in enumerate(layer_specs):
            lay = RoundedRectangle(width=2.7, height=0.5, corner_radius=0.08,
                                   stroke_color=col, stroke_width=2.5,
                                   fill_color=col, fill_opacity=0.22)
            lab = txt(name, fs=15, color=INK).move_to(lay)
            layers.add(VGroup(lay, lab))
        layers.arrange(UP, buff=0.08).move_to([rx, 0.5, 0])

        self.say("`docker build` runs each step — every line is a cached layer.",
                 color=DOCKER)
        for li_grp, (li, _, _) in zip(layers, layer_specs):
            self.focus(panel, lines, [li], color=DOCKER)
            self.play(FadeIn(li_grp, shift=UP * 0.25), run_time=0.45)
            self.beat(0.5)
        img_brace = Brace(layers, LEFT, color=MUTED)
        img_lbl = txt("image", fs=18, color=MUTED).next_to(img_brace, LEFT, buff=0.1)
        self.play(GrowFromCenter(img_brace), FadeIn(img_lbl), run_time=0.5)
        self.beat(1.2)

        # image → running container --------------------------------------- #
        self.focus(panel, lines, [9], color=DOCKER)  # CMD is the entrypoint
        run_lbl = txt("docker run", fs=20, color=INK, font=MONO).move_to([rx, 2.5, 0])
        self.say("`docker run` turns that image into a live container.", color=DOCKER)
        self.play(ReplacementTransform(build_lbl, run_lbl), run_time=0.4)
        cont = container_box(w=2.8, h=1.9, color=DOCKER, ridges=6, label=None)
        inner = VGroup(
            chip("your code", DOCKER, fs=15, h=0.36, fill=0.22),
            chip("python 3.12", NODE_C, fs=15, h=0.36, fill=0.22),
            chip("libs / deps", CTRL_C, fs=15, h=0.36, fill=0.22),
        ).arrange(DOWN, buff=0.12).move_to(cont)
        container = VGroup(cont, inner).move_to([rx, 0.4, 0])
        self.play(
            ReplacementTransform(VGroup(layers, img_brace, img_lbl), cont),
            run_time=0.9)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.1) for c in inner],
                              lag_ratio=0.2), run_time=0.9)
        self.say("A container = your code + everything it needs, sealed in one unit.",
                 color=INK)
        self.beat(1.6)

        # portability punchline: same box, laptop or cloud ----------------- #
        wh = whale(scale=0.7).next_to(container, DOWN, buff=0.55)
        self.play(FadeOut(self.hlrect), FadeIn(wh, shift=UP * 0.2), run_time=0.7)
        self.hlrect = None
        self.say("It runs the same on your laptop and in the cloud — portable & immutable.",
                 color=GOOD)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — The cluster: Pod ⊂ Node ⊂ Cluster (+ Control Plane)
    # ====================================================================== #
    def scene_cluster(self):
        self.section_header("03", "The Cluster", K8S)

        # 1) a lone container ---------------------------------------------- #
        cont = container_box(w=1.1, h=0.78, color=DOCKER, ridges=5, label="app").scale(1.0)
        cont.move_to(ORIGIN)
        self.play(GrowFromCenter(cont), run_time=0.6)
        self.say("Start with our container.", color=DOCKER)
        self.beat(1.2)

        # 2) wrap it in a Pod ---------------------------------------------- #
        pod = pod_hex(r=0.95, color=POD_C, n_containers=1)
        pod.move_to(cont)
        # replace the freshly-grown container with the pod's own container copy
        self.play(Create(pod.hexo), run_time=0.6)
        self.play(ReplacementTransform(cont, pod[1]), run_time=0.5)
        pod_lbl = txt("Pod", fs=20, color=POD_C, weight="BOLD").next_to(pod, DOWN, buff=0.2)
        self.play(FadeIn(pod_lbl, shift=UP * 0.1), run_time=0.4)
        self.say("A Pod is the smallest thing K8s runs — usually one container.",
                 color=POD_C)
        self.beat(1.8)

        # 3) pods live on a Node ------------------------------------------- #
        pod_full = VGroup(pod, pod_lbl)
        node = node_box(w=3.0, h=2.4, color=NODE_C, title="Node")
        node.move_to(LEFT * 3.0 + DOWN * 1.15)
        # shrink the pod, drop it (plus a sibling) onto the node
        p1 = pod_hex(r=0.5, color=POD_C).move_to(node.body.get_center() + LEFT * 0.62 + DOWN * 0.15)
        p2 = pod_hex(r=0.5, color=POD_C).move_to(node.body.get_center() + RIGHT * 0.62 + DOWN * 0.15)
        self.play(FadeIn(node, shift=UP * 0.2),
                  ReplacementTransform(pod_full, p1), run_time=0.9)
        self.play(FadeIn(p2, shift=UP * 0.15), run_time=0.4)
        self.say("Pods run on a Node — a worker machine (a VM or a physical box).",
                 color=NODE_C)
        self.beat(1.4)

        # 4) a second Node, a Control Plane on top = a Cluster ------------- #
        node1 = VGroup(node, p1, p2)
        node2 = node_box(w=3.0, h=2.4, color=NODE_C, title="Node").move_to(RIGHT * 3.0 + DOWN * 1.15)
        q1 = pod_hex(r=0.5, color=POD_C).move_to(node2.body.get_center() + LEFT * 0.62 + DOWN * 0.15)
        q2 = pod_hex(r=0.5, color=POD_C).move_to(node2.body.get_center() + RIGHT * 0.62 + DOWN * 0.15)
        node2_full = VGroup(node2, q1, q2)
        self.play(FadeIn(node2_full, shift=UP * 0.2), run_time=0.7)

        # the control plane sits on top, centred between the two workers
        cp = control_plane().move_to(UP * 1.45)
        self.play(FadeIn(cp, shift=DOWN * 0.2), run_time=0.7)

        boundary = DashedVMobject(
            RoundedRectangle(width=11.2, height=5.4, corner_radius=0.22,
                             stroke_color=K8S, stroke_width=3),
            num_dashes=92, dashed_ratio=0.6)
        boundary.move_to(VGroup(node1, node2_full, cp).get_center())
        clus_lbl = chip("Cluster", K8S, fs=20, weight="BOLD").move_to(boundary.get_top())
        self.play(Create(boundary), run_time=0.9)
        self.play(FadeIn(clus_lbl), run_time=0.3)
        self.say("…nodes together — with a Control Plane — make a Cluster.", color=K8S)
        self.beat(1.6)

        # 5) the control plane's job: schedule pods onto both nodes -------- #
        self.play(Indicate(cp, color=CTRL_C, scale_factor=1.06), run_time=0.7)
        linkA = arr(cp.get_bottom() + LEFT * 1.8, node.body.get_top() + UP * 0.05,
                    color=CTRL_C, sw=3)
        linkB = arr(cp.get_bottom() + RIGHT * 1.8, node2.body.get_top() + UP * 0.05,
                    color=CTRL_C, sw=3)
        self.say("You declare the desired state; the Control Plane schedules pods onto nodes.",
                 color=CTRL_C)
        self.play(Create(linkA), Create(linkB), run_time=0.6)
        self.beat(1.6)

        # recap the nesting — clear the diagram and land it full-screen
        diagram = VGroup(node1, node2_full, cp, boundary, clus_lbl, linkA, linkB)
        nest = txt("container  ⊂  Pod  ⊂  Node  ⊂  Cluster", fs=36, color=INK, weight="BOLD")
        box = SurroundingRectangle(nest, color=K8S, buff=0.3, corner_radius=0.12)
        self.play(FadeOut(self._cap), FadeOut(diagram), run_time=0.6)
        self._cap = None
        self.play(Write(nest), Create(box), run_time=1.0)
        self.beat(2.2)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — Replicas: self-healing & scaling
    # ====================================================================== #
    def scene_replicas(self):
        self.section_header("04", "Replicas", GOOD)

        # the Deployment manifest ------------------------------------------ #
        spec = [
            (0, "kind: Deployment"),
            (0, "spec:"),
            (1, "replicas: 3"),
            (1, "template:"),
            (2, "image: $IMG"),
        ]
        panel, lines = self.code_panel(spec, YAML_T2C, title="deployment.yaml",
                                       target_h=2.6, target_w=4.4, fs=19)
        panel.to_corner(UL, buff=0.5).shift(DOWN * 1.55)
        self.play(FadeIn(panel, shift=UP * 0.15), run_time=0.7)
        self.say("A Deployment says: keep 3 identical replicas running.", color=GOOD)
        self.beat(1.4)

        # two nodes to place pods on --------------------------------------- #
        nodeA = node_box(w=3.0, h=2.0, color=NODE_C, title="Node A")
        nodeB = node_box(w=3.0, h=2.0, color=NODE_C, title="Node B")
        nodes = VGroup(nodeA, nodeB).arrange(RIGHT, buff=0.7)
        nodes.to_edge(RIGHT, buff=0.8).shift(DOWN * 0.35)
        self.play(FadeIn(nodes, shift=UP * 0.2), run_time=0.6)

        # slots: 3 per node; a slot manager keeps placements collision-free -- #
        def slots_of(node, n=3):
            cx = node.body.get_center()[0]
            cy = node.body.get_center()[1] - 0.12
            # 3 slots 0.88 apart; pods are r=0.36 (0.72 wide) so they never overlap
            xs = np.linspace(-0.88, 0.88, n)
            return [np.array([cx + dx, cy, 0]) for dx in xs]
        slotsA, slotsB = slots_of(nodeA), slots_of(nodeB)
        # alternate A/B so pods spread across both nodes as they fill
        slot_pos = [slotsA[0], slotsB[0], slotsA[1], slotsB[1], slotsA[2], slotsB[2]]
        slot_node = ["A", "B", "A", "B", "A", "B"]
        occupied = {}  # slot index -> live pod mobject

        def spawn(i):
            p = pod_hex(r=0.36, color=POD_C).move_to(slot_pos[i])
            occupied[i] = p
            return p

        def spawn_next(prefer=None):
            free = [i for i in range(len(slot_pos)) if i not in occupied]
            if prefer is not None:
                pref = [i for i in free if slot_node[i] == prefer]
                if pref:
                    return spawn(pref[0])
            return spawn(free[0])

        # desired / running read-out --------------------------------------- #
        def readout(desired, ok):
            col = GOOD if ok else WARN
            d = txt(f"desired: {desired}", fs=22, color=MUTED)
            r = txt(f"running: {len(occupied)}", fs=22, color=col, weight="BOLD")
            g = VGroup(d, r).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
            g.next_to(panel, DOWN, buff=0.5).to_edge(LEFT, buff=0.6)
            mark = (make_tick(col) if ok else make_cross(WARN)).scale(0.8)
            mark.next_to(r, RIGHT, buff=0.25)
            return VGroup(g, mark)

        ro = readout(3, False)
        self.play(FadeIn(ro), run_time=0.4)
        # controller brings up 3 pods (slots 0,1,2 → A,B,A)
        news = [spawn(i) for i in range(3)]
        self.play(LaggedStart(*[GrowFromCenter(p) for p in news], lag_ratio=0.3),
                  run_time=1.2)
        ro2 = readout(3, True)
        self.play(ReplacementTransform(ro, ro2), run_time=0.4)
        ro = ro2
        self.say("The controller schedules 3 pods across the nodes.  actual = desired ✓",
                 color=GOOD)
        self.beat(1.8)

        # self-healing: kill the pod in slot 0 (Node A) -------------------- #
        victim = occupied.pop(0)
        x = make_cross(BAD).scale(1.1).move_to(victim)
        self.play(victim.animate.set_color(BAD), FadeIn(x, scale=1.3), run_time=0.4)
        self.play(FadeOut(victim), FadeOut(x), run_time=0.5)
        ro2 = readout(3, False)
        self.play(ReplacementTransform(ro, ro2), run_time=0.4)
        ro = ro2
        self.say("A pod dies…  actual (2) ≠ desired (3).", color=WARN)
        self.beat(1.4)

        # controller reconciles → a fresh pod, rescheduled onto Node B ----- #
        heal = spawn_next(prefer="B")
        self.play(Circumscribe(panel.code, color=GOOD, run_time=0.7))
        self.play(GrowFromCenter(heal), Flash(heal.get_center(), color=GOOD, line_length=0.2),
                  run_time=0.6)
        ro2 = readout(3, True)
        self.play(ReplacementTransform(ro, ro2), run_time=0.4)
        ro = ro2
        self.say("K8s reschedules it automatically — self-healing.", color=GOOD)
        self.beat(1.8)

        # scale up: replicas 3 → 5 ----------------------------------------- #
        old_line = lines[2]
        new_line = Text("replicas: 5", font=MONO, font_size=19, color=PLAIN)
        new_line.scale(old_line.height / new_line.height)
        new_line.move_to(old_line, aligned_edge=LEFT)
        self.play(Indicate(old_line, color=ACCENT), run_time=0.4)
        self.play(ReplacementTransform(old_line, new_line), run_time=0.4)
        lines[2] = new_line
        extra = [spawn_next(), spawn_next()]  # two more pods into free slots
        self.play(LaggedStart(*[GrowFromCenter(p) for p in extra], lag_ratio=0.3),
                  run_time=0.9)
        ro2 = readout(5, True)
        self.play(ReplacementTransform(ro, ro2), run_time=0.4)
        ro = ro2
        self.say("Need more capacity?  Change one number — scale to 5.", color=GOOD)
        self.beat(1.6)

        # a Service load-balances across them ------------------------------ #
        live_pods = list(occupied.values())
        svc = chip("Service", SVC_C, fs=18, w=1.9, h=0.6, weight="BOLD")
        svc.next_to(nodes, UP, buff=0.45)
        self.play(FadeIn(svc, shift=DOWN * 0.15), run_time=0.4)
        fans = VGroup(*[arr(svc.get_bottom(), p.get_top(), color=SVC_C, sw=2.5, buff=0.1)
                        for p in live_pods])
        self.play(LaggedStart(*[Create(a) for a in fans], lag_ratio=0.12), run_time=0.9)
        req = Dot(radius=0.09, color=SVC_C).next_to(svc, UP, buff=0.4)
        self.play(FadeIn(req), run_time=0.2)
        self.play(req.animate.move_to(svc.get_center()), run_time=0.3)
        # a couple of requests flow out to different pods
        r1, r2 = req.copy(), req.copy()
        self.play(r1.animate.move_to(live_pods[0].get_center()),
                  r2.animate.move_to(live_pods[-1].get_center()), run_time=0.6)
        self.play(FadeOut(VGroup(req, r1, r2)), run_time=0.3)
        self.say("A Service gives them one stable address and spreads traffic across them.",
                 color=SVC_C)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 5 — The CD pipeline (GitHub Actions → rolling update)
    # ====================================================================== #
    def scene_pipeline(self):
        self.section_header("05", "Continuous Delivery", GH)

        # the workflow file ------------------------------------------------ #
        spec = [
            (0, "name: build-and-deploy"),
            (0, "on:"),
            (1, "push: { branches: [main] }"),
            (0, ""),
            (0, "jobs:"),
            (1, "deploy:"),
            (2, "runs-on: ubuntu-latest"),
            (2, "steps:"),
            (3, "- uses: actions/checkout@v4"),
            (3, "- run: docker build -t $IMG ."),
            (3, "- run: docker push $IMG"),
            (3, "- run: kubectl set image \\"),
            (4, "deploy/app app=$IMG"),
        ]
        panel, lines = self.code_panel(spec, YAML_T2C, title="workflows/deploy.yml",
                                       target_h=4.4, target_w=6.3, fs=18)
        panel.to_edge(LEFT, buff=0.6).shift(UP * 0.15)
        self.play(FadeIn(panel, shift=UP * 0.2), run_time=0.8)
        self.say("On every push to main, GitHub Actions runs the pipeline.", color=GH, fs=22)
        self.beat(1.4)

        # the pipeline stages, right side ---------------------------------- #
        rx = 3.7
        stage_defs = [("git push", GH, [2]),
                      ("build image", DOCKER, [9]),
                      ("push to registry", NODE_C, [10]),
                      ("kubectl deploy", K8S, [11, 12])]
        stages = VGroup()
        for name, col, _ in stage_defs:
            stages.add(chip(name, col, fs=17, w=2.9, h=0.62, weight="BOLD"))
        stages.arrange(DOWN, buff=0.42).move_to([rx, 0.4, 0])
        conns = VGroup(*[arr(stages[i].get_bottom(), stages[i + 1].get_top(),
                             color=MUTED, sw=3, buff=0.08)
                         for i in range(len(stages) - 1)])
        self.play(LaggedStart(*[FadeIn(s, shift=RIGHT * 0.15) for s in stages],
                              lag_ratio=0.15),
                  LaggedStart(*[GrowArrow(c) for c in conns], lag_ratio=0.15),
                  run_time=1.3)

        # light each stage, highlighting the matching line ----------------- #
        for (name, col, idxs), stagebox in zip(stage_defs, stages):
            self.focus(panel, lines, idxs, color=col)
            self.play(stagebox[0].animate.set_fill(col, 0.35).set_stroke(col, 4),
                      run_time=0.4)
            self.play(Flash(stagebox.get_center(), color=col, line_length=0.18,
                            num_lines=10), run_time=0.4)
            self.beat(0.7)
        img_note = txt("$IMG = ghcr.io/acme/app : <commit-sha>", fs=17, color=ACCENT,
                       font=MONO)
        img_note.next_to(stages, DOWN, buff=0.55)
        if img_note.width > 5.2:
            img_note.scale_to_fit_width(5.2)
        self.play(FadeIn(img_note, shift=UP * 0.1), run_time=0.5)
        self.say("Each image is tagged with the commit SHA — a unique, immutable build.",
                 color=ACCENT, fs=22)
        self.beat(1.8)

        # transition: clear the file & note, then tuck the pipeline to the right #
        fades = [FadeOut(panel), FadeOut(img_note)]
        if self.hlrect:
            fades.append(FadeOut(self.hlrect))
        self.play(*fades, run_time=0.6)
        self.hlrect = None
        self.play(VGroup(stages, conns).animate.scale(0.72).to_edge(RIGHT, buff=0.6),
                  run_time=0.6)

        roll_title = txt("kubectl deploy  →  rolling update", fs=23, color=K8S,
                         weight="BOLD").move_to(LEFT * 2.0 + UP * 2.0)
        self.play(FadeIn(roll_title), run_time=0.4)

        # three v1 pods → replaced one at a time by v2, kept clear of the pipeline
        def make_pod(ver, col):
            p = pod_hex(r=0.55, color=col, n_containers=1)
            tag = txt(ver, fs=16, color=col, weight="BOLD").next_to(p, DOWN, buff=0.12)
            return VGroup(p, tag)
        v1s = VGroup(*[make_pod("v1", MUTED) for _ in range(3)])
        v1s.arrange(RIGHT, buff=1.0).move_to(LEFT * 2.0 + DOWN * 0.5)
        self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.1) for p in v1s], lag_ratio=0.2),
                  run_time=0.8)
        self.say("Old version (v1) keeps serving while the new one rolls out.",
                 color=MUTED, fs=22)
        self.beat(1.2)

        for i in range(3):
            v2 = make_pod("v2", GOOD).move_to(v1s[i]).shift(UP * 1.4)
            self.play(FadeIn(v2, shift=DOWN * 0.2), run_time=0.4)
            self.play(v2.animate.move_to(v1s[i]),
                      FadeOut(v1s[i], shift=DOWN * 0.4), run_time=0.5)
            self.play(Flash(v2.get_center(), color=GOOD, line_length=0.15), run_time=0.3)
            v1s[i] = v2
        self.say("Pods are replaced a few at a time — zero downtime.  Broken? Roll back.",
                 color=GOOD, fs=22)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 6 — What a strong CD needs (the checklist)
    # ====================================================================== #
    def scene_checklist(self):
        self.section_header("06", "A Strong CD Needs…", GOOD)

        items = [
            ("Immutable, versioned images", "tag by commit SHA — never :latest", DOCKER),
            ("Automated tests as a gate", "no green pipeline, no deploy", GH),
            ("Declarative manifests in Git", "the repo is the single source of truth (GitOps)", K8S),
            ("Health probes", "liveness + readiness, so traffic only hits ready pods", POD_C),
            ("Rolling updates + fast rollback", "ship safely; undo in one command", NODE_C),
            ("Config & secrets outside the image", "ConfigMaps / Secrets, not hard-coded", CTRL_C),
            ("Observability on every release", "logs, metrics & alerts to catch regressions", SVC_C),
        ]
        rows = VGroup()
        for title_s, sub_s, col in items:
            tick = make_tick(col, sw=6).scale(0.9)
            head = txt(title_s, fs=24, color=INK, weight="BOLD")
            sub = txt(sub_s, fs=18, color=MUTED)
            body = VGroup(head, sub).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
            row = VGroup(tick, body).arrange(RIGHT, buff=0.32, aligned_edge=UP)
            rows.add(row)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.26)
        rows.scale_to_fit_height(5.2).move_to(DOWN * 0.3)

        self.say("Kubernetes doesn't give you good delivery for free — this does:", color=GOOD)
        for row in rows:
            self.play(GrowFromCenter(row[0]),
                      FadeIn(row[1], shift=RIGHT * 0.2), run_time=0.42)
            self.beat(0.55)
        self.beat(1.4)

        punch = txt("Deploy small, deploy often — and let the cluster keep it healthy.",
                    fs=25, color=K8S, weight="BOLD").to_edge(DOWN, buff=0.5)
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
        self.scene_why()
        self.scene_containers()
        self.scene_cluster()
        self.scene_replicas()
        self.scene_pipeline()
        self.scene_checklist()
        self.play_outro()


# ---- individually renderable scenes -------------------------------------- #
class Intro(_K8sBase):
    def construct(self):
        self.play_intro()


class Why(_K8sBase):
    def construct(self):
        self.scene_why()


class Containers(_K8sBase):
    def construct(self):
        self.scene_containers()


class Cluster(_K8sBase):
    def construct(self):
        self.scene_cluster()


class Replicas(_K8sBase):
    def construct(self):
        self.scene_replicas()


class Pipeline(_K8sBase):
    def construct(self):
        self.scene_pipeline()


class Checklist(_K8sBase):
    def construct(self):
        self.scene_checklist()


class Outro(_K8sBase):
    def construct(self):
        self.play_outro()


class KubernetesCD(_K8sBase):
    """The whole ~3.5 minute film, intro card to outro card."""

    def construct(self):
        self.play_all()


if __name__ == "__main__":
    KubernetesCD().render()

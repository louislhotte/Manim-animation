"""Docker, Visually — a 3D, camera-orbiting, house-style explainer.

The one idea: a container packages your app together with everything it needs
(libraries, runtime, files) into one sealed box that runs the same on every
machine. Unlike a virtual machine it does not carry its own operating system;
it shares the host's kernel, so it is small and starts in milliseconds. You
build images in layers from a Dockerfile, run them as containers, connect them
over a Docker network, and when you outgrow one machine you hand the whole fleet
to Kubernetes.

Visual language: containers are literally boxes, so they are drawn as real 3D
"crates" (translucent neon prisms) standing on a shared host slab, and the
camera slowly orbits so you see them as solid objects from every angle. The
camera only ever moves for the genuinely-3D scenes; the command / Dockerfile
scenes are flat and static (a top-down 2D view), because there is nothing 3D to
reveal there.

All text is ``Text`` (Pango), no LaTeX. Scenes render individually (``Problem``,
``Container``, ``Layers``, ``Commands``, ``Network``, ``VMs``, ``Kube`` …) or as
one film (``DockerVisually``).

Env knobs:
    DK_QUICK=1   collapse every hold for a fast layout render
    DK_DELAY=<s> override the reading-rhythm multiplier
"""
from __future__ import annotations

import os

import numpy as np
from manim import *

QUICK = os.environ.get("DK_QUICK") == "1"
# Reading rhythm. 2.3 so the captions / code panels read comfortably.
DELAY = float(os.environ.get("DK_DELAY", 0.28 if QUICK else 2.3))
ANIM_SLOW = 1.0 if QUICK else 1.15
END_HOLD = 0.2 if QUICK else 2.2

# ---- palette (shared with the Kubernetes / Quantization series) ----------- #
BG = "#0E1117"          # dark slate background
INK = "#F5F3EF"         # warm white text
MUTED = "#8A93A6"       # secondary text
FAINT = "#3A4152"       # hairlines, faint structure
SLAB = "#212C40"        # the host slab fill
DOCKER = "#2496ED"      # Docker blue (the hero container colour)
WEB = "#5B8DEF"         # web tier (blue)
API = "#2EC4B6"         # api tier (teal)
DB = "#FF9F45"          # database tier (orange)
WRITE = "#FFD166"       # writable layer / gold accent
GOOD = "#3DD68C"        # green / healthy
GOLD = "#FFD166"        # accent / gold
BAD = "#FF5C5C"         # red / stop
PANEL = "#141C29"       # HUD / panel fill
K8S = "#326CE5"         # Kubernetes blue (the handoff)
POD_C = "#5B8DEF"       # pods (blue)
NODE_C = "#2EC4B6"      # nodes (teal)
CTRL_C = "#C792EA"      # control plane (purple)
MONO = "Menlo"
FONT = "Helvetica Neue"

# ---- crisp small text ----------------------------------------------------- #
# Pango mangles glyphs/spacing below ~20 pt (small text comes out in a fallback
# font). Shadow Text so every call rasterises at a large base and is scaled DOWN.
_BaseText = Text
_BaseText.set_default(font=FONT)
_TEXT_BASE = 60


def Text(text, font_size=48, **kw):  # noqa: F811 (intentional shadow)
    if font_size >= _TEXT_BASE:
        return _BaseText(text, font_size=font_size, **kw)
    return _BaseText(text, font_size=_TEXT_BASE, **kw).scale(font_size / _TEXT_BASE)


def txt(s, fs=28, color=INK, font=None, slant=None, weight=None, **extra):
    kw = dict(font_size=fs, color=color, **extra)
    if font is not None:
        kw["font"] = font
    if slant is not None:
        kw["slant"] = slant
    if weight is not None:
        kw["weight"] = weight
    return Text(s, **kw)


def lighten(color, amt=0.4):
    return interpolate_color(ManimColor(color), WHITE, amt)


def darken(color, amt=0.4):
    return interpolate_color(ManimColor(color), BLACK, amt)


# =========================================================================== #
# 3D glyphs: crates (containers), the host slab, image layers.
# Cairo 3D has no lighting, so a solid Prism reads as a dark blob. We build every
# box as a bright, translucent "neon crate": low-opacity fill + a bright, thick
# edge stroke in a lighter tint. That reads as a solid 3D object from any orbit
# angle (the fill shows depth, the glowing edges show the shape).
# =========================================================================== #
def crate(cx, cy, size=(1.5, 1.5, 1.3), color=DOCKER, op=0.26, sw=2.6,
          z0=0.0, core=None, core_op=0.9):
    """A translucent neon container box sitting on the plane at height z0."""
    w, d, h = size
    shell = Prism(dimensions=[w, d, h]).move_to([cx, cy, z0 + h / 2])
    shell.set_fill(color, opacity=op)
    shell.set_stroke(lighten(color, 0.5), width=sw, opacity=0.95)
    grp = VGroup(shell)
    grp.shell = shell
    if core is not None:
        cw, cd = w * 0.44, d * 0.44
        ch = h * 0.5
        c = Prism(dimensions=[cw, cd, ch]).move_to([cx, cy, z0 + h / 2])
        c.set_fill(core, opacity=core_op)
        c.set_stroke(lighten(core, 0.5), width=1.6, opacity=0.9)
        grp.add(c)
        grp.core = c
    return grp


def slab(cx, cy, w, d, color=SLAB, h=0.22, z_top=0.0, op=0.55, sw=1.6):
    """A thin, wide plate (the host, a volume, an image layer). Top sits at z_top."""
    p = Prism(dimensions=[w, d, h]).move_to([cx, cy, z_top - h / 2])
    p.set_fill(color, opacity=op)
    p.set_stroke(lighten(color, 0.35), width=sw, opacity=0.8)
    return p


def ground_grid(cx, cy, w, d, color=FAINT, nx=6, ny=6, z=0.005):
    """A faint grid of lines on the z=z plane, for depth cues under the crates."""
    g = VGroup()
    x0, x1 = cx - w / 2, cx + w / 2
    y0, y1 = cy - d / 2, cy + d / 2
    for k in range(nx + 1):
        x = x0 + (x1 - x0) * k / nx
        g.add(Line([x, y0, z], [x, y1, z]))
    for k in range(ny + 1):
        y = y0 + (y1 - y0) * k / ny
        g.add(Line([x0, y, z], [x1, y, z]))
    return g.set_stroke(color=color, width=1.0, opacity=0.30)


# =========================================================================== #
# 2D glyphs for the flat scenes (problem, commands, the Kubernetes handoff).
# Ported from the Kubernetes explainer so the handoff shares its visual language.
# =========================================================================== #
CODE_FS = 20
PLAIN = "#D6DEEB"
COMMENT = "#5F6B7E"
KW = "#C792EA"
FN = "#82AAFF"
VAL = "#F78C6C"
STR = "#7FDBCA"

DOCKER_T2C = {
    "FROM": KW, "WORKDIR": KW, "COPY": KW, "RUN": KW, "EXPOSE": KW, "CMD": KW,
    "python:3.12-slim": VAL, "requirements.txt": STR, "app.py": STR,
    "pip": FN, "8080": VAL,
}


def _safe_t2c(s, table):
    present = {k: v for k, v in table.items() if k in s}
    keys = list(present)
    return {k: v for k, v in present.items()
            if not any(k != o and k in o for o in keys)}


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


def container_box(w=0.92, h=0.66, color=DOCKER, fill=0.16, label=None, ridges=4, sw=3):
    """A little 2D shipping container: a tinted box with vertical ridges."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.06,
                            stroke_color=color, stroke_width=sw,
                            fill_color=color, fill_opacity=fill)
    grp = VGroup(body)
    for x in np.linspace(-w * 0.30, w * 0.30, ridges):
        grp.add(Line([body.get_center()[0] + x, body.get_center()[1] - h * 0.28, 0],
                     [body.get_center()[0] + x, body.get_center()[1] + h * 0.28, 0],
                     stroke_color=color, stroke_width=2).set_opacity(0.7))
    if label:
        grp.add(txt(label, fs=15, color=INK).move_to(body))
    grp.body = body
    return grp


def pod_hex(r=0.55, color=POD_C, ccolor=DOCKER):
    """A Pod: a flat-top hexagon holding one container (the Kubernetes motif)."""
    hexo = RegularPolygon(n=6, start_angle=0, radius=r,
                          stroke_color=color, stroke_width=3,
                          fill_color=color, fill_opacity=0.10)
    inner = container_box(w=r * 1.0, h=r * 0.62, color=ccolor).move_to(hexo)
    grp = VGroup(hexo, inner)
    grp.hexo = hexo
    return grp


def node_box(w=2.7, h=2.0, color=NODE_C, title="Node"):
    body = RoundedRectangle(width=w, height=h, corner_radius=0.14,
                            stroke_color=color, stroke_width=3,
                            fill_color=color, fill_opacity=0.05)
    bar = RoundedRectangle(width=w, height=0.5, corner_radius=0.14, stroke_width=0,
                           fill_color=color, fill_opacity=0.16).align_to(body, UP)
    cpu = Square(side_length=0.2, stroke_color=color, stroke_width=2,
                 fill_color=color, fill_opacity=0.35)
    cpu.move_to([body.get_left()[0] + 0.34, bar.get_center()[1], 0])
    ttl = txt(title, fs=17, color=INK, weight="BOLD").next_to(cpu, RIGHT, buff=0.15)
    grp = VGroup(body, bar, cpu, ttl)
    grp.body = body
    return grp


def control_plane(w=6.4):
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


# =========================================================================== #
# Base scene
# =========================================================================== #
class _DockerBase(ThreeDScene):
    def setup(self):
        self.camera.background_color = BG
        self._orbiting = False
        self._cap = None

    # slow every played animation slightly; never scale a bare wait
    def play(self, *anims, **kw):
        if "run_time" in kw:
            kw["run_time"] *= ANIM_SLOW
        super().play(*anims, **kw)

    # ---- timing ----------------------------------------------------------- #
    def beat(self, t=1.0):
        self.wait(t * DELAY)

    def card_wait(self, t=1.0):
        self.wait(t * (0.3 if QUICK else 1.0))

    def settle(self):
        self.wait(END_HOLD)

    # ---- camera ----------------------------------------------------------- #
    def go_3d(self, phi=66, theta=-62, zoom=0.9, rate=0.045, focal=None):
        kw = dict(phi=phi * DEGREES, theta=theta * DEGREES, zoom=zoom)
        if focal is not None:
            kw["focal_distance"] = focal
        self.set_camera_orientation(**kw)
        self.begin_ambient_camera_rotation(rate=rate)
        self._orbiting = True

    def stop_orbit(self):
        if self._orbiting:
            self.stop_ambient_camera_rotation()
            self._orbiting = False

    def go_flat_instant(self):
        self.stop_orbit()
        self.set_camera_orientation(phi=0, theta=-90 * DEGREES, zoom=1.0)

    # ---- fixed-in-frame HUD (2D overlay that ignores the orbit) ----------- #
    def _fix(self, *ms):
        self.add_fixed_in_frame_mobjects(*ms)
        for m in ms:
            self.remove(m)

    def _orient(self, *ms):
        """Billboard mobjects at their current 3D anchor (they face the camera)."""
        self.add_fixed_orientation_mobjects(*ms)
        for m in ms:
            self.remove(m)

    def say(self, s, color=INK, fs=27, italic=False, buff=0.5):
        m = txt(s, fs=fs, color=color, slant=ITALIC if italic else None)
        if m.width > 12.4:
            m.scale_to_fit_width(12.4)
        m.to_edge(DOWN, buff=buff)
        return m

    def show_say(self, s, **kw):
        """Fixed-in-frame running caption at the bottom edge (works during orbit)."""
        m = self.say(s, **kw)
        self._fix(m)
        anims = [FadeIn(m, shift=UP * 0.1)]
        if self._cap is not None:
            anims.append(FadeOut(self._cap, shift=UP * 0.1))
        self.play(*anims, run_time=0.55)
        self._cap = m
        return m

    def replace_say(self, s, **kw):
        return self.show_say(s, **kw)

    def say_flat(self, s, color=INK, fs=27, weight="NORMAL"):
        """Running caption for the FLAT (2D) scenes: a plain mobject, no fixing."""
        new = txt(s, fs=fs, color=color, weight=weight).to_edge(DOWN, buff=0.5)
        if new.width > 12.6:
            new.scale_to_fit_width(12.6)
        if self._cap is None:
            self.play(FadeIn(new, shift=UP * 0.12), run_time=0.5)
        else:
            self.play(ReplacementTransform(self._cap, new), run_time=0.5)
        self._cap = new
        return new

    def show_title(self, s, color=INK, fs=44, buff=0.42):
        t = Text(s, font_size=fs, color=color, weight="BOLD")
        if t.width > 12.8:
            t.scale_to_fit_width(12.8)
        t.to_edge(UP, buff=buff)
        self._fix(t)
        self.play(FadeIn(t, shift=DOWN * 0.12), run_time=0.7)
        return t

    def section_header(self, label, color=DOCKER, flat=False):
        t = Text(label, font_size=30, color=INK, weight="BOLD")
        line = Line(t.get_left(), t.get_right()).set_stroke(color=color, width=3)
        line.next_to(t, DOWN, buff=0.12)
        g = VGroup(t, line).to_corner(UL, buff=0.5)
        if not flat:
            self._fix(g)
        self.play(FadeIn(g, shift=DOWN * 0.1), run_time=0.55)
        return g

    # ---- teardown --------------------------------------------------------- #
    def wipe(self, rt=0.7):
        self.stop_orbit()
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            super().play(*[FadeOut(m) for m in self.mobjects], run_time=rt)
        self._cap = None

    def _rule_under(self, header, pad=1.0, color=GOLD, drop=0.45):
        return Line([header.get_left()[0] - pad, header.get_bottom()[1] - drop, 0],
                    [header.get_right()[0] + pad, header.get_bottom()[1] - drop, 0]
                    ).set_stroke(width=3, color=color)

    # ---- code panel (Menlo, syntax-coloured, night-owl-ish) --------------- #
    def code_panel(self, spec, table, title="Dockerfile", fs=CODE_FS,
                   indent_unit=0.5, line_buff=0.17, target_h=5.6, target_w=6.6):
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
                              fill_color="#0A0E15", fill_opacity=1.0).move_to(code)
        bar = RoundedRectangle(width=bg.width, height=0.5, corner_radius=0.16,
                               stroke_width=0, fill_color="#141C29", fill_opacity=1.0)
        bar.move_to(bg).align_to(bg, UP)
        dots = VGroup(*[Dot(radius=0.045, color=c)
                        for c in ("#FF5F57", "#FEBC2E", "#28C840")]).arrange(RIGHT, buff=0.11)
        dots.move_to([bg.get_left()[0] + 0.42, bar.get_center()[1], 0])
        ttl = txt(title, fs=15, color=MUTED, font=MONO)
        if ttl.width > bg.width - 1.5:
            ttl.scale_to_fit_width(bg.width - 1.5)
        ttl.next_to(dots, RIGHT, buff=0.34).set_y(bar.get_center()[1])
        code.shift(DOWN * 0.2)
        panel = VGroup(bg, bar, dots, ttl, code)
        panel.code = code
        return panel, lines

    def hl_lines(self, panel, lines, idxs, color=GOLD, opacity=0.16, pad=0.05, xpad=0.34):
        tops = [lines[i].get_top()[1] for i in idxs]
        bots = [lines[i].get_bottom()[1] for i in idxs]
        y_hi, y_lo = max(tops) + pad, min(bots) - pad
        rect = RoundedRectangle(width=panel[0].width - xpad, height=(y_hi - y_lo),
                                corner_radius=0.08, stroke_width=0,
                                fill_color=color, fill_opacity=opacity)
        rect.move_to([panel[0].get_center()[0], (y_hi + y_lo) / 2, 0])
        return rect

    # ====================================================================== #
    # Intro card (flat)
    # ====================================================================== #
    def play_intro(self):
        self.go_flat_instant()
        wh = whale(scale=0.85, color=DOCKER).to_edge(UP, buff=0.9)
        self.play(FadeIn(wh, shift=DOWN * 0.2), run_time=1.0)
        self.play(wh.animate.shift(UP * 0.12), rate_func=there_and_back,
                  run_time=1.6)
        header = Text("Docker, Visually", font_size=56, color=INK, weight="BOLD")
        header.set(width=min(9.4, header.width)).move_to(DOWN * 0.2)
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=DOCKER)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        self.play(Write(header), Create(line), run_time=1.5)
        self.card_wait(0.6)
        sub = Text("What a container is, and how it runs your code anywhere",
                   font_size=29, color=MUTED)
        if sub.width > line.width + 1.4:
            sub.scale_to_fit_width(line.width + 1.4)
        sub.move_to(header)
        self.play(Transform(header, sub), run_time=1.0)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.card_wait(1.8)
        self.play(FadeOut(VGroup(header, writer, line)), FadeOut(wh), run_time=1.0)
        self.card_wait(0.2)

    # ====================================================================== #
    # Scene 1 — "It works on my machine" (flat 2D)
    # ====================================================================== #
    def scene_problem(self):
        self.go_flat_instant()
        hdr = self.section_header("The problem", DOCKER, flat=True)

        def machine(title, py, lib, ok):
            col = GOOD if ok else BAD
            body = RoundedRectangle(width=4.0, height=2.7, corner_radius=0.16,
                                    stroke_color=MUTED, stroke_width=2.5,
                                    fill_color=PANEL, fill_opacity=0.9)
            bar = RoundedRectangle(width=4.0, height=0.55, corner_radius=0.16,
                                   stroke_width=0, fill_color="#1C2536",
                                   fill_opacity=1.0).align_to(body, UP)
            name = txt(title, fs=20, color=INK, weight="BOLD").move_to(
                [body.get_left()[0] + 1.1, bar.get_center()[1], 0])
            envs = VGroup(chip(py, MUTED, fs=16, h=0.44),
                          chip(lib, MUTED, fs=16, h=0.44)).arrange(DOWN, buff=0.18)
            envs.move_to(body).shift(UP * 0.12)
            status = txt("app runs" if ok else "app crashes", fs=19, color=col,
                         weight="BOLD")
            mark = (make_check(col) if ok else make_x(col)).scale(0.8)
            row = VGroup(mark, status).arrange(RIGHT, buff=0.2)
            row.next_to(envs, DOWN, buff=0.3)
            return VGroup(body, bar, name, envs, row)

        left = machine("my laptop", "Python 3.12", "libssl 3.0", True)
        right = machine("the server", "Python 3.9", "libssl 1.1", False)
        VGroup(left, right).arrange(RIGHT, buff=1.1).move_to(UP * 0.25)

        self.say_flat("You write an app, and on your laptop it runs perfectly.",
                      color=INK)
        self.play(FadeIn(left, shift=UP * 0.2), run_time=0.8)
        self.beat(1.7)

        self.say_flat("You ship the exact same code to the server.", color=INK)
        self.play(FadeIn(right, shift=UP * 0.2), run_time=0.8)
        self.beat(1.5)

        self.say_flat("Different Python, different libraries, and it breaks.",
                      color=BAD)
        self.play(Wiggle(right, scale_value=1.05, rotation_angle=0.015 * TAU),
                  run_time=0.8)
        self.beat(1.9)

        punch = txt('"But it works on my machine."', fs=30, color=WRITE,
                    weight="BOLD").move_to(DOWN * 2.05)
        self.play(Write(punch), run_time=1.0)
        self.beat(1.6)
        self.say_flat("Docker fixes this: ship the app and its whole environment as one box.",
                      color=DOCKER)
        self.beat(2.0)
        self.settle()
        self.play(FadeOut(VGroup(left, right, punch, hdr, self._cap)), run_time=0.7)
        self._cap = None

    # ====================================================================== #
    # Scene 2 — the container as a 3D box (orbit)
    # ====================================================================== #
    def scene_container(self):
        self.go_3d(phi=66, theta=-62, zoom=0.95, rate=0.05)
        hdr = self.section_header("The container")

        # the host slab + a faint floor grid
        host = slab(0, 0, 6.4, 5.0, color=SLAB, h=0.24)
        grid = ground_grid(0, 0, 6.4, 5.0, nx=6, ny=5)
        self.play(FadeIn(host), FadeIn(grid), run_time=0.7)
        kern = txt("host operating system", fs=20, color=MUTED)
        kern.move_to([0, -3.0, 0.02])
        self._orient(kern)
        self.play(FadeIn(kern), run_time=0.4)

        cap = self.show_say(
            "A container is one box that holds your app and everything it needs.")

        # the hero crate, with a bright core (your app)
        box = crate(0, 0, size=(2.2, 2.2, 1.9), color=DOCKER, op=0.24, sw=3.0,
                    core=WRITE, core_op=0.85)
        self.play(GrowFromPoint(box, [0, 0, 0]), run_time=1.3)
        self.beat(1.8)

        # label the contents as billboards floating above the crate
        cap = self.replace_say(
            "Inside are your code, the libraries, and the language runtime.")
        labels = VGroup(
            chip("your code", WRITE, fs=17, h=0.5, fill=0.2, weight="BOLD"),
            chip("libraries", API, fs=17, h=0.5, fill=0.2, weight="BOLD"),
            chip("runtime", WEB, fs=17, h=0.5, fill=0.2, weight="BOLD"),
        ).arrange(DOWN, buff=0.16)
        labels.move_to([0, 0, 2.9])
        self._orient(labels)
        self.play(LaggedStart(*[FadeIn(l, shift=UP * 0.1) for l in labels],
                              lag_ratio=0.3), run_time=1.2)
        self.beat(2.2)

        cap = self.replace_say(
            "Everything it needs is sealed inside, so nothing leaks in or out.")
        self.play(Indicate(box.shell, color=lighten(DOCKER, 0.3),
                           scale_factor=1.05), run_time=1.0)
        self.beat(1.8)

        cap = self.replace_say(
            "It shares the host operating system, so it stays small and starts fast.")
        self.play(host.animate.set_fill(DOCKER, 0.16).set_stroke(lighten(DOCKER, 0.3)),
                  run_time=0.8)
        self.play(host.animate.set_fill(SLAB, 0.55).set_stroke(lighten(SLAB, 0.35)),
                  run_time=0.8)
        self.beat(2.0)

        cap = self.replace_say(
            "And the box is identical everywhere, so it runs the same on any machine.")
        self.beat(2.1)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 3 — images & layers (orbit)
    # ====================================================================== #
    def scene_layers(self):
        self.go_3d(phi=68, theta=-58, zoom=0.92, rate=0.045)
        hdr = self.section_header("Images & layers")

        host = slab(0, 0, 5.6, 4.6, color=SLAB, h=0.22)
        self.play(FadeIn(host), run_time=0.5)

        cap = self.show_say(
            "You do not build the box by hand. A Dockerfile builds an image.")
        self.beat(1.6)

        # image = a stack of read-only layers, one per Dockerfile step
        cap = self.replace_say(
            "The image is built in layers, one for each step of the recipe.")
        specs = [("base image  (python:3.12-slim)", NODE_C),
                 ("dependencies  (pip install)", CTRL_C),
                 ("your app code  (COPY . .)", WEB)]
        lay_h = 0.42
        layer_mobs = []
        legend_rows = []
        for k, (name, col) in enumerate(specs):
            z_top = (k + 1) * lay_h
            s = slab(0, 0, 2.6, 2.6, color=col, h=lay_h, z_top=z_top, op=0.42, sw=2.4)
            layer_mobs.append(s)
            dot = Dot(radius=0.09, color=col)
            lab = txt(name, fs=18, color=INK)
            row = VGroup(dot, lab).arrange(RIGHT, buff=0.2)
            legend_rows.append(row)
        legend = VGroup(*legend_rows).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        legend.to_corner(UR, buff=0.55)
        for k, (s, row) in enumerate(zip(layer_mobs, legend)):
            self._fix(row)
            self.play(GrowFromPoint(s, [0, 0, k * lay_h]),
                      FadeIn(row, shift=LEFT * 0.15), run_time=0.7)
            self.beat(0.9)
        self.beat(1.2)

        cap = self.replace_say(
            "Each layer is read-only and cached, so rebuilds only redo what changed.")
        self.beat(2.0)

        # running it adds a thin writable layer on top = a container
        cap = self.replace_say(
            "Running the image adds a thin writable layer on top. That is a container.")
        top_z = len(specs) * lay_h
        wr = slab(0, 0, 2.6, 2.6, color=WRITE, h=0.26, z_top=top_z + 0.26, op=0.5, sw=2.6)
        wlbl = txt("writable layer", fs=17, color=WRITE, weight="BOLD")
        wlbl.move_to([0, 0, top_z + 0.9])
        self._orient(wlbl)
        self.play(GrowFromPoint(wr, [0, 0, top_z]), FadeIn(wlbl), run_time=0.9)
        self.beat(2.0)

        # copy-on-write: many containers share the same read-only image layers
        cap = self.replace_say(
            "Many containers can share those same layers, so each one is cheap to start.")
        self.play(FadeOut(wr), FadeOut(wlbl), run_time=0.4)
        tops = VGroup()
        for dx in (-1.7, 0.0, 1.7):
            w = slab(dx, 0, 1.1, 2.4, color=WRITE, h=0.24, z_top=top_z + 0.24,
                     op=0.5, sw=2.2)
            tops.add(w)
        self.play(LaggedStart(*[GrowFromPoint(w, [w.get_center()[0], 0, top_z])
                                for w in tops], lag_ratio=0.25), run_time=1.1)
        share = txt("3 containers, one shared image", fs=18, color=INK)
        share.move_to([0, 0, top_z + 0.95])
        self._orient(share)
        self.play(FadeIn(share), run_time=0.5)
        self.beat(2.2)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 4 — the main commands (flat 2D, static camera)
    # ====================================================================== #
    def scene_commands(self):
        self.go_flat_instant()
        hdr = self.section_header("The main commands", DOCKER, flat=True)

        spec = [
            (0, "# a recipe for one immutable image"),
            (0, "FROM python:3.12-slim"),
            (0, "WORKDIR /app"),
            (0, "COPY requirements.txt ."),
            (0, "RUN pip install -r requirements.txt"),
            (0, "COPY . ."),
            (0, "EXPOSE 8080"),
            (0, 'CMD ["python", "app.py"]'),
        ]
        panel, lines = self.code_panel(spec, DOCKER_T2C, title="Dockerfile",
                                       target_h=4.9, target_w=5.6, fs=19)
        panel.to_edge(LEFT, buff=0.6).shift(DOWN * 0.15)
        self.play(FadeIn(panel, shift=UP * 0.2), run_time=0.8)
        self.say_flat("It starts with a Dockerfile: a recipe for the image.",
                      color=DOCKER)
        self.beat(1.6)

        # right side: the lifecycle Dockerfile -> image -> container, + registry
        rx = 3.7
        reg = chip("Docker Hub  (registry)", CTRL_C, fs=17, h=0.6, w=3.7, weight="BOLD")
        reg.move_to([rx, 2.7, 0])
        img = crate_2d("image", DOCKER, w=2.4, h=1.05)
        img.move_to([rx, 0.9, 0])
        cont = crate_2d("container", GOOD, w=2.4, h=1.05, running=True)
        cont.move_to([rx, -1.5, 0])

        build_a = arr(panel.get_right() + RIGHT * 0.05, img.get_left(),
                      color=DOCKER, sw=4)
        build_l = txt("docker build", fs=17, color=DOCKER, font=MONO, weight="BOLD")
        build_l.next_to(build_a, UP, buff=0.12)
        run_a = arr(img.get_bottom(), cont.get_top(), color=GOOD, sw=4)
        run_l = txt("docker run", fs=17, color=GOOD, font=MONO, weight="BOLD")
        run_l.next_to(run_a, RIGHT, buff=0.18)

        # registry pull / push (side by side vertical arrows)
        pull_a = arr(reg.get_bottom() + LEFT * 0.55, img.get_top() + LEFT * 0.55,
                     color=CTRL_C, sw=3.2, buff=0.1)
        push_a = arr(img.get_top() + RIGHT * 0.55, reg.get_bottom() + RIGHT * 0.55,
                     color=CTRL_C, sw=3.2, buff=0.1)
        pull_l = txt("pull", fs=15, color=CTRL_C, font=MONO).next_to(pull_a, LEFT, buff=0.12)
        push_l = txt("push", fs=15, color=CTRL_C, font=MONO).next_to(push_a, RIGHT, buff=0.12)

        self.say_flat("docker build turns the recipe into an image.", color=DOCKER)
        self.play(GrowArrow(build_a), FadeIn(build_l), FadeIn(img, shift=RIGHT * 0.15),
                  run_time=0.9)
        self.beat(1.8)

        self.say_flat("docker run turns that image into a live container.", color=GOOD)
        self.play(GrowArrow(run_a), FadeIn(run_l), FadeIn(cont, shift=DOWN * 0.15),
                  run_time=0.9)
        self.beat(1.8)

        self.say_flat("docker push and pull share images through a registry like Docker Hub.",
                      color=CTRL_C)
        self.play(FadeIn(reg, shift=DOWN * 0.15), run_time=0.6)
        self.play(GrowArrow(pull_a), GrowArrow(push_a),
                  FadeIn(pull_l), FadeIn(push_l), run_time=0.8)
        self.beat(2.0)

        # a small cheat-sheet of the everyday commands
        self.say_flat("A few commands cover the whole daily loop.", color=INK)
        cmds = VGroup(
            cmd_row("docker build -t app .", "package the image", DOCKER),
            cmd_row("docker run -p 8080:8080 app", "start a container", GOOD),
            cmd_row("docker ps", "list what is running", WEB),
            cmd_row("docker stop / rm", "stop and clean up", BAD),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        cmds.next_to(hdr, DOWN, buff=0.2).to_edge(LEFT, buff=0.6)
        # reveal only after fading the panel + its build arrow (whose origin panel
        # is gone) so nothing collides and no arrow dangles from empty space
        self.play(FadeOut(panel), FadeOut(build_a), FadeOut(build_l), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(c, shift=RIGHT * 0.15) for c in cmds],
                              lag_ratio=0.25), run_time=1.4)
        self.beat(2.4)
        self.settle()
        self.play(FadeOut(VGroup(cmds, img, cont, reg, run_a, run_l,
                                 pull_a, push_a, pull_l, push_l, hdr, self._cap)),
                  run_time=0.7)
        self._cap = None

    # ====================================================================== #
    # Scene 5 — how containers interact: one Docker network (orbit)
    # ====================================================================== #
    def scene_network(self):
        # a gentle, slow orbit: fast rotation swings a straight row of boxes edge-on
        # and collapses it into one overlapping column, so keep the sweep small.
        self.go_3d(phi=62, theta=-74, zoom=0.92, rate=0.028)
        hdr = self.section_header("How they interact")

        host = slab(0, 0, 7.0, 4.6, color=SLAB, h=0.22)
        grid = ground_grid(0, 0, 7.0, 4.6, nx=7, ny=4)
        self.play(FadeIn(host), FadeIn(grid), run_time=0.6)

        cap = self.show_say(
            "A real app is several containers, each isolated on the same host.")
        # three tiers in a shallow V (NOT a straight row): three non-collinear
        # points can never all line up under the orbit, so they stay separate.
        positions = {"web": (-2.6, 0.85), "api": (0.0, -0.85), "db": (2.6, 0.85)}
        cols = {"web": WEB, "api": API, "db": DB}
        boxes = {}
        for name, (x, y) in positions.items():
            boxes[name] = crate(x, y, size=(1.4, 1.4, 1.35), color=cols[name],
                                op=0.26, sw=2.8, core=lighten(cols[name], 0.25),
                                core_op=0.7)
        order = ["web", "api", "db"]
        self.play(LaggedStart(*[GrowFromPoint(boxes[n], [*positions[n], 0])
                                for n in order], lag_ratio=0.25), run_time=1.3)
        # name billboards above each crate
        name_labels = []
        for name in order:
            x, y = positions[name]
            lb = txt(name, fs=20, color=lighten(cols[name], 0.25), weight="BOLD")
            lb.move_to([x, y, 1.95])
            name_labels.append(lb)
        self._orient(*name_labels)
        self.play(*[FadeIn(lb) for lb in name_labels], run_time=0.5)
        self.beat(1.9)

        # the Docker network: links web -> api -> db (a V), at mid-height
        cap = self.replace_say(
            "They are private, but talk to each other over a Docker network.")
        z = 0.7
        wp = [*positions["web"], z]
        ap = [*positions["api"], z]
        dp = [*positions["db"], z]
        link_wa = Line(wp, ap).set_stroke(GOOD, 3.2, opacity=0.85)
        link_ad = Line(ap, dp).set_stroke(GOOD, 3.2, opacity=0.85)
        self.play(Create(link_wa), Create(link_ad), run_time=0.8)
        net_lbl = txt("docker network  (bridge)", fs=17, color=GOOD)
        net_lbl.move_to([0, -2.05, 0.02])
        self._orient(net_lbl)
        self.play(FadeIn(net_lbl), run_time=0.4)
        self.beat(1.6)

        # a request pulses web -> api -> db and back
        cap = self.replace_say(
            "A request flows from web, to the api, to the database, and back.")
        for _ in range(2):
            pulse = Dot3D(point=wp, radius=0.12, color=WRITE)
            self.add(pulse)
            self.play(pulse.animate.move_to(ap), run_time=0.5)
            self.play(pulse.animate.move_to(dp), run_time=0.5)
            self.play(pulse.animate.move_to(ap), run_time=0.4)
            self.play(pulse.animate.move_to(wp), run_time=0.4)
            self.remove(pulse)
        self.beat(1.4)

        # a volume under the database = persistence
        cap = self.replace_say(
            "The database keeps its data in a volume, which outlives the container.")
        dx, dy = positions["db"]
        vol = slab(dx, dy, 1.8, 1.8, color=DB, h=0.34, z_top=-0.28, op=0.4, sw=2.4)
        vlbl = txt("volume", fs=17, color=lighten(DB, 0.2), weight="BOLD")
        vlbl.move_to([dx, dy - 1.55, 0.02])
        self._orient(vlbl)
        self.play(GrowFromPoint(vol, [dx, dy, -0.28]), FadeIn(vlbl), run_time=0.8)
        self.beat(2.1)

        cap = self.replace_say(
            "One file, docker-compose.yml, wires these containers into a single app.")
        self.beat(2.0)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 6 — containers vs virtual machines (orbit, gentle)
    # ====================================================================== #
    def scene_vms(self):
        self.go_3d(phi=70, theta=-90, zoom=0.9, rate=0.03)
        hdr = self.section_header("Why so light?")

        # left: a virtual-machine stack (tall). right: a container stack (short).
        def stack(cx, base_specs, unit_specs, unit_h, n_units, base_col):
            """base_specs/unit_specs: list of (label, colour, height)."""
            mobs = []
            z = 0.0
            # shared base layers
            for label, col, h in base_specs:
                s = slab(cx, 0, 2.4, 2.0, color=col, h=h, z_top=z + h, op=0.4, sw=2.2)
                mobs.append((s, label, col, z + h / 2))
                z += h
            # repeated per-app units
            for u in range(n_units):
                for label, col, h in unit_specs:
                    s = slab(cx, 0, 2.0, 1.7, color=col, h=h, z_top=z + h, op=0.4, sw=2.0)
                    mobs.append((s, label if u == 0 else None, col, z + h / 2))
                    z += h
            return mobs, z

        vm_mobs, vm_top = stack(
            -2.6,
            base_specs=[("Hardware", FAINT, 0.34), ("Hypervisor", MUTED, 0.34)],
            unit_specs=[("Guest OS", CTRL_C, 0.42), ("App", DB, 0.30)],
            unit_h=0.72, n_units=3, base_col=FAINT)
        ct_mobs, ct_top = stack(
            2.6,
            base_specs=[("Hardware", FAINT, 0.34), ("Host OS", MUTED, 0.34),
                        ("Docker Engine", DOCKER, 0.36)],
            unit_specs=[("App", GOOD, 0.30)],
            unit_h=0.30, n_units=3, base_col=FAINT)

        vm_title = txt("Virtual machines", fs=20, color=CTRL_C, weight="BOLD")
        vm_title.move_to([-2.6, 0, vm_top + 0.6])
        ct_title = txt("Containers", fs=20, color=GOOD, weight="BOLD")
        ct_title.move_to([2.6, 0, ct_top + 0.6])
        self._orient(vm_title, ct_title)

        cap = self.show_say(
            "A virtual machine runs a full guest operating system for every app.")
        self.play(FadeIn(vm_title), run_time=0.4)
        self.play(LaggedStart(*[GrowFromPoint(s, [s.get_center()[0], 0, zc])
                                for (s, _, _, zc) in vm_mobs], lag_ratio=0.12),
                  run_time=1.8)
        # billboard the VM layer labels
        vm_labels = VGroup(*[txt(lbl, fs=14, color=INK).move_to(
            [-2.6 + 1.95, 0, zc]) for (s, lbl, col, zc) in vm_mobs if lbl])
        self._orient(*vm_labels)
        self.play(FadeIn(vm_labels), run_time=0.5)
        self.beat(2.0)

        cap = self.replace_say(
            "That is heavy: gigabytes of memory, and minutes to boot.")
        self.beat(1.7)

        cap = self.replace_say(
            "Containers share the host kernel through the Docker engine.")
        self.play(FadeIn(ct_title), run_time=0.4)
        self.play(LaggedStart(*[GrowFromPoint(s, [s.get_center()[0], 0, zc])
                                for (s, _, _, zc) in ct_mobs], lag_ratio=0.12),
                  run_time=1.6)
        ct_labels = VGroup(*[txt(lbl, fs=14, color=INK).move_to(
            [2.6 + 2.1, 0, zc]) for (s, lbl, col, zc) in ct_mobs if lbl])
        self._orient(*ct_labels)
        self.play(FadeIn(ct_labels), run_time=0.5)
        self.beat(2.0)

        cap = self.replace_say(
            "So they are megabytes, not gigabytes, and start in milliseconds.")
        self.beat(2.2)
        self.settle()
        self.wipe()

    # ====================================================================== #
    # Scene 7 — the link to Kubernetes (orbit -> flat handoff)
    # ====================================================================== #
    def scene_kube(self):
        self.go_3d(phi=64, theta=-64, zoom=0.95, rate=0.05)
        hdr = self.section_header("Scaling up")

        host = slab(0, 0, 6.6, 4.4, color=SLAB, h=0.22)
        self.play(FadeIn(host), run_time=0.5)
        cap = self.show_say("One machine happily runs a handful of containers.")
        spots = [(-2.0, 0.8), (0.0, 0.8), (2.0, 0.8),
                 (-2.0, -0.8), (0.0, -0.8), (2.0, -0.8)]
        cols = [WEB, API, DB, GOOD, CTRL_C, DOCKER]
        boxes = VGroup()
        for (x, y), c in zip(spots, cols):
            boxes.add(crate(x, y, size=(1.3, 1.1, 1.2), color=c, op=0.26, sw=2.4))
        self.play(LaggedStart(*[GrowFromPoint(b, [b.get_center()[0],
                                                  b.get_center()[1], 0])
                                for b in boxes], lag_ratio=0.12), run_time=1.5)
        self.beat(1.8)

        cap = self.replace_say(
            "But what about hundreds of them, across many machines?")
        self.beat(1.9)

        # transition to the flat Kubernetes diagram
        self.stop_orbit()
        self.play(FadeOut(boxes), FadeOut(host), FadeOut(hdr), run_time=0.6)
        self.go_flat_instant()
        hdr2 = self.section_header("Enter Kubernetes", K8S, flat=True)

        # two nodes, each with two pods, a control plane on top, cluster boundary
        nodeA = node_box(w=3.0, h=1.9, color=NODE_C, title="Node A")
        nodeB = node_box(w=3.0, h=1.9, color=NODE_C, title="Node B")
        nodes = VGroup(nodeA, nodeB).arrange(RIGHT, buff=0.7).move_to(DOWN * 1.1)
        for node in (nodeA, nodeB):
            pods = VGroup(pod_hex(r=0.42, color=POD_C),
                          pod_hex(r=0.42, color=POD_C)).arrange(RIGHT, buff=0.5)
            pods.move_to(node.body.get_center() + DOWN * 0.1)
            node.add(pods)
        cp = control_plane(w=6.2).move_to(UP * 1.35)
        boundary = DashedVMobject(
            RoundedRectangle(width=8.6, height=5.0, corner_radius=0.22,
                             stroke_color=K8S, stroke_width=3),
            num_dashes=84, dashed_ratio=0.6)
        boundary.move_to(VGroup(nodes, cp).get_center())
        clus = chip("Cluster", K8S, fs=18, weight="BOLD").move_to(boundary.get_top())

        self.say_flat("Kubernetes schedules your containers onto a cluster of machines.",
                      color=K8S)
        self.play(FadeIn(cp, shift=DOWN * 0.15), run_time=0.6)
        self.play(FadeIn(nodes, shift=UP * 0.15), run_time=0.8)
        self.play(Create(boundary), FadeIn(clus), run_time=0.8)
        linkA = arr(cp.get_bottom() + LEFT * 1.6, nodeA.body.get_top(),
                    color=CTRL_C, sw=3)
        linkB = arr(cp.get_bottom() + RIGHT * 1.6, nodeB.body.get_top(),
                    color=CTRL_C, sw=3)
        self.play(Create(linkA), Create(linkB), run_time=0.6)
        self.beat(2.0)

        self.say_flat("It restarts them when they crash, and scales them on demand.",
                      color=GOOD)
        self.beat(2.0)

        # handoff card
        self.play(FadeOut(VGroup(nodes, cp, boundary, clus, linkA, linkB, hdr2,
                                 self._cap)), run_time=0.6)
        self._cap = None
        line1 = txt("Docker builds and runs one container.", fs=30, color=DOCKER,
                    weight="BOLD")
        line2 = txt("Kubernetes runs thousands, across many machines.", fs=30,
                    color=K8S, weight="BOLD")
        card = VGroup(line1, line2).arrange(DOWN, buff=0.4).move_to(UP * 0.4)
        self.play(Write(line1), run_time=0.9)
        self.play(Write(line2), run_time=0.9)
        self.beat(1.6)
        nxt = txt("Continue with the Kubernetes explainer.", fs=24, color=MUTED)
        nxt.next_to(card, DOWN, buff=0.7)
        self.play(FadeIn(nxt, shift=UP * 0.1), run_time=0.6)
        self.beat(2.0)
        self.settle()
        self.play(FadeOut(VGroup(card, nxt)), run_time=0.7)

    # ====================================================================== #
    # Outro — a gentle orbiting row of crates behind the thank-you card
    # ====================================================================== #
    def play_outro(self):
        self.go_3d(phi=66, theta=-58, zoom=0.95, rate=0.05)
        host = slab(0, 0, 6.4, 3.4, color=SLAB, h=0.2)
        self.add(host)
        row = VGroup()
        cols = [WEB, API, DB, GOOD, DOCKER]
        for i, c in enumerate(cols):
            x = -3.0 + i * 1.5
            row.add(crate(x, 0, size=(1.1, 1.1, 1.0 + 0.35 * np.sin(i)),
                          color=c, op=0.26, sw=2.4))
        self.play(LaggedStart(*[GrowFromPoint(b, [b.get_center()[0], 0, 0])
                                for b in row], lag_ratio=0.15), run_time=1.4)
        self.beat(0.4)
        header = Text("Thank you for watching!", font_size=46, color=INK, weight="BOLD")
        line = self._rule_under(header)
        writer = Text("Created by Ptolémé", font_size=28, color=DOCKER)
        writer.move_to([line.get_center()[0], line.get_bottom()[1] - 0.55, 0])
        recap = Text("One box that holds your app, and runs the same everywhere.",
                     font_size=24, color="#B7C0D0")
        recap.next_to(writer, DOWN, buff=0.5)
        if recap.width > 12.4:
            recap.scale_to_fit_width(12.4)
        cardv = VGroup(header, line, writer, recap)
        scrim = RoundedRectangle(width=cardv.width + 1.4, height=cardv.height + 1.1,
                                 corner_radius=0.2, stroke_width=0,
                                 fill_color=BG, fill_opacity=0.9).move_to(cardv)
        self._fix(scrim, cardv)
        self.play(FadeIn(scrim), run_time=0.5)
        self.play(Write(header), Create(line), run_time=1.5)
        self.play(FadeIn(writer, shift=UP * 0.3), run_time=0.9)
        self.play(FadeIn(recap), run_time=0.7)
        self.card_wait(2.4)
        self.stop_orbit()
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.2)

    # ====================================================================== #
    # The whole film
    # ====================================================================== #
    def play_all(self):
        self.play_intro()
        self.scene_problem()
        self.scene_container()
        self.scene_layers()
        self.scene_commands()
        self.scene_network()
        self.scene_vms()
        self.scene_kube()
        self.play_outro()


# =========================================================================== #
# 2D helpers used only by the flat command scene
# =========================================================================== #
def make_check(color=GOOD, sw=7, scale=1.0):
    v = VMobject()
    v.set_points_as_corners([np.array([-0.2, 0.0, 0]), np.array([-0.05, -0.18, 0]),
                             np.array([0.24, 0.22, 0])])
    return v.set_stroke(color=color, width=sw).scale(scale)


def make_x(color=BAD, sw=7, scale=1.0):
    a = Line([-0.16, -0.16, 0], [0.16, 0.16, 0])
    b = Line([-0.16, 0.16, 0], [0.16, -0.16, 0])
    return VGroup(a, b).set_stroke(color=color, width=sw).scale(scale)


def crate_2d(label, color, w=2.4, h=1.05, running=False):
    """A flat 2D box glyph (image / container) for the command lifecycle."""
    body = RoundedRectangle(width=w, height=h, corner_radius=0.1,
                            stroke_color=color, stroke_width=3,
                            fill_color=color, fill_opacity=0.14)
    grp = VGroup(body)
    for x in np.linspace(-w * 0.32, w * 0.32, 5):
        grp.add(Line([body.get_center()[0] + x, body.get_center()[1] - h * 0.26, 0],
                     [body.get_center()[0] + x, body.get_center()[1] + h * 0.26, 0],
                     stroke_color=color, stroke_width=1.6).set_opacity(0.5))
    name = txt(label, fs=18, color=INK, weight="BOLD").move_to(body)
    bgpad = RoundedRectangle(width=name.width + 0.3, height=name.height + 0.12,
                             corner_radius=0.06, stroke_width=0,
                             fill_color=BG, fill_opacity=0.65).move_to(name)
    grp.add(bgpad, name)
    if running:
        dot = Dot(radius=0.06, color=GOOD).move_to(
            [body.get_right()[0] - 0.18, body.get_top()[1] - 0.18, 0])
        grp.add(dot)
    grp.body = body
    return grp


def cmd_row(cmd, desc, color):
    c = txt(cmd, fs=18, color=color, font=MONO, weight="BOLD")
    cbox = RoundedRectangle(width=c.width + 0.3, height=c.height + 0.18,
                            corner_radius=0.08, stroke_color=color, stroke_width=1.6,
                            fill_color=PANEL, fill_opacity=0.9)
    c.move_to(cbox)
    chipm = VGroup(cbox, c)
    d = txt(desc, fs=17, color=MUTED)
    row = VGroup(chipm, d).arrange(RIGHT, buff=0.3)
    return row


# =========================================================================== #
# Thin per-scene classes + the whole film
# =========================================================================== #
class Intro(_DockerBase):
    def construct(self):
        self.play_intro()


class Problem(_DockerBase):
    def construct(self):
        self.scene_problem()


class Container(_DockerBase):
    def construct(self):
        self.scene_container()


class Layers(_DockerBase):
    def construct(self):
        self.scene_layers()


class Commands(_DockerBase):
    def construct(self):
        self.scene_commands()


class Network(_DockerBase):
    def construct(self):
        self.scene_network()


class VMs(_DockerBase):
    def construct(self):
        self.scene_vms()


class Kube(_DockerBase):
    def construct(self):
        self.scene_kube()


class Outro(_DockerBase):
    def construct(self):
        self.play_outro()


class DockerVisually(_DockerBase):
    """The whole ~4.5-minute film, intro card to outro card."""

    def construct(self):
        self.play_all()

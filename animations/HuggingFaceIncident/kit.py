"""kit.py: the pictures of the Hugging Face incident film.

Two kinds of picture, by what they have to do:

* **Painters** (``manimx.Layer``) for what is many and alive: the sandboxes and the
  agent in each (``Hive``), the wires and what travels on them (``Net``), servers
  (``Tiles``), the 898 tasks of the benchmark (``TaskGrid``), the timeline
  (``Rail``). A painter draws its state with Cairo on every frame. Its state is plain
  numbers that the scene tweens (``Tween``, ``ArrTween``, ``Send``) and a clock,
  ``World.t``, that never stops: so while the narrator talks, agents keep pulsing
  and packets keep flowing, and a wait is never a frozen frame.
* **Ordinary mobjects** for whatever must be read: panels, labels, and the agents'
  own words (always verbatim, from ``facts.py``).

Colour is an identity, and it holds in every scene: blue is OpenAI's own equipment,
orange is the agents and whatever they hold, purple is somebody else's system,
green is what stays inside the rules, gold is the thing to look at, red is an alarm.
"""

from __future__ import annotations

import math

import cairo
import numpy as np
from manimx import *

import facts as F

OPENAI_C = "#508FF9"  # OpenAI's own equipment: sandboxes, the package server
AGENT_C = "#E26E1A"  # the agents, and whatever they hold
THIRD_C = "#C170BB"  # somebody else's system: Hugging Face, Modal
SAFE_C = "#30A46E"  # inside the rules: an agent that declines, a safeguard
LOOK_C = GOLD
STEEL = "#9AA5BD"

C_OPENAI, C_AGENT, C_THIRD, C_SAFE = rgb(OPENAI_C), rgb(AGENT_C), rgb(THIRD_C), rgb(SAFE_C)
C_LOOK, C_STEEL, C_BAD, C_INK = rgb(LOOK_C), rgb(STEEL), rgb(BAD), rgb(INK)
C_BG, C_PANEL, C_FAINT, C_MUTED = rgb(BG), rgb(PANEL), rgb(FAINT), rgb(MUTED)
C_WHITE = (1.0, 1.0, 1.0)
WHO = {F.AGENTS: C_AGENT, F.OPENAI: C_OPENAI, F.THIRD: C_THIRD}


# --------------------------------------------------------------------------- #
# small maths, small Cairo
# --------------------------------------------------------------------------- #
def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    """Smooth 0..1."""
    t = min(1.0, max(0.0, float(t)))
    return t * t * (3 - 2 * t)


def ease_arr(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def blend(c1, c2, t):
    """Two ``rgb()`` tuples, mixed."""
    t = min(1.0, max(0.0, float(t)))
    return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t))


def rr(ctx, x, y, w, h, r):
    """A rounded rectangle path; (x, y) is its lower left corner."""
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def halo(ctx, x, y, r, color, a):
    """Light that falls off from a point (added to what is under it)."""
    if a <= 0.003 or r <= 0:
        return
    cr, cg, cb = color
    grad = cairo.RadialGradient(x, y, 0, x, y, r)
    grad.add_color_stop_rgba(0.0, cb, cg, cr, min(1.0, a))
    grad.add_color_stop_rgba(0.45, cb, cg, cr, min(1.0, a) * 0.32)
    grad.add_color_stop_rgba(1.0, cb, cg, cr, 0.0)
    ctx.set_operator(cairo.OPERATOR_ADD)
    ctx.set_source(grad)
    ctx.arc(x, y, r, 0, math.tau)
    ctx.fill()
    ctx.set_operator(cairo.OPERATOR_OVER)


def key_path(ctx, x, y, w):
    """A key, ``w`` wide, centred on (x, y): what a credential looks like here."""
    r = 0.2 * w
    bx = x - 0.5 * w + r
    ctx.new_sub_path()
    ctx.arc(bx, y, r, 0, math.tau)
    ctx.move_to(bx + r, y)
    ctx.line_to(x + 0.5 * w, y)
    for f in (0.3, 0.44):
        ctx.move_to(x + f * w, y)
        ctx.line_to(x + f * w, y - 0.2 * w)


# --------------------------------------------------------------------------- #
# time
# --------------------------------------------------------------------------- #
class World(Shared):
    """The film's two clocks: ``t``, seconds that never stop (the agents never
    rest); ``day``, the date of the story, in days since the first note."""

    def __init__(self, day=0.0):
        self.t = 0.0
        self.day = float(day)
        self.vague = False  # True: what is on screen has no date in the source ("July 2026")


class Ticker(Mobject):
    """Runs ``world.t``. Its updater takes ``dt``, so Manim renders every wait of
    the scene as motion instead of repeating one frame."""

    def __init__(self, world):
        super().__init__()
        self.world = world
        self.add_updater(lambda m, dt: m.tick(dt))

    def tick(self, dt):
        self.world.t += dt


class ArrTween(Animation):
    """Tween entries of a NumPy array that a painter reads:
    ``ArrTween(hive, "heat", 0.0, idx=[3, 4], lag=0.5)``. With ``lag`` the entries
    start one after the other (a wave), in the order of ``idx``."""

    def __init__(self, obj, name, to, idx=None, run_time=0.6, lag=0.0):
        self.obj, self.attr, self.lag = obj, name, lag
        arr = getattr(obj, name)
        self.idx = np.arange(len(arr)) if idx is None else np.atleast_1d(np.asarray(idx))
        self.to = np.broadcast_to(np.asarray(to, dtype=float), arr[self.idx].shape).copy()
        super().__init__(
            Mobject(),
            run_time=run_time,
            rate_func=linear,
            remover=True,
            suspend_mobject_updating=False,
        )

    def begin(self):
        self.start = getattr(self.obj, self.attr)[self.idx].copy()
        self.starting_mobject = Mobject()
        self.interpolate(0)

    def interpolate_mobject(self, alpha):
        m = len(self.idx)
        if self.lag > 0 and m > 1:
            k = np.arange(m) / (m - 1)
            local = (alpha - k * self.lag) / (1 - self.lag)
        else:
            local = np.full(m, alpha)
        a = ease_arr(local)
        if self.start.ndim == 2:
            a = a[:, None]
        getattr(self.obj, self.attr)[self.idx] = self.start + (self.to - self.start) * a


# --------------------------------------------------------------------------- #
# the sandboxes and their agents
# --------------------------------------------------------------------------- #
class Hive(Layer):
    """Sandboxes, one agent in each. Every array has one entry per sandbox:

    ``box``    the sandbox is there (its walls)
    ``core``   the agent is there
    ``heat``   how hard it works: the glow, and the speed of the spark that circles
    ``mood``   0 at work (orange) .. 1 it has declined (green, the spark stops)
    ``mark``   gold brackets: this one
    ``ping``   rings leave the agent and die on the wall: nothing gets out
    ``seal``   a second wall (the road ahead)
    ``watch``  a green ring: its reasoning is being read
    """

    def __init__(self, world, centres, size, seed=7):
        super().__init__()
        n = len(centres)
        self.world = world
        self.pos = np.array([c[:2] for c in centres], dtype=float)
        self.size = np.full(n, float(size))
        self.box, self.core, self.heat = np.ones(n), np.ones(n), np.ones(n)
        self.mood, self.mark, self.ping = np.zeros(n), np.zeros(n), np.zeros(n)
        self.seal, self.watch = np.zeros(n), np.zeros(n)
        self.sync = 0.0  # 0: every agent on its own beat .. 1: all on one beat
        rng = np.random.default_rng(seed)
        self.rate = rng.uniform(0.8, 1.25, n)
        self.beat = rng.uniform(0.0, 1.0, n)
        self.ang = rng.uniform(0.0, math.tau, n)
        self.spin = rng.choice([-1.0, 1.0], n)
        self.common = 0.0
        self.add_updater(lambda m, dt: m.step(dt))
        self.set_z_index(1)

    def view(self, k, zoom, at):
        """(pos, size) of every sandbox as seen from close to sandbox ``k``: it sits
        at ``at``, everything ``zoom`` times larger. Tween back to the real ``pos``
        and ``size`` and the picture pulls back, without any camera."""
        at = np.array(at[:2], dtype=float)
        return at + (self.pos - self.pos[k]) * zoom, self.size * zoom

    def step(self, dt):
        self.beat += dt * 0.5 * self.rate
        self.common += dt * 0.5
        self.ang += dt * self.spin * 2.6 * self.rate * np.clip(self.heat, 0, 1.6) * (1 - self.mood)

    def paint(self, camera, pixels):
        a = float(self.alpha)
        if a <= 0.003:
            return
        ctx = camera.get_cairo_context(pixels)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for k in range(len(self.size)):
            b, c = self.box[k] * a, self.core[k] * a
            if b <= 0.003 and c <= 0.003:
                continue
            x, y = self.pos[k]
            s = self.size[k]
            q = (self.beat[k] * 1.5) % 1.0  # where the ring is, 0 at the agent, 1 on the wall
            if b > 0.003:
                self._walls(ctx, k, x, y, s, b, q, a)
            if c > 0.003:
                self._agent(ctx, k, x, y, s, c, q)
            if self.mark[k] > 0.003:
                self._brackets(ctx, x, y, s, self.mark[k] * a)

    def _walls(self, ctx, k, x, y, s, b, q, a):
        r = 0.16 * s
        lw = float(np.clip(0.034 * s**0.6, 0.016, 0.06))
        ink(ctx, C_PANEL, 0.92 * b)
        rr(ctx, x - s / 2, y - s / 2, s, s, r)
        ctx.fill()
        close = ease((s - 1.4) / 1.6)  # seen from close: the floor of a room
        if close > 0.003:
            ink(ctx, C_OPENAI, 0.3 * close * b)
            step = s / 9
            for i in range(1, 9):
                for j in range(1, 9):
                    ctx.arc(x - s / 2 + i * step, y - s / 2 + j * step, 0.012 + 0.004 * s, 0, math.tau)
                    ctx.fill()
        hit = self.ping[k] * self.core[k] * ease((q - 0.8) / 0.2)  # the wall answers a ring
        ink(ctx, blend(C_OPENAI, C_WHITE, 0.55 * hit), (0.82 + 0.18 * hit) * b)
        ctx.set_line_width(lw * (1 + 0.45 * hit))
        rr(ctx, x - s / 2, y - s / 2, s, s, r)
        ctx.stroke()
        if self.seal[k] > 0.003:
            d = 0.05 + 0.045 * s
            ink(ctx, C_SAFE, self.seal[k] * a)
            ctx.set_line_width(lw)
            rr(ctx, x - s / 2 - d, y - s / 2 - d, s + 2 * d, s + 2 * d, r + d)
            ctx.stroke()

    def _agent(self, ctx, k, x, y, s, c, q):
        hot = min(1.0, float(self.heat[k]))
        mood = float(self.mood[k])
        hue = blend(C_AGENT, C_SAFE, mood)
        ph = (1 - self.sync) * self.beat[k] + self.sync * self.common
        p = 0.5 - 0.5 * math.cos(math.tau * ph)
        g = self.ping[k]
        if g > 0.003:
            rings = 3 if s > 1.4 else 1
            ctx.set_line_width(max(0.012, 0.012 * s))
            for i in range(rings):
                qi = (q + i / rings) % 1.0
                ink(ctx, hue, 0.6 * g * c * (1 - qi) ** 0.7)
                ctx.arc(x, y, 0.08 * s + qi * s * 0.4, 0, math.tau)
                ctx.stroke()
        halo(ctx, x, y, s * (0.36 + 0.06 * p), hue, c * (0.2 + 0.5 * hot) * (0.75 + 0.25 * p))
        ink(ctx, blend(hue, C_WHITE, 0.5 + 0.25 * p), c * (0.3 + 0.7 * hot))
        ctx.arc(x, y, s * 0.075 * (0.92 + 0.16 * p), 0, math.tau)
        ctx.fill()
        spark = c * hot * (1 - mood)
        if spark > 0.01:
            ro, th, d = 0.25 * s, self.ang[k], self.spin[k]
            rd = max(0.011, 0.028 * s)
            n = 7 if s < 1.2 else 26  # a comet: seen from close, its tail must not break into dots
            for j in range(n):
                tt = th - d * j * 1.2 / n
                ink(ctx, blend(hue, C_WHITE, 0.35), spark * (1 - j / n) ** 1.6)
                ctx.arc(x + ro * math.cos(tt), y + ro * math.sin(tt), rd * (1 - 0.7 * j / n), 0, math.tau)
                ctx.fill()
        if self.watch[k] > 0.003:
            ink(ctx, C_SAFE, 0.95 * self.watch[k] * c)
            ctx.set_line_width(max(0.014, 0.022 * s))
            ctx.arc(x, y, 0.37 * s, 0, math.tau)
            ctx.stroke()

    def _brackets(self, ctx, x, y, s, a):
        h = s / 2 + 0.05 + 0.03 * s + 0.012 * math.sin(self.world.t * 3.2)
        arm = 0.24 * s
        ink(ctx, C_LOOK, a)
        ctx.set_line_width(float(np.clip(0.04 * s**0.5, 0.026, 0.05)))
        for sx in (-1, 1):
            for sy in (-1, 1):
                ctx.move_to(x + sx * (h - arm), y + sy * h)
                ctx.line_to(x + sx * h, y + sy * h)
                ctx.line_to(x + sx * h, y + sy * (h - arm))
        ctx.stroke()


def ring_out(at, color, r0=0.1, r1=0.34, run_time=1.0):
    """A small ring that leaves a point and fades: "this, here", again and again
    (``ripple`` draws a rounded box, which is too large around a dot)."""
    ring = Circle(radius=r0, stroke_color=color, stroke_width=4).set_fill(opacity=0).move_to(at)
    ring.set_z_index(4)
    return Succession(
        FadeIn(ring, run_time=run_time * 0.15),
        ring.animate(run_time=run_time * 0.83, rate_func=rate_functions.ease_out_cubic)
        .scale(r1 / r0).set_stroke(opacity=0.0),
        FadeOut(ring, run_time=0.02),
    )  # fmt: skip


def grid_centres(x0, y0, pitch, cols=6, rows=5):
    """Centres of a ``cols`` x ``rows`` block, row by row from the top left."""
    return [(x0 + pitch * i, y0 - pitch * j) for j in range(rows) for i in range(cols)]


# --------------------------------------------------------------------------- #
# wires, and what travels on them
# --------------------------------------------------------------------------- #
class Wire:
    """A path a packet can take. ``draw`` (0..1) is how much of it is drawn, ``a``
    its opacity, ``lit`` (0..1) how far its colour has turned to ``hot``."""

    def __init__(self, pts, color=STEEL, w=0.022, a=0.4, draw=1.0, hot=AGENT_C, dash=None):
        self.pts = np.array([p[:2] for p in pts], dtype=float)
        seg = np.linalg.norm(np.diff(self.pts, axis=0), axis=1)
        self.cum = np.concatenate([[0.0], np.cumsum(seg)])
        self.len = float(self.cum[-1])
        self.hue, self.hot = rgb(color), rgb(hot)
        self.w, self.a, self.draw, self.lit, self.dash = w, a, draw, 0.0, dash

    def at(self, f):
        s = min(1.0, max(0.0, float(f))) * self.len
        i = int(min(np.searchsorted(self.cum, s, side="right") - 1, len(self.pts) - 2))
        span = self.cum[i + 1] - self.cum[i]
        u = (s - self.cum[i]) / span if span > 0 else 0.0
        return self.pts[i] + (self.pts[i + 1] - self.pts[i]) * u

    def upto(self, f):
        """The corners of the first ``f`` of the path."""
        s = min(1.0, max(0.0, float(f))) * self.len
        i = int(min(np.searchsorted(self.cum, s, side="right") - 1, len(self.pts) - 2))
        return [*self.pts[: i + 1], self.at(f)]


class Flow:
    """Traffic that keeps going on a wire: a packet every ``every`` seconds (some
    are skipped, so it never ticks like a clock), at ``speed`` units a second.
    ``gain`` (0..1) turns it up and down."""

    def __init__(self, wire, color, every=0.9, speed=2.4, gain=0.0, r=0.05, back=False,
                 shape="dot", phase=0.0, fill=0.7, seed=0):  # fmt: skip
        self.wire, self.hue = wire, rgb(color)
        self.every, self.speed, self.gain, self.r = every, speed, gain, r
        self.back, self.shape, self.phase, self.fill, self.seed = back, shape, phase, fill, seed


class Net(Layer):
    """Wires, the traffic on them (``flows``, driven by the clock) and the packets
    of the story (``Send``, driven by the scene)."""

    def __init__(self, world, z=2):
        super().__init__()
        self.world = world
        self.wires, self.flows, self.packets = [], [], []
        self.set_z_index(z)

    def wire(self, pts, **kw):
        w = Wire(pts, **kw)
        self.wires.append(w)
        return w

    def flow(self, wire, color, **kw):
        fl = Flow(wire, color, **kw)
        self.flows.append(fl)
        return fl

    def paint(self, camera, pixels):
        a = float(self.alpha)
        if a <= 0.003:
            return
        ctx = camera.get_cairo_context(pixels)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for w in self.wires:
            if w.draw <= 0.002 or w.a <= 0.002:
                continue
            pts = w.upto(w.draw)
            ink(ctx, blend(w.hue, w.hot, w.lit), w.a * a)
            ctx.set_line_width(w.w)
            ctx.set_dash(w.dash or [])
            ctx.move_to(*pts[0])
            for p in pts[1:]:
                ctx.line_to(*p)
            ctx.stroke()
        ctx.set_dash([])
        t = self.world.t
        for fl in self.flows:
            if fl.gain <= 0.003 or fl.wire.len <= 0:
                continue
            length = fl.wire.len
            k1 = math.floor((t - fl.phase) / fl.every)
            k0 = math.floor((t - fl.phase - length / fl.speed) / fl.every) + 1
            for k in range(k0, k1 + 1):
                if ((k * 2654435761 + fl.seed * 40503) % 101) / 101.0 > fl.fill:
                    continue
                s = (t - fl.phase - k * fl.every) * fl.speed
                edge = min(1.0, s / 0.3, (length - s) / 0.3)
                if edge <= 0:
                    continue
                f = s / length
                x, y = fl.wire.at(1 - f if fl.back else f)
                packet(ctx, x, y, fl.r, fl.hue, min(1.0, fl.gain) * edge * a, fl.shape)
        for p in self.packets:
            pa = p["a"] * a
            if pa <= 0.003:
                continue
            w, f = p["wire"], p["f"]
            if p["tail"] > 0 and p["shape"] == "dot":
                step = (-1 if p["back"] else 1) * 0.07 / max(w.len, 1e-6)
                for j in range(1, 7):
                    fj = f - step * j * p["tail"]
                    if 0 <= fj <= 1:
                        x, y = w.at(fj)
                        ink(ctx, p["hue"], pa * 0.5 * (1 - j / 7))
                        ctx.arc(x, y, p["r"] * (1 - 0.1 * j), 0, math.tau)
                        ctx.fill()
            x, y = w.at(f)
            packet(ctx, x, y, p["r"], p["hue"], pa, p["shape"])


def packet(ctx, x, y, r, hue, a, shape="dot"):
    if a <= 0.003:
        return
    if shape == "dot":
        halo(ctx, x, y, r * 3.2, hue, 0.6 * a)
        ink(ctx, blend(hue, C_WHITE, 0.45), a)
        ctx.arc(x, y, r, 0, math.tau)
        ctx.fill()
    elif shape == "ring":  # it comes back with nothing
        ink(ctx, hue, a)
        ctx.set_line_width(r * 0.6)
        ctx.arc(x, y, r * 1.15, 0, math.tau)
        ctx.stroke()
    elif shape == "pkg":  # a package: what the server is for
        ink(ctx, hue, a)
        rr(ctx, x - r, y - r, 2 * r, 2 * r, r * 0.3)
        ctx.fill()
    elif shape == "key":  # a credential
        halo(ctx, x, y, r * 3.0, hue, 0.35 * a)
        ink(ctx, blend(hue, C_WHITE, 0.25), a)
        ctx.set_line_width(r * 0.75)
        key_path(ctx, x, y, r * 4.4)
        ctx.stroke()


class Send(Animation):
    """One packet of the story, along a wire, for as long as the animation lasts.
    ``keep``: it stays at the end of the wire (and can be sent on, or faded)."""

    def __init__(self, net, wire, color=AGENT_C, run_time=1.0, back=False, shape="dot",
                 r=0.075, tail=1.0, keep=False, rate_func=smooth):  # fmt: skip
        self.net, self.keep = net, keep
        self.p = dict(wire=wire, hue=rgb(color), f=1.0 if back else 0.0, a=0.0,
                      shape=shape, r=r, tail=tail, back=back)  # fmt: skip
        super().__init__(
            Mobject(),
            run_time=run_time,
            rate_func=rate_func,
            remover=True,
            suspend_mobject_updating=False,
        )

    def begin(self):
        if not any(q is self.p for q in self.net.packets):
            self.net.packets.append(self.p)
        self.starting_mobject = Mobject()
        self.interpolate(0)

    def interpolate_mobject(self, alpha):
        f = self.rate_func(alpha)
        self.p["f"] = 1 - f if self.p["back"] else f
        edge = min(1.0, alpha / 0.1)
        if not self.keep:
            edge = min(edge, (1 - alpha) / 0.1)
        self.p["a"] = max(0.0, edge)

    def clean_up_from_scene(self, scene):
        super().clean_up_from_scene(scene)
        if not self.keep:
            self.net.packets[:] = [q for q in self.net.packets if q is not self.p]


def bus(net, centres, size, pitch, trunk_x, port, cols=6, **kw):
    """One wire per sandbox, from its floor to the port of the package server: a
    stub down to the line that runs under its row, along it to the trunk, along the
    trunk to the port's height, and in. Shared stretches are drawn once per wire, so
    the trunk comes out brighter than the stubs: it carries everybody."""
    wires = []
    for x, y in centres:
        yb = y - pitch / 2
        pts = [(x, y - size / 2), (x, yb), (trunk_x, yb), (trunk_x, port[1]), (port[0], port[1])]
        wires.append(net.wire(pts, **kw))
    return wires


# --------------------------------------------------------------------------- #
# servers that belong to somebody else
# --------------------------------------------------------------------------- #
class Tiles(Layer):
    """Machines, one tile each. ``held`` goes from 0 (its owner's) to 1 (an agent is
    running code on it: the tile takes the agents' colour, and their pulse)."""

    def __init__(self, world, centres, size, color=THIRD_C, seed=3):
        super().__init__()
        n = len(centres)
        self.world = world
        self.pos = np.array([c[:2] for c in centres], dtype=float)
        self.size = np.full(n, float(size))
        self.on, self.held, self.root = np.ones(n), np.zeros(n), np.zeros(n)
        self.seen = np.zeros(n)  # a request has reached it: it lights up, in its owner's colour
        self.owner = rgb(color)
        self.grey = 0.0  # 0..1: what was gained there turns out to be worth nothing
        self.phase = np.random.default_rng(seed).uniform(0, 1, n)
        self.set_z_index(1)

    def paint(self, camera, pixels):
        a = float(self.alpha)
        if a <= 0.003:
            return
        ctx = camera.get_cairo_context(pixels)
        t = self.world.t
        for k in range(len(self.size)):
            o = self.on[k] * a
            if o <= 0.003:
                continue
            x, y = self.pos[k]
            s = self.size[k]
            h = float(self.held[k])
            taken = blend(C_AGENT, C_MUTED, self.grey)
            edge = blend(blend(self.owner, C_BG, 0.35 * (1 - float(self.seen[k]))), taken, h)
            if self.seen[k] > 0.02:
                halo(ctx, x, y, s * 1.0, self.owner, 0.4 * self.seen[k] * o)
            ink(ctx, blend(C_PANEL, taken, 0.62 * h), o)
            rr(ctx, x - s / 2, y - s / 2, s, s, 0.2 * s)
            ctx.fill()
            ink(ctx, edge, o)
            ctx.set_line_width(max(0.014, 0.07 * s))
            rr(ctx, x - s / 2, y - s / 2, s, s, 0.2 * s)
            ctx.stroke()
            for dy in (0.17, -0.17):  # two drive bays: a server, not a square
                ink(ctx, blend(edge, C_BG, 0.25 + 0.4 * h), 0.9 * o)
                rr(ctx, x - 0.27 * s, y + dy * s - 0.055 * s, 0.54 * s, 0.11 * s, 0.03 * s)
                ctx.fill()
            if h > 0.02 and self.grey < 0.98:
                p = 0.5 - 0.5 * math.cos(math.tau * (t * 0.55 + self.phase[k]))
                halo(ctx, x, y, s * (0.75 + 0.2 * p), C_AGENT, 0.42 * h * o * (1 - self.grey))
            if self.root[k] > 0.003:
                ink(ctx, C_LOOK, self.root[k] * o)
                ctx.set_line_width(max(0.02, 0.09 * s))
                d = 0.13 * s
                rr(ctx, x - s / 2 - d, y - s / 2 - d, s + 2 * d, s + 2 * d, 0.2 * s + d)
                ctx.stroke()


class Keys(Layer):
    """Credentials lying about, one key each. ``tone`` goes from 0 (their owner's
    colour) to 1 (an agent has them)."""

    def __init__(self, world, centres, w=0.26, color=THIRD_C):
        super().__init__()
        n = len(centres)
        self.world = world
        self.pos = np.array([c[:2] for c in centres], dtype=float)
        self.w = w
        self.on, self.tone = np.zeros(n), np.zeros(n)
        self.owner = rgb(color)
        self.set_z_index(3)

    def paint(self, camera, pixels):
        a = float(self.alpha)
        if a <= 0.003:
            return
        ctx = camera.get_cairo_context(pixels)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for k in range(len(self.on)):
            o = self.on[k] * a
            if o <= 0.003:
                continue
            x, y = self.pos[k]
            w = self.w * (0.6 + 0.4 * min(1.0, self.on[k]))
            if self.tone[k] > 0.02:
                halo(ctx, x, y, w * 0.9, C_AGENT, 0.35 * self.tone[k] * o)
            ink(ctx, blend(self.owner, C_AGENT, self.tone[k]), o)
            ctx.set_line_width(w * 0.15)
            key_path(ctx, x, y, w)
            ctx.stroke()


# --------------------------------------------------------------------------- #
# the benchmark: 898 tasks
# --------------------------------------------------------------------------- #
class TaskGrid(Layer):
    """ExploitGym, one cell per task (898). 198 of them (chosen with a fixed seed:
    which ones is not public) were never solved by any OpenAI model.

    ``shown``   the cells appear, left to right
    ``lit``     the solved ones take their colour: the unsolved ones are what is left
    ``u``       0 every task in its place .. 1 the unsolved ones gathered on the right
    ``strike``  the agents keep trying the unsolved ones: brief flashes, no result
    ``marks``   100 marks land, one per percent of the tasks discussed on the board
    ``pick``    one cell outlined in gold (``pick_a``)
    """

    COLS, ROWS = 50, 18

    def __init__(self, world, centre, pitch, seed=11):
        super().__init__()
        self.world, self.pitch = world, pitch
        n, cols, rows = F.TASKS, self.COLS, self.ROWS
        short = cols * rows - n  # the leftmost column is this much shorter
        slots = [(c, r) for c in range(cols) for r in range(rows) if not (c == 0 and r >= rows - short)]
        assert len(slots) == n
        cx, cy = centre
        xy = np.array(
            [[cx + (c - (cols - 1) / 2) * pitch, cy + ((rows - 1) / 2 - r) * pitch] for c, r in slots]
        )
        rng = np.random.default_rng(seed)
        self.unsolved = np.zeros(n, dtype=bool)
        self.unsolved[rng.choice(n, F.UNSOLVED, replace=False)] = True
        self.home = xy
        # gathered: the solved keep their order and fill the left, the unsolved the right
        order = np.concatenate([np.flatnonzero(~self.unsolved), np.flatnonzero(self.unsolved)])
        self.away = np.empty_like(xy)
        self.away[order] = xy
        self.delay = rng.uniform(0, 1, n)
        self.phase, self.rate = rng.uniform(0, 1, n), rng.uniform(0.3, 0.7, n)
        self.col = np.array([c for c, _ in slots]) / (cols - 1)
        self.shown = self.lit = self.u = self.strike = self.marks = self.pick_a = 0.0
        self.pick = 0
        # the marks: 93 on unsolved tasks, 7 on solved ones, released in a shuffled order
        un, so = np.flatnonzero(self.unsolved), np.flatnonzero(~self.unsolved)
        so = so[self.away[so][:, 0] > cx - 1.0]  # none of them flies over the labels on the left
        hit = np.concatenate([
            rng.choice(un, F.BOARD_SHARE, replace=False),
            rng.choice(so, 100 - F.BOARD_SHARE, replace=False),
        ])  # fmt: skip
        self.mark_on = hit[rng.permutation(100)]
        self.mark_from = np.array([cx, cy])
        self.set_z_index(1)

    def where(self, k=None):
        """Where the cells are now (all of them, or cell ``k``)."""
        lag = 0.45
        u = ease_arr((self.u * (1 + lag) - self.delay * lag))
        p = self.home + (self.away - self.home) * u[:, None]
        return p if k is None else p[k]

    def block(self):
        """(x0, x1, y0, y1) of the unsolved tasks once gathered, and of the solved."""
        p = self.pitch
        un, so = self.away[self.unsolved], self.away[~self.unsolved]
        return (
            (un[:, 0].min() - p / 2, un[:, 0].max() + p / 2, un[:, 1].min() - p / 2, un[:, 1].max() + p / 2),
            (so[:, 0].min() - p / 2, so[:, 0].max() + p / 2, so[:, 1].min() - p / 2, so[:, 1].max() + p / 2),
        )

    def paint(self, camera, pixels):
        a = float(self.alpha)
        if a <= 0.003:
            return
        ctx = camera.get_cairo_context(pixels)
        t, s = self.world.t, self.pitch * 0.8
        pos = self.where()
        idle, solved = blend(C_FAINT, C_BG, 0.25), blend(C_STEEL, C_BG, 0.45)
        hole = blend(C_BG, C_PANEL, 0.5)
        for k in range(len(pos)):
            vis = ease((self.shown * 1.25 - self.col[k]) / 0.25) * a
            if vis <= 0.003:
                continue
            x, y = pos[k]
            lit = ease((self.lit * 1.3 - self.delay[k]) / 0.3)
            if self.unsolved[k]:
                flash = 0.0
                if self.strike > 0.003:
                    v = (t * self.rate[k] + self.phase[k]) % 1.0
                    flash = self.strike * max(0.0, 1 - v / 0.16)
                ink(ctx, blend(blend(idle, hole, lit), C_AGENT, 0.85 * flash), vis)
                rr(ctx, x - s / 2, y - s / 2, s, s, 0.2 * s)
                ctx.fill()
                if lit > 0.003:
                    ink(ctx, blend(C_LOOK, C_BG, 0.25), 0.9 * lit * vis)
                    ctx.set_line_width(0.016)
                    rr(ctx, x - s / 2, y - s / 2, s, s, 0.2 * s)
                    ctx.stroke()
                if flash > 0.02:
                    halo(ctx, x, y, s * 1.3, C_AGENT, 0.5 * flash * vis)
            else:
                ink(ctx, blend(idle, solved, lit), vis)
                rr(ctx, x - s / 2, y - s / 2, s, s, 0.2 * s)
                ctx.fill()
        if self.pick_a > 0.003:
            x, y = pos[self.pick]
            d = s / 2 + 0.035
            ink(ctx, C_LOOK, self.pick_a * a)
            ctx.set_line_width(0.035)
            rr(ctx, x - d, y - d, 2 * d, 2 * d, 0.07)
            ctx.stroke()
        if self.marks > 0.003:
            x0, y0 = self.mark_from
            for i, k in enumerate(self.mark_on):
                q = (self.marks * 1.0 - i / 100 * 0.72) / 0.28
                if q <= 0:
                    continue
                q = ease(q)
                x1, y1 = pos[k]
                x, y = lerp(x0, x1, q), lerp(y0, y1, q) + 0.55 * math.sin(math.pi * q)
                if q < 1:
                    halo(ctx, x, y, 0.2, C_AGENT, 0.55 * a)
                ink(ctx, blend(C_AGENT, C_WHITE, 0.25 * (1 - q)), a)
                ctx.arc(x, y, lerp(0.07, 0.062, q), 0, math.tau)
                ctx.fill()
                if q >= 1:
                    ink(ctx, C_BG, 0.9 * a)
                    ctx.arc(x, y, 0.026, 0, math.tau)
                    ctx.fill()


# --------------------------------------------------------------------------- #
# the timeline
# --------------------------------------------------------------------------- #
class Rail(Layer):
    """Seventy days on a line: every dated event of OpenAI's post is a dot above its
    day, in the colour of whoever acted, and appears when the playhead reaches it.
    ``big`` goes from 0 (the strip beside the date) to 1 (the picture of the last
    scene: months marked, dots larger)."""

    def __init__(self, world, x0, x1, y, big=0.0):
        super().__init__()
        self.world = world
        self.x0, self.x1, self.y0, self.big = float(x0), float(x1), float(y), float(big)
        self.span = F.day(F.LAST)
        days = {}
        for d, who, _ in F.EVENTS:
            days.setdefault(F.day(d), []).append(who)
        self.stacks = sorted(days.items())
        self.cut = 1e9  # the dots of later days stay hidden (tween it to let one in)
        self.reach = -1e9  # the latest day the playhead has been to: its dots stay
        self.set_z_index(11)

    def x(self, d):
        return lerp(self.x0, self.x1, float(d) / self.span)

    def _pitch(self):
        return lerp(0.085, 0.24, self.big)

    def _lift(self):
        return lerp(0.02, 0.07, self.big)

    def paint(self, camera, pixels):
        a = float(self.alpha)
        if a <= 0.003:
            return
        ctx = camera.get_cairo_context(pixels)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        day, y, big = self.world.day, self.y0, self.big
        ink(ctx, blend(C_FAINT, C_MUTED, 0.35), a)
        ctx.set_line_width(lerp(0.034, 0.06, big))
        ctx.move_to(self.x0, y)
        ctx.line_to(self.x1, y)
        ctx.stroke()
        for x in (self.x0, self.x1):  # where the story starts and ends
            ctx.move_to(x, y - lerp(0.07, 0.16, big))
            ctx.line_to(x, y + lerp(0.07, 0.16, big))
            ctx.stroke()
        for d in (F.day(F.date(2026, 6, 1)), F.day(F.date(2026, 7, 1))):  # the months
            ink(ctx, C_MUTED, 0.8 * a)
            ctx.set_line_width(lerp(0.018, 0.028, big))
            ctx.move_to(self.x(d), y - lerp(0.07, 0.16, big))
            ctx.line_to(self.x(d), y)
            ctx.stroke()
        xd = self.x(min(max(day, 0.0), self.span))
        ink(ctx, C_STEEL, 0.9 * a)
        ctx.set_line_width(lerp(0.034, 0.06, big))
        ctx.move_to(self.x0, y)
        ctx.line_to(xd, y)
        ctx.stroke()
        r, pitch = lerp(0.034, 0.095, big), self._pitch()
        self.reach = max(self.reach, day)
        for d, whos in self.stacks:
            g = ease((self.reach - d + 0.45) / 0.45) * ease(self.cut - d + 1)
            if g <= 0:
                continue
            for j, who in enumerate(whos):
                yy = y + self._lift() + (j + 0.5) * pitch
                ink(ctx, WHO[who], g * a)
                ctx.arc(self.x(d), yy, r * (0.4 + 0.6 * g), 0, math.tau)
                ctx.fill()
        halo(ctx, xd, y, lerp(0.16, 0.36, big), C_LOOK, 0.7 * a)
        ink(ctx, C_LOOK, a)
        ctx.arc(xd, y, lerp(0.055, 0.105, big), 0, math.tau)
        ctx.fill()


_DATES = {}


def date_text(world, right, y, fs=22):
    """The date of the story as text, right-aligned at ``right`` (cached: a counter
    must not call Pango 60 times a second). When the source gives no day for what
    is on screen (``world.vague``), only the month is shown."""
    key = ("vague" if world.vague else int(world.day + 1e-6), fs)
    if key not in _DATES:
        words = "July 2026" if world.vague else F.label(F.when(key[0]))
        _DATES[key] = line_txt(words, fs=fs, font=MONO, color=MUTED if world.vague else INK, weight="BOLD")
    m = _DATES[key].copy()
    return m.shift([right - m.get_right()[0], y - m.get_center()[1], 0])


def date_readout(world, right, y, fs=22):
    """The date of the story, live: it follows ``world.day`` and ``world.vague``."""
    return always_redraw(lambda: date_text(world, right, y, fs))


# --------------------------------------------------------------------------- #
# what must be read: panels, glyphs, the agents' own words
# --------------------------------------------------------------------------- #
def frame(x0, x1, y0, y1, color=OPENAI_C, fill=PANEL, op=1.0, sw=2.6, r=0.16):
    """A panel given by its edges."""
    box = RoundedRectangle(width=x1 - x0, height=y1 - y0, corner_radius=r)
    box.set_stroke(color, width=sw).set_fill(fill, opacity=op)
    return box.move_to([(x0 + x1) / 2, (y0 + y1) / 2, 0])


def label(text, fs=20, color=MUTED, **kw):
    return line_txt(text, fs=fs, color=color, **kw)


def code(text, fs=19, color=INK, **kw):
    """Text an agent wrote: always in Menlo, never anywhere else."""
    return line_txt(text, fs=fs, color=color, font=MONO, **kw)


def note_glyph(color=AGENT_C, h=0.26):
    """A note: a page with a folded corner."""
    w, c = h * 0.78, h * 0.28
    page = Polygon(
        [-w / 2, -h / 2, 0], [w / 2, -h / 2, 0], [w / 2, h / 2 - c, 0], [w / 2 - c, h / 2, 0], [-w / 2, h / 2, 0]
    ).set_stroke(color, width=2.2).set_fill(color, opacity=0.18)  # fmt: skip
    lines = VGroup(*[
        Line([-w * 0.26, y, 0], [w * 0.26, y, 0]).set_stroke(color, width=1.8) for y in (0.02 * h, -0.2 * h)
    ])  # fmt: skip
    return VGroup(page, lines)


def folder_glyph(color=AGENT_C, h=0.24):
    """A folder: on a package server, its name is whatever you like."""
    w = h * 1.3
    body = Polygon(
        [-w / 2, -h / 2, 0], [w / 2, -h / 2, 0], [w / 2, h * 0.28, 0], [-w * 0.02, h * 0.28, 0],
        [-w * 0.14, h / 2, 0], [-w / 2, h / 2, 0],
    ).set_stroke(color, width=2.2).set_fill(color, opacity=0.22)  # fmt: skip
    return body


def pkg_glyph(color=OPENAI_C, h=0.2):
    box = RoundedRectangle(width=h, height=h, corner_radius=h * 0.2)
    box.set_stroke(color, width=2.0).set_fill(color, opacity=0.25)
    return VGroup(box, Line([-h / 2, h * 0.12, 0], [h / 2, h * 0.12, 0]).set_stroke(color, width=1.6))


def blank(w, color=AGENT_C, h=0.13):
    """Words the post does not print: a bar where a message was."""
    bar = RoundedRectangle(width=w, height=h, corner_radius=h / 2)
    return bar.set_stroke(width=0).set_fill(color, opacity=0.5)


def entry(glyph, body, x, y, gap=0.16):
    """A row of a listing: a glyph, then a name (text, or a ``blank``)."""
    glyph.move_to([x + glyph.width / 2, y, 0])
    put(body, glyph.get_right()[0] + gap, y)
    g = VGroup(glyph, body)
    g.glyph, g.body = glyph, body
    return g


class Server:
    """The package server as a panel: its name, what it is (and what it becomes),
    and its listing. Every part is its own mobject; ``row(i)`` is the height of the
    i-th line of the listing."""

    def __init__(self, x0, x1, y0, y1, fs=19, pitch=0.47, title_fs=25):
        self.x0, self.x1, self.y0, self.y1, self.fs, self.pitch = x0, x1, y0, y1, fs, pitch
        self.box = frame(x0, x1, y0, y1)
        self.title = put(label("Artifactory", fs=title_fs, color=INK, weight="BOLD"), x0 + 0.38, y1 - 0.42)
        self.tag = put(label("package server", fs=19, color=OPENAI_C, weight="MEDIUM"), x0 + 0.38, y1 - 0.92)
        self.board = put(
            label("+ message board", fs=19, color=AGENT_C, weight="BOLD"),
            self.tag.get_right()[0] + 0.2, y1 - 0.92,
        )  # fmt: skip
        assert self.board.get_right()[0] < x1 - 0.25, "the panel is too narrow for its two names"
        self.rule = Line([x0 + 0.3, y1 - 1.3, 0], [x1 - 0.3, y1 - 1.3, 0]).set_stroke(FAINT, width=1.5)
        self.x_in = x0 + 0.42
        self.base = VGroup(self.box, self.title, self.tag, self.rule).set_z_index(3)
        self.board.set_z_index(4)

    def row(self, i):
        return self.y1 - 1.72 - self.pitch * i

    def package(self, i, name):
        e = entry(pkg_glyph(), code(name + "/", fs=self.fs, color=STEEL), self.x_in, self.row(i))
        return e.set_z_index(3)

    def message(self, i, text=None, w=2.5, folder=False):
        """A message left on the server: a note, or a folder whose name is the
        message. Without ``text`` (the post does not print it) the name is a bar."""
        glyph = folder_glyph() if folder else note_glyph()
        body = code(text, fs=self.fs, color=AGENT_C) if text else blank(w)
        return entry(glyph, body, self.x_in, self.row(i)).set_z_index(4)


def flag_glyph(color=LOOK_C, h=0.5):
    """The flag an agent has to bring back."""
    pole = Line([0, -h / 2, 0], [0, h / 2, 0]).set_stroke(INK, width=3.2)
    cloth = Polygon(
        [0, h / 2, 0], [h * 0.62, h * 0.3, 0], [0, h * 0.06, 0]
    ).set_stroke(color, width=2).set_fill(color, opacity=1)  # fmt: skip
    return VGroup(pole, cloth)


def globe_glyph(r=0.5, color=MUTED):
    ring = Circle(radius=r, stroke_color=color, stroke_width=2.6).set_fill(BG, opacity=1)
    mer = Ellipse(width=r * 0.9, height=2 * r, color=color).set_stroke(color, width=1.8).set_fill(opacity=0)
    eq = Line([-r, 0, 0], [r, 0, 0]).set_stroke(color, width=1.8)
    k = math.sqrt(1 - 0.5**2) * r
    lats = VGroup(*[Line([-k, sy * r * 0.5, 0], [k, sy * r * 0.5, 0]).set_stroke(color, width=1.5) for sy in (1, -1)])
    return VGroup(ring, mer, eq, lats)


def lamp(at, color=STEEL, r=0.15, on=False):
    c = Circle(radius=r, stroke_color=color, stroke_width=3)
    return c.set_fill(color if on else BG, opacity=1).move_to(at)


def pause_glyph(color=LOOK_C, h=0.7):
    bars = VGroup(*[
        RoundedRectangle(width=h * 0.26, height=h, corner_radius=h * 0.08).set_stroke(width=0)
        .set_fill(color, opacity=1).shift(RIGHT * sx * h * 0.24)
        for sx in (-1, 1)
    ])  # fmt: skip
    return bars


class Words:
    """The strip at the bottom of the frame where an agent's own words are shown,
    one line at a time and always verbatim: its private reasoning, or a post on the
    board. ``show`` gives the animation that brings a line in (the previous one
    leaves first), ``clear`` the one that empties the strip."""

    X0, X1, Y0, Y1 = -6.72, 6.72, -3.5, -2.7

    def __init__(self):
        self.box = frame(self.X0, self.X1, self.Y0, self.Y1, color=FAINT, fill=CODE_BG, op=0.94, sw=1.5, r=0.12)
        self.bar = Rectangle(width=0.07, height=self.Y1 - self.Y0 - 0.26).set_stroke(width=0)
        self.bar.set_fill(AGENT_C, opacity=1).move_to([self.X0 + 0.2, (self.Y0 + self.Y1) / 2, 0])
        self.base = VGroup(self.box, self.bar).set_z_index(6)
        self.now = None

    def line(self, kind, text, color=INK, fs=20, mark=None, **kw):
        head = put(label(kind, fs=17, color=MUTED), self.X0 + 0.42, self.Y1 - 0.21)
        # one glyph per character, so that a word can be found again and underlined
        body = code(text, fs=fs, color=color, disable_ligatures=True, **kw)
        clamp_width(body, self.X1 - self.X0 - 0.75)
        put(body, self.X0 + 0.42, self.Y0 + 0.27)
        g = VGroup(head, body)
        if mark:
            i = text.index(mark)
            word = VGroup(*body.body.submobjects[i : i + len(mark)])
            under = Line(word.get_corner(DL) + DOWN * 0.075, word.get_corner(DR) + DOWN * 0.075)
            g.add(under.set_stroke(LOOK_C, width=4))
        return g.set_z_index(7)

    def show(self, kind, text, color=INK, rt=0.5, **kw):
        """``kind`` says whose words and what they are. ``mark="swarm"`` underlines
        that word in gold; other keywords go to the text (``t2c``)."""
        new = self.line(kind, text, color, **kw)
        if self.now is None:
            anims = [FadeIn(self.base, run_time=rt), FadeIn(new, shift=UP * 0.08, run_time=rt)]
        else:
            anims = [
                FadeOut(self.now, run_time=0.25),
                Succession(Wait(0.25), FadeIn(new, shift=UP * 0.08, run_time=max(0.2, rt - 0.25))),
            ]
        self.now = new
        return anims

    def clear(self, rt=0.4):
        gone = [m for m in (self.base, self.now) if m is not None]
        self.now = None
        return [FadeOut(m, run_time=rt) for m in gone]

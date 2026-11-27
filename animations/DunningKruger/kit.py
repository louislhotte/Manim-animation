"""kit.py: the pictures of the Dunning-Kruger film.

Two kinds of picture, by what they have to do:

* **Painters** (``manimx.Layer``) for what is many and alive: the dark field and the
  light in it (``FogMap``), the darkness over a chess board (``Spot``). A painter
  draws its state with Cairo on every frame; its state is plain numbers that the
  scene tweens, and a clock that never stops (``World.t``, run by ``Ticker``), so
  the dots twinkle and the fence marches while the narrator talks.
* **Ordinary mobjects** for whatever has a face or must be read: the one who learns
  (``Buddy``, a face drawn from ten numbers, so that a mood is a tween), the chess
  board, the two gauges, the chart.

Colour is an identity, and it holds in every scene: **gold is what you believe**
(the plan, the fence, "feels like"), **blue is what is true** (what is really
known), red is the danger you did not see.
"""

from __future__ import annotations

import math

import cairo
import numpy as np
from manimx import *

import model as M

FELT_C = GOLD  # what you believe: the plan, the fence, "it feels like"
REAL_C = "#4F8FF7"  # what is true: what the light really reaches
THREAT_C = BAD  # the danger you could not see
FRIEND_C = MINT  # somebody else's light
NIGHT = "#06080D"  # the dark field
WARM = "#FFE0A0"  # the light, and the one who carries it
RIM = "#E2AE5A"
EYE = "#1B1E27"
BLUSH = "#FF8E7A"

C_FELT, C_REAL, C_THREAT, C_FRIEND = rgb(FELT_C), rgb(REAL_C), rgb(THREAT_C), rgb(FRIEND_C)
C_NIGHT, C_WARM, C_RIM, C_EYE = rgb(NIGHT), rgb(WARM), rgb(RIM), rgb(EYE)
C_MUTED, C_FAINT, C_INK = rgb(MUTED), rgb(FAINT), rgb(INK)
C_WHITE = (1.0, 1.0, 1.0)
EDGE_PAD = 0.034  # the fence and the true edge are drawn this far outside the last dot


# --------------------------------------------------------------------------- #
# small maths, small Cairo
# --------------------------------------------------------------------------- #
def ease(t):
    """Smooth 0..1."""
    t = min(1.0, max(0.0, float(t)))
    return t * t * (3 - 2 * t)


def blend(c1, c2, t):
    """Two ``rgb()`` tuples, mixed."""
    t = min(1.0, max(0.0, float(t)))
    return tuple(a + (b - a) * t for a, b in zip(c1, c2, strict=True))


def rr(ctx, x, y, w, h, r):
    """A rounded rectangle path; (x, y) is its lower left corner."""
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def lamp(ctx, x, y, r, color, a, stops=((0.0, 1.0), (0.45, 0.32), (1.0, 0.0))):
    """Light that falls off from a point, added to what is under it. ``stops`` are
    (distance 0..1, share of ``a``); Cairo sees Manim's frame as BGRA, hence the order."""
    if a <= 0.003 or r <= 0:
        return
    cr, cg, cb = color
    grad = cairo.RadialGradient(x, y, 0, x, y, r)
    for off, k in stops:
        grad.add_color_stop_rgba(off, cb, cg, cr, min(1.0, a * k))
    ctx.set_operator(cairo.OPERATOR_ADD)
    ctx.set_source(grad)
    ctx.arc(x, y, r, 0, math.tau)
    ctx.fill()
    ctx.set_operator(cairo.OPERATOR_OVER)


# --------------------------------------------------------------------------- #
# time
# --------------------------------------------------------------------------- #
class World(Shared):
    """The film's clock: seconds that never stop."""

    def __init__(self):
        self.t = 0.0


class Ticker(Mobject):
    """Runs ``world.t``. Its updater takes ``dt``, so Manim renders every wait of the
    scene as motion instead of repeating one frame."""

    def __init__(self, world):
        super().__init__()
        self.world = world
        self.add_updater(lambda m, dt: m.tick(dt))

    def tick(self, dt):
        self.world.t += dt


# --------------------------------------------------------------------------- #
# the dark field and the light in it
# --------------------------------------------------------------------------- #
class FogMap(Layer):
    """Everything there is to know about a subject (dots in a disc), and the part
    one light reaches. Plain numbers, tweened by the scene:

    ``know``     radius of the light, 0..1 of the field: inside it the dots are known (blue)
    ``sight``    0..1: the fence is drawn, and the dots between the light and the
                 fence, which you know you have not learned (hollow, gold)
    ``wall``     0..1: the fence alone (``None``: it comes and goes with ``sight``)
    ``fog``      0..1: the fog is lifted *for the viewer*: the dots nobody on the map
                 can see, and the true edge of the field
    ``ping``     0..1: a ring leaves the fence for the true edge and fades: all that is missing
    ``flash``    0..1: the edge lights up: the fence has reached it
    ``tint``     0..1: somebody else's light is seen on the field (it changes nothing else:
                 what moves the fence is ``know``)
    ``guess``    radius of a light somebody *imagines* here (gold, dashed), ``guess_a`` its opacity
    ``mark``     0..1: gold brackets, "this one"
    ``orb``      0..1: the one who carries the light is drawn
    ``R``        radius of the whole field in frame units (tween it: the picture pulls back)
    ``cx, cy``   its centre

    ``counts()`` reads the picture: dots lit, dots in sight, dots in all.
    """

    def __init__(self, world, at, R, n=M.N_DOTS, seed=7, window=None, dot=0.034):
        super().__init__()
        self.world = world
        self.cx, self.cy, self.R = float(at[0]), float(at[1]), float(R)
        self.know = 0.0
        self.sight = 0.0
        self.wall = None
        self.fog = 0.0
        self.ping = 0.0
        self.flash = 0.0
        self.tint = 0.0
        self.guess = 0.0
        self.guess_a = 0.0
        self.mark = 0.0
        self.orb = 1.0
        self.window = window  # (x0, y0, x1, y1): the field is seen through it
        self.dot = dot
        self.num = n
        self.rad, self.ang = M.scatter(n, seed)
        rng = np.random.default_rng(seed + 100)
        self.phase = rng.uniform(0, math.tau, n)
        self.rate = rng.uniform(0.7, 1.9, n)
        self.t_lit = np.full(n, -1e9)  # when each dot came into the light (it flashes)
        self.t_seen = np.full(n, -1e9)  # ... and into sight
        self.set_z_index(1)

    # ---- what the picture says ------------------------------------------------ #
    def edge(self):
        """How far the learner can tell the field goes (0..1)."""
        return float(M.horizon(max(0.0, self.know)))

    def fence_r(self):
        """Where the fence is drawn, in frame units: just outside the last dot in sight."""
        return (self.edge() + EDGE_PAD) * self.R

    def counts(self):
        """(lit, in sight, in all), read off the dots."""
        lit = int((self.rad < self.know).sum())
        return lit, max(lit, int((self.rad < self.edge()).sum())), self.num

    def spot_of(self, i):
        """Where dot ``i`` is, in frame units."""
        return np.array([
            self.cx + self.R * self.rad[i] * math.cos(self.ang[i]),
            self.cy + self.R * self.rad[i] * math.sin(self.ang[i]),
            0.0,
        ])  # fmt: skip

    def glimpsed(self):
        """The dots in sight that are not known."""
        return np.flatnonzero((self.rad < self.edge()) & (self.rad >= self.know))

    def calm(self):
        """Whatever is lit or in sight now has always been: no flash on the next frame."""
        self.t_lit[self.rad < self.know] = -1e7
        self.t_seen[self.rad < self.edge()] = -1e7
        return self

    # ---- the picture ---------------------------------------------------------------- #
    def paint(self, camera, pixels):
        a = float(self.alpha)
        if a <= 0.003:
            return
        ctx = camera.get_cairo_context(pixels)
        t = self.world.t
        cx, cy, R = self.cx, self.cy, self.R
        z = (R / 2.5) ** 0.55  # how much bigger things are drawn from close
        if self.window is not None:
            x0, y0, x1, y1 = self.window
            rr(ctx, x0, y0, x1 - x0, y1 - y0, 0.2)
            ink(ctx, C_NIGHT, a)
            ctx.fill_preserve()
            ctx.clip()
        know, e, fr = max(0.0, self.know), self.edge(), self.fence_r()
        sight, fog = float(self.sight), float(self.fog)
        wall = sight if self.wall is None else float(self.wall)

        if wall > 0.003:  # the field as the learner pictures it
            ink(ctx, C_FELT, 0.05 * wall * a)
            ctx.arc(cx, cy, fr, 0, math.tau)
            ctx.fill()
        if self.tint > 0.003:  # somebody else's light falls on the whole field
            lamp(ctx, cx, cy, R * 1.12, C_FRIEND, 0.2 * float(self.tint) * a,
                 stops=((0.0, 0.7), (0.8, 0.6), (1.0, 0.0)))  # fmt: skip
        if know > 0.002:  # the light
            lamp(ctx, cx, cy, know * R * 1.14, C_WARM, 0.25 * a,
                 stops=((0.0, 1.0), (0.7, 0.62), (0.9, 0.36), (1.0, 0.0)))  # fmt: skip

        xs = cx + R * self.rad * np.cos(self.ang)
        ys = cy + R * self.rad * np.sin(self.ang)
        s = self.dot * z
        if self.window is not None:
            x0, y0, x1, y1 = self.window
            inside = (xs > x0 - s) & (xs < x1 + s) & (ys > y0 - s) & (ys < y1 + s)
        else:
            inside = np.ones(self.num, dtype=bool)
        lit = self.rad < know
        seen = (self.rad < e) & ~lit
        self.t_lit[lit & (self.t_lit < -1e8)] = t
        self.t_lit[~lit] = -1e9
        self.t_seen[(seen | lit) & (self.t_seen < -1e8)] = t
        self.t_seen[~(seen | lit)] = -1e9
        f_lit = np.exp(-(t - self.t_lit) / 0.5)
        f_seen = np.exp(-(t - self.t_seen) / 0.4)
        tw = 0.5 + 0.5 * np.sin(t * self.rate + self.phase)

        if fog > 0.003:  # what nobody on the map can see
            ink(ctx, C_MUTED, 0.5 * fog * a)
            for i in np.flatnonzero(~lit & ~seen & inside):
                ctx.new_sub_path()
                ctx.arc(xs[i], ys[i], s * (0.7 + 0.16 * tw[i]), 0, math.tau)
            ctx.fill()
        if sight > 0.003:  # what you know you have not learned
            ctx.set_line_width(s * 0.5)
            idx = np.flatnonzero(seen & inside)
            still = idx[f_seen[idx] < 0.02]
            ink(ctx, C_FELT, 0.85 * sight * a)
            for i in still:
                ctx.new_sub_path()
                ctx.arc(xs[i], ys[i], s * 0.95, 0, math.tau)
            ctx.stroke()
            for i in idx[f_seen[idx] >= 0.02]:
                f = float(f_seen[i])
                ink(ctx, blend(C_FELT, C_WHITE, 0.5 * f), (0.85 + 0.15 * f) * sight * a)
                ctx.new_sub_path()
                ctx.arc(xs[i], ys[i], s * (0.95 + 0.6 * f), 0, math.tau)
                ctx.stroke()
        idx = np.flatnonzero(lit & inside)  # what you know
        ink(ctx, C_REAL, 0.17 * a)
        for i in idx:
            ctx.new_sub_path()
            ctx.arc(xs[i], ys[i], s * 2.3, 0, math.tau)
        ctx.fill()
        for i in idx:
            f, b = float(f_lit[i]), float(tw[i])
            if f > 0.02:
                ink(ctx, C_REAL, 0.36 * f * a)
                ctx.arc(xs[i], ys[i], s * (2.3 + 1.7 * f), 0, math.tau)
                ctx.fill()
            ink(ctx, blend(C_REAL, C_WHITE, 0.22 + 0.28 * b + 0.45 * f), a)
            ctx.arc(xs[i], ys[i], s * (1.08 + 0.55 * f), 0, math.tau)
            ctx.fill()

        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        if wall > 0.003:  # the fence: as far as you can tell, the field ends here
            ink(ctx, C_FELT, 0.95 * wall * a)
            ctx.set_line_width(0.036 * z)
            ctx.set_dash([0.15 * z, 0.14 * z], -t * 0.2)
            ctx.arc(cx, cy, fr, 0, math.tau)
            ctx.stroke()
            ctx.set_dash([])
        full = R * (1 + EDGE_PAD)
        if 0.003 < self.ping < 0.997:  # all that is missing, between the fence and the edge
            q = float(self.ping)
            ink(ctx, C_FELT, 0.75 * (1 - q) ** 1.3 * a)
            ctx.set_line_width(0.05 * z)
            ctx.arc(cx, cy, fr + (full - fr) * ease(q), 0, math.tau)
            ctx.stroke()
        if self.flash > 0.003:  # the fence has reached the edge
            q = float(self.flash)
            ink(ctx, blend(C_FELT, C_WHITE, 0.55), 0.9 * q * a)
            ctx.set_line_width((0.05 + 0.07 * q) * z)
            ctx.arc(cx, cy, full, 0, math.tau)
            ctx.stroke()
        if fog > 0.003:  # the true edge
            ink(ctx, C_MUTED, 0.85 * fog * a)
            ctx.set_line_width(0.024 * max(0.75, z))
            ctx.arc(cx, cy, R * (1 + EDGE_PAD), 0, math.tau)
            ctx.stroke()
        if self.guess_a > 0.003 and self.guess > 0.003:  # a light somebody imagines here
            ga = float(self.guess_a) * a
            ink(ctx, C_FELT, 0.2 * ga)
            ctx.arc(cx, cy, self.guess * R, 0, math.tau)
            ctx.fill()
            ink(ctx, C_FELT, 0.95 * ga)
            ctx.set_line_width(0.03 * max(0.8, z))
            ctx.set_dash([0.09, 0.08], t * 0.16)
            ctx.arc(cx, cy, self.guess * R, 0, math.tau)
            ctx.stroke()
            ctx.set_dash([])
        if self.orb > 0.003:
            self._orb(ctx, cx, cy, 0.15 * (R / 2.5) ** 0.5, t, a * float(self.orb))
        if self.mark > 0.003:
            h = R * (1 + EDGE_PAD) + 0.13 + 0.015 * math.sin(3.0 * t)
            arm = 0.3 * R
            ink(ctx, C_FELT, float(self.mark) * a)
            ctx.set_line_width(0.04)
            for sx in (-1, 1):
                for sy in (-1, 1):
                    ctx.move_to(cx + sx * (h - arm), cy + sy * h)
                    ctx.line_to(cx + sx * h, cy + sy * h)
                    ctx.line_to(cx + sx * h, cy + sy * (h - arm))
            ctx.stroke()
        if self.window is not None:
            ctx.reset_clip()
            x0, y0, x1, y1 = self.window
            rr(ctx, x0, y0, x1 - x0, y1 - y0, 0.2)
            ink(ctx, C_FAINT, a)
            ctx.set_line_width(0.028)
            ctx.stroke()

    def _orb(self, ctx, x, y, ro, t, a):
        ro *= 1 + 0.035 * math.sin(2.3 * t)
        lamp(ctx, x, y, ro * 3.3, C_WARM, 0.55 * a)
        ink(ctx, C_WARM, a)
        ctx.arc(x, y, ro, 0, math.tau)
        ctx.fill()
        ink(ctx, C_RIM, a)
        ctx.set_line_width(ro * 0.13)
        ctx.arc(x, y, ro, 0, math.tau)
        ctx.stroke()
        if ro > 0.085:
            k = 0.12 if (t % 4.3) < 0.13 else 1.0  # a blink
            ink(ctx, C_EYE, a)
            for sx in (-1, 1):
                ctx.save()
                ctx.translate(x + sx * 0.36 * ro, y + 0.1 * ro)
                ctx.scale(0.14 * ro, 0.23 * ro * k)
                ctx.arc(0, 0, 1, 0, math.tau)
                ctx.restore()
                ctx.fill()


# --------------------------------------------------------------------------- #
# darkness over a rectangle, except where a light falls
# --------------------------------------------------------------------------- #
class Spot(Layer):
    """What a beginner sees of a chess board: ``dark`` (0..1) covers the rectangle,
    except around ``lights`` (rows of x, y, radius), where it stays as it is.
    ``ring`` (x, y, radius) is a fence around the light, drawn on the rectangle only,
    as bright as ``ring_a`` (0..1); its dashes march with the clock."""

    def __init__(self, world, rect, lights, tint=NIGHT):
        super().__init__()
        self.world = world
        self.rect = rect  # (x0, y0, x1, y1)
        self.lights = np.array(lights, dtype=float)
        self.dark = 0.0
        self.ring = None
        self.ring_a = 0.0
        self.hue3 = rgb(tint)
        self.set_z_index(11)

    def paint(self, camera, pixels):
        ctx = camera.get_cairo_context(pixels)
        x0, y0, x1, y1 = self.rect
        self._dark(ctx, x0, y0, x1, y1)
        if self.ring is not None and self.ring_a * self.alpha > 0.003:
            x, y, r = self.ring
            ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
            ctx.clip()
            ink(ctx, C_FELT, 0.95 * float(self.ring_a) * float(self.alpha))
            ctx.set_line_width(0.045)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.set_dash([0.17, 0.16], -0.2 * self.world.t)
            ctx.arc(x, y, r, 0, math.tau)
            ctx.stroke()
            ctx.set_dash([])
            ctx.reset_clip()

    def _dark(self, ctx, x0, y0, x1, y1):
        a = float(self.alpha) * float(self.dark)
        if a <= 0.003:
            return
        breath = 1 + 0.03 * math.sin(1.6 * self.world.t)
        ctx.push_group()
        ink(ctx, self.hue3, 1.0)
        ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
        ctx.fill()
        ctx.set_operator(cairo.OPERATOR_DEST_OUT)
        for x, y, r in self.lights:
            grad = cairo.RadialGradient(x, y, 0, x, y, r * breath)
            grad.add_color_stop_rgba(0.0, 0, 0, 0, 1.0)
            grad.add_color_stop_rgba(0.55, 0, 0, 0, 0.95)
            grad.add_color_stop_rgba(1.0, 0, 0, 0, 0.0)
            ctx.set_source(grad)
            ctx.arc(x, y, r * breath, 0, math.tau)
            ctx.fill()
        ctx.set_operator(cairo.OPERATOR_OVER)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)


# --------------------------------------------------------------------------- #
# the one who learns: a face drawn from ten numbers
# --------------------------------------------------------------------------- #
#            eye w  lid up  lid lo  brow tilt  brow a  brow y  mouth w  top sag  low sag  blush
MOODS = {
    "calm":  (0.115, 0.165, -0.165, 0.00, 0.0, 0.00, 0.17, 0.070, 0.090, 0.0),
    "sure":  (0.125, 0.100, -0.160, -0.12, 1.0, -0.03, 0.21, 0.085, 0.130, 0.25),
    "proud": (0.150, 0.150, 0.070, 0.00, 0.0, 0.00, 0.27, 0.030, 0.260, 0.8),
    "shock": (0.150, 0.215, -0.215, 0.28, 1.0, 0.09, 0.085, -0.075, 0.105, 0.0),
    "sad":   (0.115, 0.135, -0.165, 0.50, 1.0, 0.02, 0.17, -0.075, -0.050, 0.0),
    "grit":  (0.115, 0.105, -0.155, -0.38, 1.0, -0.05, 0.14, 0.000, 0.022, 0.0),
    "wise":  (0.120, 0.125, -0.140, 0.00, 0.0, 0.00, 0.20, 0.085, 0.105, 0.3),
    "happy": (0.145, 0.140, 0.065, 0.00, 0.0, 0.00, 0.22, 0.100, 0.150, 0.6),
}  # fmt: skip
_U = np.linspace(-1.0, 1.0, 17)
_ARCH = np.sqrt(np.clip(1 - _U**2, 0, 1))  # the profile of an eyelid
_SAG = 1 - _U**2  # the profile of a lip
_DISC = Circle(radius=1.0).points.copy()


class Buddy(VGroup):
    """The one who learns. ``p`` holds the face (a row of ``MOODS``); every part is
    rebuilt from it on each frame, with a slow bob and a blink from the clock, so a
    change of mood is a tween (``feel``) and a wait is never a still face.

    ``refresh`` only ever sets points and stroke widths, never an opacity: a fade
    works on copies of the mobject whose updaters keep running, and an updater that
    sets an opacity undoes the fade on every frame (the cheeks stayed on screen after
    a ``FadeOut``). So a part that is "not there" (no blush, no brows) has no size.

    ``px, py`` its centre, ``rad`` its radius, ``pulse`` a swell (0..1), ``look_x,
    look_y`` where the eyes look (about -1..1)."""

    def __init__(self, world, at, rad=0.9, mood="calm", hue=WARM, rim=RIM, phase=0.0, bob=1.0):
        super().__init__()
        self.world = world
        self.px, self.py, self.rad = float(at[0]), float(at[1]), float(rad)
        self.p = np.array(MOODS[mood], dtype=float)
        self.pulse = 0.0
        self.bob = bob
        self.phase = phase
        self.aim = None  # a mood to drift towards (set it from an updater)
        self.look_x = self.look_y = 0.0
        self._seen_t = world.t
        self.halo2 = VMobject().set_fill(hue, 0.07).set_stroke(width=0)
        self.halo1 = VMobject().set_fill(hue, 0.13).set_stroke(width=0)
        self.body = VMobject().set_fill(hue, 1.0).set_stroke(rim, width=1)
        self.gleam = VMobject().set_fill(WHITE, 0.4).set_stroke(width=0)
        self.blush = VGroup(*[VMobject().set_fill(BLUSH, 0.5).set_stroke(width=0) for _ in "lr"])
        self.eyes = VGroup(*[VMobject().set_fill(EYE, 1.0).set_stroke(EYE, width=1) for _ in "lr"])
        self.glints = VGroup(*[VMobject().set_fill(WHITE, 0.95).set_stroke(width=0) for _ in "lr"])
        self.brows = VGroup(*[VMobject().set_stroke(EYE, width=1).set_fill(opacity=0) for _ in "lr"])
        self.mouth = VMobject().set_fill(EYE, 1.0).set_stroke(EYE, width=1)
        self.add(self.halo2, self.halo1, self.body, self.gleam, self.blush, self.eyes,
                 self.glints, self.brows, self.mouth)  # fmt: skip
        self.refresh()
        self.add_updater(lambda m: m.refresh())

    def feel(self, mood, rt=0.4):
        """The animation that takes the face to ``mood`` (with a small swell)."""
        return Feel(self, mood, run_time=rt)

    def centre(self):
        t = self.world.t
        dy = self.bob * 0.045 * self.rad * math.sin(1.9 * t + self.phase)
        return np.array([self.px, self.py + dy, 0.0])

    def refresh(self):
        t = self.world.t
        dt, self._seen_t = max(0.0, t - self._seen_t), t
        if self.aim is not None:
            self.p += (np.array(MOODS[self.aim]) - self.p) * min(1.0, 7.0 * dt)
        k = self.rad * (1 + 0.07 * self.pulse)
        c = self.centre()

        def place(pts):
            out = np.zeros((len(pts), 3))
            out[:, :2] = np.asarray(pts)[:, :2] * k
            return out + c

        sw = 4.2 * k  # strokes follow the size
        self.body.set_stroke(width=0.9 * sw)
        self.mouth.set_stroke(width=sw)
        self.halo2.set_points(place(_DISC * 1.5))
        self.halo1.set_points(place(_DISC * 1.24))
        self.body.set_points(place(_DISC))
        self.gleam.set_points(place(_DISC * [0.17, 0.1, 1] + [-0.42, 0.62, 0]))
        ew, up, lo, bt, ba, by, mw, mt, mb, bl = self.p
        wink = 1.0 if ((t + 0.7 * self.phase) % 3.9) < 0.14 and up - lo > 0.2 else 0.0
        mid = 0.5 * (up + lo)
        up_, lo_ = up + (mid - up) * wink, lo + (mid - lo) * wink
        lo_ = min(lo_, up_ - 0.03)
        wide = min(1.0, max(0.0, (up_ - lo_ - 0.12) / 0.2))
        for s, eye, glint, brow, cheek in zip(
            (-1, 1), self.eyes, self.glints, self.brows, self.blush, strict=True
        ):
            ex, ey = 0.34 * s + 0.06 * self.look_x, 0.15 + 0.05 * self.look_y
            eye.set_stroke(width=0.4 * sw)
            brow.set_stroke(width=1.15 * sw * float(ba))  # no brows: no width
            top = np.column_stack([ex + ew * _U, ey + up_ * _ARCH])
            low = np.column_stack([ex + ew * _U[::-1], ey + lo_ * _ARCH[::-1]])
            eye.set_points_as_corners(place(np.vstack([top, low, top[:1]])))
            glint.set_points(place(_DISC * (0.042 * wide) + [ex + 0.045, ey + mid + 0.06, 0]))
            bx, byy = ex, ey + 0.32 + by
            ends = np.array([[bx - 0.15 * s, byy + 0.15 * bt], [bx + 0.15 * s, byy - 0.15 * bt]])
            brow.set_points_as_corners(place(ends))
            size = math.sqrt(max(0.0, float(bl)))  # no blush: no size
            cheek.set_points(place(_DISC * [0.13 * size, 0.075 * size, 1] + [0.6 * s, -0.17, 0]))
        my = -0.36 + 0.02 * self.look_y
        mx = 0.035 * self.look_x
        top = np.column_stack([mx + mw * _U, my - mt * _SAG])
        low = np.column_stack([mx + mw * _U[::-1], my - mb * _SAG[::-1]])
        self.mouth.set_points_as_corners(place(np.vstack([top, low, top[:1]])))


class Sweep(Animation):
    """Run a plain attribute from 0 to 1 again and again for the whole ``run_time``
    (a ring that leaves, a scan): motion for a hold, as ``Breathe`` but one way."""

    def __init__(self, obj, run_time, attr="ping", period=1.6):
        self.obj, self.attr = obj, attr
        self.cycles = max(1, round(run_time / period))
        super().__init__(
            Mobject(), run_time=run_time, rate_func=linear, remover=True, suspend_mobject_updating=False
        )

    def begin(self):
        self.starting_mobject = Mobject()
        self.interpolate(0)

    def interpolate_mobject(self, alpha):
        setattr(self.obj, self.attr, 0.0 if alpha >= 1 else (alpha * self.cycles) % 1.0)


class Hop(Animation):
    """Move a ``FogMap`` to ``x`` along an arc ``lift`` high: fields that change places
    pass over each other instead of through."""

    def __init__(self, fm, x, lift=0.5, run_time=1.2):
        self.fm, self.x1, self.lift = fm, float(x), lift
        super().__init__(Mobject(), run_time=run_time, remover=True, suspend_mobject_updating=False)

    def begin(self):
        self.x0, self.y0 = self.fm.cx, self.fm.cy
        self.starting_mobject = Mobject()
        self.interpolate(0)

    def interpolate_mobject(self, alpha):
        a = self.rate_func(alpha)
        self.fm.cx = self.x0 + (self.x1 - self.x0) * a
        self.fm.cy = self.y0 + self.lift * math.sin(math.pi * a)


class Feel(Animation):
    """Take a ``Buddy``'s face to a mood. Runs on a throw-away host, so the buddy's
    own updater (the bob, the blink) keeps running."""

    def __init__(self, buddy, mood, run_time=0.4):
        self.buddy, self.goal = buddy, np.array(MOODS[mood], dtype=float)
        super().__init__(Mobject(), run_time=run_time, remover=True, suspend_mobject_updating=False)

    def begin(self):
        self.start = self.buddy.p.copy()
        self.starting_mobject = Mobject()
        self.interpolate(0)

    def interpolate_mobject(self, alpha):
        a = self.rate_func(alpha)
        self.buddy.p = self.start + (self.goal - self.start) * a
        self.buddy.pulse = math.sin(math.pi * alpha)


def face_glyph(rad=0.3):
    """A still, small face for a title card (no clock)."""
    body = Circle(radius=rad, stroke_color=RIM, stroke_width=3).set_fill(WARM, 1.0)
    halo = Circle(radius=rad * 1.45, stroke_width=0).set_fill(WARM, 0.14)
    eyes = VGroup(
        *[
            Ellipse(width=0.26 * rad, height=0.42 * rad, stroke_width=0)
            .set_fill(EYE, 1.0)
            .move_to([s * 0.36 * rad, 0.1 * rad, 0])
            for s in (-1, 1)
        ]
    )
    return VGroup(halo, body, eyes)


def thought(text, fs=25, toward=DL, hue=MUTED, color=INK):
    """A thought: a rounded box and two small bubbles trailing ``toward`` its owner."""
    t = line_txt(text, fs=fs, color=color, weight="MEDIUM")
    box = RoundedRectangle(
        width=t.width + 0.72, height=t.height + 0.34, corner_radius=0.3,
        stroke_color=hue, stroke_width=2.6, fill_color=PANEL, fill_opacity=1.0,
    )  # fmt: skip
    t.move_to(box)
    d = np.array(toward, dtype=float)
    corner = box.get_corner(toward) - 0.2 * d * np.array([1.0, 0.0, 0.0])
    dots = VGroup(
        Circle(radius=0.095).move_to(corner + 0.2 * d),
        Circle(radius=0.058).move_to(corner + 0.42 * d),
    ).set_stroke(hue, width=2.4).set_fill(PANEL, 1.0)  # fmt: skip
    g = VGroup(box, t, dots)
    g.box, g.label = box, t
    return g


# --------------------------------------------------------------------------- #
# the two gauges: how much it feels like, how much it really is
# --------------------------------------------------------------------------- #
def percent(v):
    """A share as the whole number of percent a gauge shows (halves round up)."""
    return int(math.floor(100 * v + 0.5 + 1e-9))


class Gauge(VGroup):
    """A bar from "none of it" to "all of it", with its share as a number. ``v`` (0..1)
    is a plain attribute: tween it."""

    def __init__(self, label, hue, at, w=5.3, h=0.34, fs=23):
        super().__init__()
        self.hue, self.w, self.h, self.v = hue, w, h, 0.0
        self.track = RoundedRectangle(width=w, height=h, corner_radius=h / 2, stroke_width=0)
        self.track.set_fill(FAINT, 0.6).move_to([at[0], at[1], 0])
        self.title = line_txt(label, fs=fs, color=hue, weight="BOLD")
        self.title.next_to(self.track, UP, buff=0.14).align_to(self.track, LEFT)
        self.bar = VMobject().set_fill(hue, 1.0).set_stroke(width=0)
        self.pct = VGroup()
        self._shown = None
        self.add(self.track, self.bar, self.title, self.pct)
        self.refresh()
        self.add_updater(lambda m: m.refresh())

    def _number(self, k):
        m = Text(f"{k}%", font_size=34, color=self.hue, weight="BOLD")
        m.align_to(self.track, RIGHT)
        return m.shift(UP * (baseline_of(self.title) - m.get_bottom()[1]))

    def refresh(self):
        left = self.track.get_left()
        w = max(1e-3, self.w * min(1.0, max(0.0, self.v)))
        r = min(self.h / 2, w / 2)
        box = RoundedRectangle(width=w, height=self.h, corner_radius=max(r, 1e-3), stroke_width=0)
        box.move_to(left + RIGHT * w / 2)
        self.bar.set_points(box.points)
        k = percent(self.v)
        if k != self._shown:
            new = self._number(k)
            if len(self.pct) == 0:
                self.pct.add(new)
            else:
                self.pct[0].become(new)
            self._shown = k

    def detail(self, text, fs=20):
        """A line under the bar: what the share is a share of."""
        m = line_txt(text, fs=fs, color=MUTED)
        m.next_to(self.track, DOWN, buff=0.13).align_to(self.track, LEFT)
        return m


# --------------------------------------------------------------------------- #
# the chess board (black at the bottom: you play black)
# --------------------------------------------------------------------------- #
LIGHT_SQ, DARK_SQ = "#AAB4C7", "#55617A"
PIECE_W, PIECE_W_EDGE = "#F7F2E6", "#20242C"
PIECE_B, PIECE_B_EDGE = "#14171D", "#C4CBDA"
GLYPH = {"K": "♚", "Q": "♛", "R": "♜", "B": "♝", "N": "♞", "P": "♟"}


def _symbol_font():
    import manimpango

    fonts = set(manimpango.list_fonts())
    for cand in ("Arial Unicode MS", "Apple Symbols", "DejaVu Sans", "Symbola", "Segoe UI Symbol"):
        if cand in fonts:
            return cand
    return None


SYMFONT = _symbol_font()


class Board(VGroup):
    """A chess board seen from black's side. ``at("f7")`` is the middle of a square;
    ``men`` maps a square to the piece standing on it."""

    def __init__(self, centre, sq=0.62):
        super().__init__()
        self.sq = sq
        self.c = np.array([centre[0], centre[1], 0.0])
        self.men = {}
        squares = VGroup()
        for f in range(8):
            for r in range(1, 9):
                col = DARK_SQ if (f + r) % 2 == 1 else LIGHT_SQ
                m = Square(sq).set_fill(col, 1.0).set_stroke(col, width=0.6)
                squares.add(m.move_to(self.at(M.FILES[f] + str(r))))
        frame = Square(8 * sq + 0.1).move_to(self.c).set_stroke(FAINT, width=3).set_fill(opacity=0)
        marks = VGroup()
        for f in range(8):  # line_txt: the letters share a baseline (g and d would not)
            t = line_txt(M.FILES[f], fs=17, color=MUTED)
            marks.add(t.move_to(self.at(M.FILES[f] + "8") + DOWN * (0.5 * sq + 0.24)))
        for r in range(1, 9):
            t = line_txt(str(r), fs=17, color=MUTED)
            marks.add(t.move_to(self.at("h" + str(r)) + LEFT * (0.5 * sq + 0.24)))
        self.squares, self.frame, self.marks = squares, frame, marks
        self.add(squares, frame, marks)
        king = Text(GLYPH["K"], font=SYMFONT, font_size=96) if SYMFONT else Text(GLYPH["K"], font_size=96)
        self.k = 0.78 * sq / king.height  # one scale for every piece: a pawn stays small

    def at(self, name):
        f, r = M.FILES.index(name[0]), int(name[1])
        return self.c + np.array([(3.5 - f) * self.sq, (4.5 - r) * self.sq, 0.0])

    def rect(self, pad=0.0):
        h = 4 * self.sq + pad
        return (self.c[0] - h, self.c[1] - h, self.c[0] + h, self.c[1] + h)

    def spot(self, name):
        """Where the piece on ``name`` stands (pieces stand on the bottom of their square)."""
        return self.at(name) + DOWN * 0.39 * self.sq

    def man(self, code):
        kw = {"font": SYMFONT} if SYMFONT else {}
        m = Text(GLYPH[code[1]], font_size=96, **kw).scale(self.k)
        if code[0] == "w":
            m.set_fill(PIECE_W, 1.0).set_stroke(PIECE_W_EDGE, width=0.8)
        else:
            m.set_fill(PIECE_B, 1.0).set_stroke(PIECE_B_EDGE, width=0.9)
        return m.set_z_index(10)

    def setup(self, position):
        """Build the pieces of ``position``; returns them as a group (not added)."""
        army = VGroup()
        for name, code in position.items():
            m = self.man(code)
            m.move_to(self.spot(name), aligned_edge=DOWN)
            self.men[name] = m
            army.add(m)
        return army

    def go(self, a, b, rt=0.5, hop=False):
        """The animation that moves the piece on ``a`` to ``b`` (and the bookkeeping)."""
        m = self.men.pop(a)
        self.men[b] = m
        goal = self.spot(b) + UP * m.height / 2
        kw = {"path_arc": -0.9} if hop else {}
        return m.animate(run_time=rt, **kw).move_to(goal)

    def wash(self, name, color, op=0.5):
        """A tint over one square (under the pieces)."""
        return Square(self.sq).move_to(self.at(name)).set_fill(color, op).set_stroke(width=0).set_z_index(2)


# --------------------------------------------------------------------------- #
# the same run as a chart
# --------------------------------------------------------------------------- #
class ClimbChart(VGroup):
    """Two lines drawn as the light grows: how much of the field you feel you know
    (gold) and how much you really know (blue), against time spent learning. The
    lines are read from the same functions as the map (``model``), up to the map's
    current ``know``; where the feeling runs ahead of the facts, the gap is shaded."""

    def __init__(self, fogmap, x0, y0, w, h, r_max=M.EXPERT):
        super().__init__()
        self.src, self.x0, self.y0, self.w, self.h, self.r_max = fogmap, x0, y0, w, h, r_max
        self.upto = None  # draw up to this light instead of the map's
        self.rs = np.linspace(0.0, r_max, 600)
        self.fy = M.felt(np.maximum(self.rs, 1e-6))
        self.fy[0] = 0.0
        self.ry = M.real(self.rs)
        self.gap = VMobject().set_fill(FELT_C, 0.16).set_stroke(width=0)
        self.line_real = VMobject().set_stroke(REAL_C, width=9).set_fill(opacity=0)
        self.line_felt = VMobject().set_stroke(FELT_C, width=5).set_fill(opacity=0)
        self.head = Dot(radius=0.085, color=REAL_C).set_z_index(4)
        for m in (self.line_real, self.line_felt):
            m.joint_type = LineJointType.ROUND
        self.add(self.gap, self.line_real, self.line_felt, self.head)
        self.refresh()
        self.add_updater(lambda m: m.refresh())

    def xy(self, r, v):
        return np.array([self.x0 + self.w * r / self.r_max, self.y0 + self.h * v, 0.0])

    def now(self):
        r = self.src.know if self.upto is None else self.upto
        return min(self.r_max, max(0.0, float(r)))

    def tip(self, which="felt"):
        r = self.now()
        v = float(M.felt(r)) if (which == "felt" and r > 1e-6) else float(M.real(r))
        return self.xy(r, v)

    def refresh(self):
        r = self.now()
        k = int(np.searchsorted(self.rs, r))
        rs = np.append(self.rs[:k], r)
        fy = np.append(self.fy[:k], float(M.felt(r)) if r > 1e-6 else 0.0)
        ry = np.append(self.ry[:k], float(M.real(r)))
        if len(rs) < 2:
            rs, fy, ry = np.array([0.0, 1e-4]), np.zeros(2), np.zeros(2)
        xs, zero = self.x0 + self.w * rs / self.r_max, np.zeros_like(rs)
        fp = np.column_stack([xs, self.y0 + self.h * fy, zero])
        rp = np.column_stack([xs, self.y0 + self.h * ry, zero])
        self.line_felt.set_points_as_corners(fp)
        self.line_real.set_points_as_corners(rp)
        self.gap.set_points_as_corners(np.vstack([fp, rp[::-1], fp[:1]]))
        self.head.move_to(rp[-1])

"""Motion that carries meaning: attribute tweens, ambient pulses, packets, bursts.

Two ideas, both born in the Yjs film and shared since:

* **Attribute-driven mobjects.** A self-laying-out mobject (a row of items, a line
  of text, a folding code panel) exposes plain float attributes (``open``, ``glow``,
  ``dead`` ...) and an optional ``refresh()``. ``Tween`` / ``Breathe`` animate those
  attributes on a throw-away host, so the mobject's own updaters keep running while
  the value moves (a normal ``Animation`` suspends them).
* **Holds that move.** ``Breathe`` and ``Throb`` last exactly the ``run_time`` they
  are given, so they can fill what is left of a reading hold
  (``self.hold(ambient=lambda t: [Throb(node, t)])``) with motion that points at
  the thing being discussed instead of a freeze.

``Travel`` / ``stream`` send packets along a path, ``ripple`` is the "these agree"
burst, ``Do`` runs a callback inside a ``Succession``, ``Pop`` lands a small mark.
"""

from __future__ import annotations

import math

import numpy as np
from manim import (
    Animation,
    AnimationGroup,
    Circle,
    FadeIn,
    FadeOut,
    LaggedStart,
    ManimColor,
    Mobject,
    Succession,
    SurroundingRectangle,
    VGroup,
    VMobject,
    config,
    interpolate_color,
    linear,
    rate_functions,
    smooth,
)

from .palette import GOOD


def mix(a, b, t):
    """Colour ``a`` -> ``b`` by ``t`` in [0, 1]."""
    return interpolate_color(ManimColor(a), ManimColor(b), float(np.clip(t, 0, 1)))


class Tween(Animation):
    """Animate plain float attributes of any object: ``Tween(block, dead=1.0)``.

    Runs on a throw-away host mobject so no real mobject has its updaters
    suspended (the rows and lines must keep laying themselves out).
    """

    def __init__(self, obj, run_time=0.5, rate_func=smooth, **targets):
        self.obj = obj
        self.targets = targets
        super().__init__(
            Mobject(),
            run_time=run_time,
            rate_func=rate_func,
            remover=True,
            suspend_mobject_updating=False,
        )

    def begin(self):
        self.start = {k: float(getattr(self.obj, k)) for k in self.targets}
        self.starting_mobject = Mobject()
        self.interpolate(0)

    def interpolate_mobject(self, alpha):
        a = self.rate_func(alpha)
        for k, v in self.targets.items():
            setattr(self.obj, k, self.start[k] + (v - self.start[k]) * a)
        if hasattr(self.obj, "refresh"):
            self.obj.refresh()


class Breathe(Animation):
    """Pulse a plain attribute up and back for the whole ``run_time`` (a block's glow,
    a caret...): the motion that fills a reading hold and says "look here"."""

    def __init__(self, obj, run_time, attr="glow", period=1.25, lo=0.0, hi=1.0):
        self.obj, self.attr, self.lo, self.hi = obj, attr, lo, hi
        self.cycles = max(1, round(run_time / period))
        super().__init__(
            Mobject(),
            run_time=run_time,
            rate_func=linear,
            remover=True,
            suspend_mobject_updating=False,
        )

    def begin(self):
        self.starting_mobject = Mobject()
        self.interpolate(0)

    def interpolate_mobject(self, alpha):
        v = 0.5 - 0.5 * math.cos(2 * math.pi * self.cycles * alpha)
        setattr(self.obj, self.attr, self.lo + (self.hi - self.lo) * v)
        if hasattr(self.obj, "refresh"):
            self.obj.refresh()


class Throb(Animation):
    """Gently swell a mobject and bring it back, for the whole ``run_time``."""

    def __init__(self, mob, run_time, period=1.25, amp=0.06):
        self.amp = amp
        self.cycles = max(1, round(run_time / period))
        super().__init__(mob, run_time=run_time, rate_func=linear)

    def begin(self):
        self.base = self.mobject.copy()
        self.starting_mobject = Mobject()
        self.interpolate(0)

    def interpolate_mobject(self, alpha):
        v = 0.5 - 0.5 * math.cos(2 * math.pi * self.cycles * alpha)
        self.mobject.become(self.base.copy().scale(1 + self.amp * v))


def ripple(*mobs, color=GOOD, buff=0.14, grow=1.07, run_time=0.8, margin=0.22):
    """A ring that bursts outward from ``mobs`` and fades: the "they agree" beat.

    The burst is capped so the ring never leaves the frame, however wide the group.
    """
    group = VGroup(*mobs)
    xr, yr = config.frame_x_radius - margin, config.frame_y_radius - margin
    cx, cy = group.get_center()[:2]
    room = min((xr - abs(cx)) / (group.width / 2), (yr - abs(cy)) / (group.height / 2))
    buff = max(0.02, min(buff, (room - 1) * min(group.width, group.height) / 2 * 0.6))
    ring = SurroundingRectangle(group, color=color, buff=buff, corner_radius=0.14)
    ring.set_stroke(color, width=5).set_fill(opacity=0)
    limit = min((xr - abs(cx)) / (ring.width / 2), (yr - abs(cy)) / (ring.height / 2))
    grow = max(1.004, min(grow, limit))
    return Succession(
        FadeIn(ring, run_time=run_time * 0.2),
        AnimationGroup(
            ring.animate(rate_func=rate_functions.ease_out_cubic)
            .scale(grow)
            .set_stroke(opacity=0),
            run_time=run_time * 0.8,
        ),
        FadeOut(ring, run_time=0.01),
    )


class Do(Animation):
    """Run ``fn()`` at a point in a ``Succession`` (re-aim a caret, flip a flag...)."""

    def __init__(self, fn, run_time=0.02):
        self.fn = fn
        super().__init__(
            Mobject(), run_time=run_time, remover=True, suspend_mobject_updating=False
        )

    def begin(self):
        self.starting_mobject = Mobject()
        self.fn()

    def interpolate_mobject(self, alpha):
        pass


class Pop(Animation):
    """Grow a mobject that was parked at near-zero size to ``width`` with a small bounce."""

    def __init__(self, mob, width, run_time=0.4, **kw):
        self.width = width
        super().__init__(
            mob, run_time=run_time, rate_func=rate_functions.ease_out_back, **kw
        )

    def begin(self):
        self.starting_mobject = Mobject()
        self.interpolate(0)

    def interpolate_mobject(self, alpha):
        want = max(1e-3, self.width * self.rate_func(alpha))
        self.mobject.scale(want / self.mobject.width)


def glow_dot(color, r=0.07):
    """A packet: a bright core inside two soft halos."""
    return VGroup(
        Circle(radius=r * 2.6, stroke_width=0, fill_color=color, fill_opacity=0.12),
        Circle(radius=r * 1.7, stroke_width=0, fill_color=color, fill_opacity=0.22),
        Circle(radius=r, stroke_width=0, fill_color=color, fill_opacity=1.0),
    )


class Travel(Animation):
    """Send ``mob`` along ``path`` (a VMobject); it fades in and out at the ends."""

    def __init__(
        self, mob, path, run_time=0.7, rate_func=smooth, fade=0.18, keep=False, **kw
    ):
        self.path, self.fade, self.keep = path, fade, keep
        self.base = [
            (m, m.get_fill_opacity(), m.get_stroke_opacity())
            for m in mob.family_members_with_points()
        ]
        # hidden until it departs: inside a Succession the mobject is on stage early
        for m, _, _ in self.base:
            m.set_fill(opacity=0)
            m.set_stroke(opacity=0)
        super().__init__(
            mob, run_time=run_time, rate_func=rate_func, remover=not keep, **kw
        )

    def begin(self):
        self.starting_mobject = Mobject()
        self.interpolate(0)

    def interpolate_mobject(self, alpha):
        a = self.rate_func(alpha)
        self.mobject.move_to(self.path.point_from_proportion(float(np.clip(a, 0, 1))))
        f = min(1.0, alpha / self.fade)
        if not self.keep:
            f = min(f, (1 - alpha) / self.fade)
        f = max(0.0, f)
        for m, fo, so in self.base:
            m.set_fill(opacity=fo * f)
            m.set_stroke(opacity=so * f)


def stream(path, color, n=5, run_time=1.6, r=0.06, lag=0.16):
    """``n`` packets chasing each other along ``path``."""
    return LaggedStart(
        *[
            Travel(glow_dot(color, r=r), path, run_time=run_time * 0.55)
            for _ in range(n)
        ],
        lag_ratio=lag,
        run_time=run_time,
    )


def polyline(*pts):
    """A path through ``pts`` (for packets that turn corners)."""
    v = VMobject()
    v.set_points_as_corners([np.array(p, dtype=float) for p in pts])
    return v

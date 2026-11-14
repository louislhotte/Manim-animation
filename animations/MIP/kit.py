"""kit.py: the film's building blocks.

* the baked story (``assets/story.json``) as plain Python: Lea's hour, the eleventh
  arrondissement in depth, the twenty models of the city;
* the *desk*: Lea's corner of Paris, placed beside a column of panels (scenes 2-4);
* what lives on a map: stops, labels that avoid each other, courses that follow the
  streets, the 64 possible rides as dimmable arcs;
* panels: the table of orders, the bound gauge, the search tree, a scrolling log.

Everything positions itself through a ``MapPlane`` (``plane.w(metres)``), so the
same objects work in a flat scene and under a tilted 3D camera.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from manimx import *

from stage import MapPlane

HERE = Path(__file__).resolve().parent
STORY = json.loads((HERE / "assets" / "story.json").read_text())
HERO, CITY, META = STORY["hero"], STORY["city"], STORY["meta"]
ZONES, TOTALS = CITY["zones"], CITY["totals"]
DEEP = next(z for z in ZONES if z["arr"] == CITY["deep"])

# ---- the film's colour language ------------------------------------------- #
PLAN_C = GOLD  # a real course; the best one found so far (the floor)
RELAX_C = SKY  # the relaxed problem: fractional rides, the ceiling
CUT_C = BAD  # removed, cut, impossible
DONE_C = GOOD  # delivered; proven
WINDOW_C = MINT  # a delivery window (time)
TRY_C = INK  # a course being tried
MEH_C = AMBER  # what instinct gets
STOP_C = INK  # stops on the map
LINK_C = "#9AA5BD"  # an order: restaurant to customer


def A(p):
    return np.array(p, dtype=float)


# --------------------------------------------------------------------------- #
# Lea's hour as data
# --------------------------------------------------------------------------- #
ORDERS = {o["name"]: o for o in HERO["orders"]}
NAMES = sorted(ORDERS, key=lambda j: (ORDERS[j]["early"], j))  # by window
LEA = A(HERO["start"]["lea"])
RIDES = [tuple(k.split("|")) for k in HERO["mins"]]
KEPT = [tuple(k.split("|")) for k in HERO["presolve"]["rides"]]
BEST = HERO["brute"]["seq"]
TREE = HERO["tree"]["nodes"]


def stop_xy(i, end="C"):
    """Metres: Lea's start, or an order's restaurant (R) / customer (C)."""
    return LEA if i == "lea" else A(ORDERS[i][end])


def approach(i, j):
    return A(HERO["approach"][f"{i}|{j}"])


def leg(j):
    return A(HERO["leg"][j])


def course_pieces(seq, start="lea"):
    """The street polylines of a course: approach, delivery leg, approach, ..."""
    out, i = [], start
    for j in seq:
        out += [approach(i, j), leg(j)]
        i = j
    return out


def clock(minute):
    """Minute of the shift -> 20:mm (the shift starts at 8 p.m.). Floored, the way a
    clock shows time: 20:17:31 reads 20:17, so a deadline never looks later than it
    is and two times on screen differ by what a viewer would count."""
    m = int(math.floor(minute + 1e-9))
    return f"{20 + m // 60}:{m % 60:02d}"


def euro(v):
    return f"€{v:.2f}"


def sequences(n):
    """How many ways to pick some of ``n`` orders and put them in a sequence."""
    return sum(math.perm(n, k) for k in range(1, n + 1))


def how_long(seconds):
    """A duration in the unit a person would use."""
    for unit, size in (
        ("years", 365.25 * 86400),
        ("days", 86400),
        ("hours", 3600),
        ("minutes", 60),
    ):
        if seconds >= size:
            v = seconds / size
            return f"{v:,.0f} {unit}" if v >= 10 else f"{v:.1f} {unit}"
    return f"{seconds:.1f} seconds"


# --------------------------------------------------------------------------- #
# the desk: Lea's corner of Paris beside a column of panels
# --------------------------------------------------------------------------- #
class Desk:
    """The map fills the frame; the stops sit in the part left of the HUD column."""

    X0, X1, Y0, Y1 = -6.85, -0.95, -2.62, 2.50  # where the stops may be
    PAD_X, PAD_Y = 0.80, 0.42  # room kept around them for labels
    COL_X = -0.55  # the HUD column starts here
    COL_MID = (COL_X + 7.11) / 2  # ... and this is its middle

    def __init__(self):
        pts = np.array(
            [
                LEA,
                *[o["R"] for o in ORDERS.values()],
                *[o["C"] for o in ORDERS.values()],
            ]
        )
        lo, hi = pts.min(axis=0), pts.max(axis=0)
        self.scale = min(
            (self.X1 - self.X0 - 2 * self.PAD_X) / (hi[0] - lo[0]),
            (self.Y1 - self.Y0 - 2 * self.PAD_Y) / (hi[1] - lo[1]),
        )  # frame units per metre
        self.mid = (lo + hi) / 2
        self.at = A([(self.X0 + self.X1) / 2, (self.Y0 + self.Y1) / 2])
        self.origin = (
            self.mid - self.at / self.scale
        )  # the map point at the frame's centre

    def plane(self, wide=False):
        """The ground. ``wide`` adds the whole of Paris underneath, for a camera
        that tilts and sees past the edges of the close-up."""
        p = MapPlane(self.origin, self.scale)
        if wide:
            p.add_layer(
                *BIG_VIEW[:3], 8192, aspect=BIG_VIEW[3], detail=False, feather=0.05
            )
        width = config.frame_width / self.scale * 1.3
        p.add_layer(*self.origin, width, 4096, feather=0.04 if wide else 0.0)
        return p


def _big_view():
    import osm

    s, w, n, e = osm.BBOX_BIG
    x0, y0 = osm.to_xy(s, w)
    x1, y1 = osm.to_xy(n, e)
    return ((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, (y1 - y0) / (x1 - x0))


BIG_VIEW = _big_view()  # centre x, centre y, width (metres), height / width


def band(y0, y1, top=False, x0=-7.2, x1=7.2, op=0.92):
    """A soft dark band over the map, so text on it stays readable: opaque at the
    frame edge, clear toward the picture."""
    r = Rectangle(width=x1 - x0, height=abs(y1 - y0), stroke_width=0)
    r.move_to([(x0 + x1) / 2, (y0 + y1) / 2, 0])
    r.set_fill(color=[BG, BG], opacity=[op, 0.0])
    r.set_sheen_direction(DOWN if top else UP)
    return r


def hud_column(x0=Desk.COL_X, op=0.965):
    """The right-hand column the panels live in: a dark sheet with a hairline."""
    sheet = Rectangle(width=7.2 - x0, height=8.2, stroke_width=0)
    sheet.set_fill(BG, opacity=op).move_to([(x0 + 7.2) / 2, 0, 0])
    edge = Line([x0, -4.1, 0], [x0, 4.1, 0]).set_stroke(FAINT, width=1.5, opacity=0.9)
    return VGroup(sheet, edge)


# --------------------------------------------------------------------------- #
# stops, labels
# --------------------------------------------------------------------------- #
def resto_marker(p, s=0.19, color=STOP_C):
    """A restaurant: a small rounded square."""
    m = RoundedRectangle(width=s, height=s, corner_radius=s * 0.24)
    m.set_stroke(color, width=2.4).set_fill(PANEL, opacity=1.0)
    return m.move_to(p)


def home_marker(p, r=0.085, color=STOP_C):
    """A customer: a ring."""
    m = Circle(radius=r).set_stroke(color, width=2.4).set_fill(BG, opacity=1.0)
    return m.move_to(p)


def courier_marker(p, r=0.13, color=PLAN_C, alive=False):
    """A courier: a filled disc with a halo. ``alive``: the halo breathes for as long
    as the marker is on stage (the eye finds her at once, and a hold is never frozen)."""
    halo = Circle(radius=r * 1.9, stroke_width=0).set_fill(color, opacity=0.22)
    core = Circle(radius=r).set_stroke(BG, width=2.0).set_fill(color, opacity=1.0)
    g = VGroup(halo, core).move_to(p)
    if alive:
        halo.clock, halo.w0 = 0.0, halo.width

        def tick(m, dt):
            m.clock += dt
            k = 0.5 - 0.5 * math.cos(TAU * m.clock / 1.9)
            m.scale_to_fit_width(m.w0 * (1.0 + 0.5 * k)).move_to(core)
            m.set_fill(opacity=0.26 - 0.14 * k)

        halo.add_updater(tick)
    return g


def breathing(mob, lo=0.6, period=1.8):
    """Let a highlight breathe while it is on stage: its opacity swings between its
    own value and ``lo`` times it. Returns ``mob``."""
    mob.clock = 0.0

    def tick(m, dt):
        m.clock += dt
        k = lo + (1 - lo) * (0.5 + 0.5 * math.cos(TAU * m.clock / period))
        m.set_fill(opacity=m.full * k)

    mob.full = mob.get_fill_opacity()
    mob.add_updater(tick)
    return mob


def rider(path, period=7.0, color=INK, r=0.07):
    """A dot that keeps riding along ``path`` (a course): the picture of a course
    being ridden, for as long as it is shown."""
    dot = VGroup(
        Circle(radius=r * 2.0, stroke_width=0).set_fill(color, opacity=0.25),
        Circle(radius=r, stroke_width=0).set_fill(color, opacity=1.0),
    )
    dot.clock = 0.0

    def tick(m, dt):
        m.clock += dt
        m.move_to(path.point_from_proportion((m.clock / period) % 1.0))

    dot.move_to(path.point_from_proportion(0.0))
    dot.add_updater(tick)
    return dot


def order_link(a, b, color=LINK_C):
    """An order on the map: restaurant to customer, a dashed line with a chevron."""
    a, b = A(a), A(b)
    d = (b - a) / max(np.linalg.norm(b - a), 1e-6)
    line = DashedLine(a + d * 0.11, b - d * 0.10, dash_length=0.07, dashed_ratio=0.55)
    line.set_stroke(color, width=2.0, opacity=0.9)
    mid = a + (b - a) * 0.55
    n = np.array([-d[1], d[0], 0.0])
    tip = VMobject().set_points_as_corners(
        [mid - d * 0.07 + n * 0.055, mid, mid - d * 0.07 - n * 0.055]
    )
    tip.set_stroke(color, width=2.0, opacity=0.9)
    return VGroup(line, tip)


def tag(text, fs=16, color=INK, weight="MEDIUM", op=0.78, font=None):
    """A small label on a dark plate (it has to read over streets)."""
    t = txt(text, fs=fs, color=color, weight=weight, font=font)
    bg = RoundedRectangle(
        width=t.width + 0.16, height=t.height + 0.12, corner_radius=0.05, stroke_width=0
    ).set_fill(BG, opacity=op)
    bg.move_to(t)
    g = VGroup(bg, t)
    g.text = t
    return g


def badge(text, color, fs=16):
    """A value pinned on a ride: a filled pill in the ride's colour. Unlike ``tag``
    (a label on a dark plate), so that the two never read as one phrase when they
    end up side by side ("burger 0.52")."""
    t = txt(text, fs=fs, color=BG, font=MONO, weight="BOLD")
    box = RoundedRectangle(
        width=t.width + 0.2, height=t.height + 0.14, corner_radius=0.09, stroke_width=0
    ).set_fill(color, opacity=1.0)
    box.move_to(t)
    g = VGroup(box, t)
    g.text = t
    return g


def _box(m, pad=0.0):
    c, w, h = m.get_center(), m.width / 2 + pad, m.height / 2 + pad
    return (c[0] - w, c[1] - h, c[0] + w, c[1] + h)


def _overlap(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return max(0.0, w) * max(0.0, h)


def place_labels(items, obstacles, region, segments=()):
    """Put every label next to its anchor where it covers least.

    ``items``: (label, anchor point, marker half-size); ``obstacles``: boxes
    (x0, y0, x1, y1) of the markers; ``region``: the box labels must stay in;
    ``segments``: (a, b) lines worth keeping clear (order links)."""
    placed = list(obstacles)
    dirs = [RIGHT, LEFT, UP, DOWN, UR, UL, DR, DL]
    for lab, p, half in sorted(items, key=lambda it: -it[0].width):
        best = None
        for k, d in enumerate(dirs):
            off = np.array(
                [
                    d[0] * (half + 0.07 + lab.width / 2),
                    d[1] * (half + 0.07 + lab.height / 2),
                    0,
                ]
            )
            lab.move_to(A(p) + off)
            box = _box(lab, 0.02)
            cost = sum(_overlap(box, o) for o in placed) * 40
            cost += 400 * (
                max(0, region[0] - box[0]) + max(0, box[2] - region[2])
                + max(0, region[1] - box[1]) + max(0, box[3] - region[3])
            )  # fmt: skip
            for a, b in segments:
                for s in np.linspace(0.15, 0.85, 8):
                    q = A(a) + (A(b) - A(a)) * s
                    if box[0] < q[0] < box[2] and box[1] < q[1] < box[3]:
                        cost += 0.06
            cost += 0.002 * k  # mild preference for the first sides
            if best is None or cost < best[0]:
                best = (cost, lab.get_center().copy())
        lab.move_to(best[1])
        placed.append(_box(lab, 0.02))
    return placed


class Stops(VGroup):
    """Lea and her eight orders on a map: markers, links, and their labels.

    ``self.labels`` (dish at the restaurant, fee at the customer, "Lea") are kept
    apart from the group: a flat scene adds them, a 3D scene turns them into
    billboards. ``self.of[name]`` = (restaurant, link, customer) of one order."""

    def __init__(self, plane, region=None):
        super().__init__()
        self.plane = plane
        w = plane.w
        self.lea = courier_marker(w(LEA), alive=True)
        self.of, self.dish, self.fee = {}, {}, {}
        items, obstacles, segments = [], [_box(self.lea, 0.02)], []
        for j in NAMES:
            o = ORDERS[j]
            r, c = w(A(o["R"])), w(A(o["C"]))
            parts = VGroup(order_link(r, c), resto_marker(r), home_marker(c))
            self.of[j] = parts
            self.add(parts)
            obstacles += [_box(parts[1], 0.02), _box(parts[2], 0.02)]
            segments.append((r, c))
            self.dish[j] = tag(j)
            self.fee[j] = tag(euro(o["pay"]), font=MONO, color=INK)
            items += [(self.dish[j], r, 0.10), (self.fee[j], c, 0.09)]
        self.add(self.lea)
        self.who = tag("Léa", color=PLAN_C, weight="BOLD", fs=18)
        items.append((self.who, w(LEA), 0.14))
        self.region = region or (
            Desk.X0 - 0.1,
            Desk.Y0 - 0.1,
            Desk.X1 + 0.1,
            Desk.Y1 + 0.1,
        )
        self.boxes = place_labels(items, obstacles, self.region, segments)
        self.labels = VGroup(self.who, *self.dish.values(), *self.fee.values())

    def place(self, label, anchor, half=0.05):
        """Put one more label near ``anchor``, clear of every stop and label."""
        self.boxes = place_labels([(label, anchor, half)], self.boxes, self.region)
        return label

    def is_clear(self, mob, pad=0.08, fees=True):
        """True when ``mob`` keeps ``pad`` from every stop and label, inside the
        region. ``fees=False``: for a scene that does not show the fee labels."""
        b = _box(mob, pad)
        x0, y0, x1, y1 = self.region
        skip = set() if fees else {_box(m, 0.02) for m in self.fee.values()}
        return (
            all(_overlap(b, o) == 0 for o in self.boxes if o not in skip)
            and b[0] >= x0 and b[1] >= y0 and b[2] <= x1 and b[3] <= y1
        )  # fmt: skip

    def order(self, j):
        return VGroup(self.of[j], self.dish[j], self.fee[j])


class MiniStops(VGroup):
    """The same stops, small and without labels: for a map in a window."""

    def __init__(self, plane, k=0.6):
        super().__init__()
        w = plane.w
        for j in NAMES:
            o = ORDERS[j]
            r, c = w(A(o["R"])), w(A(o["C"]))
            link = Line(r, c).set_stroke(LINK_C, width=1.2, opacity=0.55)
            self.add(
                link,
                resto_marker(r, s=0.19 * k).set_stroke(width=1.8),
                home_marker(c, r=0.085 * k).set_stroke(width=1.8),
            )
        self.lea = courier_marker(w(LEA), r=0.13 * k)
        self.add(self.lea)


# --------------------------------------------------------------------------- #
# courses and rides
# --------------------------------------------------------------------------- #
def street_path(plane, polys, z=0.0):
    """One VMobject through consecutive street polylines (metres)."""
    pts = [plane.w(polys[0], z)]
    for p in polys[1:]:
        pts.append(plane.w(p[1:], z))
    v = VMobject()
    v.set_points_as_corners(np.vstack(pts))
    return v


def course_mob(plane, seq, color=PLAN_C, width=5.0, glow=True, start="lea"):
    """A course on the streets: a bright line over a soft halo of itself."""
    core = street_path(plane, course_pieces(seq, start))
    core.set_stroke(color, width=width, opacity=1.0)
    core.joint_type = LineJointType.ROUND
    g = VGroup()
    if glow:
        halo = core.copy().set_stroke(color, width=width * 2.6, opacity=0.20)
        g.add(halo)
    g.add(core)
    g.core = core
    return g


def ride_arc(plane, i, j, bend=0.32):
    """The possible ride "after stop i, deliver order j": an arc from where i ends
    to j's restaurant. Every arc bends the same way, so i->j and j->i stay apart."""
    a, b = plane.w(stop_xy(i)), plane.w(stop_xy(j, "R"))
    return ArcBetweenPoints(a, b, angle=bend)


def _alive(m):
    """A do-nothing updater. Manim repaints, on every frame of a play, only the
    mobjects that are animated or own an updater (and whatever is drawn after the
    first of them). A mobject driven through plain attributes by ``Tween`` is
    neither: without this it would be painted once per play."""


class RideSet(VGroup):
    """The possible rides as dimmable arcs, plus each order's own leg.

    ``val[ride]`` in [0, 1] is how much of a ride is "on"; ``refresh()`` turns the
    values into stroke width and opacity. A leg shows the sum of what enters its
    order. ``Dim(rides, {...})`` animates toward new values."""

    def __init__(self, plane, rides=RIDES, color=None, base=0.0, w0=1.8, w1=6.0):
        super().__init__()
        color = mix(RELAX_C, WHITE, 0.22) if color is None else color
        # (``hue``: ``color`` is Manim's property and would repaint the children)
        self.hue, self.base, self.w0, self.w1 = ManimColor(color), base, w0, w1
        self.legs = 0.0  # 1: an order's own leg shows how much of it is delivered
        self.gain = 1.0  # all opacities times this (to let a whole plan breathe)
        self.arc = {r: ride_arc(plane, *r) for r in rides}
        self.leg = {j: street_path(plane, [leg(j)]) for j in NAMES}
        self.val = {r: 0.0 for r in rides}
        self.tint = {r: 0.0 for r in rides}  # 0: the set's colour, 1: ``hot``
        self.hot = ManimColor(PLAN_C)
        self.gone = {r: 0.0 for r in rides}  # 1: removed (drawn in red, fading)
        self.add(*self.leg.values(), *self.arc.values())
        self.add_updater(_alive)
        self.refresh()

    def refresh(self):
        inflow = {j: 0.0 for j in self.leg}
        warm = {j: 0.0 for j in self.leg}  # how much of that inflow is ``hot``
        for r, m in self.arc.items():
            v = float(np.clip(self.val[r], 0, 1))
            g = self.gone[r]
            if r[1] in inflow:
                inflow[r[1]] += v * (1 - g)
                warm[r[1]] += v * (1 - g) * self.tint[r]
            c = mix(mix(self.hue, self.hot, self.tint[r]), CUT_C, min(1.0, g * 2))
            op = (self.base + (1 - self.base) * v) * (1 - max(0.0, g * 2 - 1))
            if (
                v > 0.004
            ):  # a ride that is pointed at is fully lit, however little it is on
                op = max(op, 0.95 * self.tint[r])
            m.set_stroke(
                c,
                width=self.w0 + (self.w1 - self.w0) * v,
                opacity=self.gain * op if v > 0.004 or self.base else 0.0,
            )
        for j, m in self.leg.items():
            v = float(np.clip(inflow[j], 0, 1)) * self.legs
            # a leg wears the colour of the rides that reach it: gold in a real plan
            heat = warm[j] / inflow[j] if inflow[j] > 1e-9 else 0.0
            m.set_stroke(
                mix(self.hue, self.hot, float(np.clip(heat, 0, 1))),
                width=self.w0 + (self.w1 - self.w0) * v,
                opacity=self.gain * v,
            )
        return self


class Dim(Animation):
    """Move a ``RideSet`` toward new values: ``Dim(rides, val={...}, tint={...})``.
    Rides that are not named go to ``rest`` (default: keep their value)."""

    def __init__(
        self,
        rides,
        val=None,
        tint=None,
        gone=None,
        rest=None,
        legs=None,
        run_time=0.6,
        **kw,
    ):
        self.rs = rides
        self.goal = {
            "val": dict(val or {}),
            "tint": dict(tint or {}),
            "gone": dict(gone or {}),
        }
        self.rest, self.legs = rest, legs
        super().__init__(
            Mobject(),
            run_time=run_time,
            remover=True,
            suspend_mobject_updating=False,
            **kw,
        )

    def begin(self):
        self.start = {k: dict(getattr(self.rs, k)) for k in self.goal}
        if self.rest is not None:
            for r in self.rs.val:
                self.goal["val"].setdefault(r, self.rest)
        self.legs0 = self.rs.legs
        self.starting_mobject = Mobject()
        self.interpolate(0)

    def interpolate_mobject(self, alpha):
        a = self.rate_func(alpha)
        if self.legs is not None:
            self.rs.legs = self.legs0 + (self.legs - self.legs0) * a
        for k, goal in self.goal.items():
            cur = getattr(self.rs, k)
            for r, v in goal.items():
                cur[r] = self.start[k][r] + (v - self.start[k][r]) * a
        self.rs.refresh()


# --------------------------------------------------------------------------- #
# the table of orders (scene 2)
# --------------------------------------------------------------------------- #
class OrderTable(VGroup):
    """Eight orders as rows: dish, fee, and the delivery window on an hour-long
    axis. ``row[j]`` is the row of order j; ``bar[j]`` its window."""

    def __init__(self, w=6.3, pitch=0.43, fs=19):
        super().__init__()
        self.w, self.pitch = w, pitch
        x_name, x_fee, x_t0 = 0.0, 2.22, 2.62
        self.t0, self.t1 = x_t0, w  # the hour, left to right
        head_y = 0.0

        def tx(minute):
            return self.t0 + (self.t1 - self.t0) * minute / 60.0

        self.tx = tx
        heads = VGroup(
            line_txt("order", fs=16, color=MUTED).move_to(
                [x_name, head_y, 0], aligned_edge=LEFT
            ),
            line_txt("fee", fs=16, color=MUTED).move_to(
                [x_fee, head_y, 0], aligned_edge=RIGHT
            ),
            line_txt("may be delivered between", fs=16, color=MUTED).move_to(
                [(self.t0 + self.t1) / 2, head_y, 0]
            ),
        )
        self.heads = heads
        axis_y = head_y - 0.36
        ticks = VGroup()
        for m in (0, 15, 30, 45, 60):
            ticks.add(
                Line([tx(m), axis_y - 0.05, 0], [tx(m), axis_y + 0.05, 0]).set_stroke(
                    FAINT, 1.6
                )
            )
            if m % 30 == 0:
                lab = txt(clock(m), fs=16, color=MUTED, font=MONO)
                lab.move_to([tx(m), axis_y - 0.22, 0])
                if m == 0:
                    lab.align_to([tx(0) - 0.02, 0, 0], LEFT)
                if m == 60:
                    lab.align_to([tx(60) + 0.02, 0, 0], RIGHT)
                ticks.add(lab)
        self.axis = VGroup(
            Line([tx(0), axis_y, 0], [tx(60), axis_y, 0]).set_stroke(FAINT, 1.6), ticks
        )
        self.row, self.bar, self.label, self.fee, self.lane = {}, {}, {}, {}, {}
        y = axis_y - 0.36
        for j in NAMES:
            o = ORDERS[j]
            y -= pitch
            # line boxes: every name sits on its row's baseline, whatever its letters
            name = line_txt(j, fs=fs, color=INK, weight="MEDIUM").move_to(
                [x_name, y, 0], aligned_edge=LEFT
            )
            fee = line_txt(euro(o["pay"]), fs=fs - 1, color=INK, font=MONO).move_to(
                [x_fee, y, 0], aligned_edge=RIGHT
            )
            lane = Line([tx(0), y, 0], [tx(60), y, 0]).set_stroke(
                FAINT, width=1.2, opacity=0.7
            )
            bar = RoundedRectangle(
                width=tx(o["late"]) - tx(o["early"]),
                height=0.2,
                corner_radius=0.06,
                stroke_width=0,
            ).set_fill(WINDOW_C, opacity=0.9)
            bar.move_to([(tx(o["early"]) + tx(o["late"])) / 2, y, 0])
            self.row[j] = VGroup(name, fee, lane, bar)
            self.label[j], self.fee[j], self.lane[j], self.bar[j] = name, fee, lane, bar
        self.rows = VGroup(*self.row.values())
        self.add(heads, self.axis, self.rows)
        self.live = {j: 1.0 for j in NAMES}  # how present a row is (1) or dimmed (0)

    def y_of(self, j):
        return self.label[j].get_center()[1]

    def badge(self, j, k, color=PLAN_C):
        """The place of order j in a course: a small numbered disc before its name."""
        c = Circle(radius=0.13, stroke_width=0).set_fill(color, opacity=1.0)
        n = txt(str(k), fs=16, color=BG, weight="BOLD").move_to(c)
        return VGroup(c, n).move_to(
            [self.label[j].get_left()[0] - 0.27, self.y_of(j), 0]
        )

    def badges(self, seq, color=PLAN_C):
        return VGroup(*[self.badge(j, k + 1, color) for k, j in enumerate(seq)])

    def focus(self, seq, rt=0.4):
        """Dim the rows that are not in ``seq`` (all rows back with ``seq=None``)."""
        anims = []
        for j in NAMES:
            want = 1.0 if seq is None or j in seq else 0.0
            if want != self.live[j]:
                self.live[j] = want
                op = 1.0 if want else 0.3
                anims.append(self.label[j].animate(run_time=rt).set_opacity(op))
                anims.append(self.fee[j].animate(run_time=rt).set_opacity(op))
                anims.append(
                    self.bar[j].animate(run_time=rt).set_fill(opacity=0.9 * op)
                )
        return anims


class Readout(VGroup):
    """A small label over a big value. Both are line boxes (``line_txt``): readouts
    with the same ``fs`` placed at the same height share their two baselines,
    whatever they say. ``fresh(text)`` is a new value in place, for a value that
    changes (``holder.become(VGroup(readout.fresh(text)))``)."""

    def __init__(
        self, label, value, color=INK, fs=30, at=(0, 0), font=MONO, align=LEFT
    ):
        super().__init__()
        self._style = {"fs": fs, "color": color, "weight": "BOLD", "font": font}
        self._edge = align
        self.lab = line_txt(label, fs=16, color=MUTED)
        self.val = line_txt(value, **self._style)
        self.add(self.lab, self.val)
        self.arrange(DOWN, buff=-0.04, aligned_edge=align)
        self.move_to([at[0], at[1], 0], aligned_edge=align)

    def fresh(self, text, **style):
        return line_txt(text, **{**self._style, **style}).move_to(
            self.val, aligned_edge=self._edge
        )


def figure_line(value, label, color=INK, fs=30, at=(0, 0), lab_fs=18):
    """A big number and what it counts, on one baseline (``64  switches, one per
    possible ride``): the readout for a strip too low for a label over a value."""
    val = line_txt(value, fs=fs, color=color, weight="BOLD", font=MONO)
    lab = line_txt(label, fs=lab_fs, color=MUTED)
    row = VGroup(val, lab).arrange(RIGHT, buff=0.3)
    align_baselines(val, lab)
    return row.move_to([at[0], at[1], 0])


# --------------------------------------------------------------------------- #
# a map in a window (flat scenes where the map is not the whole frame)
# --------------------------------------------------------------------------- #
class MapWindow(Group):
    """A framed piece of the real map: ``w(metres)`` gives frame coordinates, so
    stops, rides and courses can be laid on it like on a ``MapPlane``."""

    def __init__(self, centre_m, width_m, w, h, at=(0, 0), detail=True, arr=True):
        import city

        super().__init__()
        self.origin_m, self.k = A(centre_m), w / width_m
        self.at = A([at[0], at[1]])
        px = int(round(w / config.frame_width * 1920 * 2))
        ph = int(round(px * h / w))
        img = city.texture(
            centre_m[0], centre_m[1], width_m, px, ph, detail=detail, arr=arr
        )
        self.image = ImageMobject(img)
        self.image.stretch_to_fit_width(w).stretch_to_fit_height(h)
        self.image.move_to([at[0], at[1], 0])
        self.rim = VGroup(  # hides the square corners, then draws the hairline
            RoundedRectangle(
                width=w + 0.06, height=h + 0.06, corner_radius=0.14
            ).set_stroke(BG, width=7),
            RoundedRectangle(width=w, height=h, corner_radius=0.12).set_stroke(
                FAINT, width=2
            ),
        ).move_to([at[0], at[1], 0])
        self.rim.set_fill(opacity=0)
        self.add(self.image, self.rim)

    def w(self, xy, z=0.0):
        xy = np.asarray(xy, dtype=float)
        out = np.zeros((*xy.shape[:-1], 3))
        out[..., :2] = (xy[..., :2] - self.origin_m) * self.k + self.at
        return out


# --------------------------------------------------------------------------- #
# floor and ceiling on one axis
# --------------------------------------------------------------------------- #
class GapBar(VGroup):
    """A euro axis with the two bounds of a search: the *ceiling* (what no plan can
    beat) and the *floor* (the best real plan so far), and the gap between them.

    Plain attributes, animated with ``Tween``: ``ceil``, ``floor`` (euros) and
    ``a_ceil``, ``a_floor`` (0..1: how present each marker is)."""

    def __init__(
        self,
        lo=15.0,
        hi=35.0,
        w=5.6,
        step=5,
        fs=16,
        names=("floor", "ceiling"),
        fmt=euro,
    ):
        super().__init__()
        self.lo, self.hi, self.w0, self.fmt, self.fs = lo, hi, w, fmt, fs
        self.ceil, self.floor, self.a_ceil, self.a_floor = hi, lo, 0.0, 0.0
        self.axis = Line([0, 0, 0], [w, 0, 0]).set_stroke(FAINT, width=2)
        ticks = VGroup()
        self.tick_labels = []  # (x, label): a label steps aside for a marker on it
        self.avoid, self.a_avoid = [], 1.0  # other marks under the axis (euros)
        # values that were really computed: while a marker slides between two of
        # them, its label shows the nearer one, never a number in between
        self.known = []
        v = lo
        while v <= hi + 1e-9:
            x = self.x_of(v)
            ticks.add(Line([x, -0.07, 0], [x, 0.07, 0]).set_stroke(FAINT, width=2))
            lab = txt(f"€{v:.0f}", fs=16, color=MUTED, font=MONO).move_to([x, -0.29, 0])
            self.tick_labels.append((x, lab))
            ticks.add(lab)
            v += step
        self.band = Rectangle(width=1, height=0.26, stroke_width=0)
        self.m_ceil = self._marker(RELAX_C, up=True)
        self.m_floor = self._marker(PLAN_C, up=False)
        self.n_ceil = txt(names[1], fs=fs, color=RELAX_C, weight="BOLD")
        self.n_floor = txt(names[0], fs=fs, color=PLAN_C, weight="BOLD")
        self.v_ceil, self.v_floor = VGroup(), VGroup()
        self._shown = {"ceil": None, "floor": None}
        self.add(
            self.axis,
            ticks,
            self.band,
            self.m_ceil,
            self.m_floor,
            self.n_ceil,
            self.n_floor,
            self.v_ceil,
            self.v_floor,
        )
        self.add_updater(lambda m: m.refresh())
        self.refresh()

    def x_of(self, v):
        return (
            self.w0
            * (float(np.clip(v, self.lo, self.hi)) - self.lo)
            / (self.hi - self.lo)
        )

    @staticmethod
    def _marker(color, up):
        s = 1 if up else -1
        stem = Line([0, 0, 0], [0, s * 0.30, 0]).set_stroke(color, width=3.5)
        tip = Triangle().set_fill(color, 1.0).set_stroke(width=0).scale(0.075)
        tip.rotate(PI if up else 0).move_to([0, s * 0.08, 0])
        return VGroup(stem, tip)

    def refresh(self):
        o = self.axis.get_start()
        xc, xf = self.x_of(self.ceil), self.x_of(self.floor)
        ac, af = float(np.clip(self.a_ceil, 0, 1)), float(np.clip(self.a_floor, 0, 1))
        self.m_ceil.move_to(o + [xc, 0.15, 0]).set_opacity(ac)
        self.m_floor.move_to(o + [xf, -0.15, 0]).set_opacity(af)
        for key, name, val, x, a, s, color in (
            ("ceil", self.n_ceil, self.ceil, xc, ac, 1, RELAX_C),
            ("floor", self.n_floor, self.floor, xf, af, -1, PLAN_C),
        ):
            holder = self.v_ceil if key == "ceil" else self.v_floor
            if self.known:
                val = min(self.known, key=lambda q, v=val: abs(q - v))
            text = self.fmt(val)
            if self._shown[key] != text:
                self._shown[key] = text
                holder.become(
                    VGroup(
                        txt(text, fs=self.fs + 4, color=color, font=MONO, weight="BOLD")
                    )
                )
            # labels stay inside the axis; the ceiling's hang right-aligned, the floor's left
            name.move_to(o + [x, s * 0.52, 0])
            holder.move_to(o + [x, s * 0.84, 0])
            for m in (name, holder):
                dx = max(0.0, (o[0] - 0.1) - m.get_left()[0]) - max(
                    0.0, m.get_right()[0] - (o[0] + self.w0 + 0.1)
                )
                m.shift([dx, 0, 0])
                m.set_opacity(a)
        # the floor's stem hangs through the row of tick labels: a label it would
        # strike through fades out for as long as the marker stands on it
        marks = [(xf, af), *[(self.x_of(v), self.a_avoid) for v in self.avoid]]
        for x, lab in self.tick_labels:
            hide = max(
                a * float(np.clip(1 - (abs(x - xm) - lab.width / 2 - 0.05) / 0.1, 0, 1))
                for xm, a in marks
            )
            lab.set_opacity(1.0 - hide)
        gap = max(0.0, xc - xf)
        show = ac * af
        if gap > 1e-3 and show > 0:
            self.band.stretch_to_fit_width(gap).move_to(o + [(xc + xf) / 2, 0, 0])
            self.band.set_fill(color=[PLAN_C, RELAX_C], opacity=0.34 * show)
            self.band.set_sheen_direction(RIGHT)
        else:
            self.band.set_fill(opacity=0.0)
        return self


# --------------------------------------------------------------------------- #
# the search tree
# --------------------------------------------------------------------------- #
class SearchTree(VGroup):
    """Our branch and bound, node by node, in the order it was explored.

    ``k`` (a float) is how far the search has got: node ``i`` is drawn once
    ``k >= i``. ``on_step(i)`` is called when the search reaches a new node, so the
    scene can keep a gauge and a map in step. Glyphs: a dot is a relaxation that was
    split, a gold disc a real plan, a grey cross a dead end (no plan fits), a red
    cross a branch cut by the bound."""

    def __init__(self, nodes, w, h, dy=None):
        super().__init__()
        self.nodes = nodes
        kids = {}
        for n in nodes:
            kids.setdefault(n["parent"], []).append(n)
        for v in kids.values():
            v.sort(key=lambda n: -(n["take"] or 0))  # "take" on the left
        depth = max(n["depth"] for n in nodes)
        dy = dy or h / depth
        xs, leaf = {}, [0]

        def place(n):
            ch = kids.get(n["id"], [])
            if not ch:
                xs[n["id"]] = leaf[0]
                leaf[0] += 1
            else:
                for c in ch:
                    place(c)
                xs[n["id"]] = sum(xs[c["id"]] for c in ch) / len(ch)

        place(nodes[0])
        dx = w / max(1, leaf[0] - 1)
        self.pos = {
            n["id"]: np.array(
                [(xs[n["id"]] - (leaf[0] - 1) / 2) * dx, -n["depth"] * dy, 0.0]
            )
            for n in nodes
        }
        self.edge, self.dot = {}, {}
        for n in nodes:
            i = n["id"]
            if n["parent"] is not None:
                e = Line(self.pos[n["parent"]], self.pos[i]).set_stroke(
                    MUTED, width=1.6, opacity=0.55
                )
                self.edge[i] = e
                self.add(e)
        for n in nodes:
            g = self._glyph(n).move_to(self.pos[n["id"]])
            self.dot[n["id"]] = g
            self.add(g)
        self.base = {
            m: (m.get_fill_opacity(), m.get_stroke_opacity())
            for m in self.family_members_with_points()
        }
        self.cursor = Circle(radius=0.13).set_stroke(INK, width=2.2)
        self.add(self.cursor)
        self.k, self._at, self.on_step = -1.0, None, None
        self.add_updater(_alive)
        self.refresh(force=True)

    def fit(self, x0, x1, top):
        """Put the tree's box between ``x0`` and ``x1``, its root row at ``top``."""
        self.cursor.move_to(self.dot[0])
        self.shift(
            [(x0 + x1) / 2 - self.get_center()[0], top - self.dot[0].get_center()[1], 0]
        )
        self.pos = {i: d.get_center() for i, d in self.dot.items()}
        return self

    @staticmethod
    def _glyph(n):
        kind = n["kind"]
        if kind == "branch":
            return Circle(radius=0.052, stroke_width=0).set_fill(RELAX_C, 1.0)
        if kind == "plan":
            return VGroup(
                Circle(radius=0.14, stroke_width=0).set_fill(PLAN_C, 0.25),
                Circle(radius=0.085).set_stroke(BG, width=1.5).set_fill(PLAN_C, 1.0),
            )
        c = MUTED if kind == "infeasible" else CUT_C
        s = 0.05
        return VGroup(
            Line([-s, -s, 0], [s, s, 0]), Line([-s, s, 0], [s, -s, 0])
        ).set_stroke(c, width=2.4)

    def _show(self, i, a):
        for m in [
            *self.dot[i].family_members_with_points(),
            *([self.edge[i]] if i in self.edge else []),
        ]:
            fo, so = self.base[m]
            m.set_fill(opacity=fo * a)
            m.set_stroke(opacity=so * a)

    def refresh(self, force=False):
        at = int(np.clip(math.floor(self.k), -1, len(self.nodes) - 1))
        if force:
            for n in self.nodes:
                self._show(n["id"], 1.0 if n["id"] <= at else 0.0)
        elif at != self._at:
            lo, hi = sorted((self._at if self._at is not None else -1, at))
            for i in range(max(0, lo), hi + 1):
                self._show(i, 1.0 if i <= at else 0.0)
        frac = self.k - math.floor(self.k)
        if 0 <= at < len(self.nodes):
            self._show(at, min(1.0, 0.35 + frac * 2.5))
            self.cursor.move_to(self.dot[at]).set_stroke(opacity=1.0)
        else:
            self.cursor.set_stroke(opacity=0.0)
        if at != self._at:
            self._at = at
            if self.on_step and at >= 0:
                self.on_step(at)
        return self

    def point(self, i):
        return self.dot[i].get_center()


# --------------------------------------------------------------------------- #
# one decision variable, as a control
# --------------------------------------------------------------------------- #
class Dimmer(VGroup):
    """A switch with two positions (0 or 1) that can become a dimmer (anything in
    between). ``v`` is its value; ``Tween(dimmer, v=0.52)`` slides the knob."""

    def __init__(self, w=1.9, h=0.40, fs=18):
        super().__init__()
        self.w0, self.h0, self.v, self.fs = w, h, 0.0, fs
        self.track = RoundedRectangle(width=w, height=h, corner_radius=h / 2)
        self.track.set_stroke(FAINT, width=2).set_fill(PANEL, 1.0)
        self.lit = RoundedRectangle(
            width=h, height=h, corner_radius=h / 2, stroke_width=0
        )
        self.knob = Circle(radius=h / 2 - 0.045, stroke_width=0).set_fill(INK, 1.0)
        zero = txt("0", fs=16, color=MUTED, font=MONO).next_to(
            self.track, LEFT, buff=0.16
        )
        one = txt("1", fs=16, color=MUTED, font=MONO).next_to(
            self.track, RIGHT, buff=0.16
        )
        self.value = VGroup()
        self._shown = None
        # ``hue``, not ``color``: on a VGroup ``color`` is Manim's property, and
        # setting it repaints every child (the track, the knob, the digits)
        self.hue = ManimColor(PLAN_C)
        self.add(self.track, self.lit, self.knob, zero, one, self.value)
        self.add_updater(lambda m: m.refresh())
        self.refresh()

    def refresh(self):
        v = float(np.clip(self.v, 0, 1))
        left = self.track.get_left() + RIGHT * self.h0 / 2
        x = (self.w0 - self.h0) * v
        self.knob.move_to(left + RIGHT * x)
        # rebuilt, not stretched: a stretched pill has elliptical ends
        self.lit.become(
            RoundedRectangle(
                width=self.h0 + x,
                height=self.h0,
                corner_radius=self.h0 / 2,
                stroke_width=0,
            )
            .set_fill(self.hue, opacity=0.25 + 0.5 * v)
            .move_to(left + RIGHT * x / 2)
        )
        text = f"{v:.2f}".rstrip("0").rstrip(".") if v not in (0.0, 1.0) else f"{v:.0f}"
        if text != self._shown:
            self._shown = text
            self.value.become(
                VGroup(txt(text, fs=self.fs + 4, color=INK, font=MONO, weight="BOLD"))
            )
        self.value.next_to(self.knob, UP, buff=0.16)
        return self


# --------------------------------------------------------------------------- #
# a solver's log, as the terminal shows it
# --------------------------------------------------------------------------- #
def read_log(name):
    """The lines of ``assets/gurobi_<name>.txt``: Gurobi's log, verbatim (minus the
    one line that names the log file's local path)."""
    return (HERE / "assets" / f"gurobi_{name}.txt").read_text().splitlines()


def log_line(lines, start):
    """The first line of a log that begins with ``start`` (so nothing is retyped)."""
    return next(s for s in lines if s.startswith(start))


def wrap(s, cols):
    """Break a long line at a space, the way a narrow terminal would."""
    out = []
    while len(s) > cols:
        k = s.rfind(" ", 0, cols + 1)
        out.append(s[:k])
        s = "    " + s[k + 1 :]
    return [*out, s]


class LogPanel(VGroup):
    """A terminal window showing real log lines. Plain attributes, animated with
    ``Tween``: ``shown`` (how many lines have been printed) and ``scroll`` (the
    index of the first visible line). ``mark(i, c0, c1, color)`` puts a highlight
    behind columns c0..c1 of line i; animate its ``a`` to switch it on."""

    def __init__(self, lines, cols=80, rows=15, fs=16, title="", pitch=0.29):
        super().__init__()
        probe = txt("M" * 40, fs=fs, font=MONO)
        self.adv = probe.width / 40
        self.cols, self.rows, self.pitch, self.lines = cols, rows, pitch, lines
        self.w0, self.h0 = cols * self.adv + 0.7, rows * pitch + 0.78
        self.bg = RoundedRectangle(width=self.w0, height=self.h0, corner_radius=0.16)
        self.bg.set_stroke(FAINT, width=2).set_fill(CODE_BG, 1.0)
        bar = RoundedRectangle(
            width=self.w0, height=0.46, corner_radius=0.16, stroke_width=0
        )
        bar.set_fill(CODE_BAR, 1.0).align_to(self.bg, UP)
        dots = VGroup(
            *[Dot(radius=0.045, color=c) for c in ("#FF5F57", "#FEBC2E", "#28C840")]
        )
        dots.arrange(RIGHT, buff=0.11).move_to(
            [self.bg.get_left()[0] + 0.42, bar.get_center()[1], 0]
        )
        ttl = txt(title, fs=16, color=MUTED, font=MONO).move_to(bar)
        self.frame = VGroup(self.bg, bar, dots, ttl)
        self.text, self.lead = [], []
        for s in lines:
            body = s.strip()
            self.lead.append(len(s) - len(s.lstrip()))
            if not body:
                self.text.append(None)
                continue
            color = MUTED if body == "…" else PLAIN
            self.text.append(line_txt(s.rstrip(), fs=fs, color=color, font=MONO))
        self.marks = VGroup()
        self.shown, self.scroll, self.clock = 0.0, 0.0, 0.0
        self.caret = Rectangle(
            width=self.adv * 0.86, height=pitch * 0.7, stroke_width=0
        ).set_fill(PLAIN, 0.0)
        self.add(
            self.frame, self.marks, *[m for m in self.text if m is not None], self.caret
        )
        self.add_updater(lambda m, dt: m.refresh(dt))
        self.refresh()

    def x_col(self, c):
        return self.bg.get_left()[0] + 0.35 + c * self.adv

    def y_row(self, i):
        return self.bg.get_top()[1] - 0.62 - (i - self.scroll) * self.pitch

    def _window(self, i):
        d = i - self.scroll  # 0 = the first visible row
        return float(
            np.clip(d * 2.2 + 1, 0, 1) * np.clip((self.rows - 1 - d) * 2.2 + 1, 0, 1)
        )

    def place(self, x, y):
        """Centre the window (not its hidden lines) on (x, y)."""
        self.shift(np.array([x, y, 0.0]) - self.bg.get_center())
        return self.refresh()

    def fade(self, darkness=0.5, family=True):
        """(Manim's fade, for the wipe: the caret must not blink back in.)"""
        self.clear_updaters()
        return super().fade(darkness, family)

    def mark(self, i, c0, c1, color, op=0.30, pad=0.03):
        r = RoundedRectangle(
            width=(c1 - c0) * self.adv + 2 * pad,
            height=self.pitch * 0.86,
            corner_radius=0.05,
            stroke_width=0,
        )
        r.set_fill(color, opacity=0.0)
        r.row, r.c0, r.c1, r.a, r.op = i, c0, c1, 0.0, op
        self.marks.add(r)
        return r

    def find(self, i, s, nth=0):
        """Columns (c0, c1) of the nth occurrence of ``s`` in line i."""
        k = -1
        for _ in range(nth + 1):
            k = self.lines[i].index(s, k + 1)
        return k, k + len(s)

    def refresh(self, dt=0.0):
        self.clock += dt
        for i, m in enumerate(self.text):
            if m is None:
                continue
            a = float(np.clip(self.shown - i, 0, 1)) * self._window(i)
            m.move_to([self.x_col(self.lead[i]), self.y_row(i), 0], aligned_edge=LEFT)
            m.set_opacity(a)
        swing = 0.8 + 0.2 * math.cos(TAU * self.clock / 1.8)
        for r in self.marks:
            r.move_to([(self.x_col(r.c0) + self.x_col(r.c1)) / 2, self.y_row(r.row), 0])
            r.set_fill(
                opacity=r.op * swing * float(np.clip(r.a, 0, 1)) * self._window(r.row)
            )
        # the caret waits after the last printed line, and blinks
        last = int(np.clip(math.ceil(self.shown) - 1, 0, len(self.lines) - 1))
        on = self.shown > 0.5 and (self.clock % 1.1) < 0.62
        self.caret.move_to(
            [self.x_col(len(self.lines[last].rstrip()) + 1), self.y_row(last), 0]
        )
        self.caret.set_fill(opacity=0.8 * self._window(last) if on else 0.0)
        return self


# --------------------------------------------------------------------------- #
# the two bounds of a real search, over time
# --------------------------------------------------------------------------- #
class GapChart(VGroup):
    """Incumbent (rising) and best bound (falling) against the solver's clock.
    ``t`` (seconds) is how much of the search has been drawn."""

    def __init__(
        self, plans, trace, t_end, w=6.6, h=3.3, y0=120.0, y1=186.0, y_step=20
    ):
        super().__init__()
        self.w0, self.h0, self.y0, self.y1, self.t_end = w, h, y0, y1, t_end
        inc = [(p["time"], p["obj"]) for p in plans if p["obj"] > 0]
        top = max(b for _, _, b, _ in trace if b < 1e3)
        bnd = [(t, b) for t, _, b, _ in trace if b <= top + 1e-9]
        self.inc, self.bnd = np.array(inc), np.array(bnd)
        self.nodes = np.array([(t, n) for t, _, _, n in trace])
        self.t = 0.0
        ax = VGroup(Line([0, 0, 0], [w, 0, 0]), Line([0, 0, 0], [0, h, 0])).set_stroke(
            FAINT, width=2
        )
        ticks = VGroup()
        for s in range(int(t_end) + 1):
            x = w * s / t_end
            ticks.add(Line([x, -0.06, 0], [x, 0.06, 0]).set_stroke(FAINT, width=2))
            ticks.add(
                txt(f"{s} s", fs=16, color=MUTED, font=MONO).move_to([x, -0.28, 0])
            )
        v = math.ceil(y0 / y_step) * y_step
        while v <= y1:
            y = self.y_of(v)
            ticks.add(
                Line([0, y, 0], [w, y, 0]).set_stroke(FAINT, width=1, opacity=0.45)
            )
            ticks.add(
                txt(f"€{v:.0f}", fs=16, color=MUTED, font=MONO).move_to(
                    [-0.12, y, 0], aligned_edge=RIGHT
                )
            )
            v += y_step
        self.axes = VGroup(ax, ticks)
        self.gap = (
            VMobject()
            .set_stroke(width=0)
            .set_fill(color=[PLAN_C, RELAX_C], opacity=0.16)
        )
        self.l_inc = VMobject().set_stroke(PLAN_C, width=4)
        self.l_bnd = VMobject().set_stroke(RELAX_C, width=4)
        self.d_inc = Dot(radius=0.07, color=PLAN_C)
        self.d_bnd = Dot(radius=0.07, color=RELAX_C)
        self.add(self.axes, self.gap, self.l_bnd, self.l_inc, self.d_bnd, self.d_inc)
        self.add_updater(lambda m: m.refresh())
        self.refresh()

    def y_of(self, v):
        return (
            self.h0
            * (float(np.clip(v, self.y0, self.y1)) - self.y0)
            / (self.y1 - self.y0)
        )

    def at(self, series, t):
        k = int(np.searchsorted(series[:, 0], t, side="right")) - 1
        return None if k < 0 else float(series[k, 1])

    def gap_at(self, t):
        a, b = self.at(self.inc, t), self.at(self.bnd, t)
        return None if a is None or b is None or a <= 0 else (b - a) / a

    def _steps(self, series, t):
        pts, last = [], None
        for ti, v in series:
            if ti > t:
                break
            x, y = self.w0 * ti / self.t_end, self.y_of(v)
            if last is not None:
                pts.append([x, last, 0])
            pts.append([x, y, 0])
            last = y
        if last is not None:
            pts.append([self.w0 * min(t, self.t_end) / self.t_end, last, 0])
        return pts

    def refresh(self):
        o = self.axes[0][0].get_start()
        t = float(np.clip(self.t, 0, self.t_end))
        both = []
        for series, line, dot in (
            (self.inc, self.l_inc, self.d_inc),
            (self.bnd, self.l_bnd, self.d_bnd),
        ):
            pts = self._steps(series, t)
            both.append(pts)
            if len(pts) >= 2:
                line.set_points_as_corners([o + p for p in pts])
                dot.move_to(o + pts[-1]).set_opacity(1.0)
            else:
                line.set_points_as_corners([o, o])
                dot.set_opacity(0.0)
        if all(len(p) >= 2 for p in both):
            x0 = max(both[0][0][0], both[1][0][0])
            lo = [p for p in both[0] if p[0] >= x0 - 1e-9]
            hi = [p for p in both[1] if p[0] >= x0 - 1e-9]
            self.gap.set_points_as_corners([o + p for p in [*lo, *hi[::-1], lo[0]]])
            self.gap.set_fill(color=[PLAN_C, RELAX_C], opacity=0.16)
            self.gap.set_sheen_direction(UP)
        else:
            self.gap.set_points_as_corners([o, o])
        return self


# --------------------------------------------------------------------------- #
# a district: several couriers, a plan that changes
# --------------------------------------------------------------------------- #
class District(VGroup):
    """One zone's couriers and orders on a map, and the courses of any plan.
    ``show(courses)`` redraws the plan; orders that the plan delivers are lit."""

    def __init__(self, plane, zone, k=0.55, color=PLAN_C, width=2.2):
        super().__init__()
        self.plane, self.zone, self.hue, self.lw = (
            plane,
            zone,
            color,
            width,
        )  # (``width`` and ``color`` are Manim's)
        w = plane.w
        self.start = {c["name"]: A(c["start"]) for c in zone["couriers"]}
        self.R = {o["name"]: A(o["R"]) for o in zone["orders"]}
        self.C = {o["name"]: A(o["C"]) for o in zone["orders"]}
        self.marks = {}
        for j in self.R:
            link = Line(w(self.R[j]), w(self.C[j])).set_stroke(
                LINK_C, width=1.1, opacity=0.5
            )
            r = resto_marker(w(self.R[j]), s=0.19 * k).set_stroke(width=1.6)
            c = home_marker(w(self.C[j]), r=0.085 * k).set_stroke(width=1.6)
            self.marks[j] = VGroup(link, r, c)
        self.orders = VGroup(*self.marks.values())
        self.couriers = VGroup(
            *[courier_marker(w(p), r=0.13 * k) for p in self.start.values()]
        )
        self.paths = VGroup()
        self.add(self.paths, self.orders, self.couriers)
        self.add_updater(_alive)
        self.tracks = [np.array(c["v"], dtype=float) for c in zone["couriers"]]

    def ride(self, minutes_per_second):
        """From now on the couriers move along their final courses (a time lapse)."""
        self.now = 0.0

        def tick(m, dt):
            m.now = min(60.0, m.now + dt * minutes_per_second)
            for mark, v in zip(m.couriers, m.tracks, strict=True):
                x = np.interp(m.now, v[:, 0], v[:, 1])
                y = np.interp(m.now, v[:, 0], v[:, 2])
                mark.move_to(m.plane.w(np.array([x, y])))

        self.add_updater(tick)
        return self

    def web(self, color, width=0.7, opacity=0.22):
        """Every possible ride of the zone's model, as one faint mobject."""
        w = self.plane.w
        lines = VMobject()
        for key in self.zone["mins"]:
            i, j = key.split("|")
            a = w(self.start[i]) if i in self.start else w(self.C[i])
            lines.start_new_path(a)
            lines.add_line_to(w(self.R[j]))
        return lines.set_stroke(color, width=width, opacity=opacity)

    def course(self, courier, seq):
        polys, i = [], courier
        for j in seq:
            polys += [A(self.zone["approach"][f"{i}|{j}"]), A(self.zone["leg"][j])]
            i = j
        m = street_path(self.plane, polys)
        m.set_stroke(self.hue, width=self.lw, opacity=0.9)
        m.joint_type = LineJointType.ROUND
        return m

    def show(self, courses):
        self.paths.become(
            VGroup(*[self.course(c, seq) for c, seq in courses.items() if seq])
        )
        done = {j for seq in courses.values() for j in seq}
        for j, g in self.marks.items():
            on = j in done
            g[1].set_stroke(STOP_C if on else MUTED, opacity=1.0 if on else 0.55)
            g[2].set_stroke(STOP_C if on else MUTED, opacity=1.0 if on else 0.55)
        return self


# --------------------------------------------------------------------------- #
# the model, as code
# --------------------------------------------------------------------------- #
def model_lines():
    """The model block of ``demo/course.py`` (what ``model.solve_gurobi`` runs),
    without the line that creates the model object."""
    src = (HERE / "demo" / "course.py").read_text().splitlines()
    a = next(k for k, s in enumerate(src) if s.startswith("# --- model"))
    b = next(k for k, s in enumerate(src) if s.startswith("# --- end of model"))
    block = src[a + 1 : b]
    assert block[0].startswith("m = gp.Model")
    return block[1:]


CODE_COLORS = {
    "GRB.BINARY": NUM, "GRB.MAXIMIZE": NUM, "addVars": FUNC, "setObjective": FUNC,
    "addConstrs": FUNC, "quicksum": FUNC, "optimize": FUNC, ".sum": FUNC,
    " for ": KW, "for ": KW, " in ": KW, '"*"': STR, ">>": GOLD, "<=": KW, ">=": KW, "==": KW,
}  # fmt: skip


class CodePanel(VGroup):
    """An editor window with real code, compact enough for a HUD column.

    ``line[i]`` are the lines; ``focus(idxs)`` returns the animations that leave
    only those lines bright; ``bar(idxs)`` is a highlight spanning them."""

    def __init__(self, lines, title="course.py", fs=16, pitch=0.29, cols=None):
        super().__init__()
        probe = txt("M" * 40, fs=fs, font=MONO)
        adv = probe.width / 40
        cols = cols or max(len(s) for s in lines)
        self.w0, self.h0, self.pitch = (
            cols * adv + 0.7,
            len(lines) * pitch + 0.74,
            pitch,
        )
        self.bg = RoundedRectangle(width=self.w0, height=self.h0, corner_radius=0.16)
        self.bg.set_stroke(FAINT, width=2).set_fill(CODE_BG, 1.0)
        bar = RoundedRectangle(
            width=self.w0, height=0.44, corner_radius=0.16, stroke_width=0
        )
        bar.set_fill(CODE_BAR, 1.0).align_to(self.bg, UP)
        dots = VGroup(
            *[Dot(radius=0.045, color=c) for c in ("#FF5F57", "#FEBC2E", "#28C840")]
        )
        dots.arrange(RIGHT, buff=0.11).move_to(
            [self.bg.get_left()[0] + 0.42, bar.get_center()[1], 0]
        )
        ttl = txt(title, fs=16, color=MUTED, font=MONO).move_to(bar)
        self.frame = VGroup(self.bg, bar, dots, ttl)
        self.line = []
        x0, y0 = (
            self.bg.get_left()[0] + 0.35,
            self.bg.get_top()[1] - 0.44 - 0.14 - pitch / 2,
        )
        for i, s in enumerate(lines):
            lead = len(s) - len(s.lstrip())
            m = line_txt(
                s.strip(),
                fs=fs,
                color=PLAIN,
                font=MONO,
                t2c=safe_t2c(s.strip(), CODE_COLORS),
            )
            m.move_to([x0 + lead * adv, y0 - i * pitch, 0], aligned_edge=LEFT)
            self.line.append(m)
        self.code = VGroup(*self.line)
        self.add(self.frame, self.code)
        self.level = [1.0] * len(lines)

    def focus(self, idxs, rest=0.32, rt=0.4):
        """Animations: lines ``idxs`` bright, lines already shown but not in
        ``idxs`` at ``rest``, lines never shown stay hidden."""
        anims = []
        for i, m in enumerate(self.line):
            want = 1.0 if i in idxs else (rest if self.level[i] > 0 else 0.0)
            if want != self.level[i]:
                self.level[i] = want
                anims.append(m.animate(run_time=rt).set_opacity(want))
        return anims

    def hide_all(self):
        for i, m in enumerate(self.line):
            m.set_opacity(0.0)
            self.level[i] = 0.0
        return self

    def bar(self, idxs, color=GOLD, op=0.14):
        top = self.line[min(idxs)].get_center()[1] + self.pitch / 2
        bot = self.line[max(idxs)].get_center()[1] - self.pitch / 2
        r = RoundedRectangle(
            width=self.w0 - 0.3, height=top - bot, corner_radius=0.07, stroke_width=0
        )
        r.set_fill(color, opacity=op)
        return r.move_to([self.bg.get_center()[0], (top + bot) / 2, 0])

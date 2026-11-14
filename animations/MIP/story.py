"""story.py: the film's cast, built on the real city (bake time only).

* ``World``: the street graph of Paris and its restaurants (OpenStreetMap);
* ``hero``: Lea, one hour, eight orders around her in the Marais;
* ``zone_instance``: every courier and order of one arrondissement;
* ``timeline``: a course as timed movement on real streets.

What is real: streets, ride times (shortest paths at 15 km/h), restaurant locations
and their cuisine. What is invented (seeded): which restaurants have an order, the
customers' addresses (street nodes drawn at random), fees, ready times, deadlines,
where the couriers stand at minute 0.
"""

from __future__ import annotations

import numpy as np

import city
import model
import osm
import routing

# what a restaurant's ``cuisine`` tag puts on the order's label
DISH = {
    "pizza": "pizza",
    "sushi": "sushi",
    "burger": "burger",
    "crepe": "crêpes",
    "thai": "pad thai",
    "indian": "curry",
    "lebanese": "falafel",
    "korean": "bibimbap",
    "vietnamese": "pho",
    "japanese": "ramen",
    "mexican": "tacos",
    "kebab": "kebab",
    "chinese": "noodles",
    "italian": "pasta",
    "poke": "poke",
    "couscous": "couscous",
    "bagel": "bagel",
}
FEE_BASE, FEE_PER_KM = 2.9, 1.4  # euros: an invented fee grid
HERO_ZONE = ((48.8550, 2.3380), (48.8680, 2.3680))  # the Marais, Les Halles to Temple
HERO_START = (48.8612, 2.3530)  # rue Rambuteau


class World:
    def __init__(self):
        roads = city.load_roads()
        s, w, n, e = osm.BBOX_PARIS
        x0, y0 = osm.to_xy(s, w)
        x1, y1 = osm.to_xy(n, e)
        self.graph = routing.StreetGraph(
            roads, box=(x0 - 300, y0 - 300, x1 + 300, y1 + 300)
        )
        food = osm.overpass("food", osm.queries()["food"])["elements"]
        self.food_xy = np.array([osm.to_xy(el["lat"], el["lon"]) for el in food])
        self.food_cuisine = [
            el.get("tags", {}).get("cuisine", "").split(";")[0].strip() for el in food
        ]
        self.food_node, self.food_off = self.graph.snap(self.food_xy)
        self.core_xy = self.graph.xy[self.graph.core]
        self.geo = city.geometry()
        # which arrondissement (1..20, 0 = outside Paris) every street node is in
        self.arr_of = np.zeros(len(self.graph.xy), int)
        self.food_arr = np.zeros(len(self.food_xy), int)
        for a in range(1, 21):
            rings = self.geo.arrondissement(a)
            self.arr_of[self.graph.core[inside(rings, self.core_xy)]] = a
            self.food_arr[inside(rings, self.food_xy)] = a

    def in_box(self, xy, zone):
        (s, w), (n, e) = zone
        x0, y0 = osm.to_xy(s, w)
        x1, y1 = osm.to_xy(n, e)
        return (xy[:, 0] >= x0) & (xy[:, 0] <= x1) & (xy[:, 1] >= y0) & (xy[:, 1] <= y1)


def inside(rings, pts):
    """Even-odd point-in-polygon test of ``pts`` (n, 2) against a list of rings."""
    x, y = pts[:, 0], pts[:, 1]
    odd = np.zeros(len(pts), bool)
    for r in rings:
        x0, y0 = r[:-1, 0][:, None], r[:-1, 1][:, None]
        x1, y1 = r[1:, 0][:, None], r[1:, 1][:, None]
        cross = (y0 > y) != (y1 > y)
        with np.errstate(divide="ignore", invalid="ignore"):
            xs = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
        odd ^= (cross & (x < xs)).sum(axis=0) % 2 == 1
    return odd


def simplify(poly, tol=1.5):
    """Douglas-Peucker: drop vertices closer than ``tol`` metres to the line."""
    poly = np.asarray(poly, dtype=float)
    if len(poly) < 3:
        return poly
    keep = np.zeros(len(poly), bool)
    keep[[0, -1]] = True
    stack = [(0, len(poly) - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        p, q = poly[a], poly[b]
        d = q - p
        n = np.hypot(*d)
        seg = poly[a + 1 : b] - p
        if n < 1e-9:
            dist = np.hypot(seg[:, 0], seg[:, 1])
        else:
            dist = np.abs(seg[:, 0] * d[1] - seg[:, 1] * d[0]) / n
        k = int(np.argmax(dist))
        if dist[k] > tol:
            keep[a + 1 + k] = True
            stack += [(a, a + 1 + k), (a + 1 + k, b)]
    return poly[keep]


class Cast:
    """An instance and where it lives: nodes, coordinates and street paths."""

    def __init__(self, world, courier_names, courier_nodes, orders):
        """``orders``: dicts with name, R, C (street nodes), ready, late_slack,
        bonus, cuisine."""
        g = world.graph
        self.world, self.orders_raw = world, orders
        k, n = len(courier_nodes), len(orders)
        nodes = [*courier_nodes, *[o["R"] for o in orders], *[o["C"] for o in orders]]
        self.nodes = nodes
        self.minutes, self.path = g.table(nodes)
        self.ci = {c: a for a, c in enumerate(courier_names)}
        self.ri = {o["name"]: k + a for a, o in enumerate(orders)}
        self.cui = {o["name"]: k + n + a for a, o in enumerate(orders)}
        pay, early, late, mins = {}, {}, {}, {}
        self.info = {}
        for o in orders:
            j = o["name"]
            ride = self.minutes[self.ri[j], self.cui[j]]
            km = routing.length(self.path(self.ri[j], self.cui[j])) / 1000
            pay[j] = round(FEE_BASE + FEE_PER_KM * km + o["bonus"], 1)
            early[j] = o["ready"] + model.PICKUP + ride + model.DROP
            late[j] = float(min(early[j] + o["late_slack"], model.SHIFT))
            self.info[j] = {"ride": float(ride), "km": km}
            for c in courier_names:
                mins[c, j] = (
                    self.minutes[self.ci[c], self.ri[j]]
                    + model.PICKUP
                    + ride
                    + model.DROP
                )
            for o2 in orders:
                i = o2["name"]
                if i != j:
                    mins[i, j] = (
                        self.minutes[self.cui[i], self.ri[j]]
                        + model.PICKUP
                        + ride
                        + model.DROP
                    )
        # an order nobody could deliver in time, even alone, is not an order
        ok = [o["name"] for o in orders if early[o["name"]] <= late[o["name"]] + 1e-9]
        assert len(ok) == len(orders), "an order has an empty window"
        self.inst = model.Instance(
            list(courier_names), [o["name"] for o in orders], pay, mins, early, late
        )

    # ---- geometry ----------------------------------------------------------- #
    def xy(self, stop, end="C"):
        """Where a stop is: a courier's start, or an order's restaurant (R) or
        customer (C)."""
        g = self.world.graph
        if stop in self.ci:
            return g.xy[self.nodes[self.ci[stop]]]
        return g.xy[self.nodes[(self.ri if end == "R" else self.cui)[stop]]]

    def approach(self, i, j):
        """The street path from stop i (a courier, or i's customer) to j's restaurant."""
        a = self.ci[i] if i in self.ci else self.cui[i]
        return self.path(a, self.ri[j])

    def leg(self, j):
        """The street path from j's restaurant to j's customer."""
        return self.path(self.ri[j], self.cui[j])

    def approach_minutes(self, i, j):
        a = self.ci[i] if i in self.ci else self.cui[i]
        return float(self.minutes[a, self.ri[j]])

    # ---- a course as movement ---------------------------------------------- #
    def timeline(self, courier, seq):
        """The course ridden as early as possible: vertices ``(minute, x, y)`` and
        the events (arrive / pickup / deliver) with their minute."""
        inst = self.inst
        ready = {o["name"]: o["ready"] for o in self.orders_raw}
        t, i = 0.0, courier
        verts = [(0.0, *self.xy(courier))]
        events = []

        def ride(poly, dur):
            nonlocal t
            poly = simplify(poly)
            seg = np.hypot(*np.diff(poly, axis=0).T)
            total = seg.sum()
            acc = np.cumsum(seg) / total if total > 0 else np.ones(len(seg))
            for p, a in zip(poly[1:], acc, strict=True):
                verts.append((t + dur * float(a), float(p[0]), float(p[1])))
            t += dur

        for j in seq:
            ride(self.approach(i, j), self.approach_minutes(i, j))
            events.append(("arrive", j, t))
            t = max(t, ready[j]) + model.PICKUP
            verts.append((t, *self.xy(j, "R")))
            events.append(("pickup", j, t))
            ride(self.leg(j), self.info[j]["ride"])
            t += model.DROP
            verts.append((t, *self.xy(j, "C")))
            events.append(("deliver", j, t))
            i = j
        expect = model.timing(inst, courier, seq)
        got = [e[2] for e in events if e[0] == "deliver"]
        assert expect is not None and np.allclose(got, expect, atol=1e-6), (got, expect)
        return np.array(verts), events

    # ---- export --------------------------------------------------------------- #
    def order_rows(self):
        inst = self.inst
        rows = []
        for o in self.orders_raw:
            j = o["name"]
            rows.append(
                {
                    "name": j,
                    "cuisine": o.get("cuisine", ""),
                    "R": _pt(self.xy(j, "R")),
                    "C": _pt(self.xy(j, "C")),
                    "pay": inst.pay[j],
                    "ready": int(o["ready"]),
                    # full precision: these two and ``mins`` are the instance a
                    # reader can solve again (demo/course.py)
                    "early": float(inst.early[j]),
                    "late": float(inst.late[j]),
                    "ride": round(self.info[j]["ride"], 3),
                    "km": round(self.info[j]["km"], 3),
                }
            )
        return rows


def _pt(p):
    return [round(float(p[0]), 1), round(float(p[1]), 1)]


def pts(poly, tol=1.5):
    return [[round(float(x), 1), round(float(y), 1)] for x, y in simplify(poly, tol)]


# --------------------------------------------------------------------------- #
# Lea's hour
# --------------------------------------------------------------------------- #
def hero(world, seed, n=8, sep=170.0, crow=(380.0, 1500.0), slack=(10, 21)):
    """One courier in the Marais and ``n`` orders around her, all with a different
    dish. Stops keep ``sep`` metres apart so the map stays readable."""
    rng = np.random.default_rng(seed)
    g = world.graph
    known = np.array([c in DISH for c in world.food_cuisine])
    pool = np.flatnonzero(world.in_box(world.food_xy, HERO_ZONE) & known)
    homes = g.core[world.in_box(world.core_xy, HERO_ZONE)]
    lea = int(g.snap(np.array([osm.to_xy(*HERO_START)]))[0][0])
    placed, used, picked = [g.xy[lea]], set(), []
    for _ in range(20000):
        if len(picked) == n:
            break
        k = int(pool[rng.integers(len(pool))])
        dish = DISH[world.food_cuisine[k]]
        if dish in used:
            continue
        r, c = int(world.food_node[k]), int(homes[rng.integers(len(homes))])
        if not crow[0] <= np.hypot(*(g.xy[r] - g.xy[c])) <= crow[1]:
            continue
        if min(min(np.hypot(*(g.xy[q] - p)) for p in placed) for q in (r, c)) < sep:
            continue
        placed += [g.xy[r], g.xy[c]]
        used.add(dish)
        picked.append((dish, world.food_cuisine[k], r, c))
    assert len(picked) == n
    ready = rng.permutation([0, 0, 5, 10, 15, 20, 25, 30][:n])
    bonus = rng.permutation([0, 0, 0, 0.5, 1.0, 1.0, 1.5, 2.5][:n])
    orders = [
        {
            "name": dish,
            "cuisine": cuisine,
            "R": r,
            "C": c,
            "ready": int(ready[a]),
            "bonus": float(bonus[a]),
            "late_slack": int(rng.integers(*slack)),
        }
        for a, (dish, cuisine, r, c) in enumerate(picked)
    ]
    return Cast(world, ["lea"], [lea], orders)


# --------------------------------------------------------------------------- #
# one arrondissement
# --------------------------------------------------------------------------- #
def zone_instance(world, arr, k, n, seed, crow=(380.0, 1800.0), slack=(10, 21)):
    """``k`` couriers and ``n`` orders of arrondissement ``arr``: restaurants and
    couriers inside it, customers within riding distance (possibly next door)."""
    rng = np.random.default_rng(seed)
    g = world.graph
    pool = np.flatnonzero(world.food_arr == arr)
    homes = np.flatnonzero(world.arr_of == arr)
    in_paris = world.arr_of > 0
    couriers = [int(homes[rng.integers(len(homes))]) for _ in range(k)]
    orders = []
    for _ in range(100000):
        if len(orders) == n:
            break
        f = int(pool[rng.integers(len(pool))])
        r = int(world.food_node[f])
        # a customer somewhere around the restaurant
        ang, dist = rng.uniform(0, 2 * np.pi), rng.uniform(*crow)
        target = g.xy[r] + dist * np.array([np.cos(ang), np.sin(ang)])
        c = int(g.snap(target[None, :])[0][0])
        if not in_paris[c] or not crow[0] <= np.hypot(*(g.xy[r] - g.xy[c])) <= crow[1]:
            continue
        orders.append(
            {
                "name": f"o{len(orders):02d}",
                "cuisine": world.food_cuisine[f],
                "R": r,
                "C": c,
                "ready": int(rng.integers(0, 9)) * 5,
                "bonus": float(rng.choice([0, 0, 0, 0.5, 1.0, 1.5, 2.5])),
                "late_slack": int(rng.integers(*slack)),
            }
        )
    assert len(orders) == n
    return Cast(world, [f"c{a}" for a in range(k)], couriers, orders)

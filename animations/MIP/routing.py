"""routing.py: ride times on the real street network of Paris (bake time only).

The graph is OpenStreetMap's: one node per street node, one directed edge per pair
of consecutive nodes of a way that a bicycle may ride. Rules, kept deliberately
simple and stated in the README:

* no motorways or trunk roads (the ring road), nothing tagged ``bicycle=no`` or
  private;
* one-way streets are one-way for bikes too, unless OpenStreetMap says cyclists may
  ride against the traffic (``oneway:bicycle=no`` or an ``opposite`` cycle lane);
* 15 km/h everywhere, 9 km/h in pedestrian streets. No traffic lights, no slopes.

``StreetGraph.table`` returns ride times in minutes and the street path of every
pair, by Dijkstra (``scipy.sparse.csgraph``).
"""

from __future__ import annotations

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

SPEED = 250.0  # metres per minute = 15 km/h
SPEED_PEDESTRIAN = 150.0  # 9 km/h where cyclists share the street with walkers
NO_BIKES = ("motorway", "motorway_link", "trunk", "trunk_link")


def bike_rule(tags):
    """(metres per minute, forward allowed, backward allowed) or None."""
    hw = tags.get("highway", "")
    cyc = tags.get("bicycle")
    if hw in NO_BIKES or cyc in ("no", "use_sidepath"):
        return None
    if tags.get("access") in ("no", "private") and cyc not in (
        "yes",
        "designated",
        "permissive",
    ):
        return None
    if hw == "busway" and cyc not in ("yes", "designated"):
        return None
    speed = SPEED_PEDESTRIAN if hw == "pedestrian" else SPEED
    ow = tags.get("oneway", "no")
    one = ow in ("yes", "1", "true") or tags.get("junction") in (
        "roundabout",
        "circular",
    )
    back_only = ow in ("-1", "reverse")
    contraflow = tags.get("oneway:bicycle") == "no" or any(
        "opposite" in v for k, v in tags.items() if k.startswith("cycleway")
    )
    if contraflow or not (one or back_only):
        return speed, True, True
    return (speed, False, True) if back_only else (speed, True, False)


class StreetGraph:
    def __init__(self, roads, box=None):
        """``roads``: ``city.load_roads()``. ``box`` = (x0, y0, x1, y1) in metres
        keeps only the streets that touch it."""
        index, xy = {}, []
        src, dst, cost = [], [], []
        self.stats = {"ways": 0, "one_way": 0, "contraflow": 0}
        for r in roads:
            rule = bike_rule(r["tags"])
            if rule is None:
                continue
            p = r["xy"]
            if box is not None and (
                p[:, 0].max() < box[0]
                or p[:, 0].min() > box[2]
                or p[:, 1].max() < box[1]
                or p[:, 1].min() > box[3]
            ):
                continue
            speed, fwd, back = rule
            self.stats["ways"] += 1
            self.stats["one_way"] += int(not (fwd and back))
            self.stats["contraflow"] += int(
                fwd and back and r["tags"].get("oneway") in ("yes", "1", "true")
            )
            ids = []
            for n, q in zip(r["nodes"], p, strict=True):
                k = index.get(n)
                if k is None:
                    k = index[n] = len(xy)
                    xy.append(q)
                ids.append(k)
            seg = np.hypot(*np.diff(p, axis=0).T) / speed
            for a, b, c in zip(ids[:-1], ids[1:], seg, strict=True):
                if a == b:
                    continue
                if fwd:
                    src.append(a), dst.append(b), cost.append(c)
                if back:
                    src.append(b), dst.append(a), cost.append(c)
        self.xy = np.array(xy)
        n = len(xy)
        # parallel edges: keep the fastest (csr_matrix would add them up)
        order = np.lexsort((cost, dst, src))
        s, d, c = np.array(src)[order], np.array(dst)[order], np.array(cost)[order]
        first = np.ones(len(s), bool)
        first[1:] = (s[1:] != s[:-1]) | (d[1:] != d[:-1])
        self.m = csr_matrix(
            (np.maximum(c[first], 1e-6), (s[first], d[first])), shape=(n, n)
        )
        _, label = connected_components(self.m, directed=True, connection="strong")
        main = np.bincount(label).argmax()
        self.core = np.flatnonzero(label == main)  # nodes that reach each other
        self.tree = cKDTree(self.xy[self.core])
        self.stats.update(nodes=n, edges=int(first.sum()), core=len(self.core))

    def snap(self, pts):
        """The nearest street node (of the connected core) to every point."""
        dist, k = self.tree.query(np.atleast_2d(pts))
        return self.core[k], dist

    def table(self, sources, targets=None, chunk=64):
        """Minutes from every source node to every target node, and ``path(i, j)``
        returning the street polyline (metres) from source i to target j."""
        sources = np.asarray(sources)
        targets = sources if targets is None else np.asarray(targets)
        minutes = np.zeros((len(sources), len(targets)))
        pred = {}
        for a in range(0, len(sources), chunk):
            idx = sources[a : a + chunk]
            dist, pr = dijkstra(
                self.m, directed=True, indices=idx, return_predecessors=True
            )
            minutes[a : a + chunk] = dist[:, targets]
            for k, s in enumerate(idx):
                # keep only what is needed to walk back from the targets
                pred[int(s)] = _trim(pr[k], targets, int(s))
        assert np.isfinite(minutes).all(), "a stop is cut off from the street network"

        def path(i, j):
            s, node = int(sources[i]), int(targets[j])
            walk = [node]
            pr = pred[s]
            while node != s:
                node = pr[node]
                walk.append(node)
            return self.xy[walk[::-1]]

        return minutes, path


def _trim(pr, targets, s):
    out = {}
    for t in targets:
        node = int(t)
        while node != s and node not in out:
            out[node] = int(pr[node])
            node = out[node]
    return out


def length(poly):
    return float(np.hypot(*np.diff(poly, axis=0).T).sum())

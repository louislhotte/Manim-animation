"""city.py: Paris as geometry, and as a picture.

Two halves:

* **bake** (``bake_geometry``): read the cached OpenStreetMap answers (``osm.py``),
  project them to metres, and write ``assets/paris.npz``: streets by class, water,
  green areas, railways, the building footprints of one district, and the outlines
  of the 20 arrondissements. A few megabytes, committed with the film.
* **draw** (``texture``): rasterise any window of that geometry with Cairo, in the
  house's dark palette, at any size. Textures are cached on disk (outside the repo)
  under a hash of the request, so the film never ships large images.

Coordinates are metres east / north of "point zero" (see ``osm.to_xy``).
Map data (c) OpenStreetMap contributors, ODbL.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
GEOMETRY = ASSETS / "paris.npz"
TEX_CACHE = Path(
    os.environ.get("MIP_TEX_CACHE", "~/.cache/manimx/mip-textures")
).expanduser()
UNIT = 0.1  # stored coordinates are integers, in decimetres

# street classes, thinnest first (the order they are painted in)
ROAD_GROUPS = ("path", "minor", "tertiary", "secondary", "primary", "ring")
ROAD_GROUP_OF = {
    "cycleway": "path",
    "pedestrian": "path",
    "busway": "path",
    "unclassified": "minor",
    "residential": "minor",
    "living_street": "minor",
    "tertiary": "tertiary",
    "tertiary_link": "tertiary",
    "secondary": "secondary",
    "secondary_link": "secondary",
    "primary": "primary",
    "primary_link": "primary",
    "trunk": "ring",
    "trunk_link": "ring",
    "motorway": "ring",
    "motorway_link": "ring",
}


# --------------------------------------------------------------------------- #
# bake: OpenStreetMap JSON -> compact arrays
# --------------------------------------------------------------------------- #
def _xy(geom):
    from osm import to_xy

    a = np.array([(g["lat"], g["lon"]) for g in geom], dtype=float)
    x, y = to_xy(a[:, 0], a[:, 1])
    return np.column_stack([x, y])


def stitch(segments):
    """Join way pieces end to end into rings (closed) or chains (left open)."""
    segs = [s for s in segments if len(s) >= 2]
    ends = {}
    for k, s in enumerate(segs):
        for p in (s[0], s[-1]):
            ends.setdefault((round(p[0], 2), round(p[1], 2)), []).append(k)
    used, out = set(), []
    for k0 in range(len(segs)):
        if k0 in used:
            continue
        used.add(k0)
        ring = [tuple(p) for p in segs[k0]]
        while True:
            if (
                len(ring) > 3
                and abs(ring[0][0] - ring[-1][0]) < 0.02
                and abs(ring[0][1] - ring[-1][1]) < 0.02
            ):
                break
            key = (round(ring[-1][0], 2), round(ring[-1][1], 2))
            nxt = next((k for k in ends.get(key, ()) if k not in used), None)
            if nxt is None:
                break
            used.add(nxt)
            s = [tuple(p) for p in segs[nxt]]
            if (round(s[0][0], 2), round(s[0][1], 2)) != key:
                s.reverse()
            ring.extend(s[1:])
        out.append(np.array(ring))
    return out


def polygons_of(doc, keep=lambda tags: True):
    """Every area of an Overpass answer as a list of rings (outer and inner mixed:
    they are filled with the even-odd rule, so holes stay holes)."""
    polys, tags_of = [], []
    for el in doc["elements"]:
        tags = el.get("tags", {})
        if not keep(tags):
            continue
        if el["type"] == "way" and "geometry" in el:
            g = _xy(el["geometry"])
            if len(g) >= 4 and np.allclose(g[0], g[-1], atol=0.02):
                polys.append([g])
                tags_of.append(tags)
        elif el["type"] == "relation":
            parts = [
                _xy(m["geometry"])
                for m in el.get("members", ())
                if m["type"] == "way" and m.get("geometry")
            ]
            rings = [r for r in stitch(parts) if len(r) >= 4]
            if rings:
                polys.append(rings)
                tags_of.append(tags)
    return polys, tags_of


def ring_area(r):
    x, y = r[:, 0], r[:, 1]
    return 0.5 * abs(float(np.dot(x[:-1], y[1:]) - np.dot(x[1:], y[:-1])))


def _pack(lines):
    """A list of (n, 2) arrays -> (all points as int32 decimetres, offsets)."""
    if not lines:
        return np.zeros((0, 2), np.int32), np.zeros(1, np.int64)
    off = np.cumsum([0] + [len(a) for a in lines])
    pts = np.rint(np.vstack(lines) / UNIT).astype(np.int32)
    return pts, off


def _pack_polys(polys):
    """A list of polygons (each a list of rings) -> points, ring offsets, and the
    index of the first ring of every polygon."""
    rings = [r for p in polys for r in p]
    pts, ring_off = _pack(rings)
    poly_off = np.cumsum([0] + [len(p) for p in polys])
    return pts, ring_off, poly_off


def load_roads():
    """Every street of the cached tiles, once: a list of dicts with ``id``, ``cls``,
    ``nodes`` (OpenStreetMap node ids), ``xy`` (metres) and ``tags``."""
    import osm

    seen, roads = set(), []
    for name, query in osm.queries().items():
        if not name.startswith("roads_"):
            continue
        for el in osm.overpass(name, query)["elements"]:
            if el["type"] != "way" or el["id"] in seen or "geometry" not in el:
                continue
            seen.add(el["id"])
            tags = el.get("tags", {})
            roads.append(
                {
                    "id": el["id"],
                    "cls": tags.get("highway", ""),
                    "nodes": el["nodes"],
                    "xy": _xy(el["geometry"]),
                    "tags": tags,
                }
            )
    return roads


def bake_geometry(path=GEOMETRY):
    import osm

    q = osm.queries()
    out = {}

    roads = load_roads()
    for g in ROAD_GROUPS:
        for tun in (0, 1):
            lines = [
                r["xy"]
                for r in roads
                if ROAD_GROUP_OF.get(r["cls"]) == g
                and int(r["tags"].get("tunnel", "no") not in ("no", "building_passage"))
                == tun
            ]
            out[f"road_{g}_{tun}_xy"], out[f"road_{g}_{tun}_off"] = _pack(lines)

    water = osm.overpass("water", q["water"])
    polys, _ = polygons_of(
        water,
        lambda t: (
            (
                t.get("natural") == "water"
                or t.get("waterway") == "riverbank"
                or t.get("type") == "multipolygon"
            )
            and t.get("tunnel") not in ("yes", "culvert")
            and t.get("covered") != "yes"
        ),
    )
    polys = [p for p in polys if sum(ring_area(r) for r in p) > 60]
    out["water_xy"], out["water_ring"], out["water_poly"] = _pack_polys(polys)

    green = osm.overpass("green", q["green"])
    polys, _ = polygons_of(green)
    polys = [p for p in polys if sum(ring_area(r) for r in p) > 120]
    out["green_xy"], out["green_ring"], out["green_poly"] = _pack_polys(polys)

    rail = osm.overpass("rail", q["rail"])
    lines = [_xy(el["geometry"]) for el in rail["elements"] if el.get("geometry")]
    out["rail_xy"], out["rail_off"] = _pack(lines)

    bld = osm.overpass("buildings", q["buildings"])
    polys, _ = polygons_of(bld)
    out["bld_xy"], out["bld_ring"], out["bld_poly"] = _pack_polys(polys)

    admin = osm.overpass("admin", q["admin"])
    polys, tags = polygons_of(admin)
    order = np.argsort([int(t["ref:INSEE"]) for t in tags])
    polys = [polys[i] for i in order]
    assert len(polys) == 20, len(polys)
    out["arr_xy"], out["arr_ring"], out["arr_poly"] = _pack_polys(polys)

    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **out)
    return {k: v.shape for k, v in out.items()}


# --------------------------------------------------------------------------- #
# load
# --------------------------------------------------------------------------- #
class Geometry:
    """The baked map. ``lines(name)`` and ``polys(name)`` give metres."""

    def __init__(self, path=GEOMETRY):
        self.z = np.load(path)
        self.stamp = f"{path.stat().st_size}-{int(path.stat().st_mtime)}"
        self._cache = {}

    def lines(self, name):
        if name not in self._cache:
            xy = self.z[f"{name}_xy"].astype(np.float64) * UNIT
            self._cache[name] = (xy, self.z[f"{name}_off"])
        return self._cache[name]

    def polys(self, name):
        if name not in self._cache:
            xy = self.z[f"{name}_xy"].astype(np.float64) * UNIT
            self._cache[name] = (xy, self.z[f"{name}_ring"], self.z[f"{name}_poly"])
        return self._cache[name]

    def arrondissement(self, n):
        """The outline rings of arrondissement ``n`` (1..20), in metres."""
        xy, ring, poly = self.polys("arr")
        return [xy[ring[r] : ring[r + 1]] for r in range(poly[n - 1], poly[n])]


_GEO = None


def geometry():
    global _GEO
    if _GEO is None:
        _GEO = Geometry()
    return _GEO


# --------------------------------------------------------------------------- #
# draw
# --------------------------------------------------------------------------- #
STYLE = {
    "outside": "#0C0F15",  # beyond the city limit: almost the film's background
    "land": "#121824",
    "block": "#182030",  # building footprints (close-ups)
    "green": "#13291F",
    "water": "#102741",
    "water_edge": "#1B3A5C",
    "rail": "#2B3446",
    "arr": "#33405A",  # arrondissement outlines
    # street class -> (colour, real width in metres, minimum width in pixels)
    "road": {
        "path": ("#222B3B", 4.0, 0.6),
        "minor": ("#2A3448", 7.0, 0.8),
        "tertiary": ("#34405A", 10.0, 1.0),
        "secondary": ("#3E4C6C", 13.0, 1.25),
        "primary": ("#4B5C84", 17.0, 1.6),
        "ring": ("#5A6C96", 24.0, 2.0),
    },
    "dim_outside": 0.55,  # how much of the picture survives outside Paris
}


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))


def texture(
    cx, cy, width_m, w, h, detail=True, style=None, arr=True, cache=True, min_scale=None
):
    """An RGBA uint8 array (h, w, 4): the map window centred on (cx, cy) metres,
    ``width_m`` metres wide. North is up.

    Streets are drawn at their real width, but never thinner than a minimum number
    of pixels: ``min_scale`` multiplies those minimums (default ``w / 1920``: the
    picture is meant to fill a 1080p frame; 1.0 for a texture shown pixel for pixel).
    """
    style = {**STYLE, **(style or {})}
    geo = geometry()
    min_scale = w / 1920 if min_scale is None else min_scale
    key = hashlib.sha1(
        repr((geo.stamp, cx, cy, width_m, w, h, detail, arr, min_scale, sorted(style.items(), key=str))).encode()
    ).hexdigest()[:16]  # fmt: skip
    path = TEX_CACHE / f"map-{key}.npy"
    if cache and path.exists():
        return np.load(path)
    img = _draw(geo, cx, cy, width_m, w, h, detail, style, arr, min_scale)
    if cache:
        TEX_CACHE.mkdir(parents=True, exist_ok=True)
        np.save(path, img)
    return img


def _draw(geo, cx, cy, width_m, w, h, detail, style, arr, k):
    import cairo

    ppm = w / width_m  # pixels per metre
    x0, y1 = cx - width_m / 2, cy + (h / ppm) / 2  # the top-left corner, in metres
    margin = 60.0
    lo = np.array([x0 - margin, y1 - h / ppm - margin])
    hi = np.array([x0 + width_m + margin, y1 + margin])

    def px(xy):
        return np.column_stack([(xy[:, 0] - x0) * ppm, (y1 - xy[:, 1]) * ppm])

    def visible(xy, off):
        """Indices of the polylines whose bounding box meets the window."""
        if len(off) < 2:
            return []
        mn = np.minimum.reduceat(xy, off[:-1], axis=0)
        mx = np.maximum.reduceat(xy, off[:-1], axis=0)
        ok = np.all(mx >= lo, axis=1) & np.all(mn <= hi, axis=1)
        return np.flatnonzero(ok)

    def path_lines(ctx, name):
        xy, off = geo.lines(name)
        p = px(xy)
        for k in visible(xy, off):
            a, b = off[k], off[k + 1]
            ctx.move_to(*p[a])
            for q in p[a + 1 : b]:
                ctx.line_to(*q)

    def path_polys(ctx, name, min_px=0.0):
        xy, ring, poly = geo.polys(name)
        p = px(xy)
        vis = set(visible(xy, ring).tolist())
        for k in range(len(poly) - 1):
            rings = [r for r in range(poly[k], poly[k + 1]) if r in vis]
            for r in rings:
                a, b = ring[r], ring[r + 1]
                if min_px and np.ptp(p[a:b], axis=0).max() < min_px:
                    continue
                ctx.move_to(*p[a])
                for q in p[a + 1 : b]:
                    ctx.line_to(*q)
                ctx.close_path()

    def surface():
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        c = cairo.Context(s)
        c.set_line_join(cairo.LINE_JOIN_ROUND)
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        return s, c

    surf, ctx = surface()
    ctx.set_source_rgb(*_rgb(style["land"]))
    ctx.paint()

    ctx.set_source_rgb(*_rgb(style["green"]))
    path_polys(ctx, "green", min_px=1.5)
    ctx.fill()

    ctx.set_source_rgb(*_rgb(style["water"]))
    path_polys(ctx, "water")
    ctx.fill_preserve()
    ctx.set_source_rgb(*_rgb(style["water_edge"]))
    ctx.set_line_width(max(0.8 * k, 1.6 * ppm))
    ctx.stroke()

    if detail and ppm > 0.35:
        ctx.set_source_rgb(*_rgb(style["block"]))
        path_polys(ctx, "bld", min_px=2.0)
        ctx.fill()

    ctx.set_source_rgb(*_rgb(style["rail"]))
    ctx.set_line_width(max(0.7 * k, 2.5 * ppm))
    ctx.set_dash([max(3.0 * k, 14 * ppm), max(3.0 * k, 10 * ppm)])
    path_lines(ctx, "rail")
    ctx.stroke()
    ctx.set_dash([])

    for g in ROAD_GROUPS:
        colour, real, least = style["road"][g]
        width = max(least * k, real * ppm)
        if g == "path" and width < 0.9 and not detail:
            continue
        ctx.set_line_width(width)
        ctx.set_source_rgb(*_rgb(colour))
        path_lines(ctx, f"road_{g}_0")
        ctx.stroke()
        if g != "path":  # tunnels: the same line, fainter
            ctx.set_source_rgba(*_rgb(colour), 0.28)
            path_lines(ctx, f"road_{g}_1")
            ctx.stroke()

    if arr:
        ctx.set_source_rgba(*_rgb(style["arr"]), 0.9)
        ctx.set_line_width(max(1.0, 1.1 * k))
        ctx.set_dash([6 * max(k, 1.0), 5 * max(k, 1.0)])
        path_polys(ctx, "arr")
        ctx.stroke()
        ctx.set_dash([])

    img = _rgba(surf, w, h).astype(np.float32)

    # dim what lies outside the city limit (the union of the arrondissements)
    ms, mc = surface()
    mc.set_fill_rule(cairo.FILL_RULE_WINDING)
    mc.set_source_rgb(1, 1, 1)
    path_polys(mc, "arr")
    mc.fill()
    m = _rgba(ms, w, h)[:, :, 0:1].astype(np.float32) / 255.0
    keep = m + (1 - m) * style["dim_outside"]
    out = np.array(_rgb(style["outside"]), dtype=np.float32) * 255.0
    img[:, :, :3] = img[:, :, :3] * keep + out * (1 - keep)
    img[:, :, 3] = 255.0
    return np.clip(np.rint(img), 0, 255).astype(np.uint8)


def _rgba(surf, w, h):
    surf.flush()
    a = np.frombuffer(surf.get_data(), dtype=np.uint8).reshape(
        h, surf.get_stride() // 4, 4
    )
    return a[:, :w, [2, 1, 0, 3]].copy()  # Cairo stores BGRA (little endian)


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(HERE))
    shapes = bake_geometry()
    for k, v in shapes.items():
        print(f"  {k:22s} {v}")
    print(f"{GEOMETRY.name}: {GEOMETRY.stat().st_size / 1e6:.2f} MB")

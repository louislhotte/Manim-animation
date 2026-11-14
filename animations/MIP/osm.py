"""osm.py: the real Paris, fetched once from OpenStreetMap through the Overpass API.

Read-only queries (streets, water, green areas, railways, district outlines,
restaurants, building footprints of one district). Every response is cached,
gzipped, in ``~/.cache/manimx/osm-paris``, so the public servers are asked once
per layer and a re-bake works offline.

    python osm.py            # fetch what is missing, print what is cached

Map data (c) OpenStreetMap contributors, Open Database Licence (ODbL).
"""

from __future__ import annotations

import gzip
import json
import math
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CACHE = Path(os.environ.get("MIP_OSM_CACHE", "~/.cache/manimx/osm-paris")).expanduser()
SERVERS = (  # public Overpass instances; the first one that answers is used
    "https://overpass.openstreetmap.fr/api/interpreter",  # OpenStreetMap France
    "https://overpass-api.de/api/interpreter",  # the main instance (often at capacity)
)
AGENT = "manimx-explainer/1.0 (educational animation; one-off cached map fetch)"

# (south, west, north, east)
BBOX_BIG = (
    48.790,
    2.180,
    48.928,
    2.512,
)  # Paris and what a tilted camera sees around it
BBOX_PARIS = (48.8150, 2.2235, 48.9025, 2.4705)  # the city and its two woods
BBOX_DISTRICT = (48.8440, 2.3200, 48.8740, 2.3960)  # the close-up: Louvre to Bastille

ROAD_CLASSES = (
    "motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|"
    "secondary_link|tertiary|tertiary_link|unclassified|residential|living_street|"
    "pedestrian|cycleway|busway"
)

# Local metric projection (equirectangular about "point zero", the square in front
# of Notre-Dame): x east, y north, in metres. Off by well under 0.1 % at city scale.
LAT0, LON0 = 48.85341, 2.34880
M_PER_LAT = 111_194.9
M_PER_LON = M_PER_LAT * math.cos(math.radians(LAT0))


def to_xy(lat, lon):
    return (lon - LON0) * M_PER_LON, (lat - LAT0) * M_PER_LAT


def to_latlon(x, y):
    return y / M_PER_LAT + LAT0, x / M_PER_LON + LON0


def tiles(bbox, nx, ny):
    s, w, n, e = bbox
    for j in range(ny):
        for i in range(nx):
            yield (
                s + (n - s) * j / ny,
                w + (e - w) * i / nx,
                s + (n - s) * (j + 1) / ny,
                w + (e - w) * (i + 1) / nx,
            )


def _b(bbox):
    return "({:.5f},{:.5f},{:.5f},{:.5f})".format(*bbox)


def queries():
    """name -> Overpass QL. Roads are tiled so that no answer is huge."""
    head = "[out:json][timeout:240][maxsize:1073741824];"
    q = {}
    for k, t in enumerate(tiles(BBOX_BIG, 4, 3)):
        q[f"roads_{k:02d}"] = (
            f'{head}way["highway"~"^({ROAD_CLASSES})$"]{_b(t)};out geom qt;'
        )
    big, paris, district = _b(BBOX_BIG), _b(BBOX_PARIS), _b(BBOX_DISTRICT)
    q["water"] = (
        f'{head}(way["natural"="water"]{big};relation["natural"="water"]{big};'
        f'way["waterway"="riverbank"]{big};relation["waterway"="riverbank"]{big};'
        f'way["waterway"~"^(river|canal)$"]{big};);out geom qt;'
    )
    q["green"] = (
        f'{head}(way["leisure"~"^(park|garden)$"]{big};'
        f'relation["leisure"~"^(park|garden)$"]{big};'
        f'way["landuse"~"^(forest|cemetery|grass|meadow|recreation_ground|village_green)$"]{big};'
        f'relation["landuse"~"^(forest|cemetery)$"]{big};'
        f'way["natural"="wood"]{big};relation["natural"="wood"]{big};);out geom qt;'
    )
    q["rail"] = f'{head}way["railway"="rail"]["tunnel"!="yes"]{big};out skel geom qt;'
    q["admin"] = (
        f'{head}relation["boundary"="administrative"]["admin_level"~"^(8|9)$"]'
        f'["ref:INSEE"~"^751"]{paris};out geom qt;'
    )
    q["food"] = f'{head}node["amenity"~"^(restaurant|fast_food)$"]{paris};out body qt;'
    q["buildings"] = f'{head}way["building"]{district};out skel geom qt;'
    return q


def _http(url, query, timeout=300):
    data = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(
        url, data=data, headers={"User-Agent": AGENT, "Accept-Encoding": "gzip"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            return raw
    except urllib.error.URLError as e:
        if "CERTIFICATE" not in str(e).upper():
            raise
    # Python without a CA bundle (or a corporate TLS proxy): the system curl knows
    # the machine's trust store.
    out = subprocess.run(
        ["curl", "-sS", "--fail", "--compressed", "--max-time", str(timeout),
         "-A", AGENT, "--data-urlencode", f"data={query}", url],
        capture_output=True, check=False,
    )  # fmt: skip
    if out.returncode != 0:
        raise RuntimeError(out.stderr.decode(errors="replace").strip()[:300])
    return out.stdout


def overpass(name, query, tries=6):
    """The parsed answer to ``query``, from the cache when it is there."""
    path = CACHE / f"{name}.json.gz"
    if path.exists():
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    CACHE.mkdir(parents=True, exist_ok=True)
    last = None
    for k in range(tries):
        url = SERVERS[(k // 2) % len(SERVERS)]  # two tries per server, then the next
        t0 = time.time()
        try:
            raw = _http(url, query)
            doc = json.loads(raw)
            remark = doc.get("remark", "")
            if "error" in remark.lower() or "elements" not in doc:
                raise RuntimeError(remark or "no elements in the answer")
        except Exception as e:  # noqa: BLE001 (any failure: wait, try the next server)
            last = e
            wait = 8 * (k + 1)
            print(
                f"  {name}: {type(e).__name__}: {str(e)[:160]} ({url}); retry in {wait} s"
            )
            time.sleep(wait)
            continue
        with gzip.open(path, "wt", encoding="utf-8") as f:
            json.dump(doc, f, separators=(",", ":"))
        print(
            f"  {name}: {len(doc['elements']):,} elements, {len(raw) / 1e6:.1f} MB,"
            f" {time.time() - t0:.0f} s  ({urllib.parse.urlparse(url).netloc})"
        )
        time.sleep(1.5)  # be a polite client
        return doc
    raise RuntimeError(f"could not fetch {name}: {last}")


def fetch_all(only=None):
    out = {}
    for name, query in queries().items():
        if only and not any(name.startswith(p) for p in only):
            continue
        out[name] = overpass(name, query)
    return out


if __name__ == "__main__":
    docs = fetch_all(sys.argv[1:] or None)
    total = sum(p.stat().st_size for p in CACHE.glob("*.json.gz"))
    print(f"{len(docs)} layers in {CACHE} ({total / 1e6:.1f} MB gzipped)")
    for name, doc in docs.items():
        print(f"  {name:12s} {len(doc['elements']):8,d} elements")

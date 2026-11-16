"""generate_assets.py: bake everything the film shows into ``assets/``.

    python generate_assets.py            # about 90 s (it waits for a real timeout)
    python generate_assets.py --quick    # skips the 75 s wait, keeps the old result

Nothing here touches the network: the experiments run between two programs on the
loopback interface of this machine (``lab.py``), the packet-level pictures come from
a model (``tcpsim.py``), distances from geometry. What is written:

* ``assets/story.json``       every number, byte and error message of the film
* ``assets/course_map.ppm``   the picture the server sends (Lea's course on the real
                              map of Paris, from the MIP film's assets; needs them)
* ``assets/world.json``       land outlines for the opening map (Natural Earth, from
                              the GeoDetect film's assets)
* ``assets/curl_verbose.txt`` what ``curl -v`` prints for the same request
* ``demo/courses.json``       the course the demo server answers with

Private keys of the demo's certificate authority stay outside the repository
(``demo/pki.py``).
"""

from __future__ import annotations

import json
import math
import random
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ASSETS = HERE / "assets"
sys.path.insert(0, str(HERE))

import tcpsim  # noqa: E402

MIP = REPO / "animations" / "MIP"
WORLD_SRC = REPO / "animations" / "GeoDetect" / "assets" / "world_map.json"
MAP_W, MAP_H = 320, 240

# where the story happens (the lab itself never leaves this machine)
PARIS = (48.8566, 2.3522)
SINGAPORE = (1.3521, 103.8198)
C_KM_S = 299_792.458
FIBRE_INDEX = 1.468  # group index of standard single-mode fibre at 1550 nm
VIEW = (-14.0, 128.0, -8.5, 67.5)  # lon0, lon1, lat0, lat1 of the opening map


# --------------------------------------------------------------------------- #
# geography
# --------------------------------------------------------------------------- #
def great_circle_km(a, b, radius=6371.0088):
    (la1, lo1), (la2, lo2) = (tuple(map(math.radians, p)) for p in (a, b))
    h = (
        math.sin((la2 - la1) / 2) ** 2
        + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(h))


def great_circle_path(a, b, n=64):
    """Points (lat, lon) along the shortest path on the globe."""
    (la1, lo1), (la2, lo2) = (tuple(map(math.radians, p)) for p in (a, b))

    def xyz(la, lo):
        return (math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))

    p, q = xyz(la1, lo1), xyz(la2, lo2)
    w = math.acos(max(-1.0, min(1.0, sum(x * y for x, y in zip(p, q, strict=True)))))
    out = []
    for k in range(n + 1):
        f = k / n
        s1, s2 = math.sin((1 - f) * w) / math.sin(w), math.sin(f * w) / math.sin(w)
        x, y, z = (s1 * u + s2 * v for u, v in zip(p, q, strict=True))
        out.append(
            [
                round(math.degrees(math.atan2(z, math.hypot(x, y))), 3),
                round(math.degrees(math.atan2(y, x)), 3),
            ]
        )
    return out


def geography() -> dict:
    km = great_circle_km(PARIS, SINGAPORE)
    v = C_KM_S / FIBRE_INDEX
    one_way = km / v * 1000
    return {
        "from": {"name": "Paris", "at": PARIS},
        "to": {"name": "Singapore", "at": SINGAPORE},
        "km": km,
        "fibre_km_per_s": v,
        "fibre_km_per_ms": v / 1000,
        "one_way_ms": one_way,
        "round_trip_ms": 2 * one_way,
        "path": great_circle_path(PARIS, SINGAPORE),
        "view": VIEW,
    }


def world() -> list:
    """Land outlines inside the opening map's window (lon, lat rings)."""
    lon0, lon1, lat0, lat1 = VIEW
    pad = 6.0
    rings = []
    for country in json.loads(WORLD_SRC.read_text()):
        for ring in country["rings"]:
            xs, ys = [p[0] for p in ring], [p[1] for p in ring]
            if (
                max(xs) < lon0 - pad
                or min(xs) > lon1 + pad
                or max(ys) < lat0 - pad
                or min(ys) > lat1 + pad
            ):
                continue
            rings.append([[round(x, 2), round(y, 2)] for x, y in ring])
    return rings


# --------------------------------------------------------------------------- #
# the picture the server sends
# --------------------------------------------------------------------------- #
def course_from_mip() -> dict:
    hero = json.loads((MIP / "assets" / "story.json").read_text())["hero"]
    best = hero["brute"]
    assert best["obj"] == hero["gurobi"]["obj"] == 24.4, (
        "the course the MIP film proved optimal"
    )
    return {"courier": "lea", "stops": best["seq"], "earns": best["obj"]}


def course_map() -> bytes:
    """Lea's proven-optimal course, drawn on the real street map, as raw RGB."""
    import cairo
    import numpy as np

    sys.path.insert(0, str(MIP))
    import city

    hero = json.loads((MIP / "assets" / "story.json").read_text())["hero"]
    orders = {o["name"]: o for o in hero["orders"]}
    seq, lea = hero["brute"]["seq"], np.array(hero["start"]["lea"])
    pieces, i = [], "lea"
    for j in seq:
        pieces += [np.array(hero["approach"][f"{i}|{j}"]), np.array(hero["leg"][j])]
        i = j
    pts = np.vstack(pieces + [lea[None]])
    lo, hi = pts.min(0), pts.max(0)
    w, h, k = MAP_W, MAP_H, 4
    mid = (lo + hi) / 2
    span = max((hi[0] - lo[0]) * 1.16, (hi[1] - lo[1]) * 1.16 * w / h)
    tex = city.texture(
        mid[0],
        mid[1],
        span,
        w * k,
        h * k,
        detail=True,
        arr=False,
        cache=False,
        min_scale=1.6,
    )
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w * k, h * k)
    ctx = cairo.Context(surf)
    s = w * k / span

    def px(p):
        return ((p[0] - mid[0]) * s + w * k / 2, h * k / 2 - (p[1] - mid[1]) * s)

    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for width, rgba in (
        (7.0 * k, (0.05, 0.07, 0.09, 0.55)),
        (3.4 * k, (1.0, 0.82, 0.4, 1.0)),
    ):
        ctx.set_source_rgba(*rgba)
        ctx.set_line_width(width)
        for poly in pieces:
            ctx.move_to(*px(poly[0]))
            for p in poly[1:]:
                ctx.line_to(*px(p))
            ctx.stroke()

    def dot(p, r, rgb):
        ctx.set_source_rgba(0.05, 0.07, 0.09, 1)
        ctx.arc(*px(p), (r + 1.3) * k, 0, math.tau)
        ctx.fill()
        ctx.set_source_rgb(*rgb)
        ctx.arc(*px(p), r * k, 0, math.tau)
        ctx.fill()

    for j in seq:
        dot(orders[j]["R"], 2.6, (0.96, 0.95, 0.94))
        dot(orders[j]["C"], 2.0, (0.96, 0.95, 0.94))
    dot(lea, 3.4, (1.0, 0.82, 0.4))
    over = (
        np.ndarray((h * k, w * k, 4), dtype=np.uint8, buffer=surf.get_data()).astype(
            float
        )[..., [2, 1, 0, 3]]
        / 255
    )
    rgb = (
        tex[..., :3].astype(float) / 255 * (1 - over[..., 3:4]) + over[..., :3]
    )  # cairo premultiplies
    rgb = np.clip(rgb * 1.55 + 0.02, 0, 1)  # the dark map, lifted: it is shown small
    small = rgb.reshape(h, k, w, k, 3).mean(axis=(1, 3))
    return (
        f"P6\n{w} {h}\n255\n".encode() + (small * 255 + 0.5).astype(np.uint8).tobytes()
    )


# --------------------------------------------------------------------------- #
def main() -> int:
    quick = "--quick" in sys.argv
    ASSETS.mkdir(exist_ok=True)
    story_path = ASSETS / "story.json"
    old = json.loads(story_path.read_text()) if story_path.exists() else {}

    # 0. what the server serves
    course = course_from_mip()
    (HERE / "demo" / "courses.json").write_text(
        json.dumps({"lea": course}, indent=1) + "\n"
    )
    ppm = ASSETS / "course_map.ppm"
    if (MIP / "assets" / "paris.npz").exists():
        ppm.write_bytes(course_map())
    assert ppm.read_bytes().startswith(f"P6\n{MAP_W} {MAP_H}\n255\n".encode())
    (ASSETS / "world.json").write_text(json.dumps(world(), separators=(",", ":")))

    import lab  # after courses.json and the picture exist: the server reads them

    # 1. the long wait runs beside everything else
    quiet = {}
    waiter = None
    if quick and "silence" in old.get("kernel", {}):
        quiet = old["kernel"]["silence"]
    else:
        waiter = threading.Thread(
            target=lambda: quiet.update(lab.silence()), daemon=True
        )
        waiter.start()

    t0 = time.perf_counter()
    story = {"course": course}
    story["geo"] = geo = geography()
    story["http"] = http = lab.plain_http()
    story["status"] = lab.status_codes()
    story["keep_alive"] = lab.keep_alive()
    story["tap"] = lab.eavesdrop()
    story["tls"] = tls = lab.https()
    story["tls_failures"] = lab.tls_failures()
    story["certificates"] = lab.certificates()
    story["key_agreement"] = lab.key_agreement()
    story["kernel"] = kernel = lab.kernel()
    story["gateway"] = lab.gateway()
    curl = lab.curl_verbose()
    if curl:
        (ASSETS / "curl_verbose.txt").write_text(curl)

    # 2. the models, fed with the real sizes
    rtt = geo["round_trip_ms"]
    rng = random.Random(2026)
    stream = http["map"]["bytes"]["head"] + http["map"]["bytes"]["body"]
    tcp = tcpsim.transfer(stream, rtt, lose=(92,))
    clean = tcpsim.transfer(stream, rtt)
    story["tcp"] = {
        "handshake": tcpsim.handshake(rtt, rng.getrandbits(32), rng.getrandbits(32)),
        "transfer": tcp,
        "clean_facts": clean["facts"],
        "picture": {
            "w": MAP_W,
            "h": MAP_H,
            "offset": http["map"]["bytes"]["head"] + len(f"P6\n{MAP_W} {MAP_H}\n255\n"),
        },
    }
    story["ip"] = tcpsim.best_effort(tcp["facts"]["segments"])

    # 3. the ledger: round trips before the answer starts to arrive
    story["ledger"] = {
        "round_trip_ms": rtt,
        "fresh_https": {
            "round_trips": 3,
            "ms": 3 * rtt,
            "steps": ["TCP", "TLS", "HTTP"],
        },
        "fresh_http": {"round_trips": 2, "ms": 2 * rtt},
        "reused": {"round_trips": 1, "ms": rtt},
        "picture_round_trips": clean["facts"]["round_trips"],
    }

    if waiter is not None:
        print(
            f"   waiting for the kernel to give up on {lab.NOBODY} (about 75 s) ...",
            flush=True,
        )
        waiter.join(200)
        assert quiet, "the silence experiment did not finish"
    kernel["silence"] = quiet

    # ---- the facts the film states, checked where they are produced ----------- #
    f, win = tcp["facts"], kernel["first_window"]
    assert 10_700 < geo["km"] < 10_760 and 100 < rtt < 110
    assert (
        f["flights"][:4] == [10, 20, 40, 80]
        and f["segments"] == 158
        and f["lost"] == [92]
    )
    assert abs(win["segments"] - 10) < 0.01, (
        "this machine's kernel starts with ten segments too"
    )
    assert win["after_90kB_bytes"] > win["window_bytes"], (
        "... and opens the window as data gets through"
    )
    assert kernel["refused"]["ms"] < 5 and kernel["refused"]["text"].endswith(
        "Connection refused"
    )
    assert 70 < quiet["kernel"]["gave_up_s"] < 80 and quiet["syn_s"][:6] == [
        0.0,
        1.0,
        2.0,
        3.0,
        4.0,
        5.0,
    ]
    assert (
        tls["flights"][0]["way"] == ">"
        and tls["flights"][1]["way"] == "<"
        and tls["flights"][2]["way"] == ">"
    )
    assert tls["request"]["overhead"] == 22, (
        "5 bytes of record header, 1 of type, 16 of tag"
    )
    assert story["ip"]["facts"]["arrived"] + len(story["ip"]["facts"]["lost"]) == 158

    story["meta"] = {
        "baked": time.strftime("%Y-%m-%d"),
        "python_ssl": __import__("ssl").OPENSSL_VERSION,
        "platform": sys.platform,
        "seconds": round(time.perf_counter() - t0, 1),
    }
    story_path.write_text(json.dumps(story, indent=1))
    print(
        f"baked {story_path.name} ({story_path.stat().st_size / 1e6:.2f} MB) in {story['meta']['seconds']} s"
    )
    print(f"   Paris - Singapore {geo['km']:,.0f} km, round trip at least {rtt:.1f} ms")
    print(f"   picture {stream:,} bytes in {f['segments']} segments, flights {f['flights']}, "
          f"lost {f['lost']}, last byte after {f['last_byte_ms']:.0f} ms")  # fmt: skip
    print(f"   TLS: hello {tls['client_hello']['bytes']} B, flights "
          f"{[(x['way'], x['bytes']) for x in tls['flights']]}")  # fmt: skip
    print(
        f"   kernel: SYN at {quiet['syn_s']} s, gave up after {quiet['kernel']['gave_up_s']} s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

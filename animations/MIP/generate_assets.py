"""generate_assets.py: bake everything the film shows, from real runs.

    python generate_assets.py            # bake assets/ (needs the OSM cache + gurobipy)
    python generate_assets.py scan 0 80  # compare candidate seeds for Lea's hour
    python generate_assets.py patch-cut  # recompute only the cutting-plane demo
    python generate_assets.py patch-lp   # ... or only the time one relaxation takes
    python generate_assets.py patch-data # ... or the two runnable instances at full
                                         #     precision, and the district's full log

Writes

* ``assets/paris.npz``      the map geometry (``city.bake_geometry``);
* ``assets/story.json``     Lea's hour, one arrondissement in depth, the whole city:
                            instances, street paths, every solver's answer, our
                            branch-and-bound tree, Gurobi's incumbents and bounds;
* ``assets/gurobi_*.txt``   Gurobi's logs, verbatim (``.txt``: the repo ignores
                            ``*.log``), minus the line naming the local log path.

Rendering needs none of the tools used here: only the files above.
"""

from __future__ import annotations

import json
import math
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

import city
import model
import story

HERE = Path(__file__).resolve().parent
# MIP_BAKE_DIR=<folder> bakes story.json and the logs somewhere else: a dry run to
# compare with the committed assets (Gurobi's timings differ from run to run)
ASSETS = Path(os.environ.get("MIP_BAKE_DIR") or HERE / "assets")
HERO_SEED = 59
CITY_SEED = 2026
DEEP_ARR = 11  # the arrondissement the film looks at in depth


def key(r):
    return f"{r[0]}|{r[1]}"


def keep_log(src, name):
    """Copy a Gurobi log into ``assets/`` as text, without the line that prints the
    local path of the log file."""
    lines = [
        s
        for s in Path(src).read_text().splitlines()
        if not s.startswith("Set parameter LogFile")
    ]
    (ASSETS / f"gurobi_{name}.txt").write_text("\n".join(lines) + "\n")


# --------------------------------------------------------------------------- #
# Lea's hour
# --------------------------------------------------------------------------- #
def solve_hero(cast, log=None, full=True):
    """Every way the film solves Lea's hour, cross-checked."""
    inst = cast.inst
    brute = model.brute_force(inst, keep=True)
    small = model.presolve(inst)
    tree = model.branch_and_bound(small)
    assert tree["complete"] and tree["obj"] == brute["obj"], (tree["obj"], brute["obj"])
    out = {"inst": inst, "small": small, "brute": brute, "tree": tree}
    out["greedy"] = {rule: model.greedy(inst, rule) for rule in ("pay", "soon")}
    if full:
        highs = model.solve_highs(inst)
        assert highs["optimal"] and highs["obj"] == brute["obj"], highs["obj"]
        gur = model.solve_gurobi(inst, log=log)
        assert gur["optimal"] and gur["obj"] == brute["obj"], gur["obj"]
        assert model.courses_of(inst, gur["x"])["lea"] == brute["seq"]
        assert model.courses_of(inst, highs["x"])["lea"] == brute["seq"]
        assert model.courses_of(small, tree["x"])["lea"] == brute["seq"]
        out.update(highs=highs, gurobi=gur)
    return out


def tree_stats(tree):
    nodes = tree["nodes"]
    inc = [n for n in nodes if n.get("incumbent")]
    return {
        "nodes": len(nodes),
        "lps": tree["lps"],
        "depth": max(n["depth"] for n in nodes),
        "plans": [round(n["bound"], 1) for n in inc],
        "first_plan_at": inc[0]["id"],
        "last_plan_at": inc[-1]["id"],
        "pruned": sum(n["kind"] == "pruned" for n in nodes),
        "infeasible": sum(n["kind"] == "infeasible" for n in nodes),
        "root": round(nodes[0]["bound"], 2),
        "root_frac": sum(1 for v in nodes[0]["x"].values() if 1e-6 < v < 1 - 1e-6),
    }


def scan(world, a, b):
    print(
        "seed  opt (n) uniq | greedy pay soon | rides | root frac | nodes lps depth | plans"
    )
    for seed in range(a, b):
        try:
            cast = story.hero(world, seed)
        except AssertionError:
            continue
        r = solve_hero(cast, full=False)
        s = tree_stats(r["tree"])
        g = {k: model.revenue(r["inst"], v) for k, v in r["greedy"].items()}
        print(
            f"{seed:4d} {r['brute']['obj']:5.1f} ({len(r['brute']['seq'])}) "
            f"{'yes' if r['brute']['ties'] == 1 else ' no'} | {g['pay']:5.1f} {g['soon']:5.1f} |"
            f" {len(r['inst'].rides)}->{len(r['small'].rides)} | {s['root']:5.1f} {s['root_frac']:2d} |"
            f" {s['nodes']:4d} {s['lps']:4d} {s['depth']:2d} | {s['plans']}"
            f" feasible {r['brute']['feasible']}",
            flush=True,
        )


def lp_time(small, n=300):
    """Median wall time of one root relaxation of Lea's hour, in milliseconds (HiGHS
    through SciPy, the matrices already built): what "an easy problem" means."""
    from scipy.optimize import linprog

    c, A, b, lo, hi, _, _ = model.matrices(small)
    bounds = np.column_stack([lo, hi])
    ts = []
    for _ in range(n):
        t0 = time.perf_counter()
        linprog(-c, A_ub=A, b_ub=b, bounds=bounds, method="highs")
        ts.append(time.perf_counter() - t0)
    return round(1e3 * float(np.median(ts)), 3)


def cut_demo(inst, small, brute):
    """One cutting plane on Lea's hour, small enough to say out loud: "at most k
    orders". It is *derived from the model's own data*, in the spirit of a cover
    cut: every delivery takes at least the quickest ride into it, so the (k + 1)
    quickest deliveries need ``need`` minutes, and no delivery may happen after the
    last deadline. Enumeration only confirms it: the longest feasible course has k
    orders, and the fastest sequence of k + 1 deliveries, ignoring every window,
    takes ``fastest`` minutes. The root relaxation breaks the rule; adding it lowers
    the ceiling without any branching."""
    import itertools

    from scipy.optimize import linprog

    quickest = sorted(
        min(v for (_, j2), v in small.mins.items() if j2 == j) for j in small.orders
    )
    deadline = max(small.ub(j) for j in small.orders)
    k = max(q for q in range(len(quickest) + 1) if sum(quickest[:q]) <= deadline)
    need = sum(quickest[: k + 1])
    assert need > deadline + 0.5, "too close to call a rule"
    assert k == max(len(seq) for seq, _ in brute["all"]), "the rule is not tight"
    start = inst.couriers[0]
    fastest = min(  # pure riding and service time, on the full instance
        sum(inst.mins[a, b] for a, b in zip((start, *seq[:-1]), seq, strict=True))
        for seq in itertools.permutations(inst.orders, k + 1)
    )
    assert fastest >= need - 1e-9 and fastest > deadline
    c, A, b, lo, hi, xi, _ = model.matrices(small)
    row = np.zeros(len(c))
    for q in xi.values():
        row[q] = 1.0  # every ride delivers exactly one order
    bounds = np.column_stack([lo, hi])
    before = linprog(-c, A_ub=A, b_ub=b, bounds=bounds, method="highs")
    after = linprog(
        -c,
        A_ub=np.vstack([A, row]),
        b_ub=np.append(b, k),
        bounds=bounds,
        method="highs",
    )
    nx = len(xi)
    assert before.x[:nx].sum() > k + 1e-6, "the relaxed plan does not break the rule"
    assert -after.fun < -before.fun - 1e-6
    return {
        "max_orders": k,
        "need": round(float(need), 2),  # minutes for the k + 1 quickest deliveries
        "fastest": round(float(fastest), 2),  # the fastest real sequence of k + 1
        "deadline": round(float(deadline), 3),  # the last minute anything is due
        "relaxed_orders": round(float(before.x[:nx].sum()), 3),
        "before": round(-float(before.fun), 4),
        "bound": round(-float(after.fun), 4),
        "x": {
            key(r): round(float(after.x[q]), 4)
            for r, q in xi.items()
            if after.x[q] > 1e-7
        },
    }


def _log_body(text):
    """A Gurobi log without what changes from run to run (dates, timings)."""
    import re

    out = []
    for line in text.splitlines():
        if line.startswith(("Gurobi 14", "Set parameter LogFile", "Presolve time")):
            continue
        if "seconds" in line or "work units" in line:
            continue
        out.append(re.sub(r"\s+\d+s$", "", line))
    return out


def refresh_windows(doc, world):
    """Write every zone's delivery windows at full precision (they were rounded to
    3 decimals on export). No solver run: the casts are rebuilt from their seeds and
    must equal the stored ones after rounding."""
    n = 0
    for zone in doc["city"]["zones"]:
        kk, nn, _ = zone_size(world, zone["arr"])
        inst = story.zone_instance(
            world, zone["arr"], kk, nn, CITY_SEED + zone["arr"]
        ).inst
        assert [o["name"] for o in zone["orders"]] == inst.orders
        for o in zone["orders"]:
            e, late = float(inst.early[o["name"]]), float(inst.late[o["name"]])
            assert round(e, 3) == round(o["early"], 3), (zone["arr"], o["name"])
            assert (
                round(late, 3) == round(o["late"], 3)
                and inst.pay[o["name"]] == o["pay"]
            )
            n += (o["early"], o["late"]) != (e, late)
            o["early"], o["late"] = e, late
    return n


def patch_data():
    """Write the two instances a reader can run (``demo/course.py``) into
    ``story.json`` at full precision, and the district's log in full.

    They used to be rounded on export (4 and 3 decimals), and a solver takes another
    path through the search on rounded data: our own branch and bound needs 93 nodes
    instead of 129, Gurobi's root relaxation reads 32.78635 instead of 32.78638. The
    film was right about its runs, but nobody could reproduce them from the file.

    The instances are rebuilt from the cached map, then checked three ways before
    anything is written: equal to the committed ones after rounding; same search
    tree; same Gurobi log for Lea's hour and the same node count for the district.
    Run it on an idle machine: the district's runtime replaces the baked one, so
    that the log and the numbers describe the same run."""
    path = ASSETS / "story.json"
    doc = json.loads(path.read_text())
    h, city_ = doc["hero"], doc["city"]
    zone = next(z for z in city_["zones"] if z["arr"] == city_["deep"])
    world = story.World()

    def same_after_rounding(inst, rows, mins):
        assert {key(k) for k in inst.mins} == set(mins)
        assert all(round(v, 4) == round(mins[key(k)], 4) for k, v in inst.mins.items())
        for o in rows:
            j = o["name"]
            assert round(inst.early[j], 3) == round(o["early"], 3), j
            assert (
                round(inst.late[j], 3) == round(o["late"], 3)
                and inst.pay[j] == o["pay"]
            ), j

    # ---- Lea's hour ------------------------------------------------------------
    cast = story.hero(world, HERO_SEED)
    inst = cast.inst
    same_after_rounding(inst, h["orders"], h["mins"])
    tree = model.branch_and_bound(model.presolve(inst))
    baked = h["tree"]["nodes"]
    assert len(tree["nodes"]) == len(baked) and tree["lps"] == h["tree"]["lps"]
    for a_, b_ in zip(tree["nodes"], baked, strict=True):
        assert (a_["kind"], a_["parent"], a_["lp"]) == (
            b_["kind"],
            b_["parent"],
            b_["lp"],
        )
        # (the baked bounds are rounded to 4 decimals)
        assert a_["bound"] is None or abs(a_["bound"] - b_["bound"]) < 1e-4
    logs = Path(tempfile.mkdtemp(prefix="mip-gurobi-"))
    model.solve_gurobi(inst, log=logs / "course.log")
    kept = (ASSETS / "gurobi_course.txt").read_text()
    assert _log_body((logs / "course.log").read_text()) == _log_body(kept)
    h["mins"] = {key(k): float(v) for k, v in inst.mins.items()}
    for o in h["orders"]:
        o["early"], o["late"] = (
            float(inst.early[o["name"]]),
            float(inst.late[o["name"]]),
        )

    # ---- the district ------------------------------------------------------------
    kk, nn, _ = zone_size(world, city_["deep"])
    cast = story.zone_instance(world, city_["deep"], kk, nn, CITY_SEED + city_["deep"])
    inst = cast.inst
    same_after_rounding(inst, zone["orders"], zone["mins"])
    gur = model.solve_gurobi(inst, log=logs / "district.log")
    text = (logs / "district.log").read_text()
    assert (gur["optimal"], gur["nodes"], gur["obj"]) == (
        True,
        zone["nodes"],
        zone["obj"],
    )
    assert (
        f"Explored {zone['nodes']} nodes" in text and "Optimal solution found" in text
    )
    assert abs(gur["runtime"] / zone["runtime"] - 1) < 0.08, (
        gur["runtime"],
        zone["runtime"],
        "run it again on an idle machine",
    )
    keep_log(logs / "district.log", "district")
    zone["mins"] = {key(k): float(v) for k, v in inst.mins.items()}
    for o in zone["orders"]:
        o["early"], o["late"] = (
            float(inst.early[o["name"]]),
            float(inst.late[o["name"]]),
        )
    refresh_windows(doc, world)
    doc["district"] = {
        "couriers": zone["couriers_names"],
        "orders": zone["orders"],
        "mins": zone["mins"],
    }
    old = zone["runtime"]
    zone["runtime"], zone["work"] = round(gur["runtime"], 4), round(gur["work"], 4)
    tot = city_["totals"]
    tot["runtime"] = round(tot["runtime"] - old + zone["runtime"], 2)
    path.write_text(json.dumps(doc, separators=(",", ":"), ensure_ascii=False))
    return {"district runtime": zone["runtime"], "was": old, "city": tot["runtime"]}


def patch(what):
    """Recompute one small piece of an existing ``story.json`` (HiGHS only: no Gurobi
    run, so the baked solver timings stay as they are). ``what``: "cut" (the
    cutting-plane demo) or "lp" (how long one relaxation takes)."""
    path = ASSETS / "story.json"
    doc = json.loads(path.read_text())
    h = doc["hero"]
    names = [o["name"] for o in h["orders"]]
    inst = model.Instance(
        h["couriers"],
        names,
        {o["name"]: o["pay"] for o in h["orders"]},
        {tuple(k.split("|")): v for k, v in h["mins"].items()},
        {o["name"]: o["early"] for o in h["orders"]},
        {o["name"]: o["late"] for o in h["orders"]},
    )
    small = model.presolve(inst)
    if what == "lp":
        assert abs(model.relaxation(small)[0] - h["tree"]["nodes"][0]["bound"]) < 1e-6
        h["tree"]["lp_ms"] = out = lp_time(small)
    else:
        brute = model.brute_force(inst, keep=True)
        assert brute["obj"] == h["brute"]["obj"] and brute["seq"] == h["brute"]["seq"]
        h["cut"] = out = cut_demo(inst, small, brute)
    path.write_text(json.dumps(doc, separators=(",", ":"), ensure_ascii=False))
    return out


def export_hero(cast, r):
    inst, small, brute, tree = r["inst"], r["small"], r["brute"], r["tree"]
    seq = brute["seq"]
    verts, events = cast.timeline("lea", seq)
    rng = np.random.default_rng(1)
    # a sample of real, feasible courses (for the "try them all" beat): whole
    # courses only (nothing more fits after them), a spread of revenues
    full = [
        (s, p)
        for s, p in brute["all"]
        if not any(
            len(s2) == len(s) + 1 and s2[: len(s)] == s for s2, _ in brute["all"]
        )
    ]
    pick = rng.permutation(len(full))[:14]
    sample = [{"seq": full[k][0], "pay": full[k][1]} for k in sorted(pick)]
    nodes = []
    for n in tree["nodes"]:
        row = {
            "id": n["id"],
            "parent": n["parent"],
            "depth": n["depth"],
            "ride": key(n["ride"]) if n["ride"] else None,
            "take": n["take"],
            "kind": n["kind"],
            "lp": n["lp"],
            "bound": None if n.get("bound") is None else round(n["bound"], 4),
            "x": {key(k): round(v, 4) for k, v in n["x"].items()},
            "floor": n["floor"],
            "ceiling": None if n["ceiling"] is None else round(n["ceiling"], 4),
        }
        if n.get("incumbent"):
            row["incumbent"] = True
            row["seq"] = model.courses_of(
                small, {k: round(v) for k, v in n["x"].items()}
            )["lea"]
        if n["kind"] == "branch":
            row["var"] = key(n["var"])
        nodes.append(row)
    g = r["gurobi"]
    return {
        "couriers": inst.couriers,
        "start": {"lea": story._pt(cast.xy("lea"))},
        "orders": cast.order_rows(),
        # full precision: a solver takes another path on rounded data
        "mins": {key(k): float(v) for k, v in inst.mins.items()},
        "approach": {
            key((i, j)): story.pts(cast.approach(i, j)) for i, j in inst.rides
        },
        "leg": {j: story.pts(cast.leg(j)) for j in inst.orders},
        "presolve": {
            "rides": [key(k) for k in small.rides],
            "early": {j: round(v, 3) for j, v in small.early.items()},
        },
        "brute": {
            "obj": brute["obj"],
            "seq": seq,
            "feasible": brute["feasible"],
            "sequences": brute["sequences"],
            "sample": sample,
        },
        "greedy": {
            rule: {"seq": c["lea"], "obj": model.revenue(inst, c)}
            for rule, c in r["greedy"].items()
        },
        "gurobi": {
            k: g[k]
            for k in (
                "obj",
                "bound",
                "nodes",
                "runtime",
                "vars",
                "binaries",
                "rows",
                "indicators",
            )
        },  # fmt: skip
        "highs": {"obj": r["highs"]["obj"]},
        "cut": cut_demo(inst, small, brute),
        "tree": {
            "nodes": nodes,
            "lps": tree["lps"],
            "obj": tree["obj"],
            "lp_ms": lp_time(small),
        },
        "timeline": {
            "v": [
                [round(float(a), 3), round(float(b), 1), round(float(c), 1)]
                for a, b, c in verts
            ],
            "events": [[k, j, round(float(t), 3)] for k, j, t in events],
        },
    }


# --------------------------------------------------------------------------- #
# the city: one model per arrondissement
# --------------------------------------------------------------------------- #
def zone_size(world, arr):
    """Orders and couriers of an arrondissement, from how many restaurants it has."""
    food = int((world.food_arr == arr).sum())
    n = int(np.clip(round(food / 30), 14, 32))
    return max(3, round(n / 4)), n, food


def solve_zone(world, arr, seed, k=None, n=None, record=False, log=None, time_limit=30):
    kk, nn, food = zone_size(world, arr)
    k, n = k or kk, n or nn
    cast = story.zone_instance(world, arr, k, n, seed)
    inst = cast.inst
    params = {} if time_limit is None else {"TimeLimit": time_limit}
    gur = model.solve_gurobi(inst, log=log, record=record, **params)
    courses = model.courses_of(inst, gur["x"])
    model.check(inst, courses)
    assert model.revenue(inst, courses) == gur["obj"], (
        model.revenue(inst, courses),
        gur["obj"],
    )
    greedy = {rule: model.greedy(inst, rule) for rule in ("soon", "pay")}
    for c in greedy.values():
        model.check(inst, c)
    return {
        "arr": arr,
        "cast": cast,
        "gurobi": gur,
        "courses": courses,
        "greedy": greedy,
        "food": food,
    }


def export_zone(z, deep=False):
    cast, inst, gur, courses = z["cast"], z["cast"].inst, z["gurobi"], z["courses"]
    delivered = {}
    couriers = []
    for c in inst.couriers:
        verts, events = cast.timeline(c, courses[c])
        for kind, j, t in events:
            if kind == "deliver":
                delivered[j] = round(float(t), 3)
        couriers.append(
            {
                "name": c,
                "start": story._pt(cast.xy(c)),
                "seq": courses[c],
                "v": [
                    [round(float(a), 3), round(float(b), 1), round(float(d), 1)]
                    for a, b, d in verts
                ],
                "events": [[kind, j, round(float(t), 3)] for kind, j, t in events],
            }
        )
    orders = cast.order_rows()
    for o in orders:
        o["t"] = delivered.get(o["name"])
    out = {
        "arr": z["arr"],
        "food": z["food"],
        "couriers": couriers,
        "orders": orders,
        "obj": gur["obj"],
        "bound": gur["bound"],
        "gap": gur["gap"],
        "optimal": gur["optimal"],
        "nodes": gur["nodes"],
        "runtime": round(gur["runtime"], 4),
        "work": round(gur["work"], 4),
        "binaries": gur["binaries"],
        "delivered": len(delivered),
        "greedy": {rule: model.revenue(inst, c) for rule, c in z["greedy"].items()},
        "greedy_delivered": {
            rule: sum(len(s) for s in c.values()) for rule, c in z["greedy"].items()
        },
    }
    if deep:
        used = set()
        plans = []
        for p in gur["plans"]:
            cs = model.courses_of(inst, p["x"])
            model.check(inst, cs)
            assert abs(model.revenue(inst, cs) - p["obj"]) < 1e-6
            plans.append(
                {
                    "time": round(p["time"], 4),
                    "obj": round(p["obj"], 2),
                    "nodes": p["nodes"],
                    "courses": cs,
                }
            )
            for c, seq in cs.items():
                i = c
                for j in seq:
                    used.add((i, j))
                    i = j
        for c in z["greedy"]["soon"]:
            i = c
            for j in z["greedy"]["soon"][c]:
                used.add((i, j))
                i = j
        trace, last = [], None
        for t, obj, bnd, nodes in gur["trace"]:
            row = (round(obj, 2), round(bnd, 3))
            if row != last:
                trace.append([round(t, 4), row[0], row[1], nodes])
                last = row
        out.update(
            couriers_names=inst.couriers,
            mins={key(k): float(v) for k, v in inst.mins.items()},
            plans=plans,
            trace=trace,
            approach={key(r): story.pts(cast.approach(*r), 2.5) for r in sorted(used)},
            leg={j: story.pts(cast.leg(j), 2.5) for j in inst.orders},
            greedy_courses=z["greedy"]["soon"],
            vars=gur["vars"],
            rows=gur["rows"],
            indicators=gur["indicators"],
            recorded_runtime=round(gur["runtime_recorded"], 4),
        )
    return out


def zones_report(world, seed):
    print(
        "arr food  k  n | status  obj   bound   gap%  nodes  time | greedy soon pay | delivered"
    )
    tot = np.zeros(4)
    for arr in range(1, 21):
        z = solve_zone(world, arr, seed + arr)
        g, e = z["gurobi"], export_zone(z)
        tot += [g["obj"], e["greedy"]["soon"], e["greedy"]["pay"], g["runtime"]]
        print(
            f"{arr:3d} {z['food']:4d} {len(z['cast'].inst.couriers):2d} {len(z['cast'].inst.orders):2d} |"
            f" {'opt' if g['optimal'] else 'lim'} {g['obj']:6.1f} {g['bound']:7.2f} {100 * g['gap']:5.2f}"
            f" {g['nodes']:7d} {g['runtime']:5.1f} | {e['greedy']['soon']:6.1f} {e['greedy']['pay']:6.1f} |"
            f" {e['delivered']}/{len(e['orders'])} vs {e['greedy_delivered']['soon']}",
            flush=True,
        )
    print(
        f"total: optimal {tot[0]:.1f}, greedy soon {tot[1]:.1f}"
        f" ({100 * (tot[0] / tot[1] - 1):+.1f}%), greedy pay {tot[2]:.1f}, {tot[3]:.1f} s"
    )


if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    if len(sys.argv) > 1 and sys.argv[1] in ("patch-cut", "patch-lp"):
        print(patch(sys.argv[1].split("-")[1]))
        sys.exit(0)
    if len(sys.argv) > 1 and sys.argv[1] == "patch-data":
        print(patch_data())
        sys.exit(0)
    if not city.GEOMETRY.exists():
        city.bake_geometry()
    t0 = time.time()
    world = story.World()
    print(f"world: {world.graph.stats} ({time.time() - t0:.1f} s)")
    if len(sys.argv) > 1 and sys.argv[1] == "scan":
        scan(world, int(sys.argv[2]), int(sys.argv[3]))
        sys.exit(0)
    if len(sys.argv) > 1 and sys.argv[1] == "zones":
        zones_report(world, int(sys.argv[2]) if len(sys.argv) > 2 else CITY_SEED)
        sys.exit(0)

    # ---- Lea's hour ---------------------------------------------------------- #
    ASSETS.mkdir(exist_ok=True)
    logs = Path(tempfile.mkdtemp(prefix="mip-gurobi-"))  # Gurobi appends: start clean
    cast = story.hero(world, HERO_SEED)
    r = solve_hero(cast, log=logs / "course.log")
    keep_log(logs / "course.log", "course")
    hero = export_hero(cast, r)
    s = tree_stats(r["tree"])
    print(
        f"hero: optimum {r['brute']['obj']} EUR = {' > '.join(r['brute']['seq'])};"
        f" greedy {hero['greedy']['pay']['obj']} / {hero['greedy']['soon']['obj']};"
        f" tree {s['nodes']} nodes, {s['lps']} LPs, plans {s['plans']}; Gurobi {r['gurobi']['nodes']} node(s)"
    )

    # ---- the city ------------------------------------------------------------ #
    zones = []
    for arr in range(1, 21):
        deep = arr == DEEP_ARR
        log = logs / "district.log"
        # the zone the film shows is solved by the plain call, without a time limit:
        # "same model, same call", and the log a reader gets from demo/course.py
        z = solve_zone(
            world,
            arr,
            CITY_SEED + arr,
            record=deep,
            log=log if deep else None,
            time_limit=None if deep else 30,
        )
        if deep:
            keep_log(log, "district")
        zones.append(export_zone(z, deep=deep))
        e = zones[-1]
        print(
            f"  {arr:2d}e: {len(e['couriers'])} couriers, {len(e['orders'])} orders,"
            f" {e['obj']:.1f} EUR ({'optimal' if e['optimal'] else 'gap %.2f%%' % (100 * e['gap'])}),"
            f" {e['nodes']} nodes, {e['runtime']:.2f} s; greedy {e['greedy']['soon']:.1f}",
            flush=True,
        )
    district = next(z for z in zones if z["arr"] == DEEP_ARR)
    # demo/course.py reads the district the same way as Lea's hour
    district["couriers_start"] = {c["name"]: c["start"] for c in district["couriers"]}

    totals = {
        "couriers": sum(len(z["couriers"]) for z in zones),
        "orders": sum(len(z["orders"]) for z in zones),
        "binaries": sum(z["binaries"] for z in zones),
        "obj": round(sum(z["obj"] for z in zones), 1),
        "greedy": round(sum(z["greedy"]["soon"] for z in zones), 1),
        "greedy_pay": round(sum(z["greedy"]["pay"] for z in zones), 1),
        "delivered": sum(z["delivered"] for z in zones),
        "greedy_delivered": sum(z["greedy_delivered"]["soon"] for z in zones),
        "runtime": round(sum(z["runtime"] for z in zones), 2),
        "nodes": sum(z["nodes"] for z in zones),
        "all_optimal": all(z["optimal"] for z in zones),
        # ways to hand out the orders, ignoring their sequence: every order goes to
        # one of the zone's couriers or to nobody
        "log10_assignments": round(
            sum(len(z["orders"]) * math.log10(len(z["couriers"]) + 1) for z in zones), 1
        ),
    }
    doc = {
        "hero": hero,
        "district": {
            "couriers": district["couriers_names"],
            "orders": district["orders"],
            "mins": district["mins"],
        },
        "city": {"zones": zones, "totals": totals, "deep": DEEP_ARR},
        "meta": {
            "shift": model.SHIFT,
            "pickup": model.PICKUP,
            "drop": model.DROP,
            "speed_kmh": 15,
            "fee": [story.FEE_BASE, story.FEE_PER_KM],
            "graph": world.graph.stats,
            "food_nodes": int(len(world.food_xy)),
            "hero_seed": HERO_SEED,
            "city_seed": CITY_SEED,
        },
    }
    (ASSETS / "story.json").write_text(
        json.dumps(doc, separators=(",", ":"), ensure_ascii=False)
    )
    print(f"totals: {totals}")
    print(
        f"story.json: {(ASSETS / 'story.json').stat().st_size / 1e6:.2f} MB ({time.time() - t0:.0f} s)"
    )

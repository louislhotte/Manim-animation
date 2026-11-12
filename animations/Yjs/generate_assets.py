#!/usr/bin/env python3
"""Bake the REAL data behind the Yjs film (house rule: compute, don't type numbers in).

Copies ``demo/`` to a local temp dir (never into this OneDrive-synced repo), runs
``npm install`` there, then actually runs:

    story.mjs   the film's story on real Yjs: three replicas, concurrent inserts, a
                same-position conflict, an offline peer, the state-vector handshake;
                then the story's 8 updates delivered in every order (8! = 40,320)
                and three times each in random order.          -> assets/story.json
    bench.mjs   a real-world editing trace (259,778 keystrokes of a published paper,
                Kleppmann & Beresford, CC BY 4.0, automerge/automerge-perf) replayed
                on Yjs, Automerge and Loro.                    -> assets/bench.json
    stack.mjs   two real Tiptap editors + a headless agent on a real Hocuspocus
                server: concurrent edits, a dropped connection, a server restart.
                                                               -> assets/stack.json

and asks the npm registry for release dates and last week's download counts
(-> assets/npm.json). Needs node >= 22, npm and network access; run manually
(``./render.sh --assets``), not at render time. Renders stay offline.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEMO = HERE / "demo"
ASSETS = HERE / "assets"
TRACE_URL = (
    "https://raw.githubusercontent.com/automerge/automerge-perf/master/"
    "edit-by-index/editing-trace.js"
)
RUNS = {"yjs": 5, "loro": 5, "automerge": 3}  # median of N wall-clock runs
ENV = {**os.environ, "NO_COLOR": "1", "CI": "1", "npm_config_update_notifier": "false"}


def run(cmd, cwd, timeout=900):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    p = subprocess.run(
        [str(c) for c in cmd],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=ENV,
    )
    if p.returncode != 0:
        print(p.stdout[-3000:])
        print(p.stderr[-3000:])
        raise SystemExit(f"command failed: {cmd}")
    return p.stdout


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "manim-explainer-bake"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def cpu_name():
    try:
        out = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        return out or platform.processor() or platform.machine()
    except OSError:
        return platform.processor() or platform.machine()


def bake_story(app):
    story = json.loads(run(["node", "story.mjs"], app))
    # the facts the film states, asserted here so a library change cannot silently
    # turn the film into fiction
    final = "CRDTs merge all edits, even offline"
    assert story["final"]["text"] == final and story["final"]["converged"], story[
        "final"
    ]
    snaps = story["snaps"]
    assert snaps["concurrent_local"]["ada"]["text"] == "CRDT"
    assert snaps["concurrent_local"]["bob"]["text"] == "CRTs"
    assert {s["text"] for s in snaps["concurrent_merged"].values()} == {"CRDTs"}
    assert {s["text"] for s in snaps["samespot_merged"].values()} == {
        "CRDTs merge edits in any order"
    }
    assert (
        snaps["offline"]["bob"]["text"]
        == "CRDTs merge edits in any order, even offline"
    )
    assert snaps["offline"]["online"]["text"] == "CRDTs merge all edits"
    p = story["perms"]
    assert (
        p["count"] == 40320 and p["distinct_texts"] == 1 and p["distinct_states"] == 1
    ), p
    assert p["text"] == final
    assert len(p["waited"]) == p["count"] and set(p["waited"]) <= set("01234567")
    assert sum(c != "0" for c in p["waited"]) == p["needed_pending"]
    d = story["dups"]
    assert d["distinct_texts"] == 1 and d["text"] == final, d
    assert all(t["steps"][-1]["text"] == final for t in story["traces"])
    (ASSETS / "story.json").write_text(json.dumps(story, indent=1))
    print(
        f">> story.json: {p['count']:,} delivery orders -> {p['distinct_texts']} text, "
        f"{p['needed_pending']:,} needed the pending queue; final {final!r}"
    )
    return story


def bake_bench(app, tmp):
    trace_dir = tmp / "trace"  # downloaded data lives alone, away from any script
    trace_dir.mkdir()
    trace = trace_dir / "editing-trace.js"
    print(f">> downloading the editing trace -> {trace}")
    req = urllib.request.Request(
        TRACE_URL, headers={"User-Agent": "manim-explainer-bake"}
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        trace.write_bytes(r.read())

    info = json.loads(run(["node", "bench.mjs", trace, "trace"], app))
    assert info["edits"] == 259778 and info["final_chars"] == 104852, info
    assert info["inserts"] - info["deletes"] == info["final_chars"]
    engines = {}
    for name, n in RUNS.items():
        rows = [
            json.loads(run(["node", "bench.mjs", trace, name], app)) for _ in range(n)
        ]
        assert all(r["ok"] and r["load_ok"] for r in rows), rows
        best = dict(rows[0])
        best["ms"] = statistics.median(r["ms"] for r in rows)
        best["load_ms"] = statistics.median(r["load_ms"] for r in rows)
        best["bytes"] = int(statistics.median(r["bytes"] for r in rows))
        best["runs"] = n
        best["ms_all"] = [round(r["ms"], 1) for r in rows]
        best["load_ms_all"] = [round(r["load_ms"], 2) for r in rows]
        engines[name] = best
        print(
            f"   {name:10s} {best['version']:8s} replay {best['ms']:8.0f} ms   "
            f"load {best['load_ms']:7.2f} ms   size {best['bytes']:,} B"
        )
    bench = {
        "source": "Kleppmann & Beresford editing trace, automerge/automerge-perf (CC BY 4.0)",
        "source_url": "https://github.com/automerge/automerge-perf",
        "method": "every edit is its own transaction / change / commit; median of N runs",
        "machine": cpu_name(),
        "node": engines["yjs"]["node"],
        "date": date.today().isoformat(),
        "trace": info,
        "engines": engines,
    }
    (ASSETS / "bench.json").write_text(json.dumps(bench, indent=1))
    return bench


def bake_stack(app):
    stack = json.loads(run(["node", "stack.mjs", "4391"], app, timeout=180))
    want = (
        "<h1>Release notes</h1><p>Live collaboration finally ships this week.</p>"
        "<p>Summary: we can all edit at once and stay in sync.</p>"
    )
    a = stack["after_agent"]
    assert a["ada"] == a["bob"] == want, a
    assert a["agent_xml"] == a["server_xml"]
    r = stack["after_reconnect"]
    assert r["ada"] == r["bob"] == stack["after_restart"], r
    assert stack["while_offline"]["ada"] != stack["while_offline"]["bob"]
    names = {s["user"]["name"] for s in stack["awareness"] if s["user"]}
    assert names == {"Ada", "Bob", "Agent"}, names
    assert stack["caret_labels_in_ada_editor"] == ["Agent"], stack[
        "caret_labels_in_ada_editor"
    ]
    assert (
        stack["defaults"]["debounce"] == 2000
        and stack["defaults"]["maxDebounce"] == 10000
    )
    (ASSETS / "stack.json").write_text(json.dumps(stack, indent=1))
    print(
        f">> stack.json: Tiptap {stack['versions']['tiptap']} + Hocuspocus "
        f"{stack['versions']['hocuspocus']}: converged, offline + restart survived"
    )
    return stack


def bake_npm():
    def weekly(pkg):
        q = urllib.parse.quote(pkg, safe="@")
        return get_json(f"https://api.npmjs.org/downloads/point/last-week/{q}")

    out = {"fetched": date.today().isoformat(), "downloads": {}, "created": {}}
    for pkg in (
        "yjs",
        "@automerge/automerge",
        "loro-crdt",
        "@tiptap/core",
        "@hocuspocus/server",
    ):
        w = weekly(pkg)
        out["downloads"][pkg] = w["downloads"]
        out["week"] = [w["start"], w["end"]]
    for pkg in ("yjs", "@automerge/automerge", "loro-crdt"):
        meta = get_json(
            "https://registry.npmjs.org/" + urllib.parse.quote(pkg, safe="@")
        )
        out["created"][pkg] = meta["time"]["created"][:10]
        if pkg == "yjs":
            out["yjs"] = {
                "latest": meta["dist-tags"]["latest"],
                "latest_date": meta["time"][meta["dist-tags"]["latest"]][:10],
                "v13_date": meta["time"]["13.0.0"][:10],
                "versions": len(meta["versions"]),
                "license": meta.get("license"),
            }
    assert out["yjs"]["latest"].startswith("13."), out[
        "yjs"
    ]  # the film says "still v13"
    (ASSETS / "npm.json").write_text(json.dumps(out, indent=1))
    print(
        f">> npm.json: yjs {out['downloads']['yjs']:,} downloads in the week of "
        f"{out['week'][0]}; v13 since {out['yjs']['v13_date']}"
    )
    return out


def main():
    only = set(sys.argv[1:])  # e.g. `generate_assets.py story npm` to re-bake a subset
    ASSETS.mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="yjs_assets_"))
    print(f">> working in {tmp}")
    app = tmp / "demo"
    shutil.copytree(
        DEMO, app, ignore=shutil.ignore_patterns("node_modules", "*.json.out")
    )
    try:
        if not only or only & {"story", "bench", "stack"}:
            run(["npm", "install", "--no-audit", "--no-fund", "--loglevel=error"], app)
            print(f">> node {run(['node', '--version'], app).strip()}")
        if not only or "story" in only:
            bake_story(app)
        if not only or "stack" in only:
            bake_stack(app)
        if not only or "bench" in only:
            bake_bench(app, tmp)
        if not only or "npm" in only:
            bake_npm()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(">> done")
    return 0


if __name__ == "__main__":
    sys.exit(main())

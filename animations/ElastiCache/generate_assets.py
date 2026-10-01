#!/usr/bin/env python3
"""Bake the real latency numbers used by the ElastiCache film.

The "why a cache is fast" scene compares reading a value from memory against
reading it from a database. Rather than invent numbers, we *measure* two honest
end-points on this machine:

    * an in-memory Python ``dict`` lookup   (stands in for the cache, in RAM)
    * an on-disk SQLite point-lookup on an indexed primary key
      (stands in for a local, disk-backed relational database)

We time hundreds of thousands of randomised lookups (after a warm-up), take the
median over several repeats, and write the result to ``assets/bench.json``. The
render reads that file; if it is missing it falls back to constants baked from a
previous run, so the film always shows real, computed numbers and never needs
the network.

This is deliberately run by hand (``python generate_assets.py``), not at render
time — the render stays offline and deterministic.
"""
from __future__ import annotations

import json
import os
import random
import sqlite3
import statistics
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")

N = 200_000          # number of key/value rows
LOOKUPS = 300_000    # timed lookups per repeat
REPEATS = 5          # take the median (best-of steady state)


def _make_data(n):
    keys = [f"user:{i}" for i in range(n)]
    vals = [f'{{"id":{i},"name":"user_{i}","plan":"pro","seats":{i % 50}}}' for i in range(n)]
    return keys, vals


def bench_dict(keys, vals, probe):
    d = dict(zip(keys, vals))
    # warm-up
    for k in probe[:20_000]:
        _ = d[k]
    per_op = []
    for _ in range(REPEATS):
        t0 = time.perf_counter()
        s = 0
        for k in probe:
            v = d[k]
            s += len(v)          # touch the value so it can't be optimised away
        t1 = time.perf_counter()
        per_op.append((t1 - t0) / len(probe))
    return statistics.median(per_op) * 1e9, s   # nanoseconds/op


def bench_sqlite(keys, vals, probe):
    path = os.path.join(tempfile.mkdtemp(prefix="ec_bench_"), "kv.sqlite")
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("CREATE TABLE kv (k TEXT PRIMARY KEY, v TEXT) WITHOUT ROWID;")
    con.executemany("INSERT INTO kv (k, v) VALUES (?, ?);", zip(keys, vals))
    con.commit()
    cur = con.cursor()
    sql = "SELECT v FROM kv WHERE k = ?;"
    # warm-up (also warms the OS page cache — a *generous* read for the DB)
    for k in probe[:20_000]:
        cur.execute(sql, (k,)).fetchone()
    per_op = []
    for _ in range(REPEATS):
        t0 = time.perf_counter()
        s = 0
        for k in probe:
            row = cur.execute(sql, (k,)).fetchone()
            s += len(row[0])
        t1 = time.perf_counter()
        per_op.append((t1 - t0) / len(probe))
    con.close()
    try:
        os.remove(path)
    except OSError:
        pass
    return statistics.median(per_op) * 1e6, s   # microseconds/op


def main():
    print(f">> Building {N:,} key/value rows…")
    keys, vals = _make_data(N)
    random.seed(0)
    probe = [random.choice(keys) for _ in range(LOOKUPS)]

    print(f">> Timing {LOOKUPS:,} in-memory dict lookups × {REPEATS} repeats…")
    ram_ns, _ = bench_dict(keys, vals, probe)

    print(f">> Timing {LOOKUPS:,} on-disk SQLite point-lookups × {REPEATS} repeats…")
    db_us, _ = bench_sqlite(keys, vals, probe)

    speedup = (db_us * 1000.0) / ram_ns   # both in ns

    out = {
        "n_rows": N,
        "lookups": LOOKUPS,
        "repeats": REPEATS,
        "ram_ns": round(ram_ns, 1),        # dict get, nanoseconds/op
        "db_us": round(db_us, 2),          # sqlite point-lookup, microseconds/op
        "speedup": round(speedup, 1),      # how many× faster RAM is here
    }
    os.makedirs(ASSETS, exist_ok=True)
    with open(os.path.join(ASSETS, "bench.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print("\n>> Measured on this machine:")
    print(f"   in-memory dict get   : {out['ram_ns']:.1f} ns")
    print(f"   on-disk SQLite get   : {out['db_us']:.2f} µs")
    print(f"   RAM is ~{out['speedup']:.0f}× faster here")
    print(f">> Wrote {os.path.join(ASSETS, 'bench.json')}")


if __name__ == "__main__":
    main()

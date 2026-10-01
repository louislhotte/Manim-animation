# Amazon ElastiCache — a short, house-style explainer

A no-voiceover Manim explainer on **Amazon ElastiCache**: what an in-memory cache
is, why it makes an app fast, the cache-aside read path, the hit-ratio payoff,
the finite-memory trade-offs (TTL / eviction / stale data), and what the managed
AWS service actually gives you (Redis / Valkey / Memcached in your VPC, a primary
with replicas and automatic failover, cluster-mode sharding).

Built in the shared dark house style (see `.claude/skills/manim-explainer`), all
text drawn with Manim `Text` (Pango), no LaTeX for captions.

**Measured runtime: 3:59** (`HowElastiCacheWorks`, real cadence, 239.8 s).

## What it teaches

1. **The problem** — every read travels to the database; the database reads from
   disk (slow) and, under load, repeats the same expensive query over and over.
2. **Why memory is fast** — a log-scale latency ladder (RAM ≈ 100 ns, SSD ≈ 100 µs,
   a database call ≈ 10 ms) plus a **real, measured** micro-benchmark on this
   machine: an in-memory `dict` lookup vs an on-disk SQLite point-lookup.
3. **The read path (cache-aside / lazy loading)** — check the cache first; on a
   miss, read the database and store the result; on a hit, serve from memory and
   never touch the database. Shown as a diagram and as the eight-line function.
4. **The payoff** — ten reads through the cache: at a 90% hit ratio, nine of ten
   never reach the database, so database load falls ten-fold and average latency
   collapses (0.9·0.5 ms + 0.1·(0.5+30) ms = **3.5 ms**, asserted in code).
5. **Memory is finite** — TTL expiry, LRU eviction when the cache is full, and the
   classic hazard: a cache is a copy, so it can go stale (invalidate on writes).
6. **Amazon ElastiCache** — the managed service: engines (Redis / Valkey /
   Memcached), a primary + replicas in your VPC, automatic failover (a replica is
   promoted when the primary dies), and cluster-mode sharding for horizontal scale.

## Real data

Per the house "real data beats a synthetic stand-in" rule, the "why memory is
fast" scene shows numbers that were actually measured, not invented:

- `generate_assets.py` times hundreds of thousands of randomised lookups (after a
  warm-up, median of several repeats) against an in-memory `dict` and an on-disk,
  primary-key-indexed SQLite table, and writes `assets/bench.json`.
- The last measured run: `dict` ≈ **113.8 ns**, SQLite point-lookup ≈ **2.3 µs**,
  RAM ≈ **20× faster** — and that is against a *warm, local, indexed* database, so
  it is a conservative floor; a real networked database call is milliseconds.
- The film loads `assets/bench.json` at import (with a baked fallback), so the
  render is offline and reproducible. Regenerate with:
  `python generate_assets.py`.

The canonical latency figures (RAM ~100 ns, SSD ~100 µs, database call ~10 ms) are
the widely-cited "latency numbers every programmer should know" orders of
magnitude; the measured `dict` result (~114 ns) lands right on the ~100 ns figure.

## Scenes

| render.sh name | class                 | beat                                   |
| -------------- | --------------------- | -------------------------------------- |
| `intro`        | `Intro`               | title card                             |
| `problem`      | `Problem`             | every read hits the (slow) database    |
| `memory`       | `Memory`              | RAM vs disk, with the real benchmark   |
| `cacheaside`   | `CacheAside`          | the read path + the code               |
| `payoff`       | `Payoff`              | hit ratio → load & latency collapse    |
| `eviction`     | `Eviction`            | TTL, LRU eviction, stale data          |
| `service`      | `Service`             | the managed AWS service                |
| `outro`        | `Outro`               | thanks / recap                         |
| `full`         | `HowElastiCacheWorks` | the whole film, intro to outro         |

## Rendering

```bash
./render.sh cacheaside --quick -q l   # fast layout check of one scene (480p15)
./render.sh full                      # whole film, 480p
./render.sh full -q h                 # final 1080p60 (slow — run in background)
./render.sh --stitch -q m             # render each scene and concat to one file
```

For the final HD render, write frames to a local disk (not the OneDrive-synced
repo) to avoid I/O stalls, then copy the mp4 back:

```bash
EC_MEDIA_DIR=/tmp/ec_media ./render.sh full -q h
```

Pacing knobs: `EC_QUICK=1` collapses all reading holds; `EC_DELAY` and `EC_READ`
tune the inter-step and per-caption reading rhythm.

`render.sh` reuses an existing Manim venv in the repo (HarnessEngineering / Fourier
/ CNN) if present, else bootstraps a local `.venv` from `requirements.txt`.

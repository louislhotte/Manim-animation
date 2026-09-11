# What are indexes? — a short explainer

A self-explanatory (no voice-over) Manim film about **database indexes**: why a
lookup with no index is slow, what an index actually *is*, why it makes searches
fast, and — the point of the piece — how a **composite (two-column) index**
works and why **column order matters**.

Running example: a `users` table (id, last_name, city) with eight concrete rows
standing in for **10,000,000**. `Vasquez` appears three times (Austin, Denver,
Miami); exactly one row is `(Vasquez, Denver)`. Every count and every number on
screen is derived from those rows (see the `assert`s in the source) — nothing is
faked.

## What it teaches

- **Without an index → a full table scan.** `WHERE last_name = 'Vasquez'` forces
  the engine to read *every* row to find the matches — **O(n)**, ten million
  reads for three hits.
- **What an index is.** A *separate, sorted copy* of a column, where each entry
  points back to its row (the **rowid**). Pull `last_name` out, sort it, and every
  entry keeps a `→ #id` pointer home.
- **Why it's fast.** Sorted data means **binary search** — check the middle, throw
  away half, repeat: `log₂(10,000,000) ≈ 23` checks instead of ten million. Real
  databases keep the index as a **B-tree**: wide fan-out, ~3–4 levels deep, so any
  row is ~3 hops away. **O(log n)**.
- **A composite (two-column) index.** `WHERE last_name='Vasquez' AND city='Denver'`
  on an index over **(last_name, city)** — sorted by last_name, then by city — seeks
  straight to the pair. A last_name-only index would still scan every Vasquez for
  the city.
- **The leftmost-prefix rule (why order matters).** A `(last_name, city)` index
  serves `last_name = …` and `last_name = … AND city = …`, but **not** `city = …`
  alone — Denver rows are scattered through the index, so there's no shortcut.
- **Recap card:** what an index buys (O(n)→O(log n), a sorted value→rowid map,
  ranges & ORDER BY) vs. what it costs (storage, slower writes, leftmost-prefix,
  index only what you query).

## Scenes

1. **Intro** — title card.
2. **Scan** — no index: the full table scan, a scanning beam + O(n).
3. **IndexIntro** — pull a column out, sort it, point each entry back to its row.
4. **Seek** — binary search on the sorted index → the B-tree; ~23 vs 10,000,000.
5. **Composite** — the two-column index seek + the leftmost-prefix rule.
6. **Recap** — what an index buys you vs. what it costs.
7. **Outro** — thank-you card.

Bookended by the channel's intro / outro cards, matching the sibling explainers
(`animations/PrecisionRecall`, `animations/RBAC`, …). Uses `Text` (Pango) only —
**no LaTeX**; SQL is set in Menlo.

## Render

```bash
./render.sh full            # whole film, 480p15 (fast)
./render.sh full -q h       # final 1080p60 (the delivered quality)
./render.sh composite       # a single scene
./render.sh seek --quick    # collapse the reading holds for a fast layout check
./render.sh --stitch -q m   # render each scene and ffmpeg-concat to one file
```

Scenes: `full` (default) · `intro` · `scan` · `index` · `seek` · `composite` ·
`recap` · `outro`.

`render.sh` reuses an existing Manim venv elsewhere in the repo
(HarnessEngineering / Fourier / CNN), else bootstraps a local `.venv`.

Env knobs: `IDX_QUICK=1` shortens every hold for a fast sanity render;
`IDX_DELAY=x` overrides the reading-hold multiplier.

## Runtime

Measured full-film duration (1080p60, 1920×1080): **2 min 11 s**.

Pacing is deliberately unhurried so every line can be read before the scene
wipes: `DELAY` (reading-hold multiplier, default 1.6) and `END_HOLD` (extra hold
on each scene's final frame). Drop them via `IDX_DELAY` / `IDX_QUICK=1` to iterate
faster.

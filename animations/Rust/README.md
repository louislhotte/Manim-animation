# What is Rust?

A no-voiceover Manim explainer that answers "What is Rust?" head on: a compiled
systems language whose claim to fame is **memory safety and C-level speed at
the same time**, and how the **ownership model and the borrow checker** make
that possible with **zero run-time cost**.

Runtime: **5:34** (measured with `ffprobe` on the 1080p60 deliverable at the
default cadence; the 480p15 render rounds waits up to 5:38).

## What it teaches

1. **Definition** — what Rust actually is: compiled, systems-level, born at
   Mozilla (1.0 in 2015), no garbage collector, no runtime.
2. **The old tradeoff** — the safety-vs-speed chart: managed languages pay a GC
   tax, C/C++ pay in memory bugs (~70% of severe security bugs in Windows and
   Chrome are memory bugs, per Microsoft/Chromium), and the fast-and-safe
   corner stayed empty.
3. **Ownership** — one owner per value, moves on assignment, freed
   deterministically at scope end. Ends on rustc's **real E0382** output
   (use after move), captured verbatim from `bench/move_demo.rs`.
4. **Borrowing** — shared `&` loans vs the exclusive `&mut` loan: any number of
   readers, or exactly one writer, never both.
5. **The bug it kills** — `let first = &v[0]; v.push(4);` — push reallocates,
   the old buffer is freed, `first` dangles. In C++ that is a use-after-free at
   run time; in Rust it is the **real E0502** rejection at compile time
   (`bench/borrow_demo.rs`, output shown verbatim).
6. **Why Rust is fast** — no GC pauses (the Discord Go-to-Rust story), safety
   checks spent at compile time (nothing ships in the binary), and zero-cost
   abstractions (iterators compile to the hand-written loop).
7. **Let's measure it** — a **real benchmark baked from this machine**: the
   same trial-division prime count, line for line, in CPython and in Rust.
8. **Rust in the real world** — Linux kernel (since 6.1, 2022), Android's
   memory-bug share falling 76% → 24% (Google, 2019→2024), Stack Overflow's
   most-admired language nine years running; used by Microsoft, Cloudflare,
   Discord, AWS, Firefox.

## The real data (house rule: no mock-ups)

Baked by `generate_assets.py` (run it manually to refresh; the render itself is
offline and reads `assets/`):

- `assets/bench.json` — `bench/count_primes.py` vs `bench/count_primes.rs`
  (identical algorithm, single thread, best of 3). Last run on an Apple M4 Max:
  **CPython 3.12.12: 2.4311 s** vs **rustc 1.93.0 `-O`: 0.04507 s = 53.9x**,
  both finding exactly **78,498** primes below 1,000,000 (asserted equal, and
  asserted == π(10⁶) at import).
- `assets/errors.json` — rustc's verbatim stderr for the two demo files:
  `error[E0382]: borrow of moved value: 's'` and
  `error[E0502]: cannot borrow 'v' as mutable because it is also borrowed as
  immutable`. The film renders these in terminal panels, text untouched
  (long lines soft-wrapped like a terminal would).

Claim sources: Microsoft (BlueHat IL 2019) and the Chromium project both report
~70% of severe security bugs are memory-safety bugs; Google's Android security
post (Sept 2024) for the 76%→24% drop; Discord's 2020 engineering blog "Why
Discord is switching from Go to Rust"; Stack Overflow Developer Survey
2016–2024 ("most loved/admired").

## Scenes

| `render.sh` name | Class        | Beat                                   |
| ---------------- | ------------ | -------------------------------------- |
| `intro`          | `Intro`      | Title card                             |
| `definition`     | `Definition` | What is Rust? (the direct answer)      |
| `tradeoff`       | `Tradeoff`   | Safety vs speed, the empty corner      |
| `ownership`      | `Ownership`  | One owner, scope drop, real E0382      |
| `borrow`         | `Borrow`     | `&` vs `&mut`, the one rule            |
| `dangling`       | `Dangling`   | Vec realloc use-after-free, real E0502 |
| `speed`          | `Speed`      | No GC, compile-time checks, zero-cost  |
| `bench`          | `Bench`      | The measured 54x                       |
| `world`          | `World`      | Adoption + takeaway                    |
| `outro`          | `Outro`      | Thank-you card                         |
| `full`           | `WhatIsRust` | Whole film                             |

## Render

```bash
./render.sh ownership --quick -q l   # fast layout check of one scene
./render.sh full                     # whole film, 480p15
./render.sh full -q h                # final 1080p60 (slow)
```

Reuses the HarnessEngineering venv (manim 0.21) if present. Knobs:
`RS_QUICK=1` collapses holds, `RS_DELAY` / `RS_READ` tune the reading rhythm,
`RS_MEDIA_DIR=/tmp/rs_media` dodges OneDrive I/O stalls for HD renders.

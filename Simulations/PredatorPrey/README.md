# Predator & Prey — a school that learns to survive

A 2-D vector simulation of a **school of fish** and a **hunting shark**, built to
show how *collective intelligence* can emerge from simple local rules — and,
next, how **reinforcement learning** grows it: fish that survive get to pass on
their behaviour, so the population gets harder to catch generation after
generation.

This is **not** a Manim animation. Manim is for scripted, frame-by-frame
explainers; a live agent simulation with its own dynamics belongs in a fast
NumPy + matplotlib loop. Hence the separate `Simulations/` tree.

![the tank](media/preview.png)

## What it models

- A big square **tank** (`size`, default 120 units) holding `n_fish` fish and
  `n_sharks` sharks.
- **Fish** steer with classic *boids* — separation, alignment, cohesion — so a
  school forms on its own. On top of that they **evade** the nearest shark and
  **lunge** (a short speed burst, drawn gold) when it gets too close.
- The **shark** greedily chases the nearest fish and **lunges** to close the
  gap. Any fish within `eat_radius` of the shark is **eaten** (a red flash).
- The right-hand panel tracks **surviving fish over time** — the metric the RL
  engine will push upward across generations.

## Project layout (Phase 1 — the simulator tool)

| file | role |
|------|------|
| `config.py`  | one `SimConfig` dataclass — every knob lives here |
| `physics.py` | `World`: state + vectorised motion, walls, eating (no policy) |
| `brains.py`  | `FishBrain` (boids + evasion) and `SharkBrain` (pursuit) |
| `sim.py`     | `Simulation`: wires world + brains, tracks survivors |
| `viz.py`     | matplotlib arena + live survivors panel + stats key; mp4 / PNG |
| `cards.py`   | intro / rules / outro title cards (house style) |
| `film.py`    | stitches intro + rules + sim + outro into one mp4 (ffmpeg) |
| `run.py`     | CLI entry point |

The split is deliberate: **physics and rendering never import a brain**, so the
Phase-2 RL engine just supplies a learned `fish_act` and everything else is
reused untouched.

## The film

`./render.sh` produces a bookended film in the repo's house style (like the Manim
explainers):

1. **Title card** — *Predator & Prey* + the "Created by Ptolémé" byline.
2. **Rules card** — fish vs shark stats and the lunge, then the one rule —
   *every fish steers opposite the nearest shark, unless a wall is in the way* —
   and the punchline **"This is math, not magic."**
3. **The simulation** — 2 minutes; a colour-coded stats key stays along the
   bottom. Tuned (`seed 5`) so the shark eats **~half** the school by the end.
4. **Outro** — "Thank you for watching!".

## Running

```bash
./render.sh                 # build the full film -> media/demo.mp4 (1080p)
./render.sh --headless      # run one episode, print survival stats
./render.sh --save sim.mp4  # just the simulation, no cards
./render.sh --snapshot media/frame.png   # single preview frame
./render.sh --watch         # live window (needs a display)
```

First run creates a local `.venv` (numpy + matplotlib only). `ffmpeg` is used for
mp4 export and to stitch the cards onto the sim. The default render is the **full
~2 min 20 s film** (title → rules → 2-min sim → thanks) as **1920×1080 H.264**
(CRF 18), using the calibrated `seed 5`.

## Tuning

Everything is in `config.py`. The most useful dials:

- `shark_cruise` — **the dominant mortality dial** (keeps the shark in contact).
- `shark_burst`, `eat_radius`, `n_sharks` — how deadly each strike is.
- `w_evade`, `fish_burst`, `fish_lunge_cooldown` — how well the school escapes.
- `n_fish`, `size`, `max_seconds` — scale and length of the scene.

The demo is calibrated (`seed 5`) so the shark eats **~50%** of the school over
the 2-minute run — the survivors curve crosses the drawn "½ population" line right
at the end. Mortality tracks the shark↔fish *speed gap* and is very nonlinear
(e.g. `shark_cruise` ≈ 18 → 50% eaten, ≈ 20 → 60%, ≈ 24 → ~100%). This hand-coded
balance is the *expert ceiling*; the Phase-2 learning story starts from a random
policy that does far worse and climbs toward it.

## Roadmap

- **Phase 1 — simulator tool** ✅ (this) — physics, boids, shark, visualisation.
- **Phase 2 — RL engine** — each fish carries a tiny neural-net policy;
  neuroevolution selects the survivors (fitness = time survived), and the
  survivors panel becomes a *per-generation learning curve*.
- **Phase 3 — iterate** — tune predator/prey balance, co-evolve the shark,
  richer sensing, and a polished export.

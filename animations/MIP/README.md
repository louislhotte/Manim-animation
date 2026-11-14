# Mixed-Integer Programming

How a solver finds the best plan, and proves it. A house-style Manim film built on
`manimx`, **made to be narrated**: **8:55** (535.8 s, measured on the 1080p60
render, `MIP_1080p60.mp4`; 31 narration lines, 1,090 words), with flat scenes and
scenes on a 3D map of Paris.

The example is food delivery on a Friday night in Paris: which courier delivers
which order, in which sequence, to earn the most in one hour. The film follows one
courier (Léa, one hour, eight orders) to explain what a mixed-integer program is
and how a solver such as Gurobi solves it: presolve, the LP relaxation, branch and
bound, heuristics and cutting planes, the gap. It ends on the whole city: twenty
models, 104 couriers, 403 orders.

## Scenes (`render.sh` name, class)

| # | name | class | what it shows |
|---|------|-------|---------------|
| 0 | `intro` | `Intro` | house title card |
| 1 | `night` | `Night` (3D) | Paris, tilted, real streets; 104 couriers and 403 orders appear; random assignments flicker (10^325 ways to hand out the orders, district by district); the camera dives to one courier |
| 2 | `hour` | `Hour` | Léa's corner of the Marais; her eight orders on the map and in a table (fee, delivery window); the course her instinct picks (€11.90); every sequence tried (109,600): the best course earns €24.40; with twenty orders, 200,000 years |
| 3 | `model` | `Model` (3D) | the real gurobipy model, line by line, each line with its picture on the map: 64 binary rides, the fees, the rules; then the map tilts and time becomes height: one delivery minute per order, windows as bars; then the rule that links two minutes, the course as a thread through the bars; `m.optimize()` |
| 4 | `relax` | `Relax` | presolve (28 of 64 rides can never fit the clock); the LP relaxation (a switch becomes a dimmer; one ride at 0.52, another at 0.76, then the whole fractional plan); its value, €33.90, is a ceiling |
| 5 | `branch` | `Branch` | our own branch and bound on Léa's hour, node by node: the first split shown as two smaller problems, the search tree (129 nodes, 116 LPs), the relaxed plan of each node on the map, one cut branch spelled out (ceiling €21.70 < floor €24.40), floor and ceiling closing on €24.40 |
| 6 | `solver` | `Solver` | the two accelerators, on Léa's hour: a cutting plane (six deliveries take more than 60 min and the last deadline is 20:59, so "no real course delivers more than five": the ceiling drops from €33.90 to €29.20 without a branch) and a heuristic (quick guesses, then "soonest first": a floor of €17.10). Then Gurobi's real log for the same problem (presolve, root relaxation, `H` lines, cutting planes, Incumbent / BestBd / Gap): one node. Then the 11th arrondissement (8 couriers, 32 orders, 1,248 binaries): the search replayed in real time, 3.4 s, 31,577 nodes |
| 7 | `city` | `City` (3D) | one model per arrondissement, all twenty proven optimal in 55 s; the couriers ride the plan from 20:00 to 21:00; 378 of 403 meals against 332 for the obvious rule; the hour lifts into threads of time |
| 8 | `outro` | `Outro` | house thank-you card |

The film is a stitch (`FILM=""` in `render.sh`): one class cannot be both a flat
and a 3D scene.

**The picture.** The motif is the map and the *course* on it: a gold line that
follows real streets. Colour is a language kept through the film: gold is a real
plan, and the best one so far (the floor); blue is the relaxed problem (fractional
rides, the ceiling); red is what was removed or cut; green is delivered, or
proven; mint is a time window.

## Narration

The film is paced for a voice: every beat lasts at least as long as its line takes
to say, and the picture changes when the narrator reaches the word it illustrates
(`cue("phrase")` in the code).

- **`VOICEOVER.md`** is the timed script: for each line its timecode, the room
  before the next line, its word count, and the caption on screen.
- **`voiceover.srt`** holds the same lines as subtitles: open it with the video to
  read along while recording.
- The pace is `MIP_WPS` words per second (default 2.3, about 138 words a minute),
  with a breath of 1.1 s after each line. For a slower voice, re-render with
  `MIP_WPS=2.0` and regenerate the script.

Captions are deliberately few (one short sentence per beat, on screen for the
whole beat). Nothing has to be read while it moves.

## What is real, and what is invented

**Real, from OpenStreetMap** (fetched once through the Overpass API by `osm.py`,
baked into `assets/paris.npz` by `city.py`):

- the map: every street of Paris and its near suburbs by class, the Seine and the
  canals, parks and woods, railways, the outlines of the 20 arrondissements, and
  the building footprints of the centre;
- ride times: shortest paths on that street network (`routing.py`), at 15 km/h
  (9 km/h in pedestrian streets). One-way streets are one-way for bikes too unless
  OpenStreetMap says cyclists may ride against the traffic. No traffic lights, no
  slopes: a simple, stated model of a bicycle;
- restaurants: the location and the `cuisine` tag of 14,298 real restaurants and
  fast-food places. An order's label (pizza, ramen, ...) is the cuisine of the real
  restaurant it leaves from. No business is named.

**Invented** (seeded, in `story.py`): which restaurants have an order tonight, the
customers' addresses (street nodes drawn at random around each restaurant), the
fees (€2.90 + €1.40 per km + an occasional bonus), when each meal is ready, the
deadline promised to each customer, where the couriers stand at 8 p.m. Two minutes
are counted at the counter and two at the door.

**Computed by real runs** (`generate_assets.py`, results in `assets/story.json`,
logs in `assets/gurobi_*.txt`), and asserted in the scenes:

- Léa's hour is solved four ways, which must agree on the same course and the same
  €24.40: Gurobi 14 running the model block of `demo/course.py` (the code the film
  shows, executed as is); HiGHS through SciPy on the same problem written as
  matrices; our own branch and bound; and brute force over all feasible courses.
- The search tree of scene 5 is our own plain branch and bound (`model.py`): our
  presolve, then one LP relaxation per node, solved with HiGHS's simplex through
  `scipy.optimize.linprog`. No cutting planes, no heuristics. Rule: branch on the
  most fractional ride; dive ("take it" first) until a first real plan, then always
  open the branch with the highest ceiling. 129 nodes, 116 LPs. One relaxation
  takes half a millisecond (0.52 ms, the median of 300 runs of the root's).
- The cutting plane of scene 6 is ours, chosen because it can be said in one
  sentence, and it is derived from the model's data, in the spirit of a cover cut:
  every delivery takes at least the quickest ride into it (among the 36 rides that
  survive presolve), the six quickest add up to 60.9 min, and nothing is due after
  minute 59.1. So "at most five orders" is a rule every real course obeys.
  Enumeration agrees: the longest feasible course has five orders, and the fastest
  possible sequence of six deliveries takes 62.8 min even with every window
  ignored. The root relaxation delivers six; with the rule its value is €29.20
  (HiGHS). The heuristic floor of €17.10 is the "soonest first" greedy rule.
  Gurobi's own cuts and heuristics are not shown: its log only counts the cuts by
  family and marks heuristic finds `H`.
- The log of scene 6 is Gurobi's, verbatim (an excerpt; `…` marks skipped lines,
  one long line is wrapped). For the district, the log and the runtime quoted
  (3.44 s, 31,577 nodes) come from a plain run, the same call as
  `demo/course.py district`; the incumbents and bounds drawn on the chart were
  recorded with a callback during an identical run (same nodes, same plans,
  3.40 s).
- **You can run it again.** `story.json` holds the two instances of
  `demo/course.py` at full precision (ride times and windows are not rounded: on
  rounded data a solver takes another path, 93 nodes instead of 129 for our own
  branch and bound). With the same Gurobi version on the same machine,
  `python demo/course.py` prints the log the film shows, and
  `python demo/course.py district` explores the same 31,577 nodes; timings vary
  by a few percent from run to run. Clock times on screen are floored to the
  minute (20:17:31 reads 20:17).
- The city is twenty separate models, one per arrondissement, each solved to proven
  optimality (55.2 s of solver time in all, on an Apple M4 Max, 14 threads). A
  courier only serves the orders of its own arrondissement: the plan is the best
  one *under that split*, and the film says so ("district by district"). The split
  is a modelling choice with a practical reason: the licence bundled with
  `gurobipy` caps a model at 2,000 variables, and the largest zone here has 1,288.
  The comparison is with a greedy rule applied to the same data: among the
  (courier, order) pairs that still fit, take the order that can be delivered
  soonest.

What the film does not claim: that a delivery platform works this way. Real
dispatch is online (orders keep arriving), and couriers accept or decline offers.
The film's problem is a static snapshot: one hour, known in advance. It is an
orienteering problem with time windows, which is a fair picture of why such
problems are mixed-integer programs.

Nor that branch and bound beats enumeration on eight orders. "Trying every
sequence" in scene 2 is blind: it counts all 109,600 ordered selections, of which
only 102 fit the hour, and an enumeration that gave up on a sequence as soon as it
breaks a window would look at far fewer. The count is there because it explodes
(twenty orders: 6.6 billion billion). The film compares scales where it matters, on
the district: 31,577 nodes for a problem with 9^32, about 3.4 × 10^30, ways to hand
out its orders.

## The model (`demo/course.py`)

```
x[i, j] = 1 if a courier rides from stop i straight to order j      (binary)
t[j]    = the minute order j is delivered                           (continuous)

maximise   sum of pay[j] * x[i, j]
subject to each courier leaves at most once
           each order is delivered at most once
           an order is left only if it was reached
           x[i, j] = 1  =>  t[j] >= t[i] + mins[i, j]
           early[j] <= t[j] <= late[j]
```

`mins[i, j]` is the time between the delivery of `i` and the delivery of `j`: ride
to `j`'s restaurant, pick up, ride to the customer, hand over. The time rule also
makes loops impossible, so no sub-tour constraints are needed. The same block
solves one courier or a whole district: only the data changes.

```bash
python demo/course.py            # Léa's hour: 24.40 EUR, proven optimal
python demo/course.py district   # the 11th arrondissement: 166.80 EUR
```

## Render

```bash
./render.sh hour --quick --check      # one scene: layout pass, edge scan, contact sheet
./render.sh                           # whole film, 480p (stitched)
MX_TRACE_DIR=/private/tmp/mip-media/trace ./render.sh --stitch -q h --no-cache
python ../../tools/voiceover.py . -q h --title "Mixed-Integer Programming"
```

If `./render.sh` is not executable in your checkout (this repository does not
track file modes), call it as `bash render.sh ...`.

Media goes to `/private/tmp/mip-media` (override with `MIP_MEDIA_DIR`); the final
film is copied here as `MIP_1080p60.mp4` (git-ignored). Use `--no-cache` after
changing `kit.py` or `stage.py`: Manim's partial-movie cache does not see changes
inside painters and updaters. `MIP_QUICK=1` (or `--quick`) collapses the holds.

Rendering needs only the shared venv and the committed assets. The map is drawn
on the GPU through an offscreen OpenGL context (`moderngl`, a dependency of Manim);
map textures are rasterised on first use and cached in `~/.cache/manimx/mip-textures`.
With a map that fills the frame, `--check` counts only bright pixels as content
near the edges (`MX_EDGE_THRESH=150`, set in `render.sh`).

## Re-baking the assets

```bash
python osm.py                                 # fetch OpenStreetMap once (cached, ~125 MB of JSON)
pip install -r requirements-bake.txt          # gurobipy (the bundled size-limited licence is enough)
python generate_assets.py                     # about 75 s: paris.npz, story.json, gurobi_*.txt
python generate_assets.py scan 0 80           # how other seeds for Léa's hour would look
python generate_assets.py patch-cut           # redo only the cutting-plane demo (no Gurobi run)
python generate_assets.py patch-lp            # redo only the timing of one relaxation
python generate_assets.py patch-data          # redo the two runnable instances and the district's log
MIP_BAKE_DIR=/tmp/mip-bake python generate_assets.py   # a dry run: bake somewhere else, then compare
```

A dry run of the whole bake was compared with the committed assets: every value of
`story.json` is identical except the 152 timings (runtimes, and the clock of each
incumbent and bound), and both logs are identical apart from dates and timings.

Gurobi's times and node counts depend on the machine and the version; the scenes
assert the numbers they state, so a re-bake on another machine will point at the
narration lines to update.

## Files

- `mip.py`: storyboard, the seven scenes, the narration.
- `kit.py`: the film's building blocks (stops and labels on a map, courses, the 64
  rides as dimmable arcs, the order table, the bound bar, the search tree, the log
  panel, the bound chart).
- `stage.py`: the 3D side: `MapPlane` (the map as a GPU-textured ground under
  Manim's camera, with mip levels drawn per scale), and the painters for the swarm.
- `city.py`: the baked geometry and the Cairo map renderer.
- `osm.py`, `routing.py`, `story.py`, `model.py`, `generate_assets.py`: bake time
  only (fetch, street graph and ride times, the cast, the four solvers, the bake).
- `demo/course.py`: the model, runnable.
- `assets/`: `paris.npz` (geometry), `story.json` (everything the scenes show),
  `gurobi_course.txt`, `gurobi_district.txt` (Gurobi's logs; `.txt` because the
  repo ignores `*.log`; the line that printed the local log path is removed).

## Sources and licences

- Map data © OpenStreetMap contributors, Open Database Licence (ODbL),
  <https://www.openstreetmap.org/copyright>. Fetched from the Overpass instance of
  OpenStreetMap France.
- Gurobi Optimizer 14.0 (`gurobipy` from PyPI, with the size-limited licence
  bundled in the package: non-production use). How to read its log: Gurobi
  documentation, "MIP Logging",
  <https://docs.gurobi.com/projects/optimizer/en/current/concepts/logging/mip.html>.
- HiGHS, through `scipy.optimize` (`milp`, `linprog`).
- "About 10^80 atoms in the observable universe" is the usual order-of-magnitude
  estimate. The film's 10^325 counts, for every arrondissement, the ways to give
  each order to one of its couriers or to nobody.
- This film is not affiliated with Gurobi, OpenStreetMap or any delivery platform.

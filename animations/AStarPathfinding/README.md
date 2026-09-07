# A\* Pathfinding — Manhattan street map

A short (~1m20s) Manim explainer of the **A\*** search algorithm finding the
shortest route across Manhattan, and *why* it explores the way it does: it always
expands the node with the smallest

```
f(n) = g(n) + h(n)
```

where `g(n)` is the real distance travelled so far and `h(n)` is a straight-line
(admissible) guess of what remains.

## The film

Four scenes, bookended by the channel intro/outro cards:

1. **MapIntro** — the Manhattan street network fades in; Start (Midtown) and Goal
   (Wall Street) flash.
2. **Search** — A\* explores: frontier nodes glow yellow, settled nodes turn blue,
   a live panel counts nodes / frontier / current `f(n)`, and the optimal route
   lights up green when the goal is reached.
3. **Explain** — the map dims and `g(n)`, `h(n)` and `f(n) = g(n) + h(n)` are
   labelled on an *off-path* node, so the winding real route (`g`) contrasts with
   the straight-line guess (`h`).
4. **FinalPath** — a car drives the found route from Start to Goal.

## The map (no GIS stack required)

The street network is **generated procedurally** — an authentic Manhattan grid
(rotated ~29° off true north, with **Broadway** cutting across as a diagonal
shortcut). This needs no `osmnx`/`geopandas` and no network access, and the clean
grid lets you actually *see* A\* expand.

Edge weights and the heuristic both use straight-line (Euclidean) distance in
screen space, so `h` never overestimates → A\* stays **optimal** even with
Broadway's diagonal. The start/goal were chosen so the goal sits off Broadway's
line: A\* fans out (≈37 nodes), rides Broadway as the shortcut, then cuts to Wall
Street. A single scale maps screen units to a plausible number of miles
(Times Sq → Wall St ≈ 4.5 mi straight-line).

Everything uses `Text` (Pango), not `Tex`, so no LaTeX toolchain is needed.

## Two versions

* **Flat / top-down** (`astar_pathfinding.py`) — the clean 2D map above.
* **3D perspective city** (`astar_city.py`) — a "not top-down", realistic take:
  a **dense** (12×22, ~260-node) irregular low-rise city — extruded, shaded
  buildings, a **central Central Park the routes must detour around**, scattered
  empty lots — viewed at a cinematic angle with an establishing camera tilt. It
  runs **several A→B examples** in sequence: the first in detail (with the
  f = g + h teaching + explainer), then quick follow-ups (across Central Park, a
  short crosstown hop, the length of the island), and finally a car drives the
  first route. Everything the viewer reads (title, per-example caption, panel,
  explainer boxes) is a fixed-in-frame HUD. Render it by adding `--city`:

  ```bash
  ./render.sh --city                 # the whole 3D film, 480p (~1m30s)
  ./render.sh examples --city --quick  # just the extra A→B examples
  ./render.sh search --city --quick    # the detailed first example
  ```

  The A→B pairs live in the `EXAMPLES` list at the top of `astar_city.py`.
  Quick static look-test of the city: `manim -s astar_city.py CityStill`.

## Rendering

```bash
./render.sh                 # the whole (2D) film, 480p (fast)
./render.sh --city          # the whole 3D-city film, 480p
./render.sh search --quick  # fast sanity check of one scene
./render.sh full -q h       # final 1080p render (add --city for 3D)
./render.sh --stitch -q m   # render each scene and concatenate (720p)
```

Scenes: `intro | map | search | explain | examples | final | outro` (or `full`).
(`examples` is only in the 3D `--city` version.)
`render.sh` reuses an existing Manim venv from the repo (HarnessEngineering /
CNN / Fourier); only if none is found does it bootstrap a local `.venv`.

### Pacing

`DELAY` (in `astar_pathfinding.py`) is the single pacing knob — every on-screen
hold scales with it. It's tuned to ~1m20s; raise it (e.g. `2.4`) for a ~2-minute
cut. `--quick` (`ASTAR_QUICK=1`) collapses the holds for fast iteration.

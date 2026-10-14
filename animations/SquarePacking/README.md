# The 17 Squares Problem

A house-style Manim explainer about the meme: *"this is the optimal packing of
17 squares. you have to live with this now."*

What it teaches:

1. **Problem** — 16 unit squares fill a 4x4 box perfectly; in a grid the 17th
   forces side 5 and leaves a third of the box empty.
2. **Record** — John Bidwell's 1998 packing, drawn from the exact published
   coordinates: side **4.675530...**, ten upright squares, six at **+39.80°**,
   one at **−36.62°** (notably, none at 45°). Verified by a separating-axis
   check at import time.
3. **Gap** — the meme's word "optimal" is wrong: the proven lower bound is only
   4.4452 (T. Green), so the true answer lives somewhere in an open gap.
   s(17) has been open since 1998.
4. **WhyTilt** — the proven 5-square case (Göbel's packing, side 2 + 1/√2):
   why a tilted square beats the grid at all.
5. **Search** — the methodology that finds such packings: simulated annealing
   on the *maximal inflation* score (Gensane & Ryckelynck 2005).
6. **Evolution** — a replay of **our own search run** (19.5M proposals, ~10
   minutes of laptop time): the grid melts, tilted clusters self-assemble, and
   the box shrinks from 5.0 to **4.7269** (record: 4.6755). Every frame is a
   real recorded state from `assets/packing_run.npz`.
7. **Status** — the scoreboard of which n are actually proven optimal, plus
   sources.

## Real data

- Record packing coordinates: David Ellsworth's exact-solution data
  (kingbird.myphotos.cc/packing/square-17.svg), catalogued from Bidwell's 1998
  packing; verified at import by SAT (tolerance 1e-6, coordinate rounding).
- Our search run: `generate_assets.py` — simulated annealing + exact hill-climb
  polish on the maximal-inflation objective, in the spirit of Gensane &
  Ryckelynck (2005). `SP_BUDGET=600 python generate_assets.py` reproduces it
  (seeded, default seed 7). The best configuration is strictly re-verified at
  save time and again at Manim import time.

## Sources

- E. Friedman, *Packing Unit Squares in Squares: A Survey and New Results*,
  Electronic Journal of Combinatorics, Dynamic Survey DS7 (v5, 2009).
- J. Bidwell 1998 (unpublished; catalogued in Friedman's survey). Exact
  algebraic value of s(17): D. Ellsworth, 2023.
- T. Gensane, P. Ryckelynck, *Improved Dense Packings of Congruent Squares in
  a Square*, Discrete & Computational Geometry 34, 97–109 (2005).
- P. Erdős, R. L. Graham, *On Packing Squares with Equal Squares*, J. Combin.
  Theory Ser. A 19, 119–123 (1975).
- W. Stromquist, *Packing 10 or 11 Unit Squares in a Square*, Electron. J.
  Combin. 10 (2003), #R8.

## Render

```bash
./render.sh                   # whole film, 480p
./render.sh evolution --quick # fast layout check of one scene
./render.sh --stitch -q h     # final 1080p60, scene by scene, stitched
```

Scenes: `intro problem record gap whytilt search evolution status outro`.

Measured runtime (1080p60 stitch): **4:22** (262.4 s), `media/SeventeenSquares_1080p60.mp4`.
For HD renders set `SQ_MEDIA_DIR=/private/tmp/sq17-media` (OneDrive-synced media
dirs stall long renders); the stitched film is then copied back into `media/`.

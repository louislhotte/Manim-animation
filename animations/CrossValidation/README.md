# Cross-Validation

A fast, dynamic **~1-minute** house-style demo of *why a single train/test split
lies to you* and how **k-fold cross-validation** fixes it. Scatter plots, wiggly
curves, sweeping fold blocks and small bar charts — no equations, so it renders
without LaTeX. The data and both model fits are pure NumPy.

## The film (`CrossValidation`)

Bookended by the channel's intro card and the "Thank you for watching!" outro,
three snappy scenes:

1. **Overfitting** — a degree-8 polynomial *threads every training point*
   (training error ≈ 0.00) but wiggles wildly and misses the unseen **test**
   points (test error **1.93 ✗**), while a simple degree-3 model follows the
   trend and stays consistent (test error **0.56 ✓**). *Perfect on training,
   lost on new data — that's overfitting.*
2. **K-Fold Cross-Validation** — split the data into **K = 5** folds and rotate
   which one is held out for validation, so **every point is validated exactly
   once**. Each round gives a score; the five average into a trustworthy
   **CV score = 0.72 ± 0.02**.
3. **Why it wins** — one split gives a jumpy number (**± 0.15**, "could be
   0.56 … 0.86"); 5-fold CV gives a tight, steady one (**± 0.02**) — plus the
   benefits. *Cross-validation turns a lucky score into a trustworthy one.*

The numbers on screen are computed from the fitted models (`OF_TEST`, `GD_TEST`,
`CV_MEAN ± CV_STD`); the per-fold scores and the two reliability bars are marked
*illustrative*.

## Rendering

```bash
./render.sh overfit --quick   # fast sanity check of one scene
./render.sh                   # the whole ~1-min film, 480p
./render.sh full -q m         # final 720p30
./render.sh full -q h         # 1080p60
./render.sh --stitch -q m     # render each scene and join into one 720p film
```

`render.sh` reuses the HarnessEngineering / Fourier / CNN series' `.venv` if it
finds one (so Manim isn't reinstalled), otherwise it bootstraps a local `.venv`
from `requirements.txt`.

Individually renderable scenes: `intro` · `overfit` · `kfold` · `payoff` ·
`outro` (or `full`, the default).

`CV_QUICK=1` (or `--quick`) shortens the on-screen holds while iterating. Pacing
is a single knob — module-level `DELAY` at the top of `cross_validation.py`
(1.5 ≈ the ~62 s cut; every reading hold scales with it, animation run-times do
not); the palette and the data seed live there too.

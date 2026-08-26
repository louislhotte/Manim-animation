# Parameter Evolution During Training

A dynamic **~3-minute** explainer on what actually *changes* inside a model while
it learns — its **parameters** — watched one gradient step at a time. First on a
model with **two** knobs (linear regression), then on one with **many** (a neural
network), each kept honest with **cross-validation**.

Rendered with [Manim](https://www.manim.community/). Everything uses `Text`
(Pango), never `Tex`, so **no LaTeX toolchain is required**.

## The story

**Part 1 — Linear regression (2 parameters)**

1. **Setup** — 200 noisy points; the model `ŷ = w·x + b` has two knobs (`w`, `b`),
   starting from a deliberately bad random guess.
2. **Gradient Descent** — the money scene: a live readout of `step / w / b / loss`
   drives, in lock-step, the line swinging into place (left) and the point `(w, b)`
   sliding down the **exact quadratic loss bowl** (right) to the minimum.
3. **Cross-Validation** — refit on 5 folds; the five learned lines land almost on
   top of each other and the parameters barely move → a stable, trustworthy fit.

**Part 2 — Neural network (121 parameters)**

4. **Many Knobs** — a schematic `1 → 40 → 1` net: every edge is a weight;
   **121 parameters** vs **2** — a landscape we can no longer draw.
5. **Training the Net** — the fitted curve morphs through real training snapshots:
   flat guess → the true shape → **chasing the noise (overfitting)**, while a
   corner net shows the weights still jittering and settling.
6. **Cross-Validation** — train vs. validation loss over epochs (log scale):
   training loss keeps falling but **validation turns back up**. CV marks the
   sweet spot → **early stopping**.

## Everything on screen is real

Computed in NumPy at import time — no faked numbers:

- the **gradient-descent trajectory** `(w, b, loss)` (full-batch GD, 60 steps);
- the **loss-surface contours** — the *exact* quadratic bowl of linear-regression MSE;
- the **5-fold CV** scores and per-fold fits;
- the **neural network** — real forward/back-prop (`tanh`, MSE), its fitted-curve
  snapshots and its averaged 5-fold learning curves (including the val-loss minimum).

## Render

```bash
./render.sh                    # whole film, 480p (fast)
./render.sh descent --quick    # one scene, holds collapsed — quick sanity check
./render.sh full -q h          # final 1080p60 render
./render.sh --stitch -q m      # render each scene and stitch (720p)
```

`render.sh` bootstraps a local `.venv` on first run, or reuses the
HarnessEngineering / Fourier / CNN venv if one already exists.

Scenes render individually too: `intro · setup · descent · cvlinear · manyknobs ·
trainnet · cvnet · outro`.

## Knobs

- **`PE_QUICK=1`** (or `--quick`) — collapse every reading hold *and* the fixed
  5-second end-of-scene holds, for fast iteration.
- Pacing lives in one constant, `DELAY`, at the top of `parameter_evolution.py`;
  every scene ends on a `self.settle()` hold of at least 5 seconds.

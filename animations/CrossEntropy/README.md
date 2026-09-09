# Cross-Entropy

A short, no-voice-over explainer on the cross-entropy loss: **what it is**, and
**why it is the right way to score a probabilistic prediction**. Built in the
house dark style, bookended by the channel intro / outro cards, and set entirely
in `Text` (Pango) so it renders with no LaTeX toolchain.

**Camera policy:** the formula / number / curve scenes use a **static camera** —
zooming into flat content adds nothing. Camera movement is reserved for the one
genuine 3D scene (`Descent`), where the camera orbits a real loss surface so you
see its shape from every side.

## What it teaches

One concrete 3-class example (cat / dog / bird) drives every number on screen:

1. **A prediction is a distribution.** A classifier outputs a probability for
   every class (cat 0.70, dog 0.20, bird 0.10), and the truth is one class. How
   wrong is that?
2. **The formula.** `H(p, q) = − Σ p(x) log q(x)`. With a one-hot label the sum
   collapses to `L = − log q(true)` — the negative log-likelihood of the correct
   class. Here `−log 0.70 = 0.36`.
3. **Why the log.** Plot `L = −ln q`. Confident-and-right → ≈ 0; confident-and-wrong
   → ∞. Cross-entropy is your average *surprise* at the truth, and it punishes
   confident mistakes the hardest.
4. **Why training loves it.** Softmax + cross-entropy give a strikingly simple
   gradient: `∂L/∂z = q − p` (prediction minus target). It never saturates, so
   learning stays fast where squared error would stall.
5. **Descending the loss (3D).** The cross-entropy loss over a model's two
   parameters is a single **convex bowl**. A ball runs real gradient descent
   straight to the global minimum while the camera orbits the surface. This is the
   one scene where camera control earns its keep.
6. **Why it is honest.** `H(p, q) = H(p) + KL(p ‖ q)`. `H(p)` is fixed by the
   data, so minimising cross-entropy = minimising `KL(p ‖ q)`, which is 0 only
   when `q = p`. It is a proper scoring rule: you cannot win by hedging.
7. **Recap.** One card: the formula and the five reasons it is the standard loss
   for every classifier.

Every value is computed once, from a single source of truth:

- The classifier numbers come from `LOGITS = [1.9459, 0.6931, 0.0]`: the softmax
  is exactly `[0.70, 0.20, 0.10]`, the loss is `−ln 0.70 = 0.36`, and the gradient
  is `q − p = [−0.30, 0.20, 0.10]` (an `assert` block keeps the display honest).
- The 3D bowl is a **real** logistic-regression cross-entropy surface (`ce_loss`)
  over two parameters `(w, b)`, on deliberately non-separable data so it has a
  finite, interior, convex minimum. `CE_PATH` is a real gradient-descent run on
  that surface, and `CE_MIN` is its global minimum (found by a grid scan).

## Scenes

`Intro · Setup · Formula · Surprise · Gradient · Descent (3D) · Honest · Recap · Outro`

Each renders on its own. The film mixes 2D (`Scene`) and 3D (`ThreeDScene`)
classes, so the whole film is produced by rendering every section and stitching
them (`./render.sh full` does this automatically).

## Render

```bash
./render.sh descent --quick -q l   # fast check of the 3D scene (480p15)
./render.sh full                   # whole film, 480p (renders + stitches)
./render.sh full -q h              # final 1080p60 (slow; run in background)
```

Quality: `-q l|m|h|k` = 480p15 / 720p30 / 1080p60 / 2160p60. `--quick`
(`XCE_QUICK=1`) collapses the reading holds; `XCE_DELAY=x` overrides the
reading-hold multiplier. For long HD renders, set `XCE_MEDIA_DIR=/private/tmp/…`
to render to a local dir and avoid OneDrive I/O stalls, then copy the stitched
mp4 back. `render.sh` reuses an existing Manim venv (HarnessEngineering / Fourier
/ CNN) if present, else bootstraps a local `.venv`.

## Measured runtime

Full film at 1080p60: **3:24** (204.8 s, 1920×1080), stitched from the 9 scenes.

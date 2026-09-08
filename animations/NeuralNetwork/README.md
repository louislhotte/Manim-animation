# How a Neural Network Learns

A ~10-minute, no-voiceover, house-style Manim explainer on **supervised image
classification, end to end** — teaching a neural network to tell a **car** from a
**plane** from a **ship**, from raw pixels, from a random-weight beginning to a
real accuracy number.

Everything on screen is **real**: the images, the trained models, the loss and
accuracy curves, the hyper-parameter sweep, the confusion matrix and the final
accuracies are all computed by `generate_assets.py` (numpy + PIL, deterministic)
and baked into `assets/nn_learn.npz` (+ the correctness-grid PNGs). No LaTeX —
all text is Manim `Text` (Pango).

## What it teaches

Five ~2-minute scenes, bookended by the channel's intro/outro cards:

1. **The Task** — you can't *write* the rules for "car", so we learn from
   **labelled examples**. The three classes, the mapping `f(image) → label`, and
   the punchline that to a computer an image is just 784 numbers.
2. **The Network** — flatten the 28×28 image to 784 inputs, build the
   feed-forward net (784 → 8 → 3), what one neuron computes (`z = w·x + b`,
   `a = ReLU(z)`), count the 6,307 parameters, and a forward pass with *random*
   weights that confidently guesses "plane" for a car.
3. **Training** — one step in slow motion: forward pass → **loss** →
   **backpropagation** → **weight update**, watching the same car flip from
   the wrong label to "car"; then scaled up with the real loss/accuracy curves.
4. **Tuning** — training sets the *weights*; **we** choose the *size*. A real
   sweep over the number of hidden neurons, validation accuracy vs. capacity
   (underfit → plateau → overfit), and picking three sizes to compare.
5. **The Verdict** — Tiny / Medium / Large head-to-head on nine images, then a
   **dezoom to all 2,400 test images** shown as a wall of the real pictures,
   tinted green where the net is right and red where it's wrong, plus the real
   global accuracy and the confusion matrix.

## The real task & models

- **Data:** procedural 28×28 grayscale images of cars / planes / ships with
  per-sample rotation, translation, scale, brightness and light noise — the
  shapes stay recognisable, but the pose variation makes it non-linear, so a
  linear/tiny model can't win and capacity earns its keep.
  1,500 train · 450 validation · 2,400 test.
- **Models:** one-hidden-layer MLPs (He-init ReLU, softmax + cross-entropy, Adam),
  width = the single tuned knob:

  | Size   | Hidden width | Parameters | Test accuracy |
  |--------|-------------:|-----------:|--------------:|
  | Tiny   |            2 |      1,579 |     **63.3%** |
  | Medium |            8 |      6,307 |     **83.5%** |
  | Large  |           64 |     50,435 |     **90.9%** |

  (Chance = 33%.) The hyper-parameter sweep and these three points are the same
  trained models, so Scene 4's curve and Scene 5's contenders are consistent.

## Render

```bash
./render.sh                 # whole film, 480p (default); bootstraps/reuses a venv
                            # and generates assets/nn_learn.npz on first run
./render.sh train --quick   # fast layout check of one scene (480p15)
./render.sh full -q h       # final HD (1080p60) — slow; run in background
./render.sh --stitch -q m   # render each scene and ffmpeg-concat into one file
```

Scenes: `task · arch · train · tune · verdict` (or `full`). Quality
`-q l|m|h|k` = 480p15 / 720p30 / 1080p60 / 2160p60. Iterate at `l --quick`.

Pacing knobs: `NN_QUICK=1` collapses holds; `NN_DELAY` (reading rhythm) and
`NN_READ` (caption hold, seconds) fine-tune the cadence.

## Files

- `generate_assets.py` — builds the dataset, trains the three MLPs + the width
  sweep, and bakes every on-screen number into `assets/`.
- `nn_common.py` — shared palette, crisp-`Text` shim, class glyphs, the network
  builder + signal-flow animations, and the `NNBase` scene base (timing,
  `section_header`, running `say` caption, intro/outro cards).
- `scene1_task.py … scene5_verdict.py` — one scene each (`build_<name>(scene)` +
  a thin renderable `Scene` subclass).
- `neural_network.py` — the full film (`NeuralNetworkLearns`).

## Measured runtime

**9:40** (580 s) for the whole film at the default cadence, rendered at 1080p60
(`ffprobe` on the master; duration is resolution-independent). Roughly two minutes
per scene, intro & outro cards included. `NN_QUICK=1` collapses it to ~55 s for
fast layout iteration. Verified with `edgecheck.py` (clean across 64 frames
spanning the full runtime) and by eyeballing every beat.

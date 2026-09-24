# Backpropagation

A short, no-voice-over, house-style explainer on **the power of
backpropagation**, told through a real 3D loss landscape.

The idea: the loss over a network's weights is a *landscape*. Learning means
walking downhill into a valley. The direction of "downhill" is the gradient, and
**backpropagation is the algorithm that computes that gradient for every weight
at once** — the chain rule, run backward through the network, in a single pass.
That one backward pass is what makes training networks with billions of weights
possible.

## What it teaches

- The loss is a function of the weights, so it forms a surface (a *landscape*).
- Gradient descent rolls downhill; the steepest way down is the negative gradient.
- Backpropagation computes that gradient by sending the error backward through
  the network, multiplying the local derivative at each step (the chain rule).
- One forward pass gives the loss; one backward pass gives every weight's
  gradient. The slow alternative (nudge each weight and re-run) costs one pass
  per weight, so backprop is about a millionfold less work.

## Scenes

1. **Intro** — title card.
2. **Setup** (2D) — a prediction depends on the weights; a wrong prediction is a
   high loss. With two weights, every setting is a point and the loss is a height.
3. **Landscape** (3D) — the loss surface. The camera rises from a top-down map
   into a tilted terrain: two low valleys and a ridge. Height is the loss.
4. **Descent** (3D) — gradient descent, made active and step-by-step: the ball
   drops onto the surface (its height is the loss: the forward pass), a bold arrow
   shows the gradient (the backward pass), the ball steps along it and a live loss
   readout drops. Repeat, then roll to the bottom; a second ball rolls into the
   other valley. Then the hook: which way is downhill, for millions of weights?
5. **Backward** (2D) — backpropagation: forward pass for the loss, backward pass
   for the gradient, multiplying the local derivative at each step. Real numbers.
6. **Power** (2D) — one backward pass versus one pass per weight; the payoff.
7. **Recap** — one card.
8. **Outro** — thank-you card.

Only the two 3D scenes move the camera (house rule: camera control is reserved
for genuine 3D geometry). The 2D scenes are static; their motion comes from the
mobjects.

## Real numbers

Everything on screen is computed, never fabricated. `generate_assets.py` bakes
`assets/backprop.npz`:

- the loss surface of the model `f(x) = w2 · tanh(w1 · x)` fitted (MSE) to data
  from a true tanh — nonlinear in its parameters, so the loss genuinely curves
  into valleys (two mirror valleys, from the model's sign symmetry);
- two real gradient-descent (momentum) trajectories rolling into the two valleys;
- the exact forward values **and** backward gradients of a tiny
  `x → linear → tanh → linear → loss` network (the chain-rule scene);
- the forward-pass-count comparison for the "why it is powerful" scene.

Re-bake (and eyeball the surface) with:

```bash
python generate_assets.py --preview   # writes assets/preview_*.png
```

`render.sh` bakes `assets/backprop.npz` automatically if it is missing.

## Render

```bash
./render.sh landscape --quick -q l   # fast layout check of one scene (480p15)
./render.sh                          # whole film, 480p, stitched
./render.sh full -q h                # final 1080p60 (slow; the 3D scenes dominate)
./render.sh --stitch -q m            # render each scene and stitch (720p30)
```

Scenes: `intro setup landscape descent backward power recap outro` (or `full`).
The film mixes 2D `Scene` and 3D `ThreeDScene` classes, so `full` always renders
each scene and stitches them.

Env knobs: `BP_QUICK=1` collapses the reading holds; `BP_DELAY=x` overrides the
reading-hold multiplier; `BP_MEDIA_DIR=...` overrides the media directory
(defaults to `/private/tmp/bp-media` to dodge OneDrive I/O stalls).

## Runtime

Measured runtime: **4:16** (256 s, stitched 1080p60, `ffprobe`). Per-scene: Intro
8s, Setup 33s, Landscape 38s, Descent 68s (the active gradient-descent
centerpiece), Backward 40s, Power 35s, Recap 25s, Outro 9s. Timing is
resolution-independent (holds are the same at every quality).

The two 3D scenes use hand-added per-face diffuse+specular shading (Manim's Cairo
renderer has no lighting of its own), so the loss surface reads as a lit 3D
object rather than a flat plot.

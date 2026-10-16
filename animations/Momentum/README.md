# Momentum

A short, no-voiceover, house-style explainer on **why momentum makes gradient
descent so much faster** on the long, narrow valleys that real loss surfaces
form. The payoff is a genuine 3D scene: two balls race down the same valley, one
plain gradient descent and one with momentum, while the camera orbits so you can
see the valley from every side.

## What it teaches

- Training is gradient descent: step downhill in the loss, repeat.
- Real loss surfaces often form **long, narrow valleys** (ill-conditioned:
  steep across, shallow along). Plain descent bounces between the steep walls and
  barely creeps toward the goal.
- **Momentum** keeps a *velocity*: `v ← β·v − α·∇L`, then `θ ← θ + v`. A heavy
  ball that remembers where it was already going.
- **Why it works:** across the walls the gradient flips every step, so the stored
  velocity cancels (the bounce is damped); along the floor every gradient points
  the same way, so the velocity compounds (it accelerates). The effective step
  along a consistent slope grows to `α / (1 − β)`.

## The numbers are real (one source of truth)

Everything on screen is computed by running the actual update rules on a real
ill-conditioned quadratic ravine `L(x, y) = ½(0.5·x² + 16·y²)` (condition number
κ = 32), with learning rate `α = 0.10`, momentum `β = 0.80`, from the same start
for 26 steps. `momentum.py` asserts the story at import:

- plain gradient descent never enters the basin (its closest approach is ~0.8
  from the minimum, still ~0.79 away after all 26 steps);
- momentum reaches the minimum (within ~0.07), first getting within 0.2 of the
  goal at **step 9** of 26 (roughly 3× sooner);
- the plain path genuinely zig-zags across the steep walls.

## Scenes

1. **Intro** — title card.
2. **Problem** — gradient-descent recap, then a top-down valley with the real GD
   path zig-zagging across the walls.
3. **Idea** — the momentum update rule beside plain GD; both real paths overlaid
   on the same valley.
4. **Valley (3D)** — the real valley surface; the two balls race to the goal
   while the camera orbits. The one scene with camera movement.
5. **Mechanism** — why momentum wins: gradients cancel across the walls, compound
   along the floor; effective step `α/(1−β)`.
6. **Recap** — one card: the update rule and what momentum buys you.
7. **Outro** — thank-you card.

Camera policy: 2D scenes use a **static camera** (house rule: camera control is
only for genuine 3D geometry); the orbit lives only in the `Valley` scene.

## Render

```bash
./render.sh idea --quick -q l      # fast layout check of one scene (480p15)
./render.sh valley --quick -q l    # check the 3D scene
./render.sh                        # whole film, 480p, stitched
./render.sh full -q h              # final 1080p60 (slow; run in background)
```

Quality: `-q l|m|h|k` = 480p15 / 720p30 / 1080p60 / 2160p60. `--quick`
(`MOM_QUICK=1`) collapses the reading holds for fast iteration; `MOM_DELAY`
overrides the reading-hold multiplier. Because the film mixes 2D `Scene` and 3D
`ThreeDScene` classes there is no single all-in-one class: `full` renders each
section and stitches them with ffmpeg. Renders write to `/private/tmp/mom-media`
by default (OneDrive-sync stall dodge); override with `MOM_MEDIA_DIR`.

## Runtime

Measured full-film runtime: **3:02** (182.7 s), stitched from the seven scenes.
Per scene: Intro 8s, Problem 29s, Idea 36s, Valley (3D) 44s, Mechanism 31s,
Recap 24s, Outro 9s. Rendered and verified at 480p15; delivered at 1080p60
(`-q h`). The layout is identical across qualities; only the render time changes.

# Model Quantization

A short, house-style explainer on **quantizing neural-network models** — why a huge
model can be squeezed down to run on small hardware. It is the repo's first real
**3D piece**: the model's weights are a field of glowing bars on a dark plane, and a
slow ambient camera orbit keeps the whole thing gently in motion (inspired by the
"3D field of numbers" look). Every word the viewer reads (title, captions, HUD) is a
fixed-in-frame overlay, so the text stays put and readable while the field turns
underneath.

No voiceover, no LaTeX (all `Text`/Pango). Dark house palette, house intro/outro.

## What it teaches

- A neural network is layers of neurons joined by weights. **The tall bar field is one
  layer's weight matrix** drawn as a landscape, one bar per weight, and a real model
  stacks hundreds of these layers. (This grounds the abstract field.)
- **Each weight is really a number.** At full precision it is an FP32 32-bit float; a
  7-billion-weight model is then ~28 GB.
- **Removing bits coarsens the number.** The film shows three weights whose digits
  *flicker* and snap from FP32 to INT8 to INT4, with the reconstruction error growing,
  so you can see precision (and a little accuracy) being traded away.
- **Quantization** snaps every weight to its nearest of a small set of allowed levels,
  and stores a small integer (which level) plus one shared **scale** per tensor.
- The number of levels is the **bit budget**: `b` bits give `2^b` levels. Shown as
  **FP32 / INT8 / INT4 side by side**: INT8 (256 levels) looks identical to FP32, INT4
  (16 levels) visibly steps, and both are far smaller.
- The **recipe** (scale + zero-point): `q = round(w / s) + z` to store, and
  `w ≈ s × (q − z)` to recover.
- The **payoff**: a 7B model goes 28 GB → 7 GB (INT8) → 3.5 GB (INT4), so it now fits
  on a laptop or a phone, and there are fewer bits to move, so inference is faster.

All the arithmetic on screen is computed, not fabricated (the scale/zero-point round
trip and the per-precision reconstruction errors come straight from the numbers).

## Scenes

The film runs end-to-end as `ModelQuantization`, and every section also renders alone:

1. **Intro** — title card.
2. **Network** — a neural network; one layer's connections light up, become a grid of
   numbers, then the camera tilts up into the 3D bar field (that field *is* one layer).
3. **Numbers** — three weights shown as decimals; their digits flicker and snap from
   FP32 to INT8 to INT4 while the error readout climbs.
4. **Snap** — quantize: choose a few levels, snap every weight, store an integer + scale.
5. **Compare** — FP32 / INT8 / INT4 as three fields side by side; INT8 looks identical,
   INT4 visibly steps.
6. **Mapping** — the scale + zero-point recipe on a number line, with the round trip.
7. **Payoff** — memory bars for a 7B model (FP32 / INT8 / INT4) and why it matters.
8. **Outro** — thanks + one-line recap, over the orbiting field.

## Rendering

```bash
./render.sh network --quick -q l  # fast layout check of one scene (480p15)
./render.sh full                  # whole film, 480p
./render.sh full -q h             # final 1080p60 (slow; the 3D + orbit shine at 60 fps)
./render.sh --stitch -q m         # render each scene and concat to one file (720p30)
```

Scenes: `full` (default) · `intro` · `network` · `numbers` · `snap` · `compare` ·
`mapping` · `payoff` · `outro` · `probe`. Quality: `-q l|m|h|k` =
480p15 / 720p30 / 1080p60 / 2160p60. `--quick` (`QZ_QUICK=1`) collapses the reading
holds for fast iteration; `QZ_DELAY=<s>` overrides the reading rhythm.

**Note on this OneDrive-synced repo:** `render.sh` writes Manim's media into a local
scratch dir (`/private/tmp/qz-media`) by default, because writing the many partial
movie files into the OneDrive-synced tree stalls for minutes on sync I/O. Set
`QZ_MEDIA_DIR="$PWD/media"` if you want the artifacts kept alongside the code.

## Runtime

Measured with `ffprobe`: **3:03** (183 s). Fixed animation time is roughly a third of
that; the rest is reading holds. Layout is identical at every quality — only the
resolution and frame rate change, so the duration is the same at `-q h`.

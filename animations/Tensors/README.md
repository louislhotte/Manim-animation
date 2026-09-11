# What is a Tensor?

A short, no-voiceover explainer that builds the idea of a tensor one axis at a
time: **scalar → vector → matrix → higher dimensions**, then shows how deep
learning is really just tensors flowing and changing shape.

The through-line is a **shape tuple** that grows as axes are added, plus a
`rank / axes` badge, so "rank counts the axes, shape sizes them" is felt, not
just stated. Same dark house palette as the Transformer / KV-cache series.

## What it teaches

- A tensor is an **N-dimensional array of numbers**. Rank = number of axes,
  shape = size along each axis.
- **Scalar** (rank 0, `()`): a single number: a loss, a price, a temperature.
- **Vector** (rank 1, `(d,)`): a list along one axis, and the same list drawn as
  an arrow: magnitude *and* direction (a word embedding is just a vector).
- **Matrix** (rank 2, `(r, c)`): rows and columns; two indices name a cell; an
  image *is* a matrix of pixel brightnesses (the 8×8 picture emerges from the
  numbers).
- **Higher dimensions**: an isometric cube (rank 3 needs three indices), a colour
  photo as three stacked R/G/B channels `(3, H, W)`, and a batch of images as a
  fourth axis `(N, 3, H, W)`.
- **Tensors are the data**: scalar → vector → matrix → rank-3/4/5, each mapped to
  a real deep-learning object (loss, embedding, image, RGB, batch, video).
- **Tensors are the computation**: a CNN forward pass where the shape changes at
  every layer, the matmul rule `(1, k) · (k, 10) = (1, 10)` ("inner dims must
  match"), and the last 10 numbers turned into probabilities.

Uses the PyTorch `NCHW` shape convention. No LaTeX (all `Text`/Pango); no external
assets (the images, cube and channels are all drawn from primitives).

## Scenes

| # | class        | what happens |
|---|--------------|--------------|
| — | `Hook`       | a number grows an axis at a time, the shape tuple ticking `()`→`(3,)`→`(3,3)`→`(3,3,3)` |
| — | `Intro`      | house title card |
| 1 | `Scalar`     | one number, `shape ()`, rank 0; loss / price / temperature |
| 2 | `Vector`     | a row of numbers along one axis, then drawn as an arrow in 2-D |
| 3 | `Matrix`     | a grid, two axes, indexing `M[1][2]`; an 8×8 image emerges from brightnesses |
| 4 | `Higher`     | isometric cube (3 indices) → RGB image as 3 channels → batch of images (rank 4) |
| 5 | `DataUse`    | scalar → rank-5 mapping table to real ML objects, with mini-glyphs |
| 6 | `Compute`    | a CNN forward pass, the shape at every layer, the matmul rule, softmax → prediction |
| — | `Recap`      | takeaway card: one idea, N dimensions |
| — | `Outro`      | thank-you card |

`WhatIsATensor` runs the whole film; `Probe` is a glyph sanity check.

## Render

```bash
./render.sh vector --quick -q l   # fast layout check of one scene (480p15)
./render.sh full                  # whole film, 480p
./render.sh full -q h             # final HD (1080p60), slow
./render.sh --stitch -q m         # render each scene and concat to one file
```

Env knobs: `TN_QUICK=1` collapses the reading holds; `TN_DELAY=<s>` overrides the
reading rhythm.

`render.sh` reuses an existing Manim venv elsewhere in the repo (the
HarnessEngineering / Fourier / CNN `.venv`, Manim 0.21.0) and only bootstraps a
local `.venv` if none is found.

## Measured runtime

**3:41** (221.5 s) at real cadence (non-`--quick`), full film, one-pass render.
`edgecheck.py` is clean on every scene and on the assembled film (no content
within 9 px of any edge).

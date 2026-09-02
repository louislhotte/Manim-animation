# Vision Transformers — a visual explainer

A no-voiceover, house-style Manim film on **how a Transformer, built for
sequences of words, is made to see an image**: cut the picture into fixed-size
patches, turn each patch into a token, and let self-attention do the rest.

Grounded in **"An Image Is Worth 16x16 Words: Transformers for Image Recognition
at Scale"** (Dosovitskiy et al., ICLR 2021, arXiv:2010.11929), with the attention
mechanism from "Attention Is All You Need" (Vaswani et al., 2017). It is a direct
companion to the `Transformer/` and `KVCache/` films and reuses their palette.

**Measured runtime: 3:02** (480p15, default cadence).

## What it teaches

The whole ViT forward path, end to end:

1. **Idea** — Transformers read sequences; an image is a grid of pixels, so treat
   it as a *sequence of patches*. ("An Image Is Worth 16x16 Words.")
2. **Patchify** *(the headline)* — cut the image into a 4x4 grid of patches, open
   the gaps, and flatten them in reading order into a single sequence.
3. **Embed** — flatten each patch (16·16·3 numbers), project it with a learned
   linear map to a D-dimensional vector, add a learned **position embedding**, and
   prepend a learnable **[CLS]** token.
4. **Encoder** — the Transformer encoder block: LayerNorm → Multi-Head
   Self-Attention → residual → LayerNorm → MLP → residual, repeated **× L**. No
   causal mask (bidirectional, unlike a text decoder).
5. **Attention** — self-attention is **global from the first layer**: a CNN sees a
   small local neighborhood, a ViT attends to every patch at once. The trade-off:
   fewer built-in priors, so ViTs need lots of data (and then scale beautifully).
6. **Head** — take the [CLS] output → MLP head → softmax → a class.

Bookended by the channel's intro / outro cards.

The example image (a clean flat-design mountain landscape) is **generated from
numpy at import time** — there are no asset files and nothing to download. The
patches shown are real crops of that image.

## Render

```bash
./render.sh patchify --quick -q l   # fast layout check of one scene (480p15)
./render.sh                         # the whole film, 480p (default)
./render.sh full -q h               # final 1080p60 (slow; run in background)
./render.sh --stitch -q m           # render each scene and concat (720p30)
```

Scenes: `intro | idea | patchify | embed | encoder | attention | head | outro`,
plus `full` (the whole film).

`render.sh` reuses an existing Manim venv elsewhere in the repo (HarnessEngineering
/ Fourier / CNN) if present, so Manim is not reinstalled; otherwise it bootstraps a
local `.venv` from `requirements.txt` (`manim` + `numpy`, no LaTeX).

### Env knobs

- `VIT_QUICK=1` — collapse every on-screen hold for a fast sanity render.
- `VIT_DELAY=<float>` — override the reading-hold multiplier (tunes total runtime).

## Notes

- Everything is `Text` (Pango), no `Tex`/LaTeX. `Text` is shadowed at the top of
  the module so every glyph renders at a large base size and scales down (Pango
  mangles spacing below ~20 pt); subscripts (e.g. `Wₚ`) are built from `mtext`
  pieces so they stay in the body font.
- Verified with the repo's `edgecheck.py` (no content within 9 px of any edge) and
  by eyeballing key frames of every scene.

# The KV Cache — a ~3-minute explainer

Why autoregressive LLMs don't re-read their own words. A no-voiceover, house-style
Manim film on the **key/value cache**: the optimization that makes generating the
1000th token almost as cheap as the first.

It picks up where the [Transformer Inference](../Transformer) film left off (same
palette, same Q/K/V colour language) and goes deep on the one idea that film only
touched: caching Keys and Values.

## What it teaches

1. **The waste** — generation is a loop, and the naïve loop rebuilds the Keys and
   Values of *every* previous token at every step (the red "triangle of waste",
   work ∝ n²).
2. **Reuse** — a token's Key and Value depend only on that token, so they never
   change as the sequence grows. Compute them once.
3. **The KV cache** — store past K and V; each new step computes q, k, v for the
   *new* token only, appends one column, and its query sweeps the whole cache.
   O(n²) recompute → O(n) append.
4. **Two phases** — *prefill* (whole prompt in one parallel pass, compute-bound)
   then *decode* (one token at a time, memory-bandwidth-bound: each step streams
   the entire cache).
5. **The price** — cache size = `2 × layers × heads × d_head × tokens × bytes`.
   For Llama-2-7B that's ≈ 0.5 MB/token; it grows linearly and, past ~28K tokens
   (single sequence), can outweigh the model's own weights.
6. **Shrinking it** — Multi-Head → Grouped-Query → Multi-Query attention share
   K/V across query heads (cache ÷ 4, ÷ 8); a nod to PagedAttention (vLLM).

Grounded in *Attention Is All You Need* (Vaswani et al., 2017), Multi-Query
Attention (Shazeer, 2019), GQA (Ainslie et al., 2023) and PagedAttention
(Kwon et al., 2023).

## Scenes

`Intro · Waste · Reuse · Cache · Phases · Memory · Shrink · Recap · Outro`

Each renders alone; `KVCacheFilm` is the whole thing end-to-end.

## Render

```bash
./render.sh cache --quick -q l     # fast layout check of one scene (480p15)
./render.sh                        # whole film, 480p
./render.sh full -q h              # final 1080p60 (slow; run in background)
./render.sh --stitch -q m          # render each scene and ffmpeg-concat
```

Everything uses `Text` (Pango), no LaTeX. `render.sh` reuses a sibling Manim venv
(HarnessEngineering / Fourier / CNN) if present.

Pacing knobs (tuned for readable, no-voiceover subtitles):
- `KV_READ`  — absolute reading hold after each block of text (default **3.0 s**).
- `KV_DELAY` — the small pauses *between* animation steps (default `1.1`).
- `KV_QUICK=1` collapses every hold for fast iteration.

Every subtitle stays up ~3 s so there is time to read it; animations are stretched
1.35× so transitions aren't abrupt.

**Measured runtime:** 4:43 (284 s). Verified with `edgecheck.py` (no edge bleed on
any scene) and by eyeballing key frames of every scene (no overlaps, boxes fit,
arrows clean).

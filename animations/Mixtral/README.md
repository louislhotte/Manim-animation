# Mixtral of Experts — a visual explainer

A no-voiceover Manim animation that builds up the **Sparse Mixture-of-Experts
(SMoE)** idea behind Mixtral 8×7B from the ground up, and answers the question
most people have when they first meet it: **why does every token pick exactly 2
of the 8 experts?**

Based on:

> **Mixtral of Experts** — Jiang, Sablayrolles, Roux, Mensch, *et al.*, Mistral AI,
> 2024. [arXiv:2401.04088](https://arxiv.org/abs/2401.04088)

It's a sequel to the repo's *Transformer Inference* and *KV Cache* films and
shares their dark palette and Query/Key/Value colour language.

## What it teaches

- **Why sparsity at all** — in a dense model every token flows through *all* of the
  feed-forward weights; the full price, every step.
- **The SMoE layer** — Mixtral keeps the transformer intact but replaces each
  feed-forward block with **8 experts** (each a full FFN) plus a **router**.
- **The router, exactly** — the gate scores all 8 experts, `TopK` keeps the best 2
  (sending the rest to −∞), a softmax over those two gives blend weights, and the
  layer output is
  `y = Σ softmax(Top2(x·Wg))ᵢ · Eᵢ(x)`.
- **Why 2 of 8** — capacity is (almost) free to grow, but compute is paid *per
  expert*. `k=1` is brittle and gives the router a weak training signal; `k=8` is
  just a dense 47B model again. **Two** blends two specialists at a quarter of the
  expert compute — the knee of the curve.
- **Full scale** — 32 layers, a **fresh 2-of-8 at every layer**: 47B total
  parameters but only **13B active per token**, 32k context, ~10⁴⁶ possible expert
  paths.
- **What experts actually specialize in** — from the paper's routing analysis:
  **not** by topic (code/biology/philosophy/math histograms look the same), but by
  **syntax & position** — neighbouring tokens keep hitting the same expert, a
  locality that grows with depth.
- **The payoff** — matches or beats Llama 2 70B and GPT-3.5 with ~5× fewer active
  parameters; Mixtral 8×7B-Instruct scores **8.30** on MT-Bench (beating GPT-3.5
  Turbo, Claude-2.1, Gemini Pro and Llama 2 70B-chat); open weights, Apache 2.0.

## Scenes

| # | Scene (class) | Beat |
|---|---------------|------|
| — | `Intro`    | Title card |
| 1 | `Dense`    | The cost of a dense feed-forward block |
| 2 | `Experts`  | Split the FFN into 8 experts + a router (the SMoE layer) |
| 3 | `Router`   | Gate → Top-2 → softmax blend, with the formula |
| 4 | `WhyTwo`   | Capacity vs. compute: why `k = 2` is the sweet spot |
| 5 | `Scale`    | 32 layers, a fresh 2-of-8 each; 47B / 13B / 32k |
| 6 | `Learn`    | Routing analysis: syntactic & positional, not semantic |
| 7 | `Results`  | Benchmarks, Instruct MT-Bench, open weights |
| — | `Recap`    | One-breath takeaway |
| — | `Outro`    | Thank-you card |

`MixtralFilm` is the whole thing, intro card to outro card.

## Rendering

```bash
./render.sh router --quick -q l    # fast layout check of one scene (480p15)
./render.sh full                   # whole film, 480p
./render.sh full -q h              # final 1080p60 (the deliverable) — slow
./render.sh --stitch -q h          # render each scene and ffmpeg-concat to one file
```

`render.sh` reuses an existing Manim venv elsewhere in the repo (HarnessEngineering
/ Fourier / CNN) if present, otherwise bootstraps a local `.venv`. No LaTeX is
required — everything is drawn with Pango `Text`.

Pacing knobs (generous by default so every line is readable):

- `MX_QUICK=1` — collapse every hold for a fast sanity render.
- `MX_DELAY=..` — the between-step pause multiplier.
- `MX_READ=..` — the absolute per-subtitle reading hold (≈3 s by default).

## Runtime

Rendered at **1080p60**. Measured full-film duration: **~5 min** (see
`ffprobe -show_entries format=duration` on the final file). Pacing is deliberately
generous — every block of text stays on screen long enough to read.

## Accuracy notes

All architecture numbers are from the paper's Table 1 (dim 4096, 32 layers, 8
experts, top-2, FFN hidden 14336, 32k context, vocab 32000) and Section 5. The
`k=2 → 13B active`, `k=8 → 47B` anchor points, the routing-analysis findings (no
topic specialization; positional/temporal locality that grows with depth; DM
Mathematics marginally different) and the benchmark/MT-Bench figures are all as
reported. Intermediate `active-parameter` values shown during the `k` sweep are
rounded illustrations of the (roughly linear) compute-vs-`k` relationship.

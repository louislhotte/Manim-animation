# What is CLIP?

A short, no-voiceover Manim explainer on **CLIP** (Contrastive Language-Image
Pre-training), in the channel's house style. It answers "what is CLIP?" by
building up the one idea that makes it work: put images and text into a single
vector space, and plain language becomes an open-ended image classifier.

Grounded in Radford et al., *"Learning Transferable Visual Models From Natural
Language Supervision,"* ICML 2021 (arXiv:2103.00020).

Measured runtime: **~2:17** (137 s) at the default reading cadence.

## What it teaches

- **Why CLIP exists.** A classic vision model is trained on a fixed list of
  labels and can only ever answer with one of them. CLIP instead learns from
  ~400M raw (image, caption) pairs scraped from the web, so the caption itself
  is the supervision. No hand-labeling.
- **Two encoders, one space.** An image encoder (ViT / ResNet) and a text
  encoder (Transformer) each turn their input into a vector of the same length,
  and both map into a single shared embedding space.
- **Contrastive pre-training.** Score every image against every caption to get an
  N x N similarity matrix. Training pulls the N matching pairs (the diagonal) up
  and pushes the mismatched pairs down. That is the whole training signal.
- **Zero-shot classification.** To classify a new photo, write each candidate
  label as a prompt ("a photo of a {label}"), embed image and prompts, and pick
  the highest cosine similarity. Swap the words and you have a brand-new
  classifier, with no retraining.

## Scenes

The film is `intro -> problem -> encoders -> contrast -> zeroshot -> outro`:

| Scene      | Class       | What happens |
|------------|-------------|--------------|
| `intro`    | `Intro`     | House title card: "What is CLIP?" |
| `problem`  | `Problem`   | Fixed-label classifier vs. learning from web (image, caption) pairs |
| `encoders` | `Encoders`  | Image + text encoders map into one shared embedding space |
| `contrast` | `Contrast`  | The N x N similarity matrix; the diagonal lights up green |
| `zeroshot` | `ZeroShot`  | Prompt template -> similarity bars -> winner; swap the labels |
| `outro`    | `Outro`     | "Thank you for watching!" + one-line recap |

The whole film is the `WhatIsCLIP` class.

## Rendering

```bash
./render.sh contrast --quick -q l   # fast layout check of one scene (480p15)
./render.sh full                    # whole film, 480p
./render.sh full -q h               # final 1080p60 (slow)
./render.sh --stitch -q m           # render each scene and concat (720p30)
```

`render.sh` reuses an existing repo Manim venv (HarnessEngineering / Fourier /
CNN, manim 0.21.0) if present, otherwise bootstraps a local `.venv`. No LaTeX:
everything is `Text` (Pango), and all the images are hand-drawn vector glyphs
(no baked assets).

Pacing knobs: `CLIP_QUICK=1` collapses every hold for fast iteration;
`CLIP_DELAY=<sec>` overrides the reading-hold multiplier (default 2.0).

# Diffusion Models, Visually

A short, no-voice-over explainer that answers the question people actually have
the first time they watch an image model work: **why does it start from a screen
of random static and "denoise" its way to a picture?**

The through-line:

> You can't paint a good image in one shot (almost every pixel combination is
> garbage). But *destroying* an image is trivial: add noise until any picture
> becomes the same static. So static is a starting point you can always reach.
> Train a network to undo **one small** noising step (predict the noise, subtract
> a little), and you can walk pure noise all the way back to an image. Many small
> nudges are each easy; one giant leap is the impossible problem again. A text
> prompt steers which image emerges. In practice you wire it up in ComfyUI.

The hero image is a **real ComfyUI generation** (the one in the reference
screenshot). Every noise↔image morph is a **baked trajectory** (`generate_assets.py`)
so the denoise is smooth and reproducible; nothing is hand-waved.

## Scenes (measured runtime **4:00**; final at 1080p60, iterate at 480p15)

1. **Intro** — title card, a tile of static resolving toward a picture.
2. **Hook** — pure static resolves into the detailed fox-girl. That image never
   existed; it was denoised out of noise.
3. **Examples** — a gallery of what diffusion makes: anime, photos, digital art,
   3D renders, concept art, video. One idea, all of it. "But why start from noise?"
4. **Forward** — you can't paint pixels blind (a real image is a vanishing needle
   in the haystack of noise). But wrecking one is trivial: add noise, and more,
   until every image becomes the same static.
5. **Reverse** — run the arrow backwards. A trained *denoiser* looks at a noisy
   image and answers one question: which part is noise? Subtract a sliver, repeat.
6. **Steps** — the money shot: a few dozen small steps turn static into an image.
   Why not one jump? One leap gives a blurry average; many small nudges give
   sharp detail.
7. **Prompt** — the noise fixes the layout; the words fix the content. Same seed,
   different prompt ("anime fox girl by a campfire" vs "a mountain lake at
   sunset"), different picture.
8. **Comfy** — how it's wired in practice (the ComfyUI graph): load the denoiser,
   encode the prompt (CLIP), run the sampler loop (steps / cfg / seed), decode the
   latent to pixels (VAE), save. One honest note: real systems denoise in a
   compressed *latent* space, then the VAE decodes to pixels. Closes on the
   takeaway that ComfyUI is a *framework*: chain these blocks into almost any
   generative workflow, in a visual node editor.
9. **Outro** — "Start from noise. Predict it. Subtract a little. Repeat."

Each scene also renders on its own: `Intro Hook Examples Forward Reverse Steps
Prompt Comfy Outro`; the whole film is `DiffusionModels`.

## Assets

- `src_screens/comfyui_full.png` — the reference ComfyUI screenshot.
- `src_screens/foxgirl_sq.png` — the generated image, cropped square (the hero).
- `src_screens/ksampler.png` — the KSampler node, cropped for the zoom inset.
- `generate_assets.py` — bakes `assets/diffusion.npz`: the fox and a procedural
  sunset each blended into **one shared** field of gaussian static (48 frames),
  plus a heavily-blurred fox for the "one big leap" beat. Also writes
  `assets/gallery/*.png` for the Examples scene: the real anime hero plus five
  procedural stand-ins (sunset photo, domain-warped digital art, a shaded 3D
  sphere render, a ringed-planet concept, and an aurora film frame). Deterministic
  (seeded). `render.sh` runs it automatically if the npz is missing.

## Render

```bash
./render.sh full            # whole film, 480p15  (the deliverable)
./render.sh steps --quick   # fast layout check of one scene
./render.sh full -q h       # final 1080p60 (slower)
./render.sh --stitch -q m   # render each scene and concat (720p)
```

`DIFF_QUICK=1` (or `--quick`) collapses the reading holds for fast iteration;
`DIFF_DELAY` / `DIFF_READ` override the motion rhythm and the per-caption hold.

Uses `Text` (Pango) only, no LaTeX. Reuses a sibling Manim venv if present, else
bootstraps a local `.venv`.

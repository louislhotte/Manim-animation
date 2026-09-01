# What is a GAN?

A dynamic, house-style explainer on **Generative Adversarial Networks** — two neural
networks locked in a game, one of which learns to create. It is a 3-D piece in the
spirit of the Quantization film: the discriminator's "how real does this look" score
is a field of glowing bars on a dark plane, and a slow ambient camera orbit keeps it
in motion. Every word the viewer reads (title, captions, HUD) is a fixed-in-frame
overlay, so the text stays put and readable while the field turns underneath.

No voiceover, no LaTeX (all `Text`/Pango). Dark house palette, house intro/outro.

**Everything on screen is driven by a real toy GAN**, trained from scratch in NumPy
(`generate_assets.py`, hand-derived backprop for both networks, no autograd). Nothing
is scripted: the fake cloud really does morph from a blob into the data, and the
discriminator's landscape really does collapse from a sharp terrain to a flat plateau.

## What it teaches

- A GAN is **two networks with opposite jobs**. A **generator** turns a random noise
  vector `z` into a fake sample; a **discriminator** scores how real a sample looks.
- They are **adversaries**: the generator is trained to fool the discriminator, the
  discriminator is trained to catch the fakes. This is a two-player **minimax** game,
  `min_G max_D V(D, G)`.
- The generator starts random — its samples are a **shapeless blob** that ignores the
  real data. The discriminator easily tells them apart: its confidence surface has a
  **sharp valley** carved exactly where the fakes are.
- As the two networks train against each other, the fakes **spread out and lock onto
  the real distribution** (here, the classic 8-Gaussians ring), and the discriminator's
  average score for real and fake samples **drift to the same value**.
- At convergence the discriminator's whole landscape **flattens to about one half**: it
  is reduced to a coin flip and can no longer tell real from fake. The generator has
  learned the distribution — every point in the latent space now maps to a plausible
  new sample, and gliding through the latent space sweeps smoothly through the data.

The target is the **8-Gaussians ring** benchmark; the generator (`z → R²`) and
discriminator (`R² → (0,1)`) are small MLPs trained with the non-saturating GAN loss
and Adam. All the on-screen numbers (the `D(real)` / `D(fake)` scores, the terrains,
the sample clouds) are read straight out of the trained model's snapshots.

## Scenes

The film runs end-to-end as `WhatIsAGAN`, and every section also renders alone:

1. **Intro** — title card.
2. **Goal** — the real data (a ring of eight blobs); we want to invent new samples that
   fit right in.
3. **Players** — the generator and the discriminator, their roles, and why they are
   adversaries.
4. **Generator** — noise `z` through the network to one fake sample; many samples are a
   blob that misses the ring.
5. **Discriminator** — its "realness" score as a 2-D heatmap, then lifted into a **3-D
   orbiting landscape** with a deep valley under the fakes.
6. **Game** — the adversarial training loop and the minimax objective, then the **real
   training morph**: the fakes lock onto all eight modes while `D(real)` and `D(fake)`
   converge.
7. **Convergence** — the landscape **melts flat** (a coin flip), then a **latent-space
   walk** shows the outputs sweeping smoothly around the ring.
8. **Outro** — thanks + one-line recap, over the orbiting landscape.

## Rendering

```bash
./render.sh discriminator --quick -q l   # fast layout check of one scene (480p15)
./render.sh full                         # whole film, 480p
./render.sh full -q h                    # final 1080p60 (slow; the 3-D + orbit shine at 60 fps)
./render.sh --stitch -q m                # render each scene and concat to one file (720p30)
```

Scenes: `full` (default) · `intro` · `goal` · `players` · `generator` ·
`discriminator` · `game` · `convergence` · `outro`. Quality: `-q l|m|h|k` =
480p15 / 720p30 / 1080p60 / 2160p60. `--quick` (`GAN_QUICK=1`) collapses the reading
holds for fast iteration; `GAN_DELAY=<s>` overrides the reading rhythm. `--assets`
forces a re-bake of the trained model.

**The real GAN assets** (`assets/gan.npz`) are baked automatically on the first render
if missing; regenerate them explicitly with `python generate_assets.py` (about 15 s).

**Note on this OneDrive-synced repo:** `render.sh` writes Manim's media into a local
scratch dir (`/private/tmp/gan-media`) by default, because writing the many partial
movie files into the OneDrive-synced tree stalls for minutes on sync I/O. Set
`GAN_MEDIA_DIR="$PWD/media"` if you want the artifacts kept alongside the code.

## Runtime

Measured with `ffprobe`: **4:17** (258 s) at the default reading cadence. Layout is
identical at every quality — only the resolution and frame rate change, so the
duration is the same at `-q h`.

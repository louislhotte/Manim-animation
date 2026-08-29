# How QR Codes Work

A short, no-voiceover Manim explainer: how a URL becomes the grid of black-and-white
squares you scan, and why you can cover part of it with a logo and it *still* works.

The code on screen is **not a drawing** — it is a **real, scannable QR code** for
`https://ptoleme.dev`, generated with a proper QR encoder (`segno`: version 2,
error-correction level Q, mask 7) and baked in as a literal. Everything structural
(which module is a finder / timing / alignment / format cell, the zig-zag data-placement
order, the mask pattern) is **derived from the QR spec at import time** — nothing is faked.
You can pause the film and scan the code.

## What it teaches

1. **A link in disguise** — point a camera at the squares and out comes a URL; those
   squares aren't random.
2. **From text to bits** — *byte mode*: every character becomes its 8-bit code; the whole
   link is one binary string, wrapped with a small header and error-correction bytes.
3. **Not all squares are data** — the fixed patterns: quiet zone, three finder "eyes"
   (orientation), timing lines (a ruler), the alignment square (keeps the grid true when
   tilted), and the format-info stripe.
4. **Placing & masking** — the data bits snake in from the bottom-right, two columns at a
   time; then one of eight mask patterns is XOR-ed over them to even out light and dark so
   a scanner isn't confused.
5. **Damage it — it still works** — Reed–Solomon error correction lets you cover ~a quarter
   of the code (e.g. with a logo) and still recover the link, as long as the three finder
   eyes survive.

## Scenes

| Scene        | Class        | Beat                                            |
|--------------|--------------|-------------------------------------------------|
| Intro        | `Intro`      | title card (a mini QR assembles)                |
| 01           | `Hook`       | scan the code → the URL pops out                |
| 02           | `Encode`     | URL → bytes → an 8-bit-per-character bit stream |
| 03           | `Anatomy`    | the fixed patterns, colour-coded + a legend     |
| 04           | `Placement`  | zig-zag data fill, then XOR masking             |
| 05           | `Robustness` | cover the middle with a logo, it still scans    |
| Outro        | `Outro`      | recap + "Thanks for watching!"                  |
| Whole film   | `QRCodes`    | intro card → outro card, end to end             |

## Render

```bash
./render.sh hook --quick -q l   # fast layout check of one scene (480p15)
./render.sh full                # the whole film, 480p
./render.sh full -q h           # final 1080p60 (slow; run in background)
./render.sh --stitch -q m       # render each scene and ffmpeg-concat to one file
```

Pacing knobs (env): `QR_QUICK=1` collapses every reading hold for fast iteration;
`QR_DELAY=<seconds>` overrides the reading-hold rhythm (default `1.6`).

## Runtime

Measured full-film duration (`QRCodes`, non-quick, 480p): **2:43** (163.7 s, `ffprobe`).
Uses `Text` (Pango) throughout — no LaTeX toolchain.

# Detecting Change From Space

A short, no-voiceover Manim explainer on geospatial change detection, built on
**real satellite imagery**: the same NDVI formula that flags deforestation in
the Amazon is also used to flag crop stress in a Kansas field.

## What it teaches

1. **The signal in the light** — a quick tour of the electromagnetic spectrum
   first: sunlight includes wavelengths past red that our eyes can't see at
   all, and NIR means **N**ear-**I**nfra**R**ed, just beyond it (Red ≈ 665 nm,
   NIR ≈ 842 nm, the real Sentinel-2 band centers). Every satellite pixel
   carries a Red and a NIR reflectance value. Healthy vegetation absorbs red
   for photosynthesis but scatters NIR strongly; bare ground does neither.
   That gives the NDVI formula:

   ```
   NDVI = (NIR - Red) / (NIR + Red)
   ```

   Plugging in real, representative reflectance values (healthy forest vs.
   bare/cleared ground) gives NDVI ≈ 0.82 vs. ≈ 0.15 — computed on screen, not
   hardcoded. Sentinel-2 (ESA/Copernicus) and Landsat (USGS/NASA) capture
   exactly this band pair, free and open, over the whole planet every few
   days.

2. **Deforestation** — two **real satellite photographs** of the exact same
   AOI in Rondônia, Brazil: Landsat 5 true colour from 1990 (dense forest)
   and Sentinel-2 true colour from 2023 (a checkerboard of cleared farmland),
   plus the same two scenes rendered as real, server-computed NDVI. A real
   Natural-Earth outline of Brazil marks where. Global Forest Watch and
   Brazil's DETER run this exact NDVI check on the open Sentinel-2/Landsat
   archive (built on the Hansen/UMD Global Forest Change dataset).

3. **Agriculture** — a **real Sentinel-2 photograph** of Kearny County,
   Kansas: hundreds of center-pivot irrigation circles, true colour and real
   NDVI, then a zoomed real crop showing one genuinely stressed/fallow circle
   sitting right next to thriving ones (pixel-verified against the source
   image, not illustrative).

4. **Recap** — one pipeline end to end: Red + NIR bands → NDVI → threshold →
   alert. Two very different, consequential questions, answered by the same
   open pixels.

Bookended by the channel's house intro / "Thank you for watching!" outro.

## Real data sources

All satellite imagery is fetched once by `fetch_assets.py` from
[Microsoft Planetary Computer](https://planetarycomputer.microsoft.com/)'s
public data API (a titiler deployment — free, no auth/API key). Band math
(NDVI) and colour rendering are computed **server-side on real reflectance
bands**, not faked locally. Baked into `assets/` so the render itself needs no
network access.

| asset | source | scene ID | date | cloud |
|---|---|---|---|---|
| `rondonia_2023_tci/ndvi.jpg` | Sentinel-2 L2A (ESA/Copernicus) | `S2B_MSIL2A_20231116T142709_R053_T20LNQ_20231116T201659` | 2023-11-16 | 3% |
| `rondonia_1990_tci/ndvi.jpg` | Landsat 5 C2 L2 (USGS/NASA) | `LT05_L2SP_231067_19900618_02_T1` | 1990-06-18 | 0% |
| `kansas_wide_tci/ndvi.jpg`, `kansas_close_*.jpg` | Sentinel-2 L2A (ESA/Copernicus) | `S2A_MSIL2A_20230830T171901_R012_T14SLG_20230831T022350` | 2023-08-30 | 0% |
| `world_map.json` | [Natural Earth](https://www.naturalearthdata.com/) 1:110m Admin 0 Countries (public domain) | — | — | — |

AOIs: Rondônia bbox `-62.9,-10.0,-62.45,-9.6` (a real, long-documented
"fishbone"/checkerboard clearing area along BR-364, e.g. NASA Earth
Observatory, INPE PRODES/DETER coverage); Kansas bbox
`-100.85,37.45,-100.45,37.8` (Kearny/Finney/Haskell county center-pivot
country). Landsat NDVI applies the Collection-2 reflectance scale/offset
(`DN * 0.0000275 - 0.2`) before the ratio — using the raw scaled DN directly
distorts NDVI.

To refetch or change the AOIs:

```bash
<manim-venv>/bin/python fetch_assets.py
```

## Scenes

| key             | class                       | what it shows                                    |
|-----------------|------------------------------|---------------------------------------------------|
| `intro`         | `Intro`                      | title card                                        |
| `signal`        | `Signal`                     | spectrum/NIR explainer, NDVI formula, NDVI scale  |
| `deforestation` | `Deforestation`               | real Landsat 1990 vs. Sentinel-2 2023, Rondônia   |
| `agriculture`   | `Agriculture`                 | real Sentinel-2 over Kansas center-pivot circles  |
| `recap`         | `Recap`                       | pipeline chips + climate/ag takeaways             |
| `outro`         | `Outro`                       | thank-you card                                    |
| `full`          | `DetectingChangeFromSpace`    | the whole film                                    |

## Rendering

```bash
./render.sh intro --quick -q l     # fast sanity check of one scene
./render.sh full                   # whole film, 480p
./render.sh full -q h              # final 1080p60 render
./render.sh --stitch -q m          # render each scene and stitch (720p)
```

Quality: `-q l|m|h|k` = 480p15 / 720p30 / 1080p60 / 2160p60.
`GD_QUICK=1` (or `--quick`) collapses every reading hold for fast iteration.

**Measured runtime:** ~2:56 (real pacing; 176.4s at 1080p60, 177.7s at 480p15).

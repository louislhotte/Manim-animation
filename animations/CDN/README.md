# Content Delivery Networks — a short explainer

A no‑voiceover, house‑style Manim film that introduces **CDNs** for a system‑design
audience: what a CDN is, the problem it solves, how a request actually flows
through it, and when it pays off.

Everything is set in `Text` (Pango) — no LaTeX — so it renders fast and needs no
TeX toolchain.

## What it teaches

- **Why**: your origin lives in one place, but users are global — distance adds
  latency and a single origin strains under the whole world's traffic.
- **What**: a CDN is a worldwide network of **edge** servers that keep **cached**
  copies of your content close to users (Origin / Edge‑PoP / Cache).
- **How**: cache **MISS** (the edge fetches from the origin and stores a copy)
  vs. cache **HIT** (served straight from the edge); TTL expiry and nearest‑edge
  (anycast/DNS) routing.
- **When / the payoff**: what to cache (static/media) vs. what stays at the
  origin (dynamic/personalised); lower latency, less origin load, resilience to
  spikes/outages, cheaper egress, and built‑in security (DDoS/WAF/TLS).

## Scenes

| Scene        | Class         | Beat |
|--------------|---------------|------|
| Intro card   | `Intro`       | Title + "Created by Ptolémé" |
| Problem      | `Problem`     | One origin, a planet of users; the long round‑trip; overload |
| Idea         | `Idea`        | Definition; edges cache content near users; near vs. far; key terms |
| How it works | `HowItWorks`  | User → Edge → Origin; cache miss vs. hit; TTL & routing |
| Use cases    | `UseCases`    | What to cache; when to use; the benefits; providers |
| Outro card   | `Outro`       | "Thank you for watching!" |

The whole film is the `CDN` class.

## Render

```bash
./render.sh problem --quick -q l   # fast layout check of one scene (480p15)
./render.sh                        # whole film, 480p (default)
./render.sh full -q h              # final 1080p60 (slow)
./render.sh --stitch -q m          # render each scene and ffmpeg-concat to one file
```

`render.sh` reuses an existing Manim venv in the repo (HarnessEngineering /
Fourier / CNN) if present, otherwise bootstraps a local `.venv` from
`requirements.txt` (manim 0.21.0 + numpy).

### The globe

The planet is a baked texture, `assets/planet_blue.png`, rendered as an
`ImageMobject`. Regenerate/retint it with:

```bash
../HarnessEngineering/.venv/bin/python assets/make_planet.py
```

`make_planet.py` reads `assets/source_globe.png` (a gray‑continents orthographic
globe) and re‑shades it into a blue sphere (diffuse + limb darkening + soft
specular + atmospheric rim). Tweak the `OCEAN` / `LAND` / `ATMO` colours at the
top of that script.

### Pacing knobs

- `CDN_QUICK=1` (or `--quick`) collapses every reading hold for fast iteration.
- `CDN_DELAY=<seconds>` overrides the reading rhythm (default `1.45`).

## Runtime

Measured full‑film duration: **2 min 2 s** (122 s, `CDN` class, 133 animations,
default pacing `CDN_DELAY=1.45`). Duration is the same at every quality.
_Re‑measure with_ `ffprobe -v quiet -show_entries format=duration -of csv=p=0 <file>.mp4`.

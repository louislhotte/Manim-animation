# Moiré of Life

Two overlapping grids of sine waves. One grid rotates slowly against the other,
and their interference blooms into breathing, swirling mandalas. Then the camera
falls into the centre: the giant macro-pattern inflates past the edges of the
frame and **dissolves back into the bare micro sine waves** that were there the
whole time.

> The moiré isn't drawn — it *emerges*. Nothing on screen is a circle or a
> spiral; every fringe is just `sin + sin` sampled on a pixel grid.

## The idea

Each frame is a scalar interference field, evaluated per pixel in numpy:

```
grid(θ) = Σ_{k<N} sin( k_f · (x·cos aₖ + y·sin aₖ) ),   aₖ = θ + kπ/N
F(x,y)  = grid(spin) + grid(spin + φ)      # two grids overlaid → a moiré
```

Each **grid** is a *fan* of `N` sine gratings evenly spread over a half-turn.
A single fan already has N-fold rotational symmetry about the origin — that's
the mandala. (Two perpendicular gratings, `N = 2`, would only ever tile into a
flat fabric; a fan of six radiates.) Overlay two fans, turn the second by `φ`,
and their interference is the moiré.

- **Rotation** is the relative angle **φ** between the two fans. Near `φ = 0`
  they coincide into one crisp mandala; as φ grows the rosette re-tiles — cells
  regroup into ever-larger flowers — so the mandala breathes and swirls.
- **Zoom** shrinks the sampling frequency `k_f ∝ 1/zoom` about the origin — an
  *exponential* dive into the centre. The macro mandala inflates past the frame
  and the underlying micro sine waves surface.
- A hand-built colour ramp (indigo → violet → magenta → ember → gold → white),
  fine contour etching (the crests of the field), and a radial vignette turn the
  field into a mandala.

The whole thing is a single full-frame `ImageMobject` whose `pixel_array` is
recomputed and swapped in on every frame — Manim re-rasterises it each time, so
the field animates without any vector geometry.

## Render

```bash
./render.sh --quick        # ~15 s low-res sanity check
./render.sh -q m           # 720p30
./render.sh -q h -p        # 1080p60 final, then open it
```

First run reuses a sibling series' Manim venv (HarnessEngineering / Fourier /
CNN) or bootstraps a local `.venv`. Output lands in
`media/videos/moire_of_life/<res>/MoireOfLife.mp4`.

> Heads-up: the field is computed in numpy every frame, so a full 1080p60 render
> is compute-heavy (a few minutes of field work plus Manim's encoding). Use
> `-q m` while iterating.

## Knobs

All optional environment variables:

| Var           | Default | Effect                                                    |
| ------------- | ------- | --------------------------------------------------------- |
| `MOIRE_RES`   | by `-q` | Field height in px (width follows 16:9). Sharpness ↔ cost |
| `MOIRE_FREQ`  | `26`    | Grid density — sine cycles across the frame height        |
| `MOIRE_ZOOM`  | `11`    | Final magnification reached at the bottom of the dive     |
| `MOIRE_SYM`   | `6`     | Gratings per grid = the fold of the mandala (try 4, 5, 8) |
| `MOIRE_QUICK` | `0`     | `1` compresses every beat (same as `--quick`)             |

```bash
# denser, eight-fold mandala, deeper plunge
MOIRE_FREQ=34 MOIRE_SYM=8 MOIRE_ZOOM=14 ./render.sh -q m
```

## Structure

- **Act I — the swirl:** φ rises and the whole tapestry spins; the macro mandala
  breathes (cells swell, then tighten).
- **Act II — the dive:** exponential zoom into the centre; the macro pattern
  inflates past the frame.
- **Act III — the floor:** what remains is two overlapping sine grids at an
  angle — *the same wave, all the way down.*

# Documentation

How the repository is laid out and how to run everything in it.

## Repository structure

```
Manim-animation/
├── animations/              # All Manim animation scenes
│   ├── <Name>/              # One explainer film per folder (KVCache, Transformer, …):
│   │                        #   <name>.py, a 10-line render.sh, README.md, assets/
│   ├── 2024/                # 2024 series: DFS, pendulum, Galton board, Taylor,
│   │   │                    #   KMeans, GMM, Koch curve, epidemic model, …
│   │   └── Svg/             # SVG assets used by some scenes
│   ├── Quant/               # Quant-interview notebooks (Bloomberg, dice, regression)
│   ├── CNN/                 # Convolutional Neural Network series, Parts 1–6
│   │                        #   (adapted from a third-party project; uses voiceover)
│   └── conv.py              # Standalone convolution scene (reads from ../images/)
├── manimx/                 # Shared library of the explainer series (crisp text, palette,
│                            #   pacing, captions, cards, glyphs, code panels, data visuals)
├── tools/                   # render_lib.sh (the one render driver), new_film.py,
│                            #   lint_film.py, edgecheck.py, contact_sheet.sh,
│                            #   scene_fingerprint.py, requirements-render.txt
├── Simulations/             # matplotlib simulations (same intro/outro house style)
├── .claude/skills/          # manim-explainer: the house standards + workflow for Claude
├── projects/                # Non-Manim side projects
│   ├── RL/                  # Pygame melee/genetic-algorithm simulation
│   └── Sport Tracker/       # Swimming log spreadsheet
├── images/                  # Input images (MNIST, etc.) used by conv.py & CNN scenes
├── assets/                  # Repo assets (e.g. the README banner)
├── docs/                    # You are here
├── main.py                  # Standalone networkx tree plot (scratch)
├── main.ipynb               # Web-scraping notebook (scratch)
├── requirements.txt         # Runtime dependencies
├── requirements-dev.txt     # Dev tooling (pre-commit, ruff, isort, jupyterlab)
├── pyproject.toml           # Ruff + isort configuration
└── .pre-commit-config.yaml  # Git pre-commit hooks
```

## The explainer series (`animations/<Name>/`)

Every film imports the shared library (`from manimx import *`) and renders through its
folder's `render.sh`, a thin wrapper over `tools/render_lib.sh`:

```bash
cd animations/KVCache
./render.sh --list                   # scene names
./render.sh cache --quick --check    # one scene, 480p, short holds + edge scan + contact sheet
./render.sh                          # the whole film at 480p
./render.sh full -q h                # final 1080p60 (slow: run it in the background)
```

- **Python**: on first use the driver creates one shared venv **outside OneDrive** at
  `~/.cache/manimx/venv` (`tools/requirements-render.txt`, then each film's
  `requirements.txt`). Venvs inside the OneDrive folder break: their symlinks become
  text files that "run" and render nothing. Override with `MX_PYTHON` / `MX_VENV`.
- **Knobs**: `MX_QUICK=1` (or `--quick`), `MX_DELAY`, `MX_READ`, `MX_MEDIA_DIR`, `MX_FONT`;
  each film also honours its own `<PREFIX>_QUICK/_DELAY/_READ`.
- **No LaTeX needed**: text is Pango (`manimx.Text`).

New film: `python3 tools/new_film.py Name "Title" "One-line promise" --prefix NM`, then
write the storyboard in the module docstring. Checks: `python3 tools/lint_film.py
animations/Name/name.py`. The standards, quality bar and verification loop live in
`.claude/skills/manim-explainer/SKILL.md`.

Changing `manimx`? Prove no film changed: run
`~/.cache/manimx/venv/bin/python tools/scene_fingerprint.py animations/<Name>/<file>.py`
before and after and diff the digests (identical digests mean identical frames).

## Prerequisites (legacy scenes)

Manim renders LaTeX and encodes video, so besides Python you need:

- **Python 3.11+**
- **ffmpeg** — video encoding (`brew install ffmpeg`)
- **A LaTeX distribution**: only for the legacy `Tex`/`MathTex` scenes (2024 series, CNN,
  Fourier); the explainer series does not need it

See the [Manim installation guide](https://docs.manim.community/en/stable/installation.html) for platform details.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # add -r requirements-dev.txt for the tooling
```

## Rendering a legacy scene

Each `.py` file under `animations/2024/` (and `conv.py`) defines one or more `Scene` subclasses. Render a
scene by pointing the `manim` CLI at the file and naming the class:

```bash
# high quality + open when done (-p preview, -q quality l/m/h/k)
manim -pqh animations/2024/galton.py GaltonBoard
manim -pql animations/2024/Koch_curve.py KochCurve
manim -pqh animations/2024/normal.py GaussianDistribution
```

- Rendered files land in `media/` (git-ignored).
- To list the scenes in a file without rendering: `manim animations/2024/galton.py`.
- **Working directory matters** for scenes that load images. `animations/conv.py`
  reads from `images/`, so run it from the repo root:
  `manim -pqh animations/conv.py Scene1_2`.

### Voiceover scenes (`animations/CNN/`)

These use [`manim-voiceover`](https://voiceover.manim.community/). They need
`manim-voiceover` + a TTS backend (ElevenLabs) and an API key in your environment:

```bash
export ELEVEN_API_KEY="..."        # or the backend configured in the scene
```

CNN scenes reference images with paths relative to their own `Part …/` folder, so
`cd` into that folder before rendering. Some intermediate images are generated by the
`apply_kernel.py` / `add.py` helper scripts in the same folder.

## Running the notebooks

`animations/Quant/*.ipynb` and `animations/2024/GMM.ipynb`:

```bash
pip install -r requirements-dev.txt   # includes jupyterlab
jupyter lab
```

Run `from manim import *` in an early cell, then render a scene with the cell magic
(it must be the **first line** of the cell):

```python
%%manim -qm ExampleScene
class ExampleScene(Scene):
    def construct(self):
        self.play(Write(Text("Hello")))
```

## Running the RL project

```bash
python projects/RL/game.py     # single simulation
python projects/RL/gen.py      # genetic-algorithm training loop
```

Asset paths in `projects/RL/` are resolved relative to the scripts, so they work from
any working directory.

## Development tooling

```bash
pip install -r requirements-dev.txt
pre-commit install            # run the hooks automatically on `git commit`
pre-commit run --all-files    # run them once across the whole repo
```

The hooks (configured in `.pre-commit-config.yaml`, with rules in `pyproject.toml`):

| Hook          | What it does                                  |
|---------------|-----------------------------------------------|
| `isort`       | Sorts and groups imports (black profile)      |
| `ruff`        | Lints Python and auto-fixes what it safely can |
| `ruff-format` | Formats Python (black-compatible)             |
| misc hooks    | Trailing whitespace, EOF newline, YAML/TOML, large files |

Bump hook versions with `pre-commit autoupdate`.

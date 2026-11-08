"""Scaffold a new explainer: animations/<Name>/ wired to manimx and the shared renderer.

    python3 tools/new_film.py RAFT "Retrieval-Augmented Fine-Tuning" \
        "Why a model should study the documents it will be quizzed on" --prefix RAFT

Creates <name>.py (storyboard docstring, base scene, three scene stubs that
already follow the house bar, Intro/Outro, the full-film class), render.sh,
requirements.txt and README.md. Fill the STORYBOARD first, then the scenes.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

FILM_PY = '''"""{title}: {subtitle}.

STORYBOARD (write this before any code; one line per scene, see the skill):

    scene        question it answers        hero visual (fills the frame)        what moves                  takeaway caption
    1 problem    ...                        ...                                  ...                         ...
    2 mechanism  ...                        ...                                  ...                         ...
    3 payoff     ...                        ...                                  ...                         ...

Persistent motif (the object that travels through every scene): ...
Real data / source: ...  (cite it on screen with self.cite(...))

Scenes render alone (``./render.sh problem --quick --check``) or as one film
(``./render.sh full``). Pacing knobs: {prefix}_QUICK, {prefix}_DELAY, {prefix}_READ.
"""

from __future__ import annotations

import numpy as np
from manimx import *

# ---- the film's colour language (semantic aliases of the house hues) -------- #
HERO_C = LILAC  # the persistent motif
DATA_C = MINT  # data at rest
HOT_C = AMBER  # where attention should go

RNG = np.random.default_rng(7)  # seeded: every render is identical
VALUES = RNG.uniform(size=(7, 14))  # TODO: the real data; it is the film's motif
FOCUS = (2, slice(4, 9))  # the cells the story is about


class _Base(ExplainerScene):
    pace = Pace.from_env("{prefix}")
    TITLE = "{title}"
    SUBTITLE = "{subtitle}"
    TAGLINE = "{tagline}"
    RECAP = "{recap}"
    SCENES = ("problem", "mechanism", "payoff")

    def motif(self, cell=0.56):
        """The object that travels through the film (here: the data heatmap)."""
        return heatmap(VALUES, DATA_C, cell=cell)

    # ---- scene 1 --------------------------------------------------------- #
    def scene_problem(self):
        header = self.section_header("1 · The problem", HOT_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # The hero visual IS the explanation: real values drawn as a picture,
        # big enough to fill the frame between the header and the caption.
        grid = self.motif().move_to(DOWN * 0.15)
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.2) for r in grid], lag_ratio=0.1),
                  run_time=1.4)
        self.caption("Write one plain sentence that says what the picture shows.")

        hot = SurroundingRectangle(grid[FOCUS[0]][FOCUS[1]], color=HOT_C, buff=0.06)
        self.play(Create(hot), run_time=0.6)
        self.caption("Then point at the one thing to look at, and say why it matters.", hold=1.4)
        self.settle()
        self.wipe()

    # ---- scene 2 --------------------------------------------------------- #
    def scene_mechanism(self):
        header = self.section_header("2 · How it works", HERO_C)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        bars = prob_bars([("first", 0.62), ("second", 0.21), ("third", 0.17)],
                         unit=7.0, fs=34, gap=0.95, color=HOT_C)
        bars.move_to(UP * 0.5)
        self.play(LaggedStart(*[GrowFromEdge(r, LEFT) for r in bars], lag_ratio=0.15),
                  run_time=1.2)
        self.caption("Show the mechanism moving: the same object, transformed step by step.")

        n = ValueTracker(0)
        counter = live_number(n, fmt="{{:,.0f}} steps", fs=34,
                              anchor=lambda m: m.next_to(bars, DOWN, buff=0.7))
        self.add(counter)
        self.play(n.animate.set_value(1000), run_time=2.0, rate_func=linear)
        self.read(1.0)
        self.settle()
        self.wipe()

    # ---- scene 3 --------------------------------------------------------- #
    def scene_payoff(self):
        header = self.section_header("3 · The payoff", GOOD)
        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.6)

        # Reprise the motif: the same picture, now resolved. No bullet list.
        grid = self.motif().move_to(DOWN * 0.15)
        self.play(FadeIn(grid), run_time=0.8)
        fixed = grid[FOCUS[0]][FOCUS[1]]
        self.play(fixed.animate.set_fill(GOOD, opacity=0.95), run_time=1.0)
        self.add(self.cite("Source: the paper / dataset / benchmark the numbers come from"))
        self.caption("Land the takeaway on the hero visual itself, not on a bullet list.", hold=1.4)
        self.settle()
        self.wipe()


# ---- renderable scenes ------------------------------------------------------ #
class Intro(_Base):
    def construct(self):
        self.play_intro()


class Problem(_Base):
    def construct(self):
        self.scene_problem()


class Mechanism(_Base):
    def construct(self):
        self.scene_mechanism()


class Payoff(_Base):
    def construct(self):
        self.scene_payoff()


class Outro(_Base):
    def construct(self):
        self.play_outro()


class {film}(_Base):
    def construct(self):
        self.play_all()
'''

RENDER_SH = """#!/usr/bin/env bash
#
# Render the "{title}" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE={snake}.py
FILM={film}
SCENES=(Intro Problem Mechanism Payoff Outro)
source "$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)/../../tools/render_lib.sh"
"""

REQS = """# Rendered with the shared venv (tools/requirements-render.txt: manim, numpy,
# pillow, scipy). List only what this film needs beyond that.
manim==0.21.0
numpy
"""

README = """# {title}

{subtitle}. A no-voiceover, house-style Manim film built on `manimx`.

## What it teaches

1. **Problem**: ...
2. **Mechanism**: ...
3. **Payoff**: ...

## Storyboard

See the docstring at the top of `{snake}.py` (question, hero visual, motion,
takeaway per scene; the persistent motif; the data source).

## Scenes

`Intro · Problem · Mechanism · Payoff · Outro`, each renderable alone;
`{film}` is the whole film.

## Render

```bash
./render.sh problem --quick --check   # layout pass + edge scan + contact sheet
./render.sh                           # whole film, 480p
./render.sh full -q h                 # final 1080p60 (slow: run in background)
```

Pacing knobs: `{prefix}_READ` (reading hold), `{prefix}_DELAY` (rhythm),
`{prefix}_QUICK=1` / `--quick` (collapse holds).

**Measured runtime:** TODO (`ffprobe` the final render).

## Sources

TODO: every number on screen, and where it comes from.
"""


def snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("name", help="CamelCase folder name, e.g. RAFT or VectorClocks")
    ap.add_argument("title", help='on-screen title, e.g. "Vector Clocks"')
    ap.add_argument("subtitle", help="one-line promise of the film")
    ap.add_argument(
        "--prefix", help="env-var prefix for pacing knobs (default: initials)"
    )
    ap.add_argument(
        "--tagline", default="", help="small line under the byline on the intro card"
    )
    ap.add_argument("--recap", default="", help="one-line recap on the outro card")
    args = ap.parse_args()

    if not re.fullmatch(r"[A-Z][A-Za-z0-9]+", args.name):
        sys.exit("name must be CamelCase, e.g. VectorClocks")
    root = REPO / "animations" / args.name
    if root.exists():
        sys.exit(f"{root} already exists")
    prefix = (
        args.prefix
        or "".join(c for c in args.name if c.isupper())[:4]
        or args.name[:3].upper()
    )
    fields = dict(
        title=args.title,
        subtitle=args.subtitle,
        tagline=args.tagline,
        recap=args.recap,
        prefix=prefix,
        snake=snake(args.name),
        film=f"{args.name}Film",
    )
    root.mkdir(parents=True)
    (root / f"{fields['snake']}.py").write_text(FILM_PY.format(**fields))
    (root / "render.sh").write_text(RENDER_SH.format(**fields))
    (root / "render.sh").chmod(0o755)
    (root / "requirements.txt").write_text(REQS)
    (root / "README.md").write_text(README.format(**fields))
    print(
        f"Created {root.relative_to(REPO)}/ ({fields['snake']}.py, render.sh, README.md)"
    )
    print(
        "Next: write the STORYBOARD docstring, then  cd",
        root.relative_to(REPO),
        "&& ./render.sh problem --quick --check",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

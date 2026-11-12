"""How much of a rendered film is actually moving, and where does it freeze?

Decodes each video at a few frames per second, counts the pixels that change from one
sample to the next and reports:

  * the share of the running time with visible motion;
  * every still stretch of ``--min`` seconds or more, with its start time,

so the dead spots of a film can be found (and filled with motion that means
something) without watching it. Use it before and after a pacing change: the Yjs
film went from 47-73 % moving per scene, with freezes of up to 5 s, to 69-82 % with
no still stretch over 2 s.

Catches: reading holds where nothing moves, endings that sit on a finished picture.
Does NOT judge: whether the motion means anything (read the contact sheet for that).

Usage:
    python motioncheck.py <video.mp4> [more.mp4 ...] [--min 2.0] [--fps 5]

Needs ffmpeg on PATH and numpy (the Manim venv has it). Run it on the full-pace render,
not on a ``--quick`` one (quick mode collapses the holds this tool is looking for):
    ~/.cache/manimx/venv/bin/python tools/motioncheck.py /private/tmp/x-media/videos/x/480p15/*.mp4
"""

import argparse
import subprocess
from pathlib import Path

import numpy as np

W, H = 427, 240  # analysis size: small enough to be fast, large enough to see a caret
LUMA_STEP = 18  # a pixel "changed" when its luma moved by more than this (of 255)
STILL_PIXELS = 60  # fewer changed pixels than this (of 102k) = nothing visibly moved


def frames(path, fps):
    cmd = [
        "ffmpeg", "-v", "error", "-i", str(path), "-vf", f"fps={fps},scale={W}:{H}",
        "-f", "rawvideo", "-pix_fmt", "gray", "-",
    ]  # fmt: skip
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, H, W)


def still_runs(still, fps, min_s):
    """``[(start_s, length_s), ...]`` for every run of still samples >= ``min_s``."""
    runs, start = [], None
    for i, s in enumerate(still):
        if s and start is None:
            start = i
        if start is not None and (not s or i == len(still) - 1):
            end = i if not s else i + 1
            if (end - start) / fps >= min_s:
                runs.append((start / fps, (end - start) / fps))
            start = None
    return runs


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("videos", nargs="+", type=Path)
    ap.add_argument(
        "--min", type=float, default=2.0, help="shortest still stretch to report (s)"
    )
    ap.add_argument("--fps", type=int, default=5, help="samples per second")
    args = ap.parse_args()

    for path in args.videos:
        f = frames(path, args.fps).astype(np.int16)
        if len(f) < 2:
            print(f"{path.name}: too short to analyse")
            continue
        changed = (
            (np.abs(np.diff(f, axis=0)) > LUMA_STEP).reshape(len(f) - 1, -1).sum(axis=1)
        )
        still = changed < STILL_PIXELS
        runs = still_runs(still, args.fps, args.min)
        longest = max((d for _, d in runs), default=0.0)
        print(
            f"{path.name:22s} {len(f) / args.fps:6.1f} s   moving {100 * (1 - still.mean()):3.0f} %   "
            f"still stretches >= {args.min:g} s: {len(runs)}  (longest {longest:.1f} s)"
        )
        for t, d in runs:
            print(f"      still from {t:6.1f} s for {d:4.1f} s")


if __name__ == "__main__":
    main()

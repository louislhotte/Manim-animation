"""Automated off-screen / edge-bleed detector for rendered Manim scenes.

Samples frames from a video and flags any real content (non-background pixels)
that touches the outer border — which is what a cut-off label looks like. Also
reports the nearest-content gap to each edge for context.

Catches: text/elements running off-screen.
Does NOT catch: elements overlapping each other (eyeball those — see the skill).

Usage:
    python edgecheck.py <video.mp4> [n_samples]      # default 40 samples

Needs ffmpeg/ffprobe on PATH and numpy + Pillow (the Manim venv has both), e.g.
    animations/HarnessEngineering/.venv/bin/python edgecheck.py Scene.mp4 48
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

BG = np.array([14, 17, 23])   # house background #0E1117 — change if a scene differs
MARGIN = 9                    # px border strip to inspect
COLOR_THRESH = 34             # channel distance from BG to count a pixel as "content"
BLEED_THRESH = 20             # content px in a strip → flag as cut off


def content_mask(im):
    return np.abs(im.astype(int) - BG).max(axis=2) > COLOR_THRESH


def check_frame(path):
    im = np.array(Image.open(path).convert("RGB"))
    m = content_mask(im)
    h, w = m.shape
    strips = {
        "top": int(m[:MARGIN, :].sum()),
        "bottom": int(m[-MARGIN:, :].sum()),
        "left": int(m[:, :MARGIN].sum()),
        "right": int(m[:, -MARGIN:].sum()),
    }
    flagged = {k: v for k, v in strips.items() if v > BLEED_THRESH}
    ys, xs = np.where(m)
    gaps = None
    if len(xs):
        gaps = {"top": int(ys.min()), "bottom": int(h - 1 - ys.max()),
                "left": int(xs.min()), "right": int(w - 1 - xs.max())}
    return flagged, gaps


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python edgecheck.py <video.mp4> [n_samples]")
    video = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    dur = float(subprocess.check_output(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", video]).decode().strip())
    name = Path(video).stem
    any_flag = False
    with tempfile.TemporaryDirectory() as td:
        for i in range(n):
            t = min(dur * (i + 0.5) / n, max(0.0, dur - 0.15))
            fp = f"{td}/f{i:03d}.png"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}",
                            "-i", video, "-frames:v", "1", fp], check=False)
            if not Path(fp).exists():
                continue
            flagged, gaps = check_frame(fp)
            if flagged:
                any_flag = True
                print(f"  [{name}] t={t:5.1f}s  EDGE-BLEED {flagged}  gaps={gaps}")
    if not any_flag:
        print(f"  [{name}] OK — no content within {MARGIN}px of any edge "
              f"across {n} frames")


if __name__ == "__main__":
    main()

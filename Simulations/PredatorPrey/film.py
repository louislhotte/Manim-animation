"""Assemble the full film: intro card -> rules card -> simulation -> outro card.

Each piece is rendered separately (matplotlib), then concatenated in a single
ffmpeg pass with a short fade to/from black between pieces. All pieces are forced
to 1920x1080 / 30 fps / yuv420p / SAR 1:1 so the concat filter joins them cleanly.
"""

from __future__ import annotations

import os
import subprocess

import cards
import viz
from sim import Simulation


def _fade(dur, fin=0.4, fout=0.4):
    return f"fade=t=in:st=0:d={fin},fade=t=out:st={dur - fout:.2f}:d={fout}"


def build_film(cfg, out_path, workdir, dpi=120, fps=30,
               intro_s=5.0, rules_s=9.0, outro_s=5.0, ffmpeg="ffmpeg"):
    os.makedirs(workdir, exist_ok=True)
    sim_mp4 = os.path.join(workdir, "sim.mp4")
    intro_png = os.path.join(workdir, "intro.png")
    rules_png = os.path.join(workdir, "rules.png")
    outro_png = os.path.join(workdir, "outro.png")

    print("[film] 1/3  rendering simulation ...")
    viz.animate(Simulation(cfg), save=sim_mp4, dpi=dpi, fps=fps)

    print("[film] 2/3  rendering cards ...")
    cards.intro_card(cfg, intro_png, dpi=dpi)
    cards.rules_card(cfg, rules_png, dpi=dpi)
    cards.outro_card(cfg, outro_png, dpi=dpi)

    print("[film] 3/3  stitching with ffmpeg ...")
    sim_s = cfg.max_seconds
    common = f"scale=1920:1080,fps={fps},format=yuv420p,setsar=1"
    filt = (
        f"[0:v]{common},{_fade(intro_s)}[a];"
        f"[1:v]{common},{_fade(rules_s)}[b];"
        f"[2:v]{common},{_fade(sim_s)}[c];"
        f"[3:v]{common},{_fade(outro_s)}[d];"
        f"[a][b][c][d]concat=n=4:v=1:a=0[v]"
    )
    cmd = [
        ffmpeg, "-y", "-loglevel", "error",
        "-loop", "1", "-t", str(intro_s), "-i", intro_png,
        "-loop", "1", "-t", str(rules_s), "-i", rules_png,
        "-i", sim_mp4,
        "-loop", "1", "-t", str(outro_s), "-i", outro_png,
        "-filter_complex", filt, "-map", "[v]",
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(fps),
        "-movflags", "+faststart", out_path,
    ]
    subprocess.run(cmd, check=True)
    total = intro_s + rules_s + sim_s + outro_s
    print(f"[film] done -> {out_path}  (~{total:.0f}s)")
    return out_path

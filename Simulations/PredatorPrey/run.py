#!/usr/bin/env python3
"""Command-line entry point for the predator / prey simulator (Phase 1).

Examples
--------
    python run.py --headless                 # run once, print survival stats
    python run.py --save media/demo.mp4      # render an mp4 of one episode
    python run.py --snapshot media/frame.png # single preview frame
    python run.py --watch                    # live window (needs a display)
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SimConfig  # noqa: E402


def build_config(args) -> SimConfig:
    cfg = SimConfig()
    if args.fish is not None:
        cfg.n_fish = args.fish
    if args.sharks is not None:
        cfg.n_sharks = args.sharks
    if args.size is not None:
        cfg.size = args.size
    if args.seconds is not None:
        cfg.max_seconds = args.seconds
    if args.seed is not None:
        cfg.seed = None if args.seed < 0 else args.seed
    return cfg


def main() -> None:
    p = argparse.ArgumentParser(description="Predator / prey vector simulator")
    p.add_argument("--fish", type=int, help="number of fish")
    p.add_argument("--sharks", type=int, help="number of sharks")
    p.add_argument("--size", type=float, help="tank side length")
    p.add_argument("--seconds", type=float, help="episode length in seconds")
    p.add_argument("--seed", type=int, help="RNG seed (<0 for random)")

    p.add_argument("--film", metavar="PATH",
                   help="render the full bookended film (intro + rules + sim + outro) to PATH")
    p.add_argument("--save", metavar="PATH", help="render just the simulation mp4 to PATH")
    p.add_argument("--snapshot", metavar="PATH", help="save a single preview PNG")
    p.add_argument("--snap-steps", type=int, default=180,
                   help="steps to advance before the snapshot (default 180)")
    p.add_argument("--watch", action="store_true", help="open a live window")
    p.add_argument("--headless", action="store_true",
                   help="run with no rendering and print stats")
    p.add_argument("--fps", type=int, help="frames per second for --save")
    p.add_argument("--dpi", type=int, default=120, help="dpi for --save / --snapshot (120 -> 1080p)")
    args = p.parse_args()

    cfg = build_config(args)

    # Pick a backend before importing viz: Agg unless we actually open a window.
    import matplotlib
    if not args.watch:
        matplotlib.use("Agg")

    from sim import Simulation  # noqa: E402

    if args.headless:
        Simulation(cfg).run(verbose=True)
        return

    import viz  # noqa: E402

    if args.film:
        import tempfile
        from film import build_film
        build_film(cfg, args.film,
                   workdir=tempfile.mkdtemp(prefix="predprey_film_"), dpi=args.dpi)
    if args.snapshot:
        viz.snapshot(Simulation(cfg), args.snap_steps, args.snapshot, dpi=args.dpi)
    if args.save:
        viz.animate(Simulation(cfg), save=args.save, fps=args.fps, dpi=args.dpi)
    if args.watch:
        viz.animate(Simulation(cfg), show=True)

    if not (args.film or args.snapshot or args.save or args.watch):
        # Sensible default: run headless and hint at the render flags.
        Simulation(cfg).run(verbose=True)
        print("tip: --film media/demo.mp4  |  --save (sim only)  |  --watch  |  --snapshot p.png")


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
#
# Render the "Rate Limiting" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=rate_limiting.py
FILM=RateLimiting
SCENES=(Intro Flood Limiter TokenBucket Algorithms Practice Outro)
ALIASES=(bucket=TokenBucket algos=Algorithms)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

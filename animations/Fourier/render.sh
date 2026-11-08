#!/usr/bin/env bash
#
# Render the Fourier / epicycle portrait (path baked from assets/louis.png).
# --quick also uses fewer vectors and a shorter draw; --assets re-traces the path.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=fourier_draw.py
FILM=FourierPortrait
SCENES=(Intro Drawing Theory)
ASSETS=(data/louis_path.npy)
ASSET_SCRIPT=generate_path.py
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

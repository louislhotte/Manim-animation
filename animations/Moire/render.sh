#!/usr/bin/env bash
#
# Render "The Moire of Life" (generative, full-frame pixel field).
# Extra knobs (env): MOIRE_RES (field height px, default 720), MOIRE_FREQ, MOIRE_ZOOM.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=moire_of_life.py
FILM=MoireOfLife
SCENES=(MoireOfLife)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

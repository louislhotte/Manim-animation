#!/usr/bin/env bash
#
# Render the "Ptolemy's Theorem" explainer (the diagonals of a cyclic
# quadrilateral, and why AC·BD = AB·CD + BC·DA).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=ptolemy.py
FILM=""  # `full` stitches SCENES (2D and 3D scenes mixed)
SCENES=(Intro Setup Check Proof Pythagoras Space Recap Outro)
MEDIA_ENV=PTOL_MEDIA_DIR
MEDIA_DEFAULT=/private/tmp/ptol-media  # off OneDrive: HD renders stall there
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

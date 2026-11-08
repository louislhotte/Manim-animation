#!/usr/bin/env bash
#
# Render the "Momentum" explainer (why momentum speeds up gradient descent).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=momentum.py
FILM=""  # `full` stitches SCENES (2D and 3D scenes mixed)
SCENES=(Intro Problem Idea Valley Mechanism Recap Outro)
MEDIA_ENV=MOM_MEDIA_DIR
MEDIA_DEFAULT=/private/tmp/mom-media  # off OneDrive: HD renders stall there
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

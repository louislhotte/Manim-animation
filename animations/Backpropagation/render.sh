#!/usr/bin/env bash
#
# Render the "Backpropagation" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=backprop.py
FILM=""  # `full` stitches SCENES (2D and 3D scenes mixed)
SCENES=(Intro Setup Landscape Descent Backward Power Recap Outro)
ASSETS=(assets/backprop.npz)  # baked by generate_assets.py
MEDIA_ENV=BP_MEDIA_DIR
MEDIA_DEFAULT=/private/tmp/bp-media  # off OneDrive: HD renders stall there
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

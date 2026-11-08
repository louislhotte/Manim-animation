#!/usr/bin/env bash
#
# Render the "Cross-Entropy" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=cross_entropy.py
FILM=""  # `full` stitches SCENES (2D and 3D scenes mixed)
SCENES=(Intro Setup Formula Surprise Gradient Descent Honest Recap Outro)
MEDIA_ENV=XCE_MEDIA_DIR
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

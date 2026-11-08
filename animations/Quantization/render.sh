#!/usr/bin/env bash
#
# Render the "Model Quantization" explainer (a 3D, perpetually-orbiting piece).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=quantization.py
FILM=ModelQuantization
SCENES=(Intro Network Numbers Snap Compare Mapping Payoff Outro)
MEDIA_ENV=QZ_MEDIA_DIR
MEDIA_DEFAULT=/private/tmp/qz-media  # off OneDrive: HD renders stall there
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

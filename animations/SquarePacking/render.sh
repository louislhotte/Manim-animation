#!/usr/bin/env bash
#
# Render "The 17 Squares Problem" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=squarepacking.py
FILM=SeventeenSquares
SCENES=(Intro Problem Record Gap WhyTilt Search Evolution Status Outro)
MEDIA_ENV=SQ_MEDIA_DIR
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

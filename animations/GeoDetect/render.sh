#!/usr/bin/env bash
#
# Render the "Detecting Change From Space" geospatial-detection explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=geodetect.py
FILM=DetectingChangeFromSpace
SCENES=(Intro Signal Deforestation Agriculture Recap Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

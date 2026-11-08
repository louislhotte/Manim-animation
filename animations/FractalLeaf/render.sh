#!/usr/bin/env bash
#
# Render the fractal (Barnsley-style) leaf. Still frame: ./render.sh leafstill -- -s
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=fractal_leaf.py
FILM=FractalLeaf
SCENES=(FractalLeaf)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

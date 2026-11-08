#!/usr/bin/env bash
#
# Render the "Geometry of (a+b)²" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=binomial_square.py
FILM=BinomialSquare
SCENES=(Intro Hook Proof Vary Grid Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

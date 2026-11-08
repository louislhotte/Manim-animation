#!/usr/bin/env bash
#
# Render the "Precision, Recall & F1" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=precision_recall.py
FILM=PrecisionRecallF1
SCENES=(Intro Matrix Precision Recall Tradeoff Recap Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

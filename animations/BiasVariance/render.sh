#!/usr/bin/env bash
#
# Render the Bias–Variance Tradeoff explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=bias_variance.py
FILM=BiasVariance
SCENES=(Intro Setup Underfit JustRight Overfit Tradeoff Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

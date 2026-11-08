#!/usr/bin/env bash
#
# Render "The Immortal Game" chess replay (Anderssen vs. Kieseritzky, 1851).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=chess_immortal.py
FILM=Immortal
SCENES=(Intro Game Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

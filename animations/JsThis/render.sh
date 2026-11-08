#!/usr/bin/env bash
#
# Render the JavaScript `this` explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=js_this.py
FILM=ThisKeyword
SCENES=(Intro Hook DotRule Lost Rules Fix Takeaway Outro)
ALIASES=(dot=DotRule)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

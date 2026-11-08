#!/usr/bin/env bash
#
# Render the "What is Rust?" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=rust.py
FILM=WhatIsRust
SCENES=(Intro Definition Tradeoff Ownership Borrow Dangling Speed Bench World Outro)
MEDIA_ENV=RS_MEDIA_DIR
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

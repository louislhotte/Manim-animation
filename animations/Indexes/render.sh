#!/usr/bin/env bash
#
# Render the "What are indexes?" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=indexes.py
FILM=WhatAreIndexes
SCENES=(Intro Scan IndexIntro Seek Composite Recap Outro)
ALIASES=(index=IndexIntro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

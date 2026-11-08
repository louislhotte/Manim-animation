#!/usr/bin/env bash
#
# Render the OmniDocBench explainer (can AI actually read a document?).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=omnidocbench.py
FILM=OmniDocBenchFilm
SCENES=(Intro Problem Dataset Annotation Contenders Ocr Evaluation Results1 Results2 Takeaway Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

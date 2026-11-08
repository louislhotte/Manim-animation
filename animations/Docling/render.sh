#!/usr/bin/env bash
#
# Render the Docling explainer (chunking + OCR).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=docling_chunking.py
FILM=DoclingFilm
SCENES=(Intro Problem Pipeline Layout OCR Chunk Recap Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

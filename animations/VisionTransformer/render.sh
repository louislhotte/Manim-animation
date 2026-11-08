#!/usr/bin/env bash
#
# Render the Vision Transformers explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=vision_transformer.py
FILM=VisionTransformerFilm
SCENES=(Intro Idea Patchify Embed Encoder Attention Head Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

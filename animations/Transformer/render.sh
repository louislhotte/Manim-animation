#!/usr/bin/env bash
#
# Render the Transformer Inference explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=transformer_inference.py
FILM=TransformerInference
SCENES=(Intro Task Embed Architecture Attention Sample Generate Outro)
ALIASES=(arch=Architecture)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

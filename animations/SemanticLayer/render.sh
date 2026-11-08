#!/usr/bin/env bash
#
# Render the "Semantic Layers" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=semantic_layer.py
FILM=SemanticLayers
SCENES=(Intro Problem Stack WhatIsIt UsedFor Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

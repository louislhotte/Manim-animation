#!/usr/bin/env bash
#
# Render the "What is a Tensor?" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=tensors.py
FILM=WhatIsATensor
SCENES=(Hook Intro Scalar Vector Matrix Higher DataUse Compute Recap Outro)
ALIASES=(data=DataUse)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

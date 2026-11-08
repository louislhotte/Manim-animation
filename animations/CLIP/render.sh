#!/usr/bin/env bash
#
# Render the "What is CLIP?" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=clip.py
FILM=WhatIsCLIP
SCENES=(Intro Problem Encoders Contrast ZeroShot Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

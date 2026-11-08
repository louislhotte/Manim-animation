#!/usr/bin/env bash
#
# Render the "Diffusion Models, Visually" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=diffusion.py
FILM=DiffusionModels
SCENES=(Intro Hook Examples Forward Reverse Steps Prompt Comfy Outro)
ASSETS=(assets/diffusion.npz)  # baked by generate_assets.py
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

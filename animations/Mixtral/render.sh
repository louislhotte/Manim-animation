#!/usr/bin/env bash
#
# Render the Mixtral of Experts explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=mixtral.py
FILM=MixtralFilm
SCENES=(Intro Dense Experts Router WhyTwo Scale Learn Results Recap Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

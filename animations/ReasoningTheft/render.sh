#!/usr/bin/env bash
#
# Render the "Stealing a Model's Reasoning" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=reasoning_theft.py
FILM=StealingReasoning
SCENES=(Intro CoT Lockbox OneKey BankShot Harvest Distill Fix Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

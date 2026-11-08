#!/usr/bin/env bash
#
# Render the Harness Engineering explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=harness_engineering.py
FILM=HarnessEngineering
SCENES=(Intro What Prompt Context Harness Pipeline Why Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

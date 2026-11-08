#!/usr/bin/env bash
#
# Render the "LangGraph" explainer (orchestrating a team of agents).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=langgraph.py
FILM=LangGraphFilm
SCENES=(Intro Problem Graph Team Parallel Takeaway Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

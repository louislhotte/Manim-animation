#!/usr/bin/env bash
#
# Render the Unit Tests explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=unit_tests.py
FILM=UnitTestsFilm
SCENES=(Intro Unit Anatomy Assertion Edges Net Recap Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

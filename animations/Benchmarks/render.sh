#!/usr/bin/env bash
#
# Render the "How AI Benchmarks Work" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=benchmarks.py
FILM=AIBenchmarks
SCENES=(Intro Whatis Tour Grading SweBench PassK Arena Progress Catch Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

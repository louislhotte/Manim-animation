#!/usr/bin/env bash
#
# Render the Jacobian Conjecture explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=jacobian_conjecture.py
FILM=JacobianConjecture
SCENES=(Hook Intro Conjecture Intuition Counterexample Collision Significance Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

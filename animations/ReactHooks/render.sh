#!/usr/bin/env bash
#
# Render the "React Hooks & useEffect" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=react_hooks.py
FILM=ReactHooks
SCENES=(Intro Hooks State SideEffects Anatomy Example Cycle Recap Outro)
ALIASES=(effects=SideEffects)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

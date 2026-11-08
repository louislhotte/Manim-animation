#!/usr/bin/env bash
#
# Render the "IntersectionObserver in React" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=intersection_observer.py
FILM=IntersectionObserverReact
SCENES=(Intro Problem Idea Api Count Recap Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

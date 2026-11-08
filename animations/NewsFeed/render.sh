#!/usr/bin/env bash
#
# Render the "Designing the News Feed" explainer (push / pull fan-out).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=newsfeed.py
FILM=NewsFeed
SCENES=(Intro Feed Push Celebrity Hybrid Architecture Recap Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

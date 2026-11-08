#!/usr/bin/env bash
#
# Render the KV Cache explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=kv_cache.py
FILM=KVCacheFilm
SCENES=(Intro Waste Reuse Cache Phases Memory Shrink Recap Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

#!/usr/bin/env bash
#
# Render the "PubTables-1M" paper explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=pubtables.py
FILM=PubTables1M
SCENES=(Intro Paper Tasks Scale Canonical ModelResults Outro)
ALIASES=(model=ModelResults)
MEDIA_ENV=PT_MEDIA_DIR
MEDIA_DEFAULT=/private/tmp/pt-media  # off OneDrive: HD renders stall there
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

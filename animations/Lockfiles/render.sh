#!/usr/bin/env bash
#
# Render the Lockfiles explainer (package.json vs package-lock.json).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=lockfiles.py
FILM=LockfilesFilm
SCENES=(Intro Manifest Ranges Lockfile Repro Pattern Recap Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

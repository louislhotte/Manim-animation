#!/usr/bin/env bash
#
# Render the "Git & GitHub, Visually" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=git_github.py
FILM=GitHubExplained
SCENES=(Intro Overview Commit Push Branch Merge CherryPick Collab Outro)
ALIASES=(cherry=CherryPick cherry-pick=CherryPick)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

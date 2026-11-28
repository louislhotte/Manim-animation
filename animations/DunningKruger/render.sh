#!/usr/bin/env bash
#
# Render "The Dunning-Kruger Effect" (flat scenes, stitched).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
# The film is cut to its recorded voice (narration/voice.json) and reads without
# sound too (one short caption per beat). This renders the pictures; the narrated
# file is made by narration/place.py (see README.md, "The voice"). DK_VOICE=0 paces
# the film for a reader instead.
#
# Nothing is baked or downloaded: the pictures are drawn from model.py (a toy model
# of a light in a dark field, and one real four-move chess game).
#
FILE=dunning_kruger.py
FILM=""  # `full` stitches SCENES
SCENES=(Intro Move Light Climb Expert Everyone Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

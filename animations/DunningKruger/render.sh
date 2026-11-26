#!/usr/bin/env bash
#
# Render "The Dunning-Kruger Effect" (flat scenes, stitched).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
# The film is made to be narrated, and reads without the voice too (one short
# caption per beat). For the timed voice-over script, render with MX_TRACE_DIR set
# and run tools/voiceover.py (see README.md).
#
# Nothing is baked or downloaded: the pictures are drawn from model.py (a toy model
# of a light in a dark field, and one real four-move chess game).
#
FILE=dunning_kruger.py
FILM=""  # `full` stitches SCENES
SCENES=(Intro Move Light Climb Expert Everyone Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

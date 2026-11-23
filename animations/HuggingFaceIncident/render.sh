#!/usr/bin/env bash
#
# Render "The Hugging Face Incident" (flat scenes, stitched).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
# The film is made to be narrated. To get the timed voice-over script, render with
# MX_TRACE_DIR set and run tools/voiceover.py (see README.md).
#
# Nothing is baked, downloaded or executed: every date, number and quotation is in
# facts.py, copied from OpenAI's post of 26 August 2026.
#
FILE=incident.py
FILM=""  # `full` stitches SCENES
SCENES=(Intro Note WayOut Tasks BreakIn Nothing Warning Outro)
MEDIA_ENV=HFI_MEDIA_DIR
MEDIA_DEFAULT=/private/tmp/hfincident-media  # off OneDrive: HD renders stall there
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

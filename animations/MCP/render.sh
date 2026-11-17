#!/usr/bin/env bash
#
# Render the "MCP" explainer (flat scenes, stitched: every scene opens on the last
# frame of the one before it, so the cuts between clips do not show).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
# The film is made to be narrated. To get the timed voice-over script, render with
# MX_TRACE_DIR set and run tools/voiceover.py (see README.md).
#
# Nothing is baked and nothing is downloaded: the messages on screen are written
# from the MCP specification in wire.py, which checks them when it is imported.
#
FILE=mcp_film.py
FILM=""  # `full` stitches SCENES
SCENES=(Intro Alone Protocol Call Doors Anywhere Trust Recap Outro)
MEDIA_ENV=MCP_MEDIA_DIR
MEDIA_DEFAULT=/private/tmp/mcp-media  # off OneDrive: HD renders stall there
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

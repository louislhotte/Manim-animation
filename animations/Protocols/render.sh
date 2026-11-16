#!/usr/bin/env bash
#
# Render the "TCP, HTTP, HTTPS" explainer (flat scenes, stitched).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
# The film is made to be narrated. To get the timed voice-over script, render with
# MX_TRACE_DIR set and run tools/voiceover.py (see README.md).
#
# The baked assets are committed. Re-baking them (--assets) runs the film's
# laboratory on the loopback interface (no network access) and needs the openssl
# command line; the map picture also needs the MIP film's assets.
#
FILE=protocols.py
FILM=""  # `full` stitches SCENES
SCENES=(Intro Request Packets Connect Stream Http Tap Sealed Servers Stack Outro)
ASSETS=(assets/story.json assets/course_map.ppm assets/world.json)
ASSET_SCRIPT=generate_assets.py
MEDIA_ENV=NET_MEDIA_DIR
export MX_EDGE_THRESH="${MX_EDGE_THRESH:-70}"  # --check: the dim world map may touch the edges, text may not
MEDIA_DEFAULT=/private/tmp/protocols-media  # off OneDrive: HD renders stall there
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

#!/usr/bin/env bash
#
# Render the "Mixed-Integer Programming" explainer (flat scenes and scenes on a 3D
# map of Paris, stitched).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
# The film is made to be narrated. To get the timed voice-over script, render with
# MX_TRACE_DIR set and run tools/voiceover.py (see README.md).
#
# The baked assets are committed. Re-baking them (--assets) needs the cached
# OpenStreetMap answers (osm.py fetches them) and gurobipy.
#
FILE=mip.py
FILM=""  # `full` stitches SCENES (flat and 3D scenes mixed)
SCENES=(Intro Night Hour Model Relax Branch Solver City Outro)
ASSETS=(assets/paris.npz assets/story.json assets/gurobi_course.txt assets/gurobi_district.txt)
ASSET_SCRIPT=generate_assets.py
MEDIA_ENV=MIP_MEDIA_DIR
export MX_EDGE_THRESH="${MX_EDGE_THRESH:-150}"  # --check: the map may touch the edges, text may not
MEDIA_DEFAULT=/private/tmp/mip-media  # off OneDrive: HD renders stall there
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

#!/usr/bin/env bash
#
# Render the "What is Next.js?" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=nextjs.py
FILM=WhatIsNextJS
SCENES=(Intro Problem Definition ServerComponents ApiRoutes RenderModes FullStack Outro)
ALIASES=(server=ServerComponents api=ApiRoutes modes=RenderModes)
MEDIA_ENV=NX_MEDIA_DIR
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

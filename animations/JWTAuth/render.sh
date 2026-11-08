#!/usr/bin/env bash
#
# Render the JWT Authentication explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=jwt_auth.py
FILM=JWTAuthFilm
SCENES=(Intro Problem Idea Anatomy Sign Flow Catch Recap Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

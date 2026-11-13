#!/usr/bin/env bash
#
# Render the "Terraform" explainer (2D scenes and scenes on a 3D stage, stitched).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
# The film is made to be narrated. To get the timed voice-over script, render with
# MX_TRACE_DIR set and run tools/voiceover.py (see README.md).
#
FILE=terraform.py
FILM=""  # `full` stitches SCENES (2D and 3D scenes mixed)
SCENES=(Intro Apply Blocks Graph Plan Change Drift Team Envs Outro)
MEDIA_ENV=TF_MEDIA_DIR
MEDIA_DEFAULT=/private/tmp/terraform-media  # off OneDrive: HD renders stall there
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

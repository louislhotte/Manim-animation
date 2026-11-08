#!/usr/bin/env bash
#
# Render the "What is an ALB?" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=alb.py
FILM=WhatIsAnALB
SCENES=(Intro FrontDoor Anatomy Routing Health Layers Scale Outro)
MEDIA_ENV=ALB_MEDIA_DIR
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

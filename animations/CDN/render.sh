#!/usr/bin/env bash
#
# Render the "Content Delivery Networks" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=cdn.py
FILM=CDN
SCENES=(Intro Problem Idea HowItWorks UseCases Outro)
ALIASES=(how=HowItWorks use=UseCases)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

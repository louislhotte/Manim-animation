#!/usr/bin/env bash
#
# Render the "How QR Codes Work" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=qr_code.py
FILM=QRCodes
SCENES=(Intro Hook Encode Anatomy Placement Robustness Outro)
ALIASES=(robust=Robustness)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

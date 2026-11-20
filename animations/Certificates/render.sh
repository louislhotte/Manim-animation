#!/usr/bin/env bash
#
# Render the "Certificates" explainer (flat scenes, stitched).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
# The film is made to be narrated. To get the timed voice-over script, render with
# MX_TRACE_DIR set and run tools/voiceover.py (see README.md).
#
# Nothing is baked and nothing is downloaded: the certificates on screen are an
# illustration written in facts.py, which computes their fingerprints (SHA-256).
#
FILE=certificates.py
FILM=""  # `full` stitches SCENES
SCENES=(Intro Claim Seal Chain Checks Outro)
MEDIA_ENV=CERT_MEDIA_DIR
MEDIA_DEFAULT=/private/tmp/certificates-media  # off OneDrive: HD renders stall there
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

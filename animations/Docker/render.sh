#!/usr/bin/env bash
#
# Render the "Docker, Visually" explainer (a 3D, camera-orbiting piece).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=docker.py
FILM=DockerVisually
SCENES=(Intro Problem Container Layers Commands Network VMs Kube Outro)
MEDIA_ENV=DK_MEDIA_DIR
MEDIA_DEFAULT=/private/tmp/dk-media  # off OneDrive: HD renders stall there
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

#!/usr/bin/env bash
#
# Render the "What is a GAN?" explainer (a dynamic 3-D, orbiting piece).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=gan.py
FILM=WhatIsAGAN
SCENES=(Intro Goal Players Generator Discriminator Game Convergence Outro)
ASSETS=(assets/gan.npz)  # baked by generate_assets.py
MEDIA_ENV=GAN_MEDIA_DIR
MEDIA_DEFAULT=/private/tmp/gan-media  # off OneDrive: HD renders stall there
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

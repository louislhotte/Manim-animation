#!/usr/bin/env bash
#
# Render the Embeddings & Retrieval explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=embedding_retrieval.py
FILM=EmbeddingRetrieval
SCENES=(Intro Problem Embed Space Retrieve Systems Why Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

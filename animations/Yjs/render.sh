#!/usr/bin/env bash
#
# Render the "Yjs & CRDTs" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
# The film's numbers are baked from real runs (Yjs, Tiptap, Hocuspocus, a real
# editing trace) into assets/*.json by generate_assets.py: `./render.sh --assets`
# re-bakes them (needs node >= 22, npm and network; a minute or two).
#
FILE=yjs.py
FILM=YjsFilm
SCENES=(Intro Together Positions Items SameSpot Offline AnyOrder Numbers Stack Outro)
ASSETS=(assets/story.json assets/stack.json assets/bench.json assets/npm.json)
MEDIA_ENV=YJ_MEDIA_DIR
MEDIA_DEFAULT=/private/tmp/yjs-media
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

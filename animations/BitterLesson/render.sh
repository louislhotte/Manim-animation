#!/usr/bin/env bash
#
# Render the Bitter Lesson explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=bitter_lesson.py
FILM=BitterLessonFilm
SCENES=(Intro Roads Moore Pattern Scale Lesson Recap Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

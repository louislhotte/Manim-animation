#!/usr/bin/env bash
#
# Render the "LLM-as-a-Judge" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=llm_judge.py
FILM=LLMAsJudge
SCENES=(Intro Gap Idea Prompt Evaluators Pipeline Limits Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

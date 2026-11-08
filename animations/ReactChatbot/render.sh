#!/usr/bin/env bash
#
# Render the React.js & System-Design explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=react_chatbot.py
FILM=ReactChatbot
SCENES=(Intro WhatIs Components Reconcile UsedFor Architecture Flows Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

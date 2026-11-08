#!/usr/bin/env bash
#
# Render the "Amazon ElastiCache" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=elasticache.py
FILM=HowElastiCacheWorks
SCENES=(Intro Problem Memory CacheAside Payoff Eviction Service Outro)
MEDIA_ENV=EC_MEDIA_DIR
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

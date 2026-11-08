#!/usr/bin/env bash
#
# Render the "Kubernetes & Continuous Delivery" explainer.
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=kubernetes_cd.py
FILM=KubernetesCD
SCENES=(Intro Why Containers Cluster Replicas Pipeline Checklist Outro)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

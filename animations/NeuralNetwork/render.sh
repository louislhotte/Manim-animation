#!/usr/bin/env bash
#
# Render "How a Neural Network Learns" (five scene files + one full-film file).
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=neural_network.py
FILM=NeuralNetworkLearns
SCENES=(scene1_task.py:Task scene2_arch.py:Arch scene3_train.py:Train scene4_tune.py:Tune scene5_verdict.py:Verdict)
ASSETS=(assets/nn_learn.npz assets/grid_large.png)  # baked by generate_assets.py
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

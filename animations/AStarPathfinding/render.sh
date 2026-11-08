#!/usr/bin/env bash
#
# Render the A* Pathfinding (Manhattan street map) explainer.
# The 3D perspective-city variant lives in astar_city.py: ./render.sh city
#
# ./render.sh [SCENE] [-q l|m|h|k] [--quick] [--check] [--stitch] [--list] [-p]
# Everything else (shared venv, scene lookup, stitching, --check) lives in
# tools/render_lib.sh: run ./render.sh --help for all options.
#
FILE=astar_pathfinding.py
FILM=AStarPathfinding
SCENES=(Intro MapIntro Search Explain FinalPath Outro)
ALIASES=(map=MapIntro final=FinalPath city=astar_city.py:AStarCity examples=astar_city.py:MoreExamples city-still=astar_city.py:CityStill)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"

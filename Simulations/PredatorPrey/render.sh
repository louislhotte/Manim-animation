#!/usr/bin/env bash
#
# Run / render the predator-prey simulator.
#
# On first run it bootstraps a local virtualenv (.venv) with numpy + matplotlib,
# then runs the simulator. Subsequent runs reuse the venv. This module has NO
# manim / LaTeX dependency — it is a standalone matplotlib simulation.
#
# Usage:
#   ./render.sh                      # build the full film -> media/demo.mp4 (default)
#   ./render.sh --film out.mp4       # full film (intro + rules + sim + outro)
#   ./render.sh --save out.mp4       # just the simulation (no cards)
#   ./render.sh --headless           # run once, print survival stats
#   ./render.sh --snapshot media/frame.png
#   ./render.sh --watch              # live window (needs a display)
#   ./render.sh --save out.mp4 --seconds 40 --sharks 2
#   ./render.sh --reinstall          # rebuild the venv from scratch
#
# Any flags are passed straight through to run.py (see: ./render.sh --help-run).
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"
PY="$VENV/bin/python"

if [ "${1:-}" = "--reinstall" ]; then
  rm -rf "$VENV"
  shift
fi

if [ ! -x "$PY" ]; then
  echo ">> bootstrapping virtualenv (.venv) ..."
  python3 -m venv "$VENV"
  "$PY" -m pip install -q --upgrade pip
  "$PY" -m pip install -q -r "$ROOT/requirements.txt"
fi

if [ "${1:-}" = "--help-run" ]; then
  exec "$PY" "$ROOT/run.py" --help
fi

if [ $# -eq 0 ]; then
  # Build the full bookended film (intro + rules + sim + outro) to a local temp
  # file first: writing the mp4 straight into a synced OneDrive folder is heavily
  # I/O-bound (minutes of stalls). Then move the finished file in.
  mkdir -p "$ROOT/media"
  TMP="${TMPDIR:-/tmp}/predprey_demo_$$.mp4"
  "$PY" "$ROOT/run.py" --film "$TMP"
  mv -f "$TMP" "$ROOT/media/demo.mp4"
  echo "saved $ROOT/media/demo.mp4"
  exit 0
fi

exec "$PY" "$ROOT/run.py" "$@"

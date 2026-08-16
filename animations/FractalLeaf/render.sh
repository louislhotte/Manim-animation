#!/usr/bin/env bash
#
# Render the Fractal Leaf animation.
#
# It reuses the manim environment that already exists in the repo (the CNN
# series' .venv) so there's nothing to install.  If that venv is missing it
# bootstraps a local .venv from requirements.txt instead.
#
# Usage:
#   ./render.sh [SCENE] [-q l|m|h|k] [-p] [-s] [--no-cache] [--reinstall]
#
#   SCENE   FractalLeaf (default, the full animation) or LeafStill (one frame)
#   -q      Quality: l=480p15 (default, fast), m=720p30, h=1080p60, k=2160p60
#   -p      Preview: open the output when done
#   -s      Save the last frame as a PNG instead of a video (use with LeafStill)
#   --no-cache    Force a full re-render
#   --reinstall   Recreate the local .venv from scratch
#
# Examples:
#   ./render.sh                 # full animation, low quality — good for iterating
#   ./render.sh -p              # ... and open it when done
#   ./render.sh LeafStill -s    # a quick still to eyeball the shape
#   ./render.sh -q h -p         # full animation in 1080p
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_VENV="$ROOT/.venv"
# The CNN series ships a working manim 0.18.1 venv — reuse it if present.
CNN_VENV="$ROOT/../Convolutional-Neural-Networks-main/Convolutional-Neural-Networks-main/.venv"

# ---- defaults ------------------------------------------------------------- #
SCENE="FractalLeaf"
QUALITY="l"
PREVIEW=""
STILL=""
NOCACHE=""
REINSTALL=0

# ---- argument parsing ----------------------------------------------------- #
while [ $# -gt 0 ]; do
  case "$1" in
    -q) QUALITY="${2:?-q needs a value: l|m|h|k}"; shift 2 ;;
    -p) PREVIEW="-p"; shift ;;
    -s) STILL="-s"; shift ;;
    --no-cache) NOCACHE="--disable_caching"; shift ;;
    --reinstall) REINSTALL=1; shift ;;
    -h|--help) sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "Unknown option: $1" >&2; exit 2 ;;
    *) SCENE="$1"; shift ;;
  esac
done

case "$QUALITY" in
  l) QFLAG="-ql" ;;
  m) QFLAG="-qm" ;;
  h) QFLAG="-qh" ;;
  k) QFLAG="-qk" ;;
  *) echo "Invalid quality '$QUALITY' (use l|m|h|k)" >&2; exit 2 ;;
esac

# ---- pick / bootstrap an interpreter with manim --------------------------- #
if [ "$REINSTALL" -eq 1 ]; then rm -rf "$LOCAL_VENV"; fi

PY=""
if [ -x "$LOCAL_VENV/bin/python" ] && "$LOCAL_VENV/bin/python" -c "import manim" 2>/dev/null; then
  PY="$LOCAL_VENV/bin/python"
elif [ -x "$CNN_VENV/bin/python" ] && "$CNN_VENV/bin/python" -c "import manim" 2>/dev/null; then
  PY="$CNN_VENV/bin/python"
  echo ">> Reusing the CNN series' manim venv"
else
  echo ">> No manim venv found — bootstrapping $LOCAL_VENV"
  PYBOOT="$(command -v python3.12 || command -v python3)"
  "$PYBOOT" -m venv "$LOCAL_VENV"
  "$LOCAL_VENV/bin/python" -m pip install --upgrade pip >/dev/null
  "$LOCAL_VENV/bin/python" -m pip install -r "$ROOT/requirements.txt"
  PY="$LOCAL_VENV/bin/python"
fi

# ---- render --------------------------------------------------------------- #
echo ">> Rendering $SCENE ($QFLAG)"
( cd "$ROOT" && "$PY" -m manim $QFLAG $PREVIEW $STILL $NOCACHE fractal_leaf.py "$SCENE" )
echo ">> Done. Output is under $ROOT/media/"

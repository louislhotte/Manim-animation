#!/usr/bin/env bash
#
# Render the Fourier / epicycle portrait animation.
#
# On first run it bootstraps a local virtualenv (.venv), installs the pinned
# dependencies and (re)generates the drawing path from assets/louis.png, then
# renders the requested scene. Subsequent runs reuse the venv.
#
# If a Manim venv already exists elsewhere in the repo (the CNN series' .venv),
# it is reused automatically so we don't reinstall Manim.
#
# Usage:
#   ./render.sh [SCENE] [-q l|m|h|k] [-p] [--quick] [--no-cache] [--skip-assets] [--reinstall]
#
#   SCENE   FourierPortrait (default, the full film) | Intro | Drawing | Theory
#   -q      Quality: l=480p15 (default, fast), m=720p30, h=1080p60, k=2160p60
#   -p      Preview: open the clip when it finishes
#   --quick        Fewer vectors + shorter draw time (fast sanity render)
#   --no-cache     Force a full re-render
#   --skip-assets  Do not regenerate the path (use the existing data/louis_path.npy)
#   --reinstall    Recreate the local venv from scratch
#
# Examples:
#   ./render.sh Drawing --quick        # fast check of just the drawing
#   ./render.sh                        # the whole film, low quality
#   ./render.sh FourierPortrait -q h   # final 1080p render
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"
CNN_VENV="$ROOT/../Convolutional-Neural-Networks-main/Convolutional-Neural-Networks-main/.venv"
MEDIA_DIR="$ROOT/media"

SCENE="FourierPortrait"
QUALITY="l"
PREVIEW=""
SKIP_ASSETS=0
REINSTALL=0
NOCACHE=""
export FOURIER_QUICK="${FOURIER_QUICK:-0}"

while [ $# -gt 0 ]; do
  case "$1" in
    -q) QUALITY="${2:?-q needs a value: l|m|h|k}"; shift 2 ;;
    -p) PREVIEW="-p"; shift ;;
    --quick) FOURIER_QUICK=1; shift ;;
    --no-cache) NOCACHE="--disable_caching"; shift ;;
    --skip-assets) SKIP_ASSETS=1; shift ;;
    --reinstall) REINSTALL=1; shift ;;
    -h|--help) sed -n '2,28p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
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

# ---- pick / bootstrap an interpreter with Manim --------------------------- #
if [ "$REINSTALL" -eq 1 ]; then rm -rf "$VENV"; fi

PY=""
if [ -x "$VENV/bin/python" ]; then
  PY="$VENV/bin/python"
elif [ -x "$CNN_VENV/bin/python" ] && "$CNN_VENV/bin/python" -c "import manim" >/dev/null 2>&1; then
  echo ">> Reusing existing Manim venv: $CNN_VENV"
  PY="$CNN_VENV/bin/python"
fi

if [ -z "$PY" ]; then
  echo ">> Creating virtualenv (.venv)"
  PYBOOT="$(command -v python3.12 || command -v python3)"
  "$PYBOOT" -m venv "$VENV"
  PY="$VENV/bin/python"
fi

if ! "$PY" -c "import manim" >/dev/null 2>&1; then
  echo ">> Installing dependencies from requirements.txt"
  "$PY" -m pip install --upgrade pip >/dev/null
  "$PY" -m pip install -r "$ROOT/requirements.txt"
fi

# ---- (re)generate the drawing path ---------------------------------------- #
if [ "$SKIP_ASSETS" -eq 0 ]; then
  echo ">> Generating drawing path from assets/louis.png"
  "$PY" "$ROOT/generate_path.py"
fi

# ---- render --------------------------------------------------------------- #
export FOURIER_QUICK
echo ""
echo ">> Rendering $SCENE  ($QFLAG, quick=$FOURIER_QUICK)"
( cd "$ROOT" && "$PY" -m manim $QFLAG $PREVIEW $NOCACHE --media_dir "$MEDIA_DIR" fourier_draw.py "$SCENE" )

echo ""
echo ">> Done. Video is under: $MEDIA_DIR/videos/fourier_draw/<quality>/"

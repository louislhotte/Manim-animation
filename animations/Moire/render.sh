#!/usr/bin/env bash
#
# Render "Moiré of Life" — two rotating sine-wave grids whose interference
# blooms into swirling mandalas, then a dive into the centre that dissolves the
# macro-pattern back into the bare micro sine waves.
#
# On first run it reuses an existing Manim venv from a sibling series
# (HarnessEngineering / Fourier / CNN); if none exists it bootstraps a local
# .venv from requirements.txt. Only numpy + Pillow are needed on top of Manim.
#
# Usage:
#   ./render.sh [-q l|m|h|k] [-p] [--quick] [--no-cache] [--reinstall]
#
#   -q      Quality: l=480p15 (default, fast), m=720p30, h=1080p60, k=2160p60
#   -p      Preview: open the clip when it finishes
#   --quick        Compress every beat (MOIRE_QUICK=1) for a fast sanity check
#   --no-cache     Force a full re-render
#   --reinstall    Recreate the local venv from scratch
#
# The field resolution auto-scales with quality; override with MOIRE_RES.
# Other knobs: MOIRE_FREQ (grid density), MOIRE_ZOOM (final magnification).
#
# Examples:
#   ./render.sh --quick            # ~15s low-res sanity check
#   ./render.sh -q m               # 720p
#   ./render.sh -q h -p            # 1080p60 final, then open it
#   MOIRE_FREQ=60 MOIRE_ZOOM=48 ./render.sh -q m   # denser, deeper dive
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"
HARNESS_VENV="$ROOT/../HarnessEngineering/.venv"
FOURIER_VENV="$ROOT/../Fourier/.venv"
CNN_VENV="$ROOT/../CNN/.venv"
MEDIA_DIR="$ROOT/media"
FILE="moire_of_life.py"
KLASS="MoireOfLife"

QUALITY="l"
PREVIEW=""
REINSTALL=0
NOCACHE=""
export MOIRE_QUICK="${MOIRE_QUICK:-0}"

while [ $# -gt 0 ]; do
  case "$1" in
    -q) QUALITY="${2:?-q needs a value: l|m|h|k}"; shift 2 ;;
    -p) PREVIEW="-p"; shift ;;
    --quick) MOIRE_QUICK=1; shift ;;
    --no-cache) NOCACHE="--disable_caching"; shift ;;
    --reinstall) REINSTALL=1; shift ;;
    -h|--help) sed -n '2,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "Unknown option: $1" >&2; exit 2 ;;
    *) echo "Unexpected argument: $1" >&2; exit 2 ;;
  esac
done

case "$QUALITY" in
  l) QFLAG="-ql"; RESDIR="480p15";  DEF_RES=480 ;;
  m) QFLAG="-qm"; RESDIR="720p30";  DEF_RES=720 ;;
  h) QFLAG="-qh"; RESDIR="1080p60"; DEF_RES=1080 ;;
  k) QFLAG="-qk"; RESDIR="2160p60"; DEF_RES=1440 ;;   # field capped; upscaled clean
  *) echo "Invalid quality '$QUALITY' (use l|m|h|k)" >&2; exit 2 ;;
esac

# Field resolution follows quality unless the caller pinned MOIRE_RES.
export MOIRE_RES="${MOIRE_RES:-$DEF_RES}"

# ---- pick / bootstrap an interpreter with Manim --------------------------- #
if [ "$REINSTALL" -eq 1 ]; then rm -rf "$VENV"; fi

PY=""
if [ -x "$VENV/bin/python" ]; then
  PY="$VENV/bin/python"
else
  for CAND in "$HARNESS_VENV" "$FOURIER_VENV" "$CNN_VENV"; do
    if [ -x "$CAND/bin/python" ] && "$CAND/bin/python" -c "import manim" >/dev/null 2>&1; then
      echo ">> Reusing existing Manim venv: $CAND"
      PY="$CAND/bin/python"
      break
    fi
  done
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

export MOIRE_QUICK MOIRE_RES

# ---- render --------------------------------------------------------------- #
echo ""
echo ">> Rendering $KLASS  ($QFLAG, res=${MOIRE_RES}, quick=${MOIRE_QUICK})"
( cd "$ROOT" && "$PY" -m manim $QFLAG $PREVIEW $NOCACHE --media_dir "$MEDIA_DIR" "$FILE" "$KLASS" )

echo ""
echo ">> Done. Video under: $MEDIA_DIR/videos/${FILE%.py}/$RESDIR/$KLASS.mp4"

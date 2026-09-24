#!/usr/bin/env bash
#
# Render the "Backpropagation" explainer.
#
# On first run it reuses an existing Manim venv elsewhere in the repo (the
# HarnessEngineering / CNN / Fourier series' .venv) so Manim isn't reinstalled;
# otherwise it bootstraps a local .venv from requirements.txt. The real numbers
# behind the film (loss surface, descent paths, the tiny net's forward/backward
# values, the cost comparison) are baked into assets/backprop.npz by
# generate_assets.py, which this script runs automatically if the file is
# missing (or when you pass --assets).
#
# Usage:
#   ./render.sh [SCENE] [-q l|m|h|k] [-p] [--quick] [--stitch] [--assets] [--no-cache] [--reinstall]
#
#   SCENE   full (default, the whole film, stitched) | intro | setup | landscape
#             | descent | backward | power | recap | outro
#   -q      Quality: l=480p15 (default, fast), m=720p30, h=1080p60, k=2160p60
#   -p      Preview: open the clip when it finishes
#   --quick        Shorten the on-screen holds (BP_QUICK=1) for a fast test
#   --stitch       Render every section scene and join them into one film
#   --assets       Force a re-bake of assets/backprop.npz before rendering
#   --no-cache     Force a full re-render
#   --reinstall    Recreate the local venv from scratch
#
# Examples:
#   ./render.sh landscape --quick     # fast sanity check of one scene
#   ./render.sh                       # the whole film, 480p
#   ./render.sh full -q h             # final 1080p render
#   ./render.sh --stitch -q m         # render each section and stitch (720p)
#
# Note: the repo lives on a OneDrive-synced path, and writing Manim's many
# partial-movie files there stalls for minutes on OneDrive I/O — especially for
# the render-heavy 3D scenes. So MEDIA_DIR defaults to /private/tmp/bp-media;
# override with BP_MEDIA_DIR=... and copy the final mp4 back yourself.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"
HARNESS_VENV="$ROOT/../HarnessEngineering/.venv"
FOURIER_VENV="$ROOT/../Fourier/.venv"
CNN_VENV="$ROOT/../CNN/.venv"
MEDIA_DIR="${BP_MEDIA_DIR:-/private/tmp/bp-media}"
FILE="backprop.py"

SCENE="full"
QUALITY="l"
PREVIEW=""
STITCH=0
ASSETS=0
REINSTALL=0
NOCACHE=""
export BP_QUICK="${BP_QUICK:-0}"

while [ $# -gt 0 ]; do
  case "$1" in
    -q) QUALITY="${2:?-q needs a value: l|m|h|k}"; shift 2 ;;
    -p) PREVIEW="-p"; shift ;;
    --quick) BP_QUICK=1; shift ;;
    --stitch) STITCH=1; shift ;;
    --assets) ASSETS=1; shift ;;
    --no-cache) NOCACHE="--disable_caching"; shift ;;
    --reinstall) REINSTALL=1; shift ;;
    -h|--help) sed -n '2,34p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "Unknown option: $1" >&2; exit 2 ;;
    *) SCENE="$1"; shift ;;
  esac
done

case "$QUALITY" in
  l) QFLAG="-ql"; RESDIR="480p15" ;;
  m) QFLAG="-qm"; RESDIR="720p30" ;;
  h) QFLAG="-qh"; RESDIR="1080p60" ;;
  k) QFLAG="-qk"; RESDIR="2160p60" ;;
  *) echo "Invalid quality '$QUALITY' (use l|m|h|k)" >&2; exit 2 ;;
esac

# ---- scene name -> Manim class -------------------------------------------- #
scene_class() {
  case "$1" in
    intro)     echo "Intro" ;;
    setup)     echo "Setup" ;;
    landscape) echo "Landscape" ;;
    descent)   echo "Descent" ;;
    backward)  echo "Backward" ;;
    power)     echo "Power" ;;
    recap)     echo "Recap" ;;
    outro)     echo "Outro" ;;
    *) return 1 ;;
  esac
}

# The whole film mixes 2D (Scene) and 3D (ThreeDScene) classes, so there is no
# single all-in-one class: "full" renders every section and stitches them.
if [ "$SCENE" = "full" ]; then STITCH=1; fi

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

# ---- bake the real numbers if needed -------------------------------------- #
if [ "$ASSETS" -eq 1 ] || [ ! -f "$ROOT/assets/backprop.npz" ]; then
  echo ">> Baking real assets (assets/backprop.npz)"
  ( cd "$ROOT" && "$PY" generate_assets.py )
fi

export BP_QUICK

# ---- render --------------------------------------------------------------- #
render_one() {
  local klass="$1"
  echo ""
  echo ">> Rendering $klass  ($QFLAG, quick=$BP_QUICK)"
  ( cd "$ROOT" && "$PY" -m manim $QFLAG $PREVIEW $NOCACHE --media_dir "$MEDIA_DIR" "$FILE" "$klass" )
}

if [ "$STITCH" -eq 1 ]; then
  ORDER=(Intro Setup Landscape Descent Backward Power Recap Outro)
  OUTPUTS=()
  for klass in "${ORDER[@]}"; do
    render_one "$klass"
    OUTPUTS+=("$MEDIA_DIR/videos/${FILE%.py}/$RESDIR/$klass.mp4")
  done
  FULL="$MEDIA_DIR/Backpropagation_${RESDIR}.mp4"
  LIST="$(mktemp)"
  for f in "${OUTPUTS[@]}"; do printf "file '%s'\n" "$f" >> "$LIST"; done
  echo ""
  echo ">> Stitching ${#OUTPUTS[@]} clips -> $FULL"
  if ! ffmpeg -y -loglevel error -f concat -safe 0 -i "$LIST" -c copy "$FULL"; then
    echo "   (stream copy failed — re-encoding)"
    ffmpeg -y -loglevel error -f concat -safe 0 -i "$LIST" -c:v libx264 -pix_fmt yuv420p "$FULL"
  fi
  rm -f "$LIST"
  echo ">> Full video: $FULL"
else
  KLASS="$(scene_class "$SCENE")" || { echo "Unknown scene '$SCENE'" >&2; exit 2; }
  render_one "$KLASS"
  echo ""
  echo ">> Done. Video under: $MEDIA_DIR/videos/${FILE%.py}/$RESDIR/$KLASS.mp4"
fi

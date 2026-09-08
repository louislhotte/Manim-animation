#!/usr/bin/env bash
#
# Render the "How a Neural Network Learns" explainer (car / plane / ship).
#
# On first run it bootstraps (or reuses a sibling) Manim venv, generates the
# real dataset + trained-model assets (assets/nn_learn.npz + correctness PNGs),
# then renders the requested scene. Subsequent runs reuse both.
#
# Usage:
#   ./render.sh [SCENE] [-q l|m|h|k] [-p] [--quick] [--stitch] [--no-cache] [--reinstall] [--assets]
#
#   SCENE   full (default) | task | arch | train | tune | verdict
#   -q      Quality: l=480p15 (default), m=720p30, h=1080p60, k=2160p60
#   -p      Preview the clip when done
#   --quick     Collapse on-screen holds (NN_QUICK=1) for fast layout checks
#   --stitch    Render every scene and ffmpeg-concat into one film
#   --no-cache  Force a full re-render
#   --reinstall Recreate the local venv
#   --assets    Force-regenerate assets/nn_learn.npz first
#
# Examples:
#   ./render.sh train --quick      # fast layout check of one scene (480p15)
#   ./render.sh                    # whole film, 480p
#   ./render.sh full -q h          # final HD (slow; run in background)
#   ./render.sh --stitch -q m      # render each scene and stitch (720p)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"
HARNESS_VENV="$ROOT/../HarnessEngineering/.venv"
FOURIER_VENV="$ROOT/../Fourier/.venv"
CNN_VENV="$ROOT/../CNN/.venv"
MEDIA_DIR="$ROOT/media"

SCENE="full"
QUALITY="l"
PREVIEW=""
STITCH=0
REINSTALL=0
NOCACHE=""
FORCE_ASSETS=0
export NN_QUICK="${NN_QUICK:-0}"

while [ $# -gt 0 ]; do
  case "$1" in
    -q) QUALITY="${2:?-q needs a value: l|m|h|k}"; shift 2 ;;
    -p) PREVIEW="-p"; shift ;;
    --quick) NN_QUICK=1; shift ;;
    --stitch) STITCH=1; shift ;;
    --no-cache) NOCACHE="--disable_caching"; shift ;;
    --reinstall) REINSTALL=1; shift ;;
    --assets) FORCE_ASSETS=1; shift ;;
    -h|--help) sed -n '2,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
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

# ---- scene name -> "file class" ------------------------------------------- #
scene_target() {
  case "$1" in
    full)    echo "neural_network.py NeuralNetworkLearns" ;;
    task)    echo "scene1_task.py Task" ;;
    arch)    echo "scene2_arch.py Arch" ;;
    train)   echo "scene3_train.py Train" ;;
    tune)    echo "scene4_tune.py Tune" ;;
    verdict) echo "scene5_verdict.py Verdict" ;;
    *) return 1 ;;
  esac
}

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

# ---- ensure the real dataset / model assets exist ------------------------- #
# The baked PNGs are git-ignored (regenerable), so also regenerate when they're
# missing — e.g. on a fresh clone that has the .npz but not the correctness grids.
if [ "$FORCE_ASSETS" -eq 1 ] || [ ! -f "$ROOT/assets/nn_learn.npz" ] \
   || [ ! -f "$ROOT/assets/grid_large.png" ]; then
  echo ">> Generating dataset + training models (assets/nn_learn.npz + grids)"
  ( cd "$ROOT" && "$PY" generate_assets.py )
fi

export NN_QUICK

render_one() {
  local file="$1" klass="$2"
  echo ""
  echo ">> Rendering $klass  ($file, $QFLAG, quick=$NN_QUICK)"
  ( cd "$ROOT" && "$PY" -m manim $QFLAG $PREVIEW $NOCACHE --media_dir "$MEDIA_DIR" "$file" "$klass" )
}

if [ "$STITCH" -eq 1 ]; then
  ORDER=(task arch train tune verdict)
  OUTPUTS=()
  for s in "${ORDER[@]}"; do
    read -r f k <<< "$(scene_target "$s")"
    render_one "$f" "$k"
    OUTPUTS+=("$MEDIA_DIR/videos/${f%.py}/$RESDIR/$k.mp4")
  done
  FULL="$MEDIA_DIR/NeuralNetwork_${RESDIR}.mp4"
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
  read -r FILE KLASS <<< "$(scene_target "$SCENE")" || { echo "Unknown scene '$SCENE'" >&2; exit 2; }
  render_one "$FILE" "$KLASS"
  echo ""
  echo ">> Done. Video under: $MEDIA_DIR/videos/${FILE%.py}/$RESDIR/$KLASS.mp4"
fi

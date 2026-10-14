#!/usr/bin/env bash
#
# Render "The 17 Squares Problem" explainer.
#
# On first run it reuses an existing Manim venv elsewhere in the repo (the
# HarnessEngineering / Fourier / CNN series' .venv) so Manim isn't reinstalled;
# otherwise it bootstraps a local .venv from requirements.txt.
#
# Usage:
#   ./render.sh [SCENE] [-q l|m|h|k] [-p] [--quick] [--stitch] [--no-cache] [--reinstall]
#
#   SCENE   full (default, the whole film) | intro | problem | record | gap
#             | whytilt | search | evolution | status | outro
#   -q      Quality: l=480p15 (default, fast), m=720p30, h=1080p60, k=2160p60
#   -p      Preview: open the clip when it finishes
#   --quick        Shorten the on-screen holds (SQ_QUICK=1) for a fast test
#   --stitch       Render every section scene and join them into one film
#   --no-cache     Force a full re-render
#   --reinstall    Recreate the local venv from scratch
#
# The animation replays a real packing-search run baked into
# assets/packing_run.npz; regenerate it with:
#   <venv-python> generate_assets.py       (env: SP_BUDGET seconds, SP_SEED)
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"
HARNESS_VENV="$ROOT/../HarnessEngineering/.venv"
FOURIER_VENV="$ROOT/../Fourier/.venv"
CNN_VENV="$ROOT/../CNN/.venv"
MEDIA_DIR="${SQ_MEDIA_DIR:-$ROOT/media}"   # long HD renders: point at /private/tmp (OneDrive stalls)
FILE="squarepacking.py"

SCENE="full"
QUALITY="l"
PREVIEW=""
STITCH=0
REINSTALL=0
NOCACHE=""
export SQ_QUICK="${SQ_QUICK:-0}"

while [ $# -gt 0 ]; do
  case "$1" in
    -q) QUALITY="${2:?-q needs a value: l|m|h|k}"; shift 2 ;;
    -p) PREVIEW="-p"; shift ;;
    --quick) SQ_QUICK=1; shift ;;
    --stitch) STITCH=1; shift ;;
    --no-cache) NOCACHE="--disable_caching"; shift ;;
    --reinstall) REINSTALL=1; shift ;;
    -h|--help) sed -n '2,26p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
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
    full)      echo "SeventeenSquares" ;;
    intro)     echo "Intro" ;;
    problem)   echo "Problem" ;;
    record)    echo "Record" ;;
    gap)       echo "Gap" ;;
    whytilt)   echo "WhyTilt" ;;
    search)    echo "Search" ;;
    evolution) echo "Evolution" ;;
    status)    echo "Status" ;;
    outro)     echo "Outro" ;;
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

export SQ_QUICK

# ---- render --------------------------------------------------------------- #
render_one() {
  local klass="$1"
  echo ""
  echo ">> Rendering $klass  ($QFLAG, quick=$SQ_QUICK)"
  ( cd "$ROOT" && "$PY" -m manim $QFLAG $PREVIEW $NOCACHE --media_dir "$MEDIA_DIR" "$FILE" "$klass" )
}

if [ "$STITCH" -eq 1 ]; then
  ORDER=(Intro Problem Record Gap WhyTilt Search Evolution Status Outro)
  OUTPUTS=()
  for klass in "${ORDER[@]}"; do
    render_one "$klass"
    OUTPUTS+=("$MEDIA_DIR/videos/${FILE%.py}/$RESDIR/$klass.mp4")
  done
  FULL="$MEDIA_DIR/SeventeenSquares_${RESDIR}.mp4"
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

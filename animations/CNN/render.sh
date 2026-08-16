#!/usr/bin/env bash
#
# Render CNN animation Parts 4, 5 and 6.
#
# On first run it bootstraps a local virtualenv (.venv), installs the pinned
# dependencies and (re)generates the image assets, then renders the requested
# scene(s).  Subsequent runs reuse the venv, so iteration is fast.
#
# Usage:
#   ./render.sh [SCENE] [-q l|m|h|k] [-p] [--stitch] [--no-cache] [--skip-assets] [--reinstall]
#
#   SCENE   Which scene(s) to render (default: all)
#             4        -> Part 4 activations      (Scene4_1)
#             5        -> Part 5 pooling           (Scene5_1, Scene5_2)
#             6        -> Part 6 conclusion        (Scene6_1, Scene6_2, Scene6_3)
#             4.1 / 5.2 / 6.3 ...  -> a single scene
#             all      -> every scene above
#
#   -q      Quality: l=480p15 (default, fast), m=720p30, h=1080p60, k=2160p60
#   -p      Preview: open each clip when it finishes
#   --stitch        Join the rendered clips (in order) into one full video
#   --no-cache      Force a full re-render (use after changing image assets)
#   --skip-assets   Do not regenerate images (use existing ones)
#   --reinstall     Recreate the venv from scratch
#
# Examples:
#   ./render.sh              # all scenes, low quality — good for iterating
#   ./render.sh 4 -p         # just Part 4, open it when done
#   ./render.sh 5.2 -q h     # Part 5 scene 2 in 1080p
#   ./render.sh all --stitch # render everything, join into one full video
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"
PY="$VENV/bin/python"
MEDIA_DIR="$ROOT/media"

# ---- defaults ------------------------------------------------------------- #
TARGET="all"
QUALITY="l"
PREVIEW=""
SKIP_ASSETS=0
REINSTALL=0
STITCH=0
NOCACHE=""

# ---- argument parsing ----------------------------------------------------- #
while [ $# -gt 0 ]; do
  case "$1" in
    -q) QUALITY="${2:?-q needs a value: l|m|h|k}"; shift 2 ;;
    -p) PREVIEW="-p"; shift ;;
    --stitch) STITCH=1; shift ;;
    --no-cache) NOCACHE="--disable_caching"; shift ;;
    --skip-assets) SKIP_ASSETS=1; shift ;;
    --reinstall) REINSTALL=1; shift ;;
    -h|--help) sed -n '2,31p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "Unknown option: $1" >&2; exit 2 ;;
    *) TARGET="$1"; shift ;;
  esac
done

# Quality flag + the resolution folder manim writes into (needed for --stitch).
case "$QUALITY" in
  l) QFLAG="-ql"; RESDIR="480p15" ;;
  m) QFLAG="-qm"; RESDIR="720p30" ;;
  h) QFLAG="-qh"; RESDIR="1080p60" ;;
  k) QFLAG="-qk"; RESDIR="2160p60" ;;
  *) echo "Invalid quality '$QUALITY' (use l|m|h|k)" >&2; exit 2 ;;
esac

# ---- scene registry: id -> "dir|file|Class" ------------------------------- #
scene_spec() {
  case "$1" in
    4.1) echo "Part 4_ About Activations|scene_1.py|Scene4_1" ;;
    5.1) echo "Part 5_ About pooling|scene_1.py|Scene5_1" ;;
    5.2) echo "Part 5_ About pooling|scene_2.py|Scene5_2" ;;
    6.1) echo "Part 6_ Conclusion|scene_1.py|Scene6_1" ;;
    6.2) echo "Part 6_ Conclusion|scene_2.py|Scene6_2" ;;
    6.3) echo "Part 6_ Conclusion|scene_3.py|Scene6_3" ;;
    *) return 1 ;;
  esac
}

# ---- expand TARGET into a list of scene ids ------------------------------- #
case "$TARGET" in
  all) SCENES=(4.1 5.1 5.2 6.1 6.2 6.3) ;;
  4)   SCENES=(4.1) ;;
  5)   SCENES=(5.1 5.2) ;;
  6)   SCENES=(6.1 6.2 6.3) ;;
  *)   if scene_spec "$TARGET" >/dev/null; then SCENES=("$TARGET"); \
       else echo "Unknown scene '$TARGET' (try: 4, 5, 6, 4.1, 5.2, 6.3, all)" >&2; exit 2; fi ;;
esac

# ---- bootstrap the environment -------------------------------------------- #
if [ "$REINSTALL" -eq 1 ]; then rm -rf "$VENV"; fi

if [ ! -x "$PY" ]; then
  echo ">> Creating virtualenv (.venv)"
  PYBOOT="$(command -v python3.12 || command -v python3)"
  "$PYBOOT" -m venv "$VENV"
fi

if ! "$PY" -c "import manim" >/dev/null 2>&1; then
  echo ">> Installing dependencies from requirements.txt"
  "$PY" -m pip install --upgrade pip >/dev/null
  "$PY" -m pip install -r "$ROOT/requirements.txt"
fi

# ---- (re)generate image assets -------------------------------------------- #
if [ "$SKIP_ASSETS" -eq 0 ]; then
  echo ">> Generating image assets"
  "$PY" "$ROOT/generate_assets.py"
fi

# ---- render --------------------------------------------------------------- #
OUTPUTS=()
for id in "${SCENES[@]}"; do
  IFS='|' read -r dir file klass <<< "$(scene_spec "$id")"
  echo ""
  echo ">> Rendering $id -> $klass  ($QFLAG)"
  # Run from inside the part directory so the scenes' relative image paths
  # (images/...) resolve; send all output to one shared media/ folder.
  ( cd "$ROOT/$dir" && "$PY" -m manim $QFLAG $PREVIEW $NOCACHE --media_dir "$MEDIA_DIR" "$file" "$klass" )
  OUTPUTS+=("$MEDIA_DIR/videos/${file%.py}/$RESDIR/$klass.mp4")
done

echo ""
echo ">> Done. Videos are in: $MEDIA_DIR/videos/<scene_file>/<quality>/"

# ---- stitch clips into one full video ------------------------------------- #
if [ "$STITCH" -eq 1 ]; then
  FULL="$MEDIA_DIR/CNN_parts_4-6_${RESDIR}.mp4"
  LIST="$(mktemp)"
  for f in "${OUTPUTS[@]}"; do printf "file '%s'\n" "$f" >> "$LIST"; done
  echo ""
  echo ">> Stitching ${#OUTPUTS[@]} clip(s) -> $FULL"
  # All clips share the same codec/res/fps, so a stream copy joins them
  # losslessly and instantly; re-encode as a fallback if that ever fails.
  if ! ffmpeg -y -loglevel error -f concat -safe 0 -i "$LIST" -c copy "$FULL"; then
    echo "   (stream copy failed — re-encoding)"
    ffmpeg -y -loglevel error -f concat -safe 0 -i "$LIST" -c:v libx264 -pix_fmt yuv420p "$FULL"
  fi
  rm -f "$LIST"
  echo ">> Full video: $FULL"
fi

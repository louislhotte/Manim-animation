# shellcheck shell=bash
#
# tools/render_lib.sh: the one render driver behind every animations/<Name>/render.sh.
#
# A film's render.sh declares only what is specific to it, then sources this file:
#
#     FILE=kv_cache.py                     # scene file, relative to the film folder
#     FILM=KVCacheFilm                     # class rendered by `full` ("" = stitch SCENES)
#     SCENES=(Intro Waste Reuse Outro)     # stitch order; "other.py:Class" for other files
#     ALIASES=(idea=TheIdea)               # optional: CLI names that are not lower(Class)
#     ASSETS=(assets/data.npz)             # optional: baked by $ASSET_SCRIPT if missing
#     ASSET_SCRIPT=generate_assets.py      # optional: the baking script (default shown)
#     MEDIA_ENV=KV_MEDIA_DIR               # optional: legacy env var for the media dir
#     MEDIA_DEFAULT=/private/tmp/kv-media  # optional: default media dir (else ./media)
#     source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../tools/render_lib.sh"
#
# Python: $MX_PYTHON if set, else one shared venv OUTSIDE OneDrive at
# ${MX_VENV:-~/.cache/manimx/venv}, created on first use. (OneDrive turns venv
# symlinks into 10-byte text files; such a "python" exits 0 and renders nothing,
# which is why the old per-film venv probing silently failed.)
#
# Written for macOS's bash 3.2: no associative arrays, guarded empty arrays.

set -euo pipefail

MX_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$(dirname "${BASH_SOURCE[1]}")" && pwd)"
FILM="${FILM:-}"
declare -p SCENES >/dev/null 2>&1 || SCENES=()
declare -p ALIASES >/dev/null 2>&1 || ALIASES=()
declare -p ASSETS >/dev/null 2>&1 || ASSETS=()

mx_help() {
  local name; name="$(basename "$ROOT")"
  sed -n '2,/^[^#]/p' "$ROOT/render.sh" | sed -n '/^#/s/^# \{0,1\}//p'
  cat <<EOF
Usage: ./render.sh [SCENE] [-q l|m|h|k] [-p] [--quick] [--check] [--stitch]
                   [--list] [--assets] [--no-cache] [--reinstall] [-- MANIM_ARGS]

  SCENE        full (default: the whole film) or a scene name (see --list)
  -q           quality: l=480p15 (default) | m=720p30 | h=1080p60 | k=2160p60
  -p           open the video when done
  --quick      collapse reading holds (MX_QUICK=1): fast layout checks
  --check      after rendering: edge-bleed scan + 12-frame contact sheet
  --stitch     render every scene in SCENES, then ffmpeg-concat them
  --list       print the scene names and exit
  --assets     re-run generate_assets.py before rendering
  --no-cache   force Manim to re-render every animation
  --reinstall  rebuild the shared venv (\$MX_VENV)
  -- ARGS      pass the rest straight to manim (e.g. -- -s for a still image)

Env: MX_PYTHON (interpreter to use), MX_VENV, MX_MEDIA_DIR, MX_QUICK, MX_DELAY,
     MX_READ, MX_FONT, MX_TRACE=1 (print how long each timed caption stays up),
     MX_TRACE_DIR=<dir> (save those timings: tools/voiceover.py turns them into a
     narration script). Typical loop for $name:
  ./render.sh <scene> --quick --check     # layout pass, then read the sheet
  ./render.sh full -q h                   # final 1080p60 (slow: run in background)
EOF
}

# ---- arguments -------------------------------------------------------------- #
SCENE="full"; QUALITY="l"; PREVIEW=""; NOCACHE=""
STITCH=0; CHECK=0; LIST=0; FORCE_ASSETS=0; REINSTALL=0
MANIM_EXTRA=()
while [ $# -gt 0 ]; do
  case "$1" in
    --) shift; MANIM_EXTRA=("$@"); break ;;
    -q) QUALITY="${2:?-q needs a value: l|m|h|k}"; shift 2 ;;
    -p) PREVIEW="-p"; shift ;;
    --quick) export MX_QUICK=1; shift ;;
    --stitch) STITCH=1; shift ;;
    --check) CHECK=1; shift ;;
    --list) LIST=1; shift ;;
    --assets) FORCE_ASSETS=1; shift ;;
    --no-cache) NOCACHE="--disable_caching"; shift ;;
    --reinstall) REINSTALL=1; shift ;;
    -h|--help) mx_help; exit 0 ;;
    -*) echo "Unknown option: $1 (see --help)" >&2; exit 2 ;;
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

# ---- scene lookup ------------------------------------------------------------- #
mx_lower() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]'; }

mx_target() {  # "file Class" for a SCENES / FILM / ALIASES entry
  case "$1" in
    *:*) echo "${1%%:*} ${1#*:}" ;;
    *) echo "$FILE $1" ;;
  esac
}

mx_resolve() {  # CLI scene name -> "file Class"
  local want e a
  want="$(mx_lower "$1")"
  if [ "$want" = "full" ] && [ -n "$FILM" ]; then mx_target "$FILM"; return 0; fi
  for a in ${ALIASES[@]+"${ALIASES[@]}"}; do
    if [ "$(mx_lower "${a%%=*}")" = "$want" ]; then mx_target "${a#*=}"; return 0; fi
  done
  for e in ${SCENES[@]+"${SCENES[@]}"} ${FILM:+"$FILM"}; do
    if [ "$(mx_lower "${e#*:}")" = "$want" ]; then mx_target "$e"; return 0; fi
  done
  case "$1" in [A-Z]*) echo "$FILE $1"; return 0 ;; esac  # any class in FILE
  return 1
}

if [ "$LIST" -eq 1 ]; then
  echo "Scenes of $(basename "$ROOT") (CLI name -> class):"
  [ -n "$FILM" ] && echo "  full -> ${FILM#*:}"
  for a in ${ALIASES[@]+"${ALIASES[@]}"}; do echo "  ${a%%=*} -> ${a#*=}"; done
  for e in ${SCENES[@]+"${SCENES[@]}"}; do echo "  $(mx_lower "${e#*:}") -> ${e#*:}"; done
  exit 0
fi

if [ "$(mx_lower "$SCENE")" = "full" ] && [ -z "$FILM" ]; then STITCH=1; fi

# ---- interpreter ---------------------------------------------------------------- #
mx_manim_version() {  # prints the manim version $1 can import, or nothing
  [ -n "$1" ] && [ -x "$1" ] || return 0
  "$1" -c 'import manim; print(manim.__version__)' </dev/null 2>/dev/null | tail -1 || true
}

VENV="${MX_VENV:-$HOME/.cache/manimx/venv}"
if [ -n "${MX_PYTHON:-}" ]; then
  PY="$MX_PYTHON"
  [ -n "$(mx_manim_version "$PY")" ] || { echo "MX_PYTHON=$PY cannot import manim" >&2; exit 1; }
else
  if [ "$REINSTALL" -eq 1 ] && [ -f "$VENV/pyvenv.cfg" ]; then rm -rf "$VENV"; fi
  PY="$VENV/bin/python"
  if [ -z "$(mx_manim_version "$PY")" ]; then
    echo ">> Creating the shared Manim venv at $VENV (one time, needs network)"
    PYBOOT="$(command -v python3.12 || command -v python3.11 || command -v python3)"
    mkdir -p "$(dirname "$VENV")"
    "$PYBOOT" -m venv "$VENV"
    "$PY" -m pip install -q --upgrade pip
    "$PY" -m pip install -r "$MX_REPO/tools/requirements-render.txt"
    [ -n "$(mx_manim_version "$PY")" ] || { echo "manim is still not importable from $PY" >&2; exit 1; }
  fi
  if [ -f "$ROOT/requirements.txt" ]; then  # per-film extras, once per file content
    STAMP="$VENV/.mx-req-$(shasum "$ROOT/requirements.txt" | cut -c1-12)"
    if [ ! -f "$STAMP" ]; then
      echo ">> Installing $(basename "$ROOT")/requirements.txt into the shared venv"
      "$PY" -m pip install -q -r "$ROOT/requirements.txt" && touch "$STAMP"
    fi
  fi
fi
export PYTHONPATH="$MX_REPO${PYTHONPATH:+:$PYTHONPATH}"  # -> `import manimx`

# ---- media dir + assets ------------------------------------------------------------ #
MEDIA_DIR="${MX_MEDIA_DIR:-}"
if [ -z "$MEDIA_DIR" ] && [ -n "${MEDIA_ENV:-}" ]; then MEDIA_DIR="${!MEDIA_ENV:-}"; fi
MEDIA_DIR="${MEDIA_DIR:-${MEDIA_DEFAULT:-$ROOT/media}}"

NEED_ASSETS="$FORCE_ASSETS"
for a in ${ASSETS[@]+"${ASSETS[@]}"}; do [ -e "$ROOT/$a" ] || NEED_ASSETS=1; done
if [ "$NEED_ASSETS" -eq 1 ]; then
  ASSET_SCRIPT="${ASSET_SCRIPT:-generate_assets.py}"
  if [ -f "$ROOT/$ASSET_SCRIPT" ]; then
    echo ">> Baking assets ($ASSET_SCRIPT)"
    ( cd "$ROOT" && "$PY" "$ASSET_SCRIPT" )
  else
    echo "!! assets missing and no $ASSET_SCRIPT in $ROOT" >&2; exit 1
  fi
fi

# ---- render ------------------------------------------------------------------------- #
OUTPUTS=()
mx_render() {  # file class
  local file="$1" klass="$2" out marker
  out="$MEDIA_DIR/videos/${file%.py}/$RESDIR/$klass.mp4"
  marker="$(mktemp)"
  echo ""
  echo ">> Rendering $klass ($file, $QFLAG, quick=${MX_QUICK:-0})"
  ( cd "$ROOT" && "$PY" -m manim $QFLAG $PREVIEW $NOCACHE ${MANIM_EXTRA[@]+"${MANIM_EXTRA[@]}"} \
      --media_dir "$MEDIA_DIR" "$file" "$klass" )
  case " ${MANIM_EXTRA[*]-} " in *" -s "*|*" --save_last_frame "*) rm -f "$marker"; return 0 ;; esac
  if [ ! -f "$out" ] || [ "$marker" -nt "$out" ]; then
    rm -f "$marker"
    echo "!! Manim exited cleanly but $out was not (re)written" >&2
    return 1
  fi
  rm -f "$marker"
  OUTPUTS+=("$out")
}

if [ "$STITCH" -eq 1 ]; then
  [ ${#SCENES[@]} -gt 0 ] || { echo "No SCENES declared to stitch" >&2; exit 2; }
  for e in "${SCENES[@]}"; do
    read -r f k <<< "$(mx_target "$e")"
    mx_render "$f" "$k"
  done
  NAME="${FILM#*:}"; NAME="${NAME:-$(basename "$ROOT")}"
  FULL="$MEDIA_DIR/${NAME}_${RESDIR}.mp4"
  LIST_FILE="$(mktemp)"
  for f in "${OUTPUTS[@]}"; do printf "file '%s'\n" "$f" >> "$LIST_FILE"; done
  echo ""
  echo ">> Stitching ${#OUTPUTS[@]} clips -> $FULL"
  if ! ffmpeg -y -loglevel error -f concat -safe 0 -i "$LIST_FILE" -c copy "$FULL"; then
    echo "   (stream copy failed: re-encoding)"
    ffmpeg -y -loglevel error -f concat -safe 0 -i "$LIST_FILE" -c:v libx264 -pix_fmt yuv420p "$FULL"
  fi
  rm -f "$LIST_FILE"
  OUTPUTS=("$FULL")
else
  TARGET="$(mx_resolve "$SCENE")" || { echo "Unknown scene '$SCENE' (see --list)" >&2; exit 2; }
  read -r f k <<< "$TARGET"
  mx_render "$f" "$k"
fi

[ ${#OUTPUTS[@]} -gt 0 ] || { echo ">> Done (still image under $MEDIA_DIR/images)"; exit 0; }
DUR="$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "${OUTPUTS[${#OUTPUTS[@]}-1]}" 2>/dev/null || echo "?")"
echo ""
echo ">> Done ($(printf '%.1f' "$DUR" 2>/dev/null || echo "$DUR") s): ${OUTPUTS[${#OUTPUTS[@]}-1]}"

if [ "$CHECK" -eq 1 ]; then
  for out in "${OUTPUTS[@]}"; do
    echo ""
    echo ">> Checking $(basename "$out")"
    "$PY" "$MX_REPO/tools/edgecheck.py" "$out" 48 || true
    sheet="${out%.mp4}_sheet.jpg"
    "$MX_REPO/tools/contact_sheet.sh" "$out" "$sheet" >/dev/null && echo "   contact sheet: $sheet"
  done
  echo ""
  echo ">> Now LOOK at the sheet(s): overlaps, cropped text, stray arrows, dead space."
fi

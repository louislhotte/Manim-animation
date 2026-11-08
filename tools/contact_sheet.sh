#!/usr/bin/env bash
#
# contact_sheet.sh: tile 12 evenly spaced frames of a video into one image.
#
#   tools/contact_sheet.sh <video.mp4> [out.jpg] [cols] [rows]
#
# The fastest way to *see* a whole scene or film at once: density, dead space,
# repeated slide-like frames, text that is too small, overlaps. Frames are taken
# between 7% and 94% of the duration so the intro/outro cards don't dominate.
set -euo pipefail

VIDEO="${1:?usage: contact_sheet.sh <video.mp4> [out.jpg] [cols] [rows]}"
OUT="${2:-${VIDEO%.*}_sheet.jpg}"
COLS="${3:-4}"
ROWS="${4:-3}"
N=$((COLS * ROWS))

DUR="$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$VIDEO")"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

for i in $(seq 0 $((N - 1))); do
  T="$(awk -v d="$DUR" -v i="$i" -v n="$N" 'BEGIN { printf "%.3f", d * (0.07 + 0.87 * i / (n - 1)) }')"
  ffmpeg -v error -y -ss "$T" -i "$VIDEO" -frames:v 1 -vf "scale=400:225" "$TMP/f$(printf %02d "$i").png"
done
ffmpeg -v error -y -framerate 1 -i "$TMP/f%02d.png" \
  -vf "tile=${COLS}x${ROWS}:padding=4:color=white" -frames:v 1 "$OUT"
echo "$OUT"

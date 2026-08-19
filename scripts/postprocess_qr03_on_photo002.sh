#!/bin/sh
set -eu

root_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source_image="$root_dir/text/application/assets/selection/photo-002.png"
qr_state="$root_dir/text/application/assets/qr_progression/inv_qr_03_6fb1.png"
output_image="$root_dir/text/application/assets/selection/photo-002-qr03.png"
work_dir=$(mktemp -d "${TMPDIR:-/tmp}/takeover-qr03.XXXXXX")
trap 'rm -rf "$work_dir"' EXIT HUP INT TERM

# Crop the third front-page state to its drawn boundary, invert it for the
# photographed black carrier, then register it to the carrier's 66 x 68 px face.
magick "$qr_state" \
  -trim +repage \
  -negate \
  -bordercolor black -border 8 \
  -resize '66x68!' \
  "$work_dir/qr03-on-black.png"

magick "$source_image" "$work_dir/qr03-on-black.png" \
  -geometry +259+201 -composite \
  "$output_image"

printf '%s\n' "$output_image"

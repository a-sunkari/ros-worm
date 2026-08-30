#!/usr/bin/env bash
set -euo pipefail
DEST="${1:-/home/asunkari/ros-worm/ros_worm_stage1}"
mkdir -p "$DEST"
cp -r transport_manifest scripts config docs "$DEST/"
echo "Installed into $DEST"
echo "Next: cd $DEST && ./scripts/build_full_pipeline_v2.sh"

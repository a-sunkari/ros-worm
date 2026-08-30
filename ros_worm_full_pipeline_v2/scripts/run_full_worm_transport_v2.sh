#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_NAME="${1:-transport_full_$(date +%Y%m%d_%H%M%S)}"
MACRO="${TRANSPORT_MACRO:-macros/focused_50kvp.mac}"
RESULTS_DIR="$ROOT_DIR/results/$RUN_NAME"
mkdir -p "$RESULTS_DIR"

if [[ ! -x "$ROOT_DIR/transport_manifest/build/ros_worm_manifest" ]]; then
  "$ROOT_DIR/scripts/build_full_pipeline_v2.sh"
fi

cd "$ROOT_DIR/transport_manifest/build"
rm -f output*.root electron_spectrum*.csv compartment_dose.csv edep_hits.csv secondary_electrons.csv transport_summary.json
./ros_worm_manifest "$MACRO" | tee "$RESULTS_DIR/transport.log"
python3 "$ROOT_DIR/scripts/extract_transport_outputs.py" output0.root \
  --regions "$ROOT_DIR/config/regions.csv" \
  --materials "$ROOT_DIR/config/region_materials.csv" \
  --outdir "$RESULTS_DIR" \
  --target-dose-rate "${TARGET_DOSE_RATE:-1.0}" \
  --pulse-s "${PULSE_S:-10.0}"
cp output0.root "$RESULTS_DIR/transport_output0.root"
echo "Results: $RESULTS_DIR"

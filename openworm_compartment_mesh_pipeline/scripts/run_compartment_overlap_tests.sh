#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 /path/to/openworm_validator /path/to/compartment_pipeline_dir"
  exit 2
fi
VALIDATOR="$1"
PIPE="$2"

run_one() {
  local manifest="$1"
  local label="$2"
  echo "=== Running $label ==="
  G4FORCENUMBEROFTHREADS=1 "$VALIDATOR" \
    --manifest "$manifest" \
    --mm-per-unit 0.1 --res 1000 --tol-mm 0.0001 --maxerr 20 \
    > "${label}.log" 2>&1
  echo "wrote ${label}.log"
}

run_one "$PIPE/manifest_wu_core_children.csv" "wu_core_children_overlap"
run_one "$PIPE/manifest_material_children_no_body.csv" "material_children_no_body_overlap"
run_one "$PIPE/manifest_scoring_atlas.csv" "scoring_atlas_overlap"

#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_NAME="${1:-full_worm_$(date +%Y%m%d_%H%M%S)}"
RESULTS_DIR="$ROOT_DIR/results/$RUN_NAME"
REGIONS="${REGIONS:-1:body 2:nervous 3:bodywall 4:digestive 5:reproductive 6:excretory}"
CHEM_MACRO="${CHEM_MACRO:-ros_spectrum.in}"
mkdir -p "$RESULTS_DIR/regions"

if [[ ! -x "$ROOT_DIR/transport_manifest/build/ros_worm_manifest" || ! -x "$ROOT_DIR/chemistry/build/ros_worm_chem" ]]; then
  "$ROOT_DIR/scripts/build_full_pipeline_v2.sh"
fi

# Stage 1 transport
cd "$ROOT_DIR/transport_manifest/build"
rm -f output*.root
./ros_worm_manifest "${TRANSPORT_MACRO:-macros/focused_50kvp.mac}" | tee "$RESULTS_DIR/transport.log"
python3 "$ROOT_DIR/scripts/extract_transport_outputs.py" output0.root \
  --regions "$ROOT_DIR/config/regions.csv" \
  --materials "$ROOT_DIR/config/region_materials.csv" \
  --outdir "$RESULTS_DIR" \
  --target-dose-rate "${TARGET_DOSE_RATE:-1.0}" \
  --pulse-s "${PULSE_S:-10.0}"
cp output0.root "$RESULTS_DIR/transport_output0.root"

# Stage 2 chemistry by region
for entry in $REGIONS; do
  id="${entry%%:*}"; name="${entry#*:}"
  spec="$RESULTS_DIR/electron_spectrum_region${id}_${name}.csv"
  if [[ ! -s "$spec" ]]; then
    echo "[WARN] missing/empty spectrum $spec; skipping region $id:$name"
    continue
  fi
  rdir="$RESULTS_DIR/regions/region${id}_${name}"
  mkdir -p "$rdir"
  tail -n +2 "$spec" > "$rdir/electron_spectrum.csv"
  cd "$ROOT_DIR/chemistry/build"
  rm -f Species*.root Species.txt electron_spectrum.csv
  cp "$rdir/electron_spectrum.csv" electron_spectrum.csv
  ./ros_worm_chem "$CHEM_MACRO" | tee "$rdir/chemistry.log"
  python3 analysis/summarize_species_root.py --latest --csv "$rdir/species_summary.csv" Species*.root | tee "$rdir/species_summary.txt" || true
  cp Species*.root Species.txt "$rdir/" 2>/dev/null || true
done

python3 "$ROOT_DIR/scripts/make_technical_report.py" --results "$RESULTS_DIR" --out "$RESULTS_DIR/technical_note.md" || true

echo "Results: $RESULTS_DIR"

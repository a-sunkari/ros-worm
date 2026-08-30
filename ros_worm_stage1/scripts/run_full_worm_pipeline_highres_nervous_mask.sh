#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_NAME="${1:-full_worm_$(date +%Y%m%d_%H%M%S)}"
RESULTS_DIR="$ROOT_DIR/results/$RUN_NAME"

GEOM_MANIFEST="${GEOM_MANIFEST:-/home/asunkari/ros-worm/openworm_geometry/compartment_pipeline/non_nervous_priority_bake/debug_core_voxel_remesh_NO_PHYSICAL_NERVOUS_manifest.csv}"
TRANSPORT_MACRO_IN="${TRANSPORT_MACRO:-$ROOT_DIR/transport_manifest/macros/focused_50kvp.mac}"
CHEM_MACRO="${CHEM_MACRO:-ros_spectrum.in}"

# Physical transport regions only. Nervous system is handled later as high-res spatial mask.
REGIONS="${REGIONS:-1:body 3:bodywall 4:digestive 5:reproductive 6:excretory}"

mkdir -p "$RESULTS_DIR/regions" "$RESULTS_DIR/_runtime"

if [[ ! -x "$ROOT_DIR/transport_manifest/build/ros_worm_manifest" || ! -x "$ROOT_DIR/chemistry/build/ros_worm_chem" ]]; then
  "$ROOT_DIR/scripts/build_full_pipeline_v2.sh"
fi

# Create runtime macro with manifest forcibly replaced.
RUNTIME_MACRO="$RESULTS_DIR/_runtime/transport_runtime.mac"
python3 - "$TRANSPORT_MACRO_IN" "$GEOM_MANIFEST" "$RUNTIME_MACRO" <<'PY'
from pathlib import Path
import sys, re

src = Path(sys.argv[1])
manifest = Path(sys.argv[2])
dst = Path(sys.argv[3])

s = src.read_text()

if "/rosworm/manifest" in s:
    s = re.sub(r"(?m)^/rosworm/manifest\s+.*$", f"/rosworm/manifest {manifest}", s)
else:
    s = f"/rosworm/manifest {manifest}\n" + s

dst.write_text(s)

print("[RUNTIME_MACRO]", dst)
for line in s.splitlines():
    if "/rosworm/manifest" in line or "/run/numberOfThreads" in line or "/run/beamOn" in line:
        print(line)
PY

echo "[PIPELINE] RUN_NAME=$RUN_NAME"
echo "[PIPELINE] RESULTS_DIR=$RESULTS_DIR"
echo "[PIPELINE] GEOM_MANIFEST=$GEOM_MANIFEST"
echo "[PIPELINE] TRANSPORT_MACRO_IN=$TRANSPORT_MACRO_IN"
echo "[PIPELINE] RUNTIME_MACRO=$RUNTIME_MACRO"
echo "[PIPELINE] REGIONS=$REGIONS"

# Stage 1 transport
cd "$ROOT_DIR/transport_manifest/build"
rm -f output*.root
./ros_worm_manifest "$RUNTIME_MACRO" | tee "$RESULTS_DIR/transport.log"

python3 "$ROOT_DIR/scripts/extract_transport_outputs.py" output0.root \
  --regions "$ROOT_DIR/config/regions.csv" \
  --materials "$ROOT_DIR/config/region_materials.csv" \
  --outdir "$RESULTS_DIR" \
  --target-dose-rate "${TARGET_DOSE_RATE:-1.0}" \
  --pulse-s "${PULSE_S:-10.0}"

cp output0.root "$RESULTS_DIR/transport_output0.root"

# Stage 2 chemistry by physical region only
for entry in $REGIONS; do
  id="${entry%%:*}"
  name="${entry#*:}"
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

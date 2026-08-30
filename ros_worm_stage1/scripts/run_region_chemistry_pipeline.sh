#!/usr/bin/env bash
set -euo pipefail

# Run Stage-1 transport once, then run Geant4-DNA chemistry separately for each
# transport scoring region that produces an electron spectrum.
#
# Default regions are the currently nonzero Level-1 ROIs:
#   1 whole worm, 4 body-wall/muscle proxy, 5 intestine proxy
# You can override with e.g.:
#   REGIONS="1:worm 2:head 3:vnc 4:bodywall 5:intestine" ./scripts/run_region_chemistry_pipeline.sh run_all

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_NAME="${1:-regions_$(date +%Y%m%d_%H%M%S)}"
RESULTS_DIR="${ROOT_DIR}/results/${RUN_NAME}"
TRANSPORT_MACRO="${TRANSPORT_MACRO:-macros/run_focused_transport.mac}"
TARGET_DOSE_RATE="${TARGET_DOSE_RATE:-1.0}"
CHEM_MACRO="${CHEM_MACRO:-ros_spectrum.in}"
REGIONS_STRING="${REGIONS:-1:worm 4:bodywall 5:intestine}"
mkdir -p "${RESULTS_DIR}/regions"

echo "=== Stage-1 regional ROS Worm pipeline: ${RUN_NAME} ==="
echo "Transport macro: ${TRANSPORT_MACRO}"
echo "Chemistry macro: ${CHEM_MACRO}"
echo "Regions: ${REGIONS_STRING}"

if [[ ! -x "${ROOT_DIR}/transport/build/ros_worm" || ! -x "${ROOT_DIR}/chemistry/build/ros_worm_chem" ]]; then
  echo "Build products not found. Running scripts/build_all.sh first."
  "${ROOT_DIR}/scripts/build_all.sh"
fi

echo "=== Cleaning old run outputs ==="
rm -f "${ROOT_DIR}/transport/build/output"*.root 2>/dev/null || true
rm -f "${ROOT_DIR}/transport/build/electron_spectrum"*.csv 2>/dev/null || true
rm -f "${ROOT_DIR}/chemistry/build/Species"*.root 2>/dev/null || true
rm -f "${ROOT_DIR}/chemistry/build/Species.txt" 2>/dev/null || true
rm -f "${ROOT_DIR}/chemistry/build/electron_spectrum.csv" 2>/dev/null || true

cd "${ROOT_DIR}/transport/build"
echo "=== Transport: X-ray into simplified worm analogue ==="
./ros_worm "${TRANSPORT_MACRO}" | tee "${RESULTS_DIR}/transport.log"
python3 analysis/summarize_transport.py output0.root | tee "${RESULTS_DIR}/transport_summary.txt"
python3 analysis/scale_to_doserate.py output0.root --target-dose-rate "${TARGET_DOSE_RATE}" | tee "${RESULTS_DIR}/dose_scaling_${TARGET_DOSE_RATE}Gy_s.txt"
cp output0.root "${RESULTS_DIR}/transport_output0.root"

REGION_CSVS=()

for entry in ${REGIONS_STRING}; do
  region_id="${entry%%:*}"
  region_name="${entry#*:}"
  region_dir="${RESULTS_DIR}/regions/region${region_id}_${region_name}"
  mkdir -p "${region_dir}"

  echo "=== Region ${region_id} (${region_name}): spectrum generation ==="
  cd "${ROOT_DIR}/transport/build"
  spectrum_file="electron_spectrum_region${region_id}_${region_name}.csv"
  if python3 analysis/make_chemistry_spectrum.py output0.root --region "${region_id}" --output "${spectrum_file}" | tee "${region_dir}/spectrum_generation.txt"; then
    cp "${spectrum_file}" "${region_dir}/electron_spectrum.csv"
  else
    echo "[WARN] Region ${region_id} (${region_name}) had no usable electron spectrum; skipping chemistry." | tee -a "${region_dir}/spectrum_generation.txt"
    continue
  fi

  echo "=== Region ${region_id} (${region_name}): chemistry ==="
  cd "${ROOT_DIR}/chemistry/build"
  rm -f Species*.root Species.txt electron_spectrum.csv 2>/dev/null || true
  cp "${region_dir}/electron_spectrum.csv" electron_spectrum.csv
  ./ros_worm_chem "${CHEM_MACRO}" | tee "${region_dir}/chemistry.log"

  python3 analysis/summarize_species_root.py --latest --csv "${region_dir}/species_summary.csv" Species*.root | tee "${region_dir}/species_summary.txt"
  cp Species*.root Species.txt "${region_dir}/" 2>/dev/null || true
  REGION_CSVS+=("${region_id}:${region_name}:${region_dir}/species_summary.csv")
done

if [[ ${#REGION_CSVS[@]} -gt 0 ]]; then
  echo "=== Combining region species summaries ==="
  python3 "${ROOT_DIR}/scripts/merge_region_species.py" \
    --output "${RESULTS_DIR}/region_species_summary.csv" \
    "${REGION_CSVS[@]}"
  column -s, -t "${RESULTS_DIR}/region_species_summary.csv" | tee "${RESULTS_DIR}/region_species_summary.txt" || cat "${RESULTS_DIR}/region_species_summary.csv" | tee "${RESULTS_DIR}/region_species_summary.txt"
else
  echo "[WARN] No region chemistry summaries were produced."
fi

echo "=== Completed regional pipeline ==="
echo "Results: ${RESULTS_DIR}"

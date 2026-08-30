#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_NAME="${1:-stage1_$(date +%Y%m%d_%H%M%S)}"
RESULTS_DIR="${ROOT_DIR}/results/${RUN_NAME}"
mkdir -p "${RESULTS_DIR}"

echo "=== Stage-1 ROS Worm pipeline: ${RUN_NAME} ==="

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

echo "=== Transport: X-ray into simplified worm analogue ==="
cd "${ROOT_DIR}/transport/build"
./ros_worm macros/run_focused_transport.mac | tee "${RESULTS_DIR}/transport.log"
python3 analysis/summarize_transport.py output0.root | tee "${RESULTS_DIR}/transport_summary.txt"
python3 analysis/scale_to_doserate.py output0.root --target-dose-rate 1.0 | tee "${RESULTS_DIR}/dose_scaling_1Gy_s.txt"
python3 analysis/make_chemistry_spectrum.py output0.root --region 1 --output electron_spectrum.csv | tee "${RESULTS_DIR}/spectrum_generation.txt"
cp output0.root "${RESULTS_DIR}/transport_output0.root"
cp electron_spectrum.csv "${RESULTS_DIR}/electron_spectrum.csv"

echo "=== Chemistry: Geant4-DNA water radiolysis from transport electron spectrum ==="
cp electron_spectrum.csv "${ROOT_DIR}/chemistry/build/electron_spectrum.csv"
cd "${ROOT_DIR}/chemistry/build"
./ros_worm_chem ros_spectrum.in | tee "${RESULTS_DIR}/chemistry.log"
python3 analysis/summarize_species_root.py --latest --csv "${RESULTS_DIR}/species_summary.csv" Species*.root | tee "${RESULTS_DIR}/species_summary.txt"
cp Species*.root Species.txt "${RESULTS_DIR}/" 2>/dev/null || true

echo "=== Completed ==="
echo "Results: ${RESULTS_DIR}"

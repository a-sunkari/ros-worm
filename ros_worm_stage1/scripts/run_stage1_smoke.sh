#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Transport smoke test
cd "${ROOT_DIR}/transport/build"
./ros_worm macros/debug_steps.mac
python3 analysis/make_chemistry_spectrum.py output0.root --region 1 --output electron_spectrum.csv

# Chemistry smoke test using generated transport spectrum
cp electron_spectrum.csv "${ROOT_DIR}/chemistry/build/electron_spectrum.csv"
cd "${ROOT_DIR}/chemistry/build"
./ros_worm_chem ros_spectrum.in
python3 analysis/summarize_species_root.py Species*.root || true

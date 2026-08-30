#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

rm -f "${ROOT_DIR}"/transport/build/output*.root 2>/dev/null || true
rm -f "${ROOT_DIR}"/transport/build/electron_spectrum*.csv 2>/dev/null || true
rm -f "${ROOT_DIR}"/chemistry/build/Species*.root 2>/dev/null || true
rm -f "${ROOT_DIR}"/chemistry/build/Species.txt 2>/dev/null || true
rm -f "${ROOT_DIR}"/chemistry/build/electron_spectrum.csv 2>/dev/null || true
rm -rf "${ROOT_DIR}"/results/* 2>/dev/null || true
mkdir -p "${ROOT_DIR}"/results

echo "Cleaned generated Stage-1 outputs."

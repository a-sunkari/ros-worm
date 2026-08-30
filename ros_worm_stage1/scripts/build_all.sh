#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for sub in transport chemistry; do
  echo "=== Building ${sub} ==="
  cd "${ROOT_DIR}/${sub}"
  rm -rf build
  mkdir build
  cd build
  cmake ..
  make -j"$(nproc)"
done

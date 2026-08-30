#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "$ROOT_DIR/transport_manifest/build"
cd "$ROOT_DIR/transport_manifest/build"
cmake ..
cmake --build . -j"$(nproc)"

mkdir -p "$ROOT_DIR/chemistry/build"
cd "$ROOT_DIR/chemistry/build"
cmake ..
cmake --build . -j"$(nproc)"

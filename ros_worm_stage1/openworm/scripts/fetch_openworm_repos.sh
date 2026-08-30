#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "${ROOT_DIR}/external"
cd "${ROOT_DIR}/external"

clone_or_update() {
  local url="$1"
  local name="$2"
  if [[ -d "$name/.git" ]]; then
    echo "Updating $name"
    git -C "$name" pull --ff-only || true
  else
    echo "Cloning $name"
    git clone "$url" "$name"
  fi
}

clone_or_update https://github.com/openworm/c302.git c302
clone_or_update https://github.com/openworm/CElegansNeuroML.git CElegansNeuroML
clone_or_update https://github.com/openworm/sibernetic.git sibernetic

echo "OpenWorm repositories are in ${ROOT_DIR}/external"

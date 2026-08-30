#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

echo "=== git status ==="
git status --short || true

echo
echo "=== tracked build/generated files that should generally not be tracked ==="
(git ls-files | grep -E '(^|/)build/|\.root$|Species\.txt$|electron_spectrum\.csv$|__pycache__|\.pyc$' || true)

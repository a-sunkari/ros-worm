#!/usr/bin/env bash
set -euo pipefail
LOG="${1:?usage: summarize_validator_log.sh audit.log}"
echo "=== counts ==="
printf "loaded objects: "; grep -c "\[OPENWORM-VALIDATOR\]\[LOADED\]" "$LOG" || true
printf "load errors: "; grep -c "\[OPENWORM-VALIDATOR\]\[LOAD_ERROR\]" "$LOG" || true
printf "GeomSolids1001 small/narrow facets: "; grep -c "GeomSolids1001" "$LOG" || true
printf "GeomSolids1002 bad facet add: "; grep -c "GeomSolids1002" "$LOG" || true
printf "solid defects: "; grep -c "Defects in solid" "$LOG" || true
printf "overlap mentions: "; grep -ci "overlap" "$LOG" || true

echo
echo "=== load errors ==="
grep "\[OPENWORM-VALIDATOR\]\[LOAD_ERROR\]" "$LOG" || true

echo
echo "=== solid defects / holes / orientation ==="
grep -iE "Defects in solid|holes|wrong orientation|GeomSolids1001|GeomSolids1002" "$LOG" | head -300 || true

echo
echo "=== overlap lines tail ==="
grep -i "overlap" "$LOG" | tail -300 || true

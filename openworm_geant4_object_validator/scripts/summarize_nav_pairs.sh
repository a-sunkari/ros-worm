#!/usr/bin/env bash
set -euo pipefail

LOG="${1:?usage: summarize_nav_pairs.sh log.txt}"

echo "=== counts ==="
printf "GeomNav1002: "
grep -c "GeomNav1002" "$LOG" || true
printf "Track stuck: "
grep -c "Track stuck" "$LOG" || true

echo
echo "=== stuck boundary pairs ==="
awk '
/Current  phys volume:/ {
  cur=$0
  sub(/^.*Current  phys volume: /, "", cur)
  gsub(/\047/, "", cur)
}
/Previous phys volume:/ {
  prev=$0
  sub(/^.*Previous phys volume: /, "", prev)
  gsub(/\047/, "", prev)
  print "current=" cur " previous=" prev
}
' "$LOG" | sort | uniq -c | sort -nr

echo
echo "=== smoke summary ==="
grep -nE "SMOKE_RUN_END|SMOKE_STEP_VOLUME_COUNTS|SMOKE_EDEP_BY_VOLUME_KEV" "$LOG" || true
grep -nA80 "SMOKE_STEP_VOLUME_COUNTS" "$LOG" || true

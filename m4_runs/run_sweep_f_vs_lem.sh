#!/usr/bin/env bash
# Drive bench_sweep_f_vs_lem across all N in m4_runs/sweep_n_list_f_vs_lem.txt
# for 5 runs of 4 modes each (hb, hs, cb, cs). Each invocation is a fresh
# process so cold modes get genuine cold caches.
#
# Output layout:
#   m4_runs/sweep_fvl_n${N}_${mode}_run${R}.txt   -- raw bench_sweep_f_vs_lem stdout
#
# Resume-friendly: skips outputs that already contain a RESULT line.
#
# Usage: m4_runs/run_sweep_f_vs_lem.sh [num_sets=200] [hot_reps=200]

set -euo pipefail

NUM_SETS=${1:-200}
HOT_REPS=${2:-200}

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

LIST="m4_runs/sweep_n_list_f_vs_lem.txt"
BIN="./bench_sweep_f_vs_lem"

if [[ ! -x "$BIN" ]]; then
  echo "missing $BIN -- build first:" >&2
  echo "  clang++ -O3 -mcpu=apple-m4 -std=c++20 bench_sweep_f_vs_lem.cpp simd_quad_m4.c -o bench_sweep_f_vs_lem" >&2
  exit 1
fi

NS=$(cat "$LIST")
N_COUNT=$(wc -l <"$LIST" | tr -d ' ')

MODES="hb hs cb cs"
RUNS="1 2 3 4 5"

TOTAL=$(( N_COUNT * 4 * 5 ))
DONE=0
T0=$SECONDS

# Outer loop over runs, inner over modes, innermost over N. Spreads each
# run-R median's draws across time so thermal/background drift averages out.
for R in $RUNS; do
  for MODE in $MODES; do
    for N in $NS; do
      OUT="m4_runs/sweep_fvl_n${N}_${MODE}_run${R}.txt"
      DONE=$((DONE + 1))
      if [[ -s "$OUT" ]] && grep -q "^RESULT " "$OUT"; then
        continue
      fi
      ELAPSED=$((SECONDS - T0))
      if (( DONE > 1 )); then
        ETA=$(( ELAPSED * (TOTAL - DONE) / (DONE - 1) ))
        printf "[%5d/%5d] elapsed %5ds eta %5ds  n=%-4d %s run%s\n" \
          "$DONE" "$TOTAL" "$ELAPSED" "$ETA" "$N" "$MODE" "$R"
      else
        printf "[%5d/%5d] elapsed %5ds  n=%-4d %s run%s\n" \
          "$DONE" "$TOTAL" "$ELAPSED" "$N" "$MODE" "$R"
      fi
      "$BIN" "$N" "$MODE" "$NUM_SETS" "$HOT_REPS" >"$OUT" 2>&1
    done
  done
done

echo "sweep complete: $TOTAL invocations in $((SECONDS - T0))s"

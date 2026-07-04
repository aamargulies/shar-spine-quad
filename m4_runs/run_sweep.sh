#!/usr/bin/env bash
# Drive bench_sweep across all N in m4_runs/sweep_n_list.txt for 5 runs of
# 4 modes each (hb, hs, cb, cs). Cold modes run in fresh processes; we
# already get that here since each ./bench_sweep is its own process.
#
# Output layout:
#   m4_runs/sweep_n${N}_${mode}_run${R}.txt   -- raw bench_sweep stdout
#
# Resume-friendly: skips outputs that already exist (so `kill` + rerun is
# safe). To force a fresh run, delete the relevant files first.
#
# Usage: m4_runs/run_sweep.sh [num_sets=200] [hot_reps=200]
#   from the QuadSearch repo root.

set -euo pipefail

NUM_SETS=${1:-200}
HOT_REPS=${2:-200}

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

LIST="m4_runs/sweep_n_list.txt"
BIN="./bench_sweep"

if [[ ! -x "$BIN" ]]; then
  echo "missing $BIN -- build first:" >&2
  echo "  clang++ -O3 -mcpu=apple-m4 -std=c++20 bench_sweep.cpp simd_quad_m4.c simd_quad_m4_spine_family.c -o bench_sweep" >&2
  exit 1
fi

NS=$(cat "$LIST")
N_COUNT=$(wc -l <"$LIST" | tr -d ' ')

MODES="hb hs cb cs"
RUNS="1 2 3 4 5"

# Total work units (for progress).
TOTAL=$(( N_COUNT * 4 * 5 ))
DONE=0
T0=$SECONDS

# Order: outer loop over runs, inner over modes, innermost over N. Spreading
# runs across time keeps each "run R median" estimate insensitive to thermal
# drift and background noise on a particular timeslice.
for R in $RUNS; do
  for MODE in $MODES; do
    for N in $NS; do
      OUT="m4_runs/sweep_n${N}_${MODE}_run${R}.txt"
      DONE=$((DONE + 1))
      if [[ -s "$OUT" ]] && grep -q "^RESULT " "$OUT"; then
        continue  # already complete
      fi
      ELAPSED=$((SECONDS - T0))
      if (( DONE > 1 )); then
        ETA=$(( ELAPSED * (TOTAL - DONE) / (DONE - 1) ))
        printf "[%4d/%4d] elapsed %5ds eta %5ds  n=%-4d %s run%s\n" \
          "$DONE" "$TOTAL" "$ELAPSED" "$ETA" "$N" "$MODE" "$R"
      else
        printf "[%4d/%4d] elapsed %5ds  n=%-4d %s run%s\n" \
          "$DONE" "$TOTAL" "$ELAPSED" "$N" "$MODE" "$R"
      fi
      "$BIN" "$N" "$MODE" "$NUM_SETS" "$HOT_REPS" >"$OUT" 2>&1
    done
  done
done

echo "sweep complete: $TOTAL invocations in $((SECONDS - T0))s"

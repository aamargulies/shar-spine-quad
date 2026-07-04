#!/usr/bin/env bash
# Drive bench_sweep across all N in pi5_runs/sweep_n_list.txt for 5 runs of
# 4 modes each (hb, hs, cb, cs). Cold modes run in fresh processes; we
# already get that here since each ./bench_sweep is its own process.
#
# Output layout:
#   pi5_runs/sweep_n${N}_${mode}_run${R}.txt   -- raw bench_sweep stdout
#
# Resume-friendly: skips outputs that already exist.
#
# Usage: pi5_runs/run_sweep.sh [num_sets=200] [hot_reps=200]
#   from the QuadSearch repo root, with the Pi 5 bench_sweep already built:
#     g++ -O3 -mcpu=cortex-a76 -std=c++20 -DQUADSEARCH_ARM_PI5 \
#         bench_sweep.cpp simd_quad_pi5.c simd_quad_pi5_spine_family.c \
#         -o bench_sweep

set -euo pipefail

NUM_SETS=${1:-200}
HOT_REPS=${2:-200}

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

LIST="pi5_runs/sweep_n_list.txt"
BIN="./bench_sweep"

if [[ ! -x "$BIN" ]]; then
  echo "missing $BIN -- build first:" >&2
  echo "  g++ -O3 -mcpu=cortex-a76 -std=c++20 -DQUADSEARCH_ARM_PI5 bench_sweep.cpp simd_quad_pi5.c simd_quad_pi5_spine_family.c -o bench_sweep" >&2
  exit 1
fi

NS=$(cat "$LIST")
N_COUNT=$(wc -l <"$LIST" | tr -d ' ')

MODES="hb hs cb cs"
RUNS="1 2 3 4 5"

TOTAL=$(( N_COUNT * 4 * 5 ))
DONE=0
T0=$SECONDS

for R in $RUNS; do
  for MODE in $MODES; do
    for N in $NS; do
      OUT="pi5_runs/sweep_n${N}_${MODE}_run${R}.txt"
      DONE=$((DONE + 1))
      if [[ -s "$OUT" ]] && grep -q "^RESULT " "$OUT"; then
        continue
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

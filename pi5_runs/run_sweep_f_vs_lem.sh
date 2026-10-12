#!/usr/bin/env bash
# Drive bench_sweep_f_vs_lem (F vs Lemire 2026-04-27 vs Lemire 2026-10-02) on
# the Raspberry Pi 5 across every N in a size list (default: the 200 sizes of
# m4_runs/sweep_n_list_f_vs_lem.txt, shared with the M4 campaign) for 5 runs of
# 4 modes each (hb, hs, cb, cs). Each cell is a fresh process pinned to one
# core, so cold modes get genuine cold caches; the run index is passed as
# order_seed so the three variants are timed in a different order per run.
#
# Output layout:
#   pi5_runs/sweep_fvl2_n${N}_${mode}_run${R}.txt
#     '# host / date / governor / temp_c / command' lines written here, then
#     the harness stdout (its own '# ...' lines and the RESULT line).
# After a campaign fold the per-cell files into pi5_runs/sweep_fvl2_raw.txt:
#   python3 consolidate_sweep.py pi5_runs sweep_fvl2 --delete
# The prefix is sweep_fvl2 (not sweep_fvl): the RESULT line has a third
# column, Lem2, and the April-only M4 archive must stay as it is.
#
# Resume-friendly: skips cells whose file already holds a RESULT line. A cell
# whose process fails gets a '# FAILED exit N' line and is retried next time.
#
# Usage (from the repo root). Build the binary on local disk, not on the CIFS
# share, whose client cannot be trusted to keep the exec bit visible:
#   g++ -O3 -mcpu=cortex-a76 -std=c++20 -DQUADSEARCH_ARM_PI5 \
#       bench_sweep_f_vs_lem.cpp simd_quad_pi5.c -o /home/pi/bench_sweep_f_vs_lem
#   FVL_BIN=/home/pi/bench_sweep_f_vs_lem bash pi5_runs/run_sweep_f_vs_lem.sh [num_sets=100] [hot_reps=200] [list]
# Env: FVL_BIN (binary, default ./bench_sweep_f_vs_lem), FVL_CPU (core to pin,
# default 3), FVL_RUNS (default "1 2 3 4 5").

set -euo pipefail

NUM_SETS=${1:-100}
HOT_REPS=${2:-200}
LIST=${3:-m4_runs/sweep_n_list_f_vs_lem.txt}
BIN="${FVL_BIN:-./bench_sweep_f_vs_lem}"
CPU="${FVL_CPU:-3}"
RUNS="${FVL_RUNS:-1 2 3 4 5}"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -f "$BIN" ]]; then
  echo "missing $BIN -- build first (see the header of this script)" >&2
  exit 1
fi
if [[ ! -f "$LIST" ]]; then
  echo "missing size list $LIST" >&2
  exit 1
fi

NS=$(cat "$LIST")
N_COUNT=$(wc -l <"$LIST" | tr -d ' ')
MODES="hb hs cb cs"
N_RUNS=$(wc -w <<<"$RUNS")

TOTAL=$(( N_COUNT * 4 * N_RUNS ))
DONE=0
FAILED=0
T0=$SECONDS

governor() { cat "/sys/devices/system/cpu/cpu${CPU}/cpufreq/scaling_governor" 2>/dev/null || echo unknown; }
temp_c()   { awk '{printf "%.1f", $1/1000}' /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo unknown; }

echo "bench_sweep_f_vs_lem campaign: ${N_COUNT} sizes x 4 modes x ${N_RUNS} runs = ${TOTAL} cells; num_sets=${NUM_SETS} hot_reps=${HOT_REPS} cpu=${CPU} bin=${BIN} governor=$(governor) temp_c=$(temp_c)"

# Outer loop over runs, inner over modes, innermost over N, as in the M4
# driver: each run's measurements are spread across the whole campaign so
# thermal and background drift average out across runs.
for R in $RUNS; do
  for MODE in $MODES; do
    for N in $NS; do
      OUT="pi5_runs/sweep_fvl2_n${N}_${MODE}_run${R}.txt"
      DONE=$((DONE + 1))
      if [[ -s "$OUT" ]] && grep -q "^RESULT " "$OUT"; then
        continue
      fi
      ELAPSED=$((SECONDS - T0))
      if (( DONE > 1 )); then
        ETA=$(( ELAPSED * (TOTAL - DONE) / (DONE - 1) ))
        printf "[%5d/%5d] elapsed %5ds eta %5ds  n=%-4d %s run%s temp=%s\n" \
          "$DONE" "$TOTAL" "$ELAPSED" "$ETA" "$N" "$MODE" "$R" "$(temp_c)"
      else
        printf "[%5d/%5d] elapsed %5ds  n=%-4d %s run%s temp=%s\n" \
          "$DONE" "$TOTAL" "$ELAPSED" "$N" "$MODE" "$R" "$(temp_c)"
      fi
      {
        echo "# host: pi5"
        echo "# date: $(date -Is)"
        echo "# governor: $(governor)"
        echo "# temp_c: $(temp_c)"
        echo "# command: taskset -c $CPU $BIN $N $MODE $NUM_SETS $HOT_REPS $R"
      } >"$OUT"
      if ! taskset -c "$CPU" "$BIN" "$N" "$MODE" "$NUM_SETS" "$HOT_REPS" "$R" >>"$OUT" 2>&1; then
        echo "# FAILED exit $?" >>"$OUT"
        FAILED=$((FAILED + 1))
        echo "  cell failed: $OUT" >&2
      fi
    done
  done
done

echo "sweep complete: $TOTAL cells in $((SECONDS - T0))s, $FAILED failed"

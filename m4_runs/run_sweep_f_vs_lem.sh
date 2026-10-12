#!/usr/bin/env bash
# Drive bench_sweep_f_vs_lem (F vs Lemire 2026-04-27 vs Lemire 2026-10-02)
# across all N in m4_runs/sweep_n_list_f_vs_lem.txt for 5 runs of 4 modes
# each (hb, hs, cb, cs). Each invocation is a fresh process so cold modes get
# genuine cold caches; the run index is passed as order_seed so the three
# variants are timed in a different order per run.
#
# Output layout:
#   m4_runs/sweep_fvl2_n${N}_${mode}_run${R}.txt   -- raw bench_sweep_f_vs_lem stdout
#
# The prefix is sweep_fvl2: since 2026-10-11 the harness prints a third column
# (Lem2, Lemire's revised kernel), and these cells must not be merged into the
# archived April-only campaign m4_runs/sweep_fvl_raw.txt (2026-05-20, F and
# Lem). After a campaign fold the per-cell files into m4_runs/sweep_fvl2_raw.txt
# (one '### <basename>' header per file, then its lines verbatim) with
#   python3 consolidate_sweep.py m4_runs sweep_fvl2 --delete
# from the repo root. The resume check below only sees per-cell files, so
# re-running this driver after consolidation re-measures every cell; the
# consolidator then merges the new files into the raw file, replacing
# same-named entries.
#
# Resume-friendly: skips outputs that already contain a RESULT line.
#
# Usage: m4_runs/run_sweep_f_vs_lem.sh [num_sets=200] [hot_reps=200]
# Env: FVL_BIN overrides the binary path (default ./bench_sweep_f_vs_lem).

set -euo pipefail

NUM_SETS=${1:-200}
HOT_REPS=${2:-200}

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

LIST="m4_runs/sweep_n_list_f_vs_lem.txt"
BIN="${FVL_BIN:-./bench_sweep_f_vs_lem}"

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
      OUT="m4_runs/sweep_fvl2_n${N}_${MODE}_run${R}.txt"
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
      "$BIN" "$N" "$MODE" "$NUM_SETS" "$HOT_REPS" "$R" >"$OUT" 2>&1
    done
  done
done

echo "sweep complete: $TOTAL invocations in $((SECONDS - T0))s"

#!/usr/bin/env bash
# Host-generic driver for bench_sweep_f_vs_lem (F, Lemire 2026-04-27, Lemire
# 2026-10-02, Fb, LemS) across every N in a size list, RUNS runs of 4 modes
# each (hb, hs, cb, cs). Each cell is a fresh process pinned to one core, so
# the cold modes get genuinely cold caches; the run index is the order_seed,
# so the variants are timed in a different order per run.
#
# The per-host drivers m4_runs/run_sweep_f_vs_lem.sh and
# pi5_runs/run_sweep_f_vs_lem.sh are the ones the archived campaigns used;
# this one writes the same cells for any host:
#
# Usage: ./run_sweep_f_vs_lem.sh HOST [num_sets=100] [hot_reps=200] [list]
#   HOST   pi5 | m4 | m1 | skx | emr | gv4 | cfl ...   (selects HOST_runs/)
#   list   size list, one N per line (default pi5_runs/sweep_n_list_f_vs_lem.txt:
#          the 179 sizes 1..4096 of the Pi 5 campaigns; the M4 archive used the
#          200-size list to 8192, m4_runs/sweep_n_list_f_vs_lem.txt)
#
# Output: HOST_runs/${FVL_PREFIX}_n${N}_${mode}_run${R}.txt with the header
# lines '# host / machine / date / governor / temp_c / command [/ note]' and
# the harness stdout (its '# ...' lines and the RESULT line). Afterwards fold
# the cells:  python3 consolidate_sweep.py HOST_runs ${FVL_PREFIX} --delete
# and aggregate:  python3 compute_sweep_fvl.py HOST --prefix ${FVL_PREFIX}
#
# The prefix names the harness's column set and must match the binary
# (sweep_fvl3 = F Lem Lem2 Fb LemS, the harness since 2026-10-12; sweep_fvl2 =
# F Lem Lem2; sweep_fvl = F Lem). Never mix column sets under one prefix. The
# harness header also records desc_align (the container descriptor layout,
# -DQUADSEARCH_DESCRIPTOR_ALIGN; 16 in the Pi 5 and M4 archives, 64 from the
# 2026-10-12 layout fix on), which the aggregator reports.
#
# Resume-friendly: cells whose file already holds a RESULT line are skipped;
# a failed cell gets a '# FAILED exit N' line and is retried next time.
#
# Environment: FVL_BIN (binary, default ./bench_sweep_f_vs_lem), FVL_CPU
# (core to pin, default last core; none disables), FVL_RUNS (default
# "1 2 3 4 5 6 7 8 9 10"), FVL_PREFIX (default sweep_fvl3), FVL_NOTE (written
# as '# note: ...' in every cell, e.g. the compiler and build line).
set -euo pipefail

HOST=${1:?usage: run_sweep_f_vs_lem.sh HOST [num_sets=100] [hot_reps=200] [list]}
NUM_SETS=${2:-100}
HOT_REPS=${3:-200}
LIST=${4:-pi5_runs/sweep_n_list_f_vs_lem.txt}
BIN="${FVL_BIN:-./bench_sweep_f_vs_lem}"
RUNS="${FVL_RUNS:-1 2 3 4 5 6 7 8 9 10}"
PREFIX="${FVL_PREFIX:-sweep_fvl3}"
OUTDIR=${HOST}_runs
mkdir -p "$OUTDIR"

if [[ ! -f "$BIN" ]]; then
  echo "missing $BIN -- build first (see the header of bench_sweep_f_vs_lem.cpp)" >&2
  exit 1
fi
if [[ ! -f "$LIST" ]]; then
  echo "missing size list $LIST" >&2
  exit 1
fi

PIN=()
cpu=0
if [[ "${FVL_CPU:-}" != "none" ]] && command -v taskset >/dev/null 2>&1; then
  ncpu=$(nproc 2>/dev/null || echo 1)
  cpu=${FVL_CPU:-$((ncpu - 1))}
  PIN=(taskset -c "$cpu")
fi

governor() {
  local f=/sys/devices/system/cpu/cpu${cpu}/cpufreq/scaling_governor
  [[ -r $f ]] && cat "$f" || echo unknown
}
temp_c() {
  if command -v vcgencmd >/dev/null 2>&1; then
    vcgencmd measure_temp 2>/dev/null | sed 's/temp=//; s/.C$//' ; return
  fi
  local z
  for z in /sys/class/thermal/thermal_zone*; do
    [[ -r $z/type ]] || continue
    case "$(cat "$z/type")" in
      x86_pkg_temp|cpu-thermal|cpu_thermal|soc_thermal)
        awk '{printf "%.1f", $1/1000}' "$z/temp"; return ;;
    esac
  done
  echo unknown
}

NS=$(cat "$LIST")
N_COUNT=$(wc -l <"$LIST" | tr -d ' ')
MODES="hb hs cb cs"
N_RUNS=$(wc -w <<<"$RUNS")
TOTAL=$(( N_COUNT * 4 * N_RUNS ))
DONE=0
FAILED=0
T0=$SECONDS

echo "bench_sweep_f_vs_lem campaign ${PREFIX} on ${HOST} ($(hostname)): ${N_COUNT} sizes x 4 modes x ${N_RUNS} runs = ${TOTAL} cells; num_sets=${NUM_SETS} hot_reps=${HOT_REPS} cpu=${cpu} bin=${BIN} governor=$(governor) temp_c=$(temp_c)"

# Outer loop over runs, inner over modes, innermost over N, as in the
# per-host drivers: each run's measurements are spread across the whole
# campaign so thermal and background drift average out across runs.
for R in $RUNS; do
  for MODE in $MODES; do
    for N in $NS; do
      OUT="$OUTDIR/${PREFIX}_n${N}_${MODE}_run${R}.txt"
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
        echo "# host: $HOST"
        echo "# machine: $(hostname)"
        echo "# date: $(date -Is)"
        echo "# governor: $(governor)"
        echo "# temp_c: $(temp_c)"
        echo "# command: ${PIN[*]:-} $BIN $N $MODE $NUM_SETS $HOT_REPS $R"
        if [[ -n "${FVL_NOTE:-}" ]]; then echo "# note: $FVL_NOTE"; fi
      } >"$OUT"
      if ! "${PIN[@]}" "$BIN" "$N" "$MODE" "$NUM_SETS" "$HOT_REPS" "$R" >>"$OUT" 2>&1; then
        echo "# FAILED exit $?" >>"$OUT"
        FAILED=$((FAILED + 1))
        echo "  cell failed: $OUT" >&2
      fi
    done
  done
done

echo "sweep complete: $TOTAL cells in $((SECONDS - T0))s, $FAILED failed"

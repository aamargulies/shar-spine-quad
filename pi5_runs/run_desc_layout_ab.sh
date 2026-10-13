#!/usr/bin/env bash
# Descriptor-layout A/B of the F-vs-Lemire sweep harness: the same five
# variants (F, Lem, Lem2, Fb, LemS) with the 48-byte descriptor of the
# archived campaigns (desc_align=16) and with a line-aligned 64-byte
# descriptor (desc_align=64), run back to back per cell, alternating which
# binary goes first. Cells: lay16_n<N>_<mode>_run<R>.txt / lay64_... in OUTDIR.
set -euo pipefail
OUTDIR=${OUTDIR:-pi5_runs}
B16=${B16:-./bench_sweep_fvl_desc16}
B64=${B64:-./bench_sweep_fvl_desc64}
CPU=${CPU:-3}
RUNS=${RUNS:-"1 2 3 4 5"}
SIZES=${SIZES:-"16 32 64 96 128 160 200 255 256 333 512 1024 2048 4096"}
MODES="hb hs cb cs"
NUM_SETS=${NUM_SETS:-100}
HOT_REPS=${HOT_REPS:-200}
mkdir -p "$OUTDIR"
temp_c() { awk '{printf "%.1f", $1/1000}' /sys/class/thermal/thermal_zone0/temp; }
T0=$SECONDS
for R in $RUNS; do
  for MODE in $MODES; do
    for N in $SIZES; do
      if (( R % 2 == 1 )); then ORDER="16 64"; else ORDER="64 16"; fi
      for L in $ORDER; do
        if [[ $L == 16 ]]; then BIN=$B16; else BIN=$B64; fi
        OUT="$OUTDIR/lay${L}_n${N}_${MODE}_run${R}.txt"
        {
          echo "# host: pi5"
          echo "# machine: $(hostname)"
          echo "# date: $(date -Is)"
          echo "# governor: $(cat /sys/devices/system/cpu/cpu${CPU}/cpufreq/scaling_governor)"
          echo "# temp_c: $(temp_c)"
          echo "# command: taskset -c $CPU $BIN $N $MODE $NUM_SETS $HOT_REPS $R"
          taskset -c "$CPU" "$BIN" "$N" "$MODE" "$NUM_SETS" "$HOT_REPS" "$R"
        } > "$OUT" 2>&1 || echo "# FAILED exit $?" >> "$OUT"
      done
    done
    echo "run $R mode $MODE done, elapsed $((SECONDS - T0))s, temp $(temp_c)"
  done
done
echo "layout A/B complete in $((SECONDS - T0))s"

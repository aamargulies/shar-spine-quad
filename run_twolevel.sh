#!/usr/bin/env bash
# Driver for repeated bench_twolevel runs with randomised timing order.
#
# Usage: ./run_twolevel.sh HOST RUNS [BINARY] [NUM_SETS] [HOT_REPS]
#   HOST      pi5 | m4 | m1 | skx | emr | gv4   (selects HOST_runs/)
#   RUNS      number of runs (10 recommended; 5 cannot reach p < 0.0625)
#   BINARY    harness binary (default ./bench_twolevel)
#   NUM_SETS  default 200
#   HOT_REPS  default 200
#
# Each run R writes HOST_runs/twolevel_v2_runR.txt with order_seed=R so the
# variants are timed in a different order every run (see bench_twolevel.cpp).
# Existing twolevel_run*.txt archives are never touched: the "v2" files are
# the post-2026-10-11 harness (corrected Eytzinger prefetch, warm-up pass,
# randomised order, 512 MB thrash) and are not comparable to the old ones
# for variants H and I.
#
# Environment: TWOLEVEL_CPU pins the harness to one core on Linux hosts
# that have taskset (default: last core). Set TWOLEVEL_CPU=none to disable.
# TWOLEVEL_FIRST (default 1) is the index of the first run, so a long
# campaign can be split into batches: TWOLEVEL_FIRST=6 ./run_twolevel.sh pi5 5
# The governor and SoC temperature are recorded as "# key: value" lines at
# the top of each file when the host exposes them (Linux / Raspberry Pi).
#
# Aggregate with:  python3 compute_twolevel_paired.py HOST --glob 'HOST_runs/twolevel_v2_run*.txt'
set -euo pipefail

HOST=${1:?usage: run_twolevel.sh HOST RUNS [BINARY] [NUM_SETS] [HOT_REPS]}
RUNS=${2:?usage: run_twolevel.sh HOST RUNS [BINARY] [NUM_SETS] [HOT_REPS]}
BIN=${3:-./bench_twolevel}
SETS=${4:-200}
REPS=${5:-200}
OUTDIR=${HOST}_runs
mkdir -p "$OUTDIR"

PIN=()
if [[ "${TWOLEVEL_CPU:-}" != "none" ]] && command -v taskset >/dev/null 2>&1; then
    ncpu=$(nproc 2>/dev/null || echo 1)
    cpu=${TWOLEVEL_CPU:-$((ncpu - 1))}
    PIN=(taskset -c "$cpu")
fi

FIRST=${TWOLEVEL_FIRST:-1}
LAST=$((FIRST + RUNS - 1))
for R in $(seq "$FIRST" "$LAST"); do
    out="$OUTDIR/twolevel_v2_run${R}.txt"
    {
        echo "# date: $(date -Iseconds)"
        echo "# host: $(uname -srm)"
        echo "# command: ${PIN[*]:-} $BIN $SETS $REPS all $R"
        if [[ -r /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]]; then
            echo "# governor: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)"
        fi
        if command -v vcgencmd >/dev/null 2>&1; then
            echo "# temp_before: $(vcgencmd measure_temp 2>/dev/null | tr -d 'temp=')"
        fi
        "${PIN[@]}" "$BIN" "$SETS" "$REPS" all "$R"
        if command -v vcgencmd >/dev/null 2>&1; then
            echo "# temp_after: $(vcgencmd measure_temp 2>/dev/null | tr -d 'temp=')"
        fi
    } > "$out"
    echo "run $R (of $FIRST..$LAST) -> $out"
done

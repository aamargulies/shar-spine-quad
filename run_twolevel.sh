#!/usr/bin/env bash
# Driver for repeated bench_twolevel runs with randomised timing order.
#
# Usage: ./run_twolevel.sh HOST RUNS [BINARY] [NUM_SETS] [HOT_REPS]
#   HOST      pi5 | m4 | m1 | skx | emr | gv4 | cfl   (selects HOST_runs/)
#   RUNS      number of runs (10 recommended; 5 cannot reach p < 0.0625)
#   BINARY    harness binary (default ./bench_twolevel)
#   NUM_SETS  default 200
#   HOT_REPS  default 200
#
# Each run R writes HOST_runs/twolevel_v2${TWOLEVEL_TAG}_runR.txt with
# order_seed=R so the variants are timed in a different order every run (see
# bench_twolevel.cpp). Existing twolevel_run*.txt archives are never touched:
# the "v2" files are the post-2026-10-11 harness (corrected Eytzinger
# prefetch, warm-up pass, randomised order, 512 MB thrash) and are not
# comparable to the old ones for variants H and I. An existing output file is
# never overwritten (the run is skipped).
#
# Environment: TWOLEVEL_CPU pins the harness to one core on Linux hosts
# that have taskset (default: last core). Set TWOLEVEL_CPU=none to disable.
# TWOLEVEL_FIRST (default 1) is the index of the first run, so a long
# campaign can be split into batches: TWOLEVEL_FIRST=6 ./run_twolevel.sh pi5 5
# TWOLEVEL_TAG is inserted into the file name (e.g. _noturbo for a second
# set on the same host under a different clock setting); TWOLEVEL_NOTE is
# written as a '# note: ...' header line. The governor, the machine name and
# the CPU temperature (vcgencmd on the Pi, else the x86_pkg_temp /
# cpu-thermal zone) are recorded as "# key: value" lines at the top of each
# file when the host exposes them.
#
# Aggregate with:  python3 compute_twolevel_paired.py HOST --glob 'HOST_runs/twolevel_v2_run*.txt'
set -euo pipefail

HOST=${1:?usage: run_twolevel.sh HOST RUNS [BINARY] [NUM_SETS] [HOT_REPS]}
RUNS=${2:?usage: run_twolevel.sh HOST RUNS [BINARY] [NUM_SETS] [HOT_REPS]}
BIN=${3:-./bench_twolevel}
SETS=${4:-200}
REPS=${5:-200}
OUTDIR=${HOST}_runs
TAG=${TWOLEVEL_TAG:-}
mkdir -p "$OUTDIR"

PIN=()
cpu=0
if [[ "${TWOLEVEL_CPU:-}" != "none" ]] && command -v taskset >/dev/null 2>&1; then
    ncpu=$(nproc 2>/dev/null || echo 1)
    cpu=${TWOLEVEL_CPU:-$((ncpu - 1))}
    PIN=(taskset -c "$cpu")
fi

temp_c() {
    if command -v vcgencmd >/dev/null 2>&1; then
        vcgencmd measure_temp 2>/dev/null | tr -d 'temp=' ; return
    fi
    local z
    for z in /sys/class/thermal/thermal_zone*; do
        [[ -r $z/type ]] || continue
        case "$(cat "$z/type")" in
            x86_pkg_temp|cpu-thermal|cpu_thermal|soc_thermal)
                awk '{printf "%.1f'\''C", $1/1000}' "$z/temp"; return ;;
        esac
    done
    echo unknown
}

FIRST=${TWOLEVEL_FIRST:-1}
LAST=$((FIRST + RUNS - 1))
for R in $(seq "$FIRST" "$LAST"); do
    out="$OUTDIR/twolevel_v2${TAG}_run${R}.txt"
    if [[ -e "$out" ]]; then
        echo "skip $out (exists; archived run files are never overwritten)"
        continue
    fi
    {
        echo "# date: $(date -Iseconds)"
        echo "# host: $(uname -srm)"
        echo "# machine: $(hostname)"
        echo "# command: ${PIN[*]:-} $BIN $SETS $REPS all $R"
        if [[ -r /sys/devices/system/cpu/cpu${cpu}/cpufreq/scaling_governor ]]; then
            echo "# governor: $(cat /sys/devices/system/cpu/cpu${cpu}/cpufreq/scaling_governor)"
        fi
        if [[ -n "${TWOLEVEL_NOTE:-}" ]]; then echo "# note: $TWOLEVEL_NOTE"; fi
        echo "# temp_before: $(temp_c)"
        "${PIN[@]}" "$BIN" "$SETS" "$REPS" all "$R"
        echo "# temp_after: $(temp_c)"
    } > "$out"
    echo "run $R (of $FIRST..$LAST) -> $out"
done

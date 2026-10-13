#!/usr/bin/env bash
# Driver for repeated flushed main-bench runs (bench.cpp with the 2026-10-11
# cold flush and, since 2026-10-12, the 'nA' aligned rows).
#
# Usage: ./run_bench_flushed.sh HOST RUNS [BINARY] [ARGS]
#   HOST      pi5 | m4 | m1 | skx | emr | gv4 | cfl ...   (selects HOST_runs/)
#   RUNS      number of runs (10 recommended)
#   BINARY    bench binary (default ./bench; build it on local disk)
#   ARGS      bench arguments (default "4000 5000", the canonical intensity)
#
# Run R writes HOST_runs/rebench_flushed${BENCH_TAG}_run${R}.txt:
#   # date / host / machine / command / build / compiler / governor / temp_before
#   <bench stdout>
#   # exit: <status>
#   # temp_after
# in the format of pi5_runs/rebench_flushed_run1.txt (2026-10-12). An existing
# run file is never overwritten (the run is skipped).
#
# Environment: BENCH_CPU pins the bench to one core on hosts that have taskset
# (default: last core; BENCH_CPU=none disables). BENCH_FIRST (default 1) is
# the index of the first run. BENCH_TAG is inserted into the file name (e.g.
# _eight for runs on the second Pi 5 board, _noturbo for a second set under a
# different clock setting); BENCH_NOTE is written as a '# note: ...' line.
# BENCH_BUILD is the text of the
# '# build:' line (default: the host's build line from bench.cpp's header);
# BENCH_COMPILER that of '# compiler:' (default `g++ --version`; set it when
# the binary was built elsewhere). The temperature comes from vcgencmd (Pi)
# or the x86_pkg_temp / cpu-thermal thermal zone when the host has one.
#
# Aggregate with:  python3 compute_bench_paired.py HOST
set -euo pipefail

HOST=${1:?usage: run_bench_flushed.sh HOST RUNS [BINARY] [ARGS]}
RUNS=${2:?usage: run_bench_flushed.sh HOST RUNS [BINARY] [ARGS]}
BIN=${3:-./bench}
ARGS=${4:-"4000 5000"}
OUTDIR=${HOST}_runs
mkdir -p "$OUTDIR"

if [[ ! -f "$BIN" ]]; then
  echo "missing $BIN -- build first (see the header of bench.cpp)" >&2
  exit 1
fi

PIN=()
if [[ "${BENCH_CPU:-}" != "none" ]] && command -v taskset >/dev/null 2>&1; then
  ncpu=$(nproc 2>/dev/null || echo 1)
  cpu=${BENCH_CPU:-$((ncpu - 1))}
  PIN=(taskset -c "$cpu")
fi
BUILD="${BENCH_BUILD:-see the build lines in bench.cpp (host $HOST)}"
COMPILER="${BENCH_COMPILER:-$(g++ --version 2>/dev/null | head -1)}"
TAG="${BENCH_TAG:-}"

governor() {
  local f=/sys/devices/system/cpu/cpu${cpu:-0}/cpufreq/scaling_governor
  [[ -r $f ]] && cat "$f" || echo unknown
}
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

FIRST=${BENCH_FIRST:-1}
LAST=$((FIRST + RUNS - 1))
for R in $(seq "$FIRST" "$LAST"); do
  OUT="$OUTDIR/rebench_flushed${TAG}_run${R}.txt"
  if [[ -e "$OUT" ]]; then
    echo "skip $OUT (exists; archived run files are never overwritten)"
    continue
  fi
  echo "run $R (of $FIRST..$LAST) -> $OUT  ($(date -Is), governor $(governor), $(temp_c))"
  {
    echo "# date: $(date -Iseconds)"
    echo "# host: $(uname -srm)"
    echo "# machine: $(hostname)"
    echo "# command: ${PIN[*]:-} $BIN $ARGS"
    echo "# build: $BUILD"
    echo "# compiler: $COMPILER"
    echo "# governor: $(governor)"
    if [[ -n "${BENCH_NOTE:-}" ]]; then echo "# note: $BENCH_NOTE"; fi
    echo "# temp_before: $(temp_c)"
    set +e
    "${PIN[@]}" "$BIN" $ARGS
    echo "# exit: $?"
    set -e
    echo "# temp_after: $(temp_c)"
  } > "$OUT" 2>&1
  echo "  done ($(date -Is), $(temp_c))"
done

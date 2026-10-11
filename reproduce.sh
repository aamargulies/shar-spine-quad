#!/usr/bin/env bash
#
# reproduce.sh — one-shot build + bench + spot-check for SIMD Quad results.
#
# Auto-detects the host microarchitecture (Pi 5 / M4 Max / M1 Pro /
# Skylake-SP / Emerald Rapids / Graviton 4 / generic fallback), picks the
# right compiler flags, builds bench + bench_twolevel, runs each, and diffs
# the key rows against archived per-host five-run medians.
#
# Usage:
#   ./reproduce.sh            # build, run once, compare to archived medians
#   ./reproduce.sh --runs 5   # 5 runs; report the per-cell median across runs
#   ./reproduce.sh --quick    # 2000x2000 intensity instead of 4000x5000
#
# Each bench_twolevel run i is invoked as `./bench_twolevel 200 200 all i`
# (default sets / reps, all four modes); the run index is passed as the
# harness's fourth argument, order_seed, so the variants are timed in a
# different order every run and a transient (governor hop, interrupt,
# thermal event) cannot land on the same variant each time.
#
# Logs: reproduce_bench.log and reproduce_twolevel.log, overwritten on
# every invocation, one "--- run N ---" block per run; both are gitignored.
# Logs produced before 2026-05-13 use the retired 2-column (warm/cold)
# two-level format; the parser below reports '-' for them instead of a number.
#
# Exit 0 on success (benches run, correctness ok). Any failure prints a
# diagnostic. The script does not try to "pass" a pattern match against
# archived numbers — memory-hierarchy variance across machines of the same
# microarchitecture is real and expected. It prints measured vs archived
# side by side and lets you judge.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

NUM_RUNS=1
INTENSITY=("4000" "5000")

while [[ $# -gt 0 ]]; do
    case "$1" in
        --runs) NUM_RUNS="$2"; shift 2 ;;
        --quick) INTENSITY=("2000" "2000"); shift ;;
        -h|--help)
            # Print the leading comment block (everything up to the first
            # non-comment line), minus the shebang.
            awk 'NR == 1 { next } /^#/ { print; next } { exit }' "$0"
            exit 0
            ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

# --- host detection ------------------------------------------------------

uname_m="$(uname -m)"
uname_s="$(uname -s)"
host_tag="generic"
cpu_flag=""
cxx="${CXX:-}"

if [[ "$uname_s" == "Darwin" && "$uname_m" == "arm64" ]]; then
    cxx="${cxx:-clang++}"
    brand="$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo '')"
    case "$brand" in
        *M4*) host_tag="m4";  cpu_flag="-mcpu=apple-m4" ;;
        *M3*) host_tag="m4";  cpu_flag="-mcpu=apple-m3" ;;  # use M4 variant
        *M2*) host_tag="m4";  cpu_flag="-mcpu=apple-m2" ;;
        *M1*) host_tag="m1";  cpu_flag="-mcpu=apple-m1" ;;
        *)    host_tag="apple-unknown"; cpu_flag="-mcpu=apple-m1" ;;
    esac
elif [[ "$uname_m" == "aarch64" ]]; then
    cxx="${cxx:-g++}"
    part_id="$(awk '/CPU part/ {print $NF; exit}' /proc/cpuinfo 2>/dev/null || echo '')"
    case "$part_id" in
        0xd0b) host_tag="pi5"; cpu_flag="-mcpu=cortex-a76" ;;   # Cortex-A76
        0xd4f) host_tag="gv4"; cpu_flag="-mcpu=neoverse-v2" ;;  # Neoverse V2
        *)
            model="$(awk -F: '/model name/ {print $2; exit}' /proc/cpuinfo)"
            case "$model" in
                *Neoverse-V2*|*"Neoverse V2"*) host_tag="gv4"; cpu_flag="-mcpu=neoverse-v2" ;;
                *Cortex-A76*)                  host_tag="pi5"; cpu_flag="-mcpu=cortex-a76" ;;
                *)                             host_tag="arm-unknown"; cpu_flag="-mcpu=native" ;;
            esac
            ;;
    esac
elif [[ "$uname_m" == "x86_64" ]]; then
    cxx="${cxx:-g++}"
    family_model="$(awk '/family/ {f=$NF} /model\t/ {m=$NF; print f"_"m; exit}' /proc/cpuinfo 2>/dev/null || echo '')"
    case "$family_model" in
        6_85)   host_tag="skx"; cpu_flag="-march=native" ;;  # Skylake-SP (family 6 model 85)
        6_207)  host_tag="emr"; cpu_flag="-march=native" ;;  # Emerald Rapids (family 6 model 207)
        6_143)  host_tag="emr"; cpu_flag="-march=native" ;;  # Sapphire Rapids, same codepath as EMR
        *)
            # Fallback: rely on -march=native. Prints the flags in the summary so
            # the operator can eyeball what it picked.
            host_tag="x86-unknown"; cpu_flag="-march=native"
            ;;
    esac
else
    echo "unsupported host: $uname_s $uname_m" >&2
    exit 3
fi

echo "==> host: $host_tag  ($uname_s $uname_m, $cpu_flag, $cxx)"

# --- build ---------------------------------------------------------------

common_sources_arm=(bench.cpp simd_quad_pi5.c simd_quad_m4.c simd_quad_graviton.c)
common_sources_x86=(bench.cpp simd_quad_intel.c)

case "$host_tag" in
    pi5|m4|m1|gv4|apple-unknown|arm-unknown) sources=("${common_sources_arm[@]}") ;;
    skx|emr|x86-unknown)                     sources=("${common_sources_x86[@]}") ;;
esac

echo "==> build bench"
"$cxx" -O3 "$cpu_flag" -std=c++20 "${sources[@]}" -o bench

echo "==> build bench_twolevel"
case "$host_tag" in
    pi5)       "$cxx" -O3 "$cpu_flag" -std=c++20 -DQUADSEARCH_ARM_PI5 bench_twolevel.cpp simd_quad_pi5.c        -o bench_twolevel ;;
    m4|m1)     "$cxx" -O3 "$cpu_flag" -std=c++20                       bench_twolevel.cpp simd_quad_m4.c         -o bench_twolevel ;;
    gv4)       "$cxx" -O3 "$cpu_flag" -std=c++20 -DQUADSEARCH_ARM_GV4  bench_twolevel.cpp simd_quad_graviton.c   -o bench_twolevel ;;
    skx|emr)   "$cxx" -O3 "$cpu_flag" -std=c++20                       bench_twolevel.cpp simd_quad_intel.c      -o bench_twolevel ;;
    *)         echo "==> skipping bench_twolevel on $host_tag (no variant mapping)"; ;;
esac

# --- run -----------------------------------------------------------------

run_one () {
    local bin="$1"; shift
    "./$bin" "$@"
}

echo "==> bench  ./bench ${INTENSITY[*]}  (${NUM_RUNS} run(s))"
for i in $(seq 1 "$NUM_RUNS"); do
    echo "--- run $i ---"
    run_one bench "${INTENSITY[@]}"
done | tee reproduce_bench.log

if [[ -x ./bench_twolevel ]]; then
    # Default sets / reps, all four modes; the run index is the harness's
    # order_seed (4th argv) so each run times the variants in a different order.
    echo "==> bench_twolevel  ./bench_twolevel 200 200 all <run>  (${NUM_RUNS} run(s), order_seed = run index)"
    for i in $(seq 1 "$NUM_RUNS"); do
        echo "--- run $i ---"
        run_one bench_twolevel 200 200 all "$i"
    done | tee reproduce_twolevel.log
fi

# --- archived-median comparison ------------------------------------------

python3 - "$host_tag" "$ROOT/reproduce_bench.log" "${ROOT}/reproduce_twolevel.log" "$NUM_RUNS" << 'PY'
import re, sys, pathlib, statistics
host, bench_log, twolevel_log = sys.argv[1], sys.argv[2], sys.argv[3]
num_runs = int(sys.argv[4]) if len(sys.argv) > 4 else 1

# Archived per-host five-run medians (ns/q) for the cells most worth checking.
# Recomputed 2026-10-11 from the raw run files that exist in the repo; this
# supersedes the 2026-05-01 plot.py snapshot the script carried before (whose
# two-level pairs came from the retired 2-mode harness, see the HISTORY note
# above bench_cold_batched in bench_twolevel.cpp, and whose Pi 5 main-bench
# set has since been overwritten).
#
#   main bench, n=4096:  median over {host}_runs/rebench_run{1..5}.txt of the
#       LAST `4096*` A/B row in each run. In that row `<v>_spine=` is the very
#       same measurement as the `<v>s` table column at n=4096 (bench.cpp prints
#       w[4]/c[4], or w[6]/c[6] for m4, at two decimals instead of one), and
#       `<v>_spine_4096=` is the compile-time n=4096 specialization. On ARM the
#       Pi 5 row appears twice per run (per-size family block, then the
#       dedicated cross-host row); the dedicated (last) one is used, exactly as
#       {host}_runs/compute_medians.py does.
#   two-level F:  per-cell medians -- LEVELS, not paired deltas -- of the F row
#       across {host}_runs/twolevel_run{1..5}.txt, as printed in
#       {host}_runs/twolevel_summary.txt (4-mode harness, 2026-05-18), modes
#       hot_bat / hot_ser / cold_bat / cold_ser. Whole runs drift 1.4-2.2x on
#       some hosts, so these levels are a sanity check only; any X-vs-Y question
#       needs the paired per-run deltas (compute_twolevel_paired.py).
#
# Any re-measurement on the same microarchitecture should land within ~2-10%
# warm, ~5-25% cold (Pi 5 two-level levels: up to ~2x run-to-run, see
# pi5_runs/twolevel_paired.txt).
archived = {
    # Pi 5 (Cortex-A76). Main bench: rebench_run{1..5}.txt dated 2026-05-12,
    # taken after the hybrid A/B of the same day (pi5_runs/hybrid_summary.txt),
    # so pi5_spine_4096 is the shipped hybrid: its medians (15.98 / 111.85)
    # equal plot.py's pi5_spine_4096 entry. Two-level: twolevel_summary.txt,
    # 2026-05-18.
    "pi5": {
        "n=4096 warm pi5+spine":          22.46,
        "n=4096 cold pi5+spine":         150.74,
        "n=4096 warm pi5_spine_4096":     15.98,
        "n=4096 cold pi5_spine_4096":    111.85,
        "twolevel F hot_bat":            244.40,
        "twolevel F hot_ser":            328.50,
        "twolevel F cold_bat":          1591.57,
        "twolevel F cold_ser":          1547.03,
    },
    # Apple M4 Max. Main bench: rebench_run{1..5}.txt dated 2026-05-01, which
    # predates the hybrid A/B (m4_runs/hybrid_summary.txt, 2026-05-12), so
    # m4_spine_4096 there is the retired unroll shape. Two-level:
    # twolevel_summary.txt, 2026-05-18.
    "m4": {
        "n=4096 warm m4+spine":            4.34,
        "n=4096 cold m4+spine":            6.47,
        "n=4096 warm m4_spine_4096":       3.65,
        "n=4096 cold m4_spine_4096":      18.65,
        "twolevel F hot_bat":             13.25,
        "twolevel F hot_ser":             16.33,
        "twolevel F cold_bat":           161.88,
        "twolevel F cold_ser":           281.67,
    },
    # Apple M1 Pro (shares simd_quad_m4.c). Main bench: rebench_run{1..5}.txt
    # dated 2026-05-01, before the hybrid A/B (m1_runs/hybrid_run{1..5}.txt), so
    # m4_spine_4096 there is the retired unroll shape. Two-level:
    # twolevel_summary.txt, 2026-05-18.
    "m1": {
        "n=4096 warm m4+spine":            6.33,
        "n=4096 cold m4+spine":           11.05,
        "n=4096 warm m4_spine_4096":       6.16,
        "n=4096 cold m4_spine_4096":      32.70,
        "twolevel F hot_bat":             45.88,
        "twolevel F hot_ser":             79.26,
        "twolevel F cold_bat":           278.54,
        "twolevel F cold_ser":           776.46,
    },
    # Intel Skylake-SP (Xeon 8175M, AVX2 block-check path). Main bench:
    # rebench_run{1..5}.txt dated 2026-05-01, before the hybrid A/B
    # (skx_runs/hybrid_summary.txt, 2026-05-13), so intel_spine_4096 there is
    # the retired unroll shape. Two-level: twolevel_summary.txt, 2026-05-18.
    "skx": {
        "n=4096 warm intel+spine":        26.79,
        "n=4096 cold intel+spine":       132.65,
        "n=4096 warm intel_spine_4096":   27.11,
        "n=4096 cold intel_spine_4096":  122.98,
        "twolevel F hot_bat":             84.42,
        "twolevel F hot_ser":             83.72,
        "twolevel F cold_bat":           594.47,
        "twolevel F cold_ser":           826.85,
    },
    # Intel Emerald Rapids (Xeon 8559C, zmm block-check path). Main bench:
    # rebench_run{1..5}.txt dated 2026-05-01, before the hybrid A/B
    # (emr_runs/hybrid_summary.txt, 2026-05-12), so intel_spine_4096 there is
    # the retired unroll shape. Two-level: twolevel_summary.txt, 2026-05-18.
    "emr": {
        "n=4096 warm intel+spine":        17.98,
        "n=4096 cold intel+spine":        37.23,
        "n=4096 warm intel_spine_4096":   14.02,
        "n=4096 cold intel_spine_4096":   25.87,
        "twolevel F hot_bat":             55.43,
        "twolevel F hot_ser":             58.12,
        "twolevel F cold_bat":           240.31,
        "twolevel F cold_ser":           512.30,
    },
    # AWS Graviton 4 (Neoverse V2). Main bench: rebench_run{1..5}.txt dated
    # 2026-05-01, before the hybrid A/B (gv4_runs/hybrid_summary.txt,
    # 2026-05-12), so gv4_spine_4096 there is the retired unroll shape.
    # Two-level: twolevel_summary.txt, 2026-05-18.
    "gv4": {
        "n=4096 warm gv4+spine":          16.16,
        "n=4096 cold gv4+spine":          34.58,
        "n=4096 warm gv4_spine_4096":     14.67,
        "n=4096 cold gv4_spine_4096":     29.15,
        "twolevel F hot_bat":             65.37,
        "twolevel F hot_ser":             50.34,
        "twolevel F cold_bat":           268.45,
        "twolevel F cold_ser":           486.13,
    },
}
# Hosts whose archived <v>_spine_4096 cells come from files that predate the
# hybrid finish (every host ships the hybrid today).
PRE_HYBRID_4096 = {"m4", "m1", "skx", "emr", "gv4"}

if host not in archived:
    print(f"no archived medians for host tag '{host}'; measured numbers only.")
    sys.exit(0)

def read(p):
    try:
        return pathlib.Path(p).read_text()
    except FileNotFoundError:
        return ""

# Both logs are the concatenation of one "--- run N ---" block per run (written
# by the loops above). Every parser below takes ONE value per run block and
# reports the median across runs. A log without run markers (e.g. a raw
# archived {host}_runs/*_run1.txt) is treated as a single run.
RUN_MARKER = re.compile(r"^--- run \d+ ---\s*$", re.MULTILINE)

def split_runs(log):
    return [chunk for chunk in RUN_MARKER.split(log) if chunk.strip()]

def median_or_none(vals):
    vals = [v for v in vals if v is not None]
    return statistics.median(vals) if vals else None

# bench.cpp emits "4096*" A/B rows with this shape (example, ARM):
#   " 4096* | pi5_spine=22.37 pi5_spine_4096=15.93  (warm)  | pi5_spine=145.67 pi5_spine_4096=104.93  (cold)"
#   " 4096* |  m4_spine=4.40  m4_spine_4096=3.72  (warm)  |  m4_spine=7.11  m4_spine_4096=23.50  (cold)"
# and on x86:
#   " 4096* | intel_spine=26.48 intel_spine_4096=32.49  (warm)  | intel_spine=133.22 intel_spine_4096=122.98  (cold)"
# `<v>_spine=` is the general-n spine kernel (same number as the `<v>s` table
# column at n=4096); `<v>_spine_4096=` is the compile-time specialization. A
# run may print the row for a prefix more than once (per-size family block +
# dedicated cross-host row on ARM); the last one per run is the dedicated row.
# Rows for other prefixes (`gv4_spine_pad=`, other sizes' `_256=` ... `_2048=`)
# do not match because the prefix and `_4096=` are both required.
def parse_4096star(log, variant_prefix):
    """Median across runs of the last matching '4096*' row per run.
    Returns {'warm_spine','warm_4096','cold_spine','cold_4096','runs'} or None."""
    p = re.escape(variant_prefix)
    pat = re.compile(
        r"4096\*\s*\|\s*" + p + r"=([\d.]+)\s+" + p + r"_4096=([\d.]+)\s+\(warm\)\s*\|\s*"
        + p + r"=([\d.]+)\s+" + p + r"_4096=([\d.]+)\s+\(cold\)")
    per_run = []
    for chunk in split_runs(log):
        found = pat.findall(chunk)
        if found:
            per_run.append(tuple(float(x) for x in found[-1]))
    if not per_run:
        return None
    cols = list(zip(*per_run))
    return {"warm_spine": statistics.median(cols[0]), "warm_4096": statistics.median(cols[1]),
            "cold_spine": statistics.median(cols[2]), "cold_4096": statistics.median(cols[3]),
            "runs": len(per_run)}

# bench_twolevel variant-F row. Since 2026-05-13 the harness prints FOUR
# columns (hot_bat hot_ser cold_bat cold_ser), exact text from bench_twolevel.cpp
# ("%-4s  %-56s  %10.2f  %10.2f  %10.2f  %10.2f"):
#   "F     Shar branchless outer + compile-time n=4096 inner             213.86      216.10     1877.11     1856.18"
# A mode-restricted run (argv[3] = hb/hs/cb/cs) prints "nan" (or "-nan") in the
# modes it did not run; those cells are skipped. The anchored regex ignores
# everything else in the log: the header, "timing order <mode>: ..." lines, any
# "# key: value" comment lines a driver prepends (run_twolevel.sh), and the
# indented "  F   vs A:" delta lines. The retired pre-2026-05-13 2-column
# format has only two numbers and does not match -> reported as '-'.
MODES = ("hot_bat", "hot_ser", "cold_bat", "cold_ser")
F_ROW = re.compile(
    r"^F\s+Shar branchless outer \+ compile-time n=4096 inner\s+"
    r"(-?nan|\d+\.\d+)\s+(-?nan|\d+\.\d+)\s+(-?nan|\d+\.\d+)\s+(-?nan|\d+\.\d+)\s*$",
    re.MULTILINE)

def parse_twolevel_F(log):
    """Median across runs, per mode, of the variant-F row (one row per run).
    Returns {'hot_bat','hot_ser','cold_bat','cold_ser','runs'} or None."""
    per_run = []
    for chunk in split_runs(log):
        found = F_ROW.findall(chunk)
        if found:
            per_run.append(tuple(None if x.endswith("nan") else float(x) for x in found[-1]))
    if not per_run:
        return None
    out = {mode: median_or_none([r[i] for r in per_run]) for i, mode in enumerate(MODES)}
    out["runs"] = len(per_run)
    return out

bench_log_text = read(bench_log)
twolevel_log_text = read(twolevel_log)

# Variant-prefix per host for the 4096* parser.
variant_prefix = {
    "pi5": "pi5_spine", "m4": "m4_spine", "m1": "m4_spine",
    "gv4": "gv4_spine", "skx": "intel_spine", "emr": "intel_spine",
}.get(host)

parsed = parse_4096star(bench_log_text, variant_prefix) if variant_prefix else None
tl_F = parse_twolevel_F(twolevel_log_text)

def measured_for(metric):
    if metric.startswith("twolevel F "):
        return tl_F.get(metric.split()[-1]) if tl_F else None
    if parsed is None:
        return None
    regime = "warm" if " warm " in metric else "cold"
    kind = "4096" if "_spine_4096" in metric else "spine"
    return parsed[f"{regime}_{kind}"]

def row(name, meas, arch):
    if meas is None:
        print(f"{name:<40s}  {'-':>10s}  {arch:>10.2f}  {'-':>10s}")
        return
    delta = (meas - arch) / arch * 100.0
    print(f"{name:<40s}  {meas:>10.2f}  {arch:>10.2f}  {delta:>+9.1f}%")

print()
print(f"runs found in logs: bench={parsed['runs'] if parsed else 0}  "
      f"twolevel={tl_F['runs'] if tl_F else 0}  (--runs {num_runs} requested); "
      "measured = per-cell median across the runs found")
print()
print(f"{'metric':<40s}  {'measured':>10s}  {'archived':>10s}  {'delta':>10s}")
print("-" * 76)
for metric, arch_val in archived[host].items():
    row(metric, measured_for(metric), arch_val)

print()
print("Notes:")
print("  - 'measured' is the per-cell median across the run blocks found in the")
print("    logs (last '4096*' A/B row of each run; the F row of each run).")
print("  - Warm deltas within ~10%, cold within ~25% are consistent with")
print("    measurement variance across machines of the same microarchitecture.")
print("  - Archived two-level numbers are per-cell medians (levels) of five runs")
print(f"    from {host}_runs/twolevel_summary.txt (2026-05-18); whole runs drift")
print("    1.4-2.2x on some hosts, so use compute_twolevel_paired.py, not these")
print("    levels, for any X-vs-Y comparison.")
print("  - Variants H/I in that archived 2026-05-18 two-level data were measured")
print("    with a mis-aimed Eytzinger prefetch, fixed 2026-10-11 (see the note in")
print("    bench_twolevel.cpp and KhuongMorin.md); a fresh run's H/I rows are not")
print("    expected to match them. Only the F row is compared here.")
if host in PRE_HYBRID_4096:
    print(f"  - The archived {variant_prefix}_4096 cells for '{host}' come from")
    print("    2026-05-01 files that predate the hybrid finish (shipped 2026-05-12/13;")
    print(f"    see {host}_runs/hybrid_*). Today's binary runs the hybrid, so a lower")
    print("    fresh warm number there is the expected win, not a regression.")
print("  - Visible aliasing bumps in the per-n curves are real and expected;")
print("    see Text/aliasing_investigation.md.")
print("  - Logs produced before 2026-05-13 use the retired 2-column (warm/cold)")
print("    two-level format, whose cold path never ran")
print("    the inner search; the two-level rows show '-' for such a log.")
print("  - Parsing of the bench table is heuristic; if a row shows '-', open")
print("    reproduce_bench.log / reproduce_twolevel.log and read the table.")
PY

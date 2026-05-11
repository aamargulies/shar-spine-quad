#!/usr/bin/env bash
#
# reproduce.sh — one-shot build + bench + spot-check for SIMD Quad results.
#
# Auto-detects the host microarchitecture (Pi 5 / M4 Max / M1 Pro /
# Skylake-SP / Emerald Rapids / Graviton 4 / generic fallback), picks the
# right compiler flags, builds bench + bench_twolevel, runs each, and diffs
# the key rows against archived per-host medians.
#
# Usage:
#   ./reproduce.sh            # build, run once, compare to archived medians
#   ./reproduce.sh --runs 5   # 5 runs, report per-cell median
#   ./reproduce.sh --quick    # 2000x2000 intensity instead of 4000x5000
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
            grep '^#' "$0" | head -20
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
    echo "==> bench_twolevel  ./bench_twolevel  (${NUM_RUNS} run(s))"
    for i in $(seq 1 "$NUM_RUNS"); do
        echo "--- run $i ---"
        ./bench_twolevel
    done | tee reproduce_twolevel.log
fi

# --- archived-median comparison ------------------------------------------

python3 - "$host_tag" "$ROOT/reproduce_bench.log" "${ROOT}/reproduce_twolevel.log" << 'PY'
import re, sys, pathlib
host, bench_log, twolevel_log = sys.argv[1], sys.argv[2], sys.argv[3]

# Archived per-host medians (ns/q) for the cells most worth checking.
# Numbers come from plot.py at 2026-05-01; any re-measurement on the same
# microarchitecture should land within ~2-10% warm, ~5-25% cold.
archived = {
    "pi5": {
        "n=4096 warm pi5+spine": 23.8,
        "n=4096 cold pi5+spine": 138.4,
        "twolevel F warm":       260.46,  # note: F-warm was flat on Pi 5
        "twolevel F cold":        33.05,
    },
    "m4": {
        "n=4096 warm m4+spine":  4.34,
        "n=4096 cold m4+spine":  6.47,
        "n=4096 warm m4_4096":   3.65,
        "n=4096 cold m4_4096":  18.65,
        "twolevel F warm":      13.61,
        "twolevel F cold":       7.08,
    },
    "m1": {
        "n=4096 warm m4+spine":  6.31,
        "n=4096 cold m4+spine": 11.1,
        "twolevel F warm":      54.4,
        "twolevel F cold":      11.5,
    },
    "skx": {
        "n=4096 warm intel+spine": 27.50,
        "n=4096 cold intel+spine": 131.1,
        "twolevel F warm":          91.16,
        "twolevel F cold":          26.90,
    },
    "emr": {
        "n=4096 warm intel+spine": 18.0,
        "n=4096 cold intel+spine": 37.2,
        "twolevel F warm":         72.55,
        "twolevel F cold":         16.98,
    },
    "gv4": {
        "n=4096 warm gv4+spine":   16.2,
        "n=4096 cold gv4+spine":   34.6,
        "twolevel F warm":         73.74,
        "twolevel F cold":         14.66,
    },
}
if host not in archived:
    print(f"no archived medians for host tag '{host}'; measured numbers only.")
    sys.exit(0)

def read(p):
    try:
        return pathlib.Path(p).read_text()
    except FileNotFoundError:
        return ""

def measured_bench(log, pattern_warm, pattern_cold):
    """Find the last occurrence of pattern in the log and return (warm, cold)."""
    m_warm = list(re.finditer(pattern_warm, log))
    m_cold = list(re.finditer(pattern_cold, log))
    w = float(m_warm[-1].group(1)) if m_warm else None
    c = float(m_cold[-1].group(1)) if m_cold else None
    return w, c

bench_log_text = read(bench_log)
twolevel_log_text = read(twolevel_log)

print()
print(f"{'metric':<40s}  {'measured':>10s}  {'archived':>10s}  {'delta':>10s}")
print("-" * 76)

def row(name, meas, arch):
    if meas is None or arch is None:
        print(f"{name:<40s}  {str(meas or '-'):>10s}  {arch:>10.2f}  {'-':>10s}")
        return
    delta = (meas - arch) / arch * 100.0
    print(f"{name:<40s}  {meas:>10.2f}  {arch:>10.2f}  {delta:>+9.1f}%")

# Very approximate parsing. bench.cpp prints the per-n table with columns per
# algorithm; we pull the last-seen row of interest. The exact row header text
# depends on host (ARM has 9 cols, x86 has 5). For a reproduction script we
# just need a handful of "n=4096" rows.

# Row example on ARM:
#  4096 | ... simd_quad_m4 + spine       warm=4.3  cold=6.5 ...
#
# Row example on x86:
#  4096 | simd_quad_intel + spine  warm=27.1 cold=131.9
#
# The actual bench output uses a table layout; we scan for "4096*" and
# "simd_quad_{m4,pi5,gv4,intel} + spine" tokens. Robust parsing would need
# the bench source, so this scan is heuristic.

# bench.cpp emits a "4096*" row per-variant with this shape (example):
#   " 4096* |  m4_spine=23.14  m4_spine_4096=18.30  (warm)  |  m4_spine=130.86  m4_spine_4096=180.50  (cold)"
# The first token after "4096* |" names the variant whose "+ spine" number
# we archive. We pull the warm and cold columns for each variant-of-interest.
def parse_4096star(log, variant_prefix):
    pat = (
        r"4096\*\s*\|\s*" + re.escape(variant_prefix) + r"=([\d.]+)\s+"
        + re.escape(variant_prefix) + r"_4096=([\d.]+)\s+\(warm\)\s*\|\s*"
        + re.escape(variant_prefix) + r"=([\d.]+)\s+"
        + re.escape(variant_prefix) + r"_4096=([\d.]+)\s+\(cold\)"
    )
    m = list(re.finditer(pat, log))
    if not m:
        return None
    g = m[-1].groups()
    return {"warm_spine": float(g[0]), "warm_4096": float(g[1]),
            "cold_spine": float(g[2]), "cold_4096": float(g[3])}

# bench_twolevel variant-F row (exact text from bench_twolevel.cpp):
#   "F     Shar branchless outer + compile-time n=4096 inner             216.50       30.65"
def parse_twolevel_F(log):
    m = list(re.finditer(
        r"^F\s+.*?compile-time n=4096 inner\s+([\d.]+)\s+([\d.]+)\s*$",
        log, re.MULTILINE))
    if not m:
        return None
    w, c = m[-1].groups()
    return float(w), float(c)

# Variant-prefix per host for the 4096* parser.
variant_prefix = {
    "pi5": "pi5_spine", "m4": "m4_spine", "m1": "m4_spine",
    "gv4": "gv4_spine", "skx": "intel_spine", "emr": "intel_spine",
}.get(host)

parsed = parse_4096star(bench_log_text, variant_prefix) if variant_prefix else None
tl_F = parse_twolevel_F(twolevel_log_text)

for metric, arch_val in archived[host].items():
    if "twolevel F warm" in metric:
        row(metric, tl_F[0] if tl_F else None, arch_val)
    elif "twolevel F cold" in metric:
        row(metric, tl_F[1] if tl_F else None, arch_val)
    elif parsed is None:
        row(metric, None, arch_val)
    elif "warm" in metric and "spine" in metric and "_4096" not in metric and "m4_4096" not in metric:
        row(metric, parsed["warm_spine"], arch_val)
    elif "cold" in metric and "spine" in metric and "_4096" not in metric and "m4_4096" not in metric:
        row(metric, parsed["cold_spine"], arch_val)
    elif "warm" in metric and ("_4096" in metric or "m4_4096" in metric):
        row(metric, parsed["warm_4096"], arch_val)
    elif "cold" in metric and ("_4096" in metric or "m4_4096" in metric):
        row(metric, parsed["cold_4096"], arch_val)
    else:
        row(metric, None, arch_val)

print()
print("Notes:")
print("  - Warm deltas within ~10%, cold within ~25% are consistent with")
print("    measurement variance across machines of the same microarchitecture.")
print("  - Visible aliasing bumps in the per-n curves are real and expected;")
print("    see aliasing_investigation.md.")
print("  - Parsing of the bench table is heuristic; if a row shows '-', open")
print("    reproduce_bench.log / reproduce_twolevel.log and read the table.")
PY

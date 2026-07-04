#!/usr/bin/env python3
"""Compute per-cell medians across emr_runs/shipped_run{1..5}.txt.

Post-hybrid-promotion shape: intel_spine_4096 now = the hybrid
(3 quat + branchless 2-probe finish) after the 2026-05-12 EMR ship call.

Rows parsed:
 - Main table rows:  size | 5 warm floats | 5 cold floats
 - Pad A/B rows:     size* | intel_spine=X intel_spine_pad=Y ...
 - Spine_N ship rows: size* | intel_spine=X intel_spine_<N>=Y ...

Writes shipped_summary.txt.
"""
import re
import statistics
from pathlib import Path

HERE = Path(__file__).parent
RUNS = sorted(HERE.glob("shipped_run*.txt"))
assert len(RUNS) == 5, f"expected 5 runs, got {len(RUNS)}"

MAIN_RE = re.compile(
    r"^\s*(\d+)\s*\|"
    + r"\s+(\S+)" * 5
    + r"\s*\|"
    + r"\s+(\S+)" * 5
)
PAD_RE = re.compile(
    r"^\s*(\d+)\*\s*\|\s*intel_spine=(\S+)\s+intel_spine_pad=(\S+)\s*\(warm\)"
    r"\s*\|\s*intel_spine=\S+\s+intel_spine_pad=(\S+)\s*\(cold\)"
)
SHIPN_RE = re.compile(
    r"^\s*(\d+)\*\s*\|\s*intel_spine=(\S+)\s+intel_spine_(\d+)=(\S+)\s*\(warm\)"
    r"\s*\|\s*intel_spine=\S+\s+intel_spine_\d+=(\S+)\s*\(cold\)"
)

MAIN_COLS = ["linear", "binary", "simd", "intel", "intels"]

main_samples = {}
pad_samples = {}
shipN_samples = {}

for run_path in RUNS:
    with run_path.open() as f:
        for line in f:
            m = MAIN_RE.match(line)
            if m:
                size = int(m.group(1))
                vals_warm = [float(m.group(i + 2)) for i in range(5)]
                vals_cold = [float(m.group(i + 7)) for i in range(5)]
                entry = main_samples.setdefault(size, [[] for _ in range(10)])
                for i, v in enumerate(vals_warm):
                    entry[i].append(v)
                for i, v in enumerate(vals_cold):
                    entry[5 + i].append(v)
                continue
            m = PAD_RE.match(line)
            if m:
                size = int(m.group(1))
                pad_samples.setdefault(size, []).append(
                    (float(m.group(2)), float(m.group(3)), float(m.group(4)))
                )
                continue
            m = SHIPN_RE.match(line)
            if m:
                size = int(m.group(1))
                shipN_samples.setdefault(size, []).append(
                    (float(m.group(2)), float(m.group(4)), float(m.group(5)))
                )
                continue


def median(xs):
    return statistics.median(xs)


out = HERE / "shipped_summary.txt"
with out.open("w") as f:
    f.write("5-run medians of ./bench 4000 5000 on EMR (Xeon 8559C), "
            "2026-05-12. Raw: shipped_run{1..5}.txt.\n")
    f.write("Build: g++ -O3 -march=sapphirerapids -std=c++20 "
            "bench.cpp simd_quad_intel.c -o bench\n")
    f.write("intel_spine_4096 here is the shipped hybrid (3 quat + branchless "
            "2-probe finish) after the prior unroll was retired.\n\n")

    header = f"{'n':>5}  | " + " ".join(f"{c:>7}" for c in MAIN_COLS)
    f.write(header + "   warm  |  " + " ".join(f"{c:>7}" for c in MAIN_COLS) + "   cold\n")
    f.write("-" * (len(header) * 2 + 12) + "\n")
    for size in sorted(main_samples):
        row = main_samples[size]
        warms = [median(row[i]) for i in range(5)]
        colds = [median(row[5 + i]) for i in range(5)]
        f.write(f"{size:>5}  | " + " ".join(f"{v:>7.2f}" for v in warms)
                + "   warm  | " + " ".join(f"{v:>7.2f}" for v in colds) + "   cold\n")
        if size in pad_samples:
            samples = pad_samples[size]
            sw = median([s[0] for s in samples])
            pw = median([s[1] for s in samples])
            pc = median([s[2] for s in samples])
            f.write(f"{size:>5}* | intel_spine={sw:.2f} intel_spine_pad={pw:.2f}  (warm)"
                    f"  | intel_spine_pad={pc:.2f}  (cold)\n")
        if size in shipN_samples:
            samples = shipN_samples[size]
            sw = median([s[0] for s in samples])
            nw = median([s[1] for s in samples])
            nc = median([s[2] for s in samples])
            delta_w = (nw - sw) / sw * 100
            sc = median(main_samples[size][5 + 4])
            delta_c = (nc - sc) / sc * 100
            f.write(f"{size:>5}* | intel_spine_{size}:   warm {nw:.2f}  cold {nc:.2f}"
                    f"   (vs spine: {delta_w:+.1f}% warm / {delta_c:+.1f}% cold)\n")

print(f"wrote {out}")

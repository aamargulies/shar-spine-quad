#!/usr/bin/env python3
"""Compute per-cell medians across emr_runs/shipN_run{1..5}.txt.

Each run file is the unmodified output of `./bench 4000 5000` on EMR with
the new compile-time spine specializations wired in (intel_spine_{256,512,
1024,2048} plus intel_spine_4096_hybrid vs the existing intel_spine_4096).

Parses four kinds of rows:
 - Main table rows:
     `  size  | linear binary simd intel intels | cold ...`
 - Pad A/B rows:
     `  size* | intel_spine=X intel_spine_pad=Y  (warm)  | ... (cold)`
 - Spine_N ship rows (intel_spine_{256,512,1024,2048,4096}):
     `  size* | intel_spine=X intel_spine_<N>=Y  (warm)  | ... (cold)`
 - Hybrid A/B (at n=4096 only):
     `  4096* | intel_spine_4096=X intel_spine_4096_hybrid=Y (warm) | ... (cold)`

Writes:
 - shipN_summary.txt : human-readable 5-run median table.
"""
import re
import statistics
from pathlib import Path

HERE = Path(__file__).parent
RUNS = sorted(HERE.glob("shipN_run*.txt"))
assert len(RUNS) == 5, f"expected 5 runs, got {len(RUNS)}"

# Main row: size  | 5 warm floats | 5 cold floats
MAIN_RE = re.compile(
    r"^\s*(\d+)\s*\|"
    + r"\s+(\S+)" * 5
    + r"\s*\|"
    + r"\s+(\S+)" * 5
)
# Pad A/B row (gen-n spine vs padded-spine):
PAD_RE = re.compile(
    r"^\s*(\d+)\*\s*\|\s*intel_spine=(\S+)\s+intel_spine_pad=(\S+)\s*\(warm\)"
    r"\s*\|\s*intel_spine=\S+\s+intel_spine_pad=(\S+)\s*\(cold\)"
)
# Spine_N ship row: `intel_spine_<digits>=...`
SHIPN_RE = re.compile(
    r"^\s*(\d+)\*\s*\|\s*intel_spine=(\S+)\s+intel_spine_(\d+)=(\S+)\s*\(warm\)"
    r"\s*\|\s*intel_spine=\S+\s+intel_spine_\d+=(\S+)\s*\(cold\)"
)
# Hybrid A/B row (4096 only):
HYBRID_RE = re.compile(
    r"^\s*4096\*\s*\|\s*intel_spine_4096=(\S+)\s+intel_spine_4096_hybrid=(\S+)\s*\(warm\)"
    r"\s*\|\s*intel_spine_4096=\S+\s+intel_spine_4096_hybrid=(\S+)\s*\(cold\)"
)

MAIN_COLS = ["linear", "binary", "simd", "intel", "intels"]

main_samples: dict[int, list[list[float]]] = {}
pad_samples: dict[int, list[tuple[float, float, float]]] = {}  # (spine_w, pad_w, pad_c)
shipN_samples: dict[int, list[tuple[float, float, float]]] = {}  # (spine_w, N_w, N_c)
hybrid_samples: list[tuple[float, float, float]] = []  # (unroll_w, hybrid_w, hybrid_c)

for run_path in RUNS:
    with run_path.open() as f:
        for line in f:
            # Hybrid is a specific 4096* row; match first so it doesn't
            # get caught by the generic SHIPN pattern.
            m = HYBRID_RE.match(line)
            if m:
                hybrid_samples.append((float(m.group(1)), float(m.group(2)), float(m.group(3))))
                continue
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


out = HERE / "shipN_summary.txt"
with out.open("w") as f:
    f.write("5-run medians of ./bench 4000 5000 on EMR (Xeon 8559C), "
            "2026-05-12. Raw: shipN_run{1..5}.txt.\n")
    f.write("Build: g++ -O3 -march=sapphirerapids -std=c++20 "
            "bench.cpp simd_quad_intel.c -o bench\n\n")

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
            # cold baseline: from main row (intels column, index 4)
            sc = median(main_samples[size][5 + 4])
            delta_c = (nc - sc) / sc * 100
            f.write(f"{size:>5}* | intel_spine_{size}:   warm {nw:.2f}  cold {nc:.2f}"
                    f"   (vs spine: {delta_w:+.1f}% warm / {delta_c:+.1f}% cold)\n")

    # Hybrid A/B for n=4096
    if hybrid_samples:
        uw = median([s[0] for s in hybrid_samples])
        hw = median([s[1] for s in hybrid_samples])
        hc = median([s[2] for s in hybrid_samples])
        # unroll cold from shipN_samples[4096]
        uc = median([s[2] for s in shipN_samples[4096]])
        delta_w = (hw - uw) / uw * 100
        delta_c = (hc - uc) / uc * 100
        f.write("\n")
        f.write("Hybrid A/B at n=4096 (ship/no-ship call):\n")
        f.write(f"  intel_spine_4096        : warm {uw:.2f}  cold {uc:.2f}\n")
        f.write(f"  intel_spine_4096_hybrid : warm {hw:.2f}  cold {hc:.2f}\n")
        f.write(f"  hybrid vs unroll        : {delta_w:+.1f}% warm  {delta_c:+.1f}% cold\n")

print(f"wrote {out}")

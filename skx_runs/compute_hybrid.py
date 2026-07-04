#!/usr/bin/env python3
"""Compute per-cell medians across skx_runs/hybrid_run{1..5}.txt.

SKX (Xeon 8175M) hybrid-vs-unroll ship/no-ship A/B run 2026-05-13. The
shipped intel_spine_4096 is the hybrid (3 quat + branchless 2-probe
finish, after the 2026-05-12 EMR ship call retired the prior unroll).
simd_quad_intel.c temporarily exposes a scratch simd_quad_intel_spine_
4096_unroll symbol (3 quat + binary step + final lo, i.e. the pre-EMR
shape); bench.cpp prints a second 4096* row comparing them.

Writes:
  skx_runs/hybrid_summary.txt
"""
import re
import statistics
from pathlib import Path

HERE = Path(__file__).parent
RUNS = sorted(HERE.glob("hybrid_run*.txt"))
assert len(RUNS) == 5, f"expected 5 runs, got {len(RUNS)}"

# A/B row: intel_spine_4096=<hybrid> intel_spine_4096_unroll=<unroll>
AB_RE = re.compile(
    r"^\s*4096\*\s*\|\s*intel_spine_4096=(\S+)\s+intel_spine_4096_unroll=(\S+)\s*\(warm\)"
    r"\s*\|\s*intel_spine_4096=(\S+)\s+intel_spine_4096_unroll=(\S+)\s*\(cold\)"
)

samples = []  # (hw, uw, hc, uc)
for run_path in RUNS:
    with run_path.open() as f:
        for line in f:
            m = AB_RE.match(line)
            if m:
                samples.append((float(m.group(1)), float(m.group(2)),
                                float(m.group(3)), float(m.group(4))))
                break

assert len(samples) == 5, f"expected 5 A/B rows, got {len(samples)}"


def median(xs):
    return statistics.median(xs)


hw = median([s[0] for s in samples])
uw = median([s[1] for s in samples])
hc = median([s[2] for s in samples])
uc = median([s[3] for s in samples])
dw = (hw - uw) / uw * 100
dc = (hc - uc) / uc * 100

out = HERE / "hybrid_summary.txt"
with out.open("w") as f:
    f.write("SKX hybrid-vs-unroll ship/no-ship decision (2026-05-13)\n")
    f.write("=======================================================\n\n")
    f.write("Host: Intel Xeon Platinum 8175M (Skylake-SP, AVX-512BW, no VBMI2)\n")
    f.write("Build: g++ -O3 -march=native -std=c++20 bench.cpp simd_quad_intel.c -o bench\n")
    f.write("Bench: ./bench 4000 5000, 5 runs (raw: hybrid_run{1..5}.txt)\n\n")

    f.write("Per-run A/B at n=4096:\n")
    f.write("  run | hybrid_w  unroll_w | hybrid_c  unroll_c\n")
    for i, s in enumerate(samples, 1):
        f.write(f"  {i:>3} | {s[0]:>8.2f}  {s[1]:>8.2f} | {s[2]:>8.2f}  {s[3]:>8.2f}\n")
    f.write("\n5-run median A/B at n=4096:\n")
    f.write(f"  intel_spine_4096 (hybrid)       : warm {hw:>6.2f}  cold {hc:>7.2f} ns\n")
    f.write(f"  intel_spine_4096_unroll (prior) : warm {uw:>6.2f}  cold {uc:>7.2f} ns\n")
    f.write(f"  hybrid vs unroll                : {dw:+.1f}% warm  {dc:+.1f}% cold\n")

print(f"wrote {out}")
print(f"hybrid warm/cold: {hw:.2f} / {hc:.2f}")
print(f"unroll warm/cold: {uw:.2f} / {uc:.2f}")
print(f"hybrid vs unroll: {dw:+.1f}% warm  {dc:+.1f}% cold")

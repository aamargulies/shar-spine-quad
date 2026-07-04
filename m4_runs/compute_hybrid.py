#!/usr/bin/env python3
"""Compute 5-run medians for the Apple M4 Max hybrid-vs-unroll A/B
(2026-05-12, ship/no-ship call for simd_quad_m4_spine_4096).

Each hybrid_run{1..5}.txt is the unmodified output of
./bench 4000 5000 after the scratch simd_quad_m4_spine_4096_unroll
was added and a 4096* A/B row was printed:

    4096* |  m4_spine_4096_unroll=X  m4_spine_4096_hybrid=Y  (warm)  |
           m4_spine_4096_unroll=X  m4_spine_4096_hybrid=Y  (cold)

Mirrors the m1_runs / pi5_runs / gv4_runs / emr_runs flow.
"""
import re
import statistics
from pathlib import Path

HERE = Path(__file__).parent
RUNS = sorted(HERE.glob("hybrid_run*.txt"))
assert len(RUNS) == 5, f"expected 5 runs, got {len(RUNS)}"

AB_RE = re.compile(
    r"^\s*4096\*\s*\|\s*m4_spine_4096_unroll=(\S+)\s+m4_spine_4096_hybrid=(\S+)\s+\(warm\)"
    r"\s*\|\s*m4_spine_4096_unroll=(\S+)\s+m4_spine_4096_hybrid=(\S+)\s+\(cold\)"
)

samples = []  # list of (uw, hw, uc, hc)
for p in RUNS:
    for line in p.open():
        m = AB_RE.match(line)
        if m:
            samples.append(tuple(float(x) for x in m.groups()))
            break

assert len(samples) == 5, f"expected 5 A/B rows, got {len(samples)}"

uw = [s[0] for s in samples]
hw = [s[1] for s in samples]
uc = [s[2] for s in samples]
hc = [s[3] for s in samples]

mu = lambda xs: statistics.median(xs)

uw_m, hw_m = mu(uw), mu(hw)
uc_m, hc_m = mu(uc), mu(hc)

wins_w = sum(1 for s in samples if s[1] < s[0])
wins_c = sum(1 for s in samples if s[3] < s[2])

out = HERE / "hybrid_summary.txt"
with out.open("w") as f:
    f.write(
        "Apple M4 Max hybrid-vs-unroll A/B, 2026-05-12.\n"
        "./bench 4000 5000 x 5 runs (m4_runs/hybrid_run{1..5}.txt).\n\n"
    )
    f.write(f"    unroll: warm {uw_m:.2f}  cold {uc_m:.2f}\n")
    f.write(f"    hybrid: warm {hw_m:.2f}  cold {hc_m:.2f}\n")
    f.write(
        f"    delta : warm {((hw_m - uw_m) / uw_m * 100.0):+.1f}%  "
        f"cold {((hc_m - uc_m) / uc_m * 100.0):+.1f}%\n"
    )
    f.write(f"    warm hybrid < unroll on {wins_w}/5 runs\n")
    f.write(f"    cold hybrid < unroll on {wins_c}/5 runs\n")
    f.write(f"    per-run unroll warms: " + " ".join(f"{x:.2f}" for x in uw) + "\n")
    f.write(f"    per-run hybrid warms: " + " ".join(f"{x:.2f}" for x in hw) + "\n")
    f.write(f"    per-run unroll colds: " + " ".join(f"{x:.2f}" for x in uc) + "\n")
    f.write(f"    per-run hybrid colds: " + " ".join(f"{x:.2f}" for x in hc) + "\n")

print(out.read_text())

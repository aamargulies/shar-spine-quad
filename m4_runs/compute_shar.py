#!/usr/bin/env python3
"""Aggregate shar_run*.txt medians from bench_twolevel with E/F variants."""
import glob, re, statistics

files = sorted(glob.glob("m4_runs/shar_run*.txt"))
rows = {}
for f in files:
    with open(f) as fh:
        for line in fh:
            m = re.match(r"^([A-F])\s+\S.*?\s+(\d+\.\d+)\s+(\d+\.\d+)\s*$", line)
            if m:
                v, warm, cold = m.group(1), float(m.group(2)), float(m.group(3))
                rows.setdefault(v, {"warm": [], "cold": []})
                rows[v]["warm"].append(warm)
                rows[v]["cold"].append(cold)

print(f"{'var':>4}  {'warm (med)':>12}  {'cold (med)':>12}  runs")
for v in sorted(rows):
    w = statistics.median(rows[v]["warm"])
    c = statistics.median(rows[v]["cold"])
    print(f"{v:>4}  {w:>12.2f}  {c:>12.2f}  {len(rows[v]['warm'])}")

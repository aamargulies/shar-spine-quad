#!/usr/bin/env python3
"""Aggregate m1_runs/twolevel_run*.txt medians for variants A-G + Lem
across the four measurement modes: hot_bat, hot_ser, cold_bat, cold_ser.

Harness semantics (see bench_twolevel.cpp):
  hot_bat  - 200 reps per set, independent queries, hot caches (OoO
             batches, measures throughput).
  hot_ser  - 200 reps per set, dep-chained queries, hot caches (serial,
             measures per-query critical-path latency).
  cold_bat - 1 rep per set x 200 sets, independent queries, thrashed
             LLC (OoO overlaps DRAM misses across queries).
  cold_ser - 1 rep per set x 200 sets, dep-chained queries, thrashed
             LLC (each query's cold miss serializes behind previous).
"""
import glob, re, statistics

files = sorted(glob.glob("m1_runs/twolevel_run*.txt"))
rows = {}
for f in files:
    with open(f) as fh:
        for line in fh:
            m = re.match(
                r"^([A-I]|Lem)\s+\S.*?\s+"
                r"(\d+\.\d+|nan)\s+(\d+\.\d+|nan)\s+"
                r"(\d+\.\d+|nan)\s+(\d+\.\d+|nan)\s*$", line)
            if m:
                v = m.group(1)
                vals = [float(m.group(i)) if m.group(i) != "nan" else None
                        for i in (2, 3, 4, 5)]
                rows.setdefault(v, {"hb": [], "hs": [], "cb": [], "cs": []})
                for key, val in zip(("hb", "hs", "cb", "cs"), vals):
                    if val is not None:
                        rows[v][key].append(val)

# Stable order: A-G then Lem.
order = lambda v: ("0" + v) if len(v) == 1 else "1" + v
print(f"{'var':>4}  {'hot_bat':>10}  {'hot_ser':>10}  {'cold_bat':>10}  {'cold_ser':>10}  runs")
for v in sorted(rows, key=order):
    hb = statistics.median(rows[v]["hb"]) if rows[v]["hb"] else float("nan")
    hs = statistics.median(rows[v]["hs"]) if rows[v]["hs"] else float("nan")
    cb = statistics.median(rows[v]["cb"]) if rows[v]["cb"] else float("nan")
    cs = statistics.median(rows[v]["cs"]) if rows[v]["cs"] else float("nan")
    n = max(len(rows[v][k]) for k in ("hb","hs","cb","cs"))
    print(f"{v:>4}  {hb:>10.2f}  {hs:>10.2f}  {cb:>10.2f}  {cs:>10.2f}  {n}")

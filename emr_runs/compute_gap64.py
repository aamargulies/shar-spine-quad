#!/usr/bin/env python3
"""Median-aggregate the gap64 A/B runs."""
import os, re

SIZES = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]

def parse_run(path):
    out = {}
    with open(path) as f:
        for line in f:
            m = re.match(r"\s*(\d+)\s*\|\s*(.*?)\|(.*)", line)
            if not m: continue
            size = int(m.group(1))
            w = tuple(float(x) for x in m.group(2).split()[:4])
            c = tuple(float(x) for x in m.group(3).split()[:4])
            out[size] = (w, c)
    return out

def median(lst):
    s = sorted(lst); n = len(s)
    return s[n//2] if n % 2 else 0.5 * (s[n//2 - 1] + s[n//2])

d = os.path.dirname(os.path.abspath(__file__))
runs = [parse_run(os.path.join(d, f"gap64_run{i}.txt")) for i in range(1, 6)]

print(f"=== EMR gap=32 vs gap=64, medians of 5 ===")
print(f"{'size':>5} | {'g32':>6} {'g32s':>6} {'g64':>6} {'g64s':>6} (warm) | "
      f"{'g32':>6} {'g32s':>6} {'g64':>6} {'g64s':>6} (cold)")
print("-" * 90)
for s in SIZES:
    wm = [median([r[s][0][c] for r in runs]) for c in range(4)]
    cm = [median([r[s][1][c] for r in runs]) for c in range(4)]
    print(f"{s:>5} | {wm[0]:6.1f} {wm[1]:6.1f} {wm[2]:6.1f} {wm[3]:6.1f}              | "
          f"{cm[0]:6.1f} {cm[1]:6.1f} {cm[2]:6.1f} {cm[3]:6.1f}")

print(f"\n=== % change of gap=64 vs gap=32 (negative = g64 faster) ===")
print(f"{'size':>5} | {'warm plain':>10} {'warm spine':>10} | {'cold plain':>10} {'cold spine':>10}")
for s in SIZES:
    wm = [median([r[s][0][c] for r in runs]) for c in range(4)]
    cm = [median([r[s][1][c] for r in runs]) for c in range(4)]
    def pct(a, b):
        return 100.0 * (b - a) / a if a else float('nan')
    print(f"{s:>5} | {pct(wm[0], wm[2]):10.1f} {pct(wm[1], wm[3]):10.1f} | "
          f"{pct(cm[0], cm[2]):10.1f} {pct(cm[1], cm[3]):10.1f}")

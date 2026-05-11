#!/usr/bin/env python3
"""Parse 5 bench runs and compute per-cell medians."""
import sys, re, os

SIZES = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
COLS  = ["linear", "binary", "simd", "intel", "intels"]

def parse_run(path):
    """Return dict[size] = (warm_tuple, cold_tuple) each of length 5."""
    out = {}
    with open(path) as f:
        for line in f:
            m = re.match(r"\s*(\d+)\s*\|\s*(.*?)\|(.*)", line)
            if not m: continue
            size = int(m.group(1))
            warm_s = m.group(2).split()
            cold_s = m.group(3).split()
            warm = tuple(float(x) for x in warm_s[:5])
            cold = tuple(float(x) for x in cold_s[:5])
            out[size] = (warm, cold)
    return out

def median(lst):
    s = sorted(lst)
    n = len(s)
    if n % 2: return s[n//2]
    return 0.5 * (s[n//2 - 1] + s[n//2])

def aggregate(paths):
    runs = [parse_run(p) for p in paths]
    agg = {}
    for size in SIZES:
        warm_cells = [[r[size][0][c] for r in runs] for c in range(5)]
        cold_cells = [[r[size][1][c] for r in runs] for c in range(5)]
        warm_med = tuple(median(w) for w in warm_cells)
        cold_med = tuple(median(c) for c in cold_cells)
        agg[size] = (warm_med, cold_med)
    return agg

def print_medians(label, agg):
    print(f"\n=== {label} (medians of 5) ===")
    print(f"{'size':>6} | {'warm: linear  binary  simd   intel  intels':<48} | {'cold: linear  binary  simd   intel  intels':<48}")
    for s in SIZES:
        w, c = agg[s]
        print(f"{s:>6} | "
              f"{w[0]:7.1f} {w[1]:7.1f} {w[2]:6.1f} {w[3]:6.1f} {w[4]:6.1f}           | "
              f"{c[0]:7.1f} {c[1]:7.1f} {c[2]:6.1f} {c[3]:6.1f} {c[4]:6.1f}")

def diff_table(a, b, la, lb):
    """Print (b - a) / a * 100 for intel (col 3) and intels (col 4), warm and cold."""
    print(f"\n=== (100 * ({lb} - {la}) / {la}) -- negative = {lb} faster ===")
    print(f"{'size':>6} | {'intel warm':>10} {'intels warm':>12} | {'intel cold':>10} {'intels cold':>12}")
    for s in SIZES:
        aw, ac = a[s]
        bw, bc = b[s]
        def pct(x, y):
            if x == 0: return float('nan')
            return 100.0 * (y - x) / x
        print(f"{s:>6} | {pct(aw[3], bw[3]):10.1f} {pct(aw[4], bw[4]):12.1f} | {pct(ac[3], bc[3]):10.1f} {pct(ac[4], bc[4]):12.1f}")

if __name__ == "__main__":
    d = os.path.dirname(os.path.abspath(__file__))
    baseline = aggregate([os.path.join(d, f"baseline_run{i}.txt") for i in range(1, 6)])
    nopref   = aggregate([os.path.join(d, f"noprefetch_run{i}.txt") for i in range(1, 6)])
    print_medians("BASELINE (prefetch kept)", baseline)
    print_medians("NOPREFETCH (prefetch removed)", nopref)
    diff_table(baseline, nopref, "baseline", "nopref")

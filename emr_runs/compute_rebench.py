#!/usr/bin/env python3
"""Parse the 2026-05-01 rebench runs (bench + bench_twolevel) and compute
per-cell medians. Prints values ready to paste into plot.py.

bench output rows look like:
   4096  |   667.3    60.8   13.9   19.7   17.9              |   586.9   140.1  100.9   89.0   46.5
   4096* | intel_spine=17.90 intel_spine_4096=14.02  (warm)  | intel_spine=46.50 intel_spine_4096=33.42  (cold)

bench_twolevel output rows look like:
A     bsearch outer + simd_quad_intel_spine inner                   144.94       90.25
B     two-level spine + simd_quad_intel_spine inner                 148.07       47.52
C     bsearch outer + simd_quad_intel_spine_4096 inner               75.87       55.02
D     two-level spine + simd_quad_intel_spine_4096 inner             79.44       27.31
"""
import os, re, sys

SIZES = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
COLS  = ["linear", "binary", "simd", "intel", "intels"]
HERE  = os.path.dirname(os.path.abspath(__file__))

def median(lst):
    s = sorted(lst)
    n = len(s)
    return s[n//2] if n % 2 else 0.5 * (s[n//2 - 1] + s[n//2])

def parse_bench_run(path):
    """dict[size] -> (warm[5], cold[5]); plus dict[4096_specialized] -> (warm, cold)."""
    out = {}
    spec = None
    with open(path) as f:
        for line in f:
            m = re.match(r"\s*(\d+)\s*\|\s*(.*?)\|(.*)", line)
            if m and "intel_spine=" not in line:
                size = int(m.group(1))
                warm = tuple(float(x) for x in m.group(2).split()[:5])
                cold = tuple(float(x) for x in m.group(3).split()[:5])
                out[size] = (warm, cold)
                continue
            m = re.match(r"\s*4096\*.*intel_spine=([\d.]+)\s+intel_spine_4096=([\d.]+)"
                         r".*intel_spine=([\d.]+)\s+intel_spine_4096=([\d.]+)", line)
            if m:
                spec = (float(m.group(2)), float(m.group(4)))  # warm/cold 4096-specialized
    return out, spec

def aggregate_bench(paths):
    runs = [parse_bench_run(p) for p in paths]
    agg = {}
    for size in SIZES:
        warm_cells = [[r[0][size][0][c] for r in runs] for c in range(5)]
        cold_cells = [[r[0][size][1][c] for r in runs] for c in range(5)]
        agg[size] = (tuple(median(w) for w in warm_cells),
                     tuple(median(c) for c in cold_cells))
    specs = [r[1] for r in runs if r[1] is not None]
    spec_warm = median([s[0] for s in specs]) if specs else None
    spec_cold = median([s[1] for s in specs]) if specs else None
    return agg, (spec_warm, spec_cold)

def parse_twolevel_run(path):
    """-> dict {A,B,C,D,E,F} -> (warm, cold)."""
    out = {}
    with open(path) as f:
        for line in f:
            m = re.match(r"^(A|B|C|D|E|F)\s+\S.*?\s+([\d.]+)\s+([\d.]+)\s*$", line)
            if m:
                out[m.group(1)] = (float(m.group(2)), float(m.group(3)))
    return out

def aggregate_twolevel(paths):
    runs = [parse_twolevel_run(p) for p in paths]
    agg = {}
    for v in "ABCDEF":
        cells = [r.get(v) for r in runs if v in r]
        if not cells:
            continue
        warm = median([c[0] for c in cells])
        cold = median([c[1] for c in cells])
        agg[v] = (warm, cold)
    return agg

def fmt_row(label, vals, width=6, prec=1):
    return label + "[" + ", ".join(f"{v:{width}.{prec}f}" for v in vals) + "]"

def main():
    bench_paths = [os.path.join(HERE, f"rebench_run{i}.txt") for i in range(1, 6)]
    tl_paths    = [os.path.join(HERE, f"twolevel_run{i}.txt") for i in range(1, 6)]

    bench_agg, spec = aggregate_bench(bench_paths)

    # Pretty-print the main table.
    print("=== EMR bench medians (5 runs, 2026-05-01) ===")
    print(f"{'size':>6} | {'warm: linear  binary  simd  intel  intels':<46} | cold: linear  binary  simd  intel  intels")
    for s in SIZES:
        w, c = bench_agg[s]
        print(f"{s:>6} | "
              f"{w[0]:7.1f} {w[1]:7.1f} {w[2]:6.1f} {w[3]:6.1f} {w[4]:6.1f}         | "
              f"{c[0]:7.1f} {c[1]:7.1f} {c[2]:6.1f} {c[3]:6.1f} {c[4]:6.1f}")
    print(f"\n n=4096 compile-time specialization: warm={spec[0]:.2f}  cold={spec[1]:.2f}")

    # Print plot.py-ready emr_warm / emr_cold dicts.
    labels = {
        0: ("linear (std::find)",          7, 1),
        1: ("binary (std::binary_search)", 7, 1),
        2: ("simd_quad (reference)",       6, 1),
        3: ("simd_quad_intel",             6, 1),
        4: ("simd_quad_intel + spine",     6, 1),
    }
    def emit(regime_name, regime_idx):
        print(f"\n{regime_name} = {{")
        for c in range(5):
            row = [bench_agg[s][regime_idx][c] for s in SIZES]
            name, w, p = labels[c]
            print(f'    "{name:32s}":[' +
                  ", ".join(f"{v:{w}.{p}f}" for v in row) + "],")
        print("}")
    emit("emr_warm", 0)
    emit("emr_cold", 1)

    tl_agg = aggregate_twolevel(tl_paths)
    print("\n=== EMR bench_twolevel medians (5 runs) ===")
    print(f"{'var':4}  {'warm ns/q':>10}  {'cold ns/q':>10}")
    for v in "ABCDEF":
        if v not in tl_agg: continue
        w, c = tl_agg[v]
        print(f"{v:<4}  {w:10.2f}  {c:10.2f}")
    def pct(x, y): return 100.0 * (y - x) / x
    if "A" in tl_agg:
        wA, cA = tl_agg["A"]
        print(f"\ndeltas vs A:")
        for v in "BCDEF":
            if v not in tl_agg: continue
            w, c = tl_agg[v]
            print(f"  {v} vs A:   warm {pct(wA, w):+.1f}%   cold {pct(cA, c):+.1f}%")
    if "D" in tl_agg and "F" in tl_agg:
        wD, cD = tl_agg["D"]
        print(f"\ndeltas vs D:")
        for v in "EF":
            if v not in tl_agg: continue
            w, c = tl_agg[v]
            print(f"  {v} vs D:   warm {pct(wD, w):+.1f}%   cold {pct(cD, c):+.1f}%")

    # Python dict to paste into plot.py.
    print("\n# paste into plot.py")
    print("emr_twolevel = {")
    for v in "ABCDEF":
        if v not in tl_agg: continue
        w, c = tl_agg[v]
        print(f'    "{v}": ({w:.2f}, {c:.2f}),')
    print("}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Parse the 2026-05-01 SKX bench + bench_twolevel runs and compute per-cell
medians. Prints values ready to paste into plot.py.

Bench output rows (rebench_run{1..5}.txt) look like:
   4096  |   166.6    81.8   32.3   40.5   28.2              |   582.2   265.1  172.8  176.6  129.3
   4096* | intel_spine=28.19 intel_spine_4096=26.45  (warm)  | intel_spine=129.30 intel_spine_4096=124.02  (cold)

bench_twolevel output rows (twolevel_run{1..5}.txt) look like:
A     bsearch outer + simd_quad_intel_spine inner                   237.30      126.60
B     two-level spine + simd_quad_intel_spine inner                 219.41       47.02
C     bsearch outer + simd_quad_intel_spine_4096 inner              138.92       68.70
D     two-level spine + simd_quad_intel_spine_4096 inner             95.28       33.66
"""
import os, re, sys

SIZES = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
HERE  = os.path.dirname(os.path.abspath(__file__))

def median(lst):
    s = sorted(lst)
    n = len(s)
    return s[n//2] if n % 2 else 0.5 * (s[n//2 - 1] + s[n//2])

def parse_twolevel_run(path):
    """-> dict {A..F} -> (warm, cold)."""
    out = {}
    with open(path) as f:
        for line in f:
            m = re.match(r"^(A|B|C|D|E|F)\s+\S.*?\s+([\d.]+)\s+([\d.]+)\s*$", line)
            if m:
                out[m.group(1)] = (float(m.group(2)), float(m.group(3)))
    return out

def aggregate(paths):
    runs = [parse_twolevel_run(p) for p in paths]
    agg = {}
    vars_seen = [v for v in "ABCDEF" if all(v in r for r in runs)]
    for v in vars_seen:
        warm = median([r[v][0] for r in runs])
        cold = median([r[v][1] for r in runs])
        agg[v] = (warm, cold)
    return agg, runs

def parse_bench_run(path):
    """dict[size] -> (warm[5], cold[5]); plus (spec_warm, spec_cold) for n=4096."""
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
                # Second numeric in each half is the _spine_4096 value.
                spec = (float(m.group(2)), float(m.group(4)))
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

def main():
    # --- main bench (rebench_run{1..5}.txt) ---
    bench_paths = [os.path.join(HERE, f"rebench_run{i}.txt") for i in range(1, 6)]
    bench_paths = [p for p in bench_paths if os.path.exists(p)]
    if bench_paths:
        bench_agg, spec = aggregate_bench(bench_paths)
        print("=== SKX bench medians (5 runs, 2026-05-01) ===")
        print(f"{'size':>6} | {'warm: linear  binary  simd  intel  intels':<46} | cold: linear  binary  simd  intel  intels")
        for s in SIZES:
            w, c = bench_agg[s]
            print(f"{s:>6} | "
                  f"{w[0]:7.1f} {w[1]:7.1f} {w[2]:6.1f} {w[3]:6.1f} {w[4]:6.1f}         | "
                  f"{c[0]:7.1f} {c[1]:7.1f} {c[2]:6.1f} {c[3]:6.1f} {c[4]:6.1f}")
        if spec[0] is not None:
            print(f"\n n=4096 compile-time specialization: warm={spec[0]:.2f}  cold={spec[1]:.2f}")

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
        emit("skx_warm", 0)
        emit("skx_cold", 1)
        if spec[0] is not None:
            print(f'\nskx_spine_4096 = {{"warm": {spec[0]:.2f}, "cold": {spec[1]:.2f}}}')

    # --- bench_twolevel (twolevel_run{1..5}.txt) ---
    paths = [os.path.join(HERE, f"twolevel_run{i}.txt") for i in range(1, 6)]
    agg, runs = aggregate(paths)
    print()

    vars_present = sorted(agg.keys())
    print("=== SKX bench_twolevel per-run cells ===")
    header_parts = [f"{'run':4}"]
    for v in vars_present:
        header_parts.append(f"{v+' warm':>8} {v+' cold':>8}")
    print("  ".join(header_parts))
    for i, r in enumerate(runs, 1):
        cells = [f"{i:<4}"]
        for v in vars_present:
            cells.append(f"{r[v][0]:8.2f} {r[v][1]:8.2f}")
        print("  ".join(cells))

    print("\n=== SKX bench_twolevel medians (5 runs) ===")
    print(f"{'var':4}  {'warm ns/q':>10}  {'cold ns/q':>10}")
    for v in vars_present:
        w, c = agg[v]
        print(f"{v:<4}  {w:10.2f}  {c:10.2f}")

    wA, cA = agg["A"]
    def pct(x, y): return 100.0 * (y - x) / x
    print("\ndeltas vs A (based on medians):")
    for v in vars_present[1:]:
        w, c = agg[v]
        print(f"  {v} vs A:   warm {pct(wA, w):+.1f}%   cold {pct(cA, c):+.1f}%")
    if "D" in agg:
        wD, cD = agg["D"]
        print("\ndeltas vs D (current best stacked):")
        for v in ("E", "F"):
            if v in agg:
                w, c = agg[v]
                print(f"  {v} vs D:   warm {pct(wD, w):+.1f}%   cold {pct(cD, c):+.1f}%")

    descs = {
        "A": "bsearch outer + general-n inner",
        "B": "two-level spine outer + general-n inner",
        "C": "bsearch outer + n=4096 inner",
        "D": "two-level spine outer + n=4096 inner",
        "E": "Shar branchless outer + general-n inner",
        "F": "Shar branchless outer + n=4096 inner",
    }
    print("\n# paste into plot.py")
    print("skx_twolevel = {")
    for v in vars_present:
        desc = descs[v]
        w, c = agg[v]
        print(f'    "{v}  {desc}":{" " * max(0, 44 - len(desc))}({w:6.2f}, {c:6.2f}),')
    print("}")

if __name__ == "__main__":
    main()

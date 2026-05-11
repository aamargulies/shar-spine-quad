#!/usr/bin/env python3
"""Aggregate Apple M1 Pro bench runs (main bench + bench_twolevel).

M1 Pro uses the simd_quad_m4.c variant (shared Apple-silicon gap=64 family —
same 128-byte cache line, wide OoO, no SVE). The M1's "own" column in the
bench table is therefore m4 / m4s, same as what the M4 Max host reports.

Main bench output has 9 warm + 9 cold columns (ARM):
  linear, binary, simd(ref), pi5, pi5s, m4, m4s, gv4, gv4s
and three `4096*` A/B rows (pi5, m4, gv4).

bench_twolevel output rows are A–F (same layout as other hosts after the
2026-05-01 Shar landing).

Usage:
    python3 compute_medians.py
"""
import os, re, sys

SIZES = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
HERE  = os.path.dirname(os.path.abspath(__file__))

def median(lst):
    s = sorted(lst)
    n = len(s)
    return s[n//2] if n % 2 else 0.5 * (s[n//2 - 1] + s[n//2])

def parse_bench_run(path):
    out = {}
    gv4_spec = m4_spec = pi5_spec = None
    with open(path) as f:
        for line in f:
            m = re.match(r"\s*4096\*.*gv4_spine=([\d.]+)\s+gv4_spine_4096=([\d.]+)"
                         r".*gv4_spine=([\d.]+)\s+gv4_spine_4096=([\d.]+)", line)
            if m:
                gv4_spec = (float(m.group(2)), float(m.group(4)))
                continue
            m = re.match(r"\s*4096\*.*m4_spine=([\d.]+)\s+m4_spine_4096=([\d.]+)"
                         r".*m4_spine=([\d.]+)\s+m4_spine_4096=([\d.]+)", line)
            if m:
                m4_spec = (float(m.group(2)), float(m.group(4)))
                continue
            m = re.match(r"\s*4096\*.*pi5_spine=([\d.]+)\s+pi5_spine_4096=([\d.]+)"
                         r".*pi5_spine=([\d.]+)\s+pi5_spine_4096=([\d.]+)", line)
            if m:
                pi5_spec = (float(m.group(2)), float(m.group(4)))
                continue
            m = re.match(r"\s*(\d+)\s*\|\s*(.*?)\|(.*)", line)
            if m:
                size = int(m.group(1))
                warm_nums = [float(x) for x in m.group(2).split()]
                cold_nums = [float(x) for x in m.group(3).split()]
                if len(warm_nums) >= 9 and len(cold_nums) >= 9:
                    out[size] = (tuple(warm_nums[:9]), tuple(cold_nums[:9]))
    return out, gv4_spec, m4_spec, pi5_spec

def aggregate_bench(paths):
    runs = [parse_bench_run(p) for p in paths]
    agg = {}
    for size in SIZES:
        warm_cells = [[r[0][size][0][c] for r in runs] for c in range(9)]
        cold_cells = [[r[0][size][1][c] for r in runs] for c in range(9)]
        agg[size] = (tuple(median(w) for w in warm_cells),
                     tuple(median(c) for c in cold_cells))
    def spec_median(idx):
        s = [r[idx] for r in runs if r[idx] is not None]
        if not s: return (None, None)
        return (median([x[0] for x in s]), median([x[1] for x in s]))
    return agg, spec_median(1), spec_median(2), spec_median(3)

def parse_twolevel_run(path):
    out = {}
    with open(path) as f:
        for line in f:
            m = re.match(r"^([A-F])\s+\S.*?\s+([\d.]+)\s+([\d.]+)\s*$", line)
            if m:
                out[m.group(1)] = (float(m.group(2)), float(m.group(3)))
    return out

def aggregate_twolevel(paths):
    runs = [parse_twolevel_run(p) for p in paths]
    agg = {}
    for v in "ABCDEF":
        if all(v in r for r in runs):
            agg[v] = (median([r[v][0] for r in runs]),
                      median([r[v][1] for r in runs]))
    return agg

COL_LABELS = ["linear", "binary", "simd", "pi5", "pi5s", "m4", "m4s", "gv4", "gv4s"]

def print_bench_table(agg, title):
    print(f"\n=== {title} ===")
    header = f"{'size':>5} |" + "".join(f" {l:>6}" for l in COL_LABELS) + \
             "   ||" + "".join(f" {l:>6}" for l in COL_LABELS)
    print(header)
    for s in SIZES:
        w, c = agg[s]
        print(f"{s:>5} |" + "".join(f" {v:6.1f}" for v in w) +
              "   ||" + "".join(f" {v:6.1f}" for v in c))

def emit_m1_dicts(agg):
    """Emit m1_warm / m1_cold for plot.py with 9 columns (ARM)."""
    labels = [
        ("linear (std::find)",          0),
        ("binary (std::binary_search)", 1),
        ("simd_quad (reference)",       2),
        ("simd_quad_pi5",               3),
        ("simd_quad_pi5 + spine",       4),
        ("simd_quad_m4",                5),
        ("simd_quad_m4 + spine",        6),
        ("simd_quad_graviton",          7),
        ("simd_quad_graviton + spine",  8),
    ]
    for regime_name, regime_idx in [("m1_warm", 0), ("m1_cold", 1)]:
        print(f"\n{regime_name} = {{")
        for name, col in labels:
            row = [agg[s][regime_idx][col] for s in SIZES]
            print(f'    "{name:32s}":[' +
                  ", ".join(f"{v:6.1f}" for v in row) + "],")
        print("}")

def main():
    bench_paths = [os.path.join(HERE, f"rebench_run{i}.txt") for i in range(1, 6)]
    tl_paths    = [os.path.join(HERE, f"twolevel_run{i}.txt") for i in range(1, 6)]
    bench_paths = [p for p in bench_paths if os.path.exists(p)]
    tl_paths    = [p for p in tl_paths    if os.path.exists(p)]

    if bench_paths:
        bench_agg, gv4_spec, m4_spec, pi5_spec = aggregate_bench(bench_paths)
        print_bench_table(bench_agg,
                          f"M1 Pro main bench medians ({len(bench_paths)} runs)")
        if m4_spec[0] is not None:
            print(f"\nm4_spine_4096 specialization (M1 Pro host):  "
                  f"warm={m4_spec[0]:.2f}  cold={m4_spec[1]:.2f}")
        if gv4_spec[0] is not None:
            print(f"gv4_spine_4096 on this host:   warm={gv4_spec[0]:.2f}  "
                  f"cold={gv4_spec[1]:.2f}")
        if pi5_spec[0] is not None:
            print(f"pi5_spine_4096 on this host:   warm={pi5_spec[0]:.2f}  "
                  f"cold={pi5_spec[1]:.2f}")
        emit_m1_dicts(bench_agg)
        if m4_spec[0] is not None:
            print(f"\nm1_spine_4096 = {{'warm': {m4_spec[0]:.2f}, "
                  f"'cold': {m4_spec[1]:.2f}}}")

    if tl_paths:
        tl_agg = aggregate_twolevel(tl_paths)
        print(f"\n=== M1 Pro bench_twolevel medians ({len(tl_paths)} runs) ===")
        print(f"{'var':4}  {'warm ns/q':>10}  {'cold ns/q':>10}")
        for v in "ABCDEF":
            if v in tl_agg:
                w, c = tl_agg[v]
                print(f"{v:<4}  {w:10.2f}  {c:10.2f}")
        if "A" in tl_agg:
            wA, cA = tl_agg["A"]
            def pct(x, y): return 100.0 * (y - x) / x
            print("\ndeltas vs A:")
            for v in "BCDEF":
                if v in tl_agg:
                    w, c = tl_agg[v]
                    print(f"  {v} vs A:   warm {pct(wA, w):+.1f}%   "
                          f"cold {pct(cA, c):+.1f}%")
        labels_full = [
            ("A", "bsearch outer + general-n inner"),
            ("B", "two-level spine outer + general-n inner"),
            ("C", "bsearch outer + n=4096 inner"),
            ("D", "two-level spine outer + n=4096 inner"),
            ("E", "Shar branchless outer + general-n inner"),
            ("F", "Shar branchless outer + n=4096 inner"),
        ]
        print("\n# paste into plot.py")
        print("m1_twolevel = {")
        for v, desc in labels_full:
            if v in tl_agg:
                w, c = tl_agg[v]
                print(f'    "{v}  {desc}":{" "*max(0, 44-len(desc))}'
                      f'({w:6.2f}, {c:6.2f}),')
        print("}")

if __name__ == "__main__":
    main()

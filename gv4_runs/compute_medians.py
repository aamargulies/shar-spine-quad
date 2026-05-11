#!/usr/bin/env python3
"""Aggregate Graviton 4 (Arm Neoverse V2) bench runs.

Main bench output has 9 warm + 9 cold columns (ARM):
   linear, binary, simd(ref), pi5, pi5s, m4, m4s, gv4, gv4s
and three `4096*` A/B rows (pi5, m4, gv4) that carry the compile-time-n=4096
specialization numbers.

bench_twolevel output rows look like:
   A     bsearch outer + general-n spine inner                         ...
   B     two-level spine + general-n spine inner                       ...
   C     bsearch outer + compile-time n=4096 inner                     ...
   D     two-level spine + compile-time n=4096 inner                   ...
   E     Shar branchless outer + general-n spine inner                 ...
   F     Shar branchless outer + compile-time n=4096 inner             ...

Usage:
    python3 compute_medians.py            # aggregates rebench_run*.txt + twolevel_run*.txt
    python3 compute_medians.py baseline   # aggregates baseline_run*.txt (legacy, 2026-05-01 prefetch A/B)
    python3 compute_medians.py prefetch   # aggregates prefetch_run*.txt
    python3 compute_medians.py ab         # baseline vs prefetch deltas
"""
import os, re, sys

SIZES = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
HERE  = os.path.dirname(os.path.abspath(__file__))

def median(lst):
    s = sorted(lst)
    n = len(s)
    return s[n//2] if n % 2 else 0.5 * (s[n//2 - 1] + s[n//2])

def parse_bench_run(path):
    """Returns (per_size: dict[size] -> (warm9, cold9),
                gv4_spec: (warm, cold) | None,
                m4_spec:  (warm, cold) | None,
                pi5_spec: (warm, cold) | None)."""
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

def emit_gv4_dicts(agg):
    """Emit gv4_warm / gv4_cold for plot.py. Five columns used: linear, binary,
    simd reference, simd_quad_graviton, simd_quad_graviton + spine."""
    labels = [
        ("linear (std::find)",          0),
        ("binary (std::binary_search)", 1),
        ("simd_quad (reference)",       2),
        ("simd_quad_graviton",          7),
        ("simd_quad_graviton + spine",  8),
    ]
    for regime_name, regime_idx in [("gv4_warm", 0), ("gv4_cold", 1)]:
        print(f"\n{regime_name} = {{")
        for name, col in labels:
            row = [agg[s][regime_idx][col] for s in SIZES]
            print(f'    "{name:32s}":[' +
                  ", ".join(f"{v:6.1f}" for v in row) + "],")
        print("}")

def cmd_default():
    bench_paths = [os.path.join(HERE, f"rebench_run{i}.txt") for i in range(1, 6)]
    tl_paths    = [os.path.join(HERE, f"twolevel_run{i}.txt") for i in range(1, 6)]
    bench_paths = [p for p in bench_paths if os.path.exists(p)]
    tl_paths    = [p for p in tl_paths if os.path.exists(p)]

    if bench_paths:
        bench_agg, gv4_spec, m4_spec, pi5_spec = aggregate_bench(bench_paths)
        print_bench_table(bench_agg,
                          f"Graviton 4 main bench medians ({len(bench_paths)} runs)")
        if gv4_spec[0] is not None:
            print(f"\ngv4_spine_4096 specialization: warm={gv4_spec[0]:.2f}  cold={gv4_spec[1]:.2f}")
        emit_gv4_dicts(bench_agg)
        if gv4_spec[0] is not None:
            print(f"\ngv4_spine_4096 = {{'warm': {gv4_spec[0]:.2f}, 'cold': {gv4_spec[1]:.2f}}}")
    else:
        print("no rebench_run*.txt files yet")

    if tl_paths:
        tl_agg = aggregate_twolevel(tl_paths)
        print(f"\n=== Graviton 4 bench_twolevel medians ({len(tl_paths)} runs) ===")
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
                    print(f"  {v} vs A:   warm {pct(wA, w):+.1f}%   cold {pct(cA, c):+.1f}%")
        labels_full = [
            ("A", "bsearch outer + general-n inner"),
            ("B", "two-level spine outer + general-n inner"),
            ("C", "bsearch outer + n=4096 inner"),
            ("D", "two-level spine outer + n=4096 inner"),
            ("E", "Shar branchless outer + general-n inner"),
            ("F", "Shar branchless outer + n=4096 inner"),
        ]
        print("\n# paste into plot.py")
        print("gv4_twolevel = {")
        for v, desc in labels_full:
            if v in tl_agg:
                w, c = tl_agg[v]
                print(f'    "{v}  {desc}":{" "*max(0, 44-len(desc))}({w:6.2f}, {c:6.2f}),')
        print("}")


# --- legacy subcommands for the prefetch A/B that preceded rebench ---
def cmd_baseline():
    paths = [os.path.join(HERE, f"baseline_run{i}.txt") for i in range(1, 6)]
    agg, gv4_spec, _, _ = aggregate_bench(paths)
    print_bench_table(agg, "Graviton 4 baseline (no prefetch) - medians of 5")
    emit_gv4_dicts(agg)
    if gv4_spec[0] is not None:
        print(f"\ngv4_spine_4096 = {{'warm': {gv4_spec[0]:.2f}, 'cold': {gv4_spec[1]:.2f}}}")

def cmd_prefetch():
    paths = [os.path.join(HERE, f"prefetch_run{i}.txt") for i in range(1, 6)]
    agg, _, _, _ = aggregate_bench(paths)
    print_bench_table(agg, "Graviton 4 prefetch-kept - medians of 5")

def cmd_ab():
    base_paths = [os.path.join(HERE, f"baseline_run{i}.txt") for i in range(1, 6)]
    pref_paths = [os.path.join(HERE, f"prefetch_run{i}.txt") for i in range(1, 6)]
    base_agg, *_ = aggregate_bench(base_paths)
    pref_agg, *_ = aggregate_bench(pref_paths)
    print("\n=== baseline (no prefetch) vs prefetch-kept: delta% of prefetch vs baseline ===")
    print("     (negative = prefetch faster; positive = prefetch slower, remove is correct)")
    print(f"{'n':>5}  {'gv4 warm':>10}  {'gv4 cold':>10}  {'gv4s warm':>10}  {'gv4s cold':>10}")
    for s in SIZES:
        bw, bc = base_agg[s]
        pw, pc = pref_agg[s]
        def pct(b, p):
            if b == 0: return float('nan')
            return 100.0 * (p - b) / b
        print(f"{s:>5}  "
              f"{pct(bw[7], pw[7]):>9.1f}%  {pct(bc[7], pc[7]):>9.1f}%  "
              f"{pct(bw[8], pw[8]):>9.1f}%  {pct(bc[8], pc[8]):>9.1f}%")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "default"
    {"default":  cmd_default,
     "baseline": cmd_baseline,
     "prefetch": cmd_prefetch,
     "ab":       cmd_ab}[cmd]()

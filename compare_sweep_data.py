#!/usr/bin/env python3
"""Compare two sweep campaigns' paired results, pair by pair and size by size.

Usage (from the repo root):

    python3 compare_sweep_data.py A_data.py B_data.py [--pairs "Fb vs Lem,F vs LemS"]
                                  [--sizes 16,32,...] [--out FILE]

A_data.py and B_data.py are data modules written by compute_sweep_fvl.py for
two campaigns that measured the same pairs (for example the same harness
built two ways, or two campaigns on the same arrays). For every pair, mode
and size present in both, the report gives

    A: median paired delta of the pair in campaign A (percent and ns), verdict
    B: the same in campaign B
    B - A: the difference of the two ns medians (how much campaign B moves the
           pair), and whether the two verdicts agree

and, per pair and mode, the median of B - A over the sizes, split into size
bands. Use it to quantify a harness change (the descriptor-layout A/B of
2026-10-12: desc_align=16 vs 64 builds of bench_sweep_f_vs_lem) or the
reproducibility of two campaigns on identical inputs (sweep_fvl2 vs
sweep_fvl3). Nothing is written unless --out is given.
"""
import argparse
import importlib.util
import statistics
import sys

MODES = ("hb", "hs", "cb", "cs")
MODE_NAMES = {"hb": "hot_bat", "hs": "hot_ser", "cb": "cold_bat", "cs": "cold_ser"}
BANDS = ((1, 32), (33, 128), (129, 265), (266, 512), (513, 1024), (1025, 2048), (2049, 4096), (4097, 1 << 30))


def load(path):
    spec = importlib.util.spec_from_file_location("sweep_data_" + str(abs(hash(path))), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fmt(x, w=8, p=1):
    return f"{'-':>{w}}" if x is None else f"{x:>{w}.{p}f}"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--pairs", help="comma-separated pair keys (default: every pair both modules have)")
    ap.add_argument("--sizes", help="comma-separated sizes (default: every size both modules have)")
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    A, B = load(args.a), load(args.b)
    pairs = [p.strip() for p in args.pairs.split(",")] if args.pairs else [p for p in A.PAIRS if p in B.PAIRS]
    sizes = ([int(s) for s in args.sizes.split(",")] if args.sizes
             else [N for N in A.SIZES if N in set(B.SIZES)])
    if not pairs or not sizes:
        sys.exit("error: the two modules share no pairs or no sizes")

    L = []
    w = L.append
    w(f"Campaign comparison: A = {args.a} ({A.PREFIX}, {len(A.RUNS)} runs) vs B = {args.b} ({B.PREFIX}, {len(B.RUNS)} runs)")
    w(f"host A {A.HOST_LABEL}; host B {B.HOST_LABEL}; {len(sizes)} shared sizes, pairs: {', '.join(pairs)}")
    w("Per cell: the pair's median paired delta in A and in B (percent, ns, verdict), then B - A in ns and "
      "whether the verdicts agree. Negative delta = the first-named variant of the pair faster.")
    w("")
    for pair in pairs:
        w("=" * 110)
        w(f"{pair}" + (f"   ({A.PAIR_ROLES[pair]})" if getattr(A, 'PAIR_ROLES', {}).get(pair) else ""))
        w("=" * 110)
        for mode in MODES:
            w(f"  {MODE_NAMES[mode]}")
            w(f"  {'n':>5}  {'A %':>8} {'A ns':>8} {'A verdict':<12}  {'B %':>8} {'B ns':>8} {'B verdict':<12}  {'B-A ns':>8}  agree")
            diffs = []
            for N in sizes:
                sa = A.PAIRED.get(N, {}).get(mode, {}).get(pair)
                sb = B.PAIRED.get(N, {}).get(mode, {}).get(pair)
                if not sa or not sb or sa.get("median_ns") is None or sb.get("median_ns") is None:
                    continue
                d = sb["median_ns"] - sa["median_ns"]
                diffs.append((N, d))
                agree = "yes" if sa["verdict"] == sb["verdict"] else ("flip" if sa["verdict"].startswith("WIN") and sb["verdict"].startswith("WIN") else "no")
                w(f"  {N:>5}  {fmt(sa['median'])}% {fmt(sa['median_ns'])} {sa['verdict']:<12}  "
                  f"{fmt(sb['median'])}% {fmt(sb['median_ns'])} {sb['verdict']:<12}  {d:>+8.1f}  {agree}")
            if diffs:
                parts = []
                for lo, hi in BANDS:
                    xs = [d for N, d in diffs if lo <= N <= hi]
                    if xs:
                        label = f"{lo}-{hi}" if hi < (1 << 30) else f">={lo}"
                        parts.append(f"{label}: {statistics.median(xs):+.1f} ns ({len(xs)})")
                w(f"  median of B - A by band: " + "; ".join(parts) + f"; all sizes {statistics.median(d for _, d in diffs):+.1f} ns")
            w("")
    # levels of the variants shared by both, for context
    shared_vars = [v for v in A.VARIANTS if v in B.VARIANTS]
    w("=" * 110)
    w("levels (median ns/query) of the shared variants in A and B, and B/A - 1 in percent")
    w("=" * 110)
    for mode in MODES:
        w(f"  {MODE_NAMES[mode]}")
        w(f"  {'n':>5}  " + "  ".join(f"{v:>7}A {v:>7}B {'%':>6}" for v in shared_vars))
        for N in sizes:
            row = []
            for v in shared_vars:
                la = A.LEVELS.get(N, {}).get(mode, {}).get(v)
                lb = B.LEVELS.get(N, {}).get(mode, {}).get(v)
                pct = (lb / la - 1) * 100 if la and lb else None
                row.append(f"{fmt(la)} {fmt(lb)} {fmt(pct, 6)}")
            w(f"  {N:>5}  " + "  ".join(row))
        w("")
    text = "\n".join(L) + "\n"
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(text)
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

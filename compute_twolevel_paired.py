#!/usr/bin/env python3
"""Paired aggregation of bench_twolevel runs.

Usage:
    python3 compute_twolevel_paired.py HOST [--glob PATTERN] [--out FILE]

    HOST     one of pi5 m4 m1 skx emr gv4 (selects HOST_runs/)
    --glob   run files to aggregate (default HOST_runs/twolevel_run*.txt)
    --out    where to write the report (default HOST_runs/twolevel_paired.txt;
             "-" for stdout only)

Why this script exists
----------------------
The per-host compute_twolevel.py scripts take, for every variant and mode,
the median over runs of that variant's cell.  That is fine for *absolute
levels* but wrong for *comparisons*: whole runs drift 1.4-2.2x on some
hosts (governor hops, thermal state, co-tenants), and when each variant's
median is picked from a different run the ratio of medians can invert the
ordering that every individual run shows.  bench_twolevel already prints
paired "X vs Y" deltas per run; this script recomputes them for every pair
and reports, per mode:

  * absolute per-cell medians (levels only, with per-variant min..max)
  * run-level drift (range of each run's geometric mean across variants)
  * per-run ranks: mean rank per variant and the number of runs it won
  * paired deltas for the pairs the write-ups quote: per-run values,
    median, min, max and a sign count ("X faster in k/N runs")
  * the full matrix of median paired deltas

A difference is called a WIN only when the sign count is at least 80% of
the runs and the median paired delta is at least 3%; anything else is a
TIE.  With N=5 a two-sided sign test cannot reach p < 0.0625, so even a
5/5 result is suggestive rather than conclusive; use 10 runs where you can.
"""
import argparse
import glob
import math
import os
import re
import statistics
import sys

MODES = ("hb", "hs", "cb", "cs")
MODE_NAMES = {"hb": "hot_bat", "hs": "hot_ser", "cb": "cold_bat", "cs": "cold_ser"}
VARIANTS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "Lem"]
DESC = {
    "A": "bsearch outer + general-n spine inner",
    "B": "outer spine + general-n spine inner",
    "C": "bsearch outer + compile-time n=4096 inner",
    "D": "outer spine + compile-time n=4096 inner",
    "E": "Shar outer + general-n spine inner",
    "F": "Shar outer + compile-time n=4096 inner",
    "G": "Shar outer + Shar inner (no spine)",
    "H": "Eytzinger outer + K&M prefetch + general-n inner",
    "I": "Eytzinger outer + K&M prefetch + compile-time n=4096 inner",
    "Lem": "Lemire reference (bsearch outer + simd_quad gap-16 inner)",
}
# Pairs quoted in CLAUDE.md / KhuongMorin.md / README, as (X, Y) meaning
# "X relative to Y" (negative delta = X faster).
DEFAULT_PAIRS = [
    ("F", "D"), ("F", "A"), ("F", "C"), ("F", "E"), ("E", "A"),
    ("D", "C"), ("D", "A"), ("B", "A"), ("C", "A"),
    ("I", "F"), ("H", "E"), ("H", "I"), ("I", "D"), ("G", "F"),
    ("F", "Lem"), ("A", "Lem"), ("D", "Lem"), ("I", "Lem"),
]
ROW_RE = re.compile(
    r"^([A-I]|Lem)\s+\S.*?\s+"
    r"(\d+\.\d+|nan)\s+(\d+\.\d+|nan)\s+(\d+\.\d+|nan)\s+(\d+\.\d+|nan)\s*$")
HDR_RE = re.compile(r"^num_sets=(\d+)\s+hot_reps=(\d+).*?mode=(\w+)(?:\s+order_seed=(\d+))?(?:\s+gap=(\d+))?")


def parse_run(path):
    """Return (meta, {var: {mode: value-or-None}}) for one run file."""
    meta = {"file": os.path.basename(path)}
    cells = {}
    with open(path) as fh:
        for line in fh:
            h = HDR_RE.match(line)
            if h:
                meta["num_sets"], meta["hot_reps"], meta["mode"] = int(h.group(1)), int(h.group(2)), h.group(3)
                if h.group(4) is not None:
                    meta["order_seed"] = int(h.group(4))
                if h.group(5) is not None:
                    meta["gap"] = int(h.group(5))
                continue
            if line.startswith("# "):
                k, _, v = line[2:].partition(":")
                meta.setdefault("notes", {})[k.strip()] = v.strip()
                continue
            m = ROW_RE.match(line)
            if m:
                v = m.group(1)
                vals = [None if m.group(i) == "nan" else float(m.group(i)) for i in (2, 3, 4, 5)]
                cells[v] = dict(zip(MODES, vals))
    return meta, cells


def fmt(x, w=10, p=2):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return f"{'-':>{w}}"
    return f"{x:>{w}.{p}f}"


def pct(x, w=8):
    if x is None:
        return f"{'-':>{w}}"
    return f"{x:>+{w}.1f}%"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("host")
    ap.add_argument("--glob", dest="pattern")
    ap.add_argument("--out")
    ap.add_argument("--pairs", nargs="*", help="extra pairs as X/Y, e.g. F/B")
    args = ap.parse_args()

    pattern = args.pattern or f"{args.host}_runs/twolevel_run*.txt"
    files = sorted(glob.glob(pattern))
    if not files:
        sys.exit(f"no run files match {pattern}")
    runs = [parse_run(f) for f in files]
    runs = [(m, c) for m, c in runs if c]
    N = len(runs)
    out_path = args.out or f"{args.host}_runs/twolevel_paired.txt"

    pairs = list(DEFAULT_PAIRS)
    for p in args.pairs or []:
        x, y = p.split("/")
        pairs.append((x, y))

    variants = [v for v in VARIANTS if all(v in c for _, c in runs)]
    lines = []
    w = lines.append

    w(f"Paired aggregation of {N} bench_twolevel runs for host '{args.host}'")
    w(f"pattern: {pattern}")
    for m, _ in runs:
        extra = " ".join(f"{k}={v}" for k, v in m.items() if k not in ("file", "notes"))
        notes = m.get("notes", {})
        note_s = ("  " + "; ".join(f"{k}: {v}" for k, v in notes.items())) if notes else ""
        w(f"  {m['file']}: {extra}{note_s}")
    w("")
    w("Deltas are X/Y - 1 in percent; negative means X is faster. Levels are ns/query.")
    w("WIN = X faster in >= 80% of runs AND |median paired delta| >= 3%; otherwise TIE.")
    w("")

    for mode in MODES:
        name = MODE_NAMES[mode]
        # per-run values, skipping runs where this mode was not measured
        per_run = []  # list of {var: value}
        for _, c in runs:
            vals = {v: c[v][mode] for v in variants}
            if all(x is not None for x in vals.values()):
                per_run.append(vals)
        n = len(per_run)
        w("=" * 78)
        w(f"{name}  ({n} runs with all {len(variants)} variants)")
        w("=" * 78)
        if n == 0:
            w("  no complete runs for this mode")
            w("")
            continue

        # drift
        gms = [math.exp(sum(math.log(r[v]) for v in variants) / len(variants)) for r in per_run]
        w(f"run-level drift: geometric mean across variants per run = "
          + ", ".join(f"{g:.0f}" for g in gms)
          + f"  (max/min = {max(gms)/min(gms):.2f}x)")
        w("")

        # levels
        w(f"{'var':>4}  {'median':>10}  {'min':>10}  {'max':>10}  {'range':>7}   description")
        for v in variants:
            xs = [r[v] for r in per_run]
            med = statistics.median(xs)
            w(f"{v:>4}  {fmt(med)}  {fmt(min(xs))}  {fmt(max(xs))}  {(max(xs)/min(xs)-1)*100:>6.0f}%   {DESC[v]}")
        w("  (levels only: do not difference medians across variants; use the paired deltas below)")
        w("")

        # ranks
        mean_rank = {}
        wins = {v: 0 for v in variants}
        winners = []
        for r in per_run:
            order = sorted(variants, key=lambda v: r[v])
            winners.append(order[0])
            wins[order[0]] += 1
            for rank, v in enumerate(order, 1):
                mean_rank[v] = mean_rank.get(v, 0.0) + rank / n
        w(f"{'var':>4}  {'mean rank':>9}  {'fastest in':>10}   per-run winners: {' '.join(winners)}")
        ranked = sorted(variants, key=lambda v: mean_rank[v])
        for v in ranked:
            w(f"{v:>4}  {mean_rank[v]:>9.2f}  {wins[v]:>6}/{n:<3}")
        best = ranked[0]
        w("")

        # best vs everything (verdict helper)
        w(f"best by mean rank: {best}.  Paired delta of each variant vs {best}:")
        for v in variants:
            if v == best:
                continue
            ds = [(r[v] / r[best] - 1) * 100 for r in per_run]
            med = statistics.median(ds)
            k = sum(1 for d in ds if d > 0)  # runs where best is faster
            verdict = "WIN for " + best if (k >= math.ceil(0.8 * n) and med >= 3) else "TIE"
            w(f"  {v:>3} vs {best:<3}: median {pct(med)}  range [{pct(min(ds))}, {pct(max(ds))}]  {best} faster in {k}/{n}  -> {verdict}")
        w("")

        # named pairs
        w("paired deltas for the pairs quoted in the write-ups (X vs Y = X/Y - 1):")
        for x, y in pairs:
            if x not in variants or y not in variants:
                continue
            ds = [(r[x] / r[y] - 1) * 100 for r in per_run]
            med = statistics.median(ds)
            k = sum(1 for d in ds if d < 0)
            verdict = ("WIN for " + x) if (k >= math.ceil(0.8 * n) and med <= -3) else \
                      ("WIN for " + y) if ((n - k) >= math.ceil(0.8 * n) and med >= 3) else "TIE"
            per = " ".join(f"{d:+.1f}" for d in ds)
            w(f"  {x:>3} vs {y:<3}: median {pct(med)}  [{pct(min(ds))}, {pct(max(ds))}]  {x} faster {k}/{n}  {verdict:<10}  per-run: {per}")
        w("")

        # full matrix
        w("median paired delta matrix (row vs column, %):")
        w("      " + "".join(f"{v:>8}" for v in variants))
        for x in variants:
            row = []
            for y in variants:
                if x == y:
                    row.append(f"{'.':>8}")
                else:
                    ds = [(r[x] / r[y] - 1) * 100 for r in per_run]
                    row.append(f"{statistics.median(ds):>+8.1f}")
            w(f"{x:>5} " + "".join(row))
        w("")

    text = "\n".join(lines) + "\n"
    if out_path != "-":
        with open(out_path, "w") as fh:
            fh.write(text)
        print(f"wrote {out_path}")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()

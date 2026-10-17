#!/usr/bin/env python3
"""Paired per-run aggregation of main-bench (bench.cpp) runs.

Usage (from the repo root):

    python3 compute_bench_paired.py HOST [--glob PATTERN] [--out FILE]
                                    [--pairs B:A,...] [--min-runs K]
                                    [--plot-dicts PREFIX]

    HOST          pi5, m4, m1, skx, emr, gv4: names the host in the report
    --glob        run files (default HOST_runs/rebench_flushed_run*.txt)
    --out         report (default HOST_runs/rebench_flushed_paired.txt; "-" = stdout)
    --pairs       override the pairs, 'B:A,B:A,...' (cell names, see below)
    --min-runs    fewest paired runs a cell needs for a verdict (default 3)
    --plot-dicts  also print per-cell medians as plot.py-style dict literals
                  named PREFIX_warm / PREFIX_cold (plain rows) and
                  PREFIX_aligned_warm / PREFIX_aligned_cold ('nA' rows)

Examples:
    python3 compute_bench_paired.py pi5
    python3 compute_bench_paired.py pi5 --glob 'pi5_runs/rebench_run*.txt' --out -
        (the pre-flush archive: levels reproduce plot.py's pi5 dicts)

Input
-----
bench.cpp output: '# key: value' header lines written by the driver
(pi5_runs/run_bench_flushed.sh), the harness's '# cold column:' and
'# aligned rows:' provenance lines, the column header, and per size

    <n>   | <warm cols> | <cold cols>          plain row (std::vector storage)
    <n>A  | <warm cols> | <cold cols>          aligned row (line-aligned copies, 64 B
                                              except 128 B on Apple hosts;
                                              bench.cpp since 2026-10-12)
    <n>*  | X=<w> Y=<w>  (warm)  | X=<c> Y=<c>  (cold)   A/B rows (spine_N, pad, 4096)

Column names come from the header line (ARM: linear binary simd pi5 pi5s m4
m4s gv4 gv4s; x86: linear binary simd intel intels). Cell names: a column
name for a plain-row cell, the column name + 'A' for an aligned-row cell,
and the right-hand name of an A/B row (e.g. pi5_spine_4096, gv4_spine_pad)
for that row's value; when an A/B row repeats within a run (the 4096*
pi5_spine_4096 row is printed twice) the LAST occurrence wins, as
{host}_runs/compute_medians.py and reproduce.sh do.

Why paired
----------
Whole runs drift (the Pi 5 archive has a 1.45-1.5x warm slow mode under the
ondemand governor), so differencing per-cell medians across columns measures
the drift as much as the kernels. Every comparison here is made within a run
and summarised over runs: for a pair 'B vs A' and each (size, regime) the
per-run delta (B/A - 1) * 100 (negative = B faster), its median, the sign
count, the paired ns delta, and the project verdict

    WIN(B)  B faster in >= 80% of the paired runs and median <= -3%
    WIN(A)  B slower in >= 80% of the paired runs and median >= +3%
    TIE     otherwise                      (n/a: fewer than --min-runs runs)

Default pairs (every size where both cells exist):
    gv4 vs pi5          in-loop prefetch in runs made before 2026-10-13:
                        simd_quad_graviton was simd_quad_pi5 minus the prefetch
                        line (negative = no prefetch faster); since the Pi 5
                        kernel dropped the line the two compile to identical
                        instructions and the pair is a second noise gauge
    gv4s vs pi5s        identical code (the spine kernels are byte-identical):
                        a noise gauge for the WIN rule in this harness
    pi5s vs pi5         the spine's value against the plain kernel
    <col>A vs <col>     alignment, one pair per column (negative = aligned faster)
    pi5_spine_4096 vs pi5s, m4_spine_4096 vs m4s, gv4_spine_4096 vs gv4s
                        compile-time n=4096 hybrids vs the general-n spine (n=4096)
    pi5_spine_N vs pi5s, gv4_spine_N vs gv4s for N in 256..2048
                        the compile-time family vs the general-n spine
    gv4_spine_pad vs gv4s   the padded descent
On x86 the pairs are intels vs intel, <col>A vs <col>, intel_spine_4096 vs
intels, intel_spine_N vs intels and intel_spine_pad vs intels.
"""
import argparse
import datetime
import glob
import math
import os
import re
import statistics
import sys

REGIMES = ("warm", "cold")
WIN_MIN_PCT = 3.0
HOST_LABEL = {
    "pi5": "Raspberry Pi 5 (Cortex-A76)",
    "m4": "Apple M4 Max",
    "m1": "Apple M1 Pro",
    "skx": "Intel Skylake-SP",
    "emr": "Intel Emerald Rapids",
    "gv4": "AWS Graviton 4 (Neoverse V2)",
    "cfl": "Intel Coffee Lake (i9-9980HK, 2019 MacBook Pro)",
    "icx": "Intel Ice Lake-SP (Xeon Platinum 8375C, AWS i4i.32xlarge)",
}
# plot.py's display names for the columns.
DISPLAY = {
    "linear": "linear (std::find)",
    "binary": "binary (std::binary_search)",
    "simd": "simd_quad (reference)",
    "pi5": "simd_quad_pi5",
    "pi5s": "simd_quad_pi5 + spine",
    "m4": "simd_quad_m4",
    "m4s": "simd_quad_m4 + spine",
    "gv4": "simd_quad_graviton",
    "gv4s": "simd_quad_graviton + spine",
    "intel": "simd_quad_intel",
    "intels": "simd_quad_intel + spine",
}

HEADER_COLS_RE = re.compile(r"warm ns/q:\s+(.*?)\s*\|")
ROW_RE = re.compile(r"^\s*(\d+)\s*\|\s*(.*?)\|(.*)$")
ROW_A_RE = re.compile(r"^\s*(\d+)A\s*\|\s*(.*?)\|(.*)$")
STAR_RE = re.compile(r"^\s*(\d+)\*\s*\|\s*(\w+)=([\d.]+)\s+(\w+)=([\d.]+)\s*\(warm\)\s*\|\s*(\w+)=([\d.]+)\s+(\w+)=([\d.]+)\s*\(cold\)")
RUN_RE = re.compile(r"run(\d+)\.txt$")


def need_for_win(n):
    return (4 * n + 4) // 5


def parse_run(path):
    """-> dict with 'meta', 'notes', 'cols', 'cells' {(size, regime, name): ns}, 'order' [names seen]."""
    meta, notes, cols, cells = {}, [], None, {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\r\n")
            if line.startswith("#"):
                body = line.lstrip("#").strip()
                if body.startswith(("cold column", "aligned rows")):
                    notes.append(body)
                elif ":" in body:
                    k, _, v = body.partition(":")
                    meta[k.strip()] = v.strip()
                continue
            m = HEADER_COLS_RE.search(line)
            if m and cols is None:
                cols = m.group(1).split()
                continue
            m = STAR_RE.match(line)
            if m:
                size = int(m.group(1))
                # m.group(2)=left name, (4)=right name; the right-hand cell is the A/B subject.
                cells[(size, "warm", m.group(4))] = float(m.group(5))
                cells[(size, "cold", m.group(8))] = float(m.group(9))
                continue
            m = ROW_A_RE.match(line)
            if m and cols:
                size = int(m.group(1))
                w = [float(x) for x in m.group(2).split()]
                c = [float(x) for x in m.group(3).split()]
                if len(w) >= len(cols) and len(c) >= len(cols):
                    for i, name in enumerate(cols):
                        cells[(size, "warm", name + "A")] = w[i]
                        cells[(size, "cold", name + "A")] = c[i]
                continue
            m = ROW_RE.match(line)
            if m and cols:
                size = int(m.group(1))
                w = [float(x) for x in m.group(2).split()]
                c = [float(x) for x in m.group(3).split()]
                if len(w) >= len(cols) and len(c) >= len(cols):
                    for i, name in enumerate(cols):
                        cells[(size, "warm", name)] = w[i]
                        cells[(size, "cold", name)] = c[i]
    return {"path": path, "meta": meta, "notes": notes, "cols": cols or [], "cells": cells}


def default_pairs(cols, names):
    pairs = []
    if "pi5" in cols:
        pairs += [("gv4", "pi5"), ("gv4s", "pi5s"), ("pi5s", "pi5"), ("m4s", "m4"), ("gv4s", "gv4")]
    if "intel" in cols:
        pairs += [("intels", "intel")]
    for c in cols:
        if c + "A" in names:
            pairs.append((c + "A", c))
    for base, spine_col in (("pi5", "pi5s"), ("m4", "m4s"), ("gv4", "gv4s"), ("intel", "intels")):
        if spine_col not in cols:
            continue
        for n in (256, 512, 1024, 2048, 4096):
            nm = f"{base}_spine_{n}"
            if nm in names:
                pairs.append((nm, spine_col))
        if f"{base}_spine_pad" in names:
            pairs.append((f"{base}_spine_pad", spine_col))
    return pairs


def fnum(x, w=8, p=2):
    return f"{'-':>{w}}" if x is None else f"{x:>{w}.{p}f}"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("host")
    ap.add_argument("--glob")
    ap.add_argument("--out")
    ap.add_argument("--pairs")
    ap.add_argument("--min-runs", type=int, default=3)
    ap.add_argument("--plot-dicts")
    args = ap.parse_args(argv)
    host = args.host
    pattern = args.glob or f"{host}_runs/rebench_flushed_run*.txt"
    out_path = args.out or f"{host}_runs/rebench_flushed_paired.txt"

    paths = sorted(glob.glob(pattern), key=lambda p: (int(RUN_RE.search(p).group(1)) if RUN_RE.search(p) else 0, p))
    if not paths:
        sys.exit(f"error: no files match {pattern}")
    runs = []
    for p in paths:
        r = parse_run(p)
        m = RUN_RE.search(p)
        r["run"] = int(m.group(1)) if m else len(runs) + 1
        if not r["cells"]:
            print(f"warning: no rows parsed in {p}; skipped", file=sys.stderr)
            continue
        runs.append(r)
    if not runs:
        sys.exit("error: no usable runs")
    cols = runs[0]["cols"]
    names = sorted({k[2] for r in runs for k in r["cells"]}, key=lambda s: (len(s), s))
    sizes = sorted({k[0] for r in runs for k in r["cells"]})
    if args.pairs:
        pairs = [tuple(p.split(":")) for p in args.pairs.split(",") if p.strip()]
        if any(len(p) != 2 for p in pairs):
            sys.exit("error: --pairs wants 'B:A,B:A,...'")
    else:
        pairs = default_pairs(cols, set(names))
    pairs = [p for p in pairs if any((s, rg, p[0]) in r["cells"] and (s, rg, p[1]) in r["cells"]
                                     for r in runs for s in sizes for rg in REGIMES)]

    # levels
    levels, nruns = {}, {}
    for s in sizes:
        for rg in REGIMES:
            for nm in names:
                xs = [r["cells"][(s, rg, nm)] for r in runs if (s, rg, nm) in r["cells"]]
                if xs:
                    levels[(s, rg, nm)] = statistics.median(xs)
                    nruns[(s, rg, nm)] = len(xs)

    # paired
    paired = {}
    for b, a in pairs:
        for s in sizes:
            for rg in REGIMES:
                rs = [r for r in runs if (s, rg, b) in r["cells"] and (s, rg, a) in r["cells"]]
                if not rs:
                    continue
                ds = [(r["cells"][(s, rg, b)] / r["cells"][(s, rg, a)] - 1.0) * 100.0 for r in rs]
                nds = [r["cells"][(s, rg, b)] - r["cells"][(s, rg, a)] for r in rs]
                n = len(ds)
                neg = sum(1 for d in ds if d < 0)
                pos = sum(1 for d in ds if d > 0)
                med = statistics.median(ds)
                if n < args.min_runs:
                    verdict = "n/a"
                else:
                    need = need_for_win(n)
                    if neg >= need and med <= -WIN_MIN_PCT:
                        verdict = f"WIN({b})"
                    elif pos >= need and med >= WIN_MIN_PCT:
                        verdict = f"WIN({a})"
                    else:
                        verdict = "TIE"
                paired[(b, a, s, rg)] = {"runs": [r["run"] for r in rs], "deltas": ds, "median": med,
                                         "faster": neg, "slower": pos, "n": n, "verdict": verdict,
                                         "median_ns": statistics.median(nds)}

    # drift gauge: per run, geometric mean over the plain-column cells every run has
    drift = {}
    for rg in REGIMES:
        common = None
        for r in runs:
            ks = {k for k in r["cells"] if k[1] == rg and k[2] in cols}
            common = ks if common is None else common & ks
        if common and len(runs) > 1:
            drift[rg] = {r["run"]: math.exp(sum(math.log(r["cells"][k]) for k in common) / len(common)) for r in runs}, len(common)

    # report
    L = []
    w = L.append
    w(f"Paired per-run aggregation of main-bench runs on host '{host}' ({HOST_LABEL.get(host, host)})")
    w(f"files ({len(runs)}): " + ", ".join(os.path.basename(r['path']) for r in runs))
    w(f"columns: {' '.join(cols)}; sizes: {len(sizes)} ({sizes[0]}..{sizes[-1]}); cell names: {', '.join(names)}")
    for key in ("date", "host", "machine", "command", "build", "compiler", "governor"):
        vals = sorted({r["meta"].get(key, "") for r in runs} - {""})
        if vals:
            w(f"{key}: " + ("; ".join(vals) if len(vals) <= 3 else f"{vals[0]} .. {vals[-1]} ({len(vals)} distinct)"))
    temps = []
    for r in runs:
        for key in ("temp_before", "temp_after"):
            v = r["meta"].get(key, "").rstrip("'C ")
            try:
                temps.append(float(v))
            except ValueError:
                pass
    if temps:
        w(f"temperature: {min(temps):.1f}..{max(temps):.1f} C (temp_before/temp_after)")
    notes = sorted({n for r in runs for n in r["notes"]})
    for n in notes:
        w(f"harness note: {n}")
    missing_notes = [os.path.basename(r["path"]) for r in runs if not any(n.startswith("cold column") for n in r["notes"])]
    if missing_notes:
        w(f"WARNING: no '# cold column:' line (pre-flush bench.cpp) in: {', '.join(missing_notes)}")
    exits = sorted({r["meta"].get("exit", "?") for r in runs})
    w(f"exit statuses: {', '.join(exits)}")
    w("")
    w("Deltas are B/A - 1 in percent for a pair 'B vs A'; negative means B is faster. Levels are ns/query.")
    w(f"WIN(X) = X faster in >= 80% of the paired runs (ceil(0.8 n)) AND |median paired delta| >= {WIN_MIN_PCT:.0f}%; "
      f"otherwise TIE; n/a = fewer than {args.min_runs} paired runs.")
    w("")
    w("=" * 100)
    w("run-level drift (geometric mean over the plain-column cells every run has, per run)")
    w("=" * 100)
    for rg in REGIMES:
        if rg in drift:
            gms, nc = drift[rg]
            w(f"  {rg:5s} " + ", ".join(f"run{r}: {g:.2f}" for r, g in sorted(gms.items()))
              + f"  (max/min = {max(gms.values()) / min(gms.values()):.2f}x over {nc} shared cells)")
        else:
            w(f"  {rg:5s} not computable")
    w("")
    for rg in REGIMES:
        w("=" * 100)
        w(f"levels, {rg}: per-cell medians (ns/query) over the runs that have the cell [runs]")
        w("=" * 100)
        shown = [nm for nm in names if any((s, rg, nm) in levels for s in sizes)]
        w(f"{'n':>5}  " + " ".join(f"{nm:>12}" for nm in shown))
        for s in sizes:
            row = []
            for nm in shown:
                v = levels.get((s, rg, nm))
                row.append(f"{'-':>12}" if v is None else f"{v:>8.2f}[{nruns[(s, rg, nm)]:>2}]")
            w(f"{s:>5}  " + " ".join(row))
        w("")
    for b, a in pairs:
        w("=" * 100)
        w(f"paired: {b} vs {a}  (delta = {b}/{a} - 1 per run; negative = {b} faster)")
        w(f"cell = median delta %, sign count ('-k/n' = {b} faster in k of n runs), median ns delta, verdict")
        w("=" * 100)
        w(f"{'n':>5}  {'warm':^44}  {'cold':^44}")
        counts = {rg: {"b": 0, "a": 0, "tie": 0} for rg in REGIMES}
        for s in sizes:
            row = []
            any_cell = False
            for rg in REGIMES:
                st = paired.get((b, a, s, rg))
                if st is None:
                    row.append(f"{'-':>44}")
                    continue
                any_cell = True
                sc = (f"-{st['faster']}/{st['n']}" if st["median"] < 0 else
                      f"+{st['slower']}/{st['n']}" if st["median"] > 0 else f"0/{st['n']}")
                row.append(f"{st['median']:>+8.2f}% {sc:>6} {st['median_ns']:>+9.2f} ns {st['verdict']:<12}")
                if st["verdict"] == f"WIN({b})":
                    counts[rg]["b"] += 1
                elif st["verdict"] == f"WIN({a})":
                    counts[rg]["a"] += 1
                elif st["verdict"] == "TIE":
                    counts[rg]["tie"] += 1
            if any_cell:
                w(f"{s:>5}  " + "  ".join(row))
        w("  verdicts: " + "; ".join(f"{rg}: WIN({b}) {c['b']}, WIN({a}) {c['a']}, TIE {c['tie']}" for rg, c in counts.items()))
        w("")
    w(f"generated {datetime.datetime.now().isoformat(timespec='seconds')} by compute_bench_paired.py "
      + " ".join(argv if argv is not None else sys.argv[1:]))
    text = "\n".join(L) + "\n"
    if out_path == "-":
        sys.stdout.write(text)
    else:
        with open(out_path, "w") as fh:
            fh.write(text)
        print(f"wrote {out_path}")

    if args.plot_dicts:
        pre = args.plot_dicts
        print(f"# per-cell medians of {len(runs)} run(s): {', '.join(os.path.basename(r['path']) for r in runs)}")
        print(f"{pre}_sizes = {sizes!r}")
        for suffix, al in (("", ""), ("_aligned", "A")):
            for rg in REGIMES:
                rows = []
                for c in cols:
                    vals = [levels.get((s, rg, c + al)) for s in sizes]
                    if all(v is None for v in vals):
                        continue
                    rows.append(f'    "{DISPLAY.get(c, c)}":' + " " * max(1, 30 - len(DISPLAY.get(c, c))) + "["
                                + ", ".join(f"{v:>8.2f}" if v is not None else "    None" for v in vals) + "],")
                if rows:
                    print(f"{pre}{suffix}_{rg} = {{")
                    print("\n".join(rows))
                    print("}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

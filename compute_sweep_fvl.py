#!/usr/bin/env python3
"""Paired per-run aggregation of a bench_sweep_f_vs_lem campaign.

Usage (from the repo root):

    python3 compute_sweep_fvl.py HOST [--prefix PREFIX] [--dir DIR]
                                 [--runs 1,2,3,4,5] [--list FILE]
                                 [--min-runs K] [--out FILE] [--data FILE]

    HOST        pi5, m4, m1, skx, emr, gv4 ...: selects HOST_runs/ (or --dir)
    --prefix    per-cell file prefix (default sweep_fvl2, the three-variant
                campaigns; the archived 2026-05-20 M4 campaign is sweep_fvl;
                the five-variant campaigns since 2026-10-12 are sweep_fvl3;
                sweep_ab1 is the six-variant Pi 5 kernel A/B of
                bench_ab_pi5.cpp, whose pairs are preset below)
    --pairs     override the pairs, 'B:A,B:A,...' (for a prefix without a preset)
    --dir       directory holding the cells (default HOST_runs)
    --runs      comma-separated run indices to use (default: every run found)
    --list      size list file (one N per line); restricts the sizes and
                fixes their order (default: every N found, ascending)
    --min-runs  fewest paired runs a cell needs before it gets a verdict
                (default 3; cells with fewer are reported as n/a)
    --out       report (default DIR/PREFIX_paired.txt; "-" for stdout only)
    --data      data module (default HOST_PREFIX_data.py in the cwd;
                "-" writes none)

Examples:
    python3 compute_sweep_fvl.py m4 --prefix sweep_fvl
        -> m4_runs/sweep_fvl_paired.txt and m4_sweep_fvl_data.py
    python3 compute_sweep_fvl.py pi5
        -> pi5_runs/sweep_fvl2_paired.txt and pi5_sweep_fvl2_data.py
    python3 compute_sweep_fvl.py pi5 --prefix sweep_fvl3
        -> pi5_runs/sweep_fvl3_paired.txt and pi5_sweep_fvl3_data.py
    python3 compute_sweep_fvl.py pi5 --prefix sweep_ab1
        -> pi5_runs/sweep_ab1_paired.txt and pi5_sweep_ab1_data.py

Input
-----
A cell is one (inner_n, mode, run) measurement of bench_sweep_f_vs_lem. It
is either the per-cell file DIR/PREFIX_n<N>_<mode>_run<R>.txt or an entry of
the consolidated archive DIR/PREFIX_raw.txt ('### <basename>' then the
file's lines verbatim; see consolidate_sweep.py). The per-cell file wins
when both exist. A cell holds optional '# ...' header lines -- the Pi 5
driver writes '# host:', '# date:', '# governor:', '# temp_c:' and
'# command:'; the harness writes '# bench_sweep_f_vs_lem inner_n=... mode=...
num_sets=... hot_reps=... [order_seed=... gap=... inner=...]',
'# variants: ...' and '# timing order: ...' -- and one line

    RESULT inner_n=<N> mode=<hb|hs|cb|cs> F=<ns> Lem=<ns> [Lem2=<ns>] [Fb=<ns> LemS=<ns>]

(ns per query; Lem2 is absent in the archived M4 campaign, Fb and LemS --
the bsearch-outer + spine-inner and Shar-outer + Lemire-inner cross
variants -- exist from the 2026-10-12 harness on). Cells of the Pi 5 kernel
A/B harness bench_ab_pi5.cpp (prefix sweep_ab1) have the same shape with a
'# bench_ab_pi5 ...' header and the columns F, Fcr, Fd1, Fa, G, Gnp; the
preset table PRESETS below gives that prefix its pairs. A cell without
a RESULT line (for example one ending in '# FAILED exit 1'), or whose RESULT
disagrees with its file name about inner_n or mode, is reported and skipped.
Modes: hb = hot_bat, hs = hot_ser, cb = cold_bat, cs = cold_ser.

Why paired
----------
The level-only aggregators (m4_runs/compute_sweep_f_vs_lem.py and friends)
take, per variant, the median over runs. Whole runs drift (1.2-1.6x between
runs on the Pi 5 and the M4 Max), so differencing two variants' medians
measures the drift as much as the variants, and when the two medians come
from different run sets (a missing or failed cell) the ratio of medians can
invert the ordering that every single run shows. This script keeps each
run's measurements together. For every (N, mode) and every pair B vs A it
computes the per-run delta (B/A - 1) * 100 (negative = B faster), reports
the median, the sign count and a verdict by the project rule

    WIN(B)  B faster in >= 80% of the paired runs and median <= -3%
    WIN(A)  B slower in >= 80% of the paired runs and median >= +3%
    TIE     otherwise                 (n/a: fewer than --min-runs paired runs)

and joins neighbouring sizes with the same winner into bands. The per-cell
medians (levels) are still printed, for absolute numbers only. With five
runs even 5/5 is suggestive rather than conclusive (a two-sided sign test
cannot reach p < 0.0625); ten runs are better.

Each pair also gets the paired absolute delta B - A in ns (per run, median
over runs). For the outer x inner pairs of the five-variant harness that is
the quantity of interest: a cost that sits in the outer search should be a
constant number of ns across sizes, so the report summarises it by size band.

Output
------
The report (--out) holds the campaign facts, the run-level drift gauge,
the levels table, one paired table per pair, the band summary and the list
of missing cells. The data module (--data) holds the same results as Python
literals in the schema described in its docstring; plot_sweep_fvl.py reads
it. Nothing under DIR other than the report is ever written.
"""
import argparse
import datetime
import math
import os
import re
import statistics
import sys

MODES = ("hb", "hs", "cb", "cs")
MODE_NAMES = {"hb": "hot_bat", "hs": "hot_ser", "cb": "cold_bat", "cs": "cold_ser"}
CANONICAL_VARIANTS = ("F", "Lem", "Lem2", "Fb", "LemS")
# (B, A): the pair's delta is (B/A - 1) * 100 per run, negative = B faster.
# The first three compare the Lemire kernels with F; the last four are the
# single-factor contrasts of the {Shar, bsearch} outer x {spine, Lemire}
# inner square (Fb = bsearch + spine, LemS = Shar + Lemire): Fb vs F and
# Lem vs LemS read "bsearch outer vs Shar outer" (negative = bsearch faster)
# with the spine and the Lemire inner respectively; Fb vs Lem and F vs LemS
# read "spine inner vs Lemire inner" (negative = spine faster) with the
# bsearch and the Shar outer respectively.
CANONICAL_PAIRS = (("Lem", "F"), ("Lem2", "F"), ("Lem2", "Lem"),
                   ("Fb", "F"), ("Lem", "LemS"), ("Fb", "Lem"), ("F", "LemS"))
PAIR_ROLE = {
    "Fb vs F": "outer: bsearch vs Shar, spine inner",
    "Lem vs LemS": "outer: bsearch vs Shar, Lemire inner",
    "Fb vs Lem": "inner: spine vs Lemire, bsearch outer",
    "F vs LemS": "inner: spine vs Lemire, Shar outer",
    # Pi 5 kernel A/B (bench_ab_pi5.cpp, prefix sweep_ab1, 2026-10-12). Every
    # pair is a single kernel-side change against F; F itself is the F of
    # the sweep_fvl2 / sweep_fvl3 campaigns (same arrays, same targets).
    "Fcr vs F": "kernel: the constant-return scalar-sweep source form as compiled by GCC 17 vs the shipped cset-return form (differs where a sweep runs: n < 32, tails)",
    "Fd1 vs F": "kernel: spine descent from two blocks vs delegation to the plain kernel (differs at n = 64..127)",
    "Fa vs F": "data: line-aligned arrays and spines (64 B on the Pi 5; the align= header field) vs std::vector (16-byte) storage, same code",
    "G vs F": "kernel: plain simd_quad_pi5 vs the spine kernel (same source and traffic below 128 but a separate compilation of the delegated copy = codegen-plus-noise gauge; the delegation-threshold-7 contrast at 128..255; the spine's own value from 256)",
    "Gnp vs G": "kernel: no in-loop prefetch vs the shipped prefetch (identical code below 128; differs where the quaternary loop iterates)",
    "Gnp vs F": "kernel: prefetch-free plain kernel vs the spine kernel (threshold-7 contrast with the prefetch removed)",
}
# Campaign presets keyed by file prefix: the variant order, the pairs and a
# title. Prefixes not listed here are F-vs-Lemire campaigns (sweep_fvl,
# sweep_fvl2, sweep_fvl3) and use the canonical sets above.
PRESETS = {
    "sweep_ab1": {
        "variants": ("F", "Fcr", "Fd1", "Fa", "G", "Gnp"),
        "pairs": (("Fcr", "F"), ("Fd1", "F"), ("Fa", "F"), ("G", "F"), ("Gnp", "G"), ("Gnp", "F")),
        "title": "Pi 5 kernel A/B sweep",
        # Size bands for the ns summary that follow this campaign's contrast
        # ranges: sweeps run at n < 32 and in tails; Fd1 differs at 64..127;
        # G/Gnp vs F is the threshold-7 contrast at 128..255 and the spine's
        # value from 256; the quaternary loop (and the prefetch) runs from 128.
        "bands": ((1, 7), (8, 15), (16, 31), (32, 63), (64, 127), (128, 255), (256, 511),
                  (512, 1023), (1024, 2047), (2048, 4096), (4097, 1 << 30)),
    },
}
DEFAULT_TITLE = "F-vs-Lemire sweep"
# Size bands for the absolute-delta summary (inclusive bounds).
NS_BANDS = ((1, 32), (33, 128), (129, 265), (266, 512), (513, 1024), (1025, 2048), (2049, 4096), (4097, 1 << 30))
HOST_LABEL = {
    "pi5": "Raspberry Pi 5 (Cortex-A76)",
    "m4": "Apple M4 Max",
    "m1": "Apple M1 Pro",
    "skx": "Intel Skylake-SP",
    "emr": "Intel Emerald Rapids",
    "gv4": "AWS Graviton 4 (Neoverse V2)",
    "cfl": "Intel Coffee Lake (i9-9980HK, 2019 MacBook Pro)",
}
HOST_GAP = {"pi5": 32, "m4": 64, "m1": 64, "skx": 32, "emr": 32, "gv4": 32, "cfl": 32}
DESIGN_MAX = 4096
WIN_MIN_PCT = 3.0

RESULT_RE = re.compile(r"^RESULT\s+(.*\S)\s*$")
KV_RE = re.compile(r"(\w+)=(\S+)")


def need_for_win(n):
    """Runs that must agree in sign for a WIN: ceil(0.8 n), in integers."""
    return (4 * n + 4) // 5


def pair_key(pair):
    return f"{pair[0]} vs {pair[1]}"


def cell_regex(prefix):
    """Match PREFIX_n<N>_<mode>_run<R>.txt and nothing else."""
    return re.compile(r"^" + re.escape(prefix) + r"_n(\d+)_([a-z]+)_run(\d+)\.txt$")


def read_raw(path):
    """basename -> list of lines, from a consolidate_sweep.py archive ({} if absent)."""
    entries = {}
    if not os.path.exists(path):
        return entries
    with open(path, encoding="utf-8", errors="replace") as fh:
        cur = None
        for line in fh:
            if line.startswith("### "):
                cur = entries[line[4:].rstrip("\r\n")] = []
            elif cur is not None:
                cur.append(line)
    return entries


def discover(directory, prefix):
    """All cells of the campaign: (N, mode, run) -> (basename, lines, source)."""
    rx = cell_regex(prefix)
    try:
        names = os.listdir(directory)
    except OSError as e:
        sys.exit(f"error: cannot list {directory}: {e}")
    file_names = sorted(n for n in names if rx.match(n))
    raw_path = os.path.join(directory, f"{prefix}_raw.txt")
    raw = read_raw(raw_path)
    sources = {"files": len(file_names), "raw_entries": len(raw),
               "raw_path": raw_path if raw else None, "overridden": 0, "raw_unmatched": []}
    cells = {}
    for name, lines in raw.items():
        m = rx.match(name)
        if not m:
            sources["raw_unmatched"].append(name)
            continue
        cells[(int(m.group(1)), m.group(2), int(m.group(3)))] = (name, lines, "raw")
    for name in file_names:
        m = rx.match(name)
        key = (int(m.group(1)), m.group(2), int(m.group(3)))
        with open(os.path.join(directory, name), encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
        if key in cells:
            sources["overridden"] += 1
        cells[key] = (name, lines, "file")
    return cells, sources


def parse_cell(lines):
    """Parse one cell's lines into values, driver meta and harness header fields."""
    cell = {"values": {}, "meta": {}, "harness": {}, "notes": [], "failed": None,
            "result_n": None, "result_mode": None}
    for raw in lines:
        line = raw.rstrip("\r\n")
        m = RESULT_RE.match(line)
        if m:
            kv = dict(KV_RE.findall(m.group(1)))
            try:
                cell["result_n"] = int(kv.pop("inner_n"))
            except (KeyError, ValueError):
                pass
            cell["result_mode"] = kv.pop("mode", None)
            vals = {}
            for k, v in kv.items():
                try:
                    x = float(v)
                except ValueError:
                    continue
                if math.isfinite(x) and x > 0:
                    vals[k] = x
            cell["values"] = vals
            continue
        if line.startswith("#"):
            body = line.lstrip("#").strip()
            if body.startswith(("bench_sweep", "bench_ab")):
                cell["harness"] = dict(KV_RE.findall(body))
            elif body.startswith("FAILED"):
                cell["failed"] = body
            elif ":" in body:
                k, _, v = body.partition(":")
                cell["meta"][k.strip()] = v.strip()
            elif body:
                cell["notes"].append(body)
    return cell


def paired_stats(runs, deltas, min_runs, b, a, ns_deltas=None):
    n = len(deltas)
    ns_deltas = list(ns_deltas) if ns_deltas is not None else []
    neg = sum(1 for d in deltas if d < 0)
    pos = sum(1 for d in deltas if d > 0)
    med = statistics.median(deltas) if deltas else None
    if n == 0 or n < min_runs:
        verdict = "n/a"
    else:
        need = need_for_win(n)
        if neg >= need and med <= -WIN_MIN_PCT:
            verdict = f"WIN({b})"
        elif pos >= need and med >= WIN_MIN_PCT:
            verdict = f"WIN({a})"
        else:
            verdict = "TIE"
    return {"runs": runs, "deltas": deltas, "median": med, "faster": neg, "slower": pos,
            "n": n, "verdict": verdict,
            "ns_deltas": ns_deltas, "median_ns": statistics.median(ns_deltas) if ns_deltas else None}


def winner_of(verdict):
    return verdict[4:-1] if verdict.startswith("WIN(") else None


def bands_for(pair, mode, sizes, results):
    """Maximal runs of consecutive sizes (in report order) with the same WIN winner."""
    out, cur = [], None
    for N in sizes:
        st = results[(N, mode)]["pairs"][pair]
        w = winner_of(st["verdict"])
        if w is None:
            if cur:
                out.append(cur)
            cur = None
            continue
        if cur and cur["winner"] == w:
            cur["sizes"].append(N)
            cur["cells"].append(st)
        else:
            if cur:
                out.append(cur)
            cur = {"winner": w, "sizes": [N], "cells": [st]}
    if cur:
        out.append(cur)
    return out


def band_summary(band, pair):
    b, a = pair
    winner = band["winner"]
    cells = band["cells"]
    meds = [c["median"] for c in cells]
    ks = [c["faster"] if winner == b else c["slower"] for c in cells]
    ns = [c["n"] for c in cells]
    return {"winner": winner, "loser": a if winner == b else b, "sizes": list(band["sizes"]),
            "lo": band["sizes"][0], "hi": band["sizes"][-1],
            "median_min": min(meds), "median_max": max(meds),
            "sign_min": min(ks), "sign_max": max(ks), "n_min": min(ns), "n_max": max(ns)}


def fmt_band(s, mode):
    if len(s["sizes"]) == 1:
        rng, count = f"n={s['lo']}", "single size"
    else:
        rng, count = f"n={s['lo']}-{s['hi']}", f"{len(s['sizes'])} sizes"
    if len(s["sizes"]) == 1 or s["median_min"] == s["median_max"]:
        med = f"paired median {s['median_min']:+.1f}%"
    else:
        med = f"paired medians {s['median_min']:+.1f}% to {s['median_max']:+.1f}%"
    if s["sign_min"] == s["sign_max"] and s["n_min"] == s["n_max"]:
        sign = f"{s['winner']} faster {s['sign_min']}/{s['n_min']}"
        sign += " in every cell" if len(s["sizes"]) > 1 else ""
    else:
        # Ranges of k and of n over the band's cells, reported separately: the
        # smallest k need not belong to the cell with the largest n.
        ks = (f"{s['sign_min']}" if s["sign_min"] == s["sign_max"]
              else f"{s['sign_min']}-{s['sign_max']}")
        ns = (f"{s['n_min']}" if s["n_min"] == s["n_max"]
              else f"{s['n_min']}-{s['n_max']}")
        sign = f"{s['winner']} faster in {ks} of {ns} runs per cell"
    return f"{s['winner']} faster than {s['loser']}: {rng} ({MODE_NAMES[mode]}; {count}; {med}; {sign})"


def drift_gauge(mode, runs, sizes, parsed, variants):
    """Per-run geometric mean over the (N, variant) cells every run has for this mode."""
    per_run = {}
    for r in runs:
        s = {}
        for N in sizes:
            c = parsed.get((N, mode, r))
            if c:
                for v in variants:
                    x = c["values"].get(v)
                    if x:
                        s[(N, v)] = x
        if s:
            per_run[r] = s
    if len(per_run) < 2:
        return None
    common = set.intersection(*(set(s) for s in per_run.values()))
    if not common:
        return None
    gms = {r: math.exp(sum(math.log(s[k]) for k in common) / len(common)) for r, s in per_run.items()}
    return gms, len(common)


def fnum(x, w=8, p=3):
    return f"{'-':>{w}}" if x is None else f"{x:>{w}.{p}f}"


def compress_ranges(values):
    """[1,2,3,7,9,10] -> '1-3, 7, 9-10'."""
    out, start, prev = [], None, None
    for v in values:
        if start is None:
            start = prev = v
        elif v == prev + 1:
            prev = v
        else:
            out.append(f"{start}-{prev}" if start != prev else f"{start}")
            start = prev = v
    if start is not None:
        out.append(f"{start}-{prev}" if start != prev else f"{start}")
    return ", ".join(out)


def pylit_float(x, p=5):
    return "None" if x is None else repr(round(x, p))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("host")
    ap.add_argument("--prefix", default="sweep_fvl2")
    ap.add_argument("--dir")
    ap.add_argument("--runs")
    ap.add_argument("--list")
    ap.add_argument("--min-runs", type=int, default=3)
    ap.add_argument("--out")
    ap.add_argument("--data")
    ap.add_argument("--pairs", help="override the pairs: 'B:A,B:A,...' (B/A - 1, negative = B faster)")
    args = ap.parse_args(argv)

    host, prefix = args.host, args.prefix
    directory = args.dir or f"{host}_runs"
    out_path = args.out or os.path.join(directory, f"{prefix}_paired.txt")
    data_path = args.data or f"{host}_{prefix}_data.py"
    if args.min_runs < 1:
        sys.exit("error: --min-runs must be >= 1")
    preset = PRESETS.get(prefix, {})
    canonical_variants = tuple(preset.get("variants", CANONICAL_VARIANTS))
    canonical_pairs = tuple(preset.get("pairs", CANONICAL_PAIRS))
    title = preset.get("title", DEFAULT_TITLE)
    ns_bands = tuple(preset.get("bands", NS_BANDS))
    if args.pairs:
        try:
            canonical_pairs = tuple(tuple(p.split(":")) for p in args.pairs.split(",") if p.strip())
            if any(len(p) != 2 or not p[0] or not p[1] for p in canonical_pairs):
                raise ValueError
        except ValueError:
            sys.exit("error: --pairs wants 'B:A,B:A,...'")

    cells, sources = discover(directory, prefix)
    if not cells:
        sys.exit(f"error: no cells: no {directory}/{prefix}_n<N>_<mode>_run<R>.txt files "
                 f"and no matching entries in {directory}/{prefix}_raw.txt")

    parsed, problems = {}, []
    for key, (name, lines, src) in sorted(cells.items()):
        c = parse_cell(lines)
        N, mode, run = key
        if not c["values"]:
            problems.append((key, name, c["failed"] or "no RESULT line"))
            continue
        if (c["result_n"] is not None and c["result_n"] != N) or \
           (c["result_mode"] is not None and c["result_mode"] != mode):
            problems.append((key, name, f"RESULT says inner_n={c['result_n']} mode={c['result_mode']}"))
            continue
        c["name"], c["source"] = name, src
        parsed[key] = c
    if not parsed:
        sys.exit(f"error: {len(cells)} cell(s) found but none holds a usable RESULT line")

    if args.list:
        with open(args.list) as fh:
            sizes = [int(x) for x in fh.read().split()]
    else:
        sizes = sorted({k[0] for k in parsed})
    if args.runs:
        runs = sorted({int(x) for x in args.runs.split(",") if x.strip()})
    else:
        runs = sorted({k[2] for k in parsed})
    size_set, run_set = set(sizes), set(runs)
    ignored = sorted(k for k in parsed if k[0] not in size_set or k[2] not in run_set or k[1] not in MODES)
    unknown_modes = sorted({k[1] for k in parsed if k[1] not in MODES})

    seen = []
    for key in sorted(parsed):
        for v in parsed[key]["values"]:
            if v not in seen:
                seen.append(v)
    variants = [v for v in canonical_variants if v in seen] + [v for v in seen if v not in canonical_variants]
    pairs = [p for p in canonical_pairs if p[0] in variants and p[1] in variants]
    if not pairs:
        sys.exit(f"error: none of the pairs {[pair_key(p) for p in canonical_pairs]} can be formed from the "
                 f"variants found ({', '.join(variants)}); use --pairs")

    # ---- per-cell levels and paired deltas -------------------------------------
    results, missing = {}, []
    for N in sizes:
        for mode in MODES:
            present = [r for r in runs if (N, mode, r) in parsed]
            for r in runs:
                if r not in present:
                    missing.append((N, mode, r))
            vals = {r: parsed[(N, mode, r)]["values"] for r in present}
            levels, nruns = {}, {}
            for v in variants:
                xs = [vals[r][v] for r in present if v in vals[r]]
                levels[v] = statistics.median(xs) if xs else None
                nruns[v] = len(xs)
            pr = {}
            for b, a in pairs:
                rs = [r for r in present if b in vals[r] and a in vals[r]]
                ds = [(vals[r][b] / vals[r][a] - 1.0) * 100.0 for r in rs]
                nds = [vals[r][b] - vals[r][a] for r in rs]
                pr[(b, a)] = paired_stats(rs, ds, args.min_runs, b, a, nds)
            results[(N, mode)] = {"runs": present, "levels": levels, "nruns": nruns, "pairs": pr}

    bands = {mode: {p: [band_summary(bd, p) for bd in bands_for(p, mode, sizes, results)]
                    for p in pairs} for mode in MODES}

    # ---- campaign facts ----------------------------------------------------------
    used = [parsed[k] for k in sorted(parsed) if k[0] in size_set and k[2] in run_set and k[1] in MODES]
    harness_fields = {}
    for c in used:
        for k, v in c["harness"].items():
            if k in ("inner_n", "mode"):
                continue
            harness_fields.setdefault(k, set()).add(v)
    meta_fields = {}
    for c in used:
        for k, v in c["meta"].items():
            meta_fields.setdefault(k, []).append(v)
    gap = HOST_GAP.get(host)
    if harness_fields.get("gap") and len(harness_fields["gap"]) == 1:
        try:
            gap = int(next(iter(harness_fields["gap"])))
        except ValueError:
            pass
    temps = []
    for t in meta_fields.get("temp_c", []):
        try:
            temps.append(float(t))
        except ValueError:
            pass
    dates = sorted(d for d in meta_fields.get("date", []) if d)
    governors = sorted(set(meta_fields.get("governor", [])))
    hosts_seen = sorted(set(meta_fields.get("host", [])))
    machines = sorted(set(meta_fields.get("machine", [])))
    notes = sorted(set(meta_fields.get("note", [])))
    orders = sorted(set(meta_fields.get("timing order", [])))
    variant_desc = {}
    for c in used:
        vtxt = c["meta"].get("variants")
        if vtxt:
            for part in vtxt.split(";"):
                k, eq, d = part.partition("=")
                if eq:
                    variant_desc.setdefault(k.strip(), d.strip())
            break
    expected = len(sizes) * len(MODES) * len(runs)

    meta = {
        "directory": directory, "prefix": prefix,
        "per_cell_files": sources["files"], "raw_entries": sources["raw_entries"],
        "raw_path": sources["raw_path"], "per_cell_overrides_raw": sources["overridden"],
        "cells_used": len(used), "cells_expected": expected, "cells_missing": len(missing),
        "cells_unusable": len(problems), "cells_outside_selection": len(ignored),
        "harness": {k: sorted(v) for k, v in sorted(harness_fields.items())},
        "driver_hosts": hosts_seen, "machines": machines, "driver_notes": notes, "governors": governors,
        "temp_c_range": (min(temps), max(temps)) if temps else None,
        "date_range": (dates[0], dates[-1]) if dates else None,
        "timing_orders": len(orders),
        "variant_descriptions": variant_desc,
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "command": "python3 compute_sweep_fvl.py " + " ".join(argv if argv is not None else sys.argv[1:]),
    }

    # ---- report --------------------------------------------------------------------
    L = []
    w = L.append
    w(f"Paired per-run aggregation of the {title} '{prefix}' on host '{host}' "
      f"({HOST_LABEL.get(host, host)})")
    w(f"source: {directory}/ -- {sources['files']} per-cell file(s), {sources['raw_entries']} entr(y/ies) in "
      f"{prefix}_raw.txt" + (f", {sources['overridden']} raw entr(y/ies) superseded by a per-cell file"
                              if sources["overridden"] else ""))
    w(f"cells used: {len(used)} of {expected} expected ({len(sizes)} sizes x {len(MODES)} modes x "
      f"{len(runs)} runs); missing {len(missing)}; unusable {len(problems)}; outside the size/run "
      f"selection {len(ignored)}")
    w(f"runs: {', '.join(str(r) for r in runs)}" + ("" if not args.runs else "  (--runs)"))
    w(f"sizes: {len(sizes)} (n={min(sizes)}..{max(sizes)})" + (f"  (--list {args.list}, in list order)" if args.list else ""))
    w(f"variants: {', '.join(variants)}" + (" -- " + "; ".join(f"{k} = {v}" for k, v in variant_desc.items())
                                           if variant_desc else ""))
    w(f"pairs: " + ", ".join(f"{pair_key(p)} (= {p[0]}/{p[1]} - 1"
                             + (f"; {PAIR_ROLE[pair_key(p)]}" if pair_key(p) in PAIR_ROLE else "") + ")"
                             for p in pairs))
    if harness_fields:
        w("harness header: " + "; ".join(f"{k}={'/'.join(sorted(v))}" if len(v) <= 6 else f"{k}: {len(v)} values"
                                           for k, v in sorted(harness_fields.items())))
    else:
        w("harness header: none found in the cells")
    if meta_fields:
        bits = []
        if hosts_seen:
            bits.append(f"host {'/'.join(hosts_seen)}")
        if machines:
            bits.append(f"machine {'/'.join(machines)}")
        if governors:
            bits.append(f"governor {'/'.join(governors)}")
        if temps:
            bits.append(f"temp_c {min(temps):.1f}..{max(temps):.1f}")
        if dates:
            bits.append(f"dates {dates[0]} .. {dates[-1]}")
        if orders:
            bits.append(f"{len(orders)} distinct timing order(s)")
        cmd = meta_fields.get("command")
        if cmd:
            bits.append(f"command e.g. '{cmd[0]}'")
        w("driver header: " + "; ".join(bits))
        for n in notes:
            w(f"driver note: {n}")
    else:
        w("driver header: none (no '# key: value' lines in the cells)")
    w(f"gap assumed for this host: {gap}  (design maximum n={DESIGN_MAX})")
    w("")
    w("Deltas are B/A - 1 in percent for a pair 'B vs A'; negative means B is faster. Levels are ns/query.")
    w(f"WIN(X) = X faster in >= 80% of the paired runs (ceil(0.8 n)) AND |median paired delta| >= "
      f"{WIN_MIN_PCT:.0f}%; otherwise TIE; n/a = fewer than {args.min_runs} paired runs.")
    w("Levels are medians over the runs in which that variant was measured: never difference them "
      "across variants, use the paired tables.")
    w("")

    # drift
    w("=" * 100)
    w("run-level drift (geometric mean of every (N, variant) cell the runs share, per run)")
    w("=" * 100)
    for mode in MODES:
        g = drift_gauge(mode, runs, sizes, parsed, variants)
        if g is None:
            w(f"  {MODE_NAMES[mode]:9s} not computable (fewer than two runs share a cell)")
            continue
        gms, ncommon = g
        w(f"  {MODE_NAMES[mode]:9s} " + ", ".join(f"run{r}: {gm:.2f}" for r, gm in sorted(gms.items()))
          + f"  (max/min = {max(gms.values()) / min(gms.values()):.2f}x over {ncommon} shared cells)")
    w("")

    # levels
    w("=" * 100)
    w("levels: per-cell medians (ns/query); 'runs' = runs with a usable cell per mode (hb/hs/cb/cs)")
    w("=" * 100)
    hdr = f"{'n':>5}  " + "  ".join(f"{MODE_NAMES[m]:^{9 * len(variants) - 1}}" for m in MODES) + "   runs"
    w(hdr)
    w(f"{'':>5}  " + "  ".join(" ".join(f"{v:>8}" for v in variants) for _ in MODES))
    for N in sizes:
        row = []
        for mode in MODES:
            lv = results[(N, mode)]["levels"]
            row.append(" ".join(fnum(lv[v]) for v in variants))
        rc = "/".join(str(len(results[(N, mode)]["runs"])) for mode in MODES)
        w(f"{N:>5}  " + "  ".join(row) + f"   {rc}")
    w("")

    # paired tables
    for p in pairs:
        b, a = p
        w("=" * 100)
        w(f"paired: {pair_key(p)}  (delta = {b}/{a} - 1 per run; negative = {b} faster"
          + (f"; {PAIR_ROLE[pair_key(p)]}" if pair_key(p) in PAIR_ROLE else "") + ")")
        w(f"cell = median delta, sign count ('-k/n' = {b} faster in k of n paired runs, '+k/n' = {b} slower), verdict")
        w("=" * 100)
        w(f"{'n':>5}  " + "  ".join(f"{MODE_NAMES[m]:^26}" for m in MODES))
        for N in sizes:
            row = []
            for mode in MODES:
                st = results[(N, mode)]["pairs"][p]
                if st["median"] is None:
                    row.append(f"{'-':>26}")
                    continue
                if st["median"] < 0:
                    sc = f"-{st['faster']}/{st['n']}"
                elif st["median"] > 0:
                    sc = f"+{st['slower']}/{st['n']}"
                else:
                    sc = f"0/{st['n']}"
                # two decimals so a cell at -2.96% does not read as "-3.0% TIE"
                row.append(f"{st['median']:>+8.2f}% {sc:>6} {st['verdict']:<9}")
            w(f"{N:>5}  " + "  ".join(row))
        w("")

    # bands
    w("=" * 100)
    w("bands: maximal runs of consecutive sizes with the same winner (a TIE, n/a or missing size breaks a band)")
    w("=" * 100)
    for p in pairs:
        b, a = p
        w(f"{pair_key(p)}  (delta = {b}/{a} - 1; negative = {b} faster)")
        for mode in MODES:
            counts = {"WIN(%s)" % b: 0, "WIN(%s)" % a: 0, "TIE": 0, "n/a": 0}
            for N in sizes:
                counts[results[(N, mode)]["pairs"][p]["verdict"]] += 1
            w(f"  {MODE_NAMES[mode]}: " + ", ".join(f"{k} {v}" for k, v in counts.items()) + f"  (of {len(sizes)} sizes)")
            multi = [s for s in bands[mode][p] if len(s["sizes"]) > 1]
            single = [s for s in bands[mode][p] if len(s["sizes"]) == 1]
            for s in multi:
                w("    " + fmt_band(s, mode))
            if single:
                w("    single-size wins: " + "; ".join(
                    f"{s['winner']} n={s['lo']} ({s['median_min']:+.1f}%, {s['sign_min']}/{s['n_min']})" for s in single))
            if not bands[mode][p]:
                w("    no WIN cells")
        w("")

    # absolute deltas by size band
    w("=" * 100)
    w("paired absolute deltas by size band: median over the band's sizes of each size's median over runs of "
      "B - A in ns [min .. max over those sizes]; negative = B faster")
    w("(a cost that lives in the outer search is a constant number of ns across sizes; one that lives in the "
      "inner grows with n)")
    w("=" * 100)
    for p in pairs:
        b, a = p
        w(f"{pair_key(p)}  ({b} - {a} in ns" + (f"; {PAIR_ROLE[pair_key(p)]}" if pair_key(p) in PAIR_ROLE else "") + ")")
        w(f"  {'band':>11}  " + "  ".join(f"{MODE_NAMES[m]:^30}" for m in MODES))
        for lo, hi in ns_bands:
            band_sizes = [N for N in sizes if lo <= N <= hi]
            if not band_sizes:
                continue
            row = []
            for mode in MODES:
                xs = [results[(N, mode)]["pairs"][p]["median_ns"] for N in band_sizes
                      if results[(N, mode)]["pairs"][p]["median_ns"] is not None]
                if not xs:
                    row.append(f"{'-':^30}")
                else:
                    row.append(f"{statistics.median(xs):>+7.1f} [{min(xs):>+7.1f} .. {max(xs):>+7.1f}]".ljust(30))
            label = f"{lo}-{hi}" if hi < (1 << 30) else f">= {lo}"
            w(f"  {label:>11}  " + "  ".join(row) + f"   ({len(band_sizes)} sizes)")
        w("")

    # level-ratio vs paired sign check
    w("=" * 100)
    w("ratio-of-levels check: cells where (median B)/(median A) - 1 has the opposite sign to the median paired delta")
    w("=" * 100)
    disagreements = []
    for p in pairs:
        b, a = p
        for N in sizes:
            for mode in MODES:
                st = results[(N, mode)]["pairs"][p]
                lv = results[(N, mode)]["levels"]
                if st["median"] is None or lv[b] is None or lv[a] is None:
                    continue
                lr = (lv[b] / lv[a] - 1.0) * 100.0
                if (lr < 0 < st["median"]) or (st["median"] < 0 < lr):
                    disagreements.append((p, N, mode, lr, st))
    if disagreements:
        for p, N, mode, lr, st in disagreements:
            w(f"  {pair_key(p)} n={N} {MODE_NAMES[mode]}: ratio of medians {lr:+.1f}% but paired median "
              f"{st['median']:+.1f}% ({p[0]} faster {st['faster']}/{st['n']}, slower {st['slower']}/{st['n']}; "
              f"levels over {results[(N, mode)]['nruns'][p[0]]}/{results[(N, mode)]['nruns'][p[1]]} runs)")
    else:
        w("  none")
    w("")

    # missing / problems
    w("=" * 100)
    w(f"missing cells: {len(missing)} of {expected}")
    w("=" * 100)
    if missing:
        by_run_mode = {}
        for N, mode, r in missing:
            by_run_mode.setdefault((r, mode), []).append(N)
        for (r, mode), ns in sorted(by_run_mode.items(), key=lambda kv: (kv[0][0], MODES.index(kv[0][1]))):
            w(f"  run{r} {MODE_NAMES[mode]}: {len(ns)} size(s): {compress_ranges(ns) if len(ns) > 12 else ', '.join(map(str, ns))}")
    else:
        w("  none")
    if problems:
        w(f"unusable cells: {len(problems)}")
        for key, name, reason in problems:
            w(f"  {name}: {reason}")
    if ignored:
        w(f"cells outside the size/run selection (ignored): {len(ignored)}")
    if unknown_modes:
        w(f"unknown modes ignored: {', '.join(unknown_modes)}")
    if sources["raw_unmatched"]:
        w(f"raw entries not matching the cell pattern (ignored): {len(sources['raw_unmatched'])}"
          f" e.g. {sources['raw_unmatched'][0]}")
    w("")

    text = "\n".join(L) + "\n"
    if out_path == "-":
        sys.stdout.write(text)
    else:
        with open(out_path, "w") as fh:
            fh.write(text)
        print(f"wrote {out_path}")

    # ---- data module -------------------------------------------------------------
    if data_path != "-":
        meta["title"] = title
        write_data(data_path, host, prefix, gap, variants, pairs, runs, sizes, args.min_runs,
                   results, bands, missing, meta)
        print(f"wrote {data_path}")
    print(f"{len(used)} cells used, {len(missing)} missing, {len(problems)} unusable; "
          f"{len(sizes)} sizes, {len(runs)} runs, variants {', '.join(variants)}")
    return 0


DATA_DOC = '''"""Paired F-vs-Lemire sweep results for host {host}, campaign '{prefix}'.

Generated by compute_sweep_fvl.py on {generated}; do not edit by hand.
Command: {command}

Schema (every N in SIZES has an entry; a value that could not be computed is None):

  HOST, HOST_LABEL, PREFIX   campaign identity;  GAP = the host kernel's block size,
                             DESIGN_MAX = 4096 (the Roaring container maximum)
  MODES                      ("hb", "hs", "cb", "cs"); MODE_NAMES maps them to
                             hot_bat, hot_ser, cold_bat, cold_ser
  VARIANTS                   variant names present, canonical order (F, Lem, Lem2, Fb, LemS)
  VARIANT_DESC               {{var: description}} from the harness header, if present
  PAIRS                      pair keys "B vs A"; the pair's delta is (B/A - 1) * 100
                             per run, NEGATIVE = B (the first-named variant) faster.
                             "Fb vs F" and "Lem vs LemS" contrast the outer search
                             (bsearch vs Shar) with the spine / the Lemire inner;
                             "Fb vs Lem" and "F vs LemS" contrast the inner kernel
                             (spine vs Lemire) with the bsearch / the Shar outer
  PAIR_ROLES                 {{pair key: one-line description of what the pair isolates}}
                             for the pairs that have one (the outer x inner square
                             and the Pi 5 kernel A/B pairs of prefix sweep_ab1)
  RUNS                       run indices used;  SIZES  inner_n values in report order
  MIN_RUNS                   fewest paired runs a cell needs for a verdict
  LEVELS[N][mode][var]       median ns/query over the runs in which var was measured
                             (levels only: never difference them across variants)
  NRUNS[N][mode][var]        how many runs that median covers
  PAIRED[N][mode][pair]      {{"runs": [r, ...], "deltas": [pct, ...] (per run, same order),
                              "median": pct, "faster": k (runs with delta < 0, B faster),
                              "slower": j (runs with delta > 0, B slower), "n": len(runs),
                              "verdict": "WIN(B)" | "WIN(A)" | "TIE" | "n/a",
                              "ns_deltas": [B - A in ns per run], "median_ns": ns}}
                             WIN = >= 80% of the n runs agree in sign and |median| >= 3%
  BANDS[mode][pair]          [{{"winner", "loser", "sizes", "lo", "hi", "median_min",
                              "median_max", "sign_min", "sign_max", "n_min", "n_max"}}, ...]:
                             maximal runs of consecutive SIZES with the same WIN winner
                             (sign_* = runs with the winner faster, per cell)
  MISSING                    [(N, mode, run), ...] expected cells absent or unusable
  META                       campaign facts: source counts, harness/driver header summary
"""
'''


def write_data(path, host, prefix, gap, variants, pairs, runs, sizes, min_runs, results, bands, missing, meta):
    L = []
    w = L.append
    w(DATA_DOC.format(host=host, prefix=prefix, generated=meta["generated"], command=meta["command"]))
    w(f"HOST = {host!r}")
    w(f"HOST_LABEL = {HOST_LABEL.get(host, host)!r}")
    w(f"PREFIX = {prefix!r}")
    w(f"GAP = {gap!r}")
    w(f"DESIGN_MAX = {DESIGN_MAX}")
    w(f"MODES = {MODES!r}")
    w(f"MODE_NAMES = {MODE_NAMES!r}")
    w(f"VARIANTS = {variants!r}")
    w(f"VARIANT_DESC = {meta['variant_descriptions']!r}")
    w(f"PAIRS = {[pair_key(p) for p in pairs]!r}")
    w(f"PAIR_ROLES = {{{', '.join(f'{pair_key(p)!r}: {PAIR_ROLE[pair_key(p)]!r}' for p in pairs if pair_key(p) in PAIR_ROLE)}}}")
    w(f"RUNS = {runs!r}")
    w(f"SIZES = {sizes!r}")
    w(f"MIN_RUNS = {min_runs}")
    w("")
    w("LEVELS = {")
    for N in sizes:
        parts = []
        for mode in MODES:
            lv = results[(N, mode)]["levels"]
            parts.append(f'"{mode}": {{' + ", ".join(f'"{v}": {pylit_float(lv[v])}' for v in variants) + "}")
        w(f"    {N}: {{" + ", ".join(parts) + "},")
    w("}")
    w("")
    w("NRUNS = {")
    for N in sizes:
        parts = []
        for mode in MODES:
            nr = results[(N, mode)]["nruns"]
            parts.append(f'"{mode}": {{' + ", ".join(f'"{v}": {nr[v]}' for v in variants) + "}")
        w(f"    {N}: {{" + ", ".join(parts) + "},")
    w("}")
    w("")
    w("PAIRED = {")
    for N in sizes:
        w(f"    {N}: {{")
        for mode in MODES:
            parts = []
            for p in pairs:
                st = results[(N, mode)]["pairs"][p]
                parts.append(
                    f'"{pair_key(p)}": {{"runs": {st["runs"]!r}, '
                    f'"deltas": [{", ".join(pylit_float(d, 3) for d in st["deltas"])}], '
                    f'"median": {pylit_float(st["median"], 3)}, "faster": {st["faster"]}, '
                    f'"slower": {st["slower"]}, "n": {st["n"]}, "verdict": {st["verdict"]!r}, '
                    f'"ns_deltas": [{", ".join(pylit_float(d, 3) for d in st["ns_deltas"])}], '
                    f'"median_ns": {pylit_float(st["median_ns"], 3)}}}')
            w(f'        "{mode}": {{' + ", ".join(parts) + "},")
        w("    },")
    w("}")
    w("")
    w("BANDS = {")
    for mode in MODES:
        w(f'    "{mode}": {{')
        for p in pairs:
            w(f'        "{pair_key(p)}": [')
            for s in bands[mode][p]:
                w("            " + repr({k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items()}) + ",")
            w("        ],")
        w("    },")
    w("}")
    w("")
    w(f"MISSING = {missing!r}")
    w("")
    w(f"META = {meta!r}")
    w("")
    with open(path, "w") as fh:
        fh.write("\n".join(L))


if __name__ == "__main__":
    sys.exit(main())

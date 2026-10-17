#!/usr/bin/env python3
"""Paired per-run A/B of two interleaved series of main-bench (bench.cpp) runs.

Usage (from the repo root):

    python3 compute_bench_ab.py A_GLOB B_GLOB [--host H] [--labels A,B]
                                [--effect SPEC] [--factor TEXT] [--bands N,..]
                                [--out FILE] [--min-runs K] [--allow-mixed]

    A_GLOB, B_GLOB  the two series' run files, quoted so the shell leaves the
                    wildcard alone, e.g.
                      'cfl_runs/rebench_flushed_pfab_run*.txt'
                      'cfl_runs/rebench_flushed_pfab_np_run*.txt'
                    The two globs must not share a file: one wildcard too
                    many ('rebench_flushed_pfab*_run*.txt' for A) would put
                    the np files into both series and compare np with
                    itself, so the tool refuses. The one exception is the
                    self-pair check -- both globs naming the same files --
                    which the report labels as such (every delta is 0 by
                    construction).
    --host          host tag for the report title (default: the A files'
                    directory, 'cfl_runs' -> cfl)
    --labels        display names of the two series, 'A,B' (default A,B);
                    the verdicts read WIN(<label>)
    --effect        the cells the factor under test can reach (methodology
                    lesson 7, see below): 'NAME[:COND],...' with NAME a cell
                    name or an fnmatch pattern and COND one of >=N, >N, <=N,
                    <N, =N, N-M (sizes, inclusive; no COND = every size),
                    e.g. 'intel:>=128,intelA:>=128' for the Coffee Lake
                    prefetch A/B. Every other cell is an identical-code
                    gauge: the report tallies the gauge's WIN rate and
                    magnitudes per size and per size band, splits every
                    verdict count into effect and gauge, and says for each
                    effect cell whether its |median| clears the gauge's
                    largest |median| at the same size.
    --factor        one line stating what B changes against A, printed in
                    the header (the runs' '# note:' lines are shown as well)
    --bands         size-band boundaries of the gauge summary (default
                    32,128,512,2048: <32, 32-127, 128-511, 512-2047, >=2048
                    = 0, 1-3, 4-15, 16-63 and 64-128 gap-32 blocks)
    --out           report (default DIR/bench_ab_<tagA>_vs_<tagB>_paired.txt,
                    DIR = the A files' directory, <tag> = the file-name tag of
                    rebench_flushed<tag>_run<r>.txt or 'base' when it is
                    empty; '-' = stdout)
    --min-runs      fewest paired runs a cell needs for a verdict (default 3)
    --allow-mixed   accept a series whose usable files carry more than one
                    file-name tag (refused otherwise -- it is almost always a
                    glob that is too wide); a duplicated run index then keeps
                    the file whose tag is the series' majority tag

Examples:
    python3 compute_bench_ab.py 'cfl_runs/rebench_flushed_pfab_run*.txt' \\
            'cfl_runs/rebench_flushed_pfab_np_run*.txt' --labels shipped,np \\
            --effect 'intel:>=128,intelA:>=128' \\
            --factor "the plain kernel's in-loop _mm_prefetch removed (cfl_runs/prefetch_ab_variant.diff)"
        -> cfl_runs/bench_ab_pfab_vs_pfab_np_paired.txt: the Coffee Lake
           in-loop prefetch A/B (A = the shipped simd_quad_intel.c, B = the
           same kernel with the plain kernel's _mm_prefetch removed,
           cfl_runs/prefetch_ab_variant.diff), run r of A interleaved with
           run r of B by /home/pi/build_ab/intel_ab/campaign_cfl_pfab.sh.
           The prefetch sits inside the plain kernel's `while (n > 3)` quat
           loop, which does not iterate below four 32-element blocks, and
           the spine kernels delegate to the plain kernel only below four
           blocks, so intel and intelA at n >= 128 are the effect set.
    python3 compute_bench_ab.py 'cfl_runs/rebench_flushed_run*.txt' \\
            'cfl_runs/rebench_flushed_run*.txt' --out -
        -> a series against itself (the self-pair check): every delta
           exactly 0, every verdict TIE, labelled SELF-PAIR in the report
    python3 compute_bench_ab.py 'cfl_runs/rebench_flushed_run*.txt' \\
            'cfl_runs/rebench_flushed_noturbo_run*.txt' --labels turbo,noturbo --out -
        -> turbo vs the 2.4 GHz base clock: warm about +95%, cold about +35%
           at every size (not interleaved, so a drift check, not an A/B)

What it measures
----------------
A series is a set of bench.cpp runs made with one binary (one kernel, one
clock setting, ...). Two series produced interleaved -- run r of A, then run
r of B, then run r+1 of A, ... -- give pairs that saw the same machine state
as nearly as two processes can, so the A/B of the binaries is the within-pair
comparison, and whole-run drift (thermal, clock, background load) cancels in
it the way it cancels within one run of bench.cpp. The tool pairs the files
by the run index r in their names (rebench_flushed<tag>_run<r>.txt, any tag;
the pattern is compute_bench_paired.RUN_RE, 'run<r>.txt' at the end of the
name) and, for every cell bench.cpp prints -- the plain-row cells per column,
the 'nA' aligned-row cells and the A/B-row cells (spine_N, pad, 4096) -- and
both regimes (warm, cold), computes per paired run the delta
(B/A - 1) * 100 (negative = B faster), its median over the paired runs, the
sign count, the paired ns delta (median of B - A) and the project verdict:

    WIN(B)  B faster in >= 80% of the paired runs (ceil(0.8 n)) and median <= -3%
    WIN(A)  B slower in >= 80% of the paired runs and median >= +3%
    TIE     otherwise                      n/a: fewer than --min-runs paired runs

The parser is compute_bench_paired.parse_run, imported rather than copied,
so the cells are exactly the ones that tool knows (see its docstring for the
cell names and the last-occurrence rule for a repeated A/B row). A run whose
file holds no rows -- a failed run: the driver's header lines, an error
message and '# exit: <status>' -- is listed as unusable and left out; a run
index present in one series only is listed as unpaired; a cell present in
one series only is listed and not compared.

Besides the per-cell tables (one block per cell name, rows = sizes, warm and
cold side by side, in the style of compute_bench_paired.py) the report gives
an overview matrix of the median deltas per regime, each series' run-level
drift (per run, the geometric mean over the cells every paired run of both
series has) with the per-run geometric mean of B/A over the same cells (the
whole-run A/B), and a header with the paired files, the series' file-name
tags, their '# note:' lines and the header fields on which the two series
differ (build, command, ...).

Identical-code gauge (methodology lesson 7)
-------------------------------------------
Two binaries differ by more than the factor under test: a recompiled
translation unit lays out every one of its functions afresh (code addresses,
loop and branch-target alignment), so a cell whose code the factor cannot
reach still moves between the binaries, and in an interleaved campaign at a
fixed clock it moves the SAME way in every pair. The Coffee Lake prefetch
A/B (ten interleaved pairs, intel_pstate no_turbo=1) is the measure of it:
only intel and intelA at n >= 128 can execute different instructions, yet of
the other 215 cells per regime -- linear, binary, simd (bench.cpp's own TU),
intels, the nA twins, intel_spine_N, intel_spine_pad -- 47 have a unanimous
10/10 sign warm and 14 pass the WIN rule (|median| up to 7.0% at n = 89 and
3.9% at n = 47 in the plain intel cell itself, which runs no quat loop
there; 4.1% at n = 128; at most 1.3% from n = 333 up), and cold 15 pass it
(up to 8.6%, 8-9 of 10 runs, no cell unanimous). So in this kind of A/B a
unanimous sign count is not by itself evidence of the factor,
and the "10-run WIN is a reliable sign" rule of the single-binary tools
holds only for cells the factor can reach AND whose |median| clears what
the identical-code cells do at the same sizes. --effect declares the first;
the report's gauge section (per size and per band: WIN rate, unanimous-sign
count, |median| p50/p90/max) and its effect table (every effect cell
against the gauge's largest |median| at the same size) give the second.
Without --effect the report says so and treats every cell alike; do not
quote such a report's WIN totals as the factor's.

Quote paired medians with sign counts, never the difference of the two
series' levels; a single cold cell is not a quotable magnitude.
"""
import argparse
import datetime
import fnmatch
import glob
import math
import os
import re
import statistics
import sys
from collections import Counter, defaultdict

from compute_bench_paired import HOST_LABEL, REGIMES, RUN_RE, WIN_MIN_PCT, need_for_win, parse_run

TAG_RE = re.compile(r"rebench_flushed(.*?)_run\d+\.txt$")
META_KEYS = ("date", "host", "machine", "command", "build", "compiler", "governor", "note")
DEFAULT_BANDS = (32, 128, 512, 2048)
UNTAGGED = "(untagged)"
COND_RE = re.compile(r"^(>=|<=|>|<|=)?(\d+)$")
RANGE_RE = re.compile(r"^(\d+)-(\d+)$")


def run_index(path):
    m = RUN_RE.search(path)
    return int(m.group(1)) if m else None


def file_tag(path):
    """'rebench_flushed_pfab_np_run3.txt' -> 'pfab_np'; 'rebench_flushed_run3.txt' -> 'base'; other names -> UNTAGGED."""
    m = TAG_RE.search(os.path.basename(path))
    if not m:
        return UNTAGGED
    return m.group(1).strip("_") or "base"


def load_series(pattern):
    """-> ({run: parsed}, [(path, reason)], [matched paths], Counter of tags over the usable files).

    A run index that several usable files share keeps the file whose tag is the
    series' majority tag (ties and same-tag duplicates: the first by name); the
    others are listed as unusable with the reason."""
    paths = sorted(glob.glob(pattern), key=lambda p: (run_index(p) if run_index(p) is not None else -1, p))
    usable, bad = [], []
    for p in paths:
        r = run_index(p)
        if r is None:
            bad.append((p, "no run index ('run<r>.txt') in the file name"))
            continue
        parsed = parse_run(p)
        if not parsed["cells"]:
            bad.append((p, f"no rows parsed (exit {parsed['meta'].get('exit', '?')})"))
            continue
        parsed["run"], parsed["tag"] = r, file_tag(p)
        usable.append(parsed)
    tags = Counter(u["tag"] for u in usable)
    majority = min(tags, key=lambda t: (-tags[t], t)) if tags else None
    by_run = defaultdict(list)
    for u in usable:
        by_run[u["run"]].append(u)
    runs = {}
    for r, us in sorted(by_run.items()):
        if len(us) == 1:
            runs[r] = us[0]
            continue
        maj = [u for u in us if u["tag"] == majority]
        if len(maj) == 1:
            keep, why = maj[0], f"tag '{majority}' = the series' majority tag"
        else:
            keep, why = min(us, key=lambda u: u["path"]), "first by name"
        runs[r] = keep
        for u in us:
            if u is not keep:
                bad.append((u["path"], f"duplicate run index {r}; keeping {os.path.basename(keep['path'])} ({why})"))
    bad.sort(key=lambda pr: (run_index(pr[0]) if run_index(pr[0]) is not None else -1, pr[0]))
    return runs, bad, paths, tags


def tag_summary(tags, majority_only=False):
    if not tags:
        return "-"
    items = sorted(tags.items(), key=lambda kv: (-kv[1], kv[0]))
    if majority_only or len(items) == 1:
        return items[0][0]
    return " + ".join(f"{t} x{c}" for t, c in items)


def parse_effect(spec):
    """'intel:>=128,intelA:>=128' -> [(name pattern, lo, hi)], sizes inclusive."""
    items = []
    for raw in spec.split(","):
        item = raw.strip()
        if not item:
            continue
        name, _, cond = item.partition(":")
        name, cond = name.strip(), cond.replace(" ", "")
        if not name:
            sys.exit(f"error: --effect item '{item}' has no cell name")
        lo, hi = 0, math.inf
        if cond:
            m, rg = COND_RE.match(cond), RANGE_RE.match(cond)
            if m:
                op, v = m.group(1) or "=", int(m.group(2))
                lo, hi = {">=": (v, hi), ">": (v + 1, hi), "<=": (lo, v), "<": (lo, v - 1), "=": (v, v)}[op]
            elif rg:
                lo, hi = int(rg.group(1)), int(rg.group(2))
            else:
                sys.exit(f"error: --effect condition '{cond}' in '{item}': use >=N, >N, <=N, <N, =N or N-M")
        items.append((name, lo, hi))
    if not items:
        sys.exit("error: --effect names no cell")
    return items


def in_effect(effect, name, size):
    return any(fnmatch.fnmatchcase(name, pat) and lo <= size <= hi for pat, lo, hi in effect)


def effect_text(effect):
    out = []
    for pat, lo, hi in effect:
        if lo == 0 and hi == math.inf:
            out.append(pat)
        elif hi == math.inf:
            out.append(f"{pat}:>={lo}")
        elif lo == 0:
            out.append(f"{pat}:<={hi}")
        elif lo == hi:
            out.append(f"{pat}:={lo}")
        else:
            out.append(f"{pat}:{lo}-{hi}")
    return ", ".join(out)


def pct(vals, q):
    """Nearest-rank percentile q (0..100) of a non-empty list."""
    xs = sorted(vals)
    return xs[max(1, math.ceil(q / 100.0 * len(xs))) - 1]


def band_of(size, bounds):
    lo = 0
    for b in bounds:
        if size < b:
            return (lo, b - 1)
        lo = b
    return (lo, math.inf)


def band_label(band):
    lo, hi = band
    if hi == math.inf:
        return f">={lo}"
    if lo == 0:
        return f"<{hi + 1}"
    return f"{lo}-{hi}"


def describe_sizes(eff_sizes, all_sizes):
    if not eff_sizes:
        return "none: identical-code gauge at every size"
    if eff_sizes == all_sizes:
        return "every size"
    if eff_sizes == [s for s in all_sizes if s >= eff_sizes[0]]:
        return f"n >= {eff_sizes[0]} (identical-code gauge below)"
    if eff_sizes == [s for s in all_sizes if s <= eff_sizes[-1]]:
        return f"n <= {eff_sizes[-1]} (identical-code gauge above)"
    return "n in {" + ", ".join(str(s) for s in eff_sizes) + "} (identical-code gauge elsewhere)"


def token_diff(a, b):
    ta, tb = a.split(), b.split()
    return [t for t in ta if t not in tb], [t for t in tb if t not in ta]


def meta_summary(runs, key):
    vals = sorted({runs[r]["meta"].get(key, "") for r in runs} - {""})
    if not vals:
        return None
    if len(vals) <= 3:
        return "; ".join(vals)
    return f"{vals[0]} .. {vals[-1]} ({len(vals)} distinct)"


def temps_of(runs):
    out = []
    for r in runs:
        for key in ("temp_before", "temp_after"):
            v = runs[r]["meta"].get(key, "").rstrip("'C ")
            try:
                out.append(float(v))
            except ValueError:
                pass
    return out


def verdict_counts(stats, la, lb):
    c = {"b": 0, "a": 0, "tie": 0, "na": 0}
    for st in stats:
        if st["verdict"] == f"WIN({lb})":
            c["b"] += 1
        elif st["verdict"] == f"WIN({la})":
            c["a"] += 1
        elif st["verdict"] == "TIE":
            c["tie"] += 1
        else:
            c["na"] += 1
    return c


def counts_text(c, la, lb, with_na=True):
    s = f"WIN({lb}) {c['b']}, WIN({la}) {c['a']}, TIE {c['tie']}"
    return s + (f", n/a {c['na']}" if with_na else "")


def gauge_line(stats, min_runs):
    """One summary line of a list of paired cells: judged cells, WINs, unanimous signs, |median| p50/p90/max."""
    judged = [st for st in stats if st["verdict"] != "n/a"]
    wins = [st for st in judged if st["verdict"].startswith("WIN")]
    unan = [st for st in judged if st["n"] >= min_runs and (st["faster"] == st["n"] or st["slower"] == st["n"])]
    unan_big = [st for st in unan if abs(st["median"]) >= WIN_MIN_PCT]
    mags = [abs(st["median"]) for st in judged]
    if not judged:
        return None
    top = max(judged, key=lambda st: abs(st["median"]))
    return {"cells": len(judged), "wins": len(wins), "rate": 100.0 * len(wins) / len(judged), "unan": len(unan),
            "unan_big": len(unan_big), "p50": pct(mags, 50), "p90": pct(mags, 90), "max": top["median"],
            "max_cell": f"{top['name']} n={top['size']}"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a_glob", metavar="A_GLOB")
    ap.add_argument("b_glob", metavar="B_GLOB")
    ap.add_argument("--host")
    ap.add_argument("--labels", default="A,B")
    ap.add_argument("--effect")
    ap.add_argument("--factor")
    ap.add_argument("--bands", default=",".join(str(b) for b in DEFAULT_BANDS))
    ap.add_argument("--out")
    ap.add_argument("--min-runs", type=int, default=3)
    ap.add_argument("--allow-mixed", action="store_true")
    args = ap.parse_args(argv)
    labels = [s.strip() for s in args.labels.split(",")]
    if len(labels) != 2 or not all(labels) or labels[0] == labels[1]:
        sys.exit("error: --labels wants two distinct names, 'A,B'")
    la, lb = labels
    if args.min_runs < 1:
        sys.exit("error: --min-runs must be >= 1")
    effect = parse_effect(args.effect) if args.effect else None
    try:
        bands = sorted({int(x) for x in args.bands.split(",") if x.strip()})
    except ValueError:
        sys.exit("error: --bands wants integers, 'N,N,...'")
    if not bands or bands[0] <= 0:
        sys.exit("error: --bands wants positive size boundaries")

    A, bad_a, paths_a, tags_a = load_series(args.a_glob)
    B, bad_b, paths_b, tags_b = load_series(args.b_glob)
    if not paths_a:
        sys.exit(f"error: no files match {args.a_glob}")
    if not paths_b:
        sys.exit(f"error: no files match {args.b_glob}")
    for label, tags, pattern in ((la, tags_a, args.a_glob), (lb, tags_b, args.b_glob)):
        if len(tags) > 1 and not args.allow_mixed:
            sys.exit(f"error: series {label} ({pattern}) mixes {len(tags)} file-name tags among its usable files: "
                     f"{tag_summary(tags)} -- one wildcard too many? Narrow the glob, or pass --allow-mixed to "
                     f"keep the majority tag ('{tag_summary(tags, True)}') on a duplicated run index.")
    real_a = {os.path.realpath(p) for p in paths_a}
    real_b = {os.path.realpath(p) for p in paths_b}
    self_pair = args.a_glob == args.b_glob or real_a == real_b
    overlap = sorted(real_a & real_b)
    if overlap and not self_pair:
        sys.exit(f"error: the two globs share {len(overlap)} file(s), so one series would be compared with "
                 f"itself -- one wildcard too many? Shared: {', '.join(os.path.basename(p) for p in overlap)}. "
                 f"(The self-pair check wants both globs to name exactly the same files.)")
    common = sorted(set(A) & set(B))
    if not common:
        sys.exit("error: the two series share no run index with usable rows")
    only_a = sorted(set(A) - set(B))
    only_b = sorted(set(B) - set(A))

    a_dir = os.path.dirname(paths_a[0]) or "."
    host = args.host or os.path.basename(os.path.normpath(a_dir)).removesuffix("_runs")
    if args.out:
        out_path = args.out
    else:
        ta = tag_summary(tags_a, True) if tags_a and tag_summary(tags_a, True) != UNTAGGED else la
        tb = tag_summary(tags_b, True) if tags_b and tag_summary(tags_b, True) != UNTAGGED else lb
        out_path = os.path.join(a_dir, f"bench_ab_{ta}_vs_{tb}_paired.txt")

    cols_a = A[common[0]]["cols"]
    cols_b = B[common[0]]["cols"]
    names_a = {k[2] for r in common for k in A[r]["cells"]}
    names_b = {k[2] for r in common for k in B[r]["cells"]}
    names = sorted(names_a & names_b, key=lambda s: (len(s), s))
    sizes = sorted({k[0] for r in common for s in (A, B) for k in s[r]["cells"]})

    # paired statistics per (size, regime, cell)
    paired = {}
    for s in sizes:
        for rg in REGIMES:
            for nm in names:
                key = (s, rg, nm)
                rs = [r for r in common if key in A[r]["cells"] and key in B[r]["cells"] and A[r]["cells"][key] > 0]
                if not rs:
                    continue
                ds = [(B[r]["cells"][key] / A[r]["cells"][key] - 1.0) * 100.0 for r in rs]
                nds = [B[r]["cells"][key] - A[r]["cells"][key] for r in rs]
                n = len(ds)
                neg = sum(1 for d in ds if d < 0)
                pos = sum(1 for d in ds if d > 0)
                med = statistics.median(ds)
                if n < args.min_runs:
                    verdict = "n/a"
                else:
                    need = need_for_win(n)
                    if neg >= need and med <= -WIN_MIN_PCT:
                        verdict = f"WIN({lb})"
                    elif pos >= need and med >= WIN_MIN_PCT:
                        verdict = f"WIN({la})"
                    else:
                        verdict = "TIE"
                paired[key] = {"size": s, "regime": rg, "name": nm, "runs": rs, "deltas": ds, "median": med,
                               "faster": neg, "slower": pos, "n": n, "verdict": verdict,
                               "median_ns": statistics.median(nds),
                               "level_a": statistics.median(A[r]["cells"][key] for r in rs),
                               "level_b": statistics.median(B[r]["cells"][key] for r in rs),
                               "effect": None if effect is None else in_effect(effect, nm, s)}

    # run-level drift and whole-run A/B over the cells every paired run of both series has
    drift = {}
    for rg in REGIMES:
        shared = None
        for r in common:
            ks = {k for k in A[r]["cells"] if k[1] == rg} & {k for k in B[r]["cells"] if k[1] == rg}
            shared = ks if shared is None else shared & ks
        shared = {k for k in (shared or set()) if all(A[r]["cells"][k] > 0 and B[r]["cells"][k] > 0 for r in common)}
        if shared:
            gm_a = {r: math.exp(sum(math.log(A[r]["cells"][k]) for k in shared) / len(shared)) for r in common}
            gm_b = {r: math.exp(sum(math.log(B[r]["cells"][k]) for k in shared) / len(shared)) for r in common}
            drift[rg] = (gm_a, gm_b, len(shared))

    # the gauge at each (regime, size): the largest |median| and the WIN count over the identical-code cells there
    gauge_at = {}
    if effect is not None:
        for rg in REGIMES:
            for s in sizes:
                g = [st for st in paired.values() if st["regime"] == rg and st["size"] == s and st["effect"] is False
                     and st["verdict"] != "n/a"]
                if g:
                    top = max(g, key=lambda st: abs(st["median"]))
                    gauge_at[(rg, s)] = {"cells": len(g), "wins": sum(1 for st in g if st["verdict"].startswith("WIN")),
                                         "max": top["median"], "max_cell": top["name"]}

    # ---- report ------------------------------------------------------------------
    L = []
    w = L.append
    w(f"Paired A/B of two interleaved series of main-bench runs on host '{host}' ({HOST_LABEL.get(host, host)})")
    if self_pair:
        w("SELF-PAIR: the two globs name the same files, so B is A and every delta is 0 by construction -- "
          "a parser/format check, not an A/B.")
    w(f"A = {la}: {args.a_glob}  ({len(paths_a)} file(s), {len(A)} usable)")
    w(f"B = {lb}: {args.b_glob}  ({len(paths_b)} file(s), {len(B)} usable)")
    w(f"series tags (rebench_flushed<tag>_run<r>.txt, over the usable files): A = {tag_summary(tags_a)}; "
      f"B = {tag_summary(tags_b)}"
      + ("  (--allow-mixed: a duplicated run index keeps the majority tag)" if args.allow_mixed else ""))
    w(f"paired runs ({len(common)}), run r of A with run r of B:")
    for r in common:
        w(f"  run{r}: {os.path.basename(A[r]['path'])}  <->  {os.path.basename(B[r]['path'])}")
    if only_a:
        w(f"unpaired A runs (no usable B run of the same index): " + ", ".join(f"run{r} ({os.path.basename(A[r]['path'])})" for r in only_a))
    if only_b:
        w(f"unpaired B runs (no usable A run of the same index): " + ", ".join(f"run{r} ({os.path.basename(B[r]['path'])})" for r in only_b))
    for label, bad in ((la, bad_a), (lb, bad_b)):
        for p, reason in bad:
            w(f"unusable {label} file: {os.path.basename(p)}: {reason}")
    differing = []
    for key in META_KEYS:
        va, vb = meta_summary({r: A[r] for r in common}, key), meta_summary({r: B[r] for r in common}, key)
        if va is None and vb is None:
            continue
        if va == vb:
            w(f"{key} (both): {va}")
        else:
            differing.append(key)
            w(f"{key} A: {va or '-'}")
            w(f"{key} B: {vb or '-'}")
    # what else differs besides the factor under test (methodology lesson 7)
    if not self_pair and ("build" in differing or "command" in differing):
        detail = ""
        ba, bb = meta_summary({r: A[r] for r in common}, "build"), meta_summary({r: B[r] for r in common}, "build")
        if ba and bb and ba != bb and ";" not in ba and ";" not in bb:
            oa, ob = token_diff(ba, bb)
            detail = f" (the build lines differ in: A '{' '.join(oa) or '-'}' vs B '{' '.join(ob) or '-'}')"
        w(f"two binaries{detail}: besides the factor under test, a recompiled translation unit lays out every one of "
          f"its functions afresh (code addresses, loop and branch-target alignment), so cells whose code the factor "
          f"cannot reach are identical-code gauges of what this A/B's sign counts and WIN rule do on no effect at "
          f"all (methodology lesson 7).")
    if args.factor:
        w(f"factor under test (--factor): B = {args.factor}")
    n_eff = {rg: sum(1 for st in paired.values() if st["regime"] == rg and st["effect"]) for rg in REGIMES}
    n_gau = {rg: sum(1 for st in paired.values() if st["regime"] == rg and st["effect"] is False) for rg in REGIMES}
    if effect is not None:
        w(f"effect set (--effect): {effect_text(effect)} -> "
          + "; ".join(f"{rg}: {n_eff[rg]} effect cells, {n_gau[rg]} identical-code gauge cells" for rg in REGIMES)
          + ". The overview marks a gauge WIN '~', the per-cell tables flag each row 'eff'/'gau', and the gauge "
            "and effect sections below compare the two.")
        unmatched = [pat for pat, _, _ in effect if not any(fnmatch.fnmatchcase(nm, pat) for nm in names)]
        if unmatched:
            w(f"WARNING: --effect pattern(s) matching no compared cell: {', '.join(unmatched)}")
        if not any(n_eff.values()):
            w("WARNING: the effect set holds no compared cell; every verdict below is a gauge verdict")
    elif not self_pair:
        w("WARNING: no --effect given: every cell is reported as if the factor under test could reach it, and the "
          "verdict totals mix the factor's cells with identical-code cells (methodology lesson 7: ask what else "
          "differs besides the factor). Declare the cells the factor can reach, e.g. "
          "--effect 'intel:>=128,intelA:>=128' for the Coffee Lake prefetch A/B.")
    ta, tb = temps_of({r: A[r] for r in common}), temps_of({r: B[r] for r in common})
    if ta or tb:
        w("temperature (temp_before/temp_after): "
          + "; ".join(f"{lab} {min(t):.1f}..{max(t):.1f} C" for lab, t in ((la, ta), (lb, tb)) if t))
    notes = sorted({n for s in (A, B) for r in common for n in s[r]["notes"]})
    for n in notes:
        w(f"harness note: {n}")
    missing_flush = [os.path.basename(s[r]["path"]) for s in (A, B) for r in common
                     if not any(n.startswith("cold column") for n in s[r]["notes"])]
    if missing_flush:
        w(f"WARNING: no '# cold column:' line (pre-flush bench.cpp) in: {', '.join(missing_flush)}")
    exits_a = sorted({A[r]["meta"].get("exit", "?") for r in common})
    exits_b = sorted({B[r]["meta"].get("exit", "?") for r in common})
    w(f"exit statuses: A {', '.join(exits_a)}; B {', '.join(exits_b)}")
    w(f"columns A: {' '.join(cols_a)}; columns B: {' '.join(cols_b)}")
    w(f"sizes: {len(sizes)} ({sizes[0]}..{sizes[-1]}); compared cell names ({len(names)}): {', '.join(names)}")
    only_na = sorted(names_a - names_b, key=lambda s: (len(s), s))
    only_nb = sorted(names_b - names_a, key=lambda s: (len(s), s))
    if only_na:
        w(f"cells only in A (not compared): {', '.join(only_na)}")
    if only_nb:
        w(f"cells only in B (not compared): {', '.join(only_nb)}")
    w("")
    w(f"Deltas are B/A - 1 in percent ({lb}/{la} - 1); negative means B ({lb}) is faster. Levels are ns/query, "
      f"medians over the paired runs.")
    w(f"WIN(X) = X faster in >= 80% of the paired runs (ceil(0.8 n)) AND |median paired delta| >= {WIN_MIN_PCT:.0f}%; "
      f"otherwise TIE; n/a = fewer than {args.min_runs} paired runs.")
    if effect is not None:
        w("A WIN on an identical-code (gauge) cell is what the rule does on no effect; an effect cell's WIN is "
          "evidence of the factor when its |median| clears the gauge's largest |median| at the same size "
          "(column '> gauge' of the effect table).")
    w("")

    w("=" * 100)
    w("run-level drift: per run, the geometric mean (ns) over the cells every paired run of both series has, "
      "per series; and B/A over the same cells (the whole-run A/B)")
    w("=" * 100)
    for rg in REGIMES:
        if rg not in drift:
            w(f"  {rg:5s} not computable (no cell shared by every paired run of both series)")
            continue
        gm_a, gm_b, nc = drift[rg]
        ratios = {r: (gm_b[r] / gm_a[r] - 1.0) * 100.0 for r in common}
        w(f"  {rg:5s} A ({la}): " + ", ".join(f"run{r}: {gm_a[r]:.2f}" for r in common)
          + f"  (max/min = {max(gm_a.values()) / min(gm_a.values()):.2f}x over {nc} shared cells)")
        w(f"  {'':5s} B ({lb}): " + ", ".join(f"run{r}: {gm_b[r]:.2f}" for r in common)
          + f"  (max/min = {max(gm_b.values()) / min(gm_b.values()):.2f}x)")
        w(f"  {'':5s} B/A - 1: " + ", ".join(f"run{r}: {ratios[r]:+.1f}%" for r in common)
          + f"  (median {statistics.median(ratios.values()):+.1f}%)")
    w("")

    # the identical-code gauge and the effect cells against it
    if effect is not None:
        for rg in REGIMES:
            gauge = [st for st in paired.values() if st["regime"] == rg and st["effect"] is False]
            eff = [st for st in paired.values() if st["regime"] == rg and st["effect"]]
            w("=" * 100)
            w(f"gauge, {rg}: the {len(gauge)} cells outside --effect (identical code in both binaries) -- what the "
              f"sign counts and the WIN rule do on no effect at all")
            w("=" * 100)
            g = gauge_line(gauge, args.min_runs)
            if g is None:
                w("  no gauge cell with a verdict")
            else:
                c = verdict_counts(gauge, la, lb)
                w(f"  verdicts: {counts_text(c, la, lb)} -> WIN rate {g['rate']:.1f}% of {g['cells']} judged cells")
                w(f"  |median delta| (nearest-rank percentiles): p50 {g['p50']:.1f}%, p90 {g['p90']:.1f}%, max "
                  f"{abs(g['max']):.1f}% ({g['max_cell']}, {g['max']:+.1f}%); unanimous sign (every paired run agrees): "
                  f"{g['unan']} cells, {g['unan_big']} of them with |median| >= {WIN_MIN_PCT:.0f}% (= the WINs)")
                w(f"  per size band:  {'band':>10} {'cells':>5} {'WIN':>4} {'unan':>5} {'|med| p50':>10} {'p90':>6} "
                  f"{'max':>6}  max cell")
                for band in sorted({band_of(s, bands) for s in sizes}):
                    gb = [st for st in gauge if band_of(st["size"], bands) == band]
                    gl = gauge_line(gb, args.min_runs)
                    if gl is None:
                        w(f"                  {band_label(band):>10} {0:>5}")
                        continue
                    w(f"                  {band_label(band):>10} {gl['cells']:>5} {gl['wins']:>4} {gl['unan']:>5} "
                      f"{gl['p50']:>9.1f}% {gl['p90']:>5.1f}% {abs(gl['max']):>5.1f}%  {gl['max_cell']}")
                w(f"  per size:       {'n':>10} {'cells':>5} {'WIN':>4} {'unan':>5} {'|med| p50':>10} {'p90':>6} "
                  f"{'max':>6}  max cell")
                for s in sizes:
                    gs = [st for st in gauge if st["size"] == s]
                    gl = gauge_line(gs, args.min_runs)
                    if gl is None:
                        continue
                    w(f"                  {s:>10} {gl['cells']:>5} {gl['wins']:>4} {gl['unan']:>5} "
                      f"{gl['p50']:>9.1f}% {gl['p90']:>5.1f}% {abs(gl['max']):>5.1f}%  {gl['max_cell']}")
            w("")
            w("=" * 100)
            w(f"effect, {rg}: the {len(eff)} cells --effect names (the factor can reach them), each against the "
              f"gauge at the same size")
            w("=" * 100)
            if not eff:
                w("  no effect cell")
                w("")
                continue
            w(f"  '> gauge' = the cell is a WIN and its |median| exceeds the largest gauge |median| at that size")
            w(f"  {'n':>5} {'cell':<16} {'A ns':>8} {'B ns':>8} {'delta':>8} {'sign':>6} {'ns':>9} {'verdict':<12}  "
              f"{'gauge@n: max |med| (cell)':<28} {'gauge WINs':>10}  > gauge")
            clears, eff_wins = 0, 0
            for st in sorted(eff, key=lambda st: (st["size"], len(st["name"]), st["name"])):
                sc = (f"-{st['faster']}/{st['n']}" if st["median"] < 0 else
                      f"+{st['slower']}/{st['n']}" if st["median"] > 0 else f"0/{st['n']}")
                ga = gauge_at.get((rg, st["size"]))
                is_win = st["verdict"].startswith("WIN")
                eff_wins += is_win
                if ga is None:
                    gtxt, gw, clear = "no gauge cell at this size", "-", "-"
                else:
                    gtxt = f"{ga['max']:+.1f}% ({ga['max_cell']})"
                    gw = f"{ga['wins']}/{ga['cells']}"
                    clear = "-" if not is_win else ("yes" if abs(st["median"]) > abs(ga["max"]) else "no")
                    clears += clear == "yes"
                w(f"  {st['size']:>5} {st['name']:<16} {st['level_a']:>8.2f} {st['level_b']:>8.2f} "
                  f"{st['median']:>+7.2f}% {sc:>6} {st['median_ns']:>+6.2f} ns {st['verdict']:<12}  {gtxt:<28} "
                  f"{gw:>10}  {clear}")
            c = verdict_counts(eff, la, lb)
            w(f"  verdicts: {counts_text(c, la, lb)}; {clears} of the {eff_wins} WINs clear the gauge's largest "
              f"|median| at their size")
            w("")

    # overview matrices
    for rg in REGIMES:
        shown = [nm for nm in names if any((s, rg, nm) in paired for s in sizes)]
        if not shown:
            continue
        w("=" * 100)
        if effect is None:
            w(f"overview, {rg}: median paired delta % per (size, cell), B/A - 1; '*' marks a WIN (either side), "
              f"'?' a cell below --min-runs")
        else:
            w(f"overview, {rg}: median paired delta % per (size, cell), B/A - 1; '*' marks a WIN on an effect cell, "
              f"'~' a WIN on an identical-code gauge cell, '?' a cell below --min-runs")
        w("=" * 100)
        widths = [max(8, len(nm)) for nm in shown]
        w(f"{'n':>5}  " + " ".join(f"{nm:>{wd}}" for nm, wd in zip(shown, widths)))
        for s in sizes:
            row = []
            for nm, wd in zip(shown, widths):
                st = paired.get((s, rg, nm))
                if st is None:
                    row.append(f"{'-':>{wd}}")
                else:
                    if st["verdict"].startswith("WIN"):
                        mark = "~" if st["effect"] is False else "*"
                    else:
                        mark = "?" if st["verdict"] == "n/a" else " "
                    row.append(f"{st['median']:>+{wd - 1}.1f}{mark}")
            w(f"{s:>5}  " + " ".join(row))
        allc = [paired[(s, rg, nm)] for s in sizes for nm in shown if (s, rg, nm) in paired]
        c = verdict_counts(allc, la, lb)
        w(f"  {rg} verdicts over {len(allc)} cells: {counts_text(c, la, lb)}")
        if effect is not None:
            ce = verdict_counts([st for st in allc if st["effect"]], la, lb)
            cg = verdict_counts([st for st in allc if st["effect"] is False], la, lb)
            w(f"  {'':5s} effect cells ({sum(ce.values())}): {counts_text(ce, la, lb)}; "
              f"gauge cells ({sum(cg.values())}): {counts_text(cg, la, lb)}")
        w("")

    # per-cell paired tables
    for nm in names:
        if not any((s, rg, nm) in paired for s in sizes for rg in REGIMES):
            continue
        w("=" * 100)
        w(f"paired: {nm}  (delta = {lb}/{la} - 1 per run; negative = {lb} faster)")
        w(f"cell = median {la} ns, median {lb} ns, median delta %, sign count ('-k/n' = {lb} faster in k of n paired runs, "
          f"'+k/n' = {lb} slower), median ns delta, verdict")
        if effect is not None:
            cell_sizes = [s for s in sizes if any((s, rg, nm) in paired for rg in REGIMES)]
            eff_sizes = [s for s in cell_sizes if in_effect(effect, nm, s)]
            w(f"effect cell at: {describe_sizes(eff_sizes, cell_sizes)}  (column 'set': eff = the factor can reach "
              f"it, gau = identical-code gauge)")
        w("=" * 100)
        w(f"{'n':>5} {'set':>3}  {'warm':^62}  {'cold':^62}")
        rows_by_set = {rg: {"eff": [], "gau": [], "all": []} for rg in REGIMES}
        for s in sizes:
            row, any_cell, flag = [], False, ""
            for rg in REGIMES:
                st = paired.get((s, rg, nm))
                if st is None:
                    row.append(f"{'-':>62}")
                    continue
                any_cell = True
                if st["effect"] is not None:
                    flag = "eff" if st["effect"] else "gau"
                    rows_by_set[rg][flag].append(st)
                rows_by_set[rg]["all"].append(st)
                sc = (f"-{st['faster']}/{st['n']}" if st["median"] < 0 else
                      f"+{st['slower']}/{st['n']}" if st["median"] > 0 else f"0/{st['n']}")
                row.append(f"{st['level_a']:>8.2f} {st['level_b']:>8.2f} {st['median']:>+8.2f}% {sc:>6} "
                           f"{st['median_ns']:>+9.2f} ns {st['verdict']:<12}")
            if any_cell:
                w(f"{s:>5} {flag:>3}  " + "  ".join(row))
        w("  verdicts: " + "; ".join(f"{rg}: {counts_text(verdict_counts(rows_by_set[rg]['all'], la, lb), la, lb, False)}"
                                     for rg in REGIMES))
        if effect is not None:
            w("  of which:  " + "; ".join(
                f"{rg}: effect {counts_text(verdict_counts(rows_by_set[rg]['eff'], la, lb), la, lb, False)} | "
                f"gauge {counts_text(verdict_counts(rows_by_set[rg]['gau'], la, lb), la, lb, False)}"
                for rg in REGIMES))
        w("")

    w(f"generated {datetime.datetime.now().isoformat(timespec='seconds')} by compute_bench_ab.py "
      + " ".join(argv if argv is not None else sys.argv[1:]))
    text = "\n".join(L) + "\n"
    if out_path == "-":
        sys.stdout.write(text)
    else:
        with open(out_path, "w") as fh:
            fh.write(text)
        print(f"wrote {out_path}")
    if self_pair:
        print("SELF-PAIR: the two globs name the same files; every delta is 0 by construction")
    print(f"{len(common)} paired run(s); {len(names)} cell names x {len(sizes)} sizes; "
          f"unusable files: {len(bad_a)} A, {len(bad_b)} B; unpaired runs: {len(only_a)} A, {len(only_b)} B; "
          f"series tags: A = {tag_summary(tags_a)}, B = {tag_summary(tags_b)}")
    if effect is not None:
        for rg in REGIMES:
            eff = [st for st in paired.values() if st["regime"] == rg and st["effect"]]
            gau = [st for st in paired.values() if st["regime"] == rg and st["effect"] is False]
            ce, g = verdict_counts(eff, la, lb), gauge_line(gau, args.min_runs)
            gtxt = ("no judged gauge cell" if g is None else
                    f"{g['cells']} cells, WIN rate {g['rate']:.1f}%, |median| p90 {g['p90']:.1f}%, "
                    f"max {abs(g['max']):.1f}% ({g['max_cell']})")
            print(f"{rg}: effect {len(eff)} cells: {counts_text(ce, la, lb)}; gauge {gtxt}")
    elif not self_pair:
        print("WARNING: no --effect given; the verdict totals mix the factor's cells with identical-code cells")
    return 0


if __name__ == "__main__":
    sys.exit(main())

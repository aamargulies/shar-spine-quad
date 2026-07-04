#!/usr/bin/env python3
"""Aggregate the 2026-05-19 F vs F* sweep on M4 Max.

Reads m4_runs/sweep_n${N}_${mode}_run${R}.txt (RESULT lines emitted by
bench_sweep), takes the per-cell median across the 5 runs, and prints:

    1. A 4-mode table: for each N, F and F* medians and the delta.
    2. A "paste into plot.py" block: m4_sweep = {N: {mode: (F, Fstar)}}.

Modes: hb hot_bat / hs hot_ser / cb cold_bat / cs cold_ser.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIST = os.path.join(HERE, "sweep_n_list.txt")
MODES = ("hb", "hs", "cb", "cs")
RUNS  = (1, 2, 3, 4, 5)

def median(lst):
    s = sorted(lst)
    n = len(s)
    return s[n//2] if n % 2 else 0.5 * (s[n//2 - 1] + s[n//2])

# RESULT line: "RESULT inner_n=N mode=M F=val Fstar=val"
RESULT_RE = re.compile(
    r"^RESULT\s+inner_n=(\d+)\s+mode=(\w+)\s+F=([\d.]+)\s+Fstar=([\d.]+)\s*$"
)

def parse_one(path):
    with open(path) as f:
        for line in f:
            m = RESULT_RE.match(line)
            if m:
                return float(m.group(3)), float(m.group(4))
    return None

def main():
    with open(LIST) as f:
        ns = [int(x) for x in f.read().split()]

    # data[n][mode] = list of (F, Fstar) across runs
    data = {n: {m: [] for m in MODES} for n in ns}
    missing = []
    for n in ns:
        for m in MODES:
            for r in RUNS:
                p = os.path.join(HERE, f"sweep_n{n}_{m}_run{r}.txt")
                v = parse_one(p) if os.path.exists(p) else None
                if v is None:
                    missing.append(p)
                else:
                    data[n][m].append(v)

    if missing:
        sys.stderr.write(f"warning: {len(missing)} missing/incomplete output files\n")
        for p in missing[:5]:
            sys.stderr.write(f"  {p}\n")
        if len(missing) > 5:
            sys.stderr.write(f"  ... and {len(missing) - 5} more\n")

    # Compute medians per (n, mode).
    med = {n: {m: (None, None) for m in MODES} for n in ns}
    for n in ns:
        for m in MODES:
            xs = data[n][m]
            if not xs:
                continue
            med[n][m] = (median([x[0] for x in xs]),
                         median([x[1] for x in xs]))

    # Table.
    print("=== M4 Max F vs F* sweep medians (5 runs, 2026-05-19) ===")
    print(f"{'n':>5}  "
          f"{'F.hb':>7} {'Fs.hb':>7} {'d%':>6}  "
          f"{'F.hs':>7} {'Fs.hs':>7} {'d%':>6}  "
          f"{'F.cb':>7} {'Fs.cb':>7} {'d%':>6}  "
          f"{'F.cs':>7} {'Fs.cs':>7} {'d%':>6}")
    for n in ns:
        cells = []
        for m in MODES:
            f, fs = med[n][m]
            if f is None or fs is None:
                cells.append("    nan     nan     nan")
            else:
                d = (fs / f - 1.0) * 100
                cells.append(f"{f:7.2f} {fs:7.2f} {d:+6.1f}")
        print(f"{n:>5}  " + "  ".join(cells))

    # Summary: where does F* win, by how much, in each mode.
    print("\n=== F* vs F summary (median across all sweep n) ===")
    for m, label in zip(MODES, ("hot_bat", "hot_ser", "cold_bat", "cold_ser")):
        deltas = []
        wins = 0
        ties = 0
        losses = 0
        for n in ns:
            f, fs = med[n][m]
            if f is None or fs is None:
                continue
            d = (fs / f - 1.0) * 100
            deltas.append(d)
            if d < -1.0:   wins += 1
            elif d > 1.0:  losses += 1
            else:          ties += 1
        if deltas:
            ds = sorted(deltas)
            mid = ds[len(ds)//2]
            print(f"  {label:9s}  median delta {mid:+6.1f}%   "
                  f"win/tie/loss = {wins}/{ties}/{losses}/{len(deltas)} "
                  f"min={min(ds):+.1f}% max={max(ds):+.1f}%")

    # plot.py paste block.
    print("\n# paste into plot.py:")
    print("m4_sweep = {")
    for n in ns:
        cells = []
        for m in MODES:
            f, fs = med[n][m]
            if f is None or fs is None:
                cells.append('"' + m + '":(None,None)')
            else:
                cells.append(f'"{m}":({f:.3f},{fs:.3f})')
        print(f"    {n}: {{" + ", ".join(cells) + "},")
    print("}")

if __name__ == "__main__":
    main()

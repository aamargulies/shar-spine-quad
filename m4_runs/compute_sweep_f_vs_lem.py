#!/usr/bin/env python3
"""Aggregate the 2026-05-20 F vs Lemire-reference sweep on M4 Max.

Reads m4_runs/sweep_fvl_n${N}_${mode}_run${R}.txt (RESULT lines emitted by
bench_sweep_f_vs_lem), takes per-cell median across the 5 runs, and prints:

    1. A 4-mode table of F and Lem medians + delta per N.
    2. A "paste into plot.py" block: m4_fvl_sweep = {N: {mode: (F, Lem)}}.

Modes: hb hot_bat / hs hot_ser / cb cold_bat / cs cold_ser.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIST = os.path.join(HERE, "sweep_n_list_f_vs_lem.txt")
MODES = ("hb", "hs", "cb", "cs")
RUNS  = (1, 2, 3, 4, 5)

def median(lst):
    s = sorted(lst)
    n = len(s)
    return s[n//2] if n % 2 else 0.5 * (s[n//2 - 1] + s[n//2])

# RESULT line: "RESULT inner_n=N mode=M F=val Lem=val"
RESULT_RE = re.compile(
    r"^RESULT\s+inner_n=(\d+)\s+mode=(\w+)\s+F=([\d.]+)\s+Lem=([\d.]+)\s*$"
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

    data = {n: {m: [] for m in MODES} for n in ns}
    missing = []
    for n in ns:
        for m in MODES:
            for r in RUNS:
                p = os.path.join(HERE, f"sweep_fvl_n{n}_{m}_run{r}.txt")
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

    med = {n: {m: (None, None) for m in MODES} for n in ns}
    for n in ns:
        for m in MODES:
            xs = data[n][m]
            if not xs:
                continue
            med[n][m] = (median([x[0] for x in xs]),
                         median([x[1] for x in xs]))

    print("=== M4 Max F vs Lem sweep medians (5 runs, 2026-05-20) ===")
    print(f"{'n':>5}  "
          f"{'F.hb':>7} {'L.hb':>7} {'d%':>6}  "
          f"{'F.hs':>7} {'L.hs':>7} {'d%':>6}  "
          f"{'F.cb':>7} {'L.cb':>7} {'d%':>6}  "
          f"{'F.cs':>7} {'L.cs':>7} {'d%':>6}")
    for n in ns:
        cells = []
        for m in MODES:
            f, lem = med[n][m]
            if f is None or lem is None:
                cells.append("    nan     nan     nan")
            else:
                # Negative d% = F faster than Lem (our stack wins).
                d = (f / lem - 1.0) * 100
                cells.append(f"{f:7.2f} {lem:7.2f} {d:+6.1f}")
        print(f"{n:>5}  " + "  ".join(cells))

    print("\n=== F vs Lem summary (median across all sweep n) ===")
    for m, label in zip(MODES, ("hot_bat", "hot_ser", "cold_bat", "cold_ser")):
        deltas = []
        wins = 0   # F faster (negative delta)
        ties = 0
        losses = 0
        for n in ns:
            f, lem = med[n][m]
            if f is None or lem is None:
                continue
            d = (f / lem - 1.0) * 100
            deltas.append(d)
            if d < -1.0:   wins += 1
            elif d > 1.0:  losses += 1
            else:          ties += 1
        if deltas:
            ds = sorted(deltas)
            mid = ds[len(ds)//2]
            print(f"  {label:9s}  median F vs Lem {mid:+6.1f}%   "
                  f"F-wins/ties/F-losses = {wins}/{ties}/{losses}/{len(deltas)} "
                  f"min={min(ds):+.1f}% max={max(ds):+.1f}%")

    print("\n# paste into plot.py:")
    print("m4_fvl_sweep = {")
    for n in ns:
        cells = []
        for m in MODES:
            f, lem = med[n][m]
            if f is None or lem is None:
                cells.append('"' + m + '":(None,None)')
            else:
                cells.append(f'"{m}":({f:.3f},{lem:.3f})')
        print(f"    {n}: {{" + ", ".join(cells) + "},")
    print("}")

if __name__ == "__main__":
    main()

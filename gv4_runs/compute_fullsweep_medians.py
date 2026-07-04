#!/usr/bin/env python3
"""Compute per-cell medians across fullsweep_run{1..5}.txt.

Each run file is the unmodified output of `./bench 4000 5000` with the
extended sweep (22 sizes: 10 powers of 2 + 12 non-power-of-2 values
added 2026-05-12 at Lemire's request).

Parses two kinds of rows:
 - Main table rows: `  size  | warm linear binary simd pi5 pi5s m4 m4s gv4 gv4s | cold ...`
 - Ship A/B rows:   `  size* | gv4_spine=X gv4_spine_N=Y (warm) | gv4_spine=X gv4_spine_N=Y (cold)`

Emits:
 - fullsweep_summary.txt: human-readable table of 5-run medians.
 - fullsweep_medians.py: Python dicts ready to copy into plot.py.
"""
import re
import statistics
from pathlib import Path

HERE = Path(__file__).parent
RUNS = sorted(HERE.glob("fullsweep_run*.txt"))
assert len(RUNS) == 5, f"expected 5 runs, got {len(RUNS)}"

MAIN_RE = re.compile(
    r"^\s*(\d+)\s*\|"
    + r"\s+(\S+)" * 9
    + r"\s*\|"
    + r"\s+(\S+)" * 9
)
SHIP_RE = re.compile(
    r"^\s*(\d+)\*\s*\|\s*gv4_spine=(\S+)\s+gv4_spine_\d+=(\S+)\s+\(warm\)"
    r"\s*\|\s*gv4_spine=\S+\s+gv4_spine_\d+=(\S+)\s+\(cold\)"
)

# samples[size][column] -> list of floats across runs
main_samples: dict[int, list[list[float]]] = {}
# ship_samples[size] -> list of (warm_N, cold_N) tuples across runs
ship_samples: dict[int, list[tuple[float, float]]] = {}

MAIN_COLS = ["linear", "binary", "simd", "pi5", "pi5s", "m4", "m4s", "gv4", "gv4s"]

for run_path in RUNS:
    with run_path.open() as f:
        for line in f:
            m = MAIN_RE.match(line)
            if m:
                size = int(m.group(1))
                vals_warm = [float(m.group(i + 2)) for i in range(9)]
                vals_cold = [float(m.group(i + 11)) for i in range(9)]
                entry = main_samples.setdefault(size, [[] for _ in range(18)])
                for i, v in enumerate(vals_warm):
                    entry[i].append(v)
                for i, v in enumerate(vals_cold):
                    entry[9 + i].append(v)
                continue
            m = SHIP_RE.match(line)
            if m:
                size = int(m.group(1))
                warm_spec = float(m.group(3))
                cold_spec = float(m.group(4))
                ship_samples.setdefault(size, []).append((warm_spec, cold_spec))


def median(xs: list[float]) -> float:
    return statistics.median(xs)


# --- human-readable summary ---
out_txt = HERE / "fullsweep_summary.txt"
with out_txt.open("w") as f:
    f.write(
        f"5-run median of ./bench 4000 5000 on GV4 r8g, 2026-05-12, "
        f"extended sweep (22 n values). Raw: fullsweep_run{{1..5}}.txt.\n\n"
    )
    header = f"{'n':>5}  | " + " ".join(f"{c:>6}" for c in MAIN_COLS)
    f.write(header + "  warm  |  " + " ".join(f"{c:>6}" for c in MAIN_COLS) + "  cold\n")
    f.write("-" * (len(header) * 2 + 12) + "\n")
    for size in sorted(main_samples):
        row = main_samples[size]
        warms = [median(row[i]) for i in range(9)]
        colds = [median(row[9 + i]) for i in range(9)]
        f.write(
            f"{size:>5}  | "
            + " ".join(f"{v:>6.2f}" for v in warms)
            + "  warm  | "
            + " ".join(f"{v:>6.2f}" for v in colds)
            + "  cold\n"
        )
        if size in ship_samples:
            samples = ship_samples[size]
            w = median([s[0] for s in samples])
            c = median([s[1] for s in samples])
            f.write(
                f"{size:>5}* | gv4_spine_{size}: warm {w:.2f}  cold {c:.2f}\n"
            )

# --- plot.py-friendly python dicts ---
out_py = HERE / "fullsweep_medians.py"
with out_py.open("w") as f:
    f.write("# 5-run medians on GV4 r8g, 2026-05-12, extended sweep\n")
    f.write("# (22 n values: 10 powers of 2 + 12 non-power-of-2 added\n")
    f.write("# per Lemire's request).\n")
    f.write("# Copy into plot.py as gv4_fullsweep / gv4_fullsweep_cold.\n\n")

    f.write("gv4_fullsweep_warm = {\n")
    for size in sorted(main_samples):
        row = main_samples[size]
        vals = [median(row[i]) for i in range(9)]
        labels = [f"'{c}': {v:.2f}" for c, v in zip(MAIN_COLS, vals)]
        f.write(f"    {size}: {{{', '.join(labels)}}},\n")
    f.write("}\n\n")

    f.write("gv4_fullsweep_cold = {\n")
    for size in sorted(main_samples):
        row = main_samples[size]
        vals = [median(row[9 + i]) for i in range(9)]
        labels = [f"'{c}': {v:.2f}" for c, v in zip(MAIN_COLS, vals)]
        f.write(f"    {size}: {{{', '.join(labels)}}},\n")
    f.write("}\n\n")

    f.write("# Ship variants at power-of-2 specialized sizes only.\n")
    f.write("gv4_fullsweep_ship = {\n")
    for size in sorted(ship_samples):
        samples = ship_samples[size]
        w = median([s[0] for s in samples])
        c = median([s[1] for s in samples])
        f.write(f"    {size}: {{'warm': {w:.2f}, 'cold': {c:.2f}}},\n")
    f.write("}\n")

print(f"wrote {out_txt}")
print(f"wrote {out_py}")

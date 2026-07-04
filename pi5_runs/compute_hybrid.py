#!/usr/bin/env python3
"""Compute per-cell medians across pi5_runs/hybrid_run{1..5}.txt.

Each run file is the unmodified output of ./bench 4000 5000 on Pi 5
(Cortex-A76) for the 2026-05-12 hybrid A/B evaluation. This mirrors the
GV4 / EMR / M1 hybrid workups:

  - Main table rows (22 sizes, 9 ARM algo columns).
  - gv4_spine_pad A/B rows (cross-variant padded-spine comparator).
  - gv4_spine_N  A/B rows (GV4 compile-time specialization).
  - pi5_spine_N  A/B rows (new Pi 5 compile-time specialization at N in
    {256, 512, 1024, 2048, 4096}).
  - Cross-host n=4096 A/B rows (m4_spine_4096, pi5_spine_4096).
  - pi5 hybrid vs unroll A/B row (the one we actually care about for the
    ship/no-ship call).

Emits:
  - hybrid_summary.txt:  human-readable table of 5-run medians.
  - shipped_summary.txt: ship/no-ship table (pi5_spine_N, hybrid A/B).
"""
import re
import statistics
from pathlib import Path

HERE = Path(__file__).parent
RUNS = sorted(HERE.glob("hybrid_run*.txt"))
assert len(RUNS) == 5, f"expected 5 runs, got {len(RUNS)}"

# Main 9-col ARM row.
MAIN_RE = re.compile(
    r"^\s*(\d+)\s*\|"
    + r"\s+(\S+)" * 9
    + r"\s*\|"
    + r"\s+(\S+)" * 9
)
# pi5_spine_N A/B row: pi5_spine=X pi5_spine_N=Y (warm) | pi5_spine=X pi5_spine_N=Z (cold)
PI5_N_RE = re.compile(
    r"^\s*(\d+)\*\s*\|\s*pi5_spine=\S+\s+pi5_spine_\d+=(\S+)\s+\(warm\)"
    r"\s*\|\s*pi5_spine=\S+\s+pi5_spine_\d+=(\S+)\s+\(cold\)"
)
# pi5 hybrid vs unroll: pi5_spine_4096_unroll=X pi5_spine_4096_hybrid=Y (warm) | ... cold
HYBRID_RE = re.compile(
    r"^\s*4096\*\s*\|\s*pi5_spine_4096_unroll=(\S+)\s+pi5_spine_4096_hybrid=(\S+)\s+\(warm\)"
    r"\s*\|\s*pi5_spine_4096_unroll=(\S+)\s+pi5_spine_4096_hybrid=(\S+)\s+\(cold\)"
)

MAIN_COLS = ["linear", "binary", "simd", "pi5", "pi5s", "m4", "m4s", "gv4", "gv4s"]

main_samples: dict[int, list[list[float]]] = {}
pi5N_samples: dict[int, list[tuple[float, float]]] = {}
hybrid_samples: list[tuple[float, float, float, float]] = []
# pi5_spine baseline (pi5s column from main row) used for deltas.

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
            m = PI5_N_RE.match(line)
            if m:
                size = int(m.group(1))
                pi5N_samples.setdefault(size, []).append(
                    (float(m.group(2)), float(m.group(3)))
                )
                continue
            m = HYBRID_RE.match(line)
            if m:
                hybrid_samples.append(
                    (float(m.group(1)), float(m.group(2)),
                     float(m.group(3)), float(m.group(4)))
                )


def median(xs: list[float]) -> float:
    return statistics.median(xs)


# --- main bench summary ---
summary = HERE / "hybrid_summary.txt"
with summary.open("w") as f:
    f.write(
        "5-run medians of ./bench 4000 5000 on Pi 5 (Cortex-A76), 2026-05-12.\n"
        "Raw outputs: pi5_runs/hybrid_run{1..5}.txt.\n\n"
        "Main bench (9 ARM columns). ns/query.\n\n"
    )
    header = f"{'n':>5} | " + " ".join(f"{c:>6}" for c in MAIN_COLS)
    f.write(header + "  warm   |  " + " ".join(f"{c:>6}" for c in MAIN_COLS) + "  cold\n")
    f.write("-" * 160 + "\n")
    for size in sorted(main_samples):
        row = main_samples[size]
        warms = [median(row[i]) for i in range(9)]
        colds = [median(row[9 + i]) for i in range(9)]
        f.write(
            f"{size:>5} | "
            + " ".join(f"{v:>6.2f}" for v in warms)
            + "  warm   | "
            + " ".join(f"{v:>6.2f}" for v in colds)
            + "  cold\n"
        )

    f.write("\nPi 5 compile-time spine specializations (pi5_spine_N vs pi5_spine):\n")
    f.write(f"{'n':>5}  pi5_spine warm/cold        pi5_spine_N warm/cold        delta warm  delta cold\n")
    for size in sorted(pi5N_samples):
        row = main_samples[size]
        base_w = median(row[4])  # pi5s column
        base_c = median(row[9 + 4])
        samples = pi5N_samples[size]
        w = median([s[0] for s in samples])
        c = median([s[1] for s in samples])
        dw = (w - base_w) / base_w * 100.0
        dc = (c - base_c) / base_c * 100.0
        f.write(
            f"{size:>5}  {base_w:>6.2f} / {base_c:>6.2f}          "
            f"{w:>6.2f} / {c:>6.2f}           "
            f"{dw:>+6.1f}%     {dc:>+6.1f}%\n"
        )

    f.write("\nPi 5 n=4096 hybrid vs unroll A/B (what the ship call hinges on):\n")
    uw = median([s[0] for s in hybrid_samples])
    hw = median([s[1] for s in hybrid_samples])
    uc = median([s[2] for s in hybrid_samples])
    hc = median([s[3] for s in hybrid_samples])
    f.write(f"    unroll: warm {uw:.2f}  cold {uc:.2f}\n")
    f.write(f"    hybrid: warm {hw:.2f}  cold {hc:.2f}\n")
    f.write(
        f"    delta : warm {((hw - uw) / uw * 100.0):+.1f}%  "
        f"cold {((hc - uc) / uc * 100.0):+.1f}%\n"
    )

    # Strict-monotone test for warm: hybrid < unroll on every run.
    wins = sum(1 for s in hybrid_samples if s[1] < s[0])
    f.write(f"    warm hybrid < unroll on {wins}/5 runs\n")
    f.write(f"    per-run unroll warms: " + " ".join(f"{s[0]:.2f}" for s in hybrid_samples) + "\n")
    f.write(f"    per-run hybrid warms: " + " ".join(f"{s[1]:.2f}" for s in hybrid_samples) + "\n")
    f.write(f"    per-run unroll colds: " + " ".join(f"{s[2]:.2f}" for s in hybrid_samples) + "\n")
    f.write(f"    per-run hybrid colds: " + " ".join(f"{s[3]:.2f}" for s in hybrid_samples) + "\n")

print(f"wrote {summary}")

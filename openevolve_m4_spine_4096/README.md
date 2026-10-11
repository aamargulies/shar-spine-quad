# OpenEvolve experiment: simd_quad_m4_spine_4096 cold-cache regression

> **Correction notice (2026-10-11).** This document is a lab note kept as history, and the experiment setup it describes is stale: **do not run it as-is.** The baseline table scores candidates against the retired unroll rather than the shipped hybrid (see the note under "What this evolves"), `initial_program.c` is that retired unroll (note under "Files"), and the evaluator's `cold_ns` objective is parsed from `bench.cpp`'s unflushed cold column (note under "Known limits"). Before the experiment is meaningful, `initial_program.c` must be regenerated from the shipped `simd_quad_m4_spine_4096`, the baseline re-measured, and the cold objective replaced by a flushed measurement. A 2026-10-11 review of the repository's measurements found aggregation and harness defects behind several claims below; each affected statement is followed by a `Correction 2026-10-11` note and the original text is left in place. The authoritative list of retractions and replacement numbers is [Text/corrections_2026-10.md](../Text/corrections_2026-10.md); where that file and this one disagree, that file wins.

Host: **M4 Max or M1 Pro only.** Do not run on Pi 5 / GV4 / Intel hosts —
baselines and the `4096*` parse only match the Apple-silicon build.

## What this evolves

The `simd_quad_m4_spine_4096` function in `simd_quad_m4.c` (see CLAUDE.md
open item 1). Baseline on M4 Max, 5-run medians:

| variant                    | warm ns | cold ns |
|---                         |---      |---      |
| `simd_quad_m4_spine`       | 4.34    | 6.47    |
| `simd_quad_m4_spine_4096`  | 3.65    | 18.65   |

Evolution target: beat the general-n baseline on cold (≥1.0 cold_ratio)
while staying within 10% of it warm (≥0.9 warm_ratio).

> Correction 2026-10-11: the baseline numbers are the medians of the `4096*` rows in `m4_runs/rebench_run{1..5}.txt` (2026-05-01), taken when `simd_quad_m4_spine_4096` was still the retired unroll (three quaternary iterations + final-lo). The shipped kernel since 2026-05-12 is the hybrid (two iterations + branchless 4-probe finish), whose M4 Max 5-run medians are 3.71 ns warm / 21.94 ns cold (`m4_runs/hybrid_summary.txt`), so the evolution target is defined against a superseded starting point. The "cold regression" itself may be a measurement-order artifact rather than structural: `bench.cpp`'s cold column has no cache flush, the spine kernel's cold pass runs right after the non-spine kernel's cold pass with identical targets (so the block line is an L2 hit on Apple's large L2) while the `4096*` row runs after its own 32 MB warm sweep, the reported gap matches L2-hit vs SLC-hit latencies, and the same asymmetry reproduces on the Pi 5. That is a hypothesis needing a test on Apple hardware with both measurements taken after an explicit flush (`Text/corrections_2026-10.md` §5).

## Files

- `initial_program.c` — stock `simd_quad_m4_spine_4096` wrapped in
  `// EVOLVE-BLOCK-START / END` markers. Signature is frozen.

  > Correction 2026-10-11: `initial_program.c` is the retired unroll (three quaternary iterations, then `lo = (spine[base] < pos) ? base + 1 : base`), not the shipped hybrid `simd_quad_m4_spine_4096` (two iterations + branchless 4-probe finish) — compare the `EVOLVE-BLOCK` body with `Text/hybrid.md` (`Text/corrections_2026-10.md` §5).
- `evaluator.py` — splices the evolved body into a tmp copy of
  `simd_quad_m4.c`, links against the repo's `bench.cpp`, runs correctness
  then 5 × `./bench 4000 5000`, parses the `m4 4096*` row.
- `config.yaml` — 200 iterations, MAP-Elites on (prefetch_count, vld1_count,
  block_load_hoisted, cold_ns). Island model, diff-based mutations.

## Running

Requires:
- `openevolve` Python package (`pip install openevolve`) — needs Python 3.10+.
- An Anthropic API key: `export ANTHROPIC_API_KEY=...`.
- Apple clang with NEON support (any recent Xcode CLT).

```sh
cd openevolve_m4_spine_4096
python -m openevolve.cli \
    initial_program.c \
    evaluator.py \
    --config config.yaml
```

Expected wall time on M4 Max: 200 iters × (~1s compile + 6 × ~2s bench) ≈
40 min if serial, less with cascade early-exits on compile failures.
Expected API cost: $10-30 at Sonnet 4.6 primary / Opus 4.7 secondary.

> Correction 2026-10-11: do not run this as-is — see the correction notice at the top of this file (stale unroll baseline, stale `initial_program.c`, unflushed `cold_ns` objective).

## Validating a winner on both Apple hosts

The evaluator runs on one host at a time. If a candidate wins on M4 Max,
copy the evolved body into `simd_quad_m4.c` on the M1 Pro host, rebuild,
and confirm the cold regression actually resolves there too before
shipping. CLAUDE.md's "reproduces almost identically on M1 Pro" note
(+188% vs +194%) is the whole reason we believe the regression is
structural, so a fix that works on only one host is suspect.

> Correction 2026-10-11: cross-host reproduction — +188% on the M4 Max (`m4_runs/rebench_run{1..5}.txt`, `4096*` row 5-run medians 18.65 / 6.47 ns cold) and about +196% on the M1 Pro (`m1_runs/rebench_run{1..5}.txt`, `4096*` row 5-run medians 32.70 / 11.05 ns cold; the "+194%" quoted above does not reproduce from the `4096*` rows, which give +196%; the nearest archived derivation (32.70 over the main-table m4s cold median 11.1, printed to one decimal) is +195% — `m1_runs/hybrid_run{1..5}.txt` gives +213% for the unroll, 32.24 / 10.30, and +212% for the hybrid, 32.12 / 10.30) — does not by itself establish a structural mechanism: both hosts were measured with the same unflushed harness in the same measurement order, and the same `4096*`-row-vs-main-table asymmetry reproduces on the Pi 5. Treat "structural" as a hypothesis until both measurements are taken after an explicit flush on Apple hardware (`Text/corrections_2026-10.md` §5).

## Known limits

- If the structural hypothesis (1-line spine + straight-line issue) is
  fully correct, no in-function mutation fixes it and evolution will
  converge to "the current version is already pareto-optimal in the warm/cold
  trade-off." That's still a useful outcome: it confirms the mechanism and
  the ship recommendation stays "prefer `simd_quad_m4_spine` for
  first-touch workloads."

  > Correction 2026-10-11: "1-line spine" assumes an alignment the benchmark never enforces — spines are 16-byte-aligned `std::vector` allocations, so about 87.5% of 128-byte blocks straddle two cache lines (`Text/corrections_2026-10.md` §5). The evaluator's `cold_ns` objective is parsed from `bench.cpp`'s cold column, which has no cache flush and whose ~35 MB footprint fits the LLC of every host except the Pi 5, so it scores L2/SLC-regime behaviour, not DRAM-cold behaviour (`Text/corrections_2026-10.md` §5).
- Parallel evaluations are disabled because bench timing needs the core
  quiet. If you want more throughput, run the evolution on AC power with
  other apps closed.
- `OPENEVOLVE_M4_CPU_FLAG` env var overrides the `-mcpu=apple-m4` default
  (set it to `-mcpu=apple-m1` on M1 Pro).

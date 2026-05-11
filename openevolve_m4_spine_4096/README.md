# OpenEvolve experiment: simd_quad_m4_spine_4096 cold-cache regression

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

## Files

- `initial_program.c` — stock `simd_quad_m4_spine_4096` wrapped in
  `// EVOLVE-BLOCK-START / END` markers. Signature is frozen.
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

## Validating a winner on both Apple hosts

The evaluator runs on one host at a time. If a candidate wins on M4 Max,
copy the evolved body into `simd_quad_m4.c` on the M1 Pro host, rebuild,
and confirm the cold regression actually resolves there too before
shipping. CLAUDE.md's "reproduces almost identically on M1 Pro" note
(+188% vs +194%) is the whole reason we believe the regression is
structural, so a fix that works on only one host is suspect.

## Known limits

- If the structural hypothesis (1-line spine + straight-line issue) is
  fully correct, no in-function mutation fixes it and evolution will
  converge to "the current version is already pareto-optimal in the warm/cold
  trade-off." That's still a useful outcome: it confirms the mechanism and
  the ship recommendation stays "prefer `simd_quad_m4_spine` for
  first-touch workloads."
- Parallel evaluations are disabled because bench timing needs the core
  quiet. If you want more throughput, run the evolution on AC power with
  other apps closed.
- `OPENEVOLVE_M4_CPU_FLAG` env var overrides the `-mcpu=apple-m4` default
  (set it to `-mcpu=apple-m1` on M1 Pro).

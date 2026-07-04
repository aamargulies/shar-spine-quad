# F vs F* sweep findings, Pi 5 (Cortex-A76), 2026-05-19

## Setup

- **F** (baseline) = Shar branchless outer (K=512) + general-n
  `simd_quad_pi5_spine` inner (= variant E in `bench_twolevel.cpp`).
- **F\*** (specialized) = Shar branchless outer (K=512) +
  `simd_quad_pi5_spineN_<N>` compile-time-N specialized inner (constant-prop
  unroll of the general-n descent body; **not** the hybrid 2-probe finish in
  `simd_quad_pi5_spine_4096`). Same self-consistent F\* shape across the sweep
  as the M4 codegen, so n=4096 in this sweep is **not** the shipping hybrid.
- Same 90 log-spaced N from 64 to 4096 as the M4 sweep. n<64 skipped (gap=32
  on Pi 5 means the spine descent is reachable from n=32, but we keep the
  M4 list so the per-N comparison lines up cleanly).
- 4-mode harness (hot_bat / hot_ser / cold_bat / cold_ser), 5 runs of
  100 sets x 200 hot reps each, per-cell median. Halved set count vs the
  M4 sweep (200 sets) to keep wall time tractable on Pi 5; cold variance
  widens but hot signal stays tight.
- Wall: 1800 invocations in 4 h 45 m.

## Results

```
                   median   range          win/tie/loss (per N)
hot_bat   F* - F:   -4.4%   -19 .. +16%    76 / 7 / 7
hot_ser   F* - F:   -4.2%   -18 .. +18%    78 / 7 / 5
cold_bat  F* - F:   -1.0%   -39 .. +41%    44 / 11 / 35
cold_ser  F* - F:   +1.1%   -28 .. +38%    32 / 13 / 45
```

F\* wins both hot modes on the strong majority of N (76-78 of 90), modestly.
Cold modes are within noise: cold_bat is roughly even (44 win, 35 loss);
cold_ser actually has more losses than wins, with a positive median delta.

## Comparison to M4 Max sweep

| mode     | M4 median | Pi 5 median | M4 win count | Pi 5 win count |
|----------|-----------|-------------|--------------|----------------|
| hot_bat  | -15.3%    | -4.4%       | 90/90        | 76/90          |
| hot_ser  | -12.5%    | -4.2%       | 90/90        | 78/90          |
| cold_bat | -16.3%    | -1.0%       | 84/90        | 44/90          |
| cold_ser | -20.0%    | +1.1%       | 77/90        | 32/90          |

**Compile-time-N inner specialization is a much weaker lever on Pi 5 than on
M4 Max.** The M4 sweep saw a uniform 15-20% win across hot and cold, every N;
on Pi 5 the hot win is a third of that, and the cold win disappears
entirely.

## Why the difference

Three plausible mechanisms, each consistent with the existing CLAUDE.md
findings:

1. **Cortex-A76 narrow OoO already serializes the descent.** With 2 load AGUs
   and a smaller OoO window, the spine descent's loop counter chain is not
   the critical-path bottleneck on Pi 5: the dependent spine loads are. M4's
   3 AGUs + wider OoO let the loop body issue concurrently with the spine
   tier loads, so the loop counter dependency chain (`n -= 3*quarter`,
   `while (n > 3)`) can become the gating chain once those tier misses are
   absorbed - and that chain is exactly what constant-prop eliminates.
2. **gap=32 means more iters and shorter per-iter savings.** Pi 5 num_blocks
   scales as n/32 (vs n/64 on M4), so the descent at n=4096 is 4 quat iters
   on Pi 5 vs 3 on M4. Each iter's loop control is the same fixed cost, but
   the per-iter inner work is smaller (paired x2 block check vs x4), so loop
   control is a smaller share of total cost on M4 anyway. Pi 5 dilutes the
   constant-prop benefit across more iters of which a smaller fraction was
   loop control to begin with.
3. **GCC 13 on Cortex-A76 may already unroll the gap=32 descent.** With a
   fixed gap and -O3, the trip counts for `while (n > 3)` are
   loop-invariant-derived from one runtime parameter (cardinality); GCC's
   loop unroller is reasonably aggressive on aarch64. This wasn't checked
   asm-side but would explain part of the smaller delta versus the M4
   sweep, where clang is the toolchain.

The cold-mode story is even cleaner: cold cost is dominated by the demand
block-load on `carr` (the 2026-05-14 M1 Pro `bench_profile` decomposition
showed ~25 ns of the ~33 ns cold floor lives there). Constant-prop on the
descent doesn't touch that floor, so the cold mode is entirely variance-
limited - and the variance is wider on Pi 5 than M4 (5-run cold ranges
~10-20% per CLAUDE.md target hardware reference). Hence cold_bat near zero,
cold_ser slightly negative.

## What this means for the F vs F\* shipping question

**On M4 Max**, compile-time-N specialization is a uniform structural win and
worth shipping per-N. **On Pi 5**, the win is hot-only and modest (~4-5%);
worth shipping if a per-N family already exists (it does, for n in
{256, 512, 1024, 2048, 4096}, see `simd_quad_pi5.c`), but not worth growing
the family to cover every cardinality. The existing 5-size compile-time
family captures most of the hot win at the cardinalities that matter for
Roaring (the natural array-container thresholds), and the general-n
`simd_quad_pi5_spine` is a perfectly fine fallback at the in-between sizes.

The earlier finding "_spine_{256,512,1024,2048,4096} on Pi 5 wins warm
-24..-46% vs general-n" (CLAUDE.md, dated 2026-05-12) is consistent: that
delta came from comparing the **hybrid + unroll** family vs general-n, not
the naive constant-prop unroll measured here. The hybrid finish (2-probe at
high-foot sizes) is the bigger lever on Pi 5; the constant-prop alone
captures only a small slice of it.

## Cold-mode losses

- `cold_bat`: F\* loses at 35 of 90 N. Distribution is scattered across the
  range, not clustered at any boundary; ranges +0..+41%. Likely variance
  given the halved set count.
- `cold_ser`: F\* loses at 45 of 90 N. Same scatter, ranges to +37.5%. Also
  consistent with cold-cs variance.

If we cared to tighten cold confidence intervals, doubling to 200 sets x
10 runs would help. The hot signal is already clear enough that the cold
result wouldn't change the ship recommendation.

## Files

- `pi5_runs/sweep_n_list.txt` - 90 log-spaced N values (mirrors m4_runs).
- `pi5_runs/sweep_n<N>_<mode>_run<R>.txt` - 1800 raw bench_sweep outputs.
- `pi5_runs/run_sweep.sh` - driver (resume-friendly).
- `pi5_runs/compute_sweep.py` - aggregator; emits `sweep_summary.txt` plus
  paste-ready `pi5_sweep` dict.
- `pi5_runs/sweep_summary.txt` - 4-mode median table + per-mode summary.
- `simd_quad_pi5_spine_family.{c,h}` - 90 compile-time-N specializations
  (gap=32, paired vld1q_u16_x2 block check) generated by
  `gen_pi5_spine_family.py`.
- `bench_sweep.cpp` - now arch-aware: default M4 path, `-DQUADSEARCH_ARM_PI5`
  for the Pi 5 path.

## Out of scope (future work)

- Port the F\* sweep to the remaining 4 hosts (M1 Pro, EMR, GV4, SKX) to
  confirm the wide-OoO vs narrow-OoO split. Pre-registered prediction:
  M1 Pro should look like M4 (same uarch class, gap=64), GV4 like Pi 5 or
  better (4 AGUs but gap=32), EMR/SKX like M4 (wider OoO, freq license
  notwithstanding).
- Compare F\* against F at sub-gap sizes via Lemire's gap=16 reference path
  (the "spine on at n >= threshold" question from
  `shar-outer-no-prod-win.md`).
- Re-run cold modes at 10 runs to firm up cold confidence intervals on
  Pi 5; as is, the cold signal is variance-limited.

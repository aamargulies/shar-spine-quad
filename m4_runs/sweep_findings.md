# F vs F* sweep findings — M4 Max, 2026-05-19

## Setup

- **F** (baseline) = Shar branchless outer (K=512) + general-n `simd_quad_m4_spine` inner (= variant E in `bench_twolevel.cpp`).
- **F\*** (specialized) = Shar branchless outer (K=512) + `simd_quad_m4_spineN_<N>` compile-time-N specialized inner (constant-prop unroll of the general-n descent body; **not** the hybrid 4-probe finish — see `simd_quad_m4_spine_4096` for the hybrid that ships at N=4096 in `bench_twolevel`).
- 90 log-spaced N from 64 to 4096. n<64 skipped — at gap=64 the M4 inner short-circuits to small-fastpath before reaching the spine descent, so F == F* trivially.
- 4-mode harness (hot_bat / hot_ser / cold_bat / cold_ser), 5 runs of 200 sets × 200 hot reps each, per-cell median. Same harness shape as `bench_twolevel.cpp`.

## Results

```
                   median   range          win/tie/loss (per N)
hot_bat   F* − F:  −15.3%   −40 .. −4%     90 / 0 / 0
hot_ser   F* − F:  −12.5%   −29 .. −7%     90 / 0 / 0
cold_bat  F* − F:  −16.3%   −43 .. +9%     84 / 0 / 6
cold_ser  F* − F:  −20.0%   −54 .. +37%    77 / 1 / 12
```

F\* wins on every n in both hot modes and on the strong majority of n in both cold modes.

## What this means

**Compile-time-N inner specialization is a uniform ~15-20% win across the full Roaring container size range on M4 Max.** This is despite the F\* shape being the *retired* unroll (general descent with constant num_blocks), not the shipping hybrid (`_spine_4096` = 2 quat iters + branchless 4-probe finish). The win comes purely from the compiler unrolling the descent loops once the trip count is constant — eliminating the loop counter dependency chain in the `while (n > 3)` and `while (n > 1)` headers.

The headline relevance: **`simd_quad_m4_spine` (general-n) leaves a meaningful chunk of performance on the table at every N, not just at N=4096.** The shipping `_spine_4096` hybrid is even faster (`bench_twolevel` E vs F at N=4096: −19% hot_bat), but its mechanism is harder to extend per-N because the hybrid finish width depends on N/gap.

## Cold-mode losses

- `cold_bat`: F\* loses at n ∈ {143, 189, 208, 252, 858, 1659} — small (≤+8.6%), within the cold variance band.
- `cold_ser`: F\* loses at 12 n values, most by ≤+15% but n=1739 hits +36.5%. cold_ser is the noisiest mode (per `bench_twolevel` 5-run ranges); some of these may be variance, not signal.

The losses don't cluster around a particular n boundary, suggesting they're variance rather than a structural anti-pattern. If we cared, a 10-run sample would tighten cold_ser confidence intervals.

## Connecting to the open CRoaring question

Memory note `shar-outer-no-prod-win.md` (2026-05-14) flagged: "today's M4 sweep showed FN cold_ser regresses vs Lem at n ≤ 512 but wins at n ≥ 1024. CRoaring may want a 'spine on at n ≥ threshold' knob."

The current sweep is **F vs F\***, not F vs Lem, so it doesn't directly answer the threshold question. But it does say: **once you've decided to use the spine, compile-time-N specialization is worthwhile at every n ≥ 64 — there's no n range where the general-n inner wins.** If a threshold-based dispatcher gates "use spine at n ≥ T" for some T, the spine arm should be the F\* compile-time-N variant, not the general-n F.

## Measurement gotcha (recorded for future benchmarks)

First cold measurement in a fresh process pays one-time TLB warmup / page-fault / OS page-cache priming costs that the second variant doesn't. Original sweep with order `thrash → measure F → thrash → measure F*` gave bogus cold_bat numbers (F looked 4-8× slower than F* because F always ate the page-fault hit). Fix in `bench_sweep.cpp`: discarded throwaway pass before the timed measurements so the first timed run isn't fighting page faults. Re-ran 900 cold-mode invocations after fix; hot modes were unaffected (the warmup_hot lambda already paid this cost on the hot path).

## Files

- `bench_sweep.cpp` — F vs F* harness (single inner_n per process, 4 modes via argv).
- `simd_quad_m4_spine_family.{c,h}` — codegen output, 90 specializations + dispatcher.
- `gen_m4_spine_family.py` — codegen script.
- `m4_runs/sweep_n_list.txt` — 90 log-spaced N values.
- `m4_runs/run_sweep.sh` — driver (resume-friendly).
- `m4_runs/sweep_n<N>_<mode>_run<R>.txt` — 1800 raw run outputs.
- `m4_runs/compute_sweep.py` — aggregator → `m4_runs/sweep_summary.txt`.
- `m4_sweep_data.py` — `m4_sweep` dict for plotting (extracted from `sweep_summary.txt`).
- `plot_m4_sweep.py` → `bench_m4_sweep.png` (4-panel) + `bench_m4_sweep_delta.png` (overlay).

## Out of scope (future work)

- Port F\* sweep to other 5 hosts (Pi 5, M1 Pro, EMR, GV4 already have `_spine_{256,512,1024,2048,4096}` family — incremental cost; SKX has only 4096).
- Compare F\* to *hybrid-style* per-N specialization (would `_spineN_<N>` benefit from the 2-quat + 4-probe finish at N where num_blocks divides cleanly?) — separate axis from this sweep.
- Compare F\* to F at sub-gap sizes via Lemire's gap=16 reference path (the "spine on at n ≥ threshold" question).

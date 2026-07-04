# Experiment: per-n compile-time spine specializations for EMR and GV4

## Motivation

The EMR and GV4 warm curves for the general-n spine variant show a sawtooth: every doubling of n that adds a binary-tail iteration (`while (n > 1)` after the quaternary descent) costs roughly one load-use latency (~5 ns) vs the neighboring n that lands on a pure power-of-4 count. The first attempted fix, descent padding (3-probe branchless finish + two 0xFFFF sentinels in the spine), did not achieve the desired results on GV4. Next experiment: sidestep the sawtooth by fully unrolling the descent for each common n, following the same pattern as the existing `simd_quad_*_spine_4096`.

The `simd_quad_intel_spine_4096` and `simd_quad_graviton_spine_4096` specializations already exist and on EMR gave −22% warm / −30% cold (re-measured 2026-05-01), on GV4 roughly −10% warm / −16% cold. If the same mechanism (loop-control, bounds checks, and data-dependent binary tail all disappear; offsets materialize as constants) is what's driving those wins, it should translate to the smaller sizes too.

## Scope

Add compile-time specializations for {128, 256, 512, 1024, 2048} to both `simd_quad_intel.c` and `simd_quad_graviton.c`. 10 new functions total.

Per-size descent shape at gap=32:

| n | num_blocks | descent |
|---|---|---|
| 128 | 4 | pure finish (n=4 at entry, one quat iter with quarter=1, then finish) |
| 256 | 8 | 1 quat (n=8 -> 2) + 1 binary step + final lo |
| 512 | 16 | 2 quat (n=16 -> 4) + finish |
| 1024 | 32 | 2 quat (n=32 -> 8 -> 2) + 1 binary step + final lo |
| 2048 | 64 | 3 quat (n=64 -> 16 -> 4) + finish |
| 4096 | 128 | 3 quat (n=128 -> 32 -> 8 -> 2) + 1 binary step + final lo  (existing) |

Each specialization materializes all offsets as constants and straight-lines the descent with no `while` loops and no data-dependent iteration count.

## Implementation plan

1. EMR and GV4 only for now. The sawtooth is EMR/GV4-specific in the data; other hosts can be ported later if the signal is strong.

2. Keep the general-n spine as the fallback, no size-dispatcher in the shipped function. Each `_spine_N` gets exposed directly and the bench adds per-size A/B rows, same pattern as the existing `_spine_4096` row and the `*pad` A/B row we just added.

3. Correctness: the bench harness already spins over all 10 sweep sizes, so extending `correctness()` to call each `_spine_N` at its matching n is a small diff.

4. Bench output: print a `*N` row per specialization at its matching size, e.g.:

   ```
    2048* | gv4_spine=20.5 gv4_spine_2048=16.4  (warm)  | gv4_spine=79.0 gv4_spine_2048=65.2  (cold)
   ```

## Expected results

If the mechanism diagnosis is right, the specializations should remove the sawtooth entirely on warm: every n where the general-n spine sits on the high foot of the sawtooth (n=256, 1024, 4096 at gap=32) should drop by ~5 ns to match the low feet (n=128, 512, 2048). Cold wins are less certain; the `_spine_4096` cold improvement on GV4 came from overlapping the block-load miss behind the straight-line descent, which the smaller n specializations may not reproduce since their descents are already short enough that the general-n version overlaps too.

## Status

Design agreed. Implementation pending.

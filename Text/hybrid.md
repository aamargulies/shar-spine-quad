# The hybrid spine-descent shape

The "hybrid" is the descent shape for the n=4096 spine specialization (and the `_spine_{256,1024}` high-foot siblings on gap=32 hosts). It replaced a straight-line "unroll" shape on every host where we A/B'd it, and is now what `*_spine_4096` IS on all six hosts.

## The shape

The spine descent is a quaternary search: each iteration has `n` entries in the current window, does 3 SIMD-less compares at offsets `quarter`, `2*quarter`, `3*quarter`, and sums the `<pos` booleans into a branchless base update:

```c
base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * quarter;
```

This cuts `n` by 4×. The question is how to finish once `n` gets small.

**Old shape ("unroll"):** keep descending until `n=2` or `n=1`, then either a `while (n > 1)` binary step + final-lo, or (gap=64 hosts) 3 quat iters + final-lo.

**Hybrid:** exit quat one iteration early and replace the last descent step with a single branchless multi-probe finish — no more dependent load-use round for the binary step:

```c
// gap=32 hosts (quat exits at n=2), used by Pi 5 / EMR / SKX / GV4:
int32_t lo = base + (spine[base] < pos) + (spine[base + 1] < pos);

// gap=64 hosts (quat exits at n=4), used by M4 Max / M1 Pro:
int32_t lo = base + (spine[base  ] < pos) + (spine[base+1] < pos)
                  + (spine[base+2] < pos) + (spine[base+3] < pos);
```

## Per-size descent (gap=32 hosts)

| n | num_blocks | quat iters | finish |
|---|---|---|---|
| 256 | 8 | 1 (quarter=2) | 2-probe |
| 512 | 16 | 2 (quarter=4, 1) | final-lo (pure unroll — low-foot) |
| 1024 | 32 | 2 (quarter=8, 2) | 2-probe |
| 2048 | 64 | 3 (quarter=16, 4, 1) | final-lo (pure unroll — low-foot) |
| 4096 | 128 | 3 (quarter=32, 8, 2) | 2-probe |

Low-foot {512, 2048} stayed as pure unrolls (final-lo after quat-exit n=1); high-foot {256, 1024, 4096} are the hybrid. M4/M1 only have `_spine_4096` (2 quat iters at quarter=16, 4 → 4-probe finish); the other compile-time sizes don't exist on gap=64 hosts because the descent arithmetic is different.

## Why it wins

The hybrid saves **one dependent load-use round** relative to the unroll's binary step. All probes in the finish are independent loads — they issue in parallel, so the OoO engine collapses them into a single load-use latency. The per-host warm deltas (hybrid vs unroll) matched that mechanism: EMR −54.8%, SKX −28.9%, Pi 5 −16.9%, M1 −4.4%, M4 −2.6%, all monotone 5/5. Cold was a wash on most hosts and a solid win on GV4/EMR; SKX's median cold +45.5% was dominated by shared-tenant variance with overlapping per-run ranges.

## Correctness argument

After the last quat iter, the invariant "target in [base, base+n]" means `base ≤ num_blocks - n`, so `spine[base+n-1]` is always a real entry (no sentinels needed). The spine is sorted, so the `<pos` indicators are monotone-decreasing; their sum is exactly the count of entries below `pos`, i.e. the correct offset to add to `base`. `num_blocks` is known at compile time, which is what makes the bound argument watertight and lets us elide the `while (n > 1)` binary tail.

## Status

`_spine_4096` IS the hybrid on every host that has it. Prior unrolls retired. The Apple-silicon cold regression (`_spine_4096` vs general-n `_spine`: M4 Max +188%, M1 Pro +212%) is structural to gap=64 + 128-B spine = 1 cache line + no streamer latch — the hybrid's round-saving shows up warm but can't fix the three tier misses + block-load on the critical path cold.

# The hybrid spine-descent shape

> **Correction notice (2026-10-11).** This document is a lab note kept as history. A 2026-10-11 review of the repository's measurements found aggregation and harness defects behind several claims below; each affected statement is followed by a `Correction 2026-10-11` note and the original text is left in place. The authoritative list of retractions and replacement numbers is [Text/corrections_2026-10.md](corrections_2026-10.md); where that file and this one disagree, that file wins.

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

> Correction 2026-10-11: the per-host deltas above (warm and cold) are ratios of 5-run per-cell medians, not paired per-run deltas (`Text/corrections_2026-10.md` §2, defect 2). The Pi 5 "−16.9%" is a ratio of medians over a bimodal run set; the per-run warms in `pi5_runs/hybrid_summary.txt` (unroll 23.12/23.36/34.75/34.80/23.05 vs hybrid 15.97/19.42/23.81/23.88/15.91) give a paired per-run median of −31.0%, hybrid faster 5/5 (`Text/corrections_2026-10.md` §2.3). The M4 "−2.6%" is likewise a ratio of medians; the per-run warms in `m4_runs/hybrid_summary.txt` (unroll 3.81/3.76/3.81/3.75/4.09 vs hybrid 3.69/3.75/3.71/3.71/4.06) give paired deltas of −3.1/−0.3/−2.6/−1.1/−0.7%, a paired median of −1.1%, with run 2 differing by 0.01 ns, the bench's printed resolution. With five runs a sign test cannot reach p < 0.0625, so "monotone 5/5" is suggestive, not conclusive (`Text/corrections_2026-10.md`, conventions). The finish probes `spine[base]` / `spine[base+1]` are genuinely independent loads; this is distinct from the retracted claim that Shar's *outer* search issues nine independent loads in parallel — that loop is a serial load → compare → csel → load chain (`Text/corrections_2026-10.md` §5).

> Correction 2026-10-11: the "SKX cold +45.5% was dominated by shared-tenant variance" explanation is retracted. In the same archived runs (`skx_runs/hybrid_run{1..5}.txt`, `4096*` rows) the general-n `intel_spine` control is stable at 130.53–132.05 ns cold (about ±0.6%) while the hybrid swings 116.33–213.53 ns, so tenant noise cannot explain the hybrid's spread. Against that control the hybrid is −32% warm (5/5) but cold median +40% vs the control (per-run −12/+62/+41/+40/−6%, hybrid faster in 2 of 5 runs; same `4096*` rows, hybrid 116.33/213.53/185.57/185.01/123.00 ns vs control 131.80/131.86/132.05/131.94/130.53 ns); the SKX hybrid may have a real cold cost (`skx_runs/hybrid_run{1..5}.txt`, `4096*` rows; `Text/corrections_2026-10.md` §2.3; the ratio of 5-run medians is 185.01/131.86 = +40.3%).

## Correctness argument

After the last quat iter, the invariant "target in [base, base+n]" means `base ≤ num_blocks - n`, so `spine[base+n-1]` is always a real entry (no sentinels needed). The spine is sorted, so the `<pos` indicators are monotone-decreasing; their sum is exactly the count of entries below `pos`, i.e. the correct offset to add to `base`. `num_blocks` is known at compile time, which is what makes the bound argument watertight and lets us elide the `while (n > 1)` binary tail.

## Status

`_spine_4096` IS the hybrid on every host that has it. Prior unrolls retired. The Apple-silicon cold regression (`_spine_4096` vs general-n `_spine`: M4 Max +188%, M1 Pro +212%) is structural to gap=64 + 128-B spine = 1 cache line + no streamer latch — the hybrid's round-saving shows up warm but can't fix the three tier misses + block-load on the critical path cold.

> Correction 2026-10-11: the "structural" reading of the Apple `_spine_4096` cold regression is a hypothesis, not a finding. `bench.cpp`'s cold column has no cache flush, and the spine kernel's cold pass runs right after the non-spine kernel's cold pass with identical targets (so the block line is an L2 hit on Apple's large L2) while the dedicated `4096*` row runs after its own 32 MB warm sweep; the reported gap matches L2-hit vs SLC-hit latencies and the same asymmetry reproduces on the Pi 5. It needs a test on Apple hardware with both measurements taken after an explicit flush (`Text/corrections_2026-10.md` §5). Separately, "128-B spine = 1 cache line" assumes an alignment the benchmark never enforces: spines are 16-byte-aligned `std::vector` allocations, so about 87.5% of 128-byte blocks straddle two lines (`Text/corrections_2026-10.md` §5).

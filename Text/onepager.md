# SIMD Quad across six hosts, and what to ship hot vs. cold

> Corrected 2026-10-11 against Text/corrections_2026-10.md; earlier numbers were retracted, see that file.

**Context.** Extension of Daniel Lemire's `simd_quad` membership test for sorted `uint16_t[]` Roaring containers (up to 4096 elements), ported and tuned across six CPU microarchitectures. Six per-host variants of the inner, plus a two-level composition that also touches the outer `keys[]` layer Lemire's post treats as settled. Main-bench measurements are per-cell medians of 5 `./bench 4000 5000` runs per host (`bench_table.txt`); two-level comparisons are paired per-run deltas over 5 archived runs per host (`{host}_runs/twolevel_paired.txt`) plus 10 repaired-harness runs on the Pi 5 (`pi5_runs/twolevel_paired_v2.txt`); raw outputs archived per host under `{pi5,m4,m1,skx,emr,gv4}_runs/`.

## Hosts

| | Pi 5 (A76) | M4 Max | M1 Pro | Skylake-SP 8175M | Emerald Rapids 8559C | Graviton 4 (V2) |
|---|---|---|---|---|---|---|
| line | 64 B | 128 B | 128 B | 64 B | 64 B | 64 B |
| SIMD | 128b NEON | 128b NEON | 128b NEON | AVX-512 (AVX2 used) | AVX-512 (zmm) | 128b NEON |
| L1D | 64 KB | 128 KB | 128 KB | 32 KB | 48 KB | 64 KB |
| load pipes | 2 | 3 | 3 | 2 | 3 | 3 (reported, unverified) |
| gap | 32 | 64 | 64 | 32 | 32 | 32 |
| spec prefetch | kept* | dropped | dropped | kept* | dropped | dropped |

\* "kept" describes the shipped code, not a measured win: the Pi 5 prefetch is a net loss in the archived main bench (corrections §5; see below); SKX has no archived prefetch A/B (the one noted in CLAUDE.md was inconclusive, and `skx_runs/` holds none) and the license-downclock rationale for keeping it was wrong (corrections §5). The Neoverse V2 load-pipe count was corrected from 4 to 3 by the review and is not verified on hardware here.

Apple M1 Pro and M4 Max share `simd_quad_m4.c` without modification: both are 128-B-line, 128b-NEON, wide-OoO Apple-silicon P-cores. The M1 port is a zero-line-change ship.

## Three things that replicated across the board

**The spine is the single biggest inner-layer optimization on every host.** Pack the interpolation probe keys into a dense contiguous region so the cold-cache probes land in a few adjacent cache lines instead of being scattered across the 8 KB array. At n=4096, `bench_table.txt` (5-run medians, non-spine → spine, cold ns/query): Pi 5 299.0 → 150.7, M4 Max 16.8 → 6.5, M1 Pro 37.1 → 11.1, SKX 180.9 → 132.7, EMR 64.9 → 37.2, GV4 65.0 → 34.6 — about 2–3× on the ARM/Apple cores, under 2× on the x86 and Graviton servers. The mechanism is memory-level parallelism over a short contiguous read — the descent touches those few adjacent lines instead of chasing probes through the array — not a stride prefetcher: a 256-byte spine is too short to train one. `bench.cpp`'s cold column has no cache flush (corrections §5), so this is a within-host comparison only.

**gap tracks cache line, not SIMD width.** Even on 512-bit Intel, gap=32 is right because the line is 64 B; a 64-element block would span two lines. A scratch `gap64` variant on Emerald Rapids was uniformly faster cold but alternated sign warm, winning 46-55% at n=256/1024/4096 and losing 45-67% at n=512/2048. n=512 and n=2048 are common Roaring container sizes, which is fatal for a shipping default.

**Speculative `__builtin_prefetch` inside the interpolation loop does not pay anywhere we have an A/B.** Dropped on M4, Emerald Rapids and Graviton 4 (wide OoO + strong HW streamers already overlap the miss; on GV4 keeping it costs up to +10.8% warm at n=2048, `gv4_runs/ab_summary.txt`). The shipped Pi 5 kernel keeps it on the strength of a "10–25% cold win" that no archived A/B supports: the Graviton kernel is the Pi 5 kernel minus that prefetch, and in the archived Pi 5 main bench it is faster cold at 13 of 14 sizes from n=128 up (corrections §5). Structurally the prefetch address depends on the just-updated `base`, so it issues at the same dependency depth as the loads it is meant to hide. Skylake-SP keeps it too; the stated rationale (the AVX-512 frequency license downclocking the scalar loop) was wrong — 512-bit integer compares trip license L1, not L2, and the gated build executes no zmm instruction at all. One `simd_quad_intel.c` gated on `__AVX512VBMI2__` (Ice Lake-SP or newer; note `-march=x86-64-v4` does not set it, use `-march=icelake-server` or `-march=sapphirerapids`) handles the polarity. Removing the Pi 5 prefetch is an open kernel change that needs its own all-sizes A/B.

## One surprise: Shar beats the outer spine hot, and loses to it cold

Extending beyond `simd_quad` itself, the outer `keys[]` layer is where the biggest remaining *hot* win lives. `bench_twolevel.cpp` tests ten variants (A–I plus Lemire's reference); this page covers the six crossed over (outer ∈ {bsearch, outer-spine, Shar branchless}) × (inner ∈ {general-n spine, compile-time n=4096}). A `K=512` outer key array is only 16 lines on 64-B-line hosts, 8 lines on 128-B-line Apple silicon, too short for any stride prefetcher to materially help. Leonard Shar's 1971 branchless step-halving binary search (`bit_floor(len)` + cmov chain, rediscovered recently by probablydance) replaces the branchy descent with a nine-deep serial load → compare → csel chain: no branch mispredicts and no side structure, but also nothing the core can speculate past (corrections §5).

Pre-measurement prediction: Shar would lose to the outer spine on Intel, because the spine's sequential multi-line access plays to LLC streamers. Measurement on all six hosts (paired per-run deltas, 5 runs per host, `{host}_runs/twolevel_paired.txt`; table from corrections §2.2; negative = F faster): Shar + compile-time n=4096 inner (variant F) beats outer-spine + compile-time n=4096 inner (variant D) while the outer keys are hot, and loses to it cold on four hosts:

| host | hot_bat | hot_ser | cold_bat | cold_ser |
|---|---|---|---|---|
| Pi 5 | −6.3% (4/5) | −6.4% (4/5) | **+31.8%** (0/5, D wins) | −0.4% tie |
| M4 Max | −39.1% (5/5) | −53.9% (5/5) | −11.5% (4/5) | **+16.2%** (1/5, D wins) |
| M1 Pro | −32.4% (5/5) | −38.9% (5/5) | −10.6% (5/5) | +5.7% tie |
| Skylake-SP | −14.4% (5/5) | −16.3% (4/5) | **+6.6%** (1/5, D wins) | **+16.9%** (0/5, D wins) |
| Emerald Rapids | −29.5% (5/5) | −37.1% (5/5) | −4.0% (5/5) | **+17.7%** (0/5, D wins) |
| Graviton 4 | −41.9% (5/5) | −43.4% (5/5) | −11.3% (5/5) | +1.2% tie |

Best variant per mode by paired per-run rank (corrections §2.1): hot, F or a tie with F on every host, except GV4 hot_bat (I −10.8%, 5/5) and M1 Pro hot_ser (I −10.9%, 4/5), both measured with the pre-fix Eytzinger prefetch (corrections §1) and pending re-measurement; cold, usually C or D — C wins both cold modes on EMR (5/5, 4/5) and GV4 (5/5, 5/5), D wins cold_bat 5/5 on the Pi 5 and cold_ser 5/5 on SKX. The Pi 5 re-run with the repaired harness (10 runs, `pi5_runs/twolevel_paired_v2.txt`, corrections §6) makes D the Pi 5 ship: F vs D +2.7% / +2.0% hot (ties) and +44.7% cold_bat (F faster 0/10).

Ship recommendation: **variant F (Shar outer + compile-time n=4096 inner) for cache-hot outer keys on M4 Max, M1 Pro, Skylake-SP, Emerald Rapids and Graviton 4; variant D on the Pi 5; when the outer keys are cold, D on the Pi 5 and Skylake-SP (on Skylake-SP cold_bat the bsearch outer C ranks first, with D 4/5 over F) and C on Emerald Rapids / Graviton 4.** On M4 Max and M1 Pro F still wins cold_bat (−11.5% 4/5 and −10.6% 5/5 vs D) and D is only a cold_ser alternate on M4 Max (+16.2%, D faster 4/5) — a tie on M1 Pro (+5.7%); shipping D for cold on the Apple hosts would give back that cold_bat win (corrections §2.1–2.2). The outer-spine variant stays on the shipping surface. (An earlier version of this page gave F-vs-D cold deltas of −23% to −67% and recommended dropping D; those numbers came from the retired two-mode harness and are retracted, corrections §3.)

## One open puzzle: the M-host cold regression

`simd_quad_m4_spine_4096` is the compile-time n=4096 specialization of the M-host spine path (now the hybrid; the straight unroll is retired). In `bench_table.txt` (5-run medians) it is faster warm than the general-n `simd_quad_m4_spine` (M4 Max 4.30 → 3.71 ns, M1 Pro 6.30 → 6.05 ns) and much slower cold (M4 Max 6.50 → 21.94 ns, M1 Pro 11.10 → 32.12 ns). The same shape on two Apple cores with zero code change looked structural, and the earlier hypothesis was that gap=64 on a 128-B-line host compresses the n=4096 spine to one cache line, giving the HW stream prefetcher nothing to latch onto while the straight-line descent issues all tier probes before the block load.

The 2026-10 review offers a simpler explanation that must be tested first: a measurement-order artifact in `bench.cpp`. The general-n spine kernel's cold pass runs right after the non-spine kernel's cold pass with identical targets, so its block line is an L2 hit on Apple's large L2, whereas the dedicated `4096*` row runs after its own 32 MB warm sweep and fetches the line from SLC/DRAM; the gap matches L2-hit vs SLC-hit latencies and the same asymmetry reproduces on the Pi 5 (corrections §5). Decisive test on an Apple host: flush before both passes, or run both in the same order. The OpenEvolve remediation run started from the retired unroll, not the shipped hybrid.

Ship recommendation on Apple silicon until that test is run: the specialization for warm-heavy narrow-API callers, `simd_quad_m4_spine` for first-touch.

## Methodology notes worth stating

**Measurement.** Warm reps = 5000. `bench.cpp`'s "cold" column is *not* flushed: it walks the arrays in allocation order with the targets the previous kernel just used, and the ~35 MB footprint fits every LLC except the Pi 5's (corrections §5), so it is a within-host comparison. The two-level harness flushes the LLC before every cold cell (`thrash_llc()`, now 512 MB) and its hot modes keep only the 1 KB outer hot. Per-cell medians of 5 runs are reported as *levels* only; comparisons use paired per-run deltas (`compute_twolevel_paired.py`), because whole runs drift 1.4–2.2× on the Pi 5 (`ondemand` governor; two-level F hot_bat 214–375 ns across 5 runs) and up to 1.5× on M4 Max, so medians of different variants can come from different runs. The Pi 5 main bench is bimodal too (n=4096 hybrid warm per run 15.91–23.88 ns, `pi5_runs/hybrid_summary.txt`). Emerald Rapids and Graviton 4 are bare-metal; Skylake-SP is a shared-tenant m5.

**Cache alignment, not aliasing, is the open layout issue.** An earlier version of this page described super-linear "sawtooth" steps in the cold curves at n=1024/2048/4096 and attributed them to set aliasing; the 22-size curves that argument rested on have no archived source for five of the six hosts and are treated as unmeasured (corrections §4). What is measured: arrays and spines are `std::vector` allocations (16-byte aligned), so most 64-byte blocks and nearly all 128-byte blocks straddle two cache lines, and interleaved aligned-vs-misaligned A/Bs on the Pi 5 show a +14–30% cold penalty at n=4096 (corrections §5). A Roaring integration must align container arrays and spines to get the designed one-block-one-line behaviour; `aliasing_investigation.md`'s premise that the allocator returns power-of-two-aligned blocks is false for glibc at these sizes.

**Compile-time vs runtime n.** The compile-time n=4096 specializations (`*_spine_4096`, the hybrid; the straight unroll is retired) are intended for narrow-API callers that know their container is maximally sized. Measurements are reported as a separate A/B pair next to the general-n spine on each host; they are not the default ship path, with the exception that variants D and F (the shipping two-level paths) compose with them on the inner layer. On Skylake-SP the hybrid is −32% warm (5/5) but +40% slower cold than general-n at the median (hybrid faster in only 2 of 5 runs; per-run −12% to +62%, `skx_runs/hybrid_run*.txt` `4096*` rows; corrections §2.3), so it is warm-API only there as well.

## Open items beyond what is reported above

1. Test the Apple `*_spine_4096` measurement-order hypothesis (flush before both passes); only then decide whether the cold regression is structural.
2. Re-measure the two-level harness on M4 Max, M1 Pro, Skylake-SP, Emerald Rapids and Graviton 4 with the repaired harness (`./run_twolevel.sh HOST 10`, then `compute_twolevel_paired.py`); every H/I number on those hosts predates the 2026-10-11 prefetch fix (corrections §1, §6).
3. A/B removing the Pi 5 in-loop prefetch at all sizes; the archived evidence says remove it.
4. Cache-line-align `carr` and the spines in the harnesses and kernels; add a real flush to `bench.cpp`'s cold column.
5. Close the small-container gap to Lemire's variant: F loses to it on M4 Max at n=48–62 and 81–124 (hot_bat) and n=1–7 and 64–95 (cold_ser), 5/5 (`m4_runs/sweep_fvl_summary.txt`, corrections §2.3); a size-dependent dispatch or a shorter scalar tail for n < 128.

Closed since the first draft of this page: a Shar-style inner for n=4096 (variant G) is structurally bad on every host (F faster in 117 of 120 run-cells — every hot run-cell; G faster only in two Pi 5 and one Skylake cold_bat runs — `{host}_runs/twolevel_paired.txt`, G vs F rows); Graviton 4 and Emerald Rapids were confirmed bare-metal, so tenancy is not a confound there; the `RoaringSet::contains` integration is downstream work, out of scope for this study.

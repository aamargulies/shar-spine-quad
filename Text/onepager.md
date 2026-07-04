# SIMD Quad across six hosts, one shippable recommendation

**Context.** Extension of Daniel Lemire's `simd_quad` membership test for sorted `uint16_t[]` Roaring containers (up to 4096 elements), ported and tuned across six CPU microarchitectures. Six per-host variants of the inner, plus a two-level composition that also touches the outer `keys[]` layer Lemire's post treats as settled. Measurements are per-cell medians of 5 `./bench 4000 5000` runs per host; raw outputs archived per host under `{pi5,m4,m1,skx,emr,gv4}_runs/`.

## Hosts

| | Pi 5 (A76) | M4 Max | M1 Pro | Skylake-SP 8175M | Emerald Rapids 8559C | Graviton 4 (V2) |
|---|---|---|---|---|---|---|
| line | 64 B | 128 B | 128 B | 64 B | 64 B | 64 B |
| SIMD | 128b NEON | 128b NEON | 128b NEON | AVX-512 (AVX2 used) | AVX-512 (zmm) | 128b NEON |
| L1D | 64 KB | 128 KB | 128 KB | 32 KB | 48 KB | 64 KB |
| load AGUs | 2 | 3 | 3 | 2 | 3 | 4 |
| gap | 32 | 64 | 64 | 32 | 32 | 32 |
| spec prefetch | kept | dropped | dropped | kept | dropped | dropped |

Apple M1 Pro and M4 Max share `simd_quad_m4.c` without modification: both are 128-B-line, 128b-NEON, wide-OoO Apple-silicon P-cores. The M1 port is a zero-line-change ship.

## Three things that replicated across the board

**The spine is the single biggest inner-layer optimization on every host.** Pack the interpolation probe keys into a dense contiguous region so the cold-cache pointer chase streams through consecutive cache lines. Pi 5 cold at n=4096 is roughly halved, M4 cold roughly thirded, Intel/GV4 similar. L1/L2 stride prefetchers love the sequential-read pattern.

**gap tracks cache line, not SIMD width.** Even on 512-bit Intel, gap=32 is right because the line is 64 B; a 64-element block would span two lines. A scratch `gap64` variant on Emerald Rapids was uniformly faster cold but alternated sign warm, winning 46-55% at n=256/1024/4096 and losing 45-67% at n=512/2048. n=512 and n=2048 are common Roaring container sizes, which is fatal for a shipping default.

**Speculative `__builtin_prefetch` inside the interpolation loop is microarchitecture-dependent.** Helpful on A76 (narrow OoO, 2 AGUs, limited MLP, 10-25% cold win). Wasted issue slots on M4, Emerald Rapids, Graviton 4 (wide OoO + strong HW streamers already overlap the miss). Kept on Skylake-SP because the AVX-512 frequency license downclocks the scalar loop enough that we don't have the issue-slot budget to spare. One `simd_quad_intel.c` gated on `__AVX512VBMI2__` (the proxy for "Ice Lake-SP or newer, where the freq penalty went away") handles the polarity.

## One surprise: Shar beats the outer spine on every host

Extending beyond `simd_quad` itself, the outer `keys[]` layer is where the biggest remaining win lives. `bench_twolevel.cpp` tests six variants crossed over (outer ∈ {bsearch, outer-spine, Shar branchless}) × (inner ∈ {general-n spine, compile-time n=4096}). A `K=512` outer key array is only 16 lines on 64-B-line hosts, 8 lines on 128-B-line Apple silicon, too short for any stride prefetcher to materially help. Leonard Shar's 1971 branchless step-halving binary search (`bit_floor(len)` + cmov chain, rediscovered recently by probablydance) turns the descent into ~9 independent loads that any wide-issue core with enough AGUs can pipeline.

Pre-measurement prediction: Shar would lose to the outer spine on Intel, because the spine's sequential multi-line access plays to LLC streamers. Measurement on all six hosts: Shar + compile-time n=4096 inner (variant F) is the winner, beating outer-spine + compile-time n=4096 inner (variant D) by:

| host | F vs D warm | F vs D cold |
|---|---|---|
| Pi 5 | +7% (noise) | -61% |
| M4 Max | -36% | -63% |
| M1 Pro | -30% | -67% |
| Skylake-SP | -10% | -23% |
| Emerald Rapids | -21% | -40% |
| Graviton 4 | -41% | -54% |

One ship recommendation across all six hosts: **variant F, Shar outer + compile-time n=4096 inner.** The outer-spine variant can be dropped from the shipping surface entirely; no host prefers it.

## One open puzzle: the M-host cold regression

`simd_quad_m4_spine_4096` is the compile-time n=4096 unroll of the M-host spine path. Warm on M4 Max it is ~16% faster than the general-n `simd_quad_m4_spine` (3.65 vs 4.34 ns). Cold it is ~188% SLOWER (18.65 vs 6.47 ns). Stable across 5 runs on AC power. Reproduces almost identically on M1 Pro at +194% (11.1 vs 32.7 ns) on independent hardware with a different execution engine, so the mechanism is structural, not an M4-specific quirk.

Our hypothesis: gap=64 on a 128-B-line host compresses the n=4096 spine to exactly one cache line, which gives the HW stream prefetcher nothing to latch onto; the straight-line unroll then issues all three tier probes in a single basic block before the block load, denying the wide OoO window the ability to overlap the block-load miss with tier misses. On 64-B-line hosts the spine is 4 lines so the streamer engages during the descent; `simd_quad_intel_spine_4096` on Emerald Rapids shows a clean 30% cold *improvement* from the same unroll, consistent with that mechanism.

Ship recommendation on Apple silicon: the specialization for warm-heavy narrow-API callers, `simd_quad_m4_spine` for first-touch. An OpenEvolve run is currently attempting in-function remediation (speculative `__builtin_prefetch` after tier 1, hoisted block load, alternative descent shapes) on the M4 host, to either surface a fix or confirm the pareto frontier is already tight.

## Methodology notes worth stating

**Measurement.** Warm reps = 5000, cold = first-touch with a cache flush between calls. Per-cell medians of 5 full `./bench 4000 5000` runs per host. Warm medians are stable to 1-10% across runs on every host; cold at large n swings 5-25%, with the Pi 5 and shared-tenant EC2 hosts (Skylake-SP on m5, Graviton 4 on r8g) noisier than bare-metal bare-bones.

**Cache aliasing is visible in the per-n curves and expected.** Working sets that are power-of-two multiples of (L1 ways × line size) map onto few sets, producing the characteristic super-linear steps in cold curves at n=1024/2048/4096 on 64-B-line hosts. We see it; we do not smooth it; ship decisions are keyed to realistic Roaring container sizes, not to the aliasing-prone sweep points. See `aliasing_investigation.md` for a per-host accounting.

**Compile-time vs runtime n.** The compile-time n=4096 specializations (`*_spine_4096`) are intended for narrow-API callers that know their container is maximally sized. Measurements are reported as a separate A/B pair next to the general-n spine on each host; they are not the default ship path, with the exception that variant F (the shipping two-level path) composes with them on the inner layer.

## Open items beyond what is reported above

1. Investigate and attempt to remediate the M-host `*_spine_4096` cold regression.
2. Promote variant F into a real `RoaringSet::contains` API backed by a per-container spine kept in sync with insertions/removals.
3. Re-measure Graviton 4 at bare metal. r8g shared tenancy is stable within 1-15% but is a confound at large-n cold.
4. Consider a Shar-style inner for n=4096. n=4096 is 64 lines so streamers have room, different shape than the outer, prediction unclear.

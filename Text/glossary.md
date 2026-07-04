# Glossary: cache and microarchitecture terms

Definitions for the jargon used across the project's writeups, benchmarks, and the aliasing investigation. Scoped to what actually shows up in this repo; each term includes a concrete reference to one of the six hosts where it matters.

## Cache structure

### Cache line
The unit the cache moves as a whole. A load pulls in an entire line even if only one byte is read. All six hosts use either 64-byte lines (Pi 5, Skylake-SP, Emerald Rapids, Graviton 4) or 128-byte lines (M4 P-core, M1 P-core). Line size drives the `gap` choice: gap=32 covers one 64-B line with u16 elements; gap=64 covers one 128-B line. A variant written for one line size is rarely optimal on another.

### Set
A row of the cache. An address's set is determined by a slice of its bits (the set index), so every address has exactly one set it can live in. A cache with `S` sets and `L`-byte lines and `W` ways holds `S * W * L` bytes total.

### Way
A column of the cache, i.e. one of the slots within a set. A set with `W` ways can hold `W` distinct cache lines simultaneously, each with a different tag but the same set index.

### Associativity (`W`)
How many ways each set has: the number of different lines that can share the same set at the same time. Three regimes:

- **Direct-mapped** (`W = 1`): one slot per set. Any two addresses mapping to the same set evict each other on every access.
- **Fully associative** (`W` = total lines): a line can live anywhere. No conflict misses, but every lookup compares against every tag, only practical for tiny caches.
- **Set-associative** (typical): a compromise with `W` in the range 4 to 16 on real L1/L2 caches. Pi 5 and Graviton 4 have 4-way L1Ds; M4 / M1 / Skylake-SP have 8-way; Emerald Rapids has 12-way. Higher `W` tolerates more colliding lines per set before the hardware has to evict one. This is why EMR's cold curve is the smoothest of the six hosts.

### Tag
The portion of an address bits stored alongside each cached line to identify *which* address currently occupies that slot. On a lookup, the hardware uses the set index to pick a set, then compares the incoming address's tag against all `W` stored tags in parallel; a match is a hit.

### Set index
The middle bit-slice of an address that selects which set the line belongs to. With `S` sets, the set index is `log2(S)` bits wide, just above the block-offset bits.

### Block offset
The low bits of an address that select which byte inside a cache line is being accessed. With `L`-byte lines, the block offset is `log2(L)` bits wide.

### Way size
The stride at which set-index bits repeat: `way_size = S * L = cache_size / W`. Two addresses separated by a multiple of the way size map to the same set. Not to be confused with associativity: way size is about *where* collisions happen; associativity is about *how many* collisions the set tolerates before evicting. For the hosts in this project, L1D way sizes are 16 KB on Pi 5 / M4 / M1 / Graviton 4, 4 KB on Skylake-SP and Emerald Rapids.

### Cache aliasing
Two addresses with different tags but the same set index. They *could* coexist (up to `W` of them in the same set), but once more than `W` aliasing addresses are hot at once, they start evicting each other: this is a "conflict miss". The aliasing investigation in this repo distinguishes two flavors:

- **Per-array aliasing**: a single array large enough that its own lines start colliding with each other. Requires array size >= way size and a stride pattern that exercises the aliasing. In this bench, per-array aliasing is only reachable at all on Skylake-SP and Emerald Rapids (n=2048 and n=4096 hit the 4 KB L1 way size), and the per-query footprint is too small to actually trigger it.
- **Allocation aliasing**: many separately-allocated arrays (one per container) whose base addresses happen to share bits because the allocator hands out power-of-two-aligned chunks. Consecutive containers then collide in the same sets. This is the mechanism behind the visible bumps in the cold curves.

### Cache hierarchy (L1D / L2 / LLC / DRAM)
Levels of cache in decreasing speed and increasing capacity. L1D is the fastest data cache, per-core, typically tens of KB. L2 is larger (hundreds of KB to a few MB), still per-core on Intel and ARM server parts, shared on Apple silicon. LLC (last-level cache, sometimes called L3) is the biggest on-die cache, shared across cores. DRAM is main memory, orders of magnitude slower. The cold curves in this project are dominated by L1->L2 and L2->DRAM boundary crossings.

## Cache behavior

### Warm cache
The access pattern has already been run once so the relevant lines are resident. The warm benchmark measures steady-state lookup cost with everything hot. Numbers are small (single-digit to low-double-digit ns/query at n=4096).

### Cold cache
The access pattern runs fresh with the relevant lines not resident. The cold benchmark deliberately flushes or churns the working set between queries to force real miss latency on the critical path. Numbers can be 5x to 20x the warm case at large n; Pi 5 shows the widest cold/warm ratio (roughly 10x at n=4096) because its memory hierarchy is the shallowest.

### Cold/warm ratio
Useful cross-host signal: how much absolute latency the cache hierarchy is buying back vs DRAM. Pi 5 cold/warm at n=4096 is roughly 10x, M4 is roughly 2.5x, server uarchs (SKX, EMR, GV4) fall between. The spine optimization collapses most of this ratio because it makes the descent hit a small hot metadata array instead of the full sorted array.

## Prefetch and memory parallelism

### Hardware prefetcher / streamer
A fixed-function unit that watches the memory access stream and predicts future addresses, issuing loads ahead of time to hide DRAM latency. Stride prefetchers (all six hosts) detect regular strides; next-line prefetchers are a degenerate case. The spine optimization works partly because the 3-tier quaternary descent produces a sequential scan that streamers recognize. On M4 with gap=64, the spine collapses to 1 cache line at n=4096, which is too short for the streamer to engage, which is part of the `simd_quad_m4_spine_4096` cold regression.

### Software prefetch / speculative prefetch
An instruction (`__builtin_prefetch` on GCC/Clang, `_mm_prefetch` on Intel intrinsics) that asks the hardware to start pulling a line into cache speculatively. Valuable on narrow out-of-order cores that can't overlap misses themselves (Pi 5 keeps it, +10-25% cold win). Useless to harmful on wide out-of-order cores with good streamers (M4, EMR, GV4 all drop it; GV4 sees +10.8% warm slowdown when kept).

### Memory-level parallelism (MLP)
The number of outstanding cache misses the core can have in flight at once. Bounded by the miss-status handling registers (MSHRs) and the load-store queue. High MLP lets the core overlap the latency of one miss with the work of another; low MLP serializes misses. This is why A76 (narrow OoO, 2 load AGUs) benefits from software prefetch and wide-OoO cores (M4, EMR, GV4) don't: the wide cores already achieve full MLP on the dependent-load descent.

### Load AGU (address generation unit)
A functional unit that computes the address for a load instruction. The number of load AGUs caps how many loads can issue per cycle: Pi 5 has 2, Skylake-SP has 2, Emerald Rapids has 3, M4/M1 have 3, Graviton 4 has 4. More AGUs makes it easier to issue independent loads in parallel, which is why Shar's branchless binary search (roughly 9 independent loads on the critical path) dominates the outer-spine pointer chase on all four of the 3-or-more-AGU hosts.

### Out-of-order (OoO) execution
The core buffers instructions in a reorder window and issues them as their dependencies become available, not in program order. The size of that window and the number of execution ports determines how much latency can be hidden. "Narrow OoO" here means A76 (Pi 5); "wide OoO" means M4, M1, Skylake-SP, Emerald Rapids, Graviton 4. The distinction drives most of the per-host tuning in this project.

### Dependent load
A load whose address depends on a previous load's result (e.g. pointer chasing through a spine). Dependent loads serialize on load-use latency: each miss has to complete before the next address can be computed. The outer-spine variant in `bench_twolevel.cpp` is a 3-tier dependent-load chain; that's why Shar's independent-load cmov chain beats it on every host with the MLP to exploit it.

## SIMD and instruction-set terms

### NEON
The ARM 128-bit SIMD instruction set used by all four ARM hosts (Pi 5, M4, M1, Graviton 4). `vld1q_u16` loads 8 u16 elements; `vld1q_u16_x2`/`_x4` are 2x/4x structured loads; `vceqq_u16` compares lanes for equality; `vorrq_u16` ORs two vectors; `vmaxvq_u16` reduces a vector to its scalar max (used as the "any lane matched" test).

### SVE / SVE2
ARM's scalable vector extension, vector-length-agnostic SIMD. Present on Graviton 4 (Neoverse V2), but V2's SVE2 vector length is 128 bits (same as NEON), so it buys no width advantage for u16 search. The GV4 variant stays on NEON.

### AVX2 / AVX-512 / VBMI2
Intel's 256-bit and 512-bit SIMD families. `simd_quad_intel.c` has three paths: a 512-bit zmm block check (single compare via `vpcmpw` + kortest), a 2x 256-bit AVX2 fallback, and scalar. The zmm path is gated on `__AVX512VBMI2__` (Ice Lake-SP and newer), not `__AVX512BW__`, because Skylake-SP has BW without VBMI2 and any zmm load on SKX trips the AVX-512 frequency license.

### AVX-512 frequency license
A behavior on Skylake-SP (and some later parts) where executing 512-bit SIMD instructions forces the core to downclock for a stabilization window. On SKX the penalty is large enough that the scalar interpolation loop surrounding the zmm block check runs slower than the SSE2 reference at large n, even with the SIMD speedup on the block check itself. VBMI2 landed as part of Ice Lake-SP, which is also roughly where the frequency penalty went away, so VBMI2-availability is the proxy this project uses for "zmm is cheap to issue".

## Algorithmic structures

### Spine
A small auxiliary array that holds pivot elements at a fixed stride through the main sorted array. The 3-iter quaternary descent reads from the spine, narrowing the range, then a single block-check inside the main array finishes the search. At n=4096 the spine is 4 cache lines on 64-B-line hosts (Pi 5 / SKX / EMR / GV4) and 1 cache line on 128-B-line hosts (M4 / M1). The single biggest per-host optimization in the project: cold n=4096 wins are roughly 2x on Pi 5, 3x on M4, similar on Intel and GV4.

### Gap
The stride between consecutive "block check" points on the main array during the quaternary descent. Chosen to cover one cache line with u16 elements: gap=32 on 64-B-line hosts, gap=64 on 128-B-line hosts. Tracks cache line, not SIMD width: even with 512-bit registers, Intel's right gap is 32 because the line is 64 B.

### Block check
The innermost test: load one or two cache lines' worth of u16 elements and compare each lane to the target. On ARM hosts this is `vld1q_u16_x2` or `vld1q_u16_x4` plus `vceqq_u16` plus `vorrq_u16` plus `vmaxvq_u16`. On Intel it's a single zmm compare (VBMI2 path) or 2x ymm compares plus movemask (AVX2 path).

### Shar (branchless binary search)
Leonard Shar 1971, rediscovered by Malte Skarupke in 2023. A single-pointer cmov-chain step-halving binary search with `bit_floor(len)` plus a `len - step` offset to handle non-power-of-two lengths. On K=512 outer keys it's roughly 9 independent loads on the critical path, all branch-free. Wins on every host with enough MLP to issue them back-to-back (all five benchmarked). Variant F in `bench_twolevel.cpp` is Shar outer plus compile-time n=4096 inner and is the ship recommendation across the board.

### Two-level spine
Outer level across container keys (K=512 in `bench_twolevel.cpp`) plus inner level inside each container (n=4096). Variants A-F cross outer strategy (bsearch / outer-spine / Shar) with inner strategy (general-n / compile-time n=4096). Prediction that "Intel streamers should love the outer spine" was refuted on both SKX and EMR: the K=512 outer key spine is only 1 KB, too short for any stride prefetcher to engage on, so its dependent-load chain is pure critical-path cost and Shar's independent loads beat it everywhere.

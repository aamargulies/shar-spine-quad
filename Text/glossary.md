# Glossary: cache and microarchitecture terms

Definitions for the jargon used across the project's writeups, benchmarks, and the aliasing investigation. Scoped to what actually shows up in this repo; each term includes a concrete reference to one of the six hosts where it matters.

*Corrected 2026-10-11 against Text/corrections_2026-10.md; earlier numbers were retracted, see that file.*

## Cache structure

### Cache line
The unit the cache moves as a whole. A load pulls in an entire line even if only one byte is read. All six hosts use either 64-byte lines (Pi 5, Skylake-SP, Emerald Rapids, Graviton 4) or 128-byte lines (M4 P-core, M1 P-core). Line size drives the `gap` choice: gap=32 covers one 64-B line with u16 elements; gap=64 covers one 128-B line — provided the array is line-aligned. The benchmarks never enforce that: arrays and spines are `std::vector` allocations (16-B aligned), so about 75% of 64-B blocks and 87.5% of 128-B blocks straddle two lines, and interleaved aligned-vs-misaligned A/Bs on the Pi 5 measured a +14–30% cold penalty at n=4096 (corrections section 5). A variant written for one line size is rarely optimal on another.

### Set
A row of the cache. An address's set is determined by a slice of its bits (the set index), so every address has exactly one set it can live in. A cache with `S` sets and `L`-byte lines and `W` ways holds `S * W * L` bytes total.

### Way
A column of the cache, i.e. one of the slots within a set. A set with `W` ways can hold `W` distinct cache lines simultaneously, each with a different tag but the same set index.

### Associativity (`W`)
How many ways each set has: the number of different lines that can share the same set at the same time. Three regimes:

- **Direct-mapped** (`W = 1`): one slot per set. Any two addresses mapping to the same set evict each other on every access.
- **Fully associative** (`W` = total lines): a line can live anywhere. No conflict misses, but every lookup compares against every tag, only practical for tiny caches.
- **Set-associative** (typical): a compromise with `W` in the range 4 to 16 on real L1/L2 caches. Pi 5 and Graviton 4 have 4-way L1Ds; M4 / M1 / Skylake-SP have 8-way; Emerald Rapids has 12-way. Higher `W` tolerates more colliding lines per set before the hardware has to evict one. (An earlier version of this entry credited EMR's associativity for "the smoothest cold curve of the six hosts"; the archived EMR runs hold only the ten power-of-two sizes, so the curve shape that claim rested on has no raw source — corrections section 4.)

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
- **Allocation aliasing**: many separately-allocated arrays (one per container) whose base addresses happen to share bits. The aliasing investigation assumed the allocator hands out power-of-two-aligned chunks and offered this as the mechanism behind bumps in the cold curves; both halves are withdrawn. For glibc at these sizes the premise is false (`std::vector` buffers are 16-B aligned), and the bumps sat on non-power-of-two sizes that have no archived source and should be treated as unmeasured (corrections sections 4 and 5).

### Cache hierarchy (L1D / L2 / LLC / DRAM)
Levels of cache in decreasing speed and increasing capacity. L1D is the fastest data cache, per-core, typically tens of KB. L2 is larger (hundreds of KB to a few MB), still per-core on Intel and ARM server parts, shared on Apple silicon. LLC (last-level cache, sometimes called L3) is the biggest on-die cache, shared across cores. DRAM is main memory, orders of magnitude slower. The cold curves in this project are dominated by L1->L2 and L2->DRAM boundary crossings.

## Cache behavior

### Warm cache
The access pattern has already been run once so the relevant lines are resident. The warm benchmark measures steady-state lookup cost with everything hot. Numbers are small (single-digit to low-double-digit ns/query at n=4096).

### Cold cache
The access pattern runs fresh with the relevant lines not resident. `bench_twolevel`'s cold modes arrange this with a `thrash_llc()` sweep (512 MB) before each cold cell, and since 2026-10-11 `bench.cpp` does the same before every cold pass. Every archived main-bench run predates that: there `bench.cpp`'s "cold" column had **no cache flush**: it walked the arrays in allocation order with the same targets the previous algorithm had just used, and its ~35 MB footprint fits the last-level cache of every host except the Pi 5 (and at n ≤ 256 is L2/L3-resident on the Pi 5 too). So in the archived main bench "cold" is a DRAM miss on the Pi 5 and an L2 / L3 / SLC hit on every other host — SKX included, alongside Apple silicon, EMR and GV4 — and cross-host "cold" comparisons from it compare cache levels, not cores (corrections section 5). At n=4096 the shipped spine kernels' cold cells run 1.5x (M4 Max, 6.5 vs 4.3 ns) to 6.7x (Pi 5, 150.7 vs 22.5 ns) their warm cells (`bench_table.txt`, 5-run medians).

### Cold/warm ratio
For the non-spine kernels at n=4096 in `bench_table.txt` (5-run medians, cold/warm): Pi 5 299.0/30.1 ≈ 9.9x, SKX 180.9/31.6 ≈ 5.7x, EMR 64.9/19.5 ≈ 3.3x, GV4 65.0/20.0 ≈ 3.3x, M4 Max 16.8/5.0 ≈ 3.4x. Because the main bench's cold column was unflushed when these were taken (see Cold cache), this ratio mostly records whether the ~35 MB footprint fits the host's last-level cache, not how well the core hides DRAM latency; it is not a clean cross-host signal. Within a host the spine does collapse it — on the Pi 5 from 9.9x to 6.7x (150.7/22.5) — because the descent reads a small contiguous key array instead of scattered lines of the full sorted array.

## Prefetch and memory parallelism

### Hardware prefetcher / streamer
A fixed-function unit that watches the memory access stream and predicts future addresses, issuing loads ahead of time to hide DRAM latency. Stride prefetchers (all six hosts) detect regular strides; next-line prefetchers are a degenerate case. Earlier write-ups credited the spine's win to "a sequential scan that streamers recognize" and blamed the `simd_quad_m4_spine_4096` cold regression on a 1-line spine being "too short for the streamer to engage". Neither is supported: a 256-B spine is a four-line region whose probes are data-dependent, and the project's own 2026-05-14 decomposition found the spine tiers are L1 hits (the one up-front software prefetch covers them) with the floor being the demand block load. The spine's benefit is better described as fewer, contiguous lines whose misses can be in flight together (see MLP). The Apple regression itself may be a measurement-order artifact of `bench.cpp` (corrections section 5; hypothesis pending a flushed test).

### Software prefetch / speculative prefetch
An instruction (`__builtin_prefetch` on GCC/Clang, `_mm_prefetch` on Intel intrinsics) that asks the hardware to start pulling a line into cache speculatively. The shipped Pi 5 kernel keeps one in its quaternary loop on the strength of an early "~10–25% cold win" that no archived A/B supports; the archived main-bench table is a built-in A/B (`simd_quad_graviton.c` is the Pi 5 kernel minus the prefetch) and shows the prefetch kernel slower cold at 13 of 14 sizes from n=128 up (+2% to +31%) and slower warm at 13 of 14 (`pi5_runs/rebench_run*.txt`; corrections section 5). Structurally the prefetch address depends on the just-updated `base`, so it issues at the same dependency depth as the loads it is meant to hide. M4, EMR and GV4 drop it; GV4's A/B shows the non-spine kernel +10.8% warm at n=2048 and +5.6% cold at n=256 when kept (`gv4_runs/ab_summary.txt`, 5-run medians). SKX keeps it only because its A/B was inconclusive.

### Memory-level parallelism (MLP)
The number of outstanding cache misses the core can have in flight at once. Bounded by the miss-status handling registers (MSHRs) and the load-store queue. High MLP lets the core overlap the latency of one miss with the work of another; low MLP serializes misses. The project's early reading was that the narrow A76 (2 load AGUs) would benefit from software prefetch while wide-OoO cores (M4, EMR, GV4) would not; the archived data say the in-loop prefetch loses on the A76 as well (see Software prefetch), so MLP budget does not predict that decision. Where MLP does show up is in the spine: packing the probe keys into a few contiguous lines lets their misses overlap instead of serializing through scattered lines of the sorted array.

### Load AGU (address generation unit)
A functional unit that computes the address for a load instruction. The number of load AGUs caps how many loads can issue per cycle: Pi 5 has 2, Skylake-SP has 2, Emerald Rapids has 3, M4/M1 have 3; the review puts Graviton 4's Neoverse V2 at three load pipes rather than the four quoted earlier (not verified on hardware here; corrections section 5). More AGUs make it easier to issue *independent* loads in parallel — the three probes within one quaternary iteration, for instance. It does not explain Shar's hot win: that loop is a serial cmov chain, not an independent-load pattern (see Shar).

### Out-of-order (OoO) execution
The core buffers instructions in a reorder window and issues them as their dependencies become available, not in program order. The size of that window and the number of execution ports determines how much latency can be hidden. "Narrow OoO" here means the Cortex-A76 (Pi 5) and Skylake-SP (2 load AGUs) — the same grouping CLAUDE.md, KhuongMorin.md and `simd_quad_intel.c` use; an earlier version of this entry put Skylake-SP on the wide side. "Wide OoO" means M4, M1, Emerald Rapids, Graviton 4. The distinction was the project's main explanatory axis, but note that after the paired re-analysis it predicts less than first thought: the in-loop prefetch loses on the narrow A76 too, and the Eytzinger-prefetch hot_ser win predicted for narrow cores did not materialise on either (corrections sections 2.3 and 6).

### Dependent load
A load whose address depends on a previous load's result (e.g. pointer chasing through a spine). Dependent loads serialize on load-use latency: each miss has to complete before the next address can be computed. The outer-spine variant in `bench_twolevel.cpp` is a 3-tier dependent-load chain. Shar's cmov chain is *also* a dependent chain (each address depends on the previous select); it beats the outer spine hot because it has no branch mispredicts and no side structure, and it loses to the branchy or spine outers cold on most hosts, where each link is a miss it cannot speculate past (corrections sections 2.1 and 5).

## SIMD and instruction-set terms

### NEON
The ARM 128-bit SIMD instruction set used by all four ARM hosts (Pi 5, M4, M1, Graviton 4). `vld1q_u16` loads 8 u16 elements; `vld1q_u16_x2`/`_x4` are 2x/4x structured loads; `vceqq_u16` compares lanes for equality; `vorrq_u16` ORs two vectors; `vmaxvq_u16` reduces a vector to its scalar max (used as the "any lane matched" test).

### SVE / SVE2
ARM's scalable vector extension, vector-length-agnostic SIMD. Present on Graviton 4 (Neoverse V2), but V2's SVE2 vector length is 128 bits (same as NEON), so it buys no width advantage for u16 search. The GV4 variant stays on NEON.

### AVX2 / AVX-512 / VBMI2
Intel's 256-bit and 512-bit SIMD families. `simd_quad_intel.c` has three paths: a 512-bit zmm block check (single compare via `vpcmpw` + kortest), a 2x 256-bit AVX2 fallback, and scalar. The zmm path is gated on `__AVX512VBMI2__` (Ice Lake-SP and newer), not `__AVX512BW__`, because Skylake-SP has BW without VBMI2 and a 512-bit op on SKX trips the AVX-512 frequency license (level L1 for the light integer ops used here). `-march=x86-64-v4` does **not** define `__AVX512VBMI2__` and silently builds the AVX2 + prefetch variant; use `-march=icelake-server` or `-march=sapphirerapids`. Zen 4 and Zen 5 define VBMI2, so the proxy also selects the zmm path on AMD, untested (corrections section 5).

### AVX-512 frequency license
A behavior on Skylake-SP (and some later parts) where executing 512-bit SIMD instructions forces the core to a lower frequency license for a stabilization window: light 512-bit integer ops (loads, compares — what a zmm block check uses) trip level L1, and L2 is reserved for heavy FP/multiply ops (corrections section 5; earlier text here and elsewhere said L2). In the development runs the ungated zmm block check made the non-spine kernel slower than the SSE2 reference at n ≥ 2048 warm on SKX, because the downclock lands on the scalar interpolation loop around it; no archived A/B of that experiment exists. The shipped SKX build is gated to AVX2 and executes no 512-bit instruction, so nothing is downclocked in the measured configuration. VBMI2 landed as part of Ice Lake-SP, which is also roughly where the frequency penalty went away, so VBMI2-availability is the proxy this project uses for "zmm is cheap to issue".

## Algorithmic structures

### Spine
A small auxiliary array that holds pivot elements at a fixed stride through the main sorted array. The 3-iter quaternary descent reads from the spine, narrowing the range, then a single block-check inside the main array finishes the search. At n=4096 the spine is 256 B — 4 cache lines on 64-B-line hosts (Pi 5 / SKX / EMR / GV4) when line-aligned (a 16-B-aligned one usually spans five) — and 128 B, 1 line when aligned, on 128-B-line hosts (M4 / M1). The single biggest per-host optimization in the project. Cold n=4096, non-spine → spine kernel, `bench_table.txt` 5-run medians: Pi 5 299.0 → 150.7 ns (2.0x), M4 Max 16.8 → 6.5 (2.6x), SKX 180.9 → 132.7 (1.4x), EMR 64.9 → 37.2 (1.7x), GV4 65.0 → 34.6 (1.9x) — with the caveat that this column was unflushed when these were taken, so only the Pi 5 figure is a DRAM-miss regime (see Cold cache).

### Gap
The stride between consecutive "block check" points on the main array during the quaternary descent. Chosen to cover one cache line with u16 elements: gap=32 on 64-B-line hosts, gap=64 on 128-B-line hosts (one line only for a line-aligned array; see Cache line). Tracks cache line, not SIMD width: even with 512-bit registers, Intel's right gap is 32 because the line is 64 B.

### Block check
The innermost test: load one or two cache lines' worth of u16 elements and compare each lane to the target. On ARM hosts this is `vld1q_u16_x2` or `vld1q_u16_x4` plus `vceqq_u16` plus `vorrq_u16` plus `vmaxvq_u16`. On Intel it's a single zmm compare (VBMI2 path) or 2x ymm compares plus movemask (AVX2 path).

### Shar (branchless binary search)
Leonard Shar 1971, rediscovered by Malte Skarupke in 2023. A single-pointer cmov-chain step-halving binary search with `bit_floor(len)` plus a `len - step` offset to handle non-power-of-two lengths. On K=512 outer keys it is a 9-step *serial* cmov chain — load → compare → csel → load, each address depending on the previous select — all branch-free; earlier text here called it "9 independent loads in parallel", which is wrong (corrections section 5). It wins hot because it never mispredicts and carries no side structure: variant F (Shar outer + compile-time n=4096 inner) beats D (outer spine, same inner) by −14% to −54% paired on M4 Max, M1 Pro, SKX, EMR and GV4 — in 5/5 runs on hot_bat on all five hosts and on hot_ser on four (SKX 4/5) — and on the Pi 5 is 4/5 at −6% in the archived runs and a tie in the 2026-10 repaired-harness runs (`{host}_runs/twolevel_paired.txt`, `pi5_runs/twolevel_paired_v2.txt`; corrections 2.2–2.3 and 6). It is not the ship recommendation across the board: cold, where each link is a miss it cannot speculate past, C or D is usually best (C 5/5 in both cold modes on EMR and GV4; D cold_bat 5/5 on the Pi 5, cold_ser 5/5 on SKX), and on the Pi 5 the repaired 10-run harness makes D the recommendation outright (corrections section 6).

### Two-level spine
Outer level across container keys (K=512 in `bench_twolevel.cpp`) plus inner level inside each container (n=4096). Variants A–F cross outer strategy (bsearch / outer-spine / Shar) with inner strategy (general-n / compile-time n=4096); G is Shar inner (slower than F in 59 of 60 cells), H/I add an Eytzinger outer with Khuong–Morin prefetch (depth log2(B): 5 levels at gap 32, 6 at gap 64; every H/I number recorded before 2026-10-11 used a mis-aimed prefetch offset and only the Pi 5 has been re-measured — corrections sections 1 and 6), and Lem is Lemire's published variant. Prediction that "Intel streamers should love the outer spine" was refuted on both SKX and EMR: the K=512 outer key spine is only 1 KB, too short for any stride prefetcher to engage on, so hot its dependent-load chain is pure critical-path cost and Shar's cmov chain beats it (F vs D −14.4% SKX, −29.5% EMR hot_bat, 5/5). Cold the picture flips: the branchy bsearch outer (C) is best 5/5 in both cold modes on EMR and GV4, D is cold_ser-best 5/5 on SKX, and F vs Lemire's variant is −35% to −84% hot and −7% to −45% cold at n=4096 — but Lemire's variant is faster than F at several small container sizes on M4 Max (corrections 2.1–2.3).

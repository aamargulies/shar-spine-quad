# Cache aliasing in the benchmark plots, per-host accounting

> **Correction notice (2026-10-11).** This document is a lab note kept as history. A 2026-10-11 review of the repository's measurements found aggregation and harness defects behind several claims below; each affected statement is followed by a `Correction 2026-10-11` note and the original text is left in place. The authoritative list of retractions and replacement numbers is [Text/corrections_2026-10.md](corrections_2026-10.md); where that file and this one disagree, that file wins.

Daniel Lemire flagged visible cache aliasing in the benchmark line plots during initial review and said it was "to be expected." This document spot-checks which bumps in the per-host cold curves align with obvious cache-geometry boundaries, so the answer to "have you checked which bumps are the aliasing ones" is yes.

> Correction 2026-10-11: the "cold curves" examined here are `bench.cpp`'s cold column, which has no cache flush: it walks the arrays in allocation order with the same targets the previous algorithm just used, and the ~35 MB footprint fits the LLC of every host except the Pi 5 (and at n ≤ 256 is L2/L3-resident on the Pi 5 too). The bumps discussed below are therefore LLC/L2-regime effects, not DRAM-cold behaviour (`Text/corrections_2026-10.md` §5). The non-power-of-two points of the five non-Pi 5 curves had no archived source and are to be treated as unmeasured (`Text/corrections_2026-10.md` §4).

The bench allocates one `std::vector<uint16_t>` per container of exactly `2n` bytes. For a `W`-way set-associative cache with `L`-byte lines and `S` sets (total size `W*L*S`), the **way size** is `S*L = cache_size / W`: the stride at which the set-index bits repeat. Two addresses separated by a multiple of the way size map to the same cache set and compete for its `W` slots. When an array's size `2n` reaches or exceeds the way size, some of its lines start self-colliding on the same sets, evicting each other before reuse. For this bench that manifests as super-linear jumps in cold ns/query at `n` values where `2n` matches or exceeds the way size.

## Way sizes per host

`way_size = cache_size / associativity = S * L`, where `S` is the number of sets and `L` is the line size. Sweep points are `n ∈ {8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096}`, so per-array `2n` spans 16 B to 8 KB. "Aliasing n" lists the sweep points where `2n` reaches or exceeds the way size at that level — the candidates for *per-array* aliasing. (The per-container picture is different; see the section below.)

| Host | L1D geometry | L1D way size | L1D aliasing n | L2 geometry | L2 way size | L2 aliasing n |
|---|---|---|---|---|---|---|
| Pi 5 (A76) | 64 KB, 4-way, 64 B line | 16 KB | none in sweep | 512 KB, 8-way, 64 B line | 64 KB | none in sweep |
| M4 P-core | 128 KB, 8-way, 128 B line | 16 KB | none in sweep | ~16 MB shared, 12-way | ~1.3 MB | none in sweep |
| M1 P-core | 128 KB, 8-way, 128 B line | 16 KB | none in sweep | 12 MB shared, 12-way | 1 MB | none in sweep |
| Skylake-SP | 32 KB, 8-way, 64 B line | 4 KB | 2048, 4096 | 1 MB, 16-way, 64 B line | 64 KB | none in sweep |
| Emerald Rapids | 48 KB, 12-way, 64 B line | 4 KB | 2048, 4096 | 2 MB, 16-way, 64 B line | 128 KB | none in sweep |
| Graviton 4 (V2) | 64 KB, 4-way, 64 B line | 16 KB | none in sweep | 2 MB, 8-way, 64 B line | 256 KB | none in sweep |

Under the corrected arithmetic, the only hosts where a *single array* reaches L1 way size within the sweep are Skylake-SP and Emerald Rapids, at n=2048 (2n = 4 KB, exactly one way size) and n=4096 (2n = 8 KB, two way sizes). Every other host has an L1D way size of 16 KB, which is past the top of the sweep; no per-array L1 aliasing is reachable on Pi 5, M4, M1, or Graviton 4. L2 way sizes are larger everywhere and out of reach at every n. EMR's smooth cold curve is therefore consistent with the geometry in the 12-way-L1D sense (higher associativity means more simultaneous colliding lines before eviction), but it is not the simple "no exact aliasing n" story the original table described.

## Observed non-monotonicities, cross-checked against geometry

Scanning the cold curves in `plot.py` for dips where a single point is >10% faster than both neighbors:

**Pi 5 cold, all three spine variants at n=2048:** 94-110 ns, vs 123-142 at n=1024 and 123-138 at n=4096. The n=2048 array is 4 KB, well inside Pi 5's 64 KB L1D and below the 16 KB way size, so per-array aliasing is not the mechanism. This is a local dip, not an aliasing penalty: the most likely cause is that at n=2048 (64 lines) the array fits with margin inside L1 while the cold-flush eviction pattern happens to leave more of it resident than at n=1024 or n=4096. Measurement artifact, not algorithm behavior, and the opposite direction from what aliasing would produce.

> Correction 2026-10-11: this Pi 5 dip is not in the archived data. The regenerated `bench_table.txt` (per-cell medians of 5 runs of the archived Pi 5 sweep) puts the three spine variants at 136.9–146.8 ns cold at n=2048, against 88.7–112.1 ns at n=1024 and 147.7–154.7 ns at n=4096, so n=2048 is not faster than both neighbours. The 94–110 / 123–142 / 123–138 ns figures match neither archived Pi 5 run set — not `pi5_runs/rebench_run{1..5}.txt` (2026-05-12, the set whose per-cell medians `bench_table.txt` reproduces: 146.8 / 136.9 / 137.4 ns cold at n=2048 for the pi5 / m4 / graviton spine variants), nor `pi5_runs/hybrid_run{1..5}.txt` (also 2026-05-12; per-cell medians 143.8 / 135.1 / 137.8 ns at n=2048) — so their source is unknown (an earlier, unarchived Pi 5 dataset). `Text/corrections_2026-10.md` §4 retracted only the five non-Pi 5 curves; the Pi 5 curve in `plot.py` re-derives from its archive 396/396 (see also the note at the top of this file). There is also no "cold-flush eviction pattern" in `bench.cpp` — its cold column performs no flush (`Text/corrections_2026-10.md` §5).

**M4 cold m4+spine at n=2048:** 4.2 ns, vs 6.0 at n=1024 and 6.5 at n=4096. Same shape as the Pi 5 dip at the same `n`. M4's 128 KB L1D has a 16 KB way size, so at 4 KB the array is well inside a single way and no per-array aliasing is in play. The wide OoO + HW streamer likely cover more of the cold misses at n=2048 than at the L2-spilling n=4096. `m4 cold pi5+spine` dips similarly at n=2048.

> Correction 2026-10-11: these M4 values match the regenerated `bench_table.txt` (m4+spine cold 6.0 / 4.2 / 6.5 ns at n=1024 / 2048 / 4096), but the column is unflushed (see the note at the top), so the "cold misses" here are L2/SLC-regime accesses, and the 16-byte-aligned `std::vector` arrays mean about 87.5% of 128-byte blocks straddle two cache lines, which this explanation does not account for (`Text/corrections_2026-10.md` §5).

**M4 cold pi5+spine and m4 cold gv4+spine at n=16:** 1.0-1.1 ns local minimum. This is the small-n branch of each variant (all three have `n < gap` fast paths) and the non-monotonicity likely reflects the path switching between the `n<8`, `8<=n<16`, `16<=n<32`, and `32<=n<64` branches rather than cache behavior.

**SKX, EMR, GV4, M1 cold:** monotonic within noise at the >10% threshold. No cache-geometry dips visible.

> Correction 2026-10-11: this scan covered 22 points per curve; for SKX, EMR, GV4 and M1 the twelve non-power-of-two points have no archived source (`Text/corrections_2026-10.md` §4, and the note at the top of this file), so only the ten power-of-two points in bench_table.txt can be checked, and a dip at a non-power-of-two n cannot be ruled in or out.

## What isn't in the data

We do *not* see the textbook "sharp cold ns/query spike at n=2048 or n=4096 because of way-conflicts" that a naive reader might expect from the geometry. The reason is the access pattern. The bench's hot path touches one block (one or two cache lines) per query, not the full array; the cold curve is dominated by the ~4-5 dependent loads on the descent + 1-2 block-load misses, which is a handful of distinct cache sets per query rather than a strided sweep over the whole array. Way-conflict aliasing requires enough concurrent accessed lines within one mapping to exceed associativity; the per-query footprint here is typically smaller than the cache's associativity even before streaming prefetch. This is why even on Skylake-SP and Emerald Rapids, where n=2048 and n=4096 do reach the 4 KB L1 way size, the per-array aliasing threshold alone doesn't produce a visible spike.

So what we call "visible aliasing" in the plots is real but is the *allocation-pattern* effect (each container's u16 array is `malloc`'d independently and the allocator returns power-of-two-aligned blocks, so consecutive containers land on overlapping cache sets) rather than a per-query effect. That's consistent with the cross-container-flush protocol of `bench_cold` amplifying the allocation aliasing and making it visible in the per-n curve.

> Correction 2026-10-11: the premise that "the allocator returns power-of-two-aligned blocks" is false for glibc at these sizes. Arrays and spines are `std::vector` allocations with 16-byte alignment, so about 75% of 64-byte blocks and 87.5% of 128-byte blocks straddle two cache lines and a 256-byte spine usually spans five lines. Interleaved aligned-vs-misaligned A/Bs on the Pi 5 measured a +14–30% cold penalty at n=4096, so the per-n bumps attributed here to set aliasing are at least partly a line-alignment artifact (`Text/corrections_2026-10.md` §5). `bench_cold` also has no cross-container flush (`Text/corrections_2026-10.md` §5).

## Implications for the ship recommendation

None. The ship recommendation is variant F (Shar outer + compile-time n=4096 inner), keyed to realistic Roaring container sizes that are whatever the workload gives us, not to the sweep points. The aliasing-visible bumps in the per-n cold curves affect absolute ns at specific sweep `n` but do not change the sign or magnitude of any cross-variant delta within a given `n`; all A/B comparisons are within-row, within-host, and any aliasing affects both sides equally.

> Correction 2026-10-11: the ship recommendation is no longer "F on every host". By paired per-run rank over the archived 2026-05-18 runs (`{host}_runs/twolevel_paired.txt`, 5 runs per host) the cold-best variant is usually C or D: C is cold-best on GV4 (both cold modes 5/5) and EMR (`cold_bat` 5/5, `cold_ser` 4/5), D wins `cold_bat` 5/5 on the Pi 5 and `cold_ser` 5/5 on SKX (`Text/corrections_2026-10.md` §2.1). With the repaired harness the **Pi 5 recommendation is D**: in `pi5_runs/twolevel_paired_v2.txt` (10 runs) D is best by mean rank in `hot_bat`, `hot_ser` and `cold_bat`, and F vs D `cold_bat` is +44.7% with D faster 10/10 (`Text/corrections_2026-10.md` §6). "Any aliasing affects both sides equally" is also not supported: on the Pi 5 the hybrid-vs-general-n cold ordering flips with the alignment regime (`Text/corrections_2026-10.md` §5).

## How to re-verify

```sh
# Re-run with the allocator pinned so the per-container arrays are
# deliberately mis-aligned across the sweep:
export MALLOC_ARENA_MAX=1  # on glibc, forces a single arena
./bench 4000 5000
```

On Linux hosts this reduces the allocation-aliasing component. Bumps that persist after the pin are memory-system effects (L2 miss latency at the LLC boundary, etc.) rather than allocation aliasing; bumps that disappear were allocation-aliasing. We have not run this sweep on every host; a single post-call check on whichever host Daniel is interested in should settle it.

> Correction 2026-10-11: `MALLOC_ARENA_MAX` governs the number of malloc arenas, not allocation alignment, so this check cannot separate set aliasing from the line-straddling effect described above. The relevant test is an interleaved aligned-vs-misaligned A/B of `carr` and the spine, which on the Pi 5 gave a +14–30% cold penalty at n=4096 (`Text/corrections_2026-10.md` §5); cache-line alignment of `carr`/spine in the harnesses and kernels remains an open item (`Text/corrections_2026-10.md` §6).

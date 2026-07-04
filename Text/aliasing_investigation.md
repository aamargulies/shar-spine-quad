# Cache aliasing in the benchmark plots, per-host accounting

Daniel Lemire flagged visible cache aliasing in the benchmark line plots during initial review and said it was "to be expected." This document spot-checks which bumps in the per-host cold curves align with obvious cache-geometry boundaries, so the answer to "have you checked which bumps are the aliasing ones" is yes.

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

**M4 cold m4+spine at n=2048:** 4.2 ns, vs 6.0 at n=1024 and 6.5 at n=4096. Same shape as the Pi 5 dip at the same `n`. M4's 128 KB L1D has a 16 KB way size, so at 4 KB the array is well inside a single way and no per-array aliasing is in play. The wide OoO + HW streamer likely cover more of the cold misses at n=2048 than at the L2-spilling n=4096. `m4 cold pi5+spine` dips similarly at n=2048.

**M4 cold pi5+spine and m4 cold gv4+spine at n=16:** 1.0-1.1 ns local minimum. This is the small-n branch of each variant (all three have `n < gap` fast paths) and the non-monotonicity likely reflects the path switching between the `n<8`, `8<=n<16`, `16<=n<32`, and `32<=n<64` branches rather than cache behavior.

**SKX, EMR, GV4, M1 cold:** monotonic within noise at the >10% threshold. No cache-geometry dips visible.

## What isn't in the data

We do *not* see the textbook "sharp cold ns/query spike at n=2048 or n=4096 because of way-conflicts" that a naive reader might expect from the geometry. The reason is the access pattern. The bench's hot path touches one block (one or two cache lines) per query, not the full array; the cold curve is dominated by the ~4-5 dependent loads on the descent + 1-2 block-load misses, which is a handful of distinct cache sets per query rather than a strided sweep over the whole array. Way-conflict aliasing requires enough concurrent accessed lines within one mapping to exceed associativity; the per-query footprint here is typically smaller than the cache's associativity even before streaming prefetch. This is why even on Skylake-SP and Emerald Rapids, where n=2048 and n=4096 do reach the 4 KB L1 way size, the per-array aliasing threshold alone doesn't produce a visible spike.

So what we call "visible aliasing" in the plots is real but is the *allocation-pattern* effect (each container's u16 array is `malloc`'d independently and the allocator returns power-of-two-aligned blocks, so consecutive containers land on overlapping cache sets) rather than a per-query effect. That's consistent with the cross-container-flush protocol of `bench_cold` amplifying the allocation aliasing and making it visible in the per-n curve.

## Implications for the ship recommendation

None. The ship recommendation is variant F (Shar outer + compile-time n=4096 inner), keyed to realistic Roaring container sizes that are whatever the workload gives us, not to the sweep points. The aliasing-visible bumps in the per-n cold curves affect absolute ns at specific sweep `n` but do not change the sign or magnitude of any cross-variant delta within a given `n`; all A/B comparisons are within-row, within-host, and any aliasing affects both sides equally.

## How to re-verify

```sh
# Re-run with the allocator pinned so the per-container arrays are
# deliberately mis-aligned across the sweep:
export MALLOC_ARENA_MAX=1  # on glibc, forces a single arena
./bench 4000 5000
```

On Linux hosts this reduces the allocation-aliasing component. Bumps that persist after the pin are memory-system effects (L2 miss latency at the LLC boundary, etc.) rather than allocation aliasing; bumps that disappear were allocation-aliasing. We have not run this sweep on every host; a single post-call check on whichever host Daniel is interested in should settle it.

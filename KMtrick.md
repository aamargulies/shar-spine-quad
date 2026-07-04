# The Khuong & Morin trick, in full detail

## The setup

You have a sorted array `A[0..n-1]` and want `lower_bound(x)`. Classical answer: binary search on `A` directly. The paper's claim is that for any `n` larger than a few KB, you can do strictly better by changing **both** the layout and the search code, in a way that exploits two specific microarchitectural properties most modern CPUs have:

1. A pipelined out-of-order core that does speculative execution past mispredicted branches.
2. A non-blocking memory subsystem that can have multiple cache-line fetches in flight (typically 8–10 simultaneously, governed by the load/store queue and miss-status holding registers).

The trick is to arrange the data so that **the speculative fetches the CPU issues anyway are exactly the lines you'll need next, and to issue explicit `__builtin_prefetch` for lines four levels deeper than that**.

The result: every iteration of the search loop has 4 cache-line fetches in flight simultaneously, all of which the CPU eventually consumes. Latency is hidden under bandwidth.

## Component 1: Eytzinger layout

Take a sorted array of `n` keys. Conceptually arrange them as a complete binary search tree (in-order traversal would walk back to the sorted order). Then write the tree to an array in **breadth-first / level-order** — the root at slot 1, its left child at slot 2, right child at slot 3, the four grandchildren at slots 4-7, the eight great-grandchildren at 8-15, and so on. (Slot 0 is unused; this convention makes child indexing arithmetic-friendly: from slot `i`, children are at `2i` and `2i+1`.)

Why level-order? Two reasons:

**Reason 1 (the well-known one): cache-friendly hot levels.** The first level is 1 element, second is 2, third is 4, fourth is 8 — the first 16 elements of the array contain the entire top 4 levels of the tree. The first 64 contain the top 6. The hottest part of *every* search lives contiguously at the front of the array, which is exactly where caching is most beneficial. (Sorted-order binary search has the same property in a different form — `A[n/2]` is hot — but the hot elements are spread across the array, so they take more cache lines.)

**Reason 2 (the load-bearing one for this trick): predictable index arithmetic for descendants.** From slot `i`, the children are `2i` and `2i+1`, the four grandchildren are `4i+0..3`, the eight great-grandchildren are `8i+0..7`, the sixteen great-great-grandchildren are `16i+0..15`. The 16 great-great-grandchildren live at array indices `[16i, 16i+15]`. With 4-byte keys and 64-byte cache lines, each cache line holds 16 keys — so **the 16 great-great-grandchildren of slot `i` are exactly one cache line, located at the address `&A[16*i]`** (give or take an alignment offset).

This is the geometry the prefetch instruction exploits.

## Component 2: branch-free descent

Standard binary search has a three-way branch (`<`, `>`, `=`) which is data-dependent and unpredictable; the branch predictor mispredicts ~50% of the time, and each misprediction costs a 20-cycle pipeline flush.

The branch-free Eytzinger descent looks like this (paper's Listing 5):

```c
int i = 1;
while (i <= n) {
    i = (key <= a[i]) ? (2 * i) : (2 * i + 1);
}
```

The ternary compiles to a `cmov` on x86 (or `csel` on ARM): the CPU computes both candidate next-indices unconditionally and conditionally selects one. **No branch.** The loop has a single branch — the termination test `i <= n` — which is highly predictable because the loop runs the same number of iterations on almost every call (depth of the tree, ±1 for the leaf row).

The descent runs `⌈log₂(n+1)⌉` iterations. For n=512 that's 9. For n=10⁶ that's 20.

What about the answer? The loop terminates when `i > n` — `i` is now the index of a phantom node off the bottom of the tree. The path encoded in `i`'s binary representation tells you exactly which node was the last "go-left" step on the way down. Specifically:

```c
i >>= __builtin_ffs(~i);  // strip trailing 1-bits
```

This shifts off the sequence of "went-right" steps the descent took *after* the answer node, leaving `i` pointing at the answer slot (or 0 if the key exceeded every element). Recovering the answer's *sorted* index from its BFS slot requires a small auxiliary table — for n=10⁶ that's an extra ~4 MB, but the table is only consulted once per query at the very end.

## Component 3: the speculative-execution implicit prefetcher

This is the part Khuong & Morin's paper makes precise. Even **without** explicit `__builtin_prefetch`, branchy Eytzinger search is faster than expected at large `n`. They demonstrate why with a measurement:

When the branch predictor is wrong (which it will be — there's no pattern to learn for a query against random data), the CPU has already started executing speculatively down the wrong path. Speculative execution issues memory loads. Those loads bring cache lines into L1 even though the speculation is later squashed.

In their Eytzinger code, the descent is so regular that the CPU can be 4–5 iterations ahead of the true execution point. With a 20-cycle pipeline depth and 5-instruction-per-iteration loop body, the pipeline holds 4–5 *future* `a[i]` loads at any moment. Even if the branch predictor's guesses are noise — which for random search they nearly are — the prefetched cache lines for the speculative `a[2i]` and `a[2i+1]` loads at depths `d, d+1, d+2, d+3` are streaming into L1 ahead of the actual descent.

This is **runahead execution** (Mutlu et al. 2003) emerging implicitly from a normal pipelined OoO core. The paper's contribution is recognizing that this happens, that Eytzinger layout is what makes the runahead memory accesses *correct enough often enough* to matter (because both children of a node are at adjacent array indices that share a cache line in many cases), and that you can extend it further with explicit prefetch.

## Component 4: explicit 4-deep `__builtin_prefetch` (Listing 6)

Here is the complete inner loop (paper's Listing 6):

```c
int i = 1;
while (i <= n) {
    __builtin_prefetch(a + multiplier * i + offset);
    i = (key <= a[i]) ? (2 * i) : (2 * i + 1);
}
```

Two parameters:

- **`multiplier`** = number of keys per cache line. For 4-byte keys on a 64-byte line, multiplier = 16. For our project's u16 keys on a 128-byte line (Apple silicon), multiplier = 64.
- **`offset`** = `⌊3B/2⌋ - 1` where B is the cache line in bytes — equivalent to `⌊3·multiplier/2⌋ - 1` in keys. This is a centering offset: rather than prefetching the line that *starts* at `multiplier*i`, the offset shifts the prefetch address into the middle of the descendant block, so the line we fetch covers the actual children we'll visit four levels down.

Why the address `a + multiplier*i + offset`? Because slot `i`'s **2⁴ = 16 great-great-grandchildren** live at array slots `[16i, 16i+15]`, which (with 16 keys per cache line) occupy *exactly one cache line* starting at `a + 16i`. The offset re-centers it. Issuing `prefetch(a + 16i)` at iteration `d` requests the line that the descent will hit at iteration `d+4`.

The instruction `prefetchnta` / `prefetcht0` (which `__builtin_prefetch` lowers to) is a hint, not a load. It does not block the pipeline. It does not contribute to the dependency graph of the surrounding code. It just nudges the memory subsystem to start a fetch.

So at any given iteration, the memory subsystem has:

- The **demand load** for `a[i]` at the current depth — already retired or about to retire.
- The **demand load** for `a[2i]` or `a[2i+1]` at depth `d+1` — speculatively issued by the OoO engine.
- A **prefetch** for `a + 16·i_{d-1} + offset`, the cache line covering `a[i]`'s great-great-grandchildren, queued from the previous iteration.
- A **prefetch** for `a + 16·i_{d-2} + offset`, similar from two iterations ago.

That's 4 cache lines in flight simultaneously, deliberately. On a modern CPU with ~10 outstanding load slots and ~25 ns DRAM round trip, by the time the descent reaches depth `d+4` and demands the line, it's already arriving.

## Component 5: why this is qualitatively different from `prefetch(a + n/2)` style

The traditional binary-search prefetch advice is "prefetch the next probe point" — `__builtin_prefetch(&a[mid + (mid+lo)/2])` or similar. That gives you exactly **one** cache line ahead. With single-issue prefetching the round-trip latency to DRAM is exposed for every miss after the first; you save one miss out of `log₂(n)`.

Khuong & Morin's trick gives you **four** cache lines ahead, and crucially — because Eytzinger geometry guarantees the descendant block is contiguous — every prefetch hits a real, consumed line. The CPU's load pipeline is *saturated* with useful work: while waiting for line at depth `d` you have already issued the request for the line at depth `d+4`.

The mathematical model (paper §4) is: if `W` is the number of cache lines per second the memory subsystem can deliver, `L` is the latency of one line (~25 ns), and `B` is keys-per-line, then traditional binary search runs at `L · log_B n` because every `log B` levels stalls for one full latency. Eytzinger with t-deep prefetch runs at `max(L, c) · log_B n` where `c` is the local-compute time per level — provided `WL > t · log B`, i.e. provided you have enough memory bandwidth to accommodate `t · log B` simultaneous in-flight requests. For 4-byte data and `t=1` they measured `WL ≈ 4.7`, which is exactly enough for the depth-1 prefetch to saturate; deeper prefetches contend.

## Component 6: failure modes

This is what makes the project's K=512 outer interesting.

The trick **fails or breaks even** when:

- **The array fits in L1/L2 cache.** No prefetch needed; everything is one cycle away. Khuong & Morin's own data shows the prefetch breaks even from n=2¹³ to n=2¹⁶ on the 4790K and only starts winning visibly at n=2¹⁸.
- **Bandwidth is already saturated by hardware streamers.** On wide-OoO server cores (M4 Max, EMR, GV4 in our project), the L2/L3 stride prefetcher is already filling the bandwidth budget. The software prefetches contend with demand loads rather than overlapping with idle bandwidth — the cold-mode regression we measured on M1 Pro (cold_bat +18%, cold_ser +12% for I vs F) is precisely this.
- **The array is too short for runahead to pay off.** Khuong & Morin's regime is `n > 2¹⁵`. Our K=512 outer is `n = 512` — well below their tested floor. The 9-deep descent issues 9 prefetches over ~25 ns of work; the first prefetch fires at depth 0, fetches the line for depth 4, and is consumed at depth 4. That's a head start of 4×~3 ns = 12 ns on a 25 ns DRAM round trip — useful but not free.
- **The dependency chain pinches the issue rate.** In `cold_ser` mode each query waits for the previous one's result, so the OoO engine can't even speculate forward across queries, and only the within-query prefetches help. This is exactly where the I-vs-F win shows up on M1 Pro.

The trick **wins** when: array is bigger than L2, hardware streamer cannot pattern-match the access (because the access *is* random), and there's enough bandwidth headroom to absorb 4-deep prefetching. That's the core insight of the paper.

## What we adopted, and what we changed

Our variant I keeps the trick faithful: Eytzinger layout, branch-free `cmov` descent via the ternary, `__builtin_prefetch` of `a + multiplier*i + offset` with the paper's exact constants. We added:

1. The trailing pad on `keys_eytz` (paper §5.3): some Intel CPUs penalize prefetches whose target address is past the allocation. We pad by `kGap * 16` u16 (≈ 1-2 KB per outer set) so the worst-case prefetch reach stays inside our buffer. Paper's masking variant is the alternative; padding is simpler and trivial in cost.
2. The `eytz_to_sorted` inverse permutation (paper Listing 4-5): our callsite needs the *sorted* index to address `s.containers[idx]`, not the BFS slot. The 1 KB extra table is read once per query and stays in L1 across queries.
3. Application to the K=512 outer specifically, where the paper's mechanism is the diagnosed cure for our pre-existing "narrow-OoO + dep-chain → cold-reversal" failure mode.

That's the trick in full.

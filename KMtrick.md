# The Khuong & Morin trick, in full detail

*Source: Paul-Virak Khuong and Pat Morin, "Array Layouts for Comparison-Based Searching", arXiv:1509.05053, <https://arxiv.org/abs/1509.05053> (v2, 15 March 2017); ACM Journal of Experimental Algorithmics 22 (2017), pp. 1–39, <https://doi.org/10.1145/3053370>. The listing, section and "PDF p." references below are to the authors' 49-page PDF dated 14 March 2017, which this repository redistributed until 2026-10-11 and now only cites (see `THIRD_PARTY_NOTICES.md`).*

*Revised 2026-10-11: the block/offset derivation in Components 1 and 4 was wrong — it mixed the paper's 0-based layout with this document's 1-based one, which is the error behind the mis-aimed prefetch in variants H/I — and the "~25 ns DRAM round trip" and "4-deep" wording were corrected. See `Text/corrections_2026-10.md` §1 and §5.*

## The setup

You have a sorted array `A[0..n-1]` and want `lower_bound(x)`. Classical answer: binary search on `A` directly. The paper's claim is that for any `n` larger than a few KB, you can do strictly better by changing **both** the layout and the search code, in a way that exploits two specific microarchitectural properties most modern CPUs have:

1. A pipelined out-of-order core that does speculative execution past mispredicted branches.
2. A non-blocking memory subsystem that can have multiple cache-line fetches in flight (typically 8–10 simultaneously, governed by the load/store queue and miss-status holding registers).

The trick is to arrange the data so that **the speculative fetches the CPU issues anyway are exactly the lines you'll need next, and to issue explicit `__builtin_prefetch` for the line log₂(B) levels deeper than that**, where B is the number of keys per cache line — four levels in the paper's B = 16 case (4-byte keys, 64-byte lines), five at gap 32 and six at gap 64 for this project's u16 keys.

The result: every iteration of the search loop has about log₂(B) cache-line fetches in flight simultaneously (4 in the paper's case), most of which the CPU eventually consumes. Latency is hidden under bandwidth.

## Component 1: Eytzinger layout

Take a sorted array of `n` keys. Conceptually arrange them as a complete binary search tree (in-order traversal would walk back to the sorted order). Then write the tree to an array in **breadth-first / level-order** — the root at slot 1, its left child at slot 2, right child at slot 3, the four grandchildren at slots 4-7, the eight great-grandchildren at 8-15, and so on. (Slot 0 is unused; this convention makes child indexing arithmetic-friendly: from slot `i`, children are at `2i` and `2i+1`.)

Why level-order? Two reasons:

**Reason 1 (the well-known one): cache-friendly hot levels.** The first level is 1 element, second is 2, third is 4, fourth is 8 — the first 16 elements of the array contain the entire top 4 levels of the tree. The first 64 contain the top 6. The hottest part of *every* search lives contiguously at the front of the array, which is exactly where caching is most beneficial. (Sorted-order binary search has the same property in a different form — `A[n/2]` is hot — but the hot elements are spread across the array, so they take more cache lines.)

**Reason 2 (the load-bearing one for this trick): predictable index arithmetic for descendants.** From slot `i`, the children are `2i` and `2i+1`, the four grandchildren are `4i+0..3`, the eight great-grandchildren are `8i+0..7`, the sixteen great-great-grandchildren are `16i+0..15`. The 16 great-great-grandchildren live at array indices `[16i, 16i+15]`. With 4-byte keys and 64-byte cache lines, each cache line holds 16 keys — so **the 16 great-great-grandchildren of slot `i` are exactly one cache line, starting at the address `&A[16*i]`** — *provided slot 0 starts a cache line*; with an arbitrary allocation the block straddles two lines, so the array must be line-aligned. In general, in this 1-based layout the 2ᵏ descendants of slot `i` at depth `k` occupy `[2ᵏ·i, 2ᵏ·i + 2ᵏ − 1]`, and with B keys per line the line-sized block is log₂(B) levels down at **`[B·i, B·i + B − 1]`**. (The paper's own listings are 0-based — root at `a[0]`, children `2i+1` and `2i+2` — where the same block sits one slot later, at `[B·i + B − 1, B·i + 2B − 2]`. That one-slot difference is what the offset constant in Component 4 depends on.)

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

The descent runs at most `⌈log₂(n+1)⌉` iterations. For n=512 that is 10 by the formula — 9 on every path except the all-left one, which visits slot 512 and takes a tenth. For n=10⁶ that's 20.

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

## Component 4: explicit log₂(B)-deep `__builtin_prefetch` (Listing 6)

Here is the complete inner loop, in the 1-based convention of this document (the paper's Listing 6 is the same loop in its 0-based convention — `i = 0`, children `2i+1` / `2i+2` — with a correspondingly different `offset`; see below):

```c
int i = 1;
while (i <= n) {
    __builtin_prefetch(a + multiplier * i + offset);   // offset = multiplier/2 in this 1-based layout
    i = (key <= a[i]) ? (2 * i) : (2 * i + 1);
}
```

Two parameters:

- **`multiplier`** = B = number of keys per cache line. For 4-byte keys on a 64-byte line, multiplier = 16. For our project's u16 keys, multiplier = 32 on the 64-byte-line hosts and 64 on Apple silicon's 128-byte line (`kGap` in `bench_twolevel.cpp`).
- **`offset`**: the paper's constant is `⌊3B/2⌋ − 1` with B in **keys per line, not bytes** (the paper defines B as the number of data items that fit in one cache line; in bytes the formula would be meaningless). That constant belongs to the paper's **0-based** layout, where the block log₂(B) levels below node `i` is `[B·i + B − 1, B·i + 2B − 2]` and `B·i + 3B/2 − 1` is simply its middle. In the **1-based** layout used here and in `bench_twolevel.cpp` the block is `[B·i, B·i + B − 1]`, its middle is `B·i + B/2`, and the right offset is **`B/2`**. The constant does not "re-center" anything: applied to a 1-based tree, `+3B/2 − 1` lands in `[B·(i+1), B·(i+1) + B − 1]`, the descendant block of node `i+1`, and the prefetch never touches a line on the search path. That is exactly the defect the 2026-10-11 review found in variants H/I — the shipped `kPrefOff = 3*kGap/2 − 1` aimed every prefetch at the neighbouring node's line, and the Eytzinger outer was slower than with no prefetch at all; it is now `kGap/2` (`Text/corrections_2026-10.md` §1). Every H/I number recorded before 2026-10-11 was measured with the mis-aimed version.

Why the address `a + multiplier*i + offset`? Because in the 1-based layout slot `i`'s **2⁴ = 16 great-great-grandchildren** live at array slots `[16i, 16i+15]`, which (with 16 keys per cache line and slot 0 line-aligned) occupy *exactly one cache line* starting at `a + 16i`; any offset in `[0, 15]` addresses that same line, and `B/2 = 8` aims at its middle. Issuing the prefetch at iteration `d` requests the line that the descent will hit at iteration `d + log₂(B)` — `d+4` for B = 16, `d+5` at gap 32, `d+6` at gap 64.

The instruction `prefetchnta` / `prefetcht0` (which `__builtin_prefetch` lowers to) is a hint, not a load. It does not block the pipeline. It does not contribute to the dependency graph of the surrounding code. It just nudges the memory subsystem to start a fetch.

So at any given iteration, the memory subsystem has:

- The **demand load** for `a[i]` at the current depth — already retired or about to retire.
- The **demand load** for `a[2i]` or `a[2i+1]` at depth `d+1` — speculatively issued by the OoO engine.
- A **prefetch** for `a + 16·i_{d-1} + offset`, the cache line covering `a[i]`'s descendants log₂(B) levels down (great-great-grandchildren when B = 16), queued from the previous iteration.
- A **prefetch** for `a + 16·i_{d-2} + offset`, similar from two iterations ago.

That's about log₂(B) cache lines in flight simultaneously, deliberately (4 in the paper's case). A modern CPU's ~10 outstanding load slots hold all of them, and by the time the descent reaches depth `d + log₂(B)` and demands the line it is already arriving — if the line's latency is covered by log₂(B) iterations of local work. (An earlier version of this sentence called 25 ns a "DRAM round trip". The ~25 ns this project measured as the M1 Pro cold floor is an SLC/L3-hit latency, not DRAM; a DRAM miss is substantially longer — `Text/corrections_2026-10.md` §5, and `Text/CPU.text` for the per-host latency figures.)

## Component 5: why this is qualitatively different from `prefetch(a + n/2)` style

The traditional binary-search prefetch advice is "prefetch the next probe point" — `__builtin_prefetch(&a[mid + (mid+lo)/2])` or similar. That gives you exactly **one** cache line ahead. With single-issue prefetching the round-trip latency to DRAM is exposed for every miss after the first; you save one miss out of `log₂(n)`.

Khuong & Morin's trick gives you **log₂(B)** levels of lookahead (four in the paper's case), and — because Eytzinger geometry guarantees the descendant block is contiguous — a correctly aimed prefetch hits a real, consumed line *whenever the target node exists*: only the prefetches issued at depths `d ≤ 8 − log₂(B)` of the K=512 outer's descent land on a full tree level (full levels occupy depths 0–8; depth 9 holds only slot 512): 4 at gap 32, 3 at gap 64, plus one on the all-left path through slot 512; the rest address the zero pad past the array and are wasted bandwidth, which the paper accepts in exchange for a branch-free loop. Before 2026-10-11 the shipped code's prefetches hit *no* consumed line at all (Component 4). While waiting for the line at depth `d` you have already issued the request for the line at depth `d + log₂(B)`.

The mathematical model (paper §4) is: if `W` is the number of cache lines per second the memory subsystem can deliver, `L` is the latency of one line, and `B` is keys-per-line, then traditional binary search runs at `L · log_B n` because every `log B` levels stalls for one full latency. Eytzinger with prefetching runs at `max(L, c) · log_B n`, where `c` is the local-compute time per level, provided `WL > log B` — enough bandwidth for the `log B` requests Listing 6 keeps in flight; with `t` extra levels of prefetch (`2^t` prefetches per node, reaching `t + log B` levels down) the condition becomes `WL > 2^t · log B` (paper §4.1, PDF p. 36). On their 4790K `WL ≈ 4.7` and `log B = 4` for 4-byte data, so Listing 6 (`t = 0`) already nearly saturates the memory pipeline; `t = 1` gave no speedup and `t = 2` was significantly slower. Note the direction of the condition: `WL > log B` is the regime in which the one-prefetch-per-level scheme *attains* `max(L, c) · log_B n` — where Listing 6 wins (paper §4, PDF p. 35, per the 2026-10 review). This project's earlier write-ups used "WL > log B" as the name of a bandwidth-*contention* regime to explain the cold losses of variant I; those losses were produced by the mis-aimed prefetch of Component 4, and that reading is retracted (`Text/corrections_2026-10.md` §1).

## Component 6: failure modes

This is what makes the project's K=512 outer interesting.

The trick **fails or breaks even** when:

- **The array fits in L1/L2 cache.** No prefetch needed; everything is one cycle away. Khuong & Morin's own data shows the prefetch breaks even from n=2¹³ to n=2¹⁶ on the 4790K and only starts winning visibly at n=2¹⁸. (Their Fig. 12, per the 2026-10 review, shows it as a small *cost* for n ≤ 2¹³ — the regime of our 1 KB outer in the hot modes.)
- **Bandwidth is already saturated by hardware streamers.** On wide-OoO server cores (M4 Max, EMR, GV4 in our project), the L2/L3 stride prefetcher is already filling the bandwidth budget, and software prefetches would contend with demand loads rather than overlap idle bandwidth. The cold-mode regression we measured on M1 Pro (paired I vs F, 5 runs, `m1_runs/twolevel_paired.txt`: cold_bat +17.9%, cold_ser +16.3%, I slower 5/5) was *attributed* to this — but those numbers were taken with the mis-aimed prefetch of Component 4, and variant I also pays one extra dependent load that F never pays (`eytz_to_sorted[i]`, then `keys[sorted_idx]`), so they do not test this failure mode (`Text/corrections_2026-10.md` §1).
- **The array is too short for runahead to pay off.** Khuong & Morin's regime is `n > 2¹⁵`. Our K=512 outer is `n = 512` — well below their tested floor, and L1-resident in the hot modes. The ~9-deep descent issues ~9 prefetches; the first fires at depth 0, fetches the line for depth log₂(B) (5 at gap 32) and is consumed there, so the head start is log₂(B) iterations of local work — a few nanoseconds — against one line's latency. (The earlier text put this as "12 ns on a 25 ns DRAM round trip"; the 25 ns is an SLC/L3-hit figure, not DRAM — Component 4.) The repaired Pi 5 measurement says the head start is not enough on that core: with the corrected prefetch, I is still slower than F hot (+7.3% hot_bat, F faster 8/10; +8.6% hot_ser, 8/10) and slower than D in every mode (+10.2% / +11.1% / +53.2% / +18.1%) — paired, 10 runs, `pi5_runs/twolevel_paired_v2.txt`.
- **The dependency chain pinches the issue rate.** In `cold_ser` mode each query waits for the previous one's result, so the OoO engine can't even speculate forward across queries, and only the within-query prefetches help. This is *not* where variant I won on M1 Pro: paired, I lost `cold_ser` to F (+16.3%, I slower 5/5); its only win was `hot_ser` (−10.9%, I faster 4/5), both measured with the mis-aimed prefetch (`m1_runs/twolevel_paired.txt`). The within-query-prefetch argument has no supporting measurement yet.

The trick **wins** when: array is bigger than L2, hardware streamer cannot pattern-match the access (because the access *is* random), and there's enough bandwidth headroom to absorb log₂(B)-deep prefetching. That's the core insight of the paper.

## What we adopted, and what we changed

Our variant I keeps the layout and the branch-free `cmov` descent via the ternary, and prefetches `a + multiplier*i + offset` with the paper's multiplier. It was *not* faithful on the offset until 2026-10-11: it used the paper's 0-based constant `3·multiplier/2 − 1` on our 1-based layout, which aimed every prefetch at the neighbouring node's block (Component 4); the offset is now `kGap/2`. We added:

1. The trailing pad on `keys_eytz` (paper §5.3): some Intel CPUs penalize prefetches whose target address is past the allocation. The pre-2026-10 pad of `kGap * 16` u16 covered about a thirty-second of the actual prefetch reach (`kGap·i` for `i` up to K = 512: 512 pad slots against 16,384 slots at gap 32, the same ratio at gap 64): about half of the ~9 prefetches per query left the ~2 KB allocation, by up to ~31 KB at gap 32 (~63 KB at gap 64) — the very hazard the pad was meant to prevent. Since 2026-10-11 the array is cache-line aligned (slot 0 starts a line, so a descendant block is exactly one line, as the paper assumes) and padded by `kGap·(K+1)` slots so no prefetch leaves the allocation (`Text/corrections_2026-10.md` §1). Paper's masking variant is the alternative; padding is simpler and trivial in cost.
2. The `eytz_to_sorted` inverse permutation (paper Listing 4-5): our callsite needs the *sorted* index to address `s.containers[idx]`, not the BFS slot. The 1 KB extra table is read once per query and stays in L1 across queries.
3. Application to the K=512 outer specifically, where the paper's mechanism was proposed as the cure for our pre-existing "narrow-OoO + dep-chain → cold-reversal" failure mode. That diagnosis did not survive re-measurement: the cold-reversal percentages it rested on were retracted (`Text/corrections_2026-10.md` §2.3), and on the Pi 5 with the corrected prefetch variant I never beats D in any mode (`pi5_runs/twolevel_paired_v2.txt`; §6); the other five hosts are unmeasured with the fix.

That's the trick in full.

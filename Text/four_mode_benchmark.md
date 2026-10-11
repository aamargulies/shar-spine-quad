# The 4-mode benchmark

> **Correction notice (2026-10-11).** This document is a lab note kept as history. A 2026-10-11 review of the repository's measurements found aggregation and harness defects behind several claims below; each affected statement is followed by a `Correction 2026-10-11` note and the original text is left in place. The authoritative list of retractions and replacement numbers is [Text/corrections_2026-10.md](corrections_2026-10.md); where that file and this one disagree, that file wins.

The harness (in `bench_twolevel.cpp:49-83`) crosses two independent axes, yielding four measurements instead of the old `(warm, cold)` pair.

## The two axes

**Axis 1 — cache state.** Do the container keys, spines, and target arrays already live in L1/L2, or must each query pay DRAM latency?
- `hot`: the same ~4 MB set is reused across `hot_reps` queries. After the first few reps, everything is hot.
- `cold`: one query per set, sweeping ~800 MB across 200 sets. Each cold mode is preceded by `thrash_llc()` (a 256 MB scratch write) so the starting state is genuinely cold regardless of which mode ran before it.

> Correction 2026-10-11: "everything is hot" overstates the hot modes. Each set's 200 hot reps touch about 91 distinct containers once each, so only the 1 KB outer key array stays hot; the inner container loads are first touches — DRAM-cold on the Pi 5 and SKX, L2/L3 hits on Apple / EMR / GV4. Measured on the Pi 5, F `hot_bat` is 61 ns/query at 12 sets, 172 ns at 48 and 213 ns at 200. Hot modes also send about 50% outer-miss queries while cold modes are 100% crafted hits, so cross-host "cold" comparisons compare cache levels, not cores (`Text/corrections_2026-10.md` §5). `thrash_llc()` was 256 MB, smaller than the 8559C's 260 MB L3; it is 512 MB as of 2026-10-11 (`Text/corrections_2026-10.md` §5; comment above `thrash_llc()` in `bench_twolevel.cpp`).

**Axis 2 — query dispatch.** Can the OoO engine overlap queries, or must each wait on the prior one's result?
- `batched`: queries are independent. The OoO window holds multiple in flight; cache misses on query N+1 issue while N is still resolving. Memory-level parallelism (MLP) and instruction-level parallelism (ILP) are in play.
- `serial`: each query's input depends on the previous return value via a cmov. The next query *cannot* start until the prior one's load chain finishes. No MLP, no ILP hiding — you see the raw critical path.

## Mapping to latency and throughput

| mode | cache | dispatch | what it measures |
|---|---|---|---|
| `hot_bat` | hot | batched | **throughput, cache-resident.** Per-query cost when data lives in L1/L2 and the pipeline is free to overlap. Usually the smallest number. Dominated by per-query critical-path length when the inner algorithm has a long dep chain (A, G), and by pipeline issue width otherwise. |
| `hot_ser` | hot | serial | **latency, cache-resident.** True per-query dependent critical path with no MLP/ILP hiding. The L1-hit load-use chain: how many dependent loads × load-use latency. |
| `cold_bat` | cold | batched | **throughput, memory-bound.** MLP does its heaviest work here: many independent DRAM misses stacked in the OoO window. Can counter-intuitively be *lower* than `hot_bat` on narrow-OoO hosts where the hot path is bottlenecked on a downclocked scalar loop (e.g. SKX with AVX-512 license). |
| `cold_ser` | cold | serial | **latency, memory-bound.** Worst case. Each query's cold misses serialize behind the prior query's return — no overlap available. This is what Shar-outer variants get punished on: a 9-deep cmov chain on K=512 outer keys has no spine entries to prefetch behind, so every tier pays full DRAM latency on the critical path. |

> Correction 2026-10-11 (`hot_bat` / `hot_ser` rows): "data lives in L1/L2" holds only for the 1 KB outer array; inner loads in the hot modes are first touches (see the note under Axis 1; `Text/corrections_2026-10.md` §5).

> Correction 2026-10-11 (`cold_bat` row): the "`cold_bat` lower than `hot_bat` on SKX because of the AVX-512 license" example is retracted on both counts. The shipped SKX build is gated to AVX2 and executes no zmm instruction, so nothing is downclocked, and 512-bit integer compares on Skylake-SP trip license level L1, not L2 (`Text/corrections_2026-10.md` §5). The archived SKX data show no such inversion: in `skx_runs/twolevel_summary.txt` (5-run per-cell medians) `cold_bat` exceeds `hot_bat` for all ten variants, e.g. F 84.42 ns `hot_bat` vs 594.47 ns `cold_bat`.

> Correction 2026-10-11 (`cold_ser` row): the Shar-outer `cold_ser` penalty is real only on some hosts. Paired per-run F-vs-D `cold_ser` deltas from the archived 2026-05-18 runs (`{host}_runs/twolevel_paired.txt`, 5 runs): SKX +16.9% (D faster 5/5), EMR +17.7% (D faster 5/5), M4 Max +16.2% (D faster 4/5); Pi 5 −0.4%, M1 Pro +5.7% and GV4 +1.2% are ties (`Text/corrections_2026-10.md` §2.2). Shar's chain is a serial load → compare → csel → load dependency that cannot be speculated past; the branchy `std::lower_bound` outer (variants A, C) can speculate ahead across mispredicted branches on cold data, which is why C is the cold winner on EMR and GV4 (`Text/corrections_2026-10.md` §5).

## Why it matters for this project

The old 2-mode `(warm, cold)` conflated the two axes — it was always batched, so "warm" was really `hot_bat` and "cold" was really `cold_bat`. That hid the asymmetry behind the SKX F-vs-D reversal: F wins `hot_bat` (throughput) but loses `cold_ser` (latency) because Shar's cmov chain can't exploit MLP when queries serialize. The 4-mode view surfaces that tradeoff explicitly — `hot_bat` vs `hot_ser` is the ILP/MLP delta when cache-resident; `cold_ser` minus `cold_bat` is how much MLP buys you against DRAM latency; `cold_ser` minus `hot_ser` is the cold-miss tax on the critical path.

> Correction 2026-10-11: "'cold' was really `cold_bat`" is too generous to the old 2-mode harness. Its cold query was a random 32-bit value that missed the outer keys about 99% of the time and never ran the inner search, and there was no cache flush between variants, so B–F found the keys L2-warm after A had swept them; every pre-2026-05-13 two-level cold number (including the "~12.9× cold" headline) is retracted and replaced by the paired 4-mode tables (`Text/corrections_2026-10.md` §3). The SKX F-vs-D asymmetry itself survives pairing: F `hot_bat` −14.4% (F faster 5/5) and `cold_ser` +16.9% (D faster 5/5) in `skx_runs/twolevel_paired.txt` (`Text/corrections_2026-10.md` §2.2).

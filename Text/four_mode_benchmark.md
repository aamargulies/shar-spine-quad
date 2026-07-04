# The 4-mode benchmark

The harness (in `bench_twolevel.cpp:49-83`) crosses two independent axes, yielding four measurements instead of the old `(warm, cold)` pair.

## The two axes

**Axis 1 — cache state.** Do the container keys, spines, and target arrays already live in L1/L2, or must each query pay DRAM latency?
- `hot`: the same ~4 MB set is reused across `hot_reps` queries. After the first few reps, everything is hot.
- `cold`: one query per set, sweeping ~800 MB across 200 sets. Each cold mode is preceded by `thrash_llc()` (a 256 MB scratch write) so the starting state is genuinely cold regardless of which mode ran before it.

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

## Why it matters for this project

The old 2-mode `(warm, cold)` conflated the two axes — it was always batched, so "warm" was really `hot_bat` and "cold" was really `cold_bat`. That hid the asymmetry behind the SKX F-vs-D reversal: F wins `hot_bat` (throughput) but loses `cold_ser` (latency) because Shar's cmov chain can't exploit MLP when queries serialize. The 4-mode view surfaces that tradeoff explicitly — `hot_bat` vs `hot_ser` is the ILP/MLP delta when cache-resident; `cold_ser` minus `cold_bat` is how much MLP buys you against DRAM latency; `cold_ser` minus `hot_ser` is the cold-miss tax on the critical path.

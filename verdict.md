> **Correction note (2026-10-11).** This verdict closed the M1 Pro `_spine_4096` cold-floor work (levers pfC, sentinel, sentinel_2x; archived in `m1_runs/pfC_run_aggregate.txt`, `m1_runs/sentinel_2x_aggregate.txt`, `m1_runs/sentinel_hit50_aggregate.txt`, `m1_runs/sentinel_uniform_aggregate.txt`). Its measurements stand; two of its conclusions do not survive `Text/corrections_2026-10.md` §5: the "~25 ns" floor is an SLC/L3-hit latency, not a DRAM line, and the regression it was trying to cure may be a measurement-order artifact of `bench.cpp`. Each claim below was checked against the corrections file and the archived aggregates; notes follow the affected paragraphs.

  Verdict

  The sentinel idea has the right structure (95% of queries skip the demand
  block-load) but pays for it with (a) doubled spine size that costs extra cold
  latency, and (b) an extra dependent L1 load on the critical path that costs
  warm. Net negative on both modes. All the levers I've tried this session —
  pfC, sentinel, sentinel_2x — confirm the same underlying lesson:

> **Check (2026-10-11):** The archived runs record `miss_rate = 0.931` (uniform and 2x) and `0.937` (hit50), i.e. about 93% of queries skip, not 95% (`m1_runs/sentinel_*_aggregate.txt` headers). "Net negative on both modes" holds in the archive: against the plain hybrid, `full + sentinel` is slower warm and cold in 15 of 15 trials (warm 4.87–5.24 vs 4.33–4.62 ns/query; cold 37.35–41.67 vs 34.99–38.57), and `full + sentinel_2x` is slower warm 5/5 and cold 4/5 (trial 2 of `sentinel_2x_aggregate.txt`: 36.21 vs 36.87) — best of 5 reps per trial, 512 sets, same files.

  On a wide-OoO core with lo-dependent demand load, anything that adds a
  dependent load anywhere on the critical path costs more than it saves. The
  cold floor is genuinely the architectural minimum cost of fetching one DRAM
  line whose address is the dependent product of the descent.
  Speculative-prefetch can't help (lever C, today), and
  algorithmic-skip-the-load can't help either if the skip-test itself is
  dependent-loaded (sentinel/sentinel_2x).

> **Correction (2026-10-11):** Not a DRAM line. The isolated block-load cost in these runs is about 20–25 ns (`cold blk-only-only` 19.61–25.23 ns across the 15 trials in `m1_runs/sentinel_*_aggregate.txt`), which is an SLC/L3-hit latency on M1 Pro, not a DRAM round trip (`Text/corrections_2026-10.md` §5; `Text/CPU.text` for the per-level latency figures). More importantly, the regression this floor belongs to — the Apple `_spine_4096` "structural cold regression" — may be a measurement-order artifact of `bench.cpp`: in the grid the spine kernel's cold pass runs right after the non-spine kernel's cold pass with identical targets, so the block line is an L2 hit on Apple's large L2, while the dedicated `4096*` row runs after its own 32 MB warm sweep and fetches the line from SLC/DRAM; the reported gap matches L2-hit vs SLC-hit latencies and the same asymmetry reproduces on the Pi 5 (§5). That is a hypothesis that needs a flushed A/B on Apple hardware. "Speculative-prefetch can't help (lever C)" is consistent with the archive — `full + pfC (4-way)` is slower than the hybrid cold in every trial (41.75–46.96 vs 34.99–38.57 ns) — but pfC issued four same-depth candidate lines of which three are wasted by construction, so it tests neither Khuong & Morin's deeper-prefetch `t` nor a correctly aimed prefetch (see the note to point 3 in `KhuongMorin.md`).

  The only remaining lever I can see that doesn't add a dependent load is
  changing what the descent computes — e.g., have the descent itself produce a
  "miss" verdict alongside lo, by making the spine entries encode block-edge
  info via bit-tricks rather than via a separate load. That's a bigger algorithm
   change with no obvious clean encoding.

  Recommend closing here. Want me to

> **Correction (2026-10-11):** Closing the *lever search* was right on the archived evidence; closing the *question* was premature. Before any further remediation of this floor, run the decisive test from `Text/corrections_2026-10.md` §5 on an Apple host: flush before both the grid pass and the `4096*` row (or run both in the same order) and see whether the `_spine_4096` cold regression survives. The OpenEvolve starting program for this work was also the retired unroll, not the shipped hybrid (§5). The "wide-OoO core with lo-dependent demand load" framing is unaffected, but "architectural minimum" should be read as "SLC-hit floor under the current measurement order".

  Verdict

  The sentinel idea has the right structure (95% of queries skip the demand
  block-load) but pays for it with (a) doubled spine size that costs extra cold
  latency, and (b) an extra dependent L1 load on the critical path that costs
  warm. Net negative on both modes. All the levers I've tried this session —
  pfC, sentinel, sentinel_2x — confirm the same underlying lesson:

  On a wide-OoO core with lo-dependent demand load, anything that adds a
  dependent load anywhere on the critical path costs more than it saves. The
  cold floor is genuinely the architectural minimum cost of fetching one DRAM
  line whose address is the dependent product of the descent.
  Speculative-prefetch can't help (lever C, today), and
  algorithmic-skip-the-load can't help either if the skip-test itself is
  dependent-loaded (sentinel/sentinel_2x).

  The only remaining lever I can see that doesn't add a dependent load is
  changing what the descent computes — e.g., have the descent itself produce a
  "miss" verdict alongside lo, by making the spine entries encode block-edge
  info via bit-tricks rather than via a separate load. That's a bigger algorithm
   change with no obvious clean encoding.

  Recommend closing here. Want me to

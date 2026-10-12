# Show HN post plan

> Corrected 2026-10-11 against Text/corrections_2026-10.md; earlier numbers were retracted, see that file.

## Title options

Pick one, keep under ~80 chars, no "I" or emoji per HN style:

1. `Show HN: Tuning Lemire's SIMD Quad search across six CPU families`
2. `Show HN: Per-uarch SIMD search variants for Roaring Bitmap containers`
3. `Show HN: 1971 branchless search vs. a modern index for Roaring lookups, 6 CPUs`

(An earlier option 3 claimed "~13x cold". That number came from the
retired two-mode harness and is retracted; see corrections §3.)

I'd lean toward #1, it names the thing people recognize (Lemire's
algorithm, widely read), says what's new (six hosts), and doesn't
overclaim a number.

## URL to post

`https://github.com/aamargulies/shar-spine-quad`

The README is thorough enough to stand on its own; you don't need a
blog post first. If you do write one later, you can cross-link.

## Suggested first comment

HN convention: the author posts a first comment explaining what it is
and what they learned. Don't repeat the README, add the motivation and
the surprises. Here's a draft you can edit:

```
Author here. Starting point was Daniel Lemire's "You can beat the binary
search" post (https://lemire.me/blog/2026/04/27/you-can-beat-the-binary-search/),
which gives a neat SIMD "quad" search for small sorted uint16_t arrays,
exactly the shape that lives inside Roaring Bitmap array containers.

I was curious how much the right answer varies by microarchitecture, so
I ran the same algorithmic shape through six host families: Raspberry
Pi 5 (Cortex-A76), Apple M1 Pro, Apple M4 Max, Intel Skylake-SP (Xeon
8175M), Intel Emerald Rapids (Xeon 8559C), and AWS Graviton 4
(Neoverse V2). Each ended up wanting different knobs:

- gap (32 vs 64) tracks cache-line size, not SIMD width. Intel with
  512-bit registers still wants gap=32 because the line is 64 B.
- Speculative in-loop prefetch is dropped on M1/M4/EMR/GV4, where wide
  OoO + HW streamers already overlap the miss (on GV4 keeping it costs
  up to +10.8% warm at n=2048, gv4_runs/ab_summary.txt). The shipped
  Pi 5 kernel still has one, but the archived main bench is a built-in
  A/B (the Graviton kernel is the Pi 5 kernel minus that prefetch) and
  says it is a net loss: slower cold at 13 of 14 sizes from n=128 up
  (corrections §5). SKX keeps it too, with no archived A/B (the one
  noted in the project's findings log was inconclusive).
- On Skylake-SP the zmm block check is gated off in favour of a 2x
  256-bit AVX2 fallback, with __AVX512VBMI2__ (Ice Lake-SP+) as the
  switch. An earlier draft blamed "any zmm op trips the AVX-512
  license and downclocks the scalar loop"; that was wrong on two
  counts: 512-bit integer compares trip license L1, not L2, and the
  gated build executes no zmm at all, so nothing is downclocked. Also,
  -march=x86-64-v4 does not define __AVX512VBMI2__; use
  -march=icelake-server or -march=sapphirerapids for the zmm path
  (corrections §5).

The surprise at the end was the two-level result. I expected the outer
"spine" (a small side array that lets you skip into the right
container) to be the winner on Intel because its stride prefetchers
love sequential multi-line reads. With the outer keys hot, a Leonard
Shar (1971) branchless binary search (bit_floor + cmov step-halving,
rediscovered by probablydance in 2023) beat the outer spine on five of
the six hosts, M4, M1, EMR, GV4 and SKX (-14% to -54%; 5/5 paired runs
in every cell except SKX hot_ser at 4/5); on the Pi 5 the two tie.
Cold, it reverses: the spine outer wins cold_bat on the Pi 5 (Shar
+31.8% slower, 0/5) and cold_ser on SKX (+16.9%, 0/5), and on EMR and
GV4 the plain branchy std::lower_bound outer is the cold-best variant
(5/5 cold_bat). Mechanism: K=512 outer keys is only ~1 KB, too short
for any stride prefetcher, so the spine descent is dependent-load
critical path. Shar's chain is serial too (load -> cmp -> csel ->
load, nine deep, not speculatable) but has no branches to mispredict,
so it wins hot; cold, the branchy bsearch gets to speculate ahead
across mispredicts and overlap the misses, the same effect Khuong &
Morin describe. Numbers: paired per-run deltas, 5 runs/host,
{host}_runs/twolevel_paired.txt, summarised in
Text/corrections_2026-10.md section 2.

The honest headline is the comparison against Lemire's own two-level
variant (bsearch outer + simd_quad inner, gap 16, no spine): with
n=4096 containers our best stack (Shar outer + compile-time n=4096
inner) is faster in all 24 host x mode cells, -35% to -84% hot and -7%
to -45% cold (paired, 5 runs, {host}_runs/twolevel_paired.txt;
corrections section 2.2). It is not a win at every container size: on
M4 Max, Lemire's variant is faster at n=48-62 and n=81-128 (hot_bat) and at
n=1-7 and n=60-156 (cold_ser) by paired per-run analysis (5/5 runs at
every size only in the 48-62 band; m4_runs/sweep_fvl_paired.txt), because the gap-64
kernel's small-n paths fall back to scalar sweeps and the spine is
inert below n=256 on 128-byte-line hosts (m4_runs/sweep_fvl_paired.txt,
corrections section 2.3). On the Pi 5 (gap 32) those hot bands do not
exist: F wins hot at essentially every size and Lemire is ahead only in
cold_ser below n~265, against both his April and his revised October
kernel (campaign sweep_fvl2, pi5_runs/sweep_fvl2_findings.md). An earlier draft quoted "426 ns -> 33 ns"
(~13x) on the Pi 5; that came from a two-mode harness whose cold query
missed the outer keys ~99% of the time and had no cache flush between
variants, and it is retracted. Under the fixed harness the same A -> F
gain on the Pi 5 is -6% to -13% per mode.

Caveats: everything is single-thread. The two-level harness flushes
the LLC (512 MB thrash) before every cold cell and uses crafted hits;
its "hot" modes keep only the 1 KB outer hot, so inner loads are
first touches (DRAM-cold on Pi 5 / SKX, L2/L3 hits on Apple / EMR /
GV4) -- cross-host "cold" comparisons compare cache levels, not
cores. bench.cpp's own "cold" column has no flush at all, so treat it
as within-host only. Arrays and spines are std::vector allocations
(16-byte aligned), so most blocks straddle two cache lines;
misalignment costs +14-30% cold at n=4096 on the Pi 5 and a Roaring
integration must align them. The Pi 5 drifts ~50% run to run
(ondemand governor), so use the paired per-run deltas, not medians of
cells. The Eytzinger+prefetch variants (H/I) measured before
2026-10-11 had a mis-aimed prefetch (corrections section 1); only the
Pi 5 has been re-measured. And I haven't wrapped this in a RoaringSet
interface yet, it's still a benchmark-driven tuning study.

Repro: ./reproduce.sh on any of the six hosts (or --quick on
smaller boxes) for the main bench; ./run_twolevel.sh HOST 10 plus
compute_twolevel_paired.py for the two-level harness. Raw outputs +
aggregators are in the *_runs/ directories; use the paired per-run
deltas ({host}_runs/twolevel_paired.txt), not per-cell medians.

Happy to take suggestions, especially on the Apple-silicon cold
regression for the compile-time n=4096 spine (the shipped hybrid;
bench_table.txt 5-run medians: M4 Max 6.50 -> 21.94 ns cold, M1 Pro
11.10 -> 32.12 ns). The current best hypothesis is a measurement-order
artifact in bench.cpp (the general-n kernel's cold pass leaves the
block line L2-warm for the next kernel, while the dedicated 4096 row
runs after its own warm sweep); it needs a flush-before-both test on
Apple hardware (corrections section 5).
```

## Logistics

- **Timing**: weekday mornings US Pacific (~9-11am PT) tend to land
  best on HN. Avoid Friday/weekend and US holidays. Tuesday through
  Thursday is ideal.
- **One submission**: don't delete + resubmit if it flops; mods notice
  and penalize. If it falls off, you can email hn@ycombinator.com
  after ~24h asking for a second-chance pool review.
- **Engage in-thread**: be around for the first few hours to answer
  technical questions. HN rewards authors who show up.
- **Lemire will likely see it.** Given he's already reviewed your
  numbers and called them "impressive", ping him before posting: the
  numbers he saw were the pre-correction ones (the ~13x cold headline
  is retracted), so point him at Text/corrections_2026-10.md (you
  already have the call scheduled). His upvote/comment on a Show HN
  tends to matter.

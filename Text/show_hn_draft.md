# Show HN post plan

## Title options

Pick one, keep under ~80 chars, no "I" or emoji per HN style:

1. `Show HN: Tuning Lemire's SIMD Quad search across six CPU families`
2. `Show HN: Per-uarch SIMD search variants for Roaring Bitmap containers`
3. `Show HN: A branchless outer + SIMD spine beats two-level bsearch ~13x cold`

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
search" post (lemire.me/blog/2025/10/25/...), which gives a neat SIMD
"quad" search for small sorted uint16_t arrays, exactly the shape that
lives inside Roaring Bitmap array containers.

I was curious how much the right answer varies by microarchitecture, so
I ran the same algorithmic shape through six host families: Raspberry
Pi 5 (Cortex-A76), Apple M1 Pro, Apple M4 Max, Intel Skylake-SP (Xeon
8175M), Intel Emerald Rapids (Xeon 8559C), and AWS Graviton 4
(Neoverse V2). Each ended up wanting different knobs:

- gap (32 vs 64) tracks cache-line size, not SIMD width. Intel with
  512-bit registers still wants gap=32 because the line is 64 B.
- Speculative in-loop prefetch is a win on Pi 5 and SKX, useless on
  M1/M4/EMR/GV4 where wide OoO + HW streamers already overlap the miss.
- On Skylake-SP, any zmm op trips the AVX-512 frequency license and
  downclocks the surrounding scalar interpolation loop enough that the
  zmm block check loses to a 2x 256-bit AVX2 fallback. Gating the zmm
  path on __AVX512VBMI2__ (Ice Lake-SP+) turns out to be a decent
  proxy for "the frequency penalty is gone".

The surprise at the end was the two-level result. I expected the outer
"spine" (a small side array that lets you skip into the right
container) to be the winner on Intel because its stride prefetchers
love sequential multi-line reads. Instead a Leonard Shar (1971)
branchless binary search (bit_floor + cmov step-halving, rediscovered
by probablydance in 2023) beat the outer spine on every host tested,
SKX, EMR, Pi 5, M1, M4, GV4. The mechanism is the same everywhere:
K=512 outer keys is only ~1 KB, way too short for any stride
prefetcher, so the spine descent is pure dependent-load critical
path, which Shar replaces with ~9 independent cmov-gated loads.

Biggest cold-cache win I measured: Pi 5 two-level lookup, 426 ns with
a naive std::lower_bound outer + general-n inner, 33 ns with Shar
outer + compile-time-n=4096 inner. That's the ratio that matters for
first-touch Roaring workloads.

Caveats: everything here is single-thread, the "cold" bench has one
query per dataset per variant so only the first variant is a true
cold miss, and I haven't wrapped this in a RoaringSet interface yet,
it's still a benchmark-driven tuning study.

Repro: ./reproduce.sh on any of the six hosts (or --quick on
smaller boxes). Raw 5-run outputs + aggregator scripts are in the
*_runs/ directories if you want to re-derive the medians.

Happy to take suggestions, especially on the Apple-silicon cold
regression for the compile-time-unrolled n=4096 spine (the one
result in the repo I don't fully understand).
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
  numbers and called them "impressive", maybe ping him before/after
  posting so he's not surprised (you already have the call scheduled).
  His upvote/comment on a Show HN tends to matter.

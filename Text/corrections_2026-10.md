# Corrections to the QuadSearch results and write-ups (2026-10-11)

A full review of this repository on 2026-10-11 (28-agent review with
adversarial verification, plus re-measurement on the Raspberry Pi 5) found
that the shipped kernels are correct and the large effects are real, but
that four measurement and aggregation defects sit under most of the
published comparisons. This document is the single authoritative list of
what was retracted, what replaces it, and where the replacement numbers
come from. Every other document in the repository (README, CLAUDE.md,
KhuongMorin.md, the talk, the Show HN draft, the one-pager, the blog draft)
was corrected against this file; if a document and this file disagree,
this file wins.

Replacement numbers in this file come from two sources:

* `{host}_runs/twolevel_paired.txt` — paired per-run re-analysis of the
  archived 2026-05-18 `bench_twolevel` runs (5 runs per host, A–I + Lem,
  variants H and I still measured with the mis-aimed prefetch of defect 1).
  Produced by `compute_twolevel_paired.py HOST`.
* `pi5_runs/twolevel_paired_v2.txt` — the repaired harness re-run on the
  Pi 5 (10 runs, randomised timing order, corrected prefetch). See
  section 6.

Conventions: deltas are `X/Y − 1` in percent, negative means X is faster.
"5/5" is the number of runs in which the first-named variant was faster.
WIN means at least 80% of runs agree in sign and the median paired delta is
at least 3%; everything else is a TIE. With five runs a sign test cannot
reach p < 0.0625, so even 5/5 is suggestive, not conclusive.

---

## 1. Defect: the Eytzinger prefetch (variants H and I) never targeted the search path

`bench_twolevel.cpp` implements Khuong & Morin's Listing 6 with
`kPrefOff = 3*kGap/2 − 1`. That constant belongs to the paper's **0-based**
layout (root at `a[0]`, children `2i+1`/`2i+2`, descendants log2(B) levels
down at `[B·i + B − 1, B·i + 2B − 2]`). The harness tree is **1-based**
(root at slot 1, children `2i`/`2i+1`, descendants at `[B·i, B·i + B − 1]`),
so every prefetch landed in the descendant line of node `i+1`, never on the
path being searched. The pad behind the array (`kGap*16` slots) was also
far too small: about half of the ~9 prefetches per query left the ~2 KB
allocation, by up to ~31 KB at gap 32 (~63 KB at gap 64).

**Fix (2026-10-11, `bench_twolevel.cpp`):** `kPrefOff = kGap/2`; the
Eytzinger array is now cache-line aligned (so one node's descendant block
is exactly one line, as the paper assumes) and padded by
`kGap·(K+1)` slots so no prefetch leaves the allocation. In the review's three-run A/B on this Pi 5 (`pi5_runs/eytz_offset_ab/`, 100 sets × 200 reps, 2026-10-10) the corrected, line-aligned prefetch (variant I4, masked) was faster than the shipped offset in every run: cold_bat -31% to -10%, cold_ser -51% to -21%, hot modes −1.5% to −6.2% (the gated variant I3: cold_bat -35% to -16%, cold_ser -55% to +3%); the shipped offset was slower than no prefetch at all in 5 of 6 cold cells (cold_bat +11% to +20%) and 4–7% slower hot.

**Consequence:** every H/I number recorded before 2026-10-11 on every host
(KhuongMorin.md tables, CLAUDE.md, plot.py `*_twolevel` dicts, the
two-level bar chart, bench_table.txt) measured a mis-aimed prefetch. The
"runahead via software prefetch" and "WL > log B bandwidth contention"
narratives in KhuongMorin.md explained numbers produced by that bug. The
corrected variants have been re-measured on the Pi 5 only (section 6); the
other five hosts need `./run_twolevel.sh HOST 10` with a rebuilt harness.

Also note: variant I pays one extra dependent load that F never pays
(`eytz_to_sorted[i]`, then `keys[sorted_idx]`), so the cold I-vs-F
comparison is structurally biased by about one memory round trip
independent of any prefetch.

## 2. Defect: per-cell medians across drifting runs

Every `{host}_runs/compute_twolevel.py` took, per variant and mode, the
median over runs of that variant's cell, and the write-ups differenced
those medians. Whole runs drift 1.4–2.2× on the Pi 5 (governor hops) and
up to 1.5× on the M4 Max, so the medians of different variants come from
different runs and their ratio can invert the ordering that every single
run shows. The harness has always printed paired "X vs Y" deltas per run;
the aggregators discarded them.

**Fix:** `compute_twolevel_paired.py` (new) recomputes paired per-run
deltas for every pair, per-run ranks, sign counts and run-level drift, and
writes `{host}_runs/twolevel_paired.txt`. The per-cell medians remain
valid as *levels* and are now labelled as such.

### 2.1 Best variant per mode by paired per-run rank (archived 2026-05-18 runs)

| host | hot_bat | hot_ser | cold_bat | cold_ser |
|---|---|---|---|---|
| Pi 5 | F (ties A, B, C, E, H, I) | E (F ties E) | **D** 5/5 | F (ties C, D) |
| M4 Max | F (I ties) | **F** 5/5 | E (F ties E) | B |
| M1 Pro | I (F ties) | I (−10.9% vs F, 4/5) | F | A |
| Skylake-SP | F | F | C (D 4/5 over F) | **D** 5/5 over F |
| Emerald Rapids | I (−0.7% vs F in 5/5, a tie by size) | **F** 5/5 | **C** 5/5 | **C** 4/5 |
| Graviton 4 | **I** 5/5 (−10.8% vs F) | **F** 5/5 | **C** 5/5 | **C** 5/5 |

Run-level drift (max/min of each run's geometric mean over variants): Pi 5
1.5–1.6× in every mode; M4 Max 1.2–1.5×; M1 Pro 1.1–1.4×; SKX 1.0–1.25×;
EMR 1.0–1.1×; GV4 1.0–1.1×.

### 2.2 Paired deltas for the pairs the write-ups quote (archived 2026-05-18 runs)

F vs D (Shar outer vs outer spine, same compile-time inner):

| host | hot_bat | hot_ser | cold_bat | cold_ser |
|---|---|---|---|---|
| Pi 5 | −6.3% (4/5) | −6.4% (4/5) | **+31.8%** (0/5, D wins) | −0.4% tie |
| M4 Max | −39.1% (5/5) | −53.9% (5/5) | −11.5% (4/5) | **+16.2%** (1/5, D wins) |
| M1 Pro | −32.4% (5/5) | −38.9% (5/5) | −10.6% (5/5) | +5.7% tie |
| SKX | −14.4% (5/5) | −16.3% (4/5) | **+6.6%** (1/5, D wins) | **+16.9%** (0/5, D wins) |
| EMR | −29.5% (5/5) | −37.1% (5/5) | −4.0% (5/5) | **+17.7%** (0/5, D wins) |
| GV4 | −41.9% (5/5) | −43.4% (5/5) | −11.3% (5/5) | +1.2% tie |

I vs F (Eytzinger + prefetch vs Shar, same inner; **pre-fix prefetch**):

| host | hot_bat | hot_ser | cold_bat | cold_ser |
|---|---|---|---|---|
| Pi 5 | +2.6% tie | **+5.8%** (I faster 1/5) | +34.6% (0/5) | +30.0% (0/5) |
| M4 Max | −0.4% tie | +16.0% (0/5) | +13.3% (1/5) | +26.4% (0/5) |
| M1 Pro | −0.3% tie | **−10.9%** (4/5, I wins) | +17.9% (0/5) | +16.3% (0/5) |
| SKX | +7.7% (0/5) | +10.3% (0/5) | +9.8% (0/5) | +13.4% (0/5) |
| EMR | −0.7% (5/5, tie by size) | +7.2% (0/5) | +28.8% (0/5) | +19.6% (0/5) |
| GV4 | **−10.8%** (5/5, I wins) | +16.4% (0/5) | +11.6% (0/5) | +28.1% (0/5) |

F vs Lem (our stack vs Lemire's published variant, n = 4096 containers):

| host | hot_bat | hot_ser | cold_bat | cold_ser |
|---|---|---|---|---|
| Pi 5 | −35.2% (5/5) | −39.3% (4/5) | −28.4% (5/5) | −16.7% (5/5) |
| M4 Max | −84.2% (5/5) | −79.6% (5/5) | −37.1% (5/5) | −42.5% (5/5) |
| M1 Pro | −68.4% (5/5) | −60.6% (5/5) | −27.7% (5/5) | −20.5% (5/5) |
| SKX | −69.0% (5/5) | −70.1% (5/5) | −29.0% (4/5) | −13.9% (5/5) |
| EMR | −69.1% (5/5) | −60.8% (5/5) | −45.2% (5/5) | −25.7% (5/5) |
| GV4 | −64.5% (5/5) | −74.1% (5/5) | −25.4% (5/5) | −7.4% (4/5) |

F vs A (the "naive two-level" baseline the README quotes):

| host | hot_bat | hot_ser | cold_bat | cold_ser |
|---|---|---|---|---|
| Pi 5 | −6.3% (3/5 tie) | −11.4% (4/5) | −12.9% (3/5 tie) | −6.4% (5/5) |
| M4 Max | −83.0% (5/5) | −46.2% (5/5) | −26.8% (5/5) | −25.8% (4/5) |
| M1 Pro | −87.6% (5/5) | −20.6% (5/5) | −68.1% (5/5) | **+26.3%** (A faster 4/5) |
| SKX | −64.0% (5/5) | −40.5% (5/5) | −24.1% (3/5 tie) | **+5.9%** (A faster 5/5) |
| EMR | −59.4% (5/5) | −48.5% (5/5) | −7.8% (5/5) | **+15.2%** (A faster 5/5) |
| GV4 | −59.3% (5/5) | −51.3% (5/5) | −28.5% (5/5) | **+14.2%** (A faster 5/5) |

G vs F: +67% to +455% hot, +13% to +129% cold, F faster in 117 of 120 run-cells (every hot run-cell; G faster only in two Pi 5 and one Skylake cold_bat runs).
The variant-G conclusion stands.

### 2.3 Sentences retracted and their replacements

* "F beats D on hot_bat and hot_ser across all six hosts, by −6.5% (Pi 5)
  up to −53% (M4 hot_ser)." → Holds on five hosts (−14% to −54%; 5/5 in every cell except SKX hot_ser, 4/5). On
  the Pi 5 it is 4/5 at −6% in the archived runs and a tie in the
  2026-10 re-runs (section 6): on the Pi 5 all of A–F, H and I are within
  about 7% of each other hot.
* The six-host "cold reversal" percentages (SKX +11.5%/+18.6%, Pi 5
  +13.3%/+4.2%, EMR −1.3%/+13.8%, M1 Pro −14.4%/+9.5%, M4 Max −6.0%/+2.7%,
  GV4 −13.8%/−0.9%) came from 2026-05-13 runs that commit 5fdbb0a
  overwrote in place; no raw file supports them. Replace with the F vs D
  table in 2.2. The cold-best variant is usually **C or D** (bsearch or
  spine outer with the compile-time inner), not F: C beats F 5/5 in both cold modes on EMR and GV4 (fastest in 5/5 GV4 runs
  and 5/5 EMR cold_bat runs, 4/5 EMR cold_ser runs), D wins cold_bat 5/5
  on the Pi 5 and cold_ser 5/5 on SKX.
* "M4 Max and GV4: no reversal, F strict-best every mode, ship F
  unconditionally." → False. GV4: C beats F in both cold modes in 5/5
  runs. M4 Max: F ties E in cold_bat and loses cold_ser to B, D and E
  (F vs E +28%, E faster 5/5). EMR likewise: C is cold-best 5/5.
* "C is cold_bat-best on Pi 5." → D is cold_bat-best on the Pi 5, 5/5
  (D vs C −15.3%).
* "F now wins cold_ser vs D on Pi 5." → Tie (−0.4%, 3/5).
* "I beats F by −22.5% on hot_ser on Pi 5, the largest dep-chain win on
  the bench; ship I for hot_ser." → Retracted. In the archived runs I is
  slower than F in 4 of 5 runs (paired median +5.8%); one F outlier run
  (481.98 ns, 2.2× its own hot_bat) produced the published median. I is
  slower than F in all six fresh runs of 2026-10-10 and in 8 of the 10
  repaired-harness runs of section 6, in both hot modes.
* "I −19.8% hot_ser on M1 Pro." → −10.9% paired, I faster in 4 of 5 runs,
  measured with the mis-aimed prefetch. Still the only hot_ser I win on
  the bench; needs re-measurement with the fixed harness.
* "I −12.0% hot_bat on GV4." → −10.8% paired, 5/5. Holds (pre-fix
  prefetch); needs re-measurement.
* "M4 Max cold_ser blowup +103.9%." → +26.4% paired (I slower 5/5). The
  dedicated mechanism paragraph explained a number that does not exist.
* "EMR hot_bat I −0.7% (tie)." → I is faster in 5 of 5 runs by 0.6–0.9%:
  consistent but too small to matter.
* "H underperforms I on all six hosts." → Mixed. Hot: H and I tie on the
  Pi 5; on GV4 H beats E 5/5 (−18%) in hot_bat. Cold: H is slower than I
  on every host.
* "Settled pattern (6 hosts): the I hot_ser win requires a slow inner and
  adequate OoO width." → Retracted as a conclusion. After pairing, the only
  hot_ser I win is M1 Pro; a one-host pattern is a hypothesis.
* "Our stack beats the published Lemire reference on every mode on every
  host." → True for **n = 4096 containers** (F faster than Lem in all 24
  cells, 5/5 in 21 and 4/5 in 3). It is **not** true across container
  sizes: the unreported M4 Max F-vs-Lemire sweep (`m4_runs/sweep_fvl_*`,
  200 sizes, 5 runs, `m4_fvl_sweep_data.py`) shows Lemire faster than F
  in the bands n = 48–62 (hot_bat, medians 25–31%), n = 81–124 (hot_bat,
  5–33%), n = 1–7 (cold_ser, 42–47%) and n = 64–95 (cold_ser, 19–35%) by
  per-cell medians. The paired per-run re-analysis of 2026-10-11
  (`m4_runs/sweep_fvl_paired.txt`, `compute_sweep_fvl.py`) keeps all four
  as WINs (Lemire faster in ≥4 of 5 runs, |median| ≥ 3%) but only 48–62 is
  5/5 at every size; the paired bands are 81–128 and 60–156 (+167–197)
  rather than 81–124 and 64–95, and smaller Lemire wins exist at hot_bat
  30–31, 146–190, 224–240, hot_ser 112–124 and cold_bat 54–62, 102–109,
  116–124. Pi 5 re-run (campaign `sweep_fvl2`, 2026-10-11/12,
  `pi5_runs/sweep_fvl2_raw.txt`, 179 sizes, 10 runs, against the 2026-04-27
  and the revised 2026-10-02 kernel; `pi5_runs/sweep_fvl2_findings.md`): no
  hot Lemire WIN at any size on the gap-32 kernel (F faster at 48–62 by
  16–33%, 10/10 at 8 of 9 sizes, and at 81–128 by 3–18%), Lemire ahead in
  cold_ser below n ≈ 265 (WIN 49 / F 1 / TIE 46 over 96 sizes, mostly
  3–14%, the same in both 5-run halves) and F above n ≈ 320 (65 / 0 / 13);
  the revised kernel changes no verdict; and the identical-code pair (both
  Lemire kernels, n ≥ 16) shows the 5-run WIN rule firing at 16–23% of
  sizes and the 10-run rule at 3–9%, so single-size 5-run bands are noise. The
  outer × inner square on the Pi 5 (campaign `sweep_fvl3`, 2026-10-12, 10 runs on
  the same arrays and targets, variants Fb = bsearch outer + spine inner and
  LemS = Shar outer + Lemire inner; `pi5_runs/sweep_fvl3_findings.md`) shows
  the cold_ser deficit at 33–265 to be the outer search: the branchy
  `std::lower_bound` costs a flat 18–33 ns per query hot at every size and
  saves a flat 45–110 ns per query cold from n ≈ 33 up, with either inner,
  while the inner is neutral or favours the spine in that range; below n = 8
  the deficit is the kernel's scalar path (`cset` return; untested lead).
  The two campaigns' Lem-vs-F verdicts agree on 592 of 716 cells with no
  contradiction. The code
  explains the bands: the gap-64 kernel's [32,64) path is one vector load
  plus a scalar sweep of up to 31 elements, the general tail scans up to 63
  elements, and the spine is inert below n = 256 on 128-byte-line hosts
  (below 128 on 64-byte-line hosts) because `num_blocks <= 3` delegates to
  the plain path.
* "Hybrid-vs-general-n ~−1.5% warm on SKX (noise)." → That number describes
  the retired unroll. The archived hybrid data (`skx_runs/hybrid_run*.txt`)
  give −32% warm, 5/5, and a +40% cold regression (paired per-run median;
  per-run −12%, +62%, +41%, +40%, −6%, so the hybrid is faster in only 2 of
  5 runs; ratio of 5-run medians +40.3%) against a general-n control that is
  stable to ±0.6% in the same runs, so "shared-tenant noise" cannot explain
  it; the SKX hybrid may have a real cold cost. (The +45.5% sometimes quoted
  is the hybrid-vs-unroll figure from `skx_runs/hybrid_summary.txt`.)
* "Pi 5 hybrid −16.9% warm" is a ratio of medians over a bimodal run set;
  the paired per-run median is −31.0%.
* "Run-to-run stability: Pi 5 warm ~5%." → Pi 5 whole-run swings are
  ~50% (`pi5_runs/twolevel_run*.txt`: F hot_bat 214–375 ns; D 229–547 ns).
  The host runs the `ondemand` governor; no archived run recorded governor,
  clock or temperature. The repaired driver records them.

## 3. Defect: the public headline numbers come from the retired harness

The "~12.9× cold speedup" (426.1 → 33.1 ns on the Pi 5), the entire
"Two-level lookup (A → F)" cold column in `Text/README.md`, and the same
numbers in `Text/presentation.md`, `Text/presentation.slides.md`,
`Text/show_hn_draft.md`, `Text/onepager.md`, `Text/friday_results.text`,
`Text/journey.text` and `Text/novelty.text` were measured before
2026-05-13 with a two-mode harness whose cold query was a random 32-bit
value: it missed the outer keys about 99% of the time and never ran the
inner search, and there was no cache flush between variants, so B–F found
the keys L2-warm after A had swept them. The project found and fixed this
(targets[si][1] crafted hits, `thrash_llc()` before every cold cell) and
re-measured everything under the 4-mode harness, but the public documents
were never updated and the README commit (2026-05-11) predates the fix.

**Replacement:** the archived 4-mode levels and the paired F-vs-A deltas in
section 2.2. On the Pi 5 the A → F gain is −6% to −13% in every mode, not
−92%. On four hosts A is *faster* than F in cold_ser. The honest headline is
the F-vs-Lemire table in 2.2 (−35% to −84% hot, −7% to −45% cold at
n = 4096), with the small-container caveat above.

Per-cell medians (levels, ns/query, archived 2026-05-18 runs) for A and F:

| host | A hb / hs / cb / cs | F hb / hs / cb / cs |
|---|---|---|
| Pi 5 | 238.2 / 284.1 / 1650.4 / 1652.3 | 244.4 / 328.5 / 1591.6 / 1547.0 |

(Other hosts: see `{host}_runs/twolevel_summary.txt`; levels for the Pi 5
are especially noisy, see section 2.) Note that on the Pi 5 the F hot_ser
median (328.5) is an artifact of the outlier run; the per-run values are
216, 340, 482, 252, 329.

## 4. Defect: the main-bench curves for five hosts had no archived source

`plot.py` carried 22-size warm/cold curves for M4 Max, M1 Pro, SKX, EMR
and GV4, but the archived `{host}_runs/rebench_run{1..5}.txt` for those
hosts hold only the ten power-of-two sizes, and at the overlapping sizes
the dict values disagreed with the archived medians (M4 cold, graviton
kernel, n = 4096: 17.4 in plot.py vs 11.7 archived; 37 of 90 M4 cold cells
more than 10% off). Only the Pi 5 curve re-derived from its archive
(396/396 cells). Two number sets circulated: archived values in CLAUDE.md,
reproduce.sh and the README; unarchived values in plot.py, bench_table.txt
and every PNG.

**Fix (2026-10-11):** plot.py now holds only values derivable from the
archived runs (ten sizes for the five hosts, 22 for the Pi 5), with a
provenance comment above every dict; the plots and `bench_table.txt` were
regenerated. The twelve non-power-of-two points per curve and the
"sawtooth" discussion built on them (`Text/experiments.md`,
`Text/aliasing_investigation.md`) have no raw source and should be treated
as unmeasured until those sizes are re-run and archived.

## 5. Other corrected statements

* **Pi 5 speculative prefetch is a net loss, not a "~10–25% cold win".**
  `simd_quad_graviton.c` is `simd_quad_pi5.c` minus the one in-loop
  prefetch (plus padded variants), so the archived Pi 5 main-bench table
  is a built-in A/B: the prefetch kernel is slower cold at 13 of 14 sizes
  from n = 128 up (+2% to +31%) and slower warm at 13 of 14 (`plot.py`
  pi5 dicts, pi5 vs graviton columns; per-run pairs in
  `pi5_runs/rebench_run*.txt` agree, e.g. n = 2048 cold 5/5). Fresh
  interleaved A/Bs in the review agreed (1–6% slower at n = 4096, 17–20%
  slower at n = 2048; only n = 1024 favoured the prefetch). No prefetch A/B
  exists anywhere in `pi5_runs/`. Structurally the prefetch address
  depends on the just-updated `base`, so it issues at the same dependency
  depth as the demand loads it is supposed to hide. The M4 and Graviton
  kernel headers restate the Pi 5 claim as the rationale for their own
  prefetch decisions; the shipped Pi 5 kernel still contains the prefetch
  (removing it is a kernel change that needs its own A/B on all sizes).
* **"One block = one cache line" is asserted but never enforced.** Arrays
  and spines are `std::vector` allocations (16-byte aligned), so about 75%
  of 64-byte blocks and 87.5% of 128-byte blocks straddle two lines, and a
  256-byte spine usually spans five lines. Interleaved aligned-vs-misaligned
  A/Bs on the Pi 5 measured a +14–30% cold penalty at n = 4096, and the
  hybrid-vs-general-n cold ordering flips with the alignment regime. A
  Roaring integration must align container arrays and spines to get the
  designed behaviour. `Text/aliasing_investigation.md`'s premise that "the
  allocator returns power-of-two-aligned blocks" is false for glibc at
  these sizes.
* **Shar's outer search is a serial cmov chain, not "nine independent
  loads in parallel".** The compiled loop is load → compare → csel → load,
  each address depending on the previous select; it cannot be speculated
  past. It wins hot because it has no branch mispredicts and no side
  structure. On cold data the *branchy* `std::lower_bound` (variants A, C)
  lets the core speculate ahead across mispredicted branches, which is why
  C is the cold winner on EMR and GV4 — the same mechanism Khuong & Morin
  report for branchy vs branch-free search out of cache.
* **The cache-state labels.** `bench.cpp`'s "cold" column had no cache
  flush in any archived run (see the update at the end of this bullet): it
  walked the arrays in allocation order with the same targets the previous
  algorithm had just used, and the ~35 MB footprint fits the LLC of
  every host except the Pi 5 (and at n ≤ 256 is L2/L3-resident on the Pi 5
  too). `bench_twolevel`'s "hot" modes keep only the 1 KB outer hot: each
  set's 200 reps touch ~91 distinct containers once each, so inner loads
  are first touches (DRAM-cold on Pi 5 / SKX, L2/L3 hits on Apple / EMR /
  GV4). Measured on the Pi 5: F hot_bat 61 ns at 12 sets, 172 ns at 48,
  213 ns at 200. Hot modes also send ~50% outer-miss queries while cold
  modes are 100% crafted hits. Cross-host "cold" comparisons therefore
  compare cache levels, not cores.
  *Update, later on 2026-10-11:* `bench.cpp` now calls a copy of the
  two-level harness's 512 MB `thrash_llc()` before every cold pass and prints a
  `# cold column:` provenance line (nothing renamed). The description above
  holds for every archived `rebench_run*.txt` (none has the line) and for
  the `plot.py` dicts and figures built from them; the first flushed run is
  `pi5_runs/rebench_flushed_run1.txt` (Pi 5, 2026-10-12, one run, pinned to
  core 3, `# key: value` header lines with date, build, compiler, governor
  and temperature); no other host has been re-run. What that one run shows
  (levels, not verdicts): (a) the flush evicts at canonical intensity — the
  n = 8 cold cells are 38–74 ns against 5–18 ns in the archive, and the
  n = 4096 spine cells sit 1.3–1.5× above the archived level (`pi5s` 223 ns
  against 146–160; `pi5` 382 against 289–319), so pre-flush only the array
  lines were cold on the Pi 5 while the 1 MB of spines, the pointer and
  target vectors and probably the TLB were warm; the spine's cold win at
  n = 4096 stands (`pi5s` −42% against `pi5`; archive −50%); (b) flushed,
  the m4 hybrid is faster cold than the general-n m4 spine on the Pi 5
  (`m4_spine_4096` 194.9 ns against `m4_spine` 211.6, −8%) where the
  pre-flush archive had it slower in 4 of 5 runs (+2% to +18%) — consistent
  with the measurement-order explanation of the Apple regression below, but
  one run on the wrong host; (c) the warm cells match the archive's fast
  mode within ±6% at every size (`pi5s` at n = 23: +15%), which exposes a
  property of the archive: the five `rebench_run*.txt` have a slow mode
  1.45–1.50× above the fast one, uniform across the nine columns of a row
  (1.47–1.51 at n = 16 — consistent with a clock step under `ondemand`,
  2.4 GHz against ~1.6); run 1 is slow at almost every size and run 5 at
  none, so the `plot.py` Pi 5 warm medians inherit the slow mode at n = 11,
  16, 23 and 128 in most columns and in single columns at 8, 32 and 512
  (within-row A/Bs unaffected; absolute small-n warm levels inflated by up
  to 1.5×), while the flushed run sat in the fast mode throughout — the
  512 MB thrash between cold passes plausibly keeps the clock up; (d) the
  `linear` baseline column is 2.5–3.5× faster than the archive from n = 64
  up (633 against ~2,200 ns warm at n = 4096) because GCC 17.0.0 (20260704)
  auto-vectorizes `std::find` over `uint16_t` (`-fopt-info-vec`: "loop
  vectorized using 16 byte vectors"); the archive was built with
  GCC 15 (`plot.py` provenance comment; the run files record no compiler,
  the flushed-run header does) — a toolchain change, not the flush, in a
  baseline column, not a studied kernel. The two-level "hot" caveat is unchanged.
* **Variant A was always timed first with no warm-up**, so its hot cells
  carried first-touch costs; the repaired harness runs an untimed warm-up
  pass and randomises the timing order.
* **Spine mechanism.** The spine's cold win is memory-level parallelism over
  a short contiguous read: the descent touches a few adjacent lines instead
  of chasing probes through the 8 KB array. A 256-byte spine is too short to
  train a stride prefetcher, so write-ups that credited hardware "streamers"
  for the win (talk, one-pager, ELI5, journey) were corrected; the 2–3× cold
  win at n = 4096 itself stands.
* **Microarchitecture facts.** `-march=x86-64-v4` does not define
  `__AVX512VBMI2__`, so that documented build silently produces the AVX2 +
  prefetch (Skylake) variant; use `-march=icelake-server` or
  `-march=sapphirerapids`. Zen 4 and Zen 5 define VBMI2, so the "Ice Lake
  or newer" proxy also selects the zmm path on AMD, untested. On Skylake-SP
  512-bit integer compares trip license level L1, not L2, and the shipped
  gated build executes no zmm instruction at all, so nothing is downclocked
  and "kept because the scalar loop is downclocked" is not a reason for the
  SKX prefetch. The Emerald Rapids 8559C core is Raptor Cove (not Granite
  Rapids, not Redwood Cove). The review reported Neoverse V2 has three
  load pipes rather than four (not verified on hardware here). M1 Pro runs
  at about 0.72× the M4 Max clock, not half. `thrash_llc()` was 256 MB,
  smaller than the 8559C's 260 MB L3; it is now 512 MB.
* **The Graviton and Pi 5 spine kernels are the same code.** After
  stripping comments, every `simd_quad_graviton_spine*` function is
  identical to its `simd_quad_pi5_spine*` counterpart; only the general-n
  non-spine kernel differs (the prefetch line). The `pi5s` and `gv4s`
  columns of `bench` therefore duplicate each other, and the hardware
  table's block-check descriptions ("x2 + 2 cmp" vs "x2 + 4 cmp") are
  wrong for both: both do two `vld1q_u16_x2` loads and four compares.
* **The Apple `_spine_4096` "structural cold regression" may be a
  measurement-order artifact.** In the pre-flush `bench.cpp` the spine
  kernel's cold pass ran right after the non-spine kernel's cold pass with
  identical targets, so the block line was an L2 hit on Apple's large L2,
  while the dedicated `4096*` row ran after its own 32 MB warm sweep. The reported
  gap matches L2-hit vs SLC-hit latencies and the same asymmetry
  reproduces on the Pi 5. This is a hypothesis that needs a test on Apple
  hardware (run both measurements after an explicit flush; since later on
  2026-10-11 `bench.cpp` does exactly that, so the test is a re-run on
  M1/M4; on the Pi 5 the first flushed run, 2026-10-12, removes the
  asymmetry — point (b) of the cache-state bullet's update). The OpenEvolve
  starting program is also the retired unroll, not the shipped hybrid.
* **Provenance.** CLAUDE.md is gitignored yet is the only record of most
  decisions; `bench_twolevel.cpp` cited a "fix note in CLAUDE.md" that did
  not exist (the note is now in the harness itself, above
  `bench_cold_batched`); KhuongMorin.md's pre-registered predictions live
  in a private plans file outside the repository and cannot be audited.

## 6. Status of re-measurement with the repaired harness

**Pi 5 (this host):** ten runs of the repaired harness on 2026-10-11
(`pi5_runs/twolevel_v2_run{1..10}.txt`, pinned to one core, `ondemand`
governor, 50–60 °C, order randomised per run), aggregated to
`pi5_runs/twolevel_paired_v2.txt`. The archived 2026-05-18 files were left
untouched. Hot run-level drift fell from 1.5–1.6× to 1.09–1.12× with the
warm-up pass and pinning; cold drift is still 2.4–2.9× because each cold
cell is a single pass of 200 queries (~300 µs), so cold verdicts need the
sign counts, not the medians.

Best variant by mean paired rank: **D in hot_bat (fastest in 7/10), D in
hot_ser (8/10), D in cold_bat (7/10)**; cold_ser is noise (seven different
winners in ten runs, C best by mean rank).

| pair (X vs Y) | hot_bat | hot_ser | cold_bat | cold_ser |
|---|---|---|---|---|
| F vs D | +2.7% (F faster 2/10) tie | +2.0% (1/10) tie | **+44.7%** (0/10, D wins) | −5.6% (6/10) tie |
| D vs A | −10.3% (10/10) | −15.0% (10/10) | −39.0% (9/10) | −6.6% (6/10) tie |
| F vs A | −7.7% (9/10) | −12.4% (9/10) | −9.9% (6/10) tie | −11.8% (7/10) tie |
| I vs F (fixed prefetch) | **+7.3%** (I faster 2/10, F wins) | **+8.6%** (2/10, F wins) | −2.5% (5/10) tie | +39.9% (3/10) tie |
| H vs E (fixed prefetch) | +5.6% (2/10, E wins) | +10.0% (1/10, E wins) | +13.3% (2/10, E wins) | +12.9% (4/10) tie |
| I vs D | +10.2% (0/10) | +11.1% (0/10) | +53.2% (0/10) | +18.1% (2/10) |
| F vs Lem | −37.5% (10/10) | −39.4% (10/10) | −17.3% (7/10) tie | −30.5% (8/10) |
| D vs Lem | −39.3% (10/10) | −40.7% (10/10) | −49.1% (10/10) | −19.7% (6/10) tie |
| G vs F | +68.5% (0/10) | +67.7% (0/10) | +17.5% (2/10) | +31.3% (1/10) |

Levels (median of 10, ns/query): hot_bat A 235.9, B 215.6, C 231.0,
D 209.7, E 214.9, F 214.5, G 359.4, H 231.1, I 228.6, Lem 347.0;
hot_ser A 249.5, B 216.7, C 243.7, D 209.7, E 213.8, F 216.6, G 359.6,
H 235.6, I 232.9, Lem 353.6.

What this settles for the Pi 5: with the prefetch aimed correctly the
Eytzinger variants stop being catastrophic cold (I ties F in cold_bat
instead of +35%) but are still 7–9% slower than Shar or the outer spine
hot and never beat D anywhere, so the Khuong & Morin outer does not pay
off on this core. The **Pi 5 ship recommendation is D** (outer spine +
compile-time n=4096 inner): tied-best hot with B and F (E is within 3%,
but D is faster in 8 of 10 hot_bat runs), and the only variant that wins
cold_bat. F is a hot tie and loses cold_bat by 45%.

**Other hosts:** not yet re-measured. Rebuild `bench_twolevel` with the
host's build line, then

```
./run_twolevel.sh HOST 10
python3 compute_twolevel_paired.py HOST --glob 'HOST_runs/twolevel_v2_run*.txt' --out HOST_runs/twolevel_paired_v2.txt
```

Until that is done, every H/I statement for M4 Max, M1 Pro, SKX, EMR and
GV4 is "measured with the mis-aimed prefetch", and the plot.py two-level
dicts keep the 2026-05-18 levels with H/I labelled accordingly.

**Not changed by this correction pass (open items):** the Pi 5 kernel's
in-loop prefetch (evidence says remove it; needs a kernel A/B), cache-line
alignment of `carr`/spine in the harnesses and kernels, a real cache flush
for `bench.cpp`'s cold column, the F-vs-Lemire small-container bands (a
size-dependent dispatch or a shorter scalar tail for n < 128), the
hygiene items (tracked binaries, third-party PDFs/scans, 7,600 one-line
sweep files, stale PNG copies). The hygiene items were addressed later
on 2026-10-11 (binaries untracked; PDF, scans and `Images/` removed from
the tip and cited in `THIRD_PARTY_NOTICES.md`; sweep files folded into
`*_raw.txt`; the published history was rewritten the same day to purge
the PDF, the scans and the binaries). The cache flush for `bench.cpp`'s
cold column was also added later on 2026-10-11 (see the update in section
5); the archived main-bench runs predate it, and the first flushed run
(Pi 5, one run) followed on 2026-10-12 as `pi5_runs/rebench_flushed_run1.txt`.

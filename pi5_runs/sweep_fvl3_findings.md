# Outer search versus inner kernel across container sizes on the Raspberry Pi 5 (campaign `sweep_fvl3`, 2026-10-12, 10 runs)

The previous campaign (`sweep_fvl2`, `pi5_runs/sweep_fvl2_findings.md`)
left one verdict against our stack on the Pi 5: in cold_ser Lemire's
published variant is ahead below n ≈ 265 while F wins hot at every size.
The hypothesis was that this is the *outer* search — the branchy
`std::lower_bound` lets the core speculate loads past mispredicted
branches, Shar's cmov chain cannot — and not the inner kernel. This
campaign tests it by completing the {Shar, bsearch} outer × {spine,
Lemire} inner square: the harness gained Fb (bsearch outer + our spine
inner, i.e. two-level variant A at every n) and LemS (Shar outer +
Lemire's April inner), so Fb vs F and Lem vs LemS isolate the outer
search with each inner, and Fb vs Lem and F vs LemS isolate the inner
kernel with each outer. Every cell searches the same arrays with all
five variants, and the arrays and targets are the same as `sweep_fvl2`'s
draw for draw (see Setup), so the Lem vs F verdicts of the two campaigns
are also a reproducibility test of the 10-run WIN rule.

**Result: confirmed.** On the Cortex-A76 the branchy outer costs a flat
18–28 ns per query in hot_bat and 28–33 ns in hot_ser at every size with
either inner, and saves a flat 45–110 ns per query in both cold modes
from n ≈ 33 up, with either inner. Between n = 33 and 265 the inner
kernel is neutral or favours the spine, so Lemire's cold_ser advantage
there is entirely the outer search. Below n = 8 the picture inverts (the
deficit is the inner; see result 4), and above n ≈ 300 the spine's cold
gain outgrows the flat outer penalty, which is the crossover
`sweep_fvl2` saw.

## Setup

| item | value |
|---|---|
| harness | `bench_sweep_f_vs_lem.cpp` (five variants since 2026-10-12) built with `g++ -O3 -mcpu=cortex-a76 -std=c++20 -DQUADSEARCH_ARM_PI5 bench_sweep_f_vs_lem.cpp simd_quad_pi5.c -o /home/pi/bench_sweep_fvl3` (GCC 17.0.0 20260704, binary on local disk, built 2026-10-12 13:38, used for all ten runs) |
| variants | F = Shar outer + `simd_quad_pi5_spine` inner; Lem = `std::lower_bound` outer + `simd_quad` (2026-04-27); Lem2 = `std::lower_bound` outer + `simd_quad_2026_10` (2026-10-02); **Fb** = `std::lower_bound` outer + `simd_quad_pi5_spine` inner (two-level variant A at every n); **LemS** = Shar outer + `simd_quad` (2026-04-27). All five search the same container set within a cell. |
| sizes | 179 (`pi5_runs/sweep_n_list_f_vs_lem.txt`), 1–4096 |
| modes | hot_bat, hot_ser, cold_bat, cold_ser (512 MB thrash before every cold variant) |
| intensity | 100 sets × 200 reps per cell; 10 runs with `order_seed` = run index; the variant timing order is shuffled per cell and all 120 orders of five variants occurred |
| inputs | identical to `sweep_fvl2`'s: the set-up generator was switched from `std::set` to a 65,536-bit membership bitmap that makes the same draws in the same order; `check_sweep_generator.cpp` ran both generators in lockstep over all 179 sizes at 100 sets (9,182,700 arrays, 0 mismatches, RNG states identical). Only the heap layout changes; a cell now takes 0.2–4.3 s instead of up to 24 s. |
| host state | pinned to core 3 with `taskset`, governor `ondemand`, nothing else running; 2026-10-12 14:01:15–16:17:01, 8,098 s, SoC 54.0–61.7 °C |
| cells | 7,160 of 7,160, 0 failed, no correctness mismatch; `pi5_runs/sweep_fvl3_raw.txt` (per-cell outputs folded by `consolidate_sweep.py`, verified verbatim before the per-cell files were deleted); driver log `pi5_runs/sweep_fvl3_driver.log` |
| analysis | `python3 compute_sweep_fvl.py pi5 --prefix sweep_fvl3` → `pi5_runs/sweep_fvl3_paired.txt`, `pi5_sweep_fvl3_data.py`; `python3 plot_sweep_fvl.py pi5 --prefix sweep_fvl3` → `bench_pi5_sweep_fvl3.png` (levels), `bench_pi5_sweep_fvl3_delta.png` (Lem/Lem2 vs F), `bench_pi5_sweep_fvl3_factorial.png` (the four single-factor contrasts, percent and ns) |
| rule | per cell, delta = B/A − 1 in each run; WIN(X) = X faster in ≥ 8 of 10 runs and \|median delta\| ≥ 3%, else TIE. Absolute deltas are B − A in ns per run, median over runs; a band figure is the median over the band's sizes of those per-size medians. Levels are never differenced across variants. |

Run-level drift (geometric mean over the 895 (N, variant) cells, max/min
across runs): hot_bat 1.04×, hot_ser 1.08× (run 6: 165.6 ns against
153.4–160.2), cold_bat 1.04×, cold_ser 1.03× — lower than the idle half
of `sweep_fvl2` (1.03× / 1.02× / 1.17× / 1.07×).

## Noise gauge: Lem2 vs Lem from n = 16 up (identical source, 164 sizes)

| campaign | hot_bat | hot_ser | cold_bat | cold_ser |
|---|---|---|---|---|
| `sweep_fvl3` WINs | 9 (5%) | 5 (3%) | 27 (16%) | 13 (8%) |
| \|median\| p90 / max | 3.4% / 6.7% | 3.5% / 7.7% | 5.7% / 16.5% (n = 39) | 4.7% / 10.0% |
| `sweep_fvl2` WINs | 6 (4%) | 5 (3%) | 14 (9%) | 14 (9%) |
| \|median\| p90 / max | 4.6% / 13.3% | 3.8% / 5.5% | 5.0% / 11.9% | 4.4% / 14.9% |

The cold_bat gauge fired more often this time (27 sizes, 21 of them with
the April kernel ahead, 9 of those at 109–265), so a single cold_bat cell
below ~6% — occasionally 10–16% — means nothing on its own; hot cells
over ~7% and cold_ser cells over ~10% are outside the gauge. Everything
quoted below is a band of consecutive sizes or a cell far outside these
limits.

## Results

**1. The outer search: a flat hot cost and a flat cold gain, independent
of the inner kernel.** Paired medians of B − A in ns (percent in
brackets) by size band, bsearch outer minus Shar outer:

| band | Fb − F hot_bat | hot_ser | cold_bat | cold_ser | Lem − LemS hot_bat | hot_ser | cold_bat | cold_ser |
|---|---|---|---|---|---|---|---|---|
| 1–32 | +27 (+46%) | +28 (+49%) | +36 (+6%) | −4 (−1%) | +28 (+47%) | +30 (+56%) | +11 (+2%) | −30 (−5%) |
| 33–128 | +24 (+25%) | +33 (+34%) | −9 (−1%) | −46 (−6%) | +22 (+24%) | +32 (+33%) | −46 (−7%) | −65 (−9%) |
| 129–265 | +21 (+13%) | +34 (+22%) | −52 (−7%) | −82 (−10%) | +23 (+17%) | +32 (+23%) | −110 (−13%) | −95 (−11%) |
| 266–512 | +18 (+10%) | +33 (+19%) | −104 (−12%) | −88 (−10%) | +24 (+14%) | +31 (+18%) | −99 (−10%) | −97 (−10%) |
| 513–1024 | +18 (+10%) | +33 (+19%) | −112 (−12%) | −84 (−9%) | +23 (+12%) | +32 (+15%) | −89 (−8%) | −84 (−8%) |
| 1025–2048 | +18 (+9%) | +33 (+17%) | −111 (−12%) | −83 (−9%) | +21 (+9%) | +31 (+13%) | −98 (−8%) | −94 (−8%) |
| 2049–4096 | +18 (+9%) | +33 (+16%) | −60 (−6%) | −55 (−5%) | +22 (+8%) | +31 (+11%) | −94 (−7%) | −72 (−5%) |

Hot, the Shar outer wins at every size with either inner: Fb vs F is
WIN(F) at 176 of 179 sizes in hot_bat (TIE at 137, 167 and 1058) and
179 of 179 in hot_ser; Lem vs LemS is WIN(LemS) at 177 (TIE at 75 and
86) and 179. The cost of the branchy outer is 18–28 ns per query in
hot_bat and 28–33 ns in hot_ser whatever the size and whatever the
inner; in percent it falls from +46% at n ≤ 32 to +9% at n ≥ 2049 only
because the inner grows.

Cold, the branchy outer is faster from n ≈ 33 up with either inner, again
by a roughly constant 45–110 ns per query: Fb vs F cold_ser is WIN(Fb)
at 102 sizes, WIN(F) at 2 (n = 8 and 16) and TIE at 75 — WIN(Fb) at 95
of the 126 sizes between 46 and 2849 — and cold_bat WIN(Fb) 91 / WIN(F)
23 (all at n ≤ 45) / TIE 65 (89 of 126 between 46 and 2849). Lem vs
LemS: cold_ser WIN(Lem) 127 / WIN(LemS) 2 (n = 2, 4) / TIE 50 (103 of
126), cold_bat 112 / 8 / 59 (104 of 126). Above n ≈ 2900 the band
medians are still −55 to −94 ns but the sign counts drop to ~70% of the
cells and only 1–3 of the 11 sizes are WINs; whether the effect fades
or the largest cold cells (1,100–1,500 ns per query) are simply noisier
the data cannot say.

The two inners agree on the size of the outer effect: the interaction
(Fb − F) − (Lem − LemS) is within ±8 ns at every band hot and +7 to
+59 ns cold (the bsearch gain is somewhat smaller with the spine inner
than with the Lemire inner below n = 266, cold_bat 33–265 by 50–60 ns),
inside the per-size cold noise. This is Khuong & Morin's
branchy-versus-branch-free result at the outer level, measured directly:
the cmov chain has no mispredicts (hot win) and cannot be speculated
past a miss (cold loss).

**2. The inner kernel: the spine pays from eight blocks up, in every
mode, and its gain grows with n.** Spine inner minus Lemire inner, ns
(percent):

| band | Fb − Lem hot_bat | hot_ser | cold_bat | cold_ser | F − LemS hot_bat | hot_ser | cold_bat | cold_ser |
|---|---|---|---|---|---|---|---|---|
| 1–32 | +4 (+5%) | +2 (+2%) | +8 (+1%) | +8 (+1%) | +3 (+7%) | +3 (+6%) | −4 (−1%) | −31 (−5%) |
| 33–128 | +3 (+3%) | +3 (+2%) | −15 (−2%) | +6 (+1%) | +2 (+2%) | +2 (+3%) | −60 (−9%) | −21 (−3%) |
| 129–265 | +12 (+8%) | +17 (+10%) | −50 (−6%) | −39 (−5%) | +16 (+12%) | +15 (+11%) | −102 (−12%) | −34 (−4%) |
| 266–512 | −8 (−4%) | −2 (−1%) | −168 (−19%) | −118 (−13%) | −3 (−2%) | −2 (−1%) | −172 (−17%) | −128 (−13%) |
| 513–1024 | −33 (−14%) | −24 (−10%) | −252 (−25%) | −199 (−19%) | −26 (−13%) | −27 (−13%) | −222 (−21%) | −186 (−17%) |
| 1025–2048 | −56 (−22%) | −53 (−19%) | −260 (−23%) | −227 (−19%) | −54 (−22%) | −54 (−22%) | −249 (−21%) | −220 (−18%) |
| 2049–4096 | −82 (−27%) | −77 (−24%) | −271 (−20%) | −274 (−20%) | −78 (−28%) | −80 (−28%) | −277 (−21%) | −277 (−20%) |

From n = 513 up the spine inner is a WIN at every size in every mode
with either outer (Fb vs Lem hot_bat 63 of 63, cold_ser 58 of 63; F vs
LemS cold_bat 56 of 63), and from 266 up in the cold modes (17–21 of
the 20–21 sizes per band). Hot, the spine is neutral below 128 (+2 to
+4 ns) and *slower* than Lemire's gap-16 quat search at 129–265: Fb vs
Lem +3.5% to +12% (WIN(Lem) at 19 of 22 sizes), F vs LemS +7% to +17%
(20 of 22), 6–22 ns per query. The spine engages at four blocks
(n = 128) and breaks even hot at eight (n = 256: Fb vs Lem −3.3% at 6/10,
F vs LemS −3.7%, WIN(F) 8/10). Cold it already pays at 129–265 (−39 to
−102 ns).

**3. Where the `sweep_fvl2` verdicts come from.** The hot_bat TIE zone
(this campaign: 13 sizes at 128, 137–156, 167, 172, 184, 190, 210, 217
and 224; `sweep_fvl2`: 22 sizes between 105 and 248) is the Shar outer's
gain (+12 to +25 ns, Fb vs F +8% to +16%, WIN(F) at 20 of the 22 sizes
in 129–265) cancelled by the spine inner's loss at four to seven blocks
(6–22 ns, result 2); net, Lem vs F is +1 to +15 ns there. The cold_ser
deficit: at n ≤ 265 Lem vs F is WIN(Lem) 46 / WIN(F) 2 / TIE 48
(`sweep_fvl2`: 49 / 1 / 46), and in the same range the outer accounts for
all of it — Fb vs F is WIN(Fb) at 22 of the 42 sizes in 33–128 (−46 ns)
and 20 of 22 in 129–265 (−82 ns) while the inner is neutral or favours
the spine (F vs LemS −21 and −34 ns, WIN(F) at 18 of 42 and 12 of 22;
Fb vs Lem +6 ns tie and −39 ns, 12 WIN(Fb) / 1 / 9). Above n ≈ 300
(n ≥ 273: Lem 0 / F 65 / TIE 18) the spine's cold gain over the Lemire
inner (−118 ns at 266–512, growing to −274 at 2049–4096) outgrows the
flat outer penalty (−88 to −55 ns), which is the crossover.

**4. Below n = 32 the square is not additive, and the n ≤ 7 cold_ser
deficit is the inner kernel, not the outer.** Cells here differ by
50–130 ns from one size to the next and the two outer pairs disagree:
with the spine inner, Fb vs F cold_ser is a TIE at 26 of the 32 sizes
(band −4 ns), WIN(Fb) at 6, 7, 22 and 27 and WIN(F) at 8 and 16 (+53
and +61 ns); with the Lemire inner, Lem vs LemS is WIN(Lem) at 16 of 32
(−30 ns; 6–7, 9–11, 16, 19–20, 22–23, 25–28, 30, 32). cold_bat at 1–32 has
the Shar outer *faster* with the spine inner (WIN(F) at 16 of 32,
+36 ns) and a tie with Lemire's. The inner contrast is just as
size-specific: Lemire's kernel is faster at n = 1–5 in cold_ser with the
Shar outer (F vs LemS +10% to +19%, +56 to +92 ns, LemS faster in 8–10
of 10 runs at each size) and at 1–2 and 5–6 with the bsearch outer (Fb
vs Lem +6% to +10%, +38 to +55 ns), so the `sweep_fvl2` Lemire WINs at
n = 1–3 and 5–6 (−11% to −15%) are the inner; our kernel is faster at
8–10 (F vs LemS −17% to −21%, −122 to −133 ns; Fb vs Lem −8.6% at 8), at
13 (−7%) and at 12 of the 17 sizes from 16 to 32 (F vs LemS −4% to −16%),
with n = 11 (−15%, 7/10) and the rest ties.

F's own cold levels follow the structure of its small-n code: cold_ser
578–635 ns per query at n = 1–7, 507 at n = 8, rising 525–647 through
9–15, 506 at n = 16, rising again through 17–31 (cold_bat: 498–614 at
1–7, 505 at 8, 502 at 16). In the compiled code (GCC 17, `-O3
-mcpu=cortex-a76`) both kernels' small-n loops are auto-vectorised with
early-break vectorisation, but they return differently: Lemire's
equality loop becomes a peeled scalar prologue plus one `cmeq` block in
which every exit is a branch to `mov w0, 1` or `mov w0, 0` (a constant
return), while the Pi 5 kernel's `if (x >= pos) return x == pos;`
sweeps become unrolled `ldrh; cmp; bls` chains whose exit block is
`cmp; cset w0, eq; ret` — a return computed from the loaded value; only
its vector checks (`vmaxvq != 0 → return true`, i.e. a hit in the first
8 or 16 elements) return a constant through a branch. Hypothesis, not
yet tested: in the serial chain (`t = target ^ carry`) a constant
return reached by a correctly predicted branch lets the core start the
next query's outer search before the inner line arrives, and a
mispredicted exit flushes whatever the next query had started, whereas
a `cset` return allows no overlap at all; that would put F fast exactly
at n = 8 and 16 (every hit in the vector, every return a predicted
constant), slow at n ≤ 7 (every return a `cset`) and in between
elsewhere. The test is a kernel A/B at n ≤ 31 with the scalar sweeps
rewritten as `if (x == pos) return true; if (x > pos) return false;`.
The hot modes do not care: F beats Lemire's kernel hot at n = 1–7 by
40–60% through the outer, and the inner alone (F vs LemS) costs 3 ns
there.

**5. n = 4096 against the two-level harness.** Outer: Fb vs F +8.5% /
+15.0% hot (0/10 — the bsearch outer costs 17 / 31 ns), cold_bat +8.3%
TIE (Fb faster 3/10, +101 ns), cold_ser −5.6% WIN(Fb) (9/10, −67 ns);
Lem vs LemS +7.9% / +9.2% hot (0/10, 1/10), cold ties (+5 ns both). The
repaired two-level harness measured the same contrast as A vs E (10
runs): E faster hot by 8.6% / 13.2% (9/10, 10/10), cold a TIE (+10.2% /
+3.4%, A faster 4/10) — consistent. Inner: Fb vs Lem −31.5% / −29.6%
hot (10/10, −103 / −102 ns), −18.5% cold_bat (9/10, −271 ns), −20.4%
cold_ser (10/10, −346 ns); F vs LemS −32.6% / −33.2% hot (10/10),
−21.5% cold_bat (10/10, −360 ns), −18.4% cold_ser (8/10, −263 ns). So at
the container maximum the spine inner is worth ~100 ns per query hot
and 260–360 ns cold, the Shar outer +17–31 ns hot and −67 ns cold_ser.

**6. Lem vs F replicates `sweep_fvl2` cell for cell: the 10-run rule
never contradicted itself.** Verdicts (Lem / F / TIE over 179 sizes):

| mode | `sweep_fvl3` | `sweep_fvl2` | same verdict | WIN↔TIE flips | contradictions | median / p90 of \|Δ paired median\| |
|---|---|---|---|---|---|---|
| hot_bat | 0 / 166 / 13 | 0 / 157 / 22 | 166 | 13 | 0 | 3.0 / 8.8 points |
| hot_ser | 0 / 176 / 3 | 0 / 174 / 5 | 175 | 4 | 0 | 3.2 / 9.6 |
| cold_bat | 13 / 89 / 77 | 10 / 102 / 67 | 131 | 48 | 0 | 4.1 / 12.8 |
| cold_ser | 46 / 67 / 66 | 49 / 67 / 63 | 120 | 59 | 0 | 2.8 / 7.8 |

Two independent ten-run campaigns on identical inputs (different heap
layout, different variant orders, a different day) agree on 592 of the
716 cells and never call opposite winners; the flips are WIN↔TIE, 2–7%
of sizes hot and 27–33% cold. One of them is the n = 4096 cold_ser cell:
WIN(F) +30.9% (8/10) in `sweep_fvl2`, here +17.5% with F faster in 7
of 10 (TIE); the two-level harness has it at −30.5% (8/10). The cold_ser
split by size is the same (n ≤ 265: 46 / 2 / 48 against 49 / 1 / 46;
n ≥ 273: 0 / 65 / 18 against 0 / 66 / 17).

**7. Lemire's revision replicates.** Below n = 16, where the code
differs, Lem2 is faster than Lem in hot_bat at n = 2–13 (−4% to −14%;
`sweep_fvl2`: 3–13, 4–18%) and cold_bat at 8–11 and 13–14 (−4% to
−14%); the April kernel is faster in hot_ser at 12–15 (+5% to +11%) and
Lem2 in cold_ser at 13–15 (−9% to −10%). Against F the revision again
changes no verdict class (Lem2 vs F: hot_bat 0 / 165 / 14, hot_ser 0 /
174 / 5, cold_bat 6 / 96 / 77, cold_ser 37 / 70 / 72). From n = 16 up
the pair is the noise gauge above.

## Levels for orientation (per-cell medians over ten runs, ns/query; do not difference across variants)

| n | mode | F | Lem | Lem2 | Fb | LemS |
|---|---|---|---|---|---|---|
| 1 | hot_bat / hot_ser | 42.0 / 43.6 | 66.6 / 66.6 | 68.2 / 73.7 | 70.1 / 77.3 | 38.9 / 39.7 |
| 1 | cold_bat / cold_ser | 514 / 577 | 539 / 534 | 543 / 544 | 544 / 571 | 498 / 501 |
| 128 | hot_bat / hot_ser | 134.7 / 142.3 | 146.7 / 160.0 | 154.9 / 156.4 | 157.5 / 172.4 | 123.7 / 131.0 |
| 128 | cold_bat / cold_ser | 668 / 751 | 760 / 687 | 690 / 680 | 643 / 695 | 774 / 777 |
| 4096 | hot_bat / hot_ser | 208.1 / 209.2 | 327.4 / 342.8 | 336.4 / 345.8 | 226.0 / 240.5 | 310.4 / 314.4 |
| 4096 | cold_bat / cold_ser | 1176 / 1213 | 1468 / 1470 | 1537 / 1372 | 1262 / 1103 | 1561 / 1455 |

"hot" means outer-hot and inner first-touch (each set's 200 reps touch
~91 distinct containers once); cold cells are 100 queries after a 512 MB
thrash, so a cold query is an outer miss, a container-struct miss and an
inner miss in series (~500 ns at n = 1).

## What this changes

* **The cold_ser hypothesis is confirmed and the outer trade is
  quantified for the Cortex-A76**: Shar saves 18–33 ns per query hot at
  every size; the branchy `std::lower_bound` saves 45–110 ns per query
  cold from n ≈ 33 up. F stays the hot choice; a cold-dominated workload
  wants a branchy (or otherwise speculable) outer — on the Pi 5 the
  two-level harness already has D (outer spine + compile-time inner)
  best in three modes, and on SKX/EMR/GV4 variant C (bsearch outer +
  compile-time inner) winning cold. No kernel change follows from the
  33–265 deficit; it belongs to the outer search.
* **Two kernel leads, both needing an A/B before any change.** (a) The
  n ≤ 7 cold_ser deficit is the Pi 5 kernel's scalar path returning a
  computed flag (result 4): rewrite the sweeps with constant returns and
  measure cold_ser at n ≤ 31. (b) The spine's hot break-even on the A76
  is eight blocks (n = 256); at four to seven blocks (n = 128–255) it
  costs 6–22 ns hot against Lemire's inner but gains 40–100 ns cold, so
  raising the `num_blocks <= 3` delegation threshold trades one for the
  other — measure both modes.
* **Methodology.** Two independent 10-run campaigns on identical inputs
  never contradicted each other over 716 cells; WIN↔TIE flips were 2–7%
  of sizes hot and 27–33% cold, and the identical-code gauge fired at
  3–8% hot/cold_ser and 16% in cold_bat. So a 10-run WIN is a reliable
  sign but a single cold cell is not a quotable magnitude; quote bands.
  The bitmap generator makes every future campaign on any host directly
  comparable cell by cell with these two.
* **CLAUDE.md open item 6**: the Pi 5 outer test is done. Still to run:
  the five-variant sweep on M1 Pro, SKX, EMR and GV4, ten runs each
  (now ~2.3 h per ten runs on the Pi 5 instead of 5.7 h, thanks to the
  generator), and the M4 Max re-run against both Lemire kernels.

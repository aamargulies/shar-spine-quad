# F vs Lemire across container sizes on the Raspberry Pi 5 (campaign `sweep_fvl2`, 2026-10-11/12, 10 runs)

Paired per-run comparison of our two-level stack against Lemire's published
variant, with both the kernel he published on 2026-04-27 and the one he
revised on 2026-10-02, at 179 container sizes from 1 to 4096 on the Pi 5
(Cortex-A76), ten runs in two sessions. This is the first run of the
F-vs-Lemire sweep on a gap-32 host, the first against the revised kernel and
the first with ten runs; the only earlier sweep is the M4 Max campaign of
2026-05-20 (`m4_runs/sweep_fvl_raw.txt`, April kernel only, five runs,
re-analysed in `m4_runs/sweep_fvl_paired.txt`). The first version of this
note (commit a6554b4) covered runs 1–5 alone; every verdict it drew against F
survived the second five runs, and the differences are listed below.

## Setup

| item | value |
|---|---|
| harness | `bench_sweep_f_vs_lem.cpp` built with `-DQUADSEARCH_ARM_PI5` (gap 32, `pi5_spine` inner), `g++ -O3 -mcpu=cortex-a76 -std=c++20`, binary on local disk (`/home/pi/bench_sweep_f_vs_lem`, built 2026-10-11 17:19, used for all ten runs) |
| variants | F = Shar outer + `simd_quad_pi5_spine` (general-n) inner; Lem = bsearch outer + `simd_quad` (2026-04-27); Lem2 = bsearch outer + `simd_quad_2026_10` (2026-10-02) |
| sizes | 179, the M4 list truncated at 4096 (`pi5_runs/sweep_n_list_f_vs_lem.txt`) |
| modes | hot_bat, hot_ser, cold_bat, cold_ser (512 MB thrash before every cold cell) |
| intensity | 100 sets × 200 reps per cell; 10 runs with `order_seed` = run index (variant timing order shuffled per cell; all six orders of three variants occurred) |
| host state | pinned to core 3 with `taskset`, governor `ondemand`. Runs 1–5: 2026-10-11 17:25–23:04, 20,362 s, SoC 51.2–66.7 °C, with compiles, a plot regeneration and three verification agents on cores 0–2 during runs 4–5. Runs 6–10: 2026-10-12 05:33–11:11, 20,267 s, 46.9–60.6 °C, nothing else running. |
| cells | 7,160 of 7,160, 0 failed; `pi5_runs/sweep_fvl2_raw.txt` (per-cell outputs folded by `consolidate_sweep.py`, runs 6–10 merged on 2026-10-12 with nothing replaced); driver logs `pi5_runs/sweep_fvl2_driver.log` (runs 1–5) and `pi5_runs/sweep_fvl2_driver_runs6-10.log` |
| analysis | `python3 compute_sweep_fvl.py pi5` → `pi5_runs/sweep_fvl2_paired.txt`, `pi5_sweep_fvl2_data.py`; `python3 plot_sweep_fvl.py pi5` → `bench_pi5_sweep_fvl2.png` (levels), `bench_pi5_sweep_fvl2_delta.png` (paired deltas). `--runs 1,2,3,4,5` and `--runs 6,7,8,9,10` reproduce the per-half numbers quoted below. |
| rule | per cell, delta = B/A − 1 in each run; WIN(X) = X faster in ≥ 8 of 10 runs (≥ 4 of 5 in a per-half analysis) and \|median delta\| ≥ 3%, else TIE. Levels (per-cell medians) are never differenced across variants. |

## Two sessions, and what the quiet one changed

Runs 4–5 overlapped with the `bench.cpp` cold-flush work on the other three
cores; runs 6–10 ran on an otherwise idle host. Run-level drift (geometric
mean over the 537 shared cells, max/min across runs):

| runs | hot_bat | hot_ser | cold_bat | cold_ser |
|---|---|---|---|---|
| 1–5 | 1.07× | 1.08× | 1.42× (run 5: 1187 ns against 836–890) | 1.21× |
| 6–10 | 1.03× | 1.02× | 1.17× | 1.07× |

So the idle host removed the whole-run drift. It did not remove per-cell
cold noise: the noise gauge below is the same in both halves, and the largest
identical-code cold medians are larger in the quiet half (30%, 29%) than in
the first (19%, 22%). A Pi 5 cold cell is 200 queries, a few hundred
microseconds; whatever perturbs it is not load on the other cores.

The halves agree where it matters. Over the 2,148 cells (179 sizes × 4 modes
× 3 pairs) the two 5-run analyses give the same verdict in 1,633, a WIN in one
half and a TIE in the other in 489, and contradict each other (WIN(X) in one
half, WIN(Y) in the other) in 26 — 20 of them in the identical-code pair
Lem2 vs Lem, 6 in the pairs against F (hot_bat 2, cold_bat 2, cold_ser 2). The
two 5-run Lemire hot WINs of the first note (n = 137 and 151) are among them;
at ten runs both are TIEs (+0.7%, −2.5%).

## Noise gauge: the two Lemire kernels are identical code from n = 16 up

Lemire's revision only touches arrays shorter than 16 elements, so for the
164 sizes n ≥ 16 "Lem2 vs Lem" compares two builds of the same code and shows
what the WIN rule does on pure noise. Cells read runs 1–5 / runs 6–10 /
**all ten**:

| mode | WIN called, of 164 | ≥ 80% same sign | \|median\| p90 | \|median\| max | WINs with \|median\| ≥ 10% |
|---|---|---|---|---|---|
| hot_bat | 33 / 22 / **6** | 41% / 34% / **10%** | 6.1 / 6.3 / **4.7** | 13.1 / 18.2 / **13.3** | 3 / 6 / **0** |
| hot_ser | 27 / 27 / **5** | 41% / 41% / **13%** | 5.5 / 5.7 / **3.8** | 10.1 / 13.0 / **5.5** | 1 / 3 / **0** |
| cold_bat | 37 / 35 / **14** | 38% / 40% / **12%** | 10.0 / 9.0 / **5.1** | 18.8 / 30.0 / **11.9** | 10 / 7 / **1** |
| cold_ser | 35 / 35 / **14** | 38% / 42% / **13%** | 7.7 / 8.0 / **4.4** | 22.3 / 29.4 / **14.9** | 7 / 8 / **2** |

At five runs the rule fires on identical code at 16–23% of sizes per mode,
with cold medians up to 30%; at ten runs at 3–9%, with the 90th percentile
of the called magnitude under 5% and at most two cells per mode at or above
10%. (Chance alone gives the two-sided sign test 11% at 8 of 10 before the
3% magnitude filter, so the 10-run rate is noise behaving as expected.) The
reading rules that follow: from a 5-run sweep quote bands and strongly
asymmetric counts, never single sizes; from a 10-run sweep a single-size WIN
under about 5% is still unresolved, a band of three or more sizes or a median
of 10% or more is not noise. The same reservation applies to the M4 Max paired
bands, which rest on five runs and have no gauge until the M4 sweep is re-run
with both kernels.

## Results

Verdict counts over 179 sizes at ten runs (first-named variant faster / F
faster / TIE; the runs-1–5 counts are in the first version of this note):

| pair | hot_bat | hot_ser | cold_bat | cold_ser |
|---|---|---|---|---|
| Lem vs F | 0 / 157 / 22 | 0 / 174 / 5 | 10 / 102 / 67 | 49 / 67 / 63 |
| Lem2 vs F | 0 / 158 / 21 | 0 / 175 / 4 | 8 / 92 / 79 | 47 / 63 / 69 |
| Lem2 vs Lem | 16 / 2 / 161 | 4 / 7 / 168 | 14 / 9 / 156 | 8 / 14 / 157 |

**1. Hot, F beats both Lemire kernels at essentially every size, and
Lemire wins no hot cell.** Paired median over sizes +25.2% (hot_bat) and
+33.5% (hot_ser) for Lem vs F (positive = Lemire slower), +24.0% and +33.9%
for Lem2 vs F; F is ahead (median > 0) at 175 and 178 of 179 sizes, and in
every single run at 161–170 of the 179 hot_bat sizes. Bands (Lem vs F): F
faster at n = 1–102 in hot_bat (67 sizes; +22% to +64% at n ≤ 28, 10/10 at 19
of those 28; +8% to +38% at 29–102) and at 256–4096 (85 sizes, +9% to +60%,
10/10 at 73); in hot_ser at 1–167 (+7% to +60%) and 248–4096 (+8% to +64%,
10/10 at 83 of 86). The TIE zone is n = 105–248 in hot_bat (22 of 27 sizes a
TIE, medians −2.5% to +10.6%) and five sizes in 172–240 in hot_ser — the
range where the general-n kernel runs with 4–8 blocks and the spine has just
started to act. Against Lem2 the picture is the same (158 and 175 WIN(F)).

**2. The M4 Max hot_bat Lemire bands do not exist on the gap-32 kernel.**
At n = 48–62 F is faster by +16% to +33%, WIN(F) at 9 of 9 sizes, 10/10 at
8 of them; at n = 81–128 by +3% to +18%, WIN(F) at 10 of 15 sizes (F faster
in ≥ 8 of 10 runs at those 10; the other five, 105, 116, 120, 124 and 128, are
TIEs at +3% to +9% with F faster in 6–7 of 10). On the M4 the same sizes were
Lemire WINs at −25% to −29% and −5% to −32%. The hot small-container weakness
is therefore specific to the gap-64 `simd_quad_m4.c` kernel (its [32,64) path
is one vector load plus a scalar sweep of up to 31 elements and its general
tail scans up to 63); the Pi 5 kernel's [8,16) and [16,32) fast paths and
≤ 31-element tail do not have it.

**3. cold_ser flips with size: Lemire ahead below n ≈ 265, F above
n ≈ 320.**

| range | Lem WIN / F WIN / TIE | Lem faster (median < 0) | median of paired medians |
|---|---|---|---|
| n = 1–265 (96 sizes) | 49 / 1 / 46 | 86 of 96 | −5.3% |
| n = 273–312 (5) | 0 / 1 / 4 | 1 of 5 | +1.2% |
| n = 323–4096 (78) | 0 / 65 / 13 | 0 of 78 | +13.8% |

Lem2 vs F: 47 / 3 / 46 below 265 (81 of 96 faster, −5.3%) and 0 / 59 / 19
above 320 (+14.6%). The two halves say the same thing — runs 1–5 below 265:
44 / 6 / 46, runs 6–10: 66 / 1 / 29; above 320: 0 / 67 / 11 and 0 / 62 / 16 —
and in every one of the ten runs Lemire is faster at 59–81 of the 96 sizes
below 265. Lemire's bands at ten runs are n = 1–5 (−11% to −19%), 23–24,
31–32, 48–54 (−6% to −10%), 75–81, 92–98, 105–109, 132–141, 151–172 (−5% to
−14%), 184–217 (−3% to −13%) and 256–265, plus eleven single sizes; F's are
323–345, 393–420, 547–584, 624–667, 712–927, 991–1248, 1333–3043 (26 sizes,
+11% to +54%) and 3251–4096 (+24% to +37%). The flip is sharp: Lemire WINs
through n = 217 and again at 256–265, TIEs at 224–248 and 273–312, F from
302–323 up without a single Lemire-faster median above 320.

The advantage is not confined to the sizes where the spine is inert. Split
by the kernel's structure: n = 1–96 (spine delegated to the plain path) WIN(Lem)
29 / WIN(F) 1, Lemire faster at 57 of 65 sizes, median −5.4%; n = 97–128
(four blocks) 4 / 0, 9 of 9, −4.9%; n = 132–265 (five to nine blocks) 16 / 0,
20 of 22, −6.3%. So the deficit is roughly constant from n = 1 to 265 and
then turns into a growing F win. That is what the outer-search hypothesis of
the first note predicts (still untested): Shar's cmov chain is nine serial
cold loads that the core cannot speculate past, whereas the branchy
`std::lower_bound` lets it issue loads ahead across mispredicts — a fixed
per-query penalty, the same Khuong & Morin effect behind variant C's cold wins
on Emerald Rapids and Graviton 4 in the two-level harness — while the spine's
memory-level parallelism on the inner search grows with n and outweighs it
from about n = 300. A bsearch-outer + `pi5_spine`-inner variant in the sweep
harness would separate the two.

**4. cold_bat is mostly a tie below 265 and an F win above.** Lem vs F:
n ≤ 265 Lem 10 / F 26 / TIE 60 (median of medians +2.7%); n ≥ 273 Lem 0 /
F 76 / TIE 7 (+20.1%), with F's bands at 8–14 (+8% to +17%), 273–333,
356–689 (21 sizes), 736–1208 (16), 1290–2415 (20) and 3251–3834 (+20% to
+40%). Lemire's cold_bat WINs are the band 197–217 (−10% to −14%) and the
single sizes 29, 54, 58, 62, 83 and 146 (−3% to −9%), inside the gauge; the
first note's n = 48 (−21%, 5/5) is a TIE at ten runs (−12%, 7/10). Lem2 vs F:
8 / 17 / 71 below 265 and 0 / 75 / 8 above; its only WINs at or beyond 10%
are n = 7 (−21%, 10/10, where the revised kernel differs) and 197–203.

**5. n = 4096 against the two-level harness.** Hot: Lem is +60.0% (hot_bat)
and +64.4% (hot_ser) slower than F, 10/10, matching the repaired two-level
harness (F −37.5% / −39.4%, 10/10, which is Lem +60% / +65%). cold_bat
+30.9% (F faster 9/10; two-level −17.3%, 7/10). cold_ser +30.9% (F faster
8/10; two-level F −30.5% at 8/10). At five runs cold_ser was a TIE here
(median +0.8%, per-run +95, +37, +1, −28, −17%); runs 6–10 added +58, +75,
+68, +19, +25%, and the two harnesses now agree. Lem2 vs F is the same
(+60.1%, +63.9%, +29.6% at 9/10, +34.0% at 8/10).

**6. Lemire's revision (Lem2 vs Lem).** Below n = 16, where the code
differs, the revised kernel is faster hot_bat at n = 3–13 by 4% to 18%
(WIN(Lem2) at 12 of the 15 sizes, 8–10/10) and cold_bat at n = 3–15 by 3% to
16% (9 WINs); hot_ser shows no consistent gain (3 Lem2 / 3 Lem / 9 TIE) and
cold_ser is mixed (the April kernel faster at n = 1–3 by 6% to 9%, the revised
one at 6–7 and 9–15 by 3% to 12%). Against F the revision changes no verdict
class: F still wins every hot cell below 16 (+20% to +65%), and cold_ser below
16 is Lem2 WIN 9 / F 1 / TIE 5 against Lem's 7 / 1 / 7. From n = 16 up the
pair is the noise gauge above.

## Levels for orientation (per-cell medians over ten runs, ns/query; do not difference across variants)

| n | hot_bat F / Lem / Lem2 | hot_ser | cold_bat | cold_ser |
|---|---|---|---|---|
| 1 | 49.6 / 69.3 / 71.0 | 47.4 / 70.7 / 77.7 | 501 / 489 / 508 | 570 / 512 / 561 |
| 128 | 137.2 / 155.2 / 148.8 | 141.7 / 166.5 / 157.3 | 707 / 706 / 692 | 861 / 710 / 705 |
| 4096 | 207.6 / 334.3 / 333.9 | 209.2 / 344.0 / 342.4 | 1279 / 1768 / 1968 | 1283 / 1475 / 1479 |

"hot" means outer-hot and inner first-touch (each set's 200 reps touch
~91 distinct containers once), so the Pi 5's hot levels include one DRAM
line per query; cold cells are 200 queries after a 512 MB thrash.

## What this changes

* Nothing in the verdicts against F: the second five runs confirmed every
  5-run conclusion, turned the n = 4096 cold_ser TIE into a WIN(F) that
  agrees with the two-level harness, and dissolved the handful of
  single-size Lemire WINs (hot_bat 137 and 151, cold_bat 48) into TIEs.
* CLAUDE.md open item 6. The hot small-container path is a gap-64 problem
  (M4 Max, M1 Pro): design the shorter small-n path or the size-dependent
  dispatch for `simd_quad_m4.c`, and re-run the M4 sweep against both Lemire
  kernels first (`m4_runs/run_sweep_f_vs_lem.sh`, ten runs) to see whether
  the revised kernel widens its bands. On the Pi 5 no hot small-n work is
  indicated. The Pi 5 cold 10-run re-run asked for by the first note is done.
* The cold_ser deficit below ≈ 265 on the Pi 5 (and the M4's cold_ser bands)
  points at the outer search, not the inner kernel; it belongs with the
  two-level cold findings (C and D winning cold) rather than with the
  small-n kernel path. Test the outer hypothesis before changing a kernel.
* Methodology: five runs separate long bands from noise but not single
  sizes (identical code: 16–23% false WINs); ten runs bring that to 3–9%
  with the called magnitudes under 5% at the 90th percentile. An idle host
  removes whole-run drift (cold_bat 1.42× → 1.17×) but not per-cell cold
  noise on this host; use ten runs for any cold claim regardless.

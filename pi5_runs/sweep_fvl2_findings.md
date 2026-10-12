# F vs Lemire across container sizes on the Raspberry Pi 5 (campaign `sweep_fvl2`, 2026-10-11)

Paired per-run comparison of our two-level stack against Lemire's published
variant, with both the kernel he published on 2026-04-27 and the one he
revised on 2026-10-02, at 179 container sizes from 1 to 4096 on the Pi 5
(Cortex-A76). This is the first run of the F-vs-Lemire sweep on a gap-32
host and the first against the revised kernel; the only earlier sweep is the
M4 Max campaign of 2026-05-20 (`m4_runs/sweep_fvl_raw.txt`, April kernel
only, re-analysed in `m4_runs/sweep_fvl_paired.txt`).

## Setup

| item | value |
|---|---|
| harness | `bench_sweep_f_vs_lem.cpp` built with `-DQUADSEARCH_ARM_PI5` (gap 32, `pi5_spine` inner), `g++ -O3 -mcpu=cortex-a76 -std=c++20`, binary on local disk (`/home/pi/bench_sweep_f_vs_lem`) |
| variants | F = Shar outer + `simd_quad_pi5_spine` (general-n) inner; Lem = bsearch outer + `simd_quad` (2026-04-27); Lem2 = bsearch outer + `simd_quad_2026_10` (2026-10-02) |
| sizes | 179, the M4 list truncated at 4096 (`pi5_runs/sweep_n_list_f_vs_lem.txt`) |
| modes | hot_bat, hot_ser, cold_bat, cold_ser (512 MB thrash before every cold cell) |
| intensity | 100 sets × 200 reps per cell; 5 runs with `order_seed` = run index (variant timing order shuffled per cell; 6 distinct orders occurred) |
| host state | pinned to core 3 with `taskset`, governor `ondemand`, SoC 51.2–66.7 °C, 2026-10-11 17:25–23:04 local, 20,362 s |
| cells | 3,580 of 3,580, 0 failed; `pi5_runs/sweep_fvl2_raw.txt` (per-cell outputs folded by `consolidate_sweep.py`), driver log `pi5_runs/sweep_fvl2_driver.log` |
| analysis | `python3 compute_sweep_fvl.py pi5` → `pi5_runs/sweep_fvl2_paired.txt`, `pi5_sweep_fvl2_data.py`; `python3 plot_sweep_fvl.py pi5` → `bench_pi5_sweep_fvl2.png` (levels), `bench_pi5_sweep_fvl2_delta.png` (paired deltas) |
| rule | per cell, delta = B/A − 1 in each run; WIN(X) = X faster in ≥ 4 of 5 runs and \|median delta\| ≥ 3%, else TIE. Levels (per-cell medians) are never differenced across variants. |

**Caveat on host activity.** Runs 4–5 overlapped with the `bench.cpp`
cold-flush work on cores 0–2 (compiles, a plot regeneration and three
verification agents between about 21:35 and 22:50). Run-level drift is
1.07× (hot_bat) and 1.08× (hot_ser) but 1.42× in cold_bat and 1.21× in
cold_ser, almost entirely run 5 (cold_bat geometric mean 1187 ns against
836–890 ns in runs 1–4). Paired within-run deltas are immune to a uniform
slowdown but not to intermittent interference, so the cold verdicts below
should be read against the noise gauge, and the cold modes should be
repeated with 10 runs on a quiet host before any design decision
(`FVL_RUNS='6 7 8 9 10' FVL_BIN=/home/pi/bench_sweep_f_vs_lem bash
pi5_runs/run_sweep_f_vs_lem.sh 100 200 pi5_runs/sweep_n_list_f_vs_lem.txt`
adds runs 6–10 in about 5.7 h; the aggregator picks up every run it finds).

## Noise gauge: the two Lemire kernels are identical code from n = 16 up

Lemire's revision only touches arrays shorter than 16 elements, so for the
164 sizes n ≥ 16 "Lem2 vs Lem" compares two builds of the same code and
shows what the 5-run WIN rule does on pure noise:

| mode | WIN called | ≥ 4/5 same sign | \|median\| p50 / p90 / max | WINs with \|median\| ≥ 10% |
|---|---|---|---|---|
| hot_bat | 33 of 164 (20%) | 41% | 2.0% / 6.1% / 13.1% | 3 |
| hot_ser | 27 (16%) | 41% | 1.8% / 5.5% / 10.1% | 1 |
| cold_bat | 37 (23%) | 38% | 2.2% / 10.0% / 18.8% | 10 |
| cold_ser | 35 (21%) | 38% | 2.0% / 7.7% / 22.3% | 7 |

So at 5 runs on this host a single-size WIN, a 2–3-size band, or a cold
median under about 20% is not evidence on its own. What counts is long
bands, large magnitudes, and counts that are far from the gauge's roughly
symmetric split (hot_bat 19 Lem2 / 14 Lem, cold_ser 13 / 22). The same
reservation applies to the M4 Max paired bands, which also rest on 5 runs
and have no gauge until the M4 sweep is re-run with both kernels.

## Results

Verdict counts over 179 sizes (first-named variant faster / F faster / TIE):

| pair | hot_bat | hot_ser | cold_bat | cold_ser |
|---|---|---|---|---|
| Lem vs F | 2 / 156 / 21 | 0 / 175 / 4 | 14 / 102 / 63 | 44 / 75 / 60 |
| Lem2 vs F | 2 / 157 / 20 | 0 / 173 / 6 | 18 / 91 / 70 | 48 / 73 / 58 |
| Lem2 vs Lem | 31 / 14 / 134 | 17 / 18 / 144 | 24 / 21 / 134 | 18 / 27 / 134 |

**1. Hot, F beats both Lemire kernels at essentially every size.** Paired
median over sizes +25.9% (hot_bat) and +32.1% (hot_ser) for Lem vs F
(positive = Lemire slower); F is ahead at 174 and 177 of 179 sizes. Bands:
F faster at n = 1–28 by +21% to +72%, at 30–78 by +10% to +43%, and at
380–4096 by +8.5% to +59% (hot_bat), and at 1–167 and 240–4096 in hot_ser.
The only Lemire hot WINs are single sizes at n = 137 and 151 (−6%, 4/5),
inside the gauge. F's margin is smallest at n = 128–265 (15 of 23 sizes a
TIE in hot_bat), the range where the general-n kernel runs with 4–8 blocks
and the spine has just started to act. Against Lem2 the picture is the
same (157 and 173 WIN(F)).

**2. The M4 Max hot_bat Lemire bands do not exist on the gap-32 kernel.**
At n = 48–62 F is faster by +15% to +33% (5/5 at 8 of 9 sizes, 4/5 at
n = 58); at n = 81–128 by +2% to +25% (4–5/5 at 14 of 15 sizes; n = 105 is
+2%, 3/5). On the M4 the same sizes were Lemire WINs at −25% to −29% and
−5% to −32%. The hot small-container weakness is therefore specific to the
gap-64 `simd_quad_m4.c` kernel (its [32,64) path is one vector load plus a
scalar sweep of up to 31 elements and its general tail scans up to 63);
the Pi 5 kernel's [8,16) and [16,32) fast paths and ≤ 31-element tail do
not have it.

**3. cold_ser flips with size: Lemire ahead below n ≈ 265, F above
n ≈ 320.**

| range | Lem WIN / F WIN / TIE | Lem faster (median < 0) | median of paired medians |
|---|---|---|---|
| n = 1–265 (96 sizes) | 44 / 6 / 46 | 75 of 96 | −4.7% |
| n = 273–312 (5) | 0 / 2 / 3 | 1 of 5 | +3.0% |
| n = 323–4096 (78) | 0 / 67 / 11 | 1 of 78 | +13.6% |

Lem2 vs F: 48 / 7 / 41 below 265 (76 of 96 faster, −4.2%) and 0 / 65 / 13
above 320 (+14.7%). Lemire's cold_ser bands are n = 1–5 (−6% to −21%),
31–32, 37–38, 48–49, 53–54, 58–62, 75–81, 105–109, 151–172 (−4% to −22%),
197–217, 256–265 and single sizes in between; F's are 323–420, 464–495,
547–927, 991–1248, 1333–1795 and 2188–3963 (+3% to +41%). Individually the
small-n cells (mostly −3% to −13%) sit inside the gauge's cold range, but
44-against-6 over 96 sizes is nothing like the gauge's 13-against-22, so the
direction below ≈ 265 is real even though no single band's edge or
magnitude is resolved at 5 runs.

Hypothesis for the mechanism (not tested here): below n = 128 the spine is
inert on a gap-32 host (`num_blocks <= 3` delegates to the plain kernel), so
both stacks run a plain inner search over the same one or two lines; what
differs is the outer search over 512 keys. Shar's cmov chain is nine serial
cold loads that the core cannot speculate past, whereas the branchy
`std::lower_bound` lets it issue loads ahead across mispredicts — the same
Khuong & Morin effect behind variant C's cold wins on Emerald Rapids and
Graviton 4 in the two-level harness. Above ≈ 320 the spine's memory-level
parallelism on the inner outweighs the outer penalty. A bsearch-outer +
`pi5_spine`-inner variant in the sweep harness would separate the two.

**4. cold_bat is mostly a tie below 265 and an F win above.** Lem vs F:
n ≤ 265 Lem 14 / F 31 / TIE 51; n ≥ 273 Lem 0 / F 71 / TIE 12, with F's
bands at 292–333, 368–420, 464–667, 736–1208, 1290–1855, 1982–2756,
2945–3473 and 3710–3834 (+4% to +65%). The scattered Lemire WINs below
(29–30, 81–83, 210–217 and singles at 7, 48, 51, 54, 58, 62, 146, 197) are
2-size bands or singles at −4% to −25%, within the gauge except perhaps
n = 48 (−21%, 5/5).

**5. n = 4096 against the two-level harness.** Hot: Lem is +58.8% (hot_bat)
and +62.4% (hot_ser) slower than F, 5/5, matching the repaired two-level
harness (F −37.5% / −39.4%, 10/10, which is Lem +60% / +65%). cold_bat
+29.0% (F faster 4/5; two-level −17.3%, 7/10, a tie). cold_ser is a TIE
here (median +0.8%; per-run +95%, +37%, +1%, −28%, −17%) where the
two-level harness had F −30.5% at 8/10. This harness runs 100 sets rather
than 200 and 5 runs rather than 10, and a Pi 5 cold cell is a few hundred
microseconds (methodology lesson 5); the two-level number stands as the
better-measured one.

**6. Lemire's revision (Lem2 vs Lem).** Below n = 16, where the code
differs, the revised kernel is faster hot_bat at n = 3–13 by 5% to 18%
(4–5/5 at every size) and cold_bat at n = 9–15 by 5% to 15%; hot_ser shows
no consistent gain (signs mixed, \|median\| ≤ 9%), and cold_ser is mixed
(the April kernel faster at n = 1–3 by 14% to 20%, the revised one at n = 6
and 9 by about 21%). Against F the revision changes no verdict class: F
still wins every hot cell below 16 (+15% to +61%), and cold_ser below 16
is Lem2 WIN 8 / F 1 / TIE 6 against Lem's 7 / 4 / 4.

## Levels for orientation (per-cell medians, ns/query; do not difference across variants)

| n | hot_bat F / Lem / Lem2 | hot_ser | cold_bat | cold_ser |
|---|---|---|---|---|
| 1 | 48.8 / 69.2 / 72.6 | 47.4 / 71.7 / 76.3 | 501 / 492 / 511 | 628 / 550 / 664 |
| 128 | 138.8 / 155.9 / 147.2 | 153.7 / 171.5 / 156.6 | 715 / 696 / 700 | 754 / 839 / 861 |
| 4096 | 207.8 / 334.6 / 338.2 | 211.1 / 340.0 / 347.7 | 1526 / 1682 / 1940 | 1261 / 1441 / 1449 |

"hot" means outer-hot and inner first-touch (each set's 200 reps touch
~91 distinct containers once), so the Pi 5's hot levels include one DRAM
line per query; cold cells are 200 queries after a 512 MB thrash.

## What this changes

* CLAUDE.md open item 6 splits in two. The hot small-container path is a
  gap-64 problem (M4 Max, M1 Pro): design the shorter small-n path or the
  size-dependent dispatch for `simd_quad_m4.c`, and re-run the M4 sweep
  against both Lemire kernels first (`m4_runs/run_sweep_f_vs_lem.sh`) to see
  whether the revised kernel widens its bands. On the Pi 5 no hot small-n
  work is indicated.
* The cold_ser deficit below ≈ 265 on the Pi 5 (and the M4's cold_ser bands)
  points at the outer search, not the inner kernel; it belongs with the
  two-level cold findings (C and D winning cold) rather than with the
  small-n kernel path. Test the outer hypothesis before changing a kernel.
* Five runs separate long bands from noise but not single sizes; quote
  bands, not cells, from any 5-run sweep, and extend to 10 runs for cold
  claims.

# Intel Coffee Lake (i9-9980HK): onboarding and first campaigns, 2026-10-12

Host tag `cfl`. The user's 2019 MacBook Pro ("i9", hostname mb2019) running
Ubuntu (kernel 7.2.9 with the T2 patches): Intel Core i9-9980HK, 8 cores /
16 threads, Coffee Lake-H Refresh (a Skylake-class client core), 32 KB L1D,
256 KB L2 per core, 16 MB L3, 64-byte lines, AVX2 and no AVX-512, 62 GB RAM,
NVMe. `intel_pstate` with the `performance` governor; turbo on (up to
5.0 GHz) for the first set, off (2.4 GHz base clock) for the second. GCC
17.0.0 20260824 in `/usr/local/bin`; `-march=native` resolves to `skylake`
(`__AVX2__` set, `__AVX512F__`/`__AVX512VBMI2__` not), so `simd_quad_intel`
takes its 2x ymm block check and keeps the in-loop prefetch, as on
Skylake-SP. Everything was driven from the Pi 5 over ssh; the sources were
rsynced to `~/QuadSearch` on the laptop, built there, and the run files
copied back to `cfl_runs/`.

Builds (all three harnesses pass their correctness checks):

    g++ -O3 -march=native -std=c++20 bench.cpp simd_quad_intel.c -o bench
    g++ -O3 -march=native -std=c++20 -DQUADSEARCH_DESCRIPTOR_ALIGN=64 bench_twolevel.cpp simd_quad_intel.c -o bench_twolevel
    g++ -O3 -march=native -std=c++20 -DQUADSEARCH_DESCRIPTOR_ALIGN=64 bench_sweep_f_vs_lem.cpp simd_quad_intel.c -o bench_sweep_f_vs_lem

Every run was pinned to CPU 15 (the hyperthread sibling of core 7; the host
was otherwise idle, load 0.1) with the drivers `run_bench_flushed.sh cfl 10`,
`run_twolevel.sh cfl 10` and `run_sweep_f_vs_lem.sh cfl 100 200
pi5_runs/sweep_n_list_f_vs_lem.txt` (179 sizes 1..4096, 10 runs,
`order_seed` = run index).

## Thermal behaviour: the laptop throttles

The package temperature was 84-91 C at the end of nine of the ten
2.2-2.6-minute bench runs (run 10 ended at 68 C; `temp_after` headers of
`rebench_flushed_run{1..10}.txt`) and 50-94 C between cells during the sweep
(the driver log's reading at the start of each cell: median 82 C, 250 of
7,160 cells at 90 C or above; the per-cell `# temp_c` headers span 50-89 C);
the kernel's PROCHOT counters (`thermal_throttle/package_throttle_count`)
were climbing. Under turbo:

- the ten flushed bench runs were stable (run-level warm drift 1.10x, cold
  1.32x over 110 shared cells);
- the ten two-level runs were not: hot_bat run-level drift 4.15x, hot_ser
  4.58x (runs 1 and 5 about four times slower than the others), cold_bat
  2.75x (run 1), cold_ser 1.34x, and the per-run paired deltas of one pair
  swing from -39% to +114%. Only verdicts with 10/10 sign counts are quoted
  from that set; its hot levels are not usable.

With the user's agreement the whole set was repeated with turbo disabled
(`intel_pstate/no_turbo=1`, restored afterwards), archived with the tag
`noturbo` (`rebench_flushed_noturbo_run*`, `twolevel_v2_noturbo_run*`,
prefix `sweep_fvl3_noturbo`). See the section below once it is in.

## Flushed main bench, turbo set (10 runs, `rebench_flushed_run{1..10}.txt`, `rebench_flushed_paired.txt`)

Paired per-run deltas, WIN = >= 8 of 10 runs agree and |median| >= 3%.

- **Spine vs plain kernel (`intels` vs `intel`).** Warm: WIN(spine) at 13 of
  the 14 sizes from n = 128 up (-4% to -16%; 10/10 at seven of them, 8-9/10 at
  the rest), the exception being 3967, a 7/10 TIE at -15%: three runs carry a
  throttle spike in that one `intels` warm cell (80.5, 74.8 and 32.7 ns against
  17.2-17.4 in the other seven; the noturbo set has the cell at -16%, 10/10).
  WIN(plain) at 16, 64, 89 (+4% to +11%; at 64-89 the spine kernel delegates
  to the plain one, so this is the cost of the delegated copy as GCC compiles
  it inside the spine function, 0.6 ns). Cold: WIN(spine) at every size from
  333 up (-7% at 333 to -42% at 3967, -41% at 4096; 9-10/10) and also at 32
  and 47 (-7%, 9/10 and -10%, 10/10; delegated sizes, so the 1-3 ns there is
  not the spine descent), WIN(plain) at 64-177 (+3% to +6%).
- **Line alignment (`nA` rows vs plain rows).** Warm: ties everywhere for the
  spine kernel (|median| <= 2.9%), small WIN(aligned) for the plain kernel at
  8, 23, 32, 47, 64 (-3% to -7%, 8-10/10). Cold, spine kernel: WIN(aligned) at
  64 (-26%, 8/10), 89 (-20%, 8/10) and at every size from 617 up (-32% at 617,
  -37% at 1001, -36% at 1024, -26% at 1234, -38% at 1777, -40% at 2048, -37%
  at 2999, -36% at 3967, -37% at 4096; 10/10 everywhere but 2048, 9/10), ties
  at 23-47 and 256-512 (512: -15%, 6/10), WIN(unaligned) at 8-16 (+13% to
  +19%), 128 (+28%, 10/10) and 177 (+23%, 9/10). Cold, plain kernel:
  WIN(aligned) at 47 (-11%), 64 (-24%), 89 (-20%), 128 (-10%), 1024 (-9%) and
  3967 (-3%, 8/10); WIN(unaligned) at 8-16 (+12% to +15%), 177 (+7%, 8/10),
  333 (+14%, 10/10) and 512 (+8%). The small-n reversals are the footprint of
  one-line-per-array copies in the sequential cold sweep (the plain arrays of
  neighbouring sizes share lines; see the n = 8 control, where nothing can
  straddle), not alignment; the plain kernel's reversal at 333 (+14% here,
  +15% in the turbo-off set) is not small-n and is not explained. From 617 up
  the aligned spine kernel is 26-40% faster cold (35-40% at seven of the nine
  sizes; -32% at 617 and -26% at 1234, the latter -28% in the turbo-off set,
  both 10/10): the one-block-one-line property and the 256-byte spine in four
  lines instead of five.
- **Compile-time `_spine_N` vs the general-n spine.** WIN(spine_N) at every
  size, warm -18% (512) to -29% (2048, 4096), cold -16% (256) to -43% (2048),
  10/10 in every cell but two (4096 warm and 256 cold, 9/10 each).
- **Padded descent (`intel_spine_pad`).** Warm WIN(pad) at 177, 256, 1024,
  1234, 4096 (-5% to -6%) and at 2999, 3967 (-13%), 9-10/10, WIN(general) at
  512 (+3%, 9/10); cold WIN(general) at every size 32-1024 (+7% at 1001 to
  +70% at 64, 8-10/10), WIN(pad) only at 3967 and 4096 (-4% to -5%): not
  shippable here either.

## Two-level harness, turbo set (10 runs, `twolevel_v2_run{1..10}.txt`, `twolevel_paired_v2.txt`; throttled, see above)

Robust results only (10/10 sign counts, or cold modes):

- F vs Lem: hot_bat -47.6% (10/10), hot_ser -63.7% (10/10), cold_bat -36.5%
  (9/10), cold_ser -8.1% (10/10). D vs Lem: -54.5%, -60.0%, -32.1%, -14.9%
  (10/10, 10/10, 10/10, 9/10).
- G vs F: +120% / +186% hot (0/10), +35% / +34% cold (1/10, 0/10): the Shar
  inner is out, as on every other host.
- Cold modes: C (bsearch outer + compile-time inner) is best by rank in both,
  fastest in 9/10 cold_bat runs -- the EMR/GV4 pattern (the branchy outer
  speculates past mispredicts on cold data), not the Pi 5's.
- Hot modes: E best by rank in hot_bat and F in hot_ser. With the throttled
  runs only the hot_bat F vs D (+5.1%, F faster 5/10, per-run -39% to +114%)
  and F vs E (+22.0%, 3/10, -34% to +116%) pairs are ties; A vs E is a WIN for
  E in hot_bat (+33.1%, 9/10) and all three pairs are WINs in hot_ser (F vs D
  -8.7%, 9/10; F vs E -5.8%, 9/10; E vs A -36.8%, 10/10), of which only E vs A
  meets this set's 10/10 bar. Deferred to the noturbo set, which reproduces
  all six verdicts.

## F-vs-Lemire sweep, turbo set (`sweep_fvl3_raw.txt`, `sweep_fvl3_paired.txt`, `cfl_sweep_fvl3_data.py`, `bench_cfl_sweep_fvl3{,_delta,_factorial}.png`)

7,160 cells (179 sizes 1..4096 x 4 modes x 10 runs, 100 sets x 200 reps,
the Pi 5 campaigns' arrays and targets), 21:28-22:49, 0 failed, package
50-89 C, turbo on. Unlike the two-level runs the sweep was stable: each cell
is a 1-2 s process with the five variants interleaved, and the run-level
drift over 895 shared cells is 1.02x hot_bat, 1.09x hot_ser, 1.03x cold_bat
and 1.03x cold_ser (the Pi 5's cold drift was 1.2-1.4x). WIN = >= 8 of 10 runs and
|median| >= 3%; the identical-code gauge (Lem2 vs Lem from n = 16 up) fires
at 2 of 164 sizes in hot_bat (n = 224, 302), 0 in hot_ser, 9 in cold_bat (5%)
and 11 in cold_ser (7%).

- **Hot: F beats both Lemire kernels at every size**, WIN(F) 179 of 179 in
  hot_bat (+38% to +197%, 10/10 in every cell) and 179 of 179 in hot_ser
  (+49% to +200%). In ns the margin is flat, +28 to +38 ns per query at every
  band, and the square says it is the outer: Fb vs F and Lem vs LemS both put
  the branchy `std::lower_bound` at +23 to +32 ns hot_bat and +32 ns hot_ser
  at every size (WIN(Shar) 179/179 in both pairs and both hot modes), while
  the inner contrasts sit within +/-3.5 ns hot below n = 266.
- **cold_ser: Lemire ahead below n ~ 512**, WIN(Lem) 102 / WIN(F) 21 / TIE 56:
  n = 1-7 (-21% to -31%), 9-15, 37-39, 45-53 and 58-240 (44 consecutive
  sizes, -4% to -15%), 256-283, then scattered 2-7-size bands up to 2497 and the single sizes 42,
  420, 512, 584, 2261, 2756 and 3043 (-3% to -8%); F wins at 16-22 (+4% to
  +38%), 1169-1248, 3360-3473 and 3710-3963, plus the single sizes 8, 645,
  868, 927, 1680 and 1855 (+4% to +8%). cold_bat is F's at 8-11, 16-46,
  98-105, 529-1094 and 1169-1290 (+5% to +33%), at 1795-1855, 3145-3360 and
  3710-3963 and at the single sizes 89, 151, 1378, 1472, 1573, 1680 and
  1982, and Lemire's at 1-7 and 12-15 (-5% to -16%) and at the single sizes
  54, 64, 512, 1333, 1424, 1522, 1625 and 1917 (-4% to -9%); the ties sit at
  48-95 (19 of 22 sizes) and 109-190 (17 of 18, plus 224 and
  256-273), while 197-495 alternates one-to-four-size bands -- Lemire at
  197-217, 232, 323-333, 368-380, 420 and 464-479 (-4% to -14%), F at
  240-248, 283-312, 345-356, 393-406, 434-449 and 495 (+5% to +19%) -- with
  no tie at all from 283 to 495 (WIN(Lem) 31 / WIN(F) 90 / TIE 58).
- **The outer, cold.** Fb vs F: WIN(Fb) 126 of 179 in cold_bat (every size
  from 120 up, -4% to -18%) and 154 in cold_ser (every size from 32 up except
  ties at 86, 95, 116 and 240, each Fb faster 7/10, -3% to -15%; plus 2-7,
  13-14, 25 and 29 below 32); Lem vs LemS the same (137 and 161). In ns the
  saving grows with n here, unlike the Pi 5's flat 45-110 ns: cold_bat -9 ns
  at 33-128, -26 at 129-265, -38 at 266-512, -39 at 513-1024, -57 at
  1025-2048, -77 at 2049-4096 (Fb vs F; Lem vs LemS -15, -34, -37, -51, -66,
  -74); cold_ser -19, -30, -36, -43, -56, -68 (-22, -29, -38, -49, -60, -77).
  Below n = 32 the branchy outer costs cold_bat too (+8 ns; F wins at 1-4,
  8-13, 16-21 and the single sizes 24, 26 and 30, once more at 35), while
  cold_ser is mixed there (Fb wins at 2-7, 13-14, 25 and 29, F at 8-11 and
  16-21; -3 ns by band).
- **The inner, cold.** Fb vs Lem: WIN(Fb) 140 of 179 in cold_bat (Lemire's
  kernel is 13% to 30% faster at 1-7 and 12-15 and 8% faster at 51, 8/10; 27
  ties at 8-11, 16-17, 23, 28, 30, 34, seven of the nine sizes in 48-62,
  73-78, 197-217, 265, 333 and 380; Fb wins the rest from 18 up -- the bands
  18-22, 24-27, 31-33, 35-46, 64-71, 81-190, 224-256, 273-323, 345-368, the
  single sizes 29 and 58, and every size from 393 up), 98 in cold_ser (Lemire
  ahead at 1-15 by 15% to 35%, then 83-86, 137-141, 217-224 and the single
  sizes 78, 116 and 203). In ns the spine inner is neutral in cold_ser up to
  n = 265 (+2, -2, +5 ns by band) and ahead from 266 (-17, -37, -47, -60 ns),
  while in cold_bat it is ahead from 33 (-12, -21, -47, -96, -88, -85 ns). So
  F's cold_ser deficit below 512 is the outer alone, as on the Pi 5, and the
  crossover is where the spine's cold gain outgrows the outer's saving.
- **No four-to-seven-block hot deficit on this core.** Fb vs Lem at 129-265
  is -3.5 ns hot_bat and -0.1 ns hot_ser (WIN(Fb) at 128-190 hot_bat). The
  spine inner loses hot only in narrow bands: with the bsearch outer (Fb vs
  Lem) at n = 48-62 (+7% to +10% hot_bat, 9 sizes: one 32-element block plus
  a 16-30 element scalar tail against Lemire's three gap-16 blocks) and at six
  hot_ser sizes between 73 and 112 (73, 81, 83, 92, 95, 112; +3.5% to +4.3%,
  86 and 89 ties); with the Shar outer (F vs LemS) at 64-66 (+3% to +4%),
  81-95 (+7% to +10%, both modes), 120-124 (+5% to +8%) and 210-217 (+4.5%,
  hot_bat), while 48-62 is a WIN(F) or a tie there. None of these bands costs
  more than about +5 ns per query (per-size maxima in the ns table: Fb vs Lem
  +5.3 ns hot_bat in 33-128, F vs LemS +3.3 ns hot_bat and +3.0 ns hot_ser
  there, +1.6 ns in 129-265). From 393 up the spine inner wins hot at
  66 consecutive sizes (-4% to -20%).
- **Lemire's 2026-10-02 revision** is faster than his April kernel hot at
  n = 2-15 (-7% to -15% hot_bat, -4% to -11% hot_ser, 9-10/10) and slower
  cold_ser at 1-15 (+13% to +33%), identical from 16 up; it changes no
  verdict against F.
- **Levels** (median ns/query; F / Lem / Fb / LemS): n = 1 hot_bat 20.8 /
  53.5 / 53.9 / 20.9; n = 4096 hot_bat 58.8 / 87.1 / 79.0 / 62.4, hot_ser
  60.0 / 92.8 / 91.6 / 63.1, cold_bat 541 / 542 / 445 / 618, cold_ser 534 /
  518 / 474 / 600. The cheapest cold configuration at n = 4096 is Fb,
  bsearch outer + spine inner (two-level A): 18% under F in cold_bat.

## Second set with turbo disabled (`intel_pstate/no_turbo=1`, 2.4 GHz base clock, from 22:50)

### Flushed main bench, noturbo set (10 runs, `rebench_flushed_noturbo_run{1..10}.txt`, `rebench_flushed_noturbo_paired.txt`)

Run-level drift 1.00x warm and 1.02x cold (package 43-48 C): the clock cap
removes the residual noise. Every verdict of the turbo set reproduces:

- spine vs plain kernel: warm WIN(spine) at 15 of 22 sizes: n = 8 (-3%) and
  every size from 128 up (-4% at 128 to -16% at 4096, 10/10 everywhere),
  WIN(plain) at 16, 64, 89 (the delegated copy, +4% to +11%); cold WIN(spine)
  at 14 sizes: 23, 32, 47 (-5%, -11%, -10%, 10/10) and every size from 333 up
  (-15% at 512, -22% at 1024, -30% at 2048, -41% at 4096, 10/10), WIN(plain)
  at 64, 128 and 177 (+6% to +7%, 9-10/10), 89 a tie (+2.8%, 10/10, under the
  3% threshold).
- alignment, spine kernel: warm all ties (|median| <= 2.7%); cold
  WIN(aligned) at 64 (-30%), 89 (-19%) and at every size from 512 up (-27% at
  512, -26% at 617, -34% at 1024 and 2048, -33% at 4096, 10/10 in every
  cell), WIN(unaligned) at 8-16 (+3% to +7%, the footprint of one-line copies
  in the sequential sweep), 128 (+19%, 9/10) and 177 (+11%, 8/10). Plain
  kernel: warm WIN(aligned) at 8, 16, 32, 47, 64 (-4% to -6%, 10/10; n = 11 is
  an exact tie), cold WIN(aligned) at 23, 32, 47 (-4% to -9%), 64 (-31%), 89
  (-20%), 128 (-14%), 177, 256 (-3% to -4%) and 1024 (-7%), WIN(unaligned) at
  11 (+3%, 10/10) and 333 (+15%, 9/10).
- compile-time `_spine_N`: WIN at every size, warm -17% (512) to -29%
  (4096; -28% at 2048), cold -19% (256) to -39% (2048), -36% at 4096, 10/10
  in every cell; padded descent: warm WIN(pad) at 177, 256, 1024, 1234, 4096
  (-5%) and 2999, 3967 (-12%), WIN(general) at 32, 333, 512 (+3% to +4%), all
  10/10; cold +4% (1024) to +46% (128) slower at every size 32-1024 (8-10/10),
  WIN(pad) at 1234, 2999, 3967 (-3% to -4%), 4096 a TIE (-2.4%, 9/10).

Absolute levels at the base clock are ~1.95x the turbo levels warm (warm
drift geomean 36.8 against 19-21 ns) but only 1.35-1.37x cold at n = 4096
(cold drift geomean 76.7 against 47-62 ns): e.g. n = 4096 warm plain / spine
36.1 / 30.3 ns (turbo medians 18.55 / 15.60), cold 220 / 129 ns (turbo
161 / 96). The turbo-set levels are the ones to quote as "the laptop"; the
noturbo set is the stable replication.

### Two-level harness, noturbo set (10 runs, `twolevel_v2_noturbo_run{1..10}.txt`, `twolevel_paired_v2_noturbo.txt`, 23:32-23:52)

Run-level drift 1.07x hot_bat, 1.05x hot_ser, 1.12x cold_bat, 1.22x
cold_ser (turbo set: 4.15x, 4.58x, 2.75x, 1.34x). hot_bat per-run ranges are
still wide (F vs E from -31% to +55%), so hot_bat is read by rank and sign
count; the other three modes are clean.

| mode | best by rank | paired deltas vs the best (10 runs) |
|---|---|---|
| hot_bat | E (fastest 4/10; winners D E F E F E F E I D) | D +5.2% (6/10) tie, I +4.5% tie, B +6.9% tie, F +9.9% (7/10) tie, H +11.4% tie, C +26.1% WIN(E), A +32.8% WIN(E), Lem +107%, G +143% |
| hot_ser | **F** (10/10) | E +4.9%, D +12.7%, I +16.7%, B +22.9%, H +25.0%, C +64.7%, A +74.3%, Lem +160.7%, G +166.6% (all 10/10) |
| cold_bat | **C** (10/10) | F +7.1%, D +12.4%, I +24.6%, A +30.4%, B +43.8%, E +45.3%, G +49.7%, Lem +70.5%, H +76.1% (all 10/10) |
| cold_ser | **D** (8/10; C 2/10) | C +0.8% tie, A +5.1%, B +5.1%, F +8.9%, E +10.2%, Lem +17.0%, I +20.9%, H +23.2%, G +50.8% |

- F vs Lem: -49.6% / -61.6% / -37.9% / -6.0% (10/10 in every mode); D vs
  Lem -51.5% / -57.0% / -33.7% / -14.5% (10/10). The turbo set, read by sign
  counts, said the same (-47.6 / -63.7 / -36.5 / -8.1).
- G vs F: +135% / +167% / +39% / +38% (0/10): the Shar inner is out here too.
- F vs D: tie / -11.3% (F, 10/10) / -3.9% (F, 9/10) / +8.9% (D, 10/10); F vs
  E: tie / -4.6% (F) / -26.8% (F) / -1.7% tie.
- Khuong & Morin (repaired prefetch): I vs F -2.3% tie / +16.7% / +17.2% /
  +10.3% (0/10 in the last three); H vs E tie / +18.3% / +19.7% / +11.3%
  (0/10). The Eytzinger outer never beats Shar or the outer spine on this
  core either.
- **Ship reading for Coffee Lake: F hot (hot_ser best 10/10, hot_bat tied
  with E, D and I), C for cold_bat (F is 7% behind), D or C for cold_ser** --
  the Skylake-SP / Emerald Rapids / Graviton 4 pattern (branchy or spine
  outer wins cold), not the Pi 5's (D everywhere).

### F-vs-Lemire sweep, noturbo set (`sweep_fvl3_noturbo_raw.txt`, `sweep_fvl3_noturbo_paired.txt`, `cfl_sweep_fvl3_noturbo_data.py`, `bench_cfl_sweep_fvl3_noturbo{,_delta,_factorial}.png`; turbo-vs-noturbo comparison `sweep_fvl3_turbo_vs_noturbo.txt`)

7,160 cells again (the same 179 sizes, arrays and targets, 100 sets x 200
reps, `order_seed` = run index), 23:52 on the 12th to 02:12 on the 13th,
8,400 s, 0 failed, package 45-50 C at the 2.4 GHz cap. Run-level drift 1.00x
hot_bat, 1.00x hot_ser, 1.01x cold_bat, 1.05x cold_ser (turbo set 1.02 /
1.09 / 1.03 / 1.03). Levels are 1.97-2.01x the turbo set's in both hot modes
for every variant (medians over the 179 sizes; down to 1.75-1.77x for F at
n = 4096 and 1.72x at n = 3710-3963, where part of the time is memory) and 1.37-1.42x cold (1.41-1.52x
at n <= 128, 1.34-1.38x from 256 up): the hot cells scale with the core
clock, the cold cells with a DRAM latency that does not. The identical-code
gauge (Lem2 vs Lem from n = 16 up) fires at 0 of 164 sizes in both hot
modes, 11 in cold_bat (7%) and 9 in cold_ser (5%).

- **Every verdict of the turbo set survives but one.** `compare_sweep_data.py`
  over the seven pairs x four modes (5,012 cells,
  `sweep_fvl3_turbo_vs_noturbo.txt`): one opposite winner (Lem2 vs F,
  cold_bat, n = 161: WIN(Lem2) -3.7%, 8/10 with turbo, WIN(F) +3.6%, 8/10
  without -- both at the rule's thresholds; the one line marked `flip`); the
  four pairs that carry the outer contrast (Lem vs F, Lem2 vs F, Fb vs F, Lem
  vs LemS) agree 179 of 179 in both hot modes; every other difference is a
  WIN<->TIE flip, 0-15% of sizes hot (0 for those four pairs, 6-27 sizes for
  the inner pairs Fb vs Lem and F vs LemS) and 8-30% cold (14-53 sizes per
  pair and mode) -- the reproducibility the Pi 5's two 10-run campaigns on
  identical inputs showed (2-7% hot, 27-33% cold).
- **Hot: WIN(F) 179 of 179 against both Lemire kernels in both modes**, +47%
  to +192% hot_bat and +64% to +194% hot_ser (10/10 in every cell; turbo
  +38-197% / +49-200%). The outer's cost doubled in ns with the halved clock:
  Fb vs F +61 ns hot_bat at 1-32 falling to +44 ns at 2049-4096 and +62 to
  +65 ns hot_ser flat (turbo +32 -> +23 and +32-33), Lem vs LemS +52 to +61 /
  +64 (turbo +25-31 / +32) -- a fixed 105-155 cycles at 2.4 GHz, not a fixed
  number of ns.
- **cold_ser: Lemire ahead below n ~ 512 again**, WIN(Lem) 78 / WIN(F) 32 /
  TIE 69 (turbo 102 / 21 / 56): 1-7 (-12% to -24%), 12-15 (-9% to -16%),
  62-83, 92-146 and 156-232 (38 of the 41 sizes from 62 to 232 -- the turbo
  set's 58-240 band with ties at 86, 89 and 151; -3% to -14%), 256-283,
  323-333, 368-393, 464-512, then 2-5-size bands up to 2497 and the single
  sizes 51, 786 and 1625; F at 8 (+19%, 10/10), 16-22 (+11% to +40%), 26-28,
  32-34, 927-959, 1169-1290, 1795-1855 and 3710-3963, plus the single sizes
  24, 43, 547, 868, 1058, 1680 and 3360 (+5% to +9%). cold_bat: WIN(Lem) 10 /
  WIN(F) 114 / TIE 55 (turbo 31 / 90 / 58) -- F from 8-11 and 16-46 (+10% to
  +27%), 86-116, 124-137, 172-190, 240-248, 265-312, 345-356, 393-406,
  434-449, 529-1094 and 1169-1290 (+9% to +35%), 1795-1855, 1982-2048,
  2945-3963 and nine single sizes (49, 53, 81, 156, 495, 1378, 1472, 1573,
  1680; +6% to +21%); Lemire at 197-217 (-3.5% to -8.5%), n = 4 (-3.9%,
  8/10) and the single sizes 1333, 1424, 1522, 1625 and 1917 (-3% to -8%),
  the turbo set's other 1-7 and 12-15 wins now ties (-4.1% to +1.3%).
- **The outer, cold.** Fb vs F: WIN(Fb) 98 cold_bat (68-75, 109, 141-151,
  184-248 and 292-4096 except 1058, with F ahead only up to 62; -3% to -16%)
  and 141 cold_ser (from 34 up with short gaps; -3% to -15%); Lem vs LemS 118
  and 141. The saving grows with n as before and sits within 1-25% of the
  turbo set's ns from 266 up (9-25% except the 266-512 cold_bat band, +1% to
  +4%): cold_bat +2 ns at 33-128, -15 at 129-265, -40 at
  266-512, -48 at 513-1024, -69 at 1025-2048, -91 at 2049-4096 (Lem vs LemS
  -5, -36, -37, -64, -78, -90); cold_ser -18, -33, -43, -50, -65, -84 (-18,
  -28, -41, -55, -74, -92). Below n = 32 the branchy outer costs +22 ns
  cold_bat (F wins at 1-9 and 13-29) and +7 ns cold_ser.
- **The inner, cold.** Fb vs Lem: WIN(Fb) 145 cold_bat (8-10 and every size
  from 18 up except ties at 23-25, 28-29, 32, 39, 49-62, 78-81 and 210-217
  and a WIN(Lem) at 48, +8.5%, 8/10; Lemire's kernel ahead at 1-7 by 9-19%
  and 12-15 by 6-14%) and 88 cold_ser (Lemire at 1-7 by
  18-29%, 9-15 by 10-18%, 112-116 and 137-141). In ns the spine inner is
  neutral in cold_ser to n = 265 (+3, -4, +2 by band) and ahead from 266
  (-20, -50, -70, -84; turbo -17, -37, -47, -60), ahead in cold_bat from 33
  (-21, -27, -78, -134, -117, -115). Same decomposition as the turbo set:
  F's cold_ser deficit below 512 is the outer, the n <= 7 deficit the inner
  (F vs LemS +35% to +54% there).
- **The inner, hot: no four-to-seven-block deficit, and the same narrow
  loss bands.** Fb vs Lem at 129-265 is -6.2 ns hot_bat (WIN(Fb) at 128-151
  and 161-190, -3.6% to -6.1%, 10/10) and +0.5 ns hot_ser (ties, but 210-217
  at +3%). The gap-32 inner loses hot at 48-62 with the bsearch outer (Fb vs
  Lem +7.6% to +8.9%, 10/10; with the Shar outer F vs LemS is -3.4% to +2.5%,
  a tie), at 81-95 with both outers (F vs LemS +7% to +10% in both modes, Fb
  vs Lem +3% to +4% hot_ser), at 112-124 (F vs LemS +4% to +6%) and 210-217
  (+3% to +5%) -- the turbo set's bands; at most +6 ns per query for the
  F vs LemS bands and +10 ns for the 48-62 Fb vs Lem band at this clock --
  and wins from 240 up in hot_bat and from 393 up in both modes
  (72 sizes, -3% to -17%, 8-10/10).
- **Lemire's 2026-10-02 revision**: -7% to -15% hot_bat and -4% to -11%
  hot_ser at n = 2-15 (10/10), +7% to +21% slower cold_ser at 1-15, faster
  cold_bat at 8-11 (-5% to -16%), identical from 16 up; no verdict against F
  changes.
- **Levels** (median ns/query; F / Lem / Fb / LemS): n = 1 hot_bat 41.8 /
  105.2 / 105.6 / 41.7 (turbo 20.8 / 53.5 / 53.9 / 20.9); n = 4096 hot_bat
  102.7 / 165.0 / 143.4 / 114.4, hot_ser 106.1 / 181.3 / 169.1 / 117.0,
  cold_bat 715 / 740 / 607 / 837, cold_ser 727 / 716 / 639 / 824. At
  n = 4096 Lem vs F is +61% / +74% hot (10/10) and a tie cold (+1.9%, -0.7%;
  turbo +49% / +56%, -0.1%, -2.4%); Fb, the cheapest cold configuration, is
  -16% / -11% cold against F (10/10; turbo -18% / -12%) for +40% / +59% hot;
  the spine inner against Lemire's under the Shar outer (F vs LemS) is -11% /
  -10% hot and -13% / -11% cold (10/10; turbo -5% / -6% and -11% / -12%).

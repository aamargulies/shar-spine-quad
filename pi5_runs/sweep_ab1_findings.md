# Pi 5 kernel A/B (campaign `sweep_ab1`, 2026-10-12, on the second board "eight")

Four open items of CLAUDE.md measured in one campaign of the kernel A/B
harness `bench_ab_pi5.cpp`: the constant-return small-n sweeps (open item 6,
first lead), the spine's delegation threshold (open item 6, second lead), the
in-loop prefetch (open item 2) and cache-line alignment of arrays and spines
(open item 3). Six two-level variants with the Shar outer fixed, timed per
inner_n on the sweep_fvl3 arrays and targets:

| variant | what differs from F |
|---|---|
| F | Shar outer + `simd_quad_pi5_spine` as shipped (kernel blob f7c140b8) |
| Fcr | the eight scalar sweep steps rewritten `if (x == pos) return true; if (x > pos) return false;` |
| Fd1 | spine delegation threshold `num_blocks <= 1` instead of `<= 3` (spine from two blocks, n >= 64) |
| Fa | F on 64-byte-aligned copies of every array and spine (sizes rounded up to the line) |
| G | Shar outer + the plain kernel `simd_quad_pi5` (in-loop prefetch as shipped) |
| Gnp | G without the in-loop prefetch (the code of `simd_quad_graviton`) |

The variant sources are derived from `simd_quad_pi5.c` by
`gen_pi5_ab_variants.py` (diffs: `sweep_ab1_variants.diff`; assembly:
`sweep_ab1_asm/`), each compiled as its own namespaced TU with the shipped
flags (`-O3 -mcpu=cortex-a76`, GCC 17.0.0 20260704 on trixie; the baseline TU
is instruction-identical to the shipped kernel TU). Pairs (B vs A, negative =
B faster): Fcr vs F, Fd1 vs F, Fa vs F, G vs F (the delegation-threshold-7
contrast at n = 128..255 and the spine's own value from 256), Gnp vs G (the
prefetch), Gnp vs F.

| | |
|---|---|
| host | Raspberry Pi 5 "eight" (Cortex-A76, 16 GB, `ondemand`, 48-58 C), otherwise idle |
| cells | 179 sizes 1..4096 x 4 modes x 10 runs = 7,160; 100 sets x 200 reps; `order_seed` = run index (720 distinct timing orders); 0 failed |
| wall-clock | 20:57-23:26, 8,990 s (fourth launch; the first three were stopped after the pre-launch review found a warm-up-order artefact and a heap-layout change, both fixed) |
| drift | run-level 1.01x hot_bat, 1.00x in the other three modes over 1,074 shared cells |
| rule | WIN = >= 8 of 10 runs agree in sign and \|median\| >= 3% |
| gauges | Gnp vs G is identical code below n = 128: WIN cells there 3 / 2 / 2 / 0 of 73 sizes per mode (hot_bat, hot_ser, cold_bat, cold_ser); n = 128 itself, where the loop that holds the prefetch iterates once, is WIN(G) +3.1% (9/10) in hot_bat and not a gauge cell. G vs F below 128 is the same source separately compiled: 6 / 1 / 9 / 1 |
| files | `sweep_ab1_raw.txt`, `sweep_ab1_driver.log`, `sweep_ab1_paired.txt`, `pi5_sweep_ab1_data.py`, `bench_pi5_sweep_ab1{,_delta,_delta_ns}.png` |

Every quoted delta is a paired per-run median; ns figures are the median over
a size band of each size's median B - A.

## 1. Constant-return sweeps (Fcr vs F): a cold_ser gain below 32, a cold_bat loss at 5-7 and 13-14, nothing hot

Hot: ties at 175 and 173 of 179 sizes (band medians within 1.2 ns below
128). The ten WIN cells are isolated single sizes of mixed sign: two below
128 where the rewritten sweep is live (hot_ser n = 29 WIN(F) +3.1%, hot_bat
n = 60 WIN(Fcr) -4.2%, both 8/10, within the identical-code gauges' 1-6 hot
WIN cells below 128) and eight above 128 (hot_bat 240, 273, 991; hot_ser
406, 449, 959, 3360, 3589) where the rewrite differs only in the tail sweep
past the last full block, which only the (n mod 32)/n of hits beyond it
reach -- 0.1-7% at seven of them, none at 3360 = 105 x 32 -- too few to
carry a 4-12% per-query delta. cold_ser, where
the sweep_fvl3 deficit lived: WIN(Fcr) at n = 1-4 (-7% to -13%, 10/10 in
every cell), 9-12 (-7% to -8%, 10/10), 14-15 (-5% to -8%) and 17-27 (-7% to
-10%, 9-10/10): 21 sizes, -38 to -43 ns per query by band. But F is faster
in cold_ser at 6-7 (+4%, 8/10) and at single sizes 29, 31, 54, 62, 75 (+3%
to +5%, 8-9/10), and in cold_bat at 5-7 (+9% to +14%, 10/10 in every
cell), 13-14 (+3% to +5%) and single sizes 28, 51, 54, 58, 62 (+3% to +6%):
cold_bat +5 to +14 ns by band below 32 (+14 at 1-7, +10 at 8-15, +5 at
16-31), with +78 ns at one size (n = 7). So the
rewrite moves the serial-chain penalty around rather than removing it: the
n <= 7 cold_ser deficit found in sweep_fvl3 (F vs LemS +56 to +92 ns at
n = 1-5) is reduced by ~40 ns at 1-4 and most of 9-27, not at 5-7, and the
independent-query mode pays for it at 5-7 and 13-14. GCC 17 compiles the
rewrite to two branches per scalar element and a different vector step, not
to the shipped code with a different return (`sweep_ab1_asm/README.md`).
**Not adopted**: the hypothesis (constant returns help the speculating
serial chain) is supported where it applies, but the form that GCC produces
is not a free win.

## 2. Delegation threshold: keep `num_blocks <= 3`

Lowering it to 1 (Fd1 vs F, spine descent at two and three blocks, n =
64-127): the spine path is slower hot by +8% to +26% at 21 consecutive sizes
64-124 in both hot modes (hot_bat +9% to +26%, hot_ser +8% to +24%; 9-10/10;
+17 ns by band) and gains little cold:
cold_bat -14 ns by band (WIN(Fd1) at 66-73 and 83-86, -3% to -5%), cold_ser
+8 ns (F wins at 66, 75, 83, 89, 112). Elsewhere the two compute the same
thing but are not one compilation. From 128 up both run the spine descent
and tie (10 WIN cells of 424, both signs); below 32 both run the spine
function's own fast paths and tie (6 of 124, both signs). At 32-63 both
delegate to the inlined plain kernel, but GCC specialises Fd1's copy to one
block instead of three (`sweep_ab1_asm/README.md`), and Fd1's copy is slower
hot: at 21 of 21 sizes in hot_ser and 18 of 21 in hot_bat, +2.2 and +1.5 ns
per query by band, WIN(F) at 33-35, 40, 42, 46, 56 in hot_ser (+3.3% to
+7.9%, 8-9/10) and at 33, 38, 42, 45, 53 in hot_bat (+3.1% to +4.5%,
8-10/10); cold ties there (one cell, Fd1 at 56 cold_bat). A codegen side
effect of the threshold constant, not the threshold itself.

Raising it to 7 (G vs F and Gnp vs F at four to seven blocks, n = 128-255:
the spine would delegate to the plain kernel, whose code G runs): the plain
kernel is faster hot by 5% to 16% (WIN(G) at 128-172, 184-190, 203-210,
224-240 in hot_bat; -10 ns by band, -8 ns with the prefetch removed) and
slower cold by +98 ns cold_bat (+22 to +137 ns by size; WIN(F) at every size
128-203, 15 sizes, +3% to +17%) and +22 ns cold_ser (up to +114; WIN(F) at
132-137, 156-161, 224-265). So the four-to-seven-block region is the
hot/cold trade CLAUDE.md suspected, and the cold side is larger -- about ten
times in cold_bat (+98 / +82 ns against -10 / -8 ns hot) and about twice in
cold_ser (+22 / +14 ns): **threshold 3 stays.** (The spine's own value from n = 256 up, G vs
F: -8 to -66 ns hot_bat and -146 to -272 ns cold_bat per query by band,
WIN(F) at every size from 584 up in hot_bat except n = 1024 (7/10), from 512
up for Gnp vs F, and from 224 up in cold_bat for both pairs.)

## 3. In-loop prefetch (Gnp vs G): faster hot mostly from n ~ 667 (shorter 3-5% bands from 124), slower cold from n ~ 224

Removing the prefetch from the plain kernel:

| mode | WIN(Gnp) / WIN(G) / TIE | where | ns by band (Gnp - G) |
|---|---|---|---|
| hot_bat | 2 / 46 / 131 | G (prefetch) faster at 124-128, 323-345, 667-761, 813-868, 959-1472, 2756-3473, 3710-4096 and at single sizes 137, 146, 156, 197, 406, 1680, 2415 (+3% to +13%) | +7 (512-1023), +15 (1024-2047), +10 (2048-4096) |
| hot_ser | 3 / 43 / 133 | G faster at 146-151, 712-761, 813-868, 959-1131, 1208-1573, 2945-3473, 3710-4096 and at single sizes 137, 345, 368, 604, 645, 1680, 1917, 2188, 2497, 2667 (+3% to +14%) | +5, +15, +10 |
| cold_bat | 39 / 0 / 140 | Gnp faster at 224-248, 323-345, 512-529, 897-927, 1024-1094, 1169-1208, 1982-2048, 2849-2945, 3589-4096 and at 14 single sizes (-3% to -8%) | -22, -42, -44 |
| cold_ser | 34 / 0 / 145 | Gnp faster at 224-248, 323-345, 420-434, 512-529, 897-927, 1169-1208, 1982-2048, 3589-4096 and at 12 single sizes (-3% to -8%) | -9, -31, -39 |

Below n = 128 the two kernels are the same code (the loop that holds the
prefetch does not iterate) and tie, which is the campaign's identical-code
gauge. In this harness "hot" is outer-hot with the inner arrays first-touched
(DRAM-cold on the Pi 5, each container hit about twice per set), and there
the prefetch pays 3-14% from n ~ 667, and 3-5% in the shorter bands 124-128,
146-151 and 323-345 and at single sizes between 137 and 645 (one of them,
604 hot_ser, +8%); in the flushed cold modes it costs 3-8% wherever the sign is
clear. The archived main-bench A/B (pi5 vs gv4
columns, L1-hot "warm" and a sequential cold sweep) had it slower in both
regimes; the ten flushed main-bench runs on this board
(`rebench_flushed_eight_run*.txt`, `rebench_flushed_findings.md`) re-measured
that pair with ten paired runs: slower warm at every size from 128 up (+3%
to +8%, 10/10) and slower cold at 12 of those 14 sizes (up to +18%), faster
only at 1024 cold (WIN, +7.7%, 9/10) and marginally at 1234 (+2.1%, 8/10, a
tie under the 3% rule). **Decision: removed from `simd_quad_pi5.c` on
2026-10-13** -- a loss in both regimes of the main bench and in the cold
modes here, with its only gain in one regime of the two-level harness. This
campaign measured the kernel with the prefetch (blob f7c140b8); the Gnp
column is the kernel as it is now.

## 4. Line alignment (Fa vs F): cheaper cold from n ~ 512, dearer hot everywhere

| mode | WIN(Fa) / WIN(F) / TIE | ns by band (Fa - F) |
|---|---|---|
| hot_bat | 1 / 113 / 65 | +31 (1-15), +23 (16-31), +9 (32-63), +13 (64-255), +12 (256-511), +6 (512-4096) |
| hot_ser | 1 / 106 / 72 | +31, +23, +9, +13 to +17, +12, +4 to +7 |
| cold_bat | 7 / 69 / 103 | +28 (1-7), +23 (8-15), +26 (16-31), +33 (32-63), +25 (64-255), +9 (256-511), -8 (512-1023), -13 (1024-2047), -28 (2048-4096) |
| cold_ser | 40 / 85 / 54 | +56, +34, +31, +77, +59, +42, -1, -21, -35, -43 |

Below one block the copies can only cost: a 2-byte array occupies a full
line and glibc's `aligned_alloc(64, 64)` spaces the copies 128 B apart, so
the 51,200 tiny arrays of 100 sets span ~6.3 MB and 1,600 pages against ~2 MB
and 500 pages for the vectors, leave the 2 MB L3 and cost 31 ns hot and
23-56 ns cold at n <= 15 (the review's probes put 8-9 ns of the n = 1 hot gap
on warm-up order before that was fixed, the rest on this footprint). From
n = 512 up the rounding is negligible and the aligned copies are 3-7% faster
cold (WIN(Fa) at 40 cold_ser sizes from 565 up, -21 to -43 ns per query from
512 up by band: -21 at 512-1023, -35 at 1024-2047, -43 at 2048-4096;
cold_bat -8 to -28 ns, WIN(Fa) at 2337-2415 and single sizes) --
the one-block-one-line property and a four-line spine instead of five. The
hot penalty, +4 to +17 ns in every band from 32 up (per size: TIE or WIN(F)
at every size but n = 1917, where Fa wins both hot modes, -3.6% 9/10 and
-3.7% 10/10; WIN(F) at 32-62 and 66-151 and at scattered sizes up to 4096,
+3.3% 8/10 and +4.0% 8/10 there), is larger than the footprint rounding can
explain
above 256 and is not understood; the Coffee Lake flushed main bench measured
the same pair warm as a tie (`cfl_runs/cfl_findings.md`), and the ten
flushed runs on this board give the single-level view for the Pi 5.
**For a Roaring integration:** align containers of a block or more; never
pad tiny containers to a line.

## 5. Levels (median ns/query, F / Fcr / Fd1 / Fa / G / Gnp)

| n | hot_bat | cold_bat | cold_ser |
|---|---|---|---|
| 1 | 39.1 / 38.8 / 39.3 / 69.2 / 38.5 / 38.6 | 489 / 493 / 502 / 518 / 496 / 495 | 561 / 500 / 563 / 614 / 568 / 561 |
| 16 | 48.3 / 47.0 / 47.2 / 73.8 / 46.9 / 47.6 | 498 / 509 / 505 / 522 / 505 / 507 | 509 / 501 / 511 / 525 / 506 / 507 |
| 128 | 124.9 / 122.7 / 123.8 / 146.5 / 112.7 / 116.2 | 661 / 668 / 683 / 688 / 752 / 752 | 766 / 754 / 756 / 832 / 793 / 778 |
| 1024 | 169.7 / 164.7 / 167.1 / 174.1 / 191.2 / 214.1 | 901 / 903 / 907 / 907 / 1108 / 1061 | 945 / 959 / 957 / 917 / 1113 / 1083 |
| 4096 | 201.9 / 196.7 / 201.5 / 209.2 / 279.9 / 298.9 | 1116 / 1094 / 1110 / 1083 / 1388 / 1311 | 1134 / 1126 / 1138 / 1093 / 1396 / 1320 |

F's levels sit 3-7% below the sweep_fvl3 F measured on trixie (hot_bat:
39.1 vs 42.0 at n = 1, 124.9 vs 134.7 at 128, 201.9 vs 208.1 at 4096), a
board plus harness difference (one-line descriptors, the extra warm-up
pass); the within-run pairs are what this campaign is for.

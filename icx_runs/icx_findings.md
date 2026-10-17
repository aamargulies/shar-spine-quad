# Intel Ice Lake-SP (Xeon Platinum 8375C): onboarding and first campaigns, 2026-10-13

Host tag `icx`. The user's "big" host is an AWS EC2 i4i.32xlarge in us-west-2
(hostname ip-172-31-11-73): two Intel Xeon Platinum 8375C @ 2.90 GHz
(Ice Lake-SP, Sunny Cove cores, family 6 model 106, 32 cores / 64 threads per
socket, 128 vCPUs), 48 KB L1D, 1.25 MB L2 per core, 54 MB L3 per socket, 991 GB,
Amazon Linux 2023, kernel 6.1 (amzn2023), 4 KB pages, THP `madvise`, no cpufreq
interface exposed (turbo under firmware control, cannot be pinned or read),
GCC 17.0.0 20260610 and Python 3.15 in `/usr/local/bin`, idle (load 0, no
users). `-march=native` resolves to `icelake-server` with `__AVX512VBMI2__`
defined, so `simd_quad_intel.c` takes the zmm block check (one 512-bit
compare) and has no in-loop prefetch -- the path Emerald Rapids runs, on the
previous core generation; Skylake-SP and Coffee Lake run the AVX2 path. The
first Intel server host with the repaired two-level harness, and the first
Ice Lake. Everything was driven from the Pi 5 over ssh: the sources were
rsynced to `~/QuadSearch` (without the share's stale binaries), built there
into `build_icx/`, and the run files copied back to `icx_runs/`.

Builds (all pass their correctness checks):

    g++ -O3 -march=native -std=c++20 bench.cpp simd_quad_intel.c -o bench
    g++ -O3 -march=native -std=c++20 -DQUADSEARCH_DESCRIPTOR_ALIGN=64 bench_twolevel.cpp simd_quad_intel.c -o bench_twolevel
    g++ -O3 -march=native -std=c++20 -DQUADSEARCH_DESCRIPTOR_ALIGN=64 bench_sweep_f_vs_lem.cpp simd_quad_intel.c -o bench_sweep_f_vs_lem
    python3 gen_intel_ab_variants.py V && g++ -O3 -march=native -std=c++20 -DQUADSEARCH_DESCRIPTOR_ALIGN=64 bench_ab_intel.cpp V/ab_tu_base.cpp V/ab_tu_np.cpp V/ab_tu_tail.cpp -o bench_ab_intel

Every run was pinned to core 3 of socket 0 (NUMA node 0, memory local by
first touch; the sibling thread 67 idle), with the drivers
`run_bench_flushed.sh icx 10`, `run_twolevel.sh icx 10` and
`run_sweep_f_vs_lem.sh icx 100 200 pi5_runs/sweep_n_list_f_vs_lem.txt` (179
sizes 1..4096, 10 runs, `order_seed` = run index), one after the other,
12:44-14:44 local (19:44-21:44 UTC). The machine is bare-metal class and it
shows: run-level drift 1.00x warm / 1.02x cold in the main bench, 1.00x hot
/ 1.01x cold in the sweep, 1.03-1.04x in three two-level modes (hot_bat
1.09x, see below).

## Flushed main bench (10 runs, `rebench_flushed_run{1..10}.txt`, `rebench_flushed_paired.txt`)

The 512 MB flush before every cold pass exceeds the 54 MB L3, but the cold
column walks the arrays in allocation order, so the L2 streamer hides most of
the miss latency at small n (n = 8 cold `intel` 10.2 ns against 3.0 warm; a
DRAM miss on this box is about 90 ns) -- as on every host but the Pi 5 the
cold column is a within-host A/B, not a cross-host cold number (CLAUDE.md,
`bench.cpp` entry). Paired within-run results (negative = the first-named
cell faster; WIN = >= 8 of 10 runs and |median| >= 3%):

- **Spine vs plain kernel** (`intels` vs `intel`): warm WIN(spine) at 32 and
  at every size from 128 up (-11% to -18%, 10/10; -1.0 to -2.9 ns), ties
  below; cold WIN(spine) at 32 and from 333 up (-14% at 333, -19% at 512,
  -28% at 617, -37% to -48% from 1001 up, 9-10/10; -8 to -102 ns), WIN(plain)
  at 11, 16, 64, 128 and 177 (+4% to +9%, the extra spine line of a single
  cold query), as on Coffee Lake and the Pi 5.
- **Line alignment** (`nA` rows): the plain kernel's aligned row ties warm
  at 21 of 22 sizes (|median| <= 2.3%; one WIN(aligned) at 64, -3.7%,
  10/10) and is 10-39% SLOWER cold at every size up to 177
  (9-10/10: the footprint of one-line copies in the sequential cold sweep, the
  same artefact as on the Pi 5 and Coffee Lake), a tie from 256 up with
  WIN(aligned) at 512, 617 and 2048 (-4% to -5%); the spine kernel's aligned
  row is 3-6.5% faster warm at 18 of 22 sizes (10/10; -0.2 to -0.8 ns) and,
  cold, 9-44% slower up to 177 (footprint again) but **14-29% faster from 512
  up** (-18% at 512-1001, -21% at 1024-1234, -14% at 1777, -20% at 2048, -25%
  to -29% at 2999-4096; 10/10; -11 to -32 ns), with 333 already -7.7% (9/10)
  and 256 a tie -- the five-line spine and the
  straddling block against four lines and one, as on Coffee Lake (27-40%)
  and the Pi 5 (16-37%, upper bound).
- **Compile-time `_spine_N` family**: WIN at every size, warm -34% to -38%
  (-2.7 to -4.8 ns), cold -25% at 256, -33% at 512, -37% at 1024, -35% at
  2048 and 4096 (-11 to -38 ns; 10/10 everywhere).
- **Padded descent**: warm mixed (WIN(pad) at 177, 256, 2999, 3967 by 6-10%,
  WIN(general) at 128, 333-1001, 1777-2048 by 7-12%), cold slower at every
  size but 256 and 3967 (ties at +0.8% and +2.4%; +4% to +26% elsewhere,
  8-10/10) -- not a candidate here either.

Levels (medians of 10, ns/query): n = 8 warm `intel` 3.0, cold 10.2; n = 128
warm 7.2 / 6.2 (plain / spine), cold 28 / 30; n = 4096 warm 16.2 / 13.4 /
8.6 (`intel_spine_4096`), cold 197 / 109 / 70; `intelsA` cold at 4096 77.
The box is about 1.1-1.2x faster warm than the Coffee Lake laptop with turbo
from n = 1001 up (plain kernel; 4096 warm 16.2 against 18.6; 1.1-2.6x below,
e.g. 3.0 against 7.9 at n = 8) and slower cold from n = 128 up: the plain
kernel 1.2-1.6x (78 against 49 at 512, 197 against 161 at 4096), the spine
kernel 1.0-1.5x (63 against 42 at 512, 109 against 96 at 4096) -- its DRAM
is slower, its L3 larger; read these as levels only.

## Two-level harness (10 runs, `twolevel_v2_run{1..10}.txt`, `twolevel_paired_v2.txt`; repaired harness, line-aligned descriptors)

The "hot" modes are outer-hot, inner first-touch; with a 54 MB L3 the inner
loads are L3 hits, as on Emerald Rapids and Graviton 4 (levels: hot_bat
geomean 82-89 ns, hot_ser 87-90, cold_bat 520-534, cold_ser 771-804).
hot_bat has a first-position effect: in nine of the ten runs the variant
timed first in the hot_bat pass ran 1.9-2.7x slower than its median over the
other runs that did not time it first (F in runs 1, 3 and 9: 122-123 ns
against 47; D in runs 4 and 10: 169-172 against 64; C in runs 2 and 8:
127-128 against 67; A in run 6: 137 against 73; B in run 7: 176 against 70),
and in run 5 Lem, first, was +15% and C, second, +51%; the second-timed
variant was otherwise 8-14% slower (Lem +0.4% in run 6), while E, H and I,
never timed first, stayed within 16% of their fastest run. Hence hot_bat
verdicts between F and A-E, H or I are ties by sign count (F vs D in runs
1-10: +90, -28, +76, -72, -24, -27, -27, -21, +92, -72) and hot_ser (drift
1.04x) is the hot mode to quote. The slow cell follows each run file's
`timing order hot_bat` line whichever variant is first, so the untimed
warm-up pass (one pass of A just before) does not absorb whatever slows the
first timed pass; nothing comparable happens at the start of the hot_ser
pass, and the cause is not identified.

| mode | best by rank | paired deltas vs the best (10 runs) |
|---|---|---|
| hot_bat | E (F -9.0% by median but 7/10, TIE) | D +21.4%, H +26.3%, C +27.1%, B +29.8%, A +38.3% (10/10), I +8.1% (9/10); Lem +281%, G +317% |
| hot_ser | **F** (10/10) | E +15.2%, D +43.0%, B +51.0%, I +56.6%, H +62.6%, C +105%, A +119%, G +155%, Lem +298% (all 10/10) |
| cold_bat | **C** (10/10) | D +12.8%, F +22.8%, I +22.9%, A +34.1%, B +45.4%, G +66.6%, E +84.6%, H +90.4%, Lem +92.4% (all 10/10) |
| cold_ser | **C** (10/10) | D +6.5%, A +7.1%, B +11.2%, F +30.1%, I +35.3%, E +35.6%, Lem +36.5%, H +37.4%, G +96.9% (all 10/10) |

- F vs Lem: -76.5% / -74.9% / -35.6% / -4.2% (10/10 in every mode); D vs
  Lem -68.4% / -64.2% / -41.5% / -22.6%; A vs Lem -64.3% / -45.4% / -30.9% /
  -21.9%. The cold_ser margin over Lemire is the smallest of any host (-4.2%),
  because Lemire's bsearch outer is what wins cold here (next section).
- F vs D: tie hot_bat (-25.5%, 7/10), -30.1% hot_ser (F, 10/10), +8.2%
  cold_bat and +23.3% cold_ser (D, 0/10). F vs E: -13.2% hot_ser, -32.8%
  cold_bat, -3.9% cold_ser (F, 10/10). C vs A -6.2% / -25.5% / -6.7% (C,
  10/10) and D vs C +12.8% / +6.5% cold (C): the compile-time inner behind
  the branchy outer is the cold configuration.
- Khuong & Morin (repaired prefetch): I vs F tie hot_bat (+19.1%, 3/10),
  +56.6% hot_ser (0/10), tie cold_bat (-0.6%), tie cold_ser (+1.7%); H vs E
  +26.3% / +41.2% hot (0/10), ties cold. I beats D in hot_bat (-10.6%, 8/10)
  and loses to it in the other three modes (+8.9% / +8.0% / +26.9%). The
  Eytzinger outer never beats Shar hot or the branchy outer cold here either.
- G (Shar inner) +364% / +155% hot, +34.5% / +51.3% cold against F: out.
- **Ship reading for Ice Lake-SP: F hot (hot_ser best 10/10, hot_bat a tie
  with E), C cold (both cold modes, 10/10; F is 23-30% behind)** -- the
  Skylake-SP / Emerald Rapids / Graviton 4 / Coffee Lake pattern with the
  largest cold margin for the branchy outer yet.

## F-vs-Lemire sweep (`sweep_fvl3_raw.txt`, `sweep_fvl3_paired.txt`, `icx_sweep_fvl3_data.py`, `bench_icx_sweep_fvl3{,_delta,_factorial}.png`)

7,160 cells (179 sizes x 4 modes x 10 runs, 100 sets x 200 reps, the Pi 5
campaigns' arrays and targets), 13:15-14:44 local, 0 failed; drift 1.00x hot,
1.01x cold. The identical-code gauge (Lem2 vs Lem from n = 16 up) fires at
13 of 164 sizes in hot_bat (8%: n = 16, the last size of the report's
n = 2-16 band, and 12 scattered sizes at 868-2497; -3.4% to -4.9%, 8-10/10),
at 1 in hot_ser (n = 32), at 23 in cold_bat (14%) and at 11 in cold_ser
(7%); |median| at most 4.9% hot (hot_bat n = 1680), 9.0% cold (cold_bat
n = 40).

- **Hot: F beats both Lemire kernels at every size**, WIN(F) 179 of 179 in
  both modes; in ns +23 to +46 per query in hot_bat and +37 to +70 in hot_ser
  by band, and the square puts it on the outer: Fb vs F +24 to +35 ns hot_bat
  (falling with n) and +35 to +55 hot_ser (rising), Lem vs LemS +18 to +37 /
  +40 to +45, WIN(Shar) 179/179 in both pairs and both modes. The inner
  contrasts are small hot: Fb vs Lem and F vs LemS -2 to +6 ns at 33-265
  (Lemire's gap-16 kernel ahead: WIN(LemS) at 60 / 58 of 179 sizes, WIN(Lem)
  59 / 51 against Fb -- the same tail-sweep bands Coffee Lake showed, at
  more sizes) and -3 to -27 ns from 266 up (WIN(F) 108 / 113, WIN(Fb) 96 /
  93).
- **Cold: the branchy outer wins at almost every size, by 93-222 ns per
  query in cold_ser and 21-221 ns in cold_bat (band medians), and Lemire's
  stack with it.** Fb vs F is WIN(Fb) at 174 of 179 sizes in
  cold_bat and 177 in cold_ser (-21 ns at 1-32 and -64 at 33-128 rising to
  -221 at 2049-4096 in cold_bat; -93, -167, -194, -219, -222, -211, -214 by
  band in cold_ser); Lem vs LemS the same (179/179 in both cold modes, -42 to
  -222 ns). Shar's nine-step cmov chain over the 1 KB key array is nine
  dependent misses after the flush, which the out-of-order core cannot
  overlap, while `std::lower_bound` mispredicts and speculates ahead (the
  Khuong & Morin mechanism); on this box with a ~90 ns DRAM access that is
  the whole cold budget (two-level cold_ser medians: F 806 ns, A 656, C 612). Hence
  Lem vs F cold_ser WIN(Lem) 170 / WIN(F) 4 / TIE 5 (-110 to -180 ns by band,
  the only host where Lemire leads cold at n = 4096: -116 ns at 2049-4096)
  and cold_bat WIN(Lem) 132 / WIN(F) 16 / TIE 31 (-27 to -87 ns). The inner
  is the other way: Fb vs Lem (spine vs Lemire's kernel behind the same
  bsearch) WIN(Fb) 141 cold_bat (-30 ns at 33-128 to -192 at 2049-4096) and
  109 cold_ser (from 129 up, -17 to -109 ns); F vs LemS WIN(F) 164 / 90. So
  two-level A (bsearch outer + spine inner) is the cold configuration, by
  the outer alone, and the n = 4096 two-level result (C 23-30% ahead of F
  cold) is the same fact.
- Lemire's 2026-10-02 revision beats his April kernel in hot_bat at n = 2-15
  (-6% to -16%, 10/10); its other 13 hot_bat WINs (n = 16 and 12 sizes at
  868-2497, -3.4% to -4.9%, 8-10/10; 27 of 179 in all) fall where the two
  kernels run identical code (the gauge above). It is mixed in hot_ser at
  n <= 14 (WIN(Lem2) at 6 and 8-11, WIN(Lem) at 1-2 and 12-14) and 45-72%
  SLOWER in cold_ser at n = 1-15 (10/10 at every size; +13.5% to +32.8% on
  Coffee Lake with turbo); the other cold cells are ties with scattered WINs
  either way (cold_bat WIN(Lem) 16 / WIN(Lem2) 11 of 179, cold_ser above
  n = 15 1 / 10).

Decision for this host: F for hot work, two-level A / C for cold work; the
Shar outer is not a cold option on Ice Lake-SP. The kernel A/B (`sweep_abi1`:
the vector tail on the zmm path, and Gnp = G as an identical-code gauge) has
its own section below.

## Kernel A/B (`sweep_abi1_raw.txt`, `sweep_abi1_paired.txt`, `icx_sweep_abi1_data.py`, `bench_icx_sweep_abi1{,_delta,_delta_ns}.png`; zmm path)

`bench_ab_intel.cpp` with the variants generated from the kernel at blob
418fd3a8 (the same variants as the Coffee Lake campaign,
`cfl_runs/sweep_abi1_variants.diff`), built on the box (`kernel_path=zmm`):
Shar outer fixed, inner variants F (general-n spine kernel), Ft (F with the
vector tail), G (plain kernel), Gnp (G without the in-loop prefetch), Gt (G
with the vector tail) and LemS (Lemire's 2026-04-27 kernel). 179 sizes x 4
modes x 10 runs = 7,160 cells, 100 sets x 200 reps, `order_seed` = run index,
14:44-17:03 local (21:44-00:03 UTC), 8,328 s, 0 failed, pinned to core 3;
run-level drift 1.00x in both hot modes and 1.01x in both cold modes. WIN =
>= 8 of 10 runs and |median| >= 3%.

- **Identical-code gauge.** The zmm path never had the in-loop prefetch, so
  Gnp is the same source as G at every size: it fired at 0 of 179 sizes in
  both hot modes and at 2 in each cold mode (cold_bat 89-92, +3.5% to +4.7%;
  cold_ser n = 2 and 21, +5.7% and +3.9%), with WIN(G) every time. The Ft /
  Gt contrasts are identical code below 32 and wherever n % 32 == 0 (no
  tail); they fired there at 3 cells, all in cold_ser below 12 (Ft vs F
  4, 9, 11).
- **The vector tail on the zmm path** (one 512-bit load of the array's last
  32 elements instead of the scalar sweep of the partial last block). Ft vs
  F: WIN(Ft) at 38 sizes in hot_bat (39-62 by -3% to -21%, 78-95 -3% to
  -13%, 116-124, 141-156, 178-190 and single sizes 217-380), 34 in hot_ser
  and 31 in cold_bat (42-62 by -4% to -28%, 78-95, 112-124, 151-156,
  184-190), no effect loss in any mode; cold_ser ties. In ns the gain sits in
  the same bands as on Coffee Lake: -5.2 / -4.2 ns hot (hot_bat / hot_ser) at
  48-62, -3.1 / -3.0 at 81-95, -1.9 / -1.8 at 112-124, -1.6 / -1.9 at
  210-217, -62 and -48 ns in cold_bat at 48-62 and 81-95. Gt vs G: WIN(Gt)
  at 39 / 27 / 33 / 0 sizes, no loss (-4.7 ns hot_bat and -92 ns cold_bat at
  48-62). At n = 4096 (no tail) every tail pair ties.
- **Against Lemire's kernel**: with the shipped tail F vs LemS has WIN(LemS)
  at 25 sizes in hot_bat (29-31, 48-75, 81-95 by +14% to +18%, 124) and 26 in
  hot_ser; with the vector tail Ft vs LemS has 12 and 12 -- the 48-62 band
  becomes a tie or a win for the spine inner (-1.4 ns by band in hot_bat),
  and Lemire's gap-16 kernel stays ahead at 29-31, 64-68 and 81-95 in
  hot_bat (+3% to +10%, +2.4 ns by band at 81-95) and at 1-3, 31, 64-71 and
  81-89 in hot_ser (+4% to +14%). So on this core the tail halves
  Lemire's hot wins rather than removing them (on Coffee Lake it left one);
  the residue is at two and three blocks, where the spine function delegates
  to the plain kernel. From 161 up F and Ft win hot at every size (-4% to
  -38%); cold_bat Ft is ahead at 167 of 179 sizes.
- **The prefetch**: nothing to measure on this path (Gnp = G above).
- G vs F (plain kernel against the spine inner, for the record): F faster
  at 127 / 120 sizes hot and 124 / 101 cold, G faster at one size per cold
  mode.

Levels at n = 4096 (medians of 10, ns/query; F / Ft / G / Gnp / Gt / LemS):
hot_bat 49.8 / 50.5 / 71.1 / 70.9 / 70.1 / 77.3, hot_ser 53.8 / 53.9 / 74.2 /
74.0 / 74.0 / 84.0, cold_bat 770 / 766 / 815 / 814 / 823 / 952, cold_ser
958 / 959 / 1079 / 1073 / 1072 / 1074.

**Decision**: together with the Coffee Lake campaign (AVX2 form,
`cfl_runs/prefetch_ab_findings.md`) the vector tail wins in the same bands
on both instruction paths, with no effect loss on this host and two single
cold cells on Coffee Lake; it was adopted into `simd_quad_intel.c` on
2026-10-17 (all three general-n kernels, plus a guard that returns false
without loading when the tail is empty, a case these campaigns could not
exercise), and checked exhaustively on this box (zmm) and on the laptop
(AVX2): every n from 1 to 300 and 511-513, 1023-1025, 2047-2049, 4095, 4096,
four arrays per size, all 65,536 keys, three kernels, 244.6 M lookups per
host, no mismatch.

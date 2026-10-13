# Flushed main bench on the Pi 5: ten paired runs on the second board (2026-10-12/13)

`bench.cpp` has flushed every cold pass since 2026-10-11 and printed a
line-aligned `nA` row for every size since 2026-10-12. The first flushed run
(`rebench_flushed_run1.txt`, board "trixie", 2026-10-12) established that the
flush evicts; these ten runs on the idle second board "eight"
(`rebench_flushed_eight_run{1..10}.txt`, 23:26-00:27, `run_bench_flushed.sh`
with `BENCH_TAG=_eight`, pinned to core 3, `ondemand`, 53-56 C, binary built
on trixie with GCC 17.0.0 20260704, kernel blob f7c140b8 = the Pi 5 kernel
*with* its in-loop prefetch) give the paired analysis
(`rebench_flushed_eight_paired.txt`, `compute_bench_paired.py pi5 --glob
'pi5_runs/rebench_flushed_eight_run*.txt'`). Run-level drift 1.00x warm and
1.14x cold over 198 shared cells; WIN = >= 8 of 10 runs and |median| >= 3%.
The identical-code gauge (pi5s vs gv4s, byte-identical spine kernels) ties
at all 22 sizes warm (|median| <= 2.4%) and at 20 of 22 cold (WIN at 1001
+13% and 1234 +3.7%): the cold WIN rule fires at ~9% of cells on identical
code in this harness, so single cold cells below ~10% are not quotable.

## 1. The in-loop prefetch (gv4 vs pi5: the kernel without it vs with it) -- removed

| regime | result |
|---|---|
| warm (L1-hot, 5,000 repeated queries per array) | WIN(no prefetch) at every size from 128 up: -3.0% (128), -3.6%, -4.2%, -7.7% (333), -7.4%, -7.6%, -7.6%, -6.4%, -6.8%, -7.6%, -7.6%, -6.2%, -6.2%, -6.9% (4096), 10/10 in every cell; ties below 128 (same code) |
| cold (512 MB flush, one query per array, sequential) | no-prefetch faster in 12 of the 14 sizes from 128 up: WIN at 333 (-4.3%), 617 (-18.4%), 1001 (-13.2%), 1777 (-10.7%), 2048 (-11.7%), 3967 (-4.3%), 4096 (-4.8%); ties at 128-256, 512, 1234, 2999; the prefetch WINs only at 1024 (+7.7%, 9/10) and leads at 1234 by +2.1% (8/10, a TIE) |

Together with the two-level kernel A/B of the same day (`sweep_ab1_findings.md`
section 3: 3-14% faster with the prefetch in the outer-hot modes from
n ~ 667, 4-8% slower in both cold modes), the archived "net loss" holds in
both regimes of the main bench and the only gain is one regime of the
two-level harness. The line was removed from `simd_quad_pi5.c` on
2026-10-13; the Pi 5 and Graviton plain kernels now compile to identical
instructions, so from the next flushed run on the pi5/gv4 columns are a
second identical-code gauge. Every archived Pi 5 number, including these
runs, measured the kernel with the prefetch; the `gv4` columns of the same
runs are the kernel as it is now.

## 2. Line alignment (the `nA` rows): large cold gains for the spine kernels, with a layout caveat

Warm: ties at every size from 32 up for every column (|median| <= 1.3% for
the tuned kernels, <= 2.0% for `simd`); at 8-23 the tuned kernels' aligned
rows differ by up to 2.4% (the identical-code gauge's own warm spread),
apart from one WIN(aligned), `m4` at 8 (-4.3%, 9/10, -0.2 ns on a 4.7 ns
level), and the reference `simd_quad` reads +3% to +9% slower in its
aligned row (WIN(simd) at 8, 11 and 23; +2.8% at 16, a tie), plausibly a
code-placement effect of the second lambda. Cold:

| column | aligned row vs plain row, cold |
|---|---|
| `pi5s` (spine) | WIN(aligned) at 21 of 22 sizes: -26% (8), -36% (11), -45% (16), -16% (23), -52% (32), -33% (47), -36% (64), -20% (89), -30% (128), -33% (177), -31% (256), -38% (333), -35% (512), -34% (617), -14% (1001), -36% (1024), tie (1234), -34% (1777), -37% (2048), -24% (2999), -19% (3967), -18% (4096, -33.8 ns); 10/10 in every WIN cell |
| `gv4s`, `m4s` (spine) | the same picture: 21 and 22 WINs, -8% to -51% |
| `pi5` (plain) | WIN(aligned) at 12 sizes 8-333 (-11% to -54%); from 512 up never a WIN(aligned): ties at 9 of 10 sizes (-2.9% to +2.6%; 2048 is -2.9% at 10/10, under the 3% bar) and WIN(plain) at 1024, where the aligned row is slower (+4.9%, 9/10, +10 ns) |
| `linear`, `binary`, `simd` | `linear` WIN(aligned) at all 22 (-10% at 4096, -18% at 1024, -36% at 8, -61% at 32); `binary` 14 WINs up to 617; `simd` 11 WINs up to 333 |

Two things are mixed here. At the n = 8 control nothing can straddle (16
bytes at 16-byte alignment), yet every kernel's aligned row is 22-39%
faster cold there (10/10 in all nine columns; 35-50% at 11, 44-57% at 16,
15-25% at 23, and 51-61% at 32, one block, where the plain row can
straddle): the copies are made in a second pass and sit one per line at a
regular stride, which the sequential cold sweep over 4,000 arrays streams
better than the std::vector chunks interleaved with four spine vectors
each. The same layout effect is still 8-19% at n >= 1024 for `linear`
(-8% at 1777 to -19% at 1234), which alignment cannot help at all. So the
spine kernels' cold gains at n >= 128 (pi5s 14-38% and gv4s 21-36% at 13
of the 14 sizes, 1234 a tie; m4s 8-33% at all 14) are an upper bound on
the alignment effect in this harness; the plain kernel gains nothing from
alignment from 512 up (nine ties and a WIN(plain) at 1024, +4.9%, 9/10),
which says the block load's straddle costs nothing measurable (both lines
are fetched in parallel), and the spine's four-versus-five lines is where
alignment acts. The cleaner alignment numbers are the two-level kernel A/B
on the same board (random container access, no sweep: 3-7% faster cold from
n ~ 512, `sweep_ab1_findings.md` section 4) and the Coffee Lake main bench,
whose `linear` control moves by 0-5% cold at n >= 512 apart from two
turbo-set cells (617 -8%, 1777 -6%), with WIN(aligned) at 2 of those 10
sizes with turbo and 4 without, while the aligned spine kernel gains
26-40% cold from 617 up in both sets (10/10 at every size but one 9/10; at
512 -27% without turbo, a -15% tie with it) (`cfl_runs/cfl_findings.md`,
`cfl_runs/rebench_flushed{,_noturbo}_paired.txt`). For a Roaring
integration: align containers of a block or more, never pad tiny ones.

## 3. The compile-time spine family, with the flush

| pair | warm | cold |
|---|---|---|
| `pi5_spine_256` vs `pi5s` | -16.6% (10/10) | **-10.2% (10/10)** -- the archived "+42% cold regression" at 256 was the pre-flush harness |
| `pi5_spine_512` | -9.1% | -20.2% (10/10) |
| `pi5_spine_1024` | -19.1% | -17.0% (10/10) |
| `pi5_spine_2048` | -19.1% | -16.4% (10/10) |
| `pi5_spine_4096` (the hybrid) | -27.6% (10/10) | -7.8% (8/10, WIN) |
| `gv4_spine_{256..4096}` | the same code: -16%, -9%, -21%, -19%, -29% | -11%, -20%, -17%, -16%, -8% |
| `m4_spine_4096` vs `m4s` (Apple hybrid, on Pi hardware) | -24.2% (10/10) | -2.4% (8/10, TIE) |

The Apple hybrid's "+188-212% cold structural regression" does not appear
on Pi hardware with an explicit flush before both measurements -- consistent
with the measurement-order explanation of CLAUDE.md open item 5; the test on
Apple hardware is still pending. The Graviton padded descent
(`gv4_spine_pad`) stays mixed (warm WIN(pad) 7 / WIN(gv4s) 7 / TIE 4; cold
2 / 4 / 12): warm -7% to -9% at 177, 256, 1024, 1234, 4096 and -15% at
2999, 3967, +5% to +9% at 128, 333-1001, 1777, 2048 (all 10/10); cold +7%
to +9% at 617, 1001, 1777, 2048 (8-10/10; 1024 and 1234 in between are
ties) and -4% at 177 and 2999 (9/10).

## 4. Spine kernel vs plain kernel (`pi5s` vs `pi5`)

Warm WIN(spine) at 32 (-16%) and 47 (-6%) -- sizes at which the spine
kernel still delegates to the plain kernel (`num_blocks <= 3`), so those
two cells compare two compilations of the plain kernel, not the spine --
and at every size from 128 up (-16% at 128 to -29% at 2048; -28% at 4096),
10/10 in every WIN cell; WIN(plain) at 8 and 23 (+3%); ties at 11, 16, 64
and 89. Cold WIN(plain) at every size up to 128 (+6% to +25%: the spine
kernel's extra spine line and spine-pointer read cost in a single cold
query) and WIN(spine) from 177 up (-5% at 177, 9/10; -18% at 256, -42% at
617, -57% at 1001, -45% at 4096, 10/10 at every size from 256 up).

## 5. Levels against the pre-flush archive

The plain rows' medians are the `pi5_flushed_warm` / `pi5_flushed_cold`
dicts of `plot.py` (own figures `bench_pi5_flushed_{warm,cold}.png`; the
cross-host figures stay pre-flush). Against the 2026-05-13 archive on the
first board (`pi5_warm` / `pi5_cold`): the six tuned kernels' warm cells
sit within -8% / +6% of the archive's fast mode (the per-run minimum of
`rebench_run{1..5}.txt`) at every size except n = 23, where all six read
+12% to +17% (12.1-12.6 ns against 10.7-11.0), and n = 47, where the two
m4 kernels read +19% to +20% (15.6-15.7 against a minimum of 13.1,
fast-mode runs 13.1-13.3) -- the same
values to within 0.2 ns in all ten runs and in the trixie flushed run 1,
so a property of the GCC 17 build rather than of the board; the archive's
1.45-1.5x slow-mode cells at 11, 16, 23, 128 are absent; `linear` is
2.7-3.4x faster from 64 up because GCC 17 auto-vectorises `std::find`.
Cold cells are 5-7x the archive at n = 8 for the six tuned kernels (DRAM
instead of L1/L2: 38-47 ns against 6.4-7.9; `simd_quad` 3.3x,
`linear`/`binary` 1.7-1.9x) and 1.6-6.7x at n = 11-32 (2.5-3.1x at 11,
3.6-6.7x at 16, 1.6-2.1x at 23, 3.4-6.1x at 32), 1.22-1.26x at n = 4096
for the general-n spine kernels (184-190 ns against 148-155, +35 to +39
ns; the compile-time hybrids 1.3x for `m4_spine_4096`, 206 against 158,
and 1.7-1.8x for `gv4_spine_4096` / `pi5_spine_4096`, 187 / 205 against
109 / 112, bimodal across the ten runs at 164-168 and 204-208 ns) and
1.15-1.25x for the plain kernels (335-350 against 267-299, +44 to +68 ns;
the reference `simd_quad` 1.24x, `binary` 1.33x). The flush therefore
added at least as much per query to the plain kernels as to the spine
kernels at 4096, so these medians do not separate what the pre-flush
"cold" column already had in DRAM (the plain kernel's array lines) from
what it did not (the spines, pointer and target vectors); the single
trixie run (`rebench_flushed_run1.txt`) does show a gap, spine 1.43-1.48x
against plain 1.27-1.39x, but these ten runs do not.

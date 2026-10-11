# Eytzinger prefetch-offset A/B (Raspberry Pi 5, 2026-10-10)

Raw outputs of the A/B that established the H/I prefetch-offset defect
described in `Text/corrections_2026-10.md`, section 1. They were produced by
the 2026-10-11 review on this host and are archived here so the numbers
quoted in the corrections document, `KhuongMorin.md` and `CLAUDE.md` have a
source. They predate the repaired harness; `pi5_runs/twolevel_v2_run*.txt`
are the ten-run re-measurement with the fix in place.

## Set 1: `ab_run{1,2,3}.txt` (harness `bt_ab.cpp`, driver `run_ab.sh`)

`bt_ab.cpp` is the pre-fix `bench_twolevel.cpp` with four extra variants
appended to the standard A–I + Lem set. Three runs of `bt_ab 100 200 all`
(100 sets × 200 hot reps, pinned to CPU 2, ~38 s each, `ab_timing.txt`).
Variants:

| row | outer search | prefetch |
|---|---|---|
| I | Eytzinger (1-based) | shipped: `kPrefOff = 3*kGap/2 − 1` on the unaligned `std::vector` |
| I2 | Eytzinger | none |
| I3 | Eytzinger, array cache-line aligned | corrected `kPrefOff = kGap/2`, prefetch skipped (branch) when it would leave the allocation |
| I4 | Eytzinger, array cache-line aligned | corrected `kPrefOff = kGap/2`, out-of-range prefetch address masked instead of skipped |
| I5 | Eytzinger, array cache-line aligned | shipped formula on the aligned base (isolates alignment from the offset) |

`ab_summary.py` (run from this directory) prints the paired per-run deltas.
Paired deltas, I4 vs I (corrected vs shipped), per run: cold_bat −31.2% /
−10.1% / −23.1%, cold_ser −20.6% / −27.7% / −51.4%, hot modes −1.5% to
−6.2%. I3 vs I: cold_bat −15.7% / −29.1% / −35.1%, cold_ser +3.2% / −31.1%
/ −55.3%. The shipped prefetch vs no prefetch (I vs I2): cold_bat +20.1% /
+19.8% / +10.6%, cold_ser −7.0% / +27.4% / +22.5%, hot +3.8% to +6.6%, i.e.
the mis-aimed prefetch was worse than issuing none in five of six cold cells.
Each output also prints an outer-index cross-check of the Eytzinger search
against `std::lower_bound` (0 mismatches) and the 64-byte phase histogram of
`keys_eytz.data()`, which shows the unaligned allocations.

## Set 2: `verify_ab_run{1,2}.txt` (harness `verify_bt_ab.cpp`)

An independent A/B written by the review's verification pass with its own
variant set (`F`, `I`, `Inopf` = no prefetch, `Ioff`, `Ifix`, `Ifixug`,
`Ialsh`; definitions in `verify_bt_ab.cpp`), five rounds per file, columns
hot_bat / hot_ser / cold_bat / cold_ser in ns per query. Kept as supporting
evidence; set 1 is the one quoted in the write-ups.

Caveat for both sets: the cold cells are single passes of 100 queries and
swing widely run to run (see the D cold_bat outlier in `ab_run3.txt`), so
only the sign pattern across runs should be read, not the magnitudes.

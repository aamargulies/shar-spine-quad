#!/usr/bin/env python3
"""Side-by-side benchmark comparison across Pi 5, M4 Max, and Intel.

Datasets collected with `./bench 4000 5000` on each machine.
  Pi 5:      GCC 15,         -O3 -mcpu=cortex-a76
  M4 Max:    Apple clang 21, -O3 -mcpu=apple-m4
  Intel SKX: GCC 16,         -O3 -march=native  (Xeon Platinum 8175M,
             family 6 model 85, Skylake-SP. Shared EC2 tenant, so cold
             numbers are somewhat noisier than bare-metal; each cell
             below is the per-cell median across 5 runs of
             `./bench 4000 5000`.)

On SKX, -march=native sets __AVX512BW__ but not __AVX512VBMI2__, so
simd_quad_intel auto-selects the 2x 256-bit AVX2 block check and avoids
the AVX-512 frequency downclock. On Ice Lake-SP / Sapphire Rapids /
Emerald Rapids / Granite Rapids, __AVX512VBMI2__ is set and the zmm
single-compare path kicks in.

Data provenance (2026-10-11 audit): the pi5_* dicts carry all 22 sweep
sizes (pi5_runs/rebench_run{1..5}.txt). The m4/m1/skx/emr/gv4 dicts carry
only the 10 power-of-two sizes present in their archived
{host}_runs/rebench_run{1..5}.txt files; each dict is paired with its own
size list (m4_sizes, ...) and the plotting / table code indexes by that
list. See the PROVENANCE comment above each dict.

Cache state (2026-10-11): every main-bench dict below comes from the
pre-flush bench.cpp, whose cold column had no cache flush (DRAM-cold only on the
Pi 5, and there only for n > 256; Text/corrections_2026-10.md section 5). bench.cpp now writes
512 MB before every cold pass and prints a "# cold column:" line, so its
output is not comparable with these dicts: add new dicts with their own
provenance rather than mixing.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Master size grid: the 22-point sweep that `./bench 4000 5000` prints
# today. Only the Pi 5 dataset below covers all 22 sizes. Every other
# host's archived data (2026-05-01 rebench) was taken with the 10-size
# power-of-two sweep, so each host dict is paired with its own size list
# and the plotting / table code indexes by that list, never by `sizes`.
sizes = [8, 11, 16, 23, 32, 47, 64, 89, 128, 177,
         256, 333, 512, 617, 1001, 1024, 1234, 1777,
         2048, 2999, 3967, 4096]
pow2_sizes = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]

pi5_sizes = sizes
m4_sizes  = pow2_sizes
m1_sizes  = pow2_sizes
skx_sizes = pow2_sizes
emr_sizes = pow2_sizes
gv4_sizes = pow2_sizes

# The sweep has 22 log-spaced sizes, but labeling all 22 on a log x-axis
# produces overlapping tick labels. Label only powers of two (plus 4096)
# so the axis stays readable.
label_sizes = [s for s in sizes if (s & (s - 1)) == 0]
label_strs  = [str(s) for s in label_sizes]

# Raspberry Pi 5 (Cortex-A76 @ 2.4 GHz). Per-cell median across 5 runs of
# `./bench 4000 5000`, 2026-05-13 resample (post-hybrid ship), GCC 15 with
# -O3 -mcpu=cortex-a76. Raw outputs in pi5_runs/rebench_run{1..5}.txt;
# aggregation via pi5_runs/compute_medians.py. Now 9 ARM columns (linear,
# binary, simd ref, pi5, pi5+spine, m4, m4+spine, gv4, gv4+spine) since the
# m4 and gv4 variants both compile on A76 and are useful for cross-host
# comparison at the "m4 variant" / "gv4 variant" row.
# Verified 2026-10-11: all 396 cells (22 sizes x 9 columns x warm/cold)
# reproduce exactly as per-cell medians of pi5_runs/rebench_run{1..5}.txt.
# Caveat (2026-10-12, found by comparing with the first flushed run,
# pi5_runs/rebench_flushed_run1.txt): the five runs have a slow mode
# 1.45-1.50x above the fast one, uniform across the nine columns of a row
# (consistent with a clock step under the ondemand governor), and these warm
# medians sit in the slow mode at n = 11, 16, 23 and 128 in most columns and
# in single columns at 8, 32 and 512. Within-row A/Bs are unaffected; the
# absolute small-n warm levels there are inflated by up to 1.5x. The cold
# dicts below are pre-flush (see Text/corrections_2026-10.md, section 5).
pi5_warm = {
    "linear (std::find)":          [   8.90,    8.50,   18.30,   21.90,   25.20,   34.50,   37.70,   50.30,  104.00,   96.60,  138.30,  178.60,  272.00,  403.90,  552.00,  546.00,  649.90,  961.10, 1090.80, 1558.00, 2208.70, 2195.80],
    "binary (std::binary_search)": [  20.60,   25.20,   32.10,   33.50,   33.00,   36.50,   33.40,   35.70,   55.60,   42.40,   45.80,   47.80,   57.30,   53.40,   68.60,   57.50,   59.10,   62.10,   63.30,   66.60,   68.50,   68.60],
    "simd_quad (reference)":       [  10.20,   16.30,   10.70,   20.20,   12.00,   21.50,   12.20,   17.30,   19.40,   21.70,   17.90,   22.60,   25.90,   28.00,   28.20,   24.30,   27.50,   30.60,   27.60,   31.30,   31.30,   31.10],
    "simd_quad_pi5":               [   5.40,   13.00,    7.00,   13.50,    9.30,   16.90,   10.40,   18.80,   19.70,   19.30,   17.60,   21.40,   23.80,   27.40,   27.60,   23.40,   30.30,   27.50,   27.10,   33.60,   33.60,   30.10],
    "simd_quad_pi5 + spine":       [   5.40,   10.50,    7.00,   15.70,    8.00,   14.40,   11.00,   19.00,   16.60,   15.40,   13.00,   16.60,   18.00,   20.00,   20.10,   17.30,   22.60,   20.00,   19.80,   24.90,   25.10,   22.50],
    "simd_quad_m4":                [   7.30,   14.00,    7.20,   16.50,    6.80,   13.30,    9.60,   17.10,   18.20,   23.10,   14.10,   19.10,   21.80,   23.90,   28.40,   20.50,   26.90,   28.00,   23.90,   27.40,   27.60,   26.80],
    "simd_quad_m4 + spine":        [   7.20,   13.50,    7.30,   16.30,    5.70,   13.30,    8.00,   15.60,   17.60,   23.00,   12.60,   15.60,   21.80,   19.70,   23.50,   16.80,   21.90,   23.20,   19.60,   22.40,   22.50,   21.80],
    "simd_quad_graviton":          [   4.70,   13.10,    7.00,   16.00,    9.50,   15.20,   10.60,   18.60,   15.20,   18.40,   15.80,   19.90,   28.10,   25.50,   25.50,   22.40,   29.00,   25.40,   25.30,   32.00,   32.00,   28.60],
    "simd_quad_graviton + spine":  [   4.50,   13.30,    6.90,   16.10,    9.80,   14.30,   10.60,   18.50,   13.40,   15.60,   13.10,   16.00,   21.10,   20.00,   19.90,   17.20,   22.70,   20.00,   19.80,   25.00,   25.10,   22.50],
}
pi5_cold = {
    "linear (std::find)":          [  24.10,   37.40,   41.60,   43.00,   58.70,   43.20,   46.70,   88.30,   84.60,  102.00,  141.50,  175.10,  341.70,  349.40,  598.10,  554.70,  696.40,  811.70,  923.50, 1341.80, 1695.20, 1718.00],
    "binary (std::binary_search)": [  23.80,   42.60,   45.50,   51.30,   56.80,   41.30,   46.10,   74.30,   82.50,   82.10,   87.70,  114.00,  185.50,  196.80,  246.20,  200.70,  235.80,  270.00,  257.70,  323.10,  326.10,  323.40],
    "simd_quad (reference)":       [  13.30,   22.90,   19.60,   22.90,   22.80,   19.90,   16.80,   29.90,   37.20,   60.80,   68.40,  106.10,  174.00,  226.00,  264.50,  189.60,  240.50,  275.40,  234.60,  301.40,  291.70,  296.30],
    "simd_quad_pi5":               [   7.10,   17.80,   12.50,   21.20,   14.70,   17.20,   13.80,   31.30,   32.20,   51.40,   57.20,   89.10,  172.70,  191.30,  211.70,  162.90,  256.10,  210.90,  214.50,  313.30,  304.00,  299.00],
    "simd_quad_pi5 + spine":       [   7.90,   18.90,   17.40,   20.00,   17.00,   14.90,   13.80,   32.20,   33.80,   46.90,   41.80,   93.90,  130.60,  132.60,   93.30,  112.10,   92.50,  143.70,  146.80,  182.00,  152.40,  150.70],
    "simd_quad_m4":                [   7.40,   18.80,   11.00,   21.40,   15.10,   18.50,   13.80,   29.90,   30.30,   51.00,   48.30,   71.80,  122.80,  165.50,  190.70,  160.50,  198.60,  219.40,  219.50,  364.90,  268.00,  267.30],
    "simd_quad_m4 + spine":        [   6.90,   17.60,   12.60,   21.20,   13.50,   18.40,   15.90,   28.70,   25.00,   41.70,   50.80,   71.50,   85.90,  133.00,  141.60,  106.00,  141.30,  146.60,  136.90,  168.10,  148.00,  147.70],
    "simd_quad_graviton":          [   6.40,   18.20,   12.70,   22.00,   16.20,   17.80,   13.40,   30.30,   24.60,   44.70,   47.10,   70.00,  152.00,  170.00,  202.20,  155.30,  212.40,  199.00,  201.70,  326.40,  282.10,  291.90],
    "simd_quad_graviton + spine":  [   7.20,   17.50,    9.50,   20.90,   12.30,   14.10,   12.90,   30.20,   27.80,   47.00,   43.10,   64.40,  114.40,  123.80,   79.00,   88.70,  103.10,  138.60,  137.40,  182.20,  151.00,  154.70],
}

# Apple M4 Max (P-core). Refreshed 2026-05-01 with the Graviton 4 variant
# also linked in (so every ARM host's bench now runs 9 algo columns).
# Apple clang 21, -O3 -mcpu=apple-m4; per-cell median across 5 runs of
# `./bench 4000 5000`. Raw outputs in m4_runs/rebench_run{1..5}.txt;
# aggregation by m4_runs/compute_medians.py.
#
# Columns: linear, binary, simd (reference), pi5, pi5+spine, m4, m4+spine,
# gv4, gv4+spine. The gv4 variant -- plain NEON, gap=32, no in-loop
# prefetch -- runs on M4 too, and at n=4096 warm ties the m4 variant
# within noise (gv4+spine 4.6 vs m4+spine 4.3); cold at n=4096 it actually
# *beats* m4+spine on this host (5.1 vs 6.5), because gap=32 touches half
# the cache lines per block check and M4's 128-B line is oversized for
# the data.
#
# PROVENANCE: m4_runs/rebench_run{1..5}.txt (2026-05-01), 10 sizes
# (powers of two 8..4096 = m4_sizes), per-cell median of the 5 runs,
# identical to the output of m4_runs/compute_medians.py. 22-size values
# previously here had no archived source and were removed 2026-10-11.
# [NOTE 2026-10-11: the byte-identical pi5+spine kernel reads 11.6 ns cold on the same host, so
#  this ordering is measurement order in an unflushed cold column, not line count;
#  Text/corrections_2026-10.md section 5.]
m4_warm = {
    "linear (std::find)":          [   1.50,    2.70,    5.10,    9.70,   19.20,   37.70,   81.30,  157.10,  304.00,  593.30],
    "binary (std::binary_search)": [   4.30,    4.20,    4.60,    5.10,    5.80,    6.60,    7.60,    8.60,    9.90,   11.10],
    "simd_quad (reference)":       [   2.00,    1.40,    1.60,    2.10,    2.50,    3.20,    3.70,    4.70,    5.30,    6.30],
    "simd_quad_pi5":               [   1.40,    1.20,    1.90,    2.00,    2.40,    2.80,    3.80,    4.30,    5.60,    6.20],
    "simd_quad_pi5 + spine":       [   1.40,    1.20,    2.40,    2.40,    2.10,    2.30,    2.80,    3.30,    4.00,    4.60],
    "simd_quad_m4":                [   1.60,    1.40,    1.40,    2.10,    2.10,    2.60,    3.00,    3.60,    4.20,    5.00],
    "simd_quad_m4 + spine":        [   1.60,    1.40,    1.20,    2.50,    2.60,    2.30,    2.80,    3.20,    3.70,    4.30],
    "simd_quad_graviton":          [   1.40,    1.20,    1.90,    1.90,    2.20,    2.60,    3.40,    3.90,    4.90,    5.50],
    "simd_quad_graviton + spine":  [   1.40,    1.20,    2.40,    2.40,    2.10,    2.30,    2.80,    3.30,    4.00,    4.60],
}
m4_cold = {
    "linear (std::find)":          [   4.50,    6.10,    7.10,   11.60,   19.00,   33.90,   68.20,  130.70,  240.10,  481.10],
    "binary (std::binary_search)": [   4.80,    4.40,    3.90,    4.60,    5.40,    7.10,   12.60,   22.10,   43.20,   66.60],
    "simd_quad (reference)":       [   5.40,    1.40,    1.40,    2.10,    2.50,    4.10,    5.70,    9.20,   16.10,   31.50],
    "simd_quad_pi5":               [   1.20,    1.00,    1.70,    1.90,    2.50,    3.80,    6.00,    7.00,   10.40,   15.20],
    "simd_quad_pi5 + spine":       [   1.30,    1.10,    2.20,    2.40,    2.40,    2.60,    3.10,    5.80,    4.10,   11.60],
    "simd_quad_m4":                [   1.40,    1.20,    1.20,    2.10,    2.50,    4.10,    5.10,    6.70,   10.40,   16.80],
    "simd_quad_m4 + spine":        [   1.70,    1.30,    1.20,    2.30,    2.70,    3.30,    3.50,    6.00,    4.20,    6.50],
    "simd_quad_graviton":          [   1.50,    1.30,    1.70,    1.70,    2.40,    3.70,    5.40,    5.80,    8.70,   11.70],
    "simd_quad_graviton + spine":  [   1.20,    1.00,    2.30,    2.30,    2.30,    2.30,    3.40,    3.70,    5.10,    5.10],
}

# Intel Skylake-SP (Xeon Platinum 8175M, family 6 model 85).
# Per-cell median across 5 runs of `./bench 4000 5000`, -march=native.
# Columns from the bench output on x86: linear, binary, simd (ref),
# intel, intel+spine.
#
# On this uarch -march=native sets __AVX512BW__ but not __AVX512VBMI2__,
# so the 512-bit block-check path is intentionally disabled and the code
# uses 2x 256-bit AVX2 -- the zmm path loses to frequency downclock here.
#
# Re-measured 2026-05-01 alongside the bench_twolevel run on the same
# SKX EC2 host. Raw outputs in skx_runs/rebench_run{1..5}.txt; medians
# computed by skx_runs/compute_medians.py. Warm columns are within ~2-10%
# of the 2026-04-30 run; cold columns at large n came out ~25-30% quieter
# this session (shared EC2 tenancy drift, same caveat EMR has).
#
# PROVENANCE: skx_runs/rebench_run{1..5}.txt (2026-05-01), 10 sizes
# (powers of two 8..4096 = skx_sizes), per-cell median of the 5 runs,
# identical to the output of skx_runs/compute_medians.py. 22-size values
# previously here had no archived source and were removed 2026-10-11.
skx_warm = {
    "linear (std::find)":          [  15.60,   19.70,   16.60,   17.80,   21.40,   25.40,   37.10,   49.50,  106.40,  166.90],
    "binary (std::binary_search)": [  24.90,   29.50,   36.50,   44.70,   52.60,   61.30,   64.70,   70.20,   76.90,   82.30],
    "simd_quad (reference)":       [  16.70,   14.90,   16.20,   18.50,   18.90,   22.60,   23.90,   27.00,   29.30,   33.00],
    "simd_quad_intel":             [  13.10,   12.30,   14.00,   15.10,   18.00,   19.70,   23.10,   25.30,   29.40,   31.60],
    "simd_quad_intel + spine":     [  12.90,   12.90,   15.70,   16.00,   17.50,   18.70,   20.00,   21.40,   25.20,   26.80],
}
skx_cold = {
    "linear (std::find)":          [  21.20,   23.40,   26.60,   31.30,   41.90,   62.00,  102.80,  177.90,  326.50,  582.50],
    "binary (std::binary_search)": [  30.00,   35.10,   41.00,   50.00,   60.60,   84.70,  117.30,  162.30,  205.10,  276.80],
    "simd_quad (reference)":       [  19.40,   12.90,   14.00,   16.30,   19.00,   39.80,   63.10,   84.60,  141.10,  171.50],
    "simd_quad_intel":             [  11.50,   11.00,   12.20,   14.10,   16.70,   25.80,   42.10,   75.50,  127.90,  180.90],
    "simd_quad_intel + spine":     [  11.70,   11.50,   13.60,   17.40,   17.70,   24.60,   42.80,   60.50,   93.80,  132.70],
}
have_skx = len(skx_warm["simd_quad_intel"]) == len(skx_sizes)

# Intel Emerald Rapids (Xeon Platinum 8559C, family 6 model 207, EC2 bare-metal
# neighbor). Per-cell median across 5 runs of `./bench 4000 5000`, GCC with
# -march=native. This uarch sets __AVX512VBMI2__, so simd_quad_intel uses the
# 512-bit single-compare block-check fast path and simd_quad_intel.c's
# speculative-prefetch gate also resolves to "removed" (the A/B from the
# 2026-04-30 session: 4-13% warm / up to 18% cold speedup vs. the prefetch-kept
# path; the __AVX512VBMI2__ gate auto-selects "remove" on EMR and "keep" on
# SKX/AVX2-only hosts).
#
# Re-measured 2026-05-01 with a fresh 5-run median (raw outputs in
# emr_runs/rebench_run{1..5}.txt, medians computed by compute_rebench.py).
# Warm-cache columns are essentially identical to the 2026-04-30 run (the
# observation from memory "EMR warm is near-identical across runs" still
# holds); cold-cache columns at n>=1024 shifted up a bit in this session
# (noisier EC2 neighbors, most likely - same caveat the SKX measurements had).
#
# PROVENANCE: emr_runs/rebench_run{1..5}.txt (2026-05-01), 10 sizes
# (powers of two 8..4096 = emr_sizes), per-cell median of the 5 runs,
# identical to the output of emr_runs/compute_rebench.py. 22-size values
# previously here had no archived source and were removed 2026-10-11.
emr_warm = {
    "linear (std::find)":          [   2.80,    3.90,    6.50,   12.20,   24.40,   45.40,   86.10,  179.10,  343.80,  655.40],
    "binary (std::binary_search)": [  14.60,   18.50,   22.90,   27.40,   32.80,   38.90,   44.70,   49.80,   55.00,   60.60],
    "simd_quad (reference)":       [   2.80,    3.30,    3.10,    5.00,   10.70,    7.50,   15.10,   10.30,   18.90,   13.80],
    "simd_quad_intel":             [   2.50,    2.80,    3.10,    3.30,    4.70,   10.30,    7.60,   15.50,   10.10,   19.50],
    "simd_quad_intel + spine":     [   2.50,    2.50,    3.50,    3.70,    4.40,   10.30,    6.60,   14.70,    9.00,   18.00],
}
emr_cold = {
    "linear (std::find)":          [   8.20,   10.00,   12.00,   17.00,   23.50,   42.30,   82.00,  140.90,  298.90,  493.60],
    "binary (std::binary_search)": [  17.50,   22.20,   28.10,   32.00,   36.60,   45.50,   62.40,   77.50,   98.70,  117.60],
    "simd_quad (reference)":       [   8.20,    3.20,    3.30,    5.00,   11.80,   16.60,   36.80,   43.80,   56.60,   71.00],
    "simd_quad_intel":             [   2.50,    2.50,    3.10,    3.20,    5.20,   15.40,   28.00,   38.00,   47.20,   64.90],
    "simd_quad_intel + spine":     [   2.50,    2.50,    3.50,    3.70,    5.10,   13.20,   16.70,   23.40,   25.90,   37.20],
}
have_emr = len(emr_warm["simd_quad_intel"]) == len(emr_sizes)

# AWS Graviton 4 (Arm Neoverse V2, CPU part 0xd4f). r8g EC2 instance.
# Per-cell median across 5 runs of `./bench 4000 5000`, GCC 11.5 with
# -O3 -mcpu=neoverse-v2. Re-measured 2026-05-01 from gv4_runs/rebench_run{1..5}.txt
# (the original gv4_runs/baseline_run*.txt was the prefetch A/B control set).
#
# V2 is a 64-byte-line 128-bit-NEON ARM core with 3 load-capable pipes (earlier
# text here said 4) and a deep
# OoO window, so simd_quad_graviton uses gap=32 (cache-line sized) and
# drops the A76's speculative __builtin_prefetch inside the interpolation
# loop. Polarity matches M4 Max and Emerald Rapids ("hint is pure
# dispatch waste on wide-OoO cores").
#
# PROVENANCE: gv4_runs/rebench_run{1..5}.txt (2026-05-01), 10 sizes
# (powers of two 8..4096 = gv4_sizes), per-cell median of the 5 runs,
# identical to the output of gv4_runs/compute_medians.py.
# The dict keeps 5 of the bench's 9 ARM columns (linear, binary, simd
# reference, gv4, gv4+spine), as that aggregator emits. 22-size values
# previously here had no archived source and were removed 2026-10-11.
gv4_warm = {
    "linear (std::find)":          [   3.20,    5.00,    9.30,   15.80,   31.50,   72.80,  115.40,  236.50,  462.70,  906.50],
    "binary (std::binary_search)": [  11.70,   15.00,   18.40,   21.90,   25.30,   29.20,   33.40,   37.70,   42.40,   47.10],
    "simd_quad (reference)":       [   3.60,    3.30,    3.20,    4.90,    9.60,    7.80,   15.20,   11.10,   19.90,   15.20],
    "simd_quad_graviton":          [   2.90,    2.90,    3.30,    3.50,    5.10,    9.80,    7.90,   15.50,   11.10,   20.00],
    "simd_quad_graviton + spine":  [   2.80,    2.90,    3.90,    4.10,    4.50,    8.70,    6.20,   13.40,    7.90,   16.20],
}
gv4_cold = {
    "linear (std::find)":          [   6.60,    8.60,   11.40,   17.00,   29.40,   54.70,  102.40,  203.90,  403.10,  835.10],
    "binary (std::binary_search)": [  14.40,   18.30,   22.70,   26.80,   31.90,   37.30,   43.30,   56.60,   78.60,  119.80],
    "simd_quad (reference)":       [   6.20,    3.20,    3.40,    5.20,   10.60,   10.80,   21.40,   33.20,   55.90,   81.70],
    "simd_quad_graviton":          [   2.60,    2.60,    3.30,    3.90,    6.30,   12.60,   16.20,   31.00,   43.90,   65.00],
    "simd_quad_graviton + spine":  [   2.60,    2.80,    3.90,    4.40,    5.90,   10.40,   15.40,   17.40,   22.60,   34.60],
}
have_gv4 = len(gv4_warm["simd_quad_graviton"]) == len(gv4_sizes)

# Apple M1 Pro (Firestorm P-core). Per-cell median across 5 runs of
# `./bench 4000 5000`, 2026-05-01, Apple clang 21 with -O3 -mcpu=apple-m1.
# Raw outputs in m1_runs/rebench_run{1..5}.txt; aggregation via
# m1_runs/compute_medians.py.
#
# The M1 Pro is structurally the same Apple-silicon family as the M4 Max:
# 128-byte cache line, 128 KB L1D per P-core, 128b NEON, no SVE, wide OoO.
# It therefore links + ships the *same* simd_quad_m4.c variant (gap=64,
# vld1q_u16_x4 block check, no speculative prefetch, 128-B / 1-line spine
# at n=4096). No M1-specific .c file is needed.
#
# Absolute numbers are slower than the M4 Max (warm n=4096 m4+spine ~6.3
# vs ~4.3 on M4 Max, cold n=4096 m4+spine ~11.1 vs ~6.5 on M4 Max) because
# M1 Pro has older cores and ran this benchmark on battery-plugged Apple
# clang. Relative structure is identical: m4 variant + spine is the fastest
# among the cross-host variants, gv4 variant (gap=32) comes in slightly
# behind at large-n warm, pi5 variant third.
#
# PROVENANCE: m1_runs/rebench_run{1..5}.txt (2026-05-01), 10 sizes
# (powers of two 8..4096 = m1_sizes), per-cell median of the 5 runs,
# identical to the output of m1_runs/compute_medians.py. 22-size values
# previously here had no archived source and were removed 2026-10-11.
m1_warm = {
    "linear (std::find)":          [   2.20,    3.80,    7.10,   13.40,   26.40,   51.50,  111.10,  211.90,  413.80,  803.70],
    "binary (std::binary_search)": [   8.00,    7.30,    7.30,    8.10,    9.20,   10.40,   12.30,   13.80,   15.40,   17.40],
    "simd_quad (reference)":       [   3.40,    2.60,    2.60,    3.10,    3.60,    4.60,    5.30,    6.70,    7.70,    9.20],
    "simd_quad_pi5":               [   2.50,    2.40,    2.70,    2.80,    3.70,    4.30,    5.80,    6.70,    8.50,    9.40],
    "simd_quad_pi5 + spine":       [   2.50,    2.40,    3.20,    3.10,    3.00,    3.50,    4.10,    4.80,    5.60,    6.40],
    "simd_quad_m4":                [   2.40,    2.40,    2.40,    3.10,    3.60,    4.00,    4.70,    5.50,    6.40,    7.50],
    "simd_quad_m4 + spine":        [   2.40,    2.40,    2.50,    3.40,    3.70,    3.80,    4.40,    4.90,    5.60,    6.30],
    "simd_quad_graviton":          [   2.40,    2.40,    2.70,    2.90,    3.40,    4.00,    5.10,    5.90,    7.40,    8.20],
    "simd_quad_graviton + spine":  [   2.40,    2.40,    3.20,    3.10,    3.10,    3.40,    4.00,    4.80,    5.70,    6.30],
}
m1_cold = {
    "linear (std::find)":          [   6.30,    7.80,   10.00,   15.20,   25.50,   47.00,   87.30,  167.20,  327.70,  648.40],
    "binary (std::binary_search)": [   7.30,    6.70,    6.60,    7.10,    8.80,   11.80,   15.90,   23.40,   83.30,  161.00],
    "simd_quad (reference)":       [   7.60,    2.60,    2.60,    3.00,    3.80,    5.60,    8.10,   15.60,   30.10,   58.20],
    "simd_quad_pi5":               [   2.50,    2.50,    2.60,    2.80,    3.90,    5.50,    7.90,   10.20,   23.10,   33.80],
    "simd_quad_pi5 + spine":       [   2.50,    2.50,    3.10,    3.10,    4.40,    4.80,    9.30,    9.10,   12.60,   23.20],
    "simd_quad_m4":                [   2.50,    2.40,    2.50,    3.00,    4.00,    5.40,    7.20,   10.00,   20.30,   37.10],
    "simd_quad_m4 + spine":        [   2.60,    2.50,    2.50,    3.40,    4.10,    4.60,    5.10,    8.50,    8.30,   11.10],
    "simd_quad_graviton":          [   2.40,    2.40,    2.60,    2.80,    3.60,    5.60,    7.10,    9.70,   19.80,   27.10],
    "simd_quad_graviton + spine":  [   2.40,    2.40,    3.10,    3.20,    3.50,    3.90,    4.90,    5.80,   11.40,   15.40],
}
have_m1 = len(m1_warm["simd_quad_m4"]) == len(m1_sizes)

# Guard: every value list must be exactly as long as its host's size list.
# (Prevents a 22-point list being pasted next to a 10-point size list again.)
for _host, _xs, _w, _c in [("pi5", pi5_sizes, pi5_warm, pi5_cold),
                           ("m4",  m4_sizes,  m4_warm,  m4_cold),
                           ("m1",  m1_sizes,  m1_warm,  m1_cold),
                           ("skx", skx_sizes, skx_warm, skx_cold),
                           ("emr", emr_sizes, emr_warm, emr_cold),
                           ("gv4", gv4_sizes, gv4_warm, gv4_cold)]:
    for _d in (_w, _c):
        for _k, _v in _d.items():
            assert len(_v) == len(_xs), \
                f"{_host}[{_k!r}] has {len(_v)} values for {len(_xs)} sizes"

# n=4096 compile-time specialization (simd_quad_intel_spine_4096), median of 5
# ./bench 4000 5000 runs on EMR 2026-05-01. Isolated from the main table
# because it only exists at n=4096. Warm/cold are the two numbers.
# PROVENANCE (established 2026-10-11): emr_runs/shipped_run{1..5}.txt
# (2026-05-12, post-hybrid-promotion ./bench 4000 5000 x5), 4096* row
# intel_spine_4096, medians via emr_runs/compute_shipped.py ->
# emr_runs/shipped_summary.txt / hybrid_summary.txt ("warm 6.50 cold
# 24.36"). The "2026-05-01" above is stale: the 2026-05-01 rebench rows
# measured the retired unroll (14.02 warm in rebench_run1.txt).
emr_spine_4096 = {"warm": 6.50, "cold": 24.36}
# Same structure for Graviton 4 (simd_quad_graviton_spine_4096), measured
# on the same r8g host 2026-05-01 (median of 5 runs from rebench_run{1..5}).
# PROVENANCE (established 2026-10-11): gv4_runs/fullsweep_run{1..5}.txt
# (2026-05-12, 22-size sweep), 4096* row gv4_spine_4096, medians via
# gv4_runs/compute_fullsweep_medians.py -> gv4_runs/fullsweep_summary.txt
# ("gv4_spine_4096: warm 7.00 cold 27.24"). The "2026-05-01 ... from
# rebench_run{1..5}" above is stale: those rows measured the retired
# unroll (median 14.67 warm / 29.15 cold).
gv4_spine_4096 = {"warm": 7.00, "cold": 27.24}
# Same structure for SKX (simd_quad_intel_spine_4096 on the AVX2 block-check
# path), measured on Xeon 8175M 2026-05-01 (median of 5 runs). Warm is a
# small win vs the general-n spine (27.5 -> 27.1, ~-1.5%) -- on SKX the
# scalar interpolation loop already runs at AVX-512 license L2 so the
# branch-removal effect is smaller than EMR's; cold is noise (131.9 vs
# 131.1 median, hidden by shared-tenant memory variance).
# NOTE 2026-10-11: the paragraph above describes the retired unroll (27.5 -> 27.1).
# The shipped hybrid below is 18.92 warm / 185.01 cold (skx_runs/hybrid_summary.txt):
# -32% warm 5/5, but +40% cold against a general-n control stable to +-0.6% in the
# same runs (Text/corrections_2026-10.md section 2.3). The 'license L2' rationale is
# wrong: light zmm ops trip L1, and the gated SKX build executes no zmm at all.
# PROVENANCE (established 2026-10-11): skx_runs/hybrid_run{1..5}.txt
# (2026-05-12 hybrid-vs-unroll A/B), 4096* row intel_spine_4096 (= the
# hybrid), medians per skx_runs/hybrid_summary.txt ("warm 18.92 cold
# 185.01"). The "2026-05-01" and "27.5 -> 27.1" above are stale: they
# describe the retired unroll measured in rebench_run{1..5}.txt.
skx_spine_4096 = {"warm": 18.92, "cold": 185.01}
# Same structure for M4 Max (simd_quad_m4_spine_4096, gap=64 -> 64 spine
# entries -> 128 B = 1 M4 cache line, quaternary descent of exactly three
# iterations with no binary step). Measured 2026-05-01, median of 5 runs.
#
# Warm is a clean win (4.34 -> 3.65, ~-16%). Cold is a *regression*
# (6.47 -> 18.65, +188%) and the per-run variance is stable across all
# 5 runs -- not noise. The mechanism is that the general-n spine path
# has an early __builtin_prefetch of the spine + num_blocks<=3 early-out
# + a data-dependent quaternary descent that's short enough that M4's
# wide OoO overlaps the spine miss with the final block load, while the
# unrolled compile-time path issues all three quaternary tiers in one
# basic block before the final block load, which on cold gives the core
# no chance to launch the block-load miss early. The M4's HW prefetcher
# doesn't recognize the irregular base stride between tier probes, so
# the block load waits on DRAM after all three tier misses resolve. On
# the 64-byte-line hosts the spine is 4 lines so the streamer engages
# during the descent; on M4 the spine is exactly 1 line so there's
# nothing sequential to engage on. Conclusion: ship the specialization
# for the warm case, but callers that do a lot of first-touch lookups
# should prefer simd_quad_m4_spine.
# PROVENANCE (established 2026-10-11): m4_runs/hybrid_run{1..5}.txt
# (2026-05-12 hybrid-vs-unroll A/B), 4096* row m4_spine_4096_hybrid,
# medians via m4_runs/compute_hybrid.py -> m4_runs/hybrid_summary.txt
# ("hybrid: warm 3.71 cold 21.94"). The "Measured 2026-05-01" and the
# 4.34 -> 3.65 / 6.47 -> 18.65 figures above describe the retired unroll
# measured in rebench_run{1..5}.txt (2026-05-01), not these values.
# [NOTE 2026-10-11: the 'structural' reading is now a hypothesis. In the pre-flush bench.cpp the spine kernel's cold pass
#  ran right after the non-spine pass with identical targets (L2 hit) while the 4096* row ran
#  after its own 32 MB sweep; the same asymmetry reproduces on the Pi 5. Untested with a flush on
#  Apple hardware (bench.cpp flushes since later on 2026-10-11; re-run pending). Text/corrections_2026-10.md section 5.]
m4_spine_4096 = {"warm": 3.71, "cold": 21.94}
# Pi 5 (Cortex-A76) simd_quad_pi5_spine_4096, gap=32 -> 128 spine entries ->
# 256 B = 4 cache lines. Shape is the 2026-05-12 hybrid (3-iter quaternary
# + branchless 2-probe finish), same as the GV4 and EMR _spine_4096.
# Measured on the Pi 5 4-core A76, median of 5 runs from
# pi5_runs/hybrid_run{1..5}.txt.
#
# The hybrid-vs-unroll A/B gave warm 23.36 -> 19.42 (-16.9% by ratio of medians;
# paired per-run median -31.0%, Text/corrections_2026-10.md section 2.3; monotone
# across 5/5 runs) with cold 132.1 -> 140.9 (+6.7%, inside the 107-214 ns
# cold variance band). That refutes the 2026-05-01 "GCC 15 already hoists
# loop control so branch-removal is a wash on Pi 5" hypothesis: the
# 2-probe finish saves one dependent load-use round (the binary step)
# which no compiler pass can reconstruct. Vs the general-n pi5_spine the
# hybrid's warm median is 17.75 (-27.6%) and cold 136.75 (-7.2%). Unroll
# retired; simd_quad_pi5_spine_4096 IS the hybrid. Prior-unroll numbers
# for historical comparison: warm 23.78, cold 142.10.
# PROVENANCE (established 2026-10-11): pi5_runs/rebench_run{1..5}.txt
# (2026-05-12), the LAST "4096* | pi5_spine=.. pi5_spine_4096=.." row of
# each file (each run prints that A/B row twice; pi5_runs/compute_medians.py
# keeps the last match), per-cell median: warm 15.98, cold 111.85. The
# "pi5_runs/hybrid_run{1..5}.txt" above is stale as the source of these two
# numbers: the hybrid A/B rows give 19.42 warm / 140.94 cold (see
# pi5_runs/hybrid_summary.txt).
pi5_spine_4096 = {"warm": 15.98, "cold": 111.85}
# M1 Pro simd_quad_m4_spine_4096 (same compile-time specialization that
# ships on M4 Max — shared Apple-silicon gap=64 / 128-B-line variant).
# Measured 2026-05-01, median of 5 runs on Apple clang 21 -O3 -mcpu=apple-m1.
#
# Reproduces the M4 Max cold regression in the same direction and roughly
# the same proportion (M4 Max: 6.47 -> 18.65, +188%; M1 Pro: 11.1 -> 32.7,
# +194%). Same mechanism: gap=64 -> 128-B spine = 1 cache line, nothing
# sequential for the HW streamer to latch on; the unrolled compile-time
# path issues all three quaternary tier probes in a single basic block
# before the final block load, which on cold gives the core no chance to
# launch the block-load miss early. The fact that the regression is almost
# the same magnitude on M1 Pro as on M4 Max — despite the M1's older,
# narrower cores — is strong evidence the effect is structural (cache
# line size + gap) and not specific to the M4's execution engine. The
# warm number is a slight regression on M1 Pro (6.31 -> 6.16, -2.4%,
# within noise) whereas it was a clean win on M4 Max (-16%); expected
# for the older core where the branch-removal headroom is smaller.
#
# Ship recommendation on M1 Pro: same as M4 Max -- ship the compile-time
# specialization for narrow-API callers; callers doing first-touch lookups
# should prefer simd_quad_m4_spine.
# PROVENANCE (established 2026-10-11): m1_runs/hybrid_run{1..5}.txt
# (2026-05-12 hybrid-vs-unroll A/B), 4096* row m4_spine_4096_hybrid,
# per-cell median of the 5 runs: warm 6.05 (6.10 6.05 6.02 6.06 6.05),
# cold 32.12 (32.54 32.12 29.48 33.42 31.65). The "Measured 2026-05-01"
# and "6.31 -> 6.16" above describe the retired unroll measured in
# rebench_run{1..5}.txt (median 6.16 warm / 32.70 cold), not these values.
# [NOTE 2026-10-11: same caveat as the M4 block: a measurement-order hypothesis, untested with a
#  flush (bench.cpp flushes since later on 2026-10-11; re-run pending); the +194% is +196% from the 4096* rows (openevolve_m4_spine_4096/README.md note).]
m1_spine_4096 = {"warm": 6.05, "cold": 32.12}

# Intel Emerald Rapids two-level spine micro-bench, median of 5 runs
# 2026-05-13 on Xeon Platinum 8559C (raw outputs in
# emr_runs/twolevel_run{1..5}.txt). Re-measured under the 4-mode harness
# (hot_bat / hot_ser / cold_bat / cold_ser) post bench_cold targets[si][1]
# fix, replacing the 2026-05-01 2-mode numbers (which had the outer-miss
# short-circuit bug in the cold path). Aggregator:
# emr_runs/compute_twolevel.py; summary: emr_runs/twolevel_summary.txt.
#
# Deltas vs A (hot_bat  hot_ser  cold_bat  cold_ser):
#   B vs A:   -1.2%   -15.9%    +8.1%    +4.7%
#   C vs A:  -55.0%   -10.2%   -24.1%    -5.0%
#   D vs A:  -42.4%   -18.8%    -4.0%    +2.2%
#   E vs A:  -50.9%   -38.8%   +18.1%   +18.5%
#   F vs A:  -59.8%   -48.5%    -5.2%   +16.2%
#   G vs A: +101.6%   +25.8%   +68.6%  +108.6%
#  Lem vs A: +35.2%   +31.4%   +57.9%   +56.3%
#
# Deltas vs D (outer spine + n=4096 inner):
#   E vs D:  -14.7%   -24.6%   +23.0%   +16.0%
#   F vs D:  -30.2%   -36.5%    -1.3%   +13.8%
#   G vs D: +250.1%   +55.0%   +75.6%  +104.2%
#
# F vs G: hot_bat +401.5%, hot_ser +144.3%, cold_bat +77.9%, cold_ser
# +79.5% -- G catastrophic on hot and bad on cold, same structural reason
# as SKX/M4/Pi5/M1 (12 dependent loads on 8 KB inner, streamer gets nothing).
#
# F vs Lem (how much our stack improves on the published baseline):
#   hot_bat  -70.3%   hot_ser  -60.8%   cold_bat -40.0%   cold_ser -25.6%
#
# F is strict best on hot_bat / hot_ser; F ties D on cold_bat (263 vs 267,
# -1.3%) but loses to D on cold_ser (+13.8%). EMR's 3 load AGUs + wider
# OoO than SKX absorb most of the Shar cmov chain's cold-outer penalty,
# so the SKX / Pi 5 full cold reversal does NOT reproduce on EMR: the
# cold_bat picture is flat (D wins by 1%, noise) and cold_ser is the only
# mode where D cleanly wins by ~14%. This puts EMR between M4 Max (no
# reversal, F ties D cold) and M1 Pro (partial reversal, F wins cold_bat
# loses cold_ser) -- consistent with the "OoO width + absolute clock"
# hypothesis, with EMR closer to M4 than to SKX despite sharing the x86
# uarch family with SKX.
#
# Ship recommendation on EMR: F for hot throughput everywhere; D is a
# reasonable cold-serial alternate for tight dep-chain workloads.
# NOTE (2026-10-11): the dict below holds the 2026-05-18 re-bench levels
# (A-I + Lem). The delta tables in the comment above are ratios of
# per-cell medians; because each variant's median can come from a
# different run they are not reliable comparisons -- paired per-run
# comparisons live in emr_runs/twolevel_paired.txt. H/I were measured
# with the mis-aimed Eytzinger prefetch (fixed in bench_twolevel.cpp
# 2026-10-11, not yet re-benchmarked).
# No archived run supports the 2026-05-13 delta tables in the comments above: commit 5fdbb0a
# overwrote those files in place (Text/corrections_2026-10.md section 2.3).
emr_twolevel = {
    # (hot_bat, hot_ser, cold_bat, cold_ser). 5-run medians 2026-05-18 (H/I re-bench).
    "A  bsearch outer + general-n inner":          (136.62, 113.12, 262.28, 446.37),
    "B  two-level spine outer + general-n inner":  (110.09,  94.99, 282.89, 440.29),
    "C  bsearch outer + n=4096 inner":             ( 62.63, 103.61, 200.71, 410.39),
    "D  two-level spine outer + n=4096 inner":     ( 79.30,  92.20, 251.27, 428.82),
    "E  Shar branchless outer + general-n inner":  ( 67.91,  69.32, 311.29, 518.94),
    "F  Shar branchless outer + n=4096 inner":     ( 55.43,  58.12, 240.31, 512.30),
    "G  Shar outer + Shar inner (no spine)":       (267.22, 143.00, 448.36, 923.46),
    "H  Eytzinger outer + K&M PF (pre-fix) + general-n inner":   ( 66.75,  70.72, 363.50, 631.33),
    "I  Eytzinger outer + K&M PF (pre-fix) + n=4096 inner":      ( 55.05,  62.17, 315.77, 607.45),
    "Lem  Lemire reference (bsearch + simd_quad)": (178.70, 148.98, 428.60, 666.15),
}
# SKX two-level spine micro-bench, median of 5 runs 2026-05-13 on Xeon 8175M
# (raw outputs in skx_runs/twolevel_run{1..5}.txt). Re-measured with the
# 4-mode harness (hot_bat / hot_ser / cold_bat / cold_ser), which
# replaces the old 2-mode (warm / cold) harness. Each mode crosses two
# axes: cache state (hot = same set reused 200 times, cold = one query
# per set with LLC-thrash before timing) and query dispatch (batched =
# independent queries, OoO can overlap; serial = result-dep carried
# forward, exposes critical-path latency). See CLAUDE.md findings for
# interpretation.
#
# Values are stored as 4-tuples (hot_bat, hot_ser, cold_bat, cold_ser).
# Older host dicts below use 2-tuples (warm, cold) for pre-4-mode data;
# twolevel_bar() handles both.
#
# Observations:
#   hot_bat vs hot_ser: hot_ser < hot_bat for every variant except G
#     (e.g. A 234 vs 168, F 111 vs 88). The batched mode pays pipeline
#     pressure when multiple dependent chains race for the AGUs; with a
#     single in-flight query (serial) the OoO engine dispatches the
#     short scalar chain back-to-back without resource contention.
#     Surprising at first but consistent across variants, matching
#     published observations for low-latency code paths on wide-OoO
#     Intel cores running below the AVX-512 license floor.
#   cold_bat vs cold_ser: cold_ser >= cold_bat for A, B, C, D, F, G.
#     Biggest gap is G (cold_bat 761 vs cold_ser 1248, 64% longer on
#     serial) -- 12-deep dep chain on 8 KB working set can't hide any
#     DRAM latency without independent queries in flight.
#   F remains strict best on hot_bat and hot_ser; on cold F loses to
#     C/D on cold_bat and to A/D on cold_ser. Cold-regime picture
#     flipped vs old harness -- previously F looked best cold because
#     (a) first-touch batched mode was measuring something closer to
#     throughput than latency and (b) the Shar cmov chain is
#     throughput-friendly. With a real cold-serial measurement the
#     outer-spine variants claw back enough of the cold cost that
#     F only wins cold by amortizing over many queries.
#
# Deltas vs A (hot_bat  hot_ser  cold_bat  cold_ser):
#   B vs A:   -4.7%    -26.7%    +4.3%    +12.8%
#   C vs A:  -13.6%    -15.9%   -29.1%    -2.9%
#   D vs A:  -42.0%    -38.7%   -2.1%     -4.3%
#   E vs A:  -45.6%    -38.8%  +26.9%    +22.7%
#   F vs A:  -52.4%    -47.3%  +19.8%    +12.2%
#   G vs A: +34.0%    +80.4%   +11.7%    +70.9%
#
# Deltas vs D (outer spine + n=4096 inner):
#   E vs D: -6.1%     +0.5%    +29.6%    +28.2%
#   F vs D: -17.9%   -14.1%   +22.4%    +17.2%
#   G vs D: +131.1%  +194.2%   +14.2%    +78.5%
#
# Deltas vs F (ship recommendation): G vs F +181.3% hot_bat,
# +242.4% hot_ser, -6.8% cold_bat, +52.3% cold_ser.
#
# Ship recommendation on SKX: F under normal workloads (hot path
# dominated by throughput of independent queries). For cold-serial
# workloads (tight dep chains on fresh data) D is competitive, but F
# loses by only a small margin on cold and wins by a wide margin on
# hot; F remains the default.
# NOTE (2026-10-11): the dict below holds the 2026-05-18 re-bench levels
# (A-I + Lem). The delta tables in the comment above are ratios of
# per-cell medians; because each variant's median can come from a
# different run they are not reliable comparisons -- paired per-run
# comparisons live in skx_runs/twolevel_paired.txt. H/I were measured
# with the mis-aimed Eytzinger prefetch (fixed in bench_twolevel.cpp
# 2026-10-11, not yet re-benchmarked).
# No archived run supports the 2026-05-13 delta tables in the comments above: commit 5fdbb0a
# overwrote those files in place (Text/corrections_2026-10.md section 2.3).
skx_twolevel = {
    # (hot_bat, hot_ser, cold_bat, cold_ser). 5-run medians 2026-05-18 under
    # full A-I + Lem 10-variant harness (H/I = Eytzinger outer + K&M PF (pre-fix)
    # per Khuong & Morin 2017 Listing 6).
    # Lem is the published Lemire reference (bsearch outer + simd_quad.c
    # inner, gap=16, no spine). Same outer as A (what CRoaring ships);
    # inner is the blog-post baseline. Provides the fair reference for
    # judging how much our stack (F = Shar outer + compile-time n=4096
    # spine inner) improves on the published research.
    "A  bsearch outer + general-n inner":          (235.33, 155.16, 778.10, 794.65),
    "B  two-level spine outer + general-n inner":  (216.26, 127.51, 782.86, 843.58),
    "C  bsearch outer + n=4096 inner":             (148.06, 134.88, 668.83, 718.35),
    "D  two-level spine outer + n=4096 inner":     ( 95.58,  96.18, 554.10, 710.10),
    "E  Shar branchless outer + general-n inner":  ( 86.62,  88.17, 947.75, 962.42),
    "F  Shar branchless outer + n=4096 inner":     ( 84.42,  83.72, 594.47, 826.85),
    "G  Shar outer + Shar inner (no spine)":       (304.27, 299.74, 781.71,1215.71),
    "H  Eytzinger outer + K&M PF (pre-fix) + general-n inner":   (100.65, 109.12,1052.16,1067.39),
    "I  Eytzinger outer + K&M PF (pre-fix) + n=4096 inner":      ( 88.79, 101.20, 718.71, 941.36),
    "Lem  Lemire reference (bsearch + simd_quad)": (258.17, 270.41, 951.47, 953.71),
}
# M4 Max two-level spine micro-bench (bench_twolevel, 200 sets x 200 hot reps,
# num_containers=512, inner_n=4096, gap=64 outer and inner). Median of 5 runs
# 2026-05-13 on the same M4 host as the m4_warm/m4_cold table above, under the
# 2026-05-13 4-mode harness (hot_bat/hot_ser/cold_bat/cold_ser) and post
# bench_cold targets[si][1] fix. Raw outputs in m4_runs/twolevel_run{1..5}.txt;
# compute_twolevel.py aggregates.
#
# Deltas vs A (hot_bat / hot_ser / cold_bat / cold_ser):
#   B vs A:  -70.8%  +23.8%  -44.6%   +0.8%
#   C vs A:  -81.0%  -26.2%  -55.5%  +24.6%
#   D vs A:  -77.9%  +12.4%  -48.9%  -27.8%
#   E vs A:  -84.1%  -44.5%  -53.1%  -31.7%
#   F vs A:  -84.6%  -47.4%  -52.0%  -25.9%
#   G vs A:  -26.9% +166.5%  -26.4% +115.8%
#
# Deltas vs D:
#   F vs D:  -30.3%  -53.2%   -6.0%   +2.7%   (F best hot, F ~ D cold)
#   G vs D: +231.1% +137.0%  +44.2% +198.9%
#
# F is strict best on hot_bat (15.81) / hot_ser (16.80); F ties D on cold_bat
# (146.25 vs 155.62, F -6%) and cold_ser (256.05 vs 249.38, F +3%). The SKX
# cold reversal ("F loses to D because Shar's cmov chain has no spine entries
# to stream behind") does NOT reproduce on M4 Max -- wide-OoO Apple silicon
# with 3 load AGUs absorbs the cold outer-key misses that narrow-OoO SKX
# (2 AGUs) could not. Ship: F on every mode.
#
# G (Shar inner on n=4096, no spine) is catastrophic as on SKX: 12 dependent
# loads on 8 KB with jumping addresses give the streamer nothing. F vs G:
# hot_bat -78.9%, hot_ser -80.3%, cold_bat -34.8%, cold_ser -65.6%. Shar is
# right for K=512 outer keys (1 KB, streamer-hostile) but wrong for the
# inner n=4096 search (8 KB, streams cleanly via contiguous spine entries).
#
# F vs Lem (how much our stack improves on the published Lemire baseline):
#   hot_bat  -80.6%   hot_ser  -79.8%   cold_bat -36.6%   cold_ser -48.4%
# NOTE (2026-10-11): the dict below holds the 2026-05-18 re-bench levels
# (A-I + Lem). The delta tables in the comment above are ratios of
# per-cell medians; because each variant's median can come from a
# different run they are not reliable comparisons -- paired per-run
# comparisons live in m4_runs/twolevel_paired.txt. H/I were measured
# with the mis-aimed Eytzinger prefetch (fixed in bench_twolevel.cpp
# 2026-10-11, not yet re-benchmarked).
# No archived run supports the 2026-05-13 delta tables in the comments above: commit 5fdbb0a
# overwrote those files in place (Text/corrections_2026-10.md section 2.3).
m4_twolevel = {
    # (hot_bat, hot_ser, cold_bat, cold_ser). 5-run medians 2026-05-18 under the
    # 4-mode harness, 10-variant binary (A-I + Lem; H/I = Eytzinger outer +
    # K&M PF (pre-fix), Khuong & Morin 2017 Listing 6). Raw in m4_runs/twolevel_run{1..5}.txt.
    # Uses the M4 Max build (default ARM gap=64 path, simd_quad_m4_spine /
    # simd_quad_m4_spine_4096 as inner).
    #
    # Deltas vs F (the project's primary recommendation for hot):
    #   I vs F:   +0.5%  +13.5%   +3.5% +103.9%   (no win; F strict-best every mode)
    #   [RETRACTED 2026-10-11: ratios of medians. Paired I vs F on M4 (m4_runs/twolevel_paired.txt):
    #    hot_bat -0.4% tie, hot_ser +16.0% (I faster 0/5), cold_bat +13.3% (1/5), cold_ser +26.4%
    #    (I slower 5/5; per-run +26.3 +119.4 +77.1 +22.9 +26.4). F ties E in cold_bat and loses
    #    cold_ser to B, D and E; 'F strict-best every mode' and the 'settled slow-inner pattern'
    #    below are retracted (Text/corrections_2026-10.md section 2.3).]
    #   H vs F:  +28.2%  +47.8%  +32.2%  +58.9%   (H underperforms I as elsewhere)
    #
    # Falsifies the pre-registered "I hot_bat-win mirroring GV4 (3 AGUs at full
    # clock)" expectation. Confirms the refined slow-inner-is-the-real-predictor
    # model: M4's gap=64 + vld1q_u16_x4 inner is fast enough that even the
    # dep-chained hot_ser leaves no critical-path stall for software prefetch
    # to hide -- same EMR-shape outcome despite different uarch class. Settled
    # pattern (6 hosts): I hot_ser win requires *both* slow-inner AND adequate
    # OoO/load-pipe width; M4 Max fails the slow-inner gate.
    "A  bsearch outer + general-n inner":          ( 81.63,  30.25, 228.33, 419.38),
    "B  two-level spine outer + general-n inner":  ( 31.26,  40.40, 186.25, 217.71),
    "C  bsearch outer + n=4096 inner":             ( 19.12,  24.47, 160.00, 329.38),
    "D  two-level spine outer + n=4096 inner":     ( 21.57,  38.55, 166.66, 238.54),
    "E  Shar branchless outer + general-n inner":  ( 15.12,  18.36, 158.96, 235.62),
    "F  Shar branchless outer + n=4096 inner":     ( 13.25,  16.33, 161.88, 281.67),
    "G  Shar outer + Shar inner (no spine)":       ( 73.81,  87.82, 231.66, 644.38),
    "H  Eytzinger outer + K&M PF (pre-fix) + general-n inner":   ( 16.99,  24.13, 213.96, 447.50),
    "I  Eytzinger outer + K&M PF (pre-fix) + n=4096 inner":      ( 13.32,  18.53, 167.50, 574.38),
    "Lem  Lemire reference (bsearch + simd_quad)": ( 85.17,  86.28, 263.33, 546.04),
}
# Raspberry Pi 5 (Cortex-A76) two-level spine micro-bench, median of 5 runs
# 2026-05-18 under the 4-mode harness (hot_bat/hot_ser/cold_bat/cold_ser),
# 10-variant binary (A-I + Lem; H/I = Eytzinger outer + K&M PF (pre-fix), Khuong &
# Morin 2017 Listing 6). Raw in pi5_runs/twolevel_run{1..5}.txt.
# Uses the Pi 5 build of bench_twolevel.cpp (`-DQUADSEARCH_ARM_PI5`, gap=32
# outer+inner, simd_quad_pi5_spine / simd_quad_pi5_spine_4096 as inner).
# Per-run variance on this Pi 5 sweep is wide (F hot_ser ranges 216-482 ns
# across 5 runs, ~2.2x spread; cold spreads similar; the run-level
# geometric mean drifts 1.5-1.6x between runs, mostly governor hops).
# The per-cell medians in the dict are LEVELS only: each variant's median
# can come from a different run, so differencing medians across variants
# can invert the ordering that every individual run shows. Variant
# comparisons must come from the paired per-run analysis in
# pi5_runs/twolevel_paired.txt (compute_twolevel_paired.py), which pairs
# X and Y within each run and reports the median paired delta plus a
# sign count (WIN = faster in >= 80% of runs AND |median| >= 3%).
#
# I vs F, paired per run (hot_bat / hot_ser / cold_bat / cold_ser):
#   I vs F:  +2.6% TIE (I faster 2/5) | +5.8% WIN for F (I faster 1/5;
#            per-run +5.8 +12.0 -49.2 +1.2 +6.6) | +34.6% WIN for F (0/5)
#            | +30.0% WIN for F (0/5)
#   H vs E:  +1.7% TIE | +3.3% WIN for E (0/5) | +31.3% WIN for E (0/5)
#            | +23.0% WIN for E (1/5)
# The earlier "-22.5% hot_ser win for I" was a ratio of medians picked
# from different runs; I is slower than F on hot_ser in 4 of 5 runs, and
# the one run where I is faster (run 3) is the run where F itself spiked
# (F vs D +107% in that run, vs -5..-10% in the other four). H/I were
# also measured with the mis-aimed Eytzinger prefetch (bench_twolevel.cpp
# prefetched node i+1's line instead of node i's descendants; fixed
# 2026-10-11, not yet re-benchmarked), so these H/I levels are the
# pre-fix kernels.
#
# Deltas vs A (hot_bat / hot_ser / cold_bat / cold_ser):
#   B vs A:   -2.7%   -7.1%  -13.0%  +21.6%
#   C vs A:   -1.9%   -0.5%  -17.2%  -10.9%
#   D vs A:   +0.8%   -5.4%  -25.3%   +8.4%
#   E vs A:   +7.7%  -13.6%  +17.0%  +23.4%
#   F vs A:   +2.6%  +15.6%   -3.6%   -6.4%
#   G vs A:  +81.7%  +92.6%   +5.4%  +21.9%
#   H vs A:   +9.5%  -11.1%  +42.7%  +59.5%
#   I vs A:   +1.9%  -10.4%  +14.7%  +22.0%
#   Lem vs A:+58.4%  +54.3%  +25.7%  +12.6%
#
# **Pi 5 does NOT confirm the M1-Pro-style I `hot_ser` win.** Pre-registered
# (per `KhuongMorin.md` §"Hosts pending"): "Pi 5 is the *one* remaining host
# where the narrow-OoO + slow-inner story still has a plausible critical-
# path stall (slowest NEON inner across the bench + 2-AGU OoO + only host
# where inner is critical-path under batched dispatch -- possible hot_bat
# *and* hot_ser win, or full SKX-like falsification)." Paired result
# (pi5_runs/twolevel_paired.txt): hot_ser I vs F +5.8% median, I faster in
# only 1/5 runs -> WIN for F; hot_bat I vs F +2.6%, I faster 2/5 -> TIE.
# The best hot_ser variant by mean rank is E (Shar outer + general-n
# inner), which beats I 5/5 (+6.4%) and ties F (F vs E +1.1%, E faster
# 4/5 but below the 3% threshold). Cold modes: I loses to F in 5/5 runs
# in both (cold_bat +34.6%, cold_ser +30.0%), consistent with prefetch /
# demand-load bandwidth contention (paper §4 `WL > log B` regime). The
# interpretation is provisional until H/I are re-benchmarked with the
# fixed prefetch.
#
# **Cold matrix (paired, pi5_runs/twolevel_paired.txt).** cold_bat: D is
# the fastest variant in 5/5 runs; F vs D +31.8% (WIN for D), F vs C
# +4.9% (WIN for C, F faster 1/5). cold_ser: F is best by mean rank, but
# D vs F +0.4% and C vs F +1.0% are both TIEs (F faster 3/5), while F
# beats A/B/E/G/H/I/Lem 5/5. So the cold picture is "D clearly best
# cold_bat; C/D/F indistinguishable cold_ser" -- a partial erosion of the
# full F-cold-reversal noted in the earlier CLAUDE.md ship recommendation,
# within governor-hop noise.
#
# G (Shar inner for n=4096) catastrophic as elsewhere (+82% / +93% hot vs A).
#
# F vs Lem (how much our stack improves on the published Lemire baseline):
#   hot_bat  -35.2%   hot_ser  -25.1%   cold_bat -23.3%   cold_ser -16.8%
#
# Ship (paired analysis): F for hot_bat (best by mean rank; beats D 4/5)
# and hot_ser (ties E, beats I 4/5); D for cold_bat (fastest 5/5, F +31.8%
# vs D); cold_ser is a C/D/F tie. I does not beat F on any mode on Pi 5
# under the paired analysis, so the earlier "I for hot_ser" recommendation
# is withdrawn (pending a re-bench with the fixed prefetch).
# Aggregator (levels): pi5_runs/compute_twolevel.py -> pi5_runs/twolevel_summary.txt.
# Paired comparisons: compute_twolevel_paired.py pi5 -> pi5_runs/twolevel_paired.txt.
# NOTE 2026-10-11 (repaired harness, 10 runs, pi5_runs/twolevel_paired_v2.txt): the re-bench is
# done. D is the Pi 5 ship (fastest in 7/10 hot_bat, 8/10 hot_ser, 7/10 cold_bat); F ties D hot
# (+2.7% / +2.0%) and loses cold_bat (+44.7%, F faster 0/10); I vs F +7.3% / +8.6% hot (F faster
# 8/10). The 'Deltas vs A' and 'F vs Lem' lines in this block are ratios of per-cell medians
# (paired F vs Lem: -35.2 / -39.3 / -28.4 / -16.7; paired F vs A hot_ser -11.4%).
# [RETRACTED 2026-10-11: the runahead / WL > log B mechanism explained numbers produced by the
#  mis-aimed prefetch; see KhuongMorin.md banner and Text/corrections_2026-10.md section 1.]
pi5_twolevel = {
    # (hot_bat, hot_ser, cold_bat, cold_ser). 5-run per-cell medians
    # 2026-05-18, 10-variant binary (adds H/I = Eytzinger outer + K&M PF (pre-fix),
    # Khuong & Morin 2017 Listing 6; H/I measured with the pre-fix,
    # mis-aimed prefetch). Levels only -- see pi5_runs/twolevel_paired.txt
    # for variant comparisons (I does not beat F on hot_ser there: +5.8%,
    # I faster in 1/5 runs).
    "A  bsearch outer + general-n inner":          (238.20, 284.13,1650.36,1652.31),
    "B  two-level spine outer + general-n inner":  (231.84, 264.09,1436.01,2009.15),
    "C  bsearch outer + n=4096 inner":             (233.78, 282.78,1367.12,1471.38),
    "D  two-level spine outer + n=4096 inner":     (240.10, 268.82,1233.04,1790.45),
    "E  Shar branchless outer + general-n inner":  (256.48, 245.58,1931.18,2038.13),
    "F  Shar branchless outer + n=4096 inner":     (244.40, 328.50,1591.57,1547.03),
    "G  Shar outer + Shar inner (no spine)":       (432.88, 547.26,1739.06,2015.27),
    "H  Eytzinger outer + K&M PF (pre-fix) + general-n inner":   (260.82, 252.48,2354.24,2635.44),
    "I  Eytzinger outer + K&M PF (pre-fix) + n=4096 inner":      (242.76, 254.65,1892.39,2015.35),
    "Lem  Lemire reference (bsearch + simd_quad)": (377.30, 438.38,2075.36,1859.70),
}

# AWS Graviton 4 (Arm Neoverse V2) two-level spine micro-bench, median of 5 runs
# 2026-05-13 under the 4-mode harness (hot_bat/hot_ser/cold_bat/cold_ser) post
# bench_cold targets[si][1] fix. Raw in gv4_runs/twolevel_run{1..5}.txt. Uses
# the GV4 build of bench_twolevel.cpp (`-DQUADSEARCH_ARM_GV4`, gap=32
# outer+inner, simd_quad_graviton_spine / simd_quad_graviton_spine_4096 as
# inner).
#
# Deltas vs A (hot_bat / hot_ser / cold_bat / cold_ser):
#   B vs A:   -6.5%   -4.4%   -9.2%  +16.6%
#   C vs A:  -42.3%   -7.9%  -35.7%   -5.4%
#   D vs A:  -30.0%  -11.6%  -19.7%  +14.2%
#   E vs A:  -50.6%  -42.9%  -17.8%  +13.2%
#   F vs A:  -59.6%  -52.1%  -30.8%  +13.1%
#   G vs A:   -3.0%  +16.6%   -8.0%  +38.4%
#   Lem vs A: +16.3%  +79.1%   -4.4%  +20.6%
#
# Deltas vs D (outer spine + n=4096 inner):
#   F vs D:  -42.3%  -45.8%  -13.8%   -0.9%  (F best every mode, NO cold reversal)
#
# Deltas vs F:
#   G vs F: +140.1% +143.5%  +33.0%  +22.4%
#
# Deltas vs Lemire reference:
#   A vs Lem: -14.0% -44.1%  +4.6% -17.1%
#   D vs Lem: -39.8% -50.6% -16.1%  -5.3%
#   F vs Lem: -65.3% -73.3% -27.7%  -6.2%
#
# F (Shar outer + compile-time n=4096 inner) wins every mode on GV4,
# including both cold modes. [SUPERSEDED 2026-10-11: paired analysis
# (gv4_runs/twolevel_paired.txt) gives C both cold modes 5/5 and I hot_bat 5/5;
# see the NOTE below.] Confirms the pre-registered prediction: GV4
# is the widest-OoO host in the project (Neoverse V2 has 3 load pipes, like
# M4 / M1 and EMR -- earlier text here said 4 -- vs 2 on Pi 5 / SKX; the old
# comparison read: 4 load AGUs Neoverse V2 vs 3 on
# M4 / M1, 2 on Pi 5 / SKX, 3 on EMR), so the 9-deep Shar cmov chain's
# dep-chain latency gets hidden even on cold_ser where every other host
# either reverses (SKX, Pi 5 full; EMR, M1 Pro partial) or ties (M4 Max).
# Matches the four-way split hypothesis: OoO width x clock x inner-path
# latency. GV4 has all three maxed (widest OoO, full clock, fast NEON
# paired-x2 inner), lands with M4 Max in the "no reversal" bucket.
#
# G (Shar inner for n=4096) catastrophic as everywhere: +140% hot_bat /
# +144% hot_ser vs F. Closes the "is Shar inner worth porting" question
# on the last host -- 12 dependent loads on 8 KB working set with jumping
# addresses denies the streamer on every uarch, confirmed.
#
# [SUPERSEDED 2026-10-11: C wins both cold modes 5/5, I hot_bat 5/5 (pre-fix)] Ship: F unconditionally on GV4. No cold-serial alt needed.
# Aggregator: gv4_runs/compute_twolevel.py; summary: gv4_runs/twolevel_summary.txt.
# NOTE (2026-10-11): the dict below holds the 2026-05-18 re-bench levels
# (A-I + Lem). The delta tables in the comment above are ratios of
# per-cell medians; because each variant's median can come from a
# different run they are not reliable comparisons -- paired per-run
# comparisons live in gv4_runs/twolevel_paired.txt. H/I were measured
# with the mis-aimed Eytzinger prefetch (fixed in bench_twolevel.cpp
# 2026-10-11, not yet re-benchmarked).
# No archived run supports the 2026-05-13 delta tables in the comments above: commit 5fdbb0a
# overwrote those files in place (Text/corrections_2026-10.md section 2.3).
gv4_twolevel = {
    # (hot_bat, hot_ser, cold_bat, cold_ser). 5-run medians 2026-05-18,
    # 10-variant binary (A-I + Lem). H/I = Eytzinger outer + K&M PF (pre-fix).
    "A  bsearch outer + general-n inner":          (161.29, 102.72, 382.74, 418.51),
    "B  two-level spine outer + general-n inner":  (148.54,  94.73, 345.80, 498.63),
    "C  bsearch outer + n=4096 inner":             ( 91.94,  95.44, 255.04, 406.23),
    "D  two-level spine outer + n=4096 inner":     (111.16,  89.72, 316.83, 484.37),
    "E  Shar branchless outer + general-n inner":  ( 80.11,  58.16, 325.26, 498.94),
    "F  Shar branchless outer + n=4096 inner":     ( 65.37,  50.34, 268.45, 486.13),
    "G  Shar outer + Shar inner (no spine)":       (149.60, 130.06, 359.41, 597.22),
    "H  Eytzinger outer + K&M PF (pre-fix) + general-n inner":   ( 64.71,  63.18, 370.72, 635.46),
    "I  Eytzinger outer + K&M PF (pre-fix) + n=4096 inner":      ( 57.49,  58.38, 311.10, 619.95),
    "Lem  Lemire reference (bsearch + simd_quad)": (181.62, 196.19, 366.88, 519.73),
}

# Apple M1 Pro two-level spine micro-bench, median of 5 runs 2026-05-13
# under the 4-mode harness (hot_bat/hot_ser/cold_bat/cold_ser) post
# bench_cold targets[si][1] fix. Raw in m1_runs/twolevel_run{1..5}.txt.
# Uses the default ARM build of bench_twolevel.cpp (gap=64, links
# simd_quad_m4.c -- same binary layout as the M4 Max run).
#
# Deltas vs A (hot_bat / hot_ser / cold_bat / cold_ser):
#   B vs A:  -66.1%  +36.4%  -65.4%   -0.2%
#   C vs A:  -79.9%  -20.6%  -71.6%   +4.2%
#   D vs A:  -77.4%  +38.2%  -65.7%   -3.7%
#   E vs A:  -87.8%  -19.9%  -71.5%   +9.6%
#   F vs A:  -82.6%  -22.5%  -70.6%   +5.5%
#   G vs A:  -56.9%  +89.5%  -59.3%  +54.5%
#
# Deltas vs D (outer spine + n=4096 inner):
#   F vs D:  -23.1%  -43.9%  -14.4%   +9.5%  (F best hot, partial cold reversal)
#
# Paired per-run F vs D (m1_runs/twolevel_paired.txt, 2026-05-18 runs):
# hot_bat -32.4% (F faster 5/5), hot_ser -38.9% (5/5), cold_bat -10.6%
# (5/5), cold_ser +5.7% (F faster 2/5 -> TIE). So F wins both hot modes
# and cold_bat outright; cold_ser is a tie with D rather than a clean
# reversal. cold_ser is the one mode where F is not best: A is best by
# mean rank there, E beats F 4/5 (F vs E +8.5%, WIN for E) and A beats F
# 4/5 (F vs A +26.3%, WIN for A). M1 Pro is a 3-AGU wide-OoO Apple core
# like M4 but runs ~1.4x slower absolute (clock ~0.72x M4 Max), so dep-chain stalls have more
# wall-clock room to matter -- plausibly why the Shar outer gives back
# its advantage on cold_ser even with wide OoO.
#
# G (Shar inner for n=4096) catastrophic as elsewhere.
#
# F vs Lem: hot_bat -56.5%, hot_ser -66.5%, cold_bat -36.4%, cold_ser -23.7%.
# Between M4 (steeper Lem deltas) and SKX (shallower) as expected.
#
# Ship (paired analysis, m1_runs/twolevel_paired.txt): F for hot_bat and
# cold_bat (best by mean rank in both; I vs F hot_bat -0.3%, I faster 3/5
# -> TIE; I vs F cold_bat +17.9%, F faster 5/5). **I (Eytzinger outer +
# K&M PF (pre-fix) + n=4096 inner) for hot_ser**: I vs F -10.9% median paired
# delta, I faster in 4/5 runs (per-run -5.2 -10.9 -15.5 -19.8 +22.3) ->
# WIN for I. The "-19.8%" quoted earlier was a ratio of medians (it happens
# to equal the single best run), not the paired median. cold_ser: F is
# NOT best (A by mean rank; E beats F 4/5); I vs F +16.3%, F faster 5/5.
# Mechanism per Khuong & Morin 2017 §4: explicit prefetch delivers
# runahead-via-software during the dep-chained outer descent (the K=512 /
# 1 KB outer is too short for hardware streamers to help), but the same
# prefetches contend with demand block-loads when cold-mode bandwidth
# saturates. Caveat: H/I were measured with the mis-aimed Eytzinger
# prefetch (bench_twolevel.cpp fixed 2026-10-11, not yet re-benchmarked).
# See KhuongMorin.md for the full writeup. Prior legacy 2-mode "A->F cold
# -77%" was pre-fix; superseded. Aggregator (levels):
# m1_runs/compute_twolevel.py; paired: compute_twolevel_paired.py m1.
# [RETRACTED 2026-10-11: the runahead mechanism explained numbers produced by the mis-aimed
#  prefetch; the M1 I hot_ser edge (-10.9%, 4/5) is pre-fix and pending re-measurement.]
m1_twolevel = {
    # (hot_bat, hot_ser, cold_bat, cold_ser). 5-run per-cell medians
    # 2026-05-18, 10-variant binary (adds H/I = Eytzinger outer + K&M PF (pre-fix),
    # Khuong & Morin 2017 Listing 6; H/I measured with the pre-fix,
    # mis-aimed prefetch). Levels only -- variant comparisons come from
    # m1_runs/twolevel_paired.txt: I beats F on hot_ser (-10.9% paired
    # median, I faster 4/5); hot_bat I vs F is a tie; F is best on cold_bat
    # but NOT on cold_ser (A best by mean rank, E beats F 4/5, F vs D tie).
    # Prior 2026-05-13 8-variant baseline overwritten in
    # m1_runs/twolevel_run{1..5}.txt.
    "A  bsearch outer + general-n inner":          (394.99,  98.62, 819.38, 613.54),
    "B  two-level spine outer + general-n inner":  (112.64, 147.04, 338.54, 677.09),
    "C  bsearch outer + n=4096 inner":             ( 54.85,  75.52, 263.54, 644.38),
    "D  two-level spine outer + n=4096 inner":     ( 75.55, 116.76, 306.25, 706.25),
    "E  Shar branchless outer + general-n inner":  ( 55.53,  76.05, 268.75, 630.21),
    "F  Shar branchless outer + n=4096 inner":     ( 45.88,  79.26, 278.54, 776.46),
    "G  Shar outer + Shar inner (no spine)":       (158.26, 158.17, 356.88, 888.75),
    "H  Eytzinger outer + K&M PF (pre-fix) + general-n inner":   ( 68.93,  74.33, 385.62, 826.66),
    "I  Eytzinger outer + K&M PF (pre-fix) + n=4096 inner":      ( 47.71,  63.57, 328.33, 869.79),
    "Lem  Lemire reference (bsearch + simd_quad)": (141.82, 200.30, 365.62, 876.66),
}

# --- per-machine line plots (warm + cold) ---
# Each machine gets its own pair of warm/cold plots with every algorithm that
# applies. Pi 5 plots do not include the m4 variants; M4 plots include both
# pi5 and m4 variants so you can see the M4-specific retune effect.

styles = {
    "linear (std::find)":         dict(marker="o", linestyle="--", color="#888888"),
    "binary (std::binary_search)":dict(marker="s", linestyle="-.", color="#1f77b4"),
    "simd_quad (reference)":      dict(marker="^", linestyle=":",  color="#2ca02c"),
    "simd_quad_pi5":              dict(marker="D", linestyle="-",  color="#d62728", linewidth=1.6),
    "simd_quad_pi5 + spine":      dict(marker="*", linestyle="-",  color="#9467bd", linewidth=2.0, markersize=10),
    "simd_quad_m4":               dict(marker="P", linestyle="-",  color="#ff7f0e", linewidth=1.6),
    "simd_quad_m4 + spine":       dict(marker="X", linestyle="-",  color="#8c564b", linewidth=2.2, markersize=9),
    "simd_quad_intel":            dict(marker="v", linestyle="-",  color="#17becf", linewidth=1.6),
    "simd_quad_intel + spine":    dict(marker="h", linestyle="-",  color="#e377c2", linewidth=2.2, markersize=9),
    "simd_quad_graviton":         dict(marker="<", linestyle="-",  color="#bcbd22", linewidth=1.6),
    "simd_quad_graviton + spine": dict(marker=">", linestyle="-",  color="#7f7f7f", linewidth=2.2, markersize=9),
}

def lineplot(xs, data, title, out):
    """xs is the host's own size list (22 points for Pi 5, 10 for the rest);
    every value list in `data` is exactly len(xs) long, so lines connect
    across all archived points with no gaps."""
    fig, ax = plt.subplots(figsize=(8, 5))
    for name, ys in data.items():
        ax.plot(xs, ys, label=name, **styles[name])
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xticks(label_sizes)
    ax.set_xticklabels(label_strs)
    ax.set_xlabel("array size (u16 elements)")
    ax.set_ylabel("nanoseconds per query")
    ax.set_title(title)
    ax.grid(True, which="both", linestyle=":", alpha=0.4)
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    print(f"wrote {out}")

lineplot(pi5_sizes, pi5_warm, "Raspberry Pi 5 (Cortex-A76) - warm cache", "bench_warm.png")
lineplot(pi5_sizes, pi5_cold, "Raspberry Pi 5 (Cortex-A76) - cold cache", "bench_cold.png")
lineplot(m4_sizes, m4_warm,  "Apple M4 Max (P-core) - warm cache",       "bench_m4_warm.png")
lineplot(m4_sizes, m4_cold,  "Apple M4 Max (P-core) - cold cache",       "bench_m4_cold.png")
if have_m1:
    lineplot(m1_sizes, m1_warm, "Apple M1 Pro (P-core) - warm cache", "bench_m1_warm.png")
    lineplot(m1_sizes, m1_cold, "Apple M1 Pro (P-core) - cold cache", "bench_m1_cold.png")
if have_skx:
    lineplot(skx_sizes, skx_warm, "Intel Skylake-SP (Xeon 8175M) - warm cache", "bench_skx_warm.png")
    lineplot(skx_sizes, skx_cold, "Intel Skylake-SP (Xeon 8175M) - cold cache", "bench_skx_cold.png")
if have_emr:
    lineplot(emr_sizes, emr_warm, "Intel Emerald Rapids - warm cache", "bench_emr_warm.png")
    lineplot(emr_sizes, emr_cold, "Intel Emerald Rapids - cold cache", "bench_emr_cold.png")
if have_gv4:
    lineplot(gv4_sizes, gv4_warm, "AWS Graviton 4 (Arm Neoverse V2) - warm cache", "bench_gv4_warm.png")
    lineplot(gv4_sizes, gv4_cold, "AWS Graviton 4 (Arm Neoverse V2) - cold cache", "bench_gv4_cold.png")


# --- Cross-machine comparison: a faceted view (one subplot per host, all
#     algorithms for that host visible) plus a focused "best-tuned-per-host"
#     comparison (one line per host, 4 hosts).
#
# The previous implementation put all 4 hosts and 8 algorithms on one plot
# (~32 lines). It was unreadable. Facets are cleaner, and the tuned-only
# plot is the one you actually want when comparing hosts directly.

# Each host defines (label, sizes, warm-dict, cold-dict, color for the tuned plot).
hosts = [("Pi 5 (A76)",    pi5_sizes, pi5_warm, pi5_cold, "#1f77b4"),
         ("M4 Max",         m4_sizes,  m4_warm,  m4_cold, "#d62728")]
if have_m1:
    hosts.append(("M1 Pro",         m1_sizes,  m1_warm,   m1_cold,   "#9467bd"))
if have_skx:
    hosts.append(("Intel Skylake",  skx_sizes, skx_warm,  skx_cold, "#17becf"))
if have_emr:
    hosts.append(("Intel Emerald",  emr_sizes, emr_warm,  emr_cold, "#ff7f0e"))
if have_gv4:
    hosts.append(("Graviton 4",     gv4_sizes, gv4_warm,  gv4_cold, "#2ca02c"))

# Which algorithms get plotted in the per-host facet. Only the ones that
# apply to each host - per-arch variants are skipped if the host has no
# data for them.
facet_algos = [
    "linear (std::find)",
    "binary (std::binary_search)",
    "simd_quad (reference)",
    "simd_quad_pi5",
    "simd_quad_pi5 + spine",
    "simd_quad_m4",
    "simd_quad_m4 + spine",
    "simd_quad_intel",
    "simd_quad_intel + spine",
    "simd_quad_graviton",
    "simd_quad_graviton + spine",
]

def faceted_compare(regime, out):
    n_hosts = len(hosts)
    # 2x3 if 5-6 hosts, 2x2 if 4, 1x3 if 3, 1x2 if 2.
    if n_hosts >= 5:
        rows, cols = 2, 3
    elif n_hosts == 4:
        rows, cols = 2, 2
    elif n_hosts == 3:
        rows, cols = 1, 3
    else:
        rows, cols = 1, n_hosts
    fig, axes = plt.subplots(rows, cols, figsize=(6*cols, 4.5*rows),
                             sharex=True, sharey=True)
    axes_flat = np.array(axes).reshape(-1)
    for ax, (label, xs, warm, cold, _color) in zip(axes_flat, hosts):
        src = warm if regime == "warm" else cold
        for a in facet_algos:
            if a in src and all(v is not None for v in src[a]):
                ax.plot(xs, src[a], label=a, **styles[a])
        ax.set_xscale("log", base=2)
        ax.set_yscale("log")
        ax.set_xticks(label_sizes)
        ax.set_xticklabels(label_strs, fontsize=8)
        ax.set_title(label, fontsize=11)
        ax.grid(True, which="both", linestyle=":", alpha=0.4)
    # Hide any extra axes (e.g. if n_hosts = 3 in a 2x2 grid, but we
    # avoided that above).
    for ax in axes_flat[n_hosts:]:
        ax.axis("off")
    # One shared legend.
    handles, labels = axes_flat[0].get_legend_handles_labels()
    # Merge handles/labels across all subplots (pi5/m4 variants may only
    # appear in some). Use a dict to dedupe while preserving order.
    seen = {}
    for ax in axes_flat[:n_hosts]:
        for h, l in zip(*ax.get_legend_handles_labels()):
            if l not in seen:
                seen[l] = h
    fig.legend(seen.values(), seen.keys(), loc="lower center",
               ncol=min(5, len(seen)), fontsize=9,
               bbox_to_anchor=(0.5, -0.02))
    for ax in axes_flat[:n_hosts]:
        ax.set_xlabel("array size (u16 elements)")
        ax.set_ylabel("nanoseconds per query")
    fig.suptitle(f"Cross-machine comparison - {regime} cache", fontsize=13)
    fig.tight_layout(rect=[0, 0.04, 1, 0.97])
    fig.savefig(out, dpi=130, bbox_inches="tight")
    print(f"wrote {out}")

faceted_compare("warm", "bench_compare_warm.png")
faceted_compare("cold", "bench_compare_cold.png")

# Best-tuned-per-host comparison. One line per host, showing that host's
# own tuned+spine variant. Four lines total: the cleanest apples-to-apples
# view of "what does the best version of this algorithm do on this host."

host_tuned_name = {
    "Pi 5 (A76)":    "simd_quad_pi5 + spine",
    "M4 Max":        "simd_quad_m4 + spine",
    "M1 Pro":        "simd_quad_m4 + spine",
    "Intel Skylake": "simd_quad_intel + spine",
    "Intel Emerald": "simd_quad_intel + spine",
    "Graviton 4":    "simd_quad_graviton + spine",
}

def tuned_compare(regime, out):
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for label, xs, warm, cold, color in hosts:
        src = warm if regime == "warm" else cold
        a = host_tuned_name[label]
        if a in src and all(v is not None for v in src[a]):
            ax.plot(xs, src[a], label=f"{label}  ({a})",
                    color=color, linewidth=2.0, marker="o", markersize=6)
    # Also include std::binary_search on each host, thin/dashed, as a
    # reference point so readers can see what "the baseline" costs per host.
    for label, xs, warm, cold, color in hosts:
        src = warm if regime == "warm" else cold
        if "binary (std::binary_search)" in src and \
           all(v is not None for v in src["binary (std::binary_search)"]):
            ax.plot(xs, src["binary (std::binary_search)"],
                    label=f"{label}  (std::binary_search)",
                    color=color, linewidth=1.0, linestyle="--",
                    marker="s", markersize=4, alpha=0.6)
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xticks(label_sizes)
    ax.set_xticklabels(label_strs)
    ax.set_xlabel("array size (u16 elements)")
    ax.set_ylabel("nanoseconds per query")
    ax.set_title(f"Best tuned variant per host - {regime} cache")
    ax.grid(True, which="both", linestyle=":", alpha=0.4)
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    print(f"wrote {out}")

tuned_compare("warm", "bench_tuned_warm.png")
tuned_compare("cold", "bench_tuned_cold.png")


# --- summary bar chart at n=4096: all machines, both regimes ---
# Columns: binary, simd reference, then each host's best SIMD (variant + spine).
# We show each host's *tuned* algorithm (the spine variant of that host's own
# implementation) to compare apples-to-apples on what the tuned code actually
# achieves.

def pick(d, key):
    return d.get(key, [None]*10)[-1]

bar_cols = [
    ("binary",           "binary (std::binary_search)"),
    ("simd_quad\n(ref)", "simd_quad (reference)"),
    ("tuned (plain)",    None),    # filled per host: pi5 / m4 / intel
    ("tuned + spine",    None),    # ditto
]

host_tuned = {
    "Pi 5 (A76)":     ("simd_quad_pi5",      "simd_quad_pi5 + spine"),
    "M4 Max":         ("simd_quad_m4",       "simd_quad_m4 + spine"),
    "M1 Pro":         ("simd_quad_m4",       "simd_quad_m4 + spine"),
    "Intel Skylake":  ("simd_quad_intel",    "simd_quad_intel + spine"),
    "Intel Emerald":  ("simd_quad_intel",    "simd_quad_intel + spine"),
    "Graviton 4":     ("simd_quad_graviton", "simd_quad_graviton + spine"),
}
# host -> (sizes, warm-dict, cold-dict)
host_src = {
    "Pi 5 (A76)":    (pi5_sizes, pi5_warm, pi5_cold),
    "M4 Max":        (m4_sizes,  m4_warm,  m4_cold),
}
if have_m1:
    host_src["M1 Pro"]        = (m1_sizes,  m1_warm,  m1_cold)
if have_skx:
    host_src["Intel Skylake"] = (skx_sizes, skx_warm, skx_cold)
if have_emr:
    host_src["Intel Emerald"] = (emr_sizes, emr_warm, emr_cold)
if have_gv4:
    host_src["Graviton 4"]    = (gv4_sizes, gv4_warm, gv4_cold)

summary_hosts = list(host_src.keys())
host_colors   = {"Pi 5 (A76)":    "#1f77b4",
                 "M4 Max":        "#d62728",
                 "M1 Pro":        "#9467bd",
                 "Intel Skylake": "#17becf",
                 "Intel Emerald": "#ff7f0e",
                 "Graviton 4":    "#2ca02c"}

fig, (ax_w, ax_c) = plt.subplots(1, 2, figsize=(16, 6))
x = np.arange(len(bar_cols))
w = 0.8 / max(1, len(summary_hosts))

def vals_for(host, regime):
    _xs, warm, cold = host_src[host]
    src = warm if regime == "warm" else cold
    plain_name, spine_name = host_tuned[host]
    return [pick(src, "binary (std::binary_search)"),
            pick(src, "simd_quad (reference)"),
            pick(src, plain_name),
            pick(src, spine_name)]

def bar_group(ax, regime, title):
    for i, host in enumerate(summary_hosts):
        offset = (i - (len(summary_hosts) - 1) / 2) * w
        v = vals_for(host, regime)
        vplot = [x_ if x_ is not None else 0 for x_ in v]
        bars = ax.bar(x + offset, vplot, w, label=host, color=host_colors[host])
        for rect, val in zip(bars, v):
            if val is not None:
                ax.text(rect.get_x() + rect.get_width()/2, val,
                        f"{val:.0f}", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels([c[0] for c in bar_cols], fontsize=9)
    ax.set_ylabel("nanoseconds per query")
    ax.set_title(title)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax.legend(loc="upper left", fontsize=8)

bar_group(ax_w, "warm", "n=4096, warm cache")
bar_group(ax_c, "cold", "n=4096, cold cache")
fig.suptitle("Cross-machine summary at n=4096 "
             "(tuned = each host's own simd_quad_* variant)", fontsize=13)
fig.tight_layout()
fig.savefig("bench_summary.png", dpi=130)
print("wrote bench_summary.png")


# --- speedup plot: every host vs. Pi 5 baseline, per algorithm, both regimes ---
# How much faster than a Pi 5 is each other host, running the same algorithm?
# Pi 5 is the baseline because it's the slowest host in the set - values >1
# mean the other host is faster. One line per (algorithm, other-host) pair.
# Algorithms are restricted to the two portable ones (binary, simd reference)
# plus each host's own tuned+spine variant - those are what you actually
# ship on each machine, so the cross-machine ratio is meaningful.

other_hosts = []
if any(True for _ in [m4_warm]):
    other_hosts.append(("M4 Max",        m4_sizes,  m4_warm,   m4_cold,   "#d62728"))
if have_m1:
    other_hosts.append(("M1 Pro",        m1_sizes,  m1_warm,   m1_cold,   "#9467bd"))
if have_skx:
    other_hosts.append(("Intel Skylake", skx_sizes, skx_warm,  skx_cold,  "#17becf"))
if have_emr:
    other_hosts.append(("Intel Emerald", emr_sizes, emr_warm,  emr_cold,  "#ff7f0e"))
if have_gv4:
    other_hosts.append(("Graviton 4",    gv4_sizes, gv4_warm,  gv4_cold,  "#2ca02c"))

fig, (ax_w, ax_c) = plt.subplots(1, 2, figsize=(14, 5.5))

def ratio_plot(ax, regime, title):
    # For each non-Pi-5 host, plot Pi5/host ratio for the two portable
    # algos (binary, simd reference) and that host's tuned+spine.
    pi_src = pi5_warm if regime == "warm" else pi5_cold
    # Linestyles: portable algos solid-thin, tuned+spine thick.
    for name, xs, warm, cold, color in other_hosts:
        src = warm if regime == "warm" else cold
        # The Pi 5 sweep covers every size the other host has; index the
        # Pi 5 22-point lists by size so the ratio is taken at the same n.
        pi_idx = [pi5_sizes.index(s) for s in xs]
        # portable: binary
        a = "binary (std::binary_search)"
        r = [pi_src[a][k] / src[a][j] for j, k in enumerate(pi_idx)]
        ax.plot(xs, r, label=f"{name}  binary",
                color=color, linestyle=":", marker="s", markersize=5,
                linewidth=1.2, alpha=0.75)
        # portable: simd reference
        a = "simd_quad (reference)"
        r = [pi_src[a][k] / src[a][j] for j, k in enumerate(pi_idx)]
        ax.plot(xs, r, label=f"{name}  simd_quad ref",
                color=color, linestyle="--", marker="^", markersize=5,
                linewidth=1.2, alpha=0.75)
        # each host's own tuned+spine vs Pi 5 pi5+spine
        host_tuned = host_tuned_name[name]
        pi_tuned   = "simd_quad_pi5 + spine"
        if host_tuned in src and all(v is not None for v in src[host_tuned]):
            r = [pi_src[pi_tuned][k] / src[host_tuned][j]
                 for j, k in enumerate(pi_idx)]
            ax.plot(xs, r, label=f"{name}  tuned+spine",
                    color=color, linestyle="-", marker="o", markersize=7,
                    linewidth=2.2)
    ax.axhline(1.0, color="#444", linestyle=":", linewidth=1)
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xticks(label_sizes)
    ax.set_xticklabels(label_strs)
    ax.set_xlabel("array size (u16 elements)")
    ax.set_ylabel("speedup over Pi 5  (higher = faster than Pi 5)")
    ax.set_title(title)
    ax.grid(True, which="both", linestyle=":", alpha=0.4)
    ax.legend(loc="best", fontsize=7, ncol=2)

ratio_plot(ax_w, "warm", "warm cache: speedup over Pi 5")
ratio_plot(ax_c, "cold", "cold cache: speedup over Pi 5")
fig.suptitle("Per-algorithm speedup over Raspberry Pi 5 baseline", fontsize=13)
fig.tight_layout()
fig.savefig("bench_speedup.png", dpi=130)
print("wrote bench_speedup.png")


# --- n=4096 compile-time specialization A/B chart ---
# Each host's simd_quad_*_spine vs its compile-time-n=4096 unroll (if we
# have one). Currently only EMR has the compile-time specialization; Pi 5,
# M4 Max, and SKX are open items. The chart includes them as missing bars
# so the gap is visible.

host_spine_4096 = {
    "Pi 5 (A76)":    pi5_spine_4096,   # hybrid shipped 2026-05-12 (-28% warm / -7% cold vs general-n)
    "M4 Max":        m4_spine_4096,    # 2026-05-12 hybrid A/B (warm win, cold regression)
    "M1 Pro":        m1_spine_4096,    # 2026-05-12 hybrid A/B (warm wash, cold regression -- same as M4)
    "Intel Skylake": skx_spine_4096,   # 2026-05-12 hybrid A/B (AVX2 block-check path)
    "Intel Emerald": emr_spine_4096,   # 2026-05-12 shipped_run{1..5}
    "Graviton 4":    gv4_spine_4096,   # 2026-05-12 fullsweep_run{1..5}
}

def spine_4096_bar():
    hosts_present = [h for h in summary_hosts if h in host_spine_4096]
    fig, (ax_w, ax_c) = plt.subplots(1, 2, figsize=(12, 5))
    x = np.arange(len(hosts_present))
    w = 0.38
    for ax, regime, title in [(ax_w, "warm", "n=4096, warm cache"),
                              (ax_c, "cold", "n=4096, cold cache")]:
        gen_vals, unr_vals = [], []
        for host in hosts_present:
            _xs, warm, cold = host_src[host]
            src = warm if regime == "warm" else cold
            spine_key = (
                "simd_quad_pi5 + spine"      if host == "Pi 5 (A76)" else
                "simd_quad_m4 + spine"       if host in ("M4 Max", "M1 Pro") else
                "simd_quad_graviton + spine" if host == "Graviton 4" else
                "simd_quad_intel + spine")
            gen_vals.append(src[spine_key][-1])
            sp = host_spine_4096[host]
            unr_vals.append(sp[regime] if sp else None)
        colors = [host_colors[h] for h in hosts_present]
        bars1 = ax.bar(x - w/2, gen_vals, w, color=colors, alpha=0.55,
                       label="general-n spine")
        # "Not yet measured" = 0-height hatched bar, so the gap is visible.
        unr_plot = [v if v is not None else 0 for v in unr_vals]
        bars2 = ax.bar(x + w/2, unr_plot, w, color=colors,
                       edgecolor="black", linewidth=1.0,
                       label="compile-time n=4096 hybrid")
        for i, (b, v) in enumerate(zip(bars2, unr_vals)):
            if v is None:
                ax.text(b.get_x() + b.get_width()/2, 0.3,
                        "(not yet\nmeasured)", ha="center", va="bottom",
                        fontsize=7, color="#666")
            else:
                ax.text(b.get_x() + b.get_width()/2, v,
                        f"{v:.1f}", ha="center", va="bottom", fontsize=8)
        for b, v in zip(bars1, gen_vals):
            ax.text(b.get_x() + b.get_width()/2, v,
                    f"{v:.1f}", ha="center", va="bottom", fontsize=8)
        ax.set_xticks(x)
        ax.set_xticklabels(hosts_present)
        ax.set_ylabel("nanoseconds per query")
        ax.set_title(title)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        ax.legend(loc="upper left", fontsize=9)
    fig.suptitle("Compile-time n=4096 spine unroll vs general-n spine "
                 "(all six hosts measured)",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig("bench_spine_4096.png", dpi=130)
    print("wrote bench_spine_4096.png")

spine_4096_bar()


# --- two-level spine A/B/C/D/E/F/G chart ---
# bench_twolevel data: A = bsearch outer + general-n inner (baseline),
# B = two-level spine outer + general-n inner,
# C = bsearch outer + compile-time-n=4096 inner,
# D = two-level spine outer + compile-time-n=4096 inner,
# E = Shar branchless outer + general-n inner,
# F = Shar branchless outer + compile-time-n=4096 inner,
# G = Shar branchless outer + Shar inner on n=4096 (no spine).
#
# G + Lem were added 2026-05-13 together with the bench_cold targets[si][1]
# fix and the 4-mode harness. All six hosts (SKX, M4 Max, Pi 5, M1 Pro, EMR,
# GV4) are now on the new harness with A-G + Lem (GV4 ported 2026-05-13 this
# session). H/I (Eytzinger outer + Khuong & Morin prefetch, depth log2(B)) were
# added 2026-05-18 on all six hosts; every H/I level in the *_twolevel
# dicts was measured with the mis-aimed prefetch (bench_twolevel.cpp fixed
# 2026-10-11, not yet re-benchmarked), so the chart labels them
# "pre-fix PF". Bars are per-cell medians (levels); variant comparisons
# belong to {host}_runs/twolevel_paired.txt.

# Hosts whose cold data predates the 2026-05-13 bench_cold fix. All six
# hosts are now on the 4-mode harness, so this set is empty; kept for
# backward-compatibility with the rendering code below.
PREFIX_TWOLEVEL_HOSTS = set()

host_twolevel = {
    "Pi 5 (A76)":    pi5_twolevel,
    "M4 Max":        m4_twolevel,
    "M1 Pro":        m1_twolevel,
    "Intel Skylake": skx_twolevel,
    "Intel Emerald": emr_twolevel,
    "Graviton 4":    gv4_twolevel,
}

def twolevel_bar():
    variants = ["A  bsearch outer + general-n inner",
                "B  two-level spine outer + general-n inner",
                "C  bsearch outer + n=4096 inner",
                "D  two-level spine outer + n=4096 inner",
                "E  Shar branchless outer + general-n inner",
                "F  Shar branchless outer + n=4096 inner",
                "G  Shar outer + Shar inner (no spine)",
                "H  Eytzinger outer + K&M PF (pre-fix) + general-n inner",
                "I  Eytzinger outer + K&M PF (pre-fix) + n=4096 inner",
                "Lem  Lemire reference (bsearch + simd_quad)"]
    short    = ["A\nbsearch\n+ general-n",
                "B\nouter spine\n+ general-n",
                "C\nbsearch\n+ n=4096",
                "D\nouter spine\n+ n=4096",
                "E\nShar outer\n+ general-n",
                "F\nShar outer\n+ n=4096",
                "G\nShar outer\n+ Shar inner",
                "H (pre-fix PF)\nEytz PF\n+ general-n",
                "I (pre-fix PF)\nEytz PF\n+ n=4096",
                "Lemire ref\nbsearch\n+ simd_quad"]
    hosts_present = [h for h in summary_hosts if h in host_twolevel]

    # Each dataset is a 2-tuple (warm, cold) [legacy] or 4-tuple
    # (hot_bat, hot_ser, cold_bat, cold_ser) [new harness]. Map every
    # panel to the appropriate tuple index; for legacy 2-tuples, the
    # hot_bat panel reuses warm and the cold_bat panel reuses cold;
    # the serial panels are drawn empty (marked "not yet ported").
    panels = [("hot_bat",  "hot + batched\n(reuse set, independent queries, OoO overlaps)"),
              ("hot_ser",  "hot + serial\n(reuse set, dep-chained queries, critical-path latency)"),
              ("cold_bat", "cold + batched\n(fresh set per query, OoO overlaps DRAM misses)"),
              ("cold_ser", "cold + serial\n(fresh set per query, dep-chained; worst case)")]
    # Index into each host's dict value.
    def pick(tup, panel):
        if len(tup) == 2:
            # Legacy 2-tuple (warm, cold). hot_bat~=warm, cold_bat~=cold.
            # Serial modes unavailable -- return None.
            return {"hot_bat": tup[0], "cold_bat": tup[1],
                    "hot_ser": None, "cold_ser": None}[panel]
        return {"hot_bat": tup[0], "hot_ser": tup[1],
                "cold_bat": tup[2], "cold_ser": tup[3]}[panel]

    fig, axes = plt.subplots(2, 2, figsize=(18, 10), sharey=False)
    axes_flat = axes.flat
    x = np.arange(len(variants))
    w = 0.8 / max(1, len(hosts_present))

    for ax, (panel, title) in zip(axes_flat, panels):
        for i, host in enumerate(hosts_present):
            offset = (i - (len(hosts_present) - 1) / 2) * w
            data = host_twolevel[host]
            color = host_colors[host]
            is_prefix = host in PREFIX_TWOLEVEL_HOSTS
            # Pre-fix cold numbers are misleading (measure outer-miss
            # short-circuit). Mark with hatching in the cold_bat panel
            # for legacy-data hosts; the serial panels are empty for
            # those hosts anyway, so no hatching needed there.
            hatch = "///" if (is_prefix and panel == "cold_bat") else None
            label = f"{host} (pre-fix)" if (is_prefix and panel.startswith("cold")) else host
            if data is None:
                heights = [0] * len(variants)
                ax.bar(x + offset, heights, w,
                       color=color, alpha=0.25,
                       edgecolor=color, linestyle="--", linewidth=1.0,
                       label=f"{host} (not yet ported)")
                continue
            # Check per-panel data availability.
            sample = next(iter(data.values()))
            if pick(sample, panel) is None:
                # Legacy 2-tuple and this panel is one of the serial modes.
                ax.bar(x + offset, [0]*len(variants), w,
                       color=color, alpha=0.18,
                       edgecolor=color, linestyle=":", linewidth=0.8,
                       label=f"{host} (2-mode harness, serial N/A)")
                continue
            vals = [pick(data[v], panel) if v in data else None for v in variants]
            vals_plot = [v if v is not None else 0 for v in vals]
            bars = ax.bar(x + offset, vals_plot, w, color=color,
                          label=label, hatch=hatch,
                          edgecolor="black" if hatch else None,
                          linewidth=0.3 if hatch else 0)
            for b, v in zip(bars, vals):
                if v is None:
                    continue
                ax.text(b.get_x() + b.get_width()/2, v,
                        f"{v:.0f}", ha="center", va="bottom", fontsize=6.5)
        ax.set_xticks(x)
        ax.set_xticklabels(short, fontsize=6.5)
        ax.set_ylabel("ns / outer+inner lookup")
        ax.set_title(title, fontsize=10)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        ax.legend(loc="upper right", fontsize=6.5)
    fig.suptitle("Two-level spine micro-bench (512 containers x inner_n=4096, ~4 MB per set). "
                 "All six hosts on 4-mode harness; 5-run per-cell medians, 2026-05-18. "
                 "H/I = pre-fix PF.",
                 fontsize=11)
    fig.text(0.5, 0.004,
             "H / I (Eytzinger outer + Khuong & Morin prefetch, depth log2(B)) were measured with the "
             "mis-aimed prefetch (node i+1's line instead of node i's descendants;\n"
             "fixed in bench_twolevel.cpp 2026-10-11, not yet re-benchmarked). Bars are per-cell "
             "medians (levels); compare variants with {host}_runs/twolevel_paired.txt, not by differencing bars.",
             ha="center", va="bottom", fontsize=8, color="#444444")
    fig.tight_layout(rect=[0, 0.045, 1, 1])
    fig.savefig("bench_twolevel.png", dpi=130)
    print("wrote bench_twolevel.png")

twolevel_bar()


def twolevel_bar_f_vs_lem():
    variants = ["F  Shar branchless outer + n=4096 inner",
                "Lem  Lemire reference (bsearch + simd_quad)"]
    short    = ["F\nShar outer\n+ n=4096",
                "Lemire ref\nbsearch\n+ simd_quad"]
    hosts_present = [h for h in summary_hosts if h in host_twolevel]

    panels = [("hot_bat",  "hot + batched\n(reuse set, independent queries, OoO overlaps)"),
              ("hot_ser",  "hot + serial\n(reuse set, dep-chained queries, critical-path latency)"),
              ("cold_bat", "cold + batched\n(fresh set per query, OoO overlaps DRAM misses)"),
              ("cold_ser", "cold + serial\n(fresh set per query, dep-chained; worst case)")]
    def pick(tup, panel):
        if len(tup) == 2:
            return {"hot_bat": tup[0], "cold_bat": tup[1],
                    "hot_ser": None, "cold_ser": None}[panel]
        return {"hot_bat": tup[0], "hot_ser": tup[1],
                "cold_bat": tup[2], "cold_ser": tup[3]}[panel]

    fig, axes = plt.subplots(2, 2, figsize=(14, 9), sharey=False)
    axes_flat = axes.flat
    x = np.arange(len(variants))
    w = 0.8 / max(1, len(hosts_present))

    for ax, (panel, title) in zip(axes_flat, panels):
        for i, host in enumerate(hosts_present):
            offset = (i - (len(hosts_present) - 1) / 2) * w
            data = host_twolevel[host]
            color = host_colors[host]
            sample = next(iter(data.values()))
            if pick(sample, panel) is None:
                ax.bar(x + offset, [0]*len(variants), w,
                       color=color, alpha=0.18,
                       edgecolor=color, linestyle=":", linewidth=0.8,
                       label=f"{host} (2-mode harness, serial N/A)")
                continue
            vals = [pick(data[v], panel) if v in data else None for v in variants]
            vals_plot = [v if v is not None else 0 for v in vals]
            bars = ax.bar(x + offset, vals_plot, w, color=color, label=host)
            for b, v in zip(bars, vals):
                if v is None:
                    continue
                ax.text(b.get_x() + b.get_width()/2, v,
                        f"{v:.0f}", ha="center", va="bottom", fontsize=8)
        ax.set_xticks(x)
        ax.set_xticklabels(short, fontsize=9)
        ax.set_ylabel("ns / outer+inner lookup")
        ax.set_title(title, fontsize=10)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        ax.legend(loc="upper right", fontsize=8)
    fig.suptitle("Two-level spine: variant F (shipped) vs Lemire reference "
                 "(512 containers x inner_n=4096, ~4 MB per set). "
                 "All six hosts on 4-mode harness; 5-run per-cell medians, 2026-05-18.",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig("bench_twolevel_f_vs_lem.png", dpi=130)
    print("wrote bench_twolevel_f_vs_lem.png")

twolevel_bar_f_vs_lem()


# --- per-host best-strategy vs Lemire reference ---
# One line per host showing the shipped best single-array strategy
# (host's simd_quad_* + spine across the full size sweep; for n=4096
# we swap in the compile-time-n=4096 unroll where it's strictly
# better, which is every host except M4 cold). Plotted against the
# reference simd_quad.c (Lemire's algorithm as ported) per host as
# a dashed line, so you can see the structural advance at each n.

def best_line(host, regime):
    _xs, warm, cold = host_src[host]
    src = warm if regime == "warm" else cold
    _, spine_key = host_tuned[host]
    base = list(src[spine_key])
    sp = host_spine_4096.get(host)
    if sp is not None:
        candidate = sp["warm"] if regime == "warm" else sp["cold"]
        if candidate < base[-1]:
            base[-1] = candidate
    return base

def reference_line(host, regime):
    _xs, warm, cold = host_src[host]
    src = warm if regime == "warm" else cold
    return list(src["simd_quad (reference)"])

def best_vs_reference(regime, out, title):
    fig, ax = plt.subplots(figsize=(9, 6))
    for host in summary_hosts:
        color = host_colors[host]
        xs = host_src[host][0]
        ax.plot(xs, reference_line(host, regime),
                linestyle="--", marker="o", markersize=4,
                color=color, alpha=0.55, linewidth=1.2,
                label=f"{host} - simd_quad (reference)")
        ax.plot(xs, best_line(host, regime),
                linestyle="-",  marker="s", markersize=6,
                color=color, linewidth=2.0,
                label=f"{host} - best strategy")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xticks(label_sizes)
    ax.set_xticklabels(label_strs)
    ax.set_xlabel("array size n (u16 elements)")
    ax.set_ylabel("nanoseconds per query")
    ax.set_title(title)
    ax.grid(True, which="both", linestyle=":", alpha=0.4)
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    print(f"wrote {out}")

best_vs_reference("warm", "bench_best_warm.png",
                  "Best strategy per host vs. Lemire SIMD Quad reference (warm cache)")
best_vs_reference("cold", "bench_best_cold.png",
                  "Best strategy per host vs. Lemire SIMD Quad reference (cold cache)")


# --- text comparison table ---
# All hosts, all algorithms. The per-arch variants only appear on their
# native host, so gaps are left blank for the others.

def has_data(d, key):
    return key in d and all(v is not None for v in d[key])

def table_text():
    # (label, sizes, warm, cold); cells at sizes a host did not sweep print "-".
    table_hosts = [("Pi 5",         pi5_sizes, pi5_warm,  pi5_cold)]
    table_hosts.append(("M4 Max",   m4_sizes,  m4_warm,   m4_cold))
    if have_m1:
        table_hosts.append(("M1 Pro", m1_sizes, m1_warm, m1_cold))
    if have_skx:
        table_hosts.append(("SKX",  skx_sizes, skx_warm,  skx_cold))
    if have_emr:
        table_hosts.append(("EMR",  emr_sizes, emr_warm,  emr_cold))
    if have_gv4:
        table_hosts.append(("GV4",  gv4_sizes, gv4_warm,  gv4_cold))

    algos_ordered = [
        "linear (std::find)",
        "binary (std::binary_search)",
        "simd_quad (reference)",
        "simd_quad_pi5",
        "simd_quad_pi5 + spine",
        "simd_quad_m4",
        "simd_quad_m4 + spine",
        "simd_quad_intel",
        "simd_quad_intel + spine",
        "simd_quad_graviton",
        "simd_quad_graviton + spine",
    ]

    lines = []
    lines.append("Per-cell medians of 5 runs of ./bench 4000 5000, taken with the pre-flush "
                 "bench.cpp (no cache flush before 2026-10-11, so the cold column is DRAM-cold only on "
                 "the Pi 5, and there only for n > 256; Text/corrections_2026-10.md section 5). '-' = size not in that "
                 "host's archived sweep: M4 Max / M1 Pro / SKX / EMR / GV4 "
                 "rebench_run{1..5}.txt (2026-05-01) cover only the 10 power-of-two sizes; "
                 "Pi 5 (2026-05-12) covers all 22.")
    for regime_name, regime in [("WARM", "warm"), ("COLD", "cold")]:
        lines.append(f"\n=== {regime_name} CACHE (ns/query) ===")
        header = f"{'algorithm':32s}  {'machine':8s}" + "".join(f"{s:>7d}" for s in sizes)
        lines.append(header)
        lines.append("-" * len(header))
        for a in algos_ordered:
            emitted = False
            for label, xs, warm, cold in table_hosts:
                src = warm if regime == "warm" else cold
                if has_data(src, a):
                    by_size = dict(zip(xs, src[a]))
                    row = f"{a:32s}  {label:8s}" + "".join(
                        f"{by_size[s]:>7.1f}" if s in by_size else f"{'-':>7s}"
                        for s in sizes)
                    lines.append(row)
                    emitted = True
            if emitted:
                lines.append("")

    # Compile-time n=4096 unroll: pulled out separately because it only
    # applies at that single size.
    lines.append("=== compile-time n=4096 hybrid (ns/query; replaced the retired unroll 2026-05-12) ===")
    lines.append(f"{'host':16s}  {'general-n warm':>14s}  {'hybrid warm':>12s}  "
                 f"{'general-n cold':>14s}  {'hybrid cold':>12s}")
    for host in ["Pi 5 (A76)", "M4 Max", "M1 Pro", "Intel Skylake", "Intel Emerald", "Graviton 4"]:
        if host not in host_src:
            continue
        _xs, warm, cold = host_src[host]
        spine_key = (
            "simd_quad_pi5 + spine"      if host == "Pi 5 (A76)" else
            "simd_quad_m4 + spine"       if host in ("M4 Max", "M1 Pro") else
            "simd_quad_graviton + spine" if host == "Graviton 4" else
            "simd_quad_intel + spine")
        gw = warm[spine_key][-1]
        gc = cold[spine_key][-1]
        sp = host_spine_4096.get(host)
        uw = f"{sp['warm']:>12.2f}" if sp else f"{'(not yet)':>12s}"
        uc = f"{sp['cold']:>12.2f}" if sp else f"{'(not yet)':>12s}"
        lines.append(f"{host:16s}  {gw:14.2f}  {uw}  {gc:14.2f}  {uc}")
    lines.append("")

    # Two-level spine A-G table. Hosts on the new 4-mode harness
    # print (hot_bat, hot_ser, cold_bat, cold_ser); legacy hosts print
    # (warm, cold) in the hot_bat / cold_bat columns with "-" in the
    # serial columns.
    lines.append("=== two-level spine micro-bench (ns/lookup, 512 containers, inner_n=4096) ===")
    lines.append(f"{'host':16s}  {'var':4s}  "
                 f"{'hot_bat':>8s}  {'hot_ser':>8s}  "
                 f"{'cold_bat':>9s}  {'cold_ser':>9s}  description")
    for host in ["Pi 5 (A76)", "M4 Max", "M1 Pro", "Intel Skylake", "Intel Emerald", "Graviton 4"]:
        data = host_twolevel.get(host)
        if data is None:
            lines.append(f"{host:16s}  (not yet ported)")
            continue
        for k, tup in data.items():
            var, desc = k.split("  ", 1)
            if len(tup) == 2:
                w_, c_ = tup
                lines.append(f"{host:16s}  {var:4s}  "
                             f"{w_:8.2f}  {'-':>8s}  "
                             f"{c_:9.2f}  {'-':>9s}  {desc}")
            else:
                hb, hs, cb, cs = tup
                lines.append(f"{host:16s}  {var:4s}  "
                             f"{hb:8.2f}  {hs:8.2f}  "
                             f"{cb:9.2f}  {cs:9.2f}  {desc}")
    lines.append("")

    return "\n".join(lines)

text = table_text()
with open("bench_table.txt", "w") as f:
    f.write(text + "\n")
print("wrote bench_table.txt")
print(text)

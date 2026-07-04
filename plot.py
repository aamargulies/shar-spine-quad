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
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sizes = [8, 11, 16, 23, 32, 47, 64, 89, 128, 177,
         256, 333, 512, 617, 1001, 1024, 1234, 1777,
         2048, 2999, 3967, 4096]

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
m4_warm = {
    "linear (std::find)":          [   1.60,    2.30,    2.80,    4.20,    5.20,    7.90,   10.30,   14.30,   20.30,   27.70,   39.90,   51.70,   87.00,  102.60,  162.80,  166.80,  198.80,  280.90,  327.00,  462.20,  609.10,  628.50],
    "binary (std::binary_search)": [   4.60,    6.70,    4.50,    8.00,    5.00,    9.20,    5.50,   11.50,    6.20,   13.50,    7.10,   15.20,    8.10,   14.90,    9.60,    9.30,   16.10,   13.00,   10.80,   19.20,   12.60,   12.20],
    "simd_quad (reference)":       [   2.10,    2.90,    1.40,    5.00,    1.60,    6.60,    2.10,    4.00,    2.50,    3.90,    3.30,    4.60,    3.80,    5.70,    5.60,    4.80,    5.40,    5.90,    5.50,    6.50,    6.60,    6.60],
    "simd_quad_pi5":               [   1.50,    3.80,    1.30,    4.60,    2.00,    6.40,    2.00,    7.00,    2.40,    4.90,    2.80,    4.70,    3.80,    5.90,    5.90,    4.40,    6.50,    6.00,    5.70,    7.00,    7.10,    6.40],
    "simd_quad_pi5 + spine":       [   1.50,    3.80,    1.20,    4.60,    2.50,    6.90,    2.50,    7.40,    2.10,    4.30,    2.30,    3.70,    2.80,    4.30,    4.30,    3.40,    5.00,    4.30,    4.10,    5.30,    5.30,    4.70],
    "simd_quad_m4":                [   1.70,    4.00,    1.50,    4.90,    1.50,    5.70,    2.10,    6.60,    2.20,    7.90,    2.70,    3.80,    3.00,    5.10,    6.00,    3.70,    5.40,    5.70,    4.40,    5.70,    5.60,    5.30],
    "simd_quad_m4 + spine":        [   1.70,    4.00,    1.50,    4.90,    1.30,    5.50,    2.60,    6.80,    2.70,    8.20,    2.40,    3.60,    2.90,    4.60,    5.30,    3.30,    4.80,    5.00,    3.80,    4.90,    4.80,    4.50],
    "simd_quad_graviton":          [   1.50,    3.70,    1.30,    4.70,    2.00,    6.30,    2.00,    6.90,    2.20,    4.60,    2.60,    4.30,    3.40,    5.30,    5.20,    3.90,    5.90,    5.30,    5.00,    6.40,    6.50,    5.60],
    "simd_quad_graviton + spine":  [   1.50,    3.70,    1.30,    4.60,    2.50,    6.70,    2.50,    7.30,    2.20,    4.30,    2.40,    3.80,    2.80,    4.40,    4.30,    3.30,    5.00,    4.30,    4.10,    5.40,    5.40,    4.80],
}
m4_cold = {
    "linear (std::find)":          [   4.90,    5.40,    6.10,    7.10,    7.90,    9.10,   11.80,   14.30,   19.60,   26.30,   34.20,   47.10,   70.40,   83.70,  128.20,  148.10,  155.10,  225.00,  257.40,  373.10,  484.80,  523.70],
    "binary (std::binary_search)": [   4.60,    5.60,    4.50,    7.20,    4.30,    7.70,    4.60,   10.20,    5.50,   12.90,    7.90,   18.10,   13.80,   24.60,   22.30,   33.10,   42.50,   48.80,   44.00,   76.70,   63.60,   81.50],
    "simd_quad (reference)":       [   5.30,    6.20,    1.50,    5.00,    1.60,    7.00,    2.10,    4.00,    2.60,    3.90,    4.20,    6.30,    6.40,   10.80,   10.10,   15.60,   18.70,   27.60,   17.50,   41.60,   29.60,   39.00],
    "simd_quad_pi5":               [   1.20,    5.50,    1.10,    6.00,    1.90,    6.90,    1.90,    6.70,    2.70,    5.60,    4.10,    6.80,    6.10,    9.40,    8.70,    8.00,   20.20,   26.60,   11.70,   17.70,   17.10,   20.60],
    "simd_quad_pi5 + spine":       [   1.30,    5.60,    1.10,    5.90,    2.40,    7.40,    2.40,    7.40,    2.50,    5.30,    2.70,    4.20,    3.80,    5.00,    5.10,    4.30,    6.20,    8.70,    6.20,    8.40,    9.90,    6.20],
    "simd_quad_m4":                [   1.60,    5.60,    1.30,    6.20,    1.30,    8.00,    2.10,    6.20,    2.60,    8.60,    4.20,    5.70,    5.10,    7.40,    9.90,    8.10,   21.20,   24.80,   11.30,   34.70,   16.20,   20.40],
    "simd_quad_m4 + spine":        [   1.60,    5.20,    1.30,    6.40,    1.40,    7.90,    2.50,    6.50,    2.70,    8.80,    3.30,    4.50,    3.60,    6.00,    6.20,    4.30,    5.70,    6.60,    5.00,    6.80,    7.80,    7.70],
    "simd_quad_graviton":          [   1.30,    5.00,    1.00,    6.40,    1.90,    7.00,    1.90,    7.20,    2.40,    5.30,    4.10,    6.40,    5.30,    7.60,    7.70,    6.40,    9.70,   13.70,    8.70,   15.20,   13.70,   17.40],
    "simd_quad_graviton + spine":  [   1.50,    5.40,    1.00,    6.50,    2.40,    7.30,    2.40,    7.80,    2.30,    5.10,    2.60,    4.20,    3.10,    5.10,    4.60,    3.70,    5.70,    5.80,    6.20,    8.80,    9.50,   10.20],
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
skx_warm = {
    "linear (std::find)":          [  16.10,   18.00,   20.40,   23.60,   17.40,   23.30,   18.80,   21.80,   21.90,   25.70,   27.40,   32.80,   39.50,   49.10,   63.00,   64.50,   85.20,  105.70,  116.50,  167.40,  208.10,  214.40],
    "binary (std::binary_search)": [  25.10,   27.20,   29.90,   32.30,   36.20,   38.80,   43.90,   46.30,   51.60,   54.60,   59.30,   60.60,   67.00,   66.80,   71.40,   71.30,   72.90,   77.00,   76.70,   80.90,   82.30,   82.60],
    "simd_quad (reference)":       [  17.80,   20.10,   15.80,   23.20,   17.00,   26.80,   17.20,   22.30,   18.50,   23.80,   21.50,   24.50,   23.60,   30.00,   29.40,   27.00,   29.30,   32.40,   29.60,   32.70,   33.90,   33.20],
    "simd_quad_intel":             [  12.90,   18.00,   12.90,   21.80,   14.70,   23.60,   15.40,   27.80,   17.70,   23.10,   19.10,   24.00,   22.60,   29.60,   29.40,   25.40,   32.30,   28.60,   29.30,   34.40,   34.50,   31.60],
    "simd_quad_intel + spine":     [  12.40,   17.80,   12.10,   20.10,   14.80,   23.30,   15.50,   26.00,   16.60,   20.90,   17.30,   22.80,   19.70,   25.30,   25.50,   22.40,   27.70,   25.30,   25.60,   30.50,   30.50,   27.90],
}
skx_cold = {
    "linear (std::find)":          [  23.60,   24.40,   27.20,   30.80,   31.90,   38.00,   36.80,   41.60,   45.10,   53.00,   62.60,   75.40,  106.20,  121.60,  182.90,  185.90,  221.20,  300.70,  333.10,  465.10,  598.50,  599.80],
    "binary (std::binary_search)": [  28.40,   30.80,   33.20,   37.90,   38.70,   42.20,   48.00,   51.00,   60.00,   65.40,   79.40,   89.40,  137.60,  125.70,  159.70,  169.20,  171.10,  198.30,  230.50,  236.80,  268.70,  272.00],
    "simd_quad (reference)":       [  20.00,   21.70,   14.60,   22.00,   15.60,   24.80,   15.80,   21.40,   20.20,   31.30,   39.40,   44.30,   87.40,   78.80,   95.80,   94.30,  111.10,  164.00,  138.30,  208.40,  232.20,  193.10],
    "simd_quad_intel":             [  11.90,   18.30,   11.60,   23.00,   12.70,   21.90,   13.90,   25.30,   17.80,   23.50,   26.80,   40.00,   64.30,   71.90,   99.40,   79.80,  126.30,  139.50,  128.00,  153.10,  201.90,  179.10],
    "simd_quad_intel + spine":     [  11.00,   17.30,   10.80,   20.50,   12.50,   20.60,   13.90,   24.60,   19.20,   25.10,   26.60,   34.30,   48.60,   53.90,   69.70,   63.60,   84.00,   94.30,   98.00,  155.90,  139.00,  131.90],
}
have_skx = all(skx_warm["simd_quad_intel"][i] is not None for i in range(len(sizes)))

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
emr_warm = {
    "linear (std::find)":          [   2.50,    3.40,    4.00,    5.00,    6.50,    8.50,   11.50,   15.70,   21.50,   30.00,   42.70,   54.50,   83.00,  114.80,  174.40,  177.30,  210.80,  299.00,  339.70,  489.90,  637.20,  656.10],
    "binary (std::binary_search)": [  14.60,   16.30,   18.60,   20.70,   23.00,   25.20,   27.60,   29.70,   33.40,   35.30,   39.40,   40.90,   45.20,   46.20,   50.30,   50.20,   51.60,   54.60,   55.50,   58.70,   61.00,   61.00],
    "simd_quad (reference)":       [   2.90,    3.70,    3.20,    9.40,    3.20,   10.30,    4.90,    7.50,   10.80,    7.90,    7.50,   11.20,   15.10,   11.40,   11.30,   10.20,   13.60,   18.50,   18.90,   13.60,   13.70,   13.60],
    "simd_quad_intel":             [   2.50,    6.20,    2.50,    7.70,    3.10,   10.20,    3.20,   10.20,    4.70,    7.50,   10.30,    8.50,    7.60,   10.40,   10.20,   15.20,   11.20,   10.20,    9.90,   17.40,   19.70,   19.40],
    "simd_quad_intel + spine":     [   2.50,    6.30,    2.50,    7.80,    3.90,   11.00,    4.10,   11.10,    4.40,    7.10,   10.20,    7.40,    6.50,    9.40,    9.20,   14.70,    9.70,    9.30,    9.10,   15.90,   18.10,   17.90],
}
emr_cold = {
    "linear (std::find)":          [   8.40,    9.10,    9.90,   11.20,   12.20,   14.40,   16.70,   19.10,   23.40,   31.40,   40.20,   56.20,   75.50,   94.90,  140.20,  142.30,  169.90,  232.70,  275.10,  377.80,  487.70,  498.30],
    "binary (std::binary_search)": [  17.50,   18.90,   22.00,   22.90,   25.80,   28.00,   31.00,   32.30,   37.20,   38.10,   45.30,   49.80,   61.50,   66.60,   79.40,   79.60,   85.20,   94.70,  108.20,  109.40,  119.40,  119.40],
    "simd_quad (reference)":       [   8.30,    9.40,    3.40,    9.80,    3.00,   10.60,    5.00,    7.80,   11.90,   10.60,   15.60,   23.40,   33.30,   40.20,   48.20,   46.10,   51.10,   57.50,   68.80,   69.00,   73.50,   73.70],
    "simd_quad_intel":             [   2.50,    8.20,    2.50,   10.50,    3.00,   10.50,    3.20,   10.70,    5.50,    8.90,   15.10,   19.40,   25.60,   37.30,   45.00,   39.50,   48.80,   48.80,   59.50,   63.20,   69.50,   66.90],
    "simd_quad_intel + spine":     [   2.50,    8.20,    2.50,    9.70,    4.20,   10.90,    3.90,   11.40,    5.40,    8.90,   12.90,   15.40,   15.90,   22.30,   24.50,   23.90,   26.10,   27.10,   32.20,   33.90,   38.90,   37.20],
}
have_emr = all(emr_warm["simd_quad_intel"][i] is not None for i in range(len(sizes)))

# AWS Graviton 4 (Arm Neoverse V2, CPU part 0xd4f). r8g EC2 instance.
# Per-cell median across 5 runs of `./bench 4000 5000`, GCC 11.5 with
# -O3 -mcpu=neoverse-v2. Re-measured 2026-05-01 from gv4_runs/rebench_run{1..5}.txt
# (the original gv4_runs/baseline_run*.txt was the prefetch A/B control set).
#
# V2 is a 64-byte-line 128-bit-NEON ARM core with 4 load AGUs and a deep
# OoO window, so simd_quad_graviton uses gap=32 (cache-line sized) and
# drops the A76's speculative __builtin_prefetch inside the interpolation
# loop. Polarity matches M4 Max and Emerald Rapids ("hint is pure
# dispatch waste on wide-OoO cores").
gv4_warm = {
    "linear (std::find)":          [   3.10,    4.10,    5.10,    7.20,    8.60,   11.60,   15.80,   21.50,   30.30,   40.80,   69.30,   75.70,  116.90,  139.20,  233.20,  235.40,  283.40,  410.90,  464.40,  676.60,  889.10,  903.90],
    "binary (std::binary_search)": [  11.70,   13.10,   14.90,   16.60,   18.30,   20.10,   21.90,   23.40,   25.60,   27.20,   29.80,   31.00,   34.50,   35.50,   39.00,   39.00,   39.70,   42.80,   43.80,   45.40,   48.20,   48.40],
    "simd_quad (reference)":       [   3.60,    4.70,    3.20,    8.00,    3.20,    8.60,    4.90,    7.10,    9.60,    8.60,    7.80,   11.50,   15.30,   12.30,   12.20,   11.20,   14.50,   19.50,   19.90,   15.10,   15.20,   15.20],
    "simd_quad_graviton":          [   2.90,    5.40,    2.90,    6.60,    3.30,    8.90,    3.50,    8.80,    5.10,    7.60,    9.80,    8.80,    7.90,   11.40,   11.20,   15.60,   12.20,   11.30,   11.10,   18.20,   20.50,   20.00],
    "simd_quad_graviton + spine":  [   2.80,    5.50,    2.80,    6.80,    3.80,    9.30,    4.00,    9.50,    4.50,    6.50,    8.60,    7.10,    6.20,    8.20,    8.00,   13.40,    8.60,    8.10,    7.90,   13.30,   16.40,   16.30],
}
gv4_cold = {
    "linear (std::find)":          [   6.50,    6.50,    8.50,    8.90,   11.00,   13.70,   16.80,   21.00,   29.20,   38.00,   54.50,   69.30,  101.20,  120.30,  197.00,  207.70,  243.80,  352.60,  419.60,  621.50,  798.50,  812.90],
    "binary (std::binary_search)": [  13.70,   15.10,   17.20,   19.20,   21.70,   23.50,   26.20,   27.80,   31.40,   33.00,   36.50,   38.20,   42.60,   45.70,   55.10,   57.40,   61.50,   77.10,   86.20,  105.90,  130.70,  129.50],
    "simd_quad (reference)":       [   6.20,    6.80,    3.10,    7.80,    3.30,    8.70,    5.30,    8.00,   10.80,   11.20,   11.30,   16.40,   22.30,   25.30,   36.20,   36.00,   39.70,   52.80,   58.80,   69.60,   84.90,   97.30],
    "simd_quad_graviton":          [   2.60,    6.60,    2.60,    8.70,    3.50,    9.30,    4.00,    9.60,    6.80,   10.10,   13.40,   13.70,   16.70,   22.20,   32.50,   32.20,   37.50,   42.50,   43.20,   56.40,   64.10,   62.70],
    "simd_quad_graviton + spine":  [   2.60,    6.60,    2.60,    8.30,    3.90,    9.50,    4.40,   10.00,    6.10,    9.00,   10.60,   12.00,   16.50,   20.20,   18.80,   19.00,   19.80,   24.30,   23.20,   32.00,   37.10,   37.50],
}
have_gv4 = all(gv4_warm["simd_quad_graviton"][i] is not None for i in range(len(sizes)))

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
m1_warm = {
    "linear (std::find)":          [   2.30,    3.20,    3.90,    5.60,    7.10,   10.40,   13.60,   18.80,   26.60,   36.50,   52.80,   77.70,  112.90,  134.00,  211.30,  215.40,  257.30,  368.70,  418.90,  605.60,  791.80,  815.70],
    "binary (std::binary_search)": [   8.10,    9.40,    7.30,   11.10,    7.50,   13.00,    8.20,   16.10,    9.30,   18.40,   10.70,   20.90,   12.30,   20.10,   14.30,   14.00,   22.40,   18.80,   15.70,   26.50,   18.40,   17.70],
    "simd_quad (reference)":       [   3.40,    4.40,    2.70,    7.50,    2.70,    9.80,    3.10,    6.20,    3.60,    5.70,    4.70,    6.70,    5.40,    8.10,    8.00,    6.90,    7.80,    8.50,    7.80,    9.40,    9.50,    9.40],
    "simd_quad_pi5":               [   2.50,    5.40,    2.50,    6.50,    2.70,    9.00,    2.90,    9.90,    3.80,    7.20,    4.50,    7.00,    6.00,    8.90,    8.80,    6.80,    9.70,    8.90,    8.70,   10.50,   10.70,    9.50],
    "simd_quad_pi5 + spine":       [   2.50,    5.50,    2.50,    6.50,    3.20,    9.40,    3.20,   10.10,    3.10,    6.20,    3.60,    5.30,    4.10,    6.10,    6.00,    4.80,    6.80,    6.00,    5.70,    7.40,    7.40,    6.50],
    "simd_quad_m4":                [   2.50,    5.60,    2.50,    6.70,    2.50,    7.80,    3.10,    8.80,    3.60,   11.30,    4.10,    5.80,    4.80,    7.70,    8.60,    5.60,    7.90,    8.30,    6.50,    8.20,    8.30,    7.70],
    "simd_quad_m4 + spine":        [   2.60,    6.00,    2.50,    7.20,    2.50,    8.00,    3.70,    9.50,    3.70,   11.50,    3.90,    5.40,    4.40,    7.10,    7.70,    4.90,    6.70,    7.30,    5.70,    7.00,    7.00,    6.40],
    "simd_quad_graviton":          [   2.50,    5.50,    2.50,    6.40,    2.70,    9.00,    2.90,    9.90,    3.40,    6.80,    4.10,    6.30,    5.20,    7.70,    7.70,    6.00,    8.60,    7.80,    7.50,    9.30,    9.50,    8.40],
    "simd_quad_graviton + spine":  [   2.50,    5.50,    2.40,    6.50,    3.20,    9.40,    3.20,   10.20,    3.10,    6.30,    3.70,    5.40,    4.20,    6.10,    6.00,    5.00,    7.10,    6.10,    5.70,    7.50,    7.50,    6.70],
}
m1_cold = {
    "linear (std::find)":          [   6.70,    7.10,    7.80,    9.00,   10.00,   13.10,   15.90,   19.40,   24.60,   34.50,   47.90,   62.80,   92.10,  109.90,  168.20,  198.40,  211.40,  303.80,  333.60,  474.90,  641.70,  683.20],
    "binary (std::binary_search)": [   7.80,    8.60,    6.80,   10.10,    6.60,   12.50,    7.20,   15.40,    8.40,   17.80,   11.80,   23.80,   17.20,   26.90,   34.40,   44.60,   69.50,  105.50,   69.20,  122.70,  138.30,  154.10],
    "simd_quad (reference)":       [   8.40,    9.10,    2.50,    7.10,    2.60,    9.40,    3.10,    6.30,    3.70,    5.90,    5.60,    9.00,    9.20,   11.90,   16.00,   24.60,   34.50,   46.30,   26.40,   56.90,   51.50,   62.90],
    "simd_quad_pi5":                [  2.60,    7.20,    2.50,    8.30,    2.60,    9.10,    2.90,    9.70,    3.80,    7.60,    5.60,    9.10,    8.30,   12.70,   12.80,   12.80,   34.60,   42.70,   22.00,   34.50,   28.40,   34.90],
    "simd_quad_pi5 + spine":       [   2.60,    7.40,    2.50,    8.40,    3.10,    9.40,    3.20,    9.90,    3.60,    7.30,    4.30,    6.40,    5.70,    7.90,    9.80,    9.80,   10.50,   15.10,   13.50,   26.80,   21.60,   23.60],
    "simd_quad_m4":                [   2.70,    7.40,    2.50,    8.70,    2.50,   10.40,    3.10,    8.90,    3.90,   11.30,    5.60,    7.90,    7.60,   10.80,   13.40,   13.50,   37.50,   51.30,   22.70,   54.70,   29.70,   38.00],
    "simd_quad_m4 + spine":        [   2.70,    7.70,    2.50,    8.80,    2.50,   10.30,    3.30,    9.20,    4.00,   11.40,    4.70,    6.20,    5.20,    8.00,    9.00,    6.00,    8.40,   10.80,    8.70,    9.50,   10.40,   10.30],
    "simd_quad_graviton":          [   2.60,    7.30,    2.50,    8.30,    2.60,    9.10,    2.80,    9.60,    3.50,    7.50,    5.50,    8.60,    7.50,   11.50,   11.90,   10.50,   20.50,   37.10,   21.90,   36.00,   25.90,   35.10],
    "simd_quad_graviton + spine":  [   2.50,    7.10,    2.50,    8.30,    3.10,    9.50,    3.30,    9.90,    3.40,    6.80,    3.90,    6.00,    4.90,    7.00,    6.80,    5.80,    8.40,   10.60,   10.70,   14.20,   16.40,   16.90],
}
have_m1 = all(m1_warm["simd_quad_m4"][i] is not None for i in range(len(sizes)))

# n=4096 compile-time specialization (simd_quad_intel_spine_4096), median of 5
# ./bench 4000 5000 runs on EMR 2026-05-01. Isolated from the main table
# because it only exists at n=4096. Warm/cold are the two numbers.
emr_spine_4096 = {"warm": 6.50, "cold": 24.36}
# Same structure for Graviton 4 (simd_quad_graviton_spine_4096), measured
# on the same r8g host 2026-05-01 (median of 5 runs from rebench_run{1..5}).
gv4_spine_4096 = {"warm": 7.00, "cold": 27.24}
# Same structure for SKX (simd_quad_intel_spine_4096 on the AVX2 block-check
# path), measured on Xeon 8175M 2026-05-01 (median of 5 runs). Warm is a
# small win vs the general-n spine (27.5 -> 27.1, ~-1.5%) -- on SKX the
# scalar interpolation loop already runs at AVX-512 license L2 so the
# branch-removal effect is smaller than EMR's; cold is noise (131.9 vs
# 131.1 median, hidden by shared-tenant memory variance).
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
m4_spine_4096 = {"warm": 3.71, "cold": 21.94}
# Pi 5 (Cortex-A76) simd_quad_pi5_spine_4096, gap=32 -> 128 spine entries ->
# 256 B = 4 cache lines. Shape is the 2026-05-12 hybrid (3-iter quaternary
# + branchless 2-probe finish), same as the GV4 and EMR _spine_4096.
# Measured on the Pi 5 4-core A76, median of 5 runs from
# pi5_runs/hybrid_run{1..5}.txt.
#
# The hybrid-vs-unroll A/B gave warm 23.36 -> 19.42 (-16.9%, monotone
# across 5/5 runs) with cold 132.1 -> 140.9 (+6.7%, inside the 107-214 ns
# cold variance band). That refutes the 2026-05-01 "GCC 15 already hoists
# loop control so branch-removal is a wash on Pi 5" hypothesis: the
# 2-probe finish saves one dependent load-use round (the binary step)
# which no compiler pass can reconstruct. Vs the general-n pi5_spine the
# hybrid's warm median is 17.75 (-27.6%) and cold 136.75 (-7.2%). Unroll
# retired; simd_quad_pi5_spine_4096 IS the hybrid. Prior-unroll numbers
# for historical comparison: warm 23.78, cold 142.10.
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
emr_twolevel = {
    # (hot_bat, hot_ser, cold_bat, cold_ser). 5-run medians 2026-05-18 (H/I re-bench).
    "A  bsearch outer + general-n inner":          (136.62, 113.12, 262.28, 446.37),
    "B  two-level spine outer + general-n inner":  (110.09,  94.99, 282.89, 440.29),
    "C  bsearch outer + n=4096 inner":             ( 62.63, 103.61, 200.71, 410.39),
    "D  two-level spine outer + n=4096 inner":     ( 79.30,  92.20, 251.27, 428.82),
    "E  Shar branchless outer + general-n inner":  ( 67.91,  69.32, 311.29, 518.94),
    "F  Shar branchless outer + n=4096 inner":     ( 55.43,  58.12, 240.31, 512.30),
    "G  Shar outer + Shar inner (no spine)":       (267.22, 143.00, 448.36, 923.46),
    "H  Eytzinger outer + 4-deep PF + general-n inner":   ( 66.75,  70.72, 363.50, 631.33),
    "I  Eytzinger outer + 4-deep PF + n=4096 inner":      ( 55.05,  62.17, 315.77, 607.45),
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
skx_twolevel = {
    # (hot_bat, hot_ser, cold_bat, cold_ser). 5-run medians 2026-05-18 under
    # full A-I + Lem 10-variant harness (H/I = Eytzinger outer + 4-deep PF
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
    "H  Eytzinger outer + 4-deep PF + general-n inner":   (100.65, 109.12,1052.16,1067.39),
    "I  Eytzinger outer + 4-deep PF + n=4096 inner":      ( 88.79, 101.20, 718.71, 941.36),
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
m4_twolevel = {
    # (hot_bat, hot_ser, cold_bat, cold_ser). 5-run medians 2026-05-18 under the
    # 4-mode harness, 10-variant binary (A-I + Lem; H/I = Eytzinger outer +
    # 4-deep PF, Khuong & Morin 2017 Listing 6). Raw in m4_runs/twolevel_run{1..5}.txt.
    # Uses the M4 Max build (default ARM gap=64 path, simd_quad_m4_spine /
    # simd_quad_m4_spine_4096 as inner).
    #
    # Deltas vs F (the project's primary recommendation for hot):
    #   I vs F:   +0.5%  +13.5%   +3.5% +103.9%   (no win; F strict-best every mode)
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
    "H  Eytzinger outer + 4-deep PF + general-n inner":   ( 16.99,  24.13, 213.96, 447.50),
    "I  Eytzinger outer + 4-deep PF + n=4096 inner":      ( 13.32,  18.53, 167.50, 574.38),
    "Lem  Lemire reference (bsearch + simd_quad)": ( 85.17,  86.28, 263.33, 546.04),
}
# Raspberry Pi 5 (Cortex-A76) two-level spine micro-bench, median of 5 runs
# 2026-05-18 under the 4-mode harness (hot_bat/hot_ser/cold_bat/cold_ser),
# 10-variant binary (A-I + Lem; H/I = Eytzinger outer + 4-deep PF, Khuong &
# Morin 2017 Listing 6). Raw in pi5_runs/twolevel_run{1..5}.txt.
# Uses the Pi 5 build of bench_twolevel.cpp (`-DQUADSEARCH_ARM_PI5`, gap=32
# outer+inner, simd_quad_pi5_spine / simd_quad_pi5_spine_4096 as inner).
# Per-run variance on this Pi 5 sweep is wide (F hot_ser ranges 216-482 ns
# across 5 runs, ~2.2x spread; cold spreads similar). Both governor hops
# and the inserted H/I kernels reshuffling cache state explain part of it;
# medians are taken over 5 runs to compress that. Relative I-vs-F deltas
# below are still clean because both kernels run under identical per-run
# conditions.
#
# Deltas vs F (the project's primary recommendation for hot):
#   I vs F:   -0.7%  -22.5%  +18.9%  +30.3%   (hot_ser WIN; both colds lose)
#   H vs F:   +6.7%  -23.1%  +47.9%  +70.3%   (H underperforms I as elsewhere)
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
# **Pi 5 confirms the M1-Pro-style I `hot_ser` win.** Pre-registered (per
# `KhuongMorin.md` §"Hosts pending"): "Pi 5 is the *one* remaining host
# where the narrow-OoO + slow-inner story still has a plausible critical-
# path stall (slowest NEON inner across the bench + 2-AGU OoO + only host
# where inner is critical-path under batched dispatch -- possible hot_bat
# *and* hot_ser win, or full SKX-like falsification)." Result: clean
# `hot_ser` win (I -22.5% vs F, slightly larger than M1 Pro's -19.8%);
# `hot_bat` is a tie (I -0.7% vs F, within run-to-run noise). Confirms
# the model: 2 AGUs + slowest paired-x2 NEON inner = enough critical-path
# stall on dep-chained outer for explicit prefetch to act as runahead.
# Cold modes regress as expected (I bandwidth-contention with demand
# block-load, paper §4 `WL > log B` regime). The "narrow-OoO + slow-inner
# ⇒ I hot_ser win" half of the model now stands at 1/2 (M1 Pro and Pi 5
# both confirm; SKX and EMR falsify on the inner-speed axis).
#
# **Cold matrix relative ordering shifted from the 2026-05-13 baseline.**
# F now wins cold_ser (vs D +4.2% in prior run, -13.6% now) but D still
# wins cold_bat (F +29.1% vs D). The full F-cold-reversal pattern noted
# in the prior CLAUDE.md ship recommendation is partially eroded under
# this 10-variant sweep; given Pi 5 thermal variance, treat the cold
# ordering as "C/D best cold_bat, F competitive cold_ser, all within
# governor-hop noise" rather than a structural shift.
#
# G (Shar inner for n=4096) catastrophic as elsewhere (+82% / +93% hot vs A).
#
# F vs Lem (how much our stack improves on the published Lemire baseline):
#   hot_bat  -35.2%   hot_ser  -25.1%   cold_bat -23.3%   cold_ser -16.8%
#
# Ship: F for hot_bat / cold modes; **I for hot_ser** -- I beats F by
# -22.5% on dep-chained hot, losing both colds 19-30%. C remains the
# cold_bat-best alternate; D the all-around cold alternate.
# Aggregator: pi5_runs/compute_twolevel.py; summary: pi5_runs/twolevel_summary.txt.
pi5_twolevel = {
    # (hot_bat, hot_ser, cold_bat, cold_ser). 5-run medians 2026-05-18,
    # 10-variant binary (adds H/I = Eytzinger outer + 4-deep PF, Khuong &
    # Morin 2017 Listing 6). I beats F by -22.5% on hot_ser (dep-chained
    # critical path), confirming the narrow-OoO + slow-inner runahead win.
    "A  bsearch outer + general-n inner":          (238.20, 284.13,1650.36,1652.31),
    "B  two-level spine outer + general-n inner":  (231.84, 264.09,1436.01,2009.15),
    "C  bsearch outer + n=4096 inner":             (233.78, 282.78,1367.12,1471.38),
    "D  two-level spine outer + n=4096 inner":     (240.10, 268.82,1233.04,1790.45),
    "E  Shar branchless outer + general-n inner":  (256.48, 245.58,1931.18,2038.13),
    "F  Shar branchless outer + n=4096 inner":     (244.40, 328.50,1591.57,1547.03),
    "G  Shar outer + Shar inner (no spine)":       (432.88, 547.26,1739.06,2015.27),
    "H  Eytzinger outer + 4-deep PF + general-n inner":   (260.82, 252.48,2354.24,2635.44),
    "I  Eytzinger outer + 4-deep PF + n=4096 inner":      (242.76, 254.65,1892.39,2015.35),
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
# including both cold modes. Confirms the pre-registered prediction: GV4
# is the widest-OoO host in the project (4 load AGUs Neoverse V2 vs 3 on
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
# Ship: F unconditionally on GV4. No cold-serial alt needed.
# Aggregator: gv4_runs/compute_twolevel.py; summary: gv4_runs/twolevel_summary.txt.
gv4_twolevel = {
    # (hot_bat, hot_ser, cold_bat, cold_ser). 5-run medians 2026-05-18,
    # 10-variant binary (A-I + Lem). H/I = Eytzinger outer + 4-deep PF.
    "A  bsearch outer + general-n inner":          (161.29, 102.72, 382.74, 418.51),
    "B  two-level spine outer + general-n inner":  (148.54,  94.73, 345.80, 498.63),
    "C  bsearch outer + n=4096 inner":             ( 91.94,  95.44, 255.04, 406.23),
    "D  two-level spine outer + n=4096 inner":     (111.16,  89.72, 316.83, 484.37),
    "E  Shar branchless outer + general-n inner":  ( 80.11,  58.16, 325.26, 498.94),
    "F  Shar branchless outer + n=4096 inner":     ( 65.37,  50.34, 268.45, 486.13),
    "G  Shar outer + Shar inner (no spine)":       (149.60, 130.06, 359.41, 597.22),
    "H  Eytzinger outer + 4-deep PF + general-n inner":   ( 64.71,  63.18, 370.72, 635.46),
    "I  Eytzinger outer + 4-deep PF + n=4096 inner":      ( 57.49,  58.38, 311.10, 619.95),
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
# Cold reversal is PARTIAL on M1 Pro: F vs D cold_bat -14.4% (F wins),
# cold_ser +9.5% (F loses). Not the strict SKX/A76 shape (F loses both
# cold modes) and not the strict M4 shape (F ties/wins both). M1 Pro is
# a 3-AGU wide-OoO Apple core like M4 but runs ~2x slower absolute, so
# dep-chain stalls have more wall-clock room to matter -- plausibly why
# cold_ser reverses even with wide OoO. Hot win is unambiguous in both
# modes (F vs D -23% / -44%).
#
# G (Shar inner for n=4096) catastrophic as elsewhere.
#
# F vs Lem: hot_bat -56.5%, hot_ser -66.5%, cold_bat -36.4%, cold_ser -23.7%.
# Between M4 (steeper Lem deltas) and SKX (shallower) as expected.
#
# Ship: F for hot_bat + cold modes; **I (Eytzinger outer + 4-deep PF
# + n=4096 inner) for hot_ser** -- I beats F by -19.8% on hot_ser
# (5-run median, 2026-05-18 10-variant binary), losing both cold modes
# by 12-18%. Mechanism per Khuong & Morin 2017 §4: explicit prefetch
# delivers runahead-via-software during dep-chained outer descent (the
# K=512 / 1 KB outer is too short for hardware streamers to help), but
# the same prefetches contend with demand block-loads when cold-mode
# bandwidth saturates. See KhuongMorin.md for the full result writeup
# and per-host predictions. Prior legacy 2-mode "A->F cold -77%" was
# pre-fix; superseded. Aggregator: m1_runs/compute_twolevel.py.
m1_twolevel = {
    # (hot_bat, hot_ser, cold_bat, cold_ser). 5-run medians 2026-05-18,
    # 10-variant binary (adds H/I = Eytzinger outer + 4-deep PF, Khuong &
    # Morin 2017 Listing 6). I beats F by -19.8% on hot_ser (dep-chained
    # critical path); F still strict-best on both cold modes (the cold-
    # bandwidth-saturation regime where explicit prefetches contend with
    # demand loads). Hot_bat is a tie (F 45.88 vs I 47.71). Prior 2026-05-13
    # 8-variant baseline overwritten in m1_runs/twolevel_run{1..5}.txt.
    "A  bsearch outer + general-n inner":          (394.99,  98.62, 819.38, 613.54),
    "B  two-level spine outer + general-n inner":  (112.64, 147.04, 338.54, 677.09),
    "C  bsearch outer + n=4096 inner":             ( 54.85,  75.52, 263.54, 644.38),
    "D  two-level spine outer + n=4096 inner":     ( 75.55, 116.76, 306.25, 706.25),
    "E  Shar branchless outer + general-n inner":  ( 55.53,  76.05, 268.75, 630.21),
    "F  Shar branchless outer + n=4096 inner":     ( 45.88,  79.26, 278.54, 776.46),
    "G  Shar outer + Shar inner (no spine)":       (158.26, 158.17, 356.88, 888.75),
    "H  Eytzinger outer + 4-deep PF + general-n inner":   ( 68.93,  74.33, 385.62, 826.66),
    "I  Eytzinger outer + 4-deep PF + n=4096 inner":      ( 47.71,  63.57, 328.33, 869.79),
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

def lineplot(data, title, out):
    fig, ax = plt.subplots(figsize=(8, 5))
    for name, ys in data.items():
        ax.plot(sizes, ys, label=name, **styles[name])
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

lineplot(pi5_warm, "Raspberry Pi 5 (Cortex-A76) - warm cache", "bench_warm.png")
lineplot(pi5_cold, "Raspberry Pi 5 (Cortex-A76) - cold cache", "bench_cold.png")
lineplot(m4_warm,  "Apple M4 Max (P-core) - warm cache",       "bench_m4_warm.png")
lineplot(m4_cold,  "Apple M4 Max (P-core) - cold cache",       "bench_m4_cold.png")
if have_m1:
    lineplot(m1_warm, "Apple M1 Pro (P-core) - warm cache", "bench_m1_warm.png")
    lineplot(m1_cold, "Apple M1 Pro (P-core) - cold cache", "bench_m1_cold.png")
if have_skx:
    lineplot(skx_warm, "Intel Skylake-SP (Xeon 8175M) - warm cache", "bench_skx_warm.png")
    lineplot(skx_cold, "Intel Skylake-SP (Xeon 8175M) - cold cache", "bench_skx_cold.png")
if have_emr:
    lineplot(emr_warm, "Intel Emerald Rapids - warm cache", "bench_emr_warm.png")
    lineplot(emr_cold, "Intel Emerald Rapids - cold cache", "bench_emr_cold.png")
if have_gv4:
    lineplot(gv4_warm, "AWS Graviton 4 (Arm Neoverse V2) - warm cache", "bench_gv4_warm.png")
    lineplot(gv4_cold, "AWS Graviton 4 (Arm Neoverse V2) - cold cache", "bench_gv4_cold.png")


# --- Cross-machine comparison: a faceted view (one subplot per host, all
#     algorithms for that host visible) plus a focused "best-tuned-per-host"
#     comparison (one line per host, 4 hosts).
#
# The previous implementation put all 4 hosts and 8 algorithms on one plot
# (~32 lines). It was unreadable. Facets are cleaner, and the tuned-only
# plot is the one you actually want when comparing hosts directly.

# Each host defines (label, warm-dict, cold-dict, color for the tuned plot).
hosts = [("Pi 5 (A76)",    pi5_warm, pi5_cold, "#1f77b4"),
         ("M4 Max",         m4_warm,  m4_cold, "#d62728")]
if have_m1:
    hosts.append(("M1 Pro",         m1_warm,   m1_cold,   "#9467bd"))
if have_skx:
    hosts.append(("Intel Skylake",  skx_warm,  skx_cold, "#17becf"))
if have_emr:
    hosts.append(("Intel Emerald",  emr_warm,  emr_cold, "#ff7f0e"))
if have_gv4:
    hosts.append(("Graviton 4",     gv4_warm,  gv4_cold, "#2ca02c"))

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
    for ax, (label, warm, cold, _color) in zip(axes_flat, hosts):
        src = warm if regime == "warm" else cold
        for a in facet_algos:
            if a in src and all(v is not None for v in src[a]):
                ax.plot(sizes, src[a], label=a, **styles[a])
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
    for label, warm, cold, color in hosts:
        src = warm if regime == "warm" else cold
        a = host_tuned_name[label]
        if a in src and all(v is not None for v in src[a]):
            ax.plot(sizes, src[a], label=f"{label}  ({a})",
                    color=color, linewidth=2.0, marker="o", markersize=6)
    # Also include std::binary_search on each host, thin/dashed, as a
    # reference point so readers can see what "the baseline" costs per host.
    for label, warm, cold, color in hosts:
        src = warm if regime == "warm" else cold
        if "binary (std::binary_search)" in src and \
           all(v is not None for v in src["binary (std::binary_search)"]):
            ax.plot(sizes, src["binary (std::binary_search)"],
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
host_src = {
    "Pi 5 (A76)":    (pi5_warm, pi5_cold),
    "M4 Max":        (m4_warm,  m4_cold),
}
if have_m1:
    host_src["M1 Pro"]        = (m1_warm,  m1_cold)
if have_skx:
    host_src["Intel Skylake"] = (skx_warm, skx_cold)
if have_emr:
    host_src["Intel Emerald"] = (emr_warm, emr_cold)
if have_gv4:
    host_src["Graviton 4"]    = (gv4_warm, gv4_cold)

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
    warm, cold = host_src[host]
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
    other_hosts.append(("M4 Max",        m4_warm,   m4_cold,   "#d62728"))
if have_m1:
    other_hosts.append(("M1 Pro",        m1_warm,   m1_cold,   "#9467bd"))
if have_skx:
    other_hosts.append(("Intel Skylake", skx_warm,  skx_cold,  "#17becf"))
if have_emr:
    other_hosts.append(("Intel Emerald", emr_warm,  emr_cold,  "#ff7f0e"))
if have_gv4:
    other_hosts.append(("Graviton 4",    gv4_warm,  gv4_cold,  "#2ca02c"))

fig, (ax_w, ax_c) = plt.subplots(1, 2, figsize=(14, 5.5))

def ratio_plot(ax, regime, title):
    # For each non-Pi-5 host, plot Pi5/host ratio for the two portable
    # algos (binary, simd reference) and that host's tuned+spine.
    pi_src = pi5_warm if regime == "warm" else pi5_cold
    # Linestyles: portable algos solid-thin, tuned+spine thick.
    for name, warm, cold, color in other_hosts:
        src = warm if regime == "warm" else cold
        # portable: binary
        a = "binary (std::binary_search)"
        r = [pi_src[a][i] / src[a][i] for i in range(len(sizes))]
        ax.plot(sizes, r, label=f"{name}  binary",
                color=color, linestyle=":", marker="s", markersize=5,
                linewidth=1.2, alpha=0.75)
        # portable: simd reference
        a = "simd_quad (reference)"
        r = [pi_src[a][i] / src[a][i] for i in range(len(sizes))]
        ax.plot(sizes, r, label=f"{name}  simd_quad ref",
                color=color, linestyle="--", marker="^", markersize=5,
                linewidth=1.2, alpha=0.75)
        # each host's own tuned+spine vs Pi 5 pi5+spine
        host_tuned = host_tuned_name[name]
        pi_tuned   = "simd_quad_pi5 + spine"
        if host_tuned in src and all(v is not None for v in src[host_tuned]):
            r = [pi_src[pi_tuned][i] / src[host_tuned][i]
                 for i in range(len(sizes))]
            ax.plot(sizes, r, label=f"{name}  tuned+spine",
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
    "M4 Max":        m4_spine_4096,    # measured 2026-05-01 (warm win, cold regression)
    "M1 Pro":        m1_spine_4096,    # measured 2026-05-01 (warm wash, cold regression -- same as M4)
    "Intel Skylake": skx_spine_4096,   # measured 2026-05-01 (AVX2 block-check path)
    "Intel Emerald": emr_spine_4096,   # measured 2026-05-01
    "Graviton 4":    gv4_spine_4096,   # measured 2026-05-01
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
            warm, cold = host_src[host]
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
                       label="compile-time n=4096 unroll")
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
# session).

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
                "H  Eytzinger outer + 4-deep PF + general-n inner",
                "I  Eytzinger outer + 4-deep PF + n=4096 inner",
                "Lem  Lemire reference (bsearch + simd_quad)"]
    short    = ["A\nbsearch\n+ general-n",
                "B\nouter spine\n+ general-n",
                "C\nbsearch\n+ n=4096",
                "D\nouter spine\n+ n=4096",
                "E\nShar outer\n+ general-n",
                "F\nShar outer\n+ n=4096",
                "G\nShar outer\n+ Shar inner",
                "H\nEytz PF\n+ general-n",
                "I\nEytz PF\n+ n=4096",
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
                 "All six hosts on 4-mode harness (2026-05-13).",
                 fontsize=11)
    fig.tight_layout()
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
                 "All six hosts on 4-mode harness (2026-05-13).",
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
    warm, cold = host_src[host]
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
    warm, cold = host_src[host]
    src = warm if regime == "warm" else cold
    return list(src["simd_quad (reference)"])

def best_vs_reference(regime, out, title):
    fig, ax = plt.subplots(figsize=(9, 6))
    for host in summary_hosts:
        color = host_colors[host]
        ax.plot(sizes, reference_line(host, regime),
                linestyle="--", marker="o", markersize=4,
                color=color, alpha=0.55, linewidth=1.2,
                label=f"{host} - simd_quad (reference)")
        ax.plot(sizes, best_line(host, regime),
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
    table_hosts = [("Pi 5",         pi5_warm,  pi5_cold)]
    table_hosts.append(("M4 Max",   m4_warm,   m4_cold))
    if have_m1:
        table_hosts.append(("M1 Pro", m1_warm, m1_cold))
    if have_skx:
        table_hosts.append(("SKX",  skx_warm,  skx_cold))
    if have_emr:
        table_hosts.append(("EMR",  emr_warm,  emr_cold))
    if have_gv4:
        table_hosts.append(("GV4",  gv4_warm,  gv4_cold))

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
    for regime_name, regime in [("WARM", "warm"), ("COLD", "cold")]:
        lines.append(f"\n=== {regime_name} CACHE (ns/query) ===")
        header = f"{'algorithm':32s}  {'machine':8s}" + "".join(f"{s:>7d}" for s in sizes)
        lines.append(header)
        lines.append("-" * len(header))
        for a in algos_ordered:
            emitted = False
            for label, warm, cold in table_hosts:
                src = warm if regime == "warm" else cold
                if has_data(src, a):
                    row = f"{a:32s}  {label:8s}" + "".join(f"{v:>7.1f}" for v in src[a])
                    lines.append(row)
                    emitted = True
            if emitted:
                lines.append("")

    # Compile-time n=4096 unroll: pulled out separately because it only
    # applies at that single size.
    lines.append("=== compile-time n=4096 unroll (ns/query) ===")
    lines.append(f"{'host':16s}  {'general-n warm':>14s}  {'unroll warm':>12s}  "
                 f"{'general-n cold':>14s}  {'unroll cold':>12s}")
    for host in ["Pi 5 (A76)", "M4 Max", "M1 Pro", "Intel Skylake", "Intel Emerald", "Graviton 4"]:
        if host not in host_src:
            continue
        warm, cold = host_src[host]
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

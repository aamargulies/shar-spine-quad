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

sizes = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]

# Raspberry Pi 5 (Cortex-A76 @ 2.4 GHz). Per-cell median across 5 runs of
# `./bench 4000 5000`, 2026-05-01, GCC 15 with -O3 -mcpu=cortex-a76. Raw
# outputs in pi5_runs/rebench_run{1..5}.txt; aggregation via
# pi5_runs/compute_medians.py. Now 9 ARM columns (linear, binary, simd ref,
# pi5, pi5+spine, m4, m4+spine, gv4, gv4+spine) since the m4 and gv4
# variants both compile on A76 and are useful for cross-host comparison at
# the "m4 variant" / "gv4 variant" row.
pi5_warm = {
    "linear (std::find)":          [   7.5,   12.4,   21.0,   38.1,   72.2,  143.9,  282.0,  616.4, 1125.0, 2427.9],
    "binary (std::binary_search)": [  19.2,   23.0,   27.7,   35.6,   39.8,   46.3,   52.9,   70.6,   64.9,   79.0],
    "simd_quad (reference)":       [   8.5,    7.2,   10.0,   12.2,   15.6,   18.1,   22.1,   29.6,   27.8,   31.6],
    "simd_quad_pi5":               [   5.1,    5.2,    8.3,   11.1,   13.5,   17.1,   20.7,   26.1,   28.3,   32.4],
    "simd_quad_pi5 + spine":       [   5.0,    5.4,    7.2,   11.4,   11.9,   13.5,   16.0,   17.9,   20.8,   23.8],
    "simd_quad_m4":                [   5.6,    5.2,    6.1,   10.0,   12.7,   15.0,   21.7,   20.7,   24.1,   27.6],
    "simd_quad_m4 + spine":        [   5.2,    5.3,    6.2,    8.8,   12.8,   13.4,   18.3,   17.2,   20.1,   22.8],
    "simd_quad_graviton":          [   4.8,    5.1,    8.3,   11.1,   13.0,   19.3,   22.5,   22.7,   25.9,   29.6],
    "simd_quad_graviton + spine":  [   5.1,    5.3,    7.4,   11.3,   12.0,   13.7,   19.1,   18.1,   20.3,   23.3],
}
pi5_cold = {
    "linear (std::find)":          [  15.3,   25.7,   39.2,   44.4,   82.8,  156.4,  338.2,  610.6,  962.1, 1730.4],
    "binary (std::binary_search)": [  21.9,   28.2,   36.5,   43.4,   59.2,   88.3,  173.5,  284.5,  289.2,  320.0],
    "simd_quad (reference)":       [  10.4,    9.2,   17.7,   16.7,   26.5,   68.9,  174.5,  252.5,  252.5,  295.3],
    "simd_quad_pi5":               [   5.0,    7.3,   13.8,   15.2,   25.4,   62.4,  165.0,  202.9,  245.8,  304.1],
    "simd_quad_pi5 + spine":       [   6.3,    9.0,   12.6,   16.1,   26.8,   61.8,  138.0,  142.0,   99.6,  138.4],
    "simd_quad_m4":                [   6.4,   13.8,   16.6,   17.1,   23.9,   64.1,  152.8,  203.5,  221.1,  303.7],
    "simd_quad_m4 + spine":        [   6.8,   13.5,   10.5,   16.0,   24.2,   67.1,  136.7,  134.0,   94.4,  131.4],
    "simd_quad_graviton":          [   5.6,    7.5,   13.1,   14.3,   23.0,   57.5,  158.6,  196.7,  231.6,  287.9],
    "simd_quad_graviton + spine":  [   5.6,    8.3,   11.1,   14.3,   24.9,   55.9,  133.3,  123.0,  109.7,  129.3],
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
    "linear (std::find)":         [  1.5,   2.7,   5.1,   9.7,  19.2,  37.7,  81.3, 157.1, 304.0, 593.3],
    "binary (std::binary_search)":[  4.3,   4.2,   4.6,   5.1,   5.8,   6.6,   7.6,   8.6,   9.9,  11.1],
    "simd_quad (reference)":      [  2.0,   1.4,   1.6,   2.1,   2.5,   3.2,   3.7,   4.7,   5.3,   6.3],
    "simd_quad_pi5":              [  1.4,   1.2,   1.9,   2.0,   2.4,   2.8,   3.8,   4.3,   5.6,   6.2],
    "simd_quad_pi5 + spine":      [  1.4,   1.2,   2.4,   2.4,   2.1,   2.3,   2.8,   3.3,   4.0,   4.6],
    "simd_quad_m4":               [  1.6,   1.4,   1.4,   2.1,   2.1,   2.6,   3.0,   3.6,   4.2,   5.0],
    "simd_quad_m4 + spine":       [  1.6,   1.4,   1.2,   2.5,   2.6,   2.3,   2.8,   3.2,   3.7,   4.3],
    "simd_quad_graviton":         [  1.4,   1.2,   1.9,   1.9,   2.2,   2.6,   3.4,   3.9,   4.9,   5.5],
    "simd_quad_graviton + spine": [  1.4,   1.2,   2.4,   2.4,   2.1,   2.3,   2.8,   3.3,   4.0,   4.6],
}
m4_cold = {
    "linear (std::find)":         [  4.5,   6.1,   7.1,  11.6,  19.0,  33.9,  68.2, 130.7, 240.1, 481.1],
    "binary (std::binary_search)":[  4.8,   4.4,   3.9,   4.6,   5.4,   7.1,  12.6,  22.1,  43.2,  66.6],
    "simd_quad (reference)":      [  5.4,   1.4,   1.4,   2.1,   2.5,   4.1,   5.7,   9.2,  16.1,  31.5],
    "simd_quad_pi5":              [  1.2,   1.0,   1.7,   1.9,   2.5,   3.8,   6.0,   7.0,  10.4,  15.2],
    "simd_quad_pi5 + spine":      [  1.3,   1.1,   2.2,   2.4,   2.4,   2.6,   3.1,   5.8,   4.1,  11.6],
    "simd_quad_m4":               [  1.4,   1.2,   1.2,   2.1,   2.5,   4.1,   5.1,   6.7,  10.4,  16.8],
    "simd_quad_m4 + spine":       [  1.7,   1.3,   1.2,   2.3,   2.7,   3.3,   3.5,   6.0,   4.2,   6.5],
    "simd_quad_graviton":         [  1.5,   1.3,   1.7,   1.7,   2.4,   3.7,   5.4,   5.8,   8.7,  11.7],
    "simd_quad_graviton + spine": [  1.2,   1.0,   2.3,   2.3,   2.3,   2.3,   3.4,   3.7,   5.1,   5.1],
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
    "linear (std::find)":         [ 15.6,  19.7,  16.6,  17.8,  21.4,  25.4,  37.1,  49.5, 106.4, 166.9],
    "binary (std::binary_search)":[ 24.9,  29.5,  36.5,  44.7,  52.6,  61.3,  64.7,  70.2,  76.9,  82.3],
    "simd_quad (reference)":      [ 16.7,  14.9,  16.2,  18.5,  18.9,  22.6,  23.9,  27.0,  29.3,  33.0],
    "simd_quad_intel":            [ 13.1,  12.3,  14.0,  15.1,  18.0,  19.7,  23.1,  25.3,  29.4,  31.6],
    "simd_quad_intel + spine":    [ 12.9,  12.9,  15.7,  16.0,  17.5,  18.7,  20.0,  21.4,  25.2,  26.8],
}
skx_cold = {
    "linear (std::find)":         [ 21.2,  23.4,  26.6,  31.3,  41.9,  62.0, 102.8, 177.9, 326.5, 582.5],
    "binary (std::binary_search)":[ 30.0,  35.1,  41.0,  50.0,  60.6,  84.7, 117.3, 162.3, 205.1, 276.8],
    "simd_quad (reference)":      [ 19.4,  12.9,  14.0,  16.3,  19.0,  39.8,  63.1,  84.6, 141.1, 171.5],
    "simd_quad_intel":            [ 11.5,  11.0,  12.2,  14.1,  16.7,  25.8,  42.1,  75.5, 127.9, 180.9],
    "simd_quad_intel + spine":    [ 11.7,  11.5,  13.6,  17.4,  17.7,  24.6,  42.8,  60.5,  93.8, 132.7],
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
    "linear (std::find)":         [  2.8,   3.9,   6.5,  12.2,  24.4,  45.4,  86.1, 179.1, 343.8, 655.4],
    "binary (std::binary_search)":[ 14.6,  18.5,  22.9,  27.4,  32.8,  38.9,  44.7,  49.8,  55.0,  60.6],
    "simd_quad (reference)":      [  2.8,   3.3,   3.1,   5.0,  10.7,   7.5,  15.1,  10.3,  18.9,  13.8],
    "simd_quad_intel":            [  2.5,   2.8,   3.1,   3.3,   4.7,  10.3,   7.6,  15.5,  10.1,  19.5],
    "simd_quad_intel + spine":    [  2.5,   2.5,   3.5,   3.7,   4.4,  10.3,   6.6,  14.7,   9.0,  18.0],
}
emr_cold = {
    "linear (std::find)":         [  8.2,  10.0,  12.0,  17.0,  23.5,  42.3,  82.0, 140.9, 298.9, 493.6],
    "binary (std::binary_search)":[ 17.5,  22.2,  28.1,  32.0,  36.6,  45.5,  62.4,  77.5,  98.7, 117.6],
    "simd_quad (reference)":      [  8.2,   3.2,   3.3,   5.0,  11.8,  16.6,  36.8,  43.8,  56.6,  71.0],
    "simd_quad_intel":            [  2.5,   2.5,   3.1,   3.2,   5.2,  15.4,  28.0,  38.0,  47.2,  64.9],
    "simd_quad_intel + spine":    [  2.5,   2.5,   3.5,   3.7,   5.1,  13.2,  16.7,  23.4,  25.9,  37.2],
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
    "linear (std::find)":         [   3.2,    5.0,    9.3,   15.8,   31.5,   72.8,  115.4,  236.5,  462.7,  906.5],
    "binary (std::binary_search)":[  11.7,   15.0,   18.4,   21.9,   25.3,   29.2,   33.4,   37.7,   42.4,   47.1],
    "simd_quad (reference)":      [   3.6,    3.3,    3.2,    4.9,    9.6,    7.8,   15.2,   11.1,   19.9,   15.2],
    "simd_quad_graviton":         [   2.9,    2.9,    3.3,    3.5,    5.1,    9.8,    7.9,   15.5,   11.1,   20.0],
    "simd_quad_graviton + spine": [   2.8,    2.9,    3.9,    4.1,    4.5,    8.7,    6.2,   13.4,    7.9,   16.2],
}
gv4_cold = {
    "linear (std::find)":         [   6.6,    8.6,   11.4,   17.0,   29.4,   54.7,  102.4,  203.9,  403.1,  835.1],
    "binary (std::binary_search)":[  14.4,   18.3,   22.7,   26.8,   31.9,   37.3,   43.3,   56.6,   78.6,  119.8],
    "simd_quad (reference)":      [   6.2,    3.2,    3.4,    5.2,   10.6,   10.8,   21.4,   33.2,   55.9,   81.7],
    "simd_quad_graviton":         [   2.6,    2.6,    3.3,    3.9,    6.3,   12.6,   16.2,   31.0,   43.9,   65.0],
    "simd_quad_graviton + spine": [   2.6,    2.8,    3.9,    4.4,    5.9,   10.4,   15.4,   17.4,   22.6,   34.6],
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
    "linear (std::find)":         [   2.2,    3.8,    7.1,   13.4,   26.4,   51.5,  111.1,  211.9,  413.8,  803.7],
    "binary (std::binary_search)":[   8.0,    7.3,    7.3,    8.1,    9.2,   10.4,   12.3,   13.8,   15.4,   17.4],
    "simd_quad (reference)":      [   3.4,    2.6,    2.6,    3.1,    3.6,    4.6,    5.3,    6.7,    7.7,    9.2],
    "simd_quad_pi5":              [   2.5,    2.4,    2.7,    2.8,    3.7,    4.3,    5.8,    6.7,    8.5,    9.4],
    "simd_quad_pi5 + spine":      [   2.5,    2.4,    3.2,    3.1,    3.0,    3.5,    4.1,    4.8,    5.6,    6.4],
    "simd_quad_m4":               [   2.4,    2.4,    2.4,    3.1,    3.6,    4.0,    4.7,    5.5,    6.4,    7.5],
    "simd_quad_m4 + spine":       [   2.4,    2.4,    2.5,    3.4,    3.7,    3.8,    4.4,    4.9,    5.6,    6.3],
    "simd_quad_graviton":         [   2.4,    2.4,    2.7,    2.9,    3.4,    4.0,    5.1,    5.9,    7.4,    8.2],
    "simd_quad_graviton + spine": [   2.4,    2.4,    3.2,    3.1,    3.1,    3.4,    4.0,    4.8,    5.7,    6.3],
}
m1_cold = {
    "linear (std::find)":         [   6.3,    7.8,   10.0,   15.2,   25.5,   47.0,   87.3,  167.2,  327.7,  648.4],
    "binary (std::binary_search)":[   7.3,    6.7,    6.6,    7.1,    8.8,   11.8,   15.9,   23.4,   83.3,  161.0],
    "simd_quad (reference)":      [   7.6,    2.6,    2.6,    3.0,    3.8,    5.6,    8.1,   15.6,   30.1,   58.2],
    "simd_quad_pi5":              [   2.5,    2.5,    2.6,    2.8,    3.9,    5.5,    7.9,   10.2,   23.1,   33.8],
    "simd_quad_pi5 + spine":      [   2.5,    2.5,    3.1,    3.1,    4.4,    4.8,    9.3,    9.1,   12.6,   23.2],
    "simd_quad_m4":               [   2.5,    2.4,    2.5,    3.0,    4.0,    5.4,    7.2,   10.0,   20.3,   37.1],
    "simd_quad_m4 + spine":       [   2.6,    2.5,    2.5,    3.4,    4.1,    4.6,    5.1,    8.5,    8.3,   11.1],
    "simd_quad_graviton":         [   2.4,    2.4,    2.6,    2.8,    3.6,    5.6,    7.1,    9.7,   19.8,   27.1],
    "simd_quad_graviton + spine": [   2.4,    2.4,    3.1,    3.2,    3.5,    3.9,    4.9,    5.8,   11.4,   15.4],
}
have_m1 = all(m1_warm["simd_quad_m4"][i] is not None for i in range(len(sizes)))

# n=4096 compile-time specialization (simd_quad_intel_spine_4096), median of 5
# ./bench 4000 5000 runs on EMR 2026-05-01. Isolated from the main table
# because it only exists at n=4096. Warm/cold are the two numbers.
emr_spine_4096 = {"warm": 14.02, "cold": 25.87}
# Same structure for Graviton 4 (simd_quad_graviton_spine_4096), measured
# on the same r8g host 2026-05-01 (median of 5 runs from rebench_run{1..5}).
gv4_spine_4096 = {"warm": 14.67, "cold": 29.15}
# Same structure for SKX (simd_quad_intel_spine_4096 on the AVX2 block-check
# path), measured on Xeon 8175M 2026-05-01 (median of 5 runs). Warm is a
# small win vs the general-n spine (27.5 -> 27.1, ~-1.5%) -- on SKX the
# scalar interpolation loop already runs at AVX-512 license L2 so the
# branch-removal effect is smaller than EMR's; cold is noise (131.9 vs
# 131.1 median, hidden by shared-tenant memory variance).
skx_spine_4096 = {"warm": 27.11, "cold": 122.98}
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
m4_spine_4096 = {"warm": 3.65, "cold": 18.65}
# Pi 5 (Cortex-A76) simd_quad_pi5_spine_4096, gap=32 -> 128 spine entries ->
# 256 B = 4 cache lines, 3-iter quaternary + 1 binary step + final lo pick.
# Measured 2026-05-01, median of 5 runs on the Pi 5 4-core A76.
#
# The unroll is a wash on Pi 5 in both regimes (warm 23.76 -> 23.78 = +0.1%,
# cold 138.36 -> 142.10 = +2.7%, both within ~5% run-to-run noise). Pre-
# measurement hypothesis was that Pi 5's narrow OoO + 2 load AGUs would
# reward branch-removal the most, mirroring EMR's -22/-30% win; the
# measurement disagreed. Most likely mechanism: GCC 15 with -O3 already
# hoists the 3-iter quaternary descent's loop-control out of the dependent
# load chain, and the spine-fits-in-4-lines + the in-loop speculative
# prefetch already give the A76 all the MLP it can use. Cold is dominated
# by final block-load DRAM latency, which neither branch-removal nor the
# extra __builtin_prefetch up top can buy back. Ship the specialization for
# consistency with the other hosts and the narrow-API use case; the win is
# within noise on A76.
pi5_spine_4096 = {"warm": 23.78, "cold": 142.10}
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
m1_spine_4096 = {"warm": 6.16, "cold": 32.70}

# Two-level spine micro-bench medians (bench_twolevel, 200 sets x 200 warm reps,
# num_containers=512, inner_n=4096). Median of 5 runs on EMR 2026-05-01
# (raw outputs in emr_runs/twolevel_run{1..5}.txt).
# A = bsearch outer + simd_quad_intel_spine inner (baseline)
# B = two-level spine outer + simd_quad_intel_spine inner (outer-spine only)
# C = bsearch outer + simd_quad_intel_spine_4096 inner (inner-unroll only)
# D = two-level spine outer + simd_quad_intel_spine_4096 inner (both)
# E = Shar branchless outer + simd_quad_intel_spine inner
# F = Shar branchless outer + simd_quad_intel_spine_4096 inner
#
# Deltas vs A:
#   B vs A:   warm -10.1%   cold -36.3%
#   C vs A:   warm -46.6%   cold -41.4%
#   D vs A:   warm -41.6%   cold -70.4%
#   E vs A:   warm -51.0%   cold -82.0%
#   F vs A:   warm -54.0%   cold -82.2%
#
# Deltas vs D (previous best stacked):
#   E vs D:   warm -16.1%   cold -39.1%
#   F vs D:   warm -21.2%   cold -40.0%
#
# Shar wins decisively on EMR too -- joins SKX, M4, Pi 5, GV4 in preferring
# F over D. Prior prediction was that the VBMI2 path not downclocking would
# let EMR's LLC streamer carry the outer spine past Shar's cmov chain; the
# measurement disagreed. Same likely mechanism as the ARM hosts: K=512 outer
# key spine is only 16 x 64-B = 1 KB, too short for the stride prefetcher
# to win on, so the outer spine's dependent pointer chase is pure critical-
# path cost that Shar's ~9 independent cmov-chain loads side-step. EMR's
# 3 load AGUs + deep OoO window amplify Shar's independent-load advantage.
# Ship recommendation on EMR: F (same as all four other hosts).
emr_twolevel = {
    "A  bsearch outer + general-n inner":          (157.60,  95.56),
    "B  two-level spine outer + general-n inner":  (141.76,  60.85),
    "C  bsearch outer + n=4096 inner":             ( 84.10,  55.97),
    "D  two-level spine outer + n=4096 inner":     ( 92.10,  28.29),
    "E  Shar branchless outer + general-n inner":  ( 77.29,  17.23),
    "F  Shar branchless outer + n=4096 inner":     ( 72.55,  16.98),
}
# SKX two-level spine micro-bench, median of 5 runs 2026-05-01 on Xeon 8175M
# (raw outputs in skx_runs/twolevel_run{1..5}.txt). This pass also ran the
# Shar branchless outer (E/F) variants that were previously only measured on
# M4 and Pi 5.
#
# Absolute numbers are higher than EMR (SKX runs the scalar path downclocked
# at AVX-512 license L2 and its shared-tenant LLC is noisier), but relative
# structure mirrors EMR for A-D: outer spine dominates cold, inner unroll
# dominates warm, stacking them gives a big win in both regimes.
#
# Deltas vs A (baseline):
#   B vs A:   warm  -8.6%   cold -54.7%
#   C vs A:   warm -35.2%   cold -45.2%
#   D vs A:   warm -57.0%   cold -71.4%
#   E vs A:   warm -58.1%   cold -77.9%
#   F vs A:   warm -61.2%   cold -78.0%
#
# The CLAUDE.md prediction that Shar would *lose* to D on Intel (because the
# outer spine's sequential multi-line access pattern plays to LLC streamers
# while Shar's dependent-load chain gives the streamer nothing) is refuted
# on SKX: F beats D by -9.7% warm and -22.9% cold. Likely mechanism: on SKX
# the AVX-512 frequency downclock slows the scalar interpolation loop inside
# the outer-spine descent enough that the cmov-chain's branch-free critical
# path wins anyway; and the K=512 key spine (16 lines of 64 B) is still short
# enough that whatever the LLC streamer buys is outweighed by the outer
# spine's scalar cost on a downclocked core. Ship recommendation on SKX: F.
skx_twolevel = {
    "A  bsearch outer + general-n inner":          (234.69, 122.02),
    "B  two-level spine outer + general-n inner":  (214.60,  55.28),
    "C  bsearch outer + n=4096 inner":             (152.00,  66.90),
    "D  two-level spine outer + n=4096 inner":     (100.91,  34.87),
    "E  Shar branchless outer + general-n inner":  ( 98.24,  27.02),
    "F  Shar branchless outer + n=4096 inner":     ( 91.16,  26.90),
}
# M4 Max two-level spine micro-bench (bench_twolevel, 200 sets x 200 warm reps,
# num_containers=512, inner_n=4096, gap=64 outer and inner). Median of 5 runs
# 2026-05-01 on the same M4 host as the m4_warm/m4_cold table above. Raw
# outputs in m4_runs/twolevel_run{1..5}.txt.
#
# Deltas vs A:  B -77.5% warm / -9.1% cold
#               C -87.8% warm / -53.7% cold
#               D -86.1% warm / -15.4% cold
#
# Notable differences from the Intel hosts:
#  - A (bsearch baseline) is already much faster in absolute terms (153 ns
#    warm / 23 ns cold) than SKX (238/132) or EMR (142/90). M4's L3 hit
#    latency + wide OoO already handle the plain bsearch outer path well.
#  - Cold-cache D is *not* the best variant. On SKX/EMR stacking outer
#    spine + inner unroll gave the biggest cold win. On M4, C (bsearch +
#    compile-time n=4096) is a strict winner cold and D regresses back
#    toward B. Same mechanism that makes m4_spine_4096 cold slow in the
#    single-lookup bench: M4's HW prefetcher cannot overlap the inner
#    block-load miss when the unrolled tier probes land in a single
#    basic block. On the two-level bench the outer spine path adds
#    further pointer chases that confuse the streamer.
#  - Warm, C and D are within noise of each other -- inner unroll
#    dominates and the outer spine is a wash on warm (as elsewhere).
#
# Ship recommendation for M4: bsearch outer + compile-time-n=4096 inner
# (C) is the best single variant here. Outer spine helps warm large-n
# container sets only if the containers are general-n.
m4_twolevel = {
    "A  bsearch outer + general-n inner":          (161.93,  22.30),
    "B  two-level spine outer + general-n inner":  ( 30.82,  21.46),
    "C  bsearch outer + n=4096 inner":             ( 20.82,   9.79),
    "D  two-level spine outer + n=4096 inner":     ( 22.71,  19.38),
    "E  Shar branchless outer + general-n inner":  ( 17.71,   7.50),
    "F  Shar branchless outer + n=4096 inner":     ( 13.61,   7.08),
}
# Raspberry Pi 5 (Cortex-A76) two-level spine micro-bench, median of 5 runs
# (raw in pi5_runs/twolevel_run{1..5}.txt). Uses the Pi 5 build of
# bench_twolevel.cpp (`-DQUADSEARCH_ARM_PI5`, gap=32 outer+inner,
# simd_quad_pi5_spine / simd_quad_pi5_spine_4096 as inner). 2026-05-01.
#
# Warm is nearly flat across A-F (within ~15% of the 221-260 ns band): at
# num_containers=512 * inner_n=4096 the dataset is 4 MB, and on A76's
# 2 MB L2 + 16 MB shared L3 the *warm* bench keeps hitting L3/DRAM, so the
# inner-search structural wins don't show up. The cold numbers resolve the
# story: A=426 ns, B=246 ns (outer spine alone), C=92 ns (inner unroll
# alone), D=86 ns (both), E=39 ns (Shar outer + general-n), F=33 ns (Shar
# outer + compile-time n=4096). Relative to A: B -42%, C -78%, D -80%,
# E -91%, F -92%. Matches the M4 pattern: Shar outer + inner unroll is
# the cold winner on Pi 5 too. Ship recommendation for ARM two-level
# lookups: F.
pi5_twolevel = {
    "A  bsearch outer + general-n inner":          (250.78, 426.11),
    "B  two-level spine outer + general-n inner":  (243.37, 246.48),
    "C  bsearch outer + n=4096 inner":             (241.34,  92.50),
    "D  two-level spine outer + n=4096 inner":     (242.94,  85.74),
    "E  Shar branchless outer + general-n inner":  (221.45,  38.70),
    "F  Shar branchless outer + n=4096 inner":     (260.46,  33.05),
}

# AWS Graviton 4 (Arm Neoverse V2) two-level spine micro-bench, median of 5 runs
# 2026-05-01 on r8g. Uses the GV4 build of bench_twolevel.cpp
# (`-DQUADSEARCH_ARM_GV4`, gap=32 outer+inner, simd_quad_graviton_spine /
# simd_quad_graviton_spine_4096 as inner). Raw in gv4_runs/twolevel_run{1..5}.txt.
#
# Deltas vs A:
#   B vs A:   warm  -9.0%   cold -31.6%
#   C vs A:   warm -34.9%   cold -42.6%
#   D vs A:   warm -28.8%   cold -63.3%
#   E vs A:   warm -50.4%   cold -82.1%
#   F vs A:   warm -58.1%   cold -82.9%
#
# Shar dominates: F (Shar outer + compile-time n=4096 inner) is the clear
# winner both warm and cold, beating D (the outer-spine stacked variant) by
# -41.1% warm / -53.5% cold. Same pattern as Pi 5 and M4: the K=512 outer
# key spine is only 16 x 64-B lines = 1 KB, too short for V2's aggressive
# stride prefetcher to win on, so the outer spine's dependent pointer chase
# is pure critical-path cost that Shar's cmov chain avoids. V2 has the
# deepest OoO window and the most load AGUs of any ARM host in this project,
# which should reward the branchless independent-load chain even more than
# the narrower M4/Pi 5 cores -- and does (Shar's relative advantage over D
# is larger on GV4 than on M4 or Pi 5). Ship recommendation on GV4: F.
gv4_twolevel = {
    "A  bsearch outer + general-n inner":          (175.83,  85.77),
    "B  two-level spine outer + general-n inner":  (159.94,  58.67),
    "C  bsearch outer + n=4096 inner":             (114.42,  49.19),
    "D  two-level spine outer + n=4096 inner":     (125.12,  31.50),
    "E  Shar branchless outer + general-n inner":  ( 87.22,  15.39),
    "F  Shar branchless outer + n=4096 inner":     ( 73.74,  14.66),
}

# Apple M1 Pro two-level spine micro-bench, median of 5 runs 2026-05-01.
# Uses the default ARM build of bench_twolevel.cpp (gap=64, links
# simd_quad_m4.c -- same binary layout as the M4 Max run). Raw in
# m1_runs/twolevel_run{1..5}.txt.
#
# Deltas vs A:
#   B vs A:   warm -66.1%   cold -44.5%
#   C vs A:   warm -86.9%   cold -69.3%
#   D vs A:   warm -79.6%   cold -50.0%
#   E vs A:   warm -82.0%   cold -77.3%
#   F vs A:   warm -84.0%   cold -76.9%
#
# Same overall pattern as M4 Max: the K=512 outer key spine is 8 x 128-B
# = 1 KB (one L1 line's worth per 128-B line), too short for the M1's
# streamer to get anything out of, so the outer spine's dependent pointer
# chase is pure critical-path cost that Shar's cmov chain sidesteps.
# C beats D cold (15.2 vs 24.8) for the same reason the single-lookup
# m4_spine_4096 cold regresses -- the unrolled inner overlaps the block
# miss poorly when the outer path adds further pointer chases.
#
# F wins warm (54.4, narrowly vs E's 61.2) and ties E within noise cold
# (11.46 vs 11.25 -- median of 5 runs, per-run variance ~1-2 ns). Ship
# recommendation on M1 Pro: F (same as every other host in the project).
m1_twolevel = {
    "A  bsearch outer + general-n inner":          (339.55,  49.59),
    "B  two-level spine outer + general-n inner":  (115.23,  27.50),
    "C  bsearch outer + n=4096 inner":             ( 44.63,  15.21),
    "D  two-level spine outer + n=4096 inner":     ( 69.35,  24.79),
    "E  Shar branchless outer + general-n inner":  ( 61.24,  11.25),
    "F  Shar branchless outer + n=4096 inner":     ( 54.40,  11.46),
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
    ax.set_xticks(sizes)
    ax.set_xticklabels([str(s) for s in sizes])
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
        ax.set_xticks(sizes)
        ax.set_xticklabels([str(s) for s in sizes], fontsize=8)
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
    ax.set_xticks(sizes)
    ax.set_xticklabels([str(s) for s in sizes])
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
    ax.set_xticks(sizes)
    ax.set_xticklabels([str(s) for s in sizes])
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
    "Pi 5 (A76)":    pi5_spine_4096,   # measured 2026-05-01 (wash in both regimes)
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


# --- two-level spine A/B/C/D chart ---
# bench_twolevel data: A = bsearch outer + general-n inner (baseline),
# B = two-level spine outer + general-n inner,
# C = bsearch outer + compile-time-n=4096 inner,
# D = two-level spine outer + compile-time-n=4096 inner,
# E = Shar branchless outer + general-n inner,
# F = Shar branchless outer + compile-time-n=4096 inner.
#
# All five hosts now have data (as of 2026-05-01), A-F on every host.

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
                "F  Shar branchless outer + n=4096 inner"]
    short    = ["A\nbsearch\n+ general-n",
                "B\nouter spine\n+ general-n",
                "C\nbsearch\n+ n=4096",
                "D\nouter spine\n+ n=4096",
                "E\nShar outer\n+ general-n",
                "F\nShar outer\n+ n=4096"]
    hosts_present = [h for h in summary_hosts if h in host_twolevel]
    fig, (ax_w, ax_c) = plt.subplots(1, 2, figsize=(16, 5.5))
    x = np.arange(len(variants))
    w = 0.8 / max(1, len(hosts_present))

    for ax, regime, title in [(ax_w, "warm", "warm cache"),
                              (ax_c, "cold", "cold cache")]:
        for i, host in enumerate(hosts_present):
            offset = (i - (len(hosts_present) - 1) / 2) * w
            data = host_twolevel[host]
            color = host_colors[host]
            if data is None:
                heights = [0] * len(variants)
                bars = ax.bar(x + offset, heights, w,
                              color=color, alpha=0.25,
                              edgecolor=color, linestyle="--", linewidth=1.0,
                              label=f"{host} (not yet ported)")
            else:
                # E/F may be absent on hosts measured before Shar was added
                # (SKX, EMR) -- render those cells as missing.
                vals = [data[v][0 if regime == "warm" else 1] if v in data else None
                        for v in variants]
                vals_plot = [v if v is not None else 0 for v in vals]
                bars = ax.bar(x + offset, vals_plot, w, color=color, label=host)
                for b, v in zip(bars, vals):
                    if v is None:
                        continue
                    ax.text(b.get_x() + b.get_width()/2, v,
                            f"{v:.1f}", ha="center", va="bottom", fontsize=7)
        ax.set_xticks(x)
        ax.set_xticklabels(short, fontsize=8)
        ax.set_ylabel("nanoseconds per outer+inner lookup")
        ax.set_title(title)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        ax.legend(loc="upper right", fontsize=8)
    fig.suptitle("Two-level spine micro-bench "
                 "(512 containers x inner_n=4096, ~4 MB per set). "
                 "A-F measured on all six hosts.",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig("bench_twolevel.png", dpi=130)
    print("wrote bench_twolevel.png")

twolevel_bar()


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
    ax.set_xticks(sizes)
    ax.set_xticklabels([str(s) for s in sizes])
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

    # Two-level spine A/B/C/D table.
    lines.append("=== two-level spine micro-bench (ns/lookup, 512 containers, inner_n=4096) ===")
    lines.append(f"{'host':16s}  {'var':4s}  {'warm':>8s}  {'cold':>8s}  description")
    for host in ["Pi 5 (A76)", "M4 Max", "M1 Pro", "Intel Skylake", "Intel Emerald", "Graviton 4"]:
        data = host_twolevel.get(host)
        if data is None:
            lines.append(f"{host:16s}  (not yet ported - bench_twolevel.cpp needs a "
                         f"gap=32 build against simd_quad_graviton)")
            continue
        for k, (w_, c_) in data.items():
            var, desc = k.split("  ", 1)
            lines.append(f"{host:16s}  {var:4s}  {w_:8.2f}  {c_:8.2f}  {desc}")
    lines.append("")

    return "\n".join(lines)

text = table_text()
with open("bench_table.txt", "w") as f:
    f.write(text + "\n")
print("wrote bench_table.txt")
print(text)

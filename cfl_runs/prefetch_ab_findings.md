# Intel kernel A/B on Coffee Lake, 2026-10-13: the in-loop prefetch and the scalar tail

Host: the Intel Coffee Lake laptop (i9-9980HK, `cfl_runs/cfl_findings.md`), GCC
17.0.0 20260824, `-march=native` = skylake (AVX2 path of `simd_quad_intel.c`,
kernel blob 418fd3a8), every measurement at the 2.4 GHz base clock
(`intel_pstate` `no_turbo=1`, restored afterwards), pinned to CPU 15, the
laptop otherwise idle (greeter session only).

## 1. The plain kernel's in-loop prefetch, main bench (`rebench_flushed_pfab*`)

The shipped AVX2 path keeps one `_mm_prefetch` per quaternary-loop iteration
in the plain kernel `simd_quad_intel` (gated on `!__AVX512VBMI2__`; the spine
kernels prefetch only their spine line and are untouched). Variant `np` =
the shipped file with exactly that statement removed
(`cfl_runs/prefetch_ab_variant.diff`, one hunk; the binaries differ by one
`prefetcht0`). Two builds of `bench.cpp`, `./bench` (shipped) and `./bench_np`,
were run in interleaved pairs, run r of A then run r of B, each a full
flushed main-bench run (`4000 5000`, 512 MB flush before every cold pass,
`nA` aligned rows): pairs 1, 2 and 8-15, ten pairs, 09:00-10:44 local.
Pairs 3-7 lost their A run (a stale arm64 `bench` from the share was rsynced
over the x86 build mid-campaign; the header-only files were discarded and
pairs 11-15 run in their place; the five np runs 3-7 are archived unpaired).
Files `cfl_runs/rebench_flushed_pfab_run{1,2,8..15}.txt`,
`cfl_runs/rebench_flushed_pfab_np_run{1..15}.txt`, driver and campaign logs
`rebench_flushed_pfab_driver.log`, `rebench_flushed_pfab_campaign.log`;
paired analysis `cfl_runs/bench_ab_pfab_vs_pfab_np_paired.txt` from
`compute_bench_ab.py` (run r of A against run r of B, per cell and regime,
WIN = >= 8 of 10 pairs and |median| >= 3%), companions
`rebench_flushed_pfab{,_np}_paired.txt` (within-run plain-vs-aligned pairs of
each series).

Drift: whole-run B/A -0.5% warm in every pair (the identical-code cells'
geometric means agree to 0.03 ns in every pair; the -0.5% is the `intel`
columns), cold -3.9% to +2.9% per pair, median -0.3%; series max/min 1.00x
warm, 1.04-1.05x cold.

**What else differs (methodology lesson 7).** Two binaries: a recompiled
translation unit lays out every function afresh, so the cells the factor
cannot reach -- every column but `intel`/`intelA`, and those two below n = 128,
where the quaternary loop that holds the prefetch never iterates (num_blocks
<= 3) -- are identical-code gauges. On 215 gauge cells per regime the WIN rule
fired at 6.5% warm (14 cells, all unanimous 10/10, up to +7.0% at `intel`
n = 89 and +3.9% at n = 47, 9 of the 14 in the 32-127 band, at most 1.3%
from 512 up) and 7.0% cold (15 cells, none unanimous, up to 8.6% at `simd`
n = 512). So in this design a unanimous 10/10 sign on identical code is
ordinary below n = 128 (code placement), and an effect cell counts only where
its |median| clears the gauge's largest at the same size.

**Result: the prefetch is a loss in the AVX2 path, warm at every size from
333 up and cold wherever the sign is clear.**

| regime | effect cells (`intel`, `intelA`, n >= 128) | WIN(np) | WIN(shipped) | TIE |
|---|---|---|---|---|
| warm | 28 | 22 (every size from 333 up, both rows, 10/10 each; -3.6% to -7.5%, -1.0 to -2.5 ns; all 22 clear the gauge) | 0 | 6 (128-256: five at -0.5% to -2.2% with np faster 10/10, and 177 `intel` at 0.0%, equal in 8 of 10 pairs; all under 3%) |
| cold | 28 | 9 (333A -6.0%; 512 -11.1% / -4.2%; 1234 -12.2% / -18.1%; 2999 -4.1%; 3967A -3.1%; 4096 -10.4% / -10.9%; 8 of the 9 clear the gauge) | 0 | 19 (np faster by median at 16 of them) |

Per size, plain `intel` row, warm (shipped -> np, median of 10 pairs, ns):
333 27.7 -> 26.3, 512 26.1 -> 24.5, 617 33.5 -> 31.4, 1001 33.1 -> 31.0, 1024
28.1 -> 27.1, 1234 36.5 -> 34.7, 1777 33.3 -> 31.2, 2048 33.0 -> 30.8, 2999
39.8 -> 38.1, 3967 39.7 -> 38.0, 4096 36.1 -> 34.3 (-4% to -7%, 10/10 at every
one); cold: 512 82.6 -> 71.5, 1234 166 -> 143, 4096 220 -> 197 (10/10),
2999 221 -> 213 (10/10); the other cold cells tie with np ahead by median at
most of them (617 -8.2%, 7/10; 2048 +0.3%). The aligned `intelA` row agrees
cell for cell (warm -4.5% to -7.5%, cold 333 -6.0%, 1234 -18.1%, 4096 -10.9%).
The spine kernels (`intels`, `intel_spine_N`, the pad) are gauge cells here:
the compile-time `intel_spine_N` cells all tie, while `intels`, `intelsA` and
the pad carry 11 of the 14 warm and 8 of the 15 cold gauge WINs (`intels` 5
warm / 5 cold, `intelsA` 3 / 2, the pad 3 / 1; none above 7.1%).

**Reading.** The structural argument of the Pi 5 removal applies unchanged:
the prefetch targets the start of block `base + n/2` while the next probe
reads the end of a block, with an address that depends on the just-updated
`base`, i.e. at the dependency depth of the demand loads; on a Skylake core
it costs an issue slot and a line fill per iteration and buys nothing the
out-of-order window does not already get. This is the AVX2 path shared with
Skylake-SP, where the 2026-04 A/B was "inconclusive"; Coffee Lake is the same
core with a smaller L2 and a ring L3. Decision (taken after the two-level
kernel A/B below, G vs Gnp, the outer-hot regime): the line was removed from
the `!__AVX512VBMI2__` branch on 2026-10-13, as was done for the Pi 5.

## 2. Two-level kernel A/B (`sweep_abi1`): the prefetch in the outer-hot regime, and the scalar tail

`bench_ab_intel.cpp` (the Intel twin of `bench_ab_pi5.cpp`): Shar outer fixed,
six inner variants on the `sweep_fvl3` arrays and targets -- F = the shipped
general-n spine kernel, Ft = F with a vector tail, G = the shipped plain
kernel (in-loop prefetch kept), Gnp = G without the prefetch, Gt = G with the
vector tail, LemS = Lemire's 2026-04-27 kernel -- each kernel variant its own
translation unit written by `gen_intel_ab_variants.py` from `simd_quad_intel.c`
(blob 418fd3a8) by exact substitution (`cfl_runs/sweep_abi1_variants.diff`,
assembly in `cfl_runs/sweep_abi1_asm/`). 179 sizes x 4 modes x 10 runs =
7,160 cells, 100 sets x 200 reps, `order_seed` = run index, 10:50-14:38
local at the base clock, 0 failed; package 44-58 C, 45-49 C at 98% of the
cells (above 52 C only at the first cell and in run 5's cold_bat pass at
n = 32-40). Archive
`cfl_runs/sweep_abi1_raw.txt`, driver log `sweep_abi1_driver.log`, paired
analysis `cfl_runs/sweep_abi1_paired.txt` / `cfl_sweep_abi1_data.py`, figures
`bench_cfl_sweep_abi1{,_delta,_delta_ns}.png`. Run-level drift 1.00x in both
hot modes, 1.10x cold_bat (one run at 420 against 382-393), 1.04x cold_ser.
WIN = >= 8 of 10 runs and |median| >= 3%. Identical-code gauges: Gnp vs G
below n = 128 (the loop that holds the prefetch never iterates), and every
Ft/Gt contrast below 32 and at sizes with an empty tail (n % 32 == 0), where
the tail code is never reached: they fired at 0-3 cells per contrast and
mode (three in Ft vs F cold_ser: 7, 12, 64), 3-6%.

**The vector tail.** The shipped kernels finish a query that falls past the
last full block with a scalar sweep of the partial last block (up to 31
elements; GCC 17 compiles it as an alignment-peeled prologue of up to 15
compare-and-branch steps, a vpminuw/vpcmpeqw/vptest step for tails of about
23 or more, and an epilogue). The tail variant replaces it with one
membership test of the array's last 32 elements: two 256-bit loads at
`carr + n - 32` and `carr + n - 16`, cmpeq against the broadcast key, OR,
movemask (one zmm load under VBMI2). It is correct because the descent only
reaches the tail when the last full block's maximum is below the key, so the
window's extra elements cannot match (comment and exhaustive self-test in
the variant; 70.8 M targets per kernel at every n from 32 to 300 and at
4096). It acts only on queries that reach the tail -- (n mod 32)/n of the
hits, nothing at n % 32 == 0 -- so its effect is largest where the tail is
long and the array short:

| contrast | hot_bat / hot_ser WIN cells of 179 | where | ns per query (hot) | cold_bat |
|---|---|---|---|---|
| Ft vs F (spine kernel) | 26 / 24, no losses | 42-62 (-3% to -14%, 10/10), 81-95 (-3% to -8.5%), 120-124, 151-156, 184-190, 217 | -4.2 at 48-62, -3.5 at 81-95, -1.9 at 112-124, -1.6 at 210-217, -0.6 to 0 from 256 up | 23 WINs (45-62 -4% to -17%, 81-95 -4% to -10%; -39 ns at 48-62), one single-cell loss (1208, +4.3%, 9/10) |
| Gt vs G (plain kernel) | 24 / 24, no losses | the same bands (42-62 -3% to -14%, 81-95 -3% to -9%, 120-124, 184-190, 156) | -4.4, -3.8, -2.5, -1.4 | 23 WINs, no losses (-35 ns at 48-62, -22 at 81-95) |

It closes the hot-loss bands against Lemire's gap-16 kernel that the
`sweep_fvl3` campaign found: F vs LemS was WIN(LemS) at 81-95 (+6.3% to
+8.8%), 120-124 (+3.8% to +5.0%) and 217 in hot_bat (9 cells; 12 in hot_ser
with 112-124 and 210-217) and a tie at 49-62 in hot_bat (F still wins at 48,
-3.3%) and at 56-62 in hot_ser (F wins through 54); Ft vs LemS is WIN(Ft) at
48-62 (-8% to -13%, 10/10), a tie at 81-95 (+3.0% at 81 the only remaining
WIN(LemS) hot_bat cell, -0.2% to +2.6% elsewhere), a tie at 112-124 (-0.3%
to +1.1%) and at 210-217 (+0.9% to +1.2%), and WIN(Ft) at 130 of 179 sizes
in hot_bat and 131 in hot_ser against 119 / 123 for F (cold_bat 158 against
149, cold_ser 105 against 100). So on this core the spine inner with the
vector tail beats or ties Lemire's kernel hot at every size but one in
hot_bat (81) and two in hot_ser (64 and 81, +3.0% and +3.3%), and the
hot-loss bands were the scalar tail, not the block structure. Decision: the
Ice Lake-SP kernel A/B confirmed the zmm form (`icx_runs/icx_findings.md`,
kernel A/B section: the same bands, no effect loss), and the vector tail was
adopted into `simd_quad_intel.c` on 2026-10-17 in both forms, with a guard
that keeps the shipped behaviour for an empty tail; the same scalar tail
exists in the Pi 5, Graviton and M4 kernels and is an open A/B there (the
Pi 5 already beats Lemire at 48-62 hot, so the gain, if any, is cold).

**The prefetch in the outer-hot regime.** Gnp vs G (identical code below 128)
is a tie at 175 of 179 sizes in both hot modes (|median| <= 1.4% from 128 to
1023 and <= 2.8% from 1024 to 3589; by band +0.1 to -1.3 ns up to 2047 and
-2.2 / -2.1 ns at 2048-4096) and WIN(Gnp) at 3710-4096 (-3.4% to -4.9%, -4
to -6 ns, 9-10/10); cold it is WIN(Gnp) at 49 sizes in cold_bat (224-232,
345-380, 420-565, 645-667, 736-761, 840-868, 1131-1169, 2667-3251 and singles,
-4% to -18%; by band -10 ns at 128-255, -16 at 256-511, -22 at 512-1023, -19
at 1024-2047, -31 at 2048-4096) and at 26 in cold_ser (-3% to -8%; -6 to -15
ns by band from 256 up), with WIN(G) only at the gauge cells 53 (cold_bat) and
62 (cold_ser) and at one effect size, 151 cold_ser (+4.6%, 8/10, between ties
at 146 and 156). So in this harness the prefetch is a 10-31 ns cold_bat loss
from 128 up, a 6-15 ns cold_ser loss from 256 up, and never a hot gain --
unlike the Pi 5, where the same pair was 3-13% faster hot
from n ~ 667 (`sweep_ab1`). Together with section 1 (slower warm at every
main-bench size from 333 up, slower cold at 9 of 28 cells, never faster), the
AVX2 path's in-loop prefetch has no regime left: **removed from
`simd_quad_intel.c` on 2026-10-13** (the `!__AVX512VBMI2__` branch; the zmm
branch never had it). Skylake-SP shares this core and this path; its 2026-04
A/B was "inconclusive" at 5 runs and is superseded by the Coffee Lake pair of
campaigns (ten interleaved main-bench pairs and 7,160 two-level cells).

**Plain kernel vs spine inner (G vs F), for the record.** F is faster hot at
32-62 (+3.6% to +12%, 10/10: GCC inlines the delegated plain kernel into the
spine function and compiles its tail as an unrolled ymm sweep, so F's
"delegated" copy is not G's code) and from 323 up (+5% to +29%, +9 ns at
512-1023 to +18 ns at 2048-4096), a tie in between; cold_bat WIN(F) at 104
sizes (from 420 up +6% to +36%, +100 to +120 ns per query), cold_ser mixed
below 449 (G ahead at 146-210 and 302-406 by 3-6%) and WIN(F) at 62 of the
68 sizes from 449 up (+3% to +21%, +38 to +69 ns by band).

Levels at n = 4096 (median ns/query of 10 runs; F / Ft / G / Gnp / Gt /
LemS): see `cfl_runs/sweep_abi1_paired.txt`; Ft vs F and Gt vs G are ties
there (-0.0% / -0.2%, +0.5% / -0.1%), Gnp vs G -3.4% / -4.1% hot (10/10) and
Ft vs LemS -13.7% / -12.6% hot, -13.9% / -9.8% cold (10/10).

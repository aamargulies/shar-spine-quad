# Pi 5 layout experiment (campaigns `layout1` and `layout1pf`, 2026-10-13, second board "eight")

Question (open item 3): in the Pi 5 kernel A/B of 2026-10-12 (`sweep_ab1`,
`bench_ab_pi5.cpp`) the line-aligned copies of the container arrays and spines
(variant Fa) were 4-17 ns SLOWER hot than the std::vector originals at every
size from 32 up, and nothing above n = 256 explained it. Fa's copies differed
from the originals in four ways at once -- 64-byte alignment, heap position
(a second allocation pass after every set and target), footprint (sizes
rounded to the line, glibc's spacing of aligned chunks) and, where glibc
clusters the originals' spines away from their arrays, spine placement -- so
`bench_layout_pi5.cpp` separates them. Seven variants, all the SAME kernel
(one translation unit of `simd_quad_pi5.c`) behind the Shar outer, differing
only in where the inner arrays and spines live; every variant reads one
descriptor line (`struct Desc`); the lookup is one template instantiated seven
times; the sets and targets are the `sweep_fvl3` / `sweep_ab1` draw.

| variant | storage | isolates |
|---|---|---|
| F | the std::vector originals, first allocation pass | the reference |
| Fa | `aligned_alloc(64)` copies, second pass, sizes rounded to 64 | everything at once (the `sweep_ab1` Fa) |
| Fv2 | std::vector copies, second pass, each steered to the original's residue mod 64 (shim chunks) | position (glibc), spines adjacent |
| Fao | second-pass copies at residue 16, footprint-equal to Fa | alignment, with Fa's position and footprint |
| Fpool | one arena per set, copies packed at the originals' residues | position (arena), tightly packed, spines adjacent |
| Fapool | the same arena, every copy line-aligned and rounded | alignment inside the arena |
| Fmir | one arena per set holding F's layout offset for offset (residues, strides, holes, spine placement) | position only, layout preserved |

Campaigns on eight (core 3, `ondemand`, 44-58 C), 26 sizes 8..4096
(`pi5_runs/layout1_n_list.txt`), 4 modes, 10 runs with `order_seed` = run
index, 100 sets x 200 reps: `layout1` with the shipped prefetch-free kernel
(blob ad8d331e; 12:08-12:37, 1,040 cells, 0 failed, drift 1.04x hot / 1.01x
cold) and `layout1pf` with the pre-removal kernel (blob f7c140b8, the in-loop
prefetch kept; 12:45-13:14, 1,040 cells). Archives `pi5_runs/layout1_raw.txt`,
`pi5_runs/layout1pf_raw.txt`, driver logs, paired analyses
`pi5_runs/layout1_paired.txt` / `pi5_layout1_data.py` and the `layout1pf`
twins, figures `bench_pi5_layout1{,_delta,_delta_ns}.png` (and `layout1pf`),
the two campaigns differenced in `pi5_runs/layout1_vs_layout1pf.txt`. WIN = >=
8 of 10 runs agree and |median| >= 3%. Every copy is checked byte for byte; the
`# layout:` lines record each variant's residue histograms, page and line
footprint and spine distances (Fmir's residues, line counts, strides and spine
distances equal F's at 26 of 26 sizes, its page count is 1-48% higher because
each set has its own arena where F's sets share pages; Fv2's and Fpool's
residues equal F's copy by copy).

## 1. Alignment is a hot GAIN of 5-17 ns per query from 32 to 1024, not a cost

The two clean alignment contrasts agree in both campaigns (ns = median over
the band's sizes of the per-size median paired delta; `layout1`):

| contrast | 32-127 hot_bat / hot_ser | 128-511 | 512-1023 | 1024-2048 | 2049-4096 |
|---|---|---|---|---|---|
| Fao vs Fa (misaligned copies vs aligned, same position and footprint) | +16.3 / +14.6 ns | +9.1 / +12.3 | +8.1 / +7.9 | +8.7 / +9.7 | +2.6 / +2.7 |
| Fapool vs Fpool (aligned arena vs residue-exact arena) | -15.7 / -17.0 ns | -5.3 / -8.8 | -9.1 / -10.1 | -5.3 / -4.8 | -3.3 / -3.1 |

Fao is slower than Fa at 18 of 26 sizes in hot_bat (32-40 +21% to +31%,
56-160 +5% to +23%, 224-1024 +3% to +23%, 8-10/10) and 17 in hot_ser; Fapool
is faster than Fpool at 18 of 26 (16-112 -6% to -25%, 256-1024 -5% to -20%).
Cold the clean contrasts are ties below 512 and worth one line at the top:
Fao vs Fa +74 ns cold_bat at 2049-4096 (3072-4096 +3% to +10%, 10/10) and
+49 cold_ser; Fapool vs Fpool -66 / -48 ns there (-4% to -7%), -24 / -19 at
512-1023. So on the A76, in the outer-hot inner-first-touch regime, a
line-aligned block saves 5-17 ns per query at 1-32 blocks (one line instead of
two for the block check and the spine descent's probes) and 3 ns at 128
blocks, and cold it saves 48-74 ns per query at 3072-4096 (the fifth spine
line and the second block line; 32-114 ns by size), 18-27 ns in cold_bat at
512-2048 (Fao vs Fa +18 / +27, Fapool vs Fpool -24 / -24 ns by band; WIN at
512 and 1024) and nothing measurable below 512.

**The `sweep_ab1` Fa penalty does not reproduce.** Fa vs F itself is FASTER
hot here: -15.4 / -13.5 ns at 32-127, -6.6 / -8.1 at 128-511, -7.5 / -8.5 at
512-1023, -4.5 / -6.3 at 1024-2048, -2.9 / -2.9 at 2049-4096 (WIN(Fa) at 14 of
26 sizes in each hot mode; WIN(F) only at n = 8 and 24 in hot_bat (+13% to
+25%) and at 8-24 in hot_ser (+9% to +33%), the footprint of one-line copies of
16-48-byte arrays), and the prefetch-kernel repeat gives the same (-13.8 /
-8.8, -4.7 / -9.9, -7.3 / -7.2, -4.9 / -7.9, -2.7 / -3.1 ns; the two campaigns
agree on 726 of 832 verdicts, 105 WIN<->TIE flips, one opposite winner, Fmir vs
Fpool cold_bat at 4096; F's own levels differ by at most 6% between the two
kernels from n = 16 up and by 26% at n = 8 hot_ser, a bimodal cell whose runs
sit at 40-43 or 71-81 ns). What differs from `sweep_ab1` is the harness, not
the kernel: in
`bench_ab_pi5.cpp` five of the six variants (F, Fcr, Fd1, G, Gnp) read the
plain arrays and only Fa its copies, so in every shuffled pass the plain
arrays had been touched one or two passes earlier and Fa's copies six passes
earlier -- a carry-over asymmetry in the "hot" modes (which are first-touch
only within a pass), worth 4-17 ns against Fa. In `bench_layout_pi5` every
variant has its own storage and the staleness is equal (the two-level twins
campaign of the same morning, 10 plain readers against 6 twins, sits between
the two: Fa vs F -1.3% / -1.0%, `pi5_runs/twolevel_aligned_findings.md`).
Methodology lesson: in a multi-variant hot pass, variants that share storage
refresh it for each other; give every variant its own copy or thrash before
every variant.

## 2. Position: fresh pages cost 20-40 ns per query cold, at every size

Fmir mirrors F's layout offset for offset into a fresh arena, so Fmir vs F is
position alone: hot it is a tie from 128 up (within 2 ns) and 5-7 ns FASTER at
8-112 (WIN(Fmir) at 8-32 and 48-96 hot_bat, -5% to -13%); cold it is slower
everywhere -- cold_bat +42 ns at 8-24, +31 at 32-127, +24 at 128-511, +19,
+24, +31 at 2049-4096 (WIN(F) at 15 of 26 sizes); cold_ser +37, +72, +31,
+19, +24, +18 (WIN(F) at 16-256, 15 sizes, +3% to +15%, 9-10/10). Fv2 and
Fpool, position with spines adjacent, show the same cold cost below 512 (+24
/ +47 and +28 / +64 ns at 32-127) and a tie hot except at 8-24 (WIN(F) in six
of the twelve cells, +4% to +14%) and in Fv2 hot_bat at 320 (+3%). The cost
is about one DRAM
access per query and does not depend on n: the inner arrays' pages differ
but their contents' layout does not, so the candidate is the page walk --
after the 512 MB flush the page-table lines are cold too, and F's arrays were
allocated interleaved with the sets' keys, targets and descriptors (one
first-pass heap region, their page-table entries sharing lines), while every
copy variant lives in a region of its own whose page-table lines nothing
else touches. Untested; a `perf`-less board cannot count walks, and the
experiment that would settle it (copies interleaved with the descriptors) is
not built. For a Roaring integration the point is moot -- containers are
allocated once, in one layout -- but for this harness family it means that
any copy-based variant carries a +20-40 ns cold handicap that is not the
factor under test (methodology lesson 7 again; the within-arena contrasts
Fapool vs Fpool and the second-pass contrast Fao vs Fa are free of it).

## 3. Spine placement: F's clustered spines cost 40-65 ns cold at n >= 1024

At the 7 sizes 320, 512, 1024, 1536, 2048, 3072 and 4096 glibc hands F's
spines out from freed generator slots far from their arrays (about 30 spines
per 8 KB slot, 22-366 KB before the array; the layout lines' spine_dist);
every copy variant but Fmir puts each spine right after its array. Fmir vs
Fpool (F's placement against tight packing at the same residues) is the
contrast: cold_ser +65 ns at 1024-2048 and +39 at 2049-4096 (WIN(Fpool) at
1024-4096, +3% to +8%), cold_bat +18 and +33, i.e. a spine on its own page
costs a second page walk per query cold; hot the clustered layout is 5-12 ns
FASTER at 16-112 (WIN(Fmir) at 10-11 of 26 sizes) and a tie from 128 up.
Hence Fa, Fv2 and Fpool all turn from slower-cold to faster-cold than F at
1024-4096 (Fa vs F cold_ser -46 and -48 ns, -4% to -5%, 8-10/10; Fv2 -36 /
-20; Fpool -43 / -21): their adjacent spines beat F's far-away ones by more
than the fresh-page handicap. For an integration: keep a container's spine
next to its array.

## 4. Footprint below one block

At n = 8-24 the aligned glibc copies are the variants slower hot than F by the
widest margin (Fa vs F +9% to +33%, WIN(F) in five of six hot cells, Fao the
same; Fv2 and Fpool trail F by 4-5% in five cells and Fpool by 14% at n = 16
hot_ser), because a line-aligned copy of a 16-48-byte array occupies a whole
line and glibc spaces consecutive 64-byte-aligned chunks 128 B apart; Fapool,
line-aligned but packed in an arena, is 22-28% FASTER than Fa there and 11-14
ns faster than Fpool at 16-24 (the arena's alignment without glibc's spacing);
at n = 8 it is 2-4 ns slower than Fpool (+3.4% / +7.8%, the hot_ser cell a
WIN(Fpool) at 9/10). The `sweep_ab1` reading stands: never pad tiny containers
to a line; align containers of a block or more.

## 5. Summary and what changes

- Alignment on the A76: 5-17 ns by band (3-31% per size) faster hot at
  32-1024, 3 ns (1%) at 4096, 48-74 ns faster cold at 3072-4096 and 18-27 ns
  in cold_bat at 512-2048, nothing cold below 512, footprint cost below one
  block. The `sweep_ab1` "4-17 ns slower hot" was the kernel A/B
  harness's carry-over asymmetry; the two-level twins' "tie hot" has the
  smaller asymmetry of 10 against 6 readers.
- Position (fresh pages): +18-42 ns cold per query by band for the
  position-only mirror at every size (+72 in cold_ser at 32-127) and +18-64 ns
  for Fv2 and Fpool at 32-511; a harness effect to design around, not a
  kernel fact.
- Spine placement: a spine on its own page costs 40-65 ns cold at n >= 1024;
  allocate the spine next to its array.
- The in-loop prefetch of the pre-removal kernel changes none of this.

Levels (per-cell medians of the 10 runs, `layout1`, F / Fa / Fapool, for the
record only): n = 32 hot_bat 95.4 / 83.6 / 70.4, cold_ser 671 / 744 / 739;
n = 1024 hot_bat 181.2 / 174.6 / 167.2, cold_ser 957 / 914 / 913; n = 4096
hot_bat 205.4 / 202.6 / 201.9, cold_bat 1127 / 1096 / 1062, cold_ser 1157 /
1098 / 1077.

# Two-level harness, aligned twins (campaign `twolevel_v2_aligned`, 2026-10-13, second Pi 5 board "eight")

Ten runs of `bench_twolevel` built with `-DQUADSEARCH_ARM_PI5
-DQUADSEARCH_DESCRIPTOR_ALIGN=64 -DQUADSEARCH_TWOLEVEL_ALIGNED=64` (GCC 17.0.0
20260704 on trixie; run on eight, core 3, `ondemand`, 46-54 C), 200 sets x 200
reps, `order_seed` = run index, 10:49-11:03 local, ~82 s per run. Files
`pi5_runs/twolevel_v2_aligned_run{1..10}.txt`, driver log
`pi5_runs/twolevel_v2_aligned_driver.log`, paired analysis
`pi5_runs/twolevel_paired_v2_aligned.txt` (`compute_twolevel_paired.py pi5 --glob
'pi5_runs/twolevel_v2_aligned_run*.txt'`).

The build adds six twin variants Aa..Fa = A..F with the inner kernel reading
64-byte-aligned copies of every container array (8192 B) and spine (256 B),
made in a second pass after all sets and targets exist and checked byte for
byte; the plain variants keep the harness's `std::vector` storage (the
`# layout:` line: plain arrays at residues 0/16/32/48 mod 64 in the proportions
24916/26347/24929/26208 of 102,400 arrays, spines 26239/24979/26234/24948;
copies 204,800/0/0/0). Descriptors are one line (64 B, line-aligned) in both
rows, so the only read that differs between Xa and X is the array block and
the spine. Correctness: every twin agrees with A on every target of every set.
Run-level drift 1.02x hot_bat, 1.01x hot_ser, 1.03x cold_bat, 1.03x cold_ser.

## Result: alignment is a tie hot and worth 0-5% cold at n = 4096

Paired per-run deltas Xa vs X (negative = aligned faster; k/10 = runs in which
the twin was faster; WIN = >= 8/10 and |median| >= 3%):

| pair | hot_bat | hot_ser | cold_bat | cold_ser |
|---|---|---|---|---|
| Aa vs A (bsearch outer, general-n spine) | +0.4% (5/10) TIE | +0.3% (2/10) TIE | -1.4% (9/10) TIE | -0.3% (6/10) TIE |
| Ba vs B (outer spine, general-n spine) | -0.0% (5/10) TIE | -0.1% (6/10) TIE | **-3.4% (10/10) WIN** | -2.9% (10/10) TIE |
| Ca vs C (bsearch outer, compile-time inner) | -1.6% (9/10) TIE | -2.1% (10/10) TIE | **-4.7% (10/10) WIN** | -2.5% (10/10) TIE |
| Da vs D (outer spine, compile-time inner) | **-3.3% (10/10) WIN** | -1.8% (9/10) TIE | **-3.1% (10/10) WIN** | **-3.4% (10/10) WIN** |
| Ea vs E (Shar outer, general-n spine) | +0.3% (5/10) TIE | +0.2% (4/10) TIE | -1.6% (9/10) TIE | -1.1% (9/10) TIE |
| Fa vs F (Shar outer, compile-time inner) | -1.3% (9/10) TIE | -1.0% (10/10) TIE | -0.7% (8/10) TIE | -1.8% (8/10) TIE |

- **Hot (outer-hot, inner first-touch, DRAM on the Pi 5): no cost and no
  gain.** Every pair is within +-2.1% except Da vs D hot_bat (-3.3%, 10/10).
  The +4-17 ns hot penalty of the kernel A/B's aligned variant (`sweep_ab1`
  Fa vs F, +3.3% / +4.0% at n = 4096, 8/10) does not reproduce in this
  harness: Fa vs F here is -1.3% / -1.0% (9-10/10 the other way). The two
  harnesses differ in how the plain arrays and spines were laid out by the
  allocator (bench_ab_pi5 draws its sets with the sweep generator, whose
  freed 8 KB bitmap slots take in the arrays and cluster the spines; this
  harness allocates arrays and spines as it builds each set), in the number
  of sets (100 vs 200) and in the outer miss rate -- the layout experiment
  (`bench_layout_pi5`, campaign `layout1`) is the controlled test of that
  penalty.
- **Cold: the compile-time inner behind the bsearch or spine outer gains
  2.5-4.7%, behind Shar (F) 0.7-1.8%, the general-n spine 0.3-3.4%.** The
  aligned copies turn the 8 KB array's 128 blocks into one line each and the
  256 B spine into four lines instead of five; the compile-time `_spine_4096`
  descent reads the whole spine (3 quat iterations + 2-probe finish) and the
  block, so the fifth line is the whole saving (-2.5% to -4.7%, 10/10 for C
  and D; C's cold_ser cell is a TIE at -2.5%). The general-n kernel's
  shorter descent gains less (B -3.4% / -2.9%, A and E -0.3% to -1.6%), and
  F, the compile-time inner behind the Shar outer, is a tie (-0.7% / -1.8%,
  8/10). This is the same magnitude as the kernel A/B at
  n = 4096 (Fa vs F -2.6% / -3.1%), far below the main bench's 16-37% (a
  sequential cold sweep where the aligned copies' regular layout also streams
  better) and Coffee Lake's 26-40% (a 16 MB L3 host).
- **Ranks are unchanged by the twins.** D / Da lead every mode but hot_ser
  (Fa by rank, with B, D, E, F, Ba, Da, Ea within 2.6%): Da beats every plain
  variant in hot_bat (D +3.4%, F +3.6%, B +3.0%, E +4.4%, 9-10/10), cold_bat
  (D +3.2%, C +12.2%, F +33.8%) and cold_ser (D +3.5%, C +12.4%, F +24.2%).
  The plain-variant pairs reproduce the repaired-harness campaign of
  2026-10-11 by sign: F vs D tie hot (+0.1% / -1.3%) and D's win cold (+29.3%
  / +19.4% for F, 0/10); F vs Lem -37.1% / -39.2% / -21.3% / -19.3%
  (10/10); I vs F +7.0% / +10.1% / +3.6% / +12.9% (0-2/10); G vs F +66% /
  +68% / +28% / +40%.

## What else differs between Xa and X (methodology lesson 7)

1. Placement: the copies live in a second-pass heap region above every plain
   array and target (at 200 sets about 870 MB higher), allocated array, spine,
   array, spine, so each spine sits 8256 B after its array and consecutive
   containers' block-k lines are 8576 B apart (glibc's spacing for an aligned
   8192-byte plus an aligned 256-byte chunk: the Fa `# layout:` line of
   `layout1`, the same allocation sequence, at n = 4096; the twins' run files
   record no stride); the plain arrays follow the harness's set-building order
   with keys and targets interleaved. Alignment also removes page straddles
   (16 KB pages here).
2. The descriptor layout of this campaign is one line (`-DQUADSEARCH_DESCRIPTOR_ALIGN=64`),
   whereas the archived `twolevel_v2_run*.txt` used the 48-byte, 16-byte-
   aligned descriptor; the plain variants' levels here are therefore not
   cell-for-cell those of the 2026-10-11 campaign (compare by sign and band).
3. Carry-over between variants in the hot passes: ten variants read the
   plain layout and six the copies, so a twin finds a same-layout
   predecessor's lines in cache less often; on the Pi 5 the pass footprint
   (~8 MB) exceeds the 2 MB L2 + 2 MB L3, so inner loads miss either way and
   the asymmetry is moot here. It matters on Apple / EMR / GV4 / Coffee Lake,
   where a twins campaign should thrash before every hot variant or alternate
   plain and twin variants in the order.
4. The untimed warm-up runs A and then Fa, so both layouts get one first touch
   before the timed passes.

Levels (per-cell medians of the 10 runs, ns/query, for the record only; never
difference them across variants): hot_bat D 212.1, Da 205.1, F 212.6, Fa 209.0;
hot_ser D 212.5, Da 208.6, F 209.8, Fa 207.1; cold_bat D 677, Da 655, F 878,
Fa 872; cold_ser D 768, Da 740, F 917, Fa 904.

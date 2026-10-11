# Khuong & Morin (2017), "Array Layouts for Comparison-Based Searching" — speculation for QuadSearch

*Paper: Paul-Virak Khuong and Pat Morin, "Array Layouts for Comparison-Based Searching", arXiv:1509.05053, <https://arxiv.org/abs/1509.05053> (v2, 15 March 2017); published in ACM Journal of Experimental Algorithmics 22 (2017), pp. 1–39, <https://doi.org/10.1145/3053370>. The notes below were written from the authors' 49-page PDF dated 14 March 2017, which this repository redistributed until 2026-10-11 and now only cites (see `THIRD_PARTY_NOTICES.md`); section, figure and listing numbers follow that version.*

> **Correction banner (2026-10-11).** Every H/I measurement in the 2026-05-18 sections of this file was taken with a mis-aimed prefetch. `bench_twolevel.cpp` implemented Khuong & Morin's Listing 6 with `kPrefOff = 3*kGap/2 − 1`, the constant for the paper's **0-based** Eytzinger layout (root `a[0]`, children `2i+1`/`2i+2`, descendants log₂(B) levels down at `[B·i + B − 1, B·i + 2B − 2]`). The harness tree is **1-based** (root at slot 1, children `2i`/`2i+1`, descendants at `[B·i, B·i + B − 1]`), so every prefetch landed in the descendant line of node `i+1` and never on the search path; the trailing pad (`kGap*16` slots) was also far too small, so about half of the ~9 prefetches per query left the ~2 KB allocation, by up to ~31 KB at gap 32 (~63 KB at gap 64). Fixed 2026-10-11 (`kPrefOff = kGap/2`, cache-line-aligned array, `kGap·(K+1)` pad); In the review's three-run A/B on this Pi 5 (`pi5_runs/eytz_offset_ab/`, 100 sets × 200 reps, 2026-10-10) the corrected, line-aligned prefetch (variant I4, masked) was faster than the shipped offset in every run: cold_bat -31% to -10%, cold_ser -51% to -21%, hot modes −1.5% to −6.2% (the gated variant I3: cold_bat -35% to -16%, cold_ser -55% to +3%); the shipped offset was slower than no prefetch at all in 5 of 6 cold cells (cold_bat +11% to +20%) and 4–7% slower hot (§1). The prefetch depth is log₂(B) levels — 5 at gap 32, 6 at gap 64 — not the "4-deep" of the paper's B = 16 case. Independently, every "X vs Y" percentage in the 2026-05-18 tables below is a ratio of per-cell medians (the blockquoted notes and the final section give paired per-run deltas) taken across runs that drift 1.4–2.2× on the Pi 5 as whole-run cell swings (§2; the max/min of each run's geometric mean over all variants, a different statistic, is 1.5–1.6× there, §2.1) and up to 1.5× on the M4 Max; the paired per-run re-analysis of the same archived runs (`{host}_runs/twolevel_paired.txt`, produced by `compute_twolevel_paired.py`) reverses several of them, including this file's headline Pi 5 result. **Every table below is kept as history and should be read with the blockquoted correction notes that follow each retracted claim.** The Pi 5 has been re-measured with the repaired harness (ten runs, corrected prefetch: section "Repaired harness, 2026-10-11" at the end); the other five hosts have not. Section references (§) in the notes are to `Text/corrections_2026-10.md`, which is the source of truth where it and this file disagree.

Read the full 49 pages. Speculation on what the paper has to say to this project, in rough order of "actionable for QuadSearch" → "validates a decision already made":

**1. The K=512 outer is the most promising place to apply the paper's main result.**
Their headline finding: for n that overflows L2, branch-free Eytzinger with 4-deep `__builtin_prefetch(a + B*i + offset)` beats every other layout — because speculative execution + explicit prefetch acts as runahead, keeping ~4 cache lines in flight at all times. The QuadSearch finding "K=512 outer spine is only 1 KB, too short for any stride prefetcher — pointer chase is pure critical-path cost" is *exactly* the situation their explicit prefetch was designed for. Shar's 9-deep cmov chain on the sorted-order outer is what they call "branch-free without prefetching" — fast hot, but on narrow-OoO hosts (SKX, Pi 5) cold-loses because there's no streamer to feed it. Their trick: lay the outer out in Eytzinger order, prefetch `a[multiplier*i + offset]` at the top of every iteration, multiplier=cache-line-width-in-elements. For K=512 that's 9 cmov iterations issuing 9 prefetches whose latencies overlap. This is a real new variant — neither C, D, F, nor Lem implements it — and it's the straightest path I see to the open "narrow-OoO cold reversal" pattern.

> **Correction (2026-10-11):** "4-deep" is the paper's B = 16 case (4-byte keys, 64-byte lines). The prefetch targets the descendant block log₂(B) levels down: 5 levels at gap 32 and 6 at gap 64 for this project's u16 keys. For the K=512 outer (full tree levels at depths 0–8; depth 9 holds only slot 512) only the first 9 − log₂(B) prefetches of the descent land on full tree levels: 4 at gap 32, 3 at gap 64, plus one more on the all-left path, whose block contains slot 512; the rest land in the zero pad. (The comment above `find_container_eytz_pf` in `bench_twolevel.cpp` counts that partial depth-9 level as a real level and therefore says 10 − log₂(kGap) = 5 / 4.) "Shar ... on narrow-OoO hosts (SKX, Pi 5) cold-loses" should be read against the paired F-vs-D table (§2.2; paired, 5 runs, `{host}_runs/twolevel_paired.txt`): F loses `cold_bat` on the Pi 5 (+31.8%, D faster 5/5) and SKX (+6.6%, D faster 4/5), and loses `cold_ser` on SKX (+16.9%, 5/5), EMR (+17.7%, 5/5) and M4 Max (+16.2%, 4/5); `cold_ser` is a tie on the Pi 5 (−0.4%), M1 Pro (+5.7%) and GV4 (+1.2%). Shar's outer is a serial load → compare → csel → load chain, not loads issued in parallel (§5).

**2. The hybrid n=4096 inner is structurally what they call a Btree node with B=16 (their figure 15-17).**
Their independent finding "B=16 is optimal both in theory and practice for 4-byte data, log₂17 ≈ 4.09 fewer misses" lines up with QuadSearch's gap=32 (= 64 B / 2 B per u16 = a single cache line, ~32 comparisons via SIMD per node) and gap=64 on Apple silicon (128 B line). The QuadSearch design *is* a shallow custom Btree with SIMD-vectorized inner node search and a one-level top directory (the spine). Validates the architectural decision; nothing new to try, but worth knowing the paper agrees on the gap-tracks-cache-line conclusion from a completely different angle.

**3. Their Listing 6 prefetch (`multiplier*i + offset`) is structurally identical to the Pi 5 / SKX speculative `__builtin_prefetch` in the quat loop.** The QuadSearch finding "narrow OoO + 2 AGUs benefits from kept prefetch; wide OoO + good streamers does not" is the per-uarch generalization of their single-machine result. Their model in §4 ("max{L,c} log_B n when WL > log B") explains *why* it stops helping on EMR/M4/GV4: bandwidth W is high enough that the streamer alone saturates the load pipeline, and adding software prefetches contends rather than helps. Same conclusion the project reached empirically. The 4-way pfC failure on M1 (cold +21.6%) is exactly their "t=2 saturates bandwidth" prediction — their model would have predicted the failure.

> **Correction (2026-10-11):** The premise that the Pi 5 kernel "benefits from kept prefetch" is retracted. `simd_quad_graviton.c` is the Pi 5 kernel minus that one in-loop prefetch, so the archived Pi 5 main-bench table is a built-in A/B: the prefetch kernel is slower cold at 13 of 14 sizes from n = 128 up (+2% to +31%) and slower warm at 13 of 14 (`plot.py` pi5 dicts, pi5 vs graviton columns; per-run pairs in `pi5_runs/rebench_run*.txt` agree), and fresh interleaved A/Bs in the 2026-10 review agreed (1–6% slower at n = 4096, 17–20% slower at n = 2048; only n = 1024 favoured the prefetch) (§5). The SKX half of the premise is void too: the shipped gated build executes no zmm instruction, so nothing is downclocked (§5). The reading of §4's "WL > log B" as a contention regime, and the "t=2 saturates bandwidth" analogy for the M1 pfC experiment, are retracted with the H/I numbers they were built on (§1): pfC issued four same-depth candidate lines of which three are wasted by construction, which is not the paper's t.

**4. Lesson 3 (mixed Eytzinger top + sorted-block leaves ≈ branch-free Eytzinger with prefetching) gives a ceiling for the two-level harness.** Their mixed layout never beats prefetched Eytzinger — only matches it. Translation: any K=512 outer approach is bounded by what a well-prefetched Eytzinger outer can do. So if (1) above doesn't beat Shar+F on the wide-OoO hosts, the paper says no other top-level approach will either. Useful as a "stop-here" criterion.

**5. Lesson 5 (vEB is not useful for in-memory) closes off a tempting direction.** If anyone ever proposes recursive layout for the 4096 inner block, the paper directly disproves it — vEB's odd subtree sizes guarantee 2× cache lines per subtree vs. a Btree, which kills it.

**6. Branchy-beats-branchfree-at-huge-n result (Fig 7) doesn't apply here.** Their crossover is at n ≈ 2²², far above QuadSearch's 4096 ceiling. At Roaring container sizes everything is in cache or one cold line away, not 2 GB-deep. Worth mentioning only because it explains why their conclusion is "Eytzinger+prefetch ⊕ branch-free sorted for small n" rather than "always Eytzinger" — and why QuadSearch operates entirely in the small-n regime where their Lesson 1+2 (branch-free + prefetch) applies cleanly.

**7. Apple-silicon spine_4096 cold floor (the closed open-item) lines up with their bandwidth model.** They quantify W ≈ 4.7 cache lines in flight on the 4790K and predict t=1 prefetch saturates it. M1 Pro's load pipeline is wider but the *demand line* (carr) can't issue until lo resolves, so the contention regime kicks in at smaller t. The paper's framework reproduces the project's empirical conclusion that no pre-lo prefetch can help — same closed answer, different derivation.

> **Correction (2026-10-11):** The "~25 ns" M1 Pro cold floor is an SLC/L3-hit latency, not a DRAM round trip, and the Apple `_spine_4096` "structural cold regression" may itself be a measurement-order artifact of `bench.cpp` (the spine kernel's cold pass re-touches lines the previous kernel's cold pass just loaded — an L2 hit — while the dedicated `4096*` row runs after a 32 MB warm sweep). This is a hypothesis that needs a flushed A/B on Apple hardware (§5).

**Strongest single bet: try Eytzinger-laid-out outer spine with 4-deep explicit prefetch, on the four hosts where Shar reverses cold (SKX, Pi 5, EMR, M1 Pro).** It's a genuine third option neither the project nor Lemire's reference has tried, and the paper's mechanism is exactly the failure mode the project diagnosed independently. The other six points are mostly retroactive validation.

> **Correction (2026-10-11):** "4-deep" → log₂(B) levels (5 at gap 32, 6 at gap 64). The "four hosts where Shar reverses cold" set is not supported by the paired data: by F vs D (paired, 5 runs, `{host}_runs/twolevel_paired.txt`, table in §2.2) M1 Pro's `cold_ser` is a tie (+5.7%) and M4 Max *loses* `cold_ser` (+16.2%, D faster 4/5); the six-host "cold reversal" percentages this paragraph was written against came from 2026-05-13 runs that commit 5fdbb0a overwrote, and no raw file supports them (§2.3). Outcome of the bet after the harness fix: on the Pi 5 the corrected variant I never beats D in any mode (final section); the other five hosts are unmeasured with the fix.

---

## Results — H/I implementation, 2026-05-18

Implemented the strongest-single-bet on all six hosts as variants H (Eytzinger outer + 4-deep PF + general-n inner) and I (Eytzinger outer + 4-deep PF + n=4096 inner). Spec/plan in `~/.claude/plans/let-s-spec-the-work-iridescent-waterfall.md`. Paper's Listing 6 verbatim — `__builtin_prefetch(a + multiplier*i + offset)` with multiplier = cache-line-width-in-u16 (= `kGap`: 32 on 64-B-line hosts, 64 on 128-B-line hosts), offset = `(3*kGap/2) - 1`. Trailing pad on `keys_eytz` guards against OoB-prefetch portability hazard (paper §5.3). Index recovery via `i >> __builtin_ffs(~i)` (paper Listings 4-5) plus a BFS-slot-to-sorted-index inverse permutation (`eytz_to_sorted`) so the existing `s.containers[idx]` callsites still work.

> **Correction (2026-10-11):** Not Listing 6 verbatim. `offset = (3*kGap/2) - 1` is the paper's constant for its **0-based** layout (root `a[0]`, children `2i+1`/`2i+2`, descendants log₂(B) levels down at `[B·i + B − 1, B·i + 2B − 2]`); the harness tree is **1-based** (root at slot 1, children `2i`/`2i+1`, descendants at `[B·i, B·i + B − 1]`), so every prefetch landed in node `i+1`'s descendant line and never on the search path. The pad (`kGap*16` slots) covered about a thirty-second of the prefetch reach (512 pad slots against `kGap·512` = 16,384 slots at gap 32), so about half of the ~9 prefetches per query left the ~2 KB allocation, by up to ~31 KB at gap 32 (~63 KB at gap 64) — the §5.3 hazard the pad was meant to prevent. Fixed 2026-10-11 in `bench_twolevel.cpp`: `kPrefOff = kGap/2`, cache-line-aligned Eytzinger array, pad of `kGap·(K+1)` slots (§1). "4-deep PF" → the prefetch reaches log₂(kGap) levels down (5 at gap 32, 6 at gap 64). The pre-registered predictions scored in the per-host paragraphs below live in a private plans file outside the repository (`~/.claude/plans/...`) and were never copied into the tracked tree; they cannot be audited from this repository, so the "confirmation / falsification" labels are the author's own scoring (§5, "Provenance").

### M1 Pro 5-run medians (bench_twolevel 200 200 all, 5 runs, raw in `m1_runs/twolevel_run{1..5}.txt`)

|         | hot_bat | hot_ser   | cold_bat | cold_ser |
|---------|---------|-----------|----------|----------|
| F       |  45.88  |  79.26    |  278.54  |  776.46  |
| H vs F  | +50.2%  |  −6.2%    |  +38.4%  |  +6.5%   |
| I vs F  |  +4.0%  | **−19.8%** | +17.9%  | +12.0%   |

**Partial confirmation.** I wins `hot_ser` on M1 Pro by ~20% — the dep-chained critical-path mode where the prefetch-as-runahead trick should help most. Both cold modes regress for I, exactly as the paper's bandwidth-saturation model predicts: explicit prefetches contend with the demand block-load when streamers are already saturating the load pipeline (paper §4: `WL > log B` regime). Hot_bat is a tie.

> **Correction (2026-10-11):** Measured with the mis-aimed prefetch (§1), and the deltas above are ratios of per-cell medians. Paired per-run I vs F on M1 Pro (5 runs, `m1_runs/twolevel_paired.txt`): hot_bat −0.3% (tie), hot_ser **−10.9%** (I faster 4/5; per-run −5.2, −10.9, −15.5, −19.8, +22.3 — the published −19.8% is the single best run), cold_bat +17.9% (I slower 5/5), cold_ser +16.3% (I slower 5/5). The hot_ser result is the only hot_ser I win on the bench after pairing (GV4's hot_bat −10.8%, I faster 5/5, is the other pre-fix I win): suggestive (a sign test on five runs cannot reach p < 0.0625), not established, and it needs re-measurement with the fixed harness. The "bandwidth-saturation / `WL > log B`" explanation of the cold losses is retracted — it explained numbers produced by the offset bug — and variant I also pays one extra dependent load that F never pays (`eytz_to_sorted[i]`, then `keys[sorted_idx]`), which biases the cold I-vs-F comparison by about one memory round trip regardless of prefetch (§1).

H consistently underperforms I — adding the Eytzinger+PF outer to the slower general-n inner doesn't recover the inner-path overhead. Expected; F's signature win was always n=4096-inner-specific.

> **Correction (2026-10-11):** On M1 Pro this holds in the paired data except in `cold_ser` (H vs I: hot_bat +46.9%, I faster 4/5; hot_ser +19.4%, 4/5; cold_bat +15.7%, 5/5; cold_ser +1.1%, tie — `m1_runs/twolevel_paired.txt`). As the per-host refrain repeated below (and CLAUDE.md's "H underperforms I on all six hosts") it is mixed: hot, H and I tie on the Pi 5, and on GV4 H beats E (same general-n inner) 5/5 in hot_bat (−18.1%); cold, H is slower than I on every host (§2.3).

### GV4 5-run medians (bench_twolevel 200 200 all, 5 runs, raw in `gv4_runs/twolevel_run{1..5}.txt`)

|         | hot_bat   | hot_ser  | cold_bat | cold_ser |
|---------|-----------|----------|----------|----------|
| F       |  65.37    |  50.34   |  268.45  |  486.13  |
| H vs F  |  −1.0%    | +25.5%   |  +38.1%  |  +30.7%  |
| I vs F  | **−12.0%** | +16.0%  |  +15.9%  |  +27.5%  |

**Partial falsification of the GV4 prediction.** Pre-registered: "I loses on every mode — V2's 4 AGUs already give the Shar cmov chain the most headroom; nothing for software prefetch to add." Result: I loses 3/4 but **wins `hot_bat` by −12%**. The 4-AGU headroom isn't sufficient under batched dispatch — explicit Eytzinger prefetch still extracts a meaningful win there. The dep-chained `hot_ser` mode (where the prediction expected the *biggest* surprise on narrow-OoO hosts) is actually a clean F-win on GV4: 4 AGUs give Shar enough room to issue its 9-deep cmov chain in parallel with itself, leaving no critical-path stall for software prefetch to hide. Cold modes regress as expected.

> **Correction (2026-10-11):** Mis-aimed prefetch (§1). Paired per-run I vs F on GV4 (5 runs, `gv4_runs/twolevel_paired.txt`): hot_bat **−10.8%** (I faster 5/5 — the one robust pre-fix I win; needs re-measurement), hot_ser +16.4% (0/5), cold_bat +11.6% (0/5), cold_ser +28.1% (0/5). "V2's 4 AGUs": the 2026-10 review reported that Neoverse V2 has three load pipes, not four (not verified on hardware here; §5). "Cold modes regress as expected" explained bug-produced numbers, and F is not the GV4 cold reference anyway: C (bsearch outer + compile-time inner) beats F in both cold modes 5/5 (§2.1, §2.3).

H underperforms I across the board, same pattern as M1 Pro.

> **Correction (2026-10-11):** H vs I on GV4 does hold paired (hot_bat +12.7%, hot_ser +8.1%, cold_bat +21.6%, cold_ser +3.1%; H faster in at most 1/5 — `gv4_runs/twolevel_paired.txt`), but H is not uniformly weak: it beats E, the variant with the same general-n inner, 5/5 in hot_bat (−18.1% paired, same file).

### EMR 5-run medians (bench_twolevel 200 200 all, 5 runs, raw in `emr_runs/twolevel_run{1..5}.txt`)

|         | hot_bat | hot_ser | cold_bat | cold_ser |
|---------|---------|---------|----------|----------|
| F       |  55.43  |  58.12  |  240.31  |  512.30  |
| H vs F  | +20.4%  | +21.7%  |  +51.3%  | +23.2%   |
| I vs F  |  −0.7%  |  +7.0%  |  +31.4%  | +18.6%   |

**Falsification of the EMR prediction.** Pre-registered: "modest `hot_ser` win, modest cold_bat / cold_ser losses. EMR's VBMI2 zmm inner is fast enough that the outer-prefetch headroom is smaller." Result: I has *no* `hot_ser` win — it loses +7.0%. Only `hot_bat` ties (−0.7%). The "VBMI2 inner is fast enough" reasoning was directionally right but went further than predicted: when the inner path is a single-zmm `vpcmpeqw` + `kortest`, even the dep-chained outer mode has enough OoO room (3 AGUs + wide ROB on Granite Rapids µarch, full clock, no AVX-512 freq downclock) for Shar's 9-deep cmov chain to retire in parallel with itself. Software prefetch finds no critical-path stall to hide and becomes pure contention. Cold-mode losses are larger than predicted (+31.4% / +18.6%) — same bandwidth-contention regime as M1 Pro / GV4 but EMR's higher peak DRAM bandwidth doesn't rescue it because the demand line on `carr` is on the critical path regardless.

> **Correction (2026-10-11):** Mis-aimed prefetch (§1). Paired per-run I vs F on EMR (5 runs, `emr_runs/twolevel_paired.txt`): hot_bat −0.7% with I faster in 5/5 runs by 0.6–0.9% (consistent, but too small to matter — a tie by size, not by sign), hot_ser +7.2% (0/5), cold_bat +28.8% (0/5), cold_ser +19.6% (0/5). The Emerald Rapids 8559C core is **Raptor Cove**, not a "Granite Rapids µarch" (§5). The "bandwidth-contention regime" and "demand line on `carr` is on the critical path regardless" explanations are retracted with the numbers they explained.

F is strict-best on EMR every mode. H underperforms I, same pattern as M1 Pro and GV4.

> **Correction (2026-10-11):** False. By paired per-run rank on EMR (§2.1; `emr_runs/twolevel_paired.txt`) F is best in `hot_ser` (5/5) and I is nominally best in `hot_bat`, but **C is cold-best**: 5/5 in `cold_bat` and 4/5 in `cold_ser`; F vs D `cold_ser` is +17.7% with D faster 5/5 (§2.2). "H underperforms I" holds paired on EMR in the hot modes and `cold_bat` (+21.1% / +13.8% / +19.6%, I faster 5/5) and is a tie in `cold_ser` (+2.6%).

### SKX 5-run medians (bench_twolevel 200 200 all, 5 runs, raw in `skx_runs/twolevel_run{1..5}.txt`)

|         | hot_bat | hot_ser | cold_bat | cold_ser |
|---------|---------|---------|----------|----------|
| F       |  84.42  |  83.72  |  594.47  |  826.85  |
| H vs F  | +19.2%  | +30.3%  |  +77.0%  | +29.1%   |
| I vs F  |  +5.2%  | +20.9%  |  +20.9%  | +13.9%   |

**Falsification of the SKX prediction.** Pre-registered: "biggest `hot_ser` win on the narrow-OoO axis — Shar's 9-cmov outer dep-chain on a 2-AGU core has the most stall room for runahead to fill. AVX-512 freq downclock hurts the surrounding scalar loop and pushes the Shar tail further off the critical path." Result: I has *no* winning mode on SKX — `hot_ser` is +20.9% slower than F, the predicted-winning mode. F still strict-best hot; D still strict-best cold (full F→D cold reversal preserved). The "narrow OoO + slow inner ⇒ runahead win" half of the model is now 0/2 (SKX, EMR both falsify it from opposite ends of the inner-speed axis: SKX's gated-zmm AVX2 inner is fast enough, EMR's single-zmm VBMI2 inner is fastest).

> **Correction (2026-10-11):** Mis-aimed prefetch (§1). Paired per-run I vs F on SKX (5 runs, `skx_runs/twolevel_paired.txt`): hot_bat +7.7% (0/5), hot_ser **+10.3%** (0/5; the +20.9% above is a ratio of medians), cold_bat +9.8% (0/5), cold_ser +13.4% (0/5). The direction — no I win on SKX — survives. "D still strict-best cold": by paired rank `cold_bat` is led by C (D beats F 4/5) and `cold_ser` by D (5/5 over F; F vs D +16.9%) (§2.1, §2.2). On the AVX-512 premise of the pre-registered prediction: 512-bit integer compares trip license level L1, not L2, on Skylake-SP, and the shipped gated build executes no zmm instruction at all, so nothing was ever downclocked (§5).

Mechanism: SKX's AVX2 inner (gap=32, 2× ymm + 2 cmpeq + OR + movemask, ~9 ns warm at n=4096) is fast enough that even on a 2-AGU narrow-OoO core, Shar's 9-deep cmov chain on the K=512 outer can issue concurrently with itself across the inner-search retirement window. The freq-downclock hypothesis was wrong direction: SKX gates zmm off via `__AVX512VBMI2__`, so the surrounding scalar loop *isn't* downclocked — there's no extra Shar-tail-off-critical-path effect to add stall headroom for software prefetch to fill. Cold losses are large (+20.9% / +13.9% vs F's already-cold-losing baseline) but D remains the cold-best variant; H/I do not displace D as the cold alternate.

> **Correction (2026-10-11):** "Cold losses are large (+20.9% / +13.9%)" rests on ratio-of-medians numbers measured with the mis-aimed prefetch; paired they are +9.8% / +13.4% (I slower 5/5, `skx_runs/twolevel_paired.txt`). The stall-headroom / runahead reasoning is retracted as an explanation (§1); the 2026-10 review also notes that the paper's own small-n data (Fig. 12) shows prefetching as a small cost, not a gain, for arrays this small.

H underperforms I, same pattern as M1 Pro / GV4 / EMR.

> **Correction (2026-10-11):** holds for SKX paired (H slower than I in all four modes: paired medians +12.2% / +5.1% / +34.7% / +12.7%, WIN for I in each, H faster in at most 1 of 5 runs — `skx_runs/twolevel_paired.txt`), but the pattern is not uniform: H and I tie in cold_ser on M1 Pro and EMR (see the notes above).

### Pi 5 5-run medians (bench_twolevel 200 200 all, 5 runs, raw in `pi5_runs/twolevel_run{1..5}.txt`, 2026-05-18)

|         | hot_bat | hot_ser  | cold_bat | cold_ser |
|---------|---------|----------|----------|----------|
| F       | 244.40  | 328.50   | 1591.57  | 1547.03  |
| H       | 260.82  | 252.48   | 2354.24  | 2635.44  |
| I       | 242.76  | 254.65   | 1892.39  | 2015.35  |
| I vs F  | −0.7%   | **−22.5%** | +18.9% | +30.3%   |

**Confirmation of the pre-registered Pi 5 prediction.** Pre-registered: "best `hot_ser` win on the bench (M1-comparable or larger) *and* possibly a `hot_bat` win, or full SKX-like falsification." Result: clean `hot_ser` win at −22.5% (slightly larger than M1 Pro's −19.8%, the largest dep-chain win on the bench); `hot_bat` is a tie at −0.7%, no win. Both cold modes regress as expected (paper §4 `WL > log B` regime: explicit prefetches contend for the demand block-load pipeline). The model now stands at 2/2 confirmations on hosts that satisfy *both* "narrow-or-3-AGU OoO" *and* "slow inner" (M1 Pro: 3 AGUs at half clock + slowest M4-shared NEON inner; Pi 5: 2 AGUs + slowest paired-x2 NEON inner). The hot_bat-tie-not-win on Pi 5 weakens the secondary prediction that batched dispatch on Pi 5 should also surface a stall — apparently 2-AGU OoO can still overlap inner retirement with Shar's 9-cmov chain when dispatch is batched.

> **Correction (2026-10-11): retracted.** The −22.5% is a ratio of independent per-cell medians under 1.5–1.6× per-run geometric-mean drift (max/min of each run's geometric mean over variants, 1.49–1.61× across the four modes, `pi5_runs/twolevel_paired.txt`), and its sign is wrong. Paired per-run I vs F `hot_ser` on the same five archived runs (`pi5_runs/twolevel_paired.txt`): +5.8%, +12.0%, −49.2%, +1.2%, +6.6% — median **+5.8%, I slower in 4 of 5 runs**. The one negative run is an F outlier (F `hot_ser` per run: 216, 340, 482, 252, 329 ns; the 482 is 2.2× that run's own `hot_bat`), which lifted F's median to 328.5 ns (§2.3, §3). The other cells, paired: hot_bat +2.6% (tie, not −0.7%), cold_bat +34.6% (I slower 5/5, not +18.9%), cold_ser +30.0% (5/5). With the repaired harness (ten runs, corrected prefetch; `pi5_runs/twolevel_paired_v2.txt`) I is slower than F in `hot_ser` by a paired median of +8.6% (F faster 8/10) and in `hot_bat` by +7.3% (8/10) — final section. The "2/2 confirmations" count is therefore one (M1 Pro, itself suggestive only), and "the largest dep-chain win on the bench" does not exist. "M1 Pro: 3 AGUs at half clock": M1 Pro runs at about 0.72× the M4 Max clock, not half (§5).

H underperforms I across the board, same pattern as M1 Pro / GV4 / EMR / SKX.

> **Correction (2026-10-11):** Not hot. Paired H vs I on the archived Pi 5 runs (`pi5_runs/twolevel_paired.txt`): hot_bat +1.9% (tie), hot_ser −0.2% (H faster 3/5, tie), cold_bat +10.7% (I faster 4/5), cold_ser +14.4% (4/5). With the repaired harness all four modes are ties (hot_bat +0.5%, hot_ser +1.2%, cold_bat +5.2%, cold_ser +1.7%; `pi5_runs/twolevel_paired_v2.txt`). Note that by the same ratio-of-medians statistic H's `hot_ser` median in the table above (252.48) is also well below F's (328.50) — the same F-median artifact, which should have flagged F's median rather than been read as an I win.

Per-run variance on this Pi 5 sweep is wide (F hot_ser ranges 216–482 ns across 5 runs); 5-run medians compress that, and relative I-vs-F deltas are clean because both kernels run under identical per-run thermal/governor conditions. Cold matrix relative ordering shifted from the 2026-05-13 baseline (F now wins cold_ser vs D, but D still wins cold_bat); given the Pi 5 thermal/governor variance, treat the cold ordering as "C/D best cold_bat, F competitive cold_ser, all within governor-hop noise" rather than a structural shift.

> **Correction (2026-10-11):** The sentence "relative I-vs-F deltas are clean because both kernels run under identical per-run conditions" is the justification for a *paired* comparison, but the table above never computed one; the paired result reverses the sign (previous notes). "F now wins cold_ser vs D" is a tie: paired F vs D `cold_ser` median −0.4%, F faster 3/5 (`pi5_runs/twolevel_paired.txt`; §2.3). "C/D best cold_bat": D, not C — D beats C in `cold_bat` 5/5 (D vs C −15.3%) and beats F 5/5 (F vs D +31.8%) (§2.1, §2.3). The run-level drift itself (F `hot_ser` 216–482 ns) is the reason per-cell medians cannot be differenced across variants on this host (§2); the archived runs recorded no governor, clock or temperature, and the host runs the `ondemand` governor (§2.3).

### Mechanism map (revised after M1 + GV4 + EMR + SKX + Pi 5)

For each of the four cold-reversal hosts, the paper predicts a `hot_ser` win (where dep-chain exposes pointer-chase latency that runahead can hide) and a `cold_*` loss (where bandwidth contention with demand loads dominates). M1 Pro and Pi 5 confirm the prediction. GV4 partially falsifies it with a `hot_bat`-only win (I wins `hot_bat`, no `hot_ser` win). EMR, SKX, and M4 Max each fully falsify with no winning mode. The settled pattern (6/6 hosts): **the dep-chain `hot_ser` win is conditional on the *inner* path being slow enough to leave critical-path stall for software prefetch to hide, and neither narrow-OoO nor wide-OoO-at-full-clock by itself creates that stall.** M1 Pro's M4-shared inner (`vld1q_u16_x4` + 4 cmp + OR-tree) and Pi 5's NEON paired-x2 inner are the two slowest across the six hosts; that's why I `hot_ser` wins on M1 and Pi 5 but not on GV4 (faster x2 inner with 4 AGUs), EMR (fast single-zmm inner), SKX (gated-AVX2 inner — fast enough that 2-AGU narrow-OoO still issues Shar's 9-cmov chain in parallel with inner retirement), or M4 Max (same `vld1q_u16_x4` inner as M1 but at full M4-Max clock — fast enough on a 3-AGU wide-OoO core to absorb the dep-chain stall). Narrow-OoO is necessary but not sufficient on x86; on Apple silicon, the *clock-relative inner cost* is what flips M1 Pro to a confirm and M4 Max to a falsify despite identical inner code. Slow-inner is the real predictor.

> **Correction (2026-10-11): retracted as a conclusion.** After pairing, the only `hot_ser` I win is M1 Pro (−10.9%, 4/5, measured with the mis-aimed prefetch); the Pi 5 "confirmation" reverses sign (+5.8%, I slower 4/5 archived; +8.6%, F faster 8/10 under the repaired harness). A one-host pattern is a hypothesis, not a settled six-host rule, and every number this paragraph explains was produced by a prefetch that never covered a node on the search path (§1, §2.3). "GV4 ... 4 AGUs": the review reported three load pipes on Neoverse V2 (not verified here); "clock-relative inner cost" between M1 Pro and M4 Max: M1 Pro is ~0.72× the M4 Max clock, not half (§5). The 2026-10 review also notes that the paper itself (Fig. 12) shows prefetching as a small *cost* for arrays of n ≤ 2¹³, so no hot win was ever to be expected from the prefetch on a 1 KB, L1-resident outer.

All 6 hosts landed:

- ~~M4 Max~~ — landed 2026-05-18; falsified the GV4-mirroring `hot_bat`-win prediction. Actual: hot_bat +0.5% (tie), hot_ser +13.5%, cold_bat +3.5%, cold_ser +103.9% — F strict-best every mode. Same EMR-shape outcome; cold_ser blowup tracks the existing `_spine_4096` cold mechanism (wide-OoO + 128-B line + no upstream streamer) compounded by 4-deep-prefetch bandwidth contention with demand loads.
- ~~Pi 5~~ — landed 2026-05-18, see above.
- ~~GV4~~ — landed 2026-05-18, see above.
- ~~EMR~~ — landed 2026-05-18, see above.
- ~~SKX~~ — landed 2026-05-18, see above.

> **Correction (2026-10-11), M4 Max:** the "+103.9% cold_ser blowup" does not exist — it is a ratio of medians. Paired per-run I vs F `cold_ser` is +26.3%, +119.4%, +77.1%, +22.9%, +26.4% (median **+26.4%**, I slower 5/5; `m4_runs/twolevel_paired.txt`), and the dedicated mechanism sentence explained a number produced by the mis-aimed prefetch (§1). The other cells, paired: hot_bat −0.4% (tie), hot_ser +16.0% (0/5), cold_bat +13.3% (I faster 1/5). "F strict-best every mode" is false: F ties E in `cold_bat` (F vs E +1.6%, F faster 1/5) and loses `cold_ser` to B, D and E (F vs E +28.2%, E faster 5/5; F vs D +16.2%, D faster 4/5); `cold_ser` best by paired rank is B (§2.1, §2.3). "4-deep-prefetch" → 6 levels at gap 64.

**Updated ship recommendation per host (for two-level micro-bench):**
- M1 Pro: F for hot_bat / cold_*; **I for hot_ser**.
- Pi 5: F for hot_bat / cold_ser; **I for hot_ser**; C/D for cold_bat (cold_bat-best is C; D the all-around cold alternate).
- GV4: **I for hot_bat**; F for hot_ser / cold_*.
- EMR: **F unconditionally** (I ties hot_bat but loses other 3; H underperforms I).
- SKX: **F for hot, D for cold** (no I-winning mode; H/I do not displace D as cold alternate; full F→D cold reversal preserved).
- M4 Max: **F unconditionally** (I ties hot_bat at +0.5% but loses other 3, with cold_ser blowup +103.9%; H underperforms I).

> **Correction (2026-10-11): these recommendations are superseded.** They rest on ratio-of-medians deltas and on H/I numbers measured with the mis-aimed prefetch. Replacement, from the paired re-analysis of the archived runs (`{host}_runs/twolevel_paired.txt`; §2.1–2.3) and, for the Pi 5, the repaired harness (`pi5_runs/twolevel_paired_v2.txt`; §6):
> - **Pi 5: D** (outer spine + compile-time n=4096 inner) — tied-best hot with B and F (E is within 3%, but D is faster in 8 of 10 hot_bat runs), and the only variant that wins `cold_bat` (F vs D +44.7%, D faster 10/10); `cold_ser` is noise (seven different winners in ten runs). "I for hot_ser" is withdrawn (I vs F +8.6%, F faster 8/10). "C/D for cold_bat (cold_bat-best is C)" → D (D vs C −15.3% in the archived runs, D faster 5/5).
> - **M1 Pro:** I `hot_ser` −10.9% (I faster 4/5, pre-fix prefetch) is suggestive only; I is nominally best by paired rank in `hot_bat` (F ties; I vs F −0.3%, I faster 3/5) and F is best in `cold_bat`; `cold_ser` best by rank is A, and F vs D `cold_ser` is a tie (+5.7%).
> - **GV4:** I `hot_bat` −10.8% (5/5, pre-fix prefetch) holds pending re-measurement; F `hot_ser` 5/5; **C** wins both cold modes 5/5 — not "F for cold_*".
> - **EMR:** F `hot_ser` 5/5; I `hot_bat` faster 5/5 by under 1% (a tie by size); **C** is cold-best (5/5 `cold_bat`, 4/5 `cold_ser`) — not "F unconditionally".
> - **SKX:** F best in both hot modes; `cold_bat` led by C (D over F 4/5), `cold_ser` by D (5/5) — "F for hot, D for cold" survives in substance.
> - **M4 Max:** F best in `hot_bat` (I ties) and `hot_ser` (5/5); F ties E in `cold_bat`; `cold_ser` best is B, with F losing to B, D and E — not "F unconditionally".
>
> All H/I entries for M4 Max, M1 Pro, SKX, EMR and GV4 are pre-fix and need `./run_twolevel.sh HOST 10` with a rebuilt harness before any H/I recommendation is made for them.

### Open work

None. All 6 hosts have full A–I + Lem 5-run medians under the 4-mode harness; `plot.py` per-host dicts populated; `bench_twolevel.png` has all 60 bars (10 variants × 6 hosts) per panel.

> **Correction (2026-10-11):** Not none. (1) Re-measure H/I on M4 Max, M1 Pro, SKX, EMR and GV4 with the repaired harness (commands in the next section); until then every H/I statement for those hosts is "measured with the mis-aimed prefetch", and the plot.py two-level dicts keep the 2026-05-18 levels with H/I labelled accordingly (§6). (2) The 60-bar `bench_twolevel.png` panels therefore show bug-era H/I levels for those five hosts.

---

## Repaired harness, 2026-10-11

Two defects were fixed in `bench_twolevel.cpp` on 2026-10-11 (§1, §2): the Eytzinger prefetch offset (`kPrefOff = kGap/2` for the 1-based layout; the array is now cache-line aligned so one node's descendant block is exactly one line, as the paper assumes, and padded by `kGap·(K+1)` slots so no prefetch leaves the allocation), and the aggregation (paired per-run deltas, per-run ranks, sign counts and run-level drift via `compute_twolevel_paired.py`; the driver now runs an untimed warm-up pass, randomises the timing order per run, pins to one core and records governor and temperature). In the review's three-run A/B on this Pi 5 (`pi5_runs/eytz_offset_ab/`, 100 sets × 200 reps, 2026-10-10) the corrected, line-aligned prefetch (variant I4, masked) was faster than the shipped offset in every run: cold_bat -31% to -10%, cold_ser -51% to -21%, hot modes −1.5% to −6.2% (the gated variant I3: cold_bat -35% to -16%, cold_ser -55% to +3%); the shipped offset was slower than no prefetch at all in 5 of 6 cold cells (cold_bat +11% to +20%) and 4–7% slower hot (§1).

Conventions as in `Text/corrections_2026-10.md`: deltas are X/Y − 1 in percent, negative means X is faster; "k/10" is the number of runs in which X was faster; WIN needs at least 80% of runs agreeing in sign and a median paired delta of at least 3%, everything else is a TIE.

### Pi 5 — ten runs, repaired harness

Raw: `pi5_runs/twolevel_v2_run{1..10}.txt`, aggregated to `pi5_runs/twolevel_paired_v2.txt`. Pinned to one core, `ondemand` governor, 50–60 °C, order randomised per run; the archived 2026-05-18 files were left untouched. Hot run-level drift fell from 1.5–1.6× to 1.09–1.12× with the warm-up pass and pinning; cold drift is still 2.4–2.9× because each cold cell is a single pass of 200 queries (~300 µs), so cold verdicts need the sign counts, not the medians (§6).

Best variant by mean paired rank: **D in hot_bat (fastest in 7/10), D in hot_ser (8/10), D in cold_bat (7/10)**; cold_ser is noise (seven different winners in ten runs, C best by mean rank).

| pair (X vs Y) | hot_bat | hot_ser | cold_bat | cold_ser |
|---|---|---|---|---|
| F vs D | +2.7% (F faster 2/10) tie | +2.0% (1/10) tie | **+44.7%** (0/10, D wins) | −5.6% (6/10) tie |
| D vs A | −10.3% (10/10) | −15.0% (10/10) | −39.0% (9/10) | −6.6% (6/10) tie |
| F vs A | −7.7% (9/10) | −12.4% (9/10) | −9.9% (6/10) tie | −11.8% (7/10) tie |
| I vs F (fixed prefetch) | **+7.3%** (I faster 2/10, F wins) | **+8.6%** (2/10, F wins) | −2.5% (5/10) tie | +39.9% (3/10) tie |
| H vs E (fixed prefetch) | +5.6% (2/10, E wins) | +10.0% (1/10, E wins) | +13.3% (2/10, E wins) | +12.9% (4/10) tie |
| H vs I (fixed prefetch) | +0.5% (H faster 4/10) tie | +1.2% (2/10) tie | +5.2% (3/10) tie | +1.7% (5/10) tie |
| I vs D | +10.2% (0/10) | +11.1% (0/10) | +53.2% (0/10) | +18.1% (2/10) |
| F vs Lem | −37.5% (10/10) | −39.4% (10/10) | −17.3% (7/10) tie | −30.5% (8/10) |
| D vs Lem | −39.3% (10/10) | −40.7% (10/10) | −49.1% (10/10) | −19.7% (6/10) tie |
| G vs F | +68.5% (0/10) | +67.7% (0/10) | +17.5% (2/10) | +31.3% (1/10) |

(All rows from `pi5_runs/twolevel_paired_v2.txt`; the table in §6 of the corrections file is the same source minus the H vs I row.)

Levels (median of 10, ns/query — levels only, do not difference medians across variants): hot_bat A 235.9, B 215.6, C 231.0, D 209.7, E 214.9, F 214.5, G 359.4, H 231.1, I 228.6, Lem 347.0; hot_ser A 249.5, B 216.7, C 243.7, D 209.7, E 213.8, F 216.6, G 359.6, H 235.6, I 232.9, Lem 353.6.

What this settles for the Pi 5: with the prefetch aimed correctly the Eytzinger variants stop being catastrophic cold (I ties F in cold_bat instead of the archived +34.6%) but are still 7–9% slower than Shar hot (I vs F +7.3% / +8.6%) and never beat D anywhere (I vs D +10.2% / +11.1% / +53.2% / +18.1%), so the Khuong & Morin outer does not pay off on this core. The **Pi 5 ship recommendation is D** (outer spine + compile-time n=4096 inner): tied-best hot with B and F (E is within 3%, but D is faster in 8 of 10 hot_bat runs), and the only variant that wins cold_bat. F is a hot tie and loses cold_bat by 45% (§6). This is also what the paper's own small-n data predicts for a 1 KB, L1-resident outer (Fig. 12 shows prefetching as a small cost at n ≤ 2¹³, per the 2026-10 review). Two structural caveats remain for any I-vs-F reading: variant I pays one extra dependent load that F never pays (`eytz_to_sorted[i]`, then `keys[sorted_idx]`), worth about one memory round trip cold (§1); and the hot modes keep only the 1 KB outer hot while each set's inner loads are first touches, and about half of the hot queries miss the outer and never run the inner (§5, "The cache-state labels").

### Other five hosts — not re-measured

M4 Max, M1 Pro, SKX, EMR and GV4 have not been re-run with the repaired harness. Every H/I number for them in this file, in CLAUDE.md, in the plot.py `*_twolevel` dicts and in `bench_twolevel.png` was measured with the mis-aimed prefetch; the paired re-analysis of the archived 2026-05-18 runs (`{host}_runs/twolevel_paired.txt`), summarised in the correction notes above and in §2 of the corrections file, is the best available statement of them. To close them, rebuild `bench_twolevel` with the host's build line, then

```
./run_twolevel.sh HOST 10
python3 compute_twolevel_paired.py HOST --glob 'HOST_runs/twolevel_v2_run*.txt' --out HOST_runs/twolevel_paired_v2.txt
```

### Pre-registered predictions cannot be audited

The per-host predictions that the "confirmation / falsification" paragraphs above score against were written in a private plans file outside the repository (`~/.claude/plans/let-s-spec-the-work-iridescent-waterfall.md`) and were never copied into the tracked tree. An outside reader has only the fragments quoted in this file, so the pre-registration cannot be verified from the repository (§5, "Provenance").

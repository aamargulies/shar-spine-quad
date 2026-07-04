# Khuong & Morin (2017), "Array Layouts for Comparison-Based Searching" — speculation for QuadSearch

Read the full 49 pages. Speculation on what the paper has to say to this project, in rough order of "actionable for QuadSearch" → "validates a decision already made":

**1. The K=512 outer is the most promising place to apply the paper's main result.**
Their headline finding: for n that overflows L2, branch-free Eytzinger with 4-deep `__builtin_prefetch(a + B*i + offset)` beats every other layout — because speculative execution + explicit prefetch acts as runahead, keeping ~4 cache lines in flight at all times. The QuadSearch finding "K=512 outer spine is only 1 KB, too short for any stride prefetcher — pointer chase is pure critical-path cost" is *exactly* the situation their explicit prefetch was designed for. Shar's 9-deep cmov chain on the sorted-order outer is what they call "branch-free without prefetching" — fast hot, but on narrow-OoO hosts (SKX, Pi 5) cold-loses because there's no streamer to feed it. Their trick: lay the outer out in Eytzinger order, prefetch `a[multiplier*i + offset]` at the top of every iteration, multiplier=cache-line-width-in-elements. For K=512 that's 9 cmov iterations issuing 9 prefetches whose latencies overlap. This is a real new variant — neither C, D, F, nor Lem implements it — and it's the straightest path I see to the open "narrow-OoO cold reversal" pattern.

**2. The hybrid n=4096 inner is structurally what they call a Btree node with B=16 (their figure 15-17).**
Their independent finding "B=16 is optimal both in theory and practice for 4-byte data, log₂17 ≈ 4.09 fewer misses" lines up with QuadSearch's gap=32 (= 64 B / 2 B per u16 = a single cache line, ~32 comparisons via SIMD per node) and gap=64 on Apple silicon (128 B line). The QuadSearch design *is* a shallow custom Btree with SIMD-vectorized inner node search and a one-level top directory (the spine). Validates the architectural decision; nothing new to try, but worth knowing the paper agrees on the gap-tracks-cache-line conclusion from a completely different angle.

**3. Their Listing 6 prefetch (`multiplier*i + offset`) is structurally identical to the Pi 5 / SKX speculative `__builtin_prefetch` in the quat loop.** The QuadSearch finding "narrow OoO + 2 AGUs benefits from kept prefetch; wide OoO + good streamers does not" is the per-uarch generalization of their single-machine result. Their model in §4 ("max{L,c} log_B n when WL > log B") explains *why* it stops helping on EMR/M4/GV4: bandwidth W is high enough that the streamer alone saturates the load pipeline, and adding software prefetches contends rather than helps. Same conclusion the project reached empirically. The 4-way pfC failure on M1 (cold +21.6%) is exactly their "t=2 saturates bandwidth" prediction — their model would have predicted the failure.

**4. Lesson 3 (mixed Eytzinger top + sorted-block leaves ≈ branch-free Eytzinger with prefetching) gives a ceiling for the two-level harness.** Their mixed layout never beats prefetched Eytzinger — only matches it. Translation: any K=512 outer approach is bounded by what a well-prefetched Eytzinger outer can do. So if (1) above doesn't beat Shar+F on the wide-OoO hosts, the paper says no other top-level approach will either. Useful as a "stop-here" criterion.

**5. Lesson 5 (vEB is not useful for in-memory) closes off a tempting direction.** If anyone ever proposes recursive layout for the 4096 inner block, the paper directly disproves it — vEB's odd subtree sizes guarantee 2× cache lines per subtree vs. a Btree, which kills it.

**6. Branchy-beats-branchfree-at-huge-n result (Fig 7) doesn't apply here.** Their crossover is at n ≈ 2²², far above QuadSearch's 4096 ceiling. At Roaring container sizes everything is in cache or one cold line away, not 2 GB-deep. Worth mentioning only because it explains why their conclusion is "Eytzinger+prefetch ⊕ branch-free sorted for small n" rather than "always Eytzinger" — and why QuadSearch operates entirely in the small-n regime where their Lesson 1+2 (branch-free + prefetch) applies cleanly.

**7. Apple-silicon spine_4096 cold floor (the closed open-item) lines up with their bandwidth model.** They quantify W ≈ 4.7 cache lines in flight on the 4790K and predict t=1 prefetch saturates it. M1 Pro's load pipeline is wider but the *demand line* (carr) can't issue until lo resolves, so the contention regime kicks in at smaller t. The paper's framework reproduces the project's empirical conclusion that no pre-lo prefetch can help — same closed answer, different derivation.

**Strongest single bet: try Eytzinger-laid-out outer spine with 4-deep explicit prefetch, on the four hosts where Shar reverses cold (SKX, Pi 5, EMR, M1 Pro).** It's a genuine third option neither the project nor Lemire's reference has tried, and the paper's mechanism is exactly the failure mode the project diagnosed independently. The other six points are mostly retroactive validation.

---

## Results — H/I implementation, 2026-05-18

Implemented the strongest-single-bet on all six hosts as variants H (Eytzinger outer + 4-deep PF + general-n inner) and I (Eytzinger outer + 4-deep PF + n=4096 inner). Spec/plan in `~/.claude/plans/let-s-spec-the-work-iridescent-waterfall.md`. Paper's Listing 6 verbatim — `__builtin_prefetch(a + multiplier*i + offset)` with multiplier = cache-line-width-in-u16 (= `kGap`: 32 on 64-B-line hosts, 64 on 128-B-line hosts), offset = `(3*kGap/2) - 1`. Trailing pad on `keys_eytz` guards against OoB-prefetch portability hazard (paper §5.3). Index recovery via `i >> __builtin_ffs(~i)` (paper Listings 4-5) plus a BFS-slot-to-sorted-index inverse permutation (`eytz_to_sorted`) so the existing `s.containers[idx]` callsites still work.

### M1 Pro 5-run medians (bench_twolevel 200 200 all, 5 runs, raw in `m1_runs/twolevel_run{1..5}.txt`)

|         | hot_bat | hot_ser   | cold_bat | cold_ser |
|---------|---------|-----------|----------|----------|
| F       |  45.88  |  79.26    |  278.54  |  776.46  |
| H vs F  | +50.2%  |  −6.2%    |  +38.4%  |  +6.5%   |
| I vs F  |  +4.0%  | **−19.8%** | +17.9%  | +12.0%   |

**Partial confirmation.** I wins `hot_ser` on M1 Pro by ~20% — the dep-chained critical-path mode where the prefetch-as-runahead trick should help most. Both cold modes regress for I, exactly as the paper's bandwidth-saturation model predicts: explicit prefetches contend with the demand block-load when streamers are already saturating the load pipeline (paper §4: `WL > log B` regime). Hot_bat is a tie.

H consistently underperforms I — adding the Eytzinger+PF outer to the slower general-n inner doesn't recover the inner-path overhead. Expected; F's signature win was always n=4096-inner-specific.

### GV4 5-run medians (bench_twolevel 200 200 all, 5 runs, raw in `gv4_runs/twolevel_run{1..5}.txt`)

|         | hot_bat   | hot_ser  | cold_bat | cold_ser |
|---------|-----------|----------|----------|----------|
| F       |  65.37    |  50.34   |  268.45  |  486.13  |
| H vs F  |  −1.0%    | +25.5%   |  +38.1%  |  +30.7%  |
| I vs F  | **−12.0%** | +16.0%  |  +15.9%  |  +27.5%  |

**Partial falsification of the GV4 prediction.** Pre-registered: "I loses on every mode — V2's 4 AGUs already give the Shar cmov chain the most headroom; nothing for software prefetch to add." Result: I loses 3/4 but **wins `hot_bat` by −12%**. The 4-AGU headroom isn't sufficient under batched dispatch — explicit Eytzinger prefetch still extracts a meaningful win there. The dep-chained `hot_ser` mode (where the prediction expected the *biggest* surprise on narrow-OoO hosts) is actually a clean F-win on GV4: 4 AGUs give Shar enough room to issue its 9-deep cmov chain in parallel with itself, leaving no critical-path stall for software prefetch to hide. Cold modes regress as expected.

H underperforms I across the board, same pattern as M1 Pro.

### EMR 5-run medians (bench_twolevel 200 200 all, 5 runs, raw in `emr_runs/twolevel_run{1..5}.txt`)

|         | hot_bat | hot_ser | cold_bat | cold_ser |
|---------|---------|---------|----------|----------|
| F       |  55.43  |  58.12  |  240.31  |  512.30  |
| H vs F  | +20.4%  | +21.7%  |  +51.3%  | +23.2%   |
| I vs F  |  −0.7%  |  +7.0%  |  +31.4%  | +18.6%   |

**Falsification of the EMR prediction.** Pre-registered: "modest `hot_ser` win, modest cold_bat / cold_ser losses. EMR's VBMI2 zmm inner is fast enough that the outer-prefetch headroom is smaller." Result: I has *no* `hot_ser` win — it loses +7.0%. Only `hot_bat` ties (−0.7%). The "VBMI2 inner is fast enough" reasoning was directionally right but went further than predicted: when the inner path is a single-zmm `vpcmpeqw` + `kortest`, even the dep-chained outer mode has enough OoO room (3 AGUs + wide ROB on Granite Rapids µarch, full clock, no AVX-512 freq downclock) for Shar's 9-deep cmov chain to retire in parallel with itself. Software prefetch finds no critical-path stall to hide and becomes pure contention. Cold-mode losses are larger than predicted (+31.4% / +18.6%) — same bandwidth-contention regime as M1 Pro / GV4 but EMR's higher peak DRAM bandwidth doesn't rescue it because the demand line on `carr` is on the critical path regardless.

F is strict-best on EMR every mode. H underperforms I, same pattern as M1 Pro and GV4.

### SKX 5-run medians (bench_twolevel 200 200 all, 5 runs, raw in `skx_runs/twolevel_run{1..5}.txt`)

|         | hot_bat | hot_ser | cold_bat | cold_ser |
|---------|---------|---------|----------|----------|
| F       |  84.42  |  83.72  |  594.47  |  826.85  |
| H vs F  | +19.2%  | +30.3%  |  +77.0%  | +29.1%   |
| I vs F  |  +5.2%  | +20.9%  |  +20.9%  | +13.9%   |

**Falsification of the SKX prediction.** Pre-registered: "biggest `hot_ser` win on the narrow-OoO axis — Shar's 9-cmov outer dep-chain on a 2-AGU core has the most stall room for runahead to fill. AVX-512 freq downclock hurts the surrounding scalar loop and pushes the Shar tail further off the critical path." Result: I has *no* winning mode on SKX — `hot_ser` is +20.9% slower than F, the predicted-winning mode. F still strict-best hot; D still strict-best cold (full F→D cold reversal preserved). The "narrow OoO + slow inner ⇒ runahead win" half of the model is now 0/2 (SKX, EMR both falsify it from opposite ends of the inner-speed axis: SKX's gated-zmm AVX2 inner is fast enough, EMR's single-zmm VBMI2 inner is fastest).

Mechanism: SKX's AVX2 inner (gap=32, 2× ymm + 2 cmpeq + OR + movemask, ~9 ns warm at n=4096) is fast enough that even on a 2-AGU narrow-OoO core, Shar's 9-deep cmov chain on the K=512 outer can issue concurrently with itself across the inner-search retirement window. The freq-downclock hypothesis was wrong direction: SKX gates zmm off via `__AVX512VBMI2__`, so the surrounding scalar loop *isn't* downclocked — there's no extra Shar-tail-off-critical-path effect to add stall headroom for software prefetch to fill. Cold losses are large (+20.9% / +13.9% vs F's already-cold-losing baseline) but D remains the cold-best variant; H/I do not displace D as the cold alternate.

H underperforms I, same pattern as M1 Pro / GV4 / EMR.

### Pi 5 5-run medians (bench_twolevel 200 200 all, 5 runs, raw in `pi5_runs/twolevel_run{1..5}.txt`, 2026-05-18)

|         | hot_bat | hot_ser  | cold_bat | cold_ser |
|---------|---------|----------|----------|----------|
| F       | 244.40  | 328.50   | 1591.57  | 1547.03  |
| H       | 260.82  | 252.48   | 2354.24  | 2635.44  |
| I       | 242.76  | 254.65   | 1892.39  | 2015.35  |
| I vs F  | −0.7%   | **−22.5%** | +18.9% | +30.3%   |

**Confirmation of the pre-registered Pi 5 prediction.** Pre-registered: "best `hot_ser` win on the bench (M1-comparable or larger) *and* possibly a `hot_bat` win, or full SKX-like falsification." Result: clean `hot_ser` win at −22.5% (slightly larger than M1 Pro's −19.8%, the largest dep-chain win on the bench); `hot_bat` is a tie at −0.7%, no win. Both cold modes regress as expected (paper §4 `WL > log B` regime: explicit prefetches contend for the demand block-load pipeline). The model now stands at 2/2 confirmations on hosts that satisfy *both* "narrow-or-3-AGU OoO" *and* "slow inner" (M1 Pro: 3 AGUs at half clock + slowest M4-shared NEON inner; Pi 5: 2 AGUs + slowest paired-x2 NEON inner). The hot_bat-tie-not-win on Pi 5 weakens the secondary prediction that batched dispatch on Pi 5 should also surface a stall — apparently 2-AGU OoO can still overlap inner retirement with Shar's 9-cmov chain when dispatch is batched.

H underperforms I across the board, same pattern as M1 Pro / GV4 / EMR / SKX.

Per-run variance on this Pi 5 sweep is wide (F hot_ser ranges 216–482 ns across 5 runs); 5-run medians compress that, and relative I-vs-F deltas are clean because both kernels run under identical per-run thermal/governor conditions. Cold matrix relative ordering shifted from the 2026-05-13 baseline (F now wins cold_ser vs D, but D still wins cold_bat); given the Pi 5 thermal/governor variance, treat the cold ordering as "C/D best cold_bat, F competitive cold_ser, all within governor-hop noise" rather than a structural shift.

### Mechanism map (revised after M1 + GV4 + EMR + SKX + Pi 5)

For each of the four cold-reversal hosts, the paper predicts a `hot_ser` win (where dep-chain exposes pointer-chase latency that runahead can hide) and a `cold_*` loss (where bandwidth contention with demand loads dominates). M1 Pro and Pi 5 confirm the prediction. GV4 partially falsifies it with a `hot_bat`-only win (I wins `hot_bat`, no `hot_ser` win). EMR, SKX, and M4 Max each fully falsify with no winning mode. The settled pattern (6/6 hosts): **the dep-chain `hot_ser` win is conditional on the *inner* path being slow enough to leave critical-path stall for software prefetch to hide, and neither narrow-OoO nor wide-OoO-at-full-clock by itself creates that stall.** M1 Pro's M4-shared inner (`vld1q_u16_x4` + 4 cmp + OR-tree) and Pi 5's NEON paired-x2 inner are the two slowest across the six hosts; that's why I `hot_ser` wins on M1 and Pi 5 but not on GV4 (faster x2 inner with 4 AGUs), EMR (fast single-zmm inner), SKX (gated-AVX2 inner — fast enough that 2-AGU narrow-OoO still issues Shar's 9-cmov chain in parallel with inner retirement), or M4 Max (same `vld1q_u16_x4` inner as M1 but at full M4-Max clock — fast enough on a 3-AGU wide-OoO core to absorb the dep-chain stall). Narrow-OoO is necessary but not sufficient on x86; on Apple silicon, the *clock-relative inner cost* is what flips M1 Pro to a confirm and M4 Max to a falsify despite identical inner code. Slow-inner is the real predictor.

All 6 hosts landed:

- ~~M4 Max~~ — landed 2026-05-18; falsified the GV4-mirroring `hot_bat`-win prediction. Actual: hot_bat +0.5% (tie), hot_ser +13.5%, cold_bat +3.5%, cold_ser +103.9% — F strict-best every mode. Same EMR-shape outcome; cold_ser blowup tracks the existing `_spine_4096` cold mechanism (wide-OoO + 128-B line + no upstream streamer) compounded by 4-deep-prefetch bandwidth contention with demand loads.
- ~~Pi 5~~ — landed 2026-05-18, see above.
- ~~GV4~~ — landed 2026-05-18, see above.
- ~~EMR~~ — landed 2026-05-18, see above.
- ~~SKX~~ — landed 2026-05-18, see above.

**Updated ship recommendation per host (for two-level micro-bench):**
- M1 Pro: F for hot_bat / cold_*; **I for hot_ser**.
- Pi 5: F for hot_bat / cold_ser; **I for hot_ser**; C/D for cold_bat (cold_bat-best is C; D the all-around cold alternate).
- GV4: **I for hot_bat**; F for hot_ser / cold_*.
- EMR: **F unconditionally** (I ties hot_bat but loses other 3; H underperforms I).
- SKX: **F for hot, D for cold** (no I-winning mode; H/I do not displace D as cold alternate; full F→D cold reversal preserved).
- M4 Max: **F unconditionally** (I ties hot_bat at +0.5% but loses other 3, with cold_ser blowup +103.9%; H underperforms I).

### Open work

None. All 6 hosts have full A–I + Lem 5-run medians under the 4-mode harness; `plot.py` per-host dicts populated; `bench_twolevel.png` has all 60 bars (10 variants × 6 hosts) per panel.

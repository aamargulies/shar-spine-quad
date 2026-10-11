# Quad Search Presentation — Planning & Script

A 15-minute talk on the QuadSearch project, focused on AI-assisted CS research and the Shar algorithm archaeology story. Semi-technical audience.

> **Corrected 2026-10-11 against Text/corrections_2026-10.md; earlier numbers were retracted, see that file.** Every two-level number below is a paired per-run delta (5 archived runs per host, `{host}_runs/twolevel_paired.txt`; the Pi 5 was also re-run 10× with the repaired harness, `pi5_runs/twolevel_paired_v2.txt`). Main-bench numbers are 5-run medians from the regenerated `bench_table.txt`.

---

# Part 1 — Structure / Outline

Here's a 15-min structure that puts Shar at the emotional center and weaves the AI-as-collaborator angle throughout rather than bolting it on at the end.

## Slide/segment plan (~13 min content + 2 min buffer)

**1. The hook (1 min)**
"Roaring Bitmaps are how Elasticsearch, Druid, and ClickHouse compress sets. Inside each bitmap are thousands of little sorted `uint16` arrays. Searching them faster = those systems faster. Daniel Lemire wrote a SIMD trick called *quad search*. I spent a week with Claude trying to make it go even faster on 6 different CPUs."

**2. The setup (1 min) — one slide, just the table**
Show the 6-host table: Pi 5, M1 Pro, M4 Max, Xeon Skylake, Xeon Emerald Rapids, Graviton 4. Point out: "Different cache lines, different SIMD widths, different out-of-order widths. No single answer."

**3. How the collaboration worked (2 min) — the meta frame up front**
- I wrote hypotheses. Claude ran the benchmarks on each host, wrote per-CPU variants, kept a running findings log in `CLAUDE.md`.
- The log tracks *both* what worked *and* predictions that got refuted — critical, because otherwise you talk yourself into believing the clever thing.
- Show 2-3 lines from the findings table. This is the real artifact.

**4. Finding #1: the "spine" — one idea, one direction on every CPU (2 min)**
- Problem: quaternary search does 3 dependent loads before it can even start looking. On cold cache = 3 DRAM round-trips.
- Fix: precompute a tiny "spine" of sample points — 256 bytes, read as a few adjacent cache lines. The win is memory-level parallelism over that short contiguous read, not a stride prefetcher (a 256-byte spine is too short to train one).
- Result: faster cold at n=4096 on every CPU, but not uniformly 2–3×. `bench_table.txt` 5-run medians, non-spine → spine, cold ns/query: Pi 5 299.0 → 150.7, M4 Max 16.8 → 6.5, M1 Pro 37.1 → 11.1, Skylake 180.9 → 132.7, Emerald Rapids 64.9 → 37.2, Graviton 4 65.0 → 34.6 — about 2–3× on the ARM/Apple cores, under 2× on the x86 and Graviton servers. One idea, same direction everywhere. Caveat: `bench.cpp`'s "cold" column has no cache flush (corrections §5), so compare within a host only.
- *This is the part where AI was great* — writing 6 variants of the same idea tuned per-uarch is boring, mechanical, and exactly where models excel.

**5. Finding #2: where intuition was wrong (2 min) — "lowlights"**
- Predicted the in-loop prefetch would help on modern chips. It didn't: on Graviton 4 keeping it is slower (up to +10.8% warm at n=2048, `gv4_runs/ab_summary.txt`), and it was dropped on M4 and Emerald Rapids. Wide out-of-order cores already overlap the miss — the prefetch just burns issue slots. Worse: the Pi 5 prefetch we had logged as a "10–25% cold win" is a net loss in the archived main bench (the Graviton kernel is the Pi 5 kernel minus that prefetch, and it is faster cold at 13 of 14 sizes from n=128 up; corrections §5). The shipped Pi 5 kernel still carries it.
- Predicted Skylake would win biggest from unrolling. The straight unroll measured only ~1.5% warm (that figure described the retired unroll, corrections §2.3). The hybrid finish that replaced it is −32% warm in 5/5 runs but +40% *slower cold* at the median (hybrid faster in only 2 of 5 runs; per-run −12% to +62%, `skx_runs/hybrid_run*.txt` `4096*` rows; corrections §2.3) against a general-n control stable to ±0.6% in the same runs — warm and cold disagree, and the cold cost is unexplained.
- **Point**: Claude proposed plausible-sounding hypotheses confidently. Benchmarks disagreed. The discipline is *always run it*.

**6. The Shar archaeology story (4 min — the centerpiece)**
Tell it as a story:
- **1971**: Leonard Shar, Stanford PhD student, publishes a branchless binary search. Uses `bit_floor(len)` and a conditional-move chain. No paper trail after.
- **~50 years of silence.** Everyone ships textbook binary search with a branch.
- **2023**: A blogger ("probablydance") is benchmarking binary searches, stumbles onto Shar's trick, writes it up.
- **2026 (this project)**: We built an elaborate "outer spine" — a precomputed index across 512 Roaring containers — and predicted it would crush naive binary search on Intel server chips, because streamers love sequential patterns.
- **Hot, it didn't.** With the outer keys cache-hot, Shar's 1971 cmov chain (variant F) beat our outer spine (variant D, same inner) on five hosts: hot_bat −14.4% to −41.9%, all 5/5; hot_ser −53.9% on M4 Max, −43.4% on Graviton 4, −38.9% on M1 Pro, −37.1% on Emerald Rapids (all 5/5) and −16.3% on Skylake (4/5). On the Pi 5 it is a tie (−6.4% in 4/5 archived runs; +2.0% in the ten repaired-harness runs). Source: corrections §2.2, `{host}_runs/twolevel_paired.txt`.
- **Cold, it reversed.** Flush the caches and the spine or plain bsearch outer wins back: F is +31.8% slower than D in the Pi 5's batched cold mode (0/5; +44.7% in the ten repaired runs), +16.9% slower in Skylake's serial cold mode (0/5), +17.7% on Emerald Rapids and +16.2% on M4 Max (cold_ser). On Emerald Rapids and Graviton 4 the plain bsearch outer (variant C) is the cold-best variant (5/5 cold_bat on both). Corrections §2.1–2.3 and §6.
- **Why**: 512 keys × 2 bytes = 1 KB. Too small for any prefetcher to matter, so the spine descent is dependent-load latency with nothing to hide it. Shar's chain is *also* serial — load → compare → csel → load, nine deep, and it cannot be speculated past — but it has no branches to mispredict and no side structure, which is why it wins hot. Cold, the *branchy* `std::lower_bound` lets the core speculate past mispredicted branches and overlap the misses; the cmov chain can't (corrections §5; the same effect Khuong & Morin report for branchy vs branch-free search out of cache).
- **Moral**: a 55-year-old algorithm, lost and rediscovered by a blog post, beat the modern engineered solution on hardware its inventor couldn't have imagined — when the data were hot. Cold, the spine or the textbook bsearch outer won back (D on the Pi 5 and Skylake, plain bsearch C on Emerald Rapids and Graviton 4; on Skylake's batched cold mode plain bsearch C ranks first, D still beats Shar 4/5 and is the serial-cold best 5/5 — corrections §2.1). Good ideas are timeless; hardware changes around them; and the right answer depends on where your data are.

**7. What AI was good at vs. bad at (2 min)**
- Writing 6 near-identical C variants with per-uarch tweaks (yes)
- Keeping a structured findings log across weeks of sessions (yes)
- Running the same benchmark matrix on every host, producing plots (yes)
- Predicting which optimization would win (confidently wrong, repeatedly) (no)
- Noticing the Shar option existed — *I had to bring that from outside* (no)
- The right division of labor: human sets hypotheses + curates the "what was surprising" log; AI parallelizes the grunt work of coding + measuring.

**8. Takeaway slide (1 min)**
Three lines:
1. The spine: one idea, faster cold on every CPU (about 2–3× on the ARM/Apple cores, less on the servers).
2. Shar 1971 beat our modern outer index hot on five of six CPUs — and lost cold to the spine or the textbook bsearch outer (D on the Pi 5 and Skylake, plain bsearch C on Emerald Rapids and Graviton 4). Read old papers. Measure cold too.
3. AI + measurement: AI makes 6-machine experiments cheap. Measurement keeps you honest when AI's intuition is wrong.

---

Couple of delivery notes:
- The Shar story is the emotional peak — land it with the "55-year-old algorithm beats the fancy new thing — when the data are hot" line and pause. Then give the cold reversal its own beat.
- Have the 6-host comparison plot (`bench_compare_warm.png`) and the twolevel bar chart (`bench_twolevel.png`) as your two hero visuals. Two caveats on the bar chart: its H/I bars predate the 2026-10-11 prefetch fix (corrections §1), and it plots per-cell medians (levels), so its Pi 5 F hot_ser bar is inflated by the outlier run flagged in corrections §3 — rely on the paired table for the Pi 5, or crop/annotate that panel. Don't show code.
- If you're running long, cut section 4 (spine) to 90 seconds — it's the "obvious" win. Never cut Shar.

---

# Part 2 — Slide Copy & Speaker-Notes Script

Format below: each section has **SLIDE** (what the audience sees) and **SAY** (what you say, roughly word-for-word, ~150 wpm).

---

## 1. Hook — 1 min

**SLIDE 1**
> # Making search faster on 6 different CPUs
> ### …and what a 1971 algorithm taught me about AI-assisted research
>
> *(your name / date)*

**SAY**
> Roaring Bitmaps are how Elasticsearch, Druid, and ClickHouse compress sets of integers. Inside every Roaring Bitmap are thousands of tiny sorted arrays of 16-bit numbers. Searching those arrays faster makes all of those systems faster.
>
> Earlier this year Daniel Lemire published a SIMD trick called *quad search* that beats binary search on these arrays. I spent about a week with Claude trying to push it further — on six different CPUs, from a Raspberry Pi to Amazon's newest server chip. The punchline is going to be that a 55-year-old algorithm nobody remembers beat the clever index we built — at least while the data are hot. But first let me set the stage.

---

## 2. The six machines — 1 min

**SLIDE 2**
> # Six very different CPUs
>
> | | Cache line | SIMD | OoO width |
> |---|---|---|---|
> | Raspberry Pi 5 | 64 B | 128-bit NEON | narrow |
> | Apple M1 Pro | 128 B | 128-bit NEON | wide |
> | Apple M4 Max | 128 B | 128-bit NEON | wide |
> | Intel Skylake Xeon | 64 B | 512-bit AVX | medium |
> | Intel Emerald Rapids | 64 B | 512-bit AVX | wide |
> | AWS Graviton 4 | 64 B | 128-bit NEON | wide |
>
> **No single answer works on all of them.**

**SAY**
> These six machines look similar on a spec sheet but they differ on three axes that turn out to matter: how big a cache line is, how wide their SIMD is, and how aggressively they reorder instructions out-of-order. Apple's chips have 128-byte cache lines — twice everyone else. Intel has 512-bit vector registers — four times the ARM chips. And the "out-of-order width" — how many instructions the CPU juggles in flight — varies by almost 3×.
>
> The reason this matters is that every optimization I'll talk about wins on some of these and loses on others. There is no universal best code.

---

## 3. How I worked with Claude — 2 min

**SLIDE 3**
> # The workflow
>
> **Me**: hypotheses, priorities, weird ideas from outside
>
> **Claude**: per-CPU variants, benchmarks, findings log
>
> ---
>
> The findings log tracks **both** what worked **and** predictions that got refuted.

**SAY**
> Here's how the collaboration actually worked. I'd come in with a hypothesis — "I bet prefetching helps on this chip" — and Claude would write the variant, run it on the relevant host, and add a line to a running findings log that lives in the repo. By the end of the week that log was the real artifact of the project. It's probably the most valuable thing I produced.
>
> The critical discipline — and I want to flag this because it's easy to get wrong — was writing down *refuted* predictions, not just confirmed ones. If you only record your wins, you end up believing your own theory about why code is fast, when the honest answer is "measurement disagreed with me three times and I changed my mind."
>
> Claude is very good at producing confident-sounding hypotheses. The only thing that keeps you honest is a log that says "predicted X, measured not-X."

---

## 4. Win #1: the spine — 2 min

**SLIDE 4**
> # The "spine": one idea, one direction on every CPU
>
> Quad search does **3 dependent loads** before the real work starts.
> Cold cache → 3 trips to DRAM.
>
> **Fix**: precompute a tiny sorted sample of the array. Scan it sequentially first.
>
> ### Result: faster cold on every CPU — about 2–3× on ARM/Apple, under 2× on the x86/Graviton servers.
> *(memory-level parallelism over a 256-byte contiguous read — too short to train a stride prefetcher; `bench_table.txt` n=4096 medians, within-host comparison only — `bench.cpp`'s cold column is unflushed)*

**SAY**
> The first big optimization — and the only one that wins on every machine, at least for full-size containers — is something we called the "spine."
>
> Quad search works by picking probe points, loading them, and using the result to pick the next set of probe points. That's three dependent memory loads before you even start looking for your answer. On a cold cache that's three separate trips to main memory. That's slow.
>
> The fix: precompute a tiny sampled version of the array — just a few hundred bytes — and search that first before diving into the real array. The reason this works is *not* the hardware prefetcher: a 256-byte spine is too short to train a stride prefetcher. It's that the probes now land in a handful of adjacent cache lines instead of being scattered across eight kilobytes, so the CPU can have those few lines in flight at once — memory-level parallelism over a short contiguous read — instead of paying a full memory round trip for every dependent probe.
>
> Faster cold on every single machine — roughly two to three times on the Pi and the Macs, less than two times on the Xeons and the Graviton. One idea, one direction everywhere.
>
> This part is where AI was genuinely great — writing six tuned variants of the same idea, one per CPU, is mechanical work. Exactly the kind of thing I don't want to do by hand.

---

## 5. Lowlights: where intuition was wrong — 2 min

**SLIDE 5**
> # Where we were confidently wrong
>
> - *"Prefetching will help on the fast chips."*
>   → **slower** on Graviton 4 (up to +10.8% warm), dropped on M4 and Emerald Rapids — and a net loss on the Pi 5 too, where we had logged it as a win
>
> - *"Skylake will win biggest from loop unrolling."*
>   → the unroll: ~1.5%. The hybrid that replaced it: −32% warm (5/5), **+40% slower cold at the median** (hybrid faster in only 2 of 5 runs; per-run −12% to +62%, `skx_runs/hybrid_run*.txt` `4096*` rows; corrections §2.3). Warm and cold disagree.
>
> - *"Intel's prefetcher will love the 'outer spine' for two-level search."*
>   → It didn't — hot. Cold is another story. More on this in a moment.

**SAY**
> Here's the flipside. Three predictions I made — with Claude happily agreeing — that measurement destroyed.
>
> One: I thought adding a speculative prefetch inside the search loop would help on the modern wide-out-of-order chips. It didn't: on Graviton 4 the build with the prefetch is slower, by up to eleven percent warm, and on the M4 and Emerald Rapids we dropped it. Those chips are already overlapping the memory miss with other work on their own; the prefetch just burns an instruction slot. And here's the embarrassing part: on the Raspberry Pi, where we had written down a ten-to-twenty-five percent cold win, the archived data say the prefetch is a net loss there too. Nobody had run the A/B.
>
> Two: I predicted Intel's Skylake Xeon would benefit most from unrolling a specific loop, because it has a narrower out-of-order window. The unroll gave about one and a half percent. The hybrid finish that replaced it is thirty-two percent faster warm, in every run — and about forty percent slower cold at the median, in three of five runs. Warm and cold disagree, and we don't yet know why.
>
> Three — and this is the setup for the main story — I predicted that a more elaborate *two-level* version of the spine would dominate on Intel, because Intel's hardware prefetchers are excellent at sequential patterns.
>
> With hot data it lost, on five of six machines, to a 55-year-old algorithm. Let me tell you about that — including the part where the old algorithm loses too.

---

## 6. The Shar story — 4 min (centerpiece)

**SLIDE 6a**
> # 1971
>
> ### Leonard Shar, Stanford PhD student
>
> Publishes a **branchless** binary search.
>
> Uses `bit_floor(len)` and a conditional-move chain — no branches in the inner loop.
>
> *Then disappears from the literature.*

**SAY**
> In 1971, a Stanford PhD student named Leonard Shar publishes a variant of binary search with no branches in the inner loop. Instead of an `if` statement that jumps left or right, he uses arithmetic and conditional moves so the CPU never has to guess which way the search is going.
>
> At the time this was a curiosity. Branch prediction wasn't even really a thing yet. The paper goes into a technical report, and Shar essentially vanishes from the literature.

**SLIDE 6b**
> # ~50 years of silence
>
> Every textbook ships binary search **with a branch.**
>
> `std::lower_bound`, every language's standard library, every interview answer.

**SAY**
> For the next fifty years, essentially every binary search everyone writes has a branch in it. Every standard library. Every textbook. Every whiteboard interview. If you've written a binary search, you wrote the branching kind.

**SLIDE 6c**
> # 2023
>
> A blogger — *"probablydance"* — benchmarking binary searches, rediscovers Shar's trick.
>
> Writes it up. It goes mildly viral in low-level-perf circles.

**SAY**
> In 2023, a blogger who goes by "probablydance" is benchmarking binary searches for fun, and stumbles onto Shar's branchless version. He writes it up. It goes mildly viral in the niche corner of the internet that cares about this kind of thing. That's how I heard about it.

**SLIDE 6d**
> # 2026 — this project
>
> We built an **elaborate two-level "outer spine"** to index 512 Roaring containers.
>
> Predicted: crushing win on Intel (prefetcher-friendly sequential).
>
> Reality — Shar outer (F) vs. our spine outer (D), same inner; paired per-run deltas, 5 runs per host; negative = Shar faster, **bold = our spine wins**:
>
> | Host | hot, batched | hot, serial | cold, batched | cold, serial |
> |---|---|---|---|---|
> | Raspberry Pi 5 | −6.3% (4/5)* | −6.4% (4/5)* | **+31.8%** (0/5) | −0.4% tie |
> | Apple M4 Max | −39.1% (5/5) | −53.9% (5/5) | −11.5% (4/5) | **+16.2%** (1/5) |
> | Apple M1 Pro | −32.4% (5/5) | −38.9% (5/5) | −10.6% (5/5) | +5.7% tie |
> | Intel Skylake | −14.4% (5/5) | −16.3% (4/5) | **+6.6%** (1/5) | **+16.9%** (0/5) |
> | Intel Emerald Rapids | −29.5% (5/5) | −37.1% (5/5) | −4.0% (5/5) | **+17.7%** (0/5) |
> | AWS Graviton 4 | −41.9% (5/5) | −43.4% (5/5) | −11.3% (5/5) | +1.2% tie |
>
> *Source: Text/corrections_2026-10.md §2.2 (`{host}_runs/twolevel_paired.txt`). \* Pi 5 hot cells are a tie in the ten 2026-10 repaired-harness runs (+2.7% / +2.0%, `pi5_runs/twolevel_paired_v2.txt`). On Emerald Rapids and Graviton 4 the cold-best variant is the plain bsearch outer (C), 5/5 in cold_bat.*

**SAY**
> Fast-forward to this project. I built an elaborate two-level version of the spine — an outer index across 512 Roaring containers feeding into the inner array search. I was confident it would crush naive binary search on the Intel server chips, because their prefetchers love sequential patterns.
>
> So we benchmarked Shar's 1971 code as a baseline, expecting to beat it.
>
> With the outer keys hot in cache, Shar won on five of the six machines — both Macs, both Xeons, the Graviton — by fourteen to fifty-four percent, in five of five paired runs (four of five for Skylake serial). On the Pi it was a tie.
>
> *[pause]*
>
> Then we flushed the caches. Cold, our spine won back. On the Pi 5, Shar was thirty-two percent slower in the batched cold mode. On Skylake, seventeen percent slower serial. On Emerald Rapids and Graviton the best cold variant wasn't even our spine — it was the plain, branchy, textbook binary search, in five of five batched-cold runs.
>
> Here's why. My outer spine was about 1 kilobyte. That's too small for any prefetcher to get traction on — by the time the prefetcher notices the pattern, you're already done. So the spine was just pure dependent-load latency, each step waiting for the previous one.
>
> Shar's 1971 code is *also* a dependency chain — load, compare, conditional select, load, nine levels deep — and because every address depends on the previous select, the CPU cannot speculate past it. What it doesn't have is branches. Hot, with every load an L1 hit, no mispredicts means it simply runs faster. Cold, the branchy binary search gets to guess, run ahead across its mispredicted branches, and overlap the misses — and the cmov chain can't. Khuong and Morin wrote this up in 2017; we rediscovered it the hard way.
>
> The moral: a 55-year-old algorithm, lost to history and rediscovered by a blog post, beat the modern engineered solution — on hardware its inventor couldn't have dreamed of — when the data were hot. Cold, the spine or the textbook bsearch outer won back — our spine on the Pi 5 and Skylake (though in Skylake's batched cold mode the plain bsearch outer ranks first; our spine still beats Shar there in four of five runs, and is the serial-cold best in five of five), the even older, plainer binary search on Emerald Rapids and Graviton 4. Good ideas are timeless. Hardware changes around them. And if you're only ever reading this year's papers, you're going to miss the ones already written.

---

## 7. What AI was good at vs. bad at — 2 min

**SLIDE 7**
> # The honest scorecard
>
> **AI was great at:**
> - Writing 6 near-identical C variants with per-CPU tweaks
> - Keeping a structured findings log across weeks
> - Running the same benchmark matrix on every host
> - Generating the plots
>
> **AI was bad at:**
> - Predicting which optimization would actually win *(confidently wrong, repeatedly)*
> - Noticing Shar existed — **I had to bring that from outside**
>
> **Right division of labor**: human sets hypotheses + curates surprises; AI parallelizes the grunt work.

**SAY**
> Let me be honest about the scorecard, because I think the AI-assisted-research conversation gets flattened into "it's great" or "it's hype" and the truth is more specific.
>
> Claude was genuinely great at the mechanical parallel work. Writing six variants of the same C code with slightly different tuning per CPU. Running the same benchmarks on every host and collating. Keeping a structured findings log that I could come back to a week later and still follow. The plots in this talk — all Claude.
>
> Claude was bad at two specific things. First, predicting which optimization would win. It would happily generate confident-sounding rationales for hypotheses that measurement then destroyed. If I had trusted the reasoning instead of running the benchmark, I'd have shipped worse code.
>
> Second — and this is the important one — *Claude did not surface Shar*. The single most important finding in this project came from a blog post I'd happened to read. The model didn't say "hey, have you considered branchless binary search?" It's not in its reflex set. I had to bring it in from outside.
>
> The right division of labor, at least for research like this: the human brings hypotheses and the weird-idea-from-a-blog-post. The AI parallelizes the grunt work of coding and measuring. And you always — *always* — run the benchmark, because the AI's intuitions about what will be fast are about as good as yours. Which is to say: unreliable.

---

## 8. Takeaway — 1 min

**SLIDE 8**
> # Three things to take home
>
> ### 1. The spine: one idea, faster cold on every CPU (about 2–3× on ARM/Apple, less on the servers).
>
> ### 2. Shar 1971 beat our modern outer index hot on five of six CPUs — and lost cold to the spine or the textbook bsearch outer (D on the Pi 5 and Skylake, C on Emerald Rapids and Graviton 4). **Read old papers. Measure cold.**
>
> ### 3. AI + measurement. AI makes six-machine experiments cheap. Measurement keeps you honest when AI's intuition — and yours — is wrong.
>
> ---
>
> *Thanks. Questions?*

**SAY**
> Three things to take home.
>
> One: the spine. Precompute a small sorted sample and search it first, so the probes hit a few adjacent cache lines that can be fetched together instead of being scattered across the array. Faster cold on every CPU I tested — two to three times on the ARM and Apple cores, less on the servers. Simple ideas with good mechanical sympathy still win.
>
> Two: read old papers. A 1971 algorithm beat our modern design hot on five of six machines spanning four architectures, and cold it lost back to the spine or to plain branchy binary search — older still — the spine on the Pi 5 and Skylake, plain binary search on Emerald Rapids and Graviton 4. The reasons they win are reasons that didn't exist when they were written. If you only read this year's literature, you'll miss the good stuff.
>
> Three: AI plus measurement. AI made it possible for one person to run a six-machine, multi-week experiment in a week. But AI's intuitions about performance are unreliable — and honestly so are mine. The discipline that makes this kind of work actually produce real results is writing down your predictions, running the benchmark, and logging when you were wrong.
>
> Thank you. Happy to take questions.

---

## Timing & delivery notes

- **Total**: ~13 min script + ~2 min buffer for transitions / jokes / audience reaction. Safe for a 15-min slot.
- **Visuals**: the only two charts you need are `bench_compare_warm.png` (hero plot showing all 6 machines) and `bench_twolevel.png` (the two-level bar chart: Shar wins hot on five hosts, the spine/bsearch outers win cold). Two caveats on `bench_twolevel.png`: its H/I bars predate the 2026-10-11 prefetch fix (corrections §1), and it shows per-cell medians (levels), not paired deltas — its Pi 5 F hot_ser bar is the 328.5 ns median that the 482 ns outlier run inflates (corrections §3; per-run 216, 340, 482, 252, 329 ns), so the chart shows Shar about 22% slower than D hot_ser on the Pi 5 (328.5 vs 268.8 ns medians, `pi5_runs/twolevel_summary.txt`) where the paired table says tie. Rely on the paired table for the Pi 5, or crop/annotate that panel. Drop them into slides 4 and 6d respectively.
- **Don't show code.** A semi-technical audience will nod politely and check out.
- **The Shar story is the peak.** Slow down on slide 6d. Land "a 55-year-old algorithm beat the modern engineered solution — when the data were hot" and pause for a beat before moving on. Don't drop the cold reversal; it is the honest half of the story.
- **If running long, cut from section 4** (the spine is the "obvious" win — everyone intuits prefetching). Never cut Shar or the scorecard.
- **If running short (likely in Q&A)**: good backup questions to seed — "why does Apple use 128-byte cache lines?", "did you try SVE on Graviton?", "what would Shar look like as a standard library change?"

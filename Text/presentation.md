# Quad Search Presentation — Planning & Script

A 15-minute talk on the QuadSearch project, focused on AI-assisted CS research and the Shar algorithm archaeology story. Semi-technical audience.

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

**4. Finding #1: the "spine" — one idea beats everything (2 min)**
- Problem: quaternary search does 3 dependent loads before it can even start looking. On cold cache = 3 DRAM round-trips.
- Fix: precompute a tiny "spine" of sample points. Stride-prefetcher-friendly sequential read.
- Result: ~2–3× faster cold on every CPU. One idea, universal win.
- *This is the part where AI was great* — writing 6 variants of the same idea tuned per-uarch is boring, mechanical, and exactly where models excel.

**5. Finding #2: where intuition was wrong (2 min) — "lowlights"**
- Predicted the in-loop prefetch would help on modern chips. On M4/Emerald/Graviton it actively hurt (+10% slowdown). Wide out-of-order cores already overlap the miss — the prefetch just burns issue slots.
- Predicted Skylake would win biggest from unrolling. Measured: ~1.5%. Compiler already did it.
- **Point**: Claude proposed plausible-sounding hypotheses confidently. Benchmarks disagreed. The discipline is *always run it*.

**6. The Shar archaeology story (4 min — the centerpiece)**
Tell it as a story:
- **1971**: Leonard Shar, Stanford PhD student, publishes a branchless binary search. Uses `bit_floor(len)` and a conditional-move chain. No paper trail after.
- **~50 years of silence.** Everyone ships textbook binary search with a branch.
- **2023**: A blogger ("probablydance") is benchmarking binary searches, stumbles onto Shar's trick, writes it up.
- **2026 (this project)**: We built an elaborate "outer spine" — a precomputed index across 512 Roaring containers — and predicted it would crush naive binary search on Intel server chips, because streamers love sequential patterns.
- **It didn't.** On every single host — Pi 5, M1, M4, both Xeons, Graviton — Shar's 1971 cmov chain beat our fancy spine. On Emerald Rapids: 40% faster cold. On Graviton: 53% faster.
- **Why**: 512 keys × 2 bytes = 1 KB. Too small for any prefetcher to matter. The "spine" is pure dependent-load latency. Shar's 9 independent loads all issue in parallel on any modern wide core.
- **Moral**: a 55-year-old algorithm, lost and rediscovered by a blog post, beat the modern engineered solution on hardware its inventor couldn't have imagined. Good ideas are timeless; hardware changes around them.

**7. What AI was good at vs. bad at (2 min)**
- Writing 6 near-identical C variants with per-uarch tweaks (yes)
- Keeping a structured findings log across weeks of sessions (yes)
- Running the same benchmark matrix on every host, producing plots (yes)
- Predicting which optimization would win (confidently wrong, repeatedly) (no)
- Noticing the Shar option existed — *I had to bring that from outside* (no)
- The right division of labor: human sets hypotheses + curates the "what was surprising" log; AI parallelizes the grunt work of coding + measuring.

**8. Takeaway slide (1 min)**
Three lines:
1. The spine: one idea, 2–3× faster on every CPU.
2. Shar 1971 beat every modern design we tried. Read old papers.
3. AI + measurement: AI makes 6-machine experiments cheap. Measurement keeps you honest when AI's intuition is wrong.

---

Couple of delivery notes:
- The Shar story is the emotional peak — land it with the "55-year-old algorithm beats the fancy new thing" line and pause.
- Have the 6-host comparison plot (`bench_compare_warm.png`) and the twolevel bar chart (`bench_twolevel.png`) as your two hero visuals. Don't show code.
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
> A few years ago Daniel Lemire published a SIMD trick called *quad search* that beats binary search on these arrays. I spent about a week with Claude trying to push it further — on six different CPUs, from a Raspberry Pi to Amazon's newest server chip. The punchline is going to be that a 55-year-old algorithm nobody remembers beat every clever thing we came up with. But first let me set the stage.

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
> # The "spine": one idea, universal win
>
> Quad search does **3 dependent loads** before the real work starts.
> Cold cache → 3 trips to DRAM.
>
> **Fix**: precompute a tiny sorted sample of the array. Scan it sequentially first.
>
> ### Result: 2–3× faster on every CPU.
> *(stride prefetchers love sequential reads)*

**SAY**
> The first big optimization — and the only one that wins on every machine — is something we called the "spine."
>
> Quad search works by picking probe points, loading them, and using the result to pick the next set of probe points. That's three dependent memory loads before you even start looking for your answer. On a cold cache that's three separate trips to main memory. That's slow.
>
> The fix: precompute a tiny sampled version of the array — just a few hundred bytes — and scan it sequentially before diving into the real array. The reason this works is that every modern CPU has a hardware "stride prefetcher" that watches for sequential access patterns and pulls the next cache line before you ask for it. By giving it a sequential read pattern it can latch onto, the first loads become free.
>
> 2 to 3× faster cold on every single machine. One idea, universal win.
>
> This part is where AI was genuinely great — writing six tuned variants of the same idea, one per CPU, is mechanical work. Exactly the kind of thing I don't want to do by hand.

---

## 5. Lowlights: where intuition was wrong — 2 min

**SLIDE 5**
> # Where we were confidently wrong
>
> - *"Prefetching will help on the fast chips."*
>   → +10% **slower** on M4, Emerald Rapids, Graviton
>
> - *"Skylake will win biggest from loop unrolling."*
>   → measured: 1.5%. Compiler already did it.
>
> - *"Intel's prefetcher will love the 'outer spine' for two-level search."*
>   → It didn't. More on this in a moment.

**SAY**
> Here's the flipside. Three predictions I made — with Claude happily agreeing — that measurement destroyed.
>
> One: I thought adding a speculative prefetch inside the search loop would help on the modern wide-out-of-order chips. It actively hurt them by about 10%. The reason is that those chips are already overlapping the memory miss with other work on their own. The prefetch just burns an instruction slot it doesn't need.
>
> Two: I predicted Intel's Skylake Xeon would benefit most from unrolling a specific loop, because it has a narrower out-of-order window. Measured win: one and a half percent. GCC had already done the unrolling years ago.
>
> Three — and this is the setup for the main story — I predicted that a more elaborate *two-level* version of the spine would dominate on Intel, because Intel's hardware prefetchers are excellent at sequential patterns.
>
> It lost. Everywhere. To a 55-year-old algorithm. Let me tell you about that.

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
> Reality, measured on all 6 machines:
>
> | Host | Shar vs. our spine |
> |---|---|
> | Raspberry Pi 5 | −92% cold |
> | Apple M4 Max | −28% cold |
> | Apple M1 Pro | confirmed same |
> | Intel Skylake | −23% cold |
> | Intel Emerald Rapids | **−40% cold** |
> | AWS Graviton 4 | **−53% cold** |

**SAY**
> Fast-forward to this project. I built an elaborate two-level version of the spine — an outer index across 512 Roaring containers feeding into the inner array search. I was confident it would crush naive binary search on the Intel server chips, because their prefetchers love sequential patterns.
>
> So we benchmarked Shar's 1971 code as a baseline, expecting to beat it.
>
> On every single machine — the Pi, both Macs, both Xeons, the Graviton — Shar won. On Emerald Rapids, Intel's newest server chip, Shar was 40% faster cold. On Graviton 4, Amazon's newest ARM chip, 53% faster.
>
> *[pause]*
>
> Here's why. My outer spine was about 1 kilobyte. That's too small for any prefetcher to get traction on — by the time the prefetcher notices the pattern, you're already done. So the spine was just pure dependent-load latency, each step waiting for the previous one.
>
> Shar's 1971 code, meanwhile, has about nine *independent* memory loads on its critical path. On a modern wide-out-of-order CPU — which Shar obviously couldn't have imagined in 1971 — those nine loads all issue in parallel. The critical path collapses.
>
> The moral: a 55-year-old algorithm, lost to history and rediscovered by a blog post, beat the modern engineered solution — on hardware its inventor couldn't have dreamed of. Good ideas are timeless. Hardware changes around them. And if you're only ever reading this year's papers, you're going to miss the ones already written.

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
> ### 1. The spine: one idea, 2–3× faster on every CPU.
>
> ### 2. Shar 1971 beat everything modern we tried. **Read old papers.**
>
> ### 3. AI + measurement. AI makes six-machine experiments cheap. Measurement keeps you honest when AI's intuition — and yours — is wrong.
>
> ---
>
> *Thanks. Questions?*

**SAY**
> Three things to take home.
>
> One: the spine. Precompute a small sorted sample, scan it sequentially first, let the hardware prefetcher do the work. Two to three times faster on every CPU I tested. Simple ideas with good mechanical sympathy still win.
>
> Two: read old papers. A 1971 algorithm beat every modern design we tried on six machines spanning four architectures. The reasons it wins are reasons that didn't exist when it was written. If you only read this year's literature, you'll miss the good stuff.
>
> Three: AI plus measurement. AI made it possible for one person to run a six-machine, multi-week experiment in a week. But AI's intuitions about performance are unreliable — and honestly so are mine. The discipline that makes this kind of work actually produce real results is writing down your predictions, running the benchmark, and logging when you were wrong.
>
> Thank you. Happy to take questions.

---

## Timing & delivery notes

- **Total**: ~13 min script + ~2 min buffer for transitions / jokes / audience reaction. Safe for a 15-min slot.
- **Visuals**: the only two charts you need are `bench_compare_warm.png` (hero plot showing all 6 machines) and `bench_twolevel.png` (the bar chart where Shar wins on every host). Drop them into slides 4 and 6d respectively.
- **Don't show code.** A semi-technical audience will nod politely and check out.
- **The Shar story is the peak.** Slow down on slide 6d. Land "a 55-year-old algorithm beat the modern engineered solution" and pause for a beat before moving on.
- **If running long, cut from section 4** (the spine is the "obvious" win — everyone intuits prefetching). Never cut Shar or the scorecard.
- **If running short (likely in Q&A)**: good backup questions to seed — "why does Apple use 128-byte cache lines?", "did you try SVE on Graviton?", "what would Shar look like as a standard library change?"

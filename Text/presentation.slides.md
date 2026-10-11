---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 28px;
  }
  section.title {
    text-align: center;
    justify-content: center;
  }
  section.title h1 {
    font-size: 60px;
  }
  section.title h3 {
    font-weight: 300;
    color: #555;
  }
  h1 { color: #1a1a1a; }
  h2 { color: #2a2a2a; }
  strong { color: #c0392b; }
  em { color: #2980b9; }
  table {
    margin: 0 auto;
    font-size: 24px;
  }
  th { background: #f0f0f0; }
  blockquote {
    border-left: 4px solid #c0392b;
    padding-left: 16px;
    color: #333;
  }
  .big {
    font-size: 40px;
    text-align: center;
    margin-top: 40px;
  }
  .pause {
    color: #888;
    font-style: italic;
    text-align: center;
  }
---

<!-- _class: title -->

# Making search faster on 6 different CPUs

### …and what a 1971 algorithm taught me about AI-assisted research

*your name · date*

<p class="pause">Corrected 2026-10-11 against Text/corrections_2026-10.md; earlier numbers were retracted, see that file.</p>

<!--
Speaker notes:
(Deck corrected 2026-10-11 against Text/corrections_2026-10.md. Two-level numbers are paired per-run deltas, 5 archived runs per host ({host}_runs/twolevel_paired.txt), Pi 5 also re-run 10x with the repaired harness (pi5_runs/twolevel_paired_v2.txt). Main-bench numbers are 5-run medians from bench_table.txt.)

Roaring Bitmaps are how Elasticsearch, Druid, and ClickHouse compress sets of integers. Inside every Roaring Bitmap are thousands of tiny sorted arrays of 16-bit numbers. Searching those arrays faster makes all of those systems faster.

Earlier this year Daniel Lemire published a SIMD trick called quad search that beats binary search on these arrays. I spent about a week with Claude trying to push it further — on six different CPUs, from a Raspberry Pi to Amazon's newest server chip.

The punchline is going to be that a 55-year-old algorithm nobody remembers beat the clever index we built — at least while the data are hot. But first let me set the stage.
-->

---

# Six very different CPUs

|  | Cache line | SIMD | OoO width |
|---|---|---|---|
| Raspberry Pi 5 | 64 B | 128-bit NEON | narrow |
| Apple M1 Pro | 128 B | 128-bit NEON | wide |
| Apple M4 Max | 128 B | 128-bit NEON | wide |
| Intel Skylake Xeon | 64 B | 512-bit AVX | medium |
| Intel Emerald Rapids | 64 B | 512-bit AVX | wide |
| AWS Graviton 4 | 64 B | 128-bit NEON | wide |

<div class="big"><strong>No single answer works on all of them.</strong></div>

<!--
These six machines look similar on a spec sheet but they differ on three axes that turn out to matter: cache line size, SIMD width, and out-of-order width — how many instructions the CPU juggles in flight.

Apple's chips have 128-byte cache lines — twice everyone else. Intel has 512-bit vector registers — four times the ARM chips. And OoO width varies by almost 3×.

Why this matters: every optimization I'll talk about wins on some of these and loses on others. There is no universal best code.
-->

---

# The workflow

### **Me**: hypotheses, priorities, weird ideas from outside

### **Claude**: per-CPU variants, benchmarks, findings log

<br>

The findings log tracks **both** what worked **and** predictions that got refuted.

<!--
Here's how the collaboration actually worked. I'd come in with a hypothesis — "I bet prefetching helps on this chip" — and Claude would write the variant, run it on the relevant host, and add a line to a running findings log that lives in the repo. By the end of the week that log was the real artifact of the project.

The critical discipline — and this is easy to get wrong — was writing down REFUTED predictions, not just confirmed ones. If you only record your wins, you end up believing your own theory about why code is fast, when the honest answer is "measurement disagreed with me three times and I changed my mind."

Claude is very good at producing confident-sounding hypotheses. The only thing that keeps you honest is a log that says "predicted X, measured not-X."
-->

---

# The "spine": one idea, one direction on every CPU

Quad search does **3 dependent loads** before the real work starts.
Cold cache → 3 trips to DRAM.

<br>

**Fix**: precompute a tiny sorted sample of the array. Scan it *sequentially* first.

<div class="big">Result: <strong>faster cold on every CPU</strong> — about 2–3× on ARM/Apple, under 2× on the servers.</div>

<p class="pause">(memory-level parallelism over a 256-byte contiguous read — too short to train a stride prefetcher; bench_table.txt n=4096 medians, within-host only — bench.cpp's cold column is unflushed)</p>

<!--
The first big optimization — and the only one that wins on every machine, at least for full-size containers — is the "spine."

Quad search picks probe points, loads them, uses the result to pick the next set of probe points. That's three dependent memory loads before you even start looking. On a cold cache that's three separate trips to main memory. Slow.

Fix: precompute a tiny sampled version of the array — just a few hundred bytes — and search that first before diving into the real array. This is not the hardware prefetcher at work: a 256-byte spine is too short to train a stride prefetcher. The probes now land in a handful of adjacent cache lines instead of being scattered across eight kilobytes, so the CPU can have those few lines in flight at once — memory-level parallelism over a short contiguous read — instead of paying a full memory round trip for every dependent probe.

Faster cold on every single machine — roughly two to three times on the Pi and the Macs, less than two times on the Xeons and the Graviton (bench_table.txt, cold n=4096, non-spine -> spine: Pi 5 299.0 -> 150.7 ns, M4 Max 16.8 -> 6.5, M1 Pro 37.1 -> 11.1, Skylake 180.9 -> 132.7, Emerald Rapids 64.9 -> 37.2, Graviton 4 65.0 -> 34.6). One idea, one direction everywhere.

This is where AI was genuinely great — writing six tuned variants of the same idea, one per CPU, is mechanical work. Exactly what I don't want to do by hand.
-->

---

# Where we were confidently wrong

- *"Prefetching will help on the fast chips."*
  → **slower** on Graviton 4 (up to +10.8% warm), dropped on M4 and Emerald Rapids — and a net loss on the Pi 5 too, where we had logged it as a win

<br>

- *"Skylake will win biggest from loop unrolling."*
  → the unroll: ~1.5%. The hybrid that replaced it: −32% warm (5/5), **+40% slower cold at the median** (hybrid faster in only 2 of 5 runs; per-run −12% to +62%, `skx_runs/hybrid_run*.txt` `4096*` rows; corrections §2.3). Warm and cold disagree.

<br>

- *"Intel's prefetcher will love the 'outer spine' for two-level search."*
  → It didn't — hot. Cold is another story. *More on this in a moment.*

<!--
The flipside. Three predictions I made — with Claude happily agreeing — that measurement destroyed.

One: speculative prefetch inside the search loop. I thought it would help on modern wide-OoO chips. It didn't: on Graviton 4 the build with the prefetch is slower, up to eleven percent warm at n=2048 (gv4_runs/ab_summary.txt), and on M4 and Emerald Rapids we dropped it. Those chips already overlap the memory miss on their own; the prefetch just burns an instruction slot. The embarrassing part: on the Raspberry Pi, where we had written down a 10-25% cold win, the archived data say the prefetch is a net loss there too — the Graviton kernel is the Pi 5 kernel minus that prefetch and is faster cold at 13 of 14 sizes from n=128 up (corrections §5). Nobody had run the A/B.

Two: I predicted Intel's Skylake Xeon would benefit most from unrolling — narrower OoO window. The unroll gave about 1.5% (corrections §2.3). The hybrid finish that replaced it is 32% faster warm, 5/5 — and +40% slower cold at the median (hybrid faster in only 2 of 5 runs; per-run −12% to +62%, skx_runs/hybrid_run*.txt 4096* rows; corrections §2.3), against a general-n control stable to ±0.6% in the same runs. Warm and cold disagree, and we don't yet know why.

Three — the setup for the main story — I predicted an elaborate two-level spine would dominate on Intel, because Intel's prefetchers love sequential patterns.

With hot data it lost, on five of six machines, to a 55-year-old algorithm. Let me tell you about that — including the part where the old algorithm loses too.
-->

---

# 1971

## Leonard Shar, Stanford PhD student

Publishes a **branchless** binary search.

Uses `bit_floor(len)` and a conditional-move chain — no branches in the inner loop.

<br>

*Then disappears from the literature.*

<!--
1971. Stanford PhD student Leonard Shar publishes a variant of binary search with no branches in the inner loop. Instead of an if-statement that jumps left or right, he uses arithmetic and conditional moves so the CPU never has to guess which way the search is going.

At the time this was a curiosity. Branch prediction wasn't even really a thing yet. The paper goes into a technical report, and Shar essentially vanishes from the literature.
-->

---

# ~50 years of silence

<div class="big">Every textbook ships binary search <strong>with a branch.</strong></div>

<br>

`std::lower_bound`, every language's standard library, every interview answer.

<!--
For the next fifty years, essentially every binary search everyone writes has a branch in it. Every standard library. Every textbook. Every whiteboard interview. If you've written a binary search, you wrote the branching kind.
-->

---

# 2023

A blogger — *"probablydance"* — benchmarking binary searches, **rediscovers Shar's trick.**

Writes it up. Goes mildly viral in low-level-perf circles.

<!--
2023. A blogger who goes by "probablydance" is benchmarking binary searches for fun, stumbles onto Shar's branchless version, writes it up. It goes mildly viral in the niche corner of the internet that cares about this kind of thing. That's how I heard about it.
-->

---

# 2026 — this project

We built an **elaborate two-level "outer spine"** indexing 512 Roaring containers.

*Predicted:* crushing win on Intel (prefetcher-friendly sequential).

### Reality: Shar outer vs. our spine outer (paired, 5 runs/host; negative = Shar faster)

| Host | hot, serial | cold, batched | cold, serial |
|---|---|---|---|
| Raspberry Pi 5 | −6.4% (4/5)* | **+31.8%** (0/5) | −0.4% tie |
| Apple M4 Max | −53.9% (5/5) | −11.5% (4/5) | **+16.2%** (1/5) |
| Apple M1 Pro | −38.9% (5/5) | −10.6% (5/5) | +5.7% tie |
| Intel Skylake | −16.3% (4/5) | **+6.6%** (1/5) | **+16.9%** (0/5) |
| Intel Emerald Rapids | −37.1% (5/5) | −4.0% (5/5) | **+17.7%** (0/5) |
| AWS Graviton 4 | −43.4% (5/5) | −11.3% (5/5) | +1.2% tie |

<p class="pause">Red = our spine wins. Text/corrections_2026-10.md §2.2 ({host}_runs/twolevel_paired.txt). * tie in the ten 2026-10 repaired-harness Pi 5 runs.</p>

<!--
Fast-forward to this project. I built an elaborate two-level version of the spine — an outer index across 512 Roaring containers feeding into the inner array search. I was confident it would crush naive binary search on Intel server chips — their prefetchers love sequential patterns.

We benchmarked Shar's 1971 code as a baseline, expecting to beat it.

With the outer keys hot in cache, Shar won on five of the six machines — both Macs, both Xeons, the Graviton — by fourteen to fifty-four percent, in five of five paired runs — four of five for Skylake serial (hot_bat is the same story: −14.4% to −41.9%, 5/5). On the Pi it was a tie.

[PAUSE]

Then we flushed the caches. Cold, our spine won back. On the Pi 5, Shar was thirty-two percent slower in the batched cold mode (forty-five percent in the ten repaired-harness runs). On Skylake, seventeen percent slower serial. On Emerald Rapids and Graviton the best cold variant wasn't even our spine — it was the plain, branchy, textbook binary-search outer, in five of five batched-cold runs (corrections §2.1).

Here's why. My outer spine was about 1 kilobyte. Too small for any prefetcher to get traction on — by the time it notices the pattern, you're already done. So the spine was just pure dependent-load latency, each step waiting for the previous one.

Shar's 1971 code is ALSO a dependency chain — load, compare, conditional select, load, nine levels deep — and because every address depends on the previous select, the CPU cannot speculate past it. What it doesn't have is branches. Hot, with every load an L1 hit, no mispredicts means it simply runs faster. Cold, the branchy binary search gets to guess, run ahead across its mispredicted branches and overlap the misses — and the cmov chain can't. Khuong and Morin wrote this up in 2017; we rediscovered it the hard way (corrections §5).
-->

---

<!-- _class: title -->

## A 55-year-old algorithm,
## lost to history,
## rediscovered by a blog post —
## beat the modern engineered solution
## on hardware its inventor couldn't have dreamed of —
## *when the data were hot.*

<br>

### Good ideas are timeless. Hardware changes around them. Where your data live decides which one wins.

<!--
Land this slowly. Let the punchline breathe.

Then the cold half, in one breath: flush the caches and the spine or the textbook branchy search wins back — our spine (D) on the Pi 5 and Skylake (on Skylake's batched cold mode plain bsearch C ranks first; D still beats Shar 4/5 and is the serial-cold best 5/5), plain bsearch (C) on Emerald Rapids and Graviton 4. Don't skip it — it is the honest half of the story.

Moral: if you're only ever reading this year's papers, you're going to miss the ones already written.
-->

---

# The honest scorecard

### AI was **great** at:
- Writing 6 near-identical C variants with per-CPU tweaks
- Keeping a structured findings log across weeks
- Running the same benchmark matrix on every host
- Generating the plots

### AI was **bad** at:
- Predicting which optimization would actually win *(confidently wrong, repeatedly)*
- Noticing Shar existed — **I had to bring that from outside**

<br>

**Right division of labor**: human brings hypotheses + curates surprises; AI parallelizes the grunt work.

<!--
The AI-assisted-research conversation gets flattened into "it's great" or "it's hype" — truth is more specific.

Claude was genuinely great at mechanical parallel work. Six variants of the same C code with slightly different tuning per CPU. Running benchmarks on every host and collating. Keeping a structured findings log I could come back to a week later and still follow. The plots in this talk — all Claude.

Claude was bad at two specific things. First: predicting which optimization would win. Happily generated confident rationales for hypotheses that measurement destroyed. If I'd trusted the reasoning instead of running the benchmark, I'd have shipped worse code.

Second — and this is the important one — Claude did NOT surface Shar. The single most important finding in this project came from a blog post I'd happened to read. The model didn't say "hey, have you considered branchless binary search?" Not in its reflex set. I had to bring it from outside.

The right division of labor for research like this: human brings hypotheses and the weird-idea-from-a-blog-post. AI parallelizes coding and measuring. And you always — always — run the benchmark, because the AI's intuitions about what will be fast are about as good as yours. Which is to say: unreliable.
-->

---

# Three things to take home

### 1. The spine: one idea, **faster cold on every CPU** (about 2–3× on ARM/Apple, less on the servers).

### 2. Shar 1971 beat our modern outer index hot on five of six CPUs — and lost cold to the spine or the textbook bsearch outer (D on the Pi 5 and Skylake, C on Emerald Rapids and Graviton 4). **Read old papers. Measure cold.**

### 3. AI + measurement. AI makes six-machine experiments cheap. Measurement keeps you honest when AI's intuition — and yours — is wrong.

<br>

<div class="big"><em>Thanks. Questions?</em></div>

<!--
Three things to take home.

One: the spine. Precompute a small sorted sample and search it first, so the probes hit a few adjacent cache lines that can be fetched together instead of being scattered across the array. Faster cold on every CPU I tested — two to three times on the ARM and Apple cores, less on the servers. Simple ideas with good mechanical sympathy still win.

Two: read old papers. A 1971 algorithm beat our modern design hot on five of six machines spanning four architectures, and cold it lost back to the spine or to plain branchy binary search — older still — the spine on the Pi 5 and Skylake, plain binary search on Emerald Rapids and Graviton 4. The reasons they win are reasons that didn't exist when they were written. Only reading this year's literature, you'll miss the good stuff.

Three: AI plus measurement. AI made it possible for one person to run a six-machine, multi-week experiment in a week. But AI's intuitions about performance are unreliable — and honestly so are mine. The discipline that makes this work produce real results is writing down your predictions, running the benchmark, and logging when you were wrong.

Thank you. Happy to take questions.

Backup Qs to seed if asked:
- why does Apple use 128-byte cache lines?
- did you try SVE on Graviton?
- what would Shar look like as a standard library change?
-->

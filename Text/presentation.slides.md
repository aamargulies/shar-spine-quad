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

<!--
Speaker notes:
Roaring Bitmaps are how Elasticsearch, Druid, and ClickHouse compress sets of integers. Inside every Roaring Bitmap are thousands of tiny sorted arrays of 16-bit numbers. Searching those arrays faster makes all of those systems faster.

A few years ago Daniel Lemire published a SIMD trick called quad search that beats binary search on these arrays. I spent about a week with Claude trying to push it further — on six different CPUs, from a Raspberry Pi to Amazon's newest server chip.

The punchline is going to be that a 55-year-old algorithm nobody remembers beat every clever thing we came up with. But first let me set the stage.
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

# The "spine": one idea, universal win

Quad search does **3 dependent loads** before the real work starts.
Cold cache → 3 trips to DRAM.

<br>

**Fix**: precompute a tiny sorted sample of the array. Scan it *sequentially* first.

<div class="big">Result: <strong>2–3× faster</strong> on every CPU.</div>

<p class="pause">(stride prefetchers love sequential reads)</p>

<!--
The first big optimization — and the only one that wins on every machine — is the "spine."

Quad search picks probe points, loads them, uses the result to pick the next set of probe points. That's three dependent memory loads before you even start looking. On a cold cache that's three separate trips to main memory. Slow.

Fix: precompute a tiny sampled version of the array — just a few hundred bytes — and scan it sequentially before diving into the real array. Every modern CPU has a hardware "stride prefetcher" that watches for sequential access patterns and pulls the next cache line before you ask for it. Give it a sequential pattern, the first loads become free.

2 to 3× faster cold on every single machine. One idea, universal win.

This is where AI was genuinely great — writing six tuned variants of the same idea, one per CPU, is mechanical work. Exactly what I don't want to do by hand.
-->

---

# Where we were confidently wrong

- *"Prefetching will help on the fast chips."*
  → +10% **slower** on M4, Emerald Rapids, Graviton

<br>

- *"Skylake will win biggest from loop unrolling."*
  → measured: **1.5%**. Compiler already did it.

<br>

- *"Intel's prefetcher will love the 'outer spine' for two-level search."*
  → It didn't. *More on this in a moment.*

<!--
The flipside. Three predictions I made — with Claude happily agreeing — that measurement destroyed.

One: speculative prefetch inside the search loop. I thought it would help on modern wide-OoO chips. It hurt them by 10%. Those chips are already overlapping the memory miss on their own. The prefetch just burns an instruction slot.

Two: I predicted Intel's Skylake Xeon would benefit most from unrolling — narrower OoO window. Measured win: 1.5%. GCC had already done it years ago.

Three — the setup for the main story — I predicted an elaborate two-level spine would dominate on Intel, because Intel's prefetchers love sequential patterns.

It lost. Everywhere. To a 55-year-old algorithm. Let me tell you about that.
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

### Reality, measured on all 6 machines:

| Host | Shar vs. our spine |
|---|---|
| Raspberry Pi 5 | −92% cold |
| Apple M4 Max | −28% cold |
| Apple M1 Pro | confirmed same |
| Intel Skylake | −23% cold |
| **Intel Emerald Rapids** | **−40% cold** |
| **AWS Graviton 4** | **−53% cold** |

<!--
Fast-forward to this project. I built an elaborate two-level version of the spine — an outer index across 512 Roaring containers feeding into the inner array search. I was confident it would crush naive binary search on Intel server chips — their prefetchers love sequential patterns.

We benchmarked Shar's 1971 code as a baseline, expecting to beat it.

On every single machine — the Pi, both Macs, both Xeons, the Graviton — Shar won. On Emerald Rapids, Intel's newest server chip, Shar was 40% faster cold. On Graviton 4, Amazon's newest ARM chip, 53% faster.

[PAUSE]

Here's why. My outer spine was about 1 kilobyte. Too small for any prefetcher to get traction on — by the time it notices the pattern, you're already done. So the spine was just pure dependent-load latency, each step waiting for the previous one.

Shar's 1971 code has about nine INDEPENDENT memory loads on its critical path. On a modern wide-out-of-order CPU — which Shar obviously couldn't have imagined in 1971 — those nine loads all issue in parallel. The critical path collapses.
-->

---

<!-- _class: title -->

## A 55-year-old algorithm,
## lost to history,
## rediscovered by a blog post —
## beat the modern engineered solution
## on hardware its inventor couldn't have dreamed of.

<br>

### Good ideas are timeless. Hardware changes around them.

<!--
Land this slowly. Let the punchline breathe.

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

### 1. The spine: one idea, **2–3× faster** on every CPU.

### 2. Shar 1971 beat everything modern we tried. **Read old papers.**

### 3. AI + measurement. AI makes six-machine experiments cheap. Measurement keeps you honest when AI's intuition — and yours — is wrong.

<br>

<div class="big"><em>Thanks. Questions?</em></div>

<!--
Three things to take home.

One: the spine. Precompute a small sorted sample, scan it sequentially first, let the hardware prefetcher do the work. 2–3× faster on every CPU I tested. Simple ideas with good mechanical sympathy still win.

Two: read old papers. A 1971 algorithm beat every modern design we tried on six machines spanning four architectures. The reasons it wins are reasons that didn't exist when it was written. Only reading this year's literature, you'll miss the good stuff.

Three: AI plus measurement. AI made it possible for one person to run a six-machine, multi-week experiment in a week. But AI's intuitions about performance are unreliable — and honestly so are mine. The discipline that makes this work produce real results is writing down your predictions, running the benchmark, and logging when you were wrong.

Thank you. Happy to take questions.

Backup Qs to seed if asked:
- why does Apple use 128-byte cache lines?
- did you try SVE on Graviton?
- what would Shar look like as a standard library change?
-->

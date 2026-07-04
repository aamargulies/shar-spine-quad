**Lemire's SIMD quad search** finds a target in a sorted `uint16_t` array (sized for Roaring Bitmap containers, up to 4,096 elements) by combining two tricks:

1. **Quaternary descent over block keys.** The array is split into blocks of 16 elements. The *last* element of each block is its "key" (the block's maximum). The keys form a sorted sub-array of 256 entries. Search this with a 4-way branchless step: pick probes at the ¼, ½, ¾ points, compare each to the target to get three 0/1 results `c₁, c₂, c₃`, then update the range with `base += (c₁ + c₂ + c₃) * quarter`. The sum (0–3) picks one of four quadrants arithmetically, so the inner loop has no data-dependent branches. Three iterations shrink 256 keys to one block.

2. **SIMD block check.** Once the right 16-element block is located, a single 128-bit vector compare (`vceqq_u16` on NEON, `_mm_cmpeq_epi16` on SSE2) tests all 16 elements against the target in parallel, then OR-reduces to a single "hit or no hit" answer.

**Why it beats `std::binary_search`:** binary search has a mispredicted branch on every step. Quad search replaces the branch chain with an arithmetic update on three independent compares per step (branch-predictor-friendly, wide-issue-friendly), and substitutes a single vector op for the final 16 element-wise comparisons. Three block keys are probed per step instead of one, so the range shrinks 4× per iteration instead of 2×.

**Cost model at n = 4096:** ~3 quaternary iterations over the 256 keys + a 2-probe binary tail + one SIMD compare. The critical path is short (a handful of dependent loads on the keys, one SIMD op at the end), which is exactly what the per-host variants in this project try to tune further via block-check width, gap size, prefetch, and the spine.

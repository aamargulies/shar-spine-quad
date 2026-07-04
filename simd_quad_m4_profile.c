// Profile harness companions for simd_quad_m4_spine_4096.
//
// Splits the n=4096 hybrid path into "descent only" and "block-load only"
// halves so a cold-cache micro-bench can attribute time to (a) the spine
// pointer-chase chain vs. (b) the demand block-load that follows.
//
// Build alongside simd_quad_m4.c; not linked into bench / bench_twolevel.

#include <stdbool.h>
#include <stdint.h>
#include <arm_neon.h>

// Descent only: same shape as simd_quad_m4_spine_4096 up through the
// branchless 4-probe finish, but returns `lo` directly instead of doing the
// 128-byte block-load + SIMD compare. Sink as int32_t so the caller can
// XOR-accumulate to defeat dead-store elimination.
int32_t simd_quad_m4_spine_4096_descent(const uint16_t *spine, uint16_t pos) {
    enum { num_blocks = 64 };
    __builtin_prefetch(spine);

    int32_t base = 0;
    {
        int32_t k1 = spine[base + 16];
        int32_t k2 = spine[base + 32];
        int32_t k3 = spine[base + 48];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * 16;
    }
    {
        int32_t k1 = spine[base + 4];
        int32_t k2 = spine[base + 8];
        int32_t k3 = spine[base + 12];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * 4;
    }
    int32_t lo = base
               + (spine[base    ] < pos)
               + (spine[base + 1] < pos)
               + (spine[base + 2] < pos)
               + (spine[base + 3] < pos);
    return lo;
}

// Block-load only: given a precomputed lo (the "right answer" from a prior
// descent), do exactly the SIMD block check. Same code path as the tail of
// simd_quad_m4_spine_4096.
bool simd_quad_m4_spine_4096_blkonly(const uint16_t *carr, int32_t lo,
                                     uint16_t pos) {
    enum { gap = 64, num_blocks = 64 };
    if (lo < num_blocks) {
        const uint16_t *blk = carr + lo * gap;
        uint16x8_t needle = vdupq_n_u16(pos);
        uint16x8x4_t a = vld1q_u16_x4(blk);
        uint16x8x4_t b = vld1q_u16_x4(blk + 32);
        uint16x8_t h0 = vorrq_u16(
            vorrq_u16(vceqq_u16(a.val[0], needle), vceqq_u16(a.val[1], needle)),
            vorrq_u16(vceqq_u16(a.val[2], needle), vceqq_u16(a.val[3], needle)));
        uint16x8_t h1 = vorrq_u16(
            vorrq_u16(vceqq_u16(b.val[0], needle), vceqq_u16(b.val[1], needle)),
            vorrq_u16(vceqq_u16(b.val[2], needle), vceqq_u16(b.val[3], needle)));
        return vmaxvq_u16(vorrq_u16(h0, h1)) != 0;
    }
    return false;
}

// Lever C scratch: shipping hybrid + 4-way candidate-block prefetch issued
// between iter 2 and the 4-probe finish. After iter 2, base ∈ [0, 60] and
// the eventual lo lies in {base, base+1, base+2, base+3}. We issue all 4
// candidate prefetches before reading spine[base..base+3] for the finish,
// so their DRAM round-trips overlap (i) the 4 dependent spine loads of the
// finish, (ii) the lo sum, (iii) the lo<num_blocks compare, and (iv) the
// blk pointer arithmetic before the demand vld1q_u16_x4 hits. Hit rate
// per query: 1/4 — exactly one of the prefetched lines is the demand
// block, the other 3 are wasted bandwidth. Issue-slot cost: 4 prfm.
//
// Why post-iter-2 and not post-iter-1: post-iter-1 gives 16 candidates
// (lo ∈ [base, base+16) where base ∈ {0,16,32,48}), so 4 prefetches
// would cover only 4/16 = 1/4 of the candidate space at best — but those
// 4 prefetches don't pick out blocks that are correlated with the
// iter-2 outcome, so the actual hit rate degrades to ~1/16. Post-iter-2
// is the cleanest "1/4 hit rate, real overlap" placement.
//
// If this beats the shipping hybrid cold by enough to justify the wasted
// BW + issue slots, we lift it into simd_quad_m4.c proper.
bool simd_quad_m4_spine_4096_pfC(const uint16_t *carr, const uint16_t *spine,
                                 uint16_t pos) {
    enum { gap = 64, num_blocks = 64 };

    __builtin_prefetch(spine);

    int32_t base = 0;
    {
        int32_t k1 = spine[base + 16];
        int32_t k2 = spine[base + 32];
        int32_t k3 = spine[base + 48];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * 16;
    }
    {
        int32_t k1 = spine[base + 4];
        int32_t k2 = spine[base + 8];
        int32_t k3 = spine[base + 12];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * 4;
    }
    // Post-iter-2 4-way candidate prefetch: lo ∈ {base, base+1, base+2,
    // base+3}; issue all 4 before the finish so DRAM overlaps the finish
    // + bookkeeping.
    __builtin_prefetch(carr + (base    ) * gap);
    __builtin_prefetch(carr + (base + 1) * gap);
    __builtin_prefetch(carr + (base + 2) * gap);
    __builtin_prefetch(carr + (base + 3) * gap);
    int32_t lo = base
               + (spine[base    ] < pos)
               + (spine[base + 1] < pos)
               + (spine[base + 2] < pos)
               + (spine[base + 3] < pos);

    if (lo < num_blocks) {
        const uint16_t *blk = carr + lo * gap;
        uint16x8_t needle = vdupq_n_u16(pos);
        uint16x8x4_t a = vld1q_u16_x4(blk);
        uint16x8x4_t b = vld1q_u16_x4(blk + 32);
        uint16x8_t h0 = vorrq_u16(
            vorrq_u16(vceqq_u16(a.val[0], needle), vceqq_u16(a.val[1], needle)),
            vorrq_u16(vceqq_u16(a.val[2], needle), vceqq_u16(a.val[3], needle)));
        uint16x8_t h1 = vorrq_u16(
            vorrq_u16(vceqq_u16(b.val[0], needle), vceqq_u16(b.val[1], needle)),
            vorrq_u16(vceqq_u16(b.val[2], needle), vceqq_u16(b.val[3], needle)));
        return vmaxvq_u16(vorrq_u16(h0, h1)) != 0;
    }
    return false;
}

// Sentinel-spine scratch: parallel spine_lo[i] = first key of block i. After
// the 4-probe finish gives lo, we know pos ∈ (spine[lo-1], spine[lo]] — i.e.
// strictly greater than the previous block's last key, ≤ this block's last
// key. If pos < spine_lo[lo], pos falls in the *gap* between blocks (not in
// any block) — guaranteed miss, return false without touching carr.
// Otherwise pos ∈ [spine_lo[lo], spine[lo]] = the block's range, fall through
// to the SIMD block-load.
//
// For uniform-random u16 pos and n=4096: P(in-gap) = (65536-4096)/65536 ≈
// 94%. So 94% of cold queries pay descent cost (~8 ns) and skip the ~25 ns
// demand block-load. Predicted cold: 0.94·8 + 0.06·33 ≈ 9.5 ns vs current
// ~33 ns. Real Roaring use is more hit-heavy than uniform; harness must
// report realized miss-rate so we don't overclaim.
//
// Spine size doubles: 128 B (1 line on M1/M4) → 256 B (2 lines). This is
// what the dead "lever A — widen spine" was reaching for; the streamer
// latching a stride is now a side benefit, not the point.
void simd_quad_m4_build_spine_lo(const uint16_t *carr, int32_t cardinality,
                                 uint16_t *spine_lo) {
    enum { gap = 64 };
    int32_t num_blocks = cardinality / gap;
    for (int32_t i = 0; i < num_blocks; i++) {
        spine_lo[i] = carr[i * gap];
    }
}

bool simd_quad_m4_spine_4096_sentinel(const uint16_t *carr,
                                      const uint16_t *spine,
                                      const uint16_t *spine_lo,
                                      uint16_t pos) {
    enum { gap = 64, num_blocks = 64 };

    __builtin_prefetch(spine);
    __builtin_prefetch(spine_lo);

    int32_t base = 0;
    {
        int32_t k1 = spine[base + 16];
        int32_t k2 = spine[base + 32];
        int32_t k3 = spine[base + 48];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * 16;
    }
    {
        int32_t k1 = spine[base + 4];
        int32_t k2 = spine[base + 8];
        int32_t k3 = spine[base + 12];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * 4;
    }
    int32_t lo = base
               + (spine[base    ] < pos)
               + (spine[base + 1] < pos)
               + (spine[base + 2] < pos)
               + (spine[base + 3] < pos);

    if (lo >= num_blocks) return false;

    // Sentinel test: if pos < spine_lo[lo], pos is in the inter-block gap.
    if (pos < spine_lo[lo]) return false;

    const uint16_t *blk = carr + lo * gap;
    uint16x8_t needle = vdupq_n_u16(pos);
    uint16x8x4_t a = vld1q_u16_x4(blk);
    uint16x8x4_t b = vld1q_u16_x4(blk + 32);
    uint16x8_t h0 = vorrq_u16(
        vorrq_u16(vceqq_u16(a.val[0], needle), vceqq_u16(a.val[1], needle)),
        vorrq_u16(vceqq_u16(a.val[2], needle), vceqq_u16(a.val[3], needle)));
    uint16x8_t h1 = vorrq_u16(
        vorrq_u16(vceqq_u16(b.val[0], needle), vceqq_u16(b.val[1], needle)),
        vorrq_u16(vceqq_u16(b.val[2], needle), vceqq_u16(b.val[3], needle)));
    return vmaxvq_u16(vorrq_u16(h0, h1)) != 0;
}

// Sentinel-spine v2: interleaved layout. spine_2x[2*i] = first-of-block i,
// spine_2x[2*i+1] = last-of-block i. Total: 128 u16 = 256 B = 2 cache lines
// on M1/M4. The descent reads only the odd entries (last-of-block) at the
// same logical indices as the original spine — the access pattern through
// physical memory is now stride-4 (4 bytes between consecutive reads
// during the iter-1 quartile probes [16,32,48], iter-2 quartile probes
// [base+4, base+8, base+12], and the 4 finish probes).
//
// Hypothesis: the M1/M4 HW stream prefetcher latches a stride pattern
// across the 256 B during iter 1 and pulls in the second cache line by
// the time the gap test reads spine_2x[2*lo] (which lives on either line
// depending on lo). Compared to the separate-arrays sentinel (which adds
// an unconditional second cold-line fetch on the critical path), this
// version trades cold latency for the streamer's prefetch-during-descent
// overlap.
//
// Logical descent matches the original: spine_2x[2*(base+offset)+1] is
// the last-of-block at offset offset.
void simd_quad_m4_build_spine_2x(const uint16_t *carr, int32_t cardinality,
                                 uint16_t *spine_2x) {
    enum { gap = 64 };
    int32_t num_blocks = cardinality / gap;
    for (int32_t i = 0; i < num_blocks; i++) {
        spine_2x[2 * i    ] = carr[i * gap];           // first-of-block
        spine_2x[2 * i + 1] = carr[(i + 1) * gap - 1]; // last-of-block
    }
}

bool simd_quad_m4_spine_4096_sentinel_2x(const uint16_t *carr,
                                         const uint16_t *spine_2x,
                                         uint16_t pos) {
    enum { gap = 64, num_blocks = 64 };

    // Prefetch only the first line; rely on the HW streamer to pull in the
    // second line during the descent's stride pattern.
    __builtin_prefetch(spine_2x);

    int32_t base = 0;
    {
        int32_t k1 = spine_2x[2 * (base + 16) + 1];
        int32_t k2 = spine_2x[2 * (base + 32) + 1];
        int32_t k3 = spine_2x[2 * (base + 48) + 1];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * 16;
    }
    {
        int32_t k1 = spine_2x[2 * (base + 4) + 1];
        int32_t k2 = spine_2x[2 * (base + 8) + 1];
        int32_t k3 = spine_2x[2 * (base + 12) + 1];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * 4;
    }
    int32_t lo = base
               + (spine_2x[2 * (base    ) + 1] < pos)
               + (spine_2x[2 * (base + 1) + 1] < pos)
               + (spine_2x[2 * (base + 2) + 1] < pos)
               + (spine_2x[2 * (base + 3) + 1] < pos);

    if (lo >= num_blocks) return false;

    // Gap test against first-of-block (even index).
    if (pos < spine_2x[2 * lo]) return false;

    const uint16_t *blk = carr + lo * gap;
    uint16x8_t needle = vdupq_n_u16(pos);
    uint16x8x4_t a = vld1q_u16_x4(blk);
    uint16x8x4_t b = vld1q_u16_x4(blk + 32);
    uint16x8_t h0 = vorrq_u16(
        vorrq_u16(vceqq_u16(a.val[0], needle), vceqq_u16(a.val[1], needle)),
        vorrq_u16(vceqq_u16(a.val[2], needle), vceqq_u16(a.val[3], needle)));
    uint16x8_t h1 = vorrq_u16(
        vorrq_u16(vceqq_u16(b.val[0], needle), vceqq_u16(b.val[1], needle)),
        vorrq_u16(vceqq_u16(b.val[2], needle), vceqq_u16(b.val[3], needle)));
    return vmaxvq_u16(vorrq_u16(h0, h1)) != 0;
}

// General-n descent variant for comparison. n is hardcoded to 4096 inside
// (num_blocks=64) but the descent shape matches simd_quad_m4_spine: 3 quat
// tiers + binary tail + final-lo. Returns lo for sinking.
int32_t simd_quad_m4_spine_general_descent(const uint16_t *spine,
                                           uint16_t pos) {
    enum { num_blocks = 64 };
    __builtin_prefetch(spine);

    int32_t base = 0;
    int32_t n = num_blocks;
    while (n > 3) {
        int32_t quarter = n >> 2;
        int32_t k1 = spine[base + quarter];
        int32_t k2 = spine[base + 2 * quarter];
        int32_t k3 = spine[base + 3 * quarter];
        int32_t c1 = (k1 < pos);
        int32_t c2 = (k2 < pos);
        int32_t c3 = (k3 < pos);
        base += (c1 + c2 + c3) * quarter;
        n -= 3 * quarter;
    }
    while (n > 1) {
        int32_t half = n >> 1;
        base = (spine[base + half] < pos) ? base + half : base;
        n -= half;
    }
    int32_t lo = (spine[base] < pos) ? base + 1 : base;
    return lo;
}

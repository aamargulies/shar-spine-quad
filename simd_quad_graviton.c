#include <stdbool.h>
#include <stdint.h>
#include <arm_neon.h>

/*
 * AWS Graviton 4 (Arm Neoverse V2) variant of simd_quad.
 *
 * Graviton 4 (and anything else with the V2 core, e.g. NVIDIA Grace) is
 * what you get if you take the Pi 5's Cortex-A76 blueprint and crank
 * every uarch dial towards the Apple M4 Max:
 *
 *   - 64 B cache line (same as the A76 and Intel server parts).
 *   - 64 KB L1D, 2 MB private L2, big shared L3 (36 MB on the r8g instances
 *     this was measured on).
 *   - 128-bit NEON and 128-bit SVE2. On V2 the SVE vector length is 128
 *     bits, so there is no width advantage over NEON for this algorithm;
 *     we stay on NEON for ISA portability with the other two ARM hosts.
 *   - 4 load AGUs. Two more than the A76, one more than the M4. Combined
 *     with a very wide OoO window (ROB ~320 entries) and an aggressive
 *     stride prefetcher, it is the most memory-level-parallel ARM host
 *     in this project.
 *
 * Differences from the reference simd_quad.c SSE2 path:
 *   - Block size is 32 u16 = one 64-byte cache line. Same "one block =
 *     one line" structural argument as the Pi 5 variant. The cache line
 *     drives gap, not the SIMD register width.
 *   - The block check uses vld1q_u16_x2 (two paired 128-bit loads) with
 *     the four comparisons ORed together. With 4 load AGUs the paired
 *     load is trivial to issue; using a wider vld1q_u16_x4 would buy
 *     nothing because we only need 32 u16 = 64 B per block.
 *   - AArch64/NEON only; the reference SSE2 fallback is gone.
 *   - No speculative __builtin_prefetch inside the interpolation loop.
 *     The A76 kept it (10-25% cold win) because two load AGUs and a
 *     narrow OoO window leave room for a SW hint to pay off. On V2
 *     the ROB is deep enough and the L1/L2 streamers aggressive enough
 *     that the miss already overlaps with the current iteration's
 *     loads -- same regime as the M4 Max and Emerald Rapids, where the
 *     hint was a measurable regression. Measured on Graviton 4
 *     (2026-05-01): removing the in-loop prefetch is within noise at
 *     every size and slightly faster at n >= 1024 cold. We drop it.
 *   - Small-size fast paths for [8,16) and [16,32), same structure as
 *     the Pi 5 variant. No [32,64) tier because gap=32.
 */
bool simd_quad_graviton(const uint16_t *carr, int32_t cardinality,
                        uint16_t pos) {
    enum { gap = 32 };

    if (cardinality < gap) {
        if (cardinality >= 16) {
            // 16 <= n < 32: NEON-compare the first 16, sweep the remainder.
            uint16x8_t needle = vdupq_n_u16(pos);
            uint16x8x2_t v = vld1q_u16_x2(carr);
            uint16x8_t hit = vorrq_u16(vceqq_u16(v.val[0], needle),
                                       vceqq_u16(v.val[1], needle));
            if (vmaxvq_u16(hit) != 0) return true;
            for (int32_t j = 16; j < cardinality; j++) {
                uint16_t x = carr[j];
                if (x >= pos) return x == pos;
            }
            return false;
        }
        if (cardinality >= 8) {
            // 8 <= n < 16: single 128-bit NEON compare, sweep the remainder.
            uint16x8_t needle = vdupq_n_u16(pos);
            uint16x8_t v = vld1q_u16(carr);
            if (vmaxvq_u16(vceqq_u16(v, needle)) != 0) return true;
            for (int32_t j = 8; j < cardinality; j++) {
                uint16_t x = carr[j];
                if (x >= pos) return x == pos;
            }
            return false;
        }
        for (int32_t j = 0; j < cardinality; j++) {
            uint16_t v = carr[j];
            if (v >= pos) return v == pos;
        }
        return false;
    }

    int32_t num_blocks = cardinality / gap;
    int32_t base = 0;
    int32_t n = num_blocks;

    while (n > 3) {
        int32_t quarter = n >> 2;
        int32_t k1 = carr[(base + quarter + 1) * gap - 1];
        int32_t k2 = carr[(base + 2 * quarter + 1) * gap - 1];
        int32_t k3 = carr[(base + 3 * quarter + 1) * gap - 1];
        int32_t c1 = (k1 < pos);
        int32_t c2 = (k2 < pos);
        int32_t c3 = (k3 < pos);
        base += (c1 + c2 + c3) * quarter;
        n -= 3 * quarter;
    }
    while (n > 1) {
        int32_t half = n >> 1;
        base = (carr[(base + half + 1) * gap - 1] < pos) ? base + half : base;
        n -= half;
    }
    int32_t lo = (carr[(base + 1) * gap - 1] < pos) ? base + 1 : base;

    if (lo < num_blocks) {
        const uint16_t *blk = carr + lo * gap;
        uint16x8_t needle = vdupq_n_u16(pos);
        uint16x8x2_t a = vld1q_u16_x2(blk);
        uint16x8x2_t b = vld1q_u16_x2(blk + 16);
        uint16x8_t h0 = vceqq_u16(a.val[0], needle);
        uint16x8_t h1 = vceqq_u16(a.val[1], needle);
        uint16x8_t h2 = vceqq_u16(b.val[0], needle);
        uint16x8_t h3 = vceqq_u16(b.val[1], needle);
        uint16x8_t hit = vorrq_u16(vorrq_u16(h0, h1), vorrq_u16(h2, h3));
        return vmaxvq_u16(hit) != 0;
    }

    for (int32_t j = num_blocks * gap; j < cardinality; j++) {
        uint16_t v = carr[j];
        if (v >= pos) return v == pos;
    }
    return false;
}

/*
 * Spine variant, Graviton 4 edition.
 *
 * Same idea as the Pi 5 and M4 spine variants: pack the interpolation
 * probe keys into a dense contiguous region so the cold-cache pointer
 * chase streams through consecutive cache lines. gap=32 on a 64-byte
 * line gives the same spine footprint as the Pi 5 and the Intel hosts:
 *
 *   n=4096 -> 128 spine keys -> 256 B = 4 cache lines
 *   n=2048 ->  64 spine keys -> 128 B = 2 cache lines
 *   n=1024 ->  32 spine keys ->  64 B = 1 cache line
 *
 * The V2's stride prefetcher picks up the sequential spine scan
 * immediately, and the 4 load AGUs let the quaternary iteration issue
 * all three probe loads in the same cycle. The final SIMD block check
 * still loads from carr.
 *
 * num_blocks <= 3 fallback is identical to the NEON siblings: at tiny
 * num_blocks the plain carr-based probes accidentally prime the final
 * block's cache lines, which the spine path disrupts.
 */
bool simd_quad_graviton_spine(const uint16_t *carr, const uint16_t *spine,
                              int32_t cardinality, uint16_t pos) {
    enum { gap = 32 };

    if (cardinality < gap) {
        // Same fast paths as simd_quad_graviton -- spine is irrelevant here.
        if (cardinality >= 16) {
            uint16x8_t needle = vdupq_n_u16(pos);
            uint16x8x2_t v = vld1q_u16_x2(carr);
            uint16x8_t hit = vorrq_u16(vceqq_u16(v.val[0], needle),
                                       vceqq_u16(v.val[1], needle));
            if (vmaxvq_u16(hit) != 0) return true;
            for (int32_t j = 16; j < cardinality; j++) {
                uint16_t x = carr[j];
                if (x >= pos) return x == pos;
            }
            return false;
        }
        if (cardinality >= 8) {
            uint16x8_t needle = vdupq_n_u16(pos);
            uint16x8_t v = vld1q_u16(carr);
            if (vmaxvq_u16(vceqq_u16(v, needle)) != 0) return true;
            for (int32_t j = 8; j < cardinality; j++) {
                uint16_t x = carr[j];
                if (x >= pos) return x == pos;
            }
            return false;
        }
        for (int32_t j = 0; j < cardinality; j++) {
            uint16_t v = carr[j];
            if (v >= pos) return v == pos;
        }
        return false;
    }

    int32_t num_blocks = cardinality / gap;

    if (num_blocks <= 3) {
        return simd_quad_graviton(carr, cardinality, pos);
    }

    int32_t base = 0;
    int32_t n = num_blocks;

    // Kick the whole spine into L1 right away. For n=4096 this is 4 lines;
    // for n=1024 it is 1 line. The V2 streamer picks up the rest as soon
    // as the first line triggers it.
    __builtin_prefetch(spine);

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

    if (lo < num_blocks) {
        const uint16_t *blk = carr + lo * gap;
        uint16x8_t needle = vdupq_n_u16(pos);
        uint16x8x2_t a = vld1q_u16_x2(blk);
        uint16x8x2_t b = vld1q_u16_x2(blk + 16);
        uint16x8_t h0 = vceqq_u16(a.val[0], needle);
        uint16x8_t h1 = vceqq_u16(a.val[1], needle);
        uint16x8_t h2 = vceqq_u16(b.val[0], needle);
        uint16x8_t h3 = vceqq_u16(b.val[1], needle);
        uint16x8_t hit = vorrq_u16(vorrq_u16(h0, h1), vorrq_u16(h2, h3));
        return vmaxvq_u16(hit) != 0;
    }

    for (int32_t j = num_blocks * gap; j < cardinality; j++) {
        uint16_t v = carr[j];
        if (v >= pos) return v == pos;
    }
    return false;
}

// Build the spine for a given carr. Caller allocates cardinality/32 u16s.
void simd_quad_graviton_build_spine(const uint16_t *carr, int32_t cardinality,
                                    uint16_t *spine) {
    enum { gap = 32 };
    int32_t num_blocks = cardinality / gap;
    for (int32_t i = 0; i < num_blocks; i++) {
        spine[i] = carr[(i + 1) * gap - 1];
    }
}

/*
 * Compile-time n=4096 specialization, Graviton 4 edition.
 *
 * Same shape as simd_quad_intel_spine_4096: at gap=32 and n=4096,
 * num_blocks is exactly 128 and the quaternary descent runs exactly
 * three iterations (n=128 -> 32 -> 8 -> 2), then one binary step,
 * then the final lo pick. All the probe offsets materialize as
 * constants and the compiler can straight-line the whole thing.
 *
 * On EMR this was a 22-30% win over the general-n spine. The
 * expected mechanism (one fewer backward branch per probe tier plus
 * fully register-scheduled offsets) is architecture-independent, so
 * the V2 should benefit too; the open question is how much, given
 * that V2's branch predictor is already very good.
 *
 * 4096 % 32 == 0 so there is no tail sweep: lo == num_blocks means
 * "past the end" and we return false.
 */
/*
 * Padded-descent spine variant.
 *
 * Observation: the general-n spine descent has a visible sawtooth in warm
 * ns/query vs n. Each doubling of n that adds a binary-tail iteration
 * (the `while (n > 1)` loop) adds roughly one load-use latency (~5 ns on
 * V2) relative to the neighboring n where the quaternary descent lands on
 * a pure power-of-4 count and the binary loop runs zero times. On GV4
 * warm this shows up as an alternation: n=128 cheap, n=256 expensive,
 * n=512 cheap, etc. V2 has 4 load AGUs + deep OoO, so the three quat
 * probes issue in one load-use round; the serial binary tail is the
 * outlier.
 *
 * Fix: pad the spine with two sentinel u16 0xFFFF entries past num_blocks,
 * then replace the binary-tail loop + final lo pick with a single 3-probe
 * branchless finish:
 *
 *     lo = base + (spine[base    ] < pos)
 *               + (spine[base + 1] < pos)
 *               + (spine[base + 2] < pos);
 *
 * Correctness: at quat exit, n in {1, 2, 3} and target in [base, base+n].
 * Spine is sorted, so (spine[base+k] < pos) is a monotone-decreasing
 * sequence in k; the sum counts exactly how many entries are below pos,
 * giving the correct offset. Reads past num_blocks land on 0xFFFF
 * sentinels which are >= any u16 pos and contribute 0. The descent now
 * has fixed shape (k quat iters + 1 finish round) with no data-dependent
 * iteration count.
 *
 * Caller must construct the spine with simd_quad_graviton_build_spine_padded
 * (allocates cardinality/32 + 2 u16s and fills 2 sentinels).
 */
bool simd_quad_graviton_spine_padded(const uint16_t *carr, const uint16_t *spine,
                                     int32_t cardinality, uint16_t pos) {
    enum { gap = 32 };

    if (cardinality < gap) {
        if (cardinality >= 16) {
            uint16x8_t needle = vdupq_n_u16(pos);
            uint16x8x2_t v = vld1q_u16_x2(carr);
            uint16x8_t hit = vorrq_u16(vceqq_u16(v.val[0], needle),
                                       vceqq_u16(v.val[1], needle));
            if (vmaxvq_u16(hit) != 0) return true;
            for (int32_t j = 16; j < cardinality; j++) {
                uint16_t x = carr[j];
                if (x >= pos) return x == pos;
            }
            return false;
        }
        if (cardinality >= 8) {
            uint16x8_t needle = vdupq_n_u16(pos);
            uint16x8_t v = vld1q_u16(carr);
            if (vmaxvq_u16(vceqq_u16(v, needle)) != 0) return true;
            for (int32_t j = 8; j < cardinality; j++) {
                uint16_t x = carr[j];
                if (x >= pos) return x == pos;
            }
            return false;
        }
        for (int32_t j = 0; j < cardinality; j++) {
            uint16_t v = carr[j];
            if (v >= pos) return v == pos;
        }
        return false;
    }

    int32_t num_blocks = cardinality / gap;

    if (num_blocks <= 3) {
        return simd_quad_graviton(carr, cardinality, pos);
    }

    int32_t base = 0;
    int32_t n = num_blocks;

    __builtin_prefetch(spine);

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

    // 3-probe branchless finish; see header comment for correctness.
    int32_t lo = base
               + (spine[base    ] < pos)
               + (spine[base + 1] < pos)
               + (spine[base + 2] < pos);

    if (lo < num_blocks) {
        const uint16_t *blk = carr + lo * gap;
        uint16x8_t needle = vdupq_n_u16(pos);
        uint16x8x2_t a = vld1q_u16_x2(blk);
        uint16x8x2_t b = vld1q_u16_x2(blk + 16);
        uint16x8_t h0 = vceqq_u16(a.val[0], needle);
        uint16x8_t h1 = vceqq_u16(a.val[1], needle);
        uint16x8_t h2 = vceqq_u16(b.val[0], needle);
        uint16x8_t h3 = vceqq_u16(b.val[1], needle);
        uint16x8_t hit = vorrq_u16(vorrq_u16(h0, h1), vorrq_u16(h2, h3));
        return vmaxvq_u16(hit) != 0;
    }

    for (int32_t j = num_blocks * gap; j < cardinality; j++) {
        uint16_t v = carr[j];
        if (v >= pos) return v == pos;
    }
    return false;
}

// Build a padded spine. Caller allocates cardinality/32 + 2 u16s. Writes
// num_blocks real entries followed by 2 sentinel 0xFFFF entries.
void simd_quad_graviton_build_spine_padded(const uint16_t *carr,
                                           int32_t cardinality,
                                           uint16_t *spine) {
    enum { gap = 32 };
    int32_t num_blocks = cardinality / gap;
    for (int32_t i = 0; i < num_blocks; i++) {
        spine[i] = carr[(i + 1) * gap - 1];
    }
    spine[num_blocks]     = 0xFFFF;
    spine[num_blocks + 1] = 0xFFFF;
}

/*
 * Compile-time spine specializations for n ∈ {256, 512, 1024, 2048, 4096}.
 *
 * All five share a straight-line body: num_blocks is a constant, every
 * spine offset materializes as a constant, no while loops, no
 * data-dependent iteration count. They differ in how they finish:
 *
 *   High-foot sizes {256, 1024, 4096} -- quat descent exits with n=2.
 *     Use a branchless 2-probe finish:
 *         lo = base + (spine[base] < pos) + (spine[base+1] < pos);
 *     After the last quat iter base <= num_blocks-2, so spine[base+1] is
 *     always valid. The caller-visible `lo < num_blocks` check still
 *     handles lo == base+2 == num_blocks for "past the end." No sentinels
 *     needed because num_blocks is known at compile time (unlike
 *     _spine_padded's general-n 3-probe finish).
 *
 *   Low-foot sizes {512, 2048} -- quat descent exits with n=1.
 *     Use the classic final-lo pick:
 *         lo = (spine[base] < pos) ? base+1 : base;
 *     No binary-tail round to collapse; the whole win here is outer-loop
 *     overhead removal from the straight-line unroll (2 iters for n=512,
 *     3 for n=2048).
 *
 * Per-size descent shape at gap=32 (traced from the general-n loop):
 *   n=256  (num_blocks=8):   1 quat (quarter=2)                 + 2-probe finish
 *   n=512  (num_blocks=16):  2 quat (quarter=4, 1)              + final lo
 *   n=1024 (num_blocks=32):  2 quat (quarter=8, 2)              + 2-probe finish
 *   n=2048 (num_blocks=64):  3 quat (quarter=16, 4, 1)          + final lo
 *   n=4096 (num_blocks=128): 3 quat (quarter=32, 8, 2)          + 2-probe finish
 *
 * 5-run medians vs the general-n _spine on GV4 r8g, 2026-05-12
 * (gv4_runs/hybrid_run{1..5}.txt, gv4_runs/spineN_run{1..5}.txt):
 *   n=256:  warm -60%  cold -35%   (vs _spine_padded: -27% / -28%)
 *   n=512:  warm -23%  cold -25%   (no pad comparison -- low-foot)
 *   n=1024: warm -63%  cold -31%   (vs _spine_padded: -25% / -35%)
 *   n=2048: warm -22%  cold +17%   (cold regression; unroll clusters tier
 *                                   probes before block load, denying OoO
 *                                   overlap. Same mechanism as the M4
 *                                   _spine_4096 cold regression.)
 *   n=4096: warm -57%  cold -15%   (vs _spine_padded: -18% / -19%)
 *
 * Every num_blocks is a multiple of 32 so gap=32 gives no tail sweep:
 * lo == num_blocks means "past the end" -> return false.
 */

bool simd_quad_graviton_spine_256(const uint16_t *carr,
                                  const uint16_t *spine, uint16_t pos) {
    enum { gap = 32, num_blocks = 8 };

    __builtin_prefetch(spine);

    int32_t base = 0;

    // Quaternary iter 1: n=8, quarter=2.
    {
        int32_t k1 = spine[base + 2];
        int32_t k2 = spine[base + 4];
        int32_t k3 = spine[base + 6];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * 2;
    }
    // Branchless 2-probe finish: n=2.
    int32_t lo = base + (spine[base] < pos) + (spine[base + 1] < pos);

    if (lo < num_blocks) {
        const uint16_t *blk = carr + lo * gap;
        uint16x8_t needle = vdupq_n_u16(pos);
        uint16x8x2_t a = vld1q_u16_x2(blk);
        uint16x8x2_t b = vld1q_u16_x2(blk + 16);
        uint16x8_t h0 = vceqq_u16(a.val[0], needle);
        uint16x8_t h1 = vceqq_u16(a.val[1], needle);
        uint16x8_t h2 = vceqq_u16(b.val[0], needle);
        uint16x8_t h3 = vceqq_u16(b.val[1], needle);
        uint16x8_t hit = vorrq_u16(vorrq_u16(h0, h1), vorrq_u16(h2, h3));
        return vmaxvq_u16(hit) != 0;
    }
    return false;
}

bool simd_quad_graviton_spine_512(const uint16_t *carr,
                                  const uint16_t *spine, uint16_t pos) {
    enum { gap = 32, num_blocks = 16 };

    __builtin_prefetch(spine);

    int32_t base = 0;

    // Quaternary iter 1: n=16, quarter=4.
    {
        int32_t k1 = spine[base + 4];
        int32_t k2 = spine[base + 8];
        int32_t k3 = spine[base + 12];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * 4;
    }
    // Quaternary iter 2: n=4, quarter=1.
    {
        int32_t k1 = spine[base + 1];
        int32_t k2 = spine[base + 2];
        int32_t k3 = spine[base + 3];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos));
    }
    // Final lo pick.
    int32_t lo = (spine[base] < pos) ? base + 1 : base;

    if (lo < num_blocks) {
        const uint16_t *blk = carr + lo * gap;
        uint16x8_t needle = vdupq_n_u16(pos);
        uint16x8x2_t a = vld1q_u16_x2(blk);
        uint16x8x2_t b = vld1q_u16_x2(blk + 16);
        uint16x8_t h0 = vceqq_u16(a.val[0], needle);
        uint16x8_t h1 = vceqq_u16(a.val[1], needle);
        uint16x8_t h2 = vceqq_u16(b.val[0], needle);
        uint16x8_t h3 = vceqq_u16(b.val[1], needle);
        uint16x8_t hit = vorrq_u16(vorrq_u16(h0, h1), vorrq_u16(h2, h3));
        return vmaxvq_u16(hit) != 0;
    }
    return false;
}

bool simd_quad_graviton_spine_1024(const uint16_t *carr,
                                   const uint16_t *spine, uint16_t pos) {
    enum { gap = 32, num_blocks = 32 };

    __builtin_prefetch(spine);

    int32_t base = 0;

    // Quaternary iter 1: n=32, quarter=8.
    {
        int32_t k1 = spine[base + 8];
        int32_t k2 = spine[base + 16];
        int32_t k3 = spine[base + 24];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * 8;
    }
    // Quaternary iter 2: n=8, quarter=2.
    {
        int32_t k1 = spine[base + 2];
        int32_t k2 = spine[base + 4];
        int32_t k3 = spine[base + 6];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * 2;
    }
    // Branchless 2-probe finish: n=2.
    int32_t lo = base + (spine[base] < pos) + (spine[base + 1] < pos);

    if (lo < num_blocks) {
        const uint16_t *blk = carr + lo * gap;
        uint16x8_t needle = vdupq_n_u16(pos);
        uint16x8x2_t a = vld1q_u16_x2(blk);
        uint16x8x2_t b = vld1q_u16_x2(blk + 16);
        uint16x8_t h0 = vceqq_u16(a.val[0], needle);
        uint16x8_t h1 = vceqq_u16(a.val[1], needle);
        uint16x8_t h2 = vceqq_u16(b.val[0], needle);
        uint16x8_t h3 = vceqq_u16(b.val[1], needle);
        uint16x8_t hit = vorrq_u16(vorrq_u16(h0, h1), vorrq_u16(h2, h3));
        return vmaxvq_u16(hit) != 0;
    }
    return false;
}

bool simd_quad_graviton_spine_2048(const uint16_t *carr,
                                   const uint16_t *spine, uint16_t pos) {
    enum { gap = 32, num_blocks = 64 };

    __builtin_prefetch(spine);

    int32_t base = 0;

    // Quaternary iter 1: n=64, quarter=16.
    {
        int32_t k1 = spine[base + 16];
        int32_t k2 = spine[base + 32];
        int32_t k3 = spine[base + 48];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * 16;
    }
    // Quaternary iter 2: n=16, quarter=4.
    {
        int32_t k1 = spine[base + 4];
        int32_t k2 = spine[base + 8];
        int32_t k3 = spine[base + 12];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * 4;
    }
    // Quaternary iter 3: n=4, quarter=1.
    {
        int32_t k1 = spine[base + 1];
        int32_t k2 = spine[base + 2];
        int32_t k3 = spine[base + 3];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos));
    }
    // Final lo pick.
    int32_t lo = (spine[base] < pos) ? base + 1 : base;

    if (lo < num_blocks) {
        const uint16_t *blk = carr + lo * gap;
        uint16x8_t needle = vdupq_n_u16(pos);
        uint16x8x2_t a = vld1q_u16_x2(blk);
        uint16x8x2_t b = vld1q_u16_x2(blk + 16);
        uint16x8_t h0 = vceqq_u16(a.val[0], needle);
        uint16x8_t h1 = vceqq_u16(a.val[1], needle);
        uint16x8_t h2 = vceqq_u16(b.val[0], needle);
        uint16x8_t h3 = vceqq_u16(b.val[1], needle);
        uint16x8_t hit = vorrq_u16(vorrq_u16(h0, h1), vorrq_u16(h2, h3));
        return vmaxvq_u16(hit) != 0;
    }
    return false;
}

bool simd_quad_graviton_spine_4096(const uint16_t *carr,
                                   const uint16_t *spine, uint16_t pos) {
    enum { gap = 32, num_blocks = 128 };

    __builtin_prefetch(spine);

    int32_t base = 0;

    // Quaternary iter 1: n=128, quarter=32.
    {
        int32_t k1 = spine[base + 32];
        int32_t k2 = spine[base + 64];
        int32_t k3 = spine[base + 96];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * 32;
    }
    // Quaternary iter 2: n=32, quarter=8.
    {
        int32_t k1 = spine[base + 8];
        int32_t k2 = spine[base + 16];
        int32_t k3 = spine[base + 24];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * 8;
    }
    // Quaternary iter 3: n=8, quarter=2.
    {
        int32_t k1 = spine[base + 2];
        int32_t k2 = spine[base + 4];
        int32_t k3 = spine[base + 6];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * 2;
    }
    // Branchless 2-probe finish: n=2.
    int32_t lo = base + (spine[base] < pos) + (spine[base + 1] < pos);

    if (lo < num_blocks) {
        const uint16_t *blk = carr + lo * gap;
        uint16x8_t needle = vdupq_n_u16(pos);
        uint16x8x2_t a = vld1q_u16_x2(blk);
        uint16x8x2_t b = vld1q_u16_x2(blk + 16);
        uint16x8_t h0 = vceqq_u16(a.val[0], needle);
        uint16x8_t h1 = vceqq_u16(a.val[1], needle);
        uint16x8_t h2 = vceqq_u16(b.val[0], needle);
        uint16x8_t h3 = vceqq_u16(b.val[1], needle);
        uint16x8_t hit = vorrq_u16(vorrq_u16(h0, h1), vorrq_u16(h2, h3));
        return vmaxvq_u16(hit) != 0;
    }
    return false;
}

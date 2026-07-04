#include <stdbool.h>
#include <stdint.h>
#include <arm_neon.h>

/*
 * Pi 5 (Cortex-A76) variant of simd_quad.
 *
 * Differences from the reference simd_quad.c:
 *   - Block size is 32 u16 = one 64-byte cache line, so a block hit touches
 *     exactly one line. This halves the number of blocks vs. gap=16 and
 *     therefore shortens the interpolation.
 *   - The block load uses vld1q_u16_x2 (two paired 128-bit loads), which
 *     maps well to A76's two load AGUs.
 *   - AArch64/NEON only; the SSE2 fallback from the reference is gone.
 *   - Speculative prefetch inside the quaternary loop (Eytzinger-inspired):
 *     at the end of each iteration we prefetch the next iter's middle probe
 *     and the current candidate final-block line. These misses then overlap
 *     with the in-flight k1/k2/k3 loads instead of serializing behind them.
 */
bool simd_quad_pi5(const uint16_t *carr, int32_t cardinality, uint16_t pos) {
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
        // Eytzinger-inspired speculative prefetch: the next iteration's
        // middle probe is deterministic from (base, n), so issue its
        // prefetch now. Its miss will overlap with c1/c2/c3 already in
        // flight instead of serializing behind them. Saves ~10-20% on
        // cold-cache queries for n >= 1024; near-free when warm.
        __builtin_prefetch(carr + (base + (n >> 1)) * gap);
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
 * Spine variant.
 *
 * The interpolation probes in simd_quad_pi5 read carr[(i+1)*gap - 1] — one
 * scattered cache line per probe. Here we pass in a pre-built `spine` that
 * packs those keys contiguously: spine[i] = carr[(i+1)*gap - 1]. For
 * n=4096 the spine is 128 * u16 = 256 bytes (4 cache lines), so the whole
 * interpolation phase touches only a tiny contiguous region.
 *
 * The final SIMD block check still loads from carr — the spine only covers
 * the interpolation critical path, which is where cold-cache latency lives.
 *
 * Caller is responsible for building `spine` (see simd_quad_pi5_build_spine).
 * Small-size queries (cardinality < 32) don't use the spine and just run
 * the fast paths from simd_quad_pi5; the caller may pass NULL for those.
 */
bool simd_quad_pi5_spine(const uint16_t *carr, const uint16_t *spine,
                         int32_t cardinality, uint16_t pos) {
    enum { gap = 32 };

    if (cardinality < gap) {
        // Same fast paths as simd_quad_pi5 — spine is irrelevant here.
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

    // When num_blocks <= 3 the interpolation is just 0 or 1 probes. Running
    // those off the spine is pessimistic: the carr-based probes in pi5 hit
    // the same cache lines the final SIMD block will need, while spine
    // probes are in a disjoint region (no reuse) and the prefetch slot is
    // wasted on a 4-byte region. Delegate to the plain pi5 path.
    if (num_blocks <= 3) {
        return simd_quad_pi5(carr, cardinality, pos);
    }

    int32_t base = 0;
    int32_t n = num_blocks;

    // Kick the whole spine into L1 right away. For n=4096 this is 4 lines;
    // for n=1024 it is 1 line. Cheap insurance on cold queries.
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
void simd_quad_pi5_build_spine(const uint16_t *carr, int32_t cardinality,
                               uint16_t *spine) {
    enum { gap = 32 };
    int32_t num_blocks = cardinality / gap;
    for (int32_t i = 0; i < num_blocks; i++) {
        spine[i] = carr[(i + 1) * gap - 1];
    }
}

/*
 * Compile-time spine specializations for n ∈ {256, 512, 1024, 2048, 4096},
 * Pi 5 edition. Ported wholesale from the Graviton 4 set — shared gap=32,
 * shared paired vld1q_u16_x2 block check, shared 64-byte cache line, so
 * the descent shape, probe offsets, and finish shape are bit-identical.
 *
 * High-foot sizes {256, 1024, 4096} use a branchless 2-probe finish after
 * the last quat iter (which exits with n=2); low-foot sizes {512, 2048}
 * use a pure straight-line unroll with a final-lo pick (quat-exit n=1).
 *
 * Per-size descent shape at gap=32 (identical to the Graviton variant):
 *   n=256  (num_blocks=8):   1 quat (quarter=2)                 + 2-probe finish
 *   n=512  (num_blocks=16):  2 quat (quarter=4, 1)              + final lo
 *   n=1024 (num_blocks=32):  2 quat (quarter=8, 2)              + 2-probe finish
 *   n=2048 (num_blocks=64):  3 quat (quarter=16, 4, 1)          + final lo
 *   n=4096 (num_blocks=128): 3 quat (quarter=32, 8, 2)          + 2-probe finish
 *
 * 5-run medians vs the general-n _spine on Pi 5 (Cortex-A76), 2026-05-12
 * (pi5_runs/hybrid_run{1..5}.txt):
 *   n=256:  warm -24%  cold +42%  (cold regression; unroll clusters tier
 *                                  probes before block load and denies OoO
 *                                  overlap, same shape as the GV4 n=2048
 *                                  cold regression)
 *   n=512:  warm -46%  cold -28%
 *   n=1024: warm -28%  cold  -2%
 *   n=2048: warm -25%  cold -27%
 *   n=4096: warm -28%  cold  -7%
 *
 * Ship call on n=4096 2026-05-12: hybrid (3 quat + 2-probe finish) beat the
 * prior 3-quat + binary step + final-lo unroll -16.9% warm (monotone across
 * 5/5 runs) with cold +6.7% well inside the 107-214 cold variance band.
 * Same pattern as GV4/EMR/M1 — unroll retired, simd_quad_pi5_spine_4096 IS
 * the hybrid. Refutes the 2026-05-01 hypothesis that "GCC 15 already
 * hoists loop control so branch-removal is a wash on Pi 5" -- the 2-probe
 * finish saves one dependent load-use round (the binary step) which no
 * compiler pass can reconstruct.
 *
 * Every num_blocks is a multiple of 32 so gap=32 gives no tail sweep:
 * lo == num_blocks means "past the end" -> return false.
 */

bool simd_quad_pi5_spine_256(const uint16_t *carr,
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

bool simd_quad_pi5_spine_512(const uint16_t *carr,
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

bool simd_quad_pi5_spine_1024(const uint16_t *carr,
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

bool simd_quad_pi5_spine_2048(const uint16_t *carr,
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

bool simd_quad_pi5_spine_4096(const uint16_t *carr,
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

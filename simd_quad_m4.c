#include <stdbool.h>
#include <stdint.h>
#include <arm_neon.h>

/*
 * Apple M4 Max (P-core) variant of simd_quad.
 *
 * The M4 has a 128-byte cache line, 128 KB L1D per P-core, 3 load AGUs, and
 * a very aggressive hardware prefetcher + wide OoO window. That changes
 * several decisions relative to the Pi 5 (Cortex-A76) variant:
 *
 *   - Block size is 64 u16 = one 128-byte cache line. "One block = one line"
 *     is the same structural argument we made on Pi 5, re-tuned for M4's
 *     line size. Halves the interpolation depth again vs. the Pi 5 gap=32.
 *   - The block check uses two vld1q_u16_x4 (eight paired 128-bit loads),
 *     which the three load AGUs can overlap freely. All four "a" loads and
 *     all four "b" loads are independent, so the core can pipeline the
 *     whole 128-byte block in a few cycles.
 *   - AArch64/NEON only; Apple silicon has no SVE/SVE2, and SSE2 never
 *     applied.
 *   - No speculative __builtin_prefetch in the interpolation loop. On the
 *     Pi 5 it bought 10-25% cold because the A76 has limited MLP and the
 *     data-dependent middle-probe pattern is opaque to the HW prefetcher.
 *     On the M4 the OoO window is wide enough that the miss already
 *     overlaps with other in-flight loads, and the prefetch instruction
 *     just costs an issue slot. We drop it here and rely on the spine
 *     variant for the cold-cache win.
 *   - Extra small-size fast path for 32 <= n < 64 (new tier introduced by
 *     the larger block): a vld1q_u16_x4 covers the first 32 elements and
 *     a short scalar sweep handles the tail.
 */
bool simd_quad_m4(const uint16_t *carr, int32_t cardinality, uint16_t pos) {
    enum { gap = 64 };

    if (cardinality < gap) {
        if (cardinality >= 32) {
            // 32 <= n < 64: NEON-compare the first 32 as a single x4 load,
            // sweep the remainder.
            uint16x8_t needle = vdupq_n_u16(pos);
            uint16x8x4_t v = vld1q_u16_x4(carr);
            uint16x8_t hit = vorrq_u16(
                vorrq_u16(vceqq_u16(v.val[0], needle), vceqq_u16(v.val[1], needle)),
                vorrq_u16(vceqq_u16(v.val[2], needle), vceqq_u16(v.val[3], needle)));
            if (vmaxvq_u16(hit) != 0) return true;
            for (int32_t j = 32; j < cardinality; j++) {
                uint16_t x = carr[j];
                if (x >= pos) return x == pos;
            }
            return false;
        }
        if (cardinality >= 16) {
            // 16 <= n < 32: paired x2 load + sweep tail.
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
            // 8 <= n < 16: single 128-bit compare + sweep tail.
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

    for (int32_t j = num_blocks * gap; j < cardinality; j++) {
        uint16_t v = carr[j];
        if (v >= pos) return v == pos;
    }
    return false;
}

/*
 * Spine variant, M4 edition.
 *
 * Same idea as simd_quad_pi5_spine: pack the interpolation probe keys into
 * a dense contiguous region so the cold-cache pointer chase streams through
 * consecutive cache lines. With gap=64 the spine compresses even harder
 * than on Pi 5 because the M4's cache line is bigger:
 *
 *   n=4096 -> 64 spine keys -> 128 B = 1 M4 cache line
 *   n=2048 -> 32 spine keys ->  64 B = half a line
 *   n=1024 -> 16 spine keys ->  32 B
 *
 * The entire interpolation phase for a max-sized Roaring container now
 * lives in one cache line. The final SIMD block check still loads from
 * carr.
 *
 * The num_blocks <= 3 fallback from the Pi 5 variant applies here too:
 * with very few blocks the carr-based probes accidentally prime the final
 * block's lines, which the spine path disrupts.
 */
bool simd_quad_m4_spine(const uint16_t *carr, const uint16_t *spine,
                        int32_t cardinality, uint16_t pos) {
    enum { gap = 64 };

    if (cardinality < gap) {
        // Same fast paths as simd_quad_m4 -- spine is irrelevant here.
        if (cardinality >= 32) {
            uint16x8_t needle = vdupq_n_u16(pos);
            uint16x8x4_t v = vld1q_u16_x4(carr);
            uint16x8_t hit = vorrq_u16(
                vorrq_u16(vceqq_u16(v.val[0], needle), vceqq_u16(v.val[1], needle)),
                vorrq_u16(vceqq_u16(v.val[2], needle), vceqq_u16(v.val[3], needle)));
            if (vmaxvq_u16(hit) != 0) return true;
            for (int32_t j = 32; j < cardinality; j++) {
                uint16_t x = carr[j];
                if (x >= pos) return x == pos;
            }
            return false;
        }
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
        return simd_quad_m4(carr, cardinality, pos);
    }

    int32_t base = 0;
    int32_t n = num_blocks;

    // Pull the whole spine into L1 up front. For n in [256, 4096] this is
    // 1 line (128 B); for smaller n it is a partial line. Cheap on cold.
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

    for (int32_t j = num_blocks * gap; j < cardinality; j++) {
        uint16_t v = carr[j];
        if (v >= pos) return v == pos;
    }
    return false;
}

// Build the spine for a given carr. Caller allocates cardinality/64 u16s.
void simd_quad_m4_build_spine(const uint16_t *carr, int32_t cardinality,
                              uint16_t *spine) {
    enum { gap = 64 };
    int32_t num_blocks = cardinality / gap;
    for (int32_t i = 0; i < num_blocks; i++) {
        spine[i] = carr[(i + 1) * gap - 1];
    }
}

/*
 * Compile-time n=4096 specialization, M4 edition.
 *
 * With gap=64 and n=4096 the spine has exactly 64 entries (128 B = 1 M4
 * cache line, covered by a single __builtin_prefetch). The quaternary
 * descent runs exactly three iterations (n=64 -> 16 -> 4 -> 1). Unlike
 * the gap=32 hosts, there is no binary step: the descent lands at n=1
 * directly, so the loop structure collapses to three constant-offset
 * quaternary probes followed by the final lo pick. All probe offsets
 * materialize as compile-time constants.
 *
 * 4096 % 64 == 0 so there is no tail sweep: lo == num_blocks means
 * "past the end" and we return false.
 */
bool simd_quad_m4_spine_4096(const uint16_t *carr, const uint16_t *spine,
                             uint16_t pos) {
    enum { gap = 64, num_blocks = 64 };

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
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * 1;
    }
    // No binary step: n=1 after iter 3. Final lo pick directly.
    int32_t lo = (spine[base] < pos) ? base + 1 : base;

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

/*
 * OpenEvolve target: simd_quad_m4_spine_4096 (the compile-time n=4096
 * unroll of the M4 spine variant).
 *
 * Problem: on M4 Max and M1 Pro this function is ~16% faster warm than
 * the general-n simd_quad_m4_spine but ~188-194% SLOWER cold. Structural
 * hypothesis (CLAUDE.md, open item 1): gap=64 + 128-B line collapses the
 * spine to 1 cache line, HW streamer has nothing to latch onto, and the
 * straight-line unroll issues all three tier probes before the block load
 * so the wide OoO window can't overlap the block-load miss with tier
 * misses. Goal: recover cold while keeping warm close to parity with the
 * baseline simd_quad_m4_spine.
 *
 * Constraints evolution must respect:
 *   - Signature is frozen: bool simd_quad_m4_spine_4096(const uint16_t*,
 *                                                       const uint16_t*,
 *                                                       uint16_t)
 *   - cardinality is implicitly 4096 (num_blocks=64, gap=64).
 *   - carr has 4096 u16s; spine has 64 u16s.
 *   - Must return true iff pos is in carr[0..4096).
 *   - AArch64 / NEON only. Free to use any <arm_neon.h> intrinsic,
 *     __builtin_prefetch with any locality/rw flag, and standard C.
 *   - No writes to carr or spine.
 *
 * Baselines (M4 Max, ns/query, 5-run medians from m4_runs/):
 *   simd_quad_m4_spine:      warm 4.34   cold  6.47
 *   simd_quad_m4_spine_4096: warm 3.65   cold 18.65   <-- evolved replaces this
 * A successful candidate beats cold 18.65 while staying below warm 4.34.
 */

#include <stdbool.h>
#include <stdint.h>
#include <arm_neon.h>

// EVOLVE-BLOCK-START
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
// EVOLVE-BLOCK-END

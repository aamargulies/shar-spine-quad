/*
 * Daniel Lemire's SIMD Quad search as revised on 2026-10-02: commit
 * 046ff4360a in github.com/lemire/Code-used-on-Daniel-Lemire-s-blog, file
 * 2026/04/26/benchmark/benchmarks/simple.cpp, "Search arrays under 16
 * elements with overlapping SIMD loads in the beat-binary-search post";
 * published at https://lemire.me/blog/2026/04/27/you-can-beat-the-binary-search/
 * (post updated 2026-10-02). Third-party code, (c) Daniel Lemire; see
 * THIRD_PARTY_NOTICES.md.
 *
 * Adapted to this repository's (carr, cardinality, pos) signature exactly as
 * simd_quad.c adapts the 2026-04-27 version. The only difference from
 * simd_quad.c is the cardinality < 16 path: the April kernel scans those
 * arrays linearly; this one compares the needle against two overlapping SIMD
 * loads that together cover the array (8-wide for 8..15 elements, 4-wide for
 * 4..7), and against the first, middle and last element below 4, with no
 * data-dependent branch. Everything from 16 elements up is identical.
 *
 * Bare function body: #include it into a translation unit that already has
 * <arm_neon.h> or <emmintrin.h> in scope (same convention as simd_quad.c).
 */
bool simd_quad_2026_10(const uint16_t *carr, int32_t cardinality, uint16_t pos) {
    constexpr int32_t gap = 16;
    if (cardinality < gap) {
        // two overlapping loads cover the array: no data-dependent branch
#ifdef __ARM_NEON
        if (cardinality >= 8) {
            uint16x8_t needle = vdupq_n_u16(pos);
            uint16x8_t v0 = vld1q_u16(carr);
            uint16x8_t v1 = vld1q_u16(carr + cardinality - 8);
            uint16x8_t hit = vorrq_u16(vceqq_u16(v0, needle), vceqq_u16(v1, needle));
            return vmaxvq_u16(hit) != 0;
        }
        if (cardinality >= 4) {
            uint16x4_t needle = vdup_n_u16(pos);
            uint16x4_t v0 = vld1_u16(carr);
            uint16x4_t v1 = vld1_u16(carr + cardinality - 4);
            uint16x4_t hit = vorr_u16(vceq_u16(v0, needle), vceq_u16(v1, needle));
            return vmaxv_u16(hit) != 0;
        }
#else
        if (cardinality >= 8) {
            __m128i needle = _mm_set1_epi16((short)pos);
            __m128i v0 = _mm_loadu_si128((const __m128i *)carr);
            __m128i v1 = _mm_loadu_si128((const __m128i *)(carr + cardinality - 8));
            __m128i hit = _mm_or_si128(_mm_cmpeq_epi16(v0, needle),
                                       _mm_cmpeq_epi16(v1, needle));
            return _mm_movemask_epi8(hit) != 0;
        }
        if (cardinality >= 4) {
            __m128i needle = _mm_set1_epi16((short)pos);
            __m128i v0 = _mm_loadl_epi64((const __m128i *)carr);
            __m128i v1 = _mm_loadl_epi64((const __m128i *)(carr + cardinality - 4));
            __m128i hit = _mm_or_si128(_mm_cmpeq_epi16(v0, needle),
                                       _mm_cmpeq_epi16(v1, needle));
            return (_mm_movemask_epi8(hit) & 0xFF) != 0;
        }
#endif
        if (cardinality == 0) return false;
        return (carr[0] == pos) | (carr[cardinality / 2] == pos) |
               (carr[cardinality - 1] == pos);
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
#ifdef __ARM_NEON
        uint16x8_t needle = vdupq_n_u16(pos);
        uint16x8_t v0 = vld1q_u16(blk);
        uint16x8_t v1 = vld1q_u16(blk + 8);
        uint16x8_t hit = vorrq_u16(vceqq_u16(v0, needle), vceqq_u16(v1, needle));
        return vmaxvq_u16(hit) != 0;
#else
        __m128i needle = _mm_set1_epi16((short)pos);
        __m128i v0 = _mm_loadu_si128((const __m128i *)blk);
        __m128i v1 = _mm_loadu_si128((const __m128i *)(blk + 8));
        __m128i hit = _mm_or_si128(_mm_cmpeq_epi16(v0, needle),
                                   _mm_cmpeq_epi16(v1, needle));
        return _mm_movemask_epi8(hit) != 0;
#endif
    }

    for (int32_t j = num_blocks * gap; j < cardinality; j++) {
        uint16_t v = carr[j];
        if (v >= pos) return (v == pos);
    }
    return false;
}

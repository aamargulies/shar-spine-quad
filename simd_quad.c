bool simd_quad(const uint16_t *carr, int32_t cardinality, 
            uint16_t pos) {
    constexpr int32_t gap = 16;
    if (cardinality < gap) {
      for (int32_t j = 0; j < cardinality; j++) {
          if (carr[j] == pos) return true;
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
        base = (carr[(base + half + 1) * gap - 1] < pos) 
                 ? base + half : base;
        n -= half;
    }
    int32_t lo = (carr[(base + 1) * gap - 1] < pos) 
                ? base + 1 : base;

    if (lo < num_blocks) {
        const uint16_t *blk = carr + lo * gap;
#ifdef __ARM_NEON
        uint16x8_t needle = vdupq_n_u16(pos);
        uint16x8_t v0 = vld1q_u16(blk);
        uint16x8_t v1 = vld1q_u16(blk + 8);
        uint16x8_t hit = vorrq_u16(vceqq_u16(v0, needle), 
                  vceqq_u16(v1, needle));
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

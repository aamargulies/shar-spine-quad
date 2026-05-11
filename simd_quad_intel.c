#include <stdbool.h>
#include <stdint.h>
#include <immintrin.h>

#if !defined(__AVX2__)
#error "simd_quad_intel.c requires AVX2 or better. For the 512-bit zmm block-check fast path build with -march=icelake-server or newer (or -march=x86-64-v4 / -march=sapphirerapids). For AVX2 only -- including Skylake-SP, where zmm is intentionally avoided due to frequency downclock -- use -march=haswell, -march=skylake-avx512, or -march=native on a SKX host. For pure SSE2, use the reference simd_quad.c instead."
#endif

/*
 * Intel x86_64 variant of simd_quad, targeting modern server Intel
 * (Ice Lake-SP / Sapphire Rapids / Emerald Rapids / Granite Rapids) with
 * AVX-512BW.
 *
 * Differences from the reference simd_quad.c SSE2 path:
 *   - Block size is 32 u16 = one 64-byte cache line. Same "one block =
 *     one line" structural argument as the Pi 5 variant. Intel's 64-byte
 *     line matches the Pi 5's, so gap=32 lands in the same place; the
 *     M4 Max needed gap=64 only because its line is 128 B.
 *   - On Ice Lake-SP and newer the block check is a single 512-bit load
 *     covering the whole 32-element block, _mm512_cmpeq_epi16_mask,
 *     kortest. Three hot instructions in the block check vs. four NEON
 *     instructions on Pi 5 and eight on M4.
 *   - On Skylake-SP/X (family 6 model 85) and on hosts without AVX-512BW
 *     we fall back to two 256-bit AVX2 loads + cmpeq + OR + movemask.
 *     Structurally the same as the Pi 5 vld1q_u16_x2 pattern, just wider.
 *     On Skylake-X this is *faster* than the zmm path because a single
 *     512-bit instruction per call trips the core into AVX-512 license L2
 *     and downclocks surrounding scalar code (the interpolation loop) by
 *     ~15-20% -- more than the 1-instruction block-check win saves. The
 *     zmm fast path is gated on __AVX512VBMI2__ rather than __AVX512BW__:
 *     VBMI2 first appeared in Ice Lake, which is also the first uarch
 *     where the AVX-512 frequency penalty is negligible. SKX sets
 *     __AVX512BW__ but not __AVX512VBMI2__, which is exactly the split
 *     we want.
 *   - Small-size fast path for 16 <= n < 32 uses a single 256-bit AVX2
 *     compare. Small-size fast path for 8 <= n < 16 uses a single
 *     128-bit SSE2 compare. One fewer tier than M4 (which needed
 *     [32,64) as a new tier for gap=64).
 *   - Speculative prefetch inside the interpolation loop is gated on the
 *     same __AVX512VBMI2__ proxy as the zmm block check, with the opposite
 *     polarity: kept on Skylake-SP/X and AVX2-only hosts (narrower OoO,
 *     fewer LFBs, scalar loop running downclocked under the AVX-512 license
 *     on SKX -- the hint overlaps the next probe with in-flight loads and
 *     pays its issue slot back), removed on Ice Lake-SP and newer (wide
 *     ROB + 3 load AGUs + aggressive L1/L2 streamers already overlap the
 *     miss; the hint is pure dispatch waste). Measured on Emerald Rapids
 *     (Xeon Platinum 8559C, 2026-04-30) as a 4-13% warm and up to 18% cold
 *     speedup when removed, with no regressions at any size. Polarity for
 *     A76 / M4 Max is documented in their own files.
 *   - The branchless base update (base += (c1 + c2 + c3) * quarter) is
 *     already what any modern compiler will lower to CMOV or a masked
 *     add on x86. No Intel-specific work needed here.
 */
bool simd_quad_intel(const uint16_t *carr, int32_t cardinality, uint16_t pos) {
    enum { gap = 32 };

    if (cardinality < gap) {
        if (cardinality >= 16) {
            // 16 <= n < 32: single 256-bit AVX2 compare, sweep tail.
            __m256i needle = _mm256_set1_epi16((short)pos);
            __m256i v = _mm256_loadu_si256((const __m256i *)carr);
            __m256i eq = _mm256_cmpeq_epi16(v, needle);
            if (_mm256_movemask_epi8(eq) != 0) return true;
            for (int32_t j = 16; j < cardinality; j++) {
                uint16_t x = carr[j];
                if (x >= pos) return x == pos;
            }
            return false;
        }
        if (cardinality >= 8) {
            // 8 <= n < 16: single 128-bit SSE2 compare, sweep tail.
            __m128i needle = _mm_set1_epi16((short)pos);
            __m128i v = _mm_loadu_si128((const __m128i *)carr);
            __m128i eq = _mm_cmpeq_epi16(v, needle);
            if (_mm_movemask_epi8(eq) != 0) return true;
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
#if !defined(__AVX512VBMI2__)
        // Skylake-SP/X and AVX2-only hosts: narrower OoO window, fewer LFBs,
        // and on SKX the scalar loop is running at AVX-512 license L2 anyway,
        // so overlapping the next probe with a software prefetch pays off.
        // Ice Lake-SP and newer (Sapphire/Emerald/Granite Rapids) have enough
        // ROB + load AGUs + aggressive HW prefetchers that the hint is pure
        // issue-slot waste -- measured on EMR (Xeon 8559C, 2026-04-30) as a
        // consistent 4-13% warm and up to 18% cold speedup when removed, and
        // Ice Lake/Sapphire/Granite share that uarch family. VBMI2 is our
        // proxy for "Ice Lake-SP or newer", same split as the zmm gate below.
        _mm_prefetch((const char *)(carr + (base + (n >> 1)) * gap),
                     _MM_HINT_T0);
#endif
    }
    while (n > 1) {
        int32_t half = n >> 1;
        base = (carr[(base + half + 1) * gap - 1] < pos) ? base + half : base;
        n -= half;
    }
    int32_t lo = (carr[(base + 1) * gap - 1] < pos) ? base + 1 : base;

    if (lo < num_blocks) {
        const uint16_t *blk = carr + lo * gap;
#if defined(__AVX512VBMI2__)
        __m512i needle = _mm512_set1_epi16((short)pos);
        __m512i v = _mm512_loadu_si512((const void *)blk);
        __mmask32 m = _mm512_cmpeq_epi16_mask(v, needle);
        return m != 0;
#else
        __m256i needle = _mm256_set1_epi16((short)pos);
        __m256i v0 = _mm256_loadu_si256((const __m256i *)blk);
        __m256i v1 = _mm256_loadu_si256((const __m256i *)(blk + 16));
        __m256i eq = _mm256_or_si256(_mm256_cmpeq_epi16(v0, needle),
                                     _mm256_cmpeq_epi16(v1, needle));
        return _mm256_movemask_epi8(eq) != 0;
#endif
    }

    for (int32_t j = num_blocks * gap; j < cardinality; j++) {
        uint16_t v = carr[j];
        if (v >= pos) return v == pos;
    }
    return false;
}

/*
 * Spine variant, Intel edition.
 *
 * Same idea as the Pi 5 and M4 spine variants: pack the interpolation
 * probe keys into a dense contiguous region so the cold-cache pointer
 * chase streams through consecutive cache lines, which is exactly what
 * Intel's L1 streamer + L2 stride prefetcher are tuned for.
 *
 *   n=4096 -> 128 spine keys -> 256 B = 4 cache lines
 *   n=2048 ->  64 spine keys -> 128 B = 2 cache lines
 *   n=1024 ->  32 spine keys ->  64 B = 1 cache line
 *
 * Same num_blocks <= 3 fallback as the NEON variants -- with very few
 * blocks the plain carr-based probes accidentally prime the final
 * block's cache lines, which the spine path disrupts.
 */
bool simd_quad_intel_spine(const uint16_t *carr, const uint16_t *spine,
                           int32_t cardinality, uint16_t pos) {
    enum { gap = 32 };

    if (cardinality < gap) {
        // Same small-size fast paths as simd_quad_intel -- spine is
        // irrelevant at these sizes.
        if (cardinality >= 16) {
            __m256i needle = _mm256_set1_epi16((short)pos);
            __m256i v = _mm256_loadu_si256((const __m256i *)carr);
            __m256i eq = _mm256_cmpeq_epi16(v, needle);
            if (_mm256_movemask_epi8(eq) != 0) return true;
            for (int32_t j = 16; j < cardinality; j++) {
                uint16_t x = carr[j];
                if (x >= pos) return x == pos;
            }
            return false;
        }
        if (cardinality >= 8) {
            __m128i needle = _mm_set1_epi16((short)pos);
            __m128i v = _mm_loadu_si128((const __m128i *)carr);
            __m128i eq = _mm_cmpeq_epi16(v, needle);
            if (_mm_movemask_epi8(eq) != 0) return true;
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
        return simd_quad_intel(carr, cardinality, pos);
    }

    int32_t base = 0;
    int32_t n = num_blocks;

    // Pull the whole spine into L1 up front. For n=4096 this is 4 lines;
    // for n=1024 it is 1 line. The HW streamer will pick up the rest if
    // the first line triggers it.
    _mm_prefetch((const char *)spine, _MM_HINT_T0);

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
#if defined(__AVX512VBMI2__)
        __m512i needle = _mm512_set1_epi16((short)pos);
        __m512i v = _mm512_loadu_si512((const void *)blk);
        __mmask32 m = _mm512_cmpeq_epi16_mask(v, needle);
        return m != 0;
#else
        __m256i needle = _mm256_set1_epi16((short)pos);
        __m256i v0 = _mm256_loadu_si256((const __m256i *)blk);
        __m256i v1 = _mm256_loadu_si256((const __m256i *)(blk + 16));
        __m256i eq = _mm256_or_si256(_mm256_cmpeq_epi16(v0, needle),
                                     _mm256_cmpeq_epi16(v1, needle));
        return _mm256_movemask_epi8(eq) != 0;
#endif
    }

    for (int32_t j = num_blocks * gap; j < cardinality; j++) {
        uint16_t v = carr[j];
        if (v >= pos) return v == pos;
    }
    return false;
}

// Build the spine for a given carr. Caller allocates cardinality/32 u16s.
void simd_quad_intel_build_spine(const uint16_t *carr, int32_t cardinality,
                                 uint16_t *spine) {
    enum { gap = 32 };
    int32_t num_blocks = cardinality / gap;
    for (int32_t i = 0; i < num_blocks; i++) {
        spine[i] = carr[(i + 1) * gap - 1];
    }
}

/*
 * Compile-time n=4096 specialization.
 *
 * At n=4096, gap=32, num_blocks=128, the quaternary interpolation runs
 * exactly three iterations (n=128 -> 32 -> 8 -> 2), then one binary step,
 * then the final lo pick. All the loop bounds and `quarter` values are
 * known at compile time, so the while() loops can be inlined flat with
 * the probe offsets materialized as constants.
 *
 * Roaring containers at their array-container cap (4096 elements) are the
 * common "full" case, and Roaring call sites often know the cardinality
 * by type. This specialization trades a little .text for zero loop-control
 * overhead on that hot size.
 *
 * Gains are expected to be largest on hosts where branch prediction
 * struggles with data-dependent quaternary descent (SKX especially, also
 * Pi 5). On EMR, branches here already predict well, so the win should
 * be modest - but worth measuring.
 *
 * There is no tail sweep: 4096 % 32 == 0, so `lo == num_blocks` cleanly
 * means "past the end" and we return false.
 */
bool simd_quad_intel_spine_4096(const uint16_t *carr, const uint16_t *spine,
                                uint16_t pos) {
    enum { gap = 32, num_blocks = 128 };

    _mm_prefetch((const char *)spine, _MM_HINT_T0);

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
    // Binary step: n=2, half=1.
    base = (spine[base + 1] < pos) ? base + 1 : base;
    // Final lo pick.
    int32_t lo = (spine[base] < pos) ? base + 1 : base;

    if (lo < num_blocks) {
        const uint16_t *blk = carr + lo * gap;
#if defined(__AVX512VBMI2__)
        __m512i needle = _mm512_set1_epi16((short)pos);
        __m512i v = _mm512_loadu_si512((const void *)blk);
        __mmask32 m = _mm512_cmpeq_epi16_mask(v, needle);
        return m != 0;
#else
        __m256i needle = _mm256_set1_epi16((short)pos);
        __m256i v0 = _mm256_loadu_si256((const __m256i *)blk);
        __m256i v1 = _mm256_loadu_si256((const __m256i *)(blk + 16));
        __m256i eq = _mm256_or_si256(_mm256_cmpeq_epi16(v0, needle),
                                     _mm256_cmpeq_epi16(v1, needle));
        return _mm256_movemask_epi8(eq) != 0;
#endif
    }
    return false;
}

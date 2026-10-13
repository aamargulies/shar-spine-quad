#include <stdbool.h>
#include <stdint.h>
#include <arm_neon.h>

/*
 * Pi 5 (Cortex-A76) variant of simd_quad.
 *
 * Differences from the reference simd_quad.c:
 *   - Block size is 32 u16 = one 64-byte cache line, so a block hit touches
 *     exactly one line *provided carr is 64-byte aligned*. Nothing in this
 *     file or in the benchmark harnesses aligns carr (std::vector gives
 *     16-byte alignment), so in the archived measurements about three of
 *     four blocks straddle two lines; the measured cold penalty for that
 *     is +14-30% at n=4096 (Text/corrections_2026-10.md, section 5). A
 *     Roaring integration should align container arrays and spines.
 *     Halving the number of blocks vs. gap=16 still shortens the
 *     interpolation regardless of alignment.
 *   - The block load uses vld1q_u16_x2 (two paired 128-bit loads), which
 *     maps well to A76's two load AGUs.
 *   - AArch64/NEON only; the SSE2 fallback from the reference is gone.
 *   - No speculative prefetch inside the quaternary loop. Versions up to
 *     2026-10-12 issued one __builtin_prefetch per iteration at the start
 *     of block base + n/2; the archived main bench had it as a net loss
 *     (CORRECTION 2026-10-11 of an earlier "10-25% cold win" claim) and the
 *     dedicated A/Bs of 2026-10-12/13 confirmed that in the flushed main
 *     bench (slower warm at every size from 128 up, slower cold at 12 of 14)
 *     while finding a 3-13% gain only in the two-level harness's outer-hot
 *     modes from n ~ 667 (see the note in the loop below and
 *     Text/corrections_2026-10.md, section 5). Since 2026-10-13 this kernel
 *     and simd_quad_graviton are the same code (the two plain kernels
 *     compile to identical instructions; the sources differ only in
 *     comments and line wrapping), apart from the Graviton file's
 *     _spine_padded variants; the pi5 and gv4 columns of the Pi 5 main
 *     bench now measure identical code.
 *   - Alignment precondition (measured 2026-10-12/13): the "one block = one
 *     line" property needs a 64-byte-aligned carr, and the four-line n=4096
 *     spine a 64-byte-aligned spine; std::vector gives 16 bytes. With both
 *     aligned the spine kernels are 16-37% faster cold at every size from
 *     128 up in the flushed main bench (ten paired runs on the second Pi 5
 *     board, pi5_runs/rebench_flushed_eight_paired.txt; an upper bound,
 *     since the aligned copies' regular layout also streams better in that
 *     harness's sequential cold sweep -- the linear scan gains 9-18% there
 *     too) and 3-7% faster cold from n ~ 512 in the two-level kernel A/B
 *     (random access, the cleaner number), at no warm cost in the main
 *     bench (and a 4-13 ns hot cost in the two-level harness that is not
 *     understood). Callers that can align should; tiny arrays padded to a
 *     line pay footprint instead.
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
        // Until 2026-10-13 this loop ended with a speculative
        //     __builtin_prefetch(carr + (base + (n >> 1)) * gap);
        // aimed at the START of block base + n/2 while the next middle probe
        // reads the END of a block (same line only for a 64-byte-aligned carr
        // and n % 4 in {0, 1}), with an address that depends on the
        // just-updated `base`, i.e. at the same dependency depth as the next
        // iteration's demand loads. Removed after the dedicated A/Bs of
        // 2026-10-12/13 (Text/corrections_2026-10.md, section 5): in the
        // flushed main bench (ten paired runs, pi5 vs graviton columns) the
        // prefetch kernel was slower warm at every size from 128 up (+3% to
        // +8%, 10/10) and slower cold at 12 of those 14 sizes (up to +18%),
        // faster only at 1024 cold; in the two-level kernel A/B
        // (pi5_runs/sweep_ab1_findings.md) it was 3-13% faster in the
        // outer-hot modes from n ~ 667 and 4-8% slower in the cold modes. The
        // plain kernel is now the same code as simd_quad_graviton.
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

    // Prefetch the first line of the spine (one line, not "the whole
    // spine": at n=4096 the spine is 4 lines when line-aligned, 5 when
    // not, and the first-tier probes spine[32], spine[64], spine[96] all
    // sit outside the prefetched line). Cheap; the real cold win of the
    // spine is that the descent reads a contiguous 256 B instead of
    // chasing through the 8 KB array.
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

// Correctness check for pfC and sentinel scratches vs shipping hybrid.
#include <cstdio>
#include <cstdint>
#include <random>
#include <set>
#include <vector>

bool simd_quad_m4_spine_4096(const uint16_t *carr, const uint16_t *spine,
                             uint16_t pos);
bool simd_quad_m4_spine_4096_pfC(const uint16_t *carr, const uint16_t *spine,
                                 uint16_t pos);
bool simd_quad_m4_spine_4096_sentinel(const uint16_t *carr,
                                      const uint16_t *spine,
                                      const uint16_t *spine_lo,
                                      uint16_t pos);
bool simd_quad_m4_spine_4096_sentinel_2x(const uint16_t *carr,
                                         const uint16_t *spine_2x,
                                         uint16_t pos);
void simd_quad_m4_build_spine(const uint16_t *carr, int32_t cardinality,
                              uint16_t *spine);
void simd_quad_m4_build_spine_lo(const uint16_t *carr, int32_t cardinality,
                                 uint16_t *spine_lo);
void simd_quad_m4_build_spine_2x(const uint16_t *carr, int32_t cardinality,
                                 uint16_t *spine_2x);

int main() {
    std::mt19937 rng(42);
    std::uniform_int_distribution<int> d(0, 65535);

    int total = 0, mm_pfC = 0, mm_sent = 0, mm_2x = 0;
    for (int trial = 0; trial < 200; trial++) {
        std::set<uint16_t> s;
        while ((int)s.size() < 4096) s.insert((uint16_t)d(rng));
        std::vector<uint16_t> carr(s.begin(), s.end());
        std::vector<uint16_t> spine(64), spine_lo(64), spine_2x(128);
        simd_quad_m4_build_spine(carr.data(), 4096, spine.data());
        simd_quad_m4_build_spine_lo(carr.data(), 4096, spine_lo.data());
        simd_quad_m4_build_spine_2x(carr.data(), 4096, spine_2x.data());

        for (int q = 0; q < 256; q++) {
            uint16_t pos = (uint16_t)d(rng);
            bool a = simd_quad_m4_spine_4096(carr.data(), spine.data(), pos);
            bool b = simd_quad_m4_spine_4096_pfC(carr.data(), spine.data(), pos);
            bool c = simd_quad_m4_spine_4096_sentinel(carr.data(), spine.data(),
                                                     spine_lo.data(), pos);
            bool e = simd_quad_m4_spine_4096_sentinel_2x(carr.data(),
                                                       spine_2x.data(), pos);
            total++;
            if (a != b) { mm_pfC++;  if (mm_pfC  < 5) std::printf("pfC MISMATCH pos=%u a=%d b=%d\n", pos, a, b); }
            if (a != c) { mm_sent++; if (mm_sent < 5) std::printf("sent MISMATCH pos=%u a=%d c=%d\n", pos, a, c); }
            if (a != e) { mm_2x++;   if (mm_2x   < 5) std::printf("2x MISMATCH pos=%u a=%d e=%d\n", pos, a, e); }
        }
        for (int j = 0; j < 4096; j += 17) {
            uint16_t pos = carr[j];
            bool a = simd_quad_m4_spine_4096(carr.data(), spine.data(), pos);
            bool c = simd_quad_m4_spine_4096_sentinel(carr.data(), spine.data(),
                                                     spine_lo.data(), pos);
            bool e = simd_quad_m4_spine_4096_sentinel_2x(carr.data(),
                                                       spine_2x.data(), pos);
            total++;
            if (!a) std::printf("ERROR: shipping returned false on real elem %u\n", pos);
            if (a != c) { mm_sent++; if (mm_sent < 5) std::printf("sent MISMATCH (hit) pos=%u a=%d c=%d\n", pos, a, c); }
            if (a != e) { mm_2x++;   if (mm_2x   < 5) std::printf("2x MISMATCH (hit) pos=%u a=%d e=%d\n", pos, a, e); }
        }
        for (int blk = 0; blk < 64; blk++) {
            for (int j : {0, 63}) {
                uint16_t pos = carr[blk * 64 + j];
                bool a = simd_quad_m4_spine_4096(carr.data(), spine.data(), pos);
                bool c = simd_quad_m4_spine_4096_sentinel(carr.data(),
                          spine.data(), spine_lo.data(), pos);
                bool e = simd_quad_m4_spine_4096_sentinel_2x(carr.data(),
                          spine_2x.data(), pos);
                total++;
                if (a != c) { mm_sent++; if (mm_sent < 5)
                    std::printf("sent MISMATCH (edge) blk=%d j=%d pos=%u a=%d c=%d\n",
                                blk, j, pos, a, c); }
                if (a != e) { mm_2x++; if (mm_2x < 5)
                    std::printf("2x MISMATCH (edge) blk=%d j=%d pos=%u a=%d e=%d\n",
                                blk, j, pos, a, e); }
            }
        }
    }
    std::printf("checked %d queries; pfC=%d sent=%d sent_2x=%d mismatches\n",
                total, mm_pfC, mm_sent, mm_2x);
    return (mm_pfC + mm_sent + mm_2x) == 0 ? 0 : 1;
}

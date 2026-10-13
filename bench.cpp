// Correctness check + benchmark for simd_quad variants.
//
// Build (Apple M4 Max):
//   clang++ -O3 -mcpu=apple-m4 -std=c++20 \
//       bench.cpp simd_quad_pi5.c simd_quad_m4.c simd_quad_graviton.c -o bench
//
// Build (Raspberry Pi 5):
//   g++ -O3 -mcpu=cortex-a76 -std=c++20 \
//       bench.cpp simd_quad_pi5.c simd_quad_m4.c simd_quad_graviton.c -o bench
//
// Build (AWS Graviton 4 / Arm Neoverse V2):
//   g++ -O3 -mcpu=neoverse-v2 -std=c++20 \
//       bench.cpp simd_quad_pi5.c simd_quad_m4.c simd_quad_graviton.c -o bench
//
// Build (Intel server w/ AVX-512 + VBMI2; Ice Lake-SP, Sapphire/Emerald Rapids,
// Granite Rapids):
//   g++ -O3 -march=sapphirerapids -std=c++20 \
//       bench.cpp simd_quad_intel.c -o bench
//   (or: -march=icelake-server / -march=native on an Ice Lake-SP-or-newer host;
//    note -march=x86-64-v4 does NOT define __AVX512VBMI2__ and builds the AVX2 path)
//
// Build (Skylake-SP/X -- has AVX-512BW but no VBMI2; the zmm block check is
// intentionally gated off on this uarch due to AVX-512 frequency downclock;
// -march=native will correctly select the AVX2 path):
//   g++ -O3 -march=native -std=c++20 \
//       bench.cpp simd_quad_intel.c -o bench
//
// Build (Intel / AMD with AVX2 only):
//   g++ -O3 -march=haswell -std=c++20 \
//       bench.cpp simd_quad_intel.c -o bench
//
// Only the .c sources whose ISA matches the target are compiled; the
// host arch is auto-detected below. The reference simd_quad.c has no
// #includes and uses `constexpr`, so we #include it into this TU where
// the right arch header is already in scope.

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <random>
#include <set>
#include <vector>

#if defined(__ARM_NEON) || defined(__aarch64__)
  #define QUADSEARCH_ARCH_ARM 1
  #include <arm_neon.h>
#elif defined(__x86_64__) || defined(_M_X64) || defined(__i386__)
  #define QUADSEARCH_ARCH_X86 1
  #include <immintrin.h>
#else
  #error "Unsupported architecture for simd_quad benchmark"
#endif

// Pull the reference implementation in; it's a bare function body that
// picks its own code path via __ARM_NEON.
#include "simd_quad.c"

#if QUADSEARCH_ARCH_ARM
bool simd_quad_pi5(const uint16_t *carr, int32_t cardinality, uint16_t pos);
bool simd_quad_pi5_spine(const uint16_t *carr, const uint16_t *spine,
                         int32_t cardinality, uint16_t pos);
void simd_quad_pi5_build_spine(const uint16_t *carr, int32_t cardinality,
                               uint16_t *spine);
// _spine_4096 is the hybrid (3 quat + branchless 2-probe finish). The prior
// 3-quat + binary step + final-lo unroll was retired 2026-05-12 after the
// hybrid-vs-unroll A/B (hybrid -16.9% warm by ratio of medians, -31.0% paired
// per-run median, faster in 5/5 runs; cold within noise) -- same call pattern as EMR/GV4/M1.
bool simd_quad_pi5_spine_4096(const uint16_t *carr, const uint16_t *spine,
                              uint16_t pos);
// Compile-time spine specializations (port of the GV4 set). High-foot sizes
// {256, 1024, 4096} use a branchless 2-probe finish; low-foot sizes
// {512, 2048} are pure straight-line unrolls.
bool simd_quad_pi5_spine_256 (const uint16_t *carr, const uint16_t *spine, uint16_t pos);
bool simd_quad_pi5_spine_512 (const uint16_t *carr, const uint16_t *spine, uint16_t pos);
bool simd_quad_pi5_spine_1024(const uint16_t *carr, const uint16_t *spine, uint16_t pos);
bool simd_quad_pi5_spine_2048(const uint16_t *carr, const uint16_t *spine, uint16_t pos);

bool simd_quad_m4(const uint16_t *carr, int32_t cardinality, uint16_t pos);
bool simd_quad_m4_spine(const uint16_t *carr, const uint16_t *spine,
                        int32_t cardinality, uint16_t pos);
void simd_quad_m4_build_spine(const uint16_t *carr, int32_t cardinality,
                              uint16_t *spine);
bool simd_quad_m4_spine_4096(const uint16_t *carr, const uint16_t *spine,
                             uint16_t pos);

bool simd_quad_graviton(const uint16_t *carr, int32_t cardinality, uint16_t pos);
bool simd_quad_graviton_spine(const uint16_t *carr, const uint16_t *spine,
                              int32_t cardinality, uint16_t pos);
void simd_quad_graviton_build_spine(const uint16_t *carr, int32_t cardinality,
                                    uint16_t *spine);
bool simd_quad_graviton_spine_padded(const uint16_t *carr, const uint16_t *spine,
                                     int32_t cardinality, uint16_t pos);
void simd_quad_graviton_build_spine_padded(const uint16_t *carr,
                                           int32_t cardinality,
                                           uint16_t *spine);
// Compile-time spine specializations. n ∈ {256, 1024, 4096} are hybrids
// (unroll + branchless 2-probe finish); n ∈ {512, 2048} are low-foot
// unrolls (no binary tail to collapse).
bool simd_quad_graviton_spine_256(const uint16_t *carr,
                                  const uint16_t *spine, uint16_t pos);
bool simd_quad_graviton_spine_512(const uint16_t *carr,
                                  const uint16_t *spine, uint16_t pos);
bool simd_quad_graviton_spine_1024(const uint16_t *carr,
                                   const uint16_t *spine, uint16_t pos);
bool simd_quad_graviton_spine_2048(const uint16_t *carr,
                                   const uint16_t *spine, uint16_t pos);
bool simd_quad_graviton_spine_4096(const uint16_t *carr,
                                   const uint16_t *spine, uint16_t pos);
#endif

#if QUADSEARCH_ARCH_X86
bool simd_quad_intel(const uint16_t *carr, int32_t cardinality, uint16_t pos);
bool simd_quad_intel_spine(const uint16_t *carr, const uint16_t *spine,
                           int32_t cardinality, uint16_t pos);
void simd_quad_intel_build_spine(const uint16_t *carr, int32_t cardinality,
                                 uint16_t *spine);
bool simd_quad_intel_spine_4096(const uint16_t *carr, const uint16_t *spine,
                                uint16_t pos);
bool simd_quad_intel_spine_padded(const uint16_t *carr, const uint16_t *spine,
                                  int32_t cardinality, uint16_t pos);
void simd_quad_intel_build_spine_padded(const uint16_t *carr,
                                        int32_t cardinality, uint16_t *spine);
// Compile-time spine specializations (port of the GV4 set). High-foot
// sizes {256, 1024, 4096} use a branchless 2-probe finish; low-foot
// sizes {512, 2048} are pure straight-line unrolls. The existing
// _spine_4096 declaration above is the hybrid after the 2026-05-12
// EMR ship/no-ship call (hybrid beat the prior unroll -54.8% warm /
// -9.7% cold; unroll retired).
bool simd_quad_intel_spine_256 (const uint16_t *carr, const uint16_t *spine, uint16_t pos);
bool simd_quad_intel_spine_512 (const uint16_t *carr, const uint16_t *spine, uint16_t pos);
bool simd_quad_intel_spine_1024(const uint16_t *carr, const uint16_t *spine, uint16_t pos);
bool simd_quad_intel_spine_2048(const uint16_t *carr, const uint16_t *spine, uint16_t pos);
#endif

using clock_type = std::chrono::steady_clock;

static std::vector<uint16_t> make_sorted(std::mt19937 &rng, int n) {
    std::set<uint16_t> s;
    std::uniform_int_distribution<int> d(0, 65535);
    while ((int)s.size() < n) s.insert((uint16_t)d(rng));
    return std::vector<uint16_t>(s.begin(), s.end());
}

static bool linear_find(const uint16_t *a, int32_t n, uint16_t v) {
    return std::find(a, a + n, v) != a + n;
}
static bool std_bsearch(const uint16_t *a, int32_t n, uint16_t v) {
    return std::binary_search(a, a + n, v);
}

// ---- correctness ----
static void correctness() {
    std::mt19937 rng(12345);
    for (int n : {1, 2, 3, 7, 11, 15, 16, 17, 23, 31, 32, 33, 47, 63, 64, 65,
                  89, 100, 127, 128, 177, 255, 256, 333, 511, 512, 617, 1001,
                  1023, 1024, 1234, 1777, 2048, 2999, 3967, 4096}) {
        for (int trial = 0; trial < 50; trial++) {
            auto arr = make_sorted(rng, n);
#if QUADSEARCH_ARCH_ARM
            std::vector<uint16_t> spine_pi5(std::max(1, n / 32));
            std::vector<uint16_t> spine_m4(std::max(1, n / 64));
            std::vector<uint16_t> spine_gv4(std::max(1, n / 32));
            std::vector<uint16_t> spine_gv4p(std::max(1, n / 32) + 2);
            if (n >= 32) simd_quad_pi5_build_spine(arr.data(), n, spine_pi5.data());
            if (n >= 64) simd_quad_m4_build_spine(arr.data(), n, spine_m4.data());
            if (n >= 32) simd_quad_graviton_build_spine(arr.data(), n, spine_gv4.data());
            if (n >= 32) simd_quad_graviton_build_spine_padded(arr.data(), n, spine_gv4p.data());
#endif
#if QUADSEARCH_ARCH_X86
            std::vector<uint16_t> spine_intel(std::max(1, n / 32));
            std::vector<uint16_t> spine_intelp(std::max(1, n / 32) + 2);
            if (n >= 32) simd_quad_intel_build_spine(arr.data(), n, spine_intel.data());
            if (n >= 32) simd_quad_intel_build_spine_padded(arr.data(), n, spine_intelp.data());
#endif
            std::uniform_int_distribution<int> pick(0, 65535);
            for (int q = 0; q < 200; q++) {
                uint16_t target =
                    (q & 1) ? arr[pick(rng) % arr.size()] : (uint16_t)pick(rng);
                bool want  = std_bsearch(arr.data(), n, target);
                bool r_ref = simd_quad(arr.data(), n, target);
                if (r_ref != want) {
                    std::fprintf(stderr,
                                 "MISMATCH n=%d target=%u want=%d ref=%d\n",
                                 n, target, want, r_ref);
                    std::exit(1);
                }
#if QUADSEARCH_ARCH_ARM
                bool r_pi5      = simd_quad_pi5(arr.data(), n, target);
                bool r_pi5_spn  = simd_quad_pi5_spine(arr.data(), spine_pi5.data(), n, target);
                bool r_m4       = simd_quad_m4(arr.data(), n, target);
                bool r_m4_spn   = simd_quad_m4_spine(arr.data(), spine_m4.data(), n, target);
                bool r_gv4      = simd_quad_graviton(arr.data(), n, target);
                bool r_gv4_spn  = simd_quad_graviton_spine(arr.data(), spine_gv4.data(), n, target);
                bool r_gv4_spp  = simd_quad_graviton_spine_padded(arr.data(), spine_gv4p.data(), n, target);
                if (r_pi5 != want || r_pi5_spn != want ||
                    r_m4  != want || r_m4_spn  != want ||
                    r_gv4 != want || r_gv4_spn != want || r_gv4_spp != want) {
                    std::fprintf(stderr,
                                 "MISMATCH n=%d target=%u want=%d pi5=%d pi5s=%d m4=%d m4s=%d gv4=%d gv4s=%d gv4sp=%d\n",
                                 n, target, want, r_pi5, r_pi5_spn, r_m4, r_m4_spn, r_gv4, r_gv4_spn, r_gv4_spp);
                    std::exit(1);
                }
                if (n == 4096) {
                    bool r_gv4_4096 = simd_quad_graviton_spine_4096(
                        arr.data(), spine_gv4.data(), target);
                    bool r_m4_4096 = simd_quad_m4_spine_4096(
                        arr.data(), spine_m4.data(), target);
                    bool r_pi5_4096 = simd_quad_pi5_spine_4096(
                        arr.data(), spine_pi5.data(), target);
                    if (r_gv4_4096 != want || r_m4_4096 != want ||
                        r_pi5_4096 != want) {
                        std::fprintf(stderr,
                                     "MISMATCH n=%d target=%u want=%d gv4_4096=%d m4_4096=%d pi5_4096=%d\n",
                                     n, target, want, r_gv4_4096, r_m4_4096, r_pi5_4096);
                        std::exit(1);
                    }
                }
                // gv4 spine specializations: verify at each matching n.
                bool r_gvN = want;
                if      (n == 256)  r_gvN = simd_quad_graviton_spine_256 (arr.data(), spine_gv4.data(), target);
                else if (n == 512)  r_gvN = simd_quad_graviton_spine_512 (arr.data(), spine_gv4.data(), target);
                else if (n == 1024) r_gvN = simd_quad_graviton_spine_1024(arr.data(), spine_gv4.data(), target);
                else if (n == 2048) r_gvN = simd_quad_graviton_spine_2048(arr.data(), spine_gv4.data(), target);
                if (r_gvN != want) {
                    std::fprintf(stderr,
                                 "MISMATCH n=%d target=%u want=%d gv4_spine_N=%d\n",
                                 n, target, want, r_gvN);
                    std::exit(1);
                }
                // pi5 spine specializations: verify at each matching n.
                bool r_piN = want;
                if      (n == 256)  r_piN = simd_quad_pi5_spine_256 (arr.data(), spine_pi5.data(), target);
                else if (n == 512)  r_piN = simd_quad_pi5_spine_512 (arr.data(), spine_pi5.data(), target);
                else if (n == 1024) r_piN = simd_quad_pi5_spine_1024(arr.data(), spine_pi5.data(), target);
                else if (n == 2048) r_piN = simd_quad_pi5_spine_2048(arr.data(), spine_pi5.data(), target);
                if (r_piN != want) {
                    std::fprintf(stderr,
                                 "MISMATCH n=%d target=%u want=%d pi5_spine_N=%d\n",
                                 n, target, want, r_piN);
                    std::exit(1);
                }
#endif
#if QUADSEARCH_ARCH_X86
                bool r_intel     = simd_quad_intel(arr.data(), n, target);
                bool r_intel_spn = simd_quad_intel_spine(arr.data(), spine_intel.data(), n, target);
                bool r_intel_spp = simd_quad_intel_spine_padded(arr.data(), spine_intelp.data(), n, target);
                if (r_intel != want || r_intel_spn != want || r_intel_spp != want) {
                    std::fprintf(stderr,
                                 "MISMATCH n=%d target=%u want=%d intel=%d intels=%d intelsp=%d\n",
                                 n, target, want, r_intel, r_intel_spn, r_intel_spp);
                    std::exit(1);
                }
                if (n == 4096) {
                    bool r_4096 = simd_quad_intel_spine_4096(
                        arr.data(), spine_intel.data(), target);
                    if (r_4096 != want) {
                        std::fprintf(stderr,
                                     "MISMATCH n=%d target=%u want=%d intel_4096=%d\n",
                                     n, target, want, r_4096);
                        std::exit(1);
                    }
                }
                // Intel spine_N specializations: verify at each matching n.
                bool r_intelN = want;
                if      (n == 256)  r_intelN = simd_quad_intel_spine_256 (arr.data(), spine_intel.data(), target);
                else if (n == 512)  r_intelN = simd_quad_intel_spine_512 (arr.data(), spine_intel.data(), target);
                else if (n == 1024) r_intelN = simd_quad_intel_spine_1024(arr.data(), spine_intel.data(), target);
                else if (n == 2048) r_intelN = simd_quad_intel_spine_2048(arr.data(), spine_intel.data(), target);
                if (r_intelN != want) {
                    std::fprintf(stderr,
                                 "MISMATCH n=%d target=%u want=%d intel_spine_N=%d\n",
                                 n, target, want, r_intelN);
                    std::exit(1);
                }
#endif
            }
        }
    }
    std::printf("correctness: ok\n");
}

// ---- benchmark ----
// Each algorithm is called through a lambda that knows how to dispatch on
// array index. This lets the spine variant reach for its per-array spine
// without inflating the other algorithms' signatures.
using Query = bool(*)(size_t arr_idx, uint16_t target);

template <typename Fn>
static double bench_warm(Fn q, size_t num_arrays,
                         const std::vector<uint16_t> &targets, int repeats) {
    volatile uint64_t acc = 0;
    auto t0 = clock_type::now();
    for (size_t i = 0; i < num_arrays; i++) {
        for (int r = 0; r < repeats; r++) {
            uint16_t t = targets[(i * 131u + r * 17u) % targets.size()];
            acc += q(i, t);
        }
    }
    auto t1 = clock_type::now();
    (void)acc;
    double ns = std::chrono::duration<double, std::nano>(t1 - t0).count();
    return ns / (double)(num_arrays * repeats);
}

// LLC thrash before every cold measurement (added 2026-10-11; same size and
// shape as bench_twolevel.cpp's thrash_llc, so "cold" means the same thing
// in both harnesses): a stride-64 volatile write over 512 MB, intended to
// evict the arrays, spines and target vectors from every cache level on
// every host in the project (the largest LLC is Emerald Rapids' ~260 MB L3).
// Verified on the Pi 5 (A76) only: a 1 MB thrash moves the n=8/16 cold
// cells out of L1, and the default 512 MB at canonical intensity
// (pi5_runs/rebench_flushed_run1.txt, 2026-10-12) puts the n=8 cold cells
// at 38-74 ns against 5-18 ns in the pre-flush archive and the n=4096
// spine cells 1.3-1.5x above it (pre-flush, only the array lines were cold
// there; the spines, the pointer and target vectors and probably the TLB
// were still warm). On the other hosts inspect the
// first flushed run before quoting a cross-host cold number -- small-n cold
// cells must sit at DRAM latency, not at the archived ~1.5 ns M4 / ~2.5 ns
// EMR levels; Intel LLCs use scan-resistant insertion and 512 MB is only
// ~2x the EMR L3. Before this date bench_cold had no flush, so every archived
// main-bench run (e.g. {host}_runs/rebench_run*.txt, hybrid_run*.txt,
// shipped_run*.txt, fullsweep_run*.txt) has a cold column that was a DRAM
// miss on the Pi 5 at n > 256 only, L2/L3-resident at n <= 256 there, and
// an L2/L3/SLC hit on the other five hosts (Text/corrections_2026-10.md,
// section 5); the plot.py dicts derived from them are not comparable with
// output of this version, which prints a "# cold column:" provenance line.
// The size can be overridden at build time, e.g.
// -DQUADSEARCH_THRASH_BYTES='(1ull<<20)' for a quick functional check; the
// default build does one 512 MB pass per cold measurement -- 228 on ARM and
// 133 on x86 for the plain and '*' rows, plus 198 (ARM) / 110 (x86) for the
// 'nA' aligned rows since 2026-10-12, so 426 / 243 passes and ~213 GB /
// ~122 GB written per ./bench run -- and holds a 512 MB scratch buffer.
#ifndef QUADSEARCH_THRASH_BYTES
#define QUADSEARCH_THRASH_BYTES (512ull * 1024ull * 1024ull)
#endif
static constexpr size_t kThrashBytes = QUADSEARCH_THRASH_BYTES;
static_assert(kThrashBytes >= 64, "QUADSEARCH_THRASH_BYTES must cover at least one cache line");

static void thrash_llc() {
    static std::vector<uint8_t> scratch;
    if (scratch.empty()) scratch.assign(kThrashBytes, 0);
    // Stride-64 write touches every line. volatile pointer prevents the
    // compiler from eliding the stores.
    volatile uint8_t *p = scratch.data();
    for (size_t i = 0; i < kThrashBytes; i += 64) p[i] = (uint8_t)i;
}

// Cache-line-aligned copies for the 'nA' rows (added 2026-10-12). The
// kernels' "one block = one cache line" argument holds only for a
// line-aligned carr (and a line-aligned spine), which std::vector's 16-byte
// alignment does not give: about three of four 64-byte blocks straddle two
// lines in the plain rows. Each 'nA' row repeats the warm and cold columns
// of the plain row above it on copies of the same arrays and spines aligned
// to the host's cache line (64 B on the A76, Intel and Neoverse V2 hosts,
// 128 B on the Apple P-cores) with their sizes rounded up to it, as a
// line-aligned container allocator would do, so the pair is a within-run
// A/B of the alignment (and, below one block, of that footprint rounding
// alone). The n = 8 pair is the control: a 16-byte array at 16-byte
// alignment never straddles a line, so '8A' vs '8' can only show the
// layout difference (the aligned copies occupy a full line each), not
// alignment; from n = 11 up the plain arrays straddle (11% of them at
// n = 11, 25% at 16, 34% at 23, 75% at 32 and above, by a layout probe of
// this allocation sequence) and the pair isolates alignment. The aligned rows reach the arrays through 24-byte entries
// (AlignedRef) like the plain rows' std::vector headers, so the pointer
// traffic is the same, sequential and cold after the flush in both. Parsers keyed on
// '<digits> |' rows ({host}_runs/compute_medians.py, reproduce.sh) skip the
// 'nA' rows.
#if defined(__APPLE__)
static constexpr size_t kAlign = 128;
#else
static constexpr size_t kAlign = 64;
#endif
struct FreeDeleter {
    void operator()(void *p) const { std::free(p); }
};
using AlignedBuf = std::unique_ptr<uint16_t, FreeDeleter>;
// The aligned rows reach their arrays through a vector of these, 24 bytes per
// entry like the std::vector headers the plain rows read, so the per-array
// pointer traffic of the two rows is the same (8-byte pointers would pack
// three times as many arrays per line and favour the aligned rows).
struct AlignedRef {
    AlignedBuf buf;
    uint64_t pad[2];
};
static_assert(sizeof(AlignedRef) == sizeof(std::vector<uint16_t>), "AlignedRef must match the vector header size");
static AlignedBuf aligned_copy(const std::vector<uint16_t> &v) {
    size_t bytes = std::max<size_t>(v.size(), 1) * sizeof(uint16_t);
    size_t rounded = (bytes + kAlign - 1) / kAlign * kAlign;  // aligned_alloc wants a multiple of the alignment
    void *p = std::aligned_alloc(kAlign, rounded);
    if (!p || ((uintptr_t)p & (kAlign - 1)) != 0) {
        std::fprintf(stderr, "aligned_alloc(%zu, %zu) failed\n", kAlign, rounded);
        std::exit(1);
    }
    if (!v.empty()) std::memcpy(p, v.data(), v.size() * sizeof(uint16_t));
    return AlignedBuf((uint16_t *)p);
}

// One query per array, arrays visited in allocation order, after
// thrash_llc(). The thrash is outside the timed region. What is timed is
// the first touch since the flush of every array (and spine, target and
// pointer vector), with every cache level full of dirty scratch lines and
// the TLB cold -- not an isolated DRAM miss per query: at small n the 4000
// arrays are adjacent malloc chunks, so the pass is a prefetcher-assisted
// sequential heap sweep. All of that is identical for every algorithm at a
// given size, so within one host the column remains a fair A/B, with one
// asymmetry worth knowing: the spine columns also read the spine-pointer
// vector (24 B per array, sequential), which the flush makes cold too and
// which the non-spine columns never touch.
template <typename Fn>
static double bench_cold(Fn q, size_t num_arrays,
                         const std::vector<uint16_t> &targets) {
    thrash_llc();
    volatile uint64_t acc = 0;
    auto t0 = clock_type::now();
    for (size_t i = 0; i < num_arrays; i++) {
        uint16_t t = targets[i % targets.size()];
        acc += q(i, t);
    }
    auto t1 = clock_type::now();
    (void)acc;
    double ns = std::chrono::duration<double, std::nano>(t1 - t0).count();
    return ns / (double)num_arrays;
}

int main(int argc, char **argv) {
    correctness();

    int num_arrays = (argc > 1) ? std::atoi(argv[1]) : 2000;
    int warm_reps  = (argc > 2) ? std::atoi(argv[2]) : 2000;

    // Provenance line for archived outputs: files without it predate the
    // cold-column flush (parsers key on numeric rows, so '#' lines are inert).
    std::printf("\n# cold column: thrash_llc() %.1f MB before every cold pass "
                "(flush added 2026-10-11)\n", (double)kThrashBytes / 1048576.0);
    std::printf("# aligned rows: each 'nA' row repeats the warm and cold columns of the plain row "
                "above it on %zu-byte-aligned copies of the same arrays and spines (added 2026-10-12); "
                "plain rows use std::vector storage, 16-byte aligned\n", kAlign);
#if QUADSEARCH_ARCH_ARM
    std::printf("\n%-6s | %-76s | %-76s\n", "size",
        "warm ns/q:  linear  binary  simd   pi5   pi5s    m4   m4s   gv4   gv4s",
        "cold ns/q:  linear  binary  simd   pi5   pi5s    m4   m4s   gv4   gv4s");
#else
    std::printf("\n%-6s | %-48s | %-48s\n", "size",
        "warm ns/q:  linear  binary  simd   intel  intels",
        "cold ns/q:  linear  binary  simd   intel  intels");
#endif
    std::printf("-------+"
#if QUADSEARCH_ARCH_ARM
        "----------------------------------------------------------------------------+"
        "----------------------------------------------------------------------------\n");
#else
        "------------------------------------------------+"
        "------------------------------------------------\n");
#endif

    // Power-of-2 sizes are the "hero" cells for compile-time specializations.
    // Additional non-power-of-2 n (2026-05-12, Lemire's ask) exercise the
    // general-n path: below-gap scalar fallback (11, 23), num_blocks <= 3
    // fallback (47, 89), non-power-of-2 num_blocks in the spine path (177,
    // 333, 617, 1001, 1234, 1777), and upper-range pre-specialization
    // (2999, 3967).
    for (int size : {8, 11, 16, 23, 32, 47, 64, 89, 128, 177, 256, 333, 512,
                     617, 1001, 1024, 1234, 1777, 2048, 2999, 3967, 4096}) {
        std::mt19937 rng(0xC0FFEE ^ size);
        std::vector<std::vector<uint16_t>> arrs;
        arrs.reserve(num_arrays);
#if QUADSEARCH_ARCH_ARM
        std::vector<std::vector<uint16_t>> spines_pi5;
        std::vector<std::vector<uint16_t>> spines_m4;
        std::vector<std::vector<uint16_t>> spines_gv4;
        std::vector<std::vector<uint16_t>> spines_gv4p;
        spines_pi5.reserve(num_arrays);
        spines_m4.reserve(num_arrays);
        spines_gv4.reserve(num_arrays);
        spines_gv4p.reserve(num_arrays);
#endif
#if QUADSEARCH_ARCH_X86
        std::vector<std::vector<uint16_t>> spines_intel;
        std::vector<std::vector<uint16_t>> spines_intelp;
        spines_intel.reserve(num_arrays);
        spines_intelp.reserve(num_arrays);
#endif
        for (int i = 0; i < num_arrays; i++) {
            arrs.push_back(make_sorted(rng, size));
#if QUADSEARCH_ARCH_ARM
            std::vector<uint16_t> sp_pi5(std::max(1, size / 32));
            std::vector<uint16_t> sp_m4(std::max(1, size / 64));
            std::vector<uint16_t> sp_gv4(std::max(1, size / 32));
            std::vector<uint16_t> sp_gv4p(std::max(1, size / 32) + 2);
            if (size >= 32)
                simd_quad_pi5_build_spine(arrs.back().data(), size, sp_pi5.data());
            if (size >= 64)
                simd_quad_m4_build_spine(arrs.back().data(), size, sp_m4.data());
            if (size >= 32)
                simd_quad_graviton_build_spine(arrs.back().data(), size, sp_gv4.data());
            if (size >= 32)
                simd_quad_graviton_build_spine_padded(arrs.back().data(), size, sp_gv4p.data());
            spines_pi5.push_back(std::move(sp_pi5));
            spines_m4.push_back(std::move(sp_m4));
            spines_gv4.push_back(std::move(sp_gv4));
            spines_gv4p.push_back(std::move(sp_gv4p));
#endif
#if QUADSEARCH_ARCH_X86
            std::vector<uint16_t> sp_intel(std::max(1, size / 32));
            std::vector<uint16_t> sp_intelp(std::max(1, size / 32) + 2);
            if (size >= 32)
                simd_quad_intel_build_spine(arrs.back().data(), size, sp_intel.data());
            if (size >= 32)
                simd_quad_intel_build_spine_padded(arrs.back().data(), size, sp_intelp.data());
            spines_intel.push_back(std::move(sp_intel));
            spines_intelp.push_back(std::move(sp_intelp));
#endif
        }

        // Line-aligned copies of every array and spine for the 'nA' rows:
        // same values, line-aligned addresses (see aligned_copy).
        std::vector<AlignedRef> arrs_al;
        arrs_al.reserve(num_arrays);
        for (int i = 0; i < num_arrays; i++) arrs_al.push_back(AlignedRef{aligned_copy(arrs[i]), {0, 0}});
#if QUADSEARCH_ARCH_ARM
        std::vector<AlignedRef> spines_pi5_al, spines_m4_al, spines_gv4_al;
        spines_pi5_al.reserve(num_arrays);
        spines_m4_al.reserve(num_arrays);
        spines_gv4_al.reserve(num_arrays);
        for (int i = 0; i < num_arrays; i++) {
            spines_pi5_al.push_back(AlignedRef{aligned_copy(spines_pi5[i]), {0, 0}});
            spines_m4_al.push_back(AlignedRef{aligned_copy(spines_m4[i]), {0, 0}});
            spines_gv4_al.push_back(AlignedRef{aligned_copy(spines_gv4[i]), {0, 0}});
        }
#endif
#if QUADSEARCH_ARCH_X86
        std::vector<AlignedRef> spines_intel_al;
        spines_intel_al.reserve(num_arrays);
        for (int i = 0; i < num_arrays; i++) spines_intel_al.push_back(AlignedRef{aligned_copy(spines_intel[i]), {0, 0}});
#endif

        std::vector<uint16_t> targets;
        targets.reserve(num_arrays);
        std::uniform_int_distribution<int> pick(0, 65535);
        for (int i = 0; i < num_arrays; i++) {
            if (i & 1) targets.push_back(arrs[i][pick(rng) % size]);
            else       targets.push_back((uint16_t)pick(rng));
        }

        auto q_linear = [&](size_t i, uint16_t t) {
            return linear_find(arrs[i].data(), size, t);
        };
        auto q_binary = [&](size_t i, uint16_t t) {
            return std_bsearch(arrs[i].data(), size, t);
        };
        auto q_simd = [&](size_t i, uint16_t t) {
            return simd_quad(arrs[i].data(), size, t);
        };
#if QUADSEARCH_ARCH_ARM
        auto q_pi5 = [&](size_t i, uint16_t t) {
            return simd_quad_pi5(arrs[i].data(), size, t);
        };
        auto q_pi5_spine = [&](size_t i, uint16_t t) {
            return simd_quad_pi5_spine(arrs[i].data(), spines_pi5[i].data(), size, t);
        };
        auto q_m4 = [&](size_t i, uint16_t t) {
            return simd_quad_m4(arrs[i].data(), size, t);
        };
        auto q_m4_spine = [&](size_t i, uint16_t t) {
            return simd_quad_m4_spine(arrs[i].data(), spines_m4[i].data(), size, t);
        };
        auto q_gv4 = [&](size_t i, uint16_t t) {
            return simd_quad_graviton(arrs[i].data(), size, t);
        };
        auto q_gv4_spine = [&](size_t i, uint16_t t) {
            return simd_quad_graviton_spine(arrs[i].data(), spines_gv4[i].data(), size, t);
        };

        double w[9], c[9];
        w[0] = bench_warm(q_linear,    num_arrays, targets, warm_reps);
        w[1] = bench_warm(q_binary,    num_arrays, targets, warm_reps);
        w[2] = bench_warm(q_simd,      num_arrays, targets, warm_reps);
        w[3] = bench_warm(q_pi5,       num_arrays, targets, warm_reps);
        w[4] = bench_warm(q_pi5_spine, num_arrays, targets, warm_reps);
        w[5] = bench_warm(q_m4,        num_arrays, targets, warm_reps);
        w[6] = bench_warm(q_m4_spine,  num_arrays, targets, warm_reps);
        w[7] = bench_warm(q_gv4,       num_arrays, targets, warm_reps);
        w[8] = bench_warm(q_gv4_spine, num_arrays, targets, warm_reps);
        c[0] = bench_cold(q_linear,    num_arrays, targets);
        c[1] = bench_cold(q_binary,    num_arrays, targets);
        c[2] = bench_cold(q_simd,      num_arrays, targets);
        c[3] = bench_cold(q_pi5,       num_arrays, targets);
        c[4] = bench_cold(q_pi5_spine, num_arrays, targets);
        c[5] = bench_cold(q_m4,        num_arrays, targets);
        c[6] = bench_cold(q_m4_spine,  num_arrays, targets);
        c[7] = bench_cold(q_gv4,       num_arrays, targets);
        c[8] = bench_cold(q_gv4_spine, num_arrays, targets);

        std::printf("%5d  | %7.1f %7.1f %6.1f %6.1f %6.1f %6.1f %6.1f %6.1f %6.1f | "
                    "%7.1f %7.1f %6.1f %6.1f %6.1f %6.1f %6.1f %6.1f %6.1f\n",
                    size, w[0], w[1], w[2], w[3], w[4], w[5], w[6], w[7], w[8],
                    c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7], c[8]);

        // Aligned row ('nA'): the same nine kernels on the line-aligned
        // copies, warm then cold, right after the plain row so the pair sits
        // close in time (see aligned_copy). Same targets, same order. The
        // '*' A/B rows below still compare against this plain row's w[]/c[],
        // now measured one 'nA' block earlier (~20 s at n = 4096), so their
        // warm halves are a little more exposed to a clock step under
        // ondemand than before; their cold halves each follow a flush.
        {
            auto qa_linear = [&](size_t i, uint16_t t) {
                return linear_find(arrs_al[i].buf.get(), size, t);
            };
            auto qa_binary = [&](size_t i, uint16_t t) {
                return std_bsearch(arrs_al[i].buf.get(), size, t);
            };
            auto qa_simd = [&](size_t i, uint16_t t) {
                return simd_quad(arrs_al[i].buf.get(), size, t);
            };
            auto qa_pi5 = [&](size_t i, uint16_t t) {
                return simd_quad_pi5(arrs_al[i].buf.get(), size, t);
            };
            auto qa_pi5_spine = [&](size_t i, uint16_t t) {
                return simd_quad_pi5_spine(arrs_al[i].buf.get(), spines_pi5_al[i].buf.get(), size, t);
            };
            auto qa_m4 = [&](size_t i, uint16_t t) {
                return simd_quad_m4(arrs_al[i].buf.get(), size, t);
            };
            auto qa_m4_spine = [&](size_t i, uint16_t t) {
                return simd_quad_m4_spine(arrs_al[i].buf.get(), spines_m4_al[i].buf.get(), size, t);
            };
            auto qa_gv4 = [&](size_t i, uint16_t t) {
                return simd_quad_graviton(arrs_al[i].buf.get(), size, t);
            };
            auto qa_gv4_spine = [&](size_t i, uint16_t t) {
                return simd_quad_graviton_spine(arrs_al[i].buf.get(), spines_gv4_al[i].buf.get(), size, t);
            };
            double wa[9], ca[9];
            wa[0] = bench_warm(qa_linear,    num_arrays, targets, warm_reps);
            wa[1] = bench_warm(qa_binary,    num_arrays, targets, warm_reps);
            wa[2] = bench_warm(qa_simd,      num_arrays, targets, warm_reps);
            wa[3] = bench_warm(qa_pi5,       num_arrays, targets, warm_reps);
            wa[4] = bench_warm(qa_pi5_spine, num_arrays, targets, warm_reps);
            wa[5] = bench_warm(qa_m4,        num_arrays, targets, warm_reps);
            wa[6] = bench_warm(qa_m4_spine,  num_arrays, targets, warm_reps);
            wa[7] = bench_warm(qa_gv4,       num_arrays, targets, warm_reps);
            wa[8] = bench_warm(qa_gv4_spine, num_arrays, targets, warm_reps);
            ca[0] = bench_cold(qa_linear,    num_arrays, targets);
            ca[1] = bench_cold(qa_binary,    num_arrays, targets);
            ca[2] = bench_cold(qa_simd,      num_arrays, targets);
            ca[3] = bench_cold(qa_pi5,       num_arrays, targets);
            ca[4] = bench_cold(qa_pi5_spine, num_arrays, targets);
            ca[5] = bench_cold(qa_m4,        num_arrays, targets);
            ca[6] = bench_cold(qa_m4_spine,  num_arrays, targets);
            ca[7] = bench_cold(qa_gv4,       num_arrays, targets);
            ca[8] = bench_cold(qa_gv4_spine, num_arrays, targets);
            std::printf("%4dA  | %7.1f %7.1f %6.1f %6.1f %6.1f %6.1f %6.1f %6.1f %6.1f | "
                        "%7.1f %7.1f %6.1f %6.1f %6.1f %6.1f %6.1f %6.1f %6.1f\n",
                        size, wa[0], wa[1], wa[2], wa[3], wa[4], wa[5], wa[6], wa[7], wa[8],
                        ca[0], ca[1], ca[2], ca[3], ca[4], ca[5], ca[6], ca[7], ca[8]);
        }

        // GV4 padded-descent A/B at every size. Kept as direct comparator
        // to the compile-time spine_N specializations (same problem, two
        // different mechanisms: pad removes data-dependent iter count via
        // sentinels; spine_N removes it via constant-offset unrolling).
        if (size >= 32) {
            auto q_gv4_spine_pad = [&](size_t i, uint16_t t) {
                return simd_quad_graviton_spine_padded(
                    arrs[i].data(), spines_gv4p[i].data(), size, t);
            };
            double w_gv4p = bench_warm(q_gv4_spine_pad, num_arrays, targets, warm_reps);
            double c_gv4p = bench_cold(q_gv4_spine_pad, num_arrays, targets);
            std::printf("%5d* | gv4_spine=%.2f gv4_spine_pad=%.2f  (warm)  | "
                        "gv4_spine=%.2f gv4_spine_pad=%.2f  (cold)\n",
                        size, w[8], w_gv4p, c[8], c_gv4p);
        }

        // Shipping spine specializations for n ∈ {256, 512, 1024, 2048,
        // 4096}. Hybrid (unroll + branchless 2-probe finish) at high-foot
        // sizes 256/1024/4096; pure unroll at low-foot sizes 512/2048.
        if (size == 256 || size == 512 || size == 1024 ||
            size == 2048 || size == 4096) {
            double w_n = 0, c_n = 0;
            if (size == 256) {
                auto q = [&](size_t i, uint16_t t) {
                    return simd_quad_graviton_spine_256(arrs[i].data(), spines_gv4[i].data(), t);
                };
                w_n = bench_warm(q, num_arrays, targets, warm_reps);
                c_n = bench_cold(q, num_arrays, targets);
            } else if (size == 512) {
                auto q = [&](size_t i, uint16_t t) {
                    return simd_quad_graviton_spine_512(arrs[i].data(), spines_gv4[i].data(), t);
                };
                w_n = bench_warm(q, num_arrays, targets, warm_reps);
                c_n = bench_cold(q, num_arrays, targets);
            } else if (size == 1024) {
                auto q = [&](size_t i, uint16_t t) {
                    return simd_quad_graviton_spine_1024(arrs[i].data(), spines_gv4[i].data(), t);
                };
                w_n = bench_warm(q, num_arrays, targets, warm_reps);
                c_n = bench_cold(q, num_arrays, targets);
            } else if (size == 2048) {
                auto q = [&](size_t i, uint16_t t) {
                    return simd_quad_graviton_spine_2048(arrs[i].data(), spines_gv4[i].data(), t);
                };
                w_n = bench_warm(q, num_arrays, targets, warm_reps);
                c_n = bench_cold(q, num_arrays, targets);
            } else if (size == 4096) {
                auto q = [&](size_t i, uint16_t t) {
                    return simd_quad_graviton_spine_4096(arrs[i].data(), spines_gv4[i].data(), t);
                };
                w_n = bench_warm(q, num_arrays, targets, warm_reps);
                c_n = bench_cold(q, num_arrays, targets);
            }
            std::printf("%5d* | gv4_spine=%.2f gv4_spine_%d=%.2f  (warm)  | "
                        "gv4_spine=%.2f gv4_spine_%d=%.2f  (cold)\n",
                        size, w[8], size, w_n, c[8], size, c_n);
        }

        // Pi 5 compile-time spine specializations. Identical code to the
        // GV4 set (every simd_quad_pi5_spine* function matches its
        // simd_quad_graviton_spine* twin after comment stripping), so on
        // one host the two rows differ only by measurement noise and
        // order. Prints a per-size A/B vs the general-n pi5_spine so the
        // warm sawtooth vs straight-line unroll is visible. Note that at
        // n=4096 simd_quad_pi5_spine_4096 is also timed in the cross-host
        // block further down, so archives carry two rows for it per run;
        // aggregators use the last (cross-host) row, as {host}_runs/compute_medians.py does.
        if (size == 256 || size == 512 || size == 1024 ||
            size == 2048 || size == 4096) {
            double w_pin = 0, c_pin = 0;
            if (size == 256) {
                auto q = [&](size_t i, uint16_t t) {
                    return simd_quad_pi5_spine_256(arrs[i].data(), spines_pi5[i].data(), t);
                };
                w_pin = bench_warm(q, num_arrays, targets, warm_reps);
                c_pin = bench_cold(q, num_arrays, targets);
            } else if (size == 512) {
                auto q = [&](size_t i, uint16_t t) {
                    return simd_quad_pi5_spine_512(arrs[i].data(), spines_pi5[i].data(), t);
                };
                w_pin = bench_warm(q, num_arrays, targets, warm_reps);
                c_pin = bench_cold(q, num_arrays, targets);
            } else if (size == 1024) {
                auto q = [&](size_t i, uint16_t t) {
                    return simd_quad_pi5_spine_1024(arrs[i].data(), spines_pi5[i].data(), t);
                };
                w_pin = bench_warm(q, num_arrays, targets, warm_reps);
                c_pin = bench_cold(q, num_arrays, targets);
            } else if (size == 2048) {
                auto q = [&](size_t i, uint16_t t) {
                    return simd_quad_pi5_spine_2048(arrs[i].data(), spines_pi5[i].data(), t);
                };
                w_pin = bench_warm(q, num_arrays, targets, warm_reps);
                c_pin = bench_cold(q, num_arrays, targets);
            } else if (size == 4096) {
                auto q = [&](size_t i, uint16_t t) {
                    return simd_quad_pi5_spine_4096(arrs[i].data(), spines_pi5[i].data(), t);
                };
                w_pin = bench_warm(q, num_arrays, targets, warm_reps);
                c_pin = bench_cold(q, num_arrays, targets);
            }
            std::printf("%5d* | pi5_spine=%.2f pi5_spine_%d=%.2f  (warm)  | "
                        "pi5_spine=%.2f pi5_spine_%d=%.2f  (cold)\n",
                        size, w[4], size, w_pin, c[4], size, c_pin);
        }

        // Cross-host n=4096 A/B rows for m4 and pi5 (unchanged shape).
        // GV4's own 4096 A/B is already printed above.
        if (size == 4096) {
            auto q_m4_4096 = [&](size_t i, uint16_t t) {
                return simd_quad_m4_spine_4096(
                    arrs[i].data(), spines_m4[i].data(), t);
            };
            double w_m4_4096 = bench_warm(q_m4_4096, num_arrays, targets, warm_reps);
            double c_m4_4096 = bench_cold(q_m4_4096, num_arrays, targets);
            std::printf(" 4096* |  m4_spine=%.2f  m4_spine_4096=%.2f  (warm)  | "
                        " m4_spine=%.2f  m4_spine_4096=%.2f  (cold)\n",
                        w[6], w_m4_4096, c[6], c_m4_4096);

            auto q_pi5_4096 = [&](size_t i, uint16_t t) {
                return simd_quad_pi5_spine_4096(
                    arrs[i].data(), spines_pi5[i].data(), t);
            };
            double w_pi5_4096 = bench_warm(q_pi5_4096, num_arrays, targets, warm_reps);
            double c_pi5_4096 = bench_cold(q_pi5_4096, num_arrays, targets);
            std::printf(" 4096* | pi5_spine=%.2f pi5_spine_4096=%.2f  (warm)  | "
                        "pi5_spine=%.2f pi5_spine_4096=%.2f  (cold)\n",
                        w[4], w_pi5_4096, c[4], c_pi5_4096);
        }
#endif
#if QUADSEARCH_ARCH_X86
        auto q_intel = [&](size_t i, uint16_t t) {
            return simd_quad_intel(arrs[i].data(), size, t);
        };
        auto q_intel_spine = [&](size_t i, uint16_t t) {
            return simd_quad_intel_spine(arrs[i].data(), spines_intel[i].data(), size, t);
        };

        double w[5], c[5];
        w[0] = bench_warm(q_linear,      num_arrays, targets, warm_reps);
        w[1] = bench_warm(q_binary,      num_arrays, targets, warm_reps);
        w[2] = bench_warm(q_simd,        num_arrays, targets, warm_reps);
        w[3] = bench_warm(q_intel,       num_arrays, targets, warm_reps);
        w[4] = bench_warm(q_intel_spine, num_arrays, targets, warm_reps);
        c[0] = bench_cold(q_linear,      num_arrays, targets);
        c[1] = bench_cold(q_binary,      num_arrays, targets);
        c[2] = bench_cold(q_simd,        num_arrays, targets);
        c[3] = bench_cold(q_intel,       num_arrays, targets);
        c[4] = bench_cold(q_intel_spine, num_arrays, targets);

        std::printf("%5d  | %7.1f %7.1f %6.1f %6.1f %6.1f              | "
                    "%7.1f %7.1f %6.1f %6.1f %6.1f\n",
                    size, w[0], w[1], w[2], w[3], w[4],
                    c[0], c[1], c[2], c[3], c[4]);

        // Aligned row ('nA'): the same five kernels on the line-aligned
        // copies, warm then cold, right after the plain row (see aligned_copy).
        {
            auto qa_linear = [&](size_t i, uint16_t t) {
                return linear_find(arrs_al[i].buf.get(), size, t);
            };
            auto qa_binary = [&](size_t i, uint16_t t) {
                return std_bsearch(arrs_al[i].buf.get(), size, t);
            };
            auto qa_simd = [&](size_t i, uint16_t t) {
                return simd_quad(arrs_al[i].buf.get(), size, t);
            };
            auto qa_intel = [&](size_t i, uint16_t t) {
                return simd_quad_intel(arrs_al[i].buf.get(), size, t);
            };
            auto qa_intel_spine = [&](size_t i, uint16_t t) {
                return simd_quad_intel_spine(arrs_al[i].buf.get(), spines_intel_al[i].buf.get(), size, t);
            };
            double wa[5], ca[5];
            wa[0] = bench_warm(qa_linear,      num_arrays, targets, warm_reps);
            wa[1] = bench_warm(qa_binary,      num_arrays, targets, warm_reps);
            wa[2] = bench_warm(qa_simd,        num_arrays, targets, warm_reps);
            wa[3] = bench_warm(qa_intel,       num_arrays, targets, warm_reps);
            wa[4] = bench_warm(qa_intel_spine, num_arrays, targets, warm_reps);
            ca[0] = bench_cold(qa_linear,      num_arrays, targets);
            ca[1] = bench_cold(qa_binary,      num_arrays, targets);
            ca[2] = bench_cold(qa_simd,        num_arrays, targets);
            ca[3] = bench_cold(qa_intel,       num_arrays, targets);
            ca[4] = bench_cold(qa_intel_spine, num_arrays, targets);
            std::printf("%4dA  | %7.1f %7.1f %6.1f %6.1f %6.1f              | "
                        "%7.1f %7.1f %6.1f %6.1f %6.1f\n",
                        size, wa[0], wa[1], wa[2], wa[3], wa[4],
                        ca[0], ca[1], ca[2], ca[3], ca[4]);
        }

        // Intel padded-descent A/B at every size. "*pad" compares the
        // general-n spine against the padded-spine variant (3-probe
        // branchless finish replacing the binary-tail + final lo pick).
        // Prints per-size so the sawtooth vs padded pattern is visible.
        if (size >= 32) {
            auto q_intel_spine_pad = [&](size_t i, uint16_t t) {
                return simd_quad_intel_spine_padded(
                    arrs[i].data(), spines_intelp[i].data(), size, t);
            };
            double w_intelp = bench_warm(q_intel_spine_pad, num_arrays, targets, warm_reps);
            double c_intelp = bench_cold(q_intel_spine_pad, num_arrays, targets);
            std::printf("%5d* | intel_spine=%.2f intel_spine_pad=%.2f  (warm)  | "
                        "intel_spine=%.2f intel_spine_pad=%.2f  (cold)\n",
                        size, w[4], w_intelp, c[4], c_intelp);
        }

        // Shipping spine specializations for n ∈ {256, 512, 1024, 2048, 4096}.
        // Hybrid (unroll + branchless 2-probe finish) at high-foot sizes
        // 256/1024; pure unroll at low-foot sizes 512/2048. Prints per-size so
        // the sawtooth is visible against the general-n spine baseline.
        if (size == 256 || size == 512 || size == 1024 || size == 2048) {
            double w_n = 0, c_n = 0;
            if (size == 256) {
                auto q = [&](size_t i, uint16_t t) {
                    return simd_quad_intel_spine_256(arrs[i].data(), spines_intel[i].data(), t);
                };
                w_n = bench_warm(q, num_arrays, targets, warm_reps);
                c_n = bench_cold(q, num_arrays, targets);
            } else if (size == 512) {
                auto q = [&](size_t i, uint16_t t) {
                    return simd_quad_intel_spine_512(arrs[i].data(), spines_intel[i].data(), t);
                };
                w_n = bench_warm(q, num_arrays, targets, warm_reps);
                c_n = bench_cold(q, num_arrays, targets);
            } else if (size == 1024) {
                auto q = [&](size_t i, uint16_t t) {
                    return simd_quad_intel_spine_1024(arrs[i].data(), spines_intel[i].data(), t);
                };
                w_n = bench_warm(q, num_arrays, targets, warm_reps);
                c_n = bench_cold(q, num_arrays, targets);
            } else if (size == 2048) {
                auto q = [&](size_t i, uint16_t t) {
                    return simd_quad_intel_spine_2048(arrs[i].data(), spines_intel[i].data(), t);
                };
                w_n = bench_warm(q, num_arrays, targets, warm_reps);
                c_n = bench_cold(q, num_arrays, targets);
            }
            std::printf("%5d* | intel_spine=%.2f intel_spine_%d=%.2f  (warm)  | "
                        "intel_spine=%.2f intel_spine_%d=%.2f  (cold)\n",
                        size, w[4], size, w_n, c[4], size, c_n);
        }

        // n=4096 compile-time specialization A/B. Prints a dedicated row so
        // the numbers are on the same page as the general-n spine variant.
        // _spine_4096 is the hybrid (3 quat + branchless 2-probe finish)
        // after the 2026-05-12 EMR ship call retired the prior unroll.
        if (size == 4096) {
            auto q_intel_4096 = [&](size_t i, uint16_t t) {
                return simd_quad_intel_spine_4096(
                    arrs[i].data(), spines_intel[i].data(), t);
            };
            double w_4096 = bench_warm(q_intel_4096, num_arrays, targets, warm_reps);
            double c_4096 = bench_cold(q_intel_4096, num_arrays, targets);
            std::printf(" 4096* | intel_spine=%.2f intel_spine_4096=%.2f  (warm)  | "
                        "intel_spine=%.2f intel_spine_4096=%.2f  (cold)\n",
                        w[4], w_4096, c[4], c_4096);
        }
#endif
    }
    return 0;
}

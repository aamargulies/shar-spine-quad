// Cold-path decomposition profiler for simd_quad_m4_spine_4096.
//
// Goal: attribute cold-cache time spent inside simd_quad_m4_spine_4096 to
// (a) the 3-tier spine descent ending in the branchless 4-probe finish, and
// (b) the demand block-load + SIMD compare. The function only does those
// two things (besides the up-front spine prefetch), so the cold delta
// between full / descent-only / block-only directly identifies the
// critical-path phase.
//
// Build (Apple M1 Pro / M4 Max):
//   clang++ -O3 -mcpu=apple-m1 -std=c++20 \
//       bench_profile_m4.cpp simd_quad_m4.c simd_quad_m4_profile.c \
//       -o bench_profile_m4
//
// Run: ./bench_profile_m4 [num_sets] [reps]
//   Defaults: num_sets=512, reps=1. Each set is one (carr, spine) pair with
//   carr = 4096 sorted u16 (8 KB) and spine = 64 u16 (128 B). Total working
//   set ~ 4 MB carrs + 64 KB spines, well over L2 (12 MB shared on M1 Pro
//   but partitioned per cluster). 256 MB thrash before each cold mode
//   guarantees true cold state.
//
// Output: 5 columns per harness mode (warm/cold) x 4 modes total:
//   warm_full, warm_descent, warm_blk, warm_buildlo, warm_descent+blk
//   cold_full, cold_descent, cold_blk, cold_buildlo, cold_descent+blk
//
// The "buildlo" column drives blk-only with a simulated correct lo computed
// from the descent (single descent run per query, then blkonly call). It's
// the closest comparator to "full" that's also a complete query.
//
// "descent+blk" sums the two phases measured *separately*: if cold "full"
// is close to descent+blk, the phases serialize (each phase has its own
// cold misses). If cold "full" is close to max(descent, blk), the phases
// overlap (OoO covers one behind the other). The gap between full and the
// sum quantifies overlap.
//
// 5 runs of this script, take per-cell medians, same protocol as the rest
// of the project.

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <set>
#include <vector>
#include <arm_neon.h>

bool simd_quad_m4_spine_4096(const uint16_t *carr, const uint16_t *spine,
                             uint16_t pos);
void simd_quad_m4_build_spine(const uint16_t *carr, int32_t cardinality,
                              uint16_t *spine);
int32_t simd_quad_m4_spine_4096_descent(const uint16_t *spine, uint16_t pos);
bool simd_quad_m4_spine_4096_blkonly(const uint16_t *carr, int32_t lo,
                                     uint16_t pos);
int32_t simd_quad_m4_spine_general_descent(const uint16_t *spine, uint16_t pos);
bool simd_quad_m4_spine_4096_pfC(const uint16_t *carr, const uint16_t *spine,
                                 uint16_t pos);
void simd_quad_m4_build_spine_lo(const uint16_t *carr, int32_t cardinality,
                                 uint16_t *spine_lo);
bool simd_quad_m4_spine_4096_sentinel(const uint16_t *carr,
                                      const uint16_t *spine,
                                      const uint16_t *spine_lo,
                                      uint16_t pos);
void simd_quad_m4_build_spine_2x(const uint16_t *carr, int32_t cardinality,
                                 uint16_t *spine_2x);
bool simd_quad_m4_spine_4096_sentinel_2x(const uint16_t *carr,
                                         const uint16_t *spine_2x,
                                         uint16_t pos);

using clock_type = std::chrono::steady_clock;

static constexpr int kInnerN = 4096;
static constexpr int kGap = 64;
static constexpr int kSpineEntries = kInnerN / kGap;  // 64

struct Set {
    std::vector<uint16_t> carr;      // 4096 sorted u16, 8 KB
    std::vector<uint16_t> spine;     // 64 u16, 128 B (last-of-block)
    std::vector<uint16_t> spine_lo;  // 64 u16, 128 B (first-of-block)
    std::vector<uint16_t> spine_2x;  // 128 u16, 256 B (interleaved lo/hi)
};

static std::vector<uint16_t> make_sorted_u16(std::mt19937 &rng, int n) {
    std::set<uint16_t> s;
    std::uniform_int_distribution<int> d(0, 65535);
    while ((int)s.size() < n) s.insert((uint16_t)d(rng));
    return std::vector<uint16_t>(s.begin(), s.end());
}

static std::vector<Set> make_sets(int num_sets, uint64_t seed) {
    std::mt19937 rng(seed);
    std::vector<Set> sets(num_sets);
    for (int i = 0; i < num_sets; i++) {
        sets[i].carr = make_sorted_u16(rng, kInnerN);
        sets[i].spine.resize(kSpineEntries);
        sets[i].spine_lo.resize(kSpineEntries);
        sets[i].spine_2x.resize(2 * kSpineEntries);
        simd_quad_m4_build_spine(sets[i].carr.data(), kInnerN,
                                 sets[i].spine.data());
        simd_quad_m4_build_spine_lo(sets[i].carr.data(), kInnerN,
                                    sets[i].spine_lo.data());
        simd_quad_m4_build_spine_2x(sets[i].carr.data(), kInnerN,
                                    sets[i].spine_2x.data());
    }
    return sets;
}

// hit_frac in [0,1]: fraction of targets drawn from real elements (always
// hit). Remainder uniform random (will be ~94% miss rate for n=4096).
static std::vector<uint16_t> make_targets(const std::vector<Set> &sets,
                                          int num_targets, uint64_t seed,
                                          double hit_frac) {
    std::mt19937 rng(seed);
    std::uniform_int_distribution<int> d(0, 65535);
    std::uniform_int_distribution<int> set_d(0, (int)sets.size() - 1);
    std::uniform_int_distribution<int> idx_d(0, kInnerN - 1);
    std::uniform_real_distribution<double> u(0.0, 1.0);
    std::vector<uint16_t> t(num_targets);
    for (int i = 0; i < num_targets; i++) {
        if (u(rng) < hit_frac) {
            const auto &s = sets[set_d(rng)];
            t[i] = s.carr[idx_d(rng)];
        } else {
            t[i] = (uint16_t)d(rng);
        }
    }
    return t;
}

// Compute realized miss-rate against a representative set. (All sets have
// the same cardinality and similar density, so one is enough.)
static double realized_miss_rate(const Set &s,
                                 const std::vector<uint16_t> &targets) {
    int hits = 0;
    for (uint16_t pos : targets) {
        if (std::binary_search(s.carr.begin(), s.carr.end(), pos)) hits++;
    }
    return 1.0 - (double)hits / targets.size();
}

// LLC thrasher: 256 MB stride-64 writes evict everything.
static constexpr size_t kThrashBytes = 256u * 1024u * 1024u;
static void thrash_llc() {
    static std::vector<uint8_t> scratch;
    if (scratch.empty()) scratch.assign(kThrashBytes, 0);
    volatile uint8_t *p = scratch.data();
    for (size_t i = 0; i < kThrashBytes; i += 64) p[i] = (uint8_t)i;
}

// One query iteration: walk all num_sets, doing one query per set with a
// targets[i % num_targets] needle. Sink results into an XOR accumulator so
// the compiler can't elide.
template <typename Body>
static double bench_cold(const std::vector<Set> &sets,
                         const std::vector<uint16_t> &targets, Body body,
                         int reps) {
    double best = 1e18;
    int num_sets = (int)sets.size();
    int num_targets = (int)targets.size();
    for (int r = 0; r < reps; r++) {
        thrash_llc();
        uint64_t sink = 0;
        auto t0 = clock_type::now();
        for (int i = 0; i < num_sets; i++) {
            sink ^= (uint64_t)body(sets[i], targets[i % num_targets]);
        }
        auto t1 = clock_type::now();
        double ns = std::chrono::duration<double, std::nano>(t1 - t0).count();
        double per_q = ns / num_sets;
        if (per_q < best) best = per_q;
        // Defeat DCE.
        if (sink == 0xDEADBEEFCAFEBABEULL) std::printf("");
    }
    return best;
}

template <typename Body>
static double bench_warm(const std::vector<Set> &sets,
                         const std::vector<uint16_t> &targets, Body body,
                         int reps) {
    // Warm: one set, queried reps * num_targets times. After the first few
    // its lines are in L1.
    double best = 1e18;
    int num_targets = (int)targets.size();
    const Set &s = sets[0];
    // Prime.
    uint64_t prime = 0;
    for (int i = 0; i < 1024; i++) prime ^= (uint64_t)body(s, targets[i % num_targets]);
    if (prime == 0xDEADBEEFCAFEBABEULL) std::printf("");

    constexpr int kInner = 8192;
    for (int r = 0; r < reps; r++) {
        uint64_t sink = 0;
        auto t0 = clock_type::now();
        for (int i = 0; i < kInner; i++) {
            sink ^= (uint64_t)body(s, targets[i % num_targets]);
        }
        auto t1 = clock_type::now();
        double ns = std::chrono::duration<double, std::nano>(t1 - t0).count();
        double per_q = ns / kInner;
        if (per_q < best) best = per_q;
        if (sink == 0xDEADBEEFCAFEBABEULL) std::printf("");
    }
    return best;
}

int main(int argc, char **argv) {
    int num_sets = (argc >= 2) ? std::atoi(argv[1]) : 512;
    int reps = (argc >= 3) ? std::atoi(argv[2]) : 5;
    double hit_frac = (argc >= 4) ? std::atof(argv[3]) : 0.0;

    auto sets = make_sets(num_sets, 12345);
    auto targets = make_targets(sets, 4096, 67890, hit_frac);
    double miss_rate = realized_miss_rate(sets[0], targets);

    auto body_full = [](const Set &s, uint16_t pos) -> int {
        return (int)simd_quad_m4_spine_4096(s.carr.data(), s.spine.data(), pos);
    };
    auto body_pfC = [](const Set &s, uint16_t pos) -> int {
        return (int)simd_quad_m4_spine_4096_pfC(s.carr.data(), s.spine.data(), pos);
    };
    auto body_sentinel = [](const Set &s, uint16_t pos) -> int {
        return (int)simd_quad_m4_spine_4096_sentinel(
            s.carr.data(), s.spine.data(), s.spine_lo.data(), pos);
    };
    auto body_sentinel_2x = [](const Set &s, uint16_t pos) -> int {
        return (int)simd_quad_m4_spine_4096_sentinel_2x(
            s.carr.data(), s.spine_2x.data(), pos);
    };
    auto body_descent_hybrid = [](const Set &s, uint16_t pos) -> int {
        return simd_quad_m4_spine_4096_descent(s.spine.data(), pos);
    };
    auto body_descent_general = [](const Set &s, uint16_t pos) -> int {
        return simd_quad_m4_spine_general_descent(s.spine.data(), pos);
    };
    // For block-only, we need a "lo" to feed it. Compute it via the same
    // descent (double-counts the descent's spine touch on the first call,
    // but that's a 128-byte line that's already in L1 by the time blk
    // happens, so it doesn't change the block-load cost). The point of
    // this column isn't to be a complete query --- it's to isolate the
    // demand block-load latency.
    auto body_blk = [](const Set &s, uint16_t pos) -> int {
        int32_t lo = simd_quad_m4_spine_4096_descent(s.spine.data(), pos);
        return (int)simd_quad_m4_spine_4096_blkonly(s.carr.data(), lo, pos);
    };
    // Build-lo: same as body_blk, distinguished only in the print column
    // for the warm/cold result columns. (Kept as a single body.)

    std::printf("# bench_profile_m4: num_sets=%d reps=%d hit_frac=%.2f miss_rate=%.3f\n",
                num_sets, reps, hit_frac, miss_rate);
    std::printf("# carr per set = %d u16 (%zu B), spine = %d u16 (%zu B), spine_lo = %d u16 (%zu B)\n",
                kInnerN, kInnerN * sizeof(uint16_t),
                kSpineEntries, kSpineEntries * sizeof(uint16_t),
                kSpineEntries, kSpineEntries * sizeof(uint16_t));
    std::printf("# units: ns/query (best of %d reps)\n\n", reps);

    double w_full   = bench_warm(sets, targets, body_full, reps);
    double w_pfC    = bench_warm(sets, targets, body_pfC,  reps);
    double w_sent   = bench_warm(sets, targets, body_sentinel, reps);
    double w_s2x    = bench_warm(sets, targets, body_sentinel_2x, reps);
    double w_dh     = bench_warm(sets, targets, body_descent_hybrid, reps);
    double w_dg     = bench_warm(sets, targets, body_descent_general, reps);
    double w_blk    = bench_warm(sets, targets, body_blk, reps);

    double c_full   = bench_cold(sets, targets, body_full, reps);
    double c_pfC    = bench_cold(sets, targets, body_pfC,  reps);
    double c_sent   = bench_cold(sets, targets, body_sentinel, reps);
    double c_s2x    = bench_cold(sets, targets, body_sentinel_2x, reps);
    double c_dh     = bench_cold(sets, targets, body_descent_hybrid, reps);
    double c_dg     = bench_cold(sets, targets, body_descent_general, reps);
    double c_blk    = bench_cold(sets, targets, body_blk, reps);

    std::printf("phase                | warm     | cold     | cold/warm\n");
    std::printf("---------------------+----------+----------+----------\n");
    std::printf("full (hybrid)        | %7.2f  | %7.2f  | %5.2fx\n",
                w_full, c_full, c_full / w_full);
    std::printf("full + pfC (4-way)   | %7.2f  | %7.2f  | %5.2fx\n",
                w_pfC,  c_pfC,  c_pfC  / w_pfC);
    std::printf("full + sentinel      | %7.2f  | %7.2f  | %5.2fx\n",
                w_sent, c_sent, c_sent / w_sent);
    std::printf("full + sentinel_2x   | %7.2f  | %7.2f  | %5.2fx\n",
                w_s2x,  c_s2x,  c_s2x  / w_s2x);
    std::printf("descent-only hybrid  | %7.2f  | %7.2f  | %5.2fx\n",
                w_dh,   c_dh,   c_dh   / w_dh);
    std::printf("descent-only general | %7.2f  | %7.2f  | %5.2fx\n",
                w_dg,   c_dg,   c_dg   / w_dg);
    std::printf("descent + blk-only   | %7.2f  | %7.2f  | %5.2fx\n",
                w_blk,  c_blk,  c_blk  / w_blk);
    std::printf("\n");
    std::printf("# blk-only - descent-hybrid = isolated block-load cost\n");
    std::printf("warm  blk-only-only ~ %.2f ns\n", w_blk - w_dh);
    std::printf("cold  blk-only-only ~ %.2f ns\n", c_blk - c_dh);
    std::printf("\n");
    std::printf("# Phase composition of cold full (%.2f ns/q):\n", c_full);
    std::printf("# - if descent-hybrid (%.2f) ~ full, descent dominates\n", c_dh);
    std::printf("# - if blk-only-only (%.2f) ~ full, block-load dominates\n",
                c_blk - c_dh);
    std::printf("# - if descent+blk separately (%.2f) >> full, phases overlap\n",
                c_blk);
    return 0;
}

// Two-level spine micro-benchmark for Roaring-style container sets.
//
// A Roaring container set is an array of (high16, container) pairs,
// sorted by high16. Membership of a 32-bit value v is:
//   1. find container whose key == (v >> 16)     -- outer search
//   2. test membership of (v & 0xFFFF)           -- inner search
//
// Step 2 is the existing simd_quad_*_spine problem. Step 1 is
// structurally the same shape (binary search over sorted u16), just at
// container granularity. The "two-level spine" idea is to apply the
// spine trick to the outer search too, so the cold-cache pointer chase
// through container keys becomes a contiguous streaming read.
//
// This micro-bench compares:
//   A. std::binary_search over keys      +  general-n spine inner
//   B. spine over keys                   +  general-n spine inner
//   C. std::binary_search over keys      +  compile-time-n=4096 spine inner
//   D. spine over keys                   +  compile-time-n=4096 spine inner
//   E. Shar branchless binary over keys  +  general-n spine inner
//   F. Shar branchless binary over keys  +  compile-time-n=4096 spine inner
//
// The difference between A and B isolates the outer-spine win; the
// difference between A and C isolates the compile-time-n-inner win; D
// combines both. E/F replace the outer search with Shar's 1971 branchless
// binary search (cmov chain, step halving). Interesting because it needs
// no side structure: on hosts where the outer-spine win is thin (M4's
// 128-B line makes the 1-line spine useless to the streamer) the
// cmov-chain approach may be competitive.
//
// Build (Intel / AMD):
//   g++ -O3 -march=native -std=c++20 bench_twolevel.cpp simd_quad_intel.c -o bench_twolevel
//
// Build (Apple M4 Max):
//   clang++ -O3 -mcpu=apple-m4 -std=c++20 bench_twolevel.cpp simd_quad_m4.c -o bench_twolevel
//
// Build (Raspberry Pi 5 / Cortex-A76):
//   g++ -O3 -mcpu=cortex-a76 -std=c++20 -DQUADSEARCH_ARM_PI5 \
//       bench_twolevel.cpp simd_quad_pi5.c -o bench_twolevel
//
// Build (AWS Graviton 4 / Arm Neoverse V2):
//   g++ -O3 -mcpu=neoverse-v2 -std=c++20 -DQUADSEARCH_ARM_GV4 \
//       bench_twolevel.cpp simd_quad_graviton.c -o bench_twolevel
//
// Run: ./bench_twolevel [num_sets] [warm_reps]
//   Defaults: num_sets=200, warm_reps=200. Each "set" is 512 containers
//   of cardinality 4096 -- ~4 MB of keys per set, large enough to blow
//   out L2.
//
// Gap is host-selected: gap=32 on Intel/Graviton/Pi 5, gap=64 on M4 Max.
// The outer spine is built with the same gap as the inner variant. Set
// -DQUADSEARCH_ARM_PI5 or -DQUADSEARCH_ARM_GV4 on ARM to link the Pi 5
// or Graviton 4 variant; default ARM build links the M4 variant.

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <set>
#include <vector>

#if defined(__ARM_NEON) || defined(__aarch64__)
  #define QUADSEARCH_ARCH_ARM 1
#elif defined(__x86_64__) || defined(_M_X64) || defined(__i386__)
  #define QUADSEARCH_ARCH_X86 1
  #include <immintrin.h>
#else
  #error "Unsupported architecture for bench_twolevel"
#endif

#if QUADSEARCH_ARCH_X86
bool simd_quad_intel_spine(const uint16_t *carr, const uint16_t *spine,
                           int32_t cardinality, uint16_t pos);
void simd_quad_intel_build_spine(const uint16_t *carr, int32_t cardinality,
                                 uint16_t *spine);
bool simd_quad_intel_spine_4096(const uint16_t *carr, const uint16_t *spine,
                                uint16_t pos);
static constexpr int kGap = 32;
static inline bool inner_spine(const uint16_t *carr, const uint16_t *spine,
                               int32_t cardinality, uint16_t pos) {
    return simd_quad_intel_spine(carr, spine, cardinality, pos);
}
static inline void build_spine(const uint16_t *carr, int32_t cardinality,
                               uint16_t *spine) {
    simd_quad_intel_build_spine(carr, cardinality, spine);
}
static inline bool inner_spine_4096(const uint16_t *carr, const uint16_t *spine,
                                    uint16_t pos) {
    return simd_quad_intel_spine_4096(carr, spine, pos);
}
static inline void prefetch_spine(const uint16_t *p) {
    _mm_prefetch((const char *)p, _MM_HINT_T0);
}
#endif

#if QUADSEARCH_ARCH_ARM
#if defined(QUADSEARCH_ARM_PI5)
bool simd_quad_pi5_spine(const uint16_t *carr, const uint16_t *spine,
                         int32_t cardinality, uint16_t pos);
void simd_quad_pi5_build_spine(const uint16_t *carr, int32_t cardinality,
                               uint16_t *spine);
bool simd_quad_pi5_spine_4096(const uint16_t *carr, const uint16_t *spine,
                              uint16_t pos);
static constexpr int kGap = 32;
static inline bool inner_spine(const uint16_t *carr, const uint16_t *spine,
                               int32_t cardinality, uint16_t pos) {
    return simd_quad_pi5_spine(carr, spine, cardinality, pos);
}
static inline void build_spine(const uint16_t *carr, int32_t cardinality,
                               uint16_t *spine) {
    simd_quad_pi5_build_spine(carr, cardinality, spine);
}
static inline bool inner_spine_4096(const uint16_t *carr, const uint16_t *spine,
                                    uint16_t pos) {
    return simd_quad_pi5_spine_4096(carr, spine, pos);
}
static inline void prefetch_spine(const uint16_t *p) {
    __builtin_prefetch(p);
}
#elif defined(QUADSEARCH_ARM_GV4)
bool simd_quad_graviton_spine(const uint16_t *carr, const uint16_t *spine,
                              int32_t cardinality, uint16_t pos);
void simd_quad_graviton_build_spine(const uint16_t *carr, int32_t cardinality,
                                    uint16_t *spine);
bool simd_quad_graviton_spine_4096(const uint16_t *carr, const uint16_t *spine,
                                   uint16_t pos);
static constexpr int kGap = 32;
static inline bool inner_spine(const uint16_t *carr, const uint16_t *spine,
                               int32_t cardinality, uint16_t pos) {
    return simd_quad_graviton_spine(carr, spine, cardinality, pos);
}
static inline void build_spine(const uint16_t *carr, int32_t cardinality,
                               uint16_t *spine) {
    simd_quad_graviton_build_spine(carr, cardinality, spine);
}
static inline bool inner_spine_4096(const uint16_t *carr, const uint16_t *spine,
                                    uint16_t pos) {
    return simd_quad_graviton_spine_4096(carr, spine, pos);
}
static inline void prefetch_spine(const uint16_t *p) {
    __builtin_prefetch(p);
}
#else
bool simd_quad_m4_spine(const uint16_t *carr, const uint16_t *spine,
                        int32_t cardinality, uint16_t pos);
void simd_quad_m4_build_spine(const uint16_t *carr, int32_t cardinality,
                              uint16_t *spine);
bool simd_quad_m4_spine_4096(const uint16_t *carr, const uint16_t *spine,
                             uint16_t pos);
static constexpr int kGap = 64;
static inline bool inner_spine(const uint16_t *carr, const uint16_t *spine,
                               int32_t cardinality, uint16_t pos) {
    return simd_quad_m4_spine(carr, spine, cardinality, pos);
}
static inline void build_spine(const uint16_t *carr, int32_t cardinality,
                               uint16_t *spine) {
    simd_quad_m4_build_spine(carr, cardinality, spine);
}
static inline bool inner_spine_4096(const uint16_t *carr, const uint16_t *spine,
                                    uint16_t pos) {
    return simd_quad_m4_spine_4096(carr, spine, pos);
}
static inline void prefetch_spine(const uint16_t *p) {
    __builtin_prefetch(p);
}
#endif
#endif

using clock_type = std::chrono::steady_clock;

struct Container {
    std::vector<uint16_t> carr;
    std::vector<uint16_t> spine;
};

// A Roaring-style container set: parallel arrays of keys (high16) and
// containers, sorted by key.
struct ContainerSet {
    std::vector<uint16_t> keys;            // outer keys, sorted
    std::vector<uint16_t> keys_spine;      // spine over `keys` (for B/D)
    std::vector<Container> containers;     // containers[i] matches keys[i]
};

static std::vector<uint16_t> make_sorted_u16(std::mt19937 &rng, int n) {
    std::set<uint16_t> s;
    std::uniform_int_distribution<int> d(0, 65535);
    while ((int)s.size() < n) s.insert((uint16_t)d(rng));
    return std::vector<uint16_t>(s.begin(), s.end());
}

// Build a container set: num_containers containers, each of cardinality
// inner_n. Outer keys are a sorted random selection of u16.
static ContainerSet make_set(std::mt19937 &rng, int num_containers,
                             int inner_n) {
    ContainerSet s;
    s.keys = make_sorted_u16(rng, num_containers);
    s.containers.resize(num_containers);
    for (int i = 0; i < num_containers; i++) {
        s.containers[i].carr = make_sorted_u16(rng, inner_n);
        s.containers[i].spine.resize(inner_n / kGap);
        build_spine(s.containers[i].carr.data(), inner_n,
                    s.containers[i].spine.data());
    }
    // Outer spine: same gap as inner.
    int outer_blocks = num_containers / kGap;
    if (outer_blocks > 0) {
        s.keys_spine.resize(outer_blocks);
        build_spine(s.keys.data(), num_containers, s.keys_spine.data());
    }
    return s;
}

// Outer-search variants.
static inline int find_container_bsearch(const ContainerSet &s,
                                         uint16_t key) {
    auto it = std::lower_bound(s.keys.begin(), s.keys.end(), key);
    if (it != s.keys.end() && *it == key) return (int)(it - s.keys.begin());
    return -1;
}

static inline int find_container_spine(const ContainerSet &s, uint16_t key) {
    // We need the index, not just presence. The inner spine routine returns
    // a bool; for a fair outer-search cost comparison we do a quaternary
    // descent that yields the index directly. This mirrors the spine
    // variant but terminates with a direct scalar compare at the winning
    // block (rather than a SIMD "any hit" check) so we can return the
    // index. Keeps the pointer-chase pattern identical.
    //
    // Gap matches the host-selected kGap: 32 on Intel/Graviton (64-B line),
    // 64 on M4 (128-B line). On M4 num_containers=512 -> num_blocks=8, so
    // the quaternary descent runs just once before the binary step; still
    // strictly faster than a cold bsearch because the whole key spine fits
    // in 16 bytes (one cache line trivially).
    int32_t card = (int32_t)s.keys.size();
    if (card == 0) return -1;
    int32_t num_blocks = card / kGap;
    if (num_blocks <= 3) {
        // Fall back to scalar binary search on the keys directly.
        auto it = std::lower_bound(s.keys.begin(), s.keys.end(), key);
        if (it != s.keys.end() && *it == key) return (int)(it - s.keys.begin());
        return -1;
    }
    prefetch_spine(s.keys_spine.data());
    const uint16_t *spine = s.keys_spine.data();
    int32_t base = 0, n = num_blocks;
    while (n > 3) {
        int32_t quarter = n >> 2;
        int32_t k1 = spine[base + quarter];
        int32_t k2 = spine[base + 2 * quarter];
        int32_t k3 = spine[base + 3 * quarter];
        base += ((k1 < key) + (k2 < key) + (k3 < key)) * quarter;
        n -= 3 * quarter;
    }
    while (n > 1) {
        int32_t half = n >> 1;
        base = (spine[base + half] < key) ? base + half : base;
        n -= half;
    }
    int32_t lo = (spine[base] < key) ? base + 1 : base;
    if (lo >= num_blocks) {
        // Tail region of keys (the card % kGap that didn't fit into blocks).
        for (int32_t j = num_blocks * kGap; j < card; j++) {
            if (s.keys[j] == key) return (int)j;
        }
        return -1;
    }
    // Linear scan within the winning kGap-element block. Block is one
    // cache line (kGap*2 bytes), so this costs one load at most.
    int32_t blk_start = lo * kGap;
    for (int32_t j = blk_start; j < blk_start + kGap; j++) {
        if (s.keys[j] == key) return (int)j;
    }
    return -1;
}

// Shar's 1971 branchless binary search (rediscovered by probablydance 2023).
// Single pointer + step halving; `if (begin[step] < key) begin += step;`
// compiles to a cmov, so the inner descent has no branches. For
// non-power-of-two sizes the classic "bit_floor + offset to end-step"
// trick is applied once up front.
static inline int find_container_shar(const ContainerSet &s, uint16_t key) {
    int len = (int)s.keys.size();
    if (len == 0) return -1;
    const uint16_t *base  = s.keys.data();
    const uint16_t *begin = base;

    int step = 1;
    while ((step << 1) <= len) step <<= 1;

    if (step != len && begin[step] < key) {
        begin = begin + (len - step);
    }
    for (step >>= 1; step != 0; step >>= 1) {
        if (begin[step] < key) begin += step;
    }
    const uint16_t *lo = begin + (*begin < key);
    if (lo < base + len && *lo == key) return (int)(lo - base);
    return -1;
}

// Six lookup paths.
static bool lookup_A(const ContainerSet &s, uint32_t v) {
    int idx = find_container_bsearch(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return inner_spine(c.carr.data(), c.spine.data(),
                       (int32_t)c.carr.size(), (uint16_t)v);
}
static bool lookup_B(const ContainerSet &s, uint32_t v) {
    int idx = find_container_spine(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return inner_spine(c.carr.data(), c.spine.data(),
                       (int32_t)c.carr.size(), (uint16_t)v);
}
static bool lookup_C(const ContainerSet &s, uint32_t v) {
    int idx = find_container_bsearch(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return inner_spine_4096(c.carr.data(), c.spine.data(), (uint16_t)v);
}
static bool lookup_D(const ContainerSet &s, uint32_t v) {
    int idx = find_container_spine(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return inner_spine_4096(c.carr.data(), c.spine.data(), (uint16_t)v);
}
static bool lookup_E(const ContainerSet &s, uint32_t v) {
    int idx = find_container_shar(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return inner_spine(c.carr.data(), c.spine.data(),
                       (int32_t)c.carr.size(), (uint16_t)v);
}
static bool lookup_F(const ContainerSet &s, uint32_t v) {
    int idx = find_container_shar(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return inner_spine_4096(c.carr.data(), c.spine.data(), (uint16_t)v);
}

template <typename Fn>
static double bench(const std::vector<ContainerSet> &sets,
                    const std::vector<std::vector<uint32_t>> &targets,
                    int warm_reps, Fn fn) {
    volatile uint64_t acc = 0;
    auto t0 = clock_type::now();
    for (size_t si = 0; si < sets.size(); si++) {
        for (int r = 0; r < warm_reps; r++) {
            uint32_t t = targets[si][(r * 17u) % targets[si].size()];
            acc += fn(sets[si], t);
        }
    }
    auto t1 = clock_type::now();
    (void)acc;
    double ns = std::chrono::duration<double, std::nano>(t1 - t0).count();
    return ns / (double)(sets.size() * warm_reps);
}

template <typename Fn>
static double bench_cold(const std::vector<ContainerSet> &sets,
                         const std::vector<std::vector<uint32_t>> &targets,
                         Fn fn) {
    volatile uint64_t acc = 0;
    auto t0 = clock_type::now();
    for (size_t si = 0; si < sets.size(); si++) {
        acc += fn(sets[si], targets[si][0]);
    }
    auto t1 = clock_type::now();
    (void)acc;
    double ns = std::chrono::duration<double, std::nano>(t1 - t0).count();
    return ns / (double)sets.size();
}

int main(int argc, char **argv) {
    int num_sets   = (argc > 1) ? std::atoi(argv[1]) : 200;
    int warm_reps  = (argc > 2) ? std::atoi(argv[2]) : 200;

    constexpr int num_containers = 512;
    constexpr int inner_n        = 4096;

    std::printf("two-level spine micro-bench\n");
    std::printf("num_sets=%d warm_reps=%d num_containers=%d inner_n=%d\n",
                num_sets, warm_reps, num_containers, inner_n);
    std::printf("per set: %d B of keys + %d B of container data + %d B of spines\n",
                num_containers * 2,
                num_containers * inner_n * 2,
                num_containers * (inner_n / 32) * 2);

    std::mt19937 rng(0xB17F17);
    std::vector<ContainerSet> sets;
    sets.reserve(num_sets);
    std::vector<std::vector<uint32_t>> targets;
    targets.reserve(num_sets);
    for (int i = 0; i < num_sets; i++) {
        sets.push_back(make_set(rng, num_containers, inner_n));
        // Targets: half hits (random container, random element in it),
        // half misses (random u32).
        std::vector<uint32_t> ts;
        ts.reserve(1024);
        std::uniform_int_distribution<int> pc(0, num_containers - 1);
        std::uniform_int_distribution<int> pe(0, inner_n - 1);
        std::uniform_int_distribution<uint32_t> pm(0, UINT32_MAX);
        for (int k = 0; k < 1024; k++) {
            if (k & 1) {
                int ci = pc(rng);
                uint16_t lo = sets.back().containers[ci].carr[pe(rng)];
                ts.push_back((uint32_t(sets.back().keys[ci]) << 16) | lo);
            } else {
                ts.push_back(pm(rng));
            }
        }
        targets.push_back(std::move(ts));
    }

    // Correctness spot-check: A/B/C/D must all agree on a sample of
    // targets across a handful of sets.
    for (int si = 0; si < std::min(5, num_sets); si++) {
        for (int k = 0; k < 200; k++) {
            uint32_t t = targets[si][k];
            bool rA = lookup_A(sets[si], t);
            bool rB = lookup_B(sets[si], t);
            bool rC = lookup_C(sets[si], t);
            bool rD = lookup_D(sets[si], t);
            bool rE = lookup_E(sets[si], t);
            bool rF = lookup_F(sets[si], t);
            if (rA != rB || rA != rC || rA != rD || rA != rE || rA != rF) {
                std::fprintf(stderr,
                             "MISMATCH set=%d t=%u A=%d B=%d C=%d D=%d E=%d F=%d\n",
                             si, t, rA, rB, rC, rD, rE, rF);
                return 1;
            }
        }
    }
    std::printf("correctness: ok\n\n");

    double wA = bench(sets, targets, warm_reps, lookup_A);
    double wB = bench(sets, targets, warm_reps, lookup_B);
    double wC = bench(sets, targets, warm_reps, lookup_C);
    double wD = bench(sets, targets, warm_reps, lookup_D);
    double wE = bench(sets, targets, warm_reps, lookup_E);
    double wF = bench(sets, targets, warm_reps, lookup_F);

    double cA = bench_cold(sets, targets, lookup_A);
    double cB = bench_cold(sets, targets, lookup_B);
    double cC = bench_cold(sets, targets, lookup_C);
    double cD = bench_cold(sets, targets, lookup_D);
    double cE = bench_cold(sets, targets, lookup_E);
    double cF = bench_cold(sets, targets, lookup_F);

    std::printf("%-4s  %-56s  %10s  %10s\n",
                "var", "description", "warm ns/q", "cold ns/q");
    std::printf("----  --------------------------------------------------------  ----------  ----------\n");
    std::printf("%-4s  %-56s  %10.2f  %10.2f\n",
                "A", "bsearch outer + general-n spine inner", wA, cA);
    std::printf("%-4s  %-56s  %10.2f  %10.2f\n",
                "B", "two-level spine + general-n spine inner", wB, cB);
    std::printf("%-4s  %-56s  %10.2f  %10.2f\n",
                "C", "bsearch outer + compile-time n=4096 inner", wC, cC);
    std::printf("%-4s  %-56s  %10.2f  %10.2f\n",
                "D", "two-level spine + compile-time n=4096 inner", wD, cD);
    std::printf("%-4s  %-56s  %10.2f  %10.2f\n",
                "E", "Shar branchless outer + general-n spine inner", wE, cE);
    std::printf("%-4s  %-56s  %10.2f  %10.2f\n",
                "F", "Shar branchless outer + compile-time n=4096 inner", wF, cF);

    std::printf("\ndeltas vs A:\n");
    std::printf("  outer spine   (B vs A):    warm %+.1f%%  cold %+.1f%%\n",
                (wB / wA - 1) * 100, (cB / cA - 1) * 100);
    std::printf("  inner 4096    (C vs A):    warm %+.1f%%  cold %+.1f%%\n",
                (wC / wA - 1) * 100, (cC / cA - 1) * 100);
    std::printf("  both spines   (D vs A):    warm %+.1f%%  cold %+.1f%%\n",
                (wD / wA - 1) * 100, (cD / cA - 1) * 100);
    std::printf("  Shar outer    (E vs A):    warm %+.1f%%  cold %+.1f%%\n",
                (wE / wA - 1) * 100, (cE / cA - 1) * 100);
    std::printf("  Shar + inner  (F vs A):    warm %+.1f%%  cold %+.1f%%\n",
                (wF / wA - 1) * 100, (cF / cA - 1) * 100);

    std::printf("\ndeltas vs D (current best stacked):\n");
    std::printf("  Shar outer    (E vs D):    warm %+.1f%%  cold %+.1f%%\n",
                (wE / wD - 1) * 100, (cE / cD - 1) * 100);
    std::printf("  Shar + inner  (F vs D):    warm %+.1f%%  cold %+.1f%%\n",
                (wF / wD - 1) * 100, (cF / cD - 1) * 100);
    return 0;
}

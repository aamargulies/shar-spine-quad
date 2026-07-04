// F vs F* sweep micro-benchmark over inner_n.
//
// Forked from bench_twolevel.cpp (2026-05-19). Where bench_twolevel runs 10
// variants at fixed inner_n=4096, this benchmark runs only:
//   F  = Shar branchless outer (K=512) + general-n spine inner
//   F* = Shar branchless outer (K=512) + per-N compile-time-specialized inner
//        (constant-prop unroll of the general-n descent; not the hybrid --
//        see CLAUDE.md decision 2026-05-19)
// across the swept inner_n.
//
// Hosts wired up: M4 Max (default ARM, gap=64) and Pi 5 / Cortex-A76
// (-DQUADSEARCH_ARM_PI5, gap=32). Goal is to measure where compile-time
// inner specialization actually pays across the full Roaring container size
// range, not to port to all 6.
//
// Build (M4 Max):
//   clang++ -O3 -mcpu=apple-m4 -std=c++20 \
//       bench_sweep.cpp simd_quad_m4.c simd_quad_m4_spine_family.c \
//       -o bench_sweep
//
// Build (Pi 5):
//   g++ -O3 -mcpu=cortex-a76 -std=c++20 -DQUADSEARCH_ARM_PI5 \
//       bench_sweep.cpp simd_quad_pi5.c simd_quad_pi5_spine_family.c \
//       -o bench_sweep
//
// Run: ./bench_sweep <inner_n> <mode> [num_sets] [hot_reps]
//   <inner_n>  = one of the values in {m4,pi5}_runs/sweep_n_list.txt
//   <mode>     = hb / hs / cb / cs (single-mode, fresh process)
//   defaults: num_sets=200 hot_reps=200
//
// Measurement order: cold modes thrash 256 MB scratch beforehand. Hot modes
// don't thrash. Single mode per process so cold is genuinely cold (no prior
// hot pass leaving the LLC warm).

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <random>
#include <set>
#include <vector>

#include <arm_neon.h>

// Lemire's reference simd_quad (gap=16, NEON). Included as a bare function
// body. We don't use it as a measured variant here, but bench_twolevel.cpp
// keeps it for cross-host comparison; bench_sweep is F vs F* only.
#include "simd_quad.c"

#if defined(QUADSEARCH_ARM_PI5)
bool simd_quad_pi5_spine(const uint16_t *carr, const uint16_t *spine,
                         int32_t cardinality, uint16_t pos);
void simd_quad_pi5_build_spine(const uint16_t *carr, int32_t cardinality,
                               uint16_t *spine);
bool simd_quad_pi5_spineN_dispatch(const uint16_t *carr,
                                   const uint16_t *spine,
                                   int32_t n, uint16_t pos);
static constexpr int kGap = 32;
static inline bool inner_F(const uint16_t *carr, const uint16_t *spine,
                           int32_t cardinality, uint16_t pos) {
    return simd_quad_pi5_spine(carr, spine, cardinality, pos);
}
static inline void build_spine(const uint16_t *carr, int32_t cardinality,
                               uint16_t *spine) {
    simd_quad_pi5_build_spine(carr, cardinality, spine);
}
static inline bool inner_Fstar(const uint16_t *carr, const uint16_t *spine,
                               int32_t n, uint16_t pos) {
    return simd_quad_pi5_spineN_dispatch(carr, spine, n, pos);
}
#else
bool simd_quad_m4_spine(const uint16_t *carr, const uint16_t *spine,
                        int32_t cardinality, uint16_t pos);
void simd_quad_m4_build_spine(const uint16_t *carr, int32_t cardinality,
                              uint16_t *spine);
bool simd_quad_m4_spineN_dispatch(const uint16_t *carr,
                                    const uint16_t *spine,
                                    int32_t n, uint16_t pos);
static constexpr int kGap = 64;
static inline bool inner_F(const uint16_t *carr, const uint16_t *spine,
                           int32_t cardinality, uint16_t pos) {
    return simd_quad_m4_spine(carr, spine, cardinality, pos);
}
static inline void build_spine(const uint16_t *carr, int32_t cardinality,
                               uint16_t *spine) {
    simd_quad_m4_build_spine(carr, cardinality, spine);
}
static inline bool inner_Fstar(const uint16_t *carr, const uint16_t *spine,
                               int32_t n, uint16_t pos) {
    return simd_quad_m4_spineN_dispatch(carr, spine, n, pos);
}
#endif

using clock_type = std::chrono::steady_clock;

static constexpr size_t kThrashBytes = 256u * 1024u * 1024u;
static void thrash_llc() {
    static std::vector<uint8_t> scratch;
    if (scratch.empty()) scratch.assign(kThrashBytes, 0);
    volatile uint8_t *p = scratch.data();
    for (size_t i = 0; i < kThrashBytes; i += 64) p[i] = (uint8_t)i;
}

struct Container {
    std::vector<uint16_t> carr;
    std::vector<uint16_t> spine;
};

struct ContainerSet {
    std::vector<uint16_t> keys;
    std::vector<Container> containers;
};

static std::vector<uint16_t> make_sorted_u16(std::mt19937 &rng, int n) {
    std::set<uint16_t> s;
    std::uniform_int_distribution<int> d(0, 65535);
    while ((int)s.size() < n) s.insert((uint16_t)d(rng));
    return std::vector<uint16_t>(s.begin(), s.end());
}

static ContainerSet make_set(std::mt19937 &rng, int num_containers, int inner_n) {
    ContainerSet s;
    s.keys = make_sorted_u16(rng, num_containers);
    s.containers.resize(num_containers);
    for (int i = 0; i < num_containers; i++) {
        s.containers[i].carr = make_sorted_u16(rng, inner_n);
        // spine entry per gap-sized block; partial tail block is not
        // covered by the spine (handled by the tail sweep in the inner).
        int num_blocks = inner_n / kGap;
        s.containers[i].spine.resize(num_blocks);
        if (num_blocks > 0) {
            build_spine(s.containers[i].carr.data(), inner_n,
                        s.containers[i].spine.data());
        }
    }
    return s;
}

// Shar branchless binary search over s.keys (K=num_containers). Same body
// as find_container_shar in bench_twolevel.cpp.
static inline int find_container_shar(const ContainerSet &s, uint16_t key) {
    int len = (int)s.keys.size();
    if (len == 0) return -1;
    const uint16_t *base  = s.keys.data();
    const uint16_t *begin = base;
    int step = 1;
    while ((step << 1) <= len) step <<= 1;
    if (step != len && begin[step] < key) begin = begin + (len - step);
    for (step >>= 1; step != 0; step >>= 1) {
        if (begin[step] < key) begin += step;
    }
    const uint16_t *lo = begin + (*begin < key);
    if (lo < base + len && *lo == key) return (int)(lo - base);
    return -1;
}

static int g_inner_n = 0;

static bool lookup_F(const ContainerSet &s, uint32_t v) {
    int idx = find_container_shar(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return inner_F(c.carr.data(), c.spine.data(),
                   (int32_t)c.carr.size(), (uint16_t)v);
}

static bool lookup_Fstar(const ContainerSet &s, uint32_t v) {
    int idx = find_container_shar(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return inner_Fstar(c.carr.data(), c.spine.data(),
                       g_inner_n, (uint16_t)v);
}

template <typename Fn>
static double bench_hot_batched(const std::vector<ContainerSet> &sets,
                                const std::vector<std::vector<uint32_t>> &targets,
                                int hot_reps, Fn fn) {
    volatile uint64_t acc = 0;
    auto t0 = clock_type::now();
    for (size_t si = 0; si < sets.size(); si++) {
        for (int r = 0; r < hot_reps; r++) {
            uint32_t t = targets[si][(r * 17u) % targets[si].size()];
            acc += fn(sets[si], t);
        }
    }
    auto t1 = clock_type::now();
    (void)acc;
    double ns = std::chrono::duration<double, std::nano>(t1 - t0).count();
    return ns / (double)(sets.size() * hot_reps);
}

template <typename Fn>
static double bench_hot_serial(const std::vector<ContainerSet> &sets,
                               const std::vector<std::vector<uint32_t>> &targets,
                               int hot_reps, Fn fn) {
    uint32_t carry = 0;
    volatile uint64_t acc = 0;
    auto t0 = clock_type::now();
    for (size_t si = 0; si < sets.size(); si++) {
        for (int r = 0; r < hot_reps; r++) {
            uint32_t t = targets[si][(r * 17u) % targets[si].size()] ^ carry;
            bool hit = fn(sets[si], t);
            carry = (uint32_t)hit;
            acc += carry;
        }
    }
    auto t1 = clock_type::now();
    (void)acc;
    double ns = std::chrono::duration<double, std::nano>(t1 - t0).count();
    return ns / (double)(sets.size() * hot_reps);
}

template <typename Fn>
static double bench_cold_batched(const std::vector<ContainerSet> &sets,
                                 const std::vector<std::vector<uint32_t>> &targets,
                                 Fn fn) {
    volatile uint64_t acc = 0;
    auto t0 = clock_type::now();
    for (size_t si = 0; si < sets.size(); si++) {
        acc += fn(sets[si], targets[si][1]);
    }
    auto t1 = clock_type::now();
    (void)acc;
    double ns = std::chrono::duration<double, std::nano>(t1 - t0).count();
    return ns / (double)sets.size();
}

template <typename Fn>
static double bench_cold_serial(const std::vector<ContainerSet> &sets,
                                const std::vector<std::vector<uint32_t>> &targets,
                                Fn fn) {
    uint32_t carry = 0;
    volatile uint64_t acc = 0;
    auto t0 = clock_type::now();
    for (size_t si = 0; si < sets.size(); si++) {
        uint32_t t = targets[si][1] ^ carry;
        bool hit = fn(sets[si], t);
        carry = (uint32_t)hit;
        acc += carry;
    }
    auto t1 = clock_type::now();
    (void)acc;
    double ns = std::chrono::duration<double, std::nano>(t1 - t0).count();
    return ns / (double)sets.size();
}

int main(int argc, char **argv) {
    if (argc < 3) {
        std::fprintf(stderr,
                     "usage: %s <inner_n> <mode:hb|hs|cb|cs> [num_sets=200] [hot_reps=200]\n",
                     argv[0]);
        return 2;
    }
    int inner_n   = std::atoi(argv[1]);
    const char *mode = argv[2];
    int num_sets  = (argc > 3) ? std::atoi(argv[3]) : 200;
    int hot_reps  = (argc > 4) ? std::atoi(argv[4]) : 200;

    if (inner_n < kGap) {
        std::fprintf(stderr, "inner_n=%d below gap=%d floor; sweep skips n<%d\n",
                     inner_n, kGap, kGap);
        return 2;
    }
    g_inner_n = inner_n;

    constexpr int num_containers = 512;

    std::printf("# bench_sweep inner_n=%d mode=%s num_sets=%d hot_reps=%d\n",
                inner_n, mode, num_sets, hot_reps);

    std::mt19937 rng(0xB17F17);
    std::vector<ContainerSet> sets;
    sets.reserve(num_sets);
    std::vector<std::vector<uint32_t>> targets;
    targets.reserve(num_sets);
    for (int i = 0; i < num_sets; i++) {
        sets.push_back(make_set(rng, num_containers, inner_n));
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

    // Correctness: F and F* must agree on every probe across a sample.
    for (int si = 0; si < std::min(5, num_sets); si++) {
        for (int k = 0; k < 200; k++) {
            uint32_t t = targets[si][k];
            bool rF  = lookup_F(sets[si], t);
            bool rFs = lookup_Fstar(sets[si], t);
            if (rF != rFs) {
                std::fprintf(stderr,
                             "MISMATCH inner_n=%d set=%d t=%u F=%d F*=%d\n",
                             inner_n, si, t, rF, rFs);
                return 1;
            }
        }
    }

    auto NaN = std::numeric_limits<double>::quiet_NaN();
    double F_val = NaN, Fs_val = NaN;

    // Hot modes: warmup pass over all sets so F and F* see equal cache state.
    // Without this, the first-measured variant pays the cold-DRAM working-set
    // cost (~145 ns/q) while the second runs warm (~20 ns/q); see bench_twolevel
    // variant A vs E delta. bench_twolevel masks this by running 10 variants
    // back-to-back in one process; bench_sweep has only 2, so we explicitly
    // warm with a single pass before each timed measurement.
    auto warmup_hot = [&](auto fn) {
        volatile uint64_t acc = 0;
        for (size_t si = 0; si < sets.size(); si++) {
            for (int r = 0; r < hot_reps; r++) {
                uint32_t t = targets[si][(r * 17u) % targets[si].size()];
                acc += fn(sets[si], t);
            }
        }
        (void)acc;
    };

    // Warm both variants' code + the working set before each timed run so
    // neither variant pays first-touch DRAM cost relative to the other.
    auto warm_both_hot = [&]() {
        warmup_hot(lookup_F);
        warmup_hot(lookup_Fstar);
    };

    if (std::strcmp(mode, "hb") == 0) {
        warm_both_hot();
        F_val  = bench_hot_batched(sets, targets, hot_reps, lookup_F);
        warm_both_hot();
        Fs_val = bench_hot_batched(sets, targets, hot_reps, lookup_Fstar);
    } else if (std::strcmp(mode, "hs") == 0) {
        warm_both_hot();
        F_val  = bench_hot_serial(sets, targets, hot_reps, lookup_F);
        warm_both_hot();
        Fs_val = bench_hot_serial(sets, targets, hot_reps, lookup_Fstar);
    } else if (std::strcmp(mode, "cb") == 0) {
        // First cold measurement in a process pays one-time startup costs
        // (TLB warmup / page faults / OS page-cache priming on the freshly
        // allocated 200-set heap). Run a discarded throwaway pass with one
        // of the variants so the *measured* F and F* are on equal footing.
        // Throwaway uses lookup_F so F* is structurally fresher when timed,
        // but both have paid the page-fault cost.
        bench_cold_batched(sets, targets, lookup_F);
        thrash_llc();
        F_val  = bench_cold_batched(sets, targets, lookup_F);
        thrash_llc();
        Fs_val = bench_cold_batched(sets, targets, lookup_Fstar);
    } else if (std::strcmp(mode, "cs") == 0) {
        bench_cold_serial(sets, targets, lookup_F);
        thrash_llc();
        F_val  = bench_cold_serial(sets, targets, lookup_F);
        thrash_llc();
        Fs_val = bench_cold_serial(sets, targets, lookup_Fstar);
    } else {
        std::fprintf(stderr, "unknown mode '%s' (use hb/hs/cb/cs)\n", mode);
        return 2;
    }

    // Machine-readable single-line result for the driver to grep.
    std::printf("RESULT inner_n=%d mode=%s F=%.4f Fstar=%.4f\n",
                inner_n, mode, F_val, Fs_val);
    return 0;
}

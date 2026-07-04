// F vs Lemire-reference sweep over inner_n in [1, 8192].
//
// Forked from bench_twolevel.cpp (2026-05-20). Where bench_twolevel measures
// 10 variants at fixed inner_n=4096, this sweep measures only:
//   F   = Shar branchless outer (K=512) + general-n spine inner
//         (the apples-to-apples form of F across all N -- the compile-time
//          n=4096 hybrid only exists at n=4096; for the sweep we use the
//          general-n spine inner for F)
//   Lem = Lemire reference (bsearch outer + simd_quad inner, gap=16, no spine)
//
// Goal: trace F vs Lem across the full range, deliberately exceeding 4096 to
// 8192 to see what happens beyond the "designed-for" Roaring container size.
//
// Below n=gap (n<64 on M4) the spine has no entries; the inner falls back to
// simd_quad_m4 (small-size NEON fast paths). For n in this range F still
// exists structurally (Shar outer + non-spine inner) and the F vs Lem ratio
// is meaningful but the spine does no work.
//
// Build (M4 Max):
//   clang++ -O3 -mcpu=apple-m4 -std=c++20 \
//       bench_sweep_f_vs_lem.cpp simd_quad_m4.c -o bench_sweep_f_vs_lem
//
// Run: ./bench_sweep_f_vs_lem <inner_n> <mode:hb|hs|cb|cs> [num_sets=200] [hot_reps=200]
//
// Single-mode-per-process so cold is genuinely cold.

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

// Lemire's reference simd_quad (gap=16, NEON). Bare function body.
#include "simd_quad.c"

// M4 spine inner (general-n; falls back to simd_quad_m4 at n < gap).
bool simd_quad_m4_spine(const uint16_t *carr, const uint16_t *spine,
                        int32_t cardinality, uint16_t pos);
void simd_quad_m4_build_spine(const uint16_t *carr, int32_t cardinality,
                              uint16_t *spine);

static constexpr int kGap = 64;

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
    std::vector<uint16_t> spine;  // empty when inner_n < kGap
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
        int num_blocks = inner_n / kGap;
        s.containers[i].spine.resize(num_blocks);
        if (num_blocks > 0) {
            simd_quad_m4_build_spine(s.containers[i].carr.data(), inner_n,
                                     s.containers[i].spine.data());
        }
    }
    return s;
}

// Shar branchless binary search over s.keys (K=num_containers).
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

static inline int find_container_bsearch(const ContainerSet &s, uint16_t key) {
    auto it = std::lower_bound(s.keys.begin(), s.keys.end(), key);
    if (it != s.keys.end() && *it == key) return (int)(it - s.keys.begin());
    return -1;
}

static bool lookup_F(const ContainerSet &s, uint32_t v) {
    int idx = find_container_shar(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return simd_quad_m4_spine(c.carr.data(), c.spine.data(),
                              (int32_t)c.carr.size(), (uint16_t)v);
}

static bool lookup_Lem(const ContainerSet &s, uint32_t v) {
    int idx = find_container_bsearch(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return simd_quad(c.carr.data(), (int32_t)c.carr.size(), (uint16_t)v);
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

    if (inner_n < 1) {
        std::fprintf(stderr, "inner_n must be >= 1\n");
        return 2;
    }

    constexpr int num_containers = 512;

    std::printf("# bench_sweep_f_vs_lem inner_n=%d mode=%s num_sets=%d hot_reps=%d\n",
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

    // Correctness: F and Lem must agree on every probe across a sample.
    for (int si = 0; si < std::min(5, num_sets); si++) {
        for (int k = 0; k < 200; k++) {
            uint32_t t = targets[si][k];
            bool rF = lookup_F(sets[si], t);
            bool rL = lookup_Lem(sets[si], t);
            if (rF != rL) {
                std::fprintf(stderr,
                             "MISMATCH inner_n=%d set=%d t=%u F=%d Lem=%d\n",
                             inner_n, si, t, rF, rL);
                return 1;
            }
        }
    }

    auto NaN = std::numeric_limits<double>::quiet_NaN();
    double F_val = NaN, Lem_val = NaN;

    // Equal-cache-state warmup so neither variant pays first-touch DRAM cost.
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
    auto warm_both_hot = [&]() {
        warmup_hot(lookup_F);
        warmup_hot(lookup_Lem);
    };

    if (std::strcmp(mode, "hb") == 0) {
        warm_both_hot();
        F_val   = bench_hot_batched(sets, targets, hot_reps, lookup_F);
        warm_both_hot();
        Lem_val = bench_hot_batched(sets, targets, hot_reps, lookup_Lem);
    } else if (std::strcmp(mode, "hs") == 0) {
        warm_both_hot();
        F_val   = bench_hot_serial(sets, targets, hot_reps, lookup_F);
        warm_both_hot();
        Lem_val = bench_hot_serial(sets, targets, hot_reps, lookup_Lem);
    } else if (std::strcmp(mode, "cb") == 0) {
        // Discard one cold pass so process-startup TLB/page-fault costs
        // don't bias whichever variant is measured first (per CLAUDE.md
        // memory: cold-bench-process-startup).
        bench_cold_batched(sets, targets, lookup_F);
        thrash_llc();
        F_val   = bench_cold_batched(sets, targets, lookup_F);
        thrash_llc();
        Lem_val = bench_cold_batched(sets, targets, lookup_Lem);
    } else if (std::strcmp(mode, "cs") == 0) {
        bench_cold_serial(sets, targets, lookup_F);
        thrash_llc();
        F_val   = bench_cold_serial(sets, targets, lookup_F);
        thrash_llc();
        Lem_val = bench_cold_serial(sets, targets, lookup_Lem);
    } else {
        std::fprintf(stderr, "unknown mode '%s' (use hb/hs/cb/cs)\n", mode);
        return 2;
    }

    std::printf("RESULT inner_n=%d mode=%s F=%.4f Lem=%.4f\n",
                inner_n, mode, F_val, Lem_val);
    return 0;
}

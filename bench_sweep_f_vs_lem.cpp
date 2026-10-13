// F vs Lemire-reference sweep over inner_n in [1, 8192].
//
// Forked from bench_twolevel.cpp (2026-05-20). Where bench_twolevel measures
// 10 variants at fixed inner_n=4096, this sweep measures, at one inner_n per
// process:
//   F    = Shar branchless outer (K=512) + the host's general-n spine inner
//          (the apples-to-apples form of F across all N -- the compile-time
//           n=4096 hybrid only exists at n=4096)
//   Lem  = Lemire reference as published 2026-04-27 (bsearch outer +
//          simd_quad inner, gap=16, no spine; simd_quad.c)
//   Lem2 = the same with Lemire's kernel as revised 2026-10-02
//          (simd_quad_2026_10.c: arrays under 16 elements are searched with
//           two overlapping SIMD loads instead of a linear scan; identical to
//           Lem from 16 elements up, so Lem2 vs Lem at n >= 16 is a noise
//           gauge). Added 2026-10-11; the archived 2026-05-20 M4 campaign
//          (m4_runs/sweep_fvl_raw.txt) has only F and Lem.
//   Fb   = Lem's bsearch outer in front of F's spine inner (two-level
//          variant A, here across all N). Added 2026-10-12 with LemS to
//          separate the outer search from the inner kernel: F and Lem differ
//          in both, and the Pi 5 sweep_fvl2 campaign had Lemire ahead in
//          cold_ser below n ~ 265 by a roughly size-independent margin,
//          which looks like an outer effect (the branchy std::lower_bound
//          lets the core speculate its loads past mispredicted branches,
//          Shar's cmov chain cannot be speculated past; Khuong & Morin).
//   LemS = F's Shar outer in front of Lemire's April kernel, the fourth cell
//          of the 2 x 2 {Shar, bsearch} outer x {spine, simd_quad} inner.
//          Fb vs F and Lem vs LemS are the outer's effect (negative = bsearch
//          faster) with each inner; Fb vs Lem and F vs LemS are the inner's
//          effect (negative = spine faster) with each outer.
//
// Goal: trace F vs Lem across the full range, deliberately exceeding 4096 to
// 8192 to see what happens beyond the "designed-for" Roaring container size.
//
// Below n=gap the spine has no entries and the inner delegates to the host's
// non-spine kernel (small-size fast paths); up to num_blocks <= 3 the spine
// kernel delegates as well. For n in this range F still exists structurally
// (Shar outer + non-spine inner) and the F vs Lem ratio is meaningful but the
// spine does no work.
//
// Build:
//   Apple M4 Max / M1 Pro (gap 64):
//     clang++ -O3 -mcpu=apple-m4 -std=c++20 bench_sweep_f_vs_lem.cpp simd_quad_m4.c -o bench_sweep_f_vs_lem
//   Raspberry Pi 5 (gap 32):
//     g++ -O3 -mcpu=cortex-a76 -std=c++20 -DQUADSEARCH_ARM_PI5 bench_sweep_f_vs_lem.cpp simd_quad_pi5.c -o bench_sweep_f_vs_lem
//   AWS Graviton 4 (gap 32):
//     g++ -O3 -mcpu=neoverse-v2 -std=c++20 -DQUADSEARCH_ARM_GV4 bench_sweep_f_vs_lem.cpp simd_quad_graviton.c -o bench_sweep_f_vs_lem
//   Intel (gap 32; see simd_quad_intel.c for the -march choice):
//     g++ -O3 -march=native -std=c++20 bench_sweep_f_vs_lem.cpp simd_quad_intel.c -o bench_sweep_f_vs_lem
//
// Run: ./bench_sweep_f_vs_lem <inner_n> <mode:hb|hs|cb|cs> [num_sets=200] [hot_reps=200] [order_seed=0]
//   order_seed != 0 shuffles the order in which the five variants are timed
//   (drivers pass the run index); 0 keeps the canonical F, Lem, Lem2, Fb,
//   LemS order, which starts with the F-then-Lem order of the archived M4
//   campaign. The RESULT line prints the five columns in canonical order
//   whatever the timing order; campaigns of this five-column harness use
//   the file prefix sweep_fvl3 (sweep_fvl2 = F/Lem/Lem2, sweep_fvl = F/Lem).
//
// Single-mode-per-process so cold is genuinely cold. Every variant is checked
// against a scalar reference before timing (200 probes of each of the first
// five sets; for inner_n <= 64 also every element and its two neighbours).
//
// The containers and targets are a deterministic function of (inner_n,
// num_sets): the same seed and the same draws since the 2026-05-20 campaign.
// Since 2026-10-12 make_sorted_u16 uses a 65536-bit membership bitmap instead
// of a std::set for the rejection sampling -- the same uniform draws in the
// same order with the same acceptance, so every array and every target is
// bit for bit what the earlier campaigns measured (verified against the
// std::set version over the whole size list); only the heap layout of the
// arrays and the set-up time change (~20x less at n = 4096, where set-up,
// not measurement, was most of a cell's wall-clock).

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <random>
#include <vector>

#if defined(__ARM_NEON) || defined(__aarch64__)
  #define QUADSEARCH_ARCH_ARM 1
  #include <arm_neon.h>
#elif defined(__x86_64__) || defined(_M_X64)
  #define QUADSEARCH_ARCH_X86 1
  #include <immintrin.h>
#else
  #error "Unsupported architecture for bench_sweep_f_vs_lem"
#endif

// Lemire's reference simd_quad as published 2026-04-27 (gap=16, no spine).
// Bare function body; the arch header above supplies the intrinsics.
#include "simd_quad.c"
// Lemire's kernel as revised 2026-10-02 (defines simd_quad_2026_10).
#include "simd_quad_2026_10.c"

// Host inner kernel for F: general-n spine search + spine builder. Same
// selection as bench_twolevel.cpp.
#if QUADSEARCH_ARCH_X86
bool simd_quad_intel_spine(const uint16_t *carr, const uint16_t *spine,
                           int32_t cardinality, uint16_t pos);
void simd_quad_intel_build_spine(const uint16_t *carr, int32_t cardinality,
                                 uint16_t *spine);
static constexpr int kGap = 32;
#define INNER_SPINE       simd_quad_intel_spine
#define INNER_BUILD_SPINE simd_quad_intel_build_spine
#define INNER_NAME        "intel_spine"
#elif defined(QUADSEARCH_ARM_PI5)
bool simd_quad_pi5_spine(const uint16_t *carr, const uint16_t *spine,
                         int32_t cardinality, uint16_t pos);
void simd_quad_pi5_build_spine(const uint16_t *carr, int32_t cardinality,
                               uint16_t *spine);
static constexpr int kGap = 32;
#define INNER_SPINE       simd_quad_pi5_spine
#define INNER_BUILD_SPINE simd_quad_pi5_build_spine
#define INNER_NAME        "pi5_spine"
#elif defined(QUADSEARCH_ARM_GV4)
bool simd_quad_graviton_spine(const uint16_t *carr, const uint16_t *spine,
                              int32_t cardinality, uint16_t pos);
void simd_quad_graviton_build_spine(const uint16_t *carr, int32_t cardinality,
                                    uint16_t *spine);
static constexpr int kGap = 32;
#define INNER_SPINE       simd_quad_graviton_spine
#define INNER_BUILD_SPINE simd_quad_graviton_build_spine
#define INNER_NAME        "graviton_spine"
#else
// Apple M4 Max / M1 Pro: the default ARM build, gap 64.
bool simd_quad_m4_spine(const uint16_t *carr, const uint16_t *spine,
                        int32_t cardinality, uint16_t pos);
void simd_quad_m4_build_spine(const uint16_t *carr, int32_t cardinality,
                              uint16_t *spine);
static constexpr int kGap = 64;
#define INNER_SPINE       simd_quad_m4_spine
#define INNER_BUILD_SPINE simd_quad_m4_build_spine
#define INNER_NAME        "m4_spine"
#endif

using clock_type = std::chrono::steady_clock;

// 512 MB, as in bench_twolevel.cpp: larger than any LLC on the target list
// (the 2026-05-20 M4 campaign used 256 MB).
static constexpr size_t kThrashBytes = 512u * 1024u * 1024u;
static void thrash_llc() {
    static std::vector<uint8_t> scratch;
    if (scratch.empty()) scratch.assign(kThrashBytes, 0);
    volatile uint8_t *p = scratch.data();
    for (size_t i = 0; i < kThrashBytes; i += 64) p[i] = (uint8_t)i;
}

// Container descriptor. 48 bytes in a 16-byte-aligned std::vector, so one in
// four descriptors straddles two cache lines with the spine's data pointer
// (offset 24) on the second line while carr (offsets 0..15) is on the first:
// the spine variants F and Fb read that extra line in one of four lookups,
// Lem and LemS never do. Every campaign up to sweep_fvl3 (2026-10-12) was
// measured that way. The descriptor-layout A/B of 2026-10-12 (this harness
// built both ways, 14 sizes x 5 runs on the Pi 5 "trixie",
// pi5_runs/desc_layout_ab_compare.txt) found no resolvable bias: the two
// descriptor loads are independent and overlap, the inner contrasts moved by
// +1 to +6 ns hot (inside noise) and the verdict bands are the same in both
// layouts, so the archived inner contrasts stand. Building with
// -DQUADSEARCH_DESCRIPTOR_ALIGN=64 pads and aligns the descriptor to one line
// so every variant reads exactly one descriptor line (hygiene; campaigns from
// 2026-10-12 evening on, and bench_ab_pi5.cpp, use it). The header line
// records desc_align so campaigns of the two layouts are never pooled.
#ifndef QUADSEARCH_DESCRIPTOR_ALIGN
#define QUADSEARCH_DESCRIPTOR_ALIGN 16
#endif
struct alignas(QUADSEARCH_DESCRIPTOR_ALIGN) Container {
    std::vector<uint16_t> carr;
    std::vector<uint16_t> spine;  // empty when inner_n < kGap
};

struct ContainerSet {
    std::vector<uint16_t> keys;
    std::vector<Container> containers;
};

// n distinct uniform u16 values, sorted. Rejection sampling with a 65536-bit
// membership bitmap: draw, keep if new, stop at n kept. Draw for draw the
// std::set version it replaced (2026-10-12), so the data of every campaign
// since 2026-05-20 are reproduced exactly; see the header comment.
static std::vector<uint16_t> make_sorted_u16(std::mt19937 &rng, int n) {
    std::uniform_int_distribution<int> d(0, 65535);
    std::vector<uint64_t> bits(65536 / 64, 0);
    int count = 0;
    while (count < n) {
        unsigned v = (unsigned)d(rng);
        uint64_t m = 1ull << (v & 63u);
        if (!(bits[v >> 6] & m)) {
            bits[v >> 6] |= m;
            count++;
        }
    }
    std::vector<uint16_t> out;
    out.reserve(n);
    for (unsigned w = 0; w < bits.size(); w++) {
        uint64_t x = bits[w];
        while (x) {
            out.push_back((uint16_t)(w * 64u + (unsigned)__builtin_ctzll(x)));
            x &= x - 1;
        }
    }
    return out;
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
            INNER_BUILD_SPINE(s.containers[i].carr.data(), inner_n,
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
    return INNER_SPINE(c.carr.data(), c.spine.data(),
                       (int32_t)c.carr.size(), (uint16_t)v);
}

static bool lookup_Lem(const ContainerSet &s, uint32_t v) {
    int idx = find_container_bsearch(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return simd_quad(c.carr.data(), (int32_t)c.carr.size(), (uint16_t)v);
}

// Same outer as Lem, Lemire's 2026-10-02 kernel inside.
static bool lookup_Lem2(const ContainerSet &s, uint32_t v) {
    int idx = find_container_bsearch(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return simd_quad_2026_10(c.carr.data(), (int32_t)c.carr.size(), (uint16_t)v);
}

// Lem's outer, F's inner (two-level variant A). Against F it isolates the
// outer search, against Lem the inner kernel.
static bool lookup_Fb(const ContainerSet &s, uint32_t v) {
    int idx = find_container_bsearch(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return INNER_SPINE(c.carr.data(), c.spine.data(),
                       (int32_t)c.carr.size(), (uint16_t)v);
}

// F's outer, Lem's inner: the remaining cell of the outer x inner square.
static bool lookup_LemS(const ContainerSet &s, uint32_t v) {
    int idx = find_container_shar(s, (uint16_t)(v >> 16));
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
                     "usage: %s <inner_n> <mode:hb|hs|cb|cs> [num_sets=200] [hot_reps=200] [order_seed=0]\n",
                     argv[0]);
        return 2;
    }
    int inner_n   = std::atoi(argv[1]);
    const char *mode = argv[2];
    int num_sets  = (argc > 3) ? std::atoi(argv[3]) : 200;
    int hot_reps  = (argc > 4) ? std::atoi(argv[4]) : 200;
    unsigned order_seed = (argc > 5) ? (unsigned)std::strtoul(argv[5], nullptr, 10) : 0u;

    if (inner_n < 1) {
        std::fprintf(stderr, "inner_n must be >= 1\n");
        return 2;
    }

    constexpr int num_containers = 512;

    std::printf("# bench_sweep_f_vs_lem inner_n=%d mode=%s num_sets=%d hot_reps=%d order_seed=%u gap=%d inner=%s desc_align=%d desc_size=%zu\n",
                inner_n, mode, num_sets, hot_reps, order_seed, kGap, INNER_NAME,
                (int)QUADSEARCH_DESCRIPTOR_ALIGN, sizeof(Container));
    std::printf("# variants: F = Shar outer + %s inner; Lem = bsearch outer + simd_quad (2026-04-27); "
                "Lem2 = bsearch outer + simd_quad_2026_10 (2026-10-02); "
                "Fb = bsearch outer + %s inner (two-level A); "
                "LemS = Shar outer + simd_quad (2026-04-27)\n", INNER_NAME, INNER_NAME);

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

    // Correctness: every variant must agree with a scalar reference
    // (std::lower_bound over the keys, then std::binary_search in the
    // container) on 200 probes of each of the first five sets; for small
    // inner_n also on every element of those sets' containers and on the
    // values just below and above each element, which exercises the
    // overlapping-load paths of simd_quad_2026_10 at every cardinality.
    auto ref_lookup = [&](const ContainerSet &s, uint32_t v) {
        int idx = find_container_bsearch(s, (uint16_t)(v >> 16));
        if (idx < 0) return false;
        const auto &c = s.containers[idx].carr;
        return std::binary_search(c.begin(), c.end(), (uint16_t)v);
    };
    auto check = [&](const ContainerSet &s, int si, uint32_t t) {
        bool r = ref_lookup(s, t);
        bool rF = lookup_F(s, t), rL = lookup_Lem(s, t), rL2 = lookup_Lem2(s, t);
        bool rFb = lookup_Fb(s, t), rLS = lookup_LemS(s, t);
        if (rF != r || rL != r || rL2 != r || rFb != r || rLS != r) {
            std::fprintf(stderr,
                         "MISMATCH inner_n=%d set=%d t=%u ref=%d F=%d Lem=%d Lem2=%d Fb=%d LemS=%d\n",
                         inner_n, si, t, (int)r, (int)rF, (int)rL, (int)rL2, (int)rFb, (int)rLS);
            return false;
        }
        return true;
    };
    for (int si = 0; si < std::min(5, num_sets); si++) {
        for (int k = 0; k < 200; k++)
            if (!check(sets[si], si, targets[si][k])) return 1;
        if (inner_n <= 64) {
            for (int ci = 0; ci < num_containers; ci++) {
                const auto &c = sets[si].containers[ci].carr;
                uint32_t hi = uint32_t(sets[si].keys[ci]) << 16;
                for (uint16_t e : c) {
                    if (!check(sets[si], si, hi | e)) return 1;
                    if (e > 0 && !check(sets[si], si, hi | (uint32_t)(e - 1))) return 1;
                    if (e < 65535 && !check(sets[si], si, hi | (uint32_t)(e + 1))) return 1;
                }
            }
        }
    }

    auto NaN = std::numeric_limits<double>::quiet_NaN();
    // Variants in canonical order; the RESULT line always prints F, Lem, Lem2, Fb, LemS.
    constexpr int kVariants = 5;
    const char *names[kVariants] = {"F", "Lem", "Lem2", "Fb", "LemS"};
    bool (*fns[kVariants])(const ContainerSet &, uint32_t) =
        {lookup_F, lookup_Lem, lookup_Lem2, lookup_Fb, lookup_LemS};
    double vals[kVariants] = {NaN, NaN, NaN, NaN, NaN};
    int order[kVariants] = {0, 1, 2, 3, 4};
    if (order_seed != 0) {
        std::mt19937 g(order_seed * 1000003u + (unsigned)inner_n * 7919u
                       + (unsigned)(unsigned char)mode[0] * 131u + (unsigned)(unsigned char)mode[1]);
        std::shuffle(order, order + kVariants, g);
    }
    std::printf("# timing order:");
    for (int i : order) std::printf(" %s", names[i]);
    std::printf("\n");

    // Equal-cache-state warmup so no variant pays first-touch DRAM cost: all
    // five variants run over every set before each timed variant.
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
    auto warm_all_hot = [&]() { for (int i = 0; i < kVariants; i++) warmup_hot(fns[i]); };

    if (std::strcmp(mode, "hb") == 0) {
        for (int i : order) { warm_all_hot(); vals[i] = bench_hot_batched(sets, targets, hot_reps, fns[i]); }
    } else if (std::strcmp(mode, "hs") == 0) {
        for (int i : order) { warm_all_hot(); vals[i] = bench_hot_serial(sets, targets, hot_reps, fns[i]); }
    } else if (std::strcmp(mode, "cb") == 0) {
        // Discard one cold pass so process-startup TLB/page-fault costs
        // don't bias whichever variant is measured first.
        bench_cold_batched(sets, targets, fns[order[0]]);
        for (int i : order) { thrash_llc(); vals[i] = bench_cold_batched(sets, targets, fns[i]); }
    } else if (std::strcmp(mode, "cs") == 0) {
        bench_cold_serial(sets, targets, fns[order[0]]);
        for (int i : order) { thrash_llc(); vals[i] = bench_cold_serial(sets, targets, fns[i]); }
    } else {
        std::fprintf(stderr, "unknown mode '%s' (use hb/hs/cb/cs)\n", mode);
        return 2;
    }

    std::printf("RESULT inner_n=%d mode=%s F=%.4f Lem=%.4f Lem2=%.4f Fb=%.4f LemS=%.4f\n",
                inner_n, mode, vals[0], vals[1], vals[2], vals[3], vals[4]);
    return 0;
}

// Kernel A/B harness for the Raspberry Pi 5 (Cortex-A76) kernel: six variants
// of the two-level lookup that differ only in the inner kernel (or in the
// alignment of its data), timed per inner_n on the same 512-container sets
// and the same targets as bench_sweep_f_vs_lem.cpp (same seed, same draws),
// so its F column runs the arrays and targets of the sweep_fvl2 / sweep_fvl3
// campaigns' F (with the same heap layout of the plain arrays -- the Fa
// copies are allocated in a second pass -- but a one-line descriptor instead
// of that harness's 48-byte one, and a hot warm-up that ends with the variant
// about to be timed; compare levels across campaigns with that in mind, the
// within-run pairs are what this harness is for).
//
// Forked from bench_sweep_f_vs_lem.cpp on 2026-10-12. The outer search is
// fixed (Shar's branchless binary search over the 512 container keys, as in
// F); every contrast below is a single kernel-side change:
//
//   F    = Shar outer + simd_quad_pi5_spine as shipped (the baseline; the
//          spine kernel delegates num_blocks <= 3, i.e. n < 128, to the plain
//          kernel simd_quad_pi5, and runs its own copy of the small-size
//          fast paths below n = 32)
//   Fcr  = F with constant-return scalar sweeps: every
//              if (x >= pos) return x == pos;
//          in the fast paths and block tails becomes
//              if (x == pos) return true; if (x > pos) return false;
//          (GCC 17 compiles the shipped form to a data-dependent cset return
//          and Lemire's equality loop to constant returns through branches;
//          the sweep_fvl3 campaign left the Pi 5 kernel's n <= 7 cold_ser
//          deficit at that difference -- pi5_runs/sweep_fvl3_findings.md.)
//          Note that GCC 17 does not compile the rewrite to "the shipped
//          code with a different return": the scalar steps get two branches
//          per element instead of one, the auto-vectorised step two vector
//          compares instead of one, and the last element of a sweep still
//          ends in a cset (assembly of both kernels archived in
//          pi5_runs/sweep_ab1_asm/). Fcr vs F therefore measures the
//          constant-return source form as compiled, which is what one would
//          ship, not the return idiom in isolation. Differs from F only
//          where a sweep runs: n < 32 and the tails of n that are not a
//          multiple of 32.
//   Fd1  = F with the spine's delegation threshold lowered from num_blocks
//          <= 3 to <= 1: the spine descent runs from two blocks (n >= 64)
//          instead of four (n >= 128). Differs from F at n = 64..127 only.
//   Fa   = F on cache-line-aligned copies of every container array and spine
//          (64 bytes here, 128 on Apple hosts; std::vector gives 16-byte
//          alignment, so in F about three of four 32-element blocks straddle
//          two 64-byte lines and the 256-byte n = 4096 spine usually spans
//          five lines instead of four). Same code and same values as F; the
//          addresses differ, and each copy's size is rounded up to the line,
//          as a line-aligned allocator would do (so below n = 32, where no
//          block exists, Fa vs F measures only that footprint).
//   G    = Shar outer + the plain kernel simd_quad_pi5 (no spine; one
//          speculative __builtin_prefetch per quaternary iteration, as
//          shipped). Below n = 32 F runs the spine function's own copy of
//          the fast paths (opcode for opcode the plain kernel's), and at
//          32..127 F delegates to the same source, but GCC inlines the
//          delegated copy into the spine function and range-specialises it
//          (a peeled one-block path, a fully unrolled tail sweep: a different
//          compilation of the same algorithm, a few percent apart at most in
//          the review's probes), so G vs F below 128 is a same-traffic gauge
//          of codegen plus noise, not an identical-code gauge (Gnp vs G is
//          that); at n = 128..255 it is, to the same codegen caveat, what F
//          would run with a delegation threshold of 7 (CLAUDE.md open item
//          6: the spine is 6-22 ns slower hot and 40-100 ns faster cold than
//          Lemire's inner at four to seven blocks); from n = 256 up it is the
//          value of the spine itself.
//   Gnp  = G without the in-loop prefetch -- the code of simd_quad_graviton
//          (CLAUDE.md, Files). Gnp vs G is the prefetch A/B (open item 2);
//          it can differ from G only where the quaternary loop iterates,
//          n >= 128. Gnp vs F is the threshold-7 contrast with the
//          prefetch-free kernel.
//
// The variant kernels are generated from simd_quad_pi5.c by
// gen_pi5_ab_variants.py (exact-string substitutions, counts asserted; the
// unified diffs are archived with the campaign as
// pi5_runs/sweep_ab1_variants.diff). The generator also writes one
// translation unit per kernel, ab_tu_{base,cr,d1,np}.cpp, each wrapping the
// kernel source in its own namespace (ab_base #includes simd_quad_pi5.c
// itself), so every kernel is compiled exactly as the shipped kernel TU is
// -- same flags, same intra-kernel inlining -- and the harness calls it
// across a TU boundary, as every other harness of the project does. The
// delegation call inside a variant's spine function resolves to that
// variant's own plain kernel through the namespace.
//
// Build (from the repo root; the binaries go off the CIFS share):
//   V=/home/pi/build_ab/variants
//   python3 gen_pi5_ab_variants.py $V --diff pi5_runs/sweep_ab1_variants.diff
//   for k in base cr d1 np; do
//     g++ -O3 -mcpu=cortex-a76 -std=c++20 -I $V -c $V/ab_tu_$k.cpp -o $V/ab_tu_$k.o
//   done
//   g++ -O3 -mcpu=cortex-a76 -std=c++20 \
//       -DQUADSEARCH_KERNEL_BLOB="\"$(git hash-object simd_quad_pi5.c)\"" \
//       bench_ab_pi5.cpp $V/ab_tu_base.o $V/ab_tu_cr.o $V/ab_tu_d1.o $V/ab_tu_np.o \
//       -o /home/pi/bench_ab_pi5
//
// Run: ./bench_ab_pi5 <inner_n> <mode:hb|hs|cb|cs> [num_sets=200] [hot_reps=200] [order_seed=0]
//   order_seed != 0 shuffles the order in which the six variants are timed
//   (drivers pass the run index). The RESULT line prints the six columns in
//   canonical order whatever the timing order:
//     RESULT inner_n=<N> mode=<m> F=<ns> Fcr=<ns> Fd1=<ns> Fa=<ns> G=<ns> Gnp=<ns>
//   Campaigns of this harness use the file prefix sweep_ab1 with the
//   pi5_runs/run_sweep_f_vs_lem.sh driver (FVL_BIN, FVL_PREFIX=sweep_ab1);
//   compute_sweep_fvl.py / plot_sweep_fvl.py know the prefix.
//
// Modes and measurement are those of bench_sweep_f_vs_lem.cpp: one mode per
// process; hb/hs time hot_reps queries per set (outer-hot, inner first-touch),
// cb/cs one query per set after a 512 MB flush before every variant; the
// serial modes chain each query's result into the next target. Every variant
// is checked against a scalar reference before timing (200 probes of each of
// the first five sets; for inner_n <= 64 also every element and its two
// neighbours), and the aligned copies are checked byte for byte against the
// vectors they copy.

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <memory>
#include <random>
#include <vector>

#if !defined(__ARM_NEON) && !defined(__aarch64__)
  #error "bench_ab_pi5 is an AArch64/NEON harness for the Pi 5 kernel"
#endif

#ifndef QUADSEARCH_KERNEL_BLOB
#define QUADSEARCH_KERNEL_BLOB "unknown"
#endif

// The kernels live in the generated per-variant TUs (see the header).
#define AB_DECLARE_KERNEL(ns)                                                            \
    namespace ns {                                                                       \
    bool simd_quad_pi5(const uint16_t *carr, int32_t cardinality, uint16_t pos);         \
    bool simd_quad_pi5_spine(const uint16_t *carr, const uint16_t *spine,                \
                             int32_t cardinality, uint16_t pos);                         \
    void simd_quad_pi5_build_spine(const uint16_t *carr, int32_t cardinality,            \
                                   uint16_t *spine);                                     \
    }
AB_DECLARE_KERNEL(ab_base)
AB_DECLARE_KERNEL(ab_cr)
AB_DECLARE_KERNEL(ab_d1)
AB_DECLARE_KERNEL(ab_np)

static constexpr int kGap = 32;
// The host's cache line: the Fa copies are aligned to it and their sizes
// rounded up to it, which is what a line-aligned container allocator would
// do on this host. (A larger alignment would also inflate the footprint of
// small arrays: with 128-byte rounding on this 64-byte-line host, every n < 64
// array occupied two lines' worth and the n = 1 Fa cell was 44% slower hot
// for that reason alone, in the first launch of this campaign.)
#if defined(__APPLE__)
static constexpr size_t kAlign = 128;
#else
static constexpr size_t kAlign = 64;
#endif

using clock_type = std::chrono::steady_clock;

// 512 MB, as in bench_sweep_f_vs_lem.cpp and bench_twolevel.cpp.
static constexpr size_t kThrashBytes = 512u * 1024u * 1024u;
static void thrash_llc() {
    static std::vector<uint8_t> scratch;
    if (scratch.empty()) scratch.assign(kThrashBytes, 0);
    volatile uint8_t *p = scratch.data();
    for (size_t i = 0; i < kThrashBytes; i += 64) p[i] = (uint8_t)i;
}

struct FreeDeleter {
    void operator()(void *p) const { std::free(p); }
};
using AlignedBuf = std::unique_ptr<uint16_t, FreeDeleter>;

static AlignedBuf aligned_copy(const std::vector<uint16_t> &v) {
    if (v.empty()) return AlignedBuf();
    size_t bytes = v.size() * sizeof(uint16_t);
    size_t rounded = (bytes + kAlign - 1) / kAlign * kAlign;  // aligned_alloc needs a multiple of the alignment
    void *p = std::aligned_alloc(kAlign, rounded);
    if (!p) {
        std::fprintf(stderr, "aligned_alloc(%zu, %zu) failed\n", kAlign, rounded);
        std::exit(1);
    }
    if (((uintptr_t)p & (kAlign - 1)) != 0) {
        std::fprintf(stderr, "aligned_alloc returned a misaligned pointer\n");
        std::exit(1);
    }
    std::memcpy(p, v.data(), bytes);
    return AlignedBuf((uint16_t *)p);
}

// One container descriptor = exactly one 64-byte line, line-aligned, so every
// variant's lookup touches exactly one descriptor line whichever fields it
// reads (F reads carr and spine, Fa reads carr_al and spine_al, G/Gnp read
// carr only). Without this (64 B at std::vector's 16-byte alignment) the Fa
// fields sat on a second line in three of four descriptors and F's spine
// pointer in one of four. Measured, that costs little: the two descriptor
// loads are independent and overlap, and the descriptor-layout A/B of
// 2026-10-12 on bench_sweep_f_vs_lem (48-byte vs line-aligned descriptor, 14
// sizes x 5 runs; pi5_runs/desc_layout_ab_compare.txt) moved the spine-vs-
// Lemire inner contrasts by +1 to +6 ns hot, inside run-to-run noise. The
// one-line descriptor is kept as hygiene. What does make Fa slower than F
// hot at n = 1 (69 vs 39 ns on eight at 100 sets) is footprint: a line-aligned
// copy of a 2-byte array occupies a full line, and glibc's aligned_alloc(64,
// 64) places the copies 128 B apart, so the 51,200 tiny arrays of 100 sets
// span ~6.3 MB and 1,600 pages against ~2 MB and 500 pages for the vectors
// and leave the 2 MB L3 -- the cost of line-aligning tiny containers with a
// general-purpose allocator (a packed line-aligned arena would pay less), gone
// once an array is a block or more (negligible from n = 256).
struct alignas(64) Container {
    std::vector<uint16_t> carr;
    std::vector<uint16_t> spine;  // empty when inner_n < kGap
    AlignedBuf carr_al;           // line-aligned copy of carr
    AlignedBuf spine_al;          // line-aligned copy of spine (null when spine is empty)
};
static_assert(sizeof(Container) == 64, "Container must be exactly one 64-byte line");

struct ContainerSet {
    std::vector<uint16_t> keys;
    std::vector<Container> containers;
};

// n distinct uniform u16 values, sorted: the bitmap rejection sampler of
// bench_sweep_f_vs_lem.cpp, draw for draw, so the arrays are those of the
// sweep_fvl2 / sweep_fvl3 campaigns at the same (inner_n, num_sets).
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
    if (((uintptr_t)s.containers.data() & 63u) != 0) {
        std::fprintf(stderr, "container descriptors are not line-aligned\n");
        std::exit(1);
    }
    for (int i = 0; i < num_containers; i++) {
        Container &c = s.containers[i];
        c.carr = make_sorted_u16(rng, inner_n);
        int num_blocks = inner_n / kGap;
        c.spine.resize(num_blocks);
        if (num_blocks > 0) {
            ab_base::simd_quad_pi5_build_spine(c.carr.data(), inner_n, c.spine.data());
        }
        // The Fa copies are made in a second pass in main(), after every set
        // and target exists: allocating them here, between the vectors,
        // pushed almost every plain array to one line offset (residue 16 mod
        // 64 in 90-100% of containers, review of 2026-10-12), so F's blocks
        // all straddled instead of three in four as in bench_sweep_f_vs_lem.
    }
    return s;
}

// Line-aligned copies for Fa, allocated after all sets and targets so the
// plain arrays keep the heap layout of bench_sweep_f_vs_lem.cpp. Prints the
// line-offset histogram of the plain arrays and spines (residue mod 64 in
// 16-byte steps) so the campaign archives the layout it measured.
static void make_aligned_copies(std::vector<ContainerSet> &sets) {
    unsigned hc[4] = {0, 0, 0, 0}, hs[4] = {0, 0, 0, 0}, ha[4] = {0, 0, 0, 0};
    for (auto &s : sets) {
        for (auto &c : s.containers) {
            c.carr_al = aligned_copy(c.carr);
            c.spine_al = aligned_copy(c.spine);
            if (std::memcmp(c.carr_al.get(), c.carr.data(), c.carr.size() * sizeof(uint16_t)) != 0 ||
                (!c.spine.empty() &&
                 std::memcmp(c.spine_al.get(), c.spine.data(), c.spine.size() * sizeof(uint16_t)) != 0)) {
                std::fprintf(stderr, "aligned copy differs from its source\n");
                std::exit(1);
            }
            hc[((uintptr_t)c.carr.data() >> 4) & 3u]++;
            if (!c.spine.empty()) hs[((uintptr_t)c.spine.data() >> 4) & 3u]++;
            ha[((uintptr_t)c.carr_al.get() >> 4) & 3u]++;
        }
    }
    std::printf("# layout: plain carr residue mod 64 (0/16/32/48) %u/%u/%u/%u; plain spine %u/%u/%u/%u; "
                "Fa copies %u/%u/%u/%u; descriptors %zu B line-aligned\n",
                hc[0], hc[1], hc[2], hc[3], hs[0], hs[1], hs[2], hs[3], ha[0], ha[1], ha[2], ha[3],
                sizeof(Container));
}

// Shar branchless binary search over s.keys (K=num_containers), as in F.
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
    return ab_base::simd_quad_pi5_spine(c.carr.data(), c.spine.data(),
                                        (int32_t)c.carr.size(), (uint16_t)v);
}

static bool lookup_Fcr(const ContainerSet &s, uint32_t v) {
    int idx = find_container_shar(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return ab_cr::simd_quad_pi5_spine(c.carr.data(), c.spine.data(),
                                      (int32_t)c.carr.size(), (uint16_t)v);
}

static bool lookup_Fd1(const ContainerSet &s, uint32_t v) {
    int idx = find_container_shar(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return ab_d1::simd_quad_pi5_spine(c.carr.data(), c.spine.data(),
                                      (int32_t)c.carr.size(), (uint16_t)v);
}

static bool lookup_Fa(const ContainerSet &s, uint32_t v) {
    int idx = find_container_shar(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return ab_base::simd_quad_pi5_spine(c.carr_al.get(), c.spine_al.get(),
                                        (int32_t)c.carr.size(), (uint16_t)v);
}

static bool lookup_G(const ContainerSet &s, uint32_t v) {
    int idx = find_container_shar(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return ab_base::simd_quad_pi5(c.carr.data(), (int32_t)c.carr.size(), (uint16_t)v);
}

static bool lookup_Gnp(const ContainerSet &s, uint32_t v) {
    int idx = find_container_shar(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return ab_np::simd_quad_pi5(c.carr.data(), (int32_t)c.carr.size(), (uint16_t)v);
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

    std::printf("# bench_ab_pi5 inner_n=%d mode=%s num_sets=%d hot_reps=%d order_seed=%u gap=%d inner=pi5_spine kernel_blob=%s align=%zu\n",
                inner_n, mode, num_sets, hot_reps, order_seed, kGap, QUADSEARCH_KERNEL_BLOB, kAlign);
    std::printf("# variants: F = Shar outer + simd_quad_pi5_spine as shipped; "
                "Fcr = F with constant-return scalar sweeps; "
                "Fd1 = F with spine delegation threshold 1 (spine from two blocks); "
                "Fa = F on %zu-byte-aligned arrays and spines; ", kAlign);
    std::printf(
                "G = Shar outer + plain simd_quad_pi5 (in-loop prefetch as shipped); "
                "Gnp = G without the in-loop prefetch\n");

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
    make_aligned_copies(sets);

    // Correctness: every variant must agree with a scalar reference.
    auto NaN = std::numeric_limits<double>::quiet_NaN();
    constexpr int kVariants = 6;
    const char *names[kVariants] = {"F", "Fcr", "Fd1", "Fa", "G", "Gnp"};
    bool (*fns[kVariants])(const ContainerSet &, uint32_t) =
        {lookup_F, lookup_Fcr, lookup_Fd1, lookup_Fa, lookup_G, lookup_Gnp};

    auto ref_lookup = [&](const ContainerSet &s, uint32_t v) {
        int idx = find_container_bsearch(s, (uint16_t)(v >> 16));
        if (idx < 0) return false;
        const auto &c = s.containers[idx].carr;
        return std::binary_search(c.begin(), c.end(), (uint16_t)v);
    };
    auto check = [&](const ContainerSet &s, int si, uint32_t t) {
        bool r = ref_lookup(s, t);
        for (int i = 0; i < kVariants; i++) {
            bool got = fns[i](s, t);
            if (got != r) {
                std::fprintf(stderr, "MISMATCH inner_n=%d set=%d t=%u ref=%d %s=%d\n",
                             inner_n, si, t, (int)r, names[i], (int)got);
                return false;
            }
        }
        return true;
    };
    for (int si = 0; si < std::min(5, num_sets); si++) {
        for (int k = 0; k < 200; k++)
            if (!check(sets[si], si, targets[si][k])) return 1;
        if (inner_n <= 128) {  // covers Fd1's two- and three-block descents (n = 64..127)
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

    double vals[kVariants] = {NaN, NaN, NaN, NaN, NaN, NaN};
    int order[kVariants] = {0, 1, 2, 3, 4, 5};
    if (order_seed != 0) {
        std::mt19937 g(order_seed * 1000003u + (unsigned)inner_n * 7919u
                       + (unsigned)(unsigned char)mode[0] * 131u + (unsigned)(unsigned char)mode[1]);
        std::shuffle(order, order + kVariants, g);
    }
    std::printf("# timing order:");
    for (int i : order) std::printf(" %s", names[i]);
    std::printf("\n");

    // Equal-cache-state warmup so no variant pays first-touch DRAM cost: all
    // six variants run over every set before each timed variant.
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

    // Equal-cache-state warm-up, then the variant about to be timed once more.
    // Without the second step the fixed canonical warm-up order ended with G
    // and Gnp over the std::vector arrays, so the data only some variants
    // touch was the oldest in the caches at timing time: Fa's copies (only
    // Fa reads them; review of 2026-10-12: 8-9 ns of its ~40 ns gap to F at
    // n = 1 hot, the other ~31 ns being the footprint of one line per copy)
    // and, at n >= 128, the spine lines that only F, Fcr and Fd1 read. The
    // extra pass puts every variant's data in the same, freshest state.
    if (std::strcmp(mode, "hb") == 0) {
        for (int i : order) { warm_all_hot(); warmup_hot(fns[i]); vals[i] = bench_hot_batched(sets, targets, hot_reps, fns[i]); }
    } else if (std::strcmp(mode, "hs") == 0) {
        for (int i : order) { warm_all_hot(); warmup_hot(fns[i]); vals[i] = bench_hot_serial(sets, targets, hot_reps, fns[i]); }
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

    std::printf("RESULT inner_n=%d mode=%s F=%.4f Fcr=%.4f Fd1=%.4f Fa=%.4f G=%.4f Gnp=%.4f\n",
                inner_n, mode, vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]);
    return 0;
}

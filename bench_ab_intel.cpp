// Kernel A/B harness for the Intel kernel (simd_quad_intel.c) on the Coffee
// Lake laptop (Core i9-9980HK "i9", -march=native = skylake: the AVX2 block
// check with the in-loop prefetch kept): six variants of the two-level lookup
// that differ only in the inner kernel, timed per inner_n on the same
// 512-container sets and the same targets as bench_sweep_f_vs_lem.cpp (same
// seed, same draws -- its bitmap generator is reused verbatim below), so the
// F and LemS columns run the arrays and targets of the cfl sweep_fvl3
// campaign's F and LemS, with the same heap layout of the arrays when both
// harnesses are built with -DQUADSEARCH_DESCRIPTOR_ALIGN=64 (as the Coffee
// Lake campaigns were; the descriptor is the same two std::vectors), but a
// hot warm-up that ends with the variant about to be timed; compare levels
// across campaigns with that in mind, the within-run pairs are what this
// harness is for.
//
// Modelled on bench_ab_pi5.cpp (2026-10-12, the reviewed design: Shar outer
// fixed, six inner variants, exhaustive correctness at small n, untimed
// warm_all_hot() then warmup_hot(fns[i]) before each timed hot variant,
// order_seed shuffle, thrash before every cold cell, one-line descriptors,
// one RESULT line) and forked from bench_sweep_f_vs_lem.cpp on 2026-10-13,
// without the aligned-copy machinery (no Fa: the alignment contrast exists
// for this host in bench.cpp's 'nA' rows, cfl_runs/rebench_flushed*_paired.txt).
// Every contrast is a single kernel-side change:
//
//   F    = Shar outer + simd_quad_intel_spine as shipped (the baseline; the
//          spine kernel delegates num_blocks <= 3, i.e. n < 128, to the plain
//          kernel simd_quad_intel, and runs its own copy of the small-size
//          fast paths below n = 32).
//   Ft   = F with the vector tail: in every general-n kernel of the file the
//          scalar sweep of the partial last block,
//              for (j = num_blocks * gap; j < cardinality; j++) { v = carr[j]; if (v >= pos) return v == pos; }
//          becomes the block check's membership test over the last gap (32)
//          elements of the array (two 256-bit loads + cmpeq + OR + movemask
//          on this host's AVX2 path; one zmm compare under __AVX512VBMI2__).
//          The correctness argument is in the generated source
//          (intel_ab_tail.c, TAIL_NEW in gen_intel_ab_variants.py) and
//          `./bench_ab_intel selftest` checks it exhaustively. Ft can differ
//          from F only where the tail path runs -- the descent ended at lo ==
//          num_blocks, i.e. pos is above the last full block's maximum: for
//          the campaign's targets about (n mod 32) / n of the inner queries
//          that reach a container (hits in the tail and misses above every
//          block), none at n % 32 == 0 -- and, at n = 32..127, through the
//          spine function's delegated copy of the plain kernel, which GCC
//          inlines and compiles anew inside the variant's TU. Where no tail
//          path runs, Ft vs F is an identical-traffic gauge of codegen plus
//          noise (methodology lesson 7: the tail TU is a different compilation
//          of the whole file, not the shipped object with one basic block
//          swapped). Where it runs, the sweep read the tail elements up to the
//          first >= pos with one branch each; the vector test reads the
//          array's last 64 bytes, which contain the element the descent has
//          just probed, so the line traffic differs by at most one line.
//   G    = Shar outer + the plain kernel simd_quad_intel as shipped: on this
//          AVX2 build (no __AVX512VBMI2__) the two-ymm block check and the
//          in-loop _mm_prefetch(carr + (base + n/2) * gap) kept. Below n = 32
//          F runs the spine function's own copy of the fast paths, and at
//          32..127 F delegates to the same source compiled inside the spine
//          function, so G vs F below 128 is a same-traffic gauge of codegen
//          plus noise; at n = 128..255 it is, to the same codegen caveat,
//          what F would run with a delegation threshold of 7 (the Intel spine
//          delegates num_blocks <= 3 exactly as the Pi 5's does; the Coffee
//          Lake sweep found no four-to-seven-block hot deficit for the spine
//          inner, cfl_runs/cfl_findings.md); from n = 256 up it is the value
//          of the spine itself.
//   Gnp  = G without the in-loop prefetch: the kernel of
//          cfl_runs/prefetch_ab_variant.diff, which the main-bench half of the
//          Coffee Lake prefetch A/B runs (bench.cpp, campaign tag pfab,
//          2026-10-13). Gnp vs G is the two-level half of that A/B; the two
//          kernels are identical code below n = 128 (the quaternary loop does
//          not iterate), so those sizes are the identical-code gauge. On a
//          zmm build (__AVX512VBMI2__) the shipped kernel has no in-loop
//          prefetch and Gnp is the same code as G at every size.
//   Gt   = G with the vector tail (the same substitution as Ft, read through
//          the plain kernel alone, without the delegation layer).
//   LemS = Shar outer + Lemire's reference simd_quad as published 2026-04-27
//          (gap 16, no spine; simd_quad.c, #included into this TU exactly as
//          bench_sweep_f_vs_lem.cpp does it), the LemS of sweep_fvl3. F vs
//          LemS is that campaign's "inner: spine vs Lemire, Shar outer"
//          contrast on the same arrays and targets, here so every kernel
//          contrast can be read against the Lemire inner in the same run.
//
// The variant kernels are generated from simd_quad_intel.c by
// gen_intel_ab_variants.py (exact-string substitutions, counts asserted; the
// unified diffs go to OUTDIR/intel_ab_variants.diff, which a campaign
// archives next to its raw cells). The generator also writes one translation
// unit per kernel, ab_tu_{base,np,tail}.cpp, each wrapping the kernel source
// in its own namespace (ab_base #includes simd_quad_intel.c itself), so every
// kernel is compiled exactly as the shipped kernel TU is -- same flags, same
// intra-kernel inlining -- and the harness calls it across a TU boundary, as
// every other harness of the project does. The delegation call inside a
// variant's spine function resolves to that variant's own plain kernel
// through the namespace. ab_tu_base.cpp also carries the git blob id of the
// kernel file the variants were derived from (ab_base::kernel_blob()), which
// the header line prints.
//
// Build (on the laptop, from its repo copy; the generated TUs and the binary
// go to local disk, never to the share):
//   V=/home/adam/build_ab_intel/variants
//   python3 gen_intel_ab_variants.py $V
//   g++ -O3 -march=native -std=c++20 -DQUADSEARCH_DESCRIPTOR_ALIGN=64 \
//       bench_ab_intel.cpp $V/ab_tu_base.cpp $V/ab_tu_np.cpp $V/ab_tu_tail.cpp \
//       -o /home/adam/build_ab_intel/bench_ab_intel
//   Each file on that line is its own translation unit (no LTO), which is the
//   `-c` per TU build of bench_ab_pi5.cpp in one command. The TUs find the
//   kernel sources by path (#include "intel_ab_<v>.c" next to them, the
//   shipped kernel by absolute path), so no -I is needed. Add
//   -DQUADSEARCH_THRASH_BYTES='(1ull<<20)' for a functional smoke build; the
//   header line records thrash_mb so a smoke build cannot pass as a campaign
//   binary.
//
// Run: ./bench_ab_intel <inner_n> <mode:hb|hs|cb|cs> [num_sets=200] [hot_reps=200] [order_seed=0]
//   order_seed != 0 shuffles the order in which the six variants are timed
//   (drivers pass the run index). The RESULT line prints the six columns in
//   canonical order whatever the timing order:
//     RESULT inner_n=<N> mode=<m> F=<ns> Ft=<ns> G=<ns> Gnp=<ns> Gt=<ns> LemS=<ns>
//   Campaigns of this harness use the file prefix sweep_abi1 with the
//   run_sweep_f_vs_lem.sh driver (FVL_BIN=./bench_ab_intel
//   FVL_PREFIX=sweep_abi1 FVL_CPU=<core>); compute_sweep_fvl.py has no preset
//   for that prefix yet and takes the pairs on the command line (--pairs
//   'Ft:F,Gt:G,Gnp:G,G:F,Gnp:F,LemS:F').
//      ./bench_ab_intel selftest
//   runs no benchmark: it checks the tail variant's three kernels (plain,
//   spine, padded spine) -- and, as a sanity check, the base and np kernels
//   and Lemire's simd_quad -- against std::binary_search for every one of
//   the 65536 possible targets on four arrays per size at every n from 32 to
//   300 and at n = 4096 (hits and misses, tail path and block path, empty
//   and non-empty tails), because the tail rewrite is a kernel change.
//
// Modes and measurement are those of bench_sweep_f_vs_lem.cpp: one mode per
// process; hb/hs time hot_reps queries per set (outer-hot, inner first-touch),
// cb/cs one query per set after an LLC flush before every variant; the serial
// modes chain each query's result into the next target. Before timing, every
// variant is checked against a scalar reference: 200 probes of each of the
// first five sets; at inner_n <= 128 also every element of every container of
// those sets with its two neighbours, and all 65536 targets of 16 containers
// per set (80 containers, ~5 M targets x 6 variants); at inner_n > 128 also
// the last 48 elements of every container of those sets with their
// neighbours and a few values above the maximum (the tail window).

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <random>
#include <vector>

#if !defined(__x86_64__) && !defined(_M_X64)
  #error "bench_ab_intel is an x86-64 harness for the Intel kernel (simd_quad_intel.c)"
#endif
#include <immintrin.h>

// Lemire's reference simd_quad as published 2026-04-27 (gap=16, no spine).
// Bare function body; the arch header above supplies the intrinsics. This is
// how bench_sweep_f_vs_lem.cpp includes it for its Lem / LemS columns.
#include "simd_quad.c"

// The kernels live in the generated per-variant TUs (see the header).
#define AB_DECLARE_KERNEL(ns)                                                             \
    namespace ns {                                                                        \
    bool simd_quad_intel(const uint16_t *carr, int32_t cardinality, uint16_t pos);        \
    bool simd_quad_intel_spine(const uint16_t *carr, const uint16_t *spine,               \
                               int32_t cardinality, uint16_t pos);                        \
    bool simd_quad_intel_spine_padded(const uint16_t *carr, const uint16_t *spine,        \
                                      int32_t cardinality, uint16_t pos);                 \
    void simd_quad_intel_build_spine(const uint16_t *carr, int32_t cardinality,           \
                                     uint16_t *spine);                                    \
    void simd_quad_intel_build_spine_padded(const uint16_t *carr, int32_t cardinality,    \
                                            uint16_t *spine);                             \
    }
AB_DECLARE_KERNEL(ab_base)
AB_DECLARE_KERNEL(ab_np)
AB_DECLARE_KERNEL(ab_tail)
namespace ab_base {
const char *kernel_blob();    // git blob id of the kernel file the variants were derived from
const char *kernel_source();  // its path at generation time
}

static constexpr int kGap = 32;

// Which path of simd_quad_intel.c this build takes, as seen by this TU (the
// kernel TUs are compiled with the same flags). On the zmm path the shipped
// plain kernel has no in-loop prefetch, so Gnp is the same code as G.
#if defined(__AVX512VBMI2__)
#define AB_KERNEL_PATH "zmm"
#else
#define AB_KERNEL_PATH "avx2"
#endif

using clock_type = std::chrono::steady_clock;

// 512 MB, as in bench_sweep_f_vs_lem.cpp and bench_twolevel.cpp; overridable
// for functional smoke builds, recorded in the header line.
#ifndef QUADSEARCH_THRASH_BYTES
#define QUADSEARCH_THRASH_BYTES (512ull * 1024ull * 1024ull)
#endif
static constexpr size_t kThrashBytes = QUADSEARCH_THRASH_BYTES;
static_assert(kThrashBytes >= 64, "QUADSEARCH_THRASH_BYTES must cover at least one cache line");
static void thrash_llc() {
    static std::vector<uint8_t> scratch;
    if (scratch.empty()) scratch.assign(kThrashBytes, 0);
    volatile uint8_t *p = scratch.data();
    for (size_t i = 0; i < kThrashBytes; i += 64) p[i] = (uint8_t)i;
}

// Container descriptor: the two std::vectors of bench_sweep_f_vs_lem.cpp.
// Default alignment 64 = one line, line-aligned, so every variant's lookup
// touches exactly one descriptor line whichever fields it reads (F/Ft read
// carr and spine, the plain-kernel variants and LemS read carr only) -- the
// hygiene choice of the campaigns since the evening of 2026-10-12 and of
// bench_ab_pi5.cpp; the descriptor-layout A/B of that day found the 48-byte
// layout costs little (pi5_runs/desc_layout_ab_compare.txt). Build with
// -DQUADSEARCH_DESCRIPTOR_ALIGN=16 for the archived 48-byte layout. The
// header line records desc_align and desc_size.
#ifndef QUADSEARCH_DESCRIPTOR_ALIGN
#define QUADSEARCH_DESCRIPTOR_ALIGN 64
#endif
struct alignas(QUADSEARCH_DESCRIPTOR_ALIGN) Container {
    std::vector<uint16_t> carr;
    std::vector<uint16_t> spine;  // empty when inner_n < kGap
};
static_assert(QUADSEARCH_DESCRIPTOR_ALIGN != 64 || sizeof(Container) == 64,
              "with QUADSEARCH_DESCRIPTOR_ALIGN=64 the descriptor must be exactly one 64-byte line");

struct ContainerSet {
    std::vector<uint16_t> keys;
    std::vector<Container> containers;
};

// n distinct uniform u16 values, sorted: the bitmap rejection sampler of
// bench_sweep_f_vs_lem.cpp, verbatim, draw for draw, so the arrays are those
// of the sweep_fvl2 / sweep_fvl3 campaigns at the same (inner_n, num_sets).
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

// make_set of bench_sweep_f_vs_lem.cpp (same rng consumption: keys, then each
// container's array; the spine builder draws nothing). The builder is the
// shipped one; the generator does not touch it, and selftest checks that the
// tail TU's builder agrees.
static ContainerSet make_set(std::mt19937 &rng, int num_containers, int inner_n) {
    ContainerSet s;
    s.keys = make_sorted_u16(rng, num_containers);
    s.containers.resize(num_containers);
    if (((uintptr_t)s.containers.data() & (QUADSEARCH_DESCRIPTOR_ALIGN - 1)) != 0) {
        std::fprintf(stderr, "container descriptors are not %d-byte aligned\n", (int)QUADSEARCH_DESCRIPTOR_ALIGN);
        std::exit(1);
    }
    for (int i = 0; i < num_containers; i++) {
        Container &c = s.containers[i];
        c.carr = make_sorted_u16(rng, inner_n);
        int num_blocks = inner_n / kGap;
        c.spine.resize(num_blocks);
        if (num_blocks > 0) {
            ab_base::simd_quad_intel_build_spine(c.carr.data(), inner_n, c.spine.data());
        }
    }
    return s;
}

// Line-offset histogram of the arrays and spines (residue mod 64 in 16-byte
// steps), so the campaign archives the layout it measured: with std::vector
// storage about three of four 32-element blocks straddle two lines and the
// 256-byte n = 4096 spine usually spans five lines instead of four.
static void print_layout(const std::vector<ContainerSet> &sets) {
    unsigned hc[4] = {0, 0, 0, 0}, hs[4] = {0, 0, 0, 0};
    for (auto &s : sets) {
        for (auto &c : s.containers) {
            hc[((uintptr_t)c.carr.data() >> 4) & 3u]++;
            if (!c.spine.empty()) hs[((uintptr_t)c.spine.data() >> 4) & 3u]++;
        }
    }
    std::printf("# layout: carr residue mod 64 (0/16/32/48) %u/%u/%u/%u; spine %u/%u/%u/%u; "
                "descriptors %zu B at %d-byte alignment\n",
                hc[0], hc[1], hc[2], hc[3], hs[0], hs[1], hs[2], hs[3],
                sizeof(Container), (int)QUADSEARCH_DESCRIPTOR_ALIGN);
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
    return ab_base::simd_quad_intel_spine(c.carr.data(), c.spine.data(),
                                          (int32_t)c.carr.size(), (uint16_t)v);
}

static bool lookup_Ft(const ContainerSet &s, uint32_t v) {
    int idx = find_container_shar(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return ab_tail::simd_quad_intel_spine(c.carr.data(), c.spine.data(),
                                          (int32_t)c.carr.size(), (uint16_t)v);
}

static bool lookup_G(const ContainerSet &s, uint32_t v) {
    int idx = find_container_shar(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return ab_base::simd_quad_intel(c.carr.data(), (int32_t)c.carr.size(), (uint16_t)v);
}

static bool lookup_Gnp(const ContainerSet &s, uint32_t v) {
    int idx = find_container_shar(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return ab_np::simd_quad_intel(c.carr.data(), (int32_t)c.carr.size(), (uint16_t)v);
}

static bool lookup_Gt(const ContainerSet &s, uint32_t v) {
    int idx = find_container_shar(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return ab_tail::simd_quad_intel(c.carr.data(), (int32_t)c.carr.size(), (uint16_t)v);
}

// F's outer, Lemire's inner: bench_sweep_f_vs_lem.cpp's lookup_LemS.
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

// ---------------------------------------------------------------------------
// selftest: exhaustive check of the tail variant's kernels.
//
// For every n in 32..300 and n = 4096, four sorted arrays -- (U) n distinct
// uniform values over the whole u16 range, the campaign's kind of array; (L)
// n distinct uniform values from [0, 4n), so most of the 65536 targets lie
// above the maximum and take the tail path as misses; (T) the run of n
// consecutive values ending at 65535, so the maximum is 65535 and the last
// block/tail hits at the top of the range; (B) the run 0..n-1, so every target
// from n up is a miss above the maximum -- and for each array every one of the
// 65536 targets, against std::binary_search. Checked: the tail TU's plain,
// spine and padded-spine kernels (the three sites of the substitution) and,
// as a sanity check of the generator and the baseline, the base TU's three
// kernels, the np TU's plain kernel and Lemire's simd_quad. The tail path is
// pos > carr[num_blocks * gap - 1] (the descent ends at lo == num_blocks);
// its hits are the targets in the tail and its misses the targets above the
// last full block that are not in the tail; n % 32 == 0 (every 32 <= n <= 288
// that is a multiple of 32, and 4096) exercises the empty-tail case, where
// the window is the last full block and must never match.
// ---------------------------------------------------------------------------
static std::vector<uint16_t> make_sorted_range(std::mt19937 &rng, int n, unsigned lo, unsigned hi) {
    std::uniform_int_distribution<unsigned> d(lo, hi);
    std::vector<uint64_t> bits(65536 / 64, 0);
    int count = 0;
    while (count < n) {
        unsigned v = d(rng);
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

static std::vector<uint16_t> make_run(unsigned first, int n) {
    std::vector<uint16_t> out(n);
    for (int i = 0; i < n; i++) out[i] = (uint16_t)(first + (unsigned)i);
    return out;
}

static int selftest() {
    std::mt19937 rng(0x7A11A5);
    std::vector<int> sizes;
    for (int n = 32; n <= 300; n++) sizes.push_back(n);
    sizes.push_back(4096);
    const char *kinds = "ULTB";
    constexpr int kKernels = 8;
    const char *knames[kKernels] = {"tail:plain", "tail:spine", "tail:spine_padded",
                                    "base:plain", "base:spine", "base:spine_padded",
                                    "np:plain", "simd_quad(2026-04-27)"};
    uint64_t lookups = 0, hits = 0, misses = 0, tail_hits = 0, tail_misses = 0, empty_tail_arrays = 0;
    for (int n : sizes) {
        for (int kind = 0; kind < 4; kind++) {
            std::vector<uint16_t> a;
            switch (kind) {
                case 0: a = make_sorted_range(rng, n, 0u, 65535u); break;
                case 1: a = make_sorted_range(rng, n, 0u, std::min(65535u, 4u * (unsigned)n - 1u)); break;
                case 2: a = make_run(65536u - (unsigned)n, n); break;
                default: a = make_run(0u, n); break;
            }
            int nb = n / kGap;
            std::vector<uint16_t> spine(nb), spine_p(nb + 2), spine_t(nb), spine_pt(nb + 2);
            ab_base::simd_quad_intel_build_spine(a.data(), n, spine.data());
            ab_base::simd_quad_intel_build_spine_padded(a.data(), n, spine_p.data());
            ab_tail::simd_quad_intel_build_spine(a.data(), n, spine_t.data());
            ab_tail::simd_quad_intel_build_spine_padded(a.data(), n, spine_pt.data());
            if (spine != spine_t || spine_p != spine_pt) {
                std::fprintf(stderr, "selftest: the tail TU's spine builders differ from the base TU's at n=%d\n", n);
                return 1;
            }
            uint16_t last_full_max = a[(size_t)nb * kGap - 1];
            if (n % kGap == 0) empty_tail_arrays++;
            for (uint32_t p = 0; p < 65536; p++) {
                uint16_t pos = (uint16_t)p;
                bool ref = std::binary_search(a.begin(), a.end(), pos);
                bool got[kKernels] = {
                    ab_tail::simd_quad_intel(a.data(), n, pos),
                    ab_tail::simd_quad_intel_spine(a.data(), spine.data(), n, pos),
                    ab_tail::simd_quad_intel_spine_padded(a.data(), spine_p.data(), n, pos),
                    ab_base::simd_quad_intel(a.data(), n, pos),
                    ab_base::simd_quad_intel_spine(a.data(), spine.data(), n, pos),
                    ab_base::simd_quad_intel_spine_padded(a.data(), spine_p.data(), n, pos),
                    ab_np::simd_quad_intel(a.data(), n, pos),
                    simd_quad(a.data(), n, pos),
                };
                for (int k = 0; k < kKernels; k++) {
                    if (got[k] != ref) {
                        std::fprintf(stderr, "selftest MISMATCH n=%d array=%c pos=%u ref=%d %s=%d (last_full_max=%u, tail path=%d)\n",
                                     n, kinds[kind], p, (int)ref, knames[k], (int)got[k], (unsigned)last_full_max,
                                     (int)(pos > last_full_max));
                        return 1;
                    }
                }
                lookups++;
                if (ref) hits++; else misses++;
                if (pos > last_full_max) { if (ref) tail_hits++; else tail_misses++; }
            }
        }
    }
    std::printf("selftest: ok -- %zu sizes (32..300 and 4096) x 4 arrays x 65536 targets = %llu targets per kernel, "
                "%d kernels; %llu hits / %llu misses; tail path (pos above the last full block's maximum): "
                "%llu hits / %llu misses; %llu arrays with an empty tail (n %% 32 == 0)\n",
                sizes.size(), (unsigned long long)lookups, kKernels, (unsigned long long)hits,
                (unsigned long long)misses, (unsigned long long)tail_hits, (unsigned long long)tail_misses,
                (unsigned long long)empty_tail_arrays);
    return 0;
}

int main(int argc, char **argv) {
    if (argc >= 2 && std::strcmp(argv[1], "selftest") == 0) {
        std::printf("# bench_ab_intel selftest kernel_blob=%s kernel_source=%s kernel_path=%s\n",
                    ab_base::kernel_blob(), ab_base::kernel_source(), AB_KERNEL_PATH);
        return selftest();
    }
    if (argc < 3) {
        std::fprintf(stderr,
                     "usage: %s <inner_n> <mode:hb|hs|cb|cs> [num_sets=200] [hot_reps=200] [order_seed=0]\n"
                     "       %s selftest\n",
                     argv[0], argv[0]);
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
    if (num_sets < 1 || hot_reps < 1) {
        std::fprintf(stderr, "num_sets and hot_reps must be >= 1\n");
        return 2;
    }

    constexpr int num_containers = 512;

    std::printf("# bench_ab_intel inner_n=%d mode=%s num_sets=%d hot_reps=%d order_seed=%u gap=%d inner=intel "
                "kernel_blob=%s desc_align=%d desc_size=%zu thrash_mb=%.1f kernel_path=%s\n",
                inner_n, mode, num_sets, hot_reps, order_seed, kGap, ab_base::kernel_blob(),
                (int)QUADSEARCH_DESCRIPTOR_ALIGN, sizeof(Container), (double)kThrashBytes / (1024.0 * 1024.0),
                AB_KERNEL_PATH);
    std::printf("# variants: F = Shar outer + simd_quad_intel_spine as shipped; "
                "Ft = F with the vector tail (last-32-element membership test instead of the scalar tail sweep, "
                "in the plain, spine and padded-spine kernels); "
                "G = Shar outer + plain simd_quad_intel as shipped (%s); "
                "Gnp = G without the in-loop prefetch (cfl_runs/prefetch_ab_variant.diff); "
                "Gt = G with the vector tail; "
                "LemS = Shar outer + simd_quad (Lemire 2026-04-27, gap 16)\n",
#if defined(__AVX512VBMI2__)
                "zmm block check, no in-loop prefetch on this path: Gnp is the same code as G"
#else
                "two-ymm block check, in-loop _mm_prefetch kept on this path"
#endif
    );
    std::printf("# kernel: %s (git blob %s)\n", ab_base::kernel_source(), ab_base::kernel_blob());

    // The containers and targets: the exact rng consumption of
    // bench_sweep_f_vs_lem.cpp (seed, make_set, then 1024 targets per set:
    // odd k = a hit on a random element of a random container, even k = a
    // random u32), so a cell of this harness holds the same arrays and the
    // same targets as the sweep_fvl2 / sweep_fvl3 cell of the same
    // (inner_n, num_sets).
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
    print_layout(sets);

    // Correctness: every variant must agree with a scalar reference.
    auto NaN = std::numeric_limits<double>::quiet_NaN();
    constexpr int kVariants = 6;
    const char *names[kVariants] = {"F", "Ft", "G", "Gnp", "Gt", "LemS"};
    bool (*fns[kVariants])(const ContainerSet &, uint32_t) =
        {lookup_F, lookup_Ft, lookup_G, lookup_Gnp, lookup_Gt, lookup_LemS};

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
    constexpr int kExhaustiveStride = 32;  // 16 containers per set get all 65536 targets at inner_n <= 128
    for (int si = 0; si < std::min(5, num_sets); si++) {
        for (int k = 0; k < 200; k++)
            if (!check(sets[si], si, targets[si][k])) return 1;
        if (inner_n <= 128) {
            for (int ci = 0; ci < num_containers; ci++) {
                const auto &c = sets[si].containers[ci].carr;
                uint32_t hi = uint32_t(sets[si].keys[ci]) << 16;
                for (uint16_t e : c) {
                    if (!check(sets[si], si, hi | e)) return 1;
                    if (e > 0 && !check(sets[si], si, hi | (uint32_t)(e - 1))) return 1;
                    if (e < 65535 && !check(sets[si], si, hi | (uint32_t)(e + 1))) return 1;
                }
            }
            for (int ci = 0; ci < num_containers; ci += kExhaustiveStride) {
                uint32_t hi = uint32_t(sets[si].keys[ci]) << 16;
                for (uint32_t p = 0; p < 65536; p++)
                    if (!check(sets[si], si, hi | p)) return 1;
            }
        } else {
            // The tail window of every container: its last 48 elements (the
            // partial last block and at least 16 elements of the last full
            // block) with their neighbours, and values above the maximum.
            for (int ci = 0; ci < num_containers; ci++) {
                const auto &c = sets[si].containers[ci].carr;
                uint32_t hi = uint32_t(sets[si].keys[ci]) << 16;
                for (int j = std::max(0, inner_n - 48); j < inner_n; j++) {
                    uint16_t e = c[j];
                    if (!check(sets[si], si, hi | e)) return 1;
                    if (e > 0 && !check(sets[si], si, hi | (uint32_t)(e - 1))) return 1;
                    if (e < 65535 && !check(sets[si], si, hi | (uint32_t)(e + 1))) return 1;
                }
                uint32_t m = c[inner_n - 1];
                for (uint32_t d : {1u, 2u, 16u, 32u, 1000u}) {
                    if (m + d <= 65535u && !check(sets[si], si, hi | (m + d))) return 1;
                }
                if (!check(sets[si], si, hi | 65535u)) return 1;
                if (!check(sets[si], si, hi | 0u)) return 1;
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
    // six variants run over every set before each timed variant, then the
    // variant about to be timed once more, so the data only some variants
    // touch (the spine lines that only F and Ft read) is in the same,
    // freshest state whichever variant is timed (bench_ab_pi5.cpp, review of
    // 2026-10-12).
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

    std::printf("RESULT inner_n=%d mode=%s F=%.4f Ft=%.4f G=%.4f Gnp=%.4f Gt=%.4f LemS=%.4f\n",
                inner_n, mode, vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]);
    return 0;
}

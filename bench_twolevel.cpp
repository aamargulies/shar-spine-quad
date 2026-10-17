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
// This micro-bench compares (outer search x inner search):
//   A.   std::lower_bound over keys       +  general-n spine inner
//   B.   spine over keys                  +  general-n spine inner
//   C.   std::lower_bound over keys       +  compile-time-n=4096 spine inner
//   D.   spine over keys                  +  compile-time-n=4096 spine inner
//   E.   Shar branchless binary over keys +  general-n spine inner
//   F.   Shar branchless binary over keys +  compile-time-n=4096 spine inner
//   G.   Shar branchless binary over keys +  Shar branchless inner (no spine)
//   H.   Eytzinger layout + K&M prefetch  +  general-n spine inner
//   I.   Eytzinger layout + K&M prefetch  +  compile-time-n=4096 spine inner
//   Lem. std::lower_bound over keys       +  Lemire's simd_quad (gap 16, no spine)
//   Aa..Fa (only when built with -DQUADSEARCH_TWOLEVEL_ALIGNED=<bytes>):
//        the outer search of A..F  +  the same inner kernel reading <bytes>-
//        aligned copies of carr and spine -- the aligned-layout A/B; each
//        Xa vs X pair isolates the alignment (see struct Container).
//
// The difference between A and B isolates the outer-spine win; the
// difference between A and C isolates the compile-time-n-inner win; D
// combines both. E/F replace the outer search with Shar's 1971 branchless
// binary search: a single pointer plus step halving where every step is
// `if (begin[step] < key) begin += step;`, compiled to a cmov. Note that
// this is a *serial* chain (each load's address depends on the previous
// cmov), not a set of independent loads; it wins because it has no branch
// mispredicts and no side structure, not because the loads overlap.
// H/I use Khuong & Morin's (2017) Eytzinger layout with an explicit
// prefetch of the descendant cache line log2(kGap) levels down. Lem is
// the published reference the whole stack is measured against.
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
// Run: ./bench_twolevel [num_sets] [hot_reps] [mode] [order_seed]
//   Defaults: num_sets=200, hot_reps=200, mode=all, order_seed=0.
//   Each "set" is 512 containers of cardinality 4096 -- ~4 MB of
//   container data per set. mode selects hb / hs / cb / cs / all.
//   order_seed != 0 shuffles the order in which the variants are timed
//   within each mode pass (rows are still printed A..Lem); drivers should
//   pass a different seed per run so that a transient (governor hop,
//   interrupt, thermal event) cannot land on the same variant every run.
//
// Four measurement modes, crossing two axes:
//   axis 1: cache state.  hot = same set reused for hot_reps queries.
//                                The 1 KB outer key array (and its spine /
//                                Eytzinger copy) is reused on every rep
//                                and is genuinely hot. The ~100 crafted
//                                hits per set land in ~91 distinct
//                                containers, so most *inner* spine/block
//                                loads are first touches; whether they
//                                hit LLC or DRAM depends on the host's
//                                cache size (at 200 sets the per-pass
//                                footprint is ~7 MB: fits Apple/EMR/GV4
//                                L2/L3, exceeds Pi 5 and SKX LLC). Read
//                                "hot" as "outer hot, inner first-touch".
//                                Half of the hot queries are random u32
//                                values that miss at the outer and never
//                                reach the inner search.
//                         cold = one query per set, advancing across
//                                num_sets sets in sequence; each set is
//                                4 MB and we sweep 200 * 4 MB = 800 MB
//                                of data, so most sets are cold to L2
//                                (and, at num_sets=200, cold to LLC too
//                                on Skylake-class hosts).
//   axis 2: query dispatch.  batched = independent queries; the OoO
//                                engine can overlap several in flight,
//                                so memory latency is hidden by MLP.
//                                Measures throughput.
//                            serial = each query's input depends on the
//                                previous query's return value (via a
//                                cmov), so the OoO engine cannot start
//                                the next query until the previous one
//                                returns. Measures critical-path
//                                latency.
//
// Interpreting results:
//   hot_bat  - throughput with hot caches. Shortest numbers; dominated
//              by per-query critical-path length when the scalar chain
//              is long (A, G) and by pipeline throughput when short.
//   hot_ser  - latency with hot caches. Shows the true per-query
//              dependent critical path, no MLP / ILP hiding.
//   cold_bat - throughput with cold caches. Here MLP helps a lot: many
//              independent DRAM misses can be in flight. Every cold query
//              is a crafted hit (outer + inner end-to-end); see the note
//              above bench_cold_batched for why.
//   cold_ser - latency with cold caches. Each query's cold misses
//              serialize behind the previous query's return. Usually
//              the worst of the four for any variant.
//
// Gap is host-selected: gap=32 on Intel/Graviton/Pi 5, gap=64 on M4 Max.
// The outer spine is built with the same gap as the inner variant. Set
// -DQUADSEARCH_ARM_PI5 or -DQUADSEARCH_ARM_GV4 on ARM to link the Pi 5
// or Graviton 4 variant; default ARM build links the M4 variant.

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
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
  #error "Unsupported architecture for bench_twolevel"
#endif

// Lemire's reference simd_quad (gap=16, 2x 128-bit SIMD block check).
// Included as a bare function body -- same as in bench.cpp. The arch
// headers above bring NEON / SSE2 intrinsics into scope.
#include "simd_quad.c"

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

// LLC-thrash scratch: written to before each cold-mode measurement so
// the caches are actually cold regardless of which mode ran before.
// Sized larger than any LLC on the target list: Emerald Rapids 8559C has
// a 260 MB L3 (top EMR SKUs 320 MB), so the previous 256 MB did not
// guarantee eviction there. 512 MB covers every current single-socket L3.
// The sweep also flushes the TLBs, so cold queries pay page walks too.
// -DQUADSEARCH_THRASH_BYTES='(1ull<<20)' shrinks the flush for a functional
// check (the same override bench.cpp has); a build with a non-default size
// prints a "# thrash_bytes:" line so its output can never pass for a
// campaign run. The default is the 512 MB every archived run used.
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

// Container descriptor. 48 bytes in a 16-byte-aligned std::vector, so one in
// four descriptors straddles two cache lines with the spine's data pointer
// (offset 24) on the second line while carr (offsets 0..15) is on the first:
// the spine-inner variants (A-F, H, I) read that extra descriptor line in
// one of four lookups, G and Lem (carr only) never do. Every archived
// campaign (2026-05-18 and the repaired-harness twolevel_v2 runs of
// 2026-10-11) was measured that way. The descriptor-layout A/B of 2026-10-12
// on the sweep harness (same descriptor, 48 B vs line-aligned, 14 sizes x
// 5 runs; pi5_runs/desc_layout_ab_compare.txt) found no resolvable bias --
// the two descriptor loads are independent and overlap; the spine-vs-Lemire
// contrasts moved by +1 to +6 ns hot, inside noise -- so the archived
// contrasts stand. Building with -DQUADSEARCH_DESCRIPTOR_ALIGN=64 pads and
// aligns the descriptor to one line so every variant reads exactly one
// descriptor line (hygiene, used for new hosts from 2026-10-12 on); the
// harness header records desc_align so runs of the two layouts are never
// pooled.
#ifndef QUADSEARCH_DESCRIPTOR_ALIGN
#define QUADSEARCH_DESCRIPTOR_ALIGN 16
#endif
#ifdef QUADSEARCH_TWOLEVEL_ALIGNED
// Aligned-layout A/B (2026-10-13). -DQUADSEARCH_TWOLEVEL_ALIGNED=<bytes> gives
// every container a copy of carr and of spine aligned to <bytes> (64 = one
// line on the gap-32 hosts, 128 on Apple), size rounded up to the alignment,
// and six twin variants Aa..Fa = A..F with the inner kernel reading the copies
// instead of the std::vector arrays. The copies are allocated in a second
// pass after every set and its targets exist (make_aligned_copies), so the
// plain arrays keep the heap layout the archived runs measured -- allocating
// them between the vectors moves the plain arrays' line offsets (review of
// 2026-10-12, bench_ab_pi5.cpp). A "# layout:" line records the residue
// mod 64 of the plain pointers and of the copies. Without the macro nothing
// changes: same struct, same ten variants, same output byte for byte.
static constexpr size_t kAlignedTwins = QUADSEARCH_TWOLEVEL_ALIGNED;
static_assert(kAlignedTwins >= 16 && (kAlignedTwins & (kAlignedTwins - 1)) == 0,
              "QUADSEARCH_TWOLEVEL_ALIGNED must be a power of two >= 16");
#if QUADSEARCH_DESCRIPTOR_ALIGN != 64
#warning "aligned twins without -DQUADSEARCH_DESCRIPTOR_ALIGN=64: the 64-byte descriptor straddles two lines in three of four containers"
#endif
struct FreeDeleter {
    void operator()(void *p) const { std::free(p); }
};
using AlignedBuf = std::unique_ptr<uint16_t, FreeDeleter>;
// Copy of v at kAlignedTwins alignment, size rounded up to the alignment
// (aligned_alloc needs a multiple of it; the padding is zero-filled and never
// read, every variant takes the cardinality from the plain vector). Exits on
// failure, as bench_ab_pi5.cpp does.
static AlignedBuf aligned_copy(const std::vector<uint16_t> &v) {
    if (v.empty()) return AlignedBuf();
    size_t bytes = v.size() * sizeof(uint16_t);
    size_t rounded = (bytes + kAlignedTwins - 1) / kAlignedTwins * kAlignedTwins;
    void *p = std::aligned_alloc(kAlignedTwins, rounded);
    if (!p) {
        std::fprintf(stderr, "aligned_alloc(%zu, %zu) failed\n", kAlignedTwins, rounded);
        std::exit(1);
    }
    if (((uintptr_t)p & (kAlignedTwins - 1)) != 0) {
        std::fprintf(stderr, "aligned_alloc returned a misaligned pointer\n");
        std::exit(1);
    }
    std::memset(p, 0, rounded);
    std::memcpy(p, v.data(), bytes);
    return AlignedBuf((uint16_t *)p);
}
#endif
struct alignas(QUADSEARCH_DESCRIPTOR_ALIGN) Container {
    std::vector<uint16_t> carr;
    std::vector<uint16_t> spine;
#ifdef QUADSEARCH_TWOLEVEL_ALIGNED
    AlignedBuf carr_al;    // kAlignedTwins-aligned copy of carr (read by Aa..Fa)
    AlignedBuf spine_al;   // kAlignedTwins-aligned copy of spine (read by Aa..Fa)
#endif
};
#if defined(QUADSEARCH_TWOLEVEL_ALIGNED) && QUADSEARCH_DESCRIPTOR_ALIGN == 64
static_assert(sizeof(Container) == 64, "descriptor must stay one 64-byte line: 24 + 24 + 8 + 8");
#endif

// A Roaring-style container set: parallel arrays of keys (high16) and
// containers, sorted by key.
struct ContainerSet {
    std::vector<uint16_t> keys;            // outer keys, sorted
    std::vector<uint16_t> keys_spine;      // spine over `keys` (for B/D)
    std::vector<uint16_t> keys_eytz;       // Eytzinger BFS layout (for H/I); slot 0 unused, trailing pad guards prefetch
    size_t                eytz_off = 0;    // element offset of slot 0 inside keys_eytz (cache-line aligned)
    std::vector<uint16_t> eytz_to_sorted;  // BFS slot -> original sorted index
    std::vector<Container> containers;     // containers[i] matches keys[i]
};

static std::vector<uint16_t> make_sorted_u16(std::mt19937 &rng, int n) {
    std::set<uint16_t> s;
    std::uniform_int_distribution<int> d(0, 65535);
    while ((int)s.size() < n) s.insert((uint16_t)d(rng));
    return std::vector<uint16_t>(s.begin(), s.end());
}

// Recursive sorted -> BFS conversion. k is the 1-based BFS slot (root at 1,
// children at 2k and 2k+1); i tracks the next unconsumed sorted index.
// Writes both the BFS-order keys (out) and the BFS-slot -> sorted-index
// inverse permutation (perm) in one pass.
static int build_eytzinger_rec(const uint16_t *sorted, int n,
                               uint16_t *out, uint16_t *perm,
                               int k, int i) {
    if (k > n) return i;
    i = build_eytzinger_rec(sorted, n, out, perm, 2*k, i);
    out[k]  = sorted[i];
    perm[k] = (uint16_t)i;
    i++;
    i = build_eytzinger_rec(sorted, n, out, perm, 2*k + 1, i);
    return i;
}
static void build_eytzinger(const uint16_t *sorted, int n,
                            uint16_t *out, uint16_t *perm) {
    out[0] = 0;
    perm[0] = 0;
    build_eytzinger_rec(sorted, n, out, perm, 1, 0);
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
    // Eytzinger layout for variants H, I (1-based: root at slot 1, children
    // 2k / 2k+1). Two layout requirements make the Khuong & Morin prefetch
    // work as designed:
    //  * slot 0 must start a cache line, so that node i's kGap descendants
    //    log2(kGap) levels down, slots [kGap*i, kGap*i + kGap - 1], occupy
    //    exactly one line. std::vector only guarantees 16-B alignment, so
    //    we over-allocate by one line and record the element offset.
    //  * the array must extend past the furthest prefetch address,
    //    kGap*i + kGap/2 for i up to num_containers, so that no prefetch
    //    leaves the allocation (paper section 5.3: out-of-bounds prefetches
    //    are slow on some CPUs). That is kGap*(num_containers+1) zero slots
    //    of pad; the pre-2026-10 pad of kGap*16 covered <1/15 of the reach.
    {
        const size_t line_elems = (size_t)kGap;    // kGap u16 = one cache line
        const size_t slots = (size_t)num_containers + 1
                           + (size_t)kGap * ((size_t)num_containers + 1);
        s.keys_eytz.assign(slots + line_elems, 0);
        const uintptr_t line_bytes = line_elems * sizeof(uint16_t);
        const uintptr_t p = (uintptr_t)s.keys_eytz.data();
        s.eytz_off = (size_t)(((line_bytes - (p % line_bytes)) % line_bytes)
                              / sizeof(uint16_t));
    }
    s.eytz_to_sorted.assign((size_t)num_containers + 1, 0);
    build_eytzinger(s.keys.data(), num_containers,
                    s.keys_eytz.data() + s.eytz_off, s.eytz_to_sorted.data());
    return s;
}

#ifdef QUADSEARCH_TWOLEVEL_ALIGNED
// Second pass for the aligned twins: copies of every carr and spine, made
// after all sets and targets exist so the plain arrays keep the heap layout
// of the archived runs. Each copy is checked byte for byte against its
// source. Prints the "# layout:" line: residue mod 64 (0/16/32/48) of the
// plain carr pointers, the plain spine pointers and the copies (carr_al and
// spine_al together), and how many sets' descriptor arrays start on a
// 64-byte line (all of them with -DQUADSEARCH_DESCRIPTOR_ALIGN=64).
static void make_aligned_copies(std::vector<ContainerSet> &sets) {
    unsigned hc[4] = {0, 0, 0, 0}, hs[4] = {0, 0, 0, 0}, ha[4] = {0, 0, 0, 0};
    size_t desc_lined = 0;
    for (auto &s : sets) {
        if (((uintptr_t)s.containers.data() & 63u) == 0) desc_lined++;
        for (auto &c : s.containers) {
            c.carr_al = aligned_copy(c.carr);
            c.spine_al = aligned_copy(c.spine);
            if ((!c.carr.empty() &&
                 std::memcmp(c.carr_al.get(), c.carr.data(), c.carr.size() * sizeof(uint16_t)) != 0) ||
                (!c.spine.empty() &&
                 std::memcmp(c.spine_al.get(), c.spine.data(), c.spine.size() * sizeof(uint16_t)) != 0)) {
                std::fprintf(stderr, "aligned copy differs from its source\n");
                std::exit(1);
            }
            hc[((uintptr_t)c.carr.data() >> 4) & 3u]++;
            if (!c.spine.empty()) hs[((uintptr_t)c.spine.data() >> 4) & 3u]++;
            if (c.carr_al) ha[((uintptr_t)c.carr_al.get() >> 4) & 3u]++;
            if (c.spine_al) ha[((uintptr_t)c.spine_al.get() >> 4) & 3u]++;
        }
    }
    std::printf("# layout: plain carr residue mod 64 (0/16/32/48) %u/%u/%u/%u; plain spine %u/%u/%u/%u; "
                "aligned copies (carr_al+spine_al, %zu-B) %u/%u/%u/%u; descriptors %zu B, "
                "%zu/%zu sets with a line-aligned descriptor array\n",
                hc[0], hc[1], hc[2], hc[3], hs[0], hs[1], hs[2], hs[3],
                kAlignedTwins, ha[0], ha[1], ha[2], ha[3],
                sizeof(Container), desc_lined, sets.size());
}
#endif

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

// Shar inner for n=4096. Same cmov-chain shape as the outer Shar, but over
// the 4096-element container directly (no spine). Pure membership (bool),
// not index lookup. n=4096 is already 2^12 so no bit_floor fixup needed.
//
// Expected weakness vs the shipping spine inner: 12 iters of data-dependent
// loads on a 8 KB working set, with addresses that jump around rather than
// streaming forward. The spine inner's 128-entry sequential descent is much
// more streamer-friendly.
static inline bool inner_shar_4096(const uint16_t *carr, uint16_t pos) {
    enum { n = 4096 };
    const uint16_t *begin = carr;
    for (int step = n >> 1; step != 0; step >>= 1) {
        if (begin[step] < pos) begin += step;
    }
    const uint16_t *lo = begin + (*begin < pos);
    if (lo < carr + n) return *lo == pos;
    return false;
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

// Eytzinger branch-free search with explicit prefetch (Khuong & Morin 2017,
// Listing 6 + index recovery from Listings 4-5), adapted to this harness's
// 1-based layout (root at slot 1, children 2i / 2i+1; the paper's listing is
// 0-based with children 2i+1 / 2i+2).
//
// At each step we prefetch the cache line holding node i's descendants
// log2(kGap) levels down (5 levels at gap 32, 6 at gap 64): slots
// [kGap*i, kGap*i + kGap - 1], exactly one line because make_set aligns
// slot 0 to a line. kPrefOff points at the middle of that line.
//
// NOTE: the paper's constant (3B/2 - 1) belongs to its 0-based layout,
// where the descendants are [B*i + B - 1, B*i + 2B - 2]. Applied to a
// 1-based layout it prefetches node i+1's line instead, so no prefetch ever
// covered a node on the search path. Every H/I number recorded before
// 2026-10-11 was measured with that mis-aimed prefetch; see KhuongMorin.md.
// The K=512 descent is 10 levels deep; the first 10 - log2(kGap) prefetches
// target real nodes, the remainder land in the zero pad (wasted bandwidth,
// as in the paper, in exchange for a branch-free loop).
//
// Index recovery: the loop terminates with i > n, where i's path-encoding
// has trailing 1-bits for each consecutive "go-right" step taken from the
// answer. Stripping those (i >>= ffs(~i)) yields the BFS slot of the answer
// node, or 0 when the key exceeded every node. eytz_to_sorted[] inverts the
// BFS layout back to the sorted-index that c.containers[] expects.
static inline int find_container_eytz_pf(const ContainerSet &s,
                                         uint16_t key) {
    constexpr int kPrefMul = kGap;         // u16 per cache line
    constexpr int kPrefOff = kGap / 2;     // middle of node i's descendant line (1-based layout)
    int n = (int)s.keys.size();
    if (n == 0) return -1;
    const uint16_t *a = s.keys_eytz.data() + s.eytz_off;
    int i = 1;
    while (i <= n) {
        __builtin_prefetch(a + kPrefMul * i + kPrefOff);
        i = (key <= a[i]) ? (2 * i) : (2 * i + 1);
    }
    i >>= __builtin_ffs(~i);
    if (i == 0) return -1;
    int sorted_idx = s.eytz_to_sorted[i];
    return (s.keys[sorted_idx] == key) ? sorted_idx : -1;
}

// Lookup paths.
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
static bool lookup_G(const ContainerSet &s, uint32_t v) {
    int idx = find_container_shar(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return inner_shar_4096(c.carr.data(), (uint16_t)v);
}
static bool lookup_H(const ContainerSet &s, uint32_t v) {
    int idx = find_container_eytz_pf(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return inner_spine(c.carr.data(), c.spine.data(),
                       (int32_t)c.carr.size(), (uint16_t)v);
}
static bool lookup_I(const ContainerSet &s, uint32_t v) {
    int idx = find_container_eytz_pf(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return inner_spine_4096(c.carr.data(), c.spine.data(), (uint16_t)v);
}
// Lemire reference: bsearch outer + Lemire's simd_quad inner (no spine,
// gap=16, 2x 128-bit block check on NEON/SSE2). Intended as the fair
// reference for comparing our tuning stack (F = Shar outer + compile-
// time n=4096 spine inner) against the published research baseline.
// Note the outer is the same as A (std::binary_search over keys), which
// is what CRoaring ships today.
static bool lookup_Lemire(const ContainerSet &s, uint32_t v) {
    int idx = find_container_bsearch(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return simd_quad(c.carr.data(), (int32_t)c.carr.size(), (uint16_t)v);
}

#ifdef QUADSEARCH_TWOLEVEL_ALIGNED
// Aligned twins: the outer search of A..F unchanged, the inner kernel on the
// aligned copies. The cardinality still comes from the plain vector (its
// begin/end pointers share the descriptor with the copy pointers; with
// -DQUADSEARCH_DESCRIPTOR_ALIGN=64 the whole descriptor is one line), so
// the only difference from the plain variant is the address of the array
// and spine lines the kernel reads.
static bool lookup_Aa(const ContainerSet &s, uint32_t v) {
    int idx = find_container_bsearch(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return inner_spine(c.carr_al.get(), c.spine_al.get(),
                       (int32_t)c.carr.size(), (uint16_t)v);
}
static bool lookup_Ba(const ContainerSet &s, uint32_t v) {
    int idx = find_container_spine(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return inner_spine(c.carr_al.get(), c.spine_al.get(),
                       (int32_t)c.carr.size(), (uint16_t)v);
}
static bool lookup_Ca(const ContainerSet &s, uint32_t v) {
    int idx = find_container_bsearch(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return inner_spine_4096(c.carr_al.get(), c.spine_al.get(), (uint16_t)v);
}
static bool lookup_Da(const ContainerSet &s, uint32_t v) {
    int idx = find_container_spine(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return inner_spine_4096(c.carr_al.get(), c.spine_al.get(), (uint16_t)v);
}
static bool lookup_Ea(const ContainerSet &s, uint32_t v) {
    int idx = find_container_shar(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return inner_spine(c.carr_al.get(), c.spine_al.get(),
                       (int32_t)c.carr.size(), (uint16_t)v);
}
static bool lookup_Fa(const ContainerSet &s, uint32_t v) {
    int idx = find_container_shar(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const auto &c = s.containers[idx];
    return inner_spine_4096(c.carr_al.get(), c.spine_al.get(), (uint16_t)v);
}
#endif

// Hot + batched: reuse the same set for hot_reps independent queries.
// Queries are independent (no dep chain between them), so the OoO engine
// can keep several in flight. Measures throughput with a hot *outer*:
// the 1 KB key array (plus its spine / Eytzinger copy) is reused on every
// rep, but the ~100 crafted hits per set land in ~91 distinct containers,
// so most inner spine/block loads are first touches within the pass.
// Across variants the same sets and targets are replayed, so a variant
// finds in cache whatever the previous variant's pass left there -- which
// at 200 sets (~7 MB touched per pass) is nothing on Pi 5 / SKX and most
// of it on Apple / EMR / GV4. See the header; measured on Pi 5: F hot_bat
// 61 ns at 12 sets vs 213 ns at 200 sets.
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

// Hot + serial: same hot-caches regime, but each query's target depends
// on the previous query's return via a low-bit XOR. The CPU cannot start
// query r+1 until query r retires, so the per-query critical path is
// exposed without MLP / ILP hiding. The bit-flip is one bit of a 32-bit
// key, so the outer-hit rate stays ~50% and the measured path remains
// "outer + inner" end-to-end.
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

// Cold + batched: one query per set, sweeping across num_sets in
// sequence. Each set is ~4 MB of container data, so successive queries
// miss L2 (and usually LLC) on the way. Queries are independent across
// sets, so the OoO engine can have several DRAM misses in flight at
// once. Measures throughput under cold caches.
//
// Uses targets[si][1]: targets[k] with k odd is a crafted hit, so we
// exercise outer-search + inner-search end-to-end. Index 0 is a random
// u32 that almost always misses the outer keys (~1% hit rate), which
// would hide the inner cost entirely.
//
// HISTORY (2026-05-13 fix): the original 2-mode harness used
// targets[si][0] here and had no thrash_llc() between variants, so its
// "cold" numbers measured an outer miss on L2-warm keys and never ran
// the inner search. Every two-level cold number dated before 2026-05-13
// (README "~12.9x cold", presentation, Show HN draft, reproduce.sh
// baselines) comes from that harness and is not comparable to anything
// this file produces.
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

// Cold + serial: one query per set, but each query's target depends on
// the previous query's return. With only num_sets=200 iterations and a
// dep chain between them, the DRAM misses serialize completely: each
// query pays full cold-miss latency before the next can start.
// Typically the worst ns/q of the four modes.
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
    int num_sets   = (argc > 1) ? std::atoi(argv[1]) : 200;
    int hot_reps   = (argc > 2) ? std::atoi(argv[2]) : 200;
    // Optional mode filter: "hb" / "hs" / "cb" / "cs" / "all" (default).
    // Restricting to one mode lets a fresh process measure truly cold
    // caches (via `./bench_twolevel N R cb` etc.), since once any mode
    // has swept the data the LLC/TLB state is no longer pristine for
    // the other cold modes.
    const char *mode = (argc > 3) ? argv[3] : "all";
    // Optional timing-order seed (argv[4]). 0 or absent = canonical A..Lem
    // order; anything else shuffles the order in which variants are timed
    // within each mode pass (rows are still printed in canonical order).
    unsigned order_seed = (argc > 4) ? (unsigned)std::strtoul(argv[4], nullptr, 10) : 0u;

    constexpr int num_containers = 512;
    constexpr int inner_n        = 4096;

    std::printf("two-level spine micro-bench\n");
    std::printf("num_sets=%d hot_reps=%d num_containers=%d inner_n=%d mode=%s order_seed=%u gap=%d desc_align=%d desc_size=%zu",
                num_sets, hot_reps, num_containers, inner_n, mode, order_seed, kGap,
                (int)QUADSEARCH_DESCRIPTOR_ALIGN, sizeof(Container));
#ifdef QUADSEARCH_TWOLEVEL_ALIGNED
    std::printf(" aligned_twins=%zu", kAlignedTwins);
#endif
    std::printf("\n");
    std::printf("per set: %d B of keys + %d B of container data + %d B of spines\n",
                num_containers * 2,
                num_containers * inner_n * 2,
                num_containers * (inner_n / kGap) * 2);
    if (kThrashBytes != 512ull * 1024ull * 1024ull) {
        std::printf("# thrash_bytes: %zu (NOT the 512 MB campaign flush: functional check only)\n",
                    kThrashBytes);
    }

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
#ifdef QUADSEARCH_TWOLEVEL_ALIGNED
    // Second pass, after every set and its targets: the aligned copies.
    make_aligned_copies(sets);
#endif

    // Correctness spot-check: every lookup must agree on a sample of
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
            bool rG = lookup_G(sets[si], t);
            bool rH = lookup_H(sets[si], t);
            bool rI = lookup_I(sets[si], t);
            bool rL = lookup_Lemire(sets[si], t);
            if (rA != rB || rA != rC || rA != rD || rA != rE
                || rA != rF || rA != rG || rA != rH || rA != rI || rA != rL) {
                std::fprintf(stderr,
                             "MISMATCH set=%d t=%u "
                             "A=%d B=%d C=%d D=%d E=%d F=%d G=%d H=%d I=%d Lem=%d\n",
                             si, t, rA, rB, rC, rD, rE, rF, rG, rH, rI, rL);
                return 1;
            }
#ifdef QUADSEARCH_TWOLEVEL_ALIGNED
            bool rAa = lookup_Aa(sets[si], t);
            bool rBa = lookup_Ba(sets[si], t);
            bool rCa = lookup_Ca(sets[si], t);
            bool rDa = lookup_Da(sets[si], t);
            bool rEa = lookup_Ea(sets[si], t);
            bool rFa = lookup_Fa(sets[si], t);
            if (rA != rAa || rA != rBa || rA != rCa || rA != rDa || rA != rEa || rA != rFa) {
                std::fprintf(stderr,
                             "MISMATCH set=%d t=%u A=%d Aa=%d Ba=%d Ca=%d Da=%d Ea=%d Fa=%d\n",
                             si, t, rA, rAa, rBa, rCa, rDa, rEa, rFa);
                return 1;
            }
#endif
        }
    }
#ifdef QUADSEARCH_TWOLEVEL_ALIGNED
    // The twins read new data (the copies), so they are also cross-checked
    // against A over every target of every set, hits and misses alike.
    for (int si = 0; si < num_sets; si++) {
        for (size_t k = 0; k < targets[si].size(); k++) {
            uint32_t t = targets[si][k];
            bool rA = lookup_A(sets[si], t);
            if (lookup_Aa(sets[si], t) != rA || lookup_Ba(sets[si], t) != rA
                || lookup_Ca(sets[si], t) != rA || lookup_Da(sets[si], t) != rA
                || lookup_Ea(sets[si], t) != rA || lookup_Fa(sets[si], t) != rA) {
                std::fprintf(stderr, "MISMATCH (aligned twin vs A) set=%d k=%zu t=%u\n", si, k, t);
                return 1;
            }
        }
    }
#endif
    std::printf("correctness: ok\n\n");

    struct Row { const char *var; const char *desc;
                 double hb, hs, cb, cs; };
    // Mode selection. Each mode runs in its own pass over all variants so
    // we can place thrash_llc() precisely: before every cold measurement
    // (keeping it actually cold) and never before a hot measurement. Because
    // every cold cell is preceded by its own thrash, the order of the four
    // passes does not matter; for the strictest cold numbers run each cold
    // mode in a fresh process via the mode-filter argv[3]
    // (`./bench_twolevel N R cb`, `./bench_twolevel N R cs`).
    bool run_cs = mode[0]=='a' || (mode[0]=='c' && mode[1]=='s');
    bool run_cb = mode[0]=='a' || (mode[0]=='c' && mode[1]=='b');
    bool run_hb = mode[0]=='a' || (mode[0]=='h' && mode[1]=='b');
    bool run_hs = mode[0]=='a' || (mode[0]=='h' && mode[1]=='s');
    auto NaN = std::numeric_limits<double>::quiet_NaN();
#ifdef QUADSEARCH_TWOLEVEL_ALIGNED
    constexpr int NVAR = 16;    // A..I, Lem, then the six aligned twins Aa..Fa
    constexpr int NPLAIN = 10;  // index of the first twin; twin i pairs with result[i]
    static char twin_desc[6][64];
    for (int i = 0; i < 6; i++) {
        std::snprintf(twin_desc[i], sizeof twin_desc[i],
                      "%c with the inner kernel on %zu-B-aligned copies", 'A' + i, kAlignedTwins);
    }
#else
    constexpr int NVAR = 10;
#endif
    Row result[NVAR] = {
        {"A",   "bsearch outer + general-n spine inner",                 NaN, NaN, NaN, NaN},
        {"B",   "two-level spine + general-n spine inner",               NaN, NaN, NaN, NaN},
        {"C",   "bsearch outer + compile-time n=4096 inner",             NaN, NaN, NaN, NaN},
        {"D",   "two-level spine + compile-time n=4096 inner",           NaN, NaN, NaN, NaN},
        {"E",   "Shar branchless outer + general-n spine inner",         NaN, NaN, NaN, NaN},
        {"F",   "Shar branchless outer + compile-time n=4096 inner",     NaN, NaN, NaN, NaN},
        {"G",   "Shar outer + Shar inner (n=4096, no spine)",            NaN, NaN, NaN, NaN},
        {"H",   "Eytzinger outer + K&M PF + general-n spine inner",      NaN, NaN, NaN, NaN},
        {"I",   "Eytzinger outer + K&M PF + compile-time n=4096 inner",  NaN, NaN, NaN, NaN},
        {"Lem", "Lemire reference (bsearch outer + simd_quad inner)",    NaN, NaN, NaN, NaN},
#ifdef QUADSEARCH_TWOLEVEL_ALIGNED
        {"Aa",  twin_desc[0], NaN, NaN, NaN, NaN},
        {"Ba",  twin_desc[1], NaN, NaN, NaN, NaN},
        {"Ca",  twin_desc[2], NaN, NaN, NaN, NaN},
        {"Da",  twin_desc[3], NaN, NaN, NaN, NaN},
        {"Ea",  twin_desc[4], NaN, NaN, NaN, NaN},
        {"Fa",  twin_desc[5], NaN, NaN, NaN, NaN},
#endif
    };
    auto lookups = std::array<bool(*)(const ContainerSet&, uint32_t), NVAR>{
        lookup_A, lookup_B, lookup_C, lookup_D,
        lookup_E, lookup_F, lookup_G, lookup_H, lookup_I, lookup_Lemire,
#ifdef QUADSEARCH_TWOLEVEL_ALIGNED
        lookup_Aa, lookup_Ba, lookup_Ca, lookup_Da, lookup_Ea, lookup_Fa,
#endif
    };
    // Per-pass timing order: canonical, or shuffled from order_seed (with a
    // per-mode salt so the four passes get different orders).
    auto make_order = [&](unsigned salt) {
        std::array<int, NVAR> ord{};
        for (int i = 0; i < NVAR; i++) ord[i] = i;
        if (order_seed != 0) {
            std::mt19937 g(order_seed * 1000003u + salt);
            std::shuffle(ord.begin(), ord.end(), g);
        }
        return ord;
    };
    auto print_order = [&](const char *m, const std::array<int, NVAR> &ord) {
        std::printf("timing order %s:", m);
        for (int i : ord) std::printf(" %s", result[i].var);
        std::printf("\n");
    };
    // Untimed warm-up before the hot passes. Without it the first variant
    // timed pays every first-touch TLB / cache miss for the whole working
    // set and all "vs A" hot deltas inherit the bias (A was always first).
    if (run_hb || run_hs) {
        (void)bench_hot_batched(sets, targets, hot_reps, lookup_A);
#ifdef QUADSEARCH_TWOLEVEL_ALIGNED
        // The copies get the same single first touch the plain arrays got
        // (any twin would do; all six read the same copies).
        (void)bench_hot_batched(sets, targets, hot_reps, lookup_Fa);
#endif
    }
    if (run_hb) {
        auto ord = make_order(1);
        print_order("hot_bat", ord);
        for (int i : ord)
            result[i].hb = bench_hot_batched(sets, targets, hot_reps, lookups[i]);
    }
    if (run_hs) {
        auto ord = make_order(2);
        print_order("hot_ser", ord);
        for (int i : ord)
            result[i].hs = bench_hot_serial(sets, targets, hot_reps, lookups[i]);
    }
    if (run_cb) {
        auto ord = make_order(3);
        print_order("cold_bat", ord);
        for (int i : ord) {
            thrash_llc();
            result[i].cb = bench_cold_batched(sets, targets, lookups[i]);
        }
    }
    if (run_cs) {
        auto ord = make_order(4);
        print_order("cold_ser", ord);
        for (int i : ord) {
            thrash_llc();
            result[i].cs = bench_cold_serial(sets, targets, lookups[i]);
        }
    }
    std::printf("\n");
    std::printf("%-4s  %-56s  %10s  %10s  %10s  %10s\n",
                "var", "description",
                "hot_bat", "hot_ser", "cold_bat", "cold_ser");
    std::printf("----  --------------------------------------------------------  ----------  ----------  ----------  ----------\n");
    for (auto &r : result) {
        std::printf("%-4s  %-56s  %10.2f  %10.2f  %10.2f  %10.2f\n",
                    r.var, r.desc, r.hb, r.hs, r.cb, r.cs);
    }

    auto &rA = result[0]; auto &rD = result[3];
    auto &rF = result[5]; auto &rG = result[6];
    auto &rH = result[7]; auto &rI = result[8];
    auto &rLem = result[9];

    auto dv = [](double x, double base) { return (x / base - 1) * 100; };

    // These per-run paired deltas are the numbers to aggregate across runs
    // (median of per-run deltas + sign count), NOT ratios of per-variant
    // medians: whole runs drift 1.4-2.2x on some hosts, and taking each
    // variant's median independently mixes runs. See compute_twolevel_paired.py.
    std::printf("\ndeltas vs A (hot_bat  hot_ser  cold_bat  cold_ser):\n");
    for (int i = 1; i < NVAR; i++) {
        auto &r = result[i];
        std::printf("  %-3s vs A:  %+7.1f%%  %+7.1f%%  %+7.1f%%  %+7.1f%%\n",
                    r.var,
                    dv(r.hb, rA.hb), dv(r.hs, rA.hs),
                    dv(r.cb, rA.cb), dv(r.cs, rA.cs));
    }

    std::printf("\ndeltas vs D (outer spine + n=4096 inner):\n");
    for (int i : {4, 5, 6}) {
        auto &r = result[i];
        std::printf("  %-3s vs D:  %+7.1f%%  %+7.1f%%  %+7.1f%%  %+7.1f%%\n",
                    r.var,
                    dv(r.hb, rD.hb), dv(r.hs, rD.hs),
                    dv(r.cb, rD.cb), dv(r.cs, rD.cs));
    }

    std::printf("\ndeltas vs F (Shar outer + n=4096 inner, ship recommendation):\n");
    std::printf("  G   vs F:  %+7.1f%%  %+7.1f%%  %+7.1f%%  %+7.1f%%\n",
                dv(rG.hb, rF.hb), dv(rG.hs, rF.hs),
                dv(rG.cb, rF.cb), dv(rG.cs, rF.cs));
    std::printf("  H   vs F:  %+7.1f%%  %+7.1f%%  %+7.1f%%  %+7.1f%%\n",
                dv(rH.hb, rF.hb), dv(rH.hs, rF.hs),
                dv(rH.cb, rF.cb), dv(rH.cs, rF.cs));
    std::printf("  I   vs F:  %+7.1f%%  %+7.1f%%  %+7.1f%%  %+7.1f%%\n",
                dv(rI.hb, rF.hb), dv(rI.hs, rF.hs),
                dv(rI.cb, rF.cb), dv(rI.cs, rF.cs));

    std::printf("\ndeltas vs Lemire reference "
                "(how much our stack improves on the published baseline):\n");
    std::printf("  A   vs Lem: %+7.1f%%  %+7.1f%%  %+7.1f%%  %+7.1f%%\n",
                dv(rA.hb, rLem.hb), dv(rA.hs, rLem.hs),
                dv(rA.cb, rLem.cb), dv(rA.cs, rLem.cs));
    std::printf("  D   vs Lem: %+7.1f%%  %+7.1f%%  %+7.1f%%  %+7.1f%%\n",
                dv(rD.hb, rLem.hb), dv(rD.hs, rLem.hs),
                dv(rD.cb, rLem.cb), dv(rD.cs, rLem.cs));
    std::printf("  F   vs Lem: %+7.1f%%  %+7.1f%%  %+7.1f%%  %+7.1f%%\n",
                dv(rF.hb, rLem.hb), dv(rF.hs, rLem.hs),
                dv(rF.cb, rLem.cb), dv(rF.cs, rLem.cs));

#ifdef QUADSEARCH_TWOLEVEL_ALIGNED
    std::printf("\ndeltas of the aligned twins vs their plain variant "
                "(Xa vs X: the alignment A/B, same outer, same kernel):\n");
    for (int i = 0; i < NVAR - NPLAIN; i++) {
        auto &r = result[NPLAIN + i];
        auto &b = result[i];
        std::printf("  %-3s vs %-3s: %+7.1f%%  %+7.1f%%  %+7.1f%%  %+7.1f%%\n",
                    r.var, b.var,
                    dv(r.hb, b.hb), dv(r.hs, b.hs),
                    dv(r.cb, b.cb), dv(r.cs, b.cs));
    }
#endif
    return 0;
}

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
// Run: ./bench_twolevel [num_sets] [hot_reps]
//   Defaults: num_sets=200, hot_reps=200. Each "set" is 512 containers
//   of cardinality 4096 -- ~4 MB of keys per set, large enough to blow
//   out L2.
//
// Four measurement modes, crossing two axes:
//   axis 1: cache state.  hot = same set reused for hot_reps queries,
//                                so after the first few reps the keys /
//                                containers / spines are in L1/L2.
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
//              independent DRAM misses can be in flight, so ns/q can
//              actually be *lower* than hot_bat on hosts where the hot
//              path is bottlenecked on a downclocked scalar loop
//              (e.g. Skylake-SP with AVX-512 license L2).
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
#include <limits>
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
// Sized larger than any expected LLC (host LLCs top out around 100 MB
// on Xeon; 256 MB evicts even multi-socket shared L3s).
static constexpr size_t kThrashBytes = 256u * 1024u * 1024u;
static void thrash_llc() {
    static std::vector<uint8_t> scratch;
    if (scratch.empty()) scratch.assign(kThrashBytes, 0);
    // Stride-64 write touches every line. volatile pointer prevents the
    // compiler from eliding the stores.
    volatile uint8_t *p = scratch.data();
    for (size_t i = 0; i < kThrashBytes; i += 64) p[i] = (uint8_t)i;
}

struct Container {
    std::vector<uint16_t> carr;
    std::vector<uint16_t> spine;
};

// A Roaring-style container set: parallel arrays of keys (high16) and
// containers, sorted by key.
struct ContainerSet {
    std::vector<uint16_t> keys;            // outer keys, sorted
    std::vector<uint16_t> keys_spine;      // spine over `keys` (for B/D)
    std::vector<uint16_t> keys_eytz;       // Eytzinger BFS layout (for H/I); slot 0 unused, trailing pad guards prefetch
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
    // Eytzinger layout for variants H, I. Pad past the worst-case prefetch
    // reach so out-of-bounds prefetches stay inside our allocation
    // (Khuong & Morin 2017 §5.3 portability hazard on some Intel CPUs).
    int eytz_pad = kGap * 16;
    s.keys_eytz.assign((size_t)num_containers + 1 + eytz_pad, 0);
    s.eytz_to_sorted.assign((size_t)num_containers + 1, 0);
    build_eytzinger(s.keys.data(), num_containers,
                    s.keys_eytz.data(), s.eytz_to_sorted.data());
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
// Listing 6 + index recovery from Listings 4-5). At each step the prefetch
// fetches the great-great-grandchild block of the current node; on a 9-level
// descent this keeps ~4 cache lines in flight at once, exploiting MLP
// where the K=512 outer is too short for hardware streamers to help.
//
// Index recovery: the loop terminates with i > n, where i's path-encoding
// has trailing 1-bits for each consecutive "go-right" step taken from the
// answer. Stripping those (i >>= ffs(~i)) yields the BFS slot of the answer
// node, or 0 when the key exceeded every node. eytz_to_sorted[] inverts the
// BFS layout back to the sorted-index that c.containers[] expects.
static inline int find_container_eytz_pf(const ContainerSet &s,
                                         uint16_t key) {
    constexpr int kPrefMul = kGap;                  // u16 per cache line
    constexpr int kPrefOff = (3 * kGap / 2) - 1;    // (3B/2) - 1 in u16
    int n = (int)s.keys.size();
    if (n == 0) return -1;
    const uint16_t *a = s.keys_eytz.data();
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

// Hot + batched: reuse the same set for hot_reps independent queries.
// Queries are independent (no dep chain between them), so the OoO engine
// can keep several in flight. Measures throughput with hot caches.
// At hot_reps=200 the first rep on each set pays a cold miss, then the
// remaining ~199 reps run hot (the set's keys + spines fit in L2); the
// reported ns/q is dominated by the hot tail.
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
// would hide the inner cost entirely. See 2026-05-13 fix note in
// CLAUDE.md.
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

    constexpr int num_containers = 512;
    constexpr int inner_n        = 4096;

    std::printf("two-level spine micro-bench\n");
    std::printf("num_sets=%d hot_reps=%d num_containers=%d inner_n=%d mode=%s\n",
                num_sets, hot_reps, num_containers, inner_n, mode);
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
        }
    }
    std::printf("correctness: ok\n\n");

    struct Row { const char *var; const char *desc;
                 double hb, hs, cb, cs; };
    // Measurement order matters: a cold-cache bench is only cold on its
    // first pass. When running all four modes in one process, run both
    // cold modes before the hot modes so neither cold mode benefits
    // from the LLC being warm from the other. For strict cold numbers,
    // run each cold mode in its own process via the mode-filter argv[3]
    // (`./bench_twolevel N R cb`, `./bench_twolevel N R cs`).
    bool run_cs = mode[0]=='a' || (mode[0]=='c' && mode[1]=='s');
    bool run_cb = mode[0]=='a' || (mode[0]=='c' && mode[1]=='b');
    bool run_hb = mode[0]=='a' || (mode[0]=='h' && mode[1]=='b');
    bool run_hs = mode[0]=='a' || (mode[0]=='h' && mode[1]=='s');
    auto NaN = std::numeric_limits<double>::quiet_NaN();
    // Each mode runs in its own pass over all variants so we can place
    // thrash_llc() precisely: before every cold measurement (keeping it
    // actually cold) and never before a hot measurement (the set data
    // doesn't fit in LLC anyway, but we don't want to evict TLB / i-cache
    // / the ambient state the hot path naturally settles into).
    auto measure = [&](const char *var, const char *desc, auto fn) {
        Row r;
        r.var  = var;
        r.desc = desc;
        r.hb = r.hs = r.cb = r.cs = NaN;
        return r;
    };
    constexpr int NVAR = 10;
    Row result[NVAR] = {
        measure("A",   "bsearch outer + general-n spine inner",                  lookup_A),
        measure("B",   "two-level spine + general-n spine inner",                lookup_B),
        measure("C",   "bsearch outer + compile-time n=4096 inner",              lookup_C),
        measure("D",   "two-level spine + compile-time n=4096 inner",            lookup_D),
        measure("E",   "Shar branchless outer + general-n spine inner",          lookup_E),
        measure("F",   "Shar branchless outer + compile-time n=4096 inner",      lookup_F),
        measure("G",   "Shar outer + Shar inner (n=4096, no spine)",             lookup_G),
        measure("H",   "Eytzinger outer + 4-deep PF + general-n spine inner",    lookup_H),
        measure("I",   "Eytzinger outer + 4-deep PF + compile-time n=4096 inner",lookup_I),
        measure("Lem", "Lemire reference (bsearch outer + simd_quad inner)",     lookup_Lemire),
    };
    auto lookups = std::array<bool(*)(const ContainerSet&, uint32_t), NVAR>{
        lookup_A, lookup_B, lookup_C, lookup_D,
        lookup_E, lookup_F, lookup_G, lookup_H, lookup_I, lookup_Lemire,
    };
    if (run_hb) {
        for (int i = 0; i < NVAR; i++)
            result[i].hb = bench_hot_batched(sets, targets, hot_reps, lookups[i]);
    }
    if (run_hs) {
        for (int i = 0; i < NVAR; i++)
            result[i].hs = bench_hot_serial(sets, targets, hot_reps, lookups[i]);
    }
    if (run_cb) {
        for (int i = 0; i < NVAR; i++) {
            thrash_llc();
            result[i].cb = bench_cold_batched(sets, targets, lookups[i]);
        }
    }
    if (run_cs) {
        for (int i = 0; i < NVAR; i++) {
            thrash_llc();
            result[i].cs = bench_cold_serial(sets, targets, lookups[i]);
        }
    }
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
    return 0;
}

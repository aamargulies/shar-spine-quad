// Layout-experiment harness for the Raspberry Pi 5 (Cortex-A76): WHY were the
// line-aligned copies of the container arrays 4-17 ns slower hot (outer-hot,
// inner first-touch) than the std::vector originals at every size from 32 up
// in the Pi 5 kernel A/B (bench_ab_pi5.cpp, variant Fa vs F;
// pi5_runs/sweep_ab1_findings.md, section 4)?
//
// Forked from bench_ab_pi5.cpp on 2026-10-13 and revised the same day after
// review: a seventh variant (Fmir, F's layout mirrored into a fresh arena), a
// residue-exact Fv2, a footprint-equal Fao, and a guard that keeps a smoke
// build out of the cold modes. Same 512-container sets and the same targets
// (same seed, same draws as the sweep_fvl2 / sweep_fvl3 / sweep_ab1
// campaigns), same Shar outer, same four modes, same warm-up (warm_all_hot()
// then warmup_hot() of the variant about to be timed), same order_seed
// shuffle, thrash, bitmap generator, header and RESULT conventions. ONE
// kernel: the shipped simd_quad_pi5_spine (simd_quad_pi5.c as it is now,
// prefetch-free), compiled as its own translation unit on the command line --
// no generated variants. The seven variants differ only in where the inner
// arrays and spines live: all seven run the same instructions over the same
// values and read exactly one descriptor line each (struct Desc); the lookup
// is one template instantiated seven times whose only difference is which
// descriptor array it indexes.
//
// Fa's copies in sweep_ab1 differed from the originals in four ways at once:
// alignment (64-byte vs the vectors' 16-byte residues), heap position (made in
// a second pass after every set and target, far from the descriptors and the
// original arrays), footprint (sizes rounded to the line, glibc's spacing of
// aligned chunks) and -- at the sizes where glibc clusters the originals'
// spines away from their arrays, see "spine placement" below -- spine
// placement. The variants separate them:
//
//   F      = the std::vector originals (as F everywhere).
//   Fa     = aligned_alloc(64, round64(bytes)) copies made in a second pass,
//            array copy then spine copy per container, in set and container
//            order: exactly today's Fa (every factor at once).
//   Fv2    = std::vector copies made in the same second pass -- glibc malloc,
//            the same chunk sizes as the originals -- steered to the SAME
//            residue mod 64 as the original, copy by copy: before a copy whose
//            predicted address has the wrong residue a kept-alive shim chunk
//            (32, 48 or 80 bytes) is taken from the heap top, and a copy that
//            glibc serves from a bin at the wrong residue is kept as padding
//            and the copy retried (steered_copy() below; its layout line
//            counts shims, misses, padding and re-syncs). Position only, with
//            glibc, every spine right after its array.
//   Fao    = like Fa but deliberately misaligned: posix_memalign(64,
//            round64(bytes) + 16) and the copy at p + 16, so every array and
//            spine sits at residue 16 mod 64 (every block straddles two lines,
//            like a typical vector). The +16 -- the first version had +64 --
//            is what makes Fao's footprint Fa's: this glibc (2.41) spaces
//            consecutive 64-byte-aligned chunks of request R and of request
//            R + 16 both R + 64 bytes apart, those of request R + 64 R + 128
//            apart (measured for R = 64..8192 before the change; the layout
//            lines show Fao's pages and stride equal to Fa's). Alignment only,
//            with position and footprint held equal to Fa.
//   Fpool  = per set ONE arena, aligned_alloc(16384, total), into which every
//            container's array and spine copy is packed sequentially in
//            container order, each copy at the next offset whose residue mod
//            64 EQUALS the residue of the original vector's data pointer, so
//            the straddling pattern is identical to F's copy by copy:
//            position only, an arena instead of glibc chunks, tightly packed,
//            every spine right after its array.
//   Fapool = the same arena packing with every copy at the next 64-byte
//            boundary and its size rounded up to 64: alignment (plus the
//            rounding) only, within the arena.
//   Fmir   = per set ONE arena, aligned_alloc(16384, span), holding a MIRROR
//            of F's layout: every array and spine copy at the same offset from
//            the arena's page-aligned base as the original has from the
//            page-aligned base of the set's first-pass heap region (verified
//            offset by offset), so residues, strides, the holes glibc left,
//            page offsets and the spines' placement relative to their arrays
//            are F's exactly; only the pages are new. Position only, in the
//            strictest sense: the one variant that holds spine placement.
//
// Contrasts: Fa vs F = everything at once (the sweep_ab1 pair); Fmir vs F =
// position with the whole intra-set layout held; Fpool vs F and Fv2 vs F =
// position with the residues held copy by copy but the data packed (arena /
// glibc chunks) and every spine next to its array; Fao vs Fa = alignment with
// position and footprint held; Fapool vs Fpool = alignment and rounding within
// the arena (pages: footprint bullet below); Fapool vs Fa = allocator (arena vs glibc) at equal
// alignment and rounding; Fmir vs Fpool = F's placement (its holes and, where
// present, its clustered spines) against tight packing at equal residues;
// Fv2 vs Fpool = glibc chunking vs arena packing at equal residues.
//
// Second-pass order: Fv2, Fa, Fao, Fpool, Fapool, Fmir -- Fv2 FIRST, before
// any aligned allocation. glibc's memalign frees the leading remainder of
// every aligned chunk into the bins (48 bytes before each 64-byte Fa copy,
// which is why Fa's tiny copies sit 128 B apart), and plain mallocs of fitting
// sizes -- every spine copy below ~1400 elements and every array copy below
// ~20 -- would be served from those holes, scattering Fv2 among Fa's copies
// instead of giving it a second-pass run of its own. With the bins holding
// only the first pass's leftovers, Fv2's chunks bump from the heap top the way
// the originals did (its shims drain the leftover chunks of the shim sizes on
// the way; its layout line counts them). Fa therefore starts after Fv2's
// region instead of right after the first pass; its allocator behaviour (the
// aligned_alloc spacing, the leading remainders) is the same as in sweep_ab1.
// The arenas come last: a heap-carved arena (total below glibc's 128 KB mmap
// threshold, i.e. small n) frees its alignment remainder into the bins too.
//
// What differs besides the factor each variant isolates -- methodology lesson
// 7 of CLAUDE.md; the '# layout:' lines print it, read them before a contrast:
//   - Footprint. Rounding to the line and glibc's spacing make the aligned
//     copies occupy more lines and pages than the originals below one block
//     (Fa and Fao: 128 B of heap per 64-byte copy; Fapool: 64 B; F and Fv2:
//     32-80 B chunks packed, Fv2 plus a shim of at most 80 B where the residue
//     needs one; Fpool: the exact bytes plus residue padding; Fmir: F's bytes
//     AND F's holes, see below). Negligible from n ~ 256, decisive below 32,
//     where sweep_ab1 already put Fa's cost on it. The layout lines give pages
//     (16 KB here) and lines. At 100 sets Fa and Fao are stride-equal at every
//     size and page-equal at 25 of the 26 (n = 56: 1002 against 1001), so Fao
//     vs Fa is the footprint-equal alignment pair; Fapool and Fpool have equal
//     pages at 15 sizes, Fapool 11-20% more at n = 40, 48, 80 and 112 (rounding
//     80-224-byte copies up to the line) and 2-4% fewer from 320 up, so below
//     one block Fapool vs Fpool carries the rounding's footprint as well.
//   - Fao is uniformly at residue 16; F is a mix of residues (its residue-0
//     containers never straddle), so Fao vs F is NOT pure position. Read Fao
//     against Fa.
//   - Fv2's residues are F's copy by copy (asserted), its strides are not:
//     F's bump run alternates with the generator's scratch (below), Fv2's is
//     array, spine, array, spine with a shim wherever the residue cycle of
//     that sequence departs from F's (two shims per container at n = 4096,
//     a handful per set where the spines are adjacent). Fpool is the arena
//     analogue; Fmir reproduces F's strides as well.
//   - Spine placement. glibc hands the originals' spines to whichever freed
//     chunk fits best, and at the sizes where the array request matches or
//     dominates the generator's freed 8 KB scratch slot the spines are carved
//     ~30 at a time out of OLDER slots, tens to hundreds of KB before their
//     arrays (F's layout line: spine_dist_med negative, spine_lines below the
//     per-spine line count), while at the other sizes array and spine are
//     carved together from one slot and are adjacent. At 100 sets F's spines
//     are clustered at n = 320, 512, 1024, 1536, 2048, 3072 and 4096 and
//     adjacent at the other 19 sizes of pi5_runs/layout1_n_list.txt (check
//     the F line of the cells: spine_dist_med). Fmir keeps F's placement;
//     Fa, Fv2, Fao, Fpool and Fapool put every spine right after its array.
//     So at the clustered sizes Fa vs F, Fv2 vs F and Fpool vs F carry the
//     spine placement as well as the factor they name, Fmir vs F does not,
//     and Fmir vs Fpool measures the placement (together with F's holes).
//   - F's own layout is shaped by the generator's scratch. make_sorted_u16
//     allocates an 8 KB bitmap (an 8208-byte chunk) before each array and
//     frees it after, and glibc hands the freed chunk to whichever request
//     fits best next: at n = 4096 the array request is exactly that size, so
//     the arrays take over the scratch slots and bump 8208 B apart (one extra
//     slot every ~30 containers) while the spines fill the older freed slots
//     ~30 per slot; at small n the array and spine of a container are carved
//     together from one freed slot (n = 32: stride 112 = 80 + 32) and a fresh
//     slot opens every few dozen containers; below one block (n <= 24, no
//     spine) a set's keys and its first 95 arrays are carved from the 4 KB
//     remainder the previous set's target vector left in that set's last
//     freed slot (1040 + 95 x 32 = 4080 bytes), so one jump per set lands the
//     96th array at the heap top, 70-170 KB further on. Fmir mirrors those
//     holes and jumps too, so its arena is larger than Fpool's by exactly F's
//     holes (mirror_fill= in its layout line is the data's share of the span;
//     7% at n = 8, 25% at 32, 90% from 1024). The same generator and
//     allocation order produced sweep_ab1's F (bench_ab_pi5.cpp); sweep_fvl2
//     used the std::set generator and had a different heap history.
//   - The arenas are mmap'd by glibc when their size is >= 128 KB and carved
//     from the brk heap below that (arena_region= in the layout line); the
//     originals are always brk-heap chunks. No THP on this Pi, 16 KB pages,
//     so the page count is the TLB footprint.
//   - Seven copies of the data are resident at once (~430 MB each at n = 4096
//     x 100 sets); each variant reads only its own during timing, and the
//     warm-up ends with the variant about to be timed, as in bench_ab_pi5.
//   - Descriptors: every variant has its own line-aligned 64-byte-per-
//     container descriptor array per set (the seven arrays in one 224 KB
//     block allocated with the set, before its vectors), and a one-line
//     SetView carries the keys pointer and the seven descriptor bases, so
//     every variant touches the same number of outer lines (SetView, keys,
//     one Desc). The seventh pointer took the line's last slot, so the key
//     count is the compile-time constant it always was (512) instead of a
//     field: the Shar outer's length is folded -- the same for every variant,
//     a few instructions less than bench_ab_pi5's outer. bench_ab_pi5 kept the
//     vectors inside a one-line Container descriptor; here F reads a {carr,
//     spine, n} descriptor like every other variant. Same traffic, a slightly
//     different first-pass heap layout: compare levels with sweep_ab1 with
//     that in mind -- the within-run pairs are what this harness is for.
//
// Bookkeeping stays off the brk heap (reserve_off_heap(), the static stdout
// buffer, the open/read THP probe), so F's first-pass layout depends on the
// per-set allocation sequence alone: the same for every num_sets and output
// destination, and unchanged by the size of the harness's own structs.
//
// Checks: every copy is compared byte for byte with the vector it copies, the
// residue invariants are asserted (Fa and Fapool 0, Fao 16, Fv2 and Fpool
// equal to the original copy by copy, Fmir at the original's offset from the
// page-aligned base), and all seven variants go through the exhaustive
// correctness check of bench_ab_pi5 (200 probes of each of the first five
// sets; for inner_n <= 128 also every element and its two neighbours).
//
// Build (from the repo root; binaries go on local disk, never on the share).
// The CAMPAIGN binary (512 MB flush before every cold variant) is the plain
// name:
//   /usr/local/bin/g++ -O3 -mcpu=cortex-a76 -std=c++20
//       -DQUADSEARCH_KERNEL_BLOB="\"$(git hash-object simd_quad_pi5.c)\""
//       bench_layout_pi5.cpp simd_quad_pi5.c -o /home/pi/build_ab/layout/bench_layout_pi5
//   (one command line; the blob define records the kernel in the header)
// A functional SMOKE build adds -DQUADSEARCH_THRASH_BYTES='(1ull<<20)' and
// MUST get another name (.../bench_layout_pi5_smoke). Such a build records
// thrash_bytes=1048576 in its '# bench_layout_pi5' header line (the field the
// aggregator prints in its harness-header summary), prints a '# thrash_bytes:'
// warning line, and REFUSES the cold modes cb/cs (exit 2) unless
// QUADSEARCH_SMOKE=1 is in the environment -- so a smoke binary started by the
// campaign driver fails every cold cell loudly instead of writing 1 MB-flush
// "cold" cells. Before a campaign check the binary: `./bench_layout_pi5 8 hb
// 1 1 0` must print thrash_bytes=536870912 in its header line and no
// '# thrash_bytes:' line; record its sha256 in FVL_NOTE.
//
// Run: ./bench_layout_pi5 <inner_n> <mode:hb|hs|cb|cs> [num_sets=200] [hot_reps=200] [order_seed=0]
//   RESULT inner_n=<N> mode=<m> F=<ns> Fa=<ns> Fv2=<ns> Fao=<ns> Fpool=<ns> Fapool=<ns> Fmir=<ns>
//   Campaign: run_sweep_f_vs_lem.sh with FVL_BIN=<the campaign binary>,
//   FVL_PREFIX=layout1 and the size list pi5_runs/layout1_n_list.txt
//   (26 sizes 8..4096), e.g.
//     FVL_BIN=/home/pi/build_ab/layout/bench_layout_pi5 FVL_PREFIX=layout1
//       FVL_NOTE="sha256 <of the binary>; kernel blob <hash>; 512 MB flush"
//       bash run_sweep_f_vs_lem.sh pi5 100 200 pi5_runs/layout1_n_list.txt
//   (one command line)
//   Aggregation: the layout1 preset of compute_sweep_fvl.py predates the
//   seventh column, so pass the pairs:
//     python3 compute_sweep_fvl.py pi5 --prefix layout1 --list pi5_runs/layout1_n_list.txt
//       --pairs Fa:F,Fmir:F,Fpool:F,Fv2:F,Fao:Fa,Fapool:Fpool,Fapool:Fa,Fmir:Fpool,Fv2:Fpool
//
// Modes and measurement are those of bench_ab_pi5.cpp / bench_sweep_f_vs_lem.cpp:
// one mode per process; hb/hs time hot_reps queries per set (outer-hot, inner
// first-touch), cb/cs one query per set after a 512 MB flush before every
// variant; the serial modes chain each query's result into the next target.

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
#include <fcntl.h>
#include <unistd.h>
#if defined(__GLIBC__)
#include <gnu/libc-version.h>
#include <malloc.h>  // malloc_usable_size, mallinfo2: the Fv2 steering reads the heap top
#else
#error "bench_layout_pi5 steers glibc's malloc (Fv2) and reports glibc's version: build it against glibc"
#endif

#if !defined(__ARM_NEON) && !defined(__aarch64__)
  #error "bench_layout_pi5 is an AArch64/NEON harness for the Pi 5 kernel"
#endif

#ifndef QUADSEARCH_KERNEL_BLOB
#define QUADSEARCH_KERNEL_BLOB "unknown"
#endif

// The shipped kernel: simd_quad_pi5.c, compiled by g++ as C++ on the same
// command line (so no extern "C"), as bench_sweep_f_vs_lem.cpp declares it.
bool simd_quad_pi5_spine(const uint16_t *carr, const uint16_t *spine,
                         int32_t cardinality, uint16_t pos);
void simd_quad_pi5_build_spine(const uint16_t *carr, int32_t cardinality,
                               uint16_t *spine);

static constexpr int kGap = 32;
static constexpr int kNumContainers = 512;
static constexpr size_t kAlign = 64;          // the Cortex-A76 line: Fa / Fapool alignment and rounding
static constexpr size_t kOffsetResidue = 16;  // Fao: every copy at this residue mod kAlign
static constexpr size_t kArenaAlign = 16384;  // Fpool / Fapool / Fmir arena alignment = this Pi's page size

enum : int { V_F = 0, V_Fa, V_Fv2, V_Fao, V_Fpool, V_Fapool, V_Fmir, kVariants };
static const char *const kNames[kVariants] = {"F", "Fa", "Fv2", "Fao", "Fpool", "Fapool", "Fmir"};

using clock_type = std::chrono::steady_clock;

// 512 MB, as in bench_sweep_f_vs_lem.cpp and bench_twolevel.cpp.
// -DQUADSEARCH_THRASH_BYTES='(1ull<<20)' shrinks it for a functional check;
// such a build is a smoke build: announced in the header, refused in the
// cold modes unless QUADSEARCH_SMOKE=1 (see main()).
static constexpr size_t kCampaignThrashBytes = 512ull * 1024ull * 1024ull;
#ifndef QUADSEARCH_THRASH_BYTES
#define QUADSEARCH_THRASH_BYTES (512ull * 1024ull * 1024ull)
#endif
static constexpr size_t kThrashBytes = QUADSEARCH_THRASH_BYTES;
static constexpr bool kSmokeBuild = (kThrashBytes != kCampaignThrashBytes);
static_assert(kThrashBytes >= 64, "QUADSEARCH_THRASH_BYTES must cover at least one cache line");
static void thrash_llc() {
    static std::vector<uint8_t> scratch;
    if (scratch.empty()) scratch.assign(kThrashBytes, 0);
    volatile uint8_t *p = scratch.data();
    for (size_t i = 0; i < kThrashBytes; i += 64) p[i] = (uint8_t)i;
}

[[noreturn]] static void die(const char *msg) {
    std::fprintf(stderr, "bench_layout_pi5: %s\n", msg);
    std::exit(1);
}

static inline size_t round_up(size_t x, size_t a) { return (x + a - 1) / a * a; }

struct FreeDeleter {
    void operator()(void *p) const { std::free(p); }
};
using AlignedBuf = std::unique_ptr<uint16_t, FreeDeleter>;

static AlignedBuf alloc_aligned(size_t align, size_t bytes) {  // bytes: a multiple of align
    void *p = std::aligned_alloc(align, bytes);
    if (!p) {
        std::fprintf(stderr, "aligned_alloc(%zu, %zu) failed\n", align, bytes);
        std::exit(1);
    }
    if (((uintptr_t)p & (align - 1)) != 0) die("aligned_alloc returned a misaligned pointer");
    return AlignedBuf((uint16_t *)p);
}

// Fa: bench_ab_pi5's aligned_copy, unchanged.
static AlignedBuf aligned_copy(const std::vector<uint16_t> &v) {
    if (v.empty()) return AlignedBuf();
    size_t bytes = v.size() * sizeof(uint16_t);
    size_t rounded = round_up(bytes, kAlign);  // aligned_alloc needs a multiple of the alignment
    AlignedBuf b = alloc_aligned(kAlign, rounded);
    std::memcpy(b.get(), v.data(), bytes);
    return b;
}

// Fao: a line-aligned chunk of round64(bytes) + kOffsetResidue, the copy at
// p + kOffsetResidue (it fits: bytes <= round64(bytes)). The request is not a
// multiple of the alignment, which C11's aligned_alloc does not allow and
// posix_memalign does (in glibc both are the same _mid_memalign). With +16,
// glibc spaces these chunks exactly as it spaces Fa's (header comment); the
// owner pointer (p) is returned, *used receives the pointer to read from.
static AlignedBuf offset_copy(const std::vector<uint16_t> &v, const uint16_t **used) {
    *used = nullptr;
    if (v.empty()) return AlignedBuf();
    size_t bytes = v.size() * sizeof(uint16_t);
    size_t request = round_up(bytes, kAlign) + kOffsetResidue;
    void *p = nullptr;
    if (posix_memalign(&p, kAlign, request) != 0 || p == nullptr) die("posix_memalign failed");
    if (((uintptr_t)p & (kAlign - 1)) != 0) die("posix_memalign returned a misaligned pointer");
    AlignedBuf b((uint16_t *)p);
    uint16_t *u = reinterpret_cast<uint16_t *>(reinterpret_cast<char *>(p) + kOffsetResidue);
    std::memcpy(u, v.data(), bytes);
    *used = u;
    return b;
}

// One container descriptor = exactly one 64-byte line, line-aligned. Every
// variant has its own array of these per set (variant-major in
// ContainerSet::descs), so a lookup of any variant reads: one SetView line,
// the keys (shared), one Desc line (its own), then the data (its own).
struct alignas(64) Desc {
    const uint16_t *carr;
    const uint16_t *spine;  // null when inner_n < kGap
    int32_t n;
};
static_assert(sizeof(Desc) == 64, "Desc must be exactly one 64-byte line");

// What the timed loops read per set: one line for every variant. The key
// count is kNumContainers (make_set asserts it), not a field: the seventh
// descriptor pointer took the line's last 8 bytes.
struct alignas(64) SetView {
    const uint16_t *keys;
    const Desc *desc[kVariants];
};
static_assert(sizeof(SetView) == 64, "SetView must be exactly one 64-byte line");

// Ownership (never touched by the timed loops).
struct ContainerStorage {
    std::vector<uint16_t> carr;     // F (the originals)
    std::vector<uint16_t> spine;    // empty when inner_n < kGap
    AlignedBuf carr_al, spine_al;   // Fa
    std::vector<uint16_t> carr_v2, spine_v2;  // Fv2
    AlignedBuf carr_ao, spine_ao;   // Fao owners (the descriptors point kOffsetResidue bytes in)
};

struct ContainerSet {
    std::vector<uint16_t> keys;
    std::vector<Desc> descs;  // kVariants * kNumContainers, variant-major
    std::vector<ContainerStorage> containers;
    AlignedBuf pool, apool, mirror;  // Fpool / Fapool / Fmir arenas
    size_t pool_bytes = 0, apool_bytes = 0;  // bytes used (the allocation is rounded up to kArenaAlign)
    size_t pool_alloc = 0, apool_alloc = 0;
    size_t mirror_span = 0, mirror_alloc = 0, mirror_packed = 0;  // Fmir: F's span (bytes used), allocation, data bytes
    uintptr_t mirror_fbase = 0;  // the page-aligned base of F's first-pass region that the arena base stands for
    const Desc *desc(int v) const { return descs.data() + (size_t)v * kNumContainers; }
    Desc *desc(int v) { return descs.data() + (size_t)v * kNumContainers; }
};

// n distinct uniform u16 values, sorted: the bitmap rejection sampler of
// bench_sweep_f_vs_lem.cpp, draw for draw, so the arrays are those of the
// sweep_fvl2 / sweep_fvl3 / sweep_ab1 campaigns at the same (inner_n, num_sets).
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

// First pass: keys, the descriptor block, then the originals (array, spine per
// container). The copies of every other variant are made in the second pass
// in main(), after every set and target exists, so the originals keep the
// heap layout of bench_sweep_f_vs_lem / bench_ab_pi5 (same reason as there:
// interleaving copies with the originals pushed almost every plain array to
// one line offset).
static ContainerSet make_set(std::mt19937 &rng, int inner_n) {
    ContainerSet s;
    s.keys = make_sorted_u16(rng, kNumContainers);
    if ((int)s.keys.size() != kNumContainers) die("a set must have exactly kNumContainers keys");
    s.descs.assign((size_t)kVariants * kNumContainers, Desc{nullptr, nullptr, 0});
    if (((uintptr_t)s.descs.data() & 63u) != 0) die("descriptor block is not line-aligned");
    s.containers.resize(kNumContainers);
    Desc *df = s.desc(V_F);
    for (int i = 0; i < kNumContainers; i++) {
        ContainerStorage &c = s.containers[i];
        c.carr = make_sorted_u16(rng, inner_n);
        int num_blocks = inner_n / kGap;
        c.spine.resize(num_blocks);
        if (num_blocks > 0) {
            simd_quad_pi5_build_spine(c.carr.data(), inner_n, c.spine.data());
        }
        df[i] = Desc{c.carr.data(), c.spine.empty() ? nullptr : c.spine.data(), inner_n};
    }
    return s;
}

// ---- second pass -----------------------------------------------------------

// Fv2: glibc copies steered to the originals' residues.
//
// glibc serves a plain malloc from the heap top -- payload = the previous top
// chunk's payload + its chunk size, chunk size = malloc_usable_size + 8 on
// this glibc -- unless a freed chunk fits (here: the first pass's leftovers,
// the generator's freed 8 KB scratch slots and their remainders). The steering
// keeps a prediction of the next top payload, puts a kept-alive shim chunk in
// front of a copy whose predicted residue is wrong (malloc(72) -> 80-byte
// chunk = +16 mod 64, malloc(24) -> 32 = +32, malloc(40) -> 48 = +48), and
// checks every result against the prediction: a shim or a copy that lands
// elsewhere was served from a bin. A bin-served shim moved the top by nothing
// and is simply followed by another (this drains the leftovers of that size);
// a bin-served copy is accepted if glibc happened to put it at the wanted
// residue and otherwise kept as padding and retried. The prediction is re-read
// from glibc whenever a check fails (mallinfo2().keepcost is the top chunk's
// size and the top chunk ends at sbrk(0)). Shims and padding live until exit;
// the layout line reports the counts.
struct Fv2Steer {
    std::vector<void *> shims;
    std::vector<std::vector<uint16_t>> padding;
    size_t padding_bytes = 0;
    unsigned shim_misses = 0, copy_retries = 0, bin_accepts = 0, resyncs = 0;
    uintptr_t pred = 0;  // predicted payload address of the next chunk carved from the heap top (0 = unknown)
    ~Fv2Steer() { for (void *p : shims) std::free(p); }
};
static Fv2Steer g_fv2;

static inline uintptr_t after_chunk(const void *payload) {
    return (uintptr_t)payload + malloc_usable_size(const_cast<void *>(payload)) + 8;
}

static uintptr_t top_payload() {  // the payload the next chunk carved from the heap top will get
    struct mallinfo2 mi = mallinfo2();
    return (uintptr_t)sbrk(0) - (uintptr_t)mi.keepcost + 16;
}

static std::vector<uint16_t> steered_copy(const std::vector<uint16_t> &src, Fv2Steer &st) {
    if (src.empty()) return {};
    const uintptr_t want = (uintptr_t)src.data() & (kAlign - 1);
    if (st.pred == 0) st.pred = top_payload();
    for (int attempt = 0; attempt < 64; attempt++) {
        for (unsigned k = 0;; k++) {
            uintptr_t delta = (want - (st.pred & (kAlign - 1))) & (kAlign - 1);
            if (delta == 0) break;
            void *sh = std::malloc(delta == 16 ? 72 : delta == 32 ? 24 : 40);
            if (!sh) die("Fv2: shim malloc failed");
            st.shims.push_back(sh);
            if ((uintptr_t)sh == st.pred) {
                st.pred = after_chunk(sh);  // from the top: it moved the top by its chunk size
            } else {
                st.shim_misses++;           // from a bin: the top is where it was
                if ((k & 63u) == 63u) { st.pred = top_payload(); st.resyncs++; }  // unless the prediction was stale
                if (k > (1u << 20)) die("Fv2: a million shims did not reach the heap top");
            }
        }
        std::vector<uint16_t> v(src);  // allocates exactly size() elements, like the original's reserve(n)
        uintptr_t p = (uintptr_t)v.data();
        if (p == st.pred) {            // from the top, hence at the wanted residue
            st.pred = after_chunk(v.data());
            return v;
        }
        st.pred = top_payload();
        st.resyncs++;
        if ((p & (kAlign - 1)) == want) {  // served from a bin, at the right residue: glibc's choice stands
            st.bin_accepts++;
            return v;
        }
        st.copy_retries++;
        st.padding_bytes += v.size() * sizeof(uint16_t);
        st.padding.push_back(std::move(v));
    }
    die("Fv2: 64 attempts did not place a copy at the original's residue");
}

static void make_copies_Fv2(std::vector<ContainerSet> &sets) {
    for (auto &s : sets) {
        Desc *d = s.desc(V_Fv2);
        for (int i = 0; i < kNumContainers; i++) {
            ContainerStorage &c = s.containers[i];
            c.carr_v2 = steered_copy(c.carr, g_fv2);
            c.spine_v2 = steered_copy(c.spine, g_fv2);  // no allocation when empty
            d[i] = Desc{c.carr_v2.data(), c.spine_v2.empty() ? nullptr : c.spine_v2.data(),
                        (int32_t)c.carr.size()};
        }
    }
}

static void make_copies_Fa(std::vector<ContainerSet> &sets) {
    for (auto &s : sets) {
        Desc *d = s.desc(V_Fa);
        for (int i = 0; i < kNumContainers; i++) {
            ContainerStorage &c = s.containers[i];
            c.carr_al = aligned_copy(c.carr);
            c.spine_al = aligned_copy(c.spine);
            d[i] = Desc{c.carr_al.get(), c.spine_al.get(), (int32_t)c.carr.size()};
        }
    }
}

static void make_copies_Fao(std::vector<ContainerSet> &sets) {
    for (auto &s : sets) {
        Desc *d = s.desc(V_Fao);
        for (int i = 0; i < kNumContainers; i++) {
            ContainerStorage &c = s.containers[i];
            const uint16_t *uc = nullptr, *us = nullptr;
            c.carr_ao = offset_copy(c.carr, &uc);
            c.spine_ao = offset_copy(c.spine, &us);
            d[i] = Desc{uc, us, (int32_t)c.carr.size()};
        }
    }
}

// Fpool (aligned == false): each copy at the next offset whose residue mod
// kAlign equals the original pointer's; Fapool (aligned == true): each copy at
// the next kAlign boundary with its size rounded up to kAlign. One arena per
// set, aligned_alloc(kArenaAlign, round_up(total, kArenaAlign)); the first
// loop is a dry run that computes the total.
static void make_pool(ContainerSet &s, bool aligned) {
    auto place = [aligned](size_t cur, size_t bytes, const void *orig, size_t *start) -> size_t {
        size_t off;
        if (aligned) {
            off = round_up(cur, kAlign);
            *start = off;
            return off + round_up(bytes, kAlign);
        }
        size_t want = (uintptr_t)orig & (kAlign - 1);
        off = cur + ((want - (cur & (kAlign - 1))) & (kAlign - 1));
        *start = off;
        return off + bytes;
    };
    size_t total = 0, scratch;
    for (int i = 0; i < kNumContainers; i++) {
        const ContainerStorage &c = s.containers[i];
        total = place(total, c.carr.size() * 2, c.carr.data(), &scratch);
        if (!c.spine.empty()) total = place(total, c.spine.size() * 2, c.spine.data(), &scratch);
    }
    size_t alloc_bytes = round_up(total, kArenaAlign);
    AlignedBuf arena = alloc_aligned(kArenaAlign, alloc_bytes);
    char *base = reinterpret_cast<char *>(arena.get());
    Desc *d = s.desc(aligned ? V_Fapool : V_Fpool);
    size_t cur = 0;
    for (int i = 0; i < kNumContainers; i++) {
        const ContainerStorage &c = s.containers[i];
        size_t off_c, off_s = 0;
        size_t cb = c.carr.size() * 2;
        cur = place(cur, cb, c.carr.data(), &off_c);
        std::memcpy(base + off_c, c.carr.data(), cb);
        const uint16_t *sp = nullptr;
        if (!c.spine.empty()) {
            size_t sb = c.spine.size() * 2;
            cur = place(cur, sb, c.spine.data(), &off_s);
            std::memcpy(base + off_s, c.spine.data(), sb);
            sp = reinterpret_cast<const uint16_t *>(base + off_s);
        }
        d[i] = Desc{reinterpret_cast<const uint16_t *>(base + off_c), sp, (int32_t)c.carr.size()};
    }
    if (cur != total) die("arena dry run and fill disagree");
    if (aligned) { s.apool = std::move(arena); s.apool_bytes = total; s.apool_alloc = alloc_bytes; }
    else         { s.pool  = std::move(arena); s.pool_bytes  = total; s.pool_alloc  = alloc_bytes; }
}

// Fmir: one arena per set holding F's layout at the same offsets. fbase is
// the page-aligned floor of the set's lowest original; the arena is
// aligned_alloc(kArenaAlign, round_up(span, kArenaAlign)) with span = the
// highest original's end - fbase, and every copy goes to arena + (original -
// fbase): page offsets, residues, strides, holes and spine placement are F's.
// A set whose originals span more than 4x their data plus 4 MB has a
// straggler that glibc served from a bin far away (another set's region); the
// span would be mirrored as is, so the harness stops and names it instead.
static void make_mirror(ContainerSet &s, int set_index) {
    uintptr_t lo = UINTPTR_MAX, hi = 0;
    size_t packed = 0;
    auto note = [&](const std::vector<uint16_t> &v) {
        if (v.empty()) return;
        uintptr_t a = (uintptr_t)v.data();
        lo = std::min(lo, a);
        hi = std::max(hi, a + v.size() * sizeof(uint16_t));
        packed += v.size() * sizeof(uint16_t);
    };
    for (int i = 0; i < kNumContainers; i++) {
        note(s.containers[i].carr);
        note(s.containers[i].spine);
    }
    uintptr_t fbase = lo & ~(uintptr_t)(kArenaAlign - 1);
    size_t span = (size_t)(hi - fbase);
    size_t cap = 4 * packed + ((size_t)4 << 20);
    if (span > cap) {
        std::vector<uintptr_t> arrays;
        for (int i = 0; i < kNumContainers; i++) arrays.push_back((uintptr_t)s.containers[i].carr.data());
        std::sort(arrays.begin(), arrays.end());
        long long med = (long long)arrays[arrays.size() / 2];
        int worst = -1; long long worst_d = 0; const char *what = "";
        for (int i = 0; i < kNumContainers; i++) {
            long long dc = (long long)(uintptr_t)s.containers[i].carr.data() - med;
            if (std::llabs(dc) > std::llabs(worst_d)) { worst_d = dc; worst = i; what = "array"; }
            if (!s.containers[i].spine.empty()) {
                long long ds = (long long)(uintptr_t)s.containers[i].spine.data() - med;
                if (std::llabs(ds) > std::llabs(worst_d)) { worst_d = ds; worst = i; what = "spine"; }
            }
        }
        std::fprintf(stderr, "bench_layout_pi5: Fmir: set %d: the originals span %zu bytes for %zu bytes of data "
                             "(cap %zu); container %d's %s lies %lld bytes from the median array -- a straggler "
                             "glibc served from a bin far away; not mirrored\n",
                     set_index, span, packed, cap, worst, what, worst_d);
        std::exit(1);
    }
    size_t alloc_bytes = round_up(span, kArenaAlign);
    AlignedBuf arena = alloc_aligned(kArenaAlign, alloc_bytes);
    char *base = reinterpret_cast<char *>(arena.get());
    Desc *d = s.desc(V_Fmir);
    for (int i = 0; i < kNumContainers; i++) {
        const ContainerStorage &c = s.containers[i];
        size_t off_c = (size_t)((uintptr_t)c.carr.data() - fbase);
        std::memcpy(base + off_c, c.carr.data(), c.carr.size() * sizeof(uint16_t));
        const uint16_t *sp = nullptr;
        if (!c.spine.empty()) {
            size_t off_s = (size_t)((uintptr_t)c.spine.data() - fbase);
            std::memcpy(base + off_s, c.spine.data(), c.spine.size() * sizeof(uint16_t));
            sp = reinterpret_cast<const uint16_t *>(base + off_s);
        }
        d[i] = Desc{reinterpret_cast<const uint16_t *>(base + off_c), sp, (int32_t)c.carr.size()};
    }
    s.mirror = std::move(arena);
    s.mirror_span = span;
    s.mirror_alloc = alloc_bytes;
    s.mirror_packed = packed;
    s.mirror_fbase = fbase;
}

// Every copy byte for byte against its original, plus the residue invariants.
static void verify_copies(const std::vector<ContainerSet> &sets) {
    for (const auto &s : sets) {
        const Desc *f = s.desc(V_F);
        for (int i = 0; i < kNumContainers; i++) {
            size_t cb = (size_t)f[i].n * 2;
            size_t sb = (size_t)(f[i].n / kGap) * 2;
            if ((f[i].spine == nullptr) != (sb == 0)) die("F spine pointer disagrees with its size");
            for (int v = 1; v < kVariants; v++) {
                const Desc &x = s.desc(v)[i];
                if (x.n != f[i].n) die("copy has a different cardinality");
                if (x.carr == nullptr || x.carr == f[i].carr) die("copy aliases or lacks the array");
                if ((x.spine == nullptr) != (f[i].spine == nullptr)) die("copy spine presence differs");
                if (std::memcmp(x.carr, f[i].carr, cb) != 0) die("array copy differs from its source");
                if (f[i].spine && std::memcmp(x.spine, f[i].spine, sb) != 0) die("spine copy differs from its source");
                uintptr_t rc = (uintptr_t)x.carr & (kAlign - 1);
                uintptr_t rs = x.spine ? ((uintptr_t)x.spine & (kAlign - 1)) : 0;
                uintptr_t fc = (uintptr_t)f[i].carr & (kAlign - 1);
                uintptr_t fs = f[i].spine ? ((uintptr_t)f[i].spine & (kAlign - 1)) : 0;
                bool ok = true;
                switch (v) {
                    case V_Fa: case V_Fapool: ok = (rc == 0 && rs == 0); break;
                    case V_Fao: ok = (rc == kOffsetResidue && (!x.spine || rs == kOffsetResidue)); break;
                    case V_Fv2: case V_Fpool: ok = (rc == fc && rs == fs); break;
                    case V_Fmir: {  // the original's offset from the page-aligned base, exactly (implies equal page offsets and residues)
                        uintptr_t mb = (uintptr_t)s.mirror.get();
                        ok = ((uintptr_t)x.carr - mb == (uintptr_t)f[i].carr - s.mirror_fbase)
                          && (!x.spine || (uintptr_t)x.spine - mb == (uintptr_t)f[i].spine - s.mirror_fbase);
                        break;
                    }
                    default: break;
                }
                if (!ok) {
                    std::fprintf(stderr, "residue invariant violated for %s: carr %zu spine %zu (F: %zu %zu)\n",
                                 kNames[v], (size_t)rc, (size_t)rs, (size_t)fc, (size_t)fs);
                    std::exit(1);
                }
            }
        }
    }
}

// ---- layout diagnostics ----------------------------------------------------

struct LayoutStats {
    unsigned hc[5] = {0, 0, 0, 0, 0}, hs[5] = {0, 0, 0, 0, 0};  // residue 0/16/32/48/other
    unsigned ncarr = 0, nspine = 0, eq_c = 0, eq_s = 0;        // residue equal to F's, copy by copy
    size_t pages = 0, lines = 0, spine_lines = 0;
    long long stride_med = 0, spine_dist_med = 0;  // bytes: carr[i+1] - carr[i]; spine[i] - carr[i]
    unsigned stride_n = 0, stride_off = 0;
};

static inline unsigned residue_bin(uintptr_t p) {
    return (p & 15u) ? 4u : (unsigned)((p & 63u) >> 4);
}

static void add_span(uintptr_t a, size_t bytes, std::vector<uint64_t> &pages, std::vector<uint64_t> &lines) {
    uint64_t p0 = a >> 14, p1 = (a + bytes - 1) >> 14;  // 16 KB pages
    for (uint64_t p = p0; p <= p1; p++) pages.push_back(p);
    uint64_t l0 = a >> 6, l1 = (a + bytes - 1) >> 6;
    for (uint64_t l = l0; l <= l1; l++) lines.push_back(l);
}

static size_t count_unique(std::vector<uint64_t> &v) {
    std::sort(v.begin(), v.end());
    return (size_t)(std::unique(v.begin(), v.end()) - v.begin());
}

static LayoutStats layout_stats(const std::vector<ContainerSet> &sets, int v) {
    LayoutStats st;
    std::vector<uint64_t> pages, lines, slines;
    std::vector<long long> strides, dists;
    for (const auto &s : sets) {
        const Desc *d = s.desc(v);
        const Desc *f = s.desc(V_F);
        lines.clear();
        slines.clear();
        for (int i = 0; i < kNumContainers; i++) {
            uintptr_t pc = (uintptr_t)d[i].carr;
            size_t cb = (size_t)d[i].n * 2;
            st.hc[residue_bin(pc)]++;
            st.ncarr++;
            if ((pc & 63u) == ((uintptr_t)f[i].carr & 63u)) st.eq_c++;
            add_span(pc, cb, pages, lines);
            if (d[i].spine) {
                uintptr_t ps = (uintptr_t)d[i].spine;
                size_t sb = (size_t)(d[i].n / kGap) * 2;
                st.hs[residue_bin(ps)]++;
                st.nspine++;
                if ((ps & 63u) == ((uintptr_t)f[i].spine & 63u)) st.eq_s++;
                add_span(ps, sb, pages, lines);
                for (uint64_t l = ps >> 6; l <= (ps + sb - 1) >> 6; l++) slines.push_back(l);
                dists.push_back((long long)ps - (long long)pc);
            }
            if (i > 0) strides.push_back((long long)pc - (long long)(uintptr_t)d[i - 1].carr);
        }
        st.lines += count_unique(lines);  // per set, summed (a line shared by two sets is counted twice, at most once per set boundary)
        st.spine_lines += count_unique(slines);
    }
    st.pages = count_unique(pages);
    if (!dists.empty()) {
        std::sort(dists.begin(), dists.end());
        st.spine_dist_med = dists[dists.size() / 2];
    }
    if (!strides.empty()) {
        std::vector<long long> sorted = strides;
        std::sort(sorted.begin(), sorted.end());
        st.stride_med = sorted[sorted.size() / 2];
        st.stride_n = (unsigned)strides.size();
        for (long long x : strides) if (x != st.stride_med) st.stride_off++;
    }
    return st;
}

// One line per variant: residue-mod-64 histograms of the array and spine
// pointers (16-byte steps; "other" = not a multiple of 16), how many copies
// sit at the same residue as F's (copy by copy), the footprint in 16 KB pages
// (distinct, over all sets) and 64-byte lines (distinct per set, summed; the
// spines' lines separately), the median byte stride between consecutive
// containers' arrays with the count of strides off that median, the median
// byte distance from a container's array to its spine (negative: the spine
// lies before the array), for the arenas the base alignment, the bytes used
// and allocated, the per-set range and whether glibc carved them from the brk
// heap or mmap'd them, for Fmir the data's share of the mirrored span, and
// for Fv2 the steering counts.
static void print_layout(const std::vector<ContainerSet> &sets) {
    void *heap_end = sbrk(0);
    for (int v = 0; v < kVariants; v++) {
        LayoutStats st = layout_stats(sets, v);
        std::printf("# layout: %-6s carr_res0/16/32/48/other=%u/%u/%u/%u/%u spine_res0/16/32/48/other=%u/%u/%u/%u/%u "
                    "res_eq_F=carr:%u/%u,spine:%u/%u pages=%zu lines=%zu spine_lines=%zu "
                    "stride_med=%lld stride_offmed=%u/%u spine_dist_med=%lld",
                    kNames[v], st.hc[0], st.hc[1], st.hc[2], st.hc[3], st.hc[4],
                    st.hs[0], st.hs[1], st.hs[2], st.hs[3], st.hs[4],
                    st.eq_c, st.ncarr, st.eq_s, st.nspine, st.pages, st.lines, st.spine_lines,
                    st.stride_med, st.stride_off, st.stride_n, st.spine_dist_med);
        if (v == V_Fpool || v == V_Fapool || v == V_Fmir) {
            size_t total = 0, alloc = 0, mn = SIZE_MAX, mx = 0, align = SIZE_MAX, packed = 0;
            unsigned on_heap = 0;
            for (const auto &s : sets) {
                const uint16_t *base = (v == V_Fpool) ? s.pool.get() : (v == V_Fapool) ? s.apool.get() : s.mirror.get();
                size_t used = (v == V_Fpool) ? s.pool_bytes : (v == V_Fapool) ? s.apool_bytes : s.mirror_span;
                size_t al = (v == V_Fpool) ? s.pool_alloc : (v == V_Fapool) ? s.apool_alloc : s.mirror_alloc;
                total += used; alloc += al; packed += s.mirror_packed;
                mn = std::min(mn, used); mx = std::max(mx, used);
                uintptr_t b = (uintptr_t)base;
                size_t a = (size_t)(b & (~b + 1));  // lowest set bit = largest power-of-two alignment
                align = std::min(align, std::min(a, (size_t)1 << 30));
                if ((const void *)base < heap_end) on_heap++;
            }
            std::printf(" arena_align=%zu arena_total=%zu arena_alloc=%zu arena_per_set=%zu..%zu arena_region=%s",
                        align, total, alloc, mn, mx,
                        on_heap == sets.size() ? "heap" : on_heap == 0 ? "mmap" : "mixed");
            if (v == V_Fmir) {
                std::printf(" mirror_packed=%zu mirror_fill=%.1f%%", packed, total ? 100.0 * (double)packed / (double)total : 0.0);
            }
        }
        if (v == V_Fv2) {
            std::printf(" fv2_shims=%zu fv2_shim_misses=%u fv2_padding=%zu/%zuB fv2_bin_accepts=%u fv2_resyncs=%u",
                        g_fv2.shims.size(), g_fv2.shim_misses, g_fv2.padding.size(), g_fv2.padding_bytes,
                        g_fv2.bin_accepts, g_fv2.resyncs);
        }
        std::printf("\n");
    }
}

// ---- lookups ----------------------------------------------------------------

// Shar branchless binary search over the set's keys (K = kNumContainers), as in F.
static inline int find_container_shar(const SetView &s, uint16_t key) {
    constexpr int len = kNumContainers;
    const uint16_t *base  = s.keys;
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

// The one lookup, instantiated per variant: the only difference between the
// seven is which descriptor array the view hands it.
template <int V>
static bool lookup(const SetView &s, uint32_t v) {
    int idx = find_container_shar(s, (uint16_t)(v >> 16));
    if (idx < 0) return false;
    const Desc &d = s.desc[V][idx];
    return simd_quad_pi5_spine(d.carr, d.spine, d.n, (uint16_t)v);
}

static bool ref_lookup(const ContainerSet &s, uint32_t v) {
    uint16_t key = (uint16_t)(v >> 16);
    auto it = std::lower_bound(s.keys.begin(), s.keys.end(), key);
    if (it == s.keys.end() || *it != key) return false;
    const auto &c = s.containers[(size_t)(it - s.keys.begin())].carr;
    return std::binary_search(c.begin(), c.end(), (uint16_t)v);
}

// ---- timing (bench_ab_pi5.cpp, verbatim but for the SetView) ---------------

template <typename Fn>
static double bench_hot_batched(const std::vector<SetView> &sets,
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
static double bench_hot_serial(const std::vector<SetView> &sets,
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
static double bench_cold_batched(const std::vector<SetView> &sets,
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
static double bench_cold_serial(const std::vector<SetView> &sets,
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

// Read with open/read, not stdio: a FILE and its buffer would be malloc'd and
// freed before the first pass and leave a hole that shifts F's heap layout
// on hosts that have the sysfs file (keep_heap_clean below).
static const char *thp_state(char *buf, size_t n) {
    int fd = open("/sys/kernel/mm/transparent_hugepage/enabled", O_RDONLY);
    if (fd < 0) return "none";
    char line[160] = {0};
    ssize_t got = read(fd, line, sizeof line - 1);
    close(fd);
    if (got <= 0) return "unreadable";
    char *l = std::strchr(line, '[');
    char *e = l ? std::strchr(l, ']') : nullptr;
    if (l && e) {
        std::snprintf(buf, n, "%.*s", (int)(e - l - 1), l + 1);
        return buf;
    }
    return "unknown";
}

// F's first-pass heap layout must depend on the per-set allocation sequence
// alone, not on the harness's bookkeeping: a std::vector reserve that lands on
// the brk heap before the first pass shifts every original by its chunk size
// (the first version of this harness rotated F's residues by 32 bytes when
// sizeof(ContainerSet) grew by 40, and would have shifted them with
// num_sets), and stdio malloc's its stdout buffer at the first printf, sized
// by the output file's st_blksize capped at BUFSIZ (8 KB here for /tmp, a
// pipe and the CIFS share alike -- the same 8208-byte chunk, so no shift was
// seen -- but 4 KB on a 4 KB-blksize destination). Hence: stdout gets a
// static buffer, the THP probe uses open/read, and the two per-set vectors
// are reserved beyond glibc's 128 KB mmap threshold so their storage is
// mmap'd, off the heap (the descriptor block, 224 KB, is mmap'd for the same
// reason). What remains before the first pass is glibc's own start-up state.
static char g_stdout_buf[1 << 16];
template <typename T>
static void reserve_off_heap(std::vector<T> &v, size_t n) {
    size_t off_heap = (131072 + 4096) / sizeof(T) + 1;  // > the mmap threshold even after glibc's rounding
    v.reserve(std::max(n, off_heap));
    if ((const void *)v.data() < sbrk(0)) die("a bookkeeping vector landed on the brk heap");
}

int main(int argc, char **argv) {
    std::setvbuf(stdout, g_stdout_buf, _IOFBF, sizeof g_stdout_buf);  // keep_heap_clean: no malloc'd stdio buffer
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
    if (num_sets < 1 || hot_reps < 1) {
        std::fprintf(stderr, "num_sets and hot_reps must be >= 1\n");
        return 2;
    }
    const bool hot_mode  = (std::strcmp(mode, "hb") == 0 || std::strcmp(mode, "hs") == 0);
    const bool cold_mode = (std::strcmp(mode, "cb") == 0 || std::strcmp(mode, "cs") == 0);
    if (!hot_mode && !cold_mode) {
        std::fprintf(stderr, "unknown mode '%s' (use hb/hs/cb/cs)\n", mode);
        return 2;
    }

    long page = sysconf(_SC_PAGESIZE);
    char thp_buf[64];
    const char *thp = thp_state(thp_buf, sizeof thp_buf);
    const char *libc = gnu_get_libc_version();
    std::printf("# bench_layout_pi5 inner_n=%d mode=%s num_sets=%d hot_reps=%d order_seed=%u gap=%d inner=pi5_spine "
                "kernel_blob=%s variants=%d align=%zu arena_align=%zu offset_residue=%zu page=%ld thp=%s glibc=%s "
                "desc_align=%zu thrash_bytes=%zu\n",
                inner_n, mode, num_sets, hot_reps, order_seed, kGap, QUADSEARCH_KERNEL_BLOB, kVariants,
                kAlign, kArenaAlign, kOffsetResidue, page, thp, libc, (size_t)alignof(Desc), kThrashBytes);
    std::printf("# variants: F = Shar outer + simd_quad_pi5_spine on the std::vector originals; "
                "Fa = the same on aligned_alloc(%zu) second-pass copies with sizes rounded up to %zu (sweep_ab1's Fa: alignment, position, footprint and spine placement at once); "
                "Fv2 = on std::vector second-pass copies steered to the original's residue mod %zu copy by copy (position only, glibc, spines adjacent); "
                "Fao = on second-pass posix_memalign(%zu, rounded+%zu) copies read at p+%zu, every pointer at residue %zu, the same glibc spacing as Fa (alignment only vs Fa, footprint equal); "
                "Fpool = on one aligned_alloc(%zu) arena per set, copies packed in container order at the original's residue mod %zu (position only, arena, tightly packed, spines adjacent); "
                "Fapool = the same arena with every copy at the next %zu-byte boundary and sizes rounded up to %zu (alignment only, arena); "
                "Fmir = on one aligned_alloc(%zu) arena per set holding F's layout at the original offsets from the page-aligned base (position only, F's residues, strides, holes and spine placement kept)\n",
                kAlign, kAlign, kAlign, kAlign, kOffsetResidue, kOffsetResidue, kOffsetResidue,
                kArenaAlign, kAlign, kAlign, kAlign, kArenaAlign);
    if (page != (long)kArenaAlign) {
        std::printf("# note: page size %ld differs from the arena alignment %zu\n", page, kArenaAlign);
    }
    if (kSmokeBuild) {
        std::printf("# thrash_bytes: %zu (NOT the 512 MB campaign flush: functional check only)\n", kThrashBytes);
        if (cold_mode && std::getenv("QUADSEARCH_SMOKE") == nullptr) {
            std::fprintf(stderr,
                         "bench_layout_pi5: built with QUADSEARCH_THRASH_BYTES=%zu, not the 512 MB campaign flush: "
                         "its cold cells are not measurements. Set QUADSEARCH_SMOKE=1 for a functional check, or run "
                         "the campaign binary (header comment: the plain name, built without the macro).\n",
                         kThrashBytes);
            return 2;
        }
    }

    // First pass: sets and targets, exactly as bench_ab_pi5 / bench_sweep_f_vs_lem.
    std::mt19937 rng(0xB17F17);
    std::vector<ContainerSet> sets;
    reserve_off_heap(sets, (size_t)num_sets);
    std::vector<std::vector<uint32_t>> targets;
    reserve_off_heap(targets, (size_t)num_sets);
    for (int i = 0; i < num_sets; i++) {
        sets.push_back(make_set(rng, inner_n));
        std::vector<uint32_t> ts;
        ts.reserve(1024);
        std::uniform_int_distribution<int> pc(0, kNumContainers - 1);
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

    // Second pass (see the header for the order).
    make_copies_Fv2(sets);
    make_copies_Fa(sets);
    make_copies_Fao(sets);
    for (auto &s : sets) make_pool(s, false);
    for (auto &s : sets) make_pool(s, true);
    for (int i = 0; i < num_sets; i++) make_mirror(sets[i], i);
    verify_copies(sets);

    std::vector<SetView> views(num_sets);
    if (((uintptr_t)views.data() & 63u) != 0) die("set views are not line-aligned");
    for (int i = 0; i < num_sets; i++) {
        SetView &w = views[i];
        w.keys = sets[i].keys.data();
        for (int v = 0; v < kVariants; v++) w.desc[v] = sets[i].desc(v);
    }
    print_layout(sets);

    // Correctness: every variant must agree with a scalar reference.
    auto NaN = std::numeric_limits<double>::quiet_NaN();
    bool (*fns[kVariants])(const SetView &, uint32_t) =
        {lookup<V_F>, lookup<V_Fa>, lookup<V_Fv2>, lookup<V_Fao>, lookup<V_Fpool>, lookup<V_Fapool>, lookup<V_Fmir>};

    auto check = [&](int si, uint32_t t) {
        bool r = ref_lookup(sets[si], t);
        for (int i = 0; i < kVariants; i++) {
            bool got = fns[i](views[si], t);
            if (got != r) {
                std::fprintf(stderr, "MISMATCH inner_n=%d set=%d t=%u ref=%d %s=%d\n",
                             inner_n, si, t, (int)r, kNames[i], (int)got);
                return false;
            }
        }
        return true;
    };
    for (int si = 0; si < std::min(5, num_sets); si++) {
        for (int k = 0; k < 200; k++)
            if (!check(si, targets[si][k])) return 1;
        if (inner_n <= 128) {  // every element and its neighbours: the fast paths, the delegated sizes and the first spine descents
            for (int ci = 0; ci < kNumContainers; ci++) {
                const auto &c = sets[si].containers[ci].carr;
                uint32_t hi = uint32_t(sets[si].keys[ci]) << 16;
                for (uint16_t e : c) {
                    if (!check(si, hi | e)) return 1;
                    if (e > 0 && !check(si, hi | (uint32_t)(e - 1))) return 1;
                    if (e < 65535 && !check(si, hi | (uint32_t)(e + 1))) return 1;
                }
            }
        }
    }
    std::printf("# correctness: ok (%d variants, %d sets x 200 probes%s)\n", kVariants, std::min(5, num_sets),
                inner_n <= 128 ? ", every element and its neighbours" : "");

    double vals[kVariants];
    for (int i = 0; i < kVariants; i++) vals[i] = NaN;
    int order[kVariants];
    for (int i = 0; i < kVariants; i++) order[i] = i;
    if (order_seed != 0) {
        std::mt19937 g(order_seed * 1000003u + (unsigned)inner_n * 7919u
                       + (unsigned)(unsigned char)mode[0] * 131u + (unsigned)(unsigned char)mode[1]);
        std::shuffle(order, order + kVariants, g);
    }
    std::printf("# timing order:");
    for (int i : order) std::printf(" %s", kNames[i]);
    std::printf("\n");

    // Equal-cache-state warm-up: all seven variants over every set, then the
    // variant about to be timed once more (bench_ab_pi5's semantics; the extra
    // pass puts every variant's data in the same, freshest state whatever the
    // canonical order left behind).
    auto warmup_hot = [&](auto fn) {
        volatile uint64_t acc = 0;
        for (size_t si = 0; si < views.size(); si++) {
            for (int r = 0; r < hot_reps; r++) {
                uint32_t t = targets[si][(r * 17u) % targets[si].size()];
                acc += fn(views[si], t);
            }
        }
        (void)acc;
    };
    auto warm_all_hot = [&]() { for (int i = 0; i < kVariants; i++) warmup_hot(fns[i]); };

    if (std::strcmp(mode, "hb") == 0) {
        for (int i : order) { warm_all_hot(); warmup_hot(fns[i]); vals[i] = bench_hot_batched(views, targets, hot_reps, fns[i]); }
    } else if (std::strcmp(mode, "hs") == 0) {
        for (int i : order) { warm_all_hot(); warmup_hot(fns[i]); vals[i] = bench_hot_serial(views, targets, hot_reps, fns[i]); }
    } else if (std::strcmp(mode, "cb") == 0) {
        // Discard one cold pass so process-startup TLB/page-fault costs
        // don't bias whichever variant is measured first.
        bench_cold_batched(views, targets, fns[order[0]]);
        for (int i : order) { thrash_llc(); vals[i] = bench_cold_batched(views, targets, fns[i]); }
    } else {  // cs (the mode was validated above)
        bench_cold_serial(views, targets, fns[order[0]]);
        for (int i : order) { thrash_llc(); vals[i] = bench_cold_serial(views, targets, fns[i]); }
    }

    std::printf("RESULT inner_n=%d mode=%s", inner_n, mode);
    for (int i = 0; i < kVariants; i++) std::printf(" %s=%.4f", kNames[i], vals[i]);
    std::printf("\n");
    return 0;
}

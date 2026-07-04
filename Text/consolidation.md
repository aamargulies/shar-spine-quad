# Consolidation sketch: unified templated quad_search

Here's the shape. Five files, maybe 500 lines total vs. the current ~1500.

## `quad_traits.hpp` — one struct per uarch, all knobs in one place

```cpp
struct TraitsA76 {
    static constexpr int gap = 32;
    static constexpr bool speculative_prefetch = true;
    using Leaf = NeonPairLeaf;       // vld1q_u16_x2 + 2 cmp + OR
};
struct TraitsFirestorm {             // M1 Pro + M4 Max share this
    static constexpr int gap = 64;
    static constexpr bool speculative_prefetch = false;
    using Leaf = NeonQuadPairLeaf;   // 2x vld1q_u16_x4 + 8 cmp + OR-tree
};
struct TraitsSkylakeSP {
    static constexpr int gap = 32;
    static constexpr bool speculative_prefetch = true;
    using Leaf = AvxPairLeaf;        // 2x 256b + cmpeq + OR + movemask
};
struct TraitsIceLakeSP {             // SPR / EMR / GNR
    static constexpr int gap = 32;
    static constexpr bool speculative_prefetch = false;
    using Leaf = Avx512Leaf;         // zmm + cmpeq_mask + kortest
};
struct TraitsNeoverseV2 {
    static constexpr int gap = 32;
    static constexpr bool speculative_prefetch = false;
    using Leaf = NeonPairLeaf;       // same as A76, sans prefetch
};
```

## `quad_leaf_neon.hpp` / `quad_leaf_avx.hpp` — pure leaf ops, nothing else

```cpp
struct NeonPairLeaf {
    static constexpr int gap = 32;
    static bool contains(const uint16_t *blk, uint16_t pos) {
        uint16x8_t needle = vdupq_n_u16(pos);
        uint16x8x2_t v = vld1q_u16_x2(blk);
        uint16x8_t hit = vorrq_u16(vceqq_u16(v.val[0], needle),
                                    vceqq_u16(v.val[1], needle));
        return vmaxvq_u16(hit) != 0;
    }
    // plus small-size tiers: leaf8, leaf16 as statics
};

struct Avx512Leaf {
    static constexpr int gap = 32;
    static bool contains(const uint16_t *blk, uint16_t pos) {
        __m512i needle = _mm512_set1_epi16((short)pos);
        __m512i v = _mm512_loadu_si512(blk);
        return _mm512_cmpeq_epi16_mask(v, needle) != 0;
    }
};
```

## `quad_search.hpp` — the one templated descent, shared by every host

```cpp
template <class T>
bool quad_search(const uint16_t *carr, int32_t cardinality, uint16_t pos) {
    constexpr int gap = T::gap;
    if (cardinality < gap) return small_fast_path<T>(carr, cardinality, pos);

    int32_t num_blocks = cardinality / gap;
    int32_t base = 0, n = num_blocks;

    while (n > 3) {
        int32_t q = n >> 2;
        int k1 = carr[(base + 1*q + 1) * gap - 1];
        int k2 = carr[(base + 2*q + 1) * gap - 1];
        int k3 = carr[(base + 3*q + 1) * gap - 1];
        base += ((k1 < pos) + (k2 < pos) + (k3 < pos)) * q;
        n -= 3 * q;
        if constexpr (T::speculative_prefetch) {
            __builtin_prefetch(carr + (base + (n >> 1)) * gap);
        }
    }
    while (n > 1) {
        int h = n >> 1;
        base = (carr[(base + h + 1) * gap - 1] < pos) ? base + h : base;
        n -= h;
    }
    int32_t lo = (carr[(base + 1) * gap - 1] < pos) ? base + 1 : base;

    if (lo < num_blocks) return T::Leaf::contains(carr + lo * gap, pos);
    return tail_sweep(carr, num_blocks * gap, cardinality, pos);
}

template <class T>
bool quad_search_spine(const uint16_t *carr, const uint16_t *spine,
                       int32_t cardinality, uint16_t pos) {
    // Same loop, reads `spine[base + q]` instead of `carr[(base+q+1)*gap-1]`.
}

template <class T>
bool quad_search_spine_4096(const uint16_t *carr, const uint16_t *spine,
                            uint16_t pos) {
    // Three unrolled quaternary iterations; loop count depends on gap.
    // gap=32 -> num_blocks=128 -> 3 quat + 1 binary + final lo.
    // gap=64 -> num_blocks=64  -> 3 quat + final lo (no binary step).
    // Select via `if constexpr (T::gap == 64)`.
}
```

## `quad_dispatch.hpp` — arch macros pick the traits once

```cpp
#if defined(__AVX512VBMI2__)
    using ShipTraits = TraitsIceLakeSP;
#elif defined(__AVX2__)
    using ShipTraits = TraitsSkylakeSP;
#elif defined(__ARM_FEATURE_SVE2) && defined(__aarch64__)
    using ShipTraits = TraitsNeoverseV2;   // or detect more carefully
#elif defined(__APPLE__) && defined(__aarch64__)
    using ShipTraits = TraitsFirestorm;
#elif defined(__aarch64__)
    using ShipTraits = TraitsA76;          // Pi 5 default
#endif

bool simd_quad(const uint16_t *carr, int32_t n, uint16_t pos) {
    return quad_search<ShipTraits>(carr, n, pos);
}
```

## What this buys

- Loop body written once. Every descent-level bug gets fixed once.
- Adding a seventh host = one new traits struct, maybe one new leaf file.
- `if constexpr (T::speculative_prefetch)` makes the prefetch-or-not a compile-time decision — same codegen as the hand-specialized files.
- The non-obvious bits (AVX-512 freq-license gate, gap-follows-cache-line, prefetch polarity) move from scattered `.c` comments into one documented enum of traits structs.

## What this loses

- Per-host tweaks that don't fit the traits schema need schema changes. Example: if someone finds "use `prfm pstl1keep` instead of `pldl1keep` on V2" that's a new trait bit. Manageable as long as the schema stays small.
- Debugging symbolic names in a templated binary is less pleasant than `simd_quad_m4_spine_4096`. Mitigate with explicit instantiations and `__attribute__((flatten))` at the top-level entry points.
- You lose the "open one file, see the whole host-specific algorithm" property that's been useful during tuning. Once tuning stops, this property is no longer worth duplication.

## Order of operations if you do this

1. Keep all six `.c` files in place.
2. Add `quad_*.hpp` in parallel, wired under a `-DUSE_UNIFIED` flag in `bench.cpp`.
3. Verify byte-identical correctness + within-noise perf on all six hosts.
4. Only then delete the originals.

The unified version should produce **identical machine code** for every ship path — `if constexpr` + inlined leaf functions give the compiler the same information the hand-written files give it. If something regresses, it's a template leak worth investigating (usually a missing `__attribute__((always_inline))`), not a fundamental cost of abstraction.

## Recommendation

Do this *after* `RoaringSet` (open item 2) lands. That work will either confirm the traits schema is complete or reveal one more axis of variation; either way, you want to know before you collapse the duplication.

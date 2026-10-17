# Assembly of the kernels measured by the sweep_abi1 campaign (Coffee Lake, 2026-10-13)

`objdump -d --no-show-raw-insn -C` of the campaign binary
(`/home/adam/build_ab_intel/campaign/bench_ab_intel_campaign` on the laptop,
sha256 5505ec1360c2f700..., built there with `g++ (GCC) 17.0.0 20260824 -O3
-march=native -std=c++20 -DQUADSEARCH_DESCRIPTOR_ALIGN=64 bench_ab_intel.cpp
ab_tu_base.cpp ab_tu_np.cpp ab_tu_tail.cpp`, `-march=native` = skylake: AVX2,
no AVX-512), one file per kernel variant and function, cut at the function
boundaries:

| file | kernel | lines | prefetcht0 | vpcmpeqw | vpminuw |
|---|---|---|---|---|---|
| `ab_base_simd_quad_intel.s` | shipped plain kernel (blob 418fd3a8) | 533 | 1 (the in-loop prefetch) | 6 | 2 |
| `ab_base_simd_quad_intel_spine.s` | shipped general-n spine kernel | 758 | 1 (the spine line) | 14 | 8 |
| `ab_np_simd_quad_intel.s` | variant np: the in-loop `_mm_prefetch` removed | 528 | 0 | 6 | 2 |
| `ab_np_simd_quad_intel_spine.s` | np spine kernel (unchanged source) | 762 | 1 | 14 | 8 |
| `ab_tail_simd_quad_intel.s` | variant tail: last-32-element window instead of the scalar tail sweep | 368 | 1 | 7 | 1 |
| `ab_tail_simd_quad_intel_spine.s` | tail spine kernel | 403 | 1 | 11 | 1 |

What to read in them: the shipped kernels' "scalar" tail sweep is not scalar
as compiled -- GCC 17 emits an alignment-peeling prologue of up to 15
compare-and-branch steps, a `vpminuw`/`vpcmpeqw`/`vptest` step for tails of
about 23 or more elements and a scalar epilogue (the `vpminuw` counts above);
the tail variant replaces all of it with two `vpcmpeqw` against the array's
last 64 bytes, `vpor`, `vpmovmskb`, `setne` (hence 165 and 355 fewer lines).
In the spine kernel GCC inlines the delegated plain kernel for num_blocks <= 3
and compiles that copy with its own unrolled ymm sweep, so F's 32..127 code
is not G's. The np variant differs from base by the one `prefetcht0` and the
code placement that follows from it; its spine kernel is the same source.
The variants' sources are `cfl_runs/sweep_abi1_variants.diff` against
`simd_quad_intel.c` at blob 418fd3a8 (the file as it was until the prefetch
removal of 2026-10-13); `gen_intel_ab_variants.py` regenerates them from that
blob (`git show 7011486:simd_quad_intel.c`).

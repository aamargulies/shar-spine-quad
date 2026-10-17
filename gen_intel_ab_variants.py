#!/usr/bin/env python3
"""Derive the kernel variants of the Intel kernel A/B from simd_quad_intel.c.

Usage (from the repo root):

    python3 gen_intel_ab_variants.py OUTDIR [--kernel simd_quad_intel.c] [--diff FILE]

Modelled on gen_pi5_ab_variants.py (the reviewed Pi 5 design of 2026-10-12).
Writes into OUTDIR one source file per variant, each the shipped kernel with
exactly one change made by exact-string substitution (the script aborts if a
pattern does not occur exactly the expected number of times, so a later edit
of the kernel cannot silently produce a different experiment):

    intel_ab_np.c    no in-loop prefetch: the plain kernel simd_quad_intel's
                     one in-loop statement
                         _mm_prefetch((const char *)(carr + (base + (n >> 1)) * gap),
                                      _MM_HINT_T0);
                     (inside the `#if !defined(__AVX512VBMI2__)` block of the
                     quaternary loop) is replaced by the comment line that the
                     archived variant of the Coffee Lake main-bench prefetch A/B
                     used, so this file is byte for byte the kernel of
                     cfl_runs/prefetch_ab_variant.diff (campaign tag pfab,
                     2026-10-13). The spine kernels' `_mm_prefetch(spine)`
                     stays. On a build that defines __AVX512VBMI2__ the
                     statement is compiled out of the shipped kernel anyway and
                     np is the same code as base. The pattern exists only in
                     the kernel up to blob 418fd3a8 (the file before the
                     prefetch removal of 2026-10-13, `git show
                     7011486:simd_quad_intel.c`); on the current kernel the
                     script aborts for np by design -- pass --kernel with that
                     blob's file to regenerate the archived sweep_abi1 variants.
                     The same holds for the tail variant below: the vector tail
                     was adopted into simd_quad_intel.c on 2026-10-17 (with an
                     extra empty-tail guard), so the scalar sweep it replaces
                     no longer exists in the shipped file.
    intel_ab_tail.c  vector tail: in EVERY general-n kernel of the file -- the
                     plain kernel simd_quad_intel, the general-n spine kernel
                     simd_quad_intel_spine and the padded spine kernel
                     simd_quad_intel_spine_padded, three occurrences of the
                     identical text -- the scalar sweep of the partial last
                     block,
                         for (int32_t j = num_blocks * gap; j < cardinality; j++) {
                             uint16_t v = carr[j];
                             if (v >= pos) return v == pos;
                         }
                         return false;
                     becomes a vector membership test of the last gap (= 32)
                     elements of the array, tl = carr + cardinality - gap: on
                     AVX2 two 256-bit loads at tl and tl + 16, cmpeq against the
                     broadcast needle, OR, movemask != 0; under
                     `#if defined(__AVX512VBMI2__)` the one-zmm form. The
                     correctness argument is written into the generated source
                     as a comment (TAIL_NEW below): at that point cardinality
                     >= gap, so the window is in bounds and holds the whole
                     tail (fewer than gap elements) plus a slice of the last
                     full block, whose maximum the descent has just found to be
                     < pos (that is what lo == num_blocks means), so with carr
                     sorted the slice cannot match and a match in the window is
                     a match in the tail; when the tail is empty the window is
                     the last full block, where pos cannot match for the same
                     reason. The compile-time _spine_N kernels have no tail and
                     are untouched. The small-size sweeps (`j = 0`, `j = 8`,
                     `j = 16`) are untouched.

The shipped kernel itself is variant "base" and is #included directly by its
translation unit, not copied, so the baseline is the shipped code by
construction.

For each variant, and for the shipped kernel ("base"), the script also writes
a one-namespace translation unit OUTDIR/ab_tu_<variant>.cpp:

    #include <immintrin.h> ... namespace ab_<variant> { #include "<kernel>" }

Each is compiled on its own with the kernel's build flags, exactly as the
shipped kernel TU is, so intra-kernel inlining and code layout are those of
the shipped build and the harness-to-kernel boundary is a cross-TU call, as
in every other harness of the project. No function is renamed: the
delegation call inside a variant's spine functions resolves to the variant's
own plain kernel through the namespace. ab_tu_base.cpp additionally defines
ab_base::kernel_blob() / kernel_source(): the git blob id (SHA-1 over
"blob <size>\\0" + bytes, computed here without git) and the path of the
kernel file the variants were derived from, which bench_ab_intel.cpp prints
in its header line, so a campaign's cells record the kernel they measured
without a -D flag anyone could forget.

With --diff FILE the unified diffs of the variants against the kernel are
written to FILE (default OUTDIR/intel_ab_variants.diff), which is what a
campaign archives next to its raw cells, as pi5_runs/sweep_ab1_variants.diff
does for the Pi 5 A/B. The np hunk is the archived
cfl_runs/prefetch_ab_variant.diff hunk (3 lines of context).
"""
import argparse
import difflib
import hashlib
import os
import sys

PREFETCH_OLD = ("        _mm_prefetch((const char *)(carr + (base + (n >> 1)) * gap),\n"
                "                     _MM_HINT_T0);\n")
# The replacement the archived Coffee Lake variant used (cfl_runs/prefetch_ab_variant.diff).
PREFETCH_NEW = ("        /* in-loop prefetch removed for the Coffee Lake A/B of 2026-10-13 (variant 'np') */\n")

TAIL_OLD = ("    for (int32_t j = num_blocks * gap; j < cardinality; j++) {\n"
            "        uint16_t v = carr[j];\n"
            "        if (v >= pos) return v == pos;\n"
            "    }\n"
            "    return false;\n")
TAIL_NEW = """\
    // Tail variant (gen_intel_ab_variants.py, 'tail', 2026-10-13): the partial
    // last block is checked with the block check's vector membership test over
    // the last gap elements of the array instead of the scalar sweep
    //     for (j = num_blocks * gap; j < cardinality; j++) { v = carr[j]; if (v >= pos) return v == pos; }
    //     return false;
    // Why this returns exactly what the sweep returned:
    //   - We are here because the descent ended at lo == num_blocks (every
    //     lo < num_blocks returned from the block check above) and because
    //     cardinality >= gap (cardinality < gap took the small-size paths), so
    //     tl = carr + cardinality - gap >= carr and the window [tl, tl + gap)
    //     lies inside the array: the loads below read only the array's own
    //     last 64 bytes.
    //   - The window ends where the array ends, so it holds the whole tail
    //     [num_blocks * gap, cardinality) -- fewer than gap elements -- and,
    //     before it, the last gap - (cardinality % gap) elements of block
    //     num_blocks - 1, the last full block.
    //   - lo == num_blocks means the descent compared the last full block's
    //     maximum carr[num_blocks * gap - 1] (the last spine entry) with pos
    //     and found it < pos: the final lo pick `(key < pos) ? base + 1 : base`
    //     (plain kernel, general-n spine) returns num_blocks only from base ==
    //     num_blocks - 1 with that key < pos, and the padded spine's 3-probe
    //     finish only when the entries base..num_blocks - 1 are all < pos (the
    //     spine is sorted and the two 0xFFFF sentinels never compare < pos).
    //     carr is sorted, so every element of the last full block is <= that
    //     maximum < pos and none of the window's extra elements can equal pos.
    //     Hence: a match in the window is a match in the tail, and a match in
    //     the tail is a match in the window (the tail is inside it).
    //   - When the tail is empty (cardinality % gap == 0) the window is the
    //     last full block itself, which cannot match for the same reason, and
    //     the result is false, as the empty sweep's was.
    // Cost: two unaligned 256-bit loads (one 512-bit load on the zmm path) of
    // the array's last 64 bytes and no data-dependent loop; the window contains
    // the element carr[num_blocks * gap - 1] the descent has just read, so it
    // touches at most one line the sweep would not have.
    {
        const uint16_t *tl = carr + cardinality - gap;
#if defined(__AVX512VBMI2__)
        __m512i needle = _mm512_set1_epi16((short)pos);
        __m512i v = _mm512_loadu_si512((const void *)tl);
        __mmask32 m = _mm512_cmpeq_epi16_mask(v, needle);
        return m != 0;
#else
        __m256i needle = _mm256_set1_epi16((short)pos);
        __m256i v0 = _mm256_loadu_si256((const __m256i *)tl);
        __m256i v1 = _mm256_loadu_si256((const __m256i *)(tl + 16));
        __m256i eq = _mm256_or_si256(_mm256_cmpeq_epi16(v0, needle),
                                     _mm256_cmpeq_epi16(v1, needle));
        return _mm256_movemask_epi8(eq) != 0;
#endif
    }
"""

VARIANTS = ("np", "tail")


def expect(count, want, what):
    if count != want:
        sys.exit(f"error: expected {want} occurrence(s) of {what}, found {count}; "
                 f"the kernel has changed -- revise this generator before measuring")


def no_prefetch(src):
    expect(src.count(PREFETCH_OLD), 1, "the plain kernel's in-loop _mm_prefetch statement")
    return src.replace(PREFETCH_OLD, PREFETCH_NEW)


def vector_tail(src):
    expect(src.count(TAIL_OLD), 3, "the general-n scalar tail sweep (plain, spine, padded spine)")
    return src.replace(TAIL_OLD, TAIL_NEW)


MAKERS = {"np": no_prefetch, "tail": vector_tail}

TU_TEMPLATE = """\
// Generated by gen_intel_ab_variants.py: the {label} compiled as its own
// translation unit inside namespace ab_{name}, for bench_ab_intel.cpp. The
// headers are included first so the kernel's own #includes are guarded
// no-ops inside the namespace.
#include <immintrin.h>
#include <stdbool.h>
#include <stdint.h>
namespace ab_{name} {{
#include "{include}"
}}
"""

BASE_EXTRA = """\
// The kernel the variants of this directory were derived from, for the
// harness's header line (git blob id of the file as read by the generator).
namespace ab_base {{
const char *kernel_blob() {{ return "{blob}"; }}
const char *kernel_source() {{ return "{source}"; }}
}}
"""


def git_blob_id(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def write_tu(outdir, name, include, extra=""):
    label = "shipped kernel simd_quad_intel.c" if name == "base" else f"variant {include}"
    path = os.path.join(outdir, f"ab_tu_{name}.cpp")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(TU_TEMPLATE.format(name=name, label=label, include=include))
        fh.write(extra)
    print(f"wrote {path}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outdir")
    ap.add_argument("--kernel", default="simd_quad_intel.c")
    ap.add_argument("--diff", help="write the unified diffs of the variants against the kernel here "
                                   "(default OUTDIR/intel_ab_variants.diff)")
    args = ap.parse_args(argv)

    with open(args.kernel, "rb") as fh:
        raw = fh.read()
    src = raw.decode("utf-8")
    blob = git_blob_id(raw)
    # Sanity: the sites the variants touch must be where the docstring says.
    expect(src.count("bool simd_quad_intel("), 1, "the plain kernel definition")
    expect(src.count("bool simd_quad_intel_spine("), 1, "the general-n spine kernel definition")
    expect(src.count("bool simd_quad_intel_spine_padded("), 1, "the padded spine kernel definition")
    expect(src.count("_mm_prefetch("), 8, "_mm_prefetch calls (1 in-loop + 7 spine prefetches)")

    os.makedirs(args.outdir, exist_ok=True)
    kernel_abs = os.path.abspath(args.kernel)
    print(f"kernel {kernel_abs} blob {blob}")
    write_tu(args.outdir, "base", kernel_abs, BASE_EXTRA.format(blob=blob, source=kernel_abs))
    diffs = []
    for name in VARIANTS:
        text = MAKERS[name](src)
        path = os.path.join(args.outdir, f"intel_ab_{name}.c")
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        write_tu(args.outdir, name, f"intel_ab_{name}.c")
        d = list(difflib.unified_diff(src.splitlines(keepends=True), text.splitlines(keepends=True),
                                      fromfile=args.kernel, tofile=f"intel_ab_{name}.c", n=3))
        diffs.append("".join(d))
        changed = sum(1 for l in d if l.startswith(("+", "-")) and not l.startswith(("+++", "---")))
        print(f"wrote {path} ({changed} changed line(s) vs {args.kernel})")
    diff_path = args.diff or os.path.join(args.outdir, "intel_ab_variants.diff")
    with open(diff_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(f"# Kernel variants of the Intel kernel A/B (bench_ab_intel.cpp), derived from {args.kernel} "
                 f"(git blob {blob}) by gen_intel_ab_variants.py\n")
        fh.write("# base = the kernel itself (#included directly by ab_tu_base.cpp)\n")
        fh.write("# np   = the plain kernel's in-loop _mm_prefetch replaced by a comment "
                 "(= cfl_runs/prefetch_ab_variant.diff)\n")
        fh.write("# tail = the scalar sweep of the partial last block replaced by a vector membership test "
                 "of the last 32 elements, in the plain, spine and padded-spine kernels\n\n")
        fh.write("\n".join(diffs))
    print(f"wrote {diff_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

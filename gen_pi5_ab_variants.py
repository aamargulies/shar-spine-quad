#!/usr/bin/env python3
"""Derive the kernel variants of the Pi 5 kernel A/B from simd_quad_pi5.c.

Usage (from the repo root):

    python3 gen_pi5_ab_variants.py OUTDIR [--kernel simd_quad_pi5.c] [--diff FILE]

Writes into OUTDIR one source file per variant, each the shipped kernel with
exactly one change made by exact-string substitution (the script aborts if a
pattern does not occur exactly the expected number of times, so a later edit
of the kernel cannot silently produce a different experiment):

    pi5_ab_cr.c   constant-return sweeps. Every scalar sweep step
                      if (x >= pos) return x == pos;
                  (and the same with v) becomes
                      if (x == pos) return true;
                      if (x > pos) return false;
                  Eight sites: the [1,8), [8,16) and [16,32) fast paths and
                  the block tail in simd_quad_pi5, and their copies in
                  simd_quad_pi5_spine. GCC 17 compiles the shipped form to a
                  data-dependent `cset` return and Lemire's equality loop to
                  constant returns through branches; the sweep_fvl3 campaign
                  left the n <= 7 cold_ser deficit of the Pi 5 kernel at that
                  difference (pi5_runs/sweep_fvl3_findings.md).
    pi5_ab_np.c   no in-loop prefetch: the one
                      __builtin_prefetch(carr + (base + (n >> 1)) * gap);
                  in the quaternary loop of simd_quad_pi5 is removed. The
                  spine prefetch (__builtin_prefetch(spine)) stays. This is
                  the code of simd_quad_graviton (CLAUDE.md, Files).
    pi5_ab_d1.c   delegation threshold 1: simd_quad_pi5_spine hands
                  `num_blocks <= 1` (not `<= 3`) to the plain kernel, so the
                  spine descent runs from two blocks (n >= 64) instead of
                  four (n >= 128).

The shipped kernel itself is variant "base" and is #included directly by the
harness (bench_ab_pi5.cpp), not copied, so the baseline is the shipped code
by construction.

The substitutions target the kernel as it was when the sweep_ab1 campaign ran
(git blob f7c140b8295c5388f46ca6917b6ea5f2bf81cd31, `git show
b60c8a8:simd_quad_pi5.c`). The in-loop prefetch was removed from the shipped
kernel on 2026-10-13 on the strength of that campaign and the flushed main
bench, so against the current file the "np" substitution finds nothing and
this script stops with an error, as intended: to regenerate the archived
variants, point --kernel at the old blob. With --diff the unified diffs of the three variants against
the kernel are written to FILE, which is what a campaign archives next to its
raw cells (pi5_runs/sweep_ab1_variants.diff).

For each variant, and for the shipped kernel ("base"), the script also writes
a one-namespace translation unit OUTDIR/ab_tu_<variant>.cpp:

    #include <arm_neon.h> ... namespace ab_<variant> { #include "<kernel>" }

Each is compiled on its own with the kernel's build flags, exactly as the
shipped kernel TU is, so intra-kernel inlining and code layout are those of
the shipped build and the harness-to-kernel boundary is a cross-TU call, as
in every other harness of the project. No function is renamed: the
delegation call inside the spine function resolves to the variant's own
plain kernel through the namespace.
"""
import argparse
import difflib
import os
import sys

SWEEP_OLD = "if ({v} >= pos) return {v} == pos;"
SWEEP_NEW = "if ({v} == pos) return true;\n{indent}if ({v} > pos) return false;"
PREFETCH_LINE = "        __builtin_prefetch(carr + (base + (n >> 1)) * gap);\n"
DELEGATE_OLD = "if (num_blocks <= 3) {"
DELEGATE_NEW = "if (num_blocks <= 1) {"

VARIANTS = ("cr", "np", "d1")


def expect(count, want, what):
    if count != want:
        sys.exit(f"error: expected {want} occurrence(s) of {what}, found {count}; "
                 f"the kernel has changed -- revise this generator before measuring")


def const_return(src):
    """Rewrite every scalar sweep step as two constant-return branches."""
    out_lines = []
    hits = {"x": 0, "v": 0}
    for line in src.splitlines(keepends=True):
        stripped = line.lstrip(" ")
        indent = line[: len(line) - len(stripped)]
        replaced = False
        for var in ("x", "v"):
            old = SWEEP_OLD.format(v=var)
            if stripped.rstrip("\r\n") == old:
                hits[var] += 1
                out_lines.append(indent + SWEEP_NEW.format(v=var, indent=indent) + "\n")
                replaced = True
                break
        if not replaced:
            out_lines.append(line)
    expect(hits["x"], 4, "'if (x >= pos) return x == pos;'")
    expect(hits["v"], 4, "'if (v >= pos) return v == pos;'")
    return "".join(out_lines)


def no_prefetch(src):
    expect(src.count(PREFETCH_LINE), 1, "the in-loop prefetch line")
    return src.replace(PREFETCH_LINE, "")


def delegate_1(src):
    expect(src.count(DELEGATE_OLD), 1, f"'{DELEGATE_OLD}'")
    return src.replace(DELEGATE_OLD, DELEGATE_NEW)


MAKERS = {"cr": const_return, "np": no_prefetch, "d1": delegate_1}

TU_TEMPLATE = """\
// Generated by gen_pi5_ab_variants.py: the {label} compiled as its own
// translation unit inside namespace ab_{name}, for bench_ab_pi5.cpp. The
// headers are included first so the kernel's own #includes are guarded
// no-ops inside the namespace.
#include <arm_neon.h>
#include <stdbool.h>
#include <stdint.h>
namespace ab_{name} {{
#include "{include}"
}}
"""


def write_tu(outdir, name, include):
    label = "shipped kernel simd_quad_pi5.c" if name == "base" else f"variant {include}"
    path = os.path.join(outdir, f"ab_tu_{name}.cpp")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(TU_TEMPLATE.format(name=name, label=label, include=include))
    print(f"wrote {path}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outdir")
    ap.add_argument("--kernel", default="simd_quad_pi5.c")
    ap.add_argument("--diff", help="write the unified diffs of the variants against the kernel here")
    args = ap.parse_args(argv)

    with open(args.kernel, encoding="utf-8") as fh:
        src = fh.read()
    # Sanity: the three sites the variants touch must be where the docstring says.
    expect(src.count("bool simd_quad_pi5("), 1, "the plain kernel definition")
    expect(src.count("bool simd_quad_pi5_spine("), 1, "the spine kernel definition")

    os.makedirs(args.outdir, exist_ok=True)
    write_tu(args.outdir, "base", os.path.abspath(args.kernel))
    diffs = []
    for name in VARIANTS:
        text = MAKERS[name](src)
        path = os.path.join(args.outdir, f"pi5_ab_{name}.c")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        write_tu(args.outdir, name, f"pi5_ab_{name}.c")
        d = list(difflib.unified_diff(src.splitlines(keepends=True), text.splitlines(keepends=True),
                                      fromfile=args.kernel, tofile=f"pi5_ab_{name}.c", n=2))
        diffs.append("".join(d))
        changed = sum(1 for l in d if l.startswith(("+", "-")) and not l.startswith(("+++", "---")))
        print(f"wrote {path} ({changed} changed line(s) vs {args.kernel})")
    if args.diff:
        with open(args.diff, "w", encoding="utf-8") as fh:
            fh.write(f"# Kernel variants of the Pi 5 A/B, derived from {args.kernel} by gen_pi5_ab_variants.py\n")
            fh.write("# base = the kernel itself (#included directly by bench_ab_pi5.cpp)\n\n")
            fh.write("\n".join(diffs))
        print(f"wrote {args.diff}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

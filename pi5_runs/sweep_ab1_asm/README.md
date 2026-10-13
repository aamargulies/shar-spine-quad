# Assembly of the kernels measured by the sweep_ab1 campaign (2026-10-12)

`g++ -O3 -mcpu=cortex-a76 -std=c++20 -S` (GCC 17.0.0 20260704, trixie) of the
four per-variant translation units written by `gen_pi5_ab_variants.py`:

- `ab_tu_base.s` — `simd_quad_pi5.c` as shipped (blob f7c140b8295c5388f46ca6917b6ea5f2bf81cd31),
  wrapped in `namespace ab_base`; instruction-identical to the shipped kernel
  TU apart from the mangled names (checked with a normalised diff).
- `ab_tu_cr.s` — constant-return scalar sweeps. GCC does not compile this to
  the shipped code with a different return: each scalar step has two branches
  (`cmp; beq; bcc`) instead of one, the auto-vectorised step uses `cmeq` and
  `cmhi` with two `umaxp` instead of one `cmhs`, and the last element of a
  sweep still ends in `cmp; cset w0, eq; ret`. Fcr vs F measures the source
  form as compiled, which is what one would ship.
- `ab_tu_np.s` — the in-loop prefetch removed (the plain kernel loses its
  `prfm`; the spine kernels are unchanged).
- `ab_tu_d1.s` — delegation threshold 1 (the spine function's inlined copy of
  the plain kernel is specialised to one block instead of three).

The object files the campaign binary linked are reproducible from these
sources with the same flags (byte-identical on rebuild).

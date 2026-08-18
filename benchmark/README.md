# shar-spine-quad benchmark

Per-architecture benchmark for the `simd_quad` reference search and its
tuned variants (`pi5`, `m4`, `graviton`, `intel`), with plain and
spine-augmented forms plus a compile-time `n = 4096` specialization.
Modelled on the layout of Lemire's blog benchmark at
[`2026/04/26/benchmark`](https://github.com/lemire/Code-used-on-Daniel-Lemire-s-blog/tree/master/2026/04/26/benchmark):
many pre-built sorted arrays, a flat `(indices, keys)` traversal, and
two access patterns that share the same total query count.

## What is measured

For each `array_size` in the requested sweep, the benchmark builds
`number_arrays` independent sorted `uint16_t` arrays with no duplicates,
plus one precomputed spine per array per spine-variant. It then issues
`number_arrays × warmth` queries in two modes that differ only in the
access pattern:

| Mode | `indices[i]` | Effect |
|---|---|---|
| cold | `i % number_arrays` | round-robin across the array pool; every revisit is cache-cold |
| warm | `i / warmth`       | `warmth` consecutive queries on the same array; cache-hot |

The same query loop is used in both modes, so per-query instruction
counts are directly comparable; only the memory-traffic pattern changes.
Keys are 50% drawn from the targeted array (hits) and 50% random (mostly
misses).

A verification phase runs 10000 queries through every algorithm and
asserts agreement with `std::binary_search` before any timing starts.

## Algorithms benchmarked

The host architecture is detected at compile time and only the matching
variants are linked in.

ARM (`aarch64` / Apple silicon):

- `std::binary_search`, `std::find`
- `simd_quad` — reference, from Lemire's blog (gap = 16)
- `simd_quad_pi5`, `..._m4`, `..._gv4` — per-uarch tunings
- `..._pi5_spine`, `..._m4_spine`, `..._gv4_spine` — spine outer search
- `..._pi5_spine_4096`, `..._m4_spine_4096`, `..._gv4_spine_4096` —
  compile-time `n = 4096` specializations (timed only at `array_size = 4096`)

x86_64:

- `std::binary_search`, `std::find`
- `simd_quad`, `simd_quad_intel`, `simd_quad_intel_spine`,
  `simd_quad_intel_spine_4096` (the last only at `array_size = 4096`)

## Requirements

- CMake 3.10+
- A C++23 compiler (uses `std::print` / `std::format`):
  - Apple Clang 17+ (Xcode 16) — verified
  - Clang 18+
  - GCC 14+
- Network access on the first configure (CPM downloads
  `lemire/counters` v3.1.0 from GitHub for cycle/instruction/branch-miss
  counters)
- ARM NEON or x86 with AVX2 minimum (AVX-512 + VBMI2 enables the
  Intel zmm fast path)

## Build

```sh
cmake -B build
cmake --build build
```

CMakeLists auto-detects `CMAKE_SYSTEM_PROCESSOR`:

- `arm64` / `aarch64` / Apple → compiles
  `simd_quad_{pi5,m4,graviton}.c` with `-mcpu=native -O3`
- `x86_64` / `AMD64` → compiles `simd_quad_intel.c` with
  `-march=native -O3`

To override the tuning flag (e.g. for a cross-build), set
`CMAKE_C_FLAGS` / `CMAKE_CXX_FLAGS`:

```sh
cmake -B build \
  -DCMAKE_C_FLAGS="-mcpu=neoverse-v2 -O3" \
  -DCMAKE_CXX_FLAGS="-mcpu=neoverse-v2 -O3"
```

## Run

```sh
./build/benchmark                                  # default sweep
./build/benchmark --lengths 8,32,128,1024,4096     # custom sizes
./build/benchmark --number 5000 --warmth 200       # bigger working set
./build/benchmark --cold                           # cold mode only
./build/benchmark --warm                           # warm mode only
```

### CLI flags

| Flag | Default | Meaning |
|---|---|---|
| `--number N`      | `10000` | number of sorted arrays in the working set |
| `--warmth W`      | `100`   | queries per array in warm mode (= total / `number`) |
| `--lengths a,b,c` | `8,16,32,64,128,256,512,1024,2048,4096` | sizes to sweep |
| `--cold`          | off     | run cold mode only |
| `--warm`          | off     | run warm mode only |

Total queries per mode is `number × warmth`. Working-set memory is
roughly `number × array_size × 2 B` for the arrays plus comparable spine
storage; the defaults (10k × 4096 × 2 = 80 MB) intentionally exceed
typical L2/L3 so the cold mode is genuinely cold.

## Output

For every `(array_size, algorithm, mode)` triple the live output looks like:

```
simd_quad_m4_spine_4096          warm :   3.79 ns   0.27 Gv/s   3.50 GHz   13.27 c   34.10 i   0.040 bm   2.57 i/c
```

Columns are: ns/query, queries/second, frequency, cycles/query,
instructions/query, branch-misses/query, instructions/cycle. The last
five (after Gv/s) require kernel performance counters — see
"Performance counters" below.

At the end of the run, two markdown tables summarize ns/query across
all sizes — one for cold, one for warm (or only the mode you asked
for). Sizes are rows, algorithms are columns, missing cells (e.g.
`_spine_4096` outside `n = 4096`) show as `-`:

```
### Cold cache — ns / query (lower is better)

|    n | std::binary_search | simd_quad | simd_quad_m4 | simd_quad_m4_spine | simd_quad_m4_spine_4096 |
|-----:|-------------------:|----------:|-------------:|-------------------:|------------------------:|
|   64 |               4.84 |      2.01 |         1.97 |               2.50 |                       - |
| 1024 |              15.96 |      7.59 |         6.30 |               4.08 |                       - |
| 4096 |              23.57 |     11.47 |         8.96 |               5.73 |                    4.81 |
```

(Truncated to a few columns for the README; the actual table lists all
algorithms for the host.)

## Performance counters

The cycle/instruction/branch-miss columns and the final `i/c` figure
require kernel performance-counter access via Lemire's `counters`
library. Without the right privileges those columns are blank and the
benchmark prints a one-time advisory at startup.

- **macOS**: kperf needs elevated privileges.
  ```sh
  sudo ./build/benchmark ...
  ```
  Apple Silicon allows kperf reads from a privileged process; the
  `counters` library will attach automatically.

- **Linux**: `perf_event_open` is gated by `kernel.perf_event_paranoid`.
  Either run as root, or lower the gate:
  ```sh
  sudo sysctl -w kernel.perf_event_paranoid=0
  ./build/benchmark ...
  ```

Without counters you still get accurate ns/op and Gv/s — only the
microarchitectural breakdown is missing.

## Notes

- The `_spine_4096` variants only operate when `array_size == 4096` and
  are skipped (printed as `-` in the summary tables) at other sizes.
- The reference `simd_quad` is the verbatim implementation from
  Lemire's blog post and serves as the baseline the per-uarch variants
  are tuned against.
- The parent repo has its own `bench.cpp` driver with a different
  measurement methodology (steady-clock, per-pass medians); this
  directory exists to reproduce the blog's `counters`-based layout for
  side-by-side comparison.

// Benchmark for shar-spine-quad variants, modelled on the
// 2026/04/26 lemire-blog benchmark layout:
//
//   - N pre-built sorted uint16_t arrays, no duplicates
//   - flat (indices, keys) traversal of total = N * warmth queries
//   - cold: indices[i] = i % N   (round-robin -> every revisit is cache-cold)
//   - warm: indices[i] = i / warmth (consecutive hits on the same array)
//   - same total queries in both modes; only the access pattern differs
//   - counters::bench for ns / Gv/s / cycles / instructions / branch misses
//
// All simd_quad variants whose .c file matches the host ISA are benchmarked.
// Plain (no-spine), spine, and compile-time n=4096 spine specializations all
// participate; spine_4096 only runs when array_size == 4096.

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <format>
#include <map>
#include <print>
#include <random>
#include <set>
#include <string>
#include <utility>
#include <vector>

#include "counters/bench.h"

#if defined(__ARM_NEON) || defined(__aarch64__)
  #define QUADSEARCH_ARCH_ARM 1
  #include <arm_neon.h>
#elif defined(__x86_64__) || defined(_M_X64) || defined(__i386__)
  #define QUADSEARCH_ARCH_X86 1
  #include <immintrin.h>
#else
  #error "Unsupported architecture for shar-spine-quad benchmark"
#endif

// Reference (SSE2 / plain NEON) impl, bare function body that picks its own
// code path via __ARM_NEON.
#include "simd_quad.c"

extern "C" {
#if QUADSEARCH_ARCH_ARM
bool simd_quad_pi5(const uint16_t *carr, int32_t cardinality, uint16_t pos);
bool simd_quad_pi5_spine(const uint16_t *carr, const uint16_t *spine,
                         int32_t cardinality, uint16_t pos);
void simd_quad_pi5_build_spine(const uint16_t *carr, int32_t cardinality,
                               uint16_t *spine);
bool simd_quad_pi5_spine_4096(const uint16_t *carr, const uint16_t *spine,
                              uint16_t pos);

bool simd_quad_m4(const uint16_t *carr, int32_t cardinality, uint16_t pos);
bool simd_quad_m4_spine(const uint16_t *carr, const uint16_t *spine,
                        int32_t cardinality, uint16_t pos);
void simd_quad_m4_build_spine(const uint16_t *carr, int32_t cardinality,
                              uint16_t *spine);
bool simd_quad_m4_spine_4096(const uint16_t *carr, const uint16_t *spine,
                             uint16_t pos);

bool simd_quad_graviton(const uint16_t *carr, int32_t cardinality, uint16_t pos);
bool simd_quad_graviton_spine(const uint16_t *carr, const uint16_t *spine,
                              int32_t cardinality, uint16_t pos);
void simd_quad_graviton_build_spine(const uint16_t *carr, int32_t cardinality,
                                    uint16_t *spine);
bool simd_quad_graviton_spine_4096(const uint16_t *carr, const uint16_t *spine,
                                   uint16_t pos);
#endif

#if QUADSEARCH_ARCH_X86
bool simd_quad_intel(const uint16_t *carr, int32_t cardinality, uint16_t pos);
bool simd_quad_intel_spine(const uint16_t *carr, const uint16_t *spine,
                           int32_t cardinality, uint16_t pos);
void simd_quad_intel_build_spine(const uint16_t *carr, int32_t cardinality,
                                 uint16_t *spine);
bool simd_quad_intel_spine_4096(const uint16_t *carr, const uint16_t *spine,
                                uint16_t pos);
#endif
}

#if QUADSEARCH_ARCH_ARM
static constexpr int PI5_GAP = 32;
static constexpr int M4_GAP  = 64;
static constexpr int GV4_GAP = 32;
#endif
#if QUADSEARCH_ARCH_X86
static constexpr int INTEL_GAP = 32;
#endif

double pretty_print(const std::string &name, const std::string &mode,
                    size_t num_values, counters::event_aggregate agg) {
  std::print("{:<32} {:<4} : ", name, mode);
  std::print(" {:6.3f} ns ", agg.fastest_elapsed_ns() / double(num_values));
  std::print(" {:5.2f} Gv/s ", double(num_values) / agg.fastest_elapsed_ns());
  if (counters::has_performance_counters()) {
    std::print(" {:5.2f} GHz ", agg.cycles() / double(agg.elapsed_ns()));
    std::print(" {:6.2f} c ", agg.fastest_cycles() / double(num_values));
    std::print(" {:6.2f} i ", agg.fastest_instructions() / double(num_values));
    std::print(" {:5.3f} bm ", agg.branch_misses() / double(num_values));
    std::print(" {:5.2f} i/c ",
               agg.fastest_instructions() / double(agg.fastest_cycles()));
  }
  std::print("\n");
  return double(num_values) / agg.fastest_elapsed_ns();
}

// Per-(algorithm, mode, size) measurements. -1.0 means "not measured"
// (e.g. branch-miss counter unavailable on this platform).
struct Metrics {
  double ns = -1.0;
  double bm = -1.0;
};

// Cross-size accumulator. Insertion order preserved for algorithms so the
// table columns come out in a predictable order.
struct BenchResults {
  std::vector<std::string> algo_order;
  std::set<std::string> seen_algos;
  // (algo, mode) -> size -> Metrics
  std::map<std::pair<std::string, std::string>, std::map<size_t, Metrics>> data;

  void add(const std::string &algo, const std::string &mode,
           size_t size, double ns, double bm) {
    if (!seen_algos.count(algo)) {
      seen_algos.insert(algo);
      algo_order.push_back(algo);
    }
    data[{algo, mode}][size] = Metrics{ns, bm};
  }

  bool has_mode(const std::string &mode) const {
    for (const auto &a : algo_order) {
      if (data.count({a, mode})) return true;
    }
    return false;
  }
};

// One markdown table. `extract` picks ns or bm from each cell's Metrics;
// `fmt` formats the number; missing cells render as `-`.
static void print_markdown_table(const std::string &mode,
                                 const BenchResults &r,
                                 const std::vector<size_t> &sizes,
                                 const std::string &heading,
                                 auto extract,
                                 auto fmt) {
  std::vector<std::string> algos;
  for (const auto &a : r.algo_order) {
    if (r.data.count({a, mode})) algos.push_back(a);
  }
  if (algos.empty()) return;

  auto cell_for = [&](const std::string &algo, size_t s) -> std::string {
    const auto &m = r.data.at({algo, mode});
    auto it = m.find(s);
    if (it == m.end()) return "-";
    double v = extract(it->second);
    if (v < 0.0) return "-";
    return fmt(v);
  };

  size_t w_n = std::string("n").size();
  for (size_t s : sizes) w_n = std::max(w_n, std::to_string(s).size());
  std::vector<size_t> w_algo(algos.size());
  for (size_t c = 0; c < algos.size(); ++c) {
    w_algo[c] = algos[c].size();
    for (size_t s : sizes) {
      w_algo[c] = std::max(w_algo[c], cell_for(algos[c], s).size());
    }
  }

  std::print("\n### {} cache — {}\n\n",
             mode == "warm" ? "Warm" : "Cold", heading);

  std::print("| {:>{}} ", "n", w_n);
  for (size_t c = 0; c < algos.size(); ++c) {
    std::print("| {:>{}} ", algos[c], w_algo[c]);
  }
  std::print("|\n");

  std::print("|{:->{}}:", "", w_n + 1);
  for (size_t c = 0; c < algos.size(); ++c) {
    std::print("|{:->{}}:", "", w_algo[c] + 1);
  }
  std::print("|\n");

  for (size_t s : sizes) {
    std::print("| {:>{}} ", s, w_n);
    for (size_t c = 0; c < algos.size(); ++c) {
      std::print("| {:>{}} ", cell_for(algos[c], s), w_algo[c]);
    }
    std::print("|\n");
  }
}

static std::vector<uint16_t> make_sorted_unique(std::mt19937_64 &rng, size_t n) {
  std::set<uint16_t> s;
  std::uniform_int_distribution<int> d(0, 65535);
  while (s.size() < n) s.insert((uint16_t)d(rng));
  return std::vector<uint16_t>(s.begin(), s.end());
}

// Pre-benchmark correctness check. Generates a small independent pool of
// arrays at the given size, runs every algorithm against std::binary_search
// on a fresh set of queries, and aborts on any mismatch. Returns true on
// success. Independent from the benchmark data so a verification failure
// surfaces before any timing work is wasted.
static bool verify_at_size(size_t array_size,
                           size_t num_verify_arrays,
                           size_t queries_per_array) {
  if (array_size > 65536) array_size = 65536;

  std::mt19937_64 rng(0x12345ull ^ array_size);

  std::vector<std::vector<uint16_t>> arrays;
  arrays.reserve(num_verify_arrays);
  for (size_t a = 0; a < num_verify_arrays; ++a) {
    arrays.push_back(make_sorted_unique(rng, array_size));
  }

#if QUADSEARCH_ARCH_ARM
  std::vector<std::vector<uint16_t>> spines_pi5(num_verify_arrays);
  std::vector<std::vector<uint16_t>> spines_m4(num_verify_arrays);
  std::vector<std::vector<uint16_t>> spines_gv4(num_verify_arrays);
  for (size_t a = 0; a < num_verify_arrays; ++a) {
    spines_pi5[a].resize(std::max<size_t>(1, array_size / PI5_GAP));
    spines_m4 [a].resize(std::max<size_t>(1, array_size / M4_GAP));
    spines_gv4[a].resize(std::max<size_t>(1, array_size / GV4_GAP));
    if (array_size >= (size_t)PI5_GAP)
      simd_quad_pi5_build_spine(arrays[a].data(), (int32_t)array_size, spines_pi5[a].data());
    if (array_size >= (size_t)M4_GAP)
      simd_quad_m4_build_spine (arrays[a].data(), (int32_t)array_size, spines_m4 [a].data());
    if (array_size >= (size_t)GV4_GAP)
      simd_quad_graviton_build_spine(arrays[a].data(), (int32_t)array_size, spines_gv4[a].data());
  }
#endif
#if QUADSEARCH_ARCH_X86
  std::vector<std::vector<uint16_t>> spines_intel(num_verify_arrays);
  for (size_t a = 0; a < num_verify_arrays; ++a) {
    spines_intel[a].resize(std::max<size_t>(1, array_size / INTEL_GAP));
    if (array_size >= (size_t)INTEL_GAP)
      simd_quad_intel_build_spine(arrays[a].data(), (int32_t)array_size, spines_intel[a].data());
  }
#endif

  std::uniform_int_distribution<int> key_dist(0, 65535);
  size_t mismatches = 0;
  auto check_one = [&](const char *name, bool got, bool expected,
                       size_t n, uint16_t k) {
    if (got != expected) {
      if (mismatches < 5)
        std::print("MISMATCH: {} n={} key={} expected={} got={}\n",
                   name, n, k, expected, got);
      ++mismatches;
    }
  };

  for (size_t a = 0; a < num_verify_arrays; ++a) {
    const auto &arr = arrays[a];
    for (size_t q = 0; q < queries_per_array; ++q) {
      // Half hits, half random.
      uint16_t k = (q & 1u) ? arr[key_dist(rng) % arr.size()]
                            : (uint16_t)key_dist(rng);
      bool expected = std::binary_search(arr.begin(), arr.end(), k);
      check_one("simd_quad", simd_quad(arr.data(), (int32_t)arr.size(), k),
                expected, arr.size(), k);
#if QUADSEARCH_ARCH_ARM
      check_one("simd_quad_pi5",
                simd_quad_pi5(arr.data(), (int32_t)arr.size(), k),
                expected, arr.size(), k);
      check_one("simd_quad_m4",
                simd_quad_m4(arr.data(), (int32_t)arr.size(), k),
                expected, arr.size(), k);
      check_one("simd_quad_gv4",
                simd_quad_graviton(arr.data(), (int32_t)arr.size(), k),
                expected, arr.size(), k);
      if (array_size >= (size_t)PI5_GAP) {
        check_one("simd_quad_pi5_spine",
                  simd_quad_pi5_spine(arr.data(), spines_pi5[a].data(),
                                      (int32_t)arr.size(), k),
                  expected, arr.size(), k);
      }
      if (array_size >= (size_t)M4_GAP) {
        check_one("simd_quad_m4_spine",
                  simd_quad_m4_spine(arr.data(), spines_m4[a].data(),
                                     (int32_t)arr.size(), k),
                  expected, arr.size(), k);
      }
      if (array_size >= (size_t)GV4_GAP) {
        check_one("simd_quad_gv4_spine",
                  simd_quad_graviton_spine(arr.data(), spines_gv4[a].data(),
                                           (int32_t)arr.size(), k),
                  expected, arr.size(), k);
      }
      if (array_size == 4096) {
        check_one("simd_quad_pi5_spine_4096",
                  simd_quad_pi5_spine_4096(arr.data(), spines_pi5[a].data(), k),
                  expected, arr.size(), k);
        check_one("simd_quad_m4_spine_4096",
                  simd_quad_m4_spine_4096(arr.data(), spines_m4[a].data(), k),
                  expected, arr.size(), k);
        check_one("simd_quad_gv4_spine_4096",
                  simd_quad_graviton_spine_4096(arr.data(), spines_gv4[a].data(), k),
                  expected, arr.size(), k);
      }
#endif
#if QUADSEARCH_ARCH_X86
      check_one("simd_quad_intel",
                simd_quad_intel(arr.data(), (int32_t)arr.size(), k),
                expected, arr.size(), k);
      if (array_size >= (size_t)INTEL_GAP) {
        check_one("simd_quad_intel_spine",
                  simd_quad_intel_spine(arr.data(), spines_intel[a].data(),
                                        (int32_t)arr.size(), k),
                  expected, arr.size(), k);
      }
      if (array_size == 4096) {
        check_one("simd_quad_intel_spine_4096",
                  simd_quad_intel_spine_4096(arr.data(), spines_intel[a].data(), k),
                  expected, arr.size(), k);
      }
#endif
    }
  }

  if (mismatches > 0) {
    std::print("  n = {:>5}: FAIL — {} mismatches\n", array_size, mismatches);
    return false;
  }
  std::print("  n = {:>5}: ok ({} arrays × {} queries vs std::binary_search)\n",
             array_size, num_verify_arrays, queries_per_array);
  return true;
}

void collect_benchmark_results(size_t array_size, size_t number_arrays,
                               size_t warmth, bool run_cold, bool run_warm,
                               BenchResults &results) {
  if (array_size > 65536) array_size = 65536;

  std::mt19937_64 rng(0xC0FFEEull ^ array_size);

  std::vector<std::vector<uint16_t>> arrays;
  arrays.reserve(number_arrays);
  for (size_t a = 0; a < number_arrays; ++a) {
    arrays.push_back(make_sorted_unique(rng, array_size));
  }

#if QUADSEARCH_ARCH_ARM
  std::vector<std::vector<uint16_t>> spines_pi5(number_arrays);
  std::vector<std::vector<uint16_t>> spines_m4(number_arrays);
  std::vector<std::vector<uint16_t>> spines_gv4(number_arrays);
  for (size_t a = 0; a < number_arrays; ++a) {
    spines_pi5[a].resize(std::max<size_t>(1, array_size / PI5_GAP));
    spines_m4 [a].resize(std::max<size_t>(1, array_size / M4_GAP));
    spines_gv4[a].resize(std::max<size_t>(1, array_size / GV4_GAP));
    if (array_size >= (size_t)PI5_GAP)
      simd_quad_pi5_build_spine(arrays[a].data(), (int32_t)array_size, spines_pi5[a].data());
    if (array_size >= (size_t)M4_GAP)
      simd_quad_m4_build_spine (arrays[a].data(), (int32_t)array_size, spines_m4 [a].data());
    if (array_size >= (size_t)GV4_GAP)
      simd_quad_graviton_build_spine(arrays[a].data(), (int32_t)array_size, spines_gv4[a].data());
  }
#endif
#if QUADSEARCH_ARCH_X86
  std::vector<std::vector<uint16_t>> spines_intel(number_arrays);
  for (size_t a = 0; a < number_arrays; ++a) {
    spines_intel[a].resize(std::max<size_t>(1, array_size / INTEL_GAP));
    if (array_size >= (size_t)INTEL_GAP)
      simd_quad_intel_build_spine(arrays[a].data(), (int32_t)array_size, spines_intel[a].data());
  }
#endif

  size_t total = number_arrays * warmth;

  std::vector<size_t> indices_cold(total);
  for (size_t i = 0; i < total; ++i) indices_cold[i] = i % number_arrays;
  std::vector<size_t> indices_warm(total);
  for (size_t i = 0; i < total; ++i) indices_warm[i] = i / warmth;

  // Mix of half hits (key drawn from the targeted array) and half random.
  std::vector<uint16_t> keys(total);
  std::uniform_int_distribution<int> key_dist(0, 65535);
  for (size_t i = 0; i < total; ++i) {
    if (i & 1u) {
      const auto &a = arrays[indices_cold[i]];
      keys[i] = a[key_dist(rng) % a.size()];
    } else {
      keys[i] = (uint16_t)key_dist(rng);
    }
  }

  volatile uint64_t counter = 0;

  std::print("arrays: {}  size per array: {}  warmth: {}  total queries per mode: {}\n",
             number_arrays, array_size, warmth, total);

  // One generic driver: each algorithm is a callable (arr_idx, key) -> bool.
  auto bench_one = [&](const char *name, auto fn) {
    auto make = [&](const std::vector<size_t> &indices) {
      return [&arrays, &indices, &keys, &counter, fn]() {
        size_t c = 0;
        size_t n = indices.size();
        for (size_t i = 0; i < n; ++i) {
          if (fn(indices[i], keys[i])) ++c;
        }
        counter += c;
      };
    };
    auto run = [&](const char *mode, const std::vector<size_t> &indices) {
      auto agg = counters::bench(make(indices));
      double ns = agg.fastest_elapsed_ns() / double(total);
      double bm = counters::has_performance_counters()
                      ? agg.branch_misses() / double(total)
                      : -1.0;
      pretty_print(name, mode, total, agg);
      results.add(name, mode, array_size, ns, bm);
    };
    if (run_cold) run("cold", indices_cold);
    if (run_warm) run("warm", indices_warm);
  };

  bench_one("std::binary_search", [&](size_t i, uint16_t k) {
    const auto &a = arrays[i];
    return std::binary_search(a.begin(), a.end(), k);
  });
  bench_one("simd_quad", [&](size_t i, uint16_t k) {
    const auto &a = arrays[i];
    return simd_quad(a.data(), (int32_t)a.size(), k);
  });

#if QUADSEARCH_ARCH_ARM
  bench_one("simd_quad_pi5", [&](size_t i, uint16_t k) {
    const auto &a = arrays[i];
    return simd_quad_pi5(a.data(), (int32_t)a.size(), k);
  });
  bench_one("simd_quad_m4", [&](size_t i, uint16_t k) {
    const auto &a = arrays[i];
    return simd_quad_m4(a.data(), (int32_t)a.size(), k);
  });
  bench_one("simd_quad_gv4", [&](size_t i, uint16_t k) {
    const auto &a = arrays[i];
    return simd_quad_graviton(a.data(), (int32_t)a.size(), k);
  });
  if (array_size >= (size_t)PI5_GAP) {
    bench_one("simd_quad_pi5_spine", [&](size_t i, uint16_t k) {
      const auto &a = arrays[i];
      return simd_quad_pi5_spine(a.data(), spines_pi5[i].data(),
                                 (int32_t)a.size(), k);
    });
  }
  if (array_size >= (size_t)M4_GAP) {
    bench_one("simd_quad_m4_spine", [&](size_t i, uint16_t k) {
      const auto &a = arrays[i];
      return simd_quad_m4_spine(a.data(), spines_m4[i].data(),
                                (int32_t)a.size(), k);
    });
  }
  if (array_size >= (size_t)GV4_GAP) {
    bench_one("simd_quad_gv4_spine", [&](size_t i, uint16_t k) {
      const auto &a = arrays[i];
      return simd_quad_graviton_spine(a.data(), spines_gv4[i].data(),
                                      (int32_t)a.size(), k);
    });
  }
  if (array_size == 4096) {
    bench_one("simd_quad_pi5_spine_4096", [&](size_t i, uint16_t k) {
      const auto &a = arrays[i];
      return simd_quad_pi5_spine_4096(a.data(), spines_pi5[i].data(), k);
    });
    bench_one("simd_quad_m4_spine_4096", [&](size_t i, uint16_t k) {
      const auto &a = arrays[i];
      return simd_quad_m4_spine_4096(a.data(), spines_m4[i].data(), k);
    });
    bench_one("simd_quad_gv4_spine_4096", [&](size_t i, uint16_t k) {
      const auto &a = arrays[i];
      return simd_quad_graviton_spine_4096(a.data(), spines_gv4[i].data(), k);
    });
  }
#endif
#if QUADSEARCH_ARCH_X86
  bench_one("simd_quad_intel", [&](size_t i, uint16_t k) {
    const auto &a = arrays[i];
    return simd_quad_intel(a.data(), (int32_t)a.size(), k);
  });
  if (array_size >= (size_t)INTEL_GAP) {
    bench_one("simd_quad_intel_spine", [&](size_t i, uint16_t k) {
      const auto &a = arrays[i];
      return simd_quad_intel_spine(a.data(), spines_intel[i].data(),
                                   (int32_t)a.size(), k);
    });
  }
  if (array_size == 4096) {
    bench_one("simd_quad_intel_spine_4096", [&](size_t i, uint16_t k) {
      const auto &a = arrays[i];
      return simd_quad_intel_spine_4096(a.data(), spines_intel[i].data(), k);
    });
  }
#endif
}

int main(int argc, char **argv) {
  size_t number_arrays = 10000;
  size_t warmth = 100;
  enum class Mode { Both, ColdOnly, WarmOnly };
  Mode mode = Mode::Both;
  std::vector<size_t> array_sizes = {8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096};
  for (int i = 1; i < argc; ++i) {
    std::string arg = argv[i];
    if (arg == "--number" && i + 1 < argc) {
      number_arrays = std::stoul(argv[++i]);
    } else if (arg == "--warmth" && i + 1 < argc) {
      warmth = std::stoul(argv[++i]);
    } else if (arg == "--cold") {
      mode = Mode::ColdOnly;
    } else if (arg == "--warm") {
      mode = Mode::WarmOnly;
    } else if (arg == "--lengths" && i + 1 < argc) {
      std::string lengths_str = argv[++i];
      array_sizes.clear();
      size_t pos = 0;
      while ((pos = lengths_str.find(',')) != std::string::npos) {
        array_sizes.push_back(std::stoul(lengths_str.substr(0, pos)));
        lengths_str.erase(0, pos + 1);
      }
      array_sizes.push_back(std::stoul(lengths_str));
    }
  }
  bool run_cold = (mode != Mode::WarmOnly);
  bool run_warm = (mode != Mode::ColdOnly);

  if (!counters::has_performance_counters()) {
#if defined(__APPLE__)
    std::print("[note] Performance counters unavailable. On macOS, kperf "
               "requires elevated privileges:\n"
               "       sudo ./benchmark ...\n"
               "       (cycles / instructions / branch-miss columns will "
               "be blank otherwise.)\n\n");
#elif defined(__linux__)
    std::print("[note] Performance counters unavailable. On Linux, "
               "perf_event_open requires either:\n"
               "       sudo ./benchmark ...\n"
               "       or relaxing kernel.perf_event_paranoid:\n"
               "       sudo sysctl -w kernel.perf_event_paranoid=0\n"
               "       (cycles / instructions / branch-miss columns will "
               "be blank otherwise.)\n\n");
#else
    std::print("[note] Performance counters unavailable on this platform; "
               "cycles / instructions / branch-miss columns will be blank.\n\n");
#endif
  }

  // Phase 1: correctness. Runs every algorithm vs std::binary_search on a
  // small independent data set per size, before any timing work.
  std::print("========== verification ==========\n");
  bool all_ok = true;
  for (size_t array_size : array_sizes) {
    if (!verify_at_size(array_size, /*num_verify_arrays=*/64,
                        /*queries_per_array=*/256)) {
      all_ok = false;
    }
  }
  if (!all_ok) {
    std::print("\nverification FAILED — aborting before benchmark.\n");
    return 1;
  }
  std::print("all algorithms agree with std::binary_search across all sizes.\n\n");

  // Phase 2: benchmark.
  std::print("========== benchmark ==========\n");
  BenchResults results;
  for (size_t array_size : array_sizes) {
    collect_benchmark_results(array_size, number_arrays, warmth,
                              run_cold, run_warm, results);
  }

  // Phase 3: summary tables.
  auto ns_extract = [](const Metrics &m) { return m.ns; };
  auto bm_extract = [](const Metrics &m) { return m.bm; };
  auto ns_fmt = [](double v) { return std::format("{:.2f}", v); };
  auto bm_fmt = [](double v) { return std::format("{:.3f}", v); };

  std::print("\n========== summary (markdown) ==========\n");
  if (run_cold && results.has_mode("cold"))
    print_markdown_table("cold", results, array_sizes,
                         "ns / query (lower is better)",
                         ns_extract, ns_fmt);
  if (run_warm && results.has_mode("warm"))
    print_markdown_table("warm", results, array_sizes,
                         "ns / query (lower is better)",
                         ns_extract, ns_fmt);

  if (counters::has_performance_counters()) {
    if (run_cold && results.has_mode("cold"))
      print_markdown_table("cold", results, array_sizes,
                           "branch misses / query (lower is better)",
                           bm_extract, bm_fmt);
    if (run_warm && results.has_mode("warm"))
      print_markdown_table("warm", results, array_sizes,
                           "branch misses / query (lower is better)",
                           bm_extract, bm_fmt);
  }
  return 0;
}

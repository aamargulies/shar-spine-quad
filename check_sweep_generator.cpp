// Lockstep check of the bench_sweep_f_vs_lem.cpp set-up generator.
//
// On 2026-10-12 make_sorted_u16 in bench_sweep_f_vs_lem.cpp switched from a
// std::set to a 65536-bit membership bitmap for its rejection sampling. The
// data of every sweep campaign (m4_runs/sweep_fvl_raw.txt, pi5_runs/
// sweep_fvl2_raw.txt, ...) are a deterministic function of (inner_n,
// num_sets) through that generator, so the switch is only admissible if the
// new generator makes exactly the same draws and keeps exactly the same
// values. This program runs both versions in lockstep through the harness's
// whole set-up sequence -- for each inner_n in a size list: num_sets times
// (512 keys, 512 containers of inner_n, 1024 targets) from the harness's
// seed -- and compares every array, every target draw and the final RNG
// state. Keep old_gen verbatim; new_gen must match make_sorted_u16.
//
// Build and run (any host; the std::set side takes ~20 min on a Pi 5 for the
// 179-size list at 100 sets):
//   g++ -O2 -std=c++20 check_sweep_generator.cpp -o check_sweep_generator
//   ./check_sweep_generator pi5_runs/sweep_n_list_f_vs_lem.txt 100
// Prints "arrays compared: N, mismatches: 0" and exits 0 when equivalent.
// 2026-10-12, Pi 5: arrays compared: 9182700, mismatches: 0.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <set>
#include <vector>
#include <fstream>

static std::vector<uint16_t> old_gen(std::mt19937 &rng, int n) {
    std::set<uint16_t> s;
    std::uniform_int_distribution<int> d(0, 65535);
    while ((int)s.size() < n) s.insert((uint16_t)d(rng));
    return std::vector<uint16_t>(s.begin(), s.end());
}
static std::vector<uint16_t> new_gen(std::mt19937 &rng, int n) {
    std::uniform_int_distribution<int> d(0, 65535);
    std::vector<uint64_t> bits(65536 / 64, 0);
    int count = 0;
    while (count < n) {
        unsigned v = (unsigned)d(rng);
        uint64_t m = 1ull << (v & 63u);
        if (!(bits[v >> 6] & m)) { bits[v >> 6] |= m; count++; }
    }
    std::vector<uint16_t> out;
    out.reserve(n);
    for (unsigned w = 0; w < bits.size(); w++) {
        uint64_t x = bits[w];
        while (x) { out.push_back((uint16_t)(w * 64u + (unsigned)__builtin_ctzll(x))); x &= x - 1; }
    }
    return out;
}
int main(int argc, char **argv) {
    if (argc < 2) {
        std::fprintf(stderr, "usage: %s <size list file> [num_sets=100]\n", argv[0]);
        return 2;
    }
    std::ifstream in(argv[1]);
    int inner_n, num_sets = argc > 2 ? atoi(argv[2]) : 100;
    long arrays = 0, mism = 0;
    while (in >> inner_n) {
        std::mt19937 a(0xB17F17), b(0xB17F17);
        for (int i = 0; i < num_sets; i++) {
            // make_set: keys then 512 containers
            if (old_gen(a, 512) != new_gen(b, 512)) mism++;
            arrays++;
            for (int c = 0; c < 512; c++) { if (old_gen(a, inner_n) != new_gen(b, inner_n)) mism++; arrays++; }
            // the harness then draws 1024 targets from the same rng; lockstep states must agree
            std::uniform_int_distribution<int> pc(0, 511), pe(0, inner_n - 1);
            std::uniform_int_distribution<uint32_t> pm(0, UINT32_MAX);
            for (int k = 0; k < 1024; k++) {
                if (k & 1) { if (pc(a) != pc(b) || pe(a) != pe(b)) mism++; }
                else if (pm(a) != pm(b)) mism++;
            }
        }
        if (a != b) { mism++; std::printf("rng state differs after inner_n=%d\n", inner_n); }
    }
    std::printf("arrays compared: %ld, mismatches: %ld\n", arrays, mism);
    return mism != 0;
}

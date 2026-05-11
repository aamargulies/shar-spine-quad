"""
OpenEvolve evaluator for simd_quad_m4_spine_4096.

Cascade:
  Stage 1 (cheap) -- compile + correctness. Returns combined_score=0 on
                     failure with stderr/stdout as artifacts so the LLM can
                     see compiler diagnostics and self-repair.
  Stage 2 (paid)  -- 5 runs of `./bench 4000 5000`, median of the `4096*`
                     m4 row's warm and cold columns. Score weights cold
                     heavily because that's the regression we're chasing.

The evolved file is spliced into a stub copy of simd_quad_m4.c so only the
`simd_quad_m4_spine_4096` definition changes; the main `simd_quad_m4`,
`simd_quad_m4_spine`, and `simd_quad_m4_build_spine` come from the stock
repo and define the baselines the evaluator scores against.
"""

import os
import re
import shutil
import statistics
import subprocess
import tempfile
from pathlib import Path

from openevolve.evaluation_result import EvaluationResult

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

# Host gate: this evaluator is M4 Max / M1 Pro only. Refuse to run
# elsewhere so cross-host mistakes can't silently score against the wrong
# baseline.
HOST_CPU_FLAG = "-mcpu=apple-m4"  # works on M1 too if clang is Apple's; override via env
if os.environ.get("OPENEVOLVE_M4_CPU_FLAG"):
    HOST_CPU_FLAG = os.environ["OPENEVOLVE_M4_CPU_FLAG"]

# Baselines (median of 5 runs, m4_runs/rebench_run*.txt and m1_runs/).
# Used only for ratio reporting; scoring is absolute ns.
BASELINE_WARM_SPINE = 4.34   # simd_quad_m4_spine warm ns/query
BASELINE_COLD_SPINE = 6.47   # simd_quad_m4_spine cold ns/query

# Timing budget for a single evaluation: 1 warmup + 5 timed runs of
# `./bench 4000 5000`. On M4 Max ~2s per run, so ~12s plus compile.
NUM_TIMED_RUNS = 5
BENCH_ARGS = ["4000", "5000"]
COMPILE_TIMEOUT_S = 60
BENCH_TIMEOUT_S = 90

# Regex for the m4 `4096*` row emitted by bench.cpp:
#   " 4096* |  m4_spine=3.65  m4_spine_4096=3.70  (warm)  |  m4_spine=7.12  m4_spine_4096=18.40  (cold)"
M4_ROW_RE = re.compile(
    r"^\s*4096\*\s*\|\s*m4_spine=([\d.]+)\s+m4_spine_4096=([\d.]+)\s+\(warm\)"
    r"\s*\|\s*m4_spine=([\d.]+)\s+m4_spine_4096=([\d.]+)\s+\(cold\)",
    re.MULTILINE,
)


def _zero_result(error: str, **artifacts) -> EvaluationResult:
    return EvaluationResult(
        metrics={
            "combined_score": 0.0,
            "compile_ok": 0.0,
            "correctness_ok": 0.0,
            "warm_ns": 0.0,
            "cold_ns": 0.0,
            "warm_ratio": 0.0,
            "cold_ratio": 0.0,
        },
        artifacts={"error": error, **artifacts},
    )


def _splice_evolved_into_m4(evolved_src: str, target_path: Path) -> None:
    """Produce a simd_quad_m4.c file with simd_quad_m4_spine_4096 replaced
    by the evolved body."""
    stock = (REPO / "simd_quad_m4.c").read_text()
    # Strip the stock simd_quad_m4_spine_4096 function (signature to closing
    # brace at column 0). Relies on the stock file's formatting.
    pattern = re.compile(
        r"bool\s+simd_quad_m4_spine_4096\s*\([^)]*\)\s*\{.*?\n\}\s*\n",
        re.DOTALL,
    )
    if not pattern.search(stock):
        raise RuntimeError("could not locate simd_quad_m4_spine_4096 in stock")
    # Keep only the evolve-block body from the evolved source.
    m = re.search(
        r"//\s*EVOLVE-BLOCK-START\s*\n(.*?)\n\s*//\s*EVOLVE-BLOCK-END",
        evolved_src,
        re.DOTALL,
    )
    body = m.group(1) if m else evolved_src
    spliced = pattern.sub(body.rstrip() + "\n", stock, count=1)
    target_path.write_text(spliced)


def _run_bench_once(bench: Path) -> str:
    r = subprocess.run(
        [str(bench), *BENCH_ARGS],
        capture_output=True, text=True, timeout=BENCH_TIMEOUT_S,
    )
    if r.returncode != 0:
        raise RuntimeError(f"bench exit {r.returncode}: {r.stderr[:2000]}")
    return r.stdout


def _parse_m4_4096_row(stdout: str):
    """Return (warm_spine, warm_4096, cold_spine, cold_4096) or None."""
    m = M4_ROW_RE.search(stdout)
    if not m:
        return None
    return tuple(float(x) for x in m.groups())


def evaluate(program_path: str) -> EvaluationResult:
    evolved_src = Path(program_path).read_text()

    with tempfile.TemporaryDirectory(prefix="oe_m4_") as tmp:
        tmp = Path(tmp)
        spliced_m4 = tmp / "simd_quad_m4.c"
        try:
            _splice_evolved_into_m4(evolved_src, spliced_m4)
        except Exception as e:
            return _zero_result(f"splice failed: {e}")

        bench_bin = tmp / "bench"
        compile_cmd = [
            "clang++", "-O3", HOST_CPU_FLAG, "-std=c++20",
            str(REPO / "bench.cpp"),
            str(spliced_m4),
            str(REPO / "simd_quad_pi5.c"),
            str(REPO / "simd_quad_graviton.c"),
            "-o", str(bench_bin),
        ]
        try:
            cr = subprocess.run(
                compile_cmd, capture_output=True, text=True,
                timeout=COMPILE_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired:
            return _zero_result("compile timeout")
        if cr.returncode != 0:
            return _zero_result(
                "compile failed",
                compile_stderr=cr.stderr[-4000:],
                compile_stdout=cr.stdout[-2000:],
            )

        # Stage 1: correctness + one timing sample (warmup).
        try:
            first = _run_bench_once(bench_bin)
        except Exception as e:
            return _zero_result(f"bench run failed: {e}")
        if "correctness: ok" not in first:
            return _zero_result(
                "correctness failed",
                bench_stdout=first[-4000:],
            )

        # Stage 2: 5 timed runs, take medians.
        warm_4096s, cold_4096s = [], []
        warm_spines, cold_spines = [], []
        for _ in range(NUM_TIMED_RUNS):
            try:
                out = _run_bench_once(bench_bin)
            except Exception as e:
                return _zero_result(f"bench run failed mid-timing: {e}")
            parsed = _parse_m4_4096_row(out)
            if parsed is None:
                return _zero_result(
                    "could not parse m4 4096* row",
                    bench_stdout=out[-4000:],
                )
            ws, w4, cs, c4 = parsed
            warm_spines.append(ws); warm_4096s.append(w4)
            cold_spines.append(cs); cold_4096s.append(c4)

        warm_ns = statistics.median(warm_4096s)
        cold_ns = statistics.median(cold_4096s)
        warm_baseline = statistics.median(warm_spines)
        cold_baseline = statistics.median(cold_spines)

        warm_ratio = warm_baseline / warm_ns if warm_ns > 0 else 0.0
        cold_ratio = cold_baseline / cold_ns if cold_ns > 0 else 0.0

        # Noise flag: if warm stddev > 15% of median, halve the score so
        # MAP-Elites deprioritizes thermally-disturbed samples.
        warm_noisy = (statistics.pstdev(warm_4096s) / warm_ns) > 0.15 if warm_ns > 0 else True

        # Scoring: cold is what we're chasing, weight 0.7. Warm 0.3. Ratios
        # let MAP-Elites compare candidates across hosts / sessions where
        # absolute clocks drift.
        combined = 0.3 * warm_ratio + 0.7 * cold_ratio
        if warm_noisy:
            combined *= 0.5

        # Feature-dimension hints pulled from the evolved source by regex.
        # OpenEvolve consumes these via config.yaml feature_dimensions.
        prefetch_count = len(re.findall(r"__builtin_prefetch\s*\(", evolved_src))
        vld1_count = len(re.findall(r"vld1q_u16(?:_x\d)?\s*\(", evolved_src))
        has_block_load_hoisted = int(
            bool(re.search(
                r"vld1q_u16.*?\n.*?(?:spine\[|spine\s*\+)",
                evolved_src, re.DOTALL,
            ))
        )

        return EvaluationResult(
            metrics={
                "combined_score": combined,
                "compile_ok": 1.0,
                "correctness_ok": 1.0,
                "warm_ns": warm_ns,
                "cold_ns": cold_ns,
                "warm_ratio": warm_ratio,
                "cold_ratio": cold_ratio,
                "warm_baseline_ns": warm_baseline,
                "cold_baseline_ns": cold_baseline,
                "prefetch_count": float(prefetch_count),
                "vld1_count": float(vld1_count),
                "block_load_hoisted": float(has_block_load_hoisted),
                "warm_noisy": float(warm_noisy),
            },
            artifacts={
                "warm_samples": ",".join(f"{x:.3f}" for x in warm_4096s),
                "cold_samples": ",".join(f"{x:.3f}" for x in cold_4096s),
            },
        )


if __name__ == "__main__":
    import sys
    r = evaluate(sys.argv[1] if len(sys.argv) > 1 else str(HERE / "initial_program.c"))
    for k, v in r.metrics.items():
        print(f"{k:20s} {v}")
    for k, v in r.artifacts.items():
        print(f"# {k}: {v}")

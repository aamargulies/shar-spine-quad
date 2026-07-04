#!/usr/bin/env python3
"""Plot the M4 Max F vs Lemire-reference sweep (1..8192) as a 2x2 mode-panel
figure plus a delta strip. Loads m4_fvl_sweep dict from m4_fvl_sweep_data.py.

Run on M4 Max with /opt/homebrew/bin/python3 (matplotlib lives there per
project memory note).
"""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "m4_fvl_sweep_data.py")
if not os.path.exists(DATA_PATH):
    sys.exit("m4_fvl_sweep_data.py not found; run m4_runs/compute_sweep_f_vs_lem.py "
             "and paste its m4_fvl_sweep block into m4_fvl_sweep_data.py")

ns = {}
exec(open(DATA_PATH).read(), ns)
sweep = ns["m4_fvl_sweep"]
NS = sorted(sweep.keys())

MODES  = ("hb", "hs", "cb", "cs")
TITLES = ("hot_bat", "hot_ser", "cold_bat", "cold_ser")

# Reference vertical: 4096 (designed-for max) and gap=64 (where the spine
# starts having entries).
GAP = 64
DESIGN_MAX = 4096

fig, axes = plt.subplots(2, 2, figsize=(13, 9), sharex=True)
for idx, (mode, title) in enumerate(zip(MODES, TITLES)):
    ax = axes[idx // 2][idx % 2]
    f_vals = [sweep[n][mode][0] for n in NS]
    l_vals = [sweep[n][mode][1] for n in NS]
    ax.plot(NS, f_vals, marker="o", markersize=2.5, linewidth=1.0,
            color="#d62728", label="F (Shar outer + general-n spine inner)")
    ax.plot(NS, l_vals, marker="s", markersize=2.5, linewidth=1.0,
            color="#1f77b4", label="Lem (bsearch outer + simd_quad, gap=16, no spine)")
    ax.axvline(GAP, color="grey", linewidth=0.7, linestyle=":", alpha=0.7)
    ax.axvline(DESIGN_MAX, color="grey", linewidth=0.7, linestyle="--", alpha=0.7)
    ax.set_xscale("log", base=2)
    ax.set_xticks([1, 8, 64, 256, 1024, 4096, 8192])
    ax.set_xticklabels(["1", "8", "64", "256", "1024", "4096", "8192"])
    ax.set_yscale("log")
    ax.set_title(f"M4 Max — {title}")
    ax.set_ylabel("ns / query")
    ax.grid(True, which="both", linestyle=":", alpha=0.4)
    ax.legend(loc="upper left", fontsize=8)
    if idx >= 2:
        ax.set_xlabel("inner_n (u16 elements)")
    # Annotate the two reference lines once per axis.
    ymin, ymax = ax.get_ylim()
    ax.text(GAP * 1.05, ymin * 1.5, "gap=64", fontsize=7, color="grey")
    ax.text(DESIGN_MAX * 1.05, ymin * 1.5, "n=4096\n(designed max)",
            fontsize=7, color="grey")

fig.suptitle(
    "F vs Lemire-reference sweep — Shar K=512 outer + general-n spine inner "
    "vs bsearch + simd_quad\n"
    "M4 Max, 5-run medians, 200 log-spaced n in [1, 8192], 4-mode harness "
    "(2026-05-20)",
    fontsize=11)
fig.tight_layout()
fig.savefig("bench_m4_sweep_f_vs_lem.png", dpi=130)
print("wrote bench_m4_sweep_f_vs_lem.png")

# Delta strip: F/Lem - 1 across n, all 4 modes overlaid. Negative = F faster.
fig2, ax2 = plt.subplots(figsize=(12, 5.5))
mode_colors = dict(hb="#1f77b4", hs="#ff7f0e", cb="#2ca02c", cs="#d62728")
for mode, title in zip(MODES, TITLES):
    deltas, xs = [], []
    for n in NS:
        f, lem = sweep[n][mode]
        if f and lem:
            deltas.append((f / lem - 1.0) * 100)
            xs.append(n)
    ax2.plot(xs, deltas, marker="o", markersize=2.5, linewidth=1.0,
             color=mode_colors[mode], label=title)
ax2.axhline(0, color="black", linewidth=0.7)
ax2.axvline(GAP, color="grey", linewidth=0.7, linestyle=":", alpha=0.7)
ax2.axvline(DESIGN_MAX, color="grey", linewidth=0.7, linestyle="--", alpha=0.7)
ax2.set_xscale("log", base=2)
ax2.set_xticks([1, 8, 64, 256, 1024, 4096, 8192])
ax2.set_xticklabels(["1", "8", "64", "256", "1024", "4096", "8192"])
ax2.set_xlabel("inner_n (u16 elements)")
ax2.set_ylabel("F vs Lem (% change in ns/query, negative = F faster)")
ax2.set_title("F vs Lem speedup across n — M4 Max")
ax2.grid(True, which="both", linestyle=":", alpha=0.4)
ax2.legend(loc="lower left", fontsize=9)
ax2.text(GAP * 1.05, ax2.get_ylim()[1] * 0.92, "gap=64", fontsize=8, color="grey")
ax2.text(DESIGN_MAX * 1.05, ax2.get_ylim()[1] * 0.92, "n=4096", fontsize=8, color="grey")
fig2.tight_layout()
fig2.savefig("bench_m4_sweep_f_vs_lem_delta.png", dpi=130)
print("wrote bench_m4_sweep_f_vs_lem_delta.png")

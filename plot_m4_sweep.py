#!/usr/bin/env python3
"""Plot the M4 Max F vs F* sweep as a 2x2 mode-panel figure plus a delta
strip. Reads m4_sweep dict from a separate data file so we can iterate
quickly without round-tripping plot.py.

Once the sweep is final and findings written, the m4_sweep dict and this
plotting function should be folded into plot.py to match the rest of the
project.

Run on M4 Max with /opt/homebrew/bin/python3 (matplotlib lives there per
project memory note).
"""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

# Lazy-load the dict from m4_sweep_data.py if present, else expect compute_sweep
# to be run first.
DATA_PATH = os.path.join(HERE, "m4_sweep_data.py")
if not os.path.exists(DATA_PATH):
    sys.exit("m4_sweep_data.py not found; run compute_sweep.py and paste its "
             "m4_sweep block into m4_sweep_data.py")

ns = {}
exec(open(DATA_PATH).read(), ns)
m4_sweep = ns["m4_sweep"]
NS = sorted(m4_sweep.keys())

MODES   = ("hb", "hs", "cb", "cs")
TITLES  = ("hot_bat", "hot_ser", "cold_bat", "cold_ser")

fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
for idx, (mode, title) in enumerate(zip(MODES, TITLES)):
    ax = axes[idx // 2][idx % 2]
    f_vals  = [m4_sweep[n][mode][0] for n in NS]
    fs_vals = [m4_sweep[n][mode][1] for n in NS]
    ax.plot(NS, f_vals,  marker="o", markersize=3, linewidth=1.2,
            color="#d62728", label="F (Shar outer + general-n inner)")
    ax.plot(NS, fs_vals, marker="s", markersize=3, linewidth=1.2,
            color="#1f77b4", label="F* (Shar outer + compile-time-n inner)")
    ax.set_xscale("log", base=2)
    ax.set_xticks([64, 128, 256, 512, 1024, 2048, 4096])
    ax.set_xticklabels(["64", "128", "256", "512", "1024", "2048", "4096"])
    ax.set_yscale("log")
    ax.set_title(f"M4 Max — {title}")
    ax.set_ylabel("ns / query")
    ax.grid(True, which="both", linestyle=":", alpha=0.4)
    ax.legend(loc="upper left", fontsize=8)
    if idx >= 2:
        ax.set_xlabel("inner_n (u16 elements)")

fig.suptitle(
    "F vs F* sweep — Shar K=512 outer, inner search general-n vs compile-time-n\n"
    "M4 Max, 5-run medians, 90 log-spaced n values, 4-mode harness",
    fontsize=11)
fig.tight_layout()
fig.savefig("bench_m4_sweep.png", dpi=130)
print("wrote bench_m4_sweep.png")

# Delta strip: F*/F - 1 across n, all 4 modes overlaid.
fig2, ax2 = plt.subplots(figsize=(11, 5))
mode_colors = dict(hb="#1f77b4", hs="#ff7f0e", cb="#2ca02c", cs="#d62728")
for mode, title in zip(MODES, TITLES):
    deltas = []
    xs = []
    for n in NS:
        f, fs = m4_sweep[n][mode]
        if f and fs:
            deltas.append((fs / f - 1.0) * 100)
            xs.append(n)
    ax2.plot(xs, deltas, marker="o", markersize=3, linewidth=1.2,
             color=mode_colors[mode], label=title)
ax2.axhline(0, color="black", linewidth=0.7)
ax2.set_xscale("log", base=2)
ax2.set_xticks([64, 128, 256, 512, 1024, 2048, 4096])
ax2.set_xticklabels(["64", "128", "256", "512", "1024", "2048", "4096"])
ax2.set_xlabel("inner_n (u16 elements)")
ax2.set_ylabel("F* vs F (% change in ns/query)")
ax2.set_title("F* (compile-time-n inner) vs F (general-n inner) — % change, M4 Max")
ax2.grid(True, which="both", linestyle=":", alpha=0.4)
ax2.legend(loc="lower right", fontsize=9)
fig2.tight_layout()
fig2.savefig("bench_m4_sweep_delta.png", dpi=130)
print("wrote bench_m4_sweep_delta.png")

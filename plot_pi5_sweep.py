#!/usr/bin/env python3
"""Plot the Pi 5 (Cortex-A76) F vs F* sweep as a 2x2 mode-panel figure plus
a delta strip. Mirror of plot_m4_sweep.py with Pi 5 host title + data file.

Once the sweep is final and findings written, the pi5_sweep dict and this
plotting function should be folded into plot.py to match the rest of the
project.

Run on the Pi 5 host with /usr/local/bin/python3 (matplotlib provided by the
system Python).
"""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(HERE, "pi5_sweep_data.py")
if not os.path.exists(DATA_PATH):
    sys.exit("pi5_sweep_data.py not found; run pi5_runs/compute_sweep.py and "
             "paste its pi5_sweep block into pi5_sweep_data.py")

ns = {}
exec(open(DATA_PATH).read(), ns)
pi5_sweep = ns["pi5_sweep"]
NS = sorted(pi5_sweep.keys())

MODES   = ("hb", "hs", "cb", "cs")
TITLES  = ("hot_bat", "hot_ser", "cold_bat", "cold_ser")

fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
for idx, (mode, title) in enumerate(zip(MODES, TITLES)):
    ax = axes[idx // 2][idx % 2]
    f_vals  = [pi5_sweep[n][mode][0] for n in NS]
    fs_vals = [pi5_sweep[n][mode][1] for n in NS]
    ax.plot(NS, f_vals,  marker="o", markersize=3, linewidth=1.2,
            color="#d62728", label="F (Shar outer + general-n inner)")
    ax.plot(NS, fs_vals, marker="s", markersize=3, linewidth=1.2,
            color="#1f77b4", label="F* (Shar outer + compile-time-n inner)")
    ax.set_xscale("log", base=2)
    ax.set_xticks([64, 128, 256, 512, 1024, 2048, 4096])
    ax.set_xticklabels(["64", "128", "256", "512", "1024", "2048", "4096"])
    ax.set_yscale("log")
    ax.set_title(f"Pi 5 (Cortex-A76) -- {title}")
    ax.set_ylabel("ns / query")
    ax.grid(True, which="both", linestyle=":", alpha=0.4)
    ax.legend(loc="upper left", fontsize=8)
    if idx >= 2:
        ax.set_xlabel("inner_n (u16 elements)")

fig.suptitle(
    "F vs F* sweep -- Shar K=512 outer, inner search general-n vs compile-time-n\n"
    "Pi 5 (Cortex-A76), 5-run medians, 90 log-spaced n values, 4-mode harness "
    "(100 sets x 200 hot reps)",
    fontsize=11)
fig.tight_layout()
fig.savefig("bench_pi5_sweep.png", dpi=130)
print("wrote bench_pi5_sweep.png")

fig2, ax2 = plt.subplots(figsize=(11, 5))
mode_colors = dict(hb="#1f77b4", hs="#ff7f0e", cb="#2ca02c", cs="#d62728")
for mode, title in zip(MODES, TITLES):
    deltas = []
    xs = []
    for n in NS:
        f, fs = pi5_sweep[n][mode]
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
ax2.set_title("F* (compile-time-n inner) vs F (general-n inner) -- "
              "% change, Pi 5 (Cortex-A76)")
ax2.grid(True, which="both", linestyle=":", alpha=0.4)
ax2.legend(loc="lower right", fontsize=9)
fig2.tight_layout()
fig2.savefig("bench_pi5_sweep_delta.png", dpi=130)
print("wrote bench_pi5_sweep_delta.png")

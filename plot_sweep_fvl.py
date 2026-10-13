#!/usr/bin/env python3
"""Plot a paired F-vs-Lemire sweep campaign from its data module.

Usage (from the repo root):

    python3 plot_sweep_fvl.py HOST [--prefix PREFIX] [--data FILE] [--outdir DIR] [--dpi N]

Reads HOST_PREFIX_data.py, written by compute_sweep_fvl.py (default prefix
sweep_fvl2; the archived M4 campaign is sweep_fvl), and writes

    bench_HOST_PREFIX.png        levels: 2x2 mode panels, ns/query (log) vs
                                 inner_n (log2) for every variant present (F,
                                 Lem, Lem2, and from the 2026-10-12 harness Fb
                                 and LemS), with the host's gap and n=4096 marked
    bench_HOST_PREFIX_delta.png  paired median deltas vs inner_n, one panel per
                                 mode, one line per Lemire-vs-F pair (Lem vs F,
                                 Lem2 vs F, Lem2 vs Lem); WIN cells are filled
                                 markers, TIE and n/a cells hollow; negative =
                                 the first-named variant of the pair is faster
    bench_HOST_PREFIX_factorial.png
                                 only when the outer x inner cross variants are
                                 present: the four single-factor pairs (Fb vs F
                                 and Lem vs LemS = bsearch outer vs Shar outer;
                                 Fb vs Lem and F vs LemS = spine inner vs Lemire
                                 inner), one column per mode, top row paired
                                 median deltas in percent, bottom row the same
                                 deltas in ns (a cost that lives in the outer
                                 search is a flat line there)

Examples:
    python3 plot_sweep_fvl.py m4 --prefix sweep_fvl   -> bench_m4_sweep_fvl.png, bench_m4_sweep_fvl_delta.png
    python3 plot_sweep_fvl.py pi5                     -> bench_pi5_sweep_fvl2.png, bench_pi5_sweep_fvl2_delta.png
    python3 plot_sweep_fvl.py pi5 --prefix sweep_fvl3 -> bench_pi5_sweep_fvl3.png, _delta.png, _factorial.png

Uses matplotlib's Agg backend like plot.py. Run it under nice/taskset while
a campaign is running on the host.
"""
import argparse
import importlib.util
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

# One hue per entity, assigned in a fixed order (never cycled): F blue, Lem
# orange, Lem2 aqua, Fb purple, LemS brown; the Lemire-vs-F pairs reuse the
# first three slots in the same order. The first three validate as a set for
# colour-vision deficiency (dataviz skill validator, --pairs all); the
# factorial figure keeps its four pairs apart by marker as well as hue.
COLORS = {"F": "#2a78d6", "Lem": "#eb6834", "Lem2": "#199e70", "Fb": "#8e44ad", "LemS": "#8c6d31"}
MARKERS = {"F": "o", "Lem": "s", "Lem2": "^", "Fb": "D", "LemS": "v"}
PAIR_COLORS = {"Lem vs F": "#2a78d6", "Lem2 vs F": "#eb6834", "Lem2 vs Lem": "#199e70",
               "Fb vs F": "#8e44ad", "Lem vs LemS": "#d35fb7", "Fb vs Lem": "#0e7c7b", "F vs LemS": "#7f8c1d"}
PAIR_MARKERS = {"Lem vs F": "o", "Lem2 vs F": "s", "Lem2 vs Lem": "^",
                "Fb vs F": "D", "Lem vs LemS": "d", "Fb vs Lem": "v", "F vs LemS": "P"}
# The single-factor contrasts of the {Shar, bsearch} outer x {spine, Lemire}
# inner square (Fb = bsearch + spine, LemS = Shar + Lemire). Everything else
# in PAIRS goes to the _delta figure.
FACTORIAL_PAIRS = ("Fb vs F", "Lem vs LemS", "Fb vs Lem", "F vs LemS")
FACTORIAL_LABEL = {
    "Fb vs F": "outer: bsearch vs Shar, spine inner (Fb/F - 1)",
    "Lem vs LemS": "outer: bsearch vs Shar, Lemire inner (Lem/LemS - 1)",
    "Fb vs Lem": "inner: spine vs Lemire, bsearch outer (Fb/Lem - 1)",
    "F vs LemS": "inner: spine vs Lemire, Shar outer (F/LemS - 1)",
}
DEFAULT_DESC = {
    "F": "Shar outer + host spine inner",
    "Lem": "bsearch outer + simd_quad (Lemire, 2026-04-27)",
    "Lem2": "bsearch outer + simd_quad_2026_10 (Lemire, 2026-10-02)",
    "Fb": "bsearch outer + host spine inner (two-level A)",
    "LemS": "Shar outer + simd_quad (Lemire, 2026-04-27)",
}
XTICKS = [1, 8, 64, 256, 1024, 4096, 8192]
GRID = dict(color="#b8b7b2", linestyle=":", linewidth=0.6, alpha=0.6)
REF = dict(color="#8a8984", linewidth=0.8, alpha=0.9)


def load_module(path):
    spec = importlib.util.spec_from_file_location("sweep_fvl_data", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def style_axis(ax, sizes, gap, bottom):
    ax.set_xscale("log", base=2)
    ticks = [t for t in XTICKS if t <= max(sizes) * 1.1 and t >= min(sizes) / 1.1] or XTICKS
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(t) for t in ticks])
    ax.grid(True, which="major", **GRID)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    if gap:
        ax.axvline(gap, linestyle=":", **REF)
    if min(sizes) <= 4096 <= max(sizes):
        ax.axvline(4096, linestyle="--", **REF)
    if bottom:
        ax.set_xlabel("inner_n (u16 elements per container)")


def annotate_refs(ax, gap, y, sizes):
    if gap:
        ax.text(gap * 1.06, y, f"gap={gap}", fontsize=7, color="#52514e", va="top")
    if min(sizes) <= 4096 <= max(sizes):
        ax.text(4096 * 1.06, y, "n=4096", fontsize=7, color="#52514e", va="top")


def campaign_line(d):
    bits = [f"{len(d.RUNS)} run(s)", f"{len(d.SIZES)} sizes n={min(d.SIZES)}..{max(d.SIZES)}", f"campaign '{d.PREFIX}'"]
    dr = d.META.get("date_range")
    if dr:
        bits.append(f"{dr[0][:10]}" + (f" .. {dr[1][:10]}" if dr[1][:10] != dr[0][:10] else ""))
    gov = d.META.get("governors")
    if gov:
        bits.append("governor " + "/".join(gov))
    missing = d.META.get("cells_missing", 0)
    if missing:
        bits.append(f"{missing} of {d.META.get('cells_expected')} cells missing")
    return "; ".join(bits)


def plot_levels(d, out, dpi):
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), sharex=True)
    desc = dict(DEFAULT_DESC)
    desc.update(d.VARIANT_DESC or {})
    for idx, mode in enumerate(d.MODES):
        ax = axes[idx // 2][idx % 2]
        plotted = False
        for v in d.VARIANTS:
            xs = [N for N in d.SIZES if d.LEVELS[N][mode].get(v) is not None]
            ys = [d.LEVELS[N][mode][v] for N in xs]
            if xs:
                plotted = True
                ax.plot(xs, ys, marker=MARKERS.get(v, "o"), markersize=3.2, linewidth=1.4,
                        color=COLORS.get(v, "#52514e"), label=f"{v}: {desc.get(v, v)}")
        if not plotted:
            ax.text(0.5, 0.72, "no cells for this mode yet", transform=ax.transAxes,
                    ha="center", va="center", fontsize=10, color="#52514e")
        ax.set_yscale("log")
        ax.set_title(f"{d.HOST_LABEL} - {d.MODE_NAMES[mode]}", fontsize=11, loc="left")
        ax.set_ylabel("ns / query (per-cell median, log)")
        style_axis(ax, d.SIZES, d.GAP, bottom=idx >= 2)
        ymin, ymax = ax.get_ylim()
        annotate_refs(ax, d.GAP, ymax / 1.08, d.SIZES)
        if idx == 0:
            ax.legend(loc="upper left", fontsize=8, frameon=False)
    fig.suptitle(f"F vs Lemire sweep - {d.HOST_LABEL} - levels (per-cell medians over runs; "
                 f"compare variants with the paired deltas, not here)\n{campaign_line(d)}", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out, dpi=dpi)
    plt.close(fig)


def draw_pairs(ax, d, mode, pairs, key="median"):
    """One line per pair on ax: key = 'median' (percent) or 'median_ns' (ns); WIN cells filled."""
    plotted = False
    for pair in pairs:
        pts = [(N, d.PAIRED[N][mode][pair]) for N in d.SIZES if d.PAIRED[N][mode][pair].get(key) is not None]
        if not pts:
            continue
        plotted = True
        col = PAIR_COLORS.get(pair, "#52514e")
        mk = PAIR_MARKERS.get(pair, "o")
        ax.plot([p[0] for p in pts], [p[1][key] for p in pts], color=col, linewidth=1.1, alpha=0.85, zorder=2)
        win = [(N, st[key]) for N, st in pts if st["verdict"].startswith("WIN")]
        tie = [(N, st[key]) for N, st in pts if not st["verdict"].startswith("WIN")]
        if win:
            ax.scatter([p[0] for p in win], [p[1] for p in win], marker=mk, s=26, color=col,
                       edgecolors="white", linewidths=0.6, zorder=3)
        if tie:
            ax.scatter([p[0] for p in tie], [p[1] for p in tie], marker=mk, s=26, facecolors="white",
                       edgecolors=col, linewidths=1.0, zorder=3)
    return plotted


def verdict_handles(d):
    return [Line2D([0], [0], color="#0b0b0b", marker="o", markersize=6, linewidth=0,
                   label="filled: WIN (>= 80% of runs agree in sign and |median| >= 3%)"),
            Line2D([0], [0], color="#0b0b0b", marker="o", markersize=6, linewidth=0, markerfacecolor="white",
                   label=f"hollow: TIE, or n/a (fewer than {d.MIN_RUNS} paired runs); grey band = +/-3%")]


def plot_deltas(d, out, dpi, pairs):
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), sharex=True)
    for idx, mode in enumerate(d.MODES):
        ax = axes[idx // 2][idx % 2]
        ax.axhspan(-3, 3, color="#b8b7b2", alpha=0.18, linewidth=0)
        ax.axhline(0, color="#0b0b0b", linewidth=0.8)
        if not draw_pairs(ax, d, mode, pairs):
            ax.text(0.5, 0.72, "no paired cells for this mode yet", transform=ax.transAxes,
                    ha="center", va="center", fontsize=10, color="#52514e")
        ax.set_title(f"{d.HOST_LABEL} - {d.MODE_NAMES[mode]}", fontsize=11, loc="left")
        ax.set_ylabel("paired median delta, % (B/A - 1)")
        style_axis(ax, d.SIZES, d.GAP, bottom=idx >= 2)
        ymin, ymax = ax.get_ylim()
        annotate_refs(ax, d.GAP, ymax - 0.03 * (ymax - ymin), d.SIZES)

    handles = []
    for pair in pairs:
        b, _, a = pair.partition(" vs ")
        handles.append(Line2D([0], [0], color=PAIR_COLORS.get(pair, "#52514e"), marker=PAIR_MARKERS.get(pair, "o"),
                              markersize=6, linewidth=1.1, label=f"{pair}  ({b}/{a} - 1; below 0: {b} faster)"))
    handles += verdict_handles(d)
    fig.legend(handles=handles, loc="lower center", ncol=2, fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.0))
    fig.suptitle(f"F vs Lemire sweep - {d.HOST_LABEL} - paired per-run deltas, median over runs\n{campaign_line(d)}",
                 fontsize=11)
    fig.tight_layout(rect=(0, 0.07, 1, 0.95))
    fig.savefig(out, dpi=dpi)
    plt.close(fig)


def plot_factorial(d, out, dpi, pairs):
    """Outer x inner decomposition: percent (top) and ns (bottom) paired deltas, one column per mode."""
    fig, axes = plt.subplots(2, 4, figsize=(17, 8.5), sharex=True)
    has_ns = any(d.PAIRED[N][mode][p].get("median_ns") is not None
                 for N in d.SIZES for mode in d.MODES for p in pairs)
    for col, mode in enumerate(d.MODES):
        for row, key in enumerate(("median", "median_ns")):
            ax = axes[row][col]
            if key == "median":
                ax.axhspan(-3, 3, color="#b8b7b2", alpha=0.18, linewidth=0)
            ax.axhline(0, color="#0b0b0b", linewidth=0.8)
            drawn = draw_pairs(ax, d, mode, pairs, key=key) if (key == "median" or has_ns) else False
            if not drawn:
                ax.text(0.5, 0.72, "no data" if key == "median" or has_ns else "data module predates median_ns",
                        transform=ax.transAxes, ha="center", va="center", fontsize=10, color="#52514e")
            if row == 0:
                ax.set_title(f"{d.MODE_NAMES[mode]}", fontsize=11, loc="left")
            ax.set_ylabel("paired median delta, % (B/A - 1)" if key == "median" else "paired median delta, ns (B - A)")
            style_axis(ax, d.SIZES, d.GAP, bottom=row == 1)
            ymin, ymax = ax.get_ylim()
            annotate_refs(ax, d.GAP, ymax - 0.03 * (ymax - ymin), d.SIZES)
    handles = []
    for pair in pairs:
        handles.append(Line2D([0], [0], color=PAIR_COLORS.get(pair, "#52514e"), marker=PAIR_MARKERS.get(pair, "o"),
                              markersize=6, linewidth=1.1,
                              label=f"{pair}: {FACTORIAL_LABEL.get(pair, pair)}; below 0: {pair.partition(' vs ')[0]} faster"))
    handles += verdict_handles(d)
    fig.legend(handles=handles, loc="lower center", ncol=2, fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.0))
    fig.suptitle(f"Outer x inner decomposition - {d.HOST_LABEL} - paired per-run deltas, median over runs "
                 f"(top: percent; bottom: ns -- a cost in the outer search is flat in ns across sizes)\n{campaign_line(d)}",
                 fontsize=11)
    fig.tight_layout(rect=(0, 0.09, 1, 0.94))
    fig.savefig(out, dpi=dpi)
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("host")
    ap.add_argument("--prefix", default="sweep_fvl2")
    ap.add_argument("--data", help="data module (default HOST_PREFIX_data.py)")
    ap.add_argument("--outdir", default=".", help="where to write the PNGs (default: cwd)")
    ap.add_argument("--dpi", type=int, default=110)
    args = ap.parse_args(argv)

    data_path = args.data or f"{args.host}_{args.prefix}_data.py"
    if not os.path.exists(data_path):
        sys.exit(f"{data_path} not found; run compute_sweep_fvl.py {args.host} --prefix {args.prefix} first")
    d = load_module(data_path)
    if not d.SIZES:
        sys.exit(f"{data_path} holds no sizes")

    base = os.path.join(args.outdir, f"bench_{args.host}_{args.prefix}")
    plot_levels(d, base + ".png", args.dpi)
    print(f"wrote {base}.png")
    factorial = [p for p in FACTORIAL_PAIRS if p in d.PAIRS]
    plot_deltas(d, base + "_delta.png", args.dpi, [p for p in d.PAIRS if p not in FACTORIAL_PAIRS])
    print(f"wrote {base}_delta.png")
    if factorial:
        plot_factorial(d, base + "_factorial.png", args.dpi, factorial)
        print(f"wrote {base}_factorial.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())

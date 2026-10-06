#!/usr/bin/env python3
"""Membuat diagram & grafik (PNG, hitam-putih/abu-abu, font serif) untuk laporan dari folder results/."""
import csv
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch  # noqa: E402

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
    "font.size": 10,
    "axes.titlesize": 10,
    "legend.fontsize": 9,
})

RES, FIG = "results", "figures"
BLACK, DARK, MID, LIGHT, WHITE = "black", "#404040", "#9e9e9e", "#e6e6e6", "white"


def box(ax, x, y, w, h, text, fc=LIGHT, fs=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=fc, ec=BLACK, lw=1.0))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=BLACK, fontsize=fs, linespacing=1.3)


def arrow(ax, x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=12, lw=1.2, color=BLACK))


def read_csv(name):
    with open(os.path.join(RES, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pipeline():
    fig, ax = plt.subplots(figsize=(6.5, 2.2))
    ax.set_xlim(0, 10.2); ax.set_ylim(0, 2.4); ax.axis("off")
    steps = [
        "Dataset Teks\n(bigdata.txt)",
        "Baca Data\nsc.textFile()",
        "Preprocessing\nlower + regex\nflatMap()",
        "Transformation\nmap((w,1))\nreduceByKey()",
        "Action\nsortBy()\ntake(10)",
        "Hasil\n10 kata\nterbanyak",
    ]
    w, gap, x = 1.45, 0.3, 0.1
    for i, t in enumerate(steps):
        box(ax, x, 0.8, w, 1.3, t, fc=LIGHT if i not in (4,) else MID, fs=8)
        if i < len(steps) - 1:
            arrow(ax, x + w + 0.02, 1.45, x + w + gap - 0.02, 1.45)
        x += w + gap
    ax.text(0.1, 0.35, "Narrow: baca, flatMap, map   |   Wide (shuffle): reduceByKey, sortBy   |   Action memicu eksekusi",
            fontsize=8, color=BLACK)
    fig.tight_layout(pad=0.3)
    fig.savefig(os.path.join(FIG, "pipeline.png"), dpi=220)
    plt.close(fig)


def job_stage_task():
    with open(os.path.join(RES, "job_stage_task.json"), encoding="utf-8") as f:
        info = json.load(f)
    n = info["partitions"]
    shown = min(n, 3)
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 4.2); ax.axis("off")
    box(ax, 0.1, 1.7, 1.5, 0.8, "Action\nsortBy().take(10)", fc=MID, fs=8.5)
    box(ax, 2.1, 1.7, 1.5, 0.8, "Spark Job\n(dipicu Action)", fc=LIGHT, fs=8.5)
    arrow(ax, 1.62, 2.1, 2.08, 2.1)
    box(ax, 4.4, 2.7, 2.4, 1.0, "Stage 1 (ShuffleMap)\ntextFile, flatMap, map,\ncombine reduceByKey", fc=LIGHT, fs=8)
    box(ax, 4.4, 0.5, 2.4, 1.0, "Stage 2 (Result)\nreduceByKey (merge),\nsortBy, take", fc=MID, fs=8)
    arrow(ax, 3.62, 2.25, 4.38, 3.1)
    arrow(ax, 3.62, 1.95, 4.38, 1.1)
    arrow(ax, 5.6, 2.68, 5.6, 1.52)
    ax.text(5.72, 2.1, "shuffle", fontsize=8.5, style="italic")
    for k in range(shown):
        box(ax, 7.6, 3.45 - k * 0.5, 1.5, 0.38, f"Task {k + 1}", fc=WHITE, fs=8)
        box(ax, 7.6, 1.25 - k * 0.5, 1.5, 0.38, f"Task {k + 1}", fc=WHITE, fs=8)
    arrow(ax, 6.82, 3.2, 7.58, 3.55); arrow(ax, 6.82, 1.0, 7.58, 1.35)
    ax.text(7.6, 3.95, f"{n} task (1 per partition)", fontsize=8.5)
    ax.text(7.6, 0.1, f"{n} task (1 per partition)", fontsize=8.5)
    ax.text(0.1, 0.1, f"Catatan: sortBy().take() memicu {len(info.get('jobs', []))} job.", fontsize=8.5)
    fig.tight_layout(pad=0.3)
    fig.savefig(os.path.join(FIG, "job_stage_task.png"), dpi=220)
    plt.close(fig)


def partitions_chart():
    rows = read_csv("benchmark_partitions.csv")
    with open(os.path.join(RES, "benchmark_summary.json"), encoding="utf-8") as f:
        s = json.load(f)
    xs = [str(r["partitions"]) for r in rows]
    ys = [float(r["time_s"]) for r in rows]
    best = min(range(len(ys)), key=lambda i: ys[i])
    fig, ax = plt.subplots(figsize=(5.2, 2.9))
    bars = ax.bar(xs, ys, color=[DARK if i == best else MID for i in range(len(xs))], edgecolor=BLACK, linewidth=0.8)
    ax.axhline(s["python_time_s"], color=BLACK, ls="--", lw=1.3)
    for b, v in zip(bars, ys):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}", ha="center", va="bottom", fontsize=9)
    ax.set_xlabel("Jumlah partition"); ax.set_ylabel("Waktu eksekusi (detik)")
    ax.set_title("Pengaruh jumlah partition terhadap waktu eksekusi")
    ax.legend(handles=[Patch(fc=DARK, ec=BLACK, label="Waktu terbaik"),
                       Patch(fc=MID, ec=BLACK, label="Partition lain"),
                       plt.Line2D([0], [0], color=BLACK, ls="--", label=f"Python single machine ({s['python_time_s']:.2f} s)")],
              loc="upper left", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "partitions.png"), dpi=220); plt.close(fig)


def scaling_chart():
    rows = read_csv("benchmark_scaling.csv")
    xs = [int(r["lines"]) for r in rows]
    fig, ax = plt.subplots(figsize=(5.2, 2.9))
    ax.plot(xs, [float(r["python_s"]) for r in rows], "o-", color=BLACK, lw=1.5, label="Python single machine")
    ax.plot(xs, [float(r["spark_s"]) for r in rows], "s--", color=BLACK, lw=1.5, markerfacecolor=WHITE,
            label="PySpark (local[*])")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Jumlah baris data (skala log)"); ax.set_ylabel("Waktu (detik, skala log)")
    ax.set_title("Single machine vs Spark berdasarkan ukuran data")
    ax.legend(frameon=False); ax.grid(alpha=0.3, color=MID); ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "scaling.png"), dpi=220); plt.close(fig)


def breakdown_chart():
    with open(os.path.join(RES, "benchmark_summary.json"), encoding="utf-8") as f:
        b = json.load(f)["breakdown"]
    fig, ax = plt.subplots(figsize=(5.2, 2.6))
    ax.barh(["sortBy + take"], [b["read_map_s"]], color=MID, edgecolor=BLACK, label="Stage 1: baca + flatMap + map")
    ax.barh(["sortBy + take"], [b["reduce_sort_s"]], left=[b["read_map_s"]], color=DARK, edgecolor=BLACK,
            label="Shuffle, reduce, sort, take")
    ax.barh(["takeOrdered"], [b["total_takeordered_s"]], color=LIGHT, edgecolor=BLACK, hatch="//",
            label="takeOrdered (total)")
    ax.set_xlabel("Detik"); ax.set_title(f"Estimasi pembagian waktu (partition = {b['partitions']})")
    ax.legend(fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.38), ncol=2)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "breakdown.png"), dpi=220); plt.close(fig)


if __name__ == "__main__":
    os.makedirs(FIG, exist_ok=True)
    pipeline()
    job_stage_task()
    partitions_chart()
    scaling_chart()
    breakdown_chart()
    print("Diagram & grafik tersimpan di folder figures/")
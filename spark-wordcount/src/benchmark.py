#!/usr/bin/env python3
"""Benchmark: single machine vs Spark, pengaruh jumlah partition, skala data, bottleneck.

Pemakaian:
    python src/benchmark.py            # lengkap (beberapa menit)
    python src/benchmark.py --quick    # skala data lebih kecil
"""
import argparse
import csv
import json
import os
import re
import statistics
import sys
import time

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession  # noqa: E402

from common import machine_info, set_partitions  # noqa: E402
from generate_dataset import generate  # noqa: E402
from wordcount_single import top_n, wordcount  # noqa: E402


def tokenize(line):
    return re.findall(r"[a-z0-9]+", line.lower())


def key_fn(kv):
    return (-kv[1], kv[0])


def build_counts(sc, path, n):
    lines = set_partitions(sc.textFile(path, minPartitions=n), n)
    pairs = lines.flatMap(tokenize).map(lambda w: (w, 1))
    return pairs, pairs.reduceByKey(lambda x, y: x + y, numPartitions=n)


def timed(fn, reps):
    fn()  # warm-up (JVM, worker Python, cache OS)
    times, result = [], None
    for _ in range(reps):
        t = time.perf_counter()
        result = fn()
        times.append(time.perf_counter() - t)
    return statistics.median(times), result


def spark_session(master):
    spark = (SparkSession.builder.appName("WC-Benchmark").master(master)
             .config("spark.ui.enabled", "false")
             .config("spark.ui.showConsoleProgress", "false")
             .config("spark.driver.memory", "2g")
             .getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def write_csv(path, rows, header):
    with open(path, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(header)
        wr.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/bigdata.txt")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--outdir", default="results")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    cores = os.cpu_count() or 1
    summary = {}

    spark = spark_session("local[*]")
    sc = spark.sparkContext
    summary["machine"] = machine_info(spark.version)
    summary["default_parallelism"] = sc.defaultParallelism
    summary["input"] = a.input
    summary["input_lines"] = sum(1 for _ in open(a.input, encoding="utf-8"))
    summary["input_mb"] = round(os.path.getsize(a.input) / 1e6, 1)

    # ---- 1. Baseline single machine ----
    print("[1/5] Baseline single machine (Python murni)...")
    py_t, py_top = timed(lambda: top_n(wordcount(a.input)), a.reps)
    summary["python_time_s"] = py_t
    print(f"      {py_t:.3f} s")

    # ---- 2. Sweep jumlah partition ----
    print("[2/5] Pengaruh jumlah partition (local[*])...")
    parts = [1, 2, 4, 8, 16]
    rows, all_correct = [], True
    for n in parts:
        def job(n=n):
            _, counts = build_counts(sc, a.input, n)
            return counts.sortBy(key_fn).take(10)
        t, top = timed(job, a.reps)
        all_correct &= (top == py_top)
        rows.append([n, round(t, 4)])
        print(f"      partitions={n:<3} {t:.3f} s")
    write_csv(os.path.join(a.outdir, "benchmark_partitions.csv"), rows, ["partitions", "time_s"])
    summary["results_match_python"] = bool(all_correct)

    # ---- 3. Breakdown bottleneck pada partition terbaik ----
    best_n = min(rows, key=lambda r: r[1])[0]
    print(f"[3/5] Breakdown bottleneck (partitions={best_n})...")

    def stage1_only():
        pairs, _ = build_counts(sc, a.input, best_n)
        return pairs.count()                       # baca + flatMap + map (tanpa shuffle)

    def full_sortby():
        _, counts = build_counts(sc, a.input, best_n)
        return counts.sortBy(key_fn).take(10)

    def full_takeordered():
        _, counts = build_counts(sc, a.input, best_n)
        return counts.takeOrdered(10, key=key_fn)

    t_s1, _ = timed(stage1_only, a.reps)
    t_full, _ = timed(full_sortby, a.reps)
    t_take, _ = timed(full_takeordered, a.reps)
    summary["breakdown"] = {
        "partitions": best_n,
        "read_map_s": t_s1,
        "reduce_sort_s": max(t_full - t_s1, 0.0),
        "total_sortby_s": t_full,
        "total_takeordered_s": t_take,
    }
    print(f"      baca+map={t_s1:.3f}s  total(sortBy)={t_full:.3f}s  total(takeOrdered)={t_take:.3f}s")

    # ---- 4. Skala data: Python vs Spark ----
    sizes = [5_000, 50_000, 250_000] if a.quick else [5_000, 50_000, 250_000, 1_000_000]
    print("[4/5] Skala data (Python vs Spark)...")
    scale_rows = []
    par = max(sc.defaultParallelism, 2)
    for size in sizes:
        path = os.path.join("data", f"scale_{size}.txt")
        if not os.path.exists(path):
            generate(path, size)
        mb = os.path.getsize(path) / 1e6
        tp, _ = timed(lambda: top_n(wordcount(path)), a.reps)

        def sjob():
            _, counts = build_counts(sc, path, par)
            return counts.sortBy(key_fn).take(10)
        ts, _ = timed(sjob, a.reps)
        scale_rows.append([size, round(mb, 1), round(tp, 4), round(ts, 4)])
        print(f"      {size:>9,} baris ({mb:6.1f} MB): python={tp:.3f}s spark={ts:.3f}s")
    write_csv(os.path.join(a.outdir, "benchmark_scaling.csv"), scale_rows,
              ["lines", "size_mb", "python_s", "spark_s"])
    summary["scaling_partitions"] = par

    # ---- 5. Spark local[1] vs local[*] ----
    print("[5/5] Spark local[1] vs local[*]...")
    t_all = min(r[1] for r in rows if r[0] == max(cores, 1)) if any(r[0] == cores for r in rows) else min(r[1] for r in rows)
    spark.stop()
    spark1 = spark_session("local[1]")
    sc1 = spark1.sparkContext

    def job1():
        _, counts = build_counts(sc1, a.input, 1)
        return counts.sortBy(key_fn).take(10)
    t_one, _ = timed(job1, a.reps)
    spark1.stop()
    summary["spark_local1_s"] = t_one
    summary["spark_best_all_cores_s"] = min(r[1] for r in rows)
    summary["spark_best_partitions"] = best_n
    print(f"      local[1]={t_one:.3f}s  local[*] terbaik={summary['spark_best_all_cores_s']:.3f}s")

    with open(os.path.join(a.outdir, "benchmark_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("\nSelesai. Hasil tersimpan di folder results/")


if __name__ == "__main__":
    main()

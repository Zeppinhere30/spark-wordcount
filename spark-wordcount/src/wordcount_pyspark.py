#!/usr/bin/env python3
"""WordCount dengan PySpark (RDD API).

Alur: textFile -> flatMap(tokenize) -> map((w,1)) -> reduceByKey -> sortBy -> take(10)

Pemakaian:
    python src/wordcount_pyspark.py
    python src/wordcount_pyspark.py --partitions 8 --master "local[*]"
"""
import argparse
import csv
import json
import os
import re
import sys
import time

os.environ["PYSPARK_PYTHON"] = sys.executable          # samakan Python driver & worker
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession  # noqa: E402

from common import STOPWORDS, job_stage_task, machine_info, set_partitions  # noqa: E402


def tokenize(line):
    """Preprocessing: huruf kecil + buang tanda baca -> list kata."""
    return re.findall(r"[a-z0-9]+", line.lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/bigdata.txt")
    ap.add_argument("--partitions", type=int, default=8)
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--master", default="local[*]")
    ap.add_argument("--remove-stopwords", action="store_true")
    ap.add_argument("--outdir", default="results")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    # 1. Inisialisasi SparkSession
    spark = (SparkSession.builder
             .appName("WordCount")
             .master(a.master)
             .config("spark.ui.showConsoleProgress", "false")
             .getOrCreate())
    sc = spark.sparkContext
    sc.setLogLevel("ERROR")
    sc.setJobGroup("wordcount", "WordCount top-N")

    t0 = time.perf_counter()

    # 2. Membaca file teks (transformation, lazy)
    lines = set_partitions(sc.textFile(a.input, minPartitions=a.partitions), a.partitions)

    # 3. Preprocessing + WordCount (transformation, lazy)
    words = lines.flatMap(tokenize)
    if a.remove_stopwords:
        sw = sc.broadcast(STOPWORDS)
        words = words.filter(lambda w: w not in sw.value)
    pairs = words.map(lambda w: (w, 1))
    word_counts = pairs.reduceByKey(lambda x, y: x + y, numPartitions=a.partitions)

    # 4. Action -> memicu eksekusi (Job -> Stage -> Task)
    top = word_counts.sortBy(lambda kv: (-kv[1], kv[0])).take(a.top)
    elapsed = time.perf_counter() - t0

    sc.setJobGroup("validasi", "Hitung jumlah baris")   # job terpisah agar tidak bercampur dengan job WordCount
    total_lines = lines.count()
    print(f"\n=== {a.top} KATA TERBANYAK ===")
    for w, c in top:
        print(f"{w:<15}{c:>10,}")
    print(f"\nBaris data      : {total_lines:,}")
    print(f"Partition       : {a.partitions}")
    print(f"Master          : {a.master}")
    print(f"Waktu eksekusi  : {elapsed:.3f} detik")

    # 5. Simpan artefak untuk laporan
    with open(os.path.join(a.outdir, "top10.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["rank", "kata", "frekuensi"])
        for i, (w, c) in enumerate(top, 1):
            wr.writerow([i, w, c])
    jobs = [j for j in job_stage_task(sc, "wordcount")]
    with open(os.path.join(a.outdir, "job_stage_task.json"), "w", encoding="utf-8") as f:
        json.dump({"partitions": a.partitions, "jobs": jobs}, f, indent=2)
    with open(os.path.join(a.outdir, "lineage.txt"), "w", encoding="utf-8") as f:
        f.write(word_counts.toDebugString().decode("utf-8"))
    with open(os.path.join(a.outdir, "run_info.json"), "w", encoding="utf-8") as f:
        json.dump({"lines": total_lines, "partitions": a.partitions, "elapsed_s": elapsed,
                   "master": a.master, "machine": machine_info(spark.version)}, f, indent=2)

    # 6. Tutup SparkSession
    spark.stop()


if __name__ == "__main__":
    main()

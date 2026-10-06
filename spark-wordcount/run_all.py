#!/usr/bin/env python3
"""Jalankan seluruh pipeline: dataset -> WordCount -> benchmark -> diagram -> laporan PDF.

    python run_all.py            # lengkap
    python run_all.py --quick    # skala data lebih kecil (lebih cepat)
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
quick = ["--quick"] if "--quick" in sys.argv else []

steps = [
    ("Membuat dataset", ["src/generate_dataset.py"] if not os.path.exists(os.path.join(ROOT, "data/bigdata.txt")) else None),
    ("WordCount PySpark", ["src/wordcount_pyspark.py"]),
    ("Benchmark", ["src/benchmark.py"] + quick),
    ("Diagram & grafik", ["src/make_diagrams.py"]),
    ("Laporan PDF", ["src/make_report.py"]),
]
for i, (name, cmd) in enumerate(steps, 1):
    if cmd is None:
        print(f"[{i}/{len(steps)}] {name}: sudah ada, dilewati")
        continue
    print(f"\n[{i}/{len(steps)}] {name}")
    subprocess.run([sys.executable] + cmd, cwd=ROOT, check=True)
print("\nSelesai. Cek folder results/, figures/, dan report/")

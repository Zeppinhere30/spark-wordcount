# WordCount dengan PySpark: Big Data

Tugas Individu: implementasi WordCount dengan PySpark, diagram Job/Stage/Task, perbandingan
single machine vs distributed, analisis jumlah partition, dan laporan PDF.

## Struktur
```
spark-wordcount/
├── data/bigdata.txt              # dataset (100.000 baris, dibuat generate_dataset.py)
├── src/
│   ├── generate_dataset.py       # pembuat dataset teks sintetis
│   ├── wordcount_pyspark.py      # IMPLEMENTASI UTAMA (PySpark RDD)
│   ├── wordcount_single.py       # pembanding single machine (Python murni)
│   ├── benchmark.py              # partition, skala data, bottleneck, local[1] vs local[*]
│   ├── make_diagrams.py          # diagram pipeline, Job-Stage-Task, grafik
│   ├── make_report.py            # laporan PDF otomatis
│   └── common.py
├── results/                      # CSV/JSON hasil eksekusi
├── figures/                      # PNG untuk laporan
├── report/                       # Laporan_WordCount_PySpark.pdf
├── run_all.py                    # jalankan semua langkah
└── requirements.txt
```

## Prasyarat
- Python 3.9+
- **Java 17 atau 21** (wajib untuk Spark). Cek: `java -version`
- Windows: pastikan `JAVA_HOME` terisi dan Java ada di PATH

## Cara menjalankan
```bash
python -m venv .venv
# Windows : .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt

python run_all.py            # semua langkah (benchmark lengkap)
python run_all.py --quick    # versi cepat
```

Atau per langkah:
```bash
python src/generate_dataset.py                 # opsional: --lines 5000 --out data/sample_5000.txt
python src/wordcount_pyspark.py --partitions 8
python src/wordcount_single.py
python src/benchmark.py
python src/make_diagrams.py
python src/make_report.py
```

Sebelum `make_report.py`, edit blok IDENTITAS di bagian atas `src/make_report.py`.

## Catatan metodologi
- Spark berjalan dalam mode `local[*]` (semua core satu mesin), bukan cluster multi-node.
- Waktu = median 3 kali jalan setelah 1 kali warm-up.
- Hasil top-10 Spark diverifikasi otomatis sama dengan hasil Python murni.
- Laporan dibuat dari angka hasil eksekusi di mesin yang menjalankan `run_all.py`.

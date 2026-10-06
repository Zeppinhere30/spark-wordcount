#!/usr/bin/env python3
"""Membuat dataset teks sintetis (distribusi kata ala Zipf) untuk WordCount.

Pemakaian:
    python src/generate_dataset.py                       # 100.000 baris -> data/bigdata.txt
    python src/generate_dataset.py --lines 5000 --out data/sample_5000.txt
"""
import argparse
import itertools
import os
import random

FUNCTION_WORDS = (
    "yang dan di ke dari untuk dengan pada ini itu adalah dalam tidak akan juga "
    "atau oleh sebagai karena dapat"
).split()

CONTENT_WORDS = (
    "data spark proses paralel sistem komputer jaringan node cluster memori waktu "
    "kinerja analisis partisi tugas hasil kata teks baris file aplikasi algoritma "
    "distribusi skala server mesin pengguna informasi model belajar program kode "
    "tahap stage task job shuffle transformasi aksi eksekusi performa efisien "
    "penyimpanan komputasi terdistribusi pemrosesan dataset frekuensi kelompok "
    "gabungan urutan pembacaan penulisan sumber daya inti prosesor beban kerja "
    "toleransi kegagalan replikasi cadangan penjadwalan antrean penyeimbang"
).split()

SYLLABLES = ["ba", "ka", "ri", "to", "mu", "ne", "so", "la", "pi", "du", "ge", "xa", "ve", "zi", "ho"]


def build_vocab(tail_size=3000, seed=7):
    rng = random.Random(seed)
    tail = set()
    while len(tail) < tail_size:
        tail.add("".join(rng.choice(SYLLABLES) for _ in range(rng.randint(2, 4))))
    base = set(FUNCTION_WORDS) | set(CONTENT_WORDS)
    tail = sorted(t for t in tail if t not in base)
    return FUNCTION_WORDS + CONTENT_WORDS + tail


def generate(path, lines, seed=42, zipf_s=1.05):
    vocab = build_vocab()
    weights = [1.0 / (i + 1) ** zipf_s for i in range(len(vocab))]
    cum = list(itertools.accumulate(weights))
    rng = random.Random(seed)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for _ in range(lines):
            words = rng.choices(vocab, cum_weights=cum, k=rng.randint(8, 24))
            sent = " ".join(words)
            if rng.random() < 0.3:  # variasi huruf besar + tanda baca agar preprocessing bermakna
                sent = sent.capitalize()
            sent += rng.choice([".", ".", ".", "!", "?", ", dst."])
            f.write(sent + "\n")
    return path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lines", type=int, default=100_000)
    ap.add_argument("--out", default="data/bigdata.txt")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    p = generate(a.out, a.lines, a.seed)
    print(f"Dataset dibuat: {p} ({a.lines:,} baris, {os.path.getsize(p) / 1e6:.1f} MB)")

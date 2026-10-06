#!/usr/bin/env python3
"""WordCount versi single machine (Python murni) sebagai pembanding."""
import argparse
import re
import time
from collections import Counter

from common import STOPWORDS

TOKEN_RE = re.compile(r"[a-z0-9]+")


def wordcount(path, remove_stopwords=False):
    c = Counter()
    with open(path, encoding="utf-8") as f:
        for line in f:
            c.update(TOKEN_RE.findall(line.lower()))
    if remove_stopwords:
        for w in STOPWORDS:
            c.pop(w, None)
    return c


def top_n(counter, n=10):
    return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:n]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/bigdata.txt")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--remove-stopwords", action="store_true")
    a = ap.parse_args()
    t0 = time.perf_counter()
    top = top_n(wordcount(a.input, a.remove_stopwords), a.top)
    dt = time.perf_counter() - t0
    for w, c in top:
        print(f"{w}\t{c}")
    print(f"\nWaktu eksekusi (single machine): {dt:.3f} detik")

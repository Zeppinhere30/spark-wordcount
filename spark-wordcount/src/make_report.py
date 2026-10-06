#!/usr/bin/env python3
"""Membuat laporan PDF format akademik (A4, Times New Roman 12, teks hitam) dari results/ dan figures/.

Edit blok IDENTITAS & FORMAT di bawah, lalu jalankan:  python src/make_report.py
"""
import csv
import datetime
import json
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

# ====================== IDENTITAS (EDIT DI SINI) ======================
NAMA = "Asep Suhaedi"
NIM = "312410230"
PRODI = "Teknik Informatika"
UNIV = "Universitas Pelita Bangsa"
MATKUL = "Big Data"
JUDUL = "Implementasi WordCount dengan PySpark dan Analisis Performa Pemrosesan Paralel"

# ====================== FORMAT (EDIT BILA PERLU) ======================
FONT_SIZE = 12            # ukuran huruf isi
TABLE_SIZE = 10           # ukuran huruf tabel, kode, keterangan gambar
LINE_SPACING = 1.15       # 1.0 = tunggal, 1.5 = satu setengah (laporan bisa jadi >6 halaman)
MARGIN_LEFT, MARGIN_RIGHT, MARGIN_TOP, MARGIN_BOTTOM = 4, 3, 3, 3   # cm (standar 4-3-3-3)
# =====================================================================

RES, FIG, OUT = "results", "figures", "report/Laporan_WordCount_PySpark.pdf"
BLACK = colors.black
TEXT_W = A4[0] - (MARGIN_LEFT + MARGIN_RIGHT) * cm


# ---------- font: Times New Roman bila ada, jika tidak Liberation Serif / Times bawaan PDF ----------
def register_fonts():
    candidates = [
        ("C:/Windows/Fonts/times.ttf", "C:/Windows/Fonts/timesbd.ttf", "C:/Windows/Fonts/timesi.ttf", "C:/Windows/Fonts/timesbi.ttf"),
        ("/Library/Fonts/Times New Roman.ttf", "/Library/Fonts/Times New Roman Bold.ttf",
         "/Library/Fonts/Times New Roman Italic.ttf", "/Library/Fonts/Times New Roman Bold Italic.ttf"),
        ("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf"),
    ]
    for files in candidates:
        if all(os.path.exists(f) for f in files):
            names = ("TNR", "TNR-B", "TNR-I", "TNR-BI")
            for n, f in zip(names, files):
                pdfmetrics.registerFont(TTFont(n, f))
            pdfmetrics.registerFontFamily("TNR", normal="TNR", bold="TNR-B", italic="TNR-I", boldItalic="TNR-BI")
            return "TNR", "TNR-B"
    pdfmetrics.registerFontFamily("Times-Roman", normal="Times-Roman", bold="Times-Bold",
                                  italic="Times-Italic", boldItalic="Times-BoldItalic")
    return "Times-Roman", "Times-Bold"


F, FB = register_fonts()
LEAD = FONT_SIZE * 1.15 * LINE_SPACING
TLEAD = TABLE_SIZE * 1.2

BODY = ParagraphStyle("body", fontName=F, fontSize=FONT_SIZE, leading=LEAD, alignment=TA_JUSTIFY,
                      firstLineIndent=1.25 * cm, spaceAfter=4, textColor=BLACK)
NOINDENT = ParagraphStyle("noindent", parent=BODY, firstLineIndent=0)
H1 = ParagraphStyle("h1", fontName=FB, fontSize=FONT_SIZE, leading=LEAD, spaceBefore=8, spaceAfter=3,
                    keepWithNext=1, textColor=BLACK)
H2 = ParagraphStyle("h2", fontName=FB, fontSize=FONT_SIZE, leading=LEAD, spaceBefore=4, spaceAfter=2,
                    keepWithNext=1, textColor=BLACK)
TITLE = ParagraphStyle("title", fontName=FB, fontSize=14, leading=18, alignment=TA_CENTER, spaceAfter=4, textColor=BLACK)
SUB = ParagraphStyle("sub", fontName=F, fontSize=FONT_SIZE, leading=LEAD, alignment=TA_CENTER, textColor=BLACK)
CAP = ParagraphStyle("cap", fontName=F, fontSize=TABLE_SIZE, leading=TLEAD + 1, alignment=TA_CENTER,
                     spaceAfter=6, textColor=BLACK)
CAPT = ParagraphStyle("capt", parent=CAP, spaceAfter=3, spaceBefore=4, keepWithNext=1)
CELL = ParagraphStyle("cell", fontName=F, fontSize=TABLE_SIZE, leading=TLEAD, textColor=BLACK)
REF = ParagraphStyle("ref", fontName=F, fontSize=FONT_SIZE, leading=LEAD, alignment=TA_JUSTIFY,
                     leftIndent=1 * cm, firstLineIndent=-1 * cm, spaceAfter=3, textColor=BLACK)
BUL = ParagraphStyle("bul", parent=BODY, firstLineIndent=0, leftIndent=0.9 * cm, bulletIndent=0.3 * cm,
                     bulletFontName=F, spaceAfter=2)


def P(t, s=BODY):
    return Paragraph(t, s)


def bullets(items):
    return [Paragraph(i, BUL, bulletText="\u2022") for i in items]


def table(data, fracs):
    rows = [[Paragraph(f"<b>{c}</b>", CELL) for c in data[0]]]
    rows += [[Paragraph(str(c), CELL) for c in r] for r in data[1:]]
    t = Table(rows, colWidths=[f * TEXT_W for f in fracs], repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, BLACK),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9d9d9")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def img(path, width_cm):
    w, h = ImageReader(path).getSize()
    width = min(width_cm * cm, TEXT_W)
    return Image(path, width=width, height=width * h / w)


def rcsv(name):
    with open(os.path.join(RES, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(F, 10)
    canvas.setFillColor(BLACK)
    canvas.drawCentredString(A4[0] / 2 + (MARGIN_LEFT - MARGIN_RIGHT) * cm / 2, 1.5 * cm, str(doc.page))
    canvas.restoreState()


def build():
    summ = json.load(open(os.path.join(RES, "benchmark_summary.json"), encoding="utf-8"))
    jst = json.load(open(os.path.join(RES, "job_stage_task.json"), encoding="utf-8"))
    top10 = rcsv("top10.csv")
    parts = [(int(r["partitions"]), float(r["time_s"])) for r in rcsv("benchmark_partitions.csv")]
    scaling = [(int(r["lines"]), float(r["size_mb"]), float(r["python_s"]), float(r["spark_s"]))
               for r in rcsv("benchmark_scaling.csv")]
    m, bd = summ["machine"], summ["breakdown"]
    py_t, best_n = summ["python_time_s"], summ["spark_best_partitions"]
    best_t, t_one = summ["spark_best_all_cores_s"], summ["spark_local1_s"]
    t_p1 = dict(parts).get(1, parts[0][1])
    cores = m["cpu_cores"] or 1
    nlines = summ["input_lines"]
    today = datetime.date.today().strftime("%d-%m-%Y")

    # ---------- narasi berbasis data ----------
    ratio = best_t / py_t
    if ratio > 1:
        cmp_txt = (f"Pada dataset {nlines:,} baris, Python murni menyelesaikan WordCount dalam <b>{py_t:.2f} detik</b>, "
                   f"sedangkan Spark terbaik (partition = {best_n}) membutuhkan <b>{best_t:.2f} detik</b> "
                   f"(sekitar {ratio:.1f} kali lebih lambat). Seluruh data muat di RAM satu mesin sehingga overhead "
                   "Spark (start JVM, serialisasi Python-JVM, penjadwalan task, shuffle) lebih besar daripada "
                   "keuntungan paralelisme.")
    else:
        cmp_txt = (f"Pada dataset {nlines:,} baris, Python murni membutuhkan <b>{py_t:.2f} detik</b> dan Spark terbaik "
                   f"(partition = {best_n}) <b>{best_t:.2f} detik</b> (sekitar {1 / ratio:.1f} kali lebih cepat) karena "
                   "pekerjaan dibagi ke beberapa core secara paralel.")

    worst_n, worst_t = max(parts, key=lambda p: p[1])
    if best_n == 1:
        part_txt = (f"Waktu tercepat dicapai pada <b>1 partition</b> ({best_t:.2f} detik). Mesin ini memiliki {cores} core "
                    "logis, sehingga menambah partition menambah jumlah task, biaya penjadwalan, dan blok shuffle "
                    f"tanpa menambah paralelisme yang sebanding; waktu terburuk terjadi pada {worst_n} partition "
                    f"({worst_t:.2f} detik). Ini menunjukkan overhead akibat partition berlebih.")
    else:
        part_txt = (f"Dari 1 partition ({t_p1:.2f} detik) waktu turun hingga titik optimum pada <b>{best_n} partition</b> "
                    f"({best_t:.2f} detik, speedup {t_p1 / best_t:.2f} kali). Di atas titik tersebut waktu naik kembali "
                    f"(hingga {worst_t:.2f} detik pada {worst_n} partition) karena overhead penjadwalan task, "
                    "serialisasi, dan jumlah blok shuffle yang membengkak. Pola ini sesuai kaidah praktis "
                    f"2-4 partition per core (mesin ini: {cores} core).")

    cross = next((s for s in scaling if s[3] < s[2]), None)
    if cross:
        scale_txt = (f"Spark mulai lebih cepat daripada Python murni pada sekitar <b>{cross[0]:,} baris</b> ({cross[1]:.0f} MB). "
                     "Di bawah ukuran tersebut overhead tetap Spark mendominasi.")
    else:
        big = scaling[-1]
        scale_txt = (f"Pada seluruh ukuran yang diuji (hingga {big[0]:,} baris, {big[1]:.0f} MB) Python murni masih lebih cepat. "
                     "Keunggulan Spark baru muncul ketika data melebihi kapasitas memori satu mesin atau ketika "
                     "tersedia banyak node/core; pengujian ini hanya memakai satu mesin.")

    sp = t_one / best_t
    sp_txt = (f"speedup {sp:.2f} kali dengan {cores} core logis" if sp >= 1.05
              else "tidak ada percepatan berarti (selisih dalam rentang variasi pengukuran)")
    core_txt = (f"Spark dengan <b>local[1]</b> (1 thread, 1 partition) membutuhkan {t_one:.2f} detik, dibanding "
                f"{best_t:.2f} detik pada local[*] dengan partition terbaik: {sp_txt}.")
    if cores == 1:
        core_txt += " Karena mesin uji hanya memiliki 1 core, paralelisme nyata tidak dapat diukur."

    read_pct = 100 * bd["read_map_s"] / bd["total_sortby_s"] if bd["total_sortby_s"] else 0
    opt_gain = bd["total_sortby_s"] / bd["total_takeordered_s"] if bd["total_takeordered_s"] else 1
    bott_txt = (f"Dengan {bd['partitions']} partition, tahap baca + flatMap + map (Stage 1, murni narrow) memakan sekitar "
                f"<b>{read_pct:.0f}%</b> dari total waktu, sisanya ({100 - read_pct:.0f}%) berasal dari shuffle, "
                f"reduceByKey sisi reduce, sortBy, dan take. Mengganti <font face='Courier'>sortBy().take(10)</font> "
                f"dengan <font face='Courier'>takeOrdered(10)</font> menghasilkan total {bd['total_takeordered_s']:.2f} detik "
                f"({'lebih cepat' if opt_gain > 1 else 'tidak lebih cepat'}, rasio {opt_gain:.2f}) karena tidak perlu "
                "job sampling RangePartitioner dan sort global seluruh kata.")

    story = []
    # ================= JUDUL =================
    story += [P(JUDUL.upper(), TITLE), P(f"{NAMA} (NIM {NIM})", SUB), P(f"{PRODI}, {UNIV}", SUB),
              P(f"Mata Kuliah {MATKUL} | {today}", SUB), Spacer(1, 6)]

    # ================= 1 =================
    story += [P("1. PENDAHULUAN", H1),
              P("WordCount adalah kasus dasar pemrosesan data paralel, yaitu menghitung frekuensi setiap kata pada "
                "kumpulan teks. Apache Spark memproses data sebagai <i>Resilient Distributed Dataset</i> (RDD) yang "
                "dipartisi ke banyak executor sehingga komputasi berjalan paralel dan tahan gagal melalui lineage [1]. "
                "Tugas ini mengimplementasikan WordCount dengan PySpark, memetakan alur Job, Stage, dan Task, "
                "membandingkan pemrosesan single machine dengan Spark, mengidentifikasi bottleneck, serta menganalisis "
                "pengaruh jumlah partition terhadap performa.")]

    # ================= 2 =================
    story += [P("2. LINGKUNGAN DAN DATASET", H1), P("Tabel 1. Lingkungan pengujian", CAPT)]
    story.append(table([
        ["Komponen", "Nilai"],
        ["OS / CPU / RAM", f"{m['os']} / {m['cpu_cores']} core logis / {m['ram_gb']} GB"],
        ["Python / PySpark", f"{m['python']} / {m['spark']}"],
        ["Mode Spark", "local[*] (semua core satu mesin; bukan cluster multi-node)"],
        ["Dataset", f"{nlines:,} baris, {summ['input_mb']} MB, teks sintetis berdistribusi Zipf (seed tetap)"],
        ["Metode ukur", "Median hasil jalan setelah warm-up; waktu dari pembacaan data sampai top-10 tersedia"],
    ], [0.27, 0.73]))
    story += [Spacer(1, 4),
              P("Dataset sintetis dipilih agar eksperimen dapat direproduksi dan ukurannya dapat diatur. Frekuensi kata "
                "mengikuti hukum Zipf sehingga kata fungsi (yang, dan, di) mendominasi, serupa teks bahasa Indonesia nyata.")]

    # ================= 3 =================
    story += [P("3. IMPLEMENTASI DAN PIPELINE", H1), img(os.path.join(FIG, "pipeline.png"), 14),
              P("Gambar 1. Diagram pipeline pemrosesan data", CAP)]
    code = ("lines  = sc.textFile(path, minPartitions=n)\n"
            "words  = lines.flatMap(lambda l: re.findall(r\"[a-z0-9]+\", l.lower()))\n"
            "pairs  = words.map(lambda w: (w, 1))\n"
            "counts = pairs.reduceByKey(lambda a, b: a + b, numPartitions=n)\n"
            "top10  = counts.sortBy(lambda kv: (-kv[1], kv[0])).take(10)   # ACTION")
    story += [KeepTogether([Preformatted(code, ParagraphStyle("code", fontName="Courier", fontSize=8, leading=10,
                                                              backColor=colors.HexColor("#f2f2f2"), borderPadding=4,
                                                              textColor=BLACK))]),
              Spacer(1, 6), P("Tabel 2. Transformation dan action yang digunakan", CAPT)]
    story.append(table([
        ["Operasi", "Jenis", "Penjelasan"],
        ["textFile()", "Transformation (lazy)", "Membaca file teks menjadi RDD baris dan menentukan jumlah partition awal."],
        ["flatMap(tokenize)", "Transformation, narrow", "Mengubah tiap baris menjadi banyak kata (huruf kecil, tanda baca dibuang)."],
        ["map(w -&gt; (w,1))", "Transformation, narrow", "Membentuk pasangan key-value untuk penjumlahan."],
        ["reduceByKey(a+b)", "Transformation, wide", "Menjumlahkan nilai per kata; combine di sisi map sebelum shuffle."],
        ["sortBy(-count)", "Transformation, wide", "Mengurutkan global menurun; memicu sampling dan shuffle."],
        ["take(10)", "Action", "Mengambil 10 elemen ke driver; memicu eksekusi seluruh lineage."],
        ["count()", "Action", "Menghitung jumlah baris (validasi dataset)."],
    ], [0.24, 0.26, 0.50]))

    # ================= 4 =================
    story += [P("4. ALUR SPARK JOB, STAGE, DAN TASK", H1),
              P("Transformation bersifat lazy; Spark hanya membangun DAG sampai Action dipanggil. Batas Stage ditentukan "
                "oleh operasi wide (shuffle): operasi narrow (textFile, flatMap, map, dan combine reduceByKey) berjalan "
                "berantai dalam satu Stage, sedangkan reduceByKey sisi reduce dan sortBy membutuhkan data dari semua "
                "partition sehingga membentuk Stage baru. Setiap Stage dibagi menjadi Task, satu Task per partition [1][2]."),
              img(os.path.join(FIG, "job_stage_task.png"), 12.5),
              P("Gambar 2. Alur Action, Job, Stage, dan Task", CAP)]
    rows = [["Job", "Stage", "Task", "Selesai"]]
    for j in jst["jobs"]:
        for s in j["stages"]:
            nm = s["name"].split(" at ")[0]
            note = "" if s["completed_tasks"] else " (dilewati)"
            rows.append([j["job_id"], f"{s['stage_id']}: {nm}{note}", s["num_tasks"], s["completed_tasks"]])
    story += [P("Tabel 3. Job, Stage, dan Task hasil pengamatan (statusTracker)", CAPT),
              table(rows, [0.12, 0.58, 0.15, 0.15]), Spacer(1, 4),
              P(f"Satu pemanggilan <font face='Courier'>sortBy().take()</font> menghasilkan {len(jst['jobs'])} Job: sortBy "
                "menjalankan job sampling untuk menentukan batas range partition sebelum job sort dan take. Stage yang "
                "dilewati adalah Stage reduceByKey yang keluaran shuffle-nya sudah tersedia dari job sebelumnya (reuse).")]

    # ================= 5 =================
    story += [P("5. HASIL", H1), P("5.1 Sepuluh kata terbanyak", H2),
              P("Tabel 4. Sepuluh kata dengan frekuensi tertinggi", CAPT)]
    story.append(table([["Peringkat", "Kata", "Frekuensi"]] +
                       [[r["rank"], r["kata"], f"{int(r['frekuensi']):,}"] for r in top10], [0.25, 0.4, 0.35]))
    story += [Spacer(1, 4),
              P(f"Hasil Spark identik dengan hasil Python murni (diverifikasi otomatis: "
                f"<b>{'cocok' if summ['results_match_python'] else 'TIDAK cocok'}</b> pada semua konfigurasi partition).")]
    story += [P("5.2 Single machine vs distributed", H2), P("Tabel 5. Perbandingan single machine dan distributed", CAPT)]
    story.append(table([
        ["Aspek", "Single machine (Python)", "Distributed (Spark)"],
        ["Data yang diproses", "Terbatas RAM satu mesin", "Dibagi ke banyak partition/node, dapat melebihi RAM satu mesin"],
        ["Waktu (data ini)", f"{py_t:.2f} detik", f"{best_t:.2f} detik (partition = {best_n}, local[*])"],
        ["Skalabilitas", "Vertikal (upgrade mesin)", "Horizontal (tambah node/core)"],
        ["Ketahanan gagal", "Rendah (ulang dari awal)", "Tinggi (task diulang dari lineage RDD)"],
        ["Overhead", "Sangat kecil", "Start JVM, serialisasi, scheduling, shuffle"],
        ["Biaya", "Murah, sederhana", "Lebih mahal (cluster), operasional kompleks"],
    ], [0.24, 0.31, 0.45]))
    story += [Spacer(1, 4), P(cmp_txt), img(os.path.join(FIG, "scaling.png"), 11),
              P("Gambar 3. Waktu eksekusi terhadap ukuran data", CAP), P(scale_txt)]

    # ================= 6 =================
    story += [P("6. ANALISIS PERFORMA", H1), P("6.1 Pengaruh jumlah partition", H2),
              img(os.path.join(FIG, "partitions.png"), 11), P("Gambar 4. Waktu eksekusi untuk berbagai jumlah partition", CAP)]
    k = len(parts)
    story.append(table([["Partition"] + [str(p) for p, _ in parts], ["Waktu (detik)"] + [f"{t:.2f}" for _, t in parts]],
                       [0.24] + [0.76 / k] * k))
    story += [Spacer(1, 4), P(part_txt), P(core_txt)]
    story += [P("6.2 Identifikasi bottleneck", H2), img(os.path.join(FIG, "breakdown.png"), 11),
              P("Gambar 5. Estimasi pembagian waktu per tahap (selisih total dan Stage 1, bersifat pendekatan)", CAP),
              P(bott_txt)]
    story += bullets([
        "<b>Shuffle:</b> reduceByKey dan sortBy memindahkan data antar partition; biaya naik bersama jumlah partition.",
        "<b>Overhead Python-JVM:</b> lambda Python dijalankan di proses worker Python sehingga tiap record diserialisasi bolak-balik.",
        "<b>Data skew:</b> kata dominan seperti 'yang' sangat sering muncul; map-side combine pada reduceByKey meredamnya.",
        "<b>Jumlah partition:</b> terlalu sedikit membuat core menganggur, terlalu banyak membuat overhead task melebihi kerja nyata.",
        "<b>Sorting global tak perlu:</b> hanya 10 kata dibutuhkan, sehingga takeOrdered cukup dibanding sortBy seluruh kata.",
    ])

    # ================= 7 =================
    story += [P("7. KESIMPULAN", H1)]
    story += bullets([
        "WordCount berhasil diimplementasikan dengan PySpark dan 10 kata terbanyak identik dengan hasil Python murni.",
        f"Pada {nlines:,} baris, Spark terbaik {best_t:.2f} detik (partition = {best_n}) dibanding Python murni {py_t:.2f} detik. "
        + ("Spark belum unggul karena overhead lebih besar daripada beban kerja." if ratio > 1 else "Spark unggul berkat eksekusi paralel."),
        f"Jumlah partition berpengaruh jelas: {t_p1:.2f} detik pada 1 partition, {best_t:.2f} detik pada titik terbaik, "
        f"dan {worst_t:.2f} detik pada {worst_n} partition.",
        "Bottleneck utama adalah shuffle (reduceByKey, sortBy), overhead serialisasi Python-JVM, dan skew kata dominan.",
        "Keterbatasan: pengujian memakai mode local[*] pada satu mesin dan data sintetis; hasil pada cluster "
        "multi-node dan teks nyata dapat berbeda.",
    ])
    story += [P("REFERENSI", H1)]
    for r in [
        "[1] Zaharia, M., et al. (2012). Resilient Distributed Datasets: A Fault-Tolerant Abstraction for In-Memory Cluster Computing. NSDI '12.",
        "[2] Apache Spark Documentation. RDD Programming Guide dan Cluster Mode Overview. https://spark.apache.org/docs/latest/",
        "[3] Dean, J. dan Ghemawat, S. (2004). MapReduce: Simplified Data Processing on Large Clusters. OSDI '04.",
        "[4] Damji, J., et al. (2020). Learning Spark, 2nd Edition. O'Reilly Media.",
    ]:
        story.append(P(r, REF))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=MARGIN_LEFT * cm, rightMargin=MARGIN_RIGHT * cm,
                            topMargin=MARGIN_TOP * cm, bottomMargin=MARGIN_BOTTOM * cm, title=JUDUL, author=NAMA)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"Laporan dibuat: {OUT}  (font: {F}, spasi: {LINE_SPACING})")


if __name__ == "__main__":
    build()
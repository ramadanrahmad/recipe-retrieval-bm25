# Temu Kembali Resep Masakan Indonesia Berbasis Kueri Komposisi Bahan Menggunakan Algoritma Okapi BM25

Proyek sistem **Temu Kembali Informasi (Information Retrieval - IR)** end-to-end yang mengindeks dan mencari resep masakan nusantara berdasarkan bahan/komposisi kuliner (*Ingredients*) menggunakan algoritma **Okapi BM25**.

---

## 📌 Struktur Proyek

```text
d:\tki\
├── data\                           # Dataset mentah 8 kategori masakan (Kaggle)
│   ├── dataset-ayam.csv
│   ├── dataset-ikan.csv
│   ├── dataset-kambing.csv
│   ├── dataset-sapi.csv
│   ├── dataset-tahu.csv
│   ├── dataset-telur.csv
│   ├── dataset-tempe.csv
│   └── dataset-udang.csv
├── index_storage\                  # Penyimpanan serialisasi index & metadata
│   ├── inverted_index.pkl          # File binary Inverted Index
│   ├── inverted_index_sample.json  # Cuplikan Inverted Index (human-readable)
│   ├── recipes_metadata.pkl        # Metadata resep bersih
│   └── stem_cache.pkl              # Cache hasil stemming vocabulary unik
├── reports\                        # Laporan dan artefak untuk paper UTS/UAS
│   └── report_paper_artifacts.md   # Tabel statistik, jejak preprocessing, & evaluasi
├── src\                            # Paket modular source code
│   ├── __init__.py
│   ├── config.py                   # Parameter BM25, path, & stopword kuliner
│   ├── data_loader.py              # Penggabungan dataset, penanganan null, & DocID
│   ├── preprocessor.py             # Pipeline preprocessing 6 tahap & batch stemming
│   ├── inverted_index.py           # Inverted Index sparse from scratch
│   ├── bm25.py                     # Mesin skor Okapi BM25 eksplisit
│   └── evaluator.py                # Perhitungan Precision@K & pengujian skenario
├── generate_report_artifacts.py     # Script otomatis pembuat seluruh tabel paper
├── search_cli.py                   # CLI interaktif pencarian resep
├── test_system.py                  # Unit dan integration tests
├── requirements.txt                # Dependensi pustaka Python
└── README.md                       # Dokumentasi sistem
```

---

## ⚙️ Instalasi & Persiapan Lingkungan

1. Pastikan Anda menggunakan Python 3.10+ (Diuji pada Python 3.14).
2. Instal pustaka yang dibutuhkan:
```bash
pip install -r requirements.txt
```
Dependensi utama:
- `pandas` & `numpy`: Manajemen data dan komputasi array.
- `PySastrawi`: Stemmer akar kata bahasa Indonesia dan kamus stopword standar.
- `tqdm`: Indikator progress bar saat pemrosesan batch data.
- `tabulate`: Formatting tabel teks dan Markdown.

---

## 🚀 Cara Menjalankan Sistem

### 1. Menjalankan Unit Test
Untuk memverifikasi kebenaran seluruh modul (Data Loader, Preprocessing, Inverted Index, Skor BM25, Evaluasi):
```bash
python test_system.py
```

### 2. Membangun Indeks & Menghasilkan Artefak Paper UTS/UAS
Script ini mengeksekusi pipeline end-to-end dari data mentah, membangun Inverted Index, menjalankan 5 skenario kueri bahan, menghitung metrik `Precision@5` dan `Precision@10`, serta mengekspor seluruh tabel ke `reports/report_paper_artifacts.md`:
```bash
python generate_report_artifacts.py
```

### 3. Menggunakan Pencarian Interaktif (CLI)
Pengguna dapat mencari resep dengan memasukkan bahan apa saja:
```bash
# Mode kueri langsung via command line
python search_cli.py --query "ayam, santan, serai, cabai" --top_k 5

# Mode prompt interaktif
python search_cli.py --interactive
```

---

## 🔬 Spesifikasi Algoritma & Komponen

### 1. Text Preprocessing Khusus Komposisi Kuliner
Dijalankan secara berurutan dengan pelacakan (*tracing*) step-by-step:
1. **Pemisah `--`**: Diganti dengan spasi.
2. **Case Folding**: Mengubah semua teks menjadi huruf kecil (*lowercase*).
3. **Regex Cleaning**: Menghapus angka (termasuk pecahan $1/2, 3/4$), simbol, dan tanda baca (`[^a-z\s]`).
4. **Tokenization**: Pemecahan kalimat menjadi token kata tunggal.
5. **Stopword Removal (2 Lapis)**:
   - **Lapis 1**: Stopword umum bahasa Indonesia (Sastrawi).
   - **Lapis 2**: Stopword kuliner (satuan takaran seperti `sdm`, `sdt`, `gram`, `siung`, `lembar`, dan cara pengolahan seperti `iris`, `cincang`, `rebus`, `tumis`).
6. **Stemming Teroptimasi**: Mengumpulkan kosakata unik korpus ($\approx 6.400$ kata), melakukan stemming hanya pada kata unik tersebut ke dalam dictionary mapping, lalu memetakannya kembali ke seluruh $15.593$ resep secara instan.

### 2. Inverted Index (from Scratch)
Dibangun tanpa library black-box:
- `index`: Kamus `term -> {DocID: TF}`
- `doc_lengths`: Panjang dokumen $|D|$ (jumlah token bahan bersih)
- `avgdl`: Rata-rata panjang dokumen ($22.6252$ token/resep)
- `N`: Total dokumen korpus ($15.593$ resep)

### 3. Okapi BM25
- **Rumus IDF (Robertson-Spärck Jones +1 smoothing)**:
  $$\text{IDF}(q_i) = \ln\left(\frac{N - n(q_i) + 0.5}{n(q_i) + 0.5} + 1\right)$$
- **Rumus Skor Okapi BM25**:
  $$\text{Score}(D, Q) = \sum_{q_i \in Q} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k1 + 1)}{f(q_i, D) + k1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$
  *(Default parameter: $k1 = 1.5$, $b = 0.75$)*

### 4. Metrik Evaluasi
Resep dianggap **Relevan** jika memuat minimal $\ge 60\%$ dari token bahan pada kueri:
- **Precision@5**: Proporsi dokumen relevan pada Top 5.
- **Precision@10**: Proporsi dokumen relevan pada Top 10.
- **Hasil Pengujian 5 Skenario**:
  - Macro-Average Precision@5: **100.00%**
  - Macro-Average Precision@10: **98.00%**

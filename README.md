# Sistem Temu Kembali Informasi (IR) Resep Masakan Indonesia
**Menggunakan Algoritma Probabilistik Okapi BM25 & Inverted Index**

Repositori ini memuat implementasi lengkap sistem *Information Retrieval* (IR) untuk mencari dan merekomendasikan resep masakan khas Indonesia berdasarkan sisa bahan pangan yang tersedia di dapur (*ingredient-based recipe retrieval*).

---

## 📂 Struktur Proyek

Proyek ini dibagi secara modular ke dalam 2 folder utama:

```text
├── model/                  # Pengembangan model, korpus, indeks, & evaluasi
│   ├── data/               # Korpus 7 kategori resep Cookpad (13.074 resep bersih)
│   ├── index_storage/      # Serialisasi Inverted Index & Metadata
│   ├── reports/            # Hasil benchmark metrik (Precision, MAP, MRR, Latensi)
│   ├── src/                # Modul Python (preprocessor, inverted_index, bm25, evaluator)
│   ├── model_okapi_bm25.ipynb # Single-file Jupyter Notebook model & pengujian
│   └── model_okapi_bm25.py    # Skrip pipeline model mandiri
│
├── website/                # Aplikasi web interaktif pengguna (Flask)
│   ├── templates/
│   │   └── index.html      # Tampilan antarmuka responsif (Bootstrap 5.3)
│   ├── app.py              # Backend Flask & perankingan pencarian BM25
│   ├── test_app.py         # Unit testing verifikasi web & API
│   ├── requirements.txt    # Dependensi khusus website
│   └── README.md           # Dokumentasi teknis website
│
├── requirements.txt        # Dependensi global proyek
└── README.md               # Dokumentasi utama repositori
```

---

## 🍳 Fitur Utama
1. **Korpus Kuliner Terstandarisasi**: 13.074 resep masakan Indonesia dari 7 kategori bahan utama (Ayam, Daging Sapi, Kambing, Ikan, Telur, Tahu, dan Tempe).
2. **Prapemrosesan Teks Khusus Kuliner**: Case folding, penghapusan tanda baca, penyaringan *culinary stopwords* (takaran masakan seperti *sdm, sdt, siung, gram*), dan stemming Bahasa Indonesia menggunakan PySastrawi.
3. **Retrieval Cepat Inverted Index**: Mengindeks 5.283 kosakata unik dengan waktu pencarian rata-rata **~0.02 - 0.05 detik**.
4. **Pembobotan Okapi BM25**: Menggunakan parameter optimal $k_1 = 1.2$ dan $b = 0.75$ serta formula IDF Robertson-Spärck Jones.
5. **Aplikasi Web Interaktif (Flask)**:
   - Pencarian berdasarkan bahan masakan yang dimiliki di dapur.
   - Filter kategori bahan utama.
   - Pilihan rekomendasi Top 5, 10, atau 20 resep.
   - Penilaian relevansi masakan & highlight bahan yang cocok.
   - Modal pop-up resep lengkap dengan checklist bahan dan instruksi bernomor urut.

---

## ⚡ Panduan Memulai

### 1. Kloning Repositori & Pasang Dependensi
```bash
git clone https://github.com/ramadanrahmad/recipe-retrieval-bm25.git
cd recipe-retrieval-bm25
pip install -r requirements.txt
```

### 2. Menjalankan Model & Pipeline (Opsional)
Untuk menjalankan pipeline data pre-processing, pembangunan inverted index, dan evaluasi:
```bash
python model/model_okapi_bm25.py
```
Atau buka file notebook [`model/model_okapi_bm25.ipynb`](model/model_okapi_bm25.ipynb).

### 3. Menjalankan Aplikasi Web
Jalankan server aplikasi Flask:
```bash
python website/app.py
```
Buka browser di alamat: **`http://127.0.0.1:5000`**

### 4. Menjalankan Unit Testing Website
```bash
python website/test_app.py
```

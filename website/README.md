# Aplikasi Web Temu Kembali Informasi Resep Masakan Indonesia (DapurCerdas)
**Berbasis Algoritma Probabilistik Okapi BM25 & Inverted Index**

Aplikasi web interaktif berbasis Flask untuk mencari dan memeringkat 13.074 resep masakan Indonesia berdasarkan sisa bahan yang dimiliki pengguna di dapur.

---

## 🌟 Fitur Utama
1. **Pencarian Berbasis Bahan Masakan**:
   - Pengguna cukup memasukkan daftar bahan yang tersedia (misal: `ayam santan serai cabai`).
   - Prapemrosesan teks otomatis: Case folding, pembersihan tanda baca, penghapusan *custom culinary stopwords* (takaran: *sdm, sdt, gram, siung, iris*, dll.), dan stemming Bahasa Indonesia (PySastrawi).
2. **Perangkingan Okapi BM25 Cepat**:
   - Menggunakan formula Okapi BM25 ($k_1 = 1.2, b = 0.75$) dengan pembobotan IDF Robertson-Spärck Jones.
   - Waktu respons pencarian sangat cepat (rata-rata **~0.02 - 0.05 detik**) berkat struktur data *Inverted Index*.
3. **Filter Kategori Resep**:
   - Pilihan filter bahan utama: **Semua Resep**, **Ayam**, **Ikan**, **Daging Sapi**, **Kambing**, **Telur**, **Tahu**, dan **Tempe**.
4. **Opsi Top-K Hasil Pencarian**:
   - Pilihan menampilkan Top 5, Top 10, atau Top 20 resep terbaik.
5. **Kartu Resep Interaktif & Penilaian Relevansi**:
   - Menampilkan peringkat, judul masakan, badge kategori, skor BM25, persentase kecocokan bahan, label relevansi (*Sangat Relevan* $\ge 70\%$, *Cukup Relevan* $\ge 50\%$, *Kurang Relevan* $< 50\%$), dan sorotan (*highlight*) bahan kueri yang cocok.
6. **Modal Popup Detail Resep**:
   - Klik **"Buka Resep"** untuk membaca bahan lengkap dengan *checklist checkbox* interaktif dan urutan langkah memasak bernomor.
7. **Pills Kueri Sampel**:
   - Tombol cepat untuk menguji kueri populer nusantara (Ayam Santan Serai, Telur Balado Pedas, Sapi Lada Hitam, Gurame Asam Manis, Tahu Tempe Kecap).

---

## 📁 Struktur Direktori `website/`
```text
website/
├── app.py              # Server backend Flask & logika pencarian BM25
├── test_app.py         # Unit testing verifikasi fungsionalitas web & API
├── requirements.txt    # Daftar dependensi Python
├── README.md           # Dokumentasi teknis aplikasi web
└── templates/
    └── index.html      # Antarmuka frontend (Bootstrap 5.3 + Custom Styling)
```

---

## 🚀 Cara Menjalankan Aplikasi Web

### 1. Pastikan Dependensi Terpasang
Buka terminal dan pasang pustaka yang diperlukan:
```bash
pip install -r website/requirements.txt
```

### 2. Jalankan Server Flask
Jalankan perintah berikut dari direktori root proyek (`d:\tki`):
```bash
python website/app.py
```

### 3. Buka di Browser
Buka tautan lokal berikut di peramban web:
```text
http://127.0.0.1:5000
```

---

## 🧪 Pengujian Otomatis (Unit Testing)
Untuk memastikan seluruh endpoint dan pencarian bekerja dengan sempurna:
```bash
python website/test_app.py
```
Hasil yang diharapkan: **5 tests OK (0 failures)**.

---

## 🔌 API Endpoints
- `GET /`: Halaman utama pencarian (menerima query parameters: `query`, `category`, `top_k`).
- `GET /api/recipe/<doc_id>`: Mengembalikan data JSON detail resep (judul, kategori, likes, daftar bahan, dan langkah memasak).


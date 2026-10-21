# ARTEFAK LAPORAN PAPER TEMU KEMBALI INFORMASI (IR)
**Judul Paper:** Temu Kembali Resep Masakan Indonesia Berbasis Kueri Komposisi Bahan Menggunakan Algoritma Okapi BM25  
**Tanggal Eksekusi:** 2026-10-21 21:59:51  

---

## 1. STATISTIK KORPUS DAN DISTRIBUSI DATASET

Tabel berikut merangkum statistik teknis dari korpus resep masakan Indonesia setelah tahap pembersihan dan indeksasi.

### Tabel 1.1: Ringkasan Statistik Korpus Resep
| Parameter                                          | Nilai                    |
|:---------------------------------------------------|:-------------------------|
| Total Dokumen Resep (N)                            | 15,593 dokumen           |
| Jumlah Kategori Bahan Utama                        | 8 kategori               |
| Ukuran Vocabulary Sebelum Preprocessing            | 6,824 token kata unik    |
| Ukuran Vocabulary Setelah Preprocessing & Stemming | 5,512 token kata unik    |
| Persentase Reduksi Dimensi Vocabulary              | 19.23%                   |
| Rata-rata Panjang Dokumen Bahan (avgdl)            | 22.6252 token per resep  |
| Parameter Okapi BM25: k1                           | 1.5                      |
| Parameter Okapi BM25: b                            | 0.75                     |
| Ambang Batas Relevansi Evaluasi                    | >= 60% token kueri cocok |

### Tabel 1.2: Distribusi Jumlah Resep per Kategori Bahan
| Category   |   Jumlah Resep |   Persentase (%) |
|:-----------|---------------:|-----------------:|
| udang      |           1994 |            12.79 |
| tempe      |           1985 |            12.73 |
| tahu       |           1984 |            12.72 |
| telur      |           1972 |            12.65 |
| sapi       |           1942 |            12.45 |
| ikan       |           1932 |            12.39 |
| ayam       |           1901 |            12.19 |
| kambing    |           1883 |            12.08 |

---

## 2. CONTOH DATA MENTAH (RAW CORPUS SAMPLES)

Berikut adalah 3 baris sampel resep masakan yang diambil langsung dari hasil penggabungan file CSV pada direktori `./data/`.

### Tabel 2.1: Sampel Data Mentah Resep Masakan
| DocID     | Category   | Title                    | Ingredients                                                                                                       |
|:----------|:-----------|:-------------------------|:------------------------------------------------------------------------------------------------------------------|
| DOC_00001 | ayam       | Ayam Woku Manado         | 1 Ekor Ayam Kampung (potong 12)--2 Buah Jeruk Nipis--2 Sdm Garam--3 Ruas Kunyit--7 Bawang Merah--7 Bawang Puti... |
| DOC_00002 | ayam       | Ayam goreng tulang lunak | 1 kg ayam (dipotong sesuai selera jangan kecil2 ya)--2 batang serai (memarkan)--4 lembar daun jeruk--7 butir b... |
| DOC_00003 | ayam       | Ayam cabai kawin         | 1/4 kg ayam--3 buah cabai hijau besar--7 buah cabai merah rawit--3 siung bawang putih--2 siung bawang merah--s... |

---

## 3. TABEL JEJAK PREPROCESSING BERURUTAN (STEP-BY-STEP TRACE)

Tabel di bawah ini memperlihatkan jejak perubahan teks komposisi bahan dari satu resep representatif (`DOC_00001` - *Ayam Woku Manado*) melalui seluruh tahapan pipeline preprocessing.

### Tabel 3.1: Jejak Tahapan Preprocessing Teks Komposisi Bahan
| Tahapan                       | Deskripsi                                                 | Output / Hasil Transformasi                                                                                                                                                                             |
|:------------------------------|:----------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Data Mentah (Raw Input)       | Teks asli kolom Ingredients dari dataset                  | 1 Ekor Ayam Kampung (potong 12)--2 Buah Jeruk Nipis--2 Sdm Garam--3 Ruas Kunyit--7 Bawang Merah--7 Bawang Putih--10 Cabe Merah--10 Cabe Rawi...                                                         |
| a. Delimiter Replacement      | Mengganti tanda '--' dengan spasi                         | 1 Ekor Ayam Kampung (potong 12) 2 Buah Jeruk Nipis 2 Sdm Garam 3 Ruas Kunyit 7 Bawang Merah 7 Bawang Putih 10 Cabe Merah 10 Cabe Rawit Merah...                                                         |
| b. Case Folding               | Mengubah seluruh karakter ke huruf kecil (lowercase)      | 1 ekor ayam kampung (potong 12) 2 buah jeruk nipis 2 sdm garam 3 ruas kunyit 7 bawang merah 7 bawang putih 10 cabe merah 10 cabe rawit merah...                                                         |
| c. Regex Cleaning             | Menghapus angka, pecahan (1/2, 3/4), simbol, tanda baca   | ekor ayam kampung potong buah jeruk nipis sdm garam ruas kunyit bawang merah bawang putih cabe merah cabe rawit merah sesuai selera butir ke...                                                         |
| d. Tokenization               | Memecah teks menjadi daftar kata tunggal                  | ['ekor', 'ayam', 'kampung', 'potong', 'buah', 'jeruk', 'nipis', 'sdm', 'garam', 'ruas', 'kunyit', 'bawang'] ...                                                                                         |
| e. Stopword Removal (Lapis 1) | Menghapus stopword umum bahasa Indonesia (Sastrawi)       | ['ekor', 'ayam', 'kampung', 'potong', 'buah', 'jeruk', 'nipis', 'sdm', 'garam', 'ruas', 'kunyit', 'bawang'] ...                                                                                         |
| e. Stopword Removal (Lapis 2) | Menghapus stopword takaran & cara pengolahan kuliner      | ['ayam', 'kampung', 'jeruk', 'nipis', 'garam', 'kunyit', 'bawang', 'merah', 'bawang', 'putih', 'cabe', 'merah'] ...                                                                                     |
| f. Stemming (PySastrawi)      | Mengubah kata ke bentuk dasar menggunakan kamus akar kata | ['ayam', 'kampung', 'jeruk', 'nipis', 'garam', 'kunyit', 'bawang', 'merah', 'bawang', 'putih', 'cabe', 'merah', 'cabe', 'rawit', 'merah', 'kemiri', 'sereh', 'daun', 'daun', 'kemangi', 'sedap', 'air'] |

---

## 4. CUPLIKAN STRUKTUR INVERTED INDEX (SPARSE IR)

Inverted Index dibangun murni (*from scratch*) tanpa library eksternal black-box. Struktur data memetakan setiap term bahan bersih ke daftar dokumen beserta frekuensi kemunculannya (*postings list*).

### Tabel 4.1: Cuplikan 5 Term Bahan Terpopuler dan Sampel Postings List
| Term (Bahan)   |   Document Frequency (DF) |   Collection Frequency (CF) | Sampel Postings List (5 Teratas)                                            |
|:---------------|--------------------------:|----------------------------:|:----------------------------------------------------------------------------|
| bawang         |                    14,409 |                      31,503 | {DOC_00001: 2, DOC_00002: 1, DOC_00003: 2, DOC_00005: 1, DOC_00006: 2, ...} |
| putih          |                    13,576 |                      16,513 | {DOC_00001: 1, DOC_00002: 1, DOC_00003: 1, DOC_00004: 1, DOC_00005: 1, ...} |
| garam          |                    12,856 |                      13,930 | {DOC_00001: 1, DOC_00002: 1, DOC_00003: 1, DOC_00004: 1, DOC_00007: 1, ...} |
| merah          |                    10,960 |                      18,678 | {DOC_00001: 3, DOC_00003: 3, DOC_00004: 1, DOC_00006: 3, DOC_00007: 1, ...} |
| gula           |                     8,163 |                       8,796 | {DOC_00003: 1, DOC_00004: 1, DOC_00006: 1, DOC_00007: 1, DOC_00008: 1, ...} |

---

## 5. PENGUJIAN 5 SKENARIO KUERI DAN EVALUASI SISTEM

Pengujian dilakukan menggunakan 5 skenario kueri kombinasi bahan masakan realistis. Suatu dokumen dianggap **Relevan** apabila memuat minimal **60%** dari total token bahan pada kueri (Rasio Kecocokan $\ge 60\%$).

### Tabel 5.1: Rekapitulasi Metrik Evaluasi Precision@5 dan Precision@10
| Skenario                                    | Kueri Bahan                                          | Token Kueri                                             | Jumlah Token   | Relevan @5   | Precision@5   | Relevan @10   | Precision@10   |
|:--------------------------------------------|:-----------------------------------------------------|:--------------------------------------------------------|:---------------|:-------------|:--------------|:--------------|:---------------|
| Skenario 1: Olahan Ayam Santan Bumbu Rempah | ayam, bawang merah, santan, cabai, serai             | santan, merah, cabai, bawang, serai, ayam               | 6              | 5/5          | 100.00%       | 10/10         | 100.00%        |
| Skenario 2: Olahan Telur Balado Tradisional | telur, tomat, cabai merah, bawang merah, gula        | merah, cabai, bawang, tomat, telur, gula                | 6              | 5/5          | 100.00%       | 10/10         | 100.00%        |
| Skenario 3: Olahan Tahu Tempe Kecap Gurih   | tempe, tahu, kecap manis, bawang putih, cabai rawit  | tempe, kecap, putih, manis, rawit, cabai, bawang        | 7              | 5/5          | 100.00%       | 9/10          | 90.00%         |
| Skenario 4: Olahan Sup Daging Sapi Rempah   | daging sapi, wortel, pala, seledri, merica           | seledri, pala, sapi, daging, merica, wortel             | 6              | 5/5          | 100.00%       | 10/10         | 100.00%        |
| Skenario 5: Olahan Udang Saus Asam Manis    | udang, bawang bombay, saus tomat, nanas, jeruk nipis | jeruk, saus, bombay, nipis, udang, bawang, nanas, tomat | 8              | 5/5          | 100.00%       | 10/10         | 100.00%        |
| **RATA-RATA (MACRO AVG)**                   | -                                                    | -                                                       | -              | -            | **100.00%**   | -             | **98.00%**     |

---

### Rincian Hasil Perangkingan Top-10 untuk Tiap Skenario

#### Skenario 1: Olahan Ayam Santan Bumbu Rempah
- **Kueri Masukan:** `"ayam, bawang merah, santan, cabai, serai"`
- **Token Hasil Preprocessing:** `['santan', 'merah', 'cabai', 'bawang', 'serai', 'ayam']` (6 token)
- **Precision@5:** `100.00%` (5/5 dokumen relevan)
- **Precision@10:** `100.00%` (10/10 dokumen relevan)

|   Peringkat | DocID     | Judul Resep                     | Kategori   |   Skor BM25 | Bahan Cocok                               |   |M| |   |D| | Status Relevansi   |
|------------:|:----------|:--------------------------------|:-----------|------------:|:------------------------------------------|------:|------:|:-------------------|
|           1 | DOC_00801 | Ayam cabai hijau                | ayam       |     10.0858 | ayam, bawang, cabai, merah, santan, serai |     6 |    20 | Relevan            |
|           2 | DOC_14226 | Sambal goreng udang             | udang      |      9.3237 | bawang, cabai, merah, santan, serai       |     5 |    18 | Relevan            |
|           3 | DOC_00327 | Tongseng Ayam ala ala           | ayam       |      9.2974 | ayam, bawang, cabai, merah, santan, serai |     6 |    19 | Relevan            |
|           4 | DOC_13251 | Sambal goreng hati ampela tempe | tempe      |      9.2825 | ayam, cabai, merah, santan, serai         |     5 |    26 | Relevan            |
|           5 | DOC_00709 | Opor ayam                       | ayam       |      9.0808 | ayam, bawang, cabai, merah, santan, serai |     6 |    26 | Relevan            |
|           6 | DOC_02555 | Pesmol Gurame                   | ikan       |      9.0392 | bawang, cabai, merah, santan, serai       |     5 |    17 | Relevan            |
|           7 | DOC_04820 | Tongseng Kambing Pedaz          | kambing    |      9.0386 | bawang, cabai, merah, santan, serai       |     5 |    12 | Relevan            |
|           8 | DOC_02587 | Acar kuning ikan nila           | ikan       |      8.9953 | ayam, bawang, cabai, merah, santan, serai |     6 |    33 | Relevan            |
|           9 | DOC_00041 | Ayam Garang Asem                | ayam       |      8.7828 | ayam, bawang, cabai, merah, santan, serai |     6 |    27 | Relevan            |
|          10 | DOC_01310 | Ayam suwir                      | ayam       |      8.4801 | ayam, bawang, cabai, merah, santan, serai |     6 |    30 | Relevan            |


#### Skenario 2: Olahan Telur Balado Tradisional
- **Kueri Masukan:** `"telur, tomat, cabai merah, bawang merah, gula"`
- **Token Hasil Preprocessing:** `['merah', 'cabai', 'bawang', 'tomat', 'telur', 'gula']` (6 token)
- **Precision@5:** `100.00%` (5/5 dokumen relevan)
- **Precision@10:** `100.00%` (10/10 dokumen relevan)

|   Peringkat | DocID     | Judul Resep                                      | Kategori   |   Skor BM25 | Bahan Cocok                              |   |M| |   |D| | Status Relevansi   |
|------------:|:----------|:-------------------------------------------------|:-----------|------------:|:-----------------------------------------|------:|------:|:-------------------|
|           1 | DOC_11031 | Sambal goreng ati ampela dan telur dadar non msg | telur      |      7.7715 | bawang, cabai, gula, merah, telur, tomat |     6 |    15 | Relevan            |
|           2 | DOC_10897 | Telur Ceplok Sambal Matah                        | telur      |      7.5569 | bawang, cabai, gula, merah, telur, tomat |     6 |    17 | Relevan            |
|           3 | DOC_11502 | Balado Telur Pete                                | telur      |      7.4778 | bawang, cabai, gula, merah, telur, tomat |     6 |    17 | Relevan            |
|           4 | DOC_09897 | Sambal telor bulat                               | telur      |      7.4675 | bawang, cabai, gula, merah, telur, tomat |     6 |    11 | Relevan            |
|           5 | DOC_10449 | Telur Cabe Ijo                                   | telur      |      7.4675 | bawang, cabai, gula, merah, telur, tomat |     6 |    11 | Relevan            |
|           6 | DOC_11209 | 🌶 telur sambal ijo 🌶                             | telur      |      7.4675 | bawang, cabai, gula, merah, telur, tomat |     6 |    11 | Relevan            |
|           7 | DOC_11577 | Balado Telur Ceplok                              | telur      |      7.4265 | bawang, cabai, gula, merah, telur, tomat |     6 |    12 | Relevan            |
|           8 | DOC_09712 | Telur Ceplok Balado                              | telur      |      7.3394 | bawang, cabai, gula, merah, telur, tomat |     6 |    18 | Relevan            |
|           9 | DOC_10603 | Balado telur pedas                               | telur      |      7.3394 | bawang, cabai, gula, merah, telur, tomat |     6 |    18 | Relevan            |
|          10 | DOC_14981 | Udang Krispi, Sambal Jawa                        | udang      |      7.3394 | bawang, cabai, gula, merah, telur, tomat |     6 |    18 | Relevan            |


#### Skenario 3: Olahan Tahu Tempe Kecap Gurih
- **Kueri Masukan:** `"tempe, tahu, kecap manis, bawang putih, cabai rawit"`
- **Token Hasil Preprocessing:** `['tempe', 'kecap', 'putih', 'manis', 'rawit', 'cabai', 'bawang']` (7 token)
- **Precision@5:** `100.00%` (5/5 dokumen relevan)
- **Precision@10:** `90.00%` (9/10 dokumen relevan)

|   Peringkat | DocID     | Judul Resep                  | Kategori   |   Skor BM25 | Bahan Cocok                                      |   |M| |   |D| | Status Relevansi   |
|------------:|:----------|:-----------------------------|:-----------|------------:|:-------------------------------------------------|------:|------:|:-------------------|
|           1 | DOC_11719 | Tempe orek iris              | tempe      |     10.3052 | bawang, cabai, kecap, manis, putih, rawit, tempe |     7 |    17 | Relevan            |
|           2 | DOC_11669 | Tempe kecap                  | tempe      |      9.9845 | bawang, cabai, kecap, manis, putih, rawit, tempe |     7 |    11 | Relevan            |
|           3 | DOC_12734 | Oseng soon tempe pedas...... | tempe      |      9.7766 | bawang, cabai, kecap, manis, putih, rawit, tempe |     7 |    18 | Relevan            |
|           4 | DOC_13543 | Oseng Tempe Pedas Manis      | tempe      |      9.5653 | bawang, cabai, kecap, manis, putih, rawit, tempe |     7 |    19 | Relevan            |
|           5 | DOC_12329 | Tempe Kecap                  | tempe      |      9.5652 | bawang, cabai, kecap, manis, putih, rawit, tempe |     7 |    17 | Relevan            |
|           6 | DOC_13288 | Orek Tempe                   | tempe      |      9.5585 | bawang, cabai, kecap, manis, putih, rawit, tempe |     7 |    24 | Relevan            |
|           7 | DOC_13226 | Oseng Tempe Tahu untuk Diet  | tempe      |      9.3465 | cabai, kecap, manis, tempe                       |     4 |     7 | Tidak Relevan      |
|           8 | DOC_12097 | Tumis kacang tempe           | tempe      |      9.1405 | bawang, cabai, kecap, manis, putih, rawit, tempe |     7 |    19 | Relevan            |
|           9 | DOC_12718 | Oseng Tempe Sederhana        | tempe      |      9.1405 | bawang, cabai, kecap, manis, putih, rawit, tempe |     7 |    19 | Relevan            |
|          10 | DOC_08505 | Oseng Kecap Tahu Tempe       | tahu       |      8.862  | bawang, cabai, kecap, manis, putih, rawit, tempe |     7 |    21 | Relevan            |


#### Skenario 4: Olahan Sup Daging Sapi Rempah
- **Kueri Masukan:** `"daging sapi, wortel, pala, seledri, merica"`
- **Token Hasil Preprocessing:** `['seledri', 'pala', 'sapi', 'daging', 'merica', 'wortel']` (6 token)
- **Precision@5:** `100.00%` (5/5 dokumen relevan)
- **Precision@10:** `100.00%` (10/10 dokumen relevan)

|   Peringkat | DocID     | Judul Resep             | Kategori   |   Skor BM25 | Bahan Cocok                                 |   |M| |   |D| | Status Relevansi   |
|------------:|:----------|:------------------------|:-----------|------------:|:--------------------------------------------|------:|------:|:-------------------|
|           1 | DOC_06570 | Sop Daging Sapi         | sapi       |     13.1844 | daging, merica, pala, sapi, seledri, wortel |     6 |    21 | Relevan            |
|           2 | DOC_06674 | Sop Daging Sapi         | sapi       |     13.1844 | daging, merica, pala, sapi, seledri, wortel |     6 |    21 | Relevan            |
|           3 | DOC_07430 | Sup Daging Sapi         | sapi       |     12.9502 | daging, merica, pala, sapi, seledri, wortel |     6 |    25 | Relevan            |
|           4 | DOC_07587 | Sop daging sapi         | sapi       |     12.9188 | daging, merica, pala, sapi, seledri, wortel |     6 |    22 | Relevan            |
|           5 | DOC_06107 | Sop Daging Sapi         | sapi       |     12.7531 | daging, pala, sapi, seledri, wortel         |     5 |    17 | Relevan            |
|           6 | DOC_06891 | Sup Daging Sapi non Msg | sapi       |     12.7531 | daging, pala, sapi, seledri, wortel         |     5 |    17 | Relevan            |
|           7 | DOC_07569 | Sop Daging Sapi         | sapi       |     12.7208 | daging, pala, sapi, seledri, wortel         |     5 |    20 | Relevan            |
|           8 | DOC_06665 | Sop daging sapi         | sapi       |     12.6638 | daging, merica, pala, sapi, seledri, wortel |     6 |    23 | Relevan            |
|           9 | DOC_06320 | Sup kaki sapi segar     | sapi       |     12.6426 | merica, pala, sapi, seledri, wortel         |     5 |    17 | Relevan            |
|          10 | DOC_07450 | Sop Iga Sapi            | sapi       |     12.6173 | merica, pala, sapi, seledri, wortel         |     5 |    20 | Relevan            |


#### Skenario 5: Olahan Udang Saus Asam Manis
- **Kueri Masukan:** `"udang, bawang bombay, saus tomat, nanas, jeruk nipis"`
- **Token Hasil Preprocessing:** `['jeruk', 'saus', 'bombay', 'nipis', 'udang', 'bawang', 'nanas', 'tomat']` (8 token)
- **Precision@5:** `100.00%` (5/5 dokumen relevan)
- **Precision@10:** `100.00%` (10/10 dokumen relevan)

|   Peringkat | DocID     | Judul Resep                                   | Kategori   |   Skor BM25 | Bahan Cocok                                      |   |M| |   |D| | Status Relevansi   |
|------------:|:----------|:----------------------------------------------|:-----------|------------:|:-------------------------------------------------|------:|------:|:-------------------|
|           1 | DOC_04291 | Iga Kambing teriyaki                          | kambing    |     13.811  | bawang, bombay, jeruk, nanas, nipis, saus        |     6 |    21 | Relevan            |
|           2 | DOC_02876 | Gurame Tepung Asam Manis                      | ikan       |     13.3465 | bawang, bombay, jeruk, nanas, nipis, saus, tomat |     7 |    38 | Relevan            |
|           3 | DOC_13856 | Udang Asam Manis                              | udang      |     12.9575 | bawang, bombay, jeruk, nipis, saus, tomat, udang |     7 |    19 | Relevan            |
|           4 | DOC_13973 | Udang Saus Padang #KisahKasihCookpad          | udang      |     12.7107 | bawang, bombay, jeruk, nipis, saus, tomat, udang |     7 |    25 | Relevan            |
|           5 | DOC_14287 | Udang asam manis pedas ala kadarnya 😁        | udang      |     12.6637 | bawang, bombay, jeruk, nipis, saus, tomat, udang |     7 |    25 | Relevan            |
|           6 | DOC_14871 | Udang Asam Manis                              | udang      |     12.3382 | bawang, bombay, jeruk, nipis, saus, tomat, udang |     7 |    24 | Relevan            |
|           7 | DOC_15477 | Udang Tepung Saus Asam Manis + Vegetables mix | udang      |     12.1153 | bawang, bombay, jeruk, nipis, saus, tomat, udang |     7 |    25 | Relevan            |
|           8 | DOC_14761 | Udang Galah Asam Pedas Manis                  | udang      |     12.0664 | bawang, bombay, jeruk, nipis, saus, tomat, udang |     7 |    35 | Relevan            |
|           9 | DOC_04353 | Sate Kambing #Kitaberbagi                     | kambing    |     11.9875 | bawang, jeruk, nanas, nipis, tomat               |     5 |    19 | Relevan            |
|          10 | DOC_14909 | Udang Saus Padang                             | udang      |     11.7598 | bawang, bombay, jeruk, nipis, saus, tomat, udang |     7 |    27 | Relevan            |


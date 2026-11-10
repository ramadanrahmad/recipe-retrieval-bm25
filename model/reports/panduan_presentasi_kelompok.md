# Panduan Presentasi Kelompok: Sistem Temu Kembali Resep Berbasis Okapi BM25
*Materi Slide & Naskah Presentasi (Pitch Deck) Ujian Tengah / Akhir Semester Temu Kembali Informasi (TKI)*

---

### Slide 1: Judul Proyek & Pengenalan Tim
* **Judul:** Sistem Temu Kembali Resep Masakan Indonesia Berbasis Kueri Komposisi Bahan Menggunakan Algoritma Okapi BM25
* **Sub-judul:** *Ingredient-Based Recipe Retrieval with Custom Culinary Preprocessing & Sparse Indexing*
* **Mata Kuliah:** Temu Kembali Informasi (Information Retrieval)
* **Anggota Tim:** [Nama Lengkap & NIM Seluruh Anggota Kelompok]
* **Poin Bicara:** 
  > *"Selamat pagi/siang Bapak/Ibu dosen dan rekan-rekan. Hari ini kelompok kami mempresentasikan proyek sistem temu kembali informasi yang membalikkan cara pencarian resep masakan secara cerdas berdasarkan sisa bahan mentah yang ada di dapur menggunakan algoritma Okapi BM25."*

---

### Slide 2: Latar Belakang & Urgensi Masalah
* **Fenomena Dunia Nyata:** 
  - Tingginya limbah makanan rumah tangga (*food waste*) akibat bahan sisa di kulkas membusuk karena pemilik bingung ingin memasak apa.
* **Keterbatasan Sistem Konvensional:**
  - Platform resep saat ini (Cookpad, MasakApaHariIni, dll.) bekerja satu arah: pengguna harus tahu nama makanannya dulu (misal: "Soto Ayam"), baru melihat bahannya.
  - Pengguna tidak bisa memasukkan sekumpulan bahan acak yang tersisa (misal: "ayam, santan, cabai, serai") untuk dicarikan resep yang cocok.
* **Poin Bicara:**
  > *"Sistem kami hadir untuk membalik paradigma tersebut: dari pencarian berbasis nama menu menjadi pencarian berbasis ketersediaan bahan dapur, guna membantu menekan angka pemborosan pangan."*

---

### Slide 3: Masalah Teknis di Bidang TKI (*Problem Statement*)
* **Tantangan Karakteristik Teks Kuliner:**
  - **Sangat Berisik (*Noisy Text*):** Komposisi bahan bercampur dengan angka takaran (`500 gr`, `1/2 sdt`), satuan ukur (`sdm`, `siung`, `batang`), dan instruksi (`cincang halus`, `memarkan`).
  - **Variasi Panjang Dokumen Ekstrem:** Resep masakan sederhana hanya butuh 4 bahan, sedangkan resep kompleks butuh lebih dari 25 bahan.
  - **Kelemahan Model Konvensional:** TF-IDF dan Jaccard Similarity gagal mengatasi dominasi kata takaran dan bias dokumen resep panjang.
* **Poin Bicara:**
  > *"Tantangan terbesarnya adalah data resep sangat berisik. Kata 'sendok' atau 'gram' sering kali memiliki frekuensi lebih tinggi daripada nama bahan utamanya. Selain itu, resep berukuran panjang cenderung mendominasi hasil pencarian jika tidak dinormalisasi secara tepat."*

---

### Slide 4: Solusi yang Diusulkan & Nilai Kebaruan (*Novelty*)
* **Solusi Utama:**
  - Arsitektur *Sparse Information Retrieval* berbasis *Inverted Index*.
  - Pembobotan probabilistik **Okapi BM25** dengan parameter penalti panjang dokumen ($b$) dan saturasi frekuensi ($k_1$).
* **Nilai Kebaruan (*Novelty*):**
  - **Custom Culinary Stopword Removal:** Penyaringan dua lapis untuk membuang satuan takaran pangan dan istilah cara pengolahan sebelum proses pengindeksan.
  - **Optimasi Persistent Caching Stemmer:** Mempercepat proses *stemming* 13 ribu resep menjadi di bawah 1 detik.
* **Poin Bicara:**
  > *"Kebaruan dari penelitian kami adalah penerapan kamus stopword kuliner khusus untuk memfilter kata-kata takaran kotor, sehingga Inverted Index yang terbangun murni hanya memuat entitas bahan pangan esensial."*

---

### Slide 5: Desain Arsitektur Sistem (Dua Jalur Paralel)
* **Diagram Alur (Berdasarkan Gambar 1 di Laporan):**
  1. **Jalur Offline (Proses Indexing):**
     `Dataset 7 CSV Kaggle (13.074 Resep)` $\rightarrow$ `Text Preprocessing (Case Folding, Regex, Culinary Stopwords, Sastrawi)` $\rightarrow$ `Inverted Index Builder` $\rightarrow$ `Basis Data Indeks (V = 5.170, avgdl = 21,72)`.
  2. **Jalur Online (Proses Query & Retrieval):**
     `Kueri Bahan Acak Pengguna` $\rightarrow$ `Preprocessing Kueri` $\rightarrow$ `Pencocokan Inverted Index` $\rightarrow$ `BM25 Scoring (k1=1.2, b=0.75)` $\rightarrow$ `Top-K Ranking Rekomendasi`.
* **Poin Bicara:**
  > *"Arsitektur kami memisahkan pemrosesan berat secara offline ke dalam Inverted Index, sehingga proses pencarian online oleh pengguna berlangsung sangat kilat dalam waktu sekitar 0,028 detik."*

---

### Slide 6: Prapemrosesan Teks Khusus Komposisi Bahan
* **5 Tahapan Pembersihan:**
  1. *Delimiter Replacement & Case Folding* (`--` diganti spasi, huruf kecil semua).
  2. *Regex Cleaning* (Hapus angka pecahan $1/2, 3/4$ dan simbol `[^a-z\s]`).
  3. *Tokenization* (Pemecahan kata individual).
  4. *Custom Culinary Stopwords* (Hapus satuan: *sdm, sdt, gram, siung*, dan kata kerja: *cincang, iris, haluskan*).
  5. *Stemming Nazief & Adriani* (Sastrawi).
* **Hasil Reduksi Dimensi:**
  - Kosakata awal: 6.430 kata unik.
  - Kosakata bersih: 5.170 kata unik (**Reduksi efisiensi sebesar 19,60%**).
* **Poin Bicara:**
  > *"Berdasarkan Tabel 3 di laporan, kalimat mentah '1/2 kg ayam potong, 3 siung bawang putih cincang halus, 1 sdt garam' berhasil dimurnikan menjadi 4 token bahan murni: ['ayam', 'bawang', 'putih', 'garam']."*

---

### Slide 7: Pembangunan Inverted Index & Formulasi Okapi BM25
* **Struktur Data Inverted Index:**
  - *Vocabulary* ($V = 5.170$ kata) dan *Postings List* (`term -> {DocID: TF}`).
* **Formulasi Matematis:**
  $$\text{IDF}(q_i) = \ln\left(\frac{N - n(q_i) + 0.5}{n(q_i) + 0.5} + 1\right)$$
  $$\text{Score}(D, Q) = \sum_{q_i \in Q} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{avgdl}\right)}$$
* **Parameter Optimal:**
  - $N = 13.074$ resep, $avgdl = 21{,}7248$ token.
  - $k_1 = 1{,}2$: Mengatur saturasi frekuensi kata.
  - $b = 0{,}75$: Normalisasi panjang resep agar resep sederhana tidak tergeser oleh resep dengan puluhan bumbu tambahan.
* **Poin Bicara:**
  > *"Rumus BM25 ini menggunakan smoothing +1 pada IDF agar selalu positif, dan parameter b = 0,75 menjamin keadilan pemeringkatan bagi resep dengan daftar bahan yang pendek."*

---

### Slide 8: Hasil Evaluasi Model pada 5 Skenario Kuliner
* **Tabel Hasil Pengujian (Relevance Threshold $\ge 60\%$):**
  - **SKN_1** (Ayam Santan Rempah): P@5 = 100%, P@10 = 100%, AP = 1.0000
  - **SKN_2** (Telur Balado Tradisional): P@5 = 100%, P@10 = 100%, AP = 1.0000
  - **SKN_3** (Tahu Tempe Kecap Gurih): P@5 = 100%, P@10 = 90%, AP = 0.9627
  - **SKN_4** (Sup Sapi Rempah): P@5 = 100%, P@10 = 100%, AP = 1.0000
  - **SKN_5** (Ikan Gurame Asam Manis): P@5 = 100%, P@10 = 100%, AP = 1.0000
* **Rata-Rata Makro (Macro Average):**
  - **Macro-Average P@5: 100,00%**
  - **Macro-Average P@10: 98,00%**
  - **Mean Average Precision (MAP): 0,9925**
  - **Mean Reciprocal Rank (MRR): 1,0000** (Top-1 selalu relevan!)
* **Poin Bicara:**
  > *"Seluruh skenario menghasilkan rekomendasi Top-1 yang relevan dengan MRR sempurna 1,0000 dan Macro Precision@5 sebesar 100%."*

---

### Slide 9: Analisis Bebas Overfitting & Uji Robustness
* **Apakah Terjadi Overfitting?**
  - **TIDAK.** BM25 adalah algoritma *unsupervised probabilistic ranking* tanpa proses *training/weights optimization*, sehingga tidak dapat menghafal data (*no memorization*).
  - Skor presisi tinggi disebabkan oleh melimpahnya resep pada korpus (13 ribu resep) dan ketajaman fitur setelah *culinary filtering*.
* **Uji Ketahanan (*Robustness Test*):**
  - Ketika *threshold* dinaikkan menjadi sangat ketat ($\ge 80\%$), presisi skenario 5 terkoreksi menjadi 80%.
  - Ketika diuji dengan kueri bahan langka (*"ikan stroberi nanas"*), presisi P@5 terkoreksi menjadi 80%.
  - Ketika diuji dengan kueri kombinasi rumit (*"kambing keju susu brokoli"*), presisi P@10 turun ke 70%.
* **Poin Bicara:**
  > *"Pengujian kueri ekstrem membuktikan bahwa sistem kami tidak menghasilkan nilai tinggi secara artifisial, melainkan merespons variasi kueri secara matematis dan proporsional."*

---

### Slide 10: Kesimpulan & Demo Singkat
* **Kesimpulan:**
  1. Pipeline prapemrosesan khusus kuliner sukses mereduksi 19,60% noise takaran bahan.
  2. Model Okapi BM25 berhasil membalik paradigma pencarian resep masakan berbasis bahan dengan akurasi P@5 100% dan waktu temu kembali rata-rata 0,028 detik.
* **Demonstrasi Inferensi:**
  - Menunjukkan eksekusi fungsi `predict_recipe("ikan gurame asam manis nanas cabai")` langsung di Jupyter Notebook / Terminal.
* **Poin Bicara:**
  > *"Demikian presentasi dari kelompok kami. Sistem ini telah siap diimplementasikan dan dikembangkan lebih lanjut ke tahap antarmuka web di masa mendatang. Terima kasih, kami membuka sesi tanya jawab."*


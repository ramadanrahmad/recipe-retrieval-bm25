"""
Script Generator Tabel dan Artefak Laporan Paper UTS/UAS Temu Kembali Informasi (IR).
Mengeksekusi seluruh pipeline dari data mentah hingga evaluasi, mencetak tabel ke terminal,
dan mengekspor seluruh artefak dalam format Markdown siap pakai ke reports/report_paper_artifacts.md.
"""

import os
import sys
import time
import pickle
import pandas as pd
from tabulate import tabulate

# Pastikan encoding console Windows mendukung karakter UTF-8
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.config import (
    DATA_DIR,
    STORAGE_DIR,
    REPORTS_DIR,
    INDEX_FILE_PKL,
    INDEX_FILE_JSON,
    RECIPES_META_PKL,
    REPORT_MD_FILE,
    DEFAULT_K1,
    DEFAULT_B,
)
from src.data_loader import load_and_merge_datasets, get_corpus_category_distribution
from src.preprocessor import TextPreprocessor
from src.inverted_index import InvertedIndex
from src.bm25 import BM25Okapi
from src.evaluator import RecipeRetrievalEvaluator


def format_markdown_table(df: pd.DataFrame) -> str:
    """Format DataFrame ke tabel GitHub Flavored Markdown."""
    return tabulate(df, headers="keys", tablefmt="pipe", showindex=False)


def run_full_pipeline_and_generate_artifacts():
    start_total_time = time.time()
    os.makedirs(STORAGE_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    print("=" * 80)
    print("SISTEM TEMU KEMBALI RESEP MASAKAN INDONESIA - ALGORITMA OKAPI BM25")
    print("EKSEKUSI PIPELINE & PEMBUATAN ARTEFAK LAPORAN PAPER")
    print("=" * 80)

    # -------------------------------------------------------------
    # 1. AKUISISI & PENGGABUNGAN DATASET
    # -------------------------------------------------------------
    print("\n[1/5] Memuat dan menggabungkan seluruh file CSV dataset...")
    df_recipes = load_and_merge_datasets(data_dir=DATA_DIR)
    total_docs_N = len(df_recipes)
    print(f"-> Berhasil menggabungkan dataset: Total {total_docs_N:,} resep bersih.")

    # Simpan metadata resep untuk pencarian cepat
    with open(RECIPES_META_PKL, "wb") as f:
        pickle.dump(df_recipes, f, protocol=pickle.HIGHEST_PROTOCOL)

    # Distribusi Kategori
    dist_df = get_corpus_category_distribution(df_recipes)

    # -------------------------------------------------------------
    # 2. PREPROCESSING KORPUS & STEMMING TEROPTIMASI
    # -------------------------------------------------------------
    print("\n[2/5] Menjalankan pipeline text preprocessing pada kolom 'Ingredients'...")
    preprocessor = TextPreprocessor(use_stem_cache=True)
    t0_prep = time.time()
    
    docs_tokens_list, vocab_size_before, vocab_size_after = preprocessor.fit_and_transform_corpus(
        df_recipes["Ingredients"].tolist(), show_progress=True
    )
    prep_duration = time.time() - t0_prep
    print(f"-> Preprocessing selesai dalam {prep_duration:.2f} detik.")
    print(f"-> Ukuran Kosakata (Vocabulary) sebelum preprocessing: {vocab_size_before:,} token.")
    print(f"-> Ukuran Kosakata (Vocabulary) setelah preprocessing & stemming: {vocab_size_after:,} token.")

    # Mapping doc_id -> tokens
    docs_tokens_dict = {
        doc_id: tokens
        for doc_id, tokens in zip(df_recipes["DocID"], docs_tokens_list)
    }

    # -------------------------------------------------------------
    # 3. PEMBENTUKAN INVERTED INDEX DARI NOL
    # -------------------------------------------------------------
    print("\n[3/5] Membangun Inverted Index (from scratch)...")
    inv_index = InvertedIndex()
    inv_index.build(docs_tokens_dict)
    
    # Simpan indeks ke pickle dan sampel json
    inv_index.save(INDEX_FILE_PKL)
    inv_index.export_sample_json(INDEX_FILE_JSON, top_terms=10, postings_limit=5)
    print(f"-> Inverted Index berhasil disimpan ke: {INDEX_FILE_PKL}")
    print(f"-> Sampel JSON diekspor ke: {INDEX_FILE_JSON}")
    print(f"-> Nilai Rata-rata Panjang Dokumen (avgdl): {inv_index.avgdl:.4f} token.")

    # -------------------------------------------------------------
    # 4. INISIALISASI OKAPI BM25 & PENGUJIAN 5 SKENARIO
    # -------------------------------------------------------------
    print("\n[4/5] Menginisialisasi Mesin Okapi BM25 dan menjalankan pengujian evaluasi...")
    bm25 = BM25Okapi(inv_index, k1=DEFAULT_K1, b=DEFAULT_B)
    evaluator = RecipeRetrievalEvaluator(
        bm25_engine=bm25,
        preprocessor=preprocessor,
        recipes_df=df_recipes,
        relevance_threshold=0.60,
    )

    scenarios = [
        {
            "name": "Skenario 1: Olahan Ayam Santan Bumbu Rempah",
            "query": "ayam, bawang merah, santan, cabai, serai",
        },
        {
            "name": "Skenario 2: Olahan Telur Balado Tradisional",
            "query": "telur, tomat, cabai merah, bawang merah, gula",
        },
        {
            "name": "Skenario 3: Olahan Tahu Tempe Kecap Gurih",
            "query": "tempe, tahu, kecap manis, bawang putih, cabai rawit",
        },
        {
            "name": "Skenario 4: Olahan Sup Daging Sapi Rempah",
            "query": "daging sapi, wortel, pala, seledri, merica",
        },
        {
            "name": "Skenario 5: Olahan Ikan Asam Manis Segar",
            "query": "ikan gurame nanas tomat saus bawang bombay",
        },
    ]

    detailed_eval_results, summary_eval_df = evaluator.evaluate_scenarios(scenarios, top_k=10)

    # -------------------------------------------------------------
    # 5. PEMBUATAN ARTEFAK LAPORAN MARKDOWN
    # -------------------------------------------------------------
    print("\n[5/5] Menyusun artefak tabel laporan untuk paper UTS/UAS...")

    # A. Tabel Sampel Data Mentah (3 Resep)
    sample_raw_df = df_recipes.head(3)[["DocID", "Category", "Title", "Ingredients"]].copy()
    # Rapikan tampilan teks agar tidak terlalu panjang di tabel
    sample_raw_df["Ingredients"] = sample_raw_df["Ingredients"].apply(
        lambda x: x[:110] + "..." if len(x) > 110 else x
    )

    # B. Tabel Jejak Preprocessing Berurutan (1 Resep Representatif)
    trace_recipe = df_recipes.iloc[0]
    trace_result = preprocessor.trace_pipeline(trace_recipe["Ingredients"])
    
    trace_table_data = [
        {"Tahapan": "Data Mentah (Raw Input)", "Deskripsi": "Teks asli kolom Ingredients dari dataset", "Output / Hasil Transformasi": trace_result["Raw"][:140] + "..."},
        {"Tahapan": "a. Delimiter Replacement", "Deskripsi": "Mengganti tanda '--' dengan spasi", "Output / Hasil Transformasi": trace_result["Step_A_Delimiter_Replacement"][:140] + "..."},
        {"Tahapan": "b. Case Folding", "Deskripsi": "Mengubah seluruh karakter ke huruf kecil (lowercase)", "Output / Hasil Transformasi": trace_result["Step_B_Case_Folding"][:140] + "..."},
        {"Tahapan": "c. Regex Cleaning", "Deskripsi": "Menghapus angka, pecahan (1/2, 3/4), simbol, tanda baca", "Output / Hasil Transformasi": trace_result["Step_C_Regex_Cleaning"][:140] + "..."},
        {"Tahapan": "d. Tokenization", "Deskripsi": "Memecah teks menjadi daftar kata tunggal", "Output / Hasil Transformasi": str(trace_result["Step_D_Tokenization"][:12]) + " ..."},
        {"Tahapan": "e. Stopword Removal (Lapis 1)", "Deskripsi": "Menghapus stopword umum bahasa Indonesia (Sastrawi)", "Output / Hasil Transformasi": str(trace_result["Step_E_Stopword_Lapis1"][:12]) + " ..."},
        {"Tahapan": "e. Stopword Removal (Lapis 2)", "Deskripsi": "Menghapus stopword takaran & cara pengolahan kuliner", "Output / Hasil Transformasi": str(trace_result["Step_E_Stopword_Lapis2"][:12]) + " ..."},
        {"Tahapan": "f. Stemming (PySastrawi)", "Deskripsi": "Mengubah kata ke bentuk dasar menggunakan kamus akar kata", "Output / Hasil Transformasi": str(trace_result["Step_F_Stemming"])},
    ]
    trace_df = pd.DataFrame(trace_table_data)

    # C. Cuplikan Inverted Index (5 Term Terpopuler)
    top_5_terms = inv_index.get_top_terms_by_df(top_n=5)
    index_sample_rows = []
    for term, df, cf in top_5_terms:
        postings = inv_index.get_postings(term)
        sample_postings = dict(list(postings.items())[:5])
        sample_postings_str = ", ".join([f"{doc}: {tf}" for doc, tf in sample_postings.items()])
        index_sample_rows.append({
            "Term (Bahan)": term,
            "Document Frequency (DF)": f"{df:,}",
            "Collection Frequency (CF)": f"{cf:,}",
            "Sampel Postings List (5 Teratas)": "{" + sample_postings_str + ", ...}"
        })
    index_sample_df = pd.DataFrame(index_sample_rows)

    # D. Statistik Korpus
    corpus_stats_rows = [
        {"Parameter": "Total Dokumen Resep (N)", "Nilai": f"{total_docs_N:,} dokumen"},
        {"Parameter": "Jumlah Kategori Bahan Utama", "Nilai": f"{len(dist_df)} kategori"},
        {"Parameter": "Ukuran Vocabulary Sebelum Preprocessing", "Nilai": f"{vocab_size_before:,} token kata unik"},
        {"Parameter": "Ukuran Vocabulary Setelah Preprocessing & Stemming", "Nilai": f"{vocab_size_after:,} token kata unik"},
        {"Parameter": "Persentase Reduksi Dimensi Vocabulary", "Nilai": f"{((vocab_size_before - vocab_size_after) / vocab_size_before * 100):.2f}%"},
        {"Parameter": "Rata-rata Panjang Dokumen Bahan (avgdl)", "Nilai": f"{inv_index.avgdl:.4f} token per resep"},
        {"Parameter": "Parameter Okapi BM25: k1", "Nilai": f"{DEFAULT_K1}"},
        {"Parameter": "Parameter Okapi BM25: b", "Nilai": f"{DEFAULT_B}"},
        {"Parameter": "Ambang Batas Relevansi Evaluasi", "Nilai": ">= 60% token kueri cocok"},
    ]
    corpus_stats_df = pd.DataFrame(corpus_stats_rows)

    # Susun Dokumen Markdown Lengkap
    md_content = f"""# ARTEFAK LAPORAN PAPER TEMU KEMBALI INFORMASI (IR)
**Judul Paper:** Temu Kembali Resep Masakan Indonesia Berbasis Kueri Komposisi Bahan Menggunakan Algoritma Okapi BM25  
**Tanggal Eksekusi:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}  

---

## 1. STATISTIK KORPUS DAN DISTRIBUSI DATASET

Tabel berikut merangkum statistik teknis dari korpus resep masakan Indonesia setelah tahap pembersihan dan indeksasi.

### Tabel 1.1: Ringkasan Statistik Korpus Resep
{format_markdown_table(corpus_stats_df)}

### Tabel 1.2: Distribusi Jumlah Resep per Kategori Bahan
{format_markdown_table(dist_df)}

---

## 2. CONTOH DATA MENTAH (RAW CORPUS SAMPLES)

Berikut adalah 3 baris sampel resep masakan yang diambil langsung dari hasil penggabungan file CSV pada direktori `./data/`.

### Tabel 2.1: Sampel Data Mentah Resep Masakan
{format_markdown_table(sample_raw_df)}

---

## 3. TABEL JEJAK PREPROCESSING BERURUTAN (STEP-BY-STEP TRACE)

Tabel di bawah ini memperlihatkan jejak perubahan teks komposisi bahan dari satu resep representatif (`{trace_recipe['DocID']}` - *{trace_recipe['Title']}*) melalui seluruh tahapan pipeline preprocessing.

### Tabel 3.1: Jejak Tahapan Preprocessing Teks Komposisi Bahan
{format_markdown_table(trace_df)}

---

## 4. CUPLIKAN STRUKTUR INVERTED INDEX (SPARSE IR)

Inverted Index dibangun murni (*from scratch*) tanpa library eksternal black-box. Struktur data memetakan setiap term bahan bersih ke daftar dokumen beserta frekuensi kemunculannya (*postings list*).

### Tabel 4.1: Cuplikan 5 Term Bahan Terpopuler dan Sampel Postings List
{format_markdown_table(index_sample_df)}

---

## 5. PENGUJIAN 5 SKENARIO KUERI DAN EVALUASI SISTEM

Pengujian dilakukan menggunakan 5 skenario kueri kombinasi bahan masakan realistis. Suatu dokumen dianggap **Relevan** apabila memuat minimal **60%** dari total token bahan pada kueri (Rasio Kecocokan $\ge 60\%$).

### Tabel 5.1: Rekapitulasi Metrik Evaluasi Precision@5 dan Precision@10
{format_markdown_table(summary_eval_df)}

---

### Rincian Hasil Perangkingan Top-10 untuk Tiap Skenario
"""

    # Tambahkan rincian Top 10 untuk masing-masing skenario
    for idx, eval_res in enumerate(detailed_eval_results, start=1):
        sc_table = eval_res["results_table"].copy()
        if not sc_table.empty:
            cols_to_show = [
                "Rank",
                "DocID",
                "Title",
                "Category",
                "BM25_Score",
                "Matched_Ingredients",
                "Matched_Count",
                "Total_Recipe_Ingredients",
                "Relevance_Status",
            ]
            display_table = sc_table[cols_to_show].rename(
                columns={
                    "Rank": "Peringkat",
                    "Title": "Judul Resep",
                    "Category": "Kategori",
                    "BM25_Score": "Skor BM25",
                    "Matched_Ingredients": "Bahan Cocok",
                    "Matched_Count": "|M|",
                    "Total_Recipe_Ingredients": "|D|",
                    "Relevance_Status": "Status Relevansi",
                }
            )
            table_md = format_markdown_table(display_table)
        else:
            table_md = "_Tidak ada dokumen yang cocok._"

        md_content += f"""
#### {eval_res['scenario_name']}
- **Kueri Masukan:** `"{eval_res['raw_query']}"`
- **Token Hasil Preprocessing:** `{eval_res['query_tokens']}` ({eval_res['total_query_terms']} token)
- **Precision@5:** `{eval_res['precision_at_5']:.2%}` ({eval_res['relevant_count_at_5']}/5 dokumen relevan)
- **Precision@10:** `{eval_res['precision_at_10']:.2%}` ({eval_res['relevant_count_at_10']}/10 dokumen relevan)

{table_md}

"""

    # Simpan ke file Markdown
    with open(REPORT_MD_FILE, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n-> File laporan Markdown berhasil diekspor ke: {REPORT_MD_FILE}")

    # Cetak rangkuman langsung ke terminal
    print("\n" + "=" * 80)
    print("RINGKASAN STATISTIK KORPUS RESEP")
    print("=" * 80)
    print(tabulate(corpus_stats_df, headers="keys", tablefmt="fancy_grid", showindex=False))

    print("\n" + "=" * 80)
    print("CUPLIKAN 5 TERM BAHAN POPULER PADA INVERTED INDEX")
    print("=" * 80)
    print(tabulate(index_sample_df, headers="keys", tablefmt="fancy_grid", showindex=False))

    print("\n" + "=" * 80)
    print("TABEL EVALUASI PRECISION@5 & PRECISION@10 (5 SKENARIO)")
    print("=" * 80)
    print(tabulate(summary_eval_df, headers="keys", tablefmt="fancy_grid", showindex=False))

    total_duration = time.time() - start_total_time
    print(f"\n[SELESAI] Seluruh pipeline dan laporan berhasil dibuat dalam {total_duration:.2f} detik.")


if __name__ == "__main__":
    run_full_pipeline_and_generate_artifacts()

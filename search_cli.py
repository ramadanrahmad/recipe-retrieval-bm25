"""
CLI Interaktif Pencarian Resep Masakan Berbasis Okapi BM25.
Memungkinkan pengguna memasukkan daftar bahan masakan acak dan melihat hasil
perangkingan resep teratas beserta skor BM25, kecocokan bahan, dan detail resep.
"""

import os
import sys
import argparse
import pickle
import pandas as pd
from tabulate import tabulate

# Pastikan UTF-8 di Windows
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.config import (
    INDEX_FILE_PKL,
    RECIPES_META_PKL,
    DEFAULT_K1,
    DEFAULT_B,
)
from src.preprocessor import TextPreprocessor
from src.inverted_index import InvertedIndex
from src.bm25 import BM25Okapi


def load_system():
    """Memuat indeks dan metadata resep yang telah di-cache."""
    if not os.path.exists(INDEX_FILE_PKL) or not os.path.exists(RECIPES_META_PKL):
        print("[!] Indeks atau metadata belum ditemukan.")
        print("[*] Menjalankan 'generate_report_artifacts.py' terlebih dahulu untuk membangun indeks...")
        from generate_report_artifacts import run_full_pipeline_and_generate_artifacts
        run_full_pipeline_and_generate_artifacts()

    print("[*] Memuat Inverted Index dan metadata resep...")
    inv_index = InvertedIndex()
    inv_index.load(INDEX_FILE_PKL)

    with open(RECIPES_META_PKL, "rb") as f:
        recipes_df = pickle.load(f)

    preprocessor = TextPreprocessor(use_stem_cache=True)
    bm25 = BM25Okapi(inv_index, k1=DEFAULT_K1, b=DEFAULT_B)

    return inv_index, recipes_df, preprocessor, bm25


def perform_search(query: str, bm25: BM25Okapi, preprocessor: TextPreprocessor, recipes_df: pd.DataFrame, top_k: int = 10):
    """Menjalankan dan menampilkan hasil pencarian."""
    tokens = preprocessor.preprocess_query(query)
    print("\n" + "=" * 80)
    print(f"HASIL PENCARIAN RESEP (Top {top_k})")
    print(f"Kueri Input          : '{query}'")
    print(f"Token Preprocessing  : {tokens}")
    print("=" * 80)

    if not tokens:
        print("[!] Seluruh kata dalam kueri teridentifikasi sebagai stopword. Silakan masukkan bahan spesifik.")
        return

    results = bm25.search(query, preprocessor, recipes_df, top_k=top_k)

    if results.empty:
        print("[-] Tidak ada resep yang memuat bahan-bahan tersebut.")
        return

    display_df = results[[
        "Rank", "DocID", "Title", "Category", "BM25_Score",
        "Matched_Ingredients", "Total_Recipe_Ingredients"
    ]].rename(columns={
        "Rank": "No",
        "Title": "Judul Resep",
        "Category": "Kategori",
        "BM25_Score": "Skor BM25",
        "Matched_Ingredients": "Bahan Cocok",
        "Total_Recipe_Ingredients": "Jml Bahan (|D|)",
    })

    print(tabulate(display_df, headers="keys", tablefmt="fancy_grid", showindex=False))

    # Tampilkan cuplikan bahan asli resep peringkat 1
    top_1 = results.iloc[0]
    print("\n" + "-" * 80)
    print(f"DETAIL RESEP PERINGKAT 1: {top_1['Title']} ({top_1['Category'].upper()}) [Skor: {top_1['BM25_Score']}]")
    print(f"DocID: {top_1['DocID']}")
    print(f"Bahan Asli (Ingredients):")
    print(top_1["Raw_Ingredients"].replace("--", "\n  • "))
    print("-" * 80 + "\n")


def interactive_mode():
    """Mode prompt interaktif di terminal."""
    inv_index, recipes_df, preprocessor, bm25 = load_system()
    print("\n" + "=" * 80)
    print("SISTEM PENCARIAN RESEP MASAKAN INDONESIA (OKAPI BM25)")
    print(f"Korpus: {inv_index.N:,} resep | avgdl: {inv_index.avgdl:.2f} token | Vocab: {len(inv_index.vocab):,} kata")
    print("Ketik bahan masakan Anda (pisahkan dengan koma), atau ketik 'exit' untuk keluar.")
    print("=" * 80)

    while True:
        try:
            query = input("\nMasukkan bahan masakan > ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit", "q"]:
                print("Terima kasih telah menggunakan sistem!")
                break

            perform_search(query, bm25, preprocessor, recipes_df, top_k=10)
        except (KeyboardInterrupt, EOFError):
            print("\nSelesai.")
            break


def main():
    parser = argparse.ArgumentParser(description="Pencarian Resep Masakan Indonesia Menggunakan Okapi BM25")
    parser.add_argument("--query", "-q", type=str, help="Kueri bahan masakan (misal: 'ayam, santan, cabai')")
    parser.add_argument("--top_k", "-k", type=int, default=10, help="Jumlah hasil teratas (default: 10)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Jalankan dalam mode terminal interaktif")

    args = parser.parse_args()

    if args.query:
        _, recipes_df, preprocessor, bm25 = load_system()
        perform_search(args.query, bm25, preprocessor, recipes_df, top_k=args.top_k)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()

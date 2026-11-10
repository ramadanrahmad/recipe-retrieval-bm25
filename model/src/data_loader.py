"""
Modul Akuisisi dan Penggabungan Data Resep Masakan Indonesia.
Bertanggung jawab memuat semua file CSV di folder data, memberikan label kategori,
menangani missing values, dan menghasilkan DocID unik untuk setiap dokumen resep.
"""

import os
import glob
import re
from typing import List, Dict, Any, Optional
import pandas as pd
from src.config import DATA_DIR


def extract_category_from_filename(filepath: str) -> str:
    """
    Mengekstrak nama kategori resep dari nama file CSV.
    Contoh: 'data/dataset-ayam.csv' -> 'ayam'
    """
    basename = os.path.basename(filepath)
    # Mencocokkan pola dataset-<kategori>.csv
    match = re.search(r"dataset-([a-zA-Z0-9_\-]+)\.csv", basename, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    # Fallback: hilangkan ekstensi
    return os.path.splitext(basename)[0].lower()


def load_and_merge_datasets(
    data_dir: str = DATA_DIR,
    doc_id_prefix: str = "DOC_",
    doc_id_digits: int = 5
) -> pd.DataFrame:
    """
    Memuat seluruh file CSV di folder data_dir, menggabungkannya ke dalam satu DataFrame,
    menambahkan kolom 'Category', membersihkan baris dengan Title/Ingredients null/kosong,
    dan memberikan DocID unik berurutan.
    
    Returns:
        pd.DataFrame: DataFrame bersih dengan kolom:
        ['DocID', 'Category', 'Title', 'Ingredients', 'Steps', 'Loves', 'URL']
    """
    csv_pattern = os.path.join(data_dir, "dataset-*.csv")
    csv_files = sorted(glob.glob(csv_pattern))
    
    if not csv_files:
        # Coba pola *.csv umum jika dataset-* tidak ditemukan
        csv_files = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
        
    if not csv_files:
        raise FileNotFoundError(f"Tidak ada file CSV yang ditemukan di direktori: {data_dir}")
        
    dfs: List[pd.DataFrame] = []
    
    for filepath in csv_files:
        category = extract_category_from_filename(filepath)
        try:
            df_cat = pd.read_csv(filepath, encoding="utf-8")
        except UnicodeDecodeError:
            df_cat = pd.read_csv(filepath, encoding="latin-1")
            
        df_cat["Category"] = category
        dfs.append(df_cat)
        
    merged_df = pd.concat(dfs, ignore_index=True)
    
    # 1. Hapus nilai null pada kolom Title dan Ingredients
    cleaned_df = merged_df.dropna(subset=["Title", "Ingredients"]).copy()
    
    # 2. Hapus baris yang stringnya hanya whitespace
    cleaned_df["Title"] = cleaned_df["Title"].astype(str).str.strip()
    cleaned_df["Ingredients"] = cleaned_df["Ingredients"].astype(str).str.strip()
    cleaned_df = cleaned_df[
        (cleaned_df["Title"] != "") & (cleaned_df["Ingredients"] != "")
    ].copy()
    
    # Reset index agar berurutan
    cleaned_df.reset_index(drop=True, inplace=True)
    
    # 3. Berikan DocID unik berurutan (misal: DOC_00001, DOC_00002, ...)
    cleaned_df["DocID"] = [
        f"{doc_id_prefix}{str(i + 1).zfill(doc_id_digits)}"
        for i in range(len(cleaned_df))
    ]
    
    # Atur urutan kolom agar rapi dan standar
    standard_columns = ["DocID", "Category", "Title", "Ingredients", "Steps", "Loves", "URL"]
    available_cols = [c for c in standard_columns if c in cleaned_df.columns]
    other_cols = [c for c in cleaned_df.columns if c not in available_cols]
    final_df = cleaned_df[available_cols + other_cols]
    
    return final_df


def get_corpus_category_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menghitung distribusi jumlah resep berdasarkan kategori.
    """
    dist = (
        df.groupby("Category")
        .size()
        .reset_index(name="Jumlah Resep")
        .sort_values(by="Jumlah Resep", ascending=False)
    )
    dist["Persentase (%)"] = (dist["Jumlah Resep"] / len(df) * 100).round(2)
    return dist

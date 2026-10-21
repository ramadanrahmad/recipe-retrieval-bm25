"""
Konfigurasi dan Parameter Sistem Temu Kembali Informasi (IR) Resep Masakan.
Menyimpan path direktori, parameter Okapi BM25, serta daftar stopword kuliner.
"""

import os
from typing import Set

# Path Direktori dan File
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
STORAGE_DIR = os.path.join(BASE_DIR, "index_storage")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

INDEX_FILE_PKL = os.path.join(STORAGE_DIR, "inverted_index.pkl")
INDEX_FILE_JSON = os.path.join(STORAGE_DIR, "inverted_index_sample.json")
RECIPES_META_PKL = os.path.join(STORAGE_DIR, "recipes_metadata.pkl")
STEM_CACHE_PKL = os.path.join(STORAGE_DIR, "stem_cache.pkl")
REPORT_MD_FILE = os.path.join(REPORTS_DIR, "report_paper_artifacts.md")

# Parameter Default Algoritma Okapi BM25
DEFAULT_K1: float = 1.5
DEFAULT_B: float = 0.75

# Stopword Kuliner Lapis 2: Satuan Takaran & Pengukuran
CULINARY_MEASUREMENT_STOPWORDS = [
    "sdm", "sdt", "gram", "gr", "kg", "ml", "liter", "l", "cc", "buah",
    "siung", "batang", "lembar", "butir", "bungkus", "sachet", "potong",
    "ekor", "ikat", "papan", "ons", "kuntum", "ruas", "jari", "sendok",
    "makan", "teh", "gelas", "cangkir", "secukupnya", "sejumput", "sesuai",
    "selera", "bahan", "bumbu", "halus", "pelengkap", "utama", "tambahan",
    # Variasi umum tambahan
    "bks", "bh", "btg", "ltr", "mangkok", "kotak", "kaleng", "tangkai",
    "lonjor", "centong", "wadah", "piring", "mangkok", "toples"
]

# Stopword Kuliner Lapis 2: Kata Kerja / Kondisi / Cara Pengolahan Bahan
CULINARY_PROCESSING_STOPWORDS = [
    "iris", "tipis", "potong", "cincang", "haluskan", "geprek", "memarkan",
    "rebus", "goreng", "bakar", "kukus", "panggang", "tumis", "segar",
    "matang", "mentah", "bersih", "cuci", "kupas", "belah", "dadu",
    "serong", "kecil", "besar", "sedang", "kasar", "lebar", "panjang",
    "parut", "peras", "ambil", "airnya", "buang", "biji", "kulit",
    # Variasi pengolahan umum
    "halus", "larut", "sangrai", "suwir", "rendam", "tumbuk", "ulek",
    "ulekan", "blender", "iriskan", "rajang", "lumuri", "sisir"
]

def get_culinary_stopwords() -> Set[str]:
    """Mengembalikan gabungan set seluruh stopword khusus kuliner."""
    culinary = set(m.lower() for m in CULINARY_MEASUREMENT_STOPWORDS)
    culinary.update(p.lower() for p in CULINARY_PROCESSING_STOPWORDS)
    return culinary

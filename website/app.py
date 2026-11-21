# -*- coding: utf-8 -*-
"""
========================================================================================
APLIKASI WEB SISTEM TEMU KEMBALI INFORMASI (IR) RESEP MASAKAN NUSANTARA
BERBASIS ALGORITMA OKAPI BM25 & INVERTED INDEX
========================================================================================
Framework : Flask
Dataset   : 7 Kategori Resep Masakan Tradisional Indonesia (Kaggle - 13.074 Dokumen)
Mesin IR  : Inverted Index & Okapi BM25 (k1=1.2, b=0.75) from Scratch
========================================================================================
"""

import os
import sys
import re
import math
import time
import pickle
from typing import Dict, List, Set, Any, Tuple, Optional

from flask import Flask, render_template, request, jsonify

# Pengaturan encoding console Windows
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

# ======================================================================================
# DEFINISI KELAS INVERTED INDEX (UNTUK SERIALISASI PICKLE)
# ======================================================================================
class InvertedIndex:
    """Kelas penampung struktur Inverted Index."""
    def __init__(self):
        self.index: Dict[str, Dict[str, int]] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.avgdl: float = 0.0
        self.N: int = 0
        self.vocab: Set[str] = set()


# ======================================================================================
# STOPWORDS KHUSUS KULINER (LAPIS 2)
# ======================================================================================
CULINARY_MEASUREMENT_STOPWORDS = {
    "sdm", "sdt", "gram", "gr", "kg", "ml", "liter", "l", "cc", "buah",
    "siung", "batang", "lembar", "butir", "bungkus", "sachet", "potong",
    "ekor", "ikat", "papan", "ons", "kuntum", "ruas", "jari", "sendok",
    "makan", "teh", "gelas", "cangkir", "secukupnya", "sejumput", "sesuai",
    "selera", "bahan", "bumbu", "halus", "pelengkap", "utama", "tambahan",
    "bks", "bh", "btg", "ltr", "mangkok", "kotak", "kaleng", "tangkai",
    "lonjor", "centong", "wadah", "piring", "toples", "biji"
}

CULINARY_PROCESSING_STOPWORDS = {
    "iris", "tipis", "potong", "cincang", "haluskan", "geprek", "memarkan",
    "rebus", "goreng", "bakar", "kukus", "panggang", "tumis", "segar",
    "matang", "mentah", "bersih", "cuci", "kupas", "belah", "dadu",
    "serong", "kecil", "besar", "sedang", "kasar", "lebar", "panjang",
    "parut", "peras", "ambil", "airnya", "buang", "larut", "sangrai",
    "suwir", "rendam", "tumbuk", "ulek", "ulekan", "blender", "iriskan",
    "rajang", "lumuri", "sisir", "aduk", "rata", "campur"
}

ALL_CULINARY_STOPWORDS = CULINARY_MEASUREMENT_STOPWORDS.union(CULINARY_PROCESSING_STOPWORDS)

# ======================================================================================
# PREPROCESSOR TEKS KOMPOSISI KULINER
# ======================================================================================
class TextPreprocessor:
    def __init__(self, stem_cache: Dict[str, str]):
        from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
        from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

        self.sastrawi_stop = set(StopWordRemoverFactory().get_stop_words())
        self.all_stopwords = self.sastrawi_stop.union(ALL_CULINARY_STOPWORDS)
        self.stemmer = StemmerFactory().create_stemmer()
        self.stem_cache = stem_cache

    def preprocess_query(self, query: str) -> List[str]:
        """Prapemrosesan kueri bahan: pembersihan simbol, stopword, dan stemming."""
        if not query or not isinstance(query, str):
            return []
        
        # 1. Delimiter replacement & case folding
        text = query.replace("--", " ").replace("-", " ").lower()
        # 2. Regex cleaning (alfabet saja)
        text = re.sub(r"[^a-z\s]", " ", text)
        # 3. Tokenisasi
        tokens = [w for w in text.split() if len(w) > 1]
        # 4. Stopword filtering (2 lapis)
        filtered = [w for w in tokens if w not in self.all_stopwords]
        # 5. Stemming dengan cache
        result = []
        for w in filtered:
            if w in self.stem_cache:
                result.append(self.stem_cache[w])
            else:
                stemmed = self.stemmer.stem(w)
                self.stem_cache[w] = stemmed
                result.append(stemmed)
        return result


# ======================================================================================
# MESIN PENCARIAN OKAPI BM25
# ======================================================================================
class BM25SearchEngine:
    def __init__(self, inv_index: InvertedIndex, recipes_df: Any, preprocessor: TextPreprocessor, k1: float = 1.2, b: float = 0.75):
        self.inv_index = inv_index
        self.recipes_df = recipes_df
        self.preprocessor = preprocessor
        self.k1 = k1
        self.b = b
        self.N = inv_index.N
        self.avgdl = inv_index.avgdl
        
        # Buat lookup resep cepat berdasarkan DocID sebagai dictionary murni
        self.recipes_map = {str(row["DocID"]): row.to_dict() for _, row in recipes_df.iterrows()}

    def search(self, query: str, top_k: Any = 10, category_filter: str = "all") -> Tuple[List[Dict[str, Any]], List[str], float]:
        start_time = time.time()
        query_tokens = self.preprocessor.preprocess_query(query)
        unique_q_tokens = list(set(query_tokens))

        if not unique_q_tokens:
            return [], [], 0.0

        scores: Dict[str, float] = {}
        for term in unique_q_tokens:
            if term in self.inv_index.index:
                postings = self.inv_index.index[term]
                df_t = len(postings)
                # Rumus IDF Robertson-Spärck Jones (+1 smoothing)
                idf = math.log(((self.N - df_t + 0.5) / (df_t + 0.5)) + 1.0)

                for doc_id, tf in postings.items():
                    # Filter kategori jika pengguna memilih kategori spesifik
                    if category_filter and category_filter.lower() != "all":
                        recipe = self.recipes_map.get(doc_id)
                        if recipe is None or str(recipe.get("Category", "")).lower() != category_filter.lower():
                            continue

                    dl = self.inv_index.doc_lengths.get(doc_id, self.avgdl)
                    denom = tf + self.k1 * (1.0 - self.b + self.b * (dl / self.avgdl))
                    term_score = idf * ((tf * (self.k1 + 1.0)) / denom)
                    scores[doc_id] = scores.get(doc_id, 0.0) + term_score

        # Urutkan berdasarkan skor BM25 tertinggi
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if top_k is not None and str(top_k).lower() != "all":
            try:
                k_val = int(top_k)
                ranked_docs = sorted_docs[:k_val]
            except ValueError:
                ranked_docs = sorted_docs[:10]
        else:
            ranked_docs = sorted_docs

        results = []
        for rank, (doc_id, score) in enumerate(ranked_docs, 1):
            recipe = self.recipes_map.get(doc_id)
            if recipe is None:
                continue

            # Hitung bahan kueri yang cocok
            matched_terms = [t for t in unique_q_tokens if doc_id in self.inv_index.index.get(t, {})]
            match_ratio = (len(matched_terms) / len(unique_q_tokens)) if unique_q_tokens else 0.0
            match_percentage = round(match_ratio * 100, 1)

            # Penentuan status relevansi (Standar Tugas: >= 70% Relevan, >= 50% Parsial)
            if match_percentage >= 70.0:
                status_label = "Sangat Relevan"
                status_color = "success"
                is_relevant = True
            elif match_percentage >= 50.0:
                status_label = "Cukup Relevan"
                status_color = "warning"
                is_relevant = False
            else:
                status_label = "Kurang Relevan"
                status_color = "secondary"
                is_relevant = False

            # Format bahan dan langkah
            raw_ingredients = str(recipe.get("Ingredients", ""))
            raw_steps = str(recipe.get("Steps", ""))

            results.append({
                "rank": rank,
                "doc_id": doc_id,
                "title": recipe.get("Title", "Resep Tanpa Judul"),
                "category": recipe.get("Category", "umum"),
                "score": round(score, 4),
                "matched_terms": matched_terms,
                "matched_count": len(matched_terms),
                "total_query_terms": len(unique_q_tokens),
                "match_percentage": match_percentage,
                "status_label": status_label,
                "status_color": status_color,
                "is_relevant": is_relevant,
                "ingredients_preview": raw_ingredients[:130] + ("..." if len(raw_ingredients) > 130 else ""),
                "ingredients_list": clean_ingredients_list(raw_ingredients),
                "steps_list": clean_steps_list(raw_steps),
                "loves": int(recipe.get("Loves", 0)) if str(recipe.get("Loves", "")).isdigit() else 0,
                "url": recipe.get("URL", "#")
            })

        duration = round(time.time() - start_time, 4)
        return results, query_tokens, duration


def clean_ingredients_list(raw_text: str) -> List[str]:
    """Mengubah string komposisi bahan dengan pemisah '--' menjadi daftar rapi."""
    if not raw_text or not isinstance(raw_text, str):
        return []
    items = [item.strip() for item in raw_text.split("--") if item.strip()]
    if not items:
        items = [line.strip() for line in raw_text.split("\n") if line.strip()]
    return items


def clean_steps_list(raw_text: str) -> List[str]:
    """Mengubah string langkah memasak dengan pemisah '--' menjadi urutan langkah rapi."""
    if not raw_text or not isinstance(raw_text, str):
        return []
    steps = [s.strip() for s in raw_text.split("--") if s.strip()]
    if not steps:
        steps = [line.strip() for line in raw_text.split("\n") if line.strip()]
    return steps


# ======================================================================================
# INISIALISASI APLIKASI FLASK & PEMUATAN MODEL
# ======================================================================================
app = Flask(__name__)

# Konfigurasi Path ke Folder Model
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
MODEL_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "model"))
STORAGE_DIR = os.path.join(MODEL_DIR, "index_storage")

INDEX_PKL_PATH = os.path.join(STORAGE_DIR, "inverted_index.pkl")
META_PKL_PATH = os.path.join(STORAGE_DIR, "recipes_metadata.pkl")
CACHE_PKL_PATH = os.path.join(STORAGE_DIR, "stem_cache.pkl")

print("[*] Memulai inisialisasi server Flask...")
print(f"[*] Lokasi Penyimpanan Indeks: {STORAGE_DIR}")

# Muat model Inverted Index, metadata, dan cache stemming
try:
    # Daftarkan kelas InvertedIndex ke __main__ agar kompatibel saat di-unpickle
    if '__main__' in sys.modules and not hasattr(sys.modules['__main__'], 'InvertedIndex'):
        setattr(sys.modules['__main__'], 'InvertedIndex', InvertedIndex)

    with open(INDEX_PKL_PATH, "rb") as f:
        inv_index_obj = pickle.load(f)

    with open(META_PKL_PATH, "rb") as f:
        recipes_df = pickle.load(f)

    with open(CACHE_PKL_PATH, "rb") as f:
        stem_cache = pickle.load(f)

    preprocessor = TextPreprocessor(stem_cache)
    search_engine = BM25SearchEngine(
        inv_index=inv_index_obj,
        recipes_df=recipes_df,
        preprocessor=preprocessor,
        k1=1.2,
        b=0.75
    )
    print(f"[+] Model Okapi BM25 berhasil dimuat ({inv_index_obj.N:,} resep, {len(inv_index_obj.vocab):,} kosakata unik).")
except Exception as e:
    print(f"[!] Gagal memuat model: {e}")
    sys.exit(1)


# ======================================================================================
# ROUTE ENDPOINTS APLIKASI FLASK
# ======================================================================================
CATEGORIES_INFO = [
    {"id": "all", "name": "Semua Resep", "icon": "bi-grid-fill", "badge": "bg-dark"},
    {"id": "ayam", "name": "Ayam", "icon": "bi-egg-fried", "badge": "bg-warning text-dark"},
    {"id": "ikan", "name": "Ikan", "icon": "bi-water", "badge": "bg-info text-dark"},
    {"id": "sapi", "name": "Daging Sapi", "icon": "bi-fire", "badge": "bg-danger"},
    {"id": "kambing", "name": "Kambing", "icon": "bi-shield-shaded", "badge": "bg-purple"},
    {"id": "telur", "name": "Telur", "icon": "bi-egg", "badge": "bg-orange"},
    {"id": "tahu", "name": "Tahu", "icon": "bi-square-fill", "badge": "bg-success"},
    {"id": "tempe", "name": "Tempe", "icon": "bi-layers-fill", "badge": "bg-teal"},
]

SAMPLE_QUERIES = [
    {"label": "🍗 Ayam Santan Serai", "query": "ayam santan serai cabai bawang merah"},
    {"label": "🥚 Telur Balado Pedas", "query": "telur tomat cabai merah bawang merah gula"},
    {"label": "🥩 Sapi Lada Hitam", "query": "daging sapi lada hitam kecap bawang bombay"},
    {"label": "🐟 Gurame Asam Manis", "query": "ikan gurame nanas tomat saus bawang bombay"},
    {"label": "🥢 Tahu Tempe Kecap", "query": "tempe tahu kecap manis bawang putih cabai rawit"},
]

@app.route("/", methods=["GET"])
def index():
    """Halaman utama sistem pencarian resep."""
    query = request.args.get("query", "").strip()
    category = request.args.get("category", "all").strip().lower()
    top_k_param = request.args.get("top_k", "10").strip().lower()

    if top_k_param == "all":
        top_k = "all"
    else:
        try:
            top_k = str(int(top_k_param))
        except ValueError:
            top_k = "10"

    results = []
    tokens = []
    duration = 0.0
    has_searched = False

    if query:
        has_searched = True
        results, tokens, duration = search_engine.search(
            query=query,
            top_k=top_k,
            category_filter=category
        )

    return render_template(
        "index.html",
        query=query,
        category=category,
        top_k=top_k,
        results=results,
        tokens=tokens,
        duration=duration,
        has_searched=has_searched,
        categories=CATEGORIES_INFO,
        sample_queries=SAMPLE_QUERIES,
        total_recipes=search_engine.N,
        vocab_size=len(search_engine.inv_index.vocab)
    )


@app.route("/api/recipe/<doc_id>", methods=["GET"])
def api_recipe_detail(doc_id: str):
    """API endpoint untuk mengambil detail resep lengkap (bahan & langkah) untuk modal popup."""
    recipe = search_engine.recipes_map.get(doc_id)
    if recipe is None:
        return jsonify({"status": "error", "message": "Resep tidak ditemukan"}), 404

    return jsonify({
        "status": "success",
        "doc_id": doc_id,
        "title": recipe.get("Title", ""),
        "category": recipe.get("Category", ""),
        "loves": int(recipe.get("Loves", 0)) if str(recipe.get("Loves", "")).isdigit() else 0,
        "url": recipe.get("URL", "#"),
        "ingredients": clean_ingredients_list(str(recipe.get("Ingredients", ""))),
        "steps": clean_steps_list(str(recipe.get("Steps", "")))
    })


if __name__ == "__main__":
    # Menjalankan server web di localhost port 5000
    print("\n==================================================================")
    print("🚀 Server Web Temu Kembali Resep Berhasil Dijalankan!")
    print("🌐 Buka browser Anda di URL: http://127.0.0.1:5000")
    print("==================================================================\n")
    app.run(host="127.0.0.1", port=5000, debug=True)

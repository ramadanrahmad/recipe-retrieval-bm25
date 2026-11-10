# -*- coding: utf-8 -*-
"""
========================================================================================
SISTEM TEMU KEMBALI INFORMASI (INFORMATION RETRIEVAL - OKAPI BM25)
Resep Masakan Tradisional Indonesia Berdasarkan Komposisi Bahan
========================================================================================
File Model Tunggal (Single-File Model):
1. Load Dataset & Exploratory Data Analysis (EDA)
2. Text Preprocessing Pipeline Khusus Komposisi Kuliner (2 Lapis Stopwords & Stemming)
3. Pembangunan Inverted Index & Model Okapi BM25 (from scratch)
4. Visualisasi Metrik & Evaluasi Model Komprehensif (Precision@5, Precision@10, MAP, MRR)
5. Inferensi & Pengujian Prediksi Resep Baru Interaktif
========================================================================================
"""

import os
import sys

import tempfile
os.environ["MPLCONFIGDIR"] = os.path.join(tempfile.gettempdir(), "matplotlib_cache")

import re
import math
import time
import glob
import pickle
from typing import Dict, List, Set, Any, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tabulate import tabulate
from tqdm import tqdm

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

# Pengaturan encoding console Windows
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

# ======================================================================================
# KONFIGURASI PARAMETER & PATH DIREKTORI
# ======================================================================================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STORAGE_DIR = os.path.join(BASE_DIR, "index_storage")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

DEFAULT_K1: float = 1.5      # Parameter saturasi frekuensi term (BM25)
DEFAULT_B: float = 0.75     # Parameter penalti panjang dokumen (BM25)
RELEVANCE_THRESHOLD: float = 0.60  # Resep relevan jika >= 60% token kueri cocok

# Daftar Stopwords Khusus Komposisi Kuliner (Lapis 2)
CULINARY_MEASUREMENT_STOPWORDS = [
    "sdm", "sdt", "gram", "gr", "kg", "ml", "liter", "l", "cc", "buah",
    "siung", "batang", "lembar", "butir", "bungkus", "sachet", "potong",
    "ekor", "ikat", "papan", "ons", "kuntum", "ruas", "jari", "sendok",
    "makan", "teh", "gelas", "cangkir", "secukupnya", "sejumput", "sesuai",
    "selera", "bahan", "bumbu", "halus", "pelengkap", "utama", "tambahan",
    "bks", "bh", "btg", "ltr", "mangkok", "kotak", "kaleng", "tangkai",
    "lonjor", "centong", "wadah", "piring", "toples"
]

CULINARY_PROCESSING_STOPWORDS = [
    "iris", "tipis", "potong", "cincang", "haluskan", "geprek", "memarkan",
    "rebus", "goreng", "bakar", "kukus", "panggang", "tumis", "segar",
    "matang", "mentah", "bersih", "cuci", "kupas", "belah", "dadu",
    "serong", "kecil", "besar", "sedang", "kasar", "lebar", "panjang",
    "parut", "peras", "ambil", "airnya", "buang", "biji", "kulit",
    "larut", "sangrai", "suwir", "rendam", "tumbuk", "ulek", "ulekan",
    "blender", "iriskan", "rajang", "lumuri", "sisir"
]

def get_culinary_stopwords() -> Set[str]:
    culinary = set(m.lower() for m in CULINARY_MEASUREMENT_STOPWORDS)
    culinary.update(p.lower() for p in CULINARY_PROCESSING_STOPWORDS)
    return culinary


# ======================================================================================
# BAGIAN 1: LOAD DATASET & EXPLORATORY DATA ANALYSIS (EDA)
# ======================================================================================
def load_and_merge_datasets(data_dir: str = DATA_DIR) -> pd.DataFrame:
    print("\n" + "=" * 80)
    print("BAGIAN 1: DATA LOADING & EXPLORATORY DATA ANALYSIS")
    print("=" * 80)
    
    csv_pattern = os.path.join(data_dir, "dataset-*.csv")
    csv_files = sorted(glob.glob(csv_pattern))
    if not csv_files:
        raise FileNotFoundError(f"Tidak ditemukan file CSV di: {data_dir}")
        
    print(f"[*] Ditemukan {len(csv_files)} file dataset CSV:")
    all_dfs = []
    for fpath in csv_files:
        fname = os.path.basename(fpath)
        cat = fname.replace("dataset-", "").replace(".csv", "")
        df_temp = pd.read_csv(fpath)
        df_temp["Category"] = cat
        all_dfs.append(df_temp)
        print(f"  - {fname:25s} | Kategori: {cat:8s} | Jumlah baris: {len(df_temp):,}")
        
    merged_df = pd.concat(all_dfs, ignore_index=True)
    initial_count = len(merged_df)
    
    # Penanganan data kosong dan duplikat
    merged_df.dropna(subset=["Title", "Ingredients"], inplace=True)
    merged_df.drop_duplicates(subset=["Title", "Ingredients"], inplace=True)
    merged_df.reset_index(drop=True, inplace=True)
    
    # Pembuatan DocID unik
    merged_df["DocID"] = [f"DOC_{i+1:05d}" for i in range(len(merged_df))]
    
    # Susun ulang kolom
    cols = ["DocID", "Category", "Title", "Ingredients", "Steps", "Loves", "URL"]
    merged_df = merged_df[[c for c in cols if c in merged_df.columns]]
    
    print(f"\n[+] Total resep awal       : {initial_count:,}")
    print(f"[+] Total resep bersih (N) : {len(merged_df):,} resep.")
    return merged_df


# ======================================================================================
# BAGIAN 2: TEXT PREPROCESSING PIPELINE KHUSUS KULINER
# ======================================================================================
class TextPreprocessor:
    def __init__(self, use_cache: bool = True):
        # Stopwords Lapis 1 (Sastrawi) & Lapis 2 (Kuliner)
        sastrawi_sw = StopWordRemoverFactory()
        self.sw_lapis1 = set(sastrawi_sw.get_stop_words())
        self.sw_lapis2 = get_culinary_stopwords()
        self.all_stopwords = self.sw_lapis1.union(self.sw_lapis2)
        
        # Stemmer Sastrawi & Cache
        factory = StemmerFactory()
        self.stemmer = factory.create_stemmer()
        self.stem_cache: Dict[str, str] = {}
        self.cache_path = os.path.join(STORAGE_DIR, "stem_cache.pkl")
        
        if use_cache and os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "rb") as f:
                    self.stem_cache = pickle.load(f)
            except Exception:
                self.stem_cache = {}

    def replace_delimiters(self, text: str) -> str:
        return text.replace("--", " ") if isinstance(text, str) else ""

    def case_folding(self, text: str) -> str:
        return text.lower()

    def regex_cleaning(self, text: str) -> str:
        text = re.sub(r"[½¼¾⅓⅔⅛⅜⅝⅞]", " ", text)
        text = re.sub(r"[^a-z\s]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def tokenize(self, text: str) -> List[str]:
        return text.split() if text else []

    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        return [t for t in tokens if t not in self.all_stopwords and len(t) > 1]

    def stem_token(self, token: str) -> str:
        if token in self.stem_cache:
            return self.stem_cache[token]
        res = self.stemmer.stem(token)
        self.stem_cache[token] = res
        return res

    def save_cache(self):
        with open(self.cache_path, "wb") as f:
            pickle.dump(self.stem_cache, f, protocol=pickle.HIGHEST_PROTOCOL)

    def preprocess_document(self, text: str) -> List[str]:
        step1 = self.replace_delimiters(text)
        step2 = self.case_folding(step1)
        step3 = self.regex_cleaning(step2)
        tokens = self.tokenize(step3)
        tokens_no_sw = self.remove_stopwords(tokens)
        return [self.stem_token(t) for t in tokens_no_sw]

    def trace_sample(self, text: str) -> List[Dict[str, str]]:
        s1 = self.replace_delimiters(text)
        s2 = self.case_folding(s1)
        s3 = self.regex_cleaning(s2)
        s4 = self.tokenize(s3)
        s5 = self.remove_stopwords(s4)
        s6 = [self.stem_token(t) for t in s5]
        return [
            {"Tahapan": "1. Data Mentah (Raw Input)", "Hasil": text[:90] + "..."},
            {"Tahapan": "2. Delimiter Replacement", "Hasil": s1[:90] + "..."},
            {"Tahapan": "3. Case Folding (Lowercase)", "Hasil": s2[:90] + "..."},
            {"Tahapan": "4. Regex Cleaning (Alphabet Only)", "Hasil": s3[:90] + "..."},
            {"Tahapan": "5. Tokenization", "Hasil": str(s4[:10]) + "..."},
            {"Tahapan": "6. Stopword Removal (2 Lapis)", "Hasil": str(s5[:8]) + "..."},
            {"Tahapan": "7. Stemming (PySastrawi Cache)", "Hasil": str(s6[:8]) + "..."}
        ]


# ======================================================================================
# BAGIAN 3: FEATURE EXTRACTION & BUILD MODEL (INVERTED INDEX & OKAPI BM25)
# ======================================================================================
class InvertedIndex:
    def __init__(self):
        self.index: Dict[str, Dict[str, int]] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.N: int = 0
        self.avgdl: float = 0.0
        self.vocab: Set[str] = set()

    def build(self, docs_tokens_dict: Dict[str, List[str]]):
        self.N = len(docs_tokens_dict)
        total_tokens = 0
        for doc_id, tokens in docs_tokens_dict.items():
            dlen = len(tokens)
            self.doc_lengths[doc_id] = dlen
            total_tokens += dlen
            
            tf_map = {}
            for t in tokens:
                tf_map[t] = tf_map.get(t, 0) + 1
                
            for t, tf in tf_map.items():
                if t not in self.index:
                    self.index[t] = {}
                self.index[t][doc_id] = tf
                self.vocab.add(t)
                
        self.avgdl = (total_tokens / self.N) if self.N > 0 else 0.0

    def get_document_frequency(self, term: str) -> int:
        return len(self.index.get(term, {}))


class BM25Okapi:
    def __init__(self, index: InvertedIndex, k1: float = DEFAULT_K1, b: float = DEFAULT_B):
        self.index = index
        self.k1 = k1
        self.b = b
        self.idf_cache: Dict[str, float] = {}

    def compute_idf(self, term: str) -> float:
        if term in self.idf_cache:
            return self.idf_cache[term]
        n_qi = self.index.get_document_frequency(term)
        N = self.index.N
        if N == 0:
            return 0.0
        # Rumus IDF Robertson-Spärck Jones BM25 dengan smoothing +1
        idf = math.log(((N - n_qi + 0.5) / (n_qi + 0.5)) + 1.0)
        self.idf_cache[term] = idf
        return idf

    def score_term(self, term: str, tf: int, doc_len: int) -> float:
        idf = self.compute_idf(term)
        num = tf * (self.k1 + 1.0)
        den = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.index.avgdl))
        return idf * (num / den)

    def search(
        self,
        query: str,
        preprocessor: TextPreprocessor,
        df_recipes: pd.DataFrame,
        top_k: int = 10,
        category: Optional[str] = None
    ) -> pd.DataFrame:
        query_tokens = preprocessor.preprocess_document(query)
        q_tokens_unique = list(set(query_tokens))
        if not q_tokens_unique:
            return pd.DataFrame()
            
        candidates = set()
        for t in q_tokens_unique:
            if t in self.index.index:
                candidates.update(self.index.index[t].keys())
                
        scores = {}
        matched_map = {}
        for doc_id in candidates:
            dlen = self.index.doc_lengths[doc_id]
            s = 0.0
            matched = []
            for t in q_tokens_unique:
                if t in self.index.index and doc_id in self.index.index[t]:
                    tf = self.index.index[t][doc_id]
                    s += self.score_term(t, tf, dlen)
                    matched.append(t)
            scores[doc_id] = s
            matched_map[doc_id] = matched
            
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for doc_id, score in ranked:
            row = df_recipes.loc[df_recipes["DocID"] == doc_id].iloc[0]
            if category and category.lower() != "all" and row["Category"].lower() != category.lower():
                continue
            match_ratio = len(matched_map[doc_id]) / len(q_tokens_unique)
            is_relevant = match_ratio >= RELEVANCE_THRESHOLD
            results.append({
                "DocID": doc_id,
                "Category": row["Category"],
                "Title": row["Title"],
                "BM25_Score": round(score, 4),
                "Matched_Count": len(matched_map[doc_id]),
                "Match_Ratio": round(match_ratio * 100, 1),
                "Is_Relevant": is_relevant,
                "Status": "Relevan" if is_relevant else "Tidak Relevan",
                "Matched_Terms": ", ".join(matched_map[doc_id]),
                "Ingredients": row["Ingredients"],
                "Steps": row["Steps"]
            })
            if len(results) >= top_k:
                break
                
        res_df = pd.DataFrame(results)
        if not res_df.empty:
            res_df.insert(0, "Rank", range(1, len(res_df) + 1))
        return res_df


# ======================================================================================
# BAGIAN 4: EVALUASI MODEL KOMPREHENSIF & VISUALISASI METRIK
# ======================================================================================
SCENARIOS = [
    {
        "id": "SKN_1",
        "name": "Olahan Ayam Santan Bumbu Rempah",
        "query": "ayam santan serai cabai bawang merah"
    },
    {
        "id": "SKN_2",
        "name": "Olahan Telur Balado Tradisional",
        "query": "telur tomat cabai merah bawang merah gula"
    },
    {
        "id": "SKN_3",
        "name": "Olahan Tahu Tempe Kecap Gurih",
        "query": "tempe tahu kecap manis bawang putih cabai rawit"
    },
    {
        "id": "SKN_4",
        "name": "Olahan Sup Daging Sapi Rempah",
        "query": "daging sapi wortel pala seledri merica"
    },
    {
        "id": "SKN_5",
        "name": "Olahan Ikan Asam Manis Segar",
        "query": "ikan gurame nanas tomat saus bawang bombay"
    }
]

def evaluate_scenarios(bm25_model: BM25Okapi, preprocessor: TextPreprocessor, df_recipes: pd.DataFrame):
    print("\n" + "=" * 80)
    print("BAGIAN 4: EVALUASI MODEL IR OKAPI BM25 (METRIK & SKENARIO)")
    print("=" * 80)
    
    summary_records = []
    scenario_results = {}
    
    for scn in SCENARIOS:
        q_tokens = list(set(preprocessor.preprocess_document(scn["query"])))
        res_df = bm25_model.search(scn["query"], preprocessor, df_recipes, top_k=10)
        
        top5 = res_df.head(5)
        top10 = res_df.head(10)
        
        p5 = top5["Is_Relevant"].sum() / 5.0 if len(top5) > 0 else 0.0
        p10 = top10["Is_Relevant"].sum() / 10.0 if len(top10) > 0 else 0.0
        
        # Perhitungan Average Precision (AP)
        running_rel = 0
        ap_sum = 0.0
        first_rel_rank = None
        for idx, row in top10.iterrows():
            if row["Is_Relevant"]:
                running_rel += 1
                ap_sum += (running_rel / row["Rank"])
                if first_rel_rank is None:
                    first_rel_rank = row["Rank"]
        ap = (ap_sum / running_rel) if running_rel > 0 else 0.0
        rr = (1.0 / first_rel_rank) if first_rel_rank else 0.0
        
        summary_records.append({
            "ID": scn["id"],
            "Skenario": scn["name"],
            "Kueri": scn["query"],
            "P@5": round(p5, 4),
            "P@10": round(p10, 4),
            "AP": round(ap, 4),
            "RR": round(rr, 4)
        })
        scenario_results[scn["id"]] = res_df
        
    summary_df = pd.DataFrame(summary_records)
    macro_p5 = summary_df["P@5"].mean()
    macro_p10 = summary_df["P@10"].mean()
    map_score = summary_df["AP"].mean()
    mrr_score = summary_df["RR"].mean()
    
    print("\n[+] TABEL RINGKASAN EVALUASI PER SKENARIO KUERI:")
    print(tabulate(summary_df, headers="keys", tablefmt="fancy_grid", showindex=False))
    print(f"\n[*] Macro-Average Precision@5  : {macro_p5:.2%}")
    print(f"[*] Macro-Average Precision@10 : {macro_p10:.2%}")
    print(f"[*] Mean Average Precision (MAP): {map_score:.4f}")
    print(f"[*] Mean Reciprocal Rank (MRR) : {mrr_score:.4f}")
    
    return summary_df, scenario_results, macro_p5, macro_p10, map_score, mrr_score


def generate_visualizations(df_recipes: pd.DataFrame, summary_df: pd.DataFrame, scenario_results: dict):
    print("\n[*] Membuat grafik visualisasi metrik dan analisis performa...")
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    # 1. Visualisasi Distribusi Kategori Resep Korpus
    plt.figure(figsize=(10, 4.5))
    cat_counts = df_recipes["Category"].value_counts()
    bars = plt.bar(cat_counts.index, cat_counts.values, color="#2b5c8f", edgecolor="black", alpha=0.85)
    plt.title("Distribusi Resep Masakan Berdasarkan Kategori Bahan Utama", fontsize=12, fontweight="bold")
    plt.xlabel("Kategori Bahan", fontsize=11)
    plt.ylabel("Jumlah Dokumen Resep", fontsize=11)
    for b in bars:
        h = b.get_height()
        plt.text(b.get_x() + b.get_width()/2., h + 20, f"{h:,}", ha="center", va="bottom", fontsize=9, fontweight="bold")
    plt.tight_layout()
    chart1_path = os.path.join(REPORTS_DIR, "visualisasi_distribusi_kategori.png")
    plt.savefig(chart1_path, dpi=200)
    plt.close()
    
    # 2. Visualisasi Precision@5 dan Precision@10 per Skenario
    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(summary_df))
    width = 0.35
    b1 = ax.bar(x - width/2, summary_df["P@5"] * 100, width, label="Precision@5", color="#1f77b4", edgecolor="black")
    b2 = ax.bar(x + width/2, summary_df["P@10"] * 100, width, label="Precision@10", color="#ff7f0e", edgecolor="black")
    ax.set_ylabel("Nilai Presisi (%)", fontsize=11)
    ax.set_title("Evaluasi Metrik Precision@5 dan Precision@10 Tiap Skenario Kueri", fontsize=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(summary_df["ID"], fontsize=10)
    ax.set_ylim(0, 115)
    ax.axhline(summary_df["P@5"].mean()*100, color="#1f77b4", linestyle="--", alpha=0.7, label=f"Macro P@5 ({summary_df['P@5'].mean():.1%})")
    ax.axhline(summary_df["P@10"].mean()*100, color="#ff7f0e", linestyle=":", alpha=0.7, label=f"Macro P@10 ({summary_df['P@10'].mean():.1%})")
    ax.legend(loc="lower right")
    plt.tight_layout()
    chart2_path = os.path.join(REPORTS_DIR, "visualisasi_precision_skenario.png")
    plt.savefig(chart2_path, dpi=200)
    plt.close()

    # 3. Visualisasi Kurva Penurunan Skor BM25 per Ranking (Rank 1-10)
    plt.figure(figsize=(10, 5))
    for scn_id, res in scenario_results.items():
        plt.plot(res["Rank"], res["BM25_Score"], marker="o", label=scn_id)
    plt.title("Distribusi dan Peluruhan Skor Okapi BM25 Berdasarkan Peringkat (Top-10)", fontsize=12, fontweight="bold")
    plt.xlabel("Peringkat Temu Kembali (Rank)", fontsize=11)
    plt.ylabel("Skor Okapi BM25", fontsize=11)
    plt.xticks(range(1, 11))
    plt.legend()
    plt.tight_layout()
    chart3_path = os.path.join(REPORTS_DIR, "visualisasi_peluruhan_skor_bm25.png")
    plt.savefig(chart3_path, dpi=200)
    plt.close()

    # 4. Matriks Relevansi Dokumen (Confusion Table Top-10)
    plt.figure(figsize=(10, 4))
    mat = np.zeros((len(SCENARIOS), 10))
    for i, scn in enumerate(SCENARIOS):
        res = scenario_results[scn["id"]]
        for j, is_rel in enumerate(res["Is_Relevant"].head(10)):
            mat[i, j] = 1 if is_rel else 0
    plt.imshow(mat, cmap="YlGn", aspect="auto")
    plt.title("Matriks Relevansi Dokumen Hasil Temu Kembali (1 = Relevan, 0 = Tidak Relevan)", fontsize=12, fontweight="bold")
    plt.xticks(range(10), [f"R{r+1}" for r in range(10)])
    plt.yticks(range(len(SCENARIOS)), [s["id"] for s in SCENARIOS])
    plt.colorbar(label="Status Relevansi")
    for i in range(len(SCENARIOS)):
        for j in range(10):
            val = int(mat[i, j])
            plt.text(j, i, str(val), ha="center", va="center", color="black" if val==0 else "white", fontweight="bold")
    plt.tight_layout()
    chart4_path = os.path.join(REPORTS_DIR, "visualisasi_matriks_relevansi.png")
    plt.savefig(chart4_path, dpi=200)
    plt.close()

    print(f"[+] 4 Berkas grafik visualisasi berhasil disimpan ke: {REPORTS_DIR}")


# ======================================================================================
# BAGIAN 5: INFERENSI & PENGUJIAN PREDIKSI DATA BARU INTERAKTIF
# ======================================================================================
def predict_recipe(
    query: str,
    bm25_model: BM25Okapi,
    preprocessor: TextPreprocessor,
    df_recipes: pd.DataFrame,
    top_k: int = 5,
    category: Optional[str] = None
):
    print("\n" + "-" * 75)
    print(f"PENGUJIAN PREDIKSI TEMU KEMBALI RESEP")
    print(f"Kueri Bahan Input : \"{query}\"")
    if category and category.lower() != "all":
        print(f"Filter Kategori  : {category}")
    print("-" * 75)
    
    t0 = time.time()
    res = bm25_model.search(query, preprocessor, df_recipes, top_k=top_k, category=category)
    duration = time.time() - t0
    
    if res.empty:
        print("[!] Tidak ditemukan resep yang cocok dengan bahan tersebut.")
        return
        
    print(f"[*] Ditemukan {len(res)} rekomendasi resep teratas dalam {duration:.4f} detik:\n")
    for _, row in res.iterrows():
        icon = "✅" if row["Is_Relevant"] else "⚠️"
        print(f"Peringkat {row['Rank']}: {row['Title']} ({row['Category'].upper()}) - Skor BM25: {row['BM25_Score']}")
        print(f"   Status Relevansi : {icon} {row['Status']} (Kecocokan Bahan: {row['Match_Ratio']}%)")
        print(f"   Bahan yang Cocok : {row['Matched_Terms']}")
        print(f"   Bahan Lengkap    : {row['Ingredients'][:120]}...")
        print(f"   Langkah Ringkas  : {row['Steps'][:140]}...")
        print()


# ======================================================================================
# EKSEKUSI PIPELINE END-TO-END
# ======================================================================================
if __name__ == "__main__":
    t_start = time.time()
    print("=" * 80)
    print("MEMULAI EKSEKUSI MODEL OKAPI BM25 RESEP MASAKAN (SINGLE FILE SCRIPT)")
    print("=" * 80)
    
    # 1. Load Data
    df = load_and_merge_datasets(DATA_DIR)
    
    # 2. Preprocessing
    print("\n" + "=" * 80)
    print("BAGIAN 2: TEXT PREPROCESSING PADA INGREDIENTS")
    print("=" * 80)
    prep = TextPreprocessor(use_cache=True)
    
    # Tampilkan sampel jejak preprocessing
    sample_raw = df.iloc[0]["Ingredients"]
    trace = prep.trace_sample(sample_raw)
    print("\n[*] Tabel Jejak Preprocessing Berurutan (Sampel Resep 1):")
    print(tabulate(trace, headers="keys", tablefmt="fancy_grid"))
    
    # Preprocessing seluruh korpus
    print("\n[*] Memproses seluruh 15.593 dokumen resep...")
    t0_prep = time.time()
    raw_vocab = set()
    cleaned_docs = {}
    for doc_id, text in zip(df["DocID"], df["Ingredients"]):
        raw_vocab.update(text.lower().split())
        cleaned_docs[doc_id] = prep.preprocess_document(text)
    prep_time = time.time() - t0_prep
    prep.save_cache()
    
    clean_vocab = set(t for tokens in cleaned_docs.values() for t in tokens)
    print(f"[+] Preprocessing selesai dalam {prep_time:.2f} detik.")
    print(f"[+] Ukuran Vocabulary Sebelum Preprocessing : {len(raw_vocab):,} token unik")
    print(f"[+] Ukuran Vocabulary Setelah Preprocessing : {len(clean_vocab):,} token unik")
    print(f"[+] Persentase Reduksi Dimensi             : {((len(raw_vocab)-len(clean_vocab))/len(raw_vocab)):.2%}")
    
    # 3. Build Model Inverted Index & BM25
    print("\n" + "=" * 80)
    print("BAGIAN 3: MEMBANGUN INVERTED INDEX & MODEL OKAPI BM25")
    print("=" * 80)
    inv_index = InvertedIndex()
    inv_index.build(cleaned_docs)
    print(f"[+] Inverted Index Berhasil Dibangun:")
    print(f"    - Total Dokumen Terindeks (N) : {inv_index.N:,}")
    print(f"    - Total Term Kosakata        : {len(inv_index.vocab):,}")
    print(f"    - Rata-rata Panjang Dok (avgdl): {inv_index.avgdl:.4f} token/resep")
    
    bm25 = BM25Okapi(inv_index, k1=DEFAULT_K1, b=DEFAULT_B)
    print(f"[+] Model Okapi BM25 Siap Digunakan (k1={DEFAULT_K1}, b={DEFAULT_B})")
    
    # 4. Evaluasi Model & Visualisasi
    summary_df, scn_results, p5, p10, map_sc, mrr_sc = evaluate_scenarios(bm25, prep, df)
    generate_visualizations(df, summary_df, scn_results)
    
    # 5. Uji Prediksi Data Baru
    print("\n" + "=" * 80)
    print("BAGIAN 5: PENGUJIAN PREDIKSI RESEP BARU")
    print("=" * 80)
    predict_recipe("daging sapi lada hitam bawang bombay kecap", bm25, prep, df, top_k=3)
    predict_recipe("ikan gurame asam manis nanas cabai", bm25, prep, df, top_k=3)
    predict_recipe("ayam suwir kemangi cabai rawit serai", bm25, prep, df, top_k=3)
    
    # 6. Simpan Model Artefak
    print("\n" + "=" * 80)
    print("BAGIAN 6: PENYIMPANAN ARTEFAK MODEL SERIALISASI")
    print("=" * 80)
    with open(os.path.join(STORAGE_DIR, "inverted_index.pkl"), "wb") as f:
        pickle.dump(inv_index, f, protocol=pickle.HIGHEST_PROTOCOL)
    with open(os.path.join(STORAGE_DIR, "recipes_metadata.pkl"), "wb") as f:
        pickle.dump(df, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"[+] Model Inverted Index dan Metadata berhasil disimpan ke direktori: {STORAGE_DIR}")
    print(f"[*] Seluruh eksekusi selesai dalam {time.time()-t_start:.2f} detik.")

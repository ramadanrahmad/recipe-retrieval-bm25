"""
Modul Algoritma Temu Kembali Informasi Okapi BM25 (from Scratch).
Mengimplementasikan perhitungan eksplisit skor Okapi BM25 sesuai rumus:
  - IDF(q_i) = ln(((N - n(q_i) + 0.5) / (n(q_i) + 0.5)) + 1)
  - Score(D, Q) = sum( IDF(q_i) * ((f(q_i, D) * (k1 + 1)) / (f(q_i, D) + k1 * (1 - b + b * (|D| / avgdl)))) )
Mendukung perangkingan Top-K dengan pengembalian metadata lengkap dokumen.
"""

import math
from typing import Dict, List, Set, Any, Optional
import pandas as pd

from src.inverted_index import InvertedIndex
from src.preprocessor import TextPreprocessor
from src.config import DEFAULT_K1, DEFAULT_B


class BM25Okapi:
    """
    Mesin Penilaian dan Temu Kembali Informasi menggunakan Algoritma Okapi BM25.
    
    Attributes:
        index: Objek InvertedIndex yang telah terisi data korpus.
        k1: Parameter saturasi frekuensi term (default: 1.5).
        b: Parameter penalti panjang dokumen (default: 0.75).
        idf_cache: Cache nilai IDF untuk efisiensi komputasi berulang.
    """

    def __init__(
        self,
        index: InvertedIndex,
        k1: float = DEFAULT_K1,
        b: float = DEFAULT_B,
    ):
        self.index = index
        self.k1 = k1
        self.b = b
        self.idf_cache: Dict[str, float] = {}

    def compute_idf(self, term: str) -> float:
        """
        Menghitung nilai Inverse Document Frequency (IDF) dengan Robertson-Spärck Jones formula
        ditambah penghalusan +1 (BM25+ / Lucene smoothing) agar selalu bernilai positif:
        
        IDF(q_i) = ln(((N - n(q_i) + 0.5) / (n(q_i) + 0.5)) + 1)
        """
        if term in self.idf_cache:
            return self.idf_cache[term]

        n_qi = self.index.get_document_frequency(term)
        N = self.index.N

        if N == 0:
            return 0.0

        # Rumus eksplisit sesuai spesifikasi
        numerator = N - n_qi + 0.5
        denominator = n_qi + 0.5
        idf_value = math.log((numerator / denominator) + 1.0)

        self.idf_cache[term] = idf_value
        return idf_value

    def score_term(self, term: str, tf: int, doc_len: int) -> float:
        """
        Menghitung komponen skor BM25 untuk satu term pada satu dokumen spesifik:
        
        Score_term = IDF(q_i) * ( (f(q_i, D) * (k1 + 1)) / (f(q_i, D) + k1 * (1 - b + b * (|D| / avgdl))) )
        """
        if tf <= 0 or self.index.avgdl <= 0:
            return 0.0

        idf = self.compute_idf(term)
        
        # Perhitungan pembilang dan penyebut saturasi term
        tf_numerator = tf * (self.k1 + 1.0)
        length_penalty = 1.0 - self.b + (self.b * (doc_len / self.index.avgdl))
        tf_denominator = tf + (self.k1 * length_penalty)

        return idf * (tf_numerator / tf_denominator)

    def search(
        self,
        query: str,
        preprocessor: TextPreprocessor,
        recipes_df: pd.DataFrame,
        top_k: int = 10,
    ) -> pd.DataFrame:
        """
        Menjalankan pencarian resep berbasis kueri komposisi bahan masakan.
        
        Alur:
          1. Kueri diproses dengan pipeline preprocessing yang sama dengan dokumen.
          2. Mengidentifikasi seluruh kandidat dokumen yang memuat minimal 1 token bahan kueri.
          3. Menghitung skor Okapi BM25 untuk setiap dokumen kandidat.
          4. Mengurutkan hasil pencarian secara descending berdasarkan skor.
          5. Mengembalikan Top-K dokumen dengan detail informasi lengkap.
          
        Args:
            query: String bahan masakan (contoh: "ayam, santan, cabai, bawang merah").
            preprocessor: Objek TextPreprocessor.
            recipes_df: DataFrame metadata seluruh resep yang memiliki kolom DocID, Title, Category, Ingredients, dll.
            top_k: Jumlah resep teratas yang dikembalikan (default: 10).
            
        Returns:
            pd.DataFrame: Hasil pencarian dengan kolom:
            ['Rank', 'DocID', 'Title', 'Category', 'BM25_Score',
             'Matched_Ingredients', 'Total_Recipe_Ingredients', 'Raw_Ingredients']
        """
        # 1. Preprocessing kueri menggunakan pipeline yang identik
        query_tokens = preprocessor.preprocess_query(query)

        if not query_tokens:
            return pd.DataFrame(
                columns=[
                    "Rank",
                    "DocID",
                    "Title",
                    "Category",
                    "BM25_Score",
                    "Matched_Ingredients",
                    "Total_Recipe_Ingredients",
                    "Raw_Ingredients",
                ]
            )

        # Gunakan token unik pada kueri agar perhitungan seimbang
        unique_query_tokens = sorted(list(set(query_tokens)))

        # 2. Akumulasi skor untuk dokumen kandidat
        scores: Dict[str, float] = {}
        matched_terms_per_doc: Dict[str, List[str]] = {}

        for q_term in unique_query_tokens:
            postings = self.index.get_postings(q_term)
            if not postings:
                continue

            for doc_id, tf in postings.items():
                doc_len = self.index.doc_lengths.get(doc_id, 0)
                term_score = self.score_term(q_term, tf, doc_len)

                if doc_id not in scores:
                    scores[doc_id] = 0.0
                    matched_terms_per_doc[doc_id] = []

                scores[doc_id] += term_score
                matched_terms_per_doc[doc_id].append(q_term)

        if not scores:
            return pd.DataFrame(
                columns=[
                    "Rank",
                    "DocID",
                    "Title",
                    "Category",
                    "BM25_Score",
                    "Matched_Ingredients",
                    "Total_Recipe_Ingredients",
                    "Raw_Ingredients",
                ]
            )

        # 3. Urutkan dokumen kandidat berdasarkan skor tertinggi
        sorted_docs = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]

        # 4. Bangun metadata mapping untuk akses cepat
        meta_lookup = recipes_df.set_index("DocID").to_dict(orient="index")

        results = []
        for rank, (doc_id, score) in enumerate(sorted_docs, start=1):
            doc_meta = meta_lookup.get(doc_id, {})
            matched = matched_terms_per_doc.get(doc_id, [])
            doc_len = self.index.doc_lengths.get(doc_id, 0)

            results.append({
                "Rank": rank,
                "DocID": doc_id,
                "Title": doc_meta.get("Title", "Unknown"),
                "Category": doc_meta.get("Category", "Unknown"),
                "BM25_Score": round(score, 4),
                "Matched_Ingredients": ", ".join(matched),
                "Matched_Count": len(matched),
                "Total_Recipe_Ingredients": doc_len,
                "Raw_Ingredients": doc_meta.get("Ingredients", ""),
            })

        return pd.DataFrame(results)

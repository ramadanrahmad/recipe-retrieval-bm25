"""
Modul Pembentukan Inverted Index (Sparse Information Retrieval dari Nol).
Mengimplementasikan struktur data indeks terbalik berbasis kamus Python murni (from scratch)
tanpa library eksternal black-box, menyimpan frekuensi term per dokumen, panjang dokumen,
serta menyediakan fasilitas serialisasi simpan/muat (save/load).
"""

import os
import json
import pickle
from collections import Counter
from typing import Dict, List, Tuple, Set, Any, Optional


class InvertedIndex:
    """
    Struktur Data Inverted Index untuk Temu Kembali Informasi Resep Masakan.
    
    Menyimpan:
      - index: dict yang memetakan term -> {DocID: term_frequency}
      - doc_lengths: dict yang memetakan DocID -> |D| (panjang dokumen bersih)
      - avgdl: rata-rata panjang dokumen di seluruh korpus
      - N: total dokumen di dalam korpus
      - vocab: himpunan seluruh kata unik yang terindeks
    """

    def __init__(self):
        self.index: Dict[str, Dict[str, int]] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.avgdl: float = 0.0
        self.N: int = 0
        self.vocab: Set[str] = set()

    def build(self, docs_dict: Dict[str, List[str]]) -> None:
        """
        Membangun Inverted Index dari koleksi dokumen yang telah melalui preprocessing.
        
        Args:
            docs_dict: Dictionary yang memetakan DocID -> List[token_kata]
        """
        self.index.clear()
        self.doc_lengths.clear()
        self.vocab.clear()

        self.N = len(docs_dict)
        if self.N == 0:
            self.avgdl = 0.0
            return

        total_length = 0

        for doc_id, tokens in docs_dict.items():
            doc_len = len(tokens)
            self.doc_lengths[doc_id] = doc_len
            total_length += doc_len

            # Hitung Term Frequency (TF) untuk dokumen saat ini
            tf_counter = Counter(tokens)

            for term, tf in tf_counter.items():
                if term not in self.index:
                    self.index[term] = {}
                    self.vocab.add(term)
                self.index[term][doc_id] = tf

        # Hitung rata-rata panjang dokumen (avgdl)
        self.avgdl = float(total_length / self.N) if self.N > 0 else 0.0

    def get_postings(self, term: str) -> Dict[str, int]:
        """
        Mengembalikan postings list untuk sebuah term: {DocID: TF}.
        Jika term tidak ada dalam indeks, mengembalikan dictionary kosong.
        """
        return self.index.get(term, {})

    def get_document_frequency(self, term: str) -> int:
        """
        Mengembalikan Document Frequency n(t), yaitu jumlah dokumen
        yang mengandung term tersebut.
        """
        return len(self.index.get(term, {}))

    def get_term_frequency(self, term: str, doc_id: str) -> int:
        """
        Mengembalikan frekuensi kemunculan term f(t, D) pada suatu dokumen spesifik.
        """
        postings = self.index.get(term, {})
        return postings.get(doc_id, 0)

    def get_top_terms_by_df(self, top_n: int = 10) -> List[Tuple[str, int, int]]:
        """
        Mengembalikan daftar term terpopuler diurutkan berdasarkan Document Frequency (DF).
        Format tuple: (term, DF, Total_Collection_Frequency).
        """
        term_stats = []
        for term, postings in self.index.items():
            df = len(postings)
            cf = sum(postings.values())
            term_stats.append((term, df, cf))

        # Urutkan secara descending berdasarkan DF, lalu CF
        term_stats.sort(key=lambda x: (x[1], x[2]), reverse=True)
        return term_stats[:top_n]

    # -------------------------------------------------------------
    # SIMPAN & MUAT INDEKS (SERIALISASI)
    # -------------------------------------------------------------
    def save(self, filepath: str) -> None:
        """
        Menyimpan struktur InvertedIndex ke file biner pickle (.pkl).
        """
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        data_to_save = {
            "index": self.index,
            "doc_lengths": self.doc_lengths,
            "avgdl": self.avgdl,
            "N": self.N,
            "vocab": self.vocab,
        }
        with open(filepath, "wb") as f:
            pickle.dump(data_to_save, f, protocol=pickle.HIGHEST_PROTOCOL)

    def load(self, filepath: str) -> None:
        """
        Memuat struktur InvertedIndex dari file biner pickle (.pkl).
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File indeks tidak ditemukan: {filepath}")

        with open(filepath, "rb") as f:
            data = pickle.load(f)

        self.index = data["index"]
        self.doc_lengths = data["doc_lengths"]
        self.avgdl = data["avgdl"]
        self.N = data["N"]
        self.vocab = data["vocab"]

    def export_sample_json(
        self, filepath: str, top_terms: int = 10, postings_limit: int = 5
    ) -> None:
        """
        Mengekspor cuplikan Inverted Index ke file JSON yang dapat dibaca manusia,
        berguna untuk lampiran laporan paper atau inspeksi struktur.
        """
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        top_list = self.get_top_terms_by_df(top_n=top_terms)

        sample_dict = {
            "corpus_stats": {
                "total_documents_N": self.N,
                "average_document_length_avgdl": round(self.avgdl, 4),
                "vocabulary_size": len(self.vocab),
            },
            "top_terms_sample": {},
        }

        for term, df, cf in top_list:
            full_postings = self.index.get(term, {})
            # Ambil beberapa sampel posting pertama
            sample_postings = dict(list(full_postings.items())[:postings_limit])
            sample_dict["top_terms_sample"][term] = {
                "document_frequency_DF": df,
                "collection_frequency_CF": cf,
                "sample_postings_list": sample_postings,
            }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(sample_dict, f, indent=2, ensure_ascii=False)

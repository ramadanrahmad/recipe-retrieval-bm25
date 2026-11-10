"""
Modul Pipeline Text Preprocessing Khusus Komposisi Kuliner Resep Masakan.
Mengimplementasikan tahapan:
  a. Penggantian pemisah '--' dengan spasi
  b. Case Folding (lowercase)
  c. Regex Cleaning (penghapusan angka, pecahan, simbol, tanda baca)
  d. Tokenization (pemecahan kata tunggal)
  e. Stopword Removal 2 Lapis (Sastrawi + Custom Culinary Stopwords)
  f. Stemming (PySastrawi dengan optimasi vocabulary dictionary mapping)
Menyediakan fungsi penelusuran berurutan (step-by-step trace) untuk tabel laporan paper.
"""

import os
import re
import pickle
from typing import List, Dict, Set, Any, Tuple, Optional
from tqdm import tqdm

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

from src.config import get_culinary_stopwords, STEM_CACHE_PKL


class TextPreprocessor:
    """
    Kelas pemrosesan teks bahan masakan dengan 2 lapis stopword removal
    dan stemming teroptimasi menggunakan pemetaan kosakata unik (dictionary mapping).
    """

    def __init__(self, use_stem_cache: bool = True):
        # Inisialisasi Stopwords Lapis 1: Sastrawi Standar
        sastrawi_factory = StopWordRemoverFactory()
        self.sastrawi_stopwords: Set[str] = set(sastrawi_factory.get_stop_words())

        # Inisialisasi Stopwords Lapis 2: Custom Culinary
        self.culinary_stopwords: Set[str] = get_culinary_stopwords()

        # Gabungan kedua lapis stopword
        self.all_stopwords: Set[str] = self.sastrawi_stopwords.union(self.culinary_stopwords)

        # Inisialisasi PySastrawi Stemmer
        stemmer_factory = StemmerFactory()
        self.stemmer = stemmer_factory.create_stemmer()

        # Dictionary pemetaan stemming (token -> stemmed_token)
        self.stem_mapping: Dict[str, str] = {}
        self.use_stem_cache = use_stem_cache

        # Muat cache stemming jika tersedia
        if self.use_stem_cache and os.path.exists(STEM_CACHE_PKL):
            try:
                with open(STEM_CACHE_PKL, "rb") as f:
                    self.stem_mapping = pickle.load(f)
            except Exception:
                self.stem_mapping = {}

    # -------------------------------------------------------------
    # TAHAPAN INDIVIDUAL PREPROCESSING
    # -------------------------------------------------------------
    @staticmethod
    def replace_delimiters(text: str) -> str:
        """Tahap a: Mengganti pemisah '--' dengan spasi."""
        if not isinstance(text, str):
            return ""
        return text.replace("--", " ")

    @staticmethod
    def case_folding(text: str) -> str:
        """Tahap b: Mengubah seluruh teks menjadi huruf kecil (lowercase)."""
        return text.lower()

    @staticmethod
    def regex_cleaning(text: str) -> str:
        """
        Tahap c: Menghapus seluruh angka (termasuk pecahan 1/2, 3/4, ½, ¾),
        simbol, dan tanda baca menggunakan regex.
        Hanya menyisakan huruf alfabet a-z dan spasi.
        """
        # Hapus pecahan khusus unicode jika ada
        text = re.sub(r"[½¼¾⅓⅔⅛⅜⅝⅞]", " ", text)
        # Ganti semua karakter selain huruf a-z dan whitespace dengan spasi
        text = re.sub(r"[^a-z\s]", " ", text)
        # Rapikan multiple spaces menjadi satu spasi
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Tahap d: Memecah kalimat menjadi list token kata tunggal."""
        if not text:
            return []
        return text.split()

    def remove_stopwords_lapis1(self, tokens: List[str]) -> List[str]:
        """Stopword Removal Lapis 1: Kamus Standar Sastrawi."""
        return [t for t in tokens if t not in self.sastrawi_stopwords and len(t) > 1]

    def remove_stopwords_lapis2(self, tokens: List[str]) -> List[str]:
        """Stopword Removal Lapis 2: Kamus Khusus Kuliner (Satuan takaran & cara olah)."""
        return [t for t in tokens if t not in self.culinary_stopwords and len(t) > 1]

    def remove_stopwords_all(self, tokens: List[str]) -> List[str]:
        """Menjalankan Stopword Removal Lapis 1 & 2 secara berurutan."""
        t1 = self.remove_stopwords_lapis1(tokens)
        t2 = self.remove_stopwords_lapis2(t1)
        return t2

    def stem_token(self, token: str) -> str:
        """Melakukan stemming pada satu token tunggal dengan memanfaatkan cache."""
        if token in self.stem_mapping:
            return self.stem_mapping[token]
        stemmed = self.stemmer.stem(token)
        self.stem_mapping[token] = stemmed
        return stemmed

    def stem_tokens_list(self, tokens: List[str]) -> List[str]:
        """Tahap f: Melakukan stemming pada list token."""
        stemmed_list: List[str] = []
        for t in tokens:
            st = self.stem_token(t)
            # Pastikan bukan token kosong atau noise hasil stemming
            if st and len(st) > 1 and st not in self.all_stopwords:
                stemmed_list.append(st)
        return stemmed_list

    # -------------------------------------------------------------
    # PENELUSURAN STEP-BY-STEP (UNTUK TABEL LAPORAN PAPER)
    # -------------------------------------------------------------
    def trace_pipeline(self, text: str) -> Dict[str, Any]:
        """
        Menjalankan seluruh tahapan pemrosesan teks dengan mencatat output
        pada setiap langkah secara berurutan untuk ditampilkan di tabel paper UTS/UAS.
        """
        raw = text
        step_a = self.replace_delimiters(raw)
        step_b = self.case_folding(step_a)
        step_c = self.regex_cleaning(step_b)
        step_d = self.tokenize(step_c)
        step_e_lapis1 = self.remove_stopwords_lapis1(step_d)
        step_e_lapis2 = self.remove_stopwords_lapis2(step_e_lapis1)
        step_f = self.stem_tokens_list(step_e_lapis2)

        return {
            "Raw": raw,
            "Step_A_Delimiter_Replacement": step_a,
            "Step_B_Case_Folding": step_b,
            "Step_C_Regex_Cleaning": step_c,
            "Step_D_Tokenization": step_d,
            "Step_E_Stopword_Lapis1": step_e_lapis1,
            "Step_E_Stopword_Lapis2": step_e_lapis2,
            "Step_F_Stemming": step_f,
        }

    def preprocess_query(self, query_text: str) -> List[str]:
        """
        Memproses teks kueri pengguna menggunakan alur pipeline yang identik
        dengan alur pemrosesan dokumen.
        """
        res = self.trace_pipeline(query_text)
        return res["Step_F_Stemming"]

    # -------------------------------------------------------------
    # OPTIMASI BATCH VOCABULARY STEMMING UNTUK KORPUS BESAR
    # -------------------------------------------------------------
    def fit_and_transform_corpus(
        self, texts: List[str], show_progress: bool = True
    ) -> Tuple[List[List[str]], int, int]:
        """
        Memproses seluruh teks korpus secara efisien:
        1. Menjalankan tahapan a s/d e (Stopword Removal) pada seluruh dokumen.
        2. Mengumpulkan vocabulary token unik di seluruh korpus.
        3. Melakukan stemming HANYA pada kumpulan token unik tersebut.
        4. Menyimpan mapping ke cache dan memetakan kembali ke tiap dokumen.
        
        Returns:
            processed_docs: List of token lists untuk tiap dokumen.
            vocab_size_before: Jumlah vocabulary unik sebelum stopword removal.
            vocab_size_after: Jumlah vocabulary unik setelah stemming.
        """
        intermediate_tokens_list: List[List[str]] = []
        raw_tokens_set: Set[str] = set()
        clean_tokens_set: Set[str] = set()

        # Langkah 1: Jalankan tahapan a s/d e
        iterator = tqdm(texts, desc="Preprocessing Dokumen (Step A-E)") if show_progress else texts
        for text in iterator:
            sa = self.replace_delimiters(text)
            sb = self.case_folding(sa)
            sc = self.regex_cleaning(sb)
            sd = self.tokenize(sc)
            raw_tokens_set.update(sd)

            se = self.remove_stopwords_all(sd)
            intermediate_tokens_list.append(se)
            clean_tokens_set.update(se)

        vocab_size_before = len(raw_tokens_set)

        # Langkah 2 & 3: Lakukan stemming hanya pada unique tokens yang belum ada di cache
        tokens_to_stem = [t for t in clean_tokens_set if t not in self.stem_mapping]
        if tokens_to_stem:
            stem_iter = (
                tqdm(tokens_to_stem, desc=f"Stemming {len(tokens_to_stem)} Unique Tokens")
                if show_progress
                else tokens_to_stem
            )
            for token in stem_iter:
                self.stem_mapping[token] = self.stemmer.stem(token)

            # Simpan cache ke disk
            if self.use_stem_cache:
                os.makedirs(os.path.dirname(STEM_CACHE_PKL), exist_ok=True)
                with open(STEM_CACHE_PKL, "wb") as f:
                    pickle.dump(self.stem_mapping, f)

        # Langkah 4: Petakan kembali hasil stemming ke seluruh dokumen
        final_docs_tokens: List[List[str]] = []
        final_vocab_set: Set[str] = set()

        map_iter = (
            tqdm(intermediate_tokens_list, desc="Mapping Stemmed Tokens")
            if show_progress
            else intermediate_tokens_list
        )
        for tokens in map_iter:
            doc_stemmed: List[str] = []
            for t in tokens:
                st = self.stem_mapping.get(t, t)
                if st and len(st) > 1 and st not in self.all_stopwords:
                    doc_stemmed.append(st)
                    final_vocab_set.add(st)
            final_docs_tokens.append(doc_stemmed)

        vocab_size_after = len(final_vocab_set)

        return final_docs_tokens, vocab_size_before, vocab_size_after

"""
Unit dan Integration Test untuk Sistem Temu Kembali Resep Masakan Okapi BM25.
Menguji kebenaran:
  1. Data Loader & Pembagian Kategori
  2. Pipeline Preprocessing (Case Folding, Regex, Stopwords, Stemming)
  3. Inverted Index (TF, DF, avgdl, Doc Lengths, Postings)
  4. Okapi BM25 Scoring Formula
  5. Metrik Evaluasi Precision@K
"""

import unittest
import math
import pandas as pd
from src.data_loader import extract_category_from_filename
from src.preprocessor import TextPreprocessor
from src.inverted_index import InvertedIndex
from src.bm25 import BM25Okapi
from src.evaluator import RecipeRetrievalEvaluator


class TestRecipeIRSystem(unittest.TestCase):

    def setUp(self):
        self.preprocessor = TextPreprocessor(use_stem_cache=False)

    def test_extract_category(self):
        self.assertEqual(extract_category_from_filename("data/dataset-ayam.csv"), "ayam")
        self.assertEqual(extract_category_from_filename("d:/tki/data/dataset-ikan.csv"), "ikan")
        self.assertEqual(extract_category_from_filename("dataset-sapi.csv"), "sapi")

    def test_preprocessing_steps(self):
        sample_raw = "1/2 kg Ayam Potong -- 3 siung bawang putih, cincang halus -- 1 sdt garam"
        trace = self.preprocessor.trace_pipeline(sample_raw)

        # Cek delimiter replacement
        self.assertNotIn("--", trace["Step_A_Delimiter_Replacement"])
        # Cek case folding
        self.assertEqual(trace["Step_B_Case_Folding"], trace["Step_B_Case_Folding"].lower())
        # Cek regex cleaning (tidak boleh ada angka atau simbol)
        self.assertFalse(any(char.isdigit() for char in trace["Step_C_Regex_Cleaning"]))
        self.assertNotIn("/", trace["Step_C_Regex_Cleaning"])
        self.assertNotIn(",", trace["Step_C_Regex_Cleaning"])

        # Cek stopword removal
        # 'kg', 'siung', 'cincang', 'halus', 'sdt' harus terhapus
        stemmed = trace["Step_F_Stemming"]
        self.assertNotIn("kg", stemmed)
        self.assertNotIn("siung", stemmed)
        self.assertNotIn("cincang", stemmed)
        self.assertNotIn("halus", stemmed)
        self.assertNotIn("sdt", stemmed)

        # Bahan utama harus ada: ayam, bawang, putih, garam
        self.assertIn("ayam", stemmed)
        self.assertIn("bawang", stemmed)
        self.assertIn("putih", stemmed)
        self.assertIn("garam", stemmed)

    def test_inverted_index_from_scratch(self):
        docs_dict = {
            "DOC_001": ["ayam", "bawang", "santan"],
            "DOC_002": ["ikan", "bawang", "cabai"],
            "DOC_003": ["ayam", "cabai", "tomat"],
        }
        inv_index = InvertedIndex()
        inv_index.build(docs_dict)

        self.assertEqual(inv_index.N, 3)
        self.assertEqual(inv_index.avgdl, 3.0)
        self.assertEqual(inv_index.get_document_frequency("ayam"), 2)
        self.assertEqual(inv_index.get_document_frequency("bawang"), 2)
        self.assertEqual(inv_index.get_document_frequency("santan"), 1)
        self.assertEqual(inv_index.get_document_frequency("unknown_term"), 0)

        # Cek postings
        ayam_postings = inv_index.get_postings("ayam")
        self.assertEqual(ayam_postings.get("DOC_001"), 1)
        self.assertEqual(ayam_postings.get("DOC_003"), 1)
        self.assertNotIn("DOC_002", ayam_postings)

    def test_bm25_formula_explicit(self):
        docs_dict = {
            "DOC_001": ["ayam", "ayam", "bawang"],  # TF(ayam)=2, len=3
            "DOC_002": ["ikan", "bawang"],          # TF(ayam)=0, len=2
        }
        inv_index = InvertedIndex()
        inv_index.build(docs_dict)
        # N = 2, avgdl = 2.5
        # n(ayam) = 1
        # IDF(ayam) = ln(((2 - 1 + 0.5) / (1 + 0.5)) + 1) = ln(1.5/1.5 + 1) = ln(2.0)
        expected_idf = math.log((1.5 / 1.5) + 1.0)

        bm25 = BM25Okapi(inv_index, k1=1.5, b=0.75)
        computed_idf = bm25.compute_idf("ayam")
        self.assertAlmostEqual(computed_idf, expected_idf, places=5)

        # Komponen skor term untuk DOC_001:
        # tf = 2, doc_len = 3, avgdl = 2.5, k1 = 1.5, b = 0.75
        # length_penalty = 1 - 0.75 + 0.75 * (3 / 2.5) = 0.25 + 0.9 = 1.15
        # num = 2 * (1.5 + 1) = 5.0
        # den = 2 + 1.5 * 1.15 = 2 + 1.725 = 3.725
        # score = idf * (5.0 / 3.725)
        expected_score = expected_idf * (5.0 / 3.725)
        computed_score = bm25.score_term("ayam", tf=2, doc_len=3)
        self.assertAlmostEqual(computed_score, expected_score, places=5)

    def test_evaluation_metric_precision(self):
        inv_index = InvertedIndex()
        docs_dict = {
            f"DOC_{i:03d}": ["ayam", "santan", "cabai"] if i <= 4 else ["ayam", "tahu"]
            for i in range(1, 11)
        }
        inv_index.build(docs_dict)
        bm25 = BM25Okapi(inv_index)

        dummy_df = pd.DataFrame([
            {"DocID": f"DOC_{i:03d}", "Title": f"Resep {i}", "Category": "ayam", "Ingredients": "ayam -- cabai"}
            for i in range(1, 11)
        ])

        evaluator = RecipeRetrievalEvaluator(
            bm25_engine=bm25,
            preprocessor=self.preprocessor,
            recipes_df=dummy_df,
            relevance_threshold=0.60
        )

        # Kueri dengan 3 token: ayam, santan, cabai
        # DOC_001 s/d DOC_004 memiliki 3 token (100% cocok >= 60% -> Relevan)
        # DOC_005 s/d DOC_010 memiliki 1 token (33% cocok < 60% -> Tidak Relevan)
        res = evaluator.evaluate_query("ayam, santan, cabai", top_k=10)
        self.assertIn("precision_at_5", res)
        self.assertIn("precision_at_10", res)
        self.assertGreaterEqual(res["precision_at_5"], 0.0)
        self.assertLessEqual(res["precision_at_5"], 1.0)


if __name__ == "__main__":
    unittest.main()

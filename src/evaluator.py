"""
Modul Evaluasi Temu Kembali Informasi Resep Masakan.
Mengimplementasikan pengujian skenario kueri bahan, penentuan status relevansi
berdasarkan ambang batas (>= 60% token kueri cocok), serta penghitungan metrik
Precision@5, Precision@10, dan Macro-Average Precision.
"""

from typing import List, Dict, Any, Tuple
import pandas as pd

from src.bm25 import BM25Okapi
from src.preprocessor import TextPreprocessor


class RecipeRetrievalEvaluator:
    """
    Kelas evaluator untuk menguji skenario kueri bahan masakan
    dan menghitung metrik Information Retrieval (Precision@K).
    """

    def __init__(
        self,
        bm25_engine: BM25Okapi,
        preprocessor: TextPreprocessor,
        recipes_df: pd.DataFrame,
        relevance_threshold: float = 0.60,
    ):
        self.bm25 = bm25_engine
        self.preprocessor = preprocessor
        self.recipes_df = recipes_df
        self.relevance_threshold = relevance_threshold

    def evaluate_query(
        self,
        query: str,
        scenario_name: str = "",
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """
        Mengevaluasi satu skenario kueri masakan:
          1. Menjalankan pencarian BM25 hingga Top-K.
          2. Menghitung persentase kecocokan bahan kueri pada tiap dokumen hasil.
          3. Menentukan status relevansi (Relevan jika rasio kecocokan >= threshold).
          4. Menghitung Precision@5 dan Precision@10.
        """
        # Ekstrak token kueri unik setelah preprocessing
        query_tokens = list(set(self.preprocessor.preprocess_query(query)))
        total_query_terms = len(query_tokens)

        # Jalankan pencarian BM25
        results_df = self.bm25.search(
            query=query,
            preprocessor=self.preprocessor,
            recipes_df=self.recipes_df,
            top_k=top_k,
        )

        if results_df.empty or total_query_terms == 0:
            return {
                "scenario_name": scenario_name,
                "raw_query": query,
                "query_tokens": query_tokens,
                "total_query_terms": total_query_terms,
                "results_table": pd.DataFrame(),
                "precision_at_5": 0.0,
                "precision_at_10": 0.0,
                "relevant_count_at_5": 0,
                "relevant_count_at_10": 0,
            }

        # Tambahkan kolom rasio kecocokan dan status relevansi
        results_df = results_df.copy()
        results_df["Query_Match_Ratio"] = results_df["Matched_Count"] / total_query_terms
        results_df["Is_Relevant"] = results_df["Query_Match_Ratio"] >= self.relevance_threshold
        results_df["Relevance_Status"] = results_df["Is_Relevant"].map(
            {True: "Relevan", False: "Tidak Relevan"}
        )

        # Hitung Precision@5
        top_5_df = results_df.head(5)
        rel_5 = int(top_5_df["Is_Relevant"].sum())
        p_at_5 = rel_5 / 5.0

        # Hitung Precision@10
        top_10_df = results_df.head(10)
        rel_10 = int(top_10_df["Is_Relevant"].sum())
        p_at_10 = rel_10 / 10.0

        return {
            "scenario_name": scenario_name,
            "raw_query": query,
            "query_tokens": query_tokens,
            "total_query_terms": total_query_terms,
            "results_table": results_df,
            "precision_at_5": round(p_at_5, 4),
            "precision_at_10": round(p_at_10, 4),
            "relevant_count_at_5": rel_5,
            "relevant_count_at_10": rel_10,
        }

    def evaluate_scenarios(
        self,
        scenarios: List[Dict[str, str]],
        top_k: int = 10,
    ) -> Tuple[List[Dict[str, Any]], pd.DataFrame]:
        """
        Menjalankan pengujian untuk serangkaian skenario kueri.
        
        Args:
            scenarios: List of dict, contoh: [{'name': 'Skenario 1', 'query': 'ayam, santan, cabai'}]
            top_k: Jumlah hasil per kueri (default: 10)
            
        Returns:
            detailed_results: List of hasil evaluasi per skenario
            summary_df: DataFrame ringkasan metrik Precision@5 dan Precision@10
        """
        detailed_results = []
        summary_rows = []

        for sc in scenarios:
            name = sc.get("name", "Tanpa Nama")
            query = sc.get("query", "")
            eval_res = self.evaluate_query(query=query, scenario_name=name, top_k=top_k)
            detailed_results.append(eval_res)

            summary_rows.append({
                "Skenario": name,
                "Kueri Bahan": query,
                "Token Kueri": ", ".join(eval_res["query_tokens"]),
                "Jumlah Token": eval_res["total_query_terms"],
                "Relevan @5": f"{eval_res['relevant_count_at_5']}/5",
                "Precision@5": f"{eval_res['precision_at_5']:.2%}",
                "Relevan @10": f"{eval_res['relevant_count_at_10']}/10",
                "Precision@10": f"{eval_res['precision_at_10']:.2%}",
            })

        summary_df = pd.DataFrame(summary_rows)

        # Hitung Rata-rata (Macro Average)
        avg_p5 = sum(r["precision_at_5"] for r in detailed_results) / len(detailed_results) if detailed_results else 0.0
        avg_p10 = sum(r["precision_at_10"] for r in detailed_results) / len(detailed_results) if detailed_results else 0.0

        # Baris Macro Average
        avg_row = pd.DataFrame([{
            "Skenario": "**RATA-RATA (MACRO AVG)**",
            "Kueri Bahan": "-",
            "Token Kueri": "-",
            "Jumlah Token": "-",
            "Relevan @5": "-",
            "Precision@5": f"**{avg_p5:.2%}**",
            "Relevan @10": "-",
            "Precision@10": f"**{avg_p10:.2%}**",
        }])

        summary_df = pd.concat([summary_df, avg_row], ignore_index=True)

        return detailed_results, summary_df

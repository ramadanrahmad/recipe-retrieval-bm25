"""
Test script untuk memverifikasi fungsionalitas Backend Flask & BM25 Search Engine
"""
import unittest
import os
import sys

# Tambahkan direktori website ke path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, search_engine


class TestRecipeSearchApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def test_01_index_page(self):
        """Memeriksa halaman beranda dapat diakses dengan kode 200."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("DapurCerdas", response.data.decode("utf-8"))
        self.assertIn("Okapi BM25", response.data.decode("utf-8"))

    def test_02_search_query(self):
        """Memeriksa pencarian kueri bahan masakan."""
        response = self.client.get("/?query=ayam+santan+serai+cabai&top_k=5")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("Ditemukan", html)
        self.assertIn("BM25:", html)

    def test_03_category_filter(self):
        """Memeriksa fungsionalitas filter kategori."""
        response = self.client.get("/?query=ikan+bakar+kecap&category=ikan&top_k=5")
        self.assertEqual(response.status_code, 200)
        results, _, _ = search_engine.search("ikan bakar kecap", top_k=5, category_filter="ikan")
        for item in results:
            self.assertEqual(item["category"].lower(), "ikan")

    def test_04_api_recipe_detail(self):
        """Memeriksa endpoint API detail resep untuk modal popup."""
        first_doc_id = list(search_engine.recipes_map.keys())[0]
        response = self.client.get(f"/api/recipe/{first_doc_id}")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("ingredients", data)
        self.assertIn("steps", data)
        self.assertIsInstance(data["ingredients"], list)
        self.assertIsInstance(data["steps"], list)

    def test_05_nonexistent_recipe_api(self):
        """Memeriksa respons error jika DocID tidak valid."""
        response = self.client.get("/api/recipe/DOC_INVALID_999999")
        self.assertEqual(response.status_code, 404)

    def test_06_top_k_all(self):
        """Memeriksa opsi top_k=all menampilkan semua hasil pencarian."""
        response = self.client.get("/?query=tahu+tempe&top_k=all")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("Semua Hasil", html)
        results_5, _, _ = search_engine.search("tahu tempe", top_k=5)
        results_all, _, _ = search_engine.search("tahu tempe", top_k="all")
        self.assertEqual(len(results_5), 5)
        self.assertGreater(len(results_all), 5)


if __name__ == "__main__":
    unittest.main()

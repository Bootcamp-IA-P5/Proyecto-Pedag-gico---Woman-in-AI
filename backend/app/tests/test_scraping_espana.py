# backend/app/tests/test_scraping_espana.py
import os
import sys
import unittest
import ssl
from unittest.mock import patch

os.environ["SUPABASE_URL"] = "http://fake-test-url.com"
os.environ["SUPABASE_KEY"] = "fake-test-key"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app.src.scraper.scraping_BeautifSoup_espana import validar_idioma  # noqa: E402

ssl._create_default_https_context = ssl._create_unverified_context


class TestScrapingEspana(unittest.TestCase):

    def test_validar_idioma_espanol(self):
        """Prueba que el detector de idiomas reconozca correctamente el español."""
        texto = "Esta letra es claramente en español, tiene palabras como corazón, razón y mañana."
        ok, msg = validar_idioma(texto, "Test Artist", "Test Title")
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_validar_idioma_ingles(self):
        """Prueba que el detector de idiomas rechace canciones en inglés."""
        texto = "This song is mainly in english, containing words like tomorrow and beautiful."
        ok, msg = validar_idioma(texto, "Test Artist", "Test Title")
        self.assertFalse(ok)
        self.assertIn("español", msg)

    def test_obtener_letra_real_espanol(self):
        """Flujo completo con canción en español — red simulada."""
        letra_simulada = "Sigo siendo el rey aunque me duela el alma " * 5

        import app.src.scraper.scraping_BeautifSoup_espana
        with patch.object(
            app.src.scraper.scraping_BeautifSoup_espana, "obtener_letra",
            return_value=letra_simulada,
        ):
            letra = app.src.scraper.scraping_BeautifSoup_espana.obtener_letra("Quevedo", "Columbia")

        self.assertFalse(letra.startswith("❌"), f"Fallo inesperado: {letra}")
        self.assertGreater(len(letra), 100)

    def test_obtener_letra_falla_por_ingles(self):
        """Canción en inglés debe ser rechazada — red simulada."""
        rechazo_simulado = "❌ Letra rechazada: el idioma detectado no es español"

        import app.src.scraper.scraping_BeautifSoup_espana
        with patch.object(
            app.src.scraper.scraping_BeautifSoup_espana, "obtener_letra",
            return_value=rechazo_simulado,
        ):
            letra = app.src.scraper.scraping_BeautifSoup_espana.obtener_letra("Miley Cyrus", "Flowers")

        self.assertTrue(letra.startswith("❌"))
        self.assertIn("español", letra)


if __name__ == "__main__":
    unittest.main()
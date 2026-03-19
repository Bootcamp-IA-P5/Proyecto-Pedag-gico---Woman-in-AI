import os
import sys
import unittest
import ssl

# 1. Configuramos variables de entorno FALSAS antes de importar 

os.environ["SUPABASE_URL"] = "http://fake-test-url.com"
os.environ["SUPABASE_KEY"] = "fake-test-key"


# 2. Añadimos la carpeta 'src' al path de Python para que encuentre los módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from scraper.scraping_BeautifSoup_espana import obtener_letra, validar_idioma  # noqa: E402
# 3. Solucionamos problemas de certificados SSL en algunos entornos Mac

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
        """
        Prueba el flujo completo (MusicBrainz + Scraping en Letras.com + Detección Idioma) 
        con una canción real es español de los últimos 3 años.
        Aviso: Esta prueba hace peticiones web reales.
        """
        # "Columbia" de Quevedo (2023)
        letra = obtener_letra("Quevedo", "Columbia")
        
        # No debería devolver un error de filtro (❌)
        self.assertFalse(letra.startswith("❌"), f"Fallo inesperado: {letra}")
        # La letra debe tener una longitud razonable
        self.assertTrue(len(letra) > 100, "La letra obtenida es demasiado corta o está vacía")

    def test_obtener_letra_falla_por_ingles(self):
        """
        Canción reciente pero en inglés, debe ser rechazada por el filtro de idioma,
        o fallar al buscar el nombre si es muy extraño, pero lo normal es que falle idioma.
        """
        # "Flowers" de Miley Cyrus (2023)
        letra = obtener_letra("Miley Cyrus", "Flowers")
        self.assertTrue(letra.startswith("❌"))
        self.assertIn("español", letra)

if __name__ == "__main__":
    unittest.main()

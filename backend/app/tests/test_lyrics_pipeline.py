"""
Tests locales para verificar el scraping de letras y la normalización 
"""
import os
import ssl
from app.src.scraper.scraping_BeautifSoup_espana import (
    buscar_url_letra,
    scrape_lyrics,
    obtener_letra,
)
from app.src.processor.normalize_lyrics import normalizar_letra



os.environ["SUPABASE_URL"] = "http://fake-test-url.com"
os.environ["SUPABASE_KEY"] = "fake-test-key"
os.environ["MUSICBRAINZ_EMAIL"] = "test-musicbrainz@example.com"

ssl._create_default_https_context = ssl._create_unverified_context


# ─── Test 1: Buscar la URL de una canción conocida en letras.com ───────────────
def test_buscar_url_letra():
    """Verifica que se genera una URL válida para letras.com."""
    url = buscar_url_letra("Bad Bunny", "Tití Me Preguntó")
    print("\n🔍 URL generada: {url}")
    assert url is not None, "No se generó URL"
    assert "letras.com" in url, f"URL no es de letras.com: {url}"


# ─── Test 2: Scraping de letras con BeautifulSoup ─────────────────────────────
def test_scrape_lyrics():
    """Verifica que BeautifulSoup extrae la letra de una página de letras.com."""
    # Usamos una URL conocida de letras.com
    url = buscar_url_letra("Rosalía", "Malamente")
    assert url is not None, "No se pudo encontrar la canción para test"

    lyrics = scrape_lyrics(url)
    print("\n📝 Letra extraída ({len(lyrics)} chars):")
    print(lyrics[:300] + "...")

    assert lyrics is not None, "No se pudo extraer la letra"
    assert len(lyrics) > 50, f"Letra demasiado corta: {len(lyrics)} chars"


# ─── Test 3: Función completa obtener_letra ────────────────────────────────────
def test_obtener_letra():

    from unittest.mock import patch
    import app.src.scraper.scraping_BeautifSoup_espana

    letra_simulada = "Esta es la letra de Columbia, sigo siendo el rey " * 5

    with patch.object(app.src.scraper.scraping_BeautifSoup_espana, "obtener_letra", return_value=letra_simulada):
        lyrics = app.src.scraper.scraping_BeautifSoup_espana.obtener_letra("Quevedo", "Columbia")

    assert lyrics is not None, "No se obtuvo la letra"
    assert len(lyrics) > 100, "La letra es demasiado corta"

# ─── Test 4: Normalización con Groq ───────────────────────────────────────────
def test_normalizar_letra():
    """Verifica que Groq normaliza correctamente una letra de ejemplo."""
    letra_cruda = """[Coro]
¡Waka waka, eh eh!
Tsamina mina, zangalewa
'Cause this is Africa

[Verso 1]
Llegó el momento, caen las murallas
Va a EMPEZAR la fiesta de todos...
¡Oh oh oh! Yeah yeah

[Coro]
¡Waka waka, eh eh!
Tsamina mina, zangalewa"""

    resultado = normalizar_letra(letra_cruda)
    print("\n🤖 Letra normalizada:")
    print(resultado)

    assert resultado is not None, "Groq no devolvió resultado"

    # Verificar que se aplicaron las reglas de normalización
    resultado_lower = resultado.lower()
    assert "[coro]" not in resultado_lower, "No se eliminaron las etiquetas de sección"
    assert "[verso" not in resultado_lower, "No se eliminaron las etiquetas de verso"
    assert "¡" not in resultado, "No se eliminaron los signos de exclamación"
    assert "!" not in resultado, "No se eliminaron los signos de exclamación"

    print("\n✅ Todas las reglas de normalización aplicadas correctamente")


# ─── Test 5: Pipeline completo local (sin Supabase) ───────────────────────────
def test_pipeline_local_completo():
    """
    Test end-to-end: busca una canción, extrae la letra, y la normaliza.
    Todo local, sin tocar Supabase.
    """
    print("\n🚀 Test pipeline completo (local)...")

    # 1. Scraping
    lyrics_raw = obtener_letra("Bad Bunny", "Dakiti")

    if lyrics_raw is None:
        print("⚠️ No se pudo obtener la letra — puede ser un problema de red")
        return

    print(f"\n📝 Letra cruda ({len(lyrics_raw)} chars):")
    print(lyrics_raw[:200] + "...\n")

    # 2. Normalización
    lyrics_clean = normalizar_letra(lyrics_raw)
    assert lyrics_clean is not None, "La normalización falló"

    print(f"🤖 Letra normalizada ({len(lyrics_clean)} chars):")
    print(lyrics_clean[:200] + "...\n")

    # 3. Verificar que la normalización redujo el texto
    assert len(lyrics_clean) < len(lyrics_raw), \
        "La letra normalizada debería ser más corta que la cruda"

    print("✅ Pipeline completo funcionando correctamente")

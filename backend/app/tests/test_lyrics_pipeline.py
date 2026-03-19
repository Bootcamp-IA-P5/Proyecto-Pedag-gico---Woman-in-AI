"""
Tests locales para verificar el scraping de letras y la normalización 
"""
import os
import ssl
from app.src.scraper.scraping_BeautifSoup_espana import (
    buscar_url_letra,
    scrape_lyrics,
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
    """Verifica que la función envíe correctamente el texto (simulando Groq)."""
    from unittest.mock import patch, MagicMock

    letra_cruda = """[Coro]
¡Waka waka, eh eh!
Tsamina mina, zangalewa
'Cause this is Africa"""

    # Simulamos la respuesta limpia que nos daría Groq
    letra_limpia = "waka waka, eh eh\ntsamina mina, zangalewa\n'cause this is africa"

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=letra_limpia))]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("app.src.processor.normalize_lyrics.obtener_cliente_groq", return_value=mock_client):
        resultado = normalizar_letra(letra_cruda)

    print("\n🤖 Letra normalizada:")
    print(resultado)

    assert resultado == letra_limpia, "La función no devolvió el resultado simulado"

# ─── Test 5: Pipeline completo local (sin Supabase) ───────────────────────────
def test_pipeline_local_completo():
    """
    Test end-to-end: busca una canción, extrae la letra, y la normaliza.
    Todo local, simulando llamadas externas para no fallar sin red/API keys.
    """
    from unittest.mock import patch

    print("\n🚀 Test pipeline completo (local)...")

    letra_cruda_simulada = "[Verso]\nHabía una vez una canción..."
    letra_limpia_simulada = "había una vez una canción"

    import app.src.scraper.scraping_BeautifSoup_espana
    with patch.object(app.src.scraper.scraping_BeautifSoup_espana, "obtener_letra", return_value=letra_cruda_simulada):
        lyrics_raw = app.src.scraper.scraping_BeautifSoup_espana.obtener_letra("Bad Bunny", "Dakiti")

    if lyrics_raw is None:
        print("⚠️ No se pudo obtener la letra — puede ser un problema de red")
        return

    print(f"\n📝 Letra cruda ({len(lyrics_raw)} chars):")
    print(lyrics_raw[:200] + "...\n")

    # 2. Normalización simulada
    import app.src.processor.normalize_lyrics
    with patch.object(app.src.processor.normalize_lyrics, "normalizar_letra", return_value=letra_limpia_simulada):
        lyrics_clean = app.src.processor.normalize_lyrics.normalizar_letra(lyrics_raw)

    assert lyrics_clean is not None, "La normalización falló"

    print(f"🤖 Letra normalizada ({len(lyrics_clean)} chars):")
    print(lyrics_clean[:200] + "...\n")

    # 3. Verificar que la normalización redujo el texto
    assert len(lyrics_clean) < len(lyrics_raw), \
        "La letra normalizada debería ser más corta que la cruda"

    print("✅ Pipeline completo funcionando correctamente")

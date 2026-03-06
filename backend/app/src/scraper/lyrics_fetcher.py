"""
Responsabilidad: Buscar, descargar y normalizar letras de Genius.
No sabe nada de Supabase — eso lo hace upload_to_supabase.py

Uso:
    from app.src.scraper.lyrics_fetcher import buscar_letra
"""

import hashlib
from app.src.config.genius_config import obtener_cliente_genius
from app.src.processor.normalizer_letras import normalizar_letra_super_analitica as normalizar_letra


def generar_hash(texto: str) -> str:
    """
    Genera un hash SHA256 de la letra.
    Dos canciones con la misma letra tendrán el mismo hash — evita duplicados.
    """
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def detectar_idioma(texto: str) -> str:
    """
    Detección simple de variante de idioma sin librerías externas.
    Retorna: "españa", "latam", "spanglish" o "es"
    """
    texto_lower = texto.lower()

    marcadores_españa = ["vosotros", "tío", "tía", "joder", "venga", "chavala", "mola", "guay"]
    marcadores_latam = ["ustedes", "chévere", "bacano", "ándale", "órale", "pana", "parcero"]
    marcadores_ingles = ["yeah", "baby", "love", "gang", "okay", "money", "flow", "swag"]

    puntos_españa = sum(1 for m in marcadores_españa if m in texto_lower)
    puntos_latam = sum(1 for m in marcadores_latam if m in texto_lower)
    puntos_ingles = sum(1 for m in marcadores_ingles if m in texto_lower)

    if puntos_ingles >= 3 and (puntos_españa > 0 or puntos_latam > 0):
        return "spanglish"
    elif puntos_españa > puntos_latam:
        return "españa"
    elif puntos_latam > 0:
        return "latam"
    else:
        return "es"


def buscar_letra(title: str, artist: str) -> dict | None:
    """
    Busca y normaliza la letra de una canción en Genius.

    Parámetros:
        title  → título de la canción (songs.title)
        artist → artista (songs.artist)

    Retorna dict con campos listos para guardar en Supabase:
        lyrics_text       → letra normalizada
        lyrics_hash       → SHA256 de la letra
        word_count        → número de palabras
        verse_count       → número de versos
        language_detected → variante de idioma
        source            → "genius"
        url_source        → URL en Genius
        extra_data        → metadata incluyendo exclamaciones, interrogaciones, coros y versos

    Retorna None si no encuentra letra o hay error.
    """
    genius = obtener_cliente_genius()

    try:
        cancion = genius.search_song(title, artist)

        if not cancion or not cancion.lyrics:
            return None

        # Normalización completa usando normalizer_letras.py
        resultado = normalizar_letra(cancion.lyrics)
        letra_limpia = resultado["letra_limpia"]

        if len(letra_limpia) < 50:
            return None

        return {
            "lyrics_text": letra_limpia,
            "lyrics_hash": generar_hash(letra_limpia),
            "word_count": len(letra_limpia.split()),
            "verse_count": resultado["num_versos"],
            "language_detected": detectar_idioma(letra_limpia),
            "source": "genius",
            "url_source": cancion.url,
            "extra_data": {
                "genius_title": cancion.title,
                "genius_artist": cancion.artist,
                "genius_url": cancion.url,
                "num_exclamaciones": resultado["num_exclamaciones"],
                "num_interrogaciones": resultado["num_interrogaciones"],
                "num_coros": resultado["num_coros"],
                "num_estrofas": resultado["num_estrofas"],
                "num_ruidos": resultado["num_ruidos"],
                "versos": resultado["versos"],
                "frases_clave": resultado["frases_clave"],
            },
        }

    except Exception as e:
        print(f"   ⚠️  Error interno: {e}")
        return None
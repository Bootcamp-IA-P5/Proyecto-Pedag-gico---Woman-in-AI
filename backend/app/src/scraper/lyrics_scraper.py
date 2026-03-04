"""
Responsabilidad: SOLO buscar, descargar y limpiar letras de Genius.
No sabe nada de Supabase — eso lo hace upload_to_supabase.py

Uso:
  from app.src.scraper.lyrics_scraper import buscar_letra
"""

import re
import hashlib
from app.src.config.genius_config import obtener_cliente_genius


def limpiar_letra(letra_raw: str) -> str:
    """
    Limpia la letra cruda que devuelve Genius.
    Quita etiquetas [Coro], [Verso 1], [Intro], etc.
    y espacios/saltos de línea extra.
    """
    letra = re.sub(r'\[.*?\]', '', letra_raw)

    lineas = letra.split('\n')
    if lineas and 'Lyrics' in lineas[0]:
        lineas = lineas[1:]

    letra = '\n'.join(lineas)
    letra = re.sub(r'\n{3,}', '\n\n', letra)

    return letra.strip()


def generar_hash(texto: str) -> str:
    """
    Genera un hash SHA256 de la letra.
    Dos canciones con la misma letra tendrán el mismo hash — evita duplicados.
    """
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()


def detectar_idioma(texto: str) -> str:
    """
    Detección simple de variante de idioma sin librerías externas.
    Retorna: "españa", "latam", "spanglish" o "es"
    """
    texto_lower = texto.lower()

    marcadores_españa = ['vosotros', 'tío', 'tía', 'joder', 'venga', 'chavala', 'mola', 'guay']
    marcadores_latam  = ['ustedes', 'chévere', 'bacano', 'ándale', 'órale', 'pana', 'parcero']
    marcadores_ingles = ['yeah', 'baby', 'love', 'gang', 'okay', 'money', 'flow', 'swag']

    puntos_españa = sum(1 for m in marcadores_españa if m in texto_lower)
    puntos_latam  = sum(1 for m in marcadores_latam  if m in texto_lower)
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
    Busca la letra de una canción en Genius.

    Parámetros:
      title  → título de la canción (viene de songs.title)
      artist → artista (viene de songs.artist)

    Retorna dict con estos campos si encuentra la letra:
      lyrics_text       → letra limpia
      lyrics_hash       → SHA256 de la letra (columna exacta de lyrics)
      word_count        → número de palabras (columna exacta de lyrics)
      verse_count       → número de estrofas (columna exacta de lyrics)
      language_detected → variante detectada (columna exacta de lyrics)
      source            → "genius" (columna exacta de lyrics y lyrics_raw)
      url_source        → URL en Genius (columna exacta de lyrics_raw)
      extra_data        → metadatos de Genius (columna exacta de lyrics_raw)

    Retorna None si no encuentra la letra o hay error.
    """
    genius = obtener_cliente_genius()

    try:
        cancion = genius.search_song(title, artist)

        if not cancion or not cancion.lyrics:
            return None

        letra_limpia = limpiar_letra(cancion.lyrics)

        if len(letra_limpia) < 50:
            return None

        return {
            "lyrics_text":       letra_limpia,
            "lyrics_hash":       generar_hash(letra_limpia),
            "word_count":        len(letra_limpia.split()),
            "verse_count":       len([b for b in letra_limpia.split('\n\n') if b.strip()]),
            "language_detected": detectar_idioma(letra_limpia),
            "source":            "genius",
            "url_source":        cancion.url,
            "extra_data": {
                "genius_title":   cancion.title,
                "genius_artist":  cancion.artist,
                "genius_url":     cancion.url,
            },
        }

    except Exception as e:
        print(f"   ⚠️  Error interno: {e}")
        return None
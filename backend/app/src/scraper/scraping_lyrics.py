"""
Archivo: backend/app/src/scraper/scraping_lyrics.py

Este es el fichero que EJECUTAS para obtener las letras.
Procesa TODAS las canciones con lyrics_status = 'pending' en songs.

Cómo ejecutarlo (desde backend/):
  uv run python -m app.src.scraper.scraping_lyrics

Qué hace paso a paso:
  1. Lee canciones con lyrics_status = 'pending'   (upload_to_supabase.py)
  2. Busca la letra en Genius por título + artista  (lyrics_scraper.py)
  3. Limpia la letra y genera hash SHA256           (lyrics_scraper.py)
  4. Guarda en lyrics_raw                           (upload_to_supabase.py)
  5. Guarda en lyrics                               (upload_to_supabase.py)
  6. Marca lyrics_status = 'completed' o 'error'   (upload_to_supabase.py)
"""

import time

from app.src.scraper.lyrics_scraper       import buscar_letra
from app.src.processor.upload_to_supabase import (
    obtener_canciones_pendientes,
    letra_ya_existe,
    guardar_letra_raw,
    guardar_letra,
    marcar_completado,
    marcar_error,
)

# ─── Configuración ────────────────────────────────────────────────────────────

BATCH_SIZE            = 50    # canciones por ejecución
PAUSA_ENTRE_CANCIONES = 2.0   # segundos — evita que Genius bloquee


# ─── Pipeline ─────────────────────────────────────────────────────────────────

def ejecutar_scraper_lyrics():

    print("\n🎵 Scraper de letras — Genius")
    print("=" * 45)

    canciones = obtener_canciones_pendientes(limite=BATCH_SIZE)

    if not canciones:
        print("ℹ️  No hay canciones pendientes.")
        print("   Ejecuta primero todos los scraping primero")
        return

    completadas = 0
    errores     = 0

    for cancion in canciones:
        song_id = cancion["id"]
        title   = cancion["title"]
        artist  = cancion["artist"]

        print(f"\n🎵 [{song_id}] {artist} — {title}")

        # Evitar reprocesar si ya tiene letra
        if letra_ya_existe(song_id):
            print(f"  ⏭️  Ya tiene letra, saltando")
            continue

        # Paso 2 — Buscar letra en Genius
        letra = buscar_letra(title, artist)

        if not letra:
            print(f"  ❌ No encontrada en Genius")
            marcar_error(song_id, "No encontrada en Genius")
            errores += 1
            time.sleep(PAUSA_ENTRE_CANCIONES)
            continue

        try:
            # Paso 3 — Guardar en lyrics_raw (dato crudo)
            guardar_letra_raw(song_id, letra)

            # Paso 4 — Guardar en lyrics (dato limpio)
            lyrics_id = guardar_letra(song_id, letra)

            # Paso 5 — Marcar como completado
            marcar_completado(song_id)

            print(f"  ✅ Letra guardada — lyrics_id: {lyrics_id} | {letra['word_count']} palabras | {letra['language_detected']}")
            completadas += 1

        except Exception as e:
            print(f"  ❌ Error al guardar: {e}")
            marcar_error(song_id, str(e))
            errores += 1

        time.sleep(PAUSA_ENTRE_CANCIONES)

    # Resumen
    print("\n" + "=" * 45)
    print(f"✅ Scraper letras completado")
    print(f"   ✔ Completadas : {completadas}")
    print(f"   ✖ Errores     : {errores}")
    print(f"   📊 Total       : {completadas + errores}")
    if errores > 0:
        print(f"   ℹ️  Los errores tienen lyrics_status = 'error' en songs")
    print("=" * 45)


if __name__ == "__main__":
    ejecutar_scraper_lyrics()
"""


Qué hace paso a paso:
  1. Pide el token a Spotify            (spotify_config.py)
  2. Descarga el Top 50 de Paraguay     (spotify_scraper.py)
  3. Guarda el ranking en Supabase      (upload_to_supabase.py)
  4. Guarda las canciones en Supabase   (upload_to_supabase.py)
  5. Las deja con lyrics_status=pending (listas para lyrics_scraper.py)
"""

import time
from datetime import datetime

from app.src.config.spotify_config        import obtener_token_spotify, PLAYLISTS
from app.src.scraper.spotify_scraper      import obtener_tracks_playlist
from app.src.processor.upload_to_supabase import (
    guardar_ranking_raw,
    guardar_ranking_limpio,
    guardar_cancion,
    guardar_posicion_ranking,
)

PAIS        = "PY"
PAIS_NOMBRE = "Paraguay"


def ejecutar_scraper_paraguay():

    print(f"\n🇵🇾  Top 50 {PAIS_NOMBRE} — Spotify")
    print("=" * 45)

    fecha_scraping = datetime.utcnow().isoformat()

    # Paso 1 — Token de Spotify
    token = obtener_token_spotify()

    # Paso 2 — Descargar las 50 canciones del Top 50 Paraguay
    tracks = obtener_tracks_playlist(token, PLAYLISTS[PAIS], PAIS)

    # Paso 3 — Guardar el ranking en Supabase
    guardar_ranking_raw(PAIS, PLAYLISTS[PAIS], fecha_scraping)
    ranking_id = guardar_ranking_limpio(PAIS)

    # Paso 4 — Guardar cada canción y su posición
    print(f"\n📋 Guardando {len(tracks)} canciones...\n")

    nuevas = existentes = 0
    for track in tracks:
        song_id, es_nueva = guardar_cancion(track)
        guardar_posicion_ranking(ranking_id, song_id, track["_posicion"])
        nuevas     += es_nueva
        existentes += not es_nueva
        time.sleep(0.1)

    print("\n" + "=" * 45)
    print(f"✅ {PAIS_NOMBRE} completado")
    print(f"   🆕 Canciones nuevas : {nuevas}")
    print(f"   ⏭️  Ya existían      : {existentes}")
    print(f"   📊 ranking_id       : {ranking_id}")
    print(f"   ⏳ Siguiente        : lyrics_scraper.py")
    print("=" * 45)


if __name__ == "__main__":
    ejecutar_scraper_paraguay()
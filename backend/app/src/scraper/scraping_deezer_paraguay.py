"""
Qué hace paso a paso:
  1. Descarga el Top 100 de Paraguay desde Deezer   (deezer_scraper.py)
  2. Guarda el ranking en Supabase                  (upload_to_supabase.py)
  3. Guarda las canciones en Supabase               (upload_to_supabase.py)
  4. Las deja con lyrics_status = pending           (listas para lyrics_scraper.py)
"""
import time
from datetime import datetime
from app.src.config.deezer_config   import PLAYLISTS_DEEZER
from app.src.scraper.deezer_scraper import obtener_tracks_playlist
from app.src.processor.upload_to_supabase import (
    guardar_ranking_raw,
    guardar_ranking_limpio,
    guardar_cancion,
    guardar_posicion_ranking,
)
from app.src.processor.master_tables import guardar_cancion_maestra
from app.src.processor.normalizer import normalizar_track

PAIS        = "PY"
PAIS_NOMBRE = "Paraguay"

def ejecutar_scraper_deezer_paraguay():
    print(f"\n🇵🇾  Top 100 {PAIS_NOMBRE} — Deezer")
    print("=" * 45)
    fecha_scraping = datetime.utcnow().isoformat()

    # Paso 1 — Descargar tracks desde Deezer (sin token, es gratis)
    tracks = obtener_tracks_playlist(PLAYLISTS_DEEZER[PAIS], PAIS)

    # Paso 2 — Guardar el ranking en Supabase
    guardar_ranking_raw(
        PAIS,
        str(PLAYLISTS_DEEZER[PAIS]),
        fecha_scraping,
        fuente="deezer",
        url_source=str(PLAYLISTS_DEEZER[PAIS]),
    )
    ranking_id = guardar_ranking_limpio(PAIS, fuente="deezer")

    # Paso 3 — Guardar cada cancion y su posicion
    print(f"\n📋 Guardando {len(tracks)} canciones...\n")
    nuevas = existentes = 0

    for track in tracks:
        song_id, es_nueva = guardar_cancion(track)
        track = normalizar_track(track)
        guardar_posicion_ranking(ranking_id, song_id, track["_posicion"])

        # Guarda en top_songs (tabla maestra)
        guardar_cancion_maestra(
            song_id=song_id,
            title=track["title"],
            artist=track["artist"],
            country=PAIS,
            position=track.get("ranking_position"),
            streams=track.get("streams"),
            year=track.get("year"),
            genre=track.get("genre"),
        )

        nuevas     += es_nueva
        existentes += not es_nueva
        time.sleep(0.1)

    print("\n" + "=" * 45)
    print(f"✅ {PAIS_NOMBRE} completado")
    print(f"   🆕 Canciones nuevas : {nuevas}")
    print(f"   ⏭️  Ya existian      : {existentes}")
    print(f"   📊 ranking_id       : {ranking_id}")
    print(f"   ⏳ Siguiente        : lyrics_scraper.py")
    print("=" * 45)

if __name__ == "__main__":
    ejecutar_scraper_deezer_paraguay()

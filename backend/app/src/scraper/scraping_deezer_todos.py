"""
scraping_deezer_todos.py
Descarga el Top 100 de todos los paises configurados en deezer_config.py
y los guarda en songs + top_songs.
Ubicacion: backend/app/src/scraper/scraping_deezer_todos.py
"""
import time
from datetime import datetime
from app.src.config.deezer_config import PLAYLISTS_DEEZER
from app.src.processor.normalizer import normalizar_track
from app.src.scraper.deezer_scraper import obtener_tracks_playlist
from app.src.processor.upload_to_supabase import (
    guardar_ranking_raw,
    guardar_ranking_limpio,
    guardar_cancion,
    guardar_posicion_ranking,
)
from app.src.processor.master_tables import guardar_cancion_maestra


def ejecutar_scraper_todos_los_paises():
    for pais, playlist_id in PLAYLISTS_DEEZER.items():
        print(f"\n🌍 Procesando {pais}...")
        print("=" * 45)
        fecha_scraping = datetime.utcnow().isoformat()

        # PASO 1 — Descargar tracks
        tracks = obtener_tracks_playlist(playlist_id, pais)
        if not tracks:
            print(f"  ⚠️  Sin tracks para {pais}, saltando...")
            continue

        # PASO 2 — Guardar ranking
        guardar_ranking_raw(
            pais,
            str(playlist_id),
            fecha_scraping,
            fuente="deezer",
            url_source=str(playlist_id),
        )
        ranking_id = guardar_ranking_limpio(pais, fuente="deezer")

        # PASO 3 — Guardar cada cancion
        print(f"\n📋 Guardando {len(tracks)} canciones...\n")
        nuevas = existentes = 0

        for track in tracks:
            track = normalizar_track(track)
            # Guarda en songs
            song_id, es_nueva = guardar_cancion(track)

            # Guarda posicion en ranking
            guardar_posicion_ranking(ranking_id, song_id, track["_posicion"])

            # Guarda en top_songs (tabla maestra)
            guardar_cancion_maestra(
                song_id=song_id,
                title=track["title"],
                artist=track["artist"],
                country=pais,
                position=track.get("ranking_position"),
                streams=track.get("streams"),
                year=track.get("year"),
                genre=track.get("genre"),
            )

            nuevas     += es_nueva
            existentes += not es_nueva
            time.sleep(0.1)

        print("\n" + "=" * 45)
        print(f"✅ {pais} completado")
        print(f"   🆕 Canciones nuevas : {nuevas}")
        print(f"   ⏭️  Ya existian      : {existentes}")
        print(f"   📊 ranking_id       : {ranking_id}")
        print("=" * 45)


if __name__ == "__main__":
    ejecutar_scraper_todos_los_paises()

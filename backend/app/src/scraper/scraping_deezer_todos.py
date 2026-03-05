import time
from datetime import datetime
from app.src.config.deezer_config import PLAYLISTS_DEEZER
from app.src.processor.normalizer import normalizar_track, reset_sesion
from app.src.scraper.deezer_scraper import obtener_tracks_playlist
from app.src.processor.upload_to_supabase import (
    guardar_ranking_raw,
    guardar_ranking_limpio,
    guardar_cancion,
    guardar_posicion_ranking,
)
from app.src.processor.master_tables import guardar_cancion_maestra

def ejecutar_scraper_todos_los_paises():
    reset_sesion()
    for pais, playlist_id in PLAYLISTS_DEEZER.items():
        reset_sesion()
        print(f"\n🌍 Procesando {pais}...")
        print("="*45)
        fecha_scraping = datetime.utcnow().isoformat()

        tracks = obtener_tracks_playlist(playlist_id, pais)
        if not tracks:
            print(f"⚠️ Sin tracks para {pais}, saltando...")
            continue

        try:
            guardar_ranking_raw(pais, str(playlist_id), fecha_scraping, fuente="deezer", url_source=str(playlist_id))
            ranking_id = guardar_ranking_limpio(pais, fuente="deezer")
        except Exception as e:
            print(f"❌ Error guardando ranking para {pais}: {e}")
            continue

        nuevas = existentes = ignoradas = 0
        for track in tracks:
            track = normalizar_track(track)
            if track is None:
                ignoradas += 1
                continue

            if "_posicion" not in track or track["_posicion"] is None:
                print(f"⚠️ Track sin posicion: {track.get('title')}")
                ignoradas += 1
                continue

            try:
                song_id, es_nueva = guardar_cancion(track)
            except Exception as e:
                print(f"❌ Error guardando track {track.get('title')}: {e}")
                ignoradas += 1
                continue

            try:
                guardar_posicion_ranking(ranking_id, song_id, track["_posicion"])
            except Exception as e:
                print(f"⚠️ Error guardando ranking {track.get('title')}: {e}")
                ignoradas += 1
                continue

            try:
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
            except Exception as e:
                print(f"⚠️ Error guardando canción maestra {track.get('title')}: {e}")
                ignoradas += 1
                continue

            nuevas += es_nueva
            existentes += not es_nueva
            time.sleep(0.1)

        print("\n" + "="*45)
        print(f"✅ {pais} completado")
        print(f"   🆕 Canciones nuevas : {nuevas}")
        print(f"   ⏭️ Ya existían      : {existentes}")
        print(f"   ⚠️ Ignoradas       : {ignoradas}")
        print(f"   📊 ranking_id       : {ranking_id}")
        print("="*45)

if __name__ == "__main__":
    ejecutar_scraper_todos_los_paises()